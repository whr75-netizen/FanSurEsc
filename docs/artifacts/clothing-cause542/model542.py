from pathlib import Path
import struct,numpy as np
O=Path(__file__).resolve().parent
def load():
 b=(O/'BODY_BONES542.bin').read_bytes();at=0
 def integer():
  nonlocal at
  v,=struct.unpack_from('<i',b,at);at+=4;return v
 def string():
  nonlocal at
  n=shift=0
  while True:
   q=b[at];at+=1;n|=(q&127)<<shift;shift+=7
   if q<128:break
  s=b[at:at+n].decode('utf8');at+=n;return s
 bones=[(string(),string())for _ in range(integer())];n=integer();verts=[];boneids=[];weights=[]
 for _ in range(n):
  verts.append(struct.unpack_from('<5f',b,at));at+=20;v=struct.unpack_from('<ifififif',b,at);at+=32;boneids.append(v[::2]);weights.append(v[1::2])
 indices=[]
 for _ in range(integer()):
  count=integer();indices.append(np.frombuffer(b,'<i4',count,at).copy().reshape(-1,3));at+=4*count
 raw=(O/'BODY_PARTS542.bin').read_bytes();pos=8;tags=[]
 for sm in range(len(indices)):
  role,count=struct.unpack_from('<2i',raw,pos);pos+=8;check=np.frombuffer(raw,'<i4',count*3,pos).reshape(-1,3);pos+=count*12;assert np.array_equal(check,indices[sm]);tags.append(np.frombuffer(raw,'<i4',count*3,pos).copy().reshape(-1,3));pos+=count*12
 return bones,np.array(verts),np.array(boneids),np.array(weights),indices,tags
def geometry(frame):
 b=(O/f'ActualInputs/{frame}_15_BODY_GEOMETRY.bin').read_bytes();n,=struct.unpack_from('<i',b);return np.frombuffer(b,'<f4',9*n,4).reshape(n,9)
if __name__=='__main__':
 bones,v,bi,bw,indices,tags=load();g=geometry(35);names=[h for n,h in bones];print('arm bones',[(i,p)for i,p in enumerate(bones)if'Arm'in p[0]or'Arm'in p[1]])
 for hand in ['Left','Right']:
  upper=[i for i,h in enumerate(names)if h==hand+'UpperArm'];lower=[i for i,h in enumerate(names)if h==hand+'LowerArm'];wu=(bw*np.isin(bi,upper)).sum(axis=1);wl=(bw*np.isin(bi,lower)).sum(axis=1)
  for sm,ids in enumerate(indices):
   used=np.unique(ids);near=used[(wu[used]>0)&(wl[used]>0)];allarm=used[(wu[used]+wl[used])>0]
   if len(near):print(hand,'submesh',sm,'mixedElbow',len(near),'boundsXY',g[near,3:5].min(axis=0),g[near,3:5].max(axis=0),'allArmBounds',g[allarm,3:5].min(axis=0),g[allarm,3:5].max(axis=0),'tags',np.unique(tags[sm][np.any(np.isin(ids,near),axis=1),0],return_counts=True))
