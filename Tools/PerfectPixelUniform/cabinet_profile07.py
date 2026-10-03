"""Flat cabinet profile; reuse the V6 finite renderer and material algorithms."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
RECIPE = ROOT/'Tools/PerfectPixelUniform/recipe07.json'
OLD = ROOT/'docs/artifacts/building37/Parametric06'
OUT = ROOT/'docs/artifacts/building37/Parametric07-fixed'


def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashes(paths): return {str(Path(p).resolve()):sha(p) for p in paths}
def write(p,data):
    with Path(p).open('w',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def build_geometry(output):
    import bpy
    import cabinet_geometry06 as core
    recipe=read(RECIPE); profile=recipe['profile']
    directory=output/'geometry'; directory.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter(); originals=list(bpy.data.scenes); specs=[]
    palette=read(OLD/'material/palette.json')
    for count in recipe['variants']:
        scene=bpy.data.scenes.new(f'FlatCabinet_{count}_modules')
        groups=[]; boxes=[]; objects=[]; width=2*recipe['cap']+count*recipe['module_pitch']

        def group(name,role,bay=None):
            g={'id':len(groups),'name':name,'role':role,'bay':bay,'boxes':[],
               'face_ids':{'-X':0,'+X':1,'-Y':2,'+Y':3,'-Z':4,'+Z':5}}
            groups.append(g); return g

        def solid(g,suffix,lo,hi):
            lo=[float(v) for v in lo]; hi=[float(v) for v in hi]
            if any(a>=b for a,b in zip(lo,hi)): raise ValueError('Invalid flat-profile box')
            minimum,maximum=core.box_bounds(lo,hi)
            a,b,c=minimum.tolist(); x,y,z=maximum.tolist()
            vertices=[(a,b,c),(x,b,c),(x,y,c),(a,y,c),(a,b,z),(x,b,z),(x,y,z),(a,y,z)]
            faces=[(0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2),(0,3,2,1),(4,5,6,7)]
            name=f'N{count}_{g["name"]}_{suffix}'
            mesh=bpy.data.meshes.new(name); mesh.from_pydata(vertices,[],faces); mesh.update()
            obj=bpy.data.objects.new(name,mesh); scene.collection.objects.link(obj)
            obj['semantic_part_id']=g['id']; obj['material_role']=g['role']
            obj['local_bounds_ticks']=json.dumps([lo,hi]); objects.append(obj); g['boxes'].append(name)
            normals=np.array([list(p.normal) for p in mesh.polygons])
            if not np.allclose(normals,[[-1,0,0],[1,0,0],[0,-1,0],[0,1,0],[0,0,-1],[0,0,1]],atol=1e-6):
                raise AssertionError('Non-outward box')
            actual=np.array([list(v.co) for v in mesh.vertices])
            if not np.allclose(actual.min(0),minimum,atol=1e-7) or not np.allclose(actual.max(0),maximum,atol=1e-7):
                raise AssertionError('Mesh bounds mismatch')
            boxes.append({'name':name,'part':g['id'],'role':g['role'],'bay':g['bay'],
                          'local_minimum_ticks':lo,'local_maximum_ticks':hi,
                          'minimum':minimum.tolist(),'maximum':maximum.tolist(),'mesh_readback_bounds_match':True})

        solid(group('Body','paint'),'solid',(0,6,0),(width,profile['body_top'],20))
        solid(group('Counter','wood'),'solid',(-1,profile['counter_bottom'],-1),(width+1,72,21))
        solid(group('Plinth','paint'),'solid',(2,0,3),(width-2,6,20))
        front=profile['panel_front']; near=profile['handle_front']; back=profile['handle_back']
        for i in range(count):
            start=recipe['cap']+i*recipe['module_pitch']; margin=profile['plate_side_margin']
            x0,x1=start+margin,start+recipe['module_pitch']-margin
            for kind,key in [('Door','door_y'),('Drawer','drawer_y')]:
                y0,y1=profile[key]
                solid(group(f'Bay{i}{kind}Panel','paint',i),'slab',(x0,y0,front),(x1,y1,0))
            drawer=group(f'Bay{i}DrawerHandle','brass',i); centre=(x0+x1)/2
            solid(drawer,'bar',(centre-2.5,61,near),(centre+2.5,62,back))
            for offset in (-2,2):
                solid(drawer,f'anchor_{offset}',(centre+offset-.125,61.25,back),(centre+offset+.125,61.75,front))
            door=group(f'Bay{i}DoorHandle','brass',i)
            solid(door,'bar',(start+17.5,36,near),(start+18,41,back))
            for yy in (36.5,39.875):
                solid(door,f'anchor_{yy}',(start+17.5625,yy,back),(start+17.9375,yy+.625,front))
        bpy.context.view_layer.update()
        spec={'count':count,'width_ticks':width,'height_ticks':72,'depth_ticks':20,'groups':groups,'boxes':boxes}
        core.palette_preview(objects,palette)
        core.raster_variant(scene,spec,objects,recipe,directory)
        specs.append(spec)
    if bpy.context.window: bpy.context.window.scene=scene
    for scene_old in originals: bpy.data.scenes.remove(scene_old)
    bpy.ops.wm.save_as_mainfile(filepath=str((directory/'scene.blend').resolve()))
    write(directory/'parts.json',{'schema':'flat-native-cabinet/7','variants':specs,
          'inputs':hashes([RECIPE,__file__,Path(core.__file__),ROOT/'Tools/PixelPipeline/common.py',OLD/'material/palette.json']),
          'elapsed_seconds':time.perf_counter()-started,'source_image_read':False,
          'worker_completed':True,
          'profile':'coplanar slabs; no frame or inset; side is flat body',
          'material_contract':'recipe06.json','geometry_contract':'recipe07.json'})


def geometry(output):
    directory=output/'geometry'
    if directory.exists(): raise FileExistsError('Existing V7 geometry is immutable')
    started=time.perf_counter()
    argv=['C:/Program Files/Blender Foundation/Blender 5.2/blender.exe','--background','--factory-startup',
          '--python',str(Path(__file__).resolve()),'--','geometry','--blender-worker','--output',str(output)]
    result=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=55)
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'stdout.txt').write_bytes(result.stdout); (directory/'stderr.txt').write_bytes(result.stderr)
    parts_path=directory/'parts.json'
    completed=parts_path.is_file() and read(parts_path).get('worker_completed') is True
    write(directory/'execution.json',{'argv':argv,'exit_code':result.returncode,
          'worker_completed':completed,'elapsed_seconds':time.perf_counter()-started})
    if result.returncode or not completed:
        raise RuntimeError(result.stdout.decode(errors='replace')+result.stderr.decode(errors='replace'))


def pixels(output):
    import cabinet_pipeline06 as core
    destination=output/'material'
    if destination.exists(): raise FileExistsError('Existing reused material is immutable')
    shutil.copytree(OLD/'material',destination)
    # V7 changes only geometry. The unchanged shading recipe is its own input.
    core.pixels(read(core.RECIPE),output)
    write(output/'reuse.json',{'material_contract':str(core.RECIPE),
          'inputs':hashes([__file__,Path(core.__file__),RECIPE,OLD/'material/palette.json',OLD/'material/grain.npy']),
          'material_byte_identical':all(sha(p)==sha(destination/p.name) for p in (OLD/'material').iterdir() if p.is_file())})


def validate(output):
    from PIL import Image
    from validate06 import Audit
    from cabinet_pipeline06 import RECIPE as shade_recipe
    sys.path.insert(0,str(ROOT/'Tools/PixelPipeline'))
    from common import basis,consistent_edges,parallel_double_strokes
    destination=output/'validation.json'
    if destination.exists(): raise FileExistsError('Validation evidence already exists')
    audit=Audit(output,RECIPE); recipe=read(RECIPE); parts=audit.json(output/'geometry/parts.json')
    audit.declared_hashes(parts,output/'geometry/parts.json')
    audit.declared_hashes(audit.json(output/'reuse.json'),output/'reuse.json')
    old_audit=read(OLD/'validation.json')
    for path,digest in old_audit['files_sha256'].items():
        audit.check('unchanged V6:'+path,Path(path).is_file() and sha(path)==digest)
    audit.check('unchanged V6 model',sha(OLD/'geometry/scene.blend')==old_audit['files_sha256'][str((OLD/'geometry/scene.blend').resolve())])
    palette=read(OLD/'material/palette.json')['colors_srgb8byrole']
    audit.module_geometry(recipe,parts['variants'])
    for spec in parts['variants']:
        count=spec['count']; prefix=f'n{count}:'
        b=audit.npz(output/f'geometry/buffers{count}.npz'); s=audit.npz(output/f'pixels/shading{count}.npz')
        meta=audit.json(output/f'geometry/raster{count}.json')
        pixel=audit.json(output/f'pixels/pixel{count}.json'); audit.declared_hashes(pixel,output/f'pixels/pixel{count}.json')
        rgba=audit.image(output/f'pixels/native{count}.png'); preview=audit.image(output/f'pixels/preview{count}-x4.png')
        mask=b['mask']; groups=spec['groups']
        audit.check(prefix+'no frame/inset groups',not any('Frame' in g['name'] or 'Inset' in g['name'] for g in groups))
        slabs=[box for box in spec['boxes'] if 'Panel' in box['name']]
        audit.check(prefix+'all coplanar front plates',len(slabs)==2*count and all(box['local_minimum_ticks'][2]==-.4 and box['local_maximum_ticks'][2]==0 for box in slabs))
        for box in slabs:
            audit.check(prefix+'plate width:'+box['name'],abs(box['local_maximum_ticks'][0]-box['local_minimum_ticks'][0]-19.5)<1e-10)
        body=next(box for box in spec['boxes'] if 'Body' in box['name'])
        top=next(box for box in spec['boxes'] if 'Counter' in box['name'])
        audit.check(prefix+'counter joint and thickness',body['local_maximum_ticks'][1]==top['local_minimum_ticks'][1]==70 and top['local_maximum_ticks'][1]==72)
        handles=[box for box in spec['boxes'] if 'Handle' in box['name']]
        audit.check(prefix+'handle protrusion',min(box['local_minimum_ticks'][2] for box in handles)==-1.25 and all(box['local_maximum_ticks'][2]<=-.4 for box in handles))
        audit.check(prefix+'native alpha',np.array_equal(rgba[...,3]==255,mask) and set(np.unique(rgba[...,3]).tolist())<={0,255})
        audit.check(prefix+'exact 4x',np.array_equal(preview,np.repeat(np.repeat(rgba,4,0),4,1)))
        audit.check(prefix+'same camera density phase',meta['camera']==dict(recipe['camera'],margin_pixels=8) and np.allclose(meta['screen_origin'],np.rint(meta['screen_origin'])))
        edge,_,_=consistent_edges(b,meta['camera'])
        audit.check(prefix+'actual edge owners',np.array_equal(s['ink'],edge) and not (edge&~mask).any())
        audit.check(prefix+'no parallel double strokes',not parallel_double_strokes(b,s['ink']))
        r,u,d=basis(meta['camera']); origin=np.array(meta['screen_origin']); density=meta['pixels_per_meter']
        for group in groups:
            region=b['part']==group['id']; samples=np.argwhere(region)
            audit.check(prefix+'visible:'+group['name'],len(samples)>0,int(len(samples)))
            audit.check(prefix+'source RGB:'+group['name'],np.array_equal(rgba[region,:3],np.array(palette[group['role']],np.uint8)[s['palette_index'][region]]))
            if not len(samples): continue
            y,x=samples[len(samples)//2]; q=(origin+np.array([x+.5,y+.5]))/density
            ray=r*q[0]-u*q[1]+d*meta['camera_distance']
            hit=audit.nearest_box(ray,-d,spec['boxes'])
            audit.check(prefix+'nearest depth:'+group['name'],hit is not None and hit[1]==group['id'] and abs(hit[0]-b['depth'][y,x])<1e-5)
        audit.observations[prefix]={'size':meta['size'],'shadow_pixels':int((mask&~b['visibility']).sum()),'surface_groups':len(groups)}
    report=audit.report(); report['scope']='V7 geometry correction, unchanged V6 materials/algorithms, saved pixel/visibility/display'
    write(destination,report)
    print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'failures':[c for c in report['checks'] if not c['passed']]}))
    if not report['passed']: raise SystemExit(1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['geometry','pixels','validate'])
    parser.add_argument('--output',type=Path,default=OUT)
    parser.add_argument('--blender-worker',action='store_true')
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    args=parser.parse_args(argv); output=args.output.resolve()
    if args.blender_worker:
        if args.stage!='geometry': raise ValueError('Blender only creates geometry')
        build_geometry(output)
    else: globals()[args.stage](output)


if __name__=='__main__': main()
