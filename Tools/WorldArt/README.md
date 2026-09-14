# 원본 시트에서 맵 타일 만들기

기존 수정 PerfectPixel을 사용합니다. 기본 엔진은 프로젝트의 `LocalOnly/PerfectPixelPalette_20260906/src/perfect_pixel`이며 `--engine-root`로 다른 보존 위치를 지정할 수 있습니다. NumPy와 Pillow가 필요합니다.

```powershell
python -B Tools/WorldArt/bake_planar_tiles.py --input Tools/WorldArt/gpt2_source_planes.json --output-dir LocalOnly/WorldArtNext --evidence-dir LocalOnly/WorldArtNextEvidence
```

출력 폴더는 새 경로로 지정합니다. 기존 출력/원본은 덮어쓰지 않습니다. 결과는 전체 정규화시트 `Sheets/`, 면 아틀라스 `PlanarTiles.png`, 좌표/출처 `PlanarTiles.json`, 처리 증거 `bake-report.json`입니다. 엔진은 전체 고유시트당 한 번 실행되며 타일 추출 뒤 재호출하지 않습니다.

입력 `source`는 manifest 기준 상대경로 또는 절대경로입니다. `points`는 원본 좌상단 기준 픽셀 중심00/01/11/10, `metres`는 실제 면의 크기입니다. `inset_native_pixels`는 전체 정규화 뒤 상면의 각 변에서 제외할 슬랩 테두리 폭입니다. 모든 면을 자동 인식하는 도구가 아니며 면 좌표는 저작 데이터입니다.

현재 값은 원본4×4px당 전체시트1px, 최종32texel/m, atlas512×512, edge padding2px입니다. 원본 알파>=128을255로 정하고 색·명암 생성/평균화는 하지 않습니다. planar nearest lookup, 투명면/잘못된 좌표 실패, 입력 해시 보존을 사용합니다. 무봉제 패턴 생성은 포함하지 않습니다.

Unity에서는 새 atlas를 Point/Clamp/압축없음/mipmap없음/NPOT None으로 임포트한 뒤 `Gpt2IsometricStyle.asset`에 metadata의 patch를 연결합니다. 현재 연결 결과는 `Assets/Art/IsometricUrban/Gpt2/WholeSheetNormalized`입니다. 맵 생성 중에는 처리 엔진/AI가 실행되지 않습니다.
