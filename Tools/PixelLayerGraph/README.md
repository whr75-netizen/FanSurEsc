# PixelLayerGraph — 무한 확장 계층형 레이어 트리 실행기 & GPU 패스 컴파일러

## 목적: 왜 이 도구가 필요한가?

GPT-6.2 Sol / GPT-6.2 Astra / Codex Dot처럼 추론력이 강한 AI도 **자연어 `.md` 문서만 주고 레거시 늪(`Product77 / Native395 / Integrated154`) 안에서 작업하게 두면** 다음과 같은 고질적 실패가 반복됩니다:
1. **고추론 역산 중독 (`R17~R22` 사고):** 최종 PNG의 1~2픽셀을 보고 3D VRM 정점 4,060개로 광선을 역투영하며 21개 분석 폴더를 파느라 사용량과 시간을 폭파시킴.
2. **레이어 겹 혼재 및 `1×1` 믹셀(반쪽 픽셀) 파괴:** 구 `Native395` 마스크에 얹다가 `2×2` 논리 픽셀을 `1×1` 물리 픽셀로 잘라먹음.
3. **Dot 조기 종료·스레드 유실(`completed` / `CloudThreadNotFoundError`):** 대화창 문맥이 날아가면 2,000줄 문서를 다시 읽고 딴짓을 반복함.

**`Tools/PixelLayerGraph`** 는 Higgsfield Canvas / URP RenderGraph의 핵심 원리인 **강한 타입 계층형 작업 그래프(Strong Typed Layer Tree)** 를 실제 실행 가능한 코드로 고정하여 위 3가지 실패를 **기계적으로 차단**합니다.

## 핵심 구성 파일

- [`character_layer_tree.json`](character_layer_tree.json): `1`, `2-1`, `2-2-1`, `3-2-1-1-1-1` 식으로 **20~50겹 이상 무한 확장 가능한 계층형 레이어 트리 원본** (`27`개 노드 사전 등록, `[TBD_DESIGN]` 3개 잠금).
- [`layer_graph.py`](layer_graph.py): 디스크 영구 상태 머신 실행기(`init / next / submit / invalidate`) + **27겹 논리 트리를 5개 물리 GPU 패스로 자동 평탄화하는 GPU 패스 컴파일러(`compile-gpu-plan`)**.
- [`invariants.py`](invariants.py): 외부 라이브러리 없이(Python 3.10 표준 라이브러리 전용) 실제 PNG와 소스를 직접 검사하는 **6종 수학적 불변식 게이트**:
  1. `uniform_grid_no_mixels`: 모든 픽셀이 정수 `pitch × pitch` 블록인지 검사 (`1×1` 반쪽 믹셀 즉시 기각).
  2. `parent_clip_containment`: 자식 레이어가 부모 마스크(`3-2-1` 눈 가시창 등) 안에 100% 포함되는지 검사 (개구리눈 0셀 증명).
  3. `local_eye_frontal_symmetry`: 눈 독립 로컬 격자 정면 거울 대칭 검사 (실패 시 `UPSTREAM_3D_ASYMMETRY` 반환, 2D 땜질 차단).
  4. `finite_palette_exact`: 최종 출력 RGB가 100% 유한 팔레트 LUT 내부 색인지 검사 (2중 RGB 곱셈 차단).
  5. `no_forbidden_ops`: `_History395`, `nativeReserveSupportMask`, `solve_aperture`, `OwnerLines333`, D3D11 펜스, `Fixed4x4EyeStampHardcode` 등 금지 패턴 정적 차단.
  6. `tree_integrity`: 계층 주소, 비순환성, `TBD_DESIGN` 무단 확정 차단.
- [`unity_templates/`](unity_templates/): 실행 중인 Unity 에디터를 건드리지 않도록 `Assets/` 밖에 사전 배치한 Clean-Room C# (`PixelLayerTreeSchema.cs`) 및 HLSL (`PixelLayerTreePass.hlsl`) 뼈대.
- [`test_layer_graph.py`](test_layer_graph.py): 위 모든 게이트와 상태 전이를 검증하는 자동화 단위 테스트.

## 기본 실행 명령

```powershell
# 1. 전체 계층형 레이어 트리 및 자동 상속 클리핑 체인 확인
python -B Tools/PixelLayerGraph/layer_graph.py inspect-tree

# 2. 25겹 논리 트리를 5개 물리 GPU 패스로 컴파일한 실행 계획 확인
python -B Tools/PixelLayerGraph/layer_graph.py compile-gpu-plan

# 3. 디스크 상태 원장 초기화 (Dot이 끊겨도 100% 재개 가능)
python -B Tools/PixelLayerGraph/layer_graph.py init LocalOnly/PixelLayerGraph/v4-run01/state.json

# 4. 현재 미완료 1개 노드의 초경량(< 2 KB) 원자 티켓 발급 (AI는 이 티켓만 읽음!)
python -B Tools/PixelLayerGraph/layer_graph.py next LocalOnly/PixelLayerGraph/v4-run01/state.json

# 5. 작업 결과 기계 검증 및 상태 전이 (통과 시 SHA-256 캐시 고정)
python -B Tools/PixelLayerGraph/layer_graph.py submit LocalOnly/PixelLayerGraph/v4-run01/state.json LocalOnly/PixelLayerGraph/v4-run01/submission.json

# 6. 특정 노드 수정 시 해당 노드와 자손만 무효화 (상위/형제 레이어 100% 캐시 유지)
python -B Tools/PixelLayerGraph/layer_graph.py invalidate LocalOnly/PixelLayerGraph/v4-run01/state.json 3-2-3

# 7. 엔진 자체 단위 테스트 실행
python -B -m unittest Tools/PixelLayerGraph/test_layer_graph.py
```
