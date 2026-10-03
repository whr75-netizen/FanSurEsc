"""Parametric cabinet solids -> native finite-surface buffers, run in Blender.

This stage owns geometry and visibility only.  Reference RGB, authored palette
bands and texture indices belong to the separate material stage.  No beauty
render, image resize, PerfectPixel pass or mesh scaling is performed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "PixelPipeline"))
from common import basis


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    # Serialize before opening so an invalid NumPy scalar cannot leave a partial
    # JSON artifact.  All values constructed below are native Python types.
    text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def world(local):
    """V5 local ticks (width, height, depth) -> Blender Z-up metres."""
    x, y, z = local
    return np.array((-z / 32, x / 32, y / (32 * math.sqrt(6))), float)


def box_bounds(lo, hi):
    points = np.array([world((x, y, z)) for x in (lo[0], hi[0])
                       for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    return points.min(0), points.max(0)


def build_variant(scene, count, recipe):
    pitch, cap = float(recipe.get("module_pitch", 20)), float(recipe.get("cap", 2))
    height, depth = float(recipe.get("height", 72)), float(recipe.get("depth", 20))
    if (pitch, cap, height, depth) != (20., 2., 72., 20.):
        raise ValueError("V6 reviewed profile is pitch=20, cap=2, height=72, depth=20")
    width = 2 * cap + count * pitch
    groups, boxes, objects = [], [], []

    def group(name, role, bay=None):
        entry = {"id": len(groups), "name": name, "role": role, "bay": bay,
                 "boxes": [], "face_ids": {"-X": 0, "+X": 1, "-Y": 2,
                                               "+Y": 3, "-Z": 4, "+Z": 5}}
        groups.append(entry)
        return entry

    def solid(semantic, suffix, lo, hi):
        lo, hi = [float(v) for v in lo], [float(v) for v in hi]
        if not all(math.isfinite(v) for v in lo + hi) or any(a >= b for a, b in zip(lo, hi)):
            raise ValueError(f"Invalid solid bounds: {semantic['name']}/{suffix}")
        minimum, maximum = box_bounds(lo, hi)
        a, b, c = minimum.tolist(); x, y, z = maximum.tolist()
        vertices = [(a,b,c), (x,b,c), (x,y,c), (a,y,c),
                    (a,b,z), (x,b,z), (x,y,z), (a,y,z)]
        # These are world-axis boxes.  Winding stays outward even though the
        # local-to-world mapping changes handedness; local faces are not copied.
        faces = [(0,4,7,3), (1,2,6,5), (0,1,5,4),
                 (3,7,6,2), (0,3,2,1), (4,5,6,7)]
        name = f"N{count}_{semantic['name']}_{suffix}"
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces); mesh.update()
        obj = bpy.data.objects.new(name, mesh); scene.collection.objects.link(obj)
        obj["semantic_part_id"] = semantic["id"]
        obj["material_role"] = semantic["role"]
        obj["local_bounds_ticks"] = json.dumps([lo, hi])
        rec = {"name": name, "part": semantic["id"], "role": semantic["role"],
               "bay": semantic["bay"], "local_minimum_ticks": lo, "local_maximum_ticks": hi,
               "minimum": minimum.tolist(), "maximum": maximum.tolist()}
        boxes.append(rec); semantic["boxes"].append(name); objects.append(obj)
        expected = np.array([[-1,0,0],[1,0,0],[0,-1,0],[0,1,0],[0,0,-1],[0,0,1]], float)
        if not all(np.allclose(list(p.normal), expected[i], atol=1e-6)
                   for i, p in enumerate(mesh.polygons)):
            raise AssertionError(f"Non-outward world winding: {name}")

    solid(group("Body", "paint"), "solid", (0,6,0), (width,68,depth))
    solid(group("Counter", "wood"), "solid", (-1,68,-1), (width+1,72,depth+1))
    solid(group("Plinth", "paint"), "solid", (2,0,3), (width-2,6,depth))

    def front_frame(name, bay, x0, x1, y0, y1, rail):
        g = group(name + "Frame", "paint", bay)
        # Nonoverlapping rail boxes form one semantic frame.  Their same-facing
        # polygons share face IDs, suppressing internal construction seams.
        solid(g,"bottom",(x0,y0,-2),(x1,y0+rail,0))
        solid(g,"top",(x0,y1-rail,-2),(x1,y1,0))
        solid(g,"left",(x0,y0+rail,-2),(x0+rail,y1-rail,0))
        solid(g,"right",(x1-rail,y0+rail,-2),(x1,y1-rail,0))
        solid(group(name + "Inset", "paint", bay), "panel",
              (x0+rail,y0+rail,-.4),(x1-rail,y1-rail,0))

    def handle(name, bay, xc, y0):
        g = group(name, "brass", bay)
        solid(g,"bar",(xc-3,y0,-4),(xc+3,y0+2,-3))
        for sign in (-1,1):
            anchor = xc + sign * 2.5
            solid(g, f"anchor_{sign}", (anchor-.5,y0,-3),(anchor+.5,y0+2,-.4))

    def door_handle(bay, start):
        g = group(f"Bay{bay}DoorHandle", "brass", bay)
        # Generated design board: vertical pull at the right upper door panel.
        solid(g,"bar",(start+15,36,-4),(start+16.5,42,-3))
        for yy in (36.5,40.5):
            solid(g,f"anchor_{yy}",(start+15.25,yy,-3),(start+16.25,yy+1,-.4))

    for i in range(count):
        start = cap + i * pitch
        x0, x1 = start + 1, start + 17
        front_frame(f"Bay{i}Door", i, x0,x1,12,50,2)
        front_frame(f"Bay{i}Drawer", i, x0,x1,54,64,1.5)
        door_handle(i,start)
        handle(f"Bay{i}DrawerHandle", i, (x0+x1)/2,58)

    side = group("SideFrame", "paint")
    solid(side,"bottom",(-2,12,3),(0,14,17))
    solid(side,"top",(-2,60,3),(0,62,17))
    solid(side,"front",(-2,14,3),(0,60,5))
    solid(side,"back",(-2,14,15),(0,60,17))
    solid(group("SideInset", "paint"), "panel",(-.4,14,5),(0,60,15))
    bpy.context.view_layer.update()
    for obj, rec in zip(objects, boxes):
        pts = np.array([list(obj.matrix_world @ v.co) for v in obj.data.vertices])
        if not np.allclose(pts.min(0), rec["minimum"], atol=1e-7) or not np.allclose(pts.max(0),rec["maximum"],atol=1e-7):
            raise AssertionError(f"Mesh readback bounds differ: {obj.name}")
        rec["mesh_readback_bounds_match"] = True
    return {"count": int(count), "width_ticks": width, "height_ticks": height,
            "depth_ticks": depth, "groups": groups, "boxes": boxes}, objects


def palette_preview(objects, palette):
    """Optional viewport colour only; no preview RGB enters native buffers."""
    defaults = {"paint": [53,83,89], "wood": [188,138,80], "brass": [185,132,58]}
    source = palette.get("colors_srgb8byrole",palette.get("roles",palette)) if isinstance(palette,dict) else {}
    mats = {}
    for role in defaults:
        value = source.get(role, defaults[role])
        if isinstance(value,dict): value = value.get("base", value.get("colors_srgb8", defaults[role]))
        if isinstance(value,list) and value and isinstance(value[0],list): value = value[min(1,len(value)-1)]
        if not isinstance(value,list) or len(value)!=3: value = defaults[role]
        mat = bpy.data.materials.new("Viewport_"+role)
        mat.diffuse_color = tuple(float(v)/255 for v in value) + (1.,)
        mats[role] = mat
    for obj in objects: obj.data.materials.append(mats[obj["material_role"]])


def raster_variant(scene, spec, objects, recipe, out):
    started = time.perf_counter()
    camera = dict(recipe["camera"], margin_pixels=int(recipe.get("margin_pixels",8)))
    if (camera["azimuth_degrees"], camera["elevation_degrees"]) != (45,30) or abs(camera["pixels_per_meter"]-64*math.sqrt(2))>1e-10:
        raise ValueError("Reviewed V6 camera is azimuth45/elevation30/density64sqrt2")
    r, u, d = basis(camera); density = camera["pixels_per_meter"]
    vertices, triangles, owners, face_ids = [], [], [], []
    for obj in objects:
        offset = len(vertices)
        vertices.extend([obj.matrix_world @ v.co for v in obj.data.vertices])
        obj.data.calc_loop_triangles()
        for tri in obj.data.loop_triangles:
            triangles.append(tuple(offset+int(k) for k in tri.vertices))
            owners.append(int(obj["semantic_part_id"])); face_ids.append(int(tri.polygon_index))
    points = np.array([list(v) for v in vertices], float)
    projected = np.column_stack((points @ r, -(points @ u))) * density
    # Exact intended ground slopes / height: 2x-2z, -x-z-y.
    local_tests = [(0,0,0),(spec["width_ticks"],72,20),(1.5,54,-2)]
    projection_error = max(float(np.max(np.abs(np.array([world(p)@r,-world(p)@u])*density
                         - np.array([2*p[0]-2*p[2],-p[0]-p[2]-p[1]])))) for p in local_tests)
    if projection_error > 1e-10: raise AssertionError("V5 projection contract changed")
    # Values mathematically integral are snapped only within floating roundoff,
    # preventing a one-pixel canvas jump between module counts.
    rounded = np.rint(projected)
    projected = np.where(np.abs(projected-rounded)<1e-9, rounded, projected)
    minimum, maximum = np.floor(projected.min(0)), np.ceil(projected.max(0))
    margin = camera["margin_pixels"]
    if margin < 2: raise ValueError("Native margin must preserve exterior samples")
    width, height = [int(v) for v in maximum-minimum+2*margin]
    origin_px = minimum-margin
    distance = float(np.max(points@d)+4)
    ray_direction = Vector(-d)
    light = np.array(recipe.get("lighting",{}).get("to_light",[-.15,-.55,.82]),float)
    if light.shape!=(3,) or not np.isfinite(light).all() or np.linalg.norm(light)==0:
        raise ValueError("Invalid world-space light direction")
    light /= np.linalg.norm(light)
    epsilon = float(32*np.finfo(np.float32).eps*max(1.,float(np.abs(points).max())))
    bvh = BVHTree.FromPolygons(vertices,triangles,all_triangles=True,epsilon=0.)
    mask = np.zeros((height,width),bool)
    positions = np.zeros((height,width,3),np.float32); normals = np.zeros_like(positions)
    part = np.full((height,width),-1,np.int32); face = np.full_like(part,-1)
    depth = np.zeros((height,width),np.float32); visibility = np.zeros_like(mask)

    def origin(x,y):
        q = (origin_px+np.array([x,y]))/density
        return Vector(r*q[0]-u*q[1]+d*distance)

    for y in range(height):
        for x in range(width):
            loc,normal,tri,t = bvh.ray_cast(origin(x+.5,y+.5),ray_direction,100.)
            if tri is None: continue
            mask[y,x] = True; positions[y,x] = loc; normals[y,x] = normal
            part[y,x] = owners[tri]; face[y,x] = face_ids[tri]; depth[y,x] = t
            visibility[y,x] = bvh.ray_cast(loc+normal*epsilon,Vector(light),100.)[2] is None
    if not mask.any() or not np.isfinite(positions).all() or not np.isfinite(depth).all():
        raise AssertionError("Empty or nonfinite native raster")
    if not np.allclose(np.linalg.norm(normals[mask],axis=1),1.,atol=1e-6):
        raise AssertionError("Native normals are not unit vectors")
    if not ((part[mask]>=0)&(part[mask]<len(spec["groups"]))&(face[mask]>=0)&(face[mask]<6)).all():
        raise AssertionError("Invalid native semantic surface ID")

    def slab(o,direction):
        hits = []
        for box in spec["boxes"]:
            lo, hi = np.array(box["minimum"]),np.array(box["maximum"])
            near, far = -math.inf, math.inf
            for k in range(3):
                if abs(direction[k])<1e-12:
                    if o[k]<lo[k] or o[k]>hi[k]: near=math.inf; break
                else:
                    t0,t1 = sorted(((lo[k]-o[k])/direction[k],(hi[k]-o[k])/direction[k]))
                    near,far = max(near,t0),min(far,t1)
            if far>=max(0.,near): hits.append((max(near,0.),int(box["part"])))
        return min(hits) if hits else None

    checks = []
    # One representative visible ray per material role, plus inset/frame pairs.
    wanted = [g for g in spec["groups"] if g["name"] in
              ("Body","Counter","Plinth","Bay0DoorFrame","Bay0DoorInset",
               "Bay0DrawerFrame","Bay0DrawerInset","Bay0DoorHandle","SideFrame","SideInset")]
    for g in wanted:
        samples = np.argwhere(part==g["id"])
        if not len(samples):
            checks.append({"group":g["name"],"visible":False}); continue
        yy,xx = [int(v) for v in samples[len(samples)//2]]
        expected = slab(np.array(origin(xx+.5,yy+.5)),-d)
        error = abs(float(expected[0])-float(depth[yy,xx])) if expected else None
        same = expected is not None and expected[1]==int(part[yy,xx])
        checks.append({"group":g["name"],"visible":True,"pixel":[xx,yy],
                       "same_owner":same,"depth_error_m":error})
        if not same or error>1e-5: raise AssertionError(f"Independent slab mismatch: {g['name']}")
    filename = f"buffers{spec['count']}.npz"
    np.savez_compressed(out/filename,mask=mask,positions=positions,normals=normals,
                        part=part,face=face,depth=depth,visibility=visibility)
    metadata = {"count":spec["count"],"size":[width,height],"camera":camera,
                "pixels_per_meter":density,"screen_origin":origin_px.tolist(),
                "camera_distance":distance,"world_mapping":"(-z/32,x/32,y/(32sqrt(6)))",
                "projection":"u=2x-2z;v=-x-z-y;origin is whole native pixels",
                "projection_max_error_px":projection_error,"shadow_offset_m":epsilon,
                "to_light_world":light.tolist(),"foreground_pixels":int(mask.sum()),
                "shadow_pixels":int((mask&~visibility).sum()),"parts":spec["groups"],
                "boxes":spec["boxes"],"slab_checks":checks,"native_pixel_centres":True,
                "source_rgb_used":False,"image_resize":False,"semantic_frame_seams_suppressed":True,
                "buffers_sha256":digest(out/filename),"elapsed_seconds":time.perf_counter()-started}
    write_json(out/f"raster{spec['count']}.json",metadata)
    # Editable per-variant scene with the same orthographic basis and pixel frame.
    data = bpy.data.cameras.new(f"NativeCamera{spec['count']}"); data.type="ORTHO"
    data.ortho_scale=height/density
    obj = bpy.data.objects.new(data.name,data); scene.collection.objects.link(obj)
    matrix = Matrix(np.column_stack((r,u,d)).tolist()).to_4x4()
    centre = (origin_px+np.array([width,height])/2)/density
    matrix.translation = Vector(r*centre[0]-u*centre[1]+d*distance)
    obj.matrix_world=matrix; scene.camera=obj
    scene.render.resolution_x=width; scene.render.resolution_y=height
    scene.render.resolution_percentage=100
    scene["native_raster_method"]="finite BVH pixel centres; Blender beauty render is not the final PNG"
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--palette",type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    recipe = json.loads(args.recipe.read_text(encoding="utf-8"))
    counts = recipe.get("variants",recipe.get("n",[2,3]))
    if counts!=[2,3]: raise ValueError("Reviewed V6 variants are exactly [2,3]")
    if args.output.exists(): raise FileExistsError("Use a new immutable geometry output directory")
    palette = json.loads(args.palette.read_text(encoding="utf-8")) if args.palette else {}
    args.output.mkdir(parents=True,exist_ok=False)
    started = time.perf_counter(); original_scenes=list(bpy.data.scenes)
    specs, rasters = [], []
    for count in counts:
        scene=bpy.data.scenes.new(f"Cabinet_{count}_modules")
        spec,objects=build_variant(scene,count,recipe)
        palette_preview(objects,palette)
        raster=raster_variant(scene,spec,objects,recipe,args.output)
        specs.append(spec); rasters.append(raster)
    if bpy.context.window: bpy.context.window.scene=scene
    for old in original_scenes: bpy.data.scenes.remove(old)
    bpy.ops.wm.save_as_mainfile(filepath=str((args.output/"scene.blend").resolve()))
    write_json(args.output/"parts.json",{"schema":"parametric-native-cabinet/6",
               "recipe_sha256":digest(args.recipe),"renderer_sha256":digest(__file__),
               "variants":specs,"shared_pixels_per_meter":rasters[0]["pixels_per_meter"],
               "no_uniform_or_nonuniform_mesh_scale":True,"source_image_read":False,
               "bpy_version":bpy.app.version_string,"elapsed_seconds":time.perf_counter()-started})
    print(json.dumps({"geometry":"scene.blend","variants":[{"count":r["count"],"size":r["size"]}
                      for r in rasters],"elapsed_seconds":time.perf_counter()-started}))


if __name__ == "__main__":
    main()
