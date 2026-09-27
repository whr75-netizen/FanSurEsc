# B35 추가 소품 준비 계약

최종 마감에서는 사용자가 지적한 사과 바구니3개만 [실물 치수 합성 계약](tray-composite-contract.md)으로 교정했습니다. 나머지5개 신규 소품과 기존 배치 좌표는 유지했습니다. 아래는 최초 소품 추가 단계의 입력·실행 기록입니다. 최신 작업 진입점은 [PIPELINE.md](PIPELINE.md)입니다.

상태: **담당 그래프로 준비 실행·Unity 통합·실제 기술 관찰 완료, 새 소품 외형 확인 대기**. 기존 사용자 승인 20개와 원본·정규화 출력은 변경하지 않았습니다. 새 자산 5종의 계산만 이 스크립트가 맡고, 기존 트레이 재사용을 포함한 6개 배치와 실제 관찰은 `details-graph.json`과 Unity Editor API가 수행했습니다. 증거는 `docs/artifacts/building35/details`에 있습니다.

## 입력과 실제 관찰

`details-native/<source_id>/native.png` 다섯 장을 직접 열었습니다. 장부는 수직 탑다운의 열린 책과 펜 하나, 빗자루는 정면, 쓰레기통은 미리 그려진 쿼터뷰 원통/뚜껑/페달입니다. 시계와 액자는 정면 그림이며 시계 테두리는 정확한 수학적 원이 아닙니다. 아래 bbox는 기존 그림에서 alpha/255 > 0.1인 셀의 범위입니다. 원본 그림을 다시 그리거나 자르지 않습니다.

| 출력 ID | source_id / native 전체 크기 | 보이는 bbox `[l,t,r,b)` | 물리 기준과 평면 |
|---|---|---|---|
| `detail_ledger` | `top_ledger` / 161×116 | `[10,16,151,98)` = 141×82 | 폭 .38m, 깊이 `.38×82/141` = .220992908m. **Y=.02** XZ 평면 |
| `detail_clock` | `front_clock` / 146×136 | `[12,8,134,127)` = 122×119 | 폭 .34m, 높이 `.34×119/122` = .331639344m. **Z=0** XY 평면 |
| `detail_poster` | `front_poster` / 124×157 | `[17,18,107,138)` = 90×120 | 폭 .36m, 높이 .48m. **X=0** ZY 평면, 실제 그림의 3:4 비율 |
| `detail_broom` | `front_broom` / 139×125 | `[57,3,83,123)` = 26×120 | 높이 1.20m, 폭 `1.20×26/120` = .26m. **X=0** ZY 평면 |
| `detail_bin` | `bin` / 213×215 | `[60,23,153,193)` = 93×170 | 기존 upright 2D 방식. 표시 높이 .45m, `right` 방향 폭 `.45×cos30×93/170` = .213195077m |

source 경로는 모두 `docs/artifacts/building35/details-native/<source_id>/native.png`입니다. 각 폴더의 `receipt.json`이 앞선 원본 자동 PerfectPixel 실행의 증거입니다. 시계/액자는 `docs/artifacts/building35/details-landmarks.json`의 native 해시·bbox와 일치해야 합니다. 그 문서의 시계 radius/center는 관찰 보조값이며 원형 적합성 검사가 아닙니다. 이번에는 원형으로 보정하지 않고 원본 bbox 비율을 그대로 유지합니다.

장부 64×48/빗자루 높이96이라는 생성 프롬프트의 디자인 예산은 실제 자동 검출 격자와 달랐습니다. 위 native 입력을 강제로 그 크기에 맞추지 않습니다. 장부 깊이는 최초 제안 .28m 대신 **실제 원본 비율에 따른 .220992908m**로 고정한 담당 작업의 정정을 반영했습니다.

## source 셀과 canonical 평면

source 좌상 첫 픽셀 **중심**은 (0,0), x는 오른쪽, y는 아래입니다. bbox의 마지막 두 수는 exclusive이므로 전체 셀을 포함하는 source 네 모서리는 다음과 같습니다.

`[(l-.5,t-.5), (r-.5,t-.5), (r-.5,b-.5), (l-.5,b-.5)]`

순서는 TL, TR, BR, BL입니다. bbox 중심만 끼워 맞추지 않습니다. source bbox 네 점에 대응하는 미터 좌표는 다음 고정 규칙입니다. W/H는 위 표의 폭과 높이/깊이입니다.

| 종류 | TL / TR / BR / BL의 local XYZ |
|---|---|
| 장부 | `(-W/2,.02,+H/2)`, `(+W/2,.02,+H/2)`, `(+W/2,.02,-H/2)`, `(-W/2,.02,-H/2)` |
| 뒤벽 시계 | `(-W/2,H,0)`, `(+W/2,H,0)`, `(+W/2,0,0)`, `(-W/2,0,0)` |
| 오른벽 액자/빗자루 | `(0,H,+W/2)`, `(0,H,-W/2)`, `(0,0,-W/2)`, `(0,0,+W/2)` |
| 쓰레기통 | `-right·W/2+(0,H,0)`, `+right·W/2+(0,H,0)`, `+right·W/2`, `-right·W/2` |

장부 source의 위쪽은 +Z, 오른쪽은 +X입니다. 오른벽 그림의 source 오른쪽은 -Z로 갑니다. 이는 선언한 벽면 좌표 대응이며 결과를 보고 임의 회전한 값이 아닙니다. 시계/액자/빗자루의 local 원점은 bbox 아래쪽 가운데 Y=0입니다. 장부 원점은 받침 상판이고 .02m 두께의 위 평면만 표시합니다. 시계 틀 .02m, 액자 틀 .015m, 빗자루 거치대 .04m의 벽면 이격은 담당 배치에서 명시적으로 처리하며 여기서 숨은 offset을 추가하지 않습니다.

쓰레기통은 `prepare_new.py`의 기존 upright 2D 모델을 재사용합니다. .45m는 2D 표시 높이이고 .213195077m는 원본 화면 비율을 보존하는 평면 폭입니다. 실제 3D 원통 지름/가려진 면을 복원한 값이나 Collider 지름이 아닙니다.

## 고정 계산과 alpha/depth 소유권

`details-prepare.py`는 기존 `project_faces.py`의 **R, U, homography, transform**을 import합니다. 기존 `project_faces.project()`는 alpha>=128을 선택하고 255로 바꾸므로, 기존 20개 경로는 수정하지 않고 추가 자산에만 단일 평면 RGBA writer를 둡니다.

- local pitch30/yaw45, PPU127 유지. `R=(1,0,-1)/√2`, `U=(1/(2√2),√3/2,1/(2√2))`.
- target 화면 좌표는 `127·(R·P, -U·P)`입니다. target 셀 중심에서 기존 homography의 역변환으로 source 좌표를 얻고 `rint` 최근접 표본 하나를 읽습니다.
- 보이는 bbox는 물리 크기의 기준점입니다. **전체 source 캔버스 셀 경계** `[-.5,-.5]…[Wsrc-.5,Hsrc-.5]`까지 같은 평면으로 연장합니다. 알파가 낮은 픽셀을 bbox 밖이라고 잘라내지 않습니다.
- 선택한 RGBA 값을 그대로 복사합니다. source를 binary alpha로 바꾸거나 윤곽을 팽창시키지 않습니다. 다만 물리 재표본화에서 source 셀의 중복/누락이 가능하므로 전체 source 픽셀이 모두 출력에 남는다는 뜻은 아닙니다.
- `sampled alpha/255 > .1`인 출력 셀만 `positions.rgba32f.a=1` 및 `face-id=1`입니다. 나머지 depth/face ID는 0입니다. RGBA의 낮은 alpha는 유지해도 Unity의 같은 cutoff에서는 표시되지 않습니다.
- XYZ는 색에 사용한 동일 평면과 출력 셀에서 계산합니다. 다른 상자 깊이를 붙이지 않습니다. raw XYZ 행 뒤집기는 기존 Unity `LoadRawTextureData` 하단 원점 규약을 그대로 따릅니다.
- 출력 캔버스의 floor/ceil과 2px 여백은 저장 프레임이며 물체 위치를 임의로 옮기는 offset이 아닙니다. `left`/`top`에 그 좌표를 기록합니다.

**생성 → 원본 자동 격자 정규화 → 이번 물리 투영/표본화**는 다른 단계입니다. 이번 출력은 다시 PerfectPixel에 넣지 않습니다. 행렬 잔차는 대응 계산의 수치 확인이며 디자인·내부 시점·원형 형태의 합격 증거가 아닙니다. 벽 그림은 평면 그림이고 쓰레기통은 upright 2D 아트입니다.

## 담당 그래프의 실행 계약

명령: `python -B Tools/Building35/details-prepare.py` — 기본 기존 NumPy/Pillow deps 경로를 사용하며 필요하면 `--deps`로 같은 경로를 명시할 수 있습니다. 이 문서 작성 작업에서는 명령을 실행하지 않았습니다.

새 출력은 다음뿐입니다.

- `docs/artifacts/building35/details/detail_{ledger,clock,poster,broom,bin}/`
- 각 폴더의 `native.png`, `positions.rgba32f`, `face-id.png`, `spec.json`, `receipt.json`
- `docs/artifacts/building35/details/production-manifest.json`의 `assets[{id,source_id,folder,receipt}]`

`details/` 안에 이미 있는 placement/Console 등 담당 작업의 문서는 유지합니다. 위 다섯 출력 폴더나 새 production-manifest가 이미 있으면 덮지 않고 중단합니다. 기존 B35의 production-manifest, 20개 출력, 원본 이미지와 normalized native 파일에는 쓰지 않습니다. 담당 통합 작업은 기존 셰이더의 `clip(source.a - 0.1h)`와 depth cutoff .5를 확인했으며 셰이더를 변경하지 않았습니다. 새 출력의 실제 배치/지지 관계/가림 확인은 담당 통합 작업에 남습니다.
