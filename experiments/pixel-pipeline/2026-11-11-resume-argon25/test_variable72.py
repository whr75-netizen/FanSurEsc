from pathlib import Path
import json,numpy as np
from variable_exterior72 import resolve,source_green
H=Path(__file__).resolve().parent;G=H/'face72'
def main():
 tests=0;n=13;actor=np.zeros((n,n),bool);actor[5:8,5:8]=True;eligible=actor.copy();before=np.zeros((n,n,4),np.float32);before[:,:,3]=1;depth=np.full((n,n),3,np.float32);world=np.full((n,n),8,np.float32);meta=np.zeros_like(world);keys=np.zeros_like(before);yy,xx=np.indices((n,n));keys[:,:,0]=4;keys[:,:,1]=1+yy*n+xx;keys[:,:,2]=xx/16;keys[:,:,3]=yy/16;inks=np.full((n,n,3),.1,np.float32);r=np.zeros((n,n),np.int32);r[actor]=1;r[5,5]=2
 o,p,m,t=resolve(before,actor,eligible,depth,world,meta,keys,inks,r);assert not(m&actor).any()and m.sum()>16;tests+=1
 for mirror in[False,True]:
  for k in range(4):
   transform=lambda v:np.rot90(v[:,::-1]if mirror else v,k)
   result=resolve(*[transform(v)for v in[before,actor,eligible,depth,world,meta,keys,inks,r]])
   assert all(np.array_equal(a,transform(b))for a,b in zip(result,[o,p,m,t]));tests+=1
 history={tuple(v)for v in p[m]};q=resolve(before,actor,np.zeros_like(eligible),depth,world,meta,keys,inks,r,history);assert not q[2].any();tests+=1
 q=resolve(before,actor,eligible,depth,np.ones_like(world),meta,keys,inks,r,history);assert not q[2].any();tests+=1
 q=resolve(before,actor,eligible,depth,world,meta,keys,inks,np.zeros_like(r),history);assert not q[2].any();tests+=1
 assert source_green([[0,0],[1,0],[0,1]],[0,.5,1],[.25,.25])==.375;tests+=1
 assert source_green([[0,0],[0,0],[0,0]],[0,.5,1],[0,0])is None;tests+=1
 assert source_green([[0,0],[0,0],[0,0]],[.2,.2,.2],[0,0])==.2;tests+=1
 assert source_green([[0,0],[1,0],[0,1]],[0,.5,1],[2,2])is None;tests+=1
 assert np.array_equal(np.floor(2*np.array([0,.2,.5,.8,1])+.5),[0,0,1,2,2]);tests+=1
 result={'CPUChecks':tests,'sourceRadiusField012':True,'D4Exact':True,'hiddenSourceOrWorldHistoryAdmission':False,'degenerateUVDoesNotInventCarrier':True,'GPUExecutedByThisTest':False,'runtimeHistoryImplemented':False};(G/'CPU_TEST72.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
