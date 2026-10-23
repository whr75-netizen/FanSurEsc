# 현재 구현·검증 상태

**마지막 갱신:** 2026-10-05
## 판정 규칙

- 직접 확인 → 이 표 → 최신 증거 → 과거 이력 순으로 판정한다. 차이는 원인을 확인한 뒤 쓰기 허용 작업에서 갱신한다.
- `ACTIVE`는 재개방 조건·회귀가 없으면 다시 다루지 않는다. 상세 이력은 진행 문서에 남긴다.

### 상태 표기

- 구현: `ACTIVE` 사용 중, `PARTIAL` 일부만 구현, `ABSENT` 미구현, `DISABLED` 의도적 비활성.
- 검증: `USER` 사용자 확인, `PLAYER` 빌드, `PLAY` 실제 흐름, `CALL` Play 호출, `CODE` 정적 확인, `UNVERIFIED` 미검증, `BLOCKED` 차단.
- 범위: `PROTOTYPE` 시험·그레이박스, `PRODUCTION` 정식 범위.

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
| `ENVIRONMENT-01` | GDD §10.8~10.9·14.1; 실내 비차단 GDD §7.7 |
| `CHARACTER-RENDER-01` | GDD §14.1.4 |
| `RAID-01`, `SAVE-01` | 게임플레이 계약 §4.1·4.8·4.9, `GAME_FLOW.md` §6~8, GDD §2.6~2.7·11 |
| `QUEST-01` | 게임플레이 계약 §4.4·4.7~4.9·5, GDD §2.3·3.3·8.5.4·9.5·10.5.4·12.2.5 |
| `INFO-01` | 게임플레이 계약 §4.9·5, GDD §3.4·9.1·10.2·10.15 |
| `PIXEL-01` | GDD §14·15.5; Tools/PixelDesk; 맵 연구 D10·D12 |
| `SPAWN-01` | 게임플레이 계약 §4.3, `GAME_FLOW.md` §5, GDD §7.8~7.11, 개발계획 §14.1 |
| `POI-01` | 게임플레이 계약 §4.3, GDD §7.5·7.7·7.10, 개발계획 §14.1 |
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
| `BOOT-01` | 최초 실행·메인 메뉴·공통 로딩 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §12·53·95 | `InitialLoadingScene → MainMenuScene`; New/Load는 3개 슬롯 중 하나를 고른 뒤 공통 로딩으로 기지 진입 | 시작 흐름·슬롯 선택·해당 씬/Manager 변경 |
| `SHELL-01` | 게임플레이 Player 셸 영속성 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §1·9·13·100 | Player·실루엣 외형·Camera·HUD·Inventory UI·EventSystem 동일 인스턴스 왕복 | 셸 계층·참조·생성/종료 경계 직접 변경 |
| `TRAVEL-01` | `GameMap1 ↔ GameMapTest` 직접 이동 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §1·14·20 | 시작 로딩 씬을 거치지 않고 기존 Player를 SpawnPoint로 이동 | `DirectSceneTravel`, Spawn, 도착 완료 경계 직접 변경 |
| `TRANSITION-01` | 검은 전환과 입력·피해 잠금 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §20·21 | fade 동안 이동·공격·무기·인벤토리·상호작용·저장·피해 차단 후 복원 | 전환 잠금 소유자나 복원 순서 직접 변경 |
| `INPUT-01` | Escape·입력·키 설정 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §21·46~48·53·69 | Base pause/Raid non-pause; Main/ESC 리바인딩·행별 보조키 해제/복원; 낮/밤·맑음/비 환경 시험; 별도 설정 파일·legacy 이관 | 입력·scene 또는 설정 schema·migration·복구 변경 |
| `INTERACT-01` | 공통 E 상호작용 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §3~5·36·91 | 최근접 하나, 열린 Chest 유지, 닫은 뒤 재선택, 거리 이탈 공통 닫기; 바닥 아이템도 같은 최근접 E 후보; 고정 기지 NPC는 solid `Obstacle`로 안정 정지 | `PlayerInteractor`, 거리·취소 계약 또는 고정 NPC Collider·태그 직접 변경 |
| `ACTION-01` | Player 공용 행동시간 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §37~39·48~51·53 | 한 번에 1개; External은 이동취소, Self는 이동허용; 완료·취소 불변 결과 1회 통지 | 원형 UI·음식 연결 |
| `MOVE-01` | Player 이동·달리기·8방향 회전 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §143 | Camera축·CharacterController; .2m턱/문/벽/씬왕복; 물리키 미검증 | 이동·Animator·외형 참조 변경 |
| `CAMERA-01` | 영속 Camera 줌·회전 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §142·146·167 | 30°/350°;B34 native1배·작은뷰 줌제약 | 씬이탈·입력·높이 변경 |
| `ENVIRONMENT-01` | 시간·날씨 | `PARTIAL` | `CALL` | `PROTOTYPE` | 진행 §55~88·94·101·108~110·121~126 | 11키 낮밤·8초 구름/주광/안개→0.75초 비; 비차단·웅덩이·큰 식생 시험장·shadow/cookie·로컬광 | 시각 승인·실내 안개·날씨 저장·풍향·GPU Profile·Transparent 차폐/합성 |
| `CHARACTER-RENDER-01` | 3D 픽셀 캐릭터 렌더 | `PARTIAL` | `PLAY` | `PROTOTYPE` | 아래 §241 | 348활성;527 OFF;530얼굴×.72확인·회색미확정 | 반복회색사건/경계설계·내부색·PlayerFPS 미검증 |
| `ITEM-01` | ItemDatabase·grid 인벤토리·회전·장비·HUD | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §12~13·38·40~45·48·50·53·89~95·105 | grid·stack·가방·장전탄·Save v7·저작창; ID 13 1×1 갑빠(방어 20%·육각); 바닥 drop/E, 일반 전환 삭제·Active Raid 복원 | item/grid/장비/world-item 저장 계약 변경 |
| `COMBAT-01` | 시험 총기 공격·탄약·피해·사망·효과음 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §16·48·51·105 | 체력 1000·정수 계산·공격력 10단위·총 피해 350; 갑빠 방어 1당 최종 피해 1% 감소 | 탄종·AI 탄약·무기군 장전·반동·탄퍼짐·관통·피해 유형·조준 결정 |
| `AI-01` | 근접·원거리 적 AI 1단계 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §19·67·117 | 순찰·감지·추적·LOS 공격·총성 조사; 좀비 순찰3/전투6.8 | 엄폐·도주·저격 단계 요청 |
| `CORPSE-01` | 적 사망과 공용 시체 전리품 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §20 | AI·공격·피격 정지, root·렌더 유지, 기존 Chest UI 사용 | despawn·정식 드롭·씬 재진입 저장 추가 |
| `MAP-01` | 도시·진입형 건물 | `PARTIAL` | `CALL` | `PROTOTYPE` | 진행 §203·205; Tools/PerfectPixelUniform/BUILDING16.md | N32갈색물체·전등범위복구 | 미술·캐릭터·유리 |
| `MAP-ARRIVAL-01` | 원정 맵 도착 안전 gate | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §32·34 | Ready 뒤 공개; Invalid는 covered 기지 복귀, 불가 시 잠금 보류 | readiness·도착·rollback·redirect 변경 |
| `SPAWN-01` | 도심 시험 적·상자 seed 배치 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §33~34·67~68 | spawn catalog가 Chest 1·Enemy 2 prefab을 stable manifest 위치에 생성·등록; POI·NavMesh·Recovery 복원 검증 | catalog·prefab·배치·registry·world hash 변경 |
| `POI-01` | 의료·건물용도 | `PARTIAL` | `CALL` | `PROTOTYPE` | 진행 §111·160~161 | 의료유지;상가30개/8크기·3평면 | 완성설비아트·다중보상 |
| `LOOT-01` | seed 기반 시험 LootTable | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §34·67 | Fresh 결정적 누적확률 1회·최대 1개·잔여 확률은 빈 결과; Resume grid, 미지정은 초기값 | 다중 roll·수량·희귀도·위험 예산 추가 |
| `BASE-01` | 기지 Chest·가구 영속성 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §18 | stable ID별 grid와 중첩 아이템, 왕복·backup 복원 | 배치 가능한 가구나 layout migration 추가 |
| `RAID-01` | 기지/원정 Escape·생환·사망·포기 결과 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §21·35·95 | 생환은 자동 기지 정산; 명시적 포기만 `Abandoned`; Active Raid의 `주 메뉴`는 결과 없이 exact 저장 후 같은 슬롯 Resume | 메뉴·결과·중단 정책 변경 |
| `SAVE-01` | 3슬롯 save·원정 Recovery·정산 | `ACTIVE` | `PLAY` | `PROTOTYPE` | 진행 §22~23·48·52~53·73·95 | 활성 슬롯별 ordinary/Recovery; slot 1 legacy; marker 우선 Resume/정산; Base·Raid 주메뉴 저장 gate | 슬롯 수·schema·저장 시점·정산/복구 경계 변경 |
| `MERCHANT-01` | Player Gold/Silver와 무지갑 시험 상인 | `ACTIVE` | `USER` | `PROTOTYPE` | 진행 §26 사용자 확인·순수 거래 11경로 | 상인 자금 없음, 판매 sink, 이전 성공 뒤 정산, 실패 rollback | 가격 정책·상인 자금·정식 재고 결정 |
| `QUEST-01` | Cube NPC의 적 1킬·생환 시험 의뢰 | `ACTIVE` | `CODE` | `PROTOTYPE` | 진행 §30·52 | 공통 E로 수락, Player 귀속 처치, committed `Extracted` 뒤 보고 가능, NPC 보고로 완료; ordinary·Recovery exact 저장, 보상 없음 | 퀘스트 규칙·보상·다중 의뢰 schema 또는 관련 상호작용·사망·정산 경계 변경 |
| `INFO-01` | U 정보창과 누적 기록 | `ACTIVE` | `CODE` | `PROTOTYPE` | 진행 §31·52 | 캐릭터·기록·사전·의뢰·업그레이드 5탭; 기존 원본 읽기, 누적 기록은 단일 권위 소유 후 ordinary·Recovery exact 저장; 업그레이드는 미구현 표시 | 정보 항목·기록 종류·도감 해금·업그레이드 규칙 변경 |
| `ITEM-UI-01` | 아이템 tooltip·가격·수량·탄창 배지 | `ACTIVE` | `CALL` | `PROTOTYPE` | 진행 §27·38·40~45·48~50·53 | context·수량·장착·drag·R; runtime 장전탄 tooltip; 하단 W1~W3·탄창+예비탄 즉시 갱신 | 표시 필드나 UI 배치 직접 변경 |
| `PIXEL-01` | 3D→픽셀·Unity 조명 | `PARTIAL` | `CALL` | `PROTOTYPE` | 진행 §159·165·205 | N32:2px·447셀 실제그림자 | 실내GI·일반world·미술 |

## 확인된 실제 공백과 결정 대기

이 표는 현재 확인된 후보이며 완전한 백로그가 아니다. `DECISION`은 사용자 결정 전 구현하지 않는다.

| ID | 상태 | 실제 공백 | 선행조건·금지선 |
|---|---|---|---|
| `GAP-COMBAT` | `DECISION` | 시험 탄약·3발·장전·기본 % 방어 연결; 탄종·AI 탄약·무기군 장전·반동·탄퍼짐·관통·피해 유형 미정 | 시험값을 최종 밸런스로 확대하지 않음 |
| `GAP-AI-TACTICS` | `DECISION` | 엄폐·도주·저격·분대 전술 미구현 | `AI-01`을 폐기하지 않고 다음 전술 단계로 확장 |
| `GAP-LOSS` | `DECISION` | provenance 기반 선별 손실 미정 | 현재 전체 보존/전체 소실 정산을 임의 변경하지 않음 |
| `GAP-EXTRACTION` | `DECISION` | 최종 탈출 대기 시간·피격 중단·암전 중 사망 판정 미정 | 현재 시험 포탈의 즉시 생환·피해 차단·자동 기지 정산은 임시 유지 |
| `GAP-SAVE-POLICY` | `DECISION` | 3슬롯과 기지·Active Raid 주메뉴 자동저장은 현재 확정; 수동 저장 범위·클라우드·migration 지원 기간 미정 | 현 슬롯/Recovery를 우회하는 별도 저장 경로를 만들지 않음 |
| `GAP-BASE-CONTENT` | `DECISION` | 시험 상인·의뢰 이후의 기지 성장·정식 경제·제작·치료·정식 퀘스트 범위 미정 | GDD에서 다음 우선 기능과 정식 범위를 결정한 뒤 진행 |
