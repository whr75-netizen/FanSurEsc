"""Colour-field evidence, not a semantic gradient/AA/paint classifier.

An opaque two-colour AA ramp and an authored colour gradient can have identical
RGB bytes. Return their shared feasible set rather than inventing a label.
The half-code uncertainty is the source encoding's quantization interval.
"""
import numpy as np
def linear(x):
 x=np.asarray(x,float)/255
 return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def chord_intervals(rgb,a,b):
 rgb=np.asarray(rgb)
 if rgb.dtype!=np.uint8 or rgb.shape[-1]!=3:raise ValueError('original source RGB8 required')
 a=np.asarray(a);b=np.asarray(b)
 if a.shape!=(3,)or b.shape!=(3,)or a.dtype!=np.uint8 or b.dtype!=np.uint8:raise ValueError('two source RGB8 anchors required')
 lo=linear(np.maximum(rgb.astype(float)-.5,0));hi=linear(np.minimum(rgb.astype(float)+.5,255));start=linear(a);direction=linear(b)-start
 low=np.zeros(rgb.shape[:-1]);high=np.ones(rgb.shape[:-1]);valid=np.ones(rgb.shape[:-1],bool)
 for c in range(3):
  if direction[c]==0:valid&=(start[c]>=np.nextafter(lo[...,c],-np.inf))&(start[c]<=np.nextafter(hi[...,c],np.inf))
  else:
   x=(lo[...,c]-start[c])/direction[c];y=(hi[...,c]-start[c])/direction[c];low=np.maximum(low,np.minimum(x,y));high=np.minimum(high,np.maximum(x,y))
 valid&=np.nextafter(low,-np.inf)<=np.nextafter(high,np.inf)
 return {'compatible':valid,'lower':low,'upper':high,'interpretation':'compatible with both an authored gradient and two-anchor AA; no unique semantic class'}
def monotone(intervals,reverse=False):
 lo=np.asarray(intervals['lower']).reshape(-1);hi=np.asarray(intervals['upper']).reshape(-1);valid=np.asarray(intervals['compatible']).reshape(-1)
 if reverse:lo,hi,valid=lo[::-1],hi[::-1],valid[::-1]
 value=0.
 for a,b,ok in zip(lo,hi,valid):
  if not ok:return False
  value=max(value,a)
  if np.nextafter(value,-np.inf)>np.nextafter(b,np.inf):return False
 return True
