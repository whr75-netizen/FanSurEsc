# Unity 개발 진행 기록

**마지막 확인:** 2026-08-20
**확인 환경:** Unity 6000.5.9f1, 활성 Build Target `StandaloneWindows64`, `GameMap1`/`GameMapTest`; Windows Development Player build 성공
**문서 역할:** 다음 작업에서 현재 구현을 빠르게 이어가기 위한 진행형 인계 문서다. 전체 게임 방향과 Stage 의존성은 `extraction_survival_game_design_dev_plan.md`를 따른다.

## 문서 사용 규칙

- `[Play Mode 확인]`: 실제 Play Mode 프레임·씬 수명주기에서 확인했다.
- `[Play Mode 호출 확인]`: Play Mode에서 런타임 호출 경로로 확인했으며 실제 키 입력은 우회했다.
- `[코드/씬 확인]`: 코드, 씬 또는 프리팹의 현재 구성을 확인했다.
- `[코드 확인]`: 실행 경로는 확인했지만 해당 경계를 새로 Play Mode 검증하지 않았다.
- `[사용자 요구]`: 사용자가 원하는 동작으로 직접 설명했다.
- `[사용자 확인 필요]`: 사용자의 설명이 현재 구현 설명인지, 앞으로 구현할 확정 요구인지 한 번 더 확인해야 한다.
- `[미구현]`: 현재 코드에 없다.
- `[후속 후보]`: 자동 구현 대상이 아니며 사용자가 요청한 경우에만 진행한다.
- `스크립트_사용_분석.md`는 persistent gameplay shell 도입 전의 역사적 기록이다. 현재 Player·Camera·UI 위치의 근거로 사용하지 않는다.

---

## 1. 현재 완료된 기반

- `[Play Mode 확인]` `GameMap1`의 맵 선택 Cube에서 `GameMapTest`로 직접 이동하고, 귀환 Cube에서 `GameMap1`로 직접 복귀한다.
- `[Play Mode 확인]` 이 직접 왕복은 `MainMenuScene`과 `GameLoadingScene`을 거치지 않는다.
- `[Play Mode 확인]` `PersistentGameplayShell` 하나가 실제 Player, 외형, Player 구성 스크립트, Camera, Inventory UI/Core/View와 EventSystem을 같은 인스턴스로 유지한다.
- `[코드/씬 확인]` 두 게임플레이 씬에는 scene-local 런타임 Player/gameplay Camera/Inventory UI/EventSystem 복사본이 없다. 편집 상태 Game View용 `EditorOnly` Preview Camera만 씬마다 1개 존재한다.
- `[Play Mode 확인]` Player 인벤토리는 왕복 중 동일 객체 그래프로 유지된다. 기지에서 사용하는 단일 슬롯 디스크 세이브/로드 프로토타입도 연결되어 있다.
- `[코드/씬 확인]` 현재 연결된 상호작용 대상은 `GameMap1`의 Chest 2개와 맵 선택 Cube 1개, `GameMapTest`의 귀환 Cube 1개다.
- `[Play Mode 확인]` Freya 인간형 외형은 Humanoid Avatar와 Idle/Walk/Run 로코모션에 연결되어 더 이상 T포즈로 서 있지 않는다.
- `[코드/씬 확인]` 이동 중 Left Shift 또는 Right Shift를 누르면 걷기 속도의 정확히 1.3배로 달리는 설정이 `PersistentGameplayShell`의 기존 `PlayerMovement`에 연결되어 있다.

---

## 2. 사용자가 설명한 상호작용 계약

아래는 다음 기능에서 지향할 동작을 정리한 것이다. 현재 구현과 다른 항목은 4장에 따로 표시한다.

1. `[사용자 요구]` Player가 상호작용 오브젝트의 범위에 들어가면 `[E]` 안내가 활성화된다.
2. `[사용자 요구]` Chest처럼 지속 UI가 있는 상호작용 중에도 Player는 움직일 수 있다.
3. `[사용자 요구]` 활성 상호작용 오브젝트의 허용 거리에서 벗어나면 해당 오브젝트와 연결된 UI가 자동으로 닫힌다.
4. `[사용자 요구]` 주변에 대상이 여러 개면 거리상 가장 가까운 하나만 E 입력 대상이 된다.
5. `[사용자 확인 필요]` 이미 지속 상호작용 중이라면 그 세션의 대상은 해당 오브젝트로 유지된다.
6. `[사용자 확인 필요]` 유지 중인 세션의 거리 판정도 처음 상호작용한 그 오브젝트를 기준으로 한다.
7. `[사용자 요구]` Chest, Portal, Map Terminal 같은 개별 기능은 공통 상호작용 진입 경로를 재사용하고, 각 대상은 자신의 실제 행동만 구현한다.

주의: 5번의 “활성 대상 유지”는 현재 공통 코드에 완전히 구현되어 있지 않다. 이것을 확정 요구사항으로 구현하기 전에는 사용자에게 한 번 더 확인한다.

---

## 3. 현재 공통 상호작용 구조

```text
Persistent Player
  └─ PlayerInteractor
       ├─ 매 프레임 주변 Collider 검색
       ├─ 가장 가까운 Interactable 하나 선택
       ├─ [E] 디버그 안내 표시
       └─ E 입력 시 선택된 Interactable.Interact 호출

Interactable (abstract base class)
  ├─ ChestInteractable
  ├─ MapTerminalInteractable
  └─ ReturnPortalInteractable
```

현재 코드에는 `IInteractable` 인터페이스가 없으며, 공통 계약은 `abstract class Interactable`이다.

| 책임 | 현재 소유자 | 재사용 여부 |
|---|---|---|
| E 입력 | `PlayerInteractor` | 모든 현재 대상이 공유 |
| 주변 대상 검색과 가장 가까운 하나 선택 | `PlayerInteractor` | 모든 현재 대상이 공유 |
| 기본 활성 상태 검사 | `Interactable.CanInteract` | 모든 현재 대상이 공유 |
| 안내 문구 | 각 `Interactable.InteractionPrompt` | 표시 방식은 공통, 문구는 개별 |
| Chest UI 열기/닫기 | `ChestInteractable` → `InventoryUIManager` | 모든 Chest가 같은 함수 사용 |
| 맵 선택 UI | `MapTerminalInteractable` → `MapSelectionOverlay` | 현재 단일 터미널용 |
| 씬 이동 요청 | `DirectSceneTravel.TryLoad` | 터미널과 포탈 경로가 공유 |
| 씬 이동 전 UI·입력 정리 | `PersistentGameplayShell.PrepareForTravel` | 모든 직접 씬 이동이 공유 |

### PlayerInteractor의 실제 탐색 방식

- `[코드 확인]` Player 중심 반경 3m를 `Physics.OverlapSphereNonAlloc`로 매 프레임 검색한다.
- `[코드 확인]` 모든 Physics Layer와 Trigger를 포함한다.
- `[코드 확인]` Collider에서 부모 방향으로 `Interactable`을 찾는다.
- `[코드 확인]` 후보 오브젝트의 Transform pivot까지의 거리를 비교해 하나를 고른다.
- `[코드 확인]` 후보 버퍼는 32 Collider로 고정되어 있다.
- `[코드 확인]` E 입력 직전에도 검색을 한 번 더 수행하므로 실제 실행 대상은 그 순간의 가장 가까운 대상이다.
- `[코드 확인]` E 키와 탐색 반경은 `PersistentGameplayShell.prefab`의 `PlayerInteractor`에 각각 `E`, `3`으로 직렬화되어 있다.
- `[코드 확인]` 안내는 정식 UGUI가 아니라 `OnGUI` 디버그 박스다.

즉, “각 오브젝트가 따로 Player 거리를 감지한다”기보다는 **Player 한 곳이 모든 후보를 중앙 검색하고, 각 오브젝트는 자신의 활성 가능 여부와 행동을 제공한다**가 정확하다.

---

## 4. 사용자 설명과 현재 구현의 대조

| 항목 | 현재 판정 | 근거 |
|---|---|---|
| 범위 안에서 E 안내 활성화 | 코드상 충족, 시각 미검증 | 가장 가까운 `currentInteractable` 하나의 OnGUI prompt를 표시하는 코드 확인 |
| 대상이 여러 개면 가장 가까운 하나 선택 | 코드상 충족, 런타임 호출 확인 | 중앙 거리 비교 후 하나만 실행; 실제 E 키 입력은 미검증 |
| Chest UI가 열린 동안 이동 가능 | 코드상 허용, 실제 WASD 미검증 | `PlayerMovement`를 비활성화하지 않으며 런타임에도 enabled 상태 유지 |
| 열린 Chest에서 3m 초과 시 UI 자동 닫힘 | Play Mode 충족 | `currentOpenedChest` 기준 거리 이탈 후 Update 프레임에서 두 패널 닫힘 확인 |
| 상호작용 중 처음 대상을 공통으로 고정 | **미충족** | Play Mode 호출 경로에서 `PlayerInteractor`가 더 가까운 대상으로 다시 선택 |
| 활성 Chest의 거리 기준은 처음 연 Chest | 부분 충족 | Chest UI의 거리 검사는 `currentOpenedChest` 기준이지만 E 대상은 다른 오브젝트로 바뀔 수 있음 |
| 모든 상호작용이 이동 중 지속 가능 | 미충족이 아니라 종류별 정책 | Chest는 이동 가능, Map Selection은 modal이라 이동 잠금, Portal은 즉시 이동 |
| 거리 이탈 시 모든 상호작용 UI 자동 닫힘 | Chest에만 해당 | Map Selection은 이동이 잠기며 거리 종료 없음, Portal에는 지속 UI 없음 |

### 2026-08-20 Play Mode 호출·상태 확인

1. `[Play Mode 호출 확인]` Player를 `Chest` 가까이에 배치한 뒤 `PlayerInteractor.TryInteract()` 런타임 경로를 호출하자 Player/외부 인벤토리 패널이 열렸고 `PlayerMovement`는 활성 상태였다. 실제 E 키와 WASD 축 입력은 직접 검증하지 않았다.
2. `[Play Mode 호출 확인]` 그 UI가 열린 상태로 Player를 `Chest (1)` 가까이에 배치해 같은 호출 경로를 다시 실행하자 현재 대상이 `Chest (1)`로 바뀌었다. 공통 active-target lock은 없다는 것이 확인됐다.
3. `[Play Mode 확인]` Chest UI를 연 뒤 Player를 해당 Chest에서 3m 밖으로 배치하고 Update 한 프레임을 진행하자 외부 패널과 Player 인벤토리 패널이 모두 자동으로 닫혔다.

---

## 5. 개별 상호작용 구현

### Chest

- `GameMap1`의 `Chest`, `Chest (1)`에는 각각 `Chest`와 `ChestInteractable`, 활성 BoxCollider가 있다.
- 두 Collider는 Trigger가 아닌 solid Collider다.
- `ChestInteractable.Interact`는 같은 Player의 `InventoryUIManager.TryToggleChestInventory(chest)`를 호출한다.
- 열 때 Player 인벤토리와 해당 외부 인벤토리를 함께 표시한다.
- 같은 Chest에서 다시 E를 누르면 모두 닫는다.
- 다른 Chest가 더 가까운 상태에서 E를 누르면 열린 대상을 그 Chest로 전환할 수 있다.
- `InventoryUIManager`가 열린 Chest를 `currentOpenedChest`로 기억하고 매 프레임 별도 거리 검사를 한다.
- 거리 초과 시 드래그를 취소하고 case popup을 정리한 뒤 Player/외부 인벤토리를 모두 닫는다.
- 각 Chest는 scene-local이며 `Awake`에서 6×5 빈 `StandardStashViewData`를 새로 만든다. 현재 Chest 내용 영속성은 없다.

### Map Selection Terminal

- `GameMap1`의 `Stage1_MapSelectionTerminal`에 `MapTerminalInteractable`과 `MapSelectionOverlay`가 있다.
- E 진입까지는 Chest/Portal과 같은 `PlayerInteractor` 탐색 경로를 사용한다.
- UI를 열기 전에 현재 인벤토리를 닫는다.
- UI가 열리면 Player 이동, 다른 E 상호작용, 인벤토리 입력을 잠근다.
- 현재 직렬화된 선택은 `GameMapTest / RaidEntry` 한 개다.
- 취소 또는 Escape로 닫으면 이전 입력 상태를 복원한다.
- 맵 선택 UI에는 거리 이탈 자동 종료가 없다. 이동이 잠기므로 정상 입력만으로 범위를 벗어나지 않는다.

### Return Portal

- `GameMapTest`의 `Stage1_ReturnPortal`에 `ReturnPortalInteractable`과 활성 solid BoxCollider가 있다.
- E 안내와 가장 가까운 대상 선택은 Chest와 동일한 `PlayerInteractor` 공통 경로를 사용한다.
- 현재 직렬화된 목적지는 `GameMap1 / BaseReturn`이다.
- E를 누르면 `DirectSceneTravel.TryLoad`를 호출해 즉시 비동기 씬 이동을 요청한다.
- 로딩 중에는 `CanInteract`가 false가 되어 중복 요청을 막는다.
- 이동 준비 과정에서 공통 셸이 열린 인벤토리, 드래그, popup과 입력 상태를 정리한다.
- Portal은 지속 상호작용 UI가 없으므로 “거리 이탈 시 UI 닫기”나 “상호작용 대상 유지”가 적용될 세션이 없다.
- 현재는 생환 성공 판정을 하지 않는 단순 귀환 포탈이다.

---

## 6. 공통화와 하드코딩 감사

### 이미 공통화된 부분

- 대상 검색, 가장 가까운 하나 선택, E 입력, 안내 표시가 `PlayerInteractor` 한 곳에 있다.
- 모든 현재 대상은 `Interactable`의 공통 계약을 사용한다.
- 모든 Chest는 `ChestInteractable`과 `InventoryUIManager.TryToggleChestInventory`를 재사용할 수 있다.
- 맵 터미널과 귀환 포탈은 목적지 로드에 `DirectSceneTravel`을 공유한다.
- 씬 전환 전 정리는 `PersistentGameplayShell`과 `InventoryUIManager.CloseAllInventories`를 공유한다.
- 관련 실행 경로에는 `GameObject.Find`, `FindAnyObjectByType`, `FindFirstObjectByType`로 매번 대상을 찾는 코드가 없다. Player-local `GetComponent`, serialized reference와 기존 Singleton을 사용한다.

따라서 현재 시스템은 각 오브젝트가 전부 독립적으로 하드코딩된 구조는 아니다. **공통 진입과 씬 이동은 재사용 가능하고, Chest/Terminal/Portal이 기능별 행동만 나눈 형태**다.

### 중복 또는 임시 고정값

#### 우선 해결 가치가 큰 항목

1. **공통 active interaction session이 없다.**
   - Chest UI가 열려도 `PlayerInteractor`는 더 가까운 다른 대상으로 바뀐다.
   - 사용자 의도가 “처음 연 대상을 닫거나 거리 이탈할 때까지 유지”로 확정되면 현재 경계 안에서 세션 대상 고정이 필요하다.

2. **상호작용 거리가 두 곳에 독립 저장되어 있다.**
   - `PlayerInteractor.interactionRange = 3`
   - `InventoryUIManager.interactionRange = 3`
   - 현재 값은 같지만 한쪽만 바꾸면 prompt 범위, 열기 범위, 자동 닫힘 범위가 달라질 수 있다.

3. **파괴된 Chest의 자동 UI 종료 분기가 잘못되어 있다.** `[코드 확인, Play Mode 미검증]`
   - 거리 검사 바깥 조건이 이미 `currentOpenedChest != null`을 요구해, 내부의 null 처리 분기는 사실상 도달할 수 없다.
   - 현재 Chest 파괴 기능은 없어서 정상 Stage 1 경로에서는 발생하지 않지만, 향후 파괴/재생성되는 컨테이너를 만들기 전에 수정해야 한다.

#### 현재 프로토타입에서는 허용 가능한 항목

- E는 `PlayerInteractor`의 serialized `KeyCode`라 한 곳에서 바꿀 수 있지만 아직 리바인딩 가능한 Input Action은 아니다.
- I와 Escape는 `InventoryUIManager`/`MapSelectionOverlay`가 직접 읽는다.
- prompt 문구와 맵 선택 화면은 영문 OnGUI 임시 UI다.
- 맵 터미널은 목록 데이터가 아니라 단일 serialized scene/spawn/display 값만 가진다.
- Portal의 목적지 scene/spawn은 Inspector에서 바꿀 수 있지만 문자열 기반이다.
- Portal prompt `Return To GameMap1`은 코드 고정 문자열이라 목적지 변경 시 문구와 불일치할 수 있다.
- 대상 탐색은 `Physics.AllLayers`, 고정 Collider 버퍼 32개, object pivot 거리, 같은 거리의 명시적 tie-break 없음, 시야선 검사 없음이다.
- `ChestInteractable`은 `Chest`를 Require하지만 Collider를 Require하지 않는다.

---

## 7. 현재 알려진 다음 정리 후보

아래는 아직 구현하지 않았다.

1. `[사용자 확인 우선]` 지속 상호작용 중 처음 대상을 유지한다는 계약을 확정한다.
2. `[후속 후보]` 새 Manager를 만들지 않고 현재 `PlayerInteractor`와 개별 UI 경계 안에서 active 대상의 시작/종료/거리 이탈을 한 흐름으로 연결한다.
3. `[후속 후보]` 상호작용 거리의 권위 값을 하나로 통합한다.
4. `[후속 후보]` 열린 Chest가 파괴·비활성화될 때 UI와 드래그 상태를 안전하게 정리한다.
5. `[검증]` Chest A/B 겹침, 빠른 E, 대상 비활성화, 벽 너머 대상, Collider 32개 초과를 필요 범위에 맞춰 검사한다.
6. 위 상호작용 계약을 안정화한 뒤 `RaidSession`과 저장 없는 루팅을 진행한다.

이 목록은 자동 작업 지시가 아니다. 최신 사용자 요청이 항상 우선한다.

---

## 8. 검증 근거와 최종 Editor 상태

### 직접 확인한 파일

- `Assets/Scripts/Interaction/Interactable.cs`
- `Assets/Scripts/Interaction/PlayerInteractor.cs`
- `Assets/Scripts/Interaction/ChestInteractable.cs`
- `Assets/Scripts/Interaction/MapTerminalInteractable.cs`
- `Assets/Scripts/Interaction/ReturnPortalInteractable.cs`
- `Assets/Scripts/InventoryUIManager.cs`
- `Assets/Scripts/SceneFlow/MapSelectionOverlay.cs`
- `Assets/Scripts/SceneFlow/DirectSceneTravel.cs`
- `Assets/Scripts/SceneFlow/PersistentGameplayShell.cs`
- `Assets/Scripts/Chest.cs`
- `Assets/Prefabs/PersistentGameplayShell.prefab`
- `Assets/Scenes/GameMap1.unity`
- `Assets/Scenes/GameMapTest.unity`

### Unity 검사 결과

- Player prefab의 `PlayerInteractor`: E, range 3, debug prompt 활성
- Player prefab의 `InventoryUIManager`: 별도 Chest range 3
- GameMap1: Chest 2개, Map Terminal 1개
- GameMapTest: Return Portal 1개, 목적지 `GameMap1 / BaseReturn`
- 검사 종료 후: Play Mode false, Pause false, 활성 씬 `GameMap1`, loaded scene 1개, scene dirty false
- 현재 Console Error/Exception/Assert는 0개다. Warning 1개는 외부 `AnimeNaturalEnvironment/RenderTextureBaker.cs`의 obsolete URP API 경고이며 이번 Player 기능 회귀가 아니다. 현재 prefab에는 Missing Script가 없다.

---

## 9. 플레이어 달리기와 Humanoid 로코모션

### 사용자 확정 요구

- `[사용자 요구]` 이동 중 Shift를 누르고 있는 동안 일반적인 달리기 상태가 된다.
- `[사용자 요구]` 달리기 이동 속도는 걷기 속도의 1.3배다.
- `[사용자 요구]` 걷기와 달리기에 서로 다른 애니메이션을 사용한다.
- `[사용자 요구]` 키보드 이동 입력의 8방향에 맞춰 캐릭터 외형이 바라보는 방향도 바뀐다.
- `[사용자 요구]` 방향은 순간적으로 스냅하지 않고 매우 빠른 회전 보간으로 전환한다.
- 기존 persistent Player를 재생성하거나 교체하지 않고 같은 `PersistentGameplayShell` 안의 Player를 확장한다.

### 현재 구현

- `[코드/씬 확인]` 기존 걷기 속도 `5`는 그대로 유지하고, Left Shift 또는 Right Shift를 누른 채 실제 이동할 때 `6.5`를 사용한다.
- `[코드/씬 확인]` 대각선 입력은 기존처럼 방향 벡터를 normalize하므로 대각선 달리기도 `6.5`를 넘지 않는다.
- `[코드/씬 확인]` Shift만 누르고 이동 입력이 없거나 장애물에 완전히 막혀 실제 위치가 바뀌지 않으면 Idle 값 `0`을 사용한다.
- `[코드/씬 확인]` `PlayerMovement`가 같은 persistent Player 외형의 자식 `Animator`를 직접 참조한다. 별도 Player, 별도 이동 Manager 또는 scene-local Animator를 만들지 않았다.
- `[코드/씬 확인]` Animator의 `LocomotionSpeed` 값은 Idle `0`, Walk `1`, Run `1.3`이다.
- `[코드/씬 확인]` 맵 선택 화면이나 씬 이동 준비가 `PlayerMovement`를 끌 때 `OnDisable`에서 속도와 Animator 값을 Idle로 되돌린다.
- `[코드/씬 확인]` `Horizontal/Vertical`의 `-1/0/1` 조합을 정규화한 기존 입력 벡터를 그대로 사용하므로 키보드 기준 목표 방향은 `0/45/90/135/180/225/270/315°`다.
- `[코드/씬 확인]` 기존 Animator 외형 자식만 `Quaternion.RotateTowards`로 돌린다. Player 루트, Collider, Rigidbody, Camera, 상호작용 범위는 회전시키지 않는다.
- `[코드/씬 확인]` 회전 속도는 임시 기본값 `1080°/s`이며 `turnSpeedDegreesPerSecond` 직렬화 필드에서 조정할 수 있다. 180° 반전도 약 0.167초에 끝나지만 한 프레임 스냅은 아니다.
- `[코드/씬 확인]` 입력이 없으면 마지막 방향을 유지한다. 장애물에 막혀 실제 이동하지 못해도 입력 방향으로는 제자리 회전한다.

### 애니메이션 에셋 구성

- `[코드/씬 확인]` `uploads_files_4931206_TrialFreya_FBX.fbx`와 `AnimationLibrary_Unity_Standard.fbx`는 각각 `Create From This Model` 방식의 유효한 Humanoid Avatar를 사용한다.
- `[코드/씬 확인]` `PlayerLocomotion.controller`는 1D Blend Tree 하나로 Idle, Walk, Run을 연결한다.
- `[코드/씬 확인]` 사용 클립은 `Rig|Idle_Loop`, `Rig|Walk_Loop`, `Rig|Jog_Fwd_Loop`이며 세 클립 모두 Humanoid motion과 loop가 활성화되어 있다.
- 현재 1.3배 달리기에는 `Sprint_Loop`보다 속도 체감이 가까운 `Jog_Fwd_Loop`를 임시 Run 시각으로 사용한다. 이는 이동 규칙을 바꾸지 않고 나중에 클립만 교체할 수 있다.
- `[코드/씬 확인]` `Animator.applyRootMotion = false`다. 위치 이동과 충돌 판정의 권한은 기존 `PlayerMovement`에 그대로 있다.
- `[코드/씬 확인]` `PersistentGameplayShell.prefab` 안에는 Animator와 PlayerMovement가 각각 정확히 1개이고, PlayerMovement의 Animator 참조가 연결되어 있으며 Missing Script는 0개다.

### 2026-08-20 검증 결과

- `[Play Mode 확인]` Idle, Walk, Run 값을 각각 적용해 실제 Freya SkinnedMesh를 렌더링했고, 세 포즈가 서로 다르며 T포즈가 해소되고 뼈 리타기팅이 정상인 것을 시각 확인했다.
- `[Play Mode 확인]` 런타임 시작 시 shell, PlayerMovement, Animator가 각각 1개이고 Animator Avatar는 valid Human, Controller는 `PlayerLocomotion`, root motion은 꺼짐, 초기 값은 Idle `0`이었다.
- `[코드/씬 확인]` Unity Editor에서 두 Avatar, 세 loop clip, Blend Tree 임계값 `0/1/1.3`, 걷기 `5`, 달리기 `6.5`, 양쪽 Shift, prefab 참조, Missing Script 0을 한 번에 검사했고 모두 통과했다.
- `[Play Mode 호출 확인]` 8개 입력 벡터를 런타임 회전 함수에 적용해 최종 yaw `0/45/90/135/180/225/270/315°`, 목표 오차 0을 확인했다.
- `[Play Mode 호출 확인]` 180° 목표를 한 번 갱신했을 때 20ms 프레임에서 21.6°만 회전해 보간됨을 확인했고, 반복 갱신 뒤 정확히 목표각에 도달했다.
- `[Play Mode 확인]` 입력 0에서는 마지막 방향 변화량 0, 회전 검증 중 Player 루트 회전 변화량 0, Player 위치 변화량 0이었다.
- `[Play Mode 확인]` 정면·대각선·측면·후면을 실제 SkinnedMesh로 렌더링해 외형과 Humanoid 애니메이션이 방향에 맞게 정상 회전하는 것을 시각 확인했다.
- `[Play Mode 확인]` `GameMap1 → GameMapTest/RaidEntry → GameMap1/BaseReturn` 왕복 뒤에도 shell, Player, 외형, Animator, Camera의 Entity ID가 모두 동일하고 각 구성은 1개였다.
- `[미검증]` 실제 키를 길게 누르는 자동 입력은 Unity 창에서 사용자 입력이 감지되어 중단했다. 따라서 Left/Right Shift를 실제로 홀드한 이동 거리 측정은 수동 Play Mode 확인이 한 번 필요하다.
- `[미검증]` 이번 방향 회전 추가 뒤 왕복은 1회 통과했으며, 장시간 반복 기준인 새 3회 왕복은 실행하지 않았다.
- `[미검증]` Player build에서는 확인하지 않았다.

### 현재 의도적으로 보류한 것

- 현재는 이동 입력이 외형 방향의 권한을 가진다. 향후 마우스 조준을 만들 때 `이동 방향`과 `조준/시선 방향` 중 무엇이 외형 방향의 최종 권한을 가질지는 별도로 결정한다.
- 스태미나, 달리기 토글, 카메라 흔들림/FOV, 발소리, 가속·감속, Input System 리바인딩은 이번 범위에 넣지 않았다.
- 달리기 속도와 Animator 임계값은 Inspector/Controller 데이터로 분리되어 있어 후속 조정이 가능하지만, 사용자 승인 없이 1.3배 규칙을 바꾸지 않는다.

---

## 10. GameMapTest의 애니메이션 순찰 좀비

### 이번 기능 범위

- `[사용자 요구]` 무료 3D 에셋을 사용해 실제로 움직이는 적 하나를 만든다.
- `[프로토타입 범위]` 이번 적은 두 지점을 왕복하는 시각·이동 검증용이다.
- 전투, 추적, 체력, 피해, 드롭, 상호작용, NavMesh, 저장은 아직 넣지 않는다.

### 외부 에셋과 라이선스

- `[코드/에셋 확인]` Kenney의 공식 `Animated Characters Retro` 팩에서 좀비 모델, 좀비 스킨, Idle/Run 애니메이션만 가져왔다.
- 공식 페이지: https://kenney.nl/assets/animated-characters-retro
- 원본 `LICENSE.txt`와 출처·다운로드 SHA-256을 `Assets/ThirdParty/Kenney/AnimatedCharactersRetro`에 함께 보존했다.
- 라이선스는 CC0 1.0이며 개인·교육·상업 프로젝트에서 복사·수정·배포할 수 있고 크레딧은 필수가 아니다.
- 모델을 새로 만들거나 메시를 수정한 것이 아니므로 Blender는 사용하지 않았다.

### 현재 구현

- `[코드/씬 확인]` `EnemyPatrol`은 별도 Manager나 NavMesh 없이 프리팹 로컬 좌표의 두 지점을 `MoveTowards`로 왕복한다.
- `[코드/씬 확인]` 이동 방향은 `RotateTowards`로 보간하며, 목적지 도착 시 0.5초 정지한 뒤 반대편으로 이동한다.
- `[코드/씬 확인]` `KenneyZombie.controller`는 `IsMoving` bool 하나로 Idle과 Moving 상태를 전환한다.
- `[코드/에셋 확인]` 모델, Idle, Run FBX는 각각 유효한 Humanoid Avatar다. Idle/Run clip은 loop이고 위치·회전 Root Motion은 pose에 bake했다.
- `[코드/씬 확인]` Animator의 Root Motion은 꺼져 있으며 위치 권한은 `EnemyPatrol`에만 있다.
- `[코드/씬 확인]` `KenneyZombiePatrol.prefab`은 `ZombieAgent`와 외형·Animator를 포함하고 Missing Script가 없다.
- `[코드/씬 확인]` GameMapTest에는 `Test_KenneyZombiePatrol` 인스턴스가 `(0, 0, 3)`에 하나 배치되어 있다. 순찰 구간은 이 기준점에서 X `-1.5`부터 `1.0`까지이며 Plane 안에 있다.
- `[의도적 보류]` Collider와 `Obstacle` 태그를 넣지 않아 현재 플레이어 이동이나 E 상호작용을 막지 않는다. 적 물리와 피격 판정은 전투 계약을 만들 때 별도로 결정한다.

### 2026-08-20 검증 결과

- `[Play Mode 확인]` GameMapTest 직접 실행에서 좀비가 X `-1.5 → 1.0` 방향으로 이동했고, 이후 목표가 반대로 바뀌어 X `-0.447`, forward `(-1, 0, 0)` 상태로 돌아오는 것을 확인했다.
- `[Play Mode 확인]` 이동 중 `IsMoving=true`, Animator Moving 상태, loop 진행 시간이 1을 넘어 계속 재생되는 것을 확인했다.
- `[Play Mode 확인]` 실제 Humanoid Run 포즈와 좀비 스킨이 Game View/Scene View에서 렌더링되어 T 포즈가 아닌 움직이는 외형을 시각 확인했다.
- `[Play Mode 확인]` 직접 실행 중 Enemy, PersistentGameplayShell, PlayerMovement, Camera, AudioListener, EventSystem, InventoryUIManager가 각각 정확히 1개였다.
- `[코드/씬 확인]` Prefab의 Agent, Animator Controller, valid Human Avatar, URP 재질 참조가 모두 연결되어 있고 Root Motion과 Missing Script는 0이다.
- 기능 수정 전 Console 기준선은 Error 0 / 기존 외부 RenderTextureBaker obsolete Warning 1이었다. 첫 Avatar 복사 시도에서 생긴 Rig Error 2건은 Console 이력에 남아 있지만, 루트 계층 불일치 원인을 확인한 뒤 각 FBX를 독립 Humanoid로 다시 설정했다. 그 이후 Avatar/clip/prefab/Play Mode 재검증 구간에는 신규 Error/Exception/Assert가 없었다.
- `[미검증]` Player 빌드와 전투·추적 동작은 이번 범위가 아니다.

---

## 11. 편집 상태 Game View 카메라

### 발생 원인

- `[코드/씬 확인]` 실제 Camera는 `PersistentGameplayShell.prefab` 안에 있으며 `GameplayShellBootstrap.Awake`가 Play 진입 후 셸을 생성한다.
- `[재현 확인]` 수정 전 GameMap1과 GameMapTest에는 편집 상태 Camera가 0개여서 Game View에 `No cameras rendering`이 표시됐다. 런타임 카메라가 숨겨진 것이 아니라 편집 상태에는 아직 생성되지 않은 구조였다.

### 현재 구현

- `[코드/씬 확인]` `Assets/Prefabs/EditorOnly/AuthoringPreviewCamera.prefab`을 GameMap1과 GameMapTest에 각각 1개 배치했다.
- `[코드/씬 확인]` 미리보기 루트는 `EditorOnly` 태그이며 Player, UI, EventSystem, AudioListener와 CameraFollow를 포함하지 않는다.
- `[코드/씬 확인]` `EditModeCameraPreview`는 편집 상태에서만 자식 Camera를 활성화하고 Play Mode에서는 자식 오브젝트를 비활성화한다. 실제 Player·Camera·인벤토리 셸은 기존과 같이 동일한 `PersistentGameplayShell` 인스턴스 하나가 소유한다.
- `[코드/씬 확인]` GameMap1 미리보기 위치는 기본 진입점 기준 `(2, 10.5, -10)`, GameMapTest는 `(-1, 10.5, -12)`이며, 실제 셸 카메라와 같은 Orthographic 설정을 사용한다.

### 2026-08-20 검증 결과

- `[Edit Mode 확인]` 두 씬 모두 Preview Camera 1개가 활성이고 AudioListener는 0개다. 두 씬 모두 실제 Camera 렌더 캡처로 맵 오브젝트가 표시되는 것을 시각 확인했다.
- `[Play Mode 확인]` GameMap1 직접 실행에서 활성 Camera와 AudioListener는 PersistentGameplayShell 아래 각각 1개였고 Preview Camera는 0개였다.
- `[Play Mode 확인]` `GameMap1 → GameMapTest → GameMap1` 왕복 중 shell과 실제 Camera의 Entity ID가 유지됐으며, 양쪽 씬에서 Preview Camera는 계속 비활성이었다.
- `[Play Mode 확인]` Domain Reload와 Scene Reload를 모두 비활성화한 진입에서도 shell/활성 Camera/AudioListener는 각각 1개, Preview Camera는 0개였으며 Play 종료 뒤 미리보기가 다시 활성화됐다. 검증 후 Editor 설정은 기존 `Enter Play Mode Options 비활성/None`으로 복원했다.
- `[Edit Mode 확인]` Play 종료 뒤 GameMap1 Preview Camera가 다시 활성화됐고 씬은 dirty가 아니었다.
- `[Player build 확인]` Windows Development build는 성공했다. 다만 생성된 exe를 직접 실행해 `EditorOnly` Preview Camera가 런타임에서 제거되는 장면까지 시각 확인하지는 않았다.

---

## 12. 최소 세이브/로드와 제품 시작 흐름

### 현재 제품 흐름

- `[Play Mode 확인]` `InitialLoadingScene → MainMenuScene → GameLoadingScene → GameMap1` 순서로 진입한다.
- `[코드/씬 확인]` Main Menu에는 `NEW GAME`, `LOAD GAME`, `SETTINGS`, `EXIT` 네 기능과 각각 필요한 최소 패널이 있다.
- `[Play Mode 확인]` New Game은 기존 저장 파일을 지우거나 덮어쓰지 않고, `GameMap1` 기지에서 초기 8×9 인벤토리와 시험 아이템 ID 1~6으로 시작한다.
- `[Play Mode 확인]` Load 요청은 같은 로딩 씬을 거쳐 `GameMap1`에서 persistent Player의 기존 `InventoryUIManager`에 한 번만 적용된다. Player, Camera, UI 셸을 재생성하지 않는다.
- `[코드/씬 확인]` GameLoading의 기존 Slider는 실제 비동기 로드 진행률 0~1에 연결되어 있다.
- `[Play Mode 확인]` Settings의 Sound 토글은 슬롯 세이브와 분리된 전역 `PlayerPrefs` 설정이며 즉시 `AudioListener.pause`에 적용된다.
- `[Play Mode 확인]` Exit는 확인 패널을 거치며, 실제 종료 호출은 `Application.Quit`이다.

### 저장되는 데이터

- 단일 프로토타입 슬롯 경로는 `Application.persistentDataPath/Saves/save_slot_1.json`이며 이전 정상본은 `.bak`으로 유지한다.
- 스키마 버전은 2이고 인벤토리는 재귀 객체 대신 `flat-records-v1` 목록으로 저장한다.
- 각 아이템은 ItemDatabase의 숫자 `definitionId`, 그리드 좌상단 슬롯 인덱스, 회전 상태, 컨테이너 부모 관계만 저장한다.
- 컨테이너 내부 아이템은 파일 내부 관계용 `recordId`로 연결한다. 이 값은 영구 아이템 instance ID가 아니다.
- 이름, 설명, 아이콘, 아이템 크기와 컨테이너 크기는 저장하지 않고 같은 `ItemDatabase.asset`에서 다시 조회한다.
- 씬, Player 위치, 열린 UI, 드래그, Camera, Portal, Enemy와 일시 상호작용 상태는 저장하지 않는다. 로드 후 시작 위치는 항상 기지의 SpawnPoint다.

### 기지 상태와 ItemDatabase 경계

- `[코드/씬 확인]` 현재 GameMap1의 시험 Chest 2개는 stable ID가 없고 매 씬 로드마다 빈 6×5 데이터를 생성하므로 아직 기지 영속 데이터로 저장하지 않는다.
- `[코드/씬 확인]` `BaseSaveData`에는 향후 확장용 format version만 있고, 확인되지 않은 기지 규칙이나 Chest 소유권을 임의로 만들지 않았다.
- `[코드/씬 확인]` ItemDatabase는 기존 ScriptableObject asset 하나를 persistent shell과 Main Menu가 직접 참조한다. 별도 DontDestroy Manager나 씬별 복사본을 추가하지 않았다.

### 저장·로드 안전성

- 저장 전에 열린 Player/Chest UI, 드래그와 case popup을 정리한 뒤 캡처한다.
- 쓰기 전에 DB의 null·잘못된 ID·중복 ID와 전체 인벤토리 배치·부모 관계를 검증한다.
- 임시 파일을 먼저 쓴 뒤 정상 파일로 교체하고, 기존 정상 파일은 `.bak`으로 남긴다.
- 로드는 primary를 전체 의미 검증한 뒤 사용하며, primary의 JSON 헤더가 정상이어도 아이템 ID·배치·부모 관계가 손상됐으면 정상 backup을 검증해 대신 선택한다.
- 복원은 별도 8×9 후보를 완성한 뒤 한 번에 교체하므로 실패 시 현재 인벤토리를 유지한다.
- 저장 UI는 현재 기지 `GameMap1`의 우측 상단 OnGUI 버튼과 `F5`로만 제공한다. 정식 저장 메뉴 디자인은 후속이다.

### 2026-08-20 검증 결과

- `[코드/씬 확인]` MainMenuManager 1개, 버튼 9개, Toggle 1개, 유효한 listener와 serialized reference, Missing Script 0을 확인했다.
- `[Play Mode 확인]` InitialLoading부터 Main Menu에 도착한 뒤 Load/Settings/Exit 패널과 Back 동작, Sound 토글, New Game 버튼을 실제 Button listener 경로로 실행했다.
- `[Play Mode 확인]` New Game 선택 뒤 GameLoading을 거쳐 GameMap1에 도착했고 shell, 8×9 인벤토리, 초기 아이템 6개와 BasePersistenceController를 확인했다.
- `[Play Mode 확인]` 컨테이너 내부 회전 아이템을 포함한 사용자 정의 로드 데이터를 Main Menu 시작 요청과 GameLoading을 거쳐 GameMap1에 적용했고, 루트/내부 슬롯과 회전 상태가 동일하게 복원됐다.
- `[코드/런타임 확인]` 중첩 컨테이너, 동일 종류 복수 아이템, 회전 상태를 `Capture → JSON → FromJson → Restore`로 왕복했고, 알 수 없는 definition ID, 겹침, 순환 부모 관계는 거부됐다.
- `[코드/런타임 확인]` 실제 사용자 슬롯을 건드리지 않는 임시 캐시에서 `첫 저장 → 두 번째 저장 → primary 의미 손상 → 정상 backup 복구`를 통과했다.
- `[Player build 확인]` 활성 Build Settings 5개 씬으로 Windows Development build가 성공했다. 산출물은 `Builds/SaveLoadPrototype/FantasySurvivalEscapeGame.exe`다.
- `[미검증]` 생성된 exe를 직접 실행한 수동 UI 조작과 실제 사용자 슬롯에 대한 F5 저장은 수행하지 않았다. 기존 사용자 데이터 보호를 위해 검사 당시 존재하지 않던 실제 슬롯 파일을 자동 생성하지 않았다.
