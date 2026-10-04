# N17 — 테스트 건물 한 채의 공통 native 표면·실시간 조명 제작 계약

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
