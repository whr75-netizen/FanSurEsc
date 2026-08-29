# 현재 구현·검증 상태

**마지막 갱신:** 2026-08-29
**역할:** 현재 구현·검증과 재개방 조건의 단일 인덱스

## 판정 규칙

- 직접 확인 → 이 표 → 최신 증거 → 과거 이력 순으로 판정한다. 차이는 원인을 확인한 뒤 쓰기 허용 작업에서 갱신한다.
- `ACTIVE`는 재개방 조건·회귀가 없으면 다시 다루지 않는다. 상세 이력은 진행 문서에 남긴다.

### 상태 표기

| 축 | 값 | 의미 |
|---|---|---|
| 구현 | `ACTIVE` | 적힌 현재 범위가 구현되어 사용 중 |
| 구현 | `PARTIAL` | 적힌 일부 범위만 구현 |
| 구현 | `ABSENT` | 확인된 미구현 |
| 구현 | `DISABLED` | 구현은 있으나 의도적으로 비활성 |
| 검증 | `USER` | 사용자가 실제 조작 결과를 확인 |
| 검증 | `PLAYER` | 빌드 Player에서 확인 |
| 검증 | `PLAY` | Play Mode 실제 흐름 확인 |
| 검증 | `CALL` | Play Mode 호출 확인(물리 입력 제외) |
| 검증 | `CODE` | 코드·에셋·순수 로직 확인 |
| 검증 | `UNVERIFIED` | 변경 뒤 미검증 |
| 검증 | `BLOCKED` | 외부 조건으로 차단 |
| 범위 | `PROTOTYPE` | 시험·그레이박스 범위 |
| 범위 | `PRODUCTION` | 정식 범위·수치 확정 |

`UNVERIFIED`·`BLOCKED`여도 이전 증거는 보존하되 현재 변경을 검증 완료로 보지 않는다.

## 상태 ID별 계약 경로

현재 상태 행을 바꾸기 전에 아래의 관련 절만 읽는다. playbook은 작업 절차이며 사용자·게임 계약을 대체하지 않는다.

| 상태 ID | 관련 계약·기획 절 |
|---|---|
| `BOOT-01`, `SHELL-01`, `TRAVEL-01`, `TRANSITION-01`, `INPUT-01`, `MOVE-01`, `CAMERA-01` | `AGENTS.md` §4, `GAME_FLOW.md` §1~3·8, 개발계획 §2.2~3.2, GDD §2~3 |
| `INTERACT-01`, `ACTION-01` | 게임플레이 계약 §4.4~4.5, GDD §3.3·4.6 |
| `ITEM-01`, `BASE-01`, `MERCHANT-01`, `ITEM-UI-01` | 게임플레이 계약 §4.2·4.8·4.9, GDD §5·8~10 |
| `COMBAT-01`, `CORPSE-01` | 게임플레이 계약 §4.5·4.7, GDD §4·6.11 |
| `AI-01` | 게임플레이 계약 §4.6·4.10, `ai_generation_plan.md` §1~11 |
| `MAP-01`, `MAP-ARRIVAL-01` | 게임플레이 계약 §4.3, `GAME_FLOW.md` §4~5, GDD §7, 개발계획 §14 |
| `ENVIRONMENT-01` | GDD §14.1; 실내 GDD §7.7 미정 |
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
| `GAP-BASE-CONTENT` | GDD §8~9·18.3 |

## 현재 동작 중인 기능

| ID | 기능 | 구현 | 검증 | 범위 | 상세 근거 | 현재 경계 | 다시 여는 조건 |
|---|---|---|---|---|---|---|---|
| `BOOT-01` | 최초 실행·메인 메뉴·공통 로딩 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §12·53 | `InitialLoadingScene → MainMenuScene → GameLoadingScene → GameMap1`; 기존 slot의 New는 확인 필요 | 시작 흐름이나 해당 씬·Manager 직접 변경 |
| `SHELL-01` | 게임플레이 Player 셸 영속성 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §1·9·13 | Player·외형·Camera·HUD·Inventory UI·EventSystem이 같은 `PersistentGameplayShell` 인스턴스로 왕복 | 셸 계층·참조·생성/종료 경계 직접 변경 |
| `TRAVEL-01` | `GameMap1 ↔ GameMapTest` 직접 이동 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §1·14·20 | 시작 로딩 씬을 거치지 않고 기존 Player를 SpawnPoint로 이동 | `DirectSceneTravel`, Spawn, 도착 완료 경계 직접 변경 |
| `TRANSITION-01` | 검은 전환과 입력·피해 잠금 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §20·21 | fade 동안 이동·공격·무기·인벤토리·상호작용·저장·피해 차단 후 복원 | 전환 잠금 소유자나 복원 순서 직접 변경 |
| `INPUT-01` | Escape·입력·키 설정 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §21·46~48·53 | Base pause/Raid non-pause; Main/ESC 리바인딩·행별 보조키 해제/복원; 별도 설정 파일·legacy 이관 | 입력·scene 또는 설정 schema·migration·복구 변경 |
| `INTERACT-01` | 공통 E 상호작용 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §3~5·36 | 최근접 하나, 열린 Chest 유지, 닫은 뒤 재선택, 거리 이탈 공통 닫기; 고정 기지 NPC는 solid `Obstacle`로 안정 정지 | `PlayerInteractor`, 거리·취소 계약 또는 고정 NPC Collider·태그 직접 변경 |
| `ACTION-01` | Player 공용 행동시간 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §37~39·48~51·53 | 한 번에 1개; External은 이동취소, Self는 이동허용; 완료·취소 불변 결과 1회 통지 | 원형 UI·음식 연결 |
| `MOVE-01` | Player 이동·Shift 달리기·8방향 회전·Humanoid 이동 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §9 | WASD 방향 회전, 걷기의 1.3배 달리기, root motion 없음 | 이동·Animator·외형 참조 직접 변경 |
| `CAMERA-01` | 영속 직교 Camera 제한 줌 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §54 | 휠 0.5단계, size 3.5~8; UI·ESC·전환 중 차단 | 투영·범위·입력·픽셀 퍼펙트 정책 변경 |
| `ENVIRONMENT-01` | 야외 시간·하늘광 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §55~63 | 영속 시간·씬 주광; 연속 낮밤·제한 그림자; 픽셀구름 Cookie | 날씨·실내·UI·저장·구름 설정 변경 |
| `ITEM-01` | ItemDatabase·grid 인벤토리·회전·장비·HUD | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §12~13·38·40~45·48·50·53 | click·drag·stack·Shift/Ctrl; 우클릭·Alt; W1→W3 첫 빈 호환칸; 부분 stack 변경 통지; runtime 장전탄·Save v7 | 소유권·수량·장전탄·grid·장비·저장 형식 변경 |
| `COMBAT-01` | 시험 총기 공격·탄약·피해·사망·효과음 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §16·48·51 | Player 원점 마우스 XZ Raycast; 단발/자동; 시험 총 120 RPM·3발·탄약 ID 8·R 2.5초 이동장전; 피해 35 | 정식 탄종·AI 탄약·무기군별 장전·반동·탄퍼짐·최종 조준 결정 |
| `AI-01` | 근접·원거리 적 AI 1단계 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §19 | NavMesh 순찰·감지·추적·LOS 공격·총성 조사 | 엄폐·도주·저격 등 다음 전술 단계 요청 |
| `CORPSE-01` | 적 사망과 공용 시체 전리품 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §20 | AI·공격·피격 정지, root·렌더 유지, 기존 Chest UI 사용 | despawn·정식 드롭·씬 재진입 저장 추가 |
| `MAP-01` | 도심 도로·Cube 건물·런타임 NavMesh | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §14 | seed 기반 연결 도로와 막힌 Cube 건물, Entry→Portal 경로 | 도로·건물 생성 규칙 직접 변경 |
| `MAP-ARRIVAL-01` | 원정 맵 도착 안전 gate | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §32·34 | Ready 뒤 공개; Invalid는 covered 기지 복귀, 불가 시 잠금 보류 | readiness·도착·rollback·redirect 변경 |
| `SPAWN-01` | 도심 시험 적·상자 seed 배치 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §33~34 | 필수 시험 Chest·근접 적은 Entry 근처, 원거리 적은 보존; list binding·stable manifest·NavMesh·Resume hash 검증, 전역 개수 제한 없음 | 프리팹 카탈로그·배치 규칙·binding·Recovery hash 변경 |
| `LOOT-01` | seed 기반 시험 LootTable | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §34 | `Chest → LootTable → ItemDatabase`; Fresh 1회 원자 적용, Resume은 저장 grid 복원, table 미지정은 기존 초기값 유지 | 다중 roll·수량·희귀도·위험 예산·모드 ID 정책 추가 |
| `BASE-01` | 기지 Chest·가구 영속성 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §18 | stable ID별 grid와 중첩 아이템, 왕복·backup 복원 | 배치 가능한 가구나 layout migration 추가 |
| `RAID-01` | 기지/원정 Escape·생환·사망·포기 결과 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §21·35 | 생환은 즉시 확정·피해 차단 뒤 자동 기지 정산, commit 뒤 `확인`만 표시; 포기·사망 분기는 기존 정책 유지 | 메뉴나 결과 정책 직접 변경 |
| `SAVE-01` | ordinary save·원정 Recovery·결과 정산 | `ACTIVE` | `PLAYER` | `PROTOTYPE` | 진행 §22~23·48·52~53 | marker 우선·Resume·정산; 기존 slot New 확인, Base→Main 저장 성공 gate; v7과 v2~v6 이관 | schema·정산·Recovery 경계 직접 변경 |
| `MERCHANT-01` | Player Gold/Silver와 무지갑 시험 상인 | `ACTIVE` | `USER` | `PROTOTYPE` | 진행 §26 사용자 확인·순수 거래 11경로 | 상인 자금 없음, 판매 sink, 이전 성공 뒤 정산, 실패 rollback | 가격 정책·상인 자금·정식 재고 결정 |
| `QUEST-01` | Cube NPC의 적 1킬·생환 시험 의뢰 | `ACTIVE` | `CODE` | `PROTOTYPE` | 진행 §30·52 | 공통 E로 수락, Player 귀속 처치, committed `Extracted` 뒤 보고 가능, NPC 보고로 완료; ordinary·Recovery exact 저장, 보상 없음 | 퀘스트 규칙·보상·다중 의뢰 schema 또는 관련 상호작용·사망·정산 경계 변경 |
| `INFO-01` | U 정보창과 누적 기록 | `ACTIVE` | `CODE` | `PROTOTYPE` | 진행 §31·52 | 캐릭터·기록·사전·의뢰·업그레이드 5탭; 기존 원본 읽기, 누적 기록은 단일 권위 소유 후 ordinary·Recovery exact 저장; 업그레이드는 미구현 표시 | 정보 항목·기록 종류·도감 해금·업그레이드 규칙 변경 |
| `ITEM-UI-01` | 아이템 tooltip·가격·수량·탄창 배지 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §27·38·40~45·48~50·53 | context·수량·장착·drag·R; runtime 장전탄 tooltip; 하단 W1~W3·탄창+예비탄 즉시 갱신 | 표시 필드나 UI 배치 직접 변경 |
| `PIXEL-01` | 3D 픽셀아트 시험 효과 | `DISABLED` | `PLAY` | `PROTOTYPE` | 진행 §15 | 사용자 요청으로 비활성 | 사용자가 재사용을 요청할 때만 |

## 확인된 실제 공백과 결정 대기

이 표는 현재 확인된 후보이며 완전한 백로그가 아니다. `DECISION`은 사용자 결정 전 구현하지 않는다.

| ID | 상태 | 실제 공백 | 선행조건·금지선 |
|---|---|---|---|
| `GAP-POI` | `ABSENT` | 접근 가능한 POI·건물 내부·랜드마크 없음 | Spawn→Portal 경로와 별도 접근 가능성 검증 |
| `GAP-COMBAT` | `DECISION` | Player 시험 탄약·3발 탄창·2.5초 장전은 연결됨; 정식 탄종·AI 탄약·무기군별 장전·반동·탄퍼짐·방어 미정 | 현재 시험값을 최종 밸런스로 확대하지 않고 사용자 전투 규칙 결정 뒤 진행 |
| `GAP-AI-TACTICS` | `DECISION` | 엄폐·도주·저격·분대 전술 미구현 | `AI-01`을 폐기하지 않고 다음 전술 단계로 확장 |
| `GAP-LOSS` | `DECISION` | provenance 기반 선별 손실 미정 | 현재 전체 보존/전체 소실 정산을 임의 변경하지 않음 |
| `GAP-EXTRACTION` | `DECISION` | 최종 탈출 대기 시간·피격 중단·암전 중 사망 판정 미정 | 현재 시험 포탈의 즉시 생환·피해 차단·자동 기지 정산은 임시 유지 |
| `GAP-SAVE-POLICY` | `DECISION` | 정식 저장 슬롯·자동 저장 정책 미정 | 현재 단일 슬롯 ordinary/Recovery를 미완성으로 오해하지 않음 |
| `GAP-BASE-CONTENT` | `DECISION` | 시험 상인·의뢰 이후의 기지 성장·정식 경제·제작·치료·정식 퀘스트 범위 미정 | GDD에서 다음 우선 기능과 정식 범위를 결정한 뒤 진행 |
