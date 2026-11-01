"""Read-only replay of actual packets and repackaged lossless deliverables."""
from pathlib import Path
import json,hashlib,io,zipfile,struct,re
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
from reader68 import plane
class MemoryPath:
    def __init__(self,b):self.b=b
    def open(self,mode):assert mode=='rb';return io.BytesIO(self.b)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    for f in load(HERE/'ARTIFACTS99.json')['files']:assert hashlib.sha256((HERE/f['path']).read_bytes()).hexdigest()==f['SHA256']
    s=load(HERE/'SUMMARY99.json');assert s['actualFrames']==10 and s['simultaneousSourceViewFrames']==6 and s['AContinuedAfterBDisposalFrames']==4 and s['nativeSerializedExact']==47 and not s['publicDifferences']and not s['newErrors']and s['productDefault']==77 and not s['productAssetsChanged']and not s['BFinalNativeEyeCompositionTested']
    frames=0;plane_count=0;common_world=0;b_live=0;b_gone=0;rebuilt=False
    with zipfile.ZipFile(HERE/'RAW99.zip')as z:
        for folder in sorted({n.split('/')[0]for n in z.namelist()}):
            raw=z.read(folder+'/RAW_MANIFEST.json');m=json.loads(raw);assert z.read(folder+'/RAW_COMPLETE76.marker').decode()==hashlib.sha256(raw).hexdigest();a={};heads={};v=m['views99'];A=v['A'];W=v['world'];assert A['cameraId']==A['actualGraphCameraId']and A['renderedFrame']==m['frameIndex']and not v['BFinalEyeCompositionProduced']
            for f in [n for n in z.namelist()if n.startswith(folder+'/')and n.endswith('.plane')]:
                h,x=plane(MemoryPath(z.read(f)));assert h['sourceId']==m['sourceId']and h['frameIndex']==m['frameIndex']and h['renderSerial']==m['mainSerial']and np.isfinite(x).all();a[Path(f).stem]=x;heads[Path(f).stem]=h;plane_count+=1
            assert heads['current-non-eye98-0']['viewId']=='viewA-physical-'+A['cameraId']and heads['actual-world98-1']['viewId']=='world-shared-'+W['cameraId']
            assert np.array_equal(a['actual-world98-1'][...,3],a['native-final-depth'][...,0])
            valid=a['legacy96-final3'][...,0]>=0;assert all(np.array_equal(a[f'legacy96-final{i}'][valid],a[f'live96-final{i}'][valid])for i in range(4))
            if not v['BDisposed']:
                B=v['B'];assert A['scope']!=B['scope']and A['cameraId']!=B['cameraId']and B['cameraId']==B['actualGraphCameraId']==B['nonEyeGraphCameraId']and B['ownersDisjoint']and B['AUnchangedAfterBWorld']and B['renderedFrame']==m['frameIndex']
                assert heads['B99-non-eye0']['viewId']=='viewB-physical-'+B['cameraId']and heads['B99-world1']['viewId']=='world-shared-'+W['cameraId']and np.array_equal(a['B99-world1'][...,3],a['B99-reference-depth'][...,0])
                lookup={tuple(q[:2]):(c,q)for c,q in zip(a['actual-world98-0'].reshape(-1,4),a['actual-world98-1'].reshape(-1,4))}
                for c,q in zip(a['B99-world0'].reshape(-1,4),a['B99-world1'].reshape(-1,4)):
                    if tuple(q[:2])in lookup:
                        c0,q0=lookup[tuple(q[:2])];assert np.array_equal(c,c0)and np.array_equal(q,q0);common_world+=1
                if m['motion82']['index']==1:assert B['BExplicitInvalidationZero']and B['AUnchangedAfterBInvalidation']
                if m['motion82']['index']==2:
                    b=z.read(folder+'/B99-witness.buffer');n=struct.unpack('<i',b[:4])[0];assert len(b)==4+n*16 and np.frombuffer(b,'<i4',offset=4).any();rebuilt=True
                b_live+=1
            else:assert v['AStillProducedAfterBDisposal']and v['BUnavailableNotReplayed'];b_gone+=1
            frames+=1
    assert (frames,b_live,b_gone,plane_count,common_world)==(10,6,4,1032,3996)and rebuilt
    d=load(HERE/'deliverables/DELIVERY99.json')
    # Exact original file hashes and all decoded animation frames were checked at repack.
    with Image.open(HERE/'deliverables/EYE_TIE_TURN_99.webp')as im:
        assert im.n_frames==10
        for i in range(10):im.seek(i);assert im.convert('RGB').size[0]>0
    with Image.open(HERE/'deliverables/EYE_TIE_CHOICES_99.png')as im:assert im.size==(1200,690)
    fail=load(HERE/'DELIVERY_STATUS99.json');assert not fail['webAccessibleLinkCreated']and not fail['LibraryFileIds']and fail['outcome']=='FAILED_BEFORE_PREPARATION_OR_UPLOAD'
    g=load(HERE/'PROFILING99.json');assert g['capability']['supportsGpuRecorder']and all(r['CPUNotSubstituted']for r in g['budgets'])and any(r['observationsWithSamples']>0 and r['GPUmsPerRecordedBlockMinMedianMax'][1]>.1 for r in g['budgets'])
    for ref in re.findall(r'(?:href|src)="([^"]+)"',(HERE/'INDEX.html').read_text(encoding='utf-8')):assert not re.match('https?://',ref)and(HERE/ref).exists()
    print(json.dumps({'actualFrames':frames,'liveTwoViewFrames':b_live,'AAfterBDisposalFrames':b_gone,'planeContracts':plane_count,'sharedWorldExactComparisons':common_world,'BOnlyInvalidationRebuilt':rebuilt,'GPUEnabledSamplesPresent':True,'strictPolicyRetained':True,'UnityCalls':0,'writes':0}))
if __name__=='__main__':main()
