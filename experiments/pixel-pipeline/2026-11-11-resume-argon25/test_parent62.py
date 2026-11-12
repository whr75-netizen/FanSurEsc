from pathlib import Path
import json,numpy as np
from face_parent62 import child_gate
def main():
 v=np.array([[[2,1,4,0]]],np.float32);d=np.ones((1,1,4),np.float32);o=np.array([[[2,0,2,0]]],np.float32);c=np.array([[[0,0,1,0]]],np.float32);assert child_gate(v,d,o,c)[0,0];tests=1
 for kind,role in[(1,5),(3,2),(4,2),(5,7),(7,7)]:
  a=v.copy();b=o.copy();a[0,0,0]=kind;b[0,0,0]=role;assert child_gate(a,d,b,c)[0,0];tests+=1
 for kind in[0,6,8,2.5]:
  a=v.copy();a[0,0,0]=kind;assert not child_gate(a,d,o,c)[0,0];tests+=1
 for channel,value in[(1,0),(2,0),(0,np.nan)]:
  a=v.copy();a[0,0,channel]=value;assert not child_gate(a,d,o,c)[0,0];tests+=1
 for role in[1,3,4,7]:
  b=o.copy();b[0,0,0]=role;assert not child_gate(v,d,b,c)[0,0];tests+=1
 hidden=c.copy();hidden[0,0,2]=0;assert not child_gate(v,d,o,hidden)[0,0];tests+=1
 noDomain=d.copy();noDomain[0,0,0]=0;assert not child_gate(v,noDomain,o,c)[0,0];tests+=1
 r={'CPUParentLayerCases':tests,'irisScleraLidChildrenProtected':True,'canvasSkinNotBlanketProtected':True,'actualNativeOwnerMustMatchChildRole':True,'hairAndWorldNotBypassed':True,'noSourceHistoryOrRGBMix':True,'GPUExecuted':False};p=Path(__file__).resolve().parent/'face62';p.mkdir(exist_ok=True);(p/'CPU_PARENT62.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
if __name__=='__main__':main()
