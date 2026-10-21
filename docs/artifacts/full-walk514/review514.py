from pathlib import Path
import json,struct,gzip,hashlib,collections,numpy as np
from PIL import Image,ImageDraw
W=Path(__file__).parent;R=W/'Loop514';assert json.loads((R/'status.json').read_text())['status']=='CAPTURED'
def rd(p,tag):
 path=R/(p+'_'+tag+'.bin');b=path.read_bytes()if path.exists()else gzip.decompress(Path(str(path)+'.gz').read_bytes());w,h,_,_=struct.unpack_from('<4i',b);return np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
def mesh(path):
 b=path.read_bytes();magic,n=struct.unpack_from('<2i',b);assert magic==512;at=8;out={}
 for _ in range(n):
  renderer,nv,ns=struct.unpack_from('<3i',b,at);at+=12;v=np.frombuffer(b,'<f4',offset=at,count=nv*5).reshape(nv,5).astype(float);at+=nv*20;ix=[]
  for sm in range(ns):
   ni=struct.unpack_from('<i',b,at)[0];at+=4;ix.append(np.frombuffer(b,'<i4',offset=at,count=ni).reshape(-1,3));at+=ni*4
  out[renderer]=(v,ix)
 return out
paths=sorted(R.glob('*_pose.json'));assert len(paths)==81
masks=[];parents=[]
for path in paths:
 p=path.name[:3];mask=rd(p,'MASK');masks.append(mask[:,:,1]>.5);parents.append(mask[:,:,0]>.5)
masks=np.array(masks);parents=np.array(parents);ys,xs=np.nonzero(parents.any(axis=0));x0,y0,x1,y1=int(xs.min())-2,int(ys.min())-2,int(xs.max())+3,int(ys.max())+3;yy,xx=np.indices((y1-y0,x1-x0));yy+=y0;xx+=x0;records=[];geometry=[]
for i,path in enumerate(paths):
 p=path.name[:3];pose=json.loads(path.read_text());ox,oy=pose['offset'];my,mx=yy-oy,xx+ox;d={'i':i,'p':p,'pose':pose,'mask':masks[i,y0:y1,x0:x1],'parent':parents[i,y0:y1,x0:x1]}
 for tag,key in [('BASE','original'),('ALT','candidate')]:
  meta=rd(p,tag+'_META');uv=rd(p,tag+'_UV');colour=rd(p,tag+'_FINAL');screen=np.array(Image.open(R/(p+'_'+tag+'.png')).convert('RGB'))
  d[key]={'meta':meta[my,mx].copy(),'uv':uv[my,mx].copy(),'colour':colour[my,mx].copy(),'screen':screen[2*my,2*mx].copy(),'headRaw':rd(p,tag+'_RAW')[y0:y1,x0:x1].copy(),'headPrepared':rd(p,tag+'_PREPARED')[y0:y1,x0:x1].copy(),'worldInfo':rd(p,tag+'_WORLDINFO')[my,mx].copy()}
 cfg=json.loads((R/(p+'_ALT_projection.json')).read_text());view=np.array(cfg['headView']).reshape(4,4);source,indices=mesh(R/(p+'_ALT.raymesh'))[0];v=np.c_[source[:,:3],np.ones(len(source))]@view.T;uv=source[:,3:];refs=json.loads((R/(p+'_ALT_bodyrefs512.json')).read_text())['references'];packets=json.loads((R/(p+'_packets.json')).read_text())['packets'];by={(q['x'],q['y']):q for q in packets};errors=[];maxDepth=0.;maxUV=0.;kinds=collections.Counter();front=[]
 for ref in refs:
  kinds[ref['kind']]+=1;packet=by[(ref['x'],ref['y'])]
  if ref['kind']==3:continue
  ids=indices[ref['submesh']][ref['primitive']];t=v[ids];point=view@np.array([packet['world'][k]for k in ['x','y','z']]+[1]);a=t[1,:2]-t[0,:2];b=t[2,:2]-t[0,:2];q=point[:2]-t[0,:2];den=a[0]*b[1]-a[1]*b[0];bb=(q[0]*b[1]-q[1]*b[0])/den;cc=(a[0]*q[1]-a[1]*q[0])/den;bar=np.array([1-bb-cc,bb,cc]);depth=-bar@t[:,2];tc=bar@uv[ids];de=abs(depth-ref['depth']);ue=max(abs(tc-np.array([ref['uv'][k]for k in ['x','y']])));maxDepth=max(maxDepth,de);maxUV=max(maxUV,ue)
  if de>3e-6 or ue>2e-6 or bar.min()<-.00002:errors.append([ref['x'],ref['y'],float(de),float(ue)])
  if ref['depth']<packet['depth']-.0001:front.append({'xy':[ref['x'],ref['y']],'kind':ref['kind'],'bodyDepth':ref['depth'],'hairDepth':packet['depth']})
 d['refs']={(q['x'],q['y']):q for q in refs};records.append(d);geometry.append({'target':i,'references':len(refs),'packets':len(packets),'kinds':dict(kinds),'maxDepthError':float(maxDepth),'maxUVError':float(maxUV),'errors':errors,'opaqueForegroundReferences':front})
events=[];flashes=[]
for i in range(80):
 a,b,c=[records[n]for n in [(i-1)%80,i,(i+1)%80]];maskABA=(a['mask']==c['mask'])&(a['mask']!=b['mask'])
 for ry,rx in np.argwhere(maskABA):events.append({'target':i,'kind':'region-ABA','xy':[int(rx+x0),int(ry+y0)],'states':[bool(t['mask'][ry,rx])for t in [a,b,c]],'note':'screen-coordinate region ABA observation; needs continuous curve interpretation'})
 for version in ['original','candidate']:
  vals=[r[version]for r in [a,b,c]];roles=[np.rint(t['meta'][:,:,1]).astype(int)for t in vals];ha=[(t['meta'][:,:,0]>0)&(q>=12)for t,q in zip(vals,roles)];aba=(ha[0]==ha[2])&(ha[0]!=ha[1])
  for ry,rx in np.argwhere(aba):
   x,y=int(rx+x0),int(ry+y0);events.append({'target':i,'kind':'visible-role-ABA','version':version,'xy':[x,y],'roles':[int(q[ry,rx])for q in roles],'mask':[bool(t['mask'][ry,rx])for t in [a,b,c]],'headRawRoles':[int(round(float(t[version]['headRaw'][ry,rx,1])))for t in [a,b,c]],'headPreparedRoles':[int(round(float(t[version]['headPrepared'][ry,rx,0])))for t in [a,b,c]],'bodyReferences':[t['refs'].get((x,y))if version=='candidate'else None for t in [a,b,c]],'worldInfo':[t[version]['worldInfo'][ry,rx].tolist()for t in [a,b,c]],'note':'not automatically an error; identify continuous ownership/occlusion and first differing stage'})
  colours=[t['screen'].astype(int)for t in vals];outsideDifference=np.max(abs(colours[0]-colours[2]),axis=2);residual=np.max(abs(colours[1]-(colours[0]+colours[2])*.5),axis=2);same=(roles[0]==roles[1])&(roles[1]==roles[2])&(roles[1]>=12)&(vals[0]['meta'][:,:,3]==vals[1]['meta'][:,:,3])&(vals[1]['meta'][:,:,3]==vals[2]['meta'][:,:,3]);flash=same&(outsideDifference<=4)&(residual>=8)&a['mask']&b['mask']&c['mask']
  for ry,rx in np.argwhere(flash):flashes.append({'target':i,'version':version,'xy':[int(rx+x0),int(ry+y0)],'screenRGB':[t['screen'][ry,rx].tolist()for t in vals],'linearRGB':[t['colour'][ry,rx].tolist()for t in vals],'primitive':int(round(float(vals[1]['meta'][ry,rx,3]))),'uv':[t['uv'][ry,rx].tolist()for t in vals],'worldInfo':[t['worldInfo'][ry,rx].tolist()for t in vals],'residualByte':float(residual[ry,rx]),'note':'screening observation, not a perceptual error count; thresholds8/4 bytes are diagnostic filters only'})
seam={'maskCellDifference':int((masks[0]!=masks[80]).sum()),'originalHeadRoleDifference':int((records[0]['original']['meta'][:,:,1]!=records[80]['original']['meta'][:,:,1]).sum()),'candidateHeadRoleDifference':int((records[0]['candidate']['meta'][:,:,1]!=records[80]['candidate']['meta'][:,:,1]).sum()),'originalHeadScreenMaxByteDelta':int(np.max(abs(records[0]['original']['screen'].astype(int)-records[80]['original']['screen'].astype(int)))),'candidateHeadScreenMaxByteDelta':int(np.max(abs(records[0]['candidate']['screen'].astype(int)-records[80]['candidate']['screen'].astype(int))))}
known=[]
for x,y in [(219,49),(220,45),(224,58)]:
 steps=[]
 for i in [69,70,71]:
  d=records[i];rx,ry=x-x0,y-y0;steps.append({'target':i,'mask':bool(d['mask'][ry,rx]),'originalRole':int(round(float(d['original']['meta'][ry,rx,1]))),'candidateRole':int(round(float(d['candidate']['meta'][ry,rx,1]))),'reference':d['refs'].get((x,y))})
 known.append({'xy':[x,y],'steps':steps})
out={'scope':'single actual full Walk,81 paired poses including repeated endpoint','headROI':[x0,y0,x1,y1],'geometry':geometry,'bodyReferenceErrors':sum(len(g['errors'])for g in geometry),'maxBodyRayDepthError':max(g['maxDepthError']for g in geometry),'events':events,'flashes':flashes,'seam':seam,'knownEpisodes':known,'eventObservationCounts':dict(collections.Counter((e['kind']+('/'+e.get('version','')))for e in events)),'flashObservationCounts':dict(collections.Counter(f['version']for f in flashes)),'note':'No count here defines pixel-art quality; paired frames and continuous source evidence decide each case. No code or parameters changed.'}
(R/'REVIEW514.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['geometry','events','flashes','knownEpisodes']}));print(json.dumps({'knownEpisodes':known,'candidateEvents':[e for e in events if e.get('version')=='candidate' or e['kind']=='region-ABA'][:12],'candidateFlashExamples':[f for f in flashes if f['version']=='candidate'][:6]}))
# Compact native-colour contact sheet at eight phases; integer display scaling only.
sheet=Image.new('RGB',(560,8*168),'#202020');draw=ImageDraw.Draw(sheet)
for row,i in enumerate([0,10,20,30,40,50,60,70]):
 d=records[i];ox,oy=d['pose']['offset'];box=(2*(x0+ox),2*(y0-oy),2*(x1+ox),2*(y1-oy));
 for col,tag in enumerate(['BASE','ALT']):
  im=Image.open(R/(d['p']+'_'+tag+'.png')).convert('RGB').crop(box);im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);sheet.paste(im,(col*280,row*168+18))
 draw.text((2,row*168+2),f'{i/80:.4f} ORIGINAL348 | CURVES511+BODY512 (2x native display)',fill='white')
sheet.save(R/'HEAD_CONTACT514.png')
