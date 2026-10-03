"""Exact closed-box primary rays for repeated handles; preserve all other surfaces."""
from fractions import Fraction
from pathlib import Path
import argparse
import json
import math
import shutil
import sys
import time
import numpy as np
from PIL import Image, ImageDraw
from cabinet_pipeline06 import ROOT, read, write, sha, inputs

RECIPE = ROOT/'Tools/PerfectPixelUniform/recipe09.json'
CONFIG = read(RECIPE)
OLD = ROOT/CONFIG['previous_geometry']
WOOD = ROOT/CONFIG['previous_material']
OUT = ROOT/CONFIG['output']
sys.path.insert(0,str(ROOT/'Tools/PixelPipeline'))
from common import basis


def exact_hits(boxes, meta):
    values = [Fraction(str(v)) for box in boxes
              for key in ('local_minimum_ticks','local_maximum_ticks') for v in box[key]]
    scale = 2*math.lcm(8,*(value.denominator for value in values))
    if scale > 1000000: raise ValueError('Unsupported rational bounds')
    height,width = meta['size'][1],meta['size'][0]
    ox,oy = meta['screen_origin']
    if [ox,oy] != [int(ox),int(oy)]: raise ValueError('Noninteger canvas origin')
    yy,xx = np.indices((height,width),dtype=np.int64)
    uh = ((2*(xx+int(ox))+1)*scale)//4
    vy = ((2*(yy+int(oy))+1)*scale)//2
    base_y = -vy-uh
    best = np.full((height,width),np.iinfo(np.int64).max,np.int64)
    owner = np.full((height,width),-1,np.int32)
    face = np.full_like(owner,-1); rank = np.full_like(owner,9)
    # Geometry bounds resolve coincident solids, independent of names/creation order.
    for box in sorted(boxes,key=lambda b:tuple(b['local_minimum_ticks']+b['local_maximum_ticks'])):
        lo,hi = [[int(Fraction(str(v))*scale) for v in box[k]]
                 for k in ('local_minimum_ticks','local_maximum_ticks')]
        a,b,c = lo[0]-uh,(base_y-hi[1])//2,np.full_like(best,lo[2])
        entry = np.maximum(np.maximum(a,b),c)
        exit = np.minimum(np.minimum(hi[0]-uh,(base_y-lo[1])//2),hi[2])
        # At camera-facing ties: -local z, -local x, +local y.
        f = np.where(c==entry,1,np.where(a==entry,2,5)).astype(np.int32)
        priority = np.where(f==1,0,np.where(f==2,1,2))
        take = (entry<=exit)&((entry<best)|((entry==best)&(priority<rank)))
        best[take]=entry[take]; owner[take]=box['part']; face[take]=f[take]; rank[take]=priority[take]
    return owner,face,best,scale,uh/scale,base_y/scale


def shadow_visibility(positions,normals,boxes,meta):
    start=positions+normals*meta['shadow_offset_m']; light=np.array(meta['to_light_world'])
    visible=np.ones(len(start),bool)
    for box in boxes:
        lo=np.array(box['minimum']); hi=np.array(box['maximum'])
        near=np.full(len(start),-np.inf); far=np.full(len(start),np.inf)
        for axis in range(3):
            if abs(light[axis])<1e-12:
                far[(start[:,axis]<lo[axis])|(start[:,axis]>hi[axis])]=-np.inf
            else:
                t0=(lo[axis]-start[:,axis])/light[axis]; t1=(hi[axis]-start[:,axis])/light[axis]
                near=np.maximum(near,np.minimum(t0,t1)); far=np.minimum(far,np.maximum(t0,t1))
        visible &= far < np.maximum(near,0.)
    return visible


def geometry(output):
    started=time.perf_counter(); directory=output/'base/geometry'; directory.mkdir(parents=True,exist_ok=False)
    parts=read(OLD/'geometry/parts.json')
    for spec in parts['variants']:
        n=spec['count']; meta=read(OLD/f'geometry/raster{n}.json')
        if (meta['camera']['azimuth_degrees']!=45 or meta['camera']['elevation_degrees']!=30
            or not math.isclose(meta['pixels_per_meter'],64*math.sqrt(2),abs_tol=1e-10)):
            raise ValueError('This exact ray supports only the fixed camera')
        b=dict(np.load(OLD/f'geometry/buffers{n}.npz'))
        owner,face,t,scale,uh,base_y=exact_hits(spec['boxes'],meta)
        ids=[g['id'] for g in spec['groups'] if g['name'].endswith('Handle')]
        repair=np.isin(owner,ids)|np.isin(b['part'],ids)
        if not b['mask'][repair].all() or (owner[repair]<0).any(): raise AssertionError('Unexpected exterior handle ray')
        local_t=t[repair]/scale
        local=np.column_stack((uh[repair]+local_t,base_y[repair]-2*local_t,local_t))
        position=np.column_stack((-local[:,2]/32,local[:,0]/32,local[:,1]/(32*math.sqrt(6))))
        normal=np.zeros_like(position)
        normal[face[repair]==1,0]=1; normal[face[repair]==2,1]=-1; normal[face[repair]==5,2]=1
        _,_,view=basis(meta['camera'])
        b['positions'][repair]=position; b['normals'][repair]=normal
        b['part'][repair]=owner[repair]; b['face'][repair]=face[repair]
        b['depth'][repair]=meta['camera_distance']-position@view
        b['visibility'][repair]=shadow_visibility(position,normal,spec['boxes'],meta)
        b['repair']=repair; np.savez_compressed(directory/f'buffers{n}.npz',**b)
        meta.update(buffers_sha256=sha(directory/f'buffers{n}.npz'),
                    exact_handle_rays={'scale':scale,'boundary':'closed','repair_pixels':int(repair.sum())},
                    slab_checks=[],shadow_pixels=int((b['mask']&~b['visibility']).sum()))
        write(directory/f'raster{n}.json',meta)
    shutil.copy2(OLD/'geometry/scene.blend',directory/'scene.blend')
    shutil.copy2(OLD/'geometry/parts.json',directory/'parts.json')
    shutil.copytree(OLD/'material',output/'base/material')
    write(output/'geometry.json',{'inputs':inputs([RECIPE,__file__,OLD/'geometry/parts.json',OLD/'geometry/scene.blend']),
          'mesh_changed':False,'elapsed_seconds':time.perf_counter()-started})


def pixels(output):
    started=time.perf_counter()
    import cabinet_pipeline06 as core
    core.pixels(read(core.RECIPE),output/'base')
    directory=output/'pixels'; directory.mkdir(exist_ok=False)
    levels=np.load(WOOD/'wood-levels.npy'); palette=read(OLD/'material/palette.json')
    wood=np.array(palette['colors_srgb8byrole']['wood'],np.uint8); previews=[]
    for n in CONFIG['variants']:
        b=dict(np.load(output/f'base/geometry/buffers{n}.npz'))
        s=dict(np.load(output/f'base/pixels/shading{n}.npz'))
        meta=read(output/f'base/geometry/raster{n}.json')
        rgba=np.array(Image.open(output/f'base/pixels/native{n}.png').convert('RGBA'))
        region=np.isin(b['part'],[g['id'] for g in meta['parts'] if g['role']=='wood'])&~s['ink']
        index=np.minimum(s['band']+levels[s['uvy'],s['uvx']],3)
        rgba[region,:3]=wood[index[region]]
        path=directory/f'native{n}.png'; Image.fromarray(rgba).save(path)
        preview=np.repeat(np.repeat(rgba,4,0),4,1); previews.append(preview)
        Image.fromarray(preview).save(directory/f'preview{n}-x4.png')
        write(directory/f'pixel{n}.json',{'inputs':inputs([__file__,RECIPE,WOOD/'wood-levels.npy',
              output/f'base/pixels/pixel{n}.json']),'output_sha256':sha(path),
              'image_resize':False,'wood_material_recomputed':False})
    canvas=Image.new('RGB',(sum(p.shape[1] for p in previews)+48,max(p.shape[0] for p in previews)+60),(20,24,33))
    draw=ImageDraw.Draw(canvas); x=16
    for n,preview in zip(CONFIG['variants'],previews):
        im=Image.fromarray(preview); canvas.paste(im,(x,36),im)
        draw.text((x,12),f'{n} bays | exact handle boundaries | exact 4x',fill=(240,240,240)); x+=im.width+16
    canvas.save(directory/'comparison-x4.png')
    write(output/'execution.json',{'pixel_seconds':time.perf_counter()-started})


def validate(output):
    from validate09 import validate as check
    check(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['geometry','pixels','validate'])
    parser.add_argument('--output',type=Path,default=OUT); args=parser.parse_args()
    globals()[args.stage](args.output.resolve())
