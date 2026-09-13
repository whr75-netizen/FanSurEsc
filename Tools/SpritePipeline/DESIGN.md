# 세 입력 자동 스프라이트 제작기

## 현재 결정 — 2026-09-13

사용자 확정: GPT 이미지 프롬프트, Grok 동작 프롬프트, 최종 프레임 수 세 입력. 생성부터 출력까지 고정 프로그램이 실행하며 중간 AI 검토·재생성·프레임별 시각 심사를 하지 않습니다. 기존 승인 결과는 그대로 두고 새 실행마다 LocalOnly/SpritePipelineRuns에 별도 저장합니다. 생성 서비스의 지연까지 포함한 10초 완료를 보장하지 않습니다.

최신 사용자 확정: 구간별 실행 버튼과 입력 파일 선택, 전체 루틴 ON/OFF, 중단 버튼을 추가합니다. ON일 때만 Inbox 폴더를 1초마다 감시하며 파일 크기/수정시각 2초 안정 후 다음 구간을 시작합니다. 기존 파일은 수동 입력으로 재사용하고 같은 감시 입력은 기록으로 중복 처리하지 않습니다. OFF/중단은 현재 구간의 파일 저장 뒤 다음 구간을 막습니다. 원격 요청 취소는 주장하지 않습니다. 추가 검증 실행·신규 생성·출력물별 판정은 사용자 정정에 따라 하지 않습니다.

기존 Python 모듈·FFmpeg를 직접 호출하는 로컬 프로그램을 선택했습니다. 대화로 단계마다 명령을 만드는 경로는 지연 때문에 제외합니다. **최신 정정: 유료 API 키 경로를 제외하고 구독 경로만 사용합니다.** GPT는 로그인된 Chrome의 이미지 페이지와 전용 확장을 연결합니다. Grok은 기존 구독 로그인 resolver를 사용하며 API key source이면 실패합니다. MCP는 도구 연결 규약이고, 단계 제어 자체에는 LLM이 필요하지 않습니다.

## 실행 계약

`GPT prompt → image adapter → source.png → square chroma canvas → Grok prompt/video adapter → clip.mp4 → selected source PNGs → chroma RGBA → common crop/pixel grid → PerfectPixel source_regions → shared source_palette → PNG atlas/JSON/GIF/WebP`

- GPT 구독 웹 화면을 전용 브라우저 확장이 제어합니다. 모델은 이미지 생성에만 관여하고 외부 단계 제어·프레임 심사를 위한 텍스트 AI 호출은 없습니다. 확장은 새 작업 전용 링크에서만 작동하고 기존 채팅을 자동 수정하지 않습니다. 같은 작업의 제출 표식을 유지해 재접속 시 중복 제출하지 않습니다. 기존 sprite-gen의 generate_image는 타임아웃 시 재생성하므로 사용하지 않습니다.
- 원화의 디자인은 입력 프롬프트가 소유합니다. 실행기는 전신·여백·단색 키 배경 등 영상 입력 제약만 덧붙입니다. Grok prompt도 별도 입력이며 고정 카메라·한 동작 주기·키 배경 유지의 전달 조건만 덧붙입니다.
- 새 생성의 성공 단계는 결과 파일과 manifest로 기록합니다. 후처리 실패가 새 이미지/영상 생성으로 이어지지 않게 합니다. 서버 요청을 보냈지만 응답을 확인하지 못하면 자동으로 새 요청을 보내지 않습니다.
- 영상 기본 길이6초, 해상도720p, 오디오 끔. 모델은 기존 grok-imagine-video-1.5. 직접 관측한 구독 웹 이미지 페이지 제목은 ChatGPT 이미지2.5입니다. 웹에서 제공되는 이미지 모델을 사용하며 GPT Image2.0 버전 고정을 보장하지 않습니다. 새 생성 요청은 아직 실행하지 않았습니다.

## 좌표·시간·색

모든 이미지는 좌상단 픽셀 경계 원점, +x 오른쪽/+y 아래쪽, 단위px입니다. 3D/회전/골격은 이 경로에 없습니다. 원화는 기존 sprite-gen pad_canvas의 정방형 padding을 사용하며 비균일 크기 변경을 하지 않습니다. 영상은 정방형 W=H>=512만 받습니다.

영상 프레임 좌표 p에서 논리512×512 격자 좌표는 q=(512/W)p입니다. 선택된 N장의 binary alpha(>=128)의 합집합 bbox를 공통 crop으로 삼고, crop을 유리수 scale 분모 격자에 정렬합니다. 모든 프레임은 같은 crop·scale·grid·pivot을 사용합니다. 전체145장의 bbox를 쓰던 옛 실험과 달라진 새 실행 정책이며 옛 결과와 동일하다고 주장하지 않습니다.

ffprobe의 실제 frame PTS를 사용합니다. 상대 목표 시각 t_k=kT/N, k=0..N−1에서 t_k 이하의 마지막 원본 프레임을 선택합니다(hold sampling). T는 실제 영상 시간 구간입니다. 1<=N<=16이며 선택이 중복되어 N개의 고유 원본이 나오지 않으면 실패합니다. 각 결과의 표시 시간은 T/N입니다. 마지막 끝점 표본을 중복시키지 않습니다. 원본 동작 자체의 주기성을 이 계산이 증명하지는 않습니다.

픽셀 선택은 수정 PerfectPixel sample_scoped(method=source_regions,coverage=.5,color_edge_threshold=.08)를 재사용합니다. 셀 경계와 4연결 Oklab 영역 선택·동률 규칙을 바꾸지 않습니다. source_palette(colors=64,iterations=3)는 선택 N장 전체의 공통 분포에 한 번 적용합니다. 정지 이미지용 부위 mask/임의 offset/시간 보간/별도 픽셀화는 추가하지 않습니다.

GIF/WebP는 동일 프레임을 병합할 수 있으므로 원본 N장 PNG와 atlas/JSON이 프레임 수의 권위입니다. GIF는 centisecond, WebP는 누적millisecond 반올림입니다. 시각적 루프 합격은 최종 연속 재생의 사용자 판단이며 이음새 점수100%일치를 gate로 삼지 않습니다.

## 검증·실패 조건

초기 버전에서 선택 시간·공통 좌표·중복 생성 방지 검사를 했고 기존 영상 후처리 1회 18.34초를 계측했습니다. 이후 구간 분리와 폴더 감시 추가분은 사용자 요청에 따라 추가 테스트/재계측을 하지 않았습니다. 브라우저의 실제 신규 생성→파일 전달→후속 생성도 미실행입니다.

실행 중에는 입력을 읽고 계산하는 데 필요한 파일/크기/개수 조건만 확인합니다. 저장한 출력물을 다시 열어 판정하지 않습니다. 이미지마다 AI에 보여주거나 전픽셀 source-coordinate 검사를 다시 수행하지 않습니다. 오류는 실패 단계와 마지막 완료 파일로 반환하며 자동 디자인 보정·재시도하지 않습니다. 키 색이 의상과 겹치거나 생성 모델이 몸을 잘라낸 경우는 알려진 입력 실패이며 생성 모델을 몰래 바꾸지 않습니다.

## 근거

- 기존 외부 실험 Finish-PixelIdle.py 및 pipeline.json, pipeline-speed-and-usage-audit.md의 시간/코드 근거를 재사용합니다.
- 설치 sprite-gen video/frames.py, frames/cutout.py의 공개 extract_route, video/canvas.py와 gen/video.py를 읽었습니다. 영상 생성은 POST1회와 상태 GET이며 API 인증은 기존 resolver가 소유합니다.
- [GPT Images API](https://developers.openai.com/api/docs/guides/image-generation), [GPT Image 2](https://developers.openai.com/api/docs/models/gpt-image-2).
- 독립 코드 검토에서 기존 generate_image 자동 재시도, 작은 영상의 확대, VFR, encoder 동일프레임 병합을 반례로 확인해 위 계약에 반영했습니다.
