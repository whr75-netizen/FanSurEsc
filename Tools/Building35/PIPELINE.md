# B35 제작 경로 — 원본 보존 위반으로 재검토

2026-09-27 최신 정정: 아래 §1~6은 현재 씬을 만든 **과거 경로의 설명**입니다. 면별 재투영이 원본 픽셀 배열을 바꾸므로 정규화 원본 보존 경로로 재사용하지 않습니다. 픽셀 표시 수정은 아직 미완료이며, 현재 결정·입력 충돌·Blockbench 참고·재개 조건은 [원본 보존 계약](../../docs/references/native_pixel_input_contract.md)을 따릅니다. 기존 씬과 재료는 비교용으로 보존합니다.

## 1. 원본과 계산의 책임

`역할 도면 → 실물 치수 → 생성 원본 → 원본 PerfectPixel 자동 정규화 → 공통 면 투영 → 동일 표면 RGBA/XYZ → 지지면 배치 → 기존 Unity 표시 → 영향받은 최종 관찰`

도면은 `docs/artifacts/building35/placement.json`과 `details/placement.json`, 실물 치수는 `metric-catalog.json`, 원본은 `Source/`의 PNG·프롬프트·generation 기록입니다. 잘못된 방향·치수를 임의 Transform으로 고치지 않습니다. 면 주석과 역할 해석에는 AI 저작이 남으며, 적합에 쓰지 않은 내부선도 확인해야 합니다. 선반 안 상품은 전면에 그려진 아트로, 개별3D 복원이 아닙니다.

## 2. 공통 좌표와 픽셀 밀도

건물 local X/Y/Z는 오른쪽/위/뒤입니다. 직교 pitch30°·local yaw45°·127 PPU를 공유합니다. world 카메라 yaw350°−건물 yaw305°=local45°이며 물체별 카메라 보정은 없습니다.

```text
R = (1, 0, -1) / √2
U = (1/(2√2), √3/2, 1/(2√2))
D = R × U = (√(3/8), -1/2, √(3/8))
screen(X) = (127·dot(R,X), -127·dot(U,X))  # 이미지 Y 아래
```

바닥축 화면 기울기±.5는 약26.565°이며 카메라 pitch30°와 다릅니다. 캔버스는 물리 치수와 투영 범위로 계산하므로 물체마다 크기가 다릅니다.

`project_faces.py`는 source 네 점과 공유 XYZ의 투영점으로 homography를 구해 출력 texel 중심에서 원본 한 픽셀을 선택합니다. `dot(XYZ,D)`가 작은 같은 표면이 색·alpha·깊이를 소유합니다. [OpenCV 평면 사영](https://docs.opencv.org/4.13.0/d9/dab/tutorial_homography.html)의 적용 범위이며, 행렬 잔차만으로 원본 평면성을 증명하지 않습니다.

PerfectPixel은 입력 격자를 검출하며 방향·미터 크기를 해결하지 않습니다. 이후 공통 물리 밀도로 옮길 때 **재표본화와 정보 손실**이 있습니다. nearest도 특징 보존을 보증하지 않습니다. 임의 저해상도 축소·재확대나 화면 전체 이중 픽셀화로 대신하지 않습니다.

## 3. 실측 바구니의 분리 합성

치수 근거는 [Gadsby 40×30×10cm](https://www.gadsby.co.uk/products/acacia-wooden-crate-40-x-30-x-10), 사과는 [NC 분류](https://historicsites.nc.gov/all-sites/horne-creek-farm/southern-heritage-apple-orchard/learn-more/apple-variety-information/glossary-terms)의 Large80–95mm 중90mm를 선택했습니다.

빈 상자와 사과는 별도 원본입니다. 상자 바닥Y=.015m·벽두께.012m·외곽.4×.3×높이.1m이며, 과일을 가리는 닫힌 덮개는 거절합니다.

- 첫층4×3: X={-.135,-.045,.045,.135}, Z={-.09,0,.09}, 중심Y=.06.
- 둘째층3×2: X={-.09,0,.09}, Z={-.045,.045}, 중심Y=.06+√(.09²−2×.045²)=.12363961.
- 이웃 구 중심거리≥.09m, 최상단Y=.16863961. Collider는 X/Y/Z=.4/.2/.3m입니다.

직교 광선에서 사과 앞면은 `C+R·sx+U·sy−D·√max(0,r²−sx²−sy²)`입니다. 잎·꼭지의 원본 alpha가 구의 원 밖으로 나오면 버리지 않고 같은 중심 깊이의 평면에 보존하며 확장량을 기록합니다. 이 부속 표현은 실제 구 부피가 아닙니다.

새 사과 자동 정규화는65×60 캔버스, 불투명30×32, 정사각 프레임32px입니다. 최종90mm 프레임은 `.09×127=11.43px`로 **실제 표본 감소와 세부 손실**이 있습니다. 18개 과일 합성 결과는68×47입니다. 꼭지 포함 프레임이므로 과육만90mm로 측정한 것은 아닙니다.

근거는 `docs/artifacts/building35/tray-composite/`의 `native/apple/receipt.json`·`crate-spec.json`·`render/receipt.json`입니다. 출력은 `render/native.png`, `positions.rgba32f`, `owner-id.png`; Unity raw XYZ는 아래쪽 행부터 읽도록 행을 뒤집습니다.

## 4. 부착과 Unity 표시

`position`은 바닥/지지면 중심, Collider 중심은Y+높이/2입니다. 바닥Y=.015, 계산대 실제 지지면Y=1.0566364525를 사용합니다(Collider 상면1.015와 다름). 장부 두께.02m처럼 물리 두께를 명시해 부착합니다.

벽 실내면Z≈3.925/X≈4.925에서 선언된 두께만큼 안쪽에 붙입니다. 투명 여백은 물체 폭이 아닙니다.

`IsometricAtlasSurface.shader`의 NativeDepth를 재사용합니다. 색·선형 RGBAFloat XYZ를 Point/Clamp, mipmap/압축 없음으로 읽고 Forward·DepthOnly·DepthNormals의 표면 깊이를 공유합니다. alpha/depth 영역·격자·bounds를 맞추되 GPU depth buffer 동일성까지 증명한 것은 아닙니다.

현재26개는 기본20+소품6개이며 그림 속 병은 별도로 세지 않습니다. 마지막에는 바구니3개의 Mesh/Material/Collider만 수정하고 위치와 다른23개를 유지했습니다. `tray-composite/prefab-preservation.json`은 기존18개 Transform의 HEAD 비교와 추가5개의 배치/지지 규약 대조를 구분합니다.

## 5. 명령과 그래프 운용

프로젝트 루트에서 대문자를 실제 경로로 치환합니다. ENGINE/DEPS는 native receipt를 따릅니다. argparse 대조를 마쳤습니다.

```text
python -B Tools/Building33/native_normalize.py --source INPUT --output-dir NEW_NATIVE --engine ENGINE --deps DEPS
python -B Tools/Building35/project_faces.py SPEC NEW_OUTPUT
python -B Tools/Building35/tray-composite.py --crate-spec docs/artifacts/building35/tray-composite/crate-spec.json --apple docs/artifacts/building35/tray-composite/native/apple/native.png --output NEW_RENDER
```

새 원인에만 새 출력 폴더를 사용합니다. Unity의 `Assets/Editor/PixelShopProjection35.cs` 진입점은 `Apply()`·`AppendDetails()`·`ApplyMetricTray()`입니다. **기존 결과 덮어쓰기를 차단하므로 재호출로 갱신되지 않습니다.** 새 변경에는 별도 출력과 명시적 import 연결 수정이 필요하며 writer 한 명이 담당합니다.

`graph.json`은 기본 제작, `details-graph.json`은 소품, `tray-composite-graph.json`은 현재 바구니입니다. 이전 `tray-graph.json`과 구분합니다. WorkLoop의 `init → run → next → submit` 명령·ticket은 `Tools/WorkLoop/README.md`를 따릅니다.

`command.run`은 고정 계산, `ai.work`는 Codex에 부위를 넘기는 인계입니다. 제출 후 진행하며 사용자 질문·종료가 아닙니다. 주석·생성·Unity까지 무인 자동화되지는 않았고 그래프 통과도 미술 합격이 아닙니다.

| 변경 원인 | 다시 실행할 구간 |
|---|---|
| 원본 이미지 변경 | 해당 원본 정규화→해당 면/합성→관련 import |
| 미터 치수·패킹 변경 | catalog→투영/합성→같은 오브젝트의 자산/Collider |
| source 면 주석 오류 | 면 명세→해당 투영과 깊이; 카메라로 숨기지 않음 |
| 배치·지지면 변경 | 해당 배치 계산→부착→영향 동선 |
| 셰이더/import 변경 | 관련 pass·격자와 대표 화면 |
| 문서 변경 | 문서 확인만 |

## 6. 관찰 범위와 남은 한계

기본 제작은 Play API 접근12/12, 소품 추가는 영향 경로3/3입니다. 바구니는 Collider가 줄고 위치/입력이 같아 통로 반복 없이 snapshot만 관찰했습니다. `tray-composite/play-observation.json`의 접근0·출입false는 이번 미실행 항목입니다.

Player/Camera ID 보존, alpha/depth 불일치0, 프레임/지붕 범위 누출0입니다. Console 전후 오류11→11·추가0이며 기존 오류는 보존했습니다. 실제1114×857과 재프레이밍 조망2560×1600은 구분합니다.

큰 가구 각도/배치는 사용자 유지 기준이나 세부 미술은 미완입니다. rear 내부선 약2.56/3.56px 잔차, 고정시점 평면/원본 음영, 작은 GameView 줌과 저밀도 특징 한계가 남습니다. 자유회전·숨은 면·물리 키·빌드·저장로드·GPU 깊이 동일성은 미검증입니다. 다음 명시 요청에서 원인 단계만 재개합니다.
