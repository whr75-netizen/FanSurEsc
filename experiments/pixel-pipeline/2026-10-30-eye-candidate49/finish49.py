"""Read completed tests, publish local report/diffs; no Unity or product writes."""
from pathlib import Path
import hashlib,json,html,shutil
R=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
s=load(R/'SUMMARY.json');rows=load(R/'RESULTS.json')
p=R.parent/'continuous47-counts/candidate'
(R/'patches').mkdir(exist_ok=True)
for n in ('EyeFeature348_visibility_gate47.compute','PROPOSED_ONLY.diff','STATIC_AND_COUNTERFACTUAL_VERIFIED.json'):
    shutil.copyfile(p/n,R/'patches'/n)

table='\n'.join(f"|{r['frame']}|{len(r['eyes']['1']['actualVisibleIris'])}/{len(r['eyes']['2']['actualVisibleIris'])}|{len(r['eyes']['1']['gateOnly'])}/{len(r['eyes']['2']['gateOnly'])}|{len(r['eyes']['1']['jointAfterKnownFinalGate'])}/{len(r['eyes']['2']['jointAfterKnownFinalGate'])}|{sum(c['role']==4 and c['visible']for c in r['cells'])}/12|"for r in rows)
report=f'''# 눈 후보49 — 가림 자격과 상태별 공동 배치의 분리 검사

기준 커밋은1835f10,6c31438. 새 실제 프레임은 찍지 않았다. source sequence `{s['sequenceId']}`의 동결된96–101 입력을 재사용했다. 메모리 감사48과 독립인 CPU 실험이며 제품·Unity·31·34·Desktop 수정 없음.

## 실제로 만든 것

`candidate49.py`는 source/style key+명시 state에 묶인 원본 셀 ID/role/색을 함께 이동한다. 기존Template216의 실제20셀(홍채8/흰자12)을 fixture로 사용한다. iris 셀은S2, sclera 셀은S1의 동일eyeID 기하 표본만 사용하며 skin을 홍채 색 공급자로 대체하지 않는다. 현재 찌그러진 GPU raster를 reference shape로 복제하지 않았다.

연산은 `headMatrix×modelEye.centre → 기존 camera ray basis 역투영 → 두 중심의 공통 anchor → floor(anchor-referenceAnchor+.5) 한 번 → 모든 template cell 공동 이동 → 해당 family의 원본 source 표본/외부 가림 → 기존 final hair/brow/body 깊이 gate → literal template RGBA8`다. 입력은 실제 저장 projection/transform이며 임의 camera/scale/2픽셀 규칙이 없다. 미래 런타임은 같은 anchor를 기존 `full.Project`로 계산할 수 있어 새GPU readback이 필요하지 않다.

등록된 입력은 **fully-open translation probe**다. 이 상태의 template를 여섯 미세 보행 pose에 차용한 것이며 pose별 올바른 미술 shape를 승인한 것은 아니다. blink50/100, 바뀐style, 명시되지 않은state는 열린 눈으로 대체하지 않는다. 회전/표정 범위를 자동 분류하는 코드가 완성됐다고 주장하지 않는다.

## 동결 GPU 원인 재현과 조합

전체1536packet×12성분을 재계산한 최대오차 `{s['maxFullPacketError']}`는47과 동일하다. 가림 gate만 추가하면12 eye-frame 쌍 중frame100/ID1만 바뀐다. budget과원면적을 유지하고, 가려진 후보를 다른 위치에서 다시 채우는 후처리를 넣지 않았다. frame101의 대각선은 gate만으로 남는다.

|frame|실제 가시 홍채 ID1/2|47gate 할당 ID1/2|49cache+source+known final 가시 ID1/2|49 흰자 가시/참고|
|---|---:|---:|---:|---:|
{table}

47gate열은 iris 할당 셀 진단이며 완전한 후보RGBA 렌더가 아니다.49열은 **독립 template 레이어 출력**이다. 전체 얼굴의 후보최종합성을 복원한 것이 아니다.

공동 배치는6×33×33={s['purePhasePlacements']}개 x/y위상에서 내부 상대배치1종, source ID/role/색 그대로다. generic adapter에서 원본 셀 하나를 뺀 입력은 실제로 한 셀 적게 배치되며 최소 개수를 보충하지 않는다. 각 눈의4셀은 현재Template216에서 나온 값이지 모든 눈을4셀로 만드는 하드코딩이 아니다. 현재47 면적 budget2와 reference4의 차이는 **차용한 디자인 footprint 차이**이며 픽셀 개수 증가가 디자인 성공의 근거는 아니다.

ID2/frame96의reference `(214,78)`은현위치 `(216,52)`에서앞쪽hair에가려3셀이다. 대표깊이13.71040535,raw S2 표본12개 중외부가림적용후weight합5.00404였다. 실제머리를지우거나대칭4셀로보충하지않았다. 나머지11개eye-frame의iris4셀은해당원본S2표면지지가있다. 다른family색의유입은없다.

## 발견한 조합 회귀 — 미채택

1. **상안검의 간접 의존:** `NativeLineAllocated19`가 `IrisAllocated19`를 후보제외조건에 사용한다. cache의occupancy로바꾸면frame101/ID1의line선택이 `(222,52)`에서 `(221,53)`으로 바뀐다(집합의2셀차이). gate-only는이line집합을바꾸지않는다. 이는추정이아니라동일packet에서함수를재생한결과다. 커진iris와의충돌을피하려고upper-line을새위치로보내는rank경로가남아있다.
2. **완전한 눈 key form이 아님:** Template216은upper-line role6가없다. planned sclera12개중현재source로지지되어가시인것은4,4,4,4,4,5개다. 나머지를강제로그리면실제skin/lid/가림을침범할수있다. 이누락을추정색이나min셀로채우지않았다. 남은흰자일부는실제저장upper/lower-lid 셀과겹친다(좌표별RESULTS). frame101의iris `(222,52)`도기존upper-line과겹친다.
   - 이흰자손실을모두정당한가림이라고판정하지않는다. 예를들어frame96의빠진흰자7셀은S1원본표본이1~12개실제로있지만현재S0/S3/S4가림처리후weight0이됐다. 특히아래쪽3셀은S0 skin 때문에0이다.49도여전히목적지셀의raw지원/skin가림에의존하므로사용자가요구한특징레이어확대와실제eyelid가림을구별하는계약을완성하지못했다. S0전체를무조건보호하는것도,무조건무시하는것도정답이라고하지않는다. source-cell의고정UV/triangle/barybinding은이번adapter에구현하지않았으며동일eye/material family와동일key-cell ID까지만연결했다.
3. 따라서49가순수위상shape를보존한다는결과를**실제눈전체해결**로올릴수없다. full20-cell template를그대로실제품에합치는것은현재회귀검사에서기각한다. gate47은별도좁은후보다. native upper-line/흰자/홍채를공동배치할등록key form이없는데단독iris4셀을항상우선하면또경계를지울수있다.

**미술 성공으로 보고하지 않는다.** 실제확대에서현재모델의단단한2셀눈과template의더큰2×2홍채모양차이가분명하다.49의분리레이어는흰자위아래가여러곳빠져있고completeeye가아니다. 상안검이없는template에착시로잘보이는색을입히거나전체얼굴위에덧칠해성공이미지를만들지않았다.

## 검사 범위

- test조건13500여개는일반/위상/소스동결반복검사수이며미감보증수치가아니다.
- 동결입력SHA256,packet재현,세포별ID/색/family,순회독립,최대half-cell snap 오차,source/style/lid 무효화,완전앞쪽hair합성반례,gate의제거전용(no refill),NativeLine간접회귀를검사했다.
- 원래2×표시크기 PNG와nearest8×를실제로열었다. RGBA원본을보존하고checker는비교판에서만사용한다. `comparison-1x.png` 각행은①실제GPU원본②실제iris ID진단③gate47할당진단④template공동배치(가림전)⑤source/known final가림후분리레이어다.
- 실제후보GPU컴파일/최종합성,새연속프레임,회전/blink디자인,phase변화때실제hair래스터동시변화는미검증. 저장가림맵을가짜로subpixel이동시키지않았다.
- 소스파일12개SHA는현재47기준과동일. 실행중observer/Unity호출없음. 현재dirty25를새조회한것이아니며변경명령자체를보내지않았다.

## 실행

`python -B verify49.py` (기존NumPy/Pillow 필요). runtime종속코드를import하지않고동결47/42함수AST만불러온다. `prepare_fixture.py`와`finish49.py`는증거준비/문서생성도구이며제품적용도구가아니다. `patches/PROPOSED_ONLY.diff`는원래47후보그대로이며미import/미GPU컴파일이다.49공동배치는Python의실제셀배치코드이며아직GPU적용diff로둔갑시키지않았다.

정확한최소제품변경대상/허가가필요한검증은`INTEGRATION_PLAN_KO.md`에분리한다. full49가적용가능하다고보고하지않는다.
'''
(R/'REPORT_KO.md').write_text(report,encoding='utf8')
plan='''# 제한 GPU 통합 준비와 미채택 경계

## 1. 먼저 검증 가능한 gate47 — 제품 영구 적용 전

대상: `Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeFeature348.compute`.
정확 함수: `CountPacket19`에서현재최종선택과동일한nearest-centre iris 대표깊이를packet.uv.z에추가하고,기존final hair/brow/body gate통과를uv.w에기록한다. `IrisAllocated19`는면적을그대로합산하되최종가림실패셀을자격/순위에서제외한다. `BeforeIris19`의기존비용/UV/tie식과Classify/Own/ChooseLayers/Evaluate/최종합성은바꾸지않는다.

준비물: `patches/EyeFeature348_visibility_gate47.compute` 전체후보및`PROPOSED_ONLY.diff`.
상태: CPU전체packet/allocator/line간접검사완료. **GPU컴파일·실제RGBA검증미완,제품반영불가상태**.
추가검증승인범위: 임시compute자산1개import,기존EyeFeature348.candidateShader의runtime참조만A/B,현재씬저장없이임시Play에서동일open포즈최소프레임,실패셀과양눈/흰자/upper/lower-lid 버퍼확인,메모리카운터/자원회수,정상Play종료와참조·dirty·파일hash복원. 제품compute원본영구교체는이승인에포함하지않는다. 현재추가캡처중단상태이므로실행하지않았다.
리스크: CountPacket의uv.zw를다른코드가읽는지전체소스추가정적확인필요;NativeLineAllocated의간접호출;同一pixelの最終遮蔽(논리셀)와4×coverage의차이;GPU부동소수/대표tie재현. gate가실제hair가림을없애거나원래면적을최소셀수로늘리면실패.

## 2. shape/cache49 — 현재 그대로 통합하면 안 됨

정확 최소후속파일3개는아래다. 이목록은적용승인범위제안이며완료된GPUdiff라는뜻이아니다.

1. `EyeBoundaryRestore348/Runtime/EyeFeature348.cs`의Initialise/Prepare/OnDisable: 모델topology+style+TemplateRole/RGBA+명시pose/lid상태로source key form을등록. 기존template의role/cell ID/상대좌표/색출처를한번추출. 매프레임기존full.Project(headMatrix*modelEye.centre)의공통anchor만보내며새GPU readback/화면RGB캐시를추가하지않는다. 등록되지않은blink/회전은열린눈으로대체하지않고trial을중단한다. 현재완료된것은Python adapter뿐이며자동pose-state classifier나모든상태template는없다.
2. `HeadLocal367/Runtime/EyeRenderer367.cs`의Dispatch:같은CountFeatures/Evaluate pass에등록된state/fingerprint와공통translation/reference좌표를전달한다. 순서변경이나새RT/pass는필요없다. 기존16subsample source/최종가림을계속쓴다.
3. `EyeBoundaryRestore348/Shaders/EyeFeature348.compute`의IrisAllocated19/NativeLineAllocated19/ChooseLayers19/Evaluate/Own:rank가irisshape를매프레임다시만드는대신등록feature-cell ID에서role/footprint/원래template texel을선택한다. 같은feature source기하에대표표본을연결하고외부가림을적용한다. pigment는Own의nearest재매핑대신등록된source texel을직접참조한다. **NativeLineAllocated19의iris-occupancy 종속과흰자/안검충돌을함께해결해야한다.** upper-line을기존잘못된raster로그대로캐시하거나skin보다항상앞에놓는식으로해결하면안된다.

현재필수미완입력은현재open상태에서iris/sclera/upper-line을함께정의한키폼의등록근거다. 기존Template216에는role6가없고그흰자12셀은현재6pose의S1지지와맞지않는다. 원래326의상하경계있는reference 또는이미있는native upper-arc/state 자료와정확한좌표등록을먼저연결해야한다. 눈모양을새로창작하거나현재찌그러진최종raster를자동승인하지않는다.
또한sourceUV/triangle/bary를cachecell에고정바인딩하는부분과일반face-skin 위의특징레이어허용범위/실제lid가림의구분이필요하다. 현재Pythonadapter는destination의S1/S2를다시찾는단계가남아있다. “cache가있으니shape손실문제가전부해결됐다”라고보고하지않는다. 앞선흰자손실을전부실제가림으로승인하는것도금지한다.

이부분은GPU실험승인만받는다고디자인/등록공백이해소되지않는다. 현재full49를제품에바꿔달라고요청하면안된다. gate47의좁은검증과별개로남긴다. 수동key form선택이실제로필요하다면원본reference와구체후보를먼저보여승인받는다.

## 3. 테스트/복원 순서

추가승인이올경우에도①현재상태/파일hash/dirty→②작은컴파일→③한고정frame/기존반례→④필요최소phase변화→⑤정상Play종료와반납을순서대로수행한다. 이전메모리증가소유자가미확정이고최근읽기command가timeout이므로현재연결의읽기응답부터확인해야한다. GC/Unload/강제clean/재시작/씬저장/대량loop는포함하지않는다.
원복은RT수뿐아니라Allocated/Reserved/MonoUsed/MonoHeap과동일PIDのWorkingSet/PrivateCommitを같은시점에남긴다. 증가하면추가렌더를멈추고소유분석으로넘긴다. 47이frame100을고쳐도frame101대각shape가남으므로전체눈해결이라하지않는다.
'''.replace('同一pixelの最終遮蔽','동일 pixel의 최종 가림').replace('同一pixel','동일 pixel').replace('同一PIDの','동일 PID의').replace('동일PIDの','동일 PID의').replace('同じ','같은').replace('WorkingSet/PrivateCommitを','WorkingSet/PrivateCommit을')
(R/'INTEGRATION_PLAN_KO.md').write_text(plan,encoding='utf8')
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>눈 후보49 — 제품 미적용</title><style>body{background:#181c24;color:#e8edf5;font:16px/1.7 system-ui;max-width:1250px;margin:auto;padding:24px}a{color:#9ccfff}img{image-rendering:pixelated;max-width:100%}.warning{background:#4c3529;padding:16px}figure{margin:24px 0}figcaption{margin-top:8px}code{background:#262c37}</style><h1>눈 후보49: 가림 / 공동 배치 / 조합 회귀</h1><p class="warning">새 Unity 렌더가 아닙니다. 실제47의6프레임과 원본Template216을 사용한 오프라인 레이어 시험입니다. 공동 배치는 순수위상 형태를 보존하지만 안검/흰자 충돌이 발견돼 제품 미채택입니다.</p><p><a href="REPORT_KO.md">결과·실패 근거</a> · <a href="INTEGRATION_PLAN_KO.md">정확한 통합 대상과 승인 범위</a> · <a href="SUMMARY.json">집계</a> · <a href="RESULTS.json">셀별 역할·지지·가림·line 회귀</a> · <a href="candidate49.py">실제 배치 코드</a> · <a href="verify49.py">재현 검사</a></p><p>열=frame96..101. 행=①실제 최종GPU 눈crop ②실제iris ID 진단색 ③gate47 할당 진단색 ④Template216 공동배치, 가림 전 ⑤동일cache의source/known final가림후 독립RGBA레이어. ②③은실제색아님. ④⑤를완성된얼굴합성으로보면안됩니다.</p><figure><img src="comparison-1x.png"><figcaption>원래 표시크기: 논리셀당2×2화면픽셀. checker는투명영역표시입니다.</figcaption></figure><figure><img src="comparison-8x.png"><figcaption>동일PNG의nearest 정수8배. 최종후보얼굴RGBA는복원하지않았습니다.</figcaption></figure><p>가림만고치면frame100만바뀌고frame101대각은남습니다. 공동cache에서는실제앞쪽hair에가린셀을없애며인위적대칭/최소셀보충이없습니다. 반면상안검/흰자전체key form은부족해추가통합을보류했습니다. 단순검사수·셀수증가를미감통과로쓰지않습니다.</p></html>'''
(R/'INDEX.html').write_text(page,encoding='utf8')
status=dict(offlineCompleted=True,fullJointCandidateAccepted=False,reason='confirmed native-line dependency and missing registered sclera/lid key form',
 gate47ReadyForLimitedGPUValidationOnly=True,productReady=False,newUnityCalls=0,productFilesModified=0,desktopModified=False,
 localCommitPrepared=True,sourceCommits=['1835f10','6c31438'])
(R/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(status,ensure_ascii=False))
