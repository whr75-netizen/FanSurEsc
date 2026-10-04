# N16 — 테스트 건물 한 채의 native 표면·실시간 조명 제작 계약

## 현재 결정 / R0~R2 (2026-10-04)

사용자가 N15의 표현을 개선된 기준으로 확인하고 그 파이프라인을 정리한 뒤 기지 GameMap1의 테스트 건물 내부 전체에 적용하도록 요청했다. 대상은 PlannedPixelShop33의 활성 실내다. 18종/26개 사물, 기존 구조·지붕·절개·벽등을 대상으로 하며 플레이어·카메라·동선·콜라이더·방의 역할·다른 건물·도심은 보존한다. 사용자 원본 시트와 N15 결과는 그대로 남긴다.

시작 시 직접 관측: GameMap1 Edit Mode, scene dirty=false. 건물 yaw305°, 카메라30°/350°. 활성 renderer46개, 그중18종 사물26개. 건물 nativePixelsPerUnit127은 B34 구조용 cache 해상도이고 현재 B37 사물은31.75 PPU다. N15의90.51 PPU 결과를 이 건물에 붙이지 않는다. 기존 사물의 과도한 표시 높이는 전체 PNG의 평면 역투영이며 실제 부피의 근거가 아니다. 실제 치수·방향·support는 Building37 input-contract, 실제 구조는 이번 placement-baseline.json으로 연결한다.

후보: 완성 PNG에 빛을 곱하는 방식은 고정 명암 중첩 때문에 제외한다. 기본 메시 PBR+전역 pixelization은 연속 명암·이중 픽셀 문제 때문에 제외한다. **실물 semantic geometry→native 위치/법선/재료 cache→기존 Unity 광원→작은 재질별 명암 palette**를 채택한다. 실제 메시를 별도 ShadowCaster로 사용한다. 이 연결이 최소 사물의 광원 변경에서 표면별 반응·변하지 않는 재료/경계를 보여 주지 못하면 실내에 통합하지 않는다.

## 좌표·입출력 계약

- Canonical은 각 사물의 Unity building-local XYZ 미터: X폭,Y상향,Z깊이, Unity 좌수계. 바닥 사물은 수평 bbox 중심이 X/Z0, 발이Y0. 기존 앞면 방향(-Z/-X/+Z), 실물 width/height/depth는 asset 선언에서 고정한다. 숨은 면은 source 복원이 아니라 의미 부품 template의 명시 저작이다.
- 고정 카메라 basis R=(.70710678,0,-.70710678), U=(.35355339,.8660254,.35355339), F=cross(R,U)=(.61237244,-.5,.61237244). camera local yaw45 + root305 = world350, pitch30. 공통 제작 PPU31.75는 현재 사물 표시 밀도다. 새 PNG를 축소하여 맞추지 않고 첫 기하 표본부터 이 밀도를 사용한다.
- Project(P)=(dot(R,P),-dot(U,P))*PPU. native pixel center S=(uR-vU)/PPU, primary O=S-F*far,D=F. finite solid의 최근접 양의 교차가 position·normal·part·chart·mask를 소유한다. box는 slab, 원형 부품은 원통/타원체의 해석적 교차 또는 같은 기하의 triangle ray intersection을 사용한다. 삼각형 분할선은 경계로 칠하지 않는다.
- Native 원점은 투영된 실제 geometry bounds의 floor minimum에서 정수 padding을 뺀 값이다. renderer 표시 mesh는 R/U를 따른 동일 texel domain이고 정수 texel phase만 snap한다. XYZ cache는 renderer local metre로 한 번 저장하며 runtime TransformObjectToWorld/TransformObjectToWorldNormal→현재VP로 깊이를 쓴다. ray t를 SV_Depth로 쓰지 않는다. clip/alpha/실루엣은 실제 기하만 소유한다.
- Geometry는 18종의 의미 있는 부품과 구조의 실제 폐곡면이다. cabinet·shelf 상품·냉장고 선반/병·계산기 콘솔·사과/용기·열린상자·원통·화분/줄기/잎·벽 장식은 서로 다른 template다. 통짜 큐브 사진으로 대체하지 않는다. 유리 냉장고는 frame+손잡이+내용물의 불투명 표면이 depth owner이며 glass는 표현 overlay로 구분한다.
- Material은 관측 palette·재질 ID·intrinsic pattern rank다. N15 목재 reference/관측 RGB와 B37 원본의 추가 역할색·작은 특징을 재사용한다. 광원 방향에 따른 원화의 면 밝기·접촉 그림자 RGB는 cache 재료가 아니다. 무늬 rank에 남은 원화 밝기의 영향까지 완전히 제거하거나 pure albedo를 복원했다고 주장하지 않는다.
- Lighting은 기존 Unity URP main/additional light·SH와 기존 SteppedLocalLight globals를 사용한다. 새 Manager/광원 권위를 만들지 않는다. 입사광은 normal·위치·거리감쇠·shadow에서 계산해 작은 palette를 선택한다. 기본광100·continuous PBR 색 출력은 없다. local fullscreen 재적용은 기존 stencil bit2로 제외한다. stepped presentation light의 동적 가구 그림자는 기존 기능이 아니며 URP light shadow와 혼동하지 않는다.
- Edge는 외곽·명시 깊은 틈만 검정, 실제 crease는 재질 계열색이다. smooth primitive의 triangle/chart tessellation seam은 role0. 빛이 변해도 geometry·material·edge 입력은 변하지 않는다. Native object는 캐릭터 cell expansion/전역pixel renderer에 연결하지 않는다.

## 절차 그래프와 완료 관찰

WorkLoop: geometry→material→native export/preview→CPU invariant→Unity 최소 조명 실험→26개/구조 연결→실제 게임 관측. 최초 4단계는 command.run의 실제 입력/출력/코드 해시를 고정한다. Unity 연결은 기존 오브젝트의 mesh/material 참조와 필수 cache component만 변경하는 한 writer가 맡는다. 단계 실패는 geometry/material/light/edge/binding에 귀속하고 원인 없이 전체 재생성을 반복하지 않는다.

필수 검사:18종 누락0, 실제 declared bounds·support·원본 SHA 불변, mask와finite hit 일치, normal 단위길이/좌표 왕복, surface RGB와조명분리, 검정역할/색모서리일치, 캐시map domain동일, source/PNG이중resize0, 같은assetshared자료, local/VP깊이·캐릭터앞뒤가림, 광원변경시기하/재료불변·서로다른면빛반응, 실제shadow, 지붕/벽절개와동선보존. float허용오차1e-5m와unitnormal1e-5는float32저장기준이며화면pixel표본은정수domain이다.

고정 source sheet에서 모든 디자인이 완벽히 자동 복원된다고 가정하지 않는다. 실제 최종 게임 카메라의 실내와 광원 비교를 함께 제출하며 파일 존재·컴파일·AI 동의를 미술 완성으로 바꾸지 않는다. 컴퓨터 UI 조작은 이번 범위에서 사용하지 않는다.

## 직접 근거

N15의 finite hit·재료/명암/경계 분리, PBRT slab/diffuse, Unity6.5 URP Lighting.hlsl의 GetMainLight/GetAdditionalLight와 world shadow-coordinate API를 재사용한다. 기존 IsometricAtlasSurface의 native-position→VP depth, SteppedLocalLightCommon의 조명 권위·stencil 계약은 실제 코드에서 확인했다. GroundedPropSprite/DeskLivePixelProbe의 unlit card/continuous PBR 표현은 이번 입력에 부적합하다.

## R3~R4 현재 결과와 재개 계약

[현재] `docs/artifacts/building38/run04`의 WorkLoop8노드 완료: geometry→materials→export→CPU invariant→Unity 최소 실험→실험 gate→건물 연결→실제 관측 gate. 진입점은 `Tools/Building38/run16.py`다. 원본 raw sheet/N15 reference를 보존하며 PerfectPixel·Blender beauty·생성 API·완성 PNG 재축소를 추가 호출하지 않았다. 기하에서 native pixel을 처음 제작하는 입력이므로 격자 복원 단계가 아니다.

[현재] 실제 미터 치수18종/26개 사물+17개 벽·지붕·절개면을 원래 renderer에 연결했다. 위치·법선·재료·무늬·경계 map35종은 공유 자산, 실제 폐곡면 shadow child43개다. Floor·기존 벽등2개의 자료와 표시 경로는 보존했다. cabinet inlay·clock ink·poster ink는 실제 표면 안의 material annotation으로 alpha/부피를 추가하지 않는다. 소품 support7개와 clock/poster 중심 anchor2개의 Y만 계산했고 X/Z 이동0이다.

[Play Mode 호출·실제 GPU 렌더] 26개/18종, 기존 Player·Camera 동일, pitch30.000004°/yaw349.999969°, source pixel당 화면4px. 내부 roof hidden1/wall faded9, shader error0. 실내 local light off/on은39,714px 변화. 최소 사물의 같은 renderer/maps를 유지하며 실제 주광 방향만 변경해41,424px 변화했고 실제 caster off/on 그림자는2,354px 변화했다. 기술 gate는 미술 승인·전체 게임 입력 검증이 아니다.

`play-interior.png`는 원래 게임 카메라의4px 표시다. `play-overview.png`는 같은 카메라·각도에서 일시적으로2px 정수 표시한 전체 건물 capture이며 줌은 즉시 복원했다. 제작 PNG 축소가 아니다. Play Mode 종료, Scene View30°/350°, Edit scene dirty=false, surface/caster43이다.

[범위 감사] 원래 GameMap1 serialized535블록 중534개 본문 불변, 변경은 이 건물 PrefabInstance1개다. 기존 override11개/원본 prefabGUID/콜라이더 치수 유지, 원래 블록 삭제0. 추가215개는43개 caster계층과 부모 참조뿐이다. 원본 `PlannedPixelShop33.prefab` 전체 전파는 자동 승인 검토가 다른 인스턴스 영향 가능성을 이유로 거부했다. **GameMap1의 테스트 인스턴스 override**로 저장했고 원본 prefab/다른 건물은 유지한다. 별도 명시 승인 없이 전파하지 않는다.

현재 자료를 사용할 때는 `Assets/Art/NativeBuilding38`과 씬 참조를 재사용한다. 치수/부품 변경은 geometry와 후속 cache, 재질/무늬 변경은 materials/export, 조명 변경은 기존 Unity 광원 단계로 귀속한다. PP31.75는 유지하며 큰 사물은 최초 계산에서 더 많은 pixel을 가진다. 이미지 늘리기·부위별 offset·완성 원화 음영RGB 덧곱은 수선이 아니다.

새 제작 승인 시 `python -B Tools/Building38/run16.py --output <workspace의 새폴더>`를 실행한다. 4단계 뒤 ai.work는 활성 Codex에게 Import/GPU 실험과 기존 인스턴스 Apply를 넘긴다. 사용자가 실행기를 조작하는 절차가 아니다. Importer는 다른 source hash로 기존 공유 자산을 덮어쓰지 않는다. 새 source버전 교체에는 원본 보존·GUID/참조 전환을 포함한 별도 변경 계약이 필요하다.

남은 한계: 숨은 면/상품은 semantic template 저작이며 원화의 자동3D복원이 아니다. 순수 albedo를 복원하지 않았고 wood pattern rank에 원화 밝기 영향이 남을 수 있다. native 윤곽은 해석적 hit지만 곡면 shadow mesh는16분할/8ring 근사다. 냉장고 frame/contents는 있으나 유리 반사·투과 overlay는 미구현이다. Floor/벽등을 새 cache 조명으로 통일하지 않았다. 임의 시점·시점별 cache·사용자 미술 합격·Standalone build·전체 게임 기능은 미검증이다. 현재 결과는 실제 조명이 연결된 한 건물 prototype이며 디자인 완벽/원화99%복사를 선언하지 않는다.
