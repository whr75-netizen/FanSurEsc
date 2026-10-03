# B37 — 물리 규격을 조건으로 준 공통 시트

## 실제 적용 결과 — 2026-10-03

`GameMap1`의 `PlannedPixelShop33` 프리팹에 **18종 원본 crop을 기존26개 인스턴스에 연결했다.** 이26개는 종전B35 면별 색 재투영 PNG를 사용하지 않는다. 프리팹 변경은 Mesh/Material 참조52개뿐이며 부모Transform·Collider·방·지붕·조명·Player·Camera 구조는 보존했다. 실패한R3/R4와 최초생성은 통합하지 않고 기록으로 남겼다.

| 구간 | 실제 결과/권위 |
|---|---|
| 생성 원본 | `Source/sheet.png`, 1489×1056 RGBA; 생성 출력 그대로 복사 |
| 전체 정규화 | 무수정 원본PerfectPixel OpenCV, grid_size=None/center/refine=.25/fix_square=False; 전처리 없이1회 |
| canonical | `docs/artifacts/building37/native-final/native.png`, **301×211**, 검출기가 정한 규격 |
| 분리 | 투명 경계 정수crop18종+잔여5; 63,511texel 중복/누락0, 23/23 RGBA동일 |
| Unity 원본 | `Assets/Art/NativeSheet37`, PNG hash/RGBA동일; Point/Clamp/NoMips/Uncompressed/FullRect |
| 표시 | 공통PPU31.75, 기존camera127screen px/m에서 **1texel=4×4screen px**; 같은asset은 sharedMesh/Material |
| 실제 관측 | 26/26 RGBA동일·screen기저4px·가시texel bounds초과0, 같은Player/Camera, 실내지붕숨김/외부복원 |

PPU는 표시 단위다. PNG를4배 확대해 저장하거나 모든사물을 같은width/height로 만드는 연산이 아니다. 원본fullUV를Point sampler로 읽고 공통화면 원점 위상으로 전체평면을 이동한다. 개별warp·목표해상도resample·색양자화·화면전체 재픽셀화는 추가하지 않았다.

실제 게임카메라(30°/350°,1114×857)의GPU readback은 `docs/artifacts/building37/R6/final/play-interior.png`다. `overview-*`는2560×1600으로 재프레이밍한 별도관찰화면이다. 부드럽게 보이는 문제도 조사했다. 실제renderer scale1/MSAA1/AA없음/post없음, source Point sampling이다. 화면의 고정선반영역에서q4 phase(0,1)의1,628칸 중1,428칸RGB가 완전히 동일했고 다른위상은 칸내 색차가 크게 증가했다(`capture-blocks.json`). **정규화 이후4px격자는 실제출력에도 남지만 모든화면픽셀의 색불변이나 미술합격은 증명하지 않는다.** opaqueTexture의2xBilinear 설정만으로 화면재보간 원인이라고 결론내리지 않았고 전역renderer/조명은 변경하지 않았다.

### 재사용 경로

`graph.json`은 전체정규화receipt→정수slice→RGBA검증이다. 이번저장결과는 해시를 대조해 재사용하며 정규화를 반복하지 않는다. 전체새시트일 때만 `Tools/Building33/native_normalize.py`의 원본엔진 자동검출을1회 실행한다. 실패를 임의규격으로 대체하지 않는다. `slice_sheet.py --help`로 분리명령을 확인한다.

표시는 `NativeSheetDisplay36.ApplyPlanarSources`의Edit `plan`→Play `experiment`→`display_gate.py --phase representative`→Edit `apply` 순서다. 통과한plan/code/experiment 해시가 같을 때만 기존참조를 연결한다. 최종 `ObserveLive`·`display_gate.py --phase final`·`display-graph.json`은 기술범위다. `check_capture_blocks.py`는 저장된GPU캡처의 대표칸만 검사하고 이미지를 수정하지 않는다. 고친원인의 영향단계만 재실행한다.

### 남은 한계

원본PerfectPixel도 불명확한 가짜격자에서 오검출하거나centre표본으로 특징을 잃을 수 있다. 생성입력도 가이드의 정확한3D비율/각도를 보장하지 않는다. 특히 진열섬/계산대의 원본상대크기와 소품방향·색밀도는 미술완성으로 판정하지 않았다. 이를개별scale/warp로 숨기지 않는다. 표시평면은 입체표면별 깊이/법선복원이 아니므로 복잡한Player앞뒤가림·자유회전·광원별 입체반응까지 완료했다고 확대하지 않는다. 변경하지않은Collider동선은 이전증거를 재사용했고 이번에는 키보드이동·빌드·저장로드·GPU성능을 재검증하지 않았다. 관측후Edit Mode로 복원했다.

## 현재 결정

사용자 요구는 원본 PerfectPixel의 자동 격자 검출을 사용하고, 이후 임의 해상도/비균등 비율/재투영으로 픽셀을 변형하지 않는 것이다. B36 시트는 소품과 가구의 비슷한 원본 크기 때문에 기존26개 배치에 넣으려면 q2로 전체 표시를 줄여야 했다. 실제 R4 대표2개의2×2 texel은 정상이나 선반이 과소이므로 프로덕션에 적용하지 않았다. 모든 원본·실패 실험은 보존한다.

이번 원인 단계는 **생성 입력의 상대 실물 크기**다. 기존 placement/collider와 벽 장식의 선언 치수를32texel/metre, 카메라30°/local45°로 투영한 `input-contract.json`·`guide.svg`를 제작 조건으로 사용한다. 가이드에는 보이는 cuboid/rectangle 투영 범위가 있고 개별 PNG 목표 크기 강제 변환은 없다. 미사용 하단을 뺀 가이드384×272는 제작 다이어그램의 캔버스이며 출력 PNG해상도 지정값이 아니다.

두 참조를 준 첫 생성이 옛 시트 배치를 따라 입력 불합격했다(`Source/layout-rejected.*`). 가이드만 준 후속 생성은 각 소품의 작은 상대 영역과 배치를 따랐다. `Source/sheet.png`는 생성 도구 출력을 byte 단위로 복사한 원본이다. 생성은 조건부 확률 모델이므로 도면 일치·카메라·크기·특징 보존의 수학적 증명이라고 부르지 않는다.

고정 제작 경로: **새 전체 원본→무수정 원본PerfectPixel 자동 검출1회→검출 격자의 정수 투명 경계 분리→정확 RGBA Unity import→원본 fullUV 표시**다. 기존 `NativeSheetDisplay36`의 공통 ray-plane 표시 계산을 재사용하며 셸/Collider/배치는 변경하지 않는다. 이 평면 표현은 3D부피 복원이 아니다. PNGresize/warp/사물별scale로 입력의 의미를 맞추지 않는다.

입력 실패·부분 실험 성공을 실내 완료로 바꾸지 않는다. 실제 게임 카메라에서 texel 양축 정수·동일 크기와 같은 asset 동일sharedmesh, 지붕/벽/Player 가림을 확인한 뒤 연결한다. source·normalized·crop·실제 gameplay 캡처를 구분한다. source의 숨은 RGB·낮은alpha도 임의 보정하지 않는다.

## R6 표시 원점 교정

R5 새 입력 preflight는 q3으로만 bounds에 들어갔다. 식 자체의 평면 교차는 맞았으나 카메라 평면의 원점0에서 ray를 시작해 **Collider 전면Z를 이동하면 source의X 중심까지 같이 이동하는 오류**가 있었다. 화면 원점을 실제 부착/지지 기준점 P0에 연결하지 않은 좌표계 계약 위반이다. 원본을 줄여 해결하지 않는다.

올바른 공통 식은 `S=R*u/ppu-U*v/ppu; P=P0+S-F*dot(n,S)/dot(n,F)`다. P(0,0)=P0와 n·(P−P0)=0이며 texel 투영 기저가 같다. bbox수평중앙·최소Y(또는벽상단) 규칙은 그대로 사용한다. **전면 변위가 다른 수평축의 중심에 새 변위를 만들지 않는다.** 원본/crop·배치·Collider를 다시 만들지 않고 원인 함수만 고친다. 기존 R5/support-plan.json과 이전R3/R4실험은 당시 실패/관측으로 보존한다. R6별도관측을 통합 기준으로 사용한다.
