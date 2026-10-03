"""Native cabinet authoring: geometry -> source material -> light -> edge roles.

The final image is never resized as a production step. Pixel coverage is owned
exclusively by geometry; edges and decals cannot create a new occupied pixel.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from PIL import Image
from native14_materials import Appearance
from native15_geometry import generate, project, shadow, write_assets

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'Tools/PixelPipeline'))
from common import surface_boundaries


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def items(recipe):
    return [(mode, count) for mode in recipe['modes'] for count in recipe['variants']]


def buffers(output, mode, count):
    with np.load(output/'geometry'/mode/f'buffers{count}.npz') as z:
        value = {key: z[key] for key in z.files}
    value['metadata'] = read(output/'geometry'/mode/f'geometry{count}.json')
    value['origin'] = value['metadata']['origin']
    value['size'] = value['metadata']['size']
    return value


def canonical_line(a, b):
    """One discrete path with an endpoint-order-independent half-step rule."""
    a, b = sorted((tuple(map(int, a)), tuple(map(int, b))))
    x, y = a; tx, ty = b
    dx = abs(tx-x); dy = -abs(ty-y)
    sx = 1 if x < tx else -1; sy = 1 if y < ty else -1
    error = dx+dy; output = []
    while True:
        output.append((x, y))
        if x == tx and y == ty:
            return output
        twice = 2*error
        if twice >= dy:
            error += dy; x += sx
        if twice <= dx:
            error += dx; y += sy


def geometry(recipe, output):
    for mode, count in items(recipe):
        write_assets(generate(recipe['profile'], count, mode),
                     output/'geometry'/mode, count)


def details(recipe, count, b):
    """Flush material inlays, not invented frame volume or an upper gold strip."""
    p = recipe['profile']; w = 2*p['end_cap']+count*p['module_pitch']
    x, y, z = np.moveaxis(b['position'], -1, 0)
    material = np.zeros(b['mask'].shape, np.int8)
    material[b['part'] == 0] = 1
    material[b['part'] == 1] = 2
    material[b['part'] >= 2] = 3
    front = (b['part'] == 0) & (b['face'] == 4)
    side = (b['part'] == 0) & (b['face'] == 0)
    # Existing reference corner hardware stays flush inside the body bounds.
    posts = front & ((x < 1) | (x >= w-1))
    posts |= side & ((z < 1) | (z >= p['depth']-1))
    material[posts] = 3
    endplates = front & ((x < 4) | (x >= w-4)) & ((y < 4) | (y >= 64))
    endplates |= side & ((z < 4) | (z >= p['depth']-4)) & ((y < 4) | (y >= 64))
    material[endplates] = 3
    for index in range(count):
        start = p['end_cap']+index*p['module_pitch']
        for height in (19, 57):
            material[front & (x >= start) & (x < start+1) &
                     (y >= height) & (y < height+4)] = 3
    # Thin decorative inlays are canonical surface lines; no alpha expansion.
    paths = []
    for index in range(count):
        start = p['end_cap']+index*p['module_pitch']
        vertices = [(start+3, 12, 0), (start+17, 12, 0),
                    (start+17, 58, 0), (start+3, 58, 0)]
        paths.extend(zip(vertices, vertices[1:]+vertices[:1]))
    paths += [((1, 8, 0), (w-1, 8, 0)),
              ((0, 12, 3), (0, 12, p['depth']-3)),
              ((0, 12, p['depth']-3), (0, 58, p['depth']-3)),
              ((0, 58, p['depth']-3), (0, 58, 3)),
              ((0, 58, 3), (0, 12, 3))]
    for a, end in paths:
        # One declared endpoint phase; bankers' rounding must not change slope.
        endpoints = np.floor(project([a, end])+b['origin']).astype(int)
        for px, py in canonical_line(*endpoints):
            if (0 <= py < material.shape[0] and 0 <= px < material.shape[1]
                    and b['part'][py, px] == 0
                    and b['face'][py, px] == (4 if a[2] == end[2] == 0 else 0)):
                material[py, px] = 3
    return material


def material(recipe, reference, output):
    directory = output/'material'; directory.mkdir()
    appearance = Appearance(reference, recipe['materials'])
    write(directory/'palette.json', {k: p.tolist() for k, p in appearance.palettes.items()})
    write(directory/'provenance.json', appearance.report())
    for mode, count in items(recipe):
        b = buffers(output, mode, count)
        ids = details(recipe, count, b)
        grain = np.full(b['mask'].shape, 2, np.int8)
        top = (b['part'] == 1) & (b['face'] == 3)
        positions = b['position'][top]
        u = (positions[:, 0]+1)/(recipe['profile']['reference_width']+2)
        v = (positions[:, 2]+1)/(recipe['profile']['depth']+2)
        colors = appearance.sample('wood', u, v)
        grain[top] = np.argmin(np.sum((colors[:, None].astype(int)-
                         appearance.palettes['wood'][None].astype(int))**2, axis=2), axis=1)
        dest = directory/mode; dest.mkdir(exist_ok=True)
        np.savez_compressed(dest/f'materials{count}.npz', material=ids, grain=grain,
                            decal=(b['part'] == 0) & (ids == 3))


def shade(recipe, output):
    palette = {k: np.array(p, np.uint8) for k, p in read(output/'material/palette.json').items()}
    light = np.array(recipe['lighting']['to_light_world'], float)
    light /= np.linalg.norm(light)
    paint = np.array([palette['side'][1], palette['navy'][1], palette['navy'][2]])
    for mode, count in items(recipe):
        b = buffers(output, mode, count)
        with np.load(output/'material'/mode/f'materials{count}.npz') as z:
            ids, grain = z['material'], z['grain']
        band = np.digitize(b['normal']@light, recipe['lighting']['thresholds']).astype(np.int8)
        occluded = shadow(recipe['profile'], count, b, light)
        rgb = np.zeros((*b['mask'].shape, 3), np.uint8)
        for ident, colors in [(1, paint), (3, palette['brass'])]:
            area = ids == ident; rgb[area] = colors[band[area]]
        top = (ids == 2) & (b['face'] == 3)
        fascia = (ids == 2) & ~top
        rgb[top] = palette['wood'][np.clip(grain[top]+band[top]-2, 0, 3)]
        rgb[fascia] = palette['wood'][band[fascia]]
        for ident, darkest in [(1, palette['navy'][0]), (2, palette['wood'][0]),
                               (3, palette['brass'][0])]:
            rgb[occluded & (ids == ident)] = darkest
        dest = output/'shade'/mode; dest.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(dest/f'shade{count}.npz', rgb=rgb, band=band,
                            shadow=occluded, material=ids)
        Image.fromarray((occluded*255).astype(np.uint8)).save(dest/f'shadow-{count}.png')


def edge_roles(recipe, count, b, materials):
    groups, silhouette = surface_boundaries(b)
    roles = np.zeros(b['mask'].shape, np.uint8); policies = []
    view = np.array([np.sqrt(3/8), -np.sqrt(3/8), .5])
    for key, pairs in groups.items():
        # Cap/body contact is represented by visibility + material + shadow.
        parts = {key[0][0], key[1][0]}
        if parts == {0, 1}:
            policies.append({'pair':key, 'role':0, 'rule':'actual_contact_no_extra_line'})
            continue
        a, c = pairs[0]
        score = [float(b['normal'][q]@view) for q in (a, c)]
        parallel = float(b['normal'][a]@b['normal'][c]) > .9999
        if parallel:
            score = [-float(b['depth'][q]) for q in (a, c)]
        owner = max(range(2), key=lambda i: (round(score[i], 7), key[i][1]))
        owner_roles = set()
        for pair in pairs:
            q = pair[owner]
            role = {1:3, 2:4, 3:5}[int(materials[q])]
            roles[q] = role; owner_roles.add(role)
        policies.append({'pair':key, 'owner':key[owner], 'roles':sorted(owner_roles),
                         'rule':'nearer_parallel' if parallel else 'camera_facing',
                         'pairs':len(pairs)})
    p = recipe['profile']; pos = b['position']
    labels = np.floor((pos[..., 0]-p['end_cap'])/p['module_pitch']).astype(int)
    active = ((b['part'] == 0) & (b['face'] == 4) & (pos[..., 1] >= 6) &
              (pos[..., 1] < 66) & (labels >= 0) & (labels < count))
    # A door gap is one path on the lower indexed door side, not two outlines.
    for dy, dx in ((0, 1), (1, 0)):
        h, w = active.shape
        for y in range(h-dy):
            for x in range(w-dx):
                a = (y, x); c = (y+dy, x+dx)
                if active[a] and active[c] and labels[a] != labels[c]:
                    roles[a if labels[a] < labels[c] else c] = 2
    roles[silhouette] = 1
    return roles, policies


def raster(recipe, output):
    palette = read(output/'material/palette.json')
    for mode, count in items(recipe):
        b = buffers(output, mode, count)
        with np.load(output/'shade'/mode/f'shade{count}.npz') as z:
            rgb = z['rgb'].copy(); materials = z['material']
        roles, policies = edge_roles(recipe, count, b, materials)
        strong = (roles == 1) | (roles == 2)
        for role, color in [(3, palette['navy'][0]), (4, palette['wood'][0]),
                            (5, palette['brass'][0])]:
            rgb[roles == role] = color
        rgb[strong] = 0
        rgba = np.dstack((rgb, (b['mask']*255).astype(np.uint8)))
        dest = output/'raster'/mode; dest.mkdir(parents=True, exist_ok=True)
        image = Image.fromarray(rgba); image.save(dest/f'cabinet-{count}.png')
        np.savez_compressed(dest/f'owners{count}.npz', roles=roles, strong=strong)
        write(dest/f'policies{count}.json', policies)
        role_colors = np.array([[0,0,0],[255,255,255],[230,110,110],[65,160,215],
                                [195,125,50],[240,205,70]], np.uint8)
        Image.fromarray(role_colors[roles]).save(dest/f'edge-roles-{count}.png')
        preview = Image.new('RGBA', (image.width*4, image.height*4), (180,180,172,255))
        preview.alpha_composite(image.resize(preview.size, Image.Resampling.NEAREST))
        preview.convert('RGB').save(dest/f'preview-{count}-x4.png')
    for mode in recipe['modes']:
        Image.open(output/'raster'/mode/'cabinet-3.png').save(output/f'{mode}-native.png')
        Image.open(output/'raster'/mode/'preview-3-x4.png').save(output/f'{mode}-preview-x4.png')
    left = Image.open(output/'planar-preview-x4.png'); right = Image.open(output/'solid-preview-x4.png')
    sheet = Image.new('RGB', (left.width+right.width+24, max(left.height,right.height)), (180,180,172))
    sheet.paste(left, (0,0)); sheet.paste(right, (left.width+24,0))
    sheet.save(output/'comparison-x4.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['geometry','material','shade','raster','validate'])
    for name in ('recipe','reference','output'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args(); sys.stdout.reconfigure(encoding='utf-8')
    output = Path(args.output).resolve(); reference = Path(args.reference).resolve()
    recipe = read(args.recipe)
    if not output.is_relative_to(ROOT) or sha(reference) != recipe['reference_sha256']:
        raise ValueError('Workspace output and immutable reference required')
    output.mkdir(exist_ok=True); started = time.perf_counter()
    if args.stage == 'material': material(recipe, reference, output)
    elif args.stage == 'validate':
        from native15_validation import validate
        report = validate(recipe, reference, output); write(output/'validation.json', report)
        print(json.dumps({'all_pass':report['all_pass'], 'checks':len(report['checks']),
                          'failed':[c for c in report['checks'] if not c['pass']]}))
        if not report['all_pass']: raise SystemExit(2)
    else: globals()[args.stage](recipe, output)
    write(output/(args.stage+'-receipt.json'), {'stage':args.stage,
        'wall_seconds':time.perf_counter()-started, 'recipe_sha256':sha(args.recipe),
        'reference_sha256':sha(reference)})
