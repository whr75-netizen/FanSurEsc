# 눈 source 특징 캐시와 현재 경로 · 읽기 진단/독립 실험

## 핵심 결과

사용자가 말한 방식은 **source 색 영역/셀→eye feature ID→캐시된 cluster와 상태별 배치→그 feature의 색→가림을 고려한 독립 합성**입니다. 현재 구현에는 좌우 ID·기하 adapter·2D 역할/색 템플릿과 분리 렌더는 있지만, 그 source cluster를 현재 출력 셀까지 보존하는 계약이 없습니다. PIA가 의미 인식을 하지 않는다는 점은 이 연결을 구현하지 않을 이유가 아닙니다.

실제 현재 asset Template216에는 각 눈 홍채4셀(2×2), 흰자6셀이 저장돼 있습니다. **이를 모든 각도의 최소4셀로 승인받았다고 해석하지 않습니다.** 이 참조 pose와 현재 pose/화면 크기는 다릅니다. 현재 shader는 이 배치를 형태 캐시로 사용하지 않고 Own에서 같은 eye/role의 색을 찾는 데 사용합니다. 상안검 role6은 이 TemplateRole에 없습니다. 실제 native upper-line 공급과 별도 590 curve 경로가 있으나, 저장된 제품 설정 iris582/lash583=false에서 region583/closed590 선택은 실행되지 않습니다.

## 현재 요구와 코드 차이

| 단계 | 실제 저장/선택 | 요구와 차이 |
|---|---|---|
| 원본 분리 | EyeRenderer367의 S1=sclera submesh4, S2=iris submesh1, S3=eyeline submesh6 | source part는 이미 알지만 colour-range/UV mask/cell 대응 캐시로 이어지지 않음 |
| 캐시 | EyeFeature348.cs의 topology hash, stableId1/2, rest triangles/eye ring, Template216 role/RGBA | 읽히는 cluster를 보존할 state cache가 아님. GPU records와 counts는 프레임마다 초기화/재작성 |
| 1차 손실 | LayerSample19가 실제 S2 표본에도 Classify(rest)의 iris ellipse/상안검/개구 조건을 다시 적용 | 원래 iris feature identity를 geometry style 분류가 삭제할 수 있음 |
| 2차 손실 | IrisAllocated19가 area round와 per-cell rank로 크기/배치를 결정 | 템플릿의 cluster adjacency/상안검 관계나 중요도별 가독성 제약이 입력되지 않음 |
| 색 | iris/white는 현재 source surface RGB 대신 TemplateRGBA의 role별 nearest 공급 | 형상 winner가 white/iris로 바뀌면 색 공급 역할도 바뀜. eye 전용 색 ID cache/직접 source palette contract 없음 |
| 레이어 | outline 뒤 눈을 합치되 실제 depth/alpha로 hair/skin/brow/body가 가림 | '맨앞'의 전역 덮어쓰기로 바꾸면 안 됨. 한 셀 winner로 여러 작은 특징이 경쟁하는 문제는 남음 |
| 시간 | Native395 RGB history는 눈 domain을 재사용 대상에서 제외 | source feature/cluster를 캐시하라는 요구를 충족하지 못함. history를 켜는 것만으로 해결되지 않음 |

정확한 함수/파일/행은 CONTRACT_DIFF.json에 있습니다. 현행 iris 경로는 Classify→CountFeatures19→IrisAllocated19→ChooseLayers19→대표 표본 선택→Own→Merge입니다. 기존 EyeCompose333의 parent/iris Contour295 정보를 먼저 사용해도 뒤 EyeFeature348이 자체 normalized classification/cell selection으로 다시 결정합니다. 과거 Eye431의 정규화 단계 손실과 같은 종류의 경로가 **현재도 남아 있음**을 확인했으며 과거57→26 수치를 현재 재현값으로 복사하지 않았습니다.

## 저장 자료에 현재 식을 적용한 결과

아래 S2는 **실제 저장한 iris source mesh 표본**이며, 분류 전/후는 현재 Classify를 CPU float32로 계산한 **가림 전 intrinsic 수치**입니다. skin/hair/body occlusion이 없는 실험이 아닙니다. 일부 필요한 S0/S4/S5/S6 버퍼가 저장돼 있지 않아 전체 GPU winner를 재실행할 수 없습니다.

| 저장 pose / 눈ID | 원본 S2 표본→normalized iris | 저장 최종 홍채 셀 | 저장 상안검 셀 |
|---|---:|---:|---:|
| neutral / ID2 | 71→39 | 2 | 1 |
| neutral / ID1 | 57→34 | 2 | 1 |
| walk-00 / ID2 | 61→34 | 2 | 1 |
| walk-00 / ID1 | 61→35 | 2 | 0 |
| walk-01 / ID2 | 55→34 | 2 | 0 |
| walk-01 / ID1 | 63→37 | 2 | 0 |
| walk-02 / ID2 | 54→33 | 2 | 0 |
| walk-02 / ID1 | 61→39 | 2 | 0 |
| walk-03 / ID2 | 54→30 | 1 | 0 |
| walk-03 / ID1 | 64→37 | 2 | 0 |

원본이 hidden이거나 스타일 aperture 바깥인 모든 표본을 최종에 그려야 한다는 결론은 아닙니다. 확인된 사실은 **source iris membership가 표현 단계의 조정 attribute로 남는 대신 이 단계에서 제외된다는 점**입니다. 원본 UV/primitive/rest/normalized 좌표와 alpha를 DISCARDED_SOURCE_SAMPLES.json에 저장했습니다. float32/64 분류 차이도 기록했으며 실제 shader 전체를 GPU로 재검증했다고 주장하지 않습니다.

저장 데이터의 같은 geometry 대표 UV19개는 S2와 eye-surface가 모두 정확히 일치하지만, S2층 RGB와 head출력 RGB는19개 모두 다릅니다. 예: neutral의(226,51), eye1/catch feature4는 S2=(.006312,.005404,.012785), head=(.201172,.090820,.059570). 이는 같은 UV의 geometry를 쓰면서 TemplateRGBA 공급으로 색을 바꾸는 현재 Own 경로와 맞습니다. **S2는 현행 EyeSurface shader의 MToon 결과이며 unlit albedo라고 부르지 않습니다.** 각 cache 색의 원래 제작 의도/현재 조명과의 정당성은 이 차이만으로 모두 판정하지 않았습니다. 눈 경로에서 머리의 palette-v4 family를 직접 참조하는 증거는 없습니다. 역할 재분류와 공급자 차이를 먼저 고쳐야 할 대상으로 분리합니다.

## 독립 후보와 반례

SourceFeatureCache42는 기존 template의 참조 cell ID/adjacency와 source/style fingerprint를 저장하고, **sourceRole1은 iris라는 parent ID를 유지**하게 합니다. normalized curve 결과는 subtype attribute로 남기며 iris를 white/skin으로 바꾸지 않습니다. 실제 가림이면 visible membership는0이지만 intrinsic cache는 유지합니다. source/style가 바뀌면 사용을 거부하도록 따로 시험했습니다. mesh/UV colour-range 전체 adapter는 아직 완성되지 않았고 declared prefab topology hash를 현재 Unity에서 재검증하지 않았습니다.

실제 저장10눈 입력에서 intrinsic source membership를 보존하는 후보를 시험했습니다. PNG의 prototype은 **intrinsic mask/ID 단계**이며 수정된 최종 눈이 아닙니다. 맨앞으로 색을 덧칠하거나2/4픽셀로 강제하지 않았습니다. 최종 cluster 배치·표정/방향별 디자인 최소형태·실제 가림·팔레트 출력은 아직 해결하지 않았습니다.

현행 rank/area 코어의 합성 반례도 만들었습니다. 같은 feature ID에서16표본 계수합23/16→25/16이면1→2셀,39/16→41/16이면2→3셀입니다. [14,2,2,14]는2셀 대각선을 선택합니다. 이것은 모든 대각선이나 모든 count 변화가 오류라는 뜻이 아니라, **현재 식에 승인된 cluster 형태/상태를 구분할 제약이 없다는 증거**입니다. 실제 방향·표정/가림 때문에 바뀌는 형태와 grid phase 때문에 바뀌는 형태를 다른 입력으로 검사해야 합니다.

총10개 오프라인 계약/반례 검사를 했습니다. 새 Unity 호출·GPU 캡처·최종 눈 렌더는0입니다. 기존5pose는 연속 프레임이 아니며 시간 안정성 통과로 해석하지 않습니다. 실제 저장 최종 PNG와 source/분류/prototype mask는 서로 구분해 표시했습니다.

## 다음 수정의 정확한 범위

1. EyeFeature348에서 source part/colour-range/UV 영역과 canonical cell graph를 feature ID에 연결합니다. 기존 TemplateRole 참조와 source mesh 정보를 재사용하되 source/색 범위/style fingerprint를 키에 포함합니다. geometry adapter만 캐시한 상태를 feature cache라고 부르지 않습니다.
2. EyeFeature348.compute의 LayerSample19에서 source parent identity와 style subtype을 분리합니다. 그 뒤 IrisAllocated19/NativeLineAllocated19의 단독 area winner를 상태별 cluster 공동 배치로 대체해야 합니다. **source membership만 보존한 현재 prototype을 전체 해결로 통합하지 않습니다.** 승인된 reference와 작가 도해를 기준으로 front/quarter/profile 및 blink state의 최소 읽힘/연결/상안검 관계를 정해야 하며 literal2px/4px나 같은 도장을 모든 pose에 강제하지 않습니다.
3. 현재 role별 nearest TemplateRGBA 공급을 어느 원본 색/feature palette를 유지할지 명시한 계약에 연결합니다. lower lid skin색과 iris/white/catch를 같은 family로 뭉치지 않습니다. 실제 depth/alpha의 눈꺼풀·머리 가림은 그대로 보존합니다.

이것은 제안 범위이며 제품 변경은 하지 않았습니다. 최소 후속 입력은 같은 pose/각도/표정의 source-feature cache, 현재 source/가림/depth, 배치 전/후의 feature/cell IDs와 최종 colour supplier입니다. Unity 연결이 확인되기 전 새 실행을 시작하지 않습니다.

## 연구에서 취할 부분과 제외

PIA 원문/공개 소스는 연구 담당이 확인해 전달했습니다. [논문](https://cragl.cs.gmu.edu/pixelate/pixelated_image_abstraction-journal-300dpi.pdf), [공개 코드](https://cragl.cs.gmu.edu/pixelate/code.zip). mapping은 Lab+화면거리이며 input_weights는 superpixel mean과 palette association/refinement에 쓰입니다. 이를 feature/sourceUV 검출기라고 주장하지 않습니다. 가져올 원리는 표현 단계와 기준을 일치시키고 중요한 특징의 제약/일반 신호의 soft importance를 구분하는 것입니다. 우리에게 source colour/part 분류와 eye ID 연결이 이미 가능하므로 '의미 인식 없음'으로 그 연결을 포기할 이유가 없습니다. 전체 저해상도 PIA 변환/전역 평균/bilateral RGB 혼합/새 SLIC 해상도를 적용하지 않았습니다.

[SLYNYRD 얼굴/머리](https://www.slynyrd.com/blog/2020/7/28/pixelblog-29-anime-faces-and-hair)의 큰 눈·정확한 특징 배치, [8방향 회전 비교](https://www.slynyrd.com/blog/2025/3/24/pixelblog-55-top-down-character-animation)의 같은 캔버스 검사 원리는 cluster 검증 기준에 사용합니다. [BlubbrMuffins](https://www.patreon.com/BlubbrMuffins/posts/beginner-files-163119360)의 부위/표정 상태 분리는 참고하되 큰 VTuber 눈의 픽셀 수를 이식하지 않습니다. 이 자료의 도해 확인은 연구 담당의 전달이며 이번 작업에서 새로 직접 재생한 것처럼 쓰지 않습니다.

이전 머리 contrast-bounded가 막힌 이유도 별도로 보존합니다. 첫 거부 witness18/16개 중 실제 Q조합과 같은 기록은0개였고, 원색차0인 두 셀도 가상 Q0/Q2의 그림자 폭을 unlit source 대비로 재어 거부했습니다. 모든 source gradient/그림자 변화를 특징 대비로 보호한 상한의 적용 범위가 잘못됐습니다. 실제 C후보의 두 국소 대비 증가는 별도 존재하므로 '가상 witness만 있었으니 회귀 없음'으로 결론을 바꾸지는 않습니다. 눈 source-feature 검토를 우선하느라 새 머리 미술 후보를 추가하지 않았습니다.

## 상태

모든 결과는 기존 실험 폴더 eye-cache42에만 있습니다. 제품/31/34/기존 후보/원본/Unity dirty 상태를 변경하지 않았습니다. Desktop/게시와 Unity 열기는 대기 상태이며 재시도하지 않았습니다. 현재 최종 눈 결함의 수정 완료·최종 미감·시간 안정성을 주장하지 않습니다.
