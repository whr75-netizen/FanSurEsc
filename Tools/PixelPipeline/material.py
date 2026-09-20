"""Prepare the approved flat wood as material variation, separately from light.

The upstream PerfectPixel backend is executed unchanged and checked against the
original ZIP.  Its RGB output is retained in normalized.png; grain.npy is a
separate, explicitly lossy four-level material index.  Nothing here estimates
illumination, removes shadows, synthesizes grain, or proves semantic albedo from
one image.  Source approval is a provenance gate, not such a proof.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import platform
import zipfile

import numpy as np
from PIL import Image, __version__ as PILLOW_VERSION


ROOT = Path(__file__).resolve().parents[2]
APPROVED_SOURCE = ROOT / "Tools/PixelDesk/materials/oak-user15-source.png"
APPROVED_SOURCE_SHA256 = "399f8b1eecfa0bc8d1e4eb3e92b295e389d39eb118aa2c17e4237f6fed2e344a"
PP_SOURCE = ROOT / "Tools/PixelDesk/vendor/perfectpixel-archive/perfect_pixel_noCV2.py"
PP_SOURCE_SHA256 = "99cbd4e0a9febae704a9637aeba79c68d3e0731e494db17424533c4ef1642522"
PP_ARCHIVE = Path("C:/Users/JG/Desktop/GPT/3/perfectPixel-main.zip")
PP_ARCHIVE_ENTRY = "perfectPixel-main/src/perfect_pixel/perfect_pixel_noCV2.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _packed_colors(rgb: np.ndarray) -> np.ndarray:
    wide = rgb.astype(np.uint32)
    return (wide[..., 0] << 16) | (wide[..., 1] << 8) | wide[..., 2]


def _load_original_pp() -> tuple[object, dict]:
    code = PP_SOURCE.read_bytes()
    digest = hashlib.sha256(code).hexdigest()
    if digest != PP_SOURCE_SHA256:
        raise ValueError("PerfectPixel source differs from the reviewed original implementation")
    with zipfile.ZipFile(PP_ARCHIVE) as archive:
        if archive.read(PP_ARCHIVE_ENTRY) != code:
            raise ValueError("PerfectPixel source differs from its original ZIP entry")
    spec = importlib.util.spec_from_file_location("pixel_pipeline_original_perfectpixel", PP_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load original PerfectPixel implementation")
    module = importlib.util.module_from_spec(spec)
    # Execute the verified original source without generating vendor __pycache__.
    exec(compile(code, str(PP_SOURCE), "exec"), module.__dict__)
    return module, {
        "upstream": "https://github.com/theamusing/perfectPixel",
        "algorithm": "original NumPy get_perfect_pixel / refined grid center sampling",
        "version_note": "archive pyproject 0.1.4 / __init__ 0.1.2; source SHA is authoritative",
        "source_path": str(PP_SOURCE.resolve()),
        "source_sha256": digest,
        "archive_path": str(PP_ARCHIVE.resolve()),
        "archive_entry": PP_ARCHIVE_ENTRY,
        "archive_match": True,
        "sample_method": "center",
        "refine_intensity": 0.25,
        "fix_square": False,
    }


def _quantize_variation(rgb: np.ndarray, levels: int) -> tuple[np.ndarray, dict]:
    """Quantile-bin source luminance in-place, keeping its spatial arrangement.

    Integer Rec.601 luma weights avoid float drift in the ranking.  Each palette
    entry is the source RGB nearest that bin's component median.  This is finite
    material variation, never an inferred illumination or AO value.
    """
    wide = rgb.astype(np.int32)
    luma = wide[..., 0] * 299 + wide[..., 1] * 587 + wide[..., 2] * 114
    thresholds = np.quantile(luma, np.arange(1, levels) / levels, method="linear")
    if not np.all(np.diff(thresholds) > 0):
        raise ValueError("Source has insufficient distinct luminance for the requested grain levels")
    grain = np.searchsorted(thresholds, luma, side="right").astype(np.uint8)
    counts = np.bincount(grain.ravel(), minlength=levels)
    if np.any(counts == 0):
        raise ValueError("Material quantization produced an empty grain level")
    palette = []
    for level in range(levels):
        samples = wide[grain == level]
        median = np.median(samples, axis=0)
        distances = np.sum((samples - median) ** 2, axis=1)
        # np.argmin picks the first in row-major order for deterministic ties.
        palette.append(samples[int(np.argmin(distances))].tolist())
    if len({tuple(c) for c in palette}) != levels:
        raise ValueError("Material palette does not contain the requested number of colors")
    srgb = np.array(palette, dtype=np.float64) / 255.0
    linear = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    data = {
        "schema": 1,
        "semantics": "material_variation_only",
        "levels": levels,
        "colors_srgb8": palette,
        "colors_srgb_hex": ["#" + "".join(f"{channel:02X}" for channel in color) for color in palette],
        "colors_linear": linear.tolist(),
        "ordering": "dark_to_light",
        "lighting_included": False,
        "ao_included": False,
        "lighting_flags_mean": "No lighting/AO stage was applied here; source purity is not mathematically proven.",
        "quantization": {
            "algorithm": "equal-population Rec.601 luma bins, nearest-source-RGB-to-bin-median representative",
            "luma_integer_weights": [299, 587, 114],
            "luma_divisor": 1000,
            "thresholds_srgb_luma": (thresholds / 1000).tolist(),
            "level_counts": counts.tolist(),
            "spatial_filter": "none",
            "dither": "none",
        },
    }
    return grain, data


def prepare_material(source: Path, outdir: Path, config: dict) -> dict:
    """Write a new immutable preparation directory and return paths + receipt.

    Config accepts only grid ([64,64] or [128,128]) and levels (3 or 4).
    The approved input SHA gate intentionally rejects shaded object references,
    including D20, rather than attempting to derive albedo from them.  Output
    dimensions are the actual upstream result, which can differ from grid_size.
    Array/image origin is top-left, x right, y down; no crop/rotation occurs.
    """
    if not isinstance(config, dict):
        raise TypeError("Material config must be a dictionary")
    unknown = set(config) - {"grid", "levels"}
    if unknown:
        raise ValueError(f"Unknown material settings: {sorted(unknown)}")
    grid = config.get("grid", [64, 64])
    levels = config.get("levels", 4)
    if grid not in ([64, 64], [128, 128], (64, 64), (128, 128)):
        raise ValueError("Reviewed manual PerfectPixel grids are 64x64 and 128x128")
    if isinstance(levels, bool) or not isinstance(levels, int) or levels not in (3, 4):
        raise ValueError("Grain levels must be 3 or 4")
    source, outdir = Path(source).resolve(), Path(outdir).resolve()
    if outdir.exists():
        raise FileExistsError(f"Use a new material output directory; existing data is immutable: {outdir}")
    source_sha = _sha256(source)
    if source_sha != APPROVED_SOURCE_SHA256:
        raise ValueError("Source provenance gate failed: only the approved flat wood input SHA is accepted")
    with Image.open(source) as image:
        if image.mode not in ("RGB", "RGBA"):
            raise ValueError("Approved material must decode as RGB/RGBA")
        if image.mode == "RGBA" and image.getextrema()[3] != (255, 255):
            raise ValueError("Material source must be fully opaque")
        source_rgb = np.array(image.convert("RGB"), dtype=np.uint8)
    module, pp_receipt = _load_original_pp()
    with contextlib.redirect_stdout(io.StringIO()) as pp_stdout:
        width, height, normalized = module.get_perfect_pixel(
            source_rgb, sample_method="center", grid_size=tuple(grid),
            refine_intensity=0.25, fix_square=False, debug=False,
        )
    if not width or not height or normalized.shape != (height, width, 3):
        raise ValueError("Original PerfectPixel did not return a valid RGB grid")
    if not (1 < width < source_rgb.shape[1] and 1 < height < source_rgb.shape[0]):
        raise ValueError("Original PerfectPixel returned an unchanged or invalid input grid")
    if normalized.dtype != np.uint8:
        raise ValueError("Original PerfectPixel returned a non-uint8 image")
    colors_from_source = bool(np.isin(np.unique(_packed_colors(normalized)),
                                     np.unique(_packed_colors(source_rgb))).all())
    if not colors_from_source:
        raise ValueError("Original center sampling introduced colors absent from its input")
    grain, palette = _quantize_variation(normalized, levels)
    if grain.shape != normalized.shape[:2]:
        raise ValueError("Grain index and normalized material dimensions differ")
    if _sha256(source) != source_sha or _sha256(PP_SOURCE) != PP_SOURCE_SHA256:
        raise ValueError("An immutable material input changed during preparation")
    pp_receipt.update({"requested_grid": list(grid), "returned_grid": [width, height],
                       "stdout": pp_stdout.getvalue().strip()})
    outdir.mkdir(parents=True, exist_ok=False)
    normalized_path = outdir / "normalized.png"
    grain_path = outdir / "grain.npy"
    palette_path = outdir / "palette.json"
    receipt_path = outdir / "receipt.json"
    Image.fromarray(normalized).save(normalized_path)
    np.save(grain_path, grain, allow_pickle=False)
    _write_json(palette_path, palette)
    receipt = {
        "schema": 1,
        "stage": "prepare_material",
        "source_path": str(source),
        "source_sha256": source_sha,
        "source_size": [source_rgb.shape[1], source_rgb.shape[0]],
        "source_provenance": "User-approved flat flowing wood; same bytes as clipboard 35e026e0-194d-4136-87ae-ce9e952bee72",
        "semantic_limit": "A single image cannot prove pure albedo. No illumination separation or de-lighting is claimed.",
        "perfectpixel": pp_receipt,
        "config": {"grid": list(grid), "levels": levels},
        "coordinates": {"origin": "top-left", "x": "right", "y": "down", "units": "texel", "crop": None, "rotation": None},
        "normalized_path": str(normalized_path),
        "grain_path": str(grain_path),
        "palette_path": str(palette_path),
        "receipt_path": str(receipt_path),
        "width": width,
        "height": height,
        "shape": [height, width],
        "levels": levels,
        "grain_dtype": str(grain.dtype),
        "level_counts": palette["quantization"]["level_counts"],
        "checks": {
            "approved_source_sha_matches": True,
            "original_pp_sha_matches": True,
            "original_pp_zip_matches": True,
            "normalized_colors_from_source": colors_from_source,
            "shape_matches": True,
            "all_grain_levels_present": True,
            "source_unchanged": True,
            "pp_source_unchanged": True,
        },
        "output_sha256": {p.name: _sha256(p) for p in (normalized_path, grain_path, palette_path)},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "pillow": PILLOW_VERSION},
    }
    _write_json(receipt_path, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("outdir", type=Path)
    parser.add_argument("--grid", type=int, choices=(64, 128), default=64)
    parser.add_argument("--levels", type=int, choices=(3, 4), default=4)
    args = parser.parse_args()
    result = prepare_material(args.source, args.outdir, {"grid": [args.grid, args.grid], "levels": args.levels})
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
