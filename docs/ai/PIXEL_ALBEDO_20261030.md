# 팔레트·단색 대조 인계 — 2026-10-30 고정 스냅샷

이 문서는 저장 프레임 실험의 재현 인계다. Unity 제품 적용이나 미술 승인 기록이 아니다. 제품의 현재 구현 판정은 `CURRENT_STATE.md`와 실제 코드가 우선한다. 앞 절은 프레임95 팔레트 실험이며, 별도 sequence의 연속 프레임47은 마지막 절의 독립 보관본으로 구분한다.

## 버전 관리 경계

- 감사 기준 제품: `master`, `a976f69c2c34c25978c3ebf90bb9f3b0838f53a6` (2026-10-26). 이 커밋의 제품 위에 기존 미커밋 변경이 있으므로 HEAD만으로 현재 실행 상태를 재현할 수 없다.
- 감사 시 기존 상태: tracked 수정 30개, untracked 2,158개, staged 0개. 작성자를 추정하지 않는다. 진행 중 Unity/캡처 파일은 이번 문서 커밋에서 제외한다.
- 초기 문서 커밋 `6094e02`에서는 `EXP27`, `EXP30`이 모두 Git 저장소 밖이라 코드가 제외됐다. 이후 직접 승인에 따라 완료 코드·작은 fixture·대표 증거를 [저장소 보관본](../../experiments/pixel-pipeline/2026-10-30-source-diagnostics/README_KO.md)에 복사했다. 원본은 그대로 보존하며 제품 적용이나 새 Git 저장소 생성은 아니다. 재생 범위와 제외한 전체 자산은 그 보관본의 manifest와 외부 입력 계약을 따른다.
- 아래 상대 경로·SHA256은 고정 실험을 식별한다. 이름에 포함된 v3/v4나 파일 수정 시각을 제품 버전 또는 채택 순서로 해석하지 않는다.

경로 약칭은 다음과 같다. `%USERPROFILE%`은 해당 Windows 사용자의 홈이다.

```text
PRODUCT = %USERPROFILE%\Documents\work\Fantasy Survival Escape Game
EXP27   = %USERPROFILE%\Documents\Codex\2026-10-27\task-2\render-fix21
EXP30   = %USERPROFILE%\Documents\Codex\2026-10-30\task
REVIEW  = %USERPROFILE%\Desktop\작업폴더\아트검토
```

## 입력과 원색 출처

고정 입력은 `EXP27\author33\feature34\source-export\bundle\prelight-source.json`과 같은 폴더의 `frame-source-data.json`을 함께 사용한다. frame 95, 논리 32×40, 표시 64×80, hair mask 368셀이다. 원본 재질/UV/unlit 색 표본을 보존한다. 화면 평균이나 과거 기본색 `#321C1D`를 albedo로 간주하지 않는다.

| 식별자 | 값 |
|---|---|
| sourceId | `95d042f14adf8e99685f26838beeb00ab57773e445e5997d16a9c61d0f1e2c3f` |
| 원본 AvatarSample_A.vrm SHA256 | `0e2fd0fc90308da3172ecf4e674fdeb4f054ebd617005caa5b997a2ca339cce3` |
| geometry packet SHA256 | `76fc49b722854b71f9112462b4a4753b1c59549eb700ab84b887f5257d2bf9cc` |
| 과거 sourceId — 혼용 금지 | `8d6a0a4cb858aab8e95db46aa5113cfd7bdaec7682c4c4f1bfa2618c0d4a8aa6` |

Geometry packet은 `EXP27\author33\feature34\ribbon-path\GEOMETRY_PACKETS.json`이다. 같은 capture sourceId라도 centre 표본과 geometry-selected 표본의 g/UV가 다르므로 packet SHA까지 확인한다. `EXP30\flat-albedo-control\INPUT.json`의 context/bindingReceipt가 실제 짝을 기록한다.

R6 웹 원색 공급 연결은 `REVIEW\31_머리색_슬라이더\index.html`에 있다. 이 파일의 확인 SHA256은 `138efb1e484004bf707d0b18e055ac4e41e1eb1072c14cf1f8cfcec30688a206`이다. 원색 공급 구현과 팔레트/영역 품질 완성을 구분한다. 이 경로를 수정하거나 재배포하는 인계가 아니다.

## 후보별 판정과 재개점

| 고정 경로 | 확인된 내용 | 판정/남은 문제 |
|---|---|---|
| `EXP30\palette-v3` | 공유 native16 팔레트로 두 bank의 과도한 점프 수정 | 실제 appearance 대비 9쌍 일부 손실, v2 대비 추가 톤 경계 113개. 전체 경계 수가 113이라는 뜻은 아니다. 채택 아님 |
| `EXP30\palette-v4-feature` | 16/32/64색 비교. 7개 painted source 쌍과 1개 same-Q 대비 보호, 약한 1쌍은 강제하지 않음 | 64 예산에서 검사한 대비 조건 충족. known358셀 출력51색, RGB 4연결214개/단독184개. unknown10의 원색 통과가 남은 비교 후보이며 제품/미술 완성 아님 |
| `EXP27\author33\feature34\region-colour40\contrast-bounded` | main 영역 후보의 대비 보호 검사 | coherent 후보는 일부 단독셀 감소와 대비 회귀 동반. contrast-bounded는 변경 모두 거절되어 RGB변경0/단독184 유지. 개선 채택으로 표시하지 않음 |
| `EXP30\flat-albedo-control` | 실제 단색 source override, frozen g/Q/P 짝 비교, 원색 통과 재현·최소 수정, PNG 검수 | 이 인계의 완료 진단. 단색에서도 Q 분단 잔존. 연속 프레임/전체 곡선/제품 통합 미완 |

v3 계약 `SHARED_NATIVE_PALETTE.json` SHA256은 `7acc7a4ce281eabe22e9092d4638b1dba063e575b536aceca5085af2d9ba412f`, v4 `CONSTRAINED_64.json`은 `03b7147e90782bd0fd68a5b7271d2df57bf09a0fdd731f6b556acdf70ee17979`다. 원본 패턴 보존과 gradient 제거 가설 중 미술안을 확정하지 않았다. 간격 배율은 팔레트 간격에 적용하며 최종색에 연속 g를 곱하는 방식으로 대체하지 않는다.

v4 공개 비교본은 `REVIEW\35_특징영역_공유경계후보\palette-feature-v4\INDEX.html`이다. `REVIEW\시작.html` → 기존 35 링크 → 새 9쌍/native16·32·64 링크로 열린다. 직접 사용자 승인 후 추가했고 기존 비교본은 보존했다. `EXP30\palette-v4-feature\PUBLICATION_VERIFIED.json`에 178개 파일 해시 일치와 Chrome/Edge 표시 각12검사를 기록했다.

## 단색 대조에서 확정한 것

`flat-albedo-control`은 원본 asset을 바꾸지 않고 source RGB만 상수로 치환한다. geometry/camera/g/threshold 및 짝 비교의 팔레트를 고정한다. 무조명 control은 g를 입력에 보존하되 출력에 사용하지 않는다.

단색 시험 RGB8 `(94,64,63)`은 실제 native texel의 가중 OKLab medoid다. material12/image18/texel(166,236), image SHA256 `4f6f96e95177d14cb292355c55d34bd23d6aaadb652a811cd5ec15792a08d124`. native texel 1,572,864개, 고유 RGB8 8,255개에 같은 규칙을 적용해 관측 texel을 선택했다. 제품 기본색이나 원래부터 단색인 머리라는 주장이 아니다. 모델 변경 시 원본 데이터에서 다시 계산해야 한다.

| 검사 | 원본 패턴 입력 | 단색 입력 |
|---|---|---|
| 같은 legacy P 고정 | 입력189색 → 출력51색, RGB 4연결221개/단독188개 | 입력1색 → 출력2색, RGB 4연결6개/단독1개 |
| 같은 diagnostic P 고정 | 입력189색 → 출력51색, RGB 4연결224개/단독193개 | 입력1색 → 출력3색, RGB 4연결11개/단독6개 |
| 무조명 | 입력/출력189색, RGB 4연결295개 | 입력/출력1색, RGB 연결1개/단독0개 |

- 기존 P는 같은 기준색에서도 Q0/1, Q2/3이 중복색이었다. 별도 diagnostic P에서 native span/anchor를 보존해 참조 인덱스 `[19,19,23,23]`을 `[19,20,22,23]`으로 분리했다. 이것을 단색 입력만 바꾼 효과와 혼동하지 않는다. 실제 점유 Q는 1/2/3이며 각115/101/152셀이다.
- 과거 unknown10 원색 통과 정책은 단색 무조명에서도 8색/기대 팔레트 밖10셀을 재현했다. 단색 분기에서 368셀 전체 override로 수정했다. 원본의 불확실성 metadata는 남긴다. 과거 v4/제품은 수정하지 않았다.
- 현재 main 저장 결과의 실제 colourRegion+Q 키에서는 다중 RGB 위반0이다. featureDomain+Q만 쓰면 서로 다른 색 구역이 합쳐진다. 구역 ID의 의미를 생략해 위반으로 단정하지 않는다. 상세 `CURRENT_PIPELINE_AUDIT.json` 참조.
- 정상 오프라인 6분기에서 기대 recipe 밖 RGB0, 셀 내부2×2 불일치0, nearest8× 추가색0이다. 의도한 실패 재현 2분기는 통과본으로 취급하지 않는다. Unity 실시간 AA/합성/cache 검증은 아니다.
- 단색에서도 고정 Q는 4연결11성분/단독6셀, 8연결8성분/단독3셀이다. 4연결은 변 공유, 8연결은 꼭짓점 포함이며 단독은 논리1셀이다. hair mask 자체는 한 성분이다. 따라서 분단 전체를 텍스처의 밝은 띠 탓으로 결론내릴 수 없다.
- g 표본 선택 전후 Q가6셀 바뀌고 단독5→6으로 변했다. 단색 짝 비교에서는 이 표본을 재변경하지 않았다. `SHADE_FRAGMENTATION.json`에 g/threshold/chart/primitive와 native 표본 근거가 있다. 표면/normal/shadow/래스터 중 전부를 원인 확정한 것은 아니다.

## 재현과 보존

완료 기록은 `EXP30\flat-albedo-control\VERIFIED.json`과 `MANIFEST.json`(52파일 SHA256), `REPORT_KO.md`다. API14, PNG/pixel44, Chrome11/Edge11을 실제 완료했다. native64×80와 nearest8× PNG를 직접 검수했다. 검사 통과가 미술 완성이나 시간적 안정성 통과를 뜻하지 않는다.

```powershell
# EXP30에서 실행. Unity 실행/캡처 없이 저장 프레임 검사만 한다.
node flat-albedo-control/verify.cjs
python flat-albedo-control/verify_pixels.py
# 브라우저 표시 회귀가 있을 때만 추가 실행:
node flat-albedo-control/browser-verify.mjs
# PRODUCT에서 문서 수정 검증:
powershell -NoProfile -File docs/ai/validate_ai_docs.ps1
```

새 Unity 캡처가 필요하지 않으면 prepare/rebuild/Play를 반복하지 않는다. 원본 입력 의존성은 `prepare.py`에 명시되어 있고 독립 입력 `INPUT.json`을 보존한다. PNG·로그·큰 생성 JSON과 미확인 개인정보는 저장소에 일괄 추가하지 않는다.

남은 작업은 단색에서도 남는 g/Q 경계 분단의 원인 분리, 연속 프레임의 특징/색 연속성, 승인된 후보의 제품 통합이다. 완료 코드의 고정 보관본은 위 저장소 경로로 연결했다. main의 진행 중 연속 프레임 자료와 눈 cache 진단은 별도 작업이다. 브라우저 입력/스크롤 지연 해결 여부도 이 검사로 판정하지 않는다.

Unity의 기존 미저장 상태와 dirty25, 원본 asset, 제품, 31/34 및 다른 담당 파일을 보존한다. 이 인계를 이유로 Save/Play/Exit/Reimport, cache 삭제, 브라우저/프로세스 종료를 수행하지 않는다. Git dirty는 Editor 미저장 상태의 증거가 아니며 이번 감사에서 live Editor 상태를 새로 검사하지 않았다.

## continuous47 동결 증거 — 제품 미통합

이전 코드 보관 커밋 `1835f10` 옆에 [continuous47 독립 보관본](../../experiments/pixel-pipeline/2026-10-30-continuous47-counts/README_KO.md)을 추가했다. sequence `counts47-087454994917423fa13c5fe72eceb7f4`, frame96–101이며 이전46이나 앞의 프레임95 sourceId와 혼용하지 않는다. 원본 전체225파일 대신 재생에 필요한 ROI/packet의 손실 없는 압축 fixture, 코드·보고·대표 실제 영상만 보관한다. 원본 자산·전체 씬 덤프·진행 중 메모리 추가 진단은 제외했다.

확정된 범위는 1,536 packet×12성분의 GPU 대비 CPU 최대 오차 `5.960464477539063e-08`, frame99→100의 `(223,52)` iris가중치5/budget2 유지와 rank1→2 탈락, 새 선택 `(224,52)`의 실제 앞쪽 머리 최종 가림이다. 오프라인 visibility gate는12개 eye-frame 중 frame100/eye1만 바꾼다. compute 한 파일 후보는 미import·미GPU컴파일·제품 미적용이며 frame101 대각 형태, 회전/blink와 간접 회귀가 남는다. 후보 RGBA 영상이나 전체 수정 성공이 아니다.

동결 원복 기록은 Edit/scene clean/dirty25 유지, 객체·컴포넌트3065개와 tracked12파일의 검사 범위다. 메모리 감사48의 원자료 정정: `Profiler.GetTotalAllocatedMemoryLong()`은46 종료19:55:21UTC의1,628,792,522bytes→47 종료20:16:11UTC의2,001,161,288bytes이며 증가량은372,368,766bytes=355.12MiB다. 과거 “+2GB” 해석은 잘못이고2.00GB는 총값이다. Windows working set과 다르며 잔류 소유자는 미확정이다. [정정 근거](../../experiments/pixel-pipeline/2026-10-30-continuous47-counts/MEMORY_CORRECTION.json)에 원자료 해시를 연결했다. 최신 Unity counter 조회는40초 timeout으로 실행 결과 불명이다. **완전 원복·메모리 정상으로 판정하지 않는다.** 추가 캡처는 중단됐고 이후 메모리 진단은 별도 작업이다. 이 문서 보관 작업에서는 새 Unity 실행이나 live 원복 검사를 하지 않았다.

## 눈 실험50~53 — 2026-10-31 보관

선행49는 `d0ca21f4ac87e82151357253582f9ce079596a2d`로 이미 버전 관리돼 있다. [50~53 독립 보관본](../../experiments/pixel-pipeline/2026-10-31-eye-experiments50-53/README_KO.md)은49 입력을 중복 복사하지 않고 저장소 상대 경로·해시로 연결한다. 원본 asset/전체 source 재추출과 GPU 테스트는 실행하지 않았다. 새 source/shader 후보는 런타임 밖에 보관하며 제품 미적용·GPU 미검증·미술 미채택이다.

50은 cache iris에 의한 source 상안검 재순위 feedback을 분리했지만 흰자의 S0/aperture 문제는 별개다.51은 기존 contour/carrier와 연속 control·native morph의 출처를 보존하며 closed geometry를 승인된 pixel keyform으로 취급하지 않는다.52는 전체 keyform/cache와 충돌을 명시했으나 고정 opaque glyph의 `(222,52)` 충돌을 순서 변경만으로 해결하지 못했다.53은125개 공동 이동 중 **보수적인 any-front 가림 제약 아래** B/C 두 후보를 찾았지만, 눈이1셀 낮아지는 대가가 있다. 부분 가림의 물리적 공동 판정이나 미술 성공을 검증한 것은 아니다. 같은 두 프레임을 함께 쓴 오프라인 후보이며 인과적인 runtime/실제 시간 안정화 결과가 아니다.

53의 빈 원래 눈 위치에 필요한 **clean Base/Backing6표본**이 없다. frame100은 `(223,52)·(225,52)`, frame101은 `(223,52)·(224,52)·(225,52)·(225,53)`이다. 현재 부분 PNG의 magenta는 UNKNOWN이며 주변 피부나 기존 눈 포함 출력으로 추정 보충하지 않는다. 원본 CLI/당시 보고서와 이번 함수·계약·픽셀 재생 검사를 구분한다. Unity/CUA/화면 조작/초기화/앱 종료/원격 push 없이 보관했다. 현재 Editor dirty와 재부팅 후 메모리 상태를 이번 검사로 확인했다고 하지 않는다.

### 50~53의 전제·명칭 정정 — 2026-10-31

- `joint-eye53/run53.py:external`의 `any(front)`는 새 셀에서16표본 중 하나라도 앞 가림이면 전체를 기각하는 **보수적 가정**이다. A의 hair4/16·brow2/16 등의 증거는 부분 가림이며 실제 안검 가시량0의 증거가 아니다. A를 물리적으로 불가능하다고 확정한 이전 설명을 정정한다. 저장100/101 한 셀의 이동 S3 footprint와 S4/S5 깊이·알파 공동 계산은 아래55에서 검증했다.
- 43/49/52의 `floor(delta+.5)`는 공통 **정수 이동**이다. 상대 glyph 위상 불변성과 소수 좌표의 연속 이동은 다르다. 후자를 구현/검증했다고 하지 않는다.
- `joint53.py:enumerate_joint`의 `objective=(movement,curve,relative,box,...)`는 사전식 우선순위다. `pareto` 필드는 정렬 상위8개이며 실제 비지배 Pareto 집합이 아니다. 기존 보관본은 증거 보존을 위해 수정하지 않았고 이 문서가 최신 해석을 소유한다.

## 원본 색→명암 번호→직접 팔레트54 — 2026-10-31

코드: [source-palette54](../../experiments/pixel-pipeline/2026-10-31-source-palette54/README_KO.md). 제품 기본 경로를 바꾸지 않는 Assets 밖 수직 프로토타입이다. 코드·49검사·인계 커밋은 `4ed9a15261560b44fcaf3d7d16c566e27e523de5`이며 시작 기준은 `ef7974e3b912cb55971047321f8e9a27a4327339`이다. Argon.md는 변경하지 않고 별도 Argon용 보고서를 만들지 않았다.

| 스크립트·함수 | 변경 역할 |
|---|---|
| `freeze_samples.py` | 원본 VRM의 material/primitive UV→PNG native texel. 원본 GLB 내 이미지·재질 계수와 외부 이미지 해시 대조 |
| `source-palette.cjs:sourceColours/extractReference` | sRGB8→linear RGB×원래 material factor. 같은 source domain 내 관측 표본 중 weighted squared-OKLab medoid 선택, model/material/image/triangle/UV/texel 출처 유지 |
| `source-palette.cjs:makePalette` | 관측 기준색을 최고 단계 anchor로 보존. 고정 hue의 OKLCH L/C 단계 생성, gamut 밖은 L/h 고정 C 축소. 간격 배율은 **anchor로부터의 L/C 차이**에만 적용 |
| `source-palette.cjs:shadeIndex/resolve/shade` | Float32 입력 `k=count(g≥τ)`→`P[k]` RGB8 직접 반환. 프레임별 min/max 정규화·최종RGB×g·HairAnchor 없음 |
| `adapter.cjs:packet/replayPacket` | source family ordinal과 팔레트 uint4/임계값 Float32 테이블 연결. material ID 고정 매핑 없음 |
| `SourcePalette54.hlsl:SourceShade54/SourceLookup54/SourceRGB8ToLinear54` | 미활성 GPU 연결 후보. point 정수 인덱스 조회와 linear RT용 단일 decode. GPU 미컴파일·제품 미적용 |

계산 계약: 원본 UV는 normalized/top-left, 원본 texel은 sRGB8, material factor는 linear이다. 제공된 source domain의 관측 색을 Lab에서 비교한다. `t=(k/(N−1))^γ`, `Lnative=L0(dL+(1−dL)t)`, `Cnative=C0(dC+(1−dC)t)`, 간격 배율m은 `L=L0+m(Lnative−L0)`, `C=C0+m(Cnative−C0)`에만 쓴다. RGB8 반올림 뒤의 표를 canonical 팔레트로 사용한다. g/τ는 caller가 같은 단위로 주는 명암 스칼라이며 이 프로토타입의 g는 **진단 입력**이지 새 장면 광량 캡처가 아니다.

실제2재질63 native UV 표본과 별도 합성3표본에 같은 코드 적용: 원본 hair material12 기준색 `(66,42,41)`, cloth material10 `(250,238,228)`, 합성 model/material87 `(8,150,172)`. 실제 두 재질은 **한 VRM**이며 모델100% 범용성을 입증하지 않는다. sample 범위 밖의 painted pattern/세부 색군 자동 분류도 구현하지 않았다. fixture용 `N=4/3/5`, dL=.55/dC=.6/γ=1은 공개된 시험 설정이며 최적 미술값이 아니다.

오프라인49검사 통과: source 출처·관측 anchor 일치, 8bit 왕복, material87, source 혼입/미등록 거부, palette 변경시k 보존, τ변경시P 보존, 최종RGB가 직접 P[k]인30출력에서 팔레트 밖0, 동일band g변화 시 RGB 동일, Float32 임계값 이웃·packet 일치, 간격0중복 표시, gamut C 축소. 기존 최종RGB×.72를 주입한 반례는 P 포함 조건에서 실패함을 확인했다. 원본/팔레트는 명암 영역의 공간 형상·고립셀·곡률을 고치지 않으며, 이를 이번 성공으로 보고하지 않는다.

실제 렌더 연결 시점: material/UV source family를 초기화에 공급하고 기존 연속g/향후 보정된k'를 `SourceLookup54`에 연결해야 한다. 불투명 interior의 마지막 출력에서 한 번 decode/encode하고 이후 HairFinal/G·LineTone·추가 조명·AA가 P 밖 색을 만드는지 실제 RT에서 검사해야 한다. 현재 활성 제품의 하드코딩/곱셈은 그대로 남아 있다. 이번에는 Unity/새GPU 실행이 금지되어 import/compile/최종 후단 팔레트 보존/성능/미술은 미검증이다.

원본 dirty `CURRENT_STATE.md`/AGENTS/제품은 보존하고 최신 코드 탐색과 한계는 이 인계 문서에 유지한다.

## 한 셀 부분 가림 전제55 — 2026-10-31

코드: [partial-occlusion55](../../experiments/pixel-pipeline/2026-10-31-partial-occlusion55/README_KO.md). `visibility55.py:joint_visibility/calculate`, 재생 `replay55.py:run`. 고정 입력은 기존47 frame100/101의 source `(222,52)` S3 4×4 alpha/depth/POINT와 destination `(222,51)` S4/S5/S6 표본이다. 동일 source piece를 위1셀 옮기는 반사실 진단이며 새로운3D pose/GPU 렌더가 아니다. palette/RGB나 원래 정수 이동 후보를 재조정하지 않았다.

`a_visible(s)=a_lid(s)·∏_(앞 가림)(1−a_o(s))`, `A=Σ_s a_visible(s)/16`. 앞 가림 여부는 각 source 표본의 depth와 비교한다. 이 곱셈은 alpha 투과량 계산이며 최종RGB×g가 아니다. source의 기존 S0 감쇠를 추가한 경우도 별도 계산했다.

| 입력 | 53 any-front의 전체 기각 | 이동한 native footprint의 가시 면적 | 기존 source S0 감쇠 추가 |
|---|---:|---:|---:|
| frame100 | 0 | 0.0134918771 | 0.0134918771 |
| frame101 | 0 | 0.1066622902 | 0.1066622902 |

두 입력에서 blanket-zero 근거가 반박됐다. 가시량은 **논리 셀 면적 단위**이며1.35%/10.67%가 남는다는 뜻이지, 불투명 픽셀1개를 선택해야 한다는 뜻이 아니다. 또한53의 이미 불투명화한 glyph와 원본4×4 source footprint는 표현이 다르므로 실제 GPU 출력의 동등 비교로 보고하지 않는다. A 자동 채택·전체 눈 형태 해결·색/시간 안정화 미검증. 현재 피부/안검 의미 구분과 clean backing6표본 공백도 남는다.

16검사 통과: 기존53 gate·표본 수 재현, 가시량 상한, native source/S0 경우 분리, 두 고정 진단 재생, 가림없음→원래alpha/전체앞불투명→0의 실제 함수 반례. `cell-fixtures.json`에 두4×4 source/destination raw 표본과 원본49/53 해시를 보관해 Unity 없이 재생한다. 실제 새GPU/캡처/제품/화면조작 없음. 관련 새 커밋은 이 문서·55경로의 Git 이력으로 추적한다.

다음 설계 판단은 부분 가림을 보존한 표현에서 feature shape·공동 소유권을 결정하는 것이다. 단순 `any` 완화epsilon·새 가중치·추가 정수 이동 탐색으로 대체하지 않는다. 전체 눈/Closed 상태를 원본에 없는 shape로 채우지 않는다.
