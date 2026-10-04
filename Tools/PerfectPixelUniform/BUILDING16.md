# N17 — 테스트 건물 한 채의 공통 native 표면·실시간 조명 제작 계약

## N30 현재 결정 — 원인별 재질 정보와 실제 미세 반사

[설계/R2, 2026-10-05] 최신 정정은 N29 큰 얼룩이 물을 쏟은 듯하며, 원하는 생동감은 흠집·마모·결·작은 굴곡의 재질 차이와 빛 반응이라는 것이다. N29 broad(.27×.24m) field→3색영역은 요구와 연결되지 않아 폐기한다. 생성 수식/검사 성공을 디자인 타당성으로 바꾼 것이 오해였다. 대상은 같은 checkout 한 종류다. N29 결과·원본512파일·기존 상판 grain/RGB·금장/경계·PositionMap·mesh/TRS·native 격자·카메라/조명은 보존하고 새 버전만 연결한다. 모든 사물·카메라·caster·게임 기능 재작업은 제외한다.

**근거/선택:** [Pelixir 개발자](https://starbi.dev/)의 재료별 팔레트·world-space scratches·ramp-mask decals, [Adobe Edge Wear](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/metal-edge-wear)의 curvature/position 기반 접촉 마모와 [Dirt](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/dirt)의 환경/사용이력 mask를 읽었다. [목재 구조 연구](https://arxiv.org/abs/1511.04224)는 성장 띠·기공·섬유를 색/bump/반사와 연결하며 임의 색덩어리와 구별한다. 새 SRP/Substance 설치 대신 현재 semantic chart에 원인별 mask를 적용한다. (A) 색 수만 증가/broad 잡음 유지: 같은 반례로 제외. (B) 현재 chart+마모/결/높이/거칠기 분리: 채택. (C) 원화 전체를 texture로 복사: 구운 명암/장식 중복·입력 불일치로 보류. 수치/밀도는 프로젝트 제작 매개변수이며 공개 자료가 미술 합격을 보장하지 않는다.

**canonical/계산:** N15 design_tick·design_normal·part·rotation과 기존90.5097PPU가 권위다. front chart=(tx·sx,ty·sy)m, side=(tz·sz,ty·sy)m. door/handle/profile/끝단과 하단 접촉 영역에서만 선분 흠집·소규모 chip·접촉 때를 배치한다. 미세 도장 결은 짧은 방향성 field이며 큰 patch는0이다. 각 현상은 독립 feature mask로 저장한다. 합성 우선순위는 기존 B경계/금장 보존→노출 wood chip→흠집/접촉마모→미세 도장 결이다. paint feature는 R2/part0/B0만, chip의 R2→R4만 해당 mask 안에서 허용한다. R4는 새 clone palette에서만 노출 목재이며 다른 사물의 row4는 바뀌지 않는다.

**색과 광원:** intrinsic palette 폭16/행10으로 paint의 인접색·노출목재·황동 톤을 구별한다. wood row1 첫4색/G와 나무 상판 normalXYZ는 유지한다. PaletteColor는 실제 Texture texel size를 사용하며 기존4열 UV/빛 계산은 같은 식이다. 확장 폭>4를 새 표면 계약 식별자로 사용하고 ShaderLab property/새 shader name은 추가하지 않는다. 확장 G는0..15 albedo index, 조명3단계는 기존 threshold를 유지하여 색 수와 분리한다.

**미세 굴곡/반사:** h(u,v)m의 물리 gradient로 N'=normalize(N−h_u·T−h_v·B), 법선 회전은 기존 rotation이다. paint boundary taper·최대 tilt검사를 적용한다. normal.w는 확장 표면에서만 valid+perceptualroughness=.5+.5r(r=.2.. .9), blank0; 원래4열에서는 기존 의미와 spec0을 유지한다. 설치 URP17.5 BRDF.hlsl의 InitializeBRDFData(smoothness=1−r)/DirectBRDFSpecular를 사용하고 F0·광원 RGB·NdotL·거리/그림자 감쇠·기존 strength/layer를 곱한다. 합산 spec의 peak와 RGB비를 유지한 뒤3양수단계/무광원0으로 양자화한다. 최대 추가 linear peak는 paint/wood .024, brass .06이며 광원별이 아니라 합산 후 상한이다. 기존 읽기용 diffuse에 bounded spec을 더하는 pixel-style 근사로, 엄밀한 PBR 에너지 보존/실제GI로 주장하지 않는다. moving stepped source에는 실제 Unity Light가 없어 이 단계의 GGX spec은 room/main/actual additional light만 받는다. albedo 흠집의 밝고 어두운 쌍을 고정해 빛 반사로 부르지 않는다.

**R3/실패 조건:** 큰blob 없음은 broad 생성 제거·feature의 위치/크기/면적 제한으로 확인한다. 기존4열 palette output은 같은 GPU fixture에서 수정전 PNG와 byte 비교, 새16열 색 index도 실제GPU material diagnostic과CPU 비교한다. 같은 actual camera2px 전후, 두 방향 실제 point light/0광원 spec·격자·source SHA·geometry/lighting·saved scene을 확인한다. 새로운 노출색/반사 기법의 기술 검사가 미술 합격은 아니다. 표면 subpixel h는 silhouette/투영그림자를 바꾸지 않으며 실제 기하가 필요한 변형은 별도다. 초기 미저장 씬은 LocalOnly/Material30/before-unsaved.unity로 copy 보존했고 serialized disk와 차이는 없었다.

**현재/R4·실제 Play 호출:** `material30.py features→generate`가 기존187×211 cell-centre에서 계산했다. paint 인접톤은 col4..15, 기존 paint/wood 첫4색과 모든 boundary albedo RGB는 그대로다. 독립 mask는 결11666·손 접촉74·짧은 흠집28·하단 마모71·노출목재9·금속 변색105칸이다. 작은 손 접촉 군집 최대28칸, chip 최대1칸으로 큰 물 얼룩을 만들지 않는다. paint normal 최대2.074°·높이 범위−.657~+.462mm·거칠기 packing과 N29 handle/wood XYZ 보존26조건이 통과했다. 실제 화면의 원인별 마스크/팔레트 밀도는 이번 제작값이며 원화의 흠집을 복원했다는 뜻은 아니다.

**관측/저장:** 실제 URP GPU의 old4col MaterialOnly/ReadableFixture 변경 byte0, 확장 palette albedo coverage차0/최대RGB오차0이다. 실제 PointLight 좌/우에서 spec 활성550/6067칸·방향차5816칸이며 무광원 spec0·합산3단계상한 검사가 통과했다. 같은 실제 Player/Camera·30°/350°·2screenpx 실내 전후48428px 변화, geometry/lighting·원본512SHA 보존, shadererror0이다. 단일 checkout material 참조만 바꿨고 Edit/saved/clean이다. 결과는 `docs/artifacts/building39/material30/run01/comparison.png`(실제 화면 crop, resize0), canonical map은 `material.png`/`normal.f32`/`palette.png`, 실제 관측은 `observation02`다. 새 map/hash 계산은1회이며 이후 재생성0이다.

**실패 귀속/실행:** 첫 graph init은 validation→save 간선의 feedback 누락으로 실행0이었다. plan02에서 features/maps만 생성했고 첫 카메라만 이동한 Play 촬영은 외부 Player membership 때문에 지붕에 가려 changedPixels0이었다. 재질 실패로 포장하지 않고 원래 map을 유지한 채 기존 TryTeleport 진입 API를 관측기에 연결했다. NumPy bool의 JSON serialize 실패도 검사 반환형만 bool로 수정했다. 첫 PNG/receipt와 LocalOnly 상태는 보존했고 integration03은 verify→관측→GPU gate→저장→최종 gate의5단계/48조건을 완료했다. 마지막 state atomic replace의 WinError5 뒤 실제 cursor=gate/active=null/save receipt 기록을 확인하고 미실행 gate만1회 실행했다. 원본 출력/Unity 작업을 재실행하지 않았다.

**남은 범위:** micro-height는 normal/반사 표현이며 실제 silhouette·caster·움푹 패인 geometry를 바꾸지 않는다. spec shadow attenuation은 코드 확인이고 별도 shadow on/off fixture는 미실행이다. 기존 readable diffuse+bounded spec은 스타일 근사이며 full PBR/GI, 모든 사물 적용, 미술합격·Standalone/GPU성능은 완료하지 않았다. 사용자 반례는 grain/contact/scratch/kick/chip/patina 또는 shader 반사 단계로 귀속하며 큰 색 얼룩을 새로 넣어 대신하지 않는다.

## N29 현재 설계 — 넓은 도장 면의 색 군집과 손잡이의 곡면 명암

[현재/R4, 2026-10-05] 최신 요청은 단색 면의 밋밋함을 줄이고 둥근 부위에 제한된 단계 명암을 사용하는 것이다. 작업 전 실제 empty_counter의 navy/brass G는 모두2이고 readable shader도 목재 외 column2를 강제했다. 이번 범위는 기존 checkout 수납장 한 종류다. 기존 wood grain·금장 위치·R/B/A·원본512파일·PositionMap·mesh·TRS·PPU·카메라·조명 제어를 보존하며 새 material/normal map과 material clone만 연결했다.

**요구-원인-연산:** 큰 면의 정보 부족 → 도장 재료에 object-chart의 저주파 색 군집을 추가 → G rank1/2/3. 단색 손잡이의 면 구별 부족 → front face 안쪽 3native cell 폭의 얕은 원통형 cap 법선을 20°/40°/60°로 양자화 → 기존 엔진 입사광에 응답. 고정 광원 명암을 albedo에 굽거나 모든 외곽에 3중 선을 복사하지 않는다. 현재 box caster는 유지되므로 이 microrelief는 실루엣·미세 그림자를 바꾸지 않는다. 실제 3색 출현은 광원/양자화에 따라 달라지며 법선3띠를 3색 보장으로 바꾸지 않는다.

**canonical/좌표:** 기존 geometry.npz design_tick(원본 N15 설계 tick), design_normal, part와 rotation이 권위다. 도장 chart의 x/z·y를 기존 tick_scale로 metres에 변환하고 cell-centre에서 smooth value field를 평가한다. 2D lattice value noise의 cubic interpolation, 큰 patch+짧은 결을 고정 seed로 합친 뒤 rank로 양자화한다. 외부 RGB/광원/화면 크기는 입력이 아니다. 작은 4-connected cluster(<3cells)는 base rank로 정리한다. 재료의 불균일 반사율이며 물체의 부피 명암이 아니다. 밀도/길이/색 단계는 이번 표현의 명시적 제작 매개변수이며 논문이 미술 합격을 보증한다는 뜻이 아니다.

**둥근 띠:** handle front의 x-boundary screen-normal 거리 계수는 투영 Jacobian으로 계산한다. J=(R,-U)·rotation·diag(tick_scale)·PPU, x-boundary 거리 계수는 abs(det(J))/length(J_y)다. 좌우 거리 d에 대해 d<1/2/3 native px는 θ=60/40/20°, 그 안쪽은0°. N=(sign(x-mid)*sinθ,0,-cosθ)를 rotation으로 변환한다. 따라서 tick 비등방성 때문에 띠 폭이 달라지지 않으며 한 띠=1nativecell 거리다. 새 NormalMap에서 handle front만 바뀌고 P/coverage/depth는 변하지 않는다.

**소비/검사:** 기존 _RetainPatternContrast flag를 새 clone에서1로 사용하여 readable branch가 모든 재료 G를 읽게 한다. 기존 flag0 분기와 목재는 동일 식이다. 변경 RGBA 범위·wood·원본 해시·법선 유효성과 변경 영역·동일 격자를 자동 검사하고, ±X direct fixture에서 N·L 순서 반전을 확인한다. WorkLoop는 재료 계산 → 단일 Unity writer의 import/동일 실제 카메라 비교 → 관측 기반 gate다. 출력 색 개수/계산 통과는 미술 승인으로 기록하지 않는다.

**근거/반례:** [SLYNYRD Texture](https://www.slynyrd.com/blog/2018/2/15/pixelblog-2-texture)는 연결된 재료 군집·밀도·여백을, [Saint11 Shading](https://saint11.art/pixel_art_articles/article4/)은 평면과 곡면 명암을 구별한다. [Anti-Alias/Banding](https://saint11.art/pixel_art_articles/article5/)의 윤곽을 따라 반복되는 띠는 이번 곡률 법선과 다르다. 원화 전체 navy quad 직접 복사는 투명 texel·금장·구운 면 명암을 포함하므로 제외했다. 네 종류 전체에 front 장식을 복제하면 뒷면 설계를 발명하므로 이번에는 front가 보이는 checkout만 적용한다.

**실행/결과:** `material29.py`는187×211 격자의 G5076칸, 손잡이 앞면의 normal98칸만 바꿨다. navy rank1/2/3은1378/7039/3698칸이며 기존4색 navy palette를 사용한다. 현재 patch는 도장 재료의 얼룩·결 표현으로, 목재 원화 복원이나 디자인 승인으로 부르지 않는다. 실제 Play의 같은Player/Camera·30°/350°·2screenpx에서전후19568px차이, geometry/lighting보존·shadererror0이다. 실제 GPU normal/좌우direct3장의 coverage차이0, CPU 기대 sRGB와최대RGBbyte오차0이며98handlecells의반응이반전된다. diagnostic3의연속입사광을최종3색관측으로기록하지않는다.

**실패/저장/재개:** 최초 관측 도구의 존재하지 않는 enum은 컴파일/실행0에서 수정했다. 이름만으로 찾는 Single은 비활성 역사적 checkout2개를 함께 잡아 촬영전 차단됐고 활성 native대상으로 좁혔다. 생성 map은 재생성0으로보존하고 기존두 graph/state와실패기록을남긴뒤 새 code hash로통합단위만재개했다. integration03의verify→Unity→gate3단계/20조건이통과했고 GPU수식4조건도통과했다. 실제 구도의가구하단클리핑은촬영에만카메라위치를옮겨2px/각도/실제Camera를유지했고원위치로복원했다. finalEdit/saved/clean이며씬diff는checkout material참조1개다. `Assets/Art/NativeMaterial29`와`material29/run01/comparison.png`가현재출력,원본N19map은보존된다. 큰face의밀도·색표현은후속사용자피드백입력이고모든가구확대적용·caster곡면변경·미술승인·Standalone/성능은미검증이다. 새기하가필요한실루엣/투영그림자는이 normal수선으로해결했다고하지않는다.

## N28 현재 결정 — 기존 원형 메시와 픽셀 표면의 격자 변환 공유

[현재/R4, 2026-10-05] 요청은 그림자와 현재 픽셀 표면의 일치이며, 최신 정정은 원형 메시 재사용이다. 현재 N16~27 표면은 옛 Blender scene.blend에서 나온 렌더가 아니다. `geometry16.py` 부품 정의가 position/normal cache와 closed caster를 함께 만들었고, N19는 material map만 바꿨다. 캐시 재계산의 bitwise 일치와 원형 caster 연결을 읽기 전용으로 확인했다. 금색 장식은 현재 기하에서 flush inlay이며, 새 돌출을 만드는 것은 이 요청의 원인 수정이 아니다.

**원인/후보:** 기존 `SnapNativeGrid`는 display clip.xy만 이동하고 캐시의 world position·depth·light query와 caster 정점은 이동하지 않는다. 활성44개 표면에서 Edit 카메라 기준 최대2.454621 screen px의 차이를 계산했다. (A) 현재 같은 메시를 그대로 쓰되 격자 변환을 전체 render 경로에 공유한다: 채택 후보. (B) 옛 Blender 메시로 교체: 현재 디자인과 달라 제외. (C) 픽셀마다 체적을 다시 제작: centre sampling/곡면 근사의 별도 문제이고 지금 확인된 원인보다 범위가 커 보류. 메시·배치·원화·색·PPU·조명 값을 변경하지 않는다.

**좌표/연산 계약:** canonical은 현재 부품 정의와 local XYZ(m), 원점/Unity 축/부모 TRS는 원본 mesh와 cache가 공유한다. `local p → M p(world,left-handed,m) → p+δ → V → P → clip → canonical bottom-left raster(px)`. δ는 원래 격자 phase 이동을 world로 옮긴 한 번의 rigid translation이다. 원본 texel U/V의 view 기저 길이 ux,vy, anchor a에 대해 `s=(V3x3·a).xy/(ux,vy)`, `dsource=round(s)-s`; `q=round(abs(raster(a+u).x-raster(a).x))`; `dcamera=round(raster(0)/q)*q-raster(0)`. `draster=dsource*(uraster.x,vraster.y)+dcamera`; `δ=V^-1·(draster.x/(W*P00/2),draster.y/(H*P11/2),0)`의 vector 변환. raw Camera projection의 canonical NDC를 사용하므로 RT Y flip와 기존 _ProjectionParams.x가 상쇄된다. 분모/기저 유효성은 기존 조건을 유지하며 perspective·비정수·비정렬에는 양쪽 δ=0을 다시 쓴다. 현재 지원은 renderScale1/dynamic-resolution-off/full viewport이며 다른 설정은 명시적으로 지원 밖이다.

**소비자/권위:** 건물의 renderer pair 하나가 같은 카메라 callback에서 동일 `_NativeRenderOffsetWS`를 display/caster MPB에 쓴다. display 정점과 ReadSurface world/depth/lighting도 동일 δ를 한 번만 소비한다. 원형 closed caster는 `M·vertex+δ → URP light direction → ApplyShadowBias → light VP → shadow atlas`. Unity transform/collider/원본 asset은 그대로다. render-only bounds도 같은 이동을 적용하며 기존 MPB와 원래 bounds를 보존/복원한다. 계산 API 근거: [Unity beginCameraRendering](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Rendering.RenderPipelineManager-beginCameraRendering.html), [URP ShadowCaster source](https://github.com/Unity-Technologies/Graphics/blob/master/Packages/com.unity.render-pipelines.universal/Shaders/ShadowCasterPass.hlsl). 실행 환경의 URP17.5 로컬 source에서 SingleCameraRequest callback과 Point normalBias=0을 확인했다. 이는 표준 API를 연결한 프로젝트 수정이며 공개된 완성 pixel-shadow 제품을 복제한 것이 아니다.

**R3 판정/실제 결과:** 원형 empty_counter/재료를 쓴 격리 GPU fixture, screen phase(.17,-.23),(-.31,.41) × 정수2·4배 네 case. cache world hit의 선언한 cell-centre 재투영 오차≤.02 screen px, pair δ 차이≤1e-6m, 원형 solid GPU world hit의 실제 screen sample-centre 재투영 오차≤.02px(공통 coverage 각 case100개 이상), shader error0이 기준이다. 서로 다른 cell/sample centre를 같은 점이라고 비교하지 않는다. 실제 old cache-to-display 오차 .348~2.019px → 공유 경로 최대 .000153px, solid GPU sample 최대 .002678px, 최소90,797 common hits, pair δ 차이0을 관측했다. 원형 mesh가 연속 triangle이고 픽셀은 centre-sampled square라 외곽 부분 coverage/모든 광각의 그림자 픽셀을 동일하다고 주장하지 않는다. 새 voxel/윤곽 제작으로 감추지 않는다.

**통합/관측:** `NativeSurfaceGridAlignment`와 `NativeShadow28.shader`를 기지 기존44pair에 연결했다. 원본 caster asset을 유지하며 원래 Cull Off도 보존한다. 실제 Play에서 maximum old display-only 편차2.433295px, pair 공유 좌표 오차0, 전등 shadow on/off126,980개 screen pixel 차이(>2 byte), 셰이더 error0, 2px, 같은 Player/Camera, 원본512파일·194geometry·이동광/전등 제어 보존을 확인하고 GameMap1을 Edit/saved/clean으로 마쳤다. GPU sample-centre 검사와 실제 on/off는 그림자 존재/공유 transform 증거이며 모든 실루엣의 미술 합격은 아니다. 바뀐 것은 render 정렬 경계뿐이고 frame/손잡이의 원래 입체 구조·메시와 원화는 재제작하지 않았다.

**실패 보존/명시 재개:** 첫 fixture는 Unity native MPB를 MonoBehaviour field initializer에서 만들고 옛38 asset을 가져온 시험장치 오류였다. OnEnable 초기화와 실제39 원형을 쓰도록 고치고 `fixture-failed-constructor.json`을 보존했다. 첫 최종 검사에서는 ShaderLab 새 속성 기본값이 원본36 material에 자동 저장된 것과 baseline-moving JSON 공백 차이를 검출했다. material 속성 선언만 제거하고 renderer MPB/HLSL uniform으로 유지했으며, Editor SerializedObject로 새 기본값 항목만 제거해 원본512 byte hash를 복원했다. moving 값은 양쪽 JSON 해석값이 동일함을 확인한 뒤 원래 기록 서식을 재사용하고 compact 실제 관측도 보존했다. GPU 네 case의 모든 측정값은 전후 동일했다. 조명 연산은 변하지 않아 기존 Play matrix를 재사용하고, 현재 uniform의 최종 실제 Play frame·44pair 관측을 추가했다. 초기 graph/failure와 code freeze는 보존했고 새 final-only graph로 재개했다. 최종174/174 조건 통과는 기술 범위의 판정이다.

**진입점/한계:** `docs/artifacts/building39/shadow28/{request-final,state-final,validation28}.json`, `NativeShadow28Observation.FixtureCapture/AlignmentCapture`, `shadow28_gate.py`; 실제 최종 화면은 `shadow28/final-frame/both-on.png`다. renderScale1/full viewport/orthographic/dynamic-resolution-off PC에서 검증했다. 모바일/업스케일러/TAA/custom viewport/Standalone 성능, centre-sampled 외곽과 continuous mesh의 부분 coverage, 기존 곡면 triangulation 근사와 캐릭터 미술은 미검증/한계로 유지한다. 같은 원형의 새로운 실제 반례가 있으면 해당 좌표/coverage 단계만 재개하며 전체 메시/이미지를 재생성하지 않는다.

## N27 이전 결정 — 재료를 통과하는 조명, 색 덧칠 제거

[요청/범위] 모든 조명 효과가 물감처럼 섞이는 원인을 Unity 기술과 대조해 수정한다. N26의 전등/이동광 독립 제어, 원본·512 source/cache 파일·194 geometry/TRS·30°/350°·90.5097PPU·2px는 유지한다. 조명색·위치·범위·세 단계 입력·하늘 owner·캐릭터 팔레트는 변경하지 않는다. 이번 수정은 표면 반응 계산이며 그림 원본 재생성/축소나 새 후처리 색 필터는 아니다.

[R0 원인] 직접 확인한 프로젝트는 Linear, Preview Camera post=false, 활성 Volume 없음이다. Native에는 fullscreen 제외 stencil bit2가 있어 중복 pass가 원인은 아니다. `Native18Color`는 blue 우세를 분기해 재료색을 무채색 기반 blue target으로 보간하고, 채널별 tint를 반올림한다. 이어 `nightColor + nativeAdditiveLight`가 반사 재료를 거치지 않은 흰 RGB를 더한다. 캐릭터 flat/adaptive PBR 경로는 이미 albedo 곱셈이므로 수정하지 않는다. 일반 world fullscreen도 `Blend One One`로 화면색을 덧칠한다.

[출처/후보] Unity6000.5/URP17.5 설치본 `Lighting.hlsl`의 radiance=light.color×distance×shadow×N·L 및 BRDF×radiance를 [공식 조명 API](https://docs.unity3d.com/6000.5/Documentation/Manual/urp/use-built-in-shader-methods-lighting.html), [Linear 색 공간](https://docs.unity3d.com/6000.5/Documentation/Manual/linear-color-space.html)와 대조했다. Standard Lit 전면 교체는 기존 native 팔레트/야간 가독성/광원 단계 계약을 잃으므로 제외한다. 총 E를 다시 세 단계로 분류하는 안은 이동광의 서로 다른 세 양수 단계를 한두 단계로 접는 반례 때문에 제외한다. 채택은 기존 toon 노출 F(Ebase)의 RGB 재색칠을 제거하고 `albedo × [F(Ebase)+Estepped]`로 재료 반응을 계산하는 최소 변경이다. Unity direct/shadow API는 그대로 사용한다.

[좌표·canonical·계산] N26의 metre/Y-up world P,N 및 cache→Transform→world→camera/native pixel 변환은 그대로다. PaletteMap sRGB sampler가 만든 linear albedo A, URP/SH와 room fill의 linear Ebase, 기존 registry의 양자화된 linear Estepped가 색 canonical이다. `p=max(Ebase.rgb)`, `T=Ebase/p`(p≤1e−6이면0), `Y=dot(Ebase,[.2126729,.7151522,.072175])`, 기존 Q(Y)=.55/.78/1(.12/.4 경계), `F=Q×T`, `Lout=A×(F+Estepped)`. RGB 채널별 반올림/blue target 보간/표면 saturate를 제거한다. 이 F는 읽히는 밤을 위한 제한된 toon 노출이고 물리 HDR 조명·GI 해법으로 주장하지 않는다. 표면 경계는 같은 lit 재료에 기존 sRGB .8을 한 번 적용한다. 원본색/무늬 rank/coverage는 변하지 않는다.

[일반 world·산란 경계] fullscreen에는 albedo가 없으므로 정확한 diffuse를 복원할 수 없다. `Blend DstColor One`의 기존 lit 색 증폭으로 흰 덧칠을 제거한다. 이는 `Cout=Cexisting×(1+Elocal)` 근사이며 기존색0/청색 환경광을 복구할 수 없는 한계가 있다. 실제 native/character는 이 pass에서 제외되며 정확히 자신의 A를 사용한다. volumetric/halo의 additive는 시선 산란/발광의 radiance 합이므로 유지한다. 하늘의 twilight 색 보간은 이번21시 증상 근거가 없어 바꾸지 않는다.

[R1 최소 실험/반례] 프로덕션 통합 전 독립 ARGBFloat GPU fixture: black/wood/navy/paper albedo × 6 neutral/blue/warm/zero Ebase × 이동광0와 세 양수 광량 =96case. CPU↔GPU 최대오차≤1e−5(linear float), black A의 출력0, zero E의 출력0, 백색 이동광 Δ/A=.22/3 간격 및 세 양수 단계 구분을 확인한다. 임계값은 실험 전에 고정한다. 실패하면 재료 반응 단계에서 중단하며 픽셀/원화 변경으로 덮지 않는다. `MaterialLightResponse27.hlsl`, `MaterialLight27Fixture.shader`, `NativeLight27Observation.FixtureCapture`, `light27_gate.py --fixture-only`가 진입점이다.

[R2 통합/관찰] R1 통과 후 담당 shader만 연결한다. 기존 `NativeRoom26Observation.Capture`의 실제 Play21시 all-off/lamps-only/moving-only/both-on/shadow-off와 room-fill GPU를 한 번 관찰한다. source hash·같은 Player/Camera·광원 파라미터·기하·2px와 기존 두 floor ROI 불변을 재사용 gate로 계산한다. 이전 N26 그림은 같은 원본/기하/조명 기준의 before로 보존한다. WorkLoop는 구현→실제 관찰→고정 판정으로 연결하며 최종 미술 합격/게임 전체 조명 일관성은 수치 검사만으로 선언하지 않는다.

[실제 결과] R1의96case/12검사 통과, 최대CPU↔GPU오차4.085e−8이다. 세 백색 양수 단계가 모든18재료/환경조합에서 구분되고 black albedo 출력0을 확인했다. 실제GameMap1 Play21시에서 R2의7광원/diagnostic 비교를 저장했으며 전등shadow on/off126670px 변화, 같은Player/Camera·512파일SHA·194mesh/TRS·moving파라미터·2px를 확인했다. 두 audited floor ROI 불일치0, shadererror0, 기존Console error8개 대비신규0이다. 하얀 덧칠과 rear wood의 purple 변색은 `light27/before/both-on.png`와 `light27/play/both-on.png`에서 비교한다. CPU검사/미술판정을혼동하지않는다. WorkLoop3노드가원래고정계약으로완료됐다. Play종료/모든source상태복원/sceneSavedtrue·dirtyfalse이며scene/prefab/meta기존변경0이다.

[한계/재개] 일반world의screen gain은정확한albedo기반URP조명의대체가아니다. 검정기존색이나청색cast복원은그재료의표면셰이더통합이필요하다. 현재한건물native는그경로를거치지않는다. room fill의GI근사/캐릭터미술/Standalone·GPU성능은N26한계를유지한다. N18 `night18.py`의옛색reference는역사적실험이며N27의새CPU/GPU판정대신실행하지않는다. 관측은 `docs/artifacts/building39/light27`, 현재재료반응판정은 `Tools/Building38/light27_gate.py`이고 재개는 실제반례의원인단계에서만한다. 첫MCP관측호출의중첩private클래스는도구rewriter가namespace에중복생성해컴파일전실행0이었으며단순명령으로고쳤다. 실제관측실행은1회다. 이후기존Enum drawer warning이tool을partial로표시했지만파일/receipt/finally복원을직접확인해재실행하지않았다.

## N26 현재 결정 — 테스트 구체와 건물 전등 분리

[확정] 사용자 요청: 움직이는 테스트 조명 구체는 유지하고 실제 건물 전등은 별도로 구현한다. 전등 켜짐은 방 전체 밝기와 국소 면 명암을 함께 바꾸어야 한다. 원본193파일·캐시·기하·배치·카메라30°/350°·90.5097PPU·2px표시·이동 궤적은 보존한다. 새 전등 모델/입력 단축키/전역 ambient 변경은 범위 밖이다.

[설계/구현 전] 기존 SteppedLocalLight를 유일한 전등 설정/켜짐 권위로 확장한다. Local 역할의 테스트 구체는 이전 수식을 그대로 사용한다. RoomLamp 역할의 두 고정 벽등은 같은 anchor의 Unity Point Light로 직광·실제 shadow map을 계산하고, 지정된 두 room BoxCollider의 union 안에만 isotropic diffuse indirect 근사를 공급한다. 전등 enabled 하나가 두 경로를 함께 켜고 끈다. Unity Light는 파생 표현이며 독립 설정/중복 custom 직광을 만들지 않는다. 간접광은 실제 GI bake/APV/반사 추적이 아니라 공간적으로 상수인 diffuse ambient 근사다.

입력→변환: 기존 native texel centre의 local XYZ/normal → 기존 TransformObjectToWorld/Normal로 Unity 좌수계 metres/Y-up world → room worldToLocal × [P,1]의 box membership → URP GetAdditionalLight의 거리·N·L·shadow 직광 + room diffuse irradiance → 기존 Native18Band(.12,.4)/재료 palette → 기존 native grid의2px 화면. 색 입력은 Color.linear, 출력은 기존 Linear→sRGB 경로이며 UV·coverage·depth/edge·texel centre·scale·회전은 변경0이다. 방 간접광은 E_room=Σ(enabled·color_linear·intensity·roomIndirectMultiplier·membership), 직광은 Unity Light intensity=intensity·roomDirectMultiplier이다. RoomLamp는 custom radial 직광에서 제외하여 중복 계산을 막는다. 유효 room volume이 없으면 간접광0으로 거부하며 unrestricted ambient fallback은 없다. 전등 영향 bounds는 광원 구체와 room world bounds의 union이어야 하므로 광원 중심이 화면 밖이어도 보이는 방의 간접광은 유지한다.

후보: APV on/off Lighting Scenarios는 실제 baked indirect의 공식 경로지만 현재 native shader의 probe 입력·baking geometry 계약이 없어 이번 변경보다 통합 범위가 크다. 기존 radial light 반경 확대는 원형 pool·반경 밖 어둠·가구차폐 부재를 해결하지 못해 제외한다. 선택은 URP 직광/그림자 + 방 diffuse 근사이며 실제 최종 Play 비교가 통과하기 전 scene 저장/완료로 승격하지 않는다. 근거: [Unity APV Scenarios](https://docs.unity.com/en-us/engine/6000.3/manual/lighting-overview/lighting/probevolumes/probe-volumes-change-lighting-at-runtime/bakedifferentlightingsetups), [URP additional lights](https://docs.unity3d.com/cn/6000.0/Manual/urp/use-built-in-shader-methods-additional-lights-fplus.html), [URP shadow atlas/point light six faces](https://docs.unity3d.com/cn/6000.0/Manual/urp/shadow-resolution-urp.html). diffuse ambient는 입사 조도의 방향 무관 상수항이며 Unity 기존 SH ambient와 별도 방 스위치 기여만 추가한다.

최소 case/고정 판정: 같은 실제 Player/Camera와21시에서 모두off / 전등만on / 구체만on / 둘다on, 전등 shadow off/on을1회씩 관측한다. L01 전등off의간접광0·구체role/local값불변, L02 먼바닥(두 전등반경밖)에도간접광>0 및room밖0, L03 white 간접광RGB차≤1/255·최종재료특징/면별명암유지·전등shadow on/off 실제변화>0, L04 기존2px바닥셀내색불일치0 및cache/source/geometry/Transform불변, L05 shadererror0·같은인스턴스·Edit저장상태. 수치오차는float32 world1e-5m、광량1/255、화면간격.001px를사용한다. room record 선택/frustum·직광동기화·shade·pixel 표시로 실패를 귀속한다. WorkLoop는 구현→실제관측→고정 판정이며 파일존재/AI합격boolean으로대체하지않는다.

[현재/R4·실제 Play 호출/GPU] 두 활성 벽등을 RoomLamp로 연결했다. 같은 anchor의 Unity Point Light2개는 white·range3.2·intensity3.6·Hard shadow이며 owner enabled에 동기화된다. 두 전등의 방 간접광 합은 native linear .198, 광원 반경 밖50개 projected floor 표본에서도 GPU RGB123(.1980693), 전등off0을 확인했다. 전체 source/cache/material/mesh512파일 SHA 불변·194mesh 계층/TRS불변·같은Player/Camera·30°/350°·native2px·shadererror0이다. 전등만on은810423px,구체만on은314404px 변화하며 전등shadow on/off는109710px(>2byte 기준109350px) 차이를 만든다. 원본 무늬/금장/면 명암은 최종 `room26/play/lamps-only.png`에서 관찰한다. 두 audited 바닥ROI의8900/11310개2×2칸 내부 불일치0이며 whole-frame 미술/캐릭터 검사는 아니다. 전등/구체 on/off는 `Tools/Fantasy Survival/Room lighting`의 별도 네 메뉴와 runtime `SteppedLocalLight.SetLightingEnabled`를 사용한다. 기본값은 기존처럼 양쪽on이다.

[원인/실행 기록] 최초 binding의 CLR `??`는 Unity missing-component sentinel을 실제 Light로 취급했다. Unity `==null` 판정과 실제 component 존재 검사로 원인을 고쳤으며 기존 부분변경/Undo error 기록은 남긴다. disabled room BoxCollider.bounds는 empty이므로 visibility용 room AABB는 authored centre/size의 세 변환기저 절댓값 합으로 계산한다. 이전 radial 범위를 크게 늘리거나 collider를 활성화하는 대체는 하지 않았다. 최초 WorkLoop state는 observer의 최종저장 함수 추가로 고정 code hash가 달라져 final에서 uncertain_execution으로 보존했다. 외부 gate는 해당 상태에서 실행되지 않았음을 확인하고 현재 코드·기존 실제 관측만 사용하는 명시적 validation-only request-final/state-final이1노드 완료됐다. production/Play 관측 재실행0이다. scene은 이 테스트 인스턴스의 role/reference override와 Light/URP data 추가만 저장했고 원본 prefab 전파0·EditMode/dirtyfalse이다.

[한계] 방 간접광은 isotropic diffuse 근사이고 APV/GI 베이크/실시간 다중반사/문을 통한 간접광 전달은 구현하지 않았다. point direct는 기존 physical caster와 Unity shadow map을 사용하며 room volume 자체는 indirect 경계다. 실제 전등 입력/물리 스위치 모델·캐릭터 미술·Standalone build·GPU 성능 Profile은 이번 범위 밖이다. 일반 fullscreen world와 native/character의 기존 local-light blend 계수 차이는 유지한다. N26 실행 자료는 `docs/artifacts/building39/room26`, 판정기는 `Tools/Building38/room26_gate.py`다.

## N17 현재 수정 계약 (2026-10-04, 구현 전 고정)

최신 요청은 N15의 부품·디테일을 보존해 테스트 건물을 다시 제작하고 바닥/사물 픽셀 크기를 통일하며 기본 밤과 좌우로 움직이는 양자화 조명을 넣는 것이다. N16은 원본 밀도를31.75로 바꾸고 preview/runtime 색 계산도 달랐으므로 외형 보존의 근거가 아니다. 아래 N16 기록은 이전 실행의 증거로만 보존한다.

Canonical은 기존 building-local metres/Y-up/root yaw305/카메라30°·350°다. 공통 PPU=64√2=90.50966799, ΔscreenWorld=1/PPU다. N15 tick (x,y,z)을 (x/32,y/(32√6),z/32)로 옮기면 동일 basis에서 u=2x−2z,v=−x−z−y를 얻는다. 기존 collider·지지 높이·배치는 보존하며 수납장 계열은 N15 profile의 몸체/상판/손잡이/앞·옆 장식 정의를 기존 물리 외피에 대응시킨다. 원래 PNG를 resize하지 않는다. 치수가 다른 물리 외피의 적응을 원본 픽셀 수까지 동일하다고 표시하지 않는다.

실제 활성 Floor는 PixelShopInterior34Aligned/Materials/Floor.mat,1619×819·127PPU다. 처음 측정한 PixelShopInterior34의181PPU는 비활성 이전 Floor였다. 실제 Play renderer 경로로 정정하며 원재료 Aligned/Source/floor-warm.png125×132와 판재 worldUV127×.70710678을 보존한다. 공통90.5097로 바꾸면 바닥 한 칸은1.403배 커진다. 기존 범위·높이·판재 배치를 유지하고 position/normal은 실제 수평면 ray hit로 제작하며 사물과 같은 재료/무늬/경계/명암 경로를 사용한다. 기존색 RGB 덧곱으로 밤을 흉내내지 않는다.

변환은 physical geometry→pixel-centre nearest hit→local XYZ/unit normal/material/pattern/edge→world via 기존 Transform→현재 광원 linear irradiance→공통 shade 함수→sRGB PNG 또는 Linear GPU color→native grid 정수 화면 표시다. 색 계약은 Tools/Building38/shading17.json 한 곳에서 Python 및 생성 HLSL에 공급한다. 임계값[.32,.72],외곽0,crease는재질최암색,기준백색광의tint1,재질별pattern 사용을공유한다. palette는sRGB관측값이고CPU/GPU모두linear로계산한다. 기준fixture는Unity방향[-.20,.84,-.50]/광량1/ambient0로고정하며동일표본별RGB오차≤2/255,coverage불일치0을실제GPU에서확인한다. 실제밤화면은같은색규약에실제광량을입력한다.

기존 SkyLightingCycleController의 initialHour=21과기존API로기본밤을설정하고일주기는기존owner가유지한다. 테스트빛은기존 SteppedLocalLight 한개를사용하며같은빛을URP와중복등록하지않는다. local x(t)=3sin(2πt/8),y=1.35,z=0의연속위치가유일한동작변수다. 표시marker는native정수그리드의작은emissive도트이며표면빛은같은registry→normal/감쇠→공통band로계산한다. 별도LightManager/생성API/전역pixelfilter는추가하지않는다. 이빛의가구차폐그림자는기존SteppedLocalLight범위밖이며기존주광shadow와혼동하지않는다.

제작/검증그래프는geometry/material/export→CPU불변조건→GPU동일fixture비교→기존26사물+17구조+Floor연결→밤/이동빛/게임·개발카메라관측이다. source/code hash와새출력/자산버전을사용해N16원본을보존한다. 요구판정은공통PPU·부품정의재사용·GPU색동일성·source再resize0·같은Player/Camera/collider·pixelHeight/(2·orthoSize·PPU)가정수·광원좌우실제연속동작이다. RGB/shape/phase오류는각담당단계로반환한다. 프리팹원본전체전파없이GameMap1한채의override만저장한다. 컨셉미술승인/자유회전/전게임build는별도다.

### N17 원인 단계 정정

run02의 CPU/GPU 공통fixture는 통과했으나 실제 Play 관측에서 활성 Floor가 기존 셰이더·127PPU로 남아 floor/object 화면 간격 .7126745/1로 실패했다. 해당 WorkLoop는 blocked로 보존한다. floor-fix01은 활성 Floor 계산/재료만 다시 제작하고 나머지35종 캐시는 재사용한다. 비활성 이전 Floor의 잘못된 연결과 이번에 만든 caster만 되돌리고 실제 활성 Floor 하나를 연결한다. 원래 Transform·collider·support는 보존하며 production PNG resize는0이다.

개발 밤 조명은 임의45° 방향값을 제거하고 기존 SkyLightingCycleController가21시 실제 계산한 방향·광량·ambient를 기록해 Edit 초기값으로 적용한다. 조명 권위/계산식은 변경하지 않는다. SceneView는 Unity 공식 GetVerticalOrthoSize의 aspect<1 보정을 포함해 native 정수 배율을 유지한다. SceneView camera의 GUI 갱신 전 값은 실제 렌더 관측으로 승격하지 않는다. 근거: [Unity SceneView 소스](https://github.com/Unity-Technologies/UnityCsReference/blob/master/Editor/Mono/SceneView/SceneView.cs).

실제 밤에서는 기존 wood column=clamp(pattern+band−2)가 바닥의 주요pattern0/1/2를 전부0으로 합쳐 나뭇결이 사라졌다. 바닥만 intrinsic pattern column을 유지하고 linear 출력에(band+1)/3의 세 단계 광량을 적용한다. 완성 명암PNG를 곱하는 방식이 아니며 material rank·실제 normal/irradiance는 계속 독립이다. 중립fixture의 band2에서는 배율1·같은column이므로 기존CPU표본과GPU가 동일해야 한다. 사물35종의 기존 shade 규칙은 변경하지 않는다.

### N17 현재 결과·재사용

[현재/Play 호출·GPU 렌더] 18종26사물+17구조+활성Floor=44표면에 공통90.5097PPU를 연결했다. 사물/바닥/SceneView 화면 간격은1/.99999994/.99999994px로 float32 허용오차 안에서1이다. 같은 Player/Camera,30°/350°,실내등록3·숨은지붕1·벽fade9·shadererror0을 실제 관측했다. 수납장211×187의 손잡이별56/51/57px와 N15 부품 정의를 유지했고 전체 이미지resize는0이다. 치수 적응 결과를 N15 PNG의 원본 픽셀수 동일성으로 표시하지 않는다.

[현재/밤·움직임] 기존 clock 초기값21시, 자동일주기·60초/day는 보존한다. 실제 Update의17프레임에서 light x최소−2.99810958/최대2.98794675m, 비교화면217,993px 변화, 나뭇결 유지와 가구·바닥의 단계 명암 반응을 기록했다. 촬영용 clock 고정과 background실행은 복원했다. Edit조명은 최종 `pattern-light/night-owner-output.json`의 기존owner출력이다. 개발카메라도30°/350°·정수1배이며 씬dirty=false다.

[검증/실패 보존] 수납장/진열장/수정한Floor의 동일중립GPUfixture는coverage불일치0/RGB최대오차0이다. run02는 잘못된 비활성Floor 연결로blocked, floor-fix01은실제표시.99999994를정확비교`>=1`로거절한validatorbug로blocked다. raw관측을반올림수정하지않고기존.001px허용오차를하한에도동일하게적용했다. gate-fix01은그validator한파일의before/afterhash만허용하고모든기하/재질/실제관측을재사용해1노드graph_complete다. 반례.7126745/.5px는허용하지않는다. 그래프성공을미술합격으로표시하지않는다.

현재 자료는사물/구조`Assets/Art/NativeBuilding39`,활성바닥`Assets/Art/NativeBuilding39Floor40`다. 기존 결과의 재사용에는 production/API/격자복원 재실행이 필요 없다. 실제 녹화와원본PNG는`docs/artifacts/building39/floor-fix01/pattern-light`,배포미리보기는`night-moving-light.gif`다. GIF만256색표시포맷이며Unity자료/원본PNG는변환하지않았다.

새제작: `Tools/Building38/run16.py --output <새폴더>` → CPU4단계 → `NativeBuilding16Importer.Import(output,새AssetRoot)` → `NativeBuilding17Setup.CompareFixture(output,새AssetRoot)` → probe제출 → 기존instance`Apply(building,새AssetRoot,이번baseline)`·`Configure` → 실제Play밤/연속관측 → `CaptureNightPreview` → Play종료·`ApplyNightPreview`·Scene저장 → 최종receipt제출이다. 활성Floor만수선할원인에는`floor_repair17.py`와`Import(...,floorOnly:true)`/`ApplyFloorCorrection`을사용한다. 이번validator수선이력의재확인은`final_check17.py`이며생산재실행기가아니다. 실제사물배치·collider·원본prefab·Player/Camera소유자는보존했다.

한계: 움직이는 SteppedLocalLight는가구차폐그림자를생성하지않는다. 기존주광의실물caster를보존했지만이번요청에서별도shadow회귀를반복하지않았다. 순수albedo복원/미술완벽/임의회전/유리overlay/Standalone빌드는미검증이다. 아래N16기록의31.75PPU·Floor보존·4px화면은현재지시가아니다.

## N18 현재 결정 — 읽을 수 있는 밤 (2026-10-04, 구현 전)

[사용자 요구] 밤에도 재료·세부가 보이고 푸른 명암은 그림자에 들어가야 한다. 전체 재료가 푸른색으로 덮인 N17 화면은 이 기준에 부족하다. 병은 원화 sprite를 복사한 것이 아니라 선반 semantic cylinder/label 부품→선반 전체 native cache/합친 caster다. 실제 병은 약10~11×22~28 native pixel이며 현재1:1표시다. 형상/원화 디자인 차이는 조명 수정으로 해결했다고 하지 않는다.

[원인] N17 wood `clamp(rank+band−2)`는 밤 band0에서 카운터/선반 목재의85.9/87.7%를 한 색으로 합친다. `I/Y(I)` tint는 푸른 ambient에서(2/3,1,2)로 파랑을 증폭한다. 고정 .32/.72의 광량 경계도 어두운 면을 같은 단계에 모은다. 이 실패는 격자 복원이나 이미지 resize 단계가 아니라 명암/색 계산 단계다.

[선택] 기존 geometry→native local XYZ/normal/material rank/edge→기존 Transform→URP main/additional/SH와SteppedLocalLight의 linear irradiance I→읽기용 palette ramp→기존 native grid의 표시를 재사용한다. source/position/normal/material/palette/mesh/PPU/배치/카메라/광원 owner는 보존한다. 완성 명암 PNG에 덧곱하기, 전역 ambient 올리기, 이미지 축소/재생성은 이 원인을 고치지 않아 제외한다. 현재 건물의 공유 재료만 opt-in한다.

canonical/좌표·투영/단위는 N17과 같으며 이번 자유도는 최종 색 함수 하나다. e=dot(max(I,0),[.2126729,.7151522,.0721750]), b=step(.12,e)+step(.4,e), B=[.55,.78,1][b]를 고정한다. 목재 기준색 A=Palette(material,rank), 기타 재료 A=Palette(material,min(2,count−1)); crease는같은재질column0,깊은틈/외곽은검정이다. Q=round(3I/max(I.r,I.g,I.b))/3 (0광은Q=1), cool=I.b>I.r && I.b>I.g다. 1차 시험은C=A·B·lerp(1,Q,χ)로무늬를복원했지만목재의낮은파랑채널에새푸른색을만들지못해참고화면의밤색조에부족했다. 실제결과와당시코드는readable-night18에보존하며그graph수치성공을미술성공으로승격하지않는다.

현재색식은D=A·B, S=Y(D)·Q/max(Y(Q),ε), Δ=S−D다. cool그림자에서w=min(.5(1−b/2), min_{Δc>0}((1−Dc)/Δc),1), C=D+wΔ로색조를옮긴다. 따라서Y(C)=Y(D)로무늬의밝기차이가유지되고b2에서푸른색조0이며RGB범위[0,1]안이다. 파랑채널값증가는명시적인hue shift이며전체RGB에파랑배율을곱하는것이아니다. cool이아닌색광은C=D·lerp(1,Q,.30)다. 0광NaN은허용하지않는다. GPU는linear연산→sRGB표시,CPU는같은연산→sRGB PNG다. 무늬rank·광량band는독립이다. .55최저밝기는사용자요구의명시적미술presentation값이며물리적암흑/조도재현이나pure albedo복원이라고주장하지않는다. 모서리/coverage/깊이는변경하지않는다.

[판별] 실제 기존 cache·palette로 CPU 계산→고정푸른fixture GPU한선반 비교→실제Player카메라의21시에서 같은instance의구형/신형색·빛off/on을관측한다. 위치/법선/재질/팔레트/mesh 파일hash불변,검정역할·coverage불변,유한RGB・gamut[0,1]・cool hue shift의luminance불변,wood4rank구분,빛band응답,CPU/GPU최대2/255,기존30°/350°·정수표시를마지막검증으로묶는다. 해당 수치 합격은 미술 합격이나 원화 디자인 복원 증거가 아니다. 흐름은 기존 WorkLoop의색계산→Unity관측→최종검증3단계이며실패시색단계만재개한다.

공식 근거: [Unity URP custom lighting](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/use-built-in-shader-methods-lighting.html)의Light color/direction/attenuation과[Linear color space](https://docs.unity3d.com/6000.0/Documentation/Manual/set-project-color-space.html)의linear계산/sRGB표시를사용한다. 읽기용B·χ는이번아트규약이며Grave Seasons의내부알고리즘을확인한것은아니다. 사용자 첨부화면은외관기준이다.

### N18 실제 결과와 재개

[실제GPU/Play] 현재36공유재료가ReadableNight=1이다. 최종`docs/artifacts/building39/readable-night18-hue`에서189개geometry/position/normal/material/palette파일hash불변,stock_shelf의푸른fixture CPU/GPUcoverage불일치0·RGB최대오차1/255를확인했다. 실제21시같은Player/Camera·mesh/map/Transform·30.000004°/349.999969°·1pixel·shadererror0이며구형색과신형색548,666px,빛off/on62,158px변화를관측했다. 최종PNG는readable-off/on.png이며이미지축소/생성0이다. 1차시험의수치성공/따뜻한목재와코드는readable-night18에보존한다. 그래프는둘다좁은기술판정complete이며미술합격을주장하지않는다.

[보존/한계] Player의기존adaptive PBR경로·sky owner·일주기·캐릭터dirty재료는변경하지않았다. 그러므로현재Player의암부는이옵션과별도다. 병은원화디자인복원이아닌절차형template이며10~11×22~28px,1:1표시라는작은크기도유지했다. 개별병상호작용·캐릭터가독성·미술완벽·Standalone빌드는미검증이다. Play관측의시각고정/빛toggle/임시GPU객체는복원/정리하고Edit로돌아왔다.

재사용에는cache/API/PerfectPixel실행이필요없다. 새색계산실험이승인되면`night18.py start --output <새폴더>`→CPU색만→`NativeNight18Observation.Fixture`/`Gameplay`의실제관측→기존WorkLoop submit/최종gate다. 형상/병라벨디자인의수선은별도입력저작단계이며이색함수의임계값으로대신하지않는다. 직접기하/카메라를다시만드는것은현재수선범위가아니다.

## N19 현재 수선 계약 — 누락된 금속 장식과 제작 밀도 (2026-10-04)

[요구/원인] 사용자에게N18의밤표현은개선되었지만금색문테두리가사라지고도트가너무작다는피드백을받았다. 카메라줌으로제작밀도문제를대체하지않는다. N17의실제catalog는`item.metadata.metadata.cabinet_design`에설계를저장하지만material단계는`item.metadata.cabinet_design`을읽어분기를건너뛰었다. 실제counter의brass164px는손잡이뿐이고body금색0이다. 같은원인이woodUV에도적용된다. N18은PPU/카메라를변경하지않았으며N17의90.51PPU/화면1px를유지했다. 과거N16은31.75PPU/화면4px였고N15미리보기는4배였다.

[수선] 직렬화된geometry metadata를읽는접근함수하나로두분기를교정한다. 기존네수납장geometry/declared physical bounds/PPU/edge/coverage/관측palette를재사용하여material rank/평면장식만재계산한다. 기존N15문사각선·힌지·모서리철물을이미있는투영식과canonical_line으로가시면안에기록한다. 새돌출volume나offset/장식선은발명하지않는다. Unity는현재material의MaterialMap참조만새수선PNG로연결한다. 기존position/normal/display/shadow·sceneTransform·collider·camera·N18색함수/sky owner·원본을보존한다.

[밀도판별] semantic geometry의실물치수와카메라를고정한counter하나에서90.5097와45.2548PPU로pixel-centre ray hit부터각각직접제작한다. Δworld=1/PPU이며후자의도트간격은두배다. 완성PNGresize·카메라줌을생산단계에쓰지않는다. CPU겉모양/재질이아닌같은미터bounds를canonical로재사용한다. 이한개표본은pixel밀도비교이며전체건물의새밀도승인이아니다. 45.25를전체통합하거나소스별임의scale을넣지않는다.

[검증/그래프] 기존WorkLoop: 실제catalog읽기/4종재질수선·단일밀도비교→Unity single writer의PNG연결/동일고정fixture·실제밤화면→최종검증이다. metadata설계4종검출,가시면의원래금장추가counter1810/island414px,coverage/edge불변·무채색메시/PPU/hash불변,원본팔레트불변,새material만body ID변경,동일카메라/크기의두표본1px/2px를확인한다. 낮은밀도의미세특징손실은픽셀수와실제비교로남기며기술합격을미술합격이라고하지않는다. 기존밤명암검증은N18근거를재사용하고새조명수치는조정하지않는다.

### N19 실제 관측과 재사용

[현재] `gold-density19/fine`의 네 재질만 새 PNG로 연결했다. 금장 추가는 counter 1,810/island 414px이며, 나머지 두 종은 금장 앞면이 현재 시점의 숨은 면이라 0이다. 기존 edge/coverage·관측 palette·geometry/position/normal/caster/display 189파일은 불변이다. 실제 21시 같은 Player/Camera·30°/350°·36재료·1px·shader error 0을 관측했다. 가구 치수·배치·카메라·전체 건물 PPU는 변경하지 않았다.

[비교 결함/수선] 첫 임시 comparator의 float raw row를 PNG와 맞추지 않아 coarse가 잘렸다. 실제 production importer의 ReadFloatRows는 이미 상하 행을 맞추고 있었다. 첫 이미지와 paused graph는 보존하고, 비교 코드의 동일 행 변환과 후속 GPU 관측만 재개했다. `comparison-state.json`의 최종 gate는 fine/coarse GPU→CPU coverage 차이 0·RGB 최대 오차 1/255, 기존 캐시 189파일 불변이다. 두 native 표본은 같은 물리 mesh 정점/삼각형·같은 임시 camera에서 1/2px이며 211×187/109×96이다. coarse 손잡이는 14/16/14px로 남아 있다. 45.25PPU는 비교용이며 현재 건물에 통합하지 않았다. 계산 합격을 미술 합격으로 승격하지 않는다.

[실제 이미지 비교] `source-scene-comparison/source-night-game-native.png`는 좌측 현재 제작 원본 preview 211×187, 중앙 같은 재질의 고정 밤광 CPU색, 우측 실제 Play 카메라의 `matched-frame.png` 1114×857에서 측정한 checkout 영역을 자른 것이다. native 1px→화면 1px이며 이미지 resize/resampling 0, 정수 paste/crop만 사용했다. 중앙 fixture는 일정 입사광 .03/.045/.085이며 게임의 공간별 빛과 동일하다고 주장하지 않는다. 현재 금장도 밤 색조로 옅게 보인다. PNG는 현재 제작본의 미리보기이지 원화 생성본이나 runtime에 그대로 칠하는 완성 RGB 텍스처가 아니다. 실제 runtime은 재질/무늬/기하 cache와 기존 광원으로 색을 계산한다.

재사용에는 네 수선 재료와 기존 cache를 그대로 쓴다. 새 수선은 `repair19.py start`의 새 출력 폴더에서 재질 단계만 실행한다. 비교 행 방향 실패처럼 원인이 확정된 경우 `reopen_comparison`은 기존 재질/유효 Play 관측을 재사용하고 fresh 비교 폴더로 후속 관측만 연결한다. `compare19.py`는 이번 실제 Unity 화면/rect receipt와 원본의 무변형 비교판이다. 전체 밀도 변경·금장의 밤 색감 개선·캐릭터 PBR·원화 100% 복원은 미완료다.

## N20 현재 표시 — 사용자 요청에 따른 정수 2배 카메라 줌

첨부된 N15 `NativeObject15/compare01/comparison-x4.png`는 4배 nearest 미리보기다. 현재 건물은 그 디자인/재료 설계를 실제 가구 치수에 맞춰 직접 제작한 cache를 사용하며 해당 확대 PNG를 runtime 텍스처로 붙인 것은 아니다. N19의 이미지/기하/재질/90.5097PPU는 그대로 유지하고 사용자의 새 명시 요청에 따라 카메라 표시만 2배로 바꿨다.

기존 CameraZoomController.SetNativePixelGrid의 선택적 initialIntegerScale과 NativePixelBuilding.initialNativeIntegerScale을 연결했다. 현재 GameMap1 테스트 건물만 2이며 기존 호출/기본값 0은 크기 기반 정책을 유지한다. 명시한 정수 배율을 기존 native zoom 범위에 포함하고, viewport 변화에는 선택된 배율을 유지하여 size=scaledPixelHeight/(2·PPU·scale)로 계산한다. ClearNativePixelGrid는 기존 비native 목표 size를 같은 카메라에 복원하며 원래 일반 줌 제한/입력 차단은 유지한다. Preview Camera는 이 씬의 override로 같은 2배, Scene View도 기존 각도를 유지한 정수 2배로 설정했다. 원본 preview prefab의 사용자 변경은 건드리지 않았다.

`docs/artifacts/building39/zoom20/readable-on.png`는 실제 기존 Play 카메라의 1114×857, size 2.367151, 30°/350°·원본 1픽셀당 화면 2×2픽셀이다. 같은 Player/Camera·map/mesh/Transform·36재료·shader error 0이며 기존 art 189파일은 hash 불변이다. 별도 임시 카메라의 viewport 높이 720/857/1080에서 배율 선택 2, 기존 scroll 계산 호출에서 2→1→2, native 해제 시 같은 카메라의 size 5 복원을 확인했다. 물리 휠 입력은 이번에 실행하지 않았으며 호출 확인이다. 기존 WorkLoop의 설정/실제 관측→최종 gate가 완료됐다. 밤 색감·캐릭터·디자인은 수정하지 않았다.

## N25 현재 색 수선 — 누런 벽등과 재료 계열 경계

[요구/원인] 술병의 누런 중첩광을 점검하고, 오브젝트의 검정 테두리를 조금 짙은 재료 계열색으로 변경한다. 픽셀 밀도는 참고작과 비교하되 승인된 원본/PPU를 임의 축소하지 않는다. 직접 확인한 활성 aligned 벽등2개는 RGB(1,.74,.42), intensity.12/radius3.2였고 이동광은 N24의 white/.4/5m였다. 실제 Play의 같은 카메라에서 벽등 on/off의 왼쪽 선반ROI(x0:180,y35:340) 광량 차이는54830px, 평균linear RGB=(.023778,.011935,.003456)으로 누런 기여를 확인했다. `style25/before/material-only.png`는 병 자체의 갈색·녹색도 재료색임을 구분한다.

[선택/반례] 기존 darkest palette 고정 사용은 밤 표면보다 선이 밝아질 수 있고 금장을 지나치게 어둡게 한다. 원본 map의 선 위치/역할은 유지하고 기존 최종 표면색C를 먼저 계산하여 edge1(실루엣)/2(문 경계)에만 `O=SRGBToLinear(LinearToSRGB(saturate(C))·.8)`을 적용한다. `.8`은 이번 표현의 명시적인 sRGB 감쇠값이며 물리 조도 계수가 아니다. 선은 해당 재료/같은 조명의 색을 따르고, crease3은 기존 palette column0, 바닥 edge0은 그대로다. 실제0광의 default black return은 보존한다. 원본 캐시/팔레트·geometry·depth·coverage·camera30°/350°·90.5097PPU/2px·밤 함수·N24 이동광/ramp를 변경하지 않는다. 두 활성 벽등의 색만 white로 바꾸며 다른 광원과 비활성 과거 램프는 유지한다. 캐릭터 외곽선은 별도 owner이므로 이번 오브젝트 변경에 포함하지 않는다.

[좌표/출력] N17/N24의 native texel 중심→Position/Normal/MaterialMap의 같은index→local미터/actualTRS→world광량→linear표면색→sRGB 경계감쇠→linear render→sRGB 표시를 재사용한다. 표면 비edge와 무늬 rank는 기존 연산이며 재표본화/resize/추가픽셀 패스가 없다. `NativePaletteSurface16._NativeEdgeSRGBScale` 하나가 선색 강도를 소유한다(기본.8; 비교0=기존검정,1=선없는표면색). 과거 CPU/PNG 검정 미리보기는 보존하며 N25의 현재 색은 실제 렌더의 이 단계가 담당한다. 이 색 변화는 선 texel에만 적용되므로 기존 N24의 linear 백색기여 판별은 비edge에 한정한다.

[최소 관측/실패] 기존 actual Play observer를 재사용하여 scale0/.8/1의 같은 카메라 화면을 비교한다. 불투명 선의 .8 출력은 scale1의sRGB80%(8bit/색변환 허용2/255), 비선 영역은 동일이어야 한다. 기존 occlusion fade의 반투명 선은 `render(k)=α·linear(edge(k))+(1-α)·background`로 합성되므로 전체 합성사진에.8을 곱하면 틀린다. 0/.8/1의 최종 linear차로 background를 제거하고 단계간순서와sRGB.8의linear감쇠범위를 확인한다. 원본193hash·기하/Camera 동일·2px·shadererror0, 두 벽등 색 외 광원값 불변·N24 세 백색단계와 바닥 두ROI격자를 마지막 gate에서 확인한다. 깊이/가림/캐릭터 디자인이나 전체 미술 합격으로 확대하지 않는다.

[판정기 재개] 첫 graph는 모든 선이 불투명하고 scale0이면 최종화면도0이라고 잘못 가정해 실패했다. `UrbanOcclusionFader`가 fade material의 SrcAlpha/OneMinusSrcAlpha와 BaseColor.a를 유지하는 직접 코드, 실제 색 endpoint 차이가 근거다. 이전 state/PropertyBlock 비교는 보존하고, 기존 saved material값만 일시 변경하는 `NativeStyle25Observation`으로 세 색을 비교해 복원했다. 제품의 선식/조명/가림을 다시 수정하지 않았으며 새 final 계약은 이 합성식을 명시한다. 새 Shader 기본값.8은 Unity가 현재36재료에 같은float를 직렬화했으며, 해당 추가값 외 재료 참조/원본 map은 불변이다. Inspector의 기존8항목 Diagnostic Enum drawer 경고는 렌더 shader error와 구분하며 이번에 UI를 바꾸지 않는다.

[밀도 조사/한계] 현재 캡처1114×857의2px와 제공 Grave Seasons1920×1080의약4px는 표시 해상도가 다르다. 같은 전체 가로폭에 표시할 때 참고칸은약2.32px이며 현재2px보다약16%크다. 격자로 나눈 관측 추정은 현재/참고 긴계산대 가로204/95칸, 작은병12×25/10×19칸, 캐릭터79×159/31×36칸이다. 실제 원본 sprite와 물리치수는 확인되지 않아 이를미터당PPU로 확정하지 않는다. 병이 일률적으로 압도적으로 고밀도인 근거는 없고 가구 세부/캐릭터는 차이가 크다. [공식 페이지](https://store.steampowered.com/app/3255110/Grave_Seasons/)에 원본PPU 공개는 확인하지 못했다. 이번에는 조사만 하고 PPU/카메라/저작해상도를 변경하지 않는다.

[현재/관측 완료] style25/after의 실제Play는1114×857·21시·30°/350°·2px·같은Player/Camera·map/mesh/TRS이며shadererror0이다. N24의백색세유광은최종비선RGB에서97696/42722/6636px로유지된다. material-comparison의14008변경픽셀 중불투명선4680px는sRGB.8의최대오차.003137(1/255미만),반투명선9328px는합성endpoint의사이에있고linear차비율.57987~.68041이다. 선외최대RGB차0,기존193아트hash·두바닥2px블록·두벽등색외광원값이불변이다. scene은벽등2개색g/b override4개만추가됐으며36재료에는선색scale.8만1행씩추가됐다. 기존Shader색계산을추가픽셀렌더/이미지변환으로대체하지않았다. 첫실패그래프를보존하고합성식수선후final graph를완료했다. Player/미술합격·그림자차폐·Standalone빌드는이번판정대상이아니다.

## N24 이전 조명 수선 — 범위·광량과 무광 구간

[요구/원인] N23의 백색광이 방 전체를 덮고 너무 밝다는 사용자 정정이다. `ceil(3a)/3`은 아무리 작은 a>0도 1/3로 올리므로 반경14m 전체가 최소 광량을 받았다. 기존 `intensity=.8`과 surface strength `.55`의 최대 백색 기여는 linear RGB `.44`였다. 밝기 제어가 없는 것이 아니라 범위·광량·단계 선택을 잘못 결합한 구현이었다. N23은 원본/출력 단계 검증만 보존하고 이 요구의 시각 합격으로 사용하지 않는다.

[범위/선택] 같은 moving light의 반경을5m·intensity를.4로 낮춘다. 새 원본·palette·mesh·배치·camera/PPU·motion·다른 광원·post exposure는 변경하지 않는다. 최종 합성은 N23의 백색 additive를 재사용한다. 유광 세 단계는 유지하되 최소 유효 광량과 완전 밝기 구간을 분리한 toon ramp를 사용한다. 이 값은 게임 표현용 ramp이며 물리 lux/lumen 측정값이 아니다. 자동 노출이나 전체 화면 색 필터로 범위를 덮지 않는다.

[연산/좌표] N17/N23의 미터 표면 좌표→world TRS→기존 광량 a/법선→native texel→linear RGB→sRGB 경로와 픽셀 격자를 보존한다. opt-in에만 `q=0(a<.1)`, 그 외 `q=(1+floor(saturate((a-.1)/(.5-.1))·(n-1)))/n`을 쓴다. n=3의 입력 경계는.1/.3/.5, 출력은0/1⁄3/2⁄3/1이다. 일반 광원의 양수 band 경로는 그대로다. 바닥 높이차1.335m·반경5m에서 최대 a≈.537은 최고 경계.5를 넘는다. 최대/중간/바깥 유광의 RGB 기여는 intensity·.55·q=.22/.146667/.073333이며 intensity는 단계 위치와 별개로 선형 광량을 조절한다. 기존 후처리/exposure는 유지한다. 원본 픽셀과 그림자/가림 자료는 재생성하지 않는다.

[픽셀 판별/실험] N23 실제 diagnostic 두 바닥 ROI(x200:400,y400:580; x720:850,y350:700),1114×857의2×2 phase(0,1) 내부RGB불일치가0이었다. Common worldXYZ snap과 화면격자는 다르지만 cached texel 입력은 이미 일정하므로 삭제할 원인 증거가 없다. 곡선의2/4/6px 계단 길이는 픽셀 크기와 구분한다. N24 actual Play에서는 같은 두 영역의2×2 일치, 세 양수 구간+0·백색 최종 RGB차·기존 N23 대비 유광 픽셀 수 감소·원본193hash·다른 광원 설정 보존을 확인한다. 전체 frame/캐릭터·비native의 합격으로 확장하지 않는다.

[밝기 관리 근거] 보통 광원의 [Intensity](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Light-intensity.html)와 [Range](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Light-range.html), 환경광, 표시용 [Post Exposure](https://docs.unity.com/en-us/engine/6000.0/manual/post-processing-and-full-screen-effects/urp/effect-list/color-adjustments)를 분리한다. 픽셀 명암 단계는 그 조명 입력을 표시하는 ramp다. 이 프로젝트의 SteppedLocalLight는 물리 Light의 lumen값이 아니라 기존 스타일 광량/반경 owner다. 조명은 linear RGB에서 계산하며 정수 픽셀 표시는 공간 표본이고, 노출은 표시 밝기이므로 서로 대체하지 않는다. 이번에는 기존 owner의 intensity/radius와 opt-in ramp만 수선한다.

[현재/실제 관측] `light24/moving-on.png`는 실제 기존 Play 카메라1114×857·21시·30°/350°·원본1픽셀당2×2화면픽셀이다. 실제 GPU의 linear 백색 기여0/.073333/.146667/.22 영역은337030/98330/42722/6640픽셀이며, 최종 RGB의 같은 백색 기여도97696/42722/6640픽셀에서 확인했다. 유광 영역은 N23의458562에서147692픽셀로 감소했다(같은 관측 화면, 약32%). 조명 경계를 포함한 두 바닥 ROI의8900/11310개2×2블록 내부RGB불일치는0이다. 이는 두 영역의 검사이며 캐릭터·모든 사물의 격자나 미술 합격은 아니다. 다른 광원 설정과193개아트hash·같은Player/Camera·map/mesh/TRS를 보존했고 shader error0·Edit 저장을 확인했다. 기존 좌우 이동의 두 위치도 관측했다. 전체씬diff는 같은 광원의radius/intensity 두 값뿐이다. WorkLoop `light24/request.json`→실제Unity작업/관측→`light24_gate.py`가 완료됐으며 원본 제작 재실행은0이다.

## N23 이전 조명 실험 — 범위·밝기 피드백으로 재개

[요구/원인] 사용자는 N22 실제 화면을 두 단계·누런 광으로 판정했다. N22의 Q3={0,.5,1}는 무광0을 포함하여 유광은 두 단계이며, 이를 최종 Native18Band로 다시 분류했다. 기존 기지 SteppedLocalLightFullscreen은 `Blend One One`으로 RGB를 더하지만 native 표면은 stencil2로 제외하고 재료색에 밝기만 곱했다. 설정 white와 fixture의3종 값은 원하는 실제 화면의 증거가 아니었다. N22의 관측/수학 검사는 보존하되 시각 합격으로 사용하지 않는다.

[선택/반례] 단순 bands 증가만으로는 최종 Native18Band의 재분류·목재색 강조가 남는다. 전체 광원/팔레트 변경은 다른 조명을 바꾼다. 선택은 같은 moving light에만 기본false인 native additive opt-in을 주고 기존 기지의 additive 연산을 native 표면 내부에서 한 번 적용하는 것이다. 다른 광원/기존 사용자 변경·193아트·geometry/UV·pixel grid·motion·camera는 보존한다. 3D 전환은 연구만 한다. 광원 색과 표면 색이 같아야 한다는 뜻은 아니며, 백색 광 기여 R=G=B와 실제 무늬·세 유광 구간을 관측한다.

[좌표/연산] N17의 Unity Y-up meter→실제TRS→world position/normal→기존 world-cell→광원감쇠/법선→native texel→linear RGB→sRGB 표시를 재사용한다. a=saturate(1-d/r)^2·saturate(dot(N,L)), Q+(a)=ceil(3a)/3∈{0,1/3,2/3,1}다. 0은 범위 밖/면 반대 방향, 세 양수는 유광 구간이다. 기존 양자화 설정 x의 양수는 기존 경로, 음수는 opt-in과 abs(x)의 유광 단계 수를 운반한다. mode와 band의 소비자는 같은Common 하나며 global 배열/광원owner를 추가하지 않는다. Common에서 normal/opt-in 기여를 분리하며 wrapper는 합을 반환해 기존 다른 소비자를 유지한다. native ReadableNight C는 기존환경/다른광원에서 계산하고 C'=saturate(C+RGBwhite·intensity·Q+·기존strength.55)로합성한다. 나뭇결rank·깊은틈/외곽 검정·coverage/depth는 불변이다. 별도 overlay·blur·RGB연속그라데이션/추가재양자화는 없다. 이는 게임의 기존 백색 additive presentation이며 물리적albedo 조명 복원이 아니다.

[실험/판정] 반경14m·intensity.8·3유광 단계와 움직임은 고정한다. actual GPU의 opt-in 기여 diagnostic에서0+세RGB값/각화면영역, 실제Play원본pixel2px·30°/350°·maps/mesh/TRS·캐릭터/카메라 동일, 백색기여채널 동일·비클리핑 목재rank, shader 오류를 판정한다. 다른6광원 serialized값과 기존Common양수 경로를 보존한다. 원본hash는 기존frozen193개와대조한다. 후보의 시각 결과는 실제PNG로 제출하며 자동 미술 합격을 주장하지 않는다.

[실제 결과] `docs/artifacts/building39/light23/moving-on.png`는 실제21시·30°/350°·2px·원래Player/Camera의게임화면이다. `gpu-additive.png`의linear광량0/.146667/.293333/.44는 각각29,704/291,082/139,228/28,252화면px에존재한다. 실제최종RGB차에서도세백색기여를각각289,506/133,980/28,252px확인했다(8bit변환오차로채널당.015허용). 광원off/on과우측이동출력을보존했다. 193아트hash불변·36재료Tintwhite/strength.55·shadererror0·maps/mesh/TRS/Player/Camera동일이며, 전체8기존광원의직렬화값은새opt-in하나외에불변이다. 저장씬diff는같은movinglight의flag1행뿐이다. 관측후EditMode·saved/dirtyfalse로복귀했다. 최초graph의gate에Edit저장/다른광원검사를추가한뒤기존계약을덮어쓰지않고`request-final/state-final`로연결했으며Unity관측은재실행하지않았다. 최종graphcomplete는이한정조건의검증이며미술완벽·캐릭터수광·움직이는광원의가구차폐그림자·Standalone빌드를증명하지않는다. 원본이미지의전체표면3D/방향별프레임은[O23연구](../../docs/references/pixel_object_multiview.md)이고이번에는제작하지않았다.

실행기 저장 한계: final submit 뒤 atomic state 교체가 WinError5로 막혔지만, 실제 state는 작업 제출을 보존하고 검증 노드 직전이었다. 관측/작업은 반복하지 않고 권한이 허용된 로컬 실행으로 마지막 gate와 state 저장만 이어 완료했다. 이는 기존 WorkLoop 알고리즘 변경이나 Unity 제작 재시도가 아니다.

## N22 이전 조명 실험 — 사용자 피드백으로 재개

사용자 최신 정정: 넓은 백색광의 그라데이션은 기지의 기존 조명처럼 3단계 양자화다. N21의 연속 RGB 보간은 요구 오해로 폐기한다. N21 이전의 Common/NativeReadable/NativePalette/SteppedLocalLight 계산을 복원하고 기존 `surfaceBands=3`을 사용한다. 현재 광원의 백색·motion·world cell·2배 카메라·기하/art를 유지한다. 기지의 기존 Glass centre/Emitter도 같은 Common에서 surfaceBands3을 사용한다. 1차 반경7.6m에서는 높이1.35m인 광원의 바닥 최고a가(1-1.35/7.6)^2≈.676으로, Q3 최고단계의 경계.75에 못 미쳤다. 실제 화면과 이 반례를 보존하고 반경14m로 넓힌다. (1-1.35/14)^2≈.816이므로 최고 바닥 단계가 가능하다. 값 표기만3으로 맞춘 첫 gate는 이 조건을 검사하지 않았으며 최종 미술 성공 증거가 아니다.

연산: `a=saturate(1-d/r)^2 * saturate(dot(N,L))`, `Q3(a)=floor(2a+.5)/2 ∈ {0,.5,1}`, 입사광은 기존 `I=환경/URP+Σ(RGB * intensity * Q)`이다. NativeReadable은 `b=step(.12,Y(I))+step(.4,Y(I))`, 밝기 `{.55,.78,1}`과 기존 양자화 tint를 사용한다. 기존 intensity4.2에서는 `.5*4.2*.55=1.155`여서 중간 광원 단계도 밝기2를 넘는다. intensity를.8로 낮추면 추가 광량은 `{0,.22,.44}`가 된다. 기준 밤 fixture의 Y≈.0447에서는 최종 세 명암 구간이 유지된다. 실제 normal/거리/다른 광원에 따라 한 면이 세 단계를 모두 보이는 것은 필수 조건이 아니다. 픽셀 이미지/팔레트/rank를 변환하는 연산은 없다.

검증: 같은 이동 광원·motion·다른 광원, white/radius14/intensity.8/surfaceBands3/halo0, 바닥 최고단계 도달 가능성, 원본cache와 MaterialMap hash 불변, 복원된 기존 네 계산 파일 일치, 실제21시·30°/350°·2px 카메라 및 최종 Play PNG 한 회. 검사 성공과 건물 미술 완벽은 구분한다. 건물 평면 자동화는 A30 연구 제안이며 이번에 생성기를 변경하지 않는다.

최종 실제 관측: `docs/artifacts/building39/light22/final/readable-on.png`에서 안쪽 밝음·중간·바깥 밤색을 관측했다. settings는 white/radius14/intensity.8/bands3/halo0,같은light/motion·다른6광원,shader error0이다. 실제 활성 바닥 `NativeBuilding39Floor40`의 position/material coverage를 사용한 floorY=.015m에서 최고a=.81838로 기준.75를 넘었다. 첫 바닥 observer는 shop 자식/name에 바닥이 있다고 잘못 가정해 실패했다. 반경 저장은 이미 성공했음을 확인하고 제작 재실행 없이 실제 map 참조로 관측만 교정했다. 실제21시1114×857·30°/350°·2px·같은Player/Camera·maps/mesh/Transform·36재료,art193 hash 불변,4개 기존 계산 파일의8711b7c 일치,밤fixture 최종band0/1/2를 마지막gate에서 확인했다. 1차7.6m 자료는 보존하며 최종graph만 현재 요구 판정이다. 캐릭터별 셰이더·가구 동적 shadow·전체 미술 완벽·Standalone빌드는 검증하지 않았다.

## N21 이전 실험 — 사용자 정정으로 연속 RGB 보간 폐기

사용자 정정: '반딧불이처럼'은 기존 좌우 움직임 요청이며 연두색 광원이 아니다. 현재 moving light의 색 (.78,1,.44), 반경 3.8m를 백색 (1,1,1), 반경 7.6m로 바꾼다. 같은 인스턴스·intensity 4.2·normal influence 1·좌우 진폭 3m/주기 8초·world cell 1/90.5097m·2배 카메라를 유지한다. 원형 경계의 원인은 Common의 4단계 광량과 ReadableNight의 세 단계 밝기/tint다. surfaceBands를 높이는 방법은 마지막 단계에서 다시 경계를 만들어 그라데이션 요구를 충족하지 못한다.

선택: 기존 광원에 continuousFalloff 기본 false를 추가하고 현재 움직이는 광원만 true로 설정한다. 같은 global 배열에서 surfaceBands=0을 연속 감쇠 표시로 사용한다. 기존 g=max(1-d/r,0)^2·max(dot(N,L),0)·intensity 계산을 유지하고, 해당 광원만 광량 양자화를 생략한다. 한 번의 기존 광원 순회에서 총 입사광 I와 연속 광원 기여 S, 나머지 광원 기여 B를 함께 반환한다. Native ReadableNight의 기존 밤색 C는 기존 URP 입사광+B로 직접 계산하여 기본 밤과 다른 조명을 보존한다. 이는 이상적인 I-S와 같지만 half 정밀도에서 밝은 S를 차감하며 작은 밤광이 손실되는 문제를 피한다. B와 S에는 기존 surface strength .55를 똑같이 적용한다. 새 광원 기여는 e=max(dot(S,Y),0), w=1-exp2(-e), T=Albedo·S/max(S)로 분리하고 lerp(C,T,w)로 적용한다. 백색 S는 Albedo 자체를 향해 밝기만 변화한다. 표면 모서리/무늬 rank는 같은 Point 팔레트 값이며 검정 역할은 그대로 검정이다. 0광은 w=0, alpha/coverage/depth/XYZ/normal/UV/픽셀 격자는 불변이다. RGB 이미지를 흐리거나 팔레트 열을 보간하는 단계가 아니다.

검증 범위는 동일 실제 게임 카메라의 밤 light off/on과 광원/2배 배율 readback, 기존 입력 art hash 불변, 셰이더 컴파일, baseline 밤색 수식 불변, 연속 광량의 유한성/단조성/0기여 항등이다. 사용자에게 실제 화면을 제출하며 수치 성공을 미술 완벽으로 승격하지 않는다. 다른 광원·캐릭터 재료·기본 밤색·가구/원본은 재작업하지 않는다.

N21 실제 관측: GameMap1의 같은 moving light에 white/radius7.6/continuous=true를 저장했다. intensity4.2/halo0·같은 motion·다른 활성 광원은 readback에서 불변이며 씬 diff는 이 광원의 세 필드뿐이다. 실제21시 Play 카메라는1114×857·30°/350°·2px, 같은 Player/Camera·maps/mesh/Transform·36재료, shader error0이다. `docs/artifacts/building39/light21/readable-on.png`가 최종 실제 화면이고 `readable-off.png`는 같은 호출의 광원off 관측이다. 거리257표본은 유한/단조/0기여 항등이며 기존 night 함수와 원본cache189+현재MaterialMap4파일 hash가 유지된다. WorkLoop 설정/실제 관측→최종gate는 complete다. 연속 밝기는 원본 픽셀 공간 격자를 변경하지 않으며 밤과 실제광에 따라 RGB가 바뀐다. 별도 캐릭터 PBR·고정 warm 광원의 단계·원본5px marker색은 이번에 변경하지 않았다. 동적 가구 shadow solver·전체 미술 완벽·Standalone빌드는 검증하지 않았다.

## 과거 N16 결정 / R0~R2 (2026-10-04)

사용자가 N15의 표현을 개선된 기준으로 확인하고 그 파이프라인을 정리한 뒤 기지 GameMap1의 테스트 건물 내부 전체에 적용하도록 요청했다. 대상은 PlannedPixelShop33의 활성 실내다. 18종/26개 사물, 기존 구조·지붕·절개·벽등을 대상으로 하며 플레이어·카메라·동선·콜라이더·방의 역할·다른 건물·도심은 보존한다. 사용자 원본 시트와 N15 결과는 그대로 남긴다.

시작 시 직접 관측: GameMap1 Edit Mode, scene dirty=false. 건물 yaw305°, 카메라30°/350°. 활성 renderer46개, 그중18종 사물26개. 건물 nativePixelsPerUnit127은 B34 구조용 cache 해상도이고 현재 B37 사물은31.75 PPU다. N15의90.51 PPU 결과를 이 건물에 붙이지 않는다. 기존 사물의 과도한 표시 높이는 전체 PNG의 평면 역투영이며 실제 부피의 근거가 아니다. 실제 치수·방향·support는 Building37 input-contract, 실제 구조는 이번 placement-baseline.json으로 연결한다.

후보: 완성 PNG에 빛을 곱하는 방식은 고정 명암 중첩 때문에 제외한다. 기본 메시 PBR+전역 pixelization은 연속 명암·이중 픽셀 문제 때문에 제외한다. **실물 semantic geometry→native 위치/법선/재료 cache→기존 Unity 광원→작은 재질별 명암 palette**를 채택한다. 실제 메시를 별도 ShadowCaster로 사용한다. 이 연결이 최소 사물의 광원 변경에서 표면별 반응·변하지 않는 재료/경계를 보여 주지 못하면 실내에 통합하지 않는다.

## 좌표·입출력 계약

- Canonical은 각 사물의 Unity building-local XYZ 미터: X폭,Y상향,Z깊이, Unity 좌수계. 바닥 사물은 수평 bbox 중심이 X/Z0, 발이Y0. 기존 앞면 방향(-Z/-X/+Z), 실물 width/height/depth는 asset 선언에서 고정한다. 숨은 면은 source 복원이 아니라 의미 부품 template의 명시 저작이다.
- 고정 카메라 basis R=(.70710678,0,-.70710678), U=(.35355339,.8660254,.35355339), F=cross(R,U)=(.61237244,-.5,.61237244). camera local yaw45 + root305 = world350, pitch30. 공통 제작 PPU31.75는 현재 사물 표시 밀도다. 새 PNG를 축소하여 맞추지 않고 첫 기하 표본부터 이 밀도를 사용한다.
- Project(P)=(dot(R,P),-dot(U,P))*PPU. native pixel center S=(uR-vU)/PPU, primary O=S-F*far,D=F. finite solid의 최근접 양의 교차가 position·normal·part·chart·mask를 소유한다. box는 slab, 원형 부품은 원통/타원체의 해석적 교차 또는 같은 기하의 triangle ray intersection을 사용한다. 삼각형 분할선은 경계로 칠하지 않는다.
- Native 원점은 투영된 실제 geometry bounds의 floor minimum에서 정수 padding을 뺀 값이다. renderer 표시 mesh는 R/U를 따른 동일 texel domain이고 정수 texel phase만 snap한다. XYZ cache는 renderer local metre로 한 번 저장하며 runtime TransformObjectToWorld/TransformObjectToWorldNormal→현재VP로 깊이를 쓴다. ray t를 SV_Depth로 쓰지 않는다. clip/alpha/실루엣은 실제 기하만 소유한다.
- Geometry는 18종의 의미 있는 부품과 구조의 실제 폐곡면이다. cabinet·shelf 상품·냉장고 선반/병·계산기 콘솔·사과/용기·열린상자·원통·화분/줄기/잎·벽 장식은 서로 다른 template다. 통짜 큐브 사진으로 대체하지 않는다. 유리 냉장고는 frame+손잡이+내용물의 불투명 표면이 depth owner이며 glass는 표현 overlay로 구분한다.
- Material은 관측 palette·재질 ID·intrinsic pattern rank다. N15 목재 reference/관측 RGB와 B37 원본의 추가 역할색·작은 특징을 재사용한다. 광원 방향에 따른 원화의 면 밝기·접촉 그림자 RGB는 cache 재료가 아니다. 무늬 rank에 남은 원화 밝기의 영향까지 완전히 제거하거나 pure albedo를 복원했다고 주장하지 않는다.
- Lighting은 기존 Unity URP main/additional light·SH와 기존 SteppedLocalLight globals를 사용한다. 새 Manager/광원 권위를 만들지 않는다. 입사광은 normal·위치·거리감쇠·shadow에서 계산해 작은 palette를 선택한다. 기본광100·continuous PBR 색 출력은 없다. local fullscreen 재적용은 기존 stencil bit2로 제외한다. stepped presentation light의 동적 가구 그림자는 기존 기능이 아니며 URP light shadow와 혼동하지 않는다.
- Edge는 외곽·명시 깊은 틈만 검정, 실제 crease는 재질 계열색이다. smooth primitive의 triangle/chart tessellation seam은 role0. 빛이 변해도 geometry·material·edge 입력은 변하지 않는다. Native object는 캐릭터 cell expansion/전역pixel renderer에 연결하지 않는다.

## 절차 그래프와 완료 관찰

WorkLoop: geometry→material→native export/preview→CPU invariant→Unity 최소 조명 실험→26개/구조 연결→실제 게임 관측. 최초 4단계는 command.run의 실제 입력/출력/코드 해시를 고정한다. Unity 연결은 기존 오브젝트의 mesh/material 참조와 필수 cache component만 변경하는 한 writer가 맡는다. 단계 실패는 geometry/material/light/edge/binding에 귀속하고 원인 없이 전체 재생성을 반복하지 않는다.

필수 검사:18종 누락0, 실제 declared bounds·support·원본 SHA 불변, mask와finite hit 일치, normal 단위길이/좌표 왕복, surface RGB와조명분리, 검정역할/색모서리일치, 캐시map domain동일, source/PNG이중resize0, 같은assetshared자료, local/VP깊이·캐릭터앞뒤가림, 광원변경시기하/재료불변·서로다른면빛반응, 실제shadow, 지붕/벽절개와동선보존. float허용오차1e-5m와unitnormal1e-5는float32저장기준이며화면pixel표본은정수domain이다.

고정 source sheet에서 모든 디자인이 완벽히 자동 복원된다고 가정하지 않는다. 실제 최종 게임 카메라의 실내와 광원 비교를 함께 제출하며 파일 존재·컴파일·AI 동의를 미술 완성으로 바꾸지 않는다. 컴퓨터 UI 조작은 이번 범위에서 사용하지 않는다.

## 직접 근거

N15의 finite hit·재료/명암/경계 분리, PBRT slab/diffuse, Unity6.5 URP Lighting.hlsl의 GetMainLight/GetAdditionalLight와 world shadow-coordinate API를 재사용한다. 기존 IsometricAtlasSurface의 native-position→VP depth, SteppedLocalLightCommon의 조명 권위·stencil 계약은 실제 코드에서 확인했다. GroundedPropSprite/DeskLivePixelProbe의 unlit card/continuous PBR 표현은 이번 입력에 부적합하다.

## R3~R4 현재 결과와 재개 계약

[현재] `docs/artifacts/building38/run04`의 WorkLoop8노드 완료: geometry→materials→export→CPU invariant→Unity 최소 실험→실험 gate→건물 연결→실제 관측 gate. 진입점은 `Tools/Building38/run16.py`다. 원본 raw sheet/N15 reference를 보존하며 PerfectPixel·Blender beauty·생성 API·완성 PNG 재축소를 추가 호출하지 않았다. 기하에서 native pixel을 처음 제작하는 입력이므로 격자 복원 단계가 아니다.

[현재] 실제 미터 치수18종/26개 사물+17개 벽·지붕·절개면을 원래 renderer에 연결했다. 위치·법선·재료·무늬·경계 map35종은 공유 자산, 실제 폐곡면 shadow child43개다. Floor·기존 벽등2개의 자료와 표시 경로는 보존했다. cabinet inlay·clock ink·poster ink는 실제 표면 안의 material annotation으로 alpha/부피를 추가하지 않는다. 소품 support7개와 clock/poster 중심 anchor2개의 Y만 계산했고 X/Z 이동0이다.

[Play Mode 호출·실제 GPU 렌더] 26개/18종, 기존 Player·Camera 동일, pitch30.000004°/yaw349.999969°, source pixel당 화면4px. 내부 roof hidden1/wall faded9, shader error0. 실내 local light off/on은39,714px 변화. 최소 사물의 같은 renderer/maps를 유지하며 실제 주광 방향만 변경해41,424px 변화했고 실제 caster off/on 그림자는2,354px 변화했다. 기술 gate는 미술 승인·전체 게임 입력 검증이 아니다.

`play-interior.png`는 원래 게임 카메라의4px 표시다. `play-overview.png`는 같은 카메라·각도에서 일시적으로2px 정수 표시한 전체 건물 capture이며 줌은 즉시 복원했다. 제작 PNG 축소가 아니다. Play Mode 종료, Scene View30°/350°, Edit scene dirty=false, surface/caster43이다.

[범위 감사] 원래 GameMap1 serialized535블록 중534개 본문 불변, 변경은 이 건물 PrefabInstance1개다. 기존 override11개/원본 prefabGUID/콜라이더 치수 유지, 원래 블록 삭제0. 추가215개는43개 caster계층과 부모 참조뿐이다. 원본 `PlannedPixelShop33.prefab` 전체 전파는 자동 승인 검토가 다른 인스턴스 영향 가능성을 이유로 거부했다. **GameMap1의 테스트 인스턴스 override**로 저장했고 원본 prefab/다른 건물은 유지한다. 별도 명시 승인 없이 전파하지 않는다.

현재 자료를 사용할 때는 `Assets/Art/NativeBuilding38`과 씬 참조를 재사용한다. 치수/부품 변경은 geometry와 후속 cache, 재질/무늬 변경은 materials/export, 조명 변경은 기존 Unity 광원 단계로 귀속한다. PP31.75는 유지하며 큰 사물은 최초 계산에서 더 많은 pixel을 가진다. 이미지 늘리기·부위별 offset·완성 원화 음영RGB 덧곱은 수선이 아니다.

새 제작 승인 시 `python -B Tools/Building38/run16.py --output <workspace의 새폴더>`를 실행한다. 4단계 뒤 ai.work는 활성 Codex에게 Import/GPU 실험과 기존 인스턴스 Apply를 넘긴다. 사용자가 실행기를 조작하는 절차가 아니다. Importer는 다른 source hash로 기존 공유 자산을 덮어쓰지 않는다. 새 source버전 교체에는 원본 보존·GUID/참조 전환을 포함한 별도 변경 계약이 필요하다.

남은 한계: 숨은 면/상품은 semantic template 저작이며 원화의 자동3D복원이 아니다. 순수 albedo를 복원하지 않았고 wood pattern rank에 원화 밝기 영향이 남을 수 있다. native 윤곽은 해석적 hit지만 곡면 shadow mesh는16분할/8ring 근사다. 냉장고 frame/contents는 있으나 유리 반사·투과 overlay는 미구현이다. Floor/벽등을 새 cache 조명으로 통일하지 않았다. 임의 시점·시점별 cache·사용자 미술 합격·Standalone build·전체 게임 기능은 미검증이다. 현재 결과는 실제 조명이 연결된 한 건물 prototype이며 디자인 완벽/원화99%복사를 선언하지 않는다.
