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
