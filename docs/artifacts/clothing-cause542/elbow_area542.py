from pathlib import Path
import struct,json,numpy as np
O=Path(__file__).resolve().parent;R=O.parent/'Common540/FullLoop540'
def region(f):
 b=(R/f'{f:03d}_CLOTH_PART3.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',b);at=16;area=np.frombuffer(b,'<f4',w*h,at).reshape(h,w);at+=4*w*h;mask=np.frombuffer(b,'?',w*h,at).reshape(h,w);at+=w*h;groups=[]
 for _ in range(2):
  n,=struct.unpack_from('<i',b,at);at+=4;rings=[]
  for _ in range(n):
   k,=struct.unpack_from('<i',b,at);at+=4;rings.append(np.frombuffer(b,'<f4',2*k,at).reshape(k,2).astype(float));at+=8*k
  groups.append(rings)
 return x,y,area,mask,groups
def line(xs,yy):
 hits=[]
 for r in xs:
  for a,b in zip(r,np.roll(r,-1,axis=0)):
   if(a[1]<=yy<b[1])or(b[1]<=yy<a[1]):hits.append(float(a[0]+(b[0]-a[0])*(yy-a[1])/(b[1]-a[1])))
 return sorted(hits)
rows=[]
for f in range(63,69):
 ox,oy,a,m,groups=region(f);cells=[]
 for y in [72,73,74,75,76]:
  cells.append({'xy':[201,y],'area':float(a[y-oy,201-ox]),'selected':bool(m[y-oy,201-ox]),'sourceXsAtCentre':line(groups[0],y+.5),'curveXsAtCentre':line(groups[1],y+.5)})
 rows.append({'frame':f,'cells':cells,'rowMinimumX':{str(y):int(np.where(m[y-oy])[0][0])+ox for y in range(69,80)}})
(O/'ELBOW_AREA542.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
