# Radical Fish Games — 환경·오브젝트·조명 렌더링 조사

조사일: 2026-09-20. 상태: **1차 자료 조사 완료 범위 / 프로젝트 구현·실행 없음**. 대상은 CrossCode와 Alabaster Dawn(구 Project Terra)입니다. 캐릭터의 방향별 파츠·애니메이션 상세와 본 문서의 환경 근거를 혼합하지 않습니다. 사용자가 제공한 [공식 YouTube 채널](https://www.youtube.com/@RadicalFishGames/featured)은 조사 출발점이며, 영상 외관으로 내부 기법을 확정하지 않았습니다.

## 1. 결론과 현재 결정

**[사실] 두 게임의 공간 표현과 렌더링 API는 구분해야 합니다.** CrossCode는 3D 좌표·충돌을 2D 렌더링 API로 표시했습니다. Alabaster Dawn은 WebGL의 3D 렌더링으로 전환했으며 deferred shading, 실시간 shadow mapping, HDR 색을 사용한다고 개발자가 설명했습니다. 따라서 두 작품을 동일한 “3D 모델을 픽셀 이미지로 구워 붙이는 방식”으로 묶을 근거가 없습니다. [S01][S02][S03]

**[사실] Alabaster Dawn의 픽셀 표현은 실제 원근 변화와 공존하도록 설계됐습니다.** Felix Klein은 첫인상은 픽셀아트이지만 움직이면 원근 축소가 드러나도록 의도했다고 직접 설명합니다. 캐릭터 쪽은 3D skeleton 위의 2D sprite/billboard를 선택·크기 조절·회전하는 시스템이라고 따로 설명합니다. 이 설명이 곧 모든 환경 오브젝트도 같은 billboard 시스템이라는 뜻은 아닙니다. [S04]

**[미확인] 환경의 정확한 texel/world-unit, 카메라 투영 행렬·각도·FOV, 모든 prop의 mesh/billboard 분류, sprite별 depth/normal 저작법, shadow caster 구성은 확보한 1차 자료에 없습니다.** 이 숫자나 구조를 화면 인상으로 채우지 않습니다.

**[판단] 이 사례에서 채택할 수 있는 설계 원칙은 “3D 공간의 일관성과 픽셀 아트 저작을 함께 유지한다”까지입니다.** 특정 렌더러·에디터를 Unity에 이식하거나, 임의 3D 에셋이 동일 품질의 픽셀아트로 자동 변환된다는 기술 보장은 확보하지 않았습니다. 현재 연구 단계는 R1의 사실/공백 정리이며 R3 실험 통과가 아닙니다.

## 2. 게임별로 확인된 구조

| 항목 | CrossCode | Alabaster Dawn / Project Terra |
|---|---|---|
| 엔진 출발점 | Impact.js의 핵심부를 크게 수정. 렌더링·충돌부를 3D 위치를 처리하도록 재작성 [S05][S06] | 새 HTML5 엔진, WebGL 3D, JavaScript 코드 기반을 TypeScript로 재작성 [S01] |
| 월드 좌표 | x/y는 지면, +z는 높이. entity 위치·속도에 3성분 사용 [S07] | 3D 렌더링 및 높이·원근 개선은 확인. 실제 축·단위 체계는 미확인 [S01][S04] |
| 표시 방식 | Canvas 2D/API. 개발자가 depth buffer 없이 3차원 월드를 그리는 어려움을 명시 [S02] | WebGL 3D + deferred shading + 실시간 shadow mapping + HDR [S03] |
| 원근 | 멀리 있는 물체가 작아지지 않는 pseudo 3D라고 개발자가 설명 [S08] | 의도적으로 원근 축소가 드러나는 표현 [S04] |
| 맵 저작 | 수정한 Weltmeister. collision/entities/background 유형의 layer, tile별 terrain ID, entity 높이 지정 [S09][S10] | 자체 tile 편집기, map cell별 water shader mask, 여러 editor 도구 확인 [S11][S12] |
| 환경·prop | 2D sprite를 3D 위치로 렌더하는 구조까지 확인. 모든 prop의 저작 원본은 미확인 [S05] | 환경 모델/그래픽 제작 담당자와 wind 반응 prop, light별 제어 기능 확인. prop별 메시 구조는 미확인 [S11][S12][S13] |
| 가림 | layer를 지면부터 그리는 방식·caching/prerendering에 관한 개발자 회고, depth buffer 부재 확인. 완전한 정렬 알고리즘은 미확인 [S02] | 실시간 3D/shadow 체계까지 확인. cutout·transparent·billboard의 정확한 depth 처리나 정렬 정책은 미확인 [S03] |
| 조명·그림자 | 이번 조사에서 환경 shadow의 완전한 구현 근거는 확보하지 못함 | 실시간 shadow mapping 확인. light별 속성 제어, 낮/밤별 prop·light 표시 기능 확인 [S03][S11][S14] |
| 재사용 가능한 공개 엔진 | 블로그의 설명용 코드 조각은 확인. 수정한 Weltmeister는 공유할 수 없다고 개발자가 당시 설명 [S09] | 이번 조사에서 전체 렌더러·환경 저작 툴의 공식 배포 소스나 Unity 패키지 확인 못함 |

2013년 글은 해당 시점의 구조를 설명하는 자료입니다. 출시 버전의 모든 세부사항이 동일하다고 확장하지 않습니다. CrossCode의 2D API 렌더링 자체는 2023년 개발자 회고 및 2025년 개발자 비교 설명이 뒷받침합니다. [S02][S03]

### CrossCode의 “3D”가 뜻하는 것

entity의 위치에 높이 z가 있고 실제 게임 규칙·충돌이 이를 사용한다는 사실과, GPU가 3D polygon/depth buffer를 이용해 화면을 그린다는 사실은 다릅니다. CrossCode의 공식 자료는 전자는 명시하고 후자는 Canvas 2D로 설명합니다. 그러므로 “2D이므로 높이가 없다”, “높이가 있으므로 일반적인 3D 메시 렌더러다” 모두 잘못된 분류입니다. [S02][S07]

CrossCode 개발자는 원근 단서가 부족한 상태에서 여러 높이에 있는 투사체를 구분하기 어렵다는 점을 auto-jump 설계 이유 중 하나로 설명했습니다. 이는 높이가 존재한다는 것과 플레이어가 그 높이를 쉽게 읽는다는 것이 별개의 요구라는 직접 사례입니다. [S08]

### Alabaster Dawn의 환경 제작에서 실제로 확인되는 것

2021년 공식 글은 tile editing 도구와 light별 제어, 물 효과를 별도로 소개합니다. 2022년 글은 물 shader가 필요 없는 cell을 mask하는 tool-chain, 바람에 반응하는 환경 prop을 소개합니다. 환경 자료를 넣기만 하면 완성되는 단일 pixelation filter라는 설명은 없습니다. [S11][S12]

공식 팀 소개에는 Martina가 콘셉트를 환경의 모델과 그래픽으로 옮기는 작업을 한다고 명시되어 있습니다. 다만 사용한 DCC, 모델 토폴로지, UV 규격·자산별 mesh 비율을 공개한 자료는 아닙니다. “모든 환경을 Blender로 만든 완전한 메시다” 또는 “모든 환경이 2D billboard다”로 확정하지 않습니다. [S13]

2025년 말에는 저사양 GPU 개선을 위해 더 낮은 렌더 해상도를 검토한다고 발표했습니다. 따라서 픽셀처럼 보이는 텍스처와 실제 최종 framebuffer 해상도를 같은 개념으로 취급할 수 없습니다. 해당 글만으로 원래 내부 해상도나 새 옵션의 최종 구현 수치를 알 수는 없습니다. [S15]

## 3. texel 밀도·화면 픽셀·격자에 관한 수학적 구분

이 절은 **일반 렌더링 수학 및 프로젝트 설계 해석**입니다. Radical Fish Games의 비공개 shader 공식을 복원한 내용이 아닙니다. model/view/projection과 homogeneous divide라는 표준 변환은 [MDN WebGL 공식 구현 설명](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_model_view_projection)에 근거합니다.

| 서로 다른 값 | 정의 | 필요한 입력 |
|---|---|---|
| 자산 texel 밀도 `τ` | 표면의 특정 방향에서 texture texel / world-unit | UV 크기, texture 해상도, mesh 단위·scale |
| 화면 표본 밀도 `ρ` | 해당 방향의 screen pixel / world-unit | 카메라·투영, 표면 방향, 화면 내 위치·깊이, render target 크기 |
| texel의 화면 크기 | 단순 정렬된 경우 `q = ρ / τ` screen pixel / texel | 위 두 값 모두 |
| 최종 확대 배율 | 내부 render target pixel → 표시 화면 pixel | render target/viewport, 확대 filter, 종횡비 처리 |
| grid phase | 정점·카메라·샘플 중심이 픽셀 격자 어디에 놓이는지 | 좌표 원점, rounding 규칙, pixel-center 규칙 |

**[수학] 직교 투영의 단순한 경우:** 화면 세로가 `H` pixel, 수직 시야 높이가 `2s` world-unit이면 view plane에서 `ρ = H/(2s)`입니다. 이는 카메라 평면 방향의 관계입니다. 경사진 바닥·수직벽의 표면 texel에는 각각 투영 단축이 적용되므로 같은 UV 밀도라도 화면 texel 형태가 같다고 보장하지 않습니다.

**[수학] 표준 pinhole 원근의 단순한 경우:** view depth `d>0`, vertical FOV `f`일 때 카메라와 평행한 작은 표면의 `ρ(d) = H/[2d tan(f/2)]`입니다. 따라서 한 고정 `τ`만으로 모든 깊이에서 `q=1`을 만족할 수 없습니다. 이 식은 일반 투영 관계에서 유도한 것으로 AD의 FOV나 내부 카메라 공식을 뜻하지 않습니다.

**[수학] 일반 표면에서는 투영의 국소 Jacobian으로 두 texture 축의 화면 길이·기울기를 구해야 합니다.** 텍스처 해상도나 nearest sampling만으로 perspective foreshortening, 비정수 확대, 격자 위상 변화를 없앨 수 없습니다. WebGL의 `NEAREST`/`LINEAR`는 texture sampling 규칙입니다. 월드의 단위·카메라 투영을 대신 정의하지 않습니다. [MDN texture parameter API](https://developer.mozilla.org/en-US/docs/Web/API/WebGLRenderingContext/texParameter)

**[판단] “보기 좋게 픽셀이 유지된다”는 목표에는 적어도 세 가지 독립 조건이 있습니다.** 원본 그림의 픽셀 밀도, 실제 카메라에서 투영된 크기·왜곡, 동작 중 픽셀 격자의 안정성입니다. AD가 이 셋을 구체적으로 어떤 shader·저작 규칙으로 타협했는지는 미확인입니다. “픽셀 완벽”이라는 말로 확인된 것처럼 표현하지 않습니다.

## 4. 가림·노멀·그림자는 각각 다른 데이터 계약

**[표준 원리] depth test는 화면 fragment의 깊이를 저장된 깊이와 비교하는 기능입니다.** 그림에 보이는 입체감을 해석해 자동으로 뒷면이나 두께를 만드는 기능은 아닙니다. [MDN depthFunc API](https://developer.mozilla.org/en-US/docs/Web/API/WebGLRenderingContext/depthFunc)

| 표현 | 제공하는 정보 | 그 정보만으로 해결되지 않는 것 |
|---|---|---|
| 불투명 color 이미지 | 그린 색·모양 | 표면의 실제 깊이, 숨은 면, 카메라 밖 시점 |
| color + alpha quad | 투명한 구역과 평면 위치 | 이미지 내부의 오브젝트 부위별 깊이·두께 |
| normal map | 표면 방향에 따른 조명 입력 | 실루엣, 깊이, 메시 관통, 그림자 차폐 형상 |
| view별 depth 이미지 | 그 view에서 보이는 표면의 거리 | 기록하지 않은 뒷면, 임의 시점에서 새로 드러나는 면 |
| 실제 surface mesh | 형상·깊이·표면 방향의 공통 원본 | 적절한 픽셀아트 저작, 조명 palette, camera별 픽셀 안정성 |

**[추론] AD의 deferred shading과 실시간 shadow mapping 사용은 픽셀 외관을 유지하면서도 조명을 별도 계산한다는 근거가 됩니다.** 그러나 어떤 sprite가 어떤 normal을 내보내는지, shadow pass에서 원래 2D sprite·별도 proxy·다른 geometry 중 무엇을 쓰는지는 확인되지 않았습니다. 이를 임의로 “normal/depth atlas를 3D skeleton에 붙이는 구조”라고 바꾸면 출처를 넘어갑니다. [S03]

**[프로젝트 시사점]** 책상·벽·나무를 최종 RGBA 한 장으로만 캐시할 경우 캐시가 보존하지 않은 깊이·normal·그림자 형상은 후속 단계가 사용할 수 없습니다. 실시간 광원·동적 카메라·도시 차폐가 요구된다면, 해당 정보의 권위 원본과 캐시의 유효 범위를 먼저 정해야 합니다. RGB 재질 분리 성공만으로 도시의 깊이·조명 통합이 증명되지는 않습니다. 이는 현재 `PIXEL-01`의 문서상 미완료 경계와 연결되는 검토 의견이며, 이번 작업에서 프로젝트 렌더 결과를 재검증한 결론은 아닙니다.

## 5. 모딩 가능한 오브젝트 파이프라인에 가져올 수 있는 것

**[제안] 자산의 픽셀 그림, 월드 형상, 표시 renderer를 서로 구분해 규격화합니다.** RFG의 에디터가 존재한다는 사실은 저작 규격을 정하면 반복 작업을 도구로 줄일 수 있다는 참고 사례입니다. 그들의 비공개 도구와 같은 기능을 이미 확보했다는 의미는 아닙니다.

| 단계 | 모드 입력/원본 | 변환·출력 계약 | 미리 정할 실패 조건 |
|---|---|---|---|
| 형상·재질 저작 | 기존 승인 형상 또는 새 mesh, UV, color/alpha/material | 축·단위·pivot·UV density; 실제 shape를 한 원본으로 관리 | 없는 뒷면·잘못된 단위·불명확한 alpha 정책 |
| 표시 표현 선택 | 3D mesh 또는 제한 view의 sprite/depth 자료 | 대상 camera 범위, shape/normal/depth의 대응 | 허용 view에서 새 면 노출·평면 깊이 오차 |
| 픽셀 표시 | source texel grid + projection + render target | PPU/texel 밀도, sampling, 격자 위상, palette·색공간 | 줌·이동 중 픽셀 크기 불일치나 승인 기준 밖 흔들림 |
| 월드 통합 | 동일 object transform와 원본 형상 | scene depth·shadow·local light의 동일 공간 | 캐릭터/prop 관통 정렬, 조명 시점 불일치 |
| 캐시·교체 | versioned asset ID + 변환 입력 | 어떤 변화에서 캐시가 무효인지 명시 | 카메라/형상/재질 변경 후 오래된 출력 사용 |

기존 3D 형상에서 데이터를 파생하는 후보는 숨은 면·깊이의 원본을 갖는 장점이 있지만, 그 자체가 사용자가 원하는 픽셀아트 디자인이라는 보장은 없습니다. 반대로 hand-drawn sprite는 의도한 모양을 직접 저작할 수 있지만, 자유로운 카메라·새 시점의 정보를 자동으로 갖지는 않습니다. 본 조사에서는 어느 후보도 최종 채택하지 않습니다.

## 6. 재개할 때 필요한 최소 판별 실험 — 미실행

다음은 구현 요청이 있을 경우의 **시험 설계 제안**입니다. 수치 임계값은 원본 크기·허용 시점·출력 해상도가 확정된 뒤 사전에 정의해야 합니다. 여기서 임의 수치를 정하거나 기술/미술 통과를 선언하지 않습니다.

| 질문/가설 | 고정 조건과 변경 변수 | 관찰과 반례 | 결과별 다음 결정 |
|---|---|---|---|
| 선택한 표현이 필요한 camera 범위를 지원하는가 | 승인된 비대칭 prop 1개, 같은 scale·재질·광원; camera만 움직임 | 앞/뒤·상판/측면·가려진 면, 실루엣·pixel density 연속성 | 필요한 면 소실이면 표현 후보 재검토; 임의 offset으로 덮지 않음 |
| depth가 world와 일치하는가 | 같은 prop·camera; 캐릭터 또는 판별용 기하를 전후·사이로 이동 | 정렬·깊이 교차가 참조 형상과 일치하는가 | 캐시 depth 계약 오류와 단순 sorting 오류를 분리 |
| 조명 자료가 동적 광원에 충분한가 | 같은 형상·camera; 광원 위치/방향만 변경 | normal 방향·차폐·shadow 위치의 일치 | 누락된 normal/shape 원본을 식별; baked 색을 곱하는 임시 보정으로 종결하지 않음 |
| 모드 교체가 규격만으로 가능한가 | 동일 renderer·world 단위; 같은 규격의 자산 1개 교체 | 수동 scale·pivot·shader 예외 없이 작동하는가 | 실패하면 입력 규격/변환 경계를 수정; 모드별 보정 목록 증가를 자동화로 포장하지 않음 |

이 시험은 조명·가림·camera 경계를 구분하기 위한 것입니다. 최종 그림체·형태·색과 실제 연속 움직임의 만족도는 사용자가 요청한 미리보기로 확인해야 합니다.

## 7. 미확인 범위와 조사 한계

- **texel density:** 두 게임의 공식 world-unit 기준 픽셀 밀도, texture/viewport 해상도 표준 수치는 확보하지 못했습니다. 커뮤니티 추측이나 화면 픽셀 세기로 대체하지 않았습니다.
- **AD 환경 geometry:** full mesh·billboard·부분 투영·타일별 표면 혼합 여부를 자산 유형별로 확정할 공개 소스는 확보하지 못했습니다.
- **AD camera:** 원근이 존재한다는 개발자 설명은 확보했으나 실제 FOV, 각도, 특수 projection, vertex snapping 유무는 미확인입니다.
- **lighting:** deferred/shadow mapping/HDR은 확인했습니다. G-buffer layout, normal 생성, shadow caster, alpha/discard 및 transparent 정렬의 상세는 미확인입니다.
- **DCC/툴 공개:** 자체 편집기의 존재와 일부 기능은 확인했습니다. 환경 전체가 Blender/Aseprite에서 만들어진다는 확정 근거나 배포 가능한 전체 도구는 확보하지 못했습니다. CrossCode용 Weltmeister 비공개 설명은 2013년 당시 답변입니다.
- **영상/실행:** 공식 채널과 개별 영상의 web 본문은 cache miss였고, 별도 읽기 요청은 HTTP 200을 반환했으나 실제 영상·자막의 기술 내용은 검증하지 않았습니다. 데모·게임 파일 다운로드, 역공학, renderer 실행, Unity 검증을 하지 않았습니다.
- **판정:** 미확인은 “해당 기술이 없다”라는 증거가 아닙니다. 정확한 shader/asset 규격이 추가 공개되거나 직접 분석 권한·필요성이 생기면 해당 질문만 재개합니다.

## 8. 1차 자료 목록

기술 사실은 공식 글, 개발자 직접 답변·인터뷰에 근거합니다. Steam/Reddit 일반 사용자 댓글은 기술 근거로 채택하지 않았습니다. 직접 인용을 길게 복제하지 않고 관련 주장만 요약했습니다.

- **[S01]** [Alabaster Dawn 공식 presskit — History/Features](https://www.radicalfishgames.com/presskit/sheet.php?p=alabaster_dawn): Project Terra라는 구명, HTML5/WebGL 3D, JavaScript→TypeScript, 2.5D 표현.
- **[S02]** [Radical Fish Games 공식 AMA, 2023-02-21](https://www.reddit.com/r/JRPG/comments/11836dh/ama_were_radical_fish_games_developer_for/): CrossCode 2D API/Canvas 렌더, 3D collision/physics, depth buffer 문제에 관한 개발진 답변. thread 내 “CrossCode entirely in a 2D plane” 질문과 답변 참조.
- **[S03]** [Regiden 개발자 답변 — Options for higher performance?, 2025-09-30, 댓글 #8](https://steamcommunity.com/app/3110760/discussions/0/592909603984916294/): Lachsen 설명을 개발자 계정이 인용하여 AD의 3D/deferred/shadow mapping/HDR을 확인. 일반 사용자의 성능 수치·해설은 근거에서 제외.
- **[S04]** [Felix Klein 직접 인터뷰, TestingBuddies, 2024-10-16, 질문 8](https://testingbuddies.de/interview-mit-radical-fish-games-die-macher-von-cross-code-und-project-terra-im-gespraech): 픽셀 외관과 원근 축소의 목표, skeleton 위 sprite/billboard 설명.
- **[S05]** [Lachsen의 CrossCode TechDemo 설명 — Impact 공식 포럼](https://impactjs.com/forums/games/techdemo-crosscode-throwing-energy-balls/page/1): collision/render engine rewrite, 3D 위치의 2D sprites.
- **[S06]** [Architecture of CrossCode #1, 2013-03-10](https://www.radicalfishgames.com/?p=277): 수정한 Impact.js, data/code 분리, JSON 맵과 비동기 로딩.
- **[S07]** [Movement Physics of CrossCode, 2013-01-12](https://www.radicalfishgames.com/?p=72): 3D position/velocity와 x/y ground·z height 설명.
- **[S08]** [Why do we use auto jump in CrossCode?, 2013-09-29](https://www.radicalfishgames.com/?p=1168): 높이 layer, 원근왜곡 부재와 높이 판독의 어려움.
- **[S09]** [Weekly Update #1, 2013-01-20](https://www.radicalfishgames.com/?p=96): Weltmeister 맵 유형·terrain editor. 하단 개발자 답변은 editor 공유 제약 설명.
- **[S10]** [Weekly Update #15, 2013-04-26](https://www.radicalfishgames.com/?p=485): Weltmeister의 3D positioning·정확한 entity height 지정.
- **[S11]** [One last update for A New Home!, 2021-03-30 — Our Next Game](https://www.radicalfishgames.com/?p=7136): Project Terra의 물, 개별 light 제어, tile editor 소개.
- **[S12]** [Project Terra Progress, 2022-04-19](https://www.radicalfishgames.com/?p=7294): 바람 반응 환경 prop, water shader cell mask, editor tool-chain.
- **[S13]** [RFG 공식 팀 소개 — Martina/Flora](https://www.radicalfishgames.com/?page_id=17): 환경 모델·그래픽 및 technical art 담당 범위.
- **[S14]** [Happy New Year and Progress, 2024-01-12 — Nighttime Visuals](https://www.radicalfishgames.com/?p=7499): 낮/밤별 light·prop 표시; 당시 설명한 낮밤 전환은 실시간 흐름이 아님.
- **[S15]** [2025 Wrap-Up, 2025-12-20 — Demo Reception](https://www.radicalfishgames.com/?p=7879): 저사양 GPU를 위한 lower-resolution rendering 검토.

관련 프로젝트 문서: [현재 상태](../ai/CURRENT_STATE.md), [픽셀 모딩·깊이 렌더 연구](pixel_modding_render_pipeline_research.md), [그래픽 연구 계약 §1.4–1.5](../ai/UNITY_ENGINEERING_PLAYBOOK.md). 본 문서는 이 문서들의 상태·요구를 변경하지 않습니다.

[S01]: https://www.radicalfishgames.com/presskit/sheet.php?p=alabaster_dawn
[S02]: https://www.reddit.com/r/JRPG/comments/11836dh/ama_were_radical_fish_games_developer_for/
[S03]: https://steamcommunity.com/app/3110760/discussions/0/592909603984916294/
[S04]: https://testingbuddies.de/interview-mit-radical-fish-games-die-macher-von-cross-code-und-project-terra-im-gespraech
[S05]: https://impactjs.com/forums/games/techdemo-crosscode-throwing-energy-balls/page/1
[S06]: https://www.radicalfishgames.com/?p=277
[S07]: https://www.radicalfishgames.com/?p=72
[S08]: https://www.radicalfishgames.com/?p=1168
[S09]: https://www.radicalfishgames.com/?p=96
[S10]: https://www.radicalfishgames.com/?p=485
[S11]: https://www.radicalfishgames.com/?p=7136
[S12]: https://www.radicalfishgames.com/?p=7294
[S13]: https://www.radicalfishgames.com/?page_id=17
[S14]: https://www.radicalfishgames.com/?p=7499
[S15]: https://www.radicalfishgames.com/?p=7879
