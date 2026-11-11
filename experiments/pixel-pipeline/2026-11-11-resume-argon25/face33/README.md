# 얼굴·외곽선 실제 GPU 관측33

기준 `568479d6`. 제품77과 후보31의 원본 파일은 유지했습니다. 이번에는 CPU 검토에서 멈추지 않고 새 셰이더 3개를 shader-only import하고, 정상 Play **1회·실제 프레임95 1개**를 관측했습니다. 화면 제어·초기화·강제 종료·저장·EvaluateForm115 실행은 없습니다.

## 구현과 실제 실행

- `prepare_runtime33.py::main`은 31/32에서 검토한 `SourceOutline/SourceCaptureHost`를 고유33 타입으로 연결합니다. C#은 Assets에 넣지 않고 기존 공식 relay의 동적 실행기를 사용했습니다. 전체 import/capture/final 명령을 Roslyn으로 먼저 컴파일했습니다.
- `Import33.cs.txt::Execute`: 새 `Assets/EUnityValidation01/SourceBoundary33`에 SourceOutline33/QMeta33/LineClass33만 추가했습니다. 기존 자산 덮어쓰기·전체 Refresh·C# import·SaveAssets는 없습니다. 실제 GUID/variant/kernel8×8×1/지원 여부와 native46개 내용·입력·옵션을 확인했습니다.
- `Capture33.cs.txt::Execute/Tick/Exit/Restore/Finish`: 정상 Gameplay397.Present 경로의 head camera에 `SourceOutline33`만 등록합니다. 구식 Forward113/LayerZero와115 평가는 연결하지 않습니다. 생산은 한 번, private 소유 RT만 읽고 빌린 입력은 해제하지 않습니다. 외부 백업→임시 background/DisableDomainReload→동일 프레임 고정→end callback→단일 consumer lease/최대262144B→정상 Exit→소유자원 drain/복원입니다. callback에서는 byte 복사·신규 파일 기록만 수행하고 Editor 작업은 main-thread pump가 처리합니다.
- `SourceOutline33::Prepare/DrawQ/Classify/EndBarrier`: source silhouette/pigment의 물리8× 표본, 동일 fragment의 초기 Q/meta, 기존 Qprime/proposal·Q0/rawmeta/effective-normal/UV를 같은 프레임에서 보존했습니다. 논리 ROI22×23, Q ROI28×29/halo3. 분류 dispatch는 3×3그룹×64=576 threads, 유효506셀, 셀당64개 coverage 표본+고정4이웃이며 BVH/조합 열거는 없습니다. 원본 Q 생산/깊이 패스는 현재 mesh/material을 사용합니다.
- 실제 실행 소스는 `import/RUN.cs.txt`, `capture/RUN.cs.txt`; `REQUEST/REPLY`, `COMPLETE.json`이 실행 근거입니다. 과거 helper의 “review only” 주석은 유래 주석이며, 이번 실행 여부는 이 receipt로 구분합니다. 이미 실행한 명령은 생성기가 다른 내용으로 덮어쓰지 못하게 차단했습니다.

## 실측과 판정

`analysis/ACTUAL33.json`, `FACE_GATE_CELLS33.json`, `ACTUAL_Q_BOUNDARY33.png`, `q0.png`/nearest4를 직접 확인했습니다. q0 이미지는 **원본 재질 기반 초기 색 경로**이며 최종 캐릭터/최종 외곽선 합성 PNG가 아닙니다. 이번에 새 미술 보정이나 LUT를 제품 기본값으로 활성화하지 않았습니다.

- 실제 sourceId/frame95, 전체21 strip/3,220,896B. 얼굴59셀 모두 같은 깊이에서 clone 초기Q=기존 초기Q, Qprime 적용식도59/59 일치했습니다. 미관측 쌍을 오차0으로 처리하지 않았습니다. 얼굴 외 geometry/domain 전체의 동등성은 주장하지 않습니다.
- **실제502 분기는 disabled/Ready=false**이고 기존15재질은335 LegacySignals였습니다. 그러므로32의 조건부502 classifier.Y 결함은 이번 프레임의 원인이 아닙니다. 해당 shader patch는 미적용입니다.
- 기존 얼굴 Q0는0/0.5 두 값, continuous0.015662..0.402860. proposal/Qprime 변경0셀.59셀 중 안전한8이웃 조건을 통과한 셀0, tip topology4셀, eligible0입니다. 후보 좌표 `(220,56)`, `(215,55)`, `(220,54)`, `(223,53)`은 effective-normal 또는 role/owner/alpha/깊이 조건으로 막힙니다. 이는 현재 구현이 이 프레임을 수정하지 않는 구체적 이유이며, 임계값을 풀어야 한다는 증명은 아닙니다.
- raw[2]는 geometry-only normal이 아니라 **MToon normal map이 적용된 effective normal**입니다(`VisibilityMotion331/Shaders/Probe331.shader::Probe288Fragment`). 현재 `FullFeature367.ShadeBoundary`가 이것을 `_ShadeNormal335`에 연결합니다. normal-map 변화와 실제 surface crease를 같은 hard gate로 보는 전제가 다음 검토 지점입니다. geometric normal(raw[1])은 이번 packet에 없으므로 둘의 차이를 실측했다고 하지 않습니다. 다음 관측이 필요할 때 이 필드만 추가하면 됩니다.
- source outline coverage는19논리셀/총0.734375셀 상당, 최대0.0625. pigment는17셀/총1.274995셀 상당, 최대0.199442입니다. 이는 같은 표면의 실제 얇은 색소/선 근거이며, 커버리지가 있다는 이유만으로 셀 전체를 그 색으로 채우지 않았습니다. 최종 선의 표현 두께·폐합/gradient/AA 분류와 유한 팔레트 대입은 여전히 별도 미완입니다.
- 초기 얼굴59셀 RGB는53색입니다. Q 라벨의 유한성은 최종 RGB의 유한 팔레트 완료를 뜻하지 않습니다. 확정된 face UV region→LUT binding이 없으므로 “palette 밖53색”으로 집계하지 않습니다. 87a5475c의 확정 region 입력 인터페이스를 사용할 수 있으나 볼 칠/gradient/AA를 임의 분류해 채우지 않습니다.

**메타 해석 정정:** 실제 실행 FrameInfo의 inherited caption `raw role-owner-depth-alpha`는 부정확합니다. q7=raw[5]는 `(viewDepth, role+1, sourceInstanceId, primitiveId+1)`로 W가 alpha가 아닙니다. q8=raw[2]는 `(effectiveNormal, front/back)`, q9=raw[6]는 `(UV, primitiveId+1, renderer+1)`입니다. `analyze_runtime33.py`는 실제 Probe331 생산자 schema를 사용하며 기존 JSON을 수정하지 않았습니다.

## 복원과 한계

- 11:29:31→11:30:54UTC 실제 Play 정상 종료, pending owner0, producer/consumer 완료 후 소유 RT/material/compute 해제, observer 제거. 새 Console 오류0건. 종료 후 공식 Console12항목은 사전 목록과 동일한 과거17:15(local)/08:15UTC 오류입니다. URP private job/과거 TDR의 모든 원인을 해결했다는 뜻은 아닙니다.
- native47항목 중46내용 동일. 추가1개는 `ProjectSettings/ProjectSettings.asset`의 **AssetImporter**가 미로드되어 Unavailable입니다. **PlayerSettings 본체는 동일**합니다. unloaded importer를 동일하다고 세지 않았습니다.
- 입력 객체 `568105589213756420`와 JSON22값/장치, globals74 getter, scene clean, time/pipeline/background/options을 보존했습니다. 11:33:20UTC 최종 공식 조회는 Edit/not compiling/not transitioning, GameMap1 clean, project dirty31, options=false/None, background=false입니다.
- Profiler.GetTotalAllocatedMemoryLong 1,770,976,401→1,805,269,918B(+32.70MiB), reserved+0.75MiB, Mono used−238.27MiB, RT30→30. 프로세스 working set과 다른 카운터이며 누수 확정/해소를 주장하지 않습니다. journal/관찰기의 소유 참조는 정상 종료 시 해제했습니다. 재로드·다중뷰·device error/미완료 callback 스트레스 검증은 이번1프레임으로 입증하지 않았습니다.
- 실제 safety stop 재개 조건의 정상1프레임은 확인했습니다. **전체 얼굴 UV 영역·유한 RGB·최종 외곽선·움직임 안정성의 완료가 아닙니다.** 다음은 새 threshold 반복보다 geometric/effective normal hard gate의 역할과 확정 region/선 표현 계약을 검토하는 것입니다. 제품77과 사용자30은 유지합니다.

외부 native 백업 원본은 작업폴더 capture/import 아래 보존합니다. 저장소에는 백업 내용 전체·빌드 DLL 대신 실행 receipt/해시와 실제 raw packet zip을 보관합니다.
