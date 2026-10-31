# 눈 후속50 — 상안검 재배치 수정과 흰자 원인 분리

후보49는 그대로 보존했습니다. 승인된49의 45파일은 Assets 밖 `experiments/pixel-pipeline/2026-10-30-eye-candidate49`에 커밋됐습니다: **d0ca21f4ac87e82151357253582f9ce079596a2d**. 이 후속50은 별도 작업폴더에만 있으며 그 커밋에 포함하지 않았습니다. 새 Unity 호출·렌더·캡처·GC·정리·제품 변경은 없습니다.

## 상안검 이동의 정확한 원인

49의 공통 정수 이동은 여섯 프레임 모두 `[2,-26]`입니다. 동일 frame101의 source packet을 고정하고 홍채 점유 입력만 바꾸면 상안검이 바뀝니다. 따라서 **그 이동의 직접 원인은 source 좌표나 anchor 변화가 아니라, 후단 홍채 점유가 안검의 후보 제외/순위로 되먹임되는 의존성**입니다.

`NativeLineAllocated19`는 `IrisAllocated19`인 셀을 먼저 제외합니다. frame101/ID1에서 기존 source 기준은 `(222,52)`를 안검으로 선택합니다. 49의 더 큰 cache 홍채가 그 셀을 점유하면 제외되고, `(221,53)`이 다음 후보가 됩니다.

|source 셀|white 가중치|iris 가중치|native line 가중치|line 비용 max(white,iris)−line|
|---|---:|---:|---:|---:|
|(222,52)|1|0|2.696853876|−1.696853876|
|(221,53)|0|0|0.081756473|−0.081756473|
|(225,52)|3|0|2.986550331|+0.013449669|

cache가 첫 셀을 빼면 약0.08표본의 작은 조각이 더 많은 line source를 가진 `(225,52)`보다 먼저 선택됩니다. 모델의 상안검이 실제로 왼쪽 아래로 이동한 증거가 아닙니다.

### 후속50의 최소 변경

- 원래 source iris 자격 계산을 `SourceIrisAllocated19`로 분리합니다. 새 cache footprint는 이 source 함수의 입력이 아닙니다.
- `NativeLineAllocated19`의 두 홍채 제외 참조는 source 함수만 봅니다. cache가 안검을 다른 빈 칸으로 옮기게 하지 않습니다.
- `ChooseLayers19`에서는 source native-lid를 먼저 해결하고 cache iris를 그 뒤에 둡니다. 원래 경로에서는 source iris/lid가 상호 배타적이므로 순서 교환은 기존 결과를 바꾸지 않습니다. 미래 cache가 겹칠 때도 안검을 재배치하거나 덮는 대신 원래 lid ID를 보존합니다.
- 색·SourceWhiteNeighbour·면적·비용·동률식·외부 hair/body 가림을 바꾸지 않습니다. 최소 셀 수나 빈 칸 재채우기를 넣지 않습니다.

`SOURCE_PARTS_ONLY.diff`와 `EyeFeature348_source_parts50.compute`가 실제 파일입니다. gate47 후보를 바탕으로 한 **미import·미GPU컴파일** 준비본이며, 자체적으로49의 전체 GPU cache를 구현한 파일은 아닙니다. cache 연결 지점을 분리한 코드와 CPU 결합 모델입니다.

## 실제 반례 동시 비교

|ID1|frame96|97|98|99|100|101|
|---|---:|---:|---:|---:|---:|---:|
|실제47의 가시 iris|2|2|2|2|1|2|
|49 cache+기존 외부 가림|4|4|4|4|4|4|
|50 source lid 보존 후 cache 레이어|4|4|4|4|4|3|

frame100의 기존 한 셀 소실을 되돌리는 cache 효과는 남습니다. frame101 상안검도 `(221,53)`으로 밀리지 않고 source 위치 `(222,52)`에 남습니다. 그러나 그 셀에서 iris와 lid를 동시에 하나의 불투명 픽셀로 표시할 수 없어 cache iris는3셀입니다. **full iris shape 문제까지 해결한 결과가 아닙니다.** 상안검을 없애 4셀 통과로 만들지 않았습니다.

실제 source-lid 면적/반올림 budget 자체도 ID1에서
`0.3968221, 0.4462737, 0.3908575, 0.4174230, 0.4536275, 0.5035617` → `0,0,0,0,0,1`입니다. cache의 점유 되먹임을 제거해도 이 부분은 남습니다. actual motion의 투영/가림이 함께 바뀐 자료이므로 그 면적 변화 전체를 순수 sampling artifact로 단정하지 않습니다. blink 가중치가0이라는 사실만으로 모든 보이는 면적이 일정해야 하는 것도 아닙니다.

## 흰자는 다른 단계에서 소실됨

흰자의 대표 표본은 `candidate49.representative`에서 S1 source를 찾은 뒤 S0 skin/S3 lash/외부 가림을 적용합니다. 상안검의 전체 셀 allocator보다 앞입니다. 같은 입력에서 source 하나씩만 제거한 ablation 결과:

|흰자 가시 셀/12|96|97|98|99|100|101|
|---|---:|---:|---:|---:|---:|---:|
|엄격49|4|4|4|4|4|5|
|S3만 제거 — 진단용|4|4|4|4|4|5|
|S0만 제거 — **미채택**|10|10|10|9|9|10|

frame96에서 raw 가림 때문에 사라진 흰자7셀은 S1 source가1~12개 실제 존재합니다. source가 없는 빈 곳이어서 못 그린 것이 아닙니다. 특히 아래쪽3셀은 S0 때문에 weight0입니다. 남은 별도1셀은 logical hair gate에 가립니다. 이 둘을 섞어 전부 “실제 lid니까 지워야 함”으로 판정하지 않습니다.

현재 S0는 generic face skin을 담고 있고, 일반 얼굴 underlay와 실제 upper/lower-lid의 의미 구분을 이 자료가 따로 제공하지 않습니다. 등록된 특징 레이어를 얼굴 skin 위에 놓아야 하는 범위와 실제 닫힘/가림으로 없애야 하는 범위를 구별해야 합니다. S0 전체를 무시하면 실제 lid도 덮을 수 있습니다. 따라서 **S0 bypass는 원인 확인용이며 후보에 적용하지 않았습니다.** 새 눈색을 빈 곳에 칠하거나 지원 없는 blink 상태를 추정하지 않았습니다.

## 좌표/anchor 검토에서 버린 가설

현재 `modelEyes.centre`는 흰자 socket의 중심입니다. 저장 projection으로 그 두 중심의 간격은 약8.03셀이고 Template iris 중심 간격은7셀입니다. 이를 눈별로 반올림 등록하면49의 상안검 충돌을 없애는 배치가 나옵니다. 그러나 실제 S2 alpha 가중 raster 중심 간격은 frame96에서 약7.60셀입니다. 흰자 중심을 iris 중심과 같은 사실값으로 취급하면 안 되고, alpha 가중 raster 중심 역시 정확한 native mesh 중심이 아닙니다.

따라서 **socket 중심에 맞춰 눈을 한 칸 더 옮기는 안은 채택하지 않았습니다.** 그 변경으로 충돌이 사라졌다는 것만으로 올바른 source feature 등록을 입증하지 못합니다. 보존된 core에서는49의 anchor/좌표를 그대로 두고 의존성만 분리했습니다. 앞선 중간 보고의8.03셀은 iris의 실제 중심이라고 부르면 잘못이며, socket 중심 측정이라는 한계를 이 문서에서 명확히 합니다.

## 검증·이미지·보존

- `run50.py`: 동일6프레임, 기존1536packet 재생 함수 재사용. 12 eye-frame의 source-lid 결정 보존,1536개 셀의 원래 iris/lid 순서 동등성, cache wrapper로 향하는 안검 의존 참조0, 색·role·좌표 불변, hair/body가 가린 셀 복원0, frame100/101 반례를 검사했습니다.1637검사 통과는 미감 보증이 아닙니다.
- 실제 원배율과 nearest8배 비교를 열어 확인했습니다. row1 실제 GPU, row2 잘못된49 lid ID, row3 수정50 source lid ID, row4 49 cache RGBA 레이어, row5 source lid를 보존한50 cache 레이어입니다. 진단색 lid를 실제 RGB라고 표시하지 않았으며 전체 후보 얼굴 합성도 아닙니다.
- 기존49의 모든 package hash를 확인했습니다. 49와 원본47 데이터를 바꾸지 않았습니다. 제품12파일 해시 동일. 현재 dirty25를 Unity에서 새 조회한 것은 아니며 이번에는 Unity 명령을 보내지 않았습니다.
- `EUnityValidation01`에서 `*326*` source 파일을 좁혀 찾았으나 그 이름의 자산/코드를 찾지 못했습니다. 과거326 reference가 없다고 결론내린 것이 아닙니다.

## 남은 정확한 입력/구현

안검까지 포함한 같은 상태의 iris/sclera/lid source-cell key form과 원래 표면 UV/triangle/bary binding, generic face-skin/실제 lid 또는 model-bound aperture의 구분이 필요합니다. 현재 Template216에는 lid role이 없습니다. 그 역할을 임의 모양으로 만들어 등록하지 않습니다. 기존 native closed-eye-boundary/upper-arc와 현재 source-point를 연결할 수 있는 자료를 먼저 써야 하며, 회전/blink에 대해서는 등록 상태와 실제 가림을 검증해야 합니다. 새 렌더 허가가 없어서 계속 캡처하지 않았습니다.

50은 **안검의 잘못된 빈 셀 이동 경로를 고친 독립 후보**이며, 흰자·눈 전체 완성이나 GPU 통합 성공은 아닙니다. 후속50은 아직 로컬 커밋 대상에 포함하지 않았습니다.
