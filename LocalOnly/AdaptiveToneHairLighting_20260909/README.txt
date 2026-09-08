헤어 실제 수광량 기반 단계화 비교 — 2026-09-09

요청: 만족한 몸의 낮밤/조명 반응을 보존하고, 헤어가 한 색으로 합쳐지는 문제를
실제 조명 범위 분석으로 수정해 정면 비교 사진을 제공.

변경 범위
- CharacterFlatUnlit.shader: 원래 PBR색은 그대로. Hair(part3)에만 albedo/specular 합성 전
  diffuse 수광 Y를 세 번째 native MRT에 기록. 설치된 URP 17.5 light loop와 동일한
  SH/주광/Forward+ 추가광/cookie/거리/그림자 및 프로젝트 local light 경로 사용.
- CharacterSilhouetteRendererFeature.cs / CharacterAdaptiveTonePass.cs:
  기존 RendererFeature 안의 transient texture/compute binding. 새 카메라/Manager 없음.
  hairLighting 스위치 OFF는 기존 방식, ON은 새 방식. 비활성 시 추가 MRT 할당 없음.
- CharacterAdaptiveTones.compute: 헤어만 수광 단위 histogram/DP/공간 대비/밝음/resolve.
  RMS <= max(meanE, .02) × .10. 공간/밝음 최소 대비도 같은 meanE 기준으로 환산.
  단계 개수는 자동. RGB는 관측 원본 후보만 사용. 몸/눈은 기존 Oklab L 판정 그대로.
- valid native illumination 오류 bit64 추가. RGB/geometry/depth/메타의 원본 계약 유지.

실행 검증
- 독립 수학9검사 통과: test_hair_lighting.py. GPU/아트 품질 검증과 구분.
- D3D11 / RTX2080Ti 실제 compute6case 통과: gpu_checks_20260908_154007_746/summary.json.
  큰 원본 readback JSON6개와 summary는 gpu_checks_evidence.zip에도 그대로 보관해 커밋합니다.
  day off K2 → on K3, night off K1 → on K3. albedo×4도 K3, flat E는 K1.
  body RGB 전후 최대차0; sparse depth/empty/metadata/lighting 입력 보존.
  최종 헤어RGB는 실제 입력 후보에 포함. 야간평균/주간평균=.11999052 (조명 입력 .12배).
- 실제 기존 Player entity568105589213712708 / Camera568105589213712362,
  동일 Play frame2, 동일 pose/카메라/재질/2px로6장 촬영.
  dim: key .24/fill .066/ambient .036; bright: 2/.55/.3. 정면yaw180, 384×768.
  연속(source) / 기존(old) / 수광(new). 모든 촬영 조건은 capture_hair_lighting.cs.txt.
- 촬영 뒤 source=true, adaptive=true, hairLighting=false, 2px 및 모든 임시 상태 복원.
  Play off, GameMap1 dirty=false, background=false. 저장된 씬/재질/prefab/renderer asset 변경 없음.
- 최종 flat/mask/composite shader 및 compute 메시지0. Console 오류4건은 전부 이전 FXC 기록.
  촬영 종료 근처 RelayDisconnected 경고1이 추가됐지만 후속 MCP 상태 조회는 정상 응답했습니다.
  수치 결과는 디자인 합격이 아니며 새 외형은 사용자 확인 대기.

증거·재현
- front_dim_source/old/new.png, front_bright_source/old/new.png: 실제 원본 PNG6개.
- front_hair_lighting_comparison.png: 크기/색 변경 없이 원본 RGBA를 나란히 배치.
- comparison_manifest.json: 같은 프레임/객체/pose/복원 검사를 통과한 실제 촬영 기록.
  첫 실행에서 RunCommand JsonUtility가 nested CaptureInfo[]만 생략했습니다.
  공통 조건과 성공 검사 및 PNG6장은 보존했습니다. 이미지를 재촬영/덮어쓰지 않았습니다.
  재현 스크립트는 이후 string[] JSON record로 수정했고 montage는 최초 공통 기록도 읽습니다.
- 처음 GPU 검증 스크립트는 DTO가 외부로 이동하여 Width/Height 참조 컴파일 실패.
  DTO의 fixture 크기만 수정한 뒤 첫 실제 GPU 실행6case가 모두 통과했습니다.
- 실행: probe_state → start_capture(Edit Mode) → capture_hair_lighting(Play)
  → finish_capture → python -B make_comparison.py. 기존 출력이 있으면 보존하고 거부합니다.
- unittest: python -B -m unittest discover -s LocalOnly/AdaptiveToneHairLighting_20260909 -p "test_*.py" -v

한계/다음 판정
- 이번 비교는 정지 정면. 실제 이동/회전/조명 전환 동영상, 시간 이력/hysteresis, 성능/빌드는 미검증.
- 색상 그룹은 여전히 최종 RGB의 정규화 chroma 격자이므로 유색광에서 그룹 분할 변화가 남습니다.
- 넓은 공간 보호의4×4→2×2 지지 영역 근사와 관측색 후보 방식은 유지했습니다.
  강제 밝음 추가, 피부 수치 변경, 이미지 후처리, 픽셀 디자인 수동 변경은 하지 않았습니다.
- hairLighting은 기본OFF로 복원. 사용자 승인 전에 자동으로 켜거나 추가 미술 보정을 하지 않습니다.
- GitHub 원격은 읽기 조회만 했고 push하지 않았습니다. 완료 후 이번 경로만 로컬 커밋합니다.
