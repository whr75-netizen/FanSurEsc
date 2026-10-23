from pathlib import Path
import sys,json,struct
from collections import deque
import numpy as np
O=Path(__file__).resolve().parent;R=O/'FullLoop543';sys.path.insert(0,str(O.parent/'BodyRay541'))
from model542 import load
_,_,_,_,_,tags=load();lookup={int(t[2]):int(t[0])for group in tags for t in group}
def read(f,m,s):
 b=(R/f'{f:03d}_{m}_{s}.bin').read_bytes();w,h,x,y=struct.unpack_from('<4i',b);a=np.zeros((272,480,4),np.float32);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return a
events=[e for e in json.loads((O/'FULL_RESULT543.json').read_text())['sameSurfaceColourEvents']if round(e['owner'][1])==8];out=[]
for e in events:
 f=e['frame'];x,y=e['xy'];row={'frame':f,'xy':[x,y],'sourcePacket':e['owner'],'modes':{}}
 for m in ['CLOTH','SPAN']:
  a=read(f,m,'PREPARED');meta=read(f,m,'META');covered=a[:,:,3]>0;parts=np.zeros((272,480),int)
  for yy,xx in np.argwhere(covered):parts[yy,xx]=lookup.get(round(abs(float(meta[yy,xx,3]))),0)
  ext=np.zeros_like(covered);q=deque()
  for yy in range(272):
   for xx in [0,479]:
    if not covered[yy,xx]:ext[yy,xx]=True;q.append((xx,yy))
  for xx in range(1,479):
   for yy in [0,271]:
    if not covered[yy,xx]:ext[yy,xx]=True;q.append((xx,yy))
  while q:
   xx,yy=q.popleft()
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    px,py=xx+dx,yy+dy
    if 0<=px<480 and 0<=py<272 and not covered[py,px]and not ext[py,px]:ext[py,px]=True;q.append((px,py))
  part=int(parts[y,x]);dirs=[]
  for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
   core=all(covered[y-k*dy,x-k*dx]and(part not in [2,3,4,5]or parts[y-k*dy,x-k*dx]==part)for k in [1,2]);dirs.append({'d':[dx,dy],'exterior':bool(ext[y+dy,x+dx]),'ownCore':bool(core)})
  def three(dx,dy):
   a,b=parts[y-dy,x-dx]==part,parts[y+dy,x+dx]==part;return bool((a and b)or(a and parts[y-2*dy,x-2*dx]==part)or(b and parts[y+2*dy,x+2*dx]==part))
  outer=any(d['exterior']for d in dirs);thin=any(d['exterior']and not d['ownCore']for d in dirs)or(part in[2,3,4,5]and(not three(1,0)or not three(0,1)))
  row['modes'][m]={'part':part,'outer':outer,'thin':thin,'predictedOuterReason':int(outer and not thin),'dirs':dirs,'covered5x5':covered[y-2:y+3,x-2:x+3].astype(int).tolist(),'parts5x5':parts[y-2:y+3,x-2:x+3].tolist()}
 out.append(row)
(O/'BODY_COLOUR_NEIGHBOURS543.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
