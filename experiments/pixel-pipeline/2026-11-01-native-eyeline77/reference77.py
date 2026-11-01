import numpy as np

def components(v,tri,centres,axesY):
 parent=list(range(len(tri)));seen={}
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,t in enumerate(tri):
  for x in t:
   if int(x)in seen:parent[root(i)]=root(seen[int(x)])
   else:seen[int(x)]=i
 groups={}
 for i in range(len(tri)):groups.setdefault(root(i),[]).append(i)
 out=[];ids=np.full(len(tri),-1,int)
 for i,indices in enumerate(groups.values()):
  points=v[tri[indices]];areas=np.linalg.norm(np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]),axis=1)/2;mean=(points.mean(1)*areas[:,None]).sum(0)/areas.sum();eye=int(np.argmin([np.linalg.norm(mean-np.array(c[:3]))for c in centres]));vertical=-np.dot(mean-np.array(centres[eye][:3]),axesY[eye][:3])/axesY[eye][3]
  out.append({'component':i,'eyeIndex':eye,'eyeId':int(centres[eye][3]),'part':'upper'if vertical<0 else'lower','meanRest':mean.tolist(),'meanNormalizedV':float(vertical),'primitives':indices});ids[indices]=i
 return out,ids

def valid(m,p,sid):return(m[...,0]>0)&(m[...,1]>.5)&(m[...,3]>1e-6)&(np.rint(m[...,2])==sid)&(p[...,3]>.5)

def cov(m):return(m[...,0]>0)&(m[...,1]>.5)&(m[...,3]>1e-6)

def iris_allocation(c):
 ir=np.float32(np.float32(c[...,2]+c[...,3])+c[...,4]);area=np.float32(0)
 for v in ir.flat:area=np.float32(area+np.float32(v/16))
 k=int(np.floor(np.float32(area+.5)));order=[];mask=np.zeros(ir.shape,bool)
 for y,x in np.argwhere(ir>0):order.append((float(np.float32(max(c[y,x,1],c[y,x,5],c[y,x,6])-ir[y,x])),float(c[y,x,8]),float(c[y,x,9]),int(y),int(x)))
 for r in sorted(order)[:k]:mask[r[-2],r[-1]]=True
 return mask

def supported(old,owner,domain,samples,points,composed_owner=None):
 role=int(round(owner[0]));source={2:2,5:1,7:3}.get(role)
 if source is None or old[3]<=0 or owner[2]<=0 or(role in (2,5)and domain[0]<=.5):return False,0,0
 def cov(m):return m[0]>0 and m[1]>.5 and m[3]>1e-6
 if composed_owner is None:composed_owner=[owner[0],1,0,0]
 if role!=7 and round(composed_owner[0])!=role:return False,0,0
 total=0.;sid=0;best=1e30
 for i,m in enumerate(samples[source]):
  if not cov(m)or points[source][i,3]<=.5 or not .5<m[2]<2.5:continue
  if role!=7 and round(m[2])!=round(composed_owner[1]):continue
  visible=float(np.clip(m[3],0,1))
  for other in ([2,3]if source==1 else [3]if source==2 else []):
   z=samples[other][i]
   if cov(z)and z[0]<m[0]:visible*=1-float(np.clip(z[3],0,1))
  for s in (0,4,5,6):
   z=samples[s][i]
   if cov(z)and z[0]<m[0]:visible=0 if s==6 else visible*(1-float(np.clip(z[3],0,1)))
  if visible<=0:continue
  total+=visible;d=abs(float(m[0]-owner[2]))
  if d<best:best=d;sid=round(float(m[2]))
 return total>0 and sid>0,sid,total
