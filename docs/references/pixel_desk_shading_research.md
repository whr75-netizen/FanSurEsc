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

## D21 — 제작 단계와 오류 귀속을 실제 실행기로 연결

사용자는 D20을 탈락시켰다. 최신 구현 범위는 디자인 구성 요소별 실제 실행 그래프, 결과 부족의 수학적 진단과 제한된 자동 수정, 책상으로 끝까지 적용이다. 기존 Unity/D20 입력은 보존하며 새로운 `Tools/PixelPipeline`과 `LocalOnly/PixelPipeline21`에서만 실행한다. 외형 승인과 99% 재현은 자동으로 통과시키지 않는다.

### 후보와 선택

- 큰 ai.work + 자료 존재 확인: 탈락. 제작 방법 누락을 막지 못했다.
- 문장형 지침 추가/새 대형 프레임워크: 현재 문제의 직접 해결 아님. 기존 WorkLoop를 그대로 사용한다.
- 고정 도구 단계 + 실제 배열/형상 진단 + 상한 있는 파라미터 수정: 채택. AI 호출 없이 inputs→geometry/material→raster→shade→pixel→diagnose→repair/제출 분기를 실행한다. 코드 해시/입력 해시를 고정하고 결과 생성과 결과 판정의 명령을 분리한다.

### 디자인 요소와 계산 계약

| 요소 | 입력/알고리즘 → 산출 | 부족 판정과 허용 수정 |
|---|---|---|
| 구조·비율 | D20 실제 메시의 치수/접합을 읽고 복사 → canonical geometry | 다리 동일성/접지/양수 체적/서랍-손잡이 정렬. 임의 다리 offset 금지 |
| 무늬·재료 | 승인된 평면 oak-user15-source SHA→원본 PerfectPixel center grid64→4단계 grain | 입력 출처와 실제 PP 실행을 확인. 객체 렌더의 명암을 재료로 사용하지 않음 |
| 투영·픽셀 크기 | 공통 직교 카메라, azimuth45°/elevation30°/96PPU, 픽셀 중심 광선 | coarse 격자 고정. 2:1 축 투영, 원본3D를 화상 축소하지 않고 직접 샘플 |
| 명암·접촉 그림자 | world normal·방향광·실제 BVH shadow ray → 3단계 shade index | grain과 독립. 텍스처색/부품명으로 조명 band를 대신하지 않음 |
| 내부 경계 | 실제 가시 면 쌍에서 선을 넣을 한쪽을 고정 → 가시 픽셀 내부 경계 | 면 쌍마다 양면 중복을 검사. 깊이 가림과 선 위치 규칙을 분리하며 숨은 면을 출력하지 않음 |
| 최종 픽셀 | grain index×shade index→고정12색+경계색, alpha0/255 | 임의 smooth 색/중간 alpha/배경 통계로 성공 처리 금지 |
| 화면 가독성 | 공통 서랍 틈의 경계 수직 투영폭과 실제 gap ray owner | 폭<2px면 허용된 공통 gap만 최소 수정. 상한 초과/수정 후 미관측이면 차단 |

재료의 4단계 밝기 분류가 단일 이미지에서 순수 albedo를 복원한다는 뜻은 아니다. 승인된 평면 재료의 출처만 보장하며 원본의 무늬 변화는 남는다. 3조명색×4무늬색도 미술 성공을 보장하지 않는다. 비율/그림체/색감의 남은 부족은 사용자 판단 대상으로 남긴다.

### 좌표·수학·실패 조건 — 실행 전 고정

오른손 meter, X폭/Y뒤/Z위. `r=(cosφ,sinφ,0)`, `u=(-sinφ sinθ,cosφ sinθ,cosθ)`, `d=r×u`. top-left 화면에서 pixel center `(i+.5,j+.5)`를 `O=target+r*(i+.5-W/2)/P+u*(H/2-j-.5)/P+d*distance`로 world 변환하고 `-d`로 raycast한다. Blender evaluated mesh/BVH가 실제 finite 면을 결정한다. material image는 좌상단원점, UV 반복/물리크기를 별도 고정한다.

사이 틈 g의 edge 방향 e와 gap 방향 a에 대해 `k=P*abs(det(Ba,Be))/length(Be)`, `B=[r;-u]`. 수직 서랍 경계는 `k=P*abs(cosφ)`. 앞판 두께 t를 통과하면서 광선은 X로 `s=t*tanφ`만큼 이동한다. 앞/뒤 통로 구간의 교집합 폭은 `max(0,g-abs(s))`이며 실제 가독성 폭은 그 값에 k를 곱한다. 따라서 `g*=max(g,abs(s)+2/k)`이다. 최초 전면 폭만 계산한 `2/k`는 t=.036m에서 통로 전체가 가려지는 반례로 폐기했다. 두 앞판의 외측 span은 고정하며 각폭 `(span-g*)/2`, 중심과 손잡이를 같은 식에서 재조립한다. 최대 gap은 span의5%로 제한한다. 2px/5%는 이번 실험의 명시한 디자인 제한이며 보편적 정답이 아니다. 큰 픽셀 요구를 깨는 전역PPU상승은 금지한다.

`b=quantize(max(0,N·L)*visibility)`이며 visibility는 명시한 기하에서 shadow ray로 측정한다. offset은 float32 좌표정밀도와 scene범위에 비례하는 작은 값으로 기록하는 휴리스틱이며 PBRT의 완전한 오차 경계 구현을 뜻하지 않는다. 접촉 그림자 전체를 제외하지 않는다.

경계 광선마다 선의 소유자를 따로 고르는 최초 방식은 수평/수직 이웃 탐색에서 소유 면이 교대로 바뀌어 같은 직선 양면에 선이 생겼다. pass1 실제 PNG에서 상판↔서랍 정면43쌍이 관측됐다. 후속 수정은 실제 pixel의 깊이/normal/가림을 그대로 사용하면서 `(part,face)` 쌍마다 선을 둘 면을 고정한다. 평행한 전면은 같은 normal에서 `N·position`이 큰 가까운 면, 비평행 crease는 `N·d`가 큰 면을 사용한다. 후자는 명시한 선 배치 규칙이지 깊이 판정의 대체가 아니다. 숨은 면을 그리거나 무한 평면을 화면에 외삽하지 않는다. 실제 PNG의 긴 평행 경계에서 제3면/실루엣 junction을 제외하고 양면 중복을 진단하며, 전역 모든 교차점의 유클리드1px 두께를 보장한다고 주장하지 않는다. 이 구현 결함 수정은 기존 재료/명암의 미술 변경이 아니므로 해당 버퍼를 해시 확인하여 재사용한다.

근거: [Blender Scene ray_cast](https://docs.blender.org/api/5.2/bpy.types.Scene.html), [BVHTree](https://docs.blender.org/api/5.2/mathutils.bvhtree.html), [PBRT 부동소수점 ray 오차](https://pbr-book.org/4ed/Shapes/Managing_Rounding_Error), 아래 D17의 제작자 명암 제어 자료. 표준 ray/투영/양자화를 책상 작업에 연결하는 코드이며 새로운 범용 미술 알고리즘의 증명은 아니다.

최소 최종 확인은 실제 정상/복구 분기, 출처 오류·상한 초과의 차단, 동일 다리·손잡이 정렬, 독립 box slab과 BVH 가시성 대조, PNG 팔레트/alpha, 동일 입력 재실행 방지다. 실제 출력과 수정 전후를 사용자에게 보여 주며 자동 판정은 technical_ready까지만 한다.

### D21 실행 증거와 재개 조건

현재 출력은 `LocalOnly/PixelPipeline21/run01/pass-2/package/desk.png`174×155이며 실행기/사용법은 `Tools/PixelPipeline/README.md`다. 초기 실제통로0px→2.000003px, 접합점 제외 평행경계의 양면중복68→0. 별도 독립감사는 실제 상판↔서랍정면의43쌍→0과 가시선828기록의owner불일치0을 확인했다. pass1→2의 실제 raster/model/shade SHA가 같아 선수정에만 결과가 바뀌었음을 확인했다. `pass2-final-audit.json`에 대상10개해시와 수치를 보존했다.

초기 판정기는 유한두께/선중복을 빠뜨렸고 실행 중에는 NumPy bool JSON 오류도 있었다. 그 결함과 이전 결과는 각각 recovery/reopening-history에 남겼다. 새 진단을 등록하기 전에 모든 부족을 자동으로 알고 있었다는 주장은 하지 않는다. 코드 수정 없는 일반 run/resume으로 완료/실패를 지우지 않는다.

기술조건과 사용자 외형승인은 별도다. 전역교차점의1px선폭, 임의입력물체,99%기준외형재현은 미검증이다. 새 물체나 새 부족이 생기면 물체별 구조/가림/최소세부 계약 또는 측정 가능한 새 진단을 등록하고 해당 단계만 재개한다. 기존 생성원본과 동일99%가 현재목표로 다시 지정되면 별도기법/입력적합성을 검토해야 하며 D21기술통과로 D20실패를 지우지 않는다.

## 현재 D20 — 생성 기준과 실제3D 비교, 99% 미달

최신 요청에 따라 새 생성 기준1장→공통 직교투영 최소제곱→목재추출/로컬UV→실제12솔리드/면색→Blender렌더→원본 전경비교를 실행했다. 아래 D15~D17은 당시 기록이며 이전 결과는 보존했다. 원본전체를 평면/카메라투영으로 재출력하지 않았다.

실루엣IoU95.57272%, 전경합집합 RGB채널당오차<=8 비율50.05545%로99%미달. 동일4다리/접지/투영 기술통과는 외형성공이 아니다. 부위별무늬/국소색을 공통목재로 대체한 한계와 단순형상 잔차가 남는다. 모든3D방식의 불가능성 증명도 아니다. 추가미술수정 중단. 계약은 [D20실험](../../Tools/PixelDeskReference20/README.md), 실제기준/모델/비교는 `LocalOnly/DeskReference20/`다. Unity변경은 없다.

## 사용자 확정과 현재 사실

사용자는 D15/base02 텍스처를 승인했고 D16 결과는 “명암자체가사라졌다”고 거절했다. 첨부 원본의 나뭇결·원본PerfectPixel66×64 재료·UV밀도는 유지한다. 아래 역할 마스크 단독 제안은 D16에서 실제 실행했으나 미술적으로 기각됐다. 기술 검사 통과를 명암 표현의 성공으로 바꾸지 않는다.

**현재 D17:** 빛을 없애는 대신 방향·가림을 명암 영역 선택에만 사용하고 최종색은 별도 유채색 ramp에서 고르는 방법으로 변경했다. Never’s End PDF35·37~43쪽의 실제 광원+cast shadow+shade material+normal 제어, Guilty Gear PDF17~23쪽의 법선·광원·임계값·색 분리가 근거다. [Blender Shader to RGB](https://docs.blender.org/manual/en/4.4/render/shader_nodes/converter/shader_to_rgb.html)는 BSDF 결과를 NPR용 RGB로 변환하는 EEVEE 전용 노드다. 이 부분의 Blender5.2 실행은 실제 렌더로 확인했다.

방향 입력 `max(0,N·L)`과 단일 광원의 가림을 3단계 색 선택에 연결한다. 승인 무늬의 UV와 RGB는 그대로 두며 명암 영역별 곱색만 선택한다. 실제 원본/결과는 `LocalOnly/DeskBlender17/base01/desk.blend`/`desk.png`. 가림 비활성 비교의249픽셀 차이, 재료·기하·투영 보존 확인. 사용자 외형 판정은 대기이며 자동으로 원하는 그림체를 보장하지 않는다. 좌표·후보·실패조건·실험의 단일 원본은 [현재 명암 계약](../../Tools/PixelDesk/CONTROL_SHADOW_PLAN.md)이다.

## D15 당시 구현 확인

현재 출력은 `LocalOnly/DeskBlender15/base02/desk.png`, 원본은 같은 폴더 `desk.blend`. D14저장모델의 실제노드를 읽기전용으로 확인했고 D15는 동일재질설정이다. 광원0개, 최종색경로는 원본texture×면tint×AO2단계→LospecEmission(1). 실제직사광/반사잔존이 원인이라는 설명은 틀리다. 강한조명처럼보이는 색영역 배치가 문제라는 것은 구현과사용자피드백을 연결한 해석이며 단일미술원인의증명은 아니다.

## 공식 자료 비교

| 출처 | 공개 기법 | 현재 책상에 연결할 부분 |
|---|---|---|
| [Never’s End GDC2026](https://media.gdcvault.com/gdc2026/Slides/Juckett_Ryan_HowWeDrawA3DSpriteWorldTheStylizedArtOfNeversEnd.pdf) PDF페이지35,39~44 | diffuse/specular/AO ramp 분리, shade albedo/tint, vertex bias, 편집normal, 별도caster/receiver | 가장 직접적인3D→sprite사례. 그림자용색/위치제어를 분리하고 불필요한self-shadow를 제한 |
| [Unity Toon Shader 기본3색/Shadow Control Maps](https://docs.unity3d.com/Packages/com.unity.toonshader@0.8/manual/Basic.html) | Base/1st/2nd Shade Map과 UV의고정그림자위치map. BaseMap공유가능 | 승인된나무무늬를공유하면서 그림자영역과색만별도데이터로관리 |
| [Guilty Gear Xrd 제작자GDC자료](https://www.ggxrd.com/Motomura_Junya_GuiltyGearXrd.pdf) PDF페이지17~23 | threshold/light vector/normal의제어, vertex별shade bias, 물체별light vector, 독립적인lit/shade색선택 | 단순히조명을끄거나cel threshold만넣어서는의도한2D명암이되지않는구체적제작근거 |
| [ProPixelizer 공식 Uber Shader](https://propixelizer.github.io/docs/technical/ubershader/) | lighting ramp, sceneambient↔constantambient, 별도의normal/edge설정 | scene조명으로인한불필요한색변화를제한하는기성도구후보. 현재프로젝트에설치/사용하지않음 |

Unity Toon Shader와GuiltyGear는픽셀책상전용도구가아니다. 전달가능한것은명암제어원리이며동일외형을보장하는프리셋이아니다. Never’s End전체렌더러가필요하다는뜻도아니다.

## 이전 제안 — 부품역할기반그림자마스크 단독, D16에서 기각

현재의일괄적인면tint×AO를최종디자인권위로삼지않는다. 기본/일반그림자/깊은틈에사용하는색관계와그림자가나오는영역을분리한다. 3색이라는말은이미지전체를3색으로재분류한다는뜻이아니다. 승인된texture는각영역에계속존재한다.

제안표현은 `C=(1-M1-M2)A0 + M1*A1 + M2*A2`, `Mi∈{0,1}`, `M1*M2=0`이다. A0는승인된재료, A1/A2는동일무늬의그림자용색설정이다. RGB를검정으로일괄곱하는한개계수보다부위/재료별로색관계를지정한다. 색설정자체의미술판정은사용자권위다.

M1/M2는책상템플릿의상판돌출밑,서랍앞판경계,깊은조립틈같은구조역할로관리하는후보를권장한다. 부품치수/공통좌표에서일관된규칙으로마스크를계산하면모딩시다시적용할수있다. 이것은자료의control-map원리를현재절차모델에적용하자는제안이며인용게임이똑같은책상알고리즘을쓴다는뜻이아니다.

현재반복나무UV와별도의mask UV/attribute를써야부품별그림자가서로겹치지않는다. 손으로임의pixel을고쳐넣는것이나모든물체에동일한부위offset을붙이는방법으로바꾸지않는다. 임의모델에는part role과mask 입력규약이필요하고무표식mesh에서자동으로그림자디자인을보장할수없다.

## D16 당시 최소실험과 실패 판정

승인된D15texture/geometry/96PPU를고정하고기존AO명암만위마스크경로로바꾼한버전을비교한다. 상판전체강한밝기대비,그림자번짐,부품틈가독성을실제렌더로사용자에게판정받는다. AO단독2단계화를새기법이라고재실행하지않는다. 모서리normal수정이나shadowproxy는이실험에서필요성이생길때만추가한다.

이 실험은 D16에서 실행했으며 사용자는 명암이 사라졌다고 판정했다. 넓은 면의 명암과 실제 가림까지 제거한 축약이 원래 요구와 어긋났으므로 현재 D17에서 영역 선택과 최종색을 분리한다. 자료만으로 외형 개선을 검증했다고 쓰지 않는다.
