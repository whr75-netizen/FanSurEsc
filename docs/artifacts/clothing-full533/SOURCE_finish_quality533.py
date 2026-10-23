from pathlib import Path
import json,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parent;R=O/'FullLoop';j=json.loads((O/'FULL_RESULT533.json').read_text());c=json.loads((O/'CLASSIFICATION533.json').read_text())
def packet(f):
 b=(R/f'{f:03d}_ALT_LINE_INPUTS.bin').read_bytes();magic,changed,n=struct.unpack_from('<3i',b);dt=np.dtype([('x','<i4'),('y','<i4'),('v','<f4',(2,5,4))]);return{(int(v['x']),int(v['y'])):v['v'].copy()for v in np.frombuffer(b,dt,n,12)}
for q in c['colourRows']:
 if q['classification']=='EXTERNAL_OUTLINE_RECLASSIFICATION':continue
 x,y=q['xy'];s=packet(q['frame']);v=s[x,y];details=[]
 for tag in[0,1]:
  part=round(float(v[tag,1,1]))
  def partat(dx,dy):
   w=s[x+dx,y+dy][tag];return round(float(w[1,1]))if w[0,3]>0 else 0
  def three(dx,dy):
   a=partat(-dx,-dy)==part;b=partat(dx,dy)==part
   return(a and b)or(a and partat(-2*dx,-2*dy)==part)or(b and partat(2*dx,2*dy)==part)
  cores=[]
  for (dx,dy),ext in zip([(-1,0),(1,0),(0,-1),(0,1)],q['branch'][tag]['exterior4']):
   if ext:cores.append(partat(-dx,-dy)==part and partat(-2*dx,-2*dy)==part)
  thin=(not all(cores))or(2<=part<=5 and(not three(1,0)or not three(0,1)))
  assert thin==q['branch'][tag]['thin']
  details.append({'part':part,'hasThreeX':three(1,0),'hasThreeY':three(0,1),'samePartInwardCore':cores,'thin':thin,'partSamples':{str((dx,dy)):partat(dx,dy)for dx,dy in[(-2,0),(-1,0),(1,0),(2,0),(0,-2),(0,-1),(0,1),(0,2)]}})
 q['classification']='VISIBLE_SAME_PART_THICKNESS_OUTLINE_RECLASSIFICATION';q['thicknessReplay']=details
c['colourClassCounts']={k:sum(q['classification']==k for q in c['colourRows'])for k in sorted(set(q['classification']for q in c['colourRows']))}
(O/'CLASSIFICATION533.json').write_text(json.dumps(c,indent=2))
def buf(f,tag,name='FINAL'):
 b=(R/f'{f:03d}_{tag}_{name}.bin').read_bytes();w,h,x,y=struct.unpack_from('<4i',b);q=np.zeros((272,480,4),np.float32);q[y:y+h,x:x+w]=np.frombuffer(b,'<f4',offset=16).reshape(h,w,4);return q
def events(mask):
 out=set()
 for axis in[0,1]:
  a=mask if axis==0 else mask.T
  for side in[0,1]:
   p=[]
   for row in a:
    ids=np.flatnonzero(row);p.append(None if not len(ids)else int(ids[0]if side==0 else ids[-1]))
   for length in[1,2]:
    for i in range(1,len(p)-length):
     v=p[i:i+length];before,after=p[i-1],p[i+length]
     if before is None or after is None or v[0]is None or any(x!=v[0]for x in v):continue
     d1=(before-v[0])if side==0 else(v[0]-before);d2=(after-v[0])if side==0 else(v[0]-after)
     if 1<=d1<=2 and 1<=d2<=2:out.add((axis,side,i,length,v[0],d1,d2))
 return out
spurs=[];masks={}
for f in range(81):
 for tag in['BASE','ALT']:masks[f,tag]=buf(f,tag)[:,:,3]>.5
 b,a=events(masks[f,'BASE']),events(masks[f,'ALT'])
 for e in sorted(a-b):spurs.append({'frame':f,'axis':e[0],'side':e[1],'start':e[2],'span':e[3],'extreme':e[4],'attachmentDepths':list(e[5:]),'classification':'new short return in final actor silhouette; inspect source and temporal context, not automatically an error'})
newTips=[q for q in c['tipCandidates']if(q['frame'],tuple(q['xy']))not in{(p['frame'],tuple(p['xy']))for p in j['tipCandidates']if p['tag']=='BASE'}]
tipProfiles=[]
for q in newTips:
 f=q['frame'];x,y=q['xy'];rows=[]
 for k in[f-1,f,f+1]:
  a=masks[k,'ALT'];yy=range(y-3,y+4);xx=range(x-3,x+4)
  rows.append({'frame':k,'actorRows':[''.join('#'if a[v,u]else'.'for u in xx)for v in yy],'rightmostActorX':[int(np.flatnonzero(a[v])[-1])if a[v].any()else None for v in yy],'actorDegree4':sum(bool(a[y+dy,x+dx])for dx,dy in[(-1,0),(1,0),(0,-1),(0,1)])})
 tipProfiles.append({'frame':f,'xy':[x,y],'spatialRows':rows})
a0=masks[0,'ALT'];a80=masks[80,'ALT'];f0=buf(0,'ALT');f80=buf(80,'ALT');m0=buf(0,'ALT','META');m80=buf(80,'ALT','META');u0=buf(0,'ALT','UV');u80=buf(80,'ALT','UV')
same=a0&a80&(m0[:,:,1]==m80[:,:,1])&(m0[:,:,3]==m80[:,:,3])&(np.max(abs(u0[:,:,:2]-u80[:,:,:2]),2)<2e-5)
loop={'actorAlphaChanged':int((a0!=a80).sum()),'sameApproxSurfaceRGBChangedAbove1e-5':int((same&(np.max(abs(f0[:,:,:3]-f80[:,:,:3]),2)>1e-5)).sum()),'sameApproxSurfaceMaxRGBError':float(np.max(abs(f0[:,:,:3]-f80[:,:,:3])[same])),'skyHours':j['skyHours'],'worldInputsNotAllCaptured':True}
# Correct sheet headers without altering any captured game pixels.
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
for first in[0,45]:
 path=O/f'FULL_ALL_CANDIDATES_{first:03d}_533.png';im=Image.open(path).convert('RGB');d=ImageDraw.Draw(im);cw=im.width//9;ch=Image.open(O/'FULL_CONTACT533.png').height//2
 for k in range(min(45,81-first)):
  x=(k%9)*cw;y=(k//9)*ch;d.rectangle((x,y,x+cw-1,y+39),fill='#eef3f8');d.text((x+4,y+4),f'Walk {first+k:02d} / 532 cloth ON',fill='black',font=font)
 im.save(path)
result={'colourClassCounts':c['colourClassCounts'],'newVisibleClothTipProfiles':tipProfiles,'newActorShortReturnCandidates':spurs,'loop':loop,'scope':'readonly saved-output classification; no new render or product patch','limits':'Short-return detection uses row/column outer profiles; it is a candidate diagnostic, not all contour segments or a pixel-art quality proof.'}
(O/'QUALITY533.json').write_text(json.dumps(result,indent=2));print(json.dumps({'colourClassCounts':result['colourClassCounts'],'newVisibleTipProfiles':tipProfiles,'newActorShortReturns':spurs,'loop':loop}))
