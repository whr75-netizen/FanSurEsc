# 게임 한 판 호출·분기 지도

**마지막 갱신:** 2026-08-27
**역할:** 현재 코드에서 실제로 실행되는 씬 전환, 사용자 분기와 권위 상태 변경의 단일 순서표

이 문서는 기획 백로그가 아니다. 시작·메뉴·씬 전환·원정·정산 코드를 바꾸기 전에 관련 구간을 읽고, 호출 순서가 달라졌으면 코드와 이 문서를 같은 작업에서 함께 고친다.

## 1. 전체 한 바퀴

```text
InitialLoadingScene
  → MainMenuScene
    → GameLoadingScene
      → GameMap1 (Base)
        → GameMapTest (Raid)
          ├─ 생환·사망·포기 후 GameMap1 → 다음 원정
          └─ 주 메뉴 이동 → MainMenuScene
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
  → InitializeRaidRecoveryView (ordinary save의 원정 표식을 먼저 판정)
```

| 사용자 선택 | 실제 호출과 결과 |
|---|---|
| 새로 시작 | `StartNewGame → GameStartRequest.QueueNewGame → LoadScene("GameLoadingScene")` |
| 게임 로드 | `OpenLoadPanel → TrySelectLoadCandidate(primary 우선, backup 대체) → LoadSelectedGame → QueueLoad → GameLoadingScene` |
| 설정 | `OpenSettingsPanel → SetSoundEnabled`; `MainMenuScene` 유지 |
| 나가기 | `OpenExitPanel → QuitGame → Application.Quit`; Editor에서는 종료 대신 로그 |
| 중단 원정 이어하기 | `ResumeInterruptedRaid → QueueResumeRaid → GameLoadingScene`; Base 상태를 먼저 적용한 뒤 같은 seed의 Raid로 직접 이동 |
| 중단 원정 실패 처리 | `FailInterruptedRaid → 실패 결정을 durable하게 기록 → QueueRaidRecoverySettlement/QueueOrphanedRaidFailure → GameLoadingScene` |

원정 표식이 미정산 상태면 `BlockNormalStartForRaidRecovery`가 새로 시작과 일반 로드를 막는다. 세이브와 backup이 모두 검증 실패하면 주 메뉴에 남고, 손상 상태를 임의 초기화하지 않는다.

## 3. 공통 로딩과 기지 진입

```text
[GameLoadingScene]
GameLoadingManager.Start
  → LoadGameMapAsync
  → SceneManager.LoadSceneAsync("GameMap1")

[GameMap1]
GameplayShellBootstrap.Awake [-11000]
  → 기존 PersistentGameplayShell 유지 또는 prefab 한 번 생성
SceneSpawnController.Start [-9000]
  → TryPlacePlayer("BaseEntry")
  → 같은 Player 배치
  → RaidSession.TryEnterScene(Base)
BasePersistenceController.Start [+1000]
  → GameStartRequest.TryConsume (정확히 한 번)
  → New/Load/Recovery 상태 적용
  → 기지 가구·상인 binding
  → RaidCheckpointController.NotifyBasePersistenceReady
  → CompleteStartActionAfterBaseBinding
      ├─ ResumeRaid → TryBeginRecoveredRaid → TryBeginRecoveredTravel → DirectSceneTravel
      ├─ SettleRaidRecovery → ResetHealth → TryCompleteMenuRecoverySettlementAtBase
      └─ SettleOrphanedRaid → ResetHealth → SaveSlotOne(true); 실패하면 F5 재시도
```

`GameLoadingManager`는 로딩 화면과 `GameMap1` 로드만 소유한다. New/Load/Recovery 데이터는 `BasePersistenceController`가 소비하며, Player 오브젝트를 교체하지 않는다.

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
  → GameplaySceneTransitionFader.TryCover
  → 검은 화면이 완전히 덮인 뒤 LoadSceneAsync("GameMapTest")
```

출발 전 저장 준비나 전환 시작이 실패하면 Raid에 들어가지 않는다. Fresh 출발 표식은 exact `FreshDepartureRollback` 거래로 원정 전 상태에 되돌리고, 정리가 끝나지 않으면 tracked 상태와 재시도 경계를 유지한다.

## 5. Raid 맵 도착 판정

### 5.1 Unity 생명주기 순서

```text
GameplayShellBootstrap.Awake              [-11000]
RaidCheckpointSceneBinding.Awake          [-10500]
  → binding 등록
  → Resume이면 저장된 seed를 generator에 먼저 적용
ProceduralUrbanMapGenerator.Awake/Start   [-10000]
  → layout 생성
  → Start에서 NavMesh build와 Entry→Portal 경로 판정
SceneSpawnController.Start                [ -9000]
  → 최종 Raid 도착 gate
```

Raid의 `SceneManager.sceneLoaded` 호출은 아무것도 확정하지 않고 반환하며 위 순서의 `Start`만 `Ready/Invalid`를 판정한다. Generator `Start` 뒤에도 `Pending`이면 안전하지 않은 도착으로 보아 Invalid와 같은 복귀/보류 경계로 보낸다. 실행 순서 숫자보다 `RaidCheckpointSceneBinding.GetArrivalReadiness` 결과가 권위다.

### 5.2 Ready 성공

```text
GetArrivalReadiness == Ready
  → 같은 Player를 RaidEntry에 배치 + Rigidbody 속도 0
  → RaidSession.TryEnterScene(Raid)              (Entering → Active)
  → RaidCheckpointController.TryCompleteRaidSceneArrival
      → readiness 재확인
      → Resume이면 world/Player 복원
      → Fresh/Resume 모두 첫 live Active checkpoint 생성
  → DirectSceneTravel.CompleteArrival            (pending token 소비)
  → PersistentGameplayShell.FinishArrival        (fade-in 뒤 이동·인벤토리·상호작용 복원)
  → RaidSession.CompleteSceneArrival(Raid)        (피해 차단 마지막 해제)
```

`Ready` 전에는 Player 이동, Raid Active 전이, checkpoint 캡처, pending 완료, fade 공개와 입력 복원을 하지 않는다.

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

| 결과 | 진입 호출 | 다음 분기 |
|---|---|---|
| 생환 | `ReturnPortalInteractable.Interact → TryResolveExtraction → Resolve(Extracted)` | 결과 UI의 기지 복귀 → `TryReturnToBase` |
| Player 사망 | `PlayerStats.Died → RaidSession.HandlePlayerDied → Resolve(PlayerDied)` | 결과 UI의 기지 복귀 또는 주 메뉴 |
| 원정 포기→기지 | Escape 확인 → `TryResolveAbandonment → Resolve(Abandoned) → TryReturnToBase` | `GameMap1` |
| 원정 포기→주 메뉴 | Escape 확인 → `TryResolveAbandonment → GameplaySessionExit.TryExitToMainMenu` | `MainMenuScene`; 다음 메뉴 진입에서 terminal 원정 정산을 먼저 처리 |
| Recovery 기록 실패 | `HandleCheckpointWriteFailure → Resolve/TryOverride...(RecoveryFailed)` | 기지 정산 또는 주 메뉴 실패 처리 |

## 7. 기지 귀환과 원자적 정산

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

두 기지 gate의 도착 순서는 상관없고 둘 다 필요하다. ordinary mirror나 Recovery 정리가 실패하면 tracked 상태와 입력 잠금을 유지하고 기존 F5 경계에서 같은 exact 거래를 재시도한다. Fresh invalid-map rollback은 기술적 출발 취소이므로 `SettlementCommitted`와 실패 통계·퀘스트 진행을 발생시키지 않는다.

## 8. 주 메뉴로 돌아가기

```text
GameplaySessionExit.TryExitToMainMenu
  → PersistentGameplayShell.PrepareForTravel
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
