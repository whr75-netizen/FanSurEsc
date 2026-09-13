# WorkLoop — AI 작업·피드백 제어기

AI가 작성한 작업 목록을 프로그램이 읽고, 현재 실행 가능한 작업과 다음 지시를 같은 AI에게 반환한다. Python 3.10 이상 표준 라이브러리만 사용한다. 별도 모델 호출·API 키·서버·MCP 설치는 없다. Codex의 기존 명령 실행 도구로 호출한다.

## 작동 방식

`사용자 요구 → AI가 spec 작성 → init → 다음 작업 선택/start → 실제 도구 실행 → 결과·피드백 submit → 필요한 분기 추가/제거 → 마지막 검증 → 최종 보고`

고정된 것은 순서/상태/완료 계약이다. 작업 그래프는 관찰에 따라 바뀐다. 한 작업은 여러 파일 편집과 도구 호출을 묶은 의미 있는 단위다. 호출마다 계획 문서를 읽거나 검증을 반복하지 않는다. 피드백은 도구가 실제 반환한 출력/오류와 그것이 다음 결정에 주는 영향만 짧게 기록한다. 내부 사고 과정이나 AI 자기 점수는 저장하지 않는다.

프로그램은 외부 도구를 실행하거나 종료된 AI를 다시 깨우지 않는다. 활성 AI가 반환된 지시를 따라 기존 도구를 실행한다. MCP 서버로 감싸더라도 이 실행 주체는 필요하다. AI가 이 경로를 건너뛰거나 상태/증거를 거짓 작성하는 것까지 막는 보안 경계는 아니다.

## 실행

프로젝트 루트에서 실행한다. 상태 파일은 작업마다 고유한 경로를 사용한다. 아래 예시는 실행 명령을 담고 있지 않으며 이미지/영상 생성을 자동 시작하지 않는다.

```powershell
python Tools/WorkLoop/work_loop.py init LocalOnly/WorkLoop/example/state.json Tools/WorkLoop/example.json
python Tools/WorkLoop/work_loop.py start LocalOnly/WorkLoop/example/state.json generate
# AI가 여기서 승인된 실제 도구를 실행하고 report.json을 작성한다.
python Tools/WorkLoop/work_loop.py submit LocalOnly/WorkLoop/example/state.json LocalOnly/WorkLoop/example/report.json
python Tools/WorkLoop/work_loop.py next LocalOnly/WorkLoop/example/state.json
python Tools/WorkLoop/work_loop.py stop LocalOnly/WorkLoop/example/state.json
python Tools/WorkLoop/work_loop.py resume LocalOnly/WorkLoop/example/state.json
```

`start`, `submit`, `resume`도 다음 지시를 반환하므로 직후 `next`를 중복 호출하지 않는다. `next`는 재개/상태 조회용이다. `stop`은 다음 작업 시작을 막으며 외부 생성 요청이나 실행 중 프로세스를 취소하지 않는다. 중단 후 `running`은 실제 파일/요청 ID를 확인하여 이어가고 무조건 재실행하지 않는다.

`spec.json`은 `goal`, `requirements`, `tasks`, 선택적인 `max_starts`로 구성한다. 요구는 사용자 요청에서 도출하며 목표를 쉬운 대체 문제로 바꾸지 않는다. 작업은 각각 하나의 요구 ID, 해결할 질문, 기대 기여, `work`/`validation`, 의존 작업 ID를 갖는다. 여러 요구에 대한 마지막 판정은 요구별로 짧게 나누되 같은 실제 테스트 로그를 참조하여 중복 실행하지 않는다. 예시는 `example.json`을 참고한다.

## 결과와 재계획

실제 도구 실행 후 다음 형식의 JSON을 작성하여 `submit`한다. 아래 문자열은 형식 설명이며 실행 증거가 아니다. 실제 도구 결과/파일/요청 ID로 바꿔야 한다.

```json
{
  "task": "generate",
  "status": "done",
  "observation": "이번 생성 요청에서 완료 응답과 영상 파일을 받았다.",
  "feedback": "영상 입력이 확보되어 기존 처리 단계를 실행할 수 있다.",
  "evidence": [{
    "id": "E_video", "kind": "generated",
    "ref": "실제 출력 파일의 절대 경로",
    "receipt": "실제 생성 응답/요청 ID와 이를 확인할 로그 경로"
  }]
}
```

- `status`: 실제 작업 단위 결과 `done` 또는 실제 차단 `blocked`. `done`은 전체 요청 완료를 뜻하지 않는다.
- `evidence`: `imported` 기존 입력, `generated` 이번 생성, `transformed` 변환, `execution` 실제 실행 결과, `observation` 관찰. 변환은 `parents: ["E_video"]`처럼 원본을 연결한다. 생성은 실제 요청/도구 결과를 찾을 `receipt`가 필요하다. 프로그램은 참조 문자열의 실재성/진실성을 자동 조회하지 않는다.
- `uses`: 이 결과가 사용하는 증거 ID 목록. 생략하면 이번에 추가한 증거를 사용한다. 기존 증거를 재사용하면 같은 검사를 다시 실행할 필요가 없다.
- `validation` 결과에는 `verdict: "pass" | "fail" | "unknown"`을 기록한다. 해당 요구의 증거 종류가 `generated`이면 사용한 결과의 계보에 이번 상태에 기록된 생성 증거가 있어야 `pass`를 받는다. `imported → transformed → transformed` 계보는 충족하지 못한다.
- `feedback`: 지금 얻은 근거로 계속/수정/차단을 결정한 짧은 설명. 모든 작업 뒤 사용자에게 확인을 묻는 단계가 아니다.

같은 제출에 `add`(새 작업 목록), `drop`/`reopen`(`id`, `reason` 목록)을 넣어 즉시 분기한다. 결과 제출과 재계획을 별도 호출로 나눌 필요가 없다. 이미 실행을 끝낸 뒤 새 피드백이 들어오면 `task` 없이 재계획만 제출할 수도 있다.

```json
{
  "feedback": "최종 재생에서 배경 제거 오류가 확인됐다. 처리 단계는 완료했으므로 새 생성 없이 해당 결과만 수리한다.",
  "add": [{
    "id": "fix_background", "requirement": "R2", "phase": "work",
    "question": "실제 오류를 낸 배경 제거 입력 조건을 어떻게 충족하는가?",
    "contribution": "확인된 입력 오류를 고쳐 같은 영상으로 처리한다.",
    "depends_on": ["process"]
  }]
}
```

기존 작업의 의존성을 바꿔야 하면 그 작업을 이유와 함께 `drop`하고 올바른 의존성의 새 ID로 추가한다. 삭제된 작업에 의존하는 후속 작업도 명시적으로 재계획한다. 필수 요구 자체는 삭제되지 않는다. 단순히 모든 작업을 삭제해 완료로 바꿀 수 없다.

## 프로그램이 관리하는 경계

- 실행 가능한 의존 순서, 순환/중복 ID 차단, 단일 실행 작업.
- 실행 작업의 실제 결과·피드백 참조 없이 완료 처리 금지.
- 미완료/차단 `work`가 있으면 합격 `validation` 시작 금지. 실패한 마지막 판정은 수리 분기로 되돌린다.
- 관련 작업을 추가/재개하면 해당 요구의 기존 판정과 의존 후속 작업만 다시 연다. 다른 요구의 증거는 유지한다. 다시 실행한 작업의 이전 시도 증거를 현재 증거로 자동 승인하지 않는다.
- 모든 요구에 마지막 판정과 맞는 증거 계보가 있어야 `protocol_complete`. AI의 점수/동의만으로 완료되지 않는다.
- 기본 30회 작업 시작 한도(`max_starts`). 한도에 도달하면 자동 반복을 멈추고 남은 요구/반복 원인을 보고한다. 비용이나 토큰을 직접 측정하는 한도가 아니다.
- 상태 파일 하나가 원본이다. 제출 JSON은 일회성 입력이며 별도 상태표가 아니다. 한 프로세스만 쓰며 저장은 임시 파일과 원자적 교체를 사용한다. 비정상 종료로 `.lock`이 남았다면 실제 writer가 종료되었는지 확인한 후 그 파일만 제거한다. 동시 분산 실행/정확히 한 번의 원격 실행은 제공하지 않는다.

## 선택 근거와 한계

사용자의 제안은 실제 도구에서 쓰는 방식이다. [Shrimp의 planTask](https://github.com/cjo4m06/mcp-shrimp-task-manager/blob/main/src/tools/task/planTask.ts)는 다음 지시를 호스트 AI에 반환한다. 그러나 [verifyTask](https://github.com/cjo4m06/mcp-shrimp-task-manager/blob/main/src/tools/task/verifyTask.ts)는 호출자가 넣은 점수로 상태를 바꾸므로 실제 결과 보증과 다르다. [Task Orchestrator](https://github.com/jpicklyk/task-orchestrator/blob/main/current/docs/workflow-guide.md)는 상태/의존성 관리를 제공하지만 서버가 보는 것은 상태 전이이며 도구 실행 자체는 아니라는 한계를 명시한다.

[OpenAI의 개발 워크플로 안내](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex)는 AGENTS.md와 필요에 따른 계획 파일을 사용한다. 지침 방식은 도입이 쉽고, 프로그램 방식은 검사 가능한 순서/누락 조건을 일관되게 관리한다. 여기서는 기존 도구를 이식하지 않고 필요한 상태·지시 반환 부분만 독립 구현했다. 대형 작업 관리자 설치, 매 단계 별도 평가 모델, 전체 맥락 재전송이 현재 필요하지 않기 때문이다.

검증 가능한 구조와 의미 판단을 구분한다. 잘못된 목표, 허위 생성 라벨/receipt, 쓸모없는 작업의 그럴듯한 기여 설명까지 이 프로그램이 알아낼 수는 없다. 원본 GIF 왕복이 구조상 차단되는 것은 **출처를 정직하게 입력한 경우**다. 실제 결과와 사용자 요구가 맞는지는 마지막 필요한 관찰로 확인한다. 새 증거를 얻지 않은 동일 반복, 전체 검증 반복, AI 자기 점수는 피드백이 아니다.

## 확인한 범위

2026-09-13: `python -B Tools/WorkLoop/test_work_loop.py`의 대표 계약 8개 통과. 정상 진행/중단/재개, 검증 단계 순서, GIF 왕복의 생성 증거 오인 차단, 순환/삭제 분기의 미충족 요구 유지, 피드백 수정 분기, 구형 원본 계보 차단, 증거 누락 차단, 반복 한도를 확인했다. 테스트는 임시 상태와 명시된 합성 증거로 실행하며 실제 미디어/Unity 공급자를 호출하지 않는다. `validate_ai_docs.ps1`도 통과했다.

이번 제어기 구현의 마지막 작업 기록/검증 제출에도 CLI를 실행했다(`LocalOnly/WorkLoop/controller-implementation/state.json`). 이 상태 파일은 구현 종료 시점에 도입했으며, 이전 구현 전체가 이 제어기를 거쳤다는 뜻은 아니다. 실제 Unity 작업 품질, AI의 지침 준수율, 모델 사용량 절감률, 외부 생성의 정확히 한 번 실행은 검증하지 않았다.
