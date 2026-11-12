"""Exact existing producer-address contract. No Q repair or fitted lighting."""
import numpy as np
def known(cell,owner,source,domain,raw_meta,raw_uv,head_uv,main_uv,cls):
 ordinary=(domain[...,0]<.5)&(cell[...,2]==1)&(source[...,:3]==owner[...,[2,0,1]]).all(-1)
 return ordinary&(raw_meta[...,1]==4)&(raw_uv[...,:2]==head_uv[...,:2]).all(-1)&(head_uv[...,:2]==main_uv[...,:2]).all(-1)&(head_uv[...,2]==cls[...,0])&(source[...,1:]==raw_meta[...,1:]).all(-1)

def geometry(path):
 import struct
 with path.open('rb')as f:
  def integer():return struct.unpack('<i',f.read(4))[0]
  def text():
   n=0;shift=0
   while True:
    b=f.read(1)[0];n|=(b&127)<<shift
    if b<128:break
    shift+=7
   return f.read(n).decode()
  assert text()=='face-source84/v1';sid=text();model=text();frame,renderer,submesh,n,count=[integer()for _ in range(5)];assert 0<n<100000 and 0<count<1000000 and count%3==0;view=np.frombuffer(f.read(64),'<f4').reshape(4,4,order='F').copy();v=np.frombuffer(f.read(n*28),'<f4').reshape(n,7).copy();tri=np.frombuffer(f.read(count*4),'<i4').reshape(-1,3).copy();assert not f.read()and(tri>=0).all()and(tri<n).all();return {'sourceId':sid,'model':model,'frame':frame,'renderer':renderer,'submesh':submesh,'view':view,'v':v,'tri':tri}

def barycentric_uv(points,uv):
 a,b,c=points;ab=b-a;ac=c-a;det=ab[0]*ac[1]-ab[1]*ac[0]
 if det==0:return None
 d=uv-a;u=(d[0]*ac[1]-d[1]*ac[0])/det;v=(ab[0]*d[1]-ab[1]*d[0])/det;return np.array([1-u-v,u,v])
