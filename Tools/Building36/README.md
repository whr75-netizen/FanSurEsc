# 공통 오브젝트 시트 — B35 원본 변형 교정

## 재개 인수인계 — 2026-09-28 사용자 요청으로 중단

**먼저 읽을 결론:** 전체 시트 정규화·정수 crop·Unity 원본 import까지 완료했다. **게임에 보이는 기존 B35 26개 오브젝트는 아직 교체하지 않았다.** 새 재료가 Project에 있다는 사실을 실내 수정 완료로 해석하지 않는다. 사용량이 끝나간다는 사용자 요청에 따라 추가 구현을 멈추고 현재 결과를 보존했다.

### 최신 요구와 원인

- 한 시트를 원본 PerfectPixel로 한 번 정규화한 뒤 정수 영역으로 잘라 그대로 사용한다. 개별 warp/resize, 면에 맞추기 위한 비균일 변형과 이중·삼중 픽셀화를 제거한다.
- 사용자가 Heartbeast 영상을 보낸 직접 이유는 **같은 사물을 Unity에서 다른 크기·비율로 길쭉하게 변형한 문제**였다. 일반 회전 도구 조사로 요구를 바꾸지 않는다. 같은 asset의 인스턴스는 shared mesh/material과 동일 크기·비율을 사용한다. 서로 다른 종류까지 같은 외곽 크기로 만드는 뜻은 아니다.
- 직접 확인한 색 변형 단계는 `Tools/Building35/project_faces.py:93–103`의 homography/반올림 표본화, `details-prepare.py:97–122`의 개별 목표 격자 표본화, `tray-composite.py:90–134`의 재투영·축소 합성이다. `Assets/Editor/PixelShopProjection35.cs`는 이 projected 출력을 가져온다. Point 필터만 바꾸어 이 손실을 복구할 수 없다.
- 이번 canonical 이후에는 resize/warp를 하지 않았다. 다만 원본 PerfectPixel 자동 검출 자체는 무손실이 아니며 아래에 기록한 약8% 종횡비 차이와 시트 자체의 상대 치수·방향 문제는 남는다.

### 현재 파일과 실행 결과

| 단계 | 실제 상태 | 재개에 쓸 파일 |
|---|---|---|
| 생성 원본 | 기존1회 생성 결과 보존, 이번 재생성 없음 | `Source/sheet.png` 1122×1402 |
| 원본 PP 자동 처리 | OpenCV backend 무수정, 전체 시트1회, 204×277 | `docs/artifacts/building36/native-final/{native.png,receipt.json}` |
| 정수 분리 | 오브젝트18종+잔여2영역, 20/20 RGBA 정확 일치 | `docs/artifacts/building36/slices/manifest.json`, `technical-validation.json` |
| Unity import | 18종 PNG hash·RGBA·FullRect·크기 보존 | `Assets/Art/NativeSheet36/`, `Assets/Editor/NativeSheetImport36.cs`, `unity-import.json` |
| 기존 씬 교체 | **미실행** | `Assets/Scenes/GameMap1.unity`, `Assets/Prefabs/World/PlannedPixelShop33.prefab` |
| 화면·가림·이동 검증 | **이번 미실행**, B35 과거 증거와 구분 | 아래 최소 다음 작업 |

`LocalOnly/Building36SheetFinal/state.json`은 normalize→slice→validate 완료다. `LocalOnly/Building36ImportCorrected/state.json`은 input_gate에서 declared_block이며 integrate/verify에 진입하지 않았다. 마지막 importer 재실행으로 기존 corrected report의 import 해시는 이전 관측이다. 마지막 `handoff-gate.json`은 최신 import에 대해 따로 기록한 입력 검사이며, 그래프 완료나 씬 검증으로 간주하지 않는다. LocalOnly 상태는 로컬 재개용이고 Git에는 결과 receipt를 보존한다.

### 표시 계산과 아직 결정하지 않은 부분

- 기존 카메라 grid는127PPU다. 기존 계산대 가시폭294px/새49texel=6으로 공통 정수 배율 q=6을 정했고, **모든 새 Sprite의 PPU=127/6**이다. PNG는 확대하지 않았다. 실제 게임 카메라에서 정수 화면 배율이 되는지는 아직 실행 확인하지 않았다.
- 건물 root는 local yaw305°, 원본 기준은 건물 local `Quaternion.Euler(30,45,0)`이며 게임 world camera30°/350°와 대응한다. world45°로 다시 돌리면 안 된다. 현재 GameMap1의 `PlannedPixelShop33` 위치는(-16,0,9)다.
- 기존 26개는 B34 content 아래 B35 Fixtures20개/Details6개다. 기존 shader `IsometricAtlasSurface`는 색 UV와 texel XYZ 깊이를 함께 사용한다. 새 그림에 옛 XYZ를 단순 재부착하면 그림과 깊이 의미가 어긋날 수 있다.
- `source_fit_probe.py`의 collider-box 후보 실패는 충돌 박스와 그림 외형을 동일시한 후보의 실패일 뿐이다. **모든 표시 방식이 불가능하거나 모든 새 그림이 불합격이라는 뜻이 아니다.** `NATIVE_DEPTH_MAPPING_NOT_AUTHORED`도 아직 구현하지 않은 연결부의 이름이며 외부 접근 차단이 아니다.
- 현재 import graph는 옛 meshDepthHash까지 보존하도록 작성되어 있다. **가림 동작 보존과 깊이 데이터 바이트 보존은 다르다.** 평면 Sprite 등 표현을 바꾸는 설계를 택하면 기존 graph를 무조건 실행하지 말고, 설계 근거와 실제 동작 invariant에 맞춘 후속 graph/state를 별도로 만든다. 기존 실패 기록은 지우지 않는다.

### 다음 최소 작업 — 앞 단계를 반복하지 말 것

1. 최신 요청, git diff, Unity Edit/Play/dirty와 현재 실제 카메라만 재동기화한다. 정규화·자르기·import는 결과 해시가 그대로면 재사용한다. 새 생성·전체 Play 회귀를 기본값으로 실행하지 않는다.
2. **새 색을 변형하지 않는 표시/가림 방식부터 결정한다.** 미실행 후보는 기존 shader에서 `_NativeDepthEnabled=0`으로 두고 수직 Sprite 평면의 실제 깊이를 사용하는 방식이다. local camera right R, up U, 건물 up Y에 대해 `V=Y/dot(U,Y)=Y/cos30°`, `P=R*(u-pivotX)/ppu+V*(pivotY-v)/ppu`이면 화면 투영에서 한 texel의 두 축 길이와 원본 aspect가 같다. 이는 카메라 압축을 상쇄하는 공통 좌표 변환이며 3D 부피 복원이 아니다. 이 후보는 아직 채택·구현·검증하지 않았다.
3. 현재 `GroundedPropSprite`는 위 cos 보상/격자 snap/depth 전용 pass가 없어 그대로 재사용하지 않는다. 기존 `IsometricAtlasSurface`의 depth off 경로는 실제 mesh 깊이를 쓰지만, 지붕·벽·플레이어 가림 동작이 B35와 같다는 증거는 없다. 공통 pivot/지원면 규칙과 실패 조건을 playbook §1.4/1.5 형식으로 먼저 명세한다.
4. 같은 원본을 쓰는 대표2개와 캐릭터/지붕이 만나는 최소 장면에서 원본 texel, 같은 크기·비율, 화면 정수 배율, 가림을 확인한다. 임의 asset별 scale/offset으로 통과시키지 않는다. 통과하면 기존 배치 인스턴스에 연결한다. 원본 시트의 소품 상대 크기 문제와 표시 경로의 변형 문제를 섞지 않는다.
5. 실제 게임 카메라 결과를 제시하고 남은 기술 실패/디자인 미정을 구분한다. 사용자가 요청한 실내 결과를 얻기 전 재료 준비만으로 완료 처리하지 않는다.

### 유지 사항·도구·전체 연구 위치

- 기존 GameMap1/프리팹·카메라·충돌·통로·지붕·Player 셸은 이번 변경 없음. 마지막 Editor 호출에서 Edit Mode, GameMap1 dirty=false였다. Console에 RenderGraph/ZBinningJob 오류가 관측됐으나 전후 인과를 확정하지 못했다. 컴파일 실행 성공과 Console 무오류를 혼동하지 않는다.
- Python: `C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`. 원본 PP: `C:/Users/JG/Desktop/GPT/3/perfectPixel-main/perfectPixel-main/src/perfect_pixel/`. `LocalOnly/PerfectPixelOpenCV`는 sandbox 읽기 제한으로 기본 권한 import가 실패했고, 허용된 실행에서 성공했다. 이 환경 문제 때문에 원본 알고리즘을 다시 고치지 않는다.
- Unity 편집은 MCP/Editor API writer1명. 이번 사용자 턴의 Computer Use 허용 없음. 원본 에셋과 .meta 보존. 기존 다른 작업의 dirty/untracked 파일을 이번 결과로 stage/삭제하지 않는다.
- 전체 연구를 다시 검색하기 전에 `docs/references/native_pixel_input_contract.md`(격자·비례·회전), `grave_seasons_map_art.md`(참고작), `isometric_urban_map_pipeline.md`(맵 제작), `urban_pipeline_handoff.md`(도심), `pixel_modding_render_pipeline_research.md`(모딩), `radical_fish_technical_report.md`와 `radical_fish_render_research.md`(유튜브 게임 기술), `Tools/WorkLoop/README.md`(Higgsfield와 작업그래프), `Tools/PixelPipeline/README.md`(요소별 실행), `docs/references/codex_premature_stop_research.md`·`codex_interruption_research.md`·`ai_workflow_cost_research.md`(중단·사용량)를 해당 주제에만 참조한다. 과거 문서의 제안/완료 문구보다 최신 요청과 직접 관측이 우선이다.

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
- 공식 Python OpenCV 구현은 같은 분기에서 `(None,None)`을 반환한다. 별도 로컬 의존성을 설치했지만 첫 실행은 sandbox가 해당 cv2 파일을 읽지 못해 실패했다(`native-opencv/receipt.json`). 이 실패와 NumPy 실패를 보존하고, 파일을 읽을 수 있는 권한으로 `LocalOnly/Building36SheetFinal/state.json`의 기존 3단계 그래프를 실행했다. **전체 시트 정규화·정수 분리·RGBA crop 검사는 완료했고, Unity 적용은 이 하위 그래프에 포함하지 않았다.** 새 결과는 `native-final/receipt.json`, `slices/manifest.json`, `technical-validation.json`이다.
- [공식 웹판](https://github.com/theamusing/perfectPixel_webdemo)은 별도의 TypeScript 구현이다. Python의 이 예외를 웹판의 동작이라고 일반화했던 설명은 정정한다. 웹판 소스에는 전처리 크기 조절과 검출 실패 대체 처리가 있다. 배포 bundle과 저장소 소스의 바이트 동일성은 확인하지 않았다.
- 생성 PNG에 아주 낮은 alpha의 배경 잔여물이 있다. 분리 경계의 가시성은 기존 Unity shader의 cutoff0.1과 같은 A>=26으로 측정한다. 실제 crop의 RGBA는 변경하지 않는다. 사용하지 않는 두 영역도 별도 보존하여 모든 원본 texel을 유지한다. 검출용 mask를 실제 출력 이미지의 alpha 변경으로 혼동하지 않는다.

원본 `1122×1402` PNG는 도구 출력을 그대로 복사했다. 생성은1회이며 후속 자동처리의 재실행이 새 이미지 생성은 아니다. 초기 graph의 command.run 입력 key 오류는 명령 실행 전에 발견했다. 실패 state를 보존하고 `existing-source-graph.json`으로 이미 저장된 원본부터 계속한다.

### 실제 전체 시트 실행 — 2026-09-28

- 입력 SHA-256: `345bd9d1fbd4066781381142eccdf62be41dabcded362249884597f6e9a59b50`, RGBA `1122×1402`.
- 원본 OpenCV backend, OpenCV `5.0.0`, NumPy `2.5.3`, Pillow `12.3.0`. 원본 엔진 파일과 selector 해시는 실행 전후 일치한다.
- `grid_size=None`, `sample_method=center`, `refine_intensity=0.25`, `fix_square=False`. 전처리 crop/resize/팔레트 변경/alpha 보정은 없다.
- 원본 내부 FFT 검출은 `(None,None)`, 원본의 gradient 검출은 `(187,280)`, pixel size 검출은 `5.50`이다. `detect_grid_scale=(204,255)`에서 원본 `refine_grids` 후 최종 **204×277**이 됐다. 직접 크기를 지정하거나 자체 검출 대안을 추가하지 않았다.
- 최종 시트 SHA-256: `b9dee0e6eb7f3183f70543e81c1c2467ca7b068781641134022417dc514711ea`. 원본 엔진이 고른 각 셀 중심의 RGB와 같은 위치의 원본 alpha를 저장한다.
- 정규화 시트에서 **18개 오브젝트 + 비가시 잔여 2영역**을 정수 사각형으로만 잘랐다. 저장한 20개 PNG가 시트의 해당 영역과 RGBA byte 단위로 같고, 잘라낸 영역의 합은 전체 시트 면적과 같다. 개별 정규화/resize/warp는 없다. 검사 실패 0건이다.
- WorkLoop `normalize → slice → validate` 연속 실행의 도구 측정 wall time은 약 **1.29초**다. 설치·권한 확인 시간, Unity 작업은 포함하지 않는다.
- **한계:** 원본 검출·refine의 결과로 평균 source cell 폭은 5.50px, 높이는 약5.06px다. 원본 종횡비와 정규화 결과 종횡비 사이에 약8% 차이가 있으므로 이를 무손실 비례 보존이나 디자인 합격으로 보고하지 않는다. 이 결과를 다시 강제 resize하여 덮지 않았다. 생성 시트의 잘못된 물체 비율·방향을 정수 crop 검사가 교정해 주지도 않는다.

현재 `existing-source-graph.json`은 이 실행의 경로를 기록한다. 기존 출력이나 state 위에 반복 실행하지 않는다. 후속 단계는 저장된 시트와 crop을 그대로 소비한다.

### Unity import와 실내 교체의 현재 경계

`import-graph.json`은 `실제 Sprite import → 입력 검사 → 기존 인스턴스 연결 → 실제 씬 관측 검사`의 4개 노드다. Import는 `NativeSheetImport36.Import`의 실제 `unity-import.json`을 사용했다. 18종 PNG SHA와 Unity RGBA/FullRect가 모두 일치하지만 이것은 실내 교체 완료가 아니다.

`import_gate.py`는 `technical-validation.json`, `unity-import.json`, `source-fit.json`과 실제 PNG 해시를 대조한다. 최초 `LocalOnly/Building36Import/state.json`/`import-gate.json`은 collider-box proxy의 18종 bbox 실패를 전체 통합 차단으로 일반화했으므로 **판정 범위를 정정한다.** 이 실패는 `collider-as-visual-proxy candidate rejected`라는 해당 후보의 반례일 뿐이며 실제 B35 visual-depth surface와 같지 않다. 최초 state/report는 이 정정의 근거로 보존한다.

정정한 차단원인은 **`NATIVE_DEPTH_MAPPING_NOT_AUTHORED`**다. 새 canonical 색 texel에 대응하고 기존 지붕/캐릭터 가림을 유지하는 visual-depth 매핑의 생산자·검증기가 아직 없다. 기존 색 warp/depth raster를 새 색에 그대로 붙여 재사용할 수 없으며, JSON 파일 존재나 AI 승인값을 매핑의 증거로 쓰지 않는다. 정정 실행은 `LocalOnly/Building36ImportCorrected/state.json`, `docs/artifacts/building36/import-gate-corrected.json`으로 분리한다. 이 차단은 현재 미저작 단계의 기록이며 모양·디자인 또는 다른 모든 통합 방식이 불가능하다는 결론이 아니다.

**프로덕션 씬 교체는 실행하지 않았다.** 연결 단계는 같은 인스턴스, 같은 자산의 Sprite 참조 재사용, scale1, 기존 mesh-depth/collider 계약을 보존하는 binding만 허용한다. 새 색의 visual-depth 매핑이 실제로 구현·검증되기 전에는 이 노드로 진입하지 않는다. 연결 후 검사는 실제 Editor 전후 관측과 게임 카메라 캡처를 요구하며, 미실행 관측을 통과값으로 만들지 않는다. 최종 `integration` 검사 경로는 아직 실행 검증되지 않았다.

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
