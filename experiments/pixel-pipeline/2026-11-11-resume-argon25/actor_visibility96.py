"""CPU queries of captured evaluated actor geometry and original readable alpha.

No nearest-skin substitution, world geometry inference, or GPU result replay.
Transparent/unsupported alpha remains unknown rather than treated as empty.
"""
from pathlib import Path
import json,struct,hashlib,zipfile,numpy as np
from native_width86 import text
from frame_bytes77 import decode

def packet(root,f):
 w=f['QROI'][2];n=(2*w+1)**2;info=f['sourceFootprint95'];assert info['currentFrame']==f['frame']and info['presentSerial']==f['nativeSerial']and info['worldSerial']==f['worldSerial'];path=root/'capture'/f['compressedFile']
 if path.is_file():encoded=path.read_bytes()
 else:
  # Repository99 stores exact original R77 records in a lossless archive.
  # Do not extract/replace evidence or synthesize missing packets.
  assert Path(f['compressedFile']).name==f['compressedFile']
  with zipfile.ZipFile(root/'capture/PACKETS99.zip')as archive:
   entry=archive.getinfo(f['compressedFile']);assert 0<entry.file_size<=2*f['bytes'];encoded=archive.read(entry)
 payload=decode(encoded,f['bytes']);assert hashlib.sha256(payload).hexdigest()==f['rawSHA256'];raw=np.frombuffer(payload,'<f4').reshape(-1,4);assert raw.shape==(24*w*w,4)and np.isfinite(raw).all();world=raw[:n].reshape(2*w+1,2*w+1,4);depth=raw[n:2*n].reshape(2*w+1,2*w+1,4);a=raw[2*n:2*n+14*w*w].reshape(14,w,w,4);assert(raw[2*n+14*w*w:]==0).all();first=np.array(info['worldFirst']);x,y=np.meshgrid(np.arange(2*w+1),np.arange(2*w+1));assert np.array_equal(depth[:,:,2],x+first[0])and np.array_equal(depth[:,:,3],y+first[1]);expected=(1-depth[:,:,1]if info['reversedZ']else depth[:,:,1])*(info['far']-info['near'])+info['near'];assert np.max(abs(expected-depth[:,:,0]))<=max(1e-4,abs(info['far'])*2e-7);return a,world,depth

def actor(path):
 with path.open('rb')as f:
  assert text(f)=='actor-source96/v1';sid=text(f);frame=struct.unpack('<i',f.read(4))[0];view=np.frombuffer(f.read(64),'<f4').reshape(4,4,order='F').copy();count=struct.unpack('<i',f.read(4))[0];assert 0<count<=16;meshes=[]
  for _ in range(count):
   renderer,n,subs=struct.unpack('<iii',f.read(12));assert 0<n<65536 and 0<subs<=16;v=np.frombuffer(f.read(n*28),'<f4').reshape(n,7).copy();tri={}
   for j in range(subs):
    sub,k=struct.unpack('<ii',f.read(8));assert 0<k<=196608 and k%3==0;tri[sub]=np.frombuffer(f.read(k*4),'<i4').reshape(-1,3).copy();assert(tri[sub]>=0).all()and(tri[sub]<n).all()
   meshes.append({'renderer':renderer,'v':v,'tri':tri})
  assert not f.read();return {'sourceId':sid,'frame':frame,'view':view,'meshes':meshes}

def wrap(q,n,mode):
 if mode=='Repeat':return q%n
 if mode=='Clamp':return np.clip(q,0,n-1)
 if mode=='Mirror':
  q=q%(2*n);return np.where(q<n,q,2*n-1-q)
 raise ValueError('unsupported source sampler '+mode)

class ActorQuery:
 def __init__(self,root,f):
  self.root=root;self.f=f;self.g=actor(root/'capture'/f['actorSource96']['file']);assert self.g['sourceId']==f['sourceId']and self.g['frame']==f['frame'];self.spec=json.loads((root/'capture/ACTOR_MATERIALS96.json').read_text());self.materials={(m['renderer'],m['submesh']):m for m in self.spec['materials']};self.table={(m['renderer'],m['subMesh']):m for m in json.loads((root/'capture/SOURCE_TABLE77.json').read_text())};self.tex=self.spec['textures'];self.alpha={};self.rows=[]
  verified=root/'capture/VALIDATED_ALPHA96.json';validated={t['index']:t for t in json.loads(verified.read_text())['textures']}if verified.exists()else{}
  for t in self.tex:
   source=validated.get(t['index'],t if t.get('alphaChannelVerified')else{})
   if source.get('alphaFile'):
    p=root/'capture'/source['alphaFile'];expected=t['width']*t['height']
    if p.exists():
     assert p.stat().st_size==expected;self.alpha[t['index']]=np.memmap(p,dtype=np.uint8,mode='r',shape=(t['height'],t['width']))
    else:
     # Selected repository evidence stores exactly the captured alpha files,
     # compressed losslessly. No extraction, replacement or generated alpha.
     with zipfile.ZipFile(root/'capture/ALPHA96.zip')as archive:
      member=archive.getinfo(source['alphaFile']);assert member.file_size==expected and expected<=4194304;raw=archive.read(member)
     self.alpha[t['index']]=np.frombuffer(raw,np.uint8).reshape(t['height'],t['width'])
  for m in self.g['meshes']:
   v=m['v'].astype(float);p=v[:,5:7].copy();p[:,1]=272-p[:,1];z=-(np.c_[v[:,:3],np.ones(len(v))]@self.g['view'].astype(float).T)[:,2]
   for sub,tri in m['tri'].items():
    xy=p[tri];a=xy[:,0];ab=xy[:,1]-a;ac=xy[:,2]-a;det=ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0];self.rows.append({'renderer':m['renderer'],'submesh':sub,'xy':xy,'a':a,'ab':ab,'ac':ac,'det':det,'z':z[tri],'uv':v[tri,3:5],'lo':xy.min(1),'hi':xy.max(1)})
 def alpha_at(self,m,uv):
  if self.spec['alphaTestGlobal']or self.spec['alphaBlendGlobal']:return None,'global alpha keyword not resolved'
  if any(v!=0 for v in m['scroll']):return None,'animated UV'
  if not m['alphaTest']and not m['alphaBlend']:return 1.,'opaque variant'
  t=self.tex[m['texture']]if m['texture']>=0 else None
  if t is None:return None,'missing source texture'
  if t['index']not in self.alpha:return None,'source alpha unreadable/unsupported'
  values=self.alpha[t['index']]
  if t['mipCount']!=1 and not np.all(values==values.flat[0]):return None,'mip alpha footprint not captured'
  uv=np.asarray(uv)*m['scale']+m['offset'];w,h=t['width'],t['height'];q=uv*[w,h]-.5;lo=np.floor(q).astype(int);d=q-lo
  if t['filter']=='Point':lo=np.floor(uv*[w,h]).astype(int);d=np.zeros(2)
  elif t['filter']not in['Bilinear','Trilinear']:return None,'unsupported source filter'
  xs=wrap(np.array([lo[0],lo[0]+1]),w,t['wrapU']);ys=wrap(np.array([lo[1],lo[1]+1]),h,t['wrapV']);v=values[np.ix_(ys,xs)].astype(float)/255.;a=(v[0,0]*(1-d[0])+v[0,1]*d[0])*(1-d[1])+(v[1,0]*(1-d[0])+v[1,1]*d[0])*d[1];a=float(np.float16(np.float16(a)*np.float16(m['color'][3])))
  if m['alphaTest']:
   if abs(a-m['cutoff'])<=float(np.spacing(np.float16(m['cutoff']))):return None,'half alpha cutoff boundary'
   return(float(a>=m['cutoff'])),'mask'
  if a<=1e-6:return 0.,'transparent empty'
  return None,'partial/blended source'
 def query(self,point):
  point=np.asarray(point,float);hits=[];unknown=[]
  for row in self.rows:
   m=self.materials[row['renderer'],row['submesh']];det=row['det'];good=(det!=0)&(point>=row['lo']).all(1)&(point<=row['hi']).all(1)
   if m['cull']==2:good&=det>0
   elif m['cull']==1:good&=det<0
   elif m['cull']!=0:continue
   ids=np.flatnonzero(good);d=point-row['a'][ids];ab=row['ab'][ids];ac=row['ac'][ids];u=(d[:,0]*ac[:,1]-d[:,1]*ac[:,0])/det[ids];v=(ab[:,0]*d[:,1]-ab[:,1]*d[:,0])/det[ids];inside=(u>=0)&(v>=0)&(u+v<=1)
   for i,a,b in zip(ids[inside],u[inside],v[inside]):
    bary=np.array([1-a-b,a,b]);z=float(bary@row['z'][i]);uv=bary@row['uv'][i];alpha,reason=self.alpha_at(m,uv);hit={'renderer':row['renderer'],'submesh':row['submesh'],'role':self.table[row['renderer'],row['submesh']]['role'],'primitive':int(i)+1,'depth':z,'uv':uv.tolist(),'alpha':alpha,'alphaReason':reason}
    if alpha is None:unknown.append(hit)
    elif alpha>0:hits.append(hit)
  hits.sort(key=lambda h:(h['depth'],h['renderer'],h['submesh'],h['primitive']));unknown.sort(key=lambda h:h['depth']);near=hits[0]if hits else None;uncertain=[h for h in unknown if near is None or h['depth']<=near['depth']];return {'hit':near,'unknownInFront':uncertain,'opaqueCandidates':len(hits),'known':not uncertain}
