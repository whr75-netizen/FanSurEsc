# GPT/2 등각 타일과 진입형 건물

## 현재 결정 D06 — 승인된 포장 유지, 0.2m 단차·기본 계단 이동·2층 외관

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
