"""Conservative visible-area intervals from captured source polygons.

Opaque, in-front actor polygons remove only their own intersection. Unknown
alpha/depth removes lower-bound evidence, never becomes transparent. This is a
CPU oracle, not a claim of real-time GPU integration or exact GPU raster area.
"""
import numpy as np
from actor_visibility96 import wrap

def area(p):
 p=np.asarray(p,float)
 if len(p)<3:return 0.
 q=p-p[0];r=np.roll(q,-1,axis=0);return float(abs((q[:,0]*r[:,1]-q[:,1]*r[:,0]).sum())*.5)

def area_roundoff(p):
 """Keep roundoff slivers UNKNOWN rather than evidence of visible support.

 This arithmetic diagnostic is separate from the float32 source interval in
 visible(). It never deletes upper-bound polygons or declares them transparent.
 """
 p=np.asarray(p,float)
 if len(p)<3:return 0.
 q=p-p[0];extent=float(abs(q).max());coordinate=float(abs(p).max());n=len(p)
 return 64*n*np.finfo(float).eps*(1+coordinate)*(extent+np.finfo(float).eps*(1+coordinate))

def positive_area_evidence(polygons):
 return float(sum(max(0.,area(p)-area_roundoff(p))for p in polygons))

def half(p,n,c):
 if len(p)<3:return np.empty((0,2))
 out=[];old=p[-1];a=float(old@n+c)
 for new in p:
  b=float(new@n+c)
  if(a<=0)!=(b<=0):out.append(old+(new-old)*(a/(a-b)))
  if b<=0:out.append(new)
  old=new;a=b
 result=np.asarray(out,float).reshape(-1,2);return result if area(result)>0 else np.empty((0,2))

def edges(p):
 a=p-p[0];b=np.roll(p,-1,axis=0)-p[0]
 if(a[:,0]*b[:,1]-a[:,1]*b[:,0]).sum()<0:p=p[::-1]
 for a,b in zip(p,np.roll(p,-1,axis=0)):
  d=b-a;n=np.array([d[1],-d[0]]);yield n,-float(n@a)

def intersect(p,q):
 for n,c in edges(q):
  p=half(p,n,c)
  if not len(p):break
 return p

def difference(p,q):
 out=[];inside=p
 for n,c in edges(q):
  outside=half(inside,-n,-c)
  if len(outside):out.append(outside)
  inside=half(inside,n,c)
  if not len(inside):break
 return out

def subtract(polygons,q,budget=256):
 result=[]
 for p in polygons:
  if np.any(p.max(0)<q.min(0))or np.any(q.max(0)<p.min(0)):result.append(p)
  else:result.extend(difference(p,q))
  if len(result)>budget:raise ValueError('bounded visible-polygon budget; result unknown')
 return result

def plane(xy,z):
 gradient=np.linalg.solve(xy[1:]-xy[0],np.asarray(z)[1:]-z[0]);return gradient,float(z[0]-gradient@xy[0])

def alpha_interval(query,material,row,index,p,position_error=0.):
 if query.spec['alphaTestGlobal']or query.spec['alphaBlendGlobal']or any(v!=0 for v in material['scroll']):return 'unknown'
 if not material['alphaTest']and not material['alphaBlend']:return 'opaque'
 texture=query.tex[material['texture']]if material['texture']>=0 else None
 if texture is None or texture['index']not in query.alpha:return 'unknown'
 data=query.alpha[texture['index']]
 if texture['mipCount']!=1:return 'unknown'
 xy=row['xy'][index];uv=row['uv'][index];matrix=np.linalg.solve((xy[1:]-xy[0]).T,(p-xy[0]).T).T;values=uv[0]+matrix[:,0,None]*(uv[1]-uv[0])+matrix[:,1,None]*(uv[2]-uv[0]);values=values*material['scale']+material['offset'];size=np.array([texture['width'],texture['height']]);at=values*size-(0 if texture['filter']=='Point' else .5);uv_gradient=np.linalg.solve(xy[1:]-xy[0],uv[1:]-uv[0]);padding=np.ceil(position_error*np.abs(uv_gradient).sum(0)*np.abs(material['scale'])*size+8*np.finfo(np.float32).eps*(1+np.abs(values).max(0))*size).astype(int);lo=np.floor(at.min(0)).astype(int)-padding;hi=np.floor(at.max(0)).astype(int)+(0 if texture['filter']=='Point' else 1)+padding
 if int(np.prod(hi-lo+1))>65536:return 'unknown'
 xs=wrap(np.arange(lo[0],hi[0]+1),size[0],texture['wrapU']);ys=wrap(np.arange(lo[1],hi[1]+1),size[1],texture['wrapV']);v=data[np.ix_(ys,xs)];low=float(np.float16(np.float16(float(v.min())/255)*np.float16(material['color'][3])));high=float(np.float16(np.float16(float(v.max())/255)*np.float16(material['color'][3])))
 if material['alphaTest']:
  if low>=material['cutoff']:return 'opaque'
  if high<material['cutoff']:return 'clear'
  return 'unknown'
 return 'clear'if high<=1e-6 else'unknown'

def visible(query,polygon,line_xy,line_z,shift=np.zeros(2),exclude=None):
 upper=[polygon];lower=[polygon];line_gradient,line_c=plane(line_xy,line_z);lo,hi=polygon.min(0),polygon.max(0);known_count=unknown_count=0
 # Error interval accounts for float32 projection/depth arithmetic. This is
 # uncertainty, not permission to pass an occluder or a world-space bias.
 eps=np.finfo(np.float32).eps;projection_error=8*eps*(1+max(abs(lo).max(),abs(hi).max()));line_error=16*eps*(1+max(abs(np.asarray(line_z))))
 for row in query.rows:
  material=query.materials[row['renderer'],row['submesh']];xyall=row['xy']+shift;rl=row['lo']+shift;rh=row['hi']+shift;valid=(row['det']!=0)&(rh+projection_error>=lo).all(1)&(rl-projection_error<=hi).all(1)
  if material['cull']==2:valid&=row['det']>0
  elif material['cull']==1:valid&=row['det']<0
  elif material['cull']!=0:raise ValueError('unsupported source culling')
  for index in np.flatnonzero(valid):
   if exclude==(row['renderer'],row['submesh'],int(index)):continue
   xy=xyall[index];possible_polygon=polygon;certain_polygon=polygon
   for n,c in edges(xy):
    distance=projection_error*np.linalg.norm(n);possible_polygon=half(possible_polygon,n,c-distance);certain_polygon=half(certain_polygon,n,c+distance)
    if not len(possible_polygon):break
   if not len(possible_polygon):continue
   gradient,c=plane(xy,row['z'][index]);diff=gradient-line_gradient;constant=c-line_c;error=line_error+16*eps*(1+max(abs(row['z'][index])))+projection_error*(abs(gradient).sum()+abs(line_gradient).sum());possible=half(possible_polygon,diff,constant-error)
   if not len(possible):continue
   # Alpha UVs use original actor coordinates before the common head shift.
   status=alpha_interval(query,material,row,index,possible-shift,projection_error)
   if status=='clear':continue
   certain=half(certain_polygon,diff,constant+error)if status=='opaque'and len(certain_polygon)else np.empty((0,2))
   if len(certain):upper=subtract(upper,certain);known_count+=1
   lower=subtract(lower,possible);unknown_count+=int(status=='unknown')
   if not upper:return {'lower':[],'upper':[],'knownOccluders':known_count,'unknownAlphaOccluders':unknown_count,'lowerArea':0.,'upperArea':0.}
 return {'lower':lower,'upper':upper,'knownOccluders':known_count,'unknownAlphaOccluders':unknown_count,'lowerArea':sum(area(p)for p in lower),'upperArea':sum(area(p)for p in upper)}
