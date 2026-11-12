import json,numpy as np
from pathlib import Path
from selected_light84 import known,barycentric_uv
def main():
 cell=np.array([[20.,30,1,1]]);owner=np.array([[4.,1,8,0]]);source=np.array([[8.,4,1,23]]);domain=np.zeros((1,4));meta=np.array([[8.,4,1,23]]);uv=np.array([[.25,.75,0,0]]);head=uv.copy();head[:,2]=.5;main=head.copy();cls=np.array([[.5,.51,8,1]])
 def run(*args):return bool(known(*args)[0])
 args=[cell,owner,source,domain,meta,uv,head,main,cls];assert run(*args);checks=1
 for i,j in [(0,2),(1,0),(2,3),(3,0),(4,1),(5,0),(6,1),(7,0),(8,0)]:
  copy=[x.copy()for x in args];copy[i][0,j]+=1;assert not run(*copy);checks+=1
 for flip in [1,-1]:
  for rotate in range(4):
   a=np.array([[0.,0],[2,0],[0,2]]);p=np.array([.5,.25]);m=np.linalg.matrix_power(np.array([[0.,-1],[1,0]]),rotate)@np.diag([flip,1]);b=barycentric_uv(a@m.T,p@m.T);assert np.allclose(b,[.625,.25,.125]);checks+=1
 out={'CPUChecks':checks,'wrongAddressOrOwnershipRejected':True,'D4Barycentric':True,'noLightingOrQInferred':True};(Path(__file__).resolve().parent/'face84/CPU_CONTRACT84.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=='__main__':main()
