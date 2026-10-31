# 63 — 최초 분절·영역 단계 감사와 경계 표현 / 공간 보정 미완

**62는 미채택 그대로다.** 이번에는 임계값·팔레트 수·색·RGB를 조절하지 않았다. 실제 호출 순서와 두 source의 경계를 분류하고, 색 범위를 실제 특징으로 잘못 부르지 않는 분리 adapter 및 공유 경계 그래프/측정 코드를 구현했다. **현재373셀의 실제 공간 보정은 실행하지 못했고 RGB 변경0이다.** 이를 정돈 성공이나 새 보정 후보로 표시하지 않는다.

보기: [단계와 원인 mask](INDEX.html), [66영역](REGIONS66.json), [140경계](LEGACY_140_EDGES63.json), [현373셀 모순](EQUAL_INPUT_DIFFERENT_OUTPUT63.json), [검증](VALIDATION63.json).

## 실제 순서와 처음 갈라지는 곳

`run62.py`는 원본 PNG/UV를 읽고 `region62.build_regions`를 호출한다. 이 함수는 **Lab 축별 범위 절단 → colour box code → cc4 → 대비 표지에 의한 추가 분리 → medoid → 같은 box의 palette 참조 공유** 순서다. 이후 `structure_components`로 기하 연결을 별도 읽으며, `resolve`가 `material/UV→range region→anchor→P[저장Q]`를 수행한다. 마지막으로 기존52셀에 선형 .55 선색을 적용하고 저장 배경에 합성한다.

실제 source 특징의 경계·코너를 먼저 추출하는 함수, 그 내부 색 영역의 공유 경계를 보정하는 함수는 **62에 없다**. 따라서 최초 인공 분절은 `build_regions`의 Lab 범위 절단이다. 이미 존재하는 hard-feature gate가 잘못 막아 실패한 것이 아니라, 그보다 앞선 특징/색 경계 단계가 구현되지 않은 상태였다. 팔레트 참조 공유는 RGB 공급을 바꾸었을 뿐 영역 모양·경로를 보정하지 않는다. `hasCertificateSeed`를 근거로 전체 연결 영역을 “certified feature”라고 이름 붙인 메타데이터도 과도했다. 표지 한 점/한 쌍은 그 영역의 전체 footprint를 증명하지 않는다.

Q는 독립된 조명 분류이며 이번 오프라인 코드 이전에 실제 renderer에서 계산되어 저장됐다. Q 계산이 독립/병렬이라는 사실을 순서 결함이라고 하지 않는다. 빠진 것은 **특징→색 하위영역의 기하 표현과 보정**, 그리고 그 결과를 보존하는 명암 경계 단계의 연결이다. 62에는 명암 경계 보정도 새로 호출하지 않는다. 기존 `old==Q` LUT 통과나 .55 외곽선을 이 누락의 원인으로 돌리지 않는다.

## 66영역과 140경계는 다른 입력

현재 373셀은 `renderer60-20261031T092325108Z` frame94다.

- UV colour-range66개가 화면에서는186개의 4연결 조각이다.
- 배타 분류: 다른 source 기하 구조에 걸치는 UV 영역37, 가시 조각 하나인 영역28, 단일 구조인데 화면에서 나뉘어 원인 미확정인 영역1. 겹치는 진단으로는 같은 구조 안에서 화면 분리가 관찰된 영역16개가 있다. 이16개와37개를 합산하지 않는다.
- 서로 다른 topology ID는 원본 구조 차이의 근거다. 그 자체가 가림·미술 가닥·독립 sorting owner의 증명은 아니다. UV 연결 영역이 화면에서 나뉘었다고 모두 같은 색으로 메우면 실제 가림을 침범할 수 있다. 현 frame94의 정확한 투영 경계 자료가 없어 가림/미표현/표본 간격을 완전히 분리하지 못했다.
- 색 범위 경계460변 / 공유 경로357개, 반면 저장Q 경계49변 / 공유 경로2개다. 현 분절을 모두 조명 Q의 문제로 다루면 다른 단계를 고치는 것이다. 이 경로 수가 미술적 특징 수를 의미하지 않는다.
- **같은 원본 RGB와 같은 Q인데 팔레트 출력이 다른 인접 쌍18개**를 확인했다. 전부 다른 재질 사이이며 재질별 범위/medoid가 차이를 만든다. 예: (223,226)–(224,226), 원본 둘 다 RGB(44,22,23), Q0인데 anchor(48,26,27)/(42,22,23), 출력(37,16,17)/(31,12,13)이다. .55 처리 전 수치이므로 외곽선 탓이 아니다. 이것을 고치려고 기하/영역 ID를 병합하거나 셀마다 최근접색을 다시 고르지 않았다. 서로 다른 구조에 같은 원본색이 있을 수 있다.

과거140 신규 경계는 다른 source `95d042f…`, source-known358셀의 같은 appearance/Q 쌍에서 측정한 것이다. 저장된 matched geometry와 대조한 배타 원인 분류는 다음과 같다.

| 원인 | 경계 수 | 처리 판단 |
|---|---:|---|
| 가림/투영 틈 근거 | 72 | 영역 단순화로 넘어갈 수 없는 경계 |
| depth-continuous 소유권 전환/겹침 | 15 | 다른 실제 구조와 미술 경계 여부를 구분해야 함 |
| 동일 전면 표면의 colour-range 분절 | 50 | 색 범위의 인공 경계다. 원래 그려진 무늬인지/단순 기울기인지 별도 source guide 필요 |
| 색 UV 재배치 대응 미확인 | 3 | 원본 기하 경로와 색 표본 UV를 동일하다고 취급하지 않음 |

기하 category 자체로만 보면 front/back63, gap11, depth-continuous15, same-front51이다. 앞 표는 두 재배치 셀의 경계3개를 별도 우선 분류해 수가 다르다. 표지로 확정한 특징 쌍은 이140쌍에 없다. “추가 경계”는 원본 특징이 아니라는 뜻도, 삭제 허가도 아니다.

이전 기하 자료는 source 표본368개와 matched된 다른 시각의 평가 geometry다. 최대 화면 대응오차(.001838,.001768)논리픽셀, 최대 depth오차5.52e-7m이며 **동일 capture frame은 아니다**. 원래 chart endpoint672개는 packet과 전부 일치한다. 색 UV는 index492·523 두 셀에서 selected geometry UV와 다르다. `geometryUV` 필드가 따로 있어 재배치 자체를 데이터 손상이라고 단정하지 않았다. 현 frame94에 과거 기하를 이식하지 않는다.

## 최소 변경과 재사용 범위

`shared_boundary63.separate_layers`는 source feature domain(현재 확정된 것은 caller가 공급한 가시 머리 소속), 미확정 하위 feature, colour-range region, source structure, occlusion owner, Q를 분리해 export한다. 색 범위 ID를 feature ID로 승격하지 않고, palette 공유를 공간 보정으로 간주하지 않는다. `childFeatureId=null`은 사람이 새 디자인을 반드시 그려야 한다는 뜻이 아니라 **아직 추출/투영하지 않았다는 상태**다. 자동 추출 가능한 원본 PNG 정보가 없다고 주장하지 않는다.

`shared_boundary63.trace`는 기존44의 공유 경계 원리를 임의 정수 label에 일반화했다. 각 변을 두 영역이 공동 소유하는 하나의 기록으로 저장하고, 실제 junction에서는 경로를 끊어 유지한다. 후속 보정이 입력의 모든 잡픽셀 위상을 무조건 동결해야 한다는 조건을 추가하지 않았다. 현재 colour-range460변과 Q49변이 정확히 한 번씩 저장된다. 얇은 띠의 양쪽 경계, T접합, 작은 구멍의 합성 반례는 경계 표현 과정에서 소실되지 않았다. **이것은 모양 변경 알고리즘을 완료한 결과가 아니다.**

R3의 원래 indexed `revision3/region-core.js` 파일은 명시된 옛 경로들에서 확보하지 못했다. 32 연구 색인의 R3 설명과 현재31의 후속 `regionCorrect31` 함수를 대조했다. 현재 함수는 Q(g) 뒤에서 제한적 명암 오차 내 perimeter E, 같으면2×2 corner C를 줄인다. R5 이후 동시 적용/원래 component 기준 수정이 있으므로 과거 in-place 오류가 지금도 있다고 꾸미지 않는다. 현재 함수에도 원본 곡선의 접선·가닥·색 특징 경로 목적함수는 없다. 함수 읽은 원문은 `CURRENT31_REGION_FUNCTION.txt`, 해시는 `REUSE_SOURCE63.json`이다.31은 변경하지 않았다.

44에서 재사용한 것은 source-supported 공유 경로, 양쪽 winding 일관성, 원래 input에서 제안한 뒤 동시 적용, fixed-reference-arclength 접선 검사와 source witness다. `flat-shade-boundary44`는 **색 특징 경계가 아니라 Q 경계**를 보정한다. 현재 색 영역의 누락을 대신 해결하지 않는다. 44를 새 프레임에 적용한 것처럼 표시하지 않았다.

## 얇은 특징·곡률/경로 기준과 실제 대조

보존할 것은 native source의 대비·연속 경로·가림 끝점/T접합의 근거다. 단지 작은 면적, 모든 원래 label의 hole/접합 수, material/triangle/UV seam 자체를 보존 대상이라고 승인하지 않는다. 얇은 띠는 양쪽 경로가 공유하는 폭/연결과 source witness를 함께 검사해야 하며, 한쪽 경계의 둘레 감소만으로 채택하지 않는다.

곡선 평가는 (1) source guide와의 양방향 위치 이탈, (2) **고정된 source arclength**에서 접선 흐름 오차, (3) span/run 진행과 역행, (4) 실제 protected junction/가림 끝점 및 얇은 경로의 유지로 나눈다. 접선 오차는44와 같은 `Σ ds·(1−(t_ref·t_span)^2)/Σds`다. 출력 변 수를 분모로 쓰지 않는다. 제곱 내적은 정확히 반대 방향으로 되짚는 경로를 구분하지 못하므로 source arclength 좌표에서의 역행량을 별도로 추가했다. 직선 위에서 갔다가 되돌아가는 반례는 접선 오차≈0이어도 역행1.414214를 검출한다. self-intersection에서 최근접 참조 대응이 애매할 수 있다는 한계도 기록한다. 격자 path의 길이·회전각/run도 기록하지만 참조가 없으면 “과잉 굴곡”의 정답값을 만들지 않는다. discrete right-angle 합을 연속 곡률이라고 부르지 않는다.

44의 저장된 실제 단색 반례에서 path4 접선 오차 .203877926→.171808151, 샘플 위치 최대 이탈 .799877799→.692588333논리픽셀을 재계산해 기존 결과와1e-12 이내 일치했다. 기존4셀 변경은11영역/6단독 셀을 그대로 유지한다. 무제약 실패는12영역/7단독 셀로 악화됐고, source-supported 얇은 연결을 자르는 path0은 기존 수용 코드가 기각했다. 이 때문에 단독6셀을 무조건 지우지 않는다. 그림을 직접 열어 확인했으며 이 부분적인 Q 경로 개선을 전체 미술 성공으로 확대하지 않는다.

## 현재 공간 보정을 멈춘 정확한 이유

현재 frame94에는 selected point의 primitive/UV/barycentric·색·g/Q·owner/depth와 geometry hash가 있다. 다음은 없다.

1. 같은 sourceId의 evaluated hair 위치 배열과 대응 view/projection/grid/screen sample 위치. 원본 indices/UV는59에 이미 있어 재수집할 필요가 없다. 예를 들어 hair8435정점의 위치만 약101,220bytes다. **과거 pose95의 평가 geometry로 대체하지 않는다.**
2. 양자화 전 source colour 경계를 screen에 대응시킬 contour/footprint, 가림 junction/corner의 근거. 이는 semantic 수동 정답이 필수라는 요구가 아니다. 원본 texture와 geometry에서 추출하는 구현이 아직 필요하다. 한 점 색이나 `hasCertificateSeed`는 전체 footprint가 아니다.
3. 실제 Q 공간 보정을 같은 현재 source에 검증하려면 연속 명암의 위치/가시성 표본 또는 source-guided isoline이 필요하다. 2×nearest로 복제된 최종960×544 픽셀은 독립 native 조명 표본이 아니다.

따라서 원본이 아닌 **62의 이미 양자화된 계단을 다시 fit해 원곡선처럼 쓰는 처방은 적용하지 않았다.** 구현 미완(원본 색/gradient의 특징 추출·계층화)과 자료 공백(현재 source 투영/미세 가시성)을 구분한다. 버퍼가 없다는 이유로 모든 오프라인 분석을 불가능하다고 하지 않았고, 가능한 분류·경계 그래프·기존44 반례 대조는 끝냈다. 현재 RGB는 그대로이며 신규 임계값 탐색·팔레트 pooling 처방·작은 영역 삭제·색 블러는0회다.

## 재생·보존

`python -B audit63.py`와 `python -B validate63.py`는 같은 저장소의62 snapshot과 이번 동결 입력으로 재생된다. source/evidence hash는 `EDGE_SOURCE_INPUT63.json`에 있다. Unity, Desktop 원본 도구, 원본 모델 재실행 없이 검사가 가능하다. 결과 이미지는 저장 자료의 debug mask이며 새 GPU 캡처가 아니다. 제품/31/34/기존 수정 파일은 변경하지 않았으며 Unity 접근·Play·렌더·CUA·GC·SaveAssets·앱 종료·push는0회다. 현재 Unity 상태를 재확인한 것은 아니다.
