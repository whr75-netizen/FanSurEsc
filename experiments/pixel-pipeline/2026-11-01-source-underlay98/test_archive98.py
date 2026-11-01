"""Bounded read-only replay of actual source/colour/owner/depth contracts."""
from pathlib import Path
import hashlib,json,io,struct,zipfile,re
import numpy as np
HERE=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding='utf-8'))
class MemoryPath:
    def __init__(self,data):self.data=data
    def open(self,mode):assert mode=='rb';return io.BytesIO(self.data)
def main():
    from reader68 import plane
    checks=0
    for f in load(HERE/'ARTIFACTS98.json')['files']:assert hashlib.sha256((HERE/f['path']).read_bytes()).hexdigest()==f['SHA256'];checks+=1
    s=load(HERE/'SUMMARY98.json');assert s['fixedThree']==3 and s['newInvalidRegression']==0 and s['sameFrameAfterInvalid']==9 and not s['lastEditorPlaying']and s['owned98NativeMaterialsRTComputeClonesRemaining']==0 and s['runtimeSelectionNotOfflineReplay']and s['productDefault']==77;checks+=1
    assert all(x['dirtyBefore']==x['dirtyAfter']==31 and x['native47DirectExact']and not x['publicDifferences']and not x['newConsoleErrors']for x in s['rounds']);checks+=1
    p=load(HERE/'POLICIES98C.json');assert p['baselineCPUAll35GPUFieldsExact']and len(p['baseline'])==35 and all(all(r['fieldsExact'])for r in p['baseline']);checks+=1
    for row in p['rows']:
        for policy in row['policies']:
            assert not policy['adopted']and not policy['GPUValidated']
            for e in policy['events']:assert all(e['massBounds'][str(k)][0]==e['massBounds'][str(k)][1]for k in e['possible'])
            checks+=1
    fixed=load(HERE/'FIXED_THREE98.json');assert len(fixed)==3
    with zipfile.ZipFile(HERE/'RAW98C.zip')as raw:
        for folder in sorted({n.split('/')[0]for n in raw.namelist()}):
            prefix=folder+'/';manifest=raw.read(prefix+'RAW_MANIFEST.json');m=json.loads(manifest);assert raw.read(prefix+'RAW_COMPLETE76.marker').decode()==hashlib.sha256(manifest).hexdigest();a={}
            for name in [n for n in raw.namelist()if n.startswith(prefix)and n.endswith('.plane')]:
                h,v=plane(MemoryPath(raw.read(name)));assert h['sourceId']==m['sourceId']and h['frameIndex']==m['frameIndex']and h['renderSerial']==m['mainSerial']and np.isfinite(v).all();a[name[len(prefix):-6]]=v;checks+=1
            old=a['legacy96-final3'];new=a['live96-final3'];valid=old[...,0]>=0;assert all(np.array_equal(a[f'legacy96-final{i}'][valid],a[f'live96-final{i}'][valid])for i in range(4));checks+=1
            world=new[...,0]==5;assert np.array_equal(a['live96-final0'][world],a['actual-world98-0'][world])and not a['live96-final1'][world].any()and np.array_equal(a['live96-final2'][world,0],a['actual-world98-1'][world,3]);assert np.array_equal(a['native-final-depth'][...,0],a['actual-world98-1'][...,3]);checks+=1
            for f in fixed:
                if f['frame']!=m['frameIndex']:continue
                x,y=f['nativeROIxy'];assert a['live96-final0'][y,x].tolist()==f['literalLinearRGBA']and a['live96-final1'][y,x].tolist()==f['owner']and a['live96-final2'][y,x].tolist()==f['depth'];checks+=1
            # Independently reconstruct the native world sampler's integer texels.
            ref=m['nativeFinalReference89'];h,w=new.shape[:2];yy,xx=np.mgrid[:h,:w];absolute=np.stack([xx+ref['nativeROI'][0],yy+ref['nativeROI'][1]],-1).astype('f4');origin=np.asarray(ref['origin'],'f4');scale=np.float32(ref['scale']);delta=np.asarray(m['camera86']['deliveredDelta'][:2],'f4');q=np.floor((absolute+np.float32(.5)-origin)/scale-delta);xy=np.floor(origin+(q+np.float32(.5)+delta)*scale);xy[...,0]=np.clip(xy[...,0],0,959);xy[...,1]=np.clip(xy[...,1],0,543);assert np.array_equal(xy,a['actual-world98-1'][...,:2]);checks+=1
    for ref in re.findall(r'(?:src|href)="([^"]+)"',(HERE/'INDEX.html').read_text(encoding='utf-8')):
        assert not re.match(r'https?://',ref)and(HERE/ref.split('#')[0]).exists(),ref;checks+=1
    print(json.dumps({'checks':checks,'actualStates':35,'fixed3':True,'existingValidOutputsExact':True,'remainingNativeTiePixels':9,'policyAlternativesAdopted':False,'UnityCalls':0,'writes':0}))
if __name__=='__main__':main()
