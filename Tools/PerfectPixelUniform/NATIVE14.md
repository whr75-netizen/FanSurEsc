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

## 실제 결과와 실행

최종은 `docs/artifacts/building37/NativeObject14/delivery/native.png` **183×165, 14색, alpha0/255**다. `preview-gray-x4.png`만 회색 배경/정수4배 표시다. 2문143×145/3문183×165 결과와 실제 코드·recipe·UV·부품 ID·source palette·WorkLoop snapshot·해시를 같은 폴더에 보존했다. `appearance-reference.png`1315×1196은 생성 참고이며 native 원본과 혼동하지 않는다.

실제 geometry→material→raster→validation **3.309초**, 34조건 통과. 3문 검정1088px이 독립 가시 구조선 E와 동일(추가0/누락0). 각 유한선에2×2전면채움 없음, 공유 canonical edge 중복 없음, 가려진 부품선 없음, 2문/3문의 문·손잡이·힌지 치수/재료/UV 동일, 목재4색 support와 재료명암 분리, 검정fill/중복edge 실제 거절 fixture를 확인했다. 명암 색/14색/34조건이 미술적 완벽함을 증명하지 않는다.

첫 `base01`은 Pillow polygon fill과 Bresenham의 경계 tie가 달라 선에 surface owner가 없어서 차단됐다. 모든 면 perimeter를 같은 Bresenham으로 raster하도록 **기하 단계**를 수정했다. `base02`의 source quad는 잘못된 위치의 금속선을 포함했고 문 안쪽의 회색 사선이 생겼다. 원본 위 좌표 진단으로 실제 도장 내부 quad를 정정했다. module 숫자ID 차이를 물리 치수 차이로 오인한 검사도 semantic field 비교로 고쳤다. base03은 plane rail이 빠져 참고보다 평평해 실제 원본의 도장 rail/명암 구역을 추가했다. base04/첫final은 독립 검토에서 가려진 body선4px가 cap 내부에 다시 드러나는 결함을 찾았다. **surface owner→edge visibility→E** 순서로 수정했고, body candidate9점 중 실제 잘못된 검정4px만 제거됐다(나머지는 합법적인 cap선과 같은 위치). 이전 결과/실패/코드는 모두 남긴다.

빠른 재생성은 `Tools/PerfectPixelUniform/Run-Native14.cmd`다. 매번 새 `LocalOnly/Native14/<UUID>`에 저장하며 AI/웹/PixelLab 호출 없이 계산한다. recipe의 부품 치수·handle·`door_frame_ticks`·관측색 anchor와 UV를 편집한다. 새 디자인은 새 template/참고 영역 저작이 필요하다. 이 실행기로 모든 임의 사물을 자동 해석한다고 주장하지 않는다. 명령줄:

```powershell
& 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B Tools/PerfectPixelUniform/native14_cli.py --output LocalOnly/Native14/my-new-run
```

실행기는 기존 폴더 덮어쓰기를 거절하고 기술 실패 시 dependent stage를 중단한다. 사용자 미술 승인/AI티0%·임의 카메라·동적 조명·Unity import/Play는 미검증이다. 최종 이미지를 실제 표시했으며 형식적인 만족도 질문은 전송하지 않았다.

`cmd /c Tools\PerfectPixelUniform\Run-Native14.cmd` 실제 실행은 exit0/graph_complete, 3.286초다. `LocalOnly/Native14/7f1e6e521f4d4c628e8c2bd64bec45a2` native PNG가delivery와byte동일함을확인했다. Windows에서더블클릭한것으로표기하지않는다.
