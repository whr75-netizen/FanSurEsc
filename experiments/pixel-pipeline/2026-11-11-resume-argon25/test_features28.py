"""Counterexamples separate native extrema from monotone AA and smooth ramps."""
from pathlib import Path
import json
import numpy as np
from source_features28 import extract,G
def main():
 yy,xx=np.mgrid[:48,:64];mask=np.ones(xx.shape,bool);tests=[]
 ramp=np.stack([90+xx,120+xx//2,170+xx//3],-1).astype(np.uint8)
 r=extract(ramp,mask);assert not r['positive'][6:-6,6:-6].any();tests.append('quantized monotone RGB ramp has no invented interior ridge')
 t=np.clip((xx-25)/8,0,1);aa=np.rint(np.array([80,60,50])+(np.array([240,220,200])-np.array([80,60,50]))*t[...,None]).astype(np.uint8)
 r=extract(aa,mask);assert not r['positive'][6:-6,6:-6].any();tests.append('monotone8-texel AA transition is not a source ridge')
 line=ramp.copy();line[:,31:34]=np.maximum(0,line[:,31:34].astype(int)-np.array([1,10,7])).astype(np.uint8)
 base=extract(line,mask);assert base['positive'][24,32];tests.append('weak3-texel source stroke survives without minimum-area cleanup')
 for image in [line,np.rot90(line),line[:,::-1]]:
  b=extract(image,np.ones(image.shape[:2],bool))
  for k in range(4):
   rotated=extract(np.rot90(image,k),np.rot90(np.ones(image.shape[:2],bool),k))
   assert np.array_equal(b['scale'],np.rot90(rotated['scale'],-k))and np.array_equal(b['scaleBits'],np.rot90(rotated['scaleBits'],-k));tests.append('D4 rotation scale/support invariant')
  reflected=extract(image[:,::-1],np.ones(image.shape[:2],bool))
  assert np.array_equal(b['scale'],reflected['scale'][:,::-1])and np.array_equal(b['scaleBits'],reflected['scaleBits'][:,::-1]);tests.append('D4 reflection scale/support invariant')
 unknown=mask.copy();unknown[:,30]=False;u=extract(line,unknown);assert not u['positive'][~unknown].any();tests.append('unknown source domain never becomes a feature witness')
 G.mkdir(exist_ok=True);out={'checks':len(tests),'passed':tests,'GPUUnityCalls':0,'semanticOrBeautyClaim':False};(G/'CPU_FEATURES28.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':len(tests),'passed':True}))
if __name__=='__main__':main()
