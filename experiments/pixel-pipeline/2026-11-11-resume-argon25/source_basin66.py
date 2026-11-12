"""Closed native-colour sublevel components around certified source witnesses.

This does not infer author semantics or a complete palette-family partition.
No RGB smoothing, minimum-area deletion, output painting or threshold sweep.
Each threshold is measured from that witness's real two flanks. Integer dot
products avoid arithmetic-order thresholds; different valid axes stay explicit.
"""
import numpy as np
from collections import deque
AXES=((1,0),(0,1),(1,1),(1,-1))

def component(support,seed):
 h,w=support.shape;y,x=seed;out=np.zeros((h,w),bool)
 if not(0<=x<w and 0<=y<h)or not support[y,x]:return out
 out[y,x]=True;q=deque([(y,x)])
 while q:
  y,x=q.popleft()
  for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
   if 0<=xx<w and 0<=yy<h and support[yy,xx] and not out[yy,xx]:out[yy,xx]=True;q.append((yy,xx))
 return out

def witnesses(rgba,mask,xy,radii=(1,2,4)):
 rgba=np.asarray(rgba);mask=np.asarray(mask,bool);h,w=mask.shape;x,y=xy
 if rgba.shape!=(h,w,4)or rgba.dtype!=np.uint8 or h*w>1100000:raise ValueError('bounded original native RGBA8/support required')
 if not(0<=x<w and 0<=y<h)or not mask[y,x]or rgba[y,x,3]!=255:raise ValueError('actual opaque source witness required')
 valid=mask&(rgba[:,:,3]==255);rgb=rgba[:,:,:3].astype(np.int32);c=rgb[y,x];rows=[];cores=[];nominals=[]
 for radius in radii:
  for axis,(dx,dy)in enumerate(AXES):
   ax,ay=x-dx*radius,y-dy*radius;bx,by=x+dx*radius,y+dy*radius
   if not(0<=ax<w and 0<=ay<h and 0<=bx<w and 0<=by<h and valid[ay,ax]and valid[by,bx]):continue
   left=rgb[ay,ax]-c;right=rgb[by,bx]-c;n=left+right;bound=int(abs(n).sum());cut=int(min(left@n,right@n))
   if cut<=bound:continue # Positive evidence only; non-extrema are unknown.
   level=(rgb-c)@n
   nominal=component(valid&(level<cut),(y,x))
   # Compare pixel with each flank directly: their shared subtraction of the
   # witness colour cancels. The error is ||n||1, not two independent bounds.
   # n is the fixed direction derived from the observed native RGB8 witness.
   core=component(valid&(level<cut-bound),(y,x))
   touches=bool(nominal[0].any()or nominal[-1].any()or nominal[:,0].any()or nominal[:,-1].any())
   rows.append({'radius':radius,'axis':axis,'normalIntegerRGB':n.tolist(),'flankBarrierDot':cut,'oneDeltaRoundoffBoundDot':bound,'nominalTexels':int(nominal.sum()),'robustCoreTexels':int(core.sum()),'touchesImageEdge':touches});nominals.append(nominal);cores.append(core)
 if not rows:return {'witnesses':[],'core':np.zeros((h,w),bool),'nominalUnion':np.zeros((h,w),bool),'uniqueNominal':False,'familyConfirmed':False}
 core=np.logical_and.reduce(cores);union=np.logical_or.reduce(nominals);unique=all(np.array_equal(nominals[0],m)for m in nominals[1:])
 return {'witnesses':rows,'core':core,'nominalUnion':union,'uniqueNominal':unique,'familyConfirmed':False}
