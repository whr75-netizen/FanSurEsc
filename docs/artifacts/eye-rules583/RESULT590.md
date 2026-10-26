# 590 닫힌 속눈썹 영역 — 구현·정적 검증, 실제 실행 차단

> 이 문서는 첫 590 구현 당시의 실패 기록입니다. 현재 구현·실제35쌍·남은 출몰은 [592 결과](RESULT592.md)를 보십시오.

승인된 전환을 제품3파일에 구현했습니다. 기본 `UseLashRegion583=false`는 보존했습니다. **실제 Unity 렌더·시간 품질·미술 채택은 미검증입니다.** 재부팅 후 새 실행은 라이선스 단계에서 종료198이며 새 GIF는 없습니다.

## 구현

- `EyeFeature348.cs`: 기존 ModelEye.closedBoundary와 head-bind rest를 이용해 윗경계 chain을 고르고, 현재 변형 정점과 기존 .36/.22 두께로 닫힌 ribbon을 만듭니다. 기존 CurveArea511의 positive-winding 합집합 면적을 재사용합니다. 같은ROI의4×4 subcell별 기하 면적·깊이·rest-u/v를 작은 buffer로 전달합니다. 뒷면 판정·자원 해제·실제 ribbon bounds 포함을 처리합니다.
- `EyeRenderer367.cs`: 기존550/551흐름에서 buffer와 옵션만 연결합니다. 새 고해상도RT·readback pass는 없습니다.
- `EyeFeature348.compute`: 속눈썹 후보는 native 곡선 영역이 정합니다. 원본4×4 알파는 후보의 존재·두께 통과 조건이 아닙니다. 기존 같은 sample ray의 헤어/눈썹/몸 가림과 N=floor(A+.5), rank를 유지합니다. 색은 현재 같은 눈 S3를 우선하고, 없을 때 기존 template의 같은 눈 role6을 사용합니다. 기하 support=4는 native UV/primitive/barycentric으로 위장하지 않습니다.
- `UseClosedLash590=true`는 위 실험 내부의 비교 gate입니다. `UseLashRegion583=false`인 기본 경로에는 적용되지 않습니다. 검증에서는583을 켜 둔 채 이 gate만 바꾸어583/590을 비교하도록 준비했습니다. 시간 상태나 사용자 설정에 저장하지 않습니다.

좌표·포즈별 예외, 최소1픽셀, 이전 프레임 덮개, 실패한587~589 GPU 알파/half 재현이나 대형 면적 공급기는 추가하지 않았습니다. 홍채582·흰자와 기존 비실험 경로를 유지합니다. 표본 사이의 연속 가림까지 정확하다고 주장하지 않습니다. template 색과 현재 조명 색의 차이도 실제 렌더의 남은 확인 대상입니다.

## 직접 검증

| 구분 | 결과 | 한계 |
|---|---|---|
| 순수C# 기하/저장 입력 | 74검사 통과. 원본24정점 ring을 양 눈에서 재사용해9저장 포즈를 검사. fractional영역·중복/겹침 합집합·정상 축소·회전·깊이/rest 대응 포함 | Unity나GPU를 실행한 결과 아님 |
| 현재 런타임 C# | 저장소의 기존Roslyn response와 Unity참조로 exit0, 경고28개로 기준과 동일 | Editor import·컴파일은 미확인 |
| Editor 검증기 C# | 기존Editor response에 새 검증4파일을 포함해 exit0, 경고53개 | 실제 Editor 실행 전의 컴파일 |
| 현재D3D11 HLSL | Evaluate/UnpackA/UnpackB/Merge 네 kernel 모두 FXC cs_5_0 exit0 | Unity shader import·바인딩·GPU dispatch는 미확인 |
| 지침 문서 | validate_ai_docs.ps1 통과 | 지침 링크 한 곳만 수정 |
| 실제 Unity 실행 | 2026-10-26재부팅 후 검증 실행이No valid license, exit198 | Driver590.Run 이전에 종료. 새 프레임0 |
| 실제9포즈/세 방향/20프레임 | 검증기 준비, 실행0 | 통과로 세지 않음 |
| 미술·시간 품질 | 미검증·미채택 | 기본OFF 유지 |

저장 입력의 eyeID2에 대한 새 기하/기존 가림 모델의 출력수는 case2=0/1/1, case5=0/1/1, case16=1/1/2였습니다. 이는9개 저장 입력으로 계산한 결과이며 새 GPU 선택이나 실제 시간 안정성 합격이 아닙니다. 작은 특징이 계속1픽셀이어야 한다는 기준도 부여하지 않았습니다. 각 포즈의 양 눈 영역은 기록ROI 안에 있었습니다.

## 비용

저장 입력에서 두 눈을 합친 packet은67,584~73,728바이트였습니다. 오프라인 helper는 눈당 약0.18~2.47ms였으며 JIT·파일 준비와 실제 Animator/RenderGraph/GPU를 포함하지 않습니다. 런타임 CPU/GPU·프레임 할당·전체 성능은 미측정입니다. 성능 개선이나 실시간 합격을 주장하지 않습니다.

## 복원 경로와 현재 차단

지원 Unity CLI를 실사용자 권한으로 조회해6000.5.9f1 설치 `C:\Users\15352\Documents\work\6000.5.9f1\Editor\Unity.exe`와 복원 프로젝트 등록을 확인했습니다. 일반 샌드박스 조회의 빈 목록을 실제 미등록 상태로 취급하지 않습니다. 실제 CLI 상태는 signedIn=true, active=false, licenses=[]입니다. 초기 로그인 후 exit0였던 기록과 재부팅 후의 라이선스 차단을 구분합니다. 계정 입력·활성화·약관 수락은 대신 수행하지 않았습니다.

실행 중 쓰는 Gameplay397.ReportFile과 NativePlayer395.Out의JG절대 경로는 프로젝트LocalOnly/Runtime399로 바꿨습니다. AGENTS.md의 확인된 중앙 그래프 링크만15352경로로 수정했습니다. 역사 기록·다른 지침·사용자2설정·기존미추적771파일은 보존합니다. P접근·push·reset/clean·Computer Use는 이번 재개에서 수행하지 않았습니다.

## 재개

활성 라이선스 확인 후 전용 배치Editor에서 Driver590.Run을 실행합니다. 저장9포즈, 세 방향6쌍, 실제보행/회전20프레임을 같은 카메라·포즈의583/590으로 비교하고, 가림·흰자/홍채·눈 밖RGB·색 공급 실패·비용을 판정해야 합니다. 새 전신GIF는 실제 완료된 캡처로만 만듭니다. 현재 비교판의 영상은 과거583이며 새590영상으로 표시하지 않습니다.

작업 증거: `C:\Users\15352\Documents\Codex\2026-10-26\task`의 GEOMETRY_TESTS590.json, CURRENT_STATIC590.json, CURRENT_HLSL590.json, unity-validation590.log, DESIGN590.md, validation590-source/입니다. 기록된 실패 실험과 원본 입력은 기존Current472와저장소eye-rules583에 그대로 있습니다.


## 591 재대조 — 실제Hub등록 수정, 라이선스 상태 후속 확인

[591 상세대조](HUB_LICENSE591.md): 실제Hub DB의JG등록5개를 지원CLI로교체했고 즐겨찾기를보존했습니다. 후속CLI에서는Unity Personal포함활성라이선스2개가 확인돼 새활성화요청을정정했습니다. 이전exit0은실제엔진·컴파일·종료이며 이번198은다른시점의라이선스클라이언트권한0으로엔진진입전실패입니다. 실제렌더검증은아직재실행하지않았고 새GIF는없습니다. 이후설명은590실패당시의차단기록을덮어쓰지않습니다.
