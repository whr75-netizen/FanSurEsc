"""Compare native transverse RGB profiles: affine field, finite line, AA step.

Model-fit evidence is not author-semantic truth. No fitted RGB is emitted as a
palette reference. Native observed bytes remain the only colour source.
"""
import math,numpy as np
from source_ridge70 import sample

def fit_profiles(rgb,rows,nx,ny,px,py):
 rows=np.asarray(rows,int);t=np.arange(-4,5,dtype=float);x=px[rows[:,0],rows[:,1]];y=py[rows[:,0],rows[:,1]];n=np.stack([nx[rows[:,0],rows[:,1]],ny[rows[:,0],rows[:,1]]],1)
 observed=sample(rgb.astype(float),x[:,None]+t[None,:]*n[:,0,None],y[:,None]+t[None,:]*n[:,1,None]);base=np.stack([np.ones(9),t],1);flat=observed.reshape(len(rows),9,3);pred=np.einsum('ij,njc->nic',base@np.linalg.pinv(base),flat);affine=((flat-pred)**2).sum((1,2));result={'affineSSE':affine}
 for name in ['line','step']:
  best=np.full(len(rows),np.inf);width=np.zeros(len(rows));shift=np.zeros(len(rows));amplitude=np.zeros((len(rows),3))
  for sigma in [.5,1.,1.5,2.,3.,4.]:
   for offset in[-.5,0.,.5]:
    z=(t-offset)/sigma;profile=np.exp(-.5*z*z)if name=='line'else .5*(1+np.array([math.erf(v/np.sqrt(2))for v in z]));model=np.column_stack([base,profile]);inverse=np.linalg.pinv(model);coef=np.einsum('ij,njc->nic',inverse,flat);fitted=np.einsum('ij,njc->nic',model,coef);err=((flat-fitted)**2).sum((1,2));better=err<best-1e-10
    best[better]=err[better];width[better]=sigma;shift[better]=offset;amplitude[better]=coef[better,2]
  result[name+'SSE']=best;result[name+'Sigma']=width;result[name+'Offset']=shift;result[name+'Amplitude']=amplitude
 line=result['lineSSE'];step=result['stepSSE'];amp=np.linalg.norm(result['lineAmplitude'],axis=1);amargin=abs(result['lineAmplitude']).sum(1)/np.maximum(amp,1e-30)
 # Report all residuals. This confidence margin does not relabel failures as
 # background or discard low-contrast authored features.
 result['lineWins']=(line<affine-1e-9)&(line<step-1e-9)&(amp>amargin)
 return result
