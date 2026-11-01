"""Source feature-local coverage cache + continuous placement, no screen history.

One local lattice belongs to a feature group (both eyes here), not to screen
pixels. Rebuild on actual shape/projection change, never on pure translation.
Palette index, part identity and local support are stored together. Visibility
is a separate per-fragment input, not a whole-cell any(front) veto.
"""
from dataclasses import dataclass
import numpy as np

class Unsupported(ValueError):pass

def project(H,p):
 p=np.asarray(p,float);q=np.concatenate([p,np.ones(p.shape[:-1]+(1,))],-1)@np.asarray(H,float).T
 if np.any(abs(q[...,2])<1e-10):raise Unsupported('feature crosses projective horizon')
 return q[...,:2]/q[...,2,None]

def clip(poly,axis,bound,greater):
 if not len(poly):return poly
 out=[]
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  ina=(a[axis]>=bound)if greater else(a[axis]<=bound);inb=(b[axis]>=bound)if greater else(b[axis]<=bound)
  if ina:out.append(a)
  if ina!=inb:out.append(a+(b-a)*((bound-a[axis])/(b[axis]-a[axis])))
 return np.array(out,float).reshape(-1,2)

def area(poly):
 return 0. if len(poly)<3 else float(abs(np.sum(poly[:,0]*np.roll(poly[:,1],-1)-poly[:,1]*np.roll(poly[:,0],-1)))*.5)

def cell_area(poly,x,y):
 q=poly
 for axis,bound,g in [(0,x-.5,True),(0,x+.5,False),(1,y-.5,True),(1,y+.5,False)]:q=clip(q,axis,bound,g)
 return area(q)

@dataclass(frozen=True)
class SourcePixel:
 x:int;y:int;owner:int;part:int;palette:int
 def polygon(self):return np.array([[self.x,self.y],[self.x+1,self.y],[self.x+1,self.y+1],[self.x,self.y+1]],float)

class FeatureCache:
 """Owned by one renderer/view; no static model-global cache or borrowed state."""
 def __init__(self):self.scope=None;self.vertices=None;self.rows=[];self.disposed=False;self.builds=0
 def update(self,source,H,scope,state_supported=True):
  if self.disposed:raise RuntimeError('disposed feature owner')
  if not state_supported:self.invalidate();raise Unsupported('no source key-form for this state')
  if not source:raise Unsupported('empty feature source')
  owners=sorted({p.owner for p in source});anchors={}
  for owner in owners:
   xy=np.array([[p.x,p.y]for p in source if p.owner==owner]);anchors[owner]=np.floor((xy.min(0)+xy.max(0))/2)+.5
  anchor=np.mean([project(H[o],anchors[o])for o in owners],0)
  polys=[project(H[p.owner],p.polygon())-anchor for p in source];vertices=np.concatenate(polys)
  # Arithmetic tolerance derived from float32 projection coordinate magnitude;
  # this is not a style/deformation dead zone or temporal hysteresis parameter.
  tolerance=64*np.finfo(np.float32).eps*max(1.,max(abs(np.concatenate([p+anchor for p in polys])).ravel()))
  residual=float('inf')if self.vertices is None or self.vertices.shape!=vertices.shape else float(abs(vertices-self.vertices).max())
  signature=(scope,tuple((p.x,p.y,p.owner,p.part,p.palette)for p in source))
  rebuild=self.scope!=signature or residual>tolerance
  if rebuild:
   candidates={}
   for i,(src,poly)in enumerate(zip(source,polys)):
    lo=np.floor(poly.min(0)+.5).astype(int);hi=np.ceil(poly.max(0)+.5).astype(int)
    for y in range(lo[1],hi[1]):
     for x in range(lo[0],hi[0]):
      a=cell_area(poly,x,y)
      if a>1e-10:candidates.setdefault((x,y),[]).append((i,a))
   rows=[];uncertain=[]
   for (x,y),hits in sorted(candidates.items(),key=lambda q:(q[0][1],q[0][0])):
    by={}
    for i,a in hits:by[source[i].owner,source[i].part]=by.get((source[i].owner,source[i].part),0)+a
    if len({key[0]for key in by})>1:uncertain.append((x,y,'different feature owners overlap'));continue
    total=sum(by.values());bg=max(0.,1-total);rank=sorted(by,key=lambda key:(-by[key],key))
    if by[rank[0]]<=bg+1e-10:continue
    if len(rank)>1 and abs(by[rank[0]]-by[rank[1]])<1e-10:uncertain.append((x,y,'equal part coverage'));continue
    owner,part=rank[0];i,a=min(((i,a)for i,a in hits if(source[i].owner,source[i].part)==(owner,part)),key=lambda q:(-q[1],source[q[0]].y,source[q[0]].x))
    rows.append({'xy':[int(x),int(y)],'owner':owner,'part':part,'palette':source[i].palette,'sourceIndex':i,'foregroundArea':total,'partArea':by[owner,part]})
   if uncertain:raise Unsupported('ambiguous local occupancy: '+str(uncertain))
   present={(p.owner,p.part)for p in source};got={(p['owner'],p['part'])for p in rows}
   if got!=present:raise Unsupported('a source part is unrepresentable in this canonical projection: '+str(present-got))
   self.scope=signature;self.vertices=vertices.copy();self.rows=rows;self.builds+=1
  return {'anchor':anchor.copy(),'rows':self.rows,'rebuild':bool(rebuild),'deformationResidual':residual,'numericTolerance':float(tolerance),'builds':self.builds}
 def invalidate(self):self.scope=None;self.vertices=None;self.rows=[]
 def dispose(self):self.invalidate();self.disposed=True

def raster(rows,anchor,palette,origin,size,scale=2,visibility=None):
 """Only final output samples are integer. The feature anchor stays continuous.

 `visibility` returns (fraction,reason) at a continuous *head top-left* point.
 RGB is always a literal P[index]. Alpha/coverage is returned independently.
 """
 origin=np.asarray(origin,float);anchor=np.asarray(anchor,float);w,h=size;out=np.zeros((h,w,4),np.float32);identity=np.zeros((h,w,4),np.float32);cover=np.zeros((h,w,4),np.float32);lookup={tuple(r['xy']):r for r in rows}
 for y in range(h):
  for x in range(w):
   p=origin+(np.array([x,y])+.5)/scale;k=tuple(np.floor(p-anchor+.5).astype(int));row=lookup.get(k)
   if row is None:continue
   fraction,reason=(1.,0)if visibility is None else visibility(p,row)
   identity[y,x]=[row['owner'],row['part'],row['palette']+1,row['sourceIndex']+1];cover[y,x]=[fraction,reason,k[0],k[1]]
   if fraction>0:out[y,x]=[*palette[row['palette']],fraction]
 return out,identity,cover

def fragment_visibility(metas,depth,owner):
 """Partial alpha remains fractional. This does not invent missing observations.

 source0 skin/actual lid,4 hair,5 brow,6 body. Body is binary in existing source.
 Native S3 is reported as an internal part/occluder; never relocated to rescue
 source iris. The function does not claim to redesign its missing key-form.
 """
 v=1.;why=0
 for source in [0,3,4,5,6]:
  m=metas[source]
  if m[0]>0 and m[1]>.5 and m[3]>1e-6 and m[0]<depth:
   a=1. if source==6 else float(np.clip(m[3],0,1));v*=1-a;why|=1<<source
 return v,why
