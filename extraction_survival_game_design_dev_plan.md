# 싱글 생존 탈출 게임: Unity 중심 개발 설계 및 단계별 계획

**문서 버전:** v0.2  
**갱신일:** 2026-08-20  
**프로젝트:** Fantasy Survival Escape Game  
**문서 성격:** 게임 기획서가 아니라, 현재 Unity 프로젝트에서 어떤 기반을 먼저 완성해야 다음 기능을 안전하게 구현할 수 있는지 정리한 개발 의존성 문서

---

## 0. 문서 사용 규칙

이 문서는 기능을 많이 나열하는 로드맵이 아니다. 각 기능의 Unity 선행조건과 완료 기준을 정하고, 한 단계가 실제 Play Mode에서 검증된 뒤 다음 단계로 넘어가기 위한 문서다.

문서의 표시는 다음 의미로 사용한다.

- **[확정]** 사용자가 직접 결정한 게임 방향 또는 개발 순서
- **[현재]** 프로젝트 파일과 Unity Editor에서 직접 확인한 구현 상태
- **[권장]** 현재 구조에서 재작업을 줄이기 위한 기술적 선택
- **[미정]** 구현 직전에 사용자가 결정해야 하는 게임 규칙
- **[보류]** 현재 단계의 선행조건이 아니므로 만들지 않는 기능

적용 원칙:

1. 사용자 결정이 이 문서보다 우선한다.
2. 입력키, 수치, 전투 방식, 손실 규칙 등을 AI가 임의로 확정하지 않는다.
3. 각 단계는 선행조건, Unity 구현물, 완료 기준, 다음 단계와의 관계를 함께 기록한다.
4. 완료 기준을 통과하지 못한 단계 위에 후속 기능을 얹지 않는다.
5. 기능 하나를 만들기 위해 프로젝트 전체 구조나 폴더를 한꺼번에 재편하지 않는다.
6. 씬, 프리팹, ScriptableObject, ProjectSettings를 변경하면 직렬화 참조와 Console을 반드시 확인한다.

---

## 1. 확정된 게임 방향

### 1.1 장르와 시점

- **[확정]** 싱글플레이 PvE 생존 탈출 파밍 게임
- **[확정]** 타르코프류의 출격, 파밍, 생환, 사망 손실 구조를 지향
- **[확정]** Zero Sievert처럼 탑다운 시점에서 진행
- **[확정]** 멀티플레이는 개발 범위에 포함하지 않음

장기적인 핵심 루프:

    기지 또는 안전지대
    → 출격할 맵 선택
    → 원정 맵 진입
    → 탐색, 루팅, 전투 또는 회피
    → 탈출 성공 또는 사망
    → 결과 반영
    → 정비 후 재출격

### 1.2 현재 확정된 개발 방식

- **[확정]** 전체 루프를 한 번에 만들지 않고, 실제로 실행 가능한 작은 단위로 진행한다.
- **[확정]** 첫 번째 기능은 맵 선택 오브젝트에서 빈 원정 맵으로 이동하고, 귀환 포탈로 원래 맵에 돌아오는 왕복 기능이다.
- **[확정]** 기본 플레이어 아이템 영속성은 맵 왕복 안정화 뒤 단일 슬롯 프로토타입으로 구현했다. 생환·사망 결과와 기지 전체 상태 저장은 해당 런타임 규칙이 확정된 뒤 확장한다.
- **[확정]** 첫 원정의 씬 경계는 `GameMapTest`로 고정한다. **[현재]** 그 씬 안의 도심 회색상자 공간은 런타임 seed로 도로와 큐브 건물만 절차 생성한다.
- **[확정]** 지하 던전과 오염 지역은 도심 생성기의 옵션으로 만들지 않고, 공간 규칙이 정해질 때 별도 생성 방식으로 설계한다.
- **[확정]** 현재 아이템 종류는 숫자 ID 기반 ItemDatabase로 관리한다.

### 1.3 아직 확정하지 않은 게임 규칙

다음 항목은 해당 기능을 구현하기 직전에 결정한다.

- 최종 상호작용 키와 키 변경 지원 방식
- 조준 방식과 공격 입력
- Hitscan 또는 Projectile 여부
- 체력, 피해량, 장탄수, 장전 시간 등의 수치
- 탈출 포탈의 작동 조건과 대기 시간
- 사망 시 장비 및 획득물 손실 규칙
- 저장 슬롯, 자동 저장 시점, 강제 종료 처리
- 아이템 능력치 구조
- 최종 캐릭터 비율과 아트 스타일
- 도심 생성 seed의 저장·재현 정책과 최종 생성 수치
- 지하 던전·오염 지역의 개별 공간 생성 규칙
- 난이도 구조, 상점, 제작, 퀘스트

---

## 2. 현재 Unity 프로젝트 기준선

이 절은 희망 구조가 아니라 실제 프로젝트에서 확인된 상태만 기록한다. 프로젝트가 변경되면 함께 갱신한다.

**마지막 확인:** 2026-08-21. Unity 버전, 빌드 타깃, 활성 씬, Console 상태처럼 자주 바뀌는 값은 작업을 시작할 때 다시 확인한다.

### 2.1 Unity와 빌드 기준

- **[현재]** Unity 6000.5.9f1
- **[현재]** 현재 타깃은 Standalone Windows 64-bit
- **[현재]** 별도의 프로젝트 Build Profile 에셋은 확인되지 않았고, 현재 씬 목록은 EditorBuildSettings를 사용한다.
- **[현재]** 최종 Play Mode 왕복에서 새 Error, Exception, Assert와 Stage 1 코드나 씬을 지목하는 새 Warning은 발생하지 않았다.
- **[현재 알려진 기존 이슈]** 외부 환경 에셋의 obsolete API와 과거 인벤토리 경고 등은 Stage 1 회귀와 구분한다.
- **[현재 해결]** GameMap1 Player에 남아 있던 비활성 Missing MonoBehaviour는 원본 스크립트 파일과 GUID가 프로젝트에 없고 Unity가 해당 상태로 프리팹 저장을 거부해 제거했다. 실제로 연결된 Player 컴포넌트는 모두 보존했다.

### 2.2 현재 Build Settings 씬

| 순서 | 씬 | 활성 여부 | 현재 용도 |
|---:|---|---|---|
| 0 | InitialLoadingScene | 활성 | 초기 로딩 |
| 1 | MainMenuScene | 활성 | 메인 메뉴 |
| 2 | GameLoadingScene | 활성 | GameMap1 로딩 |
| 3 | GameMap1 | 활성 | 현재 플레이 가능한 기본 맵 |
| 4 | GameMapTest | 활성 | Stage 1 직접 왕복 및 도심 절차 생성 회색상자 시험 씬 |
| 5 | Sample | 비활성 | 샘플 |

현재 시작 흐름:

    InitialLoadingScene
    → MainMenuScene
    → 시작 버튼 선택
    → GameLoadingScene
    → GameMap1

### 2.3 현재 씬 이동과 플레이어 구조

- **[현재]** GameLoadingManager는 목적지를 GameMap1로 하드코딩한다.
- **[현재]** 기존 InitialLoadingScene → MainMenuScene → GameLoadingScene 흐름은 이번 Stage 1에서 수정하지 않았다.
- **[현재]** GameMap1과 GameMapTest 사이에는 MainMenuScene과 GameLoadingScene을 거치지 않는 Stage 1 전용 직접 씬 이동이 연결되어 있다.
- **[현재]** 직접 씬 이동은 목적지 씬 이름과 SpawnPoint ID를 일회성 컨텍스트로 전달하고, 도착 배치 뒤 요청을 소비한다.
- **[현재]** Assets/Claude/GameLoader.cs에 씬 이름과 spawnPoint를 받는 미사용 프로토타입이 남아 있지만, 어떤 씬이나 프리팹에도 연결되어 있지 않다.
- **[현재]** GameMap1과 GameMapTest에는 scene-local 런타임 Player, gameplay Camera, Inventory UI, EventSystem 복사본을 두지 않는다. 단, 편집 상태 Game View용 `EditorOnly` Authoring Preview Camera가 씬마다 1개 있으며 Play 중에는 비활성화되고 빌드에서는 제거된다.
- **[현재]** 두 씬의 GameplayShellBootstrap은 PersistentGameplayShell.Instance가 없을 때만 같은 PersistentGameplayShell 프리팹을 한 번 생성한다.
- **[현재]** PersistentGameplayShell은 DontDestroyOnLoad이며 실제 Player와 외형, PlayerMovement/PlayerStats/PlayerInteractor를 포함한 Player 스크립트, Camera, InventoryUIManager와 인벤토리 UI, EventSystem을 같은 인스턴스로 유지한다.
- **[현재]** 각 씬은 SceneSpawnController와 SpawnPoint만 소유한다. SceneSpawnController는 기존 persistent Player를 목적지 SpawnPoint로 옮기고 Rigidbody 속도를 0으로 초기화한다.
- **[현재]** GameManager는 PersistentGameplayShell과 별개의 기존 전역 싱글톤이다. GameMapTest 직접 시작 시 GameManager를 자동 생성하지 않는다.
- **[현재]** 플레이어 이동은 기존 Input Manager의 축 입력을 직접 읽는다.

### 2.4 현재 상호작용 구조

- **[현재]** PlayerInteractor가 E 입력을 한 번만 읽고 범위 안의 가장 가까운 Interactable을 선택한다.
- **[현재]** InventoryUIManager는 I와 Escape 입력, 인벤토리 UI 상태, 상자 UI 열기와 닫기를 담당한다.
- **[현재]** GameMap1의 Chest 2개는 ChestInteractable을 통해 기존 인벤토리 UI에 연결된다.
- **[현재]** GameMap1에는 불투명 파란 Cube 맵 선택 오브젝트와 GameMapTest 하나를 표시하는 최소 OnGUI 선택 화면이 있다.
- **[현재]** GameMapTest에는 불투명 주황 Cube 귀환 오브젝트가 있고 GameMap1의 BaseReturn SpawnPoint로 직접 돌아온다.

포탈 코드는 InventoryUIManager에 넣지 않는다. 상자, 포탈, 문, NPC는 각각 행동만 구현하고 입력과 대상 선택은 PlayerInteractor 한 곳이 담당한다.

### 2.5 현재 아이템과 인벤토리 구조

- **[현재]** ItemDefinition은 ScriptableObject다.
- **[현재]** ItemDefinition에는 숫자 ID, 이름, 설명, 인벤토리 크기, 이미지, 장착 가능 장비 슬롯, 일반 또는 컨테이너 구분, 컨테이너 내부 크기가 있다.
- **[현재]** 능력치, 수량, 내구도, 탄약, 월드 프리팹 정보는 아직 없다.
- **[현재]** ItemDatabase는 ItemDefinition 목록을 보유하고 숫자 ID로 조회한다.
- **[현재]** DB에는 ID 1부터 6까지 6개 항목이 등록되어 있다.
- **[현재]** ID 1~5의 시험 총기 정의는 하나의 Weapon 장착 슬롯에 호환되고, ID 6 시험 보관함은 장착 불가다. Weapon 슬롯은 공격·조준·발사 기능이나 월드 3D 표현을 아직 결정하지 않는다.
- **[현재]** InventoryItemData는 ItemDefinition 참조, 회전 상태와 현재 grid/container/equipment 소유자를 가지는 런타임 객체다.
- **[현재]** 숫자 아이템 ID는 아이템 종류 ID다. 실제 소유한 개별 물건의 고유 ID는 아니다.
- **[현재]** PersistentGameplayShell이 처음 생성될 때 InventoryUIManager.Awake가 8×9 인벤토리, 시험 아이템 ID 1~6과 빈 12슬롯 EquipmentLoadoutData를 한 번 생성한다.
- **[현재]** 씬 전환 때 InventoryUIManager와 PlayerInventoryState를 새로 만들거나 재바인딩하지 않는다. 같은 InventoryUIManager, StandardStashViewData, EquipmentLoadoutData, StandardCore와 UI View가 shell 안에서 계속 유지된다.
- **[현재]** 따라서 칸 위치, 회전, 장비 슬롯, 동일 종류의 여러 런타임 객체와 컨테이너 내부 관계가 같은 객체 그래프로 유지되며, 각 아이템은 한 소유자에만 귀속된다.
- **[현재]** Play Mode 종료 시 shell 인스턴스는 파괴된다. New Game은 초기 시험 인벤토리와 빈 장비로 시작하고, 단일 슬롯 세이브/로드 프로토타입은 플레이어 아이템 상태(인벤토리·장비)를 검증 후 새 실행에 복원한다. Player·Camera·UI 오브젝트 자체는 디스크에 저장하지 않는다.
- **[현재]** Assets/Claude/SaveManager.cs에 현재 씬 이름과 날짜를 JSON으로 기록하는 미사용 저장 프로토타입이 있지만, 아이템 데이터를 저장하지 않고 활성 씬에도 연결되어 있지 않다.

---

## 3. Unity 구조 원칙

### 3.1 정의 데이터, 런타임 상태, 씬 표현, 저장 데이터를 분리한다

| 구분 | Unity 형태 | 역할 | 예시 |
|---|---|---|---|
| 정의 데이터 | ScriptableObject | 변하지 않는 프리셋 | ItemDefinition과 장착 가능 슬롯, 이후 MapDefinition |
| 런타임 상태 | 일반 C# 데이터 | 현재 플레이 세션에서 변하는 값 | 아이템 위치, 회전, 장비 슬롯, 현재 소유자, 현재 원정 상태 |
| 씬 표현 | MonoBehaviour, GameObject, UI | 입력, 충돌, 카메라, 화면 표시 | Player, Portal, Inventory UI |
| 저장 데이터 | 직렬화 가능한 DTO | 게임 종료 후에도 유지할 값 | definitionId, 위치, 회전, 컨테이너 관계, equipmentSlot |

Stage 2-A의 shell 동일 인스턴스 보존과 디스크 복원은 서로 다른 메커니즘이다. 실행 중에는 같은 PlayerInventoryState 객체가 유지되고, 재실행 로드는 DTO에서 새 PlayerInventoryState를 검증·재구성한다.

중요한 규칙:

- 아이콘, 이름, 크기처럼 ItemDefinition에 있는 값은 저장 파일에 복사하지 않는다.
- 저장과 런타임 상태에서는 숫자 definitionId를 기록하고 DB에서 다시 조회한다.
- MonoBehaviour, GameObject, Texture2D, ScriptableObject 참조를 저장 데이터에 직접 넣지 않는다.
- 동일한 종류의 아이템이 여러 개 존재하려면 런타임 단계에서 개별 인스턴스를 구분할 수 있어야 한다.
- 저장 DTO는 런타임 규칙이 검증된 뒤 만든다.

### 3.2 PersistentGameplayShell이 플레이어 셸을 소유한다

- 실제 Player, 외형, Player 스크립트, Camera, Inventory UI와 EventSystem은 PersistentGameplayShell 프리팹 하나에 속한다.
- shell 루트는 DontDestroyOnLoad이며 GameMap1과 GameMapTest 왕복 동안 같은 인스턴스를 유지한다.
- 각 게임플레이 씬은 GameplayShellBootstrap, SceneSpawnController, SpawnPoint와 월드 오브젝트만 소유한다.
- Bootstrap은 기존 shell이 있으면 새 복사본을 만들지 않는다.
- 씬 전환 시 Player 좌표는 목적지 SpawnPoint로 바꾸고 Rigidbody 속도는 초기화하지만, Player 컴포넌트와 인벤토리/UI 객체는 교체하지 않는다.

### 3.3 기존 시스템을 확장하고 평행 시스템을 만들지 않는다

- Stage 1의 DirectSceneTravel은 두 게임플레이 씬을 빠르게 검증하기 위한 격리된 프로토타입이며 기존 GameLoadingScene 흐름과 동시에 실행하지 않는다.
- 제품 시작 흐름을 통합할 때는 기존 GameLoadingManager를 범용화할지 DirectSceneTravel을 흡수할지 결정하고, 두 로더를 최종 구조에 병행해 남기지 않는다.
- 현재 프로토타입에서는 InventoryUIManager와 인벤토리 런타임 데이터가 shell 안의 동일 인스턴스로 유지된다. 저장 단계에서는 직렬화 DTO만 분리한다.
- 입력과 대상 탐지는 Player 상호작용 컴포넌트로 이동한다.
- 현재 플레이 중 상태는 PersistentGameplayShell의 실제 컴포넌트 인스턴스가 유지한다. RaidSession은 원정 경계와 결과만 별도 소유한다.
- 전역 이벤트 버스, DI 프레임워크, Addressables는 현재 필요하지 않다.

### 3.4 고정 씬 경계와 공간 생성 규칙을 분리한다

- Player 수명주기, 맵 왕복, 루팅, 전투와 AI의 씬 경계는 계속 `GameMapTest`에서 독립 검증한다.
- **[현재 적용 예외]** 사용자가 공간 제작을 먼저 시험하도록 우선순위를 바꿔, 도심형 도로와 큐브 건물 생성만 앞당겼다. 이는 루팅·전투·AI·레이드 결과 Stage까지 앞당긴다는 뜻이 아니다.
- 생성기는 불변 layout을 먼저 계획하고 런타임 오브젝트와 NavMesh를 파생하므로, 씬 이동 오류와 공간 배치 오류를 따로 재현할 수 있어야 한다.
- 지하 던전과 오염 지역은 도심 규칙의 분기로 누적하지 않고 각각 별도 생성 경계를 가진다.

---

## 4. 전체 기능 의존성

개발 순서는 다음과 같다. 이는 필수 엔진 제약이 아니라 저장 형식 재작업을 줄이기 위한 **[권장] 기본 순서**다.

    Stage 0. Unity 기준선 안정화
    → Stage 1. 맵 선택과 왕복 이동
    → Stage 2. 메모리 기반 영속 런타임 상태와 RaidSession
    → Stage 3. 저장 없는 루팅과 생환
    → Stage 4. 플레이어 전투 기반
    → Stage 5. 최소 적 AI와 사망
    → Stage 6. 메모리 안에서 최소 레이드 루프 완성
    → Stage 7. 세이브와 로드
    → Stage 8. 여러 고정 맵과 데이터 확장
    → Stage 9. 랜덤 맵, 난이도, 콘텐츠 확장
    → Stage 10. 설정, 최종 UI, 아트, 사운드, 최적화

기본 인벤토리 저장은 기술적으로 Stage 2 또는 Stage 3이 끝난 뒤 먼저 구현할 수 있다. **[현재 적용]** 사용자가 영속성 검증을 우선해 기본 인벤토리 단일 슬롯 세이브/로드를 별도 하위 단계로 앞당겼다. 생환·사망 결과 규칙과 그 결과의 저장 확장은 Stage 6 이후에 다룬다.

**[현재 적용 예외]** 사용자의 최신 우선순위에 따라 Stage 9 전체가 아니라 도심형 도로·큐브 건물 회색상자 생성만 기술 스파이크로 앞당겼다. 랜드마크, 지형지물, 내부, spawn, 난이도와 다른 맵 유형은 자동으로 다음 작업이 되지 않는다.

### 4.1 기능별 선행조건 요약

| 만들 기능 | 먼저 필요한 것 | 이유 |
|---|---|---|
| 맵 선택 UI | 범용 상호작용, 동적 씬 이동 요청 | UI 버튼이 실제 목적지와 SpawnPoint를 전달해야 함 |
| 귀환 포탈 | 동적 씬 이동, 귀환 SpawnPoint | 원래 씬의 정확한 위치로 돌아가야 함 |
| 루팅 | ItemDatabase, 인벤토리 이동, 런타임 세션 | 획득물의 소유권을 씬 전환 후에도 추적해야 함 |
| 생환 성공 | RaidSession, 루팅 상태 | 어떤 획득물을 기지 상태에 반영할지 알아야 함 |
| 전투 | 입력, Health, Damage 계약, 시험 표적 | AI 없이 공격과 피격을 분리 검증해야 함 |
| 적 AI | 전투 계약, 고정 맵 이동 방식 | AI가 검증된 공격과 피해 API를 사용해야 함 |
| 사망 실패 | Health와 적 공격, RaidSession | 사망한 원정의 상태를 한 번만 종료해야 함 |
| 기본 아이템 세이브 | Stage 2 또는 3의 안정된 런타임 아이템 상태 | 실제 상태 모델이 있어야 직렬화 필드를 정할 수 있음 |
| 생환·사망 결과 세이브 | 성공·실패 반영 규칙 | 결과 규칙 전에 만들면 저장 형식 변경이 반복됨 |
| 도심 회색상자 공간 생성 | 안정된 직접 씬 이동, SpawnPoint, 런타임 NavMesh | 공간 배치와 Player 수명주기를 분리 검증해야 함 |
| 완전한 절차 생성 레이드 | 도심 외 맵별 규칙, 루팅, 전투, AI, RaidSession | 생성된 공간과 게임 규칙의 책임을 함께 검증해야 함 |

---

## 5. Stage 0: Unity 기준선 안정화

### 목표

다음 기능의 문제와 기존 프로젝트 문제를 구분할 수 있는 기준선을 만든다.

### 선행조건

없음. 모든 후속 단계의 공통 선행 작업이다.

### Unity 구현 및 점검 항목

1. GameMap1에서 플레이어 이동, 카메라, 인벤토리, 상자 상호작용 기준을 기록한다.
2. Player의 비활성 Missing Script가 무엇이었는지 확인한다.
3. 원본을 찾을 수 없고 사용하지 않는 컴포넌트임이 확인되면 안전하게 제거한다.
4. GameMap1과 GameMapTest가 Build Settings에 포함되어 있는지 유지한다.
5. 현재 Console Error 0 상태를 기준선으로 유지한다.
6. 기존 인벤토리 드래그, 닫기, 상자 간 이동이 회귀하지 않는지 확인한다.

### 완료 기준

- Play Mode에서 GameMap1의 현재 기능이 정상 작동한다.
- 새 컴파일 오류가 없다.
- Missing Script 처리 여부와 근거가 기록되어 있다.
- 씬이 의도하지 않게 dirty 상태로 남지 않는다.
- 다음 단계에서 사용할 GameMapTest가 열리고 저장 가능한 상태다.

### 다음 단계가 의존하는 이유

Player와 씬을 복제하거나 프리팹화한 뒤 Missing Script를 발견하면 모든 게임플레이 씬을 다시 수정해야 한다.

---

## 6. Stage 1: 맵 선택과 왕복 이동

이 단계는 GameMap1을 Editor에서 직접 실행해 기능을 검증한다. InitialLoadingScene, MainMenuScene, GameLoadingScene과 해당 Manager는 사용하거나 수정하지 않는다. 제품 시작 흐름 통합은 후속 작업이다.

**구현 상태: 2026-08-20 완료.** GameMap1과 GameMapTest 직접 왕복 3회, GameMapTest 직접 실행 후 귀환, 기존 Chest 열기와 닫기 회귀를 Play Mode에서 확인했다.

### 최종 동작

    GameMap1의 맵 선택 오브젝트 앞에서 상호작용
    → 맵 선택 UI 열기
    → GameMapTest 선택
    → GameMapTest의 지정 SpawnPoint로 이동
    → 귀환 포탈 앞에서 상호작용
    → GameMap1의 지정 ReturnSpawnPoint로 복귀

### 이 단계의 임시 기본값

- 맵 선택 오브젝트와 귀환 포탈은 MeshRenderer와 Collider가 있는 디자인 없는 불투명 Cube를 사용한다. 최종 모델, 텍스처, 애니메이션, VFX는 만들지 않는다.
- **[현재 적용]** 기존 GameMapTest를 첫 원정 맵으로 재사용한다.
- 현재 프로젝트가 사용하는 E 입력을 임시로 유지한다.
- 귀환 포탈은 이 단계에서는 단순 왕복 이동이다. 생환 보상 확정은 Stage 3 이후에 붙인다.
- **[현재 완료]** 씬 사이의 플레이어와 인벤토리 상태는 PersistentGameplayShell의 동일 InventoryUIManager와 인벤토리 객체가 유지한다.

이 기본값은 최종 기획을 확정하는 것이 아니라 기능 검증을 위한 임시 규칙이다.

### Stage 1-1. 범용 상호작용 경계

#### 선행조건

- 현재 InventoryUIManager의 E 입력과 Chest 감지 위치 확인
- 기존 Chest 열기 동작의 기준선 확보

#### Unity 구현물

- Player 쪽의 단일 상호작용 입력 소유자
- 대상이 구현하는 최소 상호작용 계약
- 상호작용 가능 거리와 현재 대상 판정
- 기존 Chest를 새 입력 경로에 연결하는 어댑터 또는 변경
- UI가 열린 동안 Player 상호작용과 이동 입력이 실행되지 않게 하는 단일한 최소 입력 잠금 상태

권장 책임:

| 책임 | 소유자 |
|---|---|
| E 입력을 한 번 읽음 | Player 상호작용 컴포넌트 |
| 가까운 대상 판정 | Player 상호작용 컴포넌트 |
| 상호작용 실행 | 각 대상 컴포넌트 |
| 인벤토리 UI 열기와 닫기 | InventoryUIManager |
| 맵 선택 UI 열기 | 맵 선택 오브젝트 |
| 씬 이동 요청 | 씬 이동 시스템 |

#### 완료 기준

- 한 번의 입력에 한 대상만 반응한다.
- 상자 앞에서는 기존 상자 UI가 열린다.
- Chest, 맵 선택 Cube, 귀환 Cube가 각자의 범위에서 한 대상씩만 반응한다.
- 거리 밖에서는 반응하지 않는다.
- UI가 열린 상태에서 게임 입력이 중복 처리되지 않는다.
- E 입력과 Chest 대상 선택은 새 Player 상호작용 경로 한 곳에서만 처리한다.
- 새 경로 검증 후 InventoryUIManager에 남은 기존 E 입력과 Chest 감지 코드를 제거한다.
- InventoryUIManager는 상자 UI를 열고 닫는 API와 화면 상태만 소유한다.

### Stage 1-2. 게임플레이 맵 사이의 직접 씬 이동

#### 선행조건

- GameMap1과 GameMapTest가 Build Settings에 포함됨
- MainMenuScene과 GameLoadingScene을 이번 프로토타입 범위에서 제외함

#### Unity 구현물

- GameMap1과 GameMapTest에서만 사용하는 단일 직접 씬 이동 요청
- `SceneManager.LoadSceneAsync`를 사용하는 목적지 게임플레이 씬 직접 로드
- 목적지 씬 이름과 SpawnPoint ID
- 씬 언로드 뒤에도 요청을 유지하는 단 하나의 일회성 컨텍스트
- 중복 로드 요청 방지
- 목적지 씬이 Player를 SpawnPoint에 배치한 뒤 요청을 한 번만 소비하고 정리
- 잘못된 씬 또는 SpawnPoint가 지정되었을 때 명확한 오류
- GameMapTest를 Editor에서 직접 실행하면 GameplayShellBootstrap이 shell을 생성하고 SceneSpawnController가 defaultSpawnId=RaidEntry로 persistent Player를 배치하는 fallback
- MainMenu, GameLoading 관련 씬과 스크립트, Build Settings는 변경하지 않음

이 단계에서는 SceneManager 호출이 여러 클래스에 흩어지지 않게 한다.

**[현재 적용]** Stage 1 이동 요청은 SubsystemRegistration에서 초기화되는 작은 정적 런타임 컨텍스트다. 별도 영속 MonoBehaviour Manager를 만들지 않았으며, 일회성 요청은 목적지 씬의 SceneSpawnController가 `sceneLoaded`와 `Start` 경로에서 안전하게 한 번만 소비한다.

#### 완료 기준

- GameMap1에서 GameMapTest로 직접 이동하며 GameLoadingScene은 활성화되지 않는다.
- GameMapTest에서 GameMap1로 직접 이동하며 GameLoadingScene은 활성화되지 않는다.
- 빠르게 여러 번 입력해도 씬 로드가 중복되지 않는다.
- 목적지가 없을 때 무한 로딩이나 NullReferenceException이 발생하지 않는다.
- GameMapTest를 Editor에서 바로 실행해도 같은 PersistentGameplayShell이 생성되고 RaidEntry에 배치되어 이동, 인벤토리와 귀환을 시험할 수 있다.
- MainMenu, GameLoading 관련 파일과 EditorBuildSettings가 변경되지 않는다.

### Stage 1-3. PersistentGameplayShell과 SpawnPoint

#### 선행조건

- GameMap1의 Player, 외형, 카메라와 UI 참조 확인
- persistent root 밖의 씬 오브젝트 참조가 남지 않는지 확인

#### Unity 구현물

- 실제 Player, 외형, Player 스크립트, Camera, Inventory UI와 EventSystem을 포함하는 PersistentGameplayShell 프리팹 하나
- 두 씬에 GameplayShellBootstrap 하나씩 배치
- 각 씬에는 SceneSpawnController와 SpawnPoint만 배치
- GameMap1의 BaseEntry와 BaseReturn SpawnPoint, GameMapTest의 RaidEntry SpawnPoint
- 어느 씬에도 scene-local 런타임 Player, gameplay Camera, Inventory UI 또는 EventSystem 복사본을 두지 않음. 편집 전용 `EditorOnly` Preview Camera는 런타임 셸과 분리된 예외다.
- 씬 전환 전 인벤토리, 드래그와 컨테이너 팝업을 닫고 이동·상호작용 입력을 잠그는 처리

#### 완료 기준

- 두 씬 모두에서 같은 Player의 이동과 같은 Camera의 추적이 정상이다.
- 지정 SpawnPoint에 persistent Player가 배치되고 Rigidbody 속도가 초기화된다.
- 왕복 중 shell, Player, Camera, InventoryUIManager, StandardCore와 EventSystem의 instance ID가 바뀌지 않는다.
- Play Mode의 어느 씬에서도 Player, 활성 gameplay Camera, AudioListener, EventSystem과 입력 처리기가 중복되지 않는다. 편집 전용 Preview Camera는 Play 중 비활성이다.
- 잘못된 SpawnPoint로 도착하지 못하면 이동 요청과 입력 잠금을 해제하고 명확한 오류를 남긴다.

### Stage 1-4. 맵 선택 UI

#### 선행조건

- 범용 상호작용
- 동적 씬 이동 요청
- GameMapTest SpawnPoint

#### Unity 구현물

- 불투명 Cube MeshRenderer와 이동을 막는 Collider
- 맵 선택 오브젝트용 상호작용 컴포넌트
- 맵 표시 이름
- 목적지 씬 정보
- 목적지 SpawnPoint 정보
- 현재는 GameMapTest 하나를 보여 주는 최소 선택 UI
- 선택 버튼과 취소 동작
- 선택 UI가 열린 동안 이동, 다른 상호작용, 인벤토리 입력을 막는 처리

첫 맵 하나만을 위해 해금, 난이도, 추천 장비, 미리보기, 보상 배율까지 만들지 않는다. 여러 맵이 필요해질 때 MapDefinition을 확장한다.

#### 완료 기준

- 선택 Cube가 Game View 또는 Scene View에서 불투명하게 보인다.
- 맵 선택 오브젝트 범위에서 UI를 열 수 있다.
- GameMapTest 항목이 한 번만 표시된다.
- 취소 버튼 또는 Escape로 취소하면 씬 이동 없이 UI가 닫히고 입력 잠금이 복원된다.
- 선택하면 지정된 목적지로 이동한다.
- UI를 반복해서 열고 닫아도 버튼 이벤트가 중복되지 않는다.

### Stage 1-5. 귀환 포탈

#### 선행조건

- GameMapTest 플레이어 셸
- 동적 씬 이동
- GameMap1 ReturnSpawnPoint

#### Unity 구현물

- 불투명 Cube MeshRenderer와 이동을 막는 Collider
- GameMapTest의 귀환 포탈 오브젝트
- 귀환 포탈용 상호작용 컴포넌트
- 범용 상호작용 경로를 사용하는 포탈 컴포넌트
- Inspector에서 GameMap1과 ReturnSpawnPoint를 고정 목적지로 설정한 이동 요청

출발 씬을 기억하는 동적 귀환 경로는 아직 만들지 않는다. 해당 책임은 Stage 2의 RaidSession에서 다룬다.

#### 완료 기준

- 귀환 Cube가 Game View 또는 Scene View에서 불투명하게 보인다.
- 포탈 범위 밖에서는 작동하지 않는다.
- 포탈 상호작용 시 GameMap1의 지정 위치로 돌아온다.
- 맵 선택과 귀환을 3회 반복해도 오브젝트와 이벤트가 중복되지 않는다.
- GameMap1의 기존 인벤토리와 Chest 열기/닫기에 회귀가 없다.
- GameMapTest에서도 같은 persistent Player와 Inventory UI를 사용하며 I 입력으로 동일 인벤토리를 확인할 수 있다.
- 새 Console 오류가 없다.

### Stage 1에서 하지 않는 것

- InitialLoadingScene, MainMenuScene, GameLoadingScene과 관련 Manager 변경
- 기존 시작 흐름 또는 로딩 UI 통합
- 최종 맵 선택 장치와 포탈 디자인
- 디스크 저장
- 원정 아이템 유지
- 루팅 보상 확정
- 탈출 카운트다운
- 결과 화면
- 전투와 적
- 랜덤 맵
- 맵 해금과 난이도

### Stage 1이 다음 기능에 필요한 이유

루팅, 적, 탈출 결과는 모두 플레이어가 원정 씬에 들어가고 다시 나오는 경로가 안정되어야 검증할 수 있다.

---

## 7. Stage 2: 메모리 기반 게임 상태와 RaidSession

### Stage 2-A: PersistentGameplayShell의 동일 인스턴스 유지 **[완료]**

파일 저장 없이, 게임플레이 씬이 바뀌어도 실제 플레이어 셸 전체를 같은 인스턴스로 유지한다.

#### 구현된 Unity 구조

- PersistentGameplayShell 프리팹은 Player와 외형, Player 스크립트, Camera, Inventory UI/StandardCore/View, EventSystem을 포함한다.
- GameMap1과 GameMapTest의 GameplayShellBootstrap은 shell이 없을 때만 같은 프리팹을 한 번 생성한다.
- shell 루트는 DontDestroyOnLoad이므로 왕복 동안 Player와 포함된 모든 컴포넌트가 같은 인스턴스다.
- InventoryUIManager, StandardStashViewData와 EquipmentLoadoutData도 같은 객체이므로 별도 snapshot이나 새 UI 재바인딩 없이 현재 인벤토리·장비가 그대로 유지된다.
- DirectSceneTravel은 이동 전에 열린 인벤토리, 드래그와 컨테이너 팝업을 정리하고 이동·인벤토리·상호작용 입력을 잠근다.
- 목적지 SceneSpawnController는 같은 Player를 SpawnPoint로 옮기고 Rigidbody 속도를 초기화한 뒤 입력 상태를 복원한다.
- 이 구조는 Play Mode 메모리 유지이며 디스크 save 구조가 아니다.

#### 현재 유지되는 것과 씬별로 바뀌는 것

- Player GameObject와 전체 외형 계층
- Player에 연결된 실제 MonoBehaviour와 런타임 필드
- Camera와 CameraFollow 대상
- InventoryUIManager, StandardCore, 인벤토리·장비 View, EventSystem과 PlayerInventoryState 객체 그래프
- 아이템 위치, 회전, 장비 슬롯, 같은 definition ID의 여러 런타임 객체, 단일 소유권과 컨테이너 내부 관계
- Player의 위치와 Rigidbody 속도는 목적지 씬의 SpawnPoint 규칙에 따라 바뀐다.
- 현재 Chest와 상호작용 대상, 열린 패널, 드래그와 팝업은 씬 전환 직전에 정리한다.

같은 실행 중에는 각 InventoryItemData 객체 자체가 개별 물건을 구분한다. 현재 디스크 저장의 recordId는 파일 내부 부모 관계 키일 뿐 영구 instance ID가 아니다. 영구 instance ID와 원정 스냅샷·사망 롤백 식별 방식은 여전히 별도 결정한다.

#### 검증 결과 — 2026-08-20

- GameMap1 → GameMapTest → GameMap1 왕복을 3회 수행했다.
- shell, Player, InventoryUIManager, Camera, EventSystem과 StandardCore의 instance ID가 모든 왕복에서 동일했다.
- 테스트 맵에서도 Player 외형 계층 165개와 SkinnedMeshRenderer 10개가 유지됐다.
- 테스트 맵과 귀환한 기본 맵에서 같은 InventoryUIManager가 활성·입력 가능 상태였고 동일 인벤토리 패널이 열렸다.
- 매 도착 시 Player는 RaidEntry 또는 BaseReturn SpawnPoint에 배치됐고 Player, Camera, AudioListener, EventSystem, InventoryUIManager는 각각 1개였다.
- GameMapTest를 Editor에서 직접 실행해도 같은 프리팹 셸이 한 번 생성되고 RaidEntry에 배치되며 인벤토리 패널이 열렸다.
- Player에 있던 비활성 Missing Script는 원본 파일이 없어 제거했으며, 실제 연결된 Player 컴포넌트 수와 외형은 보존했다.
- 검증 왕복에서 새 Error, Exception, Assert는 발생하지 않았다.

### Stage 2-B: RaidSession과 원정 경계 **[후속]**

PersistentGameplayShell은 현재 플레이 중 실제 Player 상태를 유지할 뿐, 원정의 성공·실패와 소유권 규칙을 결정하지 않는다. 다음 하위 단계에서만 아래를 구현한다.

- 현재 원정 한 개를 나타내는 RaidSession
- 원정 시작, 진행, 종료 상태와 중복 생성·종료 방지
- 출발 씬, 원정 씬, 목적 SpawnPoint와 귀환 SpawnPoint
- 원정 진입 시점 스냅샷이 실제로 필요한지와 사망 롤백 정책
- 획득 출처 provenance가 실제 결과 규칙에 필요한지 확인
- **[미정]** 원정 밖 아이템 소유 주체를 현재 Player 인벤토리, 별도 보관함, 또는 다른 구조 중에서 결정
- **[미정]** 귀환 포탈이 단순 이동인지 즉시 생환 성공인지 결정

### 다음 단계가 의존하는 이유

루팅 아이템의 소유권과 생환 결과를 판정하려면 어느 원정에서 어떤 아이템이 이동했는지 추적할 주체가 필요하다.

---

## 8. Stage 3: 저장 없는 루팅과 생환

### 목표

고정 상자에서 아이템을 하나 획득하고 귀환했을 때, 같은 실행 세션의 생환 결과 목록에 한 번만 반영되게 한다.

### 선행조건

- Stage 2 RaidSession
- ItemDatabase ID 조회
- 기존 인벤토리 드래그와 컨테이너 이동
- 범용 상호작용
- **[미정]** Stage 1의 귀환 포탈을 생환 성공 오브젝트로 확장할지, 단순 이동으로 남기고 별도 탈출 오브젝트를 둘지 결정

### Unity 구현물

- GameMapTest의 루팅 컨테이너 1개
- 기존 DB 아이템 ID를 사용하는 고정 시험 내용물
- Stage 1에서 만든 상호작용 경계를 재사용하는 원정 컨테이너 연결
- 플레이어 인벤토리로 옮긴 획득물 추적
- 사용자에게 확정받은 탈출 오브젝트가 RaidSession의 생환 결과를 한 번만 확정
- 획득물을 RaidSession의 extractedItems에서 선택된 영속 런타임 상태 소유자의 임시 결과 목록으로 한 번만 전달
- 시험 상자 내용은 각 RaidSession에서 정확히 한 번만 초기화

### 완료 기준

- 상자를 열고 아이템을 플레이어 인벤토리로 옮길 수 있다.
- 드래그 취소, 닫기, 다시 열기가 정상이다.
- 사용자가 확정한 생환 오브젝트로 원정을 종료하면 획득물이 선택된 영속 런타임 상태 소유자의 임시 생환 결과 목록에 존재한다.
- 같은 귀환을 중복 처리해 아이템이 두 번 지급되지 않는다.
- 다시 출격해도 이전 상자 상태와 새 원정 상태가 섞이지 않는다.
- 게임 재실행 후 유지되는 것은 이 단계의 완료 조건이 아니다.

실제 원정 밖 소유 상태에 대한 병합, 출격 전 소지품 유지, 사망 손실 규칙은 Stage 6에서 사용자 규칙을 확정한 뒤 적용한다.

### 후속 기능이 의존하는 이유

- Stage 4 전투는 같은 원정 씬과 RaidSession 생명주기 안에서 실행되므로, 씬 재입장과 상태 초기화가 먼저 안정되어야 한다.
- 향후 세이브 형식은 실제로 검증된 아이템 위치, 회전, 소유권, 컨테이너 관계를 바탕으로 만들어야 한다.

---

## 9. Stage 4: 플레이어 전투 기반

### 목표

AI 없이 플레이어 공격, 피해, 체력, 사망 계약을 검증한다.

### 선행조건

- 원정 씬의 Player 생명주기와 입력이 안정됨
- **[미정]** 조준 방식
- **[미정]** 공격 입력
- **[미정]** Hitscan 또는 Projectile
- **[미정]** 첫 무기의 최소 동작

### Unity 구현물

- 피해를 받는 대상의 최소 계약
- Health와 사망 처리
- 플레이어의 시험용 공격
- 피격 가능한 더미 표적
- 공격 대상 레이어와 충돌 규칙
- 필요할 때만 ItemDefinition과 무기 전용 데이터의 연결

처음부터 탄약, 부품, 내구도, 방어구, 반동을 모두 만들지 않는다. 고정 시험 공격으로 전투 흐름을 먼저 검증한 뒤 아이템 데이터에 필요한 필드만 추가한다.

현재 단일 Weapon 슬롯은 인벤토리 소유권과 저장을 검증하는 장비 상태일 뿐이다. 이를 플레이어 공격의 실제 무기 선택 권한으로 사용할지, 총기 3D 모델과 장착·사격 애니메이션을 언제 연결할지는 Stage 4에서 별도로 결정한다.

### 완료 기준

- 입력 한 번에 의도한 공격 한 번이 실행된다.
- 더미 표적만 정확히 피해를 받는다.
- 체력 0에서 사망 처리가 한 번만 실행된다.
- 씬 재입장 시 이전 더미와 공격 상태가 남지 않는다.
- Stage 4에서 장비 연동을 승인한 경우에만 Weapon 슬롯의 definition ID와 실제 공격 구현 연결을 검증한다.

### 다음 단계가 의존하는 이유

적 AI는 검증된 이동, 피해, 공격 API를 호출해야 한다. 전투와 AI를 동시에 만들면 피격 실패의 원인을 구분하기 어렵다.

---

## 10. Stage 5: 최소 적 AI와 플레이어 사망

### 목표

고정 원정 맵에 실제 위협 하나를 추가한다.

### 선행조건

- Stage 4 전투 계약
- GameMapTest의 이동과 충돌
- **[미정]** 첫 적의 공격 방식
- **[미정]** 감지 방식과 최소 행동 범위

### Unity 구현물

- EnemyDefinition의 최소 데이터
- 고정 EnemySpawnPoint
- 프로젝트에 적합한 이동 방식
- 최소 인식, 추적, 공격, 사망 상태
- Player Health에 피해를 주는 공격
- Player 사망 시 RaidSession에 실패 후보를 알리는 경계

Unity AI Navigation 패키지는 설치되어 있지만 실제 게임플레이 사용은 확인되지 않았다. NavMesh를 사용할 경우 GameMapTest에서 베이크, 장애물, 재입장 동작을 먼저 검증한다.

### 완료 기준

- 적이 플레이어를 감지하고 접근한다.
- 공격 거리에서 검증된 전투 API로 피해를 준다.
- 플레이어와 적이 각각 사망할 수 있다.
- 재입장 시 이전 적 상태가 남지 않는다.
- 적 AI 오류와 전투 오류를 별도로 재현할 수 있다.

### 다음 단계가 의존하는 이유

사망 실패 루프는 실제 Player 사망 신호가 있어야 검증할 수 있다.

---

## 11. Stage 6: 메모리 안에서 최소 레이드 루프 완성

### 목표

게임을 종료하지 않은 상태에서 생환과 사망 두 결과가 모두 정확히 처리되게 한다.

### 선행조건

- 맵 왕복
- RaidSession
- 루팅
- 전투
- 최소 적 AI
- **[미정]** 생환 시 반영할 아이템 범위
- **[미정]** 사망 시 잃을 아이템 범위

### Unity 구현물

- 원정 상태를 한 번만 종료하는 결과 처리
- 생환 성공 처리
- Player 사망 실패 처리
- 사용자가 선택한 원정 밖 런타임 소유 상태에 대한 반영 또는 롤백
- 최소 결과 UI
- 결과 확인 후 GameMap1 복귀

### 완료 기준

성공 경로:

    원정 진입
    → 상자 아이템 획득
    → 귀환
    → 성공 결과
    → 정해진 아이템이 기지 상태에 반영

실패 경로:

    원정 진입
    → 아이템 획득 또는 전투
    → Player 사망
    → 실패 결과
    → 사용자 확정 규칙대로 메모리 상태 반영

공통 완료 기준:

- 결과가 두 번 처리되지 않는다.
- 아이템이 중복 지급 또는 중복 삭제되지 않는다.
- 다시 출격하면 새 RaidSession이 생성된다.
- 성공과 실패 경로를 각각 3회 반복해도 이전 상태가 섞이지 않는다.

### 다음 단계가 의존하는 이유

저장은 이미 완성된 런타임 결과를 파일에 기록하는 역할이어야 한다. 저장 코드가 게임 규칙을 대신 결정하면 안 된다.

---

## 12. Stage 7: 세이브와 로드 확장 — 기초 프로토타입 이후

### 목표

현재 단일 슬롯 프로토타입이 저장하는 플레이어 인벤토리·장비에 더해, Stage 6에서 검증된 원정 결과와 기지 상태를 게임 재실행 후 복원한다.

사용자 결정으로 기본 플레이어 아이템 상태의 단일 슬롯 저장을 앞당겨 구현했다. 이 Stage의 남은 범위는 생환·사망 결과, stable ID가 확정된 기지 상태와 최종 저장 정책의 확장이다.

### 선행조건

- 선택된 영속 런타임 상태 소유자와 RaidSession의 책임 확정
- 아이템 인스턴스 상태 확정
- 생환과 사망 결과까지 저장 범위에 포함하는 경우 해당 반영 규칙 확정
- 숫자 ItemDefinition ID가 안정됨
- **[현재 프로토타입]** 저장 슬롯 1개와 `.bak` 복구
- **[미정]** 최종 저장 슬롯 수
- **[미정]** 자동 저장 시점
- **[미정]** 강제 종료 정책
- **[현재 프로토타입]** primary 전체 의미 검증 실패 시 `.bak` 후보 검증
- **[미정]** 최종 손상 파일 복구와 백업 정책

### Unity 구현물

- Unity Object와 분리된 Save DTO
- 저장 버전
- 사용자가 선택한 원정 밖 아이템 소유 컨테이너 상태
- ItemDefinition ID
- 파일 내부 관계용 recordId와 별도로, 실제 필요가 확정될 경우 영구 아이템 instance ID
- 위치, 회전, 컨테이너 관계
- 필요한 개별 상태
- 존재하지 않는 ID 처리
- ItemDatabase의 중복 definition ID 검증
- 저장 데이터 안의 중복 recordId 및 소유 위치 검증
- 저장과 로드를 호출하는 단일 소유자

저장하지 않는 프리셋 정보:

- 아이템 이름
- 설명
- 아이콘
- 인벤토리 크기
- 고정 능력치

이 정보는 로드할 때 ItemDatabase에서 ID로 다시 조회한다.

### 권장 저장 시점

- 기지 상태가 확정되었을 때
- 생환 또는 사망 결과 처리가 끝났을 때
- 명시적으로 게임을 종료할 때

초기 버전에서는 진행 중인 원정의 적 위치, 상자 열린 상태, 탄피나 투사체를 저장하지 않는다.

### 완료 기준

- 아이템 배치 후 종료하고 다시 실행해 동일하게 복원된다.
- 회전과 컨테이너 내부 아이템이 복원된다.
- 생환 결과와 사망 결과가 재실행 후 유지된다.
- 잘못된 ItemDefinition ID가 침묵하지 않고 명확히 처리된다.
- 같은 저장을 여러 번 불러도 아이템이 중복되지 않는다.
- 저장 버전이 다른 경우의 처리 정책이 테스트된다.

### 다음 단계가 의존하는 이유

맵 해금, 상점, 제작, 진행도는 안정된 영속 상태가 있어야 의미가 있다.

---

## 13. Stage 8: 여러 고정 맵과 데이터 기반 확장

### 목표

코드 복사 없이 두 번째 고정 원정 맵과 새로운 데이터 항목을 추가할 수 있게 한다.

### 선행조건

- Stage 7까지의 최소 레이드 루프
- 첫 고정 맵에서 이동, 루팅, 전투, AI, 결과, 저장이 모두 검증됨

### Unity 구현물

- MapDefinition의 실제 필요 필드 확정
- 맵 표시 이름, 씬, SpawnPoint, 귀환 정보
- 맵 선택 UI가 정의 목록을 표시
- 맵별 고정 LootSpawnPoint와 EnemySpawnPoint
- 필요할 때 LootTable과 EnemyDefinition 확장
- Build Settings의 씬 누락을 잡는 Editor 검증

### 완료 기준

- 두 번째 고정 맵을 데이터와 씬 설정으로 추가할 수 있다.
- 맵 선택 UI 코드를 복사하지 않는다.
- 새 맵에서도 기존 레이드 완료 기준이 통과한다.
- 한 맵의 설정이 다른 맵에 섞이지 않는다.

---

## 14. Stage 9: 랜덤 맵, 난이도, 콘텐츠 확장

이 단계부터는 서로 독립적인 기능으로 나누어 진행한다.

### 14.1 맵 유형별 절차 생성

#### 현재 구현: 도심형 회색상자

- `GameMapTest` 씬 경계와 기존 `RaidEntry`, `ReturnPortal`, 적 시험 오브젝트는 유지한다.
- scene-local `ProceduralUrbanMapGenerator`가 한 번의 씬 수명 동안 seed와 불변 layout 원본을 소유한다. 생성된 Ground, 도로, 건물, 경계와 NavMesh는 이 layout에서 다시 만들 수 있는 파생 표현이다.
- 먼저 가변 간격 교차점과 연결 도로 그래프를 만든다. 주 도로를 보존하고, 보조 도로는 전체 연결성이 유지될 때만 일부 제거한다.
- 도로 배치 뒤 남은 필지에 충돌 가능한 큐브 건물을 놓는다. 도로, `RaidEntry`, 기존 귀환 포탈 위치와 보호 대상 주변은 건물로 막지 않는다.
- 전체 도심 루트는 약 35~55도 회전하고, 블록 수·간격·교차점 흔들림·건물 밀도와 높이를 seed로 바꿔 정사각 청크 반복감을 줄인다.
- 기존 귀환 포탈은 재생성하지 않고 같은 scene object를 반대편 도로 노드로 이동한다.
- 런타임 NavMesh는 생성 geometry의 콜라이더만 수집하고 `RaidEntry → ReturnPortal 접근점`의 complete path를 생성 직후 검증한다.

설계 참고:

- [Parish·Müller, Procedural Modeling of Cities](https://cgl.ethz.ch/Downloads/Publications/Papers/2001/p_Par01.pdf)의 `road map → allotment → building` 단계 분리를 현재 프로토타입의 `도로 그래프 → 필지 → 큐브 건물` 순서에 적용했다.
- [Chen et al., Interactive Procedural Street Modeling](https://www.peterwonka.net/Publications/pdfs/2008.SG.Chen.InteractiveProceduralStreetModeling.pdf)의 전역 방향과 국소 제약·noise를 함께 쓰는 관점을 주 도로, 교차점 흔들림과 연결성 제약으로 단순화했다.
- [Unity AI Navigation](https://docs.unity3d.com/Manual/com.unity.ai.navigation.html)의 런타임 NavMesh 지원을 사용하되, layout을 원본으로 두고 NavMesh는 다시 만들 수 있는 파생 데이터로만 취급한다.

#### 현재 제외 범위

- 랜드마크, 가로수, 폐차, 쓰레기통, 자전거와 기타 지형지물
- 건물 내부, 문, 층, 파괴와 실제 건축 프리팹 교체 규칙
- 상자, 전리품, 적 spawn, 엄폐 후보와 AI 순찰 지점
- 난이도 예산, 생환 조건, seed의 세이브·로드

#### 다른 맵 유형

- 지하 던전과 오염 지역은 도심 생성기의 enum 또는 옵션 분기로 추가하지 않는다.
- 각 유형은 연결 방식, 이동 가능 면, 시야, 방 구조와 환경 위험이 확정될 때 별도의 layout planner와 runtime generator를 설계한다.
- 공통으로 재사용할 수 있는 것은 seed 전달, 검증 결과와 SpawnPoint/NavMesh 계약뿐이며, 도심의 도로·필지 규칙을 강제로 공유하지 않는다.

#### 후속 검증 순서

1. 도심 생성 수치와 seed 재현 정책 확정
2. 실제 건축 프리팹 교체 경계
3. LootSpawnPoint와 EnemySpawnPoint 후보 데이터
4. ExtractionPoint와 RaidSession 연결
5. 맵 유형별 별도 planner

### 14.2 난이도와 보상

선행조건:

- 여러 아이템과 적 데이터
- 실제 플레이에서 위험과 보상을 비교할 수 있음

난이도 수치를 맵 생성 전에 확정하지 않는다. 적 수, 적 능력치, 루팅 가치, 탈출 조건 중 어떤 축을 사용할지 플레이 테스트로 결정한다.

### 14.3 콘텐츠

- 무기와 탄약
- 방어구와 가방
- 회복 아이템
- 귀중품과 재료
- 적 종류
- 상자 종류
- 상점, 제작, 퀘스트

콘텐츠 수량을 먼저 늘리지 않는다. 데이터 한 개를 추가했을 때 기존 레이드 루프 전체가 작동하는지가 우선이다.

---

## 15. Stage 10: 설정, 최종 UI, 아트, 사운드, 최적화

다음 요소는 핵심 루프가 안정된 후 진행한다.

- 해상도, 전체화면, 볼륨, 키 설정
- 최종 HUD와 결과 화면
- 캐릭터와 장비 외형
- 환경 아트, 이펙트, 사운드
- 로딩 연출
- 접근성
- 프로파일링 기반 최적화
- 배포 플랫폼별 빌드 검증

임시 UI와 임시 오브젝트를 사용하는 동안에도 Collider 크기, 이동 가능한 통로, 카메라 시야 등 실제 플레이 규격은 단계별 테스트에서 기록한다.

---

## 16. Unity 폴더와 자산 운영 원칙

현재 프로젝트 전체를 새 폴더 구조로 강제 이동하지 않는다. 새 기능만 책임별로 추가한다.

권장 추가 위치:

    Assets/Scripts/Interaction
    Assets/Scripts/SceneFlow
    Assets/Scripts/Raid
    Assets/Scripts/Combat
    Assets/Scripts/AI
    Assets/Scripts/Save
    Assets/GameData/Items
    Assets/GameData/Maps
    Assets/Prefabs/Gameplay
    Assets/Prefabs/Interaction
    Assets/Scenes

원칙:

- 외부 인벤토리 에셋 코드는 필요한 호환 수정 외에는 프로젝트 게임 규칙을 넣지 않는다.
- 프로젝트 게임 로직은 Assets/Scripts 아래에서 소유한다.
- 씬에 직접 복제한 설정은 가능하면 공통 프리팹으로 묶는다.
- 프리팹을 만들기 전 기존 씬 참조와 Missing Script를 확인한다.
- ScriptableObject ID는 배포 후 재사용하지 않는다.
- Library와 PackageCache는 직접 수정하지 않는다.
- 씬과 프리팹을 저장한 뒤 의도하지 않은 대량 직렬화 변경이 없는지 확인한다.

---

## 17. 단계 공통 검증 기준

모든 Stage는 다음 기준을 공통으로 만족해야 한다.

### 정적 검증

- 새 스크립트의 모든 사용처 확인
- public API와 serialized field 변경 확인
- Missing Reference 확인
- 새 ScriptableObject와 프리팹의 Meta 파일 확인
- 기존 외부 에셋 코드와 프로젝트 코드의 책임 분리 확인

### Unity 컴파일

- Unity Editor 컴파일 성공
- 새 Error, Exception, Assert 없음
- 기존 Warning과 새 Warning 구분

### Play Mode

- 정상 경로
- 취소 또는 거리 이탈
- 빠른 반복 입력
- 씬 재입장
- 기능을 최소 3회 반복
- Player, Camera, EventSystem, UI, 세션 중복 없음
- 기존 인벤토리 드래그와 닫기 회귀 없음

### 씬과 프리팹

- 변경한 씬만 dirty 상태가 됨
- 저장 후 Missing Reference 없음
- 프리팹 Override가 의도한 것인지 확인
- Build Settings에 필요한 씬이 포함됨

### 빌드 검증

각 Stage의 마지막에는 가능하면 Windows 타깃 빌드 또는 최소한 해당 씬의 Play Mode 왕복을 검증한다. Editor에서만 작동하는 API에 런타임 코드가 의존하지 않는지 확인한다.

---

## 18. 바로 다음 작업 목록

Stage 1 구현 결과는 다음과 같다.

1. **[완료]** Player의 비활성 Missing Script 조사: 원본 파일과 GUID가 없어 프리팹 저장을 막는 무효 컴포넌트만 제거하고 실제 Player 컴포넌트는 보존
2. **[완료]** GameMap1의 E 입력과 Chest 상호작용을 범용 PlayerInteractor 경계로 분리
3. **[완료]** MainMenu와 GameLoading을 건드리지 않는 GameMap1 ↔ GameMapTest 직접 목적지 기반 로더 구현
4. **[완료]** GameMap1에 BaseReturn SpawnPoint와 불투명 Cube 맵 선택 오브젝트 배치
5. **[완료]** 두 씬에 GameplayShellBootstrap과 scene-local SceneSpawnController/SpawnPoint를 배치하고 실제 Player, Camera, UI, EventSystem은 PersistentGameplayShell 프리팹 하나로 통합
6. **[완료]** GameMap1에 GameMapTest 하나와 취소를 제공하는 최소 선택 UI 구성
7. **[완료]** GameMapTest에 불투명 Cube 귀환 포탈 배치
8. **[완료]** GameMap1과 GameMapTest 왕복 3회 및 GameMapTest 직접 실행 후 귀환 검증
9. **[완료]** Console 새 오류 0과 기존 Chest 열기/닫기 회귀 확인

Stage 2-A의 PersistentGameplayShell 동일 인스턴스 유지와 플레이어 아이템 상태(인벤토리·빈 상태로 시작하는 12칸 장비 구조와 시험용 단일 Weapon 호환 정의)의 단일 슬롯 세이브/로드 프로토타입은 구현되었다. 이동 시험용 적 프로토타입도 별도 하위 작업으로 존재한다. 사용자의 우선순위 변경으로 `GameMapTest`의 도심형 도로·큐브 건물 생성은 별도 기술 스파이크로 구현되었다. 다음 핵심 게임 규칙 작업은 여전히 Stage 2-B에서 RaidSession의 정확한 경계와 원정 밖 아이템 소유 주체, 귀환 포탈의 의미를 결정하는 것이다. 레이드 결과 저장, 루팅, 전투, 사망 규칙, 도심 장식·내부·spawn과 다른 맵 유형은 아직 구현하지 않는다.

---

## 19. 결정 대기 목록

다음 항목은 필요한 Stage가 시작될 때 사용자와 확정한다.

| 결정 | 필요한 시점 |
|---|---|
| **[결정 완료]** 기존 GameMapTest를 최소 원정 시험 씬으로 재사용 | Stage 1 |
| 최종 상호작용 키와 입력 리매핑 | 입력 설정 또는 Stage 1 확장 |
| 원정 밖 아이템 소유 주체: 현재 인벤토리, 별도 보관함, 기타 | Stage 2 |
| 귀환 포탈이 즉시 생환인지, 조건부 탈출인지 | Stage 3 |
| **[결정 완료]** 왕복 중 실제 Player, 외형, Player 스크립트, Camera, Inventory UI/EventSystem과 인벤토리 객체를 같은 shell 인스턴스로 유지 | Stage 2-A |
| 영구 아이템 instance ID와 저장용 식별 방식 | 저장 또는 원정 스냅샷 단계 |
| 생환 시 반영할 아이템 | Stage 3 또는 6 |
| 공격, 조준, 발사 방식 | Stage 4 |
| 첫 적의 이동과 공격 방식 | Stage 5 |
| 사망 시 손실 규칙 | Stage 6 |
| 최종 저장 슬롯, 자동 저장, 백업, 강제 종료 정책(현재 프로토타입은 1슬롯+.bak) | Stage 7 |
| 맵 ID와 해금 규칙 | Stage 8 |
| **[결정 완료]** 도심형 맵은 연결 도로를 먼저 만들고 큐브 건물을 후배치 | 도심 생성 기술 스파이크 |
| **[결정 완료]** 지하 던전과 오염 지역은 도심과 별도 생성 규칙 사용 | 각 맵 유형 설계 시점 |
| 도심 seed의 저장·재현·공유 정책 | RaidSession 또는 Stage 9 확장 |

---

## 20. AI 또는 Codex 작업 요청 규칙

AI에게는 Stage 전체가 아니라 검증 가능한 하위 단위를 요청한다.

좋은 작업 단위:

- Stage 1-1만 진행: 기존 Chest 동작을 유지하면서 E 입력을 범용 상호작용 컴포넌트로 분리하고 Play Mode에서 검증
- Stage 1-2만 진행: GameMap1과 GameMapTest 사이에서만 작동하는 직접 씬 이동을 구현하고 MainMenu/GameLoading 관련 파일이 바뀌지 않았는지 검증
- GameMapTest에 SpawnPoint와 귀환 포탈만 추가하고 PersistentGameplayShell의 GameMap1 왕복을 검증
- Stage 2-B만 진행: PersistentGameplayShell과 책임이 겹치지 않는 RaidSession 경계와 중복 종료 방지를 구현
- 고정 더미 표적에 대한 Health와 Damage 계약만 구현

모든 요청에 포함할 항목:

1. 이번에 구현할 Stage와 하위 단계
2. 변경해도 되는 씬과 파일
3. 이번 단계에서 만들지 않을 기능
4. Play Mode 완료 기준
5. 사용자 결정이 필요한 항목

AI가 하지 말아야 할 것:

- 사용자 확인 없이 게임 규칙과 수치를 확정
- 현재 Stage와 무관한 Manager, 데이터베이스, 이벤트 시스템 추가
- 프로젝트 전체 폴더 재편
- 기존 씬과 프리팹 대량 저장
- 저장 구조가 정해지기 전에 문자열 또는 숫자 ID 규칙 변경
- 고정 씬 왕복과 Player 수명주기가 검증되기 전에 절차 생성부터 구현
- 전투 계약이 없는데 적 AI부터 구현

---

## 21. 현재 보류 범위

사용자가 우선순위를 변경하지 않는 한 다음 기능은 최소 레이드 루프의 선행조건으로 취급하지 않는다.

- 멀티플레이
- 지하·오염 지역까지 포함한 다중 맵 생성과 대규모 랜덤 월드
- 복잡한 난이도 예산
- 상점과 경제
- 제작
- 퀘스트와 NPC 대화
- 복잡한 총기 부품
- 세분화된 탄약과 방어구 등급
- 부위별 상처와 생존 수치
- 대규모 아이템, 적, 맵 콘텐츠
- 최종 아트, VFX, 사운드

---

## 22. 핵심 결론

현재 프로젝트의 다음 목표는 세이브, 전투, AI를 동시에 만드는 것이 아니다.

    기존 인벤토리 동작 기준선 확보
    → 범용 상호작용
    → MainMenu와 GameLoading을 건드리지 않는 GameMap1 ↔ GameMapTest 직접 씬 이동
    → PersistentGameplayShell과 두 씬의 Bootstrap 및 SpawnPoint 구성
    → 맵 선택 UI
    → 귀환 포탈
    → 반복 왕복 검증

PersistentGameplayShell의 같은 Player, Camera, InventoryUIManager, EventSystem과 PlayerInventoryState 유지는 완료되었고, 기초 PlayerItemState 저장은 이미 앞당겨졌다. 그 다음에는 실제 플레이 상태와 책임이 겹치지 않는 RaidSession을 만들고 저장 없는 루팅을 붙인다. 전투와 AI를 거쳐 생환·사망 규칙이 메모리 안에서 완성되면 현재 저장 프로토타입에 레이드 결과와 기지 상태만 확장한다.

도심형 도로·큐브 건물 생성은 이 순서와 별개로 공간 제작 위험을 먼저 확인한 기술 스파이크다. 현재 결과는 GameMapTest의 파생 공간만 바꾸며 Player 셸, 아이템 상태와 씬 이동의 권위 소유자를 바꾸지 않는다. 후속 랜드마크·내부·spawn 또는 다른 맵 유형은 각각 별도 요청과 검증 계약을 가진다.

이 순서를 지키면 Unity 씬 수명주기, 입력, 인벤토리 상태, 전투, AI, 저장 버그가 한꺼번에 섞이지 않으며, 각 단계가 실제 플레이 가능한 결과로 남는다.
