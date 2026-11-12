"""Native MToon world-width vertex extrusion, before raster/visibility.

Use the recorded deformed vertex normal, not a face-flat or normal-map normal.
The projected displacement is not an opaque integer line-width policy or a
claim that swept discs reproduce the inverted-hull rasterizer.
"""
import struct
import numpy as np

def text(stream):
 size=0;shift=0
 for _ in range(5):
  b=stream.read(1)
  if not b:raise ValueError('truncated string')
  size|=(b[0]&127)<<shift
  if b[0]<128:break
  shift+=7
 else:raise ValueError('invalid bounded string')
 if size>4096:raise ValueError('bounded provenance string')
 b=stream.read(size)
 if len(b)!=size:raise ValueError('truncated provenance')
 return b.decode('utf-8')

def normals(path):
 with path.open('rb')as f:
  if text(f)!='native-outline-normals86/v1':raise ValueError('native normals ABI')
  sid=text(f);frame,n=struct.unpack('<ii',f.read(8))
  if not 0<n<100000:raise ValueError('bounded vertex count')
  raw=f.read(n*13)
  if len(raw)!=n*13 or f.read():raise ValueError('normals payload length')
  d=np.frombuffer(raw,np.dtype([('valid','u1'),('normal','<f4',(3,))]))
  valid=d['valid'].astype(bool);normal=d['normal'].astype(float)
  if(d['valid']>1).any()or not np.isfinite(normal).all():raise ValueError('finite original normals')
  if np.max(abs(np.linalg.norm(normal[valid],axis=1)-1),initial=0)>2e-6:raise ValueError('recorded normalized world normals')
  return {'sourceId':sid,'frame':frame,'valid':valid,'normal':normal}

def project(points,view,projection,viewport):
 p=np.asarray(points,float);v=np.asarray(view,float);m=np.asarray(projection,float);size=np.asarray(viewport,float)
 if p.ndim!=2 or p.shape[1]!=3 or v.shape!=(4,4)or m.shape!=(4,4)or size.shape!=(2,)or(size<=0).any()or not np.isfinite(np.r_[p.ravel(),v.ravel(),m.ravel(),size]).all():raise ValueError('finite XYZ/view/projection/viewport ABI')
 clip=np.c_[p,np.ones(len(p))]@v.T@m.T
 if(clip[:,3]<=0).any():raise ValueError('unsupported point at/behind projection eye')
 ndc=clip[:,:2]/clip[:,3,None]
 return np.column_stack([(ndc[:,0]+1)*size[0]/2,(1-ndc[:,1])*size[1]/2])

def green_repeat_bilinear(rgba,uv,srgb=False):
 """LOD0 continuous sampler oracle; GPU fixed-point filtering may differ.

 PNG rows are top-first; source UV is bottom-first. The linear/sRGB decision
 must come from the live source format, not the PNG file's display metadata.
 """
 a=np.asarray(rgba);uv=np.asarray(uv,float)
 if a.ndim!=3 or a.shape[2]<2 or uv.ndim!=2 or uv.shape[1]!=2 or not np.isfinite(uv).all():raise ValueError('width texture/UV ABI')
 h,w=a.shape[:2];green=a[::-1,:,1].astype(float)/255
 if srgb:green=np.where(green<=.04045,green/12.92,((green+.055)/1.055)**2.4)
 p=uv*np.array([w,h])-.5;lo=np.floor(p).astype(np.int64);t=p-lo;x,y=lo[:,0]%w,lo[:,1]%h
 return (green[y,x]*(1-t[:,0])+green[y,(x+1)%w]*t[:,0])*(1-t[:,1])+(green[(y+1)%h,x]*(1-t[:,0])+green[(y+1)%h,(x+1)%w]*t[:,0])*t[:,1]

def extrude(points,world_normals,valid,width_metres,green,view,projection,viewport):
 p=np.asarray(points,float);n=np.asarray(world_normals,float);valid=np.asarray(valid,bool);g=np.asarray(green,float)
 if n.shape!=p.shape or valid.shape!=(len(p),)or g.shape!=(len(p),)or not np.isfinite(np.r_[p.ravel(),n.ravel(),g,width_metres]).all()or width_metres<0 or(g<0).any()or(g>1).any():raise ValueError('bounded native width extrusion ABI')
 if not valid.all():raise ValueError('original vertex normal missing; no geometry/effective-normal substitute')
 if np.max(abs(np.linalg.norm(n,axis=1)-1),initial=0)>2e-6:raise ValueError('normalized original normals required')
 start=project(p,view,projection,viewport);end=project(p+n*(width_metres*g)[:,None],view,projection,viewport)
 return {'start':start,'expanded':end,'delta':end-start,'length':np.linalg.norm(end-start,axis=1)}
