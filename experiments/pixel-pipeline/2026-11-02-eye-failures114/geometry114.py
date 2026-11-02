"""Exact saved current geometry; no scene access or reconstructed morph."""
import sys
from pathlib import Path
import numpy as np
import hashlib,json
from PIL import Image
from paths114 import H,R,folder
sys.path.insert(0,str(folder('111')))
from ray111 import carrier_at,NativeAlpha
from trace114 import matrix
def original_alpha(ctx):
    # Reuse already frozen, hash-verified original111 images. These are static
    # texture provenance, not old pose/visibility buffers mixed into113.
    p=folder('111')/'inputs';data=json.loads((p/'ALPHA111.json').read_text(encoding='utf8'));a=NativeAlpha.__new__(NativeAlpha);a.ctx=ctx;a.images={};a.sources={}
    tids=ctx['partMap'][ctx['partMap']>=0]
    for mi in np.unique(ctx['triangles'][tids,3]):
        role=np.unique(ctx['sources'][ctx['triangles'][:,3]==mi,:2],axis=0);assert len(role)==1
        slot,submesh=map(int,role[0]);row=next(v for v in data['images']if v['renderer']==slot and v['submesh']==submesh);f=p/row['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256'];im=np.asarray(Image.open(f).convert('RGBA'))[:,:,3].astype(float)/255;assert list(im.shape[::-1])==list(map(int,ctx['materials'][mi,0,1:3]));a.images[int(mi)]=im;a.sources[int(mi)]=row
    return a
def mapped(ctx,reg,origin):
    c=dict(ctx);c['world']=c['world4'][:,:3];c['rest']=c['rest4'][:,:3];c['triOwners']=c['owners'];c['maps']={}
    head=matrix(c['transforms']['headMatrix']);local=c['world4']@np.linalg.inv(head).T
    px={int(v['owner']):np.asarray(v['x'])for v in reg['projection']};py={int(v['owner']):np.asarray(v['y'])for v in reg['projection']}
    for eye,hom in zip(c['transforms']['eyeCentres'],c['transforms']['authoredToHead']):
        owner=round(eye[3]);q=np.c_[local@px[owner],local@py[owner],np.ones(len(local)),np.zeros(len(local))]@matrix(hom).T;c['maps'][owner]=q[:,:2]/q[:,2,None]-origin
    return c
class Face114:
    def __init__(self,ctx,mask):
        self.c=ctx;self.mask=np.asarray(mask,np.uint32);self.alpha=original_alpha(ctx);self.tids=np.where((ctx['sources'][:,0]==1)&(ctx['sources'][:,1]==3))[0];self.ids=ctx['triangles'][self.tids,:3];self.xy=ctx['physicalXY'][self.ids];self.z=ctx['depth'][self.ids];self.w=ctx['physicalW'][self.ids];self.mi=ctx['triangles'][self.tids,3];a=np.stack([self.xy[:,1]-self.xy[:,0],self.xy[:,2]-self.xy[:,0]],axis=2);self.det=np.linalg.det(a);self.good=abs(self.det)>1e-12;self.inv=np.zeros_like(a);self.inv[self.good]=np.linalg.inv(a[self.good])
    def query(self,points,depth,owner,expose=True,limit=.012):
        points=np.asarray(points);depth=np.asarray(depth);out=[];c=self.c
        for p,z in zip(points,depth):
            ab=np.einsum('tij,tj->ti',self.inv,p-self.xy[:,0]);b=np.c_[1-ab.sum(1),ab];weights=b/self.w;weights/=weights.sum(1)[:,None];zz=(weights*self.z).sum(1);good=self.good&(b.min(1)>=-1e-7)&(zz<z-3e-5)&(self.w.min(1)>0)
            cull=c['materials'][self.mi,1,2];sign=np.where(self.det>0,1,-1);good&=~(((cull==2)&(sign!=1))|((cull==1)&(sign!= -1)))
            hits=[]
            for i in np.where(good)[0]:
                ti=int(self.tids[i]);primitive=int(c['sources'][ti,2]);own=bool(int(self.mask[primitive-1])&(1<<owner));gap=float(z-zz[i]);exempt=expose and own and gap<=limit;uv=weights[i]@c['uv'][self.ids[i]];alpha=self.alpha.bounds(int(self.mi[i]),[uv])[0];hits.append({'triangle':ti,'sourcePrimitive':primitive,'material':int(self.mi[i]),'sourceUV':uv.tolist(),'depth':float(zz[i]),'depthGapMetres':gap,'unilateralRingComponent':own,'exempt113':exempt,'alphaBounds':alpha.tolist()})
            hits.sort(key=lambda h:h['depth']);lo=hi=1.
            for h in hits:
                if not h['exempt113']:lo*=1-h['alphaBounds'][1];hi*=1-h['alphaBounds'][0]
            out.append({'faceInterval':[lo,hi],'hits':hits})
        return out
def carriers(ctx,owner,part,points):
    allhits=carrier_at(ctx,None,owner,part,points,geometryOnly=True)
    return [sorted(h,key=lambda q:q['depth'])for h in allhits]
