# L11 — 옛 수정판의 명암 양자화 재사용

## 현재 결정 (2026-10-04)

사용자 요청: “수정판으로하면 어떻게되는데? 양자화가안됐는데?
옛날에수정했던거로해보던가”. 같은 실제 시트에 옛 코드를 실행한다.
새 양자화 알고리즘이나 Unity 적용을 이번 실험으로 대체하지 않는다.

출처는 `LocalOnly/PerfectPixelPalette_20260906`의
`PALETTE_LAB_README.txt` review04~06과 `src/perfect_pixel/color_ranges.py`다.
기본 `PaletteOptions.tones_per_family=3`, 지원 상한 4를 각각 실행한다.
`build_color_ranges`는 원본의 HSV 색상환을 기본 15도 범위로 나누고,
각 범위의 Oklab L을 최대 N단계로 묶으며 실제 원본 RGB를 대표색으로 고른다.
중성색은 별도 범위다. 색 범위는 물체·재질·공간 영역의 정답이 아니다.

## 고정 조건과 비교

- 원본 SHA: `e4eb81a6bb53708a807e7eb182bfaa10bc39e37a5ed337c7913384323172d1ae`.
  입력은 기존 웹 실패 기록의 1489×1056 RGBA 시트다.
- 좌상단 원점, x는 오른쪽/y는 아래, texel 중심 `(x+.5,y+.5)`.
  원본→출력 좌표변환은 항등이다. 모든 alpha>0 픽셀을 양자화하며 알파는
  그대로 보존한다. 예전 전체 래퍼의 alpha128 이진화·격자 vote는 사용하지 않는다.
- canonical은 `family_map`, `tone_labels`, 실제 원본 RGB 팔레트와 원본 alpha다.
  출력 `RGB[y,x]=palette[tone_labels[y,x]]`; 리사이즈·보간·경계 refine 없음.
- 기존 API에서 색/톤 선택만 재사용한다. `clean_tone_labels`, 격자 추정·샘플링,
  line_first, R10 선 처리, 명암 제거, 리깅은 적용하지 않는다.
- 원본·V4·옛 엔진은 보존한다. 엔진 코드 해시와 실제 실행 파일을 기록한다.
- 바뀌는 변수는 범위당 최대 톤 수 3/4 하나다. 전체 시트를 각각 1회 처리한다.

가설: 예전 양자화만으로 연속 명암이 범위별 3/4단계로 바뀐다.
색/명암의 단계화는 예상하지만 불규칙 선의 재작도까지 해결할 것으로
가정하지 않는다. 불규칙한 선이나 알파 halo가 남으면 해당 단계의 공백이다.
격자 복구나 미술 합격으로 승격하지 않는다.

후기 `continuous/spatial_steps`는 가변 K를 선택하는 다른 경로다.
`legacy_regions`는 최대 3톤이며 native 크기 base_grid는 자원 한도를 넘는다.
`region_tones + line_normalization`은 기존 코드가 미검증 조합으로 거절한다.
이 제한을 패치하거나 임의 축소하여 이번 시험을 성공시켜서는 안 된다.

## 실행과 판정

`legacy_tones_trial.py run`은 WorkLoop의 prepare→quantize→validate를 실행한다.
완료 판정은 실제 옛 API의 결과, 범위별 톤 상한·원본 RGB 출처·알파·좌표·
원본/코드 해시 보존으로 한정한다. 비교 미리보기는 같은 ROI의 정수 nearest
표시만 사용하고 제작 입력으로 되돌리지 않는다. 외형은 실제 비교 이미지로
제출한다. 이 실험은 웹 기본 엔진이나 Unity 제작 자산을 교체하지 않는다.

## 실제 결과

WorkLoop prepare→quantize→validate를 한 번 완주했다. 같은 전체 시트에
범위별 3단계/4단계를 각각 한 번 실행했고, 원본 154,249 visible RGB가
74/98개로 줄었다. 색 선택+lookup은 각각 1.371/1.453초로, 파일 저장·검사·
프로세스 시작 시간은 제외한다. 20개 기술 조건이 통과했다. 원본과 옛 엔진
코드 해시·1489×1056·모든 알파·숨은 RGB를 유지했으며 평균 RGB는 출력하지 않았다.

`docs/artifacts/building37/Legacy11`에 native-3/4.png, 같은 ROI의 표시용
2배 비교본, 영역/톤 NPZ, 실제 옛 코드와 실행기 snapshot, receipts,
validation, WorkLoop 상태를 보존했다. 기존 source.png와 V4 결과를 참조한다.

가설의 좁은 결과는 지지한다: 옛 양자화는 명암을 실제 단계화한다.
그러나 비교에서 약한 나뭇결이 넓은 단색으로 합쳐지고 경계 잔색이 남는다.
색상환 범위는 연결된 면/나뭇결/구조선 구분이 아니며, 이 API는 같은
범위 안의 명도만 묶는다. 불규칙 선 재작도와 정확 logical grid 복구는
계속 미완료다. 색수 감소와 상한 검사만으로 픽셀아트 완성이라고 하지 않는다.
