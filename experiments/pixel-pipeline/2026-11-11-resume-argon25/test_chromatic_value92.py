from pathlib import Path
import json,numpy as np
from chromatic_value92 import build
from audit_polarity76 import luminance
def main():
 rng=np.random.default_rng(92);checks=0
 for case in range(12):
  colours=np.unique(rng.integers(0,256,(16,3),dtype=np.uint8),axis=0);n=len(colours);counts=rng.integers(1,30,n);yorder=np.argsort(luminance(colours));initial=np.empty(n,int);initial[yorder]=np.arange(n)//4;pairs=[(i,j)for i in range(n)for j in range(i+1,n)];a=build(colours,counts,initial,pairs);assert a['complete']and a['sourceContrastDirectionsPreserved']and a['addresses']<=n;checks+=1
  b=build(colours,counts,initial,[(j,i)for i,j in reversed(pairs)]);assert np.array_equal(colours[a['referenceIndices'][a['colourAddress']]],colours[b['referenceIndices'][b['colourAddress']]]);checks+=1
 c=np.array([[10,20,30],[20,30,40],[100,110,120]],np.uint8);a=build(c,[1,3,1],[0,0,1],[(0,1)],max_splits=0);assert not a['complete']and len(a['unresolvedPairs'])==1;checks+=1
 result={'CPUChecks':checks,'originalRGBReferencesOnly':True,'sourcePairOrderAndEndpointSwapInvariant':True,'budgetFailureExplicit':True,'globalMinimumClaimed':False};G=Path(__file__).resolve().parent/'face92';G.mkdir(exist_ok=True);(G/'CPU_CHROMATIC92.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
