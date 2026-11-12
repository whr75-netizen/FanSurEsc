"""Feature-local whole-curve quantization; no screen colour/owner history.

Input is a current registered connected surface's projected vertices and its
actual silhouette edge set. A stable source-vertex barycentre defines one
continuous anchor. Rasterization happens relative to it; only the anchor moves
on the destination integer lattice. Rotation/deformation still change the
current local curve. Depth/alpha/occlusion are a separate later contract.
"""
import itertools,math,numpy as np

def localize(points):
 p=np.asarray(points,float)
 if p.ndim!=2 or p.shape[1]!=2 or not len(p)or not np.isfinite(p).all():raise ValueError('finite current Nx2 source points')
 # Subtract a reference before taking the barycentre. The choice does not
 # change the mathematical centre and cancels a uniform floating translation.
 d=p-p[0];centre=np.array([math.fsum(d[:,i])/len(p)for i in range(2)]);return p[0]+centre,d-centre

def anchor_candidates(anchor):
 result=[]
 for x in np.asarray(anchor,float):
  lo=math.floor(x);fraction=x-lo
  result.append([lo,lo+1]if fraction==.5 else[math.floor(x+.5)])
 # Exact half ties stay explicit alternatives. Do not draw their union or
 # claim an arbitrary first-frame unique artistic result.
 return [np.asarray(p,int)for p in itertools.product(*result)]

def intersects(a,b,r0,r1,cell):
 """Exact piecewise-quadratic swept-disc/closed cell intersection in 2D.

 Radius varies linearly along the segment. Splits are only at the four cell
 boundary crossings, so at most six intervals; no iterative search or GPU BVH.
 A zero radius is the limiting continuous centreline, not a new source colour.
 """
 a=np.asarray(a,float)-cell;v=np.asarray(b,float)-cell-a
 if not np.isfinite(np.r_[a,v,r0,r1]).all()or min(r0,r1)<0:raise ValueError('finite nonnegative curve footprint')
 cuts=[0.,1.]
 for axis in range(2):
  if v[axis]!=0:
   for edge in[-.5,.5]:
    t=(edge-a[axis])/v[axis]
    if 0<t<1:cuts.append(float(t))
 cuts=sorted(set(cuts));dr=r1-r0;best=math.inf
 for lo,hi in zip(cuts,cuts[1:]):
  mid=(lo+hi)*.5;c=np.zeros(2);d=np.zeros(2)
  for axis in range(2):
   p=a[axis]+mid*v[axis]
   if p<-.5:c[axis]=a[axis]+.5;d[axis]=v[axis]
   elif p>.5:c[axis]=a[axis]-.5;d[axis]=v[axis]
  aa=d@d-dr*dr;bb=2*(c@d-r0*dr);cc=c@c-r0*r0;ts=[lo,hi]
  if aa>0:ts.append(min(hi,max(lo,-bb/(2*aa))))
  best=min(best,*(aa*t*t+bb*t+cc for t in ts))
 return best<=0

def raster(local,edges,radii):
 p=np.asarray(local,float);edges=np.asarray(edges,int);r=np.asarray(radii,float)
 if edges.ndim!=2 or edges.shape[1]!=2 or r.shape!=(len(p),)or len(edges)>2048 or(len(edges)and (edges.min()<0 or edges.max()>=len(p)))or(r<0).any()or(r>4).any():raise ValueError('bounded registered curve/radius ABI')
 cells={}
 for eid,(ia,ib)in enumerate(edges):
  a,b=p[ia],p[ib];radius=max(r[ia],r[ib]);low=np.ceil(np.minimum(a,b)-radius-.5).astype(int);high=np.floor(np.maximum(a,b)+radius+.5).astype(int)
  if np.prod(np.maximum(0,high-low+1))>4096:raise ValueError('declared per-edge CPU footprint budget')
  for y in range(low[1],high[1]+1):
   for x in range(low[0],high[0]+1):
    if intersects(a,b,r[ia],r[ib],np.array([x,y])):cells.setdefault((x,y),[]).append(eid)
 return cells
