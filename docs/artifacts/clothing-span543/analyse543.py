from pathlib import Path
import struct,json
import numpy as np
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;R=O/'Adjacent543';frames=[34,43,44,50,64,65,66];modes=['BASE','SHAPE','INK','BOTH']
def read(path):
 b=path.read_bytes();w,h,x,y=struct.unpack_from('<4i',b);a=np.zeros((272,480,4),np.float32);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return a
def mask(path):
 b=path.read_bytes();x,y,w,h=struct.unpack_from('<4i',b);a=np.zeros((272,480),bool);a[y:y+h,x:x+w]=np.frombuffer(b,'?',w*h,16+4*w*h).reshape(h,w);return a
rows=[]
for f in frames:
 if not all((R/f'{f:03d}_{m}_stage.json').exists()for m in modes):continue
 values={m:{s:read(R/f'{f:03d}_{m}_{s}.bin')for s in ['FINAL','META','UV','PREPARED','BEFORE','POSTLINE']}for m in modes};base=values['BASE'];row={'frame':f,'modes':{}}
 for mode in modes:
  a=values[mode];changed=np.max(np.abs(a['FINAL']-base['FINAL']),axis=2)>1e-6;face=((base['META'][:,:,1]>=1)&(base['META'][:,:,1]<=7)&(base['FINAL'][:,:,3]>.5))|((a['META'][:,:,1]>=1)&(a['META'][:,:,1]<=7)&(a['FINAL'][:,:,3]>.5));hair=((base['META'][:,:,1]>=12)&(base['FINAL'][:,:,3]>.5))|((a['META'][:,:,1]>=12)&(a['FINAL'][:,:,3]>.5));parts={}
  for p in [1,2,3]:
   bm=mask(R/f'{f:03d}_BASE_PART{p}.bin');am=mask(R/f'{f:03d}_{mode}_PART{p}.bin');parts[p]={'addedXY':np.argwhere(am&~bm)[:,::-1].tolist(),'removedXY':np.argwhere(bm&~am)[:,::-1].tolist()}
  cells={f'{x},{y}':{s:a[s][y,x].tolist()for s in a}for x,y in [(201,73),(201,74)]}if f in [64,65,66]else{}
  row['modes'][mode]={'changedFinal':int(changed.sum()),'faceEyeChanged':int((changed&face).sum()),'hairChanged':int((changed&hair).sum()),'coverageAdded':int(((a['FINAL'][:,:,3]>.5)&(base['FINAL'][:,:,3]<.5)).sum()),'coverageRemoved':int(((a['FINAL'][:,:,3]<.5)&(base['FINAL'][:,:,3]>.5)).sum()),'parts':parts,'elbow':cells,'stage':json.loads((R/f'{f:03d}_{mode}_stage.json').read_text())}
 rows.append(row)
result={'status':json.loads((R/'status.json').read_text()),'completedPairs':len(rows)*4,'rows':rows,'note':'Same execution and pose; shape and ink are separate ablations. Source role, UV, depth and RGB buffers retained. Sparse causal views do not replace full animation validation.'}
(O/'ADJACENT_RESULT543.json').write_text(json.dumps(result,indent=2));print(json.dumps({'status':result['status'],'completedPairs':result['completedPairs'],'rows':[{'frame':r['frame'],'modes':{k:{q:v[q]for q in ['changedFinal','faceEyeChanged','hairChanged','coverageAdded','coverageRemoved','parts']}for k,v in r['modes'].items()}}for r in rows]}))
if len(rows)==7:
 for f in [64,65,66]:
  out=Image.new('RGB',(4*256,600),'white');d=ImageDraw.Draw(out)
  for i,m in enumerate(modes):
   im=Image.open(R/f'{f:03d}_{m}.png').convert('RGB');out.paste(im.crop((350,52,550,342)),(i*256,22));out.paste(im.crop((392,112,438,180)).resize((184,272),Image.Resampling.NEAREST),(i*256,315));d.text((i*256+3,3),f'Actual Walk{f} {m}',fill='black')
  out.save(O/f'ELBOW543_{f}.png')
