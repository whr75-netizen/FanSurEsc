"""Same-frame native triangle/alpha queries with recorded material provenance.

No neighbouring colour/depth stand-ins. Alpha transition intervals stay unknown.
The caller must validate this CPU ray adapter against actual111 GPU witnesses.
"""
from pathlib import Path
import json,hashlib,os
import numpy as np
from PIL import Image
from geometry111 import H,R,read

class NativeAlpha:
    def __init__(self,ctx):
        self.ctx=ctx;self.images={};self.sources={};frozen=os.environ.get('PIXEL111_FROZEN_INPUTS')=='1'
        if frozen:
            data=read(H/'inputs/ALPHA111.json');assert ctx['sourceId']in data['captureSourceIds'];rows=data['images']
        else:
            registry=read(R/'renderer-family59/SOURCE_REGISTRY59.json');audit=read(Path(r'C:\Users\15352\Documents\Codex\2026-10-30\task\model-source\SOURCE_AUDIT.json'));repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');model=repo/registry['modelAsset'];assert hashlib.sha256(model.read_bytes()).hexdigest()==registry['modelSHA256']
        partTris=ctx['partMap'][ctx['partMap']>=0]
        for mi in np.unique(ctx['triangles'][partTris,3]):
            triangles=np.where(ctx['triangles'][:,3]==mi)[0];roles=np.unique(ctx['sources'][triangles,:2],axis=0);assert len(roles)==1;slot,sm=map(int,roles[0])
            if frozen:
                row=next(v for v in rows if v['renderer']==slot and v['submesh']==sm);p=H/'inputs'/row['file'];expected=row['sha256'];provenance=row
            else:
                row=next(v for v in registry['bindings']if v['rendererOrdinal']==slot and v['subMesh']==sm);mat=next(v for v in audit['materials']if v['materialId']==row['materialId']);p=Path(mat['image']['file']);expected=row['imageSHA256'];provenance={'renderer':slot,'submesh':sm,'imageIndex':row['imageIndex'],'sha256':expected,'sourceModelSHA256':registry['modelSHA256']}
            data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==expected;a=np.asarray(Image.open(p).convert('RGBA'))[:,:,3].astype(float)/255;props=ctx['materials'][mi];assert list(a.shape[::-1])==list(map(int,props[0,1:3]));self.images[int(mi)]=a;self.sources[int(mi)]=provenance
    @staticmethod
    def wrap(p,n,mode):
        if mode==0:return np.mod(p,n)
        if mode==1:return np.clip(p,0,n-1)
        raise ValueError('Unsupported source wrap; no approximation')
    def corners(self,mi,uv):
        tex=self.images[mi];h,w=tex.shape;v=np.asarray(uv);pos=np.c_[v[:,0]*w-.5,(1-v[:,1])*h-.5];ij=np.floor(pos).astype(int);f=pos-ij;m=self.ctx['materials'][mi];xx=self.wrap(ij[:,0,None]+np.array([0,1,0,1]),w,int(m[1,3]));yy=self.wrap(ij[:,1,None]+np.array([0,0,1,1]),h,int(m[2,0]));a=tex[yy,xx]*float(m[1,0]);weights=np.c_[(1-f[:,0])*(1-f[:,1]),f[:,0]*(1-f[:,1]),(1-f[:,0])*f[:,1],f[:,0]*f[:,1]];return a,weights
    def bounds(self,mi,uv):
        a,_=self.corners(mi,uv);mode=int(self.ctx['materials'][mi,0,3]);cut=float(self.ctx['materials'][mi,1,1])
        if mode==0:return np.ones((len(a),2))
        lo,hi=a.min(1),a.max(1)
        if mode==1:return np.c_[(lo>=cut).astype(float),(hi>=cut).astype(float)]
        return np.c_[lo,hi]

class FaceRay:
    def __init__(self,ctx,alpha):
        self.c=ctx;self.alpha=alpha;self.tids=np.where((ctx['sources'][:,0]==1)&(ctx['sources'][:,1]==3))[0];ids=ctx['triangles'][self.tids,:3];self.ids=ids;self.xy=ctx['physicalXY'][ids];self.z=ctx['depth'][ids];self.w=ctx['physicalW'][ids];a=np.stack([self.xy[:,1]-self.xy[:,0],self.xy[:,2]-self.xy[:,0]],axis=2);det=np.linalg.det(a);self.good=abs(det)>1e-12;self.det=det;self.inv=np.zeros_like(a);self.inv[self.good]=np.linalg.inv(a[self.good])
    def query(self,world,depthOverride=None,canvasOwner=None,canvasBank=None):
        if not len(world):return []
        c=self.c;a=np.c_[world,np.ones(len(world))]@c['view'].T;cl=a@c['projection'].T;q=np.c_[(cl[:,0]/cl[:,3]*.5+.5)*480,(.5-cl[:,1]/cl[:,3]*.5)*272];z=-a[:,2]if depthOverride is None else np.array(depthOverride);out=[]
        for start in range(0,len(q),32):
            delta=q[None,start:start+32]-self.xy[:,0,None];ab=np.einsum('tij,tqj->tqi',self.inv,delta);b=np.concatenate([1-ab.sum(2,keepdims=True),ab],axis=2);pw=b/self.w[:,None];pw/=pw.sum(2,keepdims=True);depth=(pw*self.z[:,None]).sum(2);front=self.good[:,None]&(b.min(2)>=-1e-7)&(depth<z[None,start:start+32]-3e-5)
            for j in range(len(delta[0])):
                lo=hi=1.;hits=[]
                for t in np.where(front[:,j])[0]:
                    tid=self.tids[t];mi=int(c['triangles'][tid,3]);cull=int(c['materials'][mi,1,2]);winding=1 if self.det[t]>0 else-1
                    if cull==2 and winding!=1 or cull==1 and winding==1:continue
                    uv=pw[t,j]@c['uv'][self.ids[t]]
                    if canvasOwner is not None:
                        rest=np.r_[pw[t,j]@c['rest'][self.ids[t]],1];xy=np.array([rest@c['projectionX'][canvasOwner],rest@c['projectionY'][canvasOwner]]);key=tuple(np.floor(xy).astype(int))
                        if any((canvasOwner,part,*key)in canvasBank for part in [1,4]):continue
                    alpha=self.alpha.bounds(mi,[uv])[0];lo*=1-alpha[1];hi*=1-alpha[0]
                    if alpha[1]>0:hits.append({'triangle':int(tid),'source':c['sources'][tid,:3].tolist(),'depth':float(depth[t,j]),'sourceDepth':float(z[start+j]),'UV':uv.tolist(),'alphaBounds':alpha.tolist()})
                out.append({'faceVisibilityInterval':[lo,hi],'hits':hits})
        return out

def barycentric(tri,points):
    a=np.stack([tri[1]-tri[0],tri[2]-tri[0]],axis=1)
    if abs(np.linalg.det(a))<=1e-16:return None
    uv=(np.asarray(points)-tri[0])@np.linalg.inv(a).T;return np.c_[1-uv.sum(1),uv]

def carrier_at(ctx,alpha,owner,part,points,geometryOnly=False,canvasBank=None):
    """All current native carriers at each CANONICAL destination fine point."""
    result=[[]for _ in points];tids=ctx['partMap'][part];tids=tids[tids>=0];points=np.asarray(points)
    for tid in tids:
        ids=ctx['triangles'][tid,:3];tri=ctx['maps'][owner][ids];b=barycentric(tri,points)
        if b is None:continue
        for k in np.where(b.min(1)>=-1e-7)[0]:
            ownerValue=float(b[k]@ctx['triOwners'][tid,:3])
            if int(np.rint(ownerValue))!=owner:continue
            mi=int(ctx['triangles'][tid,3]);physical=ctx['physicalXY'][ids];det=np.linalg.det(np.stack([physical[1]-physical[0],physical[2]-physical[0]],axis=1));cull=int(ctx['materials'][mi,1,2]);sign=1 if det>0 else-1
            if cull==2 and sign!=1 or cull==1 and sign==1:continue
            uv=b[k]@ctx['uv'][ids];bounds=np.ones(2)if geometryOnly else alpha.bounds(mi,[uv])[0]
            if canvasBank is not None:
                rest=np.r_[b[k]@ctx['rest'][ids],1];xy=np.array([rest@ctx['projectionX'][owner],rest@ctx['projectionY'][owner]]);key=tuple(np.floor(xy).astype(int))
                if not any((owner,p,*key)in canvasBank for p in [1,4]):continue
            world=b[k]@ctx['world'][ids];depth=float(b[k]@ctx['depth'][ids]);result[k].append({'triangle':int(tid),'primitive':int(ctx['sources'][tid,2]),'source':ctx['sources'][tid,:3].tolist(),'material':mi,'barycentric':b[k].tolist(),'world':world.tolist(),'depth':depth,'UV':uv.tolist(),'candidateAlphaBounds':bounds.tolist(),'sourcePigmentAlphaUsedAsDestinationGate':not geometryOnly})
    return result
