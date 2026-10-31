"""Local evidence/index only. No Desktop, Unity, UI or Git action."""
from pathlib import Path
import hashlib,json,re
from html import escape
from PIL import Image
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49';F=R.parent/'whole-eye52'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,d):(R/n).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
s=load(R/'SUMMARY.json');a=load(R/'READABILITY_AND_SOURCE_ERROR53.json');rows=load(R/'FRAME_RESULTS53.json')
enum=load(R/'JOINT_ENUMERATION53.json');reject=next(t for t in enum['trials']if t['shifts']=={'iris':[0,0],'sclera':[0,0],'upper-lid':[0,-1]})
product=load(B/'fixtures/template43.json')['productSHA256'];changed=[p for p,h in product.items()if sha(Path(p))!=h]
old=[]
for root in[B,F]:
    m=load(root/('PACKAGE_MANIFEST.json'if root==B else'OUTPUT_MANIFEST.json'))
    old.extend(str(root/f['path'])for f in m['files']if sha(root/f['path'])!=f['sha256'])
assert not(changed or old)
dump('PRESERVATION53.json',dict(product12Changes=changed,old49And52Changes=old,
    writesOnlyThisExperiment=True,newUnityCalls=0,newCapture=0,newCommit=False,newUIControl=False,
    noGCUnloadSaveResetExit=True,currentEditorSceneDirty='not queried; current instance/project/dirty unknown',runningProcess=None))
equal_height=[t for t in enum['trials']if t['feasible']and t['shifts']['iris'][1]==0]
assert not equal_height
dump('BOUNDED_COUNTEREXAMPLE53.json',dict(scope='this exact rigid-glyph/L1<=1 candidate family only',
    withNoIrisVerticalDisplacementFeasible=len(equal_height),
    reason='All two source-occlusion-safe solutions move iris/sclera down one cell. Native-up alone intersects nearer hair/brow source. This is not a proof that non-rigid joint eye correction is impossible.',
    rejectedNativeUp=reject,feasible=[t for t in enum['trials']if t['feasible']]))
missing={str(r['frame']):r['unknownUnderlayCells']for r in rows}
dump('MISSING_UNDERLAY53.json',dict(missingCells=missing,logicalSamples=sum(map(len,missing.values())),
    why='Old same-eye feature pixels must be removed when the glyph moves. Saved final/head/eye-output already contain old eye RGB; using them as a clean backing leaves ghost features.',
    requiredSameFrameInput='The existing Evaluate-selected bc/bm before win-colour replacement: BaseRGBA/META versus BackingRGBA/META nearest valid depth, or an equivalent verified eye-free skin layer.',
    relevantCode='EyeFeature348.compute Evaluate selects Base/Backing; EyeRenderer367.Candidate.Dispatch already binds v.layers[8] and [10].',
    alternative='S0RGBA plus source metadata and the exact original resolve rule, if equivalent backing selection is proven; not texture-mean/nearby-skin copying.',
    captureNotExecuted=True,currentUnityProhibited=True,
    pastSourceIdsCannotBeReusedForNewFrames=True,
    practicalNextInput='A new paired frozen replay with the same metadata and selected clean underlay at vacated old-feature cells; keep its new sourceId distinct from frozen100/101. No large capture loop is required.'))
report=f'''# 53 눈 파츠 공동 할당 — 제한된 오프라인 후보

**(222,52)의 내부 충돌은 파츠를 삭제하지 않고 풀 수 있었다.** 현재 실험의 고정 source/state에서 기존 홍채 클러스터·흰자·확인된 native 상안검을 동시에 할당하는 코드를 구현하고 실제 PNG로 확인했다. 다만 눈이 1셀 낮아지는 형상 대가가 있고, 비워진 원래 눈의 배경색이 저장되지 않아 **완전한 원본 얼굴 합성은 미완**이다. 미술 성공·제품/GPU/실제 시간 안정화로 판정하지 않는다.

## 입력과 범위

- 같은 실제 sequence `counts47-087454994917423fa13c5fe72eceb7f4`의 frame100/101만 등록했다. 둘 다 blink0/style 동일, 공통 root 이동 `[2,-26]`이다. 두 프레임을 함께 사용한 오프라인 진단이며 미래 입력을 보지 않는 runtime 알고리즘이라고 하지 않는다.
- 홍채/흰자 목표는 기존 Template216/205 carrier의 해당 눈 **4/6셀**이다. 전역4셀/2셀 상수가 아니다. glyph 개수는 입력 리스트에서 읽는다.
- 상안검 token은 실제 frame101 `(222,52)`에서 native feature5/eye1 확인 후 가져왔다. source S3 primitive10, UV `(0.597450197,0.738912344)`, barycentric `(0.112372799,0.630962205,0.256664996)`, 3D 잔차 `2.07e−9`이다. RGB8 `[81,63,54]`는 이 실제 최종 출력의 고정 참조색이다. **무조명 원색/GPU S3 전체색 복원 또는 새 조명 반응이 아니다.** frame100에도 실제 S3 source가 있음을 확인했다. native part의 면적 반올림0을 그대로 '부위 없음'으로 취급하지 않았다.
- 이 한 native 출력 token이 전체 안검 곡선의 승인된 pixel key-form을 뜻하지는 않는다. 하안검의 현재 feature6은 일반 피부의 normalized 분류에서도 만들어지므로 원본 native 의미 part라고 승격하지 않았다. Closed/다른 pose는 추정해 채우지 않는다.

## 구현한 공동 계산

`joint53.py:enumerate_joint`는 iris/sclera/upper-lid의 **이동 조합을 동시에** 전수 생성한다. 각 파츠에 동일한 L1 최대1셀 예산을 주었고, 0예산도 별도로 검사했다. 이 1셀은 이번 진단의 공개된 변형 한계이며 최적 미술값이나 전체 모델 규칙이 아니다.

내부 파츠의 glyph 색·ID·UV provenance·연결 관계는 유지한다. 서로 다른 파츠의 같은 셀 사용을 허용하지 않으며 전체 연결성과 상안검-홍채의 위아래 관계를 검사한다. 실제 source에서 hair/brow/body에 가린 token을 이동으로 살리지 않는다. 목적지에서도 기존 가림 gate를 적용한다. **새로 차지하는 셀**은 4×4 source의 더 가까운 hair/brow/body fragment까지 확인한다.

이동 비용은 `Σ_part ||t_part||²`로 파츠별 정규화했다. 작은 안검을 싸게 희생시키는 픽셀 개수 비용이 아니다. 같은 이동 비용 안에서는 기존 source의 영역/곡선 거리, 상대 파츠 중심 변화, bounds 증가를 비교한다. 이는 미학적으로 학습/검증된 목적함수가 아니라 공개된 진단 비용이다. 현재 후보군은 **파츠별 rigid 이동**이며 자유로운 공유곡선 재설계까지 구현한 것은 아니다.

## 실제 결과

0셀 예산은 충돌 때문에 feasible0. 1셀 예산은125조합 중 logical 최종 gate만 보면3개였으나 source fragment 검사까지 적용하면 **2개**다.

| 후보 | 홍채 | 흰자 | 상안검 | 파츠 이동 비용 | 참조 영역/곡선 오차² | 상대 중심 오차² |
|---|---|---|---|---:|---:|---:|
| A / 기각 | 그대로 | 그대로 | 위1 | 1 | 1.919667 | 2 |
| B / 제한 통과 | 아래1 | 아래1 | 그대로 | 2 | 0.427808 | 2 |
| C / 제한 통과 | 아래1 | 아래1 | 오른쪽1 | 3 | 0.304477 | 4 |

A의 새 목적지 `(222,51)`는 최종 hair/brow winner 지도에서는 비어 보였지만 frame100에 더 앞선 S4 hair4/16·S5 brow2/16, frame101에 hair2/16·brow2/16 표본이 있었다. **A를 채택하지 않았다.** 이 검사는 임의 mesh seam 보호가 아니라 실제 가까운 가림 표본에 근거한다.

B/C는 실제 source 가림을 보존하면서 두 프레임 모두 iris4/상안검1을 출력한다. frame100의 흰자5와 frame101의 흰자6 차이는 기존 source의 앞머리 가림을 유지한 결과다. 원래 숨은 흰자를 빈 곳에 새로 만들지 않았다. 색은 source token의 literal RGB를 직접 대입하며 평균/곱셈/블러를 하지 않는다.

**대가:** iris/sclera 10token을 아래1셀 이동한다. 눈 범위4×3→4×4, 높이+33.3%, 수정하지 않은 반대 눈 대비 iris 높이가+1셀이다. B/C 모두 원래 iris 내부 형태와 연결성은 같지만, 눈높이와 전체 눈매가 바뀐다. 원배율 검수에서도 이 변화가 보인다. C는 참조 곡선 거리 수치가 더 작지만 상대 배치 변화가 더 크다. 이 수치를 근거로 C가 더 예쁘다고 판단하지 않는다.

이번 rigid-part/L1≤1 후보 안에서 추가로 iris 높이 이동0까지 요구하면 feasible0이다. 이는 현재 후보군의 제약 충돌이다. **비강체 공동 배치나 더 완전한 안검 key-form으로도 불가능하다는 뜻은 아니다.**

## 잔상 검수와 합성 한계

초기 직접 overlay는 원래 눈 픽셀을 남기는 오류가 있었다. 그 버전은 `source-gate-ghost-draft`에 **INVALID**로 보존했다. 현재 `compose53.py`는 실제 `eye-visible`의 같은 눈 old feature를 먼저 분리하고, 새 파츠를 대입한다. 비워진 원래 셀의 올바른 skin/background가 저장되지 않은 곳은 **magenta UNKNOWN**으로 표시한다. 주변 피부색 복사/추정 보간을 하지 않는다.

- frame100 미확인 backing: `{missing['100']}`
- frame101 미확인 backing: `{missing['101']}`

합계6 logical sample의 clean underlay가 부족하다. 실제 코드 `EyeFeature348.compute Evaluate`는 win 색 대입 전 Base/Backing 중 유효하고 가까운 `bc/bm`을 고르지만, 저장47에는 그 clean backing RGBA가 없다. `final-native`, `head-colour`, `eye-output`은 이미 기존 눈 색이 포함되어 대신 쓸 수 없다. 현재 PNG의 magenta는 실패를 숨기는 색이 아니라 **부분 합성의 데이터 공백**이다. `candidate*-isolated` PNG에서는 기존 얼굴 잔상 없이 할당된 파츠만 볼 수 있다.

현재 부분 합성의 old-eye mask에는 기존 분류가 만든 lower-like feature6도 포함되어 있다. 이를 source native 안검의 참 라벨로 승인하지 않았으며, 전체 하안검 디자인 복원/보존이 검증됐다고 하지 않는다.

## 검증·보존

{s['assertions']} assertion: source/이전49·52 불변, 0예산 실패/1예산 실제 해, 파츠 순회 순서 독립, 모든 source token 유지, 파츠 내부 모양/팔레트 불변, 가림된 source 복구 금지, 새 가림 침범 금지, vacated pixel 잔상 제거/추정 피부 금지, 수정 범위 밖0변경, P 직접 대입. 2프레임×17×17=578 공통 위상 배치에서 intrinsic glyph1종이다. 실제 가림 변화를 합성한 시간 검증은 아니다.

저장5pose는 명시 blink/state 및 이 native glyph의 완전한 외부 가림 입력이 등록되지 않아 전체 눈 출력을 하지 않았다. 이 거절은 `OLD_POSE_BOUNDARIES53.json`에 있다. 임의 열린 눈/2px eye를 그 pose의 정답으로 생성하지 않았다.

현재 `review-comparison` PNG를 원배율·12배 nearest로 직접 열어 확인했다. B/C의 iris 클러스터는 단일 연결이며 내부 충돌이 없지만, 낮아진 눈과 미확인 backing이 보인다. 미술 합격 아님. 단독 native1셀만으로 상안검 곡률을 보존했다는 주장도 하지 않는다.

제품12파일과49/52 해시 차이0. Unity/제품 수정/새 캡처/CUA/UI/reset/GC/앱 종료/저장/commit0. 현재 Editor scene/dirty는 조회하지 않아 미확인이다. 도구 거부/실행 대기는 없고 실행 중 명령도 없다.

## 다음에 필요한 최소 자료

완전한 얼굴 합성을 확인하려면 새 동일입력 재현에서 위와 같은 vacated-cell의 **win 대입 전 선택된 Base/Backing RGBA+owner/depth**만 기록하면 된다. 과거100/101의 sourceId에 새 프레임을 섞지 않는다. clean underlay가 확보되기 전 완전한 최종 이미지를 주장하지 않는다. 새 Unity 접근은 현재 금지되어 이번에는 시도하지 않았다.

재현(새 Unity 실행 없음): `run53.py` → `review53.py` → `finalize53.py`. 기존 frozen49/51/52와53의 보존된 source fixture를 읽는다. archive 생성 스크립트는 다시 실행하지 않는다.
'''
(R/'REPORT_KO.md').write_text(report,encoding='utf8')
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>53 눈 공동 셀 배치 후보</title><style>
body{background:#171b22;color:#e3e7ed;font:16px/1.65 system-ui;margin:28px}main{max-width:1300px}a{color:#9fcfff}b{color:#ffd484}.note{padding:16px;background:#29313d}img{image-rendering:pixelated}figure{margin:16px 0}.scroll{overflow:auto}table{border-collapse:collapse}td,th{padding:8px 16px;border:1px solid #697181}.magenta{color:#fa00c8}.small{font-size:14px;color:#bec7d1}</style><main>
<h1>53 전체 눈의 공동 셀 배치: 제한 후보</h1><p class="note"><b>내부 충돌 해결 가능</b>을 실제 파츠 출력으로 확인했습니다. 제품/GPU 미적용, 미술 미채택. 완전한 얼굴 합성에 필요한 배경색6표본이 없어 <span class="magenta">magenta=UNKNOWN</span>입니다.</p>
<p>단순 iris-first/lid-first 대신 파츠 이동 조합125개를 함께 검사했습니다. 0셀 이동은 해0, 최대1셀 이동+실제 가림 검사는 해2개입니다. 홍채4/흰자6은 이번 기존 Template의 입력 수이며 전역 고정 크기가 아닙니다.</p>
<p><a href="REPORT_KO.md">정확한 식·수치·한계</a> · <a href="joint53.py">공동 할당 코드</a> · <a href="compose53.py">잔상 없는 부분 합성</a> · <a href="SUMMARY.json">요약 수치</a></p>
<table><tr><th>후보</th><th>이동</th><th>검수</th></tr><tr><td>A</td><td>안검 위1, 나머지 유지</td><td>새 셀에 실제 hair/brow source가 앞서 있어 기각</td></tr><tr><td>B</td><td>홍채·흰자 아래1, 안검 유지</td><td>내부 충돌·가림 검사 통과. 오른눈이1셀 낮아짐</td></tr><tr><td>C</td><td>홍채·흰자 아래1, 안검 오른쪽1</td><td>동일 조건 통과. 상대 배치 변화가 더 큼</td></tr></table>
<h2>같은 저장 프레임 비교</h2><p>왼쪽100 / 오른쪽101. 행: ①실제 저장 최종 ②iris 우선(안검 소실) ③lid 우선(홍채 소실) ④A 기각 반례 ⑤B ⑥C.</p>
<p>2~6행은 저장 배경과 별도 파츠의 <b>부분 합성</b>입니다. 원래 눈을 그대로 남긴 잔상을 제거했고, 비워진 자리의 미확인 배경은 magenta로 표시했습니다. 피부 추정값이나 선택 팔레트색이 아닙니다.</p>
<figure><figcaption>저장 출력 크기(논리셀2×2)</figcaption><img src="review-comparison-1x.png" width="64" height="96" alt="partial composites at original saved size"></figure>
<figure class="scroll"><figcaption>정수12배 nearest</figcaption><img src="review-comparison-12x.png" width="768" height="1152" alt="six rows two frames, magenta missing underlay"></figure>
<h2>frame101 할당 파츠만 보기</h2><p>얼굴의 기존 눈 색을 섞지 않은 실제 candidate 레이어입니다. B/C는 모든 token과 원래 팔레트색을 직접 출력합니다. 투명 부분은 새 source로 메우지 않았습니다.</p>
<figure><figcaption>B 원배율</figcaption><img src="frame101-candidateB-isolated-1x.png" width="32" height="16" alt="candidate B isolated original size"></figure>
<figure class="scroll"><figcaption>B / C 정수12배</figcaption><img src="frame101-candidateB-isolated-12x.png" width="384" height="192" alt="B isolated"><img src="frame101-candidateC-isolated-12x.png" width="384" height="192" alt="C isolated"></figure>
<p class="note">B/C는 eye bounds4×3→4×4, 높이+33.3%, 반대 눈 대비 iris 높이+1셀입니다. 개수·연결성·곡선 거리 수치로 아름다움을 보증하지 않습니다. 회전/blink/새 조명/실제 GPU 시간 안정성은 미검증입니다.</p>
<h2>근거</h2><ul>'''
links=['JOINT_ENUMERATION53.json','READABILITY_AND_SOURCE_ERROR53.json','FRAME_RESULTS53.json','INPUT_GLYPHS53.json',
    'MISSING_UNDERLAY53.json','BOUNDED_COUNTEREXAMPLE53.json','OUTPUT_PALETTE53.json','TESTS.json','PRESERVATION53.json','OLD_POSE_BOUNDARIES53.json']
html+=''.join('<li><a href="'+escape(p)+'">'+escape(p)+'</a></li>'for p in links)
html+='''</ul><p class="small">logical-gate-only / source-gate-ghost-draft は初期失敗記録です。後者は元の目の残像が残るためINVALIDです。現在の結果はこのページの部分合成と独立レイヤーだけです。</p></main></html>'''.replace('logical-gate-only / source-gate-ghost-draft は初期失敗記録です。後者は元の目の残像が残るためINVALIDです。現在の結果はこのページの部分合成と独立レイヤーだけです。','logical-gate-only / source-gate-ghost-draft는 초기 실패 기록입니다. 후자는 기존 눈의 잔상이 남아 INVALID입니다. 현재 결과는 이 페이지의 부분 합성과 독립 레이어입니다.')
(R/'INDEX.html').write_text(html,encoding='utf8')
for name in re.findall(r'(?:href|src)="([^"]+)"',html):assert(R/name).is_file(),name
assert Image.open(R/'review-comparison-1x.png').size==(64,96)
assert Image.open(R/'review-comparison-12x.png').size==(768,1152)
dump('RESUME.json',dict(status='bounded joint allocation implemented; internal conflict solved for known3parts; art and clean-face composite incomplete',
    entry='INDEX.html',pendingProcess=None,newUnityCalls=0,newCommit=False,
    currentEditorState='unknown/not queried',missingCleanUnderlay=missing,
    doNotTreatAsFinal=['logical-gate-only','source-gate-ghost-draft'],
    runOrder=['run53.py','review53.py','finalize53.py'],
    nextNeed='same-frame clean backing6samples and registered whole lower/upper-lid pixel state; do not infer unknown blink'))
files=[]
for p in sorted(R.rglob('*')):
    if p.is_file()and p.name!='OUTPUT_MANIFEST.json':files.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
dump('OUTPUT_MANIFEST.json',dict(files=files,linksChecked=True,localImagesViewed=True,UIControlUsed=False,
    currentCompositeIsPartial=True,product12Changes=0,previous49And52Changes=0))
print(json.dumps(dict(entry=str(R/'INDEX.html'),files=len(files),feasibleSourceChecked=2,
    underlaySamplesMissing=6,product12Changes=0,previous49And52Changes=0,newUnityCalls=0,newCommit=False),ensure_ascii=False,indent=2))
