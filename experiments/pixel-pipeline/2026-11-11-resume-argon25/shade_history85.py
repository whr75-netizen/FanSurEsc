"""Source-carrier Q hysteresis, never RGB history or visibility reconstruction.

The uncertainty band is335's existing one-tenth quantization-bin error budget.
No screen RGB, palette interpolation, fixed feature size or light averaging.
"""
import numpy as np
from selected_light84 import barycentric_uv

def choose(current_q,g,previous_q,levels,current_valid=True,previous_valid=True):
 if levels<2 or levels>256:raise ValueError('finite shade levels')
 if not all(np.isfinite(x)for x in [current_q,g,previous_q]):return current_q,False
 if not current_valid or not previous_valid:return current_q,False
 step=np.float32(1/np.float32(levels-1));q=np.float32(current_q);p=np.float32(previous_q);cut=np.float32((q+p)*np.float32(.5));distance=abs(np.float32(g)-cut)
 if abs(abs(p-q)-step)>np.float32(1e-6)or distance>np.float32(step*np.float32(.1)):return current_q,False
 return float(p),True

def prior_address(previous_geometry,primitive,uv,previous_qroi):
 g=previous_geometry
 if not 1<=primitive<=len(g['tri']):return None,'primitive'
 t=g['v'][g['tri'][primitive-1]].astype(float);b=barycentric_uv(t[:,3:5],uv)
 if b is None:return None,'UV-degenerate'
 if min(b)<0 or max(b)>1:return None,'UV-outside-carrier'
 head=b@t[:,5:7];pixel=np.array([head[0],272-head[1]])
 # Before.x exactly integer lies halfway between two pixel centres. Do not
 # invent a unique first-frame/lookup tie from loop or memory order.
 uncertainty=32*np.finfo(np.float32).eps*(1+np.max(abs(pixel)));fraction=pixel-np.floor(pixel)
 if np.any(np.minimum(fraction,1-fraction)<=uncertainty):return None,'uncertain-grid-boundary'
 q=np.floor(pixel).astype(int);origin=np.array([previous_qroi[0],272-previous_qroi[1]-previous_qroi[3]]);local=q-origin
 if np.any(local<0)or local[0]>=previous_qroi[2]or local[1]>=previous_qroi[3]:return None,'outside-previous-ROI'
 return tuple(map(int,local)),'mapped'
