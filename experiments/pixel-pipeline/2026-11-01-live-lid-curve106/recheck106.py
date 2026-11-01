"""Portable CPU/GPU fixture verification. Reads RAW106.zip; no Unity calls.
Run: python -B recheck106.py (requires numpy, no installation performed here).
This verifies the frozen actual GPU decisions, not a new runtime performance or
all-model/visibility guarantee. Source curves are the captured registered
geometric reference; no automatic artist approval is implied.
"""
from pathlib import Path
import json,struct,hashlib,zipfile
import numpy as np
from curve_reference106 import apply,tests
H=Path(__file__).resolve().parent

def buf(b,stride=16):
    n,s=struct.unpack_from('<ii',b);assert s==stride and len(b)==8+n*s
    return np.frombuffer(b,offset=8,dtype='<f4').reshape(n,s//4)

def main():
    index=json.loads((H/'RAW106_INDEX.json').read_text(encoding='utf-8'));frames={};hashes=0;cells=0;proofs=0
    with zipfile.ZipFile(H/'RAW106.zip')as z:
        assert set(z.namelist())=={r['file']for r in index}
        for row in index:
            b=z.read(row['file']);assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256'];hashes+=1
            folder,name=row['file'].split('/',1)
            if name=='RAW_MANIFEST.json':frames[folder]=json.loads(b)
        for folder,m in frames.items():
            assert z.read(folder+'/RAW_COMPLETE76.marker').decode()==hashlib.sha256(z.read(folder+'/RAW_MANIFEST.json')).hexdigest()
            def b(name):return buf(z.read(folder+'/'+name+'.f32'))
            w,h=m['forward102']['canonicalSize'];layers=b('canonical-layers').reshape(4,5,h,w,4);vis=b('canonical-visibility').reshape(4,h,w,4)
            source=buf(z.read(folder+'/curve-segments106.f32'),32).reshape(-1,2,4)
            old=b('canonical-colour');oi=b('canonical-identity');od=b('canonical-decision')
            c,i,d,a=apply(source,layers,vis,old,oi,od)
            actual=[b(k)for k in ['curve-colour','curve-identity','curve-decision','curve-audit']]
            assert np.array_equal(c,actual[0])and np.array_equal(i,actual[1])and np.array_equal(d,actual[2])and np.array_equal(a[:,0],actual[3][:,0])
            keep=np.isin(oi[:,0],[1,4]);assert np.array_equal(c[keep],old[keep])and np.array_equal(i[keep],oi[keep])
            for k in np.flatnonzero(actual[3][:,0]==3):
                at=round(float(actual[3][k,2]))-1;y,x=divmod(at,w)
                assert np.array_equal(c[k,:3],layers[3,0,y,x,:3])and vis[3,y,x,0]>0 and vis[3,y,x,0]==vis[3,y,x,1]
                assert i[k,1]==layers[3,1,y,x,2]and i[k,2]==layers[3,1,y,x,0]
                proofs+=1
            cells+=len(c)
    assert len(frames)==51 and cells==7500
    result={'actualFrozenGPUFrames':len(frames),'CPUReferenceCells':cells,'CPUGPUMismatches':0,'nativeSampleRGBDepthOwnerProofs':proofs,'rawFileHashes':hashes,'synthetic':tests(),'UnityExecutedByThisScript':False}
    print(json.dumps(result))
    return result
if __name__=='__main__':main()
