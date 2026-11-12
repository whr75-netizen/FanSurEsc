"""Multichannel source-ridge evidence, never source recolouring/semantic labels.

Gaussian derivatives/localization follow the Hessian ridge mechanism. The RGB
Hessian Gram and bilateral native-colour confidence are our extension, not a
claim to reproduce Steger's full profile/width/bias-correction algorithm.
"""
import numpy as np

def kernels(sigma):
 if sigma not in (1.,2.):raise ValueError('two declared native-texel diagnostic scales')
 x=np.arange(-int(4*sigma),int(4*sigma)+1,dtype=float);g=np.exp(-x*x/(2*sigma*sigma));g/=g.sum()
 d=x*g/(sigma*sigma);d/=(d*x).sum()
 dd=(x*x/(sigma**4)-1/(sigma*sigma))*g;dd-=dd.sum()*g;dd*=2/(dd*x*x).sum()
 return g,d,dd

def correlate(a,k,axis):
 r=len(k)//2;pad=[(0,0)]*a.ndim;pad[axis]=(r,r);p=np.pad(a,pad,mode='reflect');out=np.zeros_like(a,dtype=float)
 for i,w in enumerate(k):
  sl=[slice(None)]*a.ndim;sl[axis]=slice(i,i+a.shape[axis]);out+=w*p[tuple(sl)]
 return out

def deriv(a,ky,kx):return correlate(correlate(a,ky,0),kx,1)

def sample(a,x,y):
 h,w=a.shape[:2];x=np.clip(x,0,w-1);y=np.clip(y,0,h-1);ix=np.floor(x).astype(int);iy=np.floor(y).astype(int);fx=(x-ix)[...,None];fy=(y-iy)[...,None];jx=np.minimum(ix+1,w-1);jy=np.minimum(iy+1,h-1)
 return (1-fy)*((1-fx)*a[iy,ix]+fx*a[iy,jx])+fy*((1-fx)*a[jy,ix]+fx*a[jy,jx])

def erode(mask,r):
 out=mask.copy();h,w=mask.shape;p=np.pad(mask,r,constant_values=False)
 for d in range(-r,r+1):out&=p[r+d:r+d+h,r:r+w]
 p=np.pad(out,r,constant_values=False);out=out.copy()
 for d in range(-r,r+1):out&=p[r:r+h,r+d:r+d+w]
 return out

def tile(rgb,mask,sigma):
 a=np.asarray(rgb,float);g,d,dd=kernels(sigma);gx=deriv(a,g,d);gy=deriv(a,d,g);hxx=deriv(a,g,dd);hyy=deriv(a,dd,g);hxy=deriv(a,d,d)
 jxx=np.sum(hxx*hxx+hxy*hxy,axis=2);jyy=np.sum(hyy*hyy+hxy*hxy,axis=2);jxy=np.sum(hxy*(hxx+hyy),axis=2)
 gap=np.hypot(jxx-jyy,2*jxy);theta=.5*np.arctan2(2*jxy,jxx-jyy);nx=np.cos(theta);ny=np.sin(theta)
 curvature=nx[...,None]**2*hxx+2*(nx*ny)[...,None]*hxy+ny[...,None]**2*hyy;strength=np.linalg.norm(curvature,axis=2);axis=np.divide(curvature,strength[...,None],out=np.zeros_like(curvature),where=strength[...,None]>1e-12)
 slope=np.sum(axis*(nx[...,None]*gx+ny[...,None]*gy),axis=2);t=np.divide(-slope,strength,out=np.zeros_like(strength),where=strength>1e-12);tx=t*nx;ty=t*ny
 yy,xx=np.indices(mask.shape);px=xx+tx;py=yy+ty;radius=2*sigma;centre=sample(a,px,py);left=sample(a,px-radius*nx,py-radius*ny);right=sample(a,px+radius*nx,py+radius*ny)
 lc=np.sum((left-centre)*axis,axis=2);rc=np.sum((right-centre)*axis,axis=2);contrast=np.minimum(lc,rc);coding=np.sum(abs(axis),axis=2)
 valid=erode(mask,int(6*sigma+2));eps=32*np.finfo(float).eps*(1+abs(t));localized=(abs(tx)<=.5+eps)&(abs(ty)<=.5+eps)&(strength>1e-10)&(gap>1e-20)
 evidence=valid&localized&(lc>0)&(rc>0)
 # Confidence margin is reported separately. Low-margin observed colours are
 # unknown, not permission to delete authored pixels as noise.
 strong=evidence&(contrast>coding)
 return {'strong':strong,'observed':evidence,'margin':(contrast-coding).astype(np.float32),'nx':nx.astype(np.float32),'ny':ny.astype(np.float32),'px':px.astype(np.float32),'py':py.astype(np.float32),'valid':valid}

def detect(rgba,mask,sigma,tile_size=128):
 a=np.asarray(rgba);mask=np.asarray(mask,bool)
 if a.dtype!=np.uint8 or a.ndim!=3 or a.shape[2]!=4 or mask.shape!=a.shape[:2]or mask.size>1100000:raise ValueError('bounded original native RGBA8/support')
 h,w=mask.shape;valid=mask&(a[:,:,3]==255);halo=int(6*sigma+2);out={k:np.zeros((h,w),dtype=bool if k in ['strong','observed','valid']else np.float32)for k in ['strong','observed','margin','nx','ny','px','py','valid']}
 for y in range(0,h,tile_size):
  for x in range(0,w,tile_size):
   y0=max(0,y-halo);x0=max(0,x-halo);y1=min(h,y+tile_size+halo);x1=min(w,x+tile_size+halo);z=tile(a[y0:y1,x0:x1,:3],valid[y0:y1,x0:x1],float(sigma));hh=min(tile_size,h-y);ww=min(tile_size,w-x)
   for k,v in z.items():
    crop=v[y-y0:y-y0+hh,x-x0:x-x0+ww].copy()
    if k=='px':crop+=x0
    if k=='py':crop+=y0
    out[k][y:y+hh,x:x+ww]=crop
 return out

def consistent(first,second):
 h,w=first['strong'].shape;out=np.zeros((h,w),bool)
 for dy in[-1,0,1]:
  for dx in[-1,0,1]:
   ya,yb=max(0,-dy),min(h,h-dy);xa,xb=max(0,-dx),min(w,w-dx);u=(slice(ya,yb),slice(xa,xb));v=(slice(ya+dy,yb+dy),slice(xa+dx,xb+dx));dot=abs(first['nx'][u]*second['nx'][v]+first['ny'][u]*second['ny'][v]);out[u]|=first['strong'][u]&second['strong'][v]&(dot>=np.sqrt(.5))
 return out
