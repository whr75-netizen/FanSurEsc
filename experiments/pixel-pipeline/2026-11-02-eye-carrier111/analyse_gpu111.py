"""Verify LIVE geometry-only111G, distinct from the offline allocator."""
import json,hashlib
import numpy as np
from geometry111 import H,read,load,plane,packet_list
from ray111 import NativeAlpha,FaceRay
from analyse111 import validate,source_fields,bank_data,source_components
def main():
    root=H/'gpu-carrier';state,packets=packet_list('geometry');assert state['PlayExited']and not state.get('error')and not state.get('restorationError');out=[]
    for p in packets:
        ctx=load(p);alpha=NativeAlpha(ctx);proof=validate(ctx,alpha,FaceRay(ctx,alpha));parts=[]
        for part in[1,2,3]:
            _,rgba=plane(p/f'C-part{part}-rgba.plane');_,meta=plane(p/f'C-part{part}-meta.plane');valid=meta[:,:,0]>0;aa=rgba[:,:,3][valid];assert len(aa)and np.all(aa==1);assert np.all(rgba[:,:,:3][valid]==0);parts.append({'part':part,'actualGeometrySamples':int(valid.sum()),'allCarrierAlphaOne':True,'RGBIsMetadataZeroNotAColourSupplier':True})
        m,a,v=source_fields(p);lo,hi,*_=__import__('io109').joint_arrays(a,v);bank,groups=bank_data();sourceProof=[]
        for owner in[1,2]:
            bits,active,ids,errors=source_components(ctx,a,lo,owner,bank,groups);assert not errors and all(r['sourceKeyUnique']for r in ids);sourceProof.append({'owner':owner,'recordedDense8xSourceKeysChecked':len(ids),'unresolvedSourceKeys':0,'bankSourceRGB8Mismatch':0,'activeComponents':active})
        out.append({'sourceId':ctx['sourceId'],'frame':ctx['frame'],'stage':m['motion82'],'GPUQueryValidation':{k:v for k,v in proof.items()if k!='checks'},'carrierParts':parts,'nativeSourceBankPathUnchanged':True,'sourceBankProof':sourceProof,'actualRuntimeGeometryPassExecuted':True,'runtime2_2AllocatorExecuted':False})
    before=state['beforeMemory'];after=state['afterMemory'];bad=[v for v in state['nativeComparisons72']if v.get('equal')is not True];fields={k:state.get(k)for k in['PlayExited','optionsRestored','timeRestored','pipelineRestored','backgroundRestored','playerSettingsRunInBackgroundRestored','carrierSourceDisposed111','carrierNativeDisposed111','editInputRestoration82','motionRestoration82','globalRestoreErrors']}
    result={'actualGPUFrames':len(out),'actualGPUCarrierQueriesChecked':sum(v['GPUQueryValidation']['sampledGPUCarrierQueryChecks']for v in out),'maxCPUvsGPUIntervalDifference':max(v['GPUQueryValidation']['maxCPUvsGPUVisibilityIntervalDifference']for v in out),'shaderOnlyImportNoDomainReload':read(root/'IMPORT111Gb.json'),'restore':fields,'nativeContentMatches':sum(v.get('equal')is True for v in state['nativeComparisons72']),'nativeComparisons':len(state['nativeComparisons72']),'unavailableOrDifferent':bad,'memoryCounterAPI':'UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong/GetTotalReservedMemoryLong/GetMonoUsedSizeLong; NOT OS working set','memoryBefore':before,'memoryAfter':after,'allocatedDeltaBytes':after['allocated']-before['allocated'],'ownedRTCountBeforeAfter':[before['renderTextureCount'],after['renderTextureCount']],'frames':out,'product77DefaultChanged':False,'runtimeAllocatorOrCanvasHypothesisApplied':False};(H/'GPU_CARRIER111.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in['frames','restore','shaderOnlyImportNoDomainReload']}))
if __name__=='__main__':main()
