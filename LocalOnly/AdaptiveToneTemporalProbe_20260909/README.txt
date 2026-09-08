적응형 명암: 수정 전 GPU 계측 기록 — 2026-09-09

범위/기준선
이 문서는 원인 진단과 후속 수정 비교 결과입니다. 사용자가 계측 중 수정을 허용했으며
몸체 Skin E 옵션의 구현·검증은 마지막 절에 구분했습니다. 미술 합격 주장은 아닙니다.
원래 기준 a88a778 → 진단 API 추가 commit 70bc8b8. Unity 6000.5.9f1, D3D11, GameMap1.
70bc8b8은 opt-in GPU readback/측정 MRT 추가이며 기존 명암 solver 결과를 바꾸는 수정이 아닙니다.
초기 Console의 기존 FXC 오류 4건을 보존했습니다. 사용자 기존 dirty 6파일은 미편집·미stage입니다.

캡처 구분: 총 96개 raw GPU capture (32 + 32 + 32)
- sweep_* 32개: 고정 Idle 포즈, white 조명 배율 1.2→0.025. 광량 변화 진단에 유효합니다.
- walk_* 32개(walk_skin_* 제외): 최초 동기 Animator.Play/Update(0) 표본입니다.
  phase 요청은 달랐지만 렌더 포즈가 모두 같았습니다. 걷기/시간안정성 근거에서 제외합니다.
- walk_skin_* 32개: SkinnedMeshRenderer.forceMatrixRecalculationPerRender를 캡처 중만 켜서
  동일 Animator의 실제 Walk 포즈가 달라지는 것을 확인했습니다. 제어된 포즈 비교에 유효합니다.
  해당 속성은 각 renderer의 이전 값으로 복원했습니다.
raw 파일은 실패/제외 표본까지 모두 보존합니다. 96개 모두 걷기 검증에 유효하다는 뜻은 아닙니다.

관측/해석
1. 몸체 저광량 단일톤: sweep index 17→18에서 GPU K=2→1.
   index 18의 GPU RMSE=0.0592396222 < 기존 toneError 약 0.06입니다.
   기존 몸체의 절대 Oklab L 오차 문턱이 이 입력에서 K=1을 허용하는 증거입니다.
2. 실제 Walk 포즈: walk_skin index 17→18→19에서 GPU K=3→4→3.
   K=3으로 고정한 CPU 재구성 오차는 약 0.05969096→0.06004171→0.05726619입니다.
   중간 표본만 0.06을 넘는 오차 문턱 전환과 대응합니다. 이 CPU 값은 GPU 기록값이 아닙니다.
3. 각 표본은 같은 captureId의 native/seed/최종출력/status/solutions를 연결해 분석합니다.
   READY/guard/K는 GPU 관측이며, CPU guard·K1·고정K 계산은 원인 해석을 위한 재구성입니다.

상태 복원과 실패 이력
- 최초 sweep_00의 8개: GPU/PNG는 기록됐지만 strict samePose=false로 manifest 검증 실패.
  그 시점의 차이 로그가 없으므로 원인은 미확정이며, 후속 회전 오차와 같은 원인으로 단정하지 않습니다.
- 최초 walk_skin_00의 2개: strict pose 검사 실패. 이번에는 회전 성분 약 6e-8 차이가 로그에 남았습니다.
  해당 실패 기록은 보존하며 성공 manifest로 바꾸지 않았습니다.
- 후속 walk_skin 30개: 위치·scale·부모·활성 상태는 exact, 회전은 quaternion 거리 ≤1e-6로 판정.
  samePose/restored=true와 별개로 poseBitwiseEqual=false를 그대로 남겼습니다.
  회전의 수치적 동등성을 비트 단위 완전 일치로 보고하지 않습니다.
- end_state.json은 최초 64개 뒤 기록입니다. end_state_after_walk.json은 총 96개 뒤 종료 직전 기록으로
  restored=true, hairLighting=false, cellSize=2, timeScale=1, 임시 조명 0, 측정 global=0입니다.
  JSON의 playingBeforeExit=true는 종료 직전 값입니다. 주 담당이 이후 Play 종료를 확인했습니다.
  각 Play 세션 안에서 Player/Camera 인스턴스를 유지했으며 서로 다른 세션 ID를 동일하다고 하지 않습니다.

재현 조건/절차
- 기존 Player/PlayerCamera/Animator/Renderer Feature를 사용합니다. 정면 yaw180, 384×768, 2px.
- white key=2, fill=0.55, ambient=0.3을 공통 배율로 조절합니다. 그림자는 없는 통제 조명입니다.
- 기존 헤어 수광 옵션은 촬영 중만 ON, 종료 후 이전 OFF. 기준 몸체 metric은 Oklab L입니다.
- GameMap1의 기존 셸이 준비된 Play 세션에서 import_diagnostics.cs.txt/API probe를 확인합니다.
- request.json: 새 batch명, mode(sweep/walk), first, count(1~8), total=32, scale,
  locomotionSpeed=1, hairLighting=true를 지정합니다. 기존 출력 경로는 덮어쓰기 없이 거부합니다.
- sweep은 capture_sequence.cs.txt, Walk는 capture_skinned.cs.txt를 사용합니다.
  기존 PlayerLocomotion의 Base Layer.Locomotion / Rig|Walk_Loop을 i/32 시점으로 평가합니다.
- batch 첫 표본의 진단 OFF/ON 최종 PNG 바이트 일치를 확인합니다. 15개 GPU readback 완료 후
  capture.json/sample.json/final.png 및 *.bin을 기록하고 try/finally로 원래 상태를 복원합니다.
- 순서는 captureId/index로 읽습니다. 이는 같은 Unity 프레임 안의 제어 표본이며 실시간 프레임 cadence가 아닙니다.
- analyze_trace.py CAPTURE_ROOT --out NEW_REPORT_DIRECTORY [--mode sweep 또는 walk]로 새 보고서를 만듭니다.
  출력: summary.json, groups.csv, adjacent_jumps.csv. 기존 보고서는 덮어쓰지 않습니다.
  전체 루트에 --mode walk를 사용하면 제외 대상 walk_*와 유효 walk_skin_*가 모두 포함됩니다.
  결과 해석 시 captureId의 walk_skin_* 및 camera/session으로 제한해야 합니다.

보고서/제약
- sweep 최종 분석: report_sweep_32. Walk 통합 분석: report_walk_by_camera(64개 중 유효 walk_skin만 사용).
- GPU uint/float32, RGBAHalf/RGBA8 원시 데이터가 관측 원본입니다. CPU float32/float64 계산은
  FXC FMA/pow의 비트 단위 에뮬레이션이 아니며 CPU 색경계 분류도 GPU와 달라질 수 있습니다.
- 그룹 대응은 hash slot이 아닌 subjectId+ColorKey, 인접 비교는 같은 camera/session/조건을 사용합니다.
- 진단 요청 API는 요청한 카메라가 해당 렌더 경로를 실제 실행해야 소비됩니다.
  요청만 하거나 AsyncGPUReadback.WaitAllRequests만 호출해도 카메라가 렌더되지는 않습니다.
  요청 카메라가 렌더되지 않으면 pending 상태가 남을 수 있고, queued/in-flight 요청은 교체할 수 없습니다.
- 통제된 GPU 호출 확인입니다. 실시간 입력/물리/게임 프레임 안정성, GPU 성능·빌드·다른 GPU,
  게임 내 유색광·구름·그림자까지 검증한 결과가 아닙니다. 미술 합격은 사용자 확인 사항입니다.

후속 몸체 수정 결과
- [구현] Skin(part4)만 skinLighting으로 E 분석을 선택합니다. 상대 RMS=max(meanE,.02)×.10.
  기본 OFF이며 별도 skinRelativeError/skinIlluminationFloor로 조절 가능합니다.
  헤어·눈·픽셀 격자·관측 RGB·깊이·Animator는 변경하지 않았습니다. 시간 보간/히스테리시스는 미구현입니다.
- [GPU 합성6case] gpu_skin_checks_20260908_164956_714/summary.json: 전부 통과.
  주야 E 경로 K3, 평평한 E는 K1, albedo×4에서 K 유지, 다른 부위 RGB/깊이/메타/관측색 소속 보존.
- [실제 paired7조건/14캡처] pair_sweep_00/000, pair_sweep_17/017·018, pair_sweep_31/031,
  pair_walk_17/017·018·019에서 같은 frame/Camera/자세로 Skin OFF→ON만 변경했습니다.
  paired_results.json: 입력 native/seed/lighting/ID exact, 다른 부위 출력 exact, depth exact, global0/READY 모두 통과.
  피부 단계: 밝음3→4, 경계17번2→4, 단색18번1→3, 최저광량31번1→3.
  걷기17·18·19번은 이전3·4·3 → 수정4·4·4. 전체 걷기 주기의 수정 후 안정성을 검증한 것은 아닙니다.
  BEFORE의 L RMSE와 AFTER의 E RMSE는 단위가 달라 크기만 직접 비교하면 안 됩니다.
- [종료] 총 raw110개. end_state_after_skin.json: 복원true, 두 수광옵션false, 2px, timeScale1,
  임시조명0, Play 종료 요청. final_editor_state.json에서 Play=false·GameMap1 dirty=false,
  shader/compute messages0·두 수광옵션OFF를 추가 확인했습니다. 씬·재질·renderer 저장값 미변경.
- [실행 중 경계] 수정 후 첫 Play 직후 모델이 아직 CPU-readable 스킨으로 준비되지 않아
  bounds 읽기에서 첫 paired 요청이 출력·상태 변경 전에 중단되었습니다. 다음 실제 걷기 캡처는 준비된 모델로 통과했고,
  미생성 저광량 조건만 이후 실행했습니다. 모델 import/read-write 설정을 바꾸어 우회하지 않았습니다.
  최종 Console은 기존FXC4건+이진단mesh읽기1건=5건을 지우지 않고 남겼습니다. 새 shader/compute 컴파일 오류는 없습니다.
  이후 harness에는 vertices 접근 전 isReadable 사전조건을 추가했습니다(이 사전조건 자체는 정적 확인).
- [재현] import_skin.cs.txt → 기존 start_capture → request.json의 새 batch 지정 → capture_skin_comparison.cs.txt.
  이 harness는 항상 같은 조건의 before/after를 둘 다 저장하며 SkinnedMesh 행렬 갱신 bool도 복원합니다.
  현재 request.json은 이미 존재하는 batch를 가리키므로 그대로 재실행하면 의도적으로 거부됩니다.
  analyze_pairs.py는 픽셀·데이터 불변조건, analyze_trace.py는 GPU/CPU 계산 보고서입니다.
- [예상 다음 수정, 미실행] K/분할을 즉시 재선택하는 대신 이전 분할을 현재 관측 후보에 대응하고
  현재 오차·대비 조건을 검사하는 분할 히스테리시스. 작은 Hair 표본 누락은 별도 문제입니다.
- [자료 저장] package_evidence.py는 모든 메타/최종PNG와 핵심 raw 사례를 gpu_evidence.zip에 묶고
  모든 raw 파일 SHA256 inventory를 남깁니다. ZIP에 빠진 raw도 현재 로컬 디렉터리에 삭제 없이 보존합니다.

참고: 단일 Update 안의 여러 스킨 포즈 렌더에는 forceMatrixRecalculationPerRender가 필요하다는 공식 문서:
https://docs.unity3d.com/6000.0/Documentation/ScriptReference/SkinnedMeshRenderer-forceMatrixRecalculationPerRender.html
