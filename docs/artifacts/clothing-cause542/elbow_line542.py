from pathlib import Path
import numpy as np,struct,json
from collections import deque
from model542 import load
O=Path(__file__).resolve().parent;R=O.parent/'Common540/FullLoop540';bones,v,bi,bw,indices,tags=load();lookup={int(t[2]):int(t[0])for group in tags for t in group}
def read(f,stage):
 b=(R/f'{f:03d}_CLOTH_{stage}.bin').read_bytes();w,h,x,y=struct.unpack_from('<4i',b);o=np.zeros((272,480,4),np.float32);o[y:y+h,x:x+w]=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return o
rows=[]
for f in [64,65,66]:
 before=read(f,'PREPARED');post=read(f,'POSTLINE');meta=read(f,'META');covered=before[:,:,3]>0;parts=np.zeros((272,480),int)
 for y,x in np.argwhere(covered):parts[y,x]=lookup.get(int(round(abs(meta[y,x,3]))),6 if meta[y,x,1]<=7 else 7)
 ext=np.zeros((272,480),bool);q=deque()
 for y in range(272):
  for x in [0,479]:
   if not covered[y,x]and not ext[y,x]:ext[y,x]=True;q.append((x,y))
 for x in range(480):
  for y in [0,271]:
   if not covered[y,x]and not ext[y,x]:ext[y,x]=True;q.append((x,y))
 while q:
  x,y=q.popleft()
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   xx,yy=x+dx,y+dy
   if 0<=xx<480 and 0<=yy<272 and not covered[yy,xx]and not ext[yy,xx]:ext[yy,xx]=True;q.append((xx,yy))
 for x,y in [(201,73),(201,74)]:
  part=int(parts[y,x]);horizontal=[int(parts[y,x+d])for d in [-2,-1,1,2]];vertical=[int(parts[y+d,x])for d in [-2,-1,1,2]]
  def three(a):return(a[1]==part and a[2]==part)or(a[1]==part and a[0]==part)or(a[2]==part and a[3]==part)
  directions=[]
  for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
   outside=bool(ext[y+dy,x+dx]);core=bool(covered[y-dy,x-dx]and covered[y-2*dy,x-2*dx]and parts[y-dy,x-dx]==part and parts[y-2*dy,x-2*dx]==part);directions.append({'d':[dx,dy],'exterior':outside,'ownCore':core})
  outer=any(d['exterior']for d in directions);thin=any(d['exterior']and not d['ownCore']for d in directions)or(part>=2 and part<=5 and(not three(horizontal)or not three(vertical)))
  rows.append({'frame':f,'xy':[x,y],'covered':bool(covered[y,x]),'part':part,'horizontalPartsMinus2Minus1Plus1Plus2':horizontal,'verticalPartsMinus2Minus1Plus1Plus2':vertical,'hasThreeHorizontal':three(horizontal),'hasThreeVertical':three(vertical),'directions':directions,'outer':outer,'thin':thin,'predictedOuterReason':1 if covered[y,x]and outer and not thin else 0,'before':before[y,x].tolist(),'postLine':post[y,x].tolist()})
(O/'ELBOW_LINE542.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
