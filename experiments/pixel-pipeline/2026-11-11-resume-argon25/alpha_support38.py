"""Exact native alpha-support identity, separate from colour family/owner.

Positive source texels form four-neighbour material-support components. Linear
filtering may sample several components; such a footprint is ambiguous, never
silently merged. Source opacity stays continuous metadata, not an opaque flag.
No colour threshold, skeleton, minimum area, or semantic label is introduced.
"""
from collections import deque
import hashlib
import numpy as np

class AlphaSupport:
 def __init__(self,alpha,repeat=True):
  a=np.asarray(alpha)
  if a.ndim!=2 or a.dtype!=np.uint8:raise ValueError('original uint8 alpha plane required')
  self.alpha=a.copy();self.h,self.w=a.shape;self.repeat=repeat;self.labels=np.zeros(a.shape,np.uint32);self.regions=[]
  for y,x in np.argwhere(a>0):
   if self.labels[y,x]:continue
   identity=len(self.regions)+1;todo=deque([(int(x),int(y))]);self.labels[y,x]=identity;count=0
   while todo:
    xx,yy=todo.popleft();count+=1
    for nx,ny in [(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)]:
     if repeat:nx%=self.w;ny%=self.h
     if 0<=nx<self.w and 0<=ny<self.h and a[ny,nx]>0 and not self.labels[ny,nx]:self.labels[ny,nx]=identity;todo.append((nx,ny))
   self.regions.append({'id':identity,'firstSourceTexel':[int(x),int(y)],'sourceTexels':count})
  self.alphaSHA256=hashlib.sha256(a.tobytes()).hexdigest()
 def sample(self,uv):
  # Input UV uses original image's top-left row orientation. Convert only at
  # the verified Unity import adapter; the support resolver does no V guessing.
  u,v=map(float,uv)
  if not np.isfinite([u,v]).all():raise ValueError('finite source UV required')
  p=np.array([u*self.w-.5,v*self.h-.5]);lo=np.floor(p).astype(int);t=p-lo;ids=set();footprintIds=set();alpha=0.;weights=[];envelope=[]
  for dy in range(2):
   for dx in range(2):
    weight=(t[0]if dx else 1-t[0])*(t[1]if dy else 1-t[1]);x,y=int(lo[0]+dx),int(lo[1]+dy)
    if self.repeat:x%=self.w;y%=self.h
    else:x=max(0,min(x,self.w-1));y=max(0,min(y,self.h-1))
    opacity=float(self.alpha[y,x])/255;identity=int(self.labels[y,x]);alpha+=weight*opacity;envelope.append(float(np.float32(opacity)))
    if opacity>0:footprintIds.add(identity)
    if weight>0 and opacity>0:ids.add(identity);weights.append({'id':identity,'texel':[x,y],'weight':float(weight),'sourceAlpha':opacity})
  return {'alpha':alpha,'supportId':next(iter(ids))if len(ids)==1 else 0,'ambiguous':len(ids)>1,'sourceIds':sorted(ids),'samples':weights,'footprintSupportId':next(iter(footprintIds))if len(footprintIds)==1 else 0,'footprintSourceIds':sorted(footprintIds),'alphaEnvelope':[min(envelope),max(envelope)]}
