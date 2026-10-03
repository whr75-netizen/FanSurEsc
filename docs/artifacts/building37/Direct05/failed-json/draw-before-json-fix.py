"""Direct native-grid cabinet drawing from geometry and material rules, not image filtering."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
RECIPE = Path(__file__).with_name("cabinet_recipe.json")
OUT = ROOT / "docs/artifacts/building37/Direct05"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def record(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def recipe():
    r = json.loads(RECIPE.read_text(encoding="utf-8"))
    if r["schema"] != "native-pixel-cabinet/1" or any(type(v) is not int or v <= 0 for v in r["canvas"] + r["size_ticks"]):
        raise ValueError("Invalid native drawing contract.")
    if sha((ROOT / r["reference"]).read_bytes()) != r["reference_sha256"]:
        raise ValueError("The preserved reference changed.")
    return r


def project(r, x, y, z):
    return np.array([r["origin"][0] + 2*x - 2*z, r["origin"][1] - x - z - y], float)


def quantize(p):
    return tuple(np.floor(np.asarray(p) + .5).astype(int))


def polygon(r, vertices):
    w, h = r["canvas"]
    points = np.asarray([quantize(p) for p in vertices], float)
    area = sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(points, np.roll(points, -1, axis=0)))
    if area < 0:
        points = points[::-1]
    yy, xx = np.mgrid[:h, :w]
    inside = np.ones((h, w), bool)
    for a, b in zip(points, np.roll(points, -1, axis=0)):
        dx, dy = b - a
        cross = dx*(yy+.5-a[1]) - dy*(xx+.5-a[0])
        inclusive = dy < 0 or (dy == 0 and dx > 0)
        inside &= (cross > 0) | ((cross == 0) & inclusive)
    return inside


def line(a, b):
    """Integer, non-AA Bresenham with one point per major-axis position."""
    x0, y0 = a
    x1, y1 = b
    dx, dy = abs(x1-x0), -abs(y1-y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    error = dx + dy
    result = []
    while True:
        result.append((int(x0), int(y0)))
        if x0 == x1 and y0 == y1:
            return result
        e2 = 2*error
        if e2 >= dy:
            error += dy
            x0 += sx
        if e2 <= dx:
            error += dx
            y0 += sy


def bezier(points, tolerance=.125, depth=0):
    p = np.asarray(points, float)
    chord = p[3]-p[0]
    length = np.linalg.norm(chord)
    error = (max(abs(chord[0]*(q[1]-p[0, 1])-chord[1]*(q[0]-p[0, 0]))/length for q in p[1:3]) if length
             else max(np.linalg.norm(q-p[0]) for q in p[1:3]))
    if error <= tolerance:
        return [p[0], p[3]]
    if depth >= 16:
        raise ValueError("Bézier flattening tolerance failed; no guessed chord.")
    a, b, c = (p[:-1]+p[1:])/2
    d, e = (a+b)/2, (b+c)/2
    f = (d+e)/2
    return bezier([p[0], a, d, f], tolerance, depth+1)[:-1] + bezier([f, e, c, p[3]], tolerance, depth+1)


def geometry():
    started = time.perf_counter()
    r = recipe()
    if OUT.exists():
        raise FileExistsError("Preserve previous drawings; do not redraw the same run.")
    OUT.mkdir(parents=True)
    width, height, depth = r["size_ticks"]
    top = [project(r, 0, height, 0), project(r, width, height, 0), project(r, width, height, depth), project(r, 0, height, depth)]
    front = [project(r, 0, 0, 0), project(r, width, 0, 0), project(r, width, height, 0), project(r, 0, height, 0)]
    side = [project(r, 0, 0, depth), project(r, 0, 0, 0), project(r, 0, height, 0), project(r, 0, height, depth)]
    masks = {name: polygon(r, vertices) for name, vertices in (("top", top), ("front", front), ("side", side))}
    if any(np.any(masks[a] & masks[b]) for a, b in (("top", "front"), ("top", "side"), ("front", "side"))):
        raise ValueError("Shared-face ownership overlap.")
    edges = {}

    def edge(a, b, colour):
        a, b = quantize(a), quantize(b)
        key = tuple(sorted((a, b)))
        old = edges.get(key)
        if old and old["colour"] != colour:
            raise ValueError("Two owners assigned different colours to one edge.")
        edges[key] = {"a": list(key[0]), "b": list(key[1]), "colour": colour}

    # Exterior silhouette and visible face joins. Shared edges are registered once.
    for a, b in zip(top, top[1:]+top[:1]):
        edge(a, b, "wood_edge")
    for x, z in ((0, depth), (0, 0), (width, 0)):
        edge(project(r, x, 0, z), project(r, x, height, z), "edge")
    edge(project(r, 0, 0, depth), project(r, 0, 0, 0), "edge")
    edge(project(r, 0, 0, 0), project(r, width, 0, 0), "edge")
    for y, colour in ((height-r["counter_thickness"], "wood_edge"), (r["plinth_height"], "edge")):
        edge(project(r, 0, y, depth), project(r, 0, y, 0), colour)
        edge(project(r, 0, y, 0), project(r, width, y, 0), colour)
    for index, (x0, x1, y0, y1) in enumerate(r["doors"]):
        if not 0 < x0 < x1 < width or not r["plinth_height"] < y0 < y1 < height-r["counter_thickness"]:
            raise ValueError("Door violates frame bounds.")
        p = [project(r, x0, y0, 0), project(r, x1, y0, 0), project(r, x1, y1, 0), project(r, x0, y1, 0)]
        masks[f"door{index}"] = polygon(r, p)
        for a, b in zip(p, p[1:]+p[:1]):
            edge(a, b, "edge")
    p = [project(r, 0, y, z) for z, y in ((3, 13), (17, 13), (17, 59), (3, 59))]
    masks["side_panel"] = polygon(r, p)
    for a, b in zip(p, p[1:]+p[:1]):
        edge(a, b, "edge")
    for z in r["planks"][1:-1]:
        edge(project(r, 0, height, z), project(r, width, height, z), "wood_joint")
    w, h = r["canvas"]
    edge_mask = np.zeros((h, w), bool)
    for item in edges.values():
        for x, y in line(item["a"], item["b"]):
            if not 0 <= x < w or not 0 <= y < h:
                raise ValueError("Structure exceeds the native canvas.")
            edge_mask[y, x] = True
    np.savez_compressed(OUT / "geometry.npz", **masks, structural_edges=edge_mask)
    record(OUT / "geometry.json", {"recipe_sha256": sha(RECIPE.read_bytes()), "code_sha256": sha(Path(__file__).read_bytes()),
           "edges": list(edges.values()), "face_overlap": 0, "canvas": r["canvas"],
           "world_metres": [width/32, depth/32, height/(32*math.sqrt(6))],
           "projection": "u=58+2x-2z;v=174-x-z-y", "elapsed_seconds": time.perf_counter()-started})
    print(json.dumps({"stage": "geometry", "unique_edges": len(edges), "face_overlap": 0}))


def material():
    started = time.perf_counter()
    r = recipe()
    geom = json.loads((OUT / "geometry.json").read_text())
    if sha(RECIPE.read_bytes()) != geom["recipe_sha256"] or sha(Path(__file__).read_bytes()) != geom["code_sha256"]:
        raise ValueError("Frozen recipe/algorithm changed.")
    if (OUT / "native.png").exists():
        raise FileExistsError("Previous actual asset must not be overwritten.")
    with np.load(OUT / "geometry.npz", allow_pickle=False) as data:
        masks = {key: data[key].copy() for key in data.files}
    w, h = r["canvas"]
    out = np.zeros((h, w, 4), np.uint8)
    palette = r["palette"]

    def paint(mask, name):
        out[mask, :3] = palette[name]
        out[mask, 3] = 255

    paint(masks["side"], "side")
    paint(masks["front"], "front")
    paint(masks["side_panel"], "side_panel")
    for i in range(len(r["doors"])):
        paint(masks[f"door{i}"], "door")
    # Direct face coordinate inversion at pixel centres, no image warp/resampling.
    yy, xx = np.mgrid[:h, :w]
    u, v = xx+.5-r["origin"][0], yy+.5-r["origin"][1]
    local_front_y = -v-u/2
    local_side_y = -v+u/2
    for name, local_y in (("front", local_front_y), ("side", local_side_y)):
        paint(masks[name] & (local_y < r["plinth_height"]), "plinth")
        paint(masks[name] & (local_y >= r["size_ticks"][1]-r["counter_thickness"]),
              "wood_fascia" if name == "front" else "wood_fascia_side")
    height = r["size_ticks"][1]
    local_top_x = u/4-(v+height)/2
    local_top_z = -u/4-(v+height)/2
    for i, (z0, z1) in enumerate(zip(r["planks"], r["planks"][1:])):
        paint(masks["top"] & (local_top_z >= z0) & (local_top_z < z1), ["wood", "wood_alt", "wood"][i])
    # Exclude a one-pixel neighbourhood of any structural line from grain.
    edges = masks["structural_edges"]
    blocked = edges.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            shifted = np.zeros_like(edges)
            ys, xs = slice(max(0, dy), min(h, h+dy)), slice(max(0, dx), min(w, w+dx))
            shifted[ys, xs] = edges[slice(max(0, -dy), min(h, h-dy)), slice(max(0, -dx), min(w, w-dx))]
            blocked |= shifted
    grain_allowed = masks["top"] & ~blocked
    grain = np.zeros((h, w), bool)

    def stroke(controls, name):
        flat = bezier([project(r, x, height, z) for x, z in controls])
        points = set()
        for a, b in zip(flat, flat[1:]):
            points.update(line(quantize(a), quantize(b)))
        for x, y in sorted(points):
            if 0 <= x < w and 0 <= y < h and grain_allowed[y, x]:
                out[y, x] = [*palette[name], 255]
                grain[y, x] = True

    for curve in r["grain_curves"]:
        stroke(curve, "wood_grain")
    # Deliberate knot clusters: four cubic quarters and a small binary core.
    k = 4*(math.sqrt(2)-1)/3
    for cx, cz, rx, rz in r["knots"]:
        quarters = [
            [(cx+rx, cz), (cx+rx, cz+k*rz), (cx+k*rx, cz+rz), (cx, cz+rz)],
            [(cx, cz+rz), (cx-k*rx, cz+rz), (cx-rx, cz+k*rz), (cx-rx, cz)],
            [(cx-rx, cz), (cx-rx, cz-k*rz), (cx-k*rx, cz-rz), (cx, cz-rz)],
            [(cx, cz-rz), (cx+k*rx, cz-rz), (cx+rx, cz-k*rz), (cx+rx, cz)]
        ]
        for curve in quarters:
            stroke(curve, "wood_grain")
        core = (((local_top_x-cx)/(rx*.32))**2 + ((local_top_z-cz)/(rz*.36))**2 <= 1) & grain_allowed
        paint(core, "wood_grain")
        grain |= core
    handles = np.zeros((h, w), bool)
    for x, y, width, handle_height in r["handles"]:
        shape = polygon(r, [project(r, sx, sy, 0) for sx, sy in ((x, y), (x+width, y), (x+width, y+handle_height), (x, y+handle_height))])
        if np.any(shape & ~masks["front"]):
            raise ValueError("Handle escaped its face.")
        paint(shape, "brass")
        paint(shape & (local_front_y >= y+handle_height-2), "brass_light")
        handles |= shape
    # Visible edges take precedence once; there is no blurred edge overlay.
    final_edge_colours = np.zeros_like(out)
    priority = {"wood_joint": 1, "edge": 2, "wood_edge": 3}
    edge_owner = np.zeros((h, w), np.uint8)
    for item in geom["edges"]:
        for x, y in line(item["a"], item["b"]):
            rank = priority[item["colour"]]
            if rank >= edge_owner[y, x]:
                out[y, x] = [*palette[item["colour"]], 255]
                final_edge_colours[y, x] = out[y, x]
                edge_owner[y, x] = rank
    Image.fromarray(out).save(OUT / "native.png")
    Image.fromarray(np.where(grain[..., None], out, 0).astype(np.uint8)).save(OUT / "grain-layer.png")
    np.savez_compressed(OUT / "material.npz", grain=grain, grain_allowed=grain_allowed, handles=handles, edge_rgba=final_edge_colours)
    record(OUT / "material.json", {"palette": palette, "grain_pixels": int(grain.sum()),
           "native_sha256": sha((OUT / "native.png").read_bytes()), "elapsed_seconds": time.perf_counter()-started,
           "output_origin": "direct_geometry_material_drawing", "source_rgb_sampled": False,
           "resize": False, "random_dither": False, "continuous_shading": False})
    print(json.dumps({"stage": "material", "native": r["canvas"], "grain_pixels": int(grain.sum())}))


def validate():
    r = recipe()
    geom = json.loads((OUT / "geometry.json").read_text())
    material_record = json.loads((OUT / "material.json").read_text())
    with Image.open(OUT / "native.png") as im:
        assert im.mode == "RGBA" and list(im.size) == r["canvas"]
        pixels = np.array(im)
    with np.load(OUT / "geometry.npz", allow_pickle=False) as g, np.load(OUT / "material.npz", allow_pickle=False) as m:
        assert not np.any(g["top"] & (g["side"] | g["front"])) and not np.any(g["side"] & g["front"])
        assert not np.any(m["grain"] & ~m["grain_allowed"])
        assert not np.any(m["grain"] & g["structural_edges"])
        np.testing.assert_array_equal(pixels[g["structural_edges"]], m["edge_rgba"][g["structural_edges"]])
        assert int(m["grain"].sum()) > 200
    assert np.isin(pixels[..., 3], [0, 255]).all()
    colours = set(map(tuple, pixels[pixels[..., 3] == 255, :3]))
    assert colours <= set(map(tuple, r["palette"].values()))
    assert len({(tuple(e["a"]), tuple(e["b"])) for e in geom["edges"]}) == len(geom["edges"])
    for edge in geom["edges"]:
        p = np.asarray(line(edge["a"], edge["b"]))
        if len(p) > 1:
            assert np.max(np.abs(np.diff(p, axis=0))) <= 1
        delta = np.abs(np.array(edge["b"])-edge["a"])
        assert len(p) == int(max(delta))+1
        axis = int(np.argmax(delta))
        assert len(np.unique(p[:, axis])) == len(p)
    assert len({x1-x0 for x0, x1, y0, y1 in r["doors"]}) == 1
    assert len({(width, height) for x, y, width, height in r["handles"]}) == 1
    assert sha(RECIPE.read_bytes()) == geom["recipe_sha256"] and sha(Path(__file__).read_bytes()) == geom["code_sha256"]
    assert sha((OUT / "native.png").read_bytes()) == material_record["native_sha256"]
    # Exact integer replication for display only, generated after production drawing.
    enlarged = np.repeat(np.repeat(pixels, 4, axis=0), 4, axis=1)
    np.testing.assert_array_equal(enlarged[::4, ::4], pixels)
    Image.fromarray(enlarged).save(OUT / "preview-x4.png")
    w, h = r["canvas"]
    panel = Image.new("RGB", (w*4+32, h*4+64), (40, 42, 47))
    draw = ImageDraw.Draw(panel)
    draw.text((16, 12), f"DIRECT NATIVE {w} x {h} | DISPLAY ONLY: EXACT 4x | {len(colours)} COLOURS", fill="white")
    sprite = Image.fromarray(enlarged)
    panel.paste(sprite, (16, 40), sprite)
    panel.save(OUT / "display-x4.png")
    report = {"passed": True, "native_size": r["canvas"], "opaque_colours": len(colours), "binary_alpha": True,
              "unique_structural_edges": len(geom["edges"]), "edge_width": "one Bresenham pixel per major-axis step; joins share endpoints",
              "grain_pixels": material_record["grain_pixels"], "face_overlap": 0, "source_unchanged": True,
              "source_rgb_sampled": False, "resize": False, "preview_integer_repeat": 4,
              "not_verified": ["aesthetic approval", "exact source reproduction", "Unity import/display", "general furniture generator"]}
    record(OUT / "validation.json", report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("geometry", "material", "validate"))
    args = parser.parse_args()
    {"geometry": geometry, "material": material, "validate": validate}[args.stage]()
