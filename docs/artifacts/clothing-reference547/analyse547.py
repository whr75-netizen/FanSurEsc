from pathlib import Path
import json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent; R=O/sys.argv[1]
def read(p):
 b=p.read_bytes();w,h,x,y=struct.unpack_from('<4i',b);a=np.zeros((272,480,4),np.float32);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return a,(x,y,x+w,y+h)
def part(p):
 b=p.read_bytes();x,y,w,h=struct.unpack_from('<4i',b);a=np.zeros((272,480),bool);a[y:y+h,x:x+w]=np.frombuffer(b,'?',w*h,16+4*w*h).reshape(h,w);return a
status=json.loads((R/'status.json').read_text());assert status['status']=='CAPTURED',status
frames=sorted(int(p.name[:3])for p in R.glob('*_pose.json'));assert len(frames)==status['poses'];rows=[];boxes=[];events=[]
for f in frames:
 data={m:{s:read(R/f'{f:03d}_{m}_{s}.bin')[0]for s in ['FINAL','META','UV','PREPARED','POSTLINE']}for m in ['OLD','FIX']};a=data['OLD'];b=data['FIX'];delta=np.max(np.abs(a['FINAL']-b['FINAL']),2)>1e-6
 same=(np.max(np.abs(a['META']-b['META']),2)<2e-6)&(np.max(np.abs(a['UV'][:,:,:2]-b['UV'][:,:,:2]),2)<2e-6)&(a['FINAL'][:,:,3]>.5)&(b['FINAL'][:,:,3]>.5)
 face=(((a['META'][:,:,1]>=1)&(a['META'][:,:,1]<=7)&(a['FINAL'][:,:,3]>.5))|((b['META'][:,:,1]>=1)&(b['META'][:,:,1]<=7)&(b['FINAL'][:,:,3]>.5)))
 hair=((a['META'][:,:,1]>=12)&(a['FINAL'][:,:,3]>.5))|((b['META'][:,:,1]>=12)&(b['FINAL'][:,:,3]>.5))
 pcs=[]
 for p in [1,2,3]:
  ma=part(R/f'{f:03d}_OLD_PART{p}.bin');mb=part(R/f'{f:03d}_FIX_PART{p}.bin');own=(np.rint(b['META'][:,:,1])==8+p)&(b['FINAL'][:,:,3]>.5)
  expected=(O/'StoredGate'/f'{f:03d}_PART{p}.bin').read_bytes();raw=(R/f'{f:03d}_FIX_PART{p}.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',raw);actual=raw[16+4*w*h:16+5*w*h]
  pcs.append({'submesh':p,'added':np.argwhere(mb&~ma)[:,::-1].tolist(),'removed':np.argwhere(ma&~mb)[:,::-1].tolist(),'outside':int((own&~mb).sum()),'storedPredictionIdentical':actual==expected})
 stages={m:json.loads((R/f'{f:03d}_{m}_stage.json').read_text())for m in ['OLD','FIX']}
 for yy,xx in np.argwhere(delta&same):events.append({'frame':f,'xy':[int(xx),int(yy)],'meta':b['META'][yy,xx].tolist(),'before':a['FINAL'][yy,xx].tolist(),'after':b['FINAL'][yy,xx].tolist(),'preparedSame':bool(np.all(a['PREPARED'][yy,xx]==b['PREPARED'][yy,xx])),'firstAtPostLine':bool(np.all(a['PREPARED'][yy,xx]==b['PREPARED'][yy,xx]) and np.any(a['POSTLINE'][yy,xx]!=b['POSTLINE'][yy,xx]))})
 row={'frame':f,'phase':json.loads((R/f'{f:03d}_pose.json').read_text())['phase'],'changedFinal':int(delta.sum()),'faceEyeChanged':int((delta&face).sum()),'hairChanged':int((delta&hair).sum()),'sameSurfaceColourChanges':int((delta&same).sum()),'inputHashEqual':(R/f'{f:03d}_OLD_INPUT_SHA.txt').read_text()==(R/f'{f:03d}_FIX_INPUT_SHA.txt').read_text(),'parts':pcs,'stages':stages}
 rows.append(row)
 for m in ['OLD','FIX']:boxes.append(read(R/f'{f:03d}_{m}_FINAL.bin')[1])
result={'scope':'Actual matched Walk; OLD543/544 vs FIX547. CPU masks are predictions, image buffers are actual Unity. Not product OFF comparison.','status':status,'rows':rows,'sameSurfaceColourEvents':events,'timing':{m:{k:{'median':float(np.median([r['stages'][m][k]for r in rows])),'p95':float(np.percentile([r['stages'][m][k]for r in rows],95))}for k in ['renderMs','geometryMs','areaMs','selectionMs','uploadMs','packetMs']}for m in ['OLD','FIX']}}
(O/(R.name+'_RESULT547.json')).write_text(json.dumps(result,indent=2))
print(json.dumps({'poses':len(rows),'changedFrames':[r['frame']for r in rows if r['changedFinal']],'faceEyeChanged':sum(r['faceEyeChanged']for r in rows),'hairChanged':sum(r['hairChanged']for r in rows),'outside':sum(p['outside']for r in rows for p in r['parts']),'predictionMismatch':[(r['frame'],p['submesh'])for r in rows for p in r['parts']if not p['storedPredictionIdentical']],'sameSurfaceColourEvents':events,'timing':result['timing']},ensure_ascii=False))
box=(max(0,min(b[0]for b in boxes)*2-12),max(0,min(b[1]for b in boxes)*2-12),min(960,max(b[2]for b in boxes)*2+12),min(544,max(b[3]for b in boxes)*2+12));w,h=box[2]-box[0],box[3]-box[1];pics=[]
for f in frames:
 im=Image.new('RGB',(w*2,h+28),'#f3f5f7');d=ImageDraw.Draw(im)
 for i,m in enumerate(['OLD','FIX']):d.text((i*w+5,5),f'{f:02d} '+('543/544 before'if m=='OLD'else'547 reference fix'),fill='black');im.paste(Image.open(R/f'{f:03d}_{m}.png').convert('RGB').crop(box),(i*w,28))
 pics.append(im)
for page in range((len(pics)+8)//9):
 sheet=Image.new('RGB',(w*2*3,(h+28)*3),'white')
 for i,im in enumerate(pics[page*9:page*9+9]):sheet.paste(im,(i%3*w*2,i//3*(h+28)))
 sheet.save(O/f'{R.name}_REVIEW{page}.png')
pics[frames.index(68) if 68 in frames else 0].save(O/(R.name+'_LATEST.png'))
if len(frames)==81:
 ds=[round((i+1)*1000/60)-round(i*1000/60)for i in range(81)];gs=[round((i+1)*100/60)*10-round(i*100/60)*10 for i in range(81)]
 wp=O/'FULL_WALK547.webp';gp=O/'FULL_WALK547.gif';pics[0].save(wp,save_all=True,append_images=pics[1:],duration=ds,loop=0,lossless=True,method=4)
 palette=Image.new('RGB',(w*2,(h+28)*81))
 for i,im in enumerate(pics):palette.paste(im,(0,i*(h+28)))
 pal=palette.quantize(colors=256,method=Image.Quantize.FASTOCTREE);gg=[im.quantize(palette=pal,dither=Image.Dither.NONE)for im in pics];gg[0].save(gp,save_all=True,append_images=gg[1:],duration=gs,loop=0,optimize=False,disposal=2)
 for p in [wp,gp]:
  with Image.open(p)as im:assert im.n_frames==81
 (O/'MEDIA547.json').write_text(json.dumps({'frames':81,'webpBytes':wp.stat().st_size,'gifBytes':gp.stat().st_size,'webpMs':sum(ds),'gifMs':sum(gs),'crop':box,'resampling':False,'comparison':'OLD543/544 vs FIX547 same execution','delivery':'local only; Library403 not retried'},indent=2))
