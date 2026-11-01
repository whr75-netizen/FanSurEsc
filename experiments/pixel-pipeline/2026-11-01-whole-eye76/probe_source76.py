"""Exact instrumentation variant: log actual Evaluate input before mutation."""
from pathlib import Path
import hashlib,json,difflib
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
SOURCE=REPO/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeFeature348.compute'
TARGET=SOURCE.with_name('BaselineProbe76.compute')
HEADER='''// Diagnostic76: owned per-instance buffer, no global binding or output behaviour change.
struct Baseline76 {float4 colour,owner,meta,uv,domain,stamp;};
RWStructuredBuffer<Baseline76> _Baseline76;
RWStructuredBuffer<uint> _ProbeVisits76;
int4 _ProbeROI76;int _ProbeFrame76,_ProbeSerialBefore76;
'''
ANCHOR='bool oldDomain=_BaselineDomain348.Load(int3(p,0)).x>.5;'
HOOK='''int2 probeLocal76=p-_ProbeROI76.xy;if(all(probeLocal76>=0)&&all(probeLocal76<_ProbeROI76.zw)){
 Baseline76 b76;b76.colour=old;b76.owner=oldOwner;b76.meta=oldMeta;b76.uv=oldUV;b76.domain=_BaselineDomain348.Load(int3(p,0));b76.stamp=float4(p,_ProbeFrame76,_ProbeSerialBefore76);
 _Baseline76[probeLocal76.y*_ProbeROI76.z+probeLocal76.x]=b76;if(all(probeLocal76==0)){uint prior76;InterlockedAdd(_ProbeVisits76[0],1,prior76);}}
'''
def prepare():
    s=SOURCE.read_text(encoding='utf-8');assert s.count(ANCHOR)==1
    out=HEADER+s.replace(ANCHOR,ANCHOR+HOOK)
    assert out.replace(HEADER,'',1).replace(HOOK,'',1)==s
    (HERE/'BaselineProbe76.compute').write_text(out,encoding='utf-8')
    (HERE/'PROBE_DIFF76.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),out.splitlines(True),fromfile=SOURCE.name,tofile=TARGET.name)),encoding='utf-8')
    (HERE/'PROBE_CONTRACT76.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'variantSHA256':hashlib.sha256(out.encode()).hexdigest(),'recordStride':96,'originalAlgorithmBytesPreserved':True,'changes':['Evaluate pre-mutation owned ROI buffer write','owned dispatch visit counter'],'productDefaultChanged':False},indent=2)+'\n')
    print('Variant prepared outside Assets; original Evaluate bytes preserved')
if __name__=='__main__':prepare()
