"""Check static plan arithmetic/closure, never create or execute the host."""
import json
from direct_support24 import H

def main():
    route=json.loads((H/'HOST_ROUTE24.json').read_text())
    plan=json.loads((H/'NEXT_GPU_PREFIX24.json').read_text())
    rows={row['kernel']:row for row in route['matrix']}
    assert not route['currentCandidateHostExists'] and not plan['executableNow']
    assert plan['inputContract']['completePairStates']==2**11
    assert plan['inputContract']['enumerationGroups']*64==2**11
    for stage in plan['stages']:
        row=rows[stage['kernel']]
        assert not row['sourceLocalArrays']
        assert sum(v.startswith('RWStructuredBuffer') for v in row['resources'].values())==stage['activeUAVs']
        mem=stage['memory'];total=sum(v for k,v in mem.items()if k not in ['sumOwnedBufferBytes','groupsharedBytesPerGroup'])
        assert total==mem['sumOwnedBufferBytes'],(stage['number'],total)
        assert stage['sourcePrivateArraysInClosure']==0
    assert [stage['kernel']for stage in plan['stages']]==['BuildSubsets113','Enumerate113','Reduce113','Write113']
    assert 96*(9+8*24*24)==443232
    assert 32*48==1536 and 4*144*16==9216
    assert route['changedKernelClosures']==['BuildSubsets113','Enumerate113','Reduce113']
    assert not route['productCSharpScan']['forbiddenReferences']
    assert not route['serializedAssetScan']['dangerous115References']
    cache=json.loads((H/'CACHE_PREFIX24.json').read_text())
    for name in rows:
        if name not in [s['kernel']for s in plan['stages']]:continue
        matches=[r for r in cache['rows']if r['kernelCandidatesByResourceSignature']==[name]]
        assert matches and all(r['privateArrayDeclarations']==0 for r in matches)
    result={'GPUOrUnityOrCompilerInvocations':0,'hostExecuted':False,'checksPassed':True,
            'requiredPreparationsRemain':['Thin4-kernel source does not exist','One-dispatch host does not exist','Candidate compilation/reflection unperformed','Fresh Editor read-only preflight unperformed'],
            'prefixBufferByteMax':max(s['memory']['sumOwnedBufferBytes']for s in plan['stages']),
            'notDeviceSafetyCertification':True}
    (H/'HOST_PLAN_CHECK24.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
