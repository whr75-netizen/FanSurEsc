from pathlib import Path
import json,hashlib,shutil,zipfile,subprocess,sys
H=Path(__file__).resolve().parent;R=H.parent;E=R/'closed-support105';P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
BASE='5f296c87d77fb7426a378f7dbc6188b50e317afc';REL='experiments/pixel-pipeline/2026-11-01-source-regions104-lid105';DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(P),*args],encoding='utf-8').strip()
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists(),q;shutil.copy2(p,q)

def prepare():
    d=H/'archive';d.mkdir(exist_ok=False)
    for p in H.rglob('*'):
        if p.is_file()and 'archive'not in p.relative_to(H).parts and p.suffix in('.py','.json','.png','.npz'):
            copy(p,d/'source-regions104'/p.relative_to(H))
    copy(R/'uv-features64/uv_features64.py',d/'source-regions104/uv_features64.py')
    for part in (3,6):
        for f in ('hierarchy.npz','source.png','uv-domain.png'):copy(R/f'source-regions103/part{part}'/f,d/f'source-regions103/part{part}'/f)
    copy(R/'source-regions103/SOURCE_EVIDENCE103.json',d/'source-regions103/SOURCE_EVIDENCE103.json')
    copy(R/'native-feature89/REGISTRATION89.json',d/'native-feature89/REGISTRATION89.json')
    for name in ('analyse105.py','source_curve105.py','curve_candidate105.py','prepare_direct105.py'):
        copy(E/name,d/'closed-support105'/name)
    copy(R/'forward-eye102/analyse102.py',d/'closed-support105/analyse102.py')
    copy(R/'forward-eye102/selection102.py',d/'closed-support105/selection102.py')
    copy(R/'apply-capture66/analyse_capture68.py',d/'closed-support105/analyse_capture68.py')
    execution=[]
    with zipfile.ZipFile(d/'RAW105.zip','x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for label,cap in [('witness',E),('direct',E/'direct')]:
            last=sorted(cap.glob('STATE102-*'))[-1];s=load(last)
            assert s['stage']=='finished'and s['PlayExited']and not s.get('error')and not s.get('restorationError')
            assert not any(x['equal']is False for x in s['nativeComparisons72'])
            execution.append({'run':label,'request':load(cap/'Capture102_REQUEST.json'),'reply':load(cap/'Capture102_REPLY.json'),'states':len(s['sequencePackets'])})
            for name in ('Capture102.cs','RUN_Capture102.cs.txt','GLOBAL_NAMES66.json','RESULT105.json','CELLS105.json','SOURCE_CURVE105.json','CLOSED_LID_CAUSE105.png','NATIVE_CURVE_MAPPING105.png','POST102.json','Post102_CONSOLE_AFTER.json'):
                copy(cap/name,d/'closed-support105'/label/name)
            copy(last,d/'closed-support105'/label/last.name)
            for image in cap.glob('*-1x.png'):copy(image,d/'closed-support105'/label/image.name)
            for packet in s['sequencePackets']:
                p=Path(packet['output']);assert(p/'RAW_COMPLETE76.marker').read_text()==sha(p/'RAW_MANIFEST.json')
                for f in p.iterdir():
                    if f.is_file():z.write(f,label+'/frame-'+str(packet['frame'])+'/'+f.name)
    for name in ('CLOSED_CURVE_CANDIDATE105.png','CURVE_CANDIDATE105.json','PRESERVATION105.json'):
        copy(E/'direct'/name,d/'closed-support105/direct'/name)
    (d/'EXECUTION105.json').write_text(json.dumps(execution,indent=2),encoding='utf-8')
    (d/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n',encoding='utf-8')
    copy(H/'test_archive104_105.py',d/'test_archive104_105.py')
    page='''<!doctype html><meta charset="utf-8"><title>104/105 · 미채택 UV 분할 / 제한된 닫힌 안검 후보</title><style>body{font-family:system-ui;max-width:1400px;margin:30px auto;background:#20252c;color:#eee}a{color:#abd8ff}img{max-width:100%;image-rendering:pixelated}td{padding:15px}</style><h1>104/105: 원본 UV 영역 분할과 닫힌 안검 손실</h1><p>제품77 유지. 이 페이지는 완성된 얼굴 팔레트나 런타임 통합 결과가 아닙니다. 원본 RGB·UV·조명·소유권을 바꾸지 않고 실패 원인을 분리했습니다.</p><h2>104: 같은 원본 UV에 두 그래프 접근을 비교</h2><img src="source-regions104/SOURCE_REGION_COMPARE104.png"><p>색이 다른 영역 표시는 label debug이며 최종 팔레트가 아닙니다. 기존103은 피부와 두피 과병합, FH는681영역/311singleton, h-minima+geodesic은36영역/0singleton이지만 볼의 실제 얇은 칠을 같은 피부 parent에 합칩니다. 안검은 각각200/370영역입니다. 영역 수 감소만으로 채택하지 않았습니다.</p><p><a href="source-regions104/DECISION104.json">근거·정확한 방법·가정</a> · <a href="source-regions104/REVIEW104.json">실제 좌표·연결성</a> · <a href="source-regions104/WATERSHED_SYNTHETIC104.json">L코너 실패 포함</a></p><h2>105: 원본 안검은 남아 있는데 면적 선택에서 소실</h2><img src="closed-support105/direct/CLOSED_LID_CAUSE105.png"><p>완전 Close: native149표본/알파108.4634 → 실제 피부 가림 후96.7750,26논리셀 지지 → 최종1셀. 같은 프레임 source triangle/UV/변형/Query/Select를 기록했습니다. CPU/GPU864셀 불일치0입니다. 두 실행의 sourceId는 별개이며 6장이 연속 동작이라는 뜻이 아닙니다.</p><h2>저장 입력의 닫힌 곡선 후보 — 새 GPU 구현 아님</h2><img src="closed-support105/direct/CLOSED_CURVE_CANDIDATE105.png"><p>기존 native ring의 등록된 위쪽 chain을 실제 변형·기존 eyeInverse로 투영하고, 같은 셀에 같은 눈의 확정 가시 색소가 있는 곳만 사용합니다. 이 포즈에서는 각각 연결7셀. 셀 수 하드코딩/임의 피부색/가림 무시 없이 원본 sample RGB·depth를 직접 선택합니다. 열림·재개방0변경. 부분 Close/회전/연속성/안검 유한P는 미검증입니다. 열린 eye2의 0.0005px 표본 대조 한계도 그대로 실패로 남겼습니다.</p><table><tr><td>실제 GPU102 원배율<br><img src="closed-support105/direct/eye-frame104-1x.png"></td><td>오프라인 후보 원배율<br><img src="closed-support105/direct/OFFLINE_curve105-frame104-1x.png"></td></tr></table><p><a href="closed-support105/direct/CURVE_CANDIDATE105.json">후보·변경셀·source UV/depth 출처</a> · <a href="closed-support105/direct/SOURCE_CURVE105.json">직접 변환·대응검사</a> · <a href="closed-support105/direct/PRESERVATION105.json">보존·메모리 API</a> · <a href="RAW105.zip">실제6상태 원시입력</a></p><p>마지막 상태: Edit/dirty31/실제 PlayerSettings 포함46직렬화 내용 동일. 만료된 임시 AssetImporter1개는 unavailable이며47/47 동등성을 주장하지 않습니다. InputSettings 동일 객체22값·장치·옵션·시간·pipeline·globals 복원, RT30→30. 마지막 Unity GetTotalAllocatedMemoryLong +34.42MiB는 physical working set이나 누수 판정이 아닙니다. CUA/Assets import/제품수정/저장/삭제/초기화/강제종료/push0.</p><p>재현검사: 이 폴더에서 Python test_archive104_105.py. 게임 동작/미술/모든 모델 일반화 검증은 아닙니다. 최신 알고리즘 위치·미해결은 docs/ai/PIXEL_ALBEDO_20261030.md만 확인합니다.</p>'''
    (d/'INDEX.html').write_text(page,encoding='utf-8')
    items=[{'path':p.relative_to(d).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size}for p in sorted(d.rglob('*'))if p.is_file()]
    (d/'ARTIFACTS104_105.json').write_text(json.dumps({'files':items},indent=2),encoding='utf-8')
    print(json.dumps({'files':len(items)+1,'RAW105bytes':(d/'RAW105.zip').stat().st_size}))

def install():
    assert git('rev-parse','HEAD')==BASE and not git('diff','--cached','--name-only')
    a=load(R/'forward-eye102/ASSET102.json');assert all(sha(P/r['path'])==r['sha']for r in a['protected32'])
    assert set(git('diff','--name-only').splitlines())==set(a['modifiedBefore'])|{DOC}
    assert (P/DOC).read_text(encoding='utf-8').startswith(git('show','HEAD:'+DOC))
    assert sha(P/DOC)==load(H/'HANDOFF_EXPECTED104_105.json')['sha256']
    dest=P/REL;assert not dest.exists()
    for p in sorted((H/'archive').rglob('*')):
        if p.is_file():copy(p,dest/p.relative_to(H/'archive'))
    print('104/105 snapshot copied; no product/Assets changes')

def commit():
    assert git('rev-parse','HEAD')==BASE
    a=load(R/'forward-eye102/ASSET102.json');assert all(sha(P/r['path'])==r['sha']for r in a['protected32'])
    assert sha(P/DOC)==load(H/'HANDOFF_EXPECTED104_105.json')['sha256']
    allowed={REL+'/'+x['path']for x in load(P/REL/'ARTIFACTS104_105.json')['files']}|{REL+'/ARTIFACTS104_105.json',DOC}
    assert not git('diff','--cached','--name-only')
    git('add','--',REL,DOC);assert set(git('diff','--cached','--name-only').splitlines())==allowed
    assert not git('diff','--cached','--check')
    git('commit','-m','test(pixel): compare UV region graphs and isolate closed-lid shape loss')
    assert not git('diff','--cached','--name-only')
    assert git('diff','--name-only').splitlines()==a['modifiedBefore']
    assert all(sha(P/r['path'])==r['sha']for r in a['protected32'])
    result={'commit':git('rev-parse','HEAD'),'selectedFiles':len(allowed),'productDefault':77,'protected32Exact':True,'userModified30Preserved':True,'newAssets':0,'push':False}
    (H/'COMMIT104_105.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':{'prepare':prepare,'install':install,'commit':commit}[sys.argv[1]]()
