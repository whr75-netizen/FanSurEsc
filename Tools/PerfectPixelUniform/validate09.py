"""Independent Fraction ray checks and saved output checks for handle boundary repair."""
from fractions import Fraction as F
from pathlib import Path
import json
import time
import numpy as np
from PIL import Image
from cabinet_pipeline06 import ROOT,read,write,sha,inputs
from handle_raster09 import RECIPE,CONFIG,OLD,WOOD


def reference_hit(boxes,u,v):
    hits=[]
    for box in boxes:
        lo=[F(str(x)) for x in box['local_minimum_ticks']]
        hi=[F(str(x)) for x in box['local_maximum_ticks']]
        intervals=[(lo[0]-u/2,hi[0]-u/2,2),
                   ((-v-u/2-hi[1])/2,(-v-u/2-lo[1])/2,5),(lo[2],hi[2],1)]
        near=max(a for a,b,f in intervals); far=min(b for a,b,f in intervals)
        if near>far: continue
        face=min((f for a,b,f in intervals if a==near),key=[1,2,5].index)
        bounds=tuple(box['local_minimum_ticks']+box['local_maximum_ticks'])
        hits.append((near,[1,2,5].index(face),bounds,box['part'],face))
    winner=min(hits) if hits else None
    return None if winner is None else (winner[0],winner[3],winner[4])


def validate(output):
    started=time.perf_counter(); checks=[]; observations={}; reference={}
    def check(name,value,observed=None): checks.append({'name':name,'passed':bool(value),'observed':observed})
    for name,digest in read(OLD/'validation.json')['files_sha256'].items():
        check('preserved source:'+name,sha(Path(name))==digest)
    check('actual scene unchanged',sha(output/'base/geometry/scene.blend')==sha(OLD/'geometry/scene.blend'))
    check('actual box definitions unchanged',sha(output/'base/geometry/parts.json')==sha(OLD/'geometry/parts.json'))
    parts=read(OLD/'geometry/parts.json'); palette=read(OLD/'material/palette.json')['colors_srgb8byrole']
    allowed=np.array([rgb for colors in palette.values() for rgb in colors],np.uint8)
    for spec in parts['variants']:
        n=spec['count']; prefix=f'n{n}:'
        old=dict(np.load(OLD/f'geometry/buffers{n}.npz'))
        new=dict(np.load(output/f'base/geometry/buffers{n}.npz'))
        shade=dict(np.load(output/f'base/pixels/shading{n}.npz'))
        meta=read(output/f'base/geometry/raster{n}.json')
        image=np.array(Image.open(output/f'pixels/native{n}.png').convert('RGBA'))
        previous=np.array(Image.open(WOOD/f'pixels/native{n}.png').convert('RGBA'))
        repair=new['repair']; affected=repair.copy()
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                y0,y1=max(0,dy),repair.shape[0]+min(0,dy)
                x0,x1=max(0,dx),repair.shape[1]+min(0,dx)
                affected[y0:y1,x0:x1]|=repair[y0-dy:y1-dy,x0-dx:x1-dx]
        check(prefix+'same canvas and alpha',image.shape==previous.shape and np.array_equal(image[...,3],previous[...,3]))
        check(prefix+'nonhandle buffers preserved',all(np.array_equal(new[k][~repair],old[k][~repair]) for k in old))
        check(prefix+'RGBA outside dependent edge cells unchanged',np.array_equal(image[~affected],previous[~affected]))
        wood_ids=[g['id'] for g in spec['groups'] if g['role']=='wood']
        wood=np.isin(old['part'],wood_ids)
        check(prefix+'all wood RGBA unchanged',np.array_equal(image[wood],previous[wood]))
        colors=np.unique(image[new['mask'],:3],axis=0)
        check(prefix+'source palette only',all(np.any(np.all(allowed==c,axis=1)) for c in colors))
        preview=np.array(Image.open(output/f'pixels/preview{n}-x4.png').convert('RGBA'))
        check(prefix+'exact 4x',np.array_equal(preview,np.repeat(np.repeat(image,4,0),4,1)))
        ox,oy=[int(x) for x in meta['screen_origin']]
        ray_ok=True; max_depth_error=0.
        for y,x in np.argwhere(repair):
            hit=reference_hit(spec['boxes'],F(2*(ox+int(x))+1,2),F(2*(oy+int(y))+1,2))
            if hit is None or hit[1]!=new['part'][y,x] or hit[2]!=new['face'][y,x]: ray_ok=False; continue
            t=float(hit[0]); u=ox+x+.5; v=oy+y+.5
            position=np.array([-t/32,(u/2+t)/32,(-v-u/2-2*t)/(32*np.sqrt(6))])
            from common import basis
            view=basis(meta['camera'])[2]
            error=abs(meta['camera_distance']-float(position@view)-float(new['depth'][y,x]))
            max_depth_error=max(max_depth_error,error)
        check(prefix+'independent Fraction nearest owner and face',ray_ok)
        check(prefix+'independent depth <=1e-5 m',max_depth_error<=1e-5,max_depth_error)
        observations[str(n)]={}
        for group in spec['groups']:
            if not group['name'].endswith('Handle'): continue
            mask=new['part']==group['id']; old_mask=old['part']==group['id']
            kind='DrawerHandle' if 'Drawer' in group['name'] else 'DoorHandle'
            count=int(mask.sum()); bay=group['bay']
            check(prefix+group['name']+':complete expected coverage',count==CONFIG['expected_visible_pixels'][kind],count)
            check(prefix+group['name']+':no existing pixels deleted',not (old_mask&~mask).any())
            records=[]
            for y,x in np.argwhere(mask):
                records.append((int(x)+ox-40*bay,int(y)+oy+20*bay,int(new['face'][y,x]),
                                tuple(new['normals'][y,x].tolist()),bool(shade['ink'][y,x]),tuple(image[y,x].tolist())))
            records.sort()
            if kind not in reference: reference[kind]=records
            check(prefix+group['name']+':translated mask face normal ink RGBA equal',records==reference[kind])
            observations[str(n)][group['name']]={'before':int(old_mask.sum()),'after':count,'added':int((mask&~old_mask).sum())}
    passed=all(c['passed'] for c in checks)
    write(output/'validation.json',{'passed':passed,'checks':checks,'handles':observations,
          'inputs':inputs([RECIPE,Path(__file__),OLD/'geometry/parts.json',WOOD/'wood-levels.npy']),
          'elapsed_seconds':time.perf_counter()-started,'aesthetic_approval':False,'unity_checked':False})
    print(json.dumps({'passed':passed,'checks':len(checks),'handles':observations,
                      'failures':[c for c in checks if not c['passed']]}))
    if not passed: raise SystemExit(1)
