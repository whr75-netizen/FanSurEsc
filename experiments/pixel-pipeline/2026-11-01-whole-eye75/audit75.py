"""Read actual on-disk bank plus frozen inputs; don't invent missing keyforms."""
from pathlib import Path
import json,re,hashlib,numpy as np
from PIL import Image,ImageDraw
from joint75 import hall,state_contract,layered_identity
R=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');BASE=REPO/'Assets/EUnityValidation01'
def sibling(a,b):
 p=R.parent/a
 return p if p.exists()else R.parent/b
NEW=sibling('eye-observer73','2026-11-01-eye-observer73');OLD=sibling('eye-candidate49','2026-10-30-eye-candidate49');KEY=sibling('whole-eye52','2026-10-31-eye-experiments50-53/archive/whole-eye52');F74=sibling('eye-allocator74','2026-11-01-eye-allocator74')
def texture(name,dtype):
 p=BASE/'SocketTemplate216/Inputs'/name;s=p.read_text(encoding='utf-8-sig');w=int(re.search(r'm_Width:\s*(\d+)',s).group(1));h=int(re.search(r'm_Height:\s*(\d+)',s).group(1));raw=bytes.fromhex(re.search(r'_typelessdata:\s*([0-9a-fA-F]+)',s).group(1));a=np.frombuffer(raw,dtype).reshape(h,w,4)[::-1].copy();return p,s,a
def cov(m):return(m[...,0]>0)&(m[...,1]>.5)&(m[...,3]>1e-6)
def domains_from_raw(d,sid,omit_skin=False):
 out={};h,w=d['hair-meta'].shape[:2]
 def valid(s):return cov(d[f'S{s}META'])&(np.rint(d[f'S{s}META'][...,2])==sid)&(d[f'S{s}POINT'][...,3]>.5)
 for f,s in [('iris',2),('white',1),('upper',3)]:
  src=d[f'S{s}META'];v=valid(s);raw=v.reshape(h,4,w,4).any((1,3));weight=np.where(v,np.clip(src[...,3],0,1),0).astype(np.float32)
  if s==1:
   m=d['S2META'];weight*=np.where(valid(2)&(m[...,0]<src[...,0]),1-np.clip(m[...,3],0,1),1)
  if not omit_skin:
   m=d['S0META'];weight*=np.where(valid(0)&(m[...,0]<src[...,0]),1-np.clip(m[...,3],0,1),1)
  if s!=3:
   m=d['S3META'];weight*=np.where(cov(m)&(m[...,0]<src[...,0]),1-np.clip(m[...,3],0,1),1)
  for name in ['S4META','S5META']:
   m=d[name];weight*=np.where(cov(m)&(m[...,0]<src[...,0]),1-np.clip(m[...,3],0,1),1)
  m=d['S6META'];weight=np.where(cov(m)&(m[...,0]<src[...,0]),0,weight)
  occ=(weight>0).reshape(h,4,w,4).any((1,3));out[f]={'raw':{(int(x),int(y))for y,x in np.argwhere(raw)},'visible':{(int(x),int(y))for y,x in np.argwhere(occ)}}
 return out
def packet_domains(a):
 return {f:{(int(x),int(y))for y,x in np.argwhere(v>0)}for f,v in [('iris',np.float32(np.float32(a[...,2]+a[...,3])+a[...,4])),('white',a[...,1]),('upper',a[...,5])]}
def main():
 assert not (R/'RESULT75.json').exists(),'Preserve existing audit'
 cp,cs,rgba=texture('TemplateRGBA.asset','u1');rp,rs,role=texture('TemplateRole.asset','<f4');assert np.isfinite(role).all();bank=[]
 for y,x in np.argwhere((role[...,0]>0)&(rgba[...,3]>0)):
  owner=int(round(float(role[y,x,1])));r=int(round(float(role[y,x,0])));bank.append({'cellId':f'eye{owner}:role{r}:template:{x},{y}','eye':owner,'role':r,'referenceXY':[int(x),int(y)],'rgba8':rgba[y,x].tolist()})
 fixture=json.loads((OLD/'fixtures/template43.json').read_text());assert sorted(bank,key=lambda c:c['cellId'])==sorted(fixture['cells'],key=lambda c:c['cellId'])
 key=json.loads((KEY/'WHOLE_KEYFORM52.json').read_text());records=json.loads((NEW/'CELL_RECORDS73.json').read_text());result73=json.loads((NEW/'RESULT73.json').read_text());gpu=[]
 for row in records['rows']:
  f=np.array(row['fields']);x,y,r,k=f[7]
  if k==1 and f[3,0]>0:
   expected=rgba[int(y),int(x),:3];linear=f[0,:3];encoded=np.rint(np.where(linear<=.0031308,linear*12.92,1.055*np.maximum(linear,0)**(1/2.4)-.055)*255).clip(0,255).astype(np.uint8);q=expected/255.;decoded=np.where(q<=.04045,q/12.92,((q+.055)/1.055)**2.4)
   gpu.append({'xyTopLeft':row['xyTopLeft'],'templateXY':[int(x),int(y)],'role':int(r),'recordRoleAgrees':int(role[int(y),int(x),0])==int(r),'storedRGB8':expected.tolist(),'observedEncodedRGB8':encoded.tolist(),'RGB8maxError':int(np.max(abs(encoded.astype(int)-expected.astype(int)))),'linearDecodeMaxError':float(np.max(abs(decoded-linear)))})
 demands={sid:{'iris':sum(c['eye']==sid and c['role']==1 for c in bank),'white':sum(c['eye']==sid and c['role']==4 for c in bank)}for sid in [1,2]};current=[]
 for e,sid in enumerate([2,1]):
  a=np.zeros((8,16,12),np.float32)
  for z in records['rows']:
   x,y=z['xyTopLeft'];a[y-49,x-212]=z['countsBothEyes'][e]
  ds=packet_domains(a);current.append({'sourceId':result73['sourceId'],'stableId':sid,'domains':{k:[list(p)for p in sorted(v)]for k,v in ds.items()},'allBankCellsVisibleDemand':demands[sid],'capacityUnderActualPostClassifyCounts':hall(ds,demands[sid]),'meaning':'conditional reuse of atlas texels as mandatory opaque pixels; count-zero is not proof of raw source absence','raw4xInputsAvailable':False})
 z=np.load(OLD/'fixtures/replay-inputs.npz');metas=json.loads((OLD/'fixtures/frames.json').read_text());ablations=[]
 for i,m in enumerate(metas):
  pre=f'f{i:02d}_';d={k[len(pre):]:z[k]for k in z.files if k.startswith(pre)and k!=pre+'GPU'};p=z[pre+'GPU']
  for e,sid in enumerate([round(c['w'])for c in m['centres']]):
   raw=domains_from_raw(d,sid);omit=domains_from_raw(d,sid,True);modes={'actual-counts':packet_domains(p[e]),'raw-owner-support':{k:v['raw']for k,v in raw.items()},'raw-with-recorded-occluders-no-Classify':{k:v['visible']for k,v in raw.items()},'raw-without-S0-sensitivity-only':{k:v['visible']for k,v in omit.items()}}
   ablations.append({'sourceId':m['sourceId'],'frame':m['frame'],'stableId':sid,'modes':{name:{'domainCounts':{k:len(v)for k,v in ds.items()},'jointIW':hall(ds,demands[sid])}for name,ds in modes.items()},'limits':'Raw support is potential geometry only. Omitting S0 is an ablation, not permission to erase true eyelids/skin. No part colour/shape is synthesized.'})
 nativecache=layered_identity(bank,set());assert len(nativecache)==20 and not any(c['visible']for c in nativecache)
 state={'iris':{'intrinsicDefinition':'source-bank role1'},'white':{'intrinsicDefinition':'source-bank role4'}}
 result={'bankSources':[{'path':str(cp),'sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'format':4},{'path':str(rp),'sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'format':20}],'bankDimensions':[480,272],'bankRoles':np.unique(role[...,0]).tolist(),'bankCells':bank,'sourceFixture20Agreement':True,'currentGPUOwnSamples':gpu,'fullCurrentGPUTextureBindingRead':False,'wholeOpenContract':state_contract(state,['iris','white','upper-lid','lower-lid']),'closeStates':{k:{'pixelFormAvailable':v.get('pixelFormAvailable'),'nativeGeometryAvailable':bool(v.get('nativeGeometry'))}for k,v in key['states'].items()if k!='existing-open-reference'},'current73ConditionalCapacity':current,'historicalAblations':ablations,'cacheVisibilityDistinction':{'allIntrinsicTokensKept':len(nativecache),'allHiddenTokensRemain':len(nativecache),'meaning':'identity retention is not a promise that every reference texel stays opaque/visible'},'sharedCell52Counterexample':json.loads((KEY/'FRAME101_FEASIBILITY52.json').read_text())['orderTruthTable'],'newUnityCalls':0,'productChanges':0,'jointCandidateRendered':False,'decision':'No complete current-state joint raster adopted. Restore existing colour bank and distinguish derived counts from source support; missing lid/state contract and source-compatible shared ownership remain explicit.'}
 with (R/'RESULT75.json').open('x',encoding='utf-8')as f:json.dump(result,f,ensure_ascii=False,indent=2)
 crop=rgba[76:82,210:225].copy();Image.fromarray(crop).save(R/'SOURCE_BANK75.png');im=Image.open(R/'SOURCE_BANK75.png');im.resize((im.width*24,im.height*24),Image.Resampling.NEAREST).save(R/'SOURCE_BANK75-nearest24.png')
 print(json.dumps({'bankCells':len(bank),'bankRoles':result['bankRoles'],'currentOwnSamples':len(gpu),'maxEncodedRGB8Error':max(x['RGB8maxError']for x in gpu),'maxLinearDecodeError':max(x['linearDecodeMaxError']for x in gpu),'missingParts':result['wholeOpenContract']['missing'],'currentHall':[(v['stableId'],v['capacityUnderActualPostClassifyCounts']['witnesses'][0])for v in current],'oldCapacityPassesByAblation':{mode:sum(r['modes'][mode]['jointIW']['capacityFeasible']for r in ablations)for mode in ablations[0]['modes']}},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
