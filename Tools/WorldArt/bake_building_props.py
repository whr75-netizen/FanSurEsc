"""Normalize each complete source sheet once, then crop complete building props.

Uses the existing modified PerfectPixel source_regions sampler from
bake_planar_tiles. Coordinates are integer pixel edges from the top-left, with
X right and Y down. Source selection cells must align to the four-pixel grid.
No homography, rotation, per-prop resampling, palette change or generated art.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image

from bake_planar_tiles import PROJECT_ROOT, SHEET_GRID_PIXELS, load_engine, sha256


def project_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def alpha_bbox(rgba: np.ndarray) -> tuple[int, int, int, int]:
    rows, columns = np.nonzero(rgba[..., 3])
    if not len(rows):
        raise ValueError("The selected cell contains no opaque pixels.")
    return int(columns.min()), int(rows.min()), int(columns.max()) + 1, int(rows.max()) + 1


def component_coverage(padded: np.ndarray, seed: list[int]) -> tuple[np.ndarray, np.ndarray, dict]:
    """Map one authored 8-connected alpha component to the unchanged sheet grid.

    The component seed identifies the object even when neighboring object bboxes
    overlap. A native cell belongs to it when at least half of that cell's source
    pixels belong to it. Mixed-object cells are rejected, never repainted.
    """
    opaque = padded[..., 3] == 255
    height, width = opaque.shape
    sx, sy = seed
    if not (0 <= sx < width and 0 <= sy < height and opaque[sy, sx]):
        raise ValueError("The authored component seed is not inside an opaque source pixel.")
    component = np.zeros(opaque.shape, dtype=bool)
    component[sy, sx] = True
    pending = deque([(sx, sy)])
    while pending:
        x, y = pending.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (0 <= nx < width and 0 <= ny < height and opaque[ny, nx]
                        and not component[ny, nx]):
                    component[ny, nx] = True
                    pending.append((nx, ny))
    grid = SHEET_GRID_PIXELS
    blocks = (height // grid, grid, width // grid, grid)
    counts = component.reshape(blocks).sum(axis=(1, 3))
    native_mask = counts >= grid * grid * .5
    other_counts = (opaque & ~component).reshape(blocks).sum(axis=(1, 3))
    mixed_count = int(np.count_nonzero(native_mask & (other_counts > 0)))
    if mixed_count:
        raise ValueError("The object shares normalized cells with another source component; no mixed colors were accepted.")
    rows, columns = np.nonzero(component)
    bounds = [int(columns.min()), int(rows.min()), int(columns.max()) + 1, int(rows.max()) + 1]
    return native_mask, component, {
        "method": "source alpha 8-connected component -> aligned 4x4 source-cell coverage >=0.5 -> native alpha mask",
        "source_component_seed_xy": seed, "source_connectivity": 8,
        "source_component_bbox_xyxy_exclusive": bounds,
        "source_component_opaque_pixels": int(component.sum()),
        "source_component_mask_sha256": hashlib.sha256(component.tobytes()).hexdigest(),
        "native_component_cells": int(native_mask.sum()), "mixed_object_source_cells": mixed_count,
    }


def bake(output_dir: Path, evidence_dir: Path, engine_root: Path, shelf_source: Path,
         profile: str = "initial", desk_source: Path | None = None, outdoor_source: Path | None = None) -> dict:
    started = perf_counter()
    output_dir, evidence_dir, engine_root, shelf_source = (
        path.resolve() for path in (output_dir, evidence_dir, engine_root, shelf_source))
    street_source = PROJECT_ROOT / "Assets/Art/IsometricUrban/Gpt2/StreetObjects.png"
    if profile == "initial":
        # This cell ends before the Stop sign begins at y=274. Bin source alpha
        # bounds are x=1155..1279, y=40..246 inclusive.
        entries = [
            {"name": "Bin", "source": street_source, "source_selection_xywh": [1088, 0, 360, 268]},
            {"name": "Shelf", "source": shelf_source, "source_selection_xywh": None},
        ]
        source_copy_paths = {shelf_source: output_dir / "Sources/ShelfSource.png"}
        sheet_paths = {street_source: output_dir / "Sheets/StreetObjects.png",
                       shelf_source: output_dir / "Sheets/ShelfSource.png"}
        report_name = "bake-report.json"
    elif profile == "poi_reviewed":
        if desk_source is None or outdoor_source is None:
            raise ValueError("The poi_reviewed profile requires desk and outdoor source images.")
        desk_source, outdoor_source = desk_source.resolve(), outdoor_source.resolve()
        entries = [
            {"name": "Desk", "source": desk_source, "source_selection_xywh": None},
            {"name": "Dumpster", "source": outdoor_source, "source_selection_xywh": None,
             "source_component_seed_xy": [540, 680]},
        ]
        source_copy_paths = {desk_source: output_dir / "Sources/DeskSource.png",
                             outdoor_source: output_dir / "Sources/OutdoorPropsSource.png"}
        sheet_paths = {desk_source: output_dir / "Sheets/DeskSource.png",
                       outdoor_source: output_dir / "Sheets/OutdoorPropsSource.png"}
        report_name = "poi-bake-report.json"
    else:
        raise ValueError("Unknown building prop profile.")
    source_paths = list(dict.fromkeys(entry["source"] for entry in entries))
    source_hashes = {path: sha256(path) for path in source_paths}
    manifest_path = output_dir / "BuildingProps.json"
    report_path = evidence_dir / report_name
    output_paths = [*source_copy_paths.values(), manifest_path, report_path, *sheet_paths.values(),
                    *(output_dir / (entry["name"] + ".png") for entry in entries)]
    if len(set(output_paths)) != len(output_paths):
        raise ValueError("Output paths must be distinct.")
    if any(path.exists() for path in output_paths):
        raise FileExistsError("A requested output exists; choose new output/evidence directories.")
    if any(path in source_paths for path in output_paths):
        raise ValueError("An output aliases a source image.")
    load_started = perf_counter()
    sample_scoped, engine_hashes, engine_hash = load_engine(engine_root)
    engine_load_seconds = perf_counter() - load_started
    sheets, source_sizes, sheet_records, component_masks, component_records = {}, {}, [], {}, {}
    for source_path in source_paths:
        with Image.open(source_path) as source_image:
            if source_image.format != "PNG" or source_image.mode != "RGBA":
                raise ValueError(f"Expected an RGBA PNG: {source_path}")
            source = np.array(source_image, dtype=np.uint8)
        height, width = source.shape[:2]
        source_sizes[source_path] = (width, height)
        padding_x, padding_y = (-width) % SHEET_GRID_PIXELS, (-height) % SHEET_GRID_PIXELS
        padded = np.pad(source, ((0, padding_y), (0, padding_x), (0, 0)), mode="constant")
        padded[..., 3] = np.where(padded[..., 3] >= 128, 255, 0).astype(np.uint8)
        native_size = (padded.shape[1] // SHEET_GRID_PIXELS, padded.shape[0] // SHEET_GRID_PIXELS)
        source_components = {}
        for entry in entries:
            if entry["source"] == source_path and "source_component_seed_xy" in entry:
                mask, component, record = component_coverage(padded, entry["source_component_seed_xy"])
                component_masks[entry["name"]] = mask
                source_components[entry["name"]] = component
                component_records[entry["name"]] = record
        sample_started = perf_counter()
        native, sample_source_xy = sample_scoped(padded, native_size, np.ones(padded.shape[:2], dtype=bool),
                               coverage=.5, method="source_regions", source_guide=padded,
                               color_edge_threshold=.08, return_source_xy=True)
        sample_seconds = perf_counter() - sample_started
        if (native.dtype != np.uint8 or native.shape != (native_size[1], native_size[0], 4)
                or not np.isin(native[..., 3], [0, 255]).all()):
            raise RuntimeError("Modified PerfectPixel returned an invalid normalized RGBA sheet.")
        for name, component in source_components.items():
            mask = component_masks[name]
            if not np.all(native[..., 3][mask] == 255):
                raise RuntimeError("Whole-sheet normalization omitted a cell meeting component coverage.")
            sampled = sample_source_xy[mask]
            if np.any(sampled < 0) or not np.all(component[sampled[:, 1], sampled[:, 0]]):
                raise RuntimeError("A retained normalized pixel came from another source object.")
            component_records[name]["retained_pixel_source_identity_mismatches"] = 0
        sheets[source_path] = native
        sheet_records.append({
            "source": project_path(source_copy_paths.get(source_path, source_path)),
            "original_source": project_path(source_path), "source_sha256": source_hashes[source_path],
            "source_size": [width, height], "padding_right_bottom": [padding_x, padding_y],
            "normalized_sheet": project_path(sheet_paths[source_path]), "native_size": list(native_size),
            "sheet_grid_pixels": SHEET_GRID_PIXELS, "engine_call_count": 1,
            "sample_seconds": sample_seconds,
        })
    props, records = {}, []
    for entry in entries:
        source_path = entry["source"]
        native = sheets[source_path]
        if entry["name"] in component_masks:
            native = native.copy()
            native[~component_masks[entry["name"]]] = 0
        selection = entry["source_selection_xywh"]
        if selection is None:
            nx, ny, nw, nh = 0, 0, native.shape[1], native.shape[0]
        else:
            if any(value % SHEET_GRID_PIXELS for value in selection):
                raise ValueError("A selection cell is not aligned to the full-sheet four-pixel grid.")
            nx, ny, nw, nh = (value // SHEET_GRID_PIXELS for value in selection)
            if nx < 0 or ny < 0 or nx + nw > native.shape[1] or ny + nh > native.shape[0]:
                raise ValueError("The authored selection cell lies outside the normalized sheet.")
        cell = native[ny:ny + nh, nx:nx + nw]
        left, top, right, bottom = alpha_bbox(cell)
        if left == 0 or top == 0 or right == nw or bottom == nh:
            raise ValueError(entry["name"] + ": visible pixels touch the selection cell; completeness is uncertain.")
        crop = np.ascontiguousarray(cell[top:bottom, left:right])
        if not np.any(crop[..., 3] == 0):
            raise ValueError(entry["name"] + ": the complete prop must retain its transparent background.")
        props[entry["name"]] = crop
        records.append({
            "name": entry["name"], "sprite": project_path(output_dir / (entry["name"] + ".png")),
            "source": project_path(source_copy_paths.get(source_path, source_path)),
            "original_source": project_path(source_path), "source_sha256": source_hashes[source_path],
            "source_size": list(source_sizes[source_path]), "source_selection_xywh": selection,
            "normalized_sheet": project_path(sheet_paths[source_path]), "sheet_grid_pixels": SHEET_GRID_PIXELS,
            "selection_native_xywh": [nx, ny, nw, nh],
            "crop_native_xywh": [nx + left, ny + top, right - left, bottom - top],
            "size_pixels": [crop.shape[1], crop.shape[0]], "pivot_normalized": [.5, 0.],
            "pivot_convention": "bottom-center of complete alpha bounds; Unity normalized sprite coordinates",
            "engine_call_count_after_crop": 0,
            "object_selection": component_records.get(entry["name"], {"method": "complete alpha bbox inside authored selection cell"}),
        })
    if any(sha256(path) != expected for path, expected in source_hashes.items()):
        raise RuntimeError("A source changed during normalization; outputs were not saved.")
    if any(sha256(engine_root / relative) != expected for relative, expected in engine_hashes.items()):
        raise RuntimeError("The modified PerfectPixel implementation changed during normalization.")
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    for source_path, copy_path in source_copy_paths.items():
        copy_path.write_bytes(source_path.read_bytes())
        if sha256(copy_path) != source_hashes[source_path]:
            raise RuntimeError("A preserved source differs from the original bytes.")
    for source_path, native in sheets.items():
        Image.fromarray(native).save(sheet_paths[source_path])
    for entry in records:
        path = output_dir / (entry["name"] + ".png")
        Image.fromarray(props[entry["name"]]).save(path)
        with Image.open(path) as saved:
            if saved.mode != "RGBA" or saved.size != tuple(entry["size_pixels"]):
                raise RuntimeError("A saved sprite has unexpected dimensions or image mode.")
        entry["sprite_sha256"] = sha256(path)
    for sheet in sheet_records:
        sheet["normalized_sheet_sha256"] = sha256(PROJECT_ROOT / sheet["normalized_sheet"])
    manifest = {
        "schema": "normalized-building-props/2", "profile": profile,
        "pipeline": "full sheet PerfectPixel once -> optional source-component native mask -> complete alpha bbox crop",
        "coordinates": "top-left pixel edges; +X right, +Y down; xywh uses exclusive right/bottom edges",
        "sheet_grid_pixels": SHEET_GRID_PIXELS,
        "alpha_policy": "source alpha >=128 becomes255, otherwise0; normalized output alpha is binary",
        "engine_options": {"method": "source_regions", "coverage": .5, "color_edge_threshold": .08},
        "resampling_after_normalization": False, "sheets": sheet_records, "entries": records,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "schema": "building-props-perfectpixel-bake/2", "profile": profile, "status": "saved", "visual_approval": "pending",
        "manifest": project_path(manifest_path), "sources_unchanged": True,
        "preserved_source_copies_match_originals": True,
        "source_hashes": {project_path(path): value for path, value in source_hashes.items()},
        "engine_root": project_path(engine_root), "engine_sha256": engine_hash,
        "engine_files_sha256": engine_hashes, "engine_call_count": len(source_paths),
        "engine_entry": "perfect_pixel.trigger_pipeline.sample_scoped",
        "engine_options": manifest["engine_options"], "sheets": sheet_records, "entries": records,
        "timings_seconds": {"engine_load": engine_load_seconds,
                            "whole_sheet_sampling": sum(sheet["sample_seconds"] for sheet in sheet_records),
                            "total": perf_counter() - started},
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"manifest": project_path(manifest_path), "report": project_path(report_path),
            "sprites": [{"name": entry["name"], "path": entry["sprite"], "size": entry["size_pixels"]}
                        for entry in records],
            "engine_call_count": len(source_paths), "seconds": report["timings_seconds"]["total"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--profile", choices=("initial", "poi_reviewed"), default="initial")
    parser.add_argument("--engine-root", type=Path, default=PROJECT_ROOT / "LocalOnly/PerfectPixelPalette_20260906")
    parser.add_argument("--shelf-source", type=Path,
                        default=Path("C:/Users/JG/Desktop/GPT/2/픽셀_아트_생존용품_금속_선반.png"))
    parser.add_argument("--desk-source", type=Path,
                        default=Path("C:/Users/JG/Desktop/GPT/2/이소메트릭_픽셀아트_홈_오피스_책상.png"))
    parser.add_argument("--outdoor-source", type=Path,
                        default=Path("C:/Users/JG/Desktop/GPT/2/등각_픽셀_아트_야외_소품_타일셋.png"))
    args = parser.parse_args()
    print(json.dumps(bake(args.output_dir, args.evidence_dir, args.engine_root, args.shelf_source,
                          args.profile, args.desk_source, args.outdoor_source), ensure_ascii=False))


if __name__ == "__main__":
    main()
