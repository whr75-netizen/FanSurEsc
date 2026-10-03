"""Source RGB roles -> finite parametric geometry -> native palette pixels.

CLI stages intentionally have immutable separate output directories. Generated
material authoring is lossy and explicit; it is not PerfectPixel grid recovery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Tools/PixelPipeline'))
from common import consistent_edges

RECIPE = ROOT / 'Tools/PerfectPixelUniform/recipe06.json'
DEFAULT_OUT = ROOT / 'docs/artifacts/building37/Parametric06'
BLENDER = Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    with Path(path).open('w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def fresh(path):
    Path(path).mkdir(parents=True, exist_ok=False)


def inputs(paths):
    return {str(Path(p).resolve()): sha(p) for p in paths}


def connected8(mask):
    """Ordinary eight-neighbour flood fill; no additional package dependency."""
    ids = np.zeros(mask.shape, dtype='int32')
    areas = [int((~mask).sum())]
    h,w = mask.shape
    for y,x in np.argwhere(mask):
        if ids[y,x]:
            continue
        index = len(areas)
        ids[y,x] = index
        stack, area = [(int(y),int(x))], 0
        while stack:
            yy,xx = stack.pop()
            area += 1
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    ny,nx = yy+dy,xx+dx
                    if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not ids[ny,nx]:
                        ids[ny,nx] = index
                        stack.append((ny,nx))
        areas.append(area)
    return ids, np.asarray(areas)


def material(recipe, output):
    started = time.perf_counter()
    if recipe['wood_variation_classes'] != 2:
        raise ValueError('Reviewed material uses two explicit grain roles')
    source = ROOT / recipe['source']
    if sha(source) != recipe['source_sha256']:
        raise ValueError('Generated source bytes changed')
    original = Image.open(source)
    if original.mode not in ('RGB', 'RGBA') or original.size != (1254,1254):
        raise ValueError('Reviewed source mode/size changed')
    rgba = np.asarray(original.convert('RGBA'))
    colors, samples = {}, []
    for role, x in recipe['palette_sample_columns'].items():
        colors[role] = []
        for band, y in enumerate(recipe['palette_sample_rows']):
            if int(rgba[y,x,3]) != 255:
                raise ValueError('Nonopaque palette sample')
            rgb = [int(c) for c in rgba[y,x,:3]]
            colors[role].append(rgb)
            samples.append({'role':role, 'band':band, 'source_xy':[x,y], 'rgb':rgb})
    x0,y0,x1,y1 = recipe['wood_roi']
    crop = rgba[y0:y1,x0:x1]
    if not (crop[...,3] == 255).all():
        raise ValueError('Nonopaque material ROI')
    luminance = crop[...,:3] @ np.array([.2126,.7152,.0722])
    threshold = float(np.percentile(luminance,25))
    width = int(recipe['wood_tile_length_ticks'] * 2)
    height = round(width * (y1-y0) / (x1-x0))
    xx = np.floor((np.arange(width)+.5) * (x1-x0)/width).astype(int)
    yy = np.floor((np.arange(height)+.5) * (y1-y0)/height).astype(int)
    candidate = luminance[np.ix_(yy,xx)] < threshold
    components, areas = connected8(candidate)
    count = len(areas)-1
    removed_ids = np.flatnonzero((areas < recipe['grain_minimum_component_pixels']) & (np.arange(len(areas)) > 0))
    grain = candidate & ~np.isin(components, removed_ids)
    out = output / 'material'
    fresh(out)
    np.save(out/'grain.npy',grain)
    Image.fromarray(np.where(grain,0,255).astype('uint8')).save(out/'grain-role.png')
    Image.fromarray(crop).save(out/'source-wood-roi.png')
    palette = {'schema':'source-pixel-role-palette/1', 'source_sha256':sha(source),
               'colors_srgb8byrole':colors, 'samples':samples, 'new_rgb_synthesized':False}
    write(out/'palette.json',palette)
    swatch = Image.new('RGB',(3*64,4*40))
    draw = ImageDraw.Draw(swatch)
    for i, role in enumerate(colors):
        for j, rgb in enumerate(colors[role]):
            draw.rectangle((i*64,j*40,i*64+63,j*40+39),fill=tuple(rgb))
    swatch.save(out/'palette.png')
    write(out/'material.json',{'inputs':inputs([source,RECIPE,__file__]),
          'palette_sha256':sha(out/'palette.json'),'grain_sha256':sha(out/'grain.npy'),
          'grain_shape':list(grain.shape),'wood_roi':recipe['wood_roi'],
          'luma_percentile':25,'threshold':threshold,'comparison':'strictly less than',
          'candidate_grain_pixels':int(candidate.sum()),'retained_grain_pixels':int(grain.sum()),
          'components_before':int(count),'removed_components':int(len(removed_ids)),
          'removed_pixels':int((candidate&~grain).sum()),
          'tile_ticks':[recipe['wood_tile_length_ticks'],recipe['wood_tile_length_ticks']*(y1-y0)/(x1-x0)],
          'source_sampling':'one ROI centre pixel per UV texel; no RGB averages',
          'lossy_material_authoring':True,'final_png_resize':False,
          'elapsed_seconds':time.perf_counter()-started})


def geometry(recipe, output):
    started = time.perf_counter()
    out = output / 'geometry'
    if out.exists():
        raise FileExistsError('Geometry output already exists')
    script = ROOT/'Tools/PerfectPixelUniform/cabinet_geometry06.py'
    argv = [str(BLENDER),'--background','--factory-startup','--python',str(script),
            '--','--recipe',str(RECIPE),'--output',str(out),'--palette',str(output/'material/palette.json')]
    process = subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=55)
    # Keep process evidence even if the producer stops before creating outputs.
    out.mkdir(parents=True,exist_ok=True)
    (out/'stdout.txt').write_bytes(process.stdout)
    (out/'stderr.txt').write_bytes(process.stderr)
    write(out/'execution.json',{'argv':argv,'exit_code':process.returncode,
          'elapsed_seconds':time.perf_counter()-started,
          'inputs':inputs([RECIPE,script,ROOT/'Tools/PixelPipeline/common.py',output/'material/palette.json']),
          'stdout_sha256':sha(out/'stdout.txt'),'stderr_sha256':sha(out/'stderr.txt')})
    if process.returncode:
        raise RuntimeError(process.stderr.decode('utf-8',errors='replace') + process.stdout.decode('utf-8',errors='replace'))


def pixels(recipe, output):
    started = time.perf_counter()
    palette_path = output/'material/palette.json'
    material_path = output/'material/material.json'
    palette, info = read(palette_path), read(material_path)
    if sha(output/'material/grain.npy') != info['grain_sha256'] or sha(palette_path) != info['palette_sha256']:
        raise ValueError('Material provenance mismatch')
    grain_map = np.load(output/'material/grain.npy')
    colors = {k:np.array(v,dtype='uint8') for k,v in palette['colors_srgb8byrole'].items()}
    out = output/'pixels'
    fresh(out)
    previews = []
    for count in recipe['variants']:
        buffers_path = output/'geometry'/f'buffers{count}.npz'
        raster_path = output/'geometry'/f'raster{count}.json'
        b = dict(np.load(buffers_path)); raster = read(raster_path)
        if sha(buffers_path) != raster['buffers_sha256']:
            raise ValueError('Geometry buffers changed')
        mask, part = b['mask'], b['part']
        light = np.asarray(raster['to_light_world'])
        dot = b['normals'] @ light
        low,high = recipe['lighting']['band_thresholds']
        band = np.where(dot >= high,0,np.where(dot >= low,1,2)).astype('uint8')
        band[mask & ~b['visibility']] = 2
        local_x = b['positions'][...,1]*32
        local_y = b['positions'][...,2]*32*math.sqrt(6)
        local_z = -b['positions'][...,0]*32
        # The UV period belongs to physical ticks, never object or canvas width.
        tex_u = np.where(np.abs(b['normals'][...,1]) > .5,local_z,local_x)
        tex_v = np.where(np.abs(b['normals'][...,2]) > .5,local_z,local_y)
        uvx = np.floor(np.mod(tex_u,info['tile_ticks'][0]) / info['tile_ticks'][0]*grain_map.shape[1]).astype(int)
        uvy = np.floor(np.mod(tex_v,info['tile_ticks'][1]) / info['tile_ticks'][1]*grain_map.shape[0]).astype(int)
        uvx = np.clip(uvx,0,grain_map.shape[1]-1); uvy = np.clip(uvy,0,grain_map.shape[0]-1)
        wood = np.zeros_like(mask)
        for group in raster['parts']:
            if group['role']=='wood': wood |= part==group['id']
        grain = wood & grain_map[uvy,uvx]
        index = np.minimum(band+grain.astype('uint8'),3)
        ink, records, policies = consistent_edges(b,recipe['camera'])
        index[ink] = 3
        rgba = np.zeros((*mask.shape,4),dtype='uint8')
        for group in raster['parts']:
            region = part==group['id']
            rgba[region,:3] = colors[group['role']][index[region]]
        rgba[mask,3] = 255
        native_path = out/f'native{count}.png'
        Image.fromarray(rgba).save(native_path)
        preview = np.repeat(np.repeat(rgba,4,0),4,1)
        Image.fromarray(preview).save(out/f'preview{count}-x4.png')
        previews.append(preview)
        np.savez_compressed(out/f'shading{count}.npz',ink=ink,band=band,grain=grain,palette_index=index,
                            edge_records=records,uvx=uvx,uvy=uvy)
        Image.fromarray(np.where(mask[...,None],np.rint((b['normals']+1)*127.5),0).astype('uint8')).save(out/f'normals{count}.png')
        visibility = np.where(mask,np.where(b['visibility'],255,80),0).astype('uint8')
        Image.fromarray(visibility).save(out/f'visibility{count}.png')
        write(out/f'pixel{count}.json',{'count':count,'size':[rgba.shape[1],rgba.shape[0]],
          'inputs':inputs([buffers_path,raster_path,palette_path,material_path,output/'material/grain.npy',RECIPE,__file__,ROOT/'Tools/PixelPipeline/common.py']),
          'outputs':inputs([native_path,out/f'preview{count}-x4.png',out/f'shading{count}.npz']),
          'grain_pixels':int(grain.sum()),'ink_pixels':int(ink.sum()),
          'band_pixels':{str(i):int((mask&(band==i)).sum()) for i in range(3)},
          'edge_policies':policies,'image_resize':False,'rgb_blending':False,
          'native_surface_depth_ownership':True,'preview_scale':4})
    canvas = Image.new('RGB',(sum(p.shape[1] for p in previews)+48,max(p.shape[0] for p in previews)+60),(20,24,33))
    x = 16
    draw = ImageDraw.Draw(canvas)
    for n,preview in zip(recipe['variants'],previews):
        im = Image.fromarray(preview)
        canvas.paste(im,(x,36),im)
        draw.text((x,12),f'{n} bays | native {im.width//4} x {im.height//4} | exact 4x',fill=(240,240,240))
        x += im.width+16
    canvas.save(out/'comparison-x4.png')
    write(out/'execution.json',{'stage':'native palette fill and visible stroke','elapsed_seconds':time.perf_counter()-started})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['material','geometry','pixels'])
    parser.add_argument('--output',type=Path,default=DEFAULT_OUT)
    args = parser.parse_args()
    recipe = read(RECIPE)
    globals()[args.stage](recipe,args.output.resolve())
    print(json.dumps({'stage':args.stage,'output':str(args.output.resolve())}))


if __name__ == '__main__':
    main()
