from pathlib import Path
import struct,json,sys
import numpy as np
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;R=O/sys.argv[1];tag=sys.argv[2]
status=json.loads((R/'status.json').read_text());poses=sorted(R.glob('*_pose.json'));print('state',status,'complete poses',len(poses))
modeNames=['CLOTH','BODY']if list(R.glob('*_BODY_FINAL.bin'))else['CLOTH']
def read(p):
 b=p.read_bytes();w,h,x,y=struct.unpack_from('<4i',b);a=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);out=np.zeros((272,480,4),np.float32);out[y:y+h,x:x+w]=a;return out,(x,y,x+w,y+h)
rows=[];bounds=[];stages=[]
for posefile in poses:
 p=json.loads(posefile.read_text());f=p['frame'];stage=[json.loads((R/f'{f:03d}_{mode}_stage.json').read_text())for mode in ['OFF']+modeNames];row={'frame':f,'phase':p['phase'],'skyHour':p['skyHour'],'stages':stage};modes={}
 for mode in ['OFF']+modeNames:
  a,b=read(R/f'{f:03d}_{mode}_FINAL.bin');bounds.append(b);m,_=read(R/f'{f:03d}_{mode}_META.bin');u,_=read(R/f'{f:03d}_{mode}_UV.bin');modes[mode]=(a,m,u)
 base,bm,bu=modes['OFF']
 for mode in modeNames:
  a,m,u=modes[mode];diff=np.max(np.abs(base-a),axis=2)>1e-6;face=((bm[:,:,1]>=1)&(bm[:,:,1]<=7)&(base[:,:,3]>.5))|((m[:,:,1]>=1)&(m[:,:,1]<=7)&(a[:,:,3]>.5));hair=((bm[:,:,1]>=12)&(base[:,:,3]>.5))|((m[:,:,1]>=12)&(a[:,:,3]>.5));same=(np.max(np.abs(bm-m),axis=2)<2e-6)&(np.max(np.abs(bu[:,:,:2]-u[:,:,:2]),axis=2)<2e-6)&(a[:,:,3]>.5)&(base[:,:,3]>.5)
  partstats=[];union=np.zeros((272,480),bool)
  for part in ([1,2,3]if mode=='CLOTH'else[0,1,2,3]):
   raw=(R/f'{f:03d}_{mode}_PART{part}.bin').read_bytes();x,y,pw,ph=struct.unpack_from('<4i',raw);mask=np.zeros((272,480),bool);mask[y:y+ph,x:x+pw]=np.frombuffer(raw,'?',pw*ph,16+pw*ph*4).reshape(ph,pw);union|=mask;own=(np.rint(m[:,:,1])==8+part)&(a[:,:,3]>.5);partstats.append({'part':part,'selected':int(mask.sum()),'visibleOwn':int(own.sum()),'outside':int((own&~mask).sum())})
  row[mode]={'changed':int(diff.sum()),'faceEyeChanged':int((diff&face).sum()),'hairChanged':int((diff&hair).sum()),'sameSurfaceColourChanges':int((diff&same).sum()),'coverageAdded':int(((a[:,:,3]>.5)&(base[:,:,3]<.5)).sum()),'coverageRemoved':int(((a[:,:,3]<.5)&(base[:,:,3]>.5)).sum()),'selectedUnionUnfilled':int((union&(a[:,:,3]<.5)).sum()),'parts':partstats}
 rows.append(row);stages.extend(stage)
if not rows:raise SystemExit('No complete poses; retain first failure files')
(O/f'{tag}_PREMEDIA.json').write_text(json.dumps({'status':status,'rows':rows},indent=2),encoding='utf8')
x0=min(b[0]for b in bounds)*2-12;y0=min(b[1]for b in bounds)*2-12;x1=max(b[2]for b in bounds)*2+12;y1=max(b[3]for b in bounds)*2+12;box=(max(0,x0),max(0,y0),min(960,x1),min(544,y1));w,h=box[2]-box[0],box[3]-box[1]
medias={}
for mode in modeNames:
 frames=[]
 for row in rows:
  f=row['frame'];canvas=Image.new('RGB',(w*2,h+32),'#f5f6f8');d=ImageDraw.Draw(canvas);d.text((6,3),f'NEW540 actual Walk {f}: PRODUCT OFF | {mode} ON',fill='black')
  for i,k in enumerate(['OFF',mode]):canvas.paste(Image.open(R/f'{f:03d}_{k}.png').convert('RGB').crop(box),(i*w,32))
  canvas.save(O/f'{tag}_{mode}_{f:03d}.png');frames.append(canvas)
 duration=[round((i+1)*1000/60)-round(i*1000/60)for i in range(len(frames))]
 path=O/f'{tag}_{mode}.webp';frames[0].save(path,save_all=True,append_images=frames[1:],duration=duration,loop=0,lossless=True,quality=100,method=6)
 sheet=Image.new('RGB',(frames[0].width,frames[0].height*len(frames)))
 for i,f in enumerate(frames):sheet.paste(f,(0,i*f.height))
 pal=sheet.quantize(colors=256,method=Image.Quantize.FASTOCTREE);gf=[f.quantize(palette=pal,dither=Image.Dither.NONE)for f in frames];gd=[round((i+1)*100/60)*10-round(i*100/60)*10 for i in range(len(frames))];gp=O/f'{tag}_{mode}.gif';gf[0].save(gp,save_all=True,append_images=gf[1:],duration=gd,loop=0,optimize=False,disposal=2)
 with Image.open(path)as im:assert im.n_frames==len(frames)
 with Image.open(gp)as im:assert im.n_frames==len(frames)
 medias[mode]={'webpBytes':path.stat().st_size,'gifBytes':gp.stat().st_size,'frames':len(frames),'durationsMs':duration,'gifDurationsMs':gd,'size':frames[0].size}
timing={}
for mode in ['product OFF','outerwear-bottom-shoes','Body0 plus clothes; hands included']:
 group=[s for s in stages if s['mode']==mode]
 if group:timing[mode]={k:{'median':float(np.median([s[k]for s in group])),'min':min(s[k]for s in group),'max':max(s[k]for s in group)}for k in ['renderMs','geometryMs','areaMs','selectionMs','uploadMs','packetMs']}
result={'restoration':status,'poses':len(rows),'rows':rows,'timing':timing,'media':medias,'scope':'actual same-pose product OFF / common cloth14'+(' / Body0+cloth15 (shared inner top, stockings, skin and hands; no garment-only classification)'if 'BODY'in modeNames else'; Body0 was tested only in the earlier adjacent33..51 run and excluded here after face ownership regression')+'. Core RenderFrame readbacks included, subsequent capture I/O excluded; not Player FPS.'}
(O/f'{tag}_RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
