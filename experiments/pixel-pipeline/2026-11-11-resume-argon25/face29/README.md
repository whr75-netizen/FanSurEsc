# 얼굴 영역·선 생산자29 — 실시간 검증 실패, 수정안 미적용

기준3a64d1a3. 제품77 기본값/사용자 tracked30을 바꾸지 않았습니다.

| 작업 | 코드·결과 | 판정 |
|---|---|---|
| gradient/AA 주변 지지 영역 | `affine_support29.py::intervals/probe/trace_native`, `test_affine29.py`, `review_support29.py` | 6개 원본 flank의 half-code interval에 맞는 affine 배경 전체를 검산.16검사 통과했지만 비선형 경사 반례가 있어 전체 색소/AA 분류기로 미채택 |
| 실제 볼 선 | `AFFINE_NATIVE_COMPONENT29.json`/`SOURCE_SUPPORT29.png` | native 반경2/4에서98/21텍셀. 인접 경계109/26개 중91/12개는 배경모델 불성립. source 전체에서 추적했으며 ROI 잘림이 아님. 픽셀 집합의 폐합과 색소/AA 영역의 올바른 폐합을 구분 |
| 원본 실루엣 생산자 | `SourceOutline29.cs`, `prepare_source29.py`, 새 Asset `SourceBoundary29/SourceOutline29.shader` | 설치 MToon의 world normal extrusion/원본 outline slot/재질 alpha를 사용. shader-only import 컴파일·전후 상태 비교 성공. 실제 raster 결과 확보는 실패 |
| 색소/Q 분리 입력 | `LineClass29.compute`, `import_class29.py` | CPU D3DCompile와 Unity import,8×8 ABI 통과.64표본+4이웃 고정, BVH/조합탐색/115 없음. RGB 변경용 패스가 아니라 독립 근거 채널. 실제 dispatch는 기록 전 실패 |
| 런타임 실패 | `FIRST_ERROR29.txt`, `ERROR_CAUSE29.json`, `run/RUN_Capture25.cs.txt` | 제가 canonical DenseNative107을 physical ROI로 잘못 연결했습니다. `SourceOutline29.Record` guard 예외가 RenderGraph 기록을 중단하고 이후 URP ZBinningJob 안전성 예외가 발생했습니다. 완료 packet/실제 검증 PNG0, 성공으로 세지 않음 |
| 최소 수정 후보 | `physical-fix/SourceOutline29.cs`, `SourceOutline29.shader`, `UNAPPLIED_SHADER29.patch`, `CPU_PHYSICAL29.json` | source pigment를 원본 mesh/material의 별도 physical8x 패스로 바꾸고 같은 VP/ROI에 붙임. 사전 검증 및 own 예외를 Graph 밖에서 처리. 전체 외부 C# CPU 컴파일만 통과. Assets 적용/import/실제 실행 모두 안 함 |

## 좌표 및 의미 계약

`NativeDense107.RecordGraph`의 grid는 native-to-authored projection/Anchor96/Bounds96의 canonical 공간입니다. 단순히 너비·높이가 physical ROI×8과 같더라도 물리 공간이 아닙니다.27 실제 입력의 dense144×64와 outputROI18×8은 우연히 차원이 맞지만, 원래 `eye.roi` 또는 카메라 투영과 같은 계약이 아닙니다. 이 점검 누락이29 실패 원인입니다.

최신 CPU 후보는 원본 material3 실루엣과 기존 verified native role6 pigment를 **같은 current evaluated mesh/물리 VP/ROI/8x sample grid**에서 생성합니다. 피부를 가까운 눈으로 나누지 않습니다. 원본 geometry/depth·material alpha/discard/depth-write를 유지하며, non-depth-writing blend 재질의 분수 transmittance는 아직 별도 한계입니다. 클래스 채널은 native outline alpha, native pigment alpha, 독립Q 전이와 유효성 플래그이며 중첩 가능합니다. 이 채널을 최종 눈/피부 소유권 또는 선 두께 결정으로 확대하지 않았습니다.

원본 RGB만으로 고유한 paint/gradient/AA 레이어를 복원할 수는 없습니다. 실제 centre I=(253,228,208)은 opaque field I와 alpha.5·pigment(252,220,202)·background(254,236,214)로 정확히 같게 재현됩니다. 이는 자동 추상화 불가능의 증명이 아니라 **선택할 배경/특징 prior가 필요함**을 보여줍니다. affine prior는 smooth quadratic에서도 잔차를 내므로 현재 전체 얼굴에 적용하지 않았습니다. 임의 색 수·색 임계값 탐색·blob 최소면적 삭제·색 평균으로 우회하지 않습니다.

## 실제 중단 및 보존

- 08:14:53~08:15:04UTC Play1회 후 정상 종료했습니다. source classifier 패스는 guard 뒤에 있어 dispatch가 기록되지 않았습니다. 추가 GPU/Play/renderer 재생성/재시작은 하지 않았습니다. 로그에 이 오류 뒤 device reset은 없지만 GPU/URP 내부 job 정상화를 증명하지는 못합니다.
- 08:20:32UTC 공개 조회는 PID28080 Edit/비컴파일/비전환/비pause, OS Responding=true였습니다. 종료 후 새 예외 header 추가0. 내부 job handle은 공개되지 않아 직접 Complete/반사 호출로 해제하지 않았습니다.
- 원래 project dirty 목록과 scene은 동일, native47개 중46개 내용 동일/clean AssetImporter1개 수명 Unavailable, InputSettings 동일 참조·22값·장치, 옵션/시간/pipeline/custom global74 복원, RT30→30, own source 자원 Dispose=true. 경로 없는 Editor 내부 Object/SceneVisibilityState2개가 추가되어 전체 세션 등가성은 미확정입니다. ClearDirty/기본값 추정 복원을 하지 않았습니다.
- `RESTORE_MEMORY29.json`: 이번 Play의 Profiler allocated+60.05MiB/reserved+.125MiB/Mono-393.16MiB. 턴 초기 OS 조회와08:20 조회 사이 private commit+3.777GiB, WorkingSet도 증가. 초기 OS UTC가 없어 동일11초 구간으로 오해하면 안 됩니다. 실패 후보의 소유 RT 상한은 약17MiB이며 이는 OS 증가 원인을 설명하지 못합니다. leak root/native/driver 보유량 미확정, 강제 GC/Unload/정리0.
- 08:40:43UTC 마지막 OS 조회는 Responding=true/private commit6,959,677,440B로 내려왔으며 초기보다181.53MiB 높습니다. 약3.78GiB peak는 대부분 자연히 되돌아갔습니다. 이를 누수 해결이나 private URP job 해제 증명으로 바꾸지 않습니다.

## 재현·다음 단계

CPU만: NumPy/Pillow가 있는 Python에서 `python test_affine29.py`, `python review_support29.py`.28의 보존된 실제 source subset을 사용합니다. `prepare_physical29.py`는 제안된 외부 host를 CPU 컴파일하며 Unity를 호출하지 않습니다. 실제 실행한 잘못된 runner는 PHASE_REQUEST/시작 marker로 재실행 차단되어 있고, 최신 후보는 `physical-fix`입니다.

**현재 기술 차단:** 반복된 URP lifetime 오류에 따른 안전 정지입니다. 공개 Edit 상태만으로 내부 job 해제를 확정할 수 없어 수정 후보를 다시 Play하지 않았습니다. 재개 시 먼저 검증할 것은 새 physical source 계약/실패 격리이고, 전체 렌더 반복이 아닙니다. 색 영역화는 별도로 source prior 및 AA/gradient 경계를 검증해야 하며 사용자에게 새 고정 셀수·갈색 선택을 요구하지 않습니다. 실제 새 렌더 결과가 없어 GPU PNG 업로드는 하지 않았습니다.

`EVIDENCE29.zip`에는 필요한 원래 명령·receipt·상태·오류만 보존하며 raw PlayerSettings/native 설정 백업은 작업폴더에 유지하고 저장소에는 복제하지 않습니다. 최신 경로·커밋 색인은 중앙 `docs/ai/PIXEL_ALBEDO_20261030.md`29절, 무결성은 `ARCHIVE29.json`입니다.
