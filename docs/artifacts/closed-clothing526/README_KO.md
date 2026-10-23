# 526 — 동일 옷 영역의 후보 제한 가속, 제품 OFF 유지

2026-10-23. 526은 작업 기록이다. 실제 제품 옷 경로는 기본 OFF이고 전체 가시/시간 품질/얼굴 회색 해결이 아니다. 525/628fa86과 원래 계산 경로를 보존한다.

## 비용 원인과 최소 변경

불변 작업과 매 포즈 작업은 이미 나뉘어 있었다. 텍스처 alpha선형등고선28,382개, UV삼각형 교차12,931조각/7,742anchor 생성은 모델/material 최초1회다. 실제 최초비용701.54ms, 추가 독립 조회845.60ms. 모델이 그대로일 때 다시 추출하지 않는다. 매 포즈 anchor 투영은 저장자료 .52~.78ms다. 원본 UV와 primitive의 투영 방향을 확인하는 일부 불변 계산이 반복되지만 주비용은 아니다.

12,931조각 중1,956삼각형은3변이며 나머지137삼각형의 MASK 경계가 조각을 늘렸다. 원 텍셀 경계의 세부가 최종 디자인 곡선으로 줄어들기 전에 합집합에 들어가는 구조다. 33포즈의 유효변6,985개, 교차후조각7,255개, 실제외곽변2,602개가 최종곡선38점이 된다. 같은 삼각형의 정확한 직선 중복은0개, 산술 오차 크기까지 허용해도 약1%만 줄어 표현 단순화안은 적용하지 않았다.

실측 기준 계산의 변쌍 검사 .661~.665초, winding순회1.137~1.178초다. 이전처럼 연산 개수만으로 주병목을 추정하지 않았다. 원래는 모든 변쌍 약2,430만개와 모든 조각×전체변 약5,010~5,068만회를 순회했다.

수정은 ClosedRegion524.cs 한 파일뿐이다. 1논리셀 크기의 AABB 후보 bin으로 교차할 수 있는 변쌍을 모으고 원래 i,j순서로 처리한다. 이것은 coverage 샘플 격자가 아니라 정확한 검색 인덱스다. 겹치는 AABB는 반드시 공통 bin을 갖는다. winding은 현재 query축의 반열린구간[min,max)에 실제로 들어오는 변만 sweep으로 유지하고 원래 방향/2e-8산술 tolerance/원래 변 순서로 계산한다. 큰 인덱스 입력은 원래 계산으로 fallback하며 mask를 바꾸지 않는다. alpha/cutoff/curve/RDP/area/cost/UV/가림식/시간상태는 변경하지 않았다.

저장3포즈에서 원525 source/최종curve 바이트가 모두 같았다. 합집합1840.41/1850.16/1806.63ms→66.05/56.84/55.32ms. 변쌍 후보267,715/261,248/239,332, 실제 winding 방문80,959/78,466/75,881회다. 이 결과는 정지 렌더 품질 판정이 아니라 동일 저장 입력의 계산 동등성이다.

## 실제 Walk 3쌍

양쪽 모두 옷525 경로 ON으로 둔 같은 실행의 실제Walk33/34/35, 원래 계산 대 후보제한만 비교했다. 자세/카메라/시간/조명 동일, 모든3프레임 보존. source/fit 경계와 면적·선택 mask 전체바이트가 같다. source centreRGBA/primitive/UV/depth, owner, 외곽선 audit도 같다. 누락/선택영역미채움/옷영역밖/최종gate 위반은 모두0이고 소매34 가시 제거는 유지됐다.

전신 PNG3쌍이 바이트 단위로 같다. 모든 float버퍼가 같지는 않다. 머리role12~14에 33/34포즈280/288셀의 RGB 최하위값 차이가 최대2.98e-8/1.49e-8 있었다. alpha/owner변경0, 실제 얼굴색변경0, 35포즈는 전체float도같다. 머리float 차이의 최초 원인까지 추적한 것은 아니며 보이는 가시나 회색으로 분류하지 않는다. FLOAT_CLASSIFICATION526.json에 원표본을 남겼다.

실제geometry 계산은 기준2569.84(최초cache포함)/1835.44/1860.89ms→67.50/110.27/58.61ms. 34번의 추가 대기/할당 등 원인은 분해 측정하지 않았으므로 GC로 단정하지 않는다. 후보 pair32.65/30.98/28.66ms, winding22.95/18.45/18.20ms, area약.2ms/선택약8ms/packet13.70~18.49ms. RenderFrame wall은 기준2947/2137/2408ms→367/413/332ms. Editorwall을 PlayerFPS나 GPU 단독 비용으로 사용하지 않는다. 기존 별도head212ms와 구별한다.

정확한 후보 제한은 효과가 있어 OFF 실험 안에 보존했지만, **58.6~110.3ms 경계 계산은 실시간 채택 불가**다. 원 텍셀 세부를 유지한 뒤 합집합하고 마지막에만38~46점으로 줄이는 표현 비용이 남는다. 더 작은 입력 표현은 현재 검증한 기하/불투명도/가림과 같은지 증명되지 않아 자동으로 추가하지 않았다. 새 전역엔진/시간DP/정밀면적/SS/후처리층/전체Loop촬영은 없다.

## 얼굴 회색과 운영 상태

저장525 자료의 실제face source role3는7/8/11셀 모두 회색이 아닌 유색이다. provider/Prepare/최종 및material/texture/culling/MPB/faceMain/provider상태도 기록됐다. 얼굴을 의도적으로 회색 원본으로 넣는다는 근거가 없다. 현재525/526 테스트는 이 상태를 변경하지 않았다.

코드상 NativePlayer395는 Awake에서 모든 source output renderer를 끄고 warmup후 모두 켜며, setupWait5 이후 surface/host 초기화와 연결을 수행한다. 얼굴만 회색으로 대체하는 분기는 이 경로에서 확인하지 못했다. 현재 캡처는 connected후라 그 시작 전환5프레임의 회색 최초버퍼는 없다. Face 분리 렌더 자체와 회색 결함을 동일시하지 않으며 **정확한 회색 원인은 미확인**으로 유지한다. 이 문제를 고쳤다는 패치나 새 캡처는 없다.

CAPTURED3, 입력/Animator Idle speed1 loc0/자동시계/capture0/후크 복원. 직접 Edit/pausedfalse/compilefalse/updatefalse/cleanGameMap1, 배경실행false/ClothEnabledfalse 확인. 인덱스는 OFF 실험 내부 옵션true이고 제품기능은 활성화하지 않았다. 사용자 QualitySettings/TimeManager는 해시 보존. 활성44d13c0, OFF511/513, 종료arcDP, 내부색head11+body1, head212ms는 별도 미해결이다.

증거 REVIEW526/STATIC_ANALYSIS526/CANDIDATE_COUNTS526/FLOAT_CLASSIFICATION526/FACE_EXISTING526 및 정상속도 전신WebP·검수GIF·PNG. 모든 원 float/코드/성능 수치는 C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Cloth526 에 보존한다. WebP17/16/17ms/GIF250ms이며35→33은 짧은 preview재시작, 전체Walk아님. Library403 우회·재시도 없이 로컬만 전달했다.
