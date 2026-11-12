"""Integer exterior band from CURRENT visible registered source cells only.

Width is an explicit test parameter. This is not native subpixel-width equality,
whole-character material registration, or permission to cache hidden strokes.
"""
import numpy as np

def resolve(before,actor,eligible,depth,world,meta,source_key,ink,width,previous=()):
 before=np.asarray(before,np.float32);actor=np.asarray(actor,bool);eligible=np.asarray(eligible,bool)
 h,w=actor.shape
 if before.shape!=(h,w,4)or max(h,w)>64 or eligible.shape!=(h,w)or source_key.shape!=(h,w,4):raise ValueError('bounded shared-grid inputs')
 if not isinstance(width,int)or not 0<=width<=2:raise ValueError('explicit integer width 0..2 only')
 if any(np.shape(a)!=(h,w)for a in [depth,world,meta]):raise ValueError('same current grid required')
 if not(np.isfinite(before).all()and np.isfinite(source_key).all()and np.isfinite(depth).all()and np.isfinite(world).all()and np.isfinite(meta).all()):raise ValueError('finite current receipts required')
 if (eligible&~actor).any()or(eligible&(depth<=0)).any():raise ValueError('source must actually be visible now')
 ink=np.asarray(ink,np.float32)
 if ink.shape not in [(3,),(h,w,3)]or not np.isfinite(ink).all():raise ValueError('actual source outline palette required')
 previous=set(previous);out=before.copy();owner=np.zeros((h,w,4),np.float32);selected=np.zeros((h,w),bool);reused=0
 # Canonical primitive/UV tie key is independent of screen traversal direction.
 # Previous keys may break equal-current-geometry ties only. They cannot admit a
 # hidden source or paint an ineligible destination, and never average RGB.
 for y in range(width,h-width):
  for x in range(width,w-width):
   if actor[y,x]or width==0:continue
   choices=[]
   for dy in range(-width,width+1):
    for dx in range(-width,width+1):
     yy,xx=y+dy,x+dx
     if not eligible[yy,xx]:continue
     z=depth[yy,xx]
     if world[y,x]<=0 or z>np.float32(world[y,x]+np.float32(.0001))or(meta[y,x]>0 and z>np.float32(meta[y,x]+np.float32(.0001))):continue
     key=tuple(float(v)for v in source_key[yy,xx]);choices.append(((dx*dx+dy*dy,float(z),key not in previous,key),key,yy,xx))
   if choices:
    _,key,yy,xx=min(choices);selected[y,x]=True;owner[y,x]=key;out[y,x]=[*(ink if ink.ndim==1 else ink[yy,xx]),1];reused+=key in previous
 return out,owner,selected,{'reusedCurrentTieSourceKeys':reused,'selected':int(selected.sum()),'cacheAdmissionOfHiddenSources':0}

def current_history(owner,selected):
 return {tuple(float(v)for v in k)for k in owner[selected]}
