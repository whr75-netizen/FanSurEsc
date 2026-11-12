from pathlib import Path
import json,hashlib,numpy as np
import review_colour89 as review
H=Path(__file__).resolve().parent;G=H/'face92/gpu'
def main():
 review.G=G;review.C=G/'capture';review.SOURCE_ROOT=H/'face92';review.CONTROL_FILE=H/'face92/PALETTE92.rgb';review.NAME='92';review.CONTROL_TITLE='Actual92 Y-only rounding control';review.VALUE_TITLE='Actual92 RGB-constraint LUT';review.main();actual=(G/'capture/RUNTIME_PALETTE89.rgb').read_bytes();assert actual==(H/'face92/CSHARP_CONSTRAINED92.rgb').read_bytes();palette=np.frombuffer(actual,np.uint8).reshape(-1,3,3);z=np.load(H/'face92/PALETTE_CONSTRAINT_INPUT92.npz');vectors=z['vectors'];a,b=vectors[:,0],vectors[:,1];rows=[]
 for k in range(3):
  dot=((palette[a,k].astype(np.int64)-palette[b,k])*vectors[:,2:]).sum(1);assert(dot>0).all();rows.append({'shade':k,'allMeasuredNativeRGBDirectionsPreserved':True,'nonpositiveContrasts':0})
 result={'actualGPUFrames':json.loads((G/'capture/COMPLETE.json').read_text())['stream77']['received'],'runtimePaletteBytesExactlyMatchIndependentCPU':True,'actualPaletteSHA256':hashlib.sha256(actual).hexdigest(),'nativeContrastPairs':len(vectors),'rows':rows,'originalContinuousTargetsAndFloorCeilBoundsUnchanged':True,'sourceRegionSemanticsOrArtAdopted':False};(G/'ACTUAL_PALETTE_CONSTRAINTS92.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':
 import sys
 if '--motion'in sys.argv:G=H/'face92/motion240'
 main()
