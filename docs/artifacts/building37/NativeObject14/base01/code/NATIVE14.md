# N14 — 편집 가능한 면 전개도에서 직접 픽셀 제작

## 현재 결정 · 2026-10-04

요청은 디자인·명암·세부를 갖춘 오브젝트 하나와 반복 제작 경로다. R13f는 선 기술 검사만 통과했고 원본의 암부를 제거해 색·입체감에 실패했다. 이번 입력은 같은 캐비닛의 새 생성 **표현 참고**이며, 최종 출력은 별도의 치수·부품·재질 recipe에서 제작한다. 기존 원본/출력/Unity는 보존한다. 완전 자동 의미 복원, 미술 승인, 게임 통합은 주장하지 않는다.

후보: (1) PixelLab reference edit → native 오브젝트: 구독 만료·가용량 0으로 실행 불가(기록 NativeObject14/PixelLabCandidate). (2) Blender/PBR 후처리: 숨은 깊이 추정과 과장된 프레임의 기존 반례가 남아 보류. (3) 생성 표현 참고 → 평면 부품 템플릿 → 원본 RGB 재료 palette → 직접 native raster: 채택. PIA의 palette/배치 동시 최적화와 달리 여기서는 배치를 template이 소유한다. 원본 PerfectPixel 격자 복원으로 표시하지 않는다.

## 제작 계약

- canonical은 `(x,y,z)` 정수 tick: 너비/높이/깊이. 기존 V7의 고정 30° 카메라 투영을 재사용: `u=2x-2z`, `v=-x-z-y`. 화면 기준 translation만 정수로 한다. ground 방향은 2:1, screen선 각도는 atan(1/2), 카메라 elevation과 혼동하지 않는다.
- 치수 template: 3개 flush 문짝, 평평한 상판/몸체/주춧대, 얇은 평면 금속 인레이, 손잡이·힌지. 문짝 테두리를 3D로 돌출시키지 않는다. 보이는 세 면의 전개도이며 숨은 면·임의 회전은 지원하지 않는다.
- template/치수 → 유한 면 polygon/part ID/UV/공유 edge ID → material palette/표면 lookup → edge raster → PNG. recipe가 구조·부품·치수·표현 재료를 소유한다. generated bitmap이 기하를 소유하지 않는다.
- UV는 같은 재질 면의 원본 위치를 조회한다. 문짝은 고정 모듈 폭; 모듈 수가 바뀌어도 한 문짝/손잡이를 늘리지 않는다. 상판 재료는 고정 길이 주기로 조회한다. 원본 그림 전체 축소·비등방 scale·warping으로 각도를 맞추지 않는다.
- 목재 4색, 앞면/옆면 각 3색, 금속 3색: 지정된 원본 표면의 관측 RGB medoid. 모든 재료색은 검정 제외. 색 가까움은 Lab 거리로 판정한다. RGB를 바꾸는 새 조명/연속 광량/halo 삭제/밝은 근접색 대체는 없다. 각 면의 암부와 상판 아래/문짝·주춧대의 구조 명암은 독립 비검정 색 역할이다.
- 구조선 `E`는 공유 정점/유한 edge/문짝 seam 데이터로 **색칠 전에** 만든다. Bresenham 한 픽셀 경로만 허용한다. 가려진 선/삼각형 분할선/재료 나뭇결에 선을 만들지 않는다. 최종 검정 mask `B=(alpha>0)&RGB==(0,0,0)`는 반드시 `B==E`. 최종 색에서 E를 역산하는 검사는 금지한다.
- 구조선과 금속 인레이/나뭇결은 서로 다른 역할이다. 장식은 금속색 한 줄이며 검정이 아니다. shared corner에서 path가 합쳐지는 것은 허용하되 parallel duplicate edge, thickened line, 끝점 자유 연결은 금지한다. 접합부 2×2와 독립선 폭 검사를 구분한다.
- alpha는 geometry가 0/255로 한 번 결정한다. final native PNG에는 후속 resize/antialias/추가 pixel renderer가 없다. 확대 PNG는 표시용 nearest 정수 배율이다.

## 반례·최소 실험

1. base 3문짜리 한 개: 실제 PNG, palette별 tone support, 상판/암부/앞·옆면/힌지/손잡이/장식 존재, 순수 검정 E 일치, 공통 투영 확인. 미술 합격은 기술 검사로 대체하지 않는다.
2. 같은 recipe 2문 variant: 문짝·손잡이·힌지의 native local pixel geometry 동일, 단지 모듈 하나 제거. 이미지 늘이기 없이 부품 치수의 모딩 가능성을 확인한다.
3. 실패 fixture: fill palette에 black이 들어오면 거절; 동일 edge가 두 번 정의되면 거절. boundary midpoint 이웃을 보간/밝은 팔레트로 채우지 않는다.

WorkLoop의 geometry/material/raster/validation 노드가 실제 계산을 호출한다. 기술 실패는 담당 단계로 귀속하고 최종 판정을 blocked로 남긴다. 생성 기준 변경은 새 버전이며 몰래 재시도하지 않는다.

## 근거와 한계

- [OpenCV drawing](https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html): LINE_8 유한 정수 raster. 이번에는 외부 dependency 없이 표준 Bresenham을 구현한다.
- [Pixelated Image Abstraction](https://gfx.cs.princeton.edu/pubs/Gerstner_2012_PIA/index.php): 배치와 palette 최적화 연구이며 lossless 정규화나 인간의 미적 합격 보증이 아니다. 이번 구현은 그 논문의 알고리즘 구현이 아니다.
- [PixelLab edit-image](https://www.pixellab.ai/docs/tools/edit-image-pro): 연결됐지만 계정 generation은 실행하지 못했다.

이 방법은 **이미지에서 임의 오브젝트를 완벽히 자동 복원하는 알고리즘이 아니다**. 이 캐비닛의 template/표면 영역을 명시한 제작 경로다. 미술 세부는 생성 참고에 의존하고, 정확한 선/투영/치수/색 개수는 코드가 소유한다. 런타임 조명과 Unity 적용은 이번 작업 범위 밖이다.
