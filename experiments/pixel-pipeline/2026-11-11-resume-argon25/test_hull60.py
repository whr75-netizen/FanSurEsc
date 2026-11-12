"""Positive/negative source contracts, including UV endpoints and real occlusion."""
from pathlib import Path
import json,numpy as np
from review_hull60 import oracle_hull
def main():
 ink=np.array([.061,.009,.014],np.float32);before=np.array([[[.8,.6,.4,1]]],np.float32);line=np.array([[[*ink,1]]],np.float32);proof=np.array([[[2,0,1,1]]],np.float32);meta=np.array([[[3,4,0,0]]],np.float32);world=np.array([[[3,0,0,0]]],np.float32);cell=np.array([[[4,7,1,0]]],np.float32);q=np.array([[[4,7]]]);inside=np.ones((1,1),bool)
 def run(l=line,p=proof,m=meta,w=world,c=cell,i=inside):return oracle_hull(l,p,before,m,w,c,i,q,0,ink,4232)
 out,gate=run();assert gate[0,0].tolist()==[1,1,1,1]and np.array_equal(out[0,0,:3],ink)
 count=1
 for primitive in[0,4233,1.5]:
  p=proof.copy();p[0,0,3]=primitive;out,g=run(p=p);assert g[0,0,0]==0 and np.array_equal(out,before);count+=1
 for uv in[[-.01,1],[0,1.01],[np.nan,1]]:
  p=proof.copy();p[0,0,1:3]=uv;out,g=run(p=p);assert g[0,0,3]!=1 and np.array_equal(out,before);count+=1
 p=proof.copy();p[0,0,3]=4232;out,g=run(p=p);assert g[0,0,3]==1;count+=1
 for d in[1.9,0]:
  w=world.copy();w[0,0,0]=d;out,g=run(w=w);assert g[0,0,2]==0 and np.array_equal(out,before);count+=1
 m=meta.copy();m[0,0,0]=1.9;out,g=run(m=m);assert g[0,0,1]==0 and np.array_equal(out,before);count+=1
 c=cell.copy();c[0,0,0]=5;out,g=run(c=c);assert g[0,0,3]==-1 and np.array_equal(out,before);count+=1
 l=line.copy();l[0,0,3]=.5;out,g=run(l=l);assert g[0,0,0]==0 and np.array_equal(out,before);count+=1
 p=proof.copy();p[0,0,0]=np.inf;out,g=run(p=p);assert g[0,0,3]==-1 and np.array_equal(out,before);count+=1
 data={'CPUContractCases':count,'positiveUVEndpointsAccepted':True,'sourcePrimitiveRangeChecked':True,'partialAlphaNotPromotedOpaque':True,'currentOcclusionOverridesSource':True,'invalidReceiptNeverChangesRGB':True,'GPUExecuted':False};p=Path(__file__).resolve().parent/'face60/CPU_CONTRACT60.json';p.write_text(json.dumps(data,indent=2));print(json.dumps(data))
if __name__=='__main__':main()
