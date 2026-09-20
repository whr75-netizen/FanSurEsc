"""Shared immutable contracts and per-stage receipts, not a second graph engine."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
PYTHON=Path('C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
BLENDER=Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def resolve(path):
    p=Path(path);return p if p.is_absolute() else ROOT/p
def basis(camera):
    phi,theta=np.radians([camera['azimuth_degrees'],camera['elevation_degrees']])
    r=np.array([np.cos(phi),np.sin(phi),0.])
    u=np.array([-np.sin(phi)*np.sin(theta),np.cos(phi)*np.sin(theta),np.cos(theta)])
    return r,u,np.cross(r,u)
def gap_coefficient(camera):
    r,u,_=basis(camera);B=np.stack([r,-u]);a=B@np.array([1.,0,0]);e=B@np.array([0.,0,1])
    return camera['pixels_per_meter']*abs(a[0]*e[1]-a[1]*e[0])/np.linalg.norm(e)

def gap_aperture(gap,front_depth,camera,required_pixels):
    """Intersection of front/back rectangular slit intervals along the view ray."""
    phi=float(np.radians(camera['azimuth_degrees']))
    shift=float(front_depth*np.tan(phi))
    lo=max(-gap/2,-gap/2+shift);hi=min(gap/2,gap/2+shift)
    coefficient=float(gap_coefficient(camera))
    return {'front_width_pixels':float(gap*coefficient),
            'clear_width_pixels':max(0.0,float(hi-lo))*coefficient,
            'front_interval':[float(lo),float(hi)],'probe_x':float(shift/2),
            'required_gap_m':abs(shift)+required_pixels/coefficient,
            'ray_x_shift_m':shift,'front_depth_m':float(front_depth)}
def linear(rgb):
    x=np.asarray(rgb,float)/255
    return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def srgb(x):
    x=np.maximum(0,np.asarray(x));v=np.where(x<=.0031308,12.92*x,1.055*x**(1/2.4)-.055)
    return np.clip(np.rint(v*255),0,255).astype('uint8')
def passdir(run,index):return Path(run)/f'pass-{index}'

def receipt(directory,stage,inputs,outputs,details):
    result={'stage':stage,'inputs':{str(Path(p).resolve()):sha(p) for p in inputs},
            'outputs':{str(Path(p).resolve()):sha(p) for p in outputs},'details':details}
    write(Path(directory)/'stage_receipt.json',result)
    return result

def verify_receipt(path):
    r=read(path)
    for bucket in ('inputs','outputs'):
        for p,h in r[bucket].items():
            if not Path(p).is_file() or sha(p)!=h:raise ValueError(f'STALE_ARTIFACT: {p}')
    return r

def surface_boundaries(buffers):
    """Four-connected visible surface pairs; no hidden/infinite face is rasterized."""
    mask=buffers['mask'];part=buffers['part'];face=buffers['face'];h,w=mask.shape
    groups={};silhouette=np.zeros_like(mask)
    for dy,dx in ((0,1),(1,0)):
        for y in range(h-dy):
            for x in range(w-dx):
                q=(y+dy,x+dx);a=bool(mask[y,x]);b=bool(mask[q])
                if a!=b:silhouette[(y,x) if a else q]=True
                if not a or not b:continue
                ka=(int(part[y,x]),int(face[y,x]));kb=(int(part[q]),int(face[q]))
                if ka==kb:continue
                key=tuple(sorted((ka,kb)));pair=((y,x),q) if ka==key[0] else (q,(y,x))
                groups.setdefault(key,[]).append(pair)
    return groups,silhouette

def consistent_edges(buffers,camera):
    """A stroke convention on visible samples, separate from geometric depth ownership.

    Parallel front planes: ink the nearer plane uniformly. Other creases: ink the
    more camera-facing plane uniformly. This cannot reveal an occluded surface.
    One owner per pair prevents the horizontal/vertical midpoint alternation.
    Junctions and silhouette stair steps do not imply global Euclidean 1px width.
    """
    groups,edge=surface_boundaries(buffers);_,_,view=basis(camera);records=[];policies=[]
    for key,pairs in groups.items():
        a,b=pairs[0];na=buffers['normals'][a];nb=buffers['normals'][b]
        pa=buffers['positions'][a];pb=buffers['positions'][b]
        parallel=float(na@nb)>.99999
        if parallel:
            score=[float(na@pa),float(na@pb)]
        else:score=[float(na@view),float(nb@view)]
        # Geometry key resolves true ties; object names never set draw order.
        keys=[]
        for j,p in enumerate((a,b)):
            area=(buffers['part']==key[j][0])&(buffers['face']==key[j][1])
            lo=buffers['positions'][area].min(axis=0);hi=buffers['positions'][area].max(axis=0)
            keys.append((round(score[j],7),*np.round(buffers['normals'][p],7).tolist(),
                         *np.round((lo+hi)/2,6).tolist()))
        owner=0 if keys[0]>=keys[1] else 1
        for pair in pairs:
            q=pair[owner];edge[q]=True;records.append([*q,*key[owner]])
        policies.append({'pair':[list(k) for k in key],'owner':list(key[owner]),
                         'rule':'nearer_parallel_plane' if parallel else 'camera_facing_stroke',
                         'samples':len(pairs)})
    return edge,np.array(records,dtype=np.int32).reshape(-1,4),policies

def parallel_double_strokes(buffers,ink):
    """Measure real PNG ink on both sides of a parallel seam, away from junctions."""
    groups,_=surface_boundaries(buffers);mask=buffers['mask'];part=buffers['part'];face=buffers['face'];h,w=mask.shape
    failures=[]
    for key,pairs in groups.items():
        if key[0][0]==key[1][0] or len(pairs)<8:continue
        a,b=pairs[0]
        if float(buffers['normals'][a]@buffers['normals'][b])<.99999:continue
        examples=[];count=0
        for a,b in pairs:
            if not (ink[a] and ink[b]):continue
            isolated=True
            for y,x in (a,b):
                for yy in range(max(0,y-1),min(h,y+2)):
                    for xx in range(max(0,x-1),min(w,x+2)):
                        if not mask[yy,xx] or (int(part[yy,xx]),int(face[yy,xx])) not in key:isolated=False
            if isolated:
                count+=1
                if len(examples)<6:examples.append([[int(a[1]),int(a[0])],[int(b[1]),int(b[0])]])
        if count:failures.append({'pair':[list(k) for k in key],'count':count,'pixel_pairs_xy':examples})
    return failures
