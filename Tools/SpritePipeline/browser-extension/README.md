# ChatGPT 구독 웹 이미지 연결

이 Chrome Manifest V3 확장은 로그인된 `https://chatgpt.com/images/`에 로컬 실행기의 프롬프트를 한 번 제출하고, 새로 표시된 이미지 파일 한 장을 로컬 서버에 전달합니다. API 키·텍스트 AI 지휘·프레임별 AI 검토를 사용하지 않습니다. 구독 권한과 이미지 모델은 해당 웹 계정 및 페이지가 결정하며, 확장이 특정 모델이나 사용량을 보장하지 않습니다.

## 현재 검증 범위

- 실제 로그인된 페이지에서 관측: `div#prompt-textarea[role=textbox][contenteditable=true]`, `#composer-submit-button`, `main` 내부 `image-*` 컨테이너의 `img`와 한국어 `생성된 이미지` 대체 텍스트, 이미지 URL의 `https://chatgpt.com` 출처.
- 현재 확장 코드는 위 관측을 바탕으로 작성했습니다. **확장 설치 후 실제 프롬프트 제출·생성 완료·원본 파일 저장까지는 검증하지 않았습니다.** 입력 이벤트의 사이트 반영, 페이지 전환, 이미지 완료 판정 및 파일 수신은 최초 연결 검증 대상입니다.
- 새 이미지 완료 조건은 기준 목록에 없던 이미지, 로드 완료, 양쪽 자연 해상도 256 px 이상, 같은 URL·해상도 3초 유지입니다. 이는 기술적 완료 추정이며 미술 검증이나 원본 해상도 보증이 아닙니다. 페이지가 중간 생성 이미지를 같은 조건으로 노출하면 완료 판정을 보강해야 합니다.
- 제출 전에 기존 이미지 URL과 `image-*` 컨테이너 ID를 기록하여 기존 컨테이너의 지연 로드·URL 변경을 제외합니다. 제출 이후 과거 이미지 컨테이너가 새로 삽입되면 새 결과로 오인할 가능성은 남아 있습니다. 실제 페이지의 요청별 결과 컨테이너를 관측해 결합하기 전 다중 요청·동일 탭 병렬 실행은 지원하지 않습니다.
- 영어 UI·변경된 DOM·외부 CDN에는 자동 대체 선택자를 시도하지 않고 실패하거나 15분 뒤 종료합니다.

## 설치와 사용

1. Chrome의 `chrome://extensions`에서 개발자 모드를 켜고 **압축해제된 확장 프로그램을 로드합니다**로 이 폴더를 선택합니다.
2. ChatGPT에 로그인하고 로컬 Sprite Pipeline 프로그램을 실행합니다. 확장을 설치하기 전에 열려 있던 탭은 새로고침해야 합니다.
3. 실행기가 작업별 새 탭을 엽니다. 형식은 `https://chatgpt.com/images/#sprite-pipeline=BASE64URL(JSON)`이며 JSON에는 `{id,token,port:8765}`만 들어갑니다. 프롬프트는 인증된 로컬 claim 응답에서 받습니다.
4. 확장은 URL의 작업 토큰을 제거한 뒤 제출합니다. 제출 직전 상태를 세션 저장소에 기록하며 새로고침·탐색 이후에는 결과 대기만 재개합니다. 서버가 이미 제출되었다고 응답하는데 해당 탭의 세션·기준 목록이 없으면 실패로 종료합니다. 브라우저 자체를 종료하면 세션 복구는 보장하지 않으며 자동 재제출하지 않습니다.
5. 파일 수신이 끝나면 로컬 프로그램이 Grok 영상과 후처리를 이어갑니다. 확장은 성공·실패 상태만 보여 줍니다. 일반 ChatGPT 탭에는 작업 요청·DOM 변경을 하지 않습니다.

설치·로그인·새 생성은 이 코드 작성 과정에서 실행하지 않았습니다. 로그인 문제와 제출 후 불확실한 실패는 새 생성 요청으로 자동 복구하지 않습니다. 같은 작업의 링크를 여러 탭에 열지 않도록 실행기가 관리해야 하며, 서버 claim은 중복 소유권 획득을 차단해야 합니다.

## 로컬 프로토콜

서비스 워커만 `http://127.0.0.1:8765`에 JSON을 전송합니다. 모든 요청에는 `id`, `token`, 실제 송신 탭의 `tab_id`를 붙입니다. 서버는 최초 claim 탭을 고정하고 이후 다른 탭의 claim/event/result를 거절해야 합니다. URL에서 전달된 임의의 탭 ID는 사용하지 않습니다.

| 요청 | 추가 필드 | 응답/역할 |
| --- | --- | --- |
| `POST /api/browser/claim` | 없음 | `{prompt,status}`. 작업 소유권을 한 번 획득합니다. |
| `POST /api/browser/event` | `stage: submitted/progress/failed`, `detail` | 제출·대기·실패 기록. JSON 응답이 필요합니다. |
| `POST /api/browser/result` | `image_base64`, `mime`, `source_url` | 최대 32 MiB 이미지 한 장. JSON 응답 후 저장 완료로 표시합니다. |

이미지 bytes는 화면 DOM이 노출한 같은 출처 URL 또는 그 페이지의 blob에서만 읽습니다. 외부 리디렉션은 거절합니다. 쿠키 값·내부 앱 상태·비공개 API를 읽지 않으며 쿠키를 로컬 서버로 복사하지 않습니다. 파일 응답이 차단되면 중단합니다. `source_url`은 페이지 origin/path만 포함하고 이미지 서명 URL·검색 인자·토큰 fragment를 저장하지 않습니다.

`chrome.storage.session`에는 탭별 작업·토큰·제출 여부·기준 이미지 URL 및 컨테이너 ID의 SHA-256 해시를 보관합니다. 일반 웹 스크립트는 이 저장소와 확장 메시지를 직접 사용할 수 없습니다. 서비스 워커는 탭별 메시지를 직렬화하여 제출 예약과 결과 전달이 겹치지 않게 합니다.

## 변경 전 확인

```powershell
node --check Tools/SpritePipeline/browser-extension/background.js
node --check Tools/SpritePipeline/browser-extension/content.js
node --preserve-symlinks-main Tools/SpritePipeline/browser-extension/tests/background.test.cjs
```

mock 테스트는 모든 POST의 탭 연결, 다른 탭 차단, 제출한 세션 소실 시 재생성 금지, 정상 세션 복구, 동시 제출 예약과 단일 결과 전달을 재현합니다. 파일 경로 realpath가 제한되는 Windows 샌드박스에서는 `Get-Content -Raw <파일> | node --check`로 같은 문법 검사를 실행할 수 있습니다.

문법·mock 검사는 실제 웹 연결 성공을 증명하지 않습니다. 실제 연결 검증은 로그인된 전용 탭 한 개에서 새 생성 한 번과 최종 파일 수신을 관측해야 합니다. 선택자 실패 시 관측 없이 여러 버튼·Enter·재생성을 차례로 시도하지 않습니다.
