"""Four source wood tones on unchanged V7 finite surfaces; no geometry run."""
from pathlib import Path
import argparse
import json
import time
import numpy as np
from PIL import Image,ImageDraw
from cabinet_pipeline06 import ROOT,read,write,sha,inputs,connected8

RECIPE=ROOT/'Tools/PerfectPixelUniform/recipe08.json'
CONFIG=read(RECIPE); PREVIOUS=ROOT/CONFIG['previous']
SOURCE_RECIPE=ROOT/CONFIG['source_recipe']; SOURCE=read(SOURCE_RECIPE)
OUT=ROOT/CONFIG['output']


def small_components(mask):
    ids,areas=connected8(mask)
    small=np.flatnonzero((areas<CONFIG['minimum_component_texels'])&(np.arange(len(areas))>0))
    return np.isin(ids,small),len(small)


def material(output):
    started=time.perf_counter(); output.mkdir(parents=True,exist_ok=False)
    source=ROOT/SOURCE['source']
    if sha(source)!=SOURCE['source_sha256']: raise ValueError('Source changed')
    rgb=np.asarray(Image.open(source).convert('RGB'))
    x0,y0,x1,y1=SOURCE['wood_roi']; crop=rgb[y0:y1,x0:x1]
    value=crop @ np.array([.2126,.7152,.0722])
    thresholds=np.percentile(value,CONFIG['quantiles'])
    old_info=read(PREVIOUS/'material/material.json'); h,w=old_info['grain_shape']
    xx=np.floor((np.arange(w)+.5)*(x1-x0)/w).astype(int)
    yy=np.floor((np.arange(h)+.5)*(y1-y0)/h).astype(int)
    texels=value[np.ix_(yy,xx)]
    masks=[]; removal=[]
    for threshold in thresholds[::-1]:
        candidate=texels<threshold; erased,components=small_components(candidate)
        masks.append(candidate&~erased)
        removal.append({'threshold':float(threshold),'components':components,'texels':int(erased.sum())})
    if (masks[2]&~masks[1]).any() or (masks[1]&~masks[0]).any(): raise AssertionError('Tone nesting broken')
    levels=np.sum(np.stack(masks),axis=0).astype('uint8')
    erased,components=small_components(levels==0); levels[erased]=1
    np.save(output/'wood-levels.npy',levels)
    wood=np.array(read(PREVIOUS/'material/palette.json')['colors_srgb8byrole']['wood'],np.uint8)
    Image.fromarray(wood[levels]).save(output/'wood-tile.png')
    Image.fromarray(np.repeat(np.repeat(wood[levels],4,0),4,1)).save(output/'wood-tile-x4.png')
    write(output/'material.json',{'inputs':inputs([source,SOURCE_RECIPE,RECIPE,__file__,PREVIOUS/'material/material.json',PREVIOUS/'material/palette.json']),
          'output_sha256':sha(output/'wood-levels.npy'),'quantiles':CONFIG['quantiles'],
          'thresholds':thresholds.tolist(),'dark_component_removals':removal,
          'bright_removed_components':components,'bright_removed_texels':int(erased.sum()),
          'level_counts':{str(i):int((levels==i).sum()) for i in range(4)},
          'nested':True,'lossy_material_authoring':True,'elapsed_seconds':time.perf_counter()-started})


def pixels(output):
    started=time.perf_counter(); directory=output/'pixels'; directory.mkdir(exist_ok=False)
    levels=np.load(output/'wood-levels.npy'); palette=read(PREVIOUS/'material/palette.json')
    wood=np.array(palette['colors_srgb8byrole']['wood'],np.uint8); previews=[]
    for count in (2,3):
        b=dict(np.load(PREVIOUS/f'geometry/buffers{count}.npz'))
        s=dict(np.load(PREVIOUS/f'pixels/shading{count}.npz'))
        meta=read(PREVIOUS/f'geometry/raster{count}.json')
        native_path=PREVIOUS/f'pixels/native{count}.png'; rgba=np.array(Image.open(native_path).convert('RGBA'))
        wood_mask=np.zeros_like(b['mask'])
        for group in meta['parts']:
            if group['role']=='wood': wood_mask |= b['part']==group['id']
        level=levels[s['uvy'],s['uvx']]
        index=np.minimum(s['band']+level,3)
        region=wood_mask&~s['ink']; rgba[region,:3]=wood[index[region]]
        path=directory/f'native{count}.png'; Image.fromarray(rgba).save(path)
        preview=np.repeat(np.repeat(rgba,4,0),4,1)
        Image.fromarray(preview).save(directory/f'preview{count}-x4.png'); previews.append(preview)
        np.savez_compressed(directory/f'material{count}.npz',wood=wood_mask,levels=level,index=index)
        write(directory/f'pixel{count}.json',{'inputs':inputs([native_path,PREVIOUS/f'geometry/buffers{count}.npz',PREVIOUS/f'pixels/shading{count}.npz',output/'wood-levels.npy',__file__,RECIPE]),
              'output_sha256':sha(path),'wood_only':True,'geometry_recomputed':False})
    canvas=Image.new('RGB',(sum(p.shape[1] for p in previews)+48,max(p.shape[0] for p in previews)+60),(20,24,33))
    draw=ImageDraw.Draw(canvas); x=16
    for count,preview in zip((2,3),previews):
        im=Image.fromarray(preview); canvas.paste(im,(x,36),im)
        draw.text((x,12),f'{count} bays | 4 wood tones | exact 4x',fill=(240,240,240)); x+=im.width+16
    canvas.save(directory/'comparison-x4.png')
    write(output/'execution.json',{'pixel_seconds':time.perf_counter()-started})


def validate(output):
    started=time.perf_counter(); checks=[]
    def check(name,result,observed=None): checks.append({'name':name,'passed':bool(result),'observed':observed})
    for raw,digest in read(PREVIOUS/'validation.json')['files_sha256'].items():
        check('unchanged V7:'+raw,Path(raw).is_file() and sha(raw)==digest)
    palette=read(PREVIOUS/'material/palette.json'); wood=np.array(palette['colors_srgb8byrole']['wood'],np.uint8)
    source=np.asarray(Image.open(ROOT/SOURCE['source']).convert('RGB'))
    for sample in palette['samples']:
        x,y=sample['source_xy']; check('source RGB:'+sample['role']+str(sample['band']),source[y,x].tolist()==sample['rgb'])
    counts={}
    for count in (2,3):
        old=np.asarray(Image.open(PREVIOUS/f'pixels/native{count}.png').convert('RGBA'))
        new=np.asarray(Image.open(output/f'pixels/native{count}.png').convert('RGBA'))
        b=dict(np.load(PREVIOUS/f'geometry/buffers{count}.npz')); s=dict(np.load(PREVIOUS/f'pixels/shading{count}.npz'))
        m=dict(np.load(output/f'pixels/material{count}.npz')); region=m['wood']&~s['ink']
        check(f'n{count}:same canvas and alpha',old.shape==new.shape and np.array_equal(old[...,3],new[...,3]))
        check(f'n{count}:nonwood and ink unchanged',np.array_equal(old[~region],new[~region]))
        check(f'n{count}:actual palette fill',np.array_equal(new[region,:3],wood[m['index'][region]]))
        top=region&(b['normals'][...,2]>.9)
        counts[str(count)]=[int(np.all(new[top,:3]==rgb,axis=1).sum()) for rgb in wood]
        check(f'n{count}:four interior top colours',min(counts[str(count)])>=6,counts[str(count)])
        preview=np.asarray(Image.open(output/f'pixels/preview{count}-x4.png').convert('RGBA'))
        check(f'n{count}:exact 4x',np.array_equal(preview,np.repeat(np.repeat(new,4,0),4,1)))
    passed=all(c['passed'] for c in checks)
    write(output/'validation.json',{'passed':passed,'checks':checks,'wood_top_colour_counts':counts,
          'inputs':inputs([__file__,RECIPE,SOURCE_RECIPE,output/'wood-levels.npy']),
          'elapsed_seconds':time.perf_counter()-started,'aesthetic_approval':False})
    print(json.dumps({'passed':passed,'wood_top_colour_counts':counts}))
    if not passed: raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('stage',choices=['material','pixels','validate'])
    parser.add_argument('--output',type=Path,default=OUT); args=parser.parse_args()
    globals()[args.stage](args.output.resolve())
