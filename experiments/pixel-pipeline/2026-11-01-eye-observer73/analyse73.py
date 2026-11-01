"""Validate one frozen real packet and replay allocator; no Unity calls."""
from pathlib import Path
import sys,json,hashlib,struct,csv
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'apply-capture66'
if not OLD.exists():OLD=HERE.parent/'2026-10-31-apply-capture66'
sys.path.insert(0,str(OLD));from analyse_capture68 import Reader,plane,rgb8
def completed(path):
 raw=path.read_bytes();h=hashlib.sha256(raw).hexdigest();m=path.parent/f'ok-{h}-{len(raw)}.complete';assert m.is_file() and m.stat().st_size==0,'Missing/mismatched marker';return raw
def read(path,counts):
 raw=completed(path);r=Reader(path);assert r.s()=='pixel-eye-readback70/v1';kind=r.s();id=r.identity();convention=r.s();roi=[r.i() for _ in range(4)];stride=r.i();x,y,w,h=roi;assert stride==(48 if counts else 256)
 a=np.empty((2,h,w,12) if counts else (h,w,64),np.float32)
 if counts:
  assert kind=='FeaturePacket19:a,b,uv'
  for eye in range(2):
   for row in range(h):
    assert [r.i(),r.i(),r.i()]==[eye,row,(eye*h+row)*w];a[eye,row]=r.a(w*12).reshape(w,12)
 else:
  assert kind=='Pixel348:sixteenFloat4InShaderOrder'
  for row in range(h):
   assert [r.i(),r.i()]==[y+row,(y+row)*480+x];a[row]=r.a(w*64).reshape(w,64)
 r.end();assert np.isfinite(a).all();return {'identity':id,'roi':roi,'stride':stride,'bytes':len(raw),'dataSHA256':hashlib.sha256(raw).hexdigest(),'marker':f'ok-{hashlib.sha256(raw).hexdigest()}-{len(raw)}.complete'},a
def main():
 for name in ['CELL_RECORDS73.json','RESULT73.json','VALIDATED_CAPTURE73.json','FINAL73.png','EYE73.png','EYE73-nearest20.png','FEATURES73-nearest20.png']:
  if (HERE/name).exists():raise FileExistsError('Existing analysis result; inspect before another run: '+name)
 state=json.loads(sorted(HERE.glob('STATE73-*.json'))[-1].read_text());assert state['stage']=='finished' and state['PlayExited'] and state['observerRemoved'] and not state.get('error') and not state.get('restorationError')
 packet=HERE/Path(state['output']).name
 if not packet.exists():packet=Path(state['output'])
 ch,c=read(packet/'eye-counts73.bin.partial',True);rh,r=read(packet/'eye-records73.bin.partial',False)
 for h in [ch,rh]:
  assert h['identity']=={'sourceId':state['sourceId'],'viewId':state['sourceView'],'frameIndex':state['frameIndex'],'renderSerial':state['mainRenderedSerial335']}
 assert ch['roi']==rh['roi']==state['eyeReadback70']['roiGpuBottomLeft'];assert state['eyeReadback70']['countsProducerRan'] and not state['eyeFeature']['featureCountsSkippedByDispatch'];x0,y0,w,h=ch['roi'];rec=r.reshape(h,w,16,4);stable=state['eyeFeature']['stableIds']
 iris=np.float32(np.float32(c[...,2]+c[...,3])+c[...,4]);alloc=np.zeros((2,h,w),bool);summary=[];rows=[]
 for eye in range(2):
  area=np.float32(0)
  for n in iris[eye].flat:area=np.float32(area+np.float32(n/np.float32(16)))
  desired=int(np.floor(np.float32(area+np.float32(.5))));candidates=[]
  for y,x in np.argwhere(iris[eye]>0):
   own=c[eye,y,x];cost=float(np.float32(max(own[1],own[5],own[6])-iris[eye,y,x]));candidates.append((cost,float(own[8]),float(own[9]),int(y+y0),int(x+x0),int(y),int(x)))
  candidates.sort()
  for rank,k in enumerate(candidates):alloc[eye,k[-2],k[-1]]=rank<desired
  sid=stable[eye];visible=(np.rint(rec[...,3,1]).astype(int)==sid)&np.isin(np.rint(rec[...,3,0]).astype(int),[2,3,4]);points=[]
  for rank,k in enumerate(candidates):
   y,x=k[-2:];v=rec[y,x];why='iris-visible' if visible[y,x] else 'not-allocated' if not alloc[eye,y,x] else 'Own-source-missing' if v[8,0]==2 else 'hair/brow/body-stage' if v[1,3] in [3,4,5] else 'representative/other-eye-or-feature; raw subcells needed'
   row={'eyeIndex':eye,'stableId':sid,'xyTopLeft':[int(x+x0),int(271-(y+y0))],'irisSamples':float(iris[eye,y,x]),'rank':rank,'allocated':bool(alloc[eye,y,x]),'actualVisibleFeature':int(round(float(v[3,0]))),'actualEyeId':int(round(float(v[3,1]))),'actualWinSamples':float(v[3,2]),'representativeIndex':float(v[3,3]),'owner':v[1].tolist(),'audit':v[8].tolist(),'support':v[6].tolist(),'pigmentProvenance':v[7].tolist(),'reason':why};rows.append(row);points.append(row['xyTopLeft'])
  summary.append({'eyeIndex':eye,'stableId':sid,'visibleSourceIrisAreaCells':float(area),'roundedAllocationTarget':desired,'positiveSourceCandidateCells':len(candidates),'allocatedCellsTopLeft':[[int(x+x0),int(271-(y+y0))] for y,x in np.argwhere(alloc[eye])],'actualVisibleIrisCellsTopLeft':[[int(x+x0),int(271-(y+y0))] for y,x in np.argwhere(visible)],'allocatedButNotFinalIris':int((alloc[eye]&~visible).sum()),'unallocatedButFinalIris':int((~alloc[eye]&visible).sum())})
 # Keep every cell's actual records, no guessed eye/background labels.
 allrows=[]
 for y in range(h):
  for x in range(w):allrows.append({'xyTopLeft':[x+x0,271-(y+y0)],'countsBothEyes':c[:,y,x].tolist(),'fields':rec[y,x].tolist()})
 checks=[];arrays={};headers={}
 for p in packet.glob('*.plane'):
  ph,a=plane(p);assert ph['sourceId']==state['sourceId'] and ph['frameIndex']==state['frameIndex'] and ph['renderSerial']==state['mainRenderedSerial335'];arrays[p.stem]=a;headers[p.stem]=ph
 final=np.zeros((544,960,4),np.float32);covered=np.zeros((544,960),bool)
 for name,a in arrays.items():
  if name.startswith('final-strip-'):
   x,y,ww,hh=headers[name]['roi'];assert not covered[y:y+hh,x:x+ww].any();final[y:y+hh,x:x+ww]=a;covered[y:y+hh,x:x+ww]=True
 assert covered.all();Image.fromarray(np.flipud(rgb8(final[...,:3]))).save(HERE/'FINAL73.png')
 sf=arrays['source-final'];sx,sy,sw,sh=headers['source-final']['roi'];eyeRgb=sf[y0-sy:y0-sy+h,x0-sx:x0-sx+w,:3];assert eyeRgb.shape==(h,w,3)
 Image.fromarray(np.flipud(rgb8(eyeRgb))).save(HERE/'EYE73.png');im=Image.open(HERE/'EYE73.png');im.resize((w*20,h*20),Image.Resampling.NEAREST).save(HERE/'EYE73-nearest20.png')
 colours=np.array([[25,27,31],[230,225,210],[125,65,40],[180,105,50],[255,240,130],[35,35,40],[120,90,85],[70,70,75]],np.uint8);vf=np.rint(rec[...,3,0]).astype(int);vf=np.where((vf>=0)&(vf<8),vf,0)
 Image.fromarray(np.flipud(colours[vf])).resize((w*20,h*20),Image.Resampling.NEAREST).save(HERE/'FEATURES73-nearest20.png')
 maxerr=float(np.max(np.abs(eyeRgb-rec[... ,0,:3])));base=json.loads((HERE/'CURRENT73.json').read_text());post=json.loads((HERE/'POST73.json').read_text());statekeys=['dirty','scenes','domain','options','optionsEnabled','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath','runInBackground','playerRunInBackground','playing','paused','compiling','updating'];statecheck={k:base.get(k)==post.get(k) for k in statekeys}
 repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');disk=json.loads((HERE/'DISK_BEFORE73.json').read_text());diskChanges=[p for p,hsh in disk['files'].items() if hashlib.sha256((repo/p).read_bytes()).hexdigest()!=hsh]
 result={'sourceId':state['sourceId'],'frameIndex':state['frameIndex'],'renderSerial':state['mainRenderedSerial335'],'PlayEntries':state['PlayEntries'],'normalHistoryResetRequested':state['resetHistoryRequestedByObserver'],'sameFrameReadback':state['frameUnchangedDuringReadback'],'counts':ch,'records':rh,'countsProducerRan':True,'modeFlags':state['modeFlags'],'eyes':summary,'candidateRows':rows,'recordVsSourceFinalRGBMaxAbsLinear':maxerr,'actualIrisPigmentRoles':np.unique(rec[np.isin(vf,[2,3,4]),7,2]).tolist(),'stateChecks':statecheck,'nativeExactComparisons':sum(v.get('equal') is True for v in state['nativeComparisons72']),'nativeUnverified':[v for v in state['nativeComparisons72'] if v.get('equal') is not True],'shaderGlobalRestoreErrors':state['globalRestoreErrors'],'disk31Changed':diskChanges,'RTbefore':state['beforeMemory']['renderTextureCount'],'RTafter':state['afterMemory']['renderTextureCount'],'internalAllocatedDeltaMiB':(state['afterMemory']['allocated']-state['beforeMemory']['allocated'])/1048576,'captureReadbackReleaseDeltaMiB':(state['afterCaptureReleaseMemory']['allocated']-state['readyMemory']['allocated'])/1048576,'completionProtocol':'Per-buffer data validated by SHA256/byte-count zero-byte CreateNew marker. No move/delete/overwrite. Bundle completion is withheld unless independent packet/state validation passes.','limits':['One frozen current normal pose; not old frame100/101 or motion/blink reproduction','Counts store per-cell feature weights, not individual per-subsample support/occluder decisions','Own template coordinate/role provenance captured in records, but exact TemplateRGBA/TemplateRole bank pixels were not separately read; no full pigment-source equality claim','Native AssetImporter object at ProjectSettings/ProjectSettings.asset unavailable after Play; PlayerSettings object itself and44 available snapshots ExactUTF8','No eye candidate/product integration or aesthetic success claimed']}
 (HERE/'CELL_RECORDS73.json').write_text(json.dumps({'sourceId':state['sourceId'],'rows':allrows},separators=(',',':'))+'\n');(HERE/'RESULT73.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert all(statecheck.values()) and not diskChanges and not state['globalRestoreErrors'] and maxerr<1e-5
 marker=HERE/'VALIDATED_CAPTURE73.json';assert not marker.exists();payload={'sourceId':state['sourceId'],'countsSHA256':ch['dataSHA256'],'recordsSHA256':rh['dataSHA256'],'resultSHA256':hashlib.sha256((HERE/'RESULT73.json').read_bytes()).hexdigest(),'status':'one-frame-data-valid; native importer limit retained'}
 with marker.open('x',encoding='utf-8') as f:json.dump(payload,f,indent=2)
 print(json.dumps({k:result[k] for k in ['sourceId','countsProducerRan','eyes','recordVsSourceFinalRGBMaxAbsLinear','actualIrisPigmentRoles','nativeExactComparisons','nativeUnverified','internalAllocatedDeltaMiB','captureReadbackReleaseDeltaMiB']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
