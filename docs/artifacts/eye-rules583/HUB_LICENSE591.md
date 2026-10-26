# 591 Hub 경로·라이선스 재대조

**Hub가 실제 사용하는 프로젝트 등록5개를 지원 CLI로 수정했습니다. 최근 공식CLI 조회에서는 Unity Personal을 포함한 활성 라이선스2개가 확인됐습니다. 새 라이선스 활성화를 요구할 상태로 단정했던 안내는 정정합니다.** 이번 조사에서는 Editor를 다시 실행하거나 촬영하지 않았습니다.

## Hub의 ‘프로젝트를 찾을 수 없음’

- 실행 중 Hub는 `C:\Program Files\Unity Hub\Unity Hub.exe`의 UNPACKAGED 프로세스입니다. 자식 프로세스의 user-data-dir은 `C:\Users\15352\AppData\Roaming\UnityHub`입니다. Windows 알려진AppData와 환경변수도 같은 위치입니다.
- MSIX 3.22.4 설치도 있지만 현재 Hub 프로세스에는 그 패키지ID가 없습니다. 확인한 MSIX LocalCache에는 Preferences/user-settings만 있었고 현재 프로젝트 목록을 제공하는 저장소가 아니었습니다.
- **옛 `projects-v1.json`에는15352경로가 있었으나, 실행 중 Hub의 `hub.db` projects 테이블5개는 여전히JG경로였습니다.** 따라서 JSON·파일 존재·CLI의 경로 정보만으로 실제 화면 등록이 정상이라고 보고한 것은 부정확했습니다.
- 현재 Hub 로그(PID8580, 08:51·09:06UTC)에도 `C:\Users\JG\Documents\work\Fantasy Survival Escape Game`이 없다는 경고가 확인됐습니다. 사용자 관측과 일치합니다.
- 복원 폴더·Assets·manifest·ProjectVersion과 이전등록 버전이 모두 일치하는5항목만 공식 `unity projects add`, `projects pin`, `projects remove --force`로 교체했습니다. 이 remove는 등록만 제거하며 디스크의 프로젝트 파일은 삭제하지 않습니다. 메인 프로젝트의 즐겨찾기true와 나머지false를 보존했습니다.
- 수정 후 실제 projects 테이블은 메인, 복사본3개, Sdoku & Logic 모두 `C:\Users\15352\Documents\work\...`이며, 대응하는JG항목은 없습니다. **읽기 전용SQL로 전후를 확인했으며 SQL쓰기·DB직접편집·앱종료/재시작은 하지 않았습니다.**
- 화면 조작·스크린샷 검사는 하지 않았으므로 화면 갱신을 완료했다고 주장하지 않습니다. 옛 항목이 보이면 Hub의 Projects탭을 다시 선택하거나 Hub창에 포커스를 주어 목록을 새로고침하면 됩니다. 현재 로그도 focus refresh를 명시합니다. 앱 재시작이나 재설치는 요청하지 않습니다.

## 이전exit0과 이번198

| 항목 | 이전 성공 로그 | 재부팅 후 실패 로그 |
|---|---|---|
| 실제 시각UTC | 03:37:52~03:40:02 | 08:49:29~08:49:31 |
| 파일 | unity-after-login.log, 새로 생성된396,369바이트 | unity-validation590.log, 별도 생성6,396바이트 |
| 실행 파일/빌드 | `...\6000.5.9f1\Editor\Unity.exe`, b57deb96f08d | 동일 경로·빌드 |
| 프로젝트 | `C:\Users\15352\Documents\work\Fantasy Survival Escape Game` | 동일 경로, 변경 성공 메시지까지 기록 |
| OS/사용자 | Windows11 26300 x64, LicenseClient-15352 | 동일 OS·IPC사용자, 기계표식 해시도 동일 |
| 배치 인자 | -batchmode -quit -projectPath -logFile | -batchmode -force-d3d11 -screen-width960 -screen-height544 -executeMethod Driver590.Run 등 |
| 라이선스 클라이언트 | 이미 실행 중인Hub 클라이언트(PID8664) | Editor가 시작한 번들 클라이언트(PID23200) |
| 클라이언트 버전 | 1.18.3+d7ffd15 | 동일 |
| 인식한 권한 | Unity Personal / Assigned / Unlimited 그룹 | 일치하는 entitlement0, headless권한 없음 |
| 실제 진입 | 엔진·AMD RX9070XT D3D11 초기화, Csc/스크립트 컴파일·AssetRefresh·정상종료 | 엔진초기화·Driver590.Run 이전 종료 |
| 종료 | 0 | 198 |

이전exit0은 잔존로그나다른프로세스 결과가 아닙니다. 생성시각·로그Date·새프로젝트경로·엔진/컴파일·종료가 연결됩니다. 다만 ‘C#/shader 오류0’이지 전체Console무오류가 아니며, 당시UVCS client.conf 미설정 예외도 기록돼 있습니다. 그 설정은 변경하지 않았습니다.

두 로그 모두 서명Code10 경고를 무시한 뒤 연결됐으므로 그 경고만으로198원인이라고 보지 않습니다. **토큰 unavailable 메시지도 양쪽에 있습니다. 차이는 성공 때 이미 인식한Personal그룹이 있었고, 실패 때는권한이0이었다는 점입니다.** 실패 실행은 Hub프로세스 시작(08:51UTC)보다 앞섭니다. 직접 확인한 차이는 실행 순서와 연결한 라이선스 클라이언트의 권한 상태입니다. 왜 그 시점에 캐시 권한이 없었는지, Unity ID계정이 같은지까지 과거로그만으로 단정하지 않습니다. 과거로그에 Unity ID계정ID가 없어 현재CLI계정과 완전 대조할 수 없습니다.

프로젝트 찾기 실패와198은 같은 원인이 아닙니다. Hub의 옛등록 오류는08:51이후의Hub로그이며, 08:49Editor는 올바른15352프로젝트경로에 들어간 뒤 라이선스 단계에서종료했습니다. 속눈썹 코드나C#/shader컴파일까지 도달하지 않았습니다.

## 현재와 최소 다음 단계

공식CLI의 후속읽기에서 로그인상태와 active=true, licenses=2를 확인했습니다. 제품은Unity Personal과Asset Store, 둘다Assigned입니다. 로그인·활성화·계약·보호설정은 대신 변경하지 않았고 토큰·키를 출력하지 않았습니다. **앞서 드린새활성화요청은 진행하지 않아도 됩니다.** 현재상태가 실제Editor에도 적용되는지는 아직 재실행하지 않았습니다.

Hub표시에는Projects탭새로고침만 필요할 수 있습니다. 그다음 준비된 전용검증기를1회실행해 실제Editor·렌더를 검증해야 합니다. 이번 조사에서는 중복Editor·재촬영을 시작하지 않았습니다. 기본OFF·제품 커밋131c66d·기존사용자설정·미추적자산을 보존했습니다.

증거는 현재작업폴더의 LICENSE_COMPARISON590.json, LICENSE_DETAIL590.json, HUB_PATH_REPAIR_BEFORE591.json, HUB_PATH_REPAIR_CALLS591.json, HUB_PATH_REPAIR591.json입니다. 마지막파일은 지원CLI 호출과 실제Hub테이블의 전후검증을 담습니다.
