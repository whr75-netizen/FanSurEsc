import numpy as np
from final_contour41 import resolve
def coordinates(rect,join,origin,delta):
 x,y,w,h=rect;yy,xx=np.mgrid[:h,:w];q=np.stack([xx+x+join[0],yy+272-y-h+join[1]],-1).astype(np.int32);v=np.float32(np.float32(q.astype(np.float32)+np.float32(.5))+np.asarray(delta,np.float32));p=np.floor(np.float32(np.asarray(origin,np.float32)+np.float32(v*np.float32(2)))).astype(int);p=np.clip(p,[0,0],[959,543]);inside=(q>=0).all(-1)&(q<[480,272]).all(-1);return q,p,inside
def native_min(rect,join,origin,delta):
 x,y,w,h=rect;q=np.array([x+join[0],272-y-h+join[1]],np.float32);v=np.float32(np.float32(q+np.asarray(delta,np.float32))*2);return np.ceil(np.float32(np.asarray(origin,np.float32)+v-.5)).astype(int)
def oracle(line,proof,before,meta,world,cell,inside,q,offset,ink):
 valid=inside&np.isfinite(cell).all(-1)&(cell[...,:2]==q).all(-1);return resolve(line,proof,before,meta,world,valid,offset,ink)
