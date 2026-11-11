"""Summarize already completed observations. No Unity/GPU/cleanup calls."""
from pathlib import Path
import json,os
H=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def public(p):
 d=read(p);logs=d['result']['structuredContent']['data']['executionLogs'];return json.loads(logs.split('[Log] ',1)[1])
def main():
 runs=[]
 for name in ['phase-run','gate/phase-run','gate-alpha/phase-run','gate-alpha/motion-run','native-proof/phase-run','native-proof/readback-run','native-proof/typed-run','native-proof/motion-run']:
  root=H/name;s=read(next(root.glob('STATE113-*-finished.json')))
  assert s['PlayExited']and not s.get('restorationError')and not s['globalRestoreErrors']
  runs.append({'run':name,'frames':len(s.get('sequencePackets')or[]),'captureError':s.get('error'),'before':s['beforeMemory'],'after':s['afterMemory'],
   'delta':{k:s['afterMemory'][k]-s['beforeMemory'][k]for k in ['allocated','reserved','mono','renderTextureCount']},
   'nativeEqual':sum(v['equal']is True for v in s['nativeComparisons72']),
   'nativeUnavailable':[v for v in s['nativeComparisons72']if v['equal']is None],
   'nativeUnequal':[v for v in s['nativeComparisons72']if v['equal']is False],
   'sceneBefore':s['beforeScenes'],'sceneAfter':s['afterScenes'],'inputReferenceAndJSON':s['editInputRestoration82']['sameAliveReference']and s['editInputRestoration82']['exactJSON'],
   'settingsRestored':all(s[k]for k in ['optionsRestored','timeRestored','pipelineRestored','backgroundRestored']),
   'ownedForwardDisposed':s['forward102Disposed'],'observerRemoved':s['observerRemoved']})
 before=public(H/'preflight/READ_REPLY.json');after=public(H/'postflight-native/READ_REPLY.json')
 assert after['ownedHairMaterials25']==after['createdHairTextures25']==0 and not after['playing']and not after['compiling']and not after['transitioning']
 memory={'UnityCounterAPIs':{'allocated':'Profiler.GetTotalAllocatedMemoryLong','reserved':'Profiler.GetTotalReservedMemoryLong','mono':'Profiler.GetMonoUsedSizeLong','renderTextureCount':'Resources.FindObjectsOfTypeAll<RenderTexture>().Length'},
  'runs':runs,'separatePublicPointBefore':before,'separatePublicPointAfter':after,
  'pointDifferenceNotSumOfRunSpikes':{k:after[k]-before[k]for k in ['allocated','reserved','mono','renderTextureCount']},
  'osSinglePoint':read(H/'OS_POST26.json'),'newHeadHairRTsTotalActualBytes':387072,
  'codeLifetime':'HeadHair25 owns four material clones and RTs per instance; both continuous and expanded physical instances Dispose. RegionDriver shared16,928B and column16,384B buffers use B()/owned buffer list. SourcePigment owns native27,072B buffer/CPU array, constructor failure and Dispose release buffer, Dispose nulls array. New per-view native resources43,456B. Existing model/view/topology checks invalidate stale owners. Release76 disposes and nulls Forward/Layer/Motion. No new static arrays or GPU feedback.',
  'causeNotDetermined':'Public named material/RT counts are0, but retained native allocations/Editor caches/managed roots were not profiled. A decrease after idle is not proof that every allocation is freed. No forced GC, Unload, private reflection, profiler dump or cleanup was used.',
  'scenePublicProbeNote':'JsonUtility log omitted the dynamic scenes array. Scene preservation is evidenced by the completed capture beforeScenes/afterScenes, not by an inferred empty scene list.'}
 (H/'MEMORY26.json').write_text(json.dumps(memory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lib=read(H/'LIBRARY_FILES26.json')
 for v in lib['directCreateResults']:
  v.pop('metadataHelperOutput',None);v['status']='succeeded'
 lib['localOSHasSetxattr']=hasattr(os,'setxattr');lib['localXattrsApplied']=False;lib['identityFallback']='Exact returned IDs/version/path are retained here; do not create duplicates on future edits.'
 (H/'LIBRARY_FILES26.json').write_text(json.dumps(lib,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 status={'scope':'Isolated runtime candidate; product77 default and original user30 unchanged',
  'implemented':['Complete candidate output domain shared by clean canvas, carrier queries, physical hair and final composition',
   'Selected source witness in existing cell channel6, chosen by final part identity, without changing RGB/mass allocation',
   'Weighted native source visibility compared exactly to same intrinsic alpha; curve source uses actual deformed PIGMENT world points and strict original ray, with neither own nor shared exemptions',
   'Additional105 active ipsilateral source-affiliation triangles applied only to certified destination rays; original source visibility never consumes the additional mask'],
  'actualGPU':'Latest strict native-proof blink4 + motion28 completed; earlier ROI2, failed-unit4 and provisional alpha32 preserved as separate inputs. Two later observation failures (stride32 passed to stride16 helper) normally exited and restored, no valid capture marker. Final observer serializes exact CPU upload array separately from stride16 GPU queries.',
  'confirmedRegressions':'Latest32 frames: crop0, direct source RGBA/LUT errors0, 922 selected witness checks; phase10 final eye labels unchanged across measured0.999878px; Close100 iris/white0; reopen labels equal. Strict original curve rays463 match same-frame CPU. Two turn rejections match32 CPU queries and fail ipsilateral/socket policy. Five critical corrected queries80 match GPU; old-mask CPU counterfactual remains separately labelled.',
  'withdrawn':'Provisional gate-alpha used display-position curve source queries and was not adopted. Earlier wrong-part material-to-geometry audit is withdrawn; actual PIGMENT vertex/barycentric data is now used. NativeProof26 source shader SHA9dfa37cadc36460d2d3bce8868aebb3222301dca65557f7886214cf07a0c19a4.',
  'remaining':['Full-face weak blush/gradient/AA feature hierarchy and per-stage region binding are still unconfirmed; new face LUT bindings0.',
   'Full-face finite outline palette/LineTone/AA ownership remains dependent on those labels; eye LUT checks do not prove whole-face quantization.',
   'Hair OFF/ON, actual multiview, model reimport/invalidation and broader expressions were not newly validated.',
   'Optional two-ring ownership extension and fixed1/2-pixel/6+2/symmetry design policies were not adopted.',
   '42 of846 source curve segments cross triangles; they remain unknown, no extra shared-skin proof fabricated. Selected ray proof is not a proof of an entire footprint.',
   'Native memory cause not isolated; public resource/point counters are reported without a leak/cache verdict.'],
  'noPendingUnityOrGPURequests':True,'forbidden115Executed':False,'noCUAResetKillDriverSecurityPush':True}
 (H/'STATUS26.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'actualFrames':sum(v['frames']for v in runs),'lastVerifiedNativeEqual':runs[-1]['nativeEqual'],'namedOwnedResourcesAfter':0,
  'idlePointAllocatedDifferenceMiB':(after['allocated']-before['allocated'])/1048576,'librarySaved':len(lib['directCreateResults'])}))
if __name__=='__main__':main()
