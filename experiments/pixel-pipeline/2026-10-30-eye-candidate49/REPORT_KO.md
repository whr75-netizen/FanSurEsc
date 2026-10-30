# 눈 후보49 — 가림 자격과 상태별 공동 배치의 분리 검사

기준 커밋은1835f10,6c31438. 새 실제 프레임은 찍지 않았다. source sequence `counts47-087454994917423fa13c5fe72eceb7f4`의 동결된96–101 입력을 재사용했다. 메모리 감사48과 독립인 CPU 실험이며 제품·Unity·31·34·Desktop 수정 없음.

## 실제로 만든 것

`candidate49.py`는 source/style key+명시 state에 묶인 원본 셀 ID/role/색을 함께 이동한다. 기존Template216의 실제20셀(홍채8/흰자12)을 fixture로 사용한다. iris 셀은S2, sclera 셀은S1의 동일eyeID 기하 표본만 사용하며 skin을 홍채 색 공급자로 대체하지 않는다. 현재 찌그러진 GPU raster를 reference shape로 복제하지 않았다.

연산은 `headMatrix×modelEye.centre → 기존 camera ray basis 역투영 → 두 중심의 공통 anchor → floor(anchor-referenceAnchor+.5) 한 번 → 모든 template cell 공동 이동 → 해당 family의 원본 source 표본/외부 가림 → 기존 final hair/brow/body 깊이 gate → literal template RGBA8`다. 입력은 실제 저장 projection/transform이며 임의 camera/scale/2픽셀 규칙이 없다. 미래 런타임은 같은 anchor를 기존 `full.Project`로 계산할 수 있어 새GPU readback이 필요하지 않다.

등록된 입력은 **fully-open translation probe**다. 이 상태의 template를 여섯 미세 보행 pose에 차용한 것이며 pose별 올바른 미술 shape를 승인한 것은 아니다. blink50/100, 바뀐style, 명시되지 않은state는 열린 눈으로 대체하지 않는다. 회전/표정 범위를 자동 분류하는 코드가 완성됐다고 주장하지 않는다.

## 동결 GPU 원인 재현과 조합

전체1536packet×12성분을 재계산한 최대오차 `5.960464477539063e-08`는47과 동일하다. 가림 gate만 추가하면12 eye-frame 쌍 중frame100/ID1만 바뀐다. budget과원면적을 유지하고, 가려진 후보를 다른 위치에서 다시 채우는 후처리를 넣지 않았다. frame101의 대각선은 gate만으로 남는다.

|frame|실제 가시 홍채 ID1/2|47gate 할당 ID1/2|49cache+source+known final 가시 ID1/2|49 흰자 가시/참고|
|---|---:|---:|---:|---:|
|96|2/2|2/2|4/3|4/12|
|97|2/2|2/2|4/4|4/12|
|98|2/2|2/2|4/4|4/12|
|99|2/2|2/2|4/4|4/12|
|100|1/2|2/2|4/4|4/12|
|101|2/2|2/2|4/4|5/12|

47gate열은 iris 할당 셀 진단이며 완전한 후보RGBA 렌더가 아니다.49열은 **독립 template 레이어 출력**이다. 전체 얼굴의 후보최종합성을 복원한 것이 아니다.

공동 배치는6×33×33=6534개 x/y위상에서 내부 상대배치1종, source ID/role/색 그대로다. generic adapter에서 원본 셀 하나를 뺀 입력은 실제로 한 셀 적게 배치되며 최소 개수를 보충하지 않는다. 각 눈의4셀은 현재Template216에서 나온 값이지 모든 눈을4셀로 만드는 하드코딩이 아니다. 현재47 면적 budget2와 reference4의 차이는 **차용한 디자인 footprint 차이**이며 픽셀 개수 증가가 디자인 성공의 근거는 아니다.

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
