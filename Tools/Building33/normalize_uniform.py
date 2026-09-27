"""B33 correction: common native pixel density, variable object canvases.

Fixtures are sampled with one aspect-preserving scale (floored to whole target
rows); their original shape is never stretched to an independently chosen height.
This fixes the earlier normalization contract, not the generated source geometry.
"""
from __future__ import annotations

import argparse
import json
import math
import time

import normalize_art as previous
from normalize_art import ROOT, ENGINE, FEATURES, np, Image, ImageDraw, sha, path_string

PPU = 32 * math.sqrt(2)
VERTICAL_PPM = PPU * math.cos(math.radians(30))
GROUND_VERTICAL_PPM = PPU * math.sin(math.radians(30)) / math.sqrt(2)
OUTPUT = ROOT / "Assets/Art/PlannedPixelBuilding33Uniform"
RECEIPTS = ROOT / "docs/artifacts/building33"


def make_spec(record):
    old = record["target"]
    name = record["id"]
    sw, sh = record["pre_normalization_crop_dimensions"]
    if "footprint_m" in old:
        width, depth = old["footprint_m"]
        max_width_exact = PPU * math.cos(math.radians(45)) * (width+depth)
        max_height_exact = GROUND_VERTICAL_PPM*(width+depth)+VERTICAL_PPM*old["visual_height_m"]
        max_width, max_height = math.floor(max_width_exact+1e-9), math.floor(max_height_exact+1e-9)
        scale = min(max_width/sw,max_height/sh)
        target_width = max(1,math.floor(sw*scale+1e-9))
        target_height = max(1,math.floor(sh*scale+1e-9))
        factor = target_width/max_width_exact
        actual_footprint = [width*factor,depth*factor]
        inferred = (target_height-GROUND_VERTICAL_PPM*sum(actual_footprint))/VERTICAL_PPM
        return {"grid": [target_width, target_height], "canvas": [target_width, target_height],
            "fixture_id": old["fixture_id"], "footprint_m": old["footprint_m"],
            "footprint_role": "reserved layout slot; not the inferred actual object footprint",
            "projected_envelope_exact_pixels": [max_width_exact,max_height_exact],
            "fit_bbox_max_pixels": [max_width,max_height], "uniform_source_scale": scale,
            "source_quantization_error_xy_pixels": [target_width-sw*scale,target_height-sh*scale],
            "actual_footprint_factor": factor, "inferred_actual_footprint_m": actual_footprint,
            "collider_height_m": old["collider_height_m"],
            "inferred_visual_height_m": inferred,
            "inferred_minus_collider_height_m": inferred-old["collider_height_m"],
            "height_status": "LIMITATION: bounding-box inference; not a corrected or verified physical height",
            "fit": "one minimum scale fits projected slot envelope; both axes floored to whole pixels",
            "bottom_margin": 0}
    if name in ("floor", "wall_left", "wall_right"):
        size = [v*2 for v in old["grid"]]
        return {"grid": size, "canvas": size, "bottom_margin": 0,
            "fit": "fixed canonical surface grid; generated source boundary is conformed explicitly"}
    # Lamp has no B32 footprint. Preserve its previous intended width in metres,
    # then derive height from its source instead of independently fixing both.
    width = old["grid"][0]*2
    size = [width, max(1,math.floor(width*sh/sw+1e-9))]
    return {"grid": size, "canvas": size, "bottom_margin": 0,
        "uniform_source_scale": width/sw,
        "source_quantization_error_xy_pixels": [0,size[1]-width*sh/sw],
        "fit": "one width scale, source-aspect height floored to an integer row",
        "physical_size_status": "no collider/footprint; width retains prior projected width in metres"}


def complete_surface_boundary(arr, desired, name):
    original = arr[..., 3] != 0
    missing = desired & ~original
    offsets = sorted((dx*dx+dy*dy, dy, dx) for dy in range(-6,7) for dx in range(-6,7)
                     if 0 < dx*dx+dy*dy <= 6**2)
    max_distance = 0.0
    for y, x in zip(*np.nonzero(missing)):
        # Only the border strip of the declared tile silhouette may be filled.
        near_boundary = any(not (0 <= y+dy < arr.shape[0] and 0 <= x+dx < arr.shape[1])
                            or not desired[y+dy,x+dx] for _,dy,dx in offsets)
        if not near_boundary:
            raise ValueError(f"{name}: missing interior pixel ({x},{y}); boundary fill prohibited")
        for squared_distance, dy, dx in offsets:
            ny, nx = y+dy, x+dx
            if 0 <= ny < arr.shape[0] and 0 <= nx < arr.shape[1] and original[ny,nx]:
                arr[y,x,:3] = arr[ny,nx,:3]
                max_distance = max(max_distance, math.sqrt(squared_distance))
                break
        else:
            raise ValueError(f"{name}: source/canonical boundary mismatch exceeds 6 pixels")
    arr[..., 3] = np.where(desired, 255, 0)
    arr[~desired] = 0
    return {"filled_boundary_cells": int(missing.sum()),
        "removed_outside_cells": int((original & ~desired).sum()),
        "max_source_boundary_distance_pixels": max_distance,
        "max_distance_world_metres": max_distance/PPU,
        "method": "existing sampled source RGB copied at canonical surface boundary only",
        "limit": "same 3 old-pixel border allowance at doubled native density; no new colors"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    old_path = RECEIPTS / "art-manifest.json"
    old = json.loads(old_path.read_text(encoding="utf-8"))
    specs = {a["id"]: make_spec(a) for a in old["assets"]}
    formula = {"shared_ppu": PPU,
        "width_max": "floor(P*cos(45deg)*(slotWidth+slotDepth))",
        "height_max": "floor(P*sin(30deg)/sqrt(2)*(slotWidth+slotDepth)+P*cos(30deg)*priorVisualHeight)",
        "uniform_scale": "q=min(widthMax/croppedSourceWidth,heightMax/croppedSourceHeight)",
        "fixture_size": "[max(1,floor(croppedSourceWidth*q)),max(1,floor(croppedSourceHeight*q))]",
        "integer_quantization": "each axis loses <1 native pixel; same q before quantization, not perfect continuous aspect equality",
        "canvas": "per-object native dimensions; no common 64x64 box",
        "display_requirement": "screenHeight / (2*orthographicSize*P) >= 2 and integer display quantization",
        "density_rationale": "doubles the existing 2:1 tile density to 128x64 per 2m tile; more source samples per object",
        "viewport_limit": "At prior 857px height and ortho5, raw scale is 1.89372, not >=2. Camera owner must establish the requested actual integer scale.",
        "source_limit": "generated internal slopes/heights are preserved, not certified exact CAD or exact source pixel clusters",
        "specifications": specs}
    if args.dry_run:
        print(json.dumps(formula, ensure_ascii=False, indent=2))
        return
    OUTPUT.mkdir(parents=True, exist_ok=True)
    work = ROOT / "LocalOnly/Building33/uniform-normalization"
    work.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "building33-uniform-art/1", "supersedes_contract_not_files": path_string(old_path),
        "original_manifest_sha256": sha(old_path), "engine": path_string(ENGINE), "features": FEATURES,
        "algorithm": "existing PerfectPixel modified source_regions; no palette, tone, line or redraw passes",
        "native_pixels_per_unit": PPU, "vertical_pixels_per_metre": VERTICAL_PPM,
        "contract": formula, "layout_source": old["layout_source"], "layout_sha256": old["layout_sha256"],
        "assets": [], "artistic_approval": "pending",
        "limitations": ["Uniform source fitting does not correct source perspective or object design.",
            "Reserved layout slots and inferred actual object footprints are separate; only the latter may derive collider width/depth.",
            "Inferred visual heights can differ from prior colliders; these differences are not passed as validated geometry.",
            "Source-region sampling can still remove details smaller than a native cell.",
            "Surface wall/floor masks remain an explicit canonical boundary constraint.",
            "Shared PPU does not by itself ensure integer screen pixels; the camera display path must do that separately."]}
    normalized = {}
    for record in old["assets"]:
        started = time.monotonic()
        name = record["id"]
        source = ROOT / record["preserved_source_path"]
        if sha(source) != record["original_sha256"]:
            raise ValueError(f"Preserved B33 source changed: {source}")
        output = OUTPUT / (name+".png")
        if output.exists():
            raise FileExistsError(f"Prior correction preserved: {output}")
        clean, crop, partial, removed, source_size = previous.prepare_source(source)
        spec = specs[name]
        target = spec["grid"]
        result = previous.normalize_triggered(clean, target, features=FEATURES)
        native = result["image"]
        coordinates = result["sampling_source_xy"]
        visible = native[...,3] != 0
        assert np.array_equal(native[visible,:3], clean[coordinates[...,1][visible], coordinates[...,0][visible], :3])
        desired = previous.canonical_mask(name, native.shape[:2])
        boundary = complete_surface_boundary(native, desired, name) if desired is not None else None
        image = Image.fromarray(native)
        image.save(output)
        normalized[name] = image
        np.savez_compressed(work/(name+"_coordinates.npz"), xy=coordinates, crop=np.array(crop))
        scale = spec.get("uniform_source_scale",target[0]/clean.shape[1])
        quantization_error = [target[0]-clean.shape[1]*scale,target[1]-clean.shape[0]*scale]
        item = {"id": name, "preserved_source_path": path_string(source), "original_sha256": sha(source),
            "original_dimensions": source_size, "crop_xyxy": crop,
            "pre_normalization_crop_dimensions": [clean.shape[1], clean.shape[0]],
            "alpha_threshold": 128, "partial_alpha_source_pixels": partial,
            "removed_remote_component_pixels": removed, "target": spec,
            "normalized_path": path_string(output), "normalized_dimensions": list(image.size),
            "visible_bbox_xyxy": list(image.getbbox()), "normalized_sha256": sha(output),
            "uniform_source_scale": scale, "quantization_error_xy_pixels": quantization_error,
            "target_aspect_over_source_aspect": (target[0]/target[1])/(clean.shape[1]/clean.shape[0]),
            "sampling": "PerfectPixel.source_regions; original sampled RGB equality checked before declared boundary completion",
            "boundary_correction": boundary, "seconds": round(time.monotonic()-started,3)}
        if name not in ("floor", "wall_left", "wall_right") and any(e > .000001 or e <= -1.000001 for e in quantization_error):
            raise ValueError(f"Independent axis fitting detected: {name}")
        if "actual_footprint_factor" in spec and not 0 < spec["actual_footprint_factor"] <= 1.000001:
            raise ValueError(f"Object exceeds reserved width: {name}")
        manifest["assets"].append(item)
        print(json.dumps({"id": name, "size": list(image.size), "quantization_error_xy_px": [round(e,4) for e in quantization_error]}), flush=True)
    atlas = Image.new("RGBA", (128,128))
    atlas.paste(normalized["wall_right"], (0,0))
    atlas.paste(normalized["wall_left"], (64,0))
    atlas_path = OUTPUT/"wall.png"
    if atlas_path.exists():
        raise FileExistsError(atlas_path)
    atlas.save(atlas_path)
    manifest["wall_atlas"] = {"path": path_string(atlas_path), "dimensions": [128,128], "sha256": sha(atlas_path),
        "halves": [{"x":0,"source_id":"wall_right","axis":"+X"}, {"x":64,"source_id":"wall_left","axis":"+Z"}]}
    sheet = Image.new("RGB", (1500,1560), (46,44,53))
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(normalized.items()):
        x, y = (index%3)*500, (index//3)*520
        draw.text((x+12,y+12), f"{name} {image.width}x{image.height}; preview x3", fill=(235,231,220))
        zoom = image.resize((image.width*3,image.height*3), Image.Resampling.NEAREST)
        sheet.paste(zoom, (x+20,y+38), zoom)
    preview = RECEIPTS/"uniform-art-contact-sheet-3x.png"
    sheet.save(preview)
    manifest["technical_preview"] = {"path":path_string(preview),"scale":3,"filter":"nearest preview only"}
    manifest["total_engine_and_save_seconds"] = sum(a["seconds"] for a in manifest["assets"])
    (RECEIPTS/"uniform-art-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Uniform art output and manifest saved.",flush=True)


if __name__ == "__main__":
    main()
