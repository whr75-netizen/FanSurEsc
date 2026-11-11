"""Summarize only completed27 evidence; no Unity/GPU/cleanup calls."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;G=H/'surface27';REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def public(p):return json.loads(read(p)['result']['structuredContent']['data']['executionLogs'].split('[Log] ',1)[1])
def main():
 runs=[]
 for name in ['pigment-run','pigment-motion']:
  s=read(next((G/name).glob('STATE113-*-finished.json')));assert s['PlayExited']and not s.get('error')and not s.get('restorationError')and not s['globalRestoreErrors']
  unavailable=[v for v in s['nativeComparisons72']if v['equal']is not True]
  assert not unavailable or unavailable==[{'equal':None,'path':'ProjectSettings/ProjectSettings.asset','status':'Unavailable','type':'UnityEditor.AssetImporter'}],unavailable
  assert s['editInputRestoration82']['sameAliveReference']and s['editInputRestoration82']['exactJSON']and s['motionRestoration82']['allRestored']
  assert all(s[k]for k in ['observerRemoved','optionsRestored','timeRestored','pipelineRestored','backgroundRestored'])
  runs.append({'run':name,'frames':len(s['sequencePackets']),'nativeEqual':sum(v['equal']is True for v in s['nativeComparisons72']),'nativeUnavailable':unavailable,'before':s['beforeMemory'],'after':s['afterMemory'],'delta':{k:s['afterMemory'][k]-s['beforeMemory'][k]for k in ['allocated','reserved','mono','renderTextureCount']},'sceneBefore':s['beforeScenes'],'sceneAfter':s['afterScenes'],'sourceIds':[v['sourceId']for v in s['sequencePackets']]})
 before=public(G/'postflight/READ_REPLY.json');after=public(G/'pigment-postflight/READ_REPLY.json');assert not after['playing']and not after['transitioning']and not after['compiling']and after['ownedHairMaterials25']==after['createdHairTextures25']==0
 baseline=read(H.parents[1]/'RESUME_STATUS.json')['userTrackedFiles'];assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==sha for p,sha in baseline.items())
 memory={'counterAPIs':{'allocated':'Profiler.GetTotalAllocatedMemoryLong','reserved':'Profiler.GetTotalReservedMemoryLong','mono':'Profiler.GetMonoUsedSizeLong','renderTextureCount':'Resources.FindObjectsOfTypeAll<RenderTexture>().Length'},'runs':runs,'separatePublicBefore':before,'separatePublicAfter':after,'separatePointDeltaBytes':{k:after[k]-before[k]for k in ['allocated','reserved','mono','renderTextureCount']},'osSinglePoint':read(G/'OS_POST27.json'),
  'ownership':'Added13,536B GPU bend buffer and846-element CPU array owned by SourcePigment. Constructor failure/Dispose release it; Dispose nulls bend/binding arrays. Existing per-model/view/topology checks plus original/bend UV checks reject stale mappings. No static per-frame cache or new GPU feedback.',
  'sourceAudit':'NativeSnapshot73 stores44 metadata/hash/path rows, not mesh JSON strings. Forward/Layer/Motion are disposed and nulled. Assistant AssemblyUtils uses CurrentAssemblies.LoadFromBytes on Unity6000.5; fallback Assembly.Load does not establish actual lifetime. Loaded-assembly/native-root profiling was not performed.',
  'limit':'Allocation deltas are neither physical private working set nor a proven leak. Separate point change is not sum of spikes. No forced GC/Unload/private reflection/cleanup.'}
 (G/'MEMORY27.json').write_text(json.dumps(memory,indent=2)+'\n',encoding='utf-8')
 status={'baselineCommit':'808fa542ce6cf90a915dea3fd0b27277768a02b7','runtimeCandidate':'Assets/EUnityValidation01/SurfaceCarrier27/SurfaceCarrier27.compute','product77DefaultChanged':False,'userTracked30HashesEqual':True,
  'implemented':'Split existing109 native UV paths at source triangle edges.42 formerly unsupported segments each have2 exact pieces,888pieces total. Only original-query geometry changes; display shape/allocation/palette and destination occlusion policy unchanged.',
  'materialProofFix':'Historical24 curve proof mistakenly addressed face material(part0/submesh3). Final SourcePigment maps it explicitly to original native pigment(part3/submesh6); current triangle map supplies the material. Actual GPU proof tag and native alpha bounds are verified separately from face occlusion. No shader/new buffer needed for this fix.',
  'provisional27':'phase-run/motion-run and PRE_ALPHA reports are before source material correction; they are retained as provisional, not final adopted proof.',
  'CPU':'378 symmetry/order/reversal tests;1344 actual deformed shared-edge joins across32 prior frames; no unresolved UV gap/overlap; C#/four HLSL entries compiled without GPU device.',
  'actualGPU':'Four evaluated blink/reopen plus28 measured phase/walk/turn frames, normally exited/restored. Original curve rays474 match CPU. Source crop/LUT outside/phase-label changes0; Close100 iris/white0; reopen equal.',
  'rotationRemaining':'Two owner2 white selections at canonical(4,5), turn frames129/133 are definite destination face rejection(-117).32 GPU rays match same-frame CPU. Their original source witnesses are valid, but other-eye-majority/non-dominant shared skin is not eligible for exemption under the active rule. No forced clearing or claim of artistic correctness.',
  'faceBlocker':'Original colour/UV exist. baseColor and shadeMultiply use the same image; no accepted scalp/cheek/gradient/AA region hierarchy or per-stage confirmed binding exists. Three weak-cheek colour probes have identical normal pixels. Eye202 FaceSkin/LidSkinCarrier both select role3. Prior103/104 are unadopted segmentation evidence. No guessed face regions applied.',
  'outlineKnownInput':'Original material3 finite outline linear RGB[.0612460561,.008568122,.014443838], lightingMix0, world width.00075 exist. Pixel classification/priority for silhouette/interior-region/partial-alpha still missing; source colour existence is separate from actual outline integration.',
  'notClaimed':['full face finite palette/outline','whole pipeline/art completion','new hair ON/OFF or multiview/model replacement tests','proof of all-point source-footprint visibility','general GPU reset cause or universal safety','memory leak resolution'],
  'EditorAfter':after,'noPendingRequests':True,'forbidden115OrCUAKillResetDriverSettingsPush':False,'limits':'Existing operational UV alpha-centre reference, not artist intent reconstruction; external runner absolute paths remain.'}
 (G/'STATUS27.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
 old=read(H/'STATUS26.json');old['latestStatus']='surface27/STATUS27.json';old['historicalRemaining42']='Resolved by explicit native UV shared-edge mapping in27; other26 records remain historical evidence.';(H/'STATUS26.json').write_text(json.dumps(old,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'actualFrames':32,'sourceCrossTriangleUnknown':0,'nativeEqual':44,'separatePointAllocatedDeltaMiB':memory['separatePointDeltaBytes']['allocated']/1048576,'GPUExtraBufferBytes':13536,'userTracked30Preserved':True,'faceBindingsAdded':0}))
if __name__=='__main__':main()
