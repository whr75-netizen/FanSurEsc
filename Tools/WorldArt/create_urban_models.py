"""Author the D09 metric urban prop kit using Blender's standard mesh/FBX APIs.

Run in a separate Blender --background --factory-startup process. Existing FBX,
metadata and preview outputs are rejected. No source blend or sprite is read.

Canonical recipe coordinates are Unity metres: X right, Y up, Z front.
Blender coordinates are (X, -Z, Y). FBX exports -Z forward / Y up with baked
space conversion. Unity import is the final authority for engine-side axes.

Every polygon receives orthonormal planar metric UVs, 1 UV = 2 metres. UV
scale is measured on all polygon edges before export. Materials are shared
semantic names; no complete-object image is projected onto any surface.

Official references:
https://docs.blender.org/api/main/bpy.ops.export_scene.html
https://docs.blender.org/api/current/bpy.types.Mesh.html
https://docs.blender.org/manual/en/latest/addons/import_export/scene_fbx.html
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from time import perf_counter

import bpy
import bmesh
from mathutils import Matrix, Vector


UV_METRES = 2.0
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS = PROJECT_ROOT / "Assets/Art/UrbanCoherent09/Models"
DEFAULT_EVIDENCE = PROJECT_ROOT / "LocalOnly/UrbanDesign09"
PALETTE = {
    "Urban_Wood": (.43, .31, .19, 1),
    "Urban_MetalDark": (.095, .12, .125, 1),
    "Urban_MetalLight": (.42, .46, .46, 1),
    "Urban_Glass": (.075, .20, .22, 1),
    "Urban_Olive": (.29, .34, .17, 1),
    "Urban_Fabric": (.24, .37, .35, 1),
    "Urban_Ceramic": (.70, .69, .61, 1),
    "Urban_Brick": (.47, .25, .18, 1),
}
SPECS = {
    "office_desk": (1.5, 1.25, .75),
    "public_round_bin": (.45, .75, .45),
    "wheeled_dumpster": (1.5, 1.2, .9),
    "storage_shelf": (1.2, 1.8, .45),
    "retail_shelf": (1.2, 1.6, .55),
    "workbench": (1.6, 1.2, .7),
    "wardrobe": (1.2, 2., .55),
    "sofa": (1.7, .9, .85),
    "bed": (1.1, .85, 2.),
    "bench": (1.6, .9, .65),
    "planter": (.8, 1.2, .8),
    "street_tree": (3.4, 4., 3.4),
}
FBX_OPTIONS = {
    "use_selection": True,
    "object_types": {"MESH"},
    "global_scale": 1.,
    "apply_unit_scale": True,
    "apply_scale_options": "FBX_SCALE_UNITS",
    "axis_forward": "-Z",
    "axis_up": "Y",
    "use_space_transform": True,
    "bake_space_transform": True,
    "use_mesh_modifiers": True,
    "mesh_smooth_type": "FACE",
    "use_triangles": True,
    "add_leaf_bones": False,
    "bake_anim": False,
    "use_custom_props": True,
    "path_mode": "AUTO",
    "embed_textures": False,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blender_point(point) -> Vector:
    x, y, z = point
    return Vector((x, -z, y))


def unity_point(point) -> Vector:
    return Vector((point.x, point.z, -point.y))


def activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def materials():
    result = {}
    for name, color in PALETTE.items():
        material = bpy.data.materials.new(name)
        material.diffuse_color = color
        material.use_nodes = True
        principled = material.node_tree.nodes.get("Principled BSDF")
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Roughness"].default_value = .78
        result[name] = material
    return result


class Recipe:
    def __init__(self, name, common_materials):
        self.name = name
        self.materials = common_materials
        self.parts = []
        self.part_records = []

    def finish_part(self, obj, name, material, kind, bevel=0):
        obj.name = self.name + "__" + name
        obj.data.name = obj.name + "_Mesh"
        obj.data.materials.append(self.materials[material])
        activate(obj)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        if bevel > 0:
            modifier = obj.modifiers.new("Small structural edge bevel", "BEVEL")
            modifier.width = bevel
            modifier.segments = 1
            modifier.affect = "EDGES"
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        for polygon in obj.data.polygons:
            polygon.use_smooth = False
        self.parts.append(obj)
        self.part_records.append({"name": name, "primitive": kind, "material": material})
        return obj

    def box(self, name, center, size, material, bevel=.006, yaw=0):
        width, height, depth = size
        if min(size) <= 0:
            raise ValueError("Part dimensions must be positive: " + name)
        bpy.ops.mesh.primitive_cube_add(size=1., location=blender_point(center))
        obj = bpy.context.object
        obj.scale = (width, depth, height)
        obj.rotation_euler.z = math.radians(yaw)
        result = self.finish_part(obj, name, material, "beveled_box", min(bevel, min(size) * .22))
        self.part_records[-1].update(center_unity=list(center), size_unity=list(size), yaw_degrees=yaw)
        return result

    def cylinder(self, name, a, b, radius, material, sides=12):
        start, end = blender_point(a), blender_point(b)
        delta = end - start
        bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=delta.length,
                                           end_fill_type="NGON", location=(start + end) * .5)
        obj = bpy.context.object
        obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
        result = self.finish_part(obj, name, material, "cylinder")
        self.part_records[-1].update(start_unity=list(a), end_unity=list(b), radius=radius, sides=sides)
        return result

    def torus(self, name, center, radius, tube_radius, material):
        bpy.ops.mesh.primitive_torus_add(major_segments=16, minor_segments=4, major_radius=radius,
                                        minor_radius=tube_radius, location=blender_point(center))
        result = self.finish_part(bpy.context.object, name, material, "open_ring")
        self.part_records[-1].update(center_unity=list(center), major_radius=radius, tube_radius=tube_radius)
        return result

    def sphere(self, name, center, size, material):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=1., location=blender_point(center))
        obj = bpy.context.object
        obj.scale = (size[0] * .5, size[2] * .5, size[1] * .5)
        result = self.finish_part(obj, name, material, "faceted_foliage")
        self.part_records[-1].update(center_unity=list(center), size_unity=list(size))
        return result

    def shell(self, name, bottom_y, top_y, bottom_shape, top_shape, thickness, material, sides=4):
        """A hollow tapered vessel with real inside/outside surfaces and an open top."""
        def ring(y, shape):
            if sides == 4:
                width, depth = shape
                return [(sx * width * .5, y, sz * depth * .5)
                        for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            radius = shape[0]
            return [(radius * math.cos(i * math.tau / sides), y,
                     radius * math.sin(i * math.tau / sides)) for i in range(sides)]
        def inner(shape):
            return tuple(value - (2 * thickness if sides == 4 else thickness) for value in shape)
        points = (ring(bottom_y, bottom_shape) + ring(top_y, top_shape) +
                  ring(bottom_y + thickness, inner(bottom_shape)) + ring(top_y, inner(top_shape)))
        faces = []
        for i in range(sides):
            j = (i + 1) % sides
            faces.extend([(i, j, sides + j, sides + i),
                          (2*sides + i, 3*sides + i, 3*sides + j, 2*sides + j),
                          (sides + i, sides + j, 3*sides + j, 3*sides + i)])
        faces.extend([tuple(reversed(range(sides))), tuple(range(2*sides, 3*sides))])
        mesh = bpy.data.meshes.new(self.name + "__" + name)
        mesh.from_pydata([blender_point(point) for point in points], [], faces)
        mesh.update()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.collection.objects.link(obj)
        result = self.finish_part(obj, name, material, "hollow_tapered_shell")
        self.part_records[-1].update(bottom_y=bottom_y, top_y=top_y, bottom_shape=list(bottom_shape),
                                     top_shape=list(top_shape), wall_thickness=thickness, sides=sides)
        return result

    def combine(self):
        bpy.ops.object.select_all(action="DESELECT")
        for part in self.parts:
            part.select_set(True)
        bpy.context.view_layer.objects.active = self.parts[0]
        bpy.ops.object.join()
        model = bpy.context.object
        model.name = self.name
        model.data.name = self.name + "_Mesh"
        # Bake the combined world geometry while making the object origin the canonical floor centre.
        model.data.transform(model.matrix_world)
        model.matrix_world = Matrix.Identity(4)
        model["canonical_forward"] = "Unity +Z / Blender -Y"
        model["canonical_up"] = "Unity +Y / Blender +Z"
        model["metres_per_uv"] = UV_METRES
        model.data.update()
        return model


def desk(r):
    r.box("desktop", (0, .72, 0), (1.5, .06, .75), "Urban_Wood", .012)
    for x in (-.685, .685):
        for z in (-.31, .31):
            r.box(f"leg_{x}_{z}", (x, .345, z), (.065, .69, .065), "Urban_MetalDark")
    r.box("rear_stretcher", (0, .55, -.31), (1.37, .065, .055), "Urban_MetalDark")
    r.box("drawer_cabinet", (-.47, .505, -.015), (.33, .34, .54), "Urban_Ceramic")
    for y in (.43, .585):
        r.box("drawer_front_" + str(y), (-.47, y, .266), (.30, .14, .025), "Urban_Wood")
        r.box("drawer_handle_" + str(y), (-.47, y, .287), (.12, .018, .020), "Urban_MetalDark", .002)
    r.box("monitor_base", (0, .765, -.21), (.31, .03, .20), "Urban_MetalDark")
    r.box("monitor_stand", (0, .87, -.23), (.045, .21, .045), "Urban_MetalDark")
    r.box("monitor_frame", (0, 1.08, -.23), (.56, .34, .055), "Urban_MetalDark", .01)
    r.box("monitor_screen", (0, 1.08, -.2005), (.50, .28, .006), "Urban_Glass", .001)
    r.box("keyboard", (0, .7675, .13), (.43, .035, .15), "Urban_MetalDark", .006)
    for row in range(3):
        for col in range(10):
            r.box(f"key_{row}_{col}", (-.18 + col * .04, .787, .087 + row * .044),
                  (.031, .006, .03), "Urban_Ceramic", .001)
    r.sphere("mouse", (.40, .774, .12), (.060, .048, .10), "Urban_MetalDark")


def shelf_structure(r, width, height, depth, tops):
    post = .035
    for x in (-width*.5 + post*.5, width*.5 - post*.5):
        for z in (-depth*.5 + post*.5, depth*.5 - post*.5):
            r.box(f"upright_{x}_{z}", (x, height*.5, z), (post, height, post), "Urban_MetalDark", .003)
    for i, top in enumerate(tops):
        r.box("shelf_" + str(i), (0, top-.020, 0), (width-.04, .04, depth-.035), "Urban_MetalLight", .004)
        r.box("shelf_front_lip_" + str(i), (0, top-.007, depth*.5-.025),
              (width-.05, .026, .022), "Urban_MetalDark", .002)
    for sign in (-1, 1):
        r.cylinder("rear_brace_" + str(sign), (-width*.46, .10 if sign > 0 else height-.07, -depth*.5+.026),
                   (width*.46, height-.07 if sign > 0 else .10, -depth*.5+.026), .009, "Urban_MetalLight", 6)


def storage_shelf(r):
    shelf_structure(r, 1.2, 1.8, .45, (.08, .50, .92, 1.34, 1.76))


def retail_shelf(r):
    levels = (.10, .54, .98, 1.42)
    shelf_structure(r, 1.2, 1.6, .55, levels)
    colors = ("Urban_Brick", "Urban_Ceramic", "Urban_Olive", "Urban_Fabric")
    for level, top in enumerate(levels):
        for index in range(5):
            height = .18 if level == 3 else (.23 if index % 2 == 0 else .29)
            x = -.45 + index * .225
            r.box(f"product_{level}_{index}", (x, top + height*.5, -.055),
                  (.18, height, .27), colors[(level + index) % len(colors)], .004)
            r.box(f"product_label_{level}_{index}", (x, top+height*.60, .081),
                  (.105, height*.34, .004), "Urban_Ceramic", .0005)


def round_bin(r):
    r.cylinder("weighted_base", (0, 0, 0), (0, .075, 0), .205, "Urban_MetalDark", 16)
    r.shell("hollow_wood_body", .06, .72, (.198,), (.208,), .019, "Urban_Wood", 16)
    r.torus("upper_open_rim", (0, .735, 0), .21, .015, "Urban_MetalDark")
    r.torus("bottom_binding", (0, .08, 0), .20, .011, "Urban_MetalDark")
    for index in range(8):
        angle = index * math.tau / 8
        x, z = .21 * math.cos(angle), .21 * math.sin(angle)
        r.cylinder("vertical_binding_" + str(index), (x, .09, z), (x, .71, z), .006, "Urban_MetalDark", 6)


def dumpster(r):
    r.shell("tapered_container", .23, 1.06, (1.26, .64), (1.43, .78), .04, "Urban_Olive")
    r.box("closed_lid", (0, 1.10, 0), (1.50, .08, .90), "Urban_MetalDark", .012)
    for index in range(5):
        r.box("lid_stiffener_" + str(index), (-.57 + index*.285, 1.1575, .015),
              (.038, .035, .80), "Urban_MetalDark", .006)
    r.cylinder("rear_lid_hinge", (-.655, 1.13, -.375), (.655, 1.13, -.375), .07, "Urban_MetalDark", 12)
    for x in (-.59, .59):
        for z in (-.28, .28):
            r.box(f"caster_mount_{x}_{z}", (x, .235, z), (.11, .13, .10), "Urban_MetalLight")
            r.cylinder(f"wheel_{x}_{z}", (x-.0375, .11, z), (x+.0375, .11, z), .11, "Urban_MetalDark", 12)
            r.cylinder(f"wheel_hub_{x}_{z}", (x-.041, .11, z), (x+.041, .11, z), .045, "Urban_MetalLight", 8)
    for x in (-.44, .44):
        r.cylinder("handle_mount_" + str(x), (x, .86, .355), (x, .86, .431), .013, "Urban_MetalDark", 8)
    r.cylinder("front_handle", (-.44, .86, .431), (.44, .86, .431), .015, "Urban_MetalDark", 10)
    for x in (-.49, 0, .49):
        r.box("front_reinforcement_" + str(x), (x, .63, .362), (.035, .56, .032), "Urban_Olive", .003)


def workbench(r):
    r.box("worktop", (0, .76, 0), (1.6, .08, .7), "Urban_Wood", .012)
    for x in (-.715, .715):
        for z in (-.265, .265):
            r.box(f"leg_{x}_{z}", (x, .36, z), (.075, .72, .075), "Urban_MetalDark")
    r.box("lower_shelf", (0, .20, 0), (1.46, .035, .55), "Urban_MetalLight")
    r.box("tool_backboard", (0, 1.0, -.32), (1.44, .40, .036), "Urban_Wood", .005)
    r.box("drawer_case", (.49, .59, 0), (.42, .26, .56), "Urban_MetalDark")
    for y in (.52, .655):
        r.box("drawer_" + str(y), (.49, y, .287), (.38, .11, .024), "Urban_MetalLight")
        r.box("handle_" + str(y), (.49, y, .305), (.18, .015, .026), "Urban_MetalDark", .002)
    for index in range(5):
        x = -.52 + index * .245
        r.box("tool_shaft_" + str(index), (x, .982, -.29), (.022, .25, .019), "Urban_MetalLight", .002)
        if index % 2 == 0:
            r.box("wrench_head_" + str(index), (x, 1.105, -.287), (.07, .035, .027), "Urban_MetalLight", .002)
            for dx in (-.029, .029):
                r.box(f"wrench_jaw_{index}_{dx}", (x+dx, 1.135, -.287), (.016, .043, .027), "Urban_MetalLight", .001)
        else:
            r.box("screwdriver_grip_" + str(index), (x, .90, -.288), (.05, .11, .04), "Urban_Brick", .006)
    r.box("vise_base", (-.51, .829, .12), (.22, .058, .19), "Urban_MetalDark")
    for z in (.06, .17):
        r.box("vise_jaw_" + str(z), (-.51, .91, z), (.19, .105, .048), "Urban_MetalLight")
    r.cylinder("vise_screw", (-.51, .86, -.01), (-.51, .86, .28), .013, "Urban_MetalLight", 8)


def wardrobe(r):
    for x in (-.50, .50):
        for z in (-.20, .20):
            r.box(f"foot_{x}_{z}", (x, .06, z), (.09, .12, .09), "Urban_MetalDark")
    for x in (-.5725, .5725):
        r.box("side_" + str(x), (x, 1.055, 0), (.055, 1.89, .55), "Urban_Wood")
    r.box("top", (0, 1.9725, 0), (1.2, .055, .55), "Urban_Wood")
    r.box("bottom", (0, .1375, 0), (1.2, .055, .55), "Urban_Wood")
    r.box("back", (0, 1.05, -.255), (1.09, 1.81, .04), "Urban_Wood")
    for x in (-.278, .278):
        r.box("door_" + str(x), (x, 1.05, .229), (.542, 1.79, .04), "Urban_Ceramic", .007)
        sign = -1 if x < 0 else 1
        r.box("handle_" + str(x), (sign*.055, 1.06, .264), (.018, .16, .022), "Urban_MetalDark", .003)


def sofa(r):
    for x in (-.72, .72):
        for z in (-.31, .31):
            r.box(f"foot_{x}_{z}", (x, .065, z), (.065, .13, .065), "Urban_Wood")
    r.box("lower_body", (0, .245, 0), (1.62, .25, .82), "Urban_Fabric", .03)
    r.box("backrest", (0, .605, -.335), (1.7, .59, .18), "Urban_Fabric", .035)
    for x in (-.78, .78):
        r.box("arm_" + str(x), (x, .535, .01), (.14, .43, .83), "Urban_Fabric", .025)
    for x in (-.36, .36):
        r.box("seat_cushion_" + str(x), (x, .44, .08), (.68, .145, .55), "Urban_Fabric", .03)
        r.box("back_cushion_" + str(x), (x, .70, -.215), (.67, .34, .105), "Urban_Fabric", .025)


def bed(r):
    for x in (-.465, .465):
        for z in (-.84, .84):
            r.box(f"foot_{x}_{z}", (x, .085, z), (.08, .17, .08), "Urban_Wood")
    r.box("bed_frame", (0, .255, 0), (1.1, .18, 2.0), "Urban_Wood", .015)
    r.box("mattress", (0, .415, 0), (1.04, .15, 1.91), "Urban_Ceramic", .035)
    r.box("blanket", (0, .503, .34), (1.045, .026, 1.17), "Urban_Fabric", .004)
    r.box("headboard", (0, .50, -.955), (1.1, .70, .09), "Urban_Wood", .012)
    r.box("pillow", (0, .545, -.625), (.76, .11, .36), "Urban_Ceramic", .022)


def bench(r):
    for x in (-.66, .66):
        for z in (-.25, .25):
            r.box(f"leg_{x}_{z}", (x, .225, z), (.075, .45, .075), "Urban_MetalDark")
        r.box("seat_support_" + str(x), (x, .43, .025), (.075, .065, .58), "Urban_MetalDark")
        r.box("back_post_" + str(x), (x, .65, -.29), (.065, .50, .07), "Urban_MetalDark")
    for index, z in enumerate((-.14, .015, .17)):
        r.box("seat_slat_" + str(index), (0, .4725, z), (1.6, .045, .135), "Urban_Wood", .008)
    for index, y in enumerate((.645, .805)):
        r.box("back_slat_" + str(index), (0, y, -.2675), (1.6, .15, .07), "Urban_Wood", .009)
    for x in (-.76, .76):
        r.box("armrest_" + str(x), (x, .635, .025), (.075, .05, .60), "Urban_MetalDark", .008)
        r.box("arm_front_support_" + str(x), (x, .535, .255), (.055, .175, .055), "Urban_MetalDark")


def planter(r):
    r.shell("tapered_planter", 0, .50, (.64, .64), (.8, .8), .045, "Urban_Ceramic")
    r.box("soil", (0, .4325, 0), (.70, .035, .70), "Urban_Wood", 0)
    r.cylinder("trunk", (0, .445, 0), (0, .99, 0), .04, "Urban_Wood", 8)
    for index, (x, z) in enumerate(((-.17, -.1), (.17, -.1), (0, .17))):
        r.cylinder("branch_" + str(index), (0, .62, 0), (x, .97, z), .016, "Urban_Wood", 7)
        r.sphere("foliage_" + str(index), (x, .88, z), (.41, .46, .41), "Urban_Olive")
    r.sphere("top_foliage", (0, 1.005, -.015), (.48, .39, .48), "Urban_Olive")


def street_tree(r):
    r.cylinder("trunk_lower", (0, 0, 0), (0, 1.8, 0), .19, "Urban_Wood", 9)
    r.cylinder("trunk_upper", (0, 1.6, 0), (.08, 3.15, -.06), .12, "Urban_Wood", 8)
    branches = [((0, 1.72, 0), (-.82, 2.85, .12)),
                ((0, 1.93, 0), (.84, 2.99, .25)),
                ((0, 2.08, 0), (.06, 3.10, -.84))]
    for index, (start, end) in enumerate(branches):
        r.cylinder("branch_" + str(index), start, end, .078, "Urban_Wood", 7)
    crowns = [((-.74, 2.98, .14), (1.62, 1.33, 1.50)),
              ((.72, 3.11, .22), (1.60, 1.37, 1.54)),
              ((.03, 3.18, -.74), (1.65, 1.36, 1.63)),
              ((-.06, 3.42, -.06), (1.60, 1.16, 1.62)),
              ((-.05, 2.98, .76), (1.43, 1.25, 1.55))]
    for index, (center, size) in enumerate(crowns):
        r.sphere("branch_foliage_cluster_" + str(index), center, size, "Urban_Olive")


BUILDERS = {
    "office_desk": desk,
    "public_round_bin": round_bin,
    "wheeled_dumpster": dumpster,
    "storage_shelf": storage_shelf,
    "retail_shelf": retail_shelf,
    "workbench": workbench,
    "wardrobe": wardrobe,
    "sofa": sofa,
    "bed": bed,
    "bench": bench,
    "planter": planter,
    "street_tree": street_tree,
}


def metric_uvs(mesh):
    uv_layer = mesh.uv_layers.new(name="Metric_2m_Repeat")
    maximum_error = 0.
    for polygon in mesh.polygons:
        normal = polygon.normal.normalized()
        vertical = Vector((0, 0, 1))
        if abs(normal.dot(vertical)) < .99:
            v = (vertical - normal * normal.dot(vertical)).normalized()
            u = v.cross(normal).normalized()
        else:
            horizontal = Vector((1, 0, 0))
            u = (horizontal - normal * normal.dot(horizontal)).normalized()
            v = normal.cross(u).normalized()
        loop_indices = list(polygon.loop_indices)
        for loop_index in loop_indices:
            point = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv_layer.data[loop_index].uv = (point.dot(u) / UV_METRES, point.dot(v) / UV_METRES)
        for index, loop_index in enumerate(loop_indices):
            next_index = loop_indices[(index + 1) % len(loop_indices)]
            p = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            q = mesh.vertices[mesh.loops[next_index].vertex_index].co
            metres = (p - q).length
            uv_metres = (uv_layer.data[loop_index].uv - uv_layer.data[next_index].uv).length * UV_METRES
            maximum_error = max(maximum_error, abs(metres - uv_metres))
    if maximum_error > 1e-5:
        raise RuntimeError(f"Metric UV edge error exceeds 1e-5m: {maximum_error}")
    return maximum_error


def validate_model(model, expected):
    if tuple(model.location) != (0., 0., 0.) or tuple(model.scale) != (1., 1., 1.):
        raise RuntimeError("The exported model root is not identity at the floor origin.")
    points = [unity_point(vertex.co) for vertex in model.data.vertices]
    minimum = [min(point[axis] for point in points) for axis in range(3)]
    maximum = [max(point[axis] for point in points) for axis in range(3)]
    size = [maximum[axis] - minimum[axis] for axis in range(3)]
    tolerance = 1e-5
    width, height, depth = expected
    if (abs(minimum[1]) > tolerance or minimum[0] < -width*.5-tolerance or maximum[0] > width*.5+tolerance
            or maximum[1] > height+tolerance or minimum[2] < -depth*.5-tolerance or maximum[2] > depth*.5+tolerance):
        raise RuntimeError(f"{model.name} geometry lies outside its authored metres: {minimum}, {maximum}, expected {expected}")
    if min(size) <= 0 or len(model.data.vertices) < 20:
        raise RuntimeError("The model does not contain an actual three-dimensional assembly.")
    uv_error = metric_uvs(model.data)
    model.data.calc_loop_triangles()
    return {"canonical_bounds_min": minimum, "canonical_bounds_max": maximum,
            "canonical_size": size, "declared_size": list(expected), "root_scale": [1, 1, 1],
            "root_position": [0, 0, 0], "front_axis": "+Z", "up_axis": "+Y",
            "vertex_count": len(model.data.vertices), "triangle_count": len(model.data.loop_triangles),
            "polygon_count": len(model.data.polygons), "max_metric_uv_edge_error_metres": uv_error,
            "materials": sorted({slot.material.name for slot in model.material_slots if slot.material})}


def render_previews(models, directory):
    directory.mkdir(parents=True, exist_ok=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_specular_highlight = False
    scene.world.color = (.20, .20, .20)
    camera_data = bpy.data.cameras.new("Preview Camera")
    camera = bpy.data.objects.new("Preview Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    for model in models.values():
        model.hide_render = True
    for name, model in models.items():
        width, height, depth = SPECS[name]
        model.hide_render = False
        target = Vector((0, 0, height*.48))
        camera.location = target + Vector((3, -4, 3)).normalized() * 8
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera_data.ortho_scale = max(height*1.30, (width+depth)*.92)
        scene.render.filepath = str(directory / (name + ".png"))
        bpy.ops.render.render(write_still=True)
        model.hide_render = True
    for model in models.values():
        model.hide_render = False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_MODELS)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    output_dir, evidence_dir = args.output_dir.resolve(), args.evidence_dir.resolve()
    metadata_path = output_dir / "modelmetadata.json"
    report_path = evidence_dir / "model-build-report.json"
    preview_dir = evidence_dir / "model-previews"
    destinations = [metadata_path, report_path, *(output_dir / (name + ".fbx") for name in BUILDERS)]
    if any(path.exists() for path in destinations) or (args.preview and preview_dir.exists()):
        raise FileExistsError("A model, report or preview output already exists; no existing assets were changed.")
    started = perf_counter()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.
    shared_materials = materials()
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    models, records = {}, []
    source_sha256 = digest(Path(__file__))
    # Validate every recipe before writing any FBX, so a technical recipe error
    # leaves existing and pending output files untouched.
    for name, build in BUILDERS.items():
        model_started = perf_counter()
        recipe = Recipe(name, shared_materials)
        build(recipe)
        model = recipe.combine()
        record = validate_model(model, SPECS[name])
        record.update(id=name,
                      source_sha256=source_sha256,
                      component_count=len(recipe.parts), components=recipe.part_records,
                      build_seconds=perf_counter()-model_started)
        records.append(record)
        models[name] = model
    for record in records:
        name = record["id"]
        destination = output_dir / (name + ".fbx")
        export_started = perf_counter()
        activate(models[name])
        bpy.ops.export_scene.fbx(filepath=str(destination), **FBX_OPTIONS)
        record.update(model_path=destination.relative_to(PROJECT_ROOT).as_posix(),
                      fbx_sha256=digest(destination), export_seconds=perf_counter()-export_started)
        print("D09_MODEL_READY " + json.dumps({"id": name, "path": str(destination),
              "size": record["canonical_size"], "triangles": record["triangle_count"]}), flush=True)
    metadata = {
        "schema": "urban-coherent-model-kit/1", "recipe_revision": "D09-initial",
        "blender_version": bpy.app.version_string,
        "source_recipe": str(Path(__file__).resolve()), "source_recipe_sha256": digest(Path(__file__)),
        "canonical": {"units": "metres", "origin": "floor centre", "right": "+X", "up": "+Y", "front": "+Z",
                      "recipe_to_blender": "(x,y,z) -> (x,-z,y)"},
        "fbx_export": {key: sorted(value) if isinstance(value, set) else value for key, value in FBX_OPTIONS.items()},
        "uv": {"metres_per_uv": UV_METRES, "texels_per_metre_for_64px_repeat": 32,
               "method": "orthonormal tangent dot mesh position / 2 on each planar polygon; no fit-to-face stretch",
               "origin": "model local origin; tangent axes fixed from polygon normal and Blender world up",
               "max_edge_error_tolerance_metres": 1e-5},
        "materials": {name: {"display_rgba": list(color), "usage": "semantic shared material; root assigns D09 surface textures"}
                      for name, color in PALETTE.items()},
        "models": records, "unity_import_axes_and_bounds": "pending root final Unity validation",
        "visual_approval": "pending",
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    model_seconds = perf_counter()-started
    if args.preview:
        render_previews(models, preview_dir)
    report = {"schema": "urban-coherent-model-build/1", "status": "exported",
              "model_count": len(records), "source_recipe_sha256": metadata["source_recipe_sha256"],
              "metadata": str(metadata_path), "metadata_sha256": digest(metadata_path),
              "model_build_seconds": model_seconds, "total_seconds": perf_counter()-started,
              "previews": str(preview_dir) if args.preview else None,
              "unity_import_validation": "not performed here", "visual_approval": "pending"}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("D09_KIT_READY " + json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
