"""N14: editable planar parts -> native pixel raster, not image-grid recovery."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from native14_materials import Appearance


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                   allow_nan=False)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def project(point):
    x, y, z = point
    if any(type(v) is not int for v in point):
        raise ValueError('Canonical vertices must use integer ticks')
    return [2*x-2*z, -x-z-y]


def line(a, b):
    """Finite inclusive Bresenham; no dilation, antialias or endpoint joining."""
    x, y = a; xx, yy = b
    dx, dy = abs(xx-x), -abs(yy-y)
    sx, sy = (1 if x < xx else -1), (1 if y < yy else -1)
    error = dx+dy; pixels = []
    while True:
        pixels.append((x, y))
        if (x, y) == (xx, yy):
            return pixels
        doubled = 2*error
        if doubled >= dy:
            error += dy; x += sx
        if doubled <= dx:
            error += dx; y += sy


def add_edge(edges, seen, name, a, b):
    key=tuple(sorted((tuple(a),tuple(b))))
    if key in seen:raise ValueError('Duplicate canonical edge: '+name)
    group='cap' if name.startswith('cap.') else '.'.join(name.split('.')[:2]) if name.startswith('handle.') else 'body'
    seen.add(key);edges.append({'id':name,'a':a,'b':b,'occlusion_class':group})


def edge_visible(edge, surface):
    """A visible surface's ownership is determined before any ink is generated."""
    return surface is not None and edge['occlusion_class']==surface['occlusion_class']


def build(recipe, count):
    p = recipe['profile']; width = 2*p['end_cap']+count*p['module_pitch']
    height = p['height']; depth = p['depth']; cap = p['cap_thickness']
    body_top = height-cap
    faces = []; edges = []; decor = []; seen = set()

    def face(name, material, quad, tone=None, uv_period=None):
        group='cap' if name.startswith('cap.') else name if name.startswith('handle.') else 'body'
        faces.append({'id':len(faces), 'name':name, 'material':material,
                      'vertices':quad, 'tone':tone, 'uv_period':uv_period,'occlusion_class':group})

    def edge(name, a, b):
        add_edge(edges,seen,name,a,b)

    def strip(name, a, b, material='brass', tone=1):
        decor.append({'name':name, 'a':a, 'b':b, 'material':material, 'tone':tone})

    def front_quad(x0, x1, y0, y1):
        return [[x0,y1,0],[x1,y1,0],[x1,y0,0],[x0,y0,0]]

    def side_quad(z0, z1, y0, y1):
        return [[0,y1,z0],[0,y1,z1],[0,y0,z1],[0,y0,z0]]

    # Large physical surface partitions are planar; no inflated frame or recess.
    face('body.side', 'side', side_quad(0,depth,0,body_top), 1)
    face('body.front', 'navy', front_quad(0,width,0,body_top), 1)
    for n in range(count):
        start = p['end_cap']+n*p['module_pitch']
        face(f'door.{n}', f'front{n%3}',
             front_quad(start+1,start+p['module_pitch']-1,8,body_top-5))
        # Painted rails visible in the reference: coplanar material domains,
        # never an extruded picture frame. Shared canonical dimensions own them.
        frame=p['door_frame_ticks']
        face(f'door_rail.{n}.near','navy',front_quad(start+1,start+1+frame,10,body_top-5),2)
        face(f'door_rail.{n}.far','navy',front_quad(start+p['module_pitch']-1-frame,start+p['module_pitch']-1,10,body_top-5),0)
        face(f'door_rail.{n}.top','navy',front_quad(start+1,start+p['module_pitch']-1,body_top-5,body_top-3),2)
        face(f'door_rail.{n}.bottom','navy',front_quad(start+1,start+p['module_pitch']-1,8,10),2)
    face('side.panel', 'side', side_quad(3,depth-3,10,body_top-8))
    face('side.rail.near','side',side_quad(1,3,10,body_top-5),2)
    face('side.rail.far','side',side_quad(depth-3,depth-1,10,body_top-5),0)
    face('side.rail.bottom','side',side_quad(1,depth-1,8,10),2)
    face('side.rail.top','side',side_quad(1,depth-1,body_top-5,body_top-3),1)
    # Shadow domains are physical cap contact/base bands, separate from ink.
    face('front.cap_shadow', 'navy', front_quad(0,width,body_top-3,body_top), 0)
    face('side.cap_shadow', 'side', side_quad(0,depth,body_top-3,body_top), 0)
    face('front.plinth', 'navy', front_quad(0,width,0,p['plinth']), 0)
    face('side.plinth', 'side', side_quad(0,depth,0,p['plinth']), 0)
    # Corner brass is a flat surface material partition, never a protruding box.
    face('front.corner', 'brass', front_quad(0,1,0,body_top), 1)
    face('side.corner', 'brass', side_quad(0,1,0,body_top), 0)
    for yy in [0,body_top-4]:
        face(f'front.corner_plate.{yy}', 'brass', front_quad(0,2,yy,yy+4), 1)
        face(f'side.corner_plate.{yy}', 'brass', side_quad(0,2,yy,yy+4), 0)
        strip(f'corner.glint.{yy}', [0,yy+3,0],[2,yy+3,0],tone=2)

    # One shared seam between flush doors; decorative inset is metal-colored.
    for n in range(1,count):
        x = p['end_cap']+n*p['module_pitch']
        edge(f'seam.{n}', [x,6,0],[x,body_top-3,0])
    for n in range(count):
        start = p['end_cap']+n*p['module_pitch']; a=start+3; b=start+17
        points = [[a,12,0],[b,12,0],[b,body_top-10,0],[a,body_top-10,0]]
        for i in range(4):
            strip(f'inlay.{n}.{i}', points[i],points[(i+1)%4],tone=1)
        for yy in [19,body_top-11]:
            face(f'hinge.{n}.{yy}', 'brass',front_quad(start, start+1,yy,yy+4),1)
            strip(f'hinge.glint.{n}.{yy}',[start,yy+3,0],[start+1,yy+3,0],tone=2)
        hx = start+p['handle_x']; y0=p['handle_y']; y1=y0+p['handle_height']
        q = front_quad(hx,hx+p['handle_width'],y0,y1)
        face(f'handle.{n}', 'brass',q,1)
        # Explicit single-pixel outline owns this hardware, not a dark fill.
        for i in range(4):
            edge(f'handle.{n}.{i}',q[i],q[(i+1)%4])
        strip(f'handle.glint.{n}',[hx+1,y1-1,0],[hx+p['handle_width']-1,y1-1,0],tone=2)
    # Decorative side panel: closed finite metal path, no inferred edges.
    q=side_quad(3,depth-3,12,body_top-10)
    for i in range(4):
        strip(f'side.inlay.{i}',q[i],q[(i+1)%4],tone=1)
    strip('front.lower_inlay',[2,8,0],[width,8,0])
    strip('side.lower_inlay',[0,8,2],[0,8,depth])
    strip('front.upper_inlay',[2,body_top-4,0],[width,body_top-4,0],tone=1)
    strip('side.upper_inlay',[0,body_top-4,2],[0,body_top-4,depth],tone=1)
    strip('front.rail_glint',[2,6,0],[width,6,0],material='navy',tone=2)
    strip('side.rail_glint',[0,6,2],[0,6,depth],material='side',tone=2)
    # The cap physically occludes the body upper rim. No second body-top line.
    face('cap.side', 'wood', [[-1,height,-1],[-1,height,depth+1],
                             [-1,body_top,depth+1],[-1,body_top,-1]],0)
    face('cap.front', 'wood', [[-1,height,-1],[width+1,height,-1],
                              [width+1,body_top,-1],[-1,body_top,-1]],0)
    face('cap.top', 'wood', [[-1,height,-1],[width+1,height,-1],
                            [width+1,height,depth+1],[-1,height,depth+1]],
         uv_period=p['reference_width']+2)
    cap_q=faces[-1]['vertices']
    for i in range(4):
        edge(f'cap.top.{i}',cap_q[i],cap_q[(i+1)%4])
    edge('cap.front.underside',[-1,body_top,-1],[width+1,body_top,-1])
    edge('cap.side.underside',[-1,body_top,-1],[-1,body_top,depth+1])
    edge('cap.near.vertical',[-1,body_top,-1],[-1,height,-1])
    edge('cap.left.vertical',[-1,body_top,depth+1],[-1,height,depth+1])
    edge('cap.right.vertical',[width+1,body_top,-1],[width+1,height,-1])
    edge('body.near.vertical',[0,0,0],[0,body_top,0])
    edge('body.left.vertical',[0,0,depth],[0,body_top,depth])
    edge('body.right.vertical',[width,0,0],[width,body_top,0])
    edge('body.front.ground',[0,0,0],[width,0,0])
    edge('body.side.ground',[0,0,0],[0,0,depth])
    return {'count':count,'width_ticks':width,'height_ticks':height,
            'depth_ticks':depth,'faces':faces,'edges':edges,'decor':decor}


def geometry(recipe, output):
    directory=output/'geometry';directory.mkdir(parents=True,exist_ok=False)
    summary=[]
    for count in recipe['variants']:
        scene=build(recipe,count)
        points=np.array([project(v) for f in scene['faces'] for v in f['vertices']])
        minimum=points.min(0)-3;maximum=points.max(0)+3
        offset=-minimum;w,h=(maximum-minimum+1).tolist()
        scene.update({'origin':offset.tolist(),'size':[w,h]})
        ids=np.full((h,w),-1,np.int16);uu=np.zeros((h,w));vv=np.zeros((h,w))
        yy,xx=np.indices((h,w))
        for f in scene['faces']:
            q=np.array([project(v) for v in f['vertices']])+offset
            mask=Image.new('1',(w,h));ImageDraw.Draw(mask).polygon([tuple(v) for v in q],fill=1)
            m=np.asarray(mask,dtype=bool).copy()
            # Polygon scan conversion and Bresenham have different half-step ties.
            # A face's own finite perimeter owns its boundary pixels before ID/UV
            # assignment, so adjacent faces and ink share a single raster rule.
            for k in range(4):
                for x,y in line(q[k].tolist(),q[(k+1)%4].tolist()):m[y,x]=True
            # Pixel centers and edge endpoints both have integral native coordinates.
            transform=np.column_stack((q[1]-q[0],q[3]-q[0]))
            uv=np.linalg.solve(transform,np.array([xx[m]-q[0,0],yy[m]-q[0,1]]))
            if f['uv_period']:
                uv[0]*=(scene['width_ticks']+2)/f['uv_period']
                uv[0]%=1.0
            ids[m]=f['id'];uu[m]=uv[0];vv[m]=uv[1]
        ink=np.zeros((h,w),bool);stroke_ids=np.full((h,w),-1,np.int16)
        for i,e in enumerate(scene['edges']):
            a=(np.array(project(e['a']))+offset).tolist()
            b=(np.array(project(e['b']))+offset).tolist()
            e['candidate_pixels']=[list(t) for t in line(a,b)]
            e['pixels']=[];e['occluded_pixels']=[]
            for x,y in e['candidate_pixels']:
                f=scene['faces'][int(ids[y,x])] if ids[y,x]>=0 else None
                (e['pixels'] if edge_visible(e,f) else e['occluded_pixels']).append([x,y])
            for x,y in e['pixels']:
                ink[y,x]=True;stroke_ids[y,x]=i
        if np.any(ink&(ids<0)):
            raise AssertionError('A structural edge has no visible surface owner')
        np.savez_compressed(directory/f'buffers{count}.npz',part=ids,u=uu,v=vv,ink=ink,stroke=stroke_ids)
        write(directory/f'parts{count}.json',scene)
        # Inspectable vector part map; the recipe and source UV remain production owners.
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
        colors={'navy':'#233e53','side':'#192d3e','brass':'#bb823b','wood':'#c7854a'}
        for f in scene['faces']:
            poly=' '.join(','.join(str(int(t)) for t in np.array(project(v))+offset) for v in f['vertices'])
            svg.append(f'<polygon id="{f["name"]}" points="{poly}" fill="{colors.get(f["material"],colors["navy"])}"/>')
        for e in scene['edges']:
            a=np.array(project(e['a']))+offset;b=np.array(project(e['b']))+offset
            svg.append(f'<path id="{e["id"]}" d="M{a[0]},{a[1]} L{b[0]},{b[1]}" fill="none" stroke="black" stroke-width="1"/>')
        svg.append('</svg>');(directory/f'parts{count}.svg').write_text('\n'.join(svg),encoding='utf-8')
        summary.append({'variant':count,'size':[w,h],'parts':len(scene['faces']),
                        'structural_edges':len(scene['edges']),'ink_pixels':int(ink.sum())})
    write(directory/'geometry.json',{'projection':'u=2x-2z;v=-x-z-y','variants':summary})


def material(recipe, reference, output):
    directory=output/'material';directory.mkdir(exist_ok=False)
    a=Appearance(reference,recipe['materials'])
    palette={name:p.tolist() for name,p in a.palettes.items()}
    write(directory/'palette.json',palette)
    write(directory/'provenance.json',a.report())
    for count in recipe['variants']:
        scene=read(output/'geometry'/f'parts{count}.json')
        b=np.load(output/'geometry'/f'buffers{count}.npz')
        rgb=np.zeros((*b['part'].shape,3),np.uint8)
        for f in scene['faces']:
            mask=b['part']==f['id']
            if not np.any(mask):
                continue
            if f['tone'] is None:
                rgb[mask]=a.sample(f['material'],b['u'][mask],b['v'][mask])
            else:
                rgb[mask]=a.palettes[f['material']][f['tone']]
        np.savez_compressed(directory/f'colors{count}.npz',rgb=rgb)


def raster(recipe, output):
    directory=output/'raster';directory.mkdir(exist_ok=False)
    palette=read(output/'material/palette.json')
    for count in recipe['variants']:
        scene=read(output/'geometry'/f'parts{count}.json')
        b=np.load(output/'geometry'/f'buffers{count}.npz')
        rgb=np.load(output/'material'/f'colors{count}.npz')['rgb'].copy()
        offset=np.array(scene['origin']);decor=np.zeros(b['part'].shape,bool)
        # All detail lives on declared visible surfaces. Cap occlusion is honored.
        for e in scene['decor']:
            a=(np.array(project(e['a']))+offset).tolist();z=(np.array(project(e['b']))+offset).tolist()
            for x,y in line(a,z):
                f=scene['faces'][int(b['part'][y,x])] if b['part'][y,x]>=0 else None
                if f is not None and not f['name'].startswith('cap.'):
                    rgb[y,x]=palette[e['material']][e['tone']];decor[y,x]=True
        # Immutable canonical E owns black; hardware glints cannot erase its paths.
        rgb[b['ink']]=[0,0,0]
        rgba=np.dstack((rgb,np.where(b['part']>=0,255,0).astype(np.uint8)))
        im=Image.fromarray(rgba);im.save(directory/f'cabinet-{count}.png')
        im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(directory/f'preview-{count}-x4.png')
        Image.fromarray((b['ink']*255).astype(np.uint8)).save(directory/f'structural-ink-{count}.png')
        np.savez_compressed(directory/f'owners{count}.npz',decor=decor)
    base=Image.open(directory/'cabinet-3.png')
    base.save(output/'native.png')
    base.resize((base.width*4,base.height*4),Image.Resampling.NEAREST).save(output/'preview-x4.png')
    display=Image.new('RGBA',(base.width*4,base.height*4),(180,180,172,255))
    display.alpha_composite(base.resize(display.size,Image.Resampling.NEAREST))
    display.convert('RGB').save(output/'preview-gray-x4.png')
    two=Image.open(directory/'preview-2-x4.png');three=Image.open(directory/'preview-3-x4.png')
    sheet=Image.new('RGBA',(two.width+three.width+24,max(two.height,three.height)),(0,0,0,0))
    sheet.alpha_composite(two,(0,0));sheet.alpha_composite(three,(two.width+24,0))
    sheet.save(output/'modular-preview-x4.png')


def validate(recipe, reference, output):
    checks=[];details=[]
    def check(name,ok,data=None):
        checks.append({'name':name,'pass':bool(ok),'detail':data})
    palette=read(output/'material/palette.json')
    check('fill_palette_never_black',all(any(int(c)>0 for c in color) for p in palette.values() for color in p))
    check('palette_tone_counts',all(len(palette[n])==m['tones'] for n,m in recipe['materials'].items()))
    check('reference_preserved',sha(reference)==recipe['reference_sha256'])
    for count in recipe['variants']:
        scene=read(output/'geometry'/f'parts{count}.json');b=np.load(output/'geometry'/f'buffers{count}.npz')
        rgba=np.asarray(Image.open(output/'raster'/f'cabinet-{count}.png').convert('RGBA'))
        black=np.all(rgba[:,:,:3]==0,axis=2)&(rgba[:,:,3]>0)
        check(f'black_equals_independent_E.{count}',np.array_equal(black,b['ink']),
              {'black':int(black.sum()),'extra':int((black&~b['ink']).sum()),'missing':int((b['ink']&~black).sum())})
        check(f'alpha_exact_geometry.{count}',np.array_equal(rgba[:,:,3]>0,b['part']>=0) and set(np.unique(rgba[:,:,3]))<={0,255})
        keys=[tuple(sorted((tuple(e['a']),tuple(e['b'])))) for e in scene['edges']]
        check(f'no_duplicate_canonical_edges.{count}',len(set(keys))==len(keys))
        hidden=[]
        for e in scene['edges']:
            for x,y in e['pixels']:
                f=scene['faces'][int(b['part'][y,x])] if b['part'][y,x]>=0 else None
                if not edge_visible(e,f):hidden.append([e['id'],x,y])
        check(f'no_hidden_structural_strokes.{count}',not hidden,hidden)
        # Width checks are per owned finite path. A shared multi-edge vertex is not a thick stroke.
        failures=[]
        for e in scene['edges']:
            if not e['pixels']:continue
            ps=np.array(e['pixels']);xs,ys=ps.T
            m=np.zeros(b['part'].shape,bool);m[ys,xs]=True
            square=m[:-1,:-1]&m[1:,:-1]&m[:-1,1:]&m[1:,1:]
            if square.any():failures.append(e['id'])
            q1,q2=project(e['a']),project(e['b']);dx=q2[0]-q1[0];dy=q2[1]-q1[1]
            if not (dx==0 or abs(dx)==2*abs(dy)):failures.append(e['id']+'.projection')
        check(f'owned_strokes_one_pixel_and_2to1.{count}',not failures,failures)
        for n in range(count):
            part=next(f for f in scene['faces'] if f['name']==f'handle.{n}')
            support=(b['part']==part['id'])&~b['ink']
            check(f'handle_colored_interior.{count}.{n}',int(support.sum())>=3,int(support.sum()))
        top=next(f for f in scene['faces'] if f['name']=='cap.top')
        tones=np.unique(rgba[b['part']==top['id'],:3],axis=0)
        check(f'wood_four_tones_present.{count}',all(any(np.array_equal(c,t) for t in tones) for c in palette['wood']))
        # Surface/shadow contrast is explicit in different observed RGB, never RGB black.
        for name in ['navy','side']:
            levels=np.array(palette[name],float)
            check(f'{name}_shade_separation.{count}',np.min(np.linalg.norm(levels[:,None]-levels[None,:]+np.eye(len(levels))[:,:,None]*999,axis=2))>=8,
                  palette[name])
        details.append({'variant':count,'native_size':scene['size'],'visible_rgb':len(np.unique(rgba[rgba[:,:,3]>0,:3],axis=0))})
    a=read(output/'geometry/parts2.json');b=read(output/'geometry/parts3.json')
    for n in range(2):
        for kind in ['door','handle','hinge']:
            aa=[f for f in a['faces'] if f['name'].startswith(f'{kind}.{n}')]
            bb=[f for f in b['faces'] if f['name'].startswith(f'{kind}.{n}')]
            # Numeric buffer IDs follow list order and may change when a module
            # is added. Semantic parts, vertices, material and UV must not change.
            check(f'unchanged_{kind}_module.{n}',
                  [{k:v for k,v in f.items() if k!='id'} for f in aa]==
                  [{k:v for k,v in f.items() if k!='id'} for f in bb])
    # Negative fixtures exercise rejection rather than masking incorrect dark fills.
    fixture_edges=[];seen=set();e=build(recipe,3)['edges'][0]
    add_edge(fixture_edges,seen,'fixture.original',e['a'],e['b'])
    duplicate_rejected=False
    try:add_edge(fixture_edges,seen,'fixture.duplicate',e['b'],e['a'])
    except ValueError:duplicate_rejected=True
    check('fixture_duplicate_edge_detected',duplicate_rejected)
    check('fixture_cap_occludes_body_edge',not edge_visible({'occlusion_class':'body'},{'occlusion_class':'cap'}))
    check('fixture_visible_body_edge_retained',edge_visible({'occlusion_class':'body'},{'occlusion_class':'body'}))
    fixture=output/'fixture-black-input.png';Image.new('RGB',(3,3),(0,0,0)).save(fixture)
    black_rejected=False
    try:Appearance(fixture,{'bad':{'quad':[[0,0],[2,0],[2,2],[0,2]],
                                 'palette_samples':[[0,0,3,3]],'tones':3}})
    except ValueError:black_rejected=True
    check('fixture_black_fill_detected',black_rejected)
    value={'checks':checks,'all_pass':all(x['pass'] for x in checks),'variants':details,
           'art_approved':False,'original_grid_recovered':False,
           'method':'editable fixed-view planar part authoring; observed RGB palette; direct native raster'}
    write(output/'validation.json',value)
    print(json.dumps({'all_pass':value['all_pass'],'failed':[x for x in checks if not x['pass']],'checks':len(checks)}))
    if not value['all_pass']:raise SystemExit(2)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['geometry','material','raster','validate'])
    parser.add_argument('--recipe',required=True);parser.add_argument('--reference',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();sys.stdout.reconfigure(encoding='utf-8')
    output=Path(args.output).resolve();recipe=read(args.recipe);reference=Path(args.reference).resolve()
    if not output.is_relative_to(ROOT):raise ValueError('Output must be inside workspace')
    if sha(reference)!=recipe['reference_sha256']:raise ValueError('Reference changed')
    started=time.perf_counter();output.mkdir(exist_ok=True)
    if args.stage=='geometry':geometry(recipe,output)
    elif args.stage=='material':material(recipe,reference,output)
    elif args.stage=='raster':raster(recipe,output)
    else:validate(recipe,reference,output)
    write(output/(args.stage+'-receipt.json'),{'stage':args.stage,'wall_seconds':time.perf_counter()-started,
                                              'reference_sha256':sha(reference),'recipe_sha256':sha(args.recipe)})
