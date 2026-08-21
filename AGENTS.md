# Fantasy Survival Escape Game — AI 개발 계약

이 파일은 이 저장소에서 작업하는 모든 AI 에이전트가 따라야 하는 프로젝트 최상위 지침이다.
단, 상위 system/developer 지침과 안전·권한·샌드박스 정책을 항상 먼저 따른다.
`MUST`, `MUST NOT`, `금지`는 권고가 아니라 작업 승인 조건이다.

## 0. 기본 태도와 언어

- 사용자가 한국어로 대화하면 모든 진행 보고와 최종 답변은 항상 존댓말로 작성한다. 사용자가 명시적으로 요청하지 않는 한 반말을 사용하지 않는다.
- 상위 지침과 안전·권한 범위 안에서 최신 사용자 요청을 문자 그대로 우선한다. AI가 세운 목표, 이전 계획, 일반적인 모범 사례, 구현 편의성은 최신 사용자 요청을 덮어쓸 수 없다.
- 사용자의 정정은 즉시 새 계약이 된다. 이전 해석을 방어하거나 조용히 유지하지 않는다.
- 사실, 사용자 확정, 제안, 미정을 구분한다. 추정이나 권장을 확정된 기획처럼 쓰지 않는다.
- 결과를 먼저 설명하되, 실행하지 않은 검증이나 확인하지 않은 상태를 완료로 표현하지 않는다.

## 1. 지시 우선순위와 재동기화

프로젝트 내부 지시끼리 충돌하면 다음 순서로 따른다. 이 순서는 상위 system/developer 지침과 안전·권한 정책 아래에서 적용된다.

1. 사용자의 가장 최근 정정과 명시적 요청
2. 현재 대화에서 사용자가 이미 확정한 결정
3. `unity_development_progress.md`의 최신 `[사용자 요구]` 기록
4. `extraction_survival_game_design_dev_plan.md`의 `[확정]` 항목
5. Unity Editor, 코드, 씬, 프리팹에서 직접 확인한 현재 사실
6. `unity_development_progress.md`의 최신 `[Play Mode 확인]`/`[Play Mode 호출 확인]`/`[코드/씬 확인]`/`[코드 확인]` 기록
7. 설계 문서의 `[현재]` 기록
8. 설계 문서나 AI의 `[권장]`, `[제안]`

다음 상황에서는 편집을 계속하기 전에 반드시 작업 기준을 다시 확인한다.

- 새 기능 구현 또는 버그 수정 턴을 시작할 때
- 대화가 요약·압축되었거나 작업 시간이 길어졌을 때
- 사용자가 결과나 해석을 정정했을 때
- 둘 이상의 씬 또는 서브시스템을 함께 변경할 때
- 커밋, 대규모 에셋 변경, 구조 변경 직전

재확인할 내용:

- 최신 사용자 메시지와 요구한 결과
- `unity_development_progress.md`의 관련 현재 동작, 알려진 차이와 미검증 항목
- 설계 문서의 현재 Stage 및 관련 `[확정]`/`[미정]`
- `git status`와 관련 diff
- Unity의 활성 씬, Play Mode/컴파일/dirty 상태, Console 기준선
- 대상 코드·씬·프리팹의 실제 참조와 수명주기

설계 문서의 “다음 Stage”는 구현 순서 참고일 뿐 구현 권한이 아니다. 사용자가 요청하지 않은 다음 단계로 자동 진행하지 않는다.

## 2. 쓰기 전 작업 계약

각 논리적 작업을 시작할 때 한 번, 파일이나 Unity 오브젝트를 변경하기 전에 아래 다섯 항목을 짧게 고정하고 사용자에게 진행 보고로 알린다. 같은 계약 안의 사소한 연속 편집마다 반복하지 않는다.

1. **요청 결과:** 사용자가 실제로 보게 될 동작
2. **요구 메커니즘:** 동일 인스턴스, 데이터 복원, 새 인스턴스 생성 등 요구된 방식
3. **반드시 보존할 것:** 기존 기능, 데이터, 오브젝트, 씬 흐름
4. **이번에 하지 않을 것:** 후속 Stage, 디자인, 리팩터링 등 제외 범위
5. **완료 검증:** 어떤 실제 조작과 관찰로 성공을 판정할지

모든 변경은 위 항목 중 하나에 직접 필요해야 한다. 완료 기준과 연결되지 않는 변경은 하지 않는다.

결과를 실질적으로 바꾸는 모호성이 있으면 편집 전에 질문한다. 현재 코드와 사용자 표현으로 안전하게 결정할 수 있으면 최소 가정으로 진행하고 그 가정을 알린다.

## 3. 사용자 용어를 임의로 바꾸지 않는다

다음 표현은 서로 대체할 수 없다.

- **“같은 오브젝트를 그대로 보존”**: 동일한 런타임 `GameObject`와 `MonoBehaviour` 인스턴스가 살아 있어야 한다. 전후 `GetInstanceID()`가 같아야 하며 재생성·복사·snapshot 복원은 불합격이다.
- **“데이터를 보존”**: 값의 연속성을 뜻한다. 새 오브젝트에 값을 복원해도 될 수 있지만, 사용자가 오브젝트 보존을 요구했다면 이것만으로는 불충분하다.
- **“전역”**: 해당 수명 범위에서 권위 있는 소유자가 하나이며 필요한 씬 전환을 견딘다는 뜻이다. 무조건 `static` 또는 새 Singleton을 만들라는 뜻은 아니다.
- **“100% 보존”**: 사용자가 지목한 대상뿐 아니라 그 기능에 필수인 직렬화 참조와 자식 계층까지 포함한다. 일부 값만 같거나 외형만 비슷하면 불합격이다.
- **“최소 구현”, “디자인 배제”**: 모델·텍스처·VFX·꾸밈을 그레이박스 수준으로 제한하라는 뜻이다. 기능, 스크립트, UI, 참조, 객체 동일성을 제거하라는 뜻이 아니다.
- **“프리셋/정의 데이터”**: 아이템 종류처럼 공유되는 정적 정의다. 개별 런타임 아이템이나 세이브 인스턴스와 동일하지 않다.

사용자가 요구한 메커니즘을 AI가 “동등하다”고 판단한 다른 구조로 바꾸는 것은 금지한다. 다른 구조가 정말 필요하면 변경 전에 원안과의 차이, 사용자에게 보이는 영향, 수명주기 영향을 설명하고 승인을 받는다.

## 4. 현재 프로젝트에서 잠긴 결정

사용자가 명시적으로 변경하기 전까지 아래 항목을 MUST 유지한다.

### 게임 방향

- 싱글플레이 PvE 생존 탈출 파밍 게임이다.
- 탑다운 시점의 Zero Sievert 계열 방향이다.
- 멀티플레이, 랜덤 맵, 전투 수치, 사망 손실, 최종 입력키 등 미정 기능을 임의로 확정하지 않는다.

### 현재 맵 왕복과 플레이어 수명주기

- `GameMap1`과 `GameMapTest`의 직접 왕복은 `MainMenuScene`과 `GameLoadingScene`을 거치거나 수정하지 않는다.
- 단 하나의 `PersistentGameplayShell`이 `DontDestroyOnLoad` 루트로 존재한다.
- 이 셸은 실제 Player, 플레이어 외형 계층, 현재 Player 구성 스크립트, Camera/AudioListener, HUD, `InventoryUIManager`와 인벤토리 UI/Core/View, EventSystem 및 기능상 필수 UI 계층을 **같은 인스턴스**로 유지한다.
- 두 게임플레이 씬에는 scene-local **런타임** Player, gameplay Camera, Inventory UI, EventSystem 복사본을 두지 않는다.
- 편집 상태 Game View를 위한 `AuthoringPreviewCamera` 프리팹 인스턴스 1개는 예외다. 이 루트는 `EditorOnly` 태그를 사용하고 AudioListener가 없으며, 자식 Camera는 Play Mode에서 비활성화되고 Player 빌드에서 제거되어야 한다. 이를 실제 gameplay Camera나 셸 복사본으로 취급하지 않는다.
- Player 셸 구성에 관해서 두 게임플레이 씬은 `GameplayShellBootstrap`, scene-local `SceneSpawnController`, SpawnPoint와 맵 오브젝트만 소유한다. 위 편집 전용 Camera와 `GameMap1`의 기존 별도 `GameManager`는 이 문장의 예외이며 셸 구성요소가 아니다.
- Bootstrap은 셸이 없을 때만 동일 프리팹을 한 번 생성한다.
- `SceneSpawnController`는 기존 persistent Player를 목적지 SpawnPoint로 이동시키고 Rigidbody 속도를 초기화할 뿐, Player를 교체하지 않는다.
- 씬별 Player 재생성, `PlayerRuntimeState` snapshot/restore, 새 UI 재바인딩을 “Player 전체 보존”의 대체 구현으로 다시 도입하지 않는다.
- 기존 `GameManager`는 셸과 별개의 전역 오브젝트다. 근거 없이 셸과 합치거나 GameMapTest 직접 실행에서 자동 생성하지 않는다.
- 현재 보존 범위는 한 번의 Play Mode 실행이다. 디스크 세이브가 구현되었다고 주장하지 않는다.

### 아이템과 인벤토리

- `ItemDefinition`/`ItemDatabase`의 숫자 ID는 **아이템 종류 definition ID**다.
- 이름, 설명, 크기, 아이콘, 컨테이너 정의는 ScriptableObject 프리셋에서 조회한다.
- 개별 영구 instance ID, 수량, 내구도, 탄약, 능력치, 저장 형식은 아직 확정하지 않는다.
- 현재 인벤토리는 persistent 셸 안의 동일 `InventoryUIManager`와 동일 런타임 객체 그래프가 유지한다. 씬 도착 때 기본 아이템을 다시 seed하지 않는다.
- 세이브 연동은 사용자가 별도로 요청하는 후속 범위다.

## 5. Unity 아키텍처 원칙

### 객체 수명과 씬

- `LoadSceneMode.Single`은 현재 씬 오브젝트를 언로드한다. 동일 인스턴스 보존이 요구되면 명시적인 영속 소유 구조가 필요하다.
- `DontDestroyOnLoad`는 root GameObject에만 적용하며 자식 계층을 함께 보존한다. 영속 루트에 일부 컴포넌트만 넣고 참조 대상 UI·Camera·EventSystem을 이전 씬에 남겨 파괴되게 해서는 안 된다.
- 영속 오브젝트를 만들기 전에 serialized reference의 전체 의존 관계를 검사한다. 프로젝트 에셋 참조를 제외하고 source scene 오브젝트를 가리키는 외부 참조가 남지 않아야 한다.
- 목적지 씬에 영속 오브젝트의 완성본 복사본을 배치한 뒤 런타임에 늦게 삭제하는 방식은 피한다. 가능하면 작은 Bootstrap이 인스턴스가 없을 때만 프리팹을 생성한다.
- 새 전역 Manager나 Singleton을 만들기 전에 기존 권위 소유자를 검색한다. 같은 책임의 평행 Manager를 만들지 않는다.
- 씬 전환 전 드래그, 열린 UI, 선택된 EventSystem 오브젝트, scene-local 상호작용 대상과 캐시를 정리한다. 도착과 배치가 성공한 뒤 입력을 다시 연다.

### Prefab과 씬 구성

- 여러 씬에서 같은 구성이 필요하면 복사·붙여넣기보다 Prefab을 단일 원본으로 사용한다.
- 프리팹 변경은 source와 instance override를 구분하고, 의도하지 않은 override를 만들지 않는다.
- 씬과 프리팹은 Unity Editor API/RunCommand로 수정한다. Unity가 사용 가능한데 `.unity`, `.prefab`, `.asset` YAML을 텍스트로 직접 조작하지 않는다.
- 씬 저장 전 Missing Script, Missing Reference, 중복 Camera/AudioListener/EventSystem, 잘못된 tag/layer, null serialized field를 검사한다.

### 정의 데이터, 런타임 상태, 세이브

- ScriptableObject는 아이템·맵·적 등의 공유 정의와 설정에 사용한다.
- 런타임 개별 상태와 정적 정의를 섞지 않는다. 개별 상태의 소유자와 수명 범위를 명시한다.
- 배포 빌드의 사용자 세이브를 ScriptableObject asset 변경으로 구현하지 않는다. 세이브는 별도 직렬화 DTO와 파일 정책을 설계하는 단계에서만 구현한다.
- 현재 사용 중인 단순 구조를 실제 요구 없이 패턴·이벤트 버스·서비스 로케이터로 바꾸지 않는다. 디자인 패턴은 목표가 아니라 문제 해결 도구다.

### 코드 책임

- 기존 구현을 먼저 검색하고 확장 가능한 경계를 확인한다. 같은 기능을 하는 새 클래스를 이름만 바꿔 만들지 않는다.
- 한 컴포넌트의 책임을 분명히 하되, 요청과 무관한 대규모 리팩터링은 하지 않는다.
- 입력 소유자는 기능별로 하나여야 한다. 같은 키를 여러 `Update`가 경쟁해서 처리하지 않게 한다.
- Unity 버전과 설치된 패키지에서 실제 사용 가능한 API인지 확인한다. `Library/PackageCache`의 registry package를 직접 수정하지 않는다.

## 6. 게임 설계와 단계별 개발 방식

- 이 프로젝트의 기본 방식은 **외형은 빠른 그레이박스, 핵심 수명주기와 데이터 계약은 실제 게임에 이어질 수 있게 구현하는 evolutionary prototype**이다.
- 사용자가 명시적으로 throwaway proof-of-concept를 요청하지 않는 한, “큐브로 테스트”를 “기능도 임시 재생성으로 대충 구현”으로 해석하지 않는다.
- 한 번에 현재 Stage의 가장 작은 플레이 가능한 흐름만 완성한다. 핵심 상호작용과 그 상호작용이 의존하는 선행조건만 포함한다.
- 각 기능은 구현 전에 “무엇을 검증하는 프로토타입인가”와 acceptance criteria를 가진다.
- 현재 Stage가 실제 Play Mode 검증을 통과하기 전 다음 Stage를 섞지 않는다.
- 디자인 수치, 입력키, 이름 규칙, 보상, 손실, 저장 시점처럼 플레이 경험을 바꾸는 결정은 `[미정]`으로 남긴다. AI의 아이디어는 `[제안]`으로만 제시하고 승인 없이 코드로 확정하지 않는다.
- 플레이테스트 결과가 기존 가정을 반박하면 문서와 구현을 구분해서 갱신한다. 사용자 승인 없이 기획 문서를 새 방향으로 전면 재작성하지 않는다.

## 7. 작업 유형별 실행 절차

### 기능 구현

1. 관련 코드·씬·프리팹만 타깃 검색한다.
2. 현재 동작, 객체 수명, 참조 그래프, Console과 git 기준선을 기록한다.
3. 2장의 작업 계약을 고정한다.
4. 기존 아키텍처를 유지하면서 요구 메커니즘을 그대로 만족하는 최소 변경을 설계한다.
5. 코드 파일은 `apply_patch`, Unity 오브젝트는 Unity Editor API/RunCommand로 변경한다.
6. 컴파일과 serialized reference를 확인한다.
7. 사용자가 실제로 수행할 입력 순서로 Play Mode에서 검증한다.
8. 기존 인접 기능 회귀를 검사하고 Editor를 안전한 상태로 되돌린다.
9. 변경 파일, 실제 검증, 남은 미검증을 구분해 보고한다.

### 버그 수정

1. 증상을 재현하거나 재현할 수 없는 이유를 확인한다.
2. 원인 후보를 한 번에 하나씩 증거로 좁힌다.
3. 근본 원인에 필요한 가장 작은 수정만 적용한다.
4. 원래 재현 절차와 인접 회귀 절차를 모두 다시 실행한다.

진단 요청은 원인과 증거까지만 제공하고, 사용자가 수정을 요청하지 않았다면 임의로 구현을 변경하지 않는다.

### 설계·검토 요청

- 읽기 전용으로 조사한다. 검토 요청을 구현 권한으로 확대하지 않는다.
- 현재 사실, 위험, 선택지, 권장을 분리한다.
- 권장이 현재 구현보다 일반적으로 좋아 보여도 사용자 요구와 충돌하면 적용하지 않는다.

## 8. AI가 하면 안 되는 행동

다음 행동은 명시적으로 금지한다.

1. 쉬운 구현을 위해 사용자의 목표나 요구 메커니즘을 다른 문제로 바꾸기
2. 동일 Player 보존 요구를 씬별 재생성, 값 복사, 외형 복제, UI 재바인딩으로 대체하기
3. 사용자가 말한 “최소 디자인”을 기능·스크립트·인벤토리 제거로 해석하기
4. 최신 사용자 정정보다 첫 계획, 장기 목표, 설계 문서의 추천 순서를 우선하기
5. 요청하지 않은 다음 Stage, 저장, 전투, AI, 랜덤 맵, 폴더 재편을 함께 구현하기
6. 기존 책임과 겹치는 Manager, Singleton, 이벤트 시스템, 데이터베이스를 추가하기
7. 일부 자식이나 참조만 `DontDestroyOnLoad`로 보내고 파괴된 scene reference를 남기기
8. 목적지 씬의 duplicate Player/Camera/EventSystem이 실행된 뒤 삭제하도록 만들어 중복 입력을 허용하기
9. ScriptableObject definition ID를 개별 아이템 instance ID 또는 세이브 데이터라고 주장하기
10. 컴파일 성공만으로 입력, 씬 전환, UI, 물리 기능까지 완료됐다고 보고하기
11. Console을 지워 오류를 해결한 것처럼 보이게 하거나 기존 오류와 신규 회귀를 구분하지 않기
12. 실행하지 않은 테스트를 통과했다고 쓰거나 정적 검사만으로 Play Mode 동작을 추정하기
13. Unity scene/prefab YAML을 무리하게 직접 편집하거나 `.meta`/GUID를 임의 생성·교체하기
14. `Library/PackageCache`나 registry package 캐시를 직접 수정하기
15. 사용자의 기존 dirty 변경, 에셋, 씬 오브젝트, Missing Script를 원인 확인 없이 삭제·덮어쓰기
16. 요청에 필요하지 않은 패키지 설치, 외부 에셋 import, ProjectSettings 변경, 대규모 이름 변경 수행하기
17. `[미정]` 기획을 코드나 문서에서 `[확정]`으로 승격하기
18. 사용자 요청 없이 커밋·push·branch 변경을 수행하거나, 관련 없는 미추적 파일을 한꺼번에 stage하기
19. 사용자에게 반말하거나, 잘못된 해석을 지적받은 뒤 같은 전제를 유지하기

## 9. 완료 검증 게이트

모든 기능은 위험에 비례해 아래 검증을 거친다.

### 공통

- 변경 전 Console 기준선과 변경 후 delta를 구분한다.
- Unity import/compile 완료 후 새 Error, Exception, Assert가 없어야 한다.
- 새 Warning은 원인을 확인한다. 기존 외부 에셋 경고를 신규 회귀로 오인하지 않는다.
- 새 Missing Script/Reference, null serialized field, 의도하지 않은 scene dirty가 없어야 한다.
- 기능과 관련된 기존 입력과 UI를 최소 한 번 회귀 테스트한다.
- 검증 후 Play Mode를 종료하고 원래 활성 씬과 의도한 저장 상태를 확인한다.

### 실제 상호작용 기능

- 코드 호출로 우회하지 말고 사용자가 누를 실제 키와 UI 순서로 검사한다.
- 정상 경로, 취소 경로, 범위 밖 입력, 빠른 중복 입력을 확인한다.
- 중요한 흐름은 반복 실행해 이벤트 구독, UI, 데이터, 오브젝트가 누적되지 않는지 확인한다.

### 객체 수명/씬 이동/영속 셸 변경

Player의 객체 수명, 씬 이동, persistent shell 계층·참조 또는 인벤토리 영속성에 영향을 주는 변경은 최소한 다음을 실제 Play Mode에서 확인한다. 단순 수치나 해당 수명주기와 무관한 Player 변경은 공통 게이트와 변경 관련 회귀만 위험에 비례해 적용한다.

- `GameMap1 → GameMapTest → GameMap1` 왕복 3회
- `GameMapTest` 직접 시작
- 셸, Player, Camera, `InventoryUIManager`, EventSystem의 `GetInstanceID()`가 왕복 전후 동일
- persistent 셸은 정확히 1개, destination scene-local 런타임 Player/gameplay Camera/UI/EventSystem은 0개. `EditorOnly` 미리보기 Camera가 직렬화되어 있으면 Play 중 활성 Camera 수에는 포함되지 않아야 한다.
- 매 도착 시 지정 SpawnPoint 배치와 Rigidbody 속도 초기화
- 두 씬에서 이동과 상호작용, `I` 인벤토리 열기/닫기
- 인벤토리 슬롯·회전·컨테이너 내부 상태 보존과 기본 아이템 재생성 없음
- Chest 열기/닫기, 드래그 중 닫기, case popup 정리 회귀
- duplicate AudioListener/EventSystem, MissingReference, destroyed-object 접근 오류 없음

“같아 보임”이 아니라 instance identity와 object count를 증거로 확인한다.

### 자동 테스트와 빌드

- 순수 데이터/규칙은 가능하면 EditMode 테스트로, 프레임·씬·입력·물리는 PlayMode 테스트 또는 실제 Play Mode로 검증한다.
- 자동 테스트가 없다는 이유로 런타임 검증을 생략하지 않는다.
- Player build가 요청 범위나 위험에 필요한 경우 실행한다. 실행하지 않았으면 “빌드 미검증”이라고 명시한다.

필수 검증을 실행할 수 없으면 작업을 “완료”라고 부르지 않고, 구현됨/미검증/차단 사유를 구분한다.

## 10. 파일과 Git 안전

- `Assets/`에서 먼저 관련 파일을 찾고, 필요한 범위만 확장한다. 무관한 대규모 폴더 열람은 피한다.
- Unity 에셋과 해당 `.meta`는 한 쌍으로 보존한다.
- `Library/`, `Temp/`, `obj/`, 빌드 출력은 소스처럼 편집하거나 커밋하지 않는다.
- 작업 전후 `git status`와 diff로 사용자 변경을 구분한다.
- 기존 dirty worktree에서 무관한 변경을 되돌리거나 포맷하지 않는다.
- 삭제·이동은 정확한 대상과 참조를 확인한 뒤 수행한다. 광범위한 reset/checkout은 금지한다.
- 커밋을 요청받으면 현재 작업 범위만 명시적으로 stage하고 diff를 검토한 뒤 커밋한다.
- push, PR, 원격 변경은 사용자가 별도로 요청한 경우에만 수행한다.

### 검증 완료 작업의 자동 로컬 커밋

- 사용자는 이 저장소에서 AI가 구현하고 검증까지 마친 작업을 기능 단위의 **로컬 Git 커밋**으로 자동 기록하는 것을 상시 승인했다. 최신 사용자 메시지에서 커밋하지 말라고 정정하면 그 지시를 우선한다.
- Unity 저장·import·compile과 요청 범위의 검증이 끝난 뒤에만 커밋한다. 구현 중간, 컴파일 실패, 필수 검증 미완료 또는 원인 불명의 신규 오류가 있는 상태는 자동 커밋하지 않는다.
- `git add .`, `git add -A`처럼 작업 트리 전체를 stage하지 않는다. 이번 작업에서 직접 변경한 경로와 필요한 대응 `.meta`만 명시적으로 stage하고, staged diff와 파일 목록을 다시 확인한다.
- 기존 dirty 변경이나 다른 기능의 변경이 같은 파일에 섞여 안전하게 분리할 수 없으면 그 파일은 자동 커밋하지 않고 사용자에게 이유를 보고한다.
- 자동 커밋은 task 완료 경계에서 한 번 수행한다. 시간 간격, 파일 저장, Play Mode 종료 또는 Unity 종료를 조건으로 전체 작업 트리를 커밋하는 스크립트는 사용하지 않는다.
- 자동 push, 원격 branch 변경, PR 생성과 Unity Version Control 체크인은 포함되지 않는다. 이 프로젝트의 자동 기록 기준은 현재 Git 저장소의 로컬 커밋이다.

## 11. Unity Editor 실행 규칙

씬 오브젝트, 프리팹, Material, serialized reference 변경은 가능하면 Unity MCP의 RunCommand를 사용한다.

RunCommand 코드 규칙:

- 클래스 이름은 반드시 `CommandScript`로 한다.
- `internal class CommandScript : IRunCommand` 형태를 사용한다.
- 생성은 `result.RegisterObjectCreation`, 수정 전에는 `result.RegisterObjectModification`, 삭제는 `result.DestroyObject`를 사용한다.
- 로그는 `result.Log`, 경고는 `result.LogWarning`, 오류는 `result.LogError`를 사용한다.
- top-level statement를 사용하지 않는다.
- Undo/Redo와 scene dirty/save 범위를 명확히 한다.
- 명령 실행 뒤 Console, 오브젝트 수, 참조, 씬 dirty 상태를 별도로 검증한다. RunCommand 성공 메시지만으로 완료 판정하지 않는다.

코드 파일 변경은 `apply_patch`를 사용한다. 코드 생성 도구로 파일 전체를 무심코 덮어쓰지 않는다.

## 12. 설계 문서 관리

- `extraction_survival_game_design_dev_plan.md`는 설계와 단계 기록의 기준 문서다.
- `unity_development_progress.md`는 최근 검증된 구현 동작, 코드와 사용자 의도의 차이, 미검증 경계를 빠르게 인계하는 진행 문서다. 새 기능·버그 작업 시작 시 관련 절을 먼저 읽는다.
- 주요 기능을 실제로 검증한 뒤에는 진행 문서를 현재 증거에 맞게 갱신한다. 코드만 읽은 사실을 Play Mode 확인으로 승격하지 않는다.
- 사용자 요청 없이 문서 전체를 재작성하거나 Stage 순서를 바꾸지 않는다.
- `[확정]`은 사용자 결정만 기록한다.
- `[미정]`은 사용자 결정 전까지 유지한다.
- `[현재]`은 코드·씬에서 직접 확인한 사실만 기록한다.
- `[완료]`는 필수 Play Mode/검증 증거가 있을 때만 기록한다.
- 구현이 문서와 다르면 조용히 문서를 구현에 맞추지 않는다. 최신 사용자 요구와 실제 구현을 비교해 어느 쪽을 고칠지 먼저 판단한다.

## 13. 근거 자료

이 지침은 다음 공식 자료의 원칙을 프로젝트 상황에 맞게 적용한다.

- OpenAI, Custom instructions with AGENTS.md: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Unity, `Object.DontDestroyOnLoad`: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Object.DontDestroyOnLoad.html
- Unity, `SceneManager.LoadSceneAsync`: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/SceneManagement.SceneManager.LoadSceneAsync.html
- Unity, Introduction to prefabs: https://docs.unity3d.com/6000.0/Documentation/Manual/prefabs-introduction.html
- Unity, ScriptableObject: https://docs.unity3d.com/6000.1/Documentation/Manual/class-ScriptableObject.html
- Unity, Three ways to architect game code with ScriptableObjects: https://unity.com/how-to/architect-game-code-scriptable-objects
- Unity Learn, Plan and scope your prototype: https://learn.unity.com/pathway/creative-core/unit/prototyping/tutorial/plan-and-scope-your-prototype-3
- Unity Learn, Test your prototype: https://learn.unity.com/pathway/creative-core/unit/prototyping/tutorial/test-your-prototype-3
- Unity Test Framework, Edit Mode vs Play Mode tests: https://docs.unity3d.com/Packages/com.unity.test-framework@2.0/manual/edit-mode-vs-play-mode-tests.html
