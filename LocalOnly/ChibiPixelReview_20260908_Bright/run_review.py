"""Use the existing engine: raw-source coordinates first, region colors second.

This asset runner does not edit the engine, infer stroke scopes, add outlines,
erase selected areas, change brightness, or reuse an external palette.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
ENGINE_FILES = (
    "src/perfect_pixel/__init__.py",
    "src/perfect_pixel/perfect_pixel_noCV2.py",
    "src/perfect_pixel/perfect_pixel.py",
    "src/perfect_pixel/palette.py",
    "src/perfect_pixel/boundary_pipeline.py",
    "src/perfect_pixel/boundary_regions.py",
    "src/perfect_pixel/region_palette.py",
    "src/perfect_pixel/trigger_pipeline.py",
    "src/perfect_pixel/source_sampling.py",
    "src/perfect_pixel/feature_scopes.py",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "review_config.json")
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    folder = config_path.parent
    source_path = (folder / config["source"]).resolve()
    engine = (folder / config["engine"]).resolve()
    output = (folder / config["output"]).resolve()
    if not output.is_relative_to(ROOT) or output == ROOT:
        raise ValueError("Output must be a child directory of this review folder.")
    if output.exists():
        raise FileExistsError("Output already exists; prior results are preserved: " + str(output))
    if not source_path.is_file():
        raise FileNotFoundError("Awaiting the Unity capture: " + str(source_path))
    if config["source_size"] != [384, 768] or config["base_grid"] != [192, 384]:
        raise ValueError("This review is explicitly 384x768 to 192x384.")
    if config["resolution_scale"] != "1.0" or config["preview_zoom"] != 2:
        raise ValueError("The requested native grid is fixed, with a 2x nearest preview.")
    if config["reference"] != "same_unmodified_source":
        raise ValueError("Only the original source palette is authorized.")
    if config["line_normalization"]["enabled"] or config["mask_cleanup"]["enabled"]:
        raise ValueError("This capture review does not enable strokes or mask cleanup.")

    implementation_before = {rel: sha256(engine / rel) for rel in ENGINE_FILES}
    config_hash = sha256(config_path)
    script_hash = sha256(Path(__file__).resolve())
    source_hash = sha256(source_path)
    sys.path.insert(0, str(engine / ".deps"))
    sys.path.insert(0, str(engine / "src"))
    import numpy as np
    import PIL
    from PIL import Image, ImageDraw, ImageFont
    from perfect_pixel.feature_scopes import build_scope
    from perfect_pixel.trigger_pipeline import center_sample, sample_scoped, source_palette

    with Image.open(source_path) as source_file:
        if source_file.mode != config["source_mode"]:
            raise ValueError("Capture must already be RGBA; no implicit mode conversion.")
        if list(source_file.size) != config["source_size"]:
            raise ValueError("Capture must be exactly 384x768; no resizing or cropping.")
        raw = np.array(source_file, dtype=np.uint8)
    if not np.isin(raw[..., 3], [0, 255]).all():
        raise ValueError("Existing sample_scoped requires binary alpha; capture without MSAA/AA. No automatic alpha threshold was applied.")
    if not np.any(raw[..., 3] == 0) or not np.any(raw[..., 3] == 255):
        raise ValueError("Capture must contain both the opaque model and transparent background.")
    original_pixels = hashlib.sha256(raw.tobytes()).hexdigest()
    grid = tuple(config["base_grid"])
    sampling_options = dict(config["cell_sampling"])
    scope_specification = sampling_options.pop("scope")
    scope = build_scope(raw.shape[:2], scope_specification, base_dir=folder)
    if sampling_options["method"] != "source_regions":
        raise ValueError("This review requires palette-independent source-region coordinates.")

    # Decide source ownership on untouched geometry/colors BEFORE recoloring.
    print("Selecting raw source-region coordinates...", flush=True)
    raw_sampled, source_xy = sample_scoped(
        raw, grid, scope, return_source_xy=True, source_guide=raw,
        **sampling_options)
    center = center_sample(raw, grid)
    coordinates_before = source_xy.copy()

    print("Applying the latest character pipeline's 64 observed-source colors...", flush=True)
    flat, palette_metadata = source_palette(raw, scope, **config["region_colors"])
    if flat.shape != raw.shape or not np.array_equal(flat[..., 3], raw[..., 3]):
        raise RuntimeError("flat_image must preserve original resolution and alpha.")

    # Use the latest character pipeline's source_palette, not the older SLIC
    # boundary experiment. Final placement uses only the fixed source coordinates.
    native = np.zeros((grid[1], grid[0], 4), np.uint8)
    valid = np.all(source_xy >= 0, axis=2)
    selected_xy = source_xy[valid]
    native[valid] = flat[selected_xy[:, 1], selected_xy[:, 0]]
    if not np.array_equal(source_xy, coordinates_before):
        raise RuntimeError("Color processing changed source coordinates.")
    if not np.array_equal(native[..., 3], raw_sampled[..., 3]):
        raise RuntimeError("Recoloring changed the previously chosen silhouette.")
    expected_shape = (384, 192, 4)
    if native.shape != expected_shape:
        raise RuntimeError("Native image does not match 192x384 RGBA.")
    # Essential provenance checks; these do not evaluate artistic quality.
    source_colors = set(map(tuple, np.unique(raw[..., :3][raw[..., 3] == 255], axis=0)))
    emitted_colors = np.unique(native[..., :3][native[..., 3] == 255], axis=0)
    if any(tuple(color) not in source_colors for color in emitted_colors):
        raise RuntimeError("An output RGB was not observed in the original source.")
    yy, xx = np.indices(native.shape[:2])
    if np.any(valid & ((source_xy[..., 0] < 2 * xx) | (source_xy[..., 0] >= 2 * xx + 2)
                       | (source_xy[..., 1] < 2 * yy) | (source_xy[..., 1] >= 2 * yy + 2))):
        raise RuntimeError("A chosen coordinate escaped its original 2x2 cell.")
    if hashlib.sha256(raw.tobytes()).hexdigest() != original_pixels or sha256(source_path) != source_hash:
        raise RuntimeError("Original source changed during processing.")
    if implementation_before != {rel: sha256(engine / rel) for rel in ENGINE_FILES}:
        raise RuntimeError("Engine changed during processing; refusing an ambiguous result.")
    if sha256(config_path) != config_hash or sha256(Path(__file__).resolve()) != script_hash:
        raise RuntimeError("Review configuration or runner changed during processing.")

    def enlarged(array):
        im = Image.fromarray(array)
        return im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST)

    preview = enlarged(native)
    center_preview = enlarged(center)
    panel_width, panel_height, margin, header = 384, 768, 16, 48
    comparison = Image.new("RGB", (3 * panel_width + 4 * margin, panel_height + 2 * margin + header), (245, 245, 245))
    draw = ImageDraw.Draw(comparison)
    font_path = Path("C:/Windows/Fonts/segoeui.ttf")
    font = ImageFont.truetype(str(font_path), 17) if font_path.exists() else ImageFont.load_default()
    panels = (("SOURCE 384 x 768", Image.fromarray(raw)),
              ("CENTER 192 x 384 / 2x", center_preview),
              ("REGIONS + PALETTE / 2x", preview))
    for index, (label, panel) in enumerate(panels):
        x, y = margin + index * (panel_width + margin), header
        draw.text((x, 14), label, fill=(25, 25, 25), font=font)
        for row in range(0, panel_height, 16):
            for col in range(0, panel_width, 16):
                shade = 230 if ((row + col) // 16) % 2 else 249
                draw.rectangle((x + col, y + row, x + col + 15, y + row + 15), fill=(shade,) * 3)
        comparison.paste(panel, (x, y), panel)

    output.mkdir()
    Image.fromarray(native).save(output / "pixel_native.png")
    preview.save(output / "pixel_preview_2x.png")
    Image.fromarray(center).save(output / "center_native.png")
    center_preview.save(output / "center_preview_2x.png")
    Image.fromarray(flat).save(output / "flat_source_palette_rgba.png")
    comparison.save(output / "comparison.png")
    np.savez_compressed(output / "processing_maps.npz", source_xy=source_xy)
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "input": {"path": str(source_path), "file_sha256": source_hash,
                  "pixel_sha256": original_pixels, "shape": list(raw.shape)},
        "runtime": {"python": sys.version, "executable": sys.executable,
                    "numpy": np.__version__, "pillow": PIL.__version__},
        "engine": {"path": str(engine), "file_sha256": implementation_before},
        "runner_sha256": script_hash,
        "config_sha256": config_hash,
        "effective_region_color_options": config["region_colors"],
        "final_sampling": {
            "public_api": "perfect_pixel.trigger_pipeline.sample_scoped",
            "source_guide": "unmodified_raw_RGBA_before_any_color_processing",
            "scope": scope_specification, "options": sampling_options,
            "order": ["raw source-region coordinate selection", "source_palette observed-color clustering at source resolution", "read palette image at frozen source coordinates"],
            "coordinate_map": "processing_maps.npz:source_xy",
            "native_grid": list(grid), "source_cell_size": [2, 2],
            "alpha_policy": "binary source alpha; >=50% opaque coverage wins; otherwise zero RGBA",
            "legacy_boundary_grid_output_used": False,
            "palette_rgb_count": len(emitted_colors)
        },
        "palette_stage_metadata": palette_metadata,
        "technical_checks": {"source_unchanged": True, "engine_unchanged": True,
                             "flat_preserves_original_shape_and_alpha": True,
                             "source_coordinates_fixed_before_color": True,
                             "coordinates_within_original_2x2_cell": True,
                             "alpha_silhouette_unchanged_by_color": True,
                             "native_192x384_RGBA": True,
                             "RGB_only_from_original_opaque_source": True},
        "limitations": ["64 colors is a global source palette, not semantic part segmentation or a three-tone material limit.",
                        "A 2x2 cell emits one selected source sample and cannot preserve every competing detail.",
                        "Color-connected regions are not guaranteed semantic material identities.",
                        "Capture lighting and framing are supplied by Unity and need source preview review."],
        "attempt_notes": ["The initially selected older boundary_pipeline rejected 4348 regions above its 4096 limit. No engine limit was changed and no failed output was accepted. The adapter was corrected to reuse source_palette and source_regions from the latest character source-guard review.", "No source-mask cleanup or line-first scopes from the unrelated anime image are reused."],
        "design_approval": "pending_user_review",
    }
    manifest["outputs"] = {path.name: {"sha256": sha256(path)}
                           for path in sorted(output.iterdir()) if path.is_file()}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"output": str(output), "native": "192x384 RGBA",
                      "comparison": str(output / "comparison.png"),
                      "design_approval": "pending_user_review"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
