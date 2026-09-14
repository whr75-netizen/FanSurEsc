# GPT/2 등각 타일과 진입형 건물

## 현재 결정 D02 — 원본 전체 벽 모듈을 보존한 시험판, 시각 승인 대기

사용자는 첫 화면의 타일이 이상하고 원본 이미지를 사용한 것인지 질문했다. D01의 벽돌 면만 반복한 표현이 기둥·창·출입구를 잃었음을 인정하고, 원본 전체 모듈로 교체했다. 현재 후보는 기술 관측을 마쳤고 사용자 판단 대기다. 캐릭터는 변경하지 않았다.

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

## 실행 상태

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
