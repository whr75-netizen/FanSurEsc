"""Source-connected, bounded-unknown shade-area reference; no RGB smoothing.

The reference is piecewise-linear interpolation of STORED native g samples,
not analytic lighting or exact continuous mesh coverage. Unknown geometry is
kept as an area interval, never borrowed from another surface or filled.
"""
import numpy as np
def clip(poly,component,threshold,keepAbove=True):
 if not len(poly):return poly
 result=[]
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  da=a[component]-threshold;db=b[component]-threshold
  ina=da>=0 if keepAbove else da<=0;inb=db>=0 if keepAbove else db<=0
  if ina:result.append(a)
  if ina!=inb:result.append(a+(b-a)*(da/(da-db)))
 return np.asarray(result,float).reshape((-1,3))
def area(poly):
 if len(poly)<3:return 0.
 return float(abs(np.dot(poly[:,0],np.roll(poly[:,1],-1))-np.dot(poly[:,1],np.roll(poly[:,0],-1)))/2)
def in_cell(poly,x,y):
 for axis,value,above in [(0,x,True),(0,x+1,False),(1,y,True),(1,y+1,False)]:poly=clip(poly,axis,value,above)
 return poly
def build_reference(g,valid,sourceFaces,faceVertices,diagonal=0):
 """A guide triangle must have source-local face connectivity, not equal material.

Requiring actual shared source vertices between all three sample faces avoids
interpolating through a front/back switch even inside one mesh/material. This
does not promote a mesh component into an artistic feature ID.
"""
 h,w=g.shape;reference=[];rejected={'missingSource':0,'localConnectionUnproven':0}
 for y in range(h-1):
  for x in range(w-1):
   splits=[[(0,0),(1,0),(1,1)],[(0,0),(1,1),(0,1)]] if diagonal==0 else [[(0,0),(1,0),(0,1)],[(1,0),(1,1),(0,1)]]
   for offsets in splits:
    pts=[(x+dx,y+dy) for dx,dy in offsets]
    if not all(valid[yy,xx] and sourceFaces.get((xx,yy)) in faceVertices for xx,yy in pts):rejected['missingSource']+=1;continue
    faces=[sourceFaces[(xx,yy)] for xx,yy in pts]
    if any(a[0]!=b[0] or not faceVertices[a].intersection(faceVertices[b]) for i,a in enumerate(faces) for b in faces[i+1:]):rejected['localConnectionUnproven']+=1;continue
    reference.append(np.array([[(xx+.5)/2,(yy+.5)/2,float(g[yy,xx])] for xx,yy in pts],float))
 return reference,rejected
def classify(q,mask,reference,threshold=.5):
 """A new label requires a majority even if ALL unobserved area opposes it."""
 bright=np.zeros(mask.shape);known=np.zeros(mask.shape)
 for triangle in reference:
  lo=np.floor(triangle[:,:2].min(0)).astype(int);hi=np.floor(triangle[:,:2].max(0)).astype(int)
  for y in range(max(0,lo[1]),min(len(mask),hi[1]+1)):
   for x in range(max(0,lo[0]),min(mask.shape[1],hi[0]+1)):
    if not mask[y,x]:continue
    p=in_cell(triangle,x,y);known[y,x]+=area(p);bright[y,x]+=area(clip(p,2,threshold))
 assert known.max()<=1+1e-9
 unknown=np.maximum(0,1-known);dark=np.maximum(0,known-bright);out=q.copy();out[mask&(bright>.5)]=1;out[mask&(dark>.5)]=0
 return out,bright,dark,unknown

def both_diagonals(q,mask,g,valid,sourceFaces,faceVertices,threshold=.5):
 """Keep an interval over BOTH linear interpolants; no privileged grid diagonal."""
 guides=[];rejected=[];bs=[];ds=[]
 for diagonal in [0,1]:
  guide,reject=build_reference(g,valid,sourceFaces,faceVertices,diagonal);_,b,d,u=classify(q,mask,guide,threshold);guides.append(guide);rejected.append(reject);bs.append(b);ds.append(d)
 bright=np.minimum(*bs);dark=np.minimum(*ds);unknown=np.maximum(0,1-bright-dark);out=q.copy();out[mask&(bright>.5)]=1;out[mask&(dark>.5)]=0
 return out,bright,dark,unknown,guides,rejected
