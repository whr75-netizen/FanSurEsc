"""Exact source-UV carrier paths, distinct from colour/feature region labels.

Only edge-adjacent triangles in the verified native face primitive may carry a
straight UV segment. Disconnected/overlapping UV islands do not imply adjacency.
No normal threshold, colour clustering or renderer/GPU call is used.
"""
from pathlib import Path
import hashlib,json,struct
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
class UVSurface:
 def __init__(self,uv,indices):
  self.uv=np.asarray(uv,float);self.indices=np.asarray(indices,int);self.tri=self.uv[self.indices];self.adj=[[]for _ in self.indices];edges={}
  for i,t in enumerate(self.indices):
   for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:edges.setdefault(tuple(sorted((int(a),int(b)))),[]).append(i)
  self.nonmanifold=[]
  for edge,ids in edges.items():
   if len(ids)==2:
    a,b=ids;self.adj[a].append(b);self.adj[b].append(a)
   elif len(ids)>2:self.nonmanifold.append(edge)
  a=self.tri[:,0];b=self.tri[:,1]-a;c=self.tri[:,2]-a;det=b[:,0]*c[:,1]-b[:,1]*c[:,0];self.good=abs(det)>1e-14;self.inv=np.zeros((len(a),2,2));self.inv[self.good]=np.stack([c[self.good,1],-c[self.good,0],-b[self.good,1],b[self.good,0]],1).reshape(-1,2,2)/det[self.good,None,None]
 def path(self,p0,p1,start,end):
  if not(0<=start<len(self.tri)and 0<=end<len(self.tri)):return {'known':False,'cause':'primitive out of range'}
  # 2e-7 UV covers source float32 interpolation/Unity V-flip arithmetic. It is
  # not a colour or surface-smoothing threshold. Report endpoint errors.
  eps=2e-7;delta=np.asarray(p1)-p0;base=np.einsum('nij,nj->ni',self.inv,np.asarray(p0)-self.tri[:,0]);slope=np.einsum('nij,j->ni',self.inv,delta);b=np.c_[1-base.sum(1),base];d=np.c_[-slope.sum(1),slope]
  if not self.good[start]or not self.good[end]or b[start].min()<-eps or (b[end]+d[end]).min()<-eps:return {'known':False,'cause':'source primitive/UV endpoint mismatch','startMinBary':float(b[start].min()),'endMinBary':float((b[end]+d[end]).min())}
  low=np.zeros(len(b));high=np.ones(len(b));valid=self.good.copy()
  for j in range(3):
   pos=d[:,j]>1e-15;neg=d[:,j]<-1e-15;flat=~(pos|neg);valid&=~(flat&(b[:,j]<-eps));cross=np.divide(-eps-b[:,j],d[:,j],out=np.zeros(len(b)),where=~flat);low[pos]=np.maximum(low[pos],cross[pos]);high[neg]=np.minimum(high[neg],cross[neg])
  valid&=low<=high;todo=[start];seen={start};parent={start:None}
  for a in todo:
   if a==end:
    chain=[]
    while a is not None:chain.append(a);a=parent[a]
    return {'known':True,'triangles':chain[::-1],'visits':len(seen),'minInterval':float(min(high[i]-low[i]for i in chain))}
   for n in self.adj[a]:
    if n not in seen and valid[n]and max(low[a],low[n])<=min(high[a],high[n])+eps:seen.add(n);parent[n]=a;todo.append(n)
  return {'known':False,'cause':'UV segment crosses a source boundary/gap/nonmanifold edge','visits':len(seen)}
def native():
 registry=json.loads((R/'renderer-family59/SOURCE_REGISTRY59.json').read_text());binding=[b for b in registry['bindings']if b['rendererOrdinal']==1 and b['subMesh']==3];assert len(binding)==1;binding=binding[0]
 data=(Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')/registry['modelAsset']).read_bytes();assert hashlib.sha256(data).hexdigest()==registry['modelSHA256'];chunks={};at=12
 while at<len(data):n,t=struct.unpack_from('<II',data,at);at+=8;chunks[t]=data[at:at+n];at+=n
 doc=json.loads(chunks[0x4e4f534a]);blob=chunks[0x004e4942]
 def acc(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];assert not a.get('normalized')and not a.get('sparse');dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]);dim={'SCALAR':1,'VEC2':2}[a['type']];return np.ndarray((a['count'],dim),dt,buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*dim),dt.itemsize)).copy()
 p=doc['meshes'][binding['gltfMesh']]['primitives'][binding['gltfPrimitive']];uv=acc(p['attributes']['TEXCOORD_0']);uv[:,1]=np.float32(1)-uv[:,1];indices=acc(p['indices']).reshape(-1,3).astype('<u4')[:,[2,1,0]]
 assert hashlib.sha256(uv.astype('<f4').tobytes()).hexdigest()==binding['meshUVSHA256'];assert hashlib.sha256(indices.copy().tobytes()).hexdigest()==binding['indexSHA256'];return UVSurface(uv,indices),binding
def main():
 g=H/'face34';c=g/'capture';out=g/'analysis';r=json.loads((c/'COMPLETE.json').read_text());w,h=r['QROI'][2:];field=lambda n:np.fromfile(c/(n+'-row0000.f32'),dtype='<f4').reshape(h,w,4);meta,uv=field('q7'),field('q9');face=np.rint(meta[:,:,1])==4;surface,binding=native();paths=[]
 for y,x in np.argwhere(face):
  for dx,dy in [(1,0),(0,1),(1,1),(-1,1)]:
   xx,yy=x+dx,y+dy
   if not(0<=xx<w and 0<=yy<h and face[yy,xx]):continue
   a=int(round(meta[y,x,3]))-1;b=int(round(meta[yy,xx,3]))-1;p=surface.path(uv[y,x,:2],uv[yy,xx,:2],a,b);paths.append({'a':[int(x),int(y)],'b':[int(xx),int(yy)],**p})
 result={'sourceId':r['frameKey'],'binding':binding,'pathCount':len(paths),'known':sum(p['known']for p in paths),'unknown':sum(not p['known']for p in paths),'maxTriangleVisits':max(p.get('visits',0)for p in paths),'nonmanifoldEdges':len(surface.nonmanifold),'colourRegionAssigned':False,'paths':paths};(out/'SOURCE_PATHS34.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items()if k not in ['binding','paths']},indent=2))
if __name__=='__main__':main()
