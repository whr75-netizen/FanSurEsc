# 완료 확인·정상 종료·Q/meta 연결 후보31

기준 `abcbfe42`. **CPU 코드 검증 단계이며 실행 보류를 유지합니다.** Unity/relay/GPU/Play/import/재시작 호출0, Assets 수정0입니다. 현재 Editor/내부 URP job/미저장 native 상태를 새로 조회하지 않았습니다. 제품77 기본 경로는 바꾸지 않았습니다.

| 변경 | 스크립트·함수 | 검증과 한계 |
|---|---|---|
| 실제 완료 확인 연결 | `SourceOutline31.cs::RecordRenderGraph/EndBarrier`, `ProducerLifetime31.cs::Submission31` | 두 hair 생산자, Q/meta, classifier 전체 출력·depth를 읽는 마지막 Graph pass에 **1×1 RGBAFloat 16B** command-buffer async readback을 연결. 각 source/view/frame/resource generation은 1회만 사용하고 callback 전 재사용 금지. CPU callback이 아니라 성공한 readback 완료가 release 근거이며 실측 callback은 아직 없음 |
| pending 소유권 | `SourceOutline31.TryReleaseOwned`, `PendingViews31<T>` | Graph 등록 전 보수적으로 commands 가능성을 기록. partial failure에도 end pass는 drain을 시도하고 실패 픽셀은 무효. error/미완료/불명 enqueue는 해제하지 않고 한 view당 strong-root owner를 유지. 예전 전체 host assembly·115 평가기 의존성 제거 |
| 종료와 해제 분리 | `ExitCoordinator31.Begin/Pump`, `SourceCaptureHost31.BeginExit/PumpExit` | detach/복구/Dispose 예외가 정상 Exit 요청을 건너뛰지 않음. Exit 요청은 1번만, GPU release와 Edit 옵션 복구는 별도 진행. pending을 timeout으로 해제하지 않음. 실제 Editor 종료/복구는 이번에 실행하지 않음 |
| Q/meta 대응 | `face31/QMeta31.shader`, `LineClass31.compute`, `SourceOutline31.DrawQ/Classify` | 기존 LegacySignals335의 **초기 Q 함수**를 재사용하고 같은 fragment에서 metadata를 SV_Target4로 동시 출력. 두 RT의 ROI·깊이·alpha가 정확히 대응하며 `native960`/`2p+1` 추정 조회를 제거. logical ROI+1 halo의 정수 Load만 사용. crop된 SV_Position은 backend Y 방향에 따라 full-head 좌표로 되돌려 조명 계산에 전달 |
| 무효화 | `SourceOutline31.MaterialVersion31/Prepare`, `SourceCaptureHost31.Arm` | material CRC, texture identity/updateCount/image hash, 모델 topology·카메라·material graph를 검사. 단일 제출이며 모델 교체·재초기화는 새 owner 필요. 같은 view의 미완료 owner가 있으면 새 arm 거부. 이 public getter들의 실제 Editor 동작은 미검증 |

## CPU 결과

- `verify_lifetime31.py` / `LifecycleTests31.cs`: **50개 통과**. 완료 전·오류·다른 view/세대·중복 callback·partial/cancel·종료/Dispose/복구/완료조회 예외·다중뷰·재초기화·격자/halo/양쪽 Y 방향·무한대 반례입니다. 실제27 ROI18×8의 144셀 대응을 검사하지만 그 ROI나 눈 크기를 알고리즘 상수로 사용하지 않습니다.
- `prepare_lifetime31.py`: 후보 C#을 Unity metadata 참조로만 컴파일했습니다. `Json58Reference31.cs`는 기존 bounded JSON helper만 그대로 추출하고 `Projection31.Crop`은 기존26 수식을 그대로 재사용합니다. 예전 실행기 DLL은 참조하지 않습니다. 새 셰이더는 **정적 검토만** 했으며 GPU variant compile/import를 하지 않았습니다.
- 결과: `CPU_LIFETIME31.json`, `CPU_INTEGRATION31.json`, `BOUNDS31.json`. 자원·dispatch 숫자는 CPU 상한 계산이지 GPU 시간·드라이버 메모리 측정이 아닙니다. 새 평가/BVH/전수 탐색 커널은 없습니다.

## 연결 범위와 재개 조건

`SourceCaptureHost31`은 `IRunCommand`도 자동 실행기도 아닙니다. 기존 stable Play에 외부 관찰기가 명시적으로 `Arm`해야만 own pass를 enqueue하며, 이 코드가 Play에 들어가거나 옵션·InputSettings·기존 재질/renderer를 바꾸지 않습니다. 정상 종료와 pending callback의 managed root를 보존하려면 외부 허용 범위에서 **domain reload가 이미 비활성화**되어 있어야 합니다. 이 조건을 검사할 뿐 설정하지 않습니다. 관찰기는 `BeginExit` 후 `PumpExit`를 호출하며, 이미 있는 외부 백업/journal에 근거한 before-exit/after-Edit 복구 action을 제공해야 합니다. arm 실패 시에는 생성한 own producer를 Dispose하는 일반 호출자 책임이 있습니다. 새로운 Play를 시작할 외부 scope는 먼저 `PendingOwnerCount==0`을 확인해야 하며, 이 값도 URP 전체 안전 증명은 아닙니다. 같은 Play의 서로 다른 view는 격리 소유자를 가질 수 있습니다.

다음 단계도 현재는 실행하지 않습니다. 재개 판단에는 최신 공개 Editor 상태와 원본 보존 기준, 새 shader-only import/실제 variant·8×8 ABI, 동일 입력의 Q/metadata/원본 깊이·alpha 대응, 성공/실패 callback 및 normal Exit 후 자원 수명 검증이 필요합니다. 현재 private URP handle 상태는 미확인이고, 미완료 readback 또는 domain/assembly reload가 발생하면 완전 복구를 보장할 수 없습니다. error callback은 release 증명으로 취급하지 않으므로 owner가 의도적으로 남을 수 있으며, 강제 GC/해제/재시작으로 지우지 않습니다.

**Q 의미는 초기 명암 범위 번호입니다.** 기존 `ApplyShadeBoundary` 이후의 Qprime과 동등하다고 주장하지 않습니다. 같은 fragment라는 대응을 확보하려고 만든 독립 관측 경로이며, 기존 제품의 Q를 바꾸지 않았습니다. 중간 colour/lit/shade MRT는 기존 shader 연산을 유지하기 위한 진단 출력이며 유한 팔레트 완성의 증거가 아닙니다. non-depth-writing blend의 부분 투과, 전체 얼굴 영역화·최종 팔레트·외곽선·미관·시간 안정성은 여전히 별도 미완입니다.

API 근거: [CommandBuffer.RequestAsyncReadback](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Rendering.CommandBuffer.RequestAsyncReadback.html)의 command-buffer 요청과 완료 callback 계약을 사용합니다. 플랫폼별 fence 의존성을 새로 추가하지 않았습니다. 이 문서와 CPU 통과는 현재 GPU/URP 세션이 안전하다는 증명이 아닙니다.
