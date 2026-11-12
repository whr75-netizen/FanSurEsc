from pathlib import Path
import json,numpy as np
from source_hysteresis80 import linked
H=Path(__file__).resolve().parent;G=H/'face80'

def main():
 G.mkdir(exist_ok=True);a=np.zeros((17,17),bool);a[2:14,7]=True;a[13,8:13]=True;a[2,14]=True;s=np.zeros_like(a);s[4,7]=True;out,cc=linked(a,s);assert out.sum()==17 and not out[2,14];tests=1
 for m in[False,True]:
  for k in range(4):
   f=lambda z:np.rot90(z[:,::-1]if m else z,k);got,_=linked(f(a),f(s));assert np.array_equal(got,f(out));tests+=1
 empty,_=linked(a,np.zeros_like(a));assert not empty.any();tests+=1
 # A missing observed pixel is not filled to connect two structures.
 gap=a.copy();gap[10,7]=False;got,_=linked(gap,s);assert not got[11,7]and not got[10,7];tests+=1
 result={'CPUChecks':tests,'D4Exact':True,'noUnobservedGapFilled':True,'unseededEvidenceNotPromoted':True,'noThresholdOrPaletteSearch':True,'GPUExecuted':False};(G/'CPU_HYSTERESIS80.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
