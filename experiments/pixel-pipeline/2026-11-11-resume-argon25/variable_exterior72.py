"""Current source radius field. Selection oracle, never uploaded RGB."""
import numpy as np

def resolve(before,actor,eligible,depth,world,meta,keys,inks,radius,previous=()):
 b=np.asarray(before,np.float32);h,w=actor.shape;r=np.asarray(radius)
 if max(h,w)>64 or b.shape!=(h,w,4)or r.shape!=(h,w)or not np.isfinite(r).all()or not np.array_equal(r,np.rint(r))or (r<0).any()or(r>2).any():raise ValueError('bounded current integer source radius 0..2')
 if any(np.shape(t)!=(h,w)for t in[eligible,depth,world,meta])or keys.shape!=(h,w,4)or inks.shape!=(h,w,3):raise ValueError('one current grid')
 if not all(np.isfinite(t).all()for t in[b,depth,world,meta,keys,inks]):raise ValueError('finite current inputs')
 if(eligible&~actor).any()or(eligible&(depth<=0)).any():raise ValueError('currently visible source required')
 out=b.copy();owner=np.zeros_like(keys);selected=np.zeros_like(actor);trace=np.zeros((h,w),np.int32);previous=set(previous)
 for y in range(2,h-2):
  for x in range(2,w-2):
   if actor[y,x]:continue
   choices=[]
   for dy in range(-2,3):
    for dx in range(-2,3):
     yy,xx=y+dy,x+dx;ch=max(abs(dx),abs(dy))
     if ch==0 or not eligible[yy,xx]or ch>r[yy,xx]:continue
     z=depth[yy,xx]
     if world[y,x]<=0 or z>np.float32(world[y,x]+np.float32(.0001))or(meta[y,x]>0 and z>np.float32(meta[y,x]+np.float32(.0001))):continue
     key=tuple(float(v)for v in keys[yy,xx]);choices.append(((dx*dx+dy*dy,float(z),key not in previous,key),yy,xx))
   if choices:
    _,yy,xx=min(choices);out[y,x]=[*inks[yy,xx],1];owner[y,x]=keys[yy,xx];selected[y,x]=True;trace[y,x]=r[yy,xx]
 return out,owner,selected,trace

def source_green(uv,values,point):
 """UV inverse only when defined. Equal scalar vertices need no inverse."""
 uv=np.asarray(uv,np.float64);values=np.asarray(values,np.float64);p=np.asarray(point,np.float64)
 if not(np.isfinite(uv).all()and np.isfinite(values).all()and np.isfinite(p).all())or(values<0).any()or(values>1).any():return None
 if np.all(values==values[0]):return float(values[0])
 a,b,c=uv;matrix=np.stack([b-a,c-a],1)
 if np.linalg.det(matrix)==0:return None
 v,w=np.linalg.solve(matrix,p-a);bary=np.array([1-v-w,v,w])
 if(bary<0).any()or(bary>1).any():return None
 return float(values@bary)
