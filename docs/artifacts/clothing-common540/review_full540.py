from pathlib import Path
import json,struct
import numpy as np
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;R=O/'FullLoop540'
def read(p):
 b=p.read_bytes();w,h,x,y=struct.unpack_from('<4i',b);o=np.zeros((272,480,4),np.float32);o[y:y+h,x:x+w]=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return o
ends={}
for mode in ['OFF','CLOTH']:
 a=read(R/f'000_{mode}_FINAL.bin');b=read(R/f'080_{mode}_FINAL.bin');am=read(R/f'000_{mode}_META.bin');bm=read(R/f'080_{mode}_META.bin');d=np.max(np.abs(a-b),axis=2)>1e-6;ends[mode]={'rgbAlphaChanged':int(d.sum()),'coverageChanged':int(np.count_nonzero((a[:,:,3]>.5)!=(b[:,:,3]>.5))),'ownerRoleChanged':int(np.count_nonzero(np.rint(am[:,:,1])!=np.rint(bm[:,:,1]))),'changedXY':np.argwhere(d)[:,::-1].tolist()}
maskends={};geometry=[]
for part in [1,2,3]:
 samples=[]
 for frame in [0,80]:
  b=(R/f'{frame:03d}_CLOTH_PART{part}.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',b);mask=np.zeros((272,480),bool);mask[y:y+h,x:x+w]=np.frombuffer(b,'?',w*h,16+4*w*h).reshape(h,w);at=16+5*w*h;groups=[]
  for group in range(2):
   n,=struct.unpack_from('<i',b,at);at+=4;rings=[]
   for _ in range(n):
    k,=struct.unpack_from('<i',b,at);at+=4;rings.append(np.frombuffer(b,'<f4',2*k,at).reshape(k,2));at+=8*k
   groups.append(rings)
  samples.append((mask,groups))
 maskends[part]=int(np.count_nonzero(samples[0][0]!=samples[1][0]));a,b=samples[0][1][0],samples[1][1][0];same=len(a)==len(b)and all(x.shape==y.shape for x,y in zip(a,b));geometry.append({'part':part,'sourceSameTopology':same,'sourceMaxCoordinateDelta':max(float(np.max(np.abs(x-y)))for x,y in zip(a,b))if same else None})
result={'loopEndpoints':ends,'selectedMasksChangedAtLoopEnds':maskends,'sourceEndpointGeometry':geometry,'endpointInputs':[json.loads((R/f'{f:03d}_pose.json').read_text())for f in [0,80]],'scope':'Actual source clip wraps; endpoints are close but not asserted bit-identical poses. End differences present in both controls are not automatically candidate regressions.'}
(O/'LOOP_REVIEW540.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
files=sorted(O.glob('FULL540_CLOTH_[0-9][0-9][0-9].png'))
if len(files)==81:
 for page in range(9):
  subset=files[page*9:page*9+9];im=Image.open(subset[0]);w,h=im.size;board=Image.new('RGB',(w*3,h*3),'white')
  for i,p in enumerate(subset):board.paste(Image.open(p),(i%3*w,i//3*h))
  board.save(O/f'REVIEW540_{page}.png')
 print('9 contact sheets saved;81 full-body pairs preserved at native integer scale')
