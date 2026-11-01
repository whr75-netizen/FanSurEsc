"""AA transition hypothesis: scale-persistent resolved gradient peaks.

Gaussian signals are used only for boundary evidence. No blurred RGB is output.
All masks and palette candidates keep the original source texels unchanged.
"""
import numpy as np
from uv_features64 import colour_intervals,barrier_components

def gaussian(a,sigma):
 r=int(np.ceil(3*sigma));x=np.arange(-r,r+1);k=np.exp(-.5*(x/sigma)**2);k/=k.sum();out=a.astype(np.float64)
 for axis in [0,1]:
  pad=[(0,0)]*out.ndim;pad[axis]=(r,r);p=np.pad(out,pad,mode='edge');v=np.zeros_like(out)
  for i,w in enumerate(k):
   sl=[slice(None)]*out.ndim;sl[axis]=slice(i,i+out.shape[axis]);v+=w*p[tuple(sl)]
  out=v
 return out
def shift(a,n,axis):return np.take(a,np.clip(np.arange(a.shape[axis])+n,0,a.shape[axis]-1),axis=axis)
def peaks(rgb,mask,scales=(1,2,4)):
 centre,lo,hi=colour_intervals(rgb);error=np.linalg.norm(np.maximum(centre-lo,hi-centre),axis=-1);byaxis=[[],[]]
 for sigma in scales:
  support=gaussian(mask.astype(float),sigma);s=np.maximum(support,1e-15);colour=gaussian(centre*mask[...,None],sigma)/s[...,None];uncertainty=gaussian(error*mask,sigma)/s
  for axis in [0,1]:
   delta=shift(colour,1,axis)-colour;mag=np.linalg.norm(delta,axis=-1);bound=uncertainty+shift(uncertainty,1,axis);valid=mask&shift(mask,1,axis);pos=np.arange(mask.shape[axis]);valid &= (pos<mask.shape[axis]-1)[:,None]if axis==0 else(pos<mask.shape[axis]-1)[None,:]
   left=shift(mag,-1,axis);right=shift(mag,1,axis);local=(mag>=left)&(mag>=right)&((mag>left)|(mag>right));resolved=mag>bound
   byaxis[axis].append(valid&local&resolved)
 persistent=[]
 for axis in [0,1]:
  first=byaxis[axis][0].copy()
  for scale,p in zip(scales[1:],byaxis[axis][1:]):
   nearby=np.zeros_like(mask)
   for offset in range(-int(scale),int(scale)+1):nearby|=shift(p,offset,axis)
   first &=nearby
  persistent.append(first)
 labels,n=barrier_components(mask,persistent[1],persistent[0]);return {'x':persistent[1],'y':persistent[0],'labels':labels,'count':n,'scales':scales,'fineX':byaxis[1][0],'fineY':byaxis[0][0]}

def tests():
 mask=np.ones((48,96),bool);ramp=np.repeat(np.linspace(40,180,96).astype(np.uint8)[None,:,None],48,axis=0);ramp=np.repeat(ramp,3,axis=2);a=peaks(ramp,mask)
 step=np.full((48,96,3),45,np.uint8);step[:,48:]=225
 for i,v in enumerate([55,90,155,210]):step[:,46+i]=v
 b=peaks(step,mask);thin=np.full((48,96,3),210,np.uint8);thin[:,46:50]=45;c=peaks(thin,mask)
 return {'rampRegions':a['count'],'aaStepRegions':b['count'],'thinStripeRegions':c['count'],'aaStepSeparated':int(b['labels'][24,10])!=int(b['labels'][24,85]),'thinSourceDifferent':int(c['labels'][24,47])!=int(c['labels'][24,10])}
