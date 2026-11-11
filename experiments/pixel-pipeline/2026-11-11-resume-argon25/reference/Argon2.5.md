# Argon 2.5 — 상안검 공유 피부 해법 · 아픽셀 눈-머리 위상 동기화 · 2D 정준 눈 캐시 템플릿 및 각도별 양안 결합 명세

> **대상 커밋:** `0284e09e` (`Fix valid eyelid depth recovery and isolate shared-skin grid failures`)
> **검토 대상 문서:** `docs/ai/PIXEL_ALBEDO_20261030.md` §117 (`carrier-fix24` 및 추가 설계 검토)
> **검토 대상 데이터:**
> - `experiments/pixel-pipeline/2026-11-02-bounded-form115/runtime24/full-render24/carrier-fix24/VALIDATED_FIX24.json`
> - `experiments/pixel-pipeline/2026-11-02-bounded-form115/runtime24/full-render24/carrier-fix24/CLOSE75_SKIN_AFFILIATION24.json`
> - `experiments/pixel-pipeline/2026-11-02-bounded-form115/runtime24/full-render24/carrier-fix24/PHASE_EXPOSURE24.json`
> - `experiments/pixel-pipeline/2026-11-02-bounded-form115/runtime24/full-render24/sequence24/RESULT_FULL24.json`
> - `Assets/EUnityValidation01/Direct24Carrier/ForwardEye113_Geometry24.compute`

---

## 0. 핵심 요약: 세 가지 문제의 통합 해결 구조

`0284e09e`를 통해 실제 GPU 40프레임에서 표면 미확정(`-116`) `0`셀, 팔레트 밖 색 `0`건, GPU 리셋 `0`건, 안검 7곳 복구가 확인되었습니다. 이제 남은 시각적·구조적 결함은 다음 **3가지**이며, 본 문서는 각 방식의 **장점만 결합한 하이브리드 해법**을 정의합니다.

1. **[§1] `Close75` 상안검 공유 피부 자기 가림(`-117`):**
   - 원본 3D 위치에서는 가림막이 `0`개(`sourceFaceVisibility = [1, 1]`)인 노출 안검이 2D 격자 양자화 변위(`-1.46 px, -0.51 px`)로 인해 같은 눈의 위쪽 상안검 주름 피부(`2691..2715`) 위로 이동했을 때, 반대쪽 눈 블렌드셰이프의 미세 번짐(`unilateral["2"] != 0`) 때문에 자기 피부로 인정받지 못해 가려지는 문제.
   - **해법:** 우세 동측 안구(Dominant-Ipsilateral Eye) 기준 `_OwnSkin113` 판정 + 원본 비차폐 셀의 로컬 피부 캔버스 공수송(Co-Transport) 규칙.
2. **[§2] `0.125 px` 아픽셀 이동 시 눈 격자와 머리카락 가림 격자의 위상 단절:**
   - `_ForwardAnchor102.x`가 반정수(`211.5`)를 넘을 때 눈 정준 셀의 화면 픽셀 `p`는 `+1.0 px`(`+4` 서브픽셀) 점프하는 반면, `_HairMeta102`는 `+0.125 px`(`+0.5` 서브픽셀)만 이동하여 흰자 위 머리카락 가림이 `12/16 -> 0/16`으로 튀는 문제.
   - **해법:** 눈 정준 셀의 스냅 잔차($\boldsymbol{\delta}_{\text{snap}}$)를 보정한 머리 기준 공변 서브샘플 좌표계(`hairShift4x` / `DestinationCanonical24`).
3. **[§3] 정면·개폐 시 좌우 눈 크기/눈동자 모양이 짝짝이로 깨지는 문제 (`sequence24/RESULT_FULL24.json`):**
   - 정면 포즈(`frame 99..107`)에서 두 눈의 3D 안와 직경은 `39.791 mm`로 100% 같지만, 두 눈 사이 화면 거리가 정수가 아니어서 단일 격자(`_ForwardAnchor102.xy`) 위상 차이로 인해 **오른쪽 눈(`owner 1`)은 눈동자 4셀(`2×2`)·흰자 4셀·안검 7셀**, **왼쪽 눈(`owner 2`)은 눈동자 5셀(기형 ㄱ자)·흰자 5셀·안검 9셀**로 배정되며, `Close50`에서는 `1셀 vs 2셀`, `Close75`에서는 `0셀 vs 1셀`(왼쪽 눈만 파란 점 1개 노출)로 좌우가 짝짝이가 되는 문제.
   - **해법 (장점 결합 하이브리드 — 2D 정준 눈 캐시 아키타입 + 눈별 로컬 앵커 + 3D 각도·개폐율 양안 결합):**
     - **2D 캐시 이미지 방식의 장점 채택:** 각 눈을 단일 공유 격자에 억지로 구겨 넣지 않고 **각 눈 고유의 로컬 2D 정준 캐시 공간**에서 **깨지지 않는 직사각형 2D 눈 템플릿(Archetype Cache)** 으로 구조를 확정하여, 격자 위상 때문에 눈동자가 5칸 ㄱ자로 찌그러지거나 좌우가 달라지는 현상을 원천 차단합니다.
     - **3D 각도(Foreshortening) 반영의 장점 채택:** 좌우 눈을 무조건 똑같이 복사하는 대신, 3D 안와 정점에서 계산한 **수평 시야 단축률 $\rho_x = W_{\text{far}} / W_{\text{near}} \approx \cos\theta_{\text{far}} / \cos\theta_{\text{near}}$** 와 **수직 개폐율 $\beta$** 로 두 눈의 2D 캐시 템플릿 선택을 수학적으로 결합합니다(정면 $\rho_x \ge 0.88$에서는 좌우 100% 대칭 템플릿 강제, 측면 회전 $\rho_x < 0.88$에서는 세로 높이 $h_1 = h_2$는 동일하게 유지한 채 먼 쪽 눈의 가로 폭만 $w_{\text{far}} \le w_{\text{near}}$로 단축).
     - **카메라 정규 픽셀 & 3D 깊이 가림의 장점 유지:** 확정된 2D 눈 캐시 셀을 화면에 출력할 때는 카메라 정규 픽셀 격자(`480×272`)에 스냅하여 믹셀(Mixels)이나 열 탈락을 막고, 각 눈의 개별 스냅 잔차 $\boldsymbol{\delta}_{\text{snap}, e}$를 §2의 규칙으로 보상하여 앞머리·콧대의 3D 실시간 가림과 오차 없이 맞물리게 합니다.

---

## 1. 상안검 공유 피부 소속 판정(`_OwnSkin113`) 및 변위 공수송 규칙

### 1.1 원인 진단 (`CLOSE75_SKIN_AFFILIATION24.json` 및 `VALIDATED_FIX24.json`)

1. `Close75` (`frame 105 / 109`, `tile (9,3)`, `canonical (10,4)`, `owner 1`) 안검 셀은 **3D 원본 위치 `(222.9603, 53.0067)`에서 가시성이 `sourceFaceVisibility = [1.0, 1.0]`(가림막 0개)** 인 완전 노출 안검입니다.
2. 이 셀이 양자화된 목적지 격자 중심 `(221.5, 52.5)` (`depth = 13.71259 m`)로 배치되면서 화면 좌표가 `(-1.46 px, -0.51 px)`만큼 바로 위쪽 상안검 주름 피부 위로 이동해 9개 피부 삼각형(`2691, 3177, 2692, 2718, 2717, 2693, 2716, 2694, 2715`, `depth = 13.6934 ~ 13.7008 m`, `depthGap = 11.8 ~ 19.1 mm`)과 교차했습니다.
3. 이 9개 삼각형은 모두 `eyeOwners = [1, 1, 1]`(동측 안와 정점)이고 `unilateral["1"] = [1, 1, 1]`(`eye 1` 깜빡임 모프에 100% 이동)이며 `depthGap < SocketLimit24(1) (= 37.67 mm)`이지만, 반대쪽 눈(`eye 2`) 블렌드셰이프 감쇠 반경이 넓어 미세 가중치(`unilateral["2"] != 0`)가 섞여 있고 개구부 링에서 1~2링 위쪽(`ringContact = 0`)이라는 이유로 기존 배타 조건(`otherEye == 0`)에서 제외되었습니다.

### 1.2 확정 설계 규칙

#### 규칙 1-A: 우세 동측 안구(Dominant-Ipsilateral Eye) 기준 `_OwnSkin113` 마스크 정의
반대쪽 눈 블렌드셰이프의 미세 감쇠 번짐(`unilateral[otherEye] != 0`)이 주 소속 눈(`eye`)의 상안검 피부 소유권을 박탈하지 않도록, 얼굴 피부 삼각형 $t = (v_0, v_1, v_2)$의 `(_OwnSkin113[t] & (1u << e)) != 0` 소속 조건을 다음과 같이 정의합니다.

1. **동측(Ipsilateral) 우세성:**
   $$\text{Ipsilateral}(t, e) \iff \Big(\sum_{i=0}^{2} \mathbf{1}[\text{eyeOwner}(v_i) = e] \ge 2\Big) \;\wedge\; \Big(\sum_{i=0}^{2} \|\Delta \mathbf{p}_{\text{blink}}(v_i, e)\|_2 \ge \sum_{i=0}^{2} \|\Delta \mathbf{p}_{\text{blink}}(v_i, e')\|_2\Big)$$
2. **상안검/안와 연결 성분 포함:**
   $\text{Ipsilateral}(t, e)$를 만족하면서, (i) $\max_{i} \|\Delta \mathbf{p}_{\text{blink}}(v_i, e)\|_2 > \varepsilon_{\text{blink}}$ (능동 안검 변형 피부: `Close75`의 9개 삼각형 `2691..2715` 전부 해당) 이거나, (ii) 눈 $e$의 개구부 링 또는 능동 안검 변형 피부로부터 동측 메쉬 위상 거리 $k \le 2$ 링 이내이고 안구 중심 거리가 `SocketLimit24(e)` 이내인 인접 상안검 주름 삼각형(`frame 122 / 125`의 `2566, 2571, 2565, 2560, 2570` 포함)이면 `_OwnSkin113[t]`에 `(1u << e)` 비트를 부여합니다.

#### 규칙 1-B: 원본 비차폐(Source-Unoccluded) 셀의 로컬 피부 캔버스 공수송
- 원본 레이에서 노출이 확정된(`ColumnVisibility24` / `sourceFaceVisibility == 1`) 눈·안검 셀이 양자화된 목적지 위치로 이동했을 때 만나는 동측 안와 피부(`(_OwnSkin113[t] & (1u << owner)) != 0` 및 `zz - hitDepth <= SocketLimit24(owner)`)는 **보정된 셀이 2D 격자 위에서 대체(Displace)하는 로컬 피부 캔버스**이므로 차폐물에서 제외합니다.
- 반면 반대쪽 얼굴·콧대(`Ipsilateral(t, owner) == false`) 또는 `zz - hitDepth > SocketLimit24(owner)`인 외부 표면은 `_OwnSkin113` 비트가 `0`이므로 측면 회전 시의 실제 얼굴 가림은 100% 그대로 유지됩니다.

---

## 2. 아픽셀(`0.125 px`) 이동 시 눈 정준 격자와 머리카락 가림 격자의 위상 동기화

### 2.1 원인 진단 (`PHASE_EXPOSURE24.json` 및 `ForwardEye113_Geometry24.compute:502, 513`)

1. `phase 0 -> phase 0.125`에서 머리 원점 `_ForwardAnchor102.x`가 `211.4362 -> 211.5612` (`+0.125 px`) 이동하며 반정수 경계 `211.5`를 넘을 때, `ComposeRegion113` 502행의 `cell = floor(centre - _ForwardAnchor102.xy)`에 의해 정준 셀 `canonical (3,4)`가 스냅되는 화면 픽셀 `p.x`는 `2(214.5) -> 3(215.5)`으로 **`+1.0 px` (`+4` 머리카락 서브픽셀) 통째로 점프**합니다(`snapDelta.x: -0.4362 -> +0.4388 px`).
2. 반면 3D 머리카락 메쉬(`_HairMeta102`)는 화면에서 `+0.125 px`(`+0.5` 서브픽셀)만 이동했는데, 513행에서 점프한 화면 픽셀 `p * 4 + int2(x, y)`로 머리카락을 조회하여 `0.875 px`(`3.5` 서브픽셀)의 인공적인 상대 위상 파열(`hairCoverage16: 12/16 -> 0/16`)이 발생했습니다.

### 2.2 확정 설계 규칙: 스냅 잔차($\boldsymbol{\delta}_{\text{snap}}$)를 보정한 머리 기준 공변 서브샘플 좌표계

채택된 눈·안검 정준 셀 `cell`은 화면 픽셀 `p`의 고정 배경이 아니라 머리 기준 연속 구간 $[\mathbf{a}_e + \text{cell},\; \mathbf{a}_e + \text{cell} + 1]$의 대리자입니다(여기서 $\mathbf{a}_e$는 해당 눈의 정준 격자 원점 anchor). 따라서 눈·안검 셀(`chosenPart != 0`)의 3D 가시성(`Destination24`)과 $4\times 4$ 머리카락 가림(`_HairMeta102`, `_HairRGBA102`)은 모두 **정준 셀 자신의 머리 기준 연속 좌표(스냅 잔차 $\boldsymbol{\delta}_{\text{snap}}$ 제거)** 에서 샘플링해야 합니다:

```hlsl
// 눈 정준 셀 중심(head-anchored)과 스냅된 화면 픽셀 중심(centre) 사이의 스냅 잔차
float2 cellCentreScreen = anchorXY + float2(cell) + 0.5;
float2 snapDelta = centre - cellCentreScreen; // [-0.5, +0.5]^2
int2 hairShift4x = int2(round(-snapDelta.x * 4.0), round(snapDelta.y * 4.0));
```

- **머리카락 $4\times 4$ 조회 (`ComposeRegion113`):**
  `chosenPart != 0`인 셀에서 `int2 hairSub = clamp(p * 4 + int2(x, y) + hairShift4x, int2(0, 0), _ForwardROI102.zw * 4 - 1);` 로 `_HairMeta102`와 `_HairRGBA102`를 읽습니다.
- **수치 검증:** `PHASE_EXPOSURE24.json`의 `canonical (3,4)`에 대입하면:
  - `phase 0` (`p.x = 2`, `snapDelta.x = -0.4362`): `hairShift4x.x = round(+1.7448) = +2` $\implies$ `hairSub.x = 8 + {0,1,2,3} + 2 = {10, 11, 12, 13}`.
  - `phase 0.125` (`p.x = 3`, `snapDelta.x = +0.4388`): `hairShift4x.x = round(-1.7552) = -2` $\implies$ `hairSub.x = 12 + {0,1,2,3} - 2 = {10, 11, 12, 13}`!
  - 즉, 화면 픽셀 `p.x`가 `1 px` 스냅 점프하는 순간에도 머리카락 서브픽셀 조회 위치는 `{10, 11, 12, 13}`으로 **단 1서브픽셀의 튐도 없이 연속 유지**되며, 실제 머리카락이 흔들리거나 고개가 돌 때는 `_HairMeta102` 자체가 이동하므로 실제 3D 머리카락 가림은 그대로 반영됩니다.

---

## 3. 좌우 눈 비대칭(짝짝이) 해결: 2D 정준 눈 캐시 템플릿(Archetype Cache) + 눈별 로컬 위상 + 3D 각도·개폐율 양안 결합

### 3.1 원인 진단 (`sequence24/RESULT_FULL24.json` 실측 분석)

`sequence24/RESULT_FULL24.json`에서 정면 포즈(`frame 99 ~ 107`)의 양안 원형 배정(`canonicalPartCounts`)을 대조하면, 앞머리 가림이 들어가기 **전**부터 이미 좌우 눈이 서로 다른 크기와 모양으로 배정되고 있습니다:

| 정면 프레임 | 오른쪽 눈 (`owner 1`) | 왼쪽 눈 (`owner 2`) | 원인 |
| :--- | :--- | :--- | :--- |
| **`Close 0` (F99, 열림)** | 홍채 **4** (`2×2`) / 흰자 **4** / 안검 **7** | 홍채 **5** (5칸 기형) / 흰자 **5** / 안검 **9** | 두 눈 사이 화면 거리가 비정수여서 `owner 2`만 격자 경계에 걸쳐 면적 합이 `4->5`, 안검 폭이 `7->9`로 부풀려짐 |
| **`Close 25` (F101)** | 홍채 **3** / 흰자 **3** / 안검 **7** | 홍채 **5** / 흰자 **3** / 안검 **9** | 양안 독립 최적화로 왼쪽 홍채만 5셀 유지 |
| **`Close 50` (F103)** | 홍채 **1** / 흰자 **2** / 안검 **7** | 홍채 **2** / 흰자 **2** / 안검 **9** | 정면 반감김인데 홍채 가로폭이 `1 vs 2`로 비대칭 |
| **`Close 75` (F105)** | 홍채 **0** / 흰자 **1** / 안검 **7** | 홍채 **1** / 흰자 **1** / 안검 **9** | 오른쪽은 감겼는데 왼쪽만 파란 홍채 1셀이 남음 |

이 문제는 **① 두 눈이 하나의 고정 격자 원점(`_ForwardAnchor102.xy`)을 공유해 서브픽셀 위상이 서로 다른 점**, **② 2D 눈동자 모양에 직사각형 캐시 템플릿 제약이 없어 5칸짜리 ㄱ자 모양 등이 허용되는 점**, **③ `Enumerate113`이 좌우 눈을 3D 각도·개폐율 결합 없이 완전히 따로 푸는 점** 때문에 발생합니다.

### 3.2 장점 결합 하이브리드 설계 (3대 불변조건)

#### 규칙 3-A: 눈별 독립 로컬 2D 정준 격자 원점 (`Per-Eye Local Canonical Anchor`)
두 눈 사이 화면 거리가 비정수(예: `7.45 px`)일 때 단일 격자 원점 `_ForwardAnchor102.xy`를 공유하면 두 눈의 서브픽셀 위상이 필연적으로 달라져 한쪽 눈만 격자선에 걸치게 됩니다.
- 이를 막기 위해 각 눈 $e \in \{0, 1\}$ (`owner 1`, `owner 2`)의 3D 안와 개구부 링 중심(또는 내안각-외안각 중점)을 화면에 투영한 $\mathbf{c}_e = (\mu_{x,e}, \mu_{y,e})$를 기준으로 **각 눈마다 동일한 위상 정렬을 갖는 로컬 2D 정준 좌표계**를 부여합니다:
  - 카메라 Roll이 없는 수평 자세에서는 두 눈의 수직 원점 위상을 $\bar{\mu}_y = \frac{1}{2}(\mu_{y,0} + \mu_{y,1})$로 동기화하고,
  - 수평 원점 $\mu_{x,e}$는 각 눈의 중심이 로컬 정준 셀 경계(짝수 폭 `2×2` 눈동자의 중앙 경계)에 똑같은 위상으로 정렬되도록 설정합니다.
  - 화면 픽셀 `p`에 최종 합성할 때는 각 눈 영역(`owner == e`)마다 자신의 $\mathbf{a}_e$와 스냅 잔차 $\boldsymbol{\delta}_{\text{snap}, e}$(§2의 `hairShift4x`)를 적용합니다. 이렇게 하면 **2D 캐시 이미지처럼 두 눈이 격자 위상 차이로 인해 서로 다른 셀 면적(`7열 vs 9열`, `4셀 vs 5셀`)으로 쪼개지는 현상이 원천적으로 사라집니다.**

#### 규칙 3-B: 2D 정준 눈 캐시 템플릿 가족 (Compact Rectangular Eye Archetype Cache)
저해상도 픽셀 캐릭터에서 눈동자(홍채, `part 1`)와 흰자(`part 4`)는 임의의 찌그러진 다각형(5칸짜리 ㄱ자·ㅗ자 폴리오미노 등)이 될 수 없으며, **사전에 구조가 검증된 2D 정준 템플릿(Archetype Cache) 가족** 안에서만 선택되어야 합니다.

1. **홍채(눈동자, `part 1`) 직사각형 충만도(Rectangular Compactness) 불변조건:**
   `BuildSubsets113`에서 홍채 후보 부분집합 $S_{\text{iris}} \neq \emptyset$가 유효(`valid = true`)하려면, $S_{\text{iris}}$의 바운딩 박스 폭 $w_{\text{iris}} = x_{\max} - x_{\min} + 1$과 높이 $h_{\text{iris}} = y_{\max} - y_{\min} + 1$에 대해 반드시 **빈틈없는 직사각형(2D Box Template)** 이어야 합니다:
   $$|S_{\text{iris}}| = w_{\text{iris}} \times h_{\text{iris}}, \qquad w_{\text{iris}} \in \{1, 2\}, \quad h_{\text{iris}} \in \{1, 2\}$$
   - 즉, 허용되는 비영(non-empty) 눈동자 2D 캐시 모양은 **`2×2`(4셀, 정면 열림), `1×2`(2셀, 측면 단축 열림), `2×1`(2셀, 반감김), `1×1`(1셀, 측면 반감김)** 의 4가지 직사각형 템플릿뿐이며, **5셀짜리 비대칭 덩어리나 3셀짜리 ㄱ자 모양은 후보 생성 단계(`BuildSubsets113`)에서 즉시 기각(`valid = false`)** 됩니다.
2. **상안검 접합 및 흰자 대칭성:**
   - $S_{\text{iris}} \neq \emptyset$일 때 홍채의 최상단 행 $y_{\max}$는 반드시 해당 열의 상안검(`row`) 바로 아래 행(`row - 1`)에 접해야 하며, 흰자(`part 4`) 부분집합 $S_{\text{white}}$ 역시 홍채와 같은 행 구간 $[y_{\min}, y_{\max}]$ 안에서 홍채 좌우에 배치되는 정규 템플릿 구조를 따릅니다.

#### 규칙 3-C: 3D 시야각(Foreshortening $\rho_x$) 및 개폐율($\beta$) 기반 양안 공동 결정 (Bilateral Joint Coupling)
좌우 눈을 무조건 똑같이 찍어내면 고개를 돌렸을 때 어색해지고, 완전히 따로 풀면 정면/깜빡임에서 짝짝이가 됩니다. 따라서 3D 안와 링(24개 정점)에서 측정한 **두 눈의 기하학적 비율**로 양안의 템플릿 치수 $(w_{\text{iris}, e}, h_{\text{iris}, e}, w_{\text{white}, e})$를 결합합니다.

1. **3D 안와 기하 비율 정의:**
   각 눈 $e \in \{0, 1\}$의 24-정점 안와 개구부 링의 화면 투영 가로 폭을 $W_e$, 세로 개폐 높이를 $H_e$, 정지 열림 상태 기준 개폐율을 $\beta_e = H_e / H_{e,\text{open}} \in [0, 1]$이라 할 때:
   - **양안 수평 시야 단축비 (Horizontal Foreshortening Ratio):**
     $$\rho_x = \frac{\min(W_0, W_1)}{\max(W_0, W_1)} \in (0, 1]$$
     (정면에서는 $\rho_x \approx 1.0$, 고개를 좌우로 돌리면 먼 쪽 눈의 $W_{\text{far}}$가 $\cos\theta$에 비례해 줄어들며 $\rho_x < 1$이 됨)
   - **양안 수직 개폐 일치도:**
     $$\Delta \beta = |\beta_0 - \beta_1|$$

2. **수직(세로) 개폐 동기화 불변조건 (모든 Yaw 회전 각도에서 성립):**
   양안이 함께 깜빡이는 대칭 표정($\Delta \beta < 0.08$)에서는 고개가 좌우 어느 각도로 돌아가 있든 **두 눈의 눈동자 세로 픽셀 높이와 노출 단계는 반드시 동일**해야 합니다:
   $$h_{\text{iris}, 0} = h_{\text{iris}, 1} = h^*(\bar{\beta}), \qquad \bar{\beta} = \frac{\beta_0 + \beta_1}{2}$$
   - 특히 거의 감긴 상태($\bar{\beta} \le 0.30$, 예: `Close75` 및 `Close100`)에서 한쪽 눈의 지지량이 임계치 미만이면 양안 모두 $h_{\text{iris}, 0} = h_{\text{iris}, 1} = 0$으로 동기화하여, `Close75`(`frame 105`)에서 왼쪽 눈에만 파란 점 1개가 남는 비대칭을 완벽히 제거합니다.

3. **수평(가로) 각도 비례 결합 규칙 (정면 대칭 + 측면 단축):**
   - **정면 및 준정면 구간 ($\rho_x \ge 0.88$):**
     두 눈의 3D 시야각 차이가 없으므로, 양안의 연속 면적 지지를 대칭 평균 $\bar{m} = \frac{1}{2}(m_0 + m_1)$으로 결합하고 **양안이 완전히 동일한 2D 템플릿 치수**를 선택하도록 강제합니다:
     $$w_{\text{iris}, 0} = w_{\text{iris}, 1}, \qquad h_{\text{iris}, 0} = h_{\text{iris}, 1}, \qquad |S_{\text{white}, 0}| = |S_{\text{white}, 1}|, \qquad w_{\text{lid}, 0} = w_{\text{lid}, 1}$$
     - **실측 대입 결과:**
       - `Close 0` (`frame 99`): 양안 모두 **홍채 `2×2`(4셀) + 흰자 4셀 + 안검 7셀**로 100% 대칭 통일 (`owner 2`의 5셀 기형 홍채 및 9셀 과잉 안검 제거).
       - `Close 25` (`frame 101`): 양안 모두 **홍채 `2×2`(4셀) + 흰자 4셀(또는 3셀)** 로 통일.
       - `Close 50` (`frame 103`): 양안 모두 **홍채 `2×1`(2셀) + 흰자 2셀 + 안검 7셀**로 100% 대칭 통일.
       - `Close 75` (`frame 105`): 양안 모두 **홍채 `0`셀**로 통일 + §1에 의해 상안검 차단 해제.
   - **측면 회전 구간 ($\rho_x < 0.88$, 예: `frame 134 ~ 136` 회전):**
     가까운 쪽 눈($e_{\text{near}}$, $W_{\text{near}} > W_{\text{far}}$)과 먼 쪽 눈($e_{\text{far}}$)에 대해 세로 높이는 $h_{\text{iris, far}} = h_{\text{iris, near}}$로 동일하게 유지하되, 먼 쪽 눈의 가로 폭만 $\rho_x$ 비율에 따라 단조 감소시킵니다:
     $$w_{\text{iris, far}} = \max\!\big(1,\; \text{round}(\rho_x \cdot w_{\text{iris, near}})\big) \le w_{\text{iris, near}}, \qquad |S_{\text{white, far}}| \le |S_{\text{white, near}}|$$
     - 이를 통해 정면에서는 좌우가 한 픽셀의 오차도 없이 대칭이고, 고개를 돌릴 때는 픽셀 구조가 뭉개지지 않은 채 먼 쪽 눈만 `2×2 -> 1×2` 직사각형 템플릿으로 깔끔하게 원근 단축됩니다.

---

## 4. 구현 반영 요약 체크리스트

1. **[§1] 상안검 공유 피부(`_OwnSkin113`) 및 공수송:**
   - `_OwnSkin113` 생성 시 반대쪽 눈 블렌드셰이프 미세 가중치(`unilateral[otherEye] != 0`)가 있더라도 `Ipsilateral(t, e)`(정점 소속 다수결 및 깜빡임 변위량 우세)와 `SocketLimit24(e)` 이내 상안검 주름 연결 조건을 만족하면 해당 눈의 피부 마스크에 포함합니다.
   - 원본 레이에서 노출된(`sourceFaceVisibility == 1`) 셀이 목적지에서 동측 `_OwnSkin113` 피부와 만날 때 자기 가림(`-117`)으로 차단하지 않습니다.
2. **[§2] 아픽셀(`0.125 px`) 눈-머리카락 위상 동기화:**
   - 채택된 눈·안검 정준 셀 `cell`에 대해 스냅 잔차 $\boldsymbol{\delta}_{\text{snap}} = \text{centre} - (\text{anchorXY} + \text{cell} + 0.5)$를 보정한 `hairShift4x = int2(round(-snapDelta.x * 4.0), round(snapDelta.y * 4.0))`로 `_HairMeta102` / `_HairRGBA102`를 샘플링합니다.
3. **[§3] 2D 정준 눈 캐시 템플릿 + 눈별 로컬 앵커 + 3D 각도·개폐율 양안 결합:**
   - `BuildSubsets113`에서 홍채(`part 1`) 부분집합을 직사각형 2D 캐시 템플릿($|S_{\text{iris}}| = w_{\text{iris}} \times h_{\text{iris}}$, $w, h \in \{1, 2\}$)으로 제한하여 5셀 ㄱ자 등 비대칭 기형을 차단합니다.
   - 각 눈의 로컬 정준 위상을 각 눈의 3D 안와 중심에 정렬하고, 3D 안와 폭 비율 $\rho_x = \min(W_0, W_1)/\max(W_0, W_1)$ 및 개폐율 $\beta$에 따라 양안 세로 높이를 동기화($h_0 = h_1$)하며, 정면($\rho_x \ge 0.88$)에서는 좌우 대칭 템플릿($w_0 = w_1$)을, 회전($\rho_x < 0.88$)에서는 먼 쪽 눈 단축 템플릿($w_{\text{far}} \le w_{\text{near}}$)을 공동 선택합니다.
