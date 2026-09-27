# 공통 오브젝트 시트 — B35 원본 변형 교정

최신 사용자 정정: 정수배 확대는 원본 픽셀을 뭉개지 않으며, 개별 원본을 억지로 맞추기보다 한 시트에 함께 생성한다. 기존127PPU를 이유로 재제작/배치변경 중 하나를 강요했던 질문은 철회한다.

## 제작 계약

`기존 실내 스타일/역할/상대 치수 → 한 장의 투명 오브젝트 시트 → 원본 PerfectPixel 자동 격자 검출 1회 → 정수 영역 분리 → 원본 격자 표시`

- 출력은 방 전체 합성 이미지가 아니라 개별 배치 가능한 오브젝트들이다. 모든 오브젝트에 공통 카메라/픽셀 크기/팔레트/명암 규칙을 제공한다. 작은 소품을 큰 가구와 같은 크기로 그리지 않는다.
- 정규화 canonical은 시트 전체의 RGBA 배열이다. 원점은 왼쪽 위, x오른쪽/y아래. 한 번 검출한 공통 격자를 사용하고 각 crop은 그 격자의 정수 사각형이다.
- 정규화 후 개별 크기 강제 지정, 면별 색 재투영, 비균등 확대, 필터링 축소를 하지 않는다. 정수배 nearest 확대는 표시/미리보기의 정상 경로이며 원본 배열을 덮어쓰지 않는다.
- 정수배 k에서 `display[x,y]=native[floor(x/k),floor(y/k)]`, k는 양의 정수다. 원본의 경계/색/연결성이 유지된다. 전체 RGBA 크기가 다르다는 이유만으로 이 표시를 실패로 판정하지 않는다.
- 생성 시트가 공통 격자를 보장한다는 주장은 하지 않는다. 자동 검출 실패/오브젝트 간 침범은 입력 오류로 반환한다. 임의 resize나 가짜 성공으로 통과시키지 않는다.
- 기존 계산대/선반/실내 스타일을 참고한다. 새 시트 원본·정규화본·잘라낸 파일을 따로 보존한다. 현재 씬/프리팹/원본은 결과가 준비되기 전에 바꾸지 않는다.
- 파일/격자/분리의 기술 확인은 미술 승인과 다르다. 시트를 보여 드린 뒤 디자인 피드백을 반영한다. 이 재료 작업을 건물 전체 수정 완료로 보고하지 않는다.

## 원본 확인과 실행 상태

- 로컬 Python 엔진의 `__init__.py`, `perfect_pixel.py`, `perfect_pixel_noCV2.py`는 [공식 저장소의 commit 72096de5cf1bff9102687c4f89af6f62c4273a86](https://github.com/theamusing/perfectPixel/tree/72096de5cf1bff9102687c4f89af6f62c4273a86)과 SHA-256이 같다. 증거는 `docs/artifacts/building36/upstream-verification.json`이다.
- 해당 Python NumPy 구현은 `estimate_grid_fft` 실패 시 None을 반환하고 호출부에서 두 값으로 unpack하여 이 입력에서 예외가 났다. 검토 중 추가했던 `--fft-none-compat` 수정은 실행하지 않고 제거했다. **현재 wrapper와 원본 엔진에는 이 호환 수정이 없다.** `native/receipt.json`에 실제 실패가 보존돼 있다.
- 공식 Python OpenCV 구현은 같은 분기에서 `(None,None)`을 반환한다. 별도 로컬 의존성을 설치했지만 첫 실행은 sandbox가 해당 cv2 파일을 읽지 못해 실패했다(`native-opencv/receipt.json`). 권한이 있는 읽기에서 cv2 5.0.0 import는 확인했으나, 이 환경으로 정규화를 아직 재실행하지 않았다. 그래프의 현재 출력 경로에는 실패 receipt가 있으므로 재개 시 새 출력 폴더/실행 상태를 사용해야 한다. **정규화·분리·Unity 적용은 미완료**다.
- [공식 웹판](https://github.com/theamusing/perfectPixel_webdemo)은 별도의 TypeScript 구현이다. Python의 이 예외를 웹판의 동작이라고 일반화했던 설명은 정정한다. 웹판 소스에는 전처리 크기 조절과 검출 실패 대체 처리가 있다. 배포 bundle과 저장소 소스의 바이트 동일성은 확인하지 않았다.
- 생성 PNG에 아주 낮은 alpha의 배경 잔여물이 있다. 분리 경계의 가시성은 기존 Unity shader의 cutoff0.1과 같은 A>=26으로 측정한다. 실제 crop의 RGBA는 변경하지 않는다. 사용하지 않는 두 영역도 별도 보존하여 모든 원본 texel을 유지한다. 검출용 mask를 실제 출력 이미지의 alpha 변경으로 혼동하지 않는다.

원본 `1122×1402` PNG는 도구 출력을 그대로 복사했다. 생성은1회이며 후속 자동처리의 재실행이 새 이미지 생성은 아니다. 초기 graph의 command.run 입력 key 오류는 명령 실행 전에 발견했다. 실패 state를 보존하고 `existing-source-graph.json`으로 이미 저장된 원본부터 계속한다.

## 시트 배치

4열×5행, 18개 오브젝트 + 빈 2칸. 칸 경계선/문자/바닥/그림자는 그리지 않는다. 객체는 서로 접촉하지 않고 여백을 둔다. 여러 배치는 해당 sprite를 재사용한다. 생성 결과의 행 간격이 균등하지 않으면 실제 투명 여백에서 정수 crop을 선택한다. 그림을 칸에 맞춰 이동/변형하지 않는다.

1행: 빈 계산대, 우측 벽 판매 선반, 후면 판매 선반, 낮은 진열섬.
2행: 재고 선반, 냉장고, 작업대, 청소 캐비닛.
3행: 계산기, 사과 상자, 화분, 나무통.
4행: 빈 운반상자, 열린 장부, 벽시계, 식물 액자.
5행: 빗자루, 실내 작은 쓰레기통, 빈칸, 빈칸.

기존 카메라 pitch30°/건물local yaw45°를 기준으로 world X/Z가 화면에서2:1 대각선이 되게 요청한다. 세로 기둥은 수직이다. 생성된 그림이 방향을 따르지 않으면 warp로 고치지 않는다.

## 참고 영상

[Heartbeast: How to Make 3D Models from Pixel Art](https://www.youtube.com/watch?v=2WwztiNmPAQ)의 공식 설명은 Aseprite/LibreSprite/Blockbench를 사용 도구로 연결한다. [제작자 자료](https://uheartbeast.itch.io/pixel-blacksmith-house)는 Toby Dixon에게 의뢰한 아트를 튜토리얼 재료로 소개한다. 영상 작업 장면은 아직 직접 확인하지 못했고 공식 자막 요청은 빈 응답이었다.

[Blockbench 공식 UV 지침](https://blockbench.net/wiki/guides/minecraft-style-guide/)은 표면 텍스처 픽셀과 모델 단위의 비율을 관리한다. 실제3D의 표면 밀도와 최종 화면 픽셀 격자는 다르므로 이 링크만으로 현재2D표시를3D로 전환하지 않는다.

## 회전 조사로 우선순위 전환

최신 요청에 따라 Aseprite의 회전 기능부터 확인했다. `check_aseprite_rotation.lua`는 별도 출력에 90° 회전을 저장하며 원본을 수정하지 않는다. 실제 241×238 → 238×241 RGBA 순열 일치 증거는 `docs/artifacts/building36/rotation/aseprite-readback.json`이다. 임의각 RotSprite는 공식 문서/소스 확인이며 실행 확인과 구분한다. 수학·대안·실패 조건은 `docs/references/native_pixel_input_contract.md` §7에 기록한다.
