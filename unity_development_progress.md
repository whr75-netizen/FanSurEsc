# Unity 개발 진행 기록

**마지막 확인:** 2026-08-22
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
- 전투, 추적, 피해 전달, 사망, 드롭, 상호작용, NavMesh와 저장은 아직 넣지 않는다. 개체별 체력 상태만 2026-08-22 후속 하위 작업으로 추가했다.

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

### 2026-08-22 시험 좀비의 최소 체력 상태

- `[사용자 요구]` 현재 배치된 시험 몹 한 마리에 우선 체력만 추가한다. 몹 종류별 수치를 개별 행동 코드에 하드코딩하지 않고, 향후 데이터 기반 몹과 Workshop 모딩으로 확장 가능한 경계를 둔다.
- `[설계 결정]` C# `struct`를 각 개체에 복사하지 않는다. 몹 종류가 공유하는 정적 프리셋은 `EnemyDefinition` ScriptableObject로, 소환된 한 개체의 현재 상태는 그 GameObject의 `EnemyStats` MonoBehaviour로 분리한다. Workshop JSON/XML 형식, 외부 ID와 로더는 아직 확정하거나 구현하지 않는다.

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | 종류별 최대 체력 원본은 공유 `EnemyDefinition`, 개체별 현재 체력 원본은 해당 `EnemyStats` 하나다. |
| 수명 범위 | 정의는 프로젝트/Application 데이터, 현재 체력은 Enemy Entity 수명이다. |
| 생성·파괴 주체 | 현재는 `KenneyZombiePatrol` 프리팹 인스턴스 생성·파괴와 함께 `EnemyStats`가 생성·정리된다. 별도 spawn 시스템은 아직 없다. |
| 변경 진입점 | 초기화는 `Initialize`, 이후 현재 체력 변경은 `ApplyDamage`, `RestoreHealth`, `ResetHealth`만 사용한다. |
| 포함 관계 | `EnemyStats`는 `EnemyDefinition`을 읽기 전용으로 참조하며 정의 에셋을 소유하거나 변경하지 않는다. `EnemyPatrol`과도 서로의 상태를 소유하지 않는다. |
| 이전 규칙 | 현재 체력의 컨테이너 이전은 없다. 다른 정의로 초기화하면 그 정의의 최대 체력으로 새 개체 상태를 시작한다. |
| 파생 표현 | 변경 완료 뒤 `HealthChanged` 이벤트만 제공한다. 적 체력바, Animator, 사망 표현과 캐시는 아직 없다. |
| 저장 경계 | 현재 시험 적의 체력은 씬/Entity 임시 상태이며 세이브하지 않는다. |
| 업데이트 주체 | `EnemyStats`에는 `Update`/Tick이 없다. 명시적 메서드 호출 때만 값이 바뀐다. |

- `[코드/에셋 확인]` `KenneyZombie.asset` 정의의 최대 체력은 100이며, `KenneyZombiePatrol.prefab` 루트의 `EnemyStats`가 이를 참조한다. GameMapTest의 기존 `Test_KenneyZombiePatrol` 인스턴스가 같은 프리팹 변경을 상속하고 Missing Script는 0이다.
- `[코드/실행 확인]` 정의가 연결된 완성형 프리팹은 `Awake`에서 초기화한다. 향후 주입형 spawner가 활성 GameObject 생성 직후 같은 프레임에 `Initialize(definition)`을 호출하는 경로도 `Start` 이전에 정상 초기화되며, `Start`가 끝날 때까지 미초기화인 잘못된 구성만 오류로 보고한다.
- `[Play Mode 호출 확인]` GameMapTest의 `EnemyStats`가 `100/100`, initialized/alive로 시작했다. 25 피해→75, 10 회복→85, 초과 피해→0, 초과 회복→100, reset→100을 확인했고 음수 피해·회복은 무시됐다. 실제 값 변경에 대한 `HealthChanged` 통지는 6회로 중복되지 않았다.
- `[코드/실행 확인]` 두 임시 `EnemyStats`가 같은 `KenneyZombie` 정의를 참조하도록 초기화한 뒤 첫 개체에만 25 피해를 적용했다. 첫 개체 75, 둘째 개체 100으로 유지되어 공유 정의와 개체별 현재 체력이 분리됨을 확인했다.
- `[Play Mode 호출 확인]` 체력 검증 뒤 기존 `EnemyPatrol`이 활성 상태를 유지했고, 프레임을 진행했을 때 Agent가 X `-1.500 → -0.777`, waypoint `0 → 1`, `IsMoving=true`로 이동해 순찰 회귀가 없음을 확인했다.
- `[의도적 보류]` 공격의 피해 전달 계약, Collider/피격 판정, 0 체력 사망 처리, 적 체력 UI, 드롭, respawn/pooling 초기화와 적 세이브는 구현하지 않았다.

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
- 현재 스키마 버전은 3이고 플레이어 인벤토리와 장비를 하나의 `playerItems` / `flat-player-items-v1` 목록으로 저장한다. 유효한 개발용 v2 `flat-records-v1`은 읽을 때 장비가 빈 v3 상태로 변환하며, 기존 아이템을 임의 장착하지 않는다.
- 각 아이템은 ItemDatabase의 숫자 `definitionId`, 파일 내부 `recordId`와 컨테이너 부모 관계, 그리드 슬롯 또는 `equipmentSlot`, 회전 상태를 저장한다.
- 컨테이너 내부 아이템은 파일 내부 관계용 `recordId`로 연결한다. 이 값은 영구 아이템 instance ID가 아니다.
- 이름, 설명, 아이콘, 아이템 크기, 컨테이너 크기와 장착 가능 슬롯은 저장하지 않고 같은 `ItemDatabase.asset`에서 다시 조회한다.
- 씬, Player 위치, 열린 UI, 드래그, Camera, Portal, Enemy와 일시 상호작용 상태는 저장하지 않는다. 로드 후 시작 위치는 항상 기지의 SpawnPoint다.

### 기지 상태와 ItemDatabase 경계

- `[코드/씬 확인]` 현재 GameMap1의 시험 Chest 2개는 stable ID가 없고 매 씬 로드마다 빈 6×5 데이터를 생성하므로 아직 기지 영속 데이터로 저장하지 않는다.
- `[코드/씬 확인]` `BaseSaveData`에는 향후 확장용 format version만 있고, 확인되지 않은 기지 규칙이나 Chest 소유권을 임의로 만들지 않았다.
- `[코드/씬 확인]` ItemDatabase는 기존 ScriptableObject asset 하나를 persistent shell과 Main Menu가 직접 참조한다. 별도 DontDestroy Manager나 씬별 복사본을 추가하지 않았다.

### 저장·로드 안전성

- 저장 전에 열린 Player/Chest UI, 드래그와 case popup을 정리한 뒤 캡처한다.
- 쓰기 전에 DB의 null·잘못된 ID·중복 ID, 전체 배치·부모 관계, 런타임 단일 소유권, 장비 슬롯 유효성·호환성과 중복을 검증한다.
- 임시 파일을 먼저 쓴 뒤 정상 파일로 교체하고, 기존 정상 파일은 `.bak`으로 남긴다.
- 로드는 primary를 전체 의미 검증한 뒤 사용하며, primary의 JSON 헤더가 정상이어도 아이템 ID·배치·부모·장비 슬롯 관계가 손상됐으면 정상 backup을 검증해 대신 선택한다.
- 복원은 별도 `PlayerInventoryState`(8×9 인벤토리와 12슬롯 장비) 후보를 완성한 뒤 한 번에 교체하므로 실패 시 현재 상태를 유지한다.
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

---

## 13. 플레이어 장비 슬롯과 아이템 소유권

### 현재 구현

- `[코드/프리팹 확인]` `PlayerInventoryState` 하나가 8×9 `StandardStashViewData`와 `EquipmentLoadoutData`를 함께 소유한다. New Game은 기존 시험 아이템 ID 1~6과 빈 장비 상태를 만들고, Load는 두 상태를 함께 교체한다.
- `[코드/프리팹 확인]` 현재 실제로 노출하고 자동 장착할 수 있는 장비 슬롯은 무기 `W1` 1칸, 모자, 갑빠, 기능 신발, 가방, 목걸이, 반지, 팬던트, 꾸밈 머리·상의·하의·신발의 총 12칸이다. 각 칸은 인벤토리 아이템 크기와 무관하게 한 아이템만 가진다. 향후 무기 전환용 `W2`·`W3` 위치 ID는 데이터 구조에만 예약되어 있고 프리팹에서는 비활성화되어 있다.
- `[코드/프리팹 확인]` 12개 장비칸은 `GridLayoutGroup`의 2열×6행으로 배치한다. 플레이어 인벤토리는 중앙 기준 x=-326의 왼쪽, 장비 패널은 x=0, 외부 인벤토리는 x=326의 오른쪽이며 중앙 anchor와 인접 배치를 유지한다.
- `[코드 확인]` I로 열 때 플레이어 인벤토리와 장비 패널을 함께 등록·표시한다. Chest를 열면 같은 두 패널에 외부 인벤토리가 추가되며, 닫기·거리 이탈·상자 파괴 때 세 View를 함께 정리한다.
- `[코드 확인]` 각 `InventoryItemData`는 grid, 내부 container, equipment 중 최대 한 `InventoryOwner`만 가진다. 이동은 같은 런타임 객체 참조의 기존 소유권을 해제한 뒤 새 소유자에 부착하며, 실패하면 원래 위치로 복구한다.
- `[코드 확인]` `ItemDefinition.EquipmentSlot`이 장착 호환성을 정의한다. UI 계층 순서나 배열 index를 게임 규칙의 장비 종류로 사용하지 않는다.
- `[코드 확인]` 드래그 복구가 실패하면 새 드래그, UI 닫기, 씬 이동, 상태 교체와 저장 캡처를 중단하고 effect-cell의 마지막 참조를 유지한다. 외부 View의 셀 hover는 각 View가 무시한다.

### 저장과 검증 경계

- `[코드/실행 확인]` 임시 정의 데이터로 동일 객체의 인벤토리↔장비 이동, 이중 소유 거부, 잘못된 슬롯 거부를 확인했다.
- `[코드/실행 확인]` 장착된 가방의 내부 아이템을 포함한 4개 런타임 객체를 `Capture → JSON → FromJson → Restore`로 왕복했고, 그리드·장비·컨테이너의 소유자가 정확히 복원됐다.
- `[코드/실행 확인]` 컨테이너 A→B→A 간접 순환 삽입을 기존 소유권 변경 없이 거부했고, 장비 셀을 기존 플레이어/상자 View에 전달해도 교차 hover 예외가 발생하지 않음을 확인했다.
- `[코드 확인]` 유효한 v2 저장은 메모리에서 v3로 변환하며 장비를 모두 빈 상태로 둔다. 기존 v2 파일을 로드 시 자동 덮어쓰지 않고 다음 명시적 저장부터 v3로 기록한다. 기존 v3의 `equipmentSlot=12`는 그대로 `W1`을 뜻하므로 이전 단일 Weapon 저장과 호환된다.
- `[코드/에셋 확인]` ItemDefinition ID 1~5의 기존 총기 정의는 `EquipmentSlot.Weapon`에 호환되고 ID 6 시험 보관함은 `None`을 유지한다. 하나의 Weapon 슬롯에는 이 총기 중 한 개만 장착할 수 있으며 같은 `InventoryItemData`와 단일 `InventoryOwner` 규칙을 사용한다.
- `[코드/에셋 확인]` 프로젝트에는 총기 2D 아이콘과 Humanoid `Pistol_*` 애니메이션 클립은 있지만 실제 총기 3D 모델·프리팹은 없다. 이 항목의 “실제 공격 미연결”은 당시 상태이며, 시험용 공격 판정은 2026-08-22 후속 `## 16`에서 구현했다.
- `[미정]` 이 당시에는 장착 아이템을 실제 공격의 권위 있는 무기로 사용하는 방식, 조준·발사 입력, 총기 3D 표현과 사격 타이밍이 미정이었다. `## 16`의 시험 판정 뒤에도 최종 키·밸런스·표현은 확정하지 않는다.

### 2026-08-21 인벤토리 UI 축소와 드래그 회전

- `[사용자 요구]` 플레이어·장비·외부 인벤토리 UI를 화면 비율 대응 방식으로 기존보다 25% 줄이고, 아이템을 집은 동안 `R`로 회전한다.
- `[코드/프리팹 확인]` PlayerCanvas, InteractableCanvas와 활성 StandardCore의 드래그 Effect Canvas 기준 해상도를 모두 `1280×720`에서 `1706.67×960`으로 바꿨다. 기존 중앙 anchor와 `x=-300/0/+300` 로컬 배치는 유지되며 화면 표시만 정확히 75%가 된다.
- `[코드 확인]` `InventoryUIManager` 한 곳이 드래그 중 `R` 입력을 기존 `StandardCore.SwitchRotate()`에 전달한다. 빈손, 입력 차단 중, UI 닫힘 상태에는 별도 회전 상태를 만들지 않는다.
- `[코드 확인]` R 회전 뒤 I/Escape, 거리 이탈, 저장 전 정리 또는 씬 이동으로 드래그를 취소하면 `CancelDrag()`가 최초 회전값부터 복원한 뒤 원래 소유 컨테이너에 같은 객체를 되돌린다.
- `[사용자 Play Mode 확인]` 드래그 중 R 회전과 실제 배치 판정은 정상 동작함을 확인했다.
- `[원인 확인]` 플레이어와 외부 인벤토리는 각자 독립적인 배치 테두리 View를 갖지만, 기존 코드는 출발 View의 테두리 크기만 갱신했다. 다른 인벤토리 진입 시 도착 View가 기본 `100×100` 또는 이전 크기·색을 재사용하는 표시 오류가 있었다.
- `[코드 확인]` 도착 `StandardStashView.OnCellEnter`가 현재 아이템과 도착 그리드 셀 크기로 테두리 크기를 갱신하고, 다음 드래그 판정에서 색을 반드시 한 번 다시 계산한다. 실제 `StandardStashViewData.CheckInsert` 규칙은 변경하지 않았다.
- `[Play Mode 호출 확인]` 플레이어→상자 `4×3` 아이템은 상자 테두리가 `100×100 → 256×192`, 상자→플레이어 `5×2` 아이템은 `256×192 → 320×128`로 갱신됐고 양쪽 모두 판정색이 기본색에서 변경됐다.
- `[Play Mode 호출 확인]` `4×3` 아이템을 회전한 뒤 다른 인벤토리로 넘겼을 때 테두리가 `192×256`으로 갱신됐으며, 취소 뒤 최초 회전·동일 객체 참조·원래 owner가 모두 복원됐다.

### 2026-08-22 시험용 단일 무기 장착칸

- `[코드/프리팹 확인]` `EquipmentPanelView`에서 활성화된 실제 장비칸은 중복·누락 없는 12개이고 Weapon 셀은 `W1` 정확히 하나다. 예약된 `W2`·`W3` GameObject는 비활성 상태이며 자동 장착 대상에도 포함되지 않는다. 기존 세로 한 줄 대신 활성 슬롯을 2열×6행으로 배치하며 플레이어·장비·외부 패널의 계산된 경계는 서로 겹치지 않는다.
- `[코드/실행 확인]` 기존 총기 ID 1~5는 Weapon에 호환되고 StorageCase ID 6은 거부된다. 빈 Weapon 장착, 이미 점유된 슬롯에 두 번째 총기 거부, 비호환 보관함 거부와 실패 시 원본 owner·위치 복구를 확인했다.
- `[코드/실행 확인]` Weapon 장착 상태를 메모리 `Capture → JSON → Restore`로 왕복했으며 `definitionId=1`, `equipmentSlot=12`, 그리드 중복 없음과 이전 v3 데이터의 빈 Weapon 기본값을 확인했다.
- `[Play Mode 호출 확인]` 생산 `EventSystem` 인터페이스와 `StandardCore` 드래그 경로로 총기 장착, 점유·비호환 드롭 rollback, 유효한 빈 칸으로 해제, 재장착과 저장 캡처를 실행했다. 이동 전후 같은 런타임 아이템 참조와 단일 owner가 유지됐다.
- `[Play Mode 호출 확인]` 장착 상태로 `GameMap1 ↔ GameMapTest`를 3회 왕복했고 shell, Player, Camera, `InventoryUIManager`, EventSystem, `EquipmentLoadoutData`와 장착 무기 객체의 identity가 모두 유지됐다.
- `[사용자 Play Mode 확인]` 실제 Game View에서 UI와 장착 시 애니메이션이 정상 작동함을 확인했다.
- `[미검증]` 실제 사용자 슬롯 F5 저장은 수행하지 않았다.

### 2026-08-22 체력 HUD와 무기 퀵 슬롯 표시

- `[사용자 요구]` 화면 좌상단에는 플레이어 체력을, 하단 중앙에는 최대 3개의 무기 표시칸을 둔다. 빈 활성 무기칸은 맨손 자세이고 무기가 있으면 총 모델 없이도 권총을 든 상체 자세로 구분한다.
- `[상태 소유권]` `PlayerStats` 하나가 현재/최대 체력의 권위 소유자이며 `ApplyDamage`, `RestoreHealth`, `ResetHealth`만 값을 바꾼다. `PlayerHealthHudView`는 `HealthChanged` 완료 통지를 받아 Slider와 `HP 현재 / 최대` 문구만 갱신한다. 현재 체력은 아직 세이브 대상이 아니다.
- `[상태 소유권]` `EquipmentLoadoutData`가 장착 아이템의 원본이고 `PlayerWeaponController`는 활성 무기 번호 1~3만 소유한다. `WeaponQuickSlotHudView`는 두 원본을 관찰하는 파생 표시이며 아이템 복사본을 소유하지 않는다. 활성 번호는 아직 세이브 대상이 아니며 Play 시작 시 1번이다.
- `[코드/프리팹 확인]` 하단 HUD는 1·2·3번 세 칸을 항상 준비하지만, 현재 인벤토리 장비 UI에서 실제로 사용할 수 있는 무기칸은 `W1` 한 칸뿐이다. 따라서 현재 단일 무기를 올리면 반드시 HUD 1번에 표시되고 2·3번은 `EMPTY`로 남는다.
- `[코드/애니메이션 확인]` 기존 locomotion controller의 Base Layer는 유지하고, Body·양팔·양손가락만 포함한 AvatarMask의 `Weapon Upper Body` override layer를 추가했다. 활성 칸에 Weapon이 있으면 기존 `Pistol_Aim_Neutral` 자세의 layer weight를 1로, 비어 있으면 0으로 바꿔 맨손 locomotion으로 돌아간다. 현재는 모든 Weapon 정의가 같은 시험 자세를 사용한다.
- `[코드/실행 확인]` 체력 피해·회복·초기화 통지, 장비 변경 통지, 잘못된 장착의 원자적 거부, 저장 슬롯 12·13·14 왕복과 기존 슬롯 12→`W1` 복원을 확인했다.
- `[Play Mode 호출 확인]` 수정 뒤 보이는 Weapon 셀이 정확히 `W1` 하나이며, 여기에 Handgun을 놓았을 때 HUD가 `[Handgun, EMPTY, EMPTY]`, 활성 번호가 1인 것을 확인했다.
- `[Play Mode 호출 확인]` 체력 75와 `W1` Handgun 상태로 `GameMap1 → GameMapTest → GameMap1` 왕복을 3회 수행했다. Shell, Player, Camera, `PlayerStats`, `InventoryUIManager`, `PlayerWeaponController`, 두 HUD View, Animator와 EventSystem의 런타임 identity가 모두 유지됐고 HUD 표시와 장착 상태도 보존됐다.
- `[검증 한계]` Windows 입력 자동화 도구가 Unity 창에 키를 전달하지 못해 자동화된 실제 숫자키 1~3 입력 검사는 수행하지 못했다. 이번 변경 뒤 Player build도 다시 만들지 않았다.

---

## 14. 도심형 도로·큐브 건물 절차 생성

### 사용자 요구와 범위

- `[사용자 요구]` 현재는 도심 맵의 생성 알고리즘 가운데 도로와 건축물 자리만 구현한다. 건축물은 실제 프리팹 대신 색이 다른 충돌 가능한 Cube로 표시한다.
- `[사용자 요구]` 맵 크기는 매번 정확히 같지 않아도 되며, 정사각 청크 반복처럼 보이지 않도록 간격·교차점·도로와 건물 배치를 불규칙하게 만든다.
- `[사용자 요구]` 랜드마크, 가로수, 폐차, 쓰레기통·자전거, 건물 내부, 상자·적 spawn은 이번 범위에서 제외한다.
- `[사용자 요구]` 지하 던전과 오염 지역은 도심 생성기의 옵션으로 섞지 않고, 각 공간 규칙을 정한 뒤 별도 생성 방식으로 설계한다.
- `[사용자 요구]` 기존 `PersistentGameplayShell`, Player, 인벤토리, 직접 씬 이동, `RaidEntry`, 귀환 포탈과 시험 적 동작은 보존한다.

### 상태 소유권

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | scene-local `ProceduralUrbanMapGenerator` 하나가 현재 seed와 `UrbanMapLayout` 원본을 쓴다. |
| 수명 범위 | `GameMapTest` Scene 수명. Player 셸이나 Application 전역으로 올리지 않는다. |
| 생성·파괴 주체 | 직렬화된 생성기가 `Awake`에서 layout과 회색상자 geometry를 만들고, 씬 unload 때 생성 루트와 런타임 NavMesh가 함께 정리된다. |
| 변경 진입점 | 초기 `Awake → GenerateWithSeed`; 이후 명시적 seed 재생성은 같은 메서드만 사용한다. |
| 포함 관계 | 생성 Ground·도로·건물·경계만 자식으로 소유한다. 기존 `ReturnPortal`과 적은 관찰·배치 보호 참조이며 재부모화하거나 소유하지 않는다. |
| 이전 규칙 | 현재 컨테이너 이전은 없다. 기존 포탈 Transform만 layout의 반대편 노드로 이동한다. |
| 파생 표현 | GameObject geometry와 NavMesh는 불변 layout에서 다시 만들 수 있다. |
| 저장 경계 | 현재 seed와 layout은 저장하지 않는다. seed 영속화는 RaidSession/세이브 정책 확정 뒤 다룬다. |
| 업데이트 주체 | 독립 `Update`가 없다. geometry는 `Awake` 한 번, NavMesh는 `NavMeshSurface.OnEnable` 뒤 `Start` 한 번 생성한다. |

### 현재 구현

- `[코드/씬 확인]` `GameMapTest`에는 `ProceduralUrbanMapGenerator`와 `NavMeshSurface`가 같은 scene-local 루트에 정확히 하나 있다. 기존 `RaidEntry`, `Stage1_ReturnPortal`, legacy `Plane`과 시험 적 Transform을 직렬화 참조한다.
- `[코드 확인]` layout planner는 X/Z 각각 4~6개 블록과 14~20 범위의 가변 간격, 교차점 흔들림을 seed로 만든다. 주 도로 행·열은 유지하고 보조 도로는 전체 그래프 연결성이 유지되는 경우에만 일부 제거한다.
- `[코드 확인]` 전체 생성 루트를 35~55도 회전한다. 도로를 먼저 확정한 뒤 남은 필지를 나누어 높이·색이 다른 Cube 건물을 배치한다.
- `[코드 확인]` 건물은 도로 폭과 setback, `RaidEntry`, 귀환 포탈 및 보호 대상의 여유 공간을 침범하지 않으며 서로 겹치지 않는다. 도로 표시는 collider가 없고, 건물과 외곽 경계는 `Obstacle` collider와 Not Walkable modifier를 가진다.
- `[코드 확인]` 기존 `Plane`은 생성 중 비활성화하고 생성기 파괴 시 원래 활성 상태를 복원한다. 기존 귀환 포탈은 새로 만들지 않고 생성된 반대편 도로 노드로 이동하며 생성 루트의 자식으로 바꾸지 않는다.
- `[원인/수정 확인]` 처음에는 매우 이른 생성기 `Awake`에서 아직 `NavMeshSurface.OnEnable` 등록 전 bake와 `SamplePosition`을 수행해 `NavMeshData`와 source bounds는 있어도 등록된 triangulation이 0개였다. geometry 생성을 `Awake`, 파생 NavMesh build·경로 검증을 `Start`로 분리해 수명주기 원인을 수정했다.
- `[코드 확인]` `NavigationBuildPending`과 `NavigationPathComplete`가 지연된 파생 NavMesh 상태를 구분한다. `RaidEntry`에서 귀환 포탈 접근점까지 `PathComplete`가 아니면 생성 성공으로 검증하지 않는다.
- `[문서 확인]` 후속 적 AI의 불완전 조준, 기억·엄폐·지능 등급, 맵 데이터 계약은 `ai_generation_plan.md`에 예약 설계로만 기록했다. AI 구현 권한이나 자동 다음 작업을 뜻하지 않는다.

### 2026-08-21 검증 결과

- `[코드/실행 확인]` `GameMapTest`에 직렬화된 실제 설정과 기본 설정 각각 256개 seed를 검사했다. 두 경우 모두 256개 layout hash가 전부 달랐고, 동일 seed 재생성 hash는 일치했다.
- `[코드/실행 확인]` 256개 seed 모두 도로 그래프 연결, 건물-도로·건물-보호 지점·건물 간 비중첩을 통과했다. 생성 범위는 폭 `72.1~124.1`, 깊이 `71.8~125.5`, 건물 `7~33`개였다.
- `[코드/실행 확인]` Unity 6000.5.9f1 별도 검증 복사본에서 최종 스크립트가 컴파일됐다. 새 C# 오류는 없었고 외부 환경 에셋의 기존 obsolete 경고만 남았다.
- `[Play Mode 호출 확인]` `GameMapTest` 직접 시작 후 기존 `DirectSceneTravel.TryLoad` 경로로 `GameMap1`에 이동하고, 이어 `GameMap1 → GameMapTest → GameMap1` 왕복을 3회 완료했다. 네 번 생성된 도심 layout 모두 `RaidEntry → ReturnPortal` NavMesh complete path를 가졌다.
- `[Play Mode 호출 확인]` 왕복 전후 `PersistentGameplayShell`, Player, Camera, `InventoryUIManager`, EventSystem의 Entity ID가 유지됐고, 각 항목과 활성 Camera·AudioListener는 하나였다. Player는 매 도착 SpawnPoint에 배치되고 Rigidbody 속도는 0이었다.
- `[Play Mode 호출 확인]` 각 `GameMapTest` 진입에서 생성기·Ground·layout 수와 일치하는 도로·건물·외곽 경계, 비활성 legacy `Plane`, 기존 포탈 위치·collider·tag와 기존 시험 적 1개를 확인했다.
- `[Play Mode 호출 확인]` Play 종료 teardown까지 Error, Exception, Assert는 0개였고 검증 후 `GameMapTest` 씬은 dirty가 아니었다.
- `[미검증]` 실제 키보드 `E`로 포탈 상호작용, `I` 인벤토리 열기, 생성 결과의 Game View 시각 품질과 Windows Player build는 이번 자동 호출 검증에서 수행하지 않았다. 기존 수동 입력 검증을 최종 사용자 확인으로 대체하지 않는다.

---

## 15. 3D 픽셀아트 URP 시험 효과

### 사용자 요구와 범위

- `[사용자 요구]` Eduardo Schildt의 Godot `3DPixelArt_Tutorial`과 영상에서 보인 3D 픽셀아트 화면 기법을 현재 Unity 프로젝트에 적용해 본다.
- `[확정 범위]` 이번 단계는 월드 화면의 저해상도 포인트 샘플링과 깊이·노멀 윤곽선 시험이다. 모델 복셀화, 전체 머티리얼 교체, 최종 팔레트·색보정, 모바일 설정과 게임플레이는 변경하지 않는다.
- `[보존]` 기존 PC Renderer의 SSAO, `PersistentGameplayShell`, gameplay Camera 동일 인스턴스, 씬 흐름과 모든 Overlay UI를 유지한다.

### 현재 구현

- `[코드/에셋 확인]` `Assets/Rendering/PixelArt`에 Unity 6 URP용 전체화면 셰이더, Material과 `PixelArtRendererFeature`를 분리했다. Godot 씬·모델·텍스처·셰이더 파일은 복사하지 않고 기법만 독립 구현했다.
- `[코드 확인]` 렌더 기능은 Unity가 유지하는 `FullScreenPassRendererFeature`를 그대로 사용하고 Play Mode/Player 빌드의 `CameraType.Game`만 허용한다. Scene View와 편집 상태의 AuthoringPreviewCamera는 처리하지 않으며, 메뉴·로딩을 포함한 실제 런타임 Game 카메라는 같은 스타일을 사용한다.
- `[에셋 확인]` `PC_Renderer`에는 기존 SSAO와 픽셀아트 기능이 각각 하나씩 있고 null/중복 feature가 없다. 픽셀아트 기능은 After Post Processing에서 Color 복사와 Depth/Normal 입력을 사용한다.
- `[UI 경계]` gameplay Canvas 6개는 모두 `Screen Space Overlay`이므로 카메라 후처리 대상이 아니며, 월드만 픽셀화되고 HUD·인벤토리는 원래 화면 해상도를 유지한다.
- `[설정]` 기본 `Pixel Size=6`이며 깊이 외곽선, 노멀 하이라이트, 임계값과 강도는 `PixelArtFullscreen.mat`에서 조절한다. `PC_Renderer`의 `3D Pixel Art (Game Cameras)` 활성 체크로 원본 화면과 즉시 전환할 수 있다.
- `[문서/라이선스]` 폴더의 README에 조절법과 제한을 기록했고, 로컬 튜토리얼에 포함된 Eduardo Schildt의 MIT 고지와 참고 링크는 `ThirdPartyNotices.txt`에 보존했다.

### 2026-08-22 검증 결과

- `[코드/셰이더 확인]` Unity 6000.5.9f1에서 C#이 컴파일됐고 픽셀아트 셰이더는 supported=true, pass=1, ShaderUtil 메시지 0개였다. gameplay Camera가 직교 투영이므로 `unity_OrthoParams`에 따라 URP의 `LinearDepthToEyeDepth`와 원근용 `LinearEyeDepth`를 구분한다.
- `[렌더 확인]` 1024×768 동일 카메라 렌더를 기능 활성/비활성으로 각각 캡처했다. 활성 화면은 정사각형 픽셀 격자와 깊이·노멀 경계가 나타났고, 비활성 화면은 기존의 부드러운 원본 렌더로 복귀했다. 직교 depth 분기를 반영한 뒤 실제 orthographic gameplay Camera로 다시 캡처해 효과가 유지됨을 확인했다.
- `[Play Mode 호출 확인]` `GameMap1 → GameMapTest → GameMap1` 왕복 뒤 shell과 gameplay Camera Entity ID가 동일했다. 각 씬에서 픽셀 feature 1개 활성, 활성 Game Camera 1개, EventSystem 1개, Overlay Canvas 6개를 확인했다.
- `[편집 상태 확인]` Play Mode 종료 뒤 활성 씬은 dirty가 아닌 `GameMap1`이며, Renderer의 전체 feature 2개 중 픽셀 feature는 정확히 하나이고 Material·Shader 참조가 유효하다.
- `[기존 에셋 문제]` 전체 에셋 재임포트 때 `Assets/AnimeNaturalEnvironment/Shaders/ASFolliage.shader`의 Unity 6 중복 keyword 오류 2개와 기존 경고가 다시 보고됐다. 픽셀아트 셰이더 메시지는 0개이며, 요청 밖 외부 에셋을 임의 수정하지 않았다.
- `[성능 경계]` 현재 방식은 실제 저해상도 RT 렌더가 아니라 원본 해상도 후처리다. 픽셀당 색상 1회와 깊이/노멀 각 5회 샘플 및 색상 복사가 필요하고 같은 픽셀 블록에서도 계산이 반복되므로 시각적 픽셀화가 자동 성능 향상을 뜻하지 않는다.
- `[미검증]` 실제 사용자 모니터 해상도별 Game View 플레이 감각, 이동 중 픽셀 shimmer, UI를 연 상태의 육안 확인, 4K GPU Profiler 비용과 Windows Player build는 아직 사용자 조율·후속 검증 대상이다.

### 2026-08-22 사용자 요청에 따른 임시 비활성화

- `[사용자 요구]` 현재 3D 픽셀아트 결과는 사용하지 않되 파일을 삭제하거나 커밋을 되돌리지 않고 Renderer Feature만 비활성 상태로 남긴다.
- `[에셋 확인]` `PC_Renderer`의 `3D Pixel Art (Game Cameras)`는 정확히 하나 존재하며 `Active=false`로 저장됐다. 기존 SSAO, Shader, Material, 조절값과 라이선스 문서는 유지한다.
- `[Play Mode 렌더 확인]` 비활성 상태의 persistent gameplay Camera를 1024×768로 직접 렌더했고 픽셀 격자·윤곽선 후처리 없이 기존의 부드러운 3D 화면이 출력됐다. 검증 중 shell과 활성 Game Camera는 각각 하나였다.
- `[복구 방법]` 추후 다시 시험하려면 `PC_Renderer`의 같은 Renderer Feature를 활성화하면 되며, 새 코드·씬·프리팹 수정은 필요하지 않다.

---

## 16. 시험용 무기 레이캐스트 공격과 좀비 사망

### 사용자 요구와 현재 범위

- `[사용자 요구]` 무기를 장착한 상태에서 좌클릭으로 탄약 소모 없는 시험용 Raycast 공격을 한다. 단발은 클릭 한 번당 한 발, 자동은 누른 동안 정의된 연사력에 맞춰 반복하며 단발도 같은 연사 쿨다운을 받는다.
- `[사용자 요구]` 현재 모든 총기 피해는 기능 확인용 `35`로 통일하고, 기존 최대 체력 100 좀비가 세 번째 적중에 죽는 것까지 연결한다.
- `[사용자 요구]` 하체에 전후좌우·대각 방향 locomotion 애니메이션 세트가 없으므로 마우스 방향 캐릭터 회전, 후진·strafe, 조준·발사 애니메이션은 이번 범위에서 건너뛴다. 기존 WASD 방향 회전과 장착 상체 pose는 보존하고 판정만 마우스 방향을 사용한다.
- `[사용자 요구]` 발사 여부와 실제 적중 여부를 귀로 구분할 수 있도록 유효한 발사에는 짧은 “뿅” 계열 소리, 피해가 적용된 적중에는 별도의 둔탁한 소리를 사용한다. 무료로 받을 수 있고 이용 조건이 명확한 원본 파일을 사용한다.
- `[제외 범위]` 탄약, 재장전, 반동, 탄퍼짐·명중률, 총기 3D 모델, VFX, 발사 애니메이션, 적 음성, 3D 공간음향, 최종 사운드 디자인, 시체·드롭, 부활·respawn과 정식 전투 밸런스는 구현하지 않는다.

### 상태 소유권과 호출 흐름

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | 장착 원본은 `EquipmentLoadoutData`, 활성 번호는 `PlayerWeaponController`, 공유 발사 정의는 `ItemDefinition`, 런타임 무기 아이템별 다음 발사 가능 시각은 `PlayerWeaponAttackController`의 해당 `WeaponFireCadence`, 적 현재 체력·생존·사망 전이는 해당 개체의 `EnemyStats` 하나가 쓴다. |
| 수명 범위 | `ItemDefinition`은 Project/Application 공유 정의, cadence는 runtime `InventoryItemData`를 key로 한 persistent Player Entity의 Play Session 상태, 적 체력과 사망은 Enemy Entity 상태다. |
| 생성·파괴 주체 | `PlayerWeaponAttackController`, `WeaponRayOrigin`, `WeaponAttackAudioFeedback`와 전용 `AudioSource`는 `PersistentGameplayShell` Player 프리팹과 함께 한 번 생성·보존된다. `EnemyStats`, `EnemyDeathHandler`와 피격 Trigger는 좀비 프리팹 인스턴스와 함께 생성·정리된다. |
| 변경 진입점 | `Update`의 입력 → `ProcessFireInput` → `WeaponFireCadence.TryConsume` → Player 원점 Raycast → `IDamageable.ApplyDamage(DamageContext)` → `EnemyStats`의 `> 0 → 0` 전이 → `Died` 완료 통지 → `EnemyDeathHandler` 순서다. |
| 포함 관계 | 공격기는 장착 정의·Camera·발사 원점·EventSystem을 참조하지만 장착이나 체력을 소유하지 않는다. 사망 처리기는 `EnemyStats`를 관찰하고 Patrol·Collider·외형을 정리하지만 생존 상태를 소유하지 않는다. |
| 이전 규칙 | 컨테이너 이전은 없다. 무기 교체 뒤 다음 입력은 새 활성 아이템의 정의와 cadence를 읽는다. 같은 런타임 무기를 다시 선택하면 그 무기의 남은 쿨다운을 이어가며, 다른 무기의 RPM 대기시간을 잘못 공유하지 않는다. |
| 파생 표현 | 기존 상체 장착 pose와 무기 HUD는 장착 상태의 파생 표현이다. 발사음은 cadence가 허용한 실제 발사, 적중음은 `DamageResult.WasApplied`의 파생 표현이다. 적 외형·순찰·피격 Collider 활성 상태는 사망 완료 뒤 정리되는 표현이며 체력 원본이 아니다. |
| 저장 경계 | 총기 시험 수치는 definition asset에서 다시 조회한다. 다음 발사 시각, 적 현재 체력·사망 상태는 현재 세이브하지 않으며 총기 수치도 정식 밸런스 확정이 아니다. |
| 업데이트 주체 | `PlayerWeaponAttackController.Update` 하나만 좌클릭을 읽는다. cadence는 매 프레임 감소값을 복사하지 않고 현재 시각과 다음 허용 시각을 비교한다. `EnemyStats`와 `EnemyDeathHandler`에는 독립 `Update`가 없다. |

### 현재 구현

- `[코드/프리팹 확인]` persistent Player에는 직렬화 참조가 완성된 `PlayerWeaponAttackController` 하나와 로컬 `(0, 2, 0)`의 `WeaponRayOrigin` 하나가 있다. 씬별 공격기나 Camera 검색 경로를 추가하지 않았다.
- `[코드 확인]` 단발은 `Input.GetMouseButtonDown(0)`, 자동은 `Input.GetMouseButton(0)`을 사용한다. 둘 다 런타임 무기별 `WeaponFireCadence.TryConsume`과 `60 / RPM` 간격을 통과해야 같은 `ProcessFireInput`·Raycast 경로를 사용한다. 정상적인 프레임 반올림 오차는 다음 예정 시각 기준으로 보정하지만 긴 지연 뒤 누적 발사를 한꺼번에 보상하지 않는다.
- `[코드 확인]` Camera의 mouse screen ray는 `WeaponRayOrigin` 높이의 수평면과 교차해 탑다운 조준점을 계산한다. 실제 Physics ray는 Camera가 아니라 `WeaponRayOrigin`에서 그 점 방향으로 Y를 제거한 XZ 방향에 발사된다.
- `[코드 확인]` `RaycastNonAlloc` 고정 버퍼를 발사 때만 사용하고 32칸이 가득 찬 조밀한 예외에서만 `RaycastAll`로 전체 후보를 다시 받아 가장 가까운 차폐 판정을 보장한다. Player 자신의 Collider와 피격 대상이 아닌 Trigger는 무시하고, 실제 Collider 장애물 또는 가장 가까운 `IDamageable`은 순서대로 막거나 피해를 받는다.
- `[코드 확인]` 열린 플레이어·장비·외부 인벤토리, 씬 이동용 `InputBlocked`, 일시정지와 UI pointer 위에서는 공격 입력을 소비하지 않는다. 빈 활성 무기칸에서도 공격·쿨다운을 만들지 않는다.
- `[코드/프리팹 확인]` persistent Player에 `WeaponAttackAudioFeedback`와 2D `AudioSource`가 각각 하나 있다. cadence를 통과한 `EmitRaycastShot` 시작에서 발사음을 재생하고, `ApplyDamage`가 반환한 `DamageResult.WasApplied`가 참일 때만 적중음을 추가 재생한다. 오디오 컴포넌트는 공격 성립이나 피해를 판정하지 않는다.
- `[에셋/라이선스 확인]` 발사음은 Kenney `Sci-Fi Sounds 1.0`의 `laserSmall_000.ogg`(0.239초), 적중음은 `Impact Sounds 1.0`의 `impactSoft_heavy_000.ogg`(0.505초)를 사용한다. 두 공식 팩 모두 CC0이며 선택 파일의 원본 이름, 출처, SHA-256과 이용 조건을 `Assets/Audio/Combat/Kenney/LICENSE.md`에 기록했다.
- `[에셋 확인]` 두 OGG는 mono, PCM, Decompress On Load, preload 설정으로 import한다. 매 발사 파일 로드나 AudioSource 생성 없이 persistent AudioSource 하나의 `PlayOneShot`으로 겹쳐 재생한다.
- `[코드/프리팹 확인]` 좀비의 실제 이동 자식 `ZombieAgent`에는 center `(0, 2, 0)`, height `4`, radius `0.6`인 Trigger CapsuleCollider가 하나 있다. Root의 `EnemyStats`가 부모 경로의 `IDamageable` 권위자다.
- `[코드 확인]` `EnemyStats.ApplyDamage`가 현재 체력을 0~최대로 제한하고, 살아 있는 상태의 `> 0 → 0` 전이에서 `isDead`를 먼저 확정한 뒤 `Died`를 정확히 한 번 통지한다. `Initialize`도 한 개체당 한 번만 성공하므로 죽은 뒤 피해·회복·Reset·재초기화는 체력만 되살리는 암묵적 부활을 만들지 않는다.
- `[코드/프리팹 확인]` `EnemyDeathHandler`는 `Died` 뒤 기존 `EnemyPatrol`, 피격 CapsuleCollider와 `ZombieAgent` 외형을 비활성화한다. Root와 죽은 `EnemyStats`는 남겨 현재 사망 상태를 유지하며 시체·드롭·Destroy 정책은 후속으로 남긴다.
- `[조사 확인]` 로컬 RimWorld 1.6.4871 코드는 단순히 “상태이상 함수가 직접 사망 호출”하는 구조가 아니라 피해·Hediff 적용 뒤 `Pawn_HealthTracker.CheckForStateChange/ShouldBeDead`가 중앙 판정하고 `Pawn.Kill`이 한 번의 사망 처리를 조정한다. 현재 프로젝트에는 거대한 Hediff 체계를 복제하지 않고 공통 피해 진입점, 단일 체력 권위자, 중앙 0 전이와 사망 후 통지만 적용했다.
- `[후속 확장 경계]` 현재 cadence registry는 공격기가 비활성화될 때 전체 정리되며, 실행 중 발사한 runtime 무기 참조는 그때까지 유지한다. 현재 3칸 시험 규모에는 문제가 없지만 대량 무기 생성·폐기가 생기면 아이템 수명 종료 통지에 맞춘 개별 제거를 함께 설계한다.
- `[후속 확장 경계]` 현재 좀비는 serialized `EnemyDefinition`을 가진 정의별 프리팹이라 `Awake`에서 1회 초기화된다. 미래 범용 spawn 프리팹은 definition을 비워 두고 spawn 직후 최초 `Initialize`를 호출하며, 이미 초기화된 개체의 definition을 교체하는 방식은 사용하지 않는다.

### 시험용 총기 정의값

| Definition | 발사 방식 | RPM | 피해 | 사거리 |
|---|---:|---:|---:|---:|
| Handgun | 단발 | 300 | 35 | 30 |
| Handgun2 | 단발 | 300 | 35 | 30 |
| Rifle | 자동 | 600 | 35 | 30 |
| SniperRifle | 단발 | 60 | 35 | 30 |
| SubmachineGun | 자동 | 720 | 35 | 30 |

위 값은 기능 검증용이며 이름, 최종 분류와 전투 밸런스를 확정하지 않는다.

### 2026-08-22 검증 결과와 한계

- `[코드/실행 확인]` 단발 첫 press 허용, 쿨다운 내부 press 거부, 쿨다운 이후 held만으로 반복 거부, 새 press 허용을 검사했다. 자동은 첫 held 즉시 허용, RPM 내부 거부, 이후 held 허용, 긴 프레임 지연 뒤 한 발만 허용, release 거부를 통과했다.
- `[코드/실행 확인]` 후속 리뷰에서 확인된 공용 cooldown과 프레임 지연 누적을 수정했다. runtime `InventoryItemData` 두 개가 서로 다른 cadence를 사용하고 같은 아이템은 기존 cadence를 유지한다. 30 FPS에서 720 RPM을 3초 모사했을 때 허용 오차 안의 36발이 나왔으며, 1초 hitch 뒤 같은 timestamp의 누적 발사는 거부했다.
- `[코드/실행 확인]` 최대 체력 100의 독립 `EnemyStats`에 피해 35를 세 번 적용해 `100 → 65 → 30 → 0`, 세 번째만 `CausedDeath=true`, `Died` 1회, 네 번째 피해 거부와 죽은 뒤 회복·Reset 거부를 확인했다.
- `[Play Mode 호출 확인]` 실제 persistent Player의 빈 3번 슬롯과 `InputBlocked`에서는 발사를 거부했다. W1 Handgun은 press/held/cooldown 순서, W2 Rifle은 held/RPM 순서로 Player 원점 Raycast를 실행했고 두 시험 좀비 모두 35 피해 세 번째에 한 번 죽었다. 사망 뒤 Patrol·피격 Collider·외형 비활성 및 추가 피해·중복 사망 없음도 확인했다.
- `[Play Mode 호출 확인]` 최종 재검증에서는 기존 장비 상태를 보관하고 장비 소유 API로 시험용 W1 Handgun과 W2 Rifle을 임시 장착했다. `권총 1발 → 권총 조기 재발 거부 → 같은 시각 소총 첫 발 허용 → 권총 재선택 시 남은 cooldown 유지 → 소총 다음 허용 시각의 세 번째 총 피해로 사망`을 통과했고, `Died`와 `EnemyDeathHandler`는 한 번만 실행됐다. 시험 장비, 활성 번호, Player·Camera 위치, 입력 차단과 EventSystem 상태를 모두 원래 값으로 복구한 뒤 Edit Mode로 종료했다.
- `[Play Mode 호출 확인]` 오디오 재검증에서 적이 없는 유효 발사는 발사 클립만 활성 재생했고, 발사 클립을 시험 중 잠시 제외한 상태에서 35 피해가 실제 적용된 적중은 적중 클립만 활성 재생했다. 두 클립을 정상 복구한 뒤 추가 두 발로 `100 → 65 → 30 → 0`, 사망·정리 1회를 다시 통과했으며 시험 장비와 모든 런타임 상태를 원복했다.
- `[검증 과정]` 최초 재검증 하네스 2회는 비활성 `Preview Camera`를 gameplay Camera로 고른 전제와 빈 런타임 장비칸을 고정 W1/W2로 가정해 실패했다. 실제 `Main Camera`와 장비 API를 사용하도록 하네스를 바로잡은 뒤 위 최종 검증이 통과했으며, 이 실패는 프로젝트 컴파일·전투 코드 오류가 아니었다.
- `[Console 기준선]` 최종 import/compile 뒤 Error/Exception/Assert는 작업 전과 같은 6개다. 이전 Camera Capture 도구 2개, 이전 SerializedProperty 도구 2개, 외부 `AwaiiStudio/ASFolliage` shader keyword 2개이며 신규 전투 오류는 없다.
- `[코드/씬 확인]` `GameMapTest`를 Preview Scene으로 열어 기존 좀비 프리팹 인스턴스가 새 `EnemyDeathHandler`와 Trigger CapsuleCollider를 상속함을 확인했고, 검사 뒤 원래 활성 `GameMap1`, dirty 상태와 Edit Mode를 그대로 복원했다.
- `[검증 한계]` Windows 입력 자동화가 Unity 창 캡처에서 `SetIsBorderRequired` 시스템 인터페이스 오류로 중단돼 실제 좌클릭의 `Update → Input.GetMouseButtonDown/GetMouseButton` 경계는 자동 조작하지 못했다. 공개 공격 진입점의 Play Mode 호출과 공식 Unity 입력 의미·컴파일까지만 확인했으며 사용자 실제 Game View 좌클릭 확인으로 승격하지 않는다.
- `[미검증]` 실제 Game View에서 권총 3회 클릭과 자동소총 hold의 손 입력·주관적 음색/음량 확인, 인벤토리를 연 채 실제 클릭, 벽 뒤 적 차폐, 씬 왕복 중 공격 cooldown·오디오와 Windows Player build는 이번 범위에서 수행하지 않았다.
