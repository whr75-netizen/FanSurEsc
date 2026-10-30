"""Replay current LayerMode19 packets, allocator and final-visibility mismatch. Offline only."""
from pathlib import Path
import sys,json,struct,math,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;O=R/'analysis';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R.parent/'author33/feature34'))
from eye_cache42 import classify
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def clean(a):
 if isinstance(a,np.ndarray):return a.tolist()
 if isinstance(a,np.generic):return a.item()
 raise TypeError(type(a).__name__)
def dump(name,a):(O/name).write_text(json.dumps(a,ensure_ascii=False,indent=2,default=clean),encoding='utf8')
def read(p):
 b=p.read_bytes();w,h=struct.unpack_from('<ii',b);return np.frombuffer(b,'<f4',offset=8).reshape(h,w,4)[::-1].copy()
def encode(a):return np.uint8(np.rint(np.clip(np.where(a<=.0031308,12.92*a,1.055*np.maximum(a,0)**(1/2.4)-.055),0,1)*255))
def cov(m):return(m[...,0]>0)&(m[...,1]>.5)&(m[...,3]>1e-6)
def valid(d,s,e):return cov(d[f'S{s}META'])&(np.rint(d[f'S{s}META'][...,2])==e)&(d[f'S{s}POINT'][...,3]>.5)
def weight_occlusion(d,weight,depth,kind):
 for source in['S4META','S5META']:
  m=d[source];weight*=np.where(cov(m)&(m[...,0]<depth),np.float32(1)-np.clip(m[...,3],0,1),np.float32(1))
 body=d['S6META'];weight=np.where(cov(body)&(body[...,0]<depth),np.float32(0),weight)
 return weight
def replay_packets(m,d):
 w,h=m['width'],m['height'];params={'centres':m['centres'],'axesX':m['axesX'],'axesY':m['axesY'],'style':json.loads(m['styleJson'])};out=np.zeros((2,h,w,12),np.float32);repDepth=np.zeros((2,h,w),np.float32)
 assert m['layerMode19']and not m['useHairRegion502']
 for eye in range(2):
  owner=round(m['centres'][eye]['w']);v=[valid(d,s,owner)for s in range(4)];f=[];u=[];vv=[]
  for s in range(4):
   a,b,c=classify(d[f'S{s}POINT'][...,:3],params,eye);f.append(a);u.append(b);vv.append(c)
  layer=[]
  for s in[2,1]:
   source=d[f'S{s}META'];eligible=v[s]&np.isin(f[s],[2,3,4]if s==2 else[1,2,3,4]);feat=np.where(eligible,f[s]if s==2 else 1,0);weight=np.where(eligible,np.clip(source[...,3],0,1),np.float32(0)).astype(np.float32)
   if s==1:
    im=d['S2META'];front=v[2]&np.isin(f[2],[2,3,4])&(im[...,0]<source[...,0]);weight*=np.where(front,np.float32(1)-np.clip(im[...,3],0,1),np.float32(1))
   skin=d['S0META'];weight*=np.where(v[0]&(skin[...,0]<source[...,0]),np.float32(1)-np.clip(skin[...,3],0,1),np.float32(1))
   line=d['S3META'];weight*=np.where(cov(line)&(line[...,0]<source[...,0]),np.float32(1)-np.clip(line[...,3],0,1),np.float32(1))
   weight=weight_occlusion(d,weight,source[...,0],s);layer.append((feat,weight,u[s],vv[s],source[...,0]))
  # Native upper-lash source, else original Sample583 lower-lid branch.
  line=d['S3META'];weight=np.clip(line[...,3],0,1).copy();skin=d['S0META'];weight*=np.where(v[0]&(skin[...,0]<line[...,0]),np.float32(1)-np.clip(skin[...,3],0,1),np.float32(1));weight=weight_occlusion(d,weight,line[...,0],3)
  first=np.zeros_like(f[0]);has=np.zeros_like(v[0])
  for s in range(4):first=np.where(~has&v[s],f[s],first);has|=v[s]
  lower=(~v[3])&(first==6)&v[0];lowerWeight=weight_occlusion(d,np.ones_like(weight),skin[...,0],0)
  lineFeat=np.where(v[3],5,np.where(lower,6,0));lineWeight=np.where(v[3],weight,np.where(lower,lowerWeight,0)).astype(np.float32);layer.append((lineFeat,lineWeight,np.zeros_like(weight),np.zeros_like(weight),np.where(v[3],line[...,0],skin[...,0])))
  for cy in range(h):
   for cx in range(w):
    counts=np.zeros(8,np.float32);mean=np.zeros(2,np.float32);total=np.float32(0);best=math.inf
    for k in range(16):
     xx=cx*4+k%4;yy=cy*4+3-k//4
     for family,(feature,weights,uu,vs,depth)in enumerate(layer):
      label=int(feature[yy,xx]);we=np.float32(weights[yy,xx])
      if label<=0 or we<=0:continue
      counts[label]=np.float32(counts[label]+we)
      if 2<=label<=4:
       mean+=we*np.array([uu[yy,xx],vs[yy,xx]],np.float32);total=np.float32(total+we)
       distance=((k%4+.5)/4-.5)**2+((k//4+.5)/4-.5)**2
       if distance<best:best=distance;repDepth[eye,cy,cx]=depth[yy,xx]
    if total>0:mean/=total
    out[eye,cy,cx,:8]=counts;out[eye,cy,cx,8:10]=mean
 return out,repDepth
def allocator(packet,m,eye,gate=None):
 a=packet[eye];I=np.float32(np.float32(a[...,2]+a[...,3])+a[...,4]);cost=np.maximum(np.maximum(a[...,1],a[...,5]),a[...,6])-I;area=np.float32(0);h,w=I.shape
 for yy in range(h-1,-1,-1):
  for xx in range(w):
   if I[yy,xx]>0:area=np.float32(area+np.float32(I[yy,xx]/16))
 eligible=[(int(x),int(y))for y,x in np.argwhere((I>0)&(np.ones_like(I,bool)if gate is None else gate))]
 eligible.sort(key=lambda t:(float(cost[t[1],t[0]]),float(a[t[1],t[0],8]),float(a[t[1],t[0],9]),-(t[1]+m['y']),t[0]+m['x']))
 budget=math.floor(float(np.float32(area+.5)));return eligible[:budget],eligible,budget,float(area),I,cost
def final_gate(d,depth):
 hair=d['hair-meta'];brow=d['brow-meta'];raw=d['raw-meta'];body=cov(raw)&(np.rint(raw[...,1])>=8)&(np.rint(raw[...,1])<=11)
 return(depth>0)&~(cov(hair)&(hair[...,0]<depth))&~(cov(brow)&(brow[...,0]<depth))&~(body&(raw[...,0]<depth))
rows=[];images=[];frames=[];counterImages=[]
for folder in sorted((R/'frames').iterdir()):
 m=load(folder/'meta.json');d={f.stem:read(f)for f in folder.glob('*.bin')if f.name!='FeatureCounts19.bin'};w,h,e,stride=struct.unpack_from('<iiii',(folder/'FeatureCounts19.bin').read_bytes());gpu=np.frombuffer((folder/'FeatureCounts19.bin').read_bytes(),'<f4',offset=16).reshape(2,h,w,12)[:,::-1].copy();cpu,depth=replay_packets(m,d);err=np.abs(cpu-gpu);maxerr=float(err.max());assert maxerr<1e-4,(m['frame'],maxerr)
 frame={'sourceId':m['sourceId'],'frame':m['frame'],'flags':{k:m[k]for k in['layerMode19','useIrisSurface582','useLashRegion583','useClosedLash590','useHairRegion502']},'packetBytes':m['packetBytes'],'packetReadMilliseconds':m['packetReadMilliseconds'],'renderSerialUnchangedDuringRead':m['renderSerialUnchangedDuringRead'],'maxFullPacketCPUvsGPUError':maxerr,'eyes':{},'metadata':m}
 actual=np.dstack((encode(d['final-native'][...,:3]),np.uint8(np.rint(d['final-native'][...,3]*255))));image=Image.fromarray(actual);image.save(O/f"frame{m['frame']}-actual.png");images.append(image)
 for eye in range(2):
  stable=round(m['centres'][eye]['w']);selected,ranked,budget,area,I,cost=allocator(gpu,m,eye);gate=final_gate(d,depth[eye]);trial,_,_,_,_,_=allocator(gpu,m,eye,gate);visible=d['eye-visible'];vcount=int(((np.rint(visible[...,1])==stable)&np.isin(np.rint(visible[...,0]),[2,3,4])).sum());cx,cy=223-m['x'],52-m['y'];ids=lambda cells:[[x+m['x'],y+m['y']]for x,y in cells]
  record={'stableId':stable,'wholeIrisArea':area,'budget':budget,'allocatedCells':ids(selected),'actualVisibleIrisCount':vcount,'candidateFinalVisibilityGateCells':ids(trial),'candidatePassesVisibilityGate':all(gate[y,x]for x,y in trial),'candidateIsOfflineOnly':True}
  if stable==1:
   record['focus']={'xy':[223,52],'IrisCount':float(I[cy,cx]),'whiteCount':float(gpu[eye,cy,cx,1]),'lineCount':float(gpu[eye,cy,cx,5]),'cost':float(cost[cy,cx]),'rank0based':ranked.index((cx,cy))if(cx,cy)in ranked else-1,'originalSelected':(cx,cy)in selected,'candidateSelected':(cx,cy)in trial,'finalGatePass':bool(gate[cy,cx])}
   record['topCandidates']=[{'xy':[x+m['x'],y+m['y']],'IrisCount':float(I[y,x]),'whiteCount':float(gpu[eye,y,x,1]),'lineCount':float(gpu[eye,y,x,5]),'cost':float(cost[y,x]),'representativeDepth':float(depth[eye,y,x]),'hairMeta':d['hair-meta'][y,x].tolist(),'finalGatePass':bool(gate[y,x])}for x,y in ranked[:5]]
  frame['eyes'][stable]=record
 frame['counterfactualIROnlyNotRGBA']='fixed existing weighted-area budget, final-cell-invisible candidates excluded from rank/eligibility; no min count, recolour, retry or forced symmetry'
 # Draw actual feature identities (top) and offline candidate allocations (bottom), never fake candidate RGBA.
 plate=Image.new('RGBA',(w,h*2+3),(23,27,34,255));draw=ImageDraw.Draw(plate)
 for ey,colour in[(1,(235,110,90,255)),(2,(80,190,220,255))]:
  for yy,xx in np.argwhere((np.rint(d['eye-visible'][...,1])==ey)&np.isin(np.rint(d['eye-visible'][...,0]),[2,3,4])):draw.point((int(xx),int(yy)),fill=colour)
  for xx,yy in frame['eyes'][ey]['candidateFinalVisibilityGateCells']:draw.point((xx-m['x'],yy-m['y']+h+3),fill=colour)
 counterImages.append(plate);rows.append(frame);frames.append((folder,m,d))
dump('PACKET_REPLAY_AND_ALLOCATOR.json',rows)
strip=Image.new('RGBA',(sum(im.width for im in images),max(im.height for im in images)))
x=0
for im in images:strip.paste(im,(x,0));x+=im.width
strip.save(O/'actual-strip-1x.png');strip.resize((strip.width*8,strip.height*8),Image.Resampling.NEAREST).save(O/'actual-strip-8x.png');anim=[i.resize((i.width*12,i.height*12),Image.Resampling.NEAREST).convert('RGB')for i in images];anim[0].save(O/'actual-slow.gif',save_all=True,append_images=anim[1:],duration=100,loop=0)
plate=Image.new('RGBA',(sum(i.width for i in counterImages),max(i.height for i in counterImages)))
x=0
for im in counterImages:plate.paste(im,(x,0));x+=im.width
plate.resize((plate.width*12,plate.height*12),Image.Resampling.NEAREST).save(O/'actual-features-above-offline-gate-below.png')
before=[load(R/'SCENE_BEFORE.ndjson')]if False else[json.loads(l)for l in(R/'SCENE_BEFORE.ndjson').read_text(encoding='utf8').splitlines()];after=[json.loads(l)for l in(R/'SCENE_AFTER.ndjson').read_text(encoding='utf8').splitlines()];aa={r['gid']:r for r in before[1:]};bb={r['gid']:r for r in after};final=load(R/'FINAL_STATE.json');files=load(R/'FILES_BEFORE.json')['files'];changes=[p for p,s in files.items()if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=s]
restore={'objectsBefore':len(aa),'objectsAfter':len(bb),'added':sorted(bb.keys()-aa.keys()),'removed':sorted(aa.keys()-bb.keys()),'serializedOrDirtyChanges':[k for k in aa.keys()&bb.keys()if aa[k]['json']!=bb[k]['json']or aa[k]['dirty']!=bb[k]['dirty']],'dirtySetExact':set(final['dirtyAssets'])==set(before[0]['dirtyAssets']),'sceneDirtyExact':final['sceneDirty']==before[0]['sceneDirty'],'rootIDsExact':final['rootIDs']==before[0]['rootIDs'],'timeScaleExact':final['timeScale']==before[0]['timeScale'],'captureDeltaExact':final['captureDelta']==before[0]['captureDelta'],'backgroundExact':final['background']==before[0]['background'],'tracked12HashChanges':changes,'finalState':final};assert not restore['serializedOrDirtyChanges']and not changes and restore['dirtySetExact'];dump('RESTORATION.json',restore)
summary={'sequenceId':load(R/'CAPTURE_DONE.json')['sequenceId'],'newSourceNotOld46':True,'frames':[r['frame']for r in rows],'actualVisibleEye1':[r['eyes'][1]['actualVisibleIrisCount']for r in rows],'actualVisibleEye2':[r['eyes'][2]['actualVisibleIrisCount']for r in rows],'maxCPUvsGPU':max(r['maxFullPacketCPUvsGPUError']for r in rows),'packetBytesTotal':sum(r['packetBytes']for r in rows),'totalTextureReadBytes':sum(m['readBytes']for _,m,_ in frames),'packetGetDataMS':[r['packetReadMilliseconds']for r in rows],'allRenderSerialStable':all(r['renderSerialUnchangedDuringRead']for r in rows),'productIntegrated':False,'candidateCompiledOnGPU':False,'focus':[{'frame':r['frame'],**r['eyes'][1]['focus']}for r in rows],'remaining':'visibility-only gate still permits diagonal eye1 at101; joint cluster/state cache needed for shape continuity, rotation/blink not tested','captureCaveat':'synchronous GetData/WaitForCompletion stalls GPU/Editor; same render serial proves no interleaved frame, not zero timing perturbation; controlled Step sequence is not a wall-clock gameplay benchmark'}
dump('SUMMARY.json',summary);print(json.dumps({k:v for k,v in summary.items()if k not in['focus']},ensure_ascii=False,indent=2))
