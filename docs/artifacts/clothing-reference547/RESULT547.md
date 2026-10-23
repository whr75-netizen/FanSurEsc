# 547 — 단순화 전 경계 구간 참조 복구

제품 파일 변경은 `ClothRegion524.cs` 하나다. `BoundarySpan543.Groups`가 단순화한 Curves에서 구간 끝을 다시 추론하던 입력을 Source로 바꿨다. 면적·지지 조건·선택 비용·544 compact cut·색·UV·깊이·OwnerLines 셰이더는 유지한다. `UseSimplifiedSpanReference546`은 이전 동작을 같은 실행에서 재현하는 진단 스위치이며 정상 span 경로는 false다. 기존540/Off 모드와 제품 기본 OFF는 보존했다.

## 완료한 검증

- 저장81포즈×3옷슬롯+얇은끝8개=251입력. 컴파일된 기존 선택기가 저장543 마스크와 모두 일치함을 먼저 확인했다. 참조 변경 후23입력,31셀(추가18/제거13)이 달라졌다.34/43/44/50 및 정상끝8개는 동일하다.65소매는 유지하고 같은 포즈 하의1셀만 달라졌다.
- 실제 Walk64~70의7쌍, 이어 전체0~80의81쌍을 각각 한 번 실행했다. OLD543/544와 FIX547는 같은 포즈·빛·카메라·변형 정점 해시를 쌍마다 확인했다. 저장 예측과 실제243부위마스크가 모두 일치했다.
- Walk68의 왼팔 소매(200,73)/(200,74), source11300/11298 제거. 안쪽(201,73)/(201,74)는 기존 OwnerLines가 선색을 적용한다.67/69는 그대로다.6~11/16의 이전 밝은 좁은 돌출은 같은 규칙으로3셀 구간 채움 또는 생략이 선택된다. 특정 좌표·팔·포즈 조건 없음.
- 최종 활성 옷 영역 밖 쓰기0, unsupported packet0, invalid owner0. 모든 실제 마스크의 foreground8-connected 성분 수 및 background4-connected hole 수는 전후 동일하다. 이는 형태 품질 전체 통과를 대신하는 기준은 아니다.
- 실제8비트 화면 변화는18프레임·266화면픽셀. 얼굴/눈·머리의 화면 차이0.51번 머리 float 두 표본은13.0~18.7e-6 차이가 있지만 실제 PNG는 전부 동일하다. 이 미세 차이의 산술 원인을547 때문/아님으로 확정하지 않는다.
- 같은 표면·UV의 색차47표본은 PREPARED 동일, POSTLINE에서 최초 변화. 변경 마스크1~2셀 이내의 기존 외곽선 재분류다. 새 RGB 보정 없음.
-76번(225,106)은 기존 Body0(depth14.214467, source3554)를 새 선택된 겉옷(depth13.899133, source11667)이 가린다. 새 packet0, 실제 native 표면이 공급됐다. 더 앞의 옷 영역 선택으로 바뀐 소유권이며 손/피부에 알고리즘을 적용한 것이 아니다. 이 셀은 시각 비교에 숨기지 않았다.
- 양팔81순서 비교와 변경23부위 확대에서 이번 추가 변화로 생긴 분리점·구멍·정상끝 소실은 관측하지 않았다. 이미 남아 있던 내부 명암/선색 변화와 손끝은 전체 해결로 판정하지 않는다. 회전/다른카메라/다른 모델/다른 애니메이션까지 검증한 결과가 아니다.

## 시간·전달·복원

전체 loop skyHour3.1476202로 고정. 과거543 촬영의 시간/배경과 다르며 밝기를 맞추지 않았다. 비교 양쪽은 동일하다.81프레임 모두 보존, WebP16/17ms 및 GIF10ms 단위 시간 근사 합계1350ms. 보간 축소 없이 전신 정수좌표 crop. GIF1,878,993B, WebP1,282,638B. Library403 재시도 없이 로컬 제공.

이번 고정순서 품질 캡처의 선택기 중앙값2.2511→2.2360ms, p955.7621→3.4923ms. geometry18.0667→18.0652ms. core RenderFrame353.6486→341.1058ms는 기존 runtime readback을 포함하며 추가 저장/PNG는 제외된다. 새 최적화 성과나 PlayerFPS로 해석하지 않는다. 기존544 결과보존 최적화는 유지했다. 정상운동을 정지캐시하거나 시간필터로 가리지 않았다.

자동 복원: 입력/Animator/clock=true. 종료 후 직접 Edit/비정지/cloth·spans·compact OFF/capture0/backgroundfalse/sceneDirtyfalse. 초기import 요청은 domain reload 동안 응답timeout이었으나 재import하지 않고 후속상태/컴파일을 확인했다. 첫 인접capture 호출은 FaceState524 helper 누락으로 컴파일 단계 미실행; output 부재 확인 후 helper 포함 호출 한 번이 실제7쌍을 수행했다. 동일 runner 중복 시작 없음.

별도 미해결: 기본 제품은 여전히 옷OFF; Body0 얼굴소유권, 얼굴회색 사용자 관측(이번 미재현), 내부명암, 머리511/513·212ms 비용,543 동률 창의 방향 의존성, 전체 실시간 성능. 본 수정은546 정보손실 원인에 대한 검증된 한정 수정이며 전신 픽셀아트 완성 선언이 아니다.

## 증거 위치

- `STORED_DIFF547.json`, `StoredGate/`: 실제 native 선택기 결과. 동적 JsonUtility가 nested row를 직렬화하지 않은 원 `STORED_GATE547.json`을 덮어쓰지 않고 mask에서 diff를 회수했다.
- `Adjacent547_RESULT547.json`, `FullLoop547_RESULT547.json`, `NATIVE547.json`, `LINE_RELATION547.json`, `BODY0_DIFFERENCE547.json`, `TOPOLOGY547.json`.
- `FULL_WALK547.webp`, `FULL_WALK547.gif`, `FullLoop547_LATEST.png`, `BOTH_ARMS547_0..4.png`, `CHANGED_REGIONS547.png`.
- `RESTORED_ADJACENT547.json`, `RESTORED_FULL547.json`; 상세 원인546은 이전 폴더에 그대로 보존.
- `DISK547.json`: C여유50.75GiB, Codex124.01GiB, W/E_UnityValidation_01 76.04GiB, Current472 14.07GiB. 삭제/압축/이동0. 최근24h 수정파일2.68GiB는 현재크기이지 측정 증가량이 아니다.
- [실제 파이프라인](CHARACTER_PIXEL_PIPELINE.md): 부위 레이어/실행15단계/버퍼·쓰기계약/현재 목표와의 차이.
