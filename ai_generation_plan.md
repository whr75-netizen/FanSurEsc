# 적 AI 설계와 단계별 구현 기록

이 문서는 현재 구현된 1단계 적 AI와 이후 확장할 전술 AI의 경계를 함께 기록한다.
후속 항목은 설계 여지이며, 사용자가 별도로 요청하기 전에는 구현 권한이나 확정 밸런스를 뜻하지 않는다.

## 1. 목표와 현재 범위

### [확정] 공통 목표

- PvP 상대를 완전히 복제하지 않는다. 여러 적을 상대할 수 있는 PvE 난이도를 유지하면서 행동 원인을 납득할 수 있게 만든다.
- AI가 Player의 현재 좌표를 벽 너머에서 상시 열람하거나 항상 직격하지 않게 한다.
- 감지, 기억, 이동과 공격을 분리해 근접·원거리·보스가 같은 기반을 재사용하게 한다.
- 랜덤 맵에서는 고정 좌표 왕복이 아니라 실제 NavMesh와 맵 생성 결과를 이용한다.
- AI의 체력·피해·사망은 기존 공통 전투 계약을 우회하지 않는다.

### [현재 1단계 구현]

- `GameMapTest`에 기존 좀비 근접형 1개와 청록색 구체 원거리형 1개가 있다.
- `GameMapTest` 두 적은 도심 layout이 한 번 만든 도로·건물 접근 후보에서 완전 경로 순찰점을 고른다. 고정 맵은 제공자가 없을 때 기존 NavMesh 임의 순찰을 유지한다.
- 시야, 총성 자극 또는 피격으로 마지막 확인 위치를 기록한다.
- 근접형은 시야가 확보되면 Player까지 최단 NavMesh 경로로 돌진하고 사거리에서 공격한다.
- 원거리형은 시야가 확보되면 선호 사거리까지 추적하면서 사격하고, 선호 사거리 안에서는 멈춰 조준 사격한다.
- 공격 애니메이션, 탄환 오브젝트, 엄폐, 후퇴, 측면 이동과 분대 전술은 아직 없다.
- `GameMap1`의 기존 좀비는 NavMesh가 없는 기지 씬의 시험 표적이므로 현재 scene override로 AI가 비활성화되어 정지한다.

## 2. 현재 권위 소유권과 호출 흐름

| 상태 | 권위 소유자 | 수명 | 변경·관찰 경계 |
|---|---|---|---|
| 적 정의와 AI 설정 | `EnemyDefinition` | Asset definition | 적 인스턴스가 읽기 전용으로 참조한다. |
| 현재 인식 상태, 타깃 기억, 순찰과 이동 명령 | `EnemyAIController` | Enemy Entity | 저빈도 판단 Tick과 명시적 자극 처리로만 변경한다. |
| 실제 NavMesh 경로와 속도 | 같은 적의 `NavMeshAgent` | Enemy Entity | `EnemyAIController.NavigateTo/StopAndFace`만 명령한다. |
| 공격 cooldown과 공격 방식 | `EnemyMeleeRushAction` 또는 `EnemyRangedPursuitAction` | Enemy Entity | Brain이 `Begin/Tick/EndCombat`을 호출한다. |
| 적 체력과 생존·사망 전이 | `EnemyStats` | Enemy Entity | 모든 피해는 `IDamageable.ApplyDamage` 하나로 들어간다. |
| 플레이어 체력 | persistent Player의 `PlayerStats` | Play Session | 적도 `IDamageable.ApplyDamage`만 호출한다. |
| 사망 뒤 행동·피격 충돌 정지와 시체 전리품 활성화 | `EnemyDeathHandler` | Enemy Entity | `EnemyStats.Died`의 완료 통지만 관찰하고 root·렌더 외형은 시체로 남긴다. |
| 시체 전리품 grid | 같은 적 root의 `Chest` | Enemy Entity/Scene | 기존 Chest 컨테이너 API가 소유하며 `EnemyDeathHandler`가 사망 뒤 상호작용만 연다. ordinary save에는 직접 저장하지 않지만, 진행 중 원정의 stable enemy/시체 인벤토리는 Recovery checkpoint가 DTO로 운반한다. |
| 일회성 세계 자극 전달 | `WorldStimulusChannel` | 통지 순간 | 상태를 저장하지 않고 활성 AI에 완료된 사건만 알린다. |
| 적 외형과 이동 Animator | 적 visual/Animator | 파생 표현 | AI·이동의 확정 상태를 표시할 뿐 판단을 소유하지 않는다. |

주요 호출은 다음처럼 역추적된다.

```text
Player 발사 cadence 성립
→ Player 원점 Raycast와 피해 적용 완료
→ GunshotSound 자극 통지
→ 각 EnemyAIController가 거리와 instigator를 판정
→ 마지막 확인 위치 기록 / Investigate
→ 시야 확보 시 Combat

EnemyAIController Combat
→ 공격 Action
→ IDamageable.ApplyDamage
→ PlayerStats 또는 EnemyStats
→ 체력 변경과 결과 반환
```

`WorldStimulusChannel`은 AI 상태의 두 번째 원본이 아니다. 이벤트를 놓치더라도 저장된 세계 상태를 복구하는 시스템이 아니며, 총성·발사체·마법처럼 드문 사건을 한 번 전달하는 통지 경계다.

## 3. 감지, 기억과 상태 전이

현재 상태는 다음과 같다.

```text
AwaitingNavigation
→ Patrol
→ Investigate                 소리 위치 조사
→ SearchLastKnown             마지막 목격·피격 위치 수색
→ Combat                      현재 시야가 있는 대상과 전투
→ Dead
```

- 시야는 거리 제곱 → 시야각 → 장애물 Raycast 순서로 검사한다.
- 가까운 범위에서는 뒤쪽에 있어도 인지할 수 있고, 그 밖에서는 정의의 시야각을 적용한다.
- 시야 검사는 매 프레임이 아니라 현재 0.2초 간격이다.
- Player가 보일 때만 현재 위치를 새로 기록한다.
- 시야를 잃으면 정의에 설정된 기억 시간 동안 마지막 확인 위치로 이동하며, 현재 Player 좌표를 계속 추적하지 않는다.
- 총성은 오디오 재생 여부와 무관한 게임플레이 사건이다. 현재 실제 cadence를 통과한 Player 발사만 반경 18의 총성 자극을 낸다.
- `FootstepSound`, `ProjectileThreat`, `MagicThreat` 종류는 통지 계약만 예약되어 있고 생산자는 아직 없다.
- 적이 Player에게 피해를 받으면 공통 `EnemyStats.DamageApplied` 완료 통지를 통해 공격자를 기억한다.

사용자가 말한 “한 번 보면 죽을 때까지 놓치지 않는 저격형”은 후속 `PersistentHunter` 기억 정책으로 만든다.

- 대상의 신원과 마지막 관측 위치는 대상 사망, AI 사망 또는 원정 종료까지 잊지 않는다.
- 시야가 끊긴 동안 Player의 현재 위치를 읽지는 않는다.
- 마지막 관측 위치, 소리, 새로 노출된 흔적과 도달 가능한 수색 후보를 이용해 다시 찾는다.
- 따라서 집요함은 유지하지만 벽 투시나 위치 치트가 되지 않는다.

## 4. 현재 순찰과 이동

- 절차 도심은 맵 소유자가 만든 read-only 공간 후보를 명시 주입받고, 자신의 시작 위치 반경·최근점을 먼저 거른 뒤 `PathComplete` 후보만 채택한다.
- 후보 cache 전체의 값싼 거리 검사는 허용하되 한 목적지 선택의 `NavMesh.CalculatePath`는 최대 8회다. 필수 제공자가 준비되지 않으면 무관한 임의점으로 덮지 않는다.
- 고정 맵은 제공자가 없을 때 기존 `NavMesh.SamplePosition` 임의 후보를 사용한다.
- 너무 가까운 지점과 최근 두 순찰점은 피하고, 도착 뒤 정의 범위 안에서 잠시 기다린다.
- 목적지가 조금 움직였다는 이유로 매 판단마다 `SetDestination`하지 않는다. 이동 임계값과 repath 간격을 모두 사용한다.
- 런타임 NavMesh가 아직 없을 때 Agent를 켜지 않는다. 보행면이 확인된 뒤 위치를 맞추고 Agent를 활성화한다.

현재 방식은 “생태계 시뮬레이션” 완성본은 아니다. 다만 고정 두 점 왕복과 AI별 지형 재분석을 제거한 1단계 기반이다. 후속 생태 순찰은 같은 맵 후보에 먹이·둥지·위험 구역·시간대 점수를 추가한다.

## 5. 현재 근접·원거리 행동

### 근접형 `MeleeRush`

- Player 시야 확보 시 `combatSpeed`로 최단 NavMesh 경로를 따라 돌진한다.
- 공격 사거리에서는 멈추고 Player를 향한다.
- 공격 cooldown이 끝나고 대상이 살아 있으며 공격 순간 시야선이 막히지 않았을 때만 공통 피해 API를 한 번 호출한다.
- 현재 시험값은 피해 10, cooldown 1초이며 최종 밸런스가 아니다.
- 선딜·타격 프레임·후딜과 공격 애니메이션은 후속이다.

### 원거리형 `RangedPursuit`

- Player가 선호 사거리보다 멀면 이동하면서 사격하고, 선호 사거리 안에서는 멈춰 조준한다.
- 현재 시험값은 공격 사거리 14, 선호 사거리 8, 피해 8, cooldown 1.1초다.
- 실제 피해 Raycast는 적의 눈높이에서 발사하며 가장 가까운 Collider가 Player일 때만 피해를 준다.
- 원거리 AI는 Player 현재점에 매번 직격하지 않는다. 연속된 가상 조준점이 제한된 속도로 목표를 따라가고, 시간에 따라 부드럽게 이동하는 오차가 수렴한다.
- 이동 중에는 오차가 더 커지며 첫 전투 판단의 긴 비전투 delta가 조준 완료 시간으로 계산되지 않는다.
- 현재 가상 조준은 1단계 시각·피해 판정용이다. 관측 지연, 속도 예측, 무기 반동과 탄속은 아직 없다.

## 6. 후속 원거리 전술은 조합으로 만든다

원거리 AI 종류마다 거대한 별도 Brain을 복제하지 않는다. 공통 인식·기억·이동 위에서 전술 선택기와 위치 평가기가 아래 행동을 조합한다.

| 전술 요소 | 조건 예시 | 행동 |
|---|---|---|
| `HoldAndAim` | 안전한 사격선, 선호 사거리 | 정지하고 조준을 수렴한 뒤 사격 |
| `AdvanceAndFire` | 목표가 너무 멀고 전진 경로가 안전 | 선호 거리까지 전진하며 낮은 정확도로 사격 |
| `RetreatAndFire` | 목표가 너무 가깝고 후퇴 경로 존재 | 뒤로 빠지며 억제·도주 사격 |
| `TakeCover` | 엄폐 후보가 현재 위치보다 유리 | 사격선·도달 시간·노출 방향을 평가해 이동 |
| `PeekAndFire` | 엄폐 점유 중 | 노출 → 짧은 조준·점사 → 다시 숨기 |
| `Flank` | 지능 프로필 허용, 측면 경로 존재 | 마지막 관측 위치의 정면 사격선을 벗어난 경로 선택 |
| `SearchAndReacquire` | 시야 상실, 기억 유지 | 마지막 위치 주변을 수색하고 새 자극으로 재획득 |
| `PersistentHunter` | 집요한 저격·사냥 프로필 | 대상 신원은 끝까지 유지하되 관측 정보만으로 추적 |

전술 결정에 사용할 점수 예시는 다음과 같다.

```text
후보 위치 점수
= 목표까지의 선호 거리 적합도
+ 실제 사격선
+ 목표 방향 엄폐 품질
+ 도달 가능한 완전 경로
+ 측면 각도와 아군 중복 방지
- 이동 시간
- 최근 피격 위험
- 막다른 길과 Player 근접 위험
```

저지능은 `HoldAndAim`과 `AdvanceAndFire`만 허용할 수 있다. 중간 지능은 후퇴와 단순 엄폐, 높은 지능은 엄폐 변경·측면 이동·지속 추적을 허용한다. 지능을 단순 명중률 하나로 만들지 않는다.

## 7. 사람처럼 납득 가능한 사격의 후속 모델

최종 사격 모델은 완전 난수나 현재점 직격 대신 아래 연속 상태를 사용한다.

```text
지연된 관측
→ 최근 관측 표본으로 속도와 신뢰도 추정
→ 탄속·거리로 예상 위치 계산
→ 제한된 속도와 가속도로 가상 조준점 이동
→ 지속되는 조준 편향, 반동과 이동 오차 적용
→ 발사 확신과 전술 상태로 발사 결정
```

요구 결과:

- 직선 이동을 오래 유지하면 예측이 좋아진다.
- 급격히 방향을 바꾸면 AI가 이전 이동 방향으로 앞질러 쏠 수 있다.
- 엄폐 뒤 재노출하면 재획득 시간이 생긴다.
- 이동·피격·압박·반동은 오차를 늘린다.
- 같은 점사의 빗나감은 서로 무관한 난수가 아니라 비슷한 방향으로 이어진다.
- 정예와 보스도 반응 시간과 최소 오차가 0이 되지 않는다.

프로필은 무기 물리 성능, 사격 숙련도, 지능, 성격과 적 등급을 분리한다. 같은 무기를 든 적은 기본 물리 성능을 공유하되 관측·행동 선택·반동 제어에서 차이가 나야 한다.

## 8. 최적화 원칙

현재 적 두 개 규모에서는 각 적의 Brain `Update` 하나가 가장 단순하다. 아직 중앙 scheduler를 만들지 않는다.

- AI 컴포넌트마다 독립 `Update`를 두지 않고 `EnemyAIController`가 판단을 조정한다.
- 비전투 판단은 현재 0.5초, 전투·수색 판단은 0.15초로 나누고 개체별 시작 시각을 분산한다.
- 시야는 단일 persistent Player만 검사하므로 `OverlapSphere`나 씬 전체 검색을 하지 않는다.
- 반복 Raycast는 고정 버퍼 `RaycastNonAlloc`을 사용하고 버퍼 포화 예외에서만 전체 결과를 할당한다.
- Player 참조는 기존 `PersistentGameplayShell`에서 얻고 매 Tick `Find*`하지 않는다.
- 총성·마법·발사체 같은 드문 자극은 event로 한 번 전달하고 프레임마다 polling하지 않는다.
- 순찰 목적지를 새로 고를 때만 완전 경로를 계산한다.
- 실제 적 수와 Profiler 증거가 늘어날 때만 scene 범위 등록 목록, 분산 Tick 또는 공간 인덱스를 도입한다.
- 향후 엄폐 캐시는 맵 layout을 원본으로 하며 생성·파괴 시 무효화와 전체 재구축 경로를 함께 가져야 한다.

## 9. 맵 생성기와 후속 데이터 경계

도심형 맵은 이후 다음 파생 정보를 제공할 수 있어야 한다.

- 연결된 도로 그래프와 교차점
- 건물 점유 영역
- **[현재]** 도로·건물 접근 순찰 후보
- **[후속]** 의미 기반 순찰·수색 관심 지점
- 엄폐와 peek 후보점
- 측면 접근 후보 경로
- 중요 Spawn·탈출 접근점
- 실제 NavMesh 완전 경로

AI가 렌더링 메시나 모든 Cube를 매번 검색해 이 정보를 다시 추론하지 않는다. 지하 던전과 오염 지역은 도심 생성기의 옵션으로 섞지 않고 각 맵 구조가 확정될 때 별도 데이터 제공자를 설계한다.

## 10. 단계별 확장 순서

1. **[현재]** 고정 맵 NavMesh 임의/도심 공유후보 순찰, 시야·기억·총성 자극
2. **[현재]** 근접 최단 경로 돌진과 공격
3. **[현재]** 원거리 접근·정지 조준·가상 조준 사격
4. **[현재]** Player 사망 완료 통지와 원정 실패 경계
5. **[후속]** 발소리·마법·발사체 위협 생산자
6. **[후속]** 후퇴·도주 사격과 단순 엄폐
7. **[후속]** peek, 엄폐 변경과 측면 이동
8. **[후속]** 기억 정책, 지능·성격·사격 숙련도 프로필
9. **[후속]** 다수 적의 동시 압박 제한과 역할 조정
10. **[후속]** 고유 행동·전조·회복 빈틈을 가진 첫 보스

## 11. 검증 기준

- NavMesh 생성 전 Agent 경고 없이 대기하고 생성 뒤 `isOnNavMesh`가 된다.
- Patrol 후보는 완전 경로이며 최근 지점만 반복하지 않는다.
- 거리·시야각·벽 뒤에서는 시야 감지가 되지 않는다.
- 총성 자극은 cadence가 성립한 발사 한 번당 한 번이며 음소거와 무관하다.
- 시야 상실 뒤 현재 Player 좌표가 아니라 마지막 관측 위치를 수색한다.
- 근접은 벽 너머에서 공격하지 않는다.
- 원거리는 실제 Collider 장애물을 관통하지 않는다.
- 공격 한 번당 대상 `ApplyDamage`가 한 번만 호출된다.
- 적 사망 뒤 Brain, 공격, Agent, Animator와 피격 Collider는 정지하고 root·렌더 외형은 시체로 남으며 전리품 상호작용만 활성화된다.
- 1명·3명·10명에서 GC, Raycast 수, `SetDestination` 빈도와 NavMesh 생성 spike를 Profiler로 비교한다.
- 후속 전술은 정지, 직선 이동, 급회전, 엄폐 재노출과 시야 상실을 각각 나눠 측정한다.

## 12. 참고한 구조와 공식 자료

- Ubisoft *The Division*: 상위 상태와 cover 후보 점수 분리 — <https://media.gdcvault.com/gdc2016/Presentations/Dunstan_Philip_BlendingAutonomyAnd.pdf>
- 2K *The Darkness II*: perception, 관측 정보와 last-known-position 분리 — <https://media.gdcvault.com/gdc2012/slides/Summit_AI/Brewer_Daniel_D2AIPostMortem.pdf>
- Day 1 Studios *F.E.A.R. 3*: 소수 상위 상태와 상황별 plan 조합 — <https://gdcvault.com/play/1013282/Three-States-and-a-Plan>
- Santa Monica Studio *God of War Ragnarök*: 공유 AI core와 역할별 subtree 분리 — <https://media.gdcvault.com/gdc2023/Slides/PreparingForRagnarokWithNotes.pdf>
- Unity AI Navigation — <https://docs.unity3d.com/Packages/com.unity.ai.navigation%402.0/manual/index.html>
- Unity `NavMesh.CalculatePath` — <https://docs.unity3d.com/jp/current/ScriptReference/AI.NavMesh.CalculatePath.html>
- Unity physics query 최적화 — <https://docs.unity3d.com/6000.0/Documentation/Manual/physics-optimization-raycasts-queries.html>

외부 사례에서 가져온 것은 “인식 정보와 실제 상태 분리”, “상위 상태와 전술 조합 분리”, “엄폐 후보 점수화”라는 원칙이다. 해당 게임의 코드나 거대한 프레임워크를 그대로 복제하지 않는다.
