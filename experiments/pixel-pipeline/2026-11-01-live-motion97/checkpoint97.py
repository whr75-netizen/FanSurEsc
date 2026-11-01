"""Read saved actual GPU inputs; no Unity calls and no output adoption."""
from pathlib import Path
import json,sys,hashlib,html
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'))
from analyse89 import packet,rgb8
from validate96 import read

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    state=load(sorted((HERE/'motion').glob('STATE97*'))[-1]);pre=load(HERE/'motion/CURRENT97.json');post=load(HERE/'motion/POST97.json');verify=load(HERE/'motion/VERIFY97.json');review=load(HERE/'MOTION_REVIEW97.json');rows=[];cost=[];palettes=[]
    current=load(HERE/'status97/CURRENT97.json');assert not current['playing'] and not current['compiling'] and not current['transitioning']
    assert not[k for k in post if k not in ['utc','memory']and post[k]!=current[k]]
    assert state['PlayEntries']==1 and state['PlayExited'] and not state.get('error') and not state.get('restorationError') and not state['globalRestoreErrors'] and state['motionRestoration82']['allRestored']
    differences=[k for k in pre if k not in ['utc','memory']and pre[k]!=post[k]];assert not differences
    assert sum(x.get('equal')is True for x in verify['nativeComparisons'])==47
    for e in state['sequencePackets']:
        d=packet(Path(e['output']));a=d['a'];m=d['m'];audit=a['live96-final3'];cw,ch=np.asarray(m['retarget89']['size'])//4;canonical=read(d['path']/'live96-colour.buffer').reshape(ch,cw,4);identity=read(d['path']/'live96-identity.buffer').reshape(ch,cw,4)
        protected=audit[...,2]>0;outside=(audit[...,0]==0)|(audit[...,0]<0)
        protectedExact=all(np.array_equal(a[f'live96-final{i}'][protected],a[key][protected])for i,key in enumerate(['native-final-rgba','native-final-owner','native-final-depth']))
        passExact=all(np.array_equal(a[f'live96-final{i}'][outside],a[key][outside])for i,key in enumerate(['native-final-rgba','native-final-owner','native-final-depth']))
        # Each selected final RGB must still be a literal observed source RGB.
        sourceAtoms=set()
        for p in range(1,4):
            rgba=a[f'retarget-part{p}-0'];meta=a[f'retarget-part{p}-1'];sourceAtoms.update(tuple(v)for v in rgba[meta[...,0]>0,:3])
        sourceColours=canonical[identity[...,0]>0,:3];foreignColours=[v.tolist()for v in sourceColours if tuple(v)not in sourceAtoms]
        finalAtoms={tuple(v)for v in sourceColours};finalForeign=[v.tolist()for v in a['live96-final0'][audit[...,0]==1,:3]if tuple(v)not in finalAtoms]
        assert protectedExact and passExact and not foreignColours and not finalForeign and m['live96']['runtimeReadbackCalls']==0 and m['live96']['stackOverflow']==0
        r={'frame':e['frame'],'sourceId':e['sourceId'],'stage':m['motion82']['stage'],'index':m['motion82']['index'],'protectedPixels':int(protected.sum()),'protectedExact':protectedExact,'passThroughExact':passExact,'paletteOutsideSourceRGB':len(foreignColours),'finalFeatureOutsideSelectedPalette':len(finalForeign),'invalidNative':int((audit[...,0]<0).sum()),'sourceGraphFrames':m['live96']['sourceGraphFrames'],'finalPresentations':m['live96']['finalPresentations']};rows.append(r);cost.append(m['live96'])
    unknown=[];provenance=load(HERE/'oracle-turn97/CELL_PROVENANCE95-source-cache-turn97v2.json')
    for p in provenance:
        for c in p['cells']:
            if c['decision']['winner'] is None:
                unknown.append({'frame':p['frame'],'canonicalXY':c['cell'],'massBounds':c['decision']['massBounds'],'possibleLabels':c['decision']['possibleLabels'],'reason':'exact coverage tie, not producer/alpha uncertainty'})
    # Preserve baseline evidence separately: it contains old colour and independent
    # source metadata, so it must not be mistaken for a ready-to-use RGBA underlay.
    backing=load(HERE/'BACKING_FAILURE97.json')
    for b in backing:
        d=packet(Path(next(e['output']for e in state['sequencePackets']if e['frame']==b['frame'])));rx,ry,rw,rh=d['roi'];x,y=b['physicalHeadRayTopLeft'];px=int(x)-rx;py=rh-1-(int(y)-(272-ry-rh));b['baselineCellXY']=[px,py];b['pre348Baseline']=dict(zip(['colour','owner','meta','uv','domain','stamp'],d['baseline'][py,px].tolist()))
        b['conclusion']='real same-frame non-eye hair exists in base; skin-only underlay contract rejects it; exact native sampling/owner provenance not yet integrated'if b['frame']==128 else'no skin intersection or base/backing source here; original/world underlay at actual native sample was not captured; do not synthesize neighbouring skin/background'
    save(HERE/'ROTATION_FAILURES97.json',{'canonicalUnknownCells':unknown,'nativeBackingFailures':backing,'countsAreNotAestheticMetric':True})
    cold=[];pics=[];out=HERE/'review97';out.mkdir(exist_ok=True)
    fixture=next(x for x in load(HERE/'fixtures/FRAMES96.json')if x['frame']==102);cw,ch=fixture['width']//4,fixture['height']//4
    for policy in [0,1,4]:
        folder=HERE/f'cold{policy}';r=load(folder/'REPORT96.json');assert r['complete']and r['remainingOwnedBytes']==0 and r['rows'][0]['queries']>0
        colour=read(folder/'gpu-output/102-final0.bin');ident=read(folder/'gpu-output/102-identity.bin').reshape(ch,cw,4);decision=read(folder/'gpu-output/102-decision.bin').reshape(ch,cw,4);oracle=np.load(HERE/'fixtures/oracle102.npz');shape=oracle['finalColour'].shape if 'finalColour'in oracle else None
        # FrozenComposition fixture stores native output dimensions in the report
        # input NPZ under finalColour; fall back to full-frozen's validated output.
        if shape is None:
            z=np.load(HERE/'oracle/candidate-source-cache-actual96/frame102.npz');shape=z['colour'].shape
        if int(np.prod(shape)//4)!=len(colour):
            # Frozen95 native ROI differs from actual96 ROI. Read its contract.
            z=np.load(ROOT/'final-eye95/candidate-source-cache-scale-correct/frame102.npz');shape=z['colour'].shape
        colour=colour.reshape(shape);im=Image.fromarray(np.flipud(rgb8(colour[...,:3])));im.save(out/f'cold-policy{policy}-native1x.png');pics.append((policy,im));changed=[]
        for y,x in np.argwhere(decision[...,1]==2):changed.append({'xy':[int(x),int(y)],'role':int(ident[y,x,0]),'sourceOwner':int(ident[y,x,1]),'sourcePrimitive':int(ident[y,x,3]),'literalRGBA':read(folder/'gpu-output/102-colour.bin').reshape(ch,cw,4)[y,x].tolist()})
        default=read(HERE/'cold0/gpu-output/102-final0.bin').reshape(shape);delta=np.any(colour!=default,axis=-1)
        cold.append({'policy':policy,'meaning':{0:'unresolved/original pass-through',1:'iris priority comparison only',4:'sclera priority comparison only'}[policy],'unresolvedCanonical':int((decision[...,0]<0).sum()),'explicitPriorityChoices':changed,'differentNativePixelsFromDefault':int(delta.sum()),'changedNativeXY':[list(map(int,[x,y]))for y,x in np.argwhere(delta)],'adopted':False})
    w=max(im.width for _,im in pics);h=max(im.height for _,im in pics);board=Image.new('RGB',(w*8*3,h*8+24),'#20242a');draw=ImageDraw.Draw(board)
    for i,(policy,im)in enumerate(pics):board.paste(im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST),(i*w*8,24));draw.text((i*w*8+4,5),f'Cold {policy} - comparison, not adopted',fill='white')
    board.save(out/'cold-policy-comparison8.png');save(HERE/'COLD_POLICIES97.json',cold)
    lifetime=load(HERE/'lifetime/REPORT96.json');assert lifetime['complete']and all(lifetime[k]for k in ['simultaneousOwnersIsolated','paletteChangesOnlyRGBNotRegion','explicitWitnessInvalidationClearedOnlyB','AStillWorksAfterBDisposal','failedConstructorCleanup','wrongScopeRejected','doubleDisposeSafe','disposedUseRejected'])and lifetime['remainingOwnedBytes']==lifetime['cancelBeforeFirstFrameOwnBytes']==0
    turn=load(HERE/'TURN_CPU_GPU97.json');assert all(all(v==0 for k,v in r.items()if k.endswith('Max'))for r in turn['rows'])
    summary={'status':'ISOLATED_REALTIME_GPU_CHECKPOINT_ROTATION_NOT_PASSED','baseCommit':'2672df7a54027dbb6f2699baf44151a7ab61c9d6','productDefault':77,'newAssetChanges':0,'runtimeSelectionNotOfflineReplay':True,'capturePlayEntries':1,'actualCapturedFrames':len(rows),'actualSourceSequence':'eye97-20261101T154213833Z-84e16ccb','phaseFrames':10,'walkFrames':8,'turnFrames':10,'phase':{k:review[k]for k in ['phaseRoleOwnerSignatures','phaseColourSignatures','phaseXRange','phaseYRange']},'actualFinalPresentations':max(c['finalPresentations']for c in cost),'sourceGraphFrames':max(c['sourceGraphFrames']for c in cost),'perObserverNormalSerialNotProductHook':True,'rotationUnresolvedNativeByFrame':review['unknownNativeByFrame'],'rotationIndependentCPUColourOwnerDepthExact':True,'rotationCPUColdHistoryLimit':turn['scope'],'rotationDesignOrInputContractsUnresolved':True,'runtimeGPUToCPUReads':0,'captureDiagnosticReadbacks':True,'sourceVertices':20459,'sourceTriangles':29542,'ownedAlgorithmBufferBytes':max(c['ownedBufferBytes']for c in cost),'queryRange':[min(c['queryCount']for c in cost),max(c['queryCount']for c in cost)],'triangleTestsRange':[min(c['triangleTests']for c in cost),max(c['triangleTests']for c in cost)],'maximumVisitedNodes':max(c['maximumNodesVisited']for c in cost),'GPUTimeMeasured':False,'perQueryFullMeshScan':False,'sourceMeshCPUUploadPerFrame':True,'lifetimeGPUValidated':True,'allProtectedExact':True,'allOriginalPassThroughExact':True,'allFeatureRGBLiteralSourceAndPaletteMember':True,'coldPriorityPoliciesAdopted':False,'afterCompileSourceGuards':'borrowed alpha liveness and view/source-array identity guards compiled in cold/lifetime runners; added after actual motion capture, not separately live-renderer exercised','EditorPlayExited':True,'scenePublicInputSettingsDevicesOptionsTimePipelineDifferences':differences,'dirtyBefore':len(pre['dirty']),'dirtyAfter':len(post['dirty']),'nativeContentsDirectExact':47,'InputSettingsSameIdentityAndJSON':pre['input']==post['input'],'motionRestoration':state['motionRestoration82'],'globalRestoreErrors':state['globalRestoreErrors'],'RTBefore':state['beforeMemory']['renderTextureCount'],'RTAfter':state['afterMemory']['renderTextureCount'],'UnityTotalAllocatedDeltaMiB':(state['afterMemory']['allocated']-state['beforeMemory']['allocated'])/1048576,'memoryNote':'Unity allocated counter; not working set, not leak proof. Owned buffers zero after disposal; no forced GC.','productIntegrated':False,'aestheticSuccess':False,'rows':rows}
    summary['latestReadOnlyEditorUTC']=current['utc'];summary['latestPublicStateStillRestored']=True
    save(HERE/'SUMMARY97.json',summary)
    page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>97 실시간 공동 선택: 위상·보행·회전</title><style>body{font:16px system-ui;line-height:1.65;margin:24px;background:#20242a;color:#eee}a{color:#9dd7ff}img{image-rendering:pixelated;max-width:100%}.native{max-width:none;margin:8px}.warn{color:#ffd18a}td,th{border:1px solid #777;padding:6px}table{border-collapse:collapse}</style><h1>97 실시간 GPU 공동 선택 검증</h1><p class="warn">중간 체크포인트 · 회전 미통과 · 제품77 기본 경로 유지 · 미관 성공 아님</p><p>실제 현재 변형 정점/원본 UV·재질·alpha로 GPU에서 BVH refit → 가림 query → 공동 선택 → 별도 native 합성을 수행했습니다. 오프라인 선택을 재생한 결과가 아닙니다. 28장 관측 중 정상 렌더 serial별 합성41회, source Graph42회입니다. 외부 관찰기 연결이며 제품의 기본 callback에는 아직 통합하지 않았습니다.</p><p>실제 0→0.999985픽셀 상대 위상10장에서는 canonical 형태와 RGB 서명이 각각 하나였습니다. 보행8장은 실제 표면/자세/가림 변화가 있으므로 단순 셀 수 불변을 요구하지 않습니다. 회전10장 중4장에서 미확정1~6 native 픽셀이 남았습니다. 그 부분은 원본을 그대로 보존하고 실패로 기록했습니다.</p><p>독립 CPU의 실제 삼각형/원본 alpha 계산과 회전4장의 최종 RGB·owner·깊이는 정확히 일치합니다. 이는 구현 이식 오차를 배제하는 근거이며, 동률의 미술적 정답이나 누락된 바탕을 보장하지 않습니다. 이 CPU 검사는4장만 냉시작했으므로 미관측 warm history 전체 동등성을 주장하지 않습니다.</p><p>남은 원인: 정확한 coverage 동률6 canonical 셀, 바탕 복원3 native 픽셀입니다. frame128의2픽셀은 실제 머리카락 바탕이 있지만 피부만 받는 복원 계약이 거부했습니다. frame134의1픽셀은 피부 교차/base/backing이 없고 실제 world underlay는 미캡처입니다. 주변 색을 만들어 채우지 않았습니다.</p><p>알고리즘 버퍼6,418,564bytes. GPU→CPU 읽기는 추가 runtime 클래스에 없고, 여기의 읽기는 진단 캡처입니다. 정적 topology BVH 구축 이후 매 프레임 O(T) refit·계층 query를 사용합니다. GPU 시간·제품 FPS는 미측정입니다. 여러 view 동시 격리·색/영역 독립·명시적 cache 무효화·중도 취소·생성 실패·중복 해제 검사는 별도 GPU 시험에서 통과했습니다.</p><p>정상 Edit 종료, scene/입력 객체와22값·장치·옵션·pipeline/time·dirty31 유지, 직접 직렬화47/47 동일, RT30→30을 확인했습니다. Unity allocated 증가35.36MiB는 물리 RAM/누수 판정이 아닙니다.</p><p><a href="SUMMARY97.json">요약/한계</a> · <a href="ROTATION_FAILURES97.json">동률·바탕 좌표/원본 수치</a> · <a href="TURN_CPU_GPU97.json">CPU/GPU 비교</a> · <a href="COLD_POLICIES97.json">동률 선택 비교</a> · <a href="lifetime/REPORT96.json">수명 검사</a> · <a href="WholeEye96.cs">GPU 자원 소유</a> · <a href="WholeEye96.compute">Query/Select/Compose</a> · <a href="LiveFinal96.cs">정상 serial별 최종 합성</a></p><h2>정확 동률의 명시적 비교</h2><p>냉시작 부분 Close50에서0=미확정/원본 보존,1=홍채 우선,4=흰자 우선. 후자의 두 정책은 디자인 비교이며 채택하지 않았습니다. 원본 key witness가 현재 가시할 때만 이전 source identity를 쓸 수 있습니다.</p><img src="review97/cold-policy-comparison8.png">'''
    for stage,frames in [('measured-phase',[101,105,109,110]),('walk',[119,122,126]),('turn',[127,128,134,136])]:
        page+=f'<h2>{stage}</h2><img src="review97/{stage}.gif">'
        for f in frames:page+=f'<details><summary>frame{f}: 원배율 / nearest ×8</summary><img class="native" src="review97/frame{f}-product77-native1x.png"><img class="native" src="review97/frame{f}-live97-native1x.png"><img src="review97/frame{f}-nearest8.png"></details>'
    page+='</html>';page=page.replace('알고리즘 버퍼6,418,564bytes','알고리즘 버퍼 최대6,678,916bytes (가변 canonical ROI에 따라 재할당)');(HERE/'INDEX97.html').write_text(page,encoding='utf-8')
    print(json.dumps({k:summary[k]for k in ['actualCapturedFrames','actualFinalPresentations','rotationUnresolvedNativeByFrame','ownedAlgorithmBufferBytes','queryRange','triangleTestsRange','maximumVisitedNodes','nativeContentsDirectExact','UnityTotalAllocatedDeltaMiB']},indent=2))

if __name__=='__main__':main()
