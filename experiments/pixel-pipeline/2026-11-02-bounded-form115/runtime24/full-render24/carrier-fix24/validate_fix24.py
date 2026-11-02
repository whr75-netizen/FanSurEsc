"""Validate actual fixed GPU packets and current-input CPU counterfactuals."""
from pathlib import Path
import hashlib,json,sys,numpy as np
H=Path(__file__).resolve().parent;R=H.parent;BASE=R.parents[2];sys.path.insert(0,str(R));sys.path.insert(0,str(H));sys.path.insert(0,str(BASE/'eye-failures114'))
from report_full24 import read,plane,buffer,rgba
from trace_carrier24 import origins,points,direct
from trace114 import geometry,transferred_sample
from geometry114 import Face114
from pairing114 import compose

def main():
 oldTrace=read(H/'TRACE_CARRIER24.json');source=read(BASE/'argon23-runtime113/SOURCE113.json');rows=[];checked=0;changed=[];memory=[];skin=[];meanErrors=[];directChecks=0
 for oldRoot,newRoot in [(R/'sequence24',H/'close'),(R/'motion24',H/'motion')]:
  oldState=read(next(oldRoot.glob('STATE113-*-finished.json')));state=read(next(newRoot.glob('STATE113-*-finished.json')))
  assert state['PlayExited']and not state.get('error')and not state.get('restorationError')and state['motionRestoration82']['allRestored']
  assert state['forward102Disposed']and state['layer102Disposed']and state['carrierSourceDisposed111']and state['carrierNativeDisposed111']
  assert all(r['equal']for r in state['nativeComparisons72'])and not state['globalRestoreErrors']
  memory.append({'run':newRoot.name,'before':state['beforeMemory'],'after':state['afterMemory'],'nativeContentsCompared':len(state['nativeComparisons72']),
                 'deltaAllocatedMiB':(state['afterMemory']['allocated']-state['beforeMemory']['allocated'])/1048576})
  for oldPkt,pkt in zip(oldState['sequencePackets'],state['sequencePackets']):
   assert oldPkt['testStage82']==pkt['testStage82']and oldPkt['stageIndex82']==pkt['stageIndex82']
   oldP,p=Path(oldPkt['output']),Path(pkt['output']);m=read(p/'RAW_MANIFEST.json');roi=m['grid102']['eyeTopLeftROI'];w,h=roi[2:];cw=m['forward102']['canonicalSize'][0]//4
   ids=buffer(p/'curve-identity.f32').reshape(-1,4);oldIds=buffer(oldP/'curve-identity.f32').reshape(-1,4)
   assert np.array_equal(ids[:,:2],oldIds[:,:2]),'Canonical source part/owner changed'
   separateDepthDelta=float(abs(ids[:,2]-oldIds[:,2]).max())
   assert np.array_equal(buffer(p/'curve-colour.f32'),buffer(oldP/'curve-colour.f32'))
   a,c=origins(m,p);q=buffer(p/'ASSIGNED-depth24.f32').reshape(h,w,16,4);v=buffer(p/'ASSIGNED-visibility24.f32').reshape(q.shape)
   cells=buffer(p/'REGION113-cells.f32').reshape(512,7,4);currentCases=[]
   metas={part:plane(p/f'C-part{part}-meta.plane')[1][::-1]for part in [1,2,3]};fo=plane(p/'F-FinalOwner.plane')[1];fc=plane(p/'F-FinalRGBA.plane')[1]
   assert not np.any(fo[:,:,3]==-116)
   for y in range(h):
    for x in range(w):
     cx,cy=np.floor(np.array([roi[0]+x+.5,272-(272-roi[1]-roi[3]+y+.5)],np.float32)-a).astype(int)
     if min(cx,cy)<0 or cx>=cw or cy>=len(ids)//cw:continue
     at=cy*cw+cx;ident=ids[at];role,eye=map(lambda z:round(float(z)),ident[:2]);part={1:1,4:2,6:3}.get(role,0)
     if part==0:continue
     xy=points(roi,x,y);z=direct(metas[part],xy,c,eye);known=z>0;lo,hi=m['runtime24']['ringDepthRanges'][(eye-1)*2:eye*2];total=np.float32(0)
     for zz in z:
      if zz>0:total=np.float32(total+zz)
     fill=np.float32(total/np.float32(known.sum()))if known.any()else ident[2]if role==6 or lo<=ident[2]<=hi else np.float32(0)
     expected=np.where(known,z,fill);actual=q[y,x,:,2]
     assert np.array_equal(actual[known],z[known]);directChecks+=int(known.sum())
     if known.any():
      assert (actual[~known]>=z[known].min()).all()and(actual[~known]<=z[known].max()).all()
      error=float(abs(expected-actual).max());meanErrors.append({'sourceId':pkt['sourceId'],'tile':[x,y],'absDepthError':error,'ULP':float(error/np.spacing(fill))})
     else:assert np.array_equal(actual,expected),'The recovered source depth itself must be exact'
     if not known.any()and role==6 and not lo<=ident[2]<=hi:
      currentCases.append({'tile':[x,y],'canonical':[int(cx),int(cy)],'eye':eye,'role':role,'run':newRoot.name})
     checked+=16
   cases=currentCases
   ctx=geometry(p,m)if cases else None;face=Face114(ctx,source['ownSkinMask'])if cases else None
   for old in cases:
    x,y=old['tile'];cx,cy=old['canonical'];at=cy*cw+cx;eye,role=old['eye'],old['role'];z=q[y,x,:,2];assert(z==ids[at,2]).all()
    query=face.query(q[y,x,:,:2],z,eye,limit=m['runtime24']['socketDiameters'][eye-1]);vis=np.array([r['faceInterval']for r in query]);assert np.array_equal(vis.astype(np.float32),v[y,x,:,:2])
    canvas=plane(p/'L0-RGBA.plane')[1][y*4+1,x*4+1];meta=plane(p/'L0-META.plane')[1][y*4+1,x*4+1];hm=plane(p/'S4-meta.plane')[1][y*4:y*4+4,x*4:x*4+4];hc=plane(p/'S4-rgba.plane')[1][y*4:y*4+4,x*4:x*4+4];selected=buffer(p/'curve-colour.f32').reshape(-1,4)[at]
    case={'fine':[{'fineXY':[i%4,i//4]}for i in range(16)]}
    before=compose(case,np.zeros((16,2)),np.full(16,np.nan),canvas,meta,selected,role,eye,hm,hc)
    after=compose(case,vis,z,canvas,meta,selected,role,eye,hm,hc)
    assert np.array_equal(fc[y,x],after['linearRGBA'])and fo[y,x,0]==after['role']and fo[y,x,1]==after['owner']and fo[y,x,3]==after['status']
    rgbChange=not np.array_equal(before['linearRGBA'],after['linearRGBA']);changed.append({'sourceId':pkt['sourceId'],'frame':pkt['frame'],'stage':pkt['testStage82'],'tile':[x,y],
         'sourceDepth':float(ids[at,2]),'actualGPUOwner':fo[y,x].tolist(),'pairedFaceQueries':16,'faceInterval16':vis.sum(0).tolist(),
         'sameCurrentInputOldPolicyCPU':before,'actualFixedGPUAndMatchedCPU':after,'causalRGBChange':rgbChange})
    if old['run']=='close':
     sample=int(cells[at,5,1])-1;assert sample>=0
     witnessMeta=plane(p/'D-lid-meta.plane')[1][::-1].reshape(-1,4)[sample];assert witnessMeta[0]==ids[at,2]
     uv=plane(p/'D-lid-uv.plane')[1][::-1].reshape(-1,4)[sample];rest=plane(p/'D-lid-rest.plane')[1][::-1].reshape(-1,4)[sample]
     witness=transferred_sample(ctx,3,rest[:3],int(round(float(uv[2]))))
     sourceVis=face.query([witness['nativePhysicalXY']],[witness['nativeDepth']],eye,limit=m['runtime24']['socketDiameters'][eye-1])[0]
     skin.append({'sourceId':pkt['sourceId'],'tile':[x,y],'nativeSource':witness,'sourceFaceVisibility':sourceVis,'destinationXY16':q[y,x,:,:2].tolist(),
                  'destinationFaceVisibility':query,'sourceRegisteredSampleXY':(a+(np.array([sample%m['forward102']['denseSize'][0],sample//m['forward102']['denseSize'][0]])+.5)/8).tolist()})
   oldRGB=plane(oldP/'F-FinalRGBA.plane')[1];oldOwner=plane(oldP/'F-FinalOwner.plane')[1]
   rows.append({'sourceId':pkt['sourceId'],'frame':pkt['frame'],'stage':pkt['testStage82'],'canonicalRoleOwnerRGBAExactBaseline':True,'separatePlaySelectedSourceDepthMaxDelta':separateDepthDelta,
                'unknown':0,'separatePlayRGBFloatDifferences':int(np.any(oldRGB!=fc,axis=2).sum()),
                'separatePlayFinalRoleOwnerDifferences':int(np.any(oldOwner[:,:,:2]!=fo[:,:,:2],axis=2).sum()),
                'warning':'Separate Play canvas/hair lighting inputs differ; only same-current-input CPU counterfactual isolates causal RGB changes.'})
 allResults=[read(H/k/'RESULT_FULL24.json')for k in ['close','motion']]
 report={'actualGPUFrames':40,'assignedDepthSamplesChecked':checked,'measuredDepthSamplesBitExact':directChecks,
         'transportedMeanMaxAbsDepthError':max(x['absDepthError']for x in meanErrors),'transportedMeanMaxULP':max(x['ULP']for x in meanErrors),
         'meanNote':'Recorded GPU mean can differ from sequential CPU float32 arithmetic; no accuracy threshold was loosened. Measured depths and zero-raster selected-source fallback remain bit-exact. No compiler-cause claim.',
         'zeroCarrierCases':len(changed),'actualNewFaceQueriesCPUExact':16*len(changed),
         'causalRGBChanges':sum(x['causalRGBChange']for x in changed),'changes':changed,'rows':rows,'close75SkinEvidence':skin,
         'eyePaletteRGB8Errors':sum(p['paletteRGB8Errors']for r in allResults for f in r['frames']for p in f['finalVisibleParts']),
         'memory':memory,'product77DefaultChanged':False,'GPUTimeMeasured':False,'wholeTemporalStabilitySolved':False}
 (H/'VALIDATED_FIX24.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:v for k,v in report.items()if k not in ['rows','changes','close75SkinEvidence']},ensure_ascii=False))
 print('Close75 source visibility',[(x['sourceFaceVisibility']['faceInterval'],x['nativeSource']['nativePhysicalXY'],x['sourceRegisteredSampleXY'])for x in skin])
if __name__=='__main__':main()
