# R13 — 원화 캐비닛의 구조선·면·장식 재작도

## 실행 전 계약 (2026-10-04)

사용자 요청: 기존 생성 사물 시트에서 한 개를, 넓은 범위에서 감지한 선을
출력 격자에 다시 그리는 방식으로 끝까지 제작한다. 실루엣·면 명암·나뭇결·
금속 장식·손잡이를 함께 남긴다. 원본 격자를 찾지 못했다고 임의 슬롯 크기로
축소하는 정규화와는 다른 **디자인 재작도**다. 원본 PerfectPixel의 손실 없는
격자 복원 기능이나 그 알고리즘 자체를 수정하는 작업이 아니다.

입력은 `docs/artifacts/building37/Redraw10/source.png`, SHA-256
`e4eb81a6bb53708a807e7eb182bfaa10bc39e37a5ed337c7913384323172d1ae`,
1489×1056 RGBA이며 첫 캐비닛 ROI는 `[16,22,340,314]`이다. 디자인·배색은
이 실제 원본을 기준으로 한다. 원화에 없는 장식/형상은 추가하지 않는다.
원본·R10·L11·웹 기본값·Unity·카메라는 보존한다.

### 선택과 반례

R12의 C/E 후보를 작은 캐비닛에 적용한다. 전체 색 양자화 B는 이미 낮은 대비
나뭇결을 지운 증거가 있으므로 단독 경로로 사용하지 않는다. 출력 크기를
지정하는 이미지 축소 D도 이번 제작 경로로 쓰지 않는다. Hough→robust TLS→
공유 방향/교점→정수 선은 확정 기하에 적용하고, 곡선/짧은 장식에는 직선을
강제하지 않는다. 목재/도장/금속 역할의 source 색 분류는 이 자산의 입력 계약이며
모든 사물을 이해하는 보편적 의미 추론기가 아니다.

공통 방향을 강제할 때 원본의 두 사선을 모두±0.5로 바꾸지 않는다. 측정한
방향을 사용한다. 긴 선을 합쳐 손잡이까지 지우거나, 금속 반사띠를 문 구분선으로
오인하거나, 최소 장식 폭이 격자에서 사라지면 해당 단계의 실패로 남긴다.

### 좌표·정규 표현

- 원본 pixel-corner 원점, x→오른쪽/y→아래, texel 중심 `(x+.5,y+.5)`.
- ROI는 분석 범위이며 원본 좌표는 receipt에 유지한다. 격자 origin `o`와
  단일 pitch `h`를 모든 면·선·장식에 사용한다. 비균일 scale은 없다.
- 출력 중심 `p=o+h*(u+.5,v+.5)`. 중심선은
  `floor((p-o)/h)`로 가장 가까운 출력 중심에 대응하며 정확한 반간격 동률은
  양의 좌표 쪽으로 고정한다. 면 coverage는 그 연속 다각형에 대한 texel 중심
  포함 검사다. 선 snap을 각 면 경계에 따로 적용하지 않는다.
- canonical 데이터: silhouette/face polygon, 공통 방향의 구조선, 작은 장식
  mask/contour, 역할·tone ID와 관측 RGB 팔레트. sourceRGB는 immutable이다.
- 한 edge/vertex가 여러 면에 공유되면 하나의 권위 좌표를 참조한다. 외곽과
  면 경계는 depth를 조작하는 대신 2D 소유권 순서(면→구조선→전경 손잡이)를
  사용한다. 실제 최종 role이 선 mask의 권위다. 배경 문틀이 손잡이를 덮지 않는다.
- LINE_8/Bresenham으로 선을 한 번 그린다. AA/blur/실수 alpha를 출력하지
  않는다. opaque 캐비닛은 alpha 0/255이고 hidden RGB는 0이다. 유리·발광
  투명재료는 이번 닫힌 캐비닛의 대상이 아니다.

### 단계와 판정

1. **geometry:** 원본 크기에서 역할 mask·큰 contour·긴 선 후보를 만든다.
   직선은 Hough 후보의 source support에서 robust fit하고 방향별 공통 기저를
   사용한다. 작은 금속/손잡이는 후보 선의 길이 제한에서 제외한다.
2. **grid:** pitch 후보는 source px 단위 2~4를 평가한다. 작은 장식의 최소3셀 폭·
   12셀 지지와 주 금속 띠의 최소3셀 폭을 관측한다. 이는 명암/경계의 공간 예산이며
   source에 없는 세 번째 반사색을 강제하는 조건이 아니다. 조건을 만족한 가장 큰 pitch를
   선택한다. 불확실한 원래 저작 pitch를 복원했다고 주장하지 않는다.
3. **detail:** source면의 명도 기저와 방향 잔차를 분리해 목재 무늬를 tone ID에
   반영한다. 면/재료별 4단계와 경계/금속의 별도 ramp를 사용한다. 대표 RGB는
   실제 source 표본이며 RGB 잔차를 다시 더하지 않는다.
4. **raster:** 같은 격자에서 면·장식·적합 선·실루엣을 한 번 조립한다.
   출력 PNG를 다시 축소하거나 늘리지 않는다. 정수 확대는 표시용 파일이다.
5. **validate/package:** source SHA, binary coverage, 역할 palette,
   비대칭 선/짧은 특징 fixture, 실제 손잡이 분리·구조·grain 유지와 native/정수
   미리보기를 함께 제출한다. 색수·파일 존재만으로 디자인 합격을 대체하지 않는다.

WorkLoop `command.run` 노드로 위 계산을 연결한다. 입력·코드 해시와 오류 단계가
고정된다. 실패를 다시 시도해 지우지 않는다. 원인 단계의 구현 버그가 발견되면
그 실행을 보존하고 새 실행으로 해당 원인의 수정 근거를 남긴다.

### 표준 기술과 독자 연결

[OpenCV Hough](https://docs.opencv.org/4.x/d9/db0/tutorial_hough_lines.html),
[robust fitLine/contour](https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html),
[LINE_8/fillPoly](https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html)가
후보·적합·정수 래스터의 단계 근거다. 기존 로컬 OpenCV 5.0.0과 NumPy/Pillow를
사용한다. 문서 4.x의 일반 연산을 사용하며 5.0 고유 기능에 의존하지 않는다.
그 기능만으로 source의 재질 의미를 알아내는 것은 아니며 역할 분류/공통
topology/특징 budget과 grain 역할 연결은 본 실험의 독자 구현이다.
무늬 역할 분리는 [flow 기반 추상화](https://pages.cs.wisc.edu/~dyer/cs534/papers/kang_tvcg09.pdf)의
방향성 아이디어를 참고하되 논문 전체 재현이라고 주장하지 않는다.

이번 원본의 명암을 참고해 픽셀 명암을 만드는 것은 순수 albedo 복원이나
Unity 재조명 성공의 증거가 아니다. 미술적 “AI 티 0%”도 자동 검사로 증명하지
않으며, 실제 그림을 숨기지 않고 제시한다.

## 실제 결과

최종 실행은 `docs/artifacts/building37/Redraw13e`이며 [실제 비교](../../docs/artifacts/building37/Redraw13e/comparison.png),
[native](../../docs/artifacts/building37/Redraw13e/native.png),
[4배 표시](../../docs/artifacts/building37/Redraw13e/preview-x4.png),
`geometry.json`, `detail.json`, `validation.json`, `execution.json`과 단계별 배열/
코드 snapshot/WorkLoop 상태를 함께 보존했다. 원본은 전체 시트가 아니라 분석한
캐비닛 ROI를 비교한다. **22,489 visible RGB→17 visible RGB**, 162×141 RGBA,
alpha0/255, source2px pitch다. 이는 재작도 격자이며 원래 저작 격자 검출 성공이 아니다.

- 33개 금속 구조선 후보를 공통 방향 family에서 적합했다. 두 사선 기울기는
  약−0.51206/+0.55120이며 원본에서 측정한 방향을 유지했다. 카메라를 바꾸지 않았다.
- 목재/앞면/옆면은 각각4단계, 금속4색과 실제 source 암부 경계색1개다. 새 나뭇결
  줄을 생성하지 않고 source 방향 잔차가 tone ID에 영향을 주도록 했다. 좁은 선은
  정수1px stroke이며 넓은 금속과 곡선/짧은 장식은 별도 표현이다.
- 어두운 금속 색이 저채도라는 원본 표본을 확인해 색 분류를 보완했다. 작은 금속
  두께 core를 Hough 전에 분리하여 손잡이가 평면 경계선의 투표/삭제 대상이 되는
  원인을 제거했다. 실제3개 지지 cluster가47/26/23셀·각4색으로 남았다. 이3개가
  개별 손잡이3개라는 의미는 아니다. 오른쪽의 두 손잡이를 포함하는 cluster가 있다.
- source paint의 구조선 corridor **11,231px**를 재샘플링 후보에서 제외했다.
  주변의 같은 면 source 표본으로 채우고 선을 다시 그린다. source의 흐릿한 선과
  새 선을 단순 중첩하는 R10 방식과 다르다. 목재의 무늬는 이 corridor에서 제외한다.
- 금속 중간 기둥에는 실제2명암이 남고 손잡이에는4명암이 남는다. 모든 금속에
  3~4띠가 생긴다고 주장하지 않는다. 원본 끝 장식의 폭 변화를 제한된 원본 영역에서
  보존하며 새 장식을 만들어 넣지 않는다.
- 실제 output·선 위치·vector stroke·선 소유권·source 팔레트/halo·금속 명암·
  특징 위치/관계·정수 확대를 포함한 **19개 기술 조건**이 통과했다. 작은 특징의
  source좌표 centroid 이동은0.69/0.95/1.11sourcepx(0.35/0.48/0.55nativepx)다.
- 최종 ink/trim 전체1,051/719셀의 적합 선까지 최대 거리는0.945/0.733nativepx다.
  거리 조건에 맞는 픽셀만 사전 선택해 검사하는 방식으로 통과시키지 않았다.
- 전체 WorkLoop4노드 실행은 **2.909초**(subprocess 시작/검사 포함)였다. 실제 생성
  호출0회다. 같은 실행을 다시 호출했을 때 해시 확인 후 `cached:true`를 반환하고
  제작을 반복하지 않았다. AI가 연구/코드를 작성하는 시간은 이3초에 포함되지 않는다.

별도 복사본의 native PNG를 고의로1byte변경한 반례에서는 캐시가 거부되고
제작을 반복하지 않았으며 실제 최종 PNG의 SHA는 그대로였다(`cache-negative.json`).

독립 검토가 확인한 최종선 mask의 오래된 소유권, source 암부 corridor 재유입과
작은 특징의 연결 판정 공백을 수정했다. `Redraw13`, `Redraw13b`는 중간 결과이며
`Redraw13c`는 수정 전 연결 검사에서 blocked된 상태를 코드와 함께 보존했다.
그 검사는 source에서 이미1px 간격/접촉하는 material support를 의미상 독립한
손잡이로 오인했다. source관계를 먼저 측정하는 계약으로 수정했으며 임의 간격을
새로 그려 통과시키지 않았다. d→e는 전체 선 위치 검사 보강이며 native 바이트가
같다. 재개용 최종은 **Redraw13e** 하나다.

### 반복 실행

프로젝트 루트에서 `Tools/PerfectPixelUniform/Run-Redraw13.cmd`를 실행한다.
기본 출력은 source+code hash로 고정된 `LocalOnly/PerfectPixelUniform/R13-…`다.
처음에는 계산하고, 이후 동일 입력에서는 파일 해시 확인으로 기존 결과를 반환한다.
다른 코드/입력이나 손상된 출력이 기존 폴더를 조용히 덮어쓰지 않는다.

```powershell
$pixelPython = 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $pixelPython -B Tools/PerfectPixelUniform/redraw13_cli.py
# 보존된 최종 결과의 캐시 확인
& $pixelPython -B Tools/PerfectPixelUniform/redraw13_cli.py --output docs/artifacts/building37/Redraw13e
```

`geometry→detail→raster→validate`는 WorkLoop의 고정 `command.run` 노드다.
실패하면 후속 계산을 실행하지 않고 담당 노드와 stderr를 보존한다. 이 캐비닛의
팔레트/형상 계약을 바꾸는 수정은 새 code hash와 새 output을 사용한다.

### 남은 범위

이 경로는 **이 source의 닫힌 목재/남색/금속 캐비닛**이다. convex silhouette와
역할 색 분류가 입력 조건이다. 다른 가구/곡면/유리/열린 선반에는 별도 적합성
검토와 역할/구조 계약이 필요하다. 원래 격자 자동 복원, reference게임과 같은
미술 완성도, 개별 장식의 의미100%, 모든 교점/인접선 합집합의 전역1px 폭,
순수albedo·Unity 조명/표시는 아직 확인한 것이 아니다. “AI 티0%”는 자동 검사의
합격 문구로 대체하지 않았다. 이 결과의 native/비교 이미지를 후속 수정의 기준으로
사용하며 형식적인 만족도 질문에서 제작이나 기록을 중단하지 않는다.
