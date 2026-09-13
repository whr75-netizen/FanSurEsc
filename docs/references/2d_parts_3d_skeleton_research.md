# 2D 원화·3D 스켈레톤 캐릭터의 기법별 연구

외부 자료 조사 기록: 2026-09-10. 기법별 재구성: 2026-09-11. 이 문서는 방법·수학·출처·실험·실패를 누적하는 연구 참고자료이며, 새 프로젝트 지침이나 아트 승인을 정의하지 않습니다. 공식 엔진 문서, 제작사 설명, 구현자 기록과 공개 연구 코드를 비교했으며 인터넷의 모든 구현이나 원본 코드를 전수 검증한 조사는 아닙니다.

**후속 연구 — 2026-09-13:** 최신 요청의 모딩 재사용·깊이/노멀·미세 회전은 [픽셀 모딩 렌더 파이프라인 연구](pixel_modding_render_pipeline_research.md)에 정리했습니다. 완성 경로 5개, 공통 형상/리그 규격, 수학적 보장 범위와 제품 연결의 미확인을 비교한 문헌 조사입니다. 아래 D01의 구현 중단을 해제하거나 새 리그를 채택한 것은 아닙니다. 과거 실패의 재진단·새 실행도 하지 않았습니다.

## 1. 목표와 최신 요구

사용자 목표는 컨셉아트의 디자인을 입력해 스켈레톤·애니메이션으로 움직이고, clip을 추가·수정해도 모든 그림 프레임을 다시 제작하지 않는 기술입니다. 제작 입력은 정상적인 완성 정면 원화 한 장 → 같은 원화의 파츠 분리 → 관절·숨은 부분 보완입니다. 기존 Chibi의 체형·골격 재사용은 목표 자체가 아닙니다. 원화에 맞춘 새 rig도 후보이지만, 최신 요청은 무근거한 새 구현을 멈추고 후보 비교와 실험 설계를 먼저 갖추라는 것입니다.

**[사용자 요구]** 동작의 기준은 투명 3D 몸체 ↔ 스켈레톤 ↔ 부착 이미지의 연결입니다. 실행 흐름은 애니메이션 → 3D 본/스킨 변형 → 부착된 이미지의 변형·가림입니다. 자세가 틀리면 3D 본·리깅부터, 3D가 정상인데 이미지만 틀리면 부착 기준·bind pose·스킨웨이트부터 확인합니다. 파츠별 각도·길이 예외를 더하는 것은 이 연결의 대체가 아닙니다.

**[현재 구분]** E는 동일 원화에서 실제 이미지 구역 17개를 분리했지만 시험 골격의 원본 3D Renderer/SkinnedMeshRenderer·MeshFilter를 제거하고, 별도 2D 관절·seam 가중치로 메시를 변형했습니다. 따라서 요구한 3D 몸체 표면/스킨웨이트 바인딩은 아닙니다. 팔다리가 정상처럼 보인다는 이전 피드백도 구조 승인으로 해석하지 않습니다. [F](#experiment-f)는 실제 스킨 연결을 시도했으나 출력이 깨졌으며, 구현을 중단하고 기존 증거를 회수한 상태입니다. 새 Blender rig를 정답으로 선정하지 않았습니다.

화면에 보이는 그림, 형태를 변형하는 표면·관절, 동작을 공급하는 clip은 서로 다른 데이터입니다. “디자인만 넣는다”는 최종 사용 경험과 현재 필요한 관절·mask·연결부·깊이 데이터 저작도 구분합니다. 정면 그림에 없는 옆면·뒤통수·발바닥·가방의 숨은 면을 관절 수학만으로 복원했다고 주장하지 않습니다.

<a id="current-decision"></a>
### 1.1 현재 결정 — D01: 구현 중단, 후보 적합성 재검토

2026-09-11. 공통 R&D 절차와 그래픽 수학 계약은 [playbook §1.4~1.5](../ai/UNITY_ENGINEERING_PLAYBOOK.md)에 있고, 여기에는 이 주제의 사실·결정만 기록합니다. 최신 요구에 따라 독자 알고리즘 선정보다 공식 웹 기술 근거를 우선합니다. 좌표계/Transform 명세와 canonical 측정·허용오차가 채워지기 전에는 프로덕션 구현으로 넘어가지 않습니다.

| 항목 | 현재 내용 |
|---|---|
| 범위·단계 | **R2 재개 전 정리**. 캐릭터·씬·rig의 새 구현은 이번 절차 수정 요청에 포함하지 않음. 기존 시험/Player 보존 |
| 핵심 질문 | 원화 비율과 깊이 굽힘을 유지하면서 새 동작을 이미지 재제작 없이 받으려면, 어떤 표현·rig·저작 데이터가 필요한가? |
| 확인된 것 | 정면 원화·17개 구역 메시·기존 Humanoid 재료 존재. E는 요구 메커니즘 불일치. F는 기준 자세 오차가 줄어도 실제 화면이 깨짐 |
| 미확인 | 원화에 맞춘 입체 표면/깊이의 제작량, 해당 표면의 스키닝 품질, 새 clip 호환, F의 native/CPU 진단 출력 차이의 원인 |
| 현재 결정 | F를 채택하지 않음. 기존 Chibi 고수와 신규 Blender rig 확정 모두 보류. 다음 후보는 아래 비교에서 근거·계약을 채운 뒤 선택 |
| 다음 한 행동 | 공식 geometry/rigging/skinning/projection/UV/retargeting 문서와 현재 입력을 대조하여 공간·Transform·canonical·G01~G12의 실제 값/허용오차를 작성. **아직 명세 필드별 값·검사 코드·새 시험 결과 없음** |
| 완료 경계 | 연구·절차 정리와 캐릭터 완성을 구분. 후보 선택·실제 연속 동작·미사용 clip 수용·사용자 시각 확인은 아직 완료되지 않음 |

### 1.2 문제공간과 후보 파이프라인

M01~M08은 **기법 모듈 분류**입니다. 스키닝·리타기팅·깊이 표현·픽셀 출력은 함께 쓰일 수 있으므로 여덟 개의 상호 배타적인 완성 파이프라인처럼 순서대로 구현하지 않습니다.

| 문제 축 | 고정 요구/기존 사실 | 선택 전에 해소할 의문 |
|---|---|---|
| 입력·디자인 | 승인된 정면 원화, 디자인 임의 변경 금지 | 숨은 면·겹침 여유·깊이를 어느 데이터로 추가 저작할 것인가 |
| 형상·관절 | 3D 동작에 따른 깊이 굽힘·투영 길이 | 원화 체형과 rig 관절이 일치하는가, 평면인지 입체 표면인지 |
| 동작·모딩 | clip 추가 시 프레임 이미지 전량 요구 금지 | clip→rig 대응 규격, 새 동작에서 추가 보정 없이 작동하는 범위 |
| 출력·표현 | 파츠·가림·일관된 픽셀 표현 | 렌더/픽셀 처리를 어디서 하는가, 카메라 전체 효과는 제외되는가 |
| 비용·제작성 | 디자인 투입 후 재사용 가능한 시스템 목표 | 최초 파츠·깊이·weight 저작과 런타임 비용, 모딩 배포 경로 |

다음 세 후보는 기존 연구 분류를 묶은 **조사·비교용 연결안**이며 이미 호환되는 제품 조합이나 채택 결정이 아닙니다. 최신 사용자 요구 이후 이 연결안을 그대로 구현하는 것은 보류하며, 공식 기술 근거로 각 연결이 성립하는지부터 확인합니다.

| 후보 | 끝까지 연결한 경로 | 근거가 있는 구간 | 아직 입증되지 않은 연결·현재 판정 |
|---|---|---|---|
| P1 원화 맞춤 3D 스킨 | 원화/파츠 → 비율 맞춘 proxy·rig·UV/weight → Humanoid clip → 스킨/가림 → 오브젝트별 픽셀 출력 | Blender armature와 Unity bindposes/retargeting은 각 단계의 표준 기능 [S08][S21][S22] | 원화→표면·관절 대응과 숨은 면, 평면 파츠의 옆면/관절 품질. **새 rig를 만든다는 이유만으로 합격 아님** |
| P2 깊이 sprite | 파츠/rig → 편집 가능한 depth → bone 변형·재투영 → sprite 출력 | Smack 제작사는 파츠/3D bone/depth/compute 재렌더와 sprite sheet export를 설명 [S05][S06] | Unity runtime에서 새 Humanoid clip을 받는 형식/구현은 미확인. export 이미지가 곧 runtime SDK인 것은 아님 |
| P3 실시간 3D 표현 개선 | 원화에 맞춘 3D 외형/rig → clip → 표면 조명·단계화 → 오브젝트별 픽셀 출력 | A의 기존 비교물과 M01의 엔진 경로 | 원화 특징 재현·시간적 명암 안정성, 현재 2D 파츠 부착 메커니즘과 다른 방향. **기준 비교물만 유지**, 대체 채택에는 요구 변경 합의 필요 |

M02의 고정 sprite sheet만 사용하는 경로는 새 clip을 받아 즉시 움직이는 요구와 다릅니다. 자동 재bake/cache 같은 추가 경로가 없는데 동일 기능이라고 취급하지 않습니다. 그 추가 기능은 이번에 구현하지 않습니다.

### 1.3 첫 판별 시험 설계 — 실행 전 제안

H1~H3는 필요한 질문을 좁힌 초안이며 playbook §1.5의 공간별 값·변환별 공식/허용오차·canonical·자동 검사 명세를 완성한 상태가 아닙니다. 이를 구현 승인이나 새 rig 선정으로 사용하지 않습니다.

**H1 좌표 계약.** 이미지 왼쪽/오른쪽, 해부학적 Right/Left, bone local축, world축, camera right/up을 각각 명시합니다. 현재 `source-first.json`에는 `screenLeftShoulder(x=373)→RightUpperArm`, `screenRightShoulder(x=650)→LeftUpperArm`으로 적혀 있습니다. 이 명명만으로 투영까지 맞았다고 볼 수는 없습니다. 비대칭 R/L 표식과 한쪽 팔만 움직이는 입력으로 변환 끝까지 대응을 확인하는 시험이 필요합니다. 과거 어깨 반전의 정확한 발생 위치는 이번 기록 작업에서 재현·확정하지 않았습니다.

**H2 변형 계약.** `v(t)=Σ wᵢ Bᵢ(t) Bᵢ(bind)⁻¹ v(bind)`에서 모든 행렬의 공간·root scale을 먼저 맞춥니다. 기본 자세 왕복, 한 관절의 앞뒤 굽힘과 투영 길이 변화, 원래 자세 복귀를 확인합니다. 좌우/축이 틀리면 H1, rig 자체가 틀리면 rig/clip, rig는 정상인데 그림만 틀리면 weight/bind/공간 경계로 돌아갑니다. 식의 항등성 통과만으로 실제 렌더 합격을 선언하지 않습니다.

**H3 입력 정보.** 올바른 3D 변형에서 가려졌던 면이 비면 단순 각도 오차와 구분합니다. 필요한 파츠 여유·깊이·숨은 면을 확인하고, 원을 덮거나 clip별 이미지 offset을 늘려 구조 문제를 숨기지 않습니다. 고정 정면에서 허용할 표현 범위도 명시합니다.

한 관절 계약을 확인한 뒤에만 전체 파츠로 확장하고, 이후 제작에 쓰지 않은 clip 하나로 **새 동작 추가 시 이미지 재분할/재바인딩/clip별 코드가 필요 없는지**를 확인하는 것이 모딩 판정입니다. 이는 다음 실험 설계이며 이번에 실행했다고 주장하지 않습니다. 새로운 rig도 이 조건을 동일하게 통과해야 합니다.

### 1.4 절차 점검: 기존 실패를 새 기준에 대입

| 기존 상황 | 새 절차에서 걸리는 경계 | 아직 증명하지 못한 것 |
|---|---|---|
| 본 기반이면 자동으로 맞을 것이라 보고 전체 연결 | R1 입력 적합성·R2 좌표 계약, H1 | 과거 어깨 반전 원인의 재현/해결 |
| E의 2D seam 변형을 요구한 3D 표면 연결처럼 취급 | R0 메커니즘 대조 | E 전체 기법이 다른 용도에서도 불가능하다는 주장 |
| F의 낮은 기준 정점 오차를 출력 성공으로 취급할 위험 | R3 실제 렌더와 동작 비교; 아래 실패 캡처 | native/CPU 차이의 정확한 원인 |
| F 실패 후 새 Blender rig를 바로 정답으로 선택 | R2 경쟁 원인·후보별 탈락 조건 | 새 rig가 현재 렌더 오류까지 해결한다는 주장 |
| 파츠 생성·연구 기록 후 구현 완료처럼 종료 | R4 요청 출력과 전달 상태 대조 | 이 문서 수정만으로 이후 AI 실행이 항상 준수됨 |

위 표는 **기존 증거를 이용한 절차 검토**이지 새 캐릭터 시험이나 새 지침의 효과를 측정한 실험이 아닙니다.

## 2. 기법 목록과 실험 찾기

기법은 입력·변형·출력 방식으로 구분하고, A~F는 각 기법을 실제로 시험한 기록 ID로 유지합니다. 실험 순서가 기법의 분류나 채택 순서를 정하지 않습니다. 기존 결과·원화·시험 오브젝트는 비교 증거로 보존합니다.

| 기법 ID | 입력 → 동작/출력 원리 | clip 추가·변경 시 | 실험과 현재 판단 |
|---|---|---|---|
| [M01 — 실시간 3D와 픽셀·조명 표현](#m01) | 3D 표면·스킨 → 카메라 렌더·픽셀 표시 | 같은 rig 범위에서 실시간 재생 | [A](#experiment-a): 기존 동작·가림 비교물 보존 |
| [M02 — 3D 애니메이션의 사전 sprite bake](#m02) | 3D 동작 → 시점·시간별 완성 프레임 | 바뀐 출력은 다시 bake | [B](#experiment-b): 기존 비교물 보존 |
| [M03 — 2D cutout과 3D bone 투영](#m03) | 부위 그림 → 3D 관절 투영·파츠 변환·가림 | 원화·관절 대응·표시 규칙 재사용 | [C](#experiment-c), [D](#experiment-d): 불합격/거부; [E](#experiment-e): 부분 관찰, 요구 메커니즘 불일치 |
| [M04 — 실제 3D 스킨에 이미지 바인딩](#m04) | 적합한 3D 몸체·bind pose·weight → 이미지 부착 표면 변형 | 동일 스킨/관절 범위에서 실시간 재생 목표 | [F](#experiment-f): 출력 실패·중단; 새 rig 미선정 |
| [M05 — depth/height로 입체 정보 보충](#m05) | 그림·깊이·3D bone → 회전 후 픽셀 재투영 | 깊이·rig 데이터 재사용 후보 | Smack Studio 공개 설명 조사; 프로젝트 실험 없음 |
| [M06 — normal map을 이용한 조명](#m06) | 기존 표면·그림·법선 → 광원 반응 | 조명 반응 재계산 | 기능 구분 조사; 독립 실험 없음 |
| [M07 — 3D motion을 해석한 2D 변형](#m07) | 3D 관절 → 2D rig/ARAP/가중 mesh | 같은 관절 대응의 motion 재사용 | 공개 구현·엔진 기능 조사; 해당 방식의 독립 실험 없음 |
| [M08 — 다중 시점 impostor](#m08) | 여러 방향 bake·normal/depth → 시점별 대체 렌더 | 임의 새 동작 대응은 별도 문제 | Amplify 문서 조사; 프로젝트 실험 없음 |

M03의 투영된 파츠를 2D에서 변형하는 것과 M04의 실제 3D 표면 스킨 변형은 다릅니다. M05의 깊이와 M06의 법선도 같은 데이터가 아닙니다. M02는 완성 동작 프레임 출력, M08은 주로 여러 관찰 방향의 대체 표현이라는 구분입니다. Smack Studio가 sprite sheet를 출력한다는 사실만으로 내부 방식을 M02로 분류하지 않습니다.

### 2.1 상태와 실험 기록 형식

상태는 **조사만 / 진행 중 / 부분 관찰 / 불합격·거부 / 중단 / 보존·재검증 없음**으로 적습니다. 구현, 실제 실행 관찰, 사용자 시각 판정은 따로 기록합니다. 빈 항목은 미기록이며 실제 미실행인지 먼저 확인합니다. 수학식이나 성공 메시지는 실행 증거가 아닙니다.

| 고정 항목 | 각 실험에 남길 내용 |
|---|---|
| ID·상태·날짜·비교 | 기법 ID, 실험 ID, 기준 결과의 위치, 현재 판단 |
| 목표·이번 차이 | 사용자에게 보일 결과, 검증할 가설·차이, 맞거나 틀렸을 때의 예상 관찰 |
| 입력·재현 | source·해상도, clip·reference 시간, 관절/PPU·카메라/표시 조건 |
| 절차·수학·구현 | 실제 처리 순서, 코드 위치, 식과 변수, 외부 근거와 자체 구현의 차이 |
| 관찰·결과·증거 | 실제 조작·자세·이미지·기술 값, 사용자 판정, 미실행 항목 |
| 실패·원인 | 증상, 직접 확인한 원인, 가설, 보존한 실패 결과 |
| 미해결·다음 판정 | 지지/기각/판정 불가, 후보 유지/보류 이유, 재개 조건과 다음 한 가지 판정 |

<a id="m01"></a>
## 3. M01 — 실시간 3D와 픽셀·조명 표현

**원리·수학·자료.** 기존 3D mesh의 스킨 변형과 카메라 투영을 유지하고 그 렌더 결과를 픽셀 표현으로 표시합니다. 일반적인 가중 스킨 개념식은 [M04](#m04)의 bind pose 식과 같습니다. 픽셀 샘플링과 광원 계산은 표현 단계이며, 원화 한 장을 기존 몸체에 연결하는 과정 자체를 제공하지 않습니다. bind pose의 일반 근거는 [Unity Mesh.bindposes][S08]이고, A의 구체적 조명·픽셀 계산은 이번 문서 재구성에서 코드로 재검증하지 않았습니다.

**구현 절차.** 정상 3D 골격·몸체를 기준으로 같은 clip·카메라에서 원래 가림과 투영을 확인한 뒤 픽셀 출력 조건을 비교합니다. Point sampling만으로 회전·확대·변형 시 계단 모양과 시간 흔들림이 모두 해결되는 것은 아닙니다. 실제 표시 크기의 선·관절·실루엣과 사용자 시각 판정이 필요합니다.

<a id="experiment-a"></a>
### 3.1 실험 A — Live 3D

| 기록 항목 | 기록 |
|---|---|
| ID·상태·날짜·비교 | M01/A, 보존·재검증 없음. 기존 A 비교물이며 원래 실행일은 이 문서에 기재되어 있지 않음 |
| 목표·이번 차이 | 기존 애니메이션·가림의 기준. 이번 문서 편집에 동작/조명 변경 없음 |
| 입력·재현 | 기존 3D 캐릭터·clip. 세부 clip·카메라 값은 이 문서에서 미확인 |
| 절차·수학·구현 | 기존 skinning → 카메라 투영. 현재 정확한 함수·수치는 미연결 |
| 관찰·결과·증거 | 기존 비교물 보존; 이번 문서 편집에서 재검증하지 않음 |
| 실패·원인 | 추가 실패 원인 미기재. 디자인 한 장 입력 방식의 증거로 사용 불가 |
| 미해결·다음 판정 | 관련 동작을 바꿀 때 필요한 기준 장면만 비교. A의 새 구현·반복 시험은 이번 연구 구조 변경의 범위가 아님 |

<a id="m02"></a>
## 4. M02 — 3D 애니메이션의 사전 sprite bake

**원리·수학·자료.** 3D 모델·clip을 시점과 시간 tₖ에서 렌더해 프레임 Iₖ를 저장하고 재생 시 해당 프레임을 선택하는 제작 경로입니다. 이 시간 샘플링 표기는 비교 원리이며 B의 실제 구현식을 검증한 것은 아닙니다. 특정 게임이 이 방식을 사용한다고 단정하지 않으며, 외부 게임 사례의 근거는 이번 조사에 추가하지 않았습니다.

**구현 절차.** 원본 rig·clip·시점·출력 크기를 정하고 프레임을 생성한 뒤 runtime에서 프레임을 선택합니다. motion은 재사용할 수 있어도 clip 또는 출력 조건이 바뀐 프레임은 재생성해야 합니다. 원화 파츠를 기존 skeleton으로 실시간 구동하는 목표와 제작 경로가 다릅니다.

<a id="experiment-b"></a>
### 4.1 실험 B — Sprite bake

| 기록 항목 | 기록 |
|---|---|
| ID·상태·날짜·비교 | M02/B, 보존·재검증 없음. 기존 B 비교물; 원래 실행일 미기재 |
| 목표·이번 차이 | 완성 프레임 출력 방식과 실시간 표시의 비교; 이번 변경 없음 |
| 입력·재현 | 3D 캐릭터·샘플링할 clip. 세부 출력 조건은 이 문서에서 미확인 |
| 절차·수학·구현 | 시간별 렌더 → 프레임 선택. 정확한 함수·수치는 미연결 |
| 관찰·결과·증거 | 기존 비교물 보존; 새 성공·실패 판정 없음 |
| 실패·원인 | clip·출력 조건 변경 시 bake 필요. runtime 파츠 구동 목표와 제작 경로가 다름 |
| 미해결·다음 판정 | 다른 기법 판정에 필요할 때 동일 자세 비교. 새 bake 도구 제작·프레임 확대는 미실행 |

<a id="m03"></a>
## 5. M03 — 2D cutout과 3D bone 투영

### 5.1 원리와 외부 구현

3D 관절을 화면/표시 평면에 투영하고, 부위별 그림의 위치·방향·길이·가림을 계산합니다. billboard, 방향에 따른 그림 교체, 투영 mesh 변형은 조합할 수 있는 서로 다른 처리입니다.

- **Project Terra / Alabaster Dawn.** Radical Fish Games는 figure editor가 관찰자에 대한 bone 각도에 따라 sprite를 표시·회전·교체한다고 설명합니다. 2023년 게임 콘텐츠 제작 사례입니다. 입증되는 것은 동작과 파츠 그림의 분리이며, 정면 원화 한 장으로 모든 방향의 품질을 얻는다는 주장은 없습니다. [공식 개발 기록, 2023-08-12][S01]
- **Sean의 Unity Bone Sprite Animation System.** billboard, 시점별 투영 변형, 방향별 sprite 교체, 카메라 거리/편집기 지정 순서 정렬, 의상·무기·눈 깜박임·머리카락 교체를 보여 줍니다. 팔·다리·무기에 효과적인 변형이 다른 부위에서는 모양을 망쳐 파츠 분할과 길이를 반복 조정했다고 합니다. 초기 prototype 2주, 전체 약 5개월은 저자의 경험이며 프로젝트 일정 예측이 아닙니다. 실시간 계산도 가능하지만 해당 구현은 계산값을 ScriptableObject에 굽습니다. 글의 View Source는 사이트 소스 링크이므로 완성 Unity 도구 공개 소스·재배포 허가로 해석하지 않습니다. [구현자 기록, 2024-05-03][S02]

### 5.2 좌표·관절·가림 수학

아래 식은 E의 설계·코드를 설명하는 기준입니다. 식 자체가 시각 합격이나 모든 clip 검증은 아닙니다.

- **공통 원화 좌표.** 좌상단 픽셀 (u,v), 표시 원점 (u₀,v₀), 공통 PPU s에 대해 q=((u−u₀)/s,(v₀−v)/s)입니다. crop 좌표에는 원본 crop offset을 먼저 더합니다. 각 파츠를 같은 높이로 따로 맞추면 원래 비율·어깨 위치가 바뀝니다.
- **기준 자세.** 팔을 내린 원화는 해당 reference idle과 연결합니다. FBX T-pose의 절대각을 그대로 곱하면 첫 프레임부터 팔/가림이 달라질 수 있습니다. reference clip·시간, source anchor, 표시 좌표계를 함께 기록합니다.
- **공유 관절과 두 점의 방향.** 인접 파츠가 같은 어깨·팔꿈치·손목·골반·무릎·발목 위치를 사용합니다. 팔·다리는 두 관절의 투영 벡터와 원화 축의 관계를 계산하며 모든 bone의 Transform.up이 그림 세로축이라고 가정하지 않습니다. 위치·방향·표시 길이를 나눠 관찰합니다.
- **E의 상대 FK.** a=artChild−artParent, s₀=Project(sourceChildReference−sourceParentReference), sₜ=Project(sourceChildNow−sourceParentNow). r=dot(s₀,sₜ)/|s₀|², b=cross₂(s₀,sₜ)/|s₀|²이면 targetChild=targetParent+[[r,−b],[b,r]]a입니다. 기준 대비 전역 투영 방향/길이 변화만 원화 뼈에 적용해 기준에서 항등변환을 얻습니다. 부모 회전을 다시 곱하지 않습니다. Offset 관절은 부모 화면 roll을 사용하고 root bob은 몸통 크기 비율 하나를 사용합니다. 구현: SourceFirstSpriteActor.ApplyCurrentPose.
- **투영 퇴화.** 발목→발끝 등의 투영 길이가 0에 가까우면 atan2에 유효한 방향 정보가 없고, reference 투영 길이 0이면 길이 비율도 정의되지 않습니다. 기준축·연속성·관찰 조건을 명시해야 합니다. 임의 90도 제한이나 부호 반전만으로 잘못된 축/관절 대응이 해결되었다고 보지 않습니다.
- **연결부와 폭.** 관절 간 투영 길이 축소는 전체 파츠의 균일 축소와 다릅니다. 관절 끝점을 유지할 영역과 부위 폭·부피감은 따로 평가합니다. 공유 joint c의 원형 보충 D={q:‖q−c‖²≤r²}에는 원화 접합부 색·픽셀 반경/PPU를 쓰고 pivot을 공유합니다. geometry 채움과 표시 범위를 고르는 mask는 다른 기능입니다.
- **가림.** 얼굴·뒤 머리카락·앞 머리카락처럼 역할이 다른 영역을 한 quad의 정렬 값만으로 분리할 수 없습니다. 같은 파츠 내부의 겹침도 필요하면 mesh 분할/triangle 순서를 검토합니다. 단색 cap은 무늬·재질 경계·옆면을 복원하지 않습니다.

두 joint 투영의 공개 근거는 [Meta 설정][S04], bind pose는 [Unity][S08], 원형 끝·숨은 영역 제작은 [공통 원화 제작 자료](#shared-art)입니다. 공통 PPU·상대 FK·Unity 절차 cap을 결합한 방식은 이번 구현 선택이며 외부 도구의 동일 구현을 확인한 것은 아닙니다.

### 5.3 구현 절차와 적용 경계

1. 정상 정면 원화와 원래 비율을 기준으로 joint·crop/polygon·앞뒤 레이어·가려진 연결부를 저작합니다.
2. source idle과 그림 관절을 대응하고 공통 좌표계에서 기준 조립을 확인합니다.
3. 3D 관절 두 점을 투영해 파츠 변환을 계산하고 연결부·가림을 적용합니다.
4. 같은 원화·clip 조건에서 기준 조립, 걷기, 발 회전, 머리 가림, 필요한 장비 교차를 구분해 관찰합니다.

clip과 그림을 분리하려면 같은 Avatar·관절 대응·표시 규칙 범위를 유지해야 합니다. 극단적인 회전, 팔다리 교차, 카메라를 향한 부위, 몸통 뒤 장비는 별도 미검증 조건입니다. 실제 Player/skeleton을 교체할 이유는 아니며, 방향 원화나 depth map 추가도 별도 아트 결정입니다. 최신 요구에서는 M03의 추가 예외 보정보다 [M04의 3D 바인딩](#m04)이 먼저입니다.

<a id="experiment-c"></a>
### 5.4 실험 C — Mesh cut

| 기록 항목 | 기록 |
|---|---|
| ID·상태·날짜·비교 | M03/C, 불합격. CHARACTER-RENDER-01의 기존 C 결과; 실행일 미기재 |
| 목표·이번 차이 | 분할 부위의 skeleton 구동 비교 |
| 입력·재현 | 기존 mesh 기반 분할 시험물. 세부 clip·카메라는 이 문서에서 미확인 |
| 절차·수학·구현 | 부위 분할·기준 변환·투영. 정확한 식/코드 근거는 아직 미연결 |
| 관찰·결과·증거 | 가림·관절 결과 불합격; 기존 C 보존 |
| 실패·원인 | 머리 앞뒤 결합·발 회전 등 실패. 부위 축·연결·가림 각각의 원인은 추가 분리가 필요 |
| 미해결·다음 판정 | C를 다시 다룰 때 원인별 코드 증거를 연결. E/F의 결과로 C의 실패 기록을 덮지 않음 |

<a id="experiment-d"></a>
### 5.5 실험 D — GeneratedFront01

| 기록 항목 | 기록 |
|---|---|
| ID·상태·날짜·비교 | M03/D, 사용자 거부. 기존 GeneratedFront01 보존 |
| 목표·이번 차이 | 생성 파츠를 기존 본 동작에 연결 |
| 입력·재현 | 독립 생성 파츠 atlas. 공통 완성 정면 원화 없음 |
| 절차·수학·구현 | 파츠별 anchor·좌표 대응으로 조립. 정확한 함수·수치는 이 문서에서 미연결 |
| 관찰·결과·증거 | 어깨 좌우·위치·파츠·레이어·동작 불일치로 사용자 거부 |
| 실패·원인 | 정상 정면 원화보다 atlas를 먼저 제작한 입력 경로가 사용자 요구와 다름. 공유 기준 없이 생성된 디자인/분리를 좌표 일치만으로 복구했다고 입증할 수 없음 |
| 미해결·다음 판정 | 입력 경로 수정은 E에서 별도 비교. 원화 우선·원형 보충을 D에 소급 적용한 것으로 기록하지 않음 |

<a id="experiment-e"></a>
### 5.6 실험 E — SourceFirst01: 실행·관찰·실패의 누적 기록

| 기록 항목 | 기록 |
|---|---|
| ID·상태·날짜·비교 | M03/E, 2026-09-10, 부분 관찰·요구 메커니즘 불일치. 원화 / source 3D 본 / 2D 파츠 비교 |
| 목표·이번 차이 | D의 독립 생성 atlas 대신 같은 완성 정면 원화에서 파츠를 분리해 기존 본 동작 전달 |
| 입력·재현 | SourceFront.png 1024×1536, 컨셉 시트 참조 후 생성한 완성 정면 1장에 사용자 승인. SourceFirstReview.unity, 기존 Humanoid Base Layer.Locomotion. 기준 speed=0·phase=0의 idle이며 FBX T-pose와 구분. PPU=380 |
| 절차·수학·구현 | 원화 배경 분리 → source-first.json 저작 → 17개 이미지 mesh → reference idle 상대 FK·단색 joint·shared seam. 상세는 아래와 [SourceFirst01 README](../../Assets/Tests/CharacterPipelines/SourceFirst01/README.md) |
| 관찰·결과·증거 | 기준/걷기/idle 캡처와 정점 연속성 값 확보. 이전 사용자 관찰은 “팔다리는 정상, 발만 문제로 보임”. 이는 3D 스킨 바인딩 또는 전체 아트 승인 아님 |
| 실패·원인 | 편집 Sprite geometry, 직렬화되지 않는 원화 패널, 넓은 골반 절단선의 틈은 아래 기록. 최신 구조적 차이는 원본 3D 표면/skin weights 제거 후 별도 2D 변형을 사용한 것 |
| 미해결·다음 판정 | E의 발 각도/길이 보정을 계속하는 후속 중단. 요구한 3D 본/몸체 → 이미지 연결은 F에서 분리 판정. E의 기존 원화·17개 mesh·비교 증거 보존 |

**입력과 실제 파츠.** SourceFront.png는 파츠별 생성물이 아닙니다. 생성기가 실제 alpha 대신 RGB 체커 배경을 반환해 외곽에 연결된 neutral mask만 alpha로 분리한 SourceCutout.png를 사용했습니다. 캐릭터 RGB를 다시 칠하거나 평균화하지 않았습니다. source-first.json은 같은 원화 좌상단 픽셀 좌표의 15관절, 17파츠 polygon, 공통 PPU380·원점·순서, 10개 단색 원형 관절, 12개 경계 band를 기록합니다. 좌상단→좌하단 좌표 변환은 builder 한 곳이 담당하고 screenLeft가 해부학적 Right라는 대응을 확인했습니다.

파츠는 본 17개나 PNG 17장 복제본이 아니라 **한 texture의 서로 다른 UV/geometry를 읽는 별도 MeshRenderer 17개**입니다. foreground 440,905픽셀은 한 파츠에만 배정됐고 메시 총 정점은 8,516개입니다. UV는 원화 좌표를 사용하며 부위별 크기 조절이 없습니다. [실제 메시 구역을 독립 배치한 렌더](evidence/source-first-20260910/image-parts.png). 이는 숨은 면/겹침 여유까지 완성한 제작용 파츠라는 뜻은 아닙니다.

**경계 수학.** 절단선의 부호 있는 거리 d, 반폭 h에 대해 t=smoothstep(0,1,0.5−d/(2h)), 출력은 (1−t)Tfirst(p)+tTsecond(p)입니다. 같은 source 좌표점은 양쪽 파츠에서 같은 weight를 사용하며 무릎보호대 overlay에도 같은 변환을 적용합니다. 여러 seam 교점은 영향 그래프 weight를 정규화하고 Initialize에 캐시합니다. 색 혼합이 아니라 정점 위치의 연결입니다. 단색 원형 joint는 평면 메시이며 3D sphere나 새 관절 이미지가 아닙니다. 무늬·선이 있는 무릎보호대는 원본을 유지합니다.

| 발견한 실패 | 확인한 원인·처리 | 남긴 증거/경계 |
|---|---|---|
| Sprite가 사각형으로 남음 | 편집 시점 Sprite.OverrideGeometry 호출 거부. 표시가 실제로 사용하는 Mesh를 직접 저장하도록 변경 | [Unity issue 1139166][S16]. runtime 호출 시점 우회로 처리하지 않음. 참조 없는 중간 Sprite 17개는 최종 파츠가 아니며 README에는 정리 대상으로 기록 |
| Play 원화 패널이 흰 사각형 | MaterialPropertyBlock이 씬에 직렬화되지 않음. 참조 재질 BaseMap에 texture를 저장 | 원화 비교 패널의 참조 보존 문제 |
| 골반 절단선이 벌어짐 | 넓은 절단선을 독립 변환한 결과. 양쪽에 같은 source-coordinate weight를 쓰는 12개 seam band로 연결 | [수정 전 캡처](evidence/source-first-20260910/before-seam-fix.png). 큰 틈을 원으로 덮지 않음 |
| 요구한 3D 몸체 연결과 다름 | Builder가 시험 clone Renderer/SkinnedMeshRenderer·MeshFilter를 제거. source SkinnedMeshRenderer 0개이며 이미지 정점은 별도 2D 관절/seam으로 움직임 | 원본 3D 표면·깊이·skin weights를 따라가는 구현이 아님. 실제 Player/프리팹·A~D·게임씬 보존 |

**실행 관찰과 증거.** Unity 6000.5.9f1 Play에서 기준 1회+걷기 16위상+idle 1회 캡처했고, 경계 계산 변경 뒤 같은 비교를 한 번 추가했습니다. 최종 기준 원화 정점의 최대 world 위치 오차는 0, walk 0.25위상 공유 절단선 정점 340쌍의 최대 틈은 0입니다. [기술 값](evidence/source-first-20260910/technical-check.txt), [정지 비교](evidence/source-first-20260910/reference.png), [움직임 비교 APNG](evidence/source-first-20260910/walk.png). 좌=원화, 중앙=source 3D 본, 우=2D 파츠입니다. 이 값과 캡처는 전 clip의 자연스러움·미술 합격·요구 메커니즘 충족을 의미하지 않습니다.

**미검증.** 원화의 관절/분리 메타데이터 저작은 여전히 필요합니다. 임의 PNG 자동 rig 완성이 아닙니다. 정면 1뷰·걷기/idle 외 8방향, 팔 교차·어깨를 넘는 팔, 등/발바닥/가방 숨은 면, 교차 장비, 임의 clip, 모드 로더, 실제 환경 조명, 대량 캐릭터 GPU/CPU Profile, 빌드는 미검증입니다. 기존 전체화면/캐릭터 픽셀 렌더러·조명 알고리즘을 이 실험에서 변경하지 않았습니다.

<a id="experiment-e-foot"></a>
### 5.7 E-foot — 제한 시험과 보류한 연구

| 기록 항목 | 기록 |
|---|---|
| ID·상태·날짜·비교 | M03/E-foot, 2026-09-10, 부분 관찰·후속 중단. 기존 E 부츠와 제한 변경 비교 |
| 목표·이번 차이 | 발 회전 해석/발목 혼합을 구분하고, 깊이 회전을 버리던 부츠 표시의 제한 시험 |
| 입력·재현 | E의 동일 원화·17개 mesh·걷기/idle. 부츠 두 곳만 RigidScreenRoll/발목→발가락 방향/Plane을 비교 |
| 절차·수학·구현 | 아래 twist·투영축 식. 최종 시험 씬/manifest의 두 boot 모드만 기존 Plane으로 남음 |
| 관찰·결과·증거 | 방향 벡터 시험은 옆 꺾임 증가로 미채택. Plane의 두 위상 길이 비율과 LocalOnly 캡처 기록은 아래에 보존 |
| 실패·원인 | 이전 RigidScreenRoll은 깊이 회전을 버리고 길이 유지. band 혼합과 단일 정면 그림 해석의 기여는 완전히 분리하지 못함 |
| 미해결·다음 판정 | 요구한 3D 표면 바인딩 해결/시각 승인 아님. 추가 발 수치 보정은 중단하고 M04/F에서 구조 차이 판정 |

**E-foot 초기 관찰·가설.** 종아리 Segment는 무릎→발목 투영 벡터를 따릅니다. 이전 부츠 RigidScreenRoll은 Foot의 기준 대비 월드 회전에서 화면 법선 twist만 읽었습니다. Δq=qNow·inverse(qReference), θ=2 atan2(dot(Δq.xyz,viewForward),Δq.w)입니다. 발목 위치는 공유하지만 발 각도는 종아리와 독립이고 y1282±45px 발목 band에서 둘을 혼합하므로 부츠 위/아래가 다르게 보일 수 있습니다. 카메라 right≈−X, up≈+Y, forward≈−Z는 right×up=forward를 만족해 단순 부호 반전이 필요하다는 증거는 없었습니다. 단일 정면 그림의 회전 해석과 band 변형의 영향은 당시 분리되지 않았습니다.

**E-foot 제한 변경과 결과.** 종아리는 투영 길이를 반영하지만 RigidScreenRoll은 깊이 회전을 버리고 길이를 유지했습니다. 발목→발가락의 2D 방향 시험은 정면 투영축이 짧아지고 회전하면서 옆 꺾임을 키워 채택하지 않았습니다. 기존 Plane 모드로 두 부츠만 바꾼 시험에서는 x=P(ΔR·camera.right), y=P(ΔR·camera.up)이며 가로축 굽힘 때 y가 cosθ만큼 줄어듭니다. Play 걷기 0.25위상 오른발 세로 투영 길이 0.247, 0.75위상 왼발 0.116을 확인했습니다. 그림 평면 축의 길이 비율이며 픽셀 행 수 직접 측정은 아닙니다.

비교 위치는 LocalOnly/SourceFirstFootReview_20260910/, Plane 기준+걷기16+idle은 LocalOnly/SourceFirstReview_20260910/capture03/입니다. 원본 그림/17개 mesh는 바꾸지 않았고 시험 씬·manifest의 두 boot 모드만 Plane으로 남은 부분 시험입니다. 재생은 중단했으며 요구한 3D 바인딩 해결이나 시각 승인으로 채택하지 않습니다.

| 보류한 연구 후보 | 근거와 당시 확인하려던 것 | 현재 판단 |
|---|---|---|
| E-foot-1 회전/혼합 비교 | [Quaternion swing/twist 수학][S17]. shin각·foot twist각·상대각을 같은 문제 프레임에서 기록해 부츠 전체 회전과 band만의 꺾임 구분 | 수학 설명은 그림의 올바른 발 방향을 보증하지 않음. 최신 3D 바인딩 요구에 따라 추가 시험 중단 |
| E-foot-2 발 표시축 비교 | [Meta 부위별 projection plane][S04]. 발목·발끝/발바닥 기준축과 정면 foot plane, 투영 길이 0 조건 구분 | 추가 appearance 보정의 진행 계획으로 취급하지 않음 |
| E-foot-3 방향별 소수 원화 | [Project Terra][S01]·[Sean][S02]의 시점별 그림 교체. 변환 오류와 원화에 없는 면 정보 구분 후 발 옆면/발바닥 보충 후보 | 별도 아트 데이터 선택이며 미실행 |

발 접지·미끄러짐은 발 그림의 회전 해석과 다른 문제입니다. [Unity Two Bone IK][S18]는 tip 목표 위치·회전을 제어하지만 현재 2D 발 해석을 자동으로 해결하지 않습니다. 미끄러짐 증거 없이 IK 추가를 해결책으로 삼지 않는다는 당시 판단을 보존하며, 이 후보 목록은 새 구현 승인이나 F보다 먼저 할 작업이 아닙니다.

<a id="m04"></a>
## 6. M04 — 실제 3D 스킨에 이미지 바인딩

### 6.1 원리·수학·자료

원화와 적합한 3D 몸체·스켈레톤의 정상 자세와 변형이 기준이고, 이미지가 그 몸체의 기준 표면·bind pose·스킨웨이트에 연결되어 같은 3D 변형을 따르는 방법입니다. 기존 몸체 재사용 또는 새 몸체 저작은 적합성 판단이며 기법의 필수 조건이 아닙니다. 몸체를 투명하게 표시하는 것과 몸체의 표면/리깅 데이터를 제거하는 것은 다릅니다.

가중 스킨 개념식은 v(t)=Σᵢ wᵢ Mᵢ(t) inverse(Mᵢ(bind)) v(bind)입니다. wᵢ는 해당 정점의 bone weight, Mᵢ(bind)는 기준 자세의 bone 변환, Mᵢ(t)는 현재 bone 변환입니다. 실제 Unity 구현은 mesh·renderer/root·bone 공간을 일치시켜야 합니다. [Unity Mesh.bindposes][S08]는 각 bindpose가 같은 인덱스 bone의 기준 자세 역변환임을 설명합니다. 이 식은 이미지 정점을 기존 표면 어디에 둘지, 기존 weight를 어떻게 대응시킬지까지 자동 결정하지 않습니다.

[Unity SpriteSkin][S07]은 rig/weight가 설정된 sprite mesh를 bone Transform으로 변형하는 기능의 근거입니다. SpriteSkin을 붙이거나 bone 이름을 같게 만드는 것만으로 기존 3D 몸체의 표면·깊이·스킨 바인딩이 완성되는 것은 아닙니다. 공개 게임의 동일 구현을 확보했거나 특정 도구와 자동 호환됨을 확인한 단계가 아닙니다.

### 6.2 구현 절차·판정 범위

1. 원화 비율·관절과 rig의 적합성, skeleton·bind pose·skin weights·표면 좌표를 먼저 확인하고 선택/교체 근거를 남깁니다. 좌우/축과 기본 자세·한 관절 시험이 전체 연결보다 먼저입니다.
2. 이미지 한 부위를 기준 표면/스킨에 연결하고, 같은 3D 변형에서 이미지가 이동하도록 합니다.
3. 동일 clip의 한 관절에서 기준 3D와 이미지의 앞뒤 굽힘·투영 길이·가림이 대응하는지 관찰합니다.
4. 자세가 잘못되면 본/리깅, 몸체가 정상인데 이미지가 잘못되면 부착 기준·bind pose·weight를 구분합니다.

이미지 접합을 성립시키기 전의 전체 캐릭터 재제작·원화 보정은 판정에 필요하지 않습니다. 새 3D 형상이 필요하면 depth map/입체 proxy를 별도 저작 데이터로 정의해야 하며, 정면 그림에 없는 면이 이 과정에서 자동 복원된다고 가정하지 않습니다.

<a id="experiment-f"></a>
### 6.3 실험 F — 기존 3D 스킨과 이미지 연결

| 기록 항목 | 기록 |
|---|---|
| ID·상태·날짜·비교 | M04/F, 2026-09-11, **출력 실패·구현 중단**. 기존 코드/로그/캡처 회수이며 이번 문서 작업의 새 Play 실행 없음 |
| 목표·이번 차이 | E의 별도 2D 관절/화면 각도 해석 대신 기존 3D 몸체·bind pose·스킨웨이트를 이미지 변형의 기준으로 사용 |
| 입력·재현 | `NativeSkin01/NativeArtSkinReview.unity`。`PersistentGameplayShell/Player/CharacterSilhouettePlayerVisual`의 복제 시험체, `Chibi_KenneyRig_review01.fbx`의 본58개; E의 `SourceCutout.png`·이미지17 mesh·PPU380. `Base Layer.Locomotion`, idle 기준0·walk16위상·idle. 카메라 orthographic 2.15, yaw180°, 1296×768 |
| 절차·수학·구현 | `Assets/Editor/NativeArtSurfaceBinder.cs`, `NativeArtSkinReviewBuilder.cs`, `Assets/Scripts/CharacterPresentation/NativeArtSkinReview.cs`. 저작 시 TPS 랜드마크→기존 몸체 투영 삼각형→barycentric 상위4 weight 전달, native SkinnedMeshRenderer 변형. 이는 프로젝트 자체 연결 가설이며 외부 완성 파이프라인을 그대로 이식한 것이 아님 |
| 관찰·결과·증거 | 저장 로그의 기준 정점 오차 2.872919→1.2701E-06, 출력 root scale1. 그러나 [native 출력 실패](evidence/native-skin-20260911/force-native.png)에서 손/머리 일부와 축소된 몸체가 분리됨. [CPU BakeMesh 진단](evidence/native-skin-20260911/baked-diagnostic.png)은 다른 출력을 보이나 정상 연결도 아님. [수정 후 값](evidence/native-skin-20260911/binding-corrected.txt). 낮은 수치 오차와 실제 렌더 성공은 일치하지 않았음 |
| 실패·원인 | 확인: source의 scale을 다시 적용하던 좌표 평가·시험 renderer scale 경계를 수정했고 기준 오차는 감소. **미확정:** native/CPU 출력 차이의 원인. **입력 적합성 위험:** 원화와 기존 Chibi의 머리·골반·다리 비율/관절 위치가 다름. 이 차이를 모든 출력 실패의 단일 원인으로 확정하지 않음 |
| 미해결·다음 판정 | F 출력은 불합격, M04 일반 기법의 불가능성은 판정 불가. CPU 진단을 대체 렌더로 채택하지 않음. 기존 rig 고수/새 rig 제작 모두 [D01](#current-decision)의 후보 비교 후 결정. 최신 요청에 따라 구현 중단 |

원래 비교 프레임과 진단은 로컬 `LocalOnly/NativeArtSkinReview_20260911/`에 보존했고 위 대표 증거만 문서와 함께 보관합니다. 관련 구현·시험 에셋은 아직 미커밋이며, 이 문서 체크포인트는 캐릭터 구현 체크포인트가 아닙니다.

<a id="m05"></a>
## 7. M05 — depth/height로 입체 정보 보충

**원리·자료.** Smack Studio가 설명한 흐름은 부위별 2D 그림 → 3D bone 연결 → 자동 생성·수정 가능한 depth map → UE4 compute shader 재투영입니다. 외부 프로젝트 출력은 sprite sheet입니다. [공식 기술·배포 설명][S05] 별도 제작 과정은 그림에서 생성한 입체 형태를 height map 칠하기·다듬기로 보정한다고 설명합니다. “부위 그림을 한 번 제작한다”는 과정에 깊이·형태 저작이 포함됩니다. [공식 제작 과정, 2021-08-20][S06]

**수학과 구현 절차.** 개념적으로 그림 좌표에 깊이/높이를 붙여 공간 위치를 정하고, 3D 자세 변화 후 그 위치를 다시 화면에 투영하는 경로입니다. 이는 공개 설명의 해석이며 비공개 depth 생성·구멍 채움·재투영 알고리즘의 정확한 식을 확보한 것은 아닙니다. 후보 절차는 부위 그림/rig → depth 생성 → 필요한 두께·형태 보정 → 회전 재투영 비교입니다. 단순 평면 휘기나 조명용 normal map과 구분합니다.

**실험·결과·실패.** 상태는 조사만입니다. 프로젝트에서 Smack 방식의 깊이 생성/compute 재투영 실험은 수행하지 않았고 실행 결과·실패 증거도 없습니다. 공개 Unity runtime SDK와 FBX Humanoid clip 직접 연결 지원은 확인하지 못했습니다.

**미해결·다음 판정.** 정면 입력에 없는 두께/옆면 저작량, 기존 skeleton 연결, 가림/실루엣 유지가 연구 대상입니다. F의 실제 3D 바인딩 결과와 구분해 필요성을 판단합니다. 개발사는 제작물 외부 사용·수익화 허용과 특허를 표기하지만, 이번 조사에서 특허 청구범위·법적 적용을 판단하지 않았습니다. 제작물 사용 허용과 엔진 코드/알고리즘 구현 권리는 별개이며 원본 코드를 복사하지 않았습니다.

<a id="m06"></a>
## 8. M06 — normal map을 이용한 조명

**원리·수학·자료.** normal map은 표면 법선에 따른 광원 반응을 바꿉니다. [Unity Normal map][S19] 여기서 법선은 표면 방향이고, M05의 공간 위치/두께 정보와 다릅니다. 조명 모델에 입력할 normal을 바꾸는 것만으로 mesh 정점 위치나 그림의 옆면·실루엣·원근 단축이 생기지 않습니다. 특정 조명 방정식이나 프로젝트 구현 수치는 이번 문서에서 검증하지 않았습니다.

**구현 절차.** 기존 그림/표면에 대응하는 normal 데이터를 마련하고 렌더러·조명이 이를 읽게 한 뒤 광원 변화의 반응을 관찰하는 경로입니다. 실제 몸체의 깊이와 스킨 변형 문제를 해결하는 절차는 [M04](#m04)·[M05](#m05)에 남습니다.

**실험·결과·실패.** 상태는 기능 구분 조사만입니다. 독립 normal-only 조명 실험이나 합격/실패 결과는 이 연구 기록에 없습니다. A/E가 이 조명 방식을 검증했다고 해석하지 않습니다.

**미해결·다음 판정.** 어떤 그림/표면에서 조명 반응이 필요한지, 실제 사용 렌더 경로가 무엇인지가 결정되었을 때 범위를 정합니다. 깊이/스킨 바인딩의 대체 후보로 채택하지 않습니다.

<a id="m07"></a>
## 9. M07 — 3D motion을 해석한 2D rig/mesh 변형

### 9.1 원리·수학·자료

- **Meta Animated Drawings.** 원화 2D mesh를 ARAP 방식으로 변형하는 Python 공개 구현입니다. MIT 라이선스, 2025-09-03 보관 처리로 기록되어 있으며 Unity 통합 패키지는 아닙니다. [공식 저장소][S03] BVH 3D joint 위치를 평면에 투영한 뒤 두 joint 벡터로 그림 bone 방향을 정하고, 몸통/팔/다리에 다른 projection plane을 선택할 수 있습니다. body-part group 깊이는 가림 순서에 사용합니다. [공식 설정][S04]
- **Unity SpriteSkin.** Skinning Editor에서 만든 rig/weight와 GameObject Transform으로 sprite mesh를 변형합니다. bone 참조가 필요하며 자동 재연결은 이름·계층 대응에 의존합니다. 자료 대상은 2D Animation 13.0이며 프로젝트 설치 버전·렌더러와의 자동 호환을 뜻하지 않습니다. [공식 문서][S07]
- **Spine.** vertex별 bone weight, 자기 겹침의 bone 순서 기반 triangle order, 여러 mesh weight를 맞추는 Weld를 제공합니다. 그림 분할만으로 접합/가림이 해결되지 않는다는 기능 근거입니다. [Weights][S09]
- **Godot.** Skeleton2D/Bone2D, rest pose, polygon weight를 설정합니다. 내부 삼각형 연결과 변형 영역의 vertex 구성이 휘어지는 결과에 영향을 줍니다. [2D skeletons][S11] Unity에서도 관절 topology/weight를 검토할 이유지만, 이 문서는 엔진 기능 설명이지 3D skeleton으로 2D 그림을 구동한 게임 사례가 아닙니다.

관절 투영은 pᵢ=P(Jᵢ), 그림 bone 방향은 pchild−pparent로 표현할 수 있습니다. 이 개념과 E의 §5.2 상대 FK는 관련이 있지만 ARAP, SpriteSkin, E의 seam 계산은 같은 알고리즘이 아닙니다. ARAP의 내부 에너지식/solver는 이번 기록에서 코드 전수 검증하지 않았습니다. 가중 mesh의 bind pose 원리는 [M04](#m04)를 참조하며, 실제 계산 공간과 원화 기준 자세의 연결이 따로 필요합니다.

### 9.2 구현 절차·장비 적용

원화의 의미에 맞게 joint/mesh/rest pose를 정하고 3D motion을 2D 목표 관절로 해석한 뒤 weight 또는 ARAP로 변형합니다. 관절 주변 topology·가림 순서·원화 축을 함께 확인합니다. Meta는 목/머리 원화 배치가 사람 skeleton과 다를 때 얼굴이 뒤집힐 수 있다고 설명합니다. bone 회전 복사만으로 대응이 성립하지 않는 이유이며, 정면 그림 유지의 기술 근거가 픽셀아트·탑다운 동작의 시각 합격을 보장하지는 않습니다.

복잡한 가방은 단일 그림을 한 bone에 붙이는 것보다 많은 연결을 요구할 수 있습니다. [Spine Mix-and-match][S10]의 예제는 가방 **4개 이미지·7개 bone**, 어깨/가방 쪽 끈 연결점, 본체/덮개 weight와 제어 bone으로 원근감을 흉내 냅니다. 장비별 skin·bone·constraint를 묶는 2D 예제이며 이 수량은 프로젝트 필수값이 아닙니다. 기존 Humanoid clip 자동 입력을 입증하지 않고 Spine 설치·도입·구매도 결정하지 않습니다.

적용 제안은 단단한 본체·앞뒤 끈·덮개·장식을 움직임/가림 의미대로 분리하거나 mesh 영역·weight를 지정하는 것입니다. 가방 본체 기준점과 어깨/몸통 끈 anchor를 구분하고 기존 관절·표시 제어점·변형 영역·순서를 기록하면 clip과 장비 그림을 분리할 수 있습니다.

### 9.3 실험·실패·미해결·다음 판정

상태는 조사만입니다. Meta ARAP/Unity SpriteSkin/Spine/Godot를 사용한 독립 프로젝트 실험이나 실제 실패 결과는 없습니다. E는 별도 상대 FK와 seam 변형을 사용한 [M03 실험](#experiment-e)이며, 위 도구의 구현을 완료한 것으로 세지 않습니다.

미해결은 원화 관절의 의미, projection plane 선택, 변형 topology와 가림, 기존 Humanoid 연결 범위입니다. 이 방법은 2D에 맞춘 동작 해석이며 모든 3D 자세의 정확한 입체 투영이 아닙니다. 현재 요구인 실제 3D 몸체 표면 바인딩을 대신 채택하지 않고 F의 요구 메커니즘 판정과 구분해 보존합니다.

<a id="m08"></a>
## 10. M08 — 다중 시점 impostor

**원리·수학·자료.** 여러 방향에서 bake한 이미지·normal/depth를 사용해 관찰 방향에 맞는 대체 표현을 만드는 방법입니다. [Amplify Impostors Manual][S20]은 여러 방향 bake, normal/depth, parallax와 depth writing을 설명합니다. 문서상 animated skinned mesh 지원이 아니며, 임의 새 애니메이션에 즉시 반응하는 캐릭터 기본 해법으로 채택하지 않았습니다.

**구현 절차.** 원본 대상과 bake 방향을 정하고 시점별 데이터를 생성한 뒤 관찰 방향·깊이 정보를 사용하는 렌더를 구성합니다. 실제 시점 선택/보간·parallax 식과 animated skinned mesh의 별도 확장 구현은 이번 조사에서 확보하지 않았습니다. M02의 시간별 동작 프레임 bake와 M08의 시점별 대체 표현은 축이 다릅니다.

**실험·결과·실패.** 상태는 조사만입니다. 프로젝트 bake/재생 실험, 품질·성능 결과, 실패 캡처는 없습니다. 일반 3D 캐릭터가 이 기법으로 새 clip을 자동 재생할 수 있다고 주장하지 않습니다.

**미해결·다음 판정.** 캐릭터 애니메이션의 변화와 bake 재사용 범위가 연구 대상입니다. 원거리 대체 표현의 필요성과 동작 지원 근거가 먼저 확보되어야 하며 현재 F의 3D 이미지 바인딩 결과로 간주하지 않습니다.

<a id="shared-art"></a>
## 11. 공통 원화 제작 근거와 출처 목록

### 11.1 원화 우선 분리·숨은 영역·원형 관절

**[사용자 확정]** 정상 정면 원화를 먼저 만들고 같은 원화에서 파츠를 분리하며 연결부에 색이 일치하는 원형 보충을 사용합니다. 원 중심은 공유 joint, 크기·팔레트는 원화 연결부 데이터가 담당합니다. 단색 연결부에 유효한 기법과 무늬/재질 경계/3D 방향 대응의 문제를 구분합니다. 실패한 C/D에 이 방식을 적용했다고 소급 기록하지 않으며 E의 실제 적용·한계는 [실험 E](#experiment-e)에 있습니다.

| 자료 | 확인한 설명 | 적용 경계 |
|---|---|---|
| [Spine — How to cut your assets for animation][S12], 2025-03-06 | 숨은 부분까지 그리기, 겹치는 관절 끝을 원형에 가깝게 만들기, 앞뒤 레이어 분리 | 잘못된 관절/좌표 대응을 원으로 덮는 근거가 아님 |
| [Toon Boom — Character building][S13] | 기준 캐릭터 그림을 준비한 다음 부위별 레이어 제작 | 검색 본문 확인; 직접 페이지 fetch 실패라는 기존 확인 한계 보존 |
| [Cartoon Animator — Joint Masks][S14] | 원형 mask 내부에서 연결 부위 앞뒤 순서 보정 | 단색 원을 그려 빈 영역을 채우는 geometry 기능과 다름 |
| [TET — Preparing for Rigging][S15], 2023-02-22 | 완성 몸 shape를 관절에서 분할하고 같은 채움색/선색의 원을 복제해 위·아래 파츠 끝에 Union. 두 원 중심 일치, 접합부 명암을 줄여 회전 시 새 선 방지 | 벡터 반쪽 제작·대칭 복제의 수작업 예제. PNG 자동 분할/Unity 3D bone 도구가 아님. Unity 절차 원형 보충은 별도 구현 선택 |

### 11.2 출처 해석과 공통 목록

외부 사실, 프로젝트 구현, 적용 제안을 구분합니다. 아래는 기존 조사에서 사용한 자료의 통합 목록이며 이번 재구성에서 새로 전부 열어 검증했다는 뜻이 아닙니다. 기존 확인 기록은 2026-09-10이고 게시일 없는 자료의 날짜는 추정하지 않았습니다.

EthrA는 시각적으로 관련 있지만 확인한 공식 홈페이지에서 기술 세부를 입증하지 못했습니다. 제3자 추측이나 “EthrA처럼”이라는 코드 제목을 제작사 구현 증거로 사용하지 않습니다. 공개 근거 미확인은 다른 사람이 해당 방법을 사용하지 않는다는 뜻이 아닙니다.

| ID | 원문·종류 | 이 문서의 사용 위치 |
|---|---|---|
| S01 | [Radical Fish Games — Project Terra Progress and Gamescom 2023][S01], 제작사 기록, 2023-08-12 | M03, E-foot |
| S02 | [Sean — Bone Sprite Animation System][S02], 구현자 기록, 2024-05-03 | M03, E-foot |
| S03 | [Meta — Animated Drawings][S03], 공개 코드 | M07 |
| S04 | [Meta — Configuration Files][S04], 공식 설정 | M03, M07, E-foot |
| S05 | [Smack Studio — Press][S05], 제작사 설명 | M05 |
| S06 | [Smack Studio — Animating 3D without using 3D Models][S06], 제작 과정, 2021-08-20 | M05 |
| S07 | [Unity — Sprite Skin, 2D Animation 13.0][S07], 기능 문서 | M04, M07 |
| S08 | [Unity — Mesh.bindposes][S08], API 문서 | M01, M03, M04 |
| S09 | [Esoteric Software — Weights][S09], 기능 문서 | M07 |
| S10 | [Esoteric Software — Mix-and-match][S10], 공식 예제 | M07 |
| S11 | [Godot — 2D skeletons][S11], 기능 튜토리얼 | M07 |
| S12 | [Esoteric Software — How to cut your assets for animation][S12], 제작 가이드, 2025-03-06 | 공통 원화 제작 |
| S13 | [Toon Boom — Character building][S13], 제작 가이드 | 공통 원화 제작 |
| S14 | [Reallusion — Using Joint Masks][S14], 기능 문서 | 공통 원화 제작 |
| S15 | [TET — Preparing for Rigging][S15], 제작 사례, 2023-02-22 | 공통 원화 제작 |
| S16 | [Unity — issue 1139166][S16], 공식 issue | E geometry 실패 |
| S17 | [Marc B. Reynolds — Quaternion swing/twist decomposition][S17], 수학 설명 | E-foot 보류 후보 |
| S18 | [Unity — Two Bone IK Constraint, Animation Rigging 1.3][S18], 기능 문서 | E-foot와 접지 구분 |
| S19 | [Unity — Normal map][S19], 기능 문서 | M06 |
| S20 | [Amplify — Impostors Manual][S20], 제품 문서 | M08 |
| S21 | [Blender — Armature Modifier][S21], 공식 기능 문서, 조회 2026-09-11 | P1. 준비된 mesh/rig의 변형 기능 근거이며 원화 자동 입체 복원 근거가 아님 |
| S22 | [Unity 6.0 — Retarget Humanoid animations][S22], 공식 기능 문서, 조회 2026-09-11 | P1. Avatar를 통한 동작 재사용이며 파츠 저작/스키닝을 대체하지 않음 |

[S01]: https://www.radicalfishgames.com/?p=7410
[S02]: https://seanrich92.github.io/tools/bone-sprite-animation-system
[S03]: https://github.com/facebookresearch/AnimatedDrawings
[S04]: https://github.com/facebookresearch/AnimatedDrawings/blob/main/examples/config/README.md
[S05]: https://smackstudio.com/press/
[S06]: https://smackstudio.com/here-is-our-technique-for-animating-3d-without-using-3d-models/
[S07]: https://docs.unity3d.com/Packages/com.unity.2d.animation@13.0/manual/SpriteSkin.html
[S08]: https://docs.unity3d.com/ScriptReference/Mesh-bindposes.html
[S09]: https://en.esotericsoftware.com/spine-weights
[S10]: https://en.esotericsoftware.com/spine-examples-mix-and-match
[S11]: https://docs.godotengine.org/en/stable/tutorials/animation/2d_skeletons.html
[S12]: https://us.esotericsoftware.com/blog/How-to-cut-your-assets-for-animation
[S13]: https://docs.toonboom.com/help/harmony-22/advanced/getting-started/character-building.html
[S14]: https://manual.reallusion.com/Cartoon-Animator/Content/Resources/ENU/03_Actor/Customing_Your_Actor_With_Actor_Composer/Using_Joint_Masks.htm
[S15]: https://www.animationandvideo.com/2023/02/preparing-for-rigging-my-character.html
[S16]: https://issuetracker.unity3d.com/issues/not-allowed-to-override-geometry-on-sprite-when-using-vector-graphics-api-on-waitforendofframe-and-awake
[S17]: https://marc-b-reynolds.github.io/quaternions/2022/01/31/QuatAxisFactor.html
[S18]: https://docs.unity.cn/Packages/com.unity.animation.rigging%401.3/manual/constraints/TwoBoneIKConstraint.html
[S19]: https://docs.unity3d.com/6000.1/Documentation/Manual/StandardShaderMaterialParameterNormalMap.html
[S20]: https://wiki.amplify.pt/index.php?title=Unity_Products%3AAmplify_Impostors%2FManual
[S21]: https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html
[S22]: https://docs.unity3d.com/6000.0/Documentation/Manual/Retargeting.html
