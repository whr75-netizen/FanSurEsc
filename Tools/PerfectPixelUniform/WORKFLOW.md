# 쿼터뷰 픽셀 제작 — 로컬 실행 계약

현재 행동과 진입점의 단일 원본이다. 제작 이력은 [README](README.md), 구현별 계약은 DESIGN06/07/08/09, 일반 실행기는 [WorkLoop](../WorkLoop/README.md)를 따른다. 실행 구조는 기존 계산을 연결하고 명시된 변경 원인의 단계만 수정한다.

생성 원화의 색/선 정리는 [R10](REDRAW_DESIGN.md) → `redraw_cli.py --source <PNG> --output <새폴더> --levels 4` 또는8768웹V4를 사용한다. 이 경로의 source1px 재작성과 V9의 알려진 기하 픽셀 제작은 서로 다른 입력 계약이다. 원래 logical grid 복원/물리 재조명/Unity 통합 완료로 바꾸지 않는다.

## 1. 다음 작업의 행동 순서

1. 요청에서 **변경 원인·담당 요소·보존 요소·최종 관찰 단위**를 정한다. 변경 원인이 없으면 현재 PNG를 재사용한다. 새 실행 ID나 검사 통과를 새 제작의 이유로 삼지 않는다.
2. 원본/recipe/부품/재료/카메라의 실제 경로와 단위를 확인한다. 생성형은 디자인·재료 후보이며 기하/가림/배치의 권위 입력으로 자동 승격하지 않는다.
3. 해당 원인에 필요한 경로만 선택하고 `plan`으로 그래프·코드 해시·출력 위치를 고정한다. 한 번의 요청에 한 실행을 사용하며 단계마다 AI에게 판단을 돌려주지 않는다.
4. `run`으로 고정된 단계와 마지막 기술 검사를 연속 실행한다. 실패하면 원인 단계·측정값·기대값을 읽고 그 단계와 후속 의존성만 수정한다. 원인 미확인 상태에서 재생성/축소/스케일/팔레트로 숨기지 않는다.
5. native PNG와 정수 확대 미리보기, 실제 검사 범위, 적용 여부를 제출한다. 미술적 만족도 질문을 자동 종료 조건으로 쓰지 않는다. Unity 적용 요청이 있으면 아래 적용 계약과 실제 Editor 관찰까지 수행한다.

## 2. 선·좌표·깊이의 고정 규격

canonical은 local tick `(x:폭, y:높이, z:깊이)`다. 현재 구현의 변환은

```text
Blender Z-up world = (-z/32, x/32, y/(32√6)) m
camera = azimuth 45°, elevation 30°, density 64√2 px/m
native screen = (u, v) = (2x - 2z, -x - z - y) + integer canvas origin
x축 한 tick = (+2, -1)px; z축 한 tick = (-2, -1)px; y축 한 tick = (0, -1)px
```

화면 좌표는 오른쪽/아래가 양수다. **카메라 고도 30°와 화면 사선 각도 arctan(1/2)=26.565°는 다르다.** 화면 선을 별도로 30° 회전하지 않는다. 축별 물리 tick 단위가 다르므로 새 모델에 metre 좌표를 그대로 tick으로 넣지 않는다.

현재 2:1 축선의 정수 끝점은 `p(k)=p₀+k(2,-1)` 또는 `p₀+k(-2,-1)`로 계산한다. 매 정점의 같은 투영식과 같은 canvas origin을 사용한다. 일반 정수 선은 Bresenham 같은 표준 raster 규칙으로 처리할 수 있으나, 현재 생산 코드는 **native 픽셀 중심의 finite BVH 최근접 표면/normal/depth/part**를 사용한다. 선 그리기를 새 렌더러로 추가하지 않는다.

일정한 사선은 면의 방향을 해결한다. 숨은 면·단차·접합·형태·가림 순서는 별도 기하 입력이 필요하다. 기존 `consistent_edges`는 보이는 인접 면과 깊이에서 경계 소유자를 계산한다. 뒤쪽 다리 등 숨은 면을 임의 레이어로 앞으로 올리거나 선 팽창으로 덮지 않는다. 교차점까지 모든 선이 항상 한 픽셀이라는 보장은 현재 계약에 없다.

폭 확장은 `W(n)=4+20n`, `xᵢ=2+20i`의 고정 끝단+동일 모듈 반복이다. 한 모듈 이동은 화면 `(40,-20)px`여서 격자 위상이 유지된다. 모듈을 늘릴 때 이미지나 메시 전체를 늘리지 않으며, UV는 기존 물리 주기를 따른다. 현재 검증된 변형은 2칸/3칸이고 임의 가구/모든 폭을 자동 설계하는 기능은 아니다.

## 3. 원인별 실행 경로와 입출력

| 원인/경로 | 고정 입력 → 연산 → 출력 | 이번 실행의 경계 |
|---|---|---|
| 변경 없음 / `reuse` | current.json의 현재 Parametric09 validation 및 native 해시 → 경로 반환 | 생산·변환·검사 그래프 재실행 없음 |
| 손잡이 경계 / `handles` | 기존 V7 box/buffer+V8 wood-map → `geometry → pixels → validate` | 정확 slab 최근접 판정과 후속 경계; 새 mesh/목재 저작 없이 복구 |
| 과거 목재 경로 / `wood` | Source06 원화+recipe08+**기존 Parametric07-fixed** → `material → pixels → validate` | V8 재현용; 기존 손잡이 경계 결함을 포함하므로 현행 제작에 사용 금지 |
| 과거 기하 경로 / `structure` | recipe07+실제 flat profile+기존 V6 재료 → `geometry → pixels → validate` | V7 재현용; 기존 손잡이 경계 결함을 포함하므로 현행 제작에 사용 금지 |

`handles`는 고정 V7 치수의 정확 교차와 기존 V8 재료를 연결한 현재 경로다. 과거 `wood`는 새 `structure` 출력과 자동 연결되지 않는다. `wood_material08.py`의 PREVIOUS가 recipe08의 기존 V7에 고정되어 있기 때문이다. **임의 새 기하+4색의 통합은 입력 경로 계약을 먼저 변경할 다음 작업**이며 현재 실행기로 완료했다고 보고하지 않는다. 단순 색/치수 변경도 실제 구현과 검사의 허용 변수인지 먼저 확인한다. 설정 일부를 바꾸면 모든 부품이 자동 대응한다고 가정하지 않는다.

| 단계 | 실제 산출/다음 소비자 | 정보 손실·실패 귀속 |
|---|---|---|
| 원화/재료 | 원화 RGB 표본·ROI → 역할 팔레트·wood-levels | 밝기 백분위/작은 성분 합병은 명시적 손실 저작; 디자인 의미나 원화 전체 복원 보증 아님 |
| 기하/투영 | 실제 scene.blend·부품 bounds → native surface/depth/normal/part/visibility | 단차·가림·치수가 틀리면 기하 원인. 기본 Blender beauty render가 final PNG가 아님 |
| 픽셀 채움/경계 | 같은 격자의 surface·UV·band·palette → native PNG·역할 배열 | 연속 조명 RGB 곱/AA/이중 픽셀화 없음. 무늬색과 구조 명암을 분리하고 같은 팔레트에서 선택 |
| 최종 기술 검사 | 저장 PNG·배열·원본 해시 → validation.json | 원인에 관련된 검사만 마지막 1회. 미술 합격·Unity 표시 합격과 구분 |
| 표시/적용 | native PNG+anchor+공통 밀도 → 미리보기 또는 Unity 소비 | 표시용 확대에서 native를 다시 만들지 않음. 실제 엔진 표시는 별도 관찰 필요 |

native로 직접 계산된 이 경로에는 PerfectPixel을 다시 적용하지 않는다. 새 생성형 시트 경로는 **시트 전체 원본 격자 자동 검출/정규화 → 격자를 보존한 정수 crop → 배치**다. 격자 미검출을 64×64 등 강제 축소로 대체하지 않는다. 정규화가 디자인/무늬/숨은 면을 만들어 주는 것은 아니다.

## 4. 로컬 명령 진입점

`pipeline_cli.py`는 기존 WorkLoop와 생산 코드를 호출하는 얇은 실행기다. 새 패키지/AI 호출/GUI는 없다. 프로젝트 루트에서 현재 NumPy/Pillow가 있는 Python을 사용한다.

```powershell
$pixelPython = 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
# 변경 없는 현재 결과: 생산하지 않음
& $pixelPython -B Tools/PerfectPixelUniform/pipeline_cli.py reuse
# 계획/해시/출력 고정만: Blender·재료·픽셀 생산하지 않음
& $pixelPython -B Tools/PerfectPixelUniform/pipeline_cli.py plan --route handles --run-id handle-example-01 --reason '요청된 손잡이 경계 수정의 원인'
# 기존 계획을 1회 연속 실행
& $pixelPython -B Tools/PerfectPixelUniform/pipeline_cli.py run --run-id handle-example-01
# 실제 생산이 승인된 작업에서 계획+실행을 한 번에
& $pixelPython -B Tools/PerfectPixelUniform/pipeline_cli.py start --route handles --run-id handle-example-02 --reason '요청된 손잡이 경계 수정의 원인'
# 상태/중단/재개: resume은 재개 허용만 하며 run은 별도
& $pixelPython -B Tools/PerfectPixelUniform/pipeline_cli.py status --run-id handle-example-01
& $pixelPython -B Tools/PerfectPixelUniform/pipeline_cli.py stop --run-id handle-example-01
& $pixelPython -B Tools/PerfectPixelUniform/pipeline_cli.py resume --run-id handle-example-01
```

현재 복구 경로는 `--route handles`다. 과거 wood/structure는 역사 재현용이며 현행 자산 제작에 사용하지 않는다. `reason`은 변경 이유 기록이며 이유의 타당성을 프로그램이 증명하지 않는다. 이미 끝난 결과를 동일 입력으로 다시 생산하는 명령으로 쓰지 않는다. 사용자가 명령을 매번 작성하는 방식이 아니라 AI가 위 계약으로 원인을 정하고 호출한다.

산출 위치는 `LocalOnly/PerfectPixelUniform/runs/<run-id>/`의 `graph.json`, `state.json`, `binding.json`, `outputs/`다. 메타데이터 폴더와 아직 존재하지 않는 outputs 폴더를 분리한다. 기존 run ID는 덮어쓰지 않는다. `plan`은 그래프를 고정하되 생산하지 않는다. 출력 위치만 새로 바인딩하고 원본 그래프/코드/recipe를 바꾸지 않는다.

실행 완료는 shell exit0만으로 정하지 않고 WorkLoop의 `graph_complete`·state.complete·저장 validation.passed·실제 native 출력 SHA를 확인한다. blocked/paused/uncertain은 run/start의 비성공으로 반환한다. 완료 상태에서 `run`은 생산하지 않고 저장된 결과의 상태를 반환한다. 실패 시 stdout/stderr/실행 단계는 state.json에 남는다. **stop/resume은 대기 상태의 pause만 지원한다.** 기존 WorkLoop가 연속 실행 전체에 lock을 유지하므로 진행 중 즉시 취소나 다음 단계 중단은 현재 미지원이다. 불확실한 실행이나 잔존 lock은 실제 writer가 종료했는지 확인하기 전 제거/재시도하지 않는다.

## 5. Unity 적용 계약 — 실행기 미연결

현재 실행기는 PNG 제작까지이며 씬 writer/importer는 붙이지 않았다. 이후 적용 시 native PNG의 픽셀 수·공통 PPU·ground anchor에서 실제 크기와 위치를 계산한다. 회전된 쿼드를 늘려 각도를 맞추거나 자산별 임의 scale/offset을 넣지 않는다. 카메라 상대 평면/투영과 충돌 체적은 선언된 배치 방법으로 분리한다.

Point sampling, 압축/밉맵/AA/후처리 재표본화, 표시 격자 위상을 실제 Unity importer·material·camera에서 확인한다. 이 설정 확인을 자동으로 게임 화면 합격이라고 부르지 않는다. 확대 미리보기는 정확 정수 nearest 표시이며 native 해상도 변경이 아니다. 공통 픽셀 밀도에서도 큰 가구는 더 많은 픽셀/더 큰 실제 크기를 가진다.

## 6. 다음 세션에서 먼저 읽을 것

이 문서 → 변경 원인의 DESIGN/recipe/담당 함수만 읽는다. 원인 없는 전체 이력/전체 검사 반복은 하지 않는다. 실제 mesh 치수는 Parametric07-fixed, 재료는 Parametric08, 수정 surface/제출 PNG는 Parametric09다. 승인된 게임 씬은 그대로 보존한다. 통합/실제 표시/디자인 수정 요청이 생기면 그 단계의 입력과 완료 기준을 먼저 확정한다.

근거: 기존 코드와 저장 결과가 직접 실행 근거다. 직교 투영 원리는 [PBRT](https://www.pbr-book.org/4ed/Cameras_and_Film/Projective_Camera_Models), 같은 부품 반복은 [Blender Array API](https://docs.blender.org/api/5.0/bpy.types.ArrayModifier.html), 평면 직사각형 9-slice의 적용 범위는 [Unity 공식 문서](https://docs.unity3d.com/6000.0/Documentation/Manual/sprite/9-slice/9-slicing.html)를 참고한다. 현재 반복은 직접 계산이며 실제 ArrayModifier 사용이 아니고, 사선 전체 외형을 9-slice로 늘리는 방식도 아니다.

실행 구조 정리 당시(2026-10-03)의 두 과거 경로 plan/init·생산0회·경로/해시30조건·pause/run거부 기록은 `LocalOnly/PerfectPixelUniform/workflow-validation.json`에 보존한다. 이후 사용자 손잡이 수정 요청으로 handles 경로 start를 실제1회완주했다. 모든 문14/서랍16px·이동 정렬 mask/face/normal/ink/RGBA·원본/목재/alpha 보존 등73조건을 확인했고 실행기는process포함2.24초였다. Parametric09/publication/workloop 기록이 현재 근거다. Unity 적용은 하지 않았다.
