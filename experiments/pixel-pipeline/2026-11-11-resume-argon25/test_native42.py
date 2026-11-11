from pathlib import Path
import json,numpy as np
from native_contour42 import coordinates,native_min
H=Path(__file__).resolve().parent;G=H/'face42'
def main():
 deltas=[-.75,-.51,-.5,-.25,-.1,0,.1,.25,.5,.51,.75];checked=0
 for dx in deltas:
  for dy in deltas:
   rect=[203,33,5,4];join=[-1,2];origin=[3,4];delta=np.array([dx,dy],np.float32);q,p,inside=coordinates(rect,join,origin,delta);assert inside.all();receipt=np.floor(np.float32(np.float32(p+.5-origin)/2-delta)).astype(int);assert np.array_equal(receipt,q)
   lo=native_min(rect,join,origin,delta);yy,xx=np.mgrid[:8,:10];pixels=np.stack([xx+lo[0],yy+lo[1]],-1);receipt=np.floor(np.float32(np.float32(pixels+.5-origin)/2-delta)).astype(int);expected=q[yy//2,xx//2];assert np.array_equal(receipt,expected);checked+=1
 result={'fractionalDeltaCases':checked,'integerScale':2,'nativePixelsChecked':checked*80,'presenterFloorAndWorldSamplingMatched':True,'deltaNotRounded':True,'GPUCalls':0};(G/'CPU_NATIVE42.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
