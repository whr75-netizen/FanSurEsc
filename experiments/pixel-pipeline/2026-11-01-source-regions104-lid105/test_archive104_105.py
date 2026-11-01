"""Portable saved-data checks; no Unity, network, extraction, cleanup or writes."""
from pathlib import Path
import hashlib,json,io,sys,struct,zipfile
import numpy as np
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'closed-support105'))
from analyse_capture68 import plane
from selection102 import cell

class MemoryPath:
    def __init__(self,name,data):self.name=name;self.data=data
    def open(self,mode):assert mode=='rb';return io.BytesIO(self.data)
    def __str__(self):return self.name

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def raw_buffer(b):
    n,stride=struct.unpack_from('<ii',b);assert stride==16 and len(b)==8+16*n
    return np.frombuffer(b,offset=8,dtype='<f4').reshape(n,4)

def main():
    manifest=load(H/'ARTIFACTS104_105.json')
    for f in manifest['files']:assert hashlib.sha256((H/f['path']).read_bytes()).hexdigest()==f['SHA256'],f['path']
    raw=zipfile.ZipFile(H/'RAW105.zip');names=raw.namelist();packets=sorted(n[:-len('/RAW_MANIFEST.json')]for n in names if n.endswith('/RAW_MANIFEST.json'))
    ids=set();planes=0;refs=0;mismatches=[];direct={}
    for prefix in packets:
        content=raw.read(prefix+'/RAW_MANIFEST.json');m=json.loads(content);ids.add(m['sourceId'])
        assert raw.read(prefix+'/RAW_COMPLETE76.marker').decode()==hashlib.sha256(content).hexdigest()
        assert m['packetComplete']and m['frameUnchangedDuringReadback']
        for path in names:
            if path.startswith(prefix+'/')and path.endswith('.plane'):
                meta,a=plane(MemoryPath(path,raw.read(path)));assert meta['sourceId']==m['sourceId']and meta['frameIndex']==m['frameIndex'];assert np.isfinite(a).all();planes+=1
        w,h=m['forward102']['canonicalSize'];layers=raw_buffer(raw.read(prefix+'/canonical-layers.f32')).reshape(4,5,h,w,4)
        visibility=raw_buffer(raw.read(prefix+'/canonical-visibility.f32')).reshape(4,h,w,4)
        decision=raw_buffer(raw.read(prefix+'/canonical-decision.f32')).reshape(h//4,w//4,4)
        for y in range(h//4):
            for x in range(w//4):
                r=cell(layers,visibility,x,y)['winner'];expected=-1 if r<0 else[1,4,6,0][r]
                if expected!=round(float(decision[y,x,0])):mismatches.append([prefix,x,y])
                refs+=1
        if prefix.startswith('direct/'):direct[m['sourceId']]=(m,layers,visibility)
    candidate=load(H/'closed-support105/direct/CURVE_CANDIDATE105.json');proofs=0
    for frame in candidate['frames']:
        if frame['evaluatedClose']!=100:assert frame['changedEyeCells']==0;continue
        m,layers,visibility=direct[frame['sourceId']]
        for eye in frame['sourceProof']:
            assert not eye['missing']and not eye['colourTies']and eye['components4']==[eye['curveCells']]
            for p in eye['proof']:
                x,y=p['nativeSubsampleXY'];v=visibility[3,y,x]
                assert v[0]>0 and v[0]==v[1]
                assert np.array_equal(np.array(p['linearRGB'],np.float32),layers[3,0,y,x,:3])
                assert round(float(layers[3,1,y,x,2]))==eye['eye'];proofs+=1
    assert len(packets)==6 and len(ids)==6 and planes==120 and refs==864 and not mismatches and proofs==14
    for row in load(H/'source-regions104/REVIEW104.json'):
        assert all(not c['disconnectedRegionIds']for c in row['connectivity'].values())
    print(json.dumps({'artifactsSHA256':len(manifest['files']),'actualSourcePackets':len(packets),'distinctSourceIds':len(ids),
        'planes':planes,'CPUReferenceCells':refs,'CPUGPUMismatches':len(mismatches),'closedSourceColourProofs':proofs,
        'productDefault':77,'newGPUcandidateTested':False,'fullFaceRegionResolverComplete':False}))
if __name__=='__main__':main()
