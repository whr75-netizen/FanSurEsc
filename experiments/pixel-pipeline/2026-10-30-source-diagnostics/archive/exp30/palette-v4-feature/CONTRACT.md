# 후속 후보 연결 계약

원래 `palette-v3`는 유지합니다. 후속 runtime은 같은 폴더의 `palette.cjs`, `palette_math.cjs`, `CONSTRAINED_64.json`을 사용합니다. 모델은 현재 실제 sourceId/modelSHA/원본 재질 가족과8개 source 대비 증거에 연결됩니다. 다른 모델/색계열에 현재 갈색 모델을 재사용하지 않습니다.

```js
const {referenceForSample,buildPalette}=require('./palette.cjs');
const P=buildPalette(model,intervalScale).tablesRGB8; // source/g를 받지 않음
// main의 기존 미확정 여부를 먼저 처리한다.
const reference=referenceForSample(model,{
 modelSHA256, materialId:packet.role,
 uv:selectedFeatureSourceUV,
 baseRGBAlinear:selectedFeatureSourceRGBA
},{colourGroupId:existingAppearance,uncertain:false});
const RGB=P[reference.paletteReferenceId][existingShadeK];
```

source 선택의 `sourceSelectionKnots`는 감사된 원색 대비로 만든 단조 선택 곡선입니다. 화면좌표·g·Q·depth로 source ID를 선택하지 않습니다. 실제 source UV/RGBA와 geometry UV/g를 서로 바꾸지 않습니다. 최종RGB에 source/g를 다시 곱하지 않습니다. m은 팔레트 간격만 변경하며 실제 원색 anchor와 기존 라벨은 유지합니다. 보호 대비 보장은 기본 m=1, 같은 Q에 대한 것입니다.

`BUDGET_BINDINGS.json`은 같은 고정 입력의16/32/64색 및 보호/비보호 비교입니다. runtime 소스 선택 코드의 좌표별 예외표가 아닙니다. 신규 카메라/모델에 고정 바인딩을 재사용하지 않습니다. 새 모델은 그 모델의 원본 재질/UV 색과 검증한 source 특징 제약을 공급해야 합니다.

`FEATURE_CERTIFICATES.json`은 source 재질/UV/RGBA·측정 대비·감사결론을 보관합니다. 저자가 부여한 특징 ID가 아니며 sourceFeatureId=null은 유지합니다. 8쌍의 증거를 모든 원본 특징의 자동 분류 성공으로 확장하지 않습니다.

`SOURCE_DOMAIN_MAP.json`의 추정 특징영역 ID와 렌더 paletteReferenceId는 별개입니다. 색수 증가로 생긴 톤 경계를 source-feature 경계로 자동 승격시키지 않습니다. 새 톤 경계에 기존2톤/4appearance 공유곡선을 그대로 붙이지 않습니다. 기하/가시 표면/명암 라벨은 main 담당과 같은 원본을 사용합니다.

보호64가 대비 조건을 만족해도 단셀과 톤 분절은 늘어납니다. 보존/정규화 어느 미술안도 선택하지 않았고 Unity/제품/31/34/dirty25에는 적용하지 않았습니다.

원본 재현 작업 경로: `C:\Users\15352\Documents\Codex\2026-10-30\task\palette-v4-feature`. 생성 스크립트는 거기에 기록한 실제 원본source/native texture/main packet 경로를 읽습니다. 복사된 폴더의 runtime HTML/API/JSON/PNG는 외부 source 경로 없이 열리며, 원본 재생성에는 기록된 입력이 필요합니다.
