# 62 — 재질 내부 원본 색 영역, 오프라인 후보 / 미채택

**구현한 범위:** 재질당 대표색 하나를 공급하던 60의 가정을 제거했다. 원본 VRM의 PNG·UV에서 색 범위를 구분하고 UV 연결 영역 ID를 만든 다음, 영역이 참조하는 원본 texel 기준색으로 유한 팔레트를 만들고 저장된 Q로 직접 조회한다. 제품·Unity·31·34는 변경하지 않았다. 이 후보는 원본 무늬를 되돌렸지만 깨끗한 픽셀 형태를 달성하지 못해 **미채택**이다.

보기: [전체 비교](FULL_COMPARE62.png), [머리 단계 비교](COMPARE62.png), [이전 반례](LEGACY_COMPARE62.png), [수치](RESULT62.json), [회귀 검사](REGRESSION62.json). `INDEX.html`은 서버 없이 로컬 파일로 열린다.

## 실제 입력과 출처

- 현재 고정 입력: 60 frame94, `renderer60-20261031T092325108Z`, source-known 373셀 / native 1492픽셀. 저장된 `CELL_AUDIT60.json`의 **paletteIndex**와 g, primitive/UV, owner/depth를 그대로 사용한다. preparedUV.z의 tag를 Q로 사용하지 않는다.
- 모델 SHA256 `0e2fd0fc90308da3172ecf4e674fdeb4f054ebd617005caa5b997a2ca339cce3`. 원본 VRM `Assets/EUnityValidation01/VRoidSampleA144/Inputs/AvatarSample_A.vrm`의 embedded PNG를 직접 읽고 59 registry의 imageSHA를 검증한다. 재질11–14 / image15·18·20·22는 이 모델의 실제 binding이며 알고리즘의 색 상수나 역할 분기 조건이 아니다.
- `materialId`: 원본 재질 binding. `sourceRegionId`: 해당 texture의 색 범위·UV 연결 영역. `sourceStructureId`: 원본 triangle 연결성. `sourceRegionInstanceId`: 색 영역과 구조의 조합. `occlusionOwnerBufferUnchanged`: 저장된 렌더 owner. 서로 동일한 ID로 취급하지 않는다. mesh 연결 조각을 미술적 머리 묶음이라고 부르지 않는다.
- 과거 회귀는 별도 sourceId `95d042f14adf8e99685f26838beeb00ab57773e445e5997d16a9c61d0f1e2c3f`, 368셀 중 source-known **358셀**이다. 10셀은 원본 정보가 없으므로 기존 PNG 그대로 유지하고 지표 주집계에서 제외했다. 현재 373셀과 동일 프레임으로 섞지 않는다. 동결 입력과 원본 파일 hash는 `LEGACY_INPUT62.json`에 있다.

## 연산과 제한

1. `region62.py:build_regions`: 원본 sRGB8 → linear RGB → OKLab. 기존 원본 팔레트에서 측정한 ΔL `0.043678819190537344`를 **진단용 색 범위 폭**으로 재사용한다. 각 L/a/b 범위 안에서 4연결 UV 영역을 만든다. 범위 수는 실제 원본 범위에서 유도되며 임의 K-means나 texel별 RGB family가 아니다. 이 폭이 올바른 미술 영역을 자동 보장하지 않는다.
2. 실제 원본 색 대비 표지가 같은 범위로 합쳐지면 표지의 가장 큰 Lab 차이 축 중간값으로 원본 영역만 분리한다. material12에 이런 충돌 3건이 있었다. 작은 영역을 면적 기준으로 삭제하지 않는다. 원본 대비 7쌍과 equal-Q 평가 1쌍만 명시적으로 보호하며, 근거 약한 1쌍은 강제 복원하지 않는다.
3. 영역 medoid는 원본 texel 색 중에서 고른다. 평균색은 거리 계산에만 쓰고 출력하지 않는다. 같은 원본 색 범위의 분리된 영역은 팔레트 참조를 공유할 수 있지만 영역·구조·가림 ID는 합치지 않는다. 대비 표지가 있는 영역은 원래 표지 texel 색을 유지한다. 모든 영역에 개별 medoid를 주는 ablation도 저장했으며 이것은 단독 색을 더 만들었다.
4. `palette`: anchor를 밝은 끝에 정확 보존하고, 기존 두 Q에 대응하는 OKLab L 간격을 계산한다. hue/chroma를 유지하되 sRGB 밖이면 L/h를 유지하며 chroma만 줄인다. 최종 RGB8로 반올림한다. 최종색은 `P[region,Q]` 직접 조회이며 **RGB×g, G, 전체 중앙값 맞춤 배율은 없다.** 간격 배율은 P의 간격에만 적용한다. Q 변경은 영역과 P를 변경하지 않는다.
5. 원래 `.55` 선형 외곽선 처리는 기존 52셀에 그대로 적용한다. 팔레트 직접 출력 단계와 이 후단을 분리했다. 영역·머리 alpha·실루엣·owner/depth·다른 파츠를 바꾸지 않는다. 이 실험은 **색 영역 공급**이며 화면 경계를 이동하는 곡선 보정은 새로 수행하지 않았다.

보존할 실제 색차의 근거는 원본 대비 표지·source UV 연결·별도 구조/가림 관계다. 그 외 단순 원본 RGB 차이를 전부 의미 특징으로 승인하지 않는다. 조명 g는 source 영역 생성에 들어가지 않으므로 실제 광원 명암과 baked texture 변화가 섞이지 않는다. `audit_source62.py`는 RGB8 ±0.5 encoding 구간을 이용해 원본 3-texel 명도 프로필의 affine 적합 가능성을 측정한다. 373개 모두 두 축을 측정했고 365개가 두 축에서 단순 기울기와 양립했다. 이는 국소 상수·완만한 변화도 포함하므로 **365개가 잡음/제거 대상이라는 뜻이 아니다.** 원래 그려진 긴 띠, 비선형 texture gradient와 형태 특징을 자동 구별하는 규칙은 아직 완성되지 않았다. 불확실 영역을 실제 의미 특징으로 이름 붙이지 않았고 baked gradient를 임의 제거하지 않았다.

## 같은 373셀 결과

RGB 연결 영역/단독 셀은 머리 가시 셀 마스크에서 **4연결·RGB8 완전 동일** 기준이다. 구조 영역 수나 미술적 특징 수와 다르다.

| 단계 | RGB8 수 | RGB 연결 영역 | 단독 셀 | OKLab L 중앙값 |
|---|---:|---:|---:|---:|
| 원본 unlit point 색 | 189 | 287 | 262 | .256064 |
| 60 재질 대표색 → P | 6 | 21 | 6 | .364635 |
| 60 기존 선 처리 후 | 9 | 37 | 13 | .339208 |
| 62 영역 기준색 | 45 | 162 | 117 | .256064 |
| 62 P[region,Q] | 62 | 175 | 132 | .256064 |
| 62 동일 선 처리 후 | 74 | 189 | 144 | .251989 |

가시 source 영역66 / topology 조각45 / 조합 instance196이다. 전체 원본 UV cache의 연결 영역2146개를 가시 특징2146개라고 해석하지 않는다. 현 가시 영역에서 사용 가능한 전체 P 색은90개, 실제 점유 색은 위 표와 같다. 재질 하나를 한 색으로 만든 60의 원본 무늬 손실과 밝기 편향은 줄었지만, 단독 색과 복잡한 경계가 여전히 많다. 명도 중앙값이 원본과 가깝다는 이유로 성공 판정하지 않는다. 전체 색에 보정 배율을 곱하지 않았다.

기준색의 원본 대비 ΔE_OK 중앙값 .006913 / p95 .020763, P 적용 후 .020986 / .057278이다. 이 값은 명암과 원본 색 변화가 섞인 거리이며 미술 합격 기준이 아니다. PNG에서 어두운 바탕과 밝은 띠가 다시 보이는 반면, 특히 하단의 작은 명암 조각은 여전히 산만하다.

## 과거 실패 재검사

- source-known 358셀에서 v3의 **단독106 / 동일 appearance·Q 쌍400개 중 추가 경계113**을 실제 저장 입력으로 재현했다. protected64는 단독184 / 연결 영역214 / 추가 경계207이다.
- 62 후보는 같은 입력에서 단독136 / 연결 영역178 / 추가 경계140, RGB79색, 변경338셀이다. protected64보다 숫자는 줄었지만 v3보다 여전히 조각이 많다. 64색이라는 예산을 그대로 재사용하거나 189색 그대로 출력을 해법으로 삼지 않았다. 결과를 정돈 성공으로 채택하지 않았다.
- region-colour40의 실제 24셀 변경, coherent 4셀 변경, contrast-bounded **18건 기각·0변경**을 동결 재사용했다. coherent에서 (11,14)→(12,14)의 출력 ΔL .008162→0, 실제 source ΔL .002267 같은 국소 대비 손실을 좌표별로 기록했다. 작고 낮은 대비라는 이유로 의미 없다고 단정하지 않는다. 원본 소스 대비가 존재한다는 것만으로 모든 미세 대비를 hard constraint로 고정하지도 않는다.
- 보호 7쌍 × 4Q에서 색 구분과 밝기 방향은 모두 유지했다. 그러나 **과거 filtered source의 최소 대비**를 모든 Q에서 유지한 것은 id0·2·6·7의 4쌍뿐이고 id3·5·8은 실패했다. equal-Q id4도 색 구분은 유지했으나 최소 대비는 Q0·2만 통과했다. 예: id8의 과거 filtered ΔL .030356 / 원본 native point ΔL .027218. source sampling 차이와 RGB8 단계화 오차를 대비 증폭으로 숨기지 않았다. `FEATURE_TESTS62.json`에 두 출처와 모든 실제 출력색을 보관한다.
- 같은 재질의 분리된 두 무늬는 다른 UV region ID를 유지하고 동일 색이면 팔레트 참조만 공유한다. 같은 색의 서로 다른 기하 구조도 다른 structure ID를 유지한다. 1-texel accent는 면적 필터로 삭제되지 않는다. `IDENTITY_FIXTURE62.png`와 `INDEPENDENCE_FIXTURE62.json`이 최소 반례다. 실제 머리의 모든 작은 특징을 이 합성 fixture로 검증했다고 말하지 않는다.

## 보존·수학 검사·실행 방법

- `test_math62.py`: 기존54 JS 색 함수와 518색 비교, 최대 Lab 성분 오차 6.80e-16, RGB8 왕복 불일치0. 최초 행렬 계수 두 개를 바꿔 쓴 후보는 자홍색이 나와 실패했으며 `invalid-math-*`로 분리했다. 고친 결과로 덮어 성공 기록으로 바꾸지 않았다.
- `test_regions62.py`: 동결 NPZ/JSON/PNG만으로 원본 정체성 최소 반례, 현재373 P 직접 조회·간격/Q 독립성, 과거106/184/113 반례를 재검사한다. Python3 + NumPy/Pillow로 `python -B test_regions62.py` 실행. 이 재검사는 Unity/원본 모델 파일 없이 가능하다. `test_math62.py`는 같은 저장소의54 모듈과 Node가 필요하다.
- `run62.py`는 원본 VRM과59·60 저장 buffer, 과거 source 대비 표지 파일을 다시 읽어 cache/출력을 재생한다. 입력 위치는 코드 상단에 명시되어 있다. 현재 PC의 기존 작업 경로가 필요하며 새 GPU 캡처는 하지 않는다. `audit_source62.py`도 원본 embedded PNG와 동일 SHA인 기존 model-source PNG 경로가 필요하다.
- `PNG_PRESERVATION62.json`: 실제 960×544 PNG의 머리 밖 RGBA 변경0, 전체 alpha 변경0. 소유권/깊이/기하/g/Q는 입력 그대로 유지했다. 전체 캐릭터 PNG는 저장된 배경에 새 머리 색을 **오프라인 재합성**한 것이며 새로운 Unity 렌더나 시간 검증이 아니다.
- 제품 파일·Unity 실행/조회·Play·CUA·GC·SaveAssets·앱 종료는 이번 작업에서0회다. 현재 Unity 상태를 새로 확인했다고 주장하지 않는다. 마지막 실제 상태 증거는61이며 그때의 dirty30과 global 복원 한계는 그대로 유지한다.

## 63 global 원래 백업 접근 한계 — 코드만 확인

60 실제 실행본 `RUN_compare3.cs.txt:249`의 원래 값은 `CommandScript` 인스턴스의 private 딕셔너리5개에 있다. `Finish:307`은 update 구독을 해제하며 원래 값을 export하지 않았다. SDK `AgentRunCommand.cs:17/104`는 private `m_ActionInstance`에 보유할 수 있지만 public 회수 getter가 없다. `RunCommandUtils.cs:118`이 호출하는 `CommandScriptPostBox.Pull:19`는 key를 Remove하여 소비한다. `RunCommandTool.cs:51/95`는 로컬 wrapper를 만들고 execution ID/로그만 반환한다.

따라서 기존 기록/공개 참조에서 안전하게 읽을 살아 있는 핸들을 식별하지 못했다. 객체가 반드시 GC됐다고 단정하지도 않는다. 반사 조회·새 probe·추정 setter·buffer binding 복원은 하지 않았다. 원래63개와 현재값의 전체 동등성은 계속 증명 불가다.

## 남은 결정

색 출처→연결 영역→P 직접 출력 계약은 동작하지만, 이 범위화가 원본의 긴 무늬와 부드러운 gradient를 충분히 구별하지 못한다. 원래 source 대비 표지의 강한 제약과 일반 texture 변화의 완만한 제약을 연결하는 다중 영역 경계 모델이 남는다. 현재 낮은 단독 셀 수/중앙값 맞춤을 위해 특징을 지우는 새 처방이나 전체 밝기 보정을 덧붙이지 않았다. 실제 GPU 연결·필터 footprint·회전/가림·연속 프레임·전체 미감 검증은 미수행이며 제품 기본 경로로 전환하지 않는다.
