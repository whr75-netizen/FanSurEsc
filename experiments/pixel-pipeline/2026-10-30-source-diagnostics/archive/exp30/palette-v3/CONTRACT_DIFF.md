# palette-v2 → v3 연결 차이

후보 전용입니다. 기존 R6/31/34/Unity와 palette-v2 파일은 유지합니다. 이번 입력은 `ribbon-path/PALETTE_V2_BINDING.json`의 보존·정규화 실제 sourceUV/RGBA이며, `tone-boundary`의 미채택 after 한 셀은 쓰지 않았습니다.

## 유지

원본 source/model/material/UV/RGBA, geometry UV/g/owner/chart, 기존 appearance, Q(g)·임계값, sourceFeatureId=null, 미확정10셀 정책을 보존합니다. 확정358+미확정10+외부912입니다. corrected feature의 sourceUV를 geometryUV로 되돌리지 않습니다. 두 안을 별도로 계산하고 미술안을 선택하지 않습니다.

## 바뀐 ID 의미

```text
v2: T = L(source)>=cut[appearance]
    referenceId = 2*appearance+T        // 8개의 독립 기준
    RGB = P[referenceId][Q]

v3: referenceId = argmin_j ΔE_OKLab(source,nativePalette[j])
    RGB = P[referenceId][기존 Q]        // 공유 native16기준
```

appearance는 지우거나 referenceId로 대체하지 않습니다. 기존 sourceTone 0/1은 과거 진단값으로만 저장하며 새 팔레트 ID와 혼용하지 않습니다. 새 reference 경계는 기존2톤 경계와 다르므로 main의 source-tone 곡선을 자동 재사용하면 안 됩니다. 기하/가시 표면 보정과 새 원색 톤 경계 보정은 별도로 검증해야 합니다.

## 팔레트 생성·간격

`SHARED_NATIVE_PALETTE.json`의16기준은 모두 실제 원본 texel입니다. 16은 이전 팔레트의 색수 예산이며 늘리지 않았습니다. 기존16색 그대로인 비교용 `SHARED_EXISTING16_ABLATION.json`도 별도입니다.

`perReferenceShadePaletteIndices[j]=[max(0,j-1),max(0,j-1),j,j]`입니다. 색표를 먼저 만들고 Q로 선택합니다. 간격 배율은 실제 native anchor 주위 Lab 간격에만 작용하며 selector와 Q 라벨은 바꾸지 않습니다. m=1은 native16색 안에서만 출력하고, 다른 m은 gamut 축소/명도 clamp 진단을 반환합니다. m=0/기준 단계3은 native 기준 RGB와 byte-exact입니다.

```js
const {referenceForSample,buildPalette}=require('./palette.cjs');
const P=buildPalette(model,intervalScale).tablesRGB8; // g 입력 없음
// main의 기존 미확정 여부를 먼저 처리
const ref=referenceForSample(model,{
  modelSHA256:verifiedSource.modelSHA256,
  materialId:packet.role,
  uv:selectedFeatureSourceUV, // geometryUV와 다른 경우 보존
  baseRGBAlinear:selectedFeatureSourceRGBA
},{colourGroupId:appearance,uncertain:false});
const rgb=P[ref.paletteReferenceId][existingShadeK];
// RGB 직접 출력. 연속 g 또는 source로 후단 곱셈하지 않음.
```

JS의 base 색변환/배율 함수는 같은 폴더의 `palette_math.cjs`로 동봉했습니다. 원래 `palette-v2/palette.cjs`와 byte-exact인 복사본이며 이전 파일은 수정하지 않았습니다. 후보 폴더를 함께 옮기면 기존 v2 경로 의존 없이 runtime API/HTML을 열 수 있습니다. 기본모델의 material14/다른 모델/다른 색계열/미확정에 임의 갈색 fallback을 넣지 않습니다. 실제 다른 모델/색계열에는 그 source에 맞는 별도 팔레트 모델을 생성해야 합니다.

## 고정 바인딩과 재생성

`BINDINGS.json`의 `variants.preserve/simplify.rows`는 같은 실제 입력 패킷에 대한 검사 스냅샷입니다. `mainBindingSHA256`와 `packetSHA256`가 맞을 때만 고정 ID를 재사용합니다. main이 owner/featureUV/source를 바꾸면 해당 실제 source에서 selector를 다시 실행합니다.

각 row는 `appearance`, `shadeK`, `geometryG/UV`, `sample.{materialId,uv,baseRGBAlinear}`, `oldToneClass`, `oldReferenceId`, 새 `paletteReferenceId`, RGB를 보관합니다. `sourceToneClass:null`은 기존2분류를 새 ID라고 속이지 않기 위한 명시값이며 미확정 표시가 아닙니다. 미확정 row는 `unresolved:true`이고 팔레트 경로에 들어가지 않습니다. 외부는 null입니다.

재현:

```powershell
python palette-v3/fit_native.py --source <prelight-source.json> --images <원본이미지폴더> --family <검증된SOURCE_FAMILY_INPUT.json> --output <NATIVE_COVERAGE_FIT.json>
node palette-v3/build.cjs
python palette-v3/analyse.py
node palette-v3/test.cjs
python palette-v3/verify_native.py
```

현재 build/analyse는 최신 저장 frame95의 고정 비교를 재현합니다. runtime selector/간격 API는 모델 JSON을 받습니다. 다른 모델의 색계열이 검증되지 않았는데 현재 warm-family를 자동 재사용하는 경로는 없습니다. 새 모델의 모든 색 특징 분류를 완료했다고 해석하지 않습니다.
