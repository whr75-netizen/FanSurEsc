# D22 기지 씬의 이미지 / 실제 기하 조명 비교

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

## 실제 Unity 결과 — D22 trial03

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
