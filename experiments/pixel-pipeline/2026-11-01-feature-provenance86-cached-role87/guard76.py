"""Unmodified76 source-support predicate, copied for portable regression."""
import numpy as np
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
