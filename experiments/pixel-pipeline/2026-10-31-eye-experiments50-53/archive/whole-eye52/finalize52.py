"""Publish only local experiment52 evidence; no Desktop/Git/Unity action."""
from pathlib import Path
import hashlib,json,re
from html import escape
from PIL import Image
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49';L=R.parent/'lid-evidence51'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,d):(R/name).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
s=load(R/'SUMMARY.json');b=load(R/'SOURCE_BINDING52.json');c=load(R/'CONSTRAINT_TESTS52.json')
uv=load(R/'CARRIER_ASSOCIATION52.json');f=load(R/'FRAME101_FEASIBILITY52.json')
manifest=load(B/'PACKAGE_MANIFEST.json');old_changes=[q['path']for q in manifest['files']if sha(B/q['path'])!=q['sha256']]
product=load(B/'fixtures/template43.json')['productSHA256'];prod_changes=[p for p,h in product.items()if sha(Path(p))!=h]
input_changes=[p for p,h in b['inputs'].items()if sha(Path(p))!=h]
assert not(old_changes or prod_changes or input_changes)
preservation=dict(previous49FilesChanged=old_changes,tracked12ProductDiskChanges=prod_changes,
    boundSourceDiskChanges=input_changes,newUnityCalls=0,newCapture=0,newCommit=False,newDesktopWrite=False,
    liveEditorState='NOT queried. Parent reports old Unity PID gone and new PIDs; current project/scene/dirty unknown.',
    historicalDirty25='Preservation target only, not a claimed current observed state.',
    noGCUnloadUIResetSaveExit=True,sourceArrayChecks=c['assertions'],runningCommandAtHandoff=None)
dump('PRESERVATION52.json',preservation)
report=f'''# 전체 눈 소스·키폼 연결 실험52 — 미채택

전체 파츠를 하나의 캐시와 기준점에 연결하는 오프라인 adapter를 구현했다. **제품 눈 보정 완료가 아니다.** 원본 연결·순수 위상 불변성은 확인했지만, 전체 안검/홍채/흰자의 일관된 최종 픽셀 형태는 해결되지 않았다. 네이티브 안검을 원본에서 다시 샘플링한 후보도 충돌/누락 때문에 채택하지 않았다.

## 실제 구현

- `whole52.py:WholeEye52.request`: source 해시와 상태를 확인한 뒤 모든 파츠에 공통 정수 이동을 적용한다. `T=floor(projectedAnchor+phase-referenceAnchor+0.5)`, `xy_i=referenceXY_i+T`. parent/iris와 상·하 경계도 같은 T를 사용한다. 파트별 면적 반올림·순위로 shape를 재결정하지 않는다.
- `attach_carrier`: 기존 Template216의 20셀을 Eye205 원래 triangle/barycentric/UV/팔레트 텍셀과 연결한다. 기존 참조 표본 위치 `(x+.75,y+.25)`를 사용한다. `uv=Σ λ_i uv_i`, point sampler 텍셀은 `floor(uv*size)`이다. **20/20셀 RGBA가 literal Template와 정확히 일치**한다. 새 색이나 현재 찌그러진 raster를 기준형으로 만들지 않았다.
- `build52.py`: native Face role6(실제 eyeline 별도 mesh)의 triangle/UV와 원래 24정점 안검 경계를 연결한다. 일반 FaceSkin을 안검으로 재분류하지 않는다. UV2는 기존 연속 변형 가중치이며 binary 안검 마스크로 쓰지 않는다.
- 원본 GLB UV와 native Unity UV를 4060정점에서 대조했다. `UnityU=GLTFU`, `UnityV=1−GLTFV`, 오차0. native 안검 PNG 표본은 source UV의 **오프라인 무조명 참고색**이다. 실제 S3RGBA/명암 또는 GPU 필터 결과를 복원했다고 하지 않는다.
- `Fcl_EYE_Close`, `_R`, `_L` 각각 50/100%에 원본 경계 정점과 UV를 연결했다. native 변형은 있지만 해당 상태의 등록된 저해상도 pixel key-form이 없으므로 **cells=[] / unknown**을 반환한다. 열린 눈을 재사용하지 않는다.

초기 본 순서 가정은 약2셀 오차로 기각했다. 두 흰자 평면을 이용한 공통 reference projection을 먼저 구하고 원래 두 eye bone과 교차 검증했다. Eye0→bone20, Eye1→bone19이며 최대 오차는 {max(e['maxReferenceFitError']for e in b['eyes']):.9f}셀이다. 이 수치는 소스 대응 오차이며 미술 합격 기준이 아니다.

## 검증 범위와 실제 실패

- 저장 5pose + 별개 실제 frame96..101의 기준점에서 각각 33×33 위상을 검사했다. 합계 **{s['phasePlacements']} 배치**, probe별 상대 형태1종, 공통 이동/UV/소스ID/팔레트 소속 불변. 실제 가림은 위상 sweep에서 합성하지 않았다. 따라서 이것은 연속 회전·blink·최종 visibility 안정화 검증이 아니다.
- 실제6frame의 원본 S1/S2/S3 대표표본 **{s['actualMeasuredSourceBindings']}개**를 원본 material triangle/barycentric/UV로 되짚었다. 최대 위치 잔차 `{s['maxActualSourcePointError']:.3g}`, UV 잔차 `{s['maxActualUVError']:.3g}`. `ACTUAL_SOURCE_BINDINGS52.json`에 전부 있다.
- native role6을 기존 reference 표본으로 래스터화하면 상안검2셀(모두 eye1), 하안검0셀이다. **원본에 하안검 정보가 없다는 뜻이 아니다.** 얇은 source가 그 고정 표본에 걸리지 않았고, 이 raster를 완성된 키폼으로 쓰면 안 된다.
- reference `(219,79)`에서 흰자/상안검, `(221,78)`에서 홍채/상안검이 중복된다. 이 후보는 매 프레임 실제 source를 확인해도 충돌 수 `{s['visibleConflictsPerFrame']}`가 남는다. 충돌 셀은 magenta로 표시하며 임의 우선순위나 새 셀로 채우지 않는다.
- 실제 frame101 source 상안검은 `(222,52)`이다. 같은 셀에 기존 Template의 홍채가 있다. 홍채 우선이면 원래 홍채4셀/안검0, 안검 우선이면 홍채3셀/안검1이다. 공통 T를 적용해도 교집합은 변하지 않는다. **이 고정 래스터 두 개와 단순 순서 변경만으로 양쪽을 모두 유지할 수 없다. 눈 보정 자체가 불가능하다는 결론은 아니다.**
- 해당 홍채 대표표본은 S2 primitive297, UV `(0.650898755,0.671227872)`, barycentric `(0.458215211,0.340783662,0.201001127)`이다. S2 표본5개가 있으나 S3 가림 후 대표 가중치는 `0.011764706`이다. 존재 여부만으로 불투명 홍채 셀을 무조건 살리는 것도 실제 안검 가림을 무시할 수 있다.
- 원본 역할+가림을 유지한 기존51/50 조합에서 eye1 홍채는 `{s['iris1AfterPreservingSourceLid']}`다. 새52가 이를 해결한 것으로 보고하지 않는다. native 안검 reference 후보 위치도 실제 frame101 상안검 위치와 다르므로 새 정답으로 승격하지 않았다.
- 추가 {c['assertions']} assertion: 앞 머리 가림 유지, S3가 없으면 native 안검 출력 금지, S1/S2가 없으면 홍채/흰자 생성 금지, foreign material을 피부 underlay로 지우지 않음, frozen 입력 불변, frame101 순서 반례.

## 이미지 해석

`actual6-layers-1x.png`는 저장 출력 크기(논리셀2×2), `8x`는 그 정수 nearest 확대다. 열은 frame96..101. 행은 ①실제 저장 최종 ②전체 reference 배치/충돌 ③원본 가시성 적용 홍채·흰자 레이어 ④native 안검 참고 레이어 ⑤모호하지 않은 셀+충돌 표시 ⑥기존 source50 안검 ID(gold)다. **②~⑥을 원본 얼굴 위에 합성한 최종 결과로 표시하지 않는다.**

실제 PNG를 로컬 파일로 열어 확인했다. ②/⑤ magenta 겹침, ④ 오른쪽 눈에만 남은 두 native 안검 표본과 frame100의 한 셀 손실, ⑥frame101 기존 상안검 위치를 확인했다. 이미지 검수 결과도 미채택이다. `source-close-geometry.png`의 선은 실제/기존 경계이며 Closed pixel art가 아니다.

## 다음 통합에 필요한 최소 범위

1. 현재20셀을 전체 눈으로 간주하는 계약을 교체해야 한다. parent/iris/native 상·하안검/표정별 공유 경계에서 **공동으로 상태 raster를 결정**해야 한다. 모든 기존 셀을 무조건 동결한 뒤 우선순위만 조절하는 방식은 위 반례로 실패했다. 2px 고정이나 임의 최소 셀 수를 새 규칙으로 넣을 근거도 없다.
2. 먼저 부족한 실제 입력만 확인한다: 원래 `EyeSkin348.shader`의 이미 할당된 S0 Target4에 aperture control을 출력하는 기존51 후보, S0UV, S3RGBA/S3Shade를 동일 source/frame/state에 기록. ordinary skin/lid 경계를 continuous control 하나로 임의 확정하면 안 된다. 기존 native morph/source 역할/깊이와 함께 대조한다.
3. 실제 제품 연결 후보는 `EyeFeature348.cs`의 Initialise/Prepare에서 source/key-form/state 관리, `EyeRenderer367.cs`의 Samples/Candidate.Dispatch에서 동일 프레임 cache/part/visibility 전달, `EyeFeature348.compute`의 IrisAllocated19/NativeLineAllocated19/ChooseLayers19/Evaluate에서 source part와 캐시의 공동 배치·가림 결정이다. 소스 확인용 S0 output만 `EyeSkin348.shader`가 추가 범위다. **아직 이 파일들을 수정하거나 GPU 통합하지 않았다.** pixel state가 미정이므로 지금을 적용 가능한 완성 diff라 하지 않는다.
4. source50의 안검 결정이 cache iris를 다시 제외·재순위하여 `(221,53)`으로 옮겨지는 feedback은 계속 제거되어야 한다. 공동 키폼과 실제 hair depth gate는 별개다. 실제 앞 머리카락 뒤를 새 눈색으로 메우지 않는다.
5. 향후 Unity 접근은 parent가 알린 새 instance 이후 project/scene/dirty부터 재확인해야 한다. 이번에는 Unity 조회도 하지 않았다. 추가 GPU 실행은 현재 금지라 미실행이며, 새 도구 거부나 승인 대기 실행은 없다.

## 보존

기존49 파일, 추적한 제품12파일과 bound source 디스크 해시 차이0. 50/51/원본/31/34/기존 커밋을 변경하지 않았다. 새 커밋/공유/업로드/Desktop 복사/Play/캡처/GC/UI/앱 종료/씬 저장0. 현재 Editor scene/dirty는 조회하지 않았으며 dirty25 유지가 관측됐다고 말하지 않는다.
'''
(R/'REPORT_KO.md').write_text(report,encoding='utf8')
links=['SUMMARY.json','WHOLE_KEYFORM52.json','SOURCE_BINDING52.json','CARRIER_ASSOCIATION52.json',
    'ACTUAL_SOURCE_BINDINGS52.json','FRAME101_FEASIBILITY52.json','PHASE_TESTS52.json','CONSTRAINT_TESTS52.json','PRESERVATION52.json']
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>52 전체 눈 소스·키폼 — 미채택</title>
<style>body{background:#171b22;color:#e1e5ec;font:16px/1.6 system-ui;margin:32px}main{max-width:1650px}a{color:#92c9ff}b{color:#ffd27b}pre{white-space:pre-wrap}img{image-rendering:pixelated;max-width:none}.scroll{overflow:auto;border:1px solid #535b68;padding:12px}.note{background:#28303c;padding:16px}li{margin:6px 0}.columns{display:grid;grid-template-columns:repeat(6,256px);font-weight:bold;margin-left:12px}.small{font-size:14px;color:#b8c1d0}</style>
<main><h1>52 전체 눈 소스·키폼 연결 <b>미채택</b></h1>
<p class="note">오프라인 adapter와 source 대응 검증 결과입니다. 전체 눈 형태/GPU 통합은 미완입니다. 원본 얼굴에 새 눈을 덧씌운 최종 결과를 만들어 보인 자료가 아닙니다.</p>
<p>기존 홍채·흰자 20셀의 carrier UV/팔레트 일치 20/20. 부모·홍채·원본 상/하 안검 경계·Close 변형을 같은 캐시에 연결했습니다. 11,979개 순수 위상 배치에서 상대 형태는 유지되지만, 안검 reference raster에는 겹침/누락이 남습니다.</p>
<p><a href="REPORT_KO.md">전체 근거·정확한 연산·다음 최소 범위</a> · <a href="whole52.py">adapter</a> · <a href="verify52.py">위상/실제6frame 대조</a> · <a href="constraints52.py">가림/순서 반례</a></p>
<h2>같은 실제 6frame과 분리 레이어</h2>
<ol><li>실제 저장 최종</li><li>전체 reference 배치 — magenta는 서로 겹치는 다른 파트</li><li>동일 source의 실제 가림을 적용한 홍채·흰자 레이어</li><li>native 안검 reference 후보: 원본 PNG 무조명 참고색, 실제 S3 최종색 아님</li><li>모호하지 않은 셀 + 충돌 표시 — 완성된 합성 결과 아님</li><li>기존 source50 native 안검 ID (gold) — RGB 아님</li></ol>
<p>2~6행은 각각 독립 진단입니다. 표본 없는 곳은 채우지 않았습니다. 색/개수만으로 미감 합격을 판정하지 않았습니다.</p>
<h3>저장 출력 크기 (논리셀 2×2)</h3><div class="scroll"><img src="actual6-layers-1x.png" width="192" height="96" alt="actual6 diagnostic layers at saved size"></div>
<h3>정수 8배 nearest 확대</h3><div class="scroll"><div class="columns"><span>96</span><span>97</span><span>98</span><span>99</span><span>100</span><span>101</span></div><img src="actual6-layers-8x.png" width="1536" height="768" alt="six frames six diagnostic layers, magenta conflicts"></div>
<h2>frame101 고정 셀 충돌</h2><p>실제 상안검과 기존 Template 홍채가 모두 (222,52)를 사용합니다. 홍채 우선: 홍채4/안검0. 안검 우선: 홍채3/안검1. 이 고정 두 footprint의 순서만 바꿔서는 둘 다 유지되지 않습니다. 이는 전체 눈 보정이 불가능하다는 주장이 아닙니다.</p>
<h2>원본 Close geometry / pixel form 미정</h2><img src="source-close-geometry.png" width="720" height="480" alt="native Close morph geometry only, no fabricated pixel shape">
<p class="small">cyan=기존 authored parent, red=기존 iris, gold=원본 native boundary. Close50/100은 native 변형 경계만 있습니다. 열린 눈 RGB를 재사용하지 않습니다.</p><h2>수치 파일</h2><ul>'''
html+=''.join('<li><a href="'+escape(p)+'">'+escape(p)+'</a></li>'for p in links)
html+='''</ul><p>제품/Unity/화면 제어/새 캡처/커밋 변경 없음. 현재 Editor scene·dirty는 조회하지 않아 미확인입니다.</p></main></html>'''
(R/'INDEX.html').write_text(html,encoding='utf8')
missing=[]
for href in re.findall(r'(?:href|src)="([^"]+)"',html):
    if not(R/href).exists():missing.append(href)
assert not missing
for name,wh in[('actual6-layers-1x.png',(192,96)),('actual6-layers-8x.png',(1536,768)),('source-close-geometry.png',(720,480))]:
    assert Image.open(R/name).size==wh
dump('RESUME.json',dict(status='offline whole source adapter complete; coherent full pixel form not solved/not adopted',
    entry='INDEX.html',runOrder=['prepare52.py','build52.py','verify52.py','constraints52.py','finalize52.py'],
    outputs='No new commit. Keep all52 files separate from approved49.',liveEditorState='unknown; no query',
    pendingProcess=None,need='joint source-supported pixel state and scoped GPU evidence; not a priority-only patch',
    prohibitedUntilChanged=['Unity calls','new captures','GC/unload','UI control','new product writes','new commit']))
files=[]
for p in sorted(R.iterdir()):
    if p.is_file()and p.name!='OUTPUT_MANIFEST.json':files.append(dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)))
dump('OUTPUT_MANIFEST.json',dict(files=files,externalFrozen49Unchanged=True,product12Unchanged=True,linksChecked=True,
    localPNGViewed=True,UIControlUsed=False))
print(json.dumps(dict(entry=str(R/'INDEX.html'),files=len(files),linksChecked=True,
    product12Changes=0,previous49Changes=0,newUnityCalls=0,newCommit=False),ensure_ascii=False,indent=2))
