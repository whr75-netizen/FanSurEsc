from pathlib import Path
import struct,json
import numpy as np
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;R=O/'FullLoop543';modes=['OFF','CLOTH','SPAN']
def read(path):
 b=path.read_bytes();w,h,x,y=struct.unpack_from('<4i',b);a=np.zeros((272,480,4),np.float32);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return a,(x,y,x+w,y+h)
def mask(path):
 b=path.read_bytes();x,y,w,h=struct.unpack_from('<4i',b);a=np.zeros((272,480),bool);a[y:y+h,x:x+w]=np.frombuffer(b,'?',w*h,16+4*w*h).reshape(h,w);return a
status=json.loads((R/'status.json').read_text());assert status['status']=='CAPTURED' and status['poses']==81,status
rows=[];bounds=[];colourEvents=[]
for f in range(81):
 data={m:{s:read(R/f'{f:03d}_{m}_{s}.bin')[0]for s in ['FINAL','META','UV','POSTLINE']}for m in modes};base=data['CLOTH'];a=data['SPAN'];stages={m:json.loads((R/f'{f:03d}_{m}_stage.json').read_text())for m in modes};parts=[]
 for m in modes:bounds.append(read(R/f'{f:03d}_{m}_FINAL.bin')[1])
 changed=np.max(np.abs(a['FINAL']-base['FINAL']),axis=2)>1e-6;face=((base['META'][:,:,1]>=1)&(base['META'][:,:,1]<=7)&(base['FINAL'][:,:,3]>.5))|((a['META'][:,:,1]>=1)&(a['META'][:,:,1]<=7)&(a['FINAL'][:,:,3]>.5));hair=((base['META'][:,:,1]>=12)&(base['FINAL'][:,:,3]>.5))|((a['META'][:,:,1]>=12)&(a['FINAL'][:,:,3]>.5));same=(np.max(np.abs(a['META']-base['META']),axis=2)<2e-6)&(np.max(np.abs(a['UV'][:,:,:2]-base['UV'][:,:,:2]),axis=2)<2e-6)&(a['FINAL'][:,:,3]>.5)&(base['FINAL'][:,:,3]>.5)
 for p in [1,2,3]:
  b=mask(R/f'{f:03d}_CLOTH_PART{p}.bin');c=mask(R/f'{f:03d}_SPAN_PART{p}.bin');own=(np.rint(a['META'][:,:,1])==8+p)&(a['FINAL'][:,:,3]>.5);parts.append({'part':p,'addedXY':np.argwhere(c&~b)[:,::-1].tolist(),'removedXY':np.argwhere(b&~c)[:,::-1].tolist(),'outside':int((own&~c).sum())})
 for y,x in np.argwhere(changed&same):colourEvents.append({'frame':f,'xy':[int(x),int(y)],'owner':a['META'][y,x].tolist(),'before':base['FINAL'][y,x].tolist(),'after':a['FINAL'][y,x].tolist(),'postLineBefore':base['POSTLINE'][y,x].tolist(),'postLineAfter':a['POSTLINE'][y,x].tolist()})
 rows.append({'frame':f,'pose':json.loads((R/f'{f:03d}_pose.json').read_text()),'changedFinal':int(changed.sum()),'faceEyeChanged':int((changed&face).sum()),'hairChanged':int((changed&hair).sum()),'sameSurfaceColorChanged':int((changed&same).sum()),'coverageAdded':int(((a['FINAL'][:,:,3]>.5)&(base['FINAL'][:,:,3]<.5)).sum()),'coverageRemoved':int(((a['FINAL'][:,:,3]<.5)&(base['FINAL'][:,:,3]>.5)).sum()),'parts':parts,'stages':stages})
result={'status':status,'frames':81,'renders':243,'comparison':'Same execution product OFF /540 Clothes /543 shape only. Body0, face, eyes, hair not expanded. All frames retained. Shape quality requires visual review in addition to these contract counts.','rows':rows,'sameSurfaceColourEvents':colourEvents,'timing':{m:{k:{'median':float(np.median([r['stages'][m][k]for r in rows])),'p95':float(np.percentile([r['stages'][m][k]for r in rows],95))}for k in ['renderMs','geometryMs','areaMs','selectionMs','uploadMs','packetMs']}for m in modes}}
(O/'FULL_RESULT543.json').write_text(json.dumps(result,indent=2));print(json.dumps({'state':status,'frames':81,'changedFrames':[r['frame']for r in rows if r['changedFinal']],'faceEyeChanged':sum(r['faceEyeChanged']for r in rows),'hairChanged':sum(r['hairChanged']for r in rows),'outside':sum(p['outside']for r in rows for p in r['parts']),'colorEvents':len(colourEvents),'maskChanges':[{'frame':r['frame'],'parts':[p for p in r['parts']if p['addedXY']or p['removedXY']]}for r in rows if any(p['addedXY']or p['removedXY']for p in r['parts'])],'timing':result['timing']}))
x0=max(0,min(b[0]for b in bounds)*2-12);y0=max(0,min(b[1]for b in bounds)*2-12);x1=min(960,max(b[2]for b in bounds)*2+12);y1=min(544,max(b[3]for b in bounds)*2+12);box=(x0,y0,x1,y1);w,h=x1-x0,y1-y0;frames=[]
for f in range(81):
 im=Image.new('RGB',(w*3,h+32),'#f5f6f8');d=ImageDraw.Draw(im)
 for i,m in enumerate(modes):d.text((i*w+5,4),f'{f:02d} '+{'OFF':'Product OFF','CLOTH':'540 Clothes','SPAN':'543 shape'}[m],fill='black');im.paste(Image.open(R/f'{f:03d}_{m}.png').convert('RGB').crop(box),(i*w,32))
 frames.append(im)
dur=[round((i+1)*1000/60)-round(i*1000/60)for i in range(81)];gd=[round((i+1)*100/60)*10-round(i*100/60)*10 for i in range(81)]
wp=O/'FULL_WALK543.webp';gp=O/'FULL_WALK543.gif';frames[0].save(wp,save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True,quality=100,method=6)
sheet=Image.new('RGB',(w*3,(h+32)*81))
for i,im in enumerate(frames):sheet.paste(im,(0,i*(h+32)))
palette=sheet.quantize(colors=256,method=Image.Quantize.FASTOCTREE);gif=[im.quantize(palette=palette,dither=Image.Dither.NONE)for im in frames];gif[0].save(gp,save_all=True,append_images=gif[1:],duration=gd,loop=0,optimize=False,disposal=2)
for p in [gp,wp]:
 with Image.open(p)as im:assert im.n_frames==81,(p,im.n_frames)
frames[65].save(O/'LATEST543.png');frames[66].save(O/'SHOE66_543.png')
for page in range(9):
 board=Image.new('RGB',(w*3*3,(h+32)*3),'white')
 for i,im in enumerate(frames[page*9:page*9+9]):board.paste(im,(i%3*w*3,i//3*(h+32)))
 board.save(O/f'REVIEW543_{page}.png')
(O/'MEDIA543.json').write_text(json.dumps({'frames':81,'nativeCrop':box,'panelPixels':[w,h],'spatialInterpolation':False,'webp':{'bytes':wp.stat().st_size,'durationMs':sum(dur),'durations':dur},'gif':{'bytes':gp.stat().st_size,'durationMs':sum(gd),'durations':gd},'delivery':'Local only; prior Library403 not retried'},indent=2));print('media',gp.stat().st_size,wp.stat().st_size,'all81 frames preserved')
