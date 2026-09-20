# 2026-09-20 Unity 종료 후 복구 확인

## 결과와 보존 범위

- `[현재]` Unity 6000.5.9f1은 16:26경 네이티브 크래시 후 재시작했다. 코드·상가 에셋·씬 참조는 남아 있고, 최신 복구 기지씬과 저장된 기지씬은 바이트 단위로 동일하다. 확인된 파일 손실이 없어 이전 버전으로 덮어쓰지 않았다.
- `[보존]` `LocalOnly/Recovery/20260920-editor-recovery/`에 두 원본 씬, Unity 복구씬, 재시작 후 Temp 백업, 이전 Editor 로그, crash.dmp, 복구 전 변경/도시 의존 파일 ZIP과 SHA256 목록을 보존했다. 로그 원문은 시작 인자를 포함하므로 Git에 넣지 않는다.
- `[요청 범위]` 미커밋 도심 구현과 필요한 에셋을 명시 경로로 로컬 기록한다. 원격 push 없음. 캐릭터·책상·상가 비율 재설계는 수행하지 않았다.

## 복구 후보 대조

| 후보 | 관측 | 결정 |
|---|---|---|
| `Assets/_Recovery/0 (2).unity` | 384,468B, 재시작 후16:27:46; 아래 GameMap1과 동일 SHA256 | 보존, 덮어쓰기 불필요 |
| `Assets/Scenes/GameMap1.unity` | 384,468B,14:22:52 | 현재 저장본 유지 |
| `Temp/__Backupscenes/0.backup` | 8,776B,16:27:46; 재시작 이후 생성 | 크래시 직전 작업으로 취급하지 않음 |
| `_Recovery/0.unity`, `0 (1).unity` | 8월의 오래된 복구씬 | 현재 작업에 적용하지 않음 |

동일한 기지씬 SHA256: `8248C9E89CD12EE5B9D788AFE7AF576FF9AAA67E3CD3F0AA9ECD757A3A1889B3`.
도심 씬 SHA256: `9AABD2AF90A15B54CEEDB08C3BC4C8326A4CFFA0F9E90244D4D1EFE703A68B7B`.

## 종료 원인: 확인과 미확정

- 이전 로그17856행 부근: `dt > 0` assertion, `PlayerMovement.Update → StepMove`의 `deltaTime` 인자 예외가 기록됐다. 실제 숫자는 로그에 없다. 코드의 검사 조건상 음수/NaN/Infinity 중 하나이며 어느 값이었는지는 확정할 수 없다.
- 그 뒤 `Native Crash Reporting`, `Crash!!!`; 마지막 managed stack은 `UnityEngine.Event.get_keyCode → UnityEditor.GUIView.ProcessEvent`이다.
- 이동 인자 예외가 네이티브 크래시의 직접 원인이라는 증거는 없다. 임의 deltaTime 대체나 예외 무시를 근본 해결로 넣지 않았다. 공개 검색에서도 이 버전과 동일한 원인을 확인하지 못했다.
- crash 원본: `%LOCALAPPDATA%/Temp/Unity/Editor/Crashes/Crash_2026-09-20_072627647/`. Bug Reporter의 report_cancelled 기록이므로 신고가 제출됐다고 볼 수 없다.
- 재발 원인 수정은 미완료다. 재발 시 새 dump와 비정상 deltaTime의 실제 값·직전 Editor 상태를 비교해야 한다. 이번 복구 관측을 크래시 해결 증거로 확대하지 않는다.

## 실제 실행 증거

- `[Play Mode 호출 확인]` 저장된 GameMap1에서 기존 RaidSession.TryBeginRaid로 GameMapTest 진입. 비활성 Editor가 frame2에 머물러 기존처럼 제한된 Editor 프레임 진행24회를 사용했다. 물리 키보드 시험은 아니다.
- `readback.json`: seed1462661998, 건물115개, 상가30개, Supermarket/Cafe/RetailShop, NavMesh 준비true, 누락 스크립트0·깨진 직렬화 참조0.
- 기지에서 도심까지 Player와 Camera의 EntityId 동일. 기존 정상 카메라30°/45° 유지. Console Error/Exception/Assert0.
- 상가 모든 방·서비스문·계단 이동은 코드 변경이 없어 기존 A27/A28 증거를 재사용했다. 이번에 반복 완주했다고 주장하지 않는다. 생성된 도심은 런타임 파생 결과로서 Play 종료 시 사라지는 것이 정상이며 씬 에셋에 구워 넣지 않았다.
- 확인 후 Play를 종료해 저장된 GameMap1 편집 상태로 돌렸다. 현재 상태가 복구본과 같으므로 불필요한 SaveScene/에셋 재생성은 하지 않았다.

## 남은 작업

상가의 가구 수가 면적에 비례하지 않는 문제, 큰 머리·짧은 다리 캐릭터와 실물 가구의 체감 비율, 지원공간 비중 및 최종 픽셀 표현은 기존 미완료 사항이다. 이번 보존 커밋은 디자인 합격이나 이 문제들의 해결을 뜻하지 않는다.
