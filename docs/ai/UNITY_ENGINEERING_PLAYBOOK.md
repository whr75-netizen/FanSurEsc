# Unity 엔지니어링 플레이북

이 문서는 Unity 코드·씬·프리팹·런타임 상태를 실제로 변경하거나 관련 버그를 조사할 때만 사용한다. 매 작업마다 전체를 읽지 말고 `rg`로 관련 제목을 찾은 뒤 필요한 절만 읽는다. 핵심 승인 경계와 금지선은 루트 `AGENTS.md`가 우선한다.

## 1. 작업 유형별 절차

### 1.1 기능 구현

1. `CURRENT_STATE.md`에서 기존 기능과 재개방 조건을 확인한다.
2. 관련 코드·씬·프리팹과 진행 이력의 근거 절만 찾는다.
3. 현재 권위 소유자, 객체 수명, 입력 소유자와 직렬화 참조를 확인한다.
4. 사용자에게 요청 결과·메커니즘·보존·제외·검증의 5항목 작업 계약을 알린다.
5. 기존 공개 진입점과 책임 경계를 확장하는 최소 변경을 구현한다.
6. 컴파일·직렬화 참조와 변경 영향에 맞는 사용자 흐름을 검증한다.
7. `CURRENT_STATE.md`의 관련 행과 필요한 상세 증거를 갱신한다.

### 1.2 버그 수정

1. 원래 증상을 대표 절차로 한 번 재현하거나 재현 불가 이유를 기록한다.
2. 최초 오류, 직전 변경, 입력, 권위 원본, 수명주기와 직렬화 참조를 확인한다.
3. 원인 후보를 한 번에 하나씩 검증한다.
4. 깨진 원본 또는 계약에 필요한 가장 작은 수정만 적용한다.
5. 원래 재현 절차와 직접 영향 회귀를 각각 한 번 확인한다.
6. 간헐 오류라 반복이 필요하면 시작 전에 횟수와 판단 기준을 정한다.

UI·프리팹·캐시·생성 결과는 원인을 고친 뒤에만 재생성한다. 재생성, 복사본 교체, 강제 재적용, 광범위한 reimport, Console 삭제나 fallback 값으로 증상만 가리는 것은 수정이 아니다.

### 1.3 진단·검토·설계

- 진단은 원인과 증거까지만 제공한다. 수정 요청이 없으면 파일과 Unity 상태를 바꾸지 않는다.
- 검토는 현재 사실, 위험, 선택지와 권장을 분리한다.
- 설계 제안은 `[제안]`, 사용자 결정 전 항목은 `[미정]`으로 남긴다.
- 더 나은 일반론이 있어도 사용자 확정 메커니즘을 조용히 교체하지 않는다.

## 2. 객체 수명과 씬

- `LoadSceneMode.Single`은 scene object를 언로드한다. 동일 인스턴스가 필요하면 명시적인 영속 루트가 소유해야 한다.
- `DontDestroyOnLoad`는 root GameObject에만 적용하고 필수 자식 참조를 함께 보존한다.
- 영속 루트가 프로젝트 에셋 외의 source scene object를 참조하지 않는지 확인한다.
- 완성본 Player·Camera·UI를 각 씬에 복제한 뒤 늦게 삭제하지 않는다. 작은 Bootstrap이 없을 때만 단일 프리팹을 만든다.
- 전환 전 drag, 열린 UI, EventSystem 선택, scene-local 상호작용과 캐시를 정리하고 도착·배치 성공 뒤 입력을 연다.
- `PersistentGameplayShell`은 객체 수명의 소유자이지 모든 게임 규칙의 만능 Manager가 아니다.
- `GameManager`와 persistent shell은 현재 별도 책임이다. 관련 요청 없이 합치지 않는다.

### 2.1 `SHELL-01` 변경 전 확인

권위 계약은 `AGENTS.md` §4와 `CURRENT_STATE.md`의 `SHELL-01`·`TRAVEL-01`·`TRANSITION-01`이다. 이 playbook에서 별도 Player 계약을 만들지 않는다. 해당 경계를 바꿀 때는 진행 이력의 연결된 상세 근거와 현재 prefab/scene 참조 그래프를 확인한 뒤 8.5의 검증을 적용한다.

## 3. 씬·프리팹·에셋

- 여러 씬의 공통 구성은 prefab을 단일 원본으로 사용한다.
- prefab source 변경과 instance override를 구분한다.
- Unity가 사용 가능하면 `.unity`, `.prefab`, `.asset` YAML을 직접 편집하지 않는다.
- 씬 저장 전 Missing Script/Reference, null 직렬화 필드, 중복 Camera/AudioListener/EventSystem, 잘못된 tag/layer와 의도하지 않은 override를 확인한다.
- Unity 에셋과 `.meta`는 한 쌍으로 보존하고 GUID를 임의로 생성·교체하지 않는다.
- 외부 에셋은 출처, 라이선스, 원본 URL과 수정 여부를 기록한다. 사용자 승인 없이 새 패키지나 외부 에셋을 들이지 않는다.

## 4. 정의 데이터·런타임 상태·세이브

- ScriptableObject는 공유 definition과 설정에 사용한다.
- mutable runtime instance와 immutable definition을 분리한다.
- Save DTO와 파일은 프로세스 사이 값을 운반하는 표현이지 live 권위 상태가 아니다.
- 배포 세이브를 ScriptableObject asset 변경으로 구현하지 않는다.
- 로드는 전체 DTO를 검증한 뒤 기존 런타임 소유자에 원자적으로 적용한다.
- `ItemDefinition` 숫자 ID는 아이템 종류 ID다. 영구 instance ID나 save record ID로 추정하지 않는다.
- UI, tooltip, 가격 배지, 검색 인덱스와 캐시는 원본에서 재구성 가능한 파생 표현이다.

## 5. 권위 소유자와 컨테이너

변하는 각 런타임 상태에는 한 시점에 쓰기 권위 소유자 하나만 둔다. 새 Manager, Session, 컨테이너나 캐시를 만들기 전에 관련 항목만 짧게 기록한다.

| 항목 | 확인 내용 |
|---|---|
| 권위 소유자 | 실제 원본을 쓰는 객체 하나 |
| 수명 | Application, Play Session, Scene, Raid, Entity, Container |
| 생성·정리 | 누가 언제 만들고 해제하는지 |
| 변경 진입점 | 값을 바꾸는 메서드와 호출자 |
| 포함 관계 | 소유 자식과 단순 참조·관찰 대상 |
| 이전 규칙 | 사전 검증, 이동, 실패 rollback |
| 파생 표현 | UI·인덱스·캐시 갱신/무효화 |
| 저장 경계 | DTO 변환 주체와 저장 여부 |
| 업데이트 | Update, Tick, Interval, Event 중 실제 주체 |

- 런타임 객체는 동시에 둘 이상의 논리 컨테이너에 소유되지 않는다.
- 컨테이너 내부 컬렉션과 불변조건은 컨테이너 API만 변경한다.
- 이전은 사전 검증 → 기존 소유자 제거 → 새 소유자 적용 → 역참조·인덱스 갱신의 한 작업 경계다.
- 실패하면 원본 위치와 값이 그대로 남아야 하며 유실·복제·부분 이동이 없어야 한다.
- 둘 이상의 소유자를 바꾸는 coordinator는 순서·검증·rollback만 조정하며 별도 원본 복사본을 소유하지 않는다.
- 직접 owner 경로가 있으면 `Find*`, 임의 Singleton, service locator나 전역 이벤트로 다시 찾지 않는다.
- 상태 변경은 `입력 소유자 → 기능 진입점 → 권위 소유자 → 상태 변경 → 완료 통지·표시 갱신`으로 역추적할 수 있어야 한다.
- 이벤트는 주로 완료 통지에 사용한다. 여러 listener가 같은 변경을 경쟁해서 결정하지 않는다.
- 실제 책임 없이 호출만 전달하는 Manager/Service나 형식적인 인터페이스 계층을 만들지 않는다.

## 6. Update·Tick·인덱스·캐시

- 매 프레임 필요한 입력·카메라·표현과 낮은 빈도의 게임 규칙을 구분한다.
- 같은 종류의 객체가 많아지면 scope 소유자의 등록 목록과 Tick을 우선 검토하되, 소수 프로토타입에 scheduler를 먼저 만들지 않는다.
- Tick 목록 순회 중 등록·해제가 가능하면 pending add/remove나 안전한 작업 경계를 둔다.
- 반복 공간 조회가 병목이면 map/scene 범위의 파생 인덱스를 사용하고 생성·이동·상태 변경·파괴 경계에서 갱신한다.
- 캐시는 원본, key, dirty 조건, 무효화 호출자와 전체 재구축 경로가 모두 있어야 한다.
- hot path에서 반복 `Find*`, `GetComponent`, LINQ 할당, 새 컬렉션과 불필요한 Physics 전체 탐색을 피한다.
- 성능 구조 변경은 대표 규모의 Profiler 전후 증거가 있을 때만 완료로 판정한다.

## 7. Unity Editor 작업 경로

- 씬 오브젝트, prefab, Material과 serialized reference는 Unity MCP/Editor API의 단일 writer가 변경한다.
- 다른 에이전트는 같은 시간에 Play Mode, AssetDatabase, scene/prefab 저장을 실행하지 않는다.
- Unity MCP가 노출되지 않으면 연결·컴파일·domain reload·승인 상태와 다른 MCP 담당을 먼저 확인한다.
- Computer Use는 사용자가 현재 턴에 명시적으로 허용한 경우에만 최소 동작에 사용하고, 끝나면 즉시 제어를 종료해 보고한다.
- C#·문서 파일은 `apply_patch`로 변경한다.

### 7.1 RunCommand 규칙

- 클래스 이름은 `CommandScript`, 형식은 `internal class CommandScript : IRunCommand`으로 한다.
- 생성은 `result.RegisterObjectCreation`, 수정 전에는 `result.RegisterObjectModification`, 삭제는 `result.DestroyObject`를 사용한다.
- 로그는 `result.Log`, 경고는 `result.LogWarning`, 오류는 `result.LogError`를 사용한다.
- top-level statement를 사용하지 않는다.
- Undo/Redo와 scene dirty/save 범위를 명확히 한다.
- 성공 메시지만 믿지 않고 Console, 오브젝트 수, 참조와 scene dirty를 별도 확인한다.

## 8. 위험 비례 검증

### 8.1 공통

- 변경 전 Console과 git 기준선을 잡고 기존 오류와 신규 delta를 구분한다.
- import/compile 뒤 새 Error, Exception, Assert와 변경이 만든 Warning이 없어야 한다.
- 새 Missing Script/Reference, null serialized field와 의도하지 않은 dirty가 없어야 한다.
- 현재 변경과 직접 연결된 정상·취소·실패 경계를 확인한다.
- 먼저 변경된 권위·입력·수명·직렬화 경계와 바로 맞물린 기능만 `인접 검증` 대상으로 고른다.
- 전체 한 바퀴는 셸·씬·저장·정산처럼 여러 단계의 실제 순서를 직접 바꿨거나 릴리스 gate일 때만 한다. 단일 기능 변경의 기본 검증으로 사용하지 않는다.
- 같은 대표 흐름은 기본 1회다. 반복은 수명 누적이나 간헐 오류처럼 이유가 있을 때 횟수를 먼저 정한다.
- 서로 다른 seed, schema/migration, 손상 분기, grid, 해상도나 플랫폼은 최소 case matrix의 서로 다른 case로 각각 1회 확인할 수 있다.
- 검증 뒤 Play Mode를 종료하고 원래 활성 씬과 의도한 저장 상태를 확인한다.

### 8.2 입력·상호작용·UI

- 입력·UI를 바꿨으면 가능할 때 실제 키와 UI 순서로 정상, 취소, 범위 밖, 빠른 중복 입력을 확인한다.
- 공개 메서드 호출로만 확인했다면 `[Play Mode 호출 확인]`으로 기록하며 실제 물리 입력 확인으로 승격하지 않는다.
- drag 중 닫기, 거리 이탈, scene transition과 UI close가 같은 데이터 안전 경로로 수렴하는지 확인한다.
- 기존 관련 기능이 현재 diff에 닿지 않았다면 과거 성공 증거를 재사용한다.

### 8.3 공격·피해·사망

- 입력 차단, 빈 활성 무기와 열린 인벤토리에서는 공격·효과음이 나가지 않아야 한다.
- 단발 edge와 자동 hold가 같은 RPM cadence를 통과하는지 확인한다.
- 실제 Raycast는 Camera가 아니라 Player 발사 원점에서 마우스 XZ 조준 방향으로 나가야 한다.
- 모든 피해는 공통 `IDamageable.ApplyDamage`를 통과하고 `EnemyStats`의 `>0 → 0`에서만 사망을 한 번 통지한다.
- 사망 뒤 Brain·공격·Agent·피격 Collider는 비활성이고 root·렌더·시체 전리품은 유지된다.
- 유효한 빗나감은 발사음만, 실제 적용 피해는 구분되는 적중음을 낸다.

### 8.4 소유권·컨테이너·캐시

- 쓰기 권위 소유자는 하나이며 우회 직접 쓰기가 없어야 한다.
- 이전 성공 뒤 기존 소유자에는 0개, 새 소유자에는 1개이며 역참조·인덱스가 일치해야 한다.
- 실패 뒤 원본과 잔액이 그대로이고 유실·복제·부분 이동이 없어야 한다.
- 등록·해제 수가 맞고 제거된 객체가 계속 Tick되지 않아야 한다.
- 원본 변경 뒤 UI·캐시가 갱신되고 전체 재구축도 같은 결과를 만들어야 한다.

### 8.5 Player 셸·씬 전환

이 경계를 직접 변경했을 때만 다음을 확인한다.

- `GameMap1 → GameMapTest → GameMap1` 대표 왕복 1회와 `GameMapTest` 직접 시작
- Shell, Player, Camera, `InventoryUIManager`, EventSystem의 전후 `GetInstanceID()` 동일
- persistent shell 1개, destination runtime 복사본 0개
- SpawnPoint 배치와 Rigidbody 속도 초기화
- 두 씬의 이동·상호작용·인벤토리와 현재 아이템 상태 보존
- 중복 AudioListener/EventSystem, destroyed reference와 기본 아이템 재생성 없음

### 8.6 테스트와 빌드

- 순수 데이터·규칙은 가능한 EditMode 테스트, 프레임·씬·입력·물리는 PlayMode 또는 실제 Play Mode로 검증한다.
- Player build는 변경 위험이나 사용자 요청에 필요할 때 수행한다. 실행하지 않았으면 빌드 미검증이라고 명시한다.
- 실행하지 않은 검증은 통과했다고 쓰지 않는다. 구현됨, 검증됨, 미검증과 차단 사유를 구분한다.

## 9. 파일·Git 마무리

- `Library/`, `Temp/`, `obj/`, build 출력과 registry `PackageCache`를 소스처럼 수정·커밋하지 않는다.
- 작업 전후 `git status`와 diff로 사용자 변경을 구분한다.
- 무관한 dirty 파일을 되돌리거나 포맷하지 않는다.
- 검증 완료 뒤 이번 작업 파일과 필요한 `.meta`만 명시적으로 stage한다. `git add .`와 `git add -A`를 쓰지 않는다.
- staged diff와 파일 목록을 확인한 뒤 기능 단위 로컬 커밋 하나를 만든다.
- 기존 변경과 안전하게 분리할 수 없는 파일은 자동 커밋하지 않고 이유를 보고한다.
- push, 원격 branch, PR과 Unity Version Control은 사용자 별도 요청 없이는 수행하지 않는다.

## 10. 증거 표기

- `[사용자 확인]`: 사용자가 실제 결과를 확인했다.
- `[Player 확인]`: 빌드된 프로세스에서 확인했다.
- `[Play Mode 확인]`: 실제 Play Mode 프레임과 사용자 흐름으로 확인했다.
- `[Play Mode 호출 확인]`: 런타임 진입점으로 확인했지만 실제 입력은 우회했다.
- `[코드/씬 확인]`: 코드, scene, prefab과 직렬화 상태를 확인했다.
- `[코드 확인]`: 실행하지 않고 경로와 불변조건만 확인했다.

증거 등급을 임의로 올리지 않는다. 완료 기능에 관련 변경이나 새 회귀가 없다면 기존 가장 강한 증거를 재사용한다.
