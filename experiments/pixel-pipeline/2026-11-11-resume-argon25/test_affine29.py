"""Validate the conditional model AND retain a nonlinear-gradient counterexample."""
import json
import numpy as np
from affine_support29 import intervals,probe,G
def main():
 yy,xx=np.mgrid[:25,:25];base=np.stack([180+xx,190+yy,200+xx+yy],-1).astype(np.uint8);mask=np.ones(xx.shape,bool);p=np.array([[12,12]]);before=base.copy();tests=[]
 for r in [1,2,4]:
  for d in [(1,0),(0,1),(1,1),(1,-1)]:
   z=probe(base,mask,p,r,d);assert z[0,0]==1 and z[0,1]<=1e-7;tests.append('affine RGB field remains feasible, all scales/directions')
 assert np.array_equal(base,before)
 stroke=base.copy();stroke[9:16,11:14]-=np.array([1,8,5],np.uint8);z=probe(stroke,mask,p,4,(1,0));assert z[0,0]==1 and z[0,1]>0;tests.append('weak finite stroke lies outside feasible affine flank field')
 masked=mask.copy();masked[8,8]=False;z=probe(stroke,masked,p,4,(1,0));assert not z[0,0];tests.append('unknown source flank rejects model rather than inventing fill')
 # Alpha is not recoverable uniquely from opaque baked RGB. Both layers here
 # exactly reproduce the actual centre RGB, with valid distinct source colours.
 I=np.array([253,228,208]);B=np.array([254,236,214]);pigment=2*I-B;assert np.all((pigment>=0)&(pigment<=255))and np.array_equal((pigment+B)/2,I);tests.append('actual RGB has distinct exact opaque-field and half-alpha-pigment explanations')
 q=np.stack([80+(xx-12)**2+(yy-12)**2]*3,-1).clip(0,255).astype(np.uint8);z=probe(q,mask,p,1,(1,0));assert z[0,0]==1 and z[0,1]>0
 tests.append('COUNTEREXAMPLE: smooth quadratic field also rejects affine model; never promote residual to pigment truth')
 result={'checks':len(tests),'passed':tests,'nonlinearGradientCounterexampleMargin':float(z[0,1]),'adoptedAsFullRegionClassifier':False,'GPUUnityCalls':0}
 G.mkdir(exist_ok=True);(G/'CPU_AFFINE29.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'checks':len(tests),'gradientCounterexampleRetained':True}))
if __name__=='__main__':main()
