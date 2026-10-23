# 525: 두 원인에 한정한 기본 OFF 실험

- 524 기록/원본 캡처와 `da3f5fd`를 보존한다. 기존 기본 활성 경로를 통과 버전으로 가정하지 않는다.
- MASK 입력: 원본 material의 `_MainTex_ST`, `_Color.a`, `_Cutoff`를 포함한다. 텍스처 texel 중심 alpha를 고정 대각선의 선형 삼각형 필드로 정의하고 cutoff의 벡터 경계를 추출한다. 이 경계와 원본 UV 삼각형의 교차로 불투명 표면 조각을 구성한다. 단일 UV 조사로 최종 셀 전체를 투명 판정하지 않는다. GPU bilinear 등고선과 선형 texel 등고선은 동일하다고 주장하지 않는다.
- 불투명 조각 경계는 원본 primitive/barycentric anchor 및 동일 rest 위치+skin weight를 가진 공유 변의 anchor로 연결한다. 매 포즈 실제 skin 변형을 투영하고 기존 vector union→RDP(error .1875 논리셀)→면적/경계길이 joint selection을 사용한다. 원본 저해상도 mask를 복사하지 않는다.
- 규모 gate: 실제 Unity 정식 컴파일 코드의 저장 33/34/35 검사에서 12,931조각, 7,742anchor, 포즈당 약1.73초. 폐합 성공과 실시간 채택 실패를 분리한다. 정확면적 엔진·추가 선택기 확장은 하지 않는다.
- 색 공급: 기존 두 렌더 사이에서 선택 영역이면서 첫 렌더의 중심 packet과 최종 actor owner가 둘 다 없는 셀만 조회한다. 현재 연속 옷 삼각형의 셀 교차/가까운 표면점을 구하고 같은 source ray에서 모든 actor 삼각형의 실제 깊이·UV alpha·cull을 대조한다. alpha가 불확실하면 통과시키지 않는다. role만으로 같은 표면이라고 보지 않는다.
- 실제 source primitive/UV/법선/접선/position을 작은 quad에 함께 실어 기존 Probe502/Legacy502 shader로 계산한다. 기존 Probe/Legacy480 attachment에만 쓰며 새 RT·렌더 패스·RGB 복사층은 없다. 원래 source 위치의 조명/깊이/소유권을 설계 픽셀로 이동한다. 첫 렌더의 실제 다른 파츠 소유 셀은 이동 대상이 아니다.
- 공급 거리 한계는 기존 곡선 오차 .1875 + 한 셀 반대각선 sqrt(.5)이다. 좌표/프레임 예외, 깊이 bias, 무조건 머리/옷 우선, 화면 RGB donor는 없다. 불확실하거나 공급할 수 없는 셀은 명시 실패다.
- 같은 포즈·조명·시간의 실제 Walk 33/34/35 OFF/ON에서 가시/불투명도/색 공급/기존 모양/얼굴·눈·가림을 확인한다. 성능 실패가 남으면 전체루프를 반복하지 않고 기본 OFF 미채택으로 종료한다. 얼굴 회색 미재현은 해결이 아니다.
