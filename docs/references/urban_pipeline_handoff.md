# 도시 제작 파이프라인 인수인계 — D09 중단 지점

현재 구조 작업은 사용자 재개 요청에 따라 [A27 건축 프로토타입](urban_architecture_prototype.md)으로 진행했다. 기존 도심에 마트·경찰·주거 평면도와 실제 2층·계단, 별도 주차 필지를 연결했다. 아래 D09 중단 기록은 과거 경위를 보존한 것이며 A27의 현재 방/층 구현 여부를 덮지 않는다. 픽셀 완성 외형이나 50종 건물 제작은 승인·완료되지 않았다.

최신 정정(2026-09-20): 사용자가 기존 3D의 깨끗한 픽셀 표현 시험과 고정/유한 방향 카메라를 허용했다. [맵 연구 D10](isometric_urban_map_pipeline.md)의 오브젝트별 RGBA/depth 캐시·미리보기까지 실행했고 사용자 외형 판정 대기다. 이 허용은 기존 D09 디자인 승인이나 전체화면 모자이크 채택이 아니다. N01의 표현 경로가 D10으로 진행 중이며 도시 전체 깊이/실내/조명 통합은 아직 없다.

갱신: 2026-09-14. **사용자 요청으로 추가 구현·생성을 중단했다. D09는 픽셀 표현 요구에서 벗어난 3D 시험 구현이다.** 다음 작업은 아래 N01부터 시작한다. D09 기술 통과를 요청 달성이나 디자인 승인으로 해석하지 않는다.

비용·모델·웹 GPT 연동 및 Blender 제작 방식의 후속 조사는 [AI 작업 비용·요구 이탈 조사](ai_workflow_cost_research.md)를 참조한다. 운영안은 제안이며 모델 설정·게임 구현을 변경한 기록이 아니다.

## 1. 첫 작업자가 알아야 할 정정

- 사용자는 PixelLab의 구독 생성량 사용을 허용했고 정사각 원본 타일을 선호했다. ‘3D처럼 보이는 현재 결과’와 제작 방식을 질문했다.
- D09는 **PixelLab 평면 픽셀 재질 → Blender/Unity의 실제 3D 형상 → Unity 렌더**다. 완성된 건물·가구 픽셀 스프라이트를 PixelLab에서 생성한 결과가 아니다.
- ‘3D로 디자인한 뒤 자동으로 픽셀 이미지로 교체’하는 단계는 **구현돼 있지 않다**. PixelLab 재질만 입혀도 원하는 픽셀아트 외형이 된다는 보장도 없다.
- 자유 yaw/pitch·높이·물리 일치를 이유로 담당 AI가 이 경로를 선택했다. 사용자가 ‘픽셀 목표를 무시하고 스스로3D가범용적이라판단한것인가’라고 정정했고 담당AI는 그 요구대체를 인정했다. **설명만 부족한 문제가 아니라 픽셀 목표 충족 없이 구현 목표를 바꾼 문제다.** 이 경로를 계속 확대하지 않는다.
- 사용자 지적대로 방향·실내 공간의 역할 분리 등은 남아 있다. 전체 구성을 완료했다고 보고하지 않는다.
- 작업 그래프에도 결함이 있었다. 기술 gate가 좌표·충돌·재현·3D소품 존재를 검사했지만 **요청된 최종 픽셀 출력**을 제작 경로의 필수조건으로 고정하지 않았다. ‘3D소품 존재’를 통과조건으로 넣어 AI가 바꾼 목표를 정확히 검사한 셈이다. 그래프 사용 자체를 신뢰성 증거로 삼지 말고 N01에서 사용자 요구→실제 산출물의 계약을 먼저 바로잡는다.

## 2. 현재 실제 제작 출처

| 대상 | 실제 제작·연결 | 범위/주의 |
|---|---|---|
| 표면 재질 | PixelLab MCP `create_tiles_pro`, job `f9eb76e3-4443-4a61-a070-7db94bcee95e`, 원본 64×64 PNG 16장 | 아스팔트·보도·벽돌·회벽·실내 바닥·지붕·목재 등. 물체 전체 그림 아님 |
| 표면 atlas | `Tools/WorldArt/pack_square_urban_kit.py` | 원본 크기 그대로 2px padding 포장, 512×512. 이미 native pixel이므로 PerfectPixel 호출0 |
| 건물/단차/차선 | `EnterableSpriteBuilding`, `MetricAtlasMesh`, `UrbanRoadMarkings`의 Unity 절차 메시 | 실제 벽·지붕·지상층·문. 차선은 미터 폭의 도색 기하 |
| 새 소품 11종+나무 | `Tools/WorldArt/create_urban_models.py`, Blender 5.2 headless → FBX | 책상·수납/진열 선반·작업대·옷장·소파·침대·원통휴지통·바퀴수거함·벤치·화분·나무. 수치로 별도 형상 저작; 새 무료 모델 다운로드 없음 |
| 가로등 | 기존 `Assets/Prefabs/Lighting/PrototypeStreetLamp.prefab` | 유지한 조명 기능 포함. 실제 MeshFilter 6개가 Unity 기본 primitive mesh 참조 |
| 캐릭터·적·Chest | 기존 게임/시험 자산 유지 | D09 새 아트 아님. 의료 건물 앞 단순 큐브는 기존 Chest 시험 외형 |

현재 연결: `Assets/Art/UrbanCoherent09/CoherentUrbanStyle.asset`, `Assets/Prefabs/World/CoherentUrban09/CoherentUrbanBuilding.prefab`, `StreetTreeVisual.prefab`; `Assets/Scenes/GameMapTest.unity`의 기존 생성기에 저장됨. 원본은 `Assets/Art/UrbanCoherent09/Surfaces/Source/`, 모델은 `Models/`, 출처/좌표는 `MaterialAtlas.json`, `Models/modelmetadata.json`에 있다.

PixelLab 호출 원문·영수증은 `LocalOnly/UrbanDesign09/{tiles-request,tiles-receipt,tiles-completed}.json`. 공식 MCP endpoint는 `https://api.pixellab.ai/mcp`; 노출된 도구에 Tiles Pro가 없어서 같은 설정의 인증으로 공식 tools/list와 tools/call을 호출했다. `pixellab_mcp.ps1`은 설정의 환경변수 이름만 읽으며 비밀을 기록하지 않는다. 설정 자체를 바꾸지 않았다. 최종 잔여량 관측1266회/$0, active Pixel Apprentice, reset2026-09-20. 타 작업 동시 사용 가능성이 있으므로 잔여량 차이를 이 작업의 정확한 과금 내역으로 단정하지 않는다.

## 3. 실제로 연결된 생성 그래프

```text
seed + generator/profile snapshot
 → 기존 연결 road graph(Kruskal + loop + 제한 대각선)
 → 2m SurfaceGrid
 → Ground의 4-neighbor 연결 컴포넌트 BlockMap
 → 접한 도로의 정면 frame + 같은 블록 안에 들어가는 OBB 예약 필지
 → 건물 본체 + 용도/POI
 → POI의 구역/확률/상한/허용 catalog
 → 벽·문·통로·다른 소품과 겹치지 않는 후보만 가중 선택
 → 실제 건물/소품 prefab/Collider
 → 기존 spawn manifest/registry
 → 기존 NavMesh·도착 gate
 → 실제 화면과 사용자 디자인 판단
```

`UrbanMapLayout/Planner`가 좌표·POI/배치의 권위다. `UrbanBuildingPrefab.Snapshot`은 저작 규칙의 불변 사본이며 별도 런타임 난수 Manager가 아니다. 지역 frame은 `p=c+r*q.x+f*q.y`, local 크기와 정면을 유지한다. OBB/SAT가 실제 포함/겹침을, AABB는 broad phase만 담당한다. 건물·문·소품·Collider 모두 같은 frame이다.

현재 시험 규격: 전체290m, node48m(5분할), tile2m, 차도6/10m, 보도폭2m, 단차0.2m, 본체 폭12~18m/깊이10~14m, 예약margin1.5m, 2층 외관6.8m. 모두 사용자 확정 디자인 수치가 아니라 현 시험 저작값이다. 동일 면의 밀도32texel/m, native64px=2m, 남는 면은 crop. 원본 테두리가 포함된 금속/유리 후보는 평면 반복으로 쓰지 않고 색 샘플로만 쓴다.

## 4. 작업 단위별 현재 판정

| 노드 | 판정 | 산출물/실제 남은 차이 |
|---|---|---|
| D01 입력/후보/좌표계 연구 | 작성됨 | `isometric_urban_map_pipeline.md` D09. 최종 표현 선택은 재개 필요 |
| D02 새 PixelLab 재질 | 실제 생성·수집됨 | 16개 source/receipt 보존. 다음 시작 때 다시 생성하지 말 것 |
| D03 도시 구조/회전 필지 | 구현·대표 seed 호출 확인 | `UrbanBlockMap`, `UrbanOrientedRect`, layout/planner. 연속 polygon 도시 생성기는 아님 |
| D04 실제 입체 소품 | 구현·치수/정면/volume 확인 | 12 FBX, 11 prop prefab + 나무. 완성 픽셀 스프라이트 아님 |
| D05 건물 용도→소품 연결 | 구현·대표 seed 호출 확인 | Medical1/Office24/Residential28/Retail28/Workshop35. 용도 총116개 |
| D06 최종 물리/생성 검사 | 제한된 기술 통과 | 실제116개 건물/470개3D소품, 벽·지붕 침투0, 문 이동/경로 통과 |
| D07 카메라 near 잘림 | 근본 수정·별도 관측 통과 | 실제 높이 bounds로 시선축 후퇴, offset/줌/화면XY 보존. 기본줌 적용 뒤 Follow 수행 |
| D08 시각 적합성 | **요구 이탈·사용자 중단** | 픽셀 목표 대신3D형상 제작. 방향/실내 역할도 미완. 기술성공으로 요청달성 선언 금지 |

Block45는 작은 Ground 섬도 센 연결 컴포넌트 수다. ‘디자인된 도시 블록45개’가 아니다. 대표 seed의 대각도로 접한 건물 필지는1개다. 도로 대부분이 격자이며 전체가 자연스러운 도심이 됐다는 의미도 아니다.

현재 실내는 **한 덩어리 내부 + 입구/업무/보관 배치 슬롯**이다. 주거의 거실·침실·욕실, 상점의 판매/창고/직원공간, 진료소의 접수/진료/대기처럼 실제 방을 나누는 벽·문·방 연결 그래프는 없다. 2층은 외관이고 플레이 가능한 2층 바닥·계단·층 이동은 없다. 각 소품 규칙의 현재 eligible 후보는 주로1종이며 많은 디자인 대안을 가진 생성 문법은 아니다.

## 5. 다음 작업 그래프 — N01부터만 재개

```text
N01 확정된 픽셀 목표로 제작 계약 복구(픽셀을원하는지다시묻지않음)
 ├─ 완성 pixel sprite 기반 후보 → N02(카메라/방향별입력 적합성 포함)
 └─ 3D중간재료가 실제 pixel목표를충족한다는샘플/근거가 있을때만 대안 제시
N02 선택 방식의 작은 건물1개 + 실내1구역 + 소품1종 실제 관찰 샘플
 → 사용자 피드백
    ├─ 부적합 → 실패 경계(표현/좌표/재료/구역)로 되돌림, 전체 재생성 금지
    └─ 유지 → N03 도시/필지 문법 + N04 실내 방 그래프
N03/N04 → N05 POI별 외관·실내·사물 catalog 연결
 → N06 선택된 표현의 필요한 재료만 생성/변환/통합
 → N07 마지막 필요한 기술검사 + 실제 외부/실내/이동 미리보기
 → 사용자 유지/수정 → 해당 분기 또는 인수인계/완료 기록
```

| 다음 노드 | 입력→반환물 | 구체적으로 해야 할 일 | 중단/분기 조건 |
|---|---|---|---|
| N01 표현 계약 | 이미 명시된 픽셀 목표/현재 실패 → 실제 픽셀 출력·카메라·최종 크기 계약 | 완성 pixel 물체를 얻는 제작경로와 기하/물리표현을 분리. 기존 자유카메라와 양립하지 않으면 누락된방향/깊이정보를 설명하고 필요한결정만 확인 | 픽셀/3D 중 다시고르라는 질문으로 요구대체를 정당화하지 않음. 현3D디테일확대 금지 |
| N02 작은 표현 샘플 | 픽셀 출력 계약/보존 재료 → 실제 건물1개/소품1종/실내 장면 | PixelLab 완성asset/다방향자료 또는 실제픽셀bake 등 근거있는 경로의 발점·크기·가림·픽셀크기를 확인 | 표면 texture만으로pixelart완성 선언 금지. 사용자 기준 미충족이면 해당 경로만 수정 |
| N03 도시/도로/필지 | 연결성/밀도/도로폭/접도 조건 → block/parcel 계획 | 대각선의2m 계단 경계, 교차부 차선/횡단보도, 과도하게 넓고 균일한 포장, 단순 균일 건물열을 개선. 용도별 도로 접면/서비스 공간/빈 부지 규칙 필요 | tile raster를 그대로 유지할지 도로 polygon과clip면을 쓸지 좌표/Collider 권위 먼저 결정 |
| N04 실내 방 그래프 | POI별 역할/방 크기/출입 → RoomGraph+벽/문+사용 가능 영역 | 방 역할·인접성·출입/복도 동선·가구 접근면·문 개폐 여유. 실제 partition을 제작 | 가구를 벽가에 나열한 것으로 방 분리 완료 처리 금지 |
| N05 POI/사물 연결 | 방/실외 역할+확인된 외형 catalog → 허용/가중 후보 | 침대는침실, 선반은판매/보관, 접수책상은접수 등 세부 역할. 가구 정면/사용면, 실외 수거함·간헐 공공휴지통·조경 밀도 구분 | 방향/크기/용도 불명 물체는 추측 배치하지 않음 |
| N06 필요한 제작만 | 채택 샘플 규격+부족 catalog → 새 자산/receipt/메타데이터 | PixelLab 이용 허용은 유지. 기존 native pixel 원본의 재정규화/재생성 반복 금지 | B경로의 숨은면/뷰 누락은 offset으로 해결하지 않음 |
| N07 최종 관측 | 변경된 권위/실제 출력 → 필요한 실제 증거+사용자 피드백 | 공통치수/정면/통로/층/재현/가림·실제이동. 현재와 무관한 검사는 재사용 | 동일AI 미술평가·동일파일형식왕복을 완료 증거로 삼지 않음 |

플레이 가능한2층·계단, 일반 POI의 전리품/위험·보상 예산, 가변적·상자 구성은 별도 기능 범위다. 이번 작업에서 자동 승인된 것으로 만들지 않는다. 성능은 실제 map generation/geometry/NavMesh 시간과 렌더 비용을 나눠 측정해야 한다. 현재 전체 생성10초 이내나 GPU최적화는 입증하지 않았다.

## 6. 실제 증거와 재실행 범위

- `LocalOnly/UrbanDesign09/technical.json`: seed1462661998, stable hash `14583068C88F2EB4`, repeat동일; .2m, 전체POI할당, 116rooms/470metricprops, frame/volume오류0, 실제벽/지붕penetration0, PlayerMovement→CharacterController 문 통과, NavMesh 문밖→실내중앙 경로. **물리키 직접 조작이 아닌 Play Mode 호출 확인**.
- `camera-technical.json`: 줌3.5/8×pitch10/35/80 총6case, near/far꼭짓점 실패0, normalized화면XY 최대차1.02894e-6, 깊이 제약해제/거리복원 확인. 전환 전체를 다시 시험한 것은 아니다.
- 최종 미리보기 `LocalOnly/UrbanDesign09/Final/{gameplay-street,street,interior,diagonal-street,pitch-10,pitch-80,orbit-0..3}.png`. `street/diagonal`은 구조 확인용 넓은줌18/28; 실제게임 줌3.5~8은 유지. `district.png`는 전체도시 관측이며 화면거리/aliasing을 미술품질로 판정하지 않는다.
- 최초 `street.png` 등은 카메라 near잘림이 포함된 **이전 관측**이고 Final과 구분한다. 실패를 숨기기 위해 삭제하지 않았다.
- 초기 영구 텍스처 참조오류는 `PaintWhite.asset`를 저장하여 해결했다. 콘솔에는 과거15:12 오류3건 및19:00 해당실패2건이 남아 있다. 마지막 조회 총5건은 보존했고 수정후새오류는 확인되지 않았다. ‘콘솔 전체무오류’가 아니다.
- 전체Recovery/모든seed/실제키보드/GPU/플랫폼build는 이번에 확인하지 않았다. enum None0/Medical1 및 기존spawn/보상경계 유지, generator11/checkpoint1007로 구버전거부는 코드검토다.

## 7. WorkLoop 재개 위치와 파일 안전

`Tools/WorkLoop/README.md` 실행기 사용. 현재 `LocalOnly/UrbanDesign09/state-v4.json`은 **paused**, `user_review` ticket `db3a23e154064d4bb90917cb6c98fb86`. 기술gate만통과했고 accepted/user_reply는 제출하지 않았다. 사용자 중단은 시각승인이나 거절자동판정이 아니다.

v2는 repair가observe입력에 연결되지 않아 `unchanged_input`으로 중단됐다. v3에서 실제 변경자원을 연결해 이전관측을 무효화했다. 이후 렌더 near잘림이라는 추가 반례 때문에 v3는pause하고 v4에서 camera증거만 추가했다. **v2→v3→v4는 새그림 재생성 횟수가 아니다.** verifier원본/상태를 보존했고 `verify_v4.py`는 기존물리JSON을 재사용한다.

다음 작업에서 N01 선택이 필요하므로 현재user_review에 임의accepted를 제출하지 않는다. 최신 요구가 현재결과의 명시적 유지라면 그 실제답변으로만resume/submit한다. 새표현/실내작업이면 기존state를 보존하고 위N노드의구체입출력/자원/실패분기를 가진 새그래프를 초기화한다. 전체변환을 처음부터 되돌리지 않는다.

Unity는 GameMapTest Edit Mode로 종료, runInBackground=false로 복원했다. 사용자 원본/이전D08/거절결과/캐릭터/무료에셋폴더를 삭제하지 않았다. 이번 결과는 디자인 미승인으로 완료커밋하지 않았으며 dirty/untracked 상태 자체를 보존한다. 다음 시작은 `git status`와 관련diff/이 문서/현재상태만 읽고 실제Editor/serialized reference를 확인한다. 기존타작업 변경을 stage하지 않는다.

주요 구현 경로: `Assets/Scripts/WorldGeneration/{UrbanBlockMap,UrbanOrientedRect,UrbanMapLayout,UrbanMapLayoutPlanner,UrbanBuildingDecorationLayout,UrbanBuildingPrefab,UrbanBuildingProp,EnterableSpriteBuilding,IsometricUrbanStyle,MetricAtlasMesh,UrbanRoadMarkings,ProceduralUrbanMapGenerator,IsometricUrbanView}.cs`, `Assets/Scripts/CameraFollow.cs`, `Assets/Editor/CoherentUrbanKitAuthoring.cs`. factory `Create()`는 기존asset존재시거절한다. 다시호출해현재결과를재생성하지 않는다.

보존해야 할 다른 작업의 dirty: 퀘스트/상인 graybox material, 캐릭터표현 material, AuthoringPreviewCamera prefab, GameMap1씬, GDD 및 미추적캐릭터시험/BrokenVector/지형자산. 현재D09만쓸때 `git add .`, reset/clean/checkout금지. 자산과meta/GUID를함께보존한다.
