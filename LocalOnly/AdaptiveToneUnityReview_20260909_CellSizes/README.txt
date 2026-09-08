정면 셀 크기 비교 — 2026-09-09

요청: 현재 외형 방향은 좋으며, 명암이 간헐적으로 단색이 되는 현상을 지적.
실제 3×3 / 4×4 셀의 정면 비교 요청. 알고리즘 수정이나 기본 크기 확정은 하지 않음.

결과
- 기존 기본값 2×2를 확인하고 동일 Play frame 2에서 2×2·3×3·4×4를 각각 촬영.
- 모두 384×768, 정면 yaw180, 같은 camera/pose/ortho/light/tone 설정.
- 실제 subject.SetPixelCellSize(2/3/4)를 사용. 이미지 확대나 리사이즈가 아님.
- 몸체와 기존 외부 1셀 선에 같은 셀 크기를 사용하므로, 셀이 커지면 선도 같이 굵어짐.
- front_cell_comparison.png는 원본 PNG를 원래 크기로 나란히 놓고 제목만 붙인 것.
- 같은 Player/Camera/프레임/위치/재질 참조와 전체 상태 복원 확인(comparison_manifest.json).
- 2×2·Adaptive=true 복원, Play 종료, background=false, GameMap1 유지.
- Assets/ProjectSettings/기본 prefab/알고리즘 변경 없음. 기존 dirty 파일 그대로 보존.
- Console은 전후 동일한 이전 FXC 중단 기록4개, 신규오류0. 기록을 지우지 않음.

명암 사라짐: 코드 기반 가설이며 움직임 재현으로 확정하지 않음
- CharacterAdaptiveTones.compute BuildBroadSupport(335~404): 넓은 명암 보호를0으로 초기화.
  명암 폭·공간 설명력·지지 영역·2개 스케일 겹침 등의 판정을 통과하지 못하면 보호 없이 종료.
- SolveTones(494~529)는 K=1부터 검사. 보호가0이고 RMS<=.06이면1색을 채택할 수 있음.
- GatherHighlights(564)는 READY+GUARD를 요구하므로 보호가 없는 프레임은 밝음 추가도 빠짐.
- 색계열 격자/그 프레임 바운딩박스의 공간 타일/관측색 분포를 매번 다시 계산.
  자세·가림·조명의 변화로 경계 판정이 달라질 수 있고 이전 K/팔레트 유지 장치는 없음.
- 다른 후보: K가 같아도 희소 셀 표본이 한 명암 구간만 잡으면 단색처럼 보일 수 있음.
- 입력/용량 실패는 원본 RGB를 유지하는 별개 경로이며, 이번 정면 비교로 배제한 것은 아님.

후속 확인 후보 (아직 실행 안 함)
- 같은 설정으로 움직일 때 '명암 있음/단색' 두 프레임만 대조.
  기존 RequestAdaptiveToneDiagnostics로 global 상태와 READY+GUARD 수를 함께 기록.
- 현재 진단 API는 K/그룹 키를 내보내지 않으므로 이 검사만으로 K 전환을 확정하지 않음.
  프레임마다 달라질 수 있는 해시 슬롯 번호를 같은 색 영역의 영구 ID로 취급하지 말 것.
- 이번에 임의 임계치 변경, 명암 강제 추가, 히스테리시스 구현이나 디자인 재보정은 하지 않았음.

파일
- front_2x2.png / front_3x3.png / front_4x4.png: 실제 Unity 캡처
- front_cell_comparison.png: 같은 배율의 비교판
- capture_cell_sizes.cs.txt: 기존 MCP 캡처 코드를 재사용한 재현 명령
- finish_capture.cs.txt: 2×2 복원 검사 후 Play 종료
- make_comparison.py: 크기 변경 없는 비교판 조립
- comparison_manifest.json: 프레임/대상 동일성·해상도·설정·복원 기록
