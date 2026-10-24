# E 캐릭터 픽셀 렌더: 실제 실행 파이프라인

2026-10-23, 기록 547. 기록 번호는 적용 버전 번호가 아니다. 이 문서는 현재 소스와 실제 Walk 버퍼를 설명한다. 이상적인 새 설계를 구현 사실로 표시하지 않는다.

## 사용자용 요약

현재 코드는 단순히 메시를 작게 찍는 한 단계가 아니다. **움직인 표면 → 투영/재질 표본 → 영역 선택 → 표면 색 공급 → 머리·몸 가림 → 외곽선 색 → 눈 → 월드 합성**을 거친다. 옷 모드에서는 표면 표본보다 먼저 닫힌 디자인 영역을 만들고 채움 권한을 제한한다. 기본 OFF 경로는 여전히 래스터 표본과 이전 윤곽 선택을 사용한다. 전신 모든 부위가 하나의 선행 디자인 경계를 공유하는 목표는 아직 완료되지 않았다.

546 왼팔 사건은 색이 마스크를 뚫은 문제가 아니다. 작은 곡선을 생략한 뒤 그 결과에서 큰 경계 구간을 다시 찾으면서 구간의 끝을 잃었다. 그래서 543의 넓은 선두 구간 제약이 적용되지 않았고, 면적 비용만으로 두 셀이 허용 영역에 남았다. 547은 **큰 구간의 참조는 단순화 전 경계에서, 실제 채움과 비용은 단순화 후 디자인 영역에서** 받도록 한 곳을 수정한다. 색/깊이/눈/외곽선 셰이더와 544 최적화는 바꾸지 않는다.

사용자가 보는 겉옷·상의·하의·스타킹·신발은 독립 렌더러 5개가 아니다. 아래의 재질 슬롯과 의미 부위를 구분해야 한다. 얼굴만 분리 렌더되는 구조는 존재하지만, 그것이 얼굴 회색 현상의 원인이라고 확인된 것은 아니다.

## 1. 부위 레이어: 실행 순서와 다른 분류

원본 3개 렌더러, 15개 서브메시/재질 슬롯이다. `Full319View335.Initialise`, `FullFeature367.Role`, `Canonical333`이 번호를 연결한다. 숫자 `role`은 셰이더 역할, `owner.x`는 보통 role+1, `owner.y`는 해부학/표면 part이다. **Body 서브메시 3과 왼팔 semantic part 2는 서로 다른 번호 체계**다.

| 시각 부위 | 원본 렌더러/슬롯 | role | 옷 공통 모드 |
|---|---|---|---|
| 겉옷·양쪽 소매 | Body/3, Tops | 10 | 적용, 같은 함수·설정·격자 |
| 하의 | Body/1, Bottoms | 8 | 적용 |
| 신발 | Body/2, Shoes | 9 | 적용 |
| 이너 상의·스타킹·몸 피부·손 | Body/0, Body_SKIN 공유 atlas | 7 | 제외. 슬롯만으로 서로 분리 불가 |
| 입·홍채·하이라이트·얼굴 피부·흰자·눈썹·눈선 | Face/0..6 | 0..6 | 변경하지 않음. 눈 전용 합성 경로 |
| 머리카락 | Hair/0..3 | 11..14 | 변경하지 않음. 511/513 실험은 별도 OFF |

`Clothing540=14`는 비트 1·2·3을 뜻한다. 옷 종류 14개 또는 3개라는 뜻이 아니다. `BodyAndClothing540=15`는 Body0 전체도 포함하는 시험이며 선택적 상의/스타킹 모드가 아니다. 이 시험의 얼굴 소유권 문제는 미해결이다.

머리/몸 카메라 분할은 `HeadLocal367.DrawSource`: main은 renderer0, head는 renderer1·2. 눈 근거 레이어 13개(`FullFeature367.Eyes`/`Eye253R3Layers.Selected`)는 피부·홍채·반짝임·흰자·눈선·눈꺼풀·전체 머리·눈썹·눈을 제외한 바탕·원본 얼굴·backing·등록 머리·나머지 머리다. 같은 메시의 다른 합성 근거이므로 독립 모델 13개가 아니다. 추가 348 표면 표본은 피부/흰자/홍채/눈선/머리/눈썹/몸 7개 그룹이다.

## 2. 좌표와 버퍼 계약

| 표현 | 단위·정의 | 변환 주체 |
|---|---|---|
| 변형 정점, UV, normal, triangle | 모델/월드 좌표, 원본 UV, 원본 primitive | 실제 Animator와 `surface.Evaluate()` |
| CPU 곡선/마스크 | 좌상단 원점 480×272 연속 논리셀 좌표. 셀 [x,x+1]×[y,y+1] | `Full319View335.Project`: x=(clip.x/w·.5+.5)480, y=(.5−clip.y/w·.5)272 |
| GPU 논리 버퍼 | 480×272, 업로드 때 y=271−CPUy | `ClothRegion524.Prepare`/기존 Read·Top·Bottom |
| native 표본 | 960×544. 중심/보조 표본의 projection shift를 명시적으로 적용 | `PrepareCurrent.nativeShift`, `Prepare333` |
| 머리 지역 격자 | 같은 논리 pitch, head bone을 따르는 카메라. main과 정수 XY offset 및 depth offset | `PrepareHead`, `GridJoin367` |
| 최종 화면 | 960×544, 논리셀 1개→화면 2×2픽셀. bilinear 축소 아님 | `Native395.Present`: q=floor((p+.5−origin)/scale−delta) |

`Owner=(role+1, semanticPart, positiveViewDepth, signedGlobalSourceID)`. `ResolvedMeta=(depth, role+1, auxiliary, signedGlobalSourceID)`. 같은 role은 같은 triangle 또는 같은 시선을 의미하지 않는다. 색 비교만으로 표면 정합을 판정하지 않는다. 조합에는 sourceID/primitive/UV/depth/좌표 변환이 함께 필요하다.

핵심 논리 버퍼는 `before`, `colour`, `owner`, `prepared`, `preparedOwner`, `preparedMeta`, `preparedUV`, `postLine`, `resolvedMeta`, `resolvedUV`, `domain`, `audit`. 대부분 RGBAFloat/point sampling이다. `native[0..7]` 및 `motion.raw[0..6]`는 색·normal/facing·물리 명암·원색·메타·UV·월드 대응 자료이며 크기가 서로 다르다. 진단 파일은 전신 bbox만 잘라 저장해도 헤더에 원점과 크기를 보존한다.

## 3. 시간순 실행과 단계별 쓰기 권한

아래 경로는 실제 `Gameplay397.Present → HeadLocal367.RenderFrame` 기준이다. RenderGraph pass 숫자만 정렬해 CPU의 두 번 렌더를 생략하면 실제 순서와 다르다.

| 순서/실제 함수 | 입력 → 출력 | 하위 알고리즘·수정 권한 | 지켜야 할 계약 |
|---|---|---|---|
| 1 `Gameplay397.BeginGameplay/Present` | 기존 PlayerMovement·Animator → 현재 Walk/Idle/Run 및 변형 표면 | 수동 preview graph 종료, 실제 controller 사용. pose metadata만 sourceFrame으로 전달 | 정지 preview를 실제 걷기로 대체 금지. `Source329`의 과거16포즈 UI는 현재 실제 Animator 경로와 구분 |
| 2 `NativePlayer395.SetLocalCamera`, `Full319View335.PrepareCurrent`, `HeadLocal367.Refresh` | 현재 camera·정점·머리 pose → effectiveProjection, proxy, source metadata | 카메라 정렬·현재 표면·눈 provider/투영 갱신 | 같은 pitch, 원본 UV/primitive 정체성. CPU/GPU 반셀 이동 혼용 금지 |
| 3 (옷 ON) `ClothRegion524.Prepare/PrepareSingle540` | 변형 Body, UV opacity, parts → Source/Curves/Areas/Selected/Atlas | 아래 §4의 선행 영역 생성. 1·2·3 슬롯을 같은 함수로 처리 | 색/명암 계산 전 영역 권위 확정. Body0·Face·Hair 임의 포함 금지 |
| 4 `HeadLocal367.PrepareHead`, headCamera.Render | Face/Hair 표면 → head prepared/layers/눈 표본 | 머리 카메라 분리 렌더. 머리 전용 외곽선 중복 적용은 생략 | 머리 split 자체는 회색 오류 증거가 아님. offset/depth 일관성 |
| 5 main camera 첫 렌더: `FullFeature367.Probe/Native/Metadata/LegacySignals/Eyes` | 표면·재질·빛 → raw480/native960, 부분 metadata, legacy480/960, layers | raster coverage, UV/alpha cutoff, URP 명암 표본, 원본 class/색 endpoint | 조사 패스는 원표면의 색/UV/깊이/owner를 함께 기록. 셰이더 교체는 probe 역할 |
| 6 `Canonical333.CanonicalMetadata` | rawmeta·원본 태그·membership → surface/normal/family | Body primitive를 part/globalID로 연결. cream/stock/skin 분류 | semantic 분류만 변경, 알파를 새로 디자인하지 않음 |
| 7 `Prepare333.NativeColour/Prepare` | 물리 명암·원색·center/native·선택마스크 → before/colour/owner/preparedMeta·UV/gridSurface·Palette | 색: Body role7..10은 profile 기준 `step`으로 lit/shade, 나머지는 원본 색. 선택된 옷 셀에서 center 없으면 같은 슬롯 native4표본 조사 | 활성 옷은 Selected 밖에서 제거. 빈 셀에 다른 파트 RGB 복사 금지. coverage 비용과 색 양자화는 별개 |
| 8 `RestoreStyle335.Restore` | legacy class/lit/shade + 선택 UV → before/colour/UV.z | 기존 스타킹 모드와 얼굴 원래 명암 endpoint 복원 | coverage/owner/depth 변경 금지. `faceMain` 분기 존재; 회색 현상의 실제 원인으로 아직 확인되지 않음 |
| 9 `HeadLocal367.JoinBare`, (별도 trial)`PostView366.Inject` | head prepared + main → 합쳐진 before/colour/owner/meta/UV | 깊이 비교로 가림. 366 trial은 4× ROI coverage·층별 morphology·ordered/depth 합성 | 현재547에서366은 OFF. 511의 source-ray513은 머리/몸 전용 별도 OFF. 모든 합성을 해결했다고 주장 금지 |
| 10 `OwnerLines333.Seed/Flood/OwnerLines` | 합쳐진 before/owner/부분표면/palette → colour, audit, postLine | 외부 빈 영역 4-neighbor flood(752dispatch), 외곽·내부선·thin 판정, 기존색×lineTone 또는 own-family deep shade | RGB만 바꿈. 알파·Selected 불변. thin 예외를 마스크라 부르면 안 됨 |
| 11 `HeadLocal367.DeferredEyes`, `EyeRenderer367.Dispatch`, `EyeFeature348` | postLine·눈 표면/anchor·가림 → 눈 domain/색/owner | MainToHead→기존 eyeMerge→348Evaluate/Unpack/Merge→EyesToMain. 44d13c0 fallback/equaldepth outline 보호 유지 | 본인 domain과 실제 가림/표면 근거. 이번547 수정은 눈 알고리즘 변경 없음 |
| 12 `Prepare333.Resolve`, `HeadRegion502.Gate`(해당 trial만) | 최종 색/owner + 권위 mask → resolvedMeta/UV/audit | 최종 활성 옷 영역 재확인. 머리 gate는 실험 ON일 때만 | downstream이 옷 영역 밖 alpha를 되살리면 위반. 정상 앞가림은 selected 영역 일부를 숨길 수 있음 |
| 13 `HeadLocal367.RenderFrame` CPU 구간 | 첫 렌더 buffers → actionMap 또는 연속표면 packet | 기존 readback. 옷 OFF는 `ContourSelect333.Build`. 옷 ON은 옷 경계가 기존 열린 arm frontier를 대체하고 `ClothSurface525.Prepare`로 빈 채움만 공급 | 두 경계 선택을 직렬로 겹치지 않음. packet은 실제 동일 표면 UV·깊이·normal·primitive. 가까운 색 임의 복사 아님 |
| 14 main camera 두 번째 렌더 | 갱신 actionMap/표면 packet → 같은 5~12 단계 재실행 | contourReady=true, 최종 표면/선/눈 재합성 | 첫 렌더의 donor miss를 최종 누락으로 오판 금지. 반대로 실제 최종 누락은 audit+색+owner로 확인 |
| 15 `FullFeature367.Composite`, `NativeWorldFeature395`, `Native395.Present` | final480 + 월드960 color/depth → 실제 게임 출력 | 월드 깊이 판정, 정수2배 배치. captureNow=false일 때 domain/role/source/UV 일치에 한정한 기존 history 선택 분기 | 세계 가림 유지. 이 history는 곡선 형태의 시간 최적화가 아님. 최종 픽셀변화0을 품질 기준으로 삼지 않음 |

현재 기본 경로에서도 `PostView366` 표본/진단 준비 코드가 남아 있을 수 있으므로 **Inject가 OFF인 것과 그 주변 계산이 전부 생략되는 것은 다르다**. 배치된 객체/콜백의 실제 실행 상태를 별도로 확인해야 한다.

## 4. 옷 공통 경계 하위 알고리즘과 547 수정

1. `OpacityRegion525`: 원본 UV, alpha cutoff/변환을 반영한 유효 표면을 모델 불변 전처리에 저장. `UseOpacityCurves527`은 텍셀 조각 전체를 매번 복제하지 않고 해당 경계 표현을 재사용한다. 변형 정점의 투영은 매 포즈 갱신한다.
2. `ClosedRegion524.BuildSegments`: 투영된 유효 경계의 교차/합집합으로 방향 있는 폐곡선을 구성한다. 526 공간 후보 제한은 중복 탐색을 줄이는 기존 경로다. 이 Source는 원본 center-sampled raster mask가 아니다.
3. `ClosedRegionDesign539.Fit`: x/y 양축·양부호의 극점에서 양쪽 진행 방향과 반환 구간을 찾는다. 접선 진행이 단조이고 바깥 return의 부호 면적이 0보다 크고 **1논리셀² 이하**면 통째로 chord 대체 후보가 된다. 작은 면적부터 겹치지 않는 구간을 선택하며 winding·자기교차를 검사한다. 임의 부분 RDP chord를 반복 잘라내는532와 다르다. Bezier가 아니라 **선분 폐곡선**이다.
4. `CurveArea511.Compute`: fitted closed region과 각 논리셀의 교차 면적 A∈[0,1]. 8×8 표본 면적이 아니다. 505의 전체 메시 정확 합집합 엔진을 매프레임 사용하는 것도 아니다.
5. `BoundarySpan543.Groups`: 큰 바깥 return(면적>1)의 순서/진행으로 선두를 찾고, 연속3셀 각각 A>0 및 안쪽2셀 A=1인 후보만 묶는다. 합계 A가 가장 큰 창을 택한다. 좁은 정상 끝은 이러한 넓은 안쪽 지지가 없으므로 일괄 삭제되지 않는다. **547부터 반환 구간 탐색 입력은 Source, A와 지지는 fitted Curves의 면적이다.** 생략한 미세 return을 다시 채우는 규칙은 아니다.
6. `HeadRegion502.SelectRegions543/Compact544`: 기존 단일 cut에서 E=Σ[selected?1−A:A]+.14Σwᵢⱼ[labelᵢ≠labelⱼ]. 가로/세로 w=.58578644, 대각 w=.29289322. 그룹 내부 label 차이에100000 연결 비용을 준다. 544는 비그룹 A=0/1 고정셀 등을 정확히 제거하여 같은 선택 결과를 계산한다. 시간 bank, RGB 이력, 후단 dilation 없음.
7. `ClothRegion524.Prepare`: part별 mask를 RGBA atlas에 업로드. `Prepare333`, probe의 옷 gate, 연속 packet draw, `Resolve`가 동일 선택 영역을 소비한다.
8. `ClothSurface525`: 설계상 채워야 하지만 center/native표본이 없는 셀은 실제 연속 삼각형에서 점/UV/barycentric/world/normal/depth/primitive를 구한다. alpha/실제 앞가림을 확인한 packet을 기존 셰이더로 다시 그린다. donor의 존재만으로 가림 통과를 가정하지 않는다.

상수1셀²·3셀·2셀은 **목표 논리 격자의 디자인 규칙**이다. `Project`가 월드 길이를 논리셀로 환산하므로 source/world 단위 고정값은 아니다. 해상도를 바꾸면 같은 셀 숫자의 월드 크기는 달라진다. 480×272 외 해상도를 일반 지원한다고 검증하지 않았으며, 연구에서 유일하게 유도된 최적 상수라고 주장하지 않는다. 앞서 검토한2016 spatial shape term이나 곡률 근사공식의 완전 구현도 아니다.

### 4.1 형상 영역과 명암/그림자 영역: 공유되는 부분과 없는 부분

사용자의 지적처럼 **영역의 경계를 정하고 격자에 배정한 뒤 채운다는 수학적 구조는 공유 가능**하다. 다만 영역을 만드는 입력과 그 영역의 권한이 다르다. 형상 영역 S는 존재하는 캐릭터 표면의 범위를 정하고, 명암 영역 H는 그 안의 색 상태를 정한다. 공통 계약은 `shadeAllowed = S ∩ H`이며, H 변화가 S 바깥 alpha를 만들면 안 된다. 현재 옷 모드는 이 실루엣 제한을 공유하지만 H를 폐곡선으로 디자인/선택하는 단계까지 공유한 것은 아니다.

| 단계 | 형상: 실제 구현 | 명암/그림자: 실제 구현 | 공통화 판단 |
|---|---|---|---|
| 영역 근거 | 변형 기하·UV opacity의 닫힌 경계 | `Probe331/Native333`: GetUnityLighting, 유효normal, DotNL, directLightAttenuation, MToon shade. `physical=(ndl,attenuation,shade,viewDepth)` | 입력은 다르다. 그림자 받는 표면·차폐·빛 위치는 형상 투영만으로 얻을 수 없음 |
| 경계 표현/곡선 정리 | Source→Fit539 선분 폐곡선 | 현재는 physical/legacy class 표본. 명암 폐곡선 추출·Fit539 연결 없음 | 명암 전용 폐영역이 정의되면 `CurveArea511` 등 기하 계산은 재사용 가능. 현재 표본을 이미 연속 경계인 것처럼 취급하면 안 됨 |
| 격자 배정 | 면적A와 경계 비용·span→Selected | `Prepare333`: `lit=step(profile.y,ndl)*step(profile.z,attenuation)`; role3/7 일부는 `Restore335` legacy classifier | 동일480격자이지만 동일 영역선택 알고리즘 아님. 단순 임계값 명암은 여전히 내부색 전환을 일으킬 수 있음 |
| 내부 채움 | 실제 표면 UV·원색·normal·depth packet | 선택된 lit/shade endpoint 또는원색×profile.x; thin/선색은 이후 OwnerLines | 표면/소유권/실루엣 gate를 공유한다. 명암용 새 alpha/owner를 만들어 형상 권위를 덮지 않아야 함 |
| 가림/화면 합성 | 같은 surface depth, HeadJoin/Resolve/Native395 | 그림자로 어두워져도 depth/coverage를 바꾸지 않음 | 기존 최종 가림·채움 제한을 공유 가능/일부 실제 공유 중 |

그림자 경계도 target-cell 단위의 곡선/영역으로 만들려면 **같은 표면에 대한 명암 영역의 연속 표현**이 먼저 필요하다. 현재 제공되는 light/shadow 값은 raster 표본이므로, 이를 연속 참조 경계와 어떻게 대응할지 정의되지 않았다. 옷의 `1셀² return 생략`과 `넓은3셀 span` 정책을 그림자에 그대로 복사하는 것은 검증된 공통화가 아니다. 좁은 형태 끝과 좁은 음영이 같은 의미라는 보장도 없다. 명암의 region 표현 이후 교차면적·영역 내부 제한·packet/fill은 재사용 후보이고, 필수 입력과 디자인 정책은 구분해야 한다. 이번547에는 새 그림자 구현을 넣지 않았다.

위 내용은 **캐릭터가 받는 명암/그림자 경로**의 소스 확인이다. 월드 전체의 별도 픽셀 그림자 기능까지 같은 구현이라고 감사한 결과는 아니다. 광원 shadow map/cascade의 공간과 최종 카메라 픽셀격자도 구분해야 한다.

## 5. 546 사건을 실제 값으로 역추적

최신543 저장 Walk68, phase≈.8500057. **캐릭터 왼쪽 소매** Body/3, role10/owner11, 해부학 part2. (200,73)/(200,74), global source11300/11298, primitive182/180. 1×2논리셀=2×4화면픽셀이다.

| 단계 | 확인된 값·판정 |
|---|---|
| Source의 큰 구간 | 깊이3.7999878셀, 면적41.276278셀², 접선 단조=true |
| Fit539에서 작은 구간 생략 | (203.8861389,86.6783218) 부근 return 깊이.231933594셀, 면적.240015713셀². x204.1180725 수직 chord로 대체 |
| 옛 Groups543 재탐색 | 작은 극점이 없어져 다른 먼 구간까지 이어짐. 깊이26.658966셀, 면적1054.164295셀², 접선 단조=false → 선두 그룹 생성 이전에 탈락 |
| 실제 두 셀 면적 | A=.5410143733/.6193720698 |
| 그룹 없는 cut | 두 셀 제거: 면적 +.3207728863, 경계 −.1640202105, 합계 +.1567526758. 따라서 두 셀 유지 |
| Prepare→PostLine→Final | 68번 두 셀 alpha/색 동일. 최초 돌출은 CPU Selected에 이미 존재 |
| thin 명도 | 68번2셀 span→thin=true;69번3셀 span→thin=false, 기존 deepCream 적용. 69번에 두 셀이 사라졌다고 보고하면 틀림 |
| 547 | Source의 큰 구간 구획을 참조해 동일 group/cut 규칙 적용. 68두 셀 제거. 면적·색·선·가림 계산은 유지 |

65번은 fitted curve에도 구간 끝이 남아 기존543이 동작했다. 양팔이 다른 셰이더를 쓰는 문제가 아니라 동일 함수가 받는 경계 구간 표현이 달랐다. 반대팔 실제 비교점(214,84)은 Body3 primitive836/semantic part3이고 A=1, 내부 arm/torso 경계다. 화면의 오른쪽 아무 돌출을 오른팔로 간주하면 안 된다.

별도 한계:546 D4 검사에서16/69번의 동률 창 선택이 일부 반전/회전에서 달랐다. 현재 `score>best`와 순회순서의 영향이며68번 원인으로 입증된 것은 아니다. 547은 그 별도 규칙을 동시에 고치지 않는다.

## 6. 중복·계약 충돌·추적 한계

| 항목 | 현재 사실과 한계 |
|---|---|
| 재추론으로 구간 정보 손실 | Fit539 이후Groups543이 큰 구간을 다시 찾던546 결함. 547은 Source참조로 분리. 명시적 persistent arc ID를 새로 만든 것은 아님 |
| 영역/선 두께 기준 | 선택은 fitted 면적·선두3/안쪽2 지지, OwnerLines는 가시 coverage/해부학 part/3셀 지지. 가림이 이후 달라질 수 있어 RGB thin 변화까지 모두 제거된다는 보장 없음 |
| 반복 렌더·동기 readback | main2회 + head1회 및 native/legacy/multiple layer raster. `RenderFrame` 내부 readback은 현재 실제 비용이다. 외부 진단 PNG/파일 비용과 별도 |
| flood·메모리 | 외부영역 752dispatch, 반복 배열·RT readback·packet 준비. 544 cut 최적화가 전체 비용을 해결하지 않음 |
| 모델 일반화 | 원본4/7/4슬롯·태그·Face provider·등록 머리 triangle 구간 등 모델 의존 정보 존재. 옷 공통 알고리즘과 모델 자동 의미 분류는 다른 문제 |
| 표면 소유권 | role만 같아도 같은 surface 아님. 기존512/513은 제한된 hair/body source ray 계약. Body0 얼굴덮임은 별도 미해결 |
| 품질 검증 범위 | mask누출0은 downstream 계약만 검사한다. mask 자체의 가시, 내부명암, 가림, 모든 프레임 시간 연속성은 실제 전신 출력에서 별도로 검사 |
| 회색 얼굴 | 사용자 관측 사실.530/이후 시험에서 미재현. 얼굴 분리 렌더·RestoreStyle 분기는 존재하지만 원인 확정/해결 아님 |
| 시간 선택 | 515~522 전역arcDP/state bank는 미채택 종료.547에 포함되지 않음. 현재 boundary 선택은 프레임별 공간 선택 |

## 7. 검증·비용과 읽을 자료

547 저장 입력251개(81포즈×3슬롯+정상 얇은 끝8개), 실제인접7쌍 및 전체루프 결과는 연결된547 검증 기록을 따른다. 저장마스크 대조는 실제 렌더 검증과 구별한다. `UseSimplifiedSpanReference546`은 이전 입력을 재현하는 진단 switch이며 정상 span 모드에서는 false다. 제품 기본 Clothes OFF, 활성348/기존540 모드와 사용자 설정은 보존한다.

544 동일 출력 최적화의 기존81쌍 결과: 선택 중앙값22.3029→2.1455ms, 경계43.2429→23.0643ms. core347.002→323.3646ms는 Editor의 기존GPUreadback 포함 호출시간이며 PlayerFPS가 아니다.545 all-thread call-window allocation은 별도 양성대조 통과 지표; `GC.GetAllocatedBytesForCurrentThread`의0은 양성대조 실패로 사용하지 않는다. 현재547 품질 비교의 렌더시간에는 cold start/고정순서 영향이 있어 독립 benchmark로 해석하지 않는다.

주요 코드(모두 `Assets/EUnityValidation01/` 아래):

- [실제 Gameplay](../../Assets/EUnityValidation01/MatchedPlayer397/Gameplay397.cs), [프레임 오케스트레이션](../../Assets/EUnityValidation01/HeadLocal367/Runtime/HeadLocal367.cs), [RenderGraph 패스](../../Assets/EUnityValidation01/HeadLocal367/Runtime/FullFeature367.cs)
- [공통 옷 경계](../../Assets/EUnityValidation01/ClothRegion524/Runtime/ClothRegion524.cs), [539 단순화](../../Assets/EUnityValidation01/ClothRegion524/Runtime/ClosedRegionDesign539.cs), [543 구간](../../Assets/EUnityValidation01/ClothRegion524/Runtime/BoundarySpan543.cs), [공통 선택기/544](../../Assets/EUnityValidation01/HeadRegion502/Runtime/HeadRegion502.cs), [연속표면 채움](../../Assets/EUnityValidation01/ClothRegion524/Runtime/ClothSurface525.cs)
- [Prepare/Resolve](../../Assets/EUnityValidation01/GameMapIntegration333/Shaders/Prepare333.compute), [분류](../../Assets/EUnityValidation01/GameMapIntegration333/Shaders/Canonical333.compute), [색정책](../../Assets/EUnityValidation01/MinimalRestore335/Shaders/RestoreStyle335.compute), [외곽선](../../Assets/EUnityValidation01/GameMapIntegration333/Shaders/OwnerLines333.compute)
- [머리 합성](../../Assets/EUnityValidation01/HeadLocal367/Shaders/GridJoin367.compute), [눈](../../Assets/EUnityValidation01/HeadLocal367/Runtime/EyeRenderer367.cs), [실제 화면 배치](../../Assets/EUnityValidation01/NativePlayer395/Shaders/Native395.compute)
- [현재 상태](CURRENT_STATE.md), [전체 개발 이력](../../unity_development_progress.md), [543 계약](../artifacts/clothing-span543/CONSISTENCY543.md), [544 최적화](../artifacts/clothing-compact544/README544.md)

로컬 상세 증거: `C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Elbow546/` 및 `Fix547/`. 원본 버퍼와 과거 실패를 보존했다. Library403은 재시도하지 않았으므로 메인.html과 로컬 자산이 전달 경로다.


## 550 동일시선 가림 입력 (기본 OFF)

`HeadLocal367.UseCentreBodyRay550`: 원래 centre hair와 body가 겹칠 때만, head 카메라에서 계산한 몸 깊이로 JoinBare를 판단한다. 기존 head `centreMeta[1]`의 torso 필터를 해제하여 모든 body part를 그리며 새 RT/패스는 없다. main torso 입력과 Face/eyes/world 경로,511·491 대체 패킷은 그대로다. 권위 있는 영역 선택 변경이나 헤어 틈 일괄 채움이 아니다.

Walk24 (216,48): hair main depth13.70192792를 다른 ray의 Body13.70149994와 비교해 잘못 버렸다. 같은 source ray Body13.70083141(head좌표)는 Hair13.69875908보다 뒤다. 아래(216,49)는 같은 ray에서도 몸이 앞이어서 유지한다. 실제3쌍+전체81쌍:17포즈22표본 복구, alpha0변경/face·eye·비헤어 안정색0변경/source 동일, 기본OFF 복원. 새 성능통과 주장은 없다.

손32/33/34는 Body0 source 삼각형 중심 표본의 출몰이다. Body0 얼굴35/36/41은 같은 ray에서도 머리 피부가 앞이므로 깊이 오류만으로 해소되지 않는다. 공유 material을 몸/손 의미 범위로 잘못 동일시하지 말고 머리 피부 소유권 분리가 남는다. 헤어 양/음 영역 디자인과 내부 명암도 별도 미완료다. [검증/제한](../artifacts/body-hair550/RESULT550.md).

### 551 몸·손 적용 범위(기본 OFF, 실제81쌍)

Body0의 주 연결 성분에는 머리와 몸이 이어져 있다. 명시적 Humanoid Head 하위 뼈 영향이 없는8,762삼각형만 공통 영역 처리에 넣고 머리/혼합 목1,260개는 원본 렌더를 유지한다. ClothRegion524.Scope551의 원본 primitive 범위표가 OpacityRegion525 경계 입력, Probe331, Prepare333 donor/Resolve, ClothSurface525 표면 후보에 공통 적용된다. 모델/화면좌표/프레임별 예외나 얼굴 깊이 바이어스가 아니다.

동일547 Clothes+550 기준 대 몸·손 포함81쌍에서 얼굴/눈/헤어 소유권 및 얼굴색 차이0, 채움 누락0. distal 손끝 표본114중2개가 생략되어 모든 세부 보존은 미확정. 경계 계산 중앙값52.25ms/p95 91.26ms(별도 공급0.12/21.22ms)로 기본 실시간 채택 근거는 부족하다. 당시 실패한GC.Alloc 대신553에서545의Bytes Recorder로 호출창 할당을 확인했다(아래). 명시적 Boundary540/Experimental551 Body-hands 모드로 시험 가능하며 Off로 복원한다. [증거·한계](../artifacts/body-scope551/RESULT551.md). 헤어 양/음 영역 및 내부 명암은 별도다.

### 552 헤어 음의 영역: 기존 경로 재사용 검사

550 이후35번 head-cell(226,54)의 얼굴 한 셀은 source 단계에서 발생한다. 기존514의 같은 포즈 곡선 면적은 약0.981셀로 머리 선택이 유지된다. 현재 프로젝트 실제34/35/36의550기준 대 기존511/513 경로3쌍에서도 틈 채움, 눈 소유권/색 차이0, 머리 마스크 밖 쓰기0을 확인했다. 새 헤어 제품 코드는 추가하지 않았다. 기존 공간 선택의 음의 영역 지속ID/폭 정책,514 선택 반전과217~228ms packet 합산 구간(Select/BodyRay512/AddQuad/Upload)은 미해결이므로 OFF/미채택이다. [실행 범위와 근거](../artifacts/hair-gap552/RESULT552.md).

### 553 외곽선의 빈 영역 계약 / 554 손끝 미채택

관리 대상의 선택 형상이 확정된 뒤,옆 빈칸의 화면 외부 연결 여부가 같은 표면의 선색을 바꾸면 국소 형상 계약과 어긋난다. 실험553은 기존 OwnerLines333의 outer 입력만 `ext>0`→`!covered`로 대체한다. closed domain의 빈 이웃은 enclosed hole이어도 경계다. 같은551 non-head primitive 범위를 쓰며 얼굴/눈/헤어는 기존 경로를 유지한다. thin·팔레트·alpha/Selected/깊이는 바꾸지 않는다.752 flood는 남겨 성능 변경과 분리했다. 기본OFF,명시적 Experimental553 메뉴.

옷색10표본 중5는 global exterior 연결 변화,5는 실제 이웃 coverage 변화다. 실제10쌍+옷-only56/UV self-repeat53의2포즈 조회에서553 기대 선색을 확인했다. mask/owner/meta/alpha 보존,관리 role 외 최종색 변화0.53 최초 UV strict 차이는 좌표 미보존으로 원인 확정하지 않았고,추가53 exact/56 self-repeat에서1.49e-8 헤어 UV 변동을 별도로 기록했다. 새81루프/전체 비트동일 판정은 없다.

손끝33/49의 source→Fit 면적은 .485724→.471973/.506141→.463276이다. Fit539가 정상끝 일부를 작은 outward return으로 생략하고 현재 셀 선택도 제외한다. 유지된 extrema 인증554는13오프라인 사례에서49를 복구하지 못해 제품 미적용. 손끝 보존과 전체 시간품질 미완료. 음의 영역의 지속ID/폭/덩어리 단위 선택 역시 현재헤어 cut에 없다.

545 Bytes Recorder 양성대조를 통과한553 한 포즈 Prepare 호출창 전체 스레드 관리할당 중앙값은 Clothes4,882,678B/Body55111,908,437B(각5회,3워밍업)다. readback/파일은 창 밖이며553 선 최적화나 Player프레임 수치가 아니다. [원인·수정·검증·한계](../artifacts/owner-lines553/RESULT553.md).

### 555 두 말단 표본의 최소 반례(제품 변경0)

같은33/49 source→Fit exact재현 후 기존 면적/선택기로 원면적·Fit면적과543그룹 유무를 분리했다. 두 표본은그룹소속0이며,그룹을제거하거나원면적을써도제외된다. 셀유지해는가능하지만원수식에서Fit기준+.22007445/+.15545775,원면적기준+.02855140/+.06972821만큼비싸다. Fit정보손실은영향을키우지만단독원인이아니고3셀소매제약이이두표본을강제삭제한것도아니다. 단순Fit복원패치를넣지않았다.

554의49셀은source극점이매핑되지않고Fit새극점만매핑돼exact원점조건에서거부된다. 기존말단가중치≥.5분류는표면관찰표본이며손가락전체소실판정이아니다. 실제가시말단의참조경계/양자화extent대응을기존3포즈자료로확인하는조건이남는다. 제품/새촬영/554재실행없음.512는선택된Hair의source-ray몸깊이를Mask.BA에기록하고513JoinBare가소비할뿐,음의영역component를선택하지않는다. [원비용·최소 반례·가장 작은 다음 검증](../artifacts/hand-counterexample555/RESULT555.md).

### 556/557 영역 면적과 공급 표면의 귀속 — 미채택·복원

556의33/49는실제국소alpha축소이나손가락전체소실은미확정으로정정한다. 별도로48손기부는같은Body0의뒤다리까지합친Fit면적약.582로선택하고앞손원영역약.333의UV를공급해한프레임나타난다. 재질/role동일을같은표면으로간주한영역구성의정보손실이다.

557A의앞면연결성분별독립Fit/cut은목표가시를제거했지만같은면적의손목셀도이웃지지분리로빠졌다. B는원래전체Fit/선택기를유지하며첫prepared owner/sparse packet의원본primitive에면적과최종허용공급을맞췄다. 두후보각실제15쌍에서공급범위위반0이나B에도새손내부빈셀이남아채택하지않았다. 앞면연결성분은실제가림을클립한전체손디자인범위가아니다. 코드철회/기존553·547복원,전체루프미실행. [정확한규칙·대조·실패·최신전신구간](../artifacts/surface-owner557/RESULT557.md).

558은50의한셀(231,87)을동결조회해firstowner/원source/기존선택exact를확인했다.B는원손합집합.999506을앞공급패치.217875로대체하며,동일이웃항-.410051에도유지−삭제비용-1.409062→+.154199로false를만든다.뒤손7122는같은시선에실제로opaque이며전체Body0마스크false와고정공급자때문에함께지워진다.A는뒤손성분원면적.931310을독립Fit .450592로줄인뒤모든기여성분을제외했다.삼각형별선택/원래공유변의파손/최초깊이오판이아니다.합성영역의contributor와앞조각생략뒤공급을표현하는계약이현재1bit재질mask+공급자1개에는없다.새분리·문턱·fallback/제품패치없음.헤어음영역계약은별도보존한다.[558입력과수식](../artifacts/surface-owner557/TRACE558.json).

### 563/564 연속 음의 영역 출력 계약 — 기본 OFF, 전체 시간품질 미채택

기존 CurveArea511 sweep → 원본 ring/segment 경계ID·좌우관계·연속 음의 면적/셀 교차면적 → NegativeRegion563.Feature → 기존 SelectRegions543 → 기존 공통mask Draw/Gate/513합성 순서다. 중심 셀0이어도 Feature는 보존한다. 소유면적>.5는 기존 면적오차의 비교이며 새 시간 문턱이 아니다. 563의 전영역 equality는 떨어진 소유 셀까지 묶어 실제 새 구멍을 만들었으므로,564는 기존8이웃으로 연결된 부분만 강제하고 singleton은 원래 cut에서 선택한다. 소스 영역ID/면적을 버리거나 새로운 후처리를 덧씌우지 않는다.

저장81입력과 실제8쌍 후 실제81쌍:2,049 source Feature 보존,예측불일치/새닫힌구멍/공급누락/공통경계밖쓰기0.17–19기존4→0→0 관계 유지와 알려진목덜미반전 해소,50–52목표틈 유지. 다만16번1×2열린틈 등 다른 시간출몰은 미판정이며 기본채택하지 않았다. 가시눈/opaque몸앞가림 표본0,내부명암/기존약222ms패킷/손561손목실패는 별도 미해결이다. [규칙·실패·81프레임 전신·제한](../artifacts/hair-groups564/RESULT564.md).


### 565 국소 틈 범위와 소유 셀 그룹의 불일치 — 코드 변경 없음

564의16번 열린틈은원연속영역이사라진것이아니다.같은X경계40~44영역과두셀틈면적은증가하지만,다른가지의거의빈셀이소유그룹에연결돼강제그룹1→4→3/비용-.3551→+.6545→-.3659로H/empty/H를만든다.축별bounded음의영역을OR결합하면배경을통한가지간결합이생기며,반대로양축소유교집합만요구한한번의15사례대조는51정상틈을다시닫았다.미채택·제품미적용.원본arc정보를사용하는국소틈가지/입구의연속범위정의가남고,소유셀연결성으로그기준을대체할수없다.새DP/후처리/수치조정없음. [실제입력·비용·단일대조실패](../artifacts/hair-groups564/DIAGNOSIS565.md).


### 566 국소 source가지/입구 → 기존선택기의 대안 — 기본 OFF

CurveArea511의이미계산된연속구간접속→분기/합류사이1-in/1-out최대chain→ordered좌/우arc·source이벤트level/구간·이웃branchID·연속면적→셀교차면적→기존8이웃cut의순서다. 셀수나>.5로가지존재/ID를정의하지않는다. NegativeRegion563.Branches566와HeadCurve511.UseNegativeBranches566가564그룹생성의대안이며후단filter가아니다. false의564/기존source-ray가림과공통mask권위는보존한다. sourcearc는기존triangle/barycentricControl511에연결되며새의미/깊이추론없음. terminal구간표기만으로전체2D틈개방/닫힘까지증명하지않는다.

16의가지입구0:44와51의입구0:56은원곡선에서유지됐다. band재분할불변/저장81대조후실제6쌍에서16순간틈제거와51기존틈유지를동시에확인했다. 소유셀0가지도보존한다. 새실행자체branch재구성오차0이고과거실행과의미세기하차이는분리기록했다. 전체실제루프/모든회전·가림·시간품질·성능은미검증이므로기본OFF/전체채택보류. [정확한표현·검증·새실제전신구간](../artifacts/hair-branches566/RESULT566.md) · [현재계약](../artifacts/hair-branches566/CONTRACT566.md).


### 567 전체 검증과511 방향 입력 한계 — 전체채택실패/OFF

25f3281의564/566을yaw80에서실제81쌍비교했다.16/51/목덜미개선과공통경계/공급계약은유지,얼굴coverage·동일비헤어meta색차0.30셀관측중16의3은기존버그수정,다른27은형태판정미확정이다.원Walk변형을566차이로세지않고모든프레임전신비교를보존했다.

가시눈/앞가림표본이없어yaw260의실제3포즈를보완했으나564/566모두머리0/0/2셀로공통입력실패.첫0의주링투영signedArea+525.50→-263.13,positive-winding영역518.85→2.70이최초단계다.현재Control511의같은3Danchor순서투영이모든방향에서권위있는가시폐곡선역할을보장하지않는다.분기나최종합성문턱으로해결할문제가아니며방향별절댓값/반전패치없이한계보존.원본입력의뷰적합성/가시경계역할이검증되기전범용Player채택금지;현재는검증한referenceyaw80preview후보/OFF다.

별도HeadRegion502.Prepare측정은readback/파일창밖CPU·Unityupload호출만이고566median256.37ms중기존packet221.43/area3.45ms다.GPU시간/PlayerFPS아님.545Recorder양성대조0/51만할당신뢰·16은미측정.유효호출창median약12.96MB,전체할당/GC·성능통과로확대하지않음.품질미통과이므로새최적화없음. [전체실행·분류·실패·정확한성능창](../artifacts/hair-full567/RESULT567.md).

### 568 손가락 논리 영역·국소 가림/선색 — 설계 비교만

현재 원본의 양손30마디+손/팔/다리6개 Humanoid 연결을 읽기 전용 확인했다. 두 prefab 참조는 같은 원메시이며 손/팔 혼합218정점·388삼각형이다. 물리 메시 분할보다 원index/UV/skin·혼합 연결을 보존하는 논리 계통이 우선 후보이고 가중치는 면적/가시성/닫힌 디자인 경계 자체가 아니다. finger ID·표면 patch·선택 region·ray를 분리하고 국소 겹침의 깊이순 유지 표면을 공급해야 한다. 손가락 전체 우선순위로 대체할 수 없다. 기존 외부/내부 OwnerLines reason은 재사용 후보지만 손가락 가림을 현재 구분하지 않는다. 48/50은 기존561 통과,47은 공유 손목 선택OR에서 구멍이 생겼고 기여자별 비용 미기록이라 동시통과 미증명이다. 새 손 코드·메시 분할·촬영 없이 [실제 매핑·혼합 입력·세 사례·필요 계약](../artifacts/hand-proposal568/RESULT568.md)에 분리했다.
