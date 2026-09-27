"""Prepare five new flat details; preserve the approved B35 outputs and inputs.

Run once from the production graph. This is physical reprojection after automatic
PerfectPixel normalization, not another normalization or a lossless conversion.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/artifacts/building35"
PPU = 127
ALPHA_CUTOFF = 0.1


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deps", type=Path, default=ROOT / "LocalOnly/PerfectPixelPalette_20260906/.deps")
    args = parser.parse_args()
    sys.path.insert(0, str(args.deps.resolve(strict=True)))
    import numpy as np
    from PIL import Image
    from project_faces import R, U, homography, transform

    output = BASE / "details"
    planned_outputs = [output / f"detail_{name}" for name in ("ledger", "clock", "poster", "broom", "bin")]
    planned_outputs.append(output / "production-manifest.json")
    existing = [str(path) for path in planned_outputs if path.exists()]
    if existing:
        raise FileExistsError(f"Preserve existing detail outputs: {existing}")
    landmarks = json.loads((BASE / "details-landmarks.json").read_text(encoding="utf-8-sig"))
    wall_sources = {a["id"]: a for a in landmarks["assets"]}
    unit = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
    jobs = [("ledger", "top_ledger", "XZ"), ("clock", "front_clock", "XY"),
            ("poster", "front_poster", "ZY"), ("broom", "front_broom", "ZY"),
            ("bin", "bin", "upright_2d")]
    prepared = []
    for asset_id, source_id, plane in jobs:
        source = BASE / "details-native" / source_id / "native.png"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        normalization = json.loads((source.parent / "receipt.json").read_text(encoding="utf-8-sig"))
        if normalization["status"] != "normalized" or normalization["output_sha256"] != digest:
            raise ValueError(f"Normalized source receipt differs: {source_id}")
        with Image.open(source) as image:
            if image.mode != "RGBA":
                raise ValueError(f"Expected unconverted RGBA source: {source_id}")
            pixels = np.array(image)
        ys, xs = np.where(pixels[..., 3] / 255.0 > ALPHA_CUTOFF)
        if not len(xs):
            raise ValueError(f"No visible source pixels: {source_id}")
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        if source_id in wall_sources:
            a = wall_sources[source_id]
            if digest != a["native_sha256"] or bbox != a["outer_bbox"]:
                raise ValueError(f"Wall source changed after landmark observation: {source_id}")
        left, top, right, bottom = [v - .5 for v in bbox]
        sw, sh = right - left, bottom - top
        reference = np.array([[left, top], [right, top], [right, bottom], [left, bottom]])
        if asset_id == "ledger":
            width, height = .38, .38 * sh / sw
            vertices = np.array([[-width/2, .02, height/2], [width/2, .02, height/2],
                                 [width/2, .02, -height/2], [-width/2, .02, -height/2]])
        elif asset_id == "clock":
            width, height = .34, .34 * sh / sw
            vertices = np.array([[-width/2, height, 0], [width/2, height, 0],
                                 [width/2, 0, 0], [-width/2, 0, 0]])
        elif asset_id in ("poster", "broom"):
            width, height = (.36, .48) if asset_id == "poster" else (1.20 * sw / sh, 1.20)
            vertices = np.array([[0, height, width/2], [0, height, -width/2],
                                 [0, 0, -width/2], [0, 0, width/2]])
        else:
            height = .45
            width = height * math.sqrt(.75) * sw / sh
            start, along = R * (-width/2), R * width
            vertices = np.array([start + [0, height, 0], start + along + [0, height, 0],
                                 start + along, start])
        source_h, source_w = pixels.shape[:2]
        canvas = np.array([[-.5, -.5], [source_w-.5, -.5],
                           [source_w-.5, source_h-.5], [-.5, source_h-.5]])
        uv = transform(homography(reference, unit), canvas)
        full_vertices = vertices[0] + uv[:, :1] * (vertices[1]-vertices[0]) + uv[:, 1:] * (vertices[3]-vertices[0])
        prepared.append((f"detail_{asset_id}", source_id, source, digest, pixels, bbox, reference,
                         canvas, vertices, full_vertices, plane, width, height))

    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for asset_id, source_id, source, digest, pixels, bbox, reference, canvas, vertices, full_vertices, plane, width, height in prepared:
        folder = output / asset_id
        folder.mkdir()
        target = np.column_stack((full_vertices @ R, -full_vertices @ U)) * PPU
        origin = np.floor(target.min(0)) - 2
        extent = np.ceil(target.max(0)) + 2
        out_w, out_h = (extent - origin).astype(int)
        yy, xx = np.indices((out_h, out_w))
        q = np.stack([xx + .5, yy + .5], axis=-1)
        target -= origin
        inverse = homography(target, canvas)
        sq = transform(inverse, q)
        source_h, source_w = pixels.shape[:2]
        inside = (sq[..., 0] >= -.5) & (sq[..., 0] < source_w-.5) & (sq[..., 1] >= -.5) & (sq[..., 1] < source_h-.5)
        sx = np.clip(np.rint(sq[..., 0]).astype(int), 0, source_w-1)
        sy = np.clip(np.rint(sq[..., 1]).astype(int), 0, source_h-1)
        rgba = np.zeros((out_h, out_w, 4), np.uint8)
        rgba[inside] = pixels[sy[inside], sx[inside]]
        visible = inside & (rgba[..., 3] / 255.0 > ALPHA_CUTOFF)
        if not visible.any():
            raise ValueError(f"No visible samples after physical reprojection: {asset_id}")
        uv = transform(homography(reference, unit), sq)
        positions = vertices[0] + uv[..., :1] * (vertices[1]-vertices[0]) + uv[..., 1:] * (vertices[3]-vertices[0])
        xyz = np.zeros((out_h, out_w, 4), np.float32)
        xyz[visible, :3] = positions[visible]
        xyz[visible, 3] = 1
        Image.fromarray(rgba).save(folder / "native.png")
        np.flipud(xyz).astype("<f4").tofile(folder / "positions.rgba32f")
        Image.fromarray(visible.astype(np.uint8)).save(folder / "face-id.png")
        relative_source = source.relative_to(ROOT).as_posix()
        spec = {"id": asset_id, "source_id": source_id, "source": relative_source, "ppu": PPU,
                "source_bbox_alpha_gt_0p1": bbox, "physical_width_m": width, "physical_height_or_depth_m": height,
                "plane": plane, "faces": [{"id": plane, "source_xy": reference.tolist(), "xyz": vertices.tolist()}],
                "full_canvas_source_xy": canvas.tolist(), "full_canvas_xyz": full_vertices.tolist(),
                "alpha_policy": "Sample source RGBA unchanged; depth.valid only when sampled alpha/255 > 0.1",
                "sampling": "One nearest source sample per canonical output texel; no image crop, palette change or alpha cleanup"}
        save_json(folder / "spec.json", spec)
        receipt = {"id": asset_id, "source": relative_source, "source_sha256": digest,
                   "width": int(out_w), "height": int(out_h), "ppu": PPU,
                   "left": float(origin[0]/PPU), "top": float(-origin[1]/PPU),
                   "opaque_pixels": int(visible.sum()), "alpha_cutoff": ALPHA_CUTOFF,
                   "faces": [{"id": plane, "written_pixels": int(visible.sum()),
                              "reprojection_residual": float(np.abs(transform(inverse, target)-canvas).max()), "holdout": []}],
                   "support_height": .02 if asset_id == "detail_ledger" else 0.0,
                   "surface_xyz_min": xyz[visible, :3].min(0).tolist(), "surface_xyz_max": xyz[visible, :3].max(0).tolist(),
                   "ground_shift_from_measured_outline_m": 0.0,
                   "outline_policy": "Full source canvas on the declared plane; visible bbox fixes physical size and anchor",
                   "spec": str(folder / "spec.json"),
                   "declared_limitations": ["Physical resampling is separate from prior PerfectPixel automatic normalization.",
                                             "Nearest sampling may omit or duplicate input texels; no complete feature preservation claim.",
                                             "Flat artwork, including clock shape and bin view, is not recovered 3D geometry."]}
        save_json(folder / "receipt.json", receipt)
        manifest.append({"id": asset_id, "source_id": source_id, "folder": folder.relative_to(ROOT).as_posix(),
                         "receipt": (folder / "receipt.json").relative_to(ROOT).as_posix()})
    save_json(output / "production-manifest.json", {"schema": "building35-details-manifest/1", "ppu": PPU,
                                        "alpha_cutoff": ALPHA_CUTOFF, "assets": manifest})
    print(json.dumps({"status": "prepared", "manifest": str(output / "production-manifest.json"), "asset_count": len(manifest)}))


if __name__ == "__main__":
    main()
