# 정규화 원본 보존과 Heartbeast / Blockbench 경로

## 현재 결정과 근거

2026-09-27. 사용자 최신 요구는 정규화한 픽셀이 다시 뭉개지게 만든 경로를 제거하고 원본을 제대로 표시하는 것입니다. **건물 수정은 아직 미완료**입니다. 아래 연구/진단의 완료를 건물 완성으로 취급하지 않습니다.

- [현재·코드/파일] B35는 원본 PerfectPixel 자동 검출 후 `project_faces.py`에서 면별 homography와 nearest 샘플링을 수행했습니다. 원본 PNG를 Unity에 그대로 연결한 경로가 아닙니다. `PixelShopProjection35.ImportAssets`는 이 파생 PNG를 복사합니다.
- [현재·Editor 읽기] GameMap1의 기존 건물에는 46개 활성 표면이 있고, 가구/소품 26개는 B35 파생 Color 파일을 사용합니다. 바구니 3개는 `appletray_composite.png`입니다. 씬은 Edit Mode이며 dirty=false였습니다. 확인용 원문은 `LocalOnly/Building35NativeCorrection/live-baseline.txt`입니다.
- [정정] 메시 사용 자체가 원본 변형을 뜻하지는 않습니다. 카메라와 평행한 사각형에 UV를 그대로 연결하면 색 원본을 보존할 수 있습니다. 이번에 확인한 변형 단계는 Unity 이전의 면별 재투영입니다. Point 필터는 이미 손상된 선을 복원하지 않습니다.
- [결정] 기존 면별 재투영/소품 축소를 **원본 보존 제작 경로로 재사용하지 않습니다.** 기존 파일과 씬은 원인 비교용으로 보존합니다. 이전 배치 승인을 픽셀 배열 변경의 승인으로 확대하지 않습니다.
- [최신 확정] 사용자가 “픽셀은 픽셀크기 키워도 뭉개지지 않는다”, “한번에 시트를 뽑으면 된다”고 정정했습니다. **정수배 확대는 정상적인 무손실 표시입니다.** 기존127PPU를 고정해 재제작/배치변경의 양자택일로 제시한 질문은 철회합니다. 한 시트에서 상대 크기·방향·스타일·픽셀 밀도를 함께 생성하고 전체 정규화 후 정수 영역으로 분리합니다. 실행 계약은 `Tools/Building36/README.md`입니다.

## 1. 새 영상에서 직접 확인한 내용

[Heartbeast — How to Make 3D Models from Pixel Art](https://www.youtube.com/watch?v=2WwztiNmPAQ)의 공식 YouTube 메타데이터/설명을 읽었습니다. 길이는 3,755초이며 설명에 Aseprite, LibreSprite, Blockbench와 아래 재료 페이지가 연결돼 있습니다.

[제작자 자료 페이지](https://uheartbeast.itch.io/pixel-blacksmith-house)는 Toby Dixon에게 의뢰한 작품을 이 튜토리얼의 재료로 제공한다고 설명합니다. 따라서 이것을 생성 이미지의 자동 3D 복원 시연이라고 소개할 근거는 없습니다. 파일 구성·이용 조건은 아직 검토하지 않았으며 다운로드/설치하지 않았습니다.

**증거 한계:** 영상 프레임이나 전체 작업 순서를 직접 확인하지 못했습니다. 공식 영어 자막 주소는 있었지만 응답 본문이 비어 있었습니다. 아래 도구 기능과 적용 판단은 공식 문서에 근거하며, 영상에서 모두 수행했다고 주장하지 않습니다.

- [Blockbench 개요](https://blockbench.net/wiki/guides/blockbench-overview-tips/): 참고 이미지를 도면으로 표시하고, cube/plane/mesh와 UV를 저작하며 외부 픽셀 편집기와 연동할 수 있습니다.
- [Blockbench UV 지침](https://blockbench.net/wiki/guides/minecraft-style-guide/): 텍스처 픽셀과 모델 단위의 비율을 유지하여 눌림/늘어남을 피합니다. Minecraft용 스타일 문서이며 현재 프로젝트의 127 PPU를 결정해 주는 규칙은 아닙니다.
- [Blockbench 내보내기](https://blockbench.net/wiki/guides/export-formats/): Unity용 FBX/DAE 경로를 안내합니다. 실제 Unity 호환성은 이 프로젝트에서 아직 실행하지 않았습니다.
- [Unity Point 필터](https://docs.unity3d.com/kr/6000.0/ScriptReference/FilterMode.Point.html): 가까이에서 texel 경계를 보존하는 샘플링입니다. 모든 원본 texel이 임의 시점/축소 배율에서 화면에 남는다는 보장은 아닙니다.

## 2. 구분해야 하는 세 가지 픽셀 규약

1. **원본 보존:** 정규화 RGBA를 별도 원본으로 보존합니다. 직접 수입은 배열 크기/값이 같고, 정수배 확대는 `Ck[x,y]=C[floor(x/k),floor(y/k)]`여야 합니다. 확대본의 치수가 다르다는 이유로 실패시키지 않습니다.
2. **표면 밀도:** 3D 모델의 표면 1m에 몇 texel을 배정하는지입니다. Blockbench의 모델/UV 저작은 이 규약을 관리할 수 있습니다.
3. **화면 격자:** 한 texel이 화면에서 같은 크기의 정사각형을 차지하는지입니다. 비스듬한 모델 면의 투영은 일반적으로 이 조건을 만족하지 않습니다.

`정규화 → Point import`만으로 2·3 또는 그림의 방향/비율까지 보장하지 않습니다. 반대로 화면 격자 검사만 통과했다고 원본 정보 보존을 주장해서도 안 됩니다.

## 3. 현재 입력의 충돌

alpha>0.1인 영역의 화면상 크기입니다. 실제 XZ footprint를 PNG bbox에서 복원한 값이 아닙니다. B34/B35 `docs/artifacts/*/native/`의 입력과 `Assets/Art/PixelShopInterior35/Color/`의 실제 연결 PNG를 읽어 계산했습니다. 새 시트의 합격 기준으로 이 비율을 사용하지 않습니다.

| 입력 | 정규화본의 불투명 영역 | 현재 파생 출력의 영역 | 원본을 공통127 PPU로 연결했을 때 |
|---|---:|---:|---|
| 계산대 | 146×130 | 294×255 | 현재의 약 0.50배 |
| 계산기 | 205×218 | 44×46 | 현재의 약 4.7배 |
| 시계 | 122×119 | 30×40 | 폭 약4.1배, 높이 약3.0배 |
| 작은 쓰레기통 | 93×170 | 28×49 | 약3.4배 |
| 상자 | 201×196 | 82×79 | 약2.5배 |

계산대와 낮은 진열대는 같은 정규화 원본을 서로 다른 치수로 재투영한 사례입니다. 동일 PPU·동일 표시 배율에서 같은 배열의 화면 크기는 같습니다. 개별 정수배 확대는 가능하며 원본 색을 보존하지만 그 물체의 화면 픽셀 크기도 함께 커집니다. 합성 바구니는 상자/사과 두 원본으로 만든 파생물이며 대응하는 단일 자동 정규화 원본이 없습니다.

이 표는 서로 독립적으로 생성한 아트를 후처리로 억지로 맞춘 기존 경로를 설명합니다. **픽셀 확대 자체가 정보를 뭉갠다는 근거가 아닙니다.** 새 입력은 사용자가 제시한 공통 시트로 구성합니다. 기존127PPU 값을 새로운 아트 규격보다 우선하지 않습니다.

## 4. 후보와 적용 범위

| 후보 | 원본 색 배열 | 현재 요구의 한계 / 결정 |
|---|---|---|
| 카메라 평행 SpriteRenderer | 보존 가능 | 평면 전체의 깊이만으로 3D 캐릭터/지붕과 부분 가림을 처리하면 오류 가능. 바로 대체하지 않음 |
| 공통 시트 + 카메라 평행 사각형 + 같은 원본 texel의 XYZ 깊이 | 보존 가능 | 공통 생성/정규화 후 원본 색은 그대로 읽고 깊이는 별도 계산. **최신2D 수정 경로**. 정수배 표시 허용 |
| Blockbench의 실제 모델 + 픽셀 UV | 파일 보존 가능 | 표면 texel 밀도는 통제 가능하지만 화면에서 사다리꼴/축소/가림이 발생. 자유 시점/모딩용 별도 후보, 이번 링크만으로 전면 전환하지 않음 |
| 기존 B35 면별 색 재투영 | 보존 불가 | 방향/치수 보정을 색 배열 변경으로 해결하므로 최신 요구에 부적합. 재사용 중단 |

## 5. 우선 후보의 좌표/변환 계약

canonical 원본은 자동 정규화 후의 RGBA PNG입니다. 이미지 원점은 왼쪽 위, u는 오른쪽, v는 아래입니다. 물리 기준은 Unity 건물 local X/Y/Z, m 단위이며 기존 pitch30°/local yaw45°를 유지합니다. 건물 world yaw305° + camera local yaw45° = camera world yaw350°입니다.

`R=(1,0,-1)/sqrt(2)`, `U=(1/(2sqrt(2)),sqrt(3)/2,1/(2sqrt(2)))`, `D=R×U`인 직교 기저를 사용합니다. R×U=D 관계를 명시하며 이미지 Y 반전은 U항에서 한 번만 합니다. 부모의 비균등 scale은 허용하지 않습니다.

```text
s = (u + 0.5 - pivot_u) / PPU
t = (pivot_v - v - 0.5) / PPU
X(u,v) = R*s + U*t + D*lambda(u,v)
dot(R,X) = s
dot(U,X) = t
```

`lambda`는 승인된 물체 proxy와 직교 광선의 교차로 구하는 깊이입니다. 이 계산이 색 C[u,v]의 주소/해상도/형태를 바꾸면 실패입니다. 불투명 texel의 ray가 proxy에 맞지 않으면 입력/깊이 저작의 오류로 귀속합니다. 임의 가까운 면으로 보내거나 색을 잘라내지 않습니다. 단일 그림에서 보이지 않는 형상이 자동 복원된다는 뜻도 아닙니다.

게임 화면 높이 H, 직교 카메라 half-height S에서 한 원본 texel의 화면 크기는 `k=H/(2*S*PPU)`입니다. k가 양의 정수이고 그리드 원점이 정렬될 때 정수 사각 셀 대응이 가능합니다. 동작/충돌 위치를 바꾸지 않고 기존 카메라 격자 소유자를 사용합니다. 임의 줌/시점까지 같은 보존을 약속하지 않습니다.

## 6. 절차와 실패의 반환 위치

`공통 오브젝트 시트 저작 → 시트 전체 자동 검출 → 정수 crop → 무변형 수입/정수배 표시 → 깊이 계산 → 기존 개체 연결 → 영향받은 최종 화면/가림 확인`

- 정규화 이후 resize/면별 color warp/강제 target grid를 넣지 않습니다.
- 화면 픽셀 부족이면 원본 저작의 세부 밀도 문제로 돌려보냅니다. 후처리 축소를 아트 제작으로 대신하지 않습니다.
- 최종 검사는 원본/표시 RGBA 대응, PPU/정수 화면 배율, alpha/depth 유효 영역, 지원된 시점의 부분 가림과 기존 출입을 변경 범위에서만 확인합니다. 이미 검증된 배치는 이유 없이 반복하지 않습니다.
- 픽셀/깊이 기술 검사가 그림체·비율·정보 전달력 합격은 아닙니다. 최종 관찰 단위를 보여 주고 사용자 판단을 받습니다.

최신 실행은 `Tools/Building36/graph.json`의 공통 시트 생성→전체 자동 정규화→정수 crop→필수 기술 확인입니다. 시트의 실제 모습과 기존 건물 적용 결과는 별도 관찰 단위입니다. 시트 재료 완료를 건물 적용 완료로 보고하지 않습니다.

## 7. 픽셀 회전: 도구, 수학, 실제 확인

2026-09-28 최신 요청: Aseprite 회전부터 확인하고 선분 회전 알고리즘과 다른 도구를 조사합니다. 이 절의 결과는 회전 기능 연구이며 기존 가구 원본을 임의각으로 보정하라는 승인이나 건물 통합 완료가 아닙니다.

### 기법과 적용 판단

| 대상 | 기법 | 확인 범위와 한계 |
|---|---|---|
| 이미지 전체의 90°/180° 회전 | Aseprite canvas 회전 | 로컬 90° 저장 실행. 적절한 출력 캔버스에서 정수 좌표 순열이므로 색과 픽셀 개수를 보존할 수 있음 |
| 이미지 전체의 임의각 평면 회전 | Aseprite RotSprite | 공식 기능/소스 확인. 윤곽에 맞춘 재래스터화이며 임의각 무손실·특징 보존을 보장하지 않음. 임의각 실행은 아직 하지 않음 |
| 선분/도형의 정확한 방향 저작 | 끝점 회전 + Bresenham | 좌표에서 픽셀 선을 새로 계산. 이미 채색된 오브젝트의 앞면/옆면·무늬·가림 정보 복원은 하지 않음 |
| 무료 편집기에서 평면 회전 | LibreSprite / Pixelorama | 공식 소스 확인, 로컬 실행/설치 안 함. LibreSprite는 RotSprite 구현, Pixelorama는 Rotxel·cleanEdge·OmniScale·nearest 등 선택 제공 |
| 바닥 위 가구의 방향 전환 | 방향별 sprite 또는 실제 형상에서 해당 시점 출력 | 이미지의 평면 회전과 구분. 새로운 방향의 노출면·가림 관계가 필요하며 단일 PNG만으로 정확한 숨은 면이 결정되지 않음 |

[Aseprite 공식 회전 문서](https://www.aseprite.org/docs/rotate/)는 선택영역을 pivot 주위로 회전하고 Fast Rotation/RotSprite를 고르는 기능을 설명합니다. [실제 RotSprite 소스](https://github.com/aseprite/aseprite/blob/main/src/doc/algorithm/rotsprite.cpp)는 Scale2x 3회로 내부 8배 공간을 만든 뒤 변환·재샘플링합니다. 이는 윤곽의 이웃 픽셀 관계를 이용하는 회전 알고리즘입니다. 완성 아트를 임의 저해상도로 축소하고 nearest 확대하는 방식으로 대체하는 근거가 아닙니다.

[LibreSprite 구현](https://github.com/LibreSprite/LibreSprite/blob/master/src/doc/algorithm/rotsprite.cpp), [Pixelorama 회전 구현](https://github.com/Orama-Interactive/Pixelorama/blob/master/src/UI/Dialogs/ImageEffects/RotateImage.gd)을 확인했습니다. 다른 도구가 가구의 3D 방향 문제까지 자동 해결한다는 뜻은 아닙니다. 이미 설치된 Aseprite를 우선 사용하며 대안 도구는 이번에 설치하지 않았습니다.

### 선분 계산과 좌표 계약

이미지 좌표는 x오른쪽/y아래, pivot은 c, 각도 단위는 radian입니다. 아래 행렬에서 양의 theta는 화면상 시계 방향입니다. 두 끝점에 같은 변환을 적용하고 같은 반올림 규칙으로 정수 격자에 양자화한 뒤 Bresenham 선분을 계산합니다.

```text
R(theta) = [[cos(theta), -sin(theta)],
            [sin(theta),  cos(theta)]]
p' = c + R(theta) * (p - c)
Aq = floor(A' + 0.5); Bq = floor(B' + 0.5)
pixels = Bresenham(Aq, Bq)
```

[Bresenham 원 논문(IBM Systems Journal, 1965)](https://ibm-1401.info/Pics3/bresenham1965.pdf)은 누적 오차에 따라 인접 격자점을 선택하는 정수 선분 알고리즘입니다. 대각 이웃까지 연결하는 선이므로 이를 모든 칸이 상하좌우로 연결되는 선이라고 혼동하지 않습니다. 면 채움/선 두께에는 별도 정의가 필요합니다. 붙어 있는 면들은 공유 꼭짓점을 한 번 계산해야 반올림으로 생기는 서로 다른 끝점을 피할 수 있습니다.

화면의 2:1 대각선은 `abs(dy/dx)=1/2`, 즉 약26.565°입니다. 프로젝트의 카메라 고도30°·수평 대각 시점45°에서 바닥 축은 `abs(slope)=sin(30°)=1/2`가 됩니다. **카메라 고도30°를 스프라이트 선분 각도30°로 넣지 않습니다.** 이미 정규 픽셀이어도 잘못 그려진 선의 방향은 정규화만으로 바뀌지 않습니다.

### 최소 실험과 증거

- 도구: `C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe`, 버전1.3.18.6-x64.
- 입력: `docs/artifacts/building35/native/crate/native.png`, 241×238. 원본을 변경하지 않았습니다.
- 실행: `Tools/Building36/check_aseprite_rotation.lua`에서 batch `app.command.Rotate {ui=false,target="default",angle="90"}` 후 별도 저장.
- 출력: `docs/artifacts/building36/rotation/crate-90.png`, 238×241. 원본 RGBA의 시계 방향90° 순열과 출력 RGBA가 정확히 같고 새 가시 색상은0개입니다. 자세한 경로/해시는 `aseprite-readback.json`에 있습니다.
- 기존 PixelLab 확장이 시작 시 `dlg nil` 오류를 출력했으나 회전 스크립트는 종료 코드0으로 저장했습니다. 확장 설정은 변경하지 않았습니다.
- [Rotate API](https://www.aseprite.org/api/command/Rotate)는 mask 회전이 UI 모드에서만 작동한다고 명시합니다. [명령 구현](https://github.com/aseprite/aseprite/blob/main/src/app/commands/cmd_rotate.cpp)의 canvas 작업은90°/-90°/180° 분기입니다. angle 인자가 있다는 이유로 batch 임의각 RotSprite 자동화가 확인됐다고 보고하지 않습니다.

### 결정, 미해결, 재개 조건

- 선/면의 방향 기준을 만드는 데에는 좌표→래스터 알고리즘을 사용합니다. 기존 가구 그림 전체를 임의 회전해 수직 기둥까지 기울이는 방식으로 바닥 방향을 보정하지 않습니다.
- 평면상 회전이 필요한 소품은 원본 정규화→회전 전용 알고리즘→별도 sprite로 한 번 저장하고 게임에서는 그 sprite를 표시하는 경로가 후보입니다. 여러 차례 회전한 결과에 다시 회전을 누적하지 않습니다.
- 이번 실제 실험은90°만 검증했습니다. 임의각을 제작 경로에 도입하려면 해당 각도/대표 소품의 별도 출력으로 선·세부 보존을 관찰해야 합니다. 현재 씬·색 텍스처·카메라에는 회전 보정을 적용하지 않았습니다.
