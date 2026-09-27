"""Normalize B33 generated sources with the existing PerfectPixel source_regions engine.

No generated source is redrawn or resized before region sampling. Output grid sizes
come from B32 metres and the shared isometric projection. Nonuniform source-to-grid
fitting is explicit in the manifest; it is not proof of exact interior projection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "LocalOnly/PerfectPixelPalette_20260906"
for directory in (ENGINE / ".deps", ENGINE / "src"):
    sys.path.insert(0, str(directory))
import numpy as np
from PIL import Image, ImageDraw
from perfect_pixel.trigger_pipeline import normalize_triggered

DEFAULT_INPUT = Path("C:/Users/JG/.codex/generated_images/01a08c0e-bbf2-7d10-b1e8-607c2c27f6d3")
SOURCES = {
    "counter": "exec-0abc651c-0240-4565-8d78-49bcb8a19d97.png",
    "rear_shelf": "exec-31a7091f-a3fa-4079-8254-6d29f8f48041.png",
    "left_shelf": "exec-ec6cc212-f2f6-4fee-923c-5c7b8856e36b.png",
    "island": "exec-505e0ee1-e019-42dc-a70f-dc688143d5e7.png",
    "stock_shelf": "exec-923639a4-6a17-4a2b-b714-e4b81b88edae.png",
    "floor": "exec-3796f5cf-08c6-4bdb-856d-fbea42bcc8b2.png",
    "wall_left": "exec-a0da5352-7dbf-476a-bbf1-0f2df68c0dfb.png",
    "wall_right": "exec-08022e00-1fa7-463e-ab35-4130641ae3b3.png",
    "lamp": "exec-de422893-21a3-4a5f-95df-ea0a0cf20171.png",
}
FIXTURE_NAMES = {"checkout": "counter", "display_island": "island"}
PPU = 16 * math.sqrt(2)
VERTICAL_PPM = PPU * math.cos(math.radians(30))
FEATURES = {"cell_sampling": {"enabled": True, "scope": {"kind": "all"},
    "options": {"method": "source_regions", "coverage": .5, "color_edge_threshold": .08}}}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_string(path):
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def prepare_source(source):
    arr = np.array(Image.open(source).convert("RGBA"))
    partial = int(((arr[..., 3] != 0) & (arr[..., 3] != 255)).sum())
    arr[..., 3] = np.where(arr[..., 3] >= 128, 255, 0)
    components = mask_components(arr[..., 3] != 0)
    if not components:
        raise ValueError(f"No opaque source: {source}")
    principal = max(components, key=lambda c: c["size"])
    # Only tiny disconnected marks outside a margin around the main object are
    # removed; disconnected details near the actual object stay intact.
    margin = max(2, round(max(arr.shape[:2]) * .01))
    x0, y0, x1, y1 = principal["box"]
    box = (x0-margin, y0-margin, x1+margin, y1+margin)
    removed = 0
    for component in components:
        if component is principal or component["size"] > principal["size"] * .001:
            continue
        x0, y0, x1, y1 = component["box"]
        remote = x1 < box[0] or x0 > box[2] or y1 < box[1] or y0 > box[3]
        if remote:
            for y, x0, x1 in component["runs"]:
                arr[y, x0:x1, 3] = 0
            removed += component["size"]
    yy, xx = np.nonzero(arr[..., 3])
    crop = [int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)]
    clean = arr[crop[1]:crop[3], crop[0]:crop[2]].copy()
    clean[clean[..., 3] == 0] = 0
    return clean, crop, partial, removed, [arr.shape[1], arr.shape[0]]


def mask_components(mask):
    """8-connected run-length union/find; no optional image library required."""
    parents, runs, previous = [], [], []
    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index
    for y, row in enumerate(mask):
        edges = np.diff(np.pad(row.astype(np.int8), (1, 1)))
        starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
        current = []
        for x0, x1 in zip(starts, ends):
            index = len(parents); parents.append(index)
            runs.append((y, int(x0), int(x1))); current.append(index)
            for prior in previous:
                _, p0, p1 = runs[prior]
                if p1 < x0:
                    continue
                if p0 > x1:
                    break
                parents[find(index)] = find(prior)
        previous = current
    groups = {}
    for index, run in enumerate(runs):
        owner = find(index)
        groups.setdefault(owner, []).append(run)
    return [{"runs": items, "size": sum(x1-x0 for y,x0,x1 in items),
        "box": [min(x0 for y,x0,x1 in items), min(y for y,x0,x1 in items),
                max(x1 for y,x0,x1 in items), max(y for y,x0,x1 in items)+1]}
        for items in groups.values()]


def canonical_mask(name, shape):
    h, w = shape
    x, y = np.meshgrid(np.arange(w)+.5, np.arange(h)+.5)
    if name == "floor":
        return np.abs(x-w/2)/(w/2)+np.abs(y-h/2)/(h/2) <= 1
    u, v = x/w, 1-y/h
    # Names describe atlas halves consumed by the builder. Source names are
    # separately recorded because the generated image labels face the other way.
    if name == "wall_right":  # Source slopes up to the right; atlas half 0, +X.
        return (v >= .25*u) & (v <= .75+.25*u)
    if name == "wall_left":  # Source slopes down to the right; atlas half 1, +Z.
        return (v >= .25*(1-u)) & (v <= 1-.25*u)
    return None


def complete_boundary(arr, desired, name):
    original = arr[..., 3] != 0
    missing = desired & ~original
    max_distance = 0.0
    offsets = sorted((dx*dx+dy*dy, dy, dx) for dy in range(-3,4) for dx in range(-3,4)
                     if 0 < dx*dx+dy*dy <= 3**2)
    # This is a raster boundary correction only, not semantic inpainting.
    for y, x in zip(*np.nonzero(missing)):
        for square_distance, dy, dx in offsets:
            ny, nx = y+dy, x+dx
            if 0 <= ny < arr.shape[0] and 0 <= nx < arr.shape[1] and original[ny,nx]:
                arr[y,x,:3] = arr[ny,nx,:3]
                max_distance = max(max_distance, math.sqrt(square_distance))
                break
        else:
            raise ValueError(f"{name}: canonical coverage requires interior repair at ({x},{y}), not a <=3px boundary fix")
    arr[..., 3] = np.where(desired, 255, 0)
    arr[~desired] = 0
    return {"filled_boundary_cells": int(missing.sum()), "removed_outside_cells": int((original & ~desired).sum()),
            "max_source_boundary_distance_pixels": max_distance, "method": "nearest existing sampled RGB, no color blend"}


def main():
    raise RuntimeError("B33_FORCED_GRID_RETIRED: source pixel detection was bypassed. Use native_normalize.py; preserved outputs are rejected history.")


def _retired_main_for_reference():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--replace", action="store_true", help="Explicitly replace this script's prior outputs; original copies must match hashes")
    args = parser.parse_args()
    source_folder = ROOT / "Tools/Building33/Source"
    out_folder = ROOT / "Assets/Art/PlannedPixelBuilding33"
    receipts = ROOT / "docs/artifacts/building33"
    work = ROOT / "LocalOnly/Building33/normalization"
    for folder in (source_folder, out_folder, receipts, work):
        folder.mkdir(parents=True, exist_ok=True)
    plan_path = ROOT / "docs/artifacts/building32/layout-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    specifications = {}
    for fixture in plan["fixtures"]:
        x0, z0, x1, z1 = fixture["rect_xz"]
        name = FIXTURE_NAMES.get(fixture["id"], fixture["id"])
        visual_height = {"counter": 1.6, "island": 1.25}.get(name, fixture["height_m"])
        target = [round(16*(x1-x0+z1-z0)), min(64, round(8*(x1-x0+z1-z0)+VERTICAL_PPM*visual_height))]
        specifications[name] = {"grid": target, "canvas": [64, 64], "bottom_margin": 0,
            "fixture_id": fixture["id"], "footprint_m": [x1-x0, z1-z0], "collider_height_m": fixture["height_m"],
            "visual_height_m": visual_height}
    for name, size in (("floor", [64, 32]), ("wall_left", [32, 64]), ("wall_right", [32, 64]), ("lamp", [16, 24])):
        specifications[name] = {"grid": size, "canvas": size, "bottom_margin": 0}
    manifest = {"schema": "building33-art/1", "source_kind": "generated individual object images",
        "engine": path_string(ENGINE), "engine_source_sha256": sha(ENGINE/"src/perfect_pixel/trigger_pipeline.py"),
        "sampling_source_sha256": sha(ENGINE/"src/perfect_pixel/source_sampling.py"),
        "engine_selection": "Tools/PerfectPixelWeb/app.py existing fallback; Desktop PerfectPixel-Web/engine absent",
        "algorithm": "PerfectPixel modified normalize_triggered: cell_sampling.source_regions only",
        "features": FEATURES, "native_pixels_per_unit": PPU, "vertical_pixels_per_metre": VERTICAL_PPM,
        "layout_source": path_string(plan_path), "layout_sha256": sha(plan_path), "assets": [],
        "limitations": ["Source art has generated baked material shading; no normal/depth map is inferred.",
            "Metric bounding-box fitting does not make generated internal edges exact CAD or identical projection.",
            "Nonuniform source-to-grid fitting is disclosed per asset.",
            "Source-region selection preserves chosen source RGB, not every fine source feature.",
            "No art/style approval is inferred from dimensions or technical checks."]}
    normalized = {}
    for name, filename in SOURCES.items():
        started = time.monotonic()
        original = args.source_root / filename
        copied = source_folder / (name+".png")
        if copied.exists() and sha(copied) != sha(original):
            raise FileExistsError(f"Preserved source differs: {copied}")
        if not copied.exists():
            shutil.copy2(original, copied)
        output = out_folder / (name+".png")
        if output.exists() and not args.replace:
            raise FileExistsError(f"Existing output preserved: {output}")
        clean, crop, partial, removed, source_size = prepare_source(copied)
        crop_file = work / (name+"_crop.png")
        Image.fromarray(clean).save(crop_file)
        spec = specifications[name]
        result = normalize_triggered(clean, spec["grid"], features=FEATURES)
        native = result["image"]
        # Source-coordinate receipts allow the no-recolor contract to be audited.
        sampling = result["sampling_source_xy"]
        valid = native[..., 3] != 0
        assert np.array_equal(native[valid, :3], clean[sampling[...,1][valid], sampling[...,0][valid], :3])
        boundary = None
        desired = canonical_mask(name, native.shape[:2])
        if desired is not None:
            boundary = complete_boundary(native, desired, name)
        canvas = Image.new("RGBA", tuple(spec["canvas"]))
        offset = [(spec["canvas"][0]-spec["grid"][0])//2, spec["canvas"][1]-spec["grid"][1]-spec["bottom_margin"]]
        canvas.paste(Image.fromarray(native), tuple(offset))
        canvas.save(output)
        normalized[name] = canvas
        np.savez_compressed(work/(name+"_source_coordinates.npz"), xy=sampling, crop=np.array(crop))
        source_aspect = clean.shape[1]/clean.shape[0]
        target_aspect = spec["grid"][0]/spec["grid"][1]
        fit_ratio = target_aspect/source_aspect
        record = {"id": name, "original_external_path": str(original), "preserved_source_path": path_string(copied),
            "original_sha256": sha(copied), "original_dimensions": source_size, "crop_xyxy": crop,
            "pre_normalization_crop_dimensions": [clean.shape[1], clean.shape[0]], "alpha_threshold": 128,
            "partial_alpha_source_pixels": partial, "removed_remote_component_pixels": removed,
            "target": spec, "canvas_placement_xy": offset, "normalized_path": path_string(output),
            "normalized_dimensions": list(canvas.size), "normalized_sha256": sha(output),
            "source_to_grid_scale_xy": [spec["grid"][0]/clean.shape[1], spec["grid"][1]/clean.shape[0]],
            "target_aspect_over_source_aspect": fit_ratio, "fit": "nonuniform bounding rectangle grid" if abs(fit_ratio-1)>.01 else "approximately uniform bounding rectangle grid",
            "rgb_contract": "all visible RGB values select existing source samples; no palette/tone/repaint pass",
            "boundary_correction": boundary, "seconds": round(time.monotonic()-started, 3)}
        manifest["assets"].append(record)
        print(json.dumps({"id": name, "size": list(canvas.size), "content_grid": spec["grid"], "aspect_ratio_change": round(fit_ratio, 4), "seconds": record["seconds"]}), flush=True)
    atlas_path = out_folder / "wall.png"
    if atlas_path.exists() and not args.replace:
        raise FileExistsError(f"Existing atlas preserved: {atlas_path}")
    atlas = Image.new("RGBA", (64, 64))
    atlas.paste(normalized["wall_right"], (0, 0))
    atlas.paste(normalized["wall_left"], (32, 0))
    atlas.save(atlas_path)
    manifest["wall_atlas"] = {"path": path_string(atlas_path), "dimensions": [64,64], "sha256": sha(atlas_path),
        "halves": [{"x": 0, "source_id": "wall_right", "axis": "+X", "uv_mask": ".25*u <= v <= .75+.25*u"},
            {"x": 32, "source_id": "wall_left", "axis": "+Z", "uv_mask": ".25*(1-u) <= v <= 1-.25*u"}],
        "explanation": "Source names follow generated visual orientation; atlas maps matching slopes without flipping pixels."}
    sheet = Image.new("RGB", (960, 864), (46, 44, 53))
    draw = ImageDraw.Draw(sheet)
    for index, (name, img) in enumerate(normalized.items()):
        x, y = (index%3)*320, (index//3)*288
        draw.text((x+10, y+9), f"{name}  {img.width}x{img.height}  preview x4", fill=(235,231,220))
        zoom = img.resize((img.width*4, img.height*4), Image.Resampling.NEAREST)
        sheet.paste(zoom, (x+32, y+28), zoom)
    sheet.save(receipts/"art-contact-sheet-4x.png")
    manifest["technical_preview"] = {"path": path_string(receipts/"art-contact-sheet-4x.png"), "scale": 4,
        "filter": "nearest, preview only; this file is not a game asset"}
    (receipts/"art-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Saved art-manifest.json and technical contact sheet", flush=True)


if __name__ == "__main__":
    main()
