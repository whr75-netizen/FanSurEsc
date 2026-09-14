"""Bake annotated atlas planes through the project's existing modified PerfectPixel.

Source PNGs stay unchanged. The source points use pixel-center coordinates in
00, 01, 11, 10 order; canonical +Y points upward while PNG rows point downward.
Each unique full sheet is padded on its right/bottom to a multiple of four and
normalized once by the existing source_regions sampler. Plane homographies then
sample that normalized sheet directly into the metric atlas with nearest lookup.
There is no per-plane PerfectPixel call, palette conversion, or seam synthesis.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEXELS_PER_METRE = 32
SHEET_GRID_PIXELS = 4
ATLAS_SIZE = 512
PADDING = 2
CANONICAL_CORNERS = np.array([[0., 0.], [0., 1.], [1., 1.], [1., 0.]])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive_pair(value, name: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must contain two finite positive numbers.")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
           not math.isfinite(v) or v <= 0 for v in value):
        raise ValueError(f"{name} must contain two finite positive numbers.")
    return float(value[0]), float(value[1])


def homography(points: np.ndarray) -> tuple[np.ndarray, float]:
    edges = np.roll(points, -1, axis=0) - points
    cross = edges[:, 0] * np.roll(edges[:, 1], -1) - edges[:, 1] * np.roll(edges[:, 0], -1)
    if np.any(np.abs(cross) < 1e-8) or not (np.all(cross > 0) or np.all(cross < 0)):
        raise ValueError("Source points must form a nondegenerate convex plane in 00,01,11,10 order.")
    matrix = np.zeros((8, 8), dtype=np.float64)
    values = np.zeros(8, dtype=np.float64)
    for index, ((u, v), (x, y)) in enumerate(zip(CANONICAL_CORNERS, points)):
        row = index * 2
        matrix[row] = [u, v, 1, 0, 0, 0, -x * u, -x * v]
        matrix[row + 1] = [0, 0, 0, u, v, 1, -y * u, -y * v]
        values[row:row + 2] = [x, y]
    coefficients = np.linalg.solve(matrix, values)
    result = np.r_[coefficients, 1.].reshape(3, 3)
    if not np.isfinite(result).all():
        raise ValueError("The source homography contains non-finite coefficients.")
    projected = np.c_[CANONICAL_CORNERS, np.ones(4)] @ result.T
    if np.any(projected[:, 2] <= 1e-9):
        raise ValueError("The source homography has a pole inside the canonical square.")
    error = float(np.max(np.linalg.norm(projected[:, :2] / projected[:, 2:] - points, axis=1)))
    if error > 1e-6:
        raise ValueError(f"Source corner correspondence error exceeds 1e-6 pixels: {error}")
    return result, error


def load_entries(input_path: Path) -> tuple[dict, list[dict]]:
    manifest = json.loads(input_path.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("entries"), list) or not manifest["entries"]:
        raise ValueError("Input must contain a nonempty entries array.")
    entries = []
    names = set()
    for entry in manifest["entries"]:
        if not isinstance(entry, dict) or any(key not in entry for key in ("name", "source", "points", "metres")):
            raise ValueError("Every entry requires name, source, points and metres.")
        name = entry["name"]
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("Every entry needs a unique nonempty name.")
        names.add(name)
        source = Path(entry["source"])
        if not source.is_absolute():
            source = input_path.parent / source
        if not source.is_file():
            raise ValueError(f"{name}: source must be an existing PNG path, relative to the manifest or absolute.")
        source = source.resolve()
        points = np.asarray(entry["points"], dtype=np.float64)
        if points.shape != (4, 2) or not np.isfinite(points).all():
            raise ValueError(f"{name}: points must be four finite coordinate pairs.")
        metres = positive_pair(entry["metres"], name + ".metres")
        size = tuple(max(1, math.floor(length * TEXELS_PER_METRE + .5)) for length in metres)
        if any(length + 2 * PADDING > ATLAS_SIZE for length in size):
            raise ValueError(f"{name}: its metric pixel dimensions {size} exceed the atlas.")
        homography(points)
        inset = entry.get("inset_native_pixels", 0)
        if isinstance(inset, bool) or not isinstance(inset, (int, float)) or not math.isfinite(inset) or inset < 0:
            raise ValueError(f"{name}: inset_native_pixels must be finite and nonnegative.")
        entries.append({"name": name, "source": source, "points": points, "metres": metres,
                        "size": size, "inset_native_pixels": float(inset)})
    return manifest, entries


def pack_shelves(entries: list[dict]) -> None:
    """Manifest order is the deterministic packing order; no hidden resize on overflow."""
    x = y = shelf_height = 0
    for entry in entries:
        width, height = entry["size"]
        outer_width, outer_height = width + PADDING * 2, height + PADDING * 2
        if x + outer_width > ATLAS_SIZE:
            x, y, shelf_height = 0, y + shelf_height, 0
        if y + outer_height > ATLAS_SIZE:
            raise ValueError("All requested metric tiles do not fit the fixed 512x512 atlas; no rescaling was applied.")
        entry["rect"] = [x + PADDING, y + PADDING, width, height]
        entry["padded_rect"] = [x, y, outer_width, outer_height]
        x += outer_width
        shelf_height = max(shelf_height, outer_height)


def inset_convex_polygon(points: np.ndarray, distance: float) -> np.ndarray:
    """Intersect the adjacent inward-offset edge lines, measured in native pixels."""
    if distance == 0:
        return points.copy()
    edges = np.roll(points, -1, axis=0) - points
    signed_area = np.sum(points[:, 0] * np.roll(points[:, 1], -1) -
                         points[:, 1] * np.roll(points[:, 0], -1))
    normals = np.stack([-edges[:, 1], edges[:, 0]], axis=1)
    normals *= math.copysign(1., signed_area) / np.linalg.norm(edges, axis=1)[:, None]
    offsets = np.sum(normals * points, axis=1) + distance
    cropped = np.array([np.linalg.solve(normals[[index - 1, index]], offsets[[index - 1, index]])
                        for index in range(4)])
    if not np.isfinite(cropped).all() or np.any(cropped @ normals.T < offsets[None, :] - 1e-7):
        raise ValueError("inset_native_pixels removes the entire convex plane.")
    homography(cropped)
    return cropped


def rectify_nearest(source: np.ndarray, mapping: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Map final metric texel centers to normalized-sheet pixel centers without filtering."""
    width, height = size
    u = (np.arange(width, dtype=np.float64) + .5) / width
    v = 1. - (np.arange(height, dtype=np.float64) + .5) / height
    uu, vv = np.meshgrid(u, v)
    denominator = mapping[2, 0] * uu + mapping[2, 1] * vv + mapping[2, 2]
    if np.any(denominator <= 1e-9):
        raise ValueError("The metric grid intersects a homography pole.")
    sx = (mapping[0, 0] * uu + mapping[0, 1] * vv + mapping[0, 2]) / denominator
    sy = (mapping[1, 0] * uu + mapping[1, 1] * vv + mapping[1, 2]) / denominator
    ix = np.floor(sx + .5).astype(np.int64)
    iy = np.floor(sy + .5).astype(np.int64)
    if np.any(ix < 0) or np.any(ix >= source.shape[1]) or np.any(iy < 0) or np.any(iy >= source.shape[0]):
        raise ValueError("A metric sample lies outside its normalized sheet; no edge clamp was applied.")
    canonical = np.ascontiguousarray(source[iy, ix])
    if np.any(canonical[..., 3] != 255):
        raise ValueError("The selected plane includes transparent normalized pixels; an opaque plane is required.")
    return canonical


def load_engine(engine_root: Path):
    source_root = engine_root / "src"
    files = sorted((source_root / "perfect_pixel").glob("*.py"))
    if not files:
        raise FileNotFoundError(f"Modified PerfectPixel source was not found: {source_root}")
    hashes = {str(path.relative_to(engine_root)).replace("\\", "/"): sha256(path) for path in files}
    digest = hashlib.sha256()
    for relative, value in hashes.items():
        digest.update(relative.encode("utf-8") + b"\0" + value.encode("ascii") + b"\n")
    sys.path.insert(0, str(source_root))
    engine = importlib.import_module("perfect_pixel.trigger_pipeline")
    if Path(engine.__file__).resolve() != (source_root / "perfect_pixel/trigger_pipeline.py").resolve():
        raise RuntimeError("A different PerfectPixel module was already loaded; refusing to substitute it.")
    return engine.sample_scoped, hashes, digest.hexdigest()


def bake(input_path: Path, output_dir: Path, evidence_dir: Path, engine_root: Path) -> dict:
    started = perf_counter()
    input_path, output_dir, evidence_dir, engine_root = (
        path.resolve() for path in (input_path, output_dir, evidence_dir, engine_root))
    _, entries = load_entries(input_path)
    pack_shelves(entries)
    atlas_path = output_dir / "PlanarTiles.png"
    manifest_path = output_dir / "PlanarTiles.json"
    report_path = evidence_dir / "bake-report.json"
    source_paths = sorted({entry["source"] for entry in entries})
    sheet_paths = {path: output_dir / "Sheets" / (path.stem + ".png") for path in source_paths}
    if len({str(path).casefold() for path in sheet_paths.values()}) != len(source_paths):
        raise ValueError("Unique source sheets must have distinct filenames to preserve their Sheets outputs.")
    output_paths = [atlas_path, manifest_path, report_path, *sheet_paths.values()]
    if any(path.exists() for path in output_paths):
        raise FileExistsError("A requested output already exists; choose new output/evidence directories to preserve it.")
    if input_path in output_paths or any(path in output_paths for path in source_paths):
        raise ValueError("An output path aliases an input path.")
    manifest_hash = sha256(input_path)
    source_hashes = {str(path): sha256(path) for path in source_paths}
    load_start = perf_counter()
    sample_scoped, engine_hashes, engine_hash = load_engine(engine_root)
    engine_load_seconds = perf_counter() - load_start
    images, normalized_sheets, sheet_measurements = {}, {}, []
    for path in source_paths:
        sheet_started = perf_counter()
        with Image.open(path) as image:
            if image.format != "PNG" or image.mode not in ("RGB", "RGBA"):
                raise ValueError(f"Source must be an RGB/RGBA PNG: {path}")
            # Adding fully opaque alpha to RGB preserves every source RGB value.
            source = np.array(image.convert("RGBA"), dtype=np.uint8)
        images[path] = source
        source_height, source_width = source.shape[:2]
        pad_x = (-source_width) % SHEET_GRID_PIXELS
        pad_y = (-source_height) % SHEET_GRID_PIXELS
        padded = np.pad(source, ((0, pad_y), (0, pad_x), (0, 0)), mode="constant")
        changed_alpha = int(np.count_nonzero((padded[..., 3] != 0) & (padded[..., 3] != 255)))
        padded[..., 3] = np.where(padded[..., 3] >= 128, 255, 0).astype(np.uint8)
        native_size = (padded.shape[1] // SHEET_GRID_PIXELS, padded.shape[0] // SHEET_GRID_PIXELS)
        sample_started = perf_counter()
        native = sample_scoped(padded, native_size, np.ones(padded.shape[:2], dtype=bool),
                               coverage=.5, method="source_regions", source_guide=padded,
                               color_edge_threshold=.08)
        sample_seconds = perf_counter() - sample_started
        if native.dtype != np.uint8 or native.shape != (native_size[1], native_size[0], 4) or not np.isin(native[..., 3], [0, 255]).all():
            raise RuntimeError(f"Modified PerfectPixel returned an invalid full-sheet RGBA grid: {path}")
        normalized_sheets[path] = native
        sheet_measurements.append({"input_source": str(path), "source_sha256": source_hashes[str(path)],
                                   "source_size": [source_width, source_height],
                                   "padded_size": [padded.shape[1], padded.shape[0]],
                                   "padding_right_bottom": [pad_x, pad_y], "native_size": list(native_size),
                                   "normalized_sheet": str(sheet_paths[path]),
                                   "alpha_binarized_count": changed_alpha,
                                   "engine_call_count": 1, "sample_seconds": sample_seconds,
                                   "total_seconds": perf_counter() - sheet_started})
    atlas = np.zeros((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.uint8)
    output_entries, measurements = [], []
    for entry in entries:
        item_started = perf_counter()
        source = images[entry["source"]]
        points = entry["points"]
        if np.any(points < 0) or np.any(points[:, 0] >= source.shape[1]) or np.any(points[:, 1] >= source.shape[0]):
            raise ValueError(entry["name"] + ": source landmarks must lie inside the input PNG.")
        sheet_points = (points + .5) / SHEET_GRID_PIXELS - .5
        plane_points = inset_convex_polygon(sheet_points, entry["inset_native_pixels"])
        mapping, corner_error = homography(plane_points)
        coordinate_error = float(np.max(np.abs((sheet_points + .5) * SHEET_GRID_PIXELS - .5 - points)))
        if coordinate_error > 1e-6:
            raise ValueError(entry["name"] + ": whole-sheet coordinate correspondence exceeds 1e-6 source pixels.")
        stage = perf_counter()
        try:
            native = rectify_nearest(normalized_sheets[entry["source"]], mapping, entry["size"])
        except ValueError as error:
            raise ValueError(entry["name"] + ": " + str(error)) from error
        warp_seconds = perf_counter() - stage
        width, height = entry["size"]
        padded = np.pad(native, ((PADDING, PADDING), (PADDING, PADDING), (0, 0)), mode="edge")
        px, py, pw, ph = entry["padded_rect"]
        atlas[py:py + ph, px:px + pw] = padded
        x, y, _, _ = entry["rect"]
        # AtlasPatch later adds .5 before dividing by texture size. These half-pixel
        # coordinates therefore address the exact outside edges of the native texels.
        normalized_points = [[x - .5, y + height - .5], [x - .5, y - .5],
                             [x + width - .5, y - .5], [x + width - .5, y + height - .5]]
        output_entries.append({"name": entry["name"], "source": str(atlas_path),
                               "points": normalized_points, "metres": list(entry["metres"]),
                               "actualMetres": [width / TEXELS_PER_METRE, height / TEXELS_PER_METRE],
                               "size_pixels": [width, height], "pixel_rect_xywh": entry["rect"],
                               "padded_rect_xywh": entry["padded_rect"],
                               "input_source": str(entry["source"]), "input_points": points.tolist(),
                               "normalized_sheet": str(sheet_paths[entry["source"]]),
                               "normalized_sheet_points": sheet_points.tolist(),
                               "normalized_plane_points": plane_points.tolist(),
                               "inset_native_pixels": entry["inset_native_pixels"]})
        measurements.append({"name": entry["name"], "source_sha256": source_hashes[str(entry["source"])],
                             "source_size": [source.shape[1], source.shape[0]],
                             "metric_tile_size": [width, height],
                             "requested_metres": list(entry["metres"]),
                             "actualMetres": [width / TEXELS_PER_METRE, height / TEXELS_PER_METRE],
                             "effective_texels_per_metre": [TEXELS_PER_METRE, TEXELS_PER_METRE],
                             "input_points": points.tolist(), "normalized_sheet_points": sheet_points.tolist(),
                             "normalized_plane_points": plane_points.tolist(),
                             "inset_native_pixels": entry["inset_native_pixels"],
                             "homography_from_normalized_sheet": mapping.tolist(),
                             "corner_error_normalized_pixels": corner_error,
                             "coordinate_error_source_pixels": coordinate_error,
                             "engine_call_count": 0,
                             "opaque_native_pixels": int(np.count_nonzero(native[..., 3] == 255)),
                             "warp_seconds": warp_seconds,
                             "total_seconds": perf_counter() - item_started})
    if sha256(input_path) != manifest_hash or any(sha256(Path(path)) != value for path, value in source_hashes.items()):
        raise RuntimeError("An input changed during normalization; no atlas was saved.")
    if any(sha256(engine_root / relative) != value for relative, value in engine_hashes.items()):
        raise RuntimeError("The modified PerfectPixel engine changed during normalization; no atlas was saved.")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "Sheets").mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    save_started = perf_counter()
    for measurement, path in zip(sheet_measurements, source_paths):
        Image.fromarray(normalized_sheets[path]).save(sheet_paths[path])
        measurement["normalized_sheet_sha256"] = sha256(sheet_paths[path])
    Image.fromarray(atlas).save(atlas_path)
    normalized = {"schema": "normalized-planar-tiles/2", "atlas": str(atlas_path),
                  "atlas_size": [ATLAS_SIZE, ATLAS_SIZE], "padding_pixels": PADDING,
                  "texels_per_metre": TEXELS_PER_METRE,
                  "dimension_rule": "max(1, floor(metres * 32 + 0.5))",
                  "repeat_metres_rule": "actualMetres = native pixel dimensions / 32; requested metres remain separate",
                  "points_convention": "00,01,11,10; top-left source pixel-center coordinates; UV=(point+.5)/atlasSize with inverted Y",
                  "sheet_grid_pixels": SHEET_GRID_PIXELS,
                  "sheet_coordinate_rule": "normalized=(source+.5)/4-.5; padding on right/bottom only",
                  "pipeline": "full sheet PerfectPixel once -> optional plane inset -> nearest homography -> metric atlas",
                  "sheets": sheet_measurements,
                  "entries": output_entries}
    manifest_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"schema": "planar-perfectpixel-bake/2", "status": "saved", "visual_approval": "pending",
              "input_manifest": str(input_path), "input_manifest_sha256": manifest_hash,
              "source_hashes": source_hashes, "sources_unchanged": True,
              "engine_root": str(engine_root), "engine_sha256": engine_hash, "engine_files_sha256": engine_hashes,
              "engine_entry": "perfect_pixel.trigger_pipeline.sample_scoped",
              "engine_options": {"method": "source_regions", "coverage": .5, "color_edge_threshold": .08},
              "alpha_policy": "whole-sheet source alpha >=128 becomes255; otherwise0; source RGB is not adjusted; final planes must be opaque",
              "sheet_grid_pixels": SHEET_GRID_PIXELS, "engine_call_count": len(source_paths),
              "resampling": "existing region-cell sampler once per padded full sheet, then plane nearest homography at final metric size",
              "palette_or_tone_conversion": False, "edge_extrusion_pixels": PADDING,
              "seam_synthesis": False, "sheets": sheet_measurements, "entries": measurements,
              "atlas": str(atlas_path), "atlas_sha256": sha256(atlas_path), "manifest": str(manifest_path),
              "timings_seconds": {"engine_load": engine_load_seconds, "save": perf_counter() - save_started,
                                  "whole_sheet_sampling": sum(item["sample_seconds"] for item in sheet_measurements),
                                  "total": perf_counter() - started}}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"atlas": str(atlas_path), "manifest": str(manifest_path), "report": str(report_path),
            "entry_count": len(entries), "seconds": report["timings_seconds"]["total"],
            "sheet_count": len(source_paths), "engine_call_count": len(source_paths),
            "status": "saved", "visual_approval": "pending"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON with named source plane entries")
    parser.add_argument("--output-dir", required=True, type=Path, help="New atlas and normalized manifest directory")
    parser.add_argument("--evidence-dir", required=True, type=Path, help="Directory for bake-report.json")
    parser.add_argument("--engine-root", type=Path,
                        default=PROJECT_ROOT / "LocalOnly/PerfectPixelPalette_20260906")
    args = parser.parse_args()
    result = bake(args.input, args.output_dir, args.evidence_dir, args.engine_root)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
