"""Read actual99 packets; no Unity calls or new rendering."""
from pathlib import Path
import hashlib,json,sys,struct
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'apply-capture66'))
from analyse_capture68 import plane

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def buffer(p,typ='<f4'):
    b=p.read_bytes();n=struct.unpack('<i',b[:4])[0];assert len(b)==4+n*16
    return np.frombuffer(b,typ,offset=4).reshape(n,4)
def main():
    cap=HERE/'capture';s=load(sorted(cap.glob('STATE99-*'))[-1]);before=load(cap/'CURRENT99.json');after=load(cap/'POST99.json');verify=load(cap/'VERIFY99.json')
    assert s['stage']=='finished'and s['PlayEntries']==1 and s['PlayExited']and not s.get('error')and not s.get('restorationError')
    assert all(s[k]for k in ['observerRemoved','backgroundRestored','optionsRestored','pipelineRestored','timeRestored'])and not s['globalRestoreErrors']and s['motionRestoration82']['allRestored']
    assert all(s[k]for k in ['joint96Disposed','current91Disposed','retargetDisposed89','ownedProbeReleased76','borrowedRestReferenceUntouched82'])and not s['borrowedRestDisposedByObserver82']
    public=[k for k in before if k not in ['utc','memory']and before[k]!=after[k]];assert not public
    assert len(before['dirty'])==len(after['dirty'])==31 and not after['playing']and not after['compiling']
    assert sum(r.get('equal')is True for r in verify['nativeComparisons'])==47 and not any(r.get('equal')is False for r in verify['nativeComparisons'])
    assert before['input']==after['input']and verify['settingsId']==before['input']['nativeId']and verify['settingsJSON']==before['input']['json']
    rows=[];perf=[];scopes=set();matrixdiff=[];totalplanes=0;unique_world=0
    for e in s['sequencePackets']:
        p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');assert (p/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()
        h={};a={}
        for f in p.glob('*.plane'):
            hh,v=plane(f);assert hh['sourceId']==m['sourceId']and hh['frameIndex']==e['frame']and hh['renderSerial']==e['serial']and np.isfinite(v).all();h[f.stem]=hh;a[f.stem]=v;totalplanes+=1
        v=m['views99'];A=v['A'];world=v['world'];assert A['cameraId']==A['actualGraphCameraId']and A['renderedFrame']==e['frame']
        assert not v['BFinalEyeCompositionProduced']and world['sharedReadOnlyOriginalNativeWorld']
        assert h['current-non-eye98-0']['viewId']=='viewA-physical-'+A['cameraId']
        assert h['actual-world98-1']['viewId']=='world-shared-'+world['cameraId']
        assert np.array_equal(a['actual-world98-1'][...,3],a['native-final-depth'][...,0])
        # Current literal source restoration and already-valid native samples.
        old=a['legacy96-final3'];new=a['live96-final3'];valid=old[...,0]>=0
        assert all(np.array_equal(a[f'legacy96-final{i}'][valid],a[f'live96-final{i}'][valid])for i in range(4))
        row={'frame':e['frame'],'serial':e['serial'],'stageIndex':e['stageIndex82'],'BDisposed':v['BDisposed'],'AQueries':m['live96']['queryCount'],'ATriangleTests':m['live96']['triangleTests'],'AOwnedBufferBytes':m['live96']['ownedBufferBytes'],'ACanonicalRGBA_SHA256':hashlib.sha256(buffer(p/'live96-colour.buffer').tobytes()).hexdigest(),'ACanonicalIdentity_SHA256':hashlib.sha256(buffer(p/'live96-identity.buffer').tobytes()).hexdigest(),'nativeROI':m['nativeFinalReference89']['nativeROI']}
        if not v['BDisposed']:
            B=v['B'];assert B['cameraId']==B['actualGraphCameraId']==B['nonEyeGraphCameraId']and B['renderedFrame']==e['frame']and A['cameraId']!=B['cameraId']and A['scope']!=B['scope']
            assert B['ownersDisjoint']and B['AUnchangedAfterBWorld']and B['queries']>0
            assert h['B99-non-eye0']['viewId']=='viewB-physical-'+B['cameraId']and h['B99-world1']['viewId']=='world-shared-'+world['cameraId']
            assert np.array_equal(a['B99-world1'][...,3],a['B99-reference-depth'][...,0])
            diff=float(np.max(abs(np.asarray(A['view'])-B['view'])));assert diff>0;matrixdiff.append(diff);scopes.update([A['scope'],B['scope']])
            # Shared world texels are intentionally equal, unlike per-view source grids.
            lookup={tuple(q[:2]):(c,q)for c,q in zip(a['actual-world98-0'].reshape(-1,4),a['actual-world98-1'].reshape(-1,4))}
            common=0
            for c,q in zip(a['B99-world0'].reshape(-1,4),a['B99-world1'].reshape(-1,4)):
                if tuple(q[:2])in lookup:
                    c0,q0=lookup[tuple(q[:2])];assert np.array_equal(c,c0)and np.array_equal(q,q0);common+=1
            assert common>0;unique_world+=common
            w=buffer(p/'B99-witness.buffer','<i4');row.update({'BQueries':B['queries'],'BTriangleTests':B['triangleTests'],'BOwnedBufferBytes':B['ownedBytes'],'viewMatrixMaxDifference':diff,'sourceGridSizes':[list(a['current-non-eye98-0'].shape[:2]),list(a['B99-non-eye0'].shape[:2])],'sharedWorldSampleComparisons':common,'BNonZeroWitnessBeforeOptionalInvalidation':int(np.any(w!=0,axis=1).sum())})
            if e['stageIndex82']==1:assert B['BExplicitInvalidationZero']and B['AUnchangedAfterBInvalidation'];row['BOnlyInvalidationPassed']=True
        else:assert v['AStillProducedAfterBDisposal']and v['BUnavailableNotReplayed']and e['stageIndex82']>=6
        for r in v['profiling']:perf.append(dict(r,readAtFrame=e['frame'],readAtSerial=e['serial']))
        rows.append(row)
    assert len(rows)==10 and sum(not r['BDisposed']for r in rows)==6 and sum(r['BDisposed']for r in rows)==4 and len(scopes)==2
    assert rows[2]['BNonZeroWitnessBeforeOptionalInvalidation']>0
    assert len({r['ACanonicalRGBA_SHA256']for r in rows})==len({r['ACanonicalIdentity_SHA256']for r in rows})==1
    budget=[]
    for name in sorted({r['name']for r in perf}):
        rr=[r for r in perf if r['name']==name and r['GPUcount']>0];each=[r['GPUms']/r['GPUcount']for r in rr]
        budget.append({'marker':name,'observationsWithSamples':len(rr),'GPUcountRange':[min((r['GPUcount']for r in rr),default=0),max((r['GPUcount']for r in rr),default=0)],'GPUmsPerRecordedBlockMinMedianMax':list(map(float,[min(each),np.median(each),max(each)]))if each else None,'CPUNotSubstituted':True,'nearZeroIsNotZeroCost':bool(each and max(each)<.001)})
    pre=load(cap/'Capture99_CONSOLE_BEFORE.json')['data']['logs'];post=load(cap/'Verify99_CONSOLE_AFTER.json')['data']['logs'];known={(r['timestamp'],r['type'],r['message'])for r in pre};errors=[r['message']for r in post if r['type']in ['Error','Exception','Assert']and(r['timestamp'],r['type'],r['message'])not in known];assert not errors
    save(HERE/'PROFILING99.json',{'capability':s['GPUCapability99'],'sampling':'GPU-enabled URP ProfilingSampler custom samplers; documented three-frame delayed aggregate, sourceFrameThreeEarlier is nominal lag association, not a hardware event fence','scope':'query=BVH refit/query/joint select; excludes canonical Pack and retarget draws; source=non-eye11draw only; world=PackWorld98 only; compose=finalcandidate only; oldcomparison/readbacks unbudgeted','limitations':'Editor, diagnostic readback and two-view extra work; not shipping frame time or FPS; near-zero compose sample does not establish zero cost; source/retarget/whole pipeline not fully profiled','budgets':budget,'raw':perf})
    save(HERE/'SUMMARY99.json',{'status':'ACTUAL_TWO_SOURCE_VIEWS_ISOLATED_GPU_SAMPLES_AVAILABLE_ART_CHOICE_PENDING','baseCommit':'cf8b14147e94ff87f2487efc523e62ea9456877f','productDefault':77,'productAssetsChanged':False,'PlayEntries':1,'actualFrames':10,'simultaneousSourceViewFrames':6,'AContinuedAfterBDisposalFrames':4,'cameraMatrixMaxDifferenceRange':[min(matrixdiff),max(matrixdiff)],'worldSharedReadOnlyExactSampleComparisons':unique_world,'sourceScopeCount':2,'allPlaneHeadersMatched':totalplanes,'BOnlyWitnessInvalidationAndRebuild':True,'BFinalNativeEyeCompositionTested':False,'BFinalNativeEyeCompositionReason':'normal head-enabled path does not produce original main-eye 348 records; these were not fabricated or read uninitialized','arbitraryRotatedViewsOrModelReplacementTested':False,'twoViewSourceAndCacheIsolationTested':True,'GPUSamplesAvailable':True,'GPUWholeFrameBudgetEstablished':False,'newErrors':errors,'lastEditUTC':after['utc'],'publicDifferences':public,'dirtyBeforeAfter':[len(before['dirty']),len(after['dirty'])],'nativeSerializedExact':47,'nativeUnavailable':[{'path':r['path'],'type':r['type']}for r in verify['nativeComparisons']if r.get('equal')is None],'InputSettingsAndDevicesExact':True,'RTCountBeforeAfter':[s['beforeMemory']['renderTextureCount'],s['afterMemory']['renderTextureCount']],'UnityAllocatedMemoryDeltaMiB':(s['afterMemory']['allocated']-s['beforeMemory']['allocated'])/1048576,'memoryCounterIsNotPhysicalRAMOrLeakProof':True,'globalRestoreErrors':s['globalRestoreErrors'],'rows':rows})
    print(json.dumps({'frames':len(rows),'twoViewFrames':6,'continuedA':4,'GPU':True,'dirty':31,'nativeExact':47,'worldExactComparisons':unique_world,'newErrors':len(errors)},ensure_ascii=False))
if __name__=='__main__':main()
