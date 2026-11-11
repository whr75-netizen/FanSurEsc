"""Float32 oracle for the bounded final depth/colour proposal, not a line raster oracle."""
import numpy as np
def resolve(line,proof,before,meta,world,inside,offset,ink):
 line,proof,before,meta,world=[np.asarray(x,np.float32)for x in [line,proof,before,meta,world]];depth=np.float32(proof[...,0]+np.float32(offset));eps=np.float32(.0001)
 finite=np.isfinite(line).all(-1)&np.isfinite(proof).all(-1)&np.isfinite(meta).all(-1)&np.isfinite(world).all(-1)&np.isfinite(depth)
 source=(line[...,3]==1)&(line[...,:3]==np.asarray(ink,np.float32)).all(-1)&(proof[...,0]>0)&(proof[...,1]>0)&(proof[...,3]>0)
 style=inside&finite&((meta[...,0]<=0)|(depth<=np.float32(meta[...,0]+eps)));visible=inside&finite&(world[...,0]>0)&(depth<=np.float32(world[...,0]+eps));use=source&style&visible
 after=before.copy();after[use]=np.r_[np.asarray(ink,np.float32),np.float32(1)];gate=np.stack([source,style,visible,np.where(inside&finite,use,-1)],-1).astype(np.float32);return after,gate
def coordinates(rect,shape,join,delta):
 x,y,w,h=rect;assert shape==[480,272]
 yy,xx=np.mgrid[:h,:w];main=np.stack([xx+x+join[0],yy+272-y-h+join[1]],-1);out=main+np.asarray(delta);valid=(main>=0).all(-1)&(main<shape).all(-1)&(out>=0).all(-1)&(out<shape).all(-1);return main,out,valid
