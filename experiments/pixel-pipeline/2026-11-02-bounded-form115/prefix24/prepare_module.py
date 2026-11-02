"""Extract original candidate113 function closure. Never imports/compiles it."""
from pathlib import Path
import hashlib, json, re, sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from host_audit24 import functions,closure

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    source=(ROOT/'ForwardEye113_Direct24.compute').read_text(encoding='utf-8')
    funcs=functions(source);kernels=['BuildSubsets113','Enumerate113','Reduce113','Write113']
    keep=set().union(*(set(closure(k,funcs))for k in kernels))
    preamble='''// Extracted Direct24 prefix only. No Unity execution or device clearance.
// The four entrypoint bodies and helper closure match the113 scalar candidate.
#pragma kernel BuildSubsets113
#pragma kernel Enumerate113
#pragma kernel Reduce113
#pragma kernel Write113
#define K113 65536.0
#define MAXP113 24
#define GROUPS113 32768u
struct Group113{float4 score;uint4 masks,tail;};
struct Subset113{uint4 a,b;};
RWStructuredBuffer<float4> _Cells113;
RWStructuredBuffer<uint4> _CellTags113,_Frame113,_Points113;
RWStructuredBuffer<Group113> _Groups113,_Best113;
RWStructuredBuffer<Subset113> _Subsets113;
RWStructuredBuffer<float4> _CurveColour106,_CurveIdentity106,_CurveDecision106,_CurveAudit106;
int2 _CurveEyeIds106,_CellsSize113;
groupshared Group113 Shared113[64];
'''
    pieces=[]
    for name,item in funcs.items():
        if name not in keep:continue
        if name in kernels:
            dims=re.search(r'\[numthreads\(([^)]+)\)\]\s*void\s+'+name+r'\b',source)[1]
            pieces.append('[numthreads('+dims+')]'+item['source'])
        else:pieces.append(item['source'])
    out=preamble+'\n'+'\n'.join(pieces)+'\n'
    actual=functions(out)
    assert set(actual)==keep and all(actual[n]['source']==funcs[n]['source']for n in keep)
    assert re.findall(r'#pragma kernel (\w+)',out)==kernels
    assert not re.search(r'\b(?:float\d?|uint\d?|int\d?|bool)\s+\w+\[\d+\]', '\n'.join(f['body']for f in actual.values()))
    for banned in ['115','Query','GatherEye','Select','Compose','Refit','Down115','Up115']:
        assert not re.search(r'\b'+banned+r'\w*\s*\(',out),banned
    (HERE/'Prefix24.compute').write_bytes(out.encode('utf-8'))
    manifest={'sourceSHA256':sha(out.encode()),'parentSourceSHA256':sha((ROOT/'ForwardEye113_Direct24.compute').read_bytes()),
              'entrypoints':kernels,'functions':{n:sha(actual[n]['source'].encode())for n in actual},'functionBodiesExactlyPreserved':True,
              'privateSourceArrays':0,'groupsharedBytes':64*48,'GPUOrUnityCalls':0}
    (HERE/'MODULE.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest))

if __name__=='__main__':main()
