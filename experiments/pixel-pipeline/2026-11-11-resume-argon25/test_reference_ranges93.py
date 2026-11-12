"""Original support-range constraints, not a semantic texture segmenter."""
import json,numpy as np
from pathlib import Path
from chromatic_value92 import build
H=Path(__file__).resolve().parent

def main():
 c=np.array([[10,20,30],[11,21,31],[80,90,100]],np.uint8);w=np.array([1,100,1]);initial=[0,0,0];bounds=np.stack([c,c],1);r=build(c,w,initial,[],reference_bounds=bounds);assert r['complete']and not len(r['unresolvedRangeColours'])and np.array_equal(c[r['referenceIndices'][r['colourAddress']]],c)
 # Strictly bounded partial failure stays explicit; cannot pretend a capped
 # refinement solved an unavailable representative.
 r=build(c,w,initial,[],max_splits=0,reference_bounds=bounds);assert not r['complete']and len(r['unresolvedRangeColours'])==2
 # Observed envelope permits reduction; it does not force per-texel colours.
 b=np.tile([[10,20,30],[80,90,100]],(3,1,1));r=build(c,w,initial,[],reference_bounds=b);assert r['complete']and r['addresses']==1
 # No-bound call retains the exact previous92 algorithm and recorded output.
 v=np.load(H/'face92/SOURCE_VALUE92.npz');scalar=np.load(H/'face90/SOURCE_VALUE90.npz');r=build(v['colours'],v['counts'],scalar['colourAddress'],v['pairs']);assert r['complete']and np.array_equal(r['colourAddress'],v['colourAddress'])and np.array_equal(r['referenceIndices'],v['referenceIndices'])
 for bad in [bounds.astype(int)+1,np.zeros((3,2,2))]:
  try:build(c,w,initial,[],reference_bounds=bad)
  except ValueError:pass
  else:raise AssertionError('invalid range accepted')
 d={'CPUOnly':True,'checks':6,'unbounded92ExactRegression':True,'constantCounterexamplePreserved':True,'limitedBudgetNotHidden':True,'notSemanticSegmentation':True};(H/'face93/CPU_REFERENCE_RANGES93.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
