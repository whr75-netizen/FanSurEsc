# WorkLoop v2 — 단위 알고리즘의 절차 그래프

## 현재 계약과 선택

사용자 정정(2026-09-13): 큰 작업에서 신뢰성을 스스로 관리할 기반이 충분하다고 가정하지 않고, 담당 작업·관련 정보·피드백 절차를 제공하여 보완한다. 담당 범위 안의 추론과 도구 선택/사용은 Codex가 수행한다. 전체 목표·완료 조건·작업 사이의 분기는 프로그램이 관리한다. AI를 사용할 수 없는 수준으로 세부 도구 호출을 고정하지 않는다.

v1은 AI가 status, verdict, add/drop/reopen을 제출하는 작업 관리자였다. 이 입력들을 없애고 같은 진입점의 v2 알고리즘 실행기로 교체한다. 이전 v1 상태는 보존하며 v2에서 자동 실행/승격하지 않는다.

사용 흐름은 **사용자가 Codex에 개발 요청 → 프로젝트 지침 → Codex가 작업 단위를 실행기에 연결 → 담당 작업 수신 → 기존 도구로 개발 → 산출물/관측 반환 → 다음 절차**다. 사용자가 JSON이나 실행기 명령을 매번 작성하지 않는다. Codex가 기존 템플릿을 재사용하거나 필요한 작업 구성을 작성한다. 이는 지침에 따른 호출이며 Codex 앱의 모든 명령을 자동 가로채는 기능은 아니다.

게임 개발의 기본 인계는 ai.work다. 예를 들어 '인벤토리 이전 실패 시 원본 보존 구현'이라는 부위·관련 파일·입출력 계약·반환물을 주고, 코드 검색이나 Unity MCP의 세부 호출 순서는 Codex가 정한다. 한 줄 편집이나 개별 도구 호출마다 별도 노드를 만들지 않는다.

| 후보 | 결정과 근거 |
|---|---|
| 지침 + v1 작업 목록 | 완료/수정 판단을 AI가 제출하므로 최신 계약에 부족하다. |
| 단위 알고리즘 + 명시적 상태 전이 | 채택. 실제 계산·출력 형식·전이·완료 판정을 코드로 분리한다. |
| 대형 그래프 프레임워크 | 현재 필요한 로컬 순차 실행보다 설치/통합 범위가 크다. 필요해질 때 재검토한다. |

[Higgsfield Canvas 공식 설명](https://higgsfield.ai/creator-hub/help-center/tools/how-do-i-use-canvas)은 모델 노드의 입출력 연결, 순차/병렬 실행과 템플릿을 공개한다. [Supercomputer 설명](https://higgsfield.ai/creator-hub/help-center/tools/how-do-i-use-supercomputer)은 에이전트의 계획과 실행을 설명한다. 내부에서 정보기하학으로 AI의 판단 주체성을 제거한다는 구현은 이 자료로 확인할 수 없다. 공개된 노드 연결 개념과 사용자의 더 엄격한 역할 계약을 구분한다.

## 수학과 권위 경계

각 단위는 `y_i = f_i(x_i; θ_i)`다. 입력 x_i, 등록된 알고리즘 f_i, 고정된 매개변수 θ_i, 출력 계약을 만족하는 결과 y_i를 명시한다. 큰 작업을 여러 제목으로 나눈 목록으로 대체하지 않는다.

다음 상태는 `s_next = δ_G(s, y_i)`로 계산한다. AI가 반환한 자연어 결론은 δ_G를 바꿀 수 없다. 그래프 G와 실행기 코드는 실행 중 고정한다. ai.map은 계산 결과를, ai.work는 도구를 사용한 작업의 산출물/관측을 반환한다. ai.work의 내부 방법 선택과 전체 그래프의 목표·분기 변경은 구분한다. 정보 계약과 출력 소비 알고리즘은 담당 범위와 반환 경계를 관리한다. 모델 내부 분포나 Fisher 계량을 구현했다는 뜻은 아니다.

Guard는 참/거짓/미정이다. 관측 누락은 거짓이나 성공 기본값으로 바꾸지 않는다. 참인 분기가 하나이고 나머지가 모두 거짓일 때만 이동한다. 여러 참, 미정, 전부 거짓은 각각 차단한다. 실패/복구도 명시한 간선으로만 이동한다. 완료는 마지막 validation 노드에서, 고정된 모든 요구 predicate가 참일 때만 가능하다.

실행 계약을 AI가 자연어 요구에서 잘못 번역하면 잘못된 계산을 정확하게 수행할 수 있다. 계약 작성 시 사용자 요구의 원문/문서 참조와 알고리즘의 실제 의미를 연결한다. 프로그램은 자연어 요구의 모든 의미를 증명하지 않는다. 해시는 우발적 변경 탐지이며 파일/엔진 자체를 수정할 권한이 있는 AI를 격리하는 보안 장치는 아니다.

## 알고리즘 레지스트리

| ID | 입력 → 출력 | 용도 |
|---|---|---|
| value.identity | JSON 값 → 같은 값 | 명시된 입력 전달 |
| math.reduce | 유한 수 목록 + sum/mean/min/max → 수 | 통계 계산을 일반 코드로 실행 |
| value.compare | 같은 타입의 값 + 비교 연산 → boolean | 고정된 비교 기준 계산 |
| json.select | JSON 문서 + 키 경로 → 값 | 실제 도구 출력 필드 추출 |
| file.inspect | 파일 경로 → 절대 경로/크기/SHA-256 | 파일을 프로그램이 직접 관측 |
| command.run | 고정 argv/cwd + JSON stdin → exit code/stdout/stderr | 외부 알고리즘을 shell=False로 실행 |
| ai.map | 입력·질문·출력 schema → JSON 후보 | AI를 제한된 계산 함수로 호출하는 연결점 |
| ai.work | 담당 범위·입력·반환 형식 → 산출물/관측 | Codex가 기존 도구를 선택·사용하여 개발하는 인계 |

새 자동 계산 함수를 실행기에 넣을 때는 알고리즘을 등록한다. ai.work에서 사용하는 기존 코드 편집·CLI·Unity MCP 등의 도구마다 새 어댑터를 등록할 필요는 없다. 일반 계산 구간은 run 한 번으로 연속 실행한다. 자체 모델/API 호출은 없으며, 활성 Codex가 ai.map/ai.work의 인계를 받아 같은 작업 안에서 수행한다. 사용자 요청과 프로젝트 계약이 수행 범위를 계속 제한한다.

command.run은 실행 권한을 새로 부여하지 않는다. 이미 승인된 범위의 도구/명령만 계약에 넣는다. 명령/cwd는 고정 매개변수이며 AI 출력으로 치환하지 않는다. stdin으로만 JSON 데이터를 전달한다. 기본 timeout 30초, 최대 60초다. 외부 요청의 정확히 한 번 실행, 비동기 서비스 취소, Unity MCP 직접 호출 어댑터는 아직 없다. 실제 Unity 동작과 원격 생성 확인에는 해당 도구의 관측 어댑터가 필요하다.

위 어댑터 한계는 실행기가 Unity/서비스를 직접 자동 호출하는 경우다. ai.work를 받은 Codex는 현재 사용 가능한 Unity MCP와 생성 도구를 직접 사용할 수 있다. 산출물 경로·실제 도구 관측을 반환하고 관련 최종 판정에 연결한다. 도구를 사용했다는 AI 설명만으로 실행 증거가 자동 입증되는 것은 아니다.

외부 명령은 읽고 변경하는 자원 ID의 reads/writes 목록을 반드시 명시한다(없으면 빈 목록). 파일은 `file:절대경로` 형식으로 연결하며, 게임 상태처럼 파일이 아닌 자원에는 동일한 이름을 사용한다. 변경 단위 진입 시 자원 버전을 올려 이전 관측을 무효화한다. file.inspect는 크기/수정 시각의 변경도 확인한다. 외부 도구의 실제 변경 범위를 누락하면 그 누락을 자동 추론할 수 없다. command.run의 parameters.code_files에는 실제 알고리즘 스크립트를 지정하여 init 시 해시로 고정한다. 실행 파일/서비스의 내부 버전까지 자동으로 증명하지는 않는다.

ai.work도 parameters.scope와 reads/writes를 선언한다. 인계 시 쓰기 범위의 옛 관측을 무효화한다. 자신의 쓰기 범위 변경은 정상 결과로 받아들이며, 쓰기 범위 밖 읽기 입력이 바뀌면 적용 가능성을 다시 확인하도록 한다. 입력은 인계 시점의 스냅샷이며 중간 도구마다 다시 제출하지 않는다. reads/writes는 작업 계약이고 OS 접근 통제가 아니다. 중단 후에는 기존 ticket과 실제 파일/도구 상태를 확인하여 이어가며 미응답을 미실행으로 간주하지 않는다.

## 실행과 재개

프로젝트 루트에서 실행한다. 예시는 외부 서비스 없는 통계 계산이며 게임 수치 변경이 아니다.

```powershell
python -B Tools/WorkLoop/work_loop.py init LocalOnly/WorkLoop/v2-example/state.json Tools/WorkLoop/example.json
python -B Tools/WorkLoop/work_loop.py run LocalOnly/WorkLoop/v2-example/state.json
python -B Tools/WorkLoop/work_loop.py next LocalOnly/WorkLoop/v2-example/state.json
python -B Tools/WorkLoop/work_loop.py submit LocalOnly/WorkLoop/v2-example/state.json LocalOnly/WorkLoop/v2-example/answer.json
python -B Tools/WorkLoop/work_loop.py stop LocalOnly/WorkLoop/v2-example/state.json
python -B Tools/WorkLoop/work_loop.py resume LocalOnly/WorkLoop/v2-example/state.json
```

init는 계약을 고정하고 실행하지 않는다. run은 AI 입력/차단/완료 지점까지 일반 알고리즘을 연속 실행한다. next는 읽기 전용 조회다. submit은 다음 형식만 받고 이후 일반 계산도 이어 실행한다.

```json
{"ticket": "run이 반환한 현재 ticket", "output": {"candidate": 50}}
```

status, verdict, feedback, next, add/drop/reopen은 제어 입력으로 받지 않는다. 출력 schema에 없는 필드도 거절한다. 완료/수정/재시도는 그래프가 계산한다. 오류 중단 상태에 run을 반복해 부작용을 재실행하지 않는다. 새 계약이 필요하면 원인을 정리하고 기존 파일을 보존한 채 새 버전/상태로 시작한다. 같은 입력으로 새 상태만 만들어 반복하는 것은 복구가 아니다.

stop은 다음 단위 실행을 막는다. 이미 시작된 외부 프로세스나 원격 생성의 취소를 뜻하지 않는다. 비정상 종료하여 실행 결과가 불명확하면 uncertain_execution으로 멈춘다. 실제 결과를 확인하기 전 같은 외부 호출을 반복하지 않는다. .lock 잔존 시 실제 writer 종료를 확인한 후 그 lock 파일만 제거한다.

## 그래프 형식

요구에는 id/text/source/predicate를 둔다. 노드는 id/algorithm/phase/inputs/parameters/edges를 갖는다. 입력은 `{"literal": 값}` 또는 `{"ref": "노드ID.출력필드"}`다. 출력 필드가 없으면 노드 결과 전체를 참조한다. AI 단위는 question/output_schema도 필요하다.

작업 단위에서 `{"feedback_ref": "판정노드.출력필드", "default": null}`을 사용하면 이전 관찰을 스냅샷으로 받는다. 이는 복구 입력이며 현재 합격 증거가 아니다. validation과 요구 판정에서는 feedback_ref를 허용하지 않는다. 일반 ref는 현재 생산 결과와 데이터 의존성의 유효성을 검사한다.

Guard는 op/args로 구성하며 연산자는 eq/ne/lt/le/gt/ge, all/any/not/known이다. 숫자의 boolean 암묵 변환, NaN/무한대, 임의 eval을 허용하지 않는다. 간선의 to는 노드 ID, @complete, @blocked다. validation→work는 feedback:true로 명시한다. on_error 기본값은 차단이다. 조건에 맞지 않는 다음 단계를 임의로 선택하지 않는다.

생산 결과가 갱신되면 그 결과에 의존한 이전 결과는 유효하지 않다. 순환 제어 간선은 복구에 사용할 수 있지만 max_visits와 전체 max_steps를 지켜야 한다. 같은 단위·실제 입력·매개변수로 AI/명령을 다시 호출하는 것은 차단한다. 순수 계산은 같은 입력이면 재사용하고, 같은 관측·같은 분기로 돌아오는 루프도 중단한다. 피드백의 진전에 설명문·시간·임의 receipt ID만 쓰지 않는다.

파일 해시 동일성은 새 생성 여부의 판정식이 아니다. 같은 출력이 새 실행에서도 나올 수 있다. 새 생성 요구에는 실제 생성 어댑터의 요청/응답 기록을 판정하는 단위가 필요하다. file.inspect나 기존 GIF 변환을 생성 단위로 취급하지 않는다. 이 예시가 이미지 생성 파이프라인을 이미 연결했다는 뜻은 아니다.

## 최소 실험과 재개 조건

최종 검사 범위: 단위 계산/연속 실행, AI 출력 계약과 제어 입력 거절, 분기의 유일성/미정, 미충족 완료 차단, 복구 시 이전 증거 무효화, 동일 입력 반복 차단, 실제 프로세스 관측, 이전 상태 보존. 합격 테스트는 구현 끝에 묶고 단위 호출마다 반복하지 않는다. AI 실수 감소율·게임 완성도·사용량 절감률은 실제 작업 측정 없이는 완료로 보고하지 않는다.

v2 초기 실행 기록(2026-09-13): 최종 검증 그래프의 command.run 두 단위를 중간 AI 호출 없이 실행했다. 대표 계약 13개가 6.217초에 통과했고, 문서 검사도 통과했다(당시 AGENTS 18,127 bytes). 기록은 `LocalOnly/WorkLoop/v2-controller-validation/state.json`에 보존한다. 이후 ai.work 인계 추가의 검증은 별도로 구분한다. 이 시간은 검사 실행 시간이며 게임 제작 속도나 모델 절감률이 아니다. 실제 Unity 기능을 이 흐름으로 끝까지 수행한 검증은 아직 없다.

ai.work 추가 확인(2026-09-14): 최종 대표 계약 15개가 7.056초에 통과했고 문서 검사도 통과했다(AGENTS 18,341 bytes). 인계받은 파일을 호스트 작업자가 직접 수정하여 반환하는 흐름, 같은 ticket으로 중단/재개, 정상적인 자기 쓰기의 허용, 쓰기 범위 밖 입력 변경의 감지를 포함한다. 임시 파일을 사용하는 작업 인계 검증이며 실제 Unity 게임 기능 완주를 뜻하지 않는다.

## 구현 후 연구 대조

가장 가까운 연구는 [LLM-Modulo](https://arxiv.org/abs/2402.01817)와 그 [기술 평가](https://arxiv.org/html/2411.14484v1)다. LLM의 후보와 외부 판정기/피드백 제어를 결합한다. 올바른 출력 보장은 판정기가 정의된 조건을 정확하게 판정한다는 가정에 종속되며, 모든 문제에서 해를 찾는다는 보장은 별개다. 이 실행기는 그 역할 구분을 참고했지만 논문의 완전한 분야별 판정기를 구현한 것은 아니다.

[PAL](https://arxiv.org/abs/2211.10435)은 계산을 실행기에 맡기는 근거, [Least-to-Most](https://arxiv.org/abs/2205.10625)는 순차적인 작은 문제 분해의 근거, [Agentless](https://arxiv.org/html/2407.01489v2)는 정해진 코드 수정 절차도 경쟁력을 가질 수 있다는 근거다. [Lost in the Middle](https://arxiv.org/html/2307.03172v3)와 [τ-bench](https://arxiv.org/html/2406.12045v1)는 각각 문맥 활용과 복합 도구 작업의 신뢰성 한계를 보여 준다. 사용자의 설계 주장은 부족한 신뢰성 관리 기반을 절차로 제공하자는 것이다. 이를 '자아의 증가를 증명하라'는 주장으로 바꾸지 않으며, 기반이 저절로 충분해진다고 가정하지 않는다. 구체적 개선율은 실제 작업에서 측정한다.

원문별 결과·가정·비용·현재 구현과의 대응은 기존 [파이프라인 연구 §8](<C:/Users/JG/.codex/visualizations/2026/09/10/01a08c0e-bbf2-7d10-b1e8-607c2c27f6d3/pipeline-session-control.md>)에 통합했다. 해당 실험 수치를 현재 Codex/Unity의 성능으로 옮겨 쓰지 않는다.
