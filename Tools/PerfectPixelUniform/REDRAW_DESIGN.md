# R10 — 생성 원화의 선·영역·명암 재구성

## 현재 결정 (2026-10-03, 구현 포함)

요구는 생성 원화의 디자인을 유지하며 지저분한 경계·연속 색을 실제 정수
픽셀과 단계 명암으로 재작성하는 로컬 실행 경로다. 임의의 64×64 축소,
재확대, 축별 늘림, 카메라 변경으로 대체하지 않는다. 기존 lossless,
bounded cleanup, V9 캐비닛·Unity 상태는 보존한다.

R0 직접 원인: cleanup은 ΔE 상한 밖의 원본색으로 돌아가므로 팔레트 상한이
없다. legacy `region_tones + line_normalization`은 미검증 조합으로 차단돼
있다. Uniform04는 전체64색·원본 해상도 시험이고 영역별4톤 통합은 아니다.

### 후보와 선택

| 후보 | 입력→출력, 근거 | 결정·반례 |
|---|---|---|
| upstream 격자 추정→색 샘플링 | 이미 존재하는 격자 후보를 추정 | 연속 원화에 원래의 격자가 있다는 증명 없음. 색/선 재작성은 하지 못함 |
| Pixelated Image Abstraction | SLIC 기반 공간·색 공동 최적화→작은 팔레트 그림 | 특징 보존 목적 참고. 작은 출력 크기를 먼저 정하는 그대로의 구현은 이번 요구와 다름 |
| 선 후보→재질 후보→단계 색→공통 격자 재래스터화 | 아래 R10 수학 계약 | 격리된 prototype으로 채택. 의미 추정과 정확한 격자 계산을 구분 |
| 알려진 모델·분리 패스→픽셀 | V9처럼 형상·법선·재료가 있는 입력 | 정확한 기하/재조명 가능. 임의 원화의 숨은 형상을 복원한 것으로 대체하지 않음 |

R10은 논문 전체의 복제나 의미 해석의 완벽성 증명이 아니다. 추론한
재질/선 후보는 가설이고 격자·색 선택·렌더는 결정적 계산이다.

## 수학과 공간 계약

입력 `I[y,x]`: RGB/RGBA uint8, 원본 좌표 x→오른쪽, y→아래, 좌상단 원점,
texel 중심 `(x+.5,y+.5)`, 최대4MP. 원본 파일 바이트를 별도 보존한다.
정규 표현은 `material_id`, `tone_id`, `line_mask`, `alpha`, 팔레트다.
리깅/본/숨은 면은 적용 대상이 아니다.

1. **입력 분석**: 이미 동일 RGBA 블록의 격자가 증명되면 기존 무손실
   규격 복원을 먼저 쓴다. 그 외에 원래 grid를 복구했다고 주장하지 않는다.
   이번 R10은 정확 반복의 증거가 없으면 source1px에서 재작성한다.
   불규칙 원화의 추정 pitch→재래스터화는 다음 연구 단계이고 구현하지
   않았다. 수동 W×H를 받지 않으며 source grid 결과를 별도 보존한다.
2. **선과 영역**: 어두운 ridge를 구조선 *후보*로 구하고 좁은 폭의 중심을
   Zhang–Suen thinning으로 구한다. 밝은 ridge는 선으로 덮지 않는다.
   어두운 금속 반사대와 진짜 홈은 단일 RGB로 유일하게 분류할 수 없으므로
   해당 후보를 semantic truth로 기록하지 않는다. 최종 구현은 양측 재질
   후보 일치·색도차≤8·양측 색도≥8을 추가하고, 중성 반사대가 의심되는
   후보는 승격하지 않는다. 유색 금속도 완전히 판별한다는 보장은 없다.
   밝기 띠는 ramp에 남기며 line mask와 명암 지도를 별도로 출력한다.
3. **색**: CIELAB 색도에 따른 재질 후보 `m`을 결정적으로 군집화한다.
   재질마다 명도 축을 3 또는4단계로 나누고 실제 원본 RGB의 대표값을
   `P[m,k]`로 선택한다. 최종 색 `C=P[m,k]`; bounded cleanup의 원본색
   fallback, 디더링, RGB 혼합은 없다. 저대비 후보와 동색 재질은 의미가
   확정된 분할이 아니며 confidence/오차를 기록한다.
4. **격자 출력**: `source=(p*(u+.5),p*(v+.5))`, 축마다 같은 전역 p와 원점.
   region/tone 소유권을 같은 셀에 대응시키고 contour는 정수 선마스크로
   다시 그린다. 이번 R10은 vector polyline fit이나 Bresenham 재투영까지
   구현한 것이 아니다. RGBA 이미지를 resize해서 색/선/alpha를 섞지 않는다.
   원화에 없는 slope를 강제로 넣거나 부위별 offset/scale을 더하지 않는다.
   구현된 pitch>1 경로는 정확 반복 입력의 격자 복원 뒤 재작성이고,
   후속 색/alpha 변경까지 무손실이라는 뜻은 아니다. 향후 **추정 격자
   재작화** 후보는 작은 특징·연결성·곡선의 명암 띠가 손실되면 채택하지
   않아야 한다. 현재 입증된 pitch가 없으면 source1px 결과를 제출하되
   공통 logical grid 정규화 성공이라고 표시하지 않는다.
5. **투명도**: 선택된 alpha128 coverage는 antialias를 제거하는 유손실
   규칙이다. 투명도 변경/소실 수와 silhouette 연결 성분을 기록한다.
   원본 alpha를 그대로 보존했다고 주장하지 않는다. RGB 입력의 배경을
   자동 투명화하지 않는다.
6. **표시**: native PNG와 정수 repeat 비교 그림을 별도 저장한다. 비교판을
   native/Unity 입력으로 사용하지 않는다. 원본→native 변환은1회뿐이다.

각 후보는 원본 폭·높이, 양 축 pitch, 중심과 셀 경계, area/crop 정책,
내부 대표색 수와 실제 최종색 수를 기록한다. source→native는 전역 uniform
scale이며 비선형 warp 없음. 셀 round-off가 최대 p/2라는 사실은 특징
보존 증명이 아니므로 별도 가는 부위/연결성과 재료 대비 관측이 필요하다.

## 분리된 조명 계약

`I=R⊙S`에서 양수 g에 대한 `R'=R⊙g, S'=S/g`도 같은 I다. 원화 한 장의
어두운 나뭇결과 실제 그림자는 단일하게 분리할 수 없다. 금속은 specular
항까지 있어 normal/roughness/view/light가 필요하다.

현재 prototype은 **원화의 명암을 스타일 단계로 보존**한다. `tone_id`는
albedo나 법선이 아니며 baked lighting을 제거했다고 기록하지 않는다.
게임 조명을 받을 때는 별도 light band `b`로 ramp의 단계만 이동하고,
색 광원도 유한 LUT에서 최종색을 선택하는 계약을 사용한다. 단순 RGB 곱셈은
팔레트색 수를 다시 늘린다. 이 도구의 조명 미리보기는 band 이동 실험이며
Unity 통합이나 방향성 재조명 완료가 아니다.

물리적 재조명은 동일 형상/카메라의 albedo, normal, depth, material,
AO, shadow, specular 분리 입력이 있어야 정확해진다. 모델 추정맵만으로
단일 이미지의 진짜 물리 재료를 복구했다고 판정하지 않는다.

고정 camera30° 계약은 변경하지 않는다. 이미지 평면90° 회전은 정수치환이
가능하지만 쿼터뷰 물체의 월드 yaw 회전과 다르다. 다른 면이 보이는 회전은
방향별 원화나 알려진 기하를 같은 카메라로 재투영해야 한다.

## 판별 실험·실패 기준 (실행 전 고정)

- 동일 격자 fixture: 이미 정규 픽셀인 input의 위치/실루엣을 불필요하게
  재생성하지 않는다. 실제 반복 증거와 grid1 해석을 구분한다.
- 얇은 손잡이/곡선 금속 fixture: 연결선1px, 내부 단조 명암4단계가 서로
  다른 마스크에 남는지 검사. 밝은 띠를 검은 선으로 만들면 실패다.
- 실제 원화: 이전 사용자 입력1489×1056 sprite sheet1회. 원본 SHA,
  라인/영역/단계 지도, native/정수 비교판, source/output 색 수, alpha
  변화, 후보 grid 탈락 이유, 단계별 시간을 남긴다.
- 색 수 상한/정수 격자/정렬만으로 디자인 합격이나100% 자동 복원을
  선언하지 않는다. 실제 결과를 함께 제출한다.
- 실패한 grid 후보는 source1px 결과로 조용히 성공 처리하지 않고,
  report의 `grid_status`에 미해결을 명시한다. 색·선 재작성 단계와 전체
  정규화의 기술 판정을 분리한다.

## 1차 연구 자료

- [Gerstner et al. Pixelated Image Abstraction (2012)](https://gfx.cs.princeton.edu/gfx/pubs/Gerstner_2012_PIA/Gerstner_2012_PIA_full.pdf): modified SLIC와 팔레트 공동 최적화. 원화의 semantic 복원 보장은 아님.
- [Kopf/Lischinski Depixelizing Pixel Art (2011)](https://johanneskopf.de/publications/pixelart/): 작은 기존 픽셀→벡터. 이번 입력과 방향은 다르며 연결성 보존 관점을 참조.
- [Kang et al. Flow-Based Image Abstraction (2009)](https://www.umsl.edu/~kangh/Papers/kang_tvcg09.pdf): ETF/FDoG 경계 방향. 모든 response가 구조선은 아님.
- [Winnemöller et al. XDoG (2012)](https://research.adobe.com/publication/xdog-an-extended-difference-of-gaussians-compendium-including-advanced-image-stylization/): 다중 scale 선 후보. 금속 highlight의 의미 판정은 아님.
- [EPFL SLIC/SLICO](https://www.epfl.ch/labs/ivrl/research/slic-superpixels/): 지역 군집화와 semantic material 분할의 차이.
- [MIT Revisiting Intrinsic Images](https://rin.csail.mit.edu/): 단일 RGB의 albedo/shading 비유일성과 사전조건.
- [Woodham photometric stereo](https://www.cs.ubc.ca/~woodham/papers/Woodham80c.pdf): 동일 표면·알려진 독립 광원·반사 조건이라는 추가 입력.
- [Unity Secondary Textures](https://docs.unity3d.com/kr/current/Manual/urp/SecondaryTextures.html), [2D Light properties](https://docs.unity3d.com/kr/6000.0/Manual/urp/2DLightProperties.html): normal/mask 지원은 이미 baked된 빛 제거 기능이 아님.

## 실제 결과·재개

`docs/artifacts/building37/Redraw10/`에서 실제 실행했다. WorkLoop의
prepare→render→validate 3단계가 완료됐으며 실제 시트 기술 검사21개가
통과했다. 원본1489×1056 그대로, visible RGB154,249→48. 분석0.104초,
재작성2.393초(색0.861초+선1.499초 포함); 이 수치는 파일 저장·검사·
WorkLoop 시작을 포함한 전체 시간과 다르다. 원본파일과 숨은 RGB는 보존했다.
alpha128 규칙으로 반투명578,487px가 바뀌고 nonzero alpha73,742px는
제거됐다. threshold128 기준 silhouette 연결 성분19개는 같다.

후보48,892px 중15,560px만 선 처리 후보로 채택했고33,332px는 보존했다.
가늘게 고정된 선11,082px, 주변영역 재배정4,478px, 미해결halo0px다.
재질색으로부터 후보를 고르는 것이며 semantic 선/재질 인식 완료는 아니다.

독립 곡면 금속/2px 손잡이 fixture, 어두운 중성 금속 반사대 fixture,
native 무변경, 반복3px/잘린 가장자리, 3단계 RGB 입력, 잘못된 단계 거부를
각각 확인했다. V4 HTTP 경로에서도 어두운 금속 fixture를 처리·검사·
다운로드했다(0.224초; 작은192×128입력, 전체 시트 속도와 다름).
`web-test.json`, `fixture-validation.json`에 직접 결과를 보존했다.

**전체 원래 격자 정규화는 미해결이다.** 이 실제 시트에는 정확 반복의
증거가 없어 `uncertified_source_lattice`이며1px 좌표에서 다시 그렸다.
48색이라고 native logical pixel 크기와 긴 대각선 리듬까지 복구한 것은
아니다. 원본에 존재하는 빨강/파랑 테두리와 카메라 오차도 자동으로 의미
판별해 제거·보정하지 않았다. 새 결과는 색·선·명암 재작성 prototype이고
사용자 미술 승인이나 Unity 통합 결과가 아니다. V9 current.json은 유지한다.

다음의 원인별 재개는 (a) 원화에 logical grid를 확정할 증거/저작 가이드가
있으면 공통격자에 region/contour를 재래스터화, (b) 잘못 승격된 유색 금속
ridge가 관측되면 그 후보의 분류만 수정, (c) 물리 조명이 필요하면 동일한
기하의 albedo/normal/depth 패스를 입력으로 추가하는 것이다. 상위 원화에
없는 정보는 임의의 축소·회전·색 재생성으로 만들어 완료 처리하지 않는다.

실행: `redraw_cli.py --source <PNG> --output <새 workspace 폴더> --levels 4`.
웹: `Start_Uniform_Web.cmd` 또는 http://127.0.0.1:8768/ → 선·영역 재작성.
작업 단위의 결정적 계산에는 모델/API 호출이 없다.
