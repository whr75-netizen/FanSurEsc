# D22 기지 씬의 이미지 / 실제 기하 조명 비교

## D26 현재 — 바닥 그림자도 2픽셀

GameMap1의 평면 `Ground`에만 전용 재료 `GroundPixelShadow.mat`를 연결했다. 원래 `Small Ground.mat`의 텍스처·Tint·LightPower를 그대로 복사하고 `_ShadowScreenCellSize=2`만 켰다. 기존 URPToonLit의 기본값0은 다른 재료의 동작을 유지한다.

바닥 fragment의 주광 그림자 조회 위치를 실제 화면 2×2 셀의 중심에서 복원한 광선과 바닥 평면의 교점으로 고정한다. 기존 ShadowCaster·shadow map·PCF·그림자 세기·GI·Cookie는 유지하며 바닥 전체 이미지를 픽셀화하지 않는다. 해당 바닥의 모든 주광 투사 그림자가 적용 대상이다. Point/Spot 그림자, SSAO, 곡면 수광은 이번 범위가 아니다.

현재 플레이어는 실제 visible renderer의 cast가 Off이며 표면 수광색만 픽셀화된다. 캐릭터 전용 바닥 그림자 기능을 복사했다는 설명은 하지 않는다. `LocalOnly/WorkLoop/desk-shadow26`에 실제 카메라 (45,350,0)/size5, 책상8개 size2, 바닥shadow size2 및 원본 재료 보존 관측과 Game View PNG 1회를 저장했다. 컴파일/Console 오류0, 외형은 사용자 피드백 대기다.

## D25 현재 — 원래 Play 카메라의 8방향

기존 D22/D23 캡처는 PlayerCamera 객체를 사용했지만 회전·위치·직교 크기·출력을 바꾼 통제 실험이었다. 사용자 Play 화면과 같다는 판정은 잘못됐다. 현재는 `ScreenCapture.CaptureScreenshot`으로 원래 Game View/UI를 그대로 저장한다. 기본 회전 `(45,350,0)`, orthographicSize `5`, offset `(2,10,-10)`이다.

`GameMap1/PixelDeskEightDirections_D24`의 8개 실제 책상은 Y 회전 0~315도/45도 간격이다. 이전 2개 비교는 보존/비활성화했다. 처음 두 배치는 기존 기둥과 큰 시험 구조물에 가려 실패했고 캡처를 보존했다. 최종 공통 루트 `(15,0,0)`은 동쪽 빈 바닥이며 8개는 X 약11.3~20.2, Z 약-5.1~-0.9에 있다. 기존 플레이어의 `TryTeleport`와 `CameraFollow`로 살펴봤으며 시작 spawn/카메라 설정은 바꾸지 않았다. 다시 살펴보려면 Play 후 **Tools → Pixel Desk → Inspect Eight Directions with Normal Player Camera**를 실행한다.

셀 모드에서 고정 시점 1px 경계 mask를 제외하고 실제 box part/face ID(1..72)를 기존 단일 소유자 cell 경계에 연결했다. 합성한 전체 셀에 stencil bit2를 기록해 후속 로컬광의 부분 재적용을 막는다. 목재/형상/조명식/2px 크기/기존 외곽선 색은 유지한다. 셀보다 가는 형상의 소실과 임의 곡면 지원까지 해결한 것은 아니다.

실제 결과는 `LocalOnly/WorkLoop/desk-cell-edges25-final/preview.png`, 카메라와 8개 방향·크기 및 12개 part ID 반환은 같은 폴더의 `readback.json`, 실행은 `state-v2.json`이다. 최종 캡처는 게임의 시간 흐름에 따른 어두운 조명 상태이며 밝기를 보정하지 않았다. 셰이더 컴파일과 실제 화면 제출을 확인했으며 외형은 사용자 피드백 대기다. 추가 카메라 조작·반복 보정·미술 자동 합격은 수행하지 않는다.

## D23 수정 계약 — 기존 엔진 조명 재사용

최신 정정: 추가 픽셀 통계/접촉 명암 검사를 중단하고 실제 화면의 픽셀 크기를 우선한다. 기존 `CharacterSilhouetteSubject`와 `CharacterSilhouetteRendererFeature`를 그대로 사용해 책상만 2×2 화면 셀로 표현한다. 캐릭터 전역 설정이나 전체 화면 해상도는 바꾸지 않는다. 실행 진입점은 `Tools/WorkLoop/pipeline.py`의 고정 `pixel_object` 제작 프로필이며, 변경 원인이 없는 상태는 유지한다. 실제 Unity readback → 최종 미리보기 한 장 → 사용자 외형 피드백 대기로 끝난다. AI가 통계로 미술 합격을 선언하지 않는다.

실제 적용: `LocalOnly/WorkLoop/desk-pixel-size-23-v2/state.json`은 apply→present→관측 파일 확인 후 `awaiting_user_visual_feedback`에 도달했다. Unity 런타임에서 `pixelCellSurface=true`, `pixelCellSize=2`를 읽었고 `LocalOnly/PixelUnityProbe22/pixel23/captures/context.png` 한 장을 최종 제출했다. Play 종료/임시 카메라 복원, Console Error/Exception 0. 실제 목재 파일·12개 치수는 보존했다. 사용자 외형 승인은 아직 없다.

픽셀 크기 변경 전 trial23의 RGB 조명 비교에서 주광 방향9,274픽셀/기존로컬광3,710픽셀 변화가 있었다. 이 수치를 픽셀 크기 변경 후 별도 측정으로 확대하지 않는다. 당시 전체 기지 PNG 비교114픽셀 차이는 원본Unlit에 URP SSAO가 적용된 접지부 최대5RGB 차이였다(설치URP `UnlitForwardPass.hlsl:130~133`). 다리의 지면 아래 좌표는 제거됐다. 이후 사용자가 추가검사를 중단시켜 SSAO 대조 촬영은 실행하지 않았으며 이전 false 판정 파일도 보존했다.

사용자 정정으로 D22의 고정 3단계 조명과 바닥을 제외한 합격 판정을 폐기한다. 새 광원 계산을 설계하지 않는다. 기존 캐릭터 adaptive source가 호출하는 `UniversalFragmentPBR`와 RGB `EvaluateSteppedLocalLights(...,0)*.55`를 책상의 기존 재료 입력에 연결한다. URP 주광·추가광·환경광·그림자를 엔진이 계산하고, 목재 UV와 실제 12개 형상 및 기존 shadow/depth pass를 보존한다. 내부선은 조명 후 고정색 덮기가 아닌 조명 전 albedo에 적용한다. 캐릭터의 별도 적응형 화면 후처리는 이번에 복제하지 않는다.

이미지 평면은 수직으로 세운다. 고정 직교뷰의 screen-up `u`, view `d`에서 기존 투영을 보존하는 수직 basis는 `Y/u.y`다. PNG의 가장 아래 불투명 픽셀 경계가 y=0에 오도록 평면 중심을 `d*t`만큼 옮긴다. `t=(원하는 중심 높이-기존 중심 높이)/d.y`이므로 화면 투영은 변하지 않는다. 임의 부위별 offset이나 depth-test 우회는 사용하지 않는다.

작업 그래프: `기존 코드·실패 증거 → 조명 연결/수직 카드 수정 → 실제 기지 전체와 조명 ON/OFF/방향 변경 촬영 → 최종 수치와 실제 이미지 제출`. 목재/형상/픽셀 격자는 유지하고 램프 세기를 올리지 않는다. 마지막 검사는 지면을 포함한 이미지 픽셀 보존, 면별 주광 반응, 로컬광 RGB 반응, 원재료·치수·캐릭터 설정 보존이다. 이전 D22 결과는 실패 이력으로 보존한다.

최신 요청: 최종 명암이 텍스처에 고정됐는지 확인하고, 기지 조명 옆에서 이미지와 실제3D를 비교한다. D21 최종PNG는 baked RGB이고 .blend는 재질 없는12상자다. 승인 목재 자체의 순수albedo는 증명되지 않았다. 원재료4색grain과 조명band는 분리돼 있다.

## 구현 전 계약

- A: 최종PNG 그대로, Point/무압축/mipmap없음. 고정 명암을 유지하는 이미지 대조군. 기지의 기존 로컬광 후처리는 평면 깊이/법선으로 반응할 수 있으며 내부그림자는 재계산하지 못한다.
- B: 같은12상자의 실제 중심/치수로 Unity 기하를 구성한다. 원재료grain만 적용하고 URP 주광의 normal·shadow와 기존 SteppedLocalLight를 읽어3단계 명암을 계산한다. 최종PNG는 B의 재료로 쓰지 않는다. 내부선mask는 기하에서 만든 고정시점 캐시이며 조명RGB가 아니다.
- 기존 PixelSpriteCacheBaker의 고정광PNG나 캐릭터flat shader의 N·L생략은 재사용하지 않는다. 전체화면 픽셀화도 켜지 않는다. Unity 표준래스터와 고정 native96PPU로 비교한다.
- Blender meter `(x,y,z)` → Unity meter `(x,z,y)`. 반사행렬 det=-1을 선언하며 box치수를 재구성해 정상외향면을 유지한다. 공통camera right/up/view basis도 같은변환을 적용한다. 이미지면은 `r*x+u*y`로 구성하고 원본174×155를96PPU로 놓는다.
- 원본screen origin과 동일pixel center를 맞춘다. orthographicSize=`출력높이/(2*96)`, AA/HDR/카메라후처리off. PPU는고정하며 게임전체줌/카메라설정은 테스트후복원한다. 자유회전/비정수확대에서 동일픽셀이 보장됐다는판정은금지한다.
- 기존 기지조명/셸/카메라/GUID를 보존한다. 조명변경은 임시Play Mode조건이고 씬에는 비교대상만저장한다. 현재로컬광은 실제shadow map을쓰지않는기존가산기능임을구분한다.

## 실행과 판정

`입력/재료export → Unity재질·기하배치 → 실제게임카메라 조건별출력 → 파일/픽셀/빛반응 측정`으로 진행한다. 일반 계산은CLI, 씬편집은Unity Editor 단일writer가한다. 실제GameCamera에서 전체기지문맥과대조군을캡처하고, 입력texture해시/Point/압축/밉맵/동일3D치수/계산명암변화/고정격자조건을확인한다. 코드컴파일을시각검증으로대체하지않는다.

표준근거: [Unity URP shadows](https://docs.unity.cn/6000.0/Documentation/Manual/urp/use-built-in-shader-methods-shadows.html), 프로젝트URP17.5 `Lighting.hlsl`, 기존 `SteppedLocalLightCommon.hlsl`의등록광원계산. 이비교는현물체/시점의최소실험이며 임의메시용픽셀렌더러의완료가아니다.

## 과거 Unity 결과 — D22 trial03 (사용자 지적으로 재개됨)

`GameMap1/PixelDeskLightingComparison_D22`에 왼쪽 A PNG, 오른쪽 B 12개 실제 메시를 저장했다. 카메라에서 보이는 면이 기존 램프를 향하도록 비교쌍의 중심을 램프에서 카메라 수평축 반대 방향 1.25m에 놓았다. 부품별 위치/치수는 바꾸지 않았다. 테스트 뒤 Play Mode를 종료하고 원래 열린 GameMapTest로 복원했다.

| 실측 항목 | 결과 |
|---|---|
| 원본 PNG / Unity PNG 픽셀 RGB 최대 오차 | 0 |
| 같은 격자의 3D 실루엣 / 원본 실루엣 IoU | 1.0 |
| 무조명 3D 출력에서 원재료 4색 이외 픽셀 | 0 |
| 주광 180° 반전 시 변경 픽셀 | A 0 / B 1,015 |
| 기존 로컬광 ON 시 최종색 변경 픽셀 | A 0 / B 1 |
| 로컬광 ON 시 양자화 전 입사광 변경 픽셀 | B 9,133 |
| 실제 주광 그림자 감쇠 진단 출력 | sRGB8 122~255; 무그림자 고정값이 아님 |

실제 게임 카메라 960×576, 직교 96PPU, AA/HDR/후처리 OFF에서 측정했다. 측정용 검정 배경과 전체 기지 문맥을 따로 저장했다. 독립 변수는 주광 방향 또는 기존 램프 ON/OFF이며, 시간·카메라 제어는 촬영 중만 중지했다. 주광 세기/색과 기지 램프 세기를 증가시키지 않았다. 현재 자유 줌·회전·카메라 이동 전체의 픽셀 안정성을 보장하는 시험은 아니다.

### 명암이 어디에 있는가

- A의 최종 `desk.png`에는 이전 렌더의 명암이 고정돼 있다.
- B의 `wood-grain.png`는 원본 PerfectPixel 재료의 4색 무늬다. 최종 desk PNG는 B의 셰이더에 연결되지 않는다. 순수 albedo라는 물리적 분해는 증명하지 않았지만 책상의 면별 명암/가림은 이 재료와 분리돼 있다.
- B의 입사광은 `Y(lightColor) × distanceAttenuation × shadowAttenuation × max(0,N·L) + Y(existingLocalLight)`이고, `.32/.72` 경계에서 `.42/.72/1` 곱색을 선택한다. 광색은 단계 선택에 쓰이며 목재 RGB를 유색광으로 물들이지는 않는다.
- 내부선은 D21 기하에서 만든 고정 시점 mask다. 조명 RGB가 아니지만 메시나 시점을 바꾸면 다시 계산해야 한다. 따라서 임의 시점용 완성 셰이더로 배포하지 않는다.

### 실패를 지우지 않은 수정

첫 실행은 픽셀 보존에 합격했지만 조명 반응이 0이어서 차단됐다. Forward+ 프로젝트인데 `_CLUSTER_LIGHT_LOOP` 변형을 빠뜨려 주광의 `unity_LightData.z` 경로를 잘못 탔다. 설치 URP의 표준 변형을 추가했다. 근거 없이 0.5로 낮춘 주광 계수도 1로 되돌렸으며 광량을 임의로 올리지 않았다.

trial02는 완료 파일을 확인하기 전에 Play Mode를 종료해 촬영이 중단됐다. 이를 성공으로 사용하지 않았다. trial03은 촬영 동안만 `Application.runInBackground`를 켜고 실제 완료/복원 기록을 확인한 뒤 종료했다. 초기 실패와 중단은 각각 원래 폴더와 trial02에 보존한다.

현재 램프는 기존 SteppedLocalLight이며 Unity Point/Spot Light가 아니다. 자체 그림자 차폐가 없는 표시용 가산광이다. alpha .35가 강도에 곱해지고, 현재 조건에서 많은 입사광 차이가 동일 명암 단계 안에 남는다. **최종 1픽셀 변화는 눈에 띄는 램프 반응이 구현됐다는 증거가 아니다.** 더 민감한 조명 반응과 픽셀 명암 단계 수의 선택은 후속 외형 결정이다. 이번 요청의 비교 시험에서는 수치를 바꿔 성공처럼 보이게 하지 않았다. Unity 추가 Point/Spot 조명 지원은 이번 셰이더의 범위가 아니다.

## 확인 경로와 재실행

- 실제 결과: `LocalOnly/PixelUnityProbe22/trial03/{capture,analysis}.json`, `captures/context.png`, `comparison.png`.
- 실행 그래프: `LocalOnly/PixelUnityProbe22/trial03-state.json`의 `graph_complete`는 위 고정된 기술 조건만 의미한다. 외형 승인이나 범용 모딩 렌더러 완성이 아니다.
- 저장된 비교 프리팹: `Assets/Tests/PixelDeskLighting22/LightingComparison.prefab`; 기지 씬에는 테스트 위치 override가 있다.
- 재촬영은 기지 Play Mode에서 `Tools > Pixel Desk > Capture D22 Play Mode Comparison`을 사용한다. 새로운 trial 폴더만 생성하며 기존 파일을 덮어쓰지 않는다. 최종 `capture.json`의 `status=captured`, `restored=true` 이후 Play Mode를 종료한다.
- 재분석: `python -B Tools/PixelUnityProbe/analyze.py <trial이름>`. 기존 원본 D21 입력이 보존된 로컬 실험용이다. `Build`는 이미 비교대상이 있으면 거절한다.
