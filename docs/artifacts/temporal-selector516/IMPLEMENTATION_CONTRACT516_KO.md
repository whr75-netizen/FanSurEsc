# 516 격리된 단일 선택기 시제품

범위는 저장514의81포즈로 활성 경계 대응과 시간 선택을 시험하는 offline 구현입니다. Unity/runtime/shader/scene은 변경하지 않았습니다. 활성348·기본OFF511/512와 사용자 설정은 유지합니다. 후단 마스크/RGB 이력층은 없습니다.

## 실제 구현

- active516.py: 지속 source `(ring,segment,t)`의 교차·T 접점·공선 겹침을 분할하고, 각 조각 양쪽 positive winding으로 실제 채움 경계를 결정합니다. 중복 경계의 다중 lineage는 그대로 표시해 단일 ID 이력을 강제하지 않습니다. 접합부·정확 동점은 대응을 해제합니다.
- 선택 셀의 directed dual-grid 경계 전체를 같은 방향의 활성 조각에 대응시킵니다. 두 끝점의 거리·방향·구간 순서를 사용합니다. source가 셀과 만나는 표현의 cell-diagonal corridor 밖은 성공으로 늘려 맞추지 않습니다. 모든 기존81선택 경계에 대응 후보가 있으며, 이는 의미론적 유일 대응의 보편적 증명이 아닙니다.
- maximal H/V 경계를 지속 source 구간에서 분할한 span으로 만들고 source parameter 순서를 유지합니다. 공통 활성 구간이 없거나 현재 packet이 앞가림을 알리면 이전 대응을 해제합니다. 새 채움의 packet 미저장은 **미확인**이며 가림검증으로 승격하지 않습니다.
- span516.py: 이전 edge 중심의 source 매개변수를 현재 곡선으로 옮기고 tangent 회전에 맞춰 양자화 offset을 회전합니다. 대응 곡선 운동을 반영한 예상 위치와 현재 span을 비교합니다. 색·옛 깊이·옛 이미지는 옮기지 않습니다.
- select516.py: 현재 정적 cut은 초기 후보입니다. 한 목적함수 안에서 모든 경계 주변/연속영역 셀의 추가·삭제를 같은 규칙으로 탐색하고 mask 하나만 냅니다. 좌표·phase 예외·1프레임 majority·별도 후처리는 없습니다. cell move는 탐색 연산이며 출력 필터가 아닙니다. greedy local optimum의 한계를 명시하며 전역 최적해라고 주장하지 않습니다.

## 편집 비용의 의미와 계수

이 시제품은 논문 Eq5의 수치 재현이 아닙니다. 다음 프로젝트 비용을 명시적으로 사용합니다.

1. span add/delete 비용은 unit boundary-edge 개수입니다.
2. substitute 비용은 길이 차이 + source 순서대로 대응시킨 edge 중심의 L1 이동 잔차이며, 전체 삭제+추가 비용을 넘으면 그 값으로 제한합니다. L1은 한 격자 축으로 이동한 boundary-pixel 거리의 합이라는 뜻입니다.
3. merge2→1/split1→2는 span을 source 순서로 연결한 동일 대체 비용입니다. span sequence DP는 이러한 연산의 최소 경로와 trace를 기록합니다. 실제 geometry event로 끝난 구간은 삭제 비용으로 보존을 강제하지 않습니다.
4. raw span 비용을 현재 spatial energy에 `eta × BoundaryCost(.14)`로 결합합니다. 기존 공간 경계 한 단위의 비용을 표현 편집 한 단위의 초기 비교 단위로 재사용하는 가설입니다. 논문 weight2.0 또는 pixel ABA 개수에 맞춘 계수가 아닙니다. `.5/1/2`의 세 eta로 민감도를 확인하며 **eta1을 기준**, 나머지는 반례·민감도입니다. 결과를 보고 새 수치를 추가 탐색하지 않습니다.
5. normalized diagnostic도 저장하지만 그것을 Eq5라고 부르거나 후보 목적에 몰래 섞지 않습니다. 현재 입력은60Hz/실제 timestamp의 한 루프입니다. 가변 cadence/seek/loop 초기조건의 품질 보장은 별도 검사이며 일반 실시간 통과를 주장하지 않습니다.

계수1은 검증된 미관값이 아닙니다. 세 민감도에서 면적오차·경계길이·계단 run 기울기 전환·연속곡선 거리·새/기존 시간 반전을 나란히 보고, 약한 계수만 유리하거나 실제 형상이 손상되면 채택하지 않습니다. 모든 틈·가닥을 보존하는 제약을 추가하지 않습니다. 모든 변화0도 목표가 아닙니다.

## 검증과 제한

합성 fixture는 identity/정수이동/90도 회전의 보정 잔차0, 활성 경계 소멸 때 history0, 공선 합침의 다중 lineage 보존, 실제 앞 packet에서 해제를 확인합니다. 실제 손이 앞을 지나는 영상의 통과가 아닙니다. context516.py는 model/projection/view basis/clip signature나 seek가 바뀌면 이전 선택을 폐기합니다. head-follow translation은 현재 기하 운동으로 처리합니다.

원본/후보는 모든81포즈를 보존하고, 고정 screen ABA는 관측으로만 기록합니다. span 편집 trace·source 운동과 함께 해석합니다. 새 채움의 packet/renderer1 가림이 저장되지 않은 경우 실제 source Select/Visible 경로 확인 없이는 runtime으로 통과시키지 않습니다. body same-ray512·눈·nativeworld·내부색11+몸1·212ms 성능은 동시에 변경하지 않습니다.

실제 Walk 진입 조건은 offline에서 개선과 원형/계단 손상 부재의 근거가 확보되고 필요한 새 패킷의 가림이 검증되는 것입니다. 그렇지 않으면 첫 형태/대응/가림 반례를 보고하고 기본OFF 시제품으로 남깁니다.
