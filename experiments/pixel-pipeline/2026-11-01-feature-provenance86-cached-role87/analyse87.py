"""Saved real87 packets only; no Unity calls or fabricated visibility/backing."""
from pathlib import Path
import json,sys,hashlib,numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'whole-eye76'))
from validate_final76 import Reader,plane,read,rgb8,supported,texture
OUT=HERE/'result87';RUN=HERE/'run87'

def load(path):
 m=json.loads((path/'RAW_MANIFEST.json').read_text());assert (path/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((path/'RAW_MANIFEST.json').read_bytes()).hexdigest()
 r=Reader(path/'baseline76.buffer');assert r.s()=='baseline76/v1';ident={'sourceId':r.s(),'viewId':r.s(),'frameIndex':r.i(),'renderSerial':r.i()};roi=[r.i()for _ in range(4)];assert r.i()==96
 x,y,w,h=roi;b=r.a(w*h*24).reshape(h,w,6,4);r.end();assert np.all(b[...,5,2]==ident['frameIndex'])and np.all(b[...,5,3]==ident['renderSerial']-1)
 ch,c=read(path/'eye-counts76.bin.partial',True);rh,z=read(path/'eye-records76.bin.partial',False);assert ch['identity']==rh['identity']==ident
 a={};headers={}
 for p in path.glob('*.plane'):
  ph,ar=plane(p);assert all(ph[k]==ident[k]for k in ['sourceId','frameIndex','renderSerial']),p
  view='native-final'if p.stem.startswith('native-final')else'main'if p.stem.startswith('main-')else'head';assert ph['viewId']==view,(p,ph['viewId']);assert np.isfinite(ar).all()
  a[p.stem]=ar;headers[p.stem]=ph
 return dict(manifest=m,identity=ident,roi=roi,baseline=b,eyeROI=ch['roi'],counts=c,records=z.reshape(z.shape[0],z.shape[1],16,4),arrays=a,headers=headers)

def local_grid(d,ei):
 x,y,w,h=d['roi'];yy,xx=np.mgrid[:h,:w];p=np.stack([xx+x+.5,271-(yy+y)+.5,np.ones_like(xx),np.zeros_like(xx)],-1).astype(np.float32)
 q=p@np.array(d['manifest']['eyeFeature']['inverse'][ei],np.float32).reshape(4,4,order='F').T;return q[...,:2]/q[...,2,None]

def pos(mask,d):
 x,y,_,_=d['roi'];return [[int(xx+x),int(271-yy-y)]for yy,xx in np.argwhere(mask)]

def role_summary(intr,owner,d):
 rows=[]
 for sid in [2,1]:
  ir=(np.rint(intr[...,0])==1)&(np.rint(intr[...,1])==sid);visible=ir&(np.rint(owner[...,0])==2)&(np.rint(owner[...,1])==sid)
  rows.append({'eye':sid,'intrinsicIris':pos(ir,d),'visibleIris':pos(visible,d)})
 return rows

def main():
 OUT.mkdir(exist_ok=False);st=json.loads(sorted(RUN.glob('STATE87-*.json'))[-1].read_text());assert st['stage']=='finished'and st['PlayExited']and not st.get('error')and not st.get('restorationError');assert st['original333Calibration87']['pass'];entries=st['sequencePackets'];assert len(entries)==29
 _,_,role=texture('TemplateRole.asset','<f4');_,_,colour=texture('TemplateRGBA.asset','u1');rows=[];pictures=[];nativepics=[];unexplained=[];protectedTotal=0;rgbChecked=0;sourceMismatch=0
 for entry in entries:
  d=load(Path(entry['output']));a=d['arrays'];m=d['manifest'];rec=d['records'];b=d['baseline'];x,y,w,h=d['roi'];rx,ry,rw,rh=d['eyeROI'];assert m['candidate87']['active']and m['frameUnchangedDuringReadback'];assert m['sourceForm86']['sourceSHA']=='284eab0902207eb71fa85be08dea99c8409898d46d7878f3fc51c352a2251b7d'
  oldintr=a['original333-2'];intr=a['old-intrinsic'];oldowner=a['original333-1'];owner=a['old-eye-owner'];pred=np.zeros_like(intr[...,:2]);sourcexy=np.zeros_like(intr[...,:2],dtype=int)
  for ei,sid in enumerate([int(v[3])for v in m['eyeFeature']['centres']]):
   q=local_grid(d,ei);k=np.floor(q).astype(int);valid=(k[...,0]>=0)&(k[...,0]<480)&(k[...,1]>=0)&(k[...,1]<272);clipped=np.clip(k,[0,0],[479,271]);sr=role[clipped[...,1],clipped[...,0]];take=valid&(np.rint(sr[...,1])==sid)&np.isin(np.rint(sr[...,0]),[1,4])&(pred[...,0]==0);pred[take]=sr[take,:2];sourcexy[take]=k[take]
  # Native early return deliberately has no intrinsic template label. Retain it.
  nativeearly=(pred[...,0]>0)&(intr[...,0]==0)&(np.rint(owner[...,0])==7)
  mismatch=np.any(pred!=intr[...,:2],-1)&~nativeearly;sourceMismatch+=int(mismatch.sum())
  if mismatch.any():unexplained.append({'frame':entry['frame'],'xy':pos(mismatch,d)})
  rgbError=[]
  for yy,xx in np.argwhere((owner[...,3]==1)&(intr[...,0]>0)):
   k=sourcexy[yy,xx];expected=colour[k[1],k[0],:3];actual=rgb8(a['old-eye-rgba'][yy,xx,:3]);rgbChecked+=1
   if not np.array_equal(expected,actual):rgbError.append({'xy':[int(xx+x),int(271-yy-y)],'expected':expected.tolist(),'actual':actual.tolist()})
  assert not rgbError,rgbError
  # Preserve76 guard against348 overwrite, independently recomputed from source samples.
  protected=np.zeros((rh,rw),bool)
  for yy in range(rh):
   for xx in range(rw):
    v=b[yy+ry-y,xx+rx-x];sm=[a[f'S{i}-meta'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(7)];pt=[a[f'S{i}-point'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(4)];ok,sid,weight=supported(v[0],v[1],v[4],sm,pt,a['old-eye-owner'][yy+ry-y,xx+rx-x]);protected[yy,xx]=ok
  assert np.array_equal(protected,rec[...,14,2]>.5);assert np.array_equal(rec[...,0,:][protected],b[ry-y:ry-y+rh,rx-x:rx-x+rw,0,:][protected]);protectedTotal+=int(protected.sum())
  original=a['original333-0'];candidate=a['old-eye-rgba'];diff=np.any(original!=candidate,-1);colourDelta=np.max(abs(rgb8(original[...,:3]).astype(int)-rgb8(candidate[...,:3]).astype(int)),-1)
  assert not np.any(diff&~(np.any(oldintr!=intr,-1)|np.any(oldowner!=owner,-1)))
  row={'frame':entry['frame'],'serial':entry['serial'],'stage':entry['testStage82'],'index':entry['stageIndex82'],'morph':m['eyeFeature']['closeMorphs'],'original333':role_summary(oldintr,oldowner,d),'candidate333':role_summary(intr,owner,d),'changed333Cells':pos(diff,d),'max333RGB8Delta':int(colourDelta.max()),'nativeEarlyReturnCells':pos(nativeearly,d),'protectedCells':int(protected.sum()),'final348Iris':[{'eye':sid,'cells':[[int(xx+rx),int(271-yy-ry)]for yy,xx in np.argwhere(np.isin(np.rint(rec[...,3,0]),[2,3,4])&(np.rint(rec[...,3,1])==sid))]}for sid in [2,1]],'sky':m.get('sky87'),'legacyQ':a['main-legacy480-3'][2,2].tolist(),'physical':a['main-centre-raw3'][2,2].tolist(),'sourceUV':a['main-centre-raw6'][2,2].tolist(),'mainBeforeRGB8':rgb8(a['main-before'][2,2,:3]).tolist(),'camera':m['camera86'],'headInverse':m['eyeFeature']['inverse'],'manifestPlaneListSameFrame':all(p['sourceId']==d['identity']['sourceId']for p in m['planes'])and len(m['planes'])==len(a)}
  rows.append(row);pictures.append([np.flipud(rgb8(v[...,:3]))for v in [original,candidate,a['head-final']]]);nativepics.append(np.flipud(rgb8(a['native-final-rgba'][...,:3])))
 # Native output is a real final RT read, not a predicted interpolated display.
 for stage in ['phase','walk','sweep','blink']:
  ix=[i for i,r in enumerate(rows)if r['stage']==stage];ww=w*10;hh=h*10;board=Image.new('RGB',(ww*len(ix),hh*3+66),'#171d24');dr=ImageDraw.Draw(board)
  for j,i in enumerate(ix):
   dr.text((j*ww+3,3),f"{rows[i]['frame']} {stage}{rows[i]['index']}",fill='white')
   for c,title in enumerate(['original333 same input','candidate333','candidate final348']):
    board.paste(Image.fromarray(pictures[i][c]).resize((ww,hh),Image.Resampling.NEAREST),(j*ww,22+c*(hh+14)));dr.text((j*ww+3,22+c*(hh+14)),title,fill='#ff5cab')
  board.save(OUT/f'{stage}-comparison-nearest10.png')
  ims=[Image.fromarray(pictures[i][2]).resize((ww,hh),Image.Resampling.NEAREST)for i in ix];ims[0].save(OUT/f'{stage}-actual-final348.gif',save_all=True,append_images=ims[1:],duration=180,loop=0,disposal=2)
  nh,nw=nativepics[ix[0]].shape[:2];ns=Image.new('RGB',(nw*3*len(ix),nh*3+22),'#171d24');nd=ImageDraw.Draw(ns)
  for j,i in enumerate(ix):ns.paste(Image.fromarray(nativepics[i]).resize((nw*3,nh*3),Image.Resampling.NEAREST),(j*nw*3,22));nd.text((j*nw*3+3,4),str(rows[i]['frame']),fill='white')
  ns.save(OUT/f'{stage}-actual-native-nearest3.png')
 for i in [0,13,14,23,24,25,26,27,28]:
  for c,name in enumerate(['original333','candidate333','candidate-final348']):Image.fromarray(pictures[i][c]).save(OUT/f"frame{rows[i]['frame']}-{name}-native.png")
 before=json.loads((RUN/'CURRENT87.json').read_text());post=json.loads((RUN/'POST87.json').read_text());verify=json.loads((RUN/'VERIFY87.json').read_text());keys=['dirty','scenes','domain','playing','paused','optionsEnabled','options','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath','runInBackground','playerRunInBackground','input'];equal={k:before[k]==post[k]for k in keys};assert all(equal.values());assert all(v['equal']is True for v in verify['nativeComparisons']);assert st['composeRestoration87']['allRestored']and st['motionRestoration82']['allRestored']and st['editInputRestoration82']['sameAliveReference'];assert st['beforeMemory']['renderTextureCount']==st['afterMemory']['renderTextureCount']==30
 out={'status':'REAL29_FRAME_EXPERIMENT_NOT_DEFAULT','sourceId':st['sequenceId'],'original333Calibration':st['original333Calibration87'],'frames':rows,'sourceRoleMismatchCount':sourceMismatch,'unexplained':unexplained,'directTemplateRGB8Checked':rgbChecked,'protected76RGBExactCells':protectedTotal,'restore':equal,'nativeExact':len(verify['nativeComparisons']),'RTbeforeAfter':[st['beforeMemory']['renderTextureCount'],st['afterMemory']['renderTextureCount']],'internalAllocatedDeltaMiB':(st['afterMemory']['allocated']-st['beforeMemory']['allocated'])/1048576,'exporterManifestPlaneListIssueFrames':[r['frame']for r in rows if not r['manifestPlaneListSameFrame']],'limits':['Only333 has same-frame original/candidate paired GPU output. Final348/native are actual candidate output, not an old348 paired replay.','Cached bitmap nearest projection can still reshape/scale a tiny feature; counts alone are not quality proof.','Scene clock/cloud motion were observed, not frozen. Real lighting changes must not be classified as raster flicker.','The RAW_MANIFEST planes list is one frame stale (exporter report pointer); binary plane headers independently validate source/frame/serial/view. All marker-committed binary inputs remain available.']};(OUT/'RESULT87.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['frames','restore','original333Calibration']},indent=2));print(json.dumps([{'frame':r['frame'],'stage':r['stage'],'close':r['morph'].get('Fcl_EYE_Close'),'oldIris':[len(e['visibleIris'])for e in r['original333']],'newIris':[len(e['visibleIris'])for e in r['candidate333']],'finalIris':[len(e['cells'])for e in r['final348Iris']],'deltaCells':len(r['changed333Cells'])}for r in rows],indent=2))

if __name__=='__main__':main()
