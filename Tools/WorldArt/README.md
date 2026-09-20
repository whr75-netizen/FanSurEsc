# 도시 표면과 입체 소품 저작 도구

## 재료 기반 D09 — 정사각 표면과 실제 3D 모델

선택·좌표 계약은 [맵 연구 D09](../../docs/references/isometric_urban_map_pipeline.md), 사물별 POI·지지면·제외 조건은 [오브젝트 카탈로그](../../docs/references/urban_object_catalog.md)를 확인합니다. D09은 정사각 표면을 실제 지형·건물 mesh에 연결하고 실제 부품으로 만든 소품을 사용합니다. 물체 전체 그림을 cube 면에 붙이지 않습니다. D08 원본과 거절된 billboard 결과는 아래의 과거 경로로 보존합니다.

현재 건축 구조는 [A27/A28 설계](../../docs/references/urban_architecture_prototype.md)로 이어졌다. 아래는 기존 재료/소품 제작 경로이며 최종 픽셀 아트 승인을 뜻하지 않는다.

[당시 D09 사용자 요청] 구현을 일시 중단하고 정확한 인수인계와 제작 방식 설명을 요청한 상태입니다. D09의 시각 디자인은 승인되지 않았으며, 이후 표현 방향과 실내 역할 분리 판단도 보류했습니다. 아래 명령은 현재 산출물의 재현 입구 설명이며 추가 생성·시각 수정의 실행 지시가 아닙니다. PixelLab이 생성한 범위는 평면 재질 16장이고 소품 형상은 Blender 스크립트로 별도 저작했습니다. 이 kit의 소품은 PixelLab 완성 픽셀 오브젝트나 외부 무료 완제품 모델을 도입한 결과가 아닙니다.

현재 경로에는 3D를 먼저 만든 다음 픽셀 이미지로 자동 교체하는 단계가 없습니다. 실행 중 물체 형상은 계속 3D mesh이며 PixelLab 재질이 그 표면에 연결됩니다. 최신 정정에서 담당AI가 픽셀 목표를 제작 편의상3D로 대체한 잘못을 인정했습니다. 다음 작업은 `docs/references/urban_pipeline_handoff.md` N01의 **픽셀 제작 계약 복구**이며, 픽셀을 원하는지 다시 묻거나 현재mesh유지를 전제로 확대하지 않습니다.

### 네이티브 표면 타일

PixelLab `create_tiles_pro` 작업 `f9eb76e3-4443-4a61-a070-7db94bcee95e`의 원본 16장은 `Assets/Art/UrbanCoherent09/Surfaces/Source/tile_0.png`부터 `tile_15.png`까지입니다. 요청·응답은 `LocalOnly/UrbanDesign09/tiles-request.json`, `tiles-receipt.json`, `tiles-completed.json`에 보존합니다. 원본은 불투명 64×64px이므로 PerfectPixel 정규화나 축소가 필요하지 않습니다.

```powershell
python -B Tools/WorldArt/pack_square_urban_kit.py
```

이 스크립트에는 CLI 옵션이 없습니다. Pillow로 고정된 D09 원본 경로를 읽어 `Surfaces/MaterialAtlas.png`와 `MaterialAtlas.json`을 만듭니다. 원본 64×64px을 그대로 복사하고 각 변에 2px edge padding을 두어 512×512 atlas에 보관합니다. SHA256, source 좌표, 작업 ID와 정규화 호출 0회를 기록하며 기존 atlas가 있으면 실행을 거부합니다. PNG 좌상단 좌표에서 Unity UV로의 Y반전은 사용하는 단계에서 한 번만 수행합니다.

64px 표면의 반복 길이는 2m, 밀도는 32texel/m입니다. 지면·건물의 표면 UV는 미터 기준이고 .2m 단차는 실제 mesh입니다. 모델 공통 재질 `Urban_Wood`는 tile8, `Urban_Brick`은 tile2를 반복 사용합니다. `Urban_MetalDark`, `Urban_MetalLight`, `Urban_Glass`, `Urban_Olive`, `Urban_Fabric`, `Urban_Ceramic`은 원본 타일의 지정 위치 색을 사용합니다. 테두리가 그려진 원본을 무봉제 금속 표면으로 늘려 붙이지 않습니다. 상세 연결은 `Assets/Editor/CoherentUrbanKitAuthoring.cs`의 `CreateMaterials()`가 소유합니다.

### 실제 부품으로 만든 모델

`create_urban_models.py`는 Blender 표준 `bpy` mesh 연산과 FBX export를 사용합니다. 기본 출력은 `Assets/Art/UrbanCoherent09/Models/`, 증거는 `LocalOnly/UrbanDesign09/`입니다. 지원 옵션은 `--output-dir`, `--evidence-dir`, `--preview`이며 Blender 인수 구분자 `--` 뒤에 전달합니다. 다음은 초기 저작용 명령이며 현재 출력이 존재하면 보존을 위해 실행을 거부합니다.

```powershell
$urbanModelScript = (Resolve-Path -LiteralPath 'Tools/WorldArt/create_urban_models.py').Path
Start-Process -FilePath 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -WindowStyle Hidden -Wait -ArgumentList @('--background', '--factory-startup', '--python', ('"' + $urbanModelScript + '"'), '--', '--preview')
```

별도 factory-startup 프로세스만 사용하므로 열린 `.blend`를 수정하지 않습니다. 출력은 `office_desk`, `storage_shelf`, `retail_shelf`, `workbench`, `wardrobe`, `sofa`, `bed`, `public_round_bin`, `wheeled_dumpster`, `bench`, `planter` FBX 11종과 `street_tree.fbx`입니다. `modelmetadata.json`에는 실제 정점 bounds, 부품 recipe, 재질, 원본 스크립트·FBX 해시와 export 옵션을 기록합니다. 모델은 바닥 중심 pivot·미터·scale1이며 Unity +X 오른쪽/+Y 높이/+Z 정면을 사용합니다. Blender에는 `(x,y,z) → (x,-z,y)`로 저작하고 표준 FBX 축 변환을 적용합니다.

각 평면 polygon의 정규직교 접선 좌표를 2m로 나누어 UV를 만들고, UV 변 길이와 실제 미터 길이의 일치를 검사합니다. 한 면에 전체 텍스처를 맞추어 늘리는 방식이 아닙니다. `model-build-report.json`은 기술 실행 기록이며 `--preview`의 `model-previews/*.png`는 Blender 형상 미리보기입니다. 실행 시간이나 미리보기만으로 전체 제작 성능·사용자 미술 승인을 판정하지 않습니다.

Unity 저작 경로는 `Assets/Editor/CoherentUrbanKitAuthoring.cs`, style은 `Assets/Art/UrbanCoherent09/CoherentUrbanStyle.asset`, prefab은 `Assets/Prefabs/World/CoherentUrban09/`입니다. `CoherentUrbanBuilding.prefab`의 용도·구역별 규칙과 소품 `CatalogId`/`AllowedZones`/개수 상한이 배치를 결정합니다. `StreetTreeVisual.prefab`은 도로 가로수의 시각 모델이며 건물 소품 후보가 아닙니다. 생성 중에는 Blender·PerfectPixel·AI를 호출하지 않습니다. 실제 맵의 디자인 승인은 아직 별도 사용자 판정입니다.

가로등은 기존 `Assets/Prefabs/Lighting/PrototypeStreetLamp.prefab`을 재사용합니다. Unity 확인 결과 MeshFilter 6개는 모두 `Library/unity default resources`의 기본 도형이며, D09에서 새 무료 완제품 에셋을 다운로드한 것이 아닙니다. 가로수 시각 모델은 위 Blender kit의 새 `street_tree`입니다.

## 보존 경로 D08 — 기존 소품 시트 추출

D08은 원본의 방향·크기와 도시 전체 외형을 사용자가 거절한 과거 결과입니다. 이 경로는 기존 재료의 추적·재현을 위해 남기며 D09의 현재 모델 제작 경로가 아닙니다.

`bake_building_props.py`는 필수 `--output-dir`, `--evidence-dir`와 선택 `--profile initial|poi_reviewed`를 받습니다. 기본 profile은 `initial`의 Bin/Shelf이며 `poi_reviewed`는 Desk/Outdoor 시트입니다. `--engine-root`, `--shelf-source`, `--desk-source`, `--outdoor-source`로 보존된 입력 위치를 지정할 수 있습니다. 기존 결과는 `Assets/Art/IsometricUrban/Gpt2/BuildingProps/`와 그 아래 `PoiReviewed/`에 있습니다. 재현할 때는 기존 결과와 겹치지 않는 새 출력·증거 경로를 지정합니다.

각 profile의 전체 시트마다 수정 PerfectPixel을 한 번 적용한 뒤 완전한 소품을 추출합니다. 원본 사본·정규화 시트·crop·SHA·엔진 호출 수를 함께 보존합니다. Dumpster는 주변 물건과 bbox가 겹쳐 독립 alpha 성분 및 샘플의 원본 좌표로 소속을 제한합니다. 당시 렌더 경로는 바닥 지지 수직 billboard였으며 완성된 여러 면의 소품에 바닥용 homography를 적용하지 않았습니다.

## 보존 경로 — 기존 GPT/2 평면 타일

기존 수정 PerfectPixel을 사용합니다. 기본 엔진은 프로젝트의 `LocalOnly/PerfectPixelPalette_20260906/src/perfect_pixel`이며 `--engine-root`로 다른 보존 위치를 지정할 수 있습니다. NumPy와 Pillow가 필요합니다.

```powershell
python -B Tools/WorldArt/bake_planar_tiles.py --input Tools/WorldArt/gpt2_source_planes.json --output-dir LocalOnly/WorldArtNext --evidence-dir LocalOnly/WorldArtNextEvidence
```

출력 폴더는 새 경로로 지정합니다. 기존 출력/원본은 덮어쓰지 않습니다. 결과는 전체 정규화시트 `Sheets/`, 면 아틀라스 `PlanarTiles.png`, 좌표/출처 `PlanarTiles.json`, 처리 증거 `bake-report.json`입니다. 엔진은 전체 고유시트당 한 번 실행되며 타일 추출 뒤 재호출하지 않습니다.

입력 `source`는 manifest 기준 상대경로 또는 절대경로입니다. `points`는 원본 좌상단 기준 픽셀 중심00/01/11/10, `metres`는 실제 면의 크기입니다. `inset_native_pixels`는 전체 정규화 뒤 상면의 각 변에서 제외할 슬랩 테두리 폭입니다. 모든 면을 자동 인식하는 도구가 아니며 면 좌표는 저작 데이터입니다.

이전 경로의 값은 원본4×4px당 전체시트1px, 최종32texel/m, atlas512×512, edge padding2px입니다. 원본 알파>=128을255로 정하고 색·명암 생성/평균화는 하지 않습니다. planar nearest lookup, 투명면/잘못된 좌표 실패, 입력 해시 보존을 사용합니다. 무봉제 패턴 생성은 포함하지 않습니다.

기존 Unity atlas는 Point/Clamp/압축없음/mipmap없음/NPOT None으로 임포트해 `Gpt2IsometricStyle.asset`에 metadata의 patch를 연결했습니다. 보존 결과는 `Assets/Art/IsometricUrban/Gpt2/WholeSheetNormalized`입니다. D09과 원본·style·출력을 혼용하지 않습니다.
