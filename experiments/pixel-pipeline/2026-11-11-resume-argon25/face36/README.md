# 얼굴 곡면·명암 영역 resolver34–36

기준 `3ae55c7b`. 최신 구현은 `SourceArea36.compute::ResolveArea36`, 실제 실행 원문은 **`fix1/capture/RUN.cs.txt`** 입니다. 제품77과 사용자30 파일은 바꾸지 않았고, 얼굴 최종 RGB·외곽선·UV 색 영역 완성을 주장하지 않습니다.

## 확인한 원인과 구현

- **34 실제 비교:** 같은 프레임59셀의 기하/effective 법선 차이는 중앙값1.31045°/최대10.96250°였습니다. 어느 법선을 써도 safe0/eligible0, 실제 기각 셀도 같았습니다. 따라서 “노멀맵 제거로 해결” 가설은 기각했습니다. `analyze_normals34.py`/`face34/analysis/NORMAL_COMPARISON34.json`이 근거입니다.
- `surface_paths34.py::UVSurface.path/native`는 원본 renderer/UV/index SHA가 일치한 face primitive 안에서 실제 공유 edge를 통과하는 UV 선분만 확인합니다. 실제 이웃177쌍 중169확인/8미확정, 최대28triangle 방문입니다.16CPU반례는 끊어진/중첩 UV섬·nonmanifold·퇴화·D4를 포함합니다. 이 연속성으로 평면 gate를 대체하는 반례에서도 safe17/실제Q변경0이라 채택하지 않았습니다. **carrier 연결은 색 영역/중간 가시성의 증명이 아닙니다.**
- **35 실제 고밀도 명암:** `FineSourceLight35.shader`는 원본 재질/메쉬/동일 조명에서8× source fragment light/Q/meta를 직접 그립니다. SV_Position은`raster.xy/8+headROIOrigin`입니다. coarse Q의 보간이나 RGB 블러가 아닙니다. `(218,54)`는 중심Q=.5이나 실제64표본은0이37/.5가27로, 평면 gate 대신 셀 내부 영역을 검사할 근거가 나왔습니다. source colour·Q·가림은 별도입니다.
- **36 runtime resolver:** 현재 Q0를 보존하고 별도Qprime 제안만 만듭니다. 전체64표본이 확인된 동일face/owner이고 라벨이 인접 단계일 때 source-area 최대 라벨을 선택합니다. 일부 가림/unknown1표본이라도 있거나, 동률/원래라벨의 source 표본 부재/여러 경계 arc면 보존합니다. 원본 색·RGB·팔레트 간격은 계산에 없습니다. 새로운 eye cell 수나 갈색 상수도 없습니다.
- HLSL CPU 컴파일은8×8/배열선언0/loop token0/2733정적 instruction입니다. fixed64 source samples+28 border comparisons이며 BVH·열거·115평가가 없습니다. 이는 GPU 시간을 보장하는 수치가 아닙니다. synth16검사에는 partial/tie/다중arc/불연속단계/미관측라벨/D4가 있습니다.
- shader-only import는 새 `SourceBoundary35/FineSourceLight35.shader`, `SourceBoundary36/SourceArea36.compute` 두 자산뿐입니다. 외부 C# 동적 컴파일, C# Assets import/프로젝트 재컴파일0입니다. 원래 renderer 설정·재질·씬을 활성 후보로 바꾸지 않았습니다.

## 실제 GPU 검증과 실패를 구분

- 첫36 실행은6개 GPU 생산 뒤 field18(논리 출력)을 fine 크기로 읽으려는 **관찰기 ROI 오류**가 제출 전 검사에서 차단됐습니다. 실패는 `capture/FAILED.json` 그대로 보존합니다. 새 장치/URP 오류가 아니었고 정상 종료·pending0·자원/입력/옵션 복원을 확인한 뒤만 재개했습니다.
- `repair_readback36.py`는 index로 크기를 추측하는 대신 **`SourceOutline36.FieldExtent36`의 실제 소유 RT 크기**를 사용하게 고쳤습니다. 실패 실행의 소스·marker는 덮어쓰지 않았습니다. 최신은 `fix1/capture`이며 계산 셰이더는 같습니다.
- 정상 재검증은 실제 Unity frame95–100 **6연속**입니다. C# cohort 한 소유자가 같은 camera에서 매프레임 서로 다른 private output을 고정합니다. producer end ack 뒤 readback50개를1개씩/최대262144B로 읽고, 모든 consumer 완료 뒤 정상 종료/해제를 확인했습니다. CPU 기대값을 GPU에 올리지 않았습니다.
- 첫 프레임812셀의 실제 GPU RGBA 출력이 독립 source fine 표본 CPU oracle와 **바이트 단위 전부 일치**, 추가 watch6회도 일치했습니다. 변경 셀은 프레임별 **1/0/2/0/0/0**입니다. 첫 프레임 source-area 오분류는168→162 fine 표본(−.09375셀 상당). 관측6프레임에서 각 명암 라벨의4연결 성분 수/단독셀 수는 증가하지 않았고, non-face 변경0입니다. 이 reference는 실제 source 조명이지 미술 정답이 아닙니다.
- **시간 한계:** 정상 Animator가 진행했고 deltaTime=.3333s, source pose도 바뀝니다. 같은 화면점 `(218,54)`의 UV 범위 변화는(.001789,.027633)입니다. 같은 화면점의 Q가 일정하다고 같은 source 특징의 시간 안정성이 검증됐다고 하지 않습니다. source UV/barycentric anchor 대응과 통제된 pose/위상 검사가 다음 독립 단계입니다. temporal RGB averaging/history 고정은 하지 않았습니다.
- `analysis/SIX_ACTUAL_FRAMES36.png` 및 webp를 직접 검수했습니다. 왼쪽은 **실제 기존 RGB**, 오른쪽들은 **Q metadata 미리보기**입니다. 새로운 finite RGB/outline 결과인 것처럼 표시하지 않습니다.

## 남은 색/선 계약

face colour-region을 face material ID 또는 UV carrier와 동일시하지 않습니다. 원본 face texture에는 opacity1 RGB11941색(이미지 전체, visible face 수치가 아님)이 있고 현재 visible source sample은51색 수준입니다. source parent/child의 gradient·AA·작은 칠을 구분하는 규칙은 아직 확정되지 않았습니다. 기존104 parent36개는 볼 child를 합쳤고, source extrema28의3scale 일치도2366성분/1317단독texel이라 이를 전부 family로 만들 수도 없습니다. 단순 threshold나 색 bin 반복은 하지 않았습니다.

`ResolvedRegionInput.Build/LookupRGB8`의 확정 source-region→LUT 계약은 재사용할 수 있지만, 의미를 모르는 colour-region에 `confirmed=true`를 달지 않았습니다. native pigment texture는 opaque texel0(최대alpha254)여서 opaque-interior LUT 계약으로 그대로 통과시킬 수도 없습니다. 별도 layer/coverage와 discrete 최종 owner가 필요합니다. 원본 MToon outline은 실제 colour/width가 있으나19셀 모두 fractional이고 최대coverage=.0625라 area-majority는 선을 없앱니다. 명암 영역의 area resolver를 그대로 중요 선/눈에 적용하지 않습니다.

따라서 다음 검토는 (1) 강한 parent 안의 연속 colour field와 약하지만 일관된 child를 어떤 source-preserving 목적함수/계층으로 팔레트 family에 연결할지, (2) 얇은 원본 curve의 discrete 경로/partial-alpha owner를 어떤 topology 계약으로 정할지입니다. 이는 셀 수를 새로 고르라는 질문이 아닙니다. 자동 추상화 불가능의 증명도 아닙니다. 현재 코드의 확정 규칙이 비어 있는 곳을 표시한 것입니다.

## 보존

34/35/36실패/36fix1 모두 정상 Edit 복귀·소유자원 release/pending0, 입력 동일참조/JSON22/장치·globals74·옵션/time/pipeline·scene clean을 확인했습니다. 각 native snapshot은46내용 동일/ProjectSettings.asset의 AssetImporter1만 미로드 Unavailable이며 PlayerSettings 본체는 같습니다. 12:17:30UTC 마지막 공식 조회는 Edit/not compiling/not transitioning/GameMap1 clean/dirty31/input568105589213756420/optionsfalseNone입니다. Console12항목은33 사전 목록과 동일한 과거 오류입니다.

마지막 성공 실행 Profiler allocated−78.65MiB/reserved+.125MiB/Mono−97.89MiB, RT30→30입니다. 중간 입력/원래 renderer의 allocation·대형 동기 readback도 섞여 있으므로 누수 해소/성능 개선을 주장하지 않습니다. CUA/kill/reset/SaveAssets/GC/driver/TDR/InputSettings교체/push0입니다.
