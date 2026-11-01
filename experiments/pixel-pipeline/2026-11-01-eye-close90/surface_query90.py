"""Actual query ray against stored current triangles; no state/colour heuristics."""
import numpy as np
class ProjectedSurface:
 def __init__(self,world_vertices,uv,indices,view,projection,size):
  self.tri=np.asarray(indices);self.uv=np.asarray(uv);self.world=np.asarray(world_vertices);clip=self.world@(projection@view).T;self.w=clip[:,3]
  self.xy=np.c_[(clip[:,0]/clip[:,3]*.5+.5)*size[0],(.5-clip[:,1]/clip[:,3]*.5)*size[1]];self.depth=-(self.world@view.T)[:,2]
  t=self.xy[self.tri];self.lo=t.min(1);self.hi=t.max(1);self.sign=np.sign(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]))
 def hits(self,point):
  p=np.asarray(point);possible=np.where((self.lo<=p+1e-9).all(1)&(self.hi>=p-1e-9).all(1)&(self.w[self.tri]>0).all(1))[0];ix=self.tri[possible];t=self.xy[ix];u=t[:,1]-t[:,0];v=t[:,2]-t[:,0];d=p-t[:,0];den=u[:,0]*v[:,1]-u[:,1]*v[:,0];safe=np.where(abs(den)>1e-12,den,1);b=(d[:,0]*v[:,1]-d[:,1]*v[:,0])/safe;c=(u[:,0]*d[:,1]-u[:,1]*d[:,0])/safe;weights=np.c_[1-b-c,b,c];valid=(abs(den)>1e-12)&(weights.min(1)>=-1e-7);result=[]
  for j,w in zip(possible[valid],weights[valid]):
   vertex=self.tri[j];w=w/self.w[vertex];w/=w.sum();result.append({'primitive':int(j+1),'vertices':vertex.tolist(),'barycentric':w.tolist(),'uv':(w@self.uv[vertex]).tolist(),'depth':float(w@self.depth[vertex]),'projectedWinding':int(self.sign[j])})
  return sorted(result,key=lambda h:h['depth'])

def visibility_bounds(hits,point_depth,alpha_bounds,front_winding=None,cull_back=False,depth_tolerance=3e-5):
 """Return a bounded transmittance; an unavailable alpha never means clear."""
 low=high=1.;used=[]
 for hit in hits:
  if hit['depth']>=point_depth-depth_tolerance:continue
  if cull_back and hit['projectedWinding']!=front_winding:continue
  bounds=alpha_bounds.get(hit['queryKey'])
  if bounds is None:lo,hi=0.,1.
  else:lo,hi=bounds
  assert 0<=lo<=hi<=1
  low*=1-hi;high*=1-lo;used.append({**hit,'alphaBounds':[lo,hi]})
 return {'lower':low,'upper':high,'resolved':abs(high-low)<1e-9,'hits':used}

def choose_joint_bounds(alpha_lower,alpha_upper,depth,labels):
 """Conservative joint occupancy. Unknown contributes an interval, not clear.

 A LUT lookup is allowed only when one label provably wins. Background is0;
 no Close value, minimum cell count, RGB or artist weight enters this decision.
 """
 lo=np.asarray(alpha_lower,float);hi=np.asarray(alpha_upper,float);z=np.asarray(depth,float);assert lo.shape==hi.shape==z.shape and lo.ndim==2;assert ((lo>=0)&(lo<=hi)&(hi<=1)).all()
 order=np.argsort(z,axis=0,kind='stable');Tlo=np.ones(lo.shape[1]);Thi=Tlo.copy();L=np.zeros(len(labels)+1);U=L.copy()
 for rank in range(len(labels)):
  p=order[rank];a=lo[p,np.arange(lo.shape[1])];b=hi[p,np.arange(lo.shape[1])]
  for i in range(len(labels)):
   take=p==i;L[i]+=(Tlo[take]*a[take]).sum();U[i]+=(Thi[take]*b[take]).sum()
  Tlo*=1-b;Thi*=1-a
 L[-1]=Tlo.sum();U[-1]=Thi.sum();allLabels=list(labels)+[0];possible=[allLabels[i]for i in range(len(allLabels))if U[i]>0 and U[i]>=L.max()-1e-10];unique=[]
 for i in range(len(allLabels)):
  if L[i]>np.max(np.delete(U,i),initial=0)+1e-10:unique.append(allLabels[i])
 return {'winner':unique[0]if len(unique)==1 else None,'possibleLabels':possible,'massBounds':{str(label):[float(L[i]),float(U[i])]for i,label in enumerate(allLabels)},'paletteLookupAllowed':len(unique)==1 and unique[0]!=0}
