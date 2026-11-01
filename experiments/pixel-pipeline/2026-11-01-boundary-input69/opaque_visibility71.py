"""Offline orthographic opaque-triangle visibility. No shader/alpha equivalence.

All evaluated source triangles participate, including never-sampled/back faces.
Screen barycentrics and view depth are affine only for the captured orthographic
projection; perspective inputs fail rather than silently using the wrong model.
"""
import numpy as np

class OpaqueScene:
 def __init__(self,xy,depth,keys,bin_size=4):
  self.xy=np.asarray(xy,float);self.depth=np.asarray(depth,float);self.keys=np.asarray(keys,int);self.bin_size=bin_size
  a=np.stack([self.xy[:,1]-self.xy[:,0],self.xy[:,2]-self.xy[:,0]],axis=2)
  det=np.linalg.det(a);self.valid=np.abs(det)>1e-12
  self.inv=np.zeros_like(a);self.inv[self.valid]=np.linalg.inv(a[self.valid]);self.bins={}
  self.bykey={tuple(k):i for i,k in enumerate(self.keys)}
  for i in np.flatnonzero(self.valid):
   lo=np.floor(self.xy[i].min(0)/bin_size).astype(int);hi=np.floor(self.xy[i].max(0)/bin_size).astype(int)
   for y in range(lo[1],hi[1]+1):
    for x in range(lo[0],hi[0]+1):self.bins.setdefault((x,y),[]).append(int(i))
 def candidates(self,p):
  lo=np.floor(np.min(p,axis=0)/self.bin_size).astype(int);hi=np.floor(np.max(p,axis=0)/self.bin_size).astype(int)
  return np.array(sorted({i for y in range(lo[1],hi[1]+1) for x in range(lo[0],hi[0]+1) for i in self.bins.get((x,y),[])}),int)
 def bary(self,p,ids):
  b=np.einsum('nij,nj->ni',self.inv[ids],np.asarray(p)-self.xy[ids,0]);return np.c_[1-b.sum(1),b]
 def point(self,p):
  ids=self.candidates(np.asarray(p)[None]);b=self.bary(p,ids);ok=(b.min(1)>=-1e-9);ids=ids[ok];b=b[ok]
  return ids,np.einsum('ni,ni->n',b,self.depth[ids])
 def line(self,segment,key,epsilon=1e-6):
  """Return union of t intervals with a strictly nearer opaque triangle.

  No raster midpoint classification: projected triangle entry/exit and affine
  depth crossings partition the entire line. Shared/coplanar faces within the
  explicit numerical epsilon do not occlude one another.
  """
  p=np.asarray(segment,float);source=self.bykey[tuple(key)];ids=self.candidates(p);ids=ids[ids!=source]
  b0=self.bary(p[0],ids);b1=self.bary(p[1],ids);db=b1-b0
  lo=np.zeros(len(ids));hi=np.ones(len(ids));ok=np.ones(len(ids),bool)
  for j in range(3):
   v=b0[:,j];d=db[:,j];nz=np.abs(d)>1e-15;c=np.divide(-v,d,out=np.zeros_like(v),where=nz)
   lo=np.where(d>1e-15,np.maximum(lo,c),lo);hi=np.where(d< -1e-15,np.minimum(hi,c),hi);ok&=nz|(v>=-1e-12)
  sd0=float(self.bary(p[0],[source])[0]@self.depth[source]);sd1=float(self.bary(p[1],[source])[0]@self.depth[source])
  delta0=np.einsum('ni,ni->n',b0,self.depth[ids])-sd0+epsilon
  dd=np.einsum('ni,ni->n',db,self.depth[ids])-(sd1-sd0)
  # Keep delta0+t*dd <0. Solve one extra affine half-space exactly.
  nz=np.abs(dd)>1e-15;cross=np.divide(-delta0,dd,out=np.zeros_like(dd),where=nz)
  hi=np.where(dd>1e-15,np.minimum(hi,cross),hi);lo=np.where(dd< -1e-15,np.maximum(lo,cross),lo);ok&=nz|(delta0<0)
  ok&=(hi>lo+1e-12)&(hi>0)&(lo<1);lo=np.clip(lo,0,1);hi=np.clip(hi,0,1)
  spans=sorted((float(a),float(b),int(i)) for a,b,i in zip(lo[ok],hi[ok],ids[ok]));merged=[]
  for a,b,i in spans:
   if merged and a<=merged[-1][1]+1e-12:merged[-1][1]=max(merged[-1][1],b)
   else:merged.append([a,b])
  blocked=sum(b-a for a,b in merged)
  return {'blockedFraction':min(1.,blocked),'blockedIntervals':merged,'blockers':[{'triangle':i,'key':self.keys[i].tolist(),'t':[a,b]} for a,b,i in spans]}

def from_meshes(meshes,camera):
 P=camera['gpuProjection'].copy()
 if not np.allclose(P[3],[0,0,0,1],atol=1e-12):raise ValueError('Only captured orthographic projection supported')
 P[0]+=float(camera['nativeShift'][0])*P[3];P[1]+=float(camera['nativeShift'][1])*P[3]
 xy=[];depth=[];keys=[];clip=[]
 for m in meshes:
  world=np.c_[m['vertices'],np.ones(len(m['vertices']))]@m['matrix'].T;view=world@camera['view'].T;c=view@P.T
  screen=np.c_[(c[:,0]/c[:,3]*.5+.5)*960,(.5-c[:,1]/c[:,3]*.5)*544]
  for sm,sub in enumerate(m['submeshes']):
   ix=sub['indices'];xy.extend(screen[ix]);depth.extend(-view[ix,2]);keys.extend((m['index'],sm,pi) for pi in range(len(ix)));clip.extend(c[ix,2]/c[ix,3])
 if np.any(np.asarray(clip)<0) or np.any(np.asarray(clip)>1):raise ValueError('Near/far clipped triangles require explicit clipping; no silent omission')
 return OpaqueScene(xy,depth,keys)
