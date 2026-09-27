"""Standard planar homography onto canonical 3D faces, with identical color/depth ownership.

This is coordinate reprojection, not PerfectPixel normalization or inferred 3D reconstruction.
"""
import argparse, copy, hashlib, json, math
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
R=np.array([1,0,-1],float)/math.sqrt(2)
U=np.array([.5/math.sqrt(2),math.sqrt(.75),.5/math.sqrt(2)])
D=np.cross(R,U)

def homography(a,b):
    matrix=[]; rhs=[]
    for (x,y),(s,t) in zip(a,b):
        matrix.extend([[x,y,1,0,0,0,-s*x,-s*y],[0,0,0,x,y,1,-t*x,-t*y]])
        rhs.extend([s,t])
    return np.append(np.linalg.solve(matrix,rhs),1).reshape(3,3)

def transform(h, p):
    q=np.concatenate([p,np.ones((*p.shape[:-1],1))],-1)@h.T
    return q[...,:2]/q[...,2,None]

def polygon_distance(p,quad):
    """Distance to a convex face domain; zero inside. Used for measured cap/foot overhangs."""
    cross=[]; distances=[]
    for a,b in zip(quad,np.roll(quad,-1,axis=0)):
        ab=b-a;ap=p-a
        t=np.clip((ap@ab)/(ab@ab),0,1)
        distances.append(np.linalg.norm(ap-t[...,None]*ab,axis=-1))
        cross.append(ab[0]*ap[...,1]-ab[1]*ap[...,0])
    signs=np.stack(cross)
    inside=(signs.min(0)>=-1e-7)|(signs.max(0)<=1e-7)
    return np.where(inside,0,np.min(distances,axis=0))

def project(spec,out):
    out.mkdir(parents=True,exist_ok=True)
    source=ROOT/spec['source']
    pixels=np.array(Image.open(source).convert('RGBA'))
    ppu=spec['ppu']
    faces=copy.deepcopy(spec['faces'])
    vertices=np.array([p for f in faces for p in f['xyz']])
    projected=np.column_stack((vertices@R, -vertices@U))*ppu
    source_y,source_x=np.indices(pixels.shape[:2]); source_q=np.stack([source_x,source_y],-1)
    distances=np.stack([polygon_distance(source_q,np.array(f['source_xy'],float)) for f in faces])
    owners=distances.argmin(0)
    source_opaque=pixels[...,3]>=128
    extrapolated=int((source_opaque&(distances.min(0)>0)).sum())
    ground_shift=0.0
    if spec.get('ground_from_source_outline',False):
        minima=[]
        square=np.array([[0,0],[1,0],[1,1],[0,1]],float)
        for i,f in enumerate(faces):
            v=np.array(f['xyz'],float);s=np.array(f['source_xy'],float)
            centers=source_q[source_opaque&(owners==i)]
            coords=np.concatenate([centers+offset for offset in ((-.5,-.5),(-.5,.5),(.5,-.5),(.5,.5))])
            uv=transform(homography(s,square),coords)
            positions=v[0]+uv[:,0,None]*(v[1]-v[0])+uv[:,1,None]*(v[3]-v[0])
            minima.append(float(positions[:,1].min()))
        ground_shift=-min(minima)+.5/ppu
        for f in faces:
            f['xyz']=[[x,y+ground_shift,z] for x,y,z in f['xyz']]
        vertices=np.array([p for f in faces for p in f['xyz']])
        projected=np.column_stack((vertices@R,-vertices@U))*ppu
    # Source outline extensions are carried by the nearest measured plane. No dilation or invented colors.
    if spec.get('preserve_outline',False):
        added=[]
        for i,f in enumerate(faces):
            s=np.array(f['source_xy']);v=np.array(f['xyz']); t=np.column_stack((v@R,-v@U))*ppu
            mask=source_opaque&(owners==i)
            added.append(transform(homography(s,t),source_q[mask]))
        projected=np.concatenate([projected,*added])
    origin=np.floor(projected.min(0))-2
    extent=np.ceil(projected.max(0))+2
    w,h=(extent-origin).astype(int)
    yy,xx=np.indices((h,w)); q=np.stack([xx+.5,yy+.5],-1)
    rgba=np.zeros((h,w,4),np.uint8)
    xyz=np.zeros((h,w,4),np.float32)
    near=np.full((h,w),np.inf)
    face_ids=np.full((h,w),-1,np.int16)
    records=[]
    for index,f in enumerate(faces):
        v=np.array(f['xyz'],float); s=np.array(f['source_xy'],float)
        t=np.column_stack((v@R,-v@U))*ppu-origin
        # 0 -> 1 is u; 0 -> 3 is v. Canonical faces are parallelograms.
        assert np.max(np.abs(v[2]-(v[1]+v[3]-v[0])))<1e-6, f['id']
        basis=np.column_stack((t[1]-t[0],t[3]-t[0]))
        uv=(q-t[0])@np.linalg.inv(basis).T
        inside=(uv[...,0]>=-1e-8)&(uv[...,0]<=1+1e-8)&(uv[...,1]>=-1e-8)&(uv[...,1]<=1+1e-8)
        source_h=homography(t,s)
        sq=transform(source_h,q)
        sx=np.rint(sq[...,0]).astype(int); sy=np.rint(sq[...,1]).astype(int)
        inside &= (sx>=0)&(sx<pixels.shape[1])&(sy>=0)&(sy<pixels.shape[0])
        color=pixels[np.clip(sy,0,pixels.shape[0]-1),np.clip(sx,0,pixels.shape[1]-1)]
        if spec.get('preserve_outline',False):
            inside=(sx>=0)&(sx<pixels.shape[1])&(sy>=0)&(sy<pixels.shape[0])
            inside &= owners[np.clip(sy,0,pixels.shape[0]-1),np.clip(sx,0,pixels.shape[1]-1)]==index
        pos=v[0]+uv[...,0,None]*(v[1]-v[0])+uv[...,1,None]*(v[3]-v[0])
        depth=pos@D
        write=inside&(color[...,3]>=128)&(depth<near-1e-7)
        rgba[write]=color[write]; rgba[write,3]=255
        xyz[write,:3]=pos[write];xyz[write,3]=1
        near[write]=depth[write];face_ids[write]=index
        held=[]
        fwd=np.linalg.inv(source_h)
        for line in f.get('holdout',[]):
            a,b=transform(fwd,np.array(line['points'],float)); delta=b-a
            slope=None if abs(delta[0])<1e-8 else float(delta[1]/delta[0])
            held.append({'id':line['id'],'slope':slope,'target':line['target_slope'],
                         'residual_px':float(abs(delta[1]-line['target_slope']*delta[0]))})
        # Matrix residual measures numerical correspondence only, not artistic agreement.
        reproj=float(np.abs(transform(source_h,t)-s).max())
        records.append({'id':f['id'],'reprojection_residual':reproj,'written_pixels':int(write.sum()),'holdout':held})
    Image.fromarray(rgba).save(out/'native.png')
    # Unity LoadRawTextureData starts at lower-left, hence an explicit row flip.
    np.flipud(xyz).astype('<f4').tofile(out/'positions.rgba32f')
    Image.fromarray(np.where(face_ids<0,0,face_ids+1).astype(np.uint8)).save(out/'face-id.png')
    report={'id':spec['id'],'source':spec['source'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'width':int(w),'height':int(h),'ppu':ppu,'left':float(origin[0]/ppu),'top':float(-origin[1]/ppu),
            'opaque_pixels':int((rgba[...,3]>0).sum()),'faces':records,
            'source_outline_pixels_outside_landmark_quads':extrapolated,
            'outline_policy':'nearest-plane extrapolation' if spec.get('preserve_outline',False) else 'quad only; experimental crop',
            'ground_shift_from_measured_outline_m':ground_shift,
            'support_height':max([float(f['xyz'][0][1]) for f in faces if max(p[1] for p in f['xyz'])-min(p[1] for p in f['xyz'])<1e-6] or [0.0]),
            'surface_xyz_min':xyz[xyz[...,3]>0,:3].min(0).tolist(),
            'surface_xyz_max':xyz[xyz[...,3]>0,:3].max(0).tolist(),
            'declared_limitations':spec.get('limitations',[]),'spec':str(out/'spec.json')}
    (out/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf8')
    (out/'receipt.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('spec');parser.add_argument('output');a=parser.parse_args()
    project(json.loads(Path(a.spec).read_text(encoding='utf-8-sig')),Path(a.output))
