"""Actual final GPU guard, pigment provenance and fixed-input regression."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'apply-capture66'));from analyse_capture68 import Reader,plane,rgb8
sys.path.insert(0,str(HERE.parent/'eye-observer73'));from analyse73 import read
sys.path.insert(0,str(HERE.parent/'whole-eye75'));from audit75 import texture
from test76 import supported

def packet(path):
 manifest=json.loads((path/'RAW_MANIFEST.json').read_text());assert(path/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((path/'RAW_MANIFEST.json').read_bytes()).hexdigest()
 r=Reader(path/'baseline76.buffer');assert r.s()=='baseline76/v1';sid,view=r.s(),r.s();frame,serial=r.i(),r.i();roi=[r.i()for _ in range(4)];assert r.i()==96;x,y,w,h=roi;b=r.a(w*h*24).reshape(h,w,6,4);r.end();assert np.all(b[...,5,2]==frame)and np.all(b[...,5,3]==serial-1)
 ch,c=read(path/'eye-counts76.bin.partial',True);rh,z=read(path/'eye-records76.bin.partial',False);ident={'sourceId':sid,'viewId':view,'frameIndex':frame,'renderSerial':serial};assert ch['identity']==rh['identity']==ident
 a={};heads={}
 for p in path.glob('*.plane'):
  ph,ar=plane(p);assert all(ph[k]==ident[k]for k in ['sourceId','frameIndex','renderSerial']);assert ph['viewId']==('main-final'if p.stem.startswith('final-strip-')else view);a[p.stem]=ar;heads[p.stem]=ph
 result=dict(manifest=manifest,identity=ident,roi=roi,baseline=b,counts=c,eyeROI=ch['roi'],records=z.reshape(z.shape[0],z.shape[1],16,4),arrays=a,headers=heads)
 if(path/'original76.buffer').exists():
  r=Reader(path/'original76.buffer');assert r.s()=='original76/v1';assert[r.s(),r.s(),r.i(),r.i()]==[sid,view,frame,serial];assert[r.i()for _ in range(4)]==roi;assert r.i()==256;result['original']=r.a(w*h*64).reshape(h,w,16,4);r.end()
 return result
def full(a,heads):
 f=np.zeros((544,960,4),np.float32)
 for n,v in a.items():
  if n.startswith('final-strip-'):
   x,y,w,h=heads[n]['roi'];f[y:y+h,x:x+w]=v
 return f
def main():
 run=HERE/'run-j';OUT=HERE/'final';OUT.mkdir(exist_ok=False);state=json.loads(sorted(run.glob('STATE76-*.json'))[-1].read_text());assert state['stage']=='finished'and state['PlayExited']and not state.get('error')and not state.get('restorationError')
 entries=state['sequencePackets'];assert len(entries)==6;assert [z['frame']for z in entries]==list(range(entries[0]['frame'],entries[0]['frame']+6));assert [z['serial']for z in entries]==list(range(entries[0]['serial'],entries[0]['serial']+6))
 _,_,bank=texture('TemplateRGBA.asset','u1');_,_,bankrole=texture('TemplateRole.asset','<f4')
 results=[];data=[];pigments=[]
 for entry in entries:
  d=packet(Path(entry['output']));data.append(d);a=d['arrays'];b=d['baseline'];rec=d['records'];x,y,w,h=d['roi'];rx,ry,rw,rh=d['eyeROI'];pred=np.zeros((rh,rw),bool);maxweight=0
  for yy in range(rh):
   for xx in range(rw):
    ly,lx=yy+ry-y,xx+rx-x;v=b[ly,lx];sm=[a[f'S{i}-meta'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(7)];pt=[a[f'S{i}-point'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(4)];co=a['old-eye-owner'][ly,lx]
    ok,sid,weight=supported(v[0],v[1],v[4],sm,pt,co);pred[yy,xx]=ok
    if not ok:continue
    out=rec[yy,xx];assert round(float(out[3,1]))==sid;maxweight=max(maxweight,abs(float(out[3,2])-weight));assert np.array_equal(out[0],v[0]);assert np.array_equal(out[11],v[1]);assert np.array_equal(out[12],v[2])and np.array_equal(out[13],v[3]);assert out[6,3]>0 and out[10,3]>0
    px,py,fam,kind=out[7];rgb=rgb8(out[0,:3]);row={'frame':entry['frame'],'xyTopLeft':[xx+rx,271-(yy+ry)],'eye':sid,'baselineRole':round(float(v[1,0])),'rgb8':rgb.tolist(),'pigment':out[7].tolist(),'support':out[6].tolist()}
    if kind==1:
     px,py=int(round(float(px))),int(round(float(py)));assert int(round(float(bankrole[py,px,0])))==round(float(fam));assert int(round(float(bankrole[py,px,1])))==sid;row['expectedBankRGB8']=bank[py,px,:3].tolist();row['RGB8maxError']=int(np.max(np.abs(rgb.astype(int)-bank[py,px,:3].astype(int))));assert row['RGB8maxError']==0
    else:assert fam==6 and kind==2;row['source']='precomposed native eyeline; S3 UV/primitive retained, not colour-bank substitution'
    pigments.append(row)
  actual=rec[...,14,2]>.5;assert np.array_equal(pred,actual),'GPU/CPU guard mismatch';assert maxweight<2e-5
  post=a['head-final'];guardRgb=post[ry-y:ry-y+rh,rx-x:rx-x+rw][pred];assert np.array_equal(guardRgb,rec[...,0,:][pred]);orig=d['original'][ry-y:ry-y+rh,rx-x:rx-x+rw];assert d['manifest']['frozenOriginal76']['sameFrame']
  changedColour=np.max(abs(orig[...,0,:]-rec[...,0,:]),axis=2)>1e-6;reserved=[];budgets=[];allowedRemoved=np.zeros((rh,rw),bool)
  for eye,sid in enumerate([int(z[3])for z in d['manifest']['eyeFeature']['centres']]):
   flags=(d['counts'][eye,...,10]>.5);expected=pred&(np.rint(rec[...,1,0])==7)&(np.rint(rec[...,3,1])==sid);assert np.array_equal(flags,expected),'Native reservation must match same-eye protected line';reserve=int(flags.sum());area=np.float32(0)
   for value in d['counts'][eye,...,5].flat:area=np.float32(area+np.float32(value/16))
   budget=int(np.floor(np.float32(area+.5)));reserved.append(reserve);budgets.append(budget)
   if reserve:allowedRemoved|=(np.rint(orig[...,3,1])==sid)&np.isin(np.rint(orig[...,3,0]),[5,7])&~pred
  outsideError=float(abs(orig[...,0,:][~pred&~allowedRemoved]-rec[...,0,:][~pred&~allowedRemoved]).max(initial=0));assert outsideError<1e-6;assert not(changedColour&~pred&~allowedRemoved).any();assert not(np.isin(np.rint(rec[...,3,0]),[5,7])&allowedRemoved).any()
  results.append({'identity':d['identity'],'protectedCells':int(pred.sum()),'maxWeightAbsError':maxweight,'originalVsFixedChangedCells':[[int(xx+rx),int(271-(yy+ry))]for yy,xx in np.argwhere(changedColour)],'reservedNativeLineCellsByEye':reserved,'nativeAreaBudgetsByEye':budgets,'duplicateNativeLineRemoved':int((changedColour&allowedRemoved).sum()),'unaffectedMaxRGBError':outsideError,'irisCells':int(np.isin(np.rint(rec[...,3,0]),[2,3,4]).sum()),'nativeLineCells':int((np.rint(rec[...,3,0])==5).sum()),'sourceFrame':d['manifest']['sourceFrame'],'evaluatedFrame':d['manifest']['evaluatedFrame'],'deltaTime':entry['deltaTime'],'visits':d['manifest']['baseline76']['visits']})
 oldstate=json.loads(sorted((HERE/'run-b').glob('STATE76-*.json'))[-1].read_text());old=packet(Path(oldstate['output']));new=data[0];same={n:np.array_equal(v,new['arrays'][n])for n,v in old['arrays'].items()if n.startswith('S')};same['baseline5']=np.array_equal(old['baseline'][...,:5,:],new['baseline'][...,:5,:]);same['counts']=np.array_equal(old['counts'],new['counts'])
 oldpost=new['original'][...,0,:];newpost=new['baseline'][...,0,:].copy();x,y,w,h=new['roi'];rx,ry,rw,rh=new['eyeROI'];newpost[ry-y:ry-y+rh,rx-x:rx-x+rw]=new['records'][...,0,:];changed=np.max(np.abs(oldpost-newpost),axis=2)>1e-6;coords=[[int(xx+x),int(271-(yy+y))]for yy,xx in np.argwhere(changed)]
 for name,a0 in [('BEFORE_SOURCE',new['baseline'][...,0,:]),('OLD_PRODUCT',oldpost),('FIXED_PRODUCT',newpost)]:Image.fromarray(np.flipud(rgb8(a0[...,:3]))).save(OUT/(name+'76.png'))
 board=Image.new('RGB',(w*20*3,h*20+28),'#15191e');draw=ImageDraw.Draw(board)
 for i,name in enumerate(['BEFORE_SOURCE','OLD_PRODUCT','FIXED_PRODUCT']):
  im=Image.open(OUT/(name+'76.png'));board.paste(im.resize((w*20,h*20),Image.Resampling.NEAREST),(i*w*20,28));draw.text((i*w*20+5,8),name,fill='white')
 board.save(OUT/'COMPARISON76-nearest20.png')
 firstFull=full(new['arrays'],new['headers']);oldFull=full(old['arrays'],old['headers']);Image.fromarray(np.flipud(rgb8(firstFull[...,:3]))).save(OUT/'FIXED_FULL76.png');Image.fromarray(np.flipud(rgb8(oldFull[...,:3]))).save(OUT/'OLD_FULL76.png');diff=np.max(np.abs(oldFull-firstFull),axis=2)>1e-6
 # Head local -> main final is an integer join at unchanged 2x pixel pitch.
 ys,xs=np.where(diff);bbox=None if len(xs)==0 else[int(xs.min()),int(543-ys.max()),int(xs.max()),int(543-ys.min())]
 strip=Image.new('RGB',(w*12*6,h*12+24),'#15191e');dd=ImageDraw.Draw(strip)
 for i,d in enumerate(data):
  im=Image.fromarray(np.flipud(rgb8(d['arrays']['head-final'][...,:3])));strip.paste(im.resize((w*12,h*12),Image.Resampling.NEAREST),(i*w*12,24));dd.text((i*w*12+4,5),str(d['identity']['frameIndex']),fill='white')
 strip.save(OUT/'SEQUENCE76-nearest12.png')
 native=state['nativeComparisons72'];before=json.loads((HERE/'CURRENT76.json').read_text());after=json.loads((run/'POST76.json').read_text());keys=['dirty','scenes','domain','playing','paused','optionsEnabled','options','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath','runInBackground','playerRunInBackground'];equal={k:before[k]==after[k]for k in keys};assert all(equal.values())
 repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');base=json.loads((HERE/'DISK_BEFORE76.json').read_text())['files'];changedDisk=[p for p,sha in base.items()if hashlib.sha256((repo/p).read_bytes()).hexdigest()!=sha];contract=json.loads((HERE/'PATCH_FINAL76.json').read_text());assert changedDisk==[contract['path']];assert hashlib.sha256((repo/contract['path']).read_bytes()).hexdigest()==contract['afterSHA256']
 frameDiffs=[int(np.any(data[i]['arrays']['head-final']!=data[i-1]['arrays']['head-final'],axis=2).sum())for i in range(1,6)]
 result={'status':'minimal source-feature overwrite fix applied and GPU-verified; not complete whole-eye/temporal correction','sourceSequence':state['sequenceId'],'frames':results,'sameFrameFrozenGPUComparison':True,'historicalReferenceInputsExactlyEqual':same,'changedHeadCellsVsFrozenOriginal':coords,'historicalFullReferenceComparison':'Different inputs; not a paired whole-frame regression','consecutiveHeadRGBChangedCells':frameDiffs,'nativeExact':sum(v.get('equal')is True for v in native),'nativeUnverified':[v for v in native if v.get('equal')is not True],'stateEqual':equal,'restoration':{k:state.get(k)for k in ['PlayExited','optionsRestored','timeRestored','pipelineRestored','backgroundRestored','ownedProbeReleased76','globalRestoreErrors']},'RTbefore':state['beforeMemory']['renderTextureCount'],'RTafter':state['afterMemory']['renderTextureCount'],'internalAllocatedDeltaMiB':(state['afterMemory']['allocated']-state['beforeMemory']['allocated'])/1048576,'captureOnlyAllocatedDeltaMiB':(state['afterCaptureReleaseMemory']['allocated']-state['readyMemory']['allocated'])/1048576,'changedProtectedDiskFiles':changedDisk,'actualRuntimeProductShaderPath':state['actualRuntimeProductShaderPath'],'pigments':pigments,'limits':['Six actual consecutive normal frames in bin0 with small continuous source changes and very short deltaTime; not a walk/rotation/blink or full subpixel-motion proof','Current-source guard does not define new whole-eye keyforms or time-continuous cache placement','Prepared baseline metadata is inherited; current sampled support/barycentric provenance is recorded separately','Existing lower-like S0 shade and regions outside protected precomposed features are unchanged','One non-dirty AssetImporter object unavailable after Play; PlayerSettings itself and all29 dirty objects exact','Internal Unity allocation delta is not physical working-set or proof of leakage']}
 (OUT/'FINAL_VALIDATION76.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items()if k not in ['pigments','frames','historicalReferenceInputsExactlyEqual']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
