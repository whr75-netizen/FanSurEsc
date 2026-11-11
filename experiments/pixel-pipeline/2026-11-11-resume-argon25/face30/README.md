# 안전 정지 중 CPU 검토30

기준 커밋 `f7a4ea84`. **실행 보류이며 `runtimeReady=false`입니다.** 이 단계는 Unity/relay/Play/셰이더 import/GPU 호출을 하지 않았고 현재 Editor 상태도 새로 조회하지 않았습니다. 29의 마지막 공개 상태와 메모리 관측은 과거 기록으로만 남깁니다. 제품77 기본 경로와 Assets는 변경하지 않습니다.

## 실제로 검증한 수정

- `ProducerContracts30.cs::GridBinding30.RequirePair`: canonical 공간과 physical head 공간을 분리합니다. source/view/model/frame/sequence, ROI 원점·범위, 8배 표본 격자, 유한한 world→cropped-clip 행렬이 모두 일치해야 합니다. `HeadX/HeadY`가 상단 원점 head와 하단 원점 RT의 표본 중심 대응을 명시합니다. 크기만 같은 입력은 충분하지 않습니다.
- `prepare_review30.py::main` → `face30/SourceOutline30.cs::RecordChecked`: 같은 evaluated mesh/material의 physical pigment와 outline을 동일 VP/ROI에 공급하는 29 미적용 후보에 계약 검사를 연결했습니다. 자체 Graph pass 등록 전에 검사하고 관리 예외는 `FailureBoundary30`으로 Graph 밖에서 전달합니다. 이는 선언/바인딩 일관성 검사이며 실제 래스터 동등성 증명은 아닙니다.
- 생성기의 광범위 문자열 치환이 셰이더 자산 경로와 `_SourceOutline29` uniform까지 잘못 바꾸는 오류를 수정했습니다. C# 타입·생성자·owner 참조만 이름을 바꾸며 기존 shader/compute/kernel ABI 보존 6항목을 검사합니다.
- `verify_contracts30.py` / `ContractTests30.cs`: 관리 코드 CPU 회귀 **38개 통과**. 실제27의 canonical 144×64와 output ROI18×8×8이 우연히 같은 반례를 사용했습니다. 양성 physical 행렬은 저장 카메라에서 계산한 **합성 CPU descriptor**이며 실제 backend GPU projection/새 GPU 출력이 아닙니다. `CPU_CONTRACT30.json`, `FIXTURE30.json`에 출처가 있습니다.
- `prepare_review30.py::compile_source`: 외부 C# 후보와 계약을 Unity DLL의 metadata 참조로만 컴파일했습니다. Unity 프로세스에 assembly를 로드하지 않았습니다. 성공한 컴파일은 실행·렌더 검증이 아닙니다. 실행 명령 runner도 생성하지 않았습니다.

## URP 예외의 근거와 한계

`audit_sources30.py`의 설치 소스 의무 검사 6개가 통과했습니다. 설치 URP `ForwardLights.PreSetup`은 `IsCompleted` 확인(387행) 뒤 `m_ZBins.GetUnsafePtr` 쓰기(404행)를 합니다. 실제 29의 후속 실패는 이 쓰기에서 발생했습니다. `SetupLights`의 `Complete()`(491행)는 기록된 pass의 **실행 callback**에 있습니다. 자체 `Record` 예외가 `EndRecordingAndExecute`를 건너뛰면 이 callback도 실행되지 않는 구조입니다.

따라서 **작업이 끝났어도 NativeContainer 소유권 회수가 누락되는 경로**가 관측된 예외 순서를 설명합니다. 작업 스레드가 계속 실행 중이었다는 확정은 정정합니다. [Unity 공식 Job 문서](https://docs.unity3d.com/2021.2/Documentation/Manual/JobSystemTroubleshooting.html)의 `Complete()`를 통한 소유권 회수 규칙과도 일치합니다. 버전별 근거는 `SOURCE_AUDIT30.json`의 설치 파일 SHA/행 번호입니다. 현재 private handle 상태, 과거 GPU reset 및 메모리 급증의 정확한 원인은 이 정적 검토로 확인되지 않았습니다. 내부 handle 반사 호출·강제 Complete·renderer 재생성은 하지 않았습니다.

Q/meta 격자는 별도 미완입니다. `Full319View335`의 `nativeShift`에는 X 반 native pixel 및 backend flip에 따른 Y 보정이 있습니다. 그러므로 `2p+1`만 보고 무조건 1/4셀 오정렬이라고 단정하지 않습니다. 실제 `motion.clipShift`, `nativeShift`, projection/viewport, alpha/geometry domain의 대응을 함께 검증해야 합니다.

## 재개 전 남은 필수 조건

1. **GPU 완료·수명 연결:** callback/`RenderedFrame`은 GPU 완료 증거가 아닙니다. hair ON/OFF 양쪽 producer와 classifier의 의존성 및 end barrier를 명시하고, 동일 source/view/model/frame/sequence의 실제 stamp/fence/readback 완료 후에만 결과 인정·자원 재할당/해제를 허용해야 합니다. 실패·취소·부분 command 기록·중복 callback도 포함합니다. `WorkReceipt30`은 이 조건의 CPU 모델일 뿐 live `Dispose`에 연결되지 않았습니다.
2. **종료 구조:** 현재 `BeginExit`는 `exiting=true` 뒤 `Release76`을 호출합니다. pending 시 `Dispose`를 단순 throw로 바꾸면 정상 Play 종료 요청도 건너뛰므로 채택하지 않습니다. 정상 종료 요청은 한 번 보장하고, 소유 자원 drain은 완료 증거에 따라 별도로 처리하는 코드가 필요합니다. 불명 결과 재제출·조기 해제는 금지합니다.
3. **입력·캐시:** 실제 Q/meta 생산자의 격자/위상/원본 geometry·alpha 대응과 동일 객체의 material/texture content generation 무효화를 완성해야 합니다. 모델 교체·재초기화·다중뷰의 소유권을 검증해야 합니다. non-depth-writing blend의 부분 transmittance는 아직 지원 증명이 없습니다.
4. **미적용 shader/현 세션:** physical pigment pass는 29의 미적용 shader patch에 의존합니다. 현재 자산은 그대로이므로 후보를 바로 실행해서는 안 됩니다. 위 CPU 코드 연결을 마친 다음에만, 별도로 허용된 재개 단계에서 최신 공개 상태/자산·입력·옵션 기준을 다시 확인하고 최소 source producer 한 프레임을 검토할 수 있습니다. 현재 세션의 private URP 안전 상태는 미확인이며, 공개 상태가 나쁘면 실행하지 않습니다. 임의 재시작/초기화로 통과시키지 않습니다.

이번 결과는 **격자 계약·예외 경로의 CPU 검증**입니다. 얼굴 영역화·외곽선 분류, 팔레트 최종 출력, 실제 래스터·부분 가림·미관·시간 안정성의 개선 결과가 아닙니다. 29의 실패 marker/runner와 백업은 변경하지 않습니다. 변경 파일·결과·커밋은 기존 중앙 인계30절에서 찾을 수 있습니다.
