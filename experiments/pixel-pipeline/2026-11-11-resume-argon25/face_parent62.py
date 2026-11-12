"""Face-outline decoration is below same-frame visible eye children, not below all skin."""
import numpy as np
from review_hull60 import oracle_hull
def child_gate(visible,domain,native_owner,cell):
 v=np.asarray(visible,np.float32);k=np.rint(v[:,:,0]);role=np.where(k==1,5,np.where((k>=2)&(k<=4),2,np.where((k==5)|(k==7),7,0)))
 return np.isfinite(v).all(2)&(v[:,:,0]==k)&(role>0)&(v[:,:,1]>0)&(v[:,:,2]>0)&(domain[:,:,0]>=.5)&(cell[:,:,2]==1)&(native_owner[:,:,0]==role)
def resolve(line,proof,before,meta,world,cell,inside,q,offset,ink,triangles,visible,domain,native_owner):
 # Keep actual floating UVs; repeat/clamp sampling belongs to the producer.
 expected,gate=oracle_hull(line,proof,before,meta,world,cell,inside,q,offset,ink,triangles,uv_bounds=False)
 blocked=(gate[:,:,3]==1)&child_gate(visible,domain,native_owner,cell);expected[blocked]=before[blocked];gate[blocked,3]=0
 return expected,gate,blocked
