"""Source-local previous owner preference, never cached screen colour."""
import numpy as np
def project(uv,xy,at):
 uv=np.asarray(uv,np.float64);xy=np.asarray(xy,np.float64);at=np.asarray(at,np.float64)
 matrix=np.stack([uv[1]-uv[0],uv[2]-uv[0]],1)
 if not np.isfinite(matrix).all()or np.linalg.det(matrix)==0:return None
 v,w=np.linalg.solve(matrix,at-uv[0]);bary=np.array([1-v-w,v,w])
 if not np.isfinite(bary).all()or(bary<0).any()or(bary>1).any():return None
 return bary@xy

def preference(source_q,target_q,key,tri_uv,current_xy,previous_xy,old_owner,old_origin,role):
 if key[0]!=role:return False
 p=int(key[1])-1
 if p<0 or p>=len(tri_uv):return False
 now=project(tri_uv[p],current_xy[p],key[2:]);old=project(tri_uv[p],previous_xy[p],key[2:])
 if now is None or old is None:return False
 wanted=old+(np.asarray(target_q)-now);shift=wanted+.5
 if not np.isfinite(shift).all()or(np.mod(shift,1)==0).any():return False
 cell=np.floor(shift).astype(int)-old_origin;x,y=cell;h,w=old_owner.shape[:2]
 if x<0 or x>=w or y<0 or y>=h:return False
 previous=old_owner[y,x]
 if not np.isfinite(previous).all()or previous[0]!=100+role or previous[1]!=p+1:return False
 carried=project(tri_uv[p],current_xy[p],previous[2:])
 return carried is not None and bool((abs(carried-source_q)<.5).all())

class Scope:
 """No GPU owner is silently reused across model/view/generation/frame changes."""
 def __init__(self):self.key=None;self.frame=None
 def accept(self,key,frame):
  reusable=self.key==key and self.frame is not None and frame==self.frame+1
  self.key=key;self.frame=frame;return reusable
