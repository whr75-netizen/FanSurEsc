# GPT/2 등각 타일과 진입형 건물

## 현재 결정 D18 — 승인된 무늬·내부 면경계·픽셀 세부 폭의 Blender 책상

생성 이미지의 디자인 방향만 참고하고 치수·부품·재질을 수정해 재렌더할 수 있는 실제 책상 원본을 만든다. 방향은 이번 범위 밖이며 한 시점으로 제작한다. D11의 임의64×64축소 결과는 거절되었다. 새 계약·좌표식·최소 실험·실행 상태는 [PixelDesk](../../Tools/PixelDesk/README.md)에 둔다. 생성형 이미지 자체를 최종 오브젝트로 대체하지 않는다. D10 기존 캐시·게임 씬은 보존한다.

D12의albedo5색재분류,D13-flat의전체명암축소,D14새무늬,D16명암소실은거절됐다. D17방향·가림명암은조금나아졌으나내부면경계/작은세부수정요청으로D18을제작했다. 승인나뭇결·전체치수·카메라를보존하고visible면ID1px선과투영최소폭을적용했으며실제렌더/저장재현확인까지전달한다. 불필요한확인질문없이최신요구를수행하며디자인합격은선언하지않는다. [현재 계약/실행](../../Tools/PixelDesk/INTERNAL_EDGE_PLAN.md), [명암 계약](../../Tools/PixelDesk/CONTROL_SHADOW_PLAN.md). Radical Fish Games 기술은 [종합 보고서](radical_fish_technical_report.md)에정리했고Unity구현으로채택하지않았다.

## 이전 결정 D10 — 고정 시점의 오브젝트 픽셀 캐시 시험

[확정·2026-09-20] 사용자는 기존 3D도 깨끗한 픽셀아트로 표현된다면 제작 입력으로 허용했다. 고정 각도 또는 정해진 몇 방향 회전이 가능하다. 색·투명 영역·실루엣·외곽선의 픽셀 크기를 통일한다. 전체 화면에 모자이크만 적용하는 경로는 채택하지 않는다. 디자인 참고작의 단일 원본은 GDD §14.1.0이다.

### 후보와 선택

| 후보 | 현재 입력에 대한 판단 / 실패조건 |
|---|---|
| 전체화면 색/깊이 양자화 | 가장 작은 변경이나 화면 이동 시 coverage가 바뀐다. 이번 목표의 단독 해결책에서 제외. |
| 직교 카메라·렌더 위치 snap + 저해상도 실시간 렌더 | 고정 회전의 평행 이동 안정화가 가능. 조명·변형은 실시간이지만 회전/비정수 zoom의 재샘플링은 남는다. 후보 유지. |
| 오브젝트별 방향별 RGBA/깊이 캐시 | **최소 실험 채택.** 현재 고정/유한 시점 요구에서 같은 그림을 재사용한다. 캐시 생성 비용을 플레이마다 내지 않는다. 캐시 용량·화면 fill-rate·상태 조합은 비용으로 남는다. |
| Octahedral impostor | 연속 시점 보간에서 ghosting·근거리 parallax 문제가 있으며 픽셀색 혼합도 생긴다. 가까운 실내의 주 표현으로 채택하지 않는다. |
| Texel splatting / cubemap probe | 3D 위치에 샘플을 고정하는 연구 경로. 숨은 면/프로브 전환·추가 캡처 비용이 남고 현재 URP에 준비된 구현이 아니다. 고정 시점 시험보다 우선하지 않는다. |

근거: [Unity Pixel Perfect의 PPU/point/정수 배율](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/2d-pixelperfect-ref.html), [ProPixelizer의 직교·공통 격자·ID 외곽선](https://sites.google.com/view/propixelizer/user-guide), [Holland의 camera snap와 화면 보상](https://www.davidhol.land/articles/3d-pixel-art-rendering/), [Amplify 공식 impostor 한계](https://wiki.amplify.pt/index.php?title=Unity_Products%3AAmplify_Impostors%2FManual), [Texel Splatting 원문](https://arxiv.org/html/2603.14587v1). 참고 구현/논문 수치를 이 프로젝트의 성능으로 옮기지 않는다. ProPixelizer/Amplify는 설치하지 않았으며 Unity 6000.5/URP17.5 호환 실행 증거도 없다.

### 좌표·변환·캐시 계약 (구현 전)

`기존 mesh local → source.localToWorld → root.worldToLocal → canonical object(m) → 고정 bake view → orthographic clip → RGBA + eye-depth(texel) → alpha 외곽선 → 캐시 → point 정수 확대`

- canonical은 기존 root 원점/축/미터를 유지한다. Unity +X right/+Y up/+Z forward, 부모는 원본 root. quaternion camera 회전 `Euler(30,45+90*i,0)`(도 단위, i=0..3)은 시험 시점이며 최종 각도 승인은 아니다. source의 상위 scale은 위 행렬에서 한 번만 적용한다. 본·retargeting은 정적 도시 시험에 해당하지 않는다.
- view의 right/up/forward는 회전 quaternion의 정규직교 기저. 투영 범위는 모든 변환된 mesh bounds 모서리에서 계산하고, X/Y 최솟값을 1/P, 최댓값을 1/P 단위로 내림/올림한 뒤 2texel 여백을 둔다. **P=32 texel/m**를 모든 물체에 공통 적용하며 물체별 fit-to-square/비균일 resize는 금지한다.
- 영상 원점은 좌하단, sample은 `(i+.5,j+.5)`, 저장 PNG 표시 시 Y 방향은 API 규약으로 한 번만 변환한다. `W=(xmax-xmin)*P`, `H=(ymax-ymin)*P`, `orthoSize=H/(2P)`, aspect=W/H. pivot은 `(-xmin*P,-ymin*P)`로 저장한다. 공통 root를 가진 벽/지붕/실내는 같은 canvas/pivot을 쓴다.
- coverage는 MSAA 없는 같은 캡처 alpha에서 얻는다. `M=alpha>=.5`, 외곽선은 같은 격자의 `Dilate8(M,1)-M`. 색을 별도 확대/alpha를 고해상도로 다시 그리지 않는다. 합친 건물의 외곽선은 합성 coverage에서만 만든다. 벽 파츠마다 겹치는 내부 테두리를 만들지 않는다.
- depth는 색과 같은 카메라/크기/coverage의 eye-depth(float, meter)다. 실게임 통합 시 `p=origin+right*x+up*y+forward*depth`에서 world/clip depth를 복원해야 한다. 평면 PNG 또는 sortingOrder를 올리는 것으로 3D 가림을 대체할 수 없다.
- 캐시 키에는 geometry/material/texture 내용, PPU, 시점, 조명/표현 버전, 숨김 상태가 필요하다. 현재 최소 실험은 고정 주광을 구운 PNG이며 낮밤/동적 그림자를 보존했다고 주장하지 않는다. 향후 albedo/normal/depth로 조명을 분리하거나 유한 조명 상태를 cache해야 한다.
- 정수 배율 k에서 texel 하나는 k×k display pixel. 비정수 zoom/임의 회전은 캐시의 무손실 표시 범위 밖이다. 런타임 렌더 anchor의 픽셀 위상까지 맞춰야 하며 물리 Transform을 snap하지 않는다.

### 최소 실험과 실패 판정

기존 12개 소품과 실제 생성 건물 1개의 4시점 캐시 및 벽/지붕/실내 분리 입력을 만든다. 오브젝트 기준 캐시 재사용 미리보기를 제공하고, 도시 전체 렌더 교체 전에 사용자 시각 피드백을 받는다. 원본 모델/씬/게임 카메라/기존 후처리는 바꾸지 않는다.

- G03/G04: view basis 내적/단위 오차 ≤1e-5, det 오차 ≤1e-5. G08/G09: PPU32, 두 축 배율 동일, canvas 내 투영 bounds 보존(2px 여백). NaN/누락 즉시 실패.
- G10/G11: 투영 origin/pivot의 독립식과 Camera.WorldToViewportPoint 차이 ≤0.01px. 색/depth 크기·시점 동일, 저장 alpha와 깊이 유효 영역 일치.
- G12: alpha는 0/255, outline은 명시된 dilation 차집합, 정수 확대 결과의 모든 k×k cell은 원 texel과 동일. 이 검사는 원본 미술 품질이나 도시 통합 성공을 뜻하지 않는다.
- 최적성은 조건부 선택이다. 생성 시간/캐시 byte 수를 실제 측정하고 게임 GPU/draw call은 통합 전 미측정으로 남긴다. 동일 PNG를 다시 PNG로 바꾸는 작업을 새 생성 증거로 삼지 않는다.

### 실험 증거 / 남은 단계

[Play Mode 호출 확인] `PixelSpriteCacheBaker.Bake()`가 실제 prefab 12종과 생성된 Medical 건물 mesh/material을 읽어 4방향 92개 color/depth 쌍을 만들었다. 건물 whole 외에도 8개 개별 floor/wall/roof 버퍼를 같은 canvas/pivot으로 저장했다. `LocalOnly/UrbanPixelCache10/manifest.json`, `preview.html`, `preview-technical.json`에 보존한다. 최초 depth raw row가 PNG와 반대인 반례는 `initial-readback/`에 보존하고 저장 행 방향을 통일했다. 수정 캡처 2.417초, PNG+비압축 float depth 48,131,508 bytes. 이 수치는 편집기 bake이며 게임 FPS/VRAM 측정은 아니다.

투영 원점 최대 오차 0.00006652px, 공통 PPU32/유한 depth/coverage 유효 영역/alpha0·255를 확인했다. 미리보기는 같은 alpha에서 한 texel 외곽선을 계산하고 정확한 2×2 반복을 확인했다. 물체마다 같은 사각형에 fit하지 않는다. 위치 이동 미리보기는 캐시를 정수 texel 이동하며 새 그림을 생성하지 않는다. 게임 카메라 각도/zoom과 물리 Transform은 아직 바꾸지 않았다.

현재 출력은 고정 주광의 5단계 명암이다. **도시 전체 픽셀 렌더·캐릭터 앞뒤/실내 depth 합성·건물 fade·동적 낮밤/그림자·게임 GPU 최적화는 미완료**다. whole PNG의 단순 평면화는 가림을 보존하지 못하므로 통합하지 않았다. 사용자 외형 판정 후 depth 합성/파츠 숨김과 조명 분리의 최소 통합으로 이어간다. 원본 D09와 기존 비활성 전체화면 효과는 보존했다.

## 이전 결정 D09 — 정사각 표면·실제 입체 소품·블록과 POI 문법

[사용자 요청/최신 정정] 도심 일관성·정사각 픽셀 재료·POI/사물 연결을 요청했고 PixelLab 사용을 허용했다. 그러나 담당AI가 픽셀 목표의 충족 없이 실제3D형상 제작을 채택했고 사용자는 이를 지적했다. D09는 기술관측이 있는 **요구에서 벗어난 시험 구현**으로 중단한다. 아래 선택/수치는 담당AI의 당시 설계이며 사용자확정이나미술완료가아니다. 다음 작업은 [인수인계](urban_pipeline_handoff.md) N01의 픽셀 제작 계약 복구부터다.

### 입력 적합성과 선택

| 완전한 경로 후보 | 판정·근거·실패조건 |
|---|---|
| 정사각 surface → 실제 높이 mesh/미터 UV → 3D object prefab → 기존 3D camera | 채택. .2m 단차, 출입, 자유 yaw/pitch와 같은 기하학을 공유한다. 물체 전체 그림을 cube 면에 붙이지 않고 물체의 실제 부분 형상과 재질을 저작한다. |
| 고정뷰 sprite/Isometric Tilemap → sprite 객체 → 고정 카메라 | 보류. source 투영과 카메라가 일치해야 한다. 현재 자유 카메라를 제한하는 별도 결정이 필요하다. |
| 다방향 sprite → yaw/elevation 선택 → billboard depth | 보류. 현재 yaw만 다른 그림으로는 pitch10–80°를 처리하지 못한다. 시점별 일치·깊이·가림과 저작량이 추가된다. |

Unity [Grid](https://docs.unity3d.com/6000.5/Documentation/Manual/tilemaps/grid-reference.html), [Tilemap](https://docs.unity3d.com/6000.5/Documentation/Manual/tilemaps/work-with-tilemaps/tilemap-reference.html)은 셀·표시 방향을 제공한다. [RuleTile](https://docs.unity3d.com/Packages/com.unity.2d.tilemap.extras@8.0/manual/RuleTile.html)과 [AutoTile](https://docs.unity3d.com/Packages/com.unity.2d.tilemap.extras@8.0/manual/AutoTile.html)은 이웃 mask에서 타일 출력을 고른다. 이웃 선택은 재사용 가능한 개념이지만 실제 .2m 측면/Collider/NavMesh가 자동 생성된다는 뜻은 아니다. 기존 SurfaceGrid 권위를 유지하며 별도 Tilemap Manager를 만들지 않는다. 새 패키지는 설치하지 않는다.

PixelLab [Tiles Pro](https://www.pixellab.ai/docs/tools/create-tiles-pro)는 square top-down·재료 변형·style reference를 지원한다. [공식 MCP](https://www.pixellab.ai/docs/ways-to-use-pixellab)의 실제 tools/list에서 create_tiles_pro/get_tiles_pro를 확인했다. 생성 request/receipt와 원본을 보존한다. 생성은 재료 단계이며 도로/건물 설계나 런타임에 AI를 호출하지 않는다.

### 도시 알고리즘과 실제 부족 단계

직접 코드 확인: 기존 고정 road graph + Kruskal + loop/diagonal 다음에 작은 동일 필지를 나열하며, 실제 block 자료형은 없고 diagonal frontage는 continue로 제외한다. 차도14/18m, node간40m, 본체8–10×8m이므로 양측 여유를 가진 건물 두 줄이 기본 블록에 들어갈 수 없다. 그림 크기 조절로 해결할 문제가 아니다.

[Parish/Müller](https://cgl.ethz.ch/Downloads/Publications/Papers/2001/p_Par01.pdf), [Chen et al.](https://www.peterwonka.net/Publications/pdfs/2008.SG.Chen.InteractiveProceduralStreetModeling.pdf), [ProbableTrain/MapGenerator](https://github.com/ProbableTrain/MapGenerator)의 도로→블록→필지→건물 분리를 참고한다. 이번 구현은 이들의 연속 polygon 코드를 복사한 것이 아니라, 현재 2m 지형 권위에 맞춘 **raster connected-component block + oriented parcel** 경로다. 도로 성장 전체 교체는 현재의 빠진 블록/필지 단계를 해결하는 선행조건이 아니다.

1. 차선 의미와 grid 해상도를 분리한다. 시험 차도는 보조6m/주요10m, 보도2m, node간48m다. 40m에서는 최소15×13m 예약필지가 대각 삼각영역에 들어가지 않는 반례를 확인해 전체290m를 유지하고 node분할6→5로 바꿨다. 도로 연결/진입/탈출 anchor는 기존 소유자가 유지한다.
2. 실제 Ground 셀의 4-neighbor connected component가 BlockId를 소유한다. 도로·보도·경계가 컴포넌트를 나눈다. 막다른 길 주변은 한 연결 블록이다.
3. 도로 방향에서 정규직교 frontage frame을 만든다. cardinal/diagonal을 같은 식으로 처리하고, local width/depth를 가진 reserved OBB를 배치한다. 교차하는 셀이 모두 같은 Ground BlockId이며 다른 필지와 겹치지 않아야 한다.
4. 건물 본체·출입구·서비스 여유는 필지 frame을 공유한다. 본체 치수는 프로그램별 frontage/depth와 필지 수용 공간에서 결정하며 개별 이미지 scale로 보정하지 않는다.
5. 모든 건물에 명시적 용도/POI를 배정하고, 그 용도의 구역별 허용 소품·가중치·개수·접근 여유를 적용한다. 기존 Medical loot 소유권은 유지하고 새 POI의 전리품·보상은 추가하지 않는다.
6. 출입구→중앙 통로→업무/보관 구역 접근을 보존한다. 소품이 안 들어가면 그 후보를 제외하며 벽/문에 밀어 넣지 않는다.

### 좌표·변환·시각 규격

`PixelLab native square PNG → atlas texel centre → metric planar UV → local surface/object mesh → parcel rigid frame → world → existing view/projection → screen`

| 공간 | 원점·축·단위·상위 |
|---|---|
| 원본 이미지 | 좌상단 pixel centre, +X오른쪽/+Y아래, px, 상위 없음 |
| 표면 UV | local 평면의 원점, 단위 접선 e1/e2, uv/texel, 표면 local |
| 물체 canonical | 지면 바닥 중심, Unity +X오른쪽/+Y위/+Z물체정면, m, 필지/건물 local |
| 필지 | 중심, road tangent와 건물정면 법선, m, map local XZ |
| world/view | Unity 좌표·Quaternion Y회전(도), localToWorldMatrix→camera view/projection, m→clip→px |

밀도 ρ=32texel/m, N=64px이면 반복길이 L=N/ρ=2m다. 표면 좌표는 s=(p−O)·e1, t=(p−O)·e2이고 UV는 (s/L,t/L). PNG Y반전은 atlas 변환에서 1회만 한다. 0.2m 측면은 6.4texel 범위를 crop하며 64px 전체를 높이에 압축하지 않는다. 축에 정렬된 square patch는 기존 homography의 affine 특수형이며 추가 diamond 변형은 없다. [Unity mesh UV](https://docs.unity3d.com/6000.5/Documentation/Manual/mesh-vertex-data.html).

필지 local점 q는 p=c+r*q.x+f*q.y로 변환한다. r/f는 길이1·내적0이고 determinant 부호를 고정한다. 렌더·Collider·문·소품 모두 같은 transform을 쓴다. AABB는 broad phase에만 사용하며 실제 회전 겹침은 SAT/OBB로 판정한다. 단일 billboard의 source 투영이나 숨겨진 면은 복원하지 않는다.

디자인 규격은 저채도 현대 도시, 어두운 아스팔트/밝은 보도/벽돌·회벽/청록 또는 올리브 소품의 공통 재료군이다. 형태는 실제 물체 부품(책상판/다리, 선반판/기둥, 수거함 몸체/뚜껑/바퀴 등)으로 저작한다. 색·표면은 하나의 kit를 공유하고 baked cast shadow는 넣지 않는다. 2층·실제 치수·정면·floor pivot은 필수 기술 규격이며 미적 적합성은 사용자 판단이다.

### 실패·최소 실험·실행 그래프

- source에 투영/테두리/물체가 포함되거나 생성 연결이 불명확하면 해당 재료를 통합하지 않는다. 요청 원본과 실제 receipt를 검사한다.
- diagonal parcel의 cell/OBB 판정 누락, reserved 교차, 문/실내 물체에 서로 다른 frame 적용, 월드 scale 비균일, 범위를 벗어난 model vertex는 실패다. 근거 없는 offset을 추가하지 않는다.
- 대표 seed의 실제 block/diagonal 접도·POI 배정·반복 hash, 실내외 Collider·문 이동/NavMesh, .2m 높이를 마지막에 함께 확인한다. 입체 소품과 바닥은 yaw4방향·pitch10/기준/80에서 같은 기하를 투영하는지 본다. 카메라를 source에 맞추어 제한하지 않는다.
- WorkLoop: 설계→신규 재료 요청→도시 layout→재료/모델 수집→POI와 렌더 통합→최종 관측→기술 판정→사용자 시각 피드백. 현재 `LocalOnly/UrbanDesign09/state-v4.json`은 사용자 요청으로paused이며 시각accepted를제출하지않았다. v2의 repair→observe입력누락과 v3이후near잘림 추가반례는 인수인계에기록했다.
- 실제 seed1462661998에서116건물/470입체소품/대각접도필지1, frame/volume오류0·벽/지붕침투0·실제문이동/경로 통과. 45Block은작은Ground연결성분포함이며45개디자인블록이아니다. 카메라6case의 near/far실패0, 화면XY차1.03e-6. 이것은픽셀외형·실내역할·도시디자인의완성이아니다. 원본/거절결과보존, 추가생성중단.

### D09 추가 반례 — 직교 카메라 near clipping

실제 생성/문/소품 검사는 통과했지만 기존 약11m 카메라 거리에서 pitch10°, zoom8의 하단 지면과 넓은 관측 뷰의 지붕이 near plane에 잘렸다. 이는 미술 취향이 아닌 투영 부피 누락이다. [Unity nearClipPlane](https://docs.unity3d.com/6000.5/Documentation/ScriptReference/Camera-nearClipPlane.html)은 해당 평면보다 가까운 기하를 표시하지 않는다.

직교 화면 좌표는 시선축 평행 이동에 불변이다. 기존 CameraFollow의 논리 offset·회전·줌을 보존하고 최종 위치만 `C'=C-d*f`로 계산한다. 생성된 Renderer bounds의 실제 world 높이 구간 `[Ymin,Ymax]`, 화면 반높이h/반폭w, camera right/up/forward r/u/f에 대해 `E=w*abs(r.y)+h*abs(u.y)`, `Nmin=C.y+near*f.y-E`, `d=max(0,(Ymax+0.01-Nmin)/(-f.y))`. 그러면 near 사각형 전체가 모든 건물보다 위에 있으므로 아래로 향한 시야의 지면/건물이 near에 잘리지 않는다. far는 `(C'.y+E-Ymin+0.01)/(-f.y)` 이상으로만 확장한다. 경계 소유 Transform이 사라지면 파생 보정과 far 확장을 해제한다. 전제는 기존 직교·pitch10~80°이며 수평/상향이나 perspective에는 이 공식을 적용하지 않는다.

관측은 화면XY 불변, 4개 near 꼭짓점의Y가Ymax 이상, far 꼭짓점Y가Ymin 이하를 zoom3.5/8×pitch10/35/80에서 확인하고 마지막 화면만 다시 캡처한다. 이미 통과한 문·물리·seed 검사를 반복하지 않는다. 이전 잘림 이미지와 WorkLoop 상태는 보존한다.

## 이전 구현 D08 — 사물 목록·POI 구역·예약 필지를 가진 건물 프리팹

[최종 사용자 판정] 수정된 POI 용도는 맞지만 **도심 디자인·이미지 크기·방향이 전체적으로 잘못됐다**고 거절했다. 전체 시각 설계가 필요한지 질문한 상태이며 추가 생산 코드/미술 보정은 중단한다. D08은 구현·제한된 기술 관측만 존재하며 미술 완료가 아니다. 원본의 투영/방향과 mesh/camera 좌표, 물리 미터와 이미지 texel 밀도, 도시의 도로/블록/건물 용도 문법을 공통 시각 규격으로 재설계해야 한다. Y축 billboard의 포함 증명은 원본의 다방향 표현·도시 디자인의 적합성을 증명하지 않는다. 현재 그림은 object yaw와 별개로 camera를 향하므로 소품의 물리 배치 방향과 그림 속 정면이 같다는 보장도 없다. 예컨대 Desk208px/1.5m와 Dumpster58px/1.2m, 지면32texel/m는 서로 다른 영상 밀도다. 이 차이는 공통 미술 규격 없이 개별 높이를 정한 한계다. 사용자 재설계 판단 전 새 그래픽 대안을 통합하지 않는다.

[최신 의미 배치 계약] 사용자는 원통형 휴지통의 외벽 반복을 거절하고 **사물 외형 확인 → 적합/부적합 장소 목록 → POI별 허용 목록과 가중치 → 배치**를 요구했다. 최초의 모든 건물 공통 bin/shelf 규칙은 폐기한다. 현재 실제 POI는 Medical 하나이므로 그 건물의 행정 업무 구역/출입구/외부 서비스 구역에만 적합한 목록을 연결하고, 미분류 건물에는 fallback 소품을 넣지 않는다. 게임플레이 POI 종류·전리품·보상은 추가하지 않는다. 금속선반은 녹색 군용 상자·연료·물·통조림·의료상자 등이 결합된 생존 보급품이며 일반 의료 진열대로 사용하지 않는다. 상세 사물 분류 목록을 별도 연결하고 그 안에서 실제 처리 가능한 재료만 사용한다.

소품 prefab catalog는 stable CatalogId, 외형에 맞는 AllowedZones, 실제 크기를 소유한다. 건물 prefab rule은 RequiredPoiKind, Zone, 발생 확률(건물/규칙당1회), 최대 수와 가중 prop 목록을 소유한다. 기존 POI 의미 데이터만 분류 권위이며 평행한 POI Manager/용도 자동추측은 만들지 않는다. planner는 실제 POI→zone→허용 catalog→공간·통로에 들어가는 후보→정규화 가중 선택 순서로 처리한다. 행정 책상은 실내 업무벽, 큰 바퀴 수거함은 출입구 반대의 서비스 외벽, 원통형 휴지통은 실내 입구에 최대1개다. 보행로의 간헐 배치는 별도 공공 구역 자료가 연결되기 전에는 만들지 않는다. 편집기 프리셋 수치는 조절 가능한 초기값이며 사용자 확정 디자인 수치가 아니다.

[최신 시각 피드백·수정 설계] 최초 camera-facing card는 사용자가 크기는 괜찮지만 벽과 겹쳐 잘린다고 재개했다. `B=foot+right*x+up*y`에서 cameraUp의 XZ 성분이 소품의 물리 footprint를 벗어난 것이 원인이다. 선반 width=2×210/288=1.45833m, pitch30°/yaw45°에서 벽법선 돌출은 width/2×cos45°+2×sin30°×cos45°=1.2227m다. 기존 반깊이.5m와 다르다. 단순 SV_Depth box clamp는 일부 불투명 pixel ray가 box를 빗나가므로 전제부터 불충족이다.

수정은 [표준 constrained billboard](https://learn.microsoft.com/en-us/dotnet/api/system.numerics.matrix4x4.createconstrainedbillboard)의 Y축 고정을 사용한다. `right_h=normalize(cameraRight.x,0,cameraRight.z)`, `B=foot+right_h*x+worldUp*y`. 원래 높이.9/2m와 PNG는 유지하며 카메라 고도에 따른 정상적인 수직 투영 길이 cos(pitch)를 적용한다. 화면 크기를 역보정하면 pitch80°에서 실제 card 높이가11.5m가 되므로 그 대안은 제외한다. 렌더 card의 회전 점유반경R=width/2를 모두 포함하도록 planner snapshot의 실효 footprint는 `(max(authoredWidth,2R),max(authoredDepth,2R))`다. 선반의 실효 깊이는1→1.45833m, 쓰레기통은불변이며 같은 치수로 배치/Collider/NavMesh/hash를 파생한다. 이는 소품별 임의 offset이 아니라 하나의 포함 조건이다. world Y 범위도0~실물높이 안이므로 외벽/천장과 교차하지 않는지 마지막에 전체card 정점의 실제벽 OBB 검사와 화면으로 확인한다. 최초 결과/증거는 보존하고 재개된 렌더·점유범위만 검사한다.

### D08 현재 연결·실행 증거

- [사물 목록] [urban_object_catalog.md](urban_object_catalog.md)에 원본36장 중 사물/환경13장과 그 안의 물건별 적합 POI·구역·지지면·금지 장소·추출 한계를 기록했다. 구조재6장/캐릭터17장은 별도다. 목록의 후속 후보가 모두 runtime asset이 됐다는 뜻은 아니다.
- [실제 asset] `Assets/Prefabs/World/UrbanBuildings/FurnishedMetricBuilding.prefab`이 catalog와 규칙을 소유하고 GameMapTest 생성기의 serialized reference로 연결됐다. Bin/Shelf/Desk/Dumpster도 실제 prefab이며 공통 생성기는 같은 metric 건물과 그 자식으로 인스턴스화한다. 현재 규칙은 Medical 행정책상1(발생1), 뒤편수거함1(발생1), 실내입구휴지통최대1(발생.35)이다. source별허용Zone와Catalog별개수상한을 검증하며 생존선반은 미연결이다. 미분류 건물의 소품은0이다.
- [현재 좌표] 주변 예약margin1.5m, 본체8~10×8m/2층6.8m 유지. 책상높이1.5m/실효footprint2×1.65865m, 수거함높이1.2m/1.4×1.13793m, 원통휴지통높이.9m/.7×.7m. 실제card vertices에서 폭을 구하고 `max(저작치수,회전card폭)`으로 동일placement/Collider/해시를 만든다. culling용확대mesh.bounds를크기로사용하지않는다. Y고정card의세로압축은실제카메라투영이며부위별보정은없다.
- [정규화] 최초Bin31×52/Shelf210×288은전체시트각1회총9.371초. 새Desk230×208/Dumpster55×58은두새시트각1회총8.043초다. 원본/이전결과SHA불변. Dumpster는원본독립alpha성분의4×4coverage를사용해정규화된2096pixel의source좌표귀속을확인했고이웃혼합셀/귀속오류0이다. `Tools/WorldArt/bake_building_props.py --profile poi_reviewed`가재현입구이며출력은`BuildingProps/PoiReviewed/`다.
- [초기 결과와 재개] 최초seed726891912에서모든건물공통bin82/shelf125배치와문/경로검사를수행했으나사용자가벽잘림과용도없는배치를거절했다. `technical.json`, `outside.png`, `inside.png`는그당시결과로보존하며최종합격증거로사용하지않는다. WorkLoop v10은당시기술조건만완료, v11은추가의미계약으로중단하고v12로통합했다.
- [최종 Play Mode 호출 확인] seed1462661998: 건물49, 실제Medical에책상1/뒤편수거함1/원통휴지통0. 전체layout/POI/Zone/Catalog상한/미분류건물빈목록검사, 같은seed재현, 확률0에서빈배치및해시변화통과. fit불가능한100×100m후보에가중치1000을줘도유효책상만선택했다. 실제card64정점case(8yaw×4vertex×2prop)가자기Collider안에있고실제모든벽/지붕과의penetration0, 같은Player의실제문통과와NavMesh입구→중앙경로를확인했다. 높이에따른XZ침투를없애므로pitch와독립적으로수평포함조건이성립한다.
- [증거/판정] `LocalOnly/IsometricMapTrial07/{semantic.json,semantic-inside.png,semantic-outside.png,poi-bake-report.json}`. 사용자에게용도는맞지만도시디자인/이미지크기/방향이잘못됐다는최종피드백을받았다. 기술gate는해당좁은조건만판정했고미술합격으로사용하지않는다. 모든방향에서원본의새면을복원한3D물체가아니라수직2.5Dcard다. 다른POI/층전환/책상위소품·벽부착/실제키보드/전체Recovery/GPU/빌드는범위밖또는미검증이다.

### 이전 도심 생성 자료의 추적 결과

사용자가9/4의 `유니티 Codex 연결 설정 찾기`에서 직접 연결한 [도심맵 생성 자료 ಹುಡುಗ](https://chatgpt.com/c/6a9a03b2-201c-83e8-a3d1-9e9b63c03acc?messageId=finalAgentTurnStart)를 찾았다. 이 작업에는 [Szuszi/CityGenerator-Unity](https://github.com/Szuszi/CityGenerator-Unity), [pboechat/roadgen](https://github.com/pboechat/roadgen), [symbios-tensor](https://github.com/TheJanusStream/symbios-tensor), [ProbableTrain/MapGenerator](https://github.com/ProbableTrain/MapGenerator)가 정리돼 있다. 각 원문은 도로/블록/필지 분리, 성장도로의교차·스냅·선분분할, 방향장추적, 지도출력 등의기법을제공한다. symbios-tensor는Rust이며퇴화블록/타일연결한계가공개되어있다.

해당두작업의사용자원문에서 **도심생성트윗URL 자체는확인하지못했다**. Astra사용량트윗과혼동하지않는다. 현재코드는이프로젝트들의통합본이아니라고정node+seed가중Kruskal+추가loop+제한대각선이며, cardinal전면Rect필지만지원한다. 방향장/닫힌face필지/대각전면필지는추가구현되지않았다. 이번변경은POI소품/프리팹예약이며도시도로생성기교체는하지않았다.

### 최초안 기록 — 사용자 피드백으로 아래 공통 소품 규칙·카메라 평면을 교체함

[최초 요청] 건물 프리팹 안에 확률과 주변 여유 범위를 넣고, 외벽에는 쓰레기통·실내에는 진열대를 배치한다. 본체 크기·2층·기존 문·도로·0.2m 단차는 유지한다. 이번 소품은 고정 장식/충돌이며 새 루팅·상태 소유자를 만들지 않는다. 아래는 최초 설계의 보존 기록이고 현재 결정은 위의 사용자 정정/실행 절이다.

후보: (1) prefab Awake의 자체 난수 배치는 필지·NavMesh·Recovery 해시 밖에서 충돌을 바꾸므로 제외, (2) 전역 거리 가구에 실내 물건을 섞으면 Sidewalk 계약을 깨므로 제외, (3) **prefab 저작 규칙 → immutable profile → 기존 planner의 예약 필지/본체/POI/소품 → 기존 generator의 실제 prefab 인스턴스**를 채택한다. Unity prefab은 재사용 가능한 저작 단위이며 확률 배치는 프로젝트의 순수 planner 책임이다. [Unity Prefab 설명](https://docs.unity3d.com/6000.0/Documentation/Manual/Prefabs.html), [NavMeshSurface](https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavMeshSurface.html)의 PhysicsColliders 경로를 사용한다.

- Canonical 표현은 맵 local XZ의 미터 단위 axis-aligned Rect와 immutable placement다. `R_reserved=R_body⊕[-m,m]²`, 초기 m=1.25m. 기존 8~10×8m 본체는 유지하고 도로 변 필지 간격을 예약 크기로 계산한다. 충돌 시 후보를 제외하므로 건물 수는 줄 수 있다. 예약 영역과 실내 바닥의 Footprint는 구분한다.
- 프리팹은 margin, 벽 두께/문 폭과 일치하는 profile, 통로 폭, stable rule ID, 출현확률, 최대 수, 가중 prop 후보/실물 크기를 소유한다. Map 생성 시작에 배열을 복사한다. 동일 seed/parcel ID/rule ID의 정수 해시로 독립 난수열을 만들고, road/building RNG를 소비하지 않는다. `p<=u`이면 빈 슬롯, 나머지는 누적 가중치로 선택한다.
- 후보는 벽에 정렬한 로컬 슬롯이며 전체 footprint로 예약 영역 포함/벽 비침범/다른 소품 비중첩을 계산한다. 실내 중앙 십자 통로와 실제 문→중앙 경로를 비운다. 의료 POI의 이동된 문 공식은 메시와 planner가 공유하고 외부 Chest 접근 구역도 제외한다. 부족한 공간을 임의 scale이나 offset 보정으로 덮지 않는다.
- 실내 root 높이=건물 root+기존 FloorLift(.016), 실외=root. 쓰레기통 초기 footprint .7×.7m/높이.9m, 진열대2.4×1m/높이2m, 통로 폭≥1.4m. 실제 solid BoxCollider와 NotWalkable NavMeshModifier를 최종 NavMesh 전에 생성한다. sprite 회전은 Collider와 분리한다.
- 이미지 입력은 기존 StreetObjects 전체 시트와 GPT/2의 단일 금속 선반이다. 각각 전체 RGBA를 D05의 수정 PerfectPixel 4px 격자로 1회 정규화한 뒤 완전한 소품의 alpha 영역을 추출한다. 원본/정규화 시트/좌표/해시를 보존한다. 완성된 여러 면의 그림에 평면 homography를 적용하지 않는다. 발끝 pivot의 camera-facing billboard를 사용하고 높이 하나로 균일 배율을 정한다. 이는 2.5D sprite 표현이며 숨은 면이나 camera orbit에 대응하는 실제 3D 복원이 아니다. 필요한 경우 후속에 방향별 sprite/실제 mesh를 저작한다.
- profile과 예약 Rect, 모든 prop ID/종류/미터 좌표/크기를 stable hash에 넣는다. planner9/geometry1006으로 기존 Recovery mismatch 차단을 재사용한다. 새 루팅 registry나 save schema는 만들지 않는다.

최종 최소 실험: 두 seed의 유효 배치, 동일 seed 재현, profile 변경 시 hash 변화, 실제 prefab 연결/문과 POI 통로의 footprint 침범0, 실내외 Collider/높이, 실제 의료 건물 문 통과와 NavMesh 경로를 확인한다. 마지막 대표 실내/외 화면의 미술 판정은 사용자에게 받는다. 기존 단차/도로/씬 왕복을 중복 테스트하지 않는다. 실패 시 해당 입력/배치/렌더 경계만 재개한다.

## 현재 결정 D07 — 이동 경계와 외곽 도로 표시 범위 분리

[요청·구현 범위] D06 결과는 사용자 유지 승인이다. 도로 끝만 재개한다. 현재 planner는 중심선 셀마다 원판 `dx²+dz²≤r²`를 합치며 외곽 node가 물리 LocalBounds보다25m 안쪽이라 원형 끝이 보인다. 기존 네 Boundary Collider와 이동 범위는 유지한다.

후보: 전체 stamp를 사각형으로 바꾸면 종료 위치는 그대로다. node를 경계로 옮기면 endpoint=node/anchor/road-fraction 배치까지 바뀐다. 기존 포장 위에 그림만 덮으면0.2m 지지면과 어긋난다. 채택은 기존 graph에서 외향 continuation을 파생하여 필지 생성 전 road mask에 합치고, 경계 밖은 표시 전용으로 확장하는 방식이다. 패키지 교체나 이미지 생성은 필요 없다.

입출력: `seed/기존 road graph(local XZ,m) → 외곽 node의 외향 tangent t/normal n → 직선 띠 → cell center 판정/road union → SurfaceGrid → 기존 높이 H/mesh/collider/필지/배치/NavMesh`. 방향은 `t=(p−q)/|p−q|`, `n=(−t.y,t.x)`. 노드 집합의 AABB 면에 놓인 p에서 해당 면의 바깥을 향하는 도로만 연장한다. 띠는 `s=(x−p)·t≥0`, `|u=(x−p)·n|≤W/2`이고 끝 길이는 대상 사각형과 ray의 양의 출구거리로 제한한다. 새 난수를 소비하거나 기존 graph/node/entry/portal을 이동하지 않는다. 타일 격자 양자화 오차는 최대 반 셀 대각선이며 source 이미지나 월드 축의 회전 보정으로 숨기지 않는다.

`PlayableBounds=기존 LocalBounds`, `DisplayBounds=PlayableBounds를 정수 타일만큼 확장`. 내부는 단일 SurfaceGrid가 권위이고 외부 종류는 같은 continuation의 파생값이다. 외부는 표시mesh만 만들고 Collider/NavMesh/spawn/POI를 만들지 않는다. 내부/외부 셀 좌표는 같은 origin/TileSize 기준 정수 좌표를 써서 재료 hash와UV 위상을 이어간다. 원본UV→D05 atlas→D06 월드/view 변환은 그대로다. 노란/흰 차선도 기존 부호정규화 tangent와 `dot(p,t)` 반복 위상을 이어가고 외곽 경계에는 횡단보도를 추가하지 않는다.

표시 여백은 직교 카메라의 허용 최대 size S/최소 하향각 φ/현재 화면비 a/카메라공간 framing offset c에서 계산한다. target 지면 높이 보수적 상한 h에서 `R=√[(|cx|+aS)²+((|cy|+S)/sinφ+h·cotφ)²]`; 타일단위로 올림하고 한타일 여유를 둔다. pitch>0 및 직교투영이 전제다. 이 공식은 yaw에 독립적인 지면 투영 반경 상한이며 무한 배경이 아니다. 화면비/카메라 지원범위를 바꾸면 표시영역을 다시 계산해야 한다. [Unity 직교 크기](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Camera-orthographicSize.html), [카메라 ray](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Camera.ViewportPointToRay.html), [Physics Colliders NavMesh 입력](https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavMeshSurface.html)을 사용한다. continuation/버퍼 연결 자체는 이 프로젝트의 명시적 파생 구현이다.

최소 실험/실패 판정: graph·anchor 불변, 기존 validator/필지 비중첩, 안팎 도로 폭/높이/UV 연결, 실제 4면 경계 CharacterController 차단, 외부Collider/NavMesh 없음, 허용카메라 지면ray가 DisplayBounds 안에 있음. 대표 seed와 방향 반례용 seed의 순수layout 검사, 실제 맵1회의 변경 경계 관찰만 모아 실행한다. 내부 막다른길·교차로 디자인/카메라제어/건물디테일/새 텍스처/전체 이동 재검증은 제외한다. 결과를 내고 사용자에게 대표 화면을 보여 준다.

### D07 실행 증거·사용자 유지 승인

- [코드/기술] planner8/등각 geometry1005. 기존 graph에서 외향 half-strip을 파생해 내부 SurfaceGrid에 합쳤다. 외부4면은 같은 격자/높이/재료좌표로 만든 표시 전용mesh이며 내부와 외부가 만나는 곳에 불필요한 연석을 만들지 않는다. 기존 네 Boundary Collider는 그대로다. Ground/Sidewalk의 승인된 같은재료 조건을 외부에도 적용하고, 외부 표시grid는 placement/graph의 원본으로 사용하지 않는다.
- [이전 구현 비교] commit2d36911의 실제 이전planner와 새planner를 같은 입력으로 실행했다. seed41721/−1243259102에서 node·road endpoint/width/type·모든 graph port·LocalBounds·entry/portal/approach 동일. continuation29/26개, 중심선1463sample 연결. 기존layout validator 통과, 필지153→145/160→154로 연장도로와 겹치는 후보를 제외했다. 이로 인해 필지/건물 배치가 이전seed와 완전히 같다는 보장은 하지 않는다.
- [Play Mode 호출 확인] 실제seed−1038015743에서 네 면의 같은Player CharacterController 이동이 경계 안1.049m 부근에서 차단됐다(벽반두께.5+반경.5+skin). 외부수직ray 충돌0/외부NavMesh sample0, 표시mesh4개Collider0, 실제surface 높이 일치, 중심선2905sample 연결, 노란/흰 차선11992정점의절대UV위상과전체SAT포함 검사 통과. 이 호출은 실제물리키보드 조작을 뜻하지 않는다.
- [카메라] 현재aspect1.299883/최대size8/최소pitch10°에서 표시여백62m. 경계4꼭짓점×yaw8×viewport4=128ray 중64개는 ray시작점 뒤쪽 교차로 실제보이는지면이 아니다. 유효64개중영역밖0, 최대지면거리50.9061m. 최초검사에서 음의ray매개변수도 실패로센검사도구오류를 카메라관찰만 수정하여 확인했다. 실제geometry나여백을보정하지 않았다. 현재실행중 화면비/지원카메라범위변경은 자동재생성하지 않으며 맵재진입때계산된다. 최소pitch의시야일부가지면을보지않는현상은 기존카메라범위의경계이고 이번도로표시기법의완성보장으로확대하지않는다.
- [근거/종료] `LocalOnly/IsometricMapTrial06/{layout.json,technical-initial.json,camera.json,technical.json,boundary.png,former-end.png}`. WorkLoop v9 최종필요gate 통과. baseline 비교용Unity코드는삭제했고원본commit은보존했다. 임시RunCommand의namespace/internal접근제한은별도임시컴파일로해결했으며production코드를그에맞춰수정하지않았다. Play종료/background설정복원. 대표화면을 보고 사용자가 현재 방식 유지, 디테일은 나중에 조절한다고 승인했다. 추가시각보정없음.
- [남은범위] 외부표시는배경이며새교차로/필지/진입영역이아니다. 외부연장끼리만나는곳에새교차로규칙을만들지않았다. 내부막다른길cap/교차로모양, 카메라시야조정, 모든seed/화면비/저장복구/GPU/빌드는 별도미검증이다. D06의재료/단차/문통과/동일Player씬왕복은변경되지않아재실행하지않았다.

## 승인된 결정 D06 — 승인된 포장 유지, 0.2m 단차·기본 계단 이동·2층 외관

[사용자 확정] D05 포장 통일은 유지한다. 인도/차도 차이는0.2m, 건물은2층, 횡단보도 줄 방향을 반대로 수정한다. D05의 평탄화는 재개방됐다. 정규화 이미지와 가중 타일 후보는 다시 생성하지 않는다.

표준 후보 비교: (1) 실제 지면Collider + Unity CharacterController.stepOffset 채택, (2) 기존XZ코드에 ground probe로 높이/천장/낙차/벽모서리를 자체 구현하는 방식은 범용동작의 자체책임이 커서 제외, (3) 시각계단+경사Collider는 긴계단용 후보이며0.2m연석에는 불필요하다. [CharacterController](https://docs.unity3d.com/6000.0/Documentation/Manual/class-CharacterController.html)는 Move 호출에서 허용단차/경사/충돌을 처리하고 [Move](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/CharacterController.Move.html)는 중력을 자동적용하지 않는다. [NavMeshSurface](https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavMeshSurface.html)는 현재 PhysicsColliders를 입력으로 사용한다.

좌표/단위/텍스처 변환은 D05를 유지하고 높이의 원본은 기존 SurfaceGrid 종류다. `H(cell)=0(road), .2m(ground/sidewalk)` → 동일H의 윗면/외부경계 수직면/지면MeshCollider → 건물root/가로시설/spawn 지지면 → NavMesh를 파생한다. 같은 포장 두셀 사이에는 수직경계를 만들지 않는다. 내부바닥은 건물root의 기존+.016m, road 표시는 기존+.012m다. 건물높이는 계획입력부터2×층고3.4=6.8m이며 이미지scale로 낮추지 않는다. 새 물리표현/version과 관련height hash를 구분한다.

기존 동일Player/PlayerMovement가 단독으로 CharacterController.Move를 호출한다. 기존 동적Rigidbody는 같은 컴포넌트를 유지하되 kinematic으로 전환하고 기존1m box는 비활성하여 이동충돌을 이중계산하지 않는다. 기존 상호작용Sphere trigger와 게임컴포넌트/Camera/Animator/입력차단은 유지한다. Capsule은 실제외형1.8m,반경.5m,feet가기존root-.5가되도록centerY=.4,skinWidth=.05,stepOffset=.3m,slopeLimit45°,minMoveDistance0을 사용한다. 물리이동은 표준solid Collider/trigger구분을 사용하며 동적몸체와 Transform이 동시위치를 쓰지 않는다.

접지상태에서 음의 수직속도를 재설정하고 명시적중력/Move 충돌플래그로 y이동을 처리한다. 순간이동/씬전환은 기존진입점에서 controller cache/수직속도를 리셋하고 같은Player를 이동한다. 기존 Rigidbody 속도 reset은 kinematic에서는 호출하지 않는다. 큰낙차를 바닥으로 순간이동시키는 무제한ground snap은 하지 않는다.

횡단보도는 흰 막대의 장축이 차도 진행 tangent를 따르고 막대 반복은 보행횡단 normal방향이 되도록 기존UV의 두축을 교환한다. 정사각 texture의 수평flip만으로 평행/수직이 바뀌지는 않는다. 실제mesh변위와UV미분의 방향이 일치해야 하며, 마지막 짧은 패치는 crop규칙을 유지한다.

최종필요검사: 실제0.2m단차 양방향이동/대각모서리/벽차단/문진입, controllerfeet와support높이오차≤.06m(skinWidth+.01), 실제높이2층6.8m, 교차무늬축, 해당구간NavMesh통행, 동일Player 씬왕복과잠금복원. 바뀌지 않은 이미지정규화는 D05증거를 재사용한다. 낮은턱 하나의 성공을 층전환/낭떠러지/모든경사의 합격으로 확대하지 않는다.

### D06 실행 증거·사용자 유지 승인

- [구현] 실제 Ground/Sidewalk 윗면Y=.205, roadY=.005이고 같은메시에 MeshCollider를 붙였다. 포장끼리 수직경계는 없으며 차도/외곽에만0.2m 수직면이 있다. 건물rootY=.205, 실내floor=.221; 배치물/적/상자spawn은 같은 지지높이를 읽는다. layout 단계부터 건물높이6.8m, Storeys2이며 checkpoint geometry1004로 구분한다. 승인된 원본/WholeSheetNormalized atlas는 재처리하지 않았다.
- [Play Mode 호출 확인] seed475456319에서 기존 PlayerMovement.StepMove→CharacterController.Move로 실제턱 왕복을 구동했다. 상승최종rootY=.7549998, 하강최종Y=.5549999(차이0.2m), 발과표면 차이는controller skin .05m 이내다. 상승/하강목적지XZ오차<.12m, 실제벽차단, 문통과, 두 지면NavMesh 경로, 모든건물2층6.8m, 실제횡단보도mesh UV축교환을 확인했다. 대각벽모서리·큰낙차·다른경사는 별도실행하지 않았다.
- [실제 씬 왕복] GameMapTest→기존DirectSceneTravel→GameMap1→기존RaidSession.TryBeginRaid→GameMapTest를 실행했다. Player/Camera/Inventory UI EntityId가 모두같고, CharacterController enabled/PlayerMovement enabled/전환잠금해제를 확인했다. 돌아온seed는−1243259102이다. Editor 임시저장루트를 사용했다. 바뀐 checkpoint복구 TryTeleport 호출은 코드확인만이며 저장/Recovery전체왕복을 검증한 것은 아니다.
- [결과] `LocalOnly/IsometricMapTrial05/technical.json`, `travel.json`, `overview.png`, `street.png`, `inside.png`, `step.webp`. WebP는 실제새이동에서촬영한23장으로, 확인을위해80ms씩느리게재생한다. 기존GIF재분해가 아니다. `WorkLoop state-v8`의 필요한최종gate 통과는 기술조건만 뜻한다.
- [사용자 승인] 현재 단차·횡단보도·2층 크기는 괜찮으며 디테일은 나중에 조절하기로 했다. 이 결과는 유지한다. 별도 재개 요청은 둥근 도로 끝의 생성 알고리즘과 이동 경계/외부 도로 표시의 분리다.
- [종료/남은범위] Unity의 background실행이꺼져frame2에멈춘 전환을 확인해 시험중에만켜서실제왕복을진행하고 원래false로복원했다. Play를종료했다. Console의과거15:12오류3건을보존했고 이번게임실행의새오류는관측하지않았다. 실제키보드, 경사/낭떠러지/모든seed/GPU성능/빌드는 미검증이다. 건물내부층전환/긴계단은 이번에만들지않았다.

## 승인된 재료 D05 — 전체 시트 정규화 후 면 추출, 바닥 역할과 테두리 교정

[사용자 정정] D04는 수정 PerfectPixel을 사용했으나 14개 면을 먼저 추출한 뒤 정규화했다. 사용자가 요구한 순서는 원본 스프라이트 시트 전체의 정규화가 먼저다. 일반 Ground에도 아스팔트가 지정되어 건물 주변이 도로처럼 보였고, source plane 앞변에 슬랩의 밝은 테두리가 섞여 반복 흰 선을 만들었다. 이전 결과와 원본은 보존한다. 인도와 건물 주변 Ground는 같은 밝은 보도 재료로 통일하고, 연결/충돌/진입/가림 구조는 바꾸지 않는다.

파이프라인: `원본 시트 RGBA/좌상단 px → 우측·하단 투명 padding → 수정 PerfectPixel source_regions로 전체 공통 격자 → 정규화된 시트 px → 상면 polygon의 테두리 제외 영역 → 기존 homography nearest 추출 → 32texel/m atlas → 기존 mesh/카메라 렌더`.

- 전체 시트의 격자 한 칸은 원본 4×4px로 고정한다. 오른쪽/아래만 4의 배수로 투명 padding하여 원본 비율과 위치를 바꾸지 않는다. alpha>=128만 opaque로 정하고 RGB/팔레트/명암은 자동 변경하지 않는다. 수정판 `sample_scoped(method=source_regions, coverage=.5, color_edge_threshold=.08)`를 각 전체 시트에 한 번 실행한다. 출력 시트와 metadata를 보존하며 조각별로 정규화를 다시 실행하지 않는다.
- 원본 픽셀 중심 좌표 p는 정규화 시트에서 `(p+.5)/4-.5`에 대응한다. 역투영은 기존 단일 평면 homography를 사용한다. 도로·보도 상면의 슬랩 외곽/하이라이트는 타일 접속용 재료가 아니므로 각 상면 변에서 안쪽으로 정규화 시트 2px(원본8px)인 평행선들의 교차 polygon만 사용한다. 이것은 입력 영역의 명시적 crop이며 숨은 면 복원이나 무봉제 생성이 아니다. 벽/유리처럼 별도 저작한 면에는 이 바닥 crop을 적용하지 않는다.
- 이 시험의 Ground/Sidewalk는 모두 기존 지면 표시 높이0.005m에 놓고 경계 띠로 솟은 보도/내부 curb를 제거한다. 기존 물리 바닥·실내 바닥·Player 높이는 유지한다. 실물 계단/보도 단차의 수직 이동을 구현했다는 뜻이 아니다. 스타일 없는 기존 맵의 보도 높이는 유지한다.
- 전체시트 먼저 처리/각 시트1회/동일 격자/원본 해시 불변/변환된 점의 대응오차≤1e-6px/바닥 crop 결과 opaque/현재 atlas 실제 연결을 마지막에 검사한다. Ground와 Sidewalk가 같은 patch인지도 실제 asset/runtime 참조에서 확인한다. 이전 크기·입력·문/가림 결과는 해당 코드가 바뀌지 않으므로 재사용한다. 마지막 대표 맵 화면으로 흰 테두리와 바닥 구분을 사용자에게 확인한다. 픽셀 통계로 미술 합격을 대신하지 않는다.

### D05 실행 증거와 남은 경계

- [실행] `Tools/WorldArt/gpt2_source_planes.json`의 기존 원본 복사본 3장을 수정 엔진으로 각1회 처리했다. 모두1448×1086 → 우/하단pad1448×1088 → 전체시트362×272. 전체15.304초 중 시트 sampling15.057초이며 맵 생성/게임 프레임 시간과는 다르다. 조각14개의 추가 엔진 호출은0회다. 원본/엔진 SHA 불변, 평면 대응/불투명 조건을 통과했다.
- [산출물] 현재 `Assets/Art/IsometricUrban/Gpt2/WholeSheetNormalized/`의 Sheets 3장, PlanarTiles.png/json과 `Gpt2IsometricStyle.asset`을 사용한다. Ground/Sidewalk는 같은 밝은 patch와 기본6:금간타일1 후보, Road는 기본960:금간도로96:맨홀11 후보다. `hash(seed,x,z)`로 고르고 도로 연결·방향 표시를 랜덤 후보와 섞지 않는다. 원본 시트의 보도 줄눈/흠집은 남긴다.
- [Play Mode 호출 확인] seed−412374159, 새 atlas가 바닥/건물 재질에 연결됨, Ground/Sidewalk patch 일치, 모든 지면정점Y=.005 및 내부curb 없음, UV 유효, 황/백/횡단보도 사용과 road영역밖quad0을 확인했다. `LocalOnly/IsometricMapTrial04/technical.json`, `street.png`, `inside.png`; WorkLoop v7의 작업→관측→최종 필요gate 완료. 이 gate는 시각 승인이 아니다.
- [재사용 증거] 직전 `IsometricMapTrial03/technical.json`에서 같은 Update의 StepMove 경로로 yaw0/45/90/180×pitch30/80×5입력=40case의 화면방향/속도, 높이1.795856m<문2.65m, 건물10.2~17m, 실제문NavMesh/통과공간/벽차단, 안/뒤fade, 동일Player를 확인했다. 이번 D05는 해당 코드를 변경하지 않았다. 실제 물리 키보드는 미검증이며 Editor 가상키 주입 실패는 입력 합격으로 쓰지 않았다.
- [구현 경계] 건물은 실제 box면/창틀/두께와 지상층 실내, 상층은 외관이다. 주광Lambert+SH만 연결됐고 원본 baked빛/추가광/그림자 통합은 완성되지 않았다. 창·벽의 투명 중첩, 전경 건물의 near-plane 잘림은 현재 화면에 남아 있다. 차선patch에는 원본 돌/균열/아스팔트 배경도 남으며 완전한 무봉제나 선 전용mask를 구현했다고 하지 않는다. 계단과 경사 높이추종/층 전환은 설계만 있다.
- [사용자 판단 대기] 도로 흰 외곽선과 밝은 포장면의 실제 화면을 제출했다. 최종 미술 합격, 물리키 입력, 모든seed/저장복구/카메라씬왕복/GPU성능/빌드는 미검증이다. Play 종료, Console에는 과거15:12오류3건만 남아 있고 이번 최종 실행의 새 게임 오류는 관측하지 않았다. 최초 metadata 적용용 임시 RunCommand의 serializer/사용불가 JSON라이브러리 오류는 확정 좌표 적용으로 해결했으며 이미지 엔진 재실행은 하지 않았다.

## 이전 결정 D03 — 실제 입체 구조와 면 텍스처, 치수·도로 연결 교정

[사용자 정정] D02의 각도/타일 종류/건물-캐릭터 비율은 불합격이다. 억지 offset/비균일 scale 대신 기술 근거와 제작·실행 비용으로 선택한다. 아래 설계 완료 후 구현한다. D02 결과는 보존한다.

| 후보 | 선택/탈락 이유 |
|---|---|
| 완성된 등각 모듈 전체를 한 수직면에 매핑 | 기각. 원본에 여러 면과 깊이가 섞여 있어 하나의 homography가 성립하지 않는다. 단일 방향에서 비슷해도 회전과 연결이 깨진다. |
| 정사각형 평면 재료 + 실제 box/모듈 geometry + 면 UV | 채택. 기존 Physics3D/NavMesh/카메라와 동일 공간. 벽돌·콘크리트·유리 등 단일 면만 원본에서 사용하고 기둥/창틀/두께는 geometry로 만든다. 숨은 면은 복원했다고 주장하지 않는다. |
| 전체 sprite 세트 재생성 또는 2D Tilemap 이관 | 이번에는 보류. 평면 재료는 재사용 가능하고 3D 이동/가림을 유지해야 한다. 부적합한 재료만 향후 평면 tileable texture로 교체한다. |

공식 제작 절차는 [Unity ProBuilder UV](https://docs.unity3d.com/Packages/com.unity.probuilder@6.0/manual/workflow-uvs.html)의 면별 repeat/UV mapping, [OpenCV 평면 homography](https://docs.opencv.org/4.13.0/d9/dab/tutorial_homography.html)의 평면 제한을 따른다. ProBuilder 패키지를 설치하거나 자체 3D 복원기를 만들 필요는 없다. 기존 procedural Mesh 생성부에서 같은 표준 좌표 계산을 사용한다. [Unity 메시 결합](https://docs.unity3d.com/6000.0/Documentation/Manual/combining-meshes.html)에 따라 벽 방향/가림 단위로 합치고 roof는 분리한다. 전체 도시 결합은 culling 손실 때문에 제외한다. [URP 조명 함수](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/use-built-in-shader-methods-lighting.html)를 사용하되 원본의 baked 음영은 제거되지 않는다. MPB 투명화는 SRP Batcher 제약이 있으므로 최고 성능을 보장하지 않으며 renderer 수와 실제 실행 시간을 구분한다.

### D03 수학·입출력 계약

`원본 PNG px → 단일 평면 landmark → homography의 동차 UV → metric 면 mesh → local-to-world → 같은 camera view/projection → depth/alpha/조명 → 화면`

- 원본 좌상단 (u 오른쪽,v 아래), texel center `(u+.5)/W,1-(v+.5)/H`. 원본 RGB는 보존한다. 단일 평면 밖 창턱/벽옆면/계단은 같은 patch에 포함하지 않는다.
- Unity +Y 위,+X/+Z 지면, 좌수계, 1unit=1m, 건물 local원점=지상 footprint 중심. 기존 도시 parent의 Y quaternion회전 한 번, scale=1. camera=도시 yaw+45°, pitch30°의 2:1 dimetric. true-isometric35.264°와 혼동하지 않는다.
- [사용자 추가 정정] 카메라 회전 뒤 WASD가 월드축에 남아 조작이 불일치했다. 맵 격자는 물리 사각격자로 유지하고 화면 마름모는 projection만 담당한다. 기존 PlayerMovement에서 카메라 right의 XZ투영을 정규화한 r, `f=cross(r,up)`로 지면 직교기저를 만들고 `normalize(input.x*r+input.y*f)`를 이동/회전에 함께 소비한다. 변환 후 x/z 변위로 충돌분기를 계산한다. 화면 W/S/A/D가 카메라 yaw0/45/90/180,pitch30/80에서 일치해야 하며 대각 속도는 기본 속도를 넘지 않는다. 기존 ReadMovement·입력차단·action취소·run·Animator의 권위는 보존한다.
- geometry `p = origin + u*e_u + v*e_v`, 면의 두 단위기저는 직교. 길이/높이가 바뀌어도 텍스처 크기는 지정 metre당 반복으로 고정한다. 남는 마지막 구간은 crop UV로 처리하고 전체 그림 stretch는 하지 않는다. source H의 동차 3좌표를 vertex에 저장하고 fragment에서 나누면 삼각형 대각선의 affine 왜곡을 피하며 같은 atlas 한 재질로 여러 patch를 묶을 수 있다.
- 크기 관측: runtime skin의 `sum(weight * boneWorld * bindPose * vertex)` 월드 정점 높이3.737243, 문2.65, wall3.4. BakeMesh prefab 관측은 scale 중복/비활성 rest 오염 가능성이 있어 채택하지 않았다. 기존 외형 공통 root만 균일 scale로 약1.8m에 정규화하고 feet pivot/rig/Player root/checkSize는 유지한다. 디자인상1.8m는 이번 비율 교정의 명시 가정이며 추정 신체 정보가 아니다.
- 건물은 기존 layout.Height10.5~18을 층고3.4의 정수층으로 반영한다. 지상층만 진입하며 upper facade는 외관이다. footprint8~10m×8m 유지. 문 폭2.4m는 기존 이동 반폭.5m+여유를 충족한다. 문 높이2.65m, 벽 두께.2m. 크기를 바꾸려고 모든 grid/이동속도/NavMesh를 확대하지 않는다.
- 도로 좌표: `t=(B-A)/length`, `n=(-t.y,t.x)`, `s=dot(p-A,t)`, `d=dot(p-A,n)`. 기존 graph로 중심선·차로·교차 진입을 계산하며 +X source 차선 방향을 t에 대응한다. 수직/대각 동일 공식. 원본 노란선/흰 점선/횡단보도/금간 바닥을 사용한다. 교차부는 선을 끊고 길 가장자리는 기존 surface grid를 침범하지 않는다. 비정규 sprite 외곽을 도로 물리로 사용하지 않는다.
- 계단은 box step의 tread/riser 면으로 가능하지만 현 PlayerMovement는 XZ 수평 이동만 있다. 계단 이동/층 전환은 이번 구현에 포함하지 않는다.

### D03 최소 실험·실패 조건

독립 반례 검토에서 전체 모듈의 다중면 문제, wallHeight가 layout.Height를 무시한 점, road-port가 중심선에만 있는 점, 고정 head ray와 실제 큰 외형 불일치를 확인했다. AI 동의를 합격 증거로 쓰지 않는다.

완성 후 하나의 대표 seed에서 (1) UV finite/범위/동차 분모>0, 코너 대응≤1e-5UV; (2) 단위기저 dot≤1e-5, parent scale=1; (3) 캐릭터 약1.8m 및 문보다 작음, 기존 checkSize 통과; (4) 실제 황/백/횡단 material 사용 및 도로영역 밖 표시 없음; (5) 입구 NavMesh/벽 차단/안과뒤 fade; (6) 실제 두 카메라 각도 화면과 건물 renderer 수를 최종에 모아 확인한다. point filtering에 따른 픽셀 coverage 변화와 source 무봉제성은 보장하지 않는다. 현재9개 기술 조건만 만족했던 D02를 미술 합격으로 재사용하지 않는다. 물리 표현 version/hash도 새 geometry를 구분한다.

### D04 추가 입력 — 사용자 수정 PerfectPixel과 랜덤 타일

[사용자 확정] Desktop/GPT/3의 수정 PerfectPixel 경로로 재료를 정규화해 타일로 사용한다. 해당 폴더 review12/review13 PNG와 `LocalOnly/PerfectPixelPalette_20260906`의 출력 SHA256가 일치하므로 동일 수정 엔진을 재사용한다. 별도 복원/AI 이미지 재생성 엔진을 만드는 요청으로 해석하지 않는다.

평면 source patch를 homography로 펴고 알파>=128을255/나머지0으로 정한 뒤, `sample_scoped(method=source_regions, color_edge_threshold=.08)`를 적용한다. 목표32texel/m, 정사각형2m 재료는64×64, 직사각형면은 같은 밀도로 가로세로를 계산한다. 출력 texel의 원본소유권은 기존 수정판의 계산을 사용한다. 색/명암 단계는 미요청이므로 자동 색보정하지 않는다. atlas2pixel edge padding/Point/Clamp/no-mipmap로 다음 재료가 번지는 것을 방지한다. 출력과 원본을 따로 보존하며 offline 1회 변환, 런타임은 atlas UV만 읽는다.

해당 엔진의 `fix_square`는 행/열1개 차 조정이며 마름모 역투영/숨은 면/계단/타일 edge 접속 계산은 아니다. 셀 선택과 색/명암을 분리한 수정 엔진을 그대로 사용하며, 타일 seam 자체의 보장은 추가 edge 규격에 달린다.

이전 [RuleTile 조사](unity_rule_tile_research.md)를 재사용한다. 현재3D grid의 연결 권위를 유지하고, 역할별 후보의 가중 누적분포에 `hash(seed,x,z)`를 넣어 표현을 선택한다. 보도는 보도 후보, 일반도로는 일반도로 후보에서만 선택한다. 차선 방향/교차부는 실제 road graph가 정하며 무조건 랜덤으로 고르지 않는다. RuleTile 패키지를 설치한 상태로 보고하지 않는다.

계단 권장 경계: 보이는 tread/riser mesh와 이동용 단순 경사 Collider를 분리한다. 계단 높이H,수평길이L에 대해 slope=atan(H/L), 바닥 높이 h(s)=H*clamp(s/L,0,1)이며 시각단차는 floor(s/run)*rise다. 충돌면이 있다고 현 XZ mover가 자동으로 높이를 따르지 않는다. [Unity CharacterController](https://docs.unity3d.com/6000.0/Documentation/Manual/class-CharacterController.html)의 slopeLimit/stepOffset와 [Move](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/CharacterController.Move.html)의 명시적 중력/수직이동 책임을 비교했다. ground following/층별 NavMesh/저장Y/가림층 ID까지 연결하는 별도 실험이 필요하며 현재 평면 맵에 경사 Collider만 끼워 넣고 완료라고 하지 않는다.

## 이전 결정 D02 — 원본 전체 벽 모듈 시험판, 사용자 불합격

사용자는 첫 화면의 타일이 이상하고 원본 이미지를 사용한 것인지 질문했다. D01의 벽돌 면만 반복한 표현이 기둥·창·출입구를 잃었음을 인정하고, 원본 전체 모듈로 교체했으나 이후 각도/비율 정정으로 불합격됐다. 아래 D02 기록은 당시 상태이며 현재 구현은 D05다.

## 이전 결정 D01 — 기존 3D 공간에 원본 아틀라스의 면을 연결

[사용자 확정, 2026-09-14] 캐릭터 작업은 중단한다. 바탕화면 GPT/2 재료로 맵 타일을 교체할 수 있게 하고, 건물에 실제로 들어가며, 안/뒤에서 캐릭터를 가리는 벽을 반투명하게 한다. 캐릭터를 최상위 레이어로 옮기지 않는다. 이번 범위는 GameMapTest 시험 표현과 단층 실내이며 다층·문 잠금·정식 실내 콘텐츠는 제외한다.

[코드 확인] 기존 맵은 UrbanSurfaceGrid의 XZ 2m 격자, 하나의 종류별 submesh, 도로 전면 필지, 전체 footprint 건물 Collider, PhysicsColliders NavMesh이다. 같은 Player와 Camera는 PersistentGameplayShell 소유다. 별도 점유 격자/Player/맵 생성기는 만들지 않는다.

| 후보 | 결정·실패 조건 |
|---|---|
| Isometric Tilemap + Physics2D | 현재 Physics3D 이동·NavMesh·3D 캐릭터와 공간 권위를 새로 연결해야 하므로 이번에는 보류. |
| 마름모 그림 전체를 XZ quad에 부착 | 이미 그려진 투영을 다시 투영하고 측면 두께까지 바닥에 반복하므로 제외. |
| 원본의 상면/벽면 코너 → 실제 XZ/수직 quad의 UV | 채택. 기존 물리와 깊이 검사를 유지하고 표준 직교투영으로 출력한다. 원본 그림의 정확한 등각성·무봉제성은 보장하지 않는다. |

## 입출력과 좌표 계약

- 입력: GPT/2 원본 PNG를 보존한 프로젝트 복사본. 원본은 실제 alpha가 있으며 상면은 정확한 2:1 마름모가 아니다. 자동 균등 slice 대신 면의 네 저작 기준점을 기록한다.
- 이미지 좌표: 좌상단 원점, 오른쪽 +u, 아래 +v, 단위 원본 pixel. texel center UV=((u+0.5)/width, 1-(v+0.5)/height). 바닥은 4점으로 정한 homography를 셰이더에서 나누어 샘플한다. 마름모의 하단 측면은 상면 UV에 포함하지 않는다.
- 월드: 기존 +Y 위, XZ 이동 평면, 1 unit=1m. 원본 surface grid의 cell center와 tileWorldSize만 배치 권위다. 바닥 normal=+Y, 벽/지붕은 실제 면이며 캐릭터와 동일 depth test를 쓴다.
- 기본 시험 카메라: 도시 격자 기준 yaw 45°, pitch 30° 직교투영. 화면상의 지면 축은 (x-z)cos45°, (x+z)sin30°sin45°이고 2:1 화면 마름모가 된다. 원본의 비정규 투영은 UV에서 해소한다. 자유 회전 시에도 실제 geometry는 유효하지만 원화의 그려진 빛은 재저작되지 않는다.
- 실내: 동일 씬의 단층 바닥, 길이가 정의된 벽, 문 폭에 해당하는 실제 Collider 공백. 전면은 기존 parcel facadeDirection이 결정한다. Collider 자신에 Obstacle tag를 둔다. 전체 건물 blocker/NotWalkable 상속은 사용하지 않는다.
- 가림: 상체/머리를 WorldToViewportPoint→ViewportPointToRay로 얻은 실제 시선 선분이 벽/지붕 Collider와 교차하거나 Player가 실내 Bounds에 있으면 해당 표면 alpha를 낮춘다. 직교 카메라에서도 평행한 시선이 유지된다. 충돌·LOS·NavMesh는 그대로다. transparent blend와 ZWrite Off 재질을 준비하고 CharacterSilhouette depth 비교는 수정하지 않는다.
- 교체 입력: ScriptableObject에서 원본 texture와 면별 UV 코너를 바꾼다. 임의 파일 하나가 관점·숨은 면까지 자동 복원된다고 간주하지 않는다.

## 최소 실험과 판정

한 실제 GameMapTest 실행에서 기존 Entry→Portal readiness, 문 통과 경로, 벽 차단, 실내/뒤/시야 복귀의 alpha와 원래 Player 참조를 확인한다. 최종 화면을 사용자에게 보여 미술적 판단을 받는다. 기술 검사와 사용자 승인을 구분하며 승인 전 미적 보정을 반복하지 않는다. 픽셀 스타일 무봉제·모든 카메라각·다층·모든 seed를 검증했다고 주장하지 않는다.

입력 UV 범위/유한수/퇴화하지 않는 면, 실제 mesh normal/배치 단위, 문 폭·NavMesh 도달과 가림 alpha를 필요한 invariant로 삼는다. 캐릭터 리깅 검사는 이 맵 작업에 적용하지 않는다. 변경된 물리 표현은 저장된 과거 맵과 동일하다고 취급하지 않도록 기존 world hash 계약도 확인한다.

## 근거

- [Unity Isometric Tilemap 제작](https://docs.unity.cn/6000.0/Documentation/Manual/tilemaps/work-with-tilemaps/isometric-tilemaps/create-isometric-tilemap.html): 화면 타일 배치·정렬과 3D 물리 공간의 역할 차이.
- [Unity Mesh UV](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Mesh-uv.html): 원본 texture를 geometry에 연결하는 UV.
- [Unity URP Lit](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/lit-shader.html): opaque와 transparent surface/blending의 구분.
- [Unity Collider.Raycast](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Collider.Raycast.html): 지정 Collider와 유한 시선 구간 교차.

## 과거 D02 실행 상태

### D02 방법과 원본

전체 벽 모듈은 p=B+s(R−B)+t(T−B)의 2×2 역행렬로 원본 pixel을 수직면 좌표(s,t)에 연결한다. 원본의 이미지 사각형 모서리를 left+s·length+up·height·t에 놓는다. 0..1 밖의 기둥·받침·창턱을 자르지 않는다. 원본 alpha>0.5의 8-connected component 세 개를 별도 mask로 선택해 겹친 이웃 sprite를 제외한다. RGB 원본은 보존하고, 의료 POI의 기존 청록 tint는 유지한다. 이 벽 그림은 한 평면의 표현이며 숨은 면과 장식의 실제 3D 깊이를 복원하지 않는다.

| 프로젝트 복사본 | Desktop/GPT/2 원본 | 현재 사용 |
|---|---|---|
| `Assets/Art/IsometricUrban/Gpt2/Roads.png` | 도시_거리와_보도_아이소메트릭_타일셋.png | 바닥·보도 상면, 임시 지붕 표면 |
| `Interior.png` | 4x4_인테리어_픽셀_타일셋.png | 나무 바닥 |
| `Walls.png` | 이소메트릭_도시_건축_타일셋_sprite_sheet.png | 기본벽·창문·열린 계단 입구 전체 모듈 |
| `StreetObjects.png` | 도시_거리_픽셀_아트_자산_시트.png | 쓰레기통 소품 |

마스크 선택 면적은 기본벽32,739·창문34,316·출입구48,144pixel이다. mask는 원본과 같은1448×1086, NPOT None, Point, 비sRGB이며 RGB source는 sRGB다. [평면 homography 근거](https://docs.opencv.org/4.13.0/d9/dab/tutorial_homography.html). 원본 저작점과 module bounds는 IsometricUrbanStyle에 직렬화했다. landmark 정확도는 원본 관찰 약±2pixel이며 알고리즘이 의미를 자동 증명하는 값은 아니다.

### 실제 관측 — 2026-09-14

- Unity6000.5.9f1, GameMapTest의 기존 생성기에 style asset 한 참조를 추가했다. 기존 Player/Camera를 사용한다. 건물 전체 blocker 대신 문 틈·벽 Collider, 실내 바닥, 독립 roof와 rain shelter를 사용한다.
- 첫 실행의 MaterialPropertyBlock 생성 시점 오류는 Awake 초기화로 수정했다. 이후 중앙 의료 Chest가 문 접근을 막는 것을 실제 Collider에서 확인하여 상자를 보존하고 그 건물 문을 전면의 오른쪽 절반으로 옮겼다. 과거 결과는 `LocalOnly/IsometricMapTrial01/`에 보존했다.
- 최종 seed −743543409에서 건물150개, Entry→Portal readiness 성공. 의료 건물의 문 앞→실내 NavMesh 경로와 Player 크기 통과 공간, 벽 차단을 Play Mode API로 확인했다. 실제 키 입력으로 보행을 녹화한 검증은 아니다.
- 실내 roof alpha0.04, 가림 표면0.18, 시야 복귀1.0, 동일 Player 참조를 확인했다. 새 레이어/ZTestAlways는 없다. 파일: `technical.json`, `v2b-outside.png`, `v2b-inside.png`, `v2b-behind.png`. `isometric-map-comparison.webp`는 이 세 상태 화면의 비교이며 걷기 영상이 아니다.
- 필요한9개 기술 조건과 파일 존재 gate가 통과했다. WorkLoop v1 후보는 사용자 정정 후 중단했고, `LocalOnly/WorkLoop/isometric-map-trial/state-v2.json`은 art→observe→외부 기술 gate까지 완료했다. 이것은 미술 합격이 아니다.
- 물리 표현은 checkpoint geometry version1002와 벽/문 치수 hash로 구분한다. style이 없는 기존 경로의 version/hash는 유지하며, 등각 모드는 과거 layout-only hash를 받아들이지 않는다. 실제 저장/복구 왕복은 미검증이다.
- Play를 종료하고 GameMapTest는 dirty 없이 남겼으며 style asset을 선택했다. 최종 Console에는 수정 전 초기 오류3건이 보존돼 있고, 그 뒤 새 Error/Exception은 관측하지 않았다.

### 사용·미해결·재개

GameMapTest에서 Play하면 적용된다. `Assets/Art/IsometricUrban/Gpt2/Gpt2IsometricStyle.asset`의 texture/patch/module 입력으로 바꾼다. 다른 texture 크기나 배치라면 원본 좌표도 함께 저작해야 한다. `ProceduralUrbanMapGenerator.isometricStyle`을 비우면 기존 3D 표현 경로다. 현재 건축 평면은 고정 원화의 색/그림자를 사용하며 실시간 환경광·역방향 원화·다층·모딩 파일 로더는 구현하지 않았다. 지붕은 보도 상면을 이용한 임시 표현이다. 모든 시트/가구를 배치한 것은 아니다.

사용자에게 원본 모듈 외형, 타일 반복, 가림 결과를 물어보고 해당 피드백을 받은 뒤에만 시각 수정을 재개한다. 사용자 승인, 모든 seed, GPU Profile, 실내 저장/복구와 카메라 씬 왕복은 남은 확인 범위다. 원본 사진 같은 자동 입체 복원/완벽한 원근 일치를 보장하지 않는다.
