# Unity 개발 진행 기록

**마지막 확인:** 2026-08-27
**확인 환경:** Unity 6000.5.9f1, 활성 Build Target `StandaloneWindows64`, 활성 씬 `GameMap1`; 격리 저장 경로의 Play Mode 호출로 정상 생환→자동 기지 정산→확인 흐름을 검증
**문서 역할:** 구현·검증 증거와 변경 이력을 보존하는 진행형 인계 문서다. 최신 구현 상태와 재개방 조건은 `docs/ai/CURRENT_STATE.md`, 장르 방향·플레이 판단·알고리즘 불변조건은 `extraction_survival_gameplay_contract.md`, 게임 요소·기능·콘텐츠·UI/UX는 `game_design_document.md`, Stage 의존성과 구현 순서는 `extraction_survival_game_design_dev_plan.md`를 따른다.

## 문서 사용 규칙

- `[Play Mode 확인]`: 실제 Play Mode 프레임·씬 수명주기에서 확인했다.
- `[Play Mode 호출 확인]`: Play Mode에서 런타임 호출 경로로 확인했으며 실제 키 입력은 우회했다.
- `[사용자 확인]`: 사용자가 실제 사용 결과를 확인했다. 관련 구현이 바뀌지 않았다면 같은 확인을 자동 반복하지 않는다.
- `[코드/씬 확인]`: 코드, 씬 또는 프리팹의 현재 구성을 확인했다.
- `[코드 확인]`: 실행 경로는 확인했지만 해당 경계를 새로 Play Mode 검증하지 않았다.
- `[사용자 요구]`: 사용자가 원하는 동작으로 직접 설명했다.
- `[사용자 확인 필요]`: 사용자의 설명이 현재 구현 설명인지, 앞으로 구현할 확정 요구인지 한 번 더 확인해야 한다.
- `[미구현]`: 현재 코드에 없다.
- `[후속 후보]`: 자동 구현 대상이 아니며 사용자가 요청한 경우에만 진행한다.
- `스크립트_사용_분석.md`는 persistent gameplay shell 도입 전의 역사적 기록이다. 현재 Player·Camera·UI 위치의 근거로 사용하지 않는다.

---

## 0. 현재 상태 인덱스 위치

현재 구현·검증·재개방 조건의 단일 인덱스는 `docs/ai/CURRENT_STATE.md`로 이동했다. 구현, 버그, 검증 또는 다음 기능 선택 시 그 파일을 먼저 읽는다.

이 문서의 1절 이후는 상세 증거와 과거 이력이다. 과거의 `당시 미구현`, `후속`, `미검증`, `다음 Stage`를 현재 작업 목록으로 사용하지 않으며, 현재 상태와 충돌하면 `CURRENT_STATE.md`를 우선한다. 이번 작업에서 직접 확인한 Unity·코드 사실이 상태 인덱스와 다르면 원인을 확인하고 상태 인덱스를 갱신한다.

---

## 1. 현재 완료된 기반

- `[Play Mode 호출 확인]` `GameMap1`에서 `GameMapTest` 원정을 시작하고 귀환 Cube로 생환을 확정하면 기존 검은 전환 뒤 자동으로 기지 정산까지 진행하며, 정산 완료 뒤 `확인` 하나로 기지 입력을 연다.
- `[Play Mode 확인]` 이 직접 왕복은 `MainMenuScene`과 `GameLoadingScene`을 거치지 않는다.
- `[Play Mode 확인]` `PersistentGameplayShell` 하나가 실제 Player, 외형, Player 구성 스크립트, Camera, Inventory UI/Core/View와 EventSystem을 같은 인스턴스로 유지한다.
- `[코드/씬 확인]` 두 게임플레이 씬에는 scene-local 런타임 Player/gameplay Camera/Inventory UI/EventSystem 복사본이 없다. 편집 상태 Game View용 `EditorOnly` Preview Camera만 씬마다 1개 존재한다.
- `[Play Mode 확인]` Player 인벤토리는 왕복 중 동일 객체 그래프로 유지된다. 기지에서 사용하는 단일 슬롯 디스크 세이브/로드 프로토타입도 연결되어 있다.
- `[코드/씬 확인]` 현재 연결된 상호작용 대상은 `GameMap1`의 Chest 2개, 맵 선택 Cube 1개와 시험 Merchant Cube 1개, `GameMapTest`의 귀환 Cube 1개다.
- `[Play Mode 확인]` Freya 인간형 외형은 Humanoid Avatar와 Idle/Walk/Run 로코모션에 연결되어 더 이상 T포즈로 서 있지 않는다.
- `[코드/씬 확인]` 이동 중 Left Shift 또는 Right Shift를 누르면 걷기 속도의 정확히 1.3배로 달리는 설정이 `PersistentGameplayShell`의 기존 `PlayerMovement`에 연결되어 있다.

---

## 2. 사용자가 설명한 상호작용 계약

아래는 다음 기능에서 지향할 동작을 정리한 것이다. 현재 구현과 다른 항목은 4장에 따로 표시한다.

1. `[사용자 요구]` Player가 상호작용 오브젝트의 범위에 들어가면 `[E]` 안내가 활성화된다.
2. `[사용자 요구]` Chest처럼 지속 UI가 있는 상호작용 중에도 Player는 움직일 수 있다.
3. `[사용자 요구]` 활성 상호작용 오브젝트의 허용 거리에서 벗어나면 해당 오브젝트와 연결된 UI가 자동으로 닫힌다.
4. `[사용자 요구]` 주변에 대상이 여러 개면 거리상 가장 가까운 하나만 E 입력 대상이 된다.
5. `[사용자 요구]` Chest UI가 실제로 열린 동안에만 처음 연 Chest를 상호작용 대상으로 유지한다.
6. `[사용자 요구]` 유지 중인 Chest의 거리 판정도 처음 연 그 Chest를 기준으로 한다.
7. `[사용자 요구]` Chest, Portal, Map Terminal 같은 개별 기능은 공통 상호작용 진입 경로를 재사용하고, 각 대상은 자신의 실제 행동만 구현한다.

주의: 5번은 닫힌 대상을 계속 고정한다는 뜻이 아니다. Chest UI가 정상적으로 닫히는 즉시 유지 상태가 끝나며, 다음 프레임 또는 다음 E 입력의 검색에서 다시 가장 가까운 대상을 고른다.

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
  ├─ MerchantInteractable
  ├─ MapTerminalInteractable
  └─ ReturnPortalInteractable
```

현재 코드에는 `IInteractable` 인터페이스가 없으며, 공통 계약은 `abstract class Interactable`이다.

| 책임 | 현재 소유자 | 재사용 여부 |
|---|---|---|
| E 입력 | `PlayerInteractor` | 모든 현재 대상이 공유 |
| 주변 대상 검색과 가장 가까운 하나 선택 | `PlayerInteractor` | 지속 UI가 열린 대상이 없을 때 모든 현재 대상이 공유 |
| 열린 지속 상호작용 대상 유지·취소 조정 | `PlayerInteractor` → 해당 `Interactable` | 공통 흐름을 사용하고 현재 Chest와 Merchant가 활성 세션을 제공 |
| 기본 활성 상태 검사 | `Interactable.CanInteract` | 모든 현재 대상이 공유 |
| 안내 문구 | 각 `Interactable.InteractionPrompt` | 표시 방식은 공통, 문구는 개별 |
| Chest·Merchant UI 열기/닫기 | 각 `Interactable` → `InventoryUIManager` | 공통 외부 인벤토리 수명 경계를 사용하고 Storage·Merchant 규칙만 구분 |
| 맵 선택 UI | `MapTerminalInteractable` → `MapSelectionOverlay` | 현재 단일 터미널용 |
| 씬 이동 요청 | `DirectSceneTravel.TryLoad` | 터미널과 포탈 경로가 공유 |
| 씬 이동 전 UI·입력 정리 | `PersistentGameplayShell.PrepareForTravel` | 모든 직접 씬 이동이 공유 |

### PlayerInteractor의 실제 탐색 방식

- `[코드 확인]` Player 중심 반경 3m를 `Physics.OverlapSphereNonAlloc`로 매 프레임 검색한다.
- `[코드 확인]` 모든 Physics Layer와 Trigger를 포함한다.
- `[코드 확인]` Collider에서 부모 방향으로 `Interactable`을 찾는다.
- `[코드 확인]` 후보 오브젝트의 Transform pivot까지의 거리를 비교해 하나를 고른다.
- `[코드 확인]` 후보 버퍼는 32 Collider로 고정되어 있다.
- `[코드 확인]` 지속 UI가 열린 대상이 없으면 E 입력 직전에도 검색을 다시 수행해 그 순간의 가장 가까운 대상을 실행한다.
- `[코드 확인]` Chest UI가 열린 동안에는 해당 Chest가 활성·범위 안인 한 그 대상을 유지한다. UI가 닫히면 다음 검색부터 즉시 최근접 선택으로 복귀한다.
- `[코드 확인]` E 키와 탐색 반경은 `PersistentGameplayShell.prefab`의 `PlayerInteractor`에 각각 `E`, `3`으로 직렬화되어 있다.
- `[코드 확인]` Chest 열기와 자동 닫기도 같은 `PlayerInteractor`의 반경 판정을 사용하며 `InventoryUIManager`에는 별도의 거리 원본이 없다.
- `[코드 확인]` 안내는 정식 UGUI가 아니라 `OnGUI` 디버그 박스다.

즉, “각 오브젝트가 따로 Player 거리를 감지한다”기보다는 **Player 한 곳이 모든 후보를 중앙 검색하고, 각 오브젝트는 자신의 활성 가능 여부와 행동을 제공한다**가 정확하다.

---

## 4. 사용자 설명과 현재 구현의 대조

| 항목 | 현재 판정 | 근거 |
|---|---|---|
| 범위 안에서 E 안내 활성화 | 코드상 충족, 시각 미검증 | 가장 가까운 `currentInteractable` 하나의 OnGUI prompt를 표시하는 코드 확인 |
| 대상이 여러 개면 가장 가까운 하나 선택 | Play Mode 호출 충족 | 지속 UI가 없을 때 중앙 거리 비교 후 하나만 실행; 실제 E 키 입력은 미검증 |
| Chest UI가 열린 동안 이동 가능 | 코드상 허용, 실제 WASD 미검증 | `PlayerMovement`를 비활성화하지 않으며 런타임에도 enabled 상태 유지 |
| 열린 Chest에서 3m 초과 시 UI 자동 닫힘 | Play Mode 충족 | `currentOpenedChest` 기준 거리 이탈 후 Update 프레임에서 두 패널 닫힘 확인 |
| Chest UI가 열린 동안 처음 대상을 유지 | Play Mode 호출 충족 | Chest A가 열린 동안 B가 더 가까워져도 두 번째 호출은 A를 닫음 |
| 닫힌 뒤 최근접 선택으로 복귀 | Play Mode 호출 충족 | A가 닫힌 직후 다음 호출에서 더 가까운 B가 선택되어 열림 |
| 활성 Chest의 거리 기준은 처음 연 Chest | Play Mode 충족 | 선택과 UI 자동 종료가 모두 같은 `PlayerInteractor` 반경과 열린 Chest를 기준으로 함 |
| 모든 상호작용이 이동 중 지속 가능 | 미충족이 아니라 종류별 정책 | Chest는 이동 가능, Map Selection은 modal이라 이동 잠금, Portal은 생환 결과를 확정하고 결과 UI로 입력 잠금 |
| 거리 이탈 시 모든 상호작용 UI 자동 닫힘 | Chest에만 해당 | Map Selection은 이동이 잠기며 거리 종료 없음, Portal의 결과 UI는 원정 종결 화면이라 거리 종료 대상이 아님 |

### 2026-08-20 Play Mode 호출·상태 확인

1. `[Play Mode 호출 확인]` Player를 `Chest` 가까이에 배치한 뒤 `PlayerInteractor.TryInteract()` 런타임 경로를 호출하자 Player/외부 인벤토리 패널이 열렸고 `PlayerMovement`는 활성 상태였다. 실제 E 키와 WASD 축 입력은 직접 검증하지 않았다.
2. `[Play Mode 호출 확인]` 그 UI가 열린 상태로 Player를 `Chest (1)` 가까이에 배치해 같은 호출 경로를 다시 실행하자 현재 대상이 `Chest (1)`로 바뀌었다. 공통 active-target lock은 없다는 것이 확인됐다.
3. `[Play Mode 확인]` Chest UI를 연 뒤 Player를 해당 Chest에서 3m 밖으로 배치하고 Update 한 프레임을 진행하자 외부 패널과 Player 인벤토리 패널이 모두 자동으로 닫혔다.

### 2026-08-23 겹친 Chest 회귀 수정·검증

1. `[원인 확인]` 기존 `PlayerInteractor`가 매 프레임과 E 입력 직전에 무조건 최근접 대상을 다시 골라, Chest A의 UI가 열린 상태에서도 더 가까운 Chest B로 전환할 수 있었다.
2. `[코드 확인]` `Interactable`의 공통 계약에 활성 세션 확인과 취소 진입점을 추가했고, Chest만 실제 열린 UI를 활성 세션으로 보고한다. Portal과 Map Terminal은 기본 비지속 정책을 유지한다.
3. `[Play Mode 호출 확인]` A를 연 뒤 두 Chest 범위가 겹치면서 B가 더 가까운 위치로 이동해 호출했을 때 A가 유지되어 닫혔다. A가 닫힌 직후 다음 호출에서는 B가 선택되어 열렸다.
4. `[Play Mode 호출 확인]` 빠른 열기→닫기→열기, 열린 대상 비활성화, 범위 이탈 취소가 모두 통과했다.
5. `[Play Mode 확인]` Chest를 연 뒤 3.5m 떨어진 위치로 옮기고 실제 Update 프레임을 진행하자 외부 UI가 자동으로 닫혔다.
6. `[코드 확인]` 드래그 복구 실패로 UI 닫기가 거부되면 기존 대상 참조도 유지해, 열린 UI와 상호작용 대상의 원본이 갈라지거나 다른 Chest로 전환되지 않는다.

---

## 5. 개별 상호작용 구현

### Chest

- `GameMap1`의 `Chest`, `Chest (1)`에는 각각 `Chest`와 `ChestInteractable`, 활성 BoxCollider가 있다.
- 두 Collider는 Trigger가 아닌 solid Collider다.
- `ChestInteractable.Interact`는 같은 Player의 `InventoryUIManager.TryToggleChestInventory(chest)`를 호출한다.
- 열 때 Player 인벤토리와 해당 외부 인벤토리를 함께 표시한다.
- 같은 Chest에서 다시 E를 누르면 모두 닫는다.
- Chest UI가 열린 동안에는 다른 Chest가 더 가까워져도 처음 연 Chest를 유지한다. 정상적으로 닫힌 뒤 다음 E부터 다시 최근접 Chest를 선택한다.
- `InventoryUIManager`가 열린 Chest를 `currentOpenedChest`로 기억하고 매 프레임 별도 거리 검사를 한다.
- 거리 초과 시 드래그를 취소하고 case popup을 정리한 뒤 Player/외부 인벤토리를 모두 닫는다.
- `GameMap1`의 두 Chest 오브젝트는 scene-local View이지만, 각각 `core:home/chest_a`, `core:home/chest_b`라는 stable placed ID를 가진다. 실제 6×5 내용은 persistent `GameManager`가 소유한 `BaseFurnitureStateStore`에 있으며 씬 재진입 때 새 Chest View에 같은 런타임 grid를 다시 연결한다.
- `GameMapTest`의 시험 Chest는 이 기지 가구 목록에 등록하지 않았다. 원정 씬 진입마다 기존 authored loot를 새로 만드는 scene-local 컨테이너라는 현재 규칙을 유지한다.

### Map Selection Terminal

- `GameMap1`의 `Stage1_MapSelectionTerminal`에 `MapTerminalInteractable`과 `MapSelectionOverlay`가 있다.
- E 진입까지는 Chest/Portal과 같은 `PlayerInteractor` 탐색 경로를 사용한다.
- UI를 열기 전에 현재 인벤토리를 닫는다.
- UI가 열리면 Player 이동, 다른 E 상호작용, 인벤토리 입력을 잠근다.
- 현재 직렬화된 선택은 `GameMapTest / RaidEntry` 한 개다.
- 취소 또는 Escape로 닫으면 이전 입력 상태를 복원한다. `MapSelectionOverlay`는 Escape를 직접 읽지 않고 persistent `GameplayEscapeMenuController`에 열린 상태를 등록한다.
- 맵 선택 UI에는 거리 이탈 자동 종료가 없다. 이동이 잠기므로 정상 입력만으로 범위를 벗어나지 않는다.

### Return Portal

- `GameMapTest`의 `Stage1_ReturnPortal`에 `ReturnPortalInteractable`과 활성 solid BoxCollider가 있다.
- E 안내와 가장 가까운 대상 선택은 Chest와 동일한 `PlayerInteractor` 공통 경로를 사용한다.
- 현재 직렬화된 목적지는 `GameMap1 / BaseReturn`이다.
- E를 누르면 `RaidSession.TryResolveExtractionAndReturn`이 생환 성공과 피해 차단을 한 번만 확정하고 즉시 공통 검은 전환을 시작한다.
- `DirectSceneTravel`로 `GameMap1 / BaseReturn`에 자동 복귀해 정산하며, `SettlementCommitted` 뒤에만 `확인` 하나를 표시한다. 결과가 이미 확정됐거나 전환 중이면 중복 요청을 거부한다.
- 이동 준비 과정에서 공통 셸이 열린 인벤토리, 드래그, popup과 입력 상태를 정리한다.
- Portal 자체에는 지속 상호작용 UI가 없으며, 확정 뒤 표시되는 결과 UI는 persistent 원정 결과 화면이다.

---

## 6. 공통화와 하드코딩 감사

### 이미 공통화된 부분

- 대상 검색, 가장 가까운 하나 선택, E 입력, 안내 표시가 `PlayerInteractor` 한 곳에 있다.
- 모든 현재 대상은 `Interactable`의 공통 계약을 사용한다.
- 모든 Chest는 `ChestInteractable`과 `InventoryUIManager.TryToggleChestInventory`를 재사용할 수 있다.
- 맵 터미널은 `RaidSession`의 원정 시작, 귀환 포탈은 생환 결과 확정을 호출하며 실제 게임플레이 씬 로드는 둘 다 `DirectSceneTravel` 경계로 수렴한다.
- 씬 전환 전 정리는 `PersistentGameplayShell`과 `InventoryUIManager.CloseAllInventories`를 공유한다.
- 관련 실행 경로에는 `GameObject.Find`, `FindAnyObjectByType`, `FindFirstObjectByType`로 매번 대상을 찾는 코드가 없다. Player-local `GetComponent`, serialized reference와 기존 Singleton을 사용한다.

따라서 현재 시스템은 각 오브젝트가 전부 독립적으로 하드코딩된 구조는 아니다. **공통 진입과 씬 이동은 재사용 가능하고, Chest/Terminal/Portal이 기능별 행동만 나눈 형태**다.

### 중복 또는 임시 고정값

#### 2026-08-23 해결한 항목

1. **열린 지속 상호작용의 대상 유지 경계를 연결했다.**
   - 열린 Chest만 활성 세션으로 취급하고 닫힘과 동시에 최근접 선택으로 복귀한다.
2. **상호작용 거리 원본을 하나로 통합했다.**
   - `PlayerInteractor.interactionRange = 3`만 권위 값이며 Chest 열기와 자동 닫기가 같은 판정을 호출한다.
3. **열린 Chest의 파괴·비활성 종료 경계를 연결했다.**
   - null, 비활성 Chest 또는 비활성 `ChestInteractable`을 감지하면 같은 전체 닫기 경로를 사용한다.

#### 현재 프로토타입에서는 허용 가능한 항목

- E는 `PlayerInteractor`의 serialized `KeyCode`라 한 곳에서 바꿀 수 있지만 아직 리바인딩 가능한 Input Action은 아니다.
- I는 `InventoryUIManager`가 읽고, Escape는 persistent `GameplayEscapeMenuController` 하나만 읽는다. 열린 확인창·설정·메뉴·맵 선택 UI·인벤토리를 정해진 우선순위로 한 단계씩 닫는다.
- prompt 문구와 맵 선택 화면은 영문 OnGUI 임시 UI다.
- 맵 터미널은 목록 데이터가 아니라 단일 serialized scene/spawn/display 값만 가진다.
- Portal의 목적지 scene/spawn은 Inspector에서 바꿀 수 있지만 문자열 기반이다.
- Portal prompt `Return To GameMap1`은 코드 고정 문자열이라 목적지 변경 시 문구와 불일치할 수 있다.
- 대상 탐색은 `Physics.AllLayers`, 고정 Collider 버퍼 32개, object pivot 거리, 같은 거리의 명시적 tie-break 없음, 시야선 검사 없음이다.
- `ChestInteractable`은 `Chest`를 Require하지만 Collider를 Require하지 않는다.

---

## 7. 당시 정리 후보 — 현재 상태는 `CURRENT_STATE.md` 우선

아래는 이 절을 작성했을 당시의 후보 기록이다. 현재 다음 작업 목록으로 사용하지 않으며, 최신 구현 여부와 재검증 조건은 `docs/ai/CURRENT_STATE.md`를 우선한다.

1. `[사용자 수동 확인 후보]` 실제 E와 WASD 입력으로 Chest A/B 겹침, 이동 중 열린 대상 유지와 거리 이탈 체감을 확인한다.
2. `[후속 후보]` 벽 너머 대상, Collider 32개 초과, 완전 동거리 tie-break는 실제 맵 밀도나 시야선 규칙이 필요해질 때 결정한다.
3. `[현재 구현 / 조건부 후속]` 생환 시 Player 소지품 전체 보존과 사망·포기·실제 복구 실패 시 소지품 전체 소실은 23절에서 구현했다. 출격 전 물건과 원정 획득물을 선별 처리해야 할 때만 영구 instance ID·획득 provenance를 별도 범위로 확장한다. 강제종료 원정 재개는 22절에서 구현했다.

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

- Player prefab의 `PlayerInteractor`: E, 유일한 interaction range 3, debug prompt 활성
- Player prefab의 `InventoryUIManager`: 같은 PlayerInteractor를 필수 참조하며 별도 Chest range 없음
- GameMap1: Chest 2개, Map Terminal 1개
- GameMapTest: Return Portal 1개, 목적지 `GameMap1 / BaseReturn`
- 2026-08-23 최종 프리팹 검사: Missing Script 0, `InventoryUIManager` 필수 직렬화 참조 8/8, `PlayerInteractor`와 `InventoryUIManager` 각각 1개
- 검사 종료 후: Play Mode false, Pause false, 활성 씬 `GameMap1`, scene dirty false
- 2026-08-23 변경 전후 Console Error 기준선은 동일한 7개다. Unity AI Camera/SerializedProperty 도구 오류 4개, 외부 AwaiiStudio shader 오류 2개, 이전 오디오 검증 harness 오류 1개이며 이번 상호작용 변경에서 새 Error/Exception/Assert는 추가되지 않았다.

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
- `[씬 확인][2026-08-23]` 기지에서 바로 전투를 확인할 수 있도록 GameMap1에도 같은 `KenneyZombiePatrol` 프리팹의 연결된 인스턴스 `Test_KenneyZombiePatrol_Base`를 `(0, 0, 5)`에 하나 배치했다. 사용자 요청에 따라 이번 추가 배치의 Play Mode 재검증은 생략했다.
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
- `[코드/씬 확인]` New Game은 기존 저장 파일을 지우거나 덮어쓰지 않고, `GameMap1` 기지에서 초기 8×9 인벤토리와 Container를 제외한 시험 아이템 ID 1~5로 시작한다.
- `[Play Mode 확인]` Load 요청은 같은 로딩 씬을 거쳐 `GameMap1`에서 persistent Player의 기존 `InventoryUIManager`에 한 번만 적용된다. Player, Camera, UI 셸을 재생성하지 않는다.
- `[코드/씬 확인]` GameLoading의 기존 Slider는 실제 비동기 로드 진행률 0~1에 연결되어 있다.
- `[Play Mode 확인]` Settings의 Sound 토글은 슬롯 세이브와 분리된 전역 `PlayerPrefs` 설정이며 즉시 `AudioListener.pause`에 적용된다.
- `[Play Mode 확인]` Exit는 확인 패널을 거치며, 실제 종료 호출은 `Application.Quit`이다.

### 저장되는 데이터

- 단일 프로토타입 슬롯 경로는 `Application.persistentDataPath/Saves/save_slot_1.json`이며 이전 정상본은 `.bak`으로 유지한다.
- 현재 최상위 스키마 버전은 5다. 플레이어 인벤토리와 장비는 `playerItems` / `flat-player-items-v1`, Player 금·은은 `playerCurrency` v1, 기지 가구는 `baseState` v2 / `base-furniture-v1`, stable Merchant별 재고는 `baseMerchantState` v1 / `base-merchants-v1`으로 저장한다. 유효한 개발용 v2·v3·v4 저장은 읽을 때 기존 아이템·기지 상태를 보존하고 누락된 화폐·상인 상태에 명시적 초기화 provenance를 더한 v5 메모리 데이터로 변환하며 원본 파일을 자동 덮어쓰지 않는다.
- 각 아이템은 ItemDatabase의 숫자 `definitionId`, 파일 내부 `recordId`와 컨테이너 부모 관계, 그리드 슬롯 또는 `equipmentSlot`, 회전 상태를 저장한다.
- 컨테이너 내부 아이템은 파일 내부 관계용 `recordId`로 연결한다. 이 값은 영구 아이템 instance ID가 아니다.
- 이름, 설명, 아이콘, 아이템 크기, 컨테이너 크기와 장착 가능 슬롯은 저장하지 않고 같은 `ItemDatabase.asset`에서 다시 조회한다.
- 이 절의 ordinary 단일 슬롯에는 씬, Player 위치, 열린 UI, 드래그, Camera, Portal, Enemy와 일시 상호작용 상태를 저장하지 않는다. 일반 로드 후 시작 위치는 항상 기지의 SpawnPoint다. 진행 중 원정의 강제 종료 복구 snapshot 범위는 아래 22절의 별도 Recovery 계약을 따른다.

### 기지 상태와 definition 경계

- `[코드/씬 확인]` GameMap1의 두 Chest는 각각 stable placed ID `core:home/chest_a`, `core:home/chest_b`와 공유 definition `core:storage_chest`를 가진다. 두 ID의 저장 grid는 서로 다른 객체이며 같은 내용을 공유하지 않는다.
- `[코드 확인]` 이름과 6×5 저장 크기 같은 공유 프리셋은 `BaseFurnitureDefinition`, 개별 배치물의 변하는 내용은 `BaseFurnitureRuntimeState`에 분리했다. Save DTO는 이 원본의 직렬화 표현일 뿐 병행 권위 상태가 아니다.
- `[코드 확인]` furniture definition key와 placed ID는 향후 모드 충돌을 줄이도록 소문자 `namespace:path` 형식이다. 알 수 없는 definition, 중복 key/placed ID, definition과 저장 크기 불일치는 조용히 대체하지 않고 로드를 거부한다.
- `[현재 정책]` 제거된 모드의 알 수 없는 가구/아이템 DTO를 코어 게임만 로드한 뒤 opaque 상태로 재저장하지 않는다. 대신 primary 원본을 수정하지 않는 fail-closed와 정상 backup 검증을 사용한다. 모드 hot-uninstall 보존이 필요해질 때 별도 orphan-content 정책과 migration을 설계한다.
- `[코드/씬 확인]` ItemDatabase와 BaseFurnitureDatabase는 ScriptableObject catalog를 기존 persistent shell/Main Menu/기지 controller가 직접 참조한다. 새 전역 Manager나 reflection 기반 범용 저장 프레임워크는 추가하지 않았다.

### 저장·로드 안전성

- 저장 전에 열린 Player/Chest UI, 드래그와 case popup을 정리한 뒤 캡처한다.
- 쓰기 전에 두 DB의 null·잘못된 ID·중복 ID, 전체 배치·부모 관계, 런타임 단일 소유권, 장비 슬롯 유효성·호환성과 가구별 저장 크기를 검증한다.
- 임시 파일을 먼저 쓴 뒤 정상 파일로 교체하고, 기존 정상 파일은 `.bak`으로 남긴다.
- 로드는 primary를 전체 의미 검증한 뒤 사용하며, primary의 JSON 헤더가 정상이어도 아이템·가구 ID, 배치, 부모, 장비 슬롯 또는 가구 저장 관계가 손상됐으면 정상 backup을 별도로 검증해 대신 선택한다. 후보 검증 중 예외가 나도 다음 backup 검증을 막지 않는다.
- 복원은 별도 `PlayerInventoryState`와 `BaseFurnitureStateStore` 후보를 모두 완성·검증한 뒤 적용한다. Base를 먼저 교체하고 Player 완료 이벤트를 나중에 발행하므로 현재 관찰자는 새 Player와 옛 Base가 섞인 순간을 보지 않으며, Player 적용 실패 시 이전 Base로 되돌린다.
- 비정상 파일의 메모리 과다 할당을 막기 위해 모든 가구 레코드의 ID·definition·크기와 전체 cell/item 예산을 먼저 검사하고, 전체 선검증 뒤에만 실제 grid와 item 객체를 만든다.
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

- `[코드/프리팹 확인]` `PlayerInventoryState` 하나가 8×9 `StandardStashViewData`, `EquipmentLoadoutData`와 Player 전용 `PlayerWallet`을 함께 소유한다. New Game은 Container를 제외한 시험 아이템 ID 1~5, 빈 장비와 금·은 각각 5000을 만들고, Load는 세 상태를 함께 교체한다.
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
- `[코드 확인]` 유효한 v2 저장은 장비가 빈 플레이어 상태로, 유효한 v3 저장은 기존 장비까지 보존한 상태로 각각 v4 메모리 데이터로 변환하고 빈 기지 상태를 붙인다. 기존 파일은 로드 시 자동 덮어쓰지 않으며 다음 명시적 저장부터 v4로 기록한다. 기존 v3의 `equipmentSlot=12`는 그대로 `W1`을 뜻한다.
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
- `[제외 범위]` 탄약, 재장전, 반동, 탄퍼짐·명중률, 총기 3D 모델, VFX, 발사 애니메이션, 적 음성, 3D 공간음향, 최종 사운드 디자인, 정식 드롭 테이블, 시체 저장·정리 시간, 부활·respawn과 정식 전투 밸런스는 구현하지 않는다.

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
- `[코드/프리팹 확인]` persistent Player에 `WeaponAttackAudioFeedback`와 2D `AudioSource`가 각각 하나 있다. cadence를 통과한 `EmitRaycastShot` 시작에서 발사음을 재생하고, `ApplyDamage`가 반환한 `DamageResult.WasApplied`가 참일 때만 적중음을 약 `0.06`초 뒤 추가 재생한다. 두 효과음의 시작점을 분리해 둔탁한 적중음이 발사음에 묻히지 않게 하며, 컴포넌트가 비활성화되면 대기 중인 재생도 취소한다. 오디오 컴포넌트는 공격 성립이나 피해를 판정하지 않는다.
- `[에셋/라이선스 확인]` 발사음은 Kenney `Sci-Fi Sounds 1.0`의 `laserSmall_000.ogg`(0.239초), 적중음은 `Impact Sounds 1.0`의 `impactSoft_heavy_000.ogg`(0.505초)를 사용한다. 두 공식 팩 모두 CC0이며 선택 파일의 원본 이름, 출처, SHA-256과 이용 조건을 `Assets/Audio/Combat/Kenney/LICENSE.md`에 기록했다.
- `[에셋 확인]` 두 OGG는 mono, PCM, Decompress On Load, preload 설정으로 import한다. 매 발사 파일 로드나 AudioSource 생성 없이 persistent AudioSource 하나의 `PlayOneShot`으로 겹쳐 재생한다.
- `[코드/프리팹 확인]` 좀비의 실제 이동 자식 `ZombieAgent`에는 center `(0, 2, 0)`, height `4`, radius `0.6`인 Trigger CapsuleCollider가 하나 있다. Root의 `EnemyStats`가 부모 경로의 `IDamageable` 권위자다.
- `[코드 확인]` `EnemyStats.ApplyDamage`가 현재 체력을 0~최대로 제한하고, 살아 있는 상태의 `> 0 → 0` 전이에서 `isDead`를 먼저 확정한 뒤 `Died`를 정확히 한 번 통지한다. `Initialize`도 한 개체당 한 번만 성공하므로 죽은 뒤 피해·회복·Reset·재초기화는 체력만 되살리는 암묵적 부활을 만들지 않는다.
- `[현재 코드/프리팹 확인]` `EnemyDeathHandler`는 `Died` 뒤 Brain, 공격 Action, Agent, Animator와 피격 Collider를 비활성화한다. Root·렌더 외형·죽은 `EnemyStats`는 시체로 남기고 기존 Chest 경로의 전리품 상호작용과 전용 Trigger를 활성화한다. 자세한 현재 계약은 20절에 기록한다.
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
- `[이전 구현 Play Mode 호출 확인]` 실제 persistent Player의 빈 3번 슬롯과 `InputBlocked`에서는 발사를 거부했다. W1 Handgun은 press/held/cooldown 순서, W2 Rifle은 held/RPM 순서로 Player 원점 Raycast를 실행했고 두 시험 좀비 모두 35 피해 세 번째에 한 번 죽었다. 당시에는 사망 뒤 Patrol·피격 Collider·외형 비활성 및 추가 피해·중복 사망 없음을 확인했으며, 현재 외형 정책은 20절의 시체 유지로 대체됐다.
- `[Play Mode 호출 확인]` 최종 재검증에서는 기존 장비 상태를 보관하고 장비 소유 API로 시험용 W1 Handgun과 W2 Rifle을 임시 장착했다. `권총 1발 → 권총 조기 재발 거부 → 같은 시각 소총 첫 발 허용 → 권총 재선택 시 남은 cooldown 유지 → 소총 다음 허용 시각의 세 번째 총 피해로 사망`을 통과했고, `Died`와 `EnemyDeathHandler`는 한 번만 실행됐다. 시험 장비, 활성 번호, Player·Camera 위치, 입력 차단과 EventSystem 상태를 모두 원래 값으로 복구한 뒤 Edit Mode로 종료했다.
- `[Play Mode 호출 확인]` 오디오 재검증에서 적이 없는 유효 발사는 발사 클립만 활성 재생했고, 발사 클립을 시험 중 잠시 제외한 상태에서 35 피해가 실제 적용된 적중은 적중 클립만 활성 재생했다. 두 클립을 정상 복구한 뒤 추가 두 발로 `100 → 65 → 30 → 0`, 사망·정리 1회를 다시 통과했으며 시험 장비와 모든 런타임 상태를 원복했다.
- `[Play Mode 사용자 확인][2026-08-23]` 발사음과 같은 순간에 재생되던 둔탁한 적중음이 섞여 잘 구분되지 않았음을 확인했다. 적중음 시작을 약 `0.06`초 분리한 뒤 실제 Game View에서 효과음이 잘 들리는 것을 사용자가 확인했으며, 요청에 따라 추가 자동 공격 테스트는 생략했다.
- `[검증 과정]` 최초 재검증 하네스 2회는 비활성 `Preview Camera`를 gameplay Camera로 고른 전제와 빈 런타임 장비칸을 고정 W1/W2로 가정해 실패했다. 실제 `Main Camera`와 장비 API를 사용하도록 하네스를 바로잡은 뒤 위 최종 검증이 통과했으며, 이 실패는 프로젝트 컴파일·전투 코드 오류가 아니었다.
- `[Console 기준선]` 최종 import/compile 뒤 Error/Exception/Assert는 작업 전과 같은 6개다. 이전 Camera Capture 도구 2개, 이전 SerializedProperty 도구 2개, 외부 `AwaiiStudio/ASFolliage` shader keyword 2개이며 신규 전투 오류는 없다.
- `[코드/씬 확인]` `GameMapTest`를 Preview Scene으로 열어 기존 좀비 프리팹 인스턴스가 새 `EnemyDeathHandler`와 Trigger CapsuleCollider를 상속함을 확인했고, 검사 뒤 원래 활성 `GameMap1`, dirty 상태와 Edit Mode를 그대로 복원했다.
- `[검증 한계]` Windows 입력 자동화가 Unity 창 캡처에서 `SetIsBorderRequired` 시스템 인터페이스 오류로 중단돼 실제 좌클릭의 `Update → Input.GetMouseButtonDown/GetMouseButton` 경계는 자동 조작하지 못했다. 공개 공격 진입점의 Play Mode 호출과 공식 Unity 입력 의미·컴파일까지만 확인했으며 사용자 실제 Game View 좌클릭 확인으로 승격하지 않는다.
- `[미검증]` 실제 Game View에서 권총 3회 클릭과 자동소총 hold의 전체 입력 회귀, 인벤토리를 연 채 실제 클릭, 벽 뒤 적 차폐, 씬 왕복 중 공격 cooldown·오디오와 Windows Player build는 이번 범위에서 수행하지 않았다. 적중음의 주관적 구분은 위 사용자 확인으로 완료됐다.

---

## 17. 저장 없는 시험 루팅과 귀환

### 사용자 요구와 범위

- `[사용자 요구]` 이미 같은 인벤토리 객체를 보존하는 맵 왕복 구조를 다시 만들지 않고, 별도 `RaidSession`이 실제로 필요한지 먼저 확인한다. 정상인 부분은 건드리지 않고 실제 누락 또는 결함만 수정한다.
- `[확정 범위]` `GameMapTest`에 디자인 없는 시험 Chest 하나와 기존 DB 아이템 하나를 두어 `상자 → 플레이어 인벤토리 → 귀환`의 같은 실행 세션 흐름만 완성한다.
- `[당시 제외 / 후속 반영]` 이 단계에서는 생환·사망 결과 목록, 획득 provenance, 원정 스냅샷·롤백, 도심 생성기의 상자 spawn, 기지 Chest 영속화와 세이브 형식 확장을 포함하지 않았다. 이후 기지 Chest 영속화, 원정 결과와 Recovery는 18·21~23절에서 구현했고 provenance와 도심 상자 spawn은 여전히 후속이다.

### 상태 소유권과 호출 흐름

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | 원정 Chest 안에서는 해당 scene-local `StandardStashViewData`, 획득 뒤에는 persistent `PlayerInventoryState.Inventory`가 같은 `InventoryItemData` 객체의 유일한 소유자다. |
| 수명 범위 | 시험 Chest와 남은 내용물은 `GameMapTest` Scene, 플레이어가 획득한 아이템은 현재 Play Session의 persistent Player 셸 수명이다. |
| 생성·파괴 주체 | persistent grid가 아직 연결되지 않은 Chest는 `Awake`에서 직렬화된 DB ID 목록을 임시 grid에 전부 배치한 뒤 authored grid를 한 번 확정한다. 이미 외부 grid가 연결된 늦은 `Awake`는 그 grid를 검증해 보존한다. Chest와 남은 내용물은 씬 unload 때 끝나며, 플레이어로 이전된 객체는 셸과 함께 유지된다. |
| 변경 진입점 | 기존 UI 드래그가 사용하는 컨테이너 `InsertInventoryItem` 경계로 원본 소유자에서 제거한 뒤 새 소유자에 삽입한다. 별도 보상 지급이나 복사 경로는 없다. |
| 이전 규칙 | 아이템 하나는 동시에 한 논리 컨테이너에만 존재한다. 이전 실패 시 기존 컨테이너 API의 소유권 검증과 drag 취소 경계를 사용한다. |
| 파생 표현 | 플레이어·외부 인벤토리 View는 현재 grid의 파생 UI이며 열 때 같은 런타임 데이터를 `Apply`한다. |
| 저장 경계 | 이번 검증은 무저장 Play Session 연속성이다. 기존 플레이어 단일 슬롯 저장은 별도 기능이며 Chest 상태·레이드 결과를 추가하지 않았다. |
| 업데이트 주체 | Chest authored seed는 외부 binding이 없을 때 `Awake` 한 번뿐이며 독립 `Update`, 새 Manager 또는 `RaidSession`은 없다. |

### 현재 구현

- `[코드 확인]` `Chest.Awake`는 외부 상태가 없을 때만 임시 grid에 authored ID 전체를 배치한 뒤 한 번에 공개한다. `GameMapTest` 시험 Chest는 기존처럼 ID 1을 만들고, 비활성 GameMap1 Chest가 store에 먼저 연결된 뒤 늦게 Awake를 실행해도 연결된 기지 원본을 초기 seed로 덮어쓰지 않는다.
- `[코드 확인]` 시작 목록은 임시 grid에 전부 배치할 수 있을 때만 유효하다. DB 누락, 알 수 없는 ID 또는 공간 부족이면 부분 seed를 노출하지 않고 빈 grid와 명시적 오류를 남긴다.
- `[씬 확인]` `GameMapTest`의 `Stage3_TestLootChest`는 `RaidEntry`에서 2m 떨어진 불투명 Cube이며, 6×5 Chest, Collider, `ChestInteractable`, `ItemDatabase`, 시작 ID 1 하나와 기존 이동 충돌 규칙에 필요한 `Obstacle` 태그가 직렬화되어 있다.
- `[구조 결정][당시]` 고정 왕복과 같은 세션 내 획득물 보존만으로는 `RaidSession`이 필요하지 않았다. `[후속 갱신]` 생환·사망·포기 결과가 요구된 뒤에는 그 결과와 원정 수명만 소유하는 최소 `RaidSession`을 추가했으며, 아이템 원본은 계속 persistent `PlayerInventoryState`가 소유한다.

### 2026-08-23 검증 결과와 한계

- `[Play Mode 호출 확인]` `GameMap1 → GameMapTest` 도착 뒤 실제 E 입력이 호출하는 `PlayerInteractor.TryInteract` 경계로 시험 Chest를 열고, 닫고, 다시 열었다. 시작 ID 1은 같은 객체로 정확히 한 번 존재했고 열기마다 다시 seed되지 않았다.
- `[Play Mode 호출 확인]` 같은 아이템 객체를 기존 컨테이너 API로 Player grid에 이전했다. 이전 뒤 Chest에는 0개, Player에는 정확히 1개였고 `InventoryOwner`는 Player grid 하나였다.
- `[Play Mode 호출 확인]` 같은 원정에서 빈 Chest를 다시 열어도 아이템이 생기지 않았다. 귀환 포탈도 `PlayerInteractor.TryInteract` 경계로 호출했으며 연속 두 번째 호출은 입력 차단으로 거부됐다.
- `[Play Mode 호출 확인]` `GameMap1` 귀환 뒤 shell, Player, `InventoryUIManager`, `PlayerState`, Player inventory와 획득 아이템이 모두 같은 참조/Entity ID였다. 슬롯, 회전과 단일 소유권도 유지됐다.
- `[Play Mode 호출 확인]` 별도 실행에서 `GameMap1 → GameMapTest → GameMap1 → GameMapTest → GameMap1`을 수행했다. 첫 Chest 오브젝트는 unload 뒤 파괴됐고 두 번째 진입의 Chest data와 ID 1 아이템은 각각 새 객체였으며, 매 진입 seed는 하나, persistent Player state는 같은 참조였다. 두 Chest 모두 `Obstacle` 태그였다.
- `[Console 기준선]` 검증 뒤 Error는 작업 전과 같은 7개다. 이전 Camera Capture 2개, 이전 SerializedProperty 2개, 외부 ASFolliage shader 2개와 이전 오디오 하네스 1개이며 신규 Chest·루팅 오류는 없다.
- `[후속 반영]` 당시 후속이던 GameMap1 기지 Chest 영속 보관은 아래 `## 18`에서 구현했다. GameMapTest 원정 Chest가 씬 종료와 함께 사라지는 규칙은 그대로다.
- `[미검증]` 실제 물리 마우스 드래그와 키보드 E 입력, Windows Player build는 이번 자동 호출 검증에 포함하지 않았다. 기존 공개 입력 진입점과 런타임 객체·UI 상태를 Play Mode에서 검증했다.

---

## 18. 정의 기반 기지 가구 영속성

### 사용자 요구와 외부 사례에서 채택한 경계

- `[사용자 요구][2026-08-23]` 기지 가구를 영속화하되 외부 유사 게임의 방식을 확인하고, RimWorld처럼 정의와 소유 경로가 선명하며 나중에 모딩 가능한 방향으로 구현한다.
- `[조사]` RimWorld의 `Def → Thing → ThingComp` 분리는 공유 정의, 배치 인스턴스, 선택적 개별 기능/상태를 구분한다. Vintage Story는 배치된 `BlockEntity`가 개별 상태를 소유하고 namespaced asset key와 명시적 attribute 직렬화를 사용한다. Cataclysm:DDA는 문자열 definition ID, 지역 단위 소유와 버전 migration을 명시한다.
- `[적용]` 이 프로젝트에는 필요한 최소 경계만 가져왔다. `BaseFurnitureDefinition → BaseFurnitureInstance → BaseFurnitureRuntimeState`를 두고 명시적 DTO/codec으로 저장한다. RimWorld 코드 복제, 범용 XML patch, reflection `Comp` 프레임워크, 모드 검색/로드기는 만들지 않았다.

참고 자료:

- [RimWorld XML Defs](https://rimworldwiki.com/wiki/Modding_Tutorials/XML_Defs), [RimWorld ThingComp](https://rimworldwiki.com/wiki/Modding_Tutorials/ThingComp)
- [Vintage Story BlockEntityBehavior API](https://apidocs.vintagestory.at/api/Vintagestory.API.Common.BlockEntityBehavior.html), [generic container 구현](https://github.com/anegostudios/vssurvivalmod/blob/master/BlockEntity/BEGenericTypedContainer.cs), [AssetLocation 구현](https://github.com/anegostudios/vsapi/blob/master/Common/Assets/AssetLocation.cs)
- [Cataclysm:DDA map/submap 개발 문서](https://docs.cataclysmdda.org/DEVELOPER_FAQ.html), [JSON migration 문서](https://github.com/CleverRaven/Cataclysm-DDA/blob/master/doc/JSON/OBSOLETION_AND_MIGRATION.md)

### 상태 소유권과 호출 흐름

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | persistent `GameManager` 하나가 plain C# `BaseFurnitureStateStore`를 소유하고, store가 placed ID별 `BaseFurnitureRuntimeState`와 해당 `StandardStashViewData` 원본을 소유한다. |
| 수명 범위 | store와 상태는 Play Session, GameMap1의 `BaseFurnitureInstance`·Chest·UI는 Scene/View다. 디스크 DTO는 실행 사이 값 전달용이다. |
| 생성·파괴 주체 | GameManager가 세션 store를 만들고, GameMap1 controller가 새 게임·로드 후보를 적용한 뒤 scene instance를 bind한다. 씬 unload는 binding만 해제하고 store를 파괴하지 않는다. |
| 변경 진입점 | 가구 내용 변경은 기존 inventory container API로만 수행한다. store 교체는 초기 GameMap1에서 `GameManager.TryReplaceBaseFurnitureState` 하나만 호출한다. |
| 포함 관계 | definition asset은 공유 immutable 참조다. placed runtime state는 정확히 한 store, item은 정확히 한 grid/container가 소유한다. Chest와 UI는 원본을 관찰하는 파생 표현이다. |
| 이전 규칙 | item drag는 기존 원자적 container 이전·rollback을 그대로 사용한다. scene bind는 전체 instance를 선검증한 뒤 적용하고 중간 실패 시 앞선 binding을 되돌린다. |
| 파생 표현 | scene Chest의 `chestInventoryData`와 inventory UI는 store grid의 같은 참조다. 별도 내용 복사본이나 scene-local 권위 데이터를 만들지 않는다. |
| 저장 경계 | v4는 placed ID, definition key와 선택적 grid의 definition ID·slot·rotation·container 관계만 저장한다. Transform, 외형, HP, 전력, 제작, 문 열림 상태는 아직 저장하지 않는다. |
| 업데이트 주체 | 독립 Tick/Update는 없다. scene Start의 bind, 기존 drag 완료, F5 capture와 load apply 경계에서만 변경한다. |

### 현재 구현과 검증 상태

- `[씬/에셋 확인]` `CoreStorageChest.asset`과 `BaseFurnitureDatabase.asset`을 만들고 GameMap1 두 Chest와 MainMenu 검증 경로에 연결했다. 두 placed ID는 `core:home/chest_a/b`, definition은 `core:storage_chest`, 저장 크기는 6×5다.
- `[정적 코드 확인]` definition·instance·runtime store·DTO·codec의 책임이 분리되어 있고, GameMapTest 시험 Chest에는 `BaseFurnitureInstance`를 붙이지 않아 원정 리셋 규칙을 보존했다.
- `[정적 코드 확인]` v2/v3→v4 migration, primary/backup 의미 검증, 알 수 없는 definition, 중복 ID, 크기 불일치, 잘못된 slot index, 총 grid/item 예산 선검증 경로를 추가했다.
- `[코드/Play Mode 확인]` Main Menu는 의미 검증을 통과한 primary와 backup을 함께 시작 요청에 전달한다. GameMap1 controller가 실제 placed-ID 집합으로 primary를 적용 전에 다시 검사하고, 이 단계에서만 실패하면 아직 live 상태를 바꾸지 않은 채 backup을 같은 경계로 검사한다. 선택된 후보까지 실패하면 scene fallback 가구를 bind하지 않고 F5 저장도 비활성 상태로 남긴다.
- `[코드 확인]` native v4 payload는 저장된 placed ID 집합과 현재 GameMap1의 placed ID 집합이 정확히 일치해야 한다. 누락 ID와 현재 layout에 없는 추가 ID는 빈 가구로 대체하거나 숨겨 보존하지 않고 로드를 거부한다. 기지 데이터가 존재하지 않았던 v2/v3 migration에만 파일에 직렬화되지 않는 일회성 초기화 표식을 붙여 현재 authored Chest 2개를 생성한다.
- `[코드 확인]` inactive scene 가구가 store에 먼저 연결된 뒤 늦게 `Chest.Awake`를 실행해도 이미 검증된 외부 grid를 authored loot로 덮지 않는다. 잘못된 외부 grid는 조용히 재초기화하지 않고 component를 비활성화한다.
- `[코드/실행 확인][2026-08-24]` 저장 codec 순수 검증 7개, native v4 exact placed-ID 검증, v2/v3의 일회성 authored 초기화, 최대 grid와 중첩 container 총 cell 예산 선검증, bool factory 실패 경계를 통과했다. 과대 payload는 실제 grid 할당 전에 거부됐다.
- `[Play Mode 확인][2026-08-24]` GameMap1의 서로 다른 6×5 grid에 `A: ID 1 회전`, `B: ID 6 회전 → 내부 ID 2 회전`을 배치하고 사용자 기준 1회 `GameMap1 → GameMapTest → GameMap1` 왕복을 확인했다. persistent `GameManager`, shell, Player, `InventoryUIManager`, 두 grid 참조와 두 상자의 분리된 내용·중첩 소유권이 그대로였고, scene-local Chest View만 재생성됐다. GameMapTest에는 `BaseFurnitureInstance`가 0개였으며 원정 Chest는 매 진입 ID 1 하나로 별도 초기화됐다.
- `[Play Mode 확인][2026-08-24]` 메모리 안에서 현재 layout의 `chest_b`가 빠진 native v4 primary와 정상 backup을 함께 요청했다. controller는 primary를 live 변경 전에 거부하고 정상 backup의 두 상자·회전·중첩 관계를 복원해 bind했으며 요청은 한 번만 소비됐다.
- `[실행 확인][2026-08-24]` `Application.temporaryCachePath`의 격리 파일로 Windows `File.Replace`를 확인했다. 정상 primary는 이전 primary를 backup으로 회전했고, 손상·layout 불일치 primary를 승격하지 않는 경로는 `null` backup 교체로 기존 정상 `.bak`을 유지했다. 시험 임시 폴더는 제거했다.
- `[씬/직렬화 확인][2026-08-24]` GameMap1 가구 2개, Main Menu DB 참조, GameMapTest scene-local Chest 1개와 persistent 가구 0개, 세 씬 Missing Script 0을 Unity Editor API로 확인했다. 최종 project compile Error 0, Console 신규 Error/Exception/Assert 0이며 현재 Warning 6개는 Input Manager 폐기 예고, Unity MCP 서명 수집, 기존 Animator Controller, 외부 RenderTextureBaker API 경고다.
- `[미검증]` 실제 사용자 slot 1 파일을 생성하는 F5와 새 프로세스의 Main Menu 버튼 Load는 기존 사용자 세이브를 건드리지 않기 위해 실행하지 않았다. 같은 저장 DTO·primary/backup 선택·실제 GameMap1 적용 경계는 격리 파일 및 Play Mode 메모리 후보로 검증했다.

---

## 19. 공통 감지 기반 근접·원거리 적 AI 1단계

### 사용자 요구와 범위

- `[사용자 요구][2026-08-24]` 기존 좀비는 야생형 근접 AI로 사용해 Player까지 최단 경로로 돌진시킨다. 별도 primitive 외형의 원거리 적 하나는 Player를 보면 추적하면서 사격하고, 전투 밖에서는 랜덤 지형을 읽어 순찰한다.
- `[사용자 요구]` 시야뿐 아니라 총성·발사체·마법 같은 자극을 받을 수 있는 공통 기반을 두고, 정지 조준·도주 사격·돌진 사격·엄폐·지속 추적형 원거리 AI의 후속 설계를 정리한다.
- `[현재 구현 범위]` 감지·기억·NavMesh 순찰, 근접 돌진, 원거리 접근·정지 조준·가상 조준 사격과 기존 피해·사망 연결까지만 구현했다.
- `[제외 범위]` 공격 애니메이션, 탄환 오브젝트, 발소리·마법·발사체 자극 생산자, 후퇴·엄폐·측면 이동, 분대 전술, Player 사망 입력 차단과 Raid 실패 처리는 포함하지 않았다.

### 조사 결과와 채택한 구조

- `[조사]` The Division의 상위 상태와 cover 후보 점수 분리, The Darkness II의 perception과 last-known-position 분리, F.E.A.R. 3의 소수 상태와 plan 조합, God of War Ragnarök의 공유 core와 역할별 subtree 분리를 비교했다.
- `[적용]` 현재 두 적 규모에는 `EnemyAIController` 하나가 저빈도 인식·기억·순찰·이동 명령을 소유하고, 근접·원거리 공격 Action만 교체하는 구성이 가장 짧다. 후속 엄폐 전술이 생길 때 `전술 선택 → 위치 후보 평가 → 행동 실행`을 추가하며 지금부터 범용 행동 트리나 중앙 scheduler를 만들지 않는다.
- `[확정 해석]` “한 번 보면 죽을 때까지 추적”은 대상 신원과 마지막 관측 위치를 잊지 않는 기억 정책이다. 시야가 끊긴 동안 현재 Player 좌표를 벽 너머로 읽는 방식은 사용하지 않는다.

참고 자료:

- <https://media.gdcvault.com/gdc2016/Presentations/Dunstan_Philip_BlendingAutonomyAnd.pdf>
- <https://media.gdcvault.com/gdc2012/slides/Summit_AI/Brewer_Daniel_D2AIPostMortem.pdf>
- <https://gdcvault.com/play/1013282/Three-States-and-a-Plan>
- <https://media.gdcvault.com/gdc2023/Slides/PreparingForRagnarokWithNotes.pdf>
- <https://docs.unity3d.com/Packages/com.unity.ai.navigation%402.0/manual/index.html>
- <https://docs.unity3d.com/6000.0/Documentation/Manual/physics-optimization-raycasts-queries.html>

### 상태 소유권과 호출 흐름

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | `EnemyAIController`가 적의 인식 상태, 현재 타깃, 마지막 확인 위치, 순찰 목적지와 NavMesh 이동 명령을 소유한다. `EnemyStats`와 `PlayerStats`는 각자의 체력을 소유한다. |
| 수명 범위 | AI 기억·공격 cooldown은 Enemy Entity, definition은 Asset, `WorldStimulus`는 통지 순간, GameMapTest NavMesh는 Scene 수명이다. |
| 생성·파괴 주체 | 씬의 프리팹 인스턴스가 AI와 scene-local 전리품 grid를 만들고 scene unload가 정리한다. `EnemyDeathHandler`는 `EnemyStats.Died` 뒤 행동·Agent·Animator·피격 Collider를 정지하고 시체 상호작용을 열지만 체력이나 사망을 다시 판정하지 않는다. |
| 변경 진입점 | Brain 상태는 저빈도 판단과 `HandleWorldStimulus`/`DamageApplied`로만 바뀐다. 공격은 `EnemyCombatAction`이 대상의 공통 `IDamageable.ApplyDamage`를 호출한다. |
| 포함 관계 | Brain은 같은 Entity의 Agent와 Action에 명령하지만 체력·정의·Player를 소유하지 않는다. `WorldStimulusChannel`은 listener 기억을 소유하지 않는다. |
| 이전 규칙 | 현재 컨테이너 소유권 이전은 없다. 타깃은 관찰 참조이며 시야·자극·사망 경계에서만 채택하거나 해제한다. |
| 파생 표현 | NavMesh path, 이동 Animator와 primitive/좀비 visual은 원본 상태에서 다시 만들 수 있는 파생 표현이다. |
| 저장 경계 | 적 AI 상태, 순찰점, 공격 cooldown과 NavMesh는 현재 저장하지 않는다. scene 재진입 시 새 적 Entity로 시작한다. |
| 업데이트 주체 | 적마다 Brain `Update` 하나만 사용한다. 비전투 0.5초, 전투·수색 0.15초 판단과 0.2초 시야 검사를 개체별로 분산한다. 총성은 사건 시 한 번 통지한다. |

### 현재 구현

- `[코드/에셋 확인]` `EnemyDefinition`에 감지·기억·순찰·이동·공격·가상 조준 설정을 추가했다. 기존 `KenneyZombie`는 `MeleeRush`, 새 `PrototypeRangedEnemy`는 `RangedPursuit` definition을 사용한다.
- `[프리팹/씬 확인]` `GameMapTest`에는 기존 좀비 1개와 청록색 구체 원거리 적 1개가 있다. 둘 다 root가 위치 권한을 가지며 `NavMeshAgent`, `EnemyAIController`, 대응 Action, `EnemyStats`, `EnemyDeathHandler`를 사용한다.
- `[코드 확인]` 두 Agent는 prefab에서 비활성으로 시작한다. Brain이 `NavMesh.SamplePosition`에 성공한 뒤 Transform을 유효한 보행면으로 맞추고 Agent를 활성화하므로 runtime NavMesh 생성 전 경고와 잘못된 `SetDestination` 호출을 피한다.
- `[코드 확인]` 순찰은 반경 안 후보를 8회까지 만들고 NavMesh 완전 경로만 채택한다. 너무 가까운 지점과 최근 두 목적지는 피하고 도착 뒤 정의 범위만큼 기다린다. 기존 고정 좌우 왕복 `EnemyPatrol`은 더 이상 참조되지 않아 제거했다.
- `[코드 확인]` 시야는 거리·시야각 뒤 장애물 Raycast를 하며, 감지 실패 시 마지막 목격 또는 들은 위치만 수색한다. 근접은 공격 순간에도 시야선을 다시 확인해 시야 캐시 동안 벽 너머 타격하지 않는다.
- `[코드 확인]` Player 발사는 Raycast·피해 적용을 먼저 마친 뒤 `GunshotSound`를 통지한다. 자극 listener 오류는 이미 완료된 발사 명령을 취소하지 않으며 정상 통지 경로에는 별도 배열 할당이 없다.
- `[코드 확인]` 원거리 적은 선호 거리 8까지 접근하며 사거리 14 안에서 피해 8을 1.1초 간격으로 시도한다. 가상 조준점의 부드러운 오차가 0.8초 동안 수렴하고 이동 중 오차가 추가되며, 첫 전투 Tick에 이전 비전투 delta를 조준 시간으로 소비하지 않는다. 모두 기능 시험값이다.
- `[당시 코드 확인 / 후속 반영]` `PlayerStats`가 기존 호환 `ApplyDamage(float)`를 유지하면서 `IDamageable`을 구현했다. 당시에는 HP 0 뒤 AI 공격 중단까지만 있었지만, 이후 Player 사망 완료 통지·입력 차단·원정 실패는 21~23절에서 구현했다.
- `[씬 정책]` NavMesh가 없는 `GameMap1`의 기존 좀비는 scene override로 Brain, Action과 Agent를 비활성화한 정지 사격 표적을 유지한다. 공유 프리팹의 전투 구성은 보존되며 GameMapTest에서만 활성 AI로 동작한다.
- `[도구 회귀]` `UrbanMapPrototypeSetup`은 모든 `EnemyAIController` root를 보호 anchor로 등록하며, `UrbanMapPlayModeValidation`은 근접 1·원거리 1뿐 아니라 두 Agent가 runtime NavMesh에 올라온 뒤에만 씬 준비 완료로 판정한다.

### 2026-08-24 검증 결과와 한계

- `[정적 Unity 확인]` 두 prefab에 Missing Script가 없고 기존 `EnemyPatrol`이 없으며 Brain, 올바른 Action, 비활성 Agent, root 피격 Collider와 사망 정리 참조가 있다. 원거리 visual에는 별도 상태 권한이 없는 청록색 Sphere만 사용한다.
- `[씬 Unity 확인]` `GameMapTest`에는 활성 근접 Brain 1개와 원거리 Brain 1개, protected anchor 2개가 있고 `GameMap1` 시험 좀비의 Brain·Action·Agent override는 비활성이다. 두 씬 모두 Missing Script 0, 검사 뒤 dirty false였다.
- `[Play Mode 확인]` corrected runtime NavMesh에서 두 Agent가 `isOnNavMesh=true`가 된 뒤 순찰·추적했다. 원거리 적은 7회 사격을 시도해 5회 실제 피해를 적용했고 Player 체력은 0이 됐으며, 죽은 대상을 추가 공격하지 않고 Patrol로 돌아갔다.
- `[최종 대표 Play Mode 확인]` 사용자 기준 한 번의 `GameMapTest` 직접 실행에서 위 결과를 다시 확인했다. 두 Agent는 모두 NavMesh ready였고, 원거리 적은 7회 시도·5회 피해로 Player HP를 0까지 낮췄으며 두 적은 죽은 대상을 놓고 다시 Patrol로 전이했다.
- `[Play Mode 호출 확인]` 근접 적과 Player를 공격 사거리 안에 둔 뒤 런타임 Cube 벽을 사이에 놓고 같은 `EnemyMeleeRushAction.TickCombat`을 호출했다. 벽이 있을 때 HP `100 → 100`, 벽을 제거한 뒤 HP `100 → 90`으로 공격 순간 LOS 차단을 확인했다.
- `[Play Mode 수명주기 확인]` 살아 있는 근접 Brain을 비활성화·재활성화했을 때 즉시 `AwaitingNavigation`으로 재기준화됐고, 이후 `Patrol`, `isOnNavMesh=true`, 새 path와 실제 velocity를 가져 이전 순찰 목적지 플래그에 막히지 않았다.
- `[Play Mode 호출 확인]` 공통 `DamageContext`로 원거리 적을 죽였을 때 `CausedDeath=true`, 사망 handler 1회, Brain·Action·Agent·피격 Collider 비활성화를 확인했다. 20절 후속 구현에서 같은 전이 뒤 root·렌더 유지와 시체 전리품 활성화까지 확장 확인했다.
- `[Play Mode 호출 확인]` Player가 instigator인 총성 자극을 근접 적 청취 반경에 발행하자 같은 호출 경계에서 `Investigate`로 전이하고 마지막 확인 위치를 자극 좌표와 정확히 맞췄다. 기억 만료 뒤 Patrol로 복귀했다.
- `[수정 과정]` 최초 smoke에서 두 Agent가 runtime NavMesh보다 먼저 활성화되어 `Failed to create agent because there is no valid NavMesh` Warning 2개가 발생했다. prefab Agent를 초기 비활성화하고 유효 보행면 확인 뒤 활성화하도록 근본 원인을 수정했으며 corrected 재실행에서는 같은 Warning이 새로 발생하지 않았다.
- `[컴파일 확인]` 최종 경계 수정 뒤 Unity asset refresh와 script compilation이 성공했고 신규 Error/Exception/Assert는 0이다.
- `[Console 기준선]` Console에는 Error 0, Warning 8개가 남아 있다. 기존 Input Manager 폐기 예고, MCP 서명, 이전 Animator와 외부 RenderTextureBaker 경고 6개에 더해 위 최초 smoke의 역사적 NavMesh Warning 2개이며 Console을 지우지 않았다. corrected 재실행 이후 같은 Warning delta는 0이다.
- `[에디터 상태 복원]` 최종 검증 뒤 `Application.runInBackground=false`, Edit Mode, 활성 `GameMap1`, scene dirty false로 되돌렸다.
- `[미검증]` 실제 키보드·마우스로 두 적을 상대하는 사용자 흐름, authored 벽을 사이에 둔 원거리 공격, 발소리·마법·발사체 생산자, Player HP 0 뒤 입력 차단과 Raid 실패, 씬 재입장 구독 누적, Windows Player build와 Profiler 수치는 이번 범위에서 확인하지 않았다.

---

## 20. 적 시체 전리품과 공용 게임플레이 검은 전환

### 사용자 요구와 범위

- `[사용자 요구][2026-08-24]` 적이 죽으면 즉시 제거하거나 외형을 숨기지 않고 시체로 남긴다. 사망 뒤 AI를 정지하고 시체에서도 인벤토리를 열 수 있어야 한다.
- `[사용자 요구]` 최초 실행 로딩 화면은 기존 흐름으로 별도 유지하고, 그 밖의 게임플레이 씬 전환은 재사용 가능한 검은 화면으로 처리한다.
- `[현재 구현 범위]` 두 시험 적의 scene-local 시체 전리품과 `GameMap1 ↔ GameMapTest`가 공유하는 persistent fade만 구현했다.
- `[제외 범위]` 사망 애니메이션, ragdoll, 정식 드롭 테이블·확률·수량, 시체 정리 시간, 시체·내용물 저장, 원정 결과와 최초 로딩 UI 디자인은 포함하지 않았다.

### 상태 소유권과 호출 흐름

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | 사망은 `EnemyStats.IsDead`, 시체 grid는 같은 적 root의 `Chest`, 이동 요청·pending 목적지는 `DirectSceneTravel`, 화면 alpha는 persistent `GameplaySceneTransitionFader`가 각각 하나의 원본을 가진다. |
| 수명 범위 | 적·시체·전리품 grid는 Enemy Entity/Scene, fader와 Player 입력 보류 상태는 persistent 셸의 Play Session, fade 한 회는 Travel Transition 수명이다. |
| 생성·파괴 주체 | 적 프리팹 인스턴스의 `Chest.Awake`가 grid를 한 번 만들고 scene unload가 시체와 함께 정리한다. fade Canvas는 `PersistentGameplayShell` 프리팹과 한 번 생성·보존된다. |
| 변경 진입점 | `ApplyDamage → EnemyStats >0→0 → Died → EnemyDeathHandler`가 행동 정지·시체 상호작용 활성화를 수행한다. `DirectSceneTravel.TryLoad → PrepareForTravel → TryCover → LoadSceneAsync → SceneSpawnController → FinishArrival → Reveal`이 씬 전환을 수행한다. |
| 포함 관계 | `EnemyDeathHandler`는 체력이나 grid 내용을 소유하지 않고 완료된 죽음을 관찰한다. fader는 목적지·Spawn ID·Player를 소유하지 않고 검은 화면만 표시한다. |
| 이전 규칙 | 시체와 Player 사이 아이템 이동은 일반 Chest와 같은 기존 원자적 drag/container API를 사용한다. 전환 중에는 열린 인벤토리와 drag를 같은 `CloseAllInventories` 경로로 먼저 정리한다. |
| 파생 표현 | 시체 root·렌더, 비활성 AI/Animator/Collider와 활성 전리품 Trigger는 `EnemyStats.IsDead`의 파생 상태다. 검은 Canvas와 입력 잠금은 pending 이동의 파생 실행 상태다. |
| 저장 경계 | Stage 20 구현 당시 ordinary 저장에는 시체·적 체력·전리품 grid와 fade 상태를 넣지 않았다. 이후 22절 Recovery checkpoint가 stable ID를 가진 적·시체·전리품을 저장하도록 확장됐으며 fade 상태는 여전히 저장하지 않는다. 시체 시작 아이템 ID 1/2는 시험 프리팹 데이터이며 정식 보상 확정이 아니다. |
| 업데이트 주체 | 사망 전이는 이벤트 1회이고 별도 시체 `Update`가 없다. fade만 `Time.unscaledDeltaTime` coroutine을 사용하며 기존 씬 이동 경계 외에 새 Manager나 Tick을 만들지 않았다. |

### 구현 내용

- `[코드 확인]` `EnemyDeathHandler`가 사망 시 비활성화할 Behaviour/Collider와 활성화할 시체 Behaviour/Collider를 명시 배열로 나눴다. 오브젝트 제거·Destroy·두 번째 사망 bool은 추가하지 않았다.
- `[프리팹 확인]` `KenneyZombiePatrol`과 `PrototypeRangedEnemy` root에 4×4 `Chest`와 기본 비활성 `ChestInteractable`을 연결했다. `CorpseInteraction` Trigger는 살아 있을 때 비활성이고 사망 뒤에만 켜진다. 좀비는 시험 ID 1, 원거리 적은 ID 2 하나를 가진다.
- `[코드 확인]` 시체는 기존 `PlayerInteractor`의 거리순 선택, 열린 대상 유지, 거리 이탈 자동 닫기와 `InventoryUIManager` 외부 인벤토리 UI를 그대로 사용한다. 별도 시체 Loot Manager/UI/컨테이너 복사본은 없다.
- `[수명 규칙]` 현재 시체는 scene unload 전 임의 비활성화·Destroy하지 않는다. 향후 despawn을 추가할 때는 먼저 공통 닫기를 요청하고 drag 복구가 거부되면 despawn 자체를 보류하는 coordinator가 필요하다.
- `[코드 확인]` Player 공격 Raycast는 죽은 `IDamageable`의 시체 Trigger를 utility Trigger처럼 건너뛰어 뒤의 살아 있는 대상에 대한 투명 장벽이 되지 않게 했다.
- `[코드/프리팹 확인]` persistent 셸 root sibling에 `GameplaySceneTransitionCanvas` 하나를 추가했다. 유휴 시 Canvas 비활성·alpha 0이고, 전환 중 최고 sorting order의 검은 Image가 전체 화면을 덮으며 raycast를 차단한다.
- `[코드 확인]` `DirectSceneTravel`은 fade-out 완료 뒤에만 `LoadSceneAsync`를 시작한다. 목적지 `SceneSpawnController`가 같은 Player를 배치한 뒤 fade-in하며, 완전히 투명해진 뒤 기존 이동·인벤토리·상호작용 상태를 복원한다. 공격과 무기 전환은 같은 인벤토리 입력 차단 상태를 읽는다.
- `[실패 경계]` 로드 완료 다음 프레임까지 목적지 배치가 완료되지 않으면 watchdog이 공통 `FailArrival`로 pending 요청과 입력 잠금을 정리한다. fade 컴포넌트가 전환 도중 비활성화되어 coroutine이 끊겨도 interruption callback이 같은 실패 정리 경로를 호출한다. 전환 중 `BasePersistenceController`의 F5와 IMGUI 저장 패널도 차단한다.
- `[시작 흐름 보존]` `InitialLoadingManager`, `MainMenuManager`, `GameLoadingManager`와 세 시작 씬은 수정하지 않았다. 공용 검은 fade는 `DirectSceneTravel`을 쓰는 게임플레이 직접 이동에만 적용된다.

### 2026-08-24 검증 결과와 한계

- `[정적 Unity 확인]` 두 적 프리팹은 살아 있을 때 시체 Interactable/Trigger 비활성, 사망 뒤 활성 참조 1개씩, 숨길 외형 0개, 피격 Collider 1개와 Brain/Action/Agent(좀비 Animator 포함) 정지 참조를 가졌다. 각 4×4 grid의 시험 아이템 ID와 ItemDatabase 참조도 확인했다.
- `[Play Mode 호출 확인]` GameMap1 좀비에 공통 `DamageContext`로 `100 → 0`을 적용했다. `CausedDeath`, `EnemyStats.IsDead`, handler 1회를 확인했고 root·Renderer는 활성, Brain·Action·Agent·Animator·피격 Collider는 비활성, 시체 Trigger와 전리품 상호작용은 활성, 아이템은 1개였다.
- `[Play Mode 호출 확인]` 실제 persistent Player를 시체 1.25m 옆에 두고 공개 `PlayerInteractor.TryInteract` 경로로 기존 외부 인벤토리를 열었다. 열린 대상이 해당 시체로 유지됐고 5m 밖으로 이동한 다음 프레임들에 UI와 대상 참조가 자동으로 닫혔다.
- `[Play Mode 확인]` 사용자 기준 한 번 `GameMap1 → GameMapTest → GameMap1` 왕복했다. 요청 직후 fade와 이동·인벤토리·상호작용 입력 잠금이 활성화됐고 중복 이동은 거부됐다. 양쪽 도착 뒤 같은 shell Entity와 Player Entity가 유지됐으며 active Camera, AudioListener, EventSystem은 각각 1개였다. fade-in 완료 뒤 해당 입력 상태가 복원됐다.
- `[코드/상태 확인]` GameMapTest 도착 시 살아 있는 근접·원거리 적 2개의 시체 상호작용과 Trigger가 모두 아직 비활성임을 확인했다. 최초 로딩 흐름과 관련 Manager에는 diff가 없다.
- `[컴파일/Console 확인]` 최종 script refresh/동적 검증 command compilation은 성공했고 Console Error 0, Warning 8 기준선에 신규 Error/Exception/Assert 또는 Warning delta가 없다. 기존 8개는 Input Manager, MCP 서명, 과거 Animator/NavMesh와 외부 RenderTextureBaker 경고다.
- `[에디터 상태 복원]` Play Mode를 종료하고 활성 `GameMap1`, dirty false, `Application.runInBackground=false`로 복원했다. 새 직렬화 필드 때문에 생긴 scene dirty는 복구 사본과 비교해 기존 Chest prompt 두 줄뿐임을 확인한 뒤 Unity API로 저장했으며 동일한 임시 사본은 휴지통으로 옮겼다.
- `[후속 해결]` 당시 비활성·오연결 상태였던 `PauseMenu`는 21절의 persistent 단일 Escape 소유 메뉴로 교체했다. 구형 컴포넌트와 스크립트는 참조가 없음을 확인한 뒤 제거했다.
- `[미검증]` 물리 키보드 E와 실제 마우스 drag로 시체를 루팅하는 사용자 입력, 픽셀 캡처로 fade 중 완전 검은 화면 확인, 잘못된 Spawn ID watchdog의 실제 실행, InitialLoadingScene부터 시작하는 전체 Player build, 시체 저장·랜덤 드롭과 Profiler 수치는 이번 범위에서 확인하지 않았다.

---

## 21. 컨텍스트별 Escape 메뉴와 최소 원정 결과

### 사용자 요구와 범위

- `[사용자 요구][2026-08-24]` Escape 입력은 한 곳에서만 처리한다.
- `[사용자 요구]` 기지에서는 실제로 게임을 일시정지하고 계속하기, 설정, 주 메뉴 이동을 제공한다. 원정 포기 버튼은 표시하지 않는다.
- `[사용자 요구]` 원정에서는 세계를 일시정지하지 않고 Player 조작만 막는다. 계속하기, 설정, 원정 포기와 주 메뉴 이동을 제공한다.
- `[사용자 요구]` 원정 중 포기 또는 주 메뉴 이동에는 “원정을 포기하시겠습니까?” 확인을 표시하며, 기지 또는 주 메뉴라는 목적지만 다르다.
- `[사용자 요구]` 생환과 Player 사망은 각각 한 번만 결과를 확정하고 최소 결과 화면을 표시한다.
- `[당시 제외 / 후속 구현]` 이 단계에서는 강제종료 뒤 원정 이어하기와 결과별 아이템 반영을 제외했지만, 이후 사용자 요청으로 22절의 일반 세이브 우선 원정 체크포인트 복구와 23절의 결과별 전체 소지품 정산을 구현했다. event log·좌표 replay, 별도 보상 지급과 최종 UI 디자인은 여전히 포함하지 않는다.

### 상태 소유권과 호출 흐름

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | gameplay scene 종류, 원정 수명주기와 정상 gameplay 결과는 `RaidSession`; Player HP·사망 전이·피해 허용은 `PlayerStats`; Escape 입력과 메뉴 화면 상태는 `GameplayEscapeMenuController`가 각각 하나의 원본을 가진다. durable exact 전 저장 실패가 결과를 `RecoveryFailed`로 fail-closed 전환할 수 있는 후속 예외는 22·23절을 따른다. |
| 수명 범위 | `RaidSession`과 Escape 메뉴는 persistent Player Shell의 Play Session, 원정 상태는 Raid, HP는 Player Entity, 확인·결과 패널은 UI 표시 수명이다. |
| 변경 진입점 | 맵 선택 → 원정 시작, 귀환 포탈 → 생환, `PlayerStats.Died` → 사망 실패, 확인된 포기 → 포기 결과로 수렴하며 `RaidSession`만 `Extracted`·`PlayerDied`·`Abandoned` 중 정상 gameplay 결과를 확정한다. durable exact 전 저장 실패의 `RecoveryFailed` 전환은 22·23절의 fail-closed 경계만 수행한다. |
| 파생 표현 | 메뉴 버튼·확인 패널·결과 패널은 scene 종류와 `RaidSession` 상태의 파생 UI이며 원정 결과를 별도로 쓰지 않는다. |
| 저장 경계 | 이 단계 당시에는 원정 상태·결과, Player 위치·HP, 적·맵 상태를 디스크에 저장하지 않았다. 현재 저장 경계는 22절의 후속 구현이 대체한다. |
| 업데이트 주체 | Escape는 persistent controller 하나가 매 프레임 읽고, 결과 전이는 명시적 호출 또는 Player 사망 완료 이벤트에서만 발생한다. |

### 현재 구현

- `[코드/프리팹 확인]` `GameplayEscapeMenuController`는 항상 활성인 persistent shell root에 있고, View인 `PauseCanvas`와 Main/Settings/Confirmation/Result 패널만 필요할 때 활성화한다. 버튼과 Toggle은 각각 한 개의 공개 기능 진입점에 연결돼 있다.
- `[코드 확인]` Escape 우선순위는 결과·전환 중 무시 → 확인 취소 → 설정에서 기본 메뉴 → 기본 메뉴 닫기 → 맵 선택 취소 → 인벤토리 안전 닫기 → 새 컨텍스트 메뉴 열기다. `InventoryUIManager`와 `MapSelectionOverlay`의 별도 Escape polling은 제거했다.
- `[코드/씬 확인]` `GameMap1`의 `SceneSpawnController`는 `Base`, `GameMapTest`는 `Raid`를 등록한다. 기지 메뉴는 `Time.timeScale = 0`, 원정 메뉴는 `Time.timeScale = 1`을 유지한다.
- `[코드 확인]` 메뉴는 Player 이동·공격·무기 전환·인벤토리·상호작용 입력을 함께 잠근다. 닫기 또는 이동 시작 전에 자신이 획득한 이전 상태만 복원한다.
- `[코드 확인]` 전환 시작부터 fade-in 완료까지 `PersistentGameplayShell`이 `PlayerStats`의 피해 진입점을 차단한다. 실패 취소는 이전 피해 허용 상태를 복원하고, 성공 도착은 입력 복원 뒤 `RaidSession.CompleteSceneArrival`이 새 컨텍스트에서 피해를 다시 허용한다.
- `[코드 확인 / 후속 확장]` 생환·사망·포기 결과가 확정되면 추가 피해를 거부한다. 사망 귀환은 기지 입력 복원 전에 체력을 최대치로 초기화한다. 이후 23절에서 `Extracted`는 같은 Player 인벤토리·장비를 전부 유지하고, `PlayerDied`·`Abandoned`·실제 `RecoveryFailed`는 같은 Player 객체 그래프에서 소지품·장비를 전부 비우도록 확장했다.
- `[코드 확인]` 주 메뉴 이동은 gameplay 직접 왕복과 분리된 `GameplaySessionExit`가 담당한다. 검은 fade 뒤 `MainMenuScene`을 로드하고 persistent shell과 기존 `GameManager`를 명시적으로 종료한다.

### 2026-08-24 검증 결과와 한계

- `[Play Mode 호출 확인]` 기지 메뉴 Main → Settings → Main → Closed를 확인했다. 메뉴가 열린 동안 `Time.timeScale=0`, Player 입력 세 종류가 잠겼고 닫은 뒤 `Time.timeScale=1`과 입력이 복원됐다.
- `[Play Mode 호출 확인]` 원정 메뉴에서 `Time.timeScale=1`과 Player 입력 잠금을 확인했다. 약 14초 동안 두 적의 Transform이 실제로 바뀌어 AI 시뮬레이션이 계속 진행됐으며 포기·주 메뉴 확인창을 각각 취소했을 때 원정 상태와 씬이 유지됐다.
- `[Play Mode 호출 확인]` Player 사망은 `PlayerDied` 결과와 실패 UI를 한 번 만들었고, 기지 도착 뒤 체력 100·결과 `None`·입력 정상 상태가 됐다. 포기는 `Abandoned` 한 결과로 기지에 한 번만 이동했다.
- `[Play Mode 호출 확인]` 귀환 포탈은 `Extracted`와 성공 UI를 만들고 두 번째 상호작용을 거부했다. 결과 확정 뒤 999 시험 피해는 `WasApplied=false`, 체력 100을 유지했다.
- `[Play Mode 호출 확인]` 원정 fade-out과 active scene의 fade-in 중 각각 999 시험 피해가 거부됐고, fade-in 완료 뒤에만 피해 허용과 Player 입력이 정상 복원됐다.
- `[Play Mode 호출 확인]` 원정의 주 메뉴 확인 뒤 `MainMenuScene`에서 `PersistentGameplayShell.Instance`와 `GameManager.Instance`가 모두 null이었고 active Camera·AudioListener·EventSystem은 각각 1개, `Time.timeScale=1`이었다. 같은 Main Menu에서 새 게임을 시작하자 이전과 다른 Shell/Player Entity로 깨끗한 `GameMap1` 세션이 생성됐다.
- `[프리팹/런타임 확인]` 메뉴 Canvas는 활성 상태에서 유효한 화면 Rect와 `0.62` runtime scale을 가졌다. Windows 캡처 도구는 해당 Unity 창에서 `SetIsBorderRequired` 시스템 인터페이스 오류로 실패했으므로 실제 픽셀 캡처와 물리 Escape/버튼 클릭은 미검증이다.
- `[컴파일/Console 확인]` 최종 script refresh는 성공했고 Console Error는 0이다. 작업 전 기준 경고 11개(Input Manager, MCP 서명, Animator/NavMesh, Unity AI 계정, 외부 RenderTextureBaker)에 더해 자동 검증 하네스가 kinematic 전환 뒤 velocity를 0으로 쓰며 만든 검증 전용 경고 8개가 Console 기록에 남아 있다. 해당 stack은 동적 `CommandScript`이며 프로젝트 런타임 코드 회귀가 아니다. Console은 기준선 보존을 위해 지우지 않았다.

---

## 22. 일반 세이브 우선 원정 중단 복구와 실시간 체크포인트

### 사용자 요구와 판정 순서

- `[사용자 요구][2026-08-25]` 첫 검사 대상은 복구 캐시가 아니라 일반 단일 슬롯 세이브다.
- 일반 세이브가 `raidInProgress=false`이면 원정 이어하기를 계산하지 않는다. 참조되지 않는 Recovery는 격리하며, 이미 ordinary save까지 기록된 exact 정산 저널의 동일 상태를 마무리하는 경우만 예외다.
- 일반 세이브가 `raidInProgress=true`이면 그 `activeRaidInstanceId`와 같은 Recovery 기준점·체크포인트를 그 다음에 검사한다.
- 표식은 있으나 같은 ID의 유효한 캐시가 없으면 애매하게 살리지 않고 `원정 실패 처리`만 허용한다.
- 같은 ID의 유효한 Active 체크포인트가 있을 때만 `이어하기`와 `원정 실패 처리`를 함께 표시한다.

### 권위 소유권과 저장 경계

| 확인 항목 | 현재 계약 |
|---|---|
| 첫 권위 소유자 | 프로세스 사이 “미정산 원정이 존재하는가”의 원본은 ordinary `GameSaveData.raidInProgress + activeRaidInstanceId`다. Recovery 파일만으로 원정을 되살리지 않는다. |
| 런타임 원본 | Player HP·Transform, 인벤토리, 기지 가구, Chest와 Enemy 상태는 기존 각 런타임 소유자가 계속 쓴다. `RaidCheckpointController`는 1초 간격으로 검증된 DTO를 투영할 뿐 두 번째 gameplay 권위자가 아니다. |
| Recovery 수명 | `RaidRecoveryBaselineData`는 출발 전 상태와 원정 ID, `RaidCheckpointData`는 같은 원정의 순번별 snapshot, `RaidSettlementJournalData`는 실패·종료·exact 정산 의도를 담는다. 정상 정산 뒤 전부 삭제한다. |
| 변경 진입점 | 새 원정 출발은 ordinary 표식 미러 저장을 먼저 완료하고 그 뒤 baseline을 만든다. 주기 snapshot은 전환·드래그 중에는 건너뛰며, 정산은 저널 → ordinary 주·백업 → Recovery 삭제 순서로 커밋한다. |
| 저장 범위 | Player 현재 HP·Transform, Player 인벤토리/장비, 기지 가구 상태, 도심 seed·generator version·layout hash, 안정 ID가 있는 원정 Chest, Enemy 생존·HP·Transform·시체 인벤토리를 저장한다. |
| 의도적 제외 | AI의 현재 행동 상태·경로 코너·감지 기억, 총알·VFX·SFX, 열린 UI·드래그, 프레임별 좌표 로그는 저장하지 않는다. 복원 뒤 권위 상태에서 다시 계산한다. |

### 구현된 실패 폐쇄 규칙

- ordinary primary를 먼저 읽는다. primary header를 읽지 못하거나 동일 원정 표식 payload의 전체 검증이 실패할 때만 backup을 후보로 사용한다. 유효한 active primary가 다른 원정이나 다른 상태라고 말하면 더 오래된 backup으로 조용히 되돌리지 않는다.
- 새 원정 표식을 ordinary 주·백업에 먼저 기록했는데 baseline 생성 전에 종료되면, 다음 실행은 `표식 있음 + 캐시 없음`으로 판정해 실패 처리만 제시한다.
- baseline과 출발 전 exact 상태까지 기록했지만 원정 씬 진입 전에 전환이 실패하면 그 exact payload를 출발 취소의 최종 권위로 사용한다. outcome 이름이 `RecoveryFailed`여도 실제 원정 실패의 빈 아이템 정책을 다시 적용하지 않고 출발 전 Player·기지 상태를 그대로 복원한다.
- Active 체크포인트는 primary와 backup을 각각 전체 검증하고 같은 원정 ID에서 가장 최신 순번을 사용한다.
- 생환·사망·포기 결과가 확정되면 Resolved 체크포인트뿐 아니라 같은 결과와 영속 payload를 exact 저널 주·백업에 즉시 고정한다. 종료 primary가 손상돼도 이전 Active backup을 이어하기로 되살리지 않는다.
- persistent state가 없는 marker-only 저널은 `RecoveryFailed` 결과에만 유효하다. 저장 실패 중 더 최신 failure marker가 앞선 Resolved 결과를 덮는 경우에는 authoritative primary 우선 규칙으로 같은 저널을 다시 검증한 뒤에만 실패 정산을 허용한다.
- 정산 저널이 ordinary save까지 기록된 뒤 프로세스가 종료되면, 다음 실행은 ordinary와 canonical JSON이 같은 exact 저널만 다시 적용해 미러 저장과 Recovery 정리를 반복한다.
- 같은 실행에서 ordinary 주·백업 반영 뒤 Recovery 파일 삭제가 일부만 성공하면, immutable exact state와 ordinary canonical 일치를 다시 확인한 뒤 삭제 단계만 재시도한다. 이미 소비된 baseline·저널을 다시 요구해 입력 잠금이 영구화되지 않게 한다.
- 정산 커밋이 실패하면 `RaidCheckpointController`가 이동·인벤토리·상호작용·피해 입력을 잠근다. 성공한 `ResetTrackedRaid`에서만 원래 입력 상태를 복원하므로 exact 저널과 이후 live 변경이 갈라지지 않는다.

### 로딩 경계

- `InitialLoadingScene → MainMenuScene`은 게임 최초 실행용 메인 로딩이다.
- Main Menu의 New Game, Load Game, 원정 Resume/실패 정산은 `GameLoadingScene → GameMap1` 공통 진입을 사용한다.
- 실행 중 `GameMap1 ↔ GameMapTest` 왕복은 위 두 로딩 씬을 거치지 않는다. persistent `GameplaySceneTransitionFader` 하나가 검은 화면으로 직접 전환을 감싼다.

### 2026-08-25 검증 결과

- `[격리 파일 계약 확인]` ordinary active 표식 주·백업, baseline, 회전 checkpoint, 손상 primary에서 정상 backup, exact settlement journal 주·백업과 전체 cleanup을 실제 파일로 확인했다.
- `[메인 메뉴 상태 행렬 확인]` 표식 없음+캐시, 표식+Active, 표식만 있음, markerless exact cleanup, markerless stale journal, active invalid exact의 여섯 상태가 각각 격리·Resume/Fail·실패 전용·정산 계속·차단 규칙을 따랐다.
- `[Play Mode E2E 확인]` 새 원정에서 ordinary 표식과 동일 ID baseline/Active checkpoint를 만든 뒤 Player 체력 77, 위치 `(17.25, 0.5, 23.75)`를 기록했다. 런타임 셸을 종료하고 Main Menu에서 Resume한 뒤 같은 GameMapTest, 원정 ID, 체력과 위치가 복원됐다.
- `[Play Mode 회귀 확인]` `Abandoned` 종료 뒤 Resolved primary, Active backup과 exact 저널 주·백업을 확인했다. 종료 primary를 손상시킨 다음 Main Menu에서 Resume은 비활성, `정산 계속`만 활성화됐다.
- `[Play Mode 실패 경계 확인]` ordinary 표식을 의도적으로 어긋나게 해 기지 정산을 실패시키자 settlement lock이 유지됐다. 같은 ID 표식을 복구해 재시도하자 ordinary save가 정산되고 Recovery가 삭제된 뒤 이동·인벤토리·상호작용·피해 상태가 원래대로 한 번 복원됐다.
- `[Play Mode 부분 cleanup 확인]` 격리 저장소의 checkpoint 파일을 점유해 ordinary 주·백업 기록 뒤 Recovery 삭제만 중간 실패시켰다. baseline이 이미 삭제되고 input lock이 유지된 상태에서 재호출하자 immutable exact state와 ordinary canonical 일치를 확인하고 cleanup만 완료해 lock을 해제했다.
- `[동적 계약 확인]` marker-only 저널은 `RecoveryFailed`만 통과하고 `Abandoned` 등 persistent state 없는 다른 terminal outcome은 거부되는 것을 확인했다.
- `[컴파일/씬 확인]` Unity script compile 성공, 최종 `GameMap1` Edit Mode, scene dirty=false다. 이 절의 위 검증은 Editor 전용 격리 저장 루트에서 수행했으며 실제 사용자 슬롯은 변경하지 않았다. 별도의 실제 Windows 프로세스 검증은 23절에 기록한다.

---

## 23. 원정 결과 아이템 정산, 재현 가능한 프로젝트 기준선과 Windows 중단 복구 검증

### 확정한 현재 규칙

- `[사용자 승인][2026-08-25]` `Extracted`는 원정 종료 시 Player grid와 장비칸의 모든 아이템을 그대로 유지한다.
- `PlayerDied`, `Abandoned`, 실제 원정의 `RecoveryFailed`는 Player grid와 장비칸의 모든 아이템을 잃는다. 루트 컨테이너 안의 중첩 아이템도 그 컨테이너와 함께 Player 소유에서 빠진다.
- 기지 가구와 기지 Chest 내용은 모든 원정 결과에서 안전하며 아이템 손실 정책이 변경하지 않는다.
- 현재 save `recordId`는 파일 안 관계 키일 뿐 영구 아이템 instance ID가 아니므로, 출격 전 소지품과 원정 획득물만 골라서 다르게 처리하지 않는다. 그런 규칙이 필요해질 때 provenance를 추가한다.
- 원정 씬에 들어가기 전에 scene load가 실패한 **출발 취소**는 실제 원정 실패와 구분한다. 저널 outcome은 `RecoveryFailed`여도 exact payload가 출발 전 상태를 권위 있게 보존하므로 아이템을 잃지 않고 원래 상태로 되돌린다.

### 권위 소유권과 호출 흐름

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | live Player grid·장비는 기존 `PlayerInventoryState`, 원정 결과는 `RaidSession`/복구 시 검증된 terminal outcome, 디스크 정산 payload는 한 번 고정된 exact settlement state가 각각 원본이다. `RaidItemSettlementPolicy`는 상태를 소유하지 않는 순수 변환 규칙이다. |
| 수명 범위 | Player 객체 그래프는 Play Session, 원정 결과·정산은 Raid, ordinary save와 exact journal DTO는 프로세스 사이 영속 수명이다. |
| 변경 진입점 | 정상 종료는 terminal checkpoint/저널 생성 뒤 기지의 `TryCommitTrackedRaidAtBase`; 메뉴 복구는 `BasePersistenceController`가 검증된 exact/fallback을 적용한 뒤 같은 commit 진입점으로 수렴한다. |
| 포함 관계 | Player grid와 장비가 루트 아이템을 소유한다. 중첩 아이템은 자신의 컨테이너가 소유한다. 기지 `BaseFurnitureStateStore`는 별도 권위 경계이며 손실 정책에 포함되지 않는다. |
| 이전 규칙 | 실패 정산은 UI/drag를 공통 안전 경로로 닫은 뒤 같은 grid·equipment 인스턴스에서 모든 Player 루트 소유권을 해제한다. 중간 실패 시 원래 배치를 복구하고 부분 소실을 성공으로 보고하지 않는다. |
| 파생 표현 | Inventory/Equipment UI와 ordinary/Recovery DTO는 원본의 파생 표현이다. exact 저널이 생긴 뒤에는 그 immutable payload를 ordinary mirror와 cleanup 재시도에 그대로 사용한다. |
| 저장 경계 | v4 `PlayerItemStateSaveData`의 definition ID·배치·회전·컨테이너 부모·장비칸을 정산한다. 내구도·탄약·개별 영구 ID·provenance는 아직 저장 대상이 아니다. |
| 업데이트 주체 | 결과 확정과 기지 정산 경계에서 한 번만 실행한다. 별도 `Update`, 전역 검색, 평행한 inventory manager는 추가하지 않았다. |

### 구현 내용

- `[코드 확인]` `RaidItemSettlementPolicy`는 `Extracted`에서 원본 persistent payload를 유지하고, 세 실패 결과에서는 clone의 `playerItems`만 같은 크기의 빈 payload로 교체한다. `baseState`는 건드리지 않는다.
- `[코드 확인]` `PlayerInventoryState.TryDiscardAllCarriedItems`와 `InventoryUIManager`의 공통 진입점이 같은 persistent Player grid·equipment 객체를 유지한 채 루트 아이템을 원자적으로 제거한다. Player나 UI를 재생성하지 않는다.
- `[코드 확인]` terminal checkpoint, exact settlement journal, ordinary 주·백업 저장이 같은 결과 payload를 사용한다. 실패 정산 뒤 재실행해 더 오래된 Active inventory가 부활하지 않는다.
- `[코드 확인]` exact journal이 있으면 outcome enum으로 다시 계산하지 않는다. exact가 빈 Player payload일 때만 live Player를 비우고 즉시 다시 캡처해 canonical 동일성을 확인한다. 출발 취소의 non-empty exact는 그대로 적용·재사용한다.
- `[코드 확인]` 정산 저널 형식 v2는 `OutcomeSettlement`, `RecoveryFailureMarker`, `FreshDepartureRollback`을 명시적으로 구분한다. 실패 outcome의 일반 exact는 빈 Player payload만, 출발 취소 exact는 baseline `startingState`와 canonical 동일할 때만 허용한다. 구형 v1의 `RecoveryFailed + settlementState 없음` marker-only 형태는 의미가 명확해 호환하고, 종류를 구분할 수 없는 v1 exact는 추측해 변환하지 않고 fail-closed로 차단한다.
- `[UI 확인]` 최소 결과 문구도 생환 시 전체 소지품 유지, 실패 시 전체 소지품 소실 규칙과 일치하도록 갱신했다.

### 2026-08-25 검증 결과

- `[동적 계약 확인]` 동일한 원본 DTO로 네 terminal outcome을 검사했다. `Extracted`만 Player item record를 그대로 유지했고 `PlayerDied`·`Abandoned`·`RecoveryFailed`는 Player payload를 비웠으며, 원본 DTO·grid 크기·base JSON은 바뀌지 않았다.
- `[동적 객체 그래프 확인]` Player grid의 컨테이너 1개와 그 중첩 아이템, 장비 1개를 둔 상태에서 정산했다. `PlayerInventoryState`, grid, equipment 인스턴스는 같았고 Player 루트와 장비만 제거됐으며 중첩 아이템은 제거된 컨테이너의 소유로 유지됐다. equipment 변경 통지는 1회였고 빈 상태 재호출도 안전했다.
- `[동적 참조 동일성 확인]` 값 동등성 `Equals`가 같은 서로 다른 두 `InventoryItemData`를 Player grid에 배치해도 별개 root로 인식해 둘 다 제거했다. grid·equipment 인스턴스는 그대로였고 두 번째 빈 정산 호출도 안전했다.
- `[동적 v2 호환성 확인]` 생환 exact, 세 실패 empty exact, marker-only 실패와 출발 취소 exact를 허용하고 실패 non-empty exact, 잘못된 marker/fresh payload와 모호한 v1 exact를 거부했다. 구형 v1 marker-only 실패 호환과 `GameStartRequest`가 fresh rollback kind를 Base 진입 요청까지 그대로 운반하는 것도 확인했다.
- `[Play Mode E2E 확인]` Editor 전용 격리 저장소에서 실제 원정을 한 번 실행했다. AI 공격으로 `PlayerDied`가 확정된 뒤 기지로 돌아오자 live Player item record `6 → 0`, ordinary primary/backup `0`, Recovery 정리 완료를 확인했다. 기지 상태 SHA-256은 전후 `C1CE71F84065618B3B71DC017633EA9617E7CBF56E02B026A2E6A1B914889BAD`로 동일했다.
- `[Windows Build 확인]` 활성 5개 씬을 포함한 Windows Development Build가 error `0`, 기존 에셋·패키지 계열 warning `491`로 성공했다. `ProjectSettings.asset`은 빌드 전후 SHA-256 `67D9A8F5902A9FA593411515FCC3F4F1307FF37290073AFDB8A2BE1874071868`로 같았다.
- `[실제 프로세스 중단 E2E 확인]` 사용자 저장과 분리한 company/product 저장 경로의 Windows Player에서 실제 새 원정을 시작하고 PID `26088`을 정확한 exe 경로로 재확인한 뒤 강제 종료했다. 같은 exe를 다시 실행해 실제 공개 `MainMenuManager.ResumeInterruptedRaid()` 경로로 같은 raid ID `f9c06651-7d92-4797-a8e3-0864b9701af8`를 이어서 열었다. seed `557376427`, layout hash `657E1CB91C9075AA`, Player 위치·HP `77`·item record `6`과 저장 대상 Chest/Enemy 전체의 정규화된 checkpoint JSON이 일치했다.
- `[보호 확인]` 실제 사용자 `Saves`는 생성·변경하지 않았고 기존 `DefaultCompany` 파일의 hash와 timestamp도 같았다. 검증 전용 build, driver, LocalLow 저장소와 임시 로그는 대상 절대경로를 확인한 뒤 삭제했다. 기존 `Builds/SaveLoadPrototype`은 사용자 기존 산출물이므로 그대로 두고 ignore했다.
- `[컴파일/씬 확인]` exact 출발 취소 예외 수정 뒤 Unity 강제 refresh와 script compilation이 다시 성공했다. 최종 상태는 Edit Mode, 활성 `GameMap1`, scene dirty=false다. 독립 코드 재검토에서도 exact non-empty 출발 취소와 exact empty 실제 실패가 각각 보존/소실로 수렴하며 새 P1/P2가 없음을 확인했다.
- `[Console 기준선]` 최종 전체 조회는 Error `0`, 기존 build/import 기록 Warning `47`이었다. Warning은 Sentis/AI Inference 셰이더, 외부 grass 셰이더와 obsolete `RenderTextureBaker` API이며 이번 정산 코드를 지목하지 않는다. Console을 해결 수단으로 지우지 않았다.

### Git·재현성 기준선과 남은 물리적 한계

- `[현재 추적]` `Packages/manifest.json`, `Packages/packages-lock.json`, `.vsconfig`, `ProjectSettings`의 공유 설정을 Git 기준선에 포함한다. Unity AI 개인 연결 설정, `Assets/_Recovery`, 생성 빌드와 사용자 save는 ignore한다.
- `[보존]` 사용자 미추적 자료 `pixel_character_pipeline.json`과 기존 2026-08-20 build는 이번 변경에 포함하거나 수정하지 않는다. `스크립트_사용_분석.md`는 이후 사용자 요청으로 원문 그대로 별도 문서 커밋했다.
- 저장장치가 terminal checkpoint, failure marker, journal과 ordinary save의 모든 쓰기·삭제를 동시에 거부하면 다음 프로세스에 결정을 남길 물리적 매체가 없다. 최소 하나의 durable 결정이 남는 정상·부분 I/O 실패는 fail-closed 처리하지만, 전면 I/O 거부까지 성공으로 보장한다고 주장하지 않는다.

---

## 24. 생존 탈출 장르 플레이·알고리즘 계약

- `[사용자 요구][2026-08-25]` 이 프로젝트가 요구하는 생존 탈출 플레이 방식과 시스템 알고리즘을 별도로 정리해, AI가 일반 RPG·웨이브 생존·PvP·선형 던전 등의 전제를 섞어 임의 구현하지 않게 한다.
- `[문서 적용]` `extraction_survival_gameplay_contract.md`를 새 기준 문서로 만들었다. 기지 준비 → 출격 → 탐색·루팅·교전 또는 회피 → 탈출 판단 → 권위 있는 최종 결과의 멱등 정산 → 재정비 루프와 플레이어가 각 단계에서 내려야 하는 판단을 고정했다.
- `[장르 경계]` 적 전멸이 아니라 생환이 성공이며, 회피·후퇴·조기 탈출도 정상적인 전략이다. “생존”을 근거로 허기·갈증·제작을, “탈출”을 근거로 PvP·축소 자기장·제한 시간을 자동 추가하지 않는다.
- `[알고리즘 경계]` 원정 수명과 단일 정산, 원자적 아이템 소유권 이전, seed 기반 제약형 맵 생성과 접근 가능성, 관측 기반 AI와 의도적으로 불완전한 사격, ordinary marker 우선 중단 복구를 장르 요구와 연결했다.
- `[문서 연결]` `AGENTS.md`의 내부 지시 우선순위와 재동기화 목록에 이 계약을 추가하고, `extraction_survival_game_design_dev_plan.md`는 구현 Stage 문서로서 장르 계약을 덮어쓰지 않도록 역할을 분리했다.
- `[낡은 기록 정정]` AGENTS의 사망 손실·기지 Chest·Recovery 상태, 설계 문서의 현재 시험 Hitscan과 seed 저장 경계, `ai_generation_plan.md`의 Player 사망 단계 표시를 최신 구현 기록과 맞췄다.
- `[제외 범위]` 이 문서 작업은 Unity 코드·씬·프리팹과 현재 게임 규칙을 변경하지 않았다. 탄약, 무게, 제한 시간, 상점, 제작, 퀘스트, provenance 선별 손실, 최종 탈출 조건과 콘텐츠 수치는 계속 `[미정]`이다.

---

## 25. 계층형 본 게임기획서

- `[사용자 요구][2026-08-25]` 게임기획서를 `1 → 1.1 → 1.1.1`처럼 세부 항목까지 나누고, 요소·기능·콘텐츠·UI 설계를 현재 프로젝트에 맞게 일부 정리하고 새로 기획한다.
- `[문서 적용]` `game_design_document.md`를 새로 만들었다. 문서 사용 규칙부터 게임 개요, 전체 루프, Player, 전투, 아이템·장비·루팅, AI, 맵, 기지, 성장·경제·퀘스트, UI/UX, 저장·복구, 콘텐츠 카탈로그, 세계관, 아트·사운드, 모딩, 마일스톤, 플레이테스트와 미정 결정 목록까지 계층적으로 기록했다.
- `[상태 경계]` 사용자 결정은 `[확정]`, 검증된 프로젝트 사실은 `[현재]`, 프로토타입 동작과 수치는 `[현재 시험]`/`[현재 시험값]`, 새 기획은 `[설계 제안]`, 결정 전 항목은 `[미정]`으로 분리했다. `[설계 제안]`은 다음 구현 권한이 아니다.
- `[문서 연결]` `AGENTS.md`, 장르 계약과 Unity Stage 문서에 본 GDD의 역할을 연결했다. 장르 불변조건은 `extraction_survival_gameplay_contract.md`, 플레이어 대상 기획은 `game_design_document.md`, 구현 의존성은 `extraction_survival_game_design_dev_plan.md`, 실제 완료 증거는 이 진행 기록이 각각 담당한다.
- `[현재 사실 반영]` W1만 활성인 장비 UI와 데이터에 예약된 W2·W3, 현재 8×9 Player grid, definition ID와 runtime item의 차이, ordinary v4·Recovery 정산, NavMesh 기반 유동 순찰, 도심 생성기의 현재 검증과 아직 없는 raid-ready 실패 gate를 구분해 기록했다.
- `[문서 검증]` 0~19장, 152개 절과 238개 세부 절의 부모 번호·중복·필수 장·Markdown 표·code fence를 정적 검사했다. 현재 사실, 문서 구조, UI·콘텐츠 관점의 독립 교차 검토에서 남은 P1/P2가 없음을 확인했다.
- `[제외 범위]` Unity 코드·씬·프리팹, 현재 게임 규칙과 콘텐츠 에셋은 변경하지 않았다. 새로 제안한 경제, 퀘스트, 최종 전투, LootTable, 랜드마크, 세계관 세부와 정식 UI 아트는 사용자 결정 전까지 구현하지 않는다.

---

## 26. Player 화폐와 무지갑 시험 상인

### 사용자 요구와 현재 시험 규칙

- `[사용자 요구][2026-08-26]` Player 인벤토리 위에 금·은 액수를 표시하고 각각 5000으로 시작한다. 상인은 화폐를 갖지 않으며 Player 판매 때 상인 잔액과 공간을 검사하지 않는다.
- `[현재 시험]` ItemDefinition ID 1~5를 Player와 상인의 동일한 초기 품목으로 사용한다. ID 1/3/5는 은 100, ID 2/4는 금 100이다. 금·은은 서로 합산하거나 환전하지 않으며 이 가격과 초기 잔액은 최종 밸런스가 아니다.
- `[현재 시험]` 신규 Player와 시험 상인 재고 및 현재 거래에서 Container를 제외한다. 기존 저장의 Player·기지 Container는 무음 삭제하지 않는다.
- `[현재 시험]` Player UI는 왼쪽, 장비는 그 옆, 상인 등 외부 inventory는 오른쪽이라는 기존 배치를 유지한다. 상인 쪽에는 전체·장비·기타 표시 탭을 둔다.

### 권위 소유권과 거래 경계

| 확인 항목 | 현재 계약 |
|---|---|
| 화폐 원본 | `PlayerInventoryState.PlayerWallet` 하나가 Gold/Silver를 쓴다. Merchant에는 wallet·balance가 없다. |
| 상인 재고 원본 | 기존 persistent `GameManager`의 `BaseMerchantStateStore`가 stable merchant ID별 grid를 소유한다. GameMap1 Cube는 `Merchant` View다. |
| 변경 진입점 | drag는 기존 `VariableInventoryCore`, Shift+클릭은 같은 `InventoryTransferCoordinator`가 조정한다. grid 원본은 각 container API만 변경한다. |
| 구매 | 거래 가능·잔액·Player 목적지 배치를 사전 검사하고 아이템 이전 성공 뒤 Player만 차감한다. 실패하면 원래 상인 슬롯과 잔액을 유지한다. |
| 판매 | 거래 가능·Player 지급 상한을 사전 검사하고 Player 원본 제거 성공 뒤 Player만 지급한다. 판매품은 merchant grid에 넣지 않는 sink다. |
| 파생 표현 | Wallet Text, 상품 가격 문구, 전체·장비·기타 탭과 drag 초록·빨간 preview는 원본의 View다. 탭은 stock과 배치 mask를 변경하지 않는다. |
| 저장 경계 | ordinary v5와 Recovery persistent state가 Player currency v1과 base merchant stock v1을 함께 운반한다. 가격·탭·열린 UI는 저장하지 않고 definition/UI에서 재구성한다. |

### 구현·감사 결과

- `[코드 확인]` `InventoryTransferCoordinator`는 상자·시체의 기존 first-fit 이동도 같은 경계에서 처리하며, 판매 sink에 merchant 공간이나 자금을 묻지 않는다. Shift 실패는 exact source slot으로 rollback하고 화폐를 바꾸지 않는다.
- `[코드 확인]` drag 정책과 preview가 같은 거래 판정을 사용한다. 판매 sink를 merchant grid의 점유 상태 때문에 빨간색으로 표시하거나, 잔액 부족 구매를 초록색으로 표시하던 불일치 경로를 차단했다.
- `[버그 수정]` 거절·공간 부족·drag 취소 뒤 같은 이미지 asset을 원래 셀에 복구할 때 꺼진 아이콘이 다시 켜지지 않던 `StandardCell` cache를 정리했다. 늦은 async 이미지 callback도 현재 cell/request와 일치할 때만 반영한다.
- `[저장 감사]` v2/v3/v4→v5 migration, ordinary/Recovery 내부 상태 정규화, 구형 journal v1 marker-only, exact DTO 재직렬화 시 authored merchant 초기화 provenance, stable ID·8×9 layout·ItemDatabase 동일성, tradable/non-container stock과 전체 allocation 예산을 검증한다.
- `[씬/프리팹 확인]` `GameMap1`에 `base:merchant_test` Cube 하나를 `(-2, 1, 1)`에 두고 `Merchant`, `MerchantInteractable`, Collider와 `BasePersistenceController.persistentMerchants`를 연결했다. `PersistentGameplayShell`에는 Player WalletPanel과 상인 controls의 직렬화 참조 8개가 있으며 Missing Script는 0이다.
- `[동적 순수 로직 확인]` 메모리 runtime 객체로 Shift 판매 제거·Player 지급·merchant 용량 무관 sink, Shift 구매 이전·Player 차감, 잔액 부족 양쪽 불변, Player 공간 부족 source rollback·무차감, Container 판매 거부·무지급을 포함한 11개 검사를 통과했다.
- `[Play Mode 부분 확인]` GameMap1에 한 번 진입해 shell의 신규 Player IDs1~5 생성과 BaseEntry 배치를 확인했고 런타임 Console 오류는 0이었다. 검증 도구의 private field 접근 제한 때문에 같은 실행에서 실제 E 열기, quick 거래, 탭, 거리 이탈과 codec 호출은 완료하지 못했으며 반복 Play 검증은 하지 않았다.
- `[최종 Editor 상태]` Edit Mode, 활성 `GameMap1`, scene dirty=false, script compile 오류 0이다. 기존 경고 3개는 Input Manager 안내, Codex 실행 파일 서명 수집과 외부 `RenderTextureBaker` obsolete API다.

### 조건부 직접 조작 회귀 절차 — 자동 다음 작업 아님

- `[사용자 확인·정정][2026-08-26]` 현재 정상 작동하는 거래를 다음 기능 전에 반복 검증하지 않는다. 아래 절차는 거래·입력·저장 관련 코드가 실제로 바뀌거나 사용자가 회귀를 보고했을 때만 대표 시나리오 1회에 사용한다.

- Player가 Cube 상인 가까이에서 E를 눌렀을 때 Player·장비·상인 UI가 함께 열리는지 확인한다.
- Shift+클릭과 drag로 구매·판매를 각각 한 번 실행해 잔액, first-fit, 판매 sink와 실패 rollback 표시를 확인한다.
- 전체·장비·기타 탭과 거리 이탈 자동 닫기를 확인한다.
- 사용자 슬롯과 분리한 저장소에서 거래 뒤 F5 → 재실행 Load로 Player 잔액과 merchant stock 복원을 확인한다.

---

## 27. 공용 아이템 툴팁과 상인 전용 가격 배지

### 사용자 요구와 범위

- `[사용자 요구][2026-08-26]` 모든 인벤토리·장비 아이템은 hover 시 설명과 현재 존재하는 능력치를 표시한다.
- `[사용자 요구]` 가격은 상인 재고의 각 아이템에 회색 거래 표시와 함께 직접 표시하되, 같은 아이템이 Player·Chest·시체 또는 장비칸에 있을 때는 표시하지 않는다.
- `[보존]` 기존 drag·회전·Shift 거래·분류 탭·장비·상자·시체·저장 v5와 아이템 소유권 경계를 변경하지 않는다.
- `[제외 범위]` 새 능력치·내구도·탄약·품질 설계, 빈 description의 임의 작성, 구매가·판매가 분리, 정식 UI 아트와 해상도별 최종 배치는 포함하지 않는다.

### 권위 소유권과 표시 경계

| 확인 항목 | 현재 계약 |
|---|---|
| 정의 원본 | 이름·description·크기·장비 분류·현재 무기/컨테이너 수치와 거래 가격은 immutable `ItemDefinition` 하나에서 읽는다. |
| 런타임 원본 | `InventoryItemData`와 기존 grid·equipment owner가 아이템 배치·회전·소유권을 계속 관리한다. 툴팁과 배지는 이를 쓰지 않는다. |
| 표시 진입점 | 등록된 공용 셀 hover는 `VariableInventoryCore.HoveredCellChanged` 완료 통지 하나로 수렴하고, `InventoryUIManager`가 정의를 공용 tooltip View에 전달한다. |
| 가격 범위 | `InventoryUIManager`가 Merchant 모드의 `externalStashView`에만 가격 provider를 설정하고 Storage 전환·닫기에서 제거한다. |
| 수명 범위 | tooltip View 하나는 기존 `PersistentGameplayShell`과 Play Session 동안 유지된다. 셀 배지는 공유 `StandardCell` 프리팹의 기본 비활성 파생 표현이다. |
| 파생 표현 | 이름·설명·스탯 문자열, 가격 배지, hover 위치와 분류 필터는 모두 원본에서 다시 만들 수 있는 View다. |
| 저장 경계 | tooltip·가격 배지·hover·분류 표시 상태는 저장하지 않는다. ordinary v5와 Recovery 형식은 변경하지 않았다. |
| 업데이트 주체 | hover enter/exit·drag·탭·닫기 이벤트로 표시 상태를 바꾸고, 보이는 tooltip 위치만 `LateUpdate`에서 마우스를 따른다. |

### 구현·근본 수정

- `[코드 확인]` `InventoryItemTooltipFormatter`가 definition에서 이름·설명·분류·인벤토리 크기와 실제 정의된 장비/무기/컨테이너 수치만 만든다. 현재 비어 있는 description은 임의 설정 대신 `설명 정보가 없습니다.`로 표시한다.
- `[코드/프리팹 확인]` persistent 셸에 공용 `InventoryItemTooltipView` 하나를 추가했다. tooltip과 배지의 모든 Graphic은 raycast를 받지 않으며 tooltip은 override sorting order 100으로 외부 인벤토리 뒤에 가려지지 않는다.
- `[코드/프리팹 확인]` 공유 `StandardCell`은 view가 제공한 badge 문자열이 있고 아이템이 현재 보일 때만 58×19 회색 배지를 켠다. 배지는 회전하는 아이콘 target이 아니라 `sizeRoot` 아래에 있어 아이템 회전 시 글자가 돌아가지 않는다.
- `[근본 수정]` 6×12와 8×9처럼 총 칸 수는 같지만 모양이 다른 외부 grid 전환에서도 `GridLayoutGroup`의 열 수·셀 크기·간격을 현재 데이터에 매번 다시 묶는다. 칸 수가 달라질 때는 이전 런타임 셀 오브젝트를 정리한 뒤 새 규격으로 만든다.
- `[근본 수정]` 분류 탭으로 숨긴 상인 아이템은 일반 hover highlight도 표시하지 않는다. setup 메뉴는 두 대상 프리팹만 명시 저장하며 다른 dirty 에셋 전체를 `SaveAssets`로 덮지 않는다.
- `[상태 정리]` drag 시작·취소, view 제거, 분류 탭 변경, 데이터 refresh, 인벤토리 닫기와 manager 비활성화에서 tooltip을 숨긴다. 늦게 도착한 이전 셀의 exit가 새 hover를 지우지 않게 현재 셀만 clear한다.

### 2026-08-26 검증 결과와 한계

- `[컴파일/Console 확인]` 최신 스크립트 강제 refresh와 compilation이 성공했고 새 MonoScript 3개가 정상 로드됐다. 검증 전·Play 중·종료 뒤 Console Error/Warning/Log는 모두 0이었다.
- `[프리팹 확인]` `StandardCell`의 배지 Rect 58×19, 직렬화 참조, 기본 비활성과 pointer 통과를 확인했다. `PersistentGameplayShell`의 tooltip 참조, 기본 비활성, sorting order 100과 pointer 통과를 확인했으며 두 프리팹 모두 Missing Script 0이었다.
- `[Play Mode 호출 확인]` Play Mode는 한 세션만 사용했다. Player를 시험 상인 가까이 배치하고 공개 `MerchantInteractable.Interact(PlayerInteractor)`를 호출한 뒤 EventSystem pointer enter/exit와 탭 Button의 `onClick`을 사용했다. 상인/Player 가격 배지는 `5/0`, 양쪽 아이템 tooltip 표시와 이름 일치, 탭 전환 뒤 tooltip 숨김, `CloseAllInventories` 뒤 tooltip과 전체 패널 닫힘을 확인했다.
- `[보호 확인]` Computer Use와 OS 입력 모사는 사용하지 않았다. `TestMerchantGraybox.mat` 등 무관한 Unity 에셋과 사용자 미추적 `pixel_character_pipeline.json`을 변경하지 않았다.
- `[최종 Editor 상태]` Edit Mode, 활성 `GameMap1`, scene dirty=false, playing/changing/compiling/updating=false다.
- `[미검증]` 실제 물리 마우스 hover·E 입력과 화면 해상도별 시각 위치·가독성은 이번 호출 검증에 포함하지 않았다. 기존 거래·저장 기능의 직접 조작 검증 미완료 항목은 26절에 남겨 둔다.

---

## 28. 현재 구현·검증 기준표와 반복 방지 계약

- `[사용자 요구][2026-08-26]` 이미 구현·검증된 기능을 AI가 다시 할 일로 반복 제안하거나 같은 검증을 여러 번 수행하지 않도록 현재 상태를 명확히 정리한다.
- `[문서 적용]` 당시 이 문서 맨 위 0절을 현재 구현 여부의 단일 요약 인덱스로 만들었다. 29절 후속 정리에서 이 인덱스는 짧은 독립 파일 `docs/ai/CURRENT_STATE.md`로 이동했다.
- `[지침 적용]` `AGENTS.md`는 모든 새 기능·버그 수정 전 현재 상태 인덱스를 확인하고, 관련 변경이나 새 회귀 증거 없이 완료 기능을 재제안·재구현·반복 검증하는 행동을 금지한다.
- `[검증 기준]` 현재 변경과 관련된 같은 대표 사용자 흐름 1회를 기본값으로 삼는다. 동일 조건의 2회 이상 반복은 씬 수명주기 변경, 간헐 오류 측정, 사용자 명시 요청처럼 반복 이유가 있을 때만 사전에 이유와 횟수를 기록한다. 서로 다른 seed·저장 migration/실패 분기·grid·해상도·플랫폼은 필요한 최소 case matrix를 먼저 정하고 각 case를 1회 확인한다.
- `[기록 해석]` 아래 상세 이력의 과거 `당시 미구현`, `후속`, `미검증`은 최신 상태표보다 우선하지 않는다. 사용자가 정상 작동을 확인한 기능은 관련 코드 변경이나 새 회귀 보고가 없는 한 미검증 상태로 되돌리지 않는다.
- `[범위]` 이번 작업은 문서와 AI 작업 계약만 변경했다. Unity 코드·씬·프리팹·에셋은 변경하지 않았으며 완료 기능의 Play Mode 재검증도 수행하지 않았다.

---

## 29. AI 지침 경량화와 조건부 문서 라우팅

- `[사용자 요구][2026-08-26]` 다른 게임 개발 프로젝트의 지침 구조와 비교해 더 효율적이고 안정적인 방식으로 만들되, 긴 지침을 읽다가 오히려 판단이 깨지는 문제를 방지한다.
- `[실제 원인 확인]` 기존 루트 `AGENTS.md`는 55,253바이트·470줄로 Codex 프로젝트 지침 기본 합산 한도 32KiB를 초과했다. 이번 세션의 자동 주입도 약 249행에서 실제로 잘려, 뒤쪽의 버그 근본 원인·재검증 제한·Git·Unity MCP·Computer Use 규칙이 로드되지 않았다.
- `[외부 비교]` OpenAI 공식 AGENTS 문서와 lean prompt 권고, Space Station 14·OpenRA·osu!·Godot의 공식 기여 문서를 비교했다. 공통적으로 짧은 루트 안내, 세부 규칙 분리, 한 변경 한 목적, 위험 비례 검증과 자동 검사 사용이 확인됐다.
- `[구조 변경]` 루트 `AGENTS.md`는 항상 필요한 핵심 계약과 작업별 문서 라우터만 남겼다. 현재 상태는 `docs/ai/CURRENT_STATE.md`, Unity 구조·도구·검증 절차는 `docs/ai/UNITY_ENGINEERING_PLAYBOOK.md`, 구조의 근거와 유지 규칙은 `docs/ai/README.md`로 분리했다.
- `[자동 검사]` `docs/ai/validate_ai_docs.ps1`이 루트 24KiB·상태표 12KiB 상한, 필수 라우팅 파일, 모든 기능·공백 ID의 중복·행 형식·계약 경로와 AI 문서 공백 오류를 검사한다.
- `[현재 상태 이동]` 이 문서의 이전 0절 상태표는 `CURRENT_STATE.md`로 이동했다. 이 문서는 현재 상태의 두 번째 복사본을 유지하지 않고 상세 증거·과거 이력만 보존한다.
- `[읽기 경로]` 앞으로 기본 흐름은 `AGENTS → CURRENT_STATE → 관련 계약 → 관련 playbook → 필요할 때만 진행 이력`이다. GDD·장르 계약·Stage 문서도 전체가 아니라 관련 절만 읽는다.
- `[보존]` 사용자 최신 정정, 동일 Player 인스턴스, 단일 권위 소유자, 원인 우선 수정, 완료 기능 재구현 금지, Computer Use opt-in, 위험 비례 검증과 검증 완료 로컬 커밋은 짧은 루트 계약에 남겼다.
- `[범위]` Unity 코드·씬·프리팹·에셋·ProjectSettings와 현재 게임 동작은 변경하지 않았고, 완료 기능의 Play Mode 검증을 반복하지 않았다.

---

## 30. Play Session 한정 그레이박스 시험 의뢰

### 사용자 요구와 이번 범위

- `[사용자 요구][2026-08-26]` 아트·애니메이션 없이 기본 판 UI와 큐브만 사용해, 새 NPC에게서 `적 1명 처치 후 살아서 귀환` 의뢰를 받고 실제 기존 원정 흐름으로 완료할 수 있는 작은 플레이 조각을 만든다.
- `[이번 범위]` `GameMap1`의 보라색 시험 NPC, 수락·진행·보고 UI, Player 처치 귀속, 생환 정산 커밋 뒤 보고 가능 상태까지 구현했다.
- `[제외]` 정식 퀘스트 목록·연계·반복·보상, NPC 대화 프레임워크, ordinary save와 Recovery의 퀘스트 DTO는 이번에 만들지 않았다. 따라서 진행도는 같은 Play Session의 persistent shell에서만 유지된다.

### 권위 소유권과 호출 흐름

| 확인 항목 | 현재 계약 |
|---|---|
| 정의 원본 | immutable `QuestDefinition` 에셋이 ID·표시 이름·설명·필요 처치 수·생환 필요 여부를 소유한다. |
| 런타임 원본 | persistent shell의 `QuestJournal` 하나가 Play Session 수명의 `QuestProgressState`를 소유하고 변경한다. NPC·적·UI는 진행도를 따로 쓰지 않는다. |
| 수락·보고 진입점 | 기존 `PlayerInteractor → QuestGiverInteractable → QuestPanelController → QuestJournal` 경로를 사용한다. 열린 패널의 대상 유지와 거리 이탈 닫기는 기존 공용 상호작용 계약을 따른다. |
| 처치 진입점 | 기존 `EnemyStats.Died` 완료 통지를 `QuestKillCreditReporter`가 관찰한다. 마지막 `DamageContext.Source`가 persistent Player 또는 그 자식일 때, 활성 원정·활성 의뢰에만 1회를 기록한다. |
| 생환 판정 | `RaidCheckpointController`가 ordinary save 미러와 Recovery 정리를 끝낸 뒤 발행하는 `SettlementCommitted`를 관찰한다. `Extracted`이고 목표를 채운 경우만 `ReadyToTurnIn`이 된다. |
| 실패 규칙 | 사망·포기·복구 실패 또는 목표 미달 생환은 의뢰를 취소하지 않고 해당 원정의 처치 수만 0으로 되돌린다. NPC 보고 뒤에만 `Completed`가 된다. |
| 파생 표현 | 중앙 의뢰 패널과 우상단 추적기는 `QuestJournal`에서 다시 만드는 UI다. 전환·정산 중에는 추적기를 숨기고, UI observer 오류가 전투 사망·이동·이미 커밋된 정산을 실패로 바꾸지 못하게 완료 통지를 격리한다. |
| 저장 경계 | 이번 진행도는 디스크에 저장하지 않는다. 실행을 종료하거나 셸이 파괴되면 초기화되며, 원정 Recovery만으로 퀘스트를 추측 복원하지 않는다. |

### 구현·검증 결과

- `[코드/에셋 확인]` `Assets/GameData/Quests/PrototypeHuntQuest.asset`과 보라색 graybox material을 만들고, `PersistentGameplayShell` prefab에 `QuestJournal`, 공용 Quest Canvas·패널·추적기를 직렬화 참조로 연결했다.
- `[씬/프리팹 확인]` `GameMap1`에 Collider와 `QuestGiverInteractable`을 가진 `Test_QuestNPC_Base` 큐브 1개를 배치했다. 두 시험 적 prefab은 각각 기존 `EnemyStats`와 같은 오브젝트에 처치 보고 컴포넌트 1개만 가진다. 세 대상과 shell의 Missing Script는 0으로 검증했다.
- `[동적 규칙 확인]` 같은 `QuestDefinition`으로 실패 분기 1회와 성공 분기 1회를 실행했다. 처치만으로 완료되지 않음, 실패 시 `Active + 0`, 생환 커밋 뒤 `ReadyToTurnIn`, NPC 보고 뒤 `Completed`, 완료 뒤 중복 보고 거부를 확인했다.
- `[Unity 컴파일/저장 확인]` Unity 6000.5.9f1의 script compilation과 domain reload가 성공했고, setup의 저장 후 shell·두 적 prefab·기지 scene 직렬화 참조 재검증이 통과했다. 기존 외부 `RenderTextureBaker` obsolete warning 외에 이번 코드의 compile error는 없었다.
- `[보호 확인]` Editor setup은 전역 `AssetDatabase.SaveAssets()`를 사용하지 않고 새 Quest definition·material과 대상 prefab·scene만 명시 저장한다. 적용 과정에서 재직렬화된 무관한 `TestMerchantGraybox.mat`은 작업 전 blob으로 복원해 변경 범위에서 제외했다.
- `[미검증]` 물리 E 입력으로 수락 → 실제 사격으로 적 처치 → 귀환 포탈 → NPC E 보고까지 이어지는 한 번의 Play Mode 사용자 흐름과 화면 해상도별 UI 가독성은 아직 직접 조작 검증하지 않았다. 현재 검증 등급은 `CODE`이며, 이 흐름을 사용자가 확인하면 `USER`로 올린다.

---

## 31. Persistent 정보창과 Play Session 기록

### 사용자 요구와 이번 범위

- `[사용자 요구][2026-08-26]` 별도 정보창을 만들고 스탯, 다양한 기록, 사전, 퀘스트와 업그레이드 같은 정보를 한곳에서 확인한다.
- `[현재 시험]` 충돌이 없는 `U` 하나를 토글 입력으로 사용하며 최종 키 바인딩은 미정이다. 캐릭터·기록·사전·의뢰·업그레이드 다섯 탭을 그레이박스 UI로 제공한다.
- `[제외]` 정식 능력치 추가, 영구 통계 save schema, 도감 발견·해금, 적의 정식 ID/표시명, 업그레이드 구매·효과·저장은 만들지 않았다. 원본이 없는 탭은 준비 중임을 사실대로 표시한다.

### 권위 소유권과 입력 경계

| 확인 항목 | 현재 계약 |
|---|---|
| 기존 상태 원본 | HP는 `PlayerStats`, 위치·원정 상태는 `RaidSession`, 아이템·장비·화폐는 기존 Player state, 활성 무기는 `PlayerWeaponController`, 의뢰는 `QuestJournal`에서 읽는다. 정보창은 쓰지 않는다. |
| 실행 기록 원본 | persistent shell의 `PlayerSessionRecords` 하나가 Player 귀속 적 처치와 committed 원정 결과, 완료 보고된 의뢰 횟수를 합산한다. |
| 처치 진입점 | 기존 `QuestKillCreditReporter`의 Player damage-source 판정 한 곳이 확인된 처치를 기록과 의뢰에 분배한다. 별도 사망 observer로 중복 귀속하지 않는다. |
| 정산 진입점 | `RaidCheckpointController.SettlementCommitted` 뒤에만 생환·사망·포기·복구 실패 기록을 올린다. `RaidSession.Resolved` 중간 상태를 합산하지 않는다. |
| UI 입력 | `InformationWindowController` 하나만 U를 읽는다. 열기 전에 의뢰창과 인벤토리를 안전하게 닫고 기존 이동·인벤토리·상호작용 잠금을 snapshot한다. |
| 중첩 방지 | Escape 메뉴, 맵 선택, 씬 전환과 정산은 자체 잠금을 저장하기 전에 정보창을 먼저 닫는다. Escape는 맵 선택 뒤, 의뢰·인벤토리 앞에서 정보창만 닫는다. |
| 시간·피해 | Base/Raid 모두 gameplay 입력은 막지만 Time.timeScale과 DamageBlocked는 변경하지 않는다. Raid에서는 세계와 피해가 계속 진행한다. |
| 저장 경계 | 기록과 선택 탭은 Play Session 전용이다. ordinary save·Recovery·정산 payload 버전은 변경하지 않았다. |

### 구현·검증 상태

- `[코드 확인]` 캐릭터 탭은 실제 HP·이동 속도·금/은·고유 grid item 수·장착 수·활성 무기 시험 수치를 표시한다. 기록 탭은 이번 실행 한정임을 명시한다.
- `[코드 확인]` 사전은 현재 ItemDatabase와 명시적으로 등록한 두 EnemyDefinition만 표시하고 발견 상태를 가장하지 않는다. 업그레이드 탭은 정의·비용·효과·저장 규칙이 미정임을 표시한다.
- `[코드 확인]` U controller를 기존 Player 입력보다 앞에서 실행해 연 프레임의 gameplay 입력 누수를 줄이고, Escape 단일 소유와 기존 overlay의 close-before-snapshot 순서를 유지했다. Base의 개발용 F5/Save 패널은 정보창 동안만 숨긴다.
- `[Unity 컴파일/프리팹 확인]` Unity 6000.5.9f1에서 script refresh와 domain reload가 성공했다. Editor API setup으로 shell prefab에 기록 소유자, root controller와 sorting 20000의 초기 비활성 Canvas를 연결했으며, 저장 후 재로드해 component 활성 상태·정확한 참조·EventSystem 1개·핵심 layout·Missing Script 0을 검증했다. 기존 외부 `RenderTextureBaker` obsolete warning 외에 신규 compile error는 없었다.
- `[보호 확인]` setup은 `PersistentGameplayShell.prefab` 하나만 명시 저장했고 scene, InputActions, ProjectSettings와 save schema는 수정하지 않았다. Computer Use는 사용하지 않았다.
- `[미검증]` 물리 U 입력, 다섯 탭 클릭, Escape 1회 닫기와 Base/Raid의 실제 화면 가독성은 아직 직접 조작하지 않았다. 현재 검증 등급은 `CODE`이며 동일 대표 흐름을 반복 실행하지 않는다.

---

## 32. 원정 맵 도착 안전 gate와 한 판 호출 지도

### 사용자 요구와 범위

- `[사용자 요구][2026-08-27]` 이미 확인된 다음 선행 공백이 있으면 구현하고, AI가 Unity 생명주기와 함수 순서를 다시 추측하지 않도록 게임 실행부터 한 판 정산까지 씬·호출·분기를 가장 짧고 구체적으로 기록한다.
- `[이번 범위][MAP-ARRIVAL-01]` `GameMapTest`의 생성 layout과 Entry→Portal NavMesh가 `Ready`일 때만 Player 배치, Raid Active, checkpoint와 화면 공개를 허용한다. `Invalid`이면 기존 검은 전환과 입력 잠금을 유지한 채 `GameMap1`로 돌아간다.
- `[보존]` 같은 persistent Player 인스턴스, 최초 로딩과 gameplay 직접 이동의 분리, 기존 seed/hash Recovery, terminal outcome 정산, 기존 fade와 입력 잠금 소유자를 그대로 사용했다.
- `[제외]` seed 자동 재굴림, POI·적·상자 spawn, LootTable, 퀘스트 저장, 새 UI·씬·프리팹·save schema는 변경하지 않았다.

### 권위와 구현

- `[권위 확인]` generator의 layout/Nav가 map 원본, `DirectSceneTravel`이 pending 이동·검은 전환, `RaidSession`이 원정 상태, `RaidCheckpointController`가 Recovery 거래의 기존 단일 소유자다. 새 Manager나 평행 상태를 만들지 않았다.
- `[호출 순서 원본]` Unity 실행 순서와 Ready/Fresh Invalid/Resume Invalid/Base 정산의 현재 호출은 `docs/ai/GAME_FLOW.md` §4~7 한 곳에서만 유지한다.

- `[근본 수정]` fresh rollback을 별도 일회성 cleanup 함수로 끝내지 않고 `BasePersistenceReady + BaseArrivalComplete → TryCommitTrackedRaidAtBase` 경로로 수렴시켰다. mirror나 cleanup이 실패해도 tracked 상태·exact 거래·F5 재시도 진입점과 입력 잠금이 남는다.
- `[근본 수정]` Fresh exact rollback을 durable하게 확보하지 못하거나 Base redirect의 `LoadSceneAsync`가 동기적으로 시작되지 못하면 성공을 반환하거나 공통 실패 reveal을 호출하지 않는다. 현재 pending token과 검은 cover·입력 잠금을 보류해 잘못된 Raid를 공개하지 않고, 재시작의 ordinary 원정 표식 우선 판정으로 넘긴다. Resume은 새 실패 기록 쓰기가 실패해도 기존 ordinary 표식·고정 Recovery seed가 fail-closed 권위를 유지하며, 기지 정산에서 다시 commit한다.
- `[실패 UI]` Base 로드는 시작됐지만 Spawn/context 도착이 실패한 Fresh rollback은 `Resolved/Outcome=None`을 유지한다. 기존 결과 UI의 default 분기를 열어 gameplay 실패로 바꾸지 않고 기지 재시도와 주 메뉴 이동을 제공한다.
- `[직접 시작 경계]` pending 이동 없이 `GameMapTest`를 직접 실행해 Invalid가 나오면 자동 기지 이동 대신 기존 travel lock으로 Player gameplay 입력과 피해를 막고 오류를 남긴다.
- `[문서 단일 원본]` `docs/ai/GAME_FLOW.md`에 `InitialLoadingScene → MainMenuScene`의 새 게임·로드·설정·나가기·중단 원정 분기, `GameLoadingScene → GameMap1`, 원정 출발·도착·결과·기지 정산·주 메뉴 종료의 실제 메서드 순서를 기록했다. 루트 `AGENTS.md`와 문서 validator가 이 파일을 조건부 필수 경로로 관리한다.

### 검증과 남은 확인

- `[컴파일 확인]` Unity 6000.5.9f1이 생성한 최신 `Assembly-CSharp.rsp/rsp2`를 같은 Unity Roslyn compiler로 실행해 exit code 0을 확인했다. 외부 `RenderTextureBaker` obsolete warning 1개만 있었고 이번 변경의 compile error는 없었다.
- `[정적 경로 확인]` Ready 성공, Fresh Invalid exact rollback, Resume Invalid fail-closed, Base redirect 동기 시작 실패와 base cleanup 재시도 분기가 각각 원본 owner를 유지하는지 코드 diff로 추적했다. `git diff --check`를 통과했다.
- `[문서 확인]` `validate_ai_docs.ps1`로 지침 크기, 상태 ID·계약 경로, 필수 `GAME_FLOW.md`와 공백 오류를 검사해 통과했다.
- `[Play Mode 미검증]` 현재 세션에는 호출 가능한 Unity MCP가 없고 Computer Use는 사용자 지침에 따라 사용하지 않았다. 변경 뒤 대표 `GameMap1 → Ready GameMapTest → GameMap1` 1회와 강제 Invalid 1회는 실제 Play Mode로 실행하지 않았으므로 `MAP-ARRIVAL-01`의 현재 검증 등급은 `CODE`다. 기존 정상 맵·왕복의 과거 `PLAY` 증거를 Invalid 분기 검증으로 과장하지 않는다.

---

## 33. Seed·stable ID 기반 시험 적·상자 배치

### 사용자 요구와 범위 `[SPAWN-01]`

- `[사용자 요구][2026-08-27]` 현재 완료 기능을 다시 제안하지 말고, 다음으로 실제 구현 가능한 기능이 있으면 이어서 구현한다.
- `[이번 범위]` `GAP-SPAWN`의 최소 선행 단계로 `GameMapTest`에 이미 있는 Chest 1개와 근접·원거리 Enemy 각 1개의 **같은 scene 인스턴스**를 seed에 따라 안전한 도로 후보로 재배치한다.
- `[보존]` 기존 stable ID 배열, Chest/EnemyStats/AI/시체 inventory, Recovery DTO, Persistent Player 셸, fade와 도착 gate를 그대로 사용한다. 새 Manager·프리팹·scene 오브젝트·save schema·runtime `Instantiate`를 추가하지 않는다.
- `[제외]` 가변 적·상자 수, prefab/definition spawn catalog, LootTable·위험/보상 예산, POI·건물 내부·장식과 최종 난이도 수치는 후속이다.

### 권위·수명과 호출 경계

| 확인 항목 | 현재 계약 |
|---|---|
| 권위 소유자 | `ProceduralUrbanMapGenerator`가 seed/layout/Nav를, 기존 `Chest`와 `EnemyStats`가 각 mutable 상태를 계속 소유한다. |
| 파생 배치 | `RaidCheckpointSceneBinding`이 scene 수명의 immutable `UrbanRaidSpawnManifest`를 seed·layout·stable ID에서 재구축한다. manifest는 상태 원본이나 별도 저장소가 아니다. |
| 생성·파괴 | authored 3개를 scene이 만들고 파괴한다. manifest는 새 개체를 생성하지 않고 초기 Transform만 한 번 배정한다. |
| 변경 진입점 | Generator의 geometry 완료 통지 하나가 Binding handler로 들어가고, 모든 ID·후보를 사전검증한 뒤 Transform을 일괄 적용한다. |
| 업데이트 | 프레임 Tick이 없으며 layout 생성 event와 도착 readiness 검사에서만 동작한다. |
| 저장 경계 | Chest grid, Enemy Transform·체력·시체 grid는 기존 DTO가 운반한다. manifest는 저장하지 않고 같은 seed로 재구축하며 layout과 함께 world hash에 포함한다. |

실행 순서는 `Binding.Awake(-10500) 구독/Resume seed 적용 → Generator.Awake(-10000) layout geometry → 동기 manifest 생성·기존 3개 배치 → EnemyStats/AI Awake → Generator.Start NavMesh → SceneSpawnController.Start 최종 Ready`다. Enemy가 먼저 초기화됐으면 중간 재굴림으로 덮지 않고 Invalid로 닫는다.

### 배치·복구 불변조건

- Stable ID ordinal 정렬과 자체 고정 해시만 사용한다. `UnityEngine.Random`, `string.GetHashCode`, instance ID나 검색 순서에 의존하지 않는다.
- Chest는 Entry 10m·Portal 8m·다른 개체 5m 이상을 지키며 도로 중심에서 옆으로 1m 배치한다. 상호작용 접근점은 막히지 않은 도로 중심이다.
- Enemy는 각 definition의 `시야 + 순찰 반경 + 2m` 이상 Entry에서 떨어지고 Portal 10m·다른 개체 6m 이상을 지킨다. 이 값은 현재 기술 안전 하한이지 최종 밸런스 확정이 아니다.
- Entry→Portal뿐 아니라 manifest의 Chest 접근점과 두 Enemy 위치까지 각각 `PathComplete`여야 한다. 후보 부족·NavMesh 실패는 seed를 조용히 재굴림하지 않고 기존 Invalid 도착 경계로 보낸다.
- Fresh와 Resume 모두 동일 authored 3개만 사용하므로 중복 생성이 없다. Resume은 manifest 초기 위치 뒤에 저장된 Enemy 현재 Transform·체력·시체 grid를 적용하고 Chest는 결정적 위치에서 저장 grid를 적용한다.
- 이전 코드의 layout-only hash Recovery는 명시적 legacy hash 분기로 한 번 복원한 뒤 첫 live checkpoint에서 새 combined world hash로 마이그레이션한다. 기술적 hash 변경을 `RecoveryFailed` 휴대품 소실로 처리하지 않는다.
- Standalone Chest와 Enemy corpse Chest를 두 역할로 중복 등록하거나 같은 Transform을 복수 stable ID에 연결하면 구성 오류로 거부한다. Chest의 authored Y·scale/구성 의미를 바꾸면 spawn version 또는 scene state identity도 함께 올린다.

### 검증과 남은 확인

- `[컴파일 확인]` Unity 6000.5.9f1의 실제 `Assembly-CSharp.rsp`와 Unity Roslyn compiler로 runtime assembly가 성공했고 기존 `RenderTextureBaker` obsolete warning 1개만 남았다. 누락된 과거 editor source 한 줄을 생성 response에서 일시 제외한 동일 Unity compiler로 Editor assembly도 exit code 0을 확인했으며 generated response는 즉시 원복했다.
- `[순수 로직 확인]` 실제 컴파일된 `Assembly-CSharp.dll`을 참조한 독립 harness로 seed 0~255를 각 2회 생성했다. 256개 모두 manifest가 결정적이었고 Entry·Portal 보호와 상호 최소 간격을 통과했으며 combined world hash도 256개 모두 달랐다.
- `[정적 경로 확인]` Fresh/Resume 수명주기, legacy hash 비손실 migration, binding 개수·ID 일치, Chest/시체 inventory 교차 중복 거부와 no-`Instantiate` 경로를 diff로 추적했다.
- `[Play Mode 미검증]` 변경 뒤 실제 `GameMapTest`에서 3개 배치, 개별 NavMesh 이동·상자 E 상호작용, 적 전투, 강제종료 Resume의 위치·체력·inventory 복원은 아직 조작하지 않았다. 현재 검증 등급은 `CODE`이며 기존 정상 왕복 `PLAY`를 새 배치 증거로 과장하지 않는다.

---

## 34. Entry 근처 시험 fixture와 결정적 LootTable

### 사용자 정정과 범위

- `[사용자 요구][2026-08-27]` 원정 진입 직후 시험하기 쉽도록 근접 적·상자·귀환 포탈을 각각 가까이 두되, 시스템이 종류별 오브젝트를 정확히 하나로 강제하는 구조로 만들지 않는다. 기존 원거리 적도 삭제하지 않는다.
- `[사용자 요구][2026-08-27]` Inspector에서 아이템 ID와 확률을 설정할 수 있게 하고, 더 나은 모딩 친화 구조가 있으면 적용 근거를 설명한다.
- `[이번 범위]` 현재 필수 시험 Chest는 Entry 3.5~8m, 피해 1 근접 적은 7~16m, ReturnPortal은 첫 인접 도로 교차점에 배치한다. 기존 원거리 적은 일반 안전 후보와 Recovery binding에 유지한다.
- `[제외]` 동적 프리팹 spawn, 가변 개수·위험/보상 예산, 다중 roll·수량·희귀도·지역 조건, 정식 모드 로더와 ID migration은 만들지 않았다.

### 정의·런타임·복구 경계

| 확인 항목 | 현재 계약 |
|---|---|
| 정의 원본 | 공유 `LootTableDefinition` 에셋이 ItemDatabase definition ID와 누적 확률을 소유한다. Chest는 해당 정의를 선택적으로 참조한다. |
| Inspector | `LootTableEntryDrawer`가 ItemDatabase를 읽어 `[ID] 표시명` 팝업과 확률을 보여준다. 저장값은 ID·확률뿐이며 누락 ID는 자동 교체하지 않고 `Missing ID`로 드러낸다. |
| 런타임 원본 | 실제 아이템과 grid는 기존 `Chest.chestInventoryData`가 소유한다. LootTable·UI·Recovery DTO는 live grid의 두 번째 원본이 아니다. |
| Fresh 진입점 | `RaidCheckpointSceneBinding.TryInitializeFreshLoot`가 Ready 뒤 첫 checkpoint 전에 table-backed Chest·시체의 후보 grid를 모두 만들고 검증한 뒤 원자 적용한다. 같은 seed에서 재호출해도 재굴림하지 않는다. |
| Resume | LootTable 호출 없이 Recovery에 저장된 실제 Chest·시체 grid를 복원한다. LootTable 미지정 컨테이너는 기존 authored 초기값을 유지한다. |
| 난수 | `loot algorithm version + map seed + stable container ID`의 로컬 결정적 난수만 사용하며 `UnityEngine.Random` 전역 상태와 열기 순서에 의존하지 않는다. 현재 표는 최대 한 아이템을 고르고 합계가 100% 미만이면 나머지는 무드롭이다. |
| 확장 | setup은 required stable ID와 적 보호 앵커를 기존 목록에 upsert할 뿐 배열을 축소하거나 미지의 binding·비-적 보호 앵커를 삭제하지 않는다. 배치·체크포인트 코드도 전체 binding 목록을 처리하므로 현재 1 Chest·2 Enemy는 fixture 수량이지 시스템 제한이 아니다. |

현재 숫자 ItemDefinition ID는 기존 저장·데이터 계약 때문에 유지한다. Steam Workshop 수준의 외부 모딩에서는 모드 간 숫자 충돌을 피할 namespaced string key와 migration이 더 적합하지만, 모드 로더·충돌 정책이 확정되기 전에 ID 의미를 조용히 바꾸지 않는다.

### 검증과 문서 정리

- `[Editor/순수 로직 확인]` Unity setup이 256개 seed에서 도로·건물·필수 근거리 배치와 보존된 원거리 배치의 결정성·간격·접근 가능성을 통과했다. LootTable도 같은 seed 반복 일치, 50/50 두 결과 관찰, 0/100 경계와 4×4 실제 grid 생성을 확인했다.
- `[Play Mode 확인]` `GameMapTest 직접 시작 → GameMap1 → GameMapTest → GameMap1` 대표 왕복 1회를 실행했다. 필수 근접 적·상자·포탈과 보존된 원거리 적, table-backed Chest·근접 시체의 각 1개 실제 아이템, manifest 3개, persistent shell 동일성, 런타임 오류 0을 확인했다.
- `[검증 도구 근본 수정]` Unity 창이 비활성일 때 Editor Play 시간이 진행되지 않아 대기하던 원인은 validator가 해당 Play Session에서만 `Application.runInBackground=true`를 사용하도록 고쳤다. ProjectSettings는 변경하지 않았다.
- `[문서 감사]` 새 Markdown을 만들지 않았다. 현재 상태는 `CURRENT_STATE`, 실제 호출 순서는 `GAME_FLOW`, 기획은 GDD·장르 계약, 상세 증거는 이 진행 파일에만 기록했다. 대형 역사 문서는 압축 뒤 기본 재로딩 대상이 아니며 필요한 절만 라우팅한다.

---

## 35. 정상 생환 자동 귀환과 정산 UI

- `[사용자 요구][2026-08-27]` 생환 뒤 Raid 화면에 기지/주 메뉴 선택을 남기지 않고, 생환 확정과 자연스러운 화면 전환을 분리한다. 최종 탈출 연출은 미정이므로 현재는 즉시 생환·피해 차단을 사용한다.
- `[근본 수정]` `ReturnPortal → Resolve(Extracted) → terminal checkpoint observer → 자동 TryReturnToBase` 순서로 고정했다. 기존 0.2초 fade가 완전히 덮인 뒤 정산 화면을 불투명하게 표시하므로 Raid가 갑자기 UI로 잘리는 장면을 피한다.
- `[정산 gate]` 기지 로드 뒤 ordinary save mirror와 Recovery 삭제가 성공해 `SettlementCommitted`가 발생하기 전에는 버튼을 숨긴다. 성공 뒤 `확인`만 표시하며 주 메뉴 경로는 차단한다. 정산 실패는 Recovery를 유지하고 `정산 재시도`만 제공한다.
- `[Play Mode 호출 확인]` 격리된 임시 save/Recovery 경로에서 `PlayerInteractor.TryInteract()` 1회로 생환을 실행했다. E 직후 `Extracted`, 피해·이동·인벤토리·상호작용 차단과 두 결과 버튼 비활성을 확인했다.
- `[Play Mode 호출 확인]` 같은 shell·Player·Inventory entity ID를 유지한 채 `GameMap1`에 자동 도착했고, primary/backup의 원정 표식 해제, Recovery 파일 0개, 주 메뉴 비활성, `확인` 활성 상태를 확인했다. 실제 버튼 callback 뒤 기지 입력이 복원됐으며 Console Error/Exception/Assert는 0건이었다.
- `[미정]` 탈출 대기 시간, 피격 시 중단, 암전 중 사망 허용 여부와 최종 연출은 이번 구현으로 확정하지 않았다.

---

## 36. 고정 기지 NPC 충돌 안정화 `[INTERACT-01]`

- `[사용자 요구][2026-08-27]` 상인·의뢰 NPC와 부딪힐 때 물리 엔진이 버벅이지 않고 상자처럼 벽으로 안정 정지하게 한다. 겹치기 방식은 이번 선택에서 사용하지 않는다.
- `[근본 원인]` Player는 `Update`에서 Transform을 이동하고 `PlayerMovement.IsColliding`은 `Obstacle` 태그만 이동 전에 차단한다. Chest는 solid Collider·`Obstacle`·Rigidbody 없음이었지만 두 고정 NPC만 solid Collider·`Untagged`·Rigidbody 없음이라, 이동 코드의 관통과 물리 solver의 밀어내기가 프레임 경계에서 경쟁했다.
- `[최소 수정]` `GameMap1`의 상인·의뢰 NPC를 `Obstacle`로 맞추고 solid Collider·Rigidbody 없음·기존 layer 0을 유지했다. `PlayerMovement`, Chest layer와 상호작용 소유자는 변경하지 않았다.
- `[재발 방지]` `MerchantPrototypeSetup`과 `QuestPrototypeSetup`이 태그와 solid Collider를 설정하고, `Obstacle + non-trigger Collider + Rigidbody 없음`을 검증하도록 고쳤다. 생성 도구를 다시 실행해도 원래 결함으로 돌아가지 않는다.
- `[Play Mode 호출 확인]` 한 Play Session에서 두 NPC 각각에 대해 PlayerMovement와 동일한 `OverlapBox + Obstacle` 쿼리가 차단을 반환했고, `PlayerInteractor.TryInteract()`로 최근접 대상 열기·닫기를 확인했다. 실제 WASD 키를 계속 누르는 수동 접촉 검증은 실행하지 않았으므로 키 입력을 확인했다고 기록하지 않는다.
- `[Editor 확인]` Quest authoring validator와 상인 고정 장애물 검사를 통과했고 GameMap1은 저장 뒤 clean이었다. Console 신규 Error는 0건이며 기존 Input Manager deprecation·Codex 서명 경고 2건만 남았다.

---

## 37. Player 공용 행동시간과 Chest 열기 연동 `[ACTION-01]`

- `[사용자 요구][2026-08-27]` 장전·회복·먹기·상자 열기가 공유할 행동시간 경계를 만들고, 외부 아트가 필요한 원형 UI와 아직 없는 실제 장전·회복·먹기 기능은 제외한다.
- `[권위 소유자]` 같은 런타임 인스턴스로 유지되는 Player의 `PlayerActionController` 하나가 동시 행동 하나, 소스·ID·경과·남은 시간·진행률을 소유한다. 호출자는 `TryBegin`의 완료·취소 콜백으로 연결하며 UI는 후속에 읽기 전용 진행률만 관찰할 수 있다. 행동 차단 상태는 현재 `PersistentGameplayShell`의 전환 경계만 쓴다.
- `[원자 경계]` 행동 상태를 먼저 정리한 뒤 완료 콜백을 호출하므로 효과는 완료 시점에만 기존 기능 API로 적용되고 콜백 재진입도 새 행동으로 명확히 구분된다. 다른 행동이 진행 중이면 새 요청은 원본을 건드리지 않고 거부한다.
- `[Chest 연동]` 닫힌 Chest는 시험값 1초 뒤 기존 `InventoryUIManager.TryToggleChestInventory`로 연다. 대기 중에는 같은 Chest를 활성 대상으로 유지하고 이동은 허용하되 거리 이탈·상호작용 차단·대상 비활성화·Player 사망 시 취소한다. 열린 Chest 닫기는 기존처럼 즉시 처리한다.
- `[Play Mode 호출 확인]` 한 Play Session에서 0.75초 시험 행동의 즉시 UI 미개방, 중복 E 무재시작, 병렬 행동 거부, 완료 뒤 열림과 즉시 닫힘을 확인했다. 이어 5초 행동에서 거리 이탈 취소와 상호작용 차단 취소를 각각 확인했으며 UI는 열리지 않고 controller는 유휴 상태로 돌아왔다.
- `[전환 경계 확인]` 30초 행동 중 `PrepareForTravel`을 호출하자 완료 효과 없이 `SceneTravel` 사유로 취소됐다. 차단 상태를 먼저 확정하므로 취소 콜백의 재시작과 전환 중 외부 시작 요청이 모두 거부됐고, 전환 취소·fade 복원 뒤에는 새 행동이 다시 허용됐다.
- `[Play Mode 확인]` 기존 도시맵 검증기로 `GameMapTest` 직접 시작과 `GameMapTest → GameMap1 → GameMapTest → GameMap1` 1회 왕복을 통과했다. Shell·Player·Camera·Inventory·EventSystem 동일성, Spawn, NavMesh와 런타임 Error 0건을 확인했다.
- `[검증 도구 근본 수정]` 도시맵 검증기의 `Application.runInBackground=true`가 `ProjectSettings`를 1로 남기던 원인을 확인했다. 시작 전 값을 저장하고 성공·실패의 Play Mode 종료 전과 Edit Mode 마무리에서 복원하도록 바꿨으며, 최종 왕복 뒤 `ProjectSettings/ProjectSettings.asset`이 clean임을 확인했다.
- `[프리팹/Console 확인]` `PersistentGameplayShell/Player`에 `PlayerInteractor`, `PlayerActionController`, `PlayerStats`가 각각 하나이고 같은 GameObject에 있으며 missing script는 0개다. 신규 Error/Exception/Assert는 0건이다. 컴포넌트 자동 보완 시 authoring 경고가 한 번 발생했지만 저장 뒤 재검사에서는 재발하지 않았다.
- `[미검증·미정]` 실제 키보드 E 입력과 원형 UI는 이번 검증에서 확인하지 않았다. 장전·회복·먹기의 시간·자원 소비·이동·피격·사격에 따른 중단 정책은 구현하거나 확정하지 않았다.

---

## 38. 행동 입력 취소 계약과 시험 resource stack `[ACTION-01][ITEM-01][ITEM-UI-01]`

- `[사용자 요구][2026-08-27]` 진행 중 행동은 WASD 같은 이동 의도, 공격과 장비 선택 입력으로 취소하고 U 정보창·I 인벤토리는 유지한다. 행동시간 자체도 같은 공용 경계에서 하나만 진행한다. 치료제·탄약·음식은 1×1 시험 아이템과 `현재/최대` 수량 표시를 만들되 실제 소비 규칙은 후속으로 둔다.
- `[입력 경계]` 기존 `PlayerMovement`, `PlayerWeaponAttackController`, `PlayerWeaponController`가 각자 유효 입력을 판정한 뒤 같은 Player의 `PlayerActionController.CancelActive`를 호출한다. 공용 controller는 동시 행동과 취소 사유만 소유하고 이동·발사·장비 효과를 대신 실행하지 않는다. 현재 실제 장비 슬롯은 W1~W3뿐이므로 W4를 임의 추가하지 않았다.
- `[U·I 보존]` 정보창은 새 상호작용 입력만 막되 이미 시작한 행동과 대상은 유지하는 기존 `PlayerInteractor` 경로를 사용한다. I 경로는 행동 controller를 건드리지 않는다. 거리 이탈·대상 비활성·Player 사망·일반 전환 차단·씬 전환의 안전 취소는 유지했다.
- `[수량 권위]` 최대 stack은 공유 `ItemDefinition`, 현재 수량은 개별 `InventoryItemData`가 소유한다. grid UI는 읽기 전용 파생 표시이며 `InventoryItemSaveData`는 ordinary save, 기지·상인, 원정 Chest·시체와 Recovery에서 같은 값을 운반한다. 기존 수량 필드가 없는 record의 0은 1개로 정규화하고 현재 writer는 양수만 기록한다.
- `[시험 데이터]` definition ID 7 치료제(초록 원), 8 총알(노랑 원), 9 음식(파랑 원)을 각각 1×1·최대 10으로 ItemDatabase와 Player 시험 시작 목록에 추가했다. 세 아이콘은 투명 배경 64×64 임시 PNG다. 최초 stack은 각각 1개다.
- `[UI 경계]` `StandardCell`의 상인 가격 배지와 stack 수량 배지를 분리했다. 공용 `StandardCore`가 Player·외부 Chest/시체와 동적으로 여는 중첩 컨테이너 View까지 수량 공급자를 전달하므로 grid가 바뀌어도 같은 runtime 값을 읽는다.
- `[Editor/데이터 확인]` ID 7~9 유일성, 64×64 아이콘, 1×1·최대 10, 6/10 메모리 저장 왕복, legacy 0→1 정규화, 11/10 거부, 가격·수량 prefab 참조 분리와 Player 시작 ID를 확인했다.
- `[Play Mode 호출 확인]` 실제 persistent shell에서 세 시험 아이템 셀이 각각 `1/10`을 표시했다. 임시 상호작용 행동에 대해 U와 I 호출이 행동·현재 대상을 유지했고, W1 선택과 유효 공격 호출은 각각 `EquipmentSwitchInput`, `AttackInput` 사유로 취소했다. 임시 대상과 무기·UI 상태는 검증 뒤 복원했으며 종료 후 Console Error/Exception/Assert는 0건이었다.
- `[코드·컴파일 확인]` 0이 아닌 이동 축이 `MovementInput` 취소 뒤 기존 이동을 계속하는 경로를 확인했고 Unity 컴파일을 통과했다.
- `[실제 입력 미검증]` 실제 키보드 WASD·U·I·숫자키와 마우스 클릭 주입은 수행하지 않았다. 장전·회복·먹기 효과, stack 합치기·분할·소비, 무기 탄창·탄약 소비와 drag ghost의 수량 표시는 이번 범위에 포함하지 않았다.

---

## 39. 기지·원정 Loot 행동시간 정책 분리 `[ACTION-01][INTERACT-01]`

- `[사용자 요구][2026-08-27]` 상자라는 이유만으로 모두 행동시간을 사용하지 않는다. I 개인 인벤토리와 기지 창고는 즉시 열고, 현재는 야외 원정 파밍 Chest·시체에만 조사 시간을 적용한다.
- `[구조 결정]` 오브젝트 태그를 행동 권위로 쓰거나 런타임 `AddComponent`로 스크립트를 보완하지 않았다. 기존 `ChestInteractable`에 직렬화된 `Immediate`·`TimedSearch` 정책을 두고 안전한 기본값을 `Immediate`로 정했다. 서로 다른 용도는 prefab variant 또는 scene instance override로 authoring할 수 있다.
- `[현재 authoring]` 공유 근접·원거리 Enemy 프리팹은 기지 시험 개체에도 쓰이므로 `Immediate`를 유지했다. `GameMapTest`의 시험 원정 Chest와 두 Enemy 시체 인스턴스만 `TimedSearch(1초)` override를 가진다. 도시맵 구성 도구도 같은 세 대상을 설정·검증한다.
- `[보존]` `PlayerInteractor`의 최근접 선택·열린 대상 유지·거리 이탈 종료, `InventoryUIManager`의 같은 Chest UI 경계, 공용 `PlayerActionController`와 기존 이동·공격·장비 전환 취소 규칙을 그대로 재사용했다. 열린 대상의 닫기는 즉시다.
- `[Play Mode 호출 확인]` I 개인 인벤토리와 `GameMap1` 기지 Chest는 행동 없이 같은 호출에서 열고 닫혔다. `GameMapTest` 시험 Chest는 즉시 열리지 않고 1초 행동을 소유했으며, 기존 controller 완료 경로 호출 뒤 열리고 다시 즉시 닫혔다. MCP 명령 중 Editor 프레임이 진행되지 않아 실제 1초 경과는 반복 측정하지 않았고, 시간 경과 자체는 변경되지 않은 §37 증거를 재사용한다.
- `[컴파일·Console 확인]` 변경 뒤 Unity 동적 검증 코드와 프로젝트 참조가 컴파일됐고 최종 Console Error/Exception은 0건이었다. 실제 E·I 키 입력 주입과 최종 진행 UI는 확인하지 않았다.

---

## 40. Stack 분할과 클릭 보유 트랜잭션 `[ITEM-01][ITEM-UI-01]`

- `[사용자 요구][2026-08-27]` 수량 stack을 우클릭 `나누기`로 열어 기본값 1과 직접 입력 수량만큼 들고, Ctrl+좌클릭은 절반을 즉시 나눈 채 들도록 한다.
- `[수량·소유권 권위]` `InventoryItemData.TryChangeQuantity`가 예상 owner·기존 수량·최대 stack을 함께 검사한다. 분할 시작은 기존 원본 runtime item과 slot·owner를 유지한 채 수량만 줄이고, `InventoryItemDataFactory`가 만든 새 runtime item 하나만 기존 `StandardCore` drag 권위에 둔다.
- `[원자 경계]` `InventoryStackSplitTransaction`은 새 item이 실제 destination owner에 연결되고 원본 잔량·owner·slot이 그대로일 때만 확정한다. 취소·무효 배치·I/Escape/거리 이탈·씬/저장 정리는 기존 drag 취소 경계에서 분할 item을 버리고 원수량을 복원한다. 중첩 컨테이너 View는 rollback 뒤 다시 그려 stale 수량 배지를 남기지 않는다.
- `[입력·UI]` 우클릭은 context의 `나누기/닫기`, 다음 modal은 `1..현재-1`, 기본값 1, 확인/취소를 제공한다. Ctrl+좌클릭은 `floor(현재/2)`, Shift는 기존 빠른 이동, Ctrl+Shift는 무동작이다. 수량 입력 중 1~3 무기 전환과 I/R을 차단하고 drag ghost에도 수량 배지를 표시한다. 중간 마우스 버튼은 우클릭으로 취급하지 않는다.
- `[거래 경계]` 현재 상인 가격은 stack 단가·총액 정책이 확정되지 않았으므로 Merchant UI가 열린 동안 우클릭과 Ctrl 분할을 모두 데이터 무변경으로 차단한다. 동일 stack 자동 합치기와 수량별 거래 정산은 후속 결정이다.
- `[Editor/순수 로직 확인]` 실제 Medicine definition과 임시 grid에서 `5→4+1→취소 5`, 홀수 절반 `5→3+2`, destination owner 연결 뒤 commit, `Capture→JSON→Restore`의 `3+2`, 수량 1·전체 수량 거부와 Merchant 차단을 각각 확인했다. 원본 참조·slot·owner와 총량 5가 유지됐다.
- `[Play Mode 호출 확인]` 실제 persistent Player stack을 검증 중에만 5로 바꾸고 `StandardButton` 우클릭 callback → `나누기` → 기본값 1 → 확인을 호출했다. Manager가 참조한 Core에서 원본 4와 detached 1, 활성 drag를 확인하고 취소하자 같은 원본·slot·owner의 5로 복원됐다. 수량 1 우클릭은 UI를 열지 않았고 검증 뒤 시작 수량 1·닫힌 UI로 복원했다.
- `[프리팹·컴파일 확인]` `PersistentGameplayShell`에는 inactive `StackSplitOverlay`와 dialog 1개만 추가됐고 Manager 참조, 필수 UI 경로 9개, sorting 160, raycast 차단, 기존 GameObject 186개 보존과 missing script 0을 확인했다. 최종 Unity Console Error/Exception은 0건이다.
- `[실제 입력 미검증]` 실제 사용자의 Ctrl 키·마우스 클릭과 다른 grid 빈 칸으로의 클릭 배치는 호출/순수 로직으로 분리 확인했으며 물리 입력 자체를 통과했다고 기록하지 않는다. Enter 확정, 배경 클릭 닫기, 동일 stack 합치기와 자동 정렬은 이번 범위에 포함하지 않았다.

---

## 41. 짧은 클릭 보유·capability 메뉴·원자 stack 합치기 `[ITEM-01][ITEM-UI-01]`

- `[사용자 요구][2026-08-28]` 좌클릭을 짧게 눌렀다 떼면 item/stack 전체를 즉시 들고, 기존 hold-drag도 별도 입력으로 유지한다. 우클릭은 실제 가능한 `사용`·`나누기`만 표시하고, Alt+좌클릭과 Alt+drag는 같은 절반 분할을 사용한다. 같은 stack 합치기는 최대치까지만 채우고 나머지를 계속 들어야 한다.
- `[입력 경계]` 고정 0.2초 지연을 새로 만들지 않고 Unity EventSystem의 click과 drag 이동 임계값을 사용한다. 짧은 클릭과 pointer drag는 같은 `OnPick → 보유 → OnDroped` 소유권 경로를 공유하되 보유 방식만 `Click`·`Pointer`로 구분한다. drag 원점은 임계값 시점 hover가 아니라 `pointerPress`의 실제 누른 셀로 고정한다. R 회전, Shift 빠른 이동과 취소·UI 정리 경계는 유지했으며 최신 요구에 따라 빠른 절반 분할 키는 Ctrl에서 Alt로 바꿨다.
- `[우클릭 capability]` 공용 context가 `사용`·`나누기` callback 유무로 버튼을 구성한다. 현재 실제 사용 기능이 있는 컨테이너만 `사용`을 제공하고, 수량 2 이상 stack만 `나누기`를 제공한다. 사용 효과가 아직 없는 치료제·음식에 임의 효과를 만들지 않았다. 이미 열린 컨테이너에는 실패할 `사용`을 다시 노출하지 않는다.
- `[원자 합치기]` 기존 transfer coordinator가 같은 definition·같은 최대 stack·정상 target owner를 확인하고 대상 수량을 먼저 CAS 변경한 뒤 detached 보유 수량을 변경한다. 두 번째 변경 실패 시 대상 수량을 원복하고 보유 item도 원래 owner 없음·원수량인지 확인하는 receipt를 사용한다. 어느 쪽도 확인되지 않은 불확정 상태는 원본을 다시 넣지 않고 보유와 recovery receipt를 유지해 다음 취소·배치에서 재복구한다. `2/5 + 4/5 → 5/5 + 보유 1/5`를 지원하고, 정확히 다 채우면 별도 0수량 item을 만들지 않고 보유를 끝낸다.
- `[분할 재기준]` 분할 item 일부가 다른 stack에 합쳐지면 합쳐진 수량은 확정되고 transaction의 미처리 수량만 갱신한다. 이후 취소는 아직 들고 있는 나머지만 원본에 돌려 총량을 보존한다. 상인 화면은 분할과 Player↔상인 거래 경계 합치기를 차단하되 Player 내부·상인 내부 합치기는 기존 일반 이동 경계와 같이 허용한다.
- `[Editor/순수 로직 확인]` `2+4→5+1`, merge receipt rollback `5+1→2+4`, 분할 부분 합치기 뒤 취소의 `source 2 + target 5 = 총 7`, 정확한 전량 합치기를 확인했다. 최종 보완 뒤 `8/10+4/10→10/10+2/10`과 receipt 원복, 상인 같은 쪽 합치기 허용·거래 경계 차단도 다시 확인했다.
- `[Play Mode 호출 확인]` 실제 Player inventory에서 기존 pointer drag의 취소·동일 item/slot 복원, 짧은 클릭 전체 보유, R 회전, `8/10 + 4/10→10/10 + 보유 2/10`, 취소 뒤 총량 12와 원회전 복원을 확인했다. 별도 대표 사례에서 일반 stack은 `나누기`만, 컨테이너는 `사용`만 표시되고 `사용`이 기존 컨테이너 popup을 여는 것을 확인했다. 최종 보완 뒤 점유된 잘못된 칸 click-carry 유지·명시적 취소 복원, hover를 이웃 셀로 바꿔도 pointerPress 원본을 집는 것, 기존 pointer drag의 다른 빈 칸 성공 배치와 보유 종료, 분할 `5→3+2` 뒤 `8+2→10` exact fill의 Core 보유 종료를 확인했다. 검증용 runtime item과 열린 UI는 모두 정리했다.
- `[프리팹·컴파일 확인]` `PersistentGameplayShell`의 dialog·UseButton이 각각 1개이고 필수 참조가 완전하며 missing script 0개다. 최신 코드 컴파일 뒤 Console Error는 0건이었다.
- `[재사용 증거·미검증]` Save schema와 codec은 변경하지 않아 §38의 양수 stack 저장 왕복과 §40의 분할 `3+2` JSON 복원 증거를 재사용한다. 실제 사용자의 Alt·마우스·R 물리 입력은 주입하지 않았으므로 코드 분기와 Play Mode 호출 확인으로만 기록한다. 실제 치료제·음식 사용 효과, 상인 stack 가격 정산과 자동 정렬은 여전히 미정이다.

---

## 42. 용량 연동 인벤토리 frame과 Storage Shift stack 우선 이동 `[ITEM-01][ITEM-UI-01]`

- `[사용자 요구][2026-08-28]` grid 칸수와 따로 노는 배경·외곽 UI를 실제 용량에 맞추고, 인벤토리↔인벤토리 Shift 이동은 대상의 기존 비가득 stack을 먼저 채운 뒤 남은 수량만 빈칸으로 옮긴다. 빈칸이 없으면 합쳐지지 않은 나머지만 원본 칸에 남긴다.
- `[UI 권위]` `StandardStashView`가 capacity, cell size, spacing에서 Content 크기를 계산하고 선택된 외곽 root에 padding만 더한다. Player와 외부 Storage view만 이 root 크기 갱신을 사용하며, 별도 popup 크기 권위를 가진 `StandardCaseView`는 기존 경로를 유지한다. 내부 배경은 Content와 같은 좌표·크기를 사용한다.
- `[Storage 원자 이동]` `InventoryTransferCoordinator`가 같은 definition·최대 stack의 대상을 slot 순서로 계획하고 기존 owner API로 source를 한 번 분리한다. 대상 수량을 채운 뒤 남은 같은 runtime source를 첫 유효 빈 위치로 연결하거나, 빈 위치가 없으면 원래 owner·slot에 재연결한다. 전량 합치기는 0수량 item을 만들지 않는다. 중간 예외는 적용한 대상 stack을 역순 복원하고 원본 참조·수량·owner·slot을 복구하며, 복구가 끝나기 전 다른 인벤토리 mutation과 session 교체를 차단한다.
- `[범위 보존]` Player↔Chest·시체 같은 Storage 양방향 Shift에만 stack 우선 규칙을 적용했다. 비stack item은 기존 whole-item first-fit을 사용하고, Player↔상인 구매·판매는 stack 가격 정책이 미정이므로 기존 거래 경계를 그대로 유지한다. drag·분할·Save schema와 수량 배지는 변경하지 않았다.
- `[Editor 호출 확인]` 실제 Medicine definition과 임시 Storage grid로 전량 합치기, 여러 대상 stack의 slot 순서 채움 뒤 같은 source remainder 빈칸 이동, 역방향 부분 합치기 뒤 빈칸 부족 시 exact 원본 owner·slot 잔류, destination 부착 뒤 예외를 주입한 원자 rollback, 비stack Handgun의 기존 first-fit을 각각 1회 확인했다. 모든 case에서 총수량·runtime 참조와 grid 소유권이 기대값과 일치했다.
- `[Play Mode 호출 확인]` Player `8×9`에서 Content·내부 배경·72개 cell 경계가 `519×584`, 외곽 root·배경이 `530×595`로 일치했다. 같은 외부 view를 `5×6 → 6×5`로 바꾸자 활성 cell 30개를 재사용하면서 Content·내부 배경·cell 경계가 `389×324`, 외곽 root·배경이 `400×335`로 함께 갱신됐다. `StandardCaseView`의 별도 크기 경로도 유지됐다.
- `[컴파일·미검증]` 최종 프로젝트 코드와 검증 명령은 컴파일됐고 Play Mode 검증 뒤 Edit Mode·`GameMap1`로 정상 복귀했다. 후속 fault-injection은 의도한 복구 실패 오류 3건을 냈고, Edit Mode에서 같은 view를 재적용한 검증 명령은 기존 `Destroy` 경로의 Editor 진단을 남겼으나 모든 assertion과 마지막 PASS까지 실행됐다. 실제 사용자의 Shift+마우스 물리 입력은 주입하지 않았으며, 변경되지 않은 입력 분기 뒤 `HandleQuickTransfer`부터 실제 owner API 경로를 호출해 검증했다.

---

## 43. 우클릭 속성 기반 장착과 외부 클릭 닫기 `[ITEM-01][ITEM-UI-01]`

- `[사용자 요구][2026-08-28]` 무기·장비처럼 장착 속성이 있는 item은 우클릭 메뉴에 `장착`을 표시하고, 가벼운 context UI는 메뉴 밖 클릭으로 취소한다.
- `[속성·소유권 경계]` 새 tag나 분기표를 만들지 않고 기존 `ItemDefinition.EquipmentSlot`·`IsEquippable`을 capability 원본으로 사용한다. Player 또는 열린 Storage 소유 item만 현재 활성 primary 슬롯이 비었을 때 기존 원자 이전 API로 장착하며, 상인 stock과 이미 장착된 item은 직접 장착하지 않는다. 현재 무기는 기존 계약대로 W1만 자동 대상이다.
- `[UI 경계]` 공용 context는 `사용`·`장착`·`나누기` callback 유무로 버튼과 높이를 구성한다. 전체 화면 raycast overlay가 활성 panel 밖 좌·우 클릭을 받으면 callback 없이 닫고, panel 내부와 버튼 클릭은 유지한다.
- `[Play Mode 호출 확인]` 실제 `Handgun` definition과 persistent shell UI로 `장착`만 표시, 외부 좌클릭 취소 시 원 owner·빈 W1 유지, 다시 연 뒤 버튼 호출 시 같은 runtime item이 Player grid에서 W1로 이동하는 것을 한 번 확인했다. Merchant stock의 직접 장착도 차단됐다. 프로젝트와 검증 명령은 컴파일됐으며 실제 물리적 우클릭 입력은 주입하지 않았다.

---

## 44. Alt+클릭 장비 즉시장착·해제 `[ITEM-01][ITEM-UI-01]`

- `[사용자 요구][2026-08-28]` 미장착 장비를 Alt+좌클릭하면 비어 있는 호환 장비칸에 즉시 장착하고, 장비칸의 item을 Alt+좌클릭하면 Player 인벤토리로 즉시 해제한다. 점유 장비 교환은 하지 않는다.
- `[입력 순서]` `StandardCore`는 Alt 입력을 `AlternateItemActionRequested` 하나로 전달한다. `InventoryUIManager`가 `Click + IsEquippable`을 먼저 장착/해제로 처리하고 return하며, 그 외 click·pointer만 기존 비장비 stack 절반 분할로 보낸다. 우클릭·Shift·일반 click/drag는 기존 경로를 유지한다.
- `[소유권·UI]` `InventoryTransferCoordinator.TryToggleEquipment`가 장비 root owner면 Player root grid first-fit으로, 그 외 허용된 Player·Storage owner면 기존 빈 primary 장비칸으로 같은 runtime item을 원자 이전한다. 점유·공간 부족은 원 owner·slot으로 복구한다. 성공 뒤 source view도 재적용해 열린 중첩 가방 popup에 stale item을 남기지 않는다. 현재 무기 자동 대상은 W1뿐이다.
- `[Play Mode 호출 확인]` 같은 Handgun 객체의 Player slot 0→W1→Player first-fit 0 왕복, W1 점유 실패의 양쪽 원본 보존, 가득 찬 Player grid에서 해제 실패 후 같은 W1 복구를 각각 한 번 확인했다. 별도 Medicine `5→3+detached 2→rollback 5`로 비장비 stack 분할도 보존됐다. 프로젝트 컴파일은 통과했으며 실제 Alt 키 물리 입력은 주입하지 않았다.

---

## 45. Ctrl 1개 집기와 빈칸 연속 분배 `[ITEM-01][ITEM-UI-01]`

- `[사용자 요구][2026-08-28]` 중첩 item을 Ctrl+좌클릭하면 1개만 들고, 이미 짧은 클릭으로 든 여러 수량은 Ctrl+좌클릭 또는 Ctrl+drag로 빈칸마다 1개씩 놓은 뒤 나머지를 계속 든다. pointer drag로 든 item에는 이 분배를 적용하지 않는다.
- `[수량·소유권]` 기존 `InventoryStackSplitTransaction`과 transfer coordinator를 확장했다. 한 개 배치는 destination owner API로 새 수량 1 runtime item을 연결한 뒤 detached 원본 수량을 exact CAS로 1 줄이며, 어느 단계든 실패하면 receipt가 owner·slot·before/after 수량을 확인해 원복한다. 마지막 1개는 0수량 복사본 없이 들고 있던 같은 runtime item을 연결한다. 이미 놓은 낱개는 확정되고 취소 시 아직 든 나머지만 원본 stack으로 돌아간다.
- `[입력·grid 경계]` `StandardCore`는 click-carry+Ctrl 단독만 연속 분배로 해석하고 같은 drag 제스처에서 방문한 cell을 한 번만 처리한다. Unity가 pointer enter를 BeginDrag보다 먼저 보내는 순서에 맞춰 누른 cell과 임계값을 넘긴 현재 cell을 모두 처리하며 EndDrag의 기존 전량 drop은 소비한다. 점유칸·원래 picked footprint·grid 밖/겹침은 무동작이고 Ctrl 전용 판정색도 같은 빈칸 규칙을 사용한다. Merchant session은 stack 단가 정책이 미정이라 양방향 분배를 차단한다.
- `[Editor 호출/순수 로직 확인]` `5→4+detached 1→rollback 5`, `held 5→placed 1+held 4→receipt rollback 5`, split 3을 두 빈칸에 1개씩 놓은 뒤 취소하여 `placed 2+source 3`, 마지막 1개의 동일 runtime 연결·원복, 점유칸 무변경과 Merchant 양방향 차단을 확인했다. Core 호출로 누른 cell+현재 cell 동시 처리, 재방문 1회 제한, EndDrag 뒤 잔량 유지, 마지막 동일 runtime commit과 Ctrl 전용 거부 판정도 확인했다. 프로젝트 컴파일을 통과했다.
- `[보존·미검증]` 우클릭/Alt 분할·일반 click·pointer drag·R 회전·Storage Shift·stack 합치기·장비·저장 schema는 기존 경로를 유지했다. 실제 사용자의 Ctrl 키와 마우스 물리 입력은 주입하지 않았으므로 통과했다고 기록하지 않는다.

---

## 46. 메인 메뉴·게임 내 공용 키 설정 `[INPUT-01]`

- `[사용자 요구][2026-08-28]` 지금까지 실제로 쓰는 조작키를 정리하고, 메인 메뉴 Settings와 게임 내 Escape Settings에서 바로 확인·변경할 수 있게 했다.
- `[입력 권위]` 기존 project-wide `InputSystem_Actions`에 `Gameplay` map 16개 action·32개 기본/보조 binding을 추가했다. 이동·달리기·상호작용·공격·무기 1~3·인벤토리·정보창·아이템 회전과 Shift·Alt·Ctrl 보조 동작의 기존 기능 진입점만 공용 `GameInputBindings`로 교체했다. Escape 단일 소유자, UI pointer 입력과 개발용 F5는 고정 경계를 유지했다.
- `[저장·충돌]` mutable override 원본은 기존 `GameUserSettings`가 `PlayerPrefs` JSON으로 소유하며 게임 save와 Recovery schema는 바꾸지 않았다. 실제 ButtonControl을 canonical path로 저장·비교해 alias 중복, synthetic·비버튼 입력, Escape/F5를 거부한다. 일반 동시 중복은 원자 거부하고 `Run ↔ QuickTransferModifier`의 의도된 중복만 허용한다. 손상·구버전 값은 자동 덮어쓰지 않고 기본값으로 안전 복귀하며 변경·초기화 저장 실패 시 runtime과 저장 원본을 복원한다.
- `[공용 UI]` `KeyBindingSettingsPanel.prefab` 하나를 `MainMenuScene/Canvas/SettingsPanel`과 `PersistentGameplayShell/PauseCanvas/SettingsPanel`에 각각 배치했다. View는 상태를 소유하지 않고 16개 행·기본/보조 키·스크롤·기본값 복원만 제공한다. 재바인딩 중 Escape는 변경만 취소하고 같은 설정 화면을 유지한다.
- `[Editor/저장 확인]` catalog 16 action·32 binding, 공용 prefab과 두 진입점 참조, 각 위치 인스턴스 1개, missing script 0을 확인했다. 임시 override를 원상복구하는 검증에서 변경·재적용·일반/alias 중복·Escape/F5·비버튼 거부·의도 중복·초기화·손상 JSON 보존/기본값 fallback 21/21 case가 통과했고, 원래 PlayerPrefs 없음·Interact E 상태로 복원했다.
- `[Play Mode 호출 확인]` MainMenu Settings와 `GameMap1` Base Escape Settings가 각각 활성화되어 16개 runtime 행을 만들고 project-wide Gameplay map이 활성화된 것을 확인했다. Base는 기존대로 `Time.timeScale=0`, 메뉴 종료 뒤 1로 복원됐다. 실제 행 버튼에서 재바인딩을 시작한 뒤 취소하면 같은 frame Escape 소비와 원 binding 보존, Settings 화면 유지가 확인됐다.
- `[보존·미검증]` Raid non-pause 분기는 변경하지 않아 기존 §21 Play 증거를 재사용한다. 실제 사용자의 키보드·마우스 물리 입력, 게임패드, 그래픽·세부 오디오 설정과 최종 UI 아트는 이번 범위에 포함하지 않았다. 손상 JSON case는 의도된 경고 1건을 냈고 값을 복구한 뒤 새 컴파일·runtime Error/Exception은 확인되지 않았다.

---

## 47. 별도 사용자 설정 파일과 PlayerPrefs 이관 `[INPUT-01]`

- `[사용자 요구][2026-08-28]` Sound와 키 설정을 gameplay 저장 슬롯·원정 Recovery에 섞지 않고 게임 저장 데이터 영역의 별도 사용자 설정 파일에 보관하도록 변경했다.
- `[저장 권위]` 기존 `GameUserSettings`를 단일 진입점으로 유지하고 `Application.persistentDataPath/Settings/user_settings.json` v1에 Sound, 키 override 존재 여부·버전·payload를 저장한다. `GameSaveData`와 Recovery schema는 변경하지 않았다.
- `[내구성·복구]` UTF-8 JSON을 `.tmp`에 flush한 뒤 원자 교체하고 이전의 유효한 primary를 `.bak`으로 회전한다. 읽을 수 없는 primary·backup은 `.corrupt-*`로 보존하며, primary가 무효이고 backup이 유효하면 backup을 적용하고 primary 복구를 시도한다.
- `[마이그레이션·실패 원자성]` 유효 설정 파일이 없을 때만 기존 PlayerPrefs를 한 번 이관하고, 별도 파일 쓰기 성공 뒤 legacy key를 정리한다. override 존재 여부와 원본 버전을 함께 보존해 손상 legacy 값을 정상값으로 가장하지 않는다. Sound·키 저장 실패 시 runtime 값과 설정 UI 표시를 이전 확정값으로 복원한다.
- `[Editor 저장 검증]` 프로젝트 내부 격리 루트에서 완전한 PlayerPrefs 이관, Sound·키 저장 후 reload와 backup, 키 초기화 시 Sound 보존, 손상 primary 격리·backup 복구, 버전 key가 빠진 부분 legacy의 원본 보존·기본키 fallback, 쓰기 실패 시 Sound·키 rollback, 실제 Settings·ordinary save·Recovery 지문 불변의 7-case matrix가 최종 7/7을 반환했다. 검증 뒤 PlayerPrefs·InputAction override·map enabled·AudioListener와 임시 파일을 원상복구했다.
- `[검증 도구 반복 주의]` 쓰기 차단 case의 의도된 Error를 Unity MCP가 명령 실패로 분류해 같은 검증 함수를 67회 자동 재호출했다. 이는 수명·간헐성 검증을 위한 요청 반복이 아니며 추가 실행을 중단했다. 매 호출은 GUID 격리 root와 `finally` 원복을 사용했고, 종료 뒤 임시 폴더 부재와 실제 Settings·ordinary save·Recovery 지문 불변을 다시 확인했다.
- `[보존·미검증]` 기존 Main/ESC 설정 UI와 Base pause/Raid non-pause는 구현을 바꾸지 않아 §21·46 Play 증거를 재사용한다. 한 matrix의 손상·부분 legacy·쓰기 차단 case에는 의도된 Warning 2건과 Error 1건이 있으며, 정리 뒤 최종 프로젝트 컴파일이 통과했다. 실제 전원 차단 순간의 원자성, 물리 키 입력과 Player build는 이번 변경 뒤 실행하지 않았다.

---

## 48. 시험 총기 탄약·3발 탄창·2.5초 재장전 `[ACTION-01][ITEM-01][COMBAT-01][SAVE-01][ITEM-UI-01]`

- `[사용자 요구][2026-08-28]` Player 총과 탄약을 연결하고 시험값을 발사 간격 0.5초, 최대 장전 3발, 재장전 2~3초의 중간값 2.5초로 둔다.
- `[상태 권위]` 탄창은 총 종류가 아니라 각 `InventoryItemData` 인스턴스의 `LoadedAmmunition`이 소유한다. `ItemDefinition`은 탄약 definition ID·탄창 용량·재장전 시간만 정의하며, 현재 다섯 시험 총은 탄약 ID 8·용량 3·2.5초·120 RPM을 공유한다. 새 총과 v5 이전 저장의 총은 빈 탄창으로 시작한다.
- `[재장전 원자 경계]` 기존 `PlayerActionController`에 `weapon.reload` 행동을 시작하고 완료 시에만 Player 소유 root·중첩 컨테이너의 같은 탄약 stack을 slot 순서로 소비해 탄창을 채운다. stack 감소·제거와 탄창 증가는 한 동기 transaction이며 중간 실패는 역순 원복한다. 이동·공격 의도·W1~W3·사망·씬 전환·공격 컴포넌트 비활성화는 취소하고 U·I는 유지한다.
- `[입력·발사·표시]` R은 gameplay에서 재장전, 인벤토리에서 item을 들고 있으면 기존 회전으로 문맥 공유한다. 발사는 장전탄 1개를 먼저 소비한 성공 건만 효과음·Raycast·자극·피해로 이어지고 빈 탄창은 발사하지 않는다. 하단 무기 HUD는 `현재탄/용량`, tooltip은 용량·재장전 시간을 표시한다.
- `[저장]` `GameSaveData` v6가 runtime 총의 장전탄을 운반하며 Player 인벤토리·장비·기지·상인·원정 Chest·시체가 공용 codec을 쓴다. v5→v6는 명시적으로 빈 탄창으로 이관하고, 음수·용량 초과·비무기 장전탄 record는 거부한다. 진행 중 재장전 행동은 저장하지 않고 완료된 탄창 상태만 저장한다.
- `[Editor/순수 로직 확인]` 탄약 `5→탄창3+stack2`, 세 발 소비와 네 번째 차단, 탄약 2발의 부분 장전과 빈 stack 제거, 장전탄 3·2의 save 왕복, 초과값 거부, v5 빈 탄창 이관, 0.49초 차단·0.5초 다음 발사를 한 matrix에서 확인했다.
- `[Play Mode 호출 확인]` 실제 `GameMap1` persistent Player의 W1 Handgun과 시작 탄약 5개로 재장전을 호출했다. 시작 직후 `weapon.reload`가 활성이고 탄창0·탄약5였으며, 2.5초 완료 뒤 행동 유휴·탄창3/3·탄약2를 확인하고 Play Mode를 종료했다.
- `[보존·미검증]` 기존 마우스 XZ Raycast·단발/자동 분기·장비·인벤토리 회전·ordinary/Recovery 저장을 유지했다. 실제 물리 R 키, 최종 탄종·무기군별 장전·AI 탄약·재장전 애니메이션·반동·탄퍼짐은 이번 범위에서 검증·확정하지 않았다.

---

## 49. 행동 source 남은 초·우측 하단 탄창 HUD와 중단 원정 오류 진단 `[ACTION-01][ITEM-UI-01][RAID-01][SAVE-01]`

- `[오류 진단][2026-08-28]` Console의 `ordinary save already declares an unresolved raid`는 저장 손상이 아니라 새 원정이 기존 중단 원정을 덮지 못하게 하는 보호 오류다. ordinary primary·backup은 동일한 v6 원정 ID를 표시하고 같은 ID의 baseline과 유효한 Active checkpoint primary·backup이 존재했다. `GameMap1` 직접 Play는 표식 생성 원인이 아니라 MainMenu의 이어하기/실패 결정을 우회한 계기다.
- `[복구 경계]` 저장·Recovery를 수정하거나 지우지 않았다. `InitialLoadingScene` 또는 `MainMenuScene`에서 이어하기를 선택하면 checkpoint를 복원하고, 버릴 때만 원정 실패 처리를 거쳐 기지 정산·cleanup을 완료해야 한다.
- `[행동 UI]` `PlayerActionController`가 현재 source의 읽기 전용 Transform을 제공하고, 영속 `HUDCanvas`의 단일 `PlayerActionWorldCountdownView`가 기존 `RemainingSeconds`를 `0.0초`로 표시한다. Chest source는 Chest Transform, 재장전 source는 Player Transform이므로 호출부·Chest prefab·시간 원본을 추가하지 않았다. 완료·취소·화면 밖에서는 숨긴다.
- `[탄창 UI]` 기존 하단 중앙 1~3 슬롯을 유지하고 우측 하단에 선택 중인 총의 현재 장전탄/용량을 큰 `탄창 n / n`으로 추가했다. 기존 `Equipment.Changed → PlayerWeaponController.WeaponStateChanged` 통지만 관찰하므로 발사·재장전 상태를 복제하지 않는다. 무기가 없으면 숨긴다.
- `[입력 보존]` 새 Image·Text의 raycast를 모두 끄므로 마우스가 HUD 위에 있어도 기존 공격의 UI pointer 차단 판정을 새로 유발하지 않는다.
- `[Prefab/Play Mode 호출 확인]` prefab에서 Countdown/Ammo View·필수 참조·우측 하단 anchor·missing script 0을 확인했다. 한 Play Session에서 Chest source `5.0초`가 Chest 투영 위치에 표시되고 취소 즉시 숨는 것, 재장전 `2.5초`가 Player 투영 위치에 표시되는 것, 완료 경계에서 `0/3→3/3` 및 1발 소비 뒤 `2/3` 갱신을 확인했다. Unity가 비활성 창에서 frame을 진행하지 않아 2.5초 자연 경과는 이번에 반복하지 않고 §48의 실제 완료 증거를 재사용했다.
- `[후속 미정]` 원형 진행 아트와 예비 탄약 총량 표시는 후속이다. 현재 우측 하단은 선택 무기의 탄창만 표시하며 실제 물리 E·R·발사 키는 이번 변경에서 주입하지 않았다.

---

## 50. 치료제 우클릭 사용·2.5초 회복 `[ACTION-01][ITEM-01][ITEM-UI-01]`

- `[사용자 요구][2026-08-28]` 기존 치료제를 인벤토리 우클릭 `사용`에 연결하고 약 2.5초 행동시간 뒤 회복하도록 했다.
- `[데이터·권위]` ID 7 `Medicine` definition에 사용시간 2.5초와 시험 회복량 35를 두었다. 체력 원본은 기존 `PlayerStats`, 수량·소유권 원본은 기존 `PlayerInventoryState`이며 별도 체력·소비 캐시는 만들지 않았다. tooltip도 두 값을 definition에서 읽는다.
- `[사용·원자 경계]` 체력이 부족하고 item이 Player root 또는 Player 소유 중첩 컨테이너에 있을 때만 우클릭 `사용`을 노출한다. 완료 직전에 같은 PlayerState·runtime item·owner·slot·수량을 다시 확인하고 1개를 owner API로 소비한 뒤 회복한다. 수량 1은 slot에서 제거하며 `0/최대` stack을 만들지 않는다. 외부 Chest·상인 stock은 거부한다.
- `[행동·표시]` 기존 `PlayerActionController`의 `item.medicine` 행동을 사용하므로 이동·공격·W1~W3·사망·씬 전환에서 효과 없이 취소되고 U·I는 유지된다. source는 영속 Player여서 기존 남은 초 View가 Player 위치를 따르며 완료·취소 때 숨는다. 진행 중 item 이동·수량 변경·만피 도달도 소비 없이 취소한다.
- `[Prefab/정적 확인]` `PersistentGameplayShell/Player`에 controller 1개, missing script 0, definition 2.5초·35, tooltip, 수량 `2→1`과 마지막 `1→slot 제거`, 중첩 Player 소유 허용과 외부 grid 거부를 확인했다. 저장 DTO는 기존 definition ID·양수 quantity와 Player health를 그대로 사용하므로 schema v6를 바꾸지 않았다.
- `[Play Mode 호출 확인]` 실제 `GameMap1` Player를 HP 50·시작 치료제 5로 두고 사용을 시작했다. 시작 시 `item.medicine`, 남은 `2.5초`, Player anchor와 체력·수량 불변을 확인했고 자연 경과 뒤 HP 85·수량 4·행동 유휴·시간 UI 숨김을 확인했다. 같은 실행에서 다시 시작한 뒤 `MovementInput` 취소 시 HP 85·수량 4가 유지되고, 최대 체력에서는 시작 거부·무소비임을 확인했다.
- `[보존·미검증]` ordinary/Recovery schema와 기존 인벤토리·재장전·Chest 사용 경로는 변경하지 않았다. 실제 물리적 우클릭·WASD 입력과 최종 회복량 밸런스, 음식 사용·애니메이션·효과음·원형 진행 아트는 이번 범위에서 검증·확정하지 않았다. Console에는 §49에서 이미 진단한 미해결 원정 보호 오류가 남아 있으며 치료제 경로 오류는 확인되지 않았다.

---

## 51. Self·External 행동 범위와 이동 중 재장전·치료 `[ACTION-01][COMBAT-01]`

- `[사용자 정정][2026-08-28]` 자기 자신에게 쓰는 치료·음식·재장전은 이동 중 유지하고, 다른 상대 오브젝트를 조사하는 상자·시체 열기만 이동에서 취소한다. 시간 UI도 Self는 Player, External은 상대 대상에 둔다. 이 결정이 §37·38·48·50 당시의 보편 이동 취소 기록을 대체한다.
- `[공용 경계]` `PlayerActionController`가 `PlayerActionScope.External/Self`를 active action 상태로 하나만 소유한다. 모든 `TryBegin` 호출자가 범위를 필수 지정하므로 아이템 kind·태그·이름·action ID·Transform 위치를 추론하지 않는다. source는 기존 행동 소유·수명 식별을 유지하고, scope는 이동 취소와 표시 anchor만 결정한다.
- `[호출부]` 재장전과 치료제는 `Self`, `ChestInteractable`의 원정 Chest·시체 `TimedSearch`는 `External`을 명시한다. 기지 Immediate Chest는 행동시간을 시작하지 않는다. 향후 음식도 `Self` 계약을 사용한다.
- `[취소]` `MovementInput`은 External만 취소하고 Self에서는 행동을 유지한다. 공격·W1~W3·Requested·사망·씬 전환·source 소실·continuation 실패·컴포넌트 비활성화는 양쪽 모두 기존 취소 경로를 유지한다. 외부 조사의 거리 이탈·대상 비활성화와 열린 UI 자동 닫기도 바꾸지 않았다.
- `[코드/Play Mode 호출 확인]` 모든 `TryBegin` overload가 scope를 필수 인수로 요구하고 세 runtime 호출부가 명시된 것을 컴파일로 확인했다. 한 `GameMap1` Play Session에서 Self는 이동 취소 요청 뒤 계속 진행·Player anchor·시간 UI 표시를 유지했고 AttackInput에서 효과 없이 종료됐다. External은 실제 `ChestInteractable` source anchor를 사용하고 이동 요청 즉시 종료·시간 UI 숨김이 됐다. 잘못된 scope 값도 시작을 거부했다.
- `[보존·미검증]` 실제 물리 WASD·R·우클릭 입력은 주입하지 않아 호출 확인으로 기록한다. 재장전·치료 완료 효과는 §48·50, Chest/시체 거리·UI 흐름은 §39·49의 기존 증거를 재사용한다. save/Recovery schema와 prefab·scene은 변경하지 않았고 Console에는 §49의 기존 미해결 원정 보호 오류만 남았다.

---

## 52. 시험 의뢰·누적 기록 ordinary/Recovery 영속화 `[SAVE-01][QUEST-01][INFO-01]`

- `[사용자 요청][2026-08-29]` 반복해서 “세이브 연동 필요”로 제안되던 항목을 실제 구현과 대조했다. 인벤토리·장비·화폐·기지 가구·상인 상태는 이미 저장됐지만, 시험 의뢰와 누적 기록은 v6 payload에 없던 실제 공백이었다.
- `[권위·schema]` 기존 `QuestJournal`과 `PlayerSessionRecords`를 유일한 runtime 쓰기 권위로 유지하고 `GameSaveData`를 v7로 올렸다. 새 `PlayerProgressSaveData`는 stable quest ID·상태·처치 수와 적 처치·생환·사망·포기·복구 실패·완료 의뢰 누계를 운반할 뿐 원본이 아니다. v2~v6는 명시적으로 v7로 이관하며 과거 저장의 비어 있는 시험 의뢰 roster만 authored 초기화를 허용한다.
- `[원정 원자 경계]` `RaidPersistentSettlementPolicy`가 아이템 손실과 player-progress 결과를 한 번에 순수 계산한다. terminal checkpoint에서 준비된 exact 상태를 settlement journal→ordinary save→live owner에 그대로 재사용해 결과를 중복 가산하지 않는다. fresh-departure rollback은 baseline을 그대로 쓰고, marker-only 복구 실패는 baseline에서 한 번만 실패 결과를 만든다.
- `[완료 통지]` 정산 중 상태 전이는 저장된 exact 상태로 적용하고, 실제 NPC 보고 완료만 `QuestCompleted` 의미 이벤트를 낸다. 따라서 load·Recovery가 완료 의뢰 누계를 다시 올리지 않는다. 정보창 표시는 “이번 실행 기록”에서 “누적 기록”으로 맞췄다.
- `[Unity 컴파일/순수 로직 확인]` Unity project compilation이 성공했다. 한 Editor matrix에서 v6→v7 migration, v7 JSON 왕복, 생환/복구 실패 투영, 원본 불변, 아이템+진행도 복합 정산과 잘못된 payload 거부를 확인했다.
- `[Play Mode 호출 확인]` 실제 `GameMap1` persistent owner에 완료 의뢰와 여섯 누계 값을 exact replacement하고 값 일치·의뢰 완료 의미 이벤트 0회를 확인한 뒤 원래 runtime snapshot으로 복원했다.
- `[보존·미검증]` 기존 인벤토리·장비·화폐·기지·상인·원정 marker/Resume/정산 흐름과 단일 시험 의뢰 규칙은 유지했다. 다중·반복 의뢰, 보상, 새 UI와 최종 저장 슬롯 정책은 이번 범위가 아니다. Console에는 §49에서 이미 진단한 미해결 원정 보호 오류만 남았으며 이번 변경의 신규 오류는 확인되지 않았다.

---

## 53. 핵심 시스템 마감과 인접 검증 계약 `[BOOT-01][INPUT-01][ACTION-01][ITEM-01][COMBAT-01][SAVE-01][ITEM-UI-01]`

- `[사용자 정정][2026-08-29]` 단일 기능을 바꿀 때마다 전체 한 바퀴를 반복하지 않는다. 변경된 권위·입력·수명·직렬화 경계와 직접 맞물린 기능만 한 번 검증하고, 전체 한 바퀴는 실제 다단계 흐름 변경이나 릴리스 gate로 미룬다.
- `[저장 UX]` ordinary primary/backup이 있으면 새 게임 진입 전에 기존 ExitPanel을 재사용한 확인을 요구한다. Base의 주 메뉴 요청은 등록된 `BasePersistenceController.SaveSlotOne` 성공 뒤에만 기존 `GameplaySessionExit`를 시작하며 실패하면 사유를 표시하고 기지에 남는다. unresolved Raid·포기·정산 분기는 선행 분기 그대로 유지한다.
- `[장비·탄약 표시]` `EquipmentLoadoutData`가 호환되는 첫 빈 칸을 반환해 무기는 W1→W2→W3 순서로 자동 장착된다. 예약 프리팹 셀 W2·W3을 활성화하고 14칸을 기존 2열 frame 안에 맞췄다. 우측 하단은 선택 총의 탄창과 같은 탄약 ID의 Player 소유 예비탄 총량을 함께 표시하며 runtime 총 tooltip도 현재 장전탄을 읽는다.
- `[키 설정]` 공용 행 prefab에 `해제`·`복원` 버튼을 추가했다. 빈 문자열 override를 “보조키 없음”으로 보존하며, 보조키 해제와 해당 행만 기본값 복원은 기존 중복 검증·즉시 파일 저장·실패 rollback 경계를 공유한다.
- `[구조 계약]` 5번은 gameplay 로그나 결과 cache가 아니다. `PlayerActionController.ActionResolved`가 완료/취소 snapshot을 한 번 통지하고 `PlayerStats.DamageApplied`가 확정된 `DamageResult`를 한 번 통지한다. lethal 상태는 관찰자보다 먼저 확정하고 통지 중 체력 재진입을 막는다. 결과 관찰자는 구독자별로 예외를 격리해 한 모드·SFX·애니메이션 observer가 뒤 observer나 확정된 gameplay 결과를 막지 못한다. 기존 controller·owner callback·체력은 계속 유일한 쓰기 권위다.
- `[부분 이동·표시 성능]` 최종 drop 전에 확정되는 한 개 배치·부분 stack 병합과 취소 복구는 owner 변경 경계에서 가벼운 read-only contents 통지만 보낸다. 최종 drop·취소는 core carry를 먼저 닫고 observer 예외를 구독자별로 격리하므로 상인 정산 재진입을 남기지 않는다. 전체 UI 재생성이나 HUD polling을 추가하지 않았다. 예비탄 조회는 쓰기용 reload mutation plan을 만들지 않고 재사용 visited set으로 Player 소유 grid를 읽기 전용 순회한다.
- `[Unity 컴파일/인접 검증]` 프로젝트 compilation과 두 prefab 직렬화 참조를 확인했다. `CoreSystemsAdjacentValidation` 1회에서 W1~W3 첫 빈 칸/4번째 거부, definition 기반 예비탄·runtime 탄창, 즉시 완료·취소 결과, 실제 legacy 설정을 건드리지 않는 보조키 해제·행 복원, primary/backup 존재 판정과 prefab wiring을 임시 상태 원복과 함께 통과했다. 후속 리뷰로 바뀐 lethal 체력 경계만 별도 1회 확인해 `HealthChanged`·`DamageApplied` 재진입이 사망 확정과 `Died` 1회 통지를 바꾸지 못하고 통지 종료 뒤 명시적 reset은 동작함을 확인했다. 검증 메뉴는 Play Mode에서 실행할 수 없다.
- `[보존·미검증]` 실제 사용자 save/settings와 기존 dirty scene·material·preview prefab은 수정하지 않았다. 물리 클릭·키 입력, Base 저장 실패 UI의 Play Mode 조작, 전체 게임 한 바퀴와 Player build는 이번 범위에서 실행하지 않았다.

---

## 54. 영속 직교 카메라 제한 줌 `[CAMERA-01][SHELL-01][INPUT-01]`

- `[사용자 요청][2026-08-29]` 림월드처럼 최소·최대 제한이 있는 카메라 줌을 추가하고, 최종 2D 픽셀아트 방향에서 미리 주의할 경계를 확인한다.
- `[소유권·입력]` `PersistentGameplayShell`의 기존 동일 `Main Camera` 인스턴스를 유지했다. 같은 오브젝트의 `CameraFollow`는 위치, 새 `CameraZoomController`는 `orthographicSize`만 소유한다. 버튼 전용 리바인딩 catalog를 왜곡하지 않고 기존 `Gameplay` map에 고정 `CameraZoom` Vector2 `<Mouse>/scroll` action을 두어 `GameInputBindings`로만 읽는다.
- `[동작]` 현재 시험값은 시작 size 5, 범위 3.5~8, 정규화 scroll delta 1당 0.5단계, 보간 0.08초다. 작은 고해상도 휠·터치패드 delta는 누적하고 한 frame의 여러 tick은 단계 수만큼 반영한다. 일반 인벤토리·ESC/settings·정보/의뢰 같은 gameplay 차단 UI와 scene travel 중에는 기존 owner 상태를 읽어 입력과 미완료 누적값을 차단한다. 저장 schema와 scene별 Camera를 추가하지 않았다.
- `[Unity 컴파일·Play Mode 호출 확인]` 프로젝트 compile, prefab의 직교 Camera·Follow·Zoom 각 1개와 shell camera 참조, missing script 0, action type/path를 확인했다. Play Mode 호출에서 0.4는 대기, 추가 0.6은 한 단계, -2는 두 단계로 처리되고 3.5/8에서 clamp됨을 확인했다. 실제 사용자의 물리 휠과 Player build는 미검증이다.
- `[검증 도구 주의]` Edit Mode에서 비실행 `MonoBehaviour` lifecycle을 `SendMessage`로 호출한 첫 검증, 비활성 Game View의 frame 진행 시도와 한 runtime field 조회 실수는 Unity MCP 검증 방식 문제로 assertion·실패 로그를 남겼다. 최종 compile·prefab·Play 호출 결과와 구분했으며 기존 미해결 원정 보호 오류를 포함한 Console 기록을 지워서 덮지 않았다.
- `[2D 픽셀아트 경계·미구현]` 현재 게임 규칙은 XZ·3D Physics·NavMesh이므로 완전 XY/Physics2D 전환은 이동·사격·AI·맵 생성 재작성이다. 기존 규칙을 보존하려면 우선 3D gameplay+2D sprite 표현을 검토한다. 정식 전환 전 PPU·기준 해상도·Point/무압축 import·pivot·sorting·건물 가림을 확정하고 Pixel Perfect Camera를 붙인 뒤에는 연속 보간 대신 `zoomSmoothTime=0`과 허용 배율 단계 정책을 정한다.

---

## 55. 야외 아침·낮·밤 하늘광과 태양 그림자 `[ENVIRONMENT-01][SHELL-01][MAP-01]`

- `[사용자 요청][2026-08-29]` 강수·구름·실내 조명 없이, 야외의 아침·낮·밤과 태양 그림자만 먼저 구현했다.
- `[권위·데이터]` 영속 `PersistentGameplayShell`의 `SkyLightingCycleController` 하나가 gameplay session 시간을 소유한다. 색·환경광·태양 세기·그림자 강도는 `ClearSkyLightingProfile`의 시간순 keyframe에서 보간하므로, 날씨 종류를 하드코딩한 평행 Manager를 만들지 않았다. 현재 시험 주기는 실제 60초당 게임 24시간이고 조명은 게임 1분 단위로 갱신된다.
- `[씬·렌더링 경계]` gameplay bootstrap이 있는 활성 씬에서 기존 Directional Light를 정확히 하나만 찾아 `RenderSettings.sun`으로 지정하고, 씬 전환 뒤 같은 시간 값을 다시 적용한다. 하늘광은 URP의 `Trilight` sky/equator/ground 색을 사용한다. 아침·낮에는 태양 회전·색·세기와 Hard Shadow를 적용하고 밤에는 직접 태양광과 그림자를 끈다. Main Menu와 기존 비활성 3D 픽셀 후처리는 건드리지 않는다.
- `[그림자 근본 수정]` 절차 도심 primitive의 그림자 생성과 수신을 분리했다. 건물은 생성·수신하고 Ground·Road·Boundary는 생성하지 않되 수신하므로 건물 그림자가 바닥에서 사라지던 기존 결합을 제거했다.
- `[Unity 컴파일·Play Mode 호출 확인]` Unity 6000.5.9f1 프로젝트 compilation과 profile/prefab 직렬화 참조를 확인했다. 한 `GameMap1` Play Session에서 아침 7.5시(태양 0.789, 그림자 0.748), 낮 12시(태양 1.064, 그림자 0.844), 밤 22시(태양 0, 그림자 없음)를 각각 한 번 강제하고, phase·Trilight 색·Directional Light 회전·Hard/None 전환과 동일 runtime controller 사용을 확인했다.
- `[보존·미검증]` Player·Camera·씬 흐름·저장 schema와 기존 사용자 dirty scene/material/preview prefab은 수정하지 않았다. 최종 색·주기 밸런스, 실제 skybox 시각, 실내 Roof/SkyVisibility 감쇠, 비·눈·안개·구름, 시간 UI와 ordinary/Recovery 시간 저장은 이번 범위가 아니다. 물리 입력이 없는 Play Mode 호출 확인이며 Player build와 gameplay 씬 왕복 중 재바인딩은 별도 실행하지 않았다.

---

## 56. 지평선 그림자 제한과 황혼·달빛 보정 `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 피드백][2026-08-29]` 일몰 직전 그림자가 과도하게 길어지고, 해가 지평선을 넘는 순간 화면의 주광이 끊기는 현상을 수정했다.
- `[확정 원인]` 기존 태양 각도는 실제 고도 0도까지 내려가 17.9시 고도 1.5도에서 높이당 그림자 길이가 약 38.2배까지 발산했다. 18.0시에는 Directional Light를 즉시 꺼 직접광이 0이 되고, 어두운 기존 Trilight만 남아 화면이 끊겨 보였다.
- `[근본 수정]` 실제 천체 시간은 유지하되 그림자를 만드는 방향광 고도는 최소 12도로 제한해 보이는 그림자를 높이의 약 4.7배 이내로 묶었다. 실제 태양 고도 20→8도에서 그림자를 SmoothStep으로 먼저 감쇠하고 8도 이하는 끈다. 지평선 ±5도에서는 그림자 없는 같은 Directional Light를 태양 방향에서 달 방향으로 보간하며, 황혼 Trilight와 달빛 최소 세기를 겹쳐 정확한 일몰·일출 순간에도 광량이 0이 되지 않게 했다. Shadow Distance나 bias로 잘라 가리지 않았고 새 Light·Manager를 추가하지 않았다.
- `[Unity 컴파일·Play Mode 호출 확인]` 프로젝트 compilation과 profile 직렬화를 확인했다. 한 `GameMap1` Play Session에서 17.0→22.0과 5.9→6.1을 강제했다. 17.0시는 그림자 길이 비율 3.732, 17.5시부터 지평선 그림자 없음, 18.0시는 방향광 0.040·ambient 0.544, 19.0시는 달빛 0.114, 22.0시는 0.132·달 그림자 없음이었다. 6.0시도 방향광 0.021을 유지했고, ±0.1시간 방향 전환과 모든 켜진 그림자 비율 4.8 이하가 통과했다.
- `[보존·미검증]` 시간 권위·씬 재바인딩·저장과 기존 dirty scene/material/preview asset은 바꾸지 않았다. 실제 Game View 색감의 최종 아트 판단, 달 원반, 달 그림자, 실내 감쇠와 Player build는 후속이며 이번에는 수치·렌더 상태의 Play Mode 호출로 확인했다. 최종 조명 아트 단계에서는 Sun/Moon을 분리하고 기존 controller 하나가 URP의 그림자 owner 하나만 교대시키는 구조를 재검토한다.

---

## 57. Player 외형 접지와 60초 조명 시험 주기 `[SHELL-01][ENVIRONMENT-01]`

- `[사용자 정정][2026-08-29]` Player 충돌체만 확인한 최초 판정은 부족했다. `GameMap1` 실측에서 바닥과 BoxCollider 하단은 모두 Y 0이었지만, 활성 `Female_Fig`의 실제 bake된 최저 버텍스는 Y 0.487이라 발과 그림자가 약 반 칸 떠 있었다.
- `[확정 원인·수정]` 높이 1·center 0인 물리 Player root Y 0.5 아래에 발 원점 기반 FBX 외형이 local Y 0으로 붙어 충돌체 중심 높이를 그대로 상속했다. 전역 Player·충돌체·스폰·저장 좌표는 유지하고 `Player/uploads_files_4931206_TrialFreya_FBX` 외형 루트 전체만 local Y -0.5로 내렸다. 개별 mesh·발 본을 보정하지 않아 외형 10개, 뼈와 그림자가 함께 같은 기준으로 이동한다.
- `[외부 사례 적용]` Unity 공식 휴머노이드 규약과 샘플처럼 물리 몸체 기준과 보이는 발 기준을 분리했다. contact offset은 물리 안정 여유이지 시각적 공중 간격이 아니며, 평지의 고정 반 칸 오류를 Foot IK로 덮지 않는다. 경사·단차나 특정 animation clip의 발 높이 편차는 별도 Root Transform Y/Feet 또는 Foot IK 범위다.
- `[시험 속도]` `SkyLightingCycleController`의 기본값과 영속 prefab 값을 실제 60초당 게임 24시간으로 맞췄다.
- `[Unity 컴파일·Play Mode 호출 확인]` 한 fresh `GameMap1` Play Session에서 root Y 0.5, collider 하단 Y 0, ground Y 0, visual local Y -0.5, 활성 skinned mesh 최저 Y -0.013을 확인해 허용오차 0.03 내 접지를 통과했다. 같은 session에서 60초 주기 직렬화 값과 §56의 일몰·일출 수치도 함께 재확인했다. 실제 물리 키보드 이동 중 animation별 발 접촉과 Player build는 미검증이다.

---

## 58. 청색 최소광·짧은 그림자·달 그림자 `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 피드백][2026-08-29]` §56 뒤에도 그림자가 길고, 태양→달 전환 중 주광이 사라져 보이며, 밤에는 달 그림자가 없다는 세 현상을 수정했다.
- `[확정 원인]` 이전 최소 주광 고도 12도는 그림자 길이를 높이의 약 4.705배까지 허용했다. 황혼 하한도 절대값이 아니라 `MoonIntensity × 0.5`라 18시는 0.040까지 떨어졌고, 그림자는 `useSun` 분기에서만 켜 밤 표본이 0건이었다.
- `[근본 수정]` 기존 씬 Directional Light 하나와 `RenderSettings.sun` 소유권을 유지하되 낮에는 태양, 밤에는 달의 방향·색·세기·그림자를 같은 Main Light에 적용한다. 지평선 ±15도에서 양쪽 기여를 SmoothStep으로 겹치고 합산 방향광 절대 하한 0.12와 청색 Trilight 하한 0.55를 별도로 보장한다. 태양·달 그림자는 각 실제 고도에서 독립 감쇠하며 지평선 구간에는 둘 다 끈다. 새 Light·Manager·씬 직렬화는 추가하지 않았다.
- `[그림자 제한]` 그림자를 만드는 방향광의 최소 고도를 31도로 올려 활성 그림자의 이론상 최대 길이를 높이의 `cot(31°) ≈ 1.664배`로 제한했다. 달 그림자는 별도 강도 0.28을 사용하며 밤에는 같은 URP Main Directional Light가 그림자 owner가 된다.
- `[Unity 컴파일·Play Mode 호출 확인]` 프로젝트와 프로필 직렬화가 컴파일됐다. 한 `GameMap1` Play Session에서 0~24시를 0.05시간 간격으로 한 번 순회해 실패 0건, 최소 방향광 0.120, 최소 ambient 0.550, 활성 그림자 최대 비율 1.664, 밤 그림자 표본 208건을 확인했다. 18시는 방향광 0.202·그림자 없음, 20시는 0.121·달 그림자 0.278, 22시는 0.132·달 그림자 0.280이었다. 자정 ambient sky 하한은 RGB `(0.147, 0.189, 0.315)`의 청색이었다. 프로필의 0/검정은 명시적 비활성 값으로 유지해 모드가 각 하한과 달 그림자를 끌 수 있다.
- `[보존·미검증]` 60초 시험 주기, Player·Camera·씬 흐름·저장과 사용자 dirty scene/material/preview prefab은 바꾸지 않았다. 실제 Game View의 최종 색감과 체감 그림자 길이, 달 원반·별·구름·실내 감쇠·Player build는 미검증이다. 검증 중 남은 `ShouldRunBehaviour()` Console assertion은 게임 코드가 아니라 Unity AI Assistant의 동적 `RunCommand` 호출 stack에서 발생했으며 Console을 지워 덮지 않았다.

---

## 59. 밝은 달과 끊기지 않는 Soft Shadow 전환 `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 피드백][2026-08-29]` 달은 밝아야 하며, 선명한 태양 그림자가 갑자기 사라진 뒤 달 그림자가 다시 나타나는 전환을 부드럽게 바꿔야 한다.
- `[확정 원인·기준선]` authoring Directional Light는 원래 Soft였지만 controller가 매 갱신마다 `Hard/None`으로 덮어썼다. 태양·달 모두 고도 12도 이하에서 그림자 강도를 0으로 만들어 일몰 17.2~18.9시에 실제 무그림자 구간 1.7시간, 60초 시험 주기에서 4.25초가 생겼다. 밤 22시 방향광도 0.132였다.
- `[근본 수정]` 기존 단일 URP Main Directional Light와 31도 방향 제한은 유지했다. 태양·달 그림자 고도 fade를 지평선 0도부터 31도까지 넓히고 프로필의 Soft 그림자 절대 하한 0.10을 적용해 그림자 map·mode가 끊기지 않게 했다. controller는 더 이상 Hard를 강제하지 않고 PC URP의 기존 High Soft Shadow를 사용한다. 모드는 이 하한만 0으로 끌 수 있으며, 그림자 전체 비활성에는 태양 keyframe과 달 그림자 강도도 0이어야 한다.
- `[밝은 달]` 월광 keyframe을 19.5시 0.32, 자정 0.40, 6.5시 0.26과 청색 RGB `(0.62, 0.72, 1.0)`으로 올렸다. 달 그림자 0.50, 방향광 하한 0.18, ambient 하한 0.62를 프로필 값으로 명시했다.
- `[Unity 컴파일·Play Mode 호출 확인]` 한 `GameMap1` Play Session에서 0~24시를 0.05시간 간격으로 한 번 순회했다. 실패 0건, `None` 0건, non-Soft 0건, 최소 방향광 0.238, 최소 ambient 0.620, 최소 그림자 0.100, 최대 그림자 길이 비율 1.664, 전환 인접 표본 최대 강도 차 0.032였다. 18시는 Soft/0.100/광량0.266, 22시는 Soft/0.500/광량0.367, 자정은 Soft/0.500/광량0.400이었다. PC pipeline의 Soft 지원과 High 품질값 3도 확인했다.
- `[보존·미검증]` Player·Camera·씬·저장·60초 주기와 사용자 dirty asset은 바꾸지 않았다. 표준 URP 실시간 Directional Light에는 시간에 따라 penumbra 폭을 연속 확대하는 공개값이 없어, 이번에는 High PCF 경계와 연속 강도 곡선을 사용했다. 실제 Game View 색감은 사용자 판단이 남았고 Mobile profile은 Soft Shadow가 비활성이라 PC와 같은 경계를 보장하지 않는다. 달 원반·별·구름·실내 감쇠·Player build는 범위 밖이다.

---

## 60. 일몰·일출 그림자 방향 연속화 `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 피드백][2026-08-29]` 밝기와 Soft 경계는 개선됐지만, 정반대 태양·달 방향을 인계할 때 그림자가 물체 반대편으로 크게 넘어가는 동작이 부자연스럽다.
- `[확정 원인·기준선]` controller는 같은 방위각에서 달 pitch를 태양보다 정확히 180도 뒤에 두고, 일몰 약 5초 동안 최소 고도 31도의 양쪽 방향을 `Slerp`했다. 실제 광원 forward는 17~19시에 총 118도, 1분 조명 갱신당 최대 1.475도씩 변해 60초 하루에서 초당 약 35.4도로 회전했다.
- `[근본 수정]` 밝기와 실제 천체 위치를 단일 그림자 방향에 억지로 합치지 않았다. 기존 Main Directional Light 하나를 유지하면서 그림자용 밤 key light의 pitch를 태양 경로에서 반사해 같은 방위각의 연속 경로로 만들었다. 일몰·일출에는 태양과 밤 key light의 전체 회전이 같고, 밤 그림자 방향은 12시간에 걸쳐 기존 속도로 이동한다. 정식 달 원반·월령·24시간 50분 궤도는 이후 별도 천체 표현으로 두며 이번 Save schema에는 상태를 추가하지 않았다.
- `[Unity 컴파일·Play Mode 호출 확인]` 한 `GameMap1` Play Session에서 0~24시를 1분 간격으로 한 번 순회해 최대 전체 회전 변화 0.253도, 최대 forward 변화 0.251도, 17→18시와 18→19시 전체 회전 차 각각 0도, `None` 0건, non-Soft 0건, 최소 그림자 0.100, 최대 그림자 길이 비율 1.664를 확인했다. 18시는 그림자/광량 0.100/0.266, 22시는 0.500/0.367로 §59의 밝은 달 값도 유지됐다.
- `[보존·미검증]` Player·Camera·씬 흐름·저장·60초 시험 주기와 사용자 dirty scene/material/preview prefab은 바꾸지 않았다. 현재 경로는 단일 URP shadow owner를 위한 아트용 조명 경로이며 실제 달 원반의 천문 궤도를 뜻하지 않는다. 실제 Game View 체감과 Player build는 미검증이다.

---

## 61. 그림자 경로 끝점 연속 감속 `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 피드백][2026-08-29]` 방향 반전은 없어졌지만 최소 광원 고도에서 그림자가 딱 멈춘 뒤 다시 움직이는 hard stop이 보이며, 끝으로 갈수록 계속 느려지는 움직임이어야 한다.
- `[확정 원인·기준선]` `ClampAboveHorizonPitch`가 원본 pitch를 31~149도로 강제 절단해 최소·최대값 바깥을 같은 회전으로 만들었다. 현재 경로의 1분 표본에는 최장 248분 연속 고정 구간이 있었고 60초 하루에서는 약 10.3초다.
- `[근본 수정]` 최소 고도와 그림자 길이 제한은 없애지 않았다. 0~180도 전체 아크를 `SmoothStep`으로 31~149도에 대응시켜 양 끝에서 속도가 0으로 연속 수렴하고, 중간에는 계속 이동하도록 `EvaluateAboveHorizonPitch`로 교체했다. 광량·색·그림자 강도는 기존 실제 고도 계산을 그대로 사용한다.
- `[Unity 컴파일·Play Mode 호출 확인]` 한 `GameMap1` Play Session에서 0~24시를 1분 간격으로 한 번 순회했다. 고정 구간 0건, 낮·밤 단조 진행 위반 0건, 일몰 마지막 1시간 감속 위반 0건, pitch 31~149도, 최대 회전 변화 0.247도, 최소 그림자 0.100, 최대 그림자 길이 비율 1.664였다. pitch는 6시 31.000, 7시 33.322, 8시 39.741, 16시 140.259, 17시 146.678, 18시 149.000도였고 18시·22시의 그림자/광량도 각각 0.100/0.266, 0.500/0.367로 유지됐다.
- `[보존·미검증]` 밝은 달·Soft Shadow·Player·Camera·씬 흐름·저장·60초 주기와 사용자 dirty asset을 보존했다. 실제 Game View 체감과 Player build는 미검증이다.

---

## 62. 일몰 교대 골 제거와 밤 최저점 연속 곡선 `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 피드백][2026-08-29]` 해가 완전히 진 뒤보다 해→달 교대 순간이 더 어두웠다. 교대 골을 없애고, 이후 밤은 현재 월광에서 점진적으로 어두워져 명확한 최저점을 지난 뒤 다시 밝아지며 아침으로 이어져야 한다.
- `[확정 원인·기준선]` 16→19.5시 키프레임이 이미 태양 광량 `0.82→0`, 달 광량 `0.04→0.32`를 시간으로 보간하는데 controller가 같은 구간에 고도 교차 페이드를 다시 곱해 이중 감쇠했다. 실제 최저는 18.30시 방향광 `0.238`·직접광 선형 명도 `0.113`이었고, 완전한 밤 19.50시는 `0.320`·`0.156`으로 다시 밝아졌다. 기존 자정 월광 `0.40`도 밤을 가장 밝게 만들어 요청한 밤 최저점과 반대였다.
- `[근본 수정]` 그림자용 태양·달 가중치는 유지하고, 광량·색 기여에만 프로필 값 `duskLightOverlapWeight=0.50`을 하강 중인 태양 반구에서 적용해 이중 감쇠 일부를 복원했다. 새벽 반구에서는 중첩값이 정확히 0이라 기존 일출 계산을 보존한다. Clear Sky와 새 기본 프로필의 자정 월광은 `0.24`로 두어 `19.5시 0.32 → 자정 0.24 → 6.5시 월광 0.26과 일출광`을 같은 SmoothStep 키프레임 곡선으로 연결했다.
- `[Unity 컴파일·Play Mode 호출 확인]` 컴파일 후 한 `GameMap1` Play Session에서 16.0→다음 날 6.5시를 0.05시간 간격으로 한 번 순회했다. 일몰·밤의 재밝아짐 0건, 직접광 명도 재상승 0건, 자정 이후 재암전 0건, 직접광 명도 재하강 0건이며 최저는 자정 방향광 `0.240`·직접광 명도 `0.117`이었다. 표본은 18.30시 `0.352/0.166`, 19.50시 `0.320/0.156`, 22시 `0.273/0.133`, 자정 `0.240/0.117`, 4시 `0.253/0.123`, 6시 `0.474/0.194`, 6.5시 `0.631/0.260`이고 모든 표본이 Soft Shadow를 유지했다.
- `[보존·미검증]` 그림자 방향 연속화·끝점 감속·31도 길이 제한·그림자 강도, 청색 월광색·ambient 하한, Player·Camera·씬 흐름·저장·60초 주기와 사용자 dirty asset을 바꾸지 않았다. 실제 Game View의 최종 체감 밝기와 Player build는 미검증이다. Console에는 본 변경 스택이 없는 기존 미정산 원정 오류와 Unity AI Assistant `ShouldRunBehaviour()` assertion이 남아 있으며 지워서 덮지 않았다.

---

## 63. 비가시 픽셀 구름 그림자 Cookie `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 정정][2026-08-29]` 탑뷰·쿼터뷰에서는 구름 본체가 화면에 보일 필요가 없다. 반투명 Plane·Quad·Sprite를 광원 앞에 두지 않고, 지면·캐릭터·건물 위를 지나가는 픽셀 구름 그림자만 구현했다.
- `[권위·데이터]` 새 날씨 Manager를 만들지 않았다. 기존 영속 `SkyLightingCycleController`가 `ClearSkyLightingProfile`의 Cookie·월드 크기 `(64,64)`·초당 이동값 `(0.35,0.15)`을 읽어 현재 씬의 단일 Main Directional Light에 적용한다. 오프셋은 게임 시각에서 다시 계산하지 않고 실제 frame 시간으로 누적·Repeat 래핑하므로 자정이나 강제 시각 변경에 점프하지 않으며, 씬 전환 뒤에도 같은 runtime 값이 이어진다.
- `[에셋·렌더링 경계]` `PixelCloudShadowCookie.png`는 64×64 RGB 회색조의 이어지는 픽셀 덩어리이며 흰색은 원광, 회색은 부분 감광이다. Import는 `Default/Linear(sRGB off)/Point/Repeat/Uncompressed/No Mipmaps/Read-Write off`로 고정했다. URP 추가 조명 데이터가 없는 Directional Light를 런타임에 몰래 보충하지 않고 해당 씬 경로와 함께 오류를 내며 바인딩을 거부한다.
- `[Unity 컴파일·Play Mode 호출 확인]` Profile 유효성, PNG 64×64, Repeat·Point·무압축·밉맵 없음과 직렬화 참조를 확인했다. 한 `GameMap1` Play Session에서 Cookie `PixelCloudShadowCookie`, 크기 `(64,64)`, 바인딩을 확인했고 백그라운드 frame 경과 뒤 오프셋이 `(0.014,0.006)→(3.016,1.293)`으로 이동했다. 같은 camera state의 Cookie A/B 렌더는 802,152 pixel 중 22,257개(2.77%)가 달라졌고 변경 pixel의 RGB 차이는 평균 13.73·최대 41이었다.
- `[씬 재연결 확인]` 같은 Play Session에서 `GameMap1→GameMapTest→GameMap1`을 한 번 호출했다. 같은 `SkyLightingCycleController` entity ID가 유지됐고 각 활성 씬 소유 Directional Light에 Cookie·크기와 연속 오프셋이 다시 적용됐다. 종료 뒤 Edit Mode `GameMap1`, pause off, `runInBackground=false`를 확인했다.
- `[보존·미검증]` 기존 낮·밤 곡선, Soft Shadow 방향·강도, Player 셸, Camera, 저장 schema와 사용자 dirty scene/material/preview prefab은 수정하지 않았다. 이 방식은 URP Main Light 직접광을 받는 Lit 표면만 감광하며 Unlit sprite에는 적용되지 않는다. 방향광 투영면 기준이라 광원 각도에 따라 무늬가 늘어날 수 있고, 최종 구름 밀도·명암·속도·픽셀 퍼펙트 정합과 Player build는 미검증이다. Console에는 검증 중 구식 camera ID를 전달한 Unity AI Assistant Capture 도구 오류 1건만 남았으며 게임 코드·런타임 stack 오류는 확인되지 않았다.

---

## 64. 상시 가시 서→동 픽셀 구름 그림자 `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 피드백][2026-08-29]` §63의 구름이 실제 Game View에서 거의 보이지 않았고, 언제 어느 방향으로 지나가는지도 분명하지 않았다. 시험 기본 풍향을 맵 서쪽에서 동쪽으로 고정하고 화면에서 명확하게 읽히도록 수정했다.
- `[확정 원인]` 기존 Cookie는 68.07%가 흰색이고 직접광 평균 감쇠가 약 5.5%였으며 투영 크기도 64×64라 현재 카메라에 한 덩어리가 지나가는 시간이 길었다. 더 근본적으로 화면 대부분인 160×160 Ground의 외부 `AwaiiStudio/URP_ToonLit`과 풀의 custom lighting이 URP Main Light Cookie를 샘플하지 않아, 변경 pixel이 위상에 따라 화면 0~5.08%뿐이었다.
- `[데이터·이동]` 같은 `SkyLightingCycleController`와 Directional Light 소유권을 유지했다. 64×64 Cookie는 2×2 pixel 단계의 `255/210/150/96` 네 명도로 재구성해 평균 직접광 감쇠를 29.24%로 올리고, 투영 크기는 24×24로 줄였다. Profile 이동값은 광원 로컬축이 아니라 맵 `X/Z` 초당 월드 이동이며 기본 `(0.75,0)`은 `+X=동`, `+Z=북` 기준 서→동이다. controller가 누적 월드 anchor를 현재 Light 투영면으로 변환해 시간 변경·씬 재바인딩 뒤에도 같은 위상을 사용하고, 이전 Vector2 field는 `FormerlySerializedAs`로 이관한다.
- `[렌더링 근본 수정]` Toon Ground와 풀 custom lighting에 `_LIGHT_COOKIES` variant와 `SampleMainLightCookie(WorldPosition)`를 연결했다. Toon은 Cookie를 기존 direct-light scalar에만 곱하고, 풀은 main-light color에만 곱하므로 ambient·추가 조명·material 색은 기존 경로를 유지한다. 새 날씨 Manager, overlay Plane·Sprite와 별도 구름 오브젝트는 추가하지 않았다.
- `[Unity 컴파일·Play Mode 호출 확인]` 변경한 Toon·Grass LOD0·Grass LOD1 shader는 compiler error 0이었다. 한 `GameMap1` Play Session에서 같은 controller entity를 9.2875초 추적해 월드 속도 `(0.75177,0,-0.00046)`을 확인했다. 낮의 실제 Camera Cookie A/B를 동쪽 위상 9개로 비교한 결과 0% 표본 없이 화면 변경 비율 최소 61.22%, 평균 68.51%, 최대 74.53%, 평균 RGB 차이 15.50이었다. 같은 session의 7.5/12/22시는 각각 66.47%/76.35%/65.62%가 바뀌어 아침·낮·밤 모두 비가시 구간이 없었다. 종료 뒤 Play Mode와 `runInBackground`를 껐다.
- `[보존·미검증]` 기존 낮밤 밝기·Soft Shadow 곡선, Player 셸·Camera·씬 흐름·저장 schema와 사용자의 dirty scene/material/preview prefab은 변경하지 않았다. Cookie는 직접광만 감쇠하므로 정식 Unlit 표현에는 별도 수신 정책이 필요하고, 광원 pitch에 따른 투영 축척은 URP Cookie 특성상 변한다. 실제 사용자 조작 중 체감 속도·최종 아트 승인과 Player build는 미검증이다. 현재 Console에는 이번 변경 대상이 아닌 `AwaiiStudio/ASFolliage`의 기존 main-light shadow keyword 중복 메시지 2건이 남아 있으며 지워서 덮지 않았다.

---

## 65. 구름 지면 크기·이동속도 고정 `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 피드백][2026-08-29]` 태양 고도에 따라 구름 그림자가 길고 짧아졌고, 이 크기 변화가 이동과 겹쳐 늘어날 때는 멈춘 듯 보이고 줄어들 때는 빠르게 넘어갔다.
- `[확정 원인]` URP Directional Light Cookie는 광원에 수직인 평면에서 `UV=(lightLocalXY-offset)/size`로 투영된다. 기존 fixed size 24는 지면에서 정오 24, 7.5시 40.762, 17시 43.689, 18시 46.599로 최대 1.942배 늘어났다. 이동을 멈춘 같은 명령 안에서도 고정 지점의 Y phase가 정오 `0.5012`에서 18시 `0.2581`로 바뀌어, world offset이 아니라 투영 scale이 가짜 속도의 원인임을 확인했다.
- `[근본 수정]` Profile의 Cookie Size를 광원 평면 크기가 아니라 수평 지면에서 원하는 한 주기 크기로 정의했다. 최종 주광 회전 뒤 동일한 `worldToLocalMatrix`로 각 light-local 축의 수평 투영 배율을 구해 Cookie size에 곱하고, world anchor도 같은 행렬로 변환한 뒤 보정된 size로 Repeat한다. 따라서 크기와 offset이 같은 투영 기준을 사용하며 새 Manager·구름 오브젝트·속도 보정값을 추가하지 않았다.
- `[Unity 컴파일·Play Mode 호출 확인]` C# compilation과 Profile 유효성을 확인했다. 한 `GameMap1` Play Session에서 7.5/12/17/18/22시의 실제 Cookie light-plane size는 각각 Y `14.131/24.000/13.184/12.361/21.110`으로 역보정됐고, 지면 footprint는 전 표본 `(24.000,24.000)`, 최대 크기 오차 0, 고정 지점 phase 최대 오차 0이었다. 가장 낮은 18시에서 4.0504 게임초 동안 지면 이동 `(3.03783,0)`과 속도 `(0.75000,0)`을 확인했다. 같은 Camera로 7.5/12/18시 화면을 캡처해 늘어진 긴 띠 없이 같은 픽셀 덩어리 크기가 유지되는 것도 확인했다.
- `[보존·미검증]` §64의 밀도·명암, 서→동 속도, 낮밤 밝기·Soft Shadow, Player 셸·Camera·씬·저장과 사용자 dirty asset을 변경하지 않았다. 현재 고정 azimuth·roll 0의 단일 주광 경로에서는 정확하며, 향후 방위각·roll까지 동적으로 바꾸면 Cookie size만으로 shear를 없앨 수 없어 world-XZ 직접 샘플 방식을 재검토한다. 실제 사용자 조작 체감과 Player build는 미검증이며 Console의 변경 전 `ASFolliage` keyword 중복 2건은 남겼다.

---

## 66. 구름 그림자 고도별 경계·농도 보정 `[ENVIRONMENT-01][SHELL-01]`

- `[사용자 피드백][2026-08-29]` 구름 그림자가 시간대와 관계없이 항상 같은 선명도였고, 기존 기능을 다른 경로로 중복 계산해 부하를 늘리지 않으면서 오브젝트 그림자 전환과 어울리게 바꿔야 했다.
- `[근본 수정]` 기존 `SkyLightingCycleController`의 시간 평가·월드 이동·24×24 역투영과 URP Main Light Cookie 수신 경로는 유지했다. 원본 64×64 Cookie에 mipmap·Trilinear를 켜고, 영속 controller가 소유하는 단일 64×64 선형 RenderTexture에 한 번의 LOD sample과 흰색 혼합만 적용한다. 낮은 주광 고도는 `mip 1.25 / opacity 0.55`, 높은 고도는 `mip 0.25 / opacity 0.90`으로 보간하며 8-bit 고도 key가 달라질 때만 갱신한다. 표준 URP·Toon·Grass의 최종 Cookie sample은 기존과 같은 수신 픽셀당 1회이고 새 Manager·구름 오브젝트·수신 shader pass는 추가하지 않았다.
- `[비용 경계]` 전처리 대상은 화면 해상도나 수신 오브젝트 수와 무관한 4,096 texel이다. 현재 60초 하루·1게임분 조명 step의 최대 약 24회/초에서도 source sample은 약 98,304회/초이고 추가 RenderTexture는 RGBA32 약 16KiB 한 장이다. 이는 구조상 상한 계산이며 GPU Profiler 실측 전에는 성능 영향이 0이라고 단정하지 않는다.
- `[Unity 컴파일·Play Mode 호출 확인]` C# compilation, Profile 유효성, 원본 7 mip·Trilinear, filter shader compiler error 0을 확인했다. 한 `GameMap1` Play Session에서 정오/18시/22시 모두 지면 footprint `(24.000,24.000)`을 유지했고 runtime Cookie는 RenderTexture, 전처리 RT·Material은 각각 1개였다. 출력 RT는 정오 `mip 0.25 / opacity 0.90 / 명도 112~255 / 4단계 / 이웃차 4.973`, 18시 `mip 1.25 / opacity 0.55 / 명도 168~255 / 28단계 / 이웃차 3.081`, 22시는 정오와 같은 값으로, 지평선 구간의 경계와 농도가 실제 출력 데이터에서 낮아졌다. Play Mode 종료 뒤 두 runtime resource가 모두 0개로 해제된 것도 확인했다.
- `[보존·미검증]` §65의 24×24 지면 크기와 `+X 0.75` 이동 계산, 낮밤 광량·오브젝트 Soft Shadow, Player 셸·Camera·씬·저장과 사용자 dirty scene/material/preview prefab은 변경하지 않았다. Game Camera 지정 캡처에는 Unity AI Assistant가 Unity 6 legacy hash를 Instance ID로 찾지 못해 도구 오류 2건이 Console에 남았으며, 변경 코드·filter shader 오류는 확인되지 않았다. 사용자 체감 선명도·GPU Profiler·Player build는 미검증이다.

---

## 67. 도심 공유 공간 후보와 의료 POI `[MAP-01][SPAWN-01][POI-01][LOOT-01][AI-01]`

- `[사용자 요청][2026-08-30]` 실제 건물·내부는 만들지 않고 특정 Cube를 다른 색의 건물로 취급하며, 그 앞 상자를 회복약/일반 같은 의미 분류로 연결하는 최소 절차 콘텐츠를 구현했다.
- `[권위·배치]` `UrbanMapLayout`이 도로 후보와 모든 건물의 도로 방향 접근 후보, seed당 `Medical` POI 하나를 불변 read-only 데이터로 한 번 소유한다. 청록 건물 색·이름은 표현이며 분류 원본은 `UrbanPoiKind.Medical`이다. 기존 authored Chest 인스턴스는 stable binding과 manifest를 통해 POI 외벽 앞 content 위치로 이동하고 별도 접근점은 NavMesh로 검증한다.
- `[AI 재사용]` `ProceduralUrbanMapGenerator`가 좁은 `IEnemyPatrolPointSource`를 구현하고 scene binding이 기존 두 Enemy에 명시 주입한다. AI는 시작 반경·최근점의 값싼 필터 뒤 완전 경로를 최대 8회 계산하며, 필수 도심 provider가 준비되지 않으면 임의 순찰 fallback으로 오류를 덮지 않는다. provider가 없는 고정 맵의 기존 임의 NavMesh 순찰은 유지한다.
- `[Loot·저장]` 기존 시험 Chest에 별도 `PrototypeMedicalPoiLoot`를 연결해 Fresh에서 치료제 Item ID 7 하나를 지급한다. 기존 일반 `PrototypeRaidChestLoot` 에셋, Chest/UI/행동시간·ItemDatabase·Fresh 원자 적용·Resume grid 복원과 entity roster는 보존했다. POI 의미와 위치를 layout/world hash에 넣고 generator·spawn manifest를 v3으로 올려 이전 v2 진행 중 원정은 다른 맵으로 조용히 복원하지 않고 기존 Recovery 실패 경계를 따른다.
- `[Unity 컴파일·순수 검증]` 전체 C# 컴파일에 성공했다. 기본 설정 seed 0~255 각각에서 같은 seed 결정성, 의료 POI 1개, 기존 순서의 Roadside와 건물 접근 후보, 일반/의료 manifest를 확인했다.
- `[Play Mode 1회]` 사용자의 dirty `GameMap1`을 저장·닫지 않고 깨끗한 `GameMapTest`만 additive로 한 번 실행했다. seed `1999354186`에서 의료 건물 1개(index 0), 공유 후보 395개, Entry→Portal과 POI 접근 complete path, 기존 Chest의 POI 위치, 치료제 ID 7 한 칸, Enemy 2개의 provider 주입·NavMesh 준비와 Raid readiness `Ready`를 확인했다. 종료 뒤 `GameMap1`을 dirty 상태 그대로 활성 복원했다.
- `[남은 범위]` 건물 내부·문·방, 대형 랜드마크·다중 POI, 일반/의료 상자의 동시 fixture, 가변 개수 동적 spawn, 위험·보상 예산과 엄폐·생태 전술은 구현하지 않았다. Console에는 변경 전 Unity AI Assistant camera ID 오류 2건과 외부 `ASFolliage` shadow keyword 중복 2건만 남아 있으며 이번 런타임 오류는 추가되지 않았다.

---

## 68. 도심 원정 개체 동적 Spawn Catalog `[SPAWN-01][POI-01][LOOT-01][AI-01][SAVE-01]`

- `[사용자 요청][2026-08-30]` §67의 고정 시험 개체를 다음 절차 콘텐츠 확장에 재사용할 수 있도록, 현재 화면 결과와 수량은 유지하면서 catalog 기반 동적 생성 경계로 옮겼다.
- `[권위·생성]` 새 `RaidSpawnCatalogDefinition`이 stable ID, 종류, 준비된 prefab, 지면 Y와 선택적 POI 의미를 소유한다. `RaidCheckpointSceneBinding`은 layout 완료 뒤 기존 planner로 manifest를 만들고 최종 world pose에 Chest 1·Enemy 2를 생성한다. 전부 초기화된 경우에만 scene-local `RuntimeRaidEntities` registry를 공개하며, 실패 후보는 비활성화 후 폐기한다.
- `[수명·NavMesh]` Enemy는 최종 pose에서 `Awake`하므로 순찰 원점이 manifest 위치이며 즉시 기존 `IEnemyPatrolPointSource`를 주입받는다. runtime root는 `ProceduralUrbanMapGenerator`의 형제로 두어 `NavMeshSurface(CollectObjects.Children)`의 geometry 수집 경계와 섞이지 않는다. 움직이는 Enemy의 현재 좌표를 초기 좌표로 오판하던 검증은 `PatrolHomePosition`을 확인하도록 바로잡았다.
- `[콘텐츠·호환]` `PrototypeMedicalPoiChest`, damage-1 근접 Enemy, 기존 동작을 보존한 원거리 Enemy 준비 prefab과 3-entry 시험 catalog를 추가했다. 씬의 고정 Chest·Enemy는 제거했지만 stable ID·요청 순서·generator/manifest version·layout 보호 입력과 combined world hash 계약은 유지해 현재 v3 Recovery 레코드 대응을 보존했다. ReturnPortal은 기존 scene object다.
- `[Unity 정적·컴파일 확인]` `GameMapTest`에는 authored Chest/Enemy 0, catalog entry 3, 보호 anchor 2와 missing script 0임을 확인했고 256 seed layout·manifest 검증을 통과했다. 전체 프로젝트 C#은 `scriptCompilationFailed=False`다.
- `[Play Mode 호출 확인]` dirty `GameMap1` 하나에서 Play를 시작해 런타임 `DirectSceneTravel`로 `GameMapTest`에 한 번 진입했다. seed `-135520631`, world hash `AEB6979AFF6755B0`에서 readiness `Ready`, sibling root, Chest 1·Enemy 2, 의료 loot·AI·NavMesh·stable-ID registry를 확인했다. 같은 세 runtime Entity ID를 유지한 채 `TryCaptureWorld → TryPrepareRestore → TryApplyRestore`를 통과했다.
- `[중단 복구·Console]` 앞선 검증 세션 중단으로 clean `GameMapTest`가 additive로 남아 두 씬이 합쳐져 보였으나, 파일 병합이나 저장은 없었다. dirty `GameMap1`을 보존하고 검증 씬만 저장 없이 닫았다. 최종 검증은 성공·실패 모두 Play 종료를 요청하는 경계로 실행했고 종료 뒤 Play off, scene 1, active `GameMap1`, dirty 보존을 확인했다. Console Error는 검증 전후 5건으로 동일하며 새 런타임 오류는 없었다. 기존 5건은 과거 Camera Capture 2, 외부 `ASFolliage` 2, ordinary save 미해결 원정 방어 1이다.
- `[남은 범위]` 가변 개수·spawn profile, 다중 POI·랜드마크, 위험·보상 예산, 정식 콘텐츠 prefab과 Player build는 이번 범위가 아니다.

---

## 69. 맑음·비 통합 날씨와 월드 고정 픽셀 강수 `[ENVIRONMENT-01][SHELL-01][INPUT-01]`

- `[사용자 요구·정정][2026-08-30]` 낮/밤은 시간, 맑음/비는 날씨인 독립 축으로 만들고 ESC에 네 시험 버튼을 둔다. 참고 영상처럼 비 자체만 픽셀 좌표를 쓰며, Camera에 붙은 양방향 짧은 사선의 연속 낙하가 아니라 희소한 긴 약사선 프레임이 나타났다 사라져야 한다. 비는 흰색이 아니라 반투명 청색이고 기존 하늘광·구름과 같은 날씨 풀에서 움직여야 한다.
- `[확정 원인·참고 구조]` 첫 초안은 64×64 두 mask를 서로 반대 방향으로 scroll해 1024×768에서 화면의 4.378%, 약 4,800개 streak group을 동시에 그렸다. 그래서 64픽셀 wallpaper·X형·화면 고정 괴리가 생겼다. 참고 제작자가 밝힌 구조는 CPU particle이나 별도 Pixel Camera가 아니라 몇 장의 tiling/looping texture를 GPU의 단일 post-process draw로 합성하는 방식이므로, 게임 화면 전체를 다시 픽셀화하지 않는다.
- `[권위·날씨 결합]` 새 Weather Manager를 만들지 않았다. 영속 `SkyLightingCycleController`가 Clear/Rain preset과 시간 축을 함께 소유하고, 매 적용마다 원래 시간 sample에 ambient·directional·shadow·cloud 보정을 합성한다. Clear는 정확한 no-op preset이다. Rain 전환과 비·구름 이동은 gameplay scaled time을 함께 사용해 Base pause에서 한쪽만 움직이지 않으며, ESC 시험 버튼은 즉시 상태만 바꾼다.
- `[강수 렌더링]` PC Renderer에 gameplay Camera 전용 `PixelRainRendererFeature` 한 개를 After Post Processing/Depth+Normal/fetchColor off로 추가했다. 256×256 Point/Repeat RGBA의 각 channel은 독립 frame이며 8FPS로 교대한다. 각 frame은 6도 선분 12개, 길이 12/16/20, 활성 texel 192개(화면 약 0.293%)로 동일하다. Camera가 2m 평행 이동한 전후 고정 월드 지점의 pattern grid가 `(0,30)`으로 같았고, 1024×768 캡처에서 X형·연속 scroll·과밀 반복 없이 1픽셀 장선과 청색 반투명이 확인됐다. Camera follow·smooth zoom이 끝난 render 경계에서 투영 좌표를 다시 게시해 이전 frame의 Camera 좌표를 쓰지 않는다.
- `[물 튐·차폐]` 완만한 Depth/Normal 표면에는 7×4 atlas의 4프레임 물 튐을 world cell 기준으로 합성한다. 명시적인 `RainShelterOccluder`만 512×512 RFloat 최고높이 cache에 들어가며 일반 Player·NPC·상자 Collider는 roof로 오인하지 않는다. cache의 월드 범위는 최소 32m이고 현재 화면비·Camera 최대 zoom의 지면 footprint와 recenter 여유를 전부 덮도록 자동 확장한다. marker가 0개면 texture upload·raycast를 생략하고, 실제 rebuild는 `Physics.SyncTransforms` 뒤 실행한다. 임시 4×4m roof Collider 검증에서 Player Y `0.500`, roof top/sample `3.125`, 외부 `-10000`으로 실내 차단과 외부 노출이 분리됐다.
- `[ESC·상태 검증]` `GameplayEscapeMenuController`의 기존 단일 Escape 입력과 Base pause/Raid non-pause를 보존한 채 `환경 테스트 → 낮/밤/맑음/비/뒤로`를 추가했다. 실제 persistent UnityEvent는 각 1개이며 낮/밤은 날씨를, 맑음/비는 시간을 바꾸지 않았다. Day·Night 각각 Clear→Rain→Clear에서 ambient·직접광·그림자·구름 값과 rain pass 상태가 최초 Clear로 복귀했고, 시험 중 멈춘 자동 시간은 뒤로/메뉴 닫기에서 이전 상태로 복원됐다. Base 환경 시험 중에는 세계 pause를 유지하고 날씨 전환·구름·비 presentation만 unscaled preview time으로 진행한다.
- `[정적·보존·미검증]` Rain shader는 D3D11에서 supported, pass 1, compiler message 0이고 Profile·Prefab 참조와 256 texture 설정을 확인했다. 기존 비활성 3D PixelArt feature, Player·Camera·씬·저장 schema, 사용자 dirty scene/material/preview prefab은 변경하지 않았다. 실제 건물 roof marker, 최종 2D transparent sprite의 Depth 계약, 물·안개·번개·잎 흔들림·빗소리·젖음, GPU Profiler와 Player build는 후속 범위다. 최종 Console에는 이번 기능과 무관한 기존 Camera Capture 2건, 외부 `ASFolliage` keyword 2건과 과거 미정산 원정 방어 3건이 남아 있으며 지워서 덮지 않았다.

---

## 70. 긴 비 선·빠른 비 cadence·줌 고정·비반복 위치 `[ENVIRONMENT-01][CAMERA-01]`

- `[사용자 피드백][2026-08-30]` §69의 비는 참고 영상보다 선이 짧아 더 많아 보였고, 8FPS 점멸은 한 frame이 멈춘 것처럼 보였다. Camera 줌에서는 화면 종속과 같은 pattern 재배치가 남았으며, 20FPS로 올린 뒤에는 네 frame이 0.2초마다 같은 자리에 반복되는 점도 확인됐다.
- `[확정 원인·시간 기준]` 기존 8FPS는 한 frame hold가 125ms이고 4-frame loop가 500ms였다. 공개 참고 자료에는 제작자의 정확한 FPS 공식이 없으므로, `hold=1/FPS`, `display frame 수=display FPS/rain FPS`를 적용해 60Hz에서 정확히 세 화면 frame마다 바뀌는 20FPS(50ms hold, 200ms loop)를 시험 기준으로 선택했다. 물 튐 cadence가 2.5배 빨라지지 않도록 splash clock은 기존 8FPS로 분리했다.
- `[선 길이·밀도]` 256×256 RGBA 각 frame을 6도 장선 5개, 길이 32/38/44/50/56으로 재생성했다. frame당 활성 texel은 192→220으로 14.6%만 늘지만 선 개수는 12→5로 58.3% 줄고 평균 길이는 16→44px로 2.75배 늘었다. 실효 시각량을 유지하도록 streak opacity는 0.55→0.48로 조정했다. 사선 계단은 간격 하드코딩이 아니라 선분의 실제 각도와 길이를 Bresenham rasterize한 결과다.
- `[줌 근본 수정]` 이전 좌표는 `screen(worldPoint)-screen(worldOrigin)`이라 Camera 평행 이동만 지우고 직교 배율 `screenHeight/(2×orthographicSize)`는 남겼다. 이제 연속 좌표를 `screen relative pixel × (2×orthographicSize/screenHeight) × 48 pattern pixel/world unit`로 변환한 뒤 마지막에 한 번만 정수화한다. 같은 시험 월드 지점은 orthographic size 8과 3.5에서 기존 grid drift `346.836`이었지만 수정식에서는 `0.000046`이었다.
- `[짧은 loop 반복 제거]` RGBA frame 선택은 그대로 GPU에서 수행하되 네 frame마다 `Hash22(loopIndex)`로 전체 periodic pattern의 월드 phase를 이동한다. 모든 tile에 같은 loop offset을 사용해 새 seam을 추가하지 않고 Camera 이동·줌 보정을 유지하며, CPU particle 상태나 진짜 runtime RNG 없이 같은 네 위치의 0.2초 반복을 숨긴다. 같은 RGBA frame index인 visual time 0.01초와 0.21초를 각각 렌더한 두 capture에서 빗줄기 위치가 서로 다름을 확인했다. 기존 tile별 channel phase 차이 때문에 256 경계를 넘는 선 끝이 드물게 끊길 가능성은 남지만 두 대표 capture에서는 seam이 관찰되지 않았다.
- `[검증·보존]` Unity C# 컴파일 성공, Rain shader supported/pass 1/compiler message 0, pattern RGBA 활성 texel 220/220/220/220, Point/Repeat, streak 20FPS·splash 8FPS·world density 48·opacity 0.48을 확인했다. Play Mode 집중 검증 뒤 Play를 종료했고 Console은 기존 Camera Capture 2·미정산 원정 3·외부 `ASFolliage` 2인 7건 그대로다. 사용자 dirty `GameMap1`·재질 2개·preview Camera prefab은 저장하거나 변경하지 않았다. 정확한 1 screen pixel 두께와 완전한 world scale 투영을 모든 zoom에서 동시에 보장하려면 향후 distance-field 선 표현이 필요하며 현재는 world 위상 보존을 우선한다.

---

## 71. Collider 기반 픽셀 물 튐과 오브젝트 경계 수정 `[ENVIRONMENT-01][CAMERA-01]`

- `[사용자 피드백][2026-08-30]` 빗줄기 외관은 거의 완성됐지만 물 튐이 잘 보이지 않았고, Collider 뒤로 항상 가려지는 것은 아니면서도 오브젝트 근처 몇 frame이 간헐적으로 잘리거나 표면과 어긋나 보였다.
- `[확정 원인]` 기존 물 튐은 실제 충돌 결과가 아니라 full-screen shader의 각 출력 픽셀이 자기 Scene Depth·Normal과 world Y를 기준으로 7×4 splash 중심을 다시 계산했다. 따라서 한 splash footprint 안에 지면·오브젝트 윗면·수직면이 함께 들어오면 서로 다른 표면 투영과 normal gate가 한 그림을 분할했다. atlas도 frame별 활성 픽셀이 `1/3/4/4`, 8FPS 뒤 긴 공백 구간이라 실제 capture에서 거의 보이지 않았다. 빗줄기 pass 자체는 `ZTest Always`라 일반 Collider가 물리적으로 가리는 구조도 아니었다.
- `[근본 수정]` 빗줄기 full-screen pass와 기존 날씨 권위는 유지하고, 같은 `PixelRainPresentation` 안에 24개짜리 reusable billboard pool을 추가했다. 화면 후보를 초당 28회만 결정론적으로 뽑아 `Physics.RaycastNonAlloc`하고, trigger·IgnoreRaycast·다른 scene을 제외한 가장 가까운 실제 Collider를 먼저 확정한 뒤 normal Y 0.75 이상인 윗면만 허용한다. 수직 앞벽을 건너뛰어 뒤 바닥에 튀지 않으며, `RainShelterOccluder` 최고높이 cache 아래의 hit도 폐기한다. 활성 splash는 Collider local anchor를 약 0.333초 추적하고 Collider 소멸·비활성·scene 이탈 때 즉시 꺼진다.
- `[표현·경계]` 기존 7×4 atlas의 frame별 활성 픽셀을 `3/3/6/6`으로 보강하고 2배 화면 픽셀 크기·12FPS·opacity 0.82로 재생한다. 전용 shader는 `ZTest LEqual`, `Transparent-100`, 그림자·probe 없음이며 Camera render 직전에 Collider anchor를 화면 픽셀 격자에 정렬한다. 그래서 오브젝트 자체가 splash를 depth로 자연스럽게 가리되, 일반 투명 캐릭터·소품은 이후에 그려져 앞뒤 관계를 보존한다. full-screen 빗줄기와 impact splash는 동일 weather intensity를 쓰지만 빗줄기 하나를 끝까지 추적하는 1:1 물리 simulation은 아니다.
- `[성능·실패 경계]` pool과 quad mesh는 런타임 한 번만 만들고 frame당 GC를 만들지 않는다. 긴 hitch가 와도 한 Tick 최대 4개만 생성하고 미처리 backlog를 다음 frame에 쏟지 않는다. Renderer Feature는 splash가 더는 Scene Normal을 읽지 않으므로 요구사항을 `Depth|Normal`에서 `Depth`로 줄였다. 현재 PC render scale 1과 단일 gameplay scene 계약에 맞춘 값이며, 전용 비 충돌 layer·급경사 splash·additive local-physics scene은 필요해질 때 별도 재개방한다.
- `[Unity 컴파일·Play Mode 호출 확인]` C# 컴파일 성공, full-screen/impact shader 모두 supported·pass 1·compiler message 0을 확인했다. 한 `GameMap1` Play Session에서 1초 hitch 주입 뒤 활성 수가 4개이고 다음 0초 Tick에도 4개라 backlog가 없었다. 정상 표본은 활성 10개 전부가 바닥 또는 오브젝트 윗면의 Collider 위에 있었고 공중 표본 0개, 최대 표면 거리 0.01855m, 화면 픽셀 오차 0.00524px였다. Camera size 5→3.5에서 billboard world scale 비율은 0.70000으로 화면 픽셀 크기를 유지했다. 최종 capture는 `Temp/RainColliderSplashFinal.png`다.
- `[보존·미검증]` 빗줄기 길이·20FPS·월드 위상·Clear/Rain 조명·Player·Camera·씬·Save와 사용자 dirty `GameMap1`·재질 2개·preview Camera prefab은 변경하지 않았다. 현재 씬에는 roof marker가 없어 splash의 shelter 판정은 기존 §69 cache 검증과 동일 계산을 코드로 재사용했으며 실제 건물 roof 체감은 미검증이다. 검증용 offscreen `Camera.Render()`가 URP UI overlay와 다른 attachment 크기를 사용해 도구 호출 stack의 RenderPass 오류를 Console에 남겼지만, 일반 gameplay 경로가 아니며 두 Rain shader compiler 오류는 0이다. Console을 지워 결과를 덮지 않았다.

---

## 72. 물 튐 밀도 소폭 상향 `[ENVIRONMENT-01]`

- `[사용자 확인·조정][2026-08-30]` §71의 물 튐 외관과 Collider 경계는 유지하고, 빗줄기 밀도에 비해 드문 물 튐만 소폭 늘렸다. 후보 충돌 빈도를 초당 `28 → 34`회로 약 21% 올렸으며 4프레임 atlas 모양·12FPS·2배 픽셀 크기·24개 pool·충돌/차폐/줌 계산은 바꾸지 않았다.
- `[현재 표현 경계]` 위치와 시작 시점은 결정론적으로 달라지지만 물 튐 모양은 현재 서로 다른 여러 종류가 아니라 하나의 4프레임 splash animation이다. 별도 모양 variant는 이번 수치 조정에 포함하지 않았다.
- `[정적 확인]` C# 기본값과 `PersistentGameplayShell` prefab 직렬화 값을 모두 34로 맞췄고 기존 사용자 dirty scene·재질·preview prefab은 변경하지 않았다. 최종 화면 밀도 체감은 사용자 확인 대상이다.

---

## 73. Editor 직접 Play 저장 격리와 물 튐 월드 줌 수정 `[SAVE-01][ENVIRONMENT-01][CAMERA-01]`

- `[사용자 피드백][2026-08-30]` 빠른 맵 진입 시험이 이전 원정 캐시 오류 때문에 반복 지연됐고, 빗줄기는 줌 비율에 따라 변하지만 Collider 물 튐만 화면에 붙은 것처럼 항상 같은 크기였다.
- `[캐시 원인·수정]` `GameMap1` 직접 Play는 `GameStartRequest` 없이 authored 상태로 시작하면서도 `GameSaveManager`와 `RaidCheckpointStore`는 실제 `Application.persistentDataPath`를 사용했다. 그래서 `TryPrepareNewRaid`가 실제 ordinary save의 `raidInProgress`를 발견해 메인메뉴 정산 오류를 3회 냈다. 이제 `GameplayShellBootstrap`이 Editor gameplay 씬 직접 시작을 판별해 두 저장소를 같은 고유 `temporaryCachePath` 하위 루트로 격리한다. 정상 메인메뉴 New/Load/Resume은 pending request가 있으므로 실제 저장·복구 경로와 fail-closed 판정을 그대로 사용한다.
- `[렌더 차이·원인]` 빗줄기는 full-screen shader가 `48 pattern pixel/world unit` 월드 격자를 샘플링한다. 반면 물 튐은 실제 Collider에 붙은 world-space pooled MeshRenderer면서도 크기를 `atlas 크기 × 2 × (2×orthoSize/pixelHeight)`로 매 frame 역보정해 화면에서 항상 14×8px가 되었다. 두 효과는 충돌 필요 때문에 같은 renderer일 수는 없지만, 물 튐 크기까지 화면 고정일 이유는 없었다.
- `[물 튐 수정]` Collider·pool·4프레임·34회/초·차폐·depth 판정은 유지하고 atlas pixel당 0.0111 world unit을 새 단일 배율로 사용해 billboard 월드 크기를 약 0.1554×0.0888로 고정했다. bottom-center anchor만 정수 화면 pixel에 맞추며, smooth zoom에서 투영 폭의 홀짝을 다시 보정해 0.5px 옆으로 튀는 처리는 제거했다. 이제 투영 크기는 `1 / orthographicSize` 비율로 변해 빗줄기와 같은 방향으로 줌에 반응한다.
- `[Play Mode 호출 확인][2026-08-30]` dirty `GameMap1`을 직접 1회 실행했다. ordinary save와 Recovery가 동일한 `temporaryCachePath/FantasySurvivalDirectPlay/<session>` 루트에 생성됐고, `TryBeginRaid("GameMapTest", "RaidEntry")`는 `Entering → Active`로 끝나 baseline·checkpoint·ordinary marker를 모두 임시 루트에 남겼다. 기존 실제 ordinary marker 오류는 전후 모두 3건이라 새 오류가 추가되지 않았다.
- `[Play Mode 호출 확인][2026-08-30]` Rain 상태의 활성 Collider 물 튐 표본은 ortho 3.5/5/8 모두 월드 크기 0.1554×0.0888을 유지했고, 현재 Game View에서 화면 높이는 10.87/7.61/4.76px로 변했다. Play 종료 뒤 `GameMap1` dirty 상태와 Edit Mode가 복원됐으며 C# 동적 컴파일 오류는 없었다. 사용자 dirty scene·재질·preview prefab과 실제 세이브/Recovery는 변경하지 않았다.

---

## 74. 물 튐 애니메이션 속도 상향 `[ENVIRONMENT-01]`

- `[사용자 조정][2026-08-30]` 4프레임 Collider 물 튐 재생을 `12 → 20FPS`로 올려 한 동작 길이를 약 `0.33 → 0.20초`로 줄였다. 발생량·pool·충돌·차폐·줌 크기와 빗줄기 표현은 변경하지 않았다.
- `[정적 확인]` `PixelRainPresentation` 기본값과 영속 prefab 직렬화 값을 20으로 맞췄고 동적 C# 컴파일이 성공했다. 사용자 dirty 씬·재질·preview prefab은 제외했다.

---

## 75. Rain 균일 흐림과 단계형 로컬광 프로토타입 `[ENVIRONMENT-01][CAMERA-01]`

- `[사용자 피드백·원인][2026-08-30]` 환경 시험에서 Rain을 눌러도 이동 구름 무늬가 남았다. 버튼이나 전환 누락이 아니라 Rain profile이 기본 Cookie 농도 `0.55~0.90`에 배율 `1.35`를 적용해 반점을 약 `0.74~1.0`으로 오히려 강화한 것이 원인이었다.
- `[날씨 근본 수정]` 기존 `SkyLightingCycleController`와 단일 Directional Light 소유권을 유지하고 Rain의 구름 농도 배율만 `0`으로 바꿨다. Rain은 기존 ambient `0.78`, directional `0.52`, shadow `0.42` 감쇠가 전체를 균일하게 흐리며, Clear는 배율 `1`의 이동 Cookie를 누적된 위치에서 다시 표시한다. 별도 Rain Cookie·날씨 Manager·Camera 픽셀화는 추가하지 않았다.
- `[로컬광 구조]` 일반 Unity `Light` 대신 scene object가 색·반경·강도·Surface/Halo band·월드 셀 크기를 소유하는 `SteppedLocalLight`와 PC Renderer의 전용 full-screen pass를 추가했다. pass는 persistent gameplay Camera에 대해 `Depth|Normal`, `BeforeTransparents`, color fetch 없음, additive 합성을 사용한다. 원본 표본은 full resolution으로 유지하고 재구성된 world position만 셀 snap한 뒤 Surface와 1.25배 Halo를 각각 단계화하므로 Camera 전체나 기본 텍스처는 픽셀화하지 않는다. 활성 scene과 `DontDestroyOnLoad` 영속 Player 셸 자식 중 Camera 절두체와 교차하는 광원을 거리순으로 고르고 기본 8개·hard cap 16개만 전달하며 초과는 1회 경고한다.
- `[시험 배치·보존]` clean `GameMapTest`의 절차 건물 배제 앵커 `UrbanLayoutProtectionAnchors/FormerMeleeFixture` 아래에 Collider·표준 Light가 없는 prefab 1개를 배치했다. 반경 4.5, 셀 0.18의 따뜻한 emitter와 비충돌 receiver pillar만 있으며 raid spawn catalog·manifest·NavMesh·persistent shell에는 넣지 않았다. 사용자 dirty `GameMap1`, 재질 2개와 authoring preview Camera prefab은 저장·stage하지 않았다.
- `[Unity 컴파일·Play Mode 확인]` shader supported/compiler error 0과 C# compile 성공을 확인했다. 한 Play Session에서 Clear→Rain→Clear의 Cookie 농도가 `양수→0→양수`, Rain 방향광이 Clear보다 낮음, 이후 복원을 확인했다. `GameMapTest` Night/Clear에서는 active scene 광원 1개·반경 4.50·셀 0.18, 표준 Light 없음, 전용 feature active와 전체화면 PixelArt feature inactive를 확인했고 실제 Game View에서 5/4단계 Surface/Halo 셀 밴드가 보였다. Day/Rain capture에서는 `opacity=0.000`이며 이동 구름 반점 없이 균일한 흐림과 비가 함께 표시됐다. 후속 집중 Play 확인에서는 scene fixture와 `DontDestroyOnLoad` 영속 셸 자식 probe가 동시에 선택되어 전달 수가 2였으며, probe 제거 뒤 Play Mode를 종료했다.
- `[남은 경계·Console]` 이번 로컬광은 프로토타입 Surface/Halo 표현이며 광원별 full-screen pass 비용이 남는다. 벽 뒤 screen-space raymarch 그림자·Transparent Sprite 수광·실내 광원 배치·다수 광원 GPU profile 및 향후 volume/tiled 전환·Mobile·Player build는 미검증이다. 검증 중 Unity Camera Capture 도구가 새 Entity ID를 잘못 해석해 도구 오류 2건을 남겼지만, 수동 `Camera.Render()` 대신 정상 Game View `ScreenCapture`로 두 화면을 확인했고 gameplay/shader 오류는 추가되지 않았다. 기존 외부 `ASFolliage` keyword 오류와 과거 Console 기록은 지우지 않았다.

---

## 76. 기지 단계형 로컬광 시험 배치 `[ENVIRONMENT-01]`

- `[사용자 요청·씬 배치][2026-08-30]` 기존 `PrototypeSteppedLocalLightFixture` prefab 인스턴스 1개를 기지 `GameMap1` scene root의 `(-2.5, 0, -2.5)`에 배치했다. BaseEntry와 BaseReturn 사이에서 보이되 NPC·Chest와 겹치지 않으며, prefab의 표준 Unity `Light`와 Collider 수는 모두 0이라 기존 이동·물리·조명 권위를 바꾸지 않는다.
- `[사용자 조정]` 광원 반경 4.5m와 Surface/Halo 단계 수는 유지하고 prefab 원본과 새 컴포넌트 기본 `worldCellSize`를 `0.18 → 0.12m`로 줄였다. 기지와 `GameMapTest`의 두 prefab 인스턴스가 같은 원본을 상속해 광원 기여의 월드 고정 도트 블록만 약 33% 더 촘촘해진다.
- `[Play Mode 확인]` 최종 조정 뒤 `GameMap1` 직접 Play 1회에서 scene의 활성 `SteppedLocalLight`가 정확히 1개이고 persistent gameplay Camera가 이를 renderer material에 `rendered=1`, `worldCellSize=0.12`로 전달함을 확인했다. Play 종료 뒤 `GameMap1`, Edit Mode, scene clean, compile failure 없음과 저장된 prefab 연결을 다시 확인했다.
- `[Git 경계]` `GameMap1`에는 작업 전부터 Base Chest의 새 직렬화 필드 6줄이 별도 변경으로 존재했다. 해당 기존 변경은 보존하며 이 배치의 prefab instance·SceneRoots hunk만 분리해 기록한다.

---

## 77. 기지 바닥·Grass 조명 수신 계약 수정 `[ENVIRONMENT-01]`

- `[사용자 피드백·확정 원인][2026-08-30]` 기지 단계형 로컬광은 기둥 등 일부 오브젝트에만 보이고 Ground에는 나타나지 않았다. `Small Ground`의 `AwaiiStudio/URP_ToonLit`은 Opaque·DepthOnly였지만 URP의 Depth/Normal prepass가 읽는 `DepthNormals` 패스가 없어 fullscreen 로컬광에서 배경으로 제외됐다. Grass LOD0/1은 depth-normal 패스는 있었지만 두 Shader Graph의 본체가 Unlit이었다. LOD1은 vertex 색 그라데이션만 출력했고, LOD0도 MainLight의 색·세기를 버린 채 shadow/self-shadow 값으로 색만 골라 빛이 없어도 선명하게 남았다.
- `[근본 수정·보존]` Toon Ground 셰이더에 URP Lit의 `DepthNormals` pass를 명시적으로 재사용해 원래 Forward 외관은 유지했다. Grass LOD0/1은 같은 URP Lit 표면 계약으로 바꾸고, LOD0 BaseColor에서 중복 수동 조명 가지를 제거해 원래 Bottom↔Top vertex 색을 표면색으로 넘겼다. 양면 렌더, 두 LOD mesh·전환, LOD0 vertex wind 연결과 재질 색 값은 바꾸지 않았다. 기지 인스턴스의 앞선 셀 크기 조정 `0.04m`는 유지하고 공유 prefab·GameMapTest 기본값은 `0.12m`다.
- `[Shader·Play Mode 확인]` Toon Ground, Grass LOD0, Grass LOD1은 모두 supported였고 관련 compiler error가 0이었다. 런타임의 Grass 재질 2개가 모두 `ForwardLit`과 `DepthNormals`를 제공하고 기지 Ground도 `DepthNormals`를 제공했다. 한 `GameMap1` Play Session의 같은 Camera에서 정오, 22시, 22시 로컬광 off와 환경광 0 제어 화면을 각각 비교했다. Grass는 정오에 밝고 그림자를 받았으며 22시에 어두워졌고, 환경광 0에서는 로컬광 범위 밖이 검게 사라졌다. 로컬광 on/off에서는 Ground의 단계형 원과 반경 안 Grass·오브젝트의 따뜻한 기여가 함께 나타났다.
- `[보존·Console]` Player·Camera·HUD·씬 흐름·날씨 권위·표준 Unity Light 수는 변경하지 않았다. 기존 외부 `AwaiiStudio/ASFolliage`의 중복 keyword 오류와 검증용 동적 명령 컴파일 실패 기록은 Console에서 지워 덮지 않았다. Player build, Mobile, Transparent Sprite 수광, 벽 차폐와 최종 Grass 명암 아트 조정은 미검증이다.

---

## 78. 환경 구조 감사와 비 연동 픽셀 웅덩이 `[ENVIRONMENT-01]`

- `[구조 감사][2026-08-30]` 시간·날씨는 `SkyLightingCycleController`, 비·물 튐은 `PixelRainPresentation`, 로컬광은 등록 목록과 Renderer Feature 하나가 각각 기존 권위를 유지한다. 평행 Manager·매 frame 씬 탐색·빗방울별 물리·중복 렌더 패스는 없었다. 다만 Rain의 카메라 좌표와 활성 물 튐 Transform을 `Tick`과 `beginCameraRendering`에서 같은 frame에 두 번 계산하던 경로는 최종 Camera가 확정되는 render 경계 한 곳으로 줄였다.
- `[문서 원인 수정]` 개발계획의 오래된 `기능 최소 3회 반복` 문구가 현재의 대표 흐름 1회·위험 비례 검증과 충돌하던 것을 단일 검증 계약 링크로 교체했다. GDD의 환경 절에서는 texture 크기·FPS·pool 수 같은 코드 세부 복제를 걷어내고 시각·소유권 계약만 남겼으며, 문서 역할 자체는 합치지 않았다. `CURRENT_STATE.md`는 상태 범례를 줄여 12KiB 아래 여유를 확보했다.
- `[웅덩이 구현]` Unity 공식 Production Ready Weather의 네 `RainRipple` 조합 원리를 참고하되 큰 Shader Graph 묶음을 가져오지 않았다. 프로젝트 소유 4정점 mesh·공유 transparent material·shader가 기존 `_FantasyRainIntensity`와 `_FantasyRainVisualTime`만 읽어 불규칙한 픽셀 웅덩이와 네 개의 결정론적 원형 파문을 만든다. 별도 script·Manager·Update·Collider·개별 빗방울 충돌은 추가하지 않았고 `GameMap1`에 시험 prefab 한 개만 배치했다.
- `[씬 설정 원인]` disk에는 기지 로컬광 `worldCellSize=0.04` override가 있었지만 저장되지 않은 Editor scene 메모리는 prefab 기본값 `0.12`와 override 없음으로 어긋나 있었다. 웅덩이 배치 전에 기존 `0.04` override를 serialized prefab modification으로 복구해 함께 저장했다. 로컬광은 기존 Depth/Normal 단일 pass를 유지하며 Transparent 웅덩이 자체의 직접 수광·벽 차폐·그림자는 이번 범위가 아니다.
- `[컴파일·Play Mode 호출/시각 확인]` 새 shader는 `supported=True`, compiler error 없음, prefab 연결·공유 material·4정점 mesh·씬 인스턴스 1개·Collider 0개·로컬광 override `0.04`를 확인했다. `GameMap1` Play Session 1회에서 정오 Rain 즉시 적용 시 weather/global rain이 `Rain/1`, 시각 시간이 `0→16.81`로 진행했고 Game View에서 비·표면 물 튐과 웅덩이 원형 파문을 함께 확인했다. 같은 Session에서 Clear 복귀 시 weather/global rain이 `Clear/0`으로 복원됐다. 기존 외부 `ASFolliage` keyword 오류와 과거 Console 기록은 지우지 않았으며 Player build·GPU Profiler·구름 아트 교체는 미검증이다.

---

## 79. 로컬광 알파 강도와 1픽셀 흰 웅덩이 파문 `[ENVIRONMENT-01][PIXEL-01]`

- `[진단·보존][2026-08-30]` 전체 화면 `3D Pixel Art` Renderer Feature는 계속 비활성이며, 큐브 실루엣 계단은 PC MSAA 1x·gameplay Camera AA `None` 상태가 원인이다. 로컬광은 월드 셀과 밝기 band만 단계화해 강한 대비로 계단을 더 두드러지게 했지만 기하 외곽선을 픽셀화하지 않는다. 픽셀 비·웅덩이를 함께 흐릴 수 있는 전역 AA 정책은 이번 범위에서 바꾸지 않았다.
- `[근본 수정]` `SteppedLocalLight`가 색 RGB만 전달하고 alpha를 버리던 계약을 `effective intensity = intensity × color alpha`로 수정하고, alpha 0 광원은 선택 대상에서도 제외했다. 공유 시험 광원 prefab alpha는 `1 → 0.35`로 낮아져 실제 기여가 `1.15 → 0.4025`가 되며, alpha 1인 기존·후속 광원은 이전 결과를 보존한다. 웅덩이 파문은 world pixel `0.04`에서 반폭 `0.035`였던 약 1.75픽셀 띠를 최소 반폭 `0.01`로 바꿔 총 1픽셀 폭으로 만들고 색을 흰색으로 변경했다.
- `[Play Mode 호출 확인·시각 미확인]` `GameMap1` 한 Session에서 Clear/22시와 Rain/12시 적용, 로컬광 RGBA `(1, 0.62, 0.28, 0.35)`, 실효 강도 `0.4025`, 웅덩이 색 `(1,1,1,1)`, 두께 `0.01`, world pixel `0.04`, rain intensity `1`, shader supported를 확인했다. Unity 동적 C# 컴파일은 성공했다. 최종 체감 화면 캡처는 MCP Game View의 frame-boundary 제약으로 얻지 못했으며, 해당 캡처 시도에서 생긴 도구 오류 기록은 gameplay 오류로 오인하지 않도록 Console에서 지우지 않았다.
- `[후속 사용자 조정]` 비의 가는 선보다 파문이 두껍고 동시에 많이 보여 강조되는 피드백에 따라 파문 world cell을 `0.04 → 0.01`, 실제 반폭을 `0.02 → 0.005`로 줄여 총 띠 폭을 `0.04 → 0.01 world`로 75% 축소했다. 최대 줌아웃에서 원호 일부가 픽셀 단위로 끊길 수 있는 표현은 사용자가 허용했다. 네 결정론적 채널과 수명 `0.72초`는 유지하고 interval만 `1.6 → 3초`로 늘려 평균 동시 활성 원을 `1.8 → 0.96개`로 낮췄다.
- `[Play Mode 호출 확인]` `GameMap1` Rain/12시 한 Session에서 global rain `1`, 공유 material의 world pixel `0.01`·반폭 `0.005`·interval `3`, 활성 웅덩이 Renderer 1개, shader supported를 확인했다. 현재 Game View 높이 857·ortho 5에서 가로 투영 띠 폭은 `0.857px`이며 Play 종료 전 Clear로 복원했다. 새 Manager·script·loop·renderer pass·scene 변경은 없다.

---

## 80. 가변 반경·큰 공백의 픽셀 웅덩이 파문 `[ENVIRONMENT-01][PIXEL-01]`

- `[사용자 피드백·제작 이력][2026-08-31]` 참고 효과는 모든 파문이 `0 → 동일 최대 크기`로 커지는 완전한 원이 아니라 파문마다 시작·끝 크기가 다르고, 원주에 3~5픽셀 규모의 의도적인 큰 공백과 수명별 굵기 차이가 있었다. 기존 비는 Bresenham으로 래스터화한 4채널 픽셀 텍스처, Collider 물 튐은 직접 저장된 7×4×4프레임 atlas이며 런타임 셰이더가 선을 새로 그리지 않는다. 반면 웅덩이 파문만 `거리 - 반경` 수식의 고정 `0 → 0.38`, 360도 완전한 원이었다.
- `[근본 수정]` 기존 `PixelRainPuddle` 공유 셰이더와 날씨 전역값 소유권을 유지했다. cycle·channel·웅덩이 위치만으로 고정 seed를 만들고 파문별 시작 반경을 최대치의 `16~55%`, 끝 반경을 `58~100%`에서 고른다. 같은 seed가 수명 내내 유지되는 1~3개의 큰 각도 공백을 만들며, 공백 중심은 gap 수에 따라 서로 떨어진 범위에 배치해 한쪽에 우연히 겹치지 않는다. 초반 반폭은 후반의 `1.25~1.75배`에서 시작해 픽셀 최소 반폭으로 줄고, alpha는 수명 `42%` 지점부터 점진적으로 사라진다.
- `[성능·보존]` 파문 중심의 월드 격자 양자화, 흰색, interval `3초`, duration `0.72초`, 네 채널 `max` 합성, `_FantasyRainIntensity`·`_FantasyRainVisualTime` 연동을 보존했다. 새 Texture·Manager·script·Update·Collider·개별 빗방울 물리와 scene/prefab 변경은 없다. 작은 웅덩이 fragment 안에서 고정 hash와 `atan2`만 추가했으며 비·Collider 물 튐의 renderer와 atlas는 변경하지 않았다.
- `[Shader·Play Mode 호출 확인]` Unity 강제 import 뒤 `PixelRainPuddle`은 `supported=True`, `ShaderHasError=False`, compiler error/warning/message 모두 `0`이었다. `GameMap1` 직접 Play 1회에서 Rain 즉시 적용 성공과 활성 웅덩이 Renderer 1개를 확인하고 Play를 종료했으며 Edit Mode·활성 scene·scene clean 상태가 복원됐다. MCP Scene View capture가 gameplay Camera 구도를 반영하지 않아 최종 모양의 육안 검증은 사용자 확인 대상으로 남겼다. 기존 외부 `AwaiiStudio/ASFolliage` keyword 오류와 사용자 dirty `GameMap1`·재질 2개·preview Camera prefab은 수정·저장·stage하지 않았다.

---

## 81. 실제 지붕 아래 강수 차단 시험 배치 `[ENVIRONMENT-01]`

- `[구현·권위][2026-08-31]` 기존 `RainShelterOccluder`와 영속 `PixelRainPresentation`의 512×512 최고높이 cache를 그대로 사용하고 새 Manager·빗방울별 충돌·평행 차폐 경로를 만들지 않았다. 재사용 `PrototypeRainShelterTestArea` prefab은 4×4m non-trigger 지붕 Collider 하나만 명시적으로 차폐 권위로 연결한다. 탑뷰에서 안팎을 비교할 수 있도록 지붕 Renderer는 숨기고, 물리 판정이 없는 네 개의 바닥 테두리만 표시한다.
- `[씬 배치·보존]` `GameMapTest`의 기존 보호 앵커 `UrbanLayoutProtectionAnchors/FormerRangedFixture` `(6,0,6)` 아래에 prefab 한 개를 배치했다. 이 앵커는 절차 건물로부터 이미 3.5m 보호되고 runtime 생성 root 밖에 있어 seed 재생성 때 삭제되지 않는다. `GameMap1`과 기존 사용자 dirty 재질·preview Camera는 수정하지 않았다.
- `[정적·Play Mode 호출 확인]` prefab의 명시 Collider 1개, 숨은 지붕 Renderer, Collider 없는 테두리 4개, scene instance 1개를 확인했다. `GameMapTest` 직접 Play 1회에서 Rain 적용 시 scene/등록 지붕 각각 1개, cache·shader ready, 내부 `(6,0.5,6)` 최고높이 `3.100`, 외부 `(9,0.5,6)` `-10000`으로 분리되어 지붕 아래 지면만 차단되고 지붕 위는 노출되는 조건을 확인했다. Clear 복귀 뒤 전역 비 강도는 `0`이었고 Play 종료 후 `GameMap1` clean authoring 상태로 복원했다. 실제 Game View 안팎의 최종 시각 체감은 사용자 확인 대상이다.
- `[결정 대기]` 시험 웅덩이의 최종 표현 방식과 젖음·안개·번개·식생 흔들림·빗소리 등 추가 날씨 반응은 GDD §14.1.2에 미정으로만 기록했으며 이번에는 구현하지 않았다. 실내 하늘광·태양광 감쇠도 강수 차단과 별도 계약이다.

---

## 82. 기지 강수 차단 시험 구역 배치 `[ENVIRONMENT-01]`

- `[배치·재사용][2026-08-31]` 새 차폐 코드나 prefab을 만들지 않고 기존 `PrototypeRainShelterTestArea`를 `GameMap1`의 빈 지면 `(6,0,-5)`에 root prefab instance로 한 개 배치했다. 4×4m footprint는 상자·NPC·포탈·로컬광·웅덩이를 포함한 기존 non-ground Collider와 XZ가 겹치지 않으며, 숨은 지붕 Collider와 Collider 없는 바닥 테두리 계약도 원정 시험 구역과 같다.
- `[Play Mode 호출 확인]` `GameMap1` 직접 Play 1회에서 scene/등록 지붕 각각 1개, Rain cache ready, 내부 `(6,0.5,-5)` 최고높이 `3.100`, 외부 `(9,0.5,-5)` `-10000`, Rain 강도 `1`과 Clear 복원 `0`을 확인했다. Play 종료 뒤 `GameMap1` Edit Mode·clean 상태로 복원했다. 최종 Game View 안팎 체감은 사용자 확인 대상이다.
- `[보존]` 기존 `GameMap1`의 Chest 직렬화 dirty 6줄과 사용자 dirty 재질·preview Camera prefab은 이번 배치와 분리해 유지했다. 웅덩이 최종 표현·추가 날씨 반응·실내 조명은 변경하지 않았다.

---

## 83. 쿼터뷰 지붕 투영부피 강수 차단 수정 `[ENVIRONMENT-01]`

- `[사용자 재현·확인][2026-08-31]` 기존 전체화면 빗줄기는 scene depth에서 보이는 바닥 한 점만 지붕 높이와 비교해, 높이 3.1m 지붕의 화면 투영선이 아니라 바닥 4×4 footprint만 잘라냈다. 기지 기본 카메라에서 같은 XZ의 지붕과 바닥은 화면 Y가 약 188px 어긋나므로 단순 테두리 마스크처럼 보이는 원인을 확인했다. Collider를 바닥까지 늘리는 것은 셰이더 입력을 바꾸지 않고 Player·AI 물리만 막으므로 사용하지 않았다.
- `[근본 수정]` 기존 512×512 RFloat 최고높이 캐시와 강수 소유자는 유지했다. 캐시 갱신 때 현재 최고 지붕 높이를 함께 게시하고, 실제 streak 픽셀만 보이는 표면에서 직교 카메라 방향으로 12단계 높이 필드를 검사해 지붕 윗면부터 아래 표면까지의 투영 건조 부피를 차단한다. 개별 빗방울 오브젝트·새 Manager·일반 Collider 차폐는 추가하지 않았다.
- `[물 튐 수정]` 일반 splash mask를 모든 `Ignore Raycast` 오브젝트로 넓히지 않고, 등록된 `RainShelterOccluder` Collider만 별도로 직접 Raycast 후보에 포함했다. 따라서 gameplay 조준·상호작용 레이어 계약은 유지하면서 지붕 윗면에는 물 튐이 생기고 아래 바닥 물 튐은 기존 높이 캐시로 거절된다.
- `[Play Mode 호출·렌더 확인]` `GameMap1` Rain 직접 Play 1회에서 캐시 최고높이 `3.1`, 지붕 화면점 뒤 바닥 `(5.46,0,-1.95)`은 구 방식 `False`·투영부피 `True`, 지붕 내부 바닥 `True`, 외부 `(10,0,-5)` `False`로 분리됐다. 실제 활성 물 튐 7개는 지붕 윗면 2·지붕 아래 바닥 0·야외 바닥 5였고, 전체화면 셰이더는 supported·compiler message 0이었다. Game View 캡처에서 지붕 상단 투영선부터 바닥까지 중앙 건조 영역과 외부 강수를 확인했으며, 종료 뒤 `GameMap1` Edit Mode·clean 상태를 확인했다.
- `[보존·비용]` 비 패턴·20 FPS·랜덤 위치·월드 고정·줌 식과 pool 크기는 변경하지 않았다. 12회 높이 조회는 패턴상 실제 streak인 약 `0.00336` 비율 픽셀의 조기 분기 뒤에만 실행한다. 사용자 dirty 재질·preview Camera·`GameMap1` Chest 직렬화 변경은 그대로 분리 보존했다.

---

## 84. Shadow-map 태양 빛줄기와 선택형 로컬광 기둥 `[ENVIRONMENT-01][SHELL-01][CAMERA-01]`

- `[사용자 요청·참고 원리][2026-08-31]` t3ssel8r의 참고 영상은 태양 방향에 정렬한 평행 quad 단면에서 light-space shadow map을 샘플해 광선을 만들며 raycast·ray tracing을 사용하지 않는다고 설명한다. 현재 구현은 이 핵심 원리를 따르되 실제 체적 산란을 물리적으로 적분하지 않는다. 하드 threshold·단계형 밀도·비 감쇠는 픽셀풍 경계와 날씨 반응을 위한 계약이고, 기존 방향광 Cookie 결합과 로컬광 원뿔 확장은 프로젝트 전용이다.
- `[권위·구조]` 새 시간·날씨·광원 Manager를 만들지 않았다. 영속 `SkyLightingCycleController`가 계산한 태양 색·기여·강수량을 파생 표현 전용 `StylizedLightShaftPresentation`에 전달한다. 표현기는 persistent gameplay Camera 주변의 평행 월드 단면 10개를 한 동적 mesh로 그려 주 방향광 shadow map과 Cookie를 샘플하고, 밤에는 태양 기여 0으로 생략하며 Rain 1에서는 기본 92% 감쇠한다. `StylizedLightShaftEmitter`는 기존 `SteppedLocalLight`에 명시적으로 붙인 광원만 같은 단계형 밀도의 교차 평면 원뿔로 그리므로 향후 도심 가로등 prefab이 재사용할 수 있다.
- `[근본 수정·비용 경계]` 최초 shader는 원근용 `LinearEyeDepth`만 사용해 직교 gameplay Camera에서 scene depth 차이가 0으로 접히며 광선 contribution이 사라졌다. 기존 PixelArt shader와 같은 `unity_OrthoParams` 분기로 직교에서는 `LinearDepthToEyeDepth`를 사용해 원인을 수정했다. URP에서 `MaterialPropertyBlock`이 SRP Batcher를 해제하는 경계도 피하도록 태양 1개와 설정된 로컬 표시 상한만큼(기본 8, hard cap 16)의 숨은 런타임 Material을 한 번 생성해 재사용한다. 매 frame GameObject·Material·Mesh 생성과 씬 검색·`params` 배열 할당은 없고, 로컬 mode는 태양 shadow·Cookie sampling을 분기로 건너뛴다. 로컬광은 활성 scene/영속 셸 소속·Camera 절두체·거리순으로 기본 8개까지만 한 draw씩 제출한다.
- `[카메라 연동 수정]` 태양 단면 간격과 snap 격자는 현재 줌이 아니라 `CameraZoomController.MaxOrthographicSize` 기준의 고정 월드 부피를 사용한다. 따라서 smooth zoom 중 밀도·밝기·배치가 다시 샘플링되지 않는다. 표현 `LateUpdate` 실행 순서는 `10000`으로 두어 기본 순서의 Camera 이동·줌 적용 뒤에 mesh와 절두체를 갱신한다.
- `[컴파일·Play Mode·렌더 확인]` C# 동적 컴파일 성공, shader `supported=True`·compiler message `0`, persistent prefab의 sky→presentation→shader 참조와 시험 광원 prefab의 emitter→source 참조를 확인했다. `GameMap1` 한 Play 흐름에서 Clear/정오 태양 단면과 로컬 기둥, Clear/22시 태양 광선 미출력과 로컬 기둥 유지, Rain/정오의 태양 광선 억제를 실제 Game View로 비교했다. 과장 진단값을 폐기한 뒤 최종 prefab 기본값 `sun=0.018`, `local=0.2`로 새 Play를 시작해 로컬 기둥과 기존 Surface/Halo가 함께 보이고 scene이 저장되지 않았음을 확인했다. 추가 Play 검사에서 직교 줌 `3.5→8.0` 사이 태양 mesh 40정점의 최대 이동은 `0.000000`, 로컬 Material pool은 8개였다.
- `[보존·미검증]` Player·Camera 인스턴스, 씬 흐름, 기존 Surface/Halo pass, 구름·비·웅덩이·저장 권위와 사용자 dirty `GameMap1` Chest 6줄·재질 2개·preview Camera prefab은 변경하지 않았다. 실제 도심 가로등 배치, 로컬광 shadow map·벽 차폐, transparent surface의 depth/차폐 계약, 다수 광원 GPU Profiler, Player build와 최종 빛줄기 아트 수치는 후속이다. 검증용 즉시 ScreenCapture와 동적 검사 실패 기록 및 기존 외부 `ASFolliage` 오류는 원인을 구분했으며 Console을 지워 덮지 않았다.

---

## 85. 전용 야간 Spot 가로등 프로토타입 `[ENVIRONMENT-01][SHELL-01][CAMERA-01]`

- `[사용자 정정·배치][2026-08-31]` 일반 구형 시험 로컬광에는 빛기둥이 필요 없다는 피드백에 따라 공유 `PrototypeSteppedLocalLightFixture`에서 emitter만 제거해 기존 Surface/Halo는 보존했다. 전용 회색상자 `PrototypeStreetLamp`를 만들고 clean `GameMapTest`의 보호 앵커 `FormerMeleeFixture` `(0,0,3)`에서 기존 일반광 시험 인스턴스만 교체했다. 사용자 dirty `GameMap1`은 열어 저장하지 않았다.
- `[권위·표현]` 새 시계·날씨·조명 Manager를 만들지 않았다. 영속 `SkyLightingCycleController`가 달빛 기여에서 연속 야간값을 한 번 계산하고, 각 `NightActivatedStreetLamp`가 그 event를 받아 같은 값으로 하향 URP Spot Light, 발광 렌즈와 카메라 facing 단계형 후광을 함께 쓴다. Spot은 24 Candela, 62도, 단계형 Cookie, Soft shadow의 medium tier이고 렌즈·후광은 전역 Bloom을 켜지 않는 개별 `MaterialPropertyBlock` 표현이다. 짧은 단일 trapezoid 기둥만 전용 prefab에 opt-in하며 비에는 산란 강도만 소폭 올라간다.
- `[컴파일·Play Mode 호출 확인]` C# 동적 컴파일과 lens·halo·shaft shader 지원을 확인했다. `GameMapTest` 한 Session에서 12시 `visibility/intensity=0/0`, 18시 `0.316/7.59`, 19·22시 `1/24`, 6시 `0.316/7.59`, 8시 `0/0`이었고 Spot·렌즈·후광 값이 각 sample에서 일치했다. Rain/22시에도 24 Candela와 점등이 유지됐으며 Spot·Cookie·Soft shadow·URP 추가광 데이터·medium shadow tier·하향 정렬을 확인했다. 종료 뒤 `GameMap1` Edit Mode·clean authoring 상태로 복귀했다.
- `[현재 경계]` MCP Scene View 캡처가 변경한 gameplay 구도를 반영하지 않아 최종 화면 체감은 사용자 확인 대상이다. Spot 수광은 Lit 계열 바닥·건물용이며 외부 unlit 재질까지 보장하지 않는다. 대기 기둥은 opaque depth에는 가려지지만 Spot의 additional-light shadow atlas를 직접 샘플하지 않는다. 현재 시험 1개에는 허용하되, 도심 다수 배치 전 가까운 1~2개만 실시간 그림자를 쓰는 shadow LOD와 GPU Profiler 검증이 필요하다. 기존 외부 `ASFolliage` keyword 오류와 검증 도구 실패 기록은 Console에서 지우지 않았다.

---

## 86. 기지 전용 가로등 시험 배치 `[ENVIRONMENT-01]`

- `[배치·보존][2026-08-31]` 기존 `PrototypeStreetLamp` prefab을 재사용해 `GameMap1` Ground 위 빈 위치 `(5,0,0)`에 `PrototypeStreetLamp_Base` 1개를 배치했다. Pole collider는 기존 NPC·상자·포탈·시험 지붕과 겹치지 않는다. 비교용 구형 로컬광과 사용자 dirty Chest 직렬화 6줄·재질 2개·preview Camera prefab은 그대로 보존했다.
- `[Play Mode 호출 확인]` `GameMap1` 한 Session에서 가로등 instance 1개, Clear/22시 야간값 `1`, Spot `enabled`, 광량 `24 Candela`를 확인했다. 기존 구형 로컬광은 1개이고 shaft emitter는 0개였다. 종료 뒤 `GameMap1` Edit Mode·scene clean·컴파일 정지 상태로 복원했다.

---

## 87. 가로등 빛줄기 360도 체적 보정 `[ENVIRONMENT-01][CAMERA-01]`

- `[원인][2026-08-31]` 로컬 가로등 줄기는 정점 4개의 사다리꼴 한 장을 매 frame Camera 방향으로 회전시키는 billboard였다. 실제 beam texture도 없고 UV 가장자리·월드셀 hash만 사용했으며, 공통 하단 fade가 길이의 마지막 18%를 바닥 전에 지워 원형 Spot 수광과 분리된 물체처럼 보였다. 태양의 다중 투영 slice 구조와 달리 로컬만 단일 평면으로 축약된 것이 직접 원인이었다.
- `[수정]` Spot/Cookie 밝은 중심부와 맞던 기존 원뿔 반경은 보존했다. 로컬 mesh 하나 안에 원형 단면을 수학적으로 채우는 9개 view-aligned depth slice를 만들고 기여도를 slice 수로 정규화했다. Camera가 돌아도 slice 표본만 재정렬되고 원뿔 외피·광원 중심은 월드에 유지된다. 로컬 하단 UV fade는 제거하고 기존 scene depth fade가 실제 표면 접촉만 처리한다. 두 씬은 같은 `PrototypeStreetLamp` prefab과 영속 표현기를 사용하므로 씬·prefab 복제 변경은 없다.
- `[Play Mode 시각 확인]` `GameMap1`, Clear/22시에서 runtime local mesh `36 vertices / 18 triangles`, Spot 점등과 shader support·compile message 0을 확인했다. gameplay Camera를 런타임에서만 0°·90°·180°·270°로 돌려 직접 RenderTexture 캡처한 결과 네 방향 모두 렌즈 아래 중심과 지면 수광 중심을 유지하고 edge-on 소실·평면 flip·공중 조기 단절이 없었다. 종료 뒤 `GameMap1` Edit Mode·scene clean·컴파일 정지 상태로 복원했다. 잘못된 Entity ID로 시도한 MCP Camera Capture 1회 오류는 기능 오류와 분리했고, 후속 직접 Camera render는 정상 완료했다. 기존 외부 `ASFolliage` shader 오류는 그대로 남아 있다.

---

## 88. 가로등 연속 체적 단일산란 렌더링 `[ENVIRONMENT-01][CAMERA-01]`

- `[사용자 정정·원인][2026-08-31]` §87의 9개 camera-facing slice는 단일 billboard 소실은 막았지만 시점에 따라 겹친 투명 판과 명확한 선으로 보였다. 픽셀 스타일을 먼저 맞추는 문제가 아니라 로컬 체적광 자체가 연속 공간을 계산하지 않은 구조가 직접 원인이므로, slice 수·텍스처·불투명도 보정으로 덮지 않았다.
- `[근본 수정]` PC URP Renderer에 gameplay Camera 전용 전체화면 RenderGraph pass를 하나 추가했다. pass는 활성 `StylizedLightShaftEmitter`의 실제 Spot Light `range`·outer angle에서 유한 원뿔을 만들고, 직교 Camera의 near/far world ray와 수학적으로 교차한 구간만 opaque scene depth까지 24개 midpoint로 적분한다. 매 표본은 URP가 packing한 동일 additional-light index로 원래 Light의 거리·inner/outer angle 감쇠, Cookie와 실시간 soft shadow를 읽으며, HG 위상함수와 Camera 경로·광원 경로 양쪽 Beer–Lambert 감쇠를 적용한다. 누적 투과율이 `0.001` 미만이면 조기 종료한다.
- `[구조 정리]` 기존 시간·날씨·가로등 점등 권위와 공유 `PrototypeStreetLamp` prefab은 유지했다. emitter는 별도 길이·반경·pixel band·cell noise 복사값을 버리고 원래 Light 기하와 매질 산란·소광·비등방성만 소유한다. `StylizedLightShaftPresentation`은 태양 단면과 로컬 표시 상한·비 산란 배율만 제공하고, 사용되지 않는 로컬 mesh/material pool과 공용 shader의 local 분기를 제거했다. Renderer feature subasset map도 실제 5개 feature local ID와 동기화했다.
- `[Unity 컴파일·Play Mode·렌더 확인]` C# compile 성공, 태양·로컬 체적 shader 모두 `supported=True`·compiler message `0`을 확인했다. `GameMap1` Clear/22시에서 Camera yaw `0/90/180/270°`, 직교 size `3.5/5.5/8.0`을 각각 직접 RenderTexture로 확인해 등기구·바닥 Spot 중심의 월드 고정, 회전 시 edge-on 소실 없음, 줌 비례, opaque depth 접촉과 Spot shadow를 확인했다. 같은 prefab을 쓰는 `GameMapTest`도 Clear/22시·24 Candela 기본 시점에서 연속 원뿔과 바닥광을 확인한 뒤 `GameMap1` Edit Mode·scene clean으로 복원했다.
- `[보존·경계]` 태양 광선·단계형 Surface/Halo·낮밤·구름·비·Player 셸·씬·저장 schema는 바꾸지 않았고 사용자 dirty 재질 2개·preview Camera prefab·`GameMap1` Chest 직렬화 6줄을 stage 대상에서 분리했다. 로컬 체적에는 pixel quantization·animated jitter·blur·temporal history를 넣지 않았다. 현재 full-resolution 비용은 보이는 원뿔 픽셀마다 최대 24회 soft shadow/Cookie 표본이므로 도심 다수 배치 전 GPU Profiler와 screen bound 또는 shadow 표본 분리 검증이 필요하다. Transparent가 체적을 차폐·수광하는 합성, 전역 fog·multiple scattering·Player build는 미검증이다. Console의 기존 외부 `AwaiiStudio/ASFolliage` keyword 중복 오류는 이번 shader 오류와 분리해 그대로 두었다.

---

## 89. 단일 ItemDatabase 아이템 저작 도구 `[ITEM-01]`

- `[구현·권위][2026-08-31]` `Tools/Fantasy Survival/Content/Items`가 기존 `ItemDefinition` asset과 단일 `ItemDatabase`만 편집한다. 자동 ID, 생성·복제·기존 asset 등록, 검색·분류, kind·slot 조건부 Inspector와 project/DB 검증을 제공하며 별도 메모·DB, runtime Inventory, Save schema와 게임 UI는 만들거나 변경하지 않았다. 사람의 창과 AI `RunCommand`는 같은 `ItemContentAuthoringService`를 사용한다.
- `[ID·트랜잭션]` DB가 다음 ID high-watermark를 영구 소유하고 생성 전에 전진·저장하므로 실패하거나 삭제된 ID도 재사용하지 않는다. 새 asset 생성·복제는 즉시 저장되고 Ctrl+Z 대상이 아니며, 실패 시 DB 목록·검증 index와 생성 파일을 각각 복원·삭제하고 cleanup 실패까지 원래 오류와 함께 보고한다. 기존 asset 편집과 DB 등록은 `SerializedObject`/Undo 경로를 유지한다.
- `[Unity Editor 호출 확인]` C# compile, 실제 창 제목·최소 크기, production definition/등록 `9/9`, blocker `0`, presentation warning `6`, 다음 ID `10`을 확인했다. 격리 임시 DB 생성 1건은 ID `10`, DB 등록, `TryGet` 동일 참조와 allocator `11`을 확인했고 asset 삭제 뒤 DB가 비어 있어도 다음 ID가 `11`로 유지됨을 확인한 뒤 임시 folder와 `.meta`를 제거했다. 미등록 탄약 ID의 무기 요청은 DB·allocator 변경 전에 거부됨도 확인했다.
- `[보존·경계]` 사용자 dirty `GameMap1`, Quest/상인 재질과 preview Camera prefab은 변경·stage하지 않았다. 현재 9개 규모에는 ScriptableObject+공용 service+IMGUI 창이 적합하며, 수백 개 평면 수치의 외부 협업 전에는 CSV/Sheets 이중 권위를, 원격 배포 전에는 Addressables를 추가하지 않는다. 기존 asset 편집·등록 Undo는 코드 확인이며 실제 Ctrl+Z/Redo는 미검증이다. 기존 외부 `ASFolliage` 오류와 과거 검증 도구 Console 오류는 이번 기능과 분리했다.

---

## 90. 가방 추가 행·자동 재배치와 픽셀 파츠 기술 기반 `[ITEM-01]`

- `[구현·권위][2026-08-31]` `ItemDefinition.BackpackBonusRows`와 기존 Backpack 장비칸을 연결했다. Player root 인벤토리 인스턴스와 기본 `8×9` 권위는 유지하고 장착 가방의 행만 아래에 추가한다. 해제 시 기존 위치 유지→원회전 우선 결정적 재배치→필요할 때 회전→제한된 exact 탐색 순으로 기본 grid 수용 여부를 계산하며, 불가능하면 장비·높이·셀·회전·소유권을 전혀 확정하지 않는다.
- `[교체·거래·복구]` 큰 가방으로 직접 교체하면 새 용량을 먼저 확정하고 기존 가방을 Player grid에 넣는다. 같거나 작은 가방은 직접 교체를 차단한다. 가방 pick 취소, 목적지 실패, 판매 대금 실패와 기존 가방 보관 실패는 receipt로 원래 셀·회전까지 CAS 복구한다. 상인↔장비칸 직접 drag는 결제 뒤 복구 경계가 없으므로 차단하고 빠른 판매/Player grid 구매만 쓴다. 바닥 아이템 시각화·월드 드롭은 이 작업에서 만들지 않았다.
- `[저장·시험 콘텐츠]` 일반 save·primary backup·Raid checkpoint/rollback은 저장된 Backpack record에서 실제 높이를 `기본 높이 + 추가 행`으로 다시 계산해 payload 크기와 일치할 때만 복원한다. 빨강 ID 10 `+1`, 초록 ID 11 `+2`, 파랑 ID 12 `+3`의 1×1 시험 가방과 Point-filtered 색상 아이콘을 단일 DB에 등록하고 시작 인벤토리에 넣었다. 시험 판매가는 은화 1이며 정식 수치·가격이 아니다. 기존 production 가방 definition이 없었으므로 과거 save migration 대상은 없지만, 이후 같은 ID의 추가 행을 변경할 때는 migration이 필요하다.
- `[픽셀 모딩 기술 기반]` 실제 아트 없이 `ModularSpriteRigDefinition`, `MotionDefinition`, `SkinDefinition`과 정수 pixel-snap FK solver를 분리했다. 8방향 hysteresis, 고정 FPS frame, 관절 덮개와 방향별 render order를 검증하지만 Renderer·Player/Enemy prefab·실제 파츠 이미지는 아직 연결하지 않았다.
- `[Unity Editor 호출 확인]` C# compile 뒤 Backpack 계약 검증에서 추가 행, 동일 root 인스턴스, 자동 재배치, 73개 item의 해제·판매 차단 완전 불변, receipt 원복, 큰 가방 교체와 기존 가방 보관, 작은 가방 차단, 보관 불가 교체 rollback, discard 기본 높이 복귀와 base/expanded save 왕복을 확인했다. production DB `12/12`, 가방 ID·행·아이콘·시험 거래값, persistent prefab의 status Text와 시작 ID를 확인했고 Modular Sprite·Core adjacent validator도 예외 없이 통과했다. 실제 Play Mode UI drag·상인 조작과 Player build는 미검증이다.

---

## 91. 바닥 아이템 드롭과 공용 E 습득 `[ITEM-01][INTERACT-01]`

- `[구현·권위][2026-08-31]` Player 소유 일반 pointer drag만 전체화면 Player 인벤토리 Canvas 뒤의 투명 DropZone에서 받는다. 실제 grid·장비·상인 UI Rect는 좌표 하드코딩 없이 제외하며, 잘못된 셀·click-carry·분할 carry·외부 Chest/상인 item은 기존 원복 경로를 유지한다. 성공 시 같은 `InventoryItemData`가 footprint 크기의 scene-local owner로 원자 이전되고 작은 색상 Trigger 구가 활성화된다.
- `[습득]` 바닥 구는 별도 입력 polling 없이 기존 `PlayerInteractor`의 최근접 E 후보가 된다. `InventoryTransferCoordinator`는 Storage Shift 이동의 stack 우선·첫 유효 빈칸 트랜잭션을 재사용해 부분 습득 잔량을 같은 바닥 owner에 남기며, 비중첩 item도 기존 first-fit을 사용한다. 드래그 중 E 습득은 임시 빈칸과 원복 충돌을 막기 위해 차단한다.
- `[Unity Editor 호출 확인]` C# compile과 persistent prefab의 실제 Player/External Canvas·Stash 계층을 확인했다. 임시 runtime item으로 stage→rollback 동일 참조·owner 해제, `8/10 + 바닥 5`에서 기존 stack `10/10` 우선·바닥 잔량 3, 빈칸 해제 뒤 같은 잔량 item이 slot 1로 이동하는 계약을 한 번 검증했다. 실제 마우스 drag·물리 E 입력과 Game View 구 표현은 미검증이다.
- `[현재 경계]` 작은 구는 텍스처 전 시험 표현이다. 바닥 entity는 ordinary save와 원정 Recovery에 아직 기록되지 않으므로 씬 전환·강제종료 영속성을 보장하지 않는다. 정식 sprite·드롭 위치 정책·저장 record는 후속이다.

---

## 92. 가방 교체 미리보기 재배치 정정 `[ITEM-01]`

- `[사용자 정정·규칙][2026-08-31]` §90의 같거나 작은 가방 직접 교체 차단을 폐기했다. 교체로 잃는 행을 제외한 목표 grid에 현재 root 아이템과 벗는 가방까지 실제로 모두 배치되는지가 유일한 판정이다. 이는 `+2` 가방 제거 시 현재 확장 grid에 폭 전체의 가상 1행 두 개를 예약하는 계산과 동치다.
- `[구현·원자성]` 먼저 현재 셀·회전을 유지한 채 벗는 가방 자리까지 찾는다. 그대로 들어가면 기존 item을 움직이지 않는다. 실패할 때만 기존 결정적 greedy→회전 포함 제한 exact 탐색으로 새 배치를 메모리에서 완성하고, 성공한 계획만 적용한다. 계획 실패·탐색 한도 도달·후속 장비 교체 실패에는 미리보기 결과를 버리고 높이·셀·회전·owner·장비와 교체 가방 source를 그대로 복구한다.
- `[Unity Editor 호출 확인]` 강제 synchronous refresh와 C# compile 뒤 Backpack 계약 검증을 실행했다. 큰→작은 교체의 기존 배치 유지, 같은 용량 교체, 2×2 기존 가방 자리가 없는 checkerboard에서 미리보기 재배치 후 성공, 기존 가방까지 합산하면 면적 초과인 교체의 완전 불변, 작은 가방 상태 Save 왕복이 모두 통과했다. 실제 마우스 drag와 Player build는 미검증이다.

---

## 93. 가방 drag 해제 지연과 목적칸 포함 미리계산 `[ITEM-01]`

- `[사용자 확정·동작]` 가방은 drag 시작 순간 해제하지 않는다. 슬롯 그림만 ghost로 들고 장비·추가 행·root grid·owner를 유지한다. hover한 실제 목적칸에 가방 footprint를 먼저 예약한 가상 grid가 성공하면 초록, 실패하면 빈칸이어도 빨강이며, drop 순간 재검사를 통과할 때만 같은 runtime 가방을 옮긴다.
- `[구현·원자성]` `StandardStashViewData`의 순수 height plan이 기존 셀 유지→결정적 greedy→회전 포함 제한 exact 탐색을 메모리에서 수행한다. 목적칸·회전을 고정한 예약 API, 현재 셀/회전/footprint/owner를 재검사하는 apply, rollback receipt와 `LayoutVersion`을 공유한다. 미리보기 cache는 Player root와 목적 grid의 version이 바뀌면 폐기한다. 다른 보관함·바닥 drop은 무알림 staged take→목적지 완료→한 번 publish 순서이며, 외부 receipt commit 전 publish invariant를 준비해 commit 뒤 알림 확정이 실패하지 않게 했다.
- `[Unity Editor 호출 확인][2026-08-31]` C# compile과 Backpack 계약 검증을 실행했다. 성공/실패 미리보기의 높이·모든 셀·회전·owner·장비·dirty·layout version 무변경, 정확한 목적칸 commit, 73개 item의 실패 원자성, 장비 슬롯 UI ghost/취소 복원, 작은 가방 교체 시 기존 가방 공간 합산, staged rollback 무알림과 외부 목적지 완료 뒤 장비/용량 알림 각 1회를 확인했다. 이어 `CoreSystemsAdjacentValidation`도 1회 통과해 함께 닿는 기존 장비·저장·입력 계약의 회귀가 없음을 확인했다.
- `[Play Mode 호출 확인][2026-08-31]` dirty `GameMap1`을 저장하지 않고 임시 Player state로 실제 `StandardCore` pointer drag callback을 호출했다. `+1` 가방과 root item 72개 상태에서 비어 있는 base slot 71은 drag가 시작되면서도 빨강이었고 drop 뒤 장비·10행·owner·layout version·슬롯 UI가 정확히 유지됐다. item 1개 상태의 base slot 0은 초록이었고 drop 순간 같은 가방 instance가 slot 0으로 이동하며 9행으로 축소됐다. 초기 결합 검증기의 두 번째 fixture 재개방 누락 오류는 기능과 분리해 수정한 뒤 두 case를 각각 성공 호출했으며 Console을 지우지 않았다. 종료 뒤 `GameMap1`의 기존 dirty 상태와 Edit Mode를 복원했다.
- `[조건부 대안·현재 경계]` 미리계산 drag가 이후 실제 UI 복잡성이나 불안정성을 만들면 자동정렬을 폐기하고, 사라지는 추가 행에 footprint가 일부라도 걸친 item만 모두 바닥 drop하며 기본 8×9 item은 움직이지 않는 방식으로 전환한다. 현재는 전환하지 않았다. 시험 가방은 모두 1×1이며 장착 가방 drag 중 별도 ghost 회전은 이번 범위에서 추가하지 않았다. 실제 사람 손의 물리 마우스 조작과 Player build는 미검증이다.

---

## 94. 대소 분리형 구름 그림자 실루엣 `[ENVIRONMENT-01]`

- `[사용자 피드백·원인][2026-08-31]` 기존 64×64 Cookie는 회색 감광 영역이 타일 대부분에서 하나로 이어지고 흰 틈만 뚫린 구조여서, 지면에서는 구름 여러 개가 아니라 큰 산등성이 한 장처럼 읽혔다.
- `[수정·보존]` 같은 `PixelCloudShadowCookie` GUID와 64×64·2픽셀 셀·4단계 투과도·Repeat/Trilinear/Mipmap 계약은 유지하고, 흰 여백으로 완전히 분리된 크기 차이의 군집 7개로 실루엣만 교체했다. `SkyLightingCycleController`, 하늘광·낮밤 곡선, Directional Light 투영·서→동 이동, Clear/Rain 결합과 수신 shader는 변경하지 않았다.
- `[정적·Play Mode 시각 확인]` 원본 PNG는 그림자 1,052/4,096 pixel(25.7%), 4방향 연결요소 7개, 최소/최대 군집 64/264 pixel이고 타일 네 경계의 그림자 pixel은 0개였다. dirty `GameMap1`을 저장하지 않은 한 Play Session에서 Clear/정오를 적용해 영속 controller·runtime filtered Cookie 바인딩과 실제 게임 Camera를 확인했으며, 큰·중간·작은 음영 사이로 밝은 바닥이 분리되어 기존 연속 산등성이가 사라진 것을 렌더로 확인했다. 종료 뒤 Edit Mode와 기존 scene dirty 상태를 보존했다. PNG 재import 때 기존 외부 `AwaiiStudio/ASFolliage` keyword 중복 오류가 다시 출력됐지만 이번 Cookie·게임 코드 오류는 아니다.

---

## 95. 3개 저장 슬롯·Active Raid 주메뉴 저장과 바닥 아이템 Recovery `[BOOT-01][ITEM-01][RAID-01][SAVE-01]`

- `[사용자 확정·슬롯 권위][2026-09-01]` New/Load는 3개 슬롯 중 하나를 고르며 `PersistentGameplayShell.ActiveSaveSlotIndex`가 현재 gameplay session의 ordinary와 Recovery namespace를 함께 선택한다. 슬롯 1은 기존 경로를 유지하고 슬롯 2·3은 독립 경로를 쓴다. New는 선택 슬롯만 확인 후 clean 상태로 교체하고, Base 저장·출발·정산·Resume·cleanup도 active slot 밖을 변경하지 않는다.
- `[Active Raid 주메뉴]` 원정 Escape의 `주 메뉴`를 명시적 `원정 포기`와 분리했다. 먼저 world exact Active checkpoint를 기록하고 그 checkpoint의 persistent state를 같은 ordinary slot primary/backup에 mirror한 뒤에만 주 메뉴로 나간다. 실패하면 원정에 남고 성공해도 `Abandoned` 결과·정산을 만들지 않으므로 같은 슬롯에서 이어하기 또는 실패 처리를 선택한다.
- `[바닥 item 수명·복원]` 바닥 item의 GameObject와 단일-item grid owner는 scene-local이며 일반 씬 전환에 따라 제거된다. 따라서 기지에 놓고 출발한 item은 사라진다. Active Raid Recovery v2만 GUID stable ID·Transform·정확한 회전 footprint grid를 저장하며 Resume에서 비활성 staging→전체 상태 적용→일괄 활성화 순으로 복원한다. ordinary save에는 바닥 entity를 넣지 않고 이전 v1 checkpoint는 빈 바닥 목록으로만 호환한다.
- `[정적·Editor 검증]` C# compile 성공 뒤 core 인접 검증에서 3슬롯 primary/backup 값 격리, slot 1 legacy 경로, 슬롯별 Recovery 경로, world-item v2 왕복·개수 불일치 거부·v1 빈 목록 호환을 확인했다. Main Menu runtime 슬롯 버튼 3개의 비중첩 배치와 같은 runtime item의 바닥 stage/commit·stable ID·scene owner도 확인했다. 최종 감사에서 ordinary는 없고 Recovery만 남은 슬롯 행이 비활성인 경계를 찾아, 그 행만 선택 가능하게 해 기존 marker-first 격리 경로로 보내고 ordinary-only 손상 슬롯은 계속 차단하도록 고쳤다.
- `[실제 Play Mode 흐름]` 사용자 dirty `GameMap1`을 저장하지 않고 슬롯 2로 실제 `GameMapTest` 원정을 시작해 바닥 item 하나를 확정한 뒤 `주 메뉴` 저장·종료와 Main Menu의 `Load → Slot 2 → 이어하기`를 실행했다. slot 2 ordinary marker와 Recovery에 같은 stable ID가 기록되고 slot 1·3에는 자료가 생기지 않았으며, 복귀한 `GameMapTest`에서 같은 stable ID의 바닥 item이 재구성됐다. 무인 대기 중 기존 적 AI가 Player를 사망시킨 것은 관찰됐으나 저장 시점의 Active checkpoint·메뉴 이동·바닥 item 복원과 `Abandonments=0`은 확인됐다. Play 종료 뒤 기존 `GameMap1` dirty 상태를 보존했고 기존 외부 shader Console 오류는 지우지 않았다.

---

## 96. 3D 마네킹 합성 실루엣 외곽선 시험 `[CHARACTER-RENDER-01]`

- `[사용자 오류·근본 원인][2026-09-02]` 설치가 끝난 임시 `[InitializeOnLoad]` 제작기가 Play Mode domain reload에서도 다시 실행되어 `EditorSceneManager.NewScene()`을 호출한 것이 빨간 `InvalidOperationException`의 원인이었다. 제작기는 결과 에셋 생성 뒤 남아 있을 런타임 책임이 없으므로 제거했고, 재컴파일 뒤 같은 예외가 다시 발생하지 않았다.
- `[구현·격리]` 프로젝트에 이미 포함된 CC0 Kenney `characterMedium.fbx`를 원본 수정 없이 재사용했다. 우윳빛 단색 Unlit 재질, 전용 rendering-layer bit만 기록하는 R8 mask, 원본 색을 저해상도로 내리지 않는 화면공간 계단 외곽선 합성, 재사용 prefab과 독립 `CharacterSilhouetteTest` scene을 추가했다. 게임플레이 물리 Layer·Player·Camera·씬에는 연결하지 않았다.
- `[수명·비용 경계]` `CharacterSilhouetteSubject` 한 종류가 활성 대상 수와 전용 bit를 소유하며 비활성화·계층 이탈 시 자신이 붙인 bit를 해제한다. Renderer Feature는 Game Camera와 유효 재질을 확인하고, Play Mode에서는 활성 대상이 없으면 mask/composite pass를 제출하지 않는다. 최종 Player 파츠·Character ID·균일 조명 합성은 아직 연결하지 않았다.
- `[Unity Editor 렌더·정적 확인]` Unity 6.5/URP 17.5에서 전체 생성물 import와 강제 동기 컴파일이 성공했고 shader compile 오류가 없었다. 격리 카메라 960×540 직접 렌더에서 검은 외곽선 4,482픽셀을 측정해 단색 내부와 계단형 총외곽선을 확인했다. 수명주기 정리 뒤 최종 C#도 Unity 강제 refresh와 같은 Unity/URP 어셈블리 독립 컴파일을 모두 통과했다. 실제 Player Play 연결과 Player build는 미검증이다.
- `[보존]` 사용자 dirty `GameMap1`, 의뢰/상인 재질과 preview Camera prefab은 저장·stage하지 않았다. Blender·외부 다운로드·새 입력·Manager·조명 권위는 추가하지 않았다.

---

## 97. 기지 실루엣 마네킹 시험 배치 `[CHARACTER-RENDER-01]`

- `[배치][2026-09-02]` 기존 `CharacterSilhouetteMannequin` prefab을 `GameMap1`의 `(-6,0,2)`에 `CharacterSilhouetteMannequin_BaseTest`로 1개 배치했다. Collider 없는 표현 전용 scene instance이며 Player 셸·외형·Animator·이동은 바꾸지 않았다.
- `[Play Mode 시각 확인]` `GameMap1` 직접 Play 1회에서 활성 subject 1개, prefab 연결, Renderer 1개·Collider 0개와 전용 rendering layer를 확인했다. 실제 gameplay Camera 렌더에서 우윳빛 단색 몸체와 검은 계단형 총외곽선이 전부 화면 안에 표시됐고 종료 뒤 Edit Mode로 복귀했다.
- `[보존·경계]` 기존 Chest 직렬화 6줄과 의뢰/상인 재질·preview Camera prefab 변경은 보존했다. 현재 마네킹은 비교용이며 실제 Player 교체·파츠·Character ID·균일 조명 합성은 후속이다. 기존 외부 `ASFolliage` 오류와 검증 Camera tool의 잘못된 ID 오류 기록은 지우지 않았다.

---

## 98. 실루엣 외곽선 안쪽 1픽셀 겹침 `[CHARACTER-RENDER-01]`

- `[원인][2026-09-02]` 기존 합성은 아트 셀 중앙 한 점으로 점유를 정한 뒤 빈 이웃 셀만 외곽선으로 그렸다. 몸체가 점유 셀 중간에서 끝나면 같은 셀의 나머지 1~2 화면 픽셀이 배경으로 남아 몸체와 검은 선 사이에 미세 여백이 생겼다. R8 binary mask·MSAA 1이므로 threshold 조정 문제가 아니었다.
- `[수정]` 기존 3×3 셀 dilation 외피는 유지하고, 그 외피 안에서 full-resolution mask를 상하좌우 1픽셀 침식한 내부만 제외해 외곽선을 합성한다. 따라서 경계 셀의 빈 부분을 메우고 몸체 안으로 정확히 1픽셀 겹치며, 대각선까지 침식해 선을 과도하게 굵게 만들지 않는다. 외피 밖 픽셀은 조기 반환하고 재질의 `_InnerOverlapPixels=1`로 명시했다.
- `[Play Mode·픽셀 확인]` `GameMap1` 한 Play에서 shader `supported=True`·compiler message 0을 확인했다. 동일 1280×720 gameplay Camera 캡처에서 보이는 몸체 경계의 외곽선 거리 2픽셀 이상이 `344/1,228 → 0/1,224`, 거리 1 접촉률이 100%가 됐다. 전후 합성 bbox `x=93~354, y=12~239`와 모든 행·열 외피는 동일해 바깥 계단 형태의 변화는 0픽셀이었다. 종료 뒤 Edit Mode·scene clean을 확인했고 기존 외부 `ASFolliage` 오류는 분리했다.

---

## 99. 실루엣 평행이동 픽셀 크리프 제거 `[CHARACTER-RENDER-01]`

- `[원인][2026-09-02]` full-resolution binary mask를 화면 원점 기준의 `floor(screen/3)` 격자 중앙에서만 표본화해, 연속 이동 중 셀 전체가 다시 분류되고 있었다. 1280픽셀 폭은 3으로 나누어떨어지지 않아 UV 재확장 셀도 불균일했다. 앞선 1픽셀 안쪽 겹침은 여백만 해결하며 이 시간축 위상 문제는 해결하지 못했다.
- `[근본 수정]` gameplay Transform은 연속으로 유지하고 물리 없는 presentation root만 URP `beginCameraRendering`에서 실제 내부 render 1픽셀 중심에 맞춘 뒤 `endCameraRendering`에서 원위치로 복원한다. 자식 Renderer는 공통 MPB anchor를 공유한다. RG8 raw/seed 2패스와 R8 expansion으로 object anchor 기준 1픽셀 seed를 정확한 3×3 블록으로 확장하고, composite는 `SV_POSITION`·`LOAD_TEXTURE2D` 정수 좌표만 사용한다. 기존 1픽셀 inward overlap·3픽셀 외곽선과 단일 shared Renderer Feature는 유지했다.
- `[Play Mode·정량 확인]` `GameMap1`, 1280×720에서 카메라 기준 0.25픽셀씩 13프레임·총 3픽셀을 이동했다. 몸체∪외곽선 픽셀 수는 17,667로 고정됐고 정수 이동 정렬 뒤 최악 XOR 0.000%, 역방향·형상 변화 0, render 뒤 root 복원 오차 0이었다. mask/composite shader compiler message 0, 종료 뒤 Edit Mode·scene clean과 최종 수정 이후 신규 관련 Console error 0을 확인했다. 기존 `ASFolliage` 오류와 수정 전 transient error는 분리했다.
- `[경계]` 이번 결과는 평행이동 안정화다. Player 교체, Character ID, 파츠, 균일 조명, continuous rotation·skinned animation·smooth zoom 안정화는 아직 구현하지 않았다.

---

## 100. 영속 Player 실루엣 마네킹 외형 연결 `[SHELL-01][MOVE-01][CHARACTER-RENDER-01]`

- `[구현][2026-09-02]` `PersistentGameplayShell/Player`와 그 fileID·Transform은 유지하고 기존 Freya nested 외형만 `CharacterSilhouetteMannequin` nested prefab으로 교체했다. 표현 wrapper `CharacterSilhouettePlayerVisual`은 Player local `(0,-0.5,0)`, Collider 없음이며 `CharacterSilhouetteSubject`의 render-time snap은 이 wrapper만 움직인다.
- `[Animator 연결]` 유효한 Humanoid `characterMediumAvatar`에 기존 `PlayerLocomotion.controller`를 instance override로 연결하고 root motion을 껐다. `PlayerMovement`와 `PlayerWeaponController`의 `characterAnimator`는 같은 새 Animator를 가리킨다. 교체 도중 샘플링된 불필요한 descendant bone rotation override 4개는 제거했으며 최종 descendant Transform override는 0개다.
- `[보존·직렬화 확인]` Player local y=0.5, BoxCollider·상호작용 SphereCollider 2개, `WeaponRayOrigin (0,2,0)`, Camera·HUD·Inventory와 게임 규칙 코드는 바꾸지 않았다. prefab Missing Script 0, 기존 Freya 계층 0, 새 Player subject 1·SkinnedMeshRenderer 1이다. 사용자 변경이 섞인 `GameMap1`과 독립 시험 mannequin은 저장하지 않았다.
- `[Play Mode 확인]` `GameMap1`에서 새 Animator initialized/human, 기존 controller·무기 layer를 확인했고 Run 값 1.3을 표본화했을 때 발 bone 자세가 25.56° 변해 Humanoid retarget을 확인했다. 격리 카메라 렌더는 몸체 4,392픽셀·검은 외곽 1,690픽셀, render 뒤 wrapper 복원 오차 0이었다. `GameMap1 → GameMapTest → GameMap1` 한 왕복에서 Shell·Player·Camera·Animator Entity ID가 모두 같았고 Shell·PlayerMovement·Player subject는 각각 1개였다. 종료 뒤 Edit Mode, `GameMap1` scene clean을 확인했다.
- `[경계]` 실제 Player의 시험 외형 연결까지다. 방향별 픽셀 파츠, Character ID, 균일 조명, 연속 회전·스킨·줌의 최종 픽셀 안정화와 체형/크기 아트 확정은 후속이다.

---

## 101. 태양자정 야간 최저와 Player 균일 실제광 `[ENVIRONMENT-01][CHARACTER-RENDER-01]`

- `[현실 기준·야간 곡선][2026-09-02]` 가장 어두운 시각을 임의의 새벽 2~3시가 아니라 태양 고도가 하루 중 가장 낮은 `local solar midnight`로 잡았다. 이 프로젝트의 06시 일출·12시 태양정오·18시 일몰 경로에서는 00시가 그 시점이다. 19.5시 밤 키→00시 최저 키→6.5시 아침 키의 기존 SmoothStep 보간을 유지해 23~01시가 갑자기 꺼지는 점이 아닌 완만한 최저 구간이 된다.
- `[밝기 근본 수정]` 기존 00시 ambient `0.50`보다 전역 하한 `0.62`가 높고 최소 청색 RGB도 00시 키를 덮어 실제 최저값이 적용되지 않았다. 00시 ambient `0.40`, reflection `0.12`, moon `0.18`로 낮추고 하한을 ambient `0.38`, directional `0.12`, RGB `(0.15,0.20,0.40)`로 내려 키프레임이 권위를 갖게 했다. 낮·일몰 키, 달 그림자 전환, 날씨 배율과 구름·로컬광 소유자는 바꾸지 않았다.
- `[캐릭터 실제광·평면 표현]` 기존 Player 재질은 BaseColor만 반환하는 순수 Unlit이라 하늘·시간·날씨·그림자·로컬광을 전혀 받지 않았다. 같은 재질 GUID에서 SH 환경광, 주광의 색/세기·cookie·shadow attenuation, URP 추가광과 기존 단계형 로컬광을 실제로 표본화한다. 단, 모든 body fragment가 픽셀 snap과 분리된 하나의 world anchor를 공유하고 normal·NdotL·BRDF·specular·SSAO를 사용하지 않아 3D 굴곡 명암 없이 캐릭터 전체 밝기와 색만 선형으로 변한다.
- `[중복광·가림 계약]` 별도 color-mask RenderTexture는 만들지 않았다. 최종 opaque depth 뒤 `ZTest Equal`로 실제 보이는 캐릭터 픽셀만 사용자 stencil bit 1에 표시한 다음 fullscreen 단계형 로컬광에서 제외해 캐릭터가 두 번 밝아지거나 전경 벽에 캐릭터 모양 구멍이 생기지 않게 했다. URP의 선택형 stencil LOD cross-fade bit와도 분리했다.
- `[검증]` 마지막 C#은 Unity 6.5/URP 17.5가 생성한 실제 compiler response로 독립 컴파일해 신규 오류 0이었다. 균일 실제광 본체와 fullscreen shader는 앞선 Unity ShaderUtil 확인에서 supported·compiler error 0이었고, 최종 RenderGraph/stencil 변경은 같은 URP 17.5 API와 renderer 설정을 정적 재검토해 P1/P2를 제거했다. 다만 열린 Editor가 최종 파일을 아직 reimport하지 않은 상태에서 MCP bridge가 끊겨 정오·황혼·00시·비·가로등의 최종 Game View 비교는 미검증이다.
- `[현재 경계]` 캐릭터 자체의 표면 명암과 자체 그림자는 의도적으로 없다. 현재는 주변 가림의 shadow/cookie를 한 anchor에서 받아 몸 전체가 균일하게 어두워지는 단계이며, 캐릭터 cast shadow는 추후 proxy/pixel shadow 정책이 정해질 때 추가한다.

---

## 102. 캐릭터 공간 수광 마스크 정정 `[CHARACTER-RENDER-01]`

- `[사용자 확인·근본 원인][2026-09-02]` §101의 전신 공용 world anchor는 메시 노멀 명암만 제거한 것이 아니라 점·스포트 광원의 거리·원뿔, cookie, shadow와 단계광 경계까지 한 점으로 축약했다. 따라서 캐릭터 일부에 빛이 닿을 수 없고 anchor가 경계를 넘는 순간 전신 색이 한 프레임에 바뀌었다. 가로등의 반투명 빛줄기는 별도 체적 pass여서 원하는 부분 조명처럼 보였을 뿐 캐릭터 표면 수광 경로가 아니었다.
- `[근본 수정]` 보이는 각 fragment의 world position으로 주광 shadow/cookie, URP 추가광의 거리·spot/shadow/cookie와 단계광을 각각 계산한다. 실제 mesh normal·NdotL·BRDF·specular·SSAO는 계속 사용하지 않으므로 조명 영역은 실루엣을 공간적으로 가로지르되 구·원통의 곡면 명암은 만들지 않는다. Forward+ 광원 타일 조회도 재투영한 clip 좌표가 아니라 실제 fragment `SV_POSITION`을 사용하도록 바로잡았다.
- `[픽셀 안정·중복 방지]` 렌더용 presentation snap은 유지하되 shader의 수광 위치에 `unsnappedRoot - snappedRoot`를 더해 Camera 이동이 shadow·cookie·단계광 경계를 끌고 다니지 않게 했다. 세계용 단계광 fullscreen pass의 보이는 캐릭터 stencil 제외는 유지해 노멀 기반 광원이 캐릭터에 중복 합성되지 않는다. 새 RenderTexture·pass·Manager와 밝기·감마 보정은 추가하지 않았다.
- `[정적 검증·남은 확인]` Unity 6.5가 생성한 실제 `Assembly-CSharp.rsp`로 C#을 독립 컴파일해 신규 오류 0, 기존 외부 obsolete·unused 경고 2개만 확인했다. 격리 Unity shader 검증은 코드가 아니라 Licensing Client 초기화에서 장시간 정지해 해당 격리 프로세스만 종료했다. 따라서 실제 Editor shader reimport와 고정 시간에서 Spot/cookie/shadow 경계가 몸 일부를 통과하면서 노멀 그라데이션이 없는지 보는 Game View 1회는 미검증이다. 구형 `SteppedLocalLight` 자체의 wall 차폐·cookie 부재와 하루 60초 시험의 약 24Hz 하늘광 갱신은 이번 원인과 별도다.

---

## 103. 캐릭터 전역광 청색화 제거 `[CHARACTER-RENDER-01]`

- `[사용자 확인·원인][2026-09-02]` §102의 픽셀별 공간 경계는 부드러워졌지만 특정 야간·날씨에서 전신이 파랗게 변했다. 기본색은 이미 우윳빛 `(0.91,0.89,0.84)`이고, 밤 SH 하늘광·청색 달빛과 비의 청색 tint를 전신 공통 RGB로 그대로 곱한 합성이 원인이다. 순백·회색 기본색으로 바꿔도 같은 RGB 곱셈이면 청색화는 남는다.
- `[근본 수정]` fragment별 shadow/cookie 감쇠까지 적용한 `SH ambient + main directional`을 먼저 합친 뒤 linear luminance 하나로 바꿔 기본색의 밝기만 조절한다. URP point/spot 추가광과 단계형 로컬광은 기존 RGB를 유지해 실제로 겹치는 부분만 가로등 등의 색을 받는다. 개념식은 `base × (Luminance(ambient + main) + colored local lights)`다.
- `[보존·검증 경계]` 월드의 밤·비 색을 소유하는 `ClearSkyLightingProfile`, 기본색 material, 낮밤 곡선, 외곽선·snap·stencil은 변경하지 않았다. URP Core의 `Color.hlsl`에서 `Luminance`를 명시적으로 포함하고 shader diff를 정적 확인했다. 열린 Editor가 아직 파일을 reimport하지 않아 야간/비의 전신 중성 밝기와 가로등 아래 부분 색을 함께 보는 Game View 1회는 미검증이다.

---

## 104. 캐릭터 첫 프레임 청록색 대체 셰이더 제거 `[CHARACTER-RENDER-01]`

- `[사용자 확인·근본 원인][2026-09-02]` Play 시작 직후 몇 프레임만 파랗고 이후 정상 회색이 되는 현상은 조명 초기화나 기본색 교체가 아니었다. 프로젝트의 `m_AsyncShaderCompilation=1`, 해당 캐릭터 셰이더의 다중 variant와 플레이 직전 import 기록을 대조했으며, Unity Editor가 variant 컴파일 중 표시하는 단색 cyan placeholder의 공식 동작과 증상이 일치했다. 씬에는 주황 단계광과 꺼진 주황 가로등 외에 캐릭터 전신을 파랗게 만들 시작 광원이 없고 Player 원본 MeshRenderer도 직렬화 상태부터 비활성이다.
- `[근본 수정·범위]` `CharacterFlatUnlit`의 실제 색 pass에만 `#pragma editor_sync_compilation`을 지정했다. 이 캐릭터의 보이는 variant를 첫 렌더 전에 준비하므로 cyan 임시 결과를 화면에 내보내지 않으며, 프로젝트 전체의 비동기 셰이더 컴파일과 색을 출력하지 않는 depth pass는 유지한다. 정상 shader의 기본색·SH/주광 중성 밝기·색 있는 로컬광·외곽선·snap·낮밤 권위는 변경하지 않았다.
- `[정적 검증·남은 확인]` Unity 6 현재 API와 공식 매뉴얼에서 해당 pragma가 개별 shader의 Editor 비동기 컴파일을 끄는 지시문임을 확인했고, 보이는 pass 한 곳에만 들어간 diff와 기존 사용자 dirty 분리를 확인했다. 열린 Editor가 수정 뒤 아직 asset refresh 로그를 쓰지 않아 실제 재import 오류 없음과 Play 첫 프레임 회색은 미검증이다. Player 빌드에는 Editor cyan placeholder 자체가 적용되지 않는다.

---

## 105. 정수 전투 스케일과 시험 갑빠 방어 `[ITEM-01][COMBAT-01]`

- `[사용자 확정·계산]` Player와 현재 시험 적의 최대 체력을 `100 → 1000`으로 전환하고 기존 체감 비율을 보존해 다섯 총 `35 → 350`, 치료제 `35 → 350`, 근접/원거리/기존 좀비 공격을 각각 `1/8/10 → 10/80/100`으로 옮겼다. authored 공격력은 10단위, 체력·회복·피해 결과는 양수 half-up 반올림 정수다.
- `[방어 권위·콘텐츠]` 새 `ID 13` 1×1 시험 갑빠가 Point-filter 육각 아이콘과 시험 방어력 20%를 가진다. `ItemDefinition`이 종류별 방어 수치, 기존 `EquipmentLoadoutData`가 현재 장착 definition, `PlayerStats`가 피해 확정을 소유하며 `round(raw × (100-defense)/100)`을 적용한다. UI는 tooltip·정보창으로 읽고, 기존 장비 definition ID 저장을 재사용해 방어 수치를 DTO에 복제하지 않았다.
- `[저장 호환]` 진행 중 원정의 구 100기준 Player·Enemy 체력은 정확히 10배 관계일 때만 1000기준으로 정규화한다. 그 밖의 max 체력 불일치는 기존 fail-closed 경계를 유지한다. 새 ordinary·Recovery 기록은 1000기준 정수 체력을 쓴다.
- `[Unity 컴파일·Editor 호출 확인]` 강제 refresh 뒤 Unity C# 재컴파일과 Core 인접 계약 1회를 통과했다. 갑빠 BodyArmor 배치·tooltip 20%, `100 → 80` 피해, 장비 save capture/restore 뒤 같은 ID·20%, 구 checkpoint `75/100 → 750/1000`, lethal 1회와 prefab HP/시작 ID를 확인했다. 실제 사람 입력의 Alt/drag 장착과 Player build는 이번 변경에서 반복하지 않았다.
- `[Loot 비변경 확인]` 현재 LootTable은 `map seed + stable owner ID`의 결정적 누적확률 1회로 최대 한 종류 1개만 만든다. 확률 합의 나머지는 빈 결과이고 Fresh 전체 후보가 유효할 때만 원자 적용하며 Resume은 실제 grid를 복원한다. 의료 Chest는 치료제 ID 7 100%, 근접 시체는 권총 ID 1 100%, 원거리 시체는 table 없이 prefab 초기값을 유지한다. 미사용 50/50 시험 table은 정의만 남아 있으며 이번 작업에서 Loot 규칙·연결은 바꾸지 않았다.

---

## 106. 폐기된 캐릭터 웜 팔레트 시도 `[CHARACTER-RENDER-01]`

- `[폐기된 시도][2026-09-02]` 낮은 조명에서 기준색이 회색처럼 보이는 현상을 해결한다며 `Light/Mid/Shadow/Dark` 네 색과 임계값을 셰이더에 직접 넣었다. 이는 원래 연속 조명 반응을 고정 팔레트 선택으로 바꾼 잘못된 변경이었다.
- `[현재 아님]` 이 팔레트와 관련 머티리얼 속성은 §107에서 전부 제거했다. 이 절은 당시 시도의 이력만 남기며 현재 구현 근거로 사용하지 않는다.

---

## 107. 고정 팔레트 제거와 캐릭터 색 입력 경로 역추적 `[CHARACTER-RENDER-01]`

- `[사용자 정정·근본 수정][2026-09-02]` §106의 고정 네 색·임계값·로컬광 색 제한을 모두 제거하고, 사용자가 정상이라고 확인했던 §103~104의 연속 수광식 `base × (환경광 luminance + 공간 로컬광)`을 복원했다. 기준색 입력만 요청값 `#FBEDE0`로 유지하며 외곽선·pixel snap·fragment별 shadow/cookie·조명 위치 계산은 바꾸지 않았다.
- `[색 경로 확인]` 실제 Player는 Kenney `characterMedium.fbx`를 사용하지만 prefab에서 FBX 내장 회색 URP/Lit 재질을 `CharacterMannequinMilky.mat`으로 명시 교체한다. FBX 내장 재질에는 텍스처가 없고, 전용 셰이더는 `POSITION`만 읽으며 UV·normal·vertex color·texture sampling을 사용하지 않는다. 런타임 MPB도 pixel anchor와 조명 위치 보정만 기록하고 `_BaseColor`를 덮어쓰지 않는다. 따라서 외부 모델의 원본 재질·텍스처가 회색 출력의 원인은 아니다.
- `[회귀 지점]` 순수 단색 원형은 `_BaseColor`를 그대로 출력했으나 실제광을 도입한 뒤부터 기준색에 조명값을 연속 곱한다. 또한 `#FBEDE0`는 §106 시도에서 처음 에셋에 직렬화되어, 그 전 정상 조명 상태에서는 이 정확한 입력색을 사용한 적이 없었다. 현재는 처음으로 `#FBEDE0`와 기존 연속 수광을 함께 둔 기준 상태다.
- `[Unity 확인]` Play Mode의 기지 mannequin과 영속 Player가 모두 같은 `CharacterMannequinMilky`와 `Spatial Flat Lit`를 사용하고, base가 `RGBA(0.984314,0.929412,0.878431,1)`, MPB base override가 0임을 확인했다. shader는 supported, `ShaderHasError=false`, 속성은 base와 기존 조명 강도 네 개뿐이다. 야간·가로등 아래 최종 색감은 사용자 시각 확인 전이므로 통과로 기록하지 않는다.

---

## 108. 캐릭터 정오 기준색과 밝기 전용 낮 조명 `[CHARACTER-RENDER-01][ENVIRONMENT-01]`

- `[확정 원인·최종 기준][2026-09-02]` 캐릭터는 FBX·texture 누락이 아니라 `base × lighting` 결과가 맑은 정오에도 linear `0.602`여서 기준색이 흐려졌고, `#FBEDE0` 자체도 최종 화면에서 너무 희게 보였다. 낮의 누런색은 물리 계산이나 후처리가 아니라 `ClearSkyLightingProfile`의 6.5/10/16시 `sunColor`와 ambient RGB에 직접 들어 있던 주황·황색 값이었다. Player 시작 8시와 낮 시험 12시도 이 키프레임을 보간해 각각 따뜻한 색을 실제 Directional Light와 바닥·Grass에 전달했다.
- `[근본 수정·일관성]` 캐릭터 material과 shader 기본색을 사용자 선택 `#F7D7BA`로 함께 바꾸고, 측정한 정오 환경값의 역수 `1.66`을 SH+주광 luminance에만 적용해 맑은 정오를 기준 밝기로 정규화했다. 6.5/10/16시 주광은 흰색으로, ambient 삼색은 원래 **선형 휘도와 같은 무채색**으로 바꾸고 주광의 원래 선형 휘도는 intensity에 옮겼다. 실제 profile asset과 `CreateClearSkyDefaults()`를 동일하게 맞췄으며 고정 팔레트·강제 색·overlay·post process는 추가하지 않았다.
- `[보존]` 0시와 19.5시 밤색, 비 weather tint, 달·가로등·URP 추가광·단계형 로컬광의 색과 픽셀별 경계, 외곽선·render snap·shadow/cookie·시간 권위·Player/씬은 유지했다.
- `[Unity 정적·Play 확인]` profile validation, C# compile, shader `supported=True`·`ShaderHasError=False`를 통과했다. 6.5/8/10/12/16시의 sun·ambient RGB가 모두 중성이며 8시는 실제 흰 주광 `0.5808233`, 12시는 `0.8876334`다. `GameMap1` 1280×720에서 순수 Unlit `#F7D7BA`가 `246/214/185`, 현재 정오가 `248/216/187`로 최대 2 차이였고 자정은 `75/64/54`로 `R>G>B`와 밝기 하강을 유지했다. 앞선 같은 shader의 캐릭터 전용 로컬광 검증은 가까운 반쪽 변화 `18.44 > 10.23`으로 공간 경계를 확인했다. 종료 뒤 Edit Mode·scene clean을 확인했고 외부 `ASFolliage` 기존 오류는 분리했다.

---

## 109. 태양 차폐 대비 체적광과 기지 시험 구역 `[ENVIRONMENT-01]`

- `[확정 원인·교체][2026-09-02]` 기존 태양 빛줄기는 카메라 범위에 맞춘 10개 반투명 Quad를 매 프레임 직접 그려 실제 차폐 공간과 무관하게 빈 하늘에서도 선이 생기고 카메라 이동·줌에 따라 판처럼 읽혔다. 이 경로와 런타임 Mesh/Material 할당을 제거하고, 기존 공용 `LocalVolumetricLightRendererFeature`가 실제 URP main-light shadow atlas의 중심/주변 가시성 차이를 half-resolution screen-space 높이 구간에서 적분한 뒤 한 번 합성하도록 교체했다. 완전 조명·완전 그림자 구간은 모두 0이고 차폐 경계만 산란광이 된다. 산란 판정은 표면용 고품질 PCF를 중첩하지 않고 단계당 5개의 단일 atlas compare로 제한한다.

- `[시험 장소]` 재사용 프리팹 `PrototypeSunShaftContrastTestArea`를 `GameMap1` 기지에 연결 배치했다. 같은 화면에서 비교할 수 있도록 콜라이더 없는 완전 개방 수광판, 기둥 4개와 회전한 지붕 슬랫 4개의 건축물, 줄기·수관 3개의 나무 군집으로 나눴다. 실제 차폐 geometry는 그림자를 만들고, 이동을 막아야 하는 기둥·줄기 7개만 기존 `Obstacle` collider를 사용한다.
- `[보존]` `SkyLightingCycleController`의 낮밤·구름·비 권위와 기존 가로등/local emitter 단일산란 경로, Player shell·Camera·씬 흐름은 바꾸지 않았다. 비는 기존 강수량에서 태양 체적광만 92% 억제하고 local emitter의 우천 산란은 유지한다.
- `[Unity 정적·Play 확인]` C# compile과 전용 shader `ShaderUtil` 메시지 0개를 확인했다. 프리팹은 renderer 17개·Obstacle collider 7개이고 scene instance 위치는 `(-15, 0, -11.25)`다. 한 Play Session의 맑은 정오 1280×720 실제 Player Camera에서 개방판은 균일하고 슬랫·수관 차폐부에서만 geometry에 맞는 체적 대비가 나타남을 확인했다. 같은 세션에서 Rain·Night 분기와 기존 local emitter 1개가 유효하고 Day·Clear 복원도 성공했다. 종료 뒤 Edit Mode·scene clean이며, 기존 `CharacterSilhouette` RenderGraph 및 외부 `ASFolliage` shader 오류는 이번 변경과 분리했다.
- `[현재 경계]` 현재 `PC_Renderer`에는 Screen Space Shadows feature가 없어서 main-light shadow atlas 경로가 맞다. 이후 renderer를 Screen Space Shadows로 전환하면 전용 variant와 texture 입력을 함께 추가하는 조건으로 재개방한다.

---

## 110. 월드 고정 광원 평면 적분과 대형 검증장 `[ENVIRONMENT-01]`

- `[근본 교체][2026-09-02]` §109의 중심/주변 4방향 `positive contrast`는 넓은 개구부 내부 가시도가 모두 같으면 광선 몸체가 사라지고 경계만 남는 구조였다. 이를 제거하고, 직교 gameplay Camera 방향을 태양축에 수직 투영해 태양 방향과 평행한 월드 평면군 `dot(P,N)=k·spacing`을 만든 뒤 카메라 광선이 통과한 각 고정 cell의 중점에서 실제 URP main-light shadow atlas 가시도·Beer-Lambert 소멸·위상함수·높이/표면 fade를 적분하도록 교체했다. 평면 원점은 월드 원점에 고정되어 이동·줌에 종속되지 않으며, 태양축과 시선이 거의 평행한 좁은 특이구간은 camera-facing normal로 연속 보간한다.
- `[비용 경계]` 방향광은 half-resolution과 단일 합성을 유지한다. 기본 12 sample에서 이전 `sample × 중심/주변 5회` 대신 cell당 raw shadow compare 1회만 사용하고 shadow atlas 밖은 `BEYOND_SHADOW_FAR`로 조명 처리한다. 조회 수 감소는 구조상 확정이지만 실제 GPU ms는 아직 측정하지 않았다. Screen Space Shadows는 공중의 임의 표본을 검사할 수 없어 이 경로에 사용하지 않는다.
- `[시험 자산]` 기존 `PrototypeSunShaftContrastTestArea` prefab GUID와 `GameMap1` 인스턴스 위치를 유지한 채 약 `100×64m`로 교체했다. 개방 대조군, 완전 지붕, `5×6m` 채광구, 반복 슬랫, 불규칙 수목, 단일 `9m` 벽, `8/24/48m` 거리 차폐물을 독립 구역으로 배치했고 방향광 높이 구간과 최대 표본 예산은 `12m/12`로 올렸다. 씬 파일은 수정하지 않았다.
- `[검증·미검증]` Unity 동적 C# 컴파일 성공, 새 shader `supported=True`·compiler message `0`, 두 prefab 재임포트 성공과 `git diff --check`를 확인했다. 자산 저장 뒤 Unity MCP 연결이 자동 종료되어 새 검증장의 저·중·고 태양각, 줌/이동 world-lock, 개방/밀폐/개구부 시각 비교와 Rain/Night 비교는 이번 작업에서 실행하지 않았으며 통과로 기록하지 않는다.
- `[보존·후속]` 기존 가로등 로컬 체적광, 낮밤·비·구름·웅덩이, Player/Camera/셸과 씬 흐름은 바꾸지 않았다. half-resolution opaque depth 경계의 얇은 foliage 절단, Transparent 차폐/수광, 실제 GPU Profile과 최종 아트 수치는 후속 재개방 조건이다. 사용자 dirty 재질 2개·preview Camera prefab·`GameMap1` Chest 직렬화 6줄은 변경·stage하지 않았다.

---

## 111. 고정 타일 도심과 8방향 도로 그래프 `[MAP-01][POI-01][SPAWN-01]`

- `[사용자 정정·근본 교체][2026-09-03]` 기존 Ground 위에 별도 Road 평면을 얹던 표현은 같은 높이 표면의 깊이 경쟁과 이후 픽셀 타일 교체 불가능성이 원인이었다. 생성 원본을 profile 고정 정사각 격자로 바꾸고 각 셀이 `Ground/Sidewalk/SecondaryRoad/PrimaryRoad` 중 정확히 하나만 소유하게 했다. 현재 renderer는 셀당 quad 하나를 한 XZ mesh의 네 submesh로 묶으며 충돌용 Ground에는 renderer가 없어 coplanar 표면을 겹치지 않는다.
- `[도로 계약]` 상하좌우·대각 8방향만 허용한다. 내부 주 도로, seed 순서의 spanning backbone, 선택 loop, coarse block당 대각 하나 순으로 만들며 선언된 공용 node 밖의 교차와 X 교차를 거부한다. 도로 그래프의 정확한 중심선 연결 `roadPorts`와 면 경계용 canonical 47타일 mask는 별도 데이터다. 대각 surface bit는 두 cardinal 이웃도 연결됐을 때만 켜므로 맞닿은 모서리가 가짜 연결을 만들지 않는다.
- `[건물·가로 시설]` 도로·인도 raster 뒤 남은 셀에 프로젝트 adapter를 거친 BrokenVector 벽돌집 네 종을 배치한다. adapter는 입구 방향을 +Z로 통일하고 vendor collider를 끄며 layout root의 BoxCollider 하나가 점유·NavMesh 권위를 가진다. 가로수·가로등·자전거·쓰레기통은 source road, 진행 거리, 좌우와 측면 offset을 저장한 뒤 인도 셀·보호 거리에서만 생성한다. 공용 시험 가로등 prefab은 원형 비율을 유지한 채 3배 크기와 3배 range, 거리 제곱 광량으로 맞췄다.
- `[알고리즘 근거]` Parish·Müller와 Chen 등의 `도로망 → 필지 → 건물` 분리, Tiled/Unity AutoTile의 47/blob surface 규칙, StreetGen의 road-relative 가로 시설 표현을 적용했다. Unity Tilemap/RuleTile은 도시 연결성을 생성하는 권위가 아니라 최종 sprite atlas를 그릴 수 있는 선택적 출력기로 취급한다. 현재 3D XZ·NavMesh·방향광 계약에는 논리 격자에서 만든 XZ mesh가 기본 출력이다.
- `[정적·변조 검증]` Unity 컴파일·Console 오류 0에서 기본 seed 0~255의 생성·결정성·D8·canonical mask·exact road-port가 모두 통과했다. 모든 port 제거, 같은 block의 X 대각, NaN tile size/road width/furniture distance를 각각 주입하면 validator가 원인별로 거부했다. 외부 foliage shader의 중복 URP keyword와 vendor `ModelCustomizer`의 고립된 attribute도 import 원인에서 제거했다.
- `[Play Mode 1회]` 직접 `GameMapTest`와 `GameMap1` 왕복 1회를 실행했다. 첫 map은 seed `1458508496`, `145×145`셀=`290×290m`, 도로 70·건물 22·가로 시설 183·의료 POI 1이었고 surface 정점은 셀당 4개인 `84,100`개였다. 단일 surface와 비렌더 Ground, 건물 root collider, 가로 시설 수, Entry→Portal 및 POI/시험 spawn NavMesh, Player·Camera·Inventory UI·EventSystem 동일 인스턴스와 runtime Error 0을 확인했다. 종료 뒤 두 scene 파일 hash는 변하지 않았다.
- `[현재 경계]` 현재 색은 알고리즘 확인용이며 최종 픽셀 atlas·variant catalog, 실제 graph-face 필지 분할, 회전별 건물 footprint mask, 내부·랜드마크·폐차는 아트/규칙이 정해질 때 같은 layout 데이터에 연결한다. 현재 시험 `145×145/2m`는 GameMapTest profile의 고정값이지 모든 미래 맵 크기를 코드 상수로 봉인한 값은 아니다.

---

## 112. 도로 전면 필지와 외관 건물 팔레트 복원 `[MAP-01][POI-01][SPAWN-01]`

- `[사용자 피드백·근본 원인][2026-09-03]` 기존 40m coarse block은 도로·인도·후퇴선을 뺀 가용 폭이 21m인데 목표 lot을 14~20m로 나눠 행·열이 항상 `1×1`이었다. density와 보호 조건은 그 한 후보를 제거할 수만 있어 512개 seed 모두 block당 최대 건물 1개였으며 건물 면적도 block 내부의 약 12%뿐이었다.
- `[구조 교체]` 생성 순서를 `도로·surface → 도로 전면 parcel → 건물 → 접근 후보·POI`로 명시했다. 상하좌우 도로 양쪽을 `10~12m × 6~8m`의 비중첩 필지로 나누고 각 건물은 `SourceParcelIndex` 하나만 점유한다. 필지가 source road·거리·side·전면 방향을 소유하므로 POI 접근점도 최근접 도로를 다시 추측하지 않는다. layout hash와 Recovery 호환 경계를 위해 generator version은 5로 올렸다.
- `[에셋 판정·표현 수정]` BrokenVector Low Poly Brick Houses는 문·내부 바닥·방·계단이 없는 exterior asset임을 prefab 구조와 배포 설명으로 확인했다. 전체 footprint BoxCollider·NotWalkable과 비활성 vendor collider를 유지해 진입 가능한 건물로 가장하지 않는다. 텍스처 누락 원인은 생성기가 원본 `Houses_2` 팔레트를 texture 없는 graybox 재질로 교체하던 것이었으며, source `_MainTex`·scale·offset·glossiness를 캐시된 URP Lit 재질의 `_BaseMap`·smoothness로 전달하도록 고쳤다. 일반 건물은 원색, 의료 POI만 property-block tint를 쓴다.
- `[불필요 표현 제거]` 가로수·가로등·자전거·쓰레기통의 결정적 road-relative socket 데이터는 미래 prefab 교체를 위해 보존하되 임시 Cylinder·Sphere·Cube는 기본 생성하지 않는다. 외곽 경계 4개는 collider·NotWalkable만 유지하고 renderer를 제거했다. vendor prefab의 비활성 선택 부품은 화면·충돌에 참여하지 않으며 wrapper 최적화는 실제 병목 증거가 생길 때만 재개방한다.
- `[Unity 컴파일·순수 검증]` 최신 C# 동적 컴파일과 setup validator의 seed 0~255를 통과했다. 실패·결정성 불일치 0, unique layout hash 256, parcel `108~169`, 건물 `77~139`이며 모든 seed에서 한 도로 전면의 최대 건물 수가 최소 2였다. 잘못 뒤집은 parcel side도 validator가 거부했다. 원본 팔레트 texture reference 전달과 선택한 네 모델의 UV가 triangle 내부에서 palette texel을 가로지르지 않는 것도 실제 Unity 객체로 확인했다.
- `[Play Mode 대표 1회]` direct `GameMapTest` 시작과 `GameMap1` 왕복 1회를 통과했다. seed `1519253678`, world hash `B21D2432AAFE23BB`, runtime Error 0, Player·Camera·Inventory UI·EventSystem 동일성, NavMesh·POI·spawn과 scene 복원을 확인했다. 사용자 기존 dirty 파일은 저장하거나 stage하지 않았다.
- `[현재 경계]` 대각 도로는 D8 네트워크와 surface에 남지만 회전 footprint mask가 없어 대각 전면 parcel은 아직 만들지 않는다. 실제 진입 건물은 최종 건물 prefab/모듈, 내부 floor·wall·door/roof visibility, 통과 collider와 내부 NavMesh 계약을 함께 정하는 별도 기능이다.

---

## 113. 양방향 도로 폭과 밀집 도심 필지 `[MAP-01][ENVIRONMENT-01]`

- `[사용자 피드백·원인][2026-09-03]` 화면의 네모난 링은 도심 생성물이나 투명 지붕 면이 아니라 고정 배치된 `PrototypeRainShelterTestArea`의 가시 바닥 테두리 Cube 네 개였다. 실제 `RoofOccluder` renderer는 꺼져 있었다. `GameMap1`·`GameMapTest`의 시험 배치를 제거하고, Setup이 폐기된 `UrbanLayoutProtectionAnchors`를 다시 만들지 않도록 바꿔 주변 8m의 불필요한 건물 금지 영역도 없앴다. 비 차단 시스템과 재사용 prefab 자체는 보존했다.
- `[도로 계약]` 일방통행 데이터가 없는 현재 도로를 모두 양방향으로 취급한다. 보조 도로는 한쪽 3타일+중심 1타일+반대쪽 3타일의 최소 7타일, 주 도로는 9타일이며 validator가 설정값과 실제 segment 폭의 일치를 확인한다. 중심 타일은 폭 계산 계약이고 최종 중앙선 그림은 atlas 표현 단계로 남겼다.
- `[밀집 배치]` 선택 loop 확률을 `0.35→0.65`, setback과 lot gap을 `0`, 필지를 `8~10m × 8m`, density를 `1`로 바꾸고 도로 전면당 최대 3필지 제한을 제거했다. 유효 필지는 모두 건물이 점유하며 generator version은 6으로 올려 변경 전 Recovery layout을 같은 월드로 오인하지 않는다.
- `[Unity 정적 검증]` 현재 runtime assembly 컴파일 뒤 기본 256개 seed가 모두 통과했다. unique hash 256, 도로 폭·D8·surface·충돌·접근 조건을 유지했고 parcel과 building은 각각 `125~183`으로 모든 seed에서 동일해 빈 유효 필지가 0개였다. 별도 64 seed 표본은 도로 `70~88`(평균 78.9), 건물 `135~182`(평균 153.7), Ground 셀 기준 건물 점유 `25.8~35.2%`(평균 31.0%)였다. 마지막 Editor validator 보강도 Unity의 동일 compiler response로 오류 없이 컴파일했다.
- `[Play Mode 미검증]` 이 수치 변경 뒤 새 대표 Play는 Unity MCP 전용 연결이 종료되어 실행하지 못했다. 직전 §112의 Play 결과는 새 7/9타일·100% 필지 설정의 런타임 증거로 재사용하지 않는다. 다음 실제 실행에서는 `GameMapTest` 재진입 1회로 도로 체감 폭, 건물 밀도, Entry→Portal·POI·spawn NavMesh와 runtime Error를 확인한다.

---

## 114. 도로 합류부 정규화와 인도·가로 시설 복원 `[MAP-01]`

- `[근본 원인·수정][2026-09-03]` 직선 도로 가장자리의 한 칸 오목부는 생성 순서나 7/9 홀수 폭 문제가 아니라 45도 도로와 직선 도로를 각각 원형 stamp로 합친 급각 접합부에 `Sidewalk` 한 셀이 남던 현상이었다. 전체 도로 합집합을 먼저 만든 뒤 원본 snapshot 기준으로 상하좌우 세 면 이상이 도로인 단일 셀만 한 번 정규화하고, 최종 도로 mask에서 인도를 파생하도록 순서를 고쳤다. 반복 팽창은 하지 않으며 인접 Primary가 있으면 해당 셀도 Primary가 된다. Recovery의 월드 동일성 경계를 위해 generator version은 7이다.
- `[표현·선택 권위]` 인도는 별도 겹침 plane이 아니라 기존 단일 surface mesh의 `Sidewalk` submesh를 0.12m 올리고 경계 curb 면과 밝은 재질로 구분했다. 기존 road-relative socket은 유지하면서 가로수와 가로등만 기본 표시하고 자전거·쓰레기통 시험 proxy는 계속 끈다. 가로등을 먼저 배정해 가로수와 같은 인도 셀을 다툴 때 조명 위치가 사라지지 않게 했다.
- `[Unity 정적 검증]` 도로 정규화 뒤 seed 0~255가 모두 유효하고 hash 256개가 서로 달랐으며, 단일 셀 오목부 validator를 모두 통과했다. 도로 `69~88`, 건물 `125~183`, 인도 `2078~2214`였다. 가로등 우선 배치까지 반영한 최신 Unity assembly를 같은 256개 seed로 다시 실행해 가로등 `23~53`개(평균 `39.41`), 가로수 `60~94`개(평균 `78.69`)와 생성 실패 0건을 확인했다. Unity 6.5 실제 runtime/editor compiler response도 오류 없이 완료됐고 기존 외부 경고 2개만 남았다.
- `[씬·미검증]` Unity Editor API로 `GameMapTest`의 가로수/가로등 표시를 켜고 clutter는 끈 채 저장했다. Play 검증의 surface 정점 계약도 논리 타일 상판과 노출된 curb 면을 각각 정확히 세도록 갱신했다. 새 v7 지형의 실제 화면상 curb 높이·가로 시설 분포·NavMesh와 사용자가 본 위치의 notch 제거는 대표 Play 1회가 아직 필요하다. 카메라 끝 건물 투명화처럼 보이는 별도 현상은 알파/LOD가 아니라 10m 카메라보다 10.5~18m 건물이 높아 near plane과 backface가 잘리는 것이 정적 근거상 유력하며 픽셀아트 교체만으로 해결되지 않는다.

---

## 115. 생성형 도심의 공유 가로등 복원 `[MAP-01][ENVIRONMENT-01]`

- `[사용자 피드백·근본 원인][2026-09-04]` 가로등 socket 데이터는 있었지만 표현 생성기가 기존 `PrototypeStreetLamp`를 사용하지 않고 Cylinder 기둥과 Cube 머리를 새로 만들고 있었다. 이 대체물에는 `Light`, `NightActivatedStreetLamp`, cookie·shadow와 `StylizedLightShaftEmitter`가 전혀 없었다. 또한 road tangent인 `LocalYawDegrees`만 적용하고 좌우 `Side`를 무시해 램프 머리가 차도가 아니라 도로 진행 방향을 향했다.
- `[수정]` `GameMapTest` 생성기에 기존 공유 `Assets/Prefabs/Lighting/PrototypeStreetLamp.prefab`을 명시 연결하고, 가로등 socket만 그 prefab 전체를 직접 인스턴스화한다. 원본 prefab의 root `BoxCollider`·carving `NavMeshObstacle`, 야간 Spot·발광부·체적광 설정은 그대로 사용한다. 원본 arm의 local `-Z`가 차도를 향하도록 표현 yaw만 `LocalYawDegrees + 90° × Side`로 바꿨으며, 결정적 layout·generator version·world hash 입력은 변경하지 않았다.
- `[회귀 방지]` 생성 전 prefab의 필수 충돌·Spot·야간 제어·빛줄기 연결을 fail-closed로 검사한다. Play validator도 생성된 모든 가로등의 prefab 구성, carving obstacle, layout stable ID와 좌우 회전을 검사하고, 22시에 모든 lamp visibility와 실제 Light intensity가 maximum에 도달하는지 확인한 뒤 원래 시간을 복원한다.
- `[Unity 컴파일·Play 1회]` Unity 동적 컴파일 성공 후 direct `GameMapTest` 시작과 `GameMap1` 왕복 1회를 통과했다. seed `-1198157842`, world hash `17B58E5B7AB85F9B`, runtime Error 0이며 생성 가로등의 22시 점등·방향, NavMesh·POI·spawn, Player·Camera·Inventory UI·EventSystem 동일성과 원래 `GameMap1` 복원을 함께 확인했다. 기존 사용자 dirty 파일은 저장하거나 stage하지 않았다.
- `[현재 경계]` seed당 다수의 실제 Spot Light가 생기며 기존 체적광 표현기는 가까운 최대 8개를 선택한다. 기능 복원과 별개로 최종 도심 야간 성능은 GPU Profiler와 shadow LOD 근거가 생길 때 재개방한다.

---

## 116. Meshy 치비 정적 렌더 시험체 `[CHARACTER-RENDER-01]`

- `[격리 시험][2026-09-04]` 사용자 제공 Meshy FBX와 Base Color·Roughness·Metallic 맵을 원본 수정 없이 별도 ThirdParty 폴더에 가져오고, 실제 Player와 `PersistentGameplayShell`은 교체하지 않았다. FBX는 단일 MeshRenderer·35,252 Unity 정점·56,840 삼각형이며 Animator·bone·skin·animation과 Collider가 없는 정적 모델이다.
- `[텍스처 경로]` 확장자만 PNG였던 Base Color WebP를 유효한 PNG로 변환하고, 기존 캐릭터 공간 평면광 셰이더에 기본 white인 `_BaseMap` 표본만 추가했다. 기존 단색 mannequin은 기본 white map으로 같은 결과를 유지하며, 표면 곡면 명암을 되살리는 PBR roughness·metallic 계산은 연결하지 않았다.
- `[Editor 렌더·참조 확인]` 전용 `CharacterSilhouetteTest` 씬에서 발 높이·약 4m 시험 크기·layer 30·외곽선·Base Map 참조를 확인하고 정면 카메라 렌더를 만들었다. 모델은 화면에 정상 표시되지만 T 포즈이고 머리카락이 얼굴 한쪽을 크게 가리며 밝은 피부·의상 경계가 약해 최종 Player 후보로는 미확정이다.
- `[보존·오류]` 임시 additive 씬은 저장 없이 닫았고 `GameMap1`은 저장하지 않았다. Unity Console 신규 Error는 0이며 기존 BrokenVector·raid direct-entry·local volumetric light·MCP 서명·외부 shader UI Warning만 남았다.

---

## 117. 좀비 실루엣·픽셀 텍스처 A/B와 이동속도 배율 `[CHARACTER-RENDER-01][MOVE-01][AI-01]`

- `[구조]` `KenneyZombiePatrol`의 gameplay root가 아니라 시각 자식 `ZombieAgent`에 기존 `CharacterSilhouetteSubject`를 붙였다. 렌더링 layer bit31과 render-time snap만 공유하므로 AI root·NavMesh·Collider·피격·시체 수명은 바뀌지 않는다. 현재 외곽선 mask는 개체 ID가 없는 공용 이진 mask라 서로 닿은 실루엣의 내부 경계는 합쳐지는 시험 한계가 있다.
- `[A/B 시험]` 별도 `EnemyPixelComparisonTest` 씬의 왼쪽은 원본 256px을 nearest로 실제 64px PNG로 만든 Point/no-mipmap 머티리얼, 오른쪽은 원본을 유지하고 같은 캐릭터 셰이더에서 UV를 64칸으로 양자화해 LOD0 Point 표본하는 머티리얼이다. 전체 화면 RenderTexture·pixel camera는 추가하지 않았고 실제 gameplay 좀비 material도 아직 교체하지 않았다.
- `[속도]` Player 권위값은 걷기 `5→10`, 기존 1.3배 규칙에 따른 달리기 `6.5→13`이다. `KenneyZombie`와 그 raid 근접 definition은 순찰 `1.5→3`, 전투 `3.4→6.8`이며 `EnemyAIController`가 이 definition 값을 기존 `NavMeshAgent`에 적용한다. 이동 Animator clip 속도는 별도 시각 튜닝이므로 변경하지 않았다.
- `[검증]` Unity shader compiler error 0, 전용 씬 좀비 2개·각 Subject 1개·render mask `2147483649`·baked/runtime material 참조를 확인하고 1280×720 Editor camera 단독 렌더를 저장했다. raw PNG 팔레트 대조에서 baked 픽셀의 원본 외 색은 0개였다. 새 수치와 prefab/asset 참조는 정적으로 확인했으며, 변경된 실제 이동 거리와 animation foot sliding은 Play Mode에서 아직 확인하지 않았다. 기존 dirty `GameMap1`과 사용자 에셋은 저장·stage하지 않는다.

---

## 118. 선택적 화면공간 좀비 픽셀 합성 `[CHARACTER-RENDER-01]`

- `[사용자 피드백·확정 원인][2026-09-04]` §117의 texture bake와 UV grid 양자화는 둘 다 표면 UV의 표본 해상도만 낮춰 실루엣·조명·화면상 픽셀 크기를 바꾸지 않으므로 거의 같아 보이는 것이 정상이다. 이를 같은 수치의 다른 패치로 반복하지 않고, 비교 오른쪽 개체만 실제 렌더 완료 색을 화면 셀 단위로 다시 구성하는 경로로 교체했다.
- `[구조]` 기존 `CharacterSilhouetteSubject`와 `CharacterSilhouetteRendererFeature`를 확장했다. Subject의 opt-in rendering-layer bit30만 별도 가시 mask에 기록하고, 원래 opaque 렌더와 조명·그림자가 끝난 camera color를 한 번 복사한 뒤 각 `3×3` 화면 셀에서 실제로 보이는 가장 가까운 좀비 색·eye depth 하나를 선택해 저해상도 buffer에 저장하고 Point 방식으로 합성한다. 색 표본이 필요한 frame만 URP intermediate camera color를 요구해 backbuffer 직접 표본을 피한다. raw mask가 한 픽셀이라도 있는 셀은 전부 채우므로 원래 고해상도 몸체 가장자리가 새지 않으며, resolved camera depth보다 가까운 벽·소품 위에는 합성하지 않는다.
- `[격리·보존]` bit31 외곽선, 표시 root의 render-time snap, Player·일반 좀비 material과 AI/NavMesh/Collider/피격/시체 수명은 유지했다. `EnemyPixelComparisonTest`의 왼쪽은 기존 64px texture bake 대조군, 오른쪽만 원본 texture·UV grid 0과 screen-space opt-in을 사용한다. 별도 Camera·Manager·전체 화면 픽셀 필터는 추가하지 않았다.
- `[Unity shader·Play 검증]` Unity 6.5/URP 17.5에서 C# compile, mask `4/4` pass와 composite `5/5` pass, 두 shader supported·compiler error 0을 확인했다. 전용 씬 Play 1회에서 왼쪽 opt-in false, 오른쪽 true, 활성 screen target 및 bit30·bit31을 확인했고 1024×640 camera render에서 밝은 내부 `3×3` 셀의 완전 단색 비율이 왼쪽 `1899/3555`, 오른쪽 `3643/3670`이었다. 임시 전면 Cube를 둔 별도 렌더에서 오른쪽 합성이 Cube 앞을 침범하지 않았고, 검증 Cube 제거·Edit Mode·scene clean을 확인했다.
- `[현재 경계]` 서로 다른 screen-pixel 대상 둘이 같은 화면 셀을 공유하면 아직 개체 ID가 없어 가장 가까운 eye-depth 표본 하나가 그 셀을 대표한다. 실제 gameplay 좀비 body 적용, 접촉 개체별 ID buffer, 최종 셀 크기·해상도/줌 정책은 시험 결과를 보고 재개방한다. Console에는 기능 오류가 아니라 잘못된 MCP Camera Capture instance ID를 사용한 검증 도구 오류 2건이 남아 있으며 실제 렌더는 Editor camera의 명시적 RenderTexture로 대체 확인했다.

---

## 119. 화면공간 5px 셀과 단일 외곽선 `[CHARACTER-RENDER-01]`

- `[원인][2026-09-04]` 화면공간 대상이 기존 bit31 외곽선과 bit30 화면 셀 경로에 동시에 포함되어 서로 다른 격자의 테두리가 겹쳤다. 모델 크기나 결과 위에 선을 덧씌우지 않고 두 외곽선 경로의 소유권을 분리했다.
- `[구조]` bit31은 기존 로컬 조명용 전체 캐릭터 표식으로 보존하고 bit29를 일반 외곽선 전용으로 추가했다. 일반 대상은 기존 3px 외곽선, screen opt-in은 전용 5px 몸체 셀과 같은 저해상도 점유 mask의 `8방향 1셀 팽창 - 본체`만 사용한다. 새 R16 buffer에는 한 겹 외곽선의 eye depth만 기록하며 최종 합성은 본체·외곽선 모두 camera depth를 통과한다.
- `[Play Mode 확인]` 비교 씬에서 왼쪽 일반 renderer는 bit31+bit29, 오른쪽 screen renderer는 bit31+bit30으로 상호배타임을 확인했다. Unity C# compile, composite shader `6/6` pass·compiler error 0 뒤 1024×640 렌더에서 오른쪽 몸체가 5px 셀로 커지고 외곽선이 같은 격자의 외부 한 셀 ring으로만 출력됨을 확인했다. Play 종료 후 scene은 clean이다.
- `[보존·경계]` Player·일반 좀비의 기존 3px 외곽선과 로컬 조명 stencil은 유지했다. 실제 gameplay screen 적용, 이동·줌 위상, 접촉한 여러 screen 대상의 ID 분리는 아직 후속이다.

---

## 120. 캐릭터 루트 부착형 화면 픽셀 `[CHARACTER-RENDER-01]`

- `[사용자 피드백·원인][2026-09-04]` §118~119는 화면 원점에서 `5×5` 칸을 다시 나눠, 캐릭터가 한 화면 픽셀만 움직여도 각 칸의 표면 대표색을 새로 선택했다. 이는 애니메이션의 실제 변형과 무관한 이동 위상 변화까지 색 떨림으로 증폭했다. 셀 RGB 평균은 위상을 고치지 못하고 피부·옷·머리의 중간색을 만들므로 적용하지 않았다.
- `[근본 수정]` 기존 `_CharacterPixelGridAnchorWS`를 화면색 경로에도 사용한다. 각 screen opt-in renderer가 자기 presentation root를 기준으로 한 칸당 가시 seed 한 점만 기록하고, full-resolution transient buffer에서 그 seed의 이미 계산된 재질·조명색과 eye depth를 `5×5`로 확장한다. 따라서 서로 다른 캐릭터의 격자 위상을 하나의 viewport 저해상도 격자에 강제로 맞추지 않으며 RGB history·시간 보간·전체 화면 저해상도화는 없다.
- `[Play Mode 수치·시각 확인]` `EnemyPixelComparisonTest`의 오른쪽 대상만 남기고 Animator pose를 고정한 뒤 Camera right 방향으로 정확히 1 screen pixel 이동시켰다. 이동 전 결과와 이동 후 결과를 1px 맞춰 비교한 캐릭터 영역 `58,475`픽셀 중 채널 차이 `2/255` 초과는 `0`, 최대 차이는 `1/255`였다. 1280×720 렌더에서 5px 본체와 같은 격자의 단일 외곽선도 유지됐다. 두 shader는 supported이며 compiler error 0, scene dirty false였다.
- `[보존·경계]` 원래 Animator 속도·clip·AI·NavMesh·Collider·조명·왼쪽 64px 대조군은 변경하지 않았다. 뼈가 실제로 변형한 표면은 해당 root-local seed에서만 정상 갱신되며, 10~12fps 표현용 pose stepping은 별도 시각 결정 전 강제하지 않는다. 접촉한 여러 개체의 정확한 내부 경계에는 stable Character ID가, full-resolution seed 확장의 최종 비용에는 GPU Profile이 필요하다. 첫 검증에서 RenderGraph pass 안의 전역값 변경 오류를 확인했으며 픽셀 크기 소유를 mask material로 옮겨 제거했다. 해당 과거 오류 기록은 Console에서 지우지 않았다.

---

## 121. 좁은 골든아워 팔레트와 연기형 구름 그림자 `[ENVIRONMENT-01]`

- `[사용자 피드백·원인][2026-09-04]` 기존 Clear 프로필은 0·6.5·10·16·19.5시 다섯 키뿐이라 새벽·일출·일몰·황혼을 각각 조형하기 어려웠다. 구름 Cookie는 64×64 안의 32×32 도안을 정확히 2배 확대한 구조여서 24m 투영 기준 한 매크로 셀이 0.75m였고, 줌에 따라 화면에서 거대한 사각 덩어리처럼 보였다. Controller의 시간 보간·구름 이동·투영은 원인이 아니었다.
- `[근본 수정]` 같은 `SkyLightingCycleController`와 단일 Cookie GUID를 유지했다. Clear 프로필을 0·4.75·5.75·6.5·7.5·10·16·17.5·18.25·19.5·22시의 11개 키로 세분화해 청색 새벽→짧은 주황 일출→중성 낮→짧은 주황 일몰→청색 황혼→0시 최저를 기존 SmoothStep 보간으로 잇는다. Cookie는 256×256에서 크기·방향이 다른 원·타원 밀도장을 결합하고 가장자리 홈을 감산한 6개 연기형 군집으로 교체했으며, 옅은 외곽부터 짙은 중심까지 네 그림자 농도를 한 소스에 저장했다. 새 구름 Manager·오브젝트·렌더 패스는 추가하지 않았다.
- `[정적·Play Mode 검증]` 프로필 asset과 코드 기본값의 11키 일치를 확인하고 0~24시 1분 표본 1,440개에서 0시가 최저, 인접 최대 변화량 0.0088임을 확인했다. Cookie는 256×256·mipmap 9·Trilinear·Repeat·선형·무압축이며 그림자 점유 22.5%, 네 농도 모두 존재하고 12px 반복 경계 침범은 0이었다. `GameMap1` 한 Play Session의 직교 size 3.5·5·8 렌더에서 둥근 군집과 픽셀 경계가 유지됐고, 6.5·12·18.25·0시 대표 프레임을 확인했다. Clear→Rain→Clear는 강수 `0→1→0`, 구름 농도 `0.902→0→0.902`로 복원됐다.
- `[보존·경계]` 비·물 튐·웅덩이·가로등·빛줄기·60초 시험 주기, Player·Camera·씬 흐름과 사용자 dirty asset은 변경하지 않았다. Unity 6의 새 Entity ID를 구식 Instance ID로 받는 MCP Camera Capture 1회가 검증 도구 오류를 남겼지만, 게임 Camera의 명시적 RenderTexture 렌더와 환경 호출에서는 신규 게임 코드 오류를 확인하지 않았다. 최종 색감·구름 농도는 사용자 아트 판단, 실제 장시간 반복 이음새와 Player build·GPU Profile은 미검증이다.

---

## 122. 고정 6군집을 동적 연속 구름 밀도장으로 교체 `[ENVIRONMENT-01]`

- `[사용자 피드백·근본 원인][2026-09-04]` §121의 결과는 여섯 텍스처가 아니라 `256×256` PNG 하나 안의 고정 군집 6개였다. 네 단계의 동심 농도와 작은 `24×24m` 반복 주기가 형태 변화 없이 이동해서, 크고 작은 구름이 아니라 빽빽한 물감 얼룩·산등성이처럼 읽혔다. 해상도나 임계값만 더 조정하는 것으로는 이 고정 형상과 반복 원인을 없앨 수 없었다.
- `[외부 구조 비교]` Horizon Zero Dawn/Nubis의 `큰 지배 형상 → Perlin-Worley 계열 둥근 덩어리 → 경계부 세부 침식`, Unity HDRP의 shaping/erosion 분리와 별도 cloud shadow map, Unreal의 저비용 Beer shadow map/Light Function, t3ssel8r 공개 설명과 후속 Unity 구현의 서로 다른 크기 노이즈 상대 이동을 비교했다. 현재 고정 쿼터뷰 URP에는 볼류메트릭 raymarch·풀스크린 후처리·투영 Quad보다 기존 Directional Light Cookie가 정확하고 가벼우므로 투영 경로는 유지했다.
- `[근본 교체]` `SkyLightingCycleController` 단일 권위 안에서 `512×512` 동적 밀도 RT와 최종 투과율 Cookie RT를 분리했다. `128×128m` 주기의 타일 가능한 저주파 2/4/8 지배 형상에 Worley 둥근 굴곡을 한 번만 더하고, 16/29 세부 노이즈는 경계에서만 감산한다. 모든 결과는 연속 밀도 하나로 합친 뒤 `1 - density × weatherOpacity × 0.42`로 직사광만 감쇠한다. 밀도는 4Hz로만 갱신하고 서로 다른 스케일의 매우 느린 상대 이동으로 형태를 바꾸며, 기존 서→동 바람 Cookie offset은 매 프레임 이동한다. 사용하지 않게 된 고정 PNG는 프로젝트 전체 dependency 0건 확인 뒤 휴지통으로 옮겼다.
- `[Unity 컴파일·Play Mode 호출 확인]` Unity 재컴파일·profile validation과 2-pass shader supported·compiler error/warning 0에서 `128m·512px·coverage 0.38·0.25초`를 확인했다. `GameMap1` 맑은 정오 한 Play Session에서 최종 Cookie `512×512`, 타일 경계 평균 채널차 `좌우 0.271/255·상하 0.613/255`였고, 8초 뒤 내부 형상은 평균 `2.894/255`, 3 이상 변화 픽셀 `14.2%`로 급격한 교체 없이 변화했다. Clear→Rain→Clear는 구름 농도 `0.902→0→0.902`, 강수 `0→1→0`으로 복원됐고 종료 뒤 `GameMap1`은 Edit Mode·scene clean이었다.
- `[보존·경계]` 11키 낮밤·고도별 경계/농도·투영 보정·비/차폐·웅덩이·로컬광·Player/Camera/씬 흐름은 변경하지 않았다. Game View의 최종 구름 크기·농도는 사용자 아트 판단, 장시간 날씨와 GPU ms·Player build는 미검증이다. Console의 BrokenVector 구버전 직렬화 오류와 시드 비교용 동적 검증 명령의 RenderTexture release 경고는 이번 런타임 코드와 분리했으며 지워서 덮지 않았다.

---

## 123. 구름 비가시 재검토와 반복 영역/형성 크기 분리 `[ENVIRONMENT-01]`

- `[사용자 회귀 신고][2026-09-05]` §122 이후 구름이 보이지 않는다는 피드백으로 재개방했다. 기존 쿠키 전체의 통계·생성 성공은 실제 카메라 영역의 구름 가독성을 검증하지 못했다. 맑은 정오 기지 Camera에서 원래 결과와 임시 흰색/검정 Cookie를 비교하여 Ground·Player가 Cookie에 반응함을 확인했다. URP17.5 주 방향광은 RT를 매 렌더 직접 바인딩하므로 atlas 갱신 누락이 아니며, 128m 반복 영역과 고정 저주파 2가 구름 형성 크기까지 함께 키워 긴 빈 구간·완만한 명암만 보일 수 있는 설정이었다.
- `[현재 시험 변경]` Profile의 `CloudShadowFormationSize=16m`를 반복 영역 128m와 분리했다. 정수 주기 `(8,8)`에서 큰 형상·둥근 굴곡·침식을 같은 비율로 계산하며, 비정사각형 각 축의 주기도 보존한다. 세부 노이즈는 RT 해상도에 맞춰 제한한다. coverage `0.55`, 직사광 최대 감쇠 `0.72`는 구름 가독성 확인용 시험값이며 최종 아트 확정값이 아니다.
- `[실제 확인·미완료 경계]` 2-pass shader supported·compiler message 0, profile validation 통과. 맑음→비→맑음에서 구름 농도 `0.902→0→0.902`와 동일 Cookie 복원을 확인했다. 기지의 실제 게임 시간 15.57초를 32프레임으로 촬영한 미리보기를 사용자에게 제시했으며, 구름의 형태·크기·농도 합격은 사용자 응답 대기다. 첫 캡처는 GameView 비활성·runInBackground false로 게임 시간이 진행되지 않아 폐기했고, 재촬영 때만 런타임 background 실행을 허용한 뒤 false로 복구했다. 게임 설정과 씬 저장 데이터는 변경하지 않았다. 최종 가시성 해결 완료·GPU 성능·Player build를 통과로 기록하지 않는다.
- `[후속 시각 피드백][2026-09-05]` 사용자가 다층 느낌 축소·선명한 경계·소폭 확대를 요청했다. 내부 `0.72→1` 농도 그라데이션을 제거하고 경계 smoothstep 폭만 `±0.055→±0.025`로 줄였다. 형성 간격 `18.3m`는 정수 주기 7, 실효 간격 약18.29m로 이전보다 약14% 크다. 생성·바람·날씨 경로는 유지했다. shader 2-pass supported·compiler message 0, 실제 기지 13.37초/26프레임 미리보기를 제시했다. 형태 합격은 사용자 확인 대기이며 반복 보정·완료 커밋은 보류한다.

---

## 124. 풀·잎 오브젝트 개별 픽셀 재질 시험과 재개 경계 `[ENVIRONMENT-01]`

- `[구현][2026-09-05]` `PrototypePixelFoliage.prefab`을 `GameMap1 (-5.5,0,-5)`에 하나 배치했다. `PixelFoliagePatch`의 Inspector 설정을 Editor mesh builder가 grass 360장·leaf 420장의 두 combined mesh로 bake한다. 자체 생성한 4×2 atlas는 alpha 형태만 사용하며 Point/Clamp·128×64로 import했다. grass는 위쪽 source normal, leaves는 수관 ellipsoid normal로 실제 URP 조명을 받는다. 별도 저폴리곤 crown은 ShadowsOnly, 줄기는 static collider다. 전체 화면 픽셀 기능·기존 풀·Camera·Player·날씨 권위는 추가/교체하지 않았다. 자세한 사용법·자료·이미지 생성 prompt는 `Assets/Rendering/Foliage/README.md`에 둔다.
- `[기존 대표 시각 확인]` 초기 8fps/3단계 결과의 실제 기지 정오·밤·비 렌더를 확인했고 사용자에게 정오 결과를 보여드렸다. shader supported 3-pass·compiler message 0, Console Error/Exception/Assert 0이었다. 전체 한 바퀴·Player build·대규모 숲 GPU 성능은 검증하지 않았다.
- `[재개·시험 설정]` 끊김 후 파일/프리팹이 유지됨을 재확인했다. 카드별 ±7% 밝기 편차를 재질의 `Per-Tuft Brightness Variation=0`으로 제거하고, 풀·잎·reference ground의 direct-light shade steps를 2로, sprite fps를 0.4로 시험했다. 각 카드는 2.5초마다 형태를 바꾸지만 개별 phase로 시점이 흩어진다. 원본의 정확한 색 개수·2.5초 간격은 확인된 제작 공식이 아니다. 이전 모습은 fps8/variation1/steps3으로 복원할 수 있고 mesh/atlas는 보존했다. domain reload 시 명령 어셈블리 조회가 한 번 실패해 실제 재질이 fps8인 것을 읽은 뒤 준비된 Editor에서만 저장했으며 shader compiler/Console error 0을 확인했다.
- `[시각 미검증]` 후속 12.002초/48프레임 촬영은 게임 시간은 진행됐으나 플레이어를 따라간 카메라의 상대 위치에 오프셋을 더해 다른 구역이 잡혔다. 식생 시각 검증/합격 증거로 사용하지 않는다. 재촬영이 필요하면 player 상대 오프셋이 아니라 실제 prefab bounds에 framing해야 한다. Play는 종료했고 runtime background=false로 복구했다. 마지막 Edit Mode에서 GameMap1 dirty=true가 관찰되어 자동 저장/되돌림하지 않았다. 기존 scene 사용자 변경 14줄과 새 식생 instance 58줄은 분리해야 한다.
- `[최신 사용자 정정]` 나뭇잎 shader는 만족하므로 더 변경하지 않는다. 풀만 문제이며 원본이 흔들림·명암으로 두 색처럼 보였는지 확인을 요청했다. 현재 풀은 단색 albedo와 모두 위쪽인 normal로 균일 수광하며, wind는 alpha 형태만 바꾼다. 따라서 shade steps2만으로 풀 자체의 두 톤 변화가 생기지는 않는다. 원본의 정확한 두 톤 원인과 수정 방식은 미정이며 leaf에 함께 적용하지 않는다. 이번 상태는 시험/검토 중이고 최종 아트 완료 커밋은 보류한다.

---

## 125. 식생 환경 시험장·주광 합성·먹구름과 비 안개 `[ENVIRONMENT-01]`

- `[요청·자료][2026-09-05]` 승인된 잎을 보존하고 풀/명암·빛줄기를 환경 속에서 비교하도록 요청받았다. t3ssel8r Grass V2의 source terrain position/normal 조명, Godrays의 light-space shadow-map 샘플, David Holland 재현의 grass-depth 경계와 반복 depth blur 비용, Frostbite unified participating media를 비교했다. 전체 카메라 픽셀화는 계속 비활성이다. 원본 영상 타임스탬프를 직접 시청하지 못했으므로 정확한 색 개수·프레임 간격·미공개 셰이더와의 동일성은 주장하지 않는다. 구현/자료 경로는 `Assets/Rendering/Foliage/README.md`에 모았다.
- `[시험장]` 기존 `PrototypeSunShaftContrastTestArea` 하나를 재사용했다. 100×64m 안에 열린 바닥/막힌 지붕/5×6m 천창/슬랫 골목/큰 숲을 비교하며, 수관 약13m인 나무9개와 ground와 수광 기준·팔레트를 공유하는 풀을 배치했다. 공유 combined mesh를 Editor에서만 생성하고 기존 잎 material은 변경하지 않았다. 기존 Ground와 slab top이 y=0에서 겹쳤던 대량 줄무늬는 slab renderer만 숨기는 분리시험으로 확인한 뒤 top을0.01m로 분리했다.
- `[빛줄기 근본 수정]` 기존 적분에 실제 주광 Cookie를 샘플 위치별 한 번 반영했다. 24표본/16m 시험 높이, half-res RGB+view-depth와 full-res 깊이 대응 합성을 사용한다. 추가로 sun on/off 동일 프레임에서 확인한 가는 수평선은 point-depth 경계의 표본 행 불일치/고정 허용폭 문제였다. 적분과 합성이 같은 full-res texel 중심을 읽도록 맞추고, 양방향 깊이 기울기가 일치하는 평면에만 예상 깊이를 보정했다. 마지막 같은 카메라 렌더에서 해당 선이 사라졌다. 실루엣 허용폭을 무조건 늘리거나 전체 화면을 흐리지 않았다.
- `[날씨 단일 소유자]` `SkyLightingCycleController`의 기존 밀도장 G채널로 구름이 빈틈을 채운 뒤 비를 시작한다. Profile의 gather8초/강우fade0.75초, ESC 날씨 버튼은 즉시전환 대신 이 흐름을 호출한다. Cookie와 방향광의 Rain 감쇠 중복을 피하고 기존 Clear/Rain 광량을 하나의 예산으로 분리한다. 같은 비 강도를 기존 light renderer가 읽어 0~8m 공기층의 회색 extinction을 opaque depth까지 계산한다. 새 Manager·구름 레이어·카메라 픽셀 기능은 없다.
- `[Unity·Play Mode 호출 확인]` 관련 shader supported/컴파일 message0, profile validation 통과. 12.001초/25프레임 기록에서 4.002초 전환계수0.500/비0, 8.003초 계수1/비0, 8.502초 비0.745, 9.002초 비1/전환종료였다. 4초에 Rain을 반복해도 재시작하지 않았다. 별도 Clear 중단은 계수0.02328723을 즉시 유지한 뒤0·비0·전환종료로 돌아갔다. 맑음·비 안개 on/off와 열린 바닥/막힌 지붕/천창/숲을 실제 Camera.Render로 확인했다. 저각 천창 촬영은 차폐 진단용일 뿐 저장된 게임 카메라 각도는 바꾸지 않았다.
- `[검증 경계·보존]` 첫 촬영 명령은 Play 중 Editor 코드 수정으로 domain reload된 직후 static shell 조회가 null이라 시작하지 못했다. 게임 오류로 취급하지 않고 Edit Mode에서 저작 완료 뒤 새 Play로 한 번 재진입했다. 후속 촬영의 shader 수정은 C# reload 없이 해당 파일만 import했다. 반복 게임 한 바퀴·Player build·GPU ms·실내별 안개 배제·Transparent 차폐는 미검증이다. 기존 가로등/잎·Player/Camera 인스턴스 설계·세이브·씬 흐름은 유지했다. 미리보기 촬영만 runtime background 실행을 켠 뒤 복구하며, 기존 dirty scene/타 에셋은 자동 저장·되돌림하지 않는다. 기능 시험 체크포인트와 최종 아트 승인은 구분한다.

---

## 126. 강우 시작 광량 전환 수정·새 Chibi 4부위 외곽선 시험 `[ENVIRONMENT-01][CHARACTER-RENDER-01][MOVE-01]`

- `[원인·수정][2026-09-05]` 구름/기본 조명은 8초 동안 변하지만 햇빛줄기 억제와 회색 안개는 지연된 강수 강도로 마지막 0.75초에 몰려 변했다. `SkyLightingCycleController`의 기존 `CurrentOvercastCoverage`를 `StylizedLightShaftPresentation.ApplySunlight`에 전달해 두 대기 표현도 구름 진행도를 읽게 했다. 별도 날씨 소유자·보정 광원 없이 맑음/비 최종값과 비 입자 타이밍을 보존한다. 가로등의 국소 비 산란 배율은 기존 강우 연동 그대로다.
- `[Play Mode 호출 확인]` 12.005초/25프레임: 7.503초 coverage0.989/rain0, 8.003초 1/0, 8.502초 1/0.744, 9초 1/1·전환 종료. 비 시작 전후 고정 바닥/도로 4지점 RGB가 각각 (47,74,37)/(14,17,21)/(42,48,55)/(41,65,32)로 일치했다. 강우=1인 같은 프레임에서 비 renderer만 On/Off해도 해당 지점은 동일했다. 잎의 남은 형태·명암 변화는 기존 0.4fps 카드 애니메이션이며 승인된 잎 shader는 변경하지 않았다. 실제 Camera post-processing=false; 무관한 RenderGraph 경로 변경은 하지 않았다.
- `[모델 연결]` 기존에 사용자가 넣은 `ChibiKenneyRigReview01.prefab`(Humanoid 58bones, 9 SkinnedMeshRenderer)을 `PersistentGameplayShell/Player/CharacterSilhouettePlayerVisual`의 외형 자식으로 교체했다. wrapper 위치(0,-0.5,0), Player/Camera/HUD/Inventory와 이동·무기 스크립트는 유지한다. 원본 prefab/FBX/3개 Unlit 재질을 보존하고 기존 Spatial Flat Lit 설정을 복제한 gameplay 재질 3개에 원본 색·눈 atlas·양면 culling을 연결했다. Avatar만 새 본을 사용하고 Controller는 기존 `PlayerLocomotion`이다. 외형 밖 참조 두 곳(PlayerMovement/PlayerWeaponController.characterAnimator)만 새 Animator로 연결했다.
- `[외곽선]` Subject 한 개의 Inspector `outlineGroups`에서 눈2메시→1, 눈썹2→2, 헤어4→3, 피부1→4를 지정한다. 기존 공유 raw/quantized 버퍼의 채널만 확장하고 깊이를 통과한 실제 표면 ID를 읽는다. 같은 셀은 낮은 부위 ID 우선, 경계는 높은 ID 쪽 한 번만 합성한다. 미지정0은 통합 외곽선이며 좀비 screen-pixel 경로/루트 snapping은 유지했다. 재질 Cull의 기본값 Back은 유지하고 새 양면 모델만 Off로 사용한다. 개별 부위 카메라/RT·전면 색 픽셀화는 추가하지 않았다.
- `[최신 정정·원인 수정]` 사용자가 둥근 본체가 픽셀 선을 침범하고 굵기가 불균일하다고 지적했다. 합성 순서가 아니라 기존 최종식이 아트 셀 band를 버리고 raw 3D 경계의 1px erosion을 우선한 것이 원인이었다. Classic raw RGBA에 visible coverage/부위ID/루트셀 내 XY를 저장하고, 셀 내 어느 표면이라도 점유하면 해당 셀 전체를 채우는 보수적 coverage로 교체했다. `occupied - eroded(occupied)`의 한 아트 셀 안쪽 ring과 부위 경계를 같은 격자로 합성한다. `_InnerOverlapPixels`와 classic seed draw를 제거했다. 기본3px에서 mask조회9→25, classic geometry draw2→1이며 추가RT는 없다. GPU ms는 미측정이다.
- `[격자 검증]` 1/3/5/8px와 세 root phase의 순수 CPU12case에서 raw coverage 누락0·expected cell 불일치0·한 셀 내 ring 두께혼용0. 실제 Unity에서는 같은 frame의3px/5px 정면과 기본3px 쿼터뷰를 렌더해 제시했다. 기본값은3px로 복구했다. 새 mask/composite shader supported·compiler message0, Console error0이다. 서브픽셀 구멍·머리카락의 미세 오목부까지 컬러를 채우는 기능은 아니며 원본색 렌더를 그대로 둔다.
- `[검증]` 관련 셰이더3개 supported·compiler message0, Console Error/Exception/Assert0. 실제 Play에서 9개 renderer의 그룹값·58bones·valid Human Avatar·2 animation layers·두 소비자 참조를 확인했다. Animator 0/1/1.3과 상체 layer1을 호출하고 서로 다른 실제 프레임에서 대기/걷기/달리기/권총 자세를 렌더했다(`[CALL]`). 임시 가상 키보드 S/Shift 시험은 이동값0이라 입력 성공으로 기록하지 않는다. 포커스를 강제하거나 입력 구조를 바꾸지 않고 Animator 호출로 검사 범위를 제한했으며 임시 장치0·이동 스크립트 enabled·Player 위치 복구를 확인했다. GetInstanceID 구형 API를 쓴 첫 진단 명령은 Unity6.5에서 컴파일되지 않아 GetEntityId로 고쳤으며 게임 코드 오류는 아니었다.
- `[미검증·보존]` 수정된 균일 격자 정면과 날씨 GIF를 사용자에게 제시하고 아트 승인 대기다. 앞머리에 가린 눈썹은 드러나지 않으며, 먼 줌의 작은 부위는 한 셀로 합쳐질 수 있다. 원본 본/웨이트·머리카락 관통을 다시 저작하지 않았다. 실제 키보드 이동/전투 조작, 빌드·GPU 성능·왕복 세이브는 재검증하지 않았다. Player 생성/보존·씬 이동·저장 경계를 바꾸지 않았으므로 전체 게임 한 바퀴는 생략했다. Play를 종료하고 background=false로 복구했으며 기존 dirty GameMap1 및 다른 에셋을 저장/되돌리지 않았다.

---

## 127. Classic 잉크와 경계 색 재구성 분리 `[CHARACTER-RENDER-01]`

- `[사용자 정정·원인][2026-09-05]` §126의 한 셀 ring은 격자가 일정하다는 뜻일 뿐 한 줄처럼 읽힌다는 보장이 아니었다. 셀 전체 검은 띠와 8-neighbor erosion은 좁은 부위를 검게 만들고, 낮은 부위 ID 우선은 소수의 눈/눈썹 표본이 셀 전체를 차지하게 했다. 이전 CPU 격자 검사는 이 시각 실패를 검증하지 못했다.
- `[수정]` 같은 RendererFeature와 루트 snap을 유지한다. 보수적 셀 coverage의 빈 공간은 면적→중심 거리로 선택한 동일 visible 부위의 실제 lit color로 채우고, 이미 보이는 눈·눈썹·헤어·피부 픽셀은 보존한다. 외곽은 4-neighbor native1px, 내부 그룹 경계도 한쪽1px로 한 번만 합성한다. 전체 몸체 색 저해상도화·하드코딩 피부색·새 카메라는 없다. RGBA8 quantized mask에 source offset을 저장하고, native lit source copy1회를 Classic/ScreenPixel이 공유한다. Classic도 intermediate color/depth를 요청한다. GPU 비용은 미측정이다.
- `[가림 순서]` 첫 시각 확인에서 선을 추출한 뒤 depth clip하면 낮은 정면 각도에서 선이 끊겼다. 직교/원근에 맞게 깊이를 환산하고 가림을 quantized mask 단계에서 먼저 확정한 뒤 잉크를 추출하도록 순서를 바꿨다. 실제 가려진 공간을 채우거나 벽 위에 테두리를 강제로 덧씌우지 않는다.
- `[검증]` Unity shader compile 오류0, 기지 실제 Camera의 정면/쿼터와3/5px 대표 렌더를 수행했다(`[CALL]`). CPU 수동 대응 회귀18개는 면적/동점·source group/cell1,800위치·원본 내부49위치·좁은3px띠·한쪽 선·metadata·직교 depth를 확인한 것이며 GPU/시각 합격을 대신하지 않는다. 이후 가림 선행 변경은 실제 재촬영으로 확인했다. 임시 진단에서 asset Material에 실행 중 RT를 GetTexture로 조회해 texture-property 오류를 냈으며 게임 셰이더 오류와 구분한다. Console을 지우지 않았다.
- `[경계·승인]` 정면과 대각선 PNG를 제시했다. 두꺼운 셀 ring은 제거됐지만 정면의 미세 오목 경계에는 거친 구간이 남아 있어 완전 해결/아트 승인으로 기록하지 않는다. 기본 계단3px·잉크1px, 보수적 확장 자체의 최대 축당2px 오차는 유지한다. 원본 파츠·텍스처·조명·Animator·이동·Player 수명·씬·세이브는 변경하지 않았다. GPU Profile·Player build·캐릭터 접촉/Transparent 차폐는 미검증이며 전체 게임 한 바퀴는 생략했다.
- `[정리]` 촬영 후 Player 위치(0,0.5,0)·movement enabled·기본 grid3 복구를 확인했다. Play 종료·background=false·GameMap1 dirty 유지이며, 기존 사용자 씬/재질/preview prefab 변경은 저장하거나 되돌리지 않았다.

---

## 128. Chibi 눈·헤어 선택 팔레트/명암 단계와 픽셀 색 시험 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-06]` Canva 예시처럼 연속 그라데이션을 소수 색으로 정리하고 현재 캐릭터 눈·헤어부터 실제 셀 색과 경계선을 시험한다. 전체 카메라 효과·원본 atlas/FBX·본·Animator·피부 내부·눈썹 크기·게임플레이/저장은 변경하지 않는다. 눈썹/피부도 선택 부위와 공유하는 경계 셀에는 영향을 받을 수 있다.
- `[조사]` [Canva](https://www.canva.com/ko_kr/create/pixel-art/)는 Pixelify와 AI 생성/편집을 함께 소개하지만 내부 공식을 공개하지 않는다. [Unity Posterize](https://docs.unity3d.com/Packages/com.unity.shadergraph@17.3/manual/Posterize-Node.html)의 단계화와 [Palette Limiter](https://godotshaders.com/shader/palette-limiter-shader/)의 최근접 팔레트 선택은 공간 격자와 별개다. [pixelism](https://github.com/longod/pixelism#discussion)의 프레임별 팔레트 변화 문제를 참고해 이번 팔레트는 원본에서 한 번 추출/고정한다. 외부 코드/패키지를 복사·설치하거나 Canva와 동일한 알고리즘이라고 주장하지 않는다.
- `[색 책임]` `CharacterFlatUnlit`에서 tint 적용 albedo를 sRGB 거리로 팔레트 하나에 대응시킨 뒤 기존 공간 조명을 적용한다. 눈 메시의 실제 UV 삼각형을12등분 표본화한 원본 색5,478개에서 darkest→farthest RGB 방식으로8개 실제 texel을 선택했다. 평균색은 생성하지 않았다. 저장 팔레트는 `150400/604134/79665D/B57E55/AA988B/D1BBAC/F1DDCB/FFFEF6`. 헤어는 원래 단색 재질이며 텍스처나 가짜 머리카락 음영을 만들지 않았다.
- `[명암 책임]` 두 재질의 `Lighting Bands=5`, `Lighting Band Range=1.2`: 기존 합산 조명의 luminance를0/.3/.6/.9/1.2로 반올림하고 동일 비율을 RGB에 적용한다. 0은0, 1.2 이상은 원래 HDR 광량을 유지한다. 로컬광 색 유지 때문에 최종 RGB 전체가8×5색으로 한정되지는 않는다. 밴드 경계의 시간 변화는 여전히 이산적이며 별도 temporal history/dithering은 없다. 각 재질의 Palette Count/Lighting Bands=0은 기본 off다.
- `[공간 책임]` 기존 Subject의 `outlineGroups.pixelColor`로 눈2/헤어4 renderer만 선택한다. Player의 `classicPixelSizeOverride=5`, 나머지 Subject0(공유3px)이며 루트 snap을 유지한다. raw/quantized RGBA8의 G에 group/선택/크기를 pack하고 BA에 remainder/고정 bias7 source offset을 전달한다. 선택 셀은 실제 면적 우승 부위의 중심에 가장 가까운 lit sample 하나로 채운다. 셀 색과 경계선이 같은 최종 group을 읽고 선은 마지막 한쪽1px이다. 다른 격자 후보를 covered 셀로 끌어오지 않게 검사한다. 추가 RT·카메라·Manager는 없다. covered 셀은g², 빈 경계는최대(2g−1)² 후보 검색이며 GPU 시간은 측정하지 않았다.
- `[검증]` Unity C# 사용 명령 컴파일 성공, 실제 대표 렌더 이후 shader3개 message/error0, Console Error/Exception/Assert0. metadata80개·source offset2,040개 CPU 왕복 검사는 byte 계약 확인이며 시각 합격을 대신하지 않는다. GameMap1 직접 Play에서 전후 정면, 대각선, 실제 게임 거리, 밤과 Animator `LocomotionSpeed=1`의 서로 다른12프레임을 캡처했다(`[CALL]`). 처음 대각선 촬영은 원래 카메라 뒤쪽 각도여서 얼굴 비교에 부적합했으며, 다른 격자 후보 검사 추가 후 정면쪽 대각선으로 최종 촬영했다. 첫 import 명령은 C# reload 중 MCP 동적 타입을 찾지 못했고, 컴파일 종료 확인 후 정상 수행했다. 게임 오류로 기록하지 않는다.
- `[승인·한계]` 실제 PNG/걷기 프리뷰를 제시하고 질문 도구로 의견을 요청했다. 큰 셀에서 작은 눈 디테일이 줄고 기존 실루엣 미세 톱니가 더 드러난다. 앞머리의 물리적 가림 때문에 높은 각도에서 눈/눈썹이 가려질 수 있다. 이를 완벽한 픽셀화나 아트 승인으로 기록하지 않는다. 다른 Subject가 동일 셀을 공유하는 경우의 식별, Transparent 차폐, 확대/축소 전 범위, GPU profile·Player build는 미검증이다.
- `[보존·정리]` 촬영 종료 후 동일 Player entity와 위치(0,.5,0), movement enabled, background=false를 확인하고 Play를 종료했다. GameMap1 Editor dirty=false이며 기존 디스크의 사용자 변경은 보존한다. 원본 UV/texture/filter/import 설정과 source prefab은 보존하고 gameplay eyes/hair 재질 및 Player wrapper override만 저장했다. 전체 한 판 테스트는 하지 않았다.
- `[사용자 불합격·최신 정정]` 사용자에게서 몸체 도트가 과대하고 선과 셀 크기가 다르며 곡면 경계가 상어 이빨처럼 들쭉날쭉하다는 피드백을 받았다. 5px 색/실루엣 격자와 native1px 잉크의 단위 혼용, 선택 부위뿐 아니라 Player 공유 실루엣까지 키운 설정을 잘못으로 인정했다. 아트 승인/완료가 아니며 추가 렌더 수정·커밋을 중단했다. 톱니의 정확한 GPU 원인은 미확정이다. 같은 셀 안에서 native 보존/확장/깊이 판정이 분기되는 현재 구조와 공통 최종 셀 표현을 구분해 재설계해야 한다. perfectPixel은 기본 center 샘플이며 majority는 RGB K-means2 군집 중 다수 군집의 평균색, median은 채널별 중앙값이다. 전역8색 팔레트나 의미론적 눈 인식 알고리즘이 아니다.

---

## 129. Chibi 빈칸 판정과2px 공통 셀 표면 `[CHARACTER-RENDER-01]`

- `[요청·원인][2026-09-06]` 사용자는 작은 굴곡에 걸친 칸을 무조건 채우지 말고 빈칸 결정을 넣어2×2부터 빠르게 비교하도록 정정했다. 기존 경로는 native 둥근 몸체가 먼저 그려져 EMPTY 결정으로 지울 수 없었고 보수적 확장·1px 잉크·fragment별 깊이를 섞었다. 단순 크기 변경으로 이 계약을 해결하지 못한다.
- `[수정]` 기존 Subject/RendererFeature 안에 opt-in `pixelCellSurface`를 추가했다. source pass가 루트 기준 칸 중앙에서만 원래 공간 조명 색을 평가하고 RGBA16F(RGB/eye depth), RGBA8(16bit Subject ID/부위/칸 크기), private D32 self-depth를 기록한다. native Forward/DepthOnly는 이 대상만 제외한다. 중심 표본 없음=EMPTY, 있음=같은 색의 정사각 셀이며4-neighbor 외곽/한쪽 부위 경계는 같은 격자의 한 셀 잉크다. 몸체 아래 native 컬러를 남기거나 외부로 무조건 팽창하지 않는다. 눈8색·눈/헤어5명암 시험과 원래 조명 수식은 유지한다.
- `[깊이·소유권]` cell은bit28, 기존 Classic29/Screen30과 배타이며 공통31은 보존한다. transient16bit ID는 활성 Subject만 소유/반환한다. source/self-depth→기존 resolved depth의R32 복사→cell MRT 색/깊이→기존 camera-depth handle로 format별 copy-back 순서다. 동일 Feature의 cell 패스301은 legacy550와 분리해450의 로컬 체적광/투명 효과보다 먼저 색·깊이를 제공한다. 별도 Camera·Manager·저장 상태는 없다. 중앙 기준 월드 차폐는 셀 내부를 다시 native 조각으로 자르지 않으며 연속 물체 경계와 최대 반 칸 정도 오차는 남는다.
- `[정리]` 실패한 `classicPixelSizeOverride`, `outlineGroups.pixelColor`와7개 prefab override를 제거했다. Player wrapper에cell opt-in을 저장했고 default2px를 쓴다.9개 SkinnedRenderer·4부위·원본 모델/재질 참조·Animator controller·이동/달리기/Player 수명은 보존했다. Classic/좀비A/B 알고리즘은 변경하지 않았다.
- `[검증·CALL]` GameMap1 직접 Play1회, 같은 프레임/동일 자세의2px·3px 정면과2px 쿼터/실제 게임 거리, 실제 Animator 걷기8프레임을 촬영했다. 전후 Player entity `568105589213733838` 동일, 위치(0,.5,0),movement enabled,2px 복구를 확인했다. 두 shader supported/messages0, Console Error/Exception/Assert0. Play 종료·compiling=false·Editor GameMap1 dirty=false·background=false. CPU 격자/ID/깊이 수식 검토는 GPU·외형 합격과 구분한다. 전체 게임 한 바퀴나 씬 전환 반복은 하지 않았다.
- `[사용자 선택]`2px/3px 실제 PNG 제시 후 사용자가 “2x2가더나아”라고 답해2px를 유지했다. 이후 외형을 임의 보정하지 않았다. 최종 아트 전체 승인이나 모든 상황의 톱니/깜빡임 해결을 의미하지 않는다. 다중 대상 겹침·전체 줌/회전·날씨 조합·Editor preview·GPU profile·Player build는 미검증이며 별도 후속 승인 없이 확대하지 않는다.

---

## 130. 몸체를 보존하는 바깥 한 셀 외곽선 `[CHARACTER-RENDER-01]`

- `[사용자 정정·확정]` §129의3px 손이 살색 없이 두 줄의 선으로 보인다는 피드백으로 커밋을 보류했다. 원인은 색 셀을 먼저 만들고도 빈 이웃을 가진 body 셀 자체를 잉크로 치환한 inward erosion이었다. 사용자는 바깥으로 한 셀을 추가하도록 명시했다.
- `[원인 수정]` Chibi `FragPixelCell`은 실제 body를 먼저 확정한다. body가 없을 때만 `ResolveOuterPixelCell`이 실제 source의8이웃 한 셀을 검색해 `Dilate8(Body)-Body`를 그린다. 새 링 중앙에서도 공급 body의 깊이를 월드와 비교하므로 공급 셀만 보인다고 벽 위로 선을 그리지 않는다. body 셀은 총외곽선으로 치환하지 않고 기존 내부 부위 선만 별개로 유지한다. 외부 링 출력은 다음 링의 source가 아니므로 재팽창하지 않는다. 기본2px/공통격자/기존 MRT/깊이 copy-back/원본 모델/애니메이션/조명은 보존했다.
- `[좁은 검증·CALL]` GameMap1 Play1회에서 같은 프레임2px·3px 정면,2px 쿼터/게임 거리4장을 촬영했다.3px에서도 손의 살색 셀이 남는 결과를 제시했다. 걷기 반복·전체 한 판·씬 전환은 수행하지 않았다. shader supported/messages0, Console Error/Exception/Assert0. 전후 Player entity `568105589213729886` 동일, 위치(0,.5,0)/movement enabled/기본2px 복구 후 Play 종료. CPU 단일/가로2/세로2셀은 body와 외부 링의 교집합0을 확인한 최소 논리 검사이며 디자인 합격을 대신하지 않는다.
- `[승인·경계]` 실제2px/3px 미리보기와 질문을 제시했다. 이번 바깥 선의 외형 승인 대기이며 임의 추가 보정하지 않는다. 다중 캐릭터 접촉·줌/회전 전범위·GPU profile·빌드는 미검증이다. 빈 화면의 외부 검색은 최대(3g)² seed 조회이며 다수/큰g의 비용을 측정했다고 주장하지 않는다.
- `[커밋 경계]` 최종 관련 diff에서 헤어 재질의 명암 단계가0(off)인 현재 값을 확인했다. 외곽선 작업에서 이 재질을 수정하지 않았고 기존5단계 설명으로 덮어쓰지 않는다. 헤어 재질의 미커밋 변경은 보존·stage 제외하고 현재 GDD에만 실제 값을 반영한다. 현재 셰이더의 기본 단계 값도0이므로 이 파일은 새 렌더 경로의 필수 변경이 아니다.
- `[후속 사용자 확인]` 사용자가 바깥 한 셀 방식에 “딱좋아”라고 답했다. 현재2px 외형은 유지하되 발밑 일부 외곽선이 사라지는 현상을 별도로 지적했다.
- `[참고 메모·미수정]` 발밑 선 소실의 유력 원인은 바닥 가림 판정이다. `Assets/Rendering/CharacterPresentation/CharacterSilhouetteComposite.shader`의 `ResolveOuterPixelCell → IsPixelCellVisibleAt`은 외부 셀에 가까운 몸체 셀의 깊이를 전달한 뒤 새 셀 중앙의 월드 깊이와 비교한다. 발 아래로 확장된 셀에서는 바닥이 더 앞에 있다고 판정되어 선이 제거될 수 있다. 원인 분리 GPU 검증은 아직 하지 않았으며, 격자/색 셀 생성 실패로 확정한 것이 아니다. 향후 검토 후보는 접지면에서의 외곽선 깊이 처리와 벽 차폐의 구분이다. 모든 외곽선을 무조건 맨앞에 그리는 변경은 벽 투시를 만들 수 있다. 사용자 요청으로 기록만 남겼으며 코드 수정·추가 테스트·자동 후속 작업은 하지 않는다. 이 메모는 개발 지침이나 확정된 해결 방법이 아니다.

---

## 131. 우클릭 드래그 자유 시점 `[CAMERA-01]`

- `[요청·2026-09-06]` 캐릭터 얼굴/픽셀 렌더를 여러 각도에서 확인할 카메라 조작. 사용자는 우클릭을 놓아도 바꾼 시점을 유지하도록 확정했다. 모델·크기·애니메이션·회전 기준·세이브는 바꾸지 않는다.
- `[구현]` 기존 `CameraFollow`가 최초 offset을 camera space에 저장하고 yaw/pitch 회전을 적용해 동일 Player 프레이밍을 보존한다. 감도0.2°/pixel, pitch10~80°, 마우스 변위에 deltaTime을 곱하지 않는다. 최초 구도를 자동 변경하지 않으며 `Reset View`는 현재 Play의 최초 시점을 복원한다. 기존 Gameplay map에 `CameraOrbit`(RMB)·`CameraLook`(mouse delta)만 추가하고 기존 action/binding ID·줌을 보존했다. 사용자 설정의 현재 RMB 지정은 CameraOrbit 하나임을 확인한 뒤 RMB를 일반 재지정에서 제외했다.
- `[입력·수명]` UI 포인터 위 시작, Inventory input block, Escape, travel prepared와 pause 중 차단. 놓기·비활성·포커스 상실 시 커서 lock/visible을 이전 상태로 복원하되 선택한 시점은 유지한다. CameraFollow/기존 InputActions만 사용하고 새 Camera·Manager·UI·저장 상태를 만들지 않는다. 기존 CameraFollow의 CP949 주석 인코딩은 UTF-8로 변환했다.
- `[좁은 검증·CALL]` 최종 코드 대표 Play에서 가상 Mouse state→InputSystem.Update→동일 CameraFollow.Update/LateUpdate 호출로18개 결과를 확인했다: RMB 시작/회전/놓기 유지, pitch10/80, Player 화면 좌표 보존, UI/ESC 차단, 포커스/disable 커서 해제, 최초 시점 복원, 동일 Player entity/transform, 기존 사용자 key 검증과 휠 binding 보존. 실패0. 재바인딩 후보 RMB는 저장 전 검증에서 거부한다. 실제 하드웨어 드래그·휠 연속 조작이나 Player build를 통과했다고 기록하지 않는다.
- `[미리보기·정리]` 실제 GameMap1 카메라의 기본 시점과 낮은 정면을 PNG로 촬영해 제시하고 사용자 감도/각도 의견을 요청했다. 앞의 좀비가 몸체를 가리는 정상 깊이 판정은 유지한다. offset(2,10,-10), Euler(45,350,0), cursor None/visible=true, background=false 복원 후 Play 종료했다. 입력 binding 확인용 초기 Play 진입1회는 코드 검토 후 종료했고 대표 검증은 최종 코드에서1회 수행했다. 씬 전환 전체 한 판·렌더 전방위/GPU 검증은 반복하지 않았다. 사용자 dirty 씬·재질·preview prefab은 수정·stage 대상이 아니다.
- `[사용자 승인·마감]` 사용자가 현재 값을 그대로 커밋하도록 승인했다. 이후 외형·감도 추가 조정은 하지 않았다. 최종 Console Error/Exception/Assert0, 관련 경로 diff whitespace 오류0을 확인했다.

---

## 132. 웹 픽셀 수학 기반 실시간 적응형 명암 시험 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-08]` 수정된 웹/Python 알고리즘의 수학으로 Unity 픽셀 렌더를 다시 구성해 개선 가능성을 시험한다. 오프라인 PNG 처리의 반복이나 생성형 아트 교체가 아니다. 이전의 고정 팔레트/균등 명암 단계가 같은 알고리즘이었다고 주장하지 않는다.
- `[구현]` 기존 캐릭터 RendererFeature의 셀 source→composite 사이에 opt-in GPU 분석을 추가했다. 원본 해상도 무광 source의 Subject/부위 ID + 정규화 Oklab 색 계열, 적응형32-bin 관측색 histogram, uint64-pair moments, 단계 수 가변1D DP, 4×4→2×2 공간 대비 guard와 근거 있는 밝음 후보를 사용한다. 원본 RGB 후보만 선택하며 source 셀 위치·ID·깊이·몸체·외곽선은 바꾸지 않는다. 정상 렌더는 CPU readback 없이7 compute pass와 transient 자원을 쓴다. Chibi prefab의 시험 bool과 PC_Renderer의 compute 참조/수치만 추가했다. 다른 모델·재질·본·Animator·게임플레이 및 기존 전체화면 효과는 보존했다.
- `[한계·명시]` 연결 성분/관측 중심 covering/다중 Gaussian을 그대로 옮긴 것이 아니라 부위 경계·색상 격자/32bin/공간 타일로 제한한 이식이다. disconnected 같은 계열은 통계를 공유할 수 있다. 한 캐릭터/160그룹/4MP 자원 상한과 실패 상태를 명시한다. 현재 머리카락의 약한 밝음이 사라지는 차이는 남아 있으며 임의 재보정하지 않았다. 시간 누적·팔레트 안정화·다중 캐릭터·빌드는 미검증이다.
- `[GPU 검증]` Unity6000.5.9f1/URP17.5/D3D11/RTX2080Ti. 독립 CPU·fixture·검증기 검사22개 통과. 실제 GPU7case중6개 전체 통과, four_observed_levels는K4·RGB·깊이·ID 보존 통과지만 보고 RMS가9.16e-5로 엄격3e-5 비교를 실패했다. 실제 palette 오차는약6e-8이며 float moment 상쇄의 연산 오차 범위 안이다. 실패summary를 그대로 보존했고 허용치를 임의 상향하지 않았다. 현행.06/시험.001 판정은 동일하나 극소 오차 제어는 제한이다. 실제RGBAHalf/RGBA32 broad-gradient 추가1case도 통과했다.
- `[Play·CALL]` GameMap1 Play1회, 같은frame2의 실제Player/Camera로 정면·45도×기존/연속입력/적응형6장을 촬영했다. 동일Player entity568105589213736218·Camera568105589213735872·위치·프레임·재질 참조·2px와 임시 조명/카메라/Time 복원을 확인했다. 이후 배경 실행을 임시 허용해 실제frame5869의936×857 렌더에서 READY6그룹(global0, 공간guard1)을 확인했다. 추가7compute의 단일측정 GPU .354304ms / CPU .0555ms / inlineCPU .0103ms이며 추가source raster·합성·전체프레임 비용은 제외한다. 이동 입력·씬 전환·장시간 깜빡임 검증으로 확대 해석하지 않는다.
- `[컴파일·복구]` 첫 FXC 컴파일의 과도한 루프 확장으로 메모리가 급증해 이 프로젝트 소속 컴파일 worker만 확인 후 중단했다. [fastopt][loop]로 연산/동기화는 유지한 채 컴파일러 확장을 제한하여 최종shader와7커널의 오류/경고0을 확인했다. 해결 전 worker중단 Console오류4건은 삭제하지 않았다. Play 종료·background false·profiler off·GameMap1 복원. 원래 조명 feature의 Create()가 메모리에서 변경한 depth bind 직렬화는 이번 diff에 섞지 않고 작업 전 저장값을 Editor API로 보존했다.
- `[저장·미리보기]` 시험 기능을 다시 사용할 수 있도록 Chibi/PC_Renderer의 두 opt-in을ON으로 저장했다. 두 옵션OFF가 기존 방식이며 다른 기능으로 대체하지 않는다. 최종 외형은 사용자 판단 대기. 간단 설명/제한/재현은 `docs/ai/CHARACTER_ADAPTIVE_TONES.txt`, 원본6PNG·비교PNG·GPU원본/summary·수치감사·실행명령은 `LocalOnly/AdaptiveToneUnityReview_20260908/`에 보존했다.

## 133. 헤어 수광량 기반 명암 단계 비교 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-09]` 몸의 현재 낮밤/조명 반응은 보존하고, 헤어 명암의 간헐 단색화를 실제 조명 범위로 판정하도록 수정해 비교 사진 제공.
- `[구현]` 기존 native source의 Hair(part3)에만 albedo/specular 합성 전 diffuse 수광 Y를 별도 MRT로 기록. 기존 URP SH·주광·추가광·거리·그림자·cookie 및 프로젝트 local light 사용. 새 hairLighting 스위치로 기존 경로와 비교하며, OFF 시 추가 MRT 할당 없음. 원래 PBR색·재질·메시·눈·몸·2px·시드·외곽선·깊이 계약은 보존.
- `[수학]` 헤어 histogram/후보/DP/공간 보호/밝음/resolve를 같은 수광 단위로 계산. 허용 RMS=max(meanE, .02)×.10, 대비 하한도 같은 광량 scale로 환산. 최종 RGB는 관측 원본 후보이며 강제3색/야간 증광은 없음. 다른 부위는 기존 Oklab L 판정. invalid native illumination은 status64, sparse mismatch는 기존 resolve-only32.
- `[GPU 호출 확인]` 독립 수학9검사 통과. D3D11 실제 합성6case 모두 통과: day K2→3, night K1→3, albedo×4 K3 동일, flat E K1. 몸 RGB 전후 최대차0·depth/empty/meta/source/lighting 보존 및 관측RGB 소속 확인. 야간/주간 출력평균 .11999052(입력 .12배). 이는 아트 합격이나 실제 움직임 검증이 아님.
- `[실제 렌더]` 동일 Player568105589213712708/Camera568105589213712362·Play frame2·정면yaw180·2px·384×768, dim/bright×source/old/new6장. 자세·재질·카메라·조명·Time·compute 참조 전후 동일 및 복원 확인. captureRecords nested DTO만 JsonUtility가 누락하여 최초 manifest와PNG는 보존, 재현 스크립트의 레코드 형식을 string[]로 교정. 재촬영/이미지 색 보정 없음.
- `[종료]` Play off·GameMap1 dirty=false·background=false. adaptive는 기존ON, 새 hairLighting은 승인 전OFF로 복원. 최종 관련3shader/compute 메시지0, Console오류4개는 이전FXC기록. 릴레이 연결 경고1이 추가됐으나 후속MCP 상태조회는 정상 응답. 기존 dirty6파일/미추적에셋·씬/재질/prefab/renderer 저장값 보존.
- `[제한·증거]` 정지 정면 비교까지이며 temporal history/hysteresis·동작 중 명암 안정성·성능·빌드·유색광 그룹변화는 미검증. 사용자 시각 승인 대기. 전체 비교와 재현/GPU원본/summary는 `LocalOnly/AdaptiveToneHairLighting_20260909/`, 옵션 설명은 `docs/ai/CHARACTER_ADAPTIVE_TONES.txt`. GitHub 읽기 조회에서149개 로컬커밋 미업로드를 확인했으며 push는 하지 않음.

## 134. 실제 GPU 계측과 피부 수광 상대오차 수정 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-09]` 수정 전에 꺼지는 지점의 실제 광량/렌더 수치를 시험하고 방법을 확인. 계측 중 사용자가 필요한 수정을 허용했다. 기존 모델·색·2px·본·이동·씬은 보존하며 화면 전체 색 보간은 추가하지 않는다.
- `[계측]` 일회성 지정 Camera capture API로 실제7compute의9buffer와6RT를 소유byte 배열로 복사한다. captureId/Unity frame/native→seed→output을 연결한다. 진단 OFF 자원/readback 없음. 완료된 실제110캡처: 초기 광량32·무효 정적walk32·본행렬 갱신 walk32·paired 수정비교14. 지정Camera가 렌더되지 않으면 pending이 남는 제한은 문서화했다. 진단 전용 체크포인트는70bc8b8이다.
- `[원인]` 광량32표본의 Skin key360833/count65893에서 scale .143618→.126758, K2→1. 고정 허용오차 .06에 대해 K1 GPU RMSE .0592396, CPU .0592398; 공간guard는 전후OFF라 새로 꺼진 guard 때문이 아니다. 유효Walk17→18→19는 K3→4→3, CPU 강제K3 오차 .059691→.060042→.057266. 작은 오차 문턱 왕복이 전체 분할/대표색을 재배치한다. 큰Hair는32포즈 모두K4지만 작은Hair는K2여도 희소seed에서실색2→1→2가 있었다. GPUglobal0이며 이 증거를 일반 TAA 필요나 전체 렌더 실패로 해석하지 않는다.
- `[수정]` Skin(part4)에만 선택 가능한 skinLighting/skinRelativeError=.10/skinIlluminationFloor=.02 추가. 원래 RGB와 별도로 기록한 수광E를 histogram/DP/공간대비/밝음/Resolve에 일관되게 사용하고 RMS=max(meanE,floor)×relativeError. Hair기능·다른부위·관측RGB·격자·깊이·7kernel/FXC제약은 유지. 고정K·자동증광·시간이력은 추가하지 않았다. 저장된 두수광옵션은OFF로 보존, 후보 외형 사용자 확인 대기.
- `[검증·GPU/CALL]` Skin합성6case 전부통과: 주야E K3, 평탄E K1, albedo×4 K유지, 타부위RGB/깊이/입력/관측색보존. 분석기14test·독립상대오차수학9test 통과. 실제white광량4조건과Walk3포즈 각각 동일frame/Camera에서before/after14캡처. 7pair 모두native RGB/E/meta/seed exact·타부위output exact·depth exact·global0/READY. 저광량두조건1→3색, Walk3·4·3→4·4·4. 해당 두Walk전환의 선형RGB팔레트Hausdorff .310/.372→.00183/.00109. L과E오차는 서로 다른 단위이므로 수치크기로 직접 우열판정하지 않는다.
- `[실패·복원]` 초기동기walk32는 같은frame에서 skin행렬이 재사용되어모두같은PNG, 움직임근거에서제외. 공식 forceMatrixRecalculationPerRender를 임시ON/복원하여본pose와PNG차이를확인한새32개만사용. 최초sweep8의bitwise pose실패는직접원인미확정; 새walk첫2는quaternion약6e-8차이를기록했고후속30은위치/scale/부모exact·회전거리≤1e-6와poseBitwiseEqual을별도표기. 실패기록을성공으로덮지않음. 수정후첫준비전Play의readable mesh오류는출력/상태변경전중단, 준비된같은모델로후속paired통과. import설정은바꾸지않음.
- `[경계·저장]` 통제된정면384×768/2px/white그림자없는촬영이며 실제이동입력·물리·전체시간주기·구름/유색광·다중GPU/성능/빌드통과가아니다. 전후각Play안에서Player/Camera동일, 임시조명0·Time1·원래옵션복원후Play종료. 사용자기존dirty6파일과미추적외부에셋보존. 원시자료·제외표본·재현명령·분석·PNG·핵심GPU archive/SHA256은 `LocalOnly/AdaptiveToneTemporalProbe_20260909/`에 보존한다. 후속후보는검증된이전분할유지/히스테리시스이며미구현이다.

## 135. 현재 오차를 지키는 명암 분할 이력 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-10]` 간헐 단색화/깜빡임 원인을 조사한 뒤 실제 수정하고 로컬 커밋. 이전 조사 체크포인트는 b0b2955. 광원 교체·성능 최적화는 제외하며 원본 관측 RGB·2px·EMPTY·외곽선·깊이·Player/Camera를 보존한다.
- `[구현]` 기존 compute/pass에 ColorKey+metric 기준의 GPU 분할 이력을 연결했다. 이전 경계를 현재32bin 평균에 대응하고 현재 후보로 RMS/공간대비를 재검사한다. 통과 시 유지, 실패 시 현재 DP; 감소만 ε×(1−.10), 증가/실제조명변화에는 원래 기준. 빈 구간/실제 평탄 입력은 K1 허용. 이전 RGB 저장/보간·임의 밝은 셀 생성 없음.
- `[소유·수명]` 카메라별 double-buffer를 기존 pass가 소유하고 subject객체/ID·설정·해상도/격자·투영·Play·frame gap·큰cut을 무효화한다. 같은frame read는 고정; Resolve 뒤 별도 StoreHistory로 D3D11 8UAV 준수. Feature Create/Dispose에서 해제, 제어 캡처 원복용 ResetAdaptiveToneHistory 공개. 정상 CPU readback 추가 없음.
- `[실제 GPU]` Unity6000.5.9f1/URP17.5/D3D11/RTX2080Ti에서 17case 기술 불변조건 통과. 원시6표본×history OFF/ON, 합성5case. 현재 관측 RGB·depth·EMPTY·타subject 보존, static 반복 exact·무효이력=fresh·평탄K1. 걷기17/18/19 피부 출력3/4/3→3/4/4. 작은Hair key295810 출력2/1/2→2/2/2, 중간14seed 중3개의 분류가 변경됨. 밝은 native 위치의 seed 누락 복원으로 해석하지 않는다.
- `[렌더·실패]` C# 컴파일 성공, 최종 compute 메시지0. 자연 렌더6표본은 실제0개/30초 timeout으로 실패하여 연속이동 검증에서 제외; observer handler 해제. 앞선 진단 스크립트의 delegate형식 오류·금지된 reflection은 실제 상태변경 전에 중단하고 제거했다. 코드리로드 뒤 static shell 없는 초기 Play는 종료했다. 최종 Camera.Render 1회 frame1/global0 및 game_preview.png 확보; 이는 CALL 정지렌더이지 연속프레임 성공이 아니다. 카메라 원복·명시 이력reset, pending은 해당렌더로 완료하고 Play 종료했다.
- `[보존·미검증]` hairLighting/skinLighting 비교옵션은 이전OFF 그대로, temporalStability=true. 사용자dirty6에셋/씬과 미추적외부에셋은 변경·stage하지 않는다. 전체이동/구름/유색광 깜빡임, 카메라 수명 실시간 검증, 다중GPU/빌드/성능·시각승인은 남았다. lit-chroma 그룹경계·guard/highlight threshold·32bin 근사·희소Hair는 별도 한계. 방법·재현·실패자료는 docs/ai/CHARACTER_ADAPTIVE_TONES.txt 및 LocalOnly/AdaptiveToneStability_20260910/에 보존한다.

## 136. 명암 등치영역의 생성·축소·대표색 시간 전환 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-10]` 사용자가 지적한 K2/3/4/1의 한 프레임 교체를 줄인다. 구름의 연산을 가져오는 것이 아니라 단색 영역이 덮이거나 물러나는 현상을 별도 알고리즘으로 시험한다. 기존2px·바깥1셀선·EMPTY·깊이·모델·실제 광원·Player/Camera는 보존하고 구름/날씨와 최적화는 변경하지 않는다.
- `[구현]` 기존 DP는 목표를 계산하고 새 UpdateRegions가 밝기 순서의 구간 대응·경계·RGB·scale·밝음 support를 보관한다. K 변화는 이전/목표 rank의 단조 공통 세분화로 출발색/도착색을 공유해 생성·합침, .25초 유한 전환 중 topology 고정 후 압축. 같은 K는 exp(-dt/.25) 응답. support .5 즉시 gate 대신 밝음 cutoff가 이동한다. 새 모드에서는 시간상 대표색 보간을 허용하지만 공간상 단색을 유지하며 화면 픽셀 평균/TAA는 없다. 현재 관측 RGB 전용은 이전 모드 계약이다.
- `[소유·입력]` 기존 pass의 camera/subject별197행×160그룹 double-buffer, 정상 CPU readback 없음. UpdateRegions는7UAV와이전SRV, Resolve는신규SRV. albedo chromaticity를 기존 nativeLighting의gb에 기록해 조명색 변화로 그룹 정체성이 바뀌는 경로를 분리한다. 같은frame 중복 시간진행 방지, pause dt0, 줌/해상도에는 영역 유지; subject/설정/Play/큰cut/.5초 초과 렌더공백에는 무효화한다. Dispose에서 해제. 진단 캡처는9buffer+영역2buffer+6RT로 확장했으며 신규17readback 완료 호출 자체는 이번 실측에 사용하지 않았다.
- `[GPU/CALL]` RTX2080Ti/D3D11 실제112dispatch 수학 검사 실패0: K2→3→4→1, 목표 변경, dt0,30/60FPS 동일경과시간,scale 변화,키/슬롯/무효화. 실제 서로 다른 Unity96프레임(수정전48/후48) 렌더 status global0. 동일 걷기 phase/white광량 곡선의 통제 호출이며 자연 WASD·전체 게임 흐름 검증은 아니다. 별도 정적 검토에서1..32 단계조합1,024개 rank 순서/범위 확인.
- `[시각 증거·제외]` PNG24쌍 중 첫 pair00은 수정전 첫 프레임의 형상 크기가 달라 비교에서 제외했다(준비 불일치의 직접 원인 미확정). 원본/로그는 보존하며 나머지23쌍의 전경 마스크는 exact 동일. 비교 APNG는 원본 등배, 배경 하단 여백만 공통 생략. 색보정/재샘플링 없음. 시각 합격은 사용자 답변 대기이며 픽셀 통계를 아트 승인 근거로 쓰지 않는다.
- `[복원·경계]` 임시 조명/카메라/Animator/시간/background/렌더 옵션 복원 후 Play off·GameMap1 dirty=false·최종 compute 메시지0. regionTransitions=true/.25, 두 수광비교옵션은 기존OFF. 저장하는 것은 밝기 등치구간이지 UV/삼각형별 표면 마스크가 아니므로 원본 광량급변/경계 동시통과/가림/희소Hair는 남는다. 전체 깜빡임 해결·GPU성능·빌드·다중GPU는 미검증. 사용자 기존dirty6파일/외부미추적에셋 보존.
- `[재현]` `LocalOnly/AdaptiveToneRegions_20260910/`의 README·gpu_regions.cs.txt·gpu_20260910_060202_016/summary.json, preview_sequence.cs.txt·preview_20260910_060833_499/{frames.jsonl,summary.txt,comparison.png,원본PNG}. 설정/수학/한계는 `docs/ai/CHARACTER_ADAPTIVE_TONES.txt`.
- `[사용자 불합격·최종 정정]` 새 Hair가 단색이라 명암구도 소실을 지적받음. 위 ON/승인대기는 중간 상태이며 최종 regionTransitions 기본OFF·메모리OFF로 기존 분할 이력 경로 복원. 이 작업을 전체 깜빡임 수정 완료로 표시하지 않는다.
- `[회귀 분리 실측]` regression_20260910_062135_942의 정지광1.2: 새Hair 목표K2/실제774·2124셀2색. regression_20260910_062312_925의 감광.4와 regression_20260910_062517_813 원곡선index46은 목표부터K1/실제2898셀1색. index46 RMSE .05789771≤.06·broad요구0으로 현재DP가1색을선택했다. 비조명키가이전작은lit그룹도병합한다. source가단색이된것이나오직Resolve버그로설명하지않는다. 17readback API는이5회raw캡처에서완료확인.
- `[좌표 결함 별도 수정]` 현재metric/지연mean의 불일치를현재mean으로통일. 같은균일광량배수는분자·분모에함께반영하고경계·대표색만시간변화한다. targetK1의실측원인은이수정으로해결되지않는다. 초기112dispatch검사가이미주어진Palette의전환만검사한탓에명암구도보존은검출하지못했음을명시한다.
- `[추가 GPU 단위검사]` gpu_20260910_063308_146:124dispatch 실패0. 현재scale 일치·분류보존CPU보조·지연분모반례검사 포함. 실제Hair Resolve수정완료 근거는 아니며 시각불합격은 유지한다.
- `[조명 코드 확인]` CharacterFlatUnlit의nativeRGB/Incident는표면별positionWS·normal·cookie로계산,root한점조명아님. 비전환은SkyLightingCycleController의8초weather진행으로전역ambient·주광tint/intensity도변경하므로부분구름과별개로전신입력변화가있다. 맑은날구름이동에는그전역weather변경없음. 바닥과신체높이의cookie투영차이도가능하나사용자가관찰한반그림자→전신현상자체는미재현. 날씨/구름코드는수정하지않음.

## 137. 약광의 상대 밝기 오차 및 피부 단계 차이 확인 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-10]` 정리한 작업에 우선순위를 정해 재개. 1순위는 약광에서 Hair 목표가 K1로 합쳐지는 판정, 후속은 실제 표면 구역 전환과 부분 그림자/이동 안정성이다. 추가 Smack Studio 영상은 기존 참고파일 말미에 공식 자료·추론·미확인 경계를 구분했다. 현 파이프라인 교체는 하지 않았다.
- `[구현]` 비수광Y 그룹에 선택적 relativeLightness, lightnessRelativeError=.10, lightnessBlackFloor=.02(Oklab L)를 추가. 오차·broad/highlight 대비를 max(meanL,floor)에 비례시킨다. Hair/Skin Y 우선·history mode3 분리·값검사/바인딩/설정동등성 연결. 후보/DP/관측RGB/격자/선/깊이/광원 변경 없음. HistoryMetricScale는 기존단위 유지하되 acceptance helper와 분리하여 동일수식으로 컴파일 경고3개 제거, 최종 메시지0.
- `[GPU/CALL]` gpu_repair_20260910_121839_987: 7입력×OFF/ON=14회 파이프라인 기술 검사 통과. 기존밝음/약광/재밝음 raw Hair2/1/1→2/2/2. 동일입력 RGB×.125/×.015625에서11그룹 K유지·전체출력 배율후 bitwise동일, 실제단색/근암부 미세변동K1. fresh history에서 관측RGB/입력/깊이/EMPTY/타subject 보존. 이전 셰이더 OFF와의 clone parity는 미실행이며 반복 시간전환 시험으로 간주하지 않는다.
- `[시각/CALL]` preview_20260910_121259_309: 같은고정pose·white광량1.2/.035/1.2의48frame씩 비교, 실제96frame global0. index24/46의nativeColor/Lighting/Meta/cellColor/Meta 전후 byte exact·깊이/EMPTY exact. 준비 index0은 형상 불일치로 비교 제외, 원본 보존. 등배23쌍 APNG와index46 PNG 제공; 사용자 오른쪽 외형 승인. 최저광량index24의 Hair는 여전히K1이다.
- `[사용자 질문·실측]` 피부3→2는 조명입력 차이가 아니다. index46 meanL=.970079→새허용오차 .097008, K2오차 .078500이 기존 .06은 넘지만 새기준은 통과. 실제색분포3색752/250/1965→2색916/2051. Hair meanL=.428981→허용오차 .042898로 K1오차 .057905를 거부한다. 밝은피부가더관대해지는차이이며 '무손실특징보존'으로 표현하지 않는다. 사용자 승인 수치는 추가 변경하지 않았다.
- `[승인 설정·복원]` PC_Renderer의 relativeLightness=true와 regionTransitions=true/.25 저장, 두Y옵션OFF. 같은asset 저장 때 이미기존 SteppedLocalLightRendererFeature.Create()가 true로강제하는 bindDepthStencilAttachment도직렬화되어diff에포함되나 코드/실제조명동작변경없음. 임시조명0·카메라/Animator/시간/배경복원·PlayOFF·GameMap1 dirty=false·Console Error/Exception/Assert0. 사용자 기존씬/재질/외부에셋 보존.
- `[남음]` 표면별시작/현재/목표 경계와가림상태는미구현. Body와Hair00~03 UV0없음 직접확인, 현재밝기등치구간/공유mean 재분류의한계는남아있다. 부분구름·자연WASD·전체깜빡임·GPU비용·빌드/다중GPU 미검증. 우선순위1의관찰된목표K1문제만수정했으며 전체해결아님. 증거와재현코드는 LocalOnly/AdaptiveToneRepair_20260910/ 및 docs/ai/CHARACTER_ADAPTIVE_TONES.txt.

## 138. 중단된 캐릭터 제작 방식 비교 재개 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-10]` 연결 실패 전 선정한 실시간3D / 자동sprite bake / 2D본 비교를 이전 대화에서 복구했다. 당시 실제 샘플 생성은 시작되지 않았음도 확인. 기존 Player/게임씬/승인된 명암 코드·설정은 교체하지 않고 별도 `Assets/Tests/CharacterPipelines/Review01/CharacterPipelineComparison.unity`에 표시 전용 샘플을 생성했다. 게임 build 씬 목록에 추가하지 않았다.
- `[구현]` A=기존 Chibi/Controller/2px renderer. B=A의 같은 걷기4/3초를16장 PNG/12fps로 자동촬영한 sprite 재생(새 픽셀화 알고리즘 아님). C=같은 mesh를모든boneweight의nearest ancestor14그룹으로분리한고정정면그림+기존ModularSpriteRig/Skin/Motion/PoseSolver와새Actor. 전체triangle분할합계보존. 그림에3D본을남겨투명하게한방식이나Smack Studio깊이복원은아님. C는원래3D본의위치/각도를사전에2Dpose로변환해서기록한다.
- `[검증 CALL]` 소스16+파츠14촬영완료, 동작16+약한key1=17실제프레임비교완료. B/C4번프레임동기,14파츠표시,disable/enable시외부child보존,미지정방향숨김확인. Console Error0. 재생종료. 첫capture는background=false로1프레임timeout, 임시true후완료하고false복원. 원본model CPU Read/Write는보존하고Edit Mode에서베이크전용mesh를준비했다. 본/PNG의같은정수pixel pivot을사용한다.
- `[사용자 피드백·불합격]` A/B시각동일. B의다른점은새렌더가아니라생산시촬영→실행시이미지재생이며조명/새클립/방향/장비조합의베이크비용이있다. C는머리로몸가림·발분리로거부됨. Head가앞/뒤머리를한그림으로가지고단일bone-depth순서로배치되며, rigid그림position/rotation뿐이고joint skinning/foreshortening없음. 실제LeftFoot로컬각0→68.6→86.2→91.2→97.6도; generic bone up축의평면투영을foot그림회전으로삼은변환은재설계필요. 이문제는Unity오류나2D본불가능증거가아니며미수정으로명시. 시각승인없이자동보정반복하지않음.
- `[자료·경계]` 샘플README와 LocalOnly/CharacterPipelineComparison_20260910/에원본PNG/manifest/17frames/APNG/실패take보존. 모든방향·모딩import·GPU비용·게임통합·최종아트미검증. B는별도조명반응을추가하지않았고C는기능proof만존재하여완료표현금지. 베이크전용메시는씬의존성이없으면정리하며builder로재생성가능.

## 139. 생성한 정면 2D 파츠와 기존 3D 스켈레톤 연결 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-10]` 기존 골격만 남겨 생성형 정면 그림·파츠를 비율/각도로 연결하고 외부 실제 구현을 조사. Project Terra·Sean Unity·Meta Animated Drawings·Smack Studio와 Unity/Spine/Godot의 1차 자료 11개를 `docs/references/2d_parts_3d_skeleton_research.md`에 구분했다. 인터넷 전수 조사나 비공개 구현 복제는 아니다.
- `[구현]` `GeneratedFront01/GeneratedFrontReview.unity` 별도 시험. 신규 clone의 Renderer만 제거하고 기존 Avatar·Controller·본을 보존, 16개 생성 그림을 같은 관절로 실시간 변형. 팔/다리는 원화 anchor 두 점→투영 관절 두 점 affine, 머리/발은 bind 역행렬에 저장한 기준면의 전체 변환. 초기화 때 bind를 새로 잡지 않는다. 앞머리/얼굴/뒷머리 분리, B처럼 애니메이션 PNG를 재생하는 방식 아님. A/B/C·실제 Player/게임씬·승인 명암 코드는 무변경.
- `[아트]` built-in 생성 원본1254² RGBA+프롬프트 보존, Sprite rect/anchor를 명시. 생성된 하퇴에 중복 부츠가 있어 하퇴 rect는 그 앞에서 끝내고 별도 Boot 하나만 사용. 원본 픽셀 수정·재생성 없음. TextureImporter의 기본 NPOT 자동축소를 None으로 설정해 좌표 일치. 원화 anchor·폭은 저작값이며 생성기가 해부학적으로 자동 보증한 값이 아니다.
- `[검증 CALL]` Unity 컴파일/씬 생성 및 Play에서 실제 걷기16frame+idle1frame 단1회 촬영. 16파츠 초기화, clone 원본 SkinnedMeshRenderer0. 기존 문제가 컸던 walk phase.25의 anchor 오차 최대1.1920929e-7 world units. 실제 캡처/APNG는 LocalOnly/GeneratedFrontReview_20260910/. 첫callback delegate 컴파일 오류와NPOT guard는 원인수정 후 실행. Unity AI 계정서비스의 generators.ai.unity.com 오류 로그는 별개이며 이번 코드로 해결했다고 주장하지 않음.
- `[미검증/보존]` 실제정면미리보기와피드백질문제공; 시각승인대기. 관절그림이음새·다방향·교차가림·멀티weight·극단적축소·실제조명·mod import·GPU비용·게임통합미검증. 고정정면순서와affine plane 시험이며Smack깊이복원아님. 사용자승인전 추가외형조정없이보존.
- `[최신 사용자 정정·불합격]` 애니메이션·위치·파츠·레이어 불일치, 양쪽 어깨 위치/그림 뒤바뀜 지적. 완성 정면 원화 없이 atlas부터 생성한 제작 순서 오류이며 anchor 수치 일치가 아트 정합성을 보증하지 않는다. 새 제작 요구는 정상 정면 원화 먼저→그 원화의 공통 좌표에서 파츠 분리→색이 맞는 원형 관절 보충. 원형은 이미지 생성이 아니라 Unity 절차적 메시/마스크로 표현. 현 샘플은 실패 근거로 보존하고 추가 생성·외형 보정 및 완료 커밋 중단. 정정된 새 방식은 아직 구현하지 않았다.

## 140. 승인된 완성 원화의 파츠 분리와 기존 본 연결 `[CHARACTER-RENDER-01]`

- `[요청·2026-09-10]` §139의 제작 순서를 수정한 별도 E 시험. 사용자 승인 정면 원화 한 장을 기준으로 파츠·관절을 연결하고, 기법·수학·외부 자료·실패·결과를 연구 문서 M03의 E/E-foot에 기록했다. 당시 사용자 판단은 팔다리 정상, 발만 문제로 보임이며 추가 외형 수정은 멈췄다.
- `[구현]` `SourceFirst01/SourceFirstReview.unity`에서 원화 공통 좌표/PPU380을 사용하는 독립 메시17개가 같은 texture를 참조한다. 원화 관절15개에 기존 Avatar/Controller의 기준 idle 대비 투영 방향·길이 변화를 전달하고, 절차적 단색 원형 관절10개와 공유 경계12개를 사용한다. 통그림 한 장을 휘는 방식이나 파츠별 독립 생성이 아니다. 실제 Player·게임씬·기존 A/B/C/D·명암 렌더러는 보존했다.
- `[원인 수정]` 편집 시 Sprite.OverrideGeometry 제한은 직접 Mesh 저장으로, 참조 패널의 Play 흰색은 비직렬화 MaterialPropertyBlock 대신 재질 BaseMap 참조 저장으로 해결했다. 골반 등 절단 경계는 원으로 큰 틈을 덮지 않고 같은 원화 점에 같은 변환 가중치를 적용했다. 초기 실패 Sprite 중간 에셋은 현재 메시에서 사용하지 않으며, MCP 정리 호출이 거부되어 삭제하지 않은 상태다.
- `[검증 CALL]` Unity Play에서 기준1·걷기16위상·idle1을 촬영했다. 경계 수정 후 최종 비교를 한 번 추가했고 기준 정점 world 오차0, 걷기0.25위상의 공유 경계340쌍 최대 틈0을 확인했다. 이는 모든 애니메이션/시각 합격을 보증하지 않는다. 실제 비교 APNG·정지 화면·기술 값은 `docs/references/evidence/source-first-20260910/`에 보존했다. Play 종료 후 기존 Review01 씬으로 복귀했다. Unity AI 계정서비스 오류는 별개로 남아 있다.
- `[발 미해결·연구]` 종아리는 무릎→발목 투영 벡터, 부츠는 Foot quaternion의 화면 법선 twist를 쓰며 발목 band가 두 변환을 혼합한다. 단순 부호 오류는 확인되지 않았다. 후속은 문제 프레임 하나에서 부츠 회전과 연결부 혼합을 분리하는 비교이며, 필요할 때만 발 표시 축 또는 방향별 발 그림을 검토한다. 정상 팔다리를 다시 바꾸지 않는다.
- `[범위·미검증]` 원화 마스크·anchor는 저작 데이터이며 임의 그림 자동 rig 완성이 아니다. 다방향·숨은 면·임의 clip·모드 로더·게임 통합·환경 조명·성능 Profile·빌드는 미검증이다. 발 미해결의 연구용 부분 구현으로 보존하며 완료 커밋은 하지 않았다.
- `[최신 정정·구조 미충족]` 사용자는 이미지별 2D 자세 보정이 아니라 투명 3D 몸체/스켈레톤에 부착되어 같은 변형을 따르는 이미지를 요구했다. E는 clone의 3D Renderer와 MeshFilter를 제거한 뒤 별도 2D 관절/평면 mesh를 변형하므로 이 구조를 구현하지 않았다. 이전 팔다리 피드백은 기술 구조 승인 아님. 발의 깊이 회전을 버린 Roll, 짧은 발끝 투영으로 옆으로 꺾이는 Segment를 구분했고 두 부츠만 기존 Plane으로 시험해 세로 축소를 확인했지만 최종 해결로 채택하지 않는다. 원화/mesh 무변경, 재생 중단, 미완료 유지. 3D 바인딩의 후속 F 실패와 현재 보류 결정은 연구 M04/F·D01에 정리했다. 이 과거 후속 제안은 새 구현 권한이 아니다.

## 141. GPT/2 등각 맵 타일과 단층 진입·가림 시험 `[MAP-01][CAMERA-01]`

- `[요청·2026-09-14]` 캐릭터 제작을 중단하고 GPT/2 원본 타일로 맵 교체, 실제 건물 진입, 실내/뒤 가림벽 반투명 시험을 요청했다. 캐릭터 최상위 레이어 처리는 사용하지 않는다.
- `[현재 후보]` GameMapTest의 기존 생성기/격자/필지/NavMesh에 IsometricUrbanStyle을 연결했다. 바닥은 원본 상면 homography, 벽·창·열린 출입구는 전체 모듈과 수직면 기준점의 역변환을 사용한다. 단층 실내·벽/문 Collider·독립 지붕·기존 비차단·쓰레기통을 조립한다. 기법과 원본 대응은 `docs/references/isometric_urban_map_pipeline.md` D02가 원본이다.
- `[사용자 정정]` 첫 벽돌 면 반복 결과의 원본 디테일 누락 지적을 반영해 전체 모듈로 전환했다. 원본 RGB는 보존하고 alpha 연결성분 mask로 이웃 모듈만 제외했다. 최초 native MPB 초기화 오류는 Awake로, 기존 의료 Chest의 문앞 차단은 Chest 보존 및 문 위치 분리로 수정했다.
- `[Play Mode 호출 확인]` Unity6000.5.9f1, 최종seed−743543409, 건물150개, readiness·문→실내 NavMesh·Player 크기 통과 공간·벽 차단·동일Player·UV 조건 확인. 실내roof0.04, 뒤 가림0.18, 시야복귀1.0. 키 입력 보행 녹화는 아니다. Console의 초기오류3건은 보존했고 수정 뒤 새 오류는 관측하지 않았다.
- `[결과]` `LocalOnly/IsometricMapTrial01/technical.json`, `v2b-{outside,inside,behind}.png`, `isometric-map-comparison.webp`. WebP는 실제 새 Unity 화면3개의 상태 비교다. WorkLoop v2 후보의 art→observe→필요한 기술 gate 완료이며 미술 합격은 아니다.
- `[보존·경계]` Player·이동·기존 3D 표현 경로·원본과 사용자 dirty 파일은 보존했다. 등각 geometry1002/치수 hash는 기존 원정 복구와 구분한다. 원래 원정 hash는 style 미사용 시 유지한다. 현재 원화 명암을 사용하는 단층 시험이며 임시 지붕 표면·다층·자유각 원화·실시간 환경광·모든seed·복구/카메라 왕복·GPU Profile·빌드는 미검증이다. Play 종료, GameMapTest dirty 없음. 시각 승인 전 추가 미적 수정은 보류한다.

## 142. 맵 치수·카메라 이동·전체시트 픽셀 정규화와 가중 타일 `[MAP-01][MOVE-01][CAMERA-01][CHARACTER-RENDER-01]`

- `[사용자 정정]` 전체 등각 벽 그림의 재투영, 작은 건물/큰 캐릭터, 월드축 WASD, 단일 도로 타일을 지적했다. 이후 수정 PerfectPixel은 조각 추출 전 전체 시트에 적용하도록 정정했고, Ground까지 아스팔트인 점과 도로의 반복 흰 테두리도 수정 요청했다. 기법/후보/좌표계/실패/결정은 `docs/references/isometric_urban_map_pipeline.md` D03~D05에 기록했다.
- `[구현]` 실제 metric box벽/창틀/두께와 동차UV, 기존 layout높이를 층고3.4m로 반영한3~5층 외관/지상층 실내를 사용한다. 공통 외형root만 균일scale하여 약1.8m, 문2.65m다. 같은 PlayerMovement.Update가 현재 셸Camera의 XZ직교기저를 사용하며 변환한 방향으로 충돌/회전을 처리한다. 차선은 기존 road graph에서 도출하고 ground/sidewalk/road의 역할별 가중 후보는 seed/x/z로 선택한다. RuleTile 패키지를 설치하지 않았다.
- `[원인과 수정]` 도로용 원본사각 영역에 독립슬랩의 밝은 외곽선이 섞여 반복 격자를 만들었고, Ground와Road가 같은 이미지라 인도가 띠처럼 보였다. 도로·보도 상면에서 공통8source-px 경계를 제외하고 Ground/Sidewalk에 동일한 밝은 후보를 지정했다. 두 영역은 표시Y=.005의 연속 평면으로 하고, 이 스타일에서만 내부 보도단차를 제거했다. 물리 바닥·NavMesh·격자 의미는 유지했다.
- `[실행]` 기존 수정 엔진으로 원본3장 전체를 각1회362×272로 정규화한 뒤14개 면을 nearest homography로 추출했다. 전체15.304초, 원본/엔진SHA불변, 조각별추가정규화0회. 현재 결과 `Assets/Art/IsometricUrban/Gpt2/WholeSheetNormalized/`, 재사용입력/실행기 `Tools/WorldArt/`. 이전출력과 원본은 보존했다. 색/명암/이미지 생성은 하지 않았다.
- `[Play Mode 호출 확인]` 직전seed−1483496983에서 StepMove40카메라/입력case, 실제외형1.795856m, 문/벽/NavMesh/안·뒤fade/동일Player/UV/도로표시영역을 확인했다. 최종seed−412374159에서 새atlas 실제재질참조, Ground=Sidewalk, 평탄지면, 황/백/횡단보도 사용, 도로밖quad0을 확인했다. 바뀌지 않은 입력·문·크기 검사는 재실행하지 않았다. 증거 `LocalOnly/IsometricMapTrial03/technical.json`, `LocalOnly/IsometricMapTrial04/{technical.json,street.png,inside.png,bake/bake-report.json}`. WorkLoop v7은 필요한기술gate까지만 완료했다.
- `[경계·판정대기]` 실제 물리키보드, 시각 승인, 모든seed/저장복구/카메라왕복/GPU Profile/빌드는 미검증이다. 계단·경사이동·층전환은 설계만 있다. 주광Lambert+SH 외 조명 통합, 투명벽 중첩과 전경 near-plane잘림, 완전무봉제는 해결했다고 주장하지 않는다. Console의 과거오류3건을 보존했고 최종게임실행의 새오류는 관측하지않았다. 임시MCP metadata parser오류는 확정좌표의Editor API적용으로 해결했으며 정규화 엔진 재실행은 없었다. 최종 실제 화면으로 사용자 피드백을 요청한 뒤 추가 시각 보정을 멈췄다.

## 143. 0.2m 연석·기본 계단 이동·2층 외관 `[MAP-01][MOVE-01][TRAVEL-01]`

- `[확정]` 밝은 포장 재료는 유지하고 단차0.2m, 건물2층, 횡단보도 줄의 축 교환을 적용했다. 사용자는 현재 결과가 괜찮고 디테일은 나중에 조절한다고 유지 승인했다. 이후 재개 요청은 도로 끝의 생성 알고리즘이다.
- `[구현]` 같은 Player에 Unity CharacterController(height1.8/radius.5/stepOffset.3/skin.05)를 사용하며 같은 Rigidbody는 kinematic, 기존 BoxCollider는 비활성, 상호작용 trigger는 유지한다. 기존 PlayerMovement만 Move/중력을 계산한다. 씬 도착과 checkpoint 복구는 동일 Player의 TryTeleport를 사용해 controller 상태/수직속도를 처리한다.
- `[높이 원본]` SurfaceGrid 역할에서 도로Y=.005/포장Y=.205를 파생해 메시·MeshCollider·건물root·배치물/spawn 지지높이·NavMesh가 공유한다. 실제 지상층 바닥Collider를 사용하고 외관높이는 계획부터2×3.4=6.8m다. checkpoint geometry1004이며 원본/정규화 atlas는 재처리하지 않았다.
- `[Play Mode 호출 확인]` seed475456319에서 실제 StepMove→CharacterController.Move의 연석 상승/하강, 벽차단, 문통과, 도로↔포장 NavMesh 경로, 2층6.8m, 실제 횡단보도 UV축을 확인했다. 상승rootY=.7549998/하강Y=.5549999, 발과표면오차≤.06m다. 실제 GameMapTest→GameMap1→GameMapTest 왕복 후 Player/Camera/InventoryUI 동일 EntityId와 Controller/이동 활성·잠금해제를 확인했다. Editor 임시저장 profile을 사용했다.
- `[근거·경계]` `LocalOnly/IsometricMapTrial05/{technical.json,travel.json,overview.png,step.webp}`. 연속동작은 실제 새 캡처23장, 관찰용80ms/frame이다. WorkLoop v8 최종기술gate 통과, 사용자 유지 승인. Play 종료/GameMapTest dirty 없음, 시험용 background실행도 원래false로 복원했다. 기존 Console오류3건은 보존했고 새 게임오류는 관측하지 않았다. 실제 키보드·대각벽모서리·큰낙차/다른경사·전체Recovery·모든seed·GPU/빌드는 미검증이며 층전환/긴계단은 미구현이다.

## 144. 외곽 도로 연장과 고정 이동 경계 `[MAP-01]`

- `[확정]` D06 외관/단차는 유지하고 원형으로 끊기는 도로 끝을 수정 요청했다. 구현 후 경계부 화면을 보고 현재 방식 유지, 디테일은 나중에 조절한다고 승인했다.
- `[원인·구현]` 원래 road mask는 중심선 원판 합집합이며 외곽node가 이동경계25m 안쪽이다. graph/node/entry/portal은 유지하고 외향 half-strip을 기존 SurfaceGrid에 합친 뒤 보도/필지/높이/충돌을 파생한다. 경계밖은 같은 좌표와 높이의4개표시mesh, Collider/NavMesh/spawn은 없다. 노란/흰 차선은 기존절대UV위상으로 이어간다. planner8/등각geometry1005로 복구판본을구분한다. 수학/후보/실패조건은 맵연구D07에 기록했다.
- `[실행]` 실제이전commit2d36911 planner와 두seed를 비교하여 모든node/road/port/anchor/범위 동일을확인했다. 연장도로와겹치는필지는 제외되고 기존validator를통과했다. Play seed−1038015743에서 같은Player를4면으로이동시켜각경계안약1.05m에서차단, 외부충돌/NavMesh없음, 도로/높이연속, 차선SAT/위상을확인했다. 현재카메라조건에서62m표시여백과유효지면64ray 모두범위안을확인했다.
- `[근거·한계]` `LocalOnly/IsometricMapTrial06/`의 실제JSON/화면, WorkLoop v9 gate통과. 최초카메라검사에ray뒤쪽교차점이섞인오류는해당관찰만수정하고초기보고도보존했다. baseline용임시코드는정리했다. Play종료/backgroundfalse복원, D06검사는반복하지않았다. 물리키·모든seed/실행중화면비변경·전체Recovery·GPU/빌드는미검증이며 내부막다른길과외부교차로의세부규칙은범위밖이다.

## 145. 건물 프리팹 예약·사물 분류와 POI 구역별 가중 소품 `[MAP-01]`

- `[요청·정정]` 건물 프리팹에 확률/주변여유를 소유하도록 요청했다. 최초 공통 원통휴지통/생존선반 배치에서 사용자는 크기는 괜찮지만 벽 잘림과 용도 없는 외벽 반복을 지적했다. 사물 외형→적합장소목록→POI 가중목록→배치 순서로 교체했다. 최초결과는 보존하고 현재합격으로 재사용하지 않는다.
- `[구현]` 실제 FurnishedMetricBuilding prefab의 immutable snapshot→예약필지/본체/POI→구역과물리조건을만족한catalog별후보풀→가중선택→같은generator의실제prop prefab/Collider→NavMesh 순서다. 규칙확률은건물당1회, 개수는규칙및catalog별상한을모두적용한다. planner10/geometry1006과profile/소품hash가변경된world를구분한다. margin1.5m, 본체8~10×8m/2층6.8m, 기존Player/도로/포장/출입구/루팅권위는유지한다.
- `[재료·의미]` GPT/2 PNG36장의사물/환경13장및개별물건목록을 `docs/references/urban_object_catalog.md`에기록했다. 실제Medical에행정용desk1,뒤편wheeled dumpster1,입구round bin≤1(발생.35)만연결한다. 생존보급선반은Medical선택0, 미분류건물장식0. 최초두시트정규화9.371초와새두시트8.043초는각원본별1회이며이전출력/원본해시보존. 새수거함2096pixel모두선택alpha성분의source좌표에속해bbox이웃혼입0이다.
- `[벽잘림 근본수정]` fullcamera-up card가XZ로1.2227m돌출해.5m물리반깊이를넘었다. 실제Y수직card로바꾸고sprite실제vertex폭의회전반경을snapshot/Collider점유범위에포함한다. 화면최상위/부위별offset/크기clamp를사용하지않는다. 카메라고도에따른정상cos투영은유지하며깊이맵이나숨은면복원으로설명하지않는다.
- `[최종 Play Mode 호출 확인]` seed1462661998의49건물중실제Medical에desk1/dumpster1/bin0. seed재현/확률0의빈배치와hash변화/POI·zone·상한·미분류배치0/불가능한100×100m가중치1000후보제외를확인했다. 두card의8yaw×4정점=64case가실제Collider안, 전체실제벽/지붕penetration0, 같은Player문통과와입구→실내중앙NavMesh경로를확인했다. 원본/초기증거와 `LocalOnly/IsometricMapTrial07/semantic.json`, `semantic-inside.png`, `semantic-outside.png`를구분한다. WorkLoop v10은초기기술gate만완료, v11은최신정정으로중단, v12는최종의미/렌더기술gate다.
- `[이전자료추적]` 사용자가9/4연결한ChatGPT작업 `6a9a03b2-201c-83e8-a3d1-9e9b63c03acc`의도심생성후보조사를찾고GitHub원문을대조했다. 도심트윗URL자체는특정하지못했다. 현재제한형도로graph와외부방향장/성장형도로프로젝트통합여부는맵연구D08에분리했다.
- `[최종 사용자 판정]` 용도는맞지만도심디자인/이미지크기/방향이전체적으로잘못됐다고거절했다. 따라서D08은미술완료가아니며추가개별보정을멈추고공통투영·치수·방향·texel밀도·도시문법재설계가재개조건이다. 기술gate합격을사용자디자인합격으로바꾸지않는다. 결과/원본은보존하고완료커밋은하지않았다. Play종료/backgroundfalse를복원했다. 콘솔의기존15:12오류3건은보존하며다른POI/부착물/층전환/전체Recovery/실제키보드/GPU/빌드는미검증이다.

## 146. D09 도시·POI·입체 재료 시험과 픽셀 요구 이탈로 중단 `[MAP-01][POI-01][CAMERA-01]`

- `[최신 사용자 정정]` 사용자는 픽셀 목표를 무시하고 AI가 범용성을 이유로3D로만든것인지 지적했다. 담당AI는 요구를구현편의판단으로대체한잘못을인정했다. PixelLab완성사물스프라이트나3D→pixel완성단계는없다. 추가생성/구현중단, 디자인합격/완료커밋없음. 자세한현재상태·다음분기는 `docs/references/urban_pipeline_handoff.md`에집중한다.
- `[실제 제작]` PixelLab MCP TilesPro job f9eb76e3-4443-4a61-a070-7db94bcee95e의64px정사각재질16장→무손실atlas, 밀도32texel/m/2m반복. Blender5.2스크립트로11소품+나무의실제3D형상저작. PixelLab이미지에서3D를복원한것이아니다. Unity기존절차건물/새CoherentUrbanBuilding prefab, 기존primitivePrototypeStreetLamp와기존게임playasset유지.
- `[도시/의미 구현]` Ground4연결BlockMap→같은block의OBB필지→같은정면frame의건물/문/소품. 40m대각부지수용실패반례후전체290m유지/node48m. Medical1/Office24/Residential28/Retail28/Workshop35. 실제방벽/실내역할연결그래프/2층바닥/계단은없다. generator11/checkpoint1007로기존복구버전거부, None0/Medical1과spawn/loot권위유지는코드검토.
- `[Play Mode 호출 확인]` seed1462661998, hash14583068C88F2EB4 repeat동일, 116건물/470실제3D소품/대각접도필지1. 좌표frame/vertexvolume오류0·실제벽/지붕침투0, .2m단차, 동일PlayerMovement→CharacterController문통과, 문밖→중앙NavMesh경로통과. 45Block은작은Ground섬포함연결성분수다.
- `[기술 반례 수정]` Texture2D.whiteTexture가style직렬화후null인문제는영구PaintWhite.asset와metric검사로수정. 카메라near평면의지붕/지면잘림은실제renderer높이bounds→직교시선축후퇴로수정했다. 같은Camera/offset/rotation/zoom을보존하고Zoom뒤Follow[50]적용. 6case(zoom3.5/8×pitch10/35/80) near/far실패0, 화면XY최대차1.02894e-6, 깊이제약해제복원통과. 문/물리검사는변경되지않아반복하지않았다.
- `[증거/중단]` `LocalOnly/UrbanDesign09/technical.json`, `camera-technical.json`, `Final/`실제화면. state-v4는user_review ticket db3a23e154064d4bb90917cb6c98fb86에서사용자요청으로paused; accepted미제출. v2 repair입력누락과v3렌더추가반례를보존하고무의미재생성은하지않았다. Play종료/backgroundfalse복원. 원본/D08/사용자dirty보존. 물리키/전체Recovery/모든seed/GPU/build/실내역할/최종픽셀출력미검증또는미구현이다.
## 147. 기존 3D의 고정 시점 픽셀 캐시 시험 `[PIXEL-01][MAP-01]`

- `[사용자 확정]` Iron Bramble·Graveyard Keeper 2·Dimraeth·Unpacking을 디자인 참고로 기록했다. 깨끗한 픽셀 출력 조건에서 기존3D 입력을 허용하며 고정/유한 방향 카메라가 가능하다. 전체화면 모자이크만으로 대체하지 않는다.
- `[구현/호출 확인]` Editor 전용 `PixelSpriteCacheBaker`와 명시적 고정 주광 bake shader. 실제 소품12종+생성Medical건물/분리벽·지붕·바닥의4방향92개 RGBA/depth 쌍, 공통32px/m, 정수bounds/pivot. 원본 씬/모델/카메라/물리/기존후처리는변경하지않았다. 수정캡처2.417초·48,131,508bytes(비압축depth포함); 런타임성능값이아니다.
- `[증거]` `LocalOnly/UrbanPixelCache10/manifest.json`, `preview.html`, `preview-technical.json`, state.json. PNG와rawdepth의상하행순서반례를initial-readback에보존하고수정했다. projection원점최대0.00006652px, alpha0/255·depth유효·PPU검사통과, 같은coverage 외곽선과2배정수확대를확인했다. Console오류0, Play종료/씬dirtyfalse/backgroundfalse복원. 기존다른변경의trailing whitespace는손대지않았다.
- `[대기/후속]` graph는기술gate exit0 뒤실제사용자시각판정ticket `171d2b6030774493b587bc932c6dda6d`에대기한다. AI가accepted를제출하지않았다. 도시전체depth합성/실내fade/동적조명/시점·zoom입력연결/GPU실측은미완료이며, 평면PNG만으로가림을보존했다고주장하지않는다. 연구D10에후속입출력/실패조건을남겼다. 사용자시각승인전완료커밋없음.

## 148. D12 편집 가능한 Blender 책상과 이미지 재질 수정 `[PIXEL-01]`

- `[사용자 확정]` 생성형은 참고/재료 입력으로 허용하되 최종은 편집 가능한 모델에서 렌더한다. 한 시점의 책상 시험이며 게임 씬은 바꾸지 않는다. 생성 참고 그림의 전체 디자인 방향만 선호했고 비율은 승인하지 않았다. 최초 noise/임의 테이퍼 결과와 이후5색 albedo 재분류 결과는 사용자가 거절했다. 마지막 정정은 나뭇결을 생성 재료와 흡사하게 유지하고 다리뿐 아니라 바닥 모서리의 픽셀 일관성을 고치는 것이다.
- `[구현/CLI 실행]` `Tools/PixelDesk`에 치수 recipe→31개 실제 메시→Blender5.2 EEVEE→native PNG 경로. 공개 Pixel Art Rendering 수정판 `Tramshy/pixel-art-addon-mod` commit `f13502c1fa71fd92e3969f35e9edeab17f4da52d`의 실제 재질 생성 함수를 로컬 호출했다. 다운로드/라이선스는 `LocalOnly/DeskBlender12/vendor`에 보존했다. 생성 나무 이미지1장을 material로pack했고 책상 그림을 축소/투영해 모델을 대체하지 않았다. PerfectPixel 원본/수정판 모두 호출하지 않았다.
- `[최신 수정]` imageRGB×tint×조명5단계, 최종 전역 색표매핑 제거. 두55×55×695mm 직선 다리와 받침의 접지 정점에 연결된 bevel weight0(바닥/세로변 sharp), 공통 az45°/elev30° 투영. 바닥 XY선의2:1 기울기를 보장하지만 임의 끝점의 픽셀 위상까지 동일하다고 주장하지 않는다. 원본1.2×.6×.74m, 렌더176×172px/128px·m⁻¹. 표시용3배 확대만 별도다.
- `[최종 기술 확인]` `source-rgb/technical-result.json`: 평가 메시 접지3부품의z=0와footprint, 실제 Blender/독립 투영오차0.00004778px미만, packed 이미지 RGB 연결과후처리재색칠없음, 저장`.blend` 재렌더동일, tint모딩RGB변경·geometry/alpha유지. Build21.464초/재개25.311초/mod25.071초이며 전체사용자대기시간/게임성능값이아니다. 이전 rejected결과와검사는각폴더에보존했다.
- `[미술 판정 대기]` 최신 원본 `LocalOnly/DeskBlender12/source-rgb/base01/desk.blend`, 출력 `desk.png`, 실행은 `Tools/PixelDesk/build-desk.cmd`. WorkLoop `source-rgb/state.json`은 technical exit0 뒤 실제사용자판정ticket `ba473f376ba3417dbe96a53d0c73bc6e`에대기한다. AI가미술합격을제출하지않았다. Unity통합·다방향·깊이/동적조명·런타임모드로더는미구현, 완료커밋없음. 상세 계약·실험·재개는 `Tools/PixelDesk/README.md`가 소유한다.

## 149. D13 원본 PerfectPixel 재료 적용과 Radical Fish 기술 조사 `[PIXEL-01]`

- `[사용자 정정]` D12는 훨씬 나아졌지만 3D 느낌이 남았고, 원본 PerfectPixel 미사용을 지적하며 책상 재제작과 Radical Fish Games 기술 조사를 요청했다. D12에는 PerfectPixel이 없었다. 5색 albedo 재분류는 AI가 넣은 별도 처리였으며 원본 PerfectPixel의 문제로 돌리지 않는다. D12 그래프는 실제 추가 수정 요청으로 종료하고 이전 결과를 보존했다.
- `[실행]` 생성 참고의 재료 표현을 따른 새 평면 나무 이미지1254² → 보관 ZIP과 동일한 PerfectPixel NumPy 원본 →64²재료 → Blender UV/조명RGB/베벨면재질 →176×172책상. 원본 PP 내부 FFT 부적합 판정 후 내장 gradient 검출이 적용됐고 처리0.288초. center 출력색 모두 입력색에 존재, 임의 전역 팔레트 변환 없음. PP는 재료에 적용했으며 완성 책상 그림을 축소하는 대체물이 아니다.
- `[기술 확인]` `LocalOnly/DeskBlender13/technical-result.json`: ZIP/source 일치, 실제 원본 함수 실행, RGB입력색선택, packed재료/베벨, 접지/투영, 저장`.blend` 재개 렌더 재현 통과. build23.32초/재개22.33초. 원본과최종은 `base01/desk.blend`/`desk.png`, 기본실행기 `Tools/PixelDesk/build-desk.cmd`. 미술 판정ticket `478fba14f3d744feb4e9f65ab1d5badd` 대기, Unity통합/완료커밋없음.
- `[조사/미구현]` 제작자 설명으로 Alabaster Dawn의3D골격+각도별2D빌보드선택/회전/크기조절,2023당시최대16방향,누락각도와맞춤프레임보완을확인했다. CrossCode의대부분수작업애니메이션/복합보스조립,Canvas2D와3D충돌을구분했다. 배경의정확한texel밀도/카메라/가림세부는미확인이다. 근거와일반수학/제안은 `docs/references/radical_fish_*` 세문서로분리했으며본프로젝트캐릭터구현은하지않았다.
- `[추가 사용자 정정/실행]` 모서리입체감을더줄이고무늬를크게하라는피드백으로 `flat01` 제작. 원본PP재료그대로/전부품공통UVfootprint2.4×1.2m/밝은베벨재질제거/명암계수0.70..0.97. 실제렌더22.262초,기하·카메라보존과변경설정검사exit0. 현재판정은 `state-flat.json` ticket `18bb4bbd0f3941caa69f1a7dbeddf134` 대기, 추가생성/저장재렌더반복없음. Radical Fish 연구3문서만로컬커밋 `1bd3322`,책상미술완료커밋과push없음.

## 150. D14 면별 색과 국소 구조 명암 `[PIXEL-01]`

- `[사용자 정정]` D13-flat의 색 구분 소실/무늬를 거절. 강한 직사광 느낌을 없애면서 면별색·돌출/틈 명암을 살리고 픽셀을 더 크게 요구했다. 실제 답변으로 이전 graph blocked, 이전 결과 보존.
- `[구현/실행]` 공식 Lospec Shadeless 그룹을 append. 새 평면 재료→원본PP64²→면색×국소2단계AO→Cycles96px/m 직접136×133출력. 실제31개 nominal부품/치수/좌표 유지, 나무베벨제거, UV1.2m정사각공통밀도.17mm손잡이는1.632px이며 최소세부계약1.5px를 명시했다. 최종이미지 재축소/전역5색재분류 없음.
- `[기술 확인/대기]` `LocalOnly/DeskBlender14/technical-result.json`: 노드/pack/투영오차0.000023216px미만/접지·직선다리/새격자/저장blend 재렌더 동일 통과. 원본 `base01/desk.blend`,136×133최종 `desk.png`. graph review ticket `ac8a056304f3466eb4dceae6d0264404`, 사용자 미술판정 대기. Unity통합·시각완료커밋없음. 계약과출처는 `Tools/PixelDesk/GRAPHIC_PLAN.md`.
- `[후속D15/사용자부분확정]` D14새무늬거절후첨부원본을원본PP수동grid64로실행,내부refinement66×64. 등방texel18.75mm에맞춰UV1.2375×1.2m. 최종 `LocalOnly/DeskBlender15/base02/desk.blend`/`desk.png`,원본SHA·원본PP·UV·기하/투영/재질보존·PNG최종검사exit0. 사용자는텍스처가훨씬나아졌다고확인했고명암웹자료를요청했다. 무늬유지,명암미승인. 공식제작자료와미구현mask대안은 `docs/references/pixel_desk_shading_research.md`. 새명암렌더/Unity적용없음.

## 151. D16 역할 기반 명암 구현과 Radical Fish 종합 전달 `[PIXEL-01]`

- `[요청 유지]` 사용자는 중간 자료 질문 때문에 제작을 멈추지 말고 실제3D오브젝트의픽셀표현과유튜브게임기술정리두목표를완수하도록정정했다. D15나뭇결승인유지,명암만재개했다.
- `[구현/실행]` Lospec무조명색앞에부품역할control mask를연결하고AO를제거했다. root높이의상판밑3px상당밴드,서랍앞면상단1px상당밴드,아랫면의깊은음영을분리한다. 마스크속성과재료UV는독립. 초기Generated.z경계오류가상판에점을만든결과를보존하고명시적drawer-role gate로수정했다. 최신원본/결과는 `LocalOnly/DeskBlender16/fixed/base01/desk.blend`/`desk.png`136×133.
- `[최종 기술 확인]` `fixed/technical-result.json`: 승인재료SHA/UV/nominal기하/투영유지,광원0/AO0,31부품mask,접지·출력,저장blend재렌더동일,높이74→80cm모드의명암구간재계산통과. 실제외형판정은 `state-v2.json` ticket `524fc41f63e64578b2b05891542dd2d7` 대기다. 기술통과를완벽한디자인으로선언하지않았으며Unity통합과미술완료커밋없음.
- `[연구 완료]` Radical Fish 공식자료/개발자답변의종합은 `docs/references/radical_fish_technical_report.md`, 공개중단보고와공식기대동작대조는 `codex_premature_stop_research.md`. 게임의확인사실/제안/비공개공백과Codex사건의사용자보고/공식원인확인여부를분리했다.

## 152. D17 방향·가림 기반 NPR 명암 `[PIXEL-01]`

- `[사용자 정정]` D16은 “명암자체가사라졌다”고 거절됐다. 해당 응답을 이전 그래프에 제출해 미술 미완료로 종료했다. 승인 나뭇결과 이전 산출물은 보존했다.
- `[구현/실행]` Never’s End/Guilty Gear 제작자 자료의 방향·가림과 최종색 분리를 채택. EEVEE 단일Sun/whiteDiffuse→binary visibility와 world N·L을 3단계 유채색ramp에 연결한다. 최종색은 같은 원본RGB×명암색이며 연속 광량/반사/AO는 없다. 모델/UV/96px/m/카메라 유지, Unity 변경 없음. 실제 `LocalOnly/DeskBlender17/base01/desk.blend`/136×133 `desk.png`, 렌더22.44초.
- `[기술 확인/미술 대기]` `technical-result.json`: 승인재료SHA/geometry/projection/UV 유지, 저장blend의shadow만 끈 비교21.17초에서249픽셀차이/alpha동일, 출력재축소없음. 기술게이트exit0. `state.json`의review ticket `11abf89759814718a954e60255dfc1a8`에서 사용자판정대기. 광원방향과노드L의임의편집자동동기화/Unity/자유회전/모든입력모딩검증은없음. 미술완료커밋없음.

## 153. D18 내부 면경계와 화면 투영 세부 폭 `[PIXEL-01]`

- `[최신 요구]` D17은조금나아졌지만불충분. 확인질문자제,목재계열내부선/면구분과픽셀보다작은서랍세부수정요청. 이전graph에는실제추가수정응답을기록했다.
- `[구현]` 동일quad면ID패스와가시면경계한쪽소유규칙으로native1px내부선을계산. 실제projection의경계수직폭공식으로서랍틈27mm/앞판33mm/실제옆틀돌출33mm/틀폭45mm/손잡이두께50mm로조정하고후퇴36mm를연결해전체1.2×0.6×0.74m보존. 나뭇결/UV/명암색/96px/m/카메라동일. 금속subpixel bevel제거·겹치는틀모서리정상접합.
- `[실제 실행/검사]` `LocalOnly/DeskBlender18/base01/desk.blend`/136×133 `desk.png`; Build20.40초/저장재개19.93초. `technical-result.json`은승인재료·전체치수·projection·UV보존,목표투영폭,10필수면의선내본색잔존,ID/색alpha일치,내부선1266픽셀,저장PNG재현을확인했다. 세부수정산출물범위graph완료이며미술합격은포함하지않는다. 확인질문없이전달;자유시점/일반mesh/Unity통합미검증. 현재규약은 `Tools/PixelDesk/INTERNAL_EDGE_PLAN.md`.

## 154. D20 생성 기준과 실제3D 재현 `[PIXEL-01]`

- 새 생성원본1장과 실제12솔리드/동일4다리/목재로컬UV/면색을 Blender5.2로 렌더했다. `LocalOnly/DeskReference20/`에 모델/원본/비교/측정을 보존했다. 원본1536×1024 전경 무정렬비교와 별도192×128 큰픽셀렌더다.
- IoU95.57272%, RGB채널당8이하50.05545%, 정확RGB3.11027%로99%재현실패. 동일다리/발Z0/접합/공통투영오차0.000372px미만은 확인했으나 부위별무늬/국소색/형상차이는남는다. 모든3D방식불가능주장이나미술승인없음.
- crop UV/색전달 기술수정1회후 미술반복중단. WorkLoop최종입력키오류는프로세스호출전중단확인, 파일검사전용graph복구exit0. 증거완비와99%성공false를구분한다. 기존파일/Unity보존. 계약/재개조건은 `Tools/PixelDeskReference20/README.md`.

## 155. D21 디자인 요소별 실행과 수학적 오류 수정 `[PIXEL-01]`

- `[요청/구현]` 실제 제작 요소별 작업 그래프와 결과 부족의 수학적 진단을 구현해 보라는 요청. 기존 WorkLoop를 변경 없이 사용하고 `Tools/PixelPipeline`에 입력/실제기하/원본PerfectPixel재료/픽셀광선/명암/경계/진단/수선/제출을 독립 실행 단위로 연결했다. 최종 결과 존재나 AI의 완료 선언만으로 합격시키지 않는다.
- `[실제 수선]` 서랍 앞판 두께.036m와45도시점이 틈을 가리는 조건을 구간교집합으로 계산. 실제투과폭0→2.000003px가 되도록 공통gap약.065463m를 선택하고 앞판 span/손잡이정렬/96PPU를 보존했다. 내부선의 수평/수직 midpoint 소유면 교대도 발견해 가시 면 쌍별 일관된 선 배치로 수정했다. 접합점 제외 평행경계 양면중복68→0, 독립측정 상판↔서랍정면43→0.
- `[실행/복구]` 첫 진단의 NumPy bool 직렬화 오류는 앞6단계 보존 후 recover했다. 완료 뒤 독립감사로 확인된 실제 내부선 결함은 증거SHA와 이전진단/제출/검사를 보존하며 reopen했다. 마지막 복구3.824초, raster/model/shade는 pass1과 같은 SHA이며 알고리즘 재실행 없음. 처음부터 완전한 판정기가 있었다거나 전체제작3.8초라고 주장하지 않는다.
- `[최종 증거]` `LocalOnly/PixelPipeline21/run01/pass-2/package/`:174×155최종PNG,6배표시,비교/HTML/기하blend. `pass2-final-audit.json`:가시선828기록 owner불일치0,mask밖ink0,기존43직선중복소거. 실제정수alpha/12재료명암색+경계색/4다리치수·접지·정렬·실제shadow관측 통과. 제어기19개/단계회귀8개/재료6개확인은 실제제작과 구분해 기록했다.
- `[미완료 범위]` 사용자 외형승인/99%재현/전역모든교차점1px선폭/임의메시 모딩/Unity통합은 완료가 아니다. 전체crosspart인접ink18쌍을 모두 정상이라고 간주하지 않았다. 기존Unity/D20파일과 사용자변경을 보존했다. 연구의 현재 결정·반례·재개 조건은 `docs/references/pixel_desk_shading_research.md` D21, 실행은 `Tools/PixelPipeline/README.md`.

## 156. D22 기지의 고정 PNG와 실제 3D 조명 비교 `[PIXEL-01]`

- `[요청/구현]` 기지 기존 램프 옆에 A 고정 명암 PNG / B 실제12메시를 저장했다. 원재료4색 grain과 동적 normal·shadow·local 조명을 분리한 URP 셰이더, 고정96PPU 투영과 실제 게임 카메라 촬영을 `Tools/PixelUnityProbe` 그래프로 연결했다. 최종 PNG를 B의 재질로 사용하지 않는다.
- `[실제 Play Mode]` trial03:960×576 출력에서 A 원본RGB오차0, B 실루엣IoU1.0, 무조명원재료4색 외 픽셀0. 주광반전 A0/B1,015픽셀변화. 기존로컬광 입사량9,133픽셀변화/최종색1픽셀변화로, 빛입력과 양자화 결과를 구분했다. Console Error/Exception 0과 shader compile을 별도로 확인했다.
- `[실패/수정]` 첫 조명무반응은 Forward+ `_CLUSTER_LIGHT_LOOP` 변형 누락을 수정했고 근거없는 주광0.5계수는1로 복원했다. trial02는 촬영완료 전Play종료로 차단됐고 성공증거에서 제외했다. trial03은 background촬영/완료기록 확인을 사용했다. 원래 실패파일은 덮어쓰지 않았다.
- `[보존/한계]` 비교대상 외 기존 씬/램프/플레이어를 유지했고 테스트 임시 카메라·시간·조명 상태를 복원한 뒤 Play를 종료했다. GameMap1 비교배치를 저장하고 원래 활성GameMapTest를 다시 열었다. 전체 게임의 자유줌/회전, 로컬광 시각반응의 충분함, 추가Unity Point/Spot, 임의모딩과 미술승인은 미완료다. 상세 계약/실행은 `Tools/PixelUnityProbe/README.md`, 실제캡처는 `LocalOnly/PixelUnityProbe22/trial03`.

## 157. D23 기본 조명 복원과 기존 오브젝트 픽셀 셀 연결 `[PIXEL-01]`

- `[요구/원인]` 사용자는 잘린 다리·독립적인 책상 조명·너무 작은 픽셀을 지적하고 추가 검사보다 픽셀 크기 수정을 우선했다. 최종 기본 원칙은 원인 없는 상태/동작 변경 금지다. 기존 형상과 목재 원본을 유지했다.
- `[구현]` 책상의 자체 최소 광량·고정 임계값을 제거하고 캐릭터와 같은 `UniversalFragmentPBR` 및 RGB 로컬광 경로를 사용했다. PNG 평면은 고정 시점 투영을 유지하면서 수직화/불투명 하단 접지했고 비교 쌍을 빈 바닥으로 함께 이동했다. 실제 3D는 기존 `CharacterSilhouetteSubject`/renderer feature에 연결하여 화면 2×2 픽셀 셀로 표시한다. 캐릭터 설정이나 전역 화면 해상도는 변경하지 않았다.
- `[실행]` 조명 수정 당시 trial23에서 주광 반전 9,274픽셀, 로컬광 3,710픽셀 변화와 RGB 반응을 관측했다. 전체 기지의 고정 PNG 114픽셀 차이로 기존 분석은 accepted=false를 보존했다. URP Unlit의 SSAO 적용 코드를 확인했지만 사용자의 검사 중단 정정 이후 원인 대조 촬영은 수행하지 않았다. 이 수치는 후속 2px 변경의 검증으로 재사용하지 않는다.
- `[최종 관측]` `LocalOnly/WorkLoop/desk-pixel-size-23-v2`를 실제 실행하여 Unity 반환값 size=2, 실제 게임 카메라의 960×576 미리보기 `LocalOnly/PixelUnityProbe22/pixel23/captures/context.png` 1회를 기록했다. 셰이더 컴파일 성공, 최종 Console Error/Exception/Assert 0. 임시 촬영 상태 복원 후 Play 종료, 활성 GameMap1 저장. 미술 합격/자유 시점/임의 모딩은 미검증이다.
- `[실행기/재개]` Higgsfield 공식 Canvas·Supercomputer·MCP 자료와 비교하여 기존 WorkLoop에 `pipeline.py`/고정 `pixel_object` 프로필을 추가했다. 변경 허용 필드와 원인, 실제 반환 파일, 최종 사용자 피드백 대기를 관리한다. 도구 호출 진위나 실행기 밖 AI 행동을 보안적으로 강제하지 않는다. 현재 `awaiting_user_visual_feedback`; 새 사용자 원인이 생기기 전 추가 수정·재촬영은 하지 않는다. 상세는 `Tools/WorkLoop/README.md`, `Tools/PixelUnityProbe/README.md`, 연구 문서 D23.

## 158. D24–25 실제 Play 8방향과 셀 경계 수정 `[PIXEL-01]`

- `[정정]` D23은 실제 PlayerCamera 객체의 설정을 촬영용으로 바꿨으므로 원래 Play 화면과 같지 않았다. 사용자 요청대로 기존 3D 책상 8개를 45도 간격으로 배치했다. 시작점과 남쪽 배치는 각각 기둥/큰 시험 구조물에 가려 실패했으며 두 화면을 보존했다. 실제 Renderer bounds 중첩 0인 동쪽 후보를 확인해 공통 루트만 (15,0,0)으로 옮겼다. 기존 비교는 삭제하지 않고 비활성화했다.
- `[수정]` 고정 시점/96PPU의1px 경계 캐시를 셀 모드에서 제외했다. 12개 box part ID와 실제 가시 face ID를 기존 `neighbor.group < center.group` 단일 소유자 경계로 연결했다. 셀 합성 전체가 stencil bit2를 기록하여 후속 fullscreen 로컬광의 셀 부분 적용을 막는다. 공유 composite 수정은 기존 local-light 포함 cell source의 계약 복원이며 새 명암식은 아니다.
- `[실행/범위]` 기존 PlayerMovement.TryTeleport로 Player를 동쪽 관찰 위치로 옮긴 뒤 CameraFollow가 따라가게 했다. 실제 Play 카메라 Euler(45,350,0)/size5, display target, part0..11, desk yaw45*i/size2를 반환했다. 셰이더 컴파일 성공. `LocalOnly/WorkLoop/desk-cell-edges25-final/preview.png`는 ScreenCapture로 저장한 실제1114×857 Game View이며 해당 게임 시간의 어두운 조명도 그대로다. 카메라·시간·조명 제어를 촬영용으로 바꾸지 않았다.
- `[현재]` graph `state-v2.json`은 사용자 피드백 대기다. 물체/재료/기존 게임 설정은 보존했고 현재 Play에서 동쪽 구역을 볼 수 있다. 재진입은 `Tools/Pixel Desk/Inspect Eight Directions with Normal Player Camera`; 시작 spawn은 그대로다. 외형 만족·셀보다 얇은 형상·임의 곡면·모든 표시 배율은 미검증이다. 픽셀 통계로 미술 합격을 선언하지 않았다.

## 159. D26 평면 바닥의 2px 주광 그림자 수광 `[PIXEL-01]`

- `[요구/확인]` 책상 그림자도 픽셀 단위로 표시하라는 요청. 실제 플레이어 visible9 renderer는 cast Off이며 shader에 ShadowCaster가 없어 기존 캐릭터 바닥 그림자 기능을 복사하는 경로는 없었다. 캐릭터 표면 수광 셀과 바닥 투사 그림자를 구분했다.
- `[구현]` 기존 URPToonLit에 기본값0인 `_ShadowScreenCellSize`를 추가했다. 화면 셀 중심을 inverseVP near/far 광선으로 복원한 뒤 실제 평면과 교차시켜 주광 shadow lookup 위치만 고정한다. GameMap1 Ground에만 원래 재료를 복사한 GroundPixelShadow(size2)를 연결했으며 원본 Small Ground/texture/Tint/LightPower는 보존했다. 몸체/무늬/배치/카메라/광원/그림자세기/PCF 변경은 없다.
- `[실행]` Unity shader compile 및 최종 Console Error/Exception/Assert0. 실제 Play camera(45,350,0)/size5, body8개 size2, shadow2/원본0와 재료 속성 동일을 반환했다. `LocalOnly/WorkLoop/desk-shadow26/preview.png`에 실제 Game View 1회. 사용자 피드백 대기이며 그림자 품질 자동 합격은 아니다.
- `[범위]` 같은 Ground의 모든 주광 그림자에 적용된다. 곡면·추가광·SSAO·모든 플랫폼은 미검증/비대상이다. 근평행 ray는 원샘플 유지. 연구 D26과 Tools/PixelUnityProbe에 입력·식·실패조건을 기록했다.

## 160. A27 도심 용도별 평면도·실제 2층 프로토타입 `[MAP-01][POI-01]`

- `[요구/연구]` 사용자 요청은 미완성 도심의 설계도·방 분리·넓은 내부·실제 2층·마트/경찰서/주차장 프로토타입이다. 기존 road graph/OBB 필지를 유지하고 architectural program→직교 평면도→동일 원본의 Mesh/Collider→기존 NavMesh를 채택했다. CGA 외관 문법과 WFC 국소 패턴만으로 전체 동선을 보장할 수 없어 주 구조에 채택하지 않았다. 자료·수학·50종 카탈로그 확장안은 `docs/references/urban_architecture_prototype.md`.
- `[구현]` `UrbanArchitecturePlan`은 마트 1층(판매/창고/직원), 경찰·주거 2층(각6개 기능 방과6개 홀/복도) 및 별도 주차 필지를 기존 layout에 연결한다. 생성 버전12, atlas checkpoint 버전1008, plan stable hash 포함. 대표 건물은 14×12m 이상 필지만 선택하며 강제 축소하지 않는다. 기본 문1.6m/복도2.4m/계단2.2m/층고3.4m. 실제 상층 slab는 계단 영역을 제외하고 시각 단과 이동 ramp Collider는 같은 시작·끝을 쓴다. 기존 Player/입력/카메라/재료·Medical 보상 owner를 유지한다.
- `[사용자 정정/실패 보존]` 사용자가 계단 접근·임의 설계를 지적했다. v1은 계단 왕복 자체는 통과했지만 경찰 상층 방 PathPartial와 주거 침실 중심 목표 실패가 남았다. `readback-v1.json` 보존. SF Planning Trocadero 보고서 p23의 현관→계단홀→직선계단→상층복도 유형을 참고해 낮은 계단 끝을 앞 로비로 연결했다. 하층 벽을 상층 slab 아래까지로 제한하여 벽 top의 coplanar NotWalkable 경계를 제거했고 방 도착점은 가구가 놓일 수 있는 중심 대신 문 안쪽 WalkAnchor로 정의했다. 각 개별 가설의 분리실험 없이 복합 수정 후 대표 동작을 확인한 것이므로 단일 원인을 독립 입증했다고 확대하지 않는다.
- `[실행]` `LocalOnly/WorkLoop/urban-architecture27/readback.json`: seed1462661998 대표 마트3/경찰12/주거12 공간 도달, 두 계단 상승·하강/NavMesh 연결, 주차 보행 진입, prop/wall 침투0, 층별 floor/roof 숨김·복원과 Collider 유지. 기존 Player/Camera 참조 및 정상 도심 카메라(30°,45°,0°)/size5 유지. **Play Mode 호출 확인**이며 물리키 조작과 전 seed/Recovery 복구 테스트는 미실행. Console Error/Exception/Assert0 확인. 기존 최종 관측 후 legacy 장식 metadata에서 새 평면도 소유 건물의 미사용 slot을 제외했으며 장면 기하는 동일하다.
- `[출력/재개]` `floorplans.json/png`는 실제 plan 데이터에서 작성했다. `supermarket/police/residential/parking.png`는 정상 Game View, 기존 게임 조명 그대로다. Unity 메뉴 `Tools/Urban Architecture/Inspect ...`로 같은 Player를 해당 관찰점에 이동한다. 기존 도심 아트를 재사용한 구조 시제품이며 완성 픽셀 아트나 용도50종 완료가 아니다. 주방/욕실/경찰 특수설비·창호·하역/차량진입 세부·더 다양한 평면도는 남았다. `state-v2.json` 기술 관측 뒤 사용자 외형/동선 판단으로 인계하며 자동 시각 합격하지 않는다. 기존 미커밋 도심 코드·미추적 에셋 의존성이 있어 이번 파일만 독립 로컬 커밋하지 않는다.
- `[사용자 확정]` 후속 답변 “구조 유지, 세부 설비·디자인은 다음 작업”을 수신해 현재 계단·방·복도 구조를 프로토타입 기준으로 확정했다. 실제 답변을 WorkLoop review에 기록했고 새 시각 보정·설비 구현·Unity 재검증은 하지 않았다. 완성 아트 승인과 구분한다.

## 161. A28 크기별 상가 평면·기본 설비·서비스 출입 `[MAP-01][POI-01]`

- `[요구/설계]` 건물별 크기/설계도를 현실 건축 참고로 구성하고 상가를 먼저 하라는 요청. 공식 상가 도면/설계설명 4건의 판매·접객·지원·WC·납품 역할을 참조했다. 도면 이미지가 아닌 PDF 추출 텍스트 확인이며 좌우 배치를 그대로 복제하거나 건축 법규 인증을 주장하지 않는다. 근거/계산식/계약은 `docs/references/urban_architecture_prototype.md` A28.
- `[구현]` `UrbanCommercialFloorPlans`의 마트(후방 횡복도), 카페(접객/주문/주방), 소매점(후방 종복도) 3유형, 기존 OBB의 실제12~18×10~14m 적용. 방·partition·납품문은 한 plan에서 mesh/collider를 만든다. 일반실최소2.4m/복도1.8m/문1.6m/납품문1.8m, 고객 WC가 주방·창고·직원실을 필수 경유하지 않는 BFS. generator13/checkpoint1009. 의료 POI·기존 경찰/주거·도로·Player/Camera 경로 유지.
- `[설비]` 기존 선반/책상 unit scale 재사용. 변기·세면대·조리싱크/작업대·주문/계산대·테이블/의자는 별도 고정치수 기하 프로토타입이다. 카운터가 공개구역 뒤 문을 막거나 주방 기구가 납품문 양쪽을 침범하는 반례를 수정: 모든 partition 문폭×양쪽1.4m, 납품문 전체폭×내측1.9m를 배치 제외 영역으로 예약. 완성 픽셀 가구라는 주장은 하지 않는다.
- `[검증]` 3유형×4폭×3깊이=36 평면조합 통과. seed1462661998 상가30개/8크기, 전체plan 유효/배치누락0. 대표마트16×14m 5공간·카페12×10m 7공간·소매12×12m 5공간의 정문→모든방→납품문→외부→정문 복귀를 실제 기존 StepMove/CharacterController로 관측. 대표 prop-wall/prop-prop 침투0, 가림/Collider 보존, 같은Player/Camera 및 30°/45°/size5 유지. A27 저장 경찰/주거 plan을 같은크기로 재계산해 방/벽/계단 동일 확인. Console Error/Exception/Assert0. 물리키·전seed·30곳모두의실제이동·Recovery/빌드는 미실행.
- `[관측/실패보존]` `LocalOnly/WorkLoop/urban-commercial28/readback.json` SHA256 `CFC8FC7A33B514E42A80CC819B3C9CC74C06917056C2C2AC348437036DDDA299`. 초기 씬 도착 전 frame2 NavMesh미준비 실패는 `readback-before-arrival.json` 보존; 실제20프레임으로 기존 초기화 완료와 NavReady 확인 후 최종관측. ScreenCapture 지연으로 마트는 GameView, 카페/소매는 실제동일카메라 URP SingleCameraRequest(overlayUI 제외)로 저장. 각도/줌/targetTexture설정/조명을 변경하지 않았다.
- `[그래프/전달]` 원 그래프에서 읽기입력 design.md를 결과 기록으로 갱신해 의존성이 무효화되었다. 원 state 정지 보존; 고정 checker/실제 관측을 그대로 소비하는 검증 인계 graph를 실행해 exit0/errors[] 확인. `validation-state.json`의 review ticket `0eb7337347ac442eaf669f0a4b9787bc`는 사용자 외형/배치 답변 대기. PNG3개·동일축척floorplans.png 및 `Tools/Urban Architecture/Inspect Cafe / Retail Shop / Supermarket` 제공. 이후 주거 세부·다층상가·창호·최종픽셀설비·차량하역은 후속. 기존 미커밋/미추적 도심 의존성을 임의 stage하지 않아 로컬 커밋은 보류했다.

## 162. Unity 네이티브 종료 후 작업 보존·재진입 확인 `[MAP-01][POI-01]`

- `[사실]` 2026-09-20 16:26 네이티브 크래시. 마지막 managed stack Event.get_keyCode→GUIView.ProcessEvent이며, 직전 dt assertion/PlayerMovement 인자예외와 직접 인과관계는 미확정이다. 근거 없이 이동 코드를 변경하지 않았다.
- `[복구]` 최신 `_Recovery/0 (2).unity`와 저장 GameMap1 SHA256 동일, 상가 소스/에셋/참조 유지. 손실 확인 없이 덮어쓰지 않았다. `LocalOnly/Recovery/20260920-editor-recovery/`에 원본·복구본·dump·변경 ZIP215파일·해시 목록을 보존했다. 기지씬 큰diff는533개동일fileID의블록순서가대부분이며 실제값7블록만변경되어 기존광원/렌더레이어값을 보존한다.
- `[Play Mode 호출 확인]` 정상 기지→도심 진입1회, seed1462661998/115동/상가30/3유형/NavMesh준비, 같은Player/Camera와30°/45°카메라유지. 누락스크립트0·깨진직렬화참조0·Console오류0. 기존상가전체방동선검증은 재실행하지 않고 §160~161을 재사용했다. 확인 후 Play종료, 저장된기지편집상태복귀.
- `[기록/미완료]` 사용자의명시요청으로 미커밋도심코드·에셋의존성과현재기지상태를 로컬커밋대상으로 정리했다. 공유문서의무관한변경과캐릭터/책상실험은 분리한다. 크래시원인수정·가구밀도/체감비율·최종아트는 미완료다. 상세근거는 `docs/references/unity_editor_recovery_20260920.md`.

## 163. B31 개별 네이티브 픽셀 점포·기본30° 카메라 `[MAP-01][CAMERA-01]`

- `[요구/교체]` 사용자가 전체 맵 생성·축소 A30을 거절하고 개별 오브젝트로 조립한 기지 테스트 건물1채를 요청했다. 이후 기본 카메라30°를 명시 승인했다. A30은 보존만 하며 이번 원본으로 사용하지 않는다.
- `[구현]` CC0 hawkbirdtree 320×960 원본의 정수crop16종, 리샘플링0회. PixelLab get_balance는 만료/가용0을 반환하여 생성 호출/결제는 하지 않았다. `Assets/Art/NativePixelBuilding31/`, `NativePixelBuildingAuthoring`, `NativePixelBuilding`과 `NativePixelShop31.prefab`을 추가하고 GameMap1(-16,0,9)에 배치했다. 바닥10×8m, 점포/계산대/재고 구역, 열린2m출입구, 개별가구와지붕. Renderer78/Collider55/MissingScript0.
- `[수학/보존]` 원본64×32tile=2m, PPU16√2, wall48px=2.44949m, camera30°/350°·건물305°. 기존PersistentGameplayShell카메라/Follow offset만30°로 갱신했다. 실제 셸·입력소유자·카메라줌·기지오브젝트/도심은 보존. UrbanOcclusionFader의 뒤벽실내유지 옵션은 기존호출 기본true를 보존한다. 표면위소품의depth tie는 시선방향투영으로 화면좌표를 보존하며해결했다.
- `[Play Mode 호출 확인]` PlayerMovement.StepMove/CharacterController: 입구통과local(0,.565,-.3), 벽충돌정지(3.95,.565,-.625), 같은Player/Camera. 실내벽fade10/지붕숨김20, 외부지붕숨김0. 실제camera30°/350°/size5, GameView1114×857 캡처. 신규Console오류0, 기존UnityAI relay종료오류1은보존. 물리키/전체회전/빌드/저장로드는 미실행.
- `[전달/제약]` `docs/artifacts/building31/` 관측/PNG, `docs/references/grave_seasons_map_art.md` B31, `Tools/Building31/graph.json` 기술조건exit0·review대기. native픽셀보존과화면정수배율은별개: 실제확대3.78744배. 자유오빗다른각도·동적표면조명·문짝/루팅·2층은미구현. Play종료후저장편집상태복귀. `Tools/World Art/Inspect Native Pixel Shop 31`로기존Player를점포내부로옮겨볼수있다. 사용자외형합격은대기다.

## 164. B32 SceneView 정렬·배치 설계·원본 픽셀 coverage 원인 `[CAMERA-01][MAP-01]`

- `[사용자 정정]` B31 미술·디테일·명암·배치를 거절, 크기는 대략 유지 가능. 임의 배치 대신 기술/기획/배치설계부터, SceneView도 기본 시점 정렬 요청. B31 사용자 피드백을 기존 WorkLoop에 반환해 거절 상태로 남겼다.
- `[구현/Editor 관측]` NativePixelBuildingAuthoring의 기존 Inspect(Edit Mode)와 Align Scene View 메뉴가 실제 PersistentGameplayShell PlayerCamera 방향/직교 설정을 읽는다. SceneView21.45°/310.12°→30°/350°,orthographic 확인. 게임 카메라/Player/씬 오브젝트 변경 없음. SceneView 캡처1회. 게임 전용 조명 pass까지 SceneView와 같다는 검증은 아니다.
- `[연구/설계]` Grave Seasons 공식 평면2D·sprite분할·수작업 조명/LUT, 작가3명·픽셀추상화 논문·Merrell 배치연구·Unity FullRect/PPC를 통합 연구 B32에 연결했다. 시설5개/사용점6개 후보 JSON→SVG, 점유·사용공간·벽 부착·문폭 위반0, 보수적 팽창/4방향 BFS6/6연결. 실제 Unity 배치/Player 이동/미술 합격은 미실행이다.
- `[원인/격리GPU]` 전역픽셀효과OFF/캐릭터효과비대상, 기본재질조명0이나 fullscreen로컬광ON. 현재비정수배율3.78744와 geometry경계clip을 구분했다. 고정30°/45°·정수4배·같은floor PNG/재질로 기존diamond는 expected18,368 화면칸 중1,984누락,FullRect누락0/추가0. 원본을 편집하거나 재픽셀화하지 않았다. 각2case1회이며 전체건물수정이 아니다.
- `[보존/검증]` preview생성의 transientdirty는 save-as-copy와 기존GameMap1 byte-identical 확인 후 동일내용저장으로 clean복귀. GameMap1 diff0. 신규Console오류0, 기존09:50UnityAIrelay오류1보존. 실제기지출입/가림은 §163증거재사용. source코드의Mesh명확화·청소처리는 실제실행한조각을최종파일에반영했고기하재시험하지않았다.
- `[범위/인계]` Tools/Building32 그래프는 도면기하+격리coverage 실험만완료. docs/artifacts/building32에SVG/JSON/원본렌더PNG/실측TXT 보존. 새개별아트·tile연결/깊이·정수줌/phase·조명합성·실제게임통합/미술승인은미완료. 다음부위는 통합연구의대표자산명세와표시계약이다.

## 165. B33 건물 통합·중도 종료 감사·가변 픽셀 원본 보존 `[MAP-01][CAMERA-01]`

- `[요구/실패 정정]` 질문 직후 종료 원인 조사와 실제 건물 마무리. AGENTS의 중간 시각 승인 해석, B31 모든 피드백의 blocked 분기, B32의 부모 제작 목표 누락을 확인했다. 공식 Astra 행동 안내와 공개 이슈4건은 `docs/references/codex_interruption_research.md`. 중간 산출물마다 승인받지 않고 최종 관찰 단위까지 이어 가도록 기존 AGENTS 문장과 WorkLoop 안내를 교체했다. 서버/컨텍스트/Ultra만의 원인으로 확정하지 않았다.
- `[제작/사용자 정정]` GPT 개별 원본9종을 Source에 보존하고 기존 수정 PerfectPixel source_regions로 정규화했다. 첫 B33은64canvas의 비균일 fitting으로 비례와 정보를 손상시켜 사용자가 거절했다. 완료로 승격하지 않았다. 최신 계약은 물체별 실제 크기는 다르고 픽셀 밀도만 공통이다. `normalize_uniform.py`는 각 B32 예약공간과 원본 종횡비에서 단일q를 계산해 가변canvas를 만든다. 계산대102×85/뒤선반109×126/왼선반71×118/진열섬89×64/재고선반94×119, PPU32√2. 정수화 오차<1texel과 원본RGB표본 보존은 확인했지만 원본 내부 각도/CAD 높이를 고친 것은 아니다. 원본과 첫 거절본을 보존했다.
- `[Unity 통합]` GameMap1(-16,0,9)의 같은 B33 prefab에 개별 아트/메시/재질 참조를 적용했다. 물리 proxy는 B32 예약공간 안에서 개별 크기를 갖는다. 벽·바닥·지붕의 계획 위치와 기존 Player/Camera/입력 owner는 보존했다. FullRect source alpha, 공통 격자와 기존 CameraZoomController opt-in 정수줌; 전역 PixelArtRendererFeature OFF. foundation은 벽 footprint를 채우며 동일 높이·먼저 그리기·ZWrite0으로 coplanar 가림을 피한다. shader forward/depth/normal은 같은alpha와격자를 사용한다.
- `[조명 근본 원인/수정]` 광원component2개가 있어도 최초 ON/OFF 차이0. 상수 fullscreen probe는 실행되나 Sample/Load depth는0이었다. 기존 CharacterSilhouetteRendererFeature만 잠시 끄면200,487화면pixel이 변했다. 해당 owner의 초기 world-depth copy와 최종 publish가 공유 material의 입력을 서로 덮어썼다. 두 draw에 MaterialPropertyBlock으로 각 입력을 고정했다. 캐릭터 픽셀 기능을 다시 켠 최종 ON/OFF 차이195,848pixel로 실제 기여 확인. 광원강도 증폭이나 새필터로 우회하지 않았다. 기존 radial광원은 실내벽차폐/세련된 lightmask를 보장하지 않는다.
- `[Play Mode 호출 확인]` 기존 StepMove/CharacterController로6개사용점6/6,벽정지,실내지붕숨김/앞벽fade; 같은Player/Camera entityID. 실제camera30°/350°/ortho4.734301/viewport높이857. 가구5개 각각 source texel X/Y 화면길이2.0(최대오차0.00008pixel),각Transformscale1,서로다른mesh·texture크기. 예약공간초과0,MissingScript0,신규Console오류0. 기존09:50UnityAI relay오류1은보존했다. 키보드 직접입력·다른회전·빌드·저장로드는 이번범위에서 미실행.
- `[납품/한계]` `docs/artifacts/building33-uniform/`의실제GameView·readback·unity-display·technical-result와`Tools/Building33/uniform-graph.json` 기술조건통과. 이전B33실행은사용자정정으로정지보존했으며실행중합격기준을바꾸지않았다. source내부투영·높이추정·원작동등미술품질은미승인. Play종료/runInBackground원복,GameMap1저장clean,SceneView30°실내개발보기. `Tools > World Art > Inspect Planned Pixel Shop 33`으로같은건물관찰.

## 166. B33 원본 격자 우회 원인・Astra 운영 계약 재구성 `[MAP-01][PIXEL-01]`

- `[사용자 정정]` 가변 크기 수정도 강제 축소라 특징이 손실됐고 질문 직후 종료가 반복됨. 개별 외형 패치보다 Astra Ultra 리뷰와 생성・배치・정규화 운영 방식 교정을 우선 요청. §165의 기술 조건은 원본 보존/디자인 완성 증거가 아니며 두 B33 외형은 거절 상태다.
- `[직접 원인]` 원본 PerfectPixel 자동 격자 API 대신 슬롯/PPU 기반 target을 수정판 source_regions에 넘겼다. 계산대 crop1179×992→102×85. 출력 RGB 표본/정수 texel 검사로 특징 보존을 주장할 수 없다. 공식 Astra 안내와 공개 Unity Ultra/목표 이탈/조기 종료/압축 사례는 `codex_interruption_research.md`에 출처・한계를 구분했다. 특정 모델/서버 원인 확정은 하지 않았다.
- `[구현]` 기존 운영 문장 중복과 형식적 최종 질문 의무를 제거하고 playbook §1.6에 요구・원본・템플릿・첫 불일치・허용 변경・원래 증상 판정을 연결했다. 게임 불변조건/기존 사용자 변경은 보존. B33 두 Python 제작 main과 Unity Build/Apply는 명시적 retired 오류로 실행 전 차단한다. Inspect/현재 씬은 유지한다.
- `[원본 실행 1회]` native_normalize.py는 원본 public selector→NumPy backend의 자동검출을 사용한다. 입력1374×1145 RGBA에서275×229 추정, 경계 정렬 후274×228. 수동목표/crop/resize/알파 threshold/경계보정 없음. 같은 upstream 셀 중심에서 RGBA 샘플링. 원본파일・엔진・출력 해시/좌표 receipt와 native.png 보존. 기존5개강제크기옵션 거절, 원본단색입력실패를 실패receipt로 보존하며 임의fallback없음, 기존출력 덮어쓰기 거절.
- `[실제 확인]` Unity Edit Mode에서두퇴역진입점2/2거절, GameMap1 dirty false→false. remediation-graph의 고정7case(legacy CLI2,원본실제산출,옛manifest거절,기준아트없는생성거절,배치solver미등록거절,Unity관측)통과. source-center별RGBA는실제원본과전부비교; 이는원본자동경로/출처범위이지미술합격아님. 일반계산만연속실행하며원본이미지정규화는재실행하지않았다.
- `[남은 범위]` 전체상가기준아트・개별자산대응・공통투영calibration・새Unity통합은 미완료. 최신 운영교정 우선요청에 따라 새 생성/씬교체는 수행하지 않았다. 로컬gate는 Codex전체도구/모델/서버/턴종료를 통제하는 sandbox가 아니다. 기존게임기능Play/빌드/저장로드검증은 변경원인이없어 반복하지 않았다.

## 167. B34 기지 상가 내부·원본 자동 격자·깊이/지붕 교정 `[MAP-01][CAMERA-01]`

- `[요구/구현]` 사용자 요청은 문제점을 고치고 건물 내부 한 채를 실제로 완성하는 것. GameMap1(-16,0,9)의 같은 PlannedPixelShop33 prefab에 개별 계산대·판매선반2개·진열섬·재고선반, 별도 재고실/목재바닥/벽/지붕/램프2개를 조립했다. 원본 Player/Camera·입력·B32평면·사용점 보존. 이전B33/최초B34는 비활성 보존했다. 미술 합격은 자기 선언하지 않는다.
- `[원본]` 원본PerfectPixel 자동검출9종, 수동target/resize/crop 없음. 각nativePNG 해시 보존. 생성한 master-reference는 참고용이며 게임 배경으로 쓰지 않는다. 새목재 재료1254×1254→자동125×132, 원본과receipt를 보존하고 표면 재료로만 샘플한다.
- `[깊이 원인]` 기존 세로quad는 그림의바닥깊이까지월드높이로읽어 선반3.23m/지붕2.46m가되었다. 고정뷰ray/cuboid교점XYZ를texel별저장,Forward/Depth/Normal모두동일SV_Depth. 원본opaque센터/네corner miss0. 닫힌roof는독립opaquecoverage로바닥alpha재사용없음.
- `[실패/교정]` 처음가구장축불일치를포함제약만으로처리해PPU181로너무작게보였다. 시설사용면에맞춰원본4종mirrorU를UV/깊이에같이적용,공통127px/m. near벽도XMIN/ZMIN으로교정. 원본내부각도/밀도차이까지수정한것은아니다. 실내앞벽/칸막이는하단.55m를남기고상부fade,물리벽/출입구보존.
- `[조명]` 기존SteppedLocalLight에선택적인2boxunion범위를추가,이번판매공간2구역연결. 미지정기존광원은기존동작. 새램프기여.12/6bands,큰원판의.12밝기점프를축소. 이는영역제한이지동적가구그림자/전체실내광차폐아님.
- `[Play Mode 호출 확인]` 기존StepMove6/6접근점·벽정지·실내지붕숨김/외부복원,동일Player/Camera EntityID. 카메라30°/350°,1114×857에서source1texel=screen1pixel. native surface25,source/depth불일치0/frame누출0/roof누출0. 화면4장과JSON은docs/artifacts/building34. overview2560×1600은같은카메라재프레이밍으로실제걷기화면과구분한다.
- `[검증 실패를 보존]` 최초2560×1800촬영이기존캐릭터대표인덱스상한초과/URP후속오류발생. 촬영해상도만2560×1600으로교정. 오류0수동기록은자동승인검토거부;기존Console지우거나수정하지않음. 이후실제내외부렌더전후MCP전체응답11→11,추가오류0을Counter로계산했다. 기존relay1/최초촬영관련10기록보존. volumetricSpotLight가시성/개수경고별도보존.
- `[납품/한계]` 기존graph/방향교정graph미완료상태보존,최종관측전후증거용graph-final-validation은고정조건통과. delivery-final-result.json은기술범위이며원작동등미술합격은아니다. 자유회전·키보드입력·빌드·저장로드·GPU성능미검증. 작은viewport의기존줌범위와native1배보존불일치노출. 메뉴Tools/World Art/Inspect Completed Shop Interior 34로편집SceneView/Play기존Player접근가능.

## 168. B35 원본 면 투영과 실제 상점 역할 배치 `[MAP-01]`

- `[원인]` B34 bbox 적합/좌우반전은 그려진 모서리 기울기를 바꾸지 못했다. 왼쪽 벽+X 앞면도 현재 카메라와 반대였다. PZ/Grave Seasons 공식 실내15장을 실제 관찰해 사물·지지면·용도를 분리하고, 판재3면 homography 최소실험 후 같은 prefab에 적용했다.
- `[구현]` 선반3개 재투영, 가려진상판대신 신규 빈계산대/진열섬템플릿, 냉장장·세척대·청소수납장과 개별소품. 실제20개(가구8/상판3/화분2/물류통2/상자5), painted 선반물품은 추가로계수하지않음. 사용면을맞춰판매선반은오른쪽벽,냉장장은뒤벽좌측,진열섬x1.8/z-2.1. 외곽/출입구/재고실/셸/카메라보존.
- `[변환]` 원본자동PP와면투영리샘플링을구분. 공통127px/m,공유3D꼭짓점·source주석·역homography·동일면RGBA/XYZ. 사각면밖작은발/테두리는가까운면외삽으로보존,접지는셀모서리하한계산. 부착소품은실제수평면높이사용. 작은4종은세로2D층근사이며정확3D복원아님. rear 내부선잔차2.56/3.56px기록.
- `[Play Mode 호출 확인]` StepMove12/12·벽정지·지붕숨김/복원·동일Player/Camera,40native surfaces,source/depth불일치0/frame0/height범위roof0. 실제1114×857 native1배/카메라30°350°. Console11→11추가0/기존이력유지. Tools/Building35/graph.json고정최종조건통과. 기록·화면 docs/artifacts/building35. 빌드/물리키/GPU깊이동등성/저장로드미검증.
- `[사용자 확인]` 실제화면에“지금은훨씬더정상이야각도랑배치같은거자연스러워졌어그런식으로쭉이어가”라고답함. 현재큰가구각도·배치유지. 모든디테일·완전3D·자유회전승인으로확대하지않음. 다음은현재20개를보존한작은상판/벽/직원용품보강.

## 169. B35 승인 배치 보존·부착면 소품6개 `[MAP-01]`

- `[구현]` 사용자 계속요청에 따라 기존20개를 유지하고 벽시계/식물액자/빗자루/장부/작은실내통5새자산과 기존사과트레이1개를 별도Details35그룹에 배치, 총26개다. source5종 생성/자동PP 각각1회, 원본과receipt보존. 벽 실내면−틀/거치대두께와 실제상판Y1.05663645+책두께.02의 고정평면을 사용했다. 새소품만source RGBA그대로단일표본,depth.valid=alpha>.1. 물리재표본화의source중복/누락한계명시.
- `[보존]` ed10f1c대비 기존904블록중903동일/삭제0, 부모children에그룹1개참조추가만변경. 기존20가구·구조·지붕·조명블록불변. 신규41블록=소품6+그룹/NativeSurface/Collider3. prefab-preservation.json에실제fileID/해시기록.
- `[Play Mode 호출 확인]` 영향동선3/3(계산대고객/직원·청소구역), 같은Player/Camera, 벽정지·지붕숨김/복원. surface46,alpha/depth0불일치·frame0·height범위roof0. 1114×857 native1배/30°350°,조망2560×1600은재프레이밍. Console11→11추가0;기존volumetricSpot경고보존. 원래12중비영향9경로재실행안함. details-graph최종기술판정통과.
- `[납품/한계]` docs/artifacts/building35/details실제화면제출/새6개미술확인대기. 수납장뒤빗자루·쓰레기통일부가림은현재깊이관계이며강제표시안함. 빌드·물리키·저장로드·GPU깊이동등성미검증. 기존줌범위/native1배불일치유지. 작업후Edit Mode/기존background false와SceneView실내보기복원.

## 170. B35 바구니 실측 교정과 제작 파이프라인 마감 `[MAP-01]`

- `[사용자 정정]` 계산대 사과 바구니가 작고 각도·픽셀 정규가 어긋난다는 지적 이후, 최종 요청은 “일단 최대한 마무리해 픽셀각도,배치같은것들 다정리해서 파이프라인처럼 기술”이다. 추가 생성·PixelLab 전송 없이 현재 교정과 문서화를 마감했다. 최종 미술 합격으로 해석하지 않는다.
- `[원인/거절 실험]` 기존 flat_prop는 사과 포함 그림 높이.25m로 표시 크기를 정해 별도 footprint와 불일치했다. 이전 그림을40×30×10cm 상자로 재투영한 첫 실험은 과육13~15cm 추정으로 비례 부적합하여 Unity 통합하지 않았다. tray-size-correction의 실제 출력·계산·거절 기록과 미완료 그래프를 보존했다.
- `[구현]` 실제 제품 치수40×30×10cm와 사과 배치용9cm 구를 metric-catalog에 두고, 분리 생성된 빈 상자/사과를 각각 원본 자동PP1회 처리했다. 열린 상자9면과4×3+3×2구 중심18개를127px/m에 합성해68×47픽셀 출력. 상자/내용물 중 같은 최소깊이 표면이RGBA/XYZ를 소유한다. 소품3개의Mesh/Material/Collider만 공통자산과.4×.2×.3m로 변경하고 기존 배치Transform·다른23개 유지. prefab fileID비교에서HEAD기존904중897동일/변경7/삭제0,Details41블록추가를 확인했다.
- `[Play Mode 호출 확인]` 최종 snapshot1회, 실제1114×857와별도조망2560×1600. 같은Player/Camera EntityID,46surface의alpha/depth불일치0·frame0·height범위roof0,공통127/native1배. Console11→11추가0. Collider가줄고위치/통로불변이므로§169의영향3경로를재사용했고, 이번에는이동/벽/외부지붕복원을다시시험하지않았다. graph4단계의고정기술범위완료,EditMode/background false/SceneView복원.
- `[재사용 문서]` Tools/Building35/PIPELINE.md에좌표식·치수권위·자동PP/재표본화구분·부착면·가림·변경원인별재실행구간·실패분기·실행명령과증거경로를정리했다. scene한장재생성이나모든PNG동일크기를제작알고리즘으로대체하지않는다.
- `[한계]` 사과는잎/꼭지포함32px프레임을11.43px로표본화해세부손실이가능하며과육9cm실측완료가아니다. 기존그림의내부선잔차2.56/3.56px·비평면소품고정시점근사·작은viewport줌충돌·기존volumetric경고유지. 미술완성/자유회전/빌드/저장로드/물리키/GPU깊이동등성미검증. PixelLab재작화는자동승인검토가해당파일의외부전송승인을요구하여실행되지않았다. 전송승인질문에사용자가마감을요청했으므로재시도안함.

## 171. 공통 시트 원본 정규화·무변형 import와 재개 인계 `[MAP-01]`

- `[요청/원인]` 전체 시트1회 정규화→정수 crop 사용, 개별 재투영·resize 제거 요청이다. 영상 의도는 같은 사물을 길쭉하게 변형한 문제로 정정됐다. B35 project_faces/details-prepare/tray-composite의 원본 이후 재표본화를 확인했다.
- `[실행]` 기존 Source/sheet.png1122×1402를 공식과 파일해시가 같은 원본 PerfectPixel OpenCV backend로 자동 처리했다. 격자 크기 강제 지정 없음. 원본 refine 결과204×277, 오브젝트18+잔여2의 정수 분리20/20 RGBA 일치. normalize→slice→validate 완료; 해당 연속 처리 약1.29초(설치/Unity/추론 제외). 원본 검출에 따른 약8% 종횡비 차이는 무손실로 보고하지 않는다.
- `[Editor 실행]` NativeSheetImport36으로18종 Sprite import. PNG SHA·RGBA·해상도 동일, Point/NoMips/Uncompressed/FullRect. 기존 계산대294px/새49texel로 공통q6, 모든Sprite PPU127/6. PNG 확대나 개별 변형 없음. unity-import.json은 실제 readback이다.
- `[미완료/정정]` GameMap1/PlannedPixelShop33 프리팹은 미교체. collider-box 후보18종 실패는 해당 proxy의 실패이며 기존 visual depth와 동일하지 않다. 새색/가림 연결 생산자 미구현으로 input_gate 중단. corrected report 이후 importer 갱신으로 마지막 입력 대조는 handoff-gate.json에 분리했다(유일실패 NATIVE_DEPTH_MAPPING_NOT_AUTHORED). 실제 화면/Play/가림/이동/미술 확인은 이번 미실행. RenderGraph/ZBinningJob Console 오류 인과 미확정.
- `[사용자 중단/재개]` 사용량 소진 임박으로 인계 요청을 받아 추가 구현 중단. Tools/Building36/README.md 첫 절에 최신 요구·완료/미적용·실패 한계·미실행 수직 sprite plane 후보·전체 연구 경로·최소 다음 작업을 기록했다. 다음은 정규화 반복이 아니라 색무변형 표시/가림 방식 설계와 대표 장면 실험이다. 후보를 구현된 기능으로 바꾸거나 기존 depth hash 보존을 사용자 요구로 오해하지 않는다.

## 172. 전체 시트 자동 정규화 이후 색·비율 무변형 표시 적용 `[MAP-01]`

- `[요청/원인]` 2026-10-03 재개: 해상도/확대/붙임/늘림 반복을 제거하고 원본PerfectPixel 자동규격으로 처리하라는 요청이다. 기존B35의project_faces/details-prepare/tray-composite 색재표본화를 이번26개연결에서 제거했다. R3 camera-facing은벽잘림/시계지붕초과, R4공통ray-plane은B36입력의상대가구크기로q2과소여서 통합하지 않았다. 실패기록을docs/artifacts/building36/R3,R4에 보존했다.
- `[제작]` 기존placement/collider를32texel/m,30°/local45°로투영한입력가이드로 공통시트1개를 생성했다. 가이드무시한첫입력은격리했다. Source/sheet.png1489×1056 RGBA sha=e4eb81a6bb53708a807e7eb182bfaa10bc39e37a5ed337c7913384323172d1ae. 공식sha와같은 원본PerfectPixel OpenCV(grid=None/center/refine.25/fix_square=False),전처리없이1회,자동301×211 sha=0101a9e42f97778a11b9371af0d0dd3f298581f5bb008f6b6528b62fda1695c7. 정수crop18종+잔여5,63511texel분할중복/누락0,23/23RGBA동일. 원본자동검출도특징무손실은아니다.
- `[표시/원인교정]` NativeSheetDisplay36의P=P0+S−F·dot(n,S)/dot(n,F),S=R*u/ppu−U*v/ppu를사용한다. R5는원점0ray때문에전면Z이동이X중심까지밀던버그여서실제지지P0원점으로고쳤다. 공통q4/PPU31.75,fullUV/Point/NoMips/RGBA32. source PNGresize/warp/개별scale/재픽셀화없음. 18sharedmesh/material을26기존인스턴스에연결했고Prefab변경은Mesh/Material참조52개뿐이다. 원래pose/collider/Player/Camera/방/지붕/조명보존. 평면표시는3D부피복원아니다.
- `[Play Mode 호출 확인]` 대표선반/시계실험후해시gate를소비해통합했다. 최종26/26sourceRGBA불일치0,실제camera1114×857/30°350°의texel기저4×4px,bounds초과0,동일Player/Camera EntityID의실내지붕숨김/외부복원. docs/artifacts/building37/R6/final과live*.json,final-gate.json. Materials/Display WorkLoop는고정기술범위완료. source·native·crop·gameplay캡처·별도overview를구분한다.
- `[최종픽셀관측]` renderer scale1/MSAA1/AA없음/post없음. 실제GPU캡처선반ROI의4px phase(0,1)에서1628칸중1428RGB완전동일,다른phase의칸내색차평균은크게증가했다(capture-blocks.json). 전체화면보간/원본특징보존을이표본으로단정하지않는다. source고주파색과원본centre표본손실은부드러운인상을남길수있다. opaqueTexture2xBilinear설정만보고원인으로확정하거나전역조명을끄지않았다. 최종Console Error최대8조회0건,EditMode복원.
- `[한계/재개]` 생성가이드의정확도·진열섬/계산대원본상대비율·소품방향·미술완성미확정. 복잡한Player앞뒤깊이/자유회전/정확표면법선·광원입체반응미검증. 기존Collider동선증거재사용,키보드이동/빌드/저장로드/GPU성능미실행. 최신결정과원인별실행경로는Tools/Building37/README.md. 기술gate를미술합격으로바꾸거나이를개별PNG늘림으로덮지않는다.

## 173. PerfectPixel 국소 형태 왜곡의 별도 전역 격자 보정 `[MAP-01]`

- `[요청/범위]` 2026-10-03 사용자: 공식 웹 데모에서 볼록/오목 거울처럼 형태가 뒤틀리며 최근 커밋 변경으로 보이지 않는다는 관찰, 수정 요청. 최근 변경을 원인으로 단정하지 않았다. 이번 쓰기는 별도 로컬 계산/브라우저 실행기와 기록이다. 원본 엔진·입력·과거 출력·Unity 씬/프리팹·사용자 dirty 변경 보존.
- `[원인 근거]` Python/웹 구현의 국소 경계 탐색과 다음 경계의 누적은 source 폭을 달리한다. B37 원본 정규화 receipt의 경계 간격은 4/5/6px, 각각 출력 1칸이다. refine 강도 0만으로도 반복 round 누적이 남는다. 이는 실제 확인된 왜곡 가능 연산이며 사용자 미제공 원본의 정확한 왜곡량을 재현했다는 뜻은 아니다. 공식 웹의 1024px 전처리도 별도 후보다. 기존 RGBA 검사로 생성 원본의 형태 보존을 증명했다는 해석을 정정했다.
- `[설계/구현]` Tools/PerfectPixelUniform/README.md에 좌표·자동 간격·전역 DFT 위상·constant Jacobian·nearest 허용오차·끝 경계 정책·실패 조건을 먼저 고정했다. 원본 자동 detect_grid_scale의 선택 개수를 반올림 전에 관찰해 공통 s를 계산, centre=origin+i*s 직접 생성, source[floor(cy),floor(cx)] 정확 RGBA. local refine/recursive round/수동 목표 크기/1024px 축소/8px fallback/색 처리 없음. 원본 get_perfect_pixel 자체를 수정하지 않은 **별도 보정 경로**다. 웹은 127.0.0.1, 이미지 bytes/PNG/receipt 고유 runs 보존, 정수 CSS 미리보기와 저장 해상도 구분.
- `[실제 계산/검증]` 원본 B37 1489×1056 sha=e4eb81a6bb53708a807e7eb182bfaa10bc39e37a5ed337c7913384323172d1ae → Uniform01 314×223, s=4.747232472324724, 약0.346초. 원본/엔진 SHA 불변, exact source RGBA, 등간격 최대오차1.972e-13px, nearest centre 오차0.49929px. WorkLoop 첫 계산 후 단색 검출 반례1건 실패, RGB 경계 없는 입력 거부 추가. 실제 시트 재정규화 없이 recovery에서 fixture/phase/분수좌표/단색실패/실제출처 5건 통과. HTTP6조건도 통과(알려진RGB 입력 처리0.081초); 서버는 시험후종료. 첫 실패/후속 통과와 결과/좌표는 docs/artifacts/building37/Uniform01에 보존. preview-x4는1256×892별도표시다.
- `[한계/재개]` 실제 B37위상신호0.0213/0.00173으로 약해 grid_status=unconfirmed. 등간격 변환은 원본 격자의 정확성/특징·미술 보존을 증명하지 않는다. 생성 원본 자체의 잘못된 비례/곡선이나 source centre 사이/끝의 미세 특징 손실은 남을 수 있다. 이번 실제 개인 브라우저 UI·Unity Play/GPU/입력/빌드 검증은 하지 않았다. 기존 바닥1px/가구4px 밀도차도 수정하지 않았다. 같은 원본을 새 도구에서 선택해 사용하는 경로와 후속 실패 귀속은 도구 README가 담당한다.

## 174. 모자이크 특징 손실을 막는 무손실 반복 격자 정규화 `[MAP-01]`

- `[사용자 확인/요청]` V1 휘어짐은 사라졌지만 해상도/특징 손실이 남았다. 어떤 해상도에서도 인지를 흐리는 모자이크 처리로 대체하지 말고 수정 가능한 부분을 고치라는 요청이다. 사전 계약은 원본/이전 결과/Unity 보존, 검출·샘플링·출력 허용 수정, 실제source/알려진native 마지막 검사였다.
- `[원인/범위]` 원본 FFT 최소4px/gradient 최소거리4, 서로 다른 X5.494/Y4를 평균4.747로 사용했고, 약한 위상이어도 표본 PNG를 저장했다. source 자체의 반복 셀 조건을 보지 않았다. 독립 측정에서 visible RGB154249색/alpha256단계, visible 인접RGB 변화X89.27%/Y86.95%, RGB 변화경계GCD양축1. 보존된 V1 역표시에서 visible 불일치89.56%/alpha0이 된 source10048px였다(이는 의미적 특징 손실률이 아니다). 원본/완료이미지를 재생성하지 않고 읽어서 측정했다.
- `[구현]` Tools/PerfectPixelUniform README V2의 요구-원인-연산/기하/실패 명세를 먼저 작성했다. 전체 RGBA 변화경계 차분의 축별GCD→공통GCD로 가장 큰 정수 무손실 셀 후보를 계산한다. 2/3px 가능, 축 평균/peak 최소4/위상0 fallback 없음. 전역floor cell map·같은좌표source재구성 byte0불일치 gate. 부분 가장자리 셀도 source 교집합으로 보존하고 canvas/offset을 기록한다. 조건실패는PNG미생성/진단, HTTP422/source다운로드/원인JSON표시. V2검출은 원본엔진을 호출하지 않으며 V1함수는진단용으로만보존했다. stale서버 코드/버전도 재사용하지 않는다.
- `[실제 검증]` graph-v2.json WorkLoop3단계완료. 실제 B37 1489×1056 sha=e4eb81a6bb53708a807e7eb182bfaa10bc39e37a5ed337c7913384323172d1ae, 변화경계GCD X/Y1, NO_LOSSLESS_COARSER_LATTICE로0.032초거부, Uniform02/failure.json만저장. 독립fixture 12개 검사 모두통과/skip0: 2·3·4·8배RGBA,1px선/눈,공통배수2,부분끝,alpha-only/flat축,미세노이즈/hiddenRGB/gradient/단색/실제입력/CLI. HTTP7조건통과,실제source거부PNG없음/sourcebytes동일. HTML JS구문·문서/대상diff정적확인은별도마지막검사다. 근사손실/미술합격을 byte검사로대신하지않는다.
- `[한계/재개]` 고친것은 **잘못 검출한 격자로 특징을 버리는 출력 경로**다. 이 실제source를 더작은 native로 재저작했다는 완료는아니다. 비정수확대/보간/혼합격자는보수적경로에서거부될수있고,작가의원격자는관측색만으로식별불가할수있다. 임의축소에서모든특징보존은보장하지않으며확대는정수nearest를쓴다. source가이미native1px인지연속그림인지의미를AI가임의확정하지않는다. Unity/개인브라우저UI/Player입력/빌드검증·새아트생성미실행. 기존4px가구/1px바닥과미술문제는별도미해결.
- `[실제 서버 원인수정]` 最終HTTP관측에서HTML은V2지만8768계산기는V1인잔존을확인했다. 확인된기존실행기를교체하고실제version2/coreSHA=eb16488844435e905c4ee62470c776d2697456ba02c4b0a696ad6c66e0416325/리스너1개를Uniform02/live-server.json으로관측했다. UI는health V2전처리비활성,계산SHA변경은503,새서버는Windows SO_EXCLUSIVEADDRUSE/동일V2SHA만재사용. 변경된HTTP부분7조건만web-tests-final.json으로재검증/통과. 원본시트판정과검출12건은재실행하지않았다. 앱브라우저열기는queued반환이어서사용자화면표시를확인했다고보고하지않는다.

## 175. 원본 해상도 유지·색 번짐 정리 모드 `[MAP-01]`

- `[최신 요구/정정]` V2 actual run이거부되어사용할결과가없으며Aseprite표시는더선명하나주변의여러색/미세명암잡음을수학적으로정리해야한다. exactRGBA축약을색정리필수입구로둔요구해석을수정했다. source/canonical격자복원과색정리를분리하고원본/과거결과/Unity를보존한다.
- `[설계/구현]` README V3에후보·원인·좌표/색공간·불변조건·반례를먼저고정했다. 새cleanup.py는원본W×H/alpha/hiddenRGB를보존한5×5bilateral1회(LabD65거리,σSpace1px,σColor=t)→median-cut후보팔레트→ditheringNONE매핑,source대비최종byteΔE76≤t. 강한4-neighbor경계양끝RGB고정,오차초과는bounded색/원본유지. t2/4/8·후보64/128/256색은색정리설정이고해상도목표가아니다. ≤K색입력noop;높은대비/반투명fringe는남을수있고최종색수≤K나의미보존을주장하지않는다.
- `[실제 제작/검증]` graph-v3 WorkLoop3단계완료. uploaded run20261003T092818576216Z-59a6e7b8655b4cf4a637cf98f68e32a7 source와B37동일SHA. Uniform03/output.png1489×1056그대로,3.630초,alpha/hiddenRGB일치·경계215329pxRGB일치·최대ΔE3.999974≤4. RGB154249→136682색/visible357806px변경. 동일source저대비쌍제곱색차0.938642배는국소변동6.14%감소이며미술/인지점수가아니다. 독립fixture및actual저장결과9검사+HTTP9조건통과. comparison-crop-x4는같은128×128영역의정수4배표시1032×540별도미리보기다.
- `[서버/제출]` 웹기본cleanup과기존lossless/API생략호환분리,UI버전3및uniform+cleanup+web코드SHA검사. 실제8768V2서버PID36976을경로/유휴확인후교체했다(Stop-Process실행오류후동일PIDtaskkill성공);version3/loadedSHA일치와netstat리스너PID40068확인. sourcequery로이전업로드불러오기가능. 원본/이전실행기록/Unity변경없음. 개인브라우저UI자동화/UnityPlay/게임통합/새아트생성은실행하지않았다.
- `[한계/재개]` 보수적인내부색정리후보까지확인했으며실제픽셀격자복원·외곽matte·디자인합격은미완료다. 원본의saturatedred3367/yellow223px모두alpha1~15라matte오염가능성이있지만원인확정이나색상일괄삭제근거는아니다. weakcontrast유효특징은자동식별불가하며강도를높인결과를보존합격으로승격하지않는다. 도구README가현재결정/원리/증거의단일원본이다.

## 176. 과거 선 우선 수정판의 원본 해상도 시험 `[MAP-01]`

최신 요청은 V3의 15만→13만색 변화가 너무 작고, 과거 선을 먼저 검출/복구한 뒤 안쪽 색을 채우는 수정판을 써보자는 것이다. `LocalOnly/PerfectPixelPalette_20260906`에서 실제 `line_first` 경로를 확인했다. `source_regions`만으로는 선 우선이 아니며, 이 수정판도 자동 저작 격자 검출·이상적 선/곡선 복원·없는 선 추론을 하지 않는다. README V4에 입력 적합성·좌표·단계별 원인·실패 귀속을 고정한 뒤 원본 해상도에서 기존 코드를 1회 실행했다.

- 실제 입력은 앞선 user run과 동일한 source SHA e4eb81a6…(1489×1056 RGBA)다. 별도 복사본에 alpha≥128→255/미만→0, 투명 RGB0을 명시했고, 원본·이전 결과·기존 엔진·Unity는 보존했다. alpha 변경578487px, nonzero alpha 중 투명 변경73742px를 `preparation.json`에 기록했다.
- 계산은 원본 크기/scale1.0/region_colors64·3회/line_first/guard true. raw Sato ridge→Zhang skeleton→고정선→4연결 raw Oklab 영역→source-supported priority flood→영역의 실제 palette 표본. 수동 erase/이중 resize/local warp/새 highlight·tones는 적용하지 않았다. 기존 과학 패키지는 sandbox 읽기가 막혀 있었으며 승인된 읽기로 사용, 설치·수정하지 않았다.
- `graph-v4.json`은 준비→고정 엔진 외부 실행 인계→저장 map 검사 3노드다. command.run의 최대60초를 늘리지 않고 엔진만 ai.work로 맡긴 뒤 실제 argv/PID/exit/time/log SHA를 반환했다. 전체 제작을 AI 성공 문장/파일 존재 검사로 바꾸지 않았다. 엔진 exit0·169.632초·stderr0bytes, 제작 재실행 없음.
- 실제 `Uniform04/engine/pixel_native.png`는 1489×1056/RGB64. 팔레트 변경502696opaque px, 선 단계 추가 변경31064px. 후보선228852→source skeleton106138→고정선104358px, 영역9802개, 채움323392px. 고정선 좌표는 identity지만 원색102614px는 팔레트로 변경됐다. 같은 색 영역 가까운 표본46640px를 써서 색 경계/선 두께가 달라진다.
- 미해결77854px(opaque505604px의15.40%)는 pre-line palette색을 유지했다. 충돌0, 지지 없는 영역 제안 거부28600은 엔진 metadata 수치다. map 기반 검사는 원본/엔진SHA, 동일W/H, 준비 alpha mask, 원본 관측RGB≤64, 고정선 좌표/색/영역 표본과 실제PNG, fallback 출처를 확인했다. 별도 읽기 전용 감사도 저장 결과를 독립 확인했다. 연결 영역2440개에는 최종2색 이상(최대26색)이 남으므로 영역별 단색 평탄화라고 설명하지 않는다. `comparison-crop-x4.png`는 같은128×128 crop nearest4배 미리보기이며 자산 재확대가 아니다.

**기존 수정판 적용 시험은 완료했으나 깨끗한 정규 픽셀 복구는 미달**이다. 확대 결과에도 잔색과 불규칙 경계가 남으며, 코드 실행/64색/이진 alpha는 구조선 복원·native 저작 격자·의미 특징/미술 완성 증거가 아니다. 선을 추가 추측하거나 원본을 줄여 완료 처리하지 않았다. 다음 부족 단계는 유효 격자와 구조선 정의/복원으로 귀속한다. 8768의 V3 기본과 Unity 배치는 변경하지 않았고 Play 검사도 하지 않았다.

## 177. 정수 구조·재료 규칙으로 수납장 직접 저작 `[MAP-01]`

- `[최신 요청/범위]` 흐린 나뭇결을 정규화하는 정도로는 pixel 저작이 아니며, 다색 명암·여러 줄 gradient 경계 대신 수학적으로 직접 그려 달라는 요청이다. 기존 청록/나무 상판 수납장 방향의 새 가구1개로 범위를 잡고 README V5에 입력/표현/치수/변환/명암/실패 계약을 먼저 고정했다. 원본 동일 복구나 전체 맵/Unity 제작으로 확대하지 않았다.
- `[직접 저작]` cabinet_recipe.json→기하 binary masks/unique edges→역할색/재료곡선→native PNG→저장결과 검사다. local tick의 공통 affine `u=58+2x-2z,v=174-x-z-y`와 1회 정점 round, pixel-centre half-open polygon, 비AA Bresenham. 실물2×.625×.9186m/투영pitch30° 대응이며 screen ground slope는2:1이다. 문3개 폭/손잡이규격 공통, grain11cubic/옹이2개는UV공간에서 De Casteljau .125px chord tolerance로 분할한다. 원본 RGB/resize/연속광원/색평균/디더링은 사용하지 않았다. 고정 sRGB 역할색의 저작 명암이며 물리 조명 시뮬레이션이 아니다.
- `[실패/원인 수정]` 첫 geometry JSON에서 np.int64 직렬화 실패. Python int 반환/파일 열기 전 JSON 직렬화로 고치고 실패 geometry/부분JSON/코드/blocked graph를 Direct05/failed-json에 보존했다. 재계산된 기하 mask는 실패시 mask와 모두 동일. 그후 첫 grain637px의 저장 감사에서1px 독립섬40개 확인. 원래11곡선은 모두 한 덩어리/19곡선의 실제 구조선 침범0이었지만, 팽창한1px 경계 배제대의 부분 clip으로 곡선2/3/6이 끊어졌다. 부분clip을 제거하고 전체stroke 소유권 실패시중단・단독점0검사를 추가했다. 이전 PNG/재료/검사/성공 graph는 failed-grain에 보존, recipe/기하/색/원본 유지하고 material→validate만 재개했다. 처음 exit0을 목표합격으로 기록하지 않는다.
- `[실제 제작/검사]` Direct05/native.png204×192 RGBA・15색・alpha0/255, unique 구조선31・face overlap0, grain695px・실제 edge 침범0・8연결 이웃없는 단독점0. 마지막 고정조건 validation과 2노드 recovery 완료, 기존 geometry bytes SHA 유지. 기하 .2937초/최종재료 .0604초 합계약.354초는 계산구간이며 프로세스/검사/AI 전체작업시간이 아니다. preview-x4는816×768 exact4×4복제, display-x4는배경/설명붙인848×832 별도표시. 제작자산에 확대본을 되먹이지 않았다.
- `[독립 저장결과 감사]` 별도 agent가 PNG/NPZ/JSON만 읽어 같은 규격/팔레트/alpha/hash/edge 조건을 확인했다. oldgrain637px 유지+58px 추가, grain밖RGB변경0, handlesmask/edgeRGBA동일. 최종grain8연결component10개・1px/2px섬0. 최초 실패 geometry와 현재 geometry NPZ는 파일SHA까지동일. 제작재실행/파일쓰기/미술합격판정없음, independent-audit.json에 관측범위를 기록했다.
- `[완료/미검증]` 이번 수납장1개의 직접native저작과 기술 조건을 확인했다. 미술합격・생성원본동일복제・범용모든가구생성・기존아트격자복구・Unity import/동적조명/표시는 미검증이다. 원본/V1~V4/8768 V3/Unity를 보존했고 게임통합/Play/빌드 검사를 실행하지 않았다. 제작 규칙과 현재 한계의 단일원본은 Tools/PerfectPixelUniform/README.md V5다.

## 178. 생성 재료·실제 깊이·동일 모듈 반복으로 픽셀 수납장 제작 `[MAP-01]`

- `[최신 요청/설계]` 생성형으로 색감·디자인을 만들고 중앙 대표색으로 채우며, 수학적으로 경계/명암을 구분한 실제 결과와 같은 디자인의 크기 확장을 요구했다. DESIGN06에 입력/좌표/기하/명암/UV/반례/완료 범위를 먼저 고정했다. 기존 V5/웹/Unity/원본을 보존하고 새 수납장2/3칸의 native PNG 및 실제3D를 제작했다.
- `[생성 입력]` 내장 imagegen 1회로1254×1254 RGB concept/material board를 생성했다. Source06에 원본SHA/프롬프트/출처를 보존했으며 결과 PNG로 제출하지 않았다. paint/wood/brass 각4역할의 선언한 중앙 한 점 RGB 그대로12색을 선택했다. source의 전체3D조명 RGB를 완성 텍스처로 붙이지 않았다. 목재 flat ROI의 휘도25백분위 미만 역할을128×54 UV지도에 옮겼고 8연결6texel미만101성분/255texel을 제외하여1536유지했다. 명시적 재료 저작이며 원화 특징 전부의 무손실 복원이 아니다.
- `[기하/확장]` local tick→Blender world `(-z/32,x/32,y/(32sqrt6))`, camera azimuth45/elevation30/density64sqrt2로 `u=2x-2z,v=-x-z-y`를 유지했다. 문틀/서랍 프레임과 안쪽 면, 손잡이/브래킷, 측면 패널, 상판/받침을 실제box로 정의했다. `W(n)=4+20n`, `x_i=2+20i`의 고정 끝단+같은bay 반복이며 image/mesh 전체scale를 쓰지 않았다. Blender Array와 같은 배치 원리를 직접 계산했으며 실제Modifier 사용은 아니다. 사선전체9-slice는 면 접합 보존에 부적합하여 제외했고 고정 물리UV를 유지했다.
- `[렌더 연산]` finite BVH의 각 native centre 최근접 surface/normal/depth/part와 실제 shadow ray를 저장한다. normal·light의 .26/.68구간+visibility로3명암역할을 고르고 wood grain과 분리했다. RGB평균/조명곱/AA/연속gradient/디더링 없이 source palette를 선택한다. 기존 PixelPipeline/common의 visible pair edge owner를 재사용하며 숨은 면이나 임의레이어로 경계를 덮지 않는다. 최종PNG 축소/늘림/PerfectPixel 재처리/선 팽창은 없다.
- `[실제 결과]` Parametric06 native2.png152×150/native3.png192×170, 각12색/alpha0·255. 모든 bay의 DoorFrame/Inset·DrawerFrame/Inset·DoorHandle/DrawerHandle 및 SideFrame/Inset >0px, 실제shadow1143/1345px. 두 크기모듈치수/밀도/UV/정수phase 일치. scene.blend에2개의 실제mesh scene+camera를 저장했다. viewport는편집용기본색이며 F12 beauty render가 finalPNG인것은아니다. 현재 재제작 권위입력은 recipe/부품code다.
- `[실제 검사/시간]` graph-v6의 material→geometry→pixels→validate 4노드가1회연속완료했다. 생산 재실행 없음. 별도 작성된 검사기는 실제PNG/배열/원본RGB좌표/팔레트/명암/고정UV/edge/평행2중선/정수4배/모듈과 SHA를 확인했고 각 visible group1점씩 box slab(17/23ray)로 BVH깊이를 대조했다.299조건통과이며 미술합격점수가아니다. 재료 .142초+Blender시작포함9.147초+pixel .303초=약9.59초, native기하 .787초/최종검사 .436초. 생성·설계·코드·AI추론시간은별도다. workloop-state.json과validation.json을보존했다.
- `[완료/미검증]` 이번두크기의생성재료→입체구조→native pixel 제작과기술조건을확인했다. 원화99%복제/유일치수복구/미술승인/범용가구·게임모딩시스템/Unityimport·조명·표시는미검증이다. 기존게임이나8768웹을수정하거나Play/빌드검사를하지않았다. 현재결정/재실행/한계는Tools/PerfectPixelUniform/README.md V6와DESIGN06을따른다.

## 179. 돌출 문틀·함몰 패널을 평판 전면으로 수정 `[MAP-01]`

- `[최신 정정/원인]` V6카툰입체감/외곽돌출과가운데함몰구조를사용자가거부했다. 실제frame/panel차50mm(투영3.58px), handle상대112.5mm, 문간몸체노출125mm/상판51.03mm를읽어원인을기하프로필로고정했다. DESIGN07에평판프로필과기존색/무늬/명암/투영/두크기보존을먼저명세했다.
- `[변경]` Frame/Inset/SideFrame제거, 모든문/서랍판frontz-.4tick, 판폭19.5tick/반복20tick/틈.5tick, door y7..53.5와drawer54.5..69.5. 몸체top70/counter70..72로상판25.52mm, 작은handle전면-1.25tick/판기준26.56mm. 기존BVH/nativecentre/가시선/RGB표본/밴드/UV함수를재사용하고재료를byte동일복사했다. 원화/기존V6code·결과/Unity웹은보존했다.
- `[실패/근본수정]` 새프로필스크립트의sibling import경로가Blender에없어ModuleNotFoundError. Blender프로세스exit0을생산완료로간주하여pixels가부재기하를읽다가차단됐다. 실패code/log/부분자료/blocked graph를Parametric07에보존했고script디렉터리명시import와worker_completed생산metadata를연결했다. 프로필값을바꾸지않고Parametric07-fixed에서새수정그래프3노드를완료했다.
- `[실제 결과/관측]` native152×150/192×170·각12색/동일밀도, Frame/Inset0, 모든판깊이동일, visiblegroups11/15와shadow388/430px. 실제PNG/팔레트/alpha/최근접boxslab/가시edge/평행2중선/정수4배/모듈/V6SHA보존의244조건통과. 읽기전용별도감사도평판/두께/handle/재료hash/밀도를확인했으며미술승인하지않았다. Blender시작포함3.218초/픽셀.257초는생성·설계·코드작업과별도다.
- `[완료 범위]` 기하정정과표시자산을제출가능상태로저장했다. 미술승인/범용모딩/Unity표시미검증. 추가로사용자가지적한2색나뭇결의부족은별도재료변경원인으로연결하며기하를다시바꾸지않는다. 현재구조는README V7/DESIGN07/Parametric07-fixed를따른다.

## 180. 2색 나뭇결을 원화 밝기 기반 4색 재료로 수정 `[MAP-01]`

- `[최신 요청/원인]` 2색나뭇결이명암/입체감부족하여잘그린참고작/3~4색을요구했다. 실제4색palette가있어도binarygrain+band연산으로한면내부2색만나오는것이원인이다. DESIGN08에imonk원문(결흐름/명암연결/무작위색·급전이반례), Rappenem그림/PixelPete영상링크,수정영역과판별을먼저고정했다. 영상자막없이세부기법검증을주장하지않고타인자산을게임재료로복사하지않았다.
- `[연산]` 같은생성목재ROI·128×54source-centre UV·물리period·4원본RGB를유지한다. source sRGB밝기p10/25/75로nested3darkmask→0..3단계. 기존8연결6texel잡음정책을nestedmask/작은bright성분에적용하여밝은결/중간목재/어두운결/짙은골을표현했다. 무작위선·두꺼운하이라이트팽창·새생성/기하조명변경/축소필터는없다. 의미적옹이완전인식이나모든원화명암보존은아니다.
- `[실제 결과/검사]` Parametric08 native152×150/192×170. 상판내부4RGB각2칸1000/2006/686/222px·3칸1332/3012/876/414px. 전체colorcount로역할충족을대체하지않았다. V7geometry/codeSHA·camera·density·canvas·alpha·visibleink·nonwoodRGBA불변을저장출력에서확인했고geometry재계산없음. 정확4배표시/원화견본출처도관측했다.4UVlevel1556/3820/1025/511texel,작은성분합병손실metadata를보존했다.
- `[실행/범위]` graph-v8재료→목재내부채움→최종검사3노드를1회연속완료. material.112초/3노드process포함약1.37초는조사·설계·AI시간과별개다. 미술승인/범용재료인식/Unity표시미검증. 평판구조는V7에보존,재료현재계약은README V8/DESIGN08/recipe08이다. 이전결과/8768웹/Unity를바꾸지않았다.

## 181. 쿼터뷰 제작 행동·로컬 실행 진입점 정리 `[MAP-01]`

- `[요청/범위]` 시각 수정은 나중에 하고 일정 사선과 빠른 제작/적용을 위한 기술 행동·실행 구조를 로컬에 남기라는 요청이다. 기존 생성 원화·V6/V7/V8 코드/recipe/산출물·Unity 씬과 미술 상태는 보존했다.
- `[현재 계약]` Tools/PerfectPixelUniform/WORKFLOW.md를 다음 작업의 단일 진입점으로 연결했다. tick→world→native 투영, camera elevation30°와 화면 사선26.565° 구분, 2:1 축선·같은 깊이/경계 소유권, 고정 끝단+bay 반복·UV/공통 밀도, 원인별 단계 선택·정보 손실·실패 귀속·최종 검사·실제 Unity 적용 경계를 명세했다. 원인 없는 재생성/축소/축별 늘림/이중 픽셀화 없이 기존 결과를 재사용한다.
- `[실행 구조]` pipeline_cli.py는 기존 WorkLoop 그래프의 출력만 새 LocalOnly run에 바인딩한다. reuse/plan/start/run/status/stop/resume과 변경 이유, 입력 SHA, transitive code 해시, 원본 보존·별도 미생성 outputs 폴더를 제공한다. wood는 기존 V7 기하의 V8 목재 생산이고 structure는 V7 기하+V6 재료이며, 새 기하와 V8 재료의 자동 연결은 미구현으로 명시했다. 완료는 WorkLoop graph_complete/state.complete/저장 validation/실제 native SHA를 함께 확인한다. 실패·불확실 실행·완료 입력을 자동 재실행하지 않는다.
- `[실제 확인]` 두 경로 plan/init을 실행했고 생산 steps0·events0·outputs 부재, 입력/코드 SHA·출력 바인딩·마지막 validation 위치 등 30조건을 확인했다. 기존 run ID 거부, idle stop→paused run exit1→resume ready, V7/V8의 서로 다른 native metadata SHA 형식도 확인했다. 기록은 LocalOnly/PerfectPixelUniform/workflow-validation.json과 runs/workflow-*-20261003이다. 독립 읽기 검토에서 진행 중 stop 미지원과 완료 후 PNG SHA 누락을 발견하여 문서/래퍼를 수정했고 해당 수정 확인을 받았다.
- `[미검증/인계]` 이 래퍼로 새 생산 start를 실행하지 않았고 Blender/재료/픽셀 생산·Unity 적용/Play/미술 검사를 하지 않았다. 기존 생산 증거는 §179/180을 재사용한다. WorkLoop가 연속 실행 전체에 lock을 유지하므로 stop/resume은 대기 상태 pause만 지원하며 실행 중 즉시/다음 단계 취소는 미지원이다. 다음 요청의 변경 원인을 WORKFLOW에서 분류하고 담당 단계만 작업한다.

## 182. 추가 모듈 손잡이의 경계 교차 누락 수정 `[MAP-01]`

- `[요청/원인]` 옆칸 추가 시 문손잡이가 잘린다는 관측을 확인했다. V7 geometry에서 문의 가시 픽셀14/9(3칸14/9/9), 서랍16/15(3칸16/15/15)이며 V8는 이를 그대로 받았다. 모듈치수는 동일하나 box 모서리에 정확히 닿는 ray를 float32 BVH가 다른 칸에서 놓쳐 문의 오른쪽5px/서랍끝1px를 panel로 판정했다. 첫 문의 face도 모듈수에 따라1/3으로 달랐다. V6에도 같은 계열 경계 문제가 있었고 이미지 복붙/crop의 원인 증거는 없었다.
- `[설계/수정]` DESIGN09에서 closed entry<=exit·동률face1/2/5·전체 실제box의 최소entry 경쟁을 고정했다. 독립 Fraction bbox 실험으로 모든 문의14px/서랍16px와 같은면목록을 제작 전에 확인했다. handle_raster09의 정수 slab가 이전/정확 최근접 owner가 손잡이인 primary ray의 position/normal/part/face/depth를 함께 복구하고 기존광원/실제box에서 해당shadow를 계산한다. 기타 buffer·실제 mesh/치수·camera/밀도·원화RGB·V8목재map는 보존한다. 기존 pixel shade/visible edge와 같은4단계wood 채움으로 후속을 계산하며 해상도/길이/레이어 보정은 없다.
- `[실제 결과/검사]` pipeline_cli start --route handles로 geometry→pixels→validate3노드를1회완주했다. 2칸/3칸의 모든 문14px·서랍16px, 정수 이동으로mask/face/normal/ink/RGBA일치, 기존픽셀삭제0·추가문5px/서랍1px복구를 저장PNG/배열과독립Fraction최근접ray로 확인했다.73조건통과: alpha/canvas/모든목재RGBA/비손잡이buffer/경계인접1셀밖RGBA·sourcepalette·정확4배·기존원본SHA를포함한다. geometry.114초/pixel.354초/마지막검사.240초,3process포함2.24초이며조사/작성시간과별개다.
- `[보존/현재]` Parametric09는 LocalOnly/runs/handle-boundary09-20261003의36산출파일을byte동일보존한snapshot이며publication/workloop기록을함께남겼다. actualscene.blend/parts는기존V7과byte동일이다. current.json이V9native를가리키고reuse의실제SHA를확인했다. 과거wood/structure경로는결함이있는V7buffer를재현하므로현행제작에사용하지않도록WORKFLOW를정정했다. 새임의기하의범용연결/Unity적용/미술승인은이번에하지않았다.

## 183. 생성 원화의 선·영역·3~4단계 명암 재작성 prototype `[MAP-01]`

- `[요청/원인]` 사용자는 원화 디자인을 보존하며 고색수/불규칙 선을 수학적으로 재작성하고 금속 반사대·기존 그림 명암과 게임 조명의 중복을 연구·구현하라고 요청했다. 직접 확인한 legacy 수정판은 region_tones+line_normalization을 미검증 조합으로 거부했고, 웹V3 cleanup은 ΔE 상한 밖에서 원본색으로 돌아가 색수 상한이 없었다. R10 설계/독립 반례 검토에서 source1px 색수 검사로 원래 logical grid 복원을 주장하는 대리 문제를 배제했다.
- `[연구/연산]` PIA/SLIC·Depixelizing·ETF/FDoG·XDoG·intrinsic 분해의 입력 적합성을 REDRAW_DESIGN에 비교했다. 정확 반복 격자만 lossless로 축약; 나머지는 원본1px에서 CIELAB색도 재질후보12개·후보별 실제 원본RGB3/4단계·narrow dark valley/Zhang–Suen 선마스크로 재작성한다. 양측 재질후보/색도 조건과 중성 반사대 보존을 사용하며 이는 의미 분류 증명이 아니다. 색 fallback/디더링/RGBA resize/축별늘림/카메라변경은 없다. 원본바이트·숨은RGB 보존, alpha128 변화 별도 기록이다.
- `[실제 결과]` redraw_cli WorkLoop prepare→render→validate 1회 완료. 실제 시트1489×1056 유지, visible154,249→48색. 분석.104초/재작성2.393초(색.861초/선1.499초 포함)는 저장/최종검사/프로세스 시작과 별개다. 21기술조건 통과. 후보48,892px 중15,560px 처리·33,332px 보존, 최종선11,082px·halo영역재배정4,478px·미해결0. alpha578,487px변경/nonzero73,742px제거; alpha128기준연결성19개 유지. 원화의 빨강/파랑 가장자리와 불규칙 logical grid는 그대로 남을 수 있으며 미술 합격을 주장하지 않는다.
- `[검증/실행]` 곡면금속/2px손잡이, 어두운 중성금속 반사대, 기존native불변, 반복3px+partial edge, 3단계RGB, invalid5단계거부를 확인했다. HTTP V4의 금속fixture1회.224초 및 PNG/지도/검사 다운로드도 확인. 기존V3 idle서버 식별 후 해당PID만 종료하고 V4로 교체했다. 기존lossless/cleanup API보존. 실제 입력/native/maps/명암band 실험/비교2배/검사/workloop/web 증거는 Redraw10에 보존한다.
- `[미완료/인계]` 임의 연속원화의 원래 logical grid 자동복구, vector contour의 정규 사선 재래스터화, 유색금속의 완전한 선/반사대 의미판별, baked조명 제거·물리적 방향성 재조명·Unity표시·미술승인은 미완료다. I=R⊙S의 비유일성 때문에 singleRGB에서 albedo/normal을 완벽복구했다고 하지 않으며 band시프트는 스타일표현 실험이다. 알려진기하의 분리passes/명시grid자료를 새입력으로 받아야 해당단계를 재개한다. V9current/Unity/C#은 보존했다.

## 184. 옛 수정판의 범위별 3/4단계 명암 양자화 재사용 비교 `[MAP-01]`

- `[요청/출처]` 사용자가 양자화 결과를 지적하며 옛 수정판 실행을 요청했다. LocalOnly/PerfectPixelPalette_20260906의 review04~06 color_ranges 경로를 직접 확인했다. 후기 continuous/spatial_steps는 가변K이고 legacy_regions는 최대3톤/자원한도, 선first+region_tones는 미검증 조합 차단 상태여서 이를 완성된 선+톤 통합으로 바꾸지 않았다.
- `[실제 실행]` L11 계약에 따라 실제1489×1056 전체 시트에 기존 build_color_ranges API만 재사용했다. 기본15도 색상환 범위/중성색 분리→범위별L 최대3/4단계→실제 원본RGB lookup이며 좌표변환은 항등이다. alpha>0 전체 색을 처리하고 모든 알파·숨은RGB를 보존했다. 예전 전체 래퍼의 alpha128·격자vote·cleanup·선처리는 실행하지 않았다. 원본/옛엔진/V4/Unity 상태는 보존했다.
- `[증거]` WorkLoop prepare→quantize→validate 1회 완료, 각case1회. visible154,249→74/98색, 색계산+lookup1.371/1.453초(저장/검사/프로세스 제외). 20조건: native크기·알파·숨은RGB·palette lookup·동일범위 원본RGB provenance·범위별톤상한·원본/엔진/출력SHA 통과. Legacy11에 PNG·2배같은ROI비교·영역/톤지도·receipt·검사·실행/옛코드 snapshot·graph/state를 보존했다.
- `[판정/미완료]` 명암 단계화 가설은 지지했으나 약한 나뭇결은 단색에 합쳐지고 경계 잔색은 남았다. Hue범위는 의미적 재질/연결면/구조선 구분이 아니다. 실제 선 기하 재작도·logical격자복구·이미지 조명분리·미술·Unity통합은 계속 미완료다. 웹 엔진 변경이나 추가 시각 보정은 하지 않았다.

## 185. 원화 캐비닛의 선·면·무늬·장식 재작도와 반복 실행 `[MAP-01]`

- `[요청/계약]` 사용자가 큰 범위에서 구조선을 감지하고 해상도를 선택한 뒤 한 줄로 재작도하며 명암·무늬·작은 특징을 함께 남기는 실제 사물 제작을 요청했다. REDRAW13.md에 R12 C/E 선택, sourceSHA/ROI·좌표/반올림·공통 기하·역할·오류/완료 범위를 실행 전에 고정했다. 기존 생성 시트의 첫 닫힌 목재/남색/금속 캐비닛만 입력 조건이다. 임의64슬롯 축소나 원래 격자 검출 성공으로 바꾸지 않았다.
- `[구현]` 기존 OpenCV5.0.0의 contour/Hough/Welschfit와 공통 방향→격자/정수stroke, NumPy의 Huber명암기저/방향잔차→역할별4톤/관측RGBmedoid를 연결했다. compact metal core는 긴 선 투표 전에 분리하고 foreground로 보존했다. sourcepaint의 구조선corridor11,231px를 sampling 후보에서 제외해 흐린 기존선+새선 중첩을 제거했다. 큰 금속띠의 끝 장식은 원본영역에서 보존한다. web/V9/Unity/C#/카메라는 보존했다.
- `[실제 산출]` docs/artifacts/building37/Redraw13e에162×141native,4/8배nearest표시,원본ROI비교,기하·tone/detail/role배열,receipt·19검사·실행코드·WorkLoop상태를 저장했다. 같은ROI의visible22,489RGB→17RGB,alpha0/255. source2pxpitch는 작은특징3셀/12셀·주금속폭3셀 예산에서 선택했으며 originalgridrecovered=false다. 작은지지cluster3개는47/26/23셀·각4색,원본centroid변화0.69/0.95/1.11sourcepx. 각pixel의선owner는최종role과일치한다.
- `[검증]` 고정geometry→detail→raster→validate4노드가2.909초(프로세스/최종검사포함),생성AI/API0회로완료했다. 실제ink/trim전체1,051/719셀의공통선까지최대오차0.945/0.733nativepx,관측palette/halo제외·pixel규격·작은특징의source관계·실제metal2명암·정수확대등19조건통과. 동일결과재호출은cached=true로재계산없음. 별도복사본PNG1byte손상은재생성하지않고거부,원본SHA불변이다. 최종정수4배PNG를실제관찰/제시했다. Unity Play검사는범위밖이어서실행하지않았다.
- `[수정 근거/한계]` 독립검토의최종inkmask소유권/sourcehalo재유입/특징검사공백을수정했다. 이전R13/R13b와R13c의blocked연결검사·code를보존했다. c는이미접촉한source지지영역을독립손잡이로오인했으므로source관계를먼저비교하는계약으로바꿨으며새간격을억지로그리지않았다. d→e는실제선전체오차검사보강이며PNG는동일하다. 실행경로는Run-Redraw13.cmd;미술적AI티0%/reference게임동등성·모든물체의의미/원래격자·albedo/Unity조명·모든교점의전역1px은미검증이다. 그래프완료를이전체목표의완료로승격하지않는다.

## 186. 원본에 없는 외곽 면·중복 내부선 생성 원인 수정 `[MAP-01]`

- `[사용자 정정/원인]` 상판 돌출부에서 아래 모서리로 없는 선이 연결되고 내부/외곽선이 뭉개졌다는 관측이다. R13e의 convexHull 외곽이 오목한 목 부분을 면으로 채웠고 nearest_role가 그 면에 인접 재질을 채웠다. alpha>160 원본 지지 밖236native셀·최대거리9sourcepx였다(전부 alpha0 원본 영역이라는 뜻은 아님). 같은 기둥의 두 Hough band106셀 중첩, 금색/어두운 선의 출력1~2셀 간격 중복도 독립 읽기 검토로 확인했다. supporting-line 교점도 위험하지만 이번 직접 외곽 원인은 hull이었다. 개별 width1 재그림 검사는 최종 합집합 문제를 놓쳤다.
- `[계약/수정]` REDRAW13의 현재 결정을 먼저 정정했다. 실제 body의 순서 contour ε1sourcepx만 외곽 권위이며 wood plane 교점이 silhouette을 확장하지 않는다. source 재질/암부mask의 Zhang–Suen→실제 연결graph의 유한chain→RDP ε1.25→같은 pitch2 LINE_8로 재작도하고 source에서 없는 끝점 연결/새 닫힌 공간 추론을 하지 않는다. 최소 길이는 component에 적용해 긴 frame의 짧은 모서리를 보존한다. broad metal은 실제 source coverage, 독립 caprim은 제거, 금속 주변2sourcepx halo를 face sampling에서 제외했다. 금속 경계 인접 dark 중복을 제거하고 최종 역할/선 mask를 하나의 소유권으로 기록한다. 기존 source/출력/목재 알고리즘/웹/Unity/카메라는 보존했다.
- `[실제 산출/검사]` Redraw13f의 native162×141/pitch2/17색/alpha0·255와4·8배 표시, 원본 비교/유한선 overlay/배열/코드/WorkLoop를 보존했다. geometry→detail→raster→validate4노드는3.537초(프로세스·최종검사 포함),외부생성0회. 최종27조건 통과: source 밖 외곽 최대거리1sourcepx·경계8셀, 실제 최종선 source거리최대2px(상한ε+h/√2=2.664), 암부256셀/금속선840셀/외곽각mask2×2전면채움0, 외곽1연결contour, source broadmetal454셀 밖 확장0, 인접독립dark 중복0, 손잡이47/26/23셀각4색/목재4톤·원화잔차4,157셀·sourceSHA·정수표시를 확인했다. 상판돌출목/떨어진2선/굵은1선 반례도 각각1회 확인했다. 마지막 PNG/원본 비교를 실제 관찰했다.
- `[한계/재개]` 독립 검토는 저장된 source지원·2×2·owner 불일치를 확인했으며 제출을 막는 오류를 찾지 못했다. 모든 source/output junction·cycle·간격의 일대일 대응이나 역할분류의 의미100%,미술적AI티0%,다른사물/Unity조명은 입증되지 않았다. 현재 재실행은 Run-Redraw13.cmd 또는 redraw13_cli.py, 최종기준은 Redraw13f다. 같은해시 결과는 캐시로 반환하며 구버전e와 실험기록은 보존한다. 형식적인 만족도 질문으로 종료하지 않는다.

## 187. 편집 가능한 캐비닛의 직접 픽셀 제작과 가시선 소유권 `[MAP-01]`

- `[요청/범위]` 디자인·명암·무늬·세부를 갖춘 픽셀 오브젝트 한 개와 반복 제작 경로, 구조선은 정확히한줄검정·그외검정0이라는 요청이다. 원화정규화를 시도한R13f는 halo삭제로front 표본60.39%를버리고L*폭18.09→2.70으로줄인 색/명암 실패를 독립 분석했다. 원화/이전산출/Unity를보존하고 새 캐비닛 한개의제작에집중했다.
- `[선택/입력]` PixelLab MCP 실제조회는구독만료·가용generation0·credits0이라job미제출이다. GPTimagegen1회로1315×1196 표현참고를생성(관측tool36.9초)하고NATIVE14계약을먼저남겼다. 원화의low3door/navy/wood/brass디자인을재료로쓰고모듈치수/가시면전개도는recipe가소유한다. Blender/PBR후처리나PerfectPixel 자동격자복원이라고표시하지않는다. 생성원본한장을최종으로제출하지않으며부품·치수·UV·색anchor가편집가능하다.
- `[제작/원인수정]` canonical정수tick→u=2x−2z,v=−x−z−y의30°camera2:1화면축→면ID/UV→실제관측RGB medoid→별도가시선E→nativePNG다. 목재4/앞면3/옆면3/금속3색,black은fill에서제외한다. 상판접촉암부·평면문짝rail·힌지·손잡이·금속인레이를부품별로정의하고나뭇결은실제참고UV를조회한다. 돌출틀/전역이미지축소/비등방늘림/새PBR조명/원본암부halo제거없다. 경계tie오류는면perimeter와선Bresenham의같은raster규칙으로수정했고, sourcequad가금속띠를잘못가져온것은실제원본좌표진단으로처음오류난UV영역을수정했다. 원본이없는선끝연결은없다.
- `[가림결함/최종]` firstfinal의B==E는잘못된E도통과했다. 독립검토가cap내부에보이면안되는body선4px를발견했다. body/cap/handle surfaceowner→edgevisibility→E로기하에서수정했고최종PNG마스크로지우지않았다. body후보9점중4px만잘못된최종검정이며나머지는합법적인cap선과중첩했다. final-v2에서없는선4px만제거·새검정0·part/UV불변·surface/E충돌0을독립읽기로확인했다. delivery는동일가림을SVG부품지도에도적용한마지막package다. base01~04/firstfinal과그코드/blocked기록은보존했다.
- `[실제검증/결과]` NativeObject14/delivery에3문183×165·14색·alpha0/255,2문143×145·14색,transparentnative와회색배경4배표시·module비교·부품SVG/JSON·배열·원본/코드/WorkLoop/해시를보존하고실제미리보기를제시했다. 4노드생산+마지막34조건3.309초,3문black1088=독립E(추가0/누락0),가려진선0,ownedstroke2×2전면채움0,canonical중복0,목재4톤존재,명암분리,모듈숫자ID를제외한문/손잡이/힌지기하·재료·UV동일,실제검정입력/중복edge거절fixture를확인했다. Run-Native14.cmd의실제cmd실행도exit0/graph_complete·3.286초·delivery PNG와SHA동일이다. 고정recipe를AI재판단없이새LocalOnly폴더로출력하며Windows더블클릭검증이라고표기하지않는다.
- `[한계/인계]` template와source영역은이번캐비닛에명시저작했다. 모든임의오브젝트의완전자동복원/미술합격·AI티0%/자유회전숨은면/동적조명/Unityimport·Play를입증하지않았다. 모딩증거는2/3문variant에한정하며재생성속도는생성참고요청/AI설계작성시간과다르다. 다음입력은동일template의명시변경또는새오브젝트저작계약이며관련없는기능을재검증하지않는다.

## 188. 하단 coverage·재질 경계와 실제 입체 명암의 대안 제작 `[MAP-01]`

- `[사용자 정정/직접 원인]` 하단 모서리 1px 돌출, 내부선 전부 검정, 잘못된 명암, 상판 바로 아래 추가선을 고치고 다른 방식을 요청했다. N14는 방향 의존 Bresenham의 반올림으로 같은 바닥선 A→B/B→A 점 집합이128점 달랐고 면+perimeter 합집합이 연속 면 밖alpha110px를 만들었다. 선 역할이 없었고 coplanar rail의 tone을 임의 지정했으며 cap검정선·upper금속띠·밝은toprail을 중첩했다. 과거34검사는 이 조건을 놓쳤다. N14의 전 구조선 검정 계약은 최신 요구로 대체하고 이전 코드·출력·생성 참고·Unity는 보존했다.
- `[설계/선택]` 구현 전에 NATIVE15.md에 canonical tick→world→2:1screen·pixelcenter·half-opencoverage·slab·normal·palette·edgeowner·반례를 고정했다. A는 해석적 평면 전개도, B는 몸체·상판·손잡이의 유한 입체 nearest hit이다. 문은 같은 앞면의 평면 재질 분할이며 돌출 틀·전체 문 후퇴는 없다. PBRT slab/diffuse와 기존 surface_boundaries를 사용하고 모든 경계를 검정으로 찍는 경로는 재사용하지 않았다.
- `[구현/실제 산출]` native15_geometry/native15/native15_validation/native15_cli와 recipe·Run-Native15.cmd로 geometry→material→shade→raster→validate를 기존 WorkLoop에 연결했다. sourceRGB medoid·목재4색 주기를 재사용하고 worldL=(.50,-.20,.84)의 normal내적을3band로 선택한다. B만 실제 shadow ray를 계산한다. geometricband/shadow/material/edge roles는 독립 배열이며 장식은 조명 전에 선택한다. 실루엣·문사이 틈은 검정, 나머지 모서리는 실제 재질 계열색이다. cap/body 접촉의 임의 추가선·upper금속띠·밝은rail은 없다. NativeObject15/compare01에 A/B의 native·4배표시·OBJ/치수JSON·NPZ·진단·원본·코드·WorkLoop·해시를 저장했다. 2문143×145,3문183×165이며 A9색/B11색,alpha0/255다. 원본 축소·PerfectPixel 재적용·이중 픽셀화·새 AI생성/API 호출은0회다.
- `[실제 검증]` CLI 실행은 graph_complete/3.220초, 마지막166조건 통과다. A/B각2·3문의 모서리231/279표본을 독립 Fraction slab/plane로 비교해 owner·위치·깊이 불일치0,최종alpha와기하mask불일치0,정의밖검정0이다. B3문의실제그늘607px·금속그늘88px는해당재질최암색,black606px는silhouette/문틈과동일,재질모서리338px는동계열색이다. 두variant의손잡이기하동일·목재4색·geometricband와그림자분리도확인했다. A/B PNG를실제관찰·제시했다. Cmd진입점은정적확인이고Windows더블클릭을실행했다고표시하지않는다. Unity변경/Play검사는범위밖이다.
- `[한계/인계]` 고정시점캐비닛template의구조/명암/가시경계개선이며모든생성이미지의자동3D복원·순수albedo복원·미술승인·AI티0%·Unity동적조명통합을입증하지않았다. 현재사용자요구의원인수정과실제대안제작을완료한것이며전체아트파이프라인완성으로승격하지않는다. 다음작업은명시원인에해당하는입력/단계만수정하고동일해시결과는그대로사용한다.

## 189. 단일 기지 건물의 native 표면·실시간 조명 적용 `[MAP-01]` `[PIXEL-01]`

- `[요구/설계]` N15 개선 방향을 파이프라인으로 정리해 기지의 테스트 건물 한 채 전체에 적용한다는 요청이다. BUILDING16.md에서 구현 전 canonical Unity metres·PP31.75·30°/350° 시점·최근접 finite hit·재료/무늬/명암/경계 분리·기존 조명 권위·실제 shadow mesh를 고정했다. 원화RGB 완성명암 덧곱/PBR beauty 후처리/강제 이미지 축소를 제외했다.
- `[구현]` Building38의 geometry16/building16/run16/unity_gate16로18종 실제 치수/부품·17구조 캐시를 제작했고 기존 WorkLoop8노드에 연결했다. NativePaletteSurface16은 캐시 position/normal→현재VP 깊이·URP main/additional/SH/shadow/cookie·기존 local data→작은 재질 palette→같은계열 crease를 계산한다. stencil2로 local fullscreen 중복을 막았다. 기존 light feature는 Scene View 데이터 업로드만 추가했고 새 Manager는 없다. Importer는43개 원래 renderer와 collider/배치/지붕·절개 owner를 유지하며 sharedcache35종과ShadowsOnly43개를 연결했다. Floor·벽등2개는 기존 경로 보존이다.
- `[원인/수선]` run01/02는 WorkLoop schema 연결 오류로 생산 전 중단했다. run03 구조 cache는 floor-normalize 후 position만 이동해 원점이 어긋났으므로 build_box의 실제 caller bounds에서 ray/mesh/position/origin을 함께 계산하도록 수정했다. 사과 갈색은 전체시트의 wood RGB를 잘못 포함한 role palette가 원인이어서 raw sheet appleROI로 제한했다. 최종 Play 관측25개는 wall_clock을 구조로 제외한 집계 원인이었고 검증 집계만 수정했다. 이전 실패/결과는 보존했다.
- `[실제 검증]` run04 geometry/material/native35종의 bounds·unitnormal·pixelcenter 왕복·mask/재료domain 검사 통과, 생산resize0. 실제UnityRGBA byte mismatch0, C#/shadercompile 및 GPU render 성공. 같은 최소 renderer/maps에서 주광 방향 변경41,424px, closedcaster on/off그림자2,354px 변화. 실제Play에서26개/18종·같은Player/Camera·pitch30.000004°/yaw349.999969°·source4px·roofhidden1/wallfaded9·local off/on39,714px·shadererror0이다. WorkLoop8노드graph_complete; actualPNG/readback은docs/artifacts/building38/run04에 있다. overview는같은카메라의 일시적정수2px이며원래줌즉시복원, Play종료/SceneView30°·350°/sceneDirtyfalse도확인했다. Console의 남은6개는11:05읽기probe에서 float property를 GetVector로조회한오류이며원본상태/Console을지우지않았다.
- `[보존/저장]` Scene semantic감사: 원래535블록 중건물PrefabInstance1개만수정,534본문불변/원래삭제0, 기존override11개·sourceGUID보존. 추가215블록은43shadow자식과부모참조뿐, mesh43=사물26+구조17정확일치, Ysupport7+anchor2/XZ이동0이다. 기지씬은저장했다. 원본PlannedPixelShop33.prefab 전체전파는자동승인검토가다른인스턴스영향가능성을이유로거부했으며안전한대안인테스트씬인스턴스override로한정했다.
- `[미검증/인계]` 미술완벽·원화99%복사·purealbedo복원·임의시점·Standalone build·전체게임기능을완료로표시하지않는다. 숨은면/상품은semantictemplate저작, curvedshadow는16분할/8ring근사, fridge유리overlay미구현, Floor/벽등은기존표시다. 현재자산은재사용하고 명시변경원인의geometry/material/light/binding만갱신한다. 다른source로공유자산덮어쓰기·원본prefab전체전파는별도변경계약없이는하지않는다.

## 190. 공통 픽셀 규격·기본 밤·움직이는 단계 조명 `[MAP-01]` `[PIXEL-01]`

- `[요구/원인]` 제작이미지와Unity의차이를수정하고바닥/사물픽셀격자를통일하며기본밤과좌우로움직이는반딧불이형조명을요청했다. N16은N15의90.5097PPU·부품profile을31.75로바꾸고CPUpreview와GPU색계산도달랐다. N17은같은미터bbox에서N15의몸체/상판/문/손잡이/인레이를재사용하고공통90.5097PPU와sRGB관측색→linear광계산규약을고정했다. 이전PNG를축소/확대하여생산하지않았다.
- `[직접 원인수선]` 첫181PPU바닥은비활성Interior34였고실제Play의바닥은Aligned127PPU였다. run02의잘못된Floor연결은실제floor/source간격.7126745/1로실패했다. floor-fix01은활성Floor1종만새로계산하고나머지35cache를재사용했다. 기존AlignedPNG의수평639,568표본을독립worldUV로재구성해RGB100%일치시킨127UV/원본sourceSHA를보존했다. 바닥의칸은127/90.5097=1.403배커지고판재world크기/10×8m범위/Y=.015m/실물collider는그대로다. 비활성Floor의잘못된새연결/이번caster를되돌렸다.
- `[표현/조명]` 바닥의낮은lightband에서pattern+band−2클램프가무늬를같은색으로합치는원인이었다. 바닥만intrinsicpattern열을유지하고(band+1)/3의3단계linear광량을적용해밤에도무늬를남겼다. 사물35종의공통shade는그대로다. runtime은position/normal→기존URP/SH/SteppedLocalLight이며완성그림명암RGB덧곱/전역pixelization/새Manager없다. 기존clockinitialHour21,autoAdvance/60seconds/day보존,localx=3sin(2πt/8),y1.35,z0빛한개와5pxmarker를추가했다. 개발조명의임의45°를제거하고기존clock21시실제출력의방향/광량/ambient를Edit에적용했다.
- `[실제 관측]` 18종26사물+17구조+Floor44표면,공유자료36종,수납장211×187/손잡이56·51·57px다. 중립GPU/CPU수납장·진열장·최종Floor의coverage불일치0/RGB최대오차0이다. 실제Play카메라30.000004°/349.999969°,사물1/바닥.99999994/개발SceneView.99999994화면px,같은Player/Camera,inside3/roofhidden1/wallfade9,shadererror0을확인했다. 실제Update17PNG에서lightx−2.99810958~2.98794675m·비교217,993px변화·나뭇결/단계색반응을관찰했다. 촬영용시각고정/background실행은복원하고Play를종료했다. 최종EditSceneView30°/350°·1px·sceneDirtyfalse를직접읽었다.
- `[그래프/실패보존]` run01은timeoutschema실패,run02는실제활성Floor검사실패,첫연속촬영은backgroundfalse에의한정지로보존했다. floor-fix01최종gate는float32 .99999994를정확하한>=1로거절한validator결함으로blocked였다. 원시receipt를반올림해고치지않고기존.001px오차를하한/정수거리양쪽에적용했다. gate-fix01은validator단한파일의before/afterhash를명시하고나머지모든frozen자료/관측불변을확인해1노드graph_complete다. .7126745/.5px는여전히실패한다. 그래프완료는미술합격이아니다.
- `[저장/인계]` GameMap1의기존사물/벽/바닥Transform·collider배치를유지한instanceoverride로저장했고원본건물prefab전체전파없다. 공유사물/구조는NativeBuilding39,활성Floor만NativeBuilding39Floor40,현재절차/실패귀속은BUILDING16.md의N17한곳에갱신했다. 원본시트·N15·N16·실패산출·PNG17프레임보존,GIF256색표시만별도며Unity자료재변환0이다. C#/shadercompile·실제GPU/Play관측은했으나Standalone빌드·전체게임기능·미술완벽·purealbedo·임의시점·유리overlay는미검증이다. 움직이는Stepped빛은가구차폐그림자기능이없고기존주광caster는보존했다.

## 191. 재료 세부를 유지하는 밤 명암 `[MAP-01]` `[PIXEL-01]`

- `[요청/원인]` 밤에 전체가 푸르게 덮이고 세부가 사라지는 문제를 수정했다. N17은 wood rank0/1/2를 band0의 한 색으로 합쳤고, RGB tint의 파랑을 최대2배 증폭했다. 원인은 색/명암 단계이며 geometry/cache/PPU를 다시 제작하지 않았다. 술병은 독립 Unity object가 아닌 선반 semantic 부품으로, 원화 병 그림을 그대로 복사한 경로가 아니다.
- `[구현]` 36개 현재 공유 재료의 ReadableNight만 opt-in했다. intrinsic wood rank를 유지하고 세 단계 읽기 밝기, 휘도가 같은 푸른 그림자 색조 이동, gamut 제한을 적용했다. 밝은 band의 푸른 색조는0이다. 강한 경계/crease·위치/법선/깊이·기존 sky owner/광원·배치·카메라·원본 이미지는 유지했다. 기존 N17 중립fixture는 새 분기와 분리했다. 1차 제한 곱셈의 따뜻한 결과도 원인과 함께 보존했다.
- `[실제GPU/Play]` 최종 readable-night18-hue/validation.json은 cache189파일 hash 불변·재생성0, stock_shelf GPU/CPU coverage 차이0·RGB최대오차1/255다. 실제21시 같은Player/Camera·maps/mesh/Transform, 36재료,30.000004°/349.999969°·1px·shadererror0을 읽었다. 구형/신형548,666px, 빛off/on62,158px 변화다. 최종 PNG는 readable-off/on.png이며 두 WorkLoop의 좁은 계산/관측판정은 complete다. 기술 성공을 미술 합격으로 선언하지 않는다.
- `[보존/한계/인계]` 촬영 시 clock/빛toggle을 복원하고 Play를 종료했다. 병은약10~11×22~28px의1:1표시로 유지했고 이미지 resize/원화 재생성0이다. 캐릭터의 별도adaptive PBR·사용자 dirty 재료는 변경하지 않아 Player 암부는 미해결이다. 개별병 상호작용·원화 디자인 복원·전체 미술 완벽·Standalone빌드는 미검증이다. 현재 수학식/단계 재개는 Tools/PerfectPixelUniform/BUILDING16.md N18, 색만 실행하는 진입점은 Tools/Building38/night18.py이며 전체 제작 재실행이 아니다.

## 192. 기존 수납장 금장 복구와 원본·게임 비교 `[MAP-01]` `[PIXEL-01]`

- `[원인/수선]` 실제 catalog의 `metadata.metadata.cabinet_design`을 한 단계 얕게 읽어 기존 N15 금장/woodUV 분기를 건너뛰었다. 접근 함수를 교정하고 네 재질의 MaterialMap 참조만 새 버전 PNG로 연결했다. counter/island 몸체 금장 1,810/414px를 복구했으며 geometry/edge/coverage/palette와 배치·collider·카메라는 보존했다. N18은 밀도를 바꾸지 않았고 N17의 90.5097PPU/1px가 현재다.
- `[실제 관측]` 21시 같은 Player/Camera·maps/mesh/Transform, 30°/350°·36재료·1px·shader error 0이다. 기존 cache 189파일은 불변이며 fine/coarse CPU/GPU coverage 차이 0·RGB 최대 오차 1/255다. 고정 카메라의 낮은 PPU 표본은 같은 물리 메시에서 직접 제작한 비교용으로, 전체 건물에 적용하지 않았다. 최초 임시 float raw row 누락으로 잘린 비교는 보존하고 기존 production importer의 상하 행 변환으로 후속 비교만 수선했다.
- `[요청 비교샷]` `gold-density19/source-scene-comparison/matched-frame.png`는 실제 Play 카메라 1114×857, 원본은 fine/empty_counter/preview.png 211×187이다. 같은 호출에서 checkout 표시 사각형 212×188을 측정했고, 8px 여백 포함 228×204 crop과 원본·고정 밤광을 나란히 저장했다. rectangle의 ceil/floor 여백은 화면 측정이며 source를 늘린 것이 아니다. `source-night-game-native.png`는 crop/정수 paste만 사용하고 resize/resampling 0이다. 원본 preview와 실제 밤의 색 차이, 금장의 옅은 밤색조는 관측 사실이며 RGB 동일성/미술 완벽을 주장하지 않는다.
- `[인계]` 현재 단계 재개와 한계는 BUILDING16.md N19, 실행은 repair19.py/compare19.py다. 원본/실패 비교/첫 paused graph와 수정 비교 complete graph를 모두 보존했다. 밀도 변경·금장 밤색감·캐릭터 PBR·원화 100% 복원·Standalone빌드는 미완료다.

## 193. 기존 native 이미지의 정수 2배 카메라 줌 `[MAP-01]` `[PIXEL-01]`

- `[요청/구현]` 사용자 첨부 N15 4배 미리보기와 현재 화면의 크기 차이에 대해 카메라를 더 줌하도록 요청했다. CameraZoomController의 기존 API에 선택적인 초기 정수 배율을 연결하고 GameMap1의 테스트 NativePixelBuilding만 2배로 설정했다. 기존 크기 기반 기본값 0과 일반 줌/입력 차단·같은 카메라의 비native size 복원은 보존했다. Preview Camera는 현재 씬 override만 변경했고 가구·이미지·재료·PPU·각도는 그대로다.
- `[실제 GPU/Play 호출]` zoom20/readable-on.png는 실제 1114×857 게임 카메라 size 2.367151·30°/350°·2px, 같은 Player/Camera·maps/mesh/Transform·36재료·shader error 0이다. 기존 art 189파일 hash 불변을 확인했다. 임시 viewport 높이 720/857/1080의 선택 배율 2·기존 scroll 계산 2→1→2·같은 카메라의 size 5 복원을 호출로 확인했다. 실제 물리 휠 입력·전체 씬 전환·Standalone빌드는 이번에 실행하지 않았다. WorkLoop 설정/관측→최종 gate 완료이며 미술 개선이나 색감 수정은 주장하지 않는다.

## 194. 기존 이동 광원의 넓은 백색 그라데이션 `[MAP-01]` `[PIXEL-01]`

- `[요청/원인/구현]` '반딧불이처럼'을 연두색으로 해석한 광원색과 좁은 단계형 경계를 사용자가 정정했다. 기존 광원의 color를white, radius를3.8→7.6m로 바꾸고 그 광원만 continuousFalloff=true로 저장했다. Common의 surfaceBands와 ReadableNight의 후속 밝기 단계에서 같은 기여가 두 번 계단화되는 원인을 분리했다. 같은 loop에서 기존/연속 기여를 따로 합산해 작은 밤광의 half 차감 손실을 피하며, 연속 기여만 기존 Point albedo를 향해 1-exp2(-energy)로 밝힌다. 강한 검정 경계·기존 밤 함수·다른 광원·motion·2배카메라·geometry/art는 보존했다.
- `[실제 GPU/Play/최종 판정]` light21/settings.json은 같은 light/motion·다른 활성광원,white/radius7.6/intensity4.2/halo0,sceneSaved·shader error0이다. 실제21시1114×857·30°/350°·2px·같은 Player/Camera·maps/mesh/Transform·36재료를 light off/on PNG와 함께 관측했다. 원본cache189+현재MaterialMap4 hash 불변, 기존 night 함수 불변, 거리257표본의 유한성/단조/0기여 항등을 마지막gate에서 확인했다. WorkLoop는 complete이며 이는 제한된 기술 판정이다. 별도 캐릭터 PBR·warm광원의 단계·작은 marker 원화·동적 가구 shadow solver·전체 미술 완벽·Standalone빌드는 이번 변경/검증 대상이 아니다. 실제 화면은 light21/readable-on.png이며 Play 종료 후 저장된 편집 상태로 복귀했다.

## 195. 백색 3단계 양자화 복원 `[MAP-01]` `[PIXEL-01]`

- `[최신 정정/구현]` 사용자가 그라데이션은 기지의3단계 양자화라고 정정했다. N21 연속 보간/bool/분리합산을 제거하여 Common/NativeReadable/NativePalette/SteppedLocalLight 네 계산 파일을8711b7c로 복원했다. 같은 이동 광원을 white/bands3/intensity.8/radius14로 저장했다. intensity4.2는 `.5*4.2*.55`가 최고명암을 넘어 중간 단계를 없앴고, 초기radius7.6은 실제 높이 때문에 최고 바닥 단계에 못 미쳤다. 첫 화면/gate의 불충분한 조건을 보존하고 해당 광량·반경만 수선했다. 백색·motion·6다른광원·원본/기하/팔레트·2배 카메라는 유지한다.
- `[실제 GPU/Play/제한 판정]` light22/final은 실제21시1114×857·30°/350°·2px, 같은 Player/Camera·maps/mesh/Transform·36재료·shader error0이다. 활성 바닥 cache의Y=.015m에서 peak .81838이 Q3 최고기준.75를 넘으며 최종화면에 안쪽/중간/바깥 명암이 보인다. 원본art193 hash 불변·기존4계산 일치·fixtureband0/1/2를 마지막gate로 확인했다. 첫 observer의 바닥 자식/name 가정은 실패했고 이미 성공한 저장을 반복하지 않고 실제 position/material map 참조로 관측만 고쳤다. 최종graph complete는 제한 기술 판정이다. Play 종료 후 저장한다. 캐릭터별 명암·동적 가구 shadow·전체 미술·Standalone빌드는 검증하지 않았다. 건물 자동 평면은 별도 A30 연구이며 이번에 생성기를 변경하지 않았다.

## 196. 세 유광 단계와 기지 백색 합성 수선 `[MAP-01]` `[PIXEL-01]`

- `[정정/원인/구현]` 사용자는 N22 화면이 두 단계·누런 광이라고 판정했다. Q3={0,.5,1}은 무광0을 포함해 실제 빛이 두 단계였고, native 최종 밝기 분류와 재료색 곱셈이 기존 기지의 RGB additive 표현과 달랐다. 같은 moving light만 native additive opt-in으로 연결했다. Q+=ceil(3a)/3의 세 양수와 0을 분리하고, 기존 밤 색 뒤에 백색 기여를 한 번 더한다. 다른 광원의 기본 경로·원본193아트·팔레트·기하·maps·motion·카메라/격자를 유지한다. 전체표면3D/방향별 프레임은 `docs/references/pixel_object_multiview.md`의 O23 조사이며 사물 재제작/설치는 하지 않았다.
- `[실제 Play 호출/제한 판정]` light23/moving-on.png는 실제21시·30°/350°·2px·같은 Player/Camera·maps/mesh/TRS이며 shader error0이다. GPU diagnostic의 linear 광량0/.146667/.293333/.44는29,704/291,082/139,228/28,252px, 최종RGB에서도 백색 증가를 세 구간 각각289,506/133,980/28,252px에서 확인했다. 실제우측이동과off/on을 보존했다. 전체8광원의 원래 직렬화값은 새 opt-in하나 외에 불변이며 saved scene diff는 flag1행이다. gate의 Edit저장/광원보존 조건을 추가한 새 final graph는 처음 atomic state 저장이 WinError5로 막혔다. 읽기 확인상 Unity작업은 제출됐고 검증 노드는 미실행이어서 해당 로컬파일 저장 권한으로 마지막 검증만 이어 완료했다. Unity 관측 재실행0, 최종 EditMode saved/dirtyfalse다. 미술 완벽·캐릭터 수광·가구에 가려지는 이동광 그림자·Standalone빌드는 미검증이다.

## 197. 이동광의 범위·강도 분리와 무광 구간 수선 `[MAP-01]` `[PIXEL-01]`

- `[정정/원인/구현]` 사용자 피드백은 방 전체를 덮는 과도한 범위·픽셀 불일치 의심·밝기 관리다. N23의 ceil은 모든 양수 광량을 최소1/3로 올렸다. 같은 이동광만 반경14→5m·강도.8→.4로 낮추고 opt-in ramp 입력.1/.3/.5에서 세 유광 단계, 그 아래0을 반환한다. 기존 백색 additive·밤색 함수·다른 광원·motion·카메라/격자·193아트·map/mesh/TRS를 유지했다. 새 제작/변환은 없으며 설계·식·공식 밝기 자료는 BUILDING16.md N24에 있다.
- `[실제 Play 호출/제한 판정]` light24/moving-on.png는 기존 실제 카메라1114×857·21시·30°/350°·2px다. 실제 GPU의0/.073333/.146667/.22 영역은337030/98330/42722/6640픽셀, 최종 백색 RGB 기여도97696/42722/6640픽셀에서 관측했다. 유광 면적은 같은 관측 화면에서458562→147692픽셀(약32%)로 줄었다. 두 바닥 ROI의8900/11310개2×2칸 내부 불일치는0이며 경계를 포함한다. 곡선 계단의 선분 길이와 픽셀 한 칸 크기는 구분한다. 다른 광원·193파일hash·같은Player/Camera·기하가 불변이며 shader error0·EditMode 저장/dirtyfalse다. scene diff는 radius/intensity 두 값뿐이다. 실제 관측1회→고정 light24_gate 마지막 판정으로 WorkLoop가 완료됐다.
- `[보존/한계]` 관측의 clock/광원toggle/diagnostic/motion을 복원하고 Play를 종료했다. 아트 재생성0, 기존 좌우 이동 두 위치 관측이다. 픽셀 검사는 해당 바닥 두 영역으로 한정하며 전체 캐릭터/모든 사물·미술 완벽·가구에 가려지는 이동광 그림자·Standalone빌드는 이번 판정 대상이 아니다. Intensity/Range·기본 환경광·표시 exposure·단계 ramp를 분리하고, 이번에는 광원 강도/범위와 무광 threshold만 변경했다.

## 198. 누런 벽등 원인과 재료 계열 오브젝트 경계 `[MAP-01]` `[PIXEL-01]`

- `[요청/원인/구현]` 술병에 겹친 누런색은 활성 aligned 벽등2개 RGB(1,.74,.42)의 기여였다. 같은 Play 카메라의 벽등 on/off에서 선반 ROI54830px의 평균linear차(.023778,.011935,.003456)를 관측했고 MaterialOnly로 병 자체의 갈색·녹색과 구분했다. 두 벽등 색만 white로 저장했다. NativePaletteSurface16의 edge1/2 검정 강제를 기존 최종재료색C의 `SRGBToLinear(LinearToSRGB(C)·.8)`로 바꿨다. 기존 crease3·바닥rank·geometry/coverage/depth·193아트·PPU/카메라·N24 이동광·밤 함수를 보존한다. Unity가36재료에새scale.8을1행씩직렬화했고scene은두벽등g/b override만추가됐다. 캐릭터선은별도owner로유지했다.
- `[실제 관측/판정 수선]` style25/after/moving-on.png는 실제21시·1114×857·30°/350°·2px·같은Player/Camera·maps/mesh/TRS·shadererror0이다. 첫판정기는반투명선까지불투명으로가정하여실패했다. 기존 UrbanOcclusionFader의SrcAlpha/OneMinusSrcAlpha와색endpoint를확인하고원래제품계산은유지한채판정식을수선했다. NativeStyle25Observation은같은saved material파라미터0/.8/1만변경하고복원한다. 변경14008px 중불투명4680px의sRGB.8 최대오차.003137,반투명9328px는합성endpoint순서와linear차비율.57987~.68041을충족했다. 선밖최대RGB차0,최종비선백색3단계97696/42722/6636px,두바닥ROI내2px칸불일치0,193아트hash/다른광원설정이불변이다. 실패state를보존한request-final/state-final의고정gate가완료됐으며제품색수선재실행0이다. 기존Diagnostic Enum의8항목Inspector drawer 경고는shader컴파일error와구분한다.
- `[밀도/한계/인계]` 제공 Grave Seasons1920×1080의약4px와현재1114×857의2px는같은표시크기가아니다. 같은전체가로폭기준은약2.32대2px이며,관측격자로환산한긴가구는204대95칸·작은병12×25대10×19칸·캐릭터79×159대31×36칸이다. source sprite/물리치수미확인으로미터당PPU가아닌추정이며전체해상도를낮추지않았다. 현재수식/실행기/실패귀속은BUILDING16.md N25·Tools/Building38 README에있다. 원본재생성0,관측후광원/시간/선색을복원하고Play종료/저장상태다. 미술합격·캐릭터변경·전체그림자차폐·Standalone빌드는이번범위가아니다.

## 199. 테스트 이동광과 방 전체 전등 효과 분리 `[MAP-01]` `[PIXEL-01]`

- `[요청/원인/구현]` 사용자 요청은 반딧불 같은 테스트 구체를 보존하고 실제 건물 전등을 따로 구현하는 것이다. 기존 local radial/normal 계산에는 전등 스위치에 연동된 방 간접광이 없었다. 기존 SteppedLocalLight의 default Local을 유지하고 두 aligned 벽등만 RoomLamp로 바꾸었다. 같은 anchor의 paired Unity Point Light2개가 white/range3.2/intensity3.6/Hard shadow의 실제 직광을 계산한다. 같은 owner enabled가 direct와 room-box-union 안의 isotropic indirect를 함께 제어하며 custom radial 중복은 제외한다. 새 Manager·전역 ambient·원화/기하/격자 변환·입력 단축키는 없다. disabled room box는 collider.bounds가 empty이므로 authored OBB를 worldAABB로 계산해 frustum eligibility에 합쳤다.
- `[실제 Play 호출/GPU]` room26/play에서 모두off/전등만on/구체만on/둘다on과 전등shadow off를 관측했다. 전등810423px·구체314404px·shadow109710px 차이를 실제PNG로 측정했다. 먼 방 projected 표본50곳에서 linear .1980693의 백색간접광과off0을 확인했다. source/cache/material/mesh512hash·194mesh계층/TRS·같은Player/Camera·30°/350°·2px·shadererror0을 보존했다. 두 바닥ROI의8900/11310개2×2칸 불일치는0이다. 최종재료색·무늬·금장·국소면명암은 lamps-only.png에 남으며 검사를 미술 승인으로 바꾸지 않는다.
- `[기록/저장/한계]` 최초 observer binding은 Unity missing-component를 CLR ??로 판정하여 실패했고 Unity ==null/실제component 검사로 원인을 고쳤다. 기존오류기록은 삭제하지 않았다. 초기 WorkLoop final은 observer 저장 함수의 codehash 변경을 거부하여 uncertain으로 보존했다. 외부 gate 미실행을 확인한 뒤 기존관측을 재사용한 명시적 validation-only final graph가 완료됐다. 생산/Play 재실행0, 저장된 scene은 테스트 인스턴스의 role/pair override와 Light/URP data2쌍뿐이며 prefab전파0·EditMode/dirtyfalse다. 메뉴 Tools/Fantasy Survival/Room lighting은 전등/구체를 각각 제어하고 runtime API는 SetLightingEnabled다. 간접광은 근사이며 실제GI/APV·물리전등스위치모델·문간접광전달·캐릭터미술·Standalone/GPU Profile은 미구현/미검증이다.

## 200. 재료색을 거치지 않는 조명 덧칠과 청색 재색칠 수정 `[MAP-01]` `[PIXEL-01]`

- `[원인/기술]` 사용자가 모든 조명이 물감 섞인 듯 싫다고 하여 Unity6000.5공식조명/Linear자료와 설치URP17.5의BRDF/radiance계산을대조했다. 실제Editor/Play 모두Linear·cameraHDRtrue·postfalse·활성Volume없음이다. native의stencil2는fullscreen을제외하므로이중pass가아니었다. blue우세target보간/채널별tint반올림과 `nightColor+nativeAdditiveLight`의albedo없는덧칠이재료색차이소실·희게덮임의원인이다. 캐릭터flat/PBR는이미albedo곱셈이므로보존했고volumetric/halo의시선산란additive도유지했다.
- `[구현/고정 모델]` MaterialLightResponse27의linear `A×[Q(Ybase)×Ebase/maxRGB(Ebase)+Estepped]`로native표면을계산한다. zeroE는0, 기존Q=.55/.78/1과threshold.12/.4는읽기용toon노출로명시한다. local을다시Q에넣어세단계를접지않는다. 강한재료경계의sRGB.8은같은lit색을사용하며표면의강제saturate를제거했다. non-readablebranch도RGB채널별tint양자화대신같은재료filter를사용한다. 일반worldfullscreen은DstColor One증폭으로흰덧칠을없앴지만albedo없는screen근사다. 원본/cache/PPU/기하/광원색·범위·밝기/하늘·배치·카메라값은변경하지않았다.
- `[실제 검증]` 프로덕션통합전floatGPU96case의CPU식오차최대4.085e−8(허용1e−5),black재료0,백색local세양수단계/재료채널비보존12검사통과다. 실제Play21시의기존N26광원행렬을1회관측했다. 전등shadow126670px차이·512source/cacheSHA·194mesh/TRS·같은Player/Camera·moving파라미터·2px와두floorROI불일치0·shadererror0을확인했다. 기존Console8error대비신규0이며보존했다. `light27/play/both-on.png`는흰덧칠/뒤쪽목재purple변색을제거한실제게임그림이고N26before는보존했다. 단순GPU계산을미술합격으로보고하지않는다.
- `[절차/저장/한계]` WorkLoop의통합→실제관측→고정gate3노드가완료됐다. 첫RunCommand의중첩클래스는도구rewriter가namespace에중복생성하여명령컴파일만실패/관측실행0이었다. 간단한명령으로1회관측했고기존Enum drawer warning때문에tool은partial로보고했으나관측파일과finally복원을확인해재실행하지않았다. Play종료·같은source상태복원·sceneSavedtrue/dirtyfalse·scene파일diff0이다. 일반world정확diffuse/실제GI/캐릭터미술/Standalone·성능은남은한계다. 새후처리필터·외부에셋·원본재제작0이며현재계약/실행경로는BUILDING16.md N27와Tools/Building38 README다.

## 201. 원형 메시를 재사용하는 픽셀 표면·그림자의 공유 격자 변환 `[MAP-01]` `[PIXEL-01]`

- `[요청/출처/원인]` 요청은 그림자와 픽셀 메시를 일치시키고 원형 메시를 그대로 쓰는 것이다. 현재 가구의 cache/caster는 옛 Blender 모델이 아니라 geometry16 부품 정의에서 같이 나왔다. N19는 재료만 변경했다. 동일 원형을 이미 사용하는데 SnapNativeGrid가 display clip.xy만 이동하여 cache world/depth/light와 caster가 원위치에 남았다. actual Play의 최대 편차2.433295 screen px가 있었다. 새 geometry나 임의 offset 디자인으로 교체하지 않았다.
- `[변경]` NativeSurfaceGridAlignment가 원래 카메라/원본 grid phase를 world δ로 옮겨 display/caster의 MPB에 똑같이 전달한다. native vertex, ReadSurface position/depth/light와 원형 shadow vertex가 같은 δ를 한 번 적용한다. shadow는 δ→punctual direction→기존 URP bias/clamp 순서, 원래 Cull Off를 보존한다. render-only bounds도 이동하고 disable은 기존 bounds/property를 복원한다. GameMap1의44 caster material 참조와 component 하나만 저장했고 원형 메시·collider·부품/캐시·색·PPU·TRS·조명은 유지한다.
- `[실제 관측]` current39 counter의2phase×2·4배 GPU4case에서 cache centre 재투영 최대.000153px, solid screen sample 최대.002678px, 각case common hit최소90797개, pair δ오차0·shadererror0이다. 같은 점이 아닌 cell-centre/sample-centre를 직접 차이 비교하지 않는다. 실제 Play RoomLamp shadow on/off126980px 차이,44pair 공유 offset/투영오차0·2px·같은Player/Camera·512원본 bytehash/194geometry·두floorROI grid0·기존 전등과이동광 독립 제어 보존을 관측했다. 최종uniform경로의 추가실제Play frame도 촬영했다. 그림은 shadow28/final-frame/both-on.png이며 캐릭터/미술 승인을 의미하지 않는다.
- `[실패/복구/한계]` fixture의 MonoBehaviour field MPB 생성예외·옛38 입력 선택은 시험장치에서 수정하고 실패기록을 보존했다. 초기최종gate는36원본material에ShaderLab 새기본값이 저장된것과moving JSON서식차이를차단했다. renderuniform을MPB/HLSL에만두고 EditorAPI로새기본값만제거해원본bytehash를복원했다. moving해석값은동일했고실제compact기록을보존한뒤원래서식을재사용했다. 전후GPU4case측정은동일하다. 초기state/failure와freeze는보존하고명시재개final-only graph가174/174를통과했다. Play종료·Edit/saved/clean이다. PC/fullviewport/ortho/renderScale1/dynamic-off에서검증했으며연속mesh/centre-sampled외곽coverage·곡면tri근사·모바일/업스케일러/Standalone성능·캐릭터미술은남은한계다. 현재결정/허용범위는BUILDING16.md N28 한곳이소유한다.

## 202. 넓은 픽셀 면의 재료 군집과 손잡이 곡면 법선 `[MAP-01]` `[PIXEL-01]`

- `[요구/원인/근거]` 단색 면의 밋밋함과 둥근 부위의 한 줄 단위 단계 명암을 연구·적용했다. 실제 navy12115칸과 brass1974칸의 rank는 모두2였고 readable shader는 목재 외의 G를 읽지 않았다. SLYNYRD Texture의 연결 군집·밀도·여백, Saint11 Shading의 평면/곡면·재질 구별과 Banding의 중복 윤곽 반례를 BUILDING16 N29에 정리했다. 원화 전체 복사는 투명부/장식/구운 명암을 섞으므로 제외했다.
- `[구현]` 기존 checkout 수납장 한 종류에서 object-chart cubic value field와 짧은 결을 rank1/2/3으로 양자화했다. G5076칸 변경, 기존 목재 G·R/B/A와 원본 palette 유지다. handle front115칸 안에서 양쪽 가장자리 각3nativecell에20°/40°/60° 법선 띠와 중앙을 넣어98칸 normal만 변경했다. 비등방 tick 대신 투영 Jacobian의 nativepx 거리로 띠 폭을 계산했다. fixed-light RGB를 재료에 굽지 않으며 기존 엔진 입사광을 사용한다. 새 material/float normal 버전과 기존 flag opt-in만 만들고 씬은 checkout material reference1개 변경이다.
- `[실제 검증]` 실제 Play 동일Player/Camera·30°/350°·2screenpx의 전후19568px차이를 관측했다. mesh/TRS·조명 설정·512원본 SHA 보존, shadererror0, generated map/f32 hash 보존과20조건 gate 통과다. 실제 GPU normal/좌우 direct fixture3장은187×211 격자·coverage차이0·CPU 기대값과최대RGB오차0byte,98handlecell 좌우반응반전이다. diagnostic3의 연속입사광을 실제3색보장으로 주장하지 않는다. 가구 전체 비교는 동일 실제카메라를 촬영에만 평행이동하여2px/각도를 유지했고 원위치 복원했다. 비교는 material29/run01/comparison.png다.
- `[실패/마무리/한계]` 관측기의 미존재 enum은 컴파일/실행0에서 기존 이동광 이름으로 수정했다. 이름만 찾는 Single은 숨겨진 역사적 checkout2개까지 잡아 촬영전 차단됐고 active native로 좁혔다. material/normal 재생성0, 기존2 graph/state/실패기록 보존 후 통합만 새해시로 재개해 integration03이3단계 완료됐다. 최종 Edit/saved/clean이다. curve normal은 얕은 표면 조명 표현이며 box caster/실루엣을 바꾸지 않아 추가 자체/투영 그림자는 없다. 모든 가구 확대적용·미술합격·Standalone/성능은 미검증이며 기존 캐릭터/바닥/다른 재료는 보존한다.

## 203. 큰 재료 얼룩을 원인별 사용 흔적·미세 반사로 교체 `[MAP-01]` `[PIXEL-01]`

- `[정정/원인]` 생동감을 면 전체의 큰 색 군집으로 해석한 N29는 물 얼룩처럼 보였다. 원인은 broad noise→3색의 임의 영역과 재료4색 제한이었다. Pelixir의 재료별 palette/world-space scratch, Adobe의 접촉 마모·환경별 dirt와 실제 목재 구조 연구를 대조해 흠집·마모·결·작은 굴곡을 별도 원인/마스크로 설계했다. 설치·새 SRP·생성 원본 복사 대신 현재 canonical chart를 사용했다. 요구/좌표/알고리즘/반례의 단일 원본은 BUILDING16 N30이다.
- `[변경]` checkout 한 종류에만 새16×10 palette/MaterialMap/float NormalMap을 연결했다. 결11666·접촉74·흠집28·하단71·노출목재9·금속변색105셀의 독립 mask를 계산했다. 작은 chip R2→R4만 허용하며 기존 wood/boundary RGB·금장 위치·N29 handle/wood normalXYZ를 보존한다. h(u,v)의 metres 미분 normal 변화 최대2.074°, 거칠기는 valid alpha에 분리 packing한다. shared shader는 확장 palette에서만 실제 URP BRDF/F0·orthographic 시선·NdotL·거리/shadow·layer/strength를 합산하고 RGB 비율을 유지한3단계/cap 반사를 더한다. SH·방 간접광·custom moving 구체는 spec 입력이 아니다. 기존4열 경로·조명 단계·배치·기하·camera/grid를 유지했다.
- `[실제 검증]` old4col MaterialOnly/ReadableFixture GPU byte차0, 새palette CPU/GPU albedo의coverage차0·최대RGB차0이다. actual PointLight 좌/우의spec 활성550/6067셀·방향차5816셀, 광원off spec0·합산상한을 확인했다. 실제 GameMap1 Play 같은Player/Camera·30°/350°·2px에서전후48428px변화, 원본512SHA·기하/조명보존·binding1·shadererror0을 관측했다. 48조건최종gate와 verify→관측→GPU gate→저장→gate5단계가완료됐다. sceneDiff는checkout material참조1개이고 Edit/saved/clean이다. 실제원배율crop은 material30/run01/comparison.png, 관측은 observation02다.
- `[실패/한계]` 초기graph feedback간선누락은실행0에서수정했다. 첫카메라만이동한Play는외부Player라지붕이가려changed0이었다. 이미지/재료를재생성하지않고기존TryTeleport진입을촬영기에연결해원인만고쳤다. NumPy bool JSON반환형도수정했고첫PNG/receipt/graph는보존했다. state atomic replace WinError5는실제cursor/active를확인한뒤미실행gate만실행했다. 미세normal은실루엣/caster를변형하지않고spec shadow는코드연결만확인했다. readable diffuse+bounded spec은스타일근사이며fullPBR/GI·미술합격·모든사물·Standalone/GPU성능은미검증이다.

## 204. Native 읽기용 노출에서 실제 그림자 손실 보존 `[MAP-01]` `[PIXEL-01]`

- `[요구/원인]` 책 그림자와 전반 조명 문제·이전 변화·자연광 존재를 확인했다. 책의 실제 closed caster는 이미 있으며 실제21시 on/off 조도 최대12byte/최종색3byte, bias0 동일이었다. `Eshadow/maxRGB(Eshadow)`와 같은 Q 구간이 직접광 손실을 다시 정규화하는 원인이다. N30의 재질/반사 변화와 전체 diffuse 문제를 구별했다. 사전 요구/수학/반례/판정은 BUILDING16 N31 R2에 고정했다.
- `[변경]` Native31Readable은 기존 URP Light 표본의 cookie/거리/layer/strength/NdotL을 재사용해 loss=ΣDi(1−Vi)를 누적한다. 노출은 Eopen=Eshadow+loss의 기존3단계에서 정하고 실제 차광 RGB는 Eshadow/maxRGB(Eopen)로 유지한다. 기존 SH/방 fill·별도 moving3단계·이미 차광된 spec·원본/mesh/배치/픽셀/광원 값을 바꾸지 않았다. shared Material27/일반world/캐릭터 shader는 변경0이다.
- `[실제 검증]` 22case ARGBFloat GPU/CPU 오차2.861e−8, 무차광 parity7.451e−9, black/zero·단조성·색광원 차광·moving 차분 검사를 통과했다. 동일 GameMap1 21시 actual camera30°/350°/2px의 책 그림자 최대차3→11, 변화400→412px, 총차840→2696이다. 전등off650143px/이동광off237899px 변화와 각 phase 동일Player/Camera·194geometry/TRS·원본/광원 보존·shadererror0,26조건 gate통과를 확인했다. 12시/21시 실제 자연광값과 별도 지붕caster1·probes0을 관찰했다. source/씬serialized diff0, Edit/compilingfalse이며 시작부터 있던 dirtytrue는 사본 보존하고 임의 저장하지 않았다. 실제 crop/no-resize 비교는 docs/artifacts/building39/light31/run01/comparison.png다.
- `[실패/한계]` 관측기 parent 경로 오류는 관측 시작 전 실제 grandparent로 수정했다. graph gate의 입력 contract 키는 command.run의 stdin 계약과 달라 프로세스 실행 전에 차단됐다. 첫3노드/state/증거를 보존하고 실제 미실행 gate만 light31-gate-recovery02에서1회 완료했다. 자연광 부재/지붕 부재가 원인이라는 추정은 현재 runtime 사실로 기각했다. 직접 지붕 차광은 있지만 SH/방 fill은 창문별 실내 간접광/GI가 아니며 그 구현·미술합격·Standalone/성능은 미검증이다.

## 205. 계산대 오른쪽 갈색 물체의 직접광 범위 복구 `[MAP-01]` `[PIXEL-01]`

- `[정정/원인]` 사용자가 지목한 것은 checkout_produce의 오른쪽 갈색 물체다. N31에서 검사한 checkout_ledger 흰 장부는 다른 대상이므로 그 결과를 이 문제의 해결 증거로 사용하지 않는다. 실제 갈색 closed caster는 이미 있고 상판 위 높이≈.1685m다. RoomLamp의 paired point range가 custom radial Radius3.2를 복사하여 Left lamp거리2.991m의 대상 뒤 receiving 영역 대부분이 cutoff 밖이었다. 실제 world/cache/δ·ray–triangle/카메라 가림으로 확인했고 설치 URP17.5의 inverse-square×smooth range fade와 일치했다.
- `[변경/수학]` 기존 SteppedLocalLight owner 한 곳에 RoomDirectRange를 추가했다. assigned BoxCollider center±size/2의8corner를 world로 변환하고 두 volume의 최대 lamp거리D에서 R=max(Radius,2D)를 산정한다. d≤D의 fade 최소(15/16)²이며 거리/NdotL/실제 차광을 유지한다. actual 범위는 Back19.445564m/Left21.330965m다. 기존 Radius3.2, moving/local 경로·전등 위치/색/세기·SH/방 fill·캐릭터·소스/기하/배치/카메라/픽셀을 바꾸지 않았다. 새 serialized 설정·shader·Manager·Update·임의 그림자 이미지는 추가하지 않았다.
- `[실제 검증]` actual GameMap1 21시 같은30°/350°·2screenpx 카메라에서 brown caster ON/OFF를 비교했다. 실제 상판 receiving union913셀 중 각2×2sample 모두 ΔY≥8byte인 최대 연결 셀은 기존0→임시 범위447→최종 코드447, 최대ΔY1.9278→18.0518byte다. 전등OFF656462px/이동광OFF237899px 변화, 같은Player/Camera·기하/TRS·owner광원설정·float cache·1539원본/재질/셰이더/씬SHA·2×2uniform·제어복원·shadererror0의29조건이 통과했다. 실제 crop resize0 비교는 docs/artifacts/building39/book32/comparison.png다.
- `[실행/보존]` WorkLoop4단계 실험 guard→owner 수정→actual 최종 관측→고정 gate가 완료됐다. 초기 init의 validation→work feedback 오류는 실행 전 차단됐으며 invalid graph/hash 보존 후 baseline의 phase만 수선했다. Unity 실험/최종 캡처는각1회·생성재작업0이다. 시작 미저장 씬을 LocalOnly/Book32/unsaved-baseline.unity 사본으로 보존했고 disk와diff0이었다. 종료Play/compiling false, 초기dirtytrue 유지·씬disk저장0이며 기존 OnEnable/OnValidate/전등 API가 새range를 자동 동기화한다.
- `[한계]` range는 URP point shadow bias의 world 크기도 바꾸므로 actual cast 경계를 같이 확인했다. 현재 직접 그림자 범위 오류를 해결했으며 간접광 차광·GI/SSAO·모든사물 미술완성·Standalone/GPU성능은 완료하지 않았다. 요구·수학·허용수선의 현재 단일 원본은 BUILDING16 N32다.

## 206. E399 원본 Player 표현 통합 `[CHARACTER-RENDER-01][MOVE-01][SHELL-01]`

- `[구현]` 기존 `PersistentGameplayShell.prefab`에 R1 Run12의 검증된 E 표현 계층을 연결했다. Player·입력·CharacterController·게임 카메라·HUD·Inventory·EventSystem과 기존 모델을 보존하며, 바인딩 뒤 이전 모델의 renderer만 숨긴다. 최종 실제 신규 자산/코드205개와 meta/폴더meta330개, 총535파일을 추가하고 기존 동일 자산23개를 재사용했다. 초기 반입계획의 상대경로 별칭16행은 실제 파일 추가가 아니며 최종 물리 경로 수로 정정했다. 필수 UniGLTF/VRM10 0.131.3은 기존 R1 로컬 UPM 캐시를 참조한다. 프로젝트 전체 복사·다운로드·원격 push는 하지 않았다.
- `[Play 호출 확인]` 원본 GameMap1에서 기존 합성 Keyboard→GameInputBindings→PlayerMovement.Update→CharacterController→Idle/Walk/Sprint 경로의 PASS,23표본,3.06666684m를 관찰했다. 물리 OS 키 입력 검증은 아니다. 가변 latest 보고서가 후속 표시 실행에서 갱신되어 첫23개 raw표본 배열은 남지 않았으며, 관찰값은 `UnityMcpAccess399/OriginalRuntime/ACTUAL_INPUT_PASS_OBSERVED399.json`에 한계를 명시했다.
- `[표시·수명 검증]` 최종960×544 텍스처를 Point·정수1배·정수원점의 Canvas로 기존 HUD 아래에 표시했다. 검수 GUI와 미리보기 카메라를 껐고 로컬 카메라/메타데이터 proxy를 영속 계층에 연결했다. 기존 DirectSceneTravel의 GameMap1→GameMapTest→GameMap1 한 왕복에서 Player·Camera·HUD·Inventory·EventSystem·E외형·로컬카메라·proxy·표시Canvas를 포함한10객체ID가 동일했다. 첫 복귀 호출의 fade guard 거부는 검사 호출 순서 문제로 보존하고, guard 해제 후 복귀만 수행했다.
- `[증거·종료]` 작업 폴더 `C:/Users/JG/Documents/Codex/2026-10-07/task/UnityMcpAccess399/`의 `OriginalRuntime/ORIGINAL_GAME_VIEW_FINAL399.png`, `TRAVEL399_FINAL.json`, `RELAY_READONLY_FINAL_STATE399.json`에 실제 화면과 관측을 보존했다. 저장 synthetic input/review GUI는 false, 종료 Play/compiling false·background false·timeScale1·captureDelta0·원본 PC pipeline·GameMap1 dirty false를 확인했다. Editor 프로세스는 유지했다. 교체 전 사용자 tracked12변경은 로컬 checkpoint `3f6c7a819ee1e958f43ea7ba13164c0e42596be3`로 보존했다.
- `[한계]` 이 통합은 398 thin 밝기 불연속이나 전체 픽셀 튐의 해결이 아니다. 픽셀/모션 연산·판정 임계치를 바꾸지 않았다. 미관·접지·옷 관통/관절·전체 loop 품질·실행 성능·Standalone build는 통과로 확대하지 않는다. VRM spring collider 식별자 중복 경고와 API obsolete 경고는 남아 있으며 초기 shader 등록 전 import 실패는 필수 shader 등록 후 해당 VRM 한 파일의 import로 복구했다. 추가 전신 모션 렌더/보정은 수행하지 않았다.

## 207. 현재 E 캐릭터의 원본 윤곽을 보존하는 돌출 셀 제거 `[CHARACTER-RENDER-01]`

- `[요청·대상]` 2026-10-20 사용자가 조사에 근거한 수정, 돌기 확대 금지, 정상 머리카락·옷 끝 보존, 실제 걷기 전후 비교를 요청했다. 실제 `PersistentGameplayShell(Clone)/Player/E395_Visual_165cm_Trial/AvatarSample_A144_SourceMToon_ArtUnaccepted(Clone)`의 Body 원본 GUID `3c6037cd1f59e9d4c97c94249271077d`와 `PlayerLocomotion397.controller` 연결을 확인했다. 공존하는 Chibi Kenney·CC0 마네킹·Kenney 좀비는 대상이 아니다.
- `[변경]` `GameMapIntegration333/Runtime/SourceSilhouetteContour.cs`의 `Apply/Envelope/BuildTopology`를 추가하고 `HeadLocal367.RefineSourceSilhouette`를 기존 선택 맵 업로드 전에 연결했다. 현재 스킨 메시의 투영된 부위별 연속 윤곽을 정확한 선분 상단 포락선으로 계산하며, 선분 교차점도 오차 검사에 포함한다. 세 안쪽 지지 셀의 owner/part가 같은 한 칸 돌출만 후보로 삼고, 원본 곡선→끝점 연결선 오차 ≤0.5 논리px, 삭제 후 경계 오차 ≤1px, 연결선 바깥 픽셀 중심인 경우만 제거한다. 기존 선택기의 두 오차 예산을 재사용했으며 픽셀 추가·색 평균·이전 프레임 coverage 보존은 없다.
- `[특징 보존]` 원본 rest 위치가 정확히 같은 UV seam 정점을 묶어 실제 열린 메시 경계를 식별하고, 옷단·소맷단 경계의 1셀 이내를 잠근다. 머리/헤어 역할, torso, 원본의 큰 꺾임, 다른 owner 접점, 기존 선택기의 변경 및 주변 2셀은 제외한다. 원본 모델·스킨/본·클립·재질·카메라·픽셀 피치·Player 입력·씬/prefab은 수정하지 않았다. 기존 순서인 윤곽 선택→복원/머리 결합→외곽선→native 합성을 유지했다.
- `[Play Mode 호출 확인]` 원본 GameMap1의 실제 `Rig|Walk_Loop` 1.333333초를 60Hz 80프레임으로 관찰했다. 원인 분리를 위해 PlayerMovement만 임시 비활성화하고 root를 고정했으며 Animator는 enabled/speed1로 진행했다. 정지 포즈 이동이나 실제 키 입력 검증이 아니다. 최종 `IntegratedPairs`는 컴파일된 프로젝트 경로의 결과를 먼저 캡처한 뒤 **같은 시뮬레이션 프레임**에서 새 삭제만 해제해 기존 선택기 대조를 렌더하고 수정 맵을 복원한다. 80쌍 모두 bone/world hash 동일, 서로 다른 bone hash80, Walk clip80을 확인했다.
- `[실제 결과]` 외곽 한 칸 극값은 프레임별 합계113→52, 실제 제거61셀, 추가0, 머리/헤어 RGBA 변경0, 삭제 이외 owner 변경0, 연결 성분/구멍 회귀0이다. 원본 오차 최대0.4942965px, 경계 오차 최대0.7359048px로 고정 범위 안이다. 열린 경계8회·큰 원본 곡률24회는 보존 분기로 남았다. 이 수치는 모든 남은 돌출의 미술적 적합성을 판정하지 않는다. 최종 Unity Error/Exception/Assert 조회0건. WorkLoop `production_state.json`의 고정 gate가 통과했다.
- `[실패와 교정]` 초기 비교 훅은 선택 전/후 두 번 호출되는 경로에서 선택 전을 캡처해 `contourReady=false`였고 실제 제거0으로 불합격이었다. 선택 완료 후로 시험 장치만 교정했다. 별도 Play 실행 간 비교는 mask/삭제 위치가 같아도 bone hash/RGB가 달라 최종 비교에서 제외하고, 위 동일 프레임 대조로 교체했다. 실패 기록은 삭제하지 않았다. MCP 동적 컴파일의 비공개 reflection 사용은 도구 검증에서 거절되어 기존 공개 `effectiveProjection`으로 바꿨다. 이는 프로젝트 알고리즘 또는 자동 승인 검토의 거절이 아니다.
- `[증거·한계]` 전달물은 `docs/artifacts/character-silhouette-20261020/`의 `walking-before-after.gif`, `validation.json`, `active-character.json`, `decision.json`, `manifest.json`이다. GIF는 80개 원본 중 격프레임40개를 30fps에 맞춰 표시하고, 관찰용으로만 nearest 4배 확대했다. 전체 float·캡처 코드·그래프·실패 근거는 `LocalOnly/SilhouetteWalk20261020/`에 보존한다. 다른 시점/clip·실제 입력 이동 결합·thin 명암 불연속·Player build·실행 성능은 미검증이다. 테스트의 다중 GPU readback 시간은 제품 성능으로 보고하지 않는다.
- `[종료]` 원본 Editor에서 Play=false, compiling=false, GameMap1 dirty=false, background=false, captureDeltaTime=0, timeScale=1을 읽어 확인했다. GIF40프레임·총1330ms와 문서 크기 검사, 관련 diff 공백 검사가 통과했다. 기존 QualitySettings/TimeManager 및 다른 미추적 자산은 보존하고 이번 변경 경로만 커밋한다.

## 208. 사용자 요청에 따른 돌기 필터만 철회 `[CHARACTER-RENDER-01]`

- `[요청·판정]` 사용자가 §207 비교에서 개선을 확인하지 못한 뒤, 추가한 돌기 필터와 연결 코드만 수정 전으로 되돌리고 다른 작업과 수정본 기록을 보존하도록 요청했다. §207의 제거61셀은 80프레임 합계이며 사용자 지적 현상의 시각적 해결을 입증한 수치가 아니다.
- `[복원]` `HeadLocal367.cs`에서 `sourceContourEnabled`, `sourceContourResult`, `RefineSourceSilhouette`와 `RenderFrame`의 호출만 제거했다. 파일의 Git blob `29474955001e6b593ed6532af83fedf8d76dc35f`는 필터 추가 전 커밋 `111638727f8be1b064916c0c48ddec1f1d903389`와 정확히 같다. 추가했던 `SourceSilhouetteContour.cs`와 해당 `.meta`만 제거했고, `Assets`의 C#에서 필터 참조가 남지 않았음을 확인했다.
- `[보존]` 수정본은 기존 로컬 커밋 `7e28757fb33f1b6281707fc11db1a81de4350680`에 보존한다. `docs/artifacts/character-silhouette-20261020/`의 기존 파일 전체와 기존 dirty `QualitySettings.asset`·`TimeManager.asset`은 복원 전후 SHA-256이 동일하다. 다른 자산·씬·prefab·캐릭터 원본·애니메이션은 변경하지 않았다. §207 및 비교 원본은 당시 실험 기록으로 남긴다.
- `[검증]` Unity Editor 8176의 실제 프로젝트 경로를 확인하고 기존 재생을 중지했다. 복원 후 `PLAY=False`, `COMPILING=False`, `SCRIPT_COMPILATION_FAILED=False`, `GameMap1 DIRTY=False`, 필터 에셋 없음·기존 Head 스크립트 존재를 읽었다. 변경 전후 Error/Exception/Assert 조회 모두 0건이다. 명시적 Refresh 호출은 discovery 파일 부재로 실행되지 않았으나 이후 재연결된 Editor에서 위 import/compile 상태를 확인했다.
- `[증거·범위]` `LocalOnly/SilhouetteWalk20261020/Rollback20261020/`에 기준 해시·정적 복원 검사·Editor 호출 결과를 보존한다. 이번 작업은 기존 코드 복원이며 걷기 재촬영·새 시각 수정·Standalone build는 실행하지 않았다. 종료 상태는 Play=false이고 씬을 저장하지 않았다.

## 209. 동일 머리카락 fallback의 외곽선 명암 덮어쓰기 수정 `[CHARACTER-RENDER-01]`

- `[대상]` 원본 프로젝트의 기존 Editor 8176·GameMap1·Unity6000.5.9f1/URP17.5·실제 E399→348→Native395 연결에서 검증했다. 시작 HEAD `36cbf50da4c8104b28eafc30a07ab256fddf08f4`는 버전 식별자이며 정상 기준으로 간주하지 않았고 새 기준 커밋을 만들지 않았다. 과거 R1/§207/정지 이동463은 이번 통과 근거가 아니다.
- `[재현]` 기본 정면 실제 Walk16프레임의 덮어쓰기는0이었으나, 카메라·크기를 유지한80도 Walk의 셀(229,48)에서 기존 선 명암이 348 fallback 이후 원래 머리카락 RGB로 돌아갔다. 원본 EyeMerge intrinsic/audit는0, 348 visibleFeature는0이었다. head 좌표(230,48)의 base/hair 깊이는13.7224178314로 같고 main 깊이13.7306365967을 현재 depthOffset0.008218865로 변환하면 정확히 일치한다.
- `[최소 수정]` `EyeFeature348.compute`에서 base/backing fallback을 선택한 직후, 현재와 같은 covered hair 역할·정확한 깊이를 다시 고르면 이미 합성된 `old.rgb`를 보존한다. 뒤의 실제 눈 선택·더 가까운 가림·owner/depth·coverage·선 생성·색/카메라 정책은 변경하지 않았다. 새로운 cache/hysteresis/quantization/threshold는 없다.
- `[실제 비교]` 같은 Unity 프레임마다 실제 수정 셰이더→원본 셰이더 대조→수정 셰이더 복원을 실행했다. 실제 `Rig|Walk_Loop`16쌍, 정규화시간0.0125→0.200000033, 서로 다른 뼈 해시16개, 쌍 안의 bone/world/preparedOwner/nativeOwner 불일치0이다. 외곽선 덮어쓰기11→0, 외곽선 밖 변경0, coverage 변경0이며 기본 정면 실제 Walk4쌍은 색·owner 차이0이다. 루트 고정의 짧은 구간이며 전체loop·다른방향/clip·접지/관통·미관·명암 전체·성능·Player build 통과로 확대하지 않는다.
- `[전달·정리]` `docs/artifacts/character-hair-fallback-20261020/validation477.json`과 첫 프레임 무손실 비교에 정확한 색·깊이·SHA256·증거 경로를 보존한다. 실제 전신 GIF16프레임은 모든 프레임을 디코딩했고 공통 palette의 새 차이/숨긴 차이0이다. Library `libfile_d9ecfb30a6b08191a3882b808b3f15f0`; 원본 float/PNG·캡처 코드는 `C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/`에 있다. 임시 원본 비교 compute는 공식 asset writer로 제거했고 기존 `PostView366.AfterRender`와 실제 수정 shader 바인딩을 복원했다. 최종 Console Error/Exception/Assert0, Play=true·paused=false·compiling=false·GameMap1 dirty=false·captureDeltaTime0이다. 기존 dirty QualitySettings/TimeManager 및 다른 미추적 자산은 보존한다.

## 210. 기본 비활성 머리 곡선 소스 실험의 소수 위상 보존 `[CHARACTER-RENDER-01]`

- 491의 첫 누락은 head(233,40)에 선택 가닥118삼각형이 전혀 겹치지 않는데 정수화한 끝점의 Bresenham이 그 셀을 선택한 연산 오류다. 인접(234,40)에는14삼각형이 겹친다. 검색 범위·좌표·메쉬 연결 부족이 아니다.
- 첫 급변은 같은 UV-section26의 x234.013107→233.993774가 floor234→233으로 바뀌며 두 구간의 정수 경로7셀을 재배열한 것이다. RDP제어점8개는 동일하고 연속 곡선 최대 이동은0.06682셀이다.
- 기존 head Probe의 대안3파일에서 Line만 연속 끝점/주축 격자 중심 평가로 수정했다. 삼각형 교집합과 동일 source primitive/UV/depth/owner,재질·눈·물리가림·480논리/960native는 유지한다. 화면좌표/위상 조건·후단closing·색history·시간threshold는 없다.
- 실제 Walk0.275~0.3625의 동일 포즈8쌍: 본행렬8/8동일,기존6프레임 후보누락→0,첫 가닥 셀전환7→1,고립셀4프레임→0. 표면패킷90개 정합,가림6개는 더 가까운 실제 다른 표면,UV최대1.49e-8·깊이9.54e-7m,머리ROI외native변화0이다.
- 493 재판정으로 별도5셀의 정상 격자교차 해석을 철회한다. 교차한 것은RDP근사선이며 원래60단면 중심곡선은 두 행 모두x>235다. 실제가시5셀은3삭제+2추가로 같은가닥 연결이 갈라지고 가운데235,42는 후보에 남지만 가시패킷에서 빠진다. 가림거절owner미기록 및 해당face/body기하 부재로 정상가림 여부는 미확정이다. 오프라인3변경 후보는 알려진 형상·연결·폭·구멍수 조건에서 불리하지 않으나 전체가림/색/시간품질 렌더는 미검증이다. 사용자에게 필수미관tradeoff를 요구할 근거는 아직 없다. 코드변경/재촬영/새최적화/기본활성화는 하지 않았다.
- 실험은 기본OFF,미관·전체loop·다른clip/각도·성능·build 미채택/미검증이다. Play·입력·Animator·background·원래PostView366훅 복원 및 임시리소스 해제 확인. 기존44d13c0수정과 사용자Quality/Time설정은 보존한다.
- 재현/증거: `docs/artifacts/hair-boundary492/validation.json`, 작업폴더 `Current472/Pairs492/`의 실제 전신A/B GIF와 `TRANSITION_TRACE492.json`/`SECOND_TRANSITION492.json`이다. 다른 Play세션 RGB를 전후 근거로 섞지 않았다.

## 211. 원곡선 선택과 정확한 삼각형 자기 가림 교정 `[CHARACTER-RENDER-01]`

- 493 미확정 가운데head(235,42)는 같은 Walk0.325의 실제 float 조회에서 renderer2/submesh1/primitive91이 자기 자신을0.287mm 앞이라고 잘못 판정한 것이었다. body/face의 실제 가림이 아니다. 근거는 `Current472/Probe494/result.txt`, 모든3renderer의 두 포즈 기하 `Geometry494/`이다.
- 같은 기본OFF 대안의 Runtime1파일만 수정했다. RDP는 방향 span만 나누고 선택 위치는 원래60단면 곡선과 실제 격자 단면의 교점으로 결정한다. 내부 RDP점을 끝점으로 clamp하지 않고 실제UV 양끝만 보존한다. 정확히 같은 source삼각형만 자기 가림에서 제외하며 나머지 깊이 판정은 double barycentric으로 계산한다. 기존 깊이허용값·눈·색·shader·허용outline과348수정은 유지한다.
- 첫494시험에서0.30의 내부 분할점이 불필요한 셀을 내며 빈 공간을 둘로 쪼갠 위반을 확인해 교정했다. 최종494B의 실제Walk0.30~0.3375 네 쌍은 동일뼈4/4,원형밖후보0,가닥연결1,고립셀0,2x2두께증가0,빈 공간5셀 유지. 493의 갈라짐·두 셀 파임 사건0.3125→0.325는 셀변화0이다. 마지막프레임의 연결된1셀 계단 이동은 원곡선 지지·연결·빈 공간 보존을 함께 확인했다.
- 45source패킷 중41GPU일치,나머지4는 정확한r2/sm0/primitive555의UV·깊이로 가려졌다. GPU UV오차1.49e-8,깊이9.54e-7m,셀중심-원곡선최대0.4672cell. 진짜UV0끝은 다른hair삼각형35~48mm 앞가림을 유지한다. 머리ROI밖 native변화0,동일삼각형 facing변경0이다.
- 전신GIF는 새 동일실행의 원본 centre source 대494이며 각960x544/6배느린4프레임 발췌이다. 과거492를 같은 실행의 수정전 RGB로 부르지 않는다. 첫frame head offset[-3,0]/이후[-3,-1]을 기록했다. 근거 `docs/artifacts/hair-boundary494/validation.json`, 로컬 `Current472/Pairs494B/`.
- 기본OFF·외형미채택. 전체loop/다른가닥·clip·카메라/성능/build 미검증. 종료 후Play·입력·Animator·Idle·background·PostView366 복원과 자체리소스해제 확인.44d13c0/b1b144e/사용자Quality·Time설정은 보존한다. 전체프로젝트 완료를 뜻하지 않는다.

## 212. 406ce30 후보 전체 Walk 한 루프 검증 실패 `[CHARACTER-RENDER-01]`

- 제품코드 변경 없이406ce30의 실제Walk 한 루프81쌍(closure포함)을 한 번 수집했다. 같은실행·뼈/광원81/81일치,각native960x544. 후보는73표본ready,8표본에서 원곡선8연결 생성 실패로 원본source로 복귀했다. 서로다른80위상 중7실패이며 위상0이closure에 반복된다. 기본활성화 불가다.
- 최초위상0의 실제연속곡선은 연결돼 있으나 span20..26의y40.5셀(233,40)에서 다음span26..39의x232.5셀(232,38)로 넘어가며 연결구간을 샘플링하지 않는다. Chebyshev2칸 점프로 검사실패하며,이검사는visibility전이다. 위상0.6875~0.7375/0.9875에서도 재현됐다. 원래변형기하는closure에서9.54e-7m내로 같고 양끝 모두 실패해 초기진입만의 문제도 아니다.
- 814source패킷,774headGPU일치,40개는 정확한 다른삼각형·UV·world·depth로 복원해 모두 더가까운표면임을 확인했다. 그중2개는GPU깊이차가CPU0.1mm허용값보다 작으며 오류2건을 뜻하지 않는다. sourceUV오차6.7e-8,world1.71e-6m,GPU깊이9.54e-7m,main패킷누락0/facing변경0이다. 실제UV0끝은81표본 모두 알려진hair표면에 가려졌다. CPU버림전체의blocker/몸·얼굴provider입력은 매프레임 저장하지 않아 전체가림통과로 부르지 않는다.
- 새전경고립셀위치/2x2두께덩어리/머리ROI밖native변경은0. 다만ready에도틈2+2/1+4등분할이 관측돼 전체미관·계단규칙을 통과로 선언하지 않는다. 위상0.6875의9셀급변은 후보→원본source복귀이며 정상격자교차가 아니다. 먼저 같은원곡선의방향span접속책임을 고쳐야 하며 사용자미관선택이불가피하다는근거는없다.
- 같은Editor실행에서A/B순서를교대하고 owner RenderFrame+1pxGPUreadback을 기록했다. 초기2표본을분리한72ready의중앙값은원본287.93ms/후보321.17ms,p95604.97/655.82ms. 변동폭이크며플레이어FPS나성능예산통과를뜻하지않는다.
- 기존PersistentGameplayShell.prefab은21시시작/자동진행/실제60초당하루다. 실제gameTime13.556688초동안시각5.422673시간과광원이변해24/60공식과일치한다. 이번캡처는현재20.2035751시를임시고정했고밝기/색/설정은튜닝하지않았다. 과거494캡처의정확시각은미기록이다. 종료후자동시계true·입력·Animator·Idle·Play·PostView366·기본OFF·자체리소스해제확인,원래Quality/Time·프리팹해시보존.
- 근거 `docs/artifacts/hair-boundary495/validation.json`, `Current472/Loop495/`. 전신GIF Library `libfile_cfd7cec55d388191883fd5b53748475f`는fallback표본에명시라벨이있다.406ce30/44d13c0/b1b144e는보존하며전체프로젝트완료가아니다.

## 213. 원곡선 방향구간 접속 수정과 제한 검증 `[CHARACTER-RENDER-01]`

- 같은기본OFF source대안Runtime1파일에서 방향span사이의 빠진연결셀 책임을 수정했다. 기존선택점이8이웃이면그대로두고,아니면그두점사이의원래UV순서곡선이통과한셀만추적한다. 순서있는후보그래프의최소8경로를고르며동일길이면원곡선과의셀중심거리합이작은경로,완전동점이면UV순서를쓴다. 후단dilation/좌표·위상조건/history/epsilon변경은없다. 원본패킷이없으면부분ready대신명시unsupported로기록한다.
- 저장된실패7위상과정상대조6위상을실제컴파일된순수C#선택기로검증했다. 실패마다원래삼각형이있는연결셀1개만추가,연결/끝점/결정성/삼각형지지/2x2없음통과,정상6대조는변경없음. 진단JSON배열복원null의Execute NRE는이진입력으로교정했으며제품오류와구별하고기록을남겼다.
- 최초실패주변실제Walk0.975~1.0375의6쌍만추가수집했다. 동일뼈/광원6/6,ready6/6,원본복귀/후보누락0,66source패킷headGPU·main일치,CPU가림47개는3renderer저장기하재검증과일치. 새연결셀2표본은실제primitive65/UV/깊이로GPU일치했다. sourceUV최대4.46e-8/world1.64e-6m,GPU깊이9.54e-7m,셀중심-원곡선0.4035cell다.
- 새전경고립위치/원선택·가시선택의2x2덩어리/facing변경/머리ROI밖native변경0. 진짜UV0끝은6포즈모두기록된hair가림유지,정상4실제대조선택불변. 틈은한개로유지되며3→2셀변화는기록했고새연결셀은그전환에서동일하다. 전체시간적틈/계단품질의완료로부르지않는다.
- 연결보장은지원정수격자안의유한한UV순서연속곡선과기존단조span조건에대한가림전source셀경로다. 각원래선분의격자통과목록이8연결이므로최소경로도항상연결되며,실제표면패킷지원은별도필수검사다. 가림/viewportclip후의모든가시조각연결·자기교차형태·전체미관보장은아니다.
- 현재3.653758시Night만자동진행일시정지하여비교했고밝기·색·시각값은튜닝하지않았다. 종료후입력·Animator·Idle·Play·PostView366·시계자동true·기본OFF·자체리소스해제확인.44d13c0/406ce30과사용자Quality·Time·시계프리팹해시보존.
- 수정후전체81쌍은다시찍지않았다. 나머지5실패위상은저장입력선택검증만통과했고live가림·미관은미검증이다. 전체loop/다른clip·뷰·가닥/전역틈·시간품질/성능·build·외형채택미완료. 근거 `docs/artifacts/hair-boundary496/validation.json`, `Current472/Pairs496/`, 실제C#저장입력결과 `UNIT496_VERIFIED.json`. 전신발췌GIF Library `libfile_005c4e1134208191bc23b9d9a62ecb28`이다.

## 214. 29d2faf 후보 전체 검증 종료: 가시연결 미해결·미채택 `[CHARACTER-RENDER-01]`

- 제품수정없이495저장81입력을현재C#선택기에검사했다. 연결/끝점/결정성/삼각형지지/2x2검사통과,기존73정상선택불변,이전8복귀표본(고유7위상+closure)경로생성통과다. 오프라인은runtime가림통과가아니다.
- 현재29d2faf의실제Walk한루프81쌍을한번확보했다. 동일포즈·광원81/81,ready81,복귀/unsupported0,903source패킷중862GPU일치·41개는정확한더가까운표면복원.2개는CPU0.1mm허용값내의더가까운GPU깊이이며오류2건이아니다. 새전경고립위치/2x2두께/facing/main패킷누락/머리ROI밖native변경0. 원래UV0끝은81포즈모두기록hair에가려진다.
- 그러나위상0.6875(sample55)의raw선택(235,42)이emittedpacket에없고HEADmeta/finalalpha도0이다. 위아래(235,41)/(235,43)은각primitive85/94패킷을유지한다. 같은가닥중간이sourceCPU가림분기에서빠져가시경로가끊기고닫힌틈이바깥으로열린다. fallback없음과가시연결통과는같지않다.
- CPU버림612개중611은저장3renderer기하재검증으로대응되며같은sample55의1개가미설명이다. 재구성primitive89는가능한별도source점이지실제버린C#패킷이라고가정하지않는다. 실제선택primitive/bary/world/projected/depth와blocker가미기록이므로정당한가림인지원인은미확정. 이검증단위에서는새패치/epsilon/dilation/전체루프반복을하지않고미채택·OFF로닫는다.
- 현재루프0.9875→0의틈3→2는연결셀(233,39)이같은채기존중간선x234.01564→233.99215가row40선택234→233을바꾼것이다. 실제경계간격0.924733→0.907761cell,같은논리중심233.5는양포즈모두원래틈안이다. 원곡선지지·8연결·두께를유지하는234,40대안(면적0.2574/primitive75/가림없음/곡선오차0.42276vs0.39586)은기하상존재하나미렌더이므로동등품질/불가피tradeoff를단정하지않는다.
- 위상0.15/0.425/0.7125/0.7375등에서픽셀틈은대각점접촉형태로좁아진다. 실제투영모든메쉬사이에는양폭경로가남는것을0.047~0.360cell최소거리로확인했다. 4이웃포켓/8이웃외부통로를구별하며,16x/32x미소영역개수는주검수틈과동일한물리구멍수로쓰지않는다. 전체미관채택은통과아니다.
- 같은Editor실행79steady쌍의동기완료중앙값원본279.29ms/후보303.94ms,p95625.01/645.09ms이며플레이어FPS나예산판정이아니다. 현재7.98043346시를일시고정했고광원·색·시각값튜닝은없었다. 종료후입력·Animator·Idle·Play·PostView366·시계자동true·실험OFF/자체리소스해제와설정해시보존확인.
- 활성제품44d13c0(외곽선색보존)은양쪽에서유지되고기본OFF실험29d2faf와구분한다. 다음판정에는sample55실제버림패킷/가림소유자근거가필요하며알수없는버림을사용자미관선택으로넘기지않는다. 근거 `docs/artifacts/hair-boundary497/validation.json`, `Current472/Loop497/`. 새동일실행전신GIF Library `libfile_f53eade6d9fc819184ac6d3ba79b6bb0`,실패확대 `libfile_e4415886d748819184d405be9435effa`다. 전체프로젝트완료아니다.

- [497-COMPACT-DELIVERY] 기존 81프레임의 전신 전후/시간순서를 보존한 2배 정수 픽셀 복제 GIF: Library `libfile_fd176f83bfe481919d2585664eb53038`, 5,907,029 bytes. 추가 색 손실/보간/새 캡처 없음. 기존 대용량 GIF의 ChatGPT 첨부는 용량 제한으로 실패하여 미전달이며 재전송하지 않았다.


## 215. 실제 버림 소유권과 공통 광선·보이는 원본 패킷 선택 수정 `[CHARACTER-RENDER-01]`

- 497 Walk .6875 head(235,42)의 실제 첫 버림은 GPU 이전 CPU Visible이다. 선택 renderer2/submesh1/triangle90 UV(.40171847,.23728807), depth13.76588154를 triangle89 UV/깊이로 가렸다고 판정했다. 실제 기록과497변형정점/UV/투영은 정확히 같다. 반올림 화면XY와 월드깊이를 섞어123.29um 차이로 계산했지만 같은 월드 카메라 광선에서는36.78um으로 기존100um허용치 안이다.
- 같은 기본OFF Runtime1파일에서 공통double camera-space ray로 대체했다. 이 수정만으로 앞 .675셀을 잃는 회귀를 발견해 실패 기록을 보존했다. 이때90은 실제89뒤433.64um이며 원본edge587/588과UV연결이 확인된다. 한 패킷을 고른 뒤 버리던 순서를 원본 동일ribbon의 셀교차 후보 중 보이는 패킷을 선택하는 책임으로 합쳤다. 다른가닥/몸/정확한다른triangle가림과0.1mm허용치는 유지한다. 후단mask/epsilon상향/history/좌표·phase하드코딩은 없다.
- 기존 실패7위상+국소6입력 C#연결/끝점/결정성 통과. 최종 실제Walk .6625~.7125 5쌍은 같은pose/광원,ready5,unsupported0이다. 66source패킷/GPU가림6개는 정확한다른primitive·UV·더가까운depth확인,main누락/새고립/2x2두께/facing/머리ROI밖변화0이다. .675와.6875모두원본앞면유지, .6875triangle89 UV(.40169582,.23728818)/depth13.76588058와GPU/합성일치,alpha0→1이다.
- 동일실행원본vs수정후보 전신5프레임GIF Library `libfile_77645e41887481919e2813800894f452`,515847bytes. 공통480x272/native960x544,전신crop후정수2배NEAREST이다. 이전497은7.9804시,이번2.0952시로배경/색은동일조건아니다. 이전과세계정점최대0.477um/투영0.0000611cell오차가있으므로비트동일포즈라고칭하지않는다. 내부224,34는기존actor불투명상태에서정확한앞면owner로바뀌었으며실루엣추가가아니다.
- 국소원인수정만통과이며새선택규칙의전체loop/기존대각틈·3→2배열/다른시점·clip/성능·build는미검증이다. 기본OFF·미채택을유지하고44d13c0/29d2faf/사용자Quality·Time설정을보존했다. 임시trace제거,입력·Animator/Idle·Play·PostView366·자동시계/실험OFF·리소스해제복원확인. 근거 `docs/artifacts/hair-boundary498/validation.json`, `Current472/Event498/`, `Pairs498/`실패중간본, `Pairs498B/`최종국소본. 전체프로젝트완료가아니다.


## 216. de06622 전체 Walk 채택 검증: 가림 정합 통과·틈 폭 손실로 미채택 `[CHARACTER-RENDER-01]`

- 제품변경 없이 기존저장81위상 C#곡선선택/독립기하재평가를 먼저 통과했다. 저장입력에는 localTransform계산전 정점이 없어 독립기하검사는 비트동일privateSelect/GPU검증으로 칭하지 않는다. 이후 현재후보 실제Walk한루프81쌍을 한 번 확보했다. 동일포즈/광원81/81,ready81,fallback/unsupported0이다.
- 원본1097패킷의 UV/world/GPU일치, GPU가림136개는 정확한다른머리primitive/UV/더가까운depth로 설명됐다. 7개는 기존CPU0.1mm허용치 안이며 오류7개가 아니다. 방출패킷 공통광선가림충돌/main누락/새고립위치/2x2두께/facing/머리ROI밖쓰기0이다. 최초.675/.6875셀도 보인다. closure세계정점최대0.954um/투영0.0000802cell이다.
- 경로중간빈셀10개를 오류수로세지않았다. 실제3renderer삼각형과depth평면의 해석적polygon차집합으로 셀안원본표면전체가 다른머리submesh0의정확한삼각형들에가려짐을 증명했다. 최대남은면적비4.44e-12이며, 별도5기본도형검사도통과했다. 이는기하증명이며 privateCPU분기로그라고칭하지않는다.
- 남은틈은미검증으로넘기지않는다. 실제final24위상에서 원형상양의폭통로가 대각점접촉통로로바뀐다. 대표기하선과전체3mesh의최소거리0.0473/0.3602/0.2497/0.2077cell, pixel4연결끊김/pixel8연결유지다. 완전틈폐쇄나24개별버그가아니며 요청된틈폭보존에는미달하는표현손실이다.
- .9875→0경계의물리틈0.924735→0.907754cell인데 pixel빈영역3→2다. join233,39는그대로이며 중심선floor가234,40→233,40으로움직인다. triangle75지원/UV/공통광선가림없음/8연결/2x2없음의234,40기하대안은빈영역3/곡선오차0.42278vs0.39583으로가능하지만 미렌더대안이다. 필수디자인tradeoff나채택해법으로단정하지않는다. 현재후보는틈폭손실로미채택·기본OFF이며 새패치루프를시작하지않았다.
- 같은실행전신81프레임GIF Library `libfile_185dfd7012808191ab6ac1f90bcfe63c`,4332893bytes,12native픽셀여백/정수2배NEAREST다. 256색팔레트양자화정보와원본PNG를보존했다. 틈확대 `libfile_712f379861b08191ba48672b32965791`. 현재19.934536시만자동진행임시정지했으며밝기조절없다. 이전시간의배경과동일조건이라칭하지않는다.
- 입력/Animator·Idle·Play/PostView366/자동시계·실험OFF/리소스해제복원,Console기존진단오류1개변함없음. de06622/44d13c0/사용자Quality·Time설정보존. Editor진단중앙값원본270.46ms/후보392.93ms이며playerFPS·성능준비완료는아니다. 근거 `docs/artifacts/hair-boundary499/validation.json`, `Current472/Loop499/`. 다른clip/시점/크기/build및전체프로젝트완료는미검증이다.

## 217. 닫힌 머리 영역502 구현·전체 Walk 검증과 미채택 [CHARACTER-RENDER-01]

- 최신 정정: 모든 가닥 연결과 미세 틈의 양의 폭 보존은 사용자 요구가 아니었다. §216의 그 조건에 따른 채택 판정은 현재 목표의 기준으로 사용하지 않는다.491은118삼각형 열린 중심선 교체였으며, 전체 닫힌 경계의 권위가 아니었음을501에서 확인했다.
- 기본OFF 대안502는 현재 변형된 머리카락 전체 투영의 합집합을1/8셀 경계로 추출하고,0.1875셀 RDP 허용치의 닫힌 구간선형 곡선으로 근사한다. signed curve/cell 교차면적 A로 영역 손실을 계산하고, 영역 손실+0.14×8이웃 경계 길이를 s/t cut으로 공동 선택한다. 직교/대각 가중치는.58578644/.29289322이다. 최종 선택 셀의 닫힌 경계가 채움 권위이며, 보존된 기존 얼굴/눈 영역과 합쳐 공통480×272 부모 영역을 만든다. Bézier/spline·색 덩어리 설계·계단 run 리듬·시간축 대응을 구현했다고 주장하지 않는다.
- 선택 셀마다 원본 submesh/triangle·barycentric·UV·world·depth·normal/tangent 패킷을 전달한다. 최근접 donor는1.1셀 이내이며 원본 coverage 밖 이동은 명시된 전송이다. Raw/Native/World/독립레이어/Legacy의 머리 원본 draw를 같은 셀 소스로 대체하고, 눈은 같은 머리 레이어로 가림을 판단한다. Prepare/눈 후/최종 소유권이 같은 부모/머리 영역을 강제한다. 기존491을 직렬로 덧씌우지 않는다.
- C#·셰이더5개 및 작은 이진 선택 전수검사5사례 통과. 실제502B 포즈의 Raw/Native/레이어/Prepare/최종 경계 밖0,524셀 패킷 불일치0이다. Native2표본 좌표 차이는 공통 셀/Native2×2 블록의 phase 정합으로 수정했다.
- 실제 Walk16쌍 뒤 같은 후보의 한 루프81쌍(1.0000025→2.0000062)을 같은 실행 원본과 비교했다. 모든 쌍 pose/light 일치, Raw/머리레이어/최종 경계 밖0,패킷 불일치0,unsupported0이다. head mask loop seam 차이0이다. 실제 PNG와 대조한 가시 머리 고립셀 표본은 원본18/후보0이다. 이것을 전체 픽셀 튐 해결로 승격하지 않는다.
- 실제 출력의 한 프레임 경계 선택 변화49표본을 찾았다(49독립 오류 아님). 대표 head-local(218,52),.0125/.0250/.0375에서 원본 피부 유지 대비 후보 피부→머리→피부이고 RGB252,230,210→16,10,19→252,231,210이다. 첫 발생은 선택 영역 자체이며 후단 경계 누출이 아니다. 독립 프레임의 곡선/면적/경계길이 선택에는 시간 일관성·작가 계단 리듬 목적이 없다. 현재502는 이 실제 출몰 잔여로 미채택·OFF다.
- 몸 색차11표본 중2개는 바깥선 가림,8개는 노출이며 저장coverage의4연결 외부 flood와 기존0.55색단계가 일치했다. 나머지.7500은 시간순 검토로 판정을 정정했다:.7375 원본/후보 내부선ON,.7500 원본만OFF,.7625 둘다머리가림이다. 후보가 순간 선을 새로 만든 회귀라는 단일쌍 판정과 몸 중심 표본 불일치 설명은 철회했다.503 두께 대안은4실제프레임에서 출력차0이어서 자산/meta/연결까지 제거했다. 공유OwnerLines333은 변경하지 않았다.
- 동일primitive·2셀 내부 머리색의0.10초과 변화 locator에는 표본0이었다. 광원/그림자 물리 입력을 프레임별로 저장하지 않았고 UV도 변하므로, 이를 전신 명암·색영역 설계나 미관 통과로 쓰지 않는다. 다른clip/각도,정면눈,접지,성능목표/build는 미검증이다. Editor영역생성136.9~279.9ms는 production 성능이 아니다.
- 503 정리 뒤 Play/입력/Animator Idle speed1/자동시계/captureDelta0/원래PostView366훅1개/실험OFF를 직접 확인했다.44d13c0와 사용자Quality·Time설정 해시를 보존했다. 현재 활성 제품 수정과 기본OFF 실험을 구분한다.
- 로컬 전신 GIF: 일반속도40프레임1330ms 1189876bytes,전체81프레임 느린검수2630245bytes. 공간보간 없이 기존 실제 캡처에서 생성했으며 원본PNG/버퍼를 보존했다. 같은 쌍 안에서 광원이 일치하며 서로 다른 실행시각의 배경을 같은 조건이라고 하지 않는다. Library403은 재시도/우회하지 않았다.
- 근거: docs/artifacts/hair-region502/validation.json 및 README.md, Current472/Loop502/·Pairs503/·FINAL_REPORT502.json. 경계 강제 통과와 선택 안정성 실패는 별개이며 전체 프로젝트/픽셀아트 제작 완료가 아니다.


## 218. 머리 영역 면적 입력504 단일 수정·실제 인접 Walk 검증, 출몰 잔여 OFF [CHARACTER-RENDER-01]

- §217 체크포인트60191b59 이후 HeadRegion502.cs의 면적 입력만 바꿨다. RDP 근사선의 signed cell 면적 대신 원래 닫힌1/8셀 추출영역의64등분 면적 합을 사용한다. 이는 추출 polygon의 정확한 적분이며 연속 mesh의 정확 면적은 아니다. RDP는 진단용이고 최종 권위 경계는 공동 선택 후 SelectedLoops이다. s/t cut의 면적손실+.14×8이웃 경계길이, 가중치, donor/depth/UV/색/눈/가림/시간은 유지했다. 중심샘플 출력이나 임계값 복사·history 필터가 아니다.
- 기존81입력에서 이전 선택 재현 불일치0. 전체마스크 한 프레임 반전 관측128→11은 기존 최종 가시49표본과 다른 측정이며 오류수가 아니다.49표본의 새 선택은 안정 생략32/안정 채움8/전환 이동8/기존010유지1이다.
- 실제5쌍에서 .0250 피부→머리→피부가 제거됐다. 추가33쌍은8개 인접 구간이며 전체runtime loop가 아니다.38쌍 모두 같은 실행 pose/light 일치, 예측마스크 일치, Raw/머리/최종 경계 밖0·패킷 불일치0·unsupported0이다. 안정 채움8중6개는 실제 인접 형태를 검토했고47/64는 저장입력만 확인했다. target79의 현재 원본 coverage는 과거502와1셀 다르므로 과거 원본을 현재 동일 색/광원 대조로 쓰지 않았다.
- 몸 색 차이5표본은 각각 동일 owner/meta/primitive/UV, 외부 flood/기존 두께 조건, RGB .55배를 확인해 외곽 밴드 노출로 분류했다. 새 내부선5건이라고 세지 않으며 전체 명암 품질 통과도 아니다.
- 남은 대상 반전9관측은8시간사건이다.7사건8관측에는1/8추출 면적 오차 기여가 있다. 대표 .2625/.2750/.2875 head(220,57)의 실제 변형 삼각형 union면적 .306404/.310049/.313548은 증가하는데 추출면적 .296875/.343750/.265625가 반전해 최종 body8/hair14/body8이 된다. 같은 삼각형 경계 edge IDs와 mask 최초 선택을 확인했으므로 정상 가림으로 처리하지 않았다. .6625는 추출면적 plateau와 이웃 변경이 함께 있다.
- (224,58),.8625/.8750/.8875는 면적 두 추정 모두 감소하지만 이웃 경계비용 기여가+.0820101→−.1640202로 바뀐다. 조건부 선택 역전 경로는 확인됐으나 동등한 형태 품질의 전역 대안은 미확인이다. exact local 면적 대조는 이웃을 고정한 진단이며 exact-area 전역 해법 검증이 아니다. 추가 패치/새 전체 캡처는 하지 않았다. 경계 강제 통과와 시간 선택 실패를 분리해 기본OFF·미채택을 유지한다.
- Play/입력/Animator Idle speed1/자동시계/captureDelta0/PostView366 단일훅/두실험OFF/비컴파일을 직접 읽어 복원 확인했다.44d13c0와 사용자 Quality/Time 설정은 보존했다.5쌍 및33쌍 전신 전후GIF는 로컬 보존,33쌍은8구간 시간 점프를 표시한80ms 느린 검수이며 공간 보간/축소가 없다. Library403은 재시도하지 않았다.
- 근거: docs/artifacts/hair-area504/README.md·validation.json·두진단PNG 및 Current472/Groups504/GROUP_REVIEW504.json·CLASSIFICATION504.json. 실제 전체504 Walk/타clip·각도/눈 정면/접지/색덩어리 설계/시간일관성/성능/build와 전체 프로젝트 완료는 주장하지 않는다.


## 219. 가시 머리 영역 교차면적505 정확도 대조·실제22쌍, 실시간 미채택 [CHARACTER-RENDER-01]

- ecde055 이후 확인된1/8면적추출 오차의 입력만 대체하는 기본OFF 진단 경로를 추가했다. HeadRegion502.Enabled와 UseVisibleArea505가 모두 켜진 검수에서만 사용한다. 원본 변형 삼각형을480×272 셀로 자르고, 앞쪽 non-hair의 cull/alpha/depth 영역을 빼고 합집합 면적을 적분한다. 겹친 hair는 한 번만 세며 동일 깊이는 마지막 hair draw가 이긴다. 같은.14 비용/이웃 가중치/선택기/UV·depth donor/색/눈/시간 처리를 유지했다. RDP·8x source loop는 진단용이며 최종 권위는 기존 선택 셀 경계이다.
- 최초 차집합은 반쪽 가림 fixture에서.875(정답.5)로 실패했다. clip 경계에 중복된 꼭짓점이 생겨 길이0 제거 변이 원영역을 다시 추가하는 것이 원인이었다. 중복 endpoint/길이0 변을 제거한 뒤 독립8fixture가 통과했다. 수정 전Bilinear81 가시영역 결과는 최종 근거에서 제외한다. 압축 texture 직접 readback의 플랫폼 오류도 기존 성공한 임시linearRT copy/readback으로 교체했다. 별도 비용실험 helper82242는 결과 없이 자기 세션 중단(exit1)으로 종료했고 제품에 넣지 않았다. Unity/다른 프로세스는 종료하지 않았다.
- 현재 원재질은 mip1/bilinear-repeat/UV변환identity/UV애니0/alpha factor1이다. UV 다각형 전체의 alpha texel 범위로 가림 상하한을 보존하고 두 면적 입력의 cut이 다르면 미확정 실패로 남긴다. 수정된 저장81입력에서 하한/상한 선택 불일치0.499 저장기하와 현재33포즈 사이 최대.00013733셀 차이가 있으므로 bit동일 원본이라 하지 않는다. 저장 전체마스크 한프레임 관측2는17(217,55),23(219,51)이며 가시 결함으로 확정한 오류수가 아니다.
- 실제 Walk22쌍/7인접구간에서504/505를 같은pose/light로 비교했고 양쪽 예측마스크 불일치0이다. Raw/머리/최종/Native 경계 밖0·packet primitive 불일치0·몸 색 차이0·동일UV/primitive 가시피부 색 차이0·unsupported0. Native packet depth 최대차1.90735e-6. 변형 머리기하 SHA는22개 모두 달라 정지 캐시로 통과시킨 것이 아니다.
- 대상7시간사건(8관측)의 불필요한 되돌림이 제거됐다. .8750/.9375는 한방향 이동으로 남겨 픽셀변화0을 목표로 하지 않았다. 별도 이웃비용 사건(224,58)은 입력의 간접영향으로111이 되었지만 일반 원인/디자인을 해결했다고 판정하지 않는다. 현재 게임각도에서 눈 feature role들은0셀이고 피부만 노출되어 정면 눈 회귀는 미검증이다. 원본 눈/비율/texture/카메라를 변경하지 않았다. 과거 run의 밝기와 일치한다고 하지 않으며 현재 쌍의 광원만 일치한다.
- 실시간 채택불가: 실제22쌍 면적계산 중앙값4247ms, 렌더호출504469ms/5055048ms. 이는 capture readback 제외 Editor 호출시간이지 playerFPS가 아니다. 같은 core의 별도1포즈 계수는 bin배정51374, front가림후보136803, clip2355912, union변쌍21710000. offline union1453.5ms/계산1688.9ms(~86%)이고 계측 전후 면적차0. per-frame 삼각형·bin·polygon·fragment·edge/level·interval list 할당은 존재하나 할당 byte는 미측정이다.
- 최소 개선 제안만 남겼다: Union event의 정확 중복 선분 제거 및 XY bbox 비교로 교차 불가능한 변쌍을 제외하고 원polygon 적분은 유지한다. 실제 교차가 없는 후보만 제거하므로 정확도 계약을 유지할 수 있으나 속도향상은 아직 측정하지 않았다. 같은 프레임의 기하 투영·불변 topology/material 재사용도 가능하지만 애니메이션의 변형정점/depth/bin은 매번 갱신해야 한다. 새 최적화 구현/전체 촬영/기본활성화는 하지 않았다.
- Play/입력/Animator Idle speed1/시계자동/captureDelta0/PostView366 단일훅/491·502·505 모두OFF/비컴파일을 직접 읽어 복원 확인했다.44d13c0/ecde055와 사용자 Quality/Time 해시를 보존했다.22쌍 전신GIF는7구간 점프를 표시한80ms 느린 검수이며 공간 보간/축소가 없고 로컬701898bytes이다. Library403은 재시도/우회하지 않았다.
- 근거: docs/artifacts/hair-area505/README.md·validation.json·ACTUAL_EVENT_COMPARISON505.png, Current472/Walk505/·Area505/Corrected81/·RESTORED505.json. 정확도 정답 대조용OFF 코드와 실시간 제품은 구별한다. 전체 runtime loop·타clip/각도·일반 시간일관성/계단·명암 덩어리 설계·접지·build 및 전체 프로젝트 완료는 미검증이다.


## 220.505 합집합 변쌍 후보제한506 동등성·비용 검증, 기본OFF [CHARACTER-RENDER-01]

-42cb52b의505 Union 본문을 Union505Reference로 그대로 보존하고 기본false인 UseSpatialCandidates506 대안만 추가했다. y최솟값으로 변 인덱스를 정렬해 y구간이 겹치지 않는 이후후보를 중단하고, x구간이 분리된 변쌍을 식 계산 전에 제외한다. 살아남은 쌍은 원래 인덱스순 산술/수치guard를 유지한다. 다각형/꼭짓점/면적적분/가림/alpha상하한/비용함수/UV·depth/눈/시간은 바꾸지 않았다. bbox는 교차후보 거절에만 쓰고 영역경계가 아니다.
- 저장81기하를 매번 읽어 reference/optimized 순서를 교차 실행했다. 면적 float비트차0·최대면적차0·상하한 cut마스크차0. clip/가림연산수와 원래 잠재변쌍수도 동일하다. 변형기하 fingerprint81개가 모두 다르며 정지캐시/표본근사를 사용하지 않는다. 기존8fixture는 두 모드 모두 통과했고 분리Y/코너접촉/수직접촉/역방향중복4경계fixture도 통과했다.
- offline CoreCLR 중앙값: 계산1120.887→1040.553ms, Union931.121→844.293ms, 변쌍 식계산21368608→3105395. 전체쌍 합계 기준 변쌍84.14% 감소이나 시간은8.09% 감소이고 paired중앙가속1.082배이다. y겹침 순회중앙값7117463과 실제변쌍식3105395를 구별한다. 관리할당 중앙값741.740→742.551MB, 평균814400bytes/pose 증가. 이는 Compute현재thread의 누적할당이지 peak/retainedRAM/GPU메모리가 아니다.
- 오프라인 통과 후 실제인접Walk3쌍(.2625/.2750/.2875)만 비교했다. pose/light·mask·예측·PNG동일, Raw/머리/최종/Native 경계밖0·packet불일치0·몸색차0. 변형기하hash3개가 달라 애니메이션정지로 비용을 숨기지 않았다. 새 전체loop 촬영은 하지 않았다.
- 실제3쌍 area중앙값5054173.997ms/5064217.987ms, 렌더호출4939.365/4929.321ms이다. Editor에서 실제속도개선이 확인됐다고 하지 않으며 실시간채택불가·OFF를 유지한다. renderer호출은 capture readback 제외이고 playerFPS/runtime메모리 측정이 아니다.
- 마지막포즈에서 RawUV53값 max1.49e-8(최대7ULP), preparedUV53값, 최종RGB387값 max3.73e-9(최대2ULP) 차이가 있다. 최초관측은 hair role12/13/14 RawUV이고 mask/owner/primitive/depth/Native/독립hairUV·8bit PNG는 같다. 원인은 분리하지 않았으며 GPU float버퍼전체 bit동일이라 하지 않는다. 이를 감추는 보정은 추가하지 않았다.
- 남은비용1포즈계측: 후보계산1018.3ms 중 Length667.9ms/221498회(~65.6%, Union의~81.9%). 각적분구간마다 polygonedge 순회·span할당/정렬/merge가 남고 호출수는 그대로다. clip/차집합·대량할당도 미개선이다. 이 단계계측에는 JIT/계측영향이 있어 기준대비가속으로 쓰지 않는다. 두번째 최적화는 구현하지 않았다. 이웃비용사건/시간설계/눈검수/기존505잔여는 미해결 유지한다.
- Play/입력/Animator Idle speed1/자동시계/captureDelta0/PostView366한훅/491·502·505·506OFF/비컴파일을 직접 확인했고 진단cache를 해제했다.44d13c0·42cb52b·사용자Quality/Time해시를 보존한다.3쌍 전신GIF는 로컬64557bytes,80ms느린발췌반복·공간보간없음. Library403 재시도/우회 없음.
- 근거: docs/artifacts/hair-pairs506/README.md·validation.json·paired81.csv, Current472/Area506/·Walk506/·FINAL_RESTORED506.json. 이번 단위는 정확도보존 후보제한 검증이며 실시간제품/전신시간품질/전체프로젝트 완료가 아니다.

- 최신 판정: 실제속도개선 미확인·관리할당 증가로506을 미채택했다. 후보 diff만 docs/artifacts/hair-pairs506/REJECTED_CANDIDATE506.diff로 격리하고 runtime HeadArea505.cs를42cb52b의 SHA c24b4e664bd713b35ba4107707c587adc0575b54c159a459d82b3fe736746dd7로 정확히 복원했다. 2171만 변쌍을 주시간비용이라고 한 추정은 철회하고 별도 실제시간분해 단위로 확인한다. 이 체크포인트에는 새 최적화를 포함하지 않는다.


## 221.505 면적단독15회 실제시간 분해507, 변쌍주병목 판정 정정 [CHARACTER-RENDER-01]

-790e724로506을 비컴파일diff에 격리하고 runtime505를 SHA c24b4e664bd713b35ba4107707c587adc0575b54c159a459d82b3fe736746dd7로 복원했다. 새최적화/렌더패치/촬영은 없다. explicit-start Editor전용 관찰코드로 Unity Mono6.13에서 저장 Loop499/022 포즈를 원본/원본+GCrecorder/동등구간계측+GCrecorder 각5회, 순서회전하여15회 측정했다. 두워밍업을 제외했고15회 면적비트차0. renderer호출·투영/build·입력load(별도386.946ms)는 Compute 시간 밖이다.
- A원본 중앙4403.167ms(4033.523~4509.123), B원본+GC4788.396ms, C계측본+GC4627.959ms. 서로 다른 호출의 중앙값을 빼지 않는다. repeat별 B-A 중앙385.229ms, C-B114.054ms(-353.162~438.846), C-A450.178ms/10.89%(112.082~814.970)이다. 계측+heap/scheduling/JIT 변동이 섞이며 원시구간시간에서 임의차감하지 않았다. 타이머쌍970859회의 빈 Begin/End 보정추정은45.949ms이며 공통창GCrecorder 자체비용은 따로 측정하지 않았다.
- C의 inclusive구간중앙: SpanBuild2185.539ms/221498회, SpanSort352.996/221498, SpanMerge105.355/221498, PairIntersections549.182/1232, EventSort80.879/1232, EdgeBuild37.332/1232, Occlusion1196.215/28921(내부 OverlapClip201.723/136803, AlphaBounds50.105/50214, Subtract876.444/49773), CellClip76.704/34493, Binning2.668/1. 부모/자식 시간을 합산하지 않는다. 별도exclusive잔여를 계산해 각 호출전체와 합계 일치를 확인했다. 무계측 전체에 대한 정확귀속시간으로 바꾸어 부르지 않는다.
- 2171만 변쌍이라는 횟수만으로 주시간비용이라고 했던 설명을 철회한다. 계측5회 모두 스팬 구축이 변쌍 계산보다 훨씬 크고, 가림의 fragment 차집합도 크다. Length가 매적분구간에서 모든 polygon/edge를 다시 훑어 span을 만들고 할당·정렬·merge하는 반복구조와, cell/hairtriangle/nonhaircandidate마다 clip/alpha/fragment분할하는 가림구조를 코드·호출수로 연결했다.
- Mono관리할당API는 모든호출0을 반환해 측정불가로 유지한다. 과거CoreCLR byte를 Unity값으로 재사용하지 않는다. GC.MaxGeneration0이므로 동일하게 찍힌 gen0/1/2 count를 합치지 않는다. 기록된10호출 GC.Alloc 마커 중앙165.793ms/6494915events, GC.Collect78.827ms/8events, Compute내 incremental0events. 마커시간은 단계와 서로 겹칠 수 있고 고유 allocator시간이라고 단정하지 않는다. 전체관찰창 GC.Collect1562.520ms에는 A호출과 프레임사이 Editor작업도 포함돼 deferredGC를 정확히 분리했다고 하지 않는다.
- 미구현 동등후보 경로: 현재 Union의 같은 y구간에 활성인 polygon만 원래순서로 유지해 원edge식/중점/정렬·merge를 보존한다. 가림은 orthographic affine D=z_hair-z_occluder의 실제겹침을포함하는 사각형 최대상한을4꼭짓점에서 보수적으로 구해 확실히음수인 후보만 조기제외할 수 있다. 부동소수rounding보장 필요, 불확실/동일깊이는 원505처리 유지, role만으로 표면합침/임의epsilon/표본근사는 금지한다. 이 경로는 제안뿐이며 새구현/추가측정을 시작하지 않았다.
- COMPLETED는 콜백해제/CSVclose/scoped·windowrecorder dispose후에만 기록된다. Profiler.enabled 전후false 및 직접readbackfalse, Play/입력/Animator Idle speed1/자동시계/captureDelta0/PostView366단일훅/모든렌더실험OFF/비컴파일을 확인했다. 진단cache를 해제했고 user설정·44d13c0·505helper를 보존했다.
- 근거: docs/artifacts/area-time507/README.md·validation.json·measurements.csv·STAGE_TABLE507.md, Current472/Profile507/Run01/ 및 FINAL_RESTORED507.json. Editor/Profile507 관찰기만 추가했고 player/runtime경로에는 연결하지 않았다. 시간실측과 연산횟수·환경·계측오버헤드를 구별한다. 실시간채택/눈/이웃비용/시간설계/전체프로젝트 완료는 여전히 미해결이다.

## 222. CHARACTER-RENDER-01 — Union→Length 활성 y구간508 단일 최적화, 기본OFF

- 요청:507에서 실측된 반복 스팬 구축에 한정해 현재 y구간 활성 다각형만 원래 순서로 유지한다. 가림 최적화·비용함수·시간 필터는 함께 변경하지 않는다. 기준505 Union 본문·정확 원본 SHA c24b4e…를 보존하고 `UseActivePolygons508` 기본false 분기만 추가했다.
- 연산:현재Union의 기존 변 순회 중 minY/maxY를 모으고, 기존 모든 변쌍 교점·정점event·sort·midpoint를 그대로 유지한다. midpoint y에서 maxY<=y를 제거하고 minY<=y<maxY를 원래 index순 active목록에 넣는다. Length508은 원래 교점/스팬추가/sort/merge/적분 연산을 유지한다. 영역 밖 다각형은 원래 half-open 교차predicate로도 crossing이 없다는 필요조건만 쓴다. 매포즈 현재 clipped polygon에서 재구성하며 정지 애니cache/표본근사/깊이수정이 아니다.
- 오프라인8개 endpoint/tie/empty/degenerate fixture doublebit동등, 저장81포즈 양면적floatbit/ambiguity차0. Unity 기존SelectRegions로81쌍 상하한mask차0. 비계측 전체Compute 짝순서 교대; .NET81쌍 mean1207.351→1047.482ms,78/81빨라짐,짝절약률중앙13.49%;같은22포즈추가5쌍 모두빨라짐,짝절약132.334ms/12.41%중앙.
- 실제Unity Mono비계측 같은22포즈5쌍 모두빨라짐,각 mode중앙4519.908→3278.350ms,짝절약중앙1538.343ms/33.97%,범위763.439~1806.212ms. 로딩/비교/저장은밖, 단계timer/counter/recorder/강제GC없음. 여전히약3.3초Compute이므로실시간채택불가. .NET관리할당API1MiB sentinel통과;81쌍평균754039739→755976948byte(약1937208byte/0.257%증가). Mono sentinel0이므로관리할당byte는측정불가,live/reservedheap관측은할당/peak/Compute고유메모리로해석하지않음.
- 실제연속Walk3쌍(.2625/.2750/.2875),변형기하3개서로다름,포즈·광원같음. mask/예측/최종PNG차0,owner/primitive/depth/Native정합·경계밖·packet회귀0. GPUfloat전체bit동등은아님:첫포즈finalRGB346값max2.98e-8/2ULP,preparedUV55/rawUV56값max1.49e-8/최대19ULP;마지막포즈UV각4값최대3ULP차. 원인미분리로기록하고보정/정규화하지않음. 이3쌍은짧은동등성검사이며새전체loop/아트·시간품질검증이아님.
- 전신GIF Current472/Walk508/WALK508_FULLBODY_BEFORE_AFTER.gif 70064byte,동일실행원본505vs508/3프레임순서/공통palette/공간보간없음;원본960×544PNG·float보존. Library403재시도없음. 측정/캡처콜백제거·CSV닫힘,직접readback Playtrue/unpaused/inputtrue/AnimatorIdle speed1 Loc0/capture0/자동시계/PostView366한훅/모든실험OFF/Profilerfalse/컴파일끝. Console과거16건그대로새delta0. 사용자Quality·Time해시/44d13c0보존.
- 근거:docs/artifacts/area-active508/README.md·validation.json·paired81.csv·UnityPairs.csv·PairArea508.cs,Current472/Area508/OFFLINE508.json·UNITY508.json·SELECTION508.json,Walk508/ACTUAL_REVIEW508.json·FLOAT_DIFFERENCES508.json,FINAL_RESTORED508.json. 실측시간개선의기본OFF후보만보존하며영역선택/픽셀튐/이웃비용/눈·각도/전체프로젝트해결로확대하지않는다. 506미채택과507변쌍주병목주장철회는유지한다.

## 223. CHARACTER-RENDER-01 — 가림후보 certificate509 동등성통과·시간개선미입증·철회

- 먼저508 기본OFF 비용개선·81입력/실제3쌍 검증을909e324로기록했다. 이후509는508활성기준에만추가하는단일가림후보제한으로검증했다. 실제cell-clipped hair polygon에원래3회Overlap clip의binary64 보간오차를포함한box를만들고,원래와같은rounded depth-plane차의outward상한이엄격히음수인경우만배제했다. 불확실/동률/unsafe수치범위는기존계산,role를표면동일성으로사용하지않음. alpha/비용함수/근사정확도/시간/눈변경없음. BOUND_PROOF509.md에64uM좌표오차한계유도와빈depthClip등가를기록했다.
- 6개기하/가림/alpha fixture와6개certificate/fallback검사통과,저장81입력의상하한area floatbit·ambiguity차0,Unity SelectRegions 양bound mask차0. 비계측Compute교대짝비교: .NET81 mean935.942→928.657ms,42/81빠름,짝절약중앙1.807ms/0.175%;같은22추가5쌍3/5빠름,짝절약중앙33.859ms. Unity같은22 5쌍은2/5빠름,mode별중앙3247.251→3374.203ms,짝절약중앙-355.896ms/범위-406.670~518.311ms. 매짝첫호출이더빠른순서패턴이관측되어고유11.79%회귀로단정하지않고,시간개선미입증으로비채택했다. 추가benchmark/튜닝/실제Walk촬영은하지않음.
- .NET관리할당sentinel통과;81평균755976942→746577344byte,약9399598byte/1.24%감소. Mono sentinel0은측정불가,live/reservedheap은할당/peak/Compute고유메모리로해석안함. 관리할당감소로실시간속도성공을대체하지않음. recorder/단계타이머/counter/강제GC없음,측정콜백10회완료후제거/CSVclose/후보OFF.
-509 Runtime추가분과이번Editor observer/자동meta만해시보호하에제거했다. Runtime/HeadArea505.cs는909e324의508과byte동일 SHA2aeca448…로복원했고,시험509코드는docs/artifacts/occlusion509의diff/standalone비교로만격리했다. Play/입력/AnimatorIdle speed1 Loc0/자동시계/capture0/PostView366한훅/실험OFF/Profilerfalse/컴파일종료를확인한다. 사용자Quality·Time/44d13c0보존,기본OFF. 새509애니동등성은미실행이며508GIF70064byte보존/Library403재시도없음.
- 잔여:508도약3.3초Compute/약4초renderer로실시간불가. 매포즈·셀별trianglefragment/가림/양면적union반복표현이남아있다. 507의변쌍주병목주장철회유지;509는새지배구간을계측한것이아니다. 미세후보필터반복대신가시닫힌영역/경계를포즈별한번구성하고경계셀교차와내외부인증으로소비하는canonical representation의비용구조검토가필요하다. 정확도oracle505/owner·가림·상하한계약을유지하는검토이며새설계구현·속도보장·정지cache를승인한것은아니다.
- 근거:docs/artifacts/occlusion509/README.md·validation.json·paired81.csv·UnityPairs.csv·PairArea509.cs·BOUND_PROOF509.md·REJECTED_CANDIDATE509.diff,Current472/Area509/OFFLINE509.json·UNITY509.json·SELECTION509.json,REJECTED509.json및FINAL_RESTORED509_REJECTED.json. 현재활성348과기본OFF508,509철회를분리하며전신표현/시간품질/이웃비용/눈·타각도/전체프로젝트완료를주장하지않는다.

## 224. CHARACTER-RENDER-01 — 곡선 영역 런타임 표현 검토510, 구현 없음

- 509 철회·운영 복원·비채택 기록을95a1382로 먼저 마무리한 뒤 코드 추가 없이 검토했다. 508은909e324의 기본OFF 후보로 보존한다. 정확면적505/508은 물리/원본 대조용이며 모든 메쉬 세부와 픽셀 마스크를 그대로 복제하는 것이 디자인 목표는 아니다.
- 현재 `HeadRegion502.Curves`는 RDP 진단값이고 실제 선택 입력은505 원본 가시 면적이다. 저작된 머리 전체 제어망·지속 제어점 ID는 없다. 실제 저장3포즈에서 source ring20/17/13,point1868/1902/1926을 확인했다. 이는 표현 재구성의 근거이며 오류 수로 세지 않는다.
- 최소 경로 하나: 지속 ID를 가진 저작 닫힌 Bézier 영역과 실제 primitive/barycentric/본 anchor를 준비하고, 현재 변형/투영에서 곡선을 갱신해 영역을 선택한다. Designed 분기는 현재 `Prepare`의 무조건적인 전체 `Union` 및 `HeadArea505.Build`를 앞에서 우회한다. 정적 triangle/UV/topology 색인과 포즈별 bounds refit/가림 질의로 `Select`의 셀별 전체 삼각형 검색도 분리해야 한다. 현재 BVH와 저작 곡선 자산은 없고 필요한 새 구조로 명시했다.
- `CellAreas`의 signed ring/clip/area, `SelectRegions`의 초기 비용/동률, `Packet/Bary/AddQuad/Piece`, 기존 Raw/Native/레이어/눈/최종 공통 mask/Gate 권위를 재사용한다. 498의 같은 camera ray 깊이 비교·가시 후보 순위를 보존하며 role를 같은 surface로 보지 않는다. 연속 C와 선택된 닫힌 셀 경계 C_Q를 구분하고 C_Q 밖 침범은0이어야 한다. 원본 alpha 재clip, ROI/hull, 잔가닥/틈 전부 보존, 정지 cache, history/RGB 필터는 대안이 아니다.
- 비용 근거는507/508/509의 측정 scope를 구별했다. 508도 약3.3초 Compute/약4초 renderer이며509는 이득 미입증이다. 새 표현의 수ms/FPS나 기존 BakeMesh/잔여 단계의 새 주병목은 측정하지 않았다. 초단위 구조를 미세 후보 제한 반복으로 해결한다고 가정하지 않는다.
- 픽셀 덩어리·생략/통합·의미있는끝·계단 리듬은 Saint11 원저자 지침과 연결했다. 현 최소 선택기는 시간/계단 리듬 목적함수가 아니므로 .8750 이웃비용 사건 자동 해결을 주장하지 않는다. 같은 설계 품질의 공동 배치/에너지를 별도 판별하며 비용함수를 동시에 바꾸지 않는다. 실제 최소 검증 구간과 numerical/owner/가림/디자인/시간/비용 검증 계약을 REVIEW.md에 정했다. 새 구현·촬영·패키지·Library403 재시도 없음; 기본OFF·사용자 설정·운영 복원 증거 유지.
- 근거: docs/artifacts/region-runtime510/REVIEW.md 및 PROVENANCE.json. 검토만 완료했으며 곡선 자산 저작·구현·실제 성능/아트/애니 통과는 미검증이다.

## 225. CHARACTER-RENDER-01 — 자동 선분곡선511 실제 Walk16쌍, 기본OFF·미채택

- 최신 사용자 요구에 따라510의 수동 곡선 저작 전제를 대체했다. 기존 Hair/Face/Eye semantic adapter를 입력으로 exact rational 투영 arrangement/positive winding, area-perimeter 영역tree, 한 번의 RDP0.1875cell 및 일반 topology repair로 지속 triangle/barycentric anchor를 자동 구성한다. 9링532점 중 미세hole6개를0.14perimeter 대비 면적비용으로 채워 outer1+hole2의3폐곡선94제어점이 됐다(3수선/4점추가). 수동 좌표/선택가닥/primitive range/phase 조건은 compiler에 없다. Bezier·의도된끝 인식·임의 새모델/시점 통과라고 주장하지 않는다. 주변 기존 renderer/style adapter의 모델종속성은 남는다.
- 매포즈 실제 변형 제어점을 갱신하고 닫힌 graph의 positive-winding 영역/cell교차면적을 계산해 기존 공동 area/perimeter 선택기로 전달한다. 선택480×272영역/공통mask/packet을 Raw·Native2×·레이어·눈·최종 Draw/Gate가 소비한다. 무조건 source Union/505 Build와 열린491 실험을 우회하며 후단 필터를 덧씌우지 않는다. 저장81포즈 중74개 projected graph 교차가 있어 단순polygon signed-sum 대신 교차event sweep으로 처리했다. 이는74오류/81실제통과가 아니다. 8기하fixture 통과.
- 전처리5.2583초는1회다. 실제Rig|Walk_Loop 네 연속구간(0..3/20..23/54..57/68..71),16쌍은 뼈·광원 동일/변형기하16개서로다름. Raw/Native/Hair/최종 공통경계 침범0, 기록된primitive/UV/renderer불일치0/unsupported0, Native donor깊이오차최대1.90735e-6. 같은role 몸/얼굴색차0. 경계정합은 디자인·시간품질 통과를 대체하지 않는다. 정면 양눈·다른각도/clip은 미검증.
- 선택영역의 내부8triplet ABA관측0, 기존최종(229,52) hair/face순간전환은 이국소구간에서사라졌다. 기존.8750 (224,58)은3포즈모두채움이나 이웃비용목적함수 해결을증명하지않는다. 새최종.8750 (220,45)/(219,49)은hair/body/hair가남는다. mask/Raw/Native/Hair/headPrepared는hair이며 JoinBare 깊이비교에서처음몸으로남는다. 같은프레임matchedHair에서추론한depthOffset spread0;중앙포즈 body+.0001 대비차0.00006403/0.00039114. bodyprimitive도변하므로 같은role를같은연속표면으로보거나 정상가림으로단정하지않았다. 실제body triangle/ray/sample 정합은미검증이며 epsilon/history 보정없음.
- 같은sourceprimitive 머리RGB차34표본(UV1e-5허용,동일좌표아님),가시최대17/8byte인2표본은약.55배. 저장final alpha/owner에서 기존OwnerLines outer/thin을재구성하면 경계변화로reason0→1과일치한다. GPU Before/Flood/Audit는미저장으로첫색단계의직접증명은아니다. 일반내부명암/시간출몰해결로보고하지않는다.
- 실제16쌍 중앙값:곡선갱신0.0343ms/면적0.5322ms/bin·가림16.8904ms/묶인packet·quad·upload212.3354ms. 후자내부주비용을계측하지않았다. RenderFrame원본307.631/후보674.862ms는기존다른작업포함·캡처readback제외·playerFPS아님. 실시간채택불가/관리할당미측정. alpha불확실검사최대3은GPU가림으로위임하며CPU확정가림이라칭하지않음.
- 긴RunCommand2회는timeout/미시작/훅없음을읽기로확인했다. 준비EditorCapture511 컴파일후짧은Start로16쌍성공. 중복전처리/캡처/다른프로세스종료/패키지설치/Library403재시도없음. 최종직접조회 Playtrue/unpaused/input·Animatortrue/Idle speed1 Loc0/자동시계/capture0/PostView366하나/491·502·505·508·511 OFF/ProfilerOFF/컴파일종료. Console과거16건delta0, 사용자Quality·Time/44d13c0보존.
- 전신GIF Current472/Walk511/WALK511_FULLBODY_BEFORE_AFTER.gif 519305byte,16쌍시간순서/같은실행원본대조/정수crop/공간보간없음/공통256palette,구간점프500ms표시;원본PNG·float보존. SHA4dd88555…467dd. 근거 docs/artifacts/automatic-curve511의README·contract·compiler·binding·controls·validation·actual16·review·first-stage-trace 및 Current472/FINAL_RESTORED511.json. 현재는기본OFF 미채택 목적체크포인트다. 다음최소검사는두.8750의실제연속body triangle/ray/sample 비교이며,그판별/수정전전체loop로대체하지않는다. 이후새표현한전체Walk가필요하며현재전체해결·아트채택·runtime성능통과는아니다.

## 226. CHARACTER-RENDER-01 — source-ray 몸 가림 입력512 교정, 실제3쌍513 국소통과·기본OFF

- 511 목적체크포인트02ec445와바이트동일v2 writer정리c5a2ad8을보존했다. .8750 두위치의실제3인접Walk포즈에서원본몸/머리world정점·삼각형·UV·카메라행렬·GPU샘플/선택맵을회수했다. 과거16쌍과투영차최대0.000034cell,같은두전환재현. 머리packet ray와JoinBare의몸샘플ray가약0.34~0.39cell다르고primitive도달랐다. 같은ray의앞면·alpha[1,1]인몸표면은머리보다1.74/4.46mm뒤인데다른ray의앞깊이로머리를가렸다. 같role를같surface로가정하지않았다.
- 가림정의는511 hair source packet W의실제모델몸가림소유권을설계픽셀의정수배치와함께이동하는것이다. 현재몸기하를W의orthographic ray에서교차해같headcamera깊이를만들고기존depthOffset으로둘다main깊이로변환한다. 정수XY이동이몸의다른ray를다시선택하지않는다. 기존mask R/G경계유지,B/A에참조깊이/종류를싣고JoinBare의hair/body입력만교체했다. 실제opaque앞가림유지,alpha불확실앞가림은명시실패,뒤의불확실표면은보수적lower-depth-bound,몸없음명시. epsilon100um/RGB/시간/history/면적/비용함수/가닥선택변경없음.
- 범위는hair/body전달이며전체렌더러의ray통일이라칭하지않는다. face/eye role은새몸참조를읽지않고원래localprovider/평면/가림경로를유지한다. head/main depthOffset왕복·같headcell키는변함없음. off-centre donor와eye sample이같ray라는가정은새로넣지않았다. 외부world composition은기존destination world-depth비교를유지하고body/body·face/body도미변경이다. 이구분을CONTRACT512.md에명시했으며정면눈/다른가림의전역정합은미검증이다.
- 실제.8625/.8750/.8875 세쌍은511전/512후같pose/light,기하3개서로다름. 두사건hair/body/hair→hair/hair/hair. 전체변경5cell관측은body8→hair14이며모두실제source몸tri에대조했다. 1568참조(opaque778/no-body790),mask참조/world/primitive/UV/bary/depth오류0,depth오차max4.76757e-7m/UV1.05884e-7. RGmask floatbit차0,Raw/Native/Hair/최종경계위반0,packet불일치0. main몸source와선택맵bit동일;headRawUV만마지막3float max1.49012e-8차를그대로기록했다.
- 같은role몸/얼굴·같sourceprimitive머리RGB차0,얼굴/눈rolecounts·최종캐릭터alpha동일. 실제scenePNG 첫포즈동일,후두포즈교정2x2block에서만12/8pixel차,캐릭터밖차0. GPU JoinBare6case를destination몸near/far와기본OFF로검사했다:앞/뒤/몸없음/얼굴제외/참조누락/기존epsilon모두예상일치. source몸이앞이면destination몸이뒤여도계속가린다. 실제손이얼굴앞을지나는애니는이3Walk포즈에포함되지않는다.
- 직접복원조회 Playtrue/unpaused/input·Animatortrue/Idle speed1 Loc0/자동시계/capture0/PostView366한훅/491·502·505·508·511·512 OFF/ProfilerOFF/컴파일종료,Console기존16건delta0. 앞선alpha읽기tool1회예외는CSV조회로복구했고제작runtime오류로보지않는다. 사용자Quality·Time해시/44d13c0보존,Library403재시도없음. packet212ms최적화없으며항목별측정계획만작성했다.
- 전신GIF Current472/Compare513/WALK513_BEFORE511_AFTER512.gif103103byte/SHA79f7fc02…93302,같실행511전/512후·시간순·정수crop·무보간·원본보존. 근거docs/artifacts/body-ray513의README/contract/validation/GPUfixture/ray·alpha증거,Current472/RESTORED_COMPARE513.json. 이국소목적커밋후새표현의실제전체Walk한번으로기존16구간과나머지위상을함께회귀검증한다. 현재기본OFF·미채택/전체픽셀튐·아트·실시간·전체프로젝트완료아님.

## 227. CHARACTER-RENDER-01 — 전체 Walk514 81쌍 경계정합 통과, 시간·명암 품질 미통과

- c15c2e84의 source-ray512 수정 후 Rig|Walk_Loop 한 루프81쌍(80구간/끝점포함), 실제1.333333177초를 한 번 회귀검증했다. 대조는 같은실행 활성348 원본과511곡선+512후보이며512단독전후가 아니다.81쌍 pose/light동일·변형기하81개,Raw/Native/HairLayer/localFinal 경계침범0,packet불일치0/unsupported0/몸참조오류0,동일ray깊이오차max4.76830e-7m. 이수치가 픽셀아트/시간/명암 품질 통과를 대체하지 않는다.
- .6375 head(234,43)/(218,55)의 skin→hair→skin 두전환은 선택mask부터Raw/최종으로전달돼 .8750 JoinBare깊이오류 재발이 아니다. 첫셀 원메쉬면적.442587→.449809→.435558 대비곡선면적.489966→.504317→.487092,조건부fill-minus-empty비용+.184088→-.008634→+.025815. 둘째셀 원면적.303332→.282171→.258389/곡선.367875→.345867→.321112로계속줄지만이웃3셀채움에따른경계비용변화로+.264249→-.019774→+.029736. 지속선분ID/anchor유지·연속운동,잠깐앞가림증거없음. 개별pose최적화가한프레임선택을선호하는이유이지시간품질완료가아니다. 원형모든디테일보존조건도다시넣지않았다.
- 511은3폐선분곡선94제어점을자동전처리한뒤각pose에서positive-winding cell면적A를계산한다. 선택기는fill1-A/emptyA와lambda.14의8이웃perimeter(축.58578644/대각.29289322)를각pose독립최적화하며시간/계단리듬목적이없다. 두중앙셀을다른선택고정하에생략할비용은각.008634/.019774로0이아니다. 동일품질의대안전체시간경로는아직입증하지않았다. 시간필터/추가양자화/제품패치/새촬영없음.
- 후보머리색screen23표본중12는최종alpha/owner로재구성한OwnerLines333 outer/thin reason전환과일치,11은원색/UV/명암최초단계미확인이다.21은원본에도같screen이나정상판정근거가아니다. 새screen2개는.7375(224,58) line일치/.8125(229,48) 미확인. GPU Before/Flood/Audit미저장으로첫GPU단계증명이라칭하지않는다. sameprimitive는sameUV가아니다.
- 몸색대조8표본은각pose의META/UV/OWNER가전후완전동일하다.7개는RGB.55배(오차1e-7이내)와외부연결/외곽선자격0→1재구성에일치한다. 나머지.7500 main(210,57)은.703125/.632813/.582188→.127438/.068478/.048172이며외곽선재구성으로설명되지않는다. internal/Palette audit부재로최초원인미확인,8개를모두정상명암/같원인으로묶지않았다. 선택반전과별도미해결로유지한다.
- 기록된hour4.740795/주광색·회전·강도/ambient는81개동일,자동시계만비교동안동결후복원했다. gameTime1.333초는흐른다. 로컬끝점mask/role/alpha동일,전체preworld RGB최대.00295410은양버전동일;머리max원본.00026855/후보.00061401. 실제scenePNG에서로컬캐릭터위치의73byte차가양버전같고일부표본preworldRGB는완전동일이나nativeworld최초입력은미확인이다. **WORLDINFO범위정정:** 저장f.motion.worldInfo는legacy480 Compose333이며실제960 Native395.Present의world/depth/owner/cellID/depthAudit/deliveredDelta를저장한것이아니다. 그visibility0/차0으로native가림/그림자정상을확정하지않는다. screen↔local seam수치는등록대조범위에한정,큰head ROI배경색차를head색회귀로세지않는다.
- 전신정상GIF2,327,242byte는67표본50fps/1.34초로공간보간없으나nearest-time선택이사건51을생략한다. 단독시간품질근거금지. 추가lossless정상60fps WebP1,325,022byte/80표본/1333ms는모든구간을보존한다. all-frame검수GIF2,778,726byte/80표본40ms와원본81PNG/float/기하도보존했다. 모든매체의대조는348원본vs511+512후보,배경시간변화를숨기지않음. 근거docs/artifacts/full-walk514의README/FINAL_REVIEW514/cause/analysis/review/manifest 및로컬Current472/Loop514.
- 직접복원조회Playtrue/unpaused/input·Animatortrue/Idle speed1Loc0/자동시계/capture0/PostView366한훅/491·502·505·508·511·512 OFF/ProfilerOFF/컴파일종료,Console기존16건유지. 진단helper CompressionLevel모호성CS0104만명시namespace로고쳐컴파일했다. runtime/shader변경없음·Quality/Time해시·44d13c0보존,Library403재시도없음. packet212ms최적화보류. 현재경계강제통과와시간선택/명암미통과를분리한기본OFF·미채택기록이며전체프로젝트/아트/실시간/다른눈각도/build완료가아니다.

## 228. CHARACTER-RENDER-01 — span516 offline81포즈·세계수 시제품 비채택, 대응/시간장벽 실패 분리

- 514의27c2eda기록 후515최소계약에따라활성경계/span과시간비용을격리된Python시제품으로구현했다. source ring/segment/parameter교차·T접점·공선겹침분할/positive-winding양쪽판정·H/Vspan/구간order를사용하며정적cut은단일선택기초기후보,별도mask/RGB후처리없음. 저장81포즈의양쪽winding·연결차수검사오류0/기존선택경계대응후보모두존재. 의미론적유일대응이나실제가림통과와동일시하지않는다. 정수이동/90도회전/identity cost0·활성구간소멸·합침·앞packet해제·model/camera/seek gate합성검사통과,실제그상황의Unity검증은아니다.
- 각span add/delete=unit edge수,substitute=길이차+source운동보정L1이동잔차(삭제+추가상한),merge/split도같은연결비용을쓰는명시적프로젝트DP이며논문Eq5재현아님. 기존BoundaryCost.14단위를eta.5/1/2로한번씩대조했다. 기존두screenABA관측은셋모두0이나평균면적오차+.6400/+1.7913/+3.3408,평균경계비용−.1205/−.2612/−.2430,계단기울기전환진단2.5309→3.0000/2.5556/3.1852,초기정적선택↔끝점8/12/15셀차이. 새계수맞추기/표본반전0성공판정없음. 계단진단은Eq4/오류수가아니며같곡선운동과분리해해석했다.
- 대응실패반례:동일폐영역·동일mask·동일제어점수에서직선위중간제어점만tangent방향이동시raw시간비용5.5(기하동일기대0). per-segment채널분할과material-parameter운반이실제기하곡선대응을대체한구현불변조건실패다. 저장자료의변하지않은gridedge중192회source채널재분류/165회현재도활성인인접segment사이지만모두오류로세지않았다.119 NO_CURRENT_VISIBLE_SPAN은선택span이그채널에없다는진단이며물리가림119건이아니다.
- 비용설계실패:기준끝점12셀차이선택을같기하에정지한채비용만평가했다. 유지T0,정적복귀raw42/가중5.88,공간개선2.042562이나한프레임목적은복귀시+3.837438. 허용142개모든1셀변경의최소증가+.015435로greedy local fixed point이며정적방향12변경도불리하다. 반복frame/loop를다시풀지않고영구전환장벽가능성을확인했다. 정적cut미관정답/실제steadyloop실패라과장하지않으며현재기하의지속형태이득을누적하지않는설계문제로분리했다.
- 머리전체bbox의위/아래끝은그대로,좌우max1cell이나국소계단/끝은변한다. 열envelope max7cell은같끝이7cell움직였다는뜻이아니다:frame39,x219에옆가닥영역y54..57이들어온사례로source대응없는열지표를손상량으로보고하지않았다. 미세틈통합을무조건실패로돌리지않고형태/시간대가를보존한다. 기준새채움471회/화면63셀은모두변형Hair기하donor≤1.1cell,실제renderer/submesh/primitive/bary/world/UV/depth기록. 투영정합max1.05308e-5cell. 다른opaqueHair앞가림0관측이나body잠재앞삼각형35회는alpha/backface미분리이며renderer1/원본alpha·cull/실제GPUpacket미인증이어서471전체를가림통과로칭하지않았다.
- 현재시제품은offline비채택·Unity미적용. 다음최소계약은①계수/공간비용그대로두고활성arc의구간간연결·tangent재매개화불변대응부터수정검증②그뒤같선택기안에서유한편집비용과지속형태근거의시간누적을비교하며실제표시경로/후보경로비용일관성을명시하는것이다. hold timer/RGBhistory/추가보정층/미래Viterbi를실시간이라고포장하는대안금지. 이번에새제품패치·Unity호출·촬영0,내부색11+몸1/nativeworld/packet212ms동시변경없음.
- 근거docs/artifacts/temporal-selector516의README/FINAL/FAILURE/SUPPORT/검증·source snapshots. 3×81전체480×272mask+실제timestamp NPZ와모든selector trace ZIP보존. FULLBODY_CONTEXT_OFFLINE_MASKS516.webp는80표본1333ms무손실·무보간이며왼쪽은기존511+512실제전신,오른쪽은미렌더mask진단이다. 새Unity전후GIF로보고하지않음. 마지막직접운영상태증거514복원/이번자체상태변경없음,기본OFF·runtime/shader·사용자Quality/Time·44d13c0보존,Library403재시도없음. 픽셀튐·아트·실시간·전체프로젝트완료아님.

## 229. CHARACTER-RENDER-01 — 재매개화517 합성불변성 통과, 수정span의실제81대조0/80쌍·미통과

- 516목적기록2af22f7을보존하고대응결함하나만offline수정했다. positive-winding활성기하의방향/연결·collinear정규화·기하arc대응·닫힌시작점동등성을사용하며source구간ID그대로의pixel부착을대체했다. 실제source model key는8435:4:38689b6b1da9c1b4이며제어점자산hash와분리해분할을모델교체reset으로오인하지않는다. 516의.14계수·모든편집연산산술·시간장벽·상태비용은동결,선택기재실행0/새mask0/Unity호출·촬영0.
- 동일폐영역의제어점slide/split/cyclic-start는5.5→0/reset없음. 정수이동8.88e-16/90도회전1.78e-15,기하만¼cell이동+pixel유지는5/같기하pixel편집11/실제폭성장11.119686으로변화구별. 명시적가림/분리/병합은해제하지만선택span부재는삭제20/가림아님. add/delete/substitute/merge/split과linearDP는같pretransportedpoints의6case산술/trace동일. 합성통과이며실제Unity새가림/모델통과가아니다.
- 이전whole-loopV1실패0/80대조는소스/결과로보존하고재실행하지않았다. 수정된span/arcV2를같은81고정pose/mask에한번실행했다:완전대응frame0/81,비교가능0/80,거부80/80,NO_CONNECTED_GEOMETRIC_SPAN_PATH loop대응거부102관측,부분edge124/9910. raw부분비용0을개선/통과로세지않고공식VERDICT의전후합/증감/모든거부쌍비용은null로기록했다. 102는실제그림오류수아님.
- 81원곡선모두분할/직선slide/시작점변형후canonical배열bit동일이지만전체대응거부때문에실제81포즈전체편집비용불변성은미검증이다. 6개component분리/병합/birth/death진단은곡선영역위상이며물리가림으로판정하지않았다. 실제전체arc깊이/alpha/owner가림미측정,516의새donor471미인증·색11+몸1/nativeworld/212ms미해결유지.
- 첫거부phase0 vertex(218,55),edge(218,56)→(218,55)→(217,55)는양쪽edge모두기하후보가있으나incoming은cell(218,54)/(218,55),outgoing은(217,54)/(217,55)을지나단일공유cell조건에서모든연결이끊긴다. 선택cell(217,54)/(218,54)/(218,55)은연결돼있어현재영역양자화가좁은연속U틈을통합한관계를규칙이표현하지못한것이다. 이거부에depth/alpha/owner조건없음. 과거.6375 ABA의같좌표전용예외로쓰지않았다.
- 이번결과는저장자료대응미통과·기본OFF·제품미적용이다. 다음최소의존성은선택된연결cell영역과연속face의통합/생략incidence를명시해같은입력mask에서연결증거를만드는것이며검색반경확대·모든미세틈보존·새후처리/계수조정이아니다. 이번에는더구현하지않고원인/계약으로남겼다. runtime/shader·Quality/Time/44d13c0보존,Library403재시도없음. 근거docs/artifacts/reparameterization517의README/VERDICT/FIXTURES/FIRST_REJECTION/검증·입력hash·V2전체대조ZIP/V1실패ZIP. 새전신영상/실제시간품질/전체프로젝트완료를주장하지않는다.

## 230. CHARACTER-RENDER-01 — 부분 edge518 phase0 통과, 저장81 대응 미완료·제품 보류

- 517/e8c4b84의 single-cell 연결 가정을 기존 선택 M과 연속 P의 정확 face incidence로 대체하는 offline 진단을 진행했다. I=P∩M/A=M\P/D=P\M을 기존 교차점에서 구분하고 양의 길이로 연결된 face만 묶었다. 이미 선택된 영역의 통합/생략을 재사용하며 새 mask/근접 반경/계수/시간 상태/선택기 실행/Unity 호출·촬영0이다. 가닥·홀 전부 보존 조건을 넣지 않았다.
- 첫(218,55) 통합 및(209,52) 부분 사례와19개 반례 통과. edge를 실제 P 교차점에서 부분화하고 corner 끝부분과 비용 anchor 중심부분을 구분했다. phase0 전체120/120대응/중심 소유권 거부0,614 sweep 조각→204부분/72 split edge/최대4부분. 원 유리수 활성 곡선을 float cost geometry에 유일하게 대응시켜 정확 공선성 오류를 막았고 unit 길이·비용 표본은1로 유지했다.516 원자 편집/시간 장벽/계수는 그대로다.
- phase0 gate 이후 저장81입력을 한 번 확장했다. 전체 대응79/81, 완전 비교71/80, 미대응 target[4, 5]/phase[0.0500, 0.0625], 기하 component 사건6쌍은 물리 가림으로 추정하지 않았다. 미대응/미완전 사건 총비용은null이며 부분0/합계로 성공을 만들지 않았다.243입력/81mask 해시 및81 canonical 재매개화 입력 동일을 확인했다.
- 첫 잔여 .0500 edge(209,53)→(208,53)는 D부분 뒤 A부분이며 중심 A3504의 실제 source81은 거리².264220014로 범위 안이지만 unit 방향 내적−.129470825로 거부된다. source82는 거리²2.312389718>2로 제외되고 기존 유일 후보80은 D만 소유한다. 실제 기하 부재/depth/alpha 가림 때문이라고 하지 않았다. unit 전체 방향/양끝 제한은 부분 영역 표현과 맞지 않는 추가 제약이다.
- 제한 삭제만으로 해결되지 않는 반례도 분리했다. 연결 A ribbon 전체의 source 소유권만 쓰면 top pixel edge에 반대 bottom 경계도 후보로 유입되며 실제 오선택까지 증명한 것은 아니다. 별도 source 영역은 incidence가 거부한다. 최소 다음 의존성은 정확 부분 전이와 선택 영역의 순서 있는 국소 경계 chain 대응이다. 이번에는 filter삭제/문턱 확대/새 규칙 패치를 하지 않았다.
- 81 부분 수194~226/평균208.444. phase0 원 overlay6.408초+부분0.993초+대응1.512초. 새80포즈 평균 overlay6.708초/부분1.120초/대응1.610초는Python 유리수offline 진단이며 실시간 해법이 아니다. 제품runtime/shader/Quality·Time 및44d13c0 보존. 마지막 직접 운영 확인514 이후 새Unity호출 없이 기본OFF 유지. 시간 장벽·donor471가림·내부색11+몸1·nativeworld/눈·212ms는 별도 미해결이다.
- 근거 docs/artifacts/partial-incidence518의 README/PHASE0/FIXTURES/FILTER_COUNTEREXAMPLES/VALIDATION/첫거부 및 전체81ZIP/이전실패ZIP/소스해시. Library403재시도/새GIF/제품적용 없음. 경계 대응 일부 통과와 픽셀아트·애니메이션·실시간 품질 통과를 구분하며 전체 프로젝트 완료가 아니다.

## 231. CHARACTER-RENDER-01 — 국소 chain519 저장 대응 gate 통과, 시간 상태·제품 미변경

- 60b40f9 이후 .0500/.0625의 edge(209,53)→(208,53)를 각자 조사했다. 서로 다른 A face 교차점 쌍을 공유하는 유일한 SOURCE/PIXEL run이 있어, 원 unit tangent 제한 대신 그 국소 경계의 순서·길이 진행으로 대응했다. 각116개 중 기존115개+새 chain1개, 두 포즈 및 인접 비용 대응 통과. 모든 edge로 새 표현을 확대한 첫 시제품은 다중-run 두 edge에서 실패하여 보존했고, 최종은 기존 수락 후보가 없을 때만 유일 paired-chain을 사용한다. 새 mask/계수/시간 상태/RGB history/Unity 호출·촬영0이다.
- 기존 수락 후보 생성은 이름·tuple identity·진단 metadata만 정규화하면 AST동일, 연결·순서·동점·DP도 동일하다. 새 구조는 후보 거부 때만 lazy구성해 유효한518 분기에 의존성을 추가하지 않았다. 좌표/phase 예외 상수 없이 동일 저장 기하를 정수 이동·90도 회전한 합성 반례에서도116/116/새 chain1개 및 anchor변환 통과. 반대편 경계 반례도 거부했다. 다중-run/무anchor 전체 대응이나 다른 모델·가림까지 새 규칙으로 해결했다는 주장은 아니다.
- 저장81 차등대조1회 결과81/81포즈 대응,74/80인접쌍 비교.77포즈는 증명된 동일 분기 재사용,2이웃포즈는 구·신binding 직접 동일대조,2변경포즈는 현재519 최소 검증 결과다. fresh overlay81회 재계산과 구별한다.243입력/81mask·518증거 해시 보존. 변경 인접3쌍 raw15.69996182949616/8.321112527710412/16.46931460836342는 쌍별 진단값이며 개선 점수가 아니다.
- target10/13/28/66/75/77 기하 component 사건6쌍은 영향을 받은 대응 구간 종료→현재 기하에서 새 구간 시작으로 명시했다. 사건 pose prior는UNAVAILABLE/전체전이비용null이며 영향 없는 component 진단은 별도다. 물리 가림이나 무료 편집으로 해석하지 않고 전체 시간 비용·구간 합계를 만들지 않았다. 제품 시간 상태 recurrence는 바꾸지 않았다.
- 두 실패포즈 경계 half-edge1997/2006,cycle80/82,단일paired78/80. 별도 구성46.6/56.6ms,최종binding약1.5~1.7초는Python 오프라인 진단이고 lazy구성 포함이다. 기존exact overlay비용 별도/실시간 해법 아님. 짧은 차등대조 실행은 동일 분기 재사용 효과이며 애니메이션 정지 cache가 아니다. runtime/shader/Quality·Time·44d13c0/기본OFF 보존, 마지막 직접Unity상태514 이후 호출 없음,Library403재시도/새GIF 없음.
- 근거 docs/artifacts/local-chain519의README/MINIMUM/GENERALITY/BRANCH_EQUIVALENCE/EVENT_INTERVALS/AUDIT/VALIDATION/전체81차등ZIP/실패V1ZIP/소스해시. 대응 gate만 통과했으며516 형태고정·초기조건/시간장벽,donor471가림,내부색11+몸1,nativeworld/눈,212ms는 미해결이다. 이후 상태 비용 수정은 별도 단위이며 현재 픽셀튀김·실제Walk품질·제품채택·실시간·전체 프로젝트 완료를 주장하지 않는다.

## 232. CHARACTER-RENDER-01 — 상태 비용520 kernel 최소대조, 선택기 통합 미완료·미채택

- 519/8cf7957 대응을 고정하고516 정지12셀 고정 반례를 다시 묶었다. 현재static120/held118 edge 모두519대응/왕복raw36이며 과거42를 재사용하지 않았다. 공간 비용53.536999→51.494437,면적오차36.642917→34.436335,계단비율반전진단4→2. 일회성βK가 현재 이득2.042562보다 커 기존 기억 방식의 장벽이 남는다.
- 같은 선택기 안에서 대안마다 상대 이력값을 유지하는 finite-state kernel을 오프라인 시험했다. 기존η=.5/1/2와β=.14×η를 유지하고 원81기록 간격 중앙값r=.01666666666666572초로dt/r 현재형태regret를 적분한다. 유효 raw편집 edge의 명시적 경로 envelope 안에서 비용을 비교하며 RGB/mask 후처리나 별도 출력층이 아니다.1초 기준 첫시도는 원가중치 보정을 바꾸어 미채택·보존했다.
- 한 기준간격의 첫 결정은 기존강도와동일,dt0/동일근거는 무조건 누적·decay없음. 정지반례η별복귀33.33/50/83.33ms,30/60/120Hz 및 포화전1/2/4/8분할 값동일. 유효동반운동이 주어진 kernel시험에서 화면고정없음. 복귀는12셀동시변경이며 실제시간품질통과가 아니다. 지속이득은초기상태영향을없애지만 근거가균형인 합성주기는 서로다른 초기선택을유지한다.
- 성분별 주변화재시작 kernel은 통과하나 전체이력삭제는 무관성분까지변경하는 반례에서실패했다. 기존516은 직전출력span한벌만저장해 대안이력/부분주변화가 아직통합되지않았다. static+기존3η의 제한4mask bank는 source사건10/13/66/75/77에서outer/holes조합4/4/8/3/4개가빠진다. 이는구조적containment진단이며source/depth/가림적격성이나오류개수가아니다. 이bank로재선택하는우회는미채택했다.
- kernel성질과실제선택기적용gate를분리해후자는미완료/미통과로남겼고 저장Walk세계수민감도는미실행이다. 다음필요조건은같은선택기상태에서대안값과변경성분만의주변화를표현하는것이며전역mask bank/전체reset/시간threshold를붙이지않는다. 제품/519대응/계수/기본OFF/Unity상태변경0,촬영0,신규채움가림미확인,내부색/성능미해결유지.
- 근거 docs/artifacts/state-cost520의README/PREFLIGHT/MINIMUM/RESTART_SUPPORT/VALIDATION/소스및기각1초보정ZIP. 마지막직접Unity운영확인514이후새호출없음,사용자설정/44d13c0/8cf7957보존,Library403재시도없음. 실제Walk픽셀튐·형태고정해결·제품채택·실시간·전체프로젝트완료를주장하지않는다.

## 233. CHARACTER-RENDER-01 — 이력 표현521 상태수·결합·비용 분석, 추가 구현 보류

- 520검증을1c90d1c로먼저커밋한뒤새선택기/무제한maskbank없이기존후보와API의범위를분석했다. 독립분리는공유pixel/owner·공간포함/8이웃·시간편집factor가없을때만성립하며공유separator는조건부로남겨야한다. 실제12셀은공간8이웃쌍0이지만모두outerarc0편집DP에속하고(229,35)는holearc2에도속한다. raw36=outer34+hole2,span71→72/2→4로arc별독립분리도자동성립하지않는다.
- 기존4mask의81포즈projection범위는outer최대4/holeunion최대4/결합최대16,독립일때만local값최대8이다. 유효4점조합공간비용비가산39포즈/포함제약26/합집합44,유효잔차최대.328040421. 이는진단용제한후보이며전체탐색·영속owner·source/depth/가림적격성으로확대하지않았다.12이진셀4096조합예도전수적격성미확인이고필수상태수하한으로주장하지않았다.
- 현재scalar span517.compare는전체arc cyclic merge/splitDP를호출하며outer71×72span이면회전72×표72×73=378432 DPcell(최종trace전)이다. 범위분석후별도6회call만측정해중앙0.945초/범위0.934~0.960초,overlay/mask/Unity제외다. 첫병렬측정은참고로만보존. 실시간FPS/하드웨어하한/할당측정이아니다.
- 조밀q상태는값q/행렬8q²byte/closureO(q³)/crossO(q_old q_new C_edit). q16이면현재offdiagonal최대240/cross256질의가가능해작은행렬보다완성형편집호출이문제다. q4096예는행렬하나128MiB/closure68719476736triple이며실제로할당·bank작성하지않았다. 모든압축알고리즘불가능이라는주장이아니라현재black-box정확경로의부담이다.
- 최소다음의존성은기존edit DAG의입구/출구정렬조건별min-plus전달factor와공유셀separator표현이다. 고정경계/merge삭제/계수변경으로519비용을바꾸지말고12셀반례의raw36과대안결정을조건부합성으로재현한뒤separator성장·시간비용을증명해야한다. 현재API는완성drawing의scalar/trace만제공하므로이를증명하기전추가선택기코딩/Walk세계수민감도를진행하지않았다.
- 근거 docs/artifacts/history-scope521의README/RANGE/COST/CONCLUSION/VALIDATION/분석source. 12셀동시복귀시간품질미통과/520통합미완료/신규채움가림미확인/내부색·성능미해결유지. 제품/Unity촬영/519대응/공간비용/계수/기본OFF변경0,사용자설정·44d13c0·8cf7957보존. 실제표현개선·실시간·전체프로젝트완료를주장하지않는다.

## 234. CHARACTER-RENDER-01 — 521경로 미채택 종료·인수인계522·기존 대안1회 검토

- 521을22b137a로커밋하고공유셀메시지/거대한bank/전역arcDP시간선택확장경로를미채택으로종료했다. 활성수정은44d13c0의348 eye fallback hair외곽선색보존이며전체픽셀튐해결이아니다.511닫힌분절선/94anchor/공통경계와c15c2e84 source-ray513(옵션512)은유지할구현·검증근거가있지만OFF/제품미채택이다.
- 내부색head11+body1첫GPU원인미확인,Native395 world입력미수집,grouped packet/quad/upload약212ms별도성능미해결,시간515~521실제선택기미통합/미채택을분리했다.12셀일괄복귀시간품질미통과유지. 신규render/선택기/촬영/Unity호출0,Runtime/Quality·Time해시보존,기본OFF소스그대로다. 마지막직접운영상태514이며새live조회라고하지않았다.
- 현재514전신파일은모두local존재:normal60 all80 WebP1325022byte/1333ms,normalGIF2327242byte/67표본(원51누락),inspectionGIF2778726byte/80×40ms. Library403접근차단으로현재자료미전달/재시도없음. 이전497compact전달·과거용량차단과혼동하지않았다.
- 기존510/511/514/515/360자료와원저자Feature-Aware/Superpixelator/ActiveStrokes/KZ를한번대조했다. 즉시채택할검증완료대체구현은없다. Feature-Aware는50×50예도5초/frame이고고정feature대응/구조전제,Superpixelator는정적벡터선,ActiveStrokes는연속선추적근거이며픽셀영역완성quantizer가아니다. 각자료를현재3D실시간·가림·아트통과근거로확대하지않았다.
- 재사용최소기반은511 current곡선/면적＋SelectRegions의joint-cut＋공통Draw/Gate다. 제한시공간binary joint-cut은전역span상태열거를없애는별도구조후보로추론할수있지만span편집거리목적을바꾸며클러스터/계단/출몰품질·실시간성은미입증이다. 원본mask후단filter나기존실패mincut재실행을해법으로포장하지않고새구현을자동시작하지않았다.212ms도이후보가해결하지않는다.
- 근거 docs/artifacts/render-handoff522의HANDOFF/ALTERNATIVE_REVIEW/PRESERVATION. 결과는인수인계와판단이며새시간선택기실험이아니다. 제품아트/실제Walk시간품질/실시간/전체프로젝트완료를주장하지않는다.

## 235. CHARACTER-RENDER-01 — 소매523 source원인 / 닫힌옷영역524 실제3쌍 실패·OFF

- 실제메인.html을현재상태와전신공통경계·옷우선으로갱신하고Chrome실표시·로컬링크를확인했다.438은과거표면표본,522/523/524는작업기록이며적용버전이아니다. 기존프로젝트/동일6000.5.9f1/공식MCP호스트를복구했으며새설치·보안변경은없다.
- 새실제Walk33/34/35를동결하여소매(198,85)가source중심래스터에서0/1/0임과Prepare의alpha전파,OwnerLines의thin/outer→reason0,nominal1셀→native2×2를확인했다.523의동결두재렌더10버퍼전체일치.옷에독립선행닫힌디자인경계가없었고기존한팔±1셀은전신해법이아니었다.
- 524는변형clothing2093삼각형의연속벡터합집합닫힌경계89~90점→.1875셀선분fit47/53/51점→CurveArea511면적＋SelectRegions면적/둘레공동선택을재사용한다.원본480mask복사/0.5독립threshold/형태일괄삭제/시간DP/후단보정층이아니다.같은C를source선행discard/Prepare/최종Resolve에연결하고열린한팔선택을대체했으나defaultOFF다.
- 같은실제3쌍에서목표가시와경계밖쓰기/게이트위반은0이지만선택영역native2×2donor가3/3/2셀누락돼미채택.첫실패33의정상프레임한포즈추가조회는마스크비트동일이고누락3셀native4표본모두0이다.영역선택과현packet입력의불충분이남아전체Walk는미실행.원본fallback/미기록가림으로통과하지않았다.
- 얼굴원본/Prepare/base·실제얼굴최종RGB,재질/텍스처/카메라/MPB/합성상태는3쌍과복원전후동일이고현재회색미재현이다.별도face/head렌더는실재하지만회색첫버퍼·다른테스트원인은미확인.비옷1셀은같은sourcecolour에서외곽선outer1→0으로밝아지는후보효과이며디자인허용미판정이다.
- 옷추가계산워밍후약19ms/pose,Editor전체RenderFrame wall변동273~711ms는PlayerFPS나개선근거가아니다.실시간미채택이며기존머리packet212ms·내부색head11+body1·시간문제와구별한다.3frame전신normalWebP/검사용GIF모두프레임보존,전체루프영상아님/Library403미재시도.근거 docs/artifacts/closed-clothing524. 입력/Animator/시계/후크/초기Edit·사용자설정복원;348및이전commit보존. 전체픽셀튐·얼굴회색·프로젝트완료아님.

## 236. CHARACTER-RENDER-01 — 525 MASK/연속 표면 공급 실제3쌍, 성능 실패·OFF

- 524실패와da3f5fd 보존. 원본UV texel-alpha선형등고선/cutoff/ST→실제삼각형anchor→기존닫힌벡터영역/RDP/면적·둘레선택. 중심raster mask복사/단일UV 셀투명판정/좌표·phase특례없음.
- 실제Walk33/34/35 같은실행 OFF/ON3쌍 모두보존. 소매34(198,85) 가시제거유지, 누락3/3/2→0/0/0. 불투명표면2/1/1셀은 같은ray의실제가시triangle/UV/depthpacket과GPU일치; 투명영역4관측셀은영역에서제외. 기존Probe502/Legacy502/attachment재사용, 새RT/패스/RGB이력층0.
- 전처리711ms/12931경계조각/7742anchor; 매포즈source2602→fit38 등. steady geometry약1750ms이므로실시간미채택이며해당확장중단. packetCPU13.75~24.31ms와별도head212ms구분. 전체Walk미실행/전체시간품질미판정.
- source색/face상태보존. 실제가시얼굴4/5/8셀RGB변경0, 회색이번미재현만확인. body33한셀은입력RGB동일/OwnerLines외곽인접판정0→1로.55톤적용; 전체시간시각채택은미검증.
- 기본OFF/입력·Animator·시계·후크/초기Edit·cleanGameMap1 직접복원.사용자설정해시보존. 44d13c0/511/513/내부색head11+body1/종료arcDP변경없음. local모든3프레임전신WebP/GIF/PNG와원float보존;Library403재시도없음. 증거docs/artifacts/closed-clothing525.메인.html현재525반영. 전체프로젝트/가시/회색해결완료아님.

## 237. CHARACTER-RENDER-01 — 526 정확 후보제한, 실제3쌍 출력 유지·아직 OFF

- 525 모델 불변전처리 약.7~.85초/12931조각은 이미캐시됨. 포즈투영.52~.78ms, 합집합약1.8초가반복비용.33유효변6985/2439만변쌍/최대5068만winding순회.실측pair.66초·winding1.14~1.18초로분리.직선중복약1%라표현삭제안은미적용.
- ClosedRegion524 한파일에서 AABB1셀검색후보/정확반열린축sweep으로원래연산순서·수식유지. 저장3pose 원525source/fit바이트동일,union1.8초→55~66ms. alpha/곡선/RDP/영역cost/UV/가림/시간상태변경없음.
- 같은실행실제Walk33/34/35(옷ON양쪽) source/fit·mask/면적·owner·source패킷·전신PNG동일.누락/경계위반0유지.모든float동일은아님:머리RGB최대2.98e-8차이,alpha/owner/실제얼굴변경0,원인미추적.실제geometry67.5/110.3/58.6ms로여전히실시간미채택/OFF,전체Loop추가촬영없음.변쌍후보약24~27만/winding7.6~8.1만,새엔진/필터없음.
- 저장525faceRAW7/8/11셀유색;재질/faceflags불변.395초기화allrenderer OFF→ON/setup5frame경로는있으나얼굴만gray대체근거없음.해당시작전환버퍼부재로gray원인미확인.코드추가/무차별촬영없음.
- 입력/Animator/시계/후크/초기cleanEdit·ClothOFF복원직접확인.인덱스는OFF실험내부만true.사용자설정/44d13c0/511/513/내부색/212ms보존.증거docs/artifacts/closed-clothing526,전신모든3frame미디어로컬보존·메인.html반영;Library403재시도없음.후보만증식하지않고추가자동최적화중단.

## 238. CHARACTER-RENDER-01 — 527 불투명도 곡선 입력, 실제 Walk81쌍 / 시간 품질 실패·기본 OFF

- OpacityRegion525/ClothRegion524 두 파일. UV alpha 연속 경로를 모델별 전처리한 뒤 매 포즈 투영 RDP(.09375셀)→벡터 합집합→닫힌 RDP(.09375)→면적/경계비용 선택→기존 공통mask Draw/Gate와 표면공급. 원 중심mask 복사/특정셀/프레임특례/시간필터 없음. raw opacity6714→약145, 입력12931→약6362. topology guard82회 명시(primitive12 매포즈/1599 frame61); 미기록 누락 fallback 없음.
- 실제 인접3쌍 후 FullLoopB81/81 종료·원본/후보PNG각81, 최종 채움/소유권/경계 밖 쓰기/표면Unsupported0. 초기 FullLoop는 합성 전 감사 오판2건으로 중지 보존; 최종 pr2512/2634·UV·depth·색이 원본과 일치함을 확인하고 검사 위치만 정정. 독립 최종 누락 검사 유지.
- 경계 강제 통과와 시간품질 실패 분리: frame43 (200,98/99) C=0→1→0의1×2논리셀 출몰, frame44 (231,78) 새1셀. 기존 선택비용을 계산해 전후/해당 선택이 더 낮음을 입증; 최종 누출 아님. 동일표면 비옷RGB33중30은.55tone, 나머지3 palette/내부선 원인 미확인. 얼굴RGB변화0/회색이번루프미재현, 로딩 원인 해결 아님.
- 경계 median7.884/p9513.434/max36.743ms, 모델 전처리약.7초와 구분. 전체 RenderFrame wall median 원본319.605/후보328.118ms: 실시간 채택 불가, PlayerFPS 아님. 출력/시간회귀로 미채택·기본OFF. loop mask/coverage0이나29RGB소차는 pose/UV/cloud입력 완전동등 미검증. head11+body1/머리212ms/종료arcDP 별도 유지.
- 모든81프레임 전신 losslessWebP2,289,420B/GIF2,892,811B,1350ms(endpoint17ms hold;GIF20/10/20ms). 로컬만 전달, Library403 재시도 없음. 입력/Animator/시계/hook 및 clean Edit·cloth/curveOFF 직접 복원. 사용자 두 settings 해시 보존. 메인.html527 및 docs/artifacts/closed-clothing527 연결. 전체 프로젝트 완료가 아니며 새 최적화/촬영 시작 없음.

## 239. CHARACTER-RENDER-01 — 528 저장43/44 벡터·픽셀 경계 대조 및 시간 범위 정정

- 제품/Unity 호출/새촬영0, 40db9925/OFF 유지. 43번 주변 source와 최종 곡선의 국소 꼭짓점은 같고 작은 굴곡이42/43/44 모두 지속. y98.5 x200.377048→200.312755→200.387847의.064~.075셀 이동이 픽셀경계201→200→201로 증폭. 두셀 삭제 대안 Δ면적+.367665/Δ경계−.164020/합+.203644로 기존 면적+길이 선택기가 거부. 진행순서/턴/계단리듬 규칙이 없음; 좌표·동률 버그로 입증되지 않아 수치/패턴 패치 안 함. 필요한 구조는 기존 선택기에 경계 구간의 진행/중요끝·생략근거를 전달하는 것; 전역시간bank 확장 안 함.
- 44번(231,78)은 곡선 x(y78.5)=231.403615→231.515521→231.405707에 따른 단조 대각 계단. 527의 확정가시 판정 정정; 단순ABA/셀크기만으로 같은결함 아님. 단순얇은셀삭제의 실제 반례. 43 가시 미채택은 유지.
- 타이머는 h.RenderFrame만 포함하고 Save/PNG/파일쓰기는 밖. 함수 내부 Full319.Read는 AsyncGPUReadback+WaitForCompletion이며 main 공통8개+기준3/후보2개; Post366.AfterRender는 candidateOFF여도28read+Process/업로드 실행. LateUpdate도 같은 함수를 호출하지만 이 동결포즈 수동call wall319.605/328.118ms를 PlayerFPS로 단정할 수 없음. 기존 '전체 실시간불가'를 '진단 포함 함수 고비용·PlayerFPS미측정'으로 정정. 7.884ms 경계/packet/진단 구별. 새계측·최적화 없음.
- docs/artifacts/closed-clothing528에 동일좌표 경계도/수식/코드위치 저장, 메인.html 정정. 원81프레임·복원증거 재사용. 비옷3/얼굴회색/내부색/212ms 별도 미해결, Library403 재시도 없음.

## 240. CHARACTER-RENDER-01 — 529 순서 구간→생략 최소 매핑의 정상 얇은 끝 반례 실패

- 저장527 닫힌ring/기존픽셀cycle 표현만 재사용. 시간arcDP/상태bank/계수/Unity호출/촬영/제품변경0. 한 축의1셀미만 되돌림+다른축 단조 구간을 명시적 OMIT shortcut으로 매핑하는 단일 소형 시험.
- 42/43/44 목표ear1개씩 .691932/.722201/.749419셀²; 정상44 대각 구간은3포즈 모두 생략없음. 단일 정상끝은보존하지만 넓은몸에붙은.75×3셀 끝 두개반례에서2.25셀²각각을잘못생략. 4회전/직선분할동일. 정상얇은끝gate실패로 graphcut/런타임적용/실제촬영미진행. 새길이/면적조건붙이지않고 해당후보종료.
- Opacity Boundary21행 primitive/anchor/alpha기원이 CurvedProjection.Emit234행 좌표쌍에서유실, ClosedRegion.BuildSegments99행/ClothPrepare35행ring→Select39행면적만전달. 순서만으로는source에도있는43되돌림을거부못함. 자동끝/파트연결근거와keep/merge/omit결정을동일구간에보존할표현필요; 토폴로지기원만으로충분하다는검증은없고FullLoopB경계기원미저장. 수작업좌표요구/전역상태확장안함.
- docs/artifacts/closed-clothing529에 최소실험source/좌표/반례도 저장, 메인.html반영. 기본OFF/기존제품·사용자설정보존. 상태변경없어527복원증거재사용, 새복원조회없음.528정정/비옷3·회색·내부색·212ms별도유지, Library403재시도없음.

## 241. CHARACTER-RENDER-01 — 530 얼굴 로딩/테스트 전환, 기존음영확인·반복회색미확정

- 529경계확장종료/제품수정0. Native395전체renderer OFF→ON, HeadLocal별도headRT, 재질복제/플래그복사/복원 경로 확인. 최근옷테스트 얼굴write없음. 프리팹 얼굴_MainTex04/Colorwhite/Debug0/indexMPB없음. grayscale Stage1분기는있지만 각패스Stage2지정/관측2. 다른세션원인단정안함.
- 실제한번 제어된paused진입 첫2렌더얼굴source/provider/prepared/final PNG확보. custom-list JSON누락 진단실패보존, 한번재진입 첫1렌더 sparsefloat로UV/명암값회수(전체Walk추가없음). UV43대응중39×.72오차최대5.48e-8/classifier0,4원색/classifier1;21미대응동일표면가정안함. 최초endpoint LegacySignals→BodyPalette302 role3;Provider Auto245Fragment동일식. Legacy/provider/prepared RGB0차, main UV대응(0,-2)/depthoffset.018461/RGB0차. sampledskin무채색0이나반복신고재현/해결아님.
- frame94 Canvas표시준비/present0→95present1 관측. 첫미생산RT RGB미회수라얼굴원인연결/패치안함. 자연coldload타이밍은paused입력한계. 다음최소증거는실제회색사건전후의테스트단계/출력종류·source/class/provider/final RGBA UV meta/StageDebug/재질MPB/history. 상수덧칠/fallback보정없음.
- ENOENT죽은24412/빈tools미실행확인후공식22792읽기로회복, 권한·계정변경없음. 두관찰완료후직접cleanEdit/pausedfalse/compilefalse/clothcurveOFF/backgroundfalse/capture0복원. 사용자settings해시보존, docs/artifacts/face-gray530/메인.html상태반영. 비옷3/내부색/212ms등별도유지, Library403재시도없음.

## 242. CHARACTER-RENDER-01 — 531 옷 기원 복원, 범주만으로 정상 끝 구별 불충분

- [현재] 527 material3 선언 범위/제품OFF. Edit 정확한 finger bone 검사: slot3 1224정점 중 finger가중치0, skin slot0 1432정점 양수. 현재 모델 맨손/손끝 직접 미적용; 모델 공통 해부학 필터 아님. 초기 Ring부분일치가 HoodString을 세던 진단만 정정. 사용자 설정/기존 활성44d13c0 보존.
- 실제 Walk43/44 기하2포즈 primitive/anchor/UV/part 회수. 국소소스7/6변 미대응0, cloth 내부edge(incident2), 알파/열린옷단 아님;43오른/44왼LowerArm. Project의 Vector2쌍 반환→BuildSegments 좌표합집합→Fit 좌표링에서 원구간 기원 소실. 반ULP 저장오차 대응, 중복후보를 가시owner로 단정하지 않음. 최초 header parser0프레임 실패 보존/제품reader block순서로 진단 수정. 진단만2점fit 저장 차이 정정: 제품len>=3 적용 곡선거리1.50e-5/1.53e-5cell, ROI<8e-6. 새 최종품질 통과 아님.
- 기존529 정상0.75×3끝을 동일투영 닫힌mesh로 만들면 같은 내부edge/material/part. 회전×직선분할8반례 확인: 기원범주/ID만으로 keep/omit 불가. 전체기하 구별불가능 증명 아님. 순서있는 연속특징 범위의 공간디자인계약이 남음;529깊이규칙/시간DP/새패널티/피부확장/새RGB·loop촬영 없음. docs/artifacts/clothing-origin531 및 메인.html 반영.
- 직접cleanEdit/paused·compile·updatefalse,clothcurveOFF,capture0,GameMap1dirtyfalse 복원 후 asset-only도EditOFF확인. 제한환경IPC미실행 뒤 기존승인host/PID22792 read정상;보안변경/Editor중복/강제종료 없음. 회색530미확정/비옷3색/내부색/성능 별도;진단RenderFrame≠PlayerFPS, Library403재시도없음. 이번 제품개선0, 전체목표미완료.

## 243. CHARACTER-RENDER-01 — 532 옷 공간 영역 근사, 실제4쌍 가시 제거·비옷5색 미확정

- 옷 기본OFF 실험2파일: ClosedRegion524.FitArea532 + ClothRegion524.UseAreaCurves532. 원불투명도/폐영역 추출·기존면적/공간cut·공통Gate 재사용, 거리RDP를 대체(필터/529예외/시간DP/손피부확장 없음). 현 방향s 비역행일 때 ∫|h(s)|ds<=1논리셀면적이면 원arc를현으로 근사, 아니면 기존최대수직점 분할. 국소절대면적이며 원저자검증공식/전역오차보장 아님.
- 기존4포즈+정상끝8반례만 사용. 반셀거리대조는 정상끝1셀손실로폐기. 실제43 폭.409729/길이2.81130/arc2.97478/면적.722201; 정상끝 .75/3/4.5/2.25; 잘못된긴shortcut 거리.372104나 절대면적1.125. 영역대조는43두셀제거/44계단·정상8마스크유지,12사례 proper교차0. (200,96)의0→1→0은 연결단조계단 길이변화이며 가시로세지않음.
- 실제Animator Walk42~45 527옷ON대조/532옷ON후보4쌍완료. 최종43두셀제거, 채움/owner/경계외쓰기/packet bary·depth 위반0,face·eye역할RGB변경0,새회색피부0. 비옷동일표면5색변경(42hair4,44role8한셀,RGB약.55배)은 최초패스미확정으로남김; 기존527비옷3과다른비교. 전체532Walk/루프미촬영·미채택.
- 경계중앙7.6037ms; 진단RenderFrame(readback/probe포함)≠PlayerFPS. 4프레임전신losslessWebP53812B/67ms·공통팔레트GIF87781B,프레임누락/보간0. input·Animator·clock 복원 및 직접cleanEdit/paused·compile·updatefalse/cloth·opacity·areaOFF/capture0/backgroundfalse/dirtyfalse 확인. 사용자설정/44d13c0보존, docs/artifacts/clothing-shape532·메인.html 반영.
- 해상도단위: 공통480×272, 화면2배. 거리 .1875/.09375=logicalcell 길이,532의1.0=logicalcell면적,cut .14 고정계수이며 명시곡률한계/격자변경자동환산없음. 부모가 전달한 Feature-Aware2016 §4.1/Fig7/Eq3 공간extrema/width대응은 미적용·대응미검증. 원자료최종검토전 추가수치/구현확대보류. 얼굴530/내부색/성능/Library403 별도미해결·재시도없음.

## 244. CHARACTER-RENDER-01 — 533 전체81쌍, 5색 원인확정·새50파임으로532 미채택

- 제품코드추가0,532/b75ecb1d·44d13c0·사용자설정 보존/OFF. 기존5표본알파계산 후 누락42/44 GPU버퍼4렌더조회:prepared RGB동일,OwnerLines audit reason0→1/outer0→1/thin0,postLine=Before*.55오차0/final동일.42옷209,57 제거로내부빈공간외부연결→hair4셀;44옷227,65 제거→226,65외부노출. shader752flood/ownCore 재계산일치,색패치없음. 재조회hour4.727/원532실제hour미저장(initial21설정)라 과거절대광원동일주장안함;소유자·UV·depth·전체alpha는동일.
- 같은실행527옷ON대조/532옷ON후보 실제Walk0..80 81쌍1회완료. skyHour5.016488고정/카메라ortho1.502602/native2 일정. 34재발없음,43두셀제거,44정상계단유지. 채움/owner/경계외쓰기/packet오류0,face·eyeRGB차0/새회색피부0. 비옷30표본 최초변경전부OwnerLines:외부노출27/visible같은part폭·ownCore3,입력RGB·targetowner동일/GPU판정재현.28own-tone/2기존palette분기이며30개오류로세지않음.39/47새visible-cloth tip은actor단조계단/색소유권전환과구별;정상앞가림전체인증아님.
- 전체후보실패:50(201,97)비워연결경계파임→아래201,98~99가1×2논리셀돌출.실제PNG확인,mask밖누출아님. A=.3882917762,채우기Δunary+.2234164476/Δboundary-.1640202105/합+.0593962371로현재선택기가파임유지. 원곡선subcell굴곡·근사·area+perimeter가디자인보장못함.49/50/51입력보존·무작위threshold/penalty/새시간층추가없음.짧은return20후보는오류수아님.
- 루프actor alpha0차/소유자·UV근접28셀RGB차최대.0737744 원인미확정(world/shadow/시간전부동일미검증).경계중앙7.6307ms≠PlayerFPS. losslessWebP1,101,318B/GIF2,419,755B·81프레임1350ms(명목60Hz+17ms닫힘hold),누락/보간0.전체후보전신sheet/대표대조육안확인. CAPTURED81/input·Animator·clock복원true후직접cleanEdit/paused·compile·updatefalse/cloth·opacity·areaOFF/capture0/backgroundfalse/dirtyfalse·face상태동일확인.
- docs/artifacts/clothing-full533·메인.html 갱신,전체raw W Current472/Outline533/FullLoop 및SHA보존. pixel단위고정상수≠해상도독립source/world상수,투영pitch가변하면source오차도변함;grid일반변경·연구식자동환산미구현.532지역면적근사와2016참조extrema/폭대응은목적공유하나후자는미적용.시간DP/Gaussian/curvature식병합없음.얼굴530/기존내부색/성능별도미해결,Library403재시도없음.

## 245. CHARACTER-RENDER-01 — 534 저장자료 인과분리, 면적근사 국소정보 손실·루프입력 미동일

- 새 렌더/Play/제품패치0. 기존 컴파일함수 Edit 수학호출1회로49/50/51의 동일Source→source/distance/area→면적/선택 대조. area곡선float배열·면적·mask 모두533runtime와오차0. 후보532/b75ecb1d는OFF/미채택,활성348/44d13c0와사용자Quality/Time보존.
- 50에서FitArea532가Source스냅샷index120(201.23416138,98.46575928)을생략. chord최대위치오차.24701128셀>옛distance.09375이나적분면적.301624718셀²<예산1로승인. 독립lobe면적차1.84e-8,상쇄/좌표변환오류없음. 셀201,97면적source/distance.458947003→area.388291776,채움→비움. 최초정보손실FitArea532:147,최초이산파임SelectRegions(ClothRegion524:40),후단누출아님. 비움유지flip비용+.059396237;옛결과비움비용+.081914216.49/51도같은승인경로/연속오차이며새재귀분기불연속을가정하지않음.
- 같은chord/오차면적.75/폐면적8.75인서로다른합성곡선2개가같은area근사로소실. 총면적은국소분포·폭·span을인코딩하지않음. 실제50동일면적동률증거는없음. 수학구현오류가아닌목적/표현부족이므로예외·벌점·threshold·시간층추가없음;옛distance복귀도정상얇은끝손상근거로성공처리안함. 참조/출력경계형상대응정보필요,2016폭항미구현.
- 루프28표본은모두같은실행527ON대조와양끝RGBA각각동일(area추가효과0). 과거원본OFF도근접매칭28/좌표27공유이나다른실행·광원이어서동등대조아님. phase0=2.50339508e-6/80=6.19888306e-6,Source최대좌표차.000854492셀/area.000259399셀. clip·회전·ortho·skyHour5.016488는같으나bone/skin·카메라행렬·전체빛/그림자·shaderclock·history미저장. UV2e-5근접매칭≠같은입력. 동일입력회귀판정및개별색원인미확정. 측정RT는worldComposite전이므로후단worldhistory의역방향원인불가,상류/눈history전체배제주장안함.
- 기존5색표본은OwnerLines의인접빈영역외부연결/외곽노출재분류(42옷209,57→hair4셀,44옷227,65→226,65). preparedRGB동일/postLine=Before*.55,원색변조버그아님.533GPU근거재사용,미술채택과구분. 얼굴회색미재현/내부색/패킷212ms/시간선택미채택은별도유지. 새기능·촬영없으므로Play재검증반복없음;수학호출Edit/OFFguard·상태변경없음/533직접복원증거유지.
- docs/artifacts/clothing-cause534 및메인.html534에수치·도식·15수학결과·입력가용성보존. 기존533전신GIF2,419,755B/81프레임1350ms를명시적으로재사용(새영상아님). Library403재시도없음. 전체해결/실시간채택판정없음.

## 246. CHARACTER-RENDER-01 — 535 고정참조 폭 항 오프라인 gate, 정상끝 생략 선호로 미통과

- 저장43/44/50+정상끝회전×직선분할8개만재사용. Unity/Play/촬영/제품수정0,폭·높이·대응반경.5/1/2논리픽셀의논문설계상수유지/탐색0. Feature-Aware2016 §4.1 Fig7/Eq3 원문재확인;전체방법은Eq1/2형상·위치와Eq4계단도사용. 현재480×272/native2의1논리셀=2화면px이며자연상수/해상도최적공식아님.
- 포즈별pre-Fit Source를고정하여모든후보가공유,FitArea/최종mask로참조재생성없음. 다만상류opacity근사/포즈간지속featureID는미인증. 기존HeadRegion502.Boundaries규칙으로셀모서리경계생성;저작선중심경로와다른표현임을명시. 높이1미만참조는eligibility제외대조이며원문반복pixelperturbation전체이식주장안함. 평탄극값중점/동축·같은극성/반경2대응,현재자료분기·다중대응·유효폭미정0;semantic선소유권전체인증아님.
- 기록된국소반사실:43가시2셀제거시2.423800→.923800,50파임1셀채움시2.992856→1.492856로각각-1.5(미대응H1/W2와H1/W1극값제거).44정상계단1셀생략은1.007784로불변. 좌표는기존사건진단라벨이며제품조건아님. 기존desired대안순위만으로통과처리안함.
- 정상H.75/W3끝2개보존은1,둘다생략한몸통은1/11=.090909로오히려선호,8반례모두동일. height1제외없는진단은보존0/생략1/11로반전하나상수수정채택제안아님. 이전반셀손상은1.083333이므로보존선호만보면잘못통과할수있음. 논문전체실패/기하불가능증명아니며폭항단독의현재적용gate실패. 진단폭밴드가H<.5이웃을넘지않게정정;정식eligibility점수전부동일/초기결과보존,미정항0취급안함.
- 필요한정보는고정참조↔출력경계같은arc/line대응·선밴드/채움좌표계·형상/위치근거·계단span품질. 판정책임은SelectRegions경계선택이며FitArea는참조를덮지않는후보역할이어야함. Eq3후단추가/새예외·penalty·시간DP·bank·새엔진구현없음. gate실패로Unity진입보류,기본OFF/활성44d13c0/사용자Quality·Time/운영상태불변;얼굴·내부색·패킷·루프입력별도미해결.
- docs/artifacts/clothing-feature535와메인.html535에원문/적용차이·전체수치·입력SHA/압축·반례도식보존. 새게임캡처아님/과거533전신GIF와구분. 문서·브라우저검사및기록목적커밋,Library403재시도없음.

## 247. CHARACTER-RENDER-01 — 536 전체 공간 목적식 입력 동등성 검토, 합계평가 미정

- 새공간평가/선택기/제품수정/Unity/촬영0. 원문2016 §4.1/Algorithm1/AppendixA의공간항을함께검토: Espace=Eso+.5Esc+Eqs+.5Eqj,시간항제외/논문공간가중치그대로/튜닝0. 원문전체적용성공·실패판정안함.
- 535정상끝8기록분해: 참조H.75/W3의출력거리.25/0/.25는반경2안이며제외전정상대응/각비용0. 높이eligibility가참조를제외해출력3극값각1/3→합1;출력극값을지우면그항도사라지고W11의1/11만남음. 검색반경실패아님. 참조제외+출력방향합산+다른공간항누락을구분.535목록제외는원문참조pixelperturbation과다름을정확히기록.
- 원문공통입력은고정변형참조선·출력픽셀중심/span벡터화·원본선대역고해상도warp·같은선대응·초기span수. 현Source/셀모서리경계/채움면적A/8이웃길이는동일입력아님. 위치coverage는선대역가중값이며A로대체불가;closed-loop시작/방향대응도미정.43/50/44+8사례전체공간값은null,누락항0처리/535Eqs인증없음.
- SelectRegions는areas,width,height만받으므로항4개를개별픽셀벌점으로붙여원문동등해법이라할수없음. 기존투영곡선·표면·Gate재사용가능하나한포즈참조선↔출력경로↔선대역↔채움의공통자동어댑터계약이선행. 사용자수작업선저작요구아님. 일정거리대역합성등은명시적영역용변형이며원문warp대역과구별.전역시간DP/bank필요없음;새대형엔진필연성도미증명.입력미동등에서합계/새선택기구현보류.
- 웹공식원문텍스트확인;로컬PDF다운로드HTTP403에서중단/우회·재시도·설치0,원도표로컬시각검증미수행(기존Library403과별개). docs/artifacts/clothing-space536에전체명세·기존8수치분해·입력SHA·메인.html반영.활성44d13c0/실험OFF/사용자Quality·Time·입력·Animator·clock·hook불변;기존얼굴/내부색/패킷/루프입력별도미해결.

## 248. CHARACTER-RENDER-01 — 537 안쪽1px 중심경로 대응, 기존순서 재사용과 구멍/접촉 한계

- 제품/선택기/Unity/촬영/네트워크조회0. B4(S)=채워진셀중4축이웃하나이상빈셀로명시(L1두께1,OwnerLines동일주장없음). 저장43baseline/50area/정상끝1개+최소대각접촉/3×3벽1구멍의한정오프라인검사. 논문포팅/새임계값/시간DP없음.
- 단일중심경로조건은고정adjacency에서성분1·모든차수2(닫힘)또는차수1두개·나머지2(열림),시작/방향anchor별도. G8에서43/50/정상끝은성분1,분기4/0/4. G4변경만하면49/44/4성분으로분리. 기존HeadRegion502.Boundaries순서→변의안쪽소유셀→연속중복제거는3사례모두단순순환/비연속반복0/전이8이웃내.픽셀삭제·근접반경·분기휴리스틱없음.무차별8이웃이만든추가연결과실제경계진행구분.
- 대각접촉2셀은영역폐경계2개이나G8중심열린경로1개로합쳐지고,경계순서별로는각단일점퇴화. 3×3벽1구멍은폐경계2개가중심셀4개를공유;G4한순환만채움경계로쓰면원래빈(1.5,1.5)이엄밀히내부가되어구멍소실. 의도적세부생략금지가아니라동등변환주장에대한반례.
- 최소판정:방향있는셀모서리폐경계/영역이권위,중심경로는경계ID/변/안쪽셀incidence를전달받는동일후보의뷰.공유셀은복수소유권,퇴화/접촉을몰래삭제·연결금지.535무라벨경계를논문선으로취급한부분은교체대상이며,이번3사례순서대응성립을전체논문/합계공간품질통과로승격안함.향후범위는기존변소유권입력어댑터와이번5사례보존검사뿐,이번에는구현안함.같은정의새단계반복종료.
- 메인.html의535문장을직접'논문재현아닌영역경계유사폭항진단'으로정정하고537·docs/artifacts/clothing-outline537에그래프/중심순서/구멍수학/SHA보존.403접근재시도/우회/Library업로드없음.활성44d13c0/실험OFF/사용자Quality·Time·입력·Animator·clock·hook불변.기존형상선택·얼굴·내부색·패킷미해결.

## 249. CHARACTER-RENDER-01 — 538 평가용 경계ID·소유권 연결, 전체 공간 항 미구현

- 오프라인최소어댑터구현:권위폐영역→방향경계ID→단위변→안쪽셀→순서중심노드.43/50/44+8정상끝+접촉/구멍13사례·저장35후보에같은함수.원마스크35개불변/SHA확인/모든변이정확히한노드로전달.공유픽셀은복수경계노드/소유권보존,중심선fill재생성0.런타임연결·선택기·Unity·촬영0.
- 참조경계선분과소유셀의직접교차에참조ID/변index/매개구간도전달,근접반경추가없음.이는2D경계incidence이며3Dsurface/UV/depth/가림동일증거아님;직접교차없음을디자인실패로세지않음.포즈간지속ID구현주장안함.
- 실제43/44는양의참조순환2개→출력경계1개,작은순환면적.0002608018/.0002608612셀²의(228,70)비선택으로carrier없음.50은.0002659395셀²순환과주참조경계가같은출력셀의노드에함께대응.작은순환과주경계선분교차0.정상끝8개는참조/출력1/1.접촉은경계2/단일점중심경로2,구멍은경계2/변16/경계별노드12/공유물리픽셀4유지,구멍채움없음.미세영역생략·통합자체를오류나복원목표로세지않음.
- Eso공통참조/출력선분할·phase·퇴화/통합규칙,Esc고정원본선대역/warp/가중coverage,Eqs원문벡터화/참조perturbation,Eqj같은극값/span초기분모모두미구현.따라서전체35점수null/완전공간평가0,누락항0·535proxy대체·가중치튜닝·추가penalty없음.두결함개선/정상보존동일기준근거미충족→런타임교체/실제캡처진입안함.남은필수전제는후보독립고정디자인참조그래프/선대역과소실·통합·퇴화의공통평가단위.원본모든미세영역복구나후보참조역생성으로숨기지않음.
- docs/artifacts/clothing-adapter538에어댑터/35뷰압축·전체입력gate·참조사건수치보존,메인.html구현/미구현구분.원535입력archive재사용.참조JSON numpy정수직렬화진단오류수정은Unity오류아님.활성44d13c0/실험OFF/사용자Quality·Time·입력·Animator·clock·hook불변.403재시도/새자료조회/Library업로드0,기존내부색/얼굴/패킷별도미해결.


## 250. CHARACTER-RENDER-01 — 539 전체 return 교체 / 540 공통 옷 실행모드와 실제81쌍

-539 `14d4b6c`: 임의 RDP 부분chord를 전체 outward-return 단위로 교체. 공통480x272에서 두return이 같은extremal level로 돌아오고 반대축 진행이 단조인 외측영역을 면적<=1논리셀²로 통합 생략; source구간 비중첩 선택·winding/교차검사.43 return .72220097셀²(폭.409729/길이2.811299),50 .79401660셀²(폭.430710/길이2.934649).532 부분chord .301624718의 국소형태손실과 구분. 프레임/셀특례·raster후처리·시간이력·논문전체포팅없음. 정상.75x3끝8저장사례 유지, Python/C#11입력 곡선/면적/mask동등.539 실제42..51 10쌍은527ON대539ON 겉옷대조이며 제품OFF/전체통과아님;539문서의167ms는전체시간으로정정,내부진단의옛depth<1라벨은실제area<=1코드와다름을명시.
-540 같은ClothRegion524 경계/면적/선택을 Body1하의·2신발·3겉옷에 재사용. RGBA role마스크로Probe/Prepare/Resolve 권위연결, ClothSurface525가해당submesh/primitive/barycentric/UV/world/depth를한packet으로유지. 부위별알고리즘복제/새엔진/색donor없음. 실행메뉴EValidation/Boundary540 Clothes/Off와Experimental Body0;serialized씬/설정변경없음. Body4/Face7/Hair4실제분류;Body0은검정이너·스타킹·피부·손공유atlas이며옷만선택분리주장안함.
-실제Walk33..51 19포즈/57장 제품OFF·옷14·Body0포함15 대조. 옷경계밖/빈칸/얼굴눈변화0. Body0은35/36(217,49),41(218,49)의Face role4→Body role8 소유권변화로미채택,전체확대안함. 깊이/UV/중간색근거보존,회색재현이나동일표면색차이로대체안함. 손전체해결주장없음.
-새전체Walk0..80 81쌍/162장 제품OFF대옷14 실제검증완료. missing/gate/unsupported/invalidOwner/선택union빈칸/visibleactive-owner경계밖0;Face/Eye RGBA0·재질/shader/texture/MPB/camera상태텍스트81쌍동일.21sourcepacket의role/선택/barycentric/유한depth/거리검사통과.34소매셀·43가시제거,44정상계단유지,50좌경계97..103행x202.모든쌍contact9장을검토했고새대형형태붕괴없음;모든미세도트/시간품질완료판정아님.머리/피부/손기본경로보존.
-잔여:비활성부위동일표면색64표본중63은OwnerLines에서최초차이,1머리표본은Prepared에서2.3268e-5차이.원색변조버그·미술정상으로일괄판정안함.루프끝선택mask3개/출력coverage/owner role동일이나floatRGB OFF65/ON66표본.후보추가(233,99)는각끝에서OFF/ON Prepared동일,기존미소입력차가OFF의고정deepCream선에가려지고ON의선생략부위에서드러남.경계/owner반전이아니며texture/shade하위입력은미분리,화면RGBA8대조도별도기록.끝source차최대.002304논리셀로동일입력가정안함.기존내부명암·회색미재현·head패킷212ms·시간선택미채택유지.
-비용:전체81쌍RenderFrame중앙OFF304.39/ON344.90ms는기존core동기GPUreadback포함·별도캡처PNG/분석제외이며PlayerFPS아님.옷geometry17.82/면적1.21/선택21.82/upload1.63ms 합42.48ms,packet중앙.064/최대40.15ms,콜드geometry1414ms분리.실시간기본채택불가로제품OFF유지하되실행가능Clothes모드보존,미세최적화층추가없음.
-영상FULL540_CLOTH GIF1,525,246B/WebP848,156B,81프레임1350ms/424x346,전신·모든프레임·원래60Hz간격보존·보간0.새전체skyHour17.86330/인접7.22407로실행간배경동등가정안함.메인.html첫화면제품OFF/통합ON·정지43/50·Body0실패·비용/미해결명시,Chrome/링크실검사.자료docs/artifacts/clothing-common540와원rawworkspace경로연결. Library403재시도/우회없음.
-운영:전체End의입력/Animator/clock복원true,최종직접Edit/비정지/모든cloth실험OFF/capture0/backgroundfalse/sceneDirtyfalse.컴파일통과·새Console오류없음(이전진단2건구분),QualitySettings/TimeManager원바이트보존.메뉴Off실행확인;ON은실제capture의동일설정으로검증했으며메뉴클릭전체조작을별도재촬영하지않음.539/540목적커밋,무관사용자/다른세션파일stage금지.


## 251. CHARACTER-RENDER-01 — 541 Body0 최초채움 추적 / 542 캐릭터 왼팔1×2돌출 원인 확정, 제품수정없음

- 540 Clothes/Off·4067f62와모든runtime소스보존.사용자새관측을우선해캐릭터기준왼팔팔꿈치를저장540전체81프레임으로검사;새전체촬영/알고리즘/threshold/성능패치0.프리팹Humanoid LeftUpperArm/LeftLowerArm→J_Bip_L_* 가중치와기존part2태그/Body3(role10·owner11)삼각형일치확인.화면좌우로부위판정안함,Clothes미적용Body0사건과구분.
- 대표64→65→66의논리(201,73),(201,74):65에1열2행돌출(실제960화면2×4px),64해당열없음→66같은열4행.원본OFF와540ON에함께존재,540신규회귀라부르지않으나미해결누락범위정정.선행선택mask에이미포함되고65Before/PostLine동일하므로후단alpha누출/dilation생성아님.
- Source/Curve x(y73.5/74.5)=201.395075956/201.469506670로동일;큰elbow return은24.7201772셀²·깊이2.9645233·길이15.991246이라539의<=1셀²전체return생략대상아님.셀면적64=.189482/.077738→65=.592356/.529834→66=.946597/.940668.선택식Σ(selected?1-A:A)+.14*(.58578644직교cut+.29289322대각cut)에서65두셀제거시면적+.244380116/경계-.164020203/합+.080359913.공간선택기가tab을유지하는이유확정;연산오류가아니며큰곡선의새leading-span진행/폭설계가목적식에없음.
- OwnerLines333의별도thin예외가밝은돌출을강조:65두셀outertrue이나세로동일part2연속3셀없음/상하ownCore2셀부족→thintrue/reason0로밝은옷색유지.66지원확장→thinfalse/reason1→기존deepCream(.127438,.068478,.048172).4연결exterior/이웃part를저장Before·tag에서재계산해PostLine과일치.경계밖0·빈칸0은선택경계모양/ink시간일관성통과가아님;논리1×2를그대로허용한mask와별도선예외의책임불일치.그냥정상운동/격자교차라며완료분류안함.왼팔domain 고정셀alphaABA0도이문제를검출못함.
- 무조건얇은끝삭제/모든thin검정칠/새penalty·history·전역DP 추가안함.이번수행은원인판별까지이며새제품수정은없음.다음수선은기존선택/생성계약안에서진행경계span과채움·선권한을같이정의해야하며원형·정상끝/손가락보존검증이필요.옷42.48ms/내부색/얼굴회색미재현은독립유지.
- 541보존:기존35/36/41 자료에서Body0 global9627→primitive9626의정점3개가모두Head100%임을확인(Body0에머리피부포함).초기수동동결fixture는정렬불일치로원인근거제외/보존;검증된실제Walk실행기35..41 7포즈21장에누락입력만추가조회해기존3사건동일depth/UV재현.중심Body0빈칸,유일native(xx0,yy1)=(x+.25,y+.25)표본을선택면적.551148/.628022/.638847로Prepare가채움.격리RT의정확Prepare재실행owner가JoinBare전이미Body8로기존최종과동일.35Body13.698246 vsHead13.8726997+offset(-.007336277)=13.8653631이므로JoinBare는Head를거부.같은시선의정확한물리가림/Head표면범위계약은왼팔우선전환으로미완료;face무조건우선/색상수패치없음.
- 메인540전체전신비교/메뉴보존,542미해결aside와기존540에서뽑은64/65/66전신+확대/81프레임왼팔확대연결;새수정결과로표시안함.원인수치·본/tag·GPU541입력archive·실패fixture구분은docs/artifacts/clothing-cause542,raw는원task에보존.최종직접Edit/모든cloth실험OFF/capture0/backgroundfalse/sceneDirtyfalse,7포즈input/Animator/clock복원true;사용자Quality/Time과540runtime바이트보존.403재시도/우회0,제품변경없는진단·검증기록목적커밋.

## 252. CHARACTER-RENDER-01 — 543 공통 옷 leading-span 선택 수정 / 실제81포즈 회귀검사

- 540 Clothes/Off와 사용자 Quality/Time 설정을 보존했다. 곡선이 최종 픽셀 경계였다는 과도한 해석을 정정: 기존 곡선은 셀면적 입력이며 최종 영역은 SelectRegions가 선택했다. 65번 두 셀은 제거 비용 +.080359913이라 유지됐고, 별도 OwnerLines333의 3셀 지원 예외가 밝게 남겼다. 후단 채움이 확정 mask 밖에 쓴 현상은 아니었다. 선색과 영역 권위는 구분한다.
- 기존 닫힌 곡선의 순서 있는 넓은 outward return에서 가장 바깥 열의 3연속 셀을 같은 cut label로 묶었다. 각 셀은 양의 면적과 안쪽 완전피복2셀을 요구한다. 원본 가는 끝/홀을 무조건 보존하거나 삭제하는 규칙이 아니며, 기존 ownCore/hasThree와 양립하는 넓은 경계 단위이다. 면적+경계 목적식은 유지하고 별도 penalty/history/filter/좌표·프레임·좌우팔 예외를 추가하지 않았다. 논리셀 기준 디자인 상수이며 해상도로 유일하게 유도된 공식이나 논문재현이 아니다.
- 저장15입력(실제7 outerwear +정상 얇은끝8)에서 C# 기하그룹과 reference parity를 확인했다. 실제 Walk34..66 중7포즈에 540/형상/명도/결합4렌더를 비교했다. 형상은65의(201,73),(201,74)를 제거하고 새 경계에 기존 선색을 적용했다. 명도만 수정하면 가시가 남아 철회했으며 OwnerLines333/FullFeature367의 원래 바이트를 복구했다. 실제66 신발 끝1셀 차이를 숨기지 않고 전체 검수에 포함했다.
- 새 실제 Walk0..80 한 루프81포즈·243렌더: 제품OFF/540/543 같은 카메라·pose·skyHour13.1281166. 누락·unsupported·잘못된owner·확정 mask밖0, 얼굴/눈/헤어 색차0. 후보와540의 최종 출력 차이는22포즈, 선택 mask 차이는 가림으로 최종에 안 보이는5포즈를 포함27포즈였다. 변경22포즈 전신contact와 국소 확대를 대조했다. 알려진34/43 가시 제거,44정상계단,50홈과8정상끝 반례를 유지하고65가시를 제거했다. 모든 미세 도트/내부명암/다른 모델의 시간품질 완료 판정은 아니다.
- 동일 source packet/UV/depth 색차44표본은 PREPARED 동일, POSTLINE에서 최초 차이였다. 비옷3관측(0/80 같은 사건 및12)은 인접옷 경계에 따른 기존 exterior/ownCore 조건 변화까지 계산했다. Body0 원색 덧칠이나 source 색 버그로 분류하지 않는다. Body0 얼굴소유권·얼굴회색 사용자보고(이번 미재현)·손 확장·기존내부색·머리패킷비용은 별도 미해결이다.
- 전신 GIF3,095,462B/WebP1,509,156B,81프레임1350ms,3열636x346. 보간/프레임누락0, GIF 시간단위10ms 근사와 WebP16/17ms를 구분했다. 메인.html 첫화면에 새543과 이전540을 구분하여 표시하고 Chrome/6로컬링크/스크린샷 확인. Library403 재시도·우회0. 상세 docs/artifacts/clothing-span543; 원raw는 Current472/Span543/FullLoop543.
- 최적화 전 후보 geometry19.2517/area1.3041/selection25.3016/upload1.8614ms는 각 중앙값이며, core RenderFrame423.3248ms는 기존 런타임 readback 포함·별도 캡처/PNG/저장 제외, PlayerFPS가 아니다. 이전54042.48ms와 다른 실행조건으로 최적화 효과를 주장하지 않았다. 다음은 같은 수정본/동일입력의 결과보존 최적화 측정이다. 제품 기본OFF, 실행가능 Shape543 모드 제공.
- End의 입력/Animator/시계복원true, 직접 Edit/비정지/실험OFF/capture0/backgroundfalse/sceneDirtyfalse 확인. 사용자변경·348·540/Body0진단 보존. 새 구조/셰이더 층은 남기지 않고 실제 형상 수정과 증거만 목적커밋한다.

## 253. CHARACTER-RENDER-01 — 544 경계 cut 동등축소 / 실제81포즈 출력·비용 검증

- 543/f53b1e2 형상수정과 기존540 모드를 보존하고 한 원인인 선택기 그래프 크기만 줄였다. 기존 .14에서8이웃 경계비용합 .4920614<unary1이므로 그룹에 속하지 않은 A0/내부A1 라벨은 엄밀히 고정된다. 그룹셀은 유지하고 fixed/free 링크를 같은 terminal 비용으로 옮기며 고정쌍상수만 제외한다. 기하·면적·span·가중치·시간·색/UV/depth 변경, 정지캐시, 추가필터0.
- 저장81포즈x3부위243마스크와8끝반례 exact. 대표 고정입력21회 비계측짝지은 cut 시간 중앙8.7907→.8343ms/p959.7992→.9663ms. 실제 경로의 새 mode Clothes543에 연결하고 참조 선택기도 보존했다.
- 첫 Runtime544는2번 float 차이로 정지, 오판을 숨기지 않았다. 후속 단일 실제0..2 prefix+2번 REF_A/REF_B/OPT/REF_C 대조에서 메시/카메라/hash/time 동일, 원본반복 자체가 머리RGB262/UV70/world24표본의<=7.45e-9/1.49e-8/1.86e-9 차이를 보였으나 nativePNG8 차이0; REF_B/OPT/REF_C는float0. 최초실패의 원버퍼는 미보존이라 동일픽셀/산술원인까지소급확정하지 않았다. 원본반복비교 없이 float count를 화면회귀로 본 검사한계를 정정했다.
- 수정된 gate는 실제 Walk81포즈 모두 원본self-control을 유지하고 측정쌍 순서를 번갈아 적용했다. mask/meta/실제native8 exact, candidate float가 같은포즈 원본들에 없으면 epsilon없이 거부한다. 최종 참조/최적화 RGBA/UV/meta/world/mask 차이 모두0. 원본self float drift21495/5237/1720관측은별도기록하며8bit0; 프레임폐기/시간필터없음.
- 실제 선택기 중앙22.3029→2.1455ms/p9542.0085→2.8867; 전체옷경계 중앙43.2429→23.0643/p9594.3667→35.9346ms. geometry17.7368→17.7560ms로변경없음. coreRenderFrame347.002→323.3646/p95747.1663→725.8658ms는 기존runtime readback포함·추가검증readback/PNG/파일제외, PlayerFPS아님.54042.48ms와실행조건이다르므로효과는현재짝지은값으로만평가했다. 초당60프레임채택/전체성능완료로과장하지않는다.
- Mono 할당API는 실제1MB양성대조도0이라 프레임할당 bytes미측정으로남겼다. 별도 코드상graph allocation객체는 실제65outerwear1980→169node/38524→3412E; 측정bytes로혼동안함. timer빈쌍p95.000100ms,10만회loop평균.0000586ms. 새Profiler/GC/설정조작없음.
- 메인543 전신GIF81프레임3095462B/1350ms를동일기능비교로정직하게재사용하고544성능/전체동등성/새정지쌍/할당한계추가,Chrome표시·로컬링크검사. 원본실패/대조/수정gate/원raw경로는docs/artifacts/clothing-compact544. Library403재시도/우회0.
- 명시Clothes543 모드에만동등축소채택,제품기본OFF/540/348보존. 실제81End입력/Animator/시계복원true,직접Edit/비정지/spans·compact·clothOFF/capture0/backgroundfalse/sceneDirtyfalse. Console은기존진단2건그대로/신규0,Quality/Time원바이트보존. 전체프로젝트/Body0얼굴·손·내부명암·회색원인·머리/실시간성능완료아님.

## 254. CHARACTER-RENDER-01 — 547 단순화 전 구간 참조 / 실제81쌍 / 파이프라인 문서

- 546에서 확인된 Fit539→Groups543 구간 재탐색 손실만 수정했다. 면적.240015713셀²의 작은 return 생략으로 큰 국소 구간이 전체의 비단조 arc로 바뀌어 그룹이 빠졌었다. ClothRegion524 한 파일에서 group 참조를 Source로 전달하고 fitted Areas/지지/비용/544 cut/셰이더는 유지한다. 이전 입력 비교용 UseSimplifiedSpanReference546 외 새 renderer/filter/시간상태/좌표예외 없음. 정상 span 경로에서 false, Release에서도 복원.
-  저장251입력 native baseline exact, 후보23입력31셀 변화. 정상 얇은끝8개,34/43/44/50,65소매 유지. 실제64~70 7쌍 후 실제81쌍 한 루프; 포즈/카메라/변형정점/clock 해시 일치,243마스크가 저장예측과 동일.68왼쪽소매(200,73)/(200,74), source11300/11298 제거. 전체팔꿈치/전신시간품질 완성으로 확대하지 않는다.
-  최종옷gate/unsupported/invalid owner0, 성분8·hole4 수 동일. 화면RGBA8 차이는18프레임266픽셀, 얼굴눈머리0.51머리 float2표본 미세차는 화면0이며 산술원인 미확정. 같은표면색47표본은 PREPARED동일/POSTLINE최초변화/바뀐경계1~2셀 이내.76(225,106)은 더 앞 옷13.899133이Body0 14.214467을 가림; Body0 알고리즘 확장이 아님.
-  실제 source와 선택경계/전체순서를 함께검토, 정상 끝·구멍/연결 회귀 미관측. 양팔 경로 동일, 이전65만으로 전체팔 통과라던 범위오류는546부터 정정 보존. 방향동률16/69·내부명암·Body0얼굴·회색사용자관측·손/머리/실시간성능은 별도 미해결.
-  GIF1,878,993B/WebP1,282,638B,81프레임1350ms 전부 보존. OLD543/544 vsFIX547 같은실행, 제품OFF영상 아님. skyHour3.1476202로 이전실행과 배경다름 명시. 메인 첫화면 최신영상/디스크/알고리즘 링크, 이전결과보존. Library403 재시도없음.
-  선택기 중앙2.2511→2.2360ms, geometry18.0667→18.0652ms; core353.6486→341.1058ms는 기존readback 포함 Editor호출. 품질캡처 고정순서이므로 새최적화율/PlayerFPS아님.544 최적화와545할당증거 별도유지.
-  docs/ai/CHARACTER_PIXEL_PIPELINE.md에 3렌더러15슬롯·semantic part 구분, 실제15단계 입력/출력/좌표/쓰기권한, 명암/색/곡선/면적/선/가림/합성과546수치예제를 연결. 명암은physical 표본step, 실루엣은폐곡선 cut이므로 현재 같은선택기 아님; 같은셀/표면/실루엣 gate와 향후공통화 가능한 면적/채움책임을 구분.100%전신단일파이프라인 목표의 미완료/모델의존/중복렌더/752flood/readback 명시. 새 그림자 구현 없음.
-  공간 읽기전용: C50.75GiB여유, Codex124.01GiB, W/E_UnityValidation_01 76.04GiB·Current47214.07GiB. 원본14.79GiB(LocalOnly8.65/Library4.12). 최근24h수정파일2.68GiB는 현재크기이지증가량측정아님. 삭제/이동/압축0.
-  기존공식host/project-path연결복구. import 응답timeout후 재import없이컴파일확인. 첫capture helper누락은 미실행으로보존후한번수정호출. 자동입력/Animator/clock 복원true; 직접Edit/unpaused/cleanScene/모든실험OFF/capture0/backgroundfalse/activeGameplay없음. Console기존진단2건동일/새0,Quality/Time바이트보존. 목적변경·증거만커밋, 제품기본OFF.


## 255. 549 손 source 추적 / 550 헤어 동일시선 가림 (2026-10-23)

- [실제 조회] 손32/33/34(207,111) primitive7997/source7998:33에만 centre barycentric(.332899,.197204,.469896) 내부. alpha1/cutoff.5, Map0, source→Prepare→final 동일. Body0는 기존 옷bits14에서 제외. 정상 끝 보존 포함 적용은 미완료.
- [가설 정정] 얼굴35/36/41의 같은 head source ray에는 실제 불투명 Body0 Head100% primitive9648이 Face보다 앞. 시선만 고치면 해결된다는 가설 기각, 머리 피부/몸 소유권 범위 분리가 남음. 얼굴 우선·깊이편향 없음.
- [수정] 헤어24 상단셀은 다른 body ray 비교로 거짓 가림, 아래셀은 정상 앞가림. HeadLocal/FullFeature/GridJoin3파일:기존 head centreMeta1을 allBody ray로 사용. 기존511/491 대체 패킷·Face/eyes/world 제외, 새RT/패스/필터 없음. defaultOFF.
- [실제 검증] 연속3쌍+전체81쌍 각1회.17포즈22표본 Body8→Hair14;같은ray규칙위반0/source동일/alpha변경0/Face·눈·안정된비헤어RGB변경0. 안정된헤어RGB float최대7.45e-9,비트동일로 표기하지 않음. 손·소매 영역 알고리즘 변경 없음. 전체헤어틈/명암 해결 아님.
- [전달] Current472/BodyHand549/FULL_WALK550.gif 2,909,861byte / losslessWebP1,428,726byte.81프레임1350ms전신보존. 메인550 첫화면 최신비교. 양쪽547Clothes ON/550만OFF vsON. Library403재시도 없음.
- [운영] 자동입력/Animator/clock복원true+직접cleanEdit/550OFF. Console기존진단2개동일/새0.547·Quality/TimeSHA불변. import및첫긴launcher timeout은 미실행/상태확인후재import없이컴파일확인·축소실행기로연결. Reflection조회도구거절은우회없이공개상태API로대체. 새성능측정없음.
- 증거: docs/artifacts/body-hair550/RESULT550.md 및 RECEIPT550.json. 원시작업C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/BodyHand549/. Body0/정상손끝,헤어양음영역,내부색/성능은다음범위다.

## 256. 551 몸·손 범위와 머리 피부 분리 — 2026-10-23

- Body0 10,022삼각형 중 주 연결 성분9,702개에 머리/몸이 함께 있다. Humanoid Head 하위 영향0인8,762개만 몸·손 대상으로, 머리/목 혼합1,260개는 원본 렌더 유지. 원본 mesh+Head binding별 범위를 캐시하되 매포즈 변형/투영/영역 선택은 갱신한다.
- 범위표를 경계 입력/원본 마스크/Prepare donor·Resolve/채움 표면에 공통 적용. 547 span reference와544 선택기 수식 보존. 얼굴 우선 덮기/깊이 바이어스/좌표 예외 없음. 6기존 파일 변경, 명시적 Experimental551 메뉴, 기본OFF.
- 실제31~42 12쌍 후 전체0~80 Walk81쌍. 양쪽547 Clothes+550 동일; 우측만 몸·손 추가. 얼굴/눈/헤어 소유권·얼굴색 변화0, 비Body0 소유권 변화0, unsupported0. 33 손 기부 순간셀 제외. distal손끝114중112동일셀,33엄지/49새끼2표본은 면적0.4719/0.4635로 생략. 전체 출몰/손끝 품질 완료 아님.
- 코드 내부 단계(첫포즈 제외80쌍) 경계 중앙값52.2466ms/p95 91.2553ms, 별도 공급0.11975/21.2163ms. 기준Clothes경계21.09075/52.9294ms. readback·파일비용 제외 단계이며 기존42.48ms와 범위가 다르다. GC.Alloc ProfilerRecorder1MiB 양성 대조 valid=true/samples0으로 할당량 미측정.
- 전신81프레임/1350ms WebP1,208,822B/GIF2,723,716B. 자동 input/Animator/clock복원true, 직접Edit/clean/OFF 확인. Library403 재시도 없음. 자료: docs/artifacts/body-scope551/RESULT551.md 및 RECEIPT551.json. 원시작업 Current472/BodyScope551. 헤어552는 별도 비교.

## 257. 552 헤어 한 셀 틈의 기존 영역 경로 재사용 — 2026-10-23

- 550기준81포즈에서 head-local 좌표를 맞춘 source 음의셀 출몰 후보7개 확보(오류수 아님). 35번(226,54)은source부터얼굴4이고34/36은hair14. 후단가림이새로만든틈아님.
- 기존514 같은포즈의source owner/primitive대응을확인. 과거면적34/35/36=0.982091/0.980956/0.979902, mask hair=true. 과거조명과현재조명이다르므로RGB대조에쓰지않음.
- 새실제34/35/36 세쌍: 547 Clothes+550 대기존511폐영역+513source-ray. 35틈이hair14로채워짐, 눈owner/색차이0, finalhair outsideMask0, unsupported0. 새제품헤어코드없음. packet합산217~228ms는Select/BodyRay/AddQuad/Upload전체이고업로드단독원인이라고단정하지않음.
- 정상틈/끝전체,514 .6375선택반전, 내부색/전시간품질은미해결;기본OFF/미채택. 3프레임/50ms의짧은원래시간출력을전체루프라고표시하지않음. input/Animator/clock복원및직접Edit/clean/OFF확인. Console기존진단2건동일/새0.
- 근거 docs/artifacts/hair-gap552/RESULT552.md/RECEIPT552.json. 메인.html551전신및552짧은전신·머리확대비교 연결. Library403재시도없음. 몸551수정0d96a66과독립검사이며전체완료아님.

### 551 옷 회귀 보충 — 저장81쌍

- 동일옷owner 색차이10표본은UV/depth/sourceID동일. 8은.55 또는역수,33의크림2셀은PREPARED동일/최종deepCream대체만다름. 최초단계OwnerLines333. 입력영역변경에따른outer/internal/thin/support재분류이며개별조건과품질정당성미확정. 옷색전체불변/품질통과로확대하지않음. 다음은33선처리입력단일조회이며새보정/전체촬영없음.

## 258. 553 선색의 영역 계약 수정 / 554 손끝 미채택 — 2026-10-23

- 실제33 입력에서 같은CREAM/UV/depth/sourceID와옆alpha0에도외부flood연결1→0이outer선색을없앤경로확정. 전체10색표본은5global연결/5실제이웃coverage변화로분리.CPU수식과GPUaudit/RGB일치.thin원인설정은정정했다.
- 실험553만관리옷/551non-head몸의outer를ext>0대신!covered로판정.마스크/면적/가중치/색상표/thin/깊이불변.4기존파일변경,명시적메뉴/Off복원.기존752flood는보존하여최적화와분리했다.
- 실제10쌍(1/2/3/32/33/34/40/49/53/56)및추가53UV/56옷조회2회.선택mask/PREPARED/owner/meta exact,alpha0변화,최종색변경role8/9/11만.33기대크림선색복구,56옷audit0→1×.55확인.최초53전체UV차이는좌표미보존으로원인미확정;추가53exact/56동일설정반복69headUV최대1.49e-8변동은별도보존.전체버퍼비트동일/새81루프통과아님.
- 정상손끝33/49의source→fit셀면적.485724→.471973/.506141→.463276;49원극점이Fit539에서평탄화되고기존면적+.14경계선택도제외.원형유지extrema/내부지원인증554의13저장반례에서33만복구/49누락,44도2셀변경.미채택/제품미적용,새수치조정없음.손끝2표본은미해결.
- 545 Bytes Recorder양성/선형대조1MiB1048608B/2MiB2097184B/empty0.실제33동결3warmup후각5회Prepare호출창전체스레드할당중앙값Clothes4882678B/Body55111908437B;readback/파일제외.553선최적화/Player프레임할당아님.헤어217~228ms는Select/BodyRay512/AddQuad/Upload합산,기존bin도존재하므로업로드단독병목가정패치없음.음의component를명시단위로선택하는정책은기존511에없다.
- 전신32~34모든3프레임/50msWebP64762B·GIF87400B/PNG26551B.좌551선대우553선,전체루프아님.입력/Animator/시계자동복원true,최종직접cleanEdit/OFF/컴파일확인.Console기존진단2건/새0.중간discovery끊김은공식projectpath복구,Editor강제종료없음.Library403재시도없음.547/550/551및사용자설정보존.근거docs/artifacts/owner-lines553/RESULT553.md·RECEIPT553.json,작업Current472/OwnerLines553.

## 259. 555 두 손끝 표본의 제한 최적해 — 2026-10-23

- 저장33/49의source/Fit을기존함수로exact재현.원면적/Fit면적×기존그룹/그룹제거/원면적그룹재구성5대조.두표본모두그룹소속0,모든경우false.강제true의기존수식최적해는한셀만변하며그룹위반0.최대이웃비용.4920614<unary1인544기존성질로제한해를인증했다.제품A/수식변경없음.
- Fit에서보존대가33면적+.05605423+경계.16402021=.22007445,49면적+.07344764+경계.08201011=.15545775.원면적에서는33+.02855140+0,49-.01228189+.08201011=.06972821.따라서hard배제나543소매제약의직접영향이아니며Fit원상복구만으로도해결안됨.현재공간목적식에참조말단extent보존계약이없다.
- 554재실행없이후보생성만역추적.33source/fit축극점각3매핑;49source극점0/Fit새극점1(232.5240,88.6231)매핑이나원점일치false.553의근처곡선점(233.4815,88.8962)은233,88로매핑되며동일새끼끝identity를확인한점이아님.원점ID보존만으로두표본복구된다고추정하지않음.
- 말단114중2생략은원삼각형말단뼈평균가중치>=.5표면분류였고전체손가락소실/품질실패자동판정아님을명확히했다.가장작은다음검증은기존32~34/48~50의가시참조경계와출력손형태대응이다.원형/fit/셀면적/현재cut/제한해의동일격자반례PNG81981B와원비용CSV보존.제품변경/새촬영/성능계측/전체루프0.
- 헤어현재512OFF/ON+513소비계약을코드로연결:positive영역선택동일,선택packet의source-ray몸triangle/UV/depth/alpha를Mask.BA에추가,JoinBare의hair/body비교만대체.negativecomponent단위선택은아님.새헤어코드0.553/550/547·사용자설정보존.근거docs/artifacts/hand-counterexample555/RESULT555.md·CAUSE555.json.
