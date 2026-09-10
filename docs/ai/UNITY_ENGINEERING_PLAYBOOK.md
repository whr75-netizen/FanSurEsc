# Unity 엔지니어링 플레이북

이 문서는 Unity 코드·씬·프리팹·런타임 상태를 실제로 변경하거나 관련 버그를 조사할 때만 사용한다. 매 작업마다 전체를 읽지 말고 `rg`로 관련 제목을 찾은 뒤 필요한 절만 읽는다. 핵심 승인 경계와 금지선은 루트 `AGENTS.md`가 우선한다.

## 1. 작업 유형별 절차

### 1.1 기능 구현

1. `CURRENT_STATE.md`에서 기존 기능과 재개방 조건을 확인한다.
2. 관련 코드·씬·프리팹과 진행 이력의 근거 절만 찾는다.
3. 현재 권위 소유자, 객체 수명, 입력 소유자와 직렬화 참조를 확인한다.
4. 사용자에게 요청 결과·메커니즘·보존·제외·검증의 5항목 작업 계약을 알린다.
5. 새 파이프라인·구조적 대안이면 §1.4의 설계 검토를 먼저 거친다. 그 밖에는 기존 공개 진입점과 책임 경계를 확장하는 최소 변경을 구현한다.
6. 컴파일·직렬화 참조와 변경 영향에 맞는 사용자 흐름을 검증한다.
7. `CURRENT_STATE.md`의 관련 행과 필요한 상세 증거를 갱신한다.

### 1.2 버그 수정

1. 원래 증상을 대표 절차로 한 번 재현하거나 재현 불가 이유를 기록한다.
2. 최초 오류, 직전 변경, 입력, 권위 원본, 수명주기와 직렬화 참조를 확인한다.
3. 원인 후보를 한 번에 하나씩 검증한다.
4. 깨진 원본 또는 계약에 필요한 가장 작은 수정만 적용한다.
5. 원래 재현 절차와 직접 영향 회귀를 각각 한 번 확인한다.
6. 간헐 오류라 반복이 필요하면 시작 전에 횟수와 판단 기준을 정한다.

UI·프리팹·캐시·생성 결과는 원인을 고친 뒤에만 재생성한다. 재생성, 복사본 교체, 강제 재적용, 광범위한 reimport, Console 삭제나 fallback 값으로 증상만 가리는 것은 수정이 아니다.

### 1.3 진단·검토·설계

- 진단은 원인과 증거까지만 제공한다. 수정 요청이 없으면 파일과 Unity 상태를 바꾸지 않는다.
- 검토는 현재 사실, 위험, 선택지와 권장을 분리한다.
- 설계 제안은 `[제안]`, 사용자 결정 전 항목은 `[미정]`으로 남긴다.
- 더 나은 일반론이 있어도 사용자 확정 메커니즘을 조용히 교체하지 않는다.

### 1.4 근거 기반 연구·설계·실행 파이프라인

새 제작 방식, 불확실한 변환/렌더/애니메이션 결합, 요구 메커니즘 불일치나 반복되는 구조적 실패에 적용한다. 기능마다 문서를 새로 만들거나 검증된 수치를 바꿀 때마다 웹 조사를 반복하지 않는다. 관련 연구 문서의 한 **현재 결정 카드**를 갱신하며, 공통 절차는 이 절만 소유한다.

#### 단계와 통과 조건

| 단계 | 남길 근거·산출물 | 다음 단계로 넘어가는 조건 |
|---|---|---|
| R0 요구·기준 확보 | 최신 요청, 승인된 입력, 목표 출력, 보존/제외, 현재 코드·실패 증거 위치 | 결과뿐 아니라 요구 메커니즘과 성공을 볼 실제 동작이 명확함 |
| R1 기존 방식 학습 | 해당 분야의 실제 제작 절차/공개 구현·공식 문서, 후보별 입력→저작→실행→출력·도구/버전·제약 | 핵심 연결이 출처로 확인되거나 공백이 명시됨. 영상의 외관만 보고 내부 구현을 단정하지 않음 |
| R2 선택·반례 검토 | 의미 있게 다른 후보(보통 2~3개), 선택/보류 이유, 입력 적합성, 가장 큰 가정, 예상 실패, 작은 시험 | 어떤 조건에서 후보가 탈락하는지와 무엇을 비교할지 실행 전에 정함. 미확인 연결은 최소 실험 대상으로만 허용 |
| R3 판별 실험 | 승인 범위의 격리된 최소 샘플, 고정 기준과 변경 변수, 실제 결과·실행 명령/진입점 | 요구의 핵심 메커니즘을 확인함. 컴파일·정지 일치·수학 오차만으로 동작/시각 성공을 선언하지 않음 |
| R4 범위 내 완성·전달 | 통과한 경로의 끝까지 연결, 요청된 출력/움직임, 관련 회귀, 남은 한계 | 사용자에게 시험할 수 있는 결과가 있음. 시각 판정은 사용자 확인으로 분리하며, 관련 상태·로컬 커밋은 기존 규칙 준수 |

R3에서 가정이 깨지면 R2로 돌아가 **실패를 설명하는 새 근거**로 결정을 수정한다. 단순 구현 버그는 §1.2로 좁혀 고치고 전면 재조사하지 않는다. 반복 결과가 같은데 수치·예외·새 rig·새 알고리즘만 추가하는 것은 진행으로 세지 않는다. 조사는 후보 선택을 바꿀 수 있는 질문에 집중하고, 관련 근거가 확보되거나 미확인 범위가 경계 지어지면 끝낸다. 모든 방법을 찾았다는 주장이나 끝없는 자료 수집은 금지한다.

#### 문제공간 탐색과 후보 전환

먼저 문제를 **입력 표현 / 변환·저작 / 동작·상태 / 출력 / 품질·비용 제약**으로 나누고, 알려진 사실·불확실성·필수 조건을 적는다. 기법 목록은 후보 파이프라인과 다르다. 함께 쓰는 스키닝·리타기팅·렌더링을 서로 대체 가능한 세 후보처럼 비교하지 않는다. 후보 하나는 입력부터 목표 출력까지 끊김 없는 연결이어야 한다.

필수 조건 위반은 먼저 탈락시킨다. 남은 후보는 외관의 호감이나 이미 쓴 작업량이 아니라 근거 수준·남은 불확실성·저작/유지/실행 비용으로 비교한다. 자료가 없다는 이유만으로 불가능이라 하거나, 수치를 임의로 점수화해 정답처럼 만들지 않는다. 다음 실험은 **적은 비용으로 후보 선택을 가장 크게 바꿀 수 있는 의문**을 판별하도록 고른다.

실험 전 `가설 → 맞으면 보일 것 / 틀리면 보일 것 → 고정 조건·변경 변수 → 결과별 다음 결정`을 기록한다. 상호작용이 의심되는 변수는 이유가 있는 작은 조합으로 시험할 수 있지만 여러 변수를 동시에 임의 조정하지 않는다. 결과는 **지지 / 기각 / 판정 불가**로 구분한다. 시험 장치·데이터 오류는 후보 기법의 기각 증거가 아니며, 유리한 결과만 남기지 않는다.

관측이 기존 가설을 반박하면 가설/후보 상태를 바꾸고, 판정 불가면 부족한 관측 하나를 보완한다. 실패한 가설을 유지한 채 후처리를 누적하지 않는다. 이때 연구의 진척은 새 코드나 문서의 양이 아니라 **해소된 의문·탈락/유지 근거·다음 선택이 명확해졌는가**로 판단한다.

#### 출처에서 배우는 범위와 독자 구현 경계

- **직접 근거:** 제작자가 공개한 전체 절차, 실행 가능한 소스/샘플. 공개되었다는 사실과 이번 환경에서 실행했다는 사실도 구분한다.
- **부분 근거:** 엔진 API, 스키닝·행렬 등 일반 원리. 한 단계만 입증하며 파이프라인 전체의 호환성을 입증하지 않는다.
- **관찰/가설:** 영상에서 보이는 현상, 공개되지 않은 내부 구현에 대한 해석, 프로젝트에 맞춘 새 연결. 가설임을 표기하고 판별 시험을 붙인다.
- 채택할 자료는 핵심 원문을 실제로 읽고 출처·해당 주장·환경 차이를 기록한다. 링크 개수만 채우거나 튜토리얼 이름만 빌리지 않는다. 외부 코드·에셋 도입에는 사용권과 지원 형식도 확인한다.
- 검증된 기본 기능을 우선 사용하되, 현재 재료와의 **적합성**을 우선한다. 재사용도 신규 제작도 자동 정답이 아니다. 대체할 단계, 기존 방식의 부족점, 추가 저작/런타임 비용을 설명한 뒤 독자 구현한다.

#### 설계 검토: 설명을 길게 쓰는 대신 계약을 확인

후보를 고른 작성과 반례 검토를 구분한다. 복잡한 첫 설계·반복 실패에는 가능한 경우 독립 검토자에게 최신 요구, 출처, 입력/출력 계약과 실패 증거를 제공하고, **탈락시킬 조건·누락된 단계·요구와 다른 대체**를 찾게 한다. 독립 검토가 없으면 작성자가 별도 검토하되 그 한계를 표시한다. AI 여러 명의 동의나 비공개 추론량은 검증이 아니다.

파이프라인의 각 경계에는 필요한 만큼 다음을 명시한다: 입력 파일/형식, 좌표계·단위·기준 자세, 데이터 소유자, 변환식과 변수의 공간, 출력과 다음 소비자, 없어지는 정보, 오류/재시작 조건. 수학은 기호를 나열하는 대신 좌우·축·scale·bind pose·시간 상태의 불변조건과 연결한다. 원화에 없는 깊이/숨은 면처럼 추가 데이터가 필요한 부분은 자동 해결된다고 가정하지 않는다.

원칙 검토 예: **상위 3D 동작도 틀림 → rig/clip**, **상위는 정상인데 이미지 변형만 틀림 → 바인딩/공간**, **변형은 정상이나 드러날 면이 없음 → 입력 표현/저작**, **색 단계가 시간에 따라 튐 → 조명 입력과 상태 유지 경계**를 각각 구분한다. 이 분류는 조사할 경계이지 진단 없이 확정할 원인이 아니다.

좌우/축 변환이 있는 작업은 전체 연결 전에 비대칭 기준점으로 이미지 좌우·해부학적 좌우·본 local축·카메라 축의 대응, 기본 자세 왕복, 한 관절의 앞뒤 굽힘을 확인한다. 좌우가 대칭인 정지 그림만 일치한다고 통과시키지 않는다. 실패하면 원본 좌표/바인딩 계약을 수정하며, 반대편 이미지를 끼우거나 화면 각도를 뒤집어 덮지 않는다. 애니메이션 모딩 요구는 제작에 쓰지 않은 clip을 추가했을 때 이미지 재제작·clip별 보정 없이 작동하는지도 판정 범위에 포함한다.

#### 하나의 연구 기록으로 누적·재개

연구는 기법별로 원리·수학·출처·적용 범위를 유지하고, 그 아래 결정과 실험 ID를 연결한다. 날짜는 부가 정보다. 실험 결과가 일반 기법 전체의 불가능성을 증명하지 않으며, 기존 실패를 지우거나 성공으로 덮어쓰지 않는다.

현재 결정 카드는 다음 내용을 짧게 유지한다. 이미 있는 값은 링크로 재사용한다.

1. **현재 단계·요청 범위:** 연구만/구현 포함, 최신 정정, 구현 허용 범위.
2. **질문·후보·결정:** 무엇을 판별하는지, 참조 기법과 선택/보류 이유, 결정을 뒤집을 조건.
3. **입출력 계약·가정:** 현재 재료와 맞는 부분/맞지 않는 부분, 추가 저작 데이터와 미확인 연결.
4. **실험:** 기준·변경 변수·성공/실패 관찰·최소 case와 실행 진입점. 횟수는 §8에 따름.
5. **실제 결과:** 실행한 것/못 한 것, 이미지·로그·코드 경로, 기술 판정과 사용자 판정을 분리.
6. **재개:** 마지막 성공 단계, 실패/차단, 다음 한 행동과 재개 조건. 구현 요청인데 조사에서 멈춘 경우 미완료임을 명시.

승인된 구현 범위와 안전한 다음 단계가 남아 있으면 조사·계획 작성만으로 턴을 끝내지 않는다. 사용자에게 매 단계 “계속할까요”를 묻지 않는다. 단, 범위/요구 변경·필수 선택·접근 차단·시각 승인 대기 또는 최신 중단 지시는 존중한다. 도구 끊김·컨텍스트 정리 뒤에는 현재 카드와 실제 파일/상태를 대조해 재개하며, 계획된 일을 실행된 일로 바꾸지 않는다.

#### 채택 근거와 적용 한계

이 절은 단일 회사의 완성 파이프라인을 복사한 것이 아니라 아래 방법의 공통점을 이 프로젝트의 작은 작업 단위로 줄인 운영 규칙이다. 캐릭터 기술의 선택은 별도 연구 근거로 결정한다.

- Michael Nygard, [Documenting Architecture Decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions), 2011-11-15: 결정의 맥락·상태·결과와 뒤집힌 이유를 보존. 이 프로젝트는 매번 새 ADR 파일 대신 기법 문서 내 결정 ID를 사용한다.
- NASA, [Systems Engineering Handbook §6.8 Decision Analysis](https://www.nasa.gov/reference/6-8-decision-analysis/): 기준과 대안을 먼저 비교하고, 불확실성·의사결정 규모에 맞춰 분석을 조정. 대형 프로젝트의 회의·승인 체계나 임의 가중 점수표는 도입하지 않는다.
- NIST/SEMATECH, [e-Handbook §5.1.4 — Steps of DOE](https://www.itl.nist.gov/div898/handbook/pri/section1/pri14.htm): 목적·변수·반응을 정한 순차 실험으로 다음 의문을 좁힌다. 이 프로젝트의 결정적 좌표/렌더 오류에 통계 반복 횟수를 기계적으로 적용하지 않는다.
- OpenAI, [Using PLANS.md for multi-hour problem solving](https://developers.openai.com/cookbook/articles/codex_exec_plans), 2025-10-07, 현재 archived: 재개 가능한 계획과 실행 가능한 작은 검증을 참고. 오래된 모델 권장이나 문서 전체 반복 읽기는 채택하지 않는다.
- OpenAI, [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices): 작업별 평가와 사람의 판단을 함께 사용. 전용 Evals 서비스나 반복 전체 게임 검사를 설치하라는 뜻은 아니다.

지침은 모델의 오류를 100% 차단하는 실행 잠금이 아니다. `validate_ai_docs.ps1`도 문서 구조/크기를 검사할 뿐 출처의 진실성·설계 타당성을 판정하지 않는다. 실제 절차 개선은 이후 작업에서 **선택 전 근거, 반례 검토, 관찰 결과, 재개 정보가 남는지**로 확인한다.

### 1.5 그래픽 파이프라인의 수학적 계약 — 구현 전 필수

**사용자 확정 요구(2026-09-11).** 기하학적으로 정의 가능한 문제를 눈대중·휴리스틱·부위별 임시 보정으로 해결하지 않는다. 생성형 입력의 의미/깊이 해석과, 확정된 기준점·메시·본을 변환하는 계산을 분리한다. 후자는 명시한 함수 합성과 자동 검사로 다룬다. 이 절은 검사 **명세**이며 검사 코드가 이미 존재하거나 통과했다는 뜻이 아니다.

§1.4에 해당하는 새 그래픽 파이프라인·변환 계약 변경/실패에 적용한다. 이미 검증된 변환은 명세·검사 근거를 재사용하며 단순 수치 조정마다 전부 다시 작성하지 않는다. 아래 canonical humanoid와 bone 검사는 인간형/골격 변환에 적용한다. 구름·UI 등 관련 없는 작업에 인간형 골격을 요구하지 않는다.

#### 표준 기술 우선과 설계 산출물

Blender/Unity/Shader의 표준 geometry·rigging·skinning·projection·UV·retargeting·rendering 기술 문서와 공개 구현을 먼저 조사한다. 각 변환에 근거 URL·관련 설명/API·사용 버전을 붙이고, 표준 기능이 해결하는 범위 밖의 연결은 미확인으로 표시한다. 외부 설명을 자기 추측으로 채우지 않는다. 기존에 해결된 계산을 새 알고리즘으로 다시 만들지 않으며, 자료로 해소되지 않는 선택은 명시적인 공백으로 남긴다.

구현 전에 **현재 문제의 수학 모델, 후보 알고리즘, 검증법**을 해당 연구 문서에 작성한다. 그래픽 파이프라인은 반드시 아래 형식으로 서술한다. 이는 명세 형식이지 모든 연산이 선형 행렬 하나라는 가정이 아니다.

`Input → Coordinate Space A → Transform T1 → Coordinate Space B → Transform T2 → … → Output`

예를 들어 이미지/UV 공간 → canonical 공간 → bone/mesh 기준 공간 → skinned world → view/clip/screen → render target → pixel grid로 나누고, 실제 경로에서 사용하는 모든 변환을 빠짐없이 기술한다. 깊이/weight/관절 표식은 추가 입력이다. 카메라 투영·가림·픽셀 양자화의 정보 손실과 시각/색 처리도 별도 단계로 명시한다.

| 좌표계별 필수 항목 | 반드시 명시할 내용 |
|---|---|
| origin | 기준 위치, 이미지 모서리/픽셀 중심 여부, bone pivot 등 |
| axis orientation | 각 축의 실제 방향, 해부학적 좌우와 화면 좌우의 대응 |
| handedness | 3D 좌/우수계, 2D이면 embedding basis/방향과 변환 관계 |
| units | px, texel, normalized UV, meter 또는 명시한 engine unit 등 |
| scale | 기준 길이·pixels per unit·단위 변환, 상위 scale 적용 위치 |
| rotation convention | quaternion/Euler/행렬, 각도 단위·축 순서·local/world·행/열벡터와 곱 순서 |
| parent coordinate system | 상위 공간 ID와 연결 변환; 최상위는 없음으로 명시 |

| Transform별 필수 항목 | 반드시 명시할 내용 |
|---|---|
| domain / codomain | 입력/출력 공간 ID, 값의 유효 범위, clip/가림 등 정의되지 않는 경우 |
| 공식 또는 알고리즘 | 공식 엔진 함수 또는 출처가 있는 알고리즘, 매개변수·연산 순서 |
| 허용 자유도 | translation/rotation/uniform scale, 관절 한계, 고정/저작/동작 변수의 구분 |
| invariant | 어떤 값·관계가 보존되어야 하는지와 검사 ID |
| numerical tolerance | 비교 metric·절대/상대 오차·단위·임계값·근거·실패 처리 |

좌표변환이 틀린 채 부위별 `localRotation`, `offset`, `scale`을 추가하지 않는다. 보정 필요 시 어느 변환에서 기대값과 실측값이 어긋났는지 재현해 원인을 입증하고 그 변환/정규화 계약을 수정한다. 정당한 저작 landmark·bind pose·단위 변환은 임시 보정과 구분하되 출처/측정법·한 번 적용되는 위치를 기록한다.

#### Canonical humanoid와 입력 적합성

3D 인간형 에셋을 바로 연결하지 않는다. 후보 공통의 **canonical humanoid representation**을 먼저 정의한다: 의미가 고정된 joint ID(LeftShoulder/RightShoulder 등), parent topology, 기준 좌표계, 기준 체형과 rest pose, 관절 자유도/한계, 측정 landmark, 허용 오차. canonical은 표준 Avatar와 대응할 프로젝트 기준이며 모든 그림에서 자동 추출되는 보편 체형이라고 가정하지 않는다.

각 모델의 **total height, head/body ratio, shoulder width, pelvis width, limb length, joint positions, rest pose, skeleton topology**를 같은 기준으로 측정한다. 머리·어깨·골반 등 어디 사이를 재는지도 고정한다. normalization/retargeting 전후 오차와 누락/중복 joint를 기록한다. 정상적인 변환이 불가능하거나 사전 임계값을 넘으면 후보에서 제외한다. 여기서 '폐기'는 실험 후보 제외이며 원본 에셋 삭제가 아니다.

2D 이미지는 단순 resize하지 않는다. 원본 aspect ratio와 target projection surface의 비율이 다르면 **uniform scale / crop / padding / UV projection** 중 정책과 그에 따른 영역 보존/손실을 명시한다. 요구에 명시되지 않은 비균일 scale은 금지한다. UV projection도 무왜곡을 자동 보장하지 않으므로 대응 오차를 검사한다. 3D 회전 때문에 화면에서 길이가 짧아지는 정상적인 투영과 저작 단계의 왜곡은 구분한다.

#### 자동 invariant 검사 명세

아래 전 항목에 검사 ID·입력 fixture·기대값·metric·tolerance·실패 출력을 연결한다. NaN/∞·누락된 참조는 먼저 실패 처리한다. 모든 후보에 동일한 측정 정의를 사용한다. **수치 임계값 미정은 통과가 아니며**, canonical과 target 해상도·float 정밀도·표준 API 오차 근거로 실험 전에 정한다. 결과를 본 뒤 합격시키려고 threshold를 늘리지 않는다. 순수 수치 오차와 허용 디자인 범위도 분리한다. 적용되지 않는 항목은 이유와 후보가 그 요구를 충족하는 다른 검사 근거를 명시한다.

| ID / invariant | 검사 기준 |
|---|---|
| G01 parent-child transform consistency | 선언한 곱 순서로 parent world × child local과 child world 비교. 원점·기저 벡터·샘플 정점을 검사하고 역변환은 가역 구간에서만 사용 |
| G02 left/right mapping consistency | 의미 ID·parent chain·대응표의 일대일성, 누락/중복/교차 매핑. 기준 자세의 비대칭 표식과 한쪽 관절만 구동한 결과까지 검사. 걷는 중 world X 부호로 좌우를 재판정하지 않음 |
| G03 rotation basis orthogonality | scale/반사를 분리한 회전 R에 대해 `RᵀR≈I`. 전체 skinning blend 행렬을 순수 회전처럼 검사하지 않음 |
| G04 determinant/sign | 순수 회전의 `det(R)≈+1`, 가역 변환의 비특이성, 선언된 좌표계 변환의 예상 부호와 비교. handedness 전환의 명시적 반사 -1을 회전 오류로 오판하지 않음 |
| G05 bone length consistency | 각 target bone의 자체 rest 길이와 동작 중 3D 길이 비교; 승인되지 않은 stretch 금지. 다른 source/target 체형의 길이가 같아야 한다고 검사하지 않음 |
| G06 rest-pose consistency | 기준 자세에서 스킨이 원래 mesh를 재현하고 bind 행렬·bone index·weight 대응이 맞음. weight 유효성/정규화, root scale의 중복 적용과 자세 왕복을 포함 |
| G07 joint constraint | 선언한 local 관절축·자유도/한계 안에서 동작. Euler 값의 단순 뺄셈으로 ±180° 경계를 오판하지 않으며 engine Avatar/constraint 정의를 사용 |
| G08 aspect-ratio preservation | 저작 단계의 원본 대비 가로/세로 비율과 선택한 crop/padding/UV 정책 검사. 카메라 투영 후 foreshortening은 이 검사와 분리 |
| G09 uniform-scale requirement | 선언한 동일 scale과 실제 변환 비교; 축별 scale·상속 shear를 확인. 승인되지 않은 비균일 scale/숨은 반사는 실패 |
| G10 reprojection error | 보정 대상과 독립된 기준점의 예상 screen 위치와 실제 엔진 투영/렌더 위치 오차를 px 단위로 비교. near/far/behind-camera 등 유효 domain을 명시하고 평균으로 큰 국소 오차를 숨기지 않음 |
| G11 UV correspondence | 이미지 landmark→UV→대상 표면 대응, UV 원점/뒤집기·atlas 영역·texel center 검사. UV 자체 기준과 projection distortion 기준을 구분 |
| G12 pixel-grid alignment | grid origin·cell size·sample center·반올림 정책을 고정하고 색/coverage/외곽선이 동일 셀 경계를 쓰는지 검사. 양자화의 비가역성·허용 오차를 정의; world나 bone을 임의 snap하는 대체 금지 |

렌더 전 수학 검사와 실제 GPU/렌더 타깃에서의 계약 검사를 구분한다. 모든 정의된 invariant/tolerance 충족이 **기술 합격**이다. 실행·컴파일 성공은 합격 기준이 아니다. 최종 육안 검사는 이 결과의 미술적 품질 검사이며 기하 오류를 눈대중으로 보정하는 주된 경로가 아니다.

#### 후보 실험·통합 금지선

Candidate A/B/C 등 실제 비교할 후보마다 **독립된 minimal prototype**과 결과 위치를 둔다. 같은 원본 입력·canonical·동작 fixture·카메라/픽셀 조건·평가 함수로 비교한다. 후보별 입력 변환이 다르면 그것도 파이프라인과 평가에 포함한다. 구체 후보 개수는 문제에 맞추며 의미 없는 세 번째 후보를 억지로 만들지 않는다.

하나의 실험을 수치 보정으로 끝없이 변형하지 않는다. 실패한 변환 ID와 오차를 보존하고, 구현 버그 수정인지 후보 기각인지 구분한다. 같은 방법의 수정 버전도 기준 결과와 diff를 보존한다. 프로덕션 코드는 **설계 완성 전 수정 금지**, prototype의 필수 검사 실패/미실행 상태에서 통합 금지다. 검사가 가능한 수학 계약은 자동 테스트로 구현하고 그 보고서를 근거로 다음 단계로 진행한다.

#### 우선 확인할 공식 기술 근거

아래는 각 표준 단계의 근거이며 전체 프로젝트 파이프라인의 완성/호환을 보장하는 출처가 아니다. Unity 6.0 문서와 현재 Editor 버전 차이는 실제 구현 전 확인한다. Blender 페이지의 상세 지원도 설치 버전에서 확인한다.

- Unity, [Rotation and orientation](https://docs.unity3d.com/6000.0/Documentation/Manual/QuaternionAndEulerRotationsInUnity.html): Unity 좌수계와 Euler/quaternion 규약.
- Unity, [Mesh.bindposes](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Mesh-bindposes.html): bone 역변환과 root 상대 기준, 공식 스키닝 예제. source/target 대응을 자동 저작하는 기능은 아님.
- Unity, [Retarget Humanoid animations](https://docs.unity3d.com/6000.0/Documentation/Manual/Retargeting.html): 구성된 Avatar를 통한 bone 구조 대응과 clip 재사용.
- Unity, [Camera.WorldToScreenPoint](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Camera.WorldToScreenPoint.html), [worldToCameraMatrix](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Camera-worldToCameraMatrix.html), [GetGPUProjectionMatrix](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GL.GetGPUProjectionMatrix.html): CPU screen·view·GPU 투영의 규약을 구분하는 기준.
- Unity, [Platform-specific rendering differences](https://docs.unity3d.com/6000.0/Documentation/Manual/SL-PlatformDifferences.html): 그래픽 API별 projection/texture 좌표 차이를 눈대중 flip으로 해결하지 않기 위한 확인 경로.
- Blender, [Armature Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html), [Bone Roll](https://docs.blender.org/manual/en/5.0/animation/armatures/bones/editing/bone_roll.html): 준비된 geometry의 weight 기반 변형과 rest-pose 축 정의. Blender의 Preserve Volume 등 선택한 알고리즘이 Unity skinning과 동일한지도 별도 확인.
- Lynch·Park, [Modern Robotics §3.2.1 Rotation Matrices](https://modernrobotics.northwestern.edu/nu-gm-book-resource/3-2-1-rotation-matrices-part-1-of-2/): 회전 기저·직교성·행렬식의 표준 수학 근거. 이 프로젝트용 새 변형 알고리즘을 제안하는 것이 아님.

## 2. 객체 수명과 씬

- `LoadSceneMode.Single`은 scene object를 언로드한다. 동일 인스턴스가 필요하면 명시적인 영속 루트가 소유해야 한다.
- `DontDestroyOnLoad`는 root GameObject에만 적용하고 필수 자식 참조를 함께 보존한다.
- 영속 루트가 프로젝트 에셋 외의 source scene object를 참조하지 않는지 확인한다.
- 완성본 Player·Camera·UI를 각 씬에 복제한 뒤 늦게 삭제하지 않는다. 작은 Bootstrap이 없을 때만 단일 프리팹을 만든다.
- 전환 전 drag, 열린 UI, EventSystem 선택, scene-local 상호작용과 캐시를 정리하고 도착·배치 성공 뒤 입력을 연다.
- `PersistentGameplayShell`은 객체 수명의 소유자이지 모든 게임 규칙의 만능 Manager가 아니다.
- `GameManager`와 persistent shell은 현재 별도 책임이다. 관련 요청 없이 합치지 않는다.

### 2.1 `SHELL-01` 변경 전 확인

권위 계약은 `AGENTS.md` §4와 `CURRENT_STATE.md`의 `SHELL-01`·`TRAVEL-01`·`TRANSITION-01`이다. 이 playbook에서 별도 Player 계약을 만들지 않는다. 해당 경계를 바꿀 때는 진행 이력의 연결된 상세 근거와 현재 prefab/scene 참조 그래프를 확인한 뒤 8.5의 검증을 적용한다.

## 3. 씬·프리팹·에셋

- 여러 씬의 공통 구성은 prefab을 단일 원본으로 사용한다.
- prefab source 변경과 instance override를 구분한다.
- Unity가 사용 가능하면 `.unity`, `.prefab`, `.asset` YAML을 직접 편집하지 않는다.
- 씬 저장 전 Missing Script/Reference, null 직렬화 필드, 중복 Camera/AudioListener/EventSystem, 잘못된 tag/layer와 의도하지 않은 override를 확인한다.
- Unity 에셋과 `.meta`는 한 쌍으로 보존하고 GUID를 임의로 생성·교체하지 않는다.
- 외부 에셋은 출처, 라이선스, 원본 URL과 수정 여부를 기록한다. 사용자 승인 없이 새 패키지나 외부 에셋을 들이지 않는다.

## 4. 정의 데이터·런타임 상태·세이브

- ScriptableObject는 공유 definition과 설정에 사용한다.
- mutable runtime instance와 immutable definition을 분리한다.
- Save DTO와 파일은 프로세스 사이 값을 운반하는 표현이지 live 권위 상태가 아니다.
- 배포 세이브를 ScriptableObject asset 변경으로 구현하지 않는다.
- 로드는 전체 DTO를 검증한 뒤 기존 런타임 소유자에 원자적으로 적용한다.
- `ItemDefinition` 숫자 ID는 아이템 종류 ID다. 영구 instance ID나 save record ID로 추정하지 않는다.
- UI, tooltip, 가격 배지, 검색 인덱스와 캐시는 원본에서 재구성 가능한 파생 표현이다.

## 5. 권위 소유자와 컨테이너

변하는 각 런타임 상태에는 한 시점에 쓰기 권위 소유자 하나만 둔다. 새 Manager, Session, 컨테이너나 캐시를 만들기 전에 관련 항목만 짧게 기록한다.

| 항목 | 확인 내용 |
|---|---|
| 권위 소유자 | 실제 원본을 쓰는 객체 하나 |
| 수명 | Application, Play Session, Scene, Raid, Entity, Container |
| 생성·정리 | 누가 언제 만들고 해제하는지 |
| 변경 진입점 | 값을 바꾸는 메서드와 호출자 |
| 포함 관계 | 소유 자식과 단순 참조·관찰 대상 |
| 이전 규칙 | 사전 검증, 이동, 실패 rollback |
| 파생 표현 | UI·인덱스·캐시 갱신/무효화 |
| 저장 경계 | DTO 변환 주체와 저장 여부 |
| 업데이트 | Update, Tick, Interval, Event 중 실제 주체 |

- 런타임 객체는 동시에 둘 이상의 논리 컨테이너에 소유되지 않는다.
- 컨테이너 내부 컬렉션과 불변조건은 컨테이너 API만 변경한다.
- 이전은 사전 검증 → 기존 소유자 제거 → 새 소유자 적용 → 역참조·인덱스 갱신의 한 작업 경계다.
- 실패하면 원본 위치와 값이 그대로 남아야 하며 유실·복제·부분 이동이 없어야 한다.
- 둘 이상의 소유자를 바꾸는 coordinator는 순서·검증·rollback만 조정하며 별도 원본 복사본을 소유하지 않는다.
- 직접 owner 경로가 있으면 `Find*`, 임의 Singleton, service locator나 전역 이벤트로 다시 찾지 않는다.
- 상태 변경은 `입력 소유자 → 기능 진입점 → 권위 소유자 → 상태 변경 → 완료 통지·표시 갱신`으로 역추적할 수 있어야 한다.
- 이벤트는 주로 완료 통지에 사용한다. 여러 listener가 같은 변경을 경쟁해서 결정하지 않는다.
- 실제 책임 없이 호출만 전달하는 Manager/Service나 형식적인 인터페이스 계층을 만들지 않는다.

## 6. Update·Tick·인덱스·캐시

- 매 프레임 필요한 입력·카메라·표현과 낮은 빈도의 게임 규칙을 구분한다.
- 같은 종류의 객체가 많아지면 scope 소유자의 등록 목록과 Tick을 우선 검토하되, 소수 프로토타입에 scheduler를 먼저 만들지 않는다.
- Tick 목록 순회 중 등록·해제가 가능하면 pending add/remove나 안전한 작업 경계를 둔다.
- 반복 공간 조회가 병목이면 map/scene 범위의 파생 인덱스를 사용하고 생성·이동·상태 변경·파괴 경계에서 갱신한다.
- 캐시는 원본, key, dirty 조건, 무효화 호출자와 전체 재구축 경로가 모두 있어야 한다.
- hot path에서 반복 `Find*`, `GetComponent`, LINQ 할당, 새 컬렉션과 불필요한 Physics 전체 탐색을 피한다.
- 성능 구조 변경은 대표 규모의 Profiler 전후 증거가 있을 때만 완료로 판정한다.

## 7. Unity Editor 작업 경로

- 씬 오브젝트, prefab, Material과 serialized reference는 Unity MCP/Editor API의 단일 writer가 변경한다.
- `GameMap1`·`GameMapTest` 직접 Play는 `GameStartRequest`가 없는 Editor authoring session으로 판정되어 ordinary save와 Raid Recovery를 같은 고유 임시 루트에 격리한다. 빠른 기능 시험에서 실제 원정 캐시를 삭제·정산·우회하지 말고 이 경로를 사용한다. 실제 복구·세이브 검증은 `InitialLoadingScene` 또는 `MainMenuScene`부터 시작한다.
- 다른 에이전트는 같은 시간에 Play Mode, AssetDatabase, scene/prefab 저장을 실행하지 않는다.
- Unity MCP가 노출되지 않으면 연결·컴파일·domain reload·승인 상태와 다른 MCP 담당을 먼저 확인한다.
- Computer Use는 사용자가 현재 턴에 명시적으로 허용한 경우에만 최소 동작에 사용하고, 끝나면 즉시 제어를 종료해 보고한다.
- C#·문서 파일은 `apply_patch`로 변경한다.

### 7.1 RunCommand 규칙

- 클래스 이름은 `CommandScript`, 형식은 `internal class CommandScript : IRunCommand`으로 한다.
- 생성은 `result.RegisterObjectCreation`, 수정 전에는 `result.RegisterObjectModification`, 삭제는 `result.DestroyObject`를 사용한다.
- 로그는 `result.Log`, 경고는 `result.LogWarning`, 오류는 `result.LogError`를 사용한다.
- top-level statement를 사용하지 않는다.
- Undo/Redo와 scene dirty/save 범위를 명확히 한다.
- 성공 메시지만 믿지 않고 Console, 오브젝트 수, 참조와 scene dirty를 별도 확인한다.

## 8. 위험 비례 검증

### 8.1 공통

- 변경 전 Console과 git 기준선을 잡고 기존 오류와 신규 delta를 구분한다.
- import/compile 뒤 새 Error, Exception, Assert와 변경이 만든 Warning이 없어야 한다.
- 새 Missing Script/Reference, null serialized field와 의도하지 않은 dirty가 없어야 한다.
- 현재 변경과 직접 연결된 정상·취소·실패 경계를 확인한다.
- 먼저 변경된 권위·입력·수명·직렬화 경계와 바로 맞물린 기능만 `인접 검증` 대상으로 고른다.
- 전체 한 바퀴는 셸·씬·저장·정산처럼 여러 단계의 실제 순서를 직접 바꿨거나 릴리스 gate일 때만 한다. 단일 기능 변경의 기본 검증으로 사용하지 않는다.
- 같은 대표 흐름은 기본 1회다. 반복은 수명 누적이나 간헐 오류처럼 이유가 있을 때 횟수를 먼저 정한다.
- 서로 다른 seed, schema/migration, 손상 분기, grid, 해상도나 플랫폼은 최소 case matrix의 서로 다른 case로 각각 1회 확인할 수 있다.
- 검증 뒤 Play Mode를 종료하고 원래 활성 씬과 의도한 저장 상태를 확인한다.

### 8.2 입력·상호작용·UI

- 입력·UI를 바꿨으면 가능할 때 실제 키와 UI 순서로 정상, 취소, 범위 밖, 빠른 중복 입력을 확인한다.
- 공개 메서드 호출로만 확인했다면 `[Play Mode 호출 확인]`으로 기록하며 실제 물리 입력 확인으로 승격하지 않는다.
- drag 중 닫기, 거리 이탈, scene transition과 UI close가 같은 데이터 안전 경로로 수렴하는지 확인한다.
- 기존 관련 기능이 현재 diff에 닿지 않았다면 과거 성공 증거를 재사용한다.

### 8.3 공격·피해·사망

- 입력 차단, 빈 활성 무기와 열린 인벤토리에서는 공격·효과음이 나가지 않아야 한다.
- 단발 edge와 자동 hold가 같은 RPM cadence를 통과하는지 확인한다.
- 실제 Raycast는 Camera가 아니라 Player 발사 원점에서 마우스 XZ 조준 방향으로 나가야 한다.
- 모든 피해는 공통 `IDamageable.ApplyDamage`를 통과하고 `EnemyStats`의 `>0 → 0`에서만 사망을 한 번 통지한다.
- 사망 뒤 Brain·공격·Agent·피격 Collider는 비활성이고 root·렌더·시체 전리품은 유지된다.
- 유효한 빗나감은 발사음만, 실제 적용 피해는 구분되는 적중음을 낸다.

### 8.4 소유권·컨테이너·캐시

- 쓰기 권위 소유자는 하나이며 우회 직접 쓰기가 없어야 한다.
- 이전 성공 뒤 기존 소유자에는 0개, 새 소유자에는 1개이며 역참조·인덱스가 일치해야 한다.
- 실패 뒤 원본과 잔액이 그대로이고 유실·복제·부분 이동이 없어야 한다.
- 등록·해제 수가 맞고 제거된 객체가 계속 Tick되지 않아야 한다.
- 원본 변경 뒤 UI·캐시가 갱신되고 전체 재구축도 같은 결과를 만들어야 한다.

### 8.5 Player 셸·씬 전환

이 경계를 직접 변경했을 때만 다음을 확인한다.

- `GameMap1 → GameMapTest → GameMap1` 대표 왕복 1회와 `GameMapTest` 직접 시작
- Shell, Player, Camera, `InventoryUIManager`, EventSystem의 전후 `GetInstanceID()` 동일
- persistent shell 1개, destination runtime 복사본 0개
- SpawnPoint 배치와 Rigidbody 속도 초기화
- 두 씬의 이동·상호작용·인벤토리와 현재 아이템 상태 보존
- 중복 AudioListener/EventSystem, destroyed reference와 기본 아이템 재생성 없음

### 8.6 테스트와 빌드

- 순수 데이터·규칙은 가능한 EditMode 테스트, 프레임·씬·입력·물리는 PlayMode 또는 실제 Play Mode로 검증한다.
- Player build는 변경 위험이나 사용자 요청에 필요할 때 수행한다. 실행하지 않았으면 빌드 미검증이라고 명시한다.
- 실행하지 않은 검증은 통과했다고 쓰지 않는다. 구현됨, 검증됨, 미검증과 차단 사유를 구분한다.

## 9. 파일·Git 마무리

- `Library/`, `Temp/`, `obj/`, build 출력과 registry `PackageCache`를 소스처럼 수정·커밋하지 않는다.
- 작업 전후 `git status`와 diff로 사용자 변경을 구분한다.
- 무관한 dirty 파일을 되돌리거나 포맷하지 않는다.
- 검증 완료 뒤 이번 작업 파일과 필요한 `.meta`만 명시적으로 stage한다. `git add .`와 `git add -A`를 쓰지 않는다.
- staged diff와 파일 목록을 확인한 뒤 기능 단위 로컬 커밋 하나를 만든다.
- 기존 변경과 안전하게 분리할 수 없는 파일은 자동 커밋하지 않고 이유를 보고한다.
- push, 원격 branch, PR과 Unity Version Control은 사용자 별도 요청 없이는 수행하지 않는다.

## 10. 증거 표기

- `[사용자 확인]`: 사용자가 실제 결과를 확인했다.
- `[Player 확인]`: 빌드된 프로세스에서 확인했다.
- `[Play Mode 확인]`: 실제 Play Mode 프레임과 사용자 흐름으로 확인했다.
- `[Play Mode 호출 확인]`: 런타임 진입점으로 확인했지만 실제 입력은 우회했다.
- `[코드/씬 확인]`: 코드, scene, prefab과 직렬화 상태를 확인했다.
- `[코드 확인]`: 실행하지 않고 경로와 불변조건만 확인했다.

증거 등급을 임의로 올리지 않는다. 완료 기능에 관련 변경이나 새 회귀가 없다면 기존 가장 강한 증거를 재사용한다.
