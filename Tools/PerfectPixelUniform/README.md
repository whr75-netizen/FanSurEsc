# PerfectPixel Uniform — 전역 격자와 원본 해상도 색 정리

**다음 작업 진입점:** [WORKFLOW.md](WORKFLOW.md)에 고정 사선·좌표·모듈·원인별 단계·실패 귀속·Unity 적용 경계를 정리했다. `pipeline_cli.py`의 `reuse / plan / start / run / status / stop / resume`은 기존 WorkLoop를 호출한다. `current.json`이 제출 PNG를 가리키며 현재 V9다. 임의 새 기하와 V8 목재의 자동 연결·Unity 적용은 아직 없다.

## 현재 결정 V9 · 2026-10-03 — 추가 칸 손잡이 경계 누락 수정

[DESIGN09.md](DESIGN09.md)의 정확 closed-box 교차로 같은 손잡이가 다르게 잘리는 원인을 고쳤다. 기존 기하 BVH에서 추가 문 오른쪽5px와 서랍 끝1px를 놓쳤으며 첫 문의 면 선택도 모듈 수에 따라 달랐다. native centre가 box 모서리에 정확히 닿는 경우를 canonical 정수 slab와 고정 면 동률 규칙으로 판정한다. 모든 실제 box와 최전면 경쟁을 계산하므로 가려진 손잡이를 앞으로 칠하는 보정은 아니다.

Parametric09의 native152×150/192×170은 문14px·서랍16px가 모든 칸에서 같고 이동 정렬 mask/face/normal/ink/RGBA도 같다. 기존 치수·실제 mesh·camera·밀도·alpha·목재4단계/RGBA를 보존했다. 새 경로 `--route handles`는 geometry→pixels→validate를1회실행하여73조건을 확인했고 process 포함2.24초였다. 원본 V6/7/8 코드와 결과를 보존했으며 Unity/새생성/미술검사는없다. snapshot의 publication/workloop 기록에서 실제 실행 출처를 확인한다.

## 현재 결정 V8 · 2026-10-03 — 나뭇결 내부를 실제4색으로 표현

사용자는V7의2색무늬가명암/입체감을표현하지못한다고지적하고3~4색을요구했다. 기존palette는4목재색이지만binarygrain과band+grain으로밝은한면의내부는실제2색이었다. [DESIGN08.md](DESIGN08.md)에원인/참고작/4단계재료표현/보존조건을고정했다. [imonk목재강좌](https://itch.io/t/1452767/pixel-tutorial-wood-texture)의결방향을따라이어지는명암과무작위색반례를참고했다. [Rappenem](https://www.newgrounds.com/art/view/rappenem/pixel-art-tutorial-wood-texture)/[Pixel Pete](https://www.youtube.com/watch?v=nzzphDLsO8g)도직접작가자료링크로보존했다. 타인자산복사/추가생성은없다.

V8은원래생성목재ROI의밝기p10/25/75로밝은결/중간목재/어두운결/짙은골의4역할지도를저작했다. 임의줄그리기나홈마다두꺼운하이라이트띠는없다. 기존8연결6texel미만성분을합병하는문양잡음정책을각nested밝기영역에적용하고손실수를기록했다. source관측밝기분류이며의미있는모든옹이의인식이나무손실사진복구는아니다.

실제결과는`docs/artifacts/building37/Parametric08/pixels/native2.png`152×150/`native3.png`192×170이다. 상판내부의4원본목재색은각각2칸1000/2006/686/222px,3칸1332/3012/876/414px로관측했다. 단지전체palette개수로4색을썼다고주장하지않는다. `wood-levels.npy`와`wood-tile-x4.png`에재료역할/표시를보존했고`pixels/comparison-x4.png`는정확4배표시다. V7geometry·조명band·UV·nativecanvas·alpha·기존ink및목재밖RGBA는불변이다. geometry/Blender를다시계산하지않고목재내부만채웠다.

graph-v8의material→pixels→validate3노드가1회완료했고저장출력과V7보존조건을확인했다. 원화RGB12견본도기존출처그대로다. 4색충족이참고작수준의미술합격증거는아니며Unity표시는미검증이다. 프로필권위는V7recipe07/scene.blend,재료권위는recipe08/source06/palette와4tone-map으로분리했다. 재실행은`wood_material08.py material/pixels/validate --output <새경로>`순서다.

## V7 · 보존 기록 — 평판 전면으로 과한 입체감 수정

사용자는 V6의 카툰 같은 입체감과 돌출 외곽/함몰 패널 구조를 거부했다. V6의 기술검사 통과는 미술합격이 아니었다. 원인은 문틀50mm 단차·손잡이112.5mm 돌출·문짝사이125mm 몸체노출·51mm 상판이었다. 새 [DESIGN07.md](DESIGN07.md)의 프로필로 수정했다. 색감·나뭇결·명암 알고리즘·픽셀밀도·2/3칸·V6 원본/코드/결과는 보존했다.

V7은 실제 평판 문/서랍을 같은 z=-.4tick에 두고 Frame/Inset/SideFrame을 제거한다. 틈은 .5tick=15.625mm, 상판25.52mm, 손잡이의 판기준 최대 돌출26.56mm다. 몸체앞면을 대부분 덮는19.5tick 판을20tick마다 반복하여 넓은 테두리가 읽히지 않도록 했다. 면마다 임의 색칠/조명/스케일 보정은 추가하지 않았다. `cabinet_profile07.py`는 새 box 프로필을 기존 `cabinet_geometry06.raster_variant`와 `cabinet_pipeline06.pixels`에 전달하는 어댑터다. 재료는 V6의 byte동일 복사이며 새 생성이나 무늬 재계산은 없다.

실제 결과는 `docs/artifacts/building37/Parametric07-fixed/pixels/native2.png`152×150, `native3.png`192×170, 각12색과 동일한 native 밀도다. `pixels/comparison-x4.png`는 정확4배 표시이며 `geometry/scene.blend`에두실제모델을보존했다. 평판 동깊이·테두리삭제·상판접합·손잡이돌출·가시선/최근접깊이·팔레트/alpha·모듈/표시/V6SHA보존의 마지막244조건을 확인했다. 그림자는388/430px로 줄었다. **미술승인이나 범용모딩/Unity표시 검증은 아니다.**

첫 실행은 Blender가 sibling renderer 모듈 경로를 찾지 못했다. 실패코드/로그/blocked state를 `Parametric07`에 보존했다. Blender exit0만으로 성공처럼 다음 단계가 진행된 관측 오류도 있었으므로, module import 경로와 worker 완료 metadata 요구를 고쳤다. 치수/재료/카메라는 바꾸지 않고 새 출력 `Parametric07-fixed`에서 `graph-v7-import-fix.json`의 geometry→pixels→validate3노드를 완료했다. Blender 시작 포함 기하3.218초/픽셀.257초로, 생성/설계/코드작성/검사시간과별도다. 기존V6를덮어쓰거나재계산하지않았다.

재실행은 `cabinet_profile07.py geometry/pixels/validate --output <새경로>`를 순서대로 호출한다. profile 입력은 recipe07, 변경하지 않은 색·UV·명암 계약은 recipe06이며 각 실제 입력 SHA를 기록한다. `.blend` viewport/F12와 final native PNG의 구분은 V6와 같다.

## V6 · 보존 기록 — 생성 재료와 입체 구조를 결합한 수납장

사용자 요청에 따라 **색감·재료 디자인은 새 생성 원화에서 가져오고, 경계·깊이·명암 영역은 부품 기하에서 계산**했다. 같은 디자인의 2칸/3칸 수납장을 실제 제작했다. 생성 원화를 축소해 최종 스프라이트로 제출한 것이 아니다. V5·기존 원본·8768 웹·Unity 배치는 보존했다.

설계 계약과 기술 비교의 단일 원본은 [DESIGN06.md](DESIGN06.md)다. imagegen으로 만든 `Source06/generated-board.png`는 1254×1254 RGB의 디자인/재료 참고이며, `Source06/prompt.txt`와 `provenance.json`에 원본·요청을 보존했다. 숨은 치수를 한 장에서 유일하게 복원했다고 주장하지 않는다.

계산 순서는 **원화의 중앙 RGB 표본 12개·UV 무늬 → 실제 입체 부품 → native 픽셀 중심의 최근접 표면 → 명암 역할 선택 → 보이는 경계 → 저장 결과 검사**다. 문틀/서랍 프레임, 안쪽 패널, 손잡이와 브래킷, 상판 돌출, 하부 받침, 측면 패널은 실제 유한 박스로 구성된다. BVH 깊이가 가림을 결정하며 부품 이름이나 임의 레이어가 깊이를 덮어쓰지 않는다.

색은 paint/wood/brass 각 light/base/shade/edge의 **원화 한 점 RGB 그대로**다. `normal·light`와 실제 shadow ray로 3명암 영역을 구분하며 RGB 밝기 곱·그라데이션·디더링이 없다. 평면 목재 ROI의 어두운 무늬는 고정 물리 UV 역할 지도로 옮겼다. 이는 표현 밀도에 맞춘 명시적 재료 저작이며 원본 무늬 전부의 무손실 복구가 아니다. 작은 독립 성분 101개/255texel을 제외하고 1536grain texel을 유지했다.

크기 확장은 `W(n)=4+20n`, `x_i=2+20i`의 **고정 끝단+동일 수납칸 반복**이다. 두 결과는 깊이·높이·문틀·손잡이 규격, 64√2 px/m 밀도와 물리 UV 주기가 같다. 전체 가구 PNG나 UV를 길게 늘리지 않았다. Blender Array와 같은 배치식을 코드로 실행했으며 Array Modifier 자체를 사용했다는 뜻은 아니다. 사선 전체 PNG에 9-slice를 적용하는 방식은 상판·측면 접합을 보존하지 못해 제외했다.

| 실제 파일 | 내용 |
|---|---|
| `docs/artifacts/building37/Parametric06/pixels/native2.png` | 2칸, 152×150 RGBA, 12색 |
| `docs/artifacts/building37/Parametric06/pixels/native3.png` | 3칸, 192×170 RGBA, 12색 |
| `pixels/comparison-x4.png` | 위 두 PNG의 정확한 정수4배 비교 표시, 제작 자산 아님 |
| `geometry/scene.blend` | 두 크기의 실제 메시·카메라를 각각 둔 편집 가능 Blender 파일 |
| `geometry/parts.json`, `geometry/buffers*.npz` | 부품 치수와 실제 표면 위치/법선/소유자/깊이/그림자 가시성 |
| `material/palette.json`, `grain.npy`, `material.json` | 원화 표본 좌표·RGB, 무늬 역할·물리 주기·손실 기록 |
| `pixels/shading*.npz` | 명암/무늬/경계/색 인덱스의 분리 지도 |
| `validation.json`, `workloop-state.json` | 실제 저장 결과 검사와 4노드 실행 기록 |

native PNG는 처음부터 1px 격자에서 생성했다. 추가 PerfectPixel·사진 축소·PNG 늘림·외곽선 팽창은 없다. canvas 차이는 가구 폭과 투영 bounds의 차이이며 픽셀 밀도 변경이 아니다. Blender 파일의 viewport 재료는 편집용 기본색이다. **Blender F12 beauty render는 최종 픽셀 PNG가 아니며**, 현재 재제작 입력은 `.blend` 수작업 수정이 아니라 치수 recipe/부품 코드다.

마지막 저장 결과 검사에서 source RGB 출처·이진 alpha·최근접 깊이·보이는 경계 소유·평행 면 2중선 없음·동일 모듈/UV·실제 shadow·모든 문/서랍/손잡이의 가시 픽셀·정수4배 대응과 원본/V5 SHA 보존을 확인했다. 두 결과 shadow는 각각 1143/1345px다. 고정 그래프 4노드를 1회 연속 실행하여 완료했고 생산 재실행/추가 시각 보정은 하지 않았다. **기술 조건 확인이며 미술 승인, 원화 99% 복제, 범용 가구 자동 설계, Unity 표시 검증은 아니다.**

재료 계산 .142초 + Blender 실행 9.147초 + 픽셀 채움 .303초 = 약9.59초. Blender 안의 기하/가시성 계산은 .787초, 최종 검사는 .436초였다. 생성 서비스 대기·설계·코드 작성·AI 추론은 별도이며 전체 작업 10초 보장이 아니다.

재실행은 기존 출력과 다른 새 디렉터리에 아래 단계를 연속 호출한다. 검토된 recipe는 2/3칸, 45° azimuth/30° elevation, 현재 부품 치수에 한정한다. `graph-v6.json`은 이번 실행의 고정 절대경로 계약이며 이미 결과가 있으면 덮어쓰기 대신 중단한다.

```powershell
python -B Tools/PerfectPixelUniform/cabinet_pipeline06.py material --output LocalOnly/Cabinet06-new
python -B Tools/PerfectPixelUniform/cabinet_pipeline06.py geometry --output LocalOnly/Cabinet06-new
python -B Tools/PerfectPixelUniform/cabinet_pipeline06.py pixels --output LocalOnly/Cabinet06-new
python -B Tools/PerfectPixelUniform/validate06.py --output LocalOnly/Cabinet06-new
```

## V5 · 보존 기록 — 픽셀 구조를 직접 저작하는 수납장

사용자의 최신 정정은 ‘흐린 나뭇결의 색만 줄이는 것으로는 도트 나뭇결·명암 덩어리·한 줄 경계가 만들어지지 않는다. 수학적으로 직접 그려 달라’이다. V4는 이 요구에 미달했다. **새 수납장 한 개를 템플릿에서 native 픽셀로 직접 제작**한다. 기존 나무 상판/청록색 수납장의 물체 종류·색 방향을 참고하며, 생성 원본의 동일 복구나 전체 실내 제작으로 확대하지 않는다. 원본/V1~V4/웹/Unity를 보존한다.

### 제작 전에 고정한 구조와 계산

1. 표현 후보: 원본 필터 추가는 기존 반례를 해결하지 않아 기각. 외부 생성 모델은 픽셀 위치의 결정적 제어 요구에 부족. **정수 면 도형·단일 경계·정의된 Bézier grain 클러스터를 직접 그리는 템플릿**을 선택한다. 물체 형태·색 역할은 저작 데이터이며 수학이 좋은 디자인을 자동 발견한다는 뜻은 아니다.
2. 좌표: local `(x,y,z)`는 투영 tick, X가구 길이/Y위/Z깊이. world metres로의 embedding은 `(x/32, y/(32√6), z/32)`다. 오른손 local 기저이고 parent 없음. orthographic native projection은 `u=58+2x-2z`, `v=174-x-z-y`, 원점 좌상단/+U오른쪽/+V아래. 실제 균일 world density `64√2 px/m`, pitch30°에 대응한다. ground 선 화면 변각은26.565°이고 pitch30°와 혼동하지 않는다. 카메라/world를 수정하는 작업은 아니다.
3. 구조: width64/depth20/height72tick → 실물2.0×.625×.9186m. native204×192 canvas는 이 투영 bounds와 여백에서 정한다. 상판 두께4tick, 하부 받침6tick, 같은 폭16tick 문3개/틈4tick/좌우여백4tick. native 손잡이 폭≥3px·높이6px, 나뭇결/옹이≥수px가 읽히는 저작 규격이다. 기존 이미지를 이 크기로 줄이지 않는다.
4. 변환: 모든 구조 정점의 공통 affine projection→`floor(value+.5)` 한 번. convex polygon은 pixel centre/half-open top-left 규칙으로 채운다. 색은 면/재료 역할에서 선택한 고정 팔레트다. side/front/top 영역은 겹침0이어야 한다. 최종 edge 소유자 한 명, endpoint pair로 중복 제거 후 비AA Bresenham 1회. 선 주변으로 색을 보간하지 않는다.
5. 질감: 나무판3개, 끊긴 곡선과 옹이2개를 top UV `(x,z)`에서 cubic Bézier로 정의한다. De Casteljau로 control hull의 chord 거리≤.125native px까지 적응 분할, 각 chord를 동일 Bresenham으로 그린다. 최대깊이16에서 만족 못하면 실패. ellipse knot는4cubic 근사, 내부 core는 식 기반 binary fill이다. 곡선 길이/위치/끊김은 recipe의 결정적 저작 변수이며 random/dither 없다. **전체 곡선의 모든 native 점이 top 내부이고 구조선과 겹치지 않을 때만 곡선을 통째로 기록**한다. core도 같은 경계를 따른다. 경계 충돌이면 조각내서 숨기지 않고 재료 단계가 실패한다. 부드러운 원본 나뭇결·사진 RGB는 읽어 칠하지 않는다.
6. 명암: top/side/front의 고정 역할색, 단차 아래 한 덩어리 음영, 문 내부의 단일 색, 금속 손잡이의 base/highlight 두 덩어리다. PBR·광택·연속 조명 gradient·색 평균 없음. 구조 경계는 질감보다 나중에 한 번 출력한다. 이 PNG의 정적 명암과 미래 Unity 동적 조명은 별개다.
7. 마지막 검사: 원본 SHA 보존, native dimensions, alpha0/255, 고정 palette 외 RGB0, shared face overlap0, edge 중복0, 각 선8연결/major-axis 한 점, 최종 구조색=선 recipe, grain top 내부·경계 침범0・8연결 이웃 없는 단독점0, 같은 문 폭·손잡이 규격, 저장 PNG/표시4배의 byte 대응. 기술 통과는 디자인/참고작 합격과 구별한다.

파이프라인: `recipe → geometry masks/unique edges → face colours/material grain → native PNG → 마지막 저장결과 검사 + 별도4배 표시`. `draw_parametric.py`는 geometry/material/validate 단계이고 `graph-v5.json`으로 연속 실행한다. 새 패키지·생성형·PerfectPixel·Aseprite 호출 없이 기존 NumPy/Pillow로 직접 저작한다. 원본은 reference SHA 확인용이며 원본 RGB 표본을 출력에 사용하지 않는다.

근거: [Bresenham 원논문](https://ibm-1401.info/Pics3/bresenham1965.pdf), [Zingl의 비AA 정수 rasterization](https://zingl.github.io/bresenham.html), [De Casteljau 분할 설명](https://pomax.github.io/bezierinfo/#decasteljau), [공유 경계 top-left 규칙](https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-rasterizer-stage-rules), [픽셀 작가 cure의 클러스터·밴딩·노이즈 설명](https://pixeljoint.com/forum/forum_posts.asp?TID=11299). De Casteljau의 bounded chord 연결과 role palette는 이 템플릿의 구현 조합이며 위 자료가 완성된 가구 생성기를 제공한다는 뜻은 아니다.

### 재료 경계의 원인 수정 계약

첫 저장 결과의 독립 감사에서 grain637px 중8연결 단독점40개를 발견했다. source curve를 다시 추적한 진단에서11개 곡선은 자르기 전 모두 한 덩어리였으며, 경계선을1px 팽창한 raster mask로 자른 뒤에만 곡선2/3/6이 다수 단독점으로 바뀌었다. 곡선19개(11grain+8knot quarter)의 원래 점은 모두 top 내부이고 실제 구조선 침범0이었다. 따라서 임의로 넓힌 경계 배제대가 원인이다.

수정은 **재료 단계의 부분 clipping 제거→전체 stroke 허용/거부**와 누락된 단독점 검사를 추가하는 범위다. recipe·기하·팔레트는 유지한다. 기하 NPZ/JSON은 재계산하지 않고 이전 producer SHA를 보존하며 재료 기록에서 입력 bytes SHA를 고정한다. 이전 PNG/재료/검사/성공 그래프를 `Direct05/failed-grain`에 보존하고 재료→마지막 검사만 새 recovery 그래프로 실행한다. 원본 필터·resize·외딴점 삭제 후처리로 대체하지 않는다. 첫 그래프의 exit0은 이 누락된 조건의 성공 증거가 아니었다.

### 실제 결과 · 이번 요청의 관측 범위

`docs/artifacts/building37/Direct05/native.png`는 **204×192 RGBA, 실제15색, alpha0/255**다. 원본을 축소한 것이 아니라 recipe의 기하·색 역할·곡선을 pixel array에 직접 기록한 새로운 수납장이다. source sheet의 RGB는 읽어 사용하지 않았다. palette16역할 중 `wood_light`는 현재 미사용이다. 문3개/손잡이3개, 나무판3개/곡선11개/옹이2개, unique 구조선31개를 저작했고 마지막 구조선 우선순위는 `wood_edge > edge > wood_joint`다. 공유 endpoint를 제외한 각 선은 major-axis마다 native1점이며 번짐·반투명선·dither·연속 조명 계산이 없다. 명암은 저작한 sRGB 역할색이지 물리광학/sRGB 광량 시뮬레이션이 아니다.

초기 geometry 계산 후 NumPy int64의 JSON 직렬화가 실패했다. `quantize`의 Python int 반환과 파일 열기 전 직렬화로 원인을 수정했고, 실패 NPZ/부분JSON/원래 코드/blocked graph를 `failed-json`에 보존했다. 복구된 모든 geometry mask는 실패 시 이미 계산된 mask와 byte 동일했다. 기하 계산 .2937초·첫 재료 계산 .0782초였으나 그 재료의 경계 clipping이 grain 단독점40개를 만들었다. 저장결과 감사에 따라 위 계약으로 재료만 수정했다.

최종 재료 계산 .0604초, grain695px/구조선 침범0/8연결 이웃 없는 단독점0. `graph-v5-recovery.json`의 **material→validate 2노드**가 완료됐고 기하 NPZ/JSON SHA는 그대로다. 최종 validation은 저장된 픽셀・recipe・구조 mask/색・공통 치수・입력 SHA・정수4배 대응을 확인했다. 기하와 최종 재료의 계산 합계 약.354초는 process 시작/검사/AI 작업 시간과 구별하며 전체 제작의 고정 소요시간 보장이 아니다.

별도 읽기 전용 감사에서 recipe/geometry producer/input SHA 유지, old grain637px 전부 유지+58px만 추가, old/newgrain 바깥 변경0px, 손잡이 mask・최종 edge RGBA 동일을 확인했다. 최종 grain8연결 component10개는24/30/32/55/64/69/79/105/116/121px이고1px·2px독립섬0이다. 직접 검사와 감사 모두 미술 점수로 대체하지 않았으며 감사에서 재제작하지 않았다(`independent-audit.json`).

`preview-x4.png`는 native각점의 정확한4×4복제(816×768), `display-x4.png`는 그 위에 배경/설명을 붙인848×832 미리보기다. 둘 다 제작 자산으로 되먹이지 않는다. 원본/과거/V3웹/Unity는 보존했고 이번에는 기존 실내에 배치하거나 동적 조명을 연결하지 않았다. 실행 예는 새 출력이 없는 상태에서 `work_loop.py init <새 state> graph-v5.json`→`run <같은 state>`다. 기존 산출물이 있으면 덮어쓰기 대신 실패하며, 이번 원인 재개는 별도 recovery 그래프/기록을 사용했다.

**직접 native 저작과 기술 조건은 확인, 미술적 완성·참고작 동일 복제·모든 가구 자동 제작은 미검증**이다. 현재 수납장 한 종류의 결정적 템플릿이며 curve/색/치수는 저작 데이터다. 그림에서 의미 있는 무늬를 자동 찾거나 사진 전체를 이상적 pixel art로 바꾸는 기능을 구현했다고 바꿔 말하지 않는다.

## V4 설계·증거 — 보존 기록

최신 정정: V3의 154249→136682색 변화는 너무 작으며 픽셀 경계 복구로 볼 수 없다. 사용자가 지정한 과거 **선 검출/고정 → 연결된 색 영역 채움** 구현을 `LocalOnly/PerfectPixelPalette_20260906`에서 찾았다. 원본 PNG는 raster이며, PNG라는 형식만으로 규칙적인 저작 픽셀 격자임을 뜻하지 않는다. V3의 약한 색 정리는 이 요구의 완료가 아니다.

### 구현 전 요구·원인·연산 계약

- 요청 결과: 같은 실제 시트에 과거 수정판을 적용한 새 PNG와 같은 좌표의 원본/결과 비교. 제작 원본·V1~V3·기존 엔진·Unity는 보존한다. 게임 통합·새 아트 생성·격자 추측 축소는 제외한다.
- 원인 단계: V3의 작은 색오차 한도는 많은 색을 남겼으며 선/색 영역 재구성을 실행하지 않았다. `source_regions`만으로는 선 우선이 아니다. 기존 `line_normalization.mode=line_first`를 명시적으로 켠다. 이 구현도 숨은 원래 격자·없는 선·이상적인 벡터 모양을 자동 복구하는 알고리즘은 아니다.
- 입력 적합성: 엔진은 uint8 RGBA의 이진 alpha만 받는다. 원본 alpha는 256단계이므로 **별도 복사본에서 alpha≥128→255, 미만→0**을 명시적으로 적용한다. 투명 RGB는 이 복사본에서만 0으로 한다. alpha 변화/삭제 수와 원본 SHA를 기록한다. 같은 크기에서 마스크만 바뀌며 가장자리 의미 보존은 보장하지 않는다.
- 좌표: source/target 원점 좌상단, X오른쪽/Y아래, source px, 중심 `(x+.5,y+.5)`. `base_grid=[W,H]`, scale1.0으로 **1489×1056 유지**. 선 투영 `floor((x+.5)*targetW/sourceW)`은 이 시험에서 identity다. RGB 공간 연산으로 Jacobian이나 배율을 바꾸지 않는다. 별도4배 crop은 표시용이며 자산에 되먹이지 않는다.
- 연산: raw Oklab L의 dark/bright Sato ridge → 반대편 색 대비/폭 필터 → Zhang skeleton → 동일 target 좌표에 선 고정 → 선 제외 4연결 raw Oklab 색영역 → source-supported priority flood(`fill_source_guard=true`) → 해당 영역의 실제 팔레트 RGB 표본으로 채움. 선 기본값 폭≤6source px, contrast≥.045, response≥.006, component≥3을 그대로 사용한다. 팔레트는 원본 관측 RGB 중 Oklab 64대표색/3회이며 디더링과 RGB 블렌딩이 없다. 과거 캐릭터의 수동 erase 좌표·별도 명암·highlight는 사용하지 않는다.
- 실패 귀속: 입력/alpha는 준비 단계, ridge·선 충돌/열린 선은 선 단계, 영역 연결/지지 없는 채움은 영역 단계, 색 소실은 64색 선택 단계다. 기존 엔진은 충돌/미해결 셀에 pre-line palette 색을 남기므로 그 수를 분리 공개한다. 이를 선 복구 성공으로 계산하지 않는다.
- 마지막 자동 검사: 원본/코드 SHA 불변, 같은 W/H, 이진 alpha와 준비 마스크 동일, opaque RGB≤64 및 실제 원본색 포함, 고정선/소유영역/표본 좌표와 실제 저장 PNG의 일치, 충돌/미해결 fallback 수, 색 변화와 선 처리의 추가 변화 수. 사라진 의미적 특징·디자인·native 저작 격자는 검사 통과로 주장하지 않는다.

근거는 기존 코드와 [Sato ridge](https://scikit-image.org/docs/stable/api/skimage.filters.html#skimage.filters.sato), [skeletonization](https://scikit-image.org/docs/stable/auto_examples/edges/plot_skeleton.html), [marker watershed](https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_watershed.html)다. guard=true는 기존 구현의 source-supported priority flood이며 표준 watershed와 구분한다. 실제 입력에서 유효한 선을 검출하는지는 결과를 보고 판정해야 한다. 기존 의존성은 읽기 권한을 확인해 사용하며 새 패키지/플러그인은 설치하지 않는다.

`graph-v4.json`의 준비 → 기존 엔진 계산 → 저장 결과 검사만 실행한다. `trial_line_first.py prepare/validate`는 경로·전처리·출처·미리보기만 담당하며 기존 선/팔레트/영역 알고리즘을 다시 만들지 않는다. V4는 독립 시험이며 8768의 V3 기본 모드를 몰래 바꾸지 않는다.

### 실제 결과와 현재 판정

`docs/artifacts/building37/Uniform04/engine/pixel_native.png`는 **1489×1056, opaque RGB64**다. 기존 CLI를 새 패키지 없이 1회 실행했고 169.632초/exit0, stderr0bytes다. 기존 WorkLoop의 command.run은 최대60초라 엔진만 고정 명령을 외부 실행 인계(`ai.work`)로 호출했다. 준비·저장결과 판정은 별도 일반 계산이다. `execution.json`은 실제 argv/PID/exit/시간/로그 SHA이며 AI의 성공 문장이 아니다. 그래프3노드와 마지막 저장결과 검사는 완료했지만, 그 판정은 아래 기술 범위다.

팔레트 단계502696opaque px 변경, 선 우선 단계31064px **추가** 변경. source 후보선228852px→source skeleton106138px→target 고정선104358px, raw 색 연결 영역9802개, 채움323392px(그중 같은 영역 가까운 표본46640px). 고정선의 **좌표**는 identity이며 102614px의 원색은64색 팔레트로 바뀌었다. 후보선을 skeleton으로 줄이면서 주변을 다른 색 영역 표본으로 채우므로 캔버스/투영은 유지돼도 색 경계·선 두께가 불변이라는 뜻은 아니다.

미해결77854px(시험 opaque505604px의15.40%)는 팔레트 처리된 pre-line 색을 그대로 남겼고 충돌0이다. guard가 거부한 영역 제안28600개는 엔진 metadata 수치이며 개별 제안 지도가 없어 독립 재산정하지 않았다. fallback을 복구 성공에 포함하지 않는다. source alpha128 복사본에서 alpha578487px가 변했고 기존 nonzero-alpha73742px가 투명해졌다. 최종 alpha는 **준비된 복사본**과 동일하며 원본 alpha 보존이 아니다. 전체RGB비교154249→64는 전처리/팔레트/선 단계를 합친 수치다.

실제 map 검사로 원본/엔진 SHA불변, W/H동일, 명시 alpha128 mask, 관측 원본RGB≤64, 고정선/영역 표본의 최종 색 일치, fallback 귀속을 확인했다(`validation.json`). 별도 읽기 전용 감사도 같은 저장 결과를 확인했으며 재생성하지 않았다. 연결 영역2440개에는 최종2색 이상(최대26색)이 남아, 영역별 단색 평탄화가 아님을 추가 확인했다. `comparison-crop-x4.png`는 원본과 결과의 같은128×128영역을 nearest4배로 표시한 미리보기다.

**현재 판정: 기존 수정판 적용 시험은 완료, 깨끗한 정규 픽셀 복구는 미달.** 확대 비교에 잔색 반점/불규칙 경계가 남는다. 이 코드는 Sato검출·선 가늘게 고정·연결 색 영역 표본화이며 이상적인 직선/곡선 복원·자동 저작 격자 검출·영역 전체 단색 채움이 아니다. 모든 색 경계를 직선화하거나64색을 더 줄이는 후처리를 완료 해결책으로 추가하지 않는다. 다음 제작의 부족 단계는 palette수보다 **유효 격자와 구조선의 정의/복원**이며, 그 근거 없는 임의 축소는 계속 금지한다. V3웹/Unity에는 이 시험을 통합하지 않았다.

## V3 설계·증거 — 보존 기록

최신 요구: V2는 실제 생성형 시트에 결과를 주지 못했고, 확대할수록 주변의 여러 색·미세 명암이 더러워 보인다. **무손실 반복 제거와 색 잡음 정리는 다른 연산**이다. V2의 byte equality를 색 정리의 통과 조건으로 쓴 요구 해석을 수정한다. 원본·과거 출력·Unity를 보존하며 원본 크기에서 색만 정리하는 별도 경로를 웹 기본 모드로 제공한다. 정규 격자 복원을 성공했다고 바꿔 말하지 않는다.

### 구현 전 선택·수학 계약

- 후보: (A) nearest 축소/고정 목표 크기 — 특징을 버려 제외. (B) 작은 반경 bilateral + 오차 제한 팔레트 매핑 — 채택. (C) guided filter — 같은 역할의 대안이며 연속 추가하지 않는다. 미확정 격자의 강제 정렬·local warp는 제외한다.
- 좌표: `RGB(A) source[y,x] → 동일 source pixel 좌표의 색 연산 → 동일 W×H PNG`. 좌상단 원점, X오른쪽/Y아래, source px 단위, 중심 `(x+.5,y+.5)`, 부모/회전 없음, 기하 Jacobian=identity. resize/crop/sample 이동 없음. alpha와 alpha0의 숨은 RGB는 byte 그대로 유지한다.
- 색 거리: sRGB를 표준 D65 CIELAB로 변환해 `ΔE76=||Lab(a)-Lab(b)||₂`로 계산한다. 색공간 변환은 가중치·오차 측정용이며 저장 모드는 원래 RGB(A)다.
- 필터: 반경2px, `σSpace=1px`, `σColor=t`인 bilateral 1회. `w=exp(-||i-j||²/2-ΔE76(i,j)²/(2t²))*alpha(j)/255`, alpha0 이웃 제외. 저장된 sRGB byte의 weighted RGB를 round한 후보가 원본에서 t보다 멀면 원본을 유지한다. 이미지 밖 이웃은 제외한다. t=2/4/8은 보수적/표준/강 정리의 명시된 색 오차 설정이며 문헌의 보장값이 아니다.
- 팔레트: alpha≥16인 색에서 Pillow median-cut 후보 팔레트 K=64/128/256을 만든 뒤 **dithering NONE**으로 매핑한다(해당 pixel이 없으면 전체 보이는 색). 낮은 coverage의 원색 fringe가 팔레트를 과점하는 것을 줄인다. 원본 대비 ΔE76≤t인 후보만 수락하고, 초과하면 오차 제한 필터 결과를 유지한다. 보호 색도 남으므로 최종 색 수가 K 이하여야 한다고 주장하지 않는다. 이미 보이는 RGB 색 수≤K인 입력은 그대로 유지한다.
- 경계: source 4-neighbor 색 차이가 `max(12,3t)` 이상인 양 끝 pixel의 RGB를 정확히 유지한다. 이는 명시된 강한 경계와 고대비 1px 특징 보호이며, 낮은 대비의 의미 있는 특징과 잡음을 자동 구별한다는 보장이 아니다. 강한 경계를 보호하면서 잔색을 정리하는 정도를 실제 시트로 관찰한다.
- 불변조건: 입력 불변, W/H/채널 불변, alpha 및 hidden RGB byte equality, 보호 pixel RGB equality, 모든 변경 pixel ΔE76≤t(+float tolerance .001), 디더링 없음. 오류는 해당 색 단계에 귀속하며 결과 저장 전에 중단한다. 출력 label은 `source_resolution_cleanup`이고 grid 검증 상태와 분리한다.

가설/판별: 내부 저대비 변동은 감소하고 고대비 선·실루엣·크기는 유지된다. 합성 flat+noise/1px 눈·선/alpha 경계와 실제 사용자 run을 검사한다. 새 격자·재저작·게임 통합은 이번 범위가 아니다. 색 fringe가 높은 대비를 가진 원본 결함이면 이 보수적 경로에서 남을 수 있으며, alpha/matte 변경을 몰래 추가하지 않는다.

근거: [OpenCV bilateral 설명](https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html), [guided 원 논문](https://people.csail.mit.edu/kaiming/publications/eccv10guidedfilter.pdf), [Aseprite ColorQuantization](https://www.aseprite.org/api/command/ColorQuantization), [Aseprite dithering none](https://www.aseprite.com/docs/cli/#--dithering-algorithm), [Pillow quantize](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.quantize). 외부 fixer/OpenCV를 새로 설치하지 않으며 NumPy의 직접 bilateral 식과 기존 Pillow를 사용한다. alpha 분리·색오차 제한·경계 고정은 이 도구의 보존 계약이다.

### 실행·판별 결과

웹 기본은 **색 번짐 정리 · 해상도 유지**이며 정리 강도/후보 팔레트만 선택한다. 확대 1/2/4/8배는 원본과 결과에 똑같이 적용하고 PNG를 다시 확대 저장하지 않는다. API는 `mode: cleanup, strength: 4, palette_colors: 256`; mode 생략은 과거 V2 호출 호환을 위해 lossless다. CLI는 `cleanup.py --source <원본> --output-dir <새 폴더>`이고 격자 규격/목표 해상도를 받지 않는다.

사용자 run `20261003T092818576216Z-59a6e7b8655b4cf4a637cf98f68e32a7`은 B37와 같은 source다. `graph-v3.json` WorkLoop3단계 완료: 실제 source 계산 1회 → 독립 fixture/저장결과 검사 → HTTP9조건. `docs/artifacts/building37/Uniform03/output.png`는 **1489×1056 그대로**인 색 정리 후보, 계산3.630초, alpha/hidden RGB byte 동일, 강한 경계215329px의 RGB 동일, 최대색변화3.999974ΔE76≤4. source SHA 불변. RGB 고유색154249→136682, 변경357806 visible px. 원본에서 선택한 저대비 인접쌍의 제곱색차 비율0.938642로6.14%감소했다. 이 수치는 국소 색 변동이며 특징/인지/미술 합격 점수가 아니다. 효과는 보수적인 수준으로, 고대비 fringe·원래 격자·픽셀아트 저작 문제를 해결했다고 주장하지 않는다.

9개 fixture/실제artifact 검사와 HTTP9조건 통과. 실제 아트는 재생성 없이 저장결과를 읽어 검사했다. `comparison-crop-x4.png`는 같은128×128 영역을 nearest4배로 보여주는 별도 미리보기(1032×540)이며 게임 자산이 아니다. 실제 원본의 매우낮은alpha1~15에 원색 red3367/yellow223px가 있어 matte 오염 가능성은 있지만 원인은 확정하지 않았다. 해당 색을 몰래 삭제하거나 alpha를 다시 만들지 않았다.

실제8768서버가V2로남아있어 경로/유휴상태를확인한PID36976만종료하고V3로교체했다. `live-server.json`의version3/계산SHA일치와netstat의리스너PID40068을확인했다. OS프로세스조회는기본sandbox에서거부되어승인된조회로대상을확인했고,Stop-Process실행오류후동일PID의taskkill성공을관측했다. 화면버전과색처리/격자/웹코드의합성SHA를확인해오래된계산기를새화면에서재사용하지않도록했다. 실제개인브라우저UI자동화와Unity변경/Play검사는하지않았다.

남은 범위: source-resolution 색 정리는 확인했지만 fake-pixel의 진짜 저작 격자를 복원한 것은 아니다. 낮은 대비의 유효 무늬도 색 정리 강도에 영향을 받을 수 있다. 외곽 matte 정리와 확실한 격자 복원은 해당 단계의 별도 증거/명세가 있어야 추가한다. 원본/V1/V2/Unity는 보존하며 같은 입력의 반복 생성이나 강제 축소로 대체하지 않는다.

## V2 설계·증거 — 보존 기록

사용자 확인: V1의 휘어짐은 사라졌지만 특징이 모자이크처럼 소실됐다. 원인 수정 범위는 **간격 검출 → 셀 표본화 → 출력 허용**이다. 원본·V1 결과·Unity는 보존한다. V1의 등간격 검사 성공을 정확한 픽셀 복원으로 승격하지 않는다.

후보 비교: 원본 FFT/gradient의 최소4px·강한 경계 간격·축 평균은 이번 source에 맞지 않는다. 다중 주기/배수 후보와 재구성 오차를 비교하는 근사법도 가능한 기술이지만, 미세 특징의 허용 손실을 사용자가 정하지 않았으므로 이번 기본 출력에 도입하지 않는다. **관찰된 동일 RGBA 블록을 정확히 축약하고 동일 source canvas에 완전히 복원할 수 있는 경로**를 채택한다. 숨은 작가의 원래 해상도나 미술 합격을 추정하는 알고리즘은 아니다.

구현 전 수학 계약:

1. 입력 `I[y,x,c]`는 원래 RGB/RGBA uint8, source 원점 좌상단, X오른쪽/Y아래, 단위 source px, pixel centre `(x+0.5,y+0.5)`. 부모/회전 없음. 분석 중 색·alpha threshold·crop·resize 없음.
2. 각 축의 **모든 채널 실제 변화 경계** 좌표를 구한다. 한 축의 변화 위치 차분 GCD는 그 축을 설명하는 정수 step의 상한이다. X/Y의 공통 step은 두 GCD의 GCD이며 축 평균이 아니다. flat 축은 다른 축의 증거를 재사용한다. 정수 약수 후보를 기록하고 가장 큰 무손실 반복 표현을 선택한다. 2/3px 기본 단위를 배제하지 않는다. 관찰된 동일색 그룹 때문에 더 작은 작가 격자와 구분할 수 없는 한계는 공개한다.
3. 전역 위상은 `o=첫 변화 경계 mod s`. 정수 cell map `q(x)=floor((x-o)/s)`로 source 전체를 덮는다. canonical index는 `q-min(q)`다. cell의 source 교집합 안에서 중심을 취한다. source에서 잘린 가장자리 cell도 명시적으로 보존하며 source canvas와 full-cell canvas의 차이를 receipt에 기록한다. 내부 affine inverse는 `source=s*(canonical+0.5)+offset`, Jacobian `diag(s,s)`다. 경계별 이동·누적 round·비균등 scale 없음.
4. 출력 `O[j,i]`에서 **같은 cell map**으로 재구성 `R[y,x]=O[qy(y),qx(x)]`. 전체 source의 RGBA 불일치가 정확히 **0**이어야 출력한다. 허용오차는 uint8 byte equality 0, 기하 정수 계산 오차0. 이 조건은 단일 픽셀 눈·선·alpha 연결/구멍도 source 재표시 범위에서 보존한다. 전체 평균 오차로 작은 특징 손실을 숨기지 않는다.
5. 공통 step≤1, 경계 증거 부족, 비균일/분수/보간/연속 명암으로 정확 복원이 안 되면 `rejected`로 중단한다. 원본과 실패 진단만 보존하며 PNG를 성공 결과로 쓰지 않는다. 이미 native1px인 입력과 격자 없는 그림의 의미는 raw byte만으로 구별할 수 없으므로 이 경로에서 새 정규화라고 꾸미지 않는다.
6. 확대는 canonical의 정수 nearest 반복 표시다. 임의 축소는 서로 다른 픽셀을 버릴 수 있으므로 모든 작은 화면 해상도에서 특징 보존을 약속하지 않는다. 이번 변경은 Unity의 실제 표시·공통PPU를 바꾸지 않는다.

최소 마지막 검사: 2/3/4/8배의 알려진 RGBA 복원, 가는 선/눈·alpha-only 격자, 축별 다른 배수의 공통기본간격, 잘린 가장자리, 블록 내부1px반례·연속 gradient·단색 거부, 실제B37 거부, HTTP에서 거부입력의 PNG 미생성/진단노출. 원본 B37 측정은 source와 보존된 출력만 읽었다: visible RGB 154,249색, alpha256단계, RGB 변화 경계 차분 GCD X/Y=1. 기존 inverse 표시의 visible 불일치89.56%는 특징 손실률이나 미술 점수가 아니다.

근거: [Aseprite 정수 nearest 확대](https://www.aseprite.com/api/command/SpriteSize), [CLI 확대](https://www.aseprite.com/docs/cli/); [공개 fixer의 배수·콘텐츠주기·drift·재구성 오류 논의](https://github.com/Retro-Diffusion/pixel-art-fixer/blob/main/docs/HOW_IT_WORKS.md). nearest는 아는 격자의 표시 기능이지 격자 복구 증명이 아니다. V2의 GCD+정확 byte 재구성은 이 프로젝트의 명시적인 보수적 구현이며 외부 fixer를 설치·실행했다는 뜻은 아니다.

### 현재 실행·실제 증거

`Start_Uniform_Web.cmd`·`http://127.0.0.1:8768`의 V2를 사용한다. 같은 입력을 선택하면 verified_lossless 결과 또는 **변환 중단 진단**이 표시된다. 성공 PNG는 정규 native 크기로 저장하고 확대는 CSS에서만 한다. 실패에는 source bytes와 failure.json만 남으며 output.png는 없다. CLI 실패 exit code2는 무손실 모델 거부다. `--engine/--deps`는 V1 호출의 경로 호환 인자이며 V2 검출은 원본 엔진을 호출하지 않는다. 원본 엔진 파일도 수정하지 않았다.

`graph-v2.json`의 실제 시트 판정 → 독립 fixture → HTTP 마지막 검증은 3단계 완료했다. `docs/artifacts/building37/Uniform02/failure.json`: source 1489×1056, 양축 변화 경계 차분 GCD1, **NO_LOSSLESS_COARSER_LATTICE**, 판정0.032초. 12개 기술검사(배율2/3/4/8, 가는 선/눈, 축별 배수 공통2, 부분 가장자리, 미세주입·gradient·단색·hiddenRGB 거부, alpha-only, flat축, 실제source/CLI)와 HTTP7조건 통과. 알려진 HTTP입력 처리0.042초/계산0.0016초는 그 fixture의 측정이며 일반 입력 시간 보장이 아니다. 새 V2 게임용 canonical이나 원본 아트 재제작은 하지 않았다.

정수 반복 셀 밖의 보간/명암 차이가 있는 입력·비정수 확대·혼합 격자는 이번 보수적인 모델에서 거부될 수 있다. 이 한계를 임계값 완화나 팔레트 감소로 숨기지 않는다. source가 이미 native1px이면 원본을 쓰며, 더 굵은 픽셀 아트를 원할 경우 별도 저작/근사 복원의 정보 손실 계약이 필요하다. V1의 graph.json/recovery.json과 314×223 결과는 보존된 과거 증거이며 V2 제작에 재실행하지 않는다. Unity의 바닥/가구 표시 밀도 문제는 별도 미해결이다.

마지막 실제 서버 확인에서 V2 HTML과 V1 메모리 계산 서버가 함께 남아 있던 문제를 발견했다. 이전 실행기를 교체했고 버전2/계산SHA 일치/리스너1개를 `Uniform02/live-server.json`에 기록했다. 화면은 health의버전2 확인 전 처리버튼을 활성화하지 않는다. 새실행기는Windows동일포트다중bind를막고 같은코드SHA의V2만재사용한다. 서버부분수정후 HTTP7조건을 `web-tests-final.json`으로1회재검증했으며 순수검출12건과실제source판정은변경되지않아재실행하지않았다.

## V1 설계·증거 — 보존 기록

사용자 관찰은 공식 웹 데모에서 형태가 볼록/오목 거울처럼 뒤틀리는 현상이다. 최근 upstream 변경으로 단정하지 않는다. 원본의 `refine_grids`는 각 경계를 이미지 gradient 근처로 옮기고 그 위치에서 다음 경계를 누적한다. 서로 다른 원본 폭이 각각 출력 한 칸이 되어 국소 확대/압축이 생길 수 있다. `refine_intensity=0`도 매번 반올림한 위치를 재사용하므로 분수 간격의 누적 오차를 없애지 못한다.

**채택:** 원본 PerfectPixel 자동 간격 검출을 재사용하고, 후속 sampling을 하나의 전역 등간격 좌표변환으로 교체한다. 이는 무수정 원본의 최종 출력이 아니라 별도 correction이다. 원본 엔진·입력·옛 결과·Unity 배치는 수정하지 않는다. 새 시트 제작이나 개별 사물 크기 보정은 범위에 없다.

## 좌표·계산 계약

- 입력은 원래 해상도의 RGB/RGBA uint8, 원본 픽셀 중심 좌표는 `(k+0.5,l+0.5)`다. 브라우저의 1024px 축소, 팔레트/alpha 변환, 수동 목표 해상도, 실패 시 8px fallback은 없다.
- 원본 `detect_grid_scale`의 FFT→필요 시 gradient 분기와 반환값을 변경하지 않는다. 최종 정수 크기로 반올림하기 전 검출 개수 `(gx,gy)`에서 공통 간격 `s`를 원본과 같이 계산한다: 축 간격 `W/gx,H/gy`의 비가 1.5 초과면 작은 값, 아니면 평균. 호출·backend·파일 SHA를 receipt에 기록한다.
- 각 축 경계의 RGB 차이 프로파일 `e[k]`에서 `C=Σ e[k] exp(-2πik/s)`를 계산하고 전역 경계 위상 `o=(-s arg(C)/(2π)) mod s`를 구한다. 투명 숨은 RGB는 위상 계산에서만 opacity로 가중하며 alpha 경계도 포함한다. 입력/출력 색은 변경하지 않는다. `|C|/Σe`는 진단값이고 검출 정확성의 증명이 아니다.
- 원점 `c0=(o+s/2) mod s`, 좌표 `ci=c0+i*s`를 **매번 원점에서 직접 계산**한다. X/Y가 같은 `s`를 쓴다. 원본 범위 `[0,W)×[0,H)` 안에 중심이 있는 표본만 취한다. 끝 경계를 W/H에 강제로 맞추지 않으며 마지막 칸을 늘리거나 복제하지 않는다.
- 출력 canonical PNG의 `(i,j)`는 원본 `[floor(cy_j),floor(cx_i)]`의 정확한 RGB(A)다. 잠재 좌표변환의 Jacobian은 `diag(s,s)`로 일정하다. nearest 표본 오차는 축당 원본 0.5px 이하다. 정수 source index 간격이 4/5px로 번갈아도 이 반 픽셀 양자화이며, 경계 탐색/누적 round에 의한 warp가 아니다.
- PNG를 저장한 뒤 추가 축소/확대/재정규화하지 않는다. 1/2/4/8배 표시는 CSS 정수 nearest 미리보기이며 원본과 출력 해상도를 구분한다.

## 실패·한계와 판정

검출 None/비유한 간격/1px 미만·RGB 경계 없는 단색 입력·비지원 모드는 오류로 중단한다. 격자가 불명확하거나 FFT/gradient가 다른 후보를 내는 경우 경고를 표시한다. 위상 신호가 없으면 0의 좌표 관례를 명시하고 `unconfirmed`로 표시한다. 검출된 간격과 위상이 틀리면 세부 특징을 잃을 수 있다. **등간격 성공은 가짜 픽셀의 정확한 복원·디자인 합격이 아니다.** 이미 원본에서 실제 선이 휘어 있으면 이 경로는 그것을 펴는 재그리기를 하지 않는다.

독립 판정: 알려진 정수 블록 원본의 전체 RGBA 복원, 분수 간격의 좌표 표식/직선에서 누적 변형 없음, 빈 이미지의 실패, 같은 실제 시트에서 기존 비균일 경계와 새 등간격 비교, HTTP에서 입력 bytes/결과/receipt 보존. 실제 Unity의 바닥/가구 픽셀 밀도 불일치는 이 도구 작업의 완료 기준이 아니다.

## 사용

`Start_Uniform_Web.cmd`를 실행하고 이미지를 선택한 뒤 **정규화 실행**을 누른다. 로컬 `http://127.0.0.1:8768`만 사용하며 결과와 입력은 `runs/<고유 실행>/`에 보존한다. 외부 전송은 없다. RGB/RGBA 정지 이미지, 4MP/20MiB 제한이다. 결과 PNG와 receipt를 다운로드할 수 있다. 새 탭은 같은 서버를 재사용한다.

CLI는 `uniform.py --source <원본> --output-dir <아직 없는 결과 폴더>`다. 기본 엔진은 `Desktop/GPT/3/perfectPixel-main/perfectPixel-main`, 의존성은 기존 `LocalOnly/PerfectPixelOpenCV`이며 `--engine`, `--deps`로 경로만 변경할 수 있다. 수동 출력 크기는 받지 않는다.

`graph.json`은 실제 B37 시트 → 전역 계산 → 마지막 기술 검증의 WorkLoop 그래프다. 기존 출력이나 이미 끝난 상태를 반복 실행하지 않는다. 테스트는 제작 이후 한 번에 수행하며 그래프의 완료는 이 보정 도구의 기술 조건에 한정한다.

## 실제 증거

- B37 원본 1489×1056 → 별도 결과 **314×223**, 자동 공통 간격 **4.7472324723 원본 px**. 계산 0.346초, 등간격 오차 최대 `1.98e-13` 원본 px, nearest 중심 오차 최대 `0.49929` 원본 px. `docs/artifacts/building37/Uniform01/output.png`·`receipt.json`에 원본/엔진 SHA와 선택 좌표를 보존했다. 출력 가장자리 정책 때문에 검출기의 반올림 높이 222와 실제 표본 수 223은 다르며 강제로 맞추지 않았다.
- 이 시트의 위상 coherence X=0.0213/Y=0.00173으로 약하다. **격자 미확정**으로 표시한다. 출력은 국소 warp를 하지 않지만 원본 특징이 완벽히 복원됐다고 승인하지 않는다. 기존 301×211·Unity 참조는 그대로다.
- 최초 마지막 검사에서 단색 입력이 원본 FFT의 허위 간격을 받는 반례가 실패했다. RGB 경계가 없는 입력의 거부를 추가했다. 실제 시트 출력은 재계산하지 않고 `recovery.json`에서 영향받은 실패 분기와 전체 기술 검사 5건을 통과했다. 첫 실패와 후속 통과 기록을 모두 보존했다(`tests.json`, `tests-after-blank-fix.json`).
- HTTP 6개 조건 확인: 알려진 4배 블록 입력의 정확한 RGB 복원, 원본 bytes/PNG/receipt 다운로드, 외부 Origin 거부, 단색 실패 표시·보존, HTML의 canvas 축소 없음. 시험 입력 HTTP 처리 0.081초이며 일반 이미지 전체 처리 시간 보장은 아니다(`web-tests.json`). 실제 개인 브라우저 UI 조작은 하지 않았다.
- `output-preview-x4.png`는 **314×223 canonical의 정수 nearest 4배 미리보기 1256×892**다. canonical PNG의 재가공본으로 사용하지 않는다. 새 생성 이미지가 아니다.

## 기술 근거

- [원본 PerfectPixel](https://github.com/theamusing/perfectPixel/blob/main/src/perfect_pixel/perfect_pixel.py): 자동 검출/경계 refine와 sampling을 구분한다.
- [공식 웹 구현](https://github.com/theamusing/perfectPixel_webdemo/blob/main/services/perfectPixelService.ts), [웹 입력 전처리](https://github.com/theamusing/perfectPixel_webdemo/blob/main/App.tsx): 국소 경계 탐색과 입력 축소는 각각 별도 원인 후보다.
- [NumPy DFT 정의](https://numpy.org/doc/stable/reference/generated/numpy.fft.fft.html): 위상의 부호/주기 계산 근거. 임의 주파수 한 점의 합을 직접 계산한다.
- [SciPy affine pull transform 정의](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.affine_transform.html): 출력→원본의 일정 행렬/offset 방식 근거. SciPy 추가 설치 없이 직접 nearest index로 구현한다.
