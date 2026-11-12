from pathlib import Path
import json,numpy as np
from pigment_rays78 import intersect,gradient_profile
H=Path(__file__).resolve().parent;G=H/'face78'

def main():
 G.mkdir(exist_ok=True);tests=0;b=np.array([[.8,.7,.6],[.7,.8,.6],[.6,.7,.8],[.9,.6,.7]]);p=np.array([.2,.1,.05]);alpha=np.array([.2,.4,.6,.8]);c=b+alpha[:,None]*(p-b);r=intersect(b,c);assert r['rank']==3 and np.allclose(r['point'],p,atol=1e-12)and r['maxRayDistance']<1e-12 and r['allRayParametersAtLeastOne'];tests+=1
 for order in[np.arange(3)[[2,0,1]],np.arange(3)[[1,0,2]]]:
  q=intersect(b[:,order],c[:,order]);assert np.allclose(q['point'],p[order],atol=1e-12);tests+=1
 q=intersect(b[::-1],c[::-1]);assert np.allclose(q['point'],p,atol=1e-12);tests+=1
 flat=np.tile([.8,.7,.6],(4,1));mixed=flat+alpha[:,None]*(p-flat);q=intersect(flat,mixed);assert q['rank']==2 and q['point']is None;tests+=1
 # Two different legal pigment/alpha decompositions produce identical source
 # RGB on a fixed background. This does not depend on a numerical threshold.
 p2=flat[0]+.9*(p-flat[0]);alpha2=alpha/.9;assert(alpha2<=1).all()and np.allclose(mixed,flat+alpha2[:,None]*(p2-flat));tests+=1
 assert intersect(b,b)['point']is None;tests+=1
 inconsistent=c.copy();inconsistent[0]=[.7,.1,.9];q=intersect(b,inconsistent);assert q['maxRayDistance']>.01;tests+=1
 beyond=b+2*(p-b);q=intersect(b,beyond);assert not q['allRayParametersAtLeastOne'];tests+=1
 try:intersect([[float('nan')]*3],[[0]*3])
 except ValueError:tests+=1
 else:raise AssertionError('nonfinite accepted')
 t=np.arange(-4,5,dtype=float);g=np.exp(-.5*((t-.25)/1.5)**2);b0=np.array([.8,.7,.6]);b1=np.array([.01,-.02,.015]);alpha=.4;observed=(1-alpha*g[:,None])*(b0+b1*t[:,None])+alpha*g[:,None]*p
 q=gradient_profile(observed,t,1.5,.25);assert abs(q['alpha']-alpha)<1e-12 and np.allclose(q['point'],p,atol=1e-12)and q['crossChannelConstraintResidual']<1e-12 and q['necessaryModelCompatible']and q['alphaInterval'][0]<=alpha<=q['alphaInterval'][1];tests+=1
 q=gradient_profile(observed[::-1],t[::-1],1.5,.25);assert np.allclose(q['point'],p,atol=1e-12);tests+=1
 fixed=(1-alpha*g[:,None])*b0+alpha*g[:,None]*p;q=gradient_profile(fixed,t,1.5,.25);assert q['backgroundSlopeNorm']<1e-12;tests+=1
 additive=b0+b1*t[:,None]+g[:,None]*np.array([-.05,-.02,-.01]);q=gradient_profile(additive,t,1.5,.25);assert abs(q['alpha'])<1e-10;tests+=1
 rounded=np.rint(observed*255)/255;q=gradient_profile(rounded,t,1.5,.25,.5/255);assert q['necessaryModelCompatible']and q['alphaInterval'][0]<=alpha<=q['alphaInterval'][1];tests+=1
 conflicting=observed.copy();conflicting[4]+=[.1,-.1,.1];q=gradient_profile(conflicting,t,1.5,.25,.5/255);assert not q['necessaryModelCompatible'];tests+=1
 q=gradient_profile(fixed,t,1.5,.25,.5/255);assert q['necessaryModelCompatible']and q['alphaInterval'][1]-q['alphaInterval'][0]>.1 and not q['matteIdentified'];tests+=1
 result={'CPUChecks':tests,'knownConstantPigmentRecovered':True,'sampleAndChannelOrderInvariant':True,'fixedBackgroundContinuumExplicit':True,'inconsistentOrSuperopaqueNotAcceptedAsSourceColour':True,'compositingGradientTermDerivedAndRecovered':True,'additiveLineNotAssumedConstantPigmentMatte':True,'quantizationBoundsNecessaryNotSufficient':True,'paletteOrGPUOutput':False};(G/'CPU_RAYS78.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
