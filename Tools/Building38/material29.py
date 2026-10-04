"""N29 native material clusters and handle microrelief. Never resizes an image."""
import argparse
import hashlib
import json
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'docs/artifacts/building39/run02/empty_counter'
MAP = ROOT/'Assets/Art/NativeBuilding41MaterialRepair/empty_counter.png'
ART_ROOTS = ('NativeBuilding39', 'NativeBuilding39Floor40', 'NativeBuilding41MaterialRepair')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def source_hashes():
    return {p.relative_to(ROOT).as_posix(): sha(p) for folder in ART_ROOTS
            for p in sorted((ROOT/'Assets/Art'/folder).rglob('*')) if p.is_file()}

def field(u, v, pitch_u, pitch_v, seed):
    """Continuous deterministic value noise; no independent per-pixel random."""
    x, y = u/pitch_u, v/pitch_v
    ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x-ix, y-iy
    fx, fy = fx*fx*(3-2*fx), fy*fy*(3-2*fy)
    def h(a,b):
        n = (a*374761393+b*668265263+seed*1442695041) & 0xffffffff
        n = ((n^(n>>13))*1274126177) & 0xffffffff
        return ((n^(n>>16)) & 65535)/65535.
    return ((1-fx)*(1-fy)*h(ix,iy)+fx*(1-fy)*h(ix+1,iy)+
            (1-fx)*fy*h(ix,iy+1)+fx*fy*h(ix+1,iy+1))

def remove_tiny(rank, mask):
    visited = np.zeros(mask.shape, bool)
    height, width = mask.shape
    for y,x in zip(*np.nonzero(mask & (rank!=2))):
        if visited[y,x]: continue
        value=int(rank[y,x]); group=[]; queue=deque([(y,x)]); visited[y,x]=True
        while queue:
            yy,xx=queue.popleft(); group.append((yy,xx))
            for dy,dx in ((0,1),(1,0),(0,-1),(-1,0)):
                a,b=yy+dy,xx+dx
                if 0<=a<height and 0<=b<width and mask[a,b] and not visited[a,b] and rank[a,b]==value:
                    visited[a,b]=True;queue.append((a,b))
        if len(group)<3:
            for a,b in group:rank[a,b]=2

def generate(out):
    if out.exists(): raise ValueError('Fresh version required; previous evidence preserved')
    out.mkdir(parents=True)
    old=np.asarray(Image.open(MAP).convert('RGBA')).copy()
    meta=json.loads((SOURCE/'geometry.json').read_text(encoding='utf-8'))
    design=meta['metadata']['cabinet_design']
    with np.load(SOURCE/'geometry.npz') as z:data={k:z[k] for k in z.files}
    new=old.copy(); mask=data['mask']; tick=data['design_tick']; dn=data['design_normal']
    navy=mask&(old[...,0]==2)&(data['part']==0)&(np.abs(dn[...,1])<.01)
    side=np.abs(dn[...,0])>.99
    u=np.where(side,tick[...,2],tick[...,0])*design['tick_scale_xyz'][0]
    v=tick[...,1]*design['tick_scale_xyz'][1]
    # Broad pigment fields plus sparse, short directional wear. Parameters are
    # material design choices, not a claim of recovered source lighting.
    broad=field(u,v,.27,.24,29)
    grain=field(u,v,.016,.105,73)
    rank=np.full(mask.shape,2,np.uint8)
    rank[navy&(broad<.31)]=1
    rank[navy&(broad>.72)]=3
    rank[navy&(grain<.16)&(broad<.56)]=1
    remove_tiny(rank,navy)
    new[...,1][navy]=rank[navy]
    normal=np.fromfile(SOURCE/'normal.f32',np.float32).reshape(*mask.shape,4).copy()
    original_normal=normal.copy(); handles=mask&(data['part']>=2)&(dn[...,2]<-.99)
    scale=np.asarray(design['tick_scale_xyz']); rotation=np.asarray(design['rotation'])
    basis=np.array([[.7071067811865476,0,-.7071067811865476],[-.3535533905932738,-.8660254037844386,-.3535533905932738]])
    j=basis@rotation@np.diag(scale)*meta['metadata']['pixels_per_metre']
    coefficient=abs(np.linalg.det(j[:,[0,1]]))/np.linalg.norm(j[:,1])
    angle=np.zeros(mask.shape)
    profile=design['profile']
    for i in range(design['count']):
        start=profile['end_cap']+i*profile['module_pitch']+profile['handle_x']
        left=(tick[...,0]-start)*coefficient
        right=(start+profile['handle_width']-tick[...,0])*coefficient
        d=np.maximum(0,np.minimum(left,right))
        theta=np.where(d<1,60,np.where(d<2,40,np.where(d<3,20,0)))
        s=np.where(left<right,-1,1)
        take=handles&(data['part']==i+2)
        angle[take]=theta[take]*s[take]
    radians=np.deg2rad(angle)
    curved=np.stack((np.sin(radians),np.zeros_like(angle),-np.cos(radians)),axis=-1)@rotation.T
    normal[...,:3][handles]=curved[handles]
    Image.fromarray(new,'RGBA').save(out/'material.png')
    normal.astype(np.float32).tofile(out/'normal.f32')
    # Native albedo preview: no lighting, no reconstruction, no downsample.
    palette=np.asarray(Image.open(ROOT/'Assets/Art/NativeBuilding39/palette.png').convert('RGB'))
    rgba=np.zeros_like(new);oldrgba=np.zeros_like(new)
    for a,b in ((new,rgba),(old,oldrgba)):
        b[mask,:3]=palette[a[...,0][mask]-1,a[...,1][mask]];b[mask,3]=255
    Image.fromarray(rgba).save(out/'albedo-native.png')
    Image.fromarray(oldrgba).save(out/'before-albedo-native.png')
    nlen=np.linalg.norm(normal[...,:3][mask],axis=-1)
    actual=curved[handles]@rotation
    left_response=np.maximum(0,actual@np.array([-.70710678,0,-.70710678]))
    right_response=np.maximum(0,actual@np.array([.70710678,0,-.70710678]))
    checks={
      'same_dimensions':new.shape==old.shape,
      'R_B_A_preserved':bool(np.array_equal(new[..., [0,2,3]],old[..., [0,2,3]])),
      'wood_rank_preserved':bool(np.array_equal(new[...,1][old[...,0]==1],old[...,1][old[...,0]==1])),
      'rank_changes_only_navy':bool(np.all(navy[new[...,1]!=old[...,1]])),
      'normal_changes_only_handle_front':bool(np.all(handles[np.any(normal!=original_normal,axis=-1)])),
      'normal_alpha_preserved':bool(np.array_equal(normal[...,3],original_normal[...,3])),
      'finite_unit_normals':bool(np.isfinite(normal).all() and np.max(np.abs(nlen-1))<1e-6),
      'valid_rank':bool(np.all(new[...,1]<=3)),
      'directional_response_reverses':bool(np.mean(left_response[angle[handles]<0])>np.mean(left_response[angle[handles]>0]) and np.mean(right_response[angle[handles]>0])>np.mean(right_response[angle[handles]<0])),
    }
    write(out/'calculation.json',{'checks':checks,'source_hashes':source_hashes(),
      'inputs':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (MAP,SOURCE/'normal.f32',SOURCE/'geometry.npz',SOURCE/'geometry.json')},
      'shape':list(new.shape),'navy_rank_counts':{str(i):int(np.sum(navy&(rank==i))) for i in (1,2,3)},
      'handle_front_cells':int(handles.sum()),'handle_angles':{str(a):int(np.sum(handles&(angle==a))) for a in sorted(set(angle[handles]))},
      'x_boundary_native_pixels_per_tick':float(coefficient),'changed_G_cells':int(np.sum(new[...,1]!=old[...,1])),
      'changed_normal_cells':int(np.sum(np.any(normal!=original_normal,axis=-1))),
      'outputs':{name:sha(out/name) for name in ('material.png','normal.f32','albedo-native.png','before-albedo-native.png')},
      'art_approval_claimed':False,'microrelief_cast_shadow_claimed':False})
    if not all(checks.values()):raise ValueError('Material calculation invariant failed')
    print(json.dumps({'checks':checks,'output':str(out)}))

def gate(out):
    calc=json.loads((out/'calculation.json').read_text(encoding='utf-8'))
    obs=json.loads((out/'observation.json').read_text(encoding='utf-8-sig'))
    final=json.loads((out/'final.json').read_text(encoding='utf-8-sig'))
    checks=dict(calc['checks'])
    checks.update({'source_hashes_preserved':calc['source_hashes']==source_hashes(),
      'same_geometry':obs['sameGeometry'],'same_lighting':obs['sameLighting'],
      'same_player_camera':obs['samePlayer'] and obs['sameCamera'],
      'play_mode_observation':obs['playMode'],'shader_errors_zero':obs['shaderErrors']==0,
      'integer_2px_display':abs(obs['screenPixelsPerCell']-2)<.001,
      'exactly_one_binding':obs['bindingCount']==1,
      'changed_visible_image':obs['changedPixels']>0,
      'saved_clean_scene':final['sceneSaved'] and not final['sceneDirty'] and not final['playing'],
      'output_hashes_frozen':all(sha(out/name)==h for name,h in calc['outputs'].items())})
    write(out/'validation.json',{'checks':checks,'passed':all(checks.values()),'art_approval_claimed':False})
    print(json.dumps({'passed':all(checks.values()),'checks':checks}))
    if not all(checks.values()):raise ValueError('N29 integration gate failed')

def verify(out):
    calc=json.loads((out/'calculation.json').read_text(encoding='utf-8'))
    if not all(calc['checks'].values()) or calc['source_hashes']!=source_hashes():
        raise ValueError('Existing calculation or source contract changed')
    for name,h in calc['outputs'].items():
        if sha(out/name)!=h:raise ValueError('Existing output changed: '+name)
    for name,h in calc['inputs'].items():
        if sha(ROOT/name)!=h:raise ValueError('Existing input changed: '+name)
    print(json.dumps({'existing_calculation_preserved':True,'regeneration_count':0}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['generate','verify','gate']);p.add_argument('--output',required=True)
    a=p.parse_args(); {'generate':generate,'verify':verify,'gate':gate}[a.phase](Path(a.output).resolve())
