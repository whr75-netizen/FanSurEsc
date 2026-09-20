"""Blender finite-mesh ray casting. No camera RGB texture or rendered-image resize."""
import argparse
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).parent))
from common import basis,read,write,resolve,sha,gap_aperture

parser=argparse.ArgumentParser()
parser.add_argument('--stage',choices=['geometry','raster'],required=True)
parser.add_argument('--contract',required=True)
parser.add_argument('--output',required=True)
parser.add_argument('--geometry')
parser.add_argument('--settings')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
contract=read(args.contract);out=Path(args.output)
out.mkdir(parents=True,exist_ok=False)
source=resolve(contract['source_blend']) if args.stage=='geometry' else Path(args.geometry)/'scene.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
meshes=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name)
assert len(meshes)==12,'Expected the inspected twelve-part desk'
assert all(not o.modifiers and not o.constraints and o.parent is None for o in meshes),'Unsupported geometry: modifiers/constraints/parent'
assert all(max(abs(a) for a in o.rotation_euler)<1e-6 for o in meshes),'This desk template requires axis-aligned part boxes'

def descriptions():
    result=[]
    for i,obj in enumerate(meshes):
        pts=np.array([list(obj.matrix_world@Vector(p)) for p in obj.bound_box])
        result.append({'id':i,'name':obj.name,'role':obj.get('part_role','body'),
                       'center':list(obj.location),'dimensions':list(obj.dimensions),
                       'minimum':pts.min(0).tolist(),'maximum':pts.max(0).tolist()})
    return result

def check_geometry(parts):
    legs=[o for o in parts if o['role']=='leg'];table=next(o for o in parts if o['name']=='Tabletop')
    checks={'four_equal_legs':len(legs)==4 and all(np.max(np.abs(np.array(o['dimensions'])-legs[0]['dimensions']))<1e-6 for o in legs),
            'feet_common_zero':all(abs(o['minimum'][2])<1e-6 for o in legs),
            'legs_touch_table':all(abs(o['maximum'][2]-table['minimum'][2])<1e-6 for o in legs),
            'positive_extents':all(min(o['dimensions'])>0 for o in parts)}
    for suffix in ['-1','1']:
        drawer=next(o for o in parts if o['name']==f'Drawer_{suffix}')
        handle=next(o for o in parts if o['name']==f'Handle_{suffix}')
        checks[f'handle_aligned_{suffix}']=abs(drawer['center'][0]-handle['center'][0])<1e-6
    return checks

if args.stage=='geometry':
    # Save a pure geometry copy: old appearance is not carried into this pipeline.
    for obj in list(bpy.context.scene.objects):
        if obj.type!='MESH':bpy.data.objects.remove(obj,do_unlink=True)
    for obj in meshes:obj.data.materials.clear()
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    for im in list(bpy.data.images):
        if im.type not in ('RENDER_RESULT','COMPOSITING'):bpy.data.images.remove(im)
    parts=descriptions();checks=check_geometry(parts)
    left=next(p for p in parts if p['name']=='Drawer_-1');right=next(p for p in parts if p['name']=='Drawer_1')
    spec={'parts':parts,'checks':checks,'source_sha256':sha(source),
          'drawer_span':right['maximum'][0]-left['minimum'][0],
          'drawer_gap':right['minimum'][0]-left['maximum'][0],
          'source_appearance_used':False,'bpy_version':bpy.app.version_string}
    write(out/'geometry.json',spec)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
    assert all(checks.values()),checks
    sys.exit(0)

settings=read(args.settings);base=read(Path(args.geometry)/'geometry.json')
change=settings.get('drawer_gap_override')
if change is not None:
    span=base['drawer_span'];new_width=(span-change)/2
    assert new_width>0 and change<=span*contract['repair']['max_gap_fraction_of_span']+1e-9
    for sign in (-1,1):
        drawer=bpy.data.objects[f'Drawer_{sign}'];handle=bpy.data.objects[f'Handle_{sign}']
        drawer.dimensions.x=new_width
        drawer.location.x=sign*(new_width+change)/2
        handle.location.x=drawer.location.x
        handle.dimensions.x=new_width*.19
    bpy.context.view_layer.update()
parts=descriptions();checks=check_geometry(parts)
assert all(checks.values()),checks

vertices=[];triangles=[];tri_part=[];tri_face=[]
for part_i,obj in enumerate(meshes):
    offset=len(vertices)
    vertices.extend([obj.matrix_world@v.co for v in obj.data.vertices])
    obj.data.calc_loop_triangles()
    for tri in obj.data.loop_triangles:
        triangles.append(tuple(offset+k for k in tri.vertices));tri_part.append(part_i);tri_face.append(tri.polygon_index)
bvh=BVHTree.FromPolygons(vertices,triangles,all_triangles=True,epsilon=0.0)
r,u,d=basis(contract['camera']);P=contract['camera']['pixels_per_meter']
allpoints=np.array([list(v) for v in vertices]);xy=np.column_stack((allpoints@r,-allpoints@u))*P
mn=np.floor(xy.min(0));mx=np.ceil(xy.max(0));margin=contract['camera']['margin_pixels']
width,height=(mx-mn+margin*2).astype(int)
assert width<=contract['camera']['max_width'] and height<=contract['camera']['max_height'],'Pixel budget exceeded'
screen_origin=mn-margin
distance=float(np.max(allpoints@d)+4)
ray_direction=Vector(-d)
light=np.array(contract['lighting']['to_light'],float);light/=np.linalg.norm(light)
epsilon=float(32*np.finfo(np.float32).eps*max(1,np.abs(allpoints).max()))
to_light=Vector(light)
mask=np.zeros((height,width),bool);positions=np.zeros((height,width,3),np.float32)
normals=np.zeros_like(positions);ids=np.full((height,width),-1,np.int16);faces=np.full_like(ids,-1)
depth=np.zeros((height,width),np.float32);visible=np.zeros((height,width),bool)

def origin(x,y):
    q=(screen_origin+np.array([x,y]))/P
    return Vector(r*q[0]-u*q[1]+d*distance)

def cast(x,y):return bvh.ray_cast(origin(x,y),ray_direction,100.0)

for y in range(height):
    for x in range(width):
        loc,n,tri,t=cast(x+.5,y+.5)
        if tri is None:continue
        mask[y,x]=True;positions[y,x]=loc;normals[y,x]=n
        ids[y,x]=tri_part[tri];faces[y,x]=tri_face[tri];depth[y,x]=t
        start=loc+n*epsilon
        visible[y,x]=bvh.ray_cast(start,to_light,100.0)[2] is None

# Only real discontinuities create boundaries. Same-plane triangle tessellation is ignored.
edge=np.zeros_like(mask);ambiguous=0;boundary_candidates=0;records=[]
for axis in (0,1):
    if axis==0:
        pairs=((y,x,y,x+1) for y in range(height) for x in range(width-1))
    else:pairs=((y,x,y+1,x) for y in range(height-1) for x in range(width))
    for y,x,yy,xx in pairs:
        a,b=mask[y,x],mask[yy,xx]
        if not a and not b:continue
        if a!=b:
            edge[y if a else yy,x if a else xx]=True
            continue
        changed=(ids[y,x]!=ids[yy,xx] or float(normals[y,x]@normals[yy,xx])<.999)
        if not changed:continue
        boundary_candidates+=1
        # A finite-mesh ray at the common pixel boundary chooses the visible owner.
        loc,n,tri,t=cast((x+xx)/2+.5,(y+yy)/2+.5)
        owner=(tri_part[tri],tri_face[tri]) if tri is not None else None
        chosen=None
        if owner==(int(ids[y,x]),int(faces[y,x])):chosen=(y,x)
        elif owner==(int(ids[yy,xx]),int(faces[yy,xx])):chosen=(yy,xx)
        if chosen is None:ambiguous+=1;continue
        edge[chosen]=True
        records.append([chosen[0],chosen[1],owner[0],owner[1]])

# Independent box slab check against selected actual scene rays (not a second BVH).
def slab(o,direction):
    hits=[]
    for part in parts:
        lo=np.array(part['minimum']);hi=np.array(part['maximum']);near=-np.inf;far=np.inf
        for k in range(3):
            if abs(direction[k])<1e-12:
                if o[k]<lo[k] or o[k]>hi[k]:near=np.inf;break
            else:
                t0,t1=sorted(((lo[k]-o[k])/direction[k],(hi[k]-o[k])/direction[k]))
                near=max(near,t0);far=min(far,t1)
        if far>=max(0,near):hits.append((max(near,0),part['id']))
    return min(hits) if hits else None

slab_checks=[]
for part in parts:
    points=np.argwhere(ids==part['id'])
    if not len(points):continue
    y,x=points[len(points)//2]
    expected=slab(np.array(origin(x+.5,y+.5)),-d)
    slab_checks.append({'part':part['name'],'pixel':[int(x),int(y)],
                        'same_owner':expected is not None and expected[1]==int(ids[y,x]),
                        'depth_error':abs(expected[0]-float(depth[y,x])) if expected else None})

# Observe the actual finite owner behind the front gap along its center line.
left=next(p for p in parts if p['name']=='Drawer_-1');right=next(p for p in parts if p['name']=='Drawer_1')
gap=right['minimum'][0]-left['maximum'][0]
aperture=gap_aperture(gap,left['dimensions'][1],contract['camera'],contract['pixel']['minimum_gap_pixels'])
gap_owners=[]
for f in (.25,.5,.75):
    q=np.array([aperture['probe_x'],left['minimum'][1]-.00001,left['minimum'][2]+f*left['dimensions'][2]])
    sx,sy=(np.array([q@r,-q@u])*P-screen_origin)
    hit=cast(sx,sy);owner=tri_part[hit[2]] if hit[2] is not None else -1
    gap_owners.append(owner)

np.savez_compressed(out/'buffers.npz',mask=mask,positions=positions,normals=normals,part=ids,face=faces,
                    depth=depth,visibility=visible,edges=edge,edge_records=np.array(records,dtype=np.int32))
write(out/'raster.json',{'size':[int(width),int(height)],'pixels_per_meter':P,'camera':contract['camera'],
    'screen_origin':screen_origin.tolist(),'camera_distance':distance,'shadow_offset_m':epsilon,
    'parts':parts,'geometry_checks':checks,'drawer_gap':gap,'gap_aperture':aperture,'gap_ray_owners':gap_owners,
    'drawer_ids':[left['id'],right['id']],'finite_boundary_ambiguous':ambiguous,
    'boundary_candidates':boundary_candidates,'slab_checks':slab_checks,
    'foreground_pixels':int(mask.sum()),'shadow_pixels':int((mask&~visible).sum()),
    'source_geometry_sha256':sha(source),'bpy_version':bpy.app.version_string})
bpy.ops.wm.save_as_mainfile(filepath=str(out/'desk.blend'))
print('FINITE_MESH_RASTER_READY')
