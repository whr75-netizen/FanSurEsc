# Argon 2.3 — `fab22d91` (`PIXEL_ALBEDO_20261030.md` §111~§112)의 2대 질문에 대한 최종 설계 확정 및 런타임 연결 지시서

- **작성일:** 2026-11-02 09:40 KST
- **검토 대상 커밋:** `fab22d91` (`docs/ai/PIXEL_ALBEDO_20261030.md` §111~§112, `experiments/pixel-pipeline/2026-11-02-eye-carrier111`, `2026-11-02-eye-support112`)
- **검토 파일:** `AUDIT112.json`, `AFFILIATION_CACHE112.json`, `SUPPORT_OWNERSHIP112.png`, `WHITE_CARRIER111.png`, `support112.py`, `audit112.py`

---

## 0. 핵심 진단: 왜 `F105 · 눈2 · canonical (x3, y5)`에서 흰자가 `2/16`로 다시 잘렸는가? (`[원인 규명]`)

`SUPPORT_OWNERSHIP112.png`와 `AUDIT112.json`의 `blockingTriangles` 9개(`globalTriangle 17440, 17441, 17444, 17468, 17473, 17474` 등)를 보면 원인이 완벽히 드러난다.

1. **1차(Source 단계)에서 이미 반영된 눈꺼풀 경계를 2차(Destination 단계)에서 ‘두 번 절단(Double-Clipping)’하고 있다:**
   - `F105`(`Close 75%`)의 셀 `(x3, y5)`는 청록색 24정점 눈구멍 경계(`ring[2]`)의 왼쪽 아래 모서리에 걸쳐 있는 픽셀이다.
   - 즉, 원래 3D 기하에서 이 $1\times 1$ 픽셀 면적의 일부(`sourceWhiteMass = 0.34375`, 목적지 투영 시 `2/16`)만 눈구멍 안쪽(흰자)이고, **나머지 `14/16` 면적은 바로 옆 눈꺼풀 테두리 피부(주황색 9개 삼각형)**다.
   - 그런데 공동 배정기(`allocate111`)가 “흰자 성분이 소실되지 않도록 이 `0.34375`짜리 분수 면적을 **$1\times 1$ 온전한 흰자 픽셀 1개(`(x3, y5)`)로 양자화(확장 배정)**한다”고 결정했다.
   - **결정적 모순:** 분수 면적(`2/16`~`5.5/16`)을 $1\times 1$ 온전한 픽셀(`16/16`)로 양자화한다는 것 자체가 **“그 셀 내부의 나머지 `14/16` 눈꺼풀 테두리 피부를 흰자 도트가 덮어쓴다(피부 경계가 그 셀 바깥으로 0.6px 물러난다)”**는 뜻이다!
   - 그런데 `111`/`112`의 `expose`는 그렇게 양자화된 `(x3, y5)` 픽셀에 다시 $4\times 4$ 광선을 쏘아 **방금 덮어쓰기로 결정한 그 눈꺼풀 테두리 삼각형 9개(`17440~17474`)에 또 가려진다며 `14/16`를 다시 잘라버렸다.** 이는 양자화(Quantization)를 해놓고 원본 연속 경계로 양자화를 취소해 버리는 **이중 절단(Double-Clipping) 오류**다.

---

## 1. Codex의 질문 1·2에 대한 Argon의 최종 수학적·구조적 해답 (`[설계 확정]`)

### [질문 1 해답] “1. 눈 모양을 보정(양자화)할 때 주변 피부를 어디까지 함께 움직일 것인가?”
> *(§112 원문: 2.2에서 공동으로 양자화한 눈 전체 support의 닫힌 경계/주변 피부를 어떤 source-local 표면 또는 cage에 붙일 것인가?)*

#### ★ 확정 규칙: 3D 피부 메쉬 정점을 변형(Cage Warp)하지 마라! `Layer 0`(무결점 피부+소켓 캔버스)와 `Layer 1`(양자화된 눈 셀 집합 $\Omega_{\text{eye}}$) 사이의 ‘이산 셀 소유권 이전(Discrete Cell Ownership Hand-off)’으로 처리한다.

1. **왜 3D 피부 메쉬를 물리적으로 늘리거나 줄일 필요가 없는가?**
   - 이미 `LayerZero101` (`Layer 0`)과 `NativeCarrier111`을 통해, 눈구멍 내부와 주변 얼굴 전체에는 **빈틈없는 순수 얼굴 피부 캔버스(`Layer 0`)**가 깔려 있다.
   - 픽셀아트에서 눈 모양이 보정(양자화)될 때 주변 피부가 함께 움직인다는 것은 3D 폴리곤을 왜곡하는 것이 아니라, **`480×272` 격자에서 어느 셀을 눈(`Layer 1`)이 소유하고 어느 셀을 바탕 피부(`Layer 0`)로 남길지 결정하는 이산 경계 이동**이다:
     - **눈이 확장된 경계 셀 ($\mathbf{p} \in \Omega_{\text{eye}}(e)$, 예: `F105`의 `(x3, y5)`):**
       공동 배정기가 셀 $\mathbf{p}$를 눈 파츠(`UpperLine`, `Iris`, `Sclera`)로 배정하면, 그 $1\times 1$ 셀 전체의 소유권은 **눈 파츠가 100% 가져간다** (셀 내부의 눈꺼풀 테두리 피부는 셀 바깥 인접 픽셀로 물러난 것으로 취급하여 `Layer 0` 피부를 덮어쓴다).
     - **눈이 축소/이동해 비워진 셀 ($\mathbf{p} \notin \Omega_{\text{eye}}(e)$):**
       공동 배정기가 눈 파츠로 배정하지 않은 셀은 `Layer 1`이 아무것도 쓰지 않으므로, 밑에 깔린 **`Layer 0`(현재 프레임의 변형된 얼굴 피부 + 소켓 프록시 피부)가 즉시 그 자리를 100% 피부색으로 메꾼다.**
2. **목적지 깊이 및 기하 운반(`Carrier Surface`) 계약:**
   - 공동 배정된 눈 셀 $\mathbf{p} \in \Omega_{\text{eye}}(e)$의 목적지 3D 깊이 $z_{\text{eye}}(\mathbf{p})$는 `109`처럼 옛날 source 위치를 그대로 복사하지 않고, `111`에서 이미 구현·검증한 **`NativeCarrier111.shader`(`_CarrierGeometryOnly111 = 1`, 안구/안검 기하 표면)의 해당 셀 가시 carrier 깊이** (만약 셀 중심이 carrier 밖이면 셀 내부 carrier 조각 또는 24정점 `ring[e]` 평면 투영 깊이)를 사용한다.

---

### [질문 2 해답] “2. 보정한 눈을 원래 눈꺼풀이 다시 잘라내지 않으면서, 측면 얼굴과 머리카락의 실제 가림은 어떻게 유지할 것인가?”
> *(§112 원문: 현재 native depth/alpha를 새 footprint에 어떻게 운반하여 자기 안검을 두 번 절단하지 않고 측면 얼굴/머리의 실제 가림을 보존할 것인가? 최소 재현은 F105의 9삼각형이다.)*

#### ★ 확정 규칙: 얼굴 피부(`submesh 3`) 삼각형을 **‘자기 눈꺼풀 소켓 테두리 $\mathcal{L}_{\text{own}}(e)$ (2차 절단 면제)’**와 **‘외부 얼굴 가림막 $\mathcal{O}_{\text{extFace}}(e)$ (콧대·측면 볼 — 2차 가림 유지)’**로 정확히 이분할하는 아래 판별식을 적용하라.

`AUDIT112.json`의 데이터로 이미 100% 구분 가능한 **결정론적 분류 수식**은 다음과 같다.

#### 1) 자기 눈꺼풀 소켓 테두리 $\mathcal{L}_{\text{own}}(e)$ 판별식 (Internal Eyelid Rim — 2차 가림 면제)
얼굴 피부(`renderer == 1, submesh == 3`)의 삼각형 $t$와 서브샘플 교차점 $(\mathbf{p}, z_t)$가 다음 **3가지 조건을 모두 만족**하면, 이는 눈 $e$ 자신의 눈꺼풀 테두리($t \in \mathcal{L}_{\text{own}}(e)$)다:

1. **단안 깜빡임 소속 (Unilateral Blink Affiliation):**
   - 삼각형 $t$의 세 정점 중 해당 눈 $e$의 단안 깜빡임(`blinkLeft` 또는 `blinkRight`) 변형량이 0이 아닌 정점이 1개 이상이고, **반대쪽 눈 $e'$의 단안 깜빡임 변형량은 0**이다:
     $$\text{any}\big(\text{blink}_e(v_t) > 0\big) \;\land\; \text{all}\big(\text{blink}_{e'}(v_t) == 0\big)$$
   - *(검증: `AUDIT112.json`의 `F105` 가림 삼각형 9개(`17440~17474`)는 **9개 전부 `unilateralBlink["2"] == [1,1,1]`, `"1" == [0,0,0]`**으로 이 조건을 100% 통과하며, 미간 공유 정점 43개나 깜빡임이 없는 일반 볼/콧대 삼각형 `15820`(`[0,0,0]`)은 즉시 배제된다!)*
2. **소켓 링 위상 연결성 (Topological Socket Collar, 눈썹 배제):**
   - 단안 깜빡임은 눈썹(50정점)도 움직이므로 눈썹과 눈꺼풀을 구분해야 한다.
   - `support112.py`의 `connected(self.tri, ...)`로 구한 단안 이동 삼각형 연결 성분(Edge-connected component) 중 **해당 눈의 24정점 개구부 `ring[e]`와 정점/에지를 공유(`ringContacts[e] > 0`)하는 주 연결 성분(Main Eyelid Component)**에 속한 삼각형만 $\mathcal{L}_{\text{own}}(e)$로 인정한다!
   - *(검증: `support112.py` L75의 `combinedBlinkAllMovingSkinEdgeComponents`에서 눈썹 성분은 `ringContacts == 0`으로 분리되어 있고, `F105`의 9개 삼각형은 모두 `ring[2]`에 연결된 눈꺼풀 성분이므로 눈썹과 100% 분리된다!)*
3. **소켓 연속 깊이 조건 (Contiguous Socket Depth — 측면 폴딩 구분):**
   - 목적지 셀에서 눈 carrier 깊이 $z_{\text{carrier}}$와 피부 교차 깊이 $z_t$의 차이가 소켓 테두리 두께 상한 $\tau_{\text{socket}} = 0.012\text{m}$ ($12\text{mm}$) 이내이다:
     $$z_{\text{carrier}} - z_t \le 0.012\text{m}$$
   - *(검증: `AUDIT112.json`에서 `F105` 9개 삼각형의 $z_{\text{carrier}} - z_t = 13.7338 - 13.7273 = 0.0065\text{m}$ ($6.5\text{mm} \le 12\text{mm}$)이므로 9개 모두 통과한다! 반면 측면 회전 시 콧대나 앞쪽 볼이 뒤쪽 눈 앞을 가릴 때는 깊이 차가 수 센티미터($> 15\sim 30\text{mm}$)로 벌어지거나 조건 1·2에서 탈락한다.)*

$$\boxed{ t \in \mathcal{L}_{\text{own}}(e) \iff \Big(\text{UnilateralBlink}_e(t)\Big) \;\land\; \Big(t \in \text{RingConnectedComponent}_e\Big) \;\land\; \Big(z_{\text{carrier}} - z_t \le 0.012\text{m}\Big) }$$

#### 2) 목적지 가림(Exposure) 판정에서의 3단계 적용 규칙
위 $\mathcal{L}_{\text{own}}(e)$ 정의를 쓰면 자기 눈꺼풀 이중 절단과 외부 가림(측면 얼굴·머리카락)이 충돌 없이 완벽히 분리된다:

1. **자기 눈꺼풀 테두리($t \in \mathcal{L}_{\text{own}}(e)$)에 의한 2차 절단 면제:**
   - 공동 배정기(`allocate111` / `Argon 2.2`)가 이미 1차 `sourceMass`(눈꺼풀 가림이 반영된 가시 질량)를 바탕으로 셀 $\mathbf{p}$를 눈 $e$의 파츠(`UpperLine`, `Iris`, `Sclera`)로 배정했다면, 목적지 노출 검사(`expose`)에서 **$t \in \mathcal{L}_{\text{own}}(e)$인 삼각형 교차는 가림막으로 세지 않는다(통과시킨다)!**
   - 결과: `F105 · 눈2 · (x3, y5)`의 가림 삼각형 9개는 전원 $t \in \mathcal{L}_{\text{own}}(2)$이므로, **머리 OFF 상태(`F125`)에서 `(x3, y5)`의 물리 가시량은 `2/16 → 16/16`이 되어 흰자 1픽셀이 온전히 살아난다!**
2. **측면 얼굴·콧대($t \notin \mathcal{L}_{\text{own}}(e)$)에 의한 실제 외부 얼굴 가림 유지:**
   - 만약 얼굴 피부 삼각형 $t$가 $t \notin \mathcal{L}_{\text{own}}(e)$이면서 $z_t < z_{\text{carrier}}$이면(예: 측면 회전 시 콧대·볼·반대쪽 눈두덩이가 가리는 경우), 이는 **실제 외부 얼굴 가림막**이므로 해당 서브샘플을 가린다.
   - 셀 $\mathbf{p}$의 16개 서브샘플 중 외부 얼굴 가림막($t \notin \mathcal{L}_{\text{own}}(e)$)에 가려지지 않은 표본이 $8/16$ ($50\%$) 미만이면 그 셀은 측면 얼굴에 가려진 것으로 보고 `Layer 0` 피부를 유지한다.
3. **머리카락(`Layer 2`, `S4`)에 의한 실제 외부 머리 가림 유지 (`WHITE_CARRIER111.png`의 `F122` 처리):**
   - 외부 얼굴 가림을 통과한 눈 셀 $\mathbf{p}$에 대해, 마지막으로 앞머리(`S4`) 표본 중 $z_{\text{hair}} < z_{\text{carrier}}$인 가시 머리카락 커버리지를 센다.
   - 가시 머리카락 표본이 $8/16$ ($50\%$) 이상이면 `Layer 2` 머리카락 픽셀이 덮어쓰고, $8/16$ 미만이면 `Layer 1` 눈 픽셀이 최종 출력된다.
   - *(확인: `WHITE_CARRIER111.png`의 `F125 (Hair OFF)`에서는 앞머리 표본이 `0/16`이므로 `(x3, y5)` 흰자가 **온전한 1픽셀로 출력**되고, `F122 (Hair ON)`에서는 실제 앞머리가 `(x3, y5)`의 `13/16`($81.25\%$)을 덮고 있으므로 **앞머리 픽셀로 덮이는 것이 100% 정상**이다!)*

---

## 2. 즉시 수행할 런타임 연결 지시 (`[보류 해제 — 바로 구현 진행]`)

`PIXEL_ALBEDO_20261030.md` 112절에서 질문한 두 가지 미정 계약(주변 피부 소유권 이전 범위 및 내부 안검 vs 외부 얼굴/머리 가림 분리 규칙)은 위 **1절의 수식(`Layer 0/1 이산 소유권 이전` + `L_own(e) 3대 조건 면제 규칙`)**으로 완전히 확정되었다.

1. **`support112.py` / `AFFILIATION_CACHE112.json`의 정적 캐시 확정:**
   - 이미 `support112.py`가 계산해 둔 `unilateralBlinkVertexInfluence`와 `combinedBlinkAllMovingSkinEdgeComponents`(`ringContacts[e] > 0`인 주 연결 성분)를 결합하면, 각 눈 $e \in \{1, 2\}$의 내부 눈꺼풀 삼각형 비트마스크 `IsOwnEyelidRim[triangleId, eye]`를 초기화 시 1회 정적 배열로 즉시 구할 수 있다 (`runtimeReady = true`).
2. **GPU/런타임 파이프라인 즉시 연결 (`보류 해제`):**
   - 더 이상 오프라인 감사(113번 등)로 멈추지 말고, **`LayerZero101` + `NativeCarrier111` + `Argon 2.2/2.3 공동 배정 및 L_own(e) 가림 면제` + `후단 머리 이산 가림` + `유한 팔레트 P[r, q]`**를 실제 GPU 렌더 경로에 연결하여 **머리 OFF / 머리 ON / 깜빡임(Close 0~75~100) / 회전 실제 렌더 이미지(PNG & WebP)**를 생성해 제출하라.
