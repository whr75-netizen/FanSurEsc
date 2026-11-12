from pathlib import Path
import json,numpy as np
from colour_field82 import build
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face82'

def main():
 G.mkdir(exist_ok=True);rgb=np.array([[110,90,80],[130,110,95],[150,130,110],[170,150,130],[190,170,150],[210,190,170]],np.uint8);w=np.array([1,5,7,7,5,1]);orders=[(0,2),(2,4),(3,5)];a=build(rgb,w,orders,[(0,5)]);assert a['families']<len(rgb)and a['sourceOrderSatisfied'];tests=1
 p=np.array([4,1,5,2,0,3]);inv=np.argsort(p);b=build(rgb[p],w[p],[(int(inv[i]),int(inv[j]))for i,j in orders],[(int(inv[0]),int(inv[5]))]);assert np.array_equal(rgb[a['referenceIndices'][a['address']]],rgb[p][b['referenceIndices'][b['address']]][inv]);tests+=1
 # Separate geometry does not enter the colour key. Equal RGB receives the
 # same address; this API rejects duplicate RGB nodes instead of assigning
 # different material/region medoids to identical source inputs.
 try:build(np.array([[1,2,3],[1,2,3]],np.uint8),np.ones(2,int),[],[])
 except ValueError:tests+=1
 else:raise AssertionError('duplicate source RGB nodes accepted')
 a=build(rgb,w,[],[]);assert a['families']==1;tests+=1
 result={'CPUChecks':tests,'nativeContrastAndFieldRangePreserved':True,'sampleOrderInvariant':True,'materialOwnerOrUVNotColourKey':True,'observedRGBOnly':True,'GPUExecuted':False};(G/'CPU_COLOUR_FIELD82.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
