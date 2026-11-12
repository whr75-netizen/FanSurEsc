"""Positive-area projected native extrusion ribbons, before visibility/style.

Unlike a symmetric radius or one-pixel line, preserve both native displacement
vectors. Exact convex clipping is a CPU oracle; no fixed footprint thickness,
screen RGB history, new pigment or whole-inverted-hull equivalence is assumed.
"""
import numpy as np

def witness(triangle,cell):
 t=np.asarray(triangle,float)-cell;a,b,c=t;ab=b-a;ac=c-a;det=np.cross(ab,ac)
 if det==0:return None
 if(t.min(0)>=.5).any()or(t.max(0)<=-.5).any():return None
 for edge in [ab,c-b,a-c]:
  axis=np.array([-edge[1],edge[0]]);v=t@axis;r=.5*abs(axis).sum()
  if v.min()>=r or v.max()<=-r:return None
 p=t.mean(0)
 if(abs(p)>.5).any():
  d=-a;u=np.cross(d,ac)/det;v=np.cross(ab,d)/det
  if u>=0 and v>=0 and u+v<=1:p=np.zeros(2)
  else:
   found=False
   for a0,b0 in [(a,b),(b,c),(c,a)]:
    lo,hi=0.,1.;d=b0-a0;valid=True
    for axis in range(2):
     if d[axis]==0:
      if abs(a0[axis])>.5:valid=False;break
     else:
      x,y=sorted([(-.5-a0[axis])/d[axis],(.5-a0[axis])/d[axis]]);lo=max(lo,x);hi=min(hi,y)
    if valid and lo<hi:p=a0+d*((lo+hi)*.5);found=True;break
   if not found:return None
 d=p-a;u=np.cross(d,ac)/det;v=np.cross(ab,d)/det
 return {'point':p+cell,'barycentric':np.array([1-u-v,u,v]),'triangleAreaNotCellCoverageArea':abs(float(det))*.5}

def clip_triangle(triangle,cell):
 p=np.asarray(triangle,float).copy();q=np.asarray(cell,float)
 if p.shape!=(3,2)or q.shape!=(2,)or not np.isfinite(np.r_[p.ravel(),q]).all():raise ValueError('finite projected triangle and cell')
 p-=q
 for axis,sign in [(0,1),(0,-1),(1,1),(1,-1)]:
  out=[]
  if not len(p):break
  old=p[-1];do=.5-sign*old[axis]
  for new in p:
   dn=.5-sign*new[axis]
   if(do>=0)!=(dn>=0):out.append(old+(new-old)*(do/(do-dn)))
   if dn>=0:out.append(new)
   old=new;do=dn
  p=np.asarray(out)
 if len(p)<3:return 0.,None
 cross=np.cross(p,np.roll(p,-1,axis=0));area=abs(cross.sum())*.5
 if area==0:return 0.,None
 centre=((p+np.roll(p,-1,axis=0))*cross[:,None]).sum(0)/(3*cross.sum())+q
 return float(area),centre

def footprint(a,b,expanded_a,expanded_b,cell):
 triangles=[np.array([a,b,expanded_b]),np.array([a,expanded_b,expanded_a])];pieces=[clip_triangle(t,cell)for t in triangles];positive=[x for x in pieces if x[0]>0]
 # Sum is not a union-area proof if the offset strip folds. Raster coverage is
 # the union; each returned centroid is an actual point of one current ribbon.
 return {'covered':bool(positive),'pieces':positive,'foldedAreaNotDoubleCountedClaimed':False}

def raster(points,expanded,edges,anchor=np.zeros(2),max_cells=8192):
 p=np.asarray(points,float)-anchor;e=np.asarray(expanded,float)-anchor;edges=np.asarray(edges,int)
 if p.shape!=e.shape or p.ndim!=2 or p.shape[1]!=2 or edges.ndim!=2 or edges.shape[1]!=2 or len(edges)>1024 or not np.isfinite(np.r_[p.ravel(),e.ravel()]).all():raise ValueError('bounded projected source ribbon ABI')
 result={};budget=0
 for eid,(a,b)in enumerate(edges):
  v=np.array([p[a],p[b],e[a],e[b]]);lo=np.ceil(v.min(0)-.5).astype(int);hi=np.floor(v.max(0)+.5).astype(int);budget+=int(np.prod(np.maximum(0,hi-lo+1)))
  if budget>max_cells:raise ValueError('CPU/GPU declared ribbon bounding-box budget exceeded before submit')
  for y in range(lo[1],hi[1]+1):
   for x in range(lo[0],hi[0]+1):
    f=footprint(p[a],p[b],e[a],e[b],np.array([x,y]))
    if f['covered']:result.setdefault((x,y),[]).append((eid,f['pieces']))
 return result,budget
