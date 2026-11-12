from pathlib import Path
import json,numpy as np
from native_width86 import project,extrude,green_repeat_bilinear

def main():
 checks=0;view=np.eye(4);pr=np.eye(4);p=np.array([[0.,0.,0.],[.1,.2,0.]])
 n=np.array([[1.,0.,0.],[0.,1.,0.]]);g=np.array([1.,.5]);a=extrude(p,n,[1,1],.02,g,view,pr,[100,80]);assert np.allclose(a['delta'],[[1,0],[0,-.4]]);checks+=1
 # A simultaneous model+camera scale change preserves the projected width.
 for scale in [.01,.1,2.,100.]:
  q=pr.copy();q[:3,:3]/=scale;b=extrude(p*scale,n,[1,1],.02*scale,g,view,q,[100,80]);assert np.allclose(a['delta'],b['delta'],atol=1e-12);checks+=1
 for width in [0,.002,.01,.02]:
  b=extrude(p,n,[1,1],width,np.zeros(2),view,pr,[100,80]);assert not b['delta'].any();checks+=1
 try:extrude(p,n,[1,0],.02,g,view,pr,[100,80])
 except ValueError:checks+=1
 else:raise AssertionError('missing normal accepted')
 image=np.zeros((2,2,4),np.uint8);image[:,:,1]=[[0,64],[128,255]]
 uv=np.array([[.25,.25],[.75,.25],[.25,.75],[.75,.75],[.5,.5]])
 assert np.allclose(green_repeat_bilinear(image,uv),[128/255,1,0,64/255,447/1020]);checks+=1
 for shift in [[1,0],[0,1],[-3,7]]:assert np.allclose(green_repeat_bilinear(image,uv+shift),green_repeat_bilinear(image,uv));checks+=1
 encoded=green_repeat_bilinear(image,uv);linear=green_repeat_bilinear(image,uv,True);assert np.all(linear<=encoded)and linear[-1]!=(encoded[-1]/12.92 if encoded[-1]<=.04045 else((encoded[-1]+.055)/1.055)**2.4);checks+=1
 # Perspective must project the expanded point, not apply one fixed pixel ratio.
 q=np.eye(4);q[3]=[0,0,1,0];r=np.array([[0.,0.,2.],[0.,0.,4.]])
 b=extrude(r,np.tile([1.,0,0],(2,1)),[1,1],.02,[1,1],view,q,[100,80]);assert np.allclose(b['length'],[.5,.25]);checks+=1
 result={'CPUChecks':checks,'sourceNormalSubstitution':False,'rasterOrIntegerWidthPolicyProven':False};root=Path(__file__).resolve().parent/'face86';root.mkdir(exist_ok=True);(root/'CPU_NATIVE_WIDTH86.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
