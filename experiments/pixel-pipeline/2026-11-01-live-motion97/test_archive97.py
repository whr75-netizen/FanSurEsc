"""Read-only, bounded replay of saved assertions; never launches Unity."""
from pathlib import Path
import hashlib,json,sys,zipfile,io,struct
import numpy as np
HERE=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding='utf-8'))
class MemoryPath:
    def __init__(self,data):self.data=data
    def open(self,mode):assert mode=='rb';return io.BytesIO(self.data)
def main():
    from reader68 import plane
    manifest=load(HERE/'ARTIFACTS97.json')['files'];checks=0
    for f in manifest:assert hashlib.sha256((HERE/f['path']).read_bytes()).hexdigest()==f['SHA256'];checks+=1
    s=load(HERE/'SUMMARY97.json');assert s['runtimeSelectionNotOfflineReplay']and not s['productIntegrated']and s['productDefault']==77 and not s['GPUTimeMeasured'];checks+=1
    assert s['phase']['phaseRoleOwnerSignatures']==s['phase']['phaseColourSignatures']==1 and .999<s['phase']['phaseXRange'][1]<1.001;checks+=1
    with zipfile.ZipFile(HERE/'RAW97.zip')as raw,zipfile.ZipFile(HERE/'OFFLINE_ORACLE97.zip')as oracle:
        for row in s['rows']:
            root=f'frame-{row["frame"]}/';m=raw.read(root+'RAW_MANIFEST.json');meta=json.loads(m);assert raw.read(root+'RAW_COMPLETE76.marker').decode()==hashlib.sha256(m).hexdigest();assert meta['sourceId']==row['sourceId'];checks+=1
            for name in [x for x in raw.namelist()if x.startswith(root)and x.endswith('.plane')]:
                # Each plane embeds the same frame/source/serial and complete raw
                # marker; no absolute original path is needed to replay it.
                header,values=plane(MemoryPath(raw.read(name)));assert header['sourceId']==meta['sourceId']and header['frameIndex']==meta['frameIndex']and header['renderSerial']==meta['mainSerial']and np.isfinite(values).all();checks+=1
            if row['frame']in [127,128,134,136]:
                z=np.load(io.BytesIO(oracle.read(f'candidate-source-cache-turn97v2/frame{row["frame"]}.npz')))
                # Raw header details are already validated above; use shared reader
                # shipped with the archive to decode exact final field values.
                for n,key in enumerate(['colour','owner','depth']):
                    header,actual=plane(MemoryPath(raw.read(root+f'live96-final{n}.plane')))
                    assert np.array_equal(actual,z[key]);checks+=1
    failures=load(HERE/'ROTATION_FAILURES97.json');assert len(failures['canonicalUnknownCells'])==6 and len(failures['nativeBackingFailures'])==3;checks+=1
    assert s['rotationUnresolvedNativeByFrame']=={'127':3,'128':6,'134':1,'136':2}and s['nativeContentsDirectExact']==47;checks+=1
    assert s['latestPublicStateStillRestored']and s['dirtyBefore']==s['dirtyAfter']==31 and not s['globalRestoreErrors'];checks+=1
    life=load(HERE/'lifetime/REPORT96.json');assert life['remainingOwnedBytes']==life['cancelBeforeFirstFrameOwnBytes']==0 and life['AStillWorksAfterBDisposal']and life['simultaneousOwnersIsolated'];checks+=1
    print(json.dumps({'checks':checks,'actualSavedFrames':len(s['rows']),'rotationStillNotPassed':True,'UnityCalls':0,'writes':0}))
if __name__=='__main__':main()
