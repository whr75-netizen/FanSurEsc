"""Independent N15 checks on actual native geometry, shade, and PNG pixels.

This module deliberately does not import the production geometry/raster module.
Rational slab/plane witnesses check finite geometry around projected corners;
neither a renderer receipt nor an AI judgement can make these checks pass.
Technical success is never an art approval.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


_NORMALS = np.array([[0, -1, 0], [0, 1, 0], [0, 0, -1],
                     [0, 0, 1], [1, 0, 0], [-1, 0, 0]], dtype=float)
_RAY = (Fraction(1), Fraction(-2), Fraction(1))
_PRIORITY = {3: 0, 4: 1, 0: 2}


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _fraction(value):
    return Fraction(str(value))


def _boxes(profile, count):
    """Reviewed two-solid/attached-handle contract, independent of saved boxes."""
    p = {key: _fraction(value) for key, value in profile.items()
         if isinstance(value, (int, float)) and not isinstance(value, bool)}
    width = 2*p['end_cap']+count*p['module_pitch']
    bottom = p['height']-p['cap_thickness']
    result = [(0, (Fraction(0), Fraction(0), Fraction(0)),
               (width, bottom, p['depth'])),
              (1, (Fraction(-1), bottom, Fraction(-1)),
               (width+1, p['height'], p['depth']+1))]
    for bay in range(count):
        x = p['end_cap']+bay*p['module_pitch']+p['handle_x']
        result.append((bay+2, (x, p['handle_y'], Fraction(-1, 2)),
                       (x+p['handle_width'], p['handle_y']+p['handle_height'],
                        Fraction(0))))
    return result


def _project(point):
    x, y, z = point
    return 2*x-2*z, -x-y-z


def _screen_ray(x, y, origin):
    # Start at the front z=0 plane, rather than copying the production eye.
    u = Fraction(2*(x-int(origin[0]))+1, 2)
    v = Fraction(2*(y-int(origin[1]))+1, 2)
    return (u/2, -v-u/2, Fraction(0))


def _slab(start, direction, lo, hi):
    near = None
    far = None
    entry_faces = []
    for axis, speed in enumerate(direction):
        if speed == 0:
            if not lo[axis] <= start[axis] <= hi[axis]:
                return None
            continue
        a = (lo[axis]-start[axis])/speed
        b = (hi[axis]-start[axis])/speed
        face = 2*axis+(1 if speed < 0 else 0)
        a, b = min(a, b), max(a, b)
        if near is None or a > near:
            near, entry_faces = a, [face]
        elif a == near:
            entry_faces.append(face)
        far = b if far is None else min(far, b)
    if near is None or far is None or near >= far:
        return None
    face = min(entry_faces, key=lambda item: _PRIORITY.get(item, 3))
    return near, far, face


def _solid_hit(boxes, start):
    hits = []
    for part, lo, hi in sorted(boxes, key=lambda box: box[1]+box[2]):
        hit = _slab(start, _RAY, lo, hi)
        if hit is not None:
            hits.append((hit[0], _PRIORITY.get(hit[2], 3), part, hit[2]))
    if not hits:
        return None
    distance, _, part, face = min(hits, key=lambda hit: (hit[0], hit[1]))
    position = tuple(start[axis]+distance*_RAY[axis] for axis in range(3))
    return part, face, position


def _plane_hit(boxes, start):
    # Canonical planar comparison: body side/front, hardware front, then cap
    # side/front/top. Domains are half-open in their declared affine direction.
    body, cap = boxes[:2]
    surfaces = [(body, 0), (body, 4)]
    surfaces += [(box, 4) for box in boxes[2:]]
    surfaces += [(cap, 0), (cap, 4), (cap, 3)]
    result = None
    for (part, lo, hi), face in surfaces:
        axis = {0: 0, 4: 2, 3: 1}[face]
        plane = hi[axis] if face == 3 else lo[axis]
        distance = (plane-start[axis])/_RAY[axis]
        p = tuple(start[k]+distance*_RAY[k] for k in range(3))
        if face == 0:
            inside = lo[2] <= p[2] < hi[2] and lo[1] < p[1] <= hi[1]
        elif face == 4:
            inside = lo[0] <= p[0] < hi[0] and lo[1] < p[1] <= hi[1]
        else:
            inside = lo[0] <= p[0] < hi[0] and lo[2] <= p[2] < hi[2]
        if inside:
            result = part, face, p
    return result


def _corner_witnesses(boxes, origin, shape):
    coordinates = set()
    for _, lo, hi in boxes:
        for x in (lo[0], hi[0]):
            for y in (lo[1], hi[1]):
                for z in (lo[2], hi[2]):
                    u, v = _project((x, y, z))
                    cx = math.floor(u)+int(origin[0])
                    cy = math.floor(v)+int(origin[1])
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            xx, yy = cx+dx, cy+dy
                            if 0 <= yy < shape[0] and 0 <= xx < shape[1]:
                                coordinates.add((xx, yy))
    return sorted(coordinates, key=lambda point: (point[1], point[0]))


def _shadow_witness(boxes, point, light):
    # Transform the WORLD direction to ticks. The square root is only a metric
    # conversion; all subsequent finite interval comparisons are rational.
    light = np.asarray(light, float)
    light = light/np.linalg.norm(light)
    direction = tuple(_fraction(value) for value in
                      (light[1]*32, light[2]*32*math.sqrt(6), -light[0]*32))
    start = tuple(point[axis]+direction[axis]*Fraction(1, 10000000)
                  for axis in range(3))
    for _, lo, hi in boxes:
        hit = _slab(start, direction, lo, hi)
        if hit is not None and max(hit[0], Fraction(0)) < hit[1]:
            return True
    return False


def _same_color(rgb, color):
    return np.all(rgb == np.asarray(color, dtype=np.uint8), axis=-1)


def _in_palette(rgb, palette):
    colors = np.asarray(palette, dtype=np.uint8)
    return np.any(np.all(rgb[..., None, :] == colors, axis=-1), axis=-1)


def validate(recipe, reference, output):
    """Return explicit pass/fail records; missing evidence is a failed check."""
    recipe = _read(recipe) if isinstance(recipe, (str, Path)) else recipe
    output = Path(output)
    checks = []

    def check(name, passed, detail):
        checks.append({'name': name, 'pass': bool(passed), 'detail': detail})

    try:
        reference_bytes = Path(reference).read_bytes()
        actual_sha = hashlib.sha256(reference_bytes).hexdigest()
        check('reference_preserved', actual_sha == recipe['reference_sha256'],
              {'sha256': actual_sha, 'expected': recipe['reference_sha256']})
        source = np.asarray(Image.open(reference).convert('RGBA'), dtype=np.uint8)
        palette = _read(output/'material/palette.json')
        required_sizes = {'wood': 4, 'navy': 3, 'side': 3, 'brass': 3}
        packed = source[..., 0].astype(np.uint32)*65536
        packed += source[..., 1].astype(np.uint32)*256+source[..., 2]
        observed = np.unique(packed[source[..., 3] > 0])
        for role, size in required_sizes.items():
            raw = np.asarray(palette[role])
            valid = (raw.shape == (size, 3) and np.issubdtype(raw.dtype, np.integer)
                     and bool(np.all((raw >= 0) & (raw <= 255))))
            check(f'palette.{role}.shape', valid,
                  {'actual_shape': list(raw.shape), 'expected_shape': [size, 3]})
            if not valid:
                raise ValueError(f'Invalid {role} palette')
            color_ids = raw[:, 0]*65536+raw[:, 1]*256+raw[:, 2]
            check(f'palette.{role}.observed_source_rgb',
                  bool(np.isin(color_ids, observed).all()),
                  {'colors': raw.tolist(), 'source_position_relocation': False})
            check(f'palette.{role}.excludes_black',
                  not bool(np.any(np.all(raw == 0, axis=1))),
                  {'black_is_reserved_for_strong_seams': True})
    except Exception as error:
        check('required_reference_and_palette', False,
              {'error': f'{type(error).__name__}: {error}'})
        return {'checks': checks, 'all_pass': False, 'art_approved': False}

    modes = list(recipe['modes'])
    counts = list(recipe['variants'])
    check('comparison_modes', modes == ['planar', 'solid'], {'modes': modes})
    check('module_variants', counts == [2, 3], {'variants': counts})
    light = np.asarray(recipe['lighting']['to_light_world'], dtype=float)
    thresholds = np.asarray(recipe['lighting']['thresholds'], dtype=float)
    light_valid = (light.shape == (3,) and np.isfinite(light).all()
                   and float(np.linalg.norm(light)) > 0 and thresholds.shape == (2,)
                   and bool(0 < thresholds[0] < thresholds[1] < 1))
    check('lighting_inputs', light_valid,
          {'world_to_light': light.tolist(), 'thresholds': thresholds.tolist()})
    if not light_valid:
        return {'checks': checks, 'all_pass': False, 'art_approved': False}
    light = light/np.linalg.norm(light)
    geometric_handles = {}

    for mode in modes:
        for count in counts:
            prefix = f'{mode}.{count}'
            try:
                meta = _read(output/'geometry'/mode/f'geometry{count}.json')
                with np.load(output/'geometry'/mode/f'buffers{count}.npz') as data:
                    g = {key: data[key].copy() for key in
                         ('mask', 'part', 'face', 'position', 'normal', 'depth')}
                with np.load(output/'shade'/mode/f'shade{count}.npz') as data:
                    s = {key: data[key].copy() for key in
                         ('rgb', 'band', 'shadow', 'material')}
                with np.load(output/'material'/mode/f'materials{count}.npz') as data:
                    authored_material = data['material'].copy()
                    grain = data['grain'].copy()
                with np.load(output/'raster'/mode/f'owners{count}.npz') as data:
                    owners = {key: data[key].copy() for key in ('roles', 'strong')}
                policies = _read(output/'raster'/mode/f'policies{count}.json')
                rgba = np.asarray(Image.open(output/'raster'/mode/f'cabinet-{count}.png')
                                  .convert('RGBA'), dtype=np.uint8)
                mask = np.asarray(g['mask'], dtype=bool)
                shape = mask.shape
                shape_ok = (len(shape) == 2 and rgba.shape == (*shape, 4)
                            and g['part'].shape == shape and g['face'].shape == shape
                            and g['depth'].shape == shape
                            and g['position'].shape == (*shape, 3)
                            and g['normal'].shape == (*shape, 3)
                            and s['rgb'].shape == (*shape, 3)
                            and all(s[key].shape == shape for key in ('band', 'shadow', 'material'))
                            and authored_material.shape == shape and grain.shape == shape
                            and all(array.shape == shape for array in owners.values()))
                check(prefix+'.native_buffer_shapes', shape_ok,
                      {'native_width_height': [shape[1], shape[0]], 'rgba': list(rgba.shape)})
                if not shape_ok:
                    raise ValueError('Inconsistent native array shapes')
                dtype_ok = (g['mask'].dtype == np.dtype(bool) and
                            s['rgb'].dtype == np.dtype(np.uint8) and
                            s['band'].dtype == np.dtype(np.int8) and
                            s['material'].dtype == np.dtype(np.int8) and
                            s['shadow'].dtype == np.dtype(bool) and
                            owners['roles'].dtype == np.dtype(np.uint8) and
                            owners['strong'].dtype == np.dtype(bool))
                check(prefix+'.native_buffer_dtypes', dtype_ok,
                      {'geometry_mask': str(g['mask'].dtype),
                       'shade': {key: str(value.dtype) for key, value in s.items()},
                       'owners': {key: str(value.dtype) for key, value in owners.items()}})
                check(prefix+'.geometry_nonempty_finite',
                      bool(mask.any() and np.isfinite(g['position'][mask]).all()
                           and np.isfinite(g['depth'][mask]).all()),
                      {'visible_pixels': int(mask.sum())})
                alpha = rgba[..., 3]
                check(prefix+'.alpha_is_exact_geometry_coverage',
                      bool(np.array_equal(alpha, mask.astype(np.uint8)*255)),
                      {'extra_visible_pixels': int(np.count_nonzero((alpha > 0) & ~mask)),
                       'missing_visible_pixels': int(np.count_nonzero(mask & (alpha == 0))),
                       'perimeter_expansion_pixels': meta.get('perimeter_expansion_pixels')})
                check(prefix+'.transparent_pixels_clean',
                      bool(np.all(rgba[~mask] == 0)),
                      {'nonzero_transparent_channels': int(np.count_nonzero(rgba[~mask]))})
                normals_expected = _NORMALS[np.clip(g['face'], 0, 5)]
                check(prefix+'.world_normals_and_visible_face_ids',
                      bool(np.isin(g['face'][mask], (0, 3, 4)).all()
                           and np.allclose(g['normal'][mask], normals_expected[mask], atol=1e-12)),
                      {'visible_faces': sorted(int(x) for x in np.unique(g['face'][mask]))})

                boxes = _boxes(recipe['profile'], count)
                saved_boxes = meta['boxes']
                exact_boxes = (len(saved_boxes) == len(boxes) and all(
                    int(saved['part']) == part
                    and tuple(_fraction(v) for v in saved['minimum_ticks']) == lo
                    and tuple(_fraction(v) for v in saved['maximum_ticks']) == hi
                    for saved, (part, lo, hi) in zip(saved_boxes, boxes)))
                check(prefix+'.declared_part_dimensions', exact_boxes,
                      {'solid_count': len(saved_boxes), 'required_body_cap_handles': count+2})
                geometric_handles[(mode, count)] = [
                    tuple(_fraction(saved['maximum_ticks'][k])-
                          _fraction(saved['minimum_ticks'][k]) for k in range(3))
                    for saved in saved_boxes if int(saved['part']) >= 2]
                origin = meta['origin']
                witnesses = _corner_witnesses(boxes, origin, shape)
                mismatches = []
                shadow_mismatches = []
                hit_count = 0
                for x, y in witnesses:
                    start = _screen_ray(x, y, origin)
                    hit = _solid_hit(boxes, start) if mode == 'solid' else _plane_hit(boxes, start)
                    if hit is None:
                        match = not bool(mask[y, x])
                    else:
                        hit_count += 1
                        part, face, position = hit
                        expected = np.array([float(value) for value in position])
                        match = (bool(mask[y, x]) and int(g['part'][y, x]) == part
                                 and int(g['face'][y, x]) == face
                                 and bool(np.allclose(g['position'][y, x], expected, atol=1e-9))
                                 and math.isclose(float(g['depth'][y, x]),
                                                  float(1000-position[1]/2), abs_tol=1e-9))
                        expected_shadow = (_shadow_witness(boxes, position, light.tolist())
                                           if mode == 'solid' else False)
                        if bool(s['shadow'][y, x]) != expected_shadow:
                            shadow_mismatches.append([x, y, expected_shadow])
                    if not match:
                        mismatches.append([x, y])
                check(prefix+'.independent_fraction_corner_geometry',
                      bool(witnesses and hit_count and not mismatches),
                      {'tested_pixels': len(witnesses), 'visible_witnesses': hit_count,
                       'mismatches': mismatches[:16], 'mismatch_count': len(mismatches),
                       'method': 'Fraction finite slab / directed half-open plane intervals'})
                check(prefix+'.independent_corner_shadow_rays', not shadow_mismatches,
                      {'tested_visible_pixels': hit_count,
                       'mismatches': shadow_mismatches[:16],
                       'mismatch_count': len(shadow_mismatches)})

                shadow = np.asarray(s['shadow'], dtype=bool)
                material = s['material']
                # Body surfaces may carry flush brass inlays, but a decal never
                # acquires exterior pixels, replaces cap wood, or changes hits.
                material_valid = ((~mask & (material == 0)) |
                                  (mask & (g['part'] == 0) & np.isin(material, (1, 3))) |
                                  (mask & (g['part'] == 1) & (material == 2)) |
                                  (mask & (g['part'] >= 2) & (material == 3)))
                check(prefix+'.material_domains_are_on_actual_visible_parts',
                      bool(material_valid.all()),
                      {'wrong_domain_pixels': int(np.count_nonzero(~material_valid)),
                       'body_brass_is_flush_inlay': True})
                check(prefix+'.shade_preserves_authored_material_domains',
                      bool(np.array_equal(material, authored_material)),
                      {'wrong_material_pixels': int(np.count_nonzero(material != authored_material))})
                diffuse = np.maximum(0, np.sum(g['normal']*light, axis=-1))
                # Directional response and occlusion are independent authority
                # buffers. Shadow changes final material RGB, never normals or
                # the stored geometric band.
                expected_band = np.digitize(diffuse, thresholds)
                check(prefix+'.normal_light_owns_geometric_band',
                      bool(np.array_equal(s['band'][mask], expected_band[mask])),
                      {'wrong_band_pixels': int(np.count_nonzero(mask & (s['band'] != expected_band))),
                       'face_target_bands': {'top': 2, 'front': 1, 'side': 0},
                       'shadow_has_separate_bool_authority': True})
                for face, target, name in ((3, 2, 'top'), (4, 1, 'front'), (0, 0, 'side')):
                    area = mask & ~shadow & (g['face'] == face)
                    check(prefix+f'.unshadowed_{name}_band_{target}',
                          bool(area.any() and np.all(s['band'][area] == target)),
                          {'tested_pixels': int(area.sum())})
                check(prefix+'.planar_volume_shadow_policy',
                      bool(mode == 'solid' or not shadow.any()),
                      {'shadow_pixels': int(shadow.sum()), 'mode': mode})
                contact = mask & shadow & (g['part'] == 0) & (g['face'] == 4)
                check(prefix+'.solid_cap_contact_shadow_exists',
                      bool(mode == 'planar' or contact.any()),
                      {'actual_front_contact_pixels': int(contact.sum()),
                       'volume_required': mode == 'solid'})
                for material_id, role in ((1, 'navy'), (2, 'wood'), (3, 'brass')):
                    area = mask & shadow & (material == material_id)
                    failures = area & ~_same_color(s['rgb'], palette[role][0])
                    check(prefix+f'.shadow_{role}_uses_darkest_material_tone',
                          not bool(failures.any()),
                          {'shadow_pixels': int(area.sum()), 'wrong_tone_pixels': int(failures.sum())})
                paint = mask & ~shadow & (material == 1)
                paint_table = np.array([palette['side'][1], palette['navy'][1], palette['navy'][2]],
                                       dtype=np.uint8)
                paint_expected = paint_table[np.clip(s['band'], 0, 2)]
                check(prefix+'.paint_face_tones_follow_band_table',
                      bool(np.array_equal(s['rgb'][paint], paint_expected[paint])),
                      {'tested_pixels': int(paint.sum())})
                fascia = mask & ~shadow & (material == 2) & (g['face'] != 3)
                wood_table = np.array(palette['wood'], dtype=np.uint8)
                check(prefix+'.fascia_uses_wood_band_not_black_extra_line',
                      bool(np.array_equal(s['rgb'][fascia], wood_table[np.clip(s['band'][fascia], 0, 3)])),
                      {'tested_pixels': int(fascia.sum())})
                top = mask & ~shadow & (material == 2) & (g['face'] == 3)
                top_indices = np.clip(grain[top]+s['band'][top]-2, 0, 3)
                check(prefix+'.top_preserves_source_grain_rank_with_geometric_band',
                      bool(np.isin(grain[top], range(4)).all() and
                           np.array_equal(s['rgb'][top], wood_table[top_indices])),
                      {'tested_pixels': int(top.sum()),
                       'grain_rank_counts': [int(np.count_nonzero(grain[top] == value)) for value in range(4)]})
                for material_id, roles in ((1, ('navy', 'side')), (2, ('wood',)), (3, ('brass',))):
                    allowed = [color for role in roles for color in palette[role]]
                    area = mask & (material == material_id)
                    check(prefix+f'.material_{material_id}_palette_only',
                          bool(_in_palette(s['rgb'][area], allowed).all()),
                          {'tested_pixels': int(area.sum())})

                edge_roles = owners['roles']
                strong = np.asarray(owners['strong'], dtype=bool)
                check(prefix+'.edge_role_domain',
                      bool(np.isin(edge_roles, range(6)).all() and np.all(edge_roles[~mask] == 0)),
                      {'role_counts': {str(role): int(np.count_nonzero(edge_roles == role)) for role in range(6)}})
                expected_strong = np.isin(edge_roles, (1, 2))
                black = mask & _same_color(rgba[..., :3], (0, 0, 0))
                check(prefix+'.black_iff_strong_silhouette_or_explicit_seam',
                      bool(np.array_equal(strong, expected_strong)
                           and np.array_equal(black, strong) and not np.any(strong & ~mask)),
                      {'unowned_black_pixels': int(np.count_nonzero(black & ~expected_strong)),
                       'missing_strong_black_pixels': int(np.count_nonzero(expected_strong & ~black))})
                for role, material_id, palette_role in ((3, 1, 'navy'), (4, 2, 'wood'), (5, 3, 'brass')):
                    area = edge_roles == role
                    failures = area & ((material != material_id) |
                                       ~_same_color(rgba[..., :3], palette[palette_role][0]))
                    check(prefix+f'.surface_crease_role_{role}_uses_own_material_color',
                          not bool(failures.any()),
                          {'crease_pixels': int(area.sum()), 'wrong_color_or_material': int(failures.sum())})
                untouched = mask & (edge_roles == 0)
                check(prefix+'.nonedge_rgb_is_unchanged_shade',
                      bool(np.array_equal(rgba[untouched, :3], s['rgb'][untouched])),
                      {'tested_pixels': int(untouched.sum())})
                seam = edge_roles == 2
                check(prefix+'.explicit_seams_are_on_body_front',
                      bool(np.all((g['part'][seam] == 0) & (g['face'][seam] == 4))),
                      {'seam_pixels': int(seam.sum())})
                # Independent seam-location check: only module joins, at most
                # one pixel column per row and join. A complete door rectangle
                # or cap-adjacent black band cannot pass this domain check.
                profile = recipe['profile']
                pos = g['position']
                seam_domain = ((g['part'] == 0) & (g['face'] == 4) &
                               (pos[..., 1] >= 6) & (pos[..., 1] < 66))
                yy, xx = np.indices(shape)
                screen_u = xx-int(origin[0])+0.5
                joins = [2*(profile['end_cap']+index*profile['module_pitch'])
                         for index in range(1, count)]
                near_join = np.zeros(shape, dtype=bool)
                doubled_rows = []
                for join in joins:
                    band_area = np.abs(screen_u-join) <= 1.0
                    near_join |= band_area
                    for row in np.flatnonzero(np.count_nonzero(seam & band_area, axis=1) > 1):
                        doubled_rows.append([int(row), float(join)])
                check(prefix+'.one_pixel_explicit_join_seams_only',
                      bool(seam.any() and np.all((seam_domain & near_join)[seam])
                           and not doubled_rows),
                      {'seam_pixels': int(seam.sum()),
                       'off_join_or_height_pixels': int(np.count_nonzero(seam & ~(seam_domain & near_join))),
                       'double_pixel_rows': doubled_rows[:16],
                       'module_join_u': joins})
                check(prefix+'.surface_crease_contains_no_black',
                      not bool(np.any(black & np.isin(edge_roles, (3, 4, 5)))),
                      {'black_surface_crease_pixels': int(np.count_nonzero(black & np.isin(edge_roles, (3, 4, 5))))})
                shadow_hardware = mask & shadow & (material == 3) & ~strong
                check(prefix+'.shadow_hardware_never_overwritten_with_bright_metal',
                      bool(np.all(_same_color(rgba[..., :3], palette['brass'][0])[shadow_hardware])),
                      {'tested_pixels': int(shadow_hardware.sum())})
                check(prefix+'.raster_policy_evidence_loaded', bool(policies),
                      {'policy_type': type(policies).__name__, 'art_approval': False})
            except Exception as error:
                check(prefix+'.required_artifact_contract', False,
                      {'error': f'{type(error).__name__}: {error}'})

    for mode in ('planar', 'solid'):
        handles2 = geometric_handles.get((mode, 2))
        handles3 = geometric_handles.get((mode, 3))
        dimensions = (handles2 or [])+(handles3 or [])
        check(mode+'.two_three_module_handles_have_identical_geometry',
              bool(handles2 and handles3 and len(handles2) == 2 and len(handles3) == 3
                   and all(value == dimensions[0] for value in dimensions)),
              {'dimensions_ticks': [[str(value) for value in size] for size in dimensions],
               'stretching_or_image_resizing_used': False})
    return {'checks': checks, 'all_pass': bool(checks and all(item['pass'] for item in checks)),
            'art_approved': False,
            'scope': 'N15 finite geometry, material/shade attribution, and actual native PNG; no Unity or art acceptance'}
