# 현재 구현·검증 상태

**마지막 갱신:** 2026-08-27
**역할:** 현재 구현 여부, 가장 강한 검증 등급과 기능을 다시 열 수 있는 조건을 기록하는 단일 인덱스

## 판정 규칙

- 판정 우선순위는 직접 확인한 Unity·코드·에셋 → 이 인덱스 → 최신 진행 증거 → 과거 이력이다. 차이가 있으면 원인을 확인하고 쓰기 허용 작업에서만 갱신한다.
- `ACTIVE`는 재개방 조건이나 회귀가 없으면 다시 구현·제안하지 않는다. 변경 시 행을 교체하고 상세 이력은 진행 문서에 남긴다.
- 목록 밖 공백은 현재 코드에 없음을 확인한 뒤 제안한다.

### 상태 표기

| 축 | 값 | 의미 |
|---|---|---|
| 구현 | `ACTIVE` | 적힌 현재 범위가 구현되어 사용 중 |
| 구현 | `PARTIAL` | 적힌 일부 범위만 구현 |
| 구현 | `ABSENT` | 확인된 미구현 |
| 구현 | `DISABLED` | 구현은 있으나 의도적으로 비활성 |
| 검증 | `USER` | 사용자가 실제 조작 결과를 확인 |
| 검증 | `PLAYER` | 빌드된 Player 프로세스에서 확인 |
| 검증 | `PLAY` | Unity Play Mode 실제 흐름으로 확인 |
| 검증 | `CALL` | Play Mode 런타임 호출로 확인했으나 물리 입력은 우회 |
| 검증 | `CODE` | 코드·씬·프리팹 또는 순수 로직만 확인 |
| 검증 | `UNVERIFIED` | 현재 변경 뒤 필요한 검증을 아직 실행하지 않음 |
| 검증 | `BLOCKED` | 현재 변경 뒤 필요한 검증이 외부 조건 때문에 차단됨 |
| 범위 | `PROTOTYPE` | 현재 시험·그레이박스 범위 완료 |
| 범위 | `PRODUCTION` | 정식 범위와 수치까지 확정·완료 |

`UNVERIFIED`와 `BLOCKED`는 이전 버전의 성공 증거를 지우지 않는다. 상세 근거에 이전 증거와 현재 변경 뒤 남은 검증을 함께 적되, 현재 행을 검증 완료로 취급하지 않는다.

## 상태 ID별 계약 경로

현재 상태 행을 바꾸기 전에 아래의 관련 절만 읽는다. playbook은 작업 절차이며 사용자·게임 계약을 대체하지 않는다.

| 상태 ID | 관련 계약·기획 절 |
|---|---|
| `BOOT-01`, `SHELL-01`, `TRAVEL-01`, `TRANSITION-01`, `INPUT-01`, `MOVE-01` | `AGENTS.md` §4, `GAME_FLOW.md` §1~3·8, 개발계획 §2.2~3.2, GDD §2~3 |
| `INTERACT-01`, `ACTION-01` | 게임플레이 계약 §4.4~4.5, GDD §3.3·4.6 |
| `ITEM-01`, `BASE-01`, `MERCHANT-01`, `ITEM-UI-01` | 게임플레이 계약 §4.2·4.8·4.9, GDD §5·8~10 |
| `COMBAT-01`, `CORPSE-01` | 게임플레이 계약 §4.5·4.7, GDD §4·6.11 |
| `AI-01` | 게임플레이 계약 §4.6·4.10, `ai_generation_plan.md` §1~11 |
| `MAP-01`, `MAP-ARRIVAL-01` | 게임플레이 계약 §4.3, `GAME_FLOW.md` §4~5, GDD §7, 개발계획 §14 |
| `RAID-01`, `SAVE-01` | 게임플레이 계약 §4.1·4.8·4.9, `GAME_FLOW.md` §6~8, GDD §2.6~2.7·11 |
| `QUEST-01` | 게임플레이 계약 §4.4·4.7~4.9·5, GDD §2.3·3.3·8.5.4·9.5·10.5.4·12.2.5 |
| `INFO-01` | 게임플레이 계약 §4.9·5, GDD §3.4·9.1·10.2·10.15 |
| `PIXEL-01` | GDD §14; 현재는 재사용 요청 전까지 계약을 확장하지 않음 |
| `SPAWN-01` | 게임플레이 계약 §4.3, `GAME_FLOW.md` §5, GDD §7.8~7.11, 개발계획 §14.1 |
| `GAP-POI` | 게임플레이 계약 §4.3, GDD §7.5·7.7·7.10, 개발계획 §14.1 |
| `LOOT-01` | 게임플레이 계약 §4.2~4.3, `GAME_FLOW.md` §5, GDD §5.7·7.9 |
| `GAP-COMBAT` | 게임플레이 계약 §4.5, GDD §4.5~4.7·18.1 |
| `GAP-AI-TACTICS` | 게임플레이 계약 §4.6·4.10, GDD §6.6~6.12, `ai_generation_plan.md` §6~11 |
| `GAP-LOSS` | 게임플레이 계약 §3.1·4.8, GDD §5.8·18.4 |
| `GAP-EXTRACTION` | 게임플레이 계약 §2·3.1·4.1, GDD §2.5.4·7.8 |
| `GAP-SAVE-POLICY` | 게임플레이 계약 §4.9, GDD §11.8·18.5 |
| `GAP-QUEST-PERSISTENCE` | 게임플레이 계약 §4.9, GDD §9.5.1·11.2.3 |
| `GAP-BASE-CONTENT` | GDD §8~9·18.3 |

## 현재 동작 중인 기능

| ID | 기능 | 구현 | 검증 | 범위 | 상세 근거 | 현재 경계 | 다시 여는 조건 |
|---|---|---|---|---|---|---|---|
| `BOOT-01` | 최초 실행·메인 메뉴·공통 로딩 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §12 | `InitialLoadingScene → MainMenuScene → GameLoadingScene → GameMap1`, New/Load/Settings/Exit | 시작 흐름이나 해당 씬·Manager 직접 변경 |
| `SHELL-01` | 게임플레이 Player 셸 영속성 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §1·9·13 | Player·외형·Camera·HUD·Inventory UI·EventSystem이 같은 `PersistentGameplayShell` 인스턴스로 왕복 | 셸 계층·참조·생성/종료 경계 직접 변경 |
| `TRAVEL-01` | `GameMap1 ↔ GameMapTest` 직접 이동 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §1·14·20 | 시작 로딩 씬을 거치지 않고 기존 Player를 SpawnPoint로 이동 | `DirectSceneTravel`, Spawn, 도착 완료 경계 직접 변경 |
| `TRANSITION-01` | 검은 전환과 입력·피해 잠금 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §20·21 | fade 동안 이동·공격·무기·인벤토리·상호작용·저장·피해 차단 후 복원 | 전환 잠금 소유자나 복원 순서 직접 변경 |
| `INPUT-01` | 씬별 Escape·입력·UI 분기 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §21 | Base pause, Raid non-pause 메뉴, 별도 Main Menu | 새 scene kind나 허용 규칙 추가 |
| `INTERACT-01` | 공통 E 상호작용 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §3~5·36 | 최근접 하나, 열린 Chest 유지, 닫은 뒤 재선택, 거리 이탈 공통 닫기; 고정 기지 NPC는 solid `Obstacle`로 안정 정지 | `PlayerInteractor`, 거리·취소 계약 또는 고정 NPC Collider·태그 직접 변경 |
| `ACTION-01` | Player 공용 행동시간 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §37 | 동시 행동 1개·진행률 소유; Chest 열기 1초, 닫기 즉시, 거리·입력·씬 전환 시 취소 | 취소 정책·UI 또는 장전·회복·먹기 연결 |
| `MOVE-01` | Player 이동·Shift 달리기·8방향 회전·Humanoid 이동 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §9 | WASD 방향 회전, 걷기의 1.3배 달리기, root motion 없음 | 이동·Animator·외형 참조 직접 변경 |
| `ITEM-01` | ItemDatabase·grid 인벤토리·회전·현재 장비·HUD | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §12~13 | definition ID, 원자적 이동/rollback, W1 장착, 저장·왕복 보존; W2·W3는 예약 | 소유권·grid·장비·저장 형식 변경 또는 W2·W3 노출 요청 |
| `COMBAT-01` | 시험 총기 공격·피해·사망·효과음 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §16 | Player 원점 마우스 XZ Raycast, 단발/자동 RPM, 피해 35 시험값 | 사용자가 탄약·재장전·최종 조준 등 새 범위 결정 |
| `AI-01` | 근접·원거리 적 AI 1단계 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §19 | NavMesh 순찰·감지·추적·LOS 공격·총성 조사 | 엄폐·도주·저격 등 다음 전술 단계 요청 |
| `CORPSE-01` | 적 사망과 공용 시체 전리품 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §20 | AI·공격·피격 정지, root·렌더 유지, 기존 Chest UI 사용 | despawn·정식 드롭·씬 재진입 저장 추가 |
| `MAP-01` | 도심 도로·Cube 건물·런타임 NavMesh | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §14 | seed 기반 연결 도로와 막힌 Cube 건물, Entry→Portal 경로 | 도로·건물 생성 규칙 직접 변경 |
| `MAP-ARRIVAL-01` | 원정 맵 도착 안전 gate | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §32·34 | Ready 뒤 공개; Invalid는 covered 기지 복귀, 불가 시 잠금 보류 | readiness·도착·rollback·redirect 변경 |
| `SPAWN-01` | 도심 시험 적·상자 seed 배치 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §33~34 | 필수 시험 Chest·근접 적은 Entry 근처, 원거리 적은 보존; list binding·stable manifest·NavMesh·Resume hash 검증, 전역 개수 제한 없음 | 프리팹 카탈로그·배치 규칙·binding·Recovery hash 변경 |
| `LOOT-01` | seed 기반 시험 LootTable | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §34 | `Chest → LootTable → ItemDatabase`; Fresh 1회 원자 적용, Resume은 저장 grid 복원, table 미지정은 기존 초기값 유지 | 다중 roll·수량·희귀도·위험 예산·모드 ID 정책 추가 |
| `BASE-01` | 기지 Chest·가구 영속성 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §18 | stable ID별 grid와 중첩 아이템, 왕복·backup 복원 | 배치 가능한 가구나 layout migration 추가 |
| `RAID-01` | 기지/원정 Escape·생환·사망·포기 결과 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §21·35 | 생환은 즉시 확정·피해 차단 뒤 자동 기지 정산, commit 뒤 `확인`만 표시; 포기·사망 분기는 기존 정책 유지 | 메뉴나 결과 정책 직접 변경 |
| `SAVE-01` | ordinary save·원정 Recovery·결과 정산 | `ACTIVE` | `PLAYER` | `PROTOTYPE` | 진행 §22~23 | ordinary marker 우선, 강제종료 Resume, 생환 전체 보존·세 실패 전체 휴대품 소실 | schema·정산·Recovery 경계 직접 변경 |
| `MERCHANT-01` | Player Gold/Silver와 무지갑 시험 상인 | `ACTIVE` | `USER` | `PROTOTYPE` | 진행 §26 사용자 확인·순수 거래 11경로 | 상인 자금 없음, 판매 sink, 이전 성공 뒤 정산, 실패 rollback | 가격 정책·상인 자금·정식 재고 결정 |
| `QUEST-01` | Cube NPC의 적 1킬·생환 시험 의뢰 | `ACTIVE` | `CODE` | `PROTOTYPE` | 진행 §30 | 공통 E로 수락, Player 귀속 처치, committed `Extracted` 뒤 보고 가능, NPC 보고로 완료; 보상 없음·Play Session 한정 | 퀘스트 규칙·보상·저장 schema 또는 관련 상호작용·사망·정산 경계 변경 |
| `INFO-01` | U 정보창과 실행 기록 | `ACTIVE` | `CODE` | `PROTOTYPE` | 진행 §31 | 캐릭터·기록·사전·의뢰·업그레이드 5탭; 기존 원본 읽기, 실행 기록만 별도 권위 소유; 업그레이드는 미구현 표시 | 정보 항목·입력·기록 저장·도감 해금·업그레이드 규칙 변경 |
| `ITEM-UI-01` | 공용 아이템 tooltip·상인 전용 가격 배지 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §27 | 모든 아이템 tooltip, 상인 stock에만 가격 표시, 탭·닫기 정리 | 표시 필드나 UI 배치 직접 변경 |
| `PIXEL-01` | 3D 픽셀아트 시험 효과 | `DISABLED` | `PLAY` | `PROTOTYPE` | 진행 §15 | 사용자 요청으로 비활성 | 사용자가 재사용을 요청할 때만 |

## 확인된 실제 공백과 결정 대기

이 표는 현재 확인된 후보이며 완전한 백로그가 아니다. `DECISION`은 사용자 결정 전 구현하지 않는다.

| ID | 상태 | 실제 공백 | 선행조건·금지선 |
|---|---|---|---|
| `GAP-POI` | `ABSENT` | 접근 가능한 POI·건물 내부·랜드마크 없음 | Spawn→Portal 경로와 별도 접근 가능성 검증 |
| `GAP-COMBAT` | `DECISION` | 탄약·재장전·반동·탄퍼짐·방어 계산 미정 | 사용자 전투 규칙 결정 뒤 진행 |
| `GAP-AI-TACTICS` | `DECISION` | 엄폐·도주·저격·분대 전술 미구현 | `AI-01`을 폐기하지 않고 다음 전술 단계로 확장 |
| `GAP-LOSS` | `DECISION` | provenance 기반 선별 손실 미정 | 현재 전체 보존/전체 소실 정산을 임의 변경하지 않음 |
| `GAP-EXTRACTION` | `DECISION` | 최종 탈출 대기 시간·피격 중단·암전 중 사망 판정 미정 | 현재 시험 포탈의 즉시 생환·피해 차단·자동 기지 정산은 임시 유지 |
| `GAP-SAVE-POLICY` | `DECISION` | 정식 저장 슬롯·자동 저장 정책 미정 | 현재 단일 슬롯 ordinary/Recovery를 미완성으로 오해하지 않음 |
| `GAP-QUEST-PERSISTENCE` | `ABSENT` | 시험 의뢰 진행도가 ordinary save·Recovery payload에 없음 | 현재 Play Session 범위를 저장 안전하다고 주장하지 않고 schema·migration·원정 정산의 원자 경계를 함께 설계 |
| `GAP-BASE-CONTENT` | `DECISION` | 시험 상인·의뢰 이후의 기지 성장·정식 경제·제작·치료·정식 퀘스트 범위 미정 | GDD에서 다음 우선 기능과 정식 범위를 결정한 뒤 진행 |
