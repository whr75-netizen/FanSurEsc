# Grave Seasons 기준 2D 맵 아트 — 첫 상가

## 현재 결정 — B33 두 버전 모두 거절, 자동 격자 복원으로 전환

**최신 사용자 정정:** 출력 크기를 임의로 줄이지 말고 원본 PerfectPixel의 픽셀 크기 추정을 사용한다. 전체 맵 아트를 기준으로 각도・비례・역할을 정한 뒤 개별 오브젝트로 제작/배치한다. 최신 우선 작업은 Astra Ultra 리뷰와 게임 개발 운영 방식의 교정이다. 새 컨셉 생성이나 기지 교체를 아직 완료하지 않았다.

### 확인된 원인과 교정

`normalize_art.py`와 `normalize_uniform.py`는 자동 격자 검출을 하지 않았다. 슬롯/임의 PPU → 목표 해상도 → 수정판 `normalize_triggered(clean, target)` 경로였다. 계산대 crop1179×992를102×85, 진열섬1330×967을89×64, 램프808×1368을32×54로 압축했다. 선택된 원본 RGB 일치 검사는 정보 보존의 증거가 아니었다. 기존 두 Python 실행과 Unity Build/Apply는 새 제작 진입점에서 차단하고 원본/씬/역사 자료는 보존한다.

`Tools/Building33/native_normalize.py`는 Desktop GPT/3의 원본 public API를 호출한다. `grid_size=None`, `fix_square=False`, center sampling이며 crop/resize/알파 임계값/경계 복사/팔레트 변경이 없다. 원본 selector가 선택한 NumPy backend를 사용했고 엔진 파일은 수정하지 않았다. RGBA 알파는 원본 RGB와 같은 검출 셀 중심에서 취한다.

실제 계산대 입력1374×1145 → 원본 자동 추정275×229(5 source px/cell) → 경계 정렬 후274×228. 투명 여백을 포함한 전체 크기이며 종전102×85는 crop 뒤 강제 출력이므로 bbox와 전체 canvas를 혼동하지 않는다. [원본 검출 receipt](../artifacts/building33-native-probe/receipt.json)에 입력・엔진・출력 해시와 실제 셀 경계가 있다. 이는 자동 경로 사용의 증거이지 미술・배치 통합 합격이 아니다. 단색 입력은 원본 NumPy 오류로 실패했고 임의 grid fallback을 만들지 않았다.

### 제작 절차와 원본 적합성

| 단계 | 권위 입력 → 산출・실패 분기 |
|---|---|
| 기준 아트 | Grave Seasons 사용자 참고와 기존 상가 역할/도면 → 전체 상가 컨셉. 게임에 한 장 배경으로 넣는 산출이 아니다. |
| 개별 자산 | 기준 아트의 같은 물체・각도・논리 픽셀 밀도 → 별도 오브젝트. 보이는 부분 crop과 가려진 부분의 생성 보완을 구분한다. 후자를 원본 추출이라고 하지 않는다. |
| 격자 복원 | 가능하면 같은 master/asset sheet의 공통 격자 → 동일 좌표선에서 분리. 독립 생성물은 검출 결과가 같다는 가정 금지. 불일치는 저작 단계로 반환한다. |
| 배치 | 기준 anchor・공통 투영・템플릿의 좌표 → world 크기/pose. 슬롯에 맞지 않으면 오류이며 자산 축소로 숨기지 않는다. |
| 납품 | 실제 기지 결과와 미해결 항목. 파일・정수 표시・좁은 그래프 완료를 미술 완성으로 승격하지 않는다. |

좌표 계약: 원본 RGBA는 좌상단 원점, +x오른쪽/+y아래, 단위source px. 검출 경계배열 `gx/gy`의 셀 중심을 원본 함수로 샘플링하여 논리texel 하나로 저장한다. 출력size는 경계 수-1이며 수동 W/H가 아니다. 템플릿의 world(m)와 이미지(texel) 사이 공통 밀도/anchor의 교정 자료가 없는 동안 world 배치를 계산하지 않는다. 원본의 불규칙 격자, 숨은RGB/투명 여백, 겹침/가림, 색 대비가 검출을 방해할 수 있으며 자동 검출은 무손실 복원이나 각도 교정이 아니다.

후보 결정: (A) 슬롯 기반 축소는 기각; (B) 기존 자산의 원본 자동 격자 추정은 실행 가능한 정규화 단계로 채택하되 서로 다른 자산의 공통 밀도는 미확정; (C) 전체 기준 아트와 공통 asset sheet 기반 제작은 다음 제작 경로. 가려진 부분・projection calibration은 아직 해결하지 않았다. 이번 운영 교정에서 새 이미지 생성/Unity 배치를 임의로 진행하지 않는다.

## B33 가변 크기 수정의 과거 기록 — 사용자 거절

**최신 사용자 계약:** 실제 물체의 크기는 서로 달라야 하며 같아야 하는 것은 픽셀의 크기다. 기존 B33의 강제64×64·비균등 맞춤 결과는 거절 상태로 보존한다. **단일 축척·가변 크기 수정본의 실제 Unity 통합과 제한된 기술 검증은 완료했다.** 새 uniform graph는3단계에서 `graph_complete`, [기술 결과](../artifacts/building33-uniform/technical-result.json)는 `technicalReady:true`/오류0이다. 이는 원본 내부 각도·팔레트·미술 품질의 승인이 아니며 새 수정본의 사용자 미술 판단은 아직 남아 있다. 아래의 이전 거절본·조명 실패는 당시 증거다.

### 입력·치수·변환의 새 계약

[uniform-art-manifest.json](../artifacts/building33/uniform-art-manifest.json)과 `Tools/Building33/normalize_uniform.py`가 새 변환의 원본이다. 원본 생성 이미지9종과 거절된 이전 PNG/manifest를 보존하고 새 자산은 `Assets/Art/PlannedPixelBuilding33Uniform/`에 쓴다. 수정 PerfectPixel의 `source_regions`를 사용하며 팔레트·톤·선 재작성은 없다. 바닥·벽의 canonical 경계 마스크와 원본 내부 형태는 다른 계약이다.

원본 crop 크기 `(Ws,Hs)`와 B32 예약공간을 투영한 상한 `(Wmax,Hmax)`에서 **`q=min(Wmax/Ws,Hmax/Hs)` 한 개만** 계산한다. native 크기는 `(floor(Ws·q),floor(Hs·q))`이며 공통64×64 상자나 x/y별 비균등 scale은 사용하지 않는다. 정수화 때문에 각 축에1 native pixel 미만의 오차가 남으며 연속적인 aspect가 수학적으로100% 같다고 주장하지 않는다.

| 개별 자산 | 새 native 크기 | 배치 의미 |
|---|---|---|
| 계산대 | 102×85 | 계산대 역할의 예약공간 안에서 원본 비율로 표시 |
| 뒤쪽 선반 | 109×126 | 뒤벽 진열 역할 |
| 왼쪽 선반 | 71×118 | 좌벽 진열 역할 |
| 낮은 진열섬 | 89×64 | 낮은 상품 진열 역할 |
| 재고 선반 | 94×119 | 재고/직원 공간 역할 |

**B32 사각형은 예약공간이며 실제 물체 전체를 그 사각형으로 늘이라는 명령이 아니다.** 새 물리 proxy의 폭/깊이는 그 공간 안에서 축소하고 사용면·통로·벽/지지 관계는 보존한다. 이 proxy는 배치/충돌용 추정치이며 이미지 bbox로 정확한 CAD 체적을 복원했다고 하지 않는다. manifest에는 bbox에서 추정한 시각 높이와 기존 collider 높이의 차이를 한계로 기록한다. 단일 q는 원본 내부 각도·비례를 변형하지 않으려는 변환이지 생성 원본에 있던 원근·방향 오류를 고치는 알고리즘이 아니다.

### 공통 픽셀과 기존 건물 연결

새 PPU는 **`P=32√2=45.254834`**로 이전의2배다. 2m 바닥 타일은128×64 native pixels이며 물체마다 필요한 texel 수가 다르다. 실제 화면높이857px/ortho4.734301에서 `s=857/(2×4.734301×45.254834)≈2`이며 **한 source pixel당 화면2칸**을 확인했다. 5개 물체 각각 x/y source cell의 측정 오차는0.00008 screen pixel 미만이고 transform scale은 모두1이다. 이전의 화면4칸 픽셀보다 source 정보 밀도를2배로 한 선택이며 건물/물체를 모두 같은 화면 크기로 만든다는 뜻이 아니다. 기존 CameraZoomController 안에서 정수 배율을 적용했다.

`PlannedPixelBuildingUniformRevision.Apply()`는 기존 prefab의 자산/mesh/material 참조와 해당 표시·proxy 데이터만 수정한다. 새 건물·Player·Camera를 만들지 않고 기존 씬 인스턴스와 소유권을 유지한다. 메뉴는 `Tools > World Art > Apply B33 Uniform Source Revision`; `Capture B33 Uniform Display Readback`으로 각 물체의 실제 texture 크기·source cell 화면폭·transform scale을 기록한다.

### 실제 기술 검증과 조명 원인 수정

사용자 정정으로 이전 계약 실행을 보존·정지하고 **새 `Tools/Building33/uniform-graph.json`**을 연결했다. 기존 실행의 판정 기준을 바꾸어 실패를 성공으로 만든 것이 아니다. 새 흐름은 `기존 prefab에 apply → 실제 building/display 관측 → 기술 판정`이며 최종 미술 판단은 사용자에게 남긴다. 상세 실행은 [B33 README](../../Tools/Building33/README.md)에 있다.

[최종 readback](../artifacts/building33-uniform/readback.json)과 [물체별 표시 관측](../artifacts/building33-uniform/unity-display.json)은 다음을 기록한다.

- 실제 GameMap1, 카메라30.000004°/349.999969° 직교·ortho4.734301·PPU45.254833·화면2px/source cell. 시설5개는 서로 다른 texture 크기·물리 collider 크기이며 모두 예약 slot 내부에 있다.
- `[Play Mode 호출 확인]` 사용점6/6 도달·벽 차단·실내 가림 통과. 전후 실제 Player/Camera entity ID가 같고 Missing Script0이다. 물리 키 입력을 보냈다는 뜻은 아니다.
- 새 Console 오류0. 기존09:50의 relay 오류1개는 변경 없이 보존했다. 마지막은 Edit Mode의 GameMap1 저장·clean 상태이며 SceneView도30°다.
- 실제 결과는 [실내](../artifacts/building33-uniform/play-interior.png)·[실외](../artifacts/building33-uniform/play-exterior.png)로 보존했다. 관측값만 제출하고 실제 건물 화면을 생략하지 않는다.

**조명차이0의 확인된 원인:** 기존 `CharacterSilhouetteRendererFeature`의 반대 방향 depth copy 두 draw가 같은 material을 공유하면서 마지막 입력 바인딩이 앞선 copy에 영향을 주었다. 같은 feature 안에서 각 draw에 `MaterialPropertyBlock`으로 별도 source depth를 전달하도록 수정했다. DepthOnly/DepthNormals의 alpha·격자 정렬 보완과 이 바인딩 수정은 서로 다른 책임이다. 새 Lighting Manager를 추가하거나 캐릭터 feature를 끈 상태를 최종 해결로 삼지 않았다.

수정 후 **캐릭터 feature가 켜진 실제 경로에서 광원 ON/OFF195,848픽셀 차이**를 확인했다(수정 전0). feature를 끈 진단 case의200,487픽셀 차이는 해당 의존성을 분리한 반례이며 최종 플레이 설정이 아니다. 따라서 local light의 실제 기여를 확인했지만 그 크기 자체로 명암의 미술 품질을 합격시키지 않는다.

### 남은 미술·표현 한계

가변 크기·단일 q는 생성 원본의 내부 투영/각도 오류를 고치지 않으며, bbox에서 유도한 시각/물리 높이도 정확한 CAD 복원이 아니다. 원본의 픽셀 클러스터·팔레트·명암·상품 디테일과 Grave Seasons 수준의 디자인 동등성은 사용자 미승인이다. 기존 local light는 방사형 영향 함수이므로 실제 벽/가구 occluder를 따라 빛을 막는 기능은 없고 경계를 넘는 빛이 남을 수 있다. 실제 occlusion-aware 조명이 구현됐다고 주장하지 않는다.

이제 피드백은 이 **통합 건물 전체라는 최종 관찰 단위에서 한 번** 받는다. 중간 PNG·기술 통계마다 질문하여 작업을 종료하지 않으며, 추가 수정이 오면 지목된 자산/표시/조명 책임 단계에 연결한다.

---

## B33 거절본 보존 이력 — 강제64×64 정규화와 첫 통합

**2026-09-27 최신 사용자 판정: B33 외형 거절.** 사용자는 더 뭉개진 표현·잘못된 각도·이중 픽셀처럼 보이는 결과를 지적했다. 단순 미응답/승인 대기로 기록하지 않는다. B33은 GameMap1 기존 위치의 10×8m(80m²) 단층 점포에 B32 시설5개·벽등2개·총79 renderer를 통합한 상태다. **실제 이동·가림·동일 Player/Camera와4배 픽셀 표시는 확인했으나, 이것은 거절된 아트의 품질을 정당화하지 않는다. 동적 광원 차이도0이어서 기술 완료 역시 미완료다.** 강제64px canvas 및 nonuniform 정규화가 이번 시각 실패의 원인 후보이며, 원본·변환 manifest로 먼저 분리한다. 아래 B32/B31/A30은 당시 결과를 보존한 이력이다.

### 제작 원본과 정규화의 실제 범위

[art-manifest.json](../artifacts/building33/art-manifest.json)이 원본 경로·해시·crop·native 크기·원본/목표 비율·실행 시간을 보존한다. 원본 9종은 새 생성 이미지인 `counter`, `rear_shelf`, `left_shelf`, `island`, `stock_shelf`, `floor`, `wall_left`, `wall_right`, `lamp`다. 벽등 2개는 같은 lamp 자산을 사용한다. 원본은 `Tools/Building33/Source/`, 개별 정규화 PNG는 `Assets/Art/PlannedPixelBuilding33/`에 둔다. 전체 방 한 장을 맵으로 쓰거나 기존 B31 무료 시트를 새 생성물로 설명하지 않는다.

수정 PerfectPixel의 `normalize_triggered`에서 **`cell_sampling.source_regions`만 사용**했다. 셀은 원본 대표 RGB를 선택하며 전역 팔레트·톤 재작성은 하지 않는다. 기록된 9종 정규화 소요 합은 **30.547초**다. 이는 생성·Unity import·통합·관측을 포함한 전체 작업 시간이 아니다. 가구 5종은64×64, 바닥64×32, 벽 각32×64, 램프16×24 native canvas다. 4배 contact sheet는 nearest 표시 미리보기이며 게임 입력이 아니다.

**실제 확인된 비례 손실과 재개 원인:** 각 generated bbox를 역할별 canonical grid에 맞추는 과정은 uniform fit이 아닌 `nonuniform bounding rectangle grid`다. 목표aspect/원본aspect는 계산대0.752824, 왼쪽 선반1.340294, 진열섬0.696129다. 따라서 출력 texel 격자가 정규여도 생성 원본의 내부 비례·투영을 정확하게 보존하지 못했다. B32의 원본aspect 보존 목표를 충족했다는 증거로 이 정규화를 제시하지 않는다. 사용자가 현재 표현을 거절했으므로 해당 자산의 형태/투영·정규화 단계가 재개 대상이다. 강제 가구64×64와 비균등 맞춤이 뭉개짐/각도 오류에 기여했을 가능성은 있지만, 모든 증상의 단일 원인으로 아직 확정하지 않는다. 실제 화면4배 또는 전역 재픽셀화 pass OFF라는 기술 수치로 이 거절을 반박하지 않는다.

### B32 도면을 소비하는 배치와 표시

- **도면:** [B32 layout-plan.json](../artifacts/building32/layout-plan.json)의 시설5개·사용점6개·벽·칸막이·문을 실제 로컬 XZ 미터 좌표로 소비한다. prefab은 `Assets/Prefabs/World/PlannedPixelShop33.prefab`; 기존 Player/Camera 소유자와 기지 흐름을 유지한다.
- **픽셀:** native PPU=`16√2=22.627417`; FullRect가 원본 alpha를 담는다. 현재 카메라 방향30°/350°와 건물yaw305°를 기준으로 공통 표시 격자를 연결한다. `CameraZoomController`의 기존 소유권 안에서 정수 배율을 결정하며 새로운 Camera Manager를 만들지 않는다. 화면높이857px, ortho4.734301에서 `857/(2×4.734301×22.627417)≈4`이며, 새 Play readback도 source 한 칸당 화면4칸·pitch30.000004°/yaw349.999969°를 기록했다. 이 확인을 미술·광원 전체 합격으로 확대하지 않는다.
- **바닥 alpha 이음새:** 원본 타일의 투명 영역 아래에 실제 바닥+벽 footprint에서 계산한 foundation mask를 둔다. 색은 바닥 원본 불투명색의 대표값이며 임의 테두리 덧칠이 아니다. 같은 높이에서 foundation queue1999/ZWrite0 → 원본 바닥 queue2000으로 그려 coplanar 깊이 덮임을 막는다. 이 파생 마스크는 생성 원본과 별도 `Derived/foundation.png`로 보존한다.
- **접촉 그림자:** 시설의 실제 footprint를 투영한 별도 mask로 만든다. sprite bbox를 물리 점유로 간주하지 않는다. 그림자 표시와 collision 원본을 구분한다.
- **개발 시점:** 기존 SceneView 정렬 메뉴와 B33 Inspect/실내 표시 메뉴가 같은30° 직교 개발 시점을 제공한다. editor의 지붕·앞벽 숨김은 SceneVisibility 상태이며 게임의 fader 규칙을 대신하지 않는다.

### 명암 층과 기존 조명 재사용

기본 면 구분·상품 디테일은 원본 아트에 있고, 접촉 그림자는 footprint mask이며, 공간 광원은 기존 **SteppedLocalLight / SteppedLocalLightRendererFeature**를 재사용한다. 두 벽등 각각 radius4.5m, intensity0.24, surface/halo3단계, normalInfluence0, worldCell0.125m다. 새 Lighting Manager나 물체 전체를 다시 픽셀화하는 pass는 추가하지 않는다.

normalInfluence0은 이미 저작한 면 명암 위에 3D normal Lambert 음영을 중복시키지 않기 위한 현재 설정이다. 광원 ON/OFF 실제 화면 차이는 관측 코드가 같은 카메라·pose·시간에서 분리 측정한다. 연결된 조명 수나 셰이더 이름만으로 명암 품질·사용자 만족을 통과시키지 않는다. 고정된 아트 자체 명암과 동적 광원 반응을 같은 것으로 설명하지 않는다.

기존 `IsometricAtlasSurface`에는 depth prepass용 pass가 없어 같은 셰이더에 `DepthOnly`와 `DepthNormalsOnly`를 추가했다. forward와 같은 픽셀 정렬·source alpha clip을 사용하고, foundation처럼 ZWrite0인 표면은 depth/normal에도 쓰지 않아 투명 픽셀이나 바탕면이 가림을 만들지 않도록 했다. **이 보완만으로 조명이 해결되지는 않았다.** 임시 상수색 probe에서는 해당 fullscreen pass 실행이 확인되지만 depth를 직접 Load하거나 Sample한 결과는 여전히0/검정이고 조명 차이도0이다. 현시점에는 depth 생성·전달·바인딩 중 근본 원인을 확정하지 않았으며, 임시 probe 실행을 정상 광원 기여로 기록하지 않는다.

### 확보된 관측과 남은 조명 실패

첫 `[Play Mode 호출 확인]`에서 실제 `PlayerMovement.StepMove`/CharacterController로 사용점6/6에 도달했고, 정해진 시설 footprint와 실제 collider 좌표 오차는0.000001m 미만이었다. 전면 벽 접근은 local z≈−3.375에서 멈췄다. 이는 호출 관측이며 실제 WASD 키 입력 검증이라고 하지 않는다.

Editor hot reload로 중단됐던 관측은 정상 새 Play에서 이어서 확인했다. 현재 readback은 시설5개, 사용점6/6, 가림, 동일 Player/Camera를 통과하고 `lightingObserved:false`, `lightingChangedPixels:0`을 명시한다. 따라서 기술 완료나 정상 동적 조명으로 보고하지 않는다. 최종 결과의 근거는 B33의 Unity readback, 실제 GameView와 `technical-result.json`이며, 조명 원인 수정과 실제 차이 관측 후에만 이 미완료 상태를 갱신한다. readback의 `artisticApproval:pending`은 관측 당시 값이며 **후속 사용자 정정으로 현재 B33 외형은 거절 상태**다. 새로운 자산/표시 수정의 미술 합격은 아직 없다.

작업 흐름과 실제 진입점은 [B33 README](../../Tools/Building33/README.md)에 연결한다. 기술 납품과 사용자 미술 판정은 분리하며, 질문 발신이나 연구 문서 작성으로 건물 완성을 대체하지 않는다.

---

## B32 보존 이력 — 배치·미술·표시 계약 재설계

**2026-09-27 최신 사용자 판정:** B31의 디자인·명암·디테일·배치는 거절됐다. 화면상 크기는 대략 유지할 수 있지만 원본 픽셀이 불규칙하게 표시되는 문제는 고쳐야 한다. Grave Seasons 첨부 화면이 우선 참고이며, 단순 축소·전체 맵 한 장·임의 가구 좌표 나열은 제작 방식으로 채택하지 않는다. **이번 변경은 Scene 뷰 정렬, 표시 결함의 최소 실험, 제작 전 배치 도면과 기술 설계다. 새 건물 미술 완성/승인을 의미하지 않는다.** 기존 B31과 기지 동작은 보존한다.

### 1. 직접 확인한 실패와 책임 단계

| 관측 | 원인/판정 | 수정 책임 |
|---|---|---|
| Scene 뷰21.45°/310.12°, 게임 기본30°/350° | Editor Preview Camera와 실제 SceneView를 혼동했다. | 기존 카메라 소유자에서 회전을 읽어 SceneView.LookAt 적용. 카메라 복제/런타임 변경 없음 |
| 15개 Prop 호출에 좌표·collider 치수 직접 입력 | 기능 구역·사용면·동선 설계도를 소비하지 않았다. 테이블-의자 틈0.5m는 반경0.5m 캐릭터가 통과할 수 없다. | 배치 명세와 configuration-space 경로 계산 |
| pixel pivot은 최하단 불투명행 중점, 물리는 footprint 가까운 꼭짓점으로 취급 | 두 landmark가 같다는 근거 없이 `(-width/2,-depth/2)`를 더했다. | 자산별 접점/바닥면 대응. 이미지 bbox에서 물리 깊이 추정 금지 |
| 원본 PNG는 정수 crop 그대로이나 경계 픽셀이 잘림 | 바닥/벽의 연속적인 메시 사선이 작가가 그린 계단형 alpha를 자른다. | 원본 alpha 전체를 담는 Full Rect 시각 표면; 물리 점유와 구별 |
| GameView857px 높이, ortho5, P=22.627417 | 확대율3.7874408이어서 원본 한 칸이 화면3/4칸으로 섞인다. | 정수 화면 배율·공통 격자 위상. 재생성/축소로 해결하지 않음 |
| 전역 PixelArtRendererFeature OFF, 캐릭터 효과 대상 아님 | B31을 전역 필터로 다시 픽셀화했다는 가설은 현재 증거와 불일치. Point, 압축없음, mipmap없음, renderScale1, AA/MSAA/post OFF | 필터를 추가하지 말고 실제 변환/coverage 수정 |
| B31 재질 MetricLighting0, shadow pass 없음 | 원본 자체 명암만 보존했을 뿐 공간별 조명을 설계하지 않았다. 별도 fullscreen 로컬 조명은 ON이므로 모든 빛이 꺼졌다는 뜻은 아니다. | 기본 아트 명암 / 접촉 / 공간 조명 / 환경색을 분리 |

마지막 Play 결과는 B31의 [실내](../artifacts/building31/play-interior.png), [관측](../artifacts/building31/readback.json)을 재사용한다. 새 Play 이동/가림 검사를 반복하지 않는다. 조명 fullscreen pass의 실제 기여량·normal buffer는 아직 GPU 분리 관측하지 않았다.

### 2. 참고작·픽셀아트 기술에서 채택할 것

- **Grave Seasons 직접 근거:** [공식 개발일지](https://steamcommunity.com/app/3255110/allnews/)의 *Farming Systems & Grids*는 평면 2D, 분할 sprite 정렬, 배치 격자와 상호작용 격자의 분리를 설명한다. *Day & Night Cycle*은 shader lights/normal maps/dynamic shadows 실험 후 직접 그린 빛과 LUT·색조 처리를 선택했다고 밝힌다. 정확한 내부 카메라·PPU·코드는 공개되지 않았다. 30°는 우리 투영 계약이며 원작 내부 수치라고 주장하지 않는다.
- **Cure:** [pixel clusters·banding·AA](https://pixeljoint.com/forum/forum_posts.asp?TID=11299). 같은 의미를 전달하는 픽셀 덩어리를 먼저 설계하고 불필요한 고립점/평행 띠를 줄인다. 픽셀 통계를 미술 판정으로 쓰지 않는다.
- **Derek Yu:** [실루엣→형태→명암→마감](https://derekyu.com/makegames/pixelart.html). 실제 사용 크기에서 사물의 특징이 먼저 읽혀야 한다. 특정 팔레트 수나 선 굵기를 모든 사물의 정답으로 강제하지 않는다.
- **Niklas Jansson:** [제한된 픽셀의 강조·생략·재질](https://androidarts.com/pixtut/pixelart.htm). 정보 밀도를 전면 노이즈와 혼동하지 않는다. 필요한 특징에 픽셀과 대비를 배정한다.
- **Gerstner et al., NPAR2012:** [Pixelated Image Abstraction](https://pixl.cs.princeton.edu/gfx/pubs/Gerstner_2012_PIA/index.php)는 단순 축소/팔레트 양자화가 작은 핵심 특징을 잃는 문제를 다루며 공간 대응과 팔레트를 함께 최적화한다. PerfectPixel을 거치는 것만으로 방향·특징·디자인이 해결된다는 근거가 아니다.
- **Merrell et al., SIGGRAPH2011:** [Interactive Furniture Layout](https://paulmerrell.org/furnitureLayout2.pdf)의 여유공간·순환·상대관계·강조점 구분을 채택한다. 원 논문의 확률적 제안/가중 목적함수를 게임 미술 자동 합격기로 이식하지 않는다.

참고 화면에서 바닥은 낮은 대비의 큰 면, 생활·주방 소품은 기능별 군집, 밝은 부분은 등/모니터/빛받는 상판이다. B31은 바닥과 벽의 반복선이 가장 강하고 물건은 기능을 설명하는 작은 부품이 부족했다. **해상도를 늘리는 대신 정보의 위치를 바꾼다.** 이것은 참고 관찰과 제작 기준이며 새 아트의 합격 판정은 아니다.

### 3. 첫 상가 아트 명세 — 제작 후보

기존 생활잡화점 역할과10×8m 외곽을 유지한 후보다. 원작 주거 주방을 상점에 그대로 복사하거나 보물상자/항아리를 빈 곳에 채우지 않는다.

| 구성 | 역할과 필수 특징 | 명암·디테일 배분 | 별도 데이터 |
|---|---|---|---|
| 바닥/벽 | 이동 가능한 면, 출입구, 벽 하단/코너 | 바닥 전체의 고대비 줄무늬 억제, 코너·접촉에서만 구분 강화 | 타일 경계/alpha 여유·배치 lattice |
| 계산대 | 고객 면·직원 면·상판·계산기 | 전면/측면/상판의 큰 색 덩어리, 서랍 틈/계산기 키 등 식별부 대비 | 양쪽 사용면, 계산기 지지면 |
| 벽 진열 | 선반 단·상품 묶음·가격표 | 선반 내부 음영, 상품 종류별 실루엣; 모든 병/상자를 동일 노이즈로 채우지 않음 | 벽 부착·앞 사용면·상품 소켓 |
| 낮은 진열 섬 | 모서리·상판·묶음 상품 | 통로 뒤 물건을 가리지 않는 높이, 상품에 집중된 대비 | 실제 footprint·지지면·가시성 높이 |
| 재고 | 선반·상자·라벨·작업 여유 | 판매장의 화려함과 구별되는 반복, 구조/재질은 공통 | 입구와 선반 access point |
| 빛 | 광원 위치·영향 영역·접촉 그림자 | 자체 면 구분/국소 빛/환경 색조를 다른 층으로 관리 | light role, mask pivot, receiver, layer/order |

규격에는 `assetId, role, sourcePNG, nativeSize, pixelPivot, groundLandmarks, footprintM, front, useArea, supportSurface, allowedView, requiredFeatures, shadingRole`을 둔다. 의미/방향이 틀린 생성물은 정규화 단계로 보내지 않는다. native 픽셀 입력에는 다시 정규화하지 않는다. 생성 입력은 **원본 보존→격자 정규화 한 번→원본 크기의 특징 확인**이며 PerfectPixel/Aseprite는 특징의 발명이나 임의 축소를 담당하지 않는다. 비교 미리보기의 정수 확대는 표시 도구일 뿐 제작 알고리즘이 아니다.

### 4. 배치 설계 원본과 계산

[배치 JSON](../artifacts/building32/layout-plan.json)이 후보 좌표·영역의 단일 원본이며 [평면도](../artifacts/building32/layout-plan.svg)는 그 파생물이다. 그림을 보고 Unity에서 하나씩 위치를 맞추지 않는다. `compile_layout.py`가 점유·사용공간·접근점·경로와 SVG를 함께 계산한다. 제안값과 확인값을 JSON에서 구분한다.

- local +X 오른쪽/+Y 위/+Z 건물 뒤, Unity 좌수계, m. 평면도는 (x,z), 원점 건물 중심, 부모는 기존 root(-16,0,9), yaw305°, scale1.
- Player prefab radius0.5m/height1.8m 확인값. 추가 여유0.1m는 후보 설계값이며 건축법 수치가 아니다. 장애물을 반경r+여유로 팽창시키고 외곽을 수축한 자유공간에서 입구→필수 사용점의 연결을 계산한다.
- `C_free=(B⊖D_r) \ (O⊕D_r)`. 격자 계산은 cell 전체를 보수적으로 자유 판정하고 4방향 BFS로 모서리 관통을 막는다. 미충족 시 객체 ID·막힌 사용점·관련 점유를 반환한다. 같은 결과를 AI의 “괜찮음”으로 통과시키지 않는다.
- 물리 비겹침, 사용면 비점유, 벽/지지면 부착, 방향 후보와 접근 연결은 hard constraint. 상품 군집·시선·밀도는 명시적인 미술 목표이며 점수 하나로 합격시키지 않는다.
- [Tiled Object Layers](https://doc.mapeditor.org/en/latest/manual/layers/)는 영역/경로/템플릿 편집에 적합하다. [CP-SAT](https://developers.google.com/optimization/cp/cp_solver)는 후보가 많아질 때 정수 배치 제약을 풀 수 있다. 지금 한 채는 고정 도면과 작은 결정적 계산으로 충분하며 새 프로그램/패키지 설치는 하지 않는다.

### 5. 픽셀 표시의 수학 계약과 후보

`개별 PNG texel → asset landmark → 건물 local m → root world → 고정 직교 view → 화면 raster`

canonical은 **오브젝트별 정규 PNG+landmark/footprint manifest**다. 전체방 PNG나 렌더 캡처는 원본이 아니다. 이미지(u,v)는 좌상단 원점, 오른쪽/아래, 픽셀 경계 정수·중심(i+.5,j+.5); UV는 좌하단 원점, 정규화0~1; world는 위의 Unity 좌수계다. `UV=((u+.5)/W,1-(v+.5)/H)`는 texel index→center를 나타낸다. root quaternion은 Unity Quaternion.Euler(0,305,0), camera는Euler(30,350,0). column-vector world=Mroot·local을 사용한다.

상대yaw45°,pitch30°에서 `qx=(x-z)/sqrt2`, `qy=(x+z)/(2sqrt2)+sqrt3*y/2`(위가 양수). `P=16sqrt2`, `X=P*qx`, `Y=P*qy`. 바닥 축의 화면 기울기는1/2, 즉26.565°이며 **카메라 기울기30°와 구별**한다. 이전 B31 절의 ground v 음수 표기는 화면 위 양수 정의와 모순되어 여기서 바로잡는다. 실제 코드의 UV 미분은 바닥·벽·가구 모두 `(1/P)I`지만 메시 범위 밖 texel까지 보존하는 것은 아니다.

| 후보 | 적용/선택 | 실패 조건 |
|---|---|---|
| A. 원본 alpha를 모두 담는 Full Rect + 공통 정수 배율/표시 anchor | **우선 최소 실험.** 기존 입력과3D 물리를 보존한다. SpriteRenderer의 Full Rect 원리이며 현 MeshRenderer는 sprite importer 변경만으로 고쳐지지 않는다. 바닥/벽 plane의 UV 역변환으로 전체 직사각 UV를 담을 수 있다. | tile overhang의 중복·정렬,3D 캐릭터 깊이와 가림을 따로 해결하지 못하면 통합 금지 |
| B. 전체 게임을 순수2D SpriteRenderer/2D Renderer로 전환 | 원작 방식에 가까우나 실제 Player/물리/조명과 통합 범위가 크므로 이번 변경에서 보류 | 엔진 전환을 단순 이미지 표시 수정으로 포장할 때 |
| C. 분리된 sprite layer를 저작 해상도에 그린 뒤 정수 합성 | 고정 시점에서 가능하나 현재3D depth/캐릭터와 합성 비용이 추가되어 보류 | 임의 저해상도 재픽셀화,3D 배경/가림 순서 깨짐 |

[Unity Full Rect](https://docs.unity3d.com/6000.0/Documentation/Manual/texture-type-sprite.html), [Pixel Perfect Camera](https://docs.unity3d.com/kr/6000.0/Manual/urp/2d-pixelperfect-ref.html)는 일부 단계의 공식 근거다. PPC의 SpriteRenderer snapping이 현재 임의 MeshRenderer에도 자동 적용된다고 가정하지 않는다.

화면높이H,orthoSizeS일 때 `s=H/(2SP)`. 정수n 표시에는 `S=H/(2Pn)` 또는 정수 확대+crop/여백 정책이 필요하다. **임의 창 크기·연속 줌·현재 시야·동일한 정수 픽셀 폭을 모두 동시에 보장할 수는 없다.** 원본을 줄이지 않고 기존 CameraZoomController 소유권 안에서 표시 배율을 해결해야 한다. 공통 source lattice의 phase는 `project(anchor)-pivot`; 물리 transform을 반올림하지 않고 표시만 최대0.5 source pixel로 양자화하는 후보다. 자유 회전은 같은 sprite의 숨은 면을 만들어내지 않으므로 별도 방향 원본 없이 지원을 주장하지 않는다.

**R3 최소 실험 계약:** 기존 floor PNG·동일 shader·카메라30°/45°·정수4배·투명 RT를 고정하고 메시 UV coverage만 마름모/Full Rect로 비교한다. 임시 preview scene만 사용하고 기지에 통합하지 않는다. 불투명 원본 texel별 화면16칸 보존, alpha 누락/추가0을 기준으로 한다. 실패하면 UV/coverage 경계로 반환하며 아트 외곽선을 덧칠하지 않는다. 성공은 단일 바닥 coverage 수정 근거일 뿐 타일 연결/전체 건물/조명/미술 합격이 아니다.

최종 통합에 필요한 invariant: 부모변환/정규기저(G01/03/04), 원본aspect·uniformscale(G08/09), landmark 재투영(G10, float허용오차0.01sourcepx), UV와 alpha coverage(G11, 누락texel0), 공통격자(G12, 정수칸·경계0.01px). 골격(G05~07)은 정적환경에 해당없음. 깊이/가림은 collider만으로 입증되지 않으며 같은game camera 관측을 별도로 요구한다. 투영으로 숨은 면이 손실되고 양자화로 subpixel 위치가 손실되는 것은 명시한 정보 손실이다.

### 6. 조명과 작업 그래프의 경계

미술의 면 구분을 지우고 전역밝기만 낮추는 방식은 채택하지 않는다. 후보는 `기본sprite의 면/재질 → 물체별 contact mask → 광원 역할별 별도 light mask → 환경 palette/LUT`다. 원작 기법을 참고하지만 조명 RGB를 모든 사물 원본에 고정해 게임의 움직이는 광원 반응을 대신하지 않는다. 움직이는 빛/물체는 기존 조명 owner와 receiver·normal/depth 계약을 명시한 별도 최소 실험이 필요하다. 현재 world XYZ 광원격자는 원본pixel격자와 다르며 동일 pixelcell로 합성할지 아직 미구현이다.

`요구/참고 → 공간 프로그램·특징 명세 → 배치 계산 → 도면 → 개별 자산 → 정규화(필요할 때만) → 공통 표시 → 조명 합성 → 실제 건물 관찰`

| 실패 | 재개할 단계 | 보존할 결과 |
|---|---|---|
| 사용점에 도달 불가/역할 누락 | 배치 계약과 계산 | 원본 아트·완료된 표시 실험 |
| 용도/방향/핵심 특징 불일치 | 해당 개별 자산 명세/제작 | 평면도·다른 승인 자산 |
| 원본에 없는 잘린 픽셀/불균일칸 | 표시 coverage/scale/phase | 자산 RGB·공간 프로그램 |
| 명암 부족/광원 위치 불일치 | 자체 명암/접촉/공간 빛 중 해당 층 | 비관련 기하·배치 |
| 예전결과 재포장만 함 | source/operation 계약 위반으로 중단 | 원본/이전결과; 생성완료 주장 금지 |

AI는 역할·특징·자산 후보를 작성하고 좌표·접근·정규화·변환은 고정 계산이 소비한다. 기존 WorkLoop를 사용하며 새 AI Manager를 추가하지 않는다. [LLM-Modulo](https://arxiv.org/abs/2402.01817)와 같은 후보생성/외부판정 분리의 근거는 있으나 자연어 계약의 완전성이나 미술 만족도를 자동 증명하지는 않는다. 실제 후속 제작 노드는 미구현이며 이번 도면 계산을 전체 게임 제작 자동화 완료로 보고하지 않는다.

### 7. 실행 결과·재개점

- SceneView는 현재30°/350° 직교로 적용했다. `Tools > World Art > Align Scene View to Gameplay Camera` 및 기존 Inspect 메뉴(Edit Mode)로 재적용한다. 기존 Camera/씬 오브젝트는 변경하지 않았다.
- [실제 계산] 시설5개·사용점6/6 연결, 점유/사용공간/벽 부착/문폭 위반0. 도면 후보이며 Unity 적용/실제 이동 검증은 아니다.
- [격리 GPU 실험] 원본 floor의 정수4배 expected18,368칸 중 기존diamond는1,984칸 누락, FullRect는 누락0/추가0. 같은shader/원본/카메라에서 geometry coverage만 변경했다. 전체 건물 수리가 아니다. [관측](../artifacts/building32/experiment-result.json)과 [실행 설명](../../Tools/Building32/README.md)에 범위/미해결을 기록했다.
- [보존] preview가 dirty flag를 세웠으나 씬 사본과 원본이 byte-identical함을 확인하고 동일 내용을 저장했다. 최종sceneDirty=false, GameMap1 git diff0. 신규Console오류0(기존relay오류1 보존). 새 건물 미술/조명은 미완료다.
- 다음 제작 단위는 **명세에 맞는 계산대·벽 진열·바닥 대표 자산과 그 접점/alpha/방향 계약**이다. 전체 건물 재생성에 앞서 대표 조립의 기능·표시를 연결한다. PixelLab 잔액은 B31에서0으로 확인했으며 새 생성이나 결제는 이번에 하지 않았다.

---

## B31 보존 이력 — 기능 통합됨, 미술·배치는 사용자 거절

**2026-09-27 최신 정정:** 아래 A30의 전체 공간 생성·384px 축소는 사용자가 거절했다. 게임 오브젝트 제작을 전체 이미지로 대체한 범위 오류다. A30 파일은 이력으로만 보존하며 채택하지 않는다. 이번 결과는 GameMap1에 배치하는 독립적인 테스트 점포 프리팹 한 채다. 바닥·벽·카운터·진열 가구·소품은 각각 선택/이동/교체 가능한 자식 오브젝트이며 충돌·출입·가림을 연결한다. 기존 기지, 실제 Player/Camera, 인벤토리와 도시 씬은 보존한다.

### 선택과 외부 근거

- PixelLab 네이티브 건축 키트/개별 가구 생성이 우선 후보였으나 실제 get_balance 응답은 구독 만료(2026-09-20), 사용가능 0회, 잔액 $0다. 생성 호출/결제는 하지 않았다.
- 이번 최소 실험은 [hawkbirdtree의 Isometric Furniture and Walls](https://opengameart.org/content/isometric-furniture-and-walls), CC0, 320×960 원본의 개별 네이티브 픽셀 타일을 사용한다. 새 AI 생성물로 설명하지 않는다. 바닥·벽·가구를 같은 제작자의 한 세트에서 취해 방향/픽셀 밀도를 공유한다. 원본 정수 crop만 허용하며 임의 축소와 PerfectPixel 재샘플링은 하지 않는다.
- 기존 GroundedPropSprite는 세로 투영 압축과 기존 fader 재질 속성 부재 때문에 그대로 재사용하지 않는다. 기존 IsometricAtlasSurface의 Point 샘플링·알파 clip·무추가조명 경로와 UrbanOcclusionFader의 실제 collider ray 판정을 재사용한다. 새 도시/카메라 Manager를 만들지 않는다.
- 변경 전 실제 기지 Play 카메라는 45° pitch / 350° yaw / ortho 5다. **최신 사용자 승인으로 기본 pitch를30°로 변경한다.** yaw350°와 같은 CameraFollow/Camera 인스턴스는 유지한다. follow offset은 기존 camera-space offset을 보존하는 quaternion 변환으로 회전한다. 지역별 전환 제안은 취소했다. 촬영 전용 카메라를 최종 Play 결과로 대신하지 않는다.

### 좌표 계약과 실패 귀속

`원본 PNG 정수 crop → sprite pixel coordinates → 건물 local metres → world → 기존 gameplay camera → screen`

- 이미지 원점 좌상단, u 오른쪽/v 아래, 단위 px. 원본 crop은 RGBA/색을 보존한다. 원본 바닥 모듈 64×32px. 이미지 피벗은 ground contact landmark로 기록하며 그림 높이에서 물리 높이를 역산하지 않는다.
- 건물 local은 Unity 좌수계 +X 오른쪽/+Y 위/+Z 뒤, 단위 m, root scale 1. 타일 한 변 L=2m, 공통 화면 밀도 P=64/(sqrt(2)*L)=22.627417px/m. 원본 벽 수직 높이48px를 그대로 쓰므로 실제 높이는48/(P*cos30)=2.44949m다. 직교 투영 pitch30°, yaw45°(건물 local 기준). 전역 yaw는 건물 root305°를 한 번 합성해350°다. 건물은5×4타일=10×8m이며 캐릭터1.8m의 수직 투영은약35.27px다.
- camera-right r, horizontal camera-away g에 대해 ground `(x,z)`는 screen `u=P(x-z)/sqrt(2)`, `v=-P(x+z)/(2sqrt(2))`(screen up 양수), 높이 h는 `+P*cos(30°)*h`다. 같은 바닥 모듈의 투영은 64×32px다.
- 바닥은 실제 XZ quad와 diamond UV, 벽은 실제 수직 quad와 해당 벽의 저작 crop UV를 연결한다. 가구는 원본 aspect를 유지하는 camera-right/vertical 평면, `world = anchor + r*(u-pivotU)/P + up*(pivotV-v)/(P*cos30°)`로 수직 압축을 정확히 상쇄한다. 물리 footprint는 별도 BoxCollider이며 시각 전체 bbox를 collider로 쓰지 않는다.
- 가구는 단일 시점 2D 카드다. 숨겨진 면/연속 자유 회전/동적 3D 표면 조명은 이 입력에 존재하지 않는다. 기본 시점을 맞추는 이유이며 3D 모델을 복원했다고 하지 않는다. RGB에 기본 조명을 다시 곱하지 않는다.
- 원본 격자·crop 범위/공통 P/바닥 연결은 조립 계산의 invariant. 부위별 임의 scale은 금지. 벽 교차·픽셀 찌그러짐은 투영/UV 단계, 통로 차단은 footprint/배치 단계, 가림 실패는 renderer/collider 등록 단계로 귀속한다.

### 범위와 판별 실험

한 층 점포: 판매·진열 구역, 계산대, 후방 보관 공간, 입구와 통로. 도시 생성/2층/새 루팅 정책/새 캐릭터는 이번 범위 밖이다. 네이티브 에셋에 맞는 원본 정보량을 그대로 보여주며 Grave Seasons와 디자인 품질이 동등하다고 자체 판정하지 않는다.

가설: 개별 native 자산 + 공통 투영/밀도 + 실제 물리 footprint면 한 장의 배경 없이 들어가고 가구를 돌아다닐 수 있다. 참이면 실제 Player가 입구를 통과하고 벽에서는 멈추며 앞벽은 가려질 때 희미해진다. 틀리면 배치/깊이 계약을 수정하고 기술 실패를 미술 질문으로 넘기지 않는다. 마지막 1회에 실제 Play 호출 이동·벽 충돌·가림·기본30°·동일 인스턴스와 정상 게임 카메라 PNG를 묶어 기록한다. WorkLoop는 `Tools/Building31/graph.json`, 증거는 `LocalOnly/Building31/`다. 사용자 외형 판정은 실제 결과를 제시한 뒤 받는다.

---

### B31 실행 결과와 남은 범위

- `NativePixelShop31.prefab`을 GameMap1 `(-16,0,9)`에 저장했다. 원본16종에서 개별 바닥/벽/가구/평지붕을 조립했으며 Renderer78, Collider55, Missing Script0. 네이티브 자산은 Point/압축없음/mipmap없음으로 임포트했다. 새 생성·축소·색 재작성은 없다. 원본은 `Tools/Building31/Source/furnitureandwalls.png`, 출처와 crop/pivot은 `Assets/Art/NativePixelBuilding31/`에 보존했다.
- 실제 기본 카메라30°/349.99997°/ortho5를 확인했다. 기존 Follow offset은 기존 camera-space 좌표를 보존하는 quaternion 변환으로 갱신했다. Editor preview도 같은30°다. 같은 런타임 Player/Camera를 사용한다.
- `[Play Mode 호출 확인]` 실제 PlayerMovement.StepMove/CharacterController로 외부 z=-5.3에서 입구를 통과해 건물 local `(0,.565,-.3)` 도달, partition 벽에는 `(3.95,.565,-.625)`에서 정지했다. 검증 전후 같은 Player/Camera. 물리 키 입력을 보낸 것은 아니다.
- 실내 앞벽10개 fade, 지붕20조각 숨김; 외부 복귀 시 숨긴 지붕0. 뒷벽은 새 `fadeWallsWhenInside=false` 옵션으로 실내에서도 유지하고 실제 ray로 가릴 때만 희미해진다. 기존 도시 호출의 기본값true는 보존했다. 표면 위 항아리는 지지면과 같은 깊이 평면으로 시선 방향을 따라 투영하여 화면 좌표를 바꾸지 않고 테이블 뒤에 잘리는 현상을 수정했다. 1mm 깊이 차이는 coplanar tie만 해결한다.
- 신규 Console Error/Exception 없음. 기존09:50:40 Unity AI relay 종료 오류1개는 보존했다. 의도한 저장 뒤 Play Mode 종료. 촬영은 실제 GameView1114×857이며 사진용 카메라/줌 변경 없음.
- 증거: `docs/artifacts/building31/play-interior.png`, `play-exterior.png`, `readback.json`, `asset-observation.json`. WorkLoop 최종 기술조건 exit0, review ticket `9abe3b6b117b465cb0e039fee809b39b`에서 사용자 미술 피드백 대기. 참조 원작과 외형 동등성은 승인하지 않았다.
- 한계: native 픽셀은 보존하지만 실제 화면 확대율3.78744여서 열 너비3/4px가 섞인다. 정수 화면 배율/자유 오빗의 새 뷰/문짝 애니메이션/루팅 연결/밤 조명/2층은 구현 범위에 포함하지 않았다. 문은 실제 열린2m 진입구다. 기존 카메라 오빗은 남아 있으며 현재 아트는 기본 고정 시점용이다.
- 접근: Play 후 `Tools > World Art > Inspect Native Pixel Shop 31`. 기존 실제 Player를 점포로 옮기며 Camera의 각도/줌을 바꾸지 않는다. Edit Mode에서는 선택/SceneView framing만 한다.

아래는 **거절된 A30 실험의 보존 기록**이다. 현재 제작 지시가 아니다.

## 확정 요구와 이번 범위

2026-09-27 사용자 정정: 대부분의 환경을 2D 픽셀아트 이미지로 제작한다. 첨부 Grave Seasons 실내 화면의 시점, 캐릭터 대비 가구/문 크기, 실내 완성도를 우선 참고한다. 맵 아트 설계 → 건물 설계도 → 사물 배치 설계 → 생성 → 공통 픽셀 격자 정규화 순서다. 기존 3D 도시의 철거나 Unity 렌더러 교체 요청으로 확대하지 않는다.

이번 제작 단위는 기존 상가 우선 요청을 잇는 생활잡화점 1채다. 골목 배치, 두 층의 공간 프로그램, 1층 물건 배치와 1층 실내 픽셀 이미지가 산출물이다. 상층/외관 전체 픽셀아트, 개별 스프라이트 분리, 캐릭터 애니메이션과 Unity 통합은 이 첫 이미지의 승인 이후 별도 작업이다. 비율용 인물은 새 캐릭터 디자인 확정이 아니다.

## 직접 근거와 선택

- [Grave Seasons 공식 개발일지](https://steamcommunity.com/app/3255110/allnews/), `Devlog: Farming Systems & Grids`: flat 2D isometric, 분할한 스프라이트와 런타임 앞뒤 정렬, 대부분 배경의 자유 배치를 설명한다. 픽셀 격자와 월드 배치 격자는 다른 계약이다.
- 같은 공식 페이지 `Devlog: Day & Night Cycle`: 의도적으로 저작한 조명과 시간대 색 조정을 설명한다. 첫 정지 아트의 명암을 Unity 동적 조명 검증으로 보고하지 않는다.
- [Aseprite Sprite Size](https://www.aseprite.org/docs/sprite-size/): 캔버스 크기와 이미지 내용 크기 변경을 구분한다. Aseprite를 거쳤다는 사실만으로 생성물의 방향/비례 오류가 고쳐지는 것은 아니다.
- 로컬 수정 PerfectPixel의 `trigger_cli.py`와 `source_sampling.py`를 직접 확인했다. `source_regions`는 셀의 원본 대표색을 고르며 전역 팔레트를 새로 만들지 않는다. 셀보다 작은 선/무늬는 손실될 수 있다. 책상 전용 3/4색 grain 경로는 사용하지 않는다.

| 후보 | 선택 판단 |
|---|---|
| 각 소품을 프롬프트만으로 별도 생성한 뒤 조립 | 각도/높이/빛이 서로 달라질 수 있음. 최초 기준을 만드는 경로로 사용하지 않음 |
| 치수 평면·공통 투영 가이드 → 하나의 공간 아트 → 정규화 | **첫 실험 채택.** 먼저 공간 전체 비례를 사용자에게 확인. 이후 같은 기준으로 분리 자산 제작 |
| 기존 3D 도시 렌더를 최종 아트로 재처리 | 이번 사용자 정정의 주 제작 경로로 채택하지 않음. 기존 결과는 보존 |

가설: 같은 설계와 투영 가이드를 함께 주면 별도 프롬프트 생성보다 한 장 안의 방향·비례를 일관되게 유도할 수 있다. 생성은 정확한 기하 계산기가 아니므로 보장은 아니다. 정규화는 색 샘플 격자만 확정한다. 원근/문 위치/가구 누락을 수선하지 않는다. 결과에 설계 위반이 보이면 해당 위치와 사실을 남기고, 사용자 답변 전 자동 재생성하지 않는다.

## 좌표와 아트 규격 — 첫 제작 가정

첨부 화면의 평행선은 대략 기울기 ±0.5인 2:1 디메트릭이다. 원작의 내부 해상도/PPU를 확인한 것은 아니다. 본 제작에서 쓸 값은 다음처럼 명시한다.

`plan metres → orthographic guide pixels → image-generation raster → PerfectPixel logical cells → integer display preview`

- 평면 원점은 건물 뒤쪽 모서리. x는 화면 오른쪽 아래, z는 왼쪽 아래, h는 위. 월드 물리/Unity 좌표를 변경하지 않는다.
- 논리 캔버스 **384×384**, 이미지 원점은 좌상단, 화면 y는 아래. 투영 원점 `(210,135)`.
- `u=210+20(x-z)`, `v=135+10(x+z)-10√6·h`. 평면 1m 기저는 `(20,10)`과 `(-20,10)`이다. 정투영 카메라의 방위45°·고도30°에 해당하는 근사 기준이며 원작 카메라 값을 단정하지 않는다.
- 0.8m 바닥 모듈의 마름모는32×16px. 가구는 이 칸 중앙에 강제로 묶지 않는다. 최종 앵커는 논리 픽셀에 반올림하고 오차는 각 축≤0.5px다. guide는 모든 꼭짓점에 같은 식을 사용한다.
- 비율 인물1.8m≈44px, 카운터1.1m≈27px, 문2.5m≈61px, 냉장고2.2m≈54px. 원작에서 측정한 정확한 치수가 아닌 제작 입력이다. 문/가구의 전체 바운딩박스에는 바닥 깊이 투영도 들어가므로 수직 모서리끼리 비교한다.
- 생성 안내 캔버스는 논리 가이드의4배인1536×1536이다. 생성기가 반환한 실제 크기는 별도 기록한다. 같은 정사각 비율일 때만384×384 공통 격자로 샘플링하며, 비균일 resize·자동 crop은 하지 않는다.
- 생성 단계부터 선·손잡이·병/책 등 의미 있는 세부는 최소1–2논리px 덩어리로 요청한다. 후처리한 파일을 원본이나 무손실 복원이라고 부르지 않는다.
- 색은 원본에서 선택하고 palette/tone/highlight/line 재작성은 끈다. opaque 실내 PNG이므로 alpha=255. RGB→RGBA 변환은 채널 추가만 한다. 투명 개별 스프라이트는 아직 제작하지 않는다.

G01/G08/G09/G10/G12 적용: 공통 투영, 단일 배율, 정사각 종횡비, 반올림 오차, 출력384×384 및 알파를 관찰한다. G02–07 골격/관절 항목과 G11 UV는 2D 정지 이미지 제작에 적용되지 않는다. 이것은 생성 이미지 속 가구의 기하 일치 증명이 아니다. 생성물의 디자인 합격은 사용자에게 받는다.

## 공간 프로그램과 사물 배치

부지12×16m, 건물8×10m. 전면 보행 공간, 측면 서비스 골목, 후면 납품 여유를 배치한다. 상가 입구와 위층 주거의 계단 입구를 분리한다. 좌표·방·문·사물 치수는 `Tools/MapArt30/design.json`이 원본이다. 도면과 투영 가이드는 같은 데이터를 소비한다.

- 1층: 왼쪽 독립 계단/현관, 후방 재고실·WC·지원 복도, 전방 판매장. 계단은 부지에서 직접 들어오며 상가를 통과하지 않는다.
- 2층: 같은 계단 코어와 현관, 거실/주방, 침실, 욕실. 이 턴의 상층은 공간 설계도이며 구조/계단 물리 검증이나 아트 완성을 뜻하지 않는다.
- 1층 상품 진열장·낮은 진열섬·냉장고·계산대·의자·재고 선반·변기/세면대의 수와 위치를 먼저 지정한다. 출입구/중앙 이동 구역에 장식 소품을 넣지 않는다.
- 아트는 원작 이미지를 재사용하지 않고 새 생활잡화점으로 생성한다. 차분한 청록/목재/벽돌색, 선택적인 어두운 경계와 넓은 색 덩어리를 사용하고 손잡이·책·용기처럼 역할을 읽게 하는 디테일을 요청한다.

## 실행·피드백

기존 WorkLoop의 `prepare(command) → generate(ai.work) → normalize(command) → validate(command) → user_review(ai.work)`로 실행한다. 계산/이미지 생성/격자 변환의 책임을 나눈다. 생성 도구 실패, 종횡비 불일치, 정규화 실패는 자동으로 성공 처리하지 않는다.

최종 기술 관측은 원본 해시 보존·실제 크기·정규화 설정/엔진 해시·공통 격자·파일 유효성을 한 번 모아 확인한다. 방향/비례가 완벽하다는 픽셀 통계 점수를 만들지 않는다. 생성 이미지를 반복적으로 자기 평가/재생성하지 않는다. 결과와 설계 차이는 기록하고 사용자가 유지/수정할 부분을 답할 때까지 review에서 대기한다.

실행 결과·원본·정규화본·미리보기는 `LocalOnly/MapArt30/run01/`에 보존하며 결과 기록은 고정 설계 입력과 별도 파일에 둔다.
