# 게임 한 판 호출·분기 지도

**마지막 갱신:** 2026-09-01
**역할:** 현재 코드에서 실제로 실행되는 씬 전환, 사용자 분기와 권위 상태 변경의 단일 순서표

이 문서는 기획 백로그가 아니다. 시작·메뉴·씬 전환·원정·정산 코드를 바꾸기 전에 관련 구간을 읽고, 호출 순서가 달라졌으면 코드와 이 문서를 같은 작업에서 함께 고친다.

## 1. 전체 한 바퀴

```text
InitialLoadingScene
  → MainMenuScene
    → New/Load 저장 슬롯 1~3 선택
      → GameLoadingScene
      → GameMap1 (Base)
        → GameMapTest (Raid)
          ├─ 생환·사망·포기 후 GameMap1 → 다음 원정
          └─ Active 저장 후 주 메뉴 → 같은 슬롯 이어하기
```

Build Settings의 활성 순서는 `InitialLoadingScene`, `MainMenuScene`, `GameLoadingScene`, `GameMap1`, `GameMapTest`다. 최초 실행의 앞 세 씬과 `GameMap1 ↔ GameMapTest` 직접 이동은 서로 다른 전환 경계다.

## 2. 실행과 주 메뉴 분기

```text
[InitialLoadingScene]
InitialLoadingManager.Start
  → LoadMainMenuAsync
  → SceneManager.LoadSceneAsync("MainMenuScene")

[MainMenuScene]
MainMenuManager.Awake
  → GameUserSettings.Apply
  → 3개 슬롯 행 초기화
```

| 사용자 선택 | 실제 호출과 결과 |
|---|---|
| 새로 시작 | `StartNewGame → 슬롯 선택`; 선택 슬롯에 ordinary/Recovery 자료가 있으면 교체 확인, 아니면 `QueueNewGame(slot) → GameLoadingScene` |
| 게임 로드 | `OpenLoadPanel → 슬롯 선택`; 선택 슬롯만 primary 우선·backup 대체 검증하고 일반 Load 또는 Recovery 판정으로 분기 |
| 설정 | `OpenSettingsPanel → KeyBindingSettingsPanel.Refresh`; Sound와 키 override는 `GameUserSettings`, `MainMenuScene` 유지 |
| 나가기 | `OpenExitPanel → QuitGame → Application.Quit`; Editor에서는 종료 대신 로그 |
| 중단 원정 이어하기 | 선택 슬롯의 `ResumeInterruptedRaid → QueueResumeRaid(slot) → GameLoadingScene`; Base 상태를 먼저 적용한 뒤 같은 seed의 Raid로 직접 이동 |
| 중단 원정 실패 처리 | 선택 슬롯의 `FailInterruptedRaid → 실패 결정을 durable하게 기록 → QueueRaidRecoverySettlement/QueueOrphanedRaidFailure(slot) → GameLoadingScene` |

ordinary와 Recovery는 슬롯별 namespace를 공유하며 런타임 권위는 `PersistentGameplayShell.ActiveSaveSlotIndex` 하나다. 원정 표식 판단도 선택 슬롯 안에서만 수행한다. 선택 슬롯의 save와 backup이 모두 검증 실패하면 그 슬롯을 불러오지 않고 주 메뉴에 남으며, 다른 슬롯이나 손상 자료를 임의 초기화하지 않는다. 슬롯 1은 기존 저장 경로와 호환되고 슬롯 2·3은 별도 경로를 쓴다.

메인 메뉴와 `GameplayEscapeMenuController.OpenSettings`는 같은 키 설정 prefab을 쓰되 각 화면 수명에 맞는 인스턴스를 가진다. 재바인딩 중 Escape는 키 변경 취소를 먼저 소비하고 설정 화면을 유지하며, Base pause/Raid non-pause 정책은 기존 Escape 소유자가 계속 적용한다. 게임 내 개발용 환경 시험은 `OpenEnvironmentTest → SetPhase(Day/Night)` 또는 `SetWeather(Clear/Rain) → BackToMainMenuPanel`이며, 시간과 날씨는 독립 축이다. 낮/밤을 고르는 동안만 자동 시간을 멈추고 패널 이탈 때 이전 자동 진행 상태를 복원한다. Base에서는 세계 pause를 유지하되 환경 시험 화면에 보이는 날씨 전환·구름·비 표현만 unscaled preview time으로 진행한다.

## 3. 공통 로딩과 기지 진입

```text
[GameLoadingScene]
GameLoadingManager.Start
  → LoadGameMapAsync
  → SceneManager.LoadSceneAsync("GameMap1")

[GameMap1]
GameplayShellBootstrap.Awake [-11000]
  → Editor gameplay 씬 직접 Play이고 GameStartRequest 없음
      → ordinary save와 Recovery를 같은 고유 임시 저장 루트로 격리
  → 기존 PersistentGameplayShell 유지 또는 prefab 한 번 생성
SceneSpawnController.Start [-9000]
  → TryPlacePlayer("BaseEntry")
  → 같은 PlayerMovement.TryTeleport로 Controller 상태를 보존하며 배치
  → RaidSession.TryEnterScene(Base)
BasePersistenceController.Start [+1000]
  → GameStartRequest.TryConsume (정확히 한 번)
  → 요청의 slot을 ActiveSaveSlotIndex로 선택
  → New/Load/Recovery 상태 적용
  → 기지 가구·상인 binding
  → RaidCheckpointController.NotifyBasePersistenceReady
  → CompleteStartActionAfterBaseBinding
      ├─ ResumeRaid → TryBeginRecoveredRaid → TryBeginRecoveredTravel → DirectSceneTravel
      ├─ SettleRaidRecovery → ResetHealth → TryCompleteMenuRecoverySettlementAtBase
      └─ SettleOrphanedRaid → ResetHealth → SaveActiveSlot(true); 실패하면 F5 재시도
```

`GameLoadingManager`는 로딩 화면과 `GameMap1` 로드만 소유한다. New/Load/Recovery 데이터는 `BasePersistenceController`가 소비하며, Player 오브젝트를 교체하지 않는다.

Editor에서 `GameMap1`·`GameMapTest`를 직접 Play하면 메인메뉴 요청이 없으므로 실제 `persistentDataPath`를 읽거나 쓰지 않고 Play Session 전용 임시 루트를 사용한다. 이전 실제 원정 표식과 Recovery가 빠른 기능 시험을 막지 않으며, 메인메뉴·최초 로딩에서 시작한 정상 흐름은 실제 저장 경로와 기존 복구 판정을 그대로 사용한다.

## 4. 기지에서 원정 출발

```text
E 입력
  → PlayerInteractor.TryInteract
  → MapTerminalInteractable.Interact
  → MapSelectionOverlay.Show
맵 선택
  → MapSelectionOverlay.SelectConfiguredMap
  → RaidSession.TryBeginRaid("GameMapTest", "RaidEntry")
  → RaidCheckpointController.TryPrepareNewRaid
      1. 현재 Player·기지 exact baseline 캡처
      2. ordinary save에 raidInProgress 표식
      3. Recovery baseline 생성
  → RaidSession.BeginRaidTravel (Inactive → Entering)
  → DirectSceneTravel.TryLoad
  → PersistentGameplayShell.PrepareForTravel
      → 진행 행동 취소 + 새 행동 차단
  → GameplaySceneTransitionFader.TryCover
  → 검은 화면이 완전히 덮인 뒤 LoadSceneAsync("GameMapTest")
```

출발 전 저장 준비나 전환 시작이 실패하면 Raid에 들어가지 않는다. Fresh 출발 표식은 exact `FreshDepartureRollback` 거래로 원정 전 상태에 되돌리고, 정리가 끝나지 않으면 tracked 상태와 재시도 경계를 유지한다.

기지 바닥 아이템은 `GameMap1` scene이 수명을 소유하므로 출발 전까지는 남지만 `GameMapTest` 로드 때 함께 제거된다. ordinary save나 persistent shell로 승격하지 않는다.

## 5. Raid 맵 도착 판정

### 5.1 Unity 생명주기 순서

```text
GameplayShellBootstrap.Awake              [-11000]
RaidCheckpointSceneBinding.Awake          [-10500]
  → spawn catalog의 prefab·stable ID 계약 검증
  → generator의 layout-geometry 완료 통지 구독
  → Resume이면 저장된 seed를 generator에 먼저 적용
ProceduralUrbanMapGenerator.Awake         [-10000]
  → layout·선택한 표현의 geometry 생성(등각: .2m포장/Collider·2층외관·지상층실내)
  → LayoutGeometryGenerated 동기 통지
      → seed + stable ID의 spawn manifest 생성
      → manifest 최종 pose에 prefab 생성 후 scene-local runtime registry 원자 등록
ProceduralUrbanMapGenerator.Start         [-10000]
  → NavMesh build와 Entry→Portal 경로 판정
SceneSpawnController.Start                [ -9000]
  → manifest의 Chest 접근점·Enemy 위치까지 개별 NavMesh 경로 확인
  → 최종 Raid 도착 gate
```

Raid의 `SceneManager.sceneLoaded` 호출은 아무것도 확정하지 않고 반환하며 위 순서의 `Start`만 `Ready/Invalid`를 판정한다. Generator `Start` 뒤에도 `Pending`이면 안전하지 않은 도착으로 보아 Invalid와 같은 복귀/보류 경계로 보낸다. 실행 순서 숫자보다 `RaidCheckpointSceneBinding.GetArrivalReadiness` 결과가 권위다.

현재 `GameMapTest`의 고정 scene object는 ReturnPortal이며, spawn catalog가 시험 Chest 1·근접 적 1·원거리 적 1을 생성한다. 이 세 entry는 빠른 시험용 현재 구성일 뿐, 시스템이 종류별 오브젝트를 정확히 하나로 제한한다는 규칙이 아니다.

### 5.2 Ready 성공

```text
GetArrivalReadiness == Ready
  → 같은 Player를 RaidEntry에 배치 + Rigidbody 속도 0
  → RaidSession.TryEnterScene(Raid)              (Entering → Active)
  → RaidCheckpointController.TryCompleteRaidSceneArrival
      → readiness 재확인
      ├─ Fresh: LootTable이 지정된 Chest·시체 후보 grid를 seed+stable ID로 1회 생성해 전부 검증 후 원자 적용
      └─ Resume: LootTable을 굴리지 않고 저장된 world/Player·Chest·Enemy·바닥 아이템 복원
      → 첫 live Active checkpoint 생성
  → DirectSceneTravel.CompleteArrival            (pending token 소비)
  → PersistentGameplayShell.FinishArrival        (fade-in 뒤 이동·인벤토리·상호작용·행동 허용 상태 복원)
  → RaidSession.CompleteSceneArrival(Raid)        (피해 차단 마지막 해제)
```

`Ready` 전에는 Player 이동, Raid Active 전이, checkpoint 캡처, pending 완료, fade 공개와 입력 복원을 하지 않는다. Spawn manifest가 없거나 후보 부족·접근 불가이면 layout 경로가 정상이어도 `Invalid`다.

도착 restore/첫 checkpoint가 실패하면 실패 결정을 먼저 durable하게 시도한 뒤 화면을 열고 `ResolveCheckpointArrivalFailure → RecoveryFailed`로만 전이한다.

### 5.3 Invalid 실패

| 진입 종류 | 같은 검은 전환 안에서의 순서 |
|---|---|
| Fresh 원정 | `TryPrepareInvalidMapReturn → exact FreshDepartureRollback journal → RaidSession Returning/Outcome=None → TryRedirectPendingArrival(GameMap1)`; 기지에서 ordinary mirror와 Recovery 정리를 끝내며 게임플레이 실패 통지는 발생시키지 않음 |
| Resume 원정 | 저장된 seed를 재굴림하지 않음 → `TryMakeRecoveryFailureDurable → Outcome=RecoveryFailed → TryRedirectPendingArrival(GameMap1)`; 새 실패 기록 쓰기가 실패해도 기존 ordinary 원정 표식·고정 seed를 유지하고 기지 정산에서 재시도하며, 정산 뒤 `SettlementCommitted(RecoveryFailed)` |
| Fresh exact rollback 확보 실패, owner/config 누락 또는 Base redirect 시작 실패 | 현재 pending token, 검은 화면과 입력 잠금을 보류한다. 현재 실행은 계속하지 않고 재시작하며, ordinary 원정 표식과 durable Recovery 자료로 판정한다. |
| Base는 로드됐지만 도착 구성 실패 | `HandleInvalidMapReturnTravelCompleted(false) → Resolved`; Fresh의 `Outcome=None`도 기술 오류 결과창을 열어 기지 재시도·주 메뉴 이동을 제공한다. |
| `GameMapTest` 직접 Play 시작 | 자동 기지 이동은 하지 않고 Player gameplay 입력·피해를 잠근 채 오류를 표시한다. |

거부된 `GameMapTest`에서는 `CompleteArrival`이나 `CancelTravelPreparation`을 호출하지 않는다. `CompleteArrival`은 최종 목적지에서 한 번만 호출한다.

## 6. Raid 플레이와 결과 분기

Raid가 `Active`인 동안 `RaidCheckpointController.Update → TryCaptureAndWrite(Active)`가 저빈도 Recovery checkpoint를 갱신한다. 결과는 모두 `RaidSession.Resolve` 한 곳으로 수렴하고, `RaidCheckpointController.HandleRaidResolved`가 terminal checkpoint와 settlement journal을 확보한다.

Recovery의 `layoutHash` 필드는 현재 도로·건물 layout과 spawn manifest를 합친 world hash다. Resume은 같은 seed로 stable prefab을 만든 뒤 Enemy·Chest와 scene-local 바닥 아이템의 stable ID·Transform·실제 grid를 적용한다. LootTable은 Fresh에서만 실행하므로 재개방·Resume 재굴림 경로가 없다. 이전 layout-only hash는 legacy migration으로 한 번 허용하고, 복원 직후 첫 live checkpoint에서 combined world hash로 교체한다.

| 결과 | 진입 호출 | 다음 분기 |
|---|---|---|
| 생환 | `ReturnPortalInteractable.Interact → TryResolveExtractionAndReturn → Resolve(Extracted) → TryReturnToBase` | 기존 0.2초 암전 → 자동 `GameMap1` 로드 → 정산 완료 뒤 `확인` |
| Player 사망 | `PlayerStats.Died → RaidSession.HandlePlayerDied → Resolve(PlayerDied)` | 결과 UI의 기지 복귀 또는 주 메뉴 |
| 원정 포기→기지 | Escape 확인 → `TryResolveAbandonment → Resolve(Abandoned) → TryReturnToBase` | `GameMap1` |
| Active Raid 저장→주 메뉴 | Escape 확인 → `TrySaveActiveRaidForMainMenu → Active Recovery exact 기록 → 같은 persistent snapshot을 active ordinary slot에 mirror → GameplaySessionExit` | 결과를 확정하지 않고 `MainMenuScene`; 같은 슬롯에서 이어하기/실패 처리 |
| Recovery 기록 실패 | `HandleCheckpointWriteFailure → Resolve/TryOverride...(RecoveryFailed)` | 기지 정산 또는 주 메뉴 실패 처리 |

## 7. 기지 귀환과 원자적 정산

정상 생환은 Raid 안에서 기지/주 메뉴 선택창을 열지 않는다. E 입력에서 `Extracted`와 피해 차단을 먼저 확정하고 기존 gameplay fade가 화면을 덮은 뒤 자동으로 기지를 로드한다.

```text
RaidSession.TryReturnToBase              (Resolved → Returning)
  → DirectSceneTravel.TryLoad("GameMap1", "BaseReturn")
  → 검은 화면 뒤 GameMap1 로드
  → SceneSpawnController.TryPlacePlayer
  → RaidSession.TryEnterScene(Base)       (pendingBaseSettlement 설정)

BasePersistenceController.Start
  → NotifyBasePersistenceReady --------┐
fade-in 완료                            ├─ 둘 다 참일 때만 TryFinalizeTrackedRaidAtBase
  → CompleteSceneArrival(Base)          │
  → ConfirmBaseSettlement -------------┘
      → TryCommitTrackedRaidAtBase
          1. settlement 입력 잠금
          2. exact journal 검증/재사용
          3. ordinary save mirror
          4. Recovery 파일 정리
          5. ResetTrackedRaid
          6. 실제 원정 결과만 SettlementCommitted
```

두 기지 gate의 도착 순서는 상관없고 둘 다 필요하다. 정상 생환 UI는 완전 암전 뒤 정산 진행 화면을 표시하고, ordinary mirror와 Recovery 정리가 끝나 `SettlementCommitted`가 발생한 뒤에만 `확인` 하나를 연다. 실패하면 주 메뉴를 열지 않고 `정산 재시도`만 제공한다. Fresh invalid-map rollback은 기술적 출발 취소이므로 `SettlementCommitted`와 실패 통계·퀘스트 진행을 발생시키지 않는다.

현재 포탈 E는 즉시 생환 확정하는 시험 규칙이다. 최종 탈출 대기 시간, 피격 시 중단 여부와 암전 중 사망 판정은 아직 디자인 미정이다.

## 8. 주 메뉴로 돌아가기

기지의 `RequestMainMenu`는 `BasePersistenceController.SaveActiveSlot`이 성공한 뒤에만 아래 종료 경로를 시작한다. 저장 기능이 준비되지 않았거나 저장에 실패하면 사유를 표시하고 paused 기지에 남는다.

Active Raid의 `RequestMainMenu`는 포기와 별도다. 먼저 world item을 포함한 Active Recovery exact checkpoint를 기록하고, 그 checkpoint의 persistent state를 같은 active ordinary slot primary/backup에 mirror한 뒤에만 종료한다. 저장 실패 시 원정에 남고, 성공해도 `Abandoned`나 정산을 만들지 않는다. Raid 바닥 item GameObject는 씬 종료로 사라지지만 같은 슬롯 Resume에서 Recovery record로 다시 만든다.

```text
GameplaySessionExit.TryExitToMainMenu
  → PersistentGameplayShell.PrepareForTravel
      → 진행 행동 취소 + 새 행동 차단
  → 검은 화면 cover
  → LoadSceneAsync("MainMenuScene")
  → CompleteExit
      → GameManager.EndGameplaySession
      → PersistentGameplayShell.EndGameplaySession
      → Time.timeScale 복원 + 설정 적용
```

게임플레이 씬끼리 이동할 때는 이 경로를 쓰지 않는다. 반대로 주 메뉴 이동에서는 persistent gameplay owner를 반드시 정리한다.

## 9. 순서 불변조건

1. Raid readiness `Ready` 전에는 Player 배치, `Active`, checkpoint, arrival 완료, 화면 공개를 하지 않는다.
2. Fresh exact rollback과 Resume `RecoveryFailed` 정산을 섞지 않고, cleanup 실패만으로 tracked 상태를 지우지 않는다.
3. 기지 정산은 `BasePersistenceReady`와 `BaseArrivalComplete` 뒤에만 실행한다.
4. 최초 로딩과 gameplay 직접 전환을 섞지 않으며 `GameMap1 ↔ GameMapTest`는 같은 shell·Player를 유지한다.
5. 정상 생환의 `Resolved`부터 `SettlementCommitted`까지 주 메뉴 종료 경로를 노출하지 않는다.
6. `PrepareForTravel`은 진행 행동을 취소하고 새 행동을 막으며, 도착·전환 취소에서 이전 허용 상태만 복원한다.
7. Base와 Active Raid의 주 메뉴 이동은 active slot ordinary 저장 성공 뒤에만 gameplay owner 종료를 시작한다.
8. 바닥 item은 scene 소유다. 일반 씬 전환에는 운반하지 않고 Active Raid Resume에서만 같은 슬롯 Recovery로 재구성한다.
