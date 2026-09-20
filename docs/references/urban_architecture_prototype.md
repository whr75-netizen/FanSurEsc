# 도심 건축 프로토타입 — 용도·평면도·층 연결

## 현재 읽기 경로

- [A28 현재 결정](#a28-현재-결정): 이번 상가별 평면·기본 설비·서비스 출입 작업.
- [A28 계산·검사 계약](#a28-계산검사-계약): 치수와 실패 귀속, 현재 확인 범위.
- [A27 승인된 기준과 이력](#a27-승인된-기준과-이력): 보존할 경찰·주거·계단과 이전 실제 관측. 아래 A27의 당시 미완료 항목을 A28 현재 미구현으로 해석하지 않는다.

## A28 현재 결정

상태: **상가 3형 평면·설비 구현, 평면 조합 36/36 및 대표 3곳의 Play Mode 호출 확인. 사용자 외형 판단 대기**. A27 이후 사용자가 “건물마다 설계도도 다를거고 크기도다를거고…상가기준으로먼저” 작업을 요청했으므로 상가의 방과 기본 설비를 확장한다. 기존 경찰·주거의 승인 구조와 도로·주차장·Player·카메라는 유지한다.

| 프로그램 | 서로 다른 공간 구조 | 크기와 설비 계약 |
|---|---|---|
| 식료품점 `Supermarket` | 넓은 판매장 → 후방 횡방향 서비스 복도 → 창고·직원실·WC; 납품문은 창고에 직접 연결 | 판매·재고 선반은 기존 크기. 계산대·WC 설비를 별도 배치. 대표 A27 마트 필지 선택은 유지 |
| 카페 `Cafe` | 전면 접객실과 측면 주문/서비스 영역 → 후방 복도 → 주방·식재료 창고·직원실·WC | 접객/카운터 구역을 나누며 테이블·의자, 주문대, 조리 싱크/작업대 배치. 고객 WC 접근에 주방 경유 불필요 |
| 소매점 `RetailShop` | 전면 판매장 → 종방향 서비스 통로; 통로 왼쪽 재고실, 오른쪽 직원실·WC | 다른 두 유형의 후방 횡복도와 연결 구조가 다름. 납품문은 후방 재고실에 연결 |

기존 OBB 건물의 `폭 {12,14,16,18}m × 깊이 {10,12,14}m`를 입력으로 쓰며 모두 최소 12×10m부터 계산한다. 기존 대표 마트·경찰·주거의 선택 순서와 14×12m 하한은 유지하고 카페·소매점을 추가 선택한다. 이후 기존 `Retail` 건물에도 footprint와 BuildingIndex로 결정한 상가 유형을 적용한다. 의료 POI는 제외한다. 새 seed 난수나 강제 scale로 크기 차이를 만드는 방식이 아니다. 이 단계의 크기/방 수는 게임 프로토타입 가정이며, 모든 도시나 실제 건축에 적합한 범용 평면도라는 주장이 아니다.

WC·싱크·카운터·카페 테이블/의자는 역할과 물리 치수를 가진 단순 기하 설비이며 기존 재료를 사용한다. 기존 shelf/desk는 원래 크기로 재사용한다. **이 설비가 완성된 픽셀 가구나 사용자 승인 아트라는 뜻은 아니다.** 새 픽셀화·조명·투영 파이프라인은 도입하지 않는다.

### A28 현실 자료와 적용 범위

1. [Peterborough 공개 Seoul Plaza 평면도](https://registers.peterborough.gov.uk/Attachments/EntertainmentLicences/134489/www%20plan.pdf): 판매장181㎡, 계산대13.7㎡, 직원실7.6㎡, 건식창고28.3㎡, 냉장·냉동실·WC·납품 공간을 별도 표기한다. 판매/계산/지원/납품 역할을 분리하는 근거이며 이 면적을 게임 건물에 축소 복제하지 않는다.
2. [Dundee 5 Bank Street 카페 신청 보고서](https://dundeecity.gov.uk/reports/plan_apps/17-00085-FUL.pdf#page=2): 도면 추출 텍스트에 좌석·서비스·식품 준비·WC가 있고 본문은 카페와 상층 주거의 출입 분리를 설명한다. 접객·준비·WC 및 다른 용도 동선의 분리 근거로 사용한다.
3. [Flintshire Gwernaffield 편의점 신청 도면, PDF21쪽](https://committeemeetings.flintshire.gov.uk/documents/s62367/Enc.%201%20for%20059396%20-%20Full%20Application%20-%20Erection%20of%2080%20Dwellings%20Convenience%20Store%20and%20Associated%20De.pdf?LLL=0#page=21): 판매장·창고/사무실·직원 WC·고객 입구·별도 납품 출입구 표기를 확인했다. 소형 상가도 판매실 하나로 끝나지 않는 근거다.
4. [Hillingdon 21 Windsor Street 식당 설계설명서](https://planning.hillingdon.gov.uk/OcellaWeb/viewDocument?file=dv_pl_files%5C19842_APP_2026_51%5CDAS.pdf&module=pl): 전면/중앙 식사 공간, 후면 주방·준비·창고·직원 구역과 후면 서비스 도로의 납품·폐기물 접근을 설명한다. 손님과 지원 구역의 인접 관계를 참고한다.

**자료 확인은 PDF 본문·도면의 추출 텍스트 범위다.** PDF screenshot은 `Cache miss`여서 실제 도면 이미지를 시각 확인하지 못했다. 문 좌우 위치·치수·설비 모양을 읽어 복제했다고 기록하지 않는다. 공개 제출 자료의 승인/시공 여부도 이번 게임 적용 증거와 구분한다. 위 역할 관계를 현재 필지에 맞춘 직교 분할로 저작했고, 건축 법규 인증을 주장하지 않는다.

## A28 계산·검사 계약

원본은 계속 `UrbanFloorPlan`이다. `UrbanCommercialFloorPlans`는 기존 건물 로컬 XZ 미터에서 프로그램별 방 Rect와 partition을 계산한다. `L/R=±W/2∓0.2`, `B/F=±D/2∓0.2`이며 +Z가 정문이다. 일반실 최소 치수2.4m, 서비스 복도1.8m, 실내 문1.6m, 후면 납품문1.8m는 현재 캐릭터 이동을 위한 프로토타입 모듈이다.

- 식료품점: 후방3.2m 지원실 띠 + 앞쪽1.8m 복도 + 나머지 판매장. 직원실/WC 폭은 각각2.8m이고 남는 후방 폭이 창고다.
- 카페: 후방3.2m 지원실 띠 +1.8m 복도. 창고/직원실/WC는 폭2.4m씩, 남는 폭은 주방이다. 전면은 우측3m 서비스 영역과 나머지 접객 영역으로 분리한다.
- 소매점: 후방5.2m 구간에 왼쪽 재고실, 폭1.8m 종방향 통로, 오른쪽 폭3.2m의 직원실/WC를 둔다. 오른쪽 두 실 깊이는 각각2.6m이고 남는 전면이 판매장이다.
- 입구 방은 문자열 이름이 아니라 `EntryPoint=(0,D/2−0.5)`를 포함하는 0층 방으로 찾는다. 후면문은 외벽 `z=−D/2`에서 창고/주방에 직접 연결되며 동일 opening이 메시와 Collider의 원본이다.
- 방 그래프 BFS는 입구부터 모든 방 연결을 검사한다. WC는 주방·창고·직원실을 통과 금지한 별도 BFS에서도 도달해야 한다. 기하 연결 통과는 실제 NavMesh/이동 성공을 대신하지 않는다.
- 가구는 방 안 점유 영역·벽·다른 설비·문 접근 여유를 계산한다. 적합하지 않은 가구를 축소하지 않으며 계획/설비 오류에 귀속한다. 실제 출입구 밖 접근도 마지막 이동 관측에 포함한다.

작업그래프는 `LocalOnly/WorkLoop/urban-commercial28/graph.json`, 상태는 `state.json`, 상세 계약은 `design.md`다. 흐름은 `implementation → observe → check → review`이며 구현 내부의 `필지 선택 → 프로그램 분할 → 문/구조 → 설비 배치`는 각각 계산과 오류 책임을 갖는다. 구현 후 읽기 입력인 design.md에 결과를 기록하여 원 그래프 의존성이 무효화됐고 `no_matching_edge`로 정지했다. 이를 성공으로 바꾸거나 구현/Play를 다시 실행하지 않았다. 같은 `check.py`와 실제 증거만 소비하는 `validation-graph.json`/`validation-state.json`으로 인계해 exit_code=0, errors=[]를 확인했다. 현재 review ticket은 `0eb7337347ac442eaf669f0a4b9787bc`이며 실제 사용자 답변 대기다. 다음부터 고정 설계 입력과 결과 기록을 분리한다. 파일 생성이나 AI 자체 외형 평가는 합격 증거가 아니다.

| 단계 | 현재 확인 범위 | 미확인 / 다음 실패 귀속 |
|---|---|---|
| 평면 계산 | 실제 `plan-matrix.txt`: 3유형 ×4폭 ×3깊이 =36개 `TryValidate` 통과 | 임의 비정형 필지·곡선벽·다층 상가까지 확대하지 않음 |
| 경찰·주거 보존 | A27 저장 plan과 같은 크기 재계산의 방·벽·계단 데이터 일치 | 기존 A27 이동 증거 유지. 새 회귀가 없는 계단 재검증은 하지 않음 |
| 실제 상가 이동/설비 충돌 | 마트5/카페7/소매5 공간 도달, 납품문→외부→정문 복귀, 대표 설비/벽·설비/설비 침투0 | 같은 seed 전체30건물의 실제 이동 검증으로 확대하지 않음 |
| 화면/외형 | 정상 플레이 카메라 PNG와 runtime 평면도 | 구조/설비/배치의 미술 합격은 사용자 판단 대기 |

### A28 결과와 다음 재개

seed1462661998에서 상가30개/8가지 크기가 생성됐다. 대표 마트16×14m, 카페12×10m, 소매점12×12m이며 설계원본은 `floorplans.json`, 도면은 같은 데이터의 `floorplans.png`다. 생성 버전13/atlas checkpoint1009. 나머지 상가에도 같은3유형을 적용하며 각 방/문/설비를 미터 단위로 계산한다. 50개 독립 평면이나 완성 아트를 만들었다는 뜻이 아니다.

`LocalOnly/WorkLoop/urban-commercial28/readback.json` SHA-256 `CFC8FC7A33B514E42A80CC819B3C9CC74C06917056C2C2AC348437036DDDA299`: 대표17공간 도달, 각 납품문 출입/외부 복귀, 충돌/가림 오류0, 같은 Player/Camera, 도심 카메라30°/45°/size5 보존. 실제 키보드 입력 대신 기존 `StepMove`/`CharacterController`를 호출했다. 전체30상가의 plan 유효성 및 배치 누락0을 확인했으나 실제 경로 이동·물리 침투 검사는 대표3곳이다.

초기 관측은 씬 초기화 전 frame2여서 NavMesh sample이 실패했다. `readback-before-arrival.json`을 보존하고, 게임 코드를 덮어고치지 않았다. Unity Editor 실제20프레임 진행으로 기존 arrival/NavMesh/카메라 초기화가 끝난 뒤 `NavigationPathComplete=true`를 읽고 같은 검사를 실행했다. 도구의 동적 어셈블리 reload 오류와 임시 명령 delegate 컴파일 오류는 프로덕션 컴파일 실패와 구분한다.

`EnterableSpriteBuilding.Commercial.cs`는 기존 선반/책상과 기본 변기·세면대·주방 싱크/작업대·주문/계산대·테이블/의자를 배치한다. 문 중심 하나만 피하면 카운터가 실제 문 폭을 침범하는 반례가 있어, partition 전체 문폭×양쪽1.4m 및 납품문 전체1.8m×실내1.9m를 비워 둔다. 방을 늘리거나 물체를 축소하는 임의 보정은 없다.

화면은 `supermarket.png`(정문 Game View), `cafe.png`, `retailshop.png`(실내 기존 gameplay Camera의 URP SingleCameraRequest 렌더, overlay UI 제외)이며 기존 조명/투영/출력크기 그대로다. 비활성 Editor의 ScreenCapture 지연 때문에 뒤 두 장은 같은 카메라의 공식 render request로 저장했다. 카메라 각도·줌·targetTexture 설정은 바꾸지 않았으며 씬 전체를 별도 촬영용 카메라로 다시 구성하지 않았다. GameMapTest Play의 `Tools → Urban Architecture → Inspect Supermarket / Cafe / Retail Shop`에서 같은 Player로 이동할 수 있다. A27 결과/실패/사용자 승인은 유지한다. 후속 주거 세부 설비·다층 상가·창호·완성 픽셀 설비·차량 하역·모든 seed/Recovery·물리 키 입력은 미검증/후속이다. 기존 미커밋 도심 코드와 미추적 자산 의존성을 임의 stage하지 않아 독립 커밋은 하지 않았다.

## A27 승인된 기준과 이력

상태: **v2 구조 구현·대표 Play Mode 호출 확인, 사용자 구조 유지 확정**. 사용자는 “구조 유지, 세부 설비·디자인은 다음 작업”으로 답했다. 현재 계단 위치와 방·복도 배치를 프로토타입 기준으로 유지하며, 완성 외형 승인이나 추가 설비 구현 권한으로 확대하지 않는다. 기존 [도심 인수인계](urban_pipeline_handoff.md)의 단일 실내와 외관뿐인 2층을 실제 방·층 연결로 확장한 결과다. 이 문서의 시험 치수는 최종 디자인 확정값이나 건축 법규 충족 주장이 아니다.

사용자 요구 원문:

> 도심 건축 알고리즘이 많이빡센가? 어떻게해야하지. 판타지 컨셉아트나 현대판타지 도심의 컨셉아트를 먼저만든뒤 그 건물을 하나하나 한50개는 설계해야할텐데 . 생성방식도설계해야하고 생성방식의모듈화 등등 기술적으로먼저 검토하고 설계해야하는데 너가 정리한뒤만들어봐 지금하다만 도심부터. 건물도 그냥 내부만 뻥뚫어놓고 어떤 설계도도없잖아. 2층도없고. 내부도좁고. 주차장이나 마트 경찰서 등등도없고. 방구분없고. 이런것들 찾아서 정리한뒤 프로토타입만 만들어봐

- 결과: 기존 도심의 서로 가까운 대표 필지 네 곳에 마트·2층 경찰서·2층 주거·주차장을 배치하고 실제 입구, 방 분리, 상층 이동을 제공한다.
- 메커니즘: 기존 도로/OBB 필지 → 용도별 공간 프로그램 → 치수 있는 평면도 → 벽/문/층판/계단 → 방 역할별 소품 → 기존 물리/NavMesh/가림 → 실제 Player 관찰.
- 보존: 기존 도로 생성, 0.2m 단차, 카메라, 같은 런타임 Player의 이동/씬 흐름, 기존 픽셀 재료 및 자산. 전체 도시 아트 재생성이나 렌더러 교체를 하지 않는다.
- 제외: 완성 아트 50개 저작, 새로운 전리품/위험/보상 정책, 임의 새 에셋 도입. 기존 3D 외형을 픽셀 완성품으로 승인하는 작업도 아니다.
- 판정: 대표 건물 입구·방·계단 왕복의 Play Mode 호출, NavMesh 연결, 소품 여유 공간, 현재 카메라에서 실제 화면. 물리 키 입력 확인과 구분한다.

대표 건물 필지는 최소 14×12m이며 적합 필지가 없으면 실패로 남긴다. 경찰서는 기존 `Office` 용도의 명시적 건축 프로그램 하위형으로 선택하여 루팅 등 기존 enum/정책을 보존한다. 주차장은 미사용 필지를 예약하고 건물 생성을 생략하는 별도 지면 프로그램이다. 카메라 보존 비교는 기존 `IsometricUrbanView`의 정상 도심 진입 설정이 끝난 뒤를 기준으로 하며, 기지→도심의 기존 자동 설정 차이는 허용한다. 별도 콘셉트 이미지는 아직 생성하지 않는다.

## 기법과 선택 근거

| 후보 파이프라인 | 장점 | 실패조건 | 결정 |
|---|---|---|---|
| 도로 그래프/지역 제약 → 필지 → 건물 | 접도·충돌·경계 제약을 단계별로 처리 | 교차로 분할 누락, 접근 없는 필지, 잔여 폭 부족 | 현재 경로 유지. 내부 문제 때문에 도로를 재작성하지 않음 |
| 필지 → CGA 외관 분할 → 임의 실내 | 층·창문·외벽 반복을 간단히 변형 | 외형과 내부가 분리되어 계단/문/방을 보장하지 않음 | 외관 모듈화의 근거로만 사용 |
| POI 방 그래프 → 확률 모델/최적화 → 평면도 | 공간 용도와 인접성, 다층 관계를 표현 | 데이터 학습·탐색 비용, 기하학적으로 불가능한 요구 | 공간 프로그램 개념 채택. 범용 학습/최적화기는 도입하지 않음 |
| POI 방 그래프 → 직교 분할 템플릿 → 치수 제약 → 실제 구조 | 결정적이고 작으며 실패 부위를 특정 가능 | 면적/문 길이/계단 코어가 부족한 필지 | **이번 채택**. 최소 치수 미달은 후보 거절, 강제 축소 금지 |
| WFC → 방/도시 전체 | 국소 모듈의 인접 패턴에 강함 | 모순, 전역 도달성·필수 POI·계단 연결은 별도 제약 필요 | 주 구조에는 보류. 장식/타일 변형의 후속 후보 |

근거는 알고리즘의 역할을 설명하며, 현재 Unity 통합 성공을 대신하지 않는다. 외부 논문의 학습 데이터·코드·상용 도구를 설치한 것은 아니다.

1. [Parish & Müller, Procedural Modeling of Cities](https://people.eecs.berkeley.edu/~sequin/CS285/PAPERS/Parish_Muller01.pdf): 도로의 전역 목표·지역 제약과 필지/건물 단계 분리. 현재의 road graph·OBB 필지 구조를 유지하는 근거다.
2. [Merrell·Schkufza·Koltun, Computer-Generated Residential Building Layouts](https://www.cs.princeton.edu/courses/archive/spr11/cos598A/pdfs/Merrell10a.pdf): 방 목록·크기·인접 관계의 architectural program을 먼저 만들고 다층 평면도로 구체화한다. 주거 연구이므로 마트/경찰 용도는 프로젝트 프로그램으로 별도 저작한다.
3. [Esri CityEngine 기본 shape grammar](https://doc.arcgis.com/en/cityengine/2024.0/tutorials/tutorial-6-basic-shape-grammar.htm): 건물 면 → 층 → 벽/창문 타일의 반복 분할. 외관 문법만으로 내부를 얻을 수 있다고 해석하지 않는다.
4. [WFC 원저자 저장소](https://github.com/mxgmn/WaveFunctionCollapse): 국소 인접 패턴과 모순 처리의 범위. 필수 POI와 전역 연결성은 별도 계약이어야 한다.
5. [Unity CharacterController](https://docs.unity3d.com/6000.0/Documentation/Manual/class-CharacterController.html): stepOffset·slopeLimit·Move 기반 충돌 이동. 식만 맞는 계단을 실제 이동 성공으로 간주하지 않는다.
6. [Unity NavMeshSurface](https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavMeshSurface.html): 수집 geometry와 agent/voxel 설정이 통로·층 연결 결과에 영향을 준다. 설치된 패키지의 실제 API/설정과 대조한다.

## 원본 표현과 생성 순서

```text
seed + 기존 RoadGraph/OBB 필지 + BuildingProgram
 → 후보 필지/정면 선택
 → StairCore·입구·복도 예약
 → FloorPlan(RoomRect, Opening, FloorIndex, Stair, PropSocket)
 → 공통 경계에서 벽/문 생성 + 계단 구멍을 제외한 층판
 → 별도의 시각 계단/이동 Collider
 → 방 역할별 기존 소품 배치
 → 기존 층별 가림/물리/NavMesh
 → 실제 플레이 관찰 + 사용자 피드백
```

원본은 평면도 데이터다. Mesh/Collider/NavMesh/가림 목록은 파생 결과다. 이름·색상만 다른 빈 건물을 프로그램이 다르다고 세지 않는다. 사후 Scene 오브젝트 이동을 평면도 변경 대신 사용하지 않는다.

| 데이터 | 권위·내용 | 소비자 |
|---|---|---|
| 기존 도시 Layout | seed, 도로, 블록, OBB 중심/크기/정면 | 대표 필지 선택 |
| BuildingProgram | 용도, 필요한 방/인접 관계, 층수, 최소 치수 | 평면도 계산 |
| FloorPlan | 건물 로컬 미터의 방, 벽 경계, 문 구간, 계단 코어, 층 높이 | 구조/충돌/소품/가림 |
| Room/Opening graph | RoomId, 역할, FloorIndex, 연결 양 끝 | 통로 검사, 소품 역할, 미리보기 표식 |
| PropSocket | RoomId, local pose, 점유/사용 여유 공간 | 기존 소품 catalog·배치 |

각 계산은 다음과 같이 귀속한다. `SelectParcel`은 필지 적합성, `PlanRooms`는 방/문/층 관계, `RealizeStructure`는 실제 기하·Collider, `PlaceProps`는 역할/여유 공간을 소유한다. 검사는 마지막 필요한 범위에 모으며 `ROOM_OVERLAP`, `MISSING_DOOR`, `STAIR_HEADROOM`, `NAV_DISCONNECTED`, `PROP_CLEARANCE` 같은 실패를 해당 단계로 돌린다. 전체 도시 재생성은 기본 복구가 아니다.

## 좌표·변환·치수 계약

`입력 필지 → 건물 canonical XZ/FloorIndex → Unity local mesh/Collider → Unity world → 기존 view/clip/screen → 기존 렌더 출력`

| 공간 | 원점/축/단위/상위 |
|---|---|
| 필지 | 기존 Layout의 world XZ 중심, meter, 정면 벡터와 OBB 기저 유지 |
| 건물 canonical | footprint 중심의 1층 기준 높이, +X 오른쪽/+Y 위/+Z 정면, Unity 좌수계, meter, scale=1 |
| 층 | canonical의 XZ와 동일, 높이 `h_f = f·3.4m`, zero-based FloorIndex, 상위=건물 |
| Mesh/Collider | 같은 canonical plan에서 생성, scale 중복 적용 없음. box의 치수 표현용 localScale은 원본 길이이며 전체 건물 왜곡과 구분 |
| world | `p_w = c + Quaternion.Euler(0,yaw,0) * p_local`, degree, yaw 한 번 적용, 상위=기존 도시 root |
| view/clip/screen | 현재 게임 카메라/API 규약 유지. 관찰을 위해 카메라 각도/줌/투영을 바꾸지 않음 |

연속 XZ/yaw는 유지하고 픽셀 표현 때문에 실제 물리 좌표를 snap하지 않는다. 새 UV/픽셀 알고리즘을 추가하지 않으며 기존 atlas/정면 계약을 사용한다. 투영/가림에는 정보 손실이 있으므로 스크린샷 하나를 3D 구조의 전체 증거로 간주하지 않는다.

프로토타입 치수: 복도 2.4m, 문 유효 폭 1.6m, 계단 폭 2.2m, 층고 3.4m, 계단 수평 진행 길이 최소 6m, 뒤 참 1.6m·앞 참 2.4m. 필지에 이를 충족하는 여유가 없으면 다른 필지를 선택한다. 기존 폭·깊이를 억지로 축소하지 않는다.

- 경사 높이 `h(s)=H·clamp(s/L,0,1)`, 경사각 `atan(H/L)`. `H=3.4,L=6`일 때 약 29.54도이며 실제 CharacterController·NavMesh slope 한도 이하이어야 한다.
- 시각 계단의 각 단 높이 `H/n`, 진행 폭 `L/n`; 이동 Collider는 동일 끝점의 연속 경사면이다. 단수 선택이 층 도착 높이를 바꾸지 않는다.
- 상층 층판에서 같은 stair core footprint를 빼고 남은 직사각 영역만 생성한다. 덮은 층판 위에 계단을 삽입하지 않는다.
- 공통 벽은 중복 생성하지 않으며, 문 구간을 제외한 벽과 문 위 lintel은 같은 경계 데이터에서 나온다.
- 방 그래프의 연결은 문 구간이 양쪽 실제 공간에 접할 때만 유효하다. 벽 너머 두 방 중심이 가깝다는 이유로 연결하지 않는다.
- 상층/지붕/벽의 시각 가림은 기존 fader에 층 정보를 더해 처리한다. 렌더 숨김과 Collider 제거를 혼동하지 않는다.

### A27-v2 계단·층 경계 교정 계약

최신 사용자 정정:

> 계단이 접근불가능한곳에 되어있는둥 이상한데 설계도를 차라리 다른데서참고하던지

v1에서 계단의 낮은 시작점이 건물 뒤에 있었고 높은 끝이 앞 로비에 닿았다. 경사 자체의 왕복 가능성과 현관에서 읽히는 접근 동선은 다른 조건이다. **앞 로비 2.4m를 순환 동선의 기준으로 두고 낮은 시작점을 앞 로비에 직접 연결하며, 상층 뒤 참을 중앙복도로 연결하는 직선계단**으로 수정한다.

- 로컬 `Rect.y`는 Unity의 높이가 아니라 canonical Z다. `Start=(Bounds.center.x, Bounds.yMax)`가 앞쪽 낮은 점, `End=(Bounds.center.x, Bounds.yMin)`이 뒤쪽 높은 점이다. `d=normalize(End-Start)`, 아래 참 관측점은 `Start-d·0.65m`, 위 참 관측점은 `End+d·0.65m`로 같은 방향식에서 계산한다. 기존 ±Z 상수로 다시 뒤집지 않는다.
- 도로 밖/현관 → 앞 로비 → 계단 하단 → 상층 뒤 참 → 중앙복도 → 각 방 → 귀환을 실제 이동 경로로 관측한다. 계단 하단에 순간이동한 뒤 왕복만 성공시킨 것은 이 계약의 증거가 아니다.
- 층판 두께 0.2m를 반영하여 하층 벽의 높이를 `floorHeight-0.2m`로 생성하는 수정안을 시험한다. **가설:** 하층 벽 윗면과 상층 보행면의 coplanar NotWalkable 경계가 상층 문을 막을 수 있다. 실제 Collider/NavMesh 관측과 수정 후 경로로 판정하며 현재 원인 확정은 아니다. NavMesh 샘플 허용 반경 확대로 다른 층/벽을 찍어 덮지 않는다.
- 가구가 있을 수 있는 방 중심을 무조건 도착점으로 삼지 않는다. `HasDoor` 방의 WalkAnchor는 문 중심에서 방 중심 방향으로 0.9m 안쪽, 공용 공간은 그 공간 중심을 사용한다. 이 앵커의 보행 가능성과 소품 여유를 함께 확인하며 실패하면 앵커/배치 계약에 귀속한다.

직선계단 동선의 근거는 [San Francisco Planning Department — Trocadero Clubhouse](https://commissions.sfplanning.org/hpcpackets/2021-003608DES.pdf)의 PDF 23쪽(0-based 22), 본문 7쪽 `Interior Description`이다. 직사각형에 가까운 2층 건물의 주출입→전실→계단 홀→직선계단, 상층 계단 끝→복도→개별 방 연결이 명시된다. 이 **동선 유형**을 참고하며 평면도·장식·치수를 복제하지 않는다. 원문도 상층 설명은 도면 근거이고 현장 직접 관찰은 아니라고 구분한다.

비교 자료는 원설계사의 [Mascord 21109](https://houseplans.co/house-plans/21109/)로, 현관→foyer→U자계단을 설명한다. 입구와 계단을 함께 계획하는 근거지만 이번 직선계단의 모양 출처는 아니다. [Avon Project Services의 Burley 주택 도면](https://www.newforestnpa.gov.uk/wp-content/uploads/2026/03/P574-201-Rev-A-Proposed.pdf)에는 entrance hall·상층 landing 및 별도 계단 머리 공간 명세가 있다. 공개 도면의 저작물은 프로젝트 자산으로 복제하지 않는다. 웹 PDF screenshot은 cache miss로 실패하여 도면 이미지를 직접 시각 확인했다고 기록하지 않는다.

## 대표 공간 프로그램

| 프로그램 | 필수 구조 | 방 역할과 소품 |
|---|---|---|
| 마트 | 입구→판매장/계산 구역→창고, 직원 공간, 접근 가능한 입구 | 선반은 판매장/창고, 계산대는 입구에서 판매장으로 이어지는 동선 옆. 출입구를 막지 않음 |
| 경찰서 | 1층 민원/접수·조사·보관, 복도/계단, 2층 사무·휴게 등 구분 | 책상은 접수/사무, 수납은 보관. 보안구역의 게임 정책은 후속이며 임의 잠금/전리품 도입 없음 |
| 주거 | 1층 공용·주방/생활·계단, 2층 침실·욕실 등 분리 | 침대는 침실, 생활 가구는 공용 공간, 통로에는 점유 소품 배치 금지 |
| 주차장 | 도로 접근·차량 통로·주차 칸·보행 연결 | 건물을 없앤 빈 필지가 아니라 별도 지면 프로그램. 차량 모델/운전 시스템 추가는 이번 범위 아님 |

마트/경찰/주거의 세부 방 이름·개수는 실제 구현 평면도에 기록한다. 위 프로그램은 구조 프로토타입이며 현실 시설의 법적·운영상 완전한 설계라는 뜻이 아니다.

## 50개로 확장하는 카탈로그 설계

**10개 공간 프로그램 × 5개 평면도 변형 슬롯 = 50개 설계 ID 구조**를 제안한다. 지금 50개 자산이나 50개 평면도가 완성됐다는 의미가 아니다. 외벽 색만 바꾼 결과를 독립 설계로 세지 않는다.

| 프로그램 계열 | 프로그램에 남길 구역 |
|---|---|
| 식료품 마트 | 판매·계산·창고·직원·하역 |
| 경찰 | 민원·사무·조사·보관·휴게 |
| 단독 주거 | 공용·주방·침실·욕실·보관 |
| 상가주택 | 판매/업무층·별도 주거층·계단 |
| 공동주거 | 공용 접근·반복 세대·설비 |
| 진료/약국 | 접수·대기·진료/조제·보관 |
| 음식점 | 홀·조리·보관·직원 |
| 작업장 | 작업·자재·사무·하역 |
| 사무/행정 | 접수·업무·회의·보관 |
| 주차/서비스 | 진입·통로·주차·보행 |

다섯 슬롯은 소형 전면 진입, 넓은 전면 진입, 코너/측면 진입, 서비스 접근 분리, 복합/증축형 같은 **실제로 다른 공간 조건**으로 관리한다. 모든 프로그램에 같은 변형을 무조건 강제하지 않는다. 각 슬롯에 `programId, variantId, minFootprint, floors, requiredRooms, adjacency, stairCore, doorRules, propRules, artStyleId`를 저장하고 실현 불가능하면 미저작/부적합으로 남긴다.

콘셉트아트는 팔레트·재료·창문/지붕 리듬·현대판타지 장식의 참고로 연결하고 방/출입/층의 원본을 대신하지 않는다. 기존 GDD §14.1 픽셀 목표가 유지된다. 구조가 통과한 뒤 선택한 대표 프로그램의 외관/실내 콘셉트를 사용자와 확인하고 필요한 자산만 추가한다.

## A27 최소 실험·자동 검사 명세

가설: 현재 OBB 지역 좌표와 입구/물리 경로를 유지하면서 프로그램별 평면도와 계단 코어를 추가하면, 빈 실내를 실제 기능 공간으로 나누고 같은 Player가 상층까지 이동할 수 있다. 맞으면 네 프로그램이 실제 생성되고 방·층으로 이동한다. 틀리면 실패 필드의 담당 계산을 수정하며 카메라/전체 도시/아트를 바꿔 덮지 않는다.

| ID | 입력/기대값 | metric·허용 오차 | 실패 귀속 |
|---|---|---|---|
| A27-C01 | canonical 점과 Unity 변환의 일치 | world 거리 ≤ 0.0001m, 회전 determinant/기저 오차 ≤ 0.0001. 도시 규모의 float 계산 오차 경계 | 필지 frame/변환 |
| A27-P01 | room rect·footprint·stair core | 유한값, containment/overlap 오차 ≤ 0.0001m, 0개 위반 | 평면도 |
| A27-P02 | 방/문 graph | 입구 BFS에서 모든 사용 방 도달, 문 양쪽 인접 공간 존재 | 문/연결 계산 |
| A27-S01 | 계단/층판/머리 공간 | 동일 plan 끝점, opening 제외, headroom ≥ 실제 controller.height+skinWidth | 구조 생성 |
| A27-M01 | 같은 실제 Player의 기존 Move 경로 | 건물 밖→현관→로비→계단 왕복→모든 방 WalkAnchor 도달, 누락·이동오류 0. 지지면 도달 오차 ≤ 0.15m | Collider/이동 계약 |
| A27-N01 | 실제 baked NavMesh 경로 | 각 상층 도착점까지 PathComplete, 겹친 다른 층을 sample한 결과 거절 | NavMesh/층 연결 |
| A27-O01 | 방별 prop footprint/use clearance | 벽·문·통로·계단 침투 0, 기하 오차 ≤ 0.0001m | 소품 배치 |
| A27-V01 | 현재 Player 카메라 실제 화면 | 외부/방/상층 요청 단위가 보이는 미리보기. AI 미술 합격 판정 없음 | 가림 또는 사용자 디자인 피드백 |

머리 공간·문 폭은 플레이어 capsule 기준으로 계산한다. 수치 실패를 허용 오차 확대나 시각 fader로 숨기지 않는다. 관절/bind pose/retargeting 검사는 이번 건축 구조에 적용되지 않는다. 기존 UV·카메라·픽셀 알고리즘은 변경하지 않으므로 새 제작 알고리즘처럼 재검증하지 않는다.

실험은 대표 seed 한 개의 네 필지, 경찰/주거의 서로 다른 평면도 계단 각 왕복 한 번이다. Play Mode 호출 확인은 실제 키보드 조작 확인이 아니다. 컴파일·파일 존재만으로 구조/이동/미술 성공을 선언하지 않는다.

## 실행기와 결과 인계

현재 그래프: `LocalOnly/WorkLoop/urban-architecture27/graph-v2.json`, 상태 `state-v2.json`. v1의 `graph.json`·`state.json`은 보존하고 state는 stop한다. `implementation → observe → check → review` 네 작업 단위로 제한한다. 구현 단위 안에서 `SelectParcel → PlanRooms →RealizeStructure → PlaceProps`를 각각 결정적 계산과 실패 책임으로 구현하고, 전 과정을 큰 ai.work 설명과 파일 검사로 대체하지 않는다.

`observe`는 Unity 실제 관측을 `readback.json`과 각 프로그램의 실제 PNG 네 장에 저장한다(설명용 평면도는 선택 추가). `check`의 고정 Python 알고리즘은 필수 필드·프로그램별 방/층·이동/NavMesh·보존·미리보기 파일을 판정한다. 실제 관측이 틀렸다면 이 판정도 틀릴 수 있으므로 원본 도구 출력과 Unity 측정 경로를 함께 보존한다. hash는 의미적 정확성의 증명이 아니다.

### v1 실제 관측과 실패

`LocalOnly/WorkLoop/urban-architecture27/readback-v1.json`에 실제 Unity 관측을 보존했다(SHA-256 `9a4a8004cb4cc8aa6da159358cda3910ab31547f539c31cc04eda3d2af747dcd`). 기존 `readback.json`과 동일 바이트의 복사본이며 v2 결과로 덮어쓰지 않는다.

| 관측 | v1 실제 결과 | 판정 |
|---|---|---|
| 마트 | 3개 방 도달, 이동오류 0 | 제한된 Play Mode 호출 확인 |
| 경찰/주거 계단 | 각각 upReached/downReached/navMeshConnected=true | 경사 왕복 확인. 계단 배치의 사용자 승인 아님 |
| 경찰 상층 | Detective office 경로 `PathPartial`, 전체 12공간 중9 도달 | 미완료. 하층 벽 coplanar 경계/가구와 목표점 겹침은 조사 가설이며 원인 미확정 |
| 주거 상층 | Bedroom 중심 NavMesh sample 실패, 전체12공간 중9 도달 | 미완료. 가구와 겹칠 수 있는 방 중심을 무조건 도착점으로 삼은 앵커 계약 수정 대상 |
| 전체 예외/보존 | compileErrors=0, top-level errors=[], 보존4필드true | 개별 방 이동실패를 상쇄하지 않음 |

v1 판정기는 `movementErrors`와 `roomsReached`를 소비하지 않는 누락이 있었다. 따라서 이 판정기로 기술 합격을 선언할 수 없으며, 실제 v1 기술 통과/미술 승인은 제출하지 않았다. v2는 프로그램별 `roomsReached==roomCount`, `movementErrors==[]`, 계단별 `errors==[]`, 최상위 `errors==[]`를 필수로 소비한다. 주차장을 제외한 세 건물에는 `occlusionErrors==[]`도 필요하다. 사용자 정정과 실제 실패로부터 계약을 강화한 새 버전이며 같은 실패 관측을 성공으로 재분류하지 않는다.

가림의 실제 관측은 지상층 실내에서 상층 renderer/roof 숨김 및 현재층 renderer 유지, 상층 실내에서 상층 renderer 표시/roof 숨김, 실외에서 renderer 복원, 전 과정 Collider 유지로 구분한다. `occlusionErrors`의 누락이나 아직 측정하지 않은 빈 배열은 통과 증거가 아니다. Unity 관측 담당자가 이 상태를 실제로 읽은 뒤에만 실패 목록을 확정한다.

### v2 실제 결과와 인계

대표 seed1462661998의 정상 도심 진입에서 마트3/경찰12/주거12 공간의 WalkAnchor에 도달했고, 두 계단 상승·하강과 모든 방 방문 뒤 현관 밖 복귀를 기존 `PlayerMovement.StepMove`로 관측했다. 공용 홀/복도를 제외하면 경찰·주거는 각6개 기능 방이다. NavMesh 연결·실제 이동·소품/벽 침투·실내 상층/지붕 숨김·실외 renderer 복원·Collider 유지에서 기록된 오류0. 같은 Player/Camera와 도심 카메라(30°,45°,0°)/size5를 보존했다. 최종 Console Error/Exception/Assert0. `readback.json` SHA-256 `29f532140db96ed6b7db7cee237e7c354d1d695009bfccdb5b8183b59b330f24`; 실제 관측 경로는 `Assets/Editor/UrbanArchitecturePrototypeReview.cs`다.

`state-v2.json`의 고정 판정 결과 `passed=true, failures=[]`. `review` ticket `3c3a7c98db0642b996f580609be09396`에 실제 사용자 답변 “구조 유지, 세부 설비·디자인은 다음 작업”을 제출했고 `results.review.output.userFeedback`에 저장됐다. 기존 그래프의 review 후속은 `@blocked`이며 실제 반환은 `action=blocked, reason=no_matching_edge`다. 실행기가 완료 상태가 된 것은 아니다. 기술 관측 통과와 사용자 구조 승인은 별도로 확인됐으며 다음 설비·디자인 작업은 새 요청 범위로 시작한다. 복합 교정 뒤의 동작 증거이며 하층 wall top와 가구 목표점 중 어느 하나만이 모든 v1 오류의 원인이라는 독립 입증은 아니다.

- 실제 평면도: `LocalOnly/WorkLoop/urban-architecture27/floorplans.json` → `Tools/WorldArt/render_urban_floorplans.py` → `floorplans.png`. 그림을 보고 메시를 임의 수정하지 않는다.
- 실제 화면: 같은 폴더의 `supermarket.png`, `police.png`, `residential.png`, `parking.png`. 정상 Game View와 기존 시간/조명 그대로이며 사진을 밝게 가공하지 않았다.
- 접근: GameMapTest Play에서 `Tools → Urban Architecture → Inspect Supermarket / Police Ground / Police Upper / Residence / Parking`. 시작 Player/Camera 복사본을 만들지 않고 같은 Player의 공개 이동 API를 사용한다. 최종 관찰 위치는 경찰서 1층 입구 홀이다.
- 미완료: 새 콘셉트아트·완성 픽셀 외형·50개 개별 건물, 주방/욕실/경찰 특수설비, 상점 하역/차량 진입, 창호·설비·더 다양한 평면도, 전 seed·모든 Recovery/플랫폼·직접 키보드 검증. 실제 주차장은4칸/차량통로6m/보행띠1.5m이며 차량 시스템은 없다.
- 파일 안전: 이전 dirty 코드·미추적 도심 자산에 의존하므로 이 변경만 독립 재현되는 커밋으로 분리할 수 없다. 해당 기존 작업을 임의 stage하지 않고 이번 baseline/graph/관측을 남겼다. 다음 작업은 승인된 구조를 기준으로 세부 설비·디자인을 다루며, 새 요구나 실제 회귀가 없는 한 평면도를 다시 생성하지 않는다.
