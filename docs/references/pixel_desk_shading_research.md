# 픽셀 책상 명암 — 공식 제작 자료와 적용 후보

## D26 결정 — 바닥 투사 그림자의 화면 셀

사용자는 책상 바닥 그림자도 플레이어처럼 픽셀 단위로 만들도록 요청했다. 직접 확인한 현재 플레이어의 보이는 9개 renderer는 cast Off이고 CharacterFlatUnlit에는 ShadowCaster pass가 없다. 캐릭터의 수광 표면 RGB 셀화와 바닥 투사 그림자를 혼동하지 않는다. 책상은 URP/Lit ShadowCaster, 바닥은 URPToonLit의 연속 shadow lookup을 사용한다.

선택: 그림자를 받는 평면 Ground의 주광 shadow lookup만 화면 2px 셀에서 고정한다. 원본 Small Ground 공유 재료를 보존하고 Ground에만 연결한 복사 재료에서 `_ShadowScreenCellSize=2`를 설정한다. 셰이더 기본값0은 기존 동작이다. shadow atlas 축소/캐스터 정점 스냅은 카메라 격자와 일치하지 않으므로 제외하고, 새 renderer나 가짜 그림자 평면은 만들지 않는다. 이 바닥에 떨어지는 모든 주광 그림자가 대상이며 물체별 선택 효과는 아니다.

경로는 `receiver world meter → 실제 camera clip/SV_POSITION → render pixel → cell center UV → inverse VP의 near/far world → receiver plane 교점 → Unity shadow coord → 기존 shadow sampling/PCF → 기존 바닥 색 합성`이다. 화면 원점과 Y 방향은 URP `GetNormalizedScreenSpaceUV`/`_ScaledScreenParams` 규약, world는 Unity Y-up meter, camera/부모 TRS는 기존 상태를 사용한다. `q=(floor(pixel/s)+0.5)*s`, `uv=q/renderSize`, `s=round(clamp(size,1,8))`. `a=invVP(uv,near)`, `d=normalize(invVP(uv,far)-a)`, `p*=a+d*dot(n,p-a)/dot(n,d)`다. reversed-Z near/far는1/0, 다른 API는 UNITY_NEAR_CLIP_VALUE/1이다. 셀 원점은 viewport0이며 여러 캐스터가 겹치므로 캐릭터별 anchor와는 별개다. 같은2px 크기이지 모든 subject의 위상까지 일치한다는 뜻은 아니다.

실제 평면과 일정 normal에서 동일 셀의 교점과 shadow attenuation이 동일해야 한다. abs(dot(n,d))<1e-6은 평행에 가까운 비지원 조건으로 원래 샘플을 유지한다. 곡면/보간 normal·추가광·SSAO의 셀화는 이번 범위가 아니다. PCF의 명암 단계·그림자 세기·GI·바닥 텍스처·Cookie·책상 형상/외곽선/배치·카메라는 그대로다. 기존 interpolated shadow coord 분기도 활성 상태에서는 p*로 덮어쓴다. 근거는 프로젝트 LocalVolumetricLightFullscreen의 ray 복원과 [Unity world position reconstruction](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/writing-shaders-urp-reconstruct-world-position.html)이다.

최소 확인: Unity 컴파일, Ground 전용 재료의 값과 원본재료 보존, 원래 카메라 실제 Game View 1회. 평면 변환의 원점/법선/TRS는 기존 상태이며 바디 픽셀·형상 검사 반복은 하지 않는다. 최종 외형은 사용자 피드백 대상이다. 실행 `LocalOnly/WorkLoop/desk-shadow26/state.json`.

실행: Unity shader errors0, Console Error/Exception/Assert0. 새 Ground 전용 재료 size2/원본size0, texture/Tint/LightPower 동일, 실제 camera(45,350,0)/size5와 8개 body size2를 반환했다. `preview.png`는 실제 Game View 1회이며 그림자 밝기나 카메라를 촬영용으로 바꾸지 않았다. 현재 graph는 review 대기이며 추가 셀보다 가는 형상/곡면/추가광/SSAO 검증으로 확대하지 않는다.

## D24–25 결정 — 실제 Play 카메라와 같은 격자의 경계

사용자 정정: D23 촬영은 카메라 객체만 실제 PlayerCamera였고 회전·위치·직교 크기·렌더 타깃을 바꿨다. 원래 Play 화면의 증거로 취급하지 않는다. 원래 카메라는 Euler(45,350,0), ortho size5, offset(2,10,-10)이다. 8개 기존 책상을 world Y=45*i도로 배치해 해당 카메라에서 비교한다. 최초 시작점 배치는 기존 기둥에 가렸고 남쪽 이동은 기존 큰 시험 구조물에 가렸다. 두 실패 화면을 보존하며 다른 오브젝트를 지우지 않고 실제 renderer bounds와 겹치지 않는 동쪽 바닥을 선택한다. 기존 PlayerMovement.TryTeleport와 CameraFollow로 관찰 위치만 이동하며 시작 spawn과 카메라 설정은 보존한다.

경계 수정 입력은 기존 12개 box의 part ID(0..11), 평면 법선, 2×2 cell이다. `Unity object meter → model/local canonical X/right,Y/back,Z/up(normalOS.xzy) → TransformObjectToWorld → 기존 UNITY_MATRIX_VP → 화면 pixel center → 기존 subject anchor 기준 2px seed → visibility/depth → 같은 cell 격자에서 면 ID 경계 → 원래 Game View`를 따른다. 물체의 yaw만 바뀌며 카메라·형상·무늬·원래 조명 계산은 변하지 않는다. meter→screen 배율은 실제 camera projection이 정하며 고정96PPU 이미지는 셀 경계 입력에서 제외한다.

고정 경계 이미지를 굵게 만드는 후보는 시점 불일치를 남기므로 제외한다. 기존 cell 그룹 알고리즘을 재사용한다: `face=2*argmax(abs(nCanonical))+(nAxis<0)`, `group=1+6*part+face`(1..72). 같은 subject의 인접 cell 그룹이 다르면 기존 `<` 규칙으로 한쪽 cell만 선을 소유한다. 그룹별 가림은 기존 source depth가 먼저 결정하므로 part 번호가 물체 깊이 우선순위를 대신하지 않는다. 외곽선 색은 기존 composite 설정을 유지한다. 기존 pixel-cell 합성 전체에 stencil bit2를 기록해 이후 per-pixel 로컬광이 셀 일부에 재적용되는 경로를 차단한다. 근거는 실제 프로젝트 cell/group 구현과 [Unity ShaderLab Stencil](https://docs.unity3d.com/6000.0/Documentation/Manual/SL-Stencil.html)의 WriteMask/Replace 규약이다.

기술 판정은 셰이더 컴파일, 12개 실제 part ID와 8개 yaw/size 반환, 원래 camera rotation/size 확인 및 실제 Game View 1회다. 상자 평면의 축별 normal은 정확한 주축을 선택하므로 임계값 조율을 하지 않는다. G01/G03/G04 변환은 기존 Unity TRS, G08/G09 형상·텍스처 크기는 미변경; 골격 관련 항목은 비해당이다. 그룹당 최대72와 같은 cell source/depth를 보존한다. 셀보다 얇은 형상 소실·곡면 일반화·외형 만족은 별도 미해결이며 이 수선이 모든 입력에서 완벽하다는 판정은 하지 않는다.

## D23 현재 결정 — 기존 상태 보존과 기존 렌더 경로 재사용

D22의 자체 3단계 명암은 사용자 요구와 달랐다. 실제 조명 입력을 좁혀 색·면 차이를 없앴으며, 이미지 평면을 기울여 다리 일부를 지면 아래에 배치했다. 고정 PNG/실루엣 통과는 바닥을 제외한 촬영의 결과였으므로 실제 기지의 완성 판정이 아니었다.

현재는 캐릭터에서 사용하는 `UniversalFragmentPBR`와 RGB 로컬광 호출을 재사용하고, 기존 `CharacterSilhouetteRendererFeature`의 오브젝트별2×2셀에 책상을 연결했다. 재료·12개 형상·실제 그림자를 유지하고 캐릭터 전역 설정/전체화면 해상도는 변경하지 않았다. 이미지 평면은 투영을 보존하는 수직 basis와 불투명 하단 접지식으로 수정했다. 계약/실제미리보기/실패 이력은 [D23 기록](../../Tools/PixelUnityProbe/README.md).

Higgsfield 공식 [Canvas](https://higgsfield.ai/creator-hub/help-center/tools/how-do-i-use-canvas)는 생성 모델의 노드 연결·재사용을 제공하며, [Supercomputer](https://higgsfield.ai/creator-hub/help-center/tools/how-do-i-use-supercomputer)는 agent가 계획과 실행을 맡는다. Unity 제작의 수학적 완전성이나 자의적 목표 변경 방지를 보장한다는 자료는 아니다. 프로젝트에는 이미 WorkLoop가 있으므로 새 엔진 대신 `Tools/WorkLoop/pipeline.py`와 고정 `pixel_object` 프로필을 추가했다. 기본은 상태 보존이고 요청된 픽셀 크기 및 필요한 기존 Subject 연결만 원인 있는 변경으로 허용한다. 실제파일/수치 반환 후 사용자 외형 피드백을 기다리며 AI submit으로 외형 완료 처리하지 않는다. 실행기 밖 도구 사용을 차단하는 보안 격리는 아니다.

실제실행 `LocalOnly/WorkLoop/desk-pixel-size-23-v2`에서 기지 적용/미리보기까지 수행했다. 재개는 사용자의 픽셀크기·외형 피드백에 한하며, 등록되지 않은 게임 제작 종류는 별도 고정 프로필이 필요하다. 모든 게임 개발을 이 프로그램 하나로 자동 완성한다고 주장하지 않는다.

## D22 — Unity 기지의 고정 PNG / 실제 메시 조명 비교

사용자는 명암을 이미 명암이 들어간 텍스처로 대체했는지 확인하고, 기지 조명 옆에서 이미지와 3D를 함께 시험하도록 요청했다. D21 최종 PNG에는 계산된 명암이 고정돼 있지만 원재료는 별도 4색 목재 무늬이며, 저장된 Blender 모델은 재질 없는 12개 상자였다. Unity에는 실제 메시와 원재료를 연결하고 주광 normal·shadow 및 기존 로컬광을 3단계 명암에 입력하는 비교 셰이더를 새로 적용했다. 최종 PNG를 3D 재질로 쓰지 않았다.

실제 GameMap1 PlayerCamera의 96PPU 고정 투영에서 PNG RGB 오차0, 실루엣 IoU1.0, 무조명 3D 출력의 재료4색 외 픽셀0. 주광 반전은 이미지0/3D1,015픽셀 변화였다. 기존 로컬광은 양자화 전9,133픽셀의 입사광이 달라졌지만 최종색은1픽셀만 변했다. **현재 램프 반응은 시각적으로 충분하다고 판정하지 않는다.** 첫 실행의 Forward+ 변형 누락과 trial02 촬영 중단을 보존하고 수정 후 trial03에서만 기술조건을 충족했다.

기법·변환·실패와 실행 증거의 상세 계약은 [D22 Unity 비교](../../Tools/PixelUnityProbe/README.md). 씬의 `PixelDeskLightingComparison_D22`와 실제 `LocalOnly/PixelUnityProbe22/trial03` 캡처가 결과다. 고정 시점 내부선 캐시, Point/무압축/밉맵 없음, AA/후처리 OFF 조건이며 자유 줌·회전 전체의 픽셀 보존은 미검증이다. 생성 목재의 순수 albedo 분해, 유색광 틴트, 추가 Point/Spot, 임의 메시/시점과 외형 만족도는 완료로 확대하지 않는다. 조명 표현을 바꾸라는 후속 요청 시 재료 재생성보다 양자화 입력·임계값과 조명 종류의 계약부터 재개한다.

## 사용자 확정과 현재 사실

사용자는 D15/base02 텍스처가 훨씬 나아졌다고 확인했다. 첨부 원본의 나뭇결·원본PerfectPixel66×64 재료·UV밀도를 유지한다. 명암과3D느낌은 미승인이다. 최신 요청은 명암 관련 웹자료 조사이며 아래 대안은 아직 구현하지 않았다.

현재 출력은 `LocalOnly/DeskBlender15/base02/desk.png`, 원본은 같은 폴더 `desk.blend`. D14저장모델의 실제노드를 읽기전용으로 확인했고 D15는 동일재질설정이다. 광원0개, 최종색경로는 원본texture×면tint×AO2단계→LospecEmission(1). 실제직사광/반사잔존이 원인이라는 설명은 틀리다. 강한조명처럼보이는 색영역 배치가 문제라는 것은 구현과사용자피드백을 연결한 해석이며 단일미술원인의증명은 아니다.

## 공식 자료 비교

| 출처 | 공개 기법 | 현재 책상에 연결할 부분 |
|---|---|---|
| [Never’s End GDC2026](https://media.gdcvault.com/gdc2026/Slides/Juckett_Ryan_HowWeDrawA3DSpriteWorldTheStylizedArtOfNeversEnd.pdf) PDF페이지35,39~44 | diffuse/specular/AO ramp 분리, shade albedo/tint, vertex bias, 편집normal, 별도caster/receiver | 가장 직접적인3D→sprite사례. 그림자용색/위치제어를 분리하고 불필요한self-shadow를 제한 |
| [Unity Toon Shader 기본3색/Shadow Control Maps](https://docs.unity3d.com/Packages/com.unity.toonshader@0.8/manual/Basic.html) | Base/1st/2nd Shade Map과 UV의고정그림자위치map. BaseMap공유가능 | 승인된나무무늬를공유하면서 그림자영역과색만별도데이터로관리 |
| [Guilty Gear Xrd 제작자GDC자료](https://www.ggxrd.com/Motomura_Junya_GuiltyGearXrd.pdf) PDF페이지17~23 | threshold/light vector/normal의제어, vertex별shade bias, 물체별light vector, 독립적인lit/shade색선택 | 단순히조명을끄거나cel threshold만넣어서는의도한2D명암이되지않는구체적제작근거 |
| [ProPixelizer 공식 Uber Shader](https://propixelizer.github.io/docs/technical/ubershader/) | lighting ramp, sceneambient↔constantambient, 별도의normal/edge설정 | scene조명으로인한불필요한색변화를제한하는기성도구후보. 현재프로젝트에설치/사용하지않음 |

Unity Toon Shader와GuiltyGear는픽셀책상전용도구가아니다. 전달가능한것은명암제어원리이며동일외형을보장하는프리셋이아니다. Never’s End전체렌더러가필요하다는뜻도아니다.

## 제안 — 승인된무늬 + 부품역할기반그림자마스크

현재의일괄적인면tint×AO를최종디자인권위로삼지않는다. 기본/일반그림자/깊은틈에사용하는색관계와그림자가나오는영역을분리한다. 3색이라는말은이미지전체를3색으로재분류한다는뜻이아니다. 승인된texture는각영역에계속존재한다.

제안표현은 `C=(1-M1-M2)A0 + M1*A1 + M2*A2`, `Mi∈{0,1}`, `M1*M2=0`이다. A0는승인된재료, A1/A2는동일무늬의그림자용색설정이다. RGB를검정으로일괄곱하는한개계수보다부위/재료별로색관계를지정한다. 색설정자체의미술판정은사용자권위다.

M1/M2는책상템플릿의상판돌출밑,서랍앞판경계,깊은조립틈같은구조역할로관리하는후보를권장한다. 부품치수/공통좌표에서일관된규칙으로마스크를계산하면모딩시다시적용할수있다. 이것은자료의control-map원리를현재절차모델에적용하자는제안이며인용게임이똑같은책상알고리즘을쓴다는뜻이아니다.

현재반복나무UV와별도의mask UV/attribute를써야부품별그림자가서로겹치지않는다. 손으로임의pixel을고쳐넣는것이나모든물체에동일한부위offset을붙이는방법으로바꾸지않는다. 임의모델에는part role과mask 입력규약이필요하고무표식mesh에서자동으로그림자디자인을보장할수없다.

## 후속 최소실험과 실패 판정 — 미실행

승인된D15texture/geometry/96PPU를고정하고기존AO명암만위마스크경로로바꾼한버전을비교한다. 상판전체강한밝기대비,그림자번짐,부품틈가독성을실제렌더로사용자에게판정받는다. AO단독2단계화를새기법이라고재실행하지않는다. 모서리normal수정이나shadowproxy는이실험에서필요성이생길때만추가한다.

현재는조사완료/명암수정미실행이다. 자료만으로외형개선을검증했다고쓰지않는다.
