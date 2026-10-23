from pathlib import Path
import json,struct,re,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parent;R=O/('FullLoop'if len(sys.argv)>1 and sys.argv[1]=='full'else'Adjacent');label='FULL'if R.name=='FullLoop'else'ADJACENT'
n={'__file__':str(O.parent/'Cloth527/analyze_full527.py')};exec((O.parent/'Cloth527/analyze_full527.py').read_text().split('rows=[]')[0],n);n['R']=R
buf,region,degree=n['buf'],n['region'],n['degree'];frames=sorted(int(p.name[:3])for p in R.glob('*_probe.json'));rows=[];union=np.zeros((272,480),bool);masks=[];basevis=[];altvis=[];noncloth=[]
for f in frames:
 probe=json.loads((R/f'{f:03d}_probe.json').read_text());bc=buf(f,'BASE','FINAL');ac=buf(f,'ALT','FINAL');bm=buf(f,'BASE','META');am=buf(f,'ALT','META');bu=buf(f,'BASE','UV');au=buf(f,'ALT','UV');a,m=region(f)
 bmask=bc[:,:,3]>.5;amask=ac[:,:,3]>.5;union|=bmask|amask;masks.append(m);basevis.append(bmask&(bm[:,:,1]==11));altvis.append(amask&(am[:,:,1]==11))
 delta=np.max(abs(bc[:,:,:3]-ac[:,:,:3]),2);same=bmask&amask&(bm[:,:,1]==am[:,:,1])&(bm[:,:,3]==am[:,:,3])&(abs(bm[:,:,0]-am[:,:,0])<2e-6)&(np.max(abs(bu[:,:,:2]-au[:,:,:2]),2)<2e-6)
 changed=same&(bm[:,:,1]!=11)&(delta>1e-6)
 for y,x in np.argwhere(changed):noncloth.append({'frame':f,'xy':[int(x),int(y)],'role':float(bm[y,x,1]),'primitive':float(bm[y,x,3]),'baseRGB':bc[y,x,:3].tolist(),'altRGB':ac[y,x,:3].tolist(),'maxUVError':float(np.max(abs(bu[y,x,:2]-au[y,x,:2])))})
 costs={k:float(v)for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',(R/f'{f:03d}_cost.txt').read_text())}
 packets=(R/f'{f:03d}_ALT_PACKETS.bin').read_bytes();count=struct.unpack_from('<i',packets)[0];dt=np.dtype([('x','<i4'),('y','<i4'),('pr','<i4'),('data','<f4',12)]);pp=np.frombuffer(packets,dt,count,4);assert len(packets)==4+count*60
 bad=int(((pp['data'][:,4:7].min(1)<-1e-5)|(abs(pp['data'][:,4:7].sum(1)-1)>1e-4)|(pp['data'][:,10]<=0)).sum())if count else 0
 row={'frame':f,'phase':probe['phase'],'skyHour':probe.get('skyHour'),'clip':probe['clip'],'census':json.loads((R/f'{f:03d}_census.json').read_text()),'unfilled':int((m&~amask).sum()),'invalidOwner':int((m&amask&((am[:,:,0]<=0)|(am[:,:,1]<1)|(am[:,:,1]>15))).sum()),'outsideCloth':int((altvis[-1]&~m).sum()),'sameSurfaceNonclothChanged':int(changed.sum()),'faceChanged':int(((bm[:,:,1]>=1)&(bm[:,:,1]<=7)&bmask&(delta>1e-6)).sum()),'newGraySkin':int(((bm[:,:,1]==4)&bmask&(np.ptp(bc[:,:,:3],2)>1e-5)&(np.ptp(ac[:,:,:3],2)<=1e-5)).sum()),'packets':count,'invalidPacketBaryDepth':bad,'cost':costs,'target43Baseline':[bool(basevis[-1][y,x])for x,y in[(200,98),(200,99)]],'target43Candidate':[bool(altvis[-1][y,x])for x,y in[(200,98),(200,99)]],'target44Baseline':bool(basevis[-1][78,231]),'target44Candidate':bool(altvis[-1][78,231])};rows.append(row)
 assert not(row['unfilled']or row['invalidOwner']or row['outsideCloth']or bad)
events=[]
for tag,vis in [('BASE',basevis),('ALT',altvis)]:
 for i in range(1,len(frames)-1):
  tip=vis[i]&(degree(vis[i])==1)&~vis[i-1]&~vis[i+1]
  for y,x in np.argwhere(tip):events.append({'tag':tag,'frame':frames[i],'xy':[int(x),int(y)],'classification':'unclassified visible degree1 ABA candidate; not automatically an error'})
ys,xs=np.where(union);crop=(max(0,int(xs.min())*2-12),max(0,int(ys.min())*2-16),min(960,(int(xs.max())+1)*2+12),min(544,(int(ys.max())+1)*2+16))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
media=[]
for f in frames:
 ims=[Image.open(R/f'{f:03d}_{tag}.png').convert('RGB').crop(crop)for tag in['BASE','ALT']];w,h=ims[0].size;panel=Image.new('RGB',(w*2,h+40),'#eef3f8');d=ImageDraw.Draw(panel);d.text((5,3),f'Walk {f:02d}: 527 cloth ON | 532 cloth ON',fill='black',font=small);d.text((5,20),'Control',fill='black',font=small);d.text((w+5,20),'Ordered-area curve',fill='black',font=small);panel.paste(ims[0],(0,40));panel.paste(ims[1],(w,40));media.append(panel)
# Lossless output retains each observed frame and its intended 1/60sec duration.
dur=[round((i+1)*1000/60)-round(i*1000/60)for i in range(len(media))]
webp=O/(label+'_WALK533.webp');media[0].save(webp,save_all=True,append_images=media[1:],duration=dur,loop=0,lossless=True,method=6)
gif=O/(label+'_WALK533.gif');paletteSource=Image.new('RGB',(media[0].width,media[0].height*len(media)))
for i,p in enumerate(media):paletteSource.paste(p,(0,i*p.height))
palette=paletteSource.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
q=[p.quantize(palette=palette,dither=Image.Dither.NONE)for p in media];q[0].save(gif,save_all=True,append_images=q[1:],duration=[10*(round((i+1)*100/60)-round(i*100/60))for i in range(len(q))],loop=0,optimize=False,disposal=2)
indices=list(range(len(media)))if len(media)<=4 else[0,16,33,42,43,44,64,80]
cw,ch=media[0].size;sheet=Image.new('RGB',(cw*4,ch*int(np.ceil(len(indices)/4))),'white')
for k,i in enumerate(indices):sheet.paste(media[i],((k%4)*cw,(k//4)*ch))
sheet.save(O/(label+'_CONTACT533.png'))

for first in range(0,len(media),45):
 selected=media[first:first+45];cols=9;cellw=media[0].width//2;cellh=media[0].height
 panel=Image.new('RGB',(cellw*cols,cellh*int(np.ceil(len(selected)/cols))),'white')
 for k,p in enumerate(selected):panel.paste(p.crop((cellw,0,p.width,p.height)),((k%cols)*cellw,(k//cols)*cellh))
 panel.save(O/(label+'_ALL_CANDIDATES_'+str(first).zfill(3)+'_533.png'))

result={'status':'ACTUAL_CAPTURED_ANALYSIS_VISUAL_PENDING','comparison':'same execution527 clothingON vs532 clothingON; product defaultOFF','frames':frames,'rows':rows,'noncloth':noncloth,'tipCandidates':events,'restoration':json.loads((R/'status.json').read_text()),'faceStateBeforeAfterEqual':(R/'face_before.txt').read_bytes()==(R/'face_after.txt').read_bytes(),'geometryMsMedian':float(np.median([r['cost']['geometryMs']for r in rows])),'skyHours':sorted(set(r['skyHour']for r in rows)),'wholeRenderCallScope':'diagnostic RenderFrame includes readback/probes; not PlayerFPS','crop':crop,'media':{'losslessWebP':str(webp),'bytes':webp.stat().st_size,'frames':len(media),'durationMs':sum(dur),'gif':str(gif),'gifBytes':gif.stat().st_size,'noFrameDropped':True,'noInterpolation':True}}
(O/(label+'_RESULT533.json')).write_bytes(json.dumps(result,indent=2).encode())
print(json.dumps({'frames':frames,'contractFailures':sum(r['unfilled']+r['invalidOwner']+r['outsideCloth']+r['invalidPacketBaryDepth']for r in rows),'noncloth':len(noncloth),'faceChanged':sum(r['faceChanged']for r in rows),'gray':sum(r['newGraySkin']for r in rows),'tipCandidates':events,'target43':[{'f':r['frame'],'base':r['target43Baseline'],'alt':r['target43Candidate']}for r in rows if r['frame']in[42,43,44]],'geometryMsMedian':result['geometryMsMedian'],'media':result['media']}))
