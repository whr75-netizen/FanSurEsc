# B35 면별 투영 계약 후보 — 원본 방향을 깊이 상자로 대체하지 않기

상태: **제안·미실행**. 2026-09-27. 현재 B34 코드·Unity 씬·이미지를 변경하지 않았다. 여기의 수식·검사 기준은 구현 후보이며 실험 통과 기록이 아니다.

## 1. 확인한 입력과 문제

직접 본 입력은 `docs/artifacts/building34/native/counter/native.png`(274×228), `rear_shelf/native.png`(289×279)다. 둘 다 자동 PerfectPixel의 native PNG이며 재검출·축소하지 않는다. 각 폴더의 `receipt.json`과 원본 해시를 입력으로 고정한다.

기존 `Tools/Building34/calibrate.py`의 볼록껍질 적합성은 **그림의 불투명 영역이 특정 상자의 투영 안에 들어간다**는 조건이다. 이것으로 그림 안 상판·기둥·선반의 각도가 상자와 같아지지 않는다. 좌우 반전도 기울기의 부호만 바꾼다. 깊이 교점의 유효성과 색 그림의 방향 일치는 서로 다른 계약이다.

사용자가 요구한 카메라 pitch 30°와 화면의 사선 30°를 혼동하지 않는다. 건물 local yaw 45°, pitch 30° 직교 카메라의 기저는 다음과 같다.

```text
right r = (1/√2, 0, -1/√2)
up    u = (1/(2√2), √3/2, 1/(2√2))
front f = (√(3/8), -1/2, √(3/8))
screen(X) = (P·r·X + ox, -P·u·X + oy)  # 이미지 y 아래쪽
```

따라서 바닥 X/Z축의 화면 기울기는 ±0.5, 즉 2:1 계단이며 화면 각도는 약 26.565°다. Y축은 수직이다. **카메라는 유지하고 대상 꼭짓점을 위 식으로 계산한다.** 이 식은 프로젝트에 선언한 목표 투영이며 참고 게임의 실제 제작 카메라를 측정했다는 주장이 아니다. 직교 투영 여부는 [Unity Camera.orthographic](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Camera-orthographic.html)로 확인한다.

## 2. 후보와 적용 범위

| 후보 | 각도를 정하는 입력 | 성립 범위 | 실패·제외 조건 |
|---|---|---|---|
| 현재 단일 이미지+상자 깊이 | 원본 그림 각도는 그대로 | 기존 그림과 목표 투영이 이미 같을 때 | 상자 안에 들어가도 내부 직선 방향이 틀린 경우 |
| 물체 전체 단일 homography | 평면 4점 | 간판·액자처럼 하나의 평면 | 상판/앞면/옆면이 다른 평면인 가구 전체에는 부적합 |
| **면별 homography+공유 3D 틀** | 각 면의 원본 표식과 하나의 치수/축 템플릿 | 직사각 몸체·상판·패널·문·선반 판재 | 원본의 가려진 면, 서로 모순되는 투시, 입체 소품을 같은 면으로 뭉치는 경우 |
| 동일 템플릿의 여러 실제 판재+UV | 면마다 원본 재료/완성 이미지 | 선반 단·테두리·다리 등 구조가 선언됐을 때 | 노출될 재료나 뒷면이 없을 때 |
| 깊이 층을 가진 별도 소품 | 소품의 mask·지지면·깊이 또는 별도 시점 | 병·화분·가방처럼 상자 3면이 아닌 대상 | 단일 색 이미지에서 보이지 않는 체적을 정확히 복원한다고 주장하는 경우 |

권장 최소 후보는 **면별 homography+공유 3D 틀**이다. OpenCV의 homography는 평면 사이 사영 변환이며, 임의 입체 물체 전체의 시점 변환 보증이 아니다. [공식 설명](https://docs.opencv.org/4.13.0/d9/dab/tutorial_homography.html)

## 3. 입력 계약: AI의 일회성 표식과 고정 계산 분리

각 자산은 다음을 가진다.

- 원본 파일·해시·native 격자, target 물리 치수와 facing, source에 실제 보이는 면 ID.
- 한 물체의 공유 꼭짓점 ID와 3D 좌표. 면마다 독립적인 크기·회전·offset을 두지 않는다.
- 각 면의 source 사각형 및 alpha/polygon mask, 동일 순서의 target 꼭짓점 ID, 최소 2개의 **적합에 쓰지 않은** 내부 직선/특징 표식.
- 상판 위 입체 소품, 선반 물품, 돌출 테두리는 별도 component 또는 지원하지 않는 영역으로 명시한다.
- source의 모서리를 시각적으로 지정하는 단계는 기하학적 연산으로 둔갑시키지 않는다. 잘못 지정되면 계산 결과도 잘못된다. 불확실한 모서리는 confidence 문구로 통과시키지 말고 입력 미완료로 둔다.

corner 순서를 결정한 뒤 face 회전/반전은 템플릿의 축 대응에서 결정한다. 화면에서 좋아 보이도록 전체 물체를 뒤집고 face ID를 유지하는 방식은 금지한다. source에 오른쪽 끝면만 있고 목표가 반대쪽 끝면을 요구하면, **대칭 형상·재료 재사용이 허용되는지**를 자산 계약에 표시해야 한다.

## 4. 변환: 색·실루엣·깊이를 동일한 면에서 계산

파이프라인:

```text
원본 native RGBA + 면/소품 표식
→ source 면 좌표
→ 공유 3D 판재의 UV
→ 고정 30°/45° 직교 투영
→ 하나의 native 출력 격자에서 색·alpha·surfaceXYZ 동시 계산
→ 기존 Unity native-depth 표시
```

면 i의 source 네 점을 `s_ij`, 공유 3D 꼭짓점을 `X_ij`, 목표 화면점을 `t_ij=screen(X_ij)`로 둔다. 정규화 DLT 또는 OpenCV `getPerspectiveTransform(s_i,t_i)`로 `H_i`를 구한다. source 사각형이 affine 조건을 만족하면 affine를 사용해 불필요한 사영 자유도를 제거한다. 사영이 필요한 입력에 affine를 억지 적용하지 않는다.

목표 texel 중심 `p=(x+.5,y+.5,1)`에서 `q=H_i^-1·p`, `s=(q.x/q.z,q.y/q.z)`를 계산하고 source의 해당 texel을 Point로 읽는다. palette·명암을 새로 만들지 않는다. 동시에 같은 target ray와 **그 면**의 교점 `X`를 구해 surfaceXYZ를 저장한다. 면 소유권은 실제 ray 깊이로 정하며, source RGBA와 다른 큰 상자의 앞면을 임의로 깊이 소유자로 삼지 않는다.

공유 경계는 하나의 꼭짓점·선분을 사용한다. 래스터 경계 소유권은 동일한 half-open/top-left 규칙으로 정하고 두 면 사이 틈을 dilation이나 별도 outline으로 메우지 않는다. 여러 면이 한 픽셀에 겹치면 목표 광선의 가장 앞 유효 면이 색·alpha·깊이를 **함께** 소유한다.

OpenCV API는 네 점 대응의 행렬 계산과 역방향 래스터 매핑을 제공한다. `INTER_NEAREST`는 새 혼합색을 만들지 않는 선택이지 특징 전체 보존의 증거가 아니다. [OpenCV geometric transforms](https://docs.opencv.org/4.13.0/da/d54/group__imgproc__transform.html)

## 5. 출력 격자: 각도 교정과 무손실을 동시에 약속하지 않기

원본 자동 격자는 **입력의 표본 좌표**를 결정한다. 방향을 바꾸는 homography는 대개 정수 격자끼리의 일대일 대응이 아니므로 재표본화가 생긴다. 이를 다시 PerfectPixel에 통과시키거나 작은 크기로 줄였다 키워 해결하지 않는다.

출력 PPU는 기존 자산을 슬롯에 넣기 위한 최소값으로 역산하지 않는다. 다음을 별도 제약으로 계산한다.

1. 물체의 선언된 물리 크기 및 프로젝트 공통 texel 밀도.
2. 면 변환의 Jacobian `J_i(s)`의 최소 singular value와 압축 방향. 값이 1보다 작으면 어느 방향으로 원본 표본이 압축되는지 보고한다.
3. source texel ID→output texel provenance와 필수 특징 영역의 실제 살아남은 표본·연결성·선폭.
4. 선언한 PPU에서 필수 특징을 유지할 수 없으면 **부적합**이다. 카메라 변경·숨은 확대·공간 축소로 통과시키지 않는다.

Jacobian 검사만으로 모든 특징 보존을 주장하지 않는다. 충분히 큰 출력에서도 nearest 표본의 위상 때문에 일부 source ID가 누락될 수 있다. 요구가 source texel 전체의 전송이라면 실제 provenance에서 누락 0을 별도로 요구해야 하며, 그것이 게임에 적합한 최소 픽셀 수를 보장하지는 않는다. 단일 공통 PPU에서 방향·물리 비례·특징 밀도의 조건이 함께 성립하지 않으면 해당 원본을 재료로 쓰는 후보를 기각한다.

## 6. counter / rear_shelf 최소 실험

### E1: counter의 캐비닛 몸체

- 원본 전체를 보존하고 앞 패널·오른쪽 끝 패널·상판을 분리한 표식 manifest만 작성한다.
- 원본은 274×228. 생성된 금전등록기, 동전통, 종이봉투는 상판보다 높은 별도 소품이므로 상판 H에 포함하지 않는다.
- 캐비닛 틀의 폭 2.4m·깊이 .8m·기본 높이 1m는 기존 B32 fixture 계약을 재사용할 수 있다. 계산기까지 하나의 1.55m 상자로 만드는 표현은 이번 면 각도 실험에 쓰지 않는다.
- source 앞면 4점으로 H를 정한 뒤 **문 패널 상/하단 및 손잡이 줄**을 holdout으로 확인한다. target 긴 가로축은 ±.5, 수직축은 dx=0이어야 한다.
- 원본 대비/변환 대비/면 ID/깊이 표시를 같은 관찰 크기로 제출한다. 몸체만 통과하면 `counter body projection only`이며 계산대 전체 완료가 아니다.

### E2: rear_shelf의 구조 판재

- 원본은 289×279. 외부 상판·좌우 세로대·하부장 전면·끝면을 템플릿 판재로 나눈다.
- shelf 전체를 하나의 front H로 처리하지 않는다. 각 진열단의 윗면은 서로 다른 높이에 있는 평면이고, 병·책·화분은 그 위에 놓인 대상이다.
- 최소 실험은 **하부장 전면+끝면+상판 구조** 및 **한 개의 빈 선반판**이다. 보이는 물품은 그 단계의 source occlusion으로 남기고, 가려진 판재를 crop으로 얻었다고 쓰지 않는다.
- 두 선반 단의 긴 앞 모서리를 holdout으로 둔다. 같은 축의 선들이 서로 다른 각도를 유지하면 `SOURCE_NOT_ONE_PLANAR_FACE`로 실패 처리한다.
- 물품 무리의 빌보드 배치는 별도 근사다. 손잡이·기둥·테두리의 검사가 맞았다고 물품의 실린더/타원 시점까지 맞았다고 보고하지 않는다.

실험용 수동 source 주석은 `rear-shelf-landmarks-proposal.json`과 `counter-landmarks-proposal.json`에 기록했다. 공통 PPU는 부모 작업이 고른 **127**이며 물리 치수는 B32를 유지한다. 두 파일은 미검증 후보로, 원본의 보이는 모서리는 약 2 native px의 주석 불확실성이 있다. counter 상판의 계산기에 가려진 뒤쪽 모서리는 평행사변형 가정으로 추정했음을 별도로 표시했다. rear의 전체 3면 실험은 상품·테두리·덮개 돌출을 평면 아트로 취급하는 외피 근사이며, 세부 판재 복원과 구분한다. 모서리/소품 mask overlay·holdout·원본 누락 검사를 통과하기 전에는 프로덕션 자산이나 성공 증거가 아니다.

## 7. 반례와 판정 산출물

| 검사 | 사전 기준·실패 반환 |
|---|---|
| source face 적합성 | 4점 순서가 뒤집히거나 면적 0, 내부 holdout이 한 평면으로 설명되지 않으면 source 표식/분할로 반환 |
| 기하 투영 | 공유 3D 꼭짓점의 연속 좌표 reprojection 잔차 ≤1e-4 native px. target edge의 방향은 ±.5 또는 수직으로 수학적으로 결정 |
| raster edge | 연속 target edge와 출력 cell coverage의 차이를 셀 단위로 확인. 1개 격자 셀의 경계 오차와 실제 기울기 오차를 구분 |
| 공유 경계 | 경계의 양쪽 face가 동일 3D edge를 참조. 같은 texel 소유권 충돌·미정 영역 0 |
| alpha/depth | 출력 opaque texel마다 동일한 face ID·source sample·유효 XYZ가 존재. 투명 texel depth validity 0 |
| 특징 | 실제 source→output provenance·필수 특징 연결성을 기록. RGB가 원본 팔레트에 있다는 이유만으로 합격 금지 |
| 가림 | 원본에 없는 면/가려진 판재가 필요한 target 영역을 검출하면 `MISSING_SOURCE_SURFACE` |
| 입력 오류 반례 | source corner 하나를 틀린 edge로 바꾼 입력, side mask를 누락한 입력, 앞면에 상판 물품까지 넣은 입력이 해당 검사에서 실패해야 함 |
| 표시 | 기존 게임 Camera/SceneView에서 공통 PPU·Point·정수 줌 확인. 이것이 미술 완성도를 대체하지 않음 |

산출물 후보: `landmarks.json`(원본·면·공유 vertex·holdout), `surface-template.json`(물리 치수/UV), `projection-report.json`(H/Jacobian/소유권/특징/실패), `color.png`, `surfaceXYZ.exr`, `face-id.png`. 모든 derived 출력은 기존 원본과 분리하며 Unity 통합 전 E1의 구조 조건부터 판정한다.

## 8. 유기적 물체·가려진 정보의 경계

병·식물·천·가방은 세 개 평면의 homography로 자연스러운 시점 변경을 보장할 수 없다. 회전이 필요한 유기적 대상은 준비된 다중 시점, 3D/깊이 재료, 또는 목표 투영에 맞춘 새 저작이 필요하다. 고정 화면의 평면 소품으로 사용할 수는 있지만 그 근사를 명시한다.

이미지 기반 모델링은 오래된 표준 접근이다. [Tour Into the Picture](https://www.cs.princeton.edu/courses/archive/spr01/cs598b/papers/horry97.pdf)는 단일 그림을 단순 평면·foreground polygon으로 저작하는 방법이며 정확한 3D 복원을 목표로 하지 않는다. [Layered Depth Images](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/Shade-SG98.pdf)는 색에 깊이/층을 추가해 시점 이동 시 가림을 처리한다. 두 자료는 **추가 표현이 필요하다는 근거**이며, 현재 그림에서 그 깊이와 가려진 색을 자동으로 얻었다는 증거가 아니다.

## 결정 요청 대신 다음 계산 입력

부모 작업은 E1 입력에 필요한 실제 face landmark·mask를 먼저 준비한 뒤 작은 실험을 선택한다. 입력이 없으면 임의 각도 수치나 2:1 선 덧그리기로 대신하지 않는다. E1 실패 원인이 비평면 source일 때는 E2 전체로 확대하지 말고, 템플릿에서 직접 각도 제약을 가진 새 자산을 만드는 후보로 돌아간다.
