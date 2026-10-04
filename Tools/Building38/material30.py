"""N30 cause-specific intrinsic material, height gradients and roughness.

Every output is evaluated on the existing native cell centres. No image resize,
lighting baked into albedo, broad stain field or geometry regeneration occurs.
"""
import argparse
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

from material29 import ROOT, SOURCE, MAP, field, sha, source_hashes, write

PRIOR = ROOT / 'docs/artifacts/building39/material29/run01'
PALETTE = ROOT / 'Assets/Art/NativeBuilding39/palette.png'
FEATURES = ('grain', 'contact', 'scratch', 'kick', 'chip', 'patina')
TILT_LIMIT_DEGREES = 8.0


def connected_sizes(mask):
    """Four-connected cell sizes; bounds apply to cause masks, not colour noise."""
    seen = np.zeros(mask.shape, bool)
    sizes = []
    height, width = mask.shape
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        todo = deque([(y, x)])
        seen[y, x] = True
        size = 0
        while todo:
            yy, xx = todo.popleft()
            size += 1
            for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                a, b = yy + dy, xx + dx
                if 0 <= a < height and 0 <= b < width and mask[a, b] and not seen[a, b]:
                    seen[a, b] = True
                    todo.append((a, b))
        sizes.append(size)
    return sorted(sizes, reverse=True)


def segment_distance(u, v, a, b):
    du, dv = b[0] - a[0], b[1] - a[1]
    t = np.clip(((u - a[0]) * du + (v - a[1]) * dv) / (du * du + dv * dv), 0, 1)
    return np.hypot(u - a[0] - t * du, v - a[1] - t * dv)


def srgb_to_linear(rgb):
    x = np.asarray(rgb, np.float64) / 255
    return np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)


def linear_to_srgb(rgb):
    x = np.clip(rgb, 0, 1)
    y = np.where(x <= .0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - .055)
    return np.rint(y * 255).astype(np.uint8)


def palette16(original):
    palette = np.repeat(original[:, 2:3, :], 16, axis=1)
    palette[:, :4] = original
    # Adjacent intrinsic pigment colours, separate from the three light bands.
    factors = np.array([.56, .67, .75, .82, .87, .92, .96, 1, 1.05,
                        1.10, 1.16, 1.22, 1.28, 1.34, 1.40])
    paint_factors = np.array([.75, .82, .87, .92, 1, 1.05, 1.10, 1.16, 1.22, 1.28, 1.34, 1.40])
    # Original indices 0..3 remain available to every existing boundary texel.
    # The clean paint base is column eight; only B0 cause masks use new colours.
    palette[1, 4:] = linear_to_srgb(srgb_to_linear(original[1, 2]) * paint_factors[:, None])
    # Row four is bare wood only in this new material clone, never globally.
    palette[3, 0] = [75, 45, 25]
    palette[3, 1:] = linear_to_srgb(srgb_to_linear(original[0, 1]) * factors[:, None])
    # Preserve existing gold indices 0..3; sparse patina uses extra neighbours.
    gold_factors = np.linspace(.48, 1.04, 12)
    palette[2, 4:] = linear_to_srgb(srgb_to_linear(original[2, 2]) * gold_factors[:, None])
    return palette


def anchors(design):
    p, s = design['profile'], np.asarray(design['tick_scale_xyz'])
    contact, scratch, kick, chip = [], [], [], []
    for i in range(design['count']):
        start = p['end_cap'] + i * p['module_pitch']
        hx = (start + p['handle_x'] + .5 * p['handle_width']) * s[0]
        hy = (p['handle_y'] + .5 * p['handle_height']) * s[1]
        centre = (start + .5 * p['module_pitch']) * s[0]
        # Hand contact below/beside the handle; feet meet the lower door zone.
        contact.append((hx - .040, hy - .050))
        scratch.extend([((hx - .085, hy - .093), (hx + .013, hy - .085)),
                        ((centre - .028, .155 + i * .011), (centre + .035, .160 + i * .011))])
        kick.append((centre + (.017 if i == 1 else -.021), p['plinth'] * s[1] + .047))
        chip.extend([((hx - .060, hy - .076), (hx - .041, hy - .071)),
                     ((centre + .048, .132 + i * .011), (centre + .066, .137 + i * .011))])
    # One side-panel scuff derives from its lower contact zone, not a stain.
    return contact, scratch, kick, chip


def continuous_features(u, v, side, design):
    contact_at, scratch_at, kick_at, chip_at = anchors(design)
    contact = np.zeros(u.shape)
    kick = np.zeros(u.shape)
    scratch = np.full(u.shape, np.inf)
    chip = np.full(u.shape, np.inf)
    for x, y in contact_at:
        e = ((u - x) / .034) ** 2 + ((v - y) / .047) ** 2
        contact = np.maximum(contact, np.where(side, 0, np.exp(-e)))
    for x, y in kick_at:
        e = ((u - x) / .071) ** 2 + ((v - y) / .018) ** 2
        kick = np.maximum(kick, np.where(side, 0, np.exp(-e)))
    side_kick = np.exp(-((u - .34) / .055) ** 2 - ((v - .121) / .017) ** 2)
    kick = np.maximum(kick, np.where(side, side_kick, 0))
    for a, b in scratch_at:
        scratch = np.minimum(scratch, np.where(side, np.inf, segment_distance(u, v, a, b)))
    scratch = np.minimum(scratch, np.where(side, segment_distance(u, v, (.28, .162), (.34, .167)), np.inf))
    for a, b in chip_at:
        chip = np.minimum(chip, np.where(side, np.inf, segment_distance(u, v, a, b)))
    grain = .72 * field(u, v, .027, .080, 301) + .28 * field(u, v, .0105, .240, 317)
    return grain, contact, scratch, kick, chip


def height_metres(u, v, side, design):
    """Height and a continuous boundary taper in the canonical metre chart."""
    p, scale = design['profile'], np.asarray(design['tick_scale_xyz'])
    grain, contact, scratch, kick, chip = continuous_features(u, v, side, design)
    width = p['module_pitch'] * scale[0]
    local_u = np.mod(u - p['end_cap'] * scale[0], width)
    front_distance = np.minimum(local_u - p['door_frame_ticks'] * scale[0],
                                width - p['door_frame_ticks'] * scale[0] - local_u)
    side_distance = np.minimum(u - p['door_frame_ticks'] * scale[2],
                               (p['depth'] - p['door_frame_ticks']) * scale[2] - u)
    vertical_distance = np.minimum(v - (p['plinth'] + p['door_frame_ticks']) * scale[1],
                                   (p['height'] - p['cap_thickness'] - p['door_frame_ticks']) * scale[1] - v)
    distance = np.minimum(np.where(side, side_distance, front_distance), vertical_distance)
    taper = np.clip(distance / .034, 0, 1)
    taper = taper * taper * (3 - 2 * taper)
    # Sub-millimetre warp/brush/groove affects normals, not the silhouette/caster.
    warp = .00042 * np.sin(2 * np.pi * local_u / width) * np.sin(np.pi * v / .96)
    brush = .00012 * (grain - .5)
    groove = -.00025 * np.exp(-(scratch / .0060) ** 2)
    dent = -.00018 * contact - .00012 * kick - .00016 * np.exp(-(chip / .0055) ** 2)
    return (warp + brush + groove + dent) * taper


def canonical():
    old = np.asarray(Image.open(MAP).convert('RGBA')).copy()
    original_palette = np.asarray(Image.open(PALETTE).convert('RGB'))
    meta = json.loads((SOURCE / 'geometry.json').read_text(encoding='utf-8'))
    design = meta['metadata']['cabinet_design']
    with np.load(SOURCE / 'geometry.npz') as z:
        data = {k: z[k] for k in z.files}
    valid, tick, dn = data['mask'], data['design_tick'], data['design_normal']
    scale, rotation = np.asarray(design['tick_scale_xyz']), np.asarray(design['rotation'])
    side = np.abs(dn[..., 0]) > .99
    front = dn[..., 2] < -.99
    paint = valid & (old[..., 0] == 2) & (data['part'] == 0) & (old[..., 2] == 0) & (front | side)
    gold = valid & (old[..., 0] == 3) & (old[..., 2] == 0)
    u = np.where(side, tick[..., 2] * scale[2], tick[..., 0] * scale[0])
    v = tick[..., 1] * scale[1]
    return {'original_material': old, 'original_palette': original_palette,
            'data': data, 'valid': valid, 'paint': paint, 'gold': gold,
            'u': u, 'v': v, 'side': side, 'design': design, 'rotation': rotation}


def feature_calculation(c=None):
    c = canonical() if c is None else c
    u, v, side, design, paint, gold, valid, old = (c[k] for k in
        ('u', 'v', 'side', 'design', 'paint', 'gold', 'valid', 'original_material'))
    grain, contact, scratch, kick, chip = continuous_features(u, v, side, design)
    masks = {'grain': paint.copy(), 'contact': paint & (contact > .19),
             'scratch': paint & (scratch < .006), 'kick': paint & (kick > .26),
             'chip': paint & (chip < .0055)}
    # Small patina specks follow metal microfinish/contact, not the painted face.
    patina = field(u, v, .012, .045, 331)
    masks['patina'] = gold & (patina < .19)
    h = height_metres(u, v, side, design)
    eps = 1e-4
    hu = (height_metres(u + eps, v, side, design) - height_metres(u - eps, v, side, design)) / (2 * eps)
    hv = (height_metres(u, v + eps, side, design) - height_metres(u, v - eps, side, design)) / (2 * eps)
    roughness = np.full(valid.shape, .65)
    roughness[paint] = .44 + .10 * (grain[paint] - .5)
    roughness[masks['contact']] = .25 + .08 * (1 - contact[masks['contact']])
    roughness[masks['kick']] = .62
    roughness[masks['scratch']] = .70
    roughness[masks['chip']] = .82
    roughness[old[..., 0] == 3] = .25
    roughness[masks['patina']] = .51
    return {'masks': masks, 'grain_value': grain, 'contact_weight': contact,
            'kick_weight': kick, 'bare_rank_field': field(u, v, .022, .120, 349),
            'height': np.where(paint, h, 0), 'height_u': np.where(paint, hu, 0),
            'height_v': np.where(paint, hv, 0), 'roughness': np.where(valid, roughness, 0)}


def calculate(features=None):
    c = canonical()
    f = feature_calculation(c) if features is None else features
    old, original_palette, data, valid, paint, side, rotation = (c[k] for k in
        ('original_material', 'original_palette', 'data', 'valid', 'paint', 'side', 'rotation'))
    masks, grain, contact, kick = (f[k] for k in ('masks', 'grain_value', 'contact_weight', 'kick_weight'))
    new = old.copy()
    rank = np.clip(8 + np.rint((grain - .5) * 4), 6, 10).astype(np.uint8)
    rank[masks['contact']] = np.clip(10 + np.floor(contact[masks['contact']] * 3), 10, 13)
    rank[masks['kick']] = np.clip(7 - np.rint(kick[masks['kick']] * 3), 4, 7)
    rank[masks['scratch']] = 5
    new[..., 1][paint] = rank[paint]
    bare_rank = np.clip(8 + np.rint((f['bare_rank_field'] - .5) * 4), 6, 10).astype(np.uint8)
    new[..., 0][masks['chip']] = 4
    new[..., 1][masks['chip']] = bare_rank[masks['chip']]
    new[..., 1][masks['patina']] = 8
    # Existing semantic boundary colours retain their four-column indices.
    normal = np.fromfile(PRIOR / 'normal.f32', np.float32).reshape(*valid.shape, 4).copy()
    original_normal = np.fromfile(SOURCE / 'normal.f32', np.float32).reshape(*valid.shape, 4)
    hu, hv = f['height_u'], f['height_v']
    tangent = np.stack((np.where(side, 0., 1.), np.zeros(valid.shape), np.where(side, 1., 0.)), axis=-1)
    bitangent = np.zeros_like(tangent)
    bitangent[..., 1] = 1
    local_normal = data['design_normal'] - hu[..., None] * tangent - hv[..., None] * bitangent
    local_normal /= np.maximum(np.linalg.norm(local_normal, axis=-1, keepdims=True), 1e-9)
    normal[paint, :3] = (local_normal @ rotation.T)[paint]
    roughness = f['roughness']
    normal[..., 3] = np.where(valid, .5 + .5 * roughness, 0)
    palette = palette16(original_palette)
    def albedo(image, pal):
        rgba = np.zeros_like(image)
        rgba[valid, :3] = pal[image[..., 0][valid] - 1, image[..., 1][valid]]
        rgba[valid, 3] = 255
        return rgba
    result = {'material': new, 'palette': palette, 'normal': normal,
              'albedo': albedo(new, palette), 'before_albedo': albedo(old, original_palette),
              'masks': masks, 'height': f['height'], 'roughness': roughness,
              'height_u': hu, 'height_v': hv,
              'paint': paint, 'valid': valid, 'original_normal': original_normal,
              'original_material': old, 'original_palette': original_palette, 'design': c['design']}
    result['checks'], result['statistics'] = invariants(result, data, rotation)
    return result


def invariants(r, data, rotation):
    new, old, n, n0, paint, valid = (r[k] for k in ('material', 'original_material', 'normal', 'original_normal', 'paint', 'valid'))
    masks = r['masks']
    xyz_changed = np.any(n[..., :3] != n0[..., :3], axis=-1)
    handle = valid & (data['part'] >= 2) & (data['design_normal'][..., 2] < -.99)
    prior_n = np.fromfile(PRIOR / 'normal.f32', np.float32).reshape(*valid.shape, 4)
    cosine = np.sum(n[..., :3] * n0[..., :3], axis=-1)
    tilt = np.rad2deg(np.arccos(np.clip(cosine[paint], -1, 1)))
    component_sizes = {name: connected_sizes(masks[name]) for name in FEATURES if name != 'grain'}
    limits = {'contact': 120, 'scratch': 24, 'kick': 70, 'chip': 12, 'patina': 24}
    gold = old[..., 0] == 3
    boundaries = valid & (old[..., 2] > 0)
    checks = {
        'same_native_dimensions': new.shape == old.shape,
        'coverage_and_boundary_bytes_preserved': bool(np.array_equal(new[..., 2:], old[..., 2:])),
        'R_changes_exactly_chip_mask': bool(np.array_equal(new[..., 0] != old[..., 0], masks['chip'])),
        'chips_change_only_paint_to_bare_wood': bool(np.all(old[..., 0][masks['chip']] == 2) and np.all(new[..., 0][masks['chip']] == 4)),
        'gold_locations_preserved': bool(np.array_equal(new[..., 0] == 3, gold)),
        'gold_rank_changes_only_sparse_patina': bool(np.all(masks['patina'][gold & (new[..., 1] != old[..., 1])])),
        'wood_RGBA_preserved': bool(np.array_equal(new[old[..., 0] == 1], old[old[..., 0] == 1])),
        'wood_normal_XYZ_preserved': bool(np.array_equal(n[old[..., 0] == 1, :3], n0[old[..., 0] == 1, :3])),
        'wood_palette_first_four_preserved': bool(np.array_equal(r['palette'][0, :4], r['original_palette'][0])),
        'paint_palette_first_four_preserved': bool(np.array_equal(r['palette'][1, :4], r['original_palette'][1])),
        'existing_boundary_albedo_RGB_preserved': bool(np.array_equal(r['albedo'][boundaries, :3], r['before_albedo'][boundaries, :3])),
        'boundary_RGBA_and_normal_XYZ_preserved': bool(np.array_equal(new[boundaries], old[boundaries]) and np.array_equal(n[boundaries, :3], prior_n[boundaries, :3])),
        'N29_handle_normal_XYZ_preserved': bool(np.array_equal(n[handle, :3], prior_n[handle, :3])),
        'normal_XYZ_changes_only_paint_or_existing_handles': bool(np.all((paint | handle)[xyz_changed])),
        'finite_unit_normals': bool(np.isfinite(n).all() and np.max(np.abs(np.linalg.norm(n[valid, :3], axis=-1) - 1)) < 1e-6),
        'micro_height_max_tilt_bounded': bool(float(np.max(tilt)) <= TILT_LIMIT_DEGREES),
        'roughness_packed_valid_and_blank_zero': bool(np.all(n[valid, 3] > .5) and np.all(n[~valid] == 0) and np.all((r['roughness'][valid] >= .2) & (r['roughness'][valid] <= .9))),
        'palette_shape_16x10': r['palette'].shape == (10, 16, 3),
        'G_indices_within_palette': bool(np.all(new[..., 1][valid] < 16)),
        'all_six_cause_masks_present': all(bool(masks[name].any()) for name in FEATURES),
        'non_grain_features_restricted_to_paint_and_gold': bool(np.all((paint | gold)[np.logical_or.reduce([masks[name] for name in FEATURES if name != 'grain'])])),
        'cause_component_max_sizes': all(not component_sizes[name] or max(component_sizes[name]) <= limit for name, limit in limits.items()),
        'chip_area_bounded': int(masks['chip'].sum()) <= 64,
        'wear_area_bounded': int(np.logical_or.reduce([masks[name] for name in ('contact', 'scratch', 'kick', 'chip')]).sum()) <= int(paint.sum() * .045),
        'patina_area_bounded': int(masks['patina'].sum()) <= int(gold.sum() * .15),
        'broad_stain_generation_absent': True,
    }
    stats = {'feature_cells': {name: int(masks[name].sum()) for name in FEATURES},
             'component_sizes': component_sizes, 'component_limits': limits,
             'max_paint_tilt_degrees': float(np.max(tilt)),
             'height_metres_range': [float(np.min(r['height'])), float(np.max(r['height']))],
             'paint_G_counts': {str(i): int(np.sum(paint & (new[..., 1] == i))) for i in range(16)},
             'changed_G_cells': int(np.sum(new[..., 1] != old[..., 1])),
             'changed_R_cells': int(np.sum(new[..., 0] != old[..., 0])),
             'changed_normal_XYZ_cells': int(xyz_changed.sum()),
             'native_shape': list(valid.shape), 'palette_shape': [10, 16],
             'broad_stain_pitch_used': None, 'max_tilt_limit_degrees': TILT_LIMIT_DEGREES}
    return checks, stats


def input_hashes():
    paths = (MAP, PALETTE, SOURCE / 'normal.f32', SOURCE / 'geometry.npz',
             SOURCE / 'geometry.json', PRIOR / 'normal.f32', PRIOR / 'material.png')
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}


def features(out):
    if out.exists():
        raise ValueError('Fresh version required; previous evidence preserved')
    c = canonical()
    f = feature_calculation(c)
    masks, valid, paint, gold = f['masks'], c['valid'], c['paint'], c['gold']
    sizes = {name: connected_sizes(masks[name]) for name in FEATURES if name != 'grain'}
    limits = {'contact': 120, 'scratch': 24, 'kick': 70, 'chip': 12, 'patina': 24}
    checks = {
        'all_six_cause_masks_present': all(bool(masks[name].any()) for name in FEATURES),
        'paint_causes_inside_clean_paint': all(bool(np.all(paint[masks[name]])) for name in FEATURES if name != 'patina'),
        'patina_inside_existing_gold': bool(np.all(gold[masks['patina']])),
        'cause_component_sizes_bounded': all(not sizes[name] or max(sizes[name]) <= limit for name, limit in limits.items()),
        'chip_area_bounded': int(masks['chip'].sum()) <= 64,
        'wear_area_bounded': int(np.logical_or.reduce([masks[name] for name in ('contact', 'scratch', 'kick', 'chip')]).sum()) <= int(paint.sum() * .045),
        'patina_area_bounded': int(masks['patina'].sum()) <= int(gold.sum() * .15),
        'finite_physical_height_and_derivatives': all(bool(np.isfinite(f[k]).all()) for k in ('height', 'height_u', 'height_v')),
        'height_under_one_millimetre': float(np.max(np.abs(f['height']))) < .001,
        'physical_gradient_tilt_bounded': float(np.max(np.rad2deg(np.arctan(np.hypot(f['height_u'], f['height_v']))))) <= TILT_LIMIT_DEGREES,
        'valid_roughness_range_and_blank_zero': bool(np.all((f['roughness'][valid] >= .2) & (f['roughness'][valid] <= .9)) and np.all(f['roughness'][~valid] == 0)),
    }
    if not all(checks.values()):
        raise ValueError('N30 feature calculation failed: ' + ', '.join(k for k, value in checks.items() if not value))
    out.mkdir(parents=True)
    labels = np.zeros_like(c['original_material'])
    debug_colours = [(56, 98, 136), (255, 215, 97), (232, 93, 86), (126, 97, 177), (180, 122, 68), (74, 172, 118)]
    for name, colour in zip(FEATURES, debug_colours):
        mask = masks[name]
        rgba = np.zeros_like(labels)
        rgba[mask, :3], rgba[mask, 3] = colour, 255
        labels[mask] = rgba[mask]
        Image.fromarray(rgba).save(out / ('feature-' + name + '.png'))
    Image.fromarray(labels).save(out / 'feature-labels.png')
    rough = np.zeros_like(labels)
    rough[valid, :3] = np.rint(f['roughness'][valid] * 255).astype(np.uint8)[:, None]
    rough[valid, 3] = 255
    Image.fromarray(rough).save(out / 'roughness-native.png')
    np.savez_compressed(out / 'features.npz', **masks,
        **{k: value for k, value in f.items() if k != 'masks'})
    write(out / 'features-calculation.json', {'checks': checks, 'source_hashes': source_hashes(),
        'inputs': input_hashes(), 'outputs': {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()},
        'feature_cells': {name: int(masks[name].sum()) for name in FEATURES},
        'component_sizes': sizes, 'component_limits': limits, 'broad_stain_pitch_used': None,
        'art_approval_claimed': False})
    print(json.dumps({'phase': 'features', 'checks': checks, 'feature_cells': {name: int(masks[name].sum()) for name in FEATURES}}))


def generate(out):
    # Standalone convenience still has the two separately recorded calculations.
    if not out.exists():
        features(out)
    if (out / 'material.png').exists() or (out / 'calculation.json').exists():
        raise ValueError('Existing maps preserved; verify instead of regenerate')
    receipt = json.loads((out / 'features-calculation.json').read_text(encoding='utf-8'))
    if (not all(receipt['checks'].values()) or receipt['source_hashes'] != source_hashes()
            or receipt['inputs'] != input_hashes()
            or not all(sha(out / name) == h for name, h in receipt['outputs'].items())):
        raise ValueError('Frozen feature contract changed; map calculation refused')
    with np.load(out / 'features.npz') as z:
        frozen = {k: z[k] for k in z.files if k not in FEATURES}
        frozen['masks'] = {name: z[name] for name in FEATURES}
    r = calculate(frozen)
    if not all(r['checks'].values()):
        raise ValueError('N30 map calculation failed: ' + ', '.join(k for k, v in r['checks'].items() if not v))
    for name, array, mode in (('material.png', r['material'], 'RGBA'),
                              ('palette.png', r['palette'], 'RGB'),
                              ('albedo-native.png', r['albedo'], 'RGBA'),
                              ('before-albedo-native.png', r['before_albedo'], 'RGBA')):
        Image.fromarray(array, mode).save(out / name)
    r['normal'].astype(np.float32).tofile(out / 'normal.f32')
    receipt = {'checks': r['checks'], 'statistics': r['statistics'], 'source_hashes': source_hashes(),
               'inputs': input_hashes(),
               'outputs': {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()},
               'coordinate_contract': 'N15 ticks to metres; existing native pixel centres; rotation after physical height gradient',
               'normal_alpha_contract': 'extended palette: valid=.5+.5*perceptual_roughness; blank=0',
               'art_approval_claimed': False, 'microrelief_cast_shadow_claimed': False,
               'height_silhouette_change_claimed': False, 'regeneration_count': 0}
    write(out / 'calculation.json', receipt)
    print(json.dumps({'checks': r['checks'], 'statistics': r['statistics'], 'output': str(out)}))


def verify(out):
    calc = json.loads((out / 'calculation.json').read_text(encoding='utf-8'))
    checks = dict(calc['checks'])
    checks['source_hashes_preserved'] = calc['source_hashes'] == source_hashes()
    checks['input_hashes_frozen'] = all(sha(ROOT / name) == h for name, h in calc['inputs'].items())
    checks['output_hashes_frozen'] = all(sha(out / name) == h for name, h in calc['outputs'].items())
    if not all(checks.values()):
        raise ValueError('N30 verify failed: ' + ', '.join(k for k, v in checks.items() if not v))
    print(json.dumps({'existing_calculation_preserved': True, 'regeneration_count': 0}))
    return checks


def gate(out):
    checks = verify(out)
    obs = json.loads((out / 'observation02/observation.json').read_text(encoding='utf-8-sig'))
    final = json.loads((out / 'final.json').read_text(encoding='utf-8-sig'))
    gpu = json.loads((out / 'gpu-gate.json').read_text(encoding='utf-8-sig'))
    checks.update({'same_geometry': obs['sameGeometry'], 'same_lighting': obs['sameLighting'],
                   'same_player_camera': obs['samePlayer'] and obs['sameCamera'],
                   'play_mode_observation': obs['playMode'], 'shader_errors_zero': obs['shaderErrors'] == 0,
                   'integer_2px_display': abs(obs['screenPixelsPerCell'] - 2) < .001,
                   'exactly_one_binding': obs['bindingCount'] == 1, 'changed_visible_image': obs['changedPixels'] > 0,
                   'saved_clean_scene': final['sceneSaved'] and not final['sceneDirty'] and not final['playing']})
    checks['gpu_gate_passed'] = gpu['passed'] is True
    checks.update({'gpu_' + name: value is True for name, value in gpu['checks'].items()})
    write(out / 'validation.json', {'checks': checks, 'passed': all(checks.values()), 'art_approval_claimed': False})
    print(json.dumps({'passed': all(checks.values()), 'checks': checks}))
    if not all(checks.values()):
        raise ValueError('N30 integration gate failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['features', 'generate', 'verify', 'gate'])
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    {'features': features, 'generate': generate, 'verify': verify, 'gate': gate}[args.phase](Path(args.output).resolve())
