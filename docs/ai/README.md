# AI 지침 구조

이 디렉터리는 AI가 프로젝트 규칙을 한 번에 과도하게 읽지 않고, 현재 작업에 필요한 계약만 선택해서 읽도록 만든 안내서다. 실행 규칙의 진입점은 저장소 루트의 `AGENTS.md`이며, 이 문서는 구조를 설명하는 사람용 자료다.

## 왜 분리했는가

2026-08-26 감사에서 기존 `AGENTS.md`는 55,253바이트였다. Codex의 프로젝트 지침 기본 합산 한도는 32KiB이므로 실제 세션에서 약 249행 이후가 잘렸고, 뒤쪽의 버그 근본 원인 규칙, 반복 검증 제한, Git, Unity MCP와 Computer Use 규칙이 자동 지침에 포함되지 않았다.

해결책은 한도를 늘리는 것이 아니라 다음 원칙으로 항상 읽는 내용을 줄이는 것이다.

- 같은 규칙은 한 곳에 한 번만 기록한다.
- 현재 상태, 안정된 계약, 작업 절차와 과거 이력을 분리한다.
- 긴 문서는 전체가 아니라 관련 제목과 범위만 읽는다.
- 기계가 판정할 수 있는 조건은 장기적으로 테스트나 Editor Validator로 옮긴다.

## 읽기 계층

```text
AGENTS.md
  → docs/ai/CURRENT_STATE.md
    → 씬·한 판 순서 작업이면 docs/ai/GAME_FLOW.md
    → 관련 게임·서브시스템 계약
      → docs/ai/UNITY_ENGINEERING_PLAYBOOK.md의 관련 절
        → 필요할 때만 unity_development_progress.md의 증거 이력
```

| 계층 | 역할 | 읽는 시점 |
|---|---|---|
| `AGENTS.md` | 짧은 핵심 계약, 금지선, 문서 라우터 | 항상 자동 로드 |
| `CURRENT_STATE.md` | 현재 구현·검증·재개방 조건의 단일 인덱스 | 구현, 버그, 검증, 다음 기능 선택 |
| `GAME_FLOW.md` | 게임 실행부터 한 판 정산까지 실제 씬·함수·분기 순서 | 시작, 메뉴, 씬 전환, 원정, 정산 순서 변경 |
| 게임·기술 계약 | 사용자 확정 규칙과 안정된 불변조건 | 현재 작업과 관련될 때만 |
| `UNITY_ENGINEERING_PLAYBOOK.md` | Unity 편집, 구조 변경, 검증 절차 | 필요한 절만 |
| `unity_development_progress.md` | 상세 증거와 과거 이력 | 원인이나 증거를 추적할 때만 |

하위 `AGENTS.md`는 대상 파일 위치가 아니라 Codex를 시작한 현재 작업 디렉터리까지의 경로에서만 자동 발견된다. 현재 작업 디렉터리가 저장소 루트이므로 `Assets/Scripts` 아래에 지침을 나누는 방식은 사용하지 않는다.

## 문서별 권위

- 현재 구현 여부: 직접 확인한 Unity·코드 사실 → `CURRENT_STATE.md` → 최신 진행 이력
- 실제 시작·메뉴·씬 전환·한 판 호출 순서: `GAME_FLOW.md`
- 장르와 플레이 판단: `extraction_survival_gameplay_contract.md`
- 게임 요소·콘텐츠·UI 기획: `game_design_document.md`
- Unity 선행조건과 Stage 의존성: `extraction_survival_game_design_dev_plan.md`
- 상세 검증·변경 이력: `unity_development_progress.md`
- Unity 작업 방법: `UNITY_ENGINEERING_PLAYBOOK.md`

과거 이력이나 Stage 문구는 현재 작업 지시가 아니다. `[제안]`과 `[미정]`도 구현 권한이 아니다.

## 다른 게임 프로젝트와 비교해 채택한 방식

| 프로젝트 | 확인한 운영 방식 | 이 프로젝트에 채택한 점 |
|---|---|---|
| Space Station 14 | 짧은 루트 안내에서 코드 규칙, PR·테스트, 코드베이스 구조, 아트·라이선스 문서로 연결 | 루트는 안내판으로 두고 세부 계약을 조건부 문서로 분리 |
| OpenRA | 루트 기여 문서는 핵심 링크만 두고 코딩 표준·개발 절차와 자동 검사를 분리 | 산문 규칙의 반복을 줄이고 검증 가능한 것은 명령·테스트로 이동 |
| osu! | 기능·큰 시각 변경은 사전 합의하고 테스트 비용에 비례해 검증 | 미정 기획의 임의 확정 금지와 위험 비례 검증 |
| Godot | 한 변경에 하나의 자기완결 목적, 관련 없는 변경 금지, 상세 기여 문서 분리 | 작업 범위를 한 기능으로 제한하고 history와 절차를 분리 |

이 프로젝트는 여기에 사용자 정정 우선, 동일 Player 인스턴스 보존, 완료 기능 재구현 금지, 단일 권위 소유자와 원인 우선 수정을 추가한다.

## 크기와 유지 규칙

- 루트 `AGENTS.md` 목표: 10~14KiB, 절대 상한 24KiB
- `CURRENT_STATE.md` 목표: 12KiB 이하
- 새 규칙을 추가하기 전에 기존 규칙을 고치거나 교체할 수 있는지 먼저 확인한다.
- 현재 사실은 `CURRENT_STATE.md` 한 곳만 갱신하며 다른 지침에 복사하지 않는다.
- 상세 절차는 playbook에 두고 루트에는 조건과 링크만 둔다.
- 진행 이력은 누적할 수 있지만 기본 읽기 대상이 아니다.
- 지침을 바꾼 뒤 `powershell -NoProfile -ExecutionPolicy Bypass -File docs/ai/validate_ai_docs.ps1`로 크기, 필수 경로, 모든 기능·공백 ID의 행 형식·계약 경로와 공백 오류를 확인한다.

## 참고한 1차 자료

- OpenAI, [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- OpenAI, [Model guidance — Favor leaner prompts](https://developers.openai.com/api/docs/guides/latest-model)
- Space Station 14, [CONTRIBUTING.md](https://github.com/space-wizards/space-station-14/blob/master/CONTRIBUTING.md)
- OpenRA, [CONTRIBUTING.md](https://github.com/OpenRA/OpenRA/blob/bleed/CONTRIBUTING.md)
- osu!, [CONTRIBUTING.md](https://github.com/ppy/osu/blob/master/CONTRIBUTING.md)
- Godot, [CONTRIBUTING.md](https://github.com/godotengine/godot/blob/master/CONTRIBUTING.md)
