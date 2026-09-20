"""Export the reviewed D21 desk for a Unity image/geometry lighting comparison.

This copies the finished image as an explicitly baked control. The other texture
is strictly palette[grain], never the finished desk or its shade bands. Existing
outputs are immutable: an identical invocation reuses them, any difference stops.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "LocalOnly/PixelPipeline21/run01"
PASS = RUN / "pass-2"
CONTRACT = ROOT / "Tools/PixelPipeline/desk_contract.json"
# Bound to the actual headless Blender inspection on 2026-09-20, not a generic
# claim that an arbitrary blend file can be replaced by twelve cubes.
AUDITED_BLEND_SHA256 = "df98e0b68639865dc9f8051176c6036e3eef7a59b776601cdc4a0553323898b6"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def png_bytes(pixels: np.ndarray) -> bytes:
    stream = io.BytesIO()
    Image.fromarray(pixels).save(stream, format="PNG")
    return stream.getvalue()


def build() -> tuple[dict[str, bytes], dict]:
    sources = {
        "contract": CONTRACT,
        "geometry_spec": PASS / "raster/raster.json",
        "geometry_blend": PASS / "package/desk.blend",
        "baked_control": PASS / "pixel/desk.png",
        "grain_indices": RUN / "material/grain.npy",
        "grain_palette": RUN / "material/palette.json",
        "material_receipt": RUN / "material/receipt.json",
        "geometry_edges": PASS / "pixel/edges.npz",
    }
    source_bytes = {key: path.read_bytes() for key, path in sources.items()}
    hashes = {key: digest(data) for key, data in source_bytes.items()}
    if hashes["geometry_blend"] != AUDITED_BLEND_SHA256:
        raise ValueError("Geometry changed since the actual twelve-box Blender audit")
    contract = read_json(CONTRACT)
    raster = read_json(sources["geometry_spec"])
    receipt = read_json(sources["material_receipt"])
    for name, key in (("grain.npy", "grain_indices"), ("palette.json", "grain_palette")):
        if hashes[key] != receipt["output_sha256"][name]:
            raise ValueError(f"Material provenance mismatch: {name}")
    if receipt["source_sha256"] != contract["source_wood_sha256"]:
        raise ValueError("Approved wood provenance differs from the D21 contract")

    parts = raster["parts"]
    if len(parts) != 12 or sorted(part["id"] for part in parts) != list(range(12)):
        raise ValueError("Expected the twelve reviewed D21 parts")
    exported_parts = []
    for part in parts:
        center = np.asarray(part["center"], dtype=float)
        dimensions = np.asarray(part["dimensions"], dtype=float)
        low, high = np.asarray(part["minimum"]), np.asarray(part["maximum"])
        if not all(np.isfinite(v).all() and v.shape == (3,) for v in (center, dimensions, low, high)):
            raise ValueError(f"Invalid geometry: {part['name']}")
        if np.any(dimensions <= 0) or not np.allclose(high-low, dimensions, atol=1e-6, rtol=0):
            raise ValueError(f"Inconsistent bounds: {part['name']}")
        if not np.allclose((low+high)/2, center, atol=1e-6, rtol=0):
            raise ValueError(f"Inconsistent center: {part['name']}")
        exported_parts.append({**part, "unity_center": center[[0, 2, 1]].tolist(),
                               "unity_dimensions": dimensions[[0, 2, 1]].tolist()})

    grain = np.load(io.BytesIO(source_bytes["grain_indices"]), allow_pickle=False)
    palette = np.asarray(read_json(sources["grain_palette"])["colors_srgb8"], dtype=np.uint8)
    if grain.shape != (64, 66) or grain.dtype != np.uint8 or palette.shape != (4, 3):
        raise ValueError("Unexpected material dimensions or index type")
    if set(np.unique(grain).tolist()) != {0, 1, 2, 3}:
        raise ValueError("Expected four material indices")
    wood = palette[grain]
    with Image.open(io.BytesIO(source_bytes["baked_control"])) as image:
        width, height = image.size
        if (width, height) != tuple(raster["size"]) or (width, height) != (174, 155):
            raise ValueError("Final image and geometry raster dimensions disagree")
    with np.load(io.BytesIO(source_bytes["geometry_edges"]), allow_pickle=False) as edge_file:
        edges = edge_file["edges"]
    if edges.shape != (height, width) or edges.dtype != np.bool_:
        raise ValueError("Geometry edge cache has the wrong dimensions or type")
    edge_rgba = np.repeat((edges.astype(np.uint8)*255)[..., None], 4, axis=2)

    camera = raster["camera"]
    phi, theta = np.radians([camera["azimuth_degrees"], camera["elevation_degrees"]])
    right = np.array([np.cos(phi), np.sin(phi), 0.0])
    up = np.array([-np.sin(phi)*np.sin(theta), np.cos(phi)*np.sin(theta), np.cos(theta)])
    toward_camera = np.cross(right, up)
    ppu = raster["pixels_per_meter"]
    origin = np.asarray(raster["screen_origin"], dtype=float)
    # raster screen is (r dot p, -u dot p), both in pixel units.
    center_screen = origin + np.array([width, height])/2
    center_canonical = right*(center_screen[0]/ppu) - up*(center_screen[1]/ppu)
    provenance = {
        "sources": {key: {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                          "sha256": hashes[key]} for key, path in sources.items()},
        "approved_wood_source_sha256": receipt["source_sha256"],
        "wood_computation": "colors_srgb8[grain_indices]; no shade-band input",
        "pure_albedo_proven": False,
        "albedo_limit": "Source color variation is preserved; no de-lighting or intrinsic-image separation was performed.",
        "blend_audit": {"mode": "actual headless Blender read on 2026-09-20",
                        "blender_version": "5.2.0 LTS", "sha256": AUDITED_BLEND_SHA256,
                        "mesh_count": 12, "each_mesh_vertices": 8, "each_mesh_quad_faces": 6,
                        "maximum_world_box_corner_error_m": 0.0,
                        "material_count": 0, "material_slot_count": 0, "light_count": 0,
                        "parents_modifiers_constraints": 0,
                        "scope": "This exact audited blend only; exporter does not invoke Blender again."},
    }
    spec = {
        "schema": 1,
        "canonical": {"units": "meters", "x": "right", "y": "back", "z": "up"},
        "unity_mapping": {"formula": "(x,y,z)_canonical -> (x,z,y)_Unity",
                          "matrix": [[1, 0, 0], [0, 0, 1], [0, 1, 0]], "determinant": -1,
                          "triangle_winding": "Reverse if transforming original triangle indices; native Unity cubes already have native winding."},
        "parts": exported_parts,
        "camera": {"r": right.tolist(), "u": up.tolist(), "d": toward_camera.tolist(),
                   "d_meaning": "toward camera; primary ray direction is -d",
                   "screen_origin": origin.tolist(), "width": width, "height": height, "ppu": ppu,
                   "azimuth_degrees": camera["azimuth_degrees"], "elevation_degrees": camera["elevation_degrees"],
                   "projection": "screen=(ppu*dot(r,p), -ppu*dot(u,p))-screen_origin; pixel centers=(x+0.5,y+0.5)",
                   "image_origin": "top-left", "bounds_center_canonical": center_canonical.tolist(),
                   "bounds_center_unity": center_canonical[[0, 2, 1]].tolist(),
                   "orthographic_half_height_m": height/(2*ppu)},
        "material": {"file": "wood-grain.png", "width": 66, "height": 64,
                     "colors_srgb8": palette.tolist(), "texel_meters": contract["material"]["texel_meters"],
                     "semantics": "material variation, not desk lighting", "filter": "Point",
                     "mipmaps": False, "compression": "None", "srgb": True,
                     "texture_address": "Repeat; image rows down; grain[floor(-v) mod 64, floor(u) mod 66]"},
        "image_control": {"file": "desk.png", "baked_lighting": True, "copy_bytes_unchanged": True,
                          "filter": "Point", "mipmaps": False, "compression": "None"},
        "edges": {"file": "edge-mask.png", "type": "geometry-derived fixed-view binary mask",
                  "contains_shaded_rgb": False, "rgba_channels": "all equal, 0 or 255",
                  "outline_srgb8": contract["pixel"]["outline_srgb8"],
                  "view_limit": "Only the recorded canonical geometry and camera basis; arbitrary rotation is unsupported."},
        "reference_lighting": contract["lighting"],
        "geometry_file": "input.blend", "provenance": provenance,
    }
    files = {"desk.png": source_bytes["baked_control"], "input.blend": source_bytes["geometry_blend"],
             "wood-grain.png": png_bytes(wood), "edge-mask.png": png_bytes(edge_rgba),
             "spec.json": (json.dumps(spec, ensure_ascii=False, indent=2, allow_nan=False)+"\n").encode("utf-8")}
    return files, provenance


def prepare(output: Path) -> dict:
    output = output.resolve()
    files, provenance = build()
    expected = {name: digest(data) for name, data in files.items()}
    reused = output.exists()
    if reused:
        if not output.is_dir() or {p.name for p in output.iterdir()} != set(files):
            raise ValueError("Existing output inventory differs; use a fresh output directory")
        if any(digest((output/name).read_bytes()) != expected[name] for name in files):
            raise ValueError("Existing output bytes differ; immutable export was not overwritten")
    else:
        output.mkdir(parents=True, exist_ok=False)
        for name, data in files.items():
            (output/name).write_bytes(data)
    return {"success": True, "reused": reused, "output": str(output),
            "artifacts": {name: {"path": str(output/name), "sha256": expected[name]} for name in files},
            "provenance": provenance}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.output)
    except Exception as error:
        print(json.dumps({"success": False, "state": "blocked", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
