# 실제 캐릭터 헤어 팔레트 연결 비교 60

**임시 GPU 연결을 검증했으며 제품 기본 경로로 적용하지 않았다.** 정상 Play 1회, frame94, sourceId `renderer60-20261031T092325108Z`에서 기존/후보를 같은 포즈·메쉬·카메라·격자로 렌더했다. [INDEX](INDEX.html), [전체/확대 비교 PNG](COMPARE60.png), [셀 수치](CELL_AUDIT60.json), [복원 감사](RESTORE_AUDIT60.json).

## 실제로 연결한 지점

- `RendererFamily59`를 실제 런타임의 3개 source mesh/15개 material 배열에 연결했다. 전체 UV/index 해시로 59의 원본 VRM primitive 대응을 재검증했다. family는 모델 SHA/mesh/primitive/material/image 출처다. 이름이나 RGB로 material을 추측하지 않았다.
- `Compare60.cs:Capture`: 실제 각 hair draw의 원본 UV triangle 중심 32표본, 총 128개를 원본 Texture2D에서 읽어 `SourcePalette58.ExtractReference/MakePalette`를 실행한다. 대표색은 원본 표본 medoid다. 모든 texel 무늬의 자동 분류가 아니라 **재질별** family이며 머리 범위는 기존 runtime role11~14 분류에 의존한다.
- 실제 `surfaceShadeSteps=2`와 같은 Q 임계값 .5를 사용했다. .55 L ratio/.6 C ratio는 기존 58의 **비교용 팔레트 설정**이며 최적 미술값이 아니다. 밝은 끝의 원본 대표 RGB는 draw11 `[95,63,64]`, draw12 `[81,54,55]`, draw13 `[98,65,67]`, draw14 `[138,128,128]`이다. 색 단계는 기존 Q와 독립이다.
- `probe-assets/LegacySignals60.shader:Eye333Fragment`: 기존 continuous 조명 함수 → Q → `SourceLookup54`를 초기 색 MRT에 직접 출력한다. `Independent60.shader:Eye333Fragment`도 실제 hair 독립 레이어에서 같은 LUT를 사용한다.
- `probe-assets/RestoreStyle60.compute:ApplyShadeBoundary`: 역할→실제 source family 버퍼를 사용해 Qprime→P를 직접 조회한다. **old==q일 때도 LUT를 통과한다.** 연속 g×RGB/HairFinal/G를 이 후보 hair 색으로 사용하지 않는다. 원본 셰이더 파일·재질·RendererFeature는 변경하지 않았다.
- main/head의 **런타임 material clone16개, compute clone2개, ComputeBuffer4개**만 임시로 연결하고 해제했다. 실행된 정확한 코드는 `RUN_compare3.cs.txt`이다. `RUN_compare`와 `RUN_compare2`는 Play 전에 각각 상태 검사와 JSON 배열 parser 오류로 중단됐다. 실제 Play 진입은 1회다.

## 동일 프레임 검증

헤어 373 logical cells를 실제 triangle/material/UV/source texel로 연결했다. 출처 미확정 0, 원본 UV triangle 내부 373/373. 동일 source의 g/Q/class/mask와 최종 RGB를 `CELL_AUDIT60.json`에 기록했다. 초기 팔레트 RGB8 불일치 0. 내부263셀, 최종 native1052픽셀은 가족 팔레트/선택 단계와 모두 일치했다.

후보가 연결되지 않은 원본을 다시 비교한 것이 아니다. 헤어의 최종 native1492픽셀 RGB가 모두 바뀌었다. 헤어 밖 최종 float RGBA 변화0, 최종 alpha 변화0, logical owner/selected meta/selected UV 변화0, native owner·depth·visibility 변화0, pose/geometry hash 차이0이다. native 해상도960×544와2×2 셀을 유지했다.

경계110셀 중 **52셀(최종 native208픽셀)은 P 밖 색**이다. 전부 기존 `OwnerLines333.compute:35`의 `c.rgb *= _LineTone`, prefab `lineTone=.55`와 일치한다(선형 최대오차5.07e-9). 예: P `[32,18,18]`→최종 `[22,11,11]`; P `[98,65,67]`→`[73,48,49]`. 내부는 P를 유지하지만 전체 최종색 계약은 외곽선에서 깨진다. 여기서 새 외곽선 팔레트를 임의 적용하지 않았다.

`preparedUV.z`는 9셀에서 primitive 관련 정수 tag를 담으므로 Q라고 해석하면 안 된다. 초기 수치 감사에서 이 점을 발견해 수정했다. 최종 감사는 정확한 role/primitive/UV 대응을 확인한 동일 프레임 source class.x==mask.x를 Qprime으로 사용한다. 원본 `RESULT60.json`과 실제 실행 코드를 보존하며 해석 수정은 `analyse60.py`에 있다.

PNG를 직접 열어 확인했다. 후보는 검정 제품 결과보다 **갈색·밝은 면이 뚜렷하며 텍스처 무늬가 줄었다.** 이는 재질 단위 대표색/진단 팔레트의 실제 차이이고 미술 개선이나 검은 머리 정체성 보존 성공으로 판정하지 않는다. 특징별 세부 family 분류와 경계 형태 보정은 해결된 것이 아니다.

## 종료와 원본 상태

`Compare60.Tick/BeginExit/Finish`가 정상 Play 종료와 update observer 제거를 수행했다. Edit/GameMap1 clean/37roots, live Native395=0, domain1→1. 옵션 enabled=false/None, pipeline 경로, timeScale/captureDeltaTime, pause가 원래 값과 같다. 기존30개 수정 파일 해시와 원래 파일 내용 변화0. RT count30→30이지만 이것만으로 전체 메모리 복원을 주장하지 않는다.

최초24dirty 이후 Play 전 `CommonSurface329.shader`가 추가로 관찰됐다(디스크 변화0, 원인 미확정). 그25개의 내용·ID는 종료 후 모두 유지됐다. 이후 **EditorSettings/GraphicsSettings/TimeManager와 FaceSourceOwner202 메쉬가 추가 dirty**, 최종29개다. 저장/폐기/리임포트/강제 dirty 해제하지 않았다. EditorSettings/GraphicsSettings 디스크 diff0, TimeManager/QualitySettings의 기존 수정도 보호 해시 변화0이다. 얼굴의 vertex attribute584640바이트와 index85464바이트 및 수·형식·read/keep flags는 디스크와 같다. 이는 Play 전 메쉬 native 상태 전체와의 비교가 아니며 morph/bindpose/모든 native cache 동일성을 증명하지 않는다.

Shader global은 코드에서 찾은 scalar/vector/matrix/texture63개 setter를 원래 값으로 호출했다. **원래 값 export와 getter 재비교는 누락**, global buffer binding은 백업하지 않았다. 모든 global state가 동일하다고 주장하지 않는다. 추가 Play 없이 이 한계를 기록한다.

Unity 내부 counter 관찰: allocated +370471101bytes(+353.31MiB), reserved +375816192bytes(+358.41MiB), mono -336244736bytes(-320.67MiB). 물리 working set/누수 판정이 아니다. 실험 소유 자원은 해제됐으나 내부 할당 증가의 전체 소유자는 미확정이다. 강제 GC/Unload/정리를 하지 않았다.

Console 읽기 창에서 새 Error/Exception0, Warning33은 변경하지 않은 EyeCompose333/EyeFeature348 코드의 cold compile 경고다. 후보 ShaderUtil에는 기존 include/keyword에서 유래한 warning2개(_FORWARD_PLUS, Auto245Shadow)가 있다. Console을 지우지 않았다. 관련 경고를 이번 색 계약으로 고쳤다고 주장하지 않는다.

초기 연결 descriptor 원문 출력 시도는 자동 승인 검토에서 실행 전 거부됐다. 안전한 PID/project-only 메타데이터 조회로 대체했으며 비밀값을 출력하지 않았다. 이후 Unity 검증은 승인 범위에서 실행됐다.

## 남은 검증

- 52개 외곽선 색을 유한 palette 계약으로 다룰지 별도 outline palette로 정의할지 결정·구현 필요. 이번에는 원래 외곽 알고리즘을 유지했다.
- 원본 텍스처의 의미 있는 색 패턴 분리와 검정 정체성/명암 면 디자인은 미해결. 재질별2색 후보를 일반 모델 미술 완성으로 확대하지 않는다.
- 정지1프레임이며 회전/blink/시간 연속성과 눈 알고리즘은 미검증. 실제 eye clean backing6표본도 수집하지 않았다. 이 헤어 후보에는 검증된 새 backing pass가 없으며 주변 피부색으로 만들지 않았다.
- 양 팔은 `capturePending=true`를 각각 한 번 사용했다. RenderPose/resetHistory는 사용하지 않았지만 이는 history를 사용하는 시간 안정성 시험이 아니다.

## 오프라인 재검사

저장소 스냅샷에서는 `FRAME60.zip`을 이 폴더에 풀고 `analyse60.py`를 실행한다. ZIP은 저장된 float4 파일만 포함한다. 59 source registry/UV/index 데이터와 NumPy/Pillow가 필요하다. Unity/새 렌더는 실행하지 않는다. `audit_restore60.py`는 현재 원본 프로젝트 디스크와 Git 읽기가 추가로 필요하다.
