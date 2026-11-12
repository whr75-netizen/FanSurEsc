"""Small source-field/feature counterexamples; no Unity or GPU API."""
from pathlib import Path
import json,numpy as np
from joint_address102 import optimize,uncertainty_edges

def fixture(colours):
 rgb=np.asarray(colours,np.uint8);refs=np.array([0,len(rgb)-1]);palette=np.repeat(rgb[refs,None,:].astype(int),3,axis=1);palette[:,0]-=30;palette[:,1]-=15;return rgb,refs,palette

def main():
 rgb,refs,p=fixture([[100,100,100],[101,100,100],[102,100,100],[104,100,100]]);initial=[0,0,1,1];plain=optimize(rgb,[1]*4,initial,refs,p,[],[]);feature=optimize(rgb,[1]*4,initial,refs,p,[[1,2]],[[1,2]]);assert plain['labels'][1]==plain['labels'][2]and feature['labels'][1]!=feature['labels'][2];assert feature['hardProfileProjectionAndLuminanceNeverWeaker'];checks=2
 # Source hue/reference values are inputs, not fixed skin/brown/material names.
 blue,refb,pb=fixture([[80,120,180],[80,121,180],[80,122,180],[80,124,180]]);b=optimize(blue,[1]*4,initial,refb,pb,[[1,2]],[[1,2]]);assert b['labels'][1]!=b['labels'][2];checks+=1
 edges,_=uncertainty_edges(np.array([[0,0,255],[0,1,0]],int));assert len(edges)==0;checks+=1
 image=np.array([[0,1,2,3,0],[0,1,2,3,0],[3,2,1,0,3]],int);expected=feature['labels'][image]
 for mirror in [False,True]:
  for k in range(4):
   src=np.fliplr(image)if mirror else image;src=np.rot90(src,k);counts=np.bincount(src.ravel(),minlength=4);result=optimize(rgb,counts,initial,refs,p,[[1,2]],[[1,2]]);out=result['labels'][src];out=np.rot90(out,-k);out=np.fliplr(out)if mirror else out;assert np.array_equal(out,expected);checks+=1
 try:optimize(rgb,[1]*4,[0,0,0,1],refs,p,[[1,2]],[]);raise RuntimeError('invalid zero-contrast feature input accepted')
 except AssertionError:checks+=1
 out={'CPUOnly':True,'checks':checks,'twoDifferentColourFixtures':True,'rangeNotAutomaticallyHardContrast':True,'observedThinFeatureContrastAndOrderPreserved':True,'D4SourceFieldEquivalent':True,'sameRGBSameAddressNoMaterialAnchor':True,'noRGBMixOrNewPalette':True,'semanticAAOrPigmentGroundTruthClaimed':False};path=Path(__file__).resolve().parent/'face102/CPU_TESTS102.json';path.write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=='__main__':main()
