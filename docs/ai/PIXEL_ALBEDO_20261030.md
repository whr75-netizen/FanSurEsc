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
| `SourcePalette54.hlsl:SourceShade54/SourceLookup54/SourceRGB8ToLinear54` | point 정수 인덱스 조회와 linear RT용 단일 decode. 54 당시 GPU 미컴파일, 이후 아래57에서 격리 GPU/RT 검증. 제품 미적용 |

계산 계약: 원본 UV는 normalized/top-left, 원본 texel은 sRGB8, material factor는 linear이다. 제공된 source domain의 관측 색을 Lab에서 비교한다. `t=(k/(N−1))^γ`, `Lnative=L0(dL+(1−dL)t)`, `Cnative=C0(dC+(1−dC)t)`, 간격 배율m은 `L=L0+m(Lnative−L0)`, `C=C0+m(Cnative−C0)`에만 쓴다. RGB8 반올림 뒤의 표를 canonical 팔레트로 사용한다. g/τ는 caller가 같은 단위로 주는 명암 스칼라이며 이 프로토타입의 g는 **진단 입력**이지 새 장면 광량 캡처가 아니다.

실제2재질63 native UV 표본과 별도 합성3표본에 같은 코드 적용: 원본 hair material12 기준색 `(66,42,41)`, cloth material10 `(250,238,228)`, 합성 model/material87 `(8,150,172)`. 실제 두 재질은 **한 VRM**이며 모델100% 범용성을 입증하지 않는다. sample 범위 밖의 painted pattern/세부 색군 자동 분류도 구현하지 않았다. fixture용 `N=4/3/5`, dL=.55/dC=.6/γ=1은 공개된 시험 설정이며 최적 미술값이 아니다.

오프라인49검사 통과: source 출처·관측 anchor 일치, 8bit 왕복, material87, source 혼입/미등록 거부, palette 변경시k 보존, τ변경시P 보존, 최종RGB가 직접 P[k]인30출력에서 팔레트 밖0, 동일band g변화 시 RGB 동일, Float32 임계값 이웃·packet 일치, 간격0중복 표시, gamut C 축소. 기존 최종RGB×.72를 주입한 반례는 P 포함 조건에서 실패함을 확인했다. 원본/팔레트는 명암 영역의 공간 형상·고립셀·곡률을 고치지 않으며, 이를 이번 성공으로 보고하지 않는다.

실제 렌더 연결 시점: material/UV source family를 초기화에 공급하고 기존 연속g/향후 보정된k'를 `SourceLookup54`에 연결해야 한다. 불투명 interior의 마지막 출력에서 한 번 decode/encode하고 이후 HairFinal/G·LineTone·추가 조명·AA가 P 밖 색을 만드는지 실제 RT에서 검사해야 한다. 현재 활성 제품의 하드코딩/곱셈은 그대로 남아 있다. 54 작성 당시에는 Unity/새GPU 실행이 금지됐으며, 이후 승인된57의 격리 검증과 실제 제품 연결/성능/미술의 미검증 범위를 구분한다.

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

## 격리 GPU/최종 sRGB 조회57 — 2026-10-31

코드·결과: [gpu-probe57](../../experiments/pixel-pipeline/2026-10-31-gpu-probe57/README_KO.md). 54의 검증된 PACKET 3family·12색·9임계값·30진단표본을 그대로 사용했다. `SourcePaletteGpuProbe57.cs:Execute/Violations`는 **Assets 밖**의 기존 `Unity_RunCommand` 실행기이고, `Assets/Editor/SourcePalette54Probe/SourcePaletteProbe57.compute:Probe57`와 `SourcePaletteOffscreen57.shader:Frag57`가 같은 `SourceShade54→SourceLookup54`를 사용한다. HLSL은54와 바이트 동일하다. C# import/domain reload를 유발하지 않고 셰이더3개만 한정 import했다. 제품·씬·재질·RendererFeature·Play·SaveAssets 변경은 없다.

2026-10-31 08:12:41 UTC, Unity6000.5.9f1/Direct3D11/Linear에서 dispatch1회·offscreen draw1회. compute uint4 30/30, `R8G8B8A8_SRGB` 30×1 RT 30/30이 원래 CPU RGB8과 정확 일치, 팔레트 밖0이다. fragment는 정수 P[k]를 한 번 sRGB decode하고 RT가 한 번 encode한다. PNG 원본/nearest16×와 CPU/GPU/RT 비교를 직접 열어 확인했다. 실제 머리/눈·광원·후단 외곽선 렌더가 아니라 **동결 진단 입력의 GPU 조회/출력 인코딩** 검증이다.

기존 dirty24의 native JSON 3,438,997bytes, entity ID, 관련 디스크49파일 해시, GameMap1 clean/37root identity, build scene 목록, Edit 상태, domain1이 전후 동일했다. 소유 ComputeBuffer5개·NativeArray2개·Material/Compute clone/RT/CommandBuffer만 해제했고 shader compiler message0·Console 신규 오류/경고0이다. 실행 직후 기존RT30개 identity가 같았지만, 후속 읽기 시 RT수30을 유지한 채2개 identity가 교체됐다. 그 소유자/원인은 미확정이며 공유RT를 임의 정리하지 않았다.

메모리 완전 원복을 주장하지 않는다. probe 전후 `Profiler.GetTotalAllocatedMemoryLong` +63,908,825bytes(+60.95MiB), `GetTotalReservedMemoryLong` −16MiB, `GetMonoUsedSizeLong` +87.84MiB다. 별도 전후 읽기 스냅샷 범위에서는 allocated +213,449,290bytes(+203.56MiB), reserved +141.28MiB, mono +129.25MiB다. 물리 working set이 아니며 동적 컴파일/JSON 직렬화/import cache/미수집 managed 할당 중 잔류 소유자는 확정하지 않았다. GC/Unload/추가 렌더로 숨기거나 장기 누적 없음으로 확대하지 않는다.

실행 전 C# 타입 오류와 명령기의 불허 `System.Runtime.InteropServices` namespace 검사가 있었으며 그 단계 GPU 실행은0이었다. 도구가 지시한 불필요 namespace/속성 제거 후 **동일 공식 실행기**의 표준 C#으로 컴파일·실행됐다. namespace 정책/보안설정/실행경로를 변경하지 않았다. 성공한 GPU 실행은1회뿐이며 이전 실패는 성공 수에 넣지 않는다.

다음 제품 연결에는54의 `sourceColours/extractReference/makePalette` 초기화 C# 이식, 실제 material/UV→family 공급, 모든 interior 셀의 P[k'] 기록이 필요하다. `RestoreStyle335.ApplyShadeBoundary`의 old==q 조기 반환에만 붙이면 미변경 셀은 기존색으로 남는다. 실제 family ID 버퍼와 후단 G/LineTone/alpha 경계를 설계·검증하기 전 제품 활성화하지 않는다. 눈 clean backing6표본과 부분 가림/전체 keyform 판정은 이번 시험에서 확보하지 않았다. 관련 커밋은 이 절·57 경로의 Git 이력으로 추적한다.

## 원본 공급·C# 이식·초기/최종 색 후보58 — 2026-10-31

[58 코드·증거](../../experiments/pixel-pipeline/2026-10-31-source-palette58/README_KO.md). 시작 commit `1879cc65257b0590e1daef0f277c5a10fc09ff46`; 이번 commit은 이 절과58경로의 Git 이력에서 찾는다. 제품 미적용이며 C#은 Assets 밖에서 기존 명령기로 실행했다.

| 스크립트·함수 | 변경과 실제 검증 범위 |
|---|---|
| `SourcePalette58.cs:SourceColours/ExtractReference/MakePalette/ShadeIndex/Resolve` |54 JS의 source 출처/alpha 가중 medoid·OKLCH 램프·Float32 Q→P 직접 출력 이식 |
| `OriginalMaterialUv58.cs:Read/ReadAccessor/FamilyKey/ResolveFamily` | 실제 원본 GLB material/texture/factor/UV/PNG를 읽어 modelSHA+mesh+primitive+material family 공급. 이름/역할/삼각형 구간 분류 없음 |
| `ReadSource58.cs:Execute`, `SourceJson58.cs` | 원본18,495,680bytes SHA 검사 후 두 명시 domain의63 UV 표본 새 추출. 한 번에 원본 이미지 최대16MiB 생성/해제 |
| `State58.cs:Read/Changes` | dirty JSON을 객체당 한 번 해시하고 큰 원문을 snapshot에 남기지 않음. `Json58.cs`는 명령기 참조 집합용 기본 C# JSON 경계 |
| `SurfaceLayerOutput58.hlsl:SurfaceLayerOutput335`, `RestoreStyle58.compute:ApplyShadeBoundary` | 제품 함수의 독립 clone. 초기 P[Q(g)], 최종 bound opaque 분기는 role/old==q 검사 **앞에서** P[k′] 기록. 기존 제품 원문/기본값 변경 없음 |
| `GpuProbe58.cs:Execute/ReadFloat/ReadByte`, `Recheck58.cs:Execute` | 실제63 source 표본에서 C#이 계산한 팔레트로 offscreen 시험. 저장값 CPU 재검사는 GPU 재실행 없음 |

원본 PNG63/63, 실제 두 재질의 대표색·출처·전체 팔레트 RGB가 JS와 정확 일치했다. 기준색 `(66,42,41)` 및 `(250,238,228)`, 좌표 최대오차2.220446049250313e-16. 간격배율 .5 변경시 Q 고정, 임계값 변경시 P 고정이며 C# 두 variant도 JS와 같았다. 이 값은 fixture 설정/유한표본 결과이고 모델100% 범용성·자동 의미분할/미술 최적값이 아니다.

GPU draw2/dispatch1회:64표본 중 opaque62(동일Q52·변경Q10), partial alpha 원본1, 미등록sentinel1. 초기 linear 최대오차2.423339741097763e-7, 최종 sRGB64/64·alpha/class/factor64/64 일치, bound opaque 팔레트 밖0. **최종 join 반례 검사에서만** 동일Q52셀 RGB를 magenta로 오염시켜 조기반환으로 거짓 통과하지 못하게 했고 모두 LUT로 교체됐다. source/UV/g/alpha는 유지했다. 이 결과를 실제 연속 캐릭터 프레임이나 중간 오염 없는 전체 렌더 통합이라고 하지 않는다.

원래 C# GPU report는 `classMismatches=63/gpuPass=false`였다. 비교식 `.4f+i*.001f`의 미저장 중간 정밀도가 업로드 Float32와 달랐다. 원본 report/제출 코드를 유지했고, 저장값의 C# CPU 재검사에서 원래식63불일치·업로드된 Float32 성분0불일치를 함께 확인했다. 현재 검사기는 실제 업로드 Color 배열을 비교하도록 교정, GPU 재실행 없음. `VERIFIED58.json`과 `CSHARP_RECHECK58.json`이 정정 근거다. 단순 허용오차 완화로 데이터 변경을 숨기지 않았다.

57 수명 감사: submitted 코드의 static 큰 배열/이벤트/비동기 callback 잔류는 없고 owned 자원 해제 경로가 있었다. 다만 DirtyLines의 객체당 JSON2회와 전체 문자열/UTF8/snapshot 반복 할당은 확인돼58에서 1회/객체+작은 해시 요약으로 줄였다. 57 RT2개 identity 교체 소유자/Unity 잔류 할당 소유자는 미확정이다.58 source 단계 allocated −33.248MiB/reserved +16.008MiB/mono −39.059MiB, GPU 단계 allocated −242.670MiB/reserved −173.273MiB/mono −20.977MiB. Unity 내부 counter의 단기 관측이며 물리RAM/누수 해결 증거가 아니다.

현재 dirty24 native내용/entity ID·관련49파일·씬 clean/37root·Edit/domain 보존, 소유 자원 회수와 신규 Console 오류/경고0 확인. 원본 제품 두 함수와 기존 변경은 보존했다. 부분alpha1셀은 opaque LUT를 강제하지 않았다. source의 PNG identity transform/UV0만 지원하며 비identity 변환·다른 UV·sparse는 미지원이다. family domain 선택은 CONFIG58의 명시 primitive이고 원본 UV는 색 표본을 고르지만 primitive 내부 painted 특징을 자동 분할하지 않는다. **현재 renderer의 실제 가시 셀→원본 primitive/family provenance 버퍼 연결은 아직 없고**, 기존 Full319View335의 역할 분류도 그대로다. 다음 연결은 이 버퍼와 후단 alpha/outline/AA 보존이며 새 머리/눈 렌더 검증·제품 활성화는 별도다.


## Renderer 실제 구성 연결59 — Play 직전 대기

[59 source 연결·정확한 실행 경계](../../experiments/pixel-pipeline/2026-10-31-renderer-family59/README_KO.md). 현재 GameMap1 Edit에는 live NativePlayer395가 0개다. GameplayShellBootstrap.Awake가 실제 shellPrefab(PersistentGameplayShell)을 생성하고 nested ValidatedPresentation399를 초기화하는 정상 Play 진입이 필요하다. prefab을 활성 Instantiate하는 우회나 초기화는 하지 않았다.

`ReadRenderer59.cs`가 실제 bootstrap의 직렬화 참조를 따라 3개 source mesh/15개 material slot을 읽고 UV/indices를 보존했다. `map_sources59.py`는 전체 UV·indices·material factor를 실제 texture가 참조하는 원본 VRM과 대조해 15개 모두 유일하게 연결했다. 수동 두 primitive/재질명 분류는 없다. `RendererFamily59.cs:constructor/TryReadSourcePoint/PackDrawDescriptors`는 실제 renderer 배열에서 해시를 재검증하고 source texture만 읽으며, 누락/범위 밖/미지원 입력에는 false/reason을 반환한다. `CheckConfiguredSources59.cs`에서 15개 draw의 원본 RGBA 120/120, descriptor uint4 240바이트를 확인했다. 이는 구성·원본 point 검사이며 가시 셀 RT/실제 프레임 성공이 아니다.

현재 Play 옵션은 enabled=false/None으로 domain reload가 발생하므로, 59의 domain reload 회피 및 모드 변경 직전 중지 조건에 따라 Play는 미실행이다. 필요한 다음 범위는 EditorSettings.asset의 옵션을 일시적으로 DisableDomainReload로 변경 → GameMap1 정상 Play 1회 → ready 후 pause에서 원본/복제 후보 동일 프레임 비교 → 정상 종료 → 옵션/pipeline/씬·dirty 내용/파일 해시 원복·검증이다. runInputTest=0 유지, Editor.Step/원본 재질·RendererFeature 편집/SaveAssets/CUA/앱 종료/push 없음. 설정 변경도 아직 실행하지 않았다.

현재 source 검사 전후 dirty 24개 내용/identity·씬 clean/37root·Edit/domain 변경 0. source helper 구간 allocated +412,592bytes/reserved 0/mono +45,936,640bytes는 내부 counter이며 누수 판정이 아니다. 실제 visible-cell provenance, 헤어 palette/g 연결, 전체 PNG, interior/경계별 후단 palette 밖 색 수는 미측정(null)이다. 이 범위를 준비 완료/미술 완료로 확대하지 않는다. 관련 commit은 이 절과59 경로의 Git 이력에서 추적한다.


59 Play 경계 추가 점검: 현재 dirty24는 Shader23+EditorBuildSettings1이다. 사전 SaveAssets는 필요 조건이 아니며 실행하지 않는다. SubsystemRegistration에 shell singleton·GameStartRequest·직접 Play 임시 저장 경로의 초기화가 있다. renderer callback은 OnDisable 해제 경로가 있지만 다른 static/비직렬화 상태까지 자동 복원되지는 않는다. 따라서 DisableDomainReload 설정만으로 무손실을 보장하지 않고 pipeline/시간/Shader global·dirty내용 전후 검사가 필요하다. 현재 renderer는 Application.isPlaying/Camera.main/Player/CharacterController/world render serial을 요구하며 같은 흐름을 지원하는 PreviewScene 경로가 없다. scene reload를 유지한 정상 Play 1회가 최소안이고, 설정 변경·Play·새 GPU 실행은 아직 하지 않았다. Shader native 상태 전체를 직렬화 해시가 백업한다고 주장하지 않는다.


## 실제 캐릭터 source→팔레트 GPU 연결60 — 임시 검증, 미채택

[전체·헤어 비교와 상태](../../experiments/pixel-pipeline/2026-10-31-renderer-compare60/INDEX.html), [코드/한계](../../experiments/pixel-pipeline/2026-10-31-renderer-compare60/README_KO.md).

`Compare60.cs:Capture`는 실제3mesh/15material을 `RendererFamily59` 전체UV/index hash로 다시 연결하고, 실제각 hair primitive UV의128원본표본에서 `SourcePalette58.ExtractReference/MakePalette`를 공급한다. 원본 source별색/실제surfaceShadeSteps2를 사용하며 재질별대표색이라는 한계가 있다. 초기 `LegacySignals60.shader:Eye333Fragment`, 독립 `Independent60.shader:Eye333Fragment`, 최종 `RestoreStyle60.compute:ApplyShadeBoundary`에 clone으로 직접 P를 연결했다. 후자는 old==q도 LUT 통과한다. 원본 shader/재질/RendererFeature 및 제품 default는 미변경이다. 정확한 실행본은 `RUN_compare3.cs.txt`, 단일Play observer는 `Tick/BeginExit/Finish`다.

frame94/sourceId renderer60-20261031T092325108Z: 실제헤어373셀의 source/triangle/UV확정373, 미확정0, 초기RGB8 LUT불일치0. 내부263셀/최종1052픽셀 P일치, 경계110중52셀/208픽셀은 기존 OwnerLines333.compute:35의 선형색×.55로 P이탈(오차최대5.07e-9). 헤어외RGBA/owner/depth변화0, pose/geometry동일. preparedUV.z의9개정수tag를 Q로 오독하지 않도록 source class.x==mask.x로 수치검사했다. 실제 PNG는 후보의 밝은갈색/무늬축소를 보여주며 미술개선으로 채택하지 않았다. 새 backing6표본/눈/회전/blink/연속검증은 미수행이다.

정상Play1회 종료 후 Edit/GameMap1 clean37root/domain1/liveNative0, options false/None·pipeline·시간복원. 원래24와 Play직전25dirty내용/ID·기존파일 hash변화0. 최종 dirty29: Play전 CommonSurface shader1(원인미확정), Play후 EditorSettings/GraphicsSettings/TimeManager/FaceSourceOwner202 추가. 저장·discard·dirty강제해제 없음. 얼굴 vertex584640/index85464바이트는 saved disk와 동일하나 전체prePlay native비교는 아님. Shader global63개 setter복원했지만 원래값 export/getter비교·bufferbinding백업은 누락했다. RT30→30, allocated+353.31MiB/reserved+358.41MiB/mono-320.67MiB는 내부counter이며 retained allocation원인미확정이다. 신규Console Error0/변경없는Eye경로cold Warning33, 후보ShaderUtil상속Warning2 기록. Console삭제/GC/새Play를 하지 않았다. [복원 감사](../../experiments/pixel-pipeline/2026-10-31-renderer-compare60/RESTORE_AUDIT60.json)의 subset/content검사와 전체dirty목록동일성검사를 구분한다.

실행shader4개+meta만 Assets/Editor/RendererCompare60Probe에 격리보관하고 C#은 Assets밖/in-memory로 실행했다. 저장 buffer ZIP17개를 오프라인 재분석해 수치·PNG byte동일을 확인했다. 이 절과 해당60경로/격리shader만 이번 로컬commit에 포함하며 기존 사용자변경은 제외한다.


## 복원 읽기 후속61 — Play/렌더/추정 복원 0회

60폴더의 `RestoreAudit61.cs:Execute`/`BindposeRead61.cs:Execute`와 `followup61.py`, [FOLLOWUP61.json](../../experiments/pixel-pipeline/2026-10-31-renderer-compare60/FOLLOWUP61.json), [색 성분 PNG](../../experiments/pixel-pipeline/2026-10-31-renderer-compare60/COLOUR_COMPONENTS61.png). Shader native 전체 JSON을 반복하지 않고 현재63getter/작은설정3개/메쉬read-only view만 읽었다. 60의 원래63값은 private인스턴스딕셔너리에만 있었고 지속export/회수handle을 만들지 않아 비교가능 원래값0개, 불일치수null이다. SDK보유/GC여부는 미확정이며 private reflection/추정setter/bufferbinding변경을 하지 않았다. 전체global 동등성증명은 불가다.

Edit/scene clean37root/domain1/liveNative0, 옵션·pipeline·시간 API는prePlay백업과 동일. 설정3개 nativehash는60종료와 동일/원래디스크변화0. 얼굴vertex584640/index85464바이트와 bindpose1456 Float32값,57morph의이름/프레임수/weight는60종료와 동일; bindpose는disk와도숫자차이0. 사전전체native/morph delta백업은없어전체형태동일성확대금지. 설정3dirty는관련APIsetter/원복setter에연결되며 얼굴dirty의정확API원인은미확정이다. dirty30은60종료29+기존DeskLivePixelProbe.shader1(원인미확정/diskdiff0)이고저장/해제하지않았다. 원래24ID/dirty와기존파일을보존했다. API enabled=false와native/disk enabled1/options0표현차이는추정수정하지않았다.

후보재질0/computeclone0/RT30. 자체코드static대형배열없음, GPU자원해제및큰배열의동기local수명확인. 제품고정색배열약4MiB/tag317080bytes/bool2×130560은존재하지만+353.31MiB소유자로확정불가, SDKmanaged root미확인. 어떤자원도강제정리/GC하지않았다. 같은373셀은원색189→재질대표3→Q팔레트6→선색후9색이며L중앙값.256→.405→.365→.339(제품.141). 무늬감소·밝기편향은per-material/offscreen포함32표본medoid선정에서이미발생하고, 기존G=(.0853,.1188,.2491)감광/청색편향우회도색차에기여한다. LineTone.55는52셀을어둡게만하므로내부갈색/밝기의원인이아니다. 새후보/파라미터변경/제품변경없이기존저장자료에서분해했다.

## 재질 내부 원본 색 영역62 — 오프라인 구현, 미채택

[62 전체/머리/이전 반례 비교](../../experiments/pixel-pipeline/2026-10-31-source-regions62/INDEX.html), [계약·실패·재생 방법](../../experiments/pixel-pipeline/2026-10-31-source-regions62/README_KO.md). 기준 commit `c5be02ddd64ad32511c421b8698a1bfdbadc5675`; 이번 commit은 이 절과62 경로의 Git 이력으로 추적한다. Unity 조회·Play·렌더·제품 변경·GC·SaveAssets·화면 조작 없이 저장60 frame94/sourceId와 원본 VRM만 사용했다.

| 스크립트·함수 | 변경·검증 범위 |
|---|---|
| `region62.py:build_regions/cc4` | 원본 PNG의 OKLab 색 범위 → UV 연결 영역. 재질 ID·색 영역 ID·topology 구조·실제 occlusion owner를 분리. 원본 대비 표지로만 추가 분리하며 면적 삭제 없음 |
| `region62.py:palette/structure_components` | 실제 native texel anchor → 유한 P 직접 조회. 동일 색 범위의 다른 영역은 참조만 공유. 원본 기하 연결은 별도 ID이며 미술 묶음/정렬 owner로 승격하지 않음 |
| `run62.py:resolve` | 실제373셀의 primitive/material/UV→source region→P[저장Q] 연결. 원래52셀 LineTone .55는 그대로 별도 적용. g를 RGB에 곱하거나 중앙값 보정 배율을 쓰지 않음 |
| `test_math62.py`, `test_regions62.py` | 기존54와518색·RGB8 왕복, 분리된 두 무늬/같은 색 다른 구조/작은 강조 셀 반례. 현재373셀의 직접 P/간격·Q 독립성과 옛 source-known358셀의106/184 singleton·113 추가 경계·region40 대비 소실/0변경을 재현 |
| `audit_source62.py` | original imageSHA 검증·native3표본 L 구간의 affine 적합 가능성 진단. 365/373 양립은 의미 특징/제거 대상의 판정이 아니며 라벨 변경0 |

같은373셀: 원본189색 → 가시 UV 영역66/구조45/instance196 → anchor45색 → P62색 → 동일 선 처리74색. 최종 RGB 연결 영역189/단독144, L 중앙값 .251989(원본 .256064,60 .339208). 실제 전체 PNG의 머리 밖 RGBA/전체 alpha 변경0. 원본 무늬는 다시 보이지만 하단 잔무늬가 남아 미술 성공으로 채택하지 않았다. 전체 UV cache2146개 영역은 실제 미술 특징2146개라는 뜻이 아니다. 원본 색 범위 폭·명암 간격은 기존 측정 ΔL .043678819190537344를 쓴 진단 설정이며 최적값이 아니다.

옛 프레임은 다른 sourceId이며358 source-known만 같은 범위로 비교했다. v3 단독106/추가 경계113, protected64 단독184/추가207,62 단독136/추가140이다. 정보 없는10셀은 기존 PNG로 유지했다. 보호7쌍×4Q의 색 구분·방향은 유지하나 기존 filtered 원본 최소 대비는4쌍만 모든Q 통과(id3·5·8 실패). equal-Q id4도 최소 대비는 Q0·2만 통과. native point/filtered 원본 차이와 RGB8 오차를 밝기/대비 증폭으로 숨기지 않았다. 모든 원본 gradient를 의미 경계로 고정하거나 source RGB189개를 그대로 family로 복제하지 않았지만, 그려진 긴 무늬와 부드러운 texture gradient를 구별하는 구조는 여전히 미완이다.

최초 Python OKLab 행렬 계수 두 개 오기로 자홍색이 난 실패는 `invalid-math-*`로 보존하고, 기존54 함수518색 최대오차6.80e-16/왕복0불일치를 확인한 수정 결과만 후속 검사했다. 순회·연결 검사와 지표 감소를 미감 증명으로 확대하지 않는다. 실제 GPU·필터 footprint·회전/가림·시간 검증은 하지 않았다.

global63 백업 추가 코드 검토:60 `CommandScript` private 딕셔너리와 SDK private `m_ActionInstance` 보유 가능성은 있으나 반환된 핸들이 없고 `CommandScriptPostBox.Pull`은 키를 제거한다. 공개 실행 결과는 ID/로그만 반환한다. 기존 참조에서 안전한 생존 객체 접근 경로를 찾지 못했다. GC 여부를 단정하지 않으며 추가 probe/반사/추정 setter 없이 원래값 백업 부재·동등성 미증명 상태를 유지한다. 마지막 실제 Unity 상태는61이며62에서 현재 상태를 재확인했다고 주장하지 않는다.

## 최초 분절·누락 단계63 — 구조/측정 구현, 공간 보정 미완

[63 단계·원인 mask](../../experiments/pixel-pipeline/2026-10-31-region-stages63/INDEX.html), [구현/입력 공백](../../experiments/pixel-pipeline/2026-10-31-region-stages63/README_KO.md), [함수 위치 색인](../../experiments/pixel-pipeline/2026-10-31-region-stages63/FUNCTION_INDEX63.json). 기준 commit `e0983eb69037cbb2111be5901b263c7a7c789be4`; 새 commit은63 경로/이 절의 이력으로 추적한다. **62 미채택 유지, 현재373셀 RGB 변경0, 실제 공간 보정 미구현**이다. Unity/제품/31/34/팔레트/임계값/GC/SaveAssets 변경 없이 저장 자료만 사용했다.

실제62 호출은 `run62 → build_regions(Lab 절단→cc4→표지 분리→medoid/참조 공유) → structure_components → resolve(material/UV→region→P[저장Q]) → 기존 .55`다. 원본 특징 경계 추출과 색 하위영역의 공유 경계 보정은 없다. 최초 인공 분절은 `build_regions`의 colour box 절단이다. Q가 독립/병렬로 계산된 것이 결함은 아니며, 빠진 source 경계/색 영역 단계를 Q 후처리나 팔레트 공유로 대체한 것이 문제다. 기존에 없던 hard-feature gate를 제거했다고 주장하지 않는다. seed 포함 영역 전체를 certified feature라고 부른 메타데이터는 근거가 부족했다.

| 스크립트·함수 | 실제 변경/대조 |
|---|---|
| `audit63.py:components`, 본문 | current66/legacy140를 source별로 분리 분류. topology·가림·UV 재배치·색 범위 cut 구분 |
| `shared_boundary63.py:separate_layers` | 확정된 머리 소속/미추출 하위 feature/colour range/structure/owner/Q 분리 adapter. family 공유를 공간 보정으로 처리하지 않음 |
| `shared_boundary63.py:trace/path_metrics/reference_metrics` |44의 공유 경계 원리를 일반 label에 적용. 고정 source arclength 접선/위치 이탈과 별도 역행량 측정. 제곱 접선 비용만으로 놓치는 역행 반례 추가 |
| `validate63.py` |373셀 460색 경계/357경로와49 Q경계/2경로, T접합·얇은 띠 양쪽·구멍, 실제44의11영역/6singleton 반례 및 무제약12/7 실패 재검사 |

current UV colour-range66개는 화면186조각이다. 배타 분류37개는 여러 source 구조에 걸침,28개는 가시 조각 하나,1개는 한 구조 내 화면 분리 원인 미확정이다. 중복 진단인 same-structure split16개와 앞 수를 합하지 않는다. 원본 RGB/Q가 같은 인접18쌍은 서로 다른 재질의 range/anchor 때문에 서로 다른 색이 나온다(.55 전). 예(223,226)–(224,226): source(44,22,23)/Q0, output(37,16,17)/(31,12,13). 이를 고치려 source structure를 합치거나 최근접색을 셀별 재선택하지 않았다.

옛140 신규경계는 matched geometry 기준 가림/틈72, 소유권 전환/겹침15, 같은 전면의 색 범위 분절50, 색UV 재배치 대응 미확인3으로 배타 분류했다. index492·523 두 셀의 colour UV와 selected geometry UV가 다르며 `geometryUV` 필드가 별도로 존재하므로 데이터 손상이라고 단정하지 않는다. 기하 평가 자료는 source 표본과 최대(.001838,.001768)논리픽셀/depth5.52e-7m 대응으로 맞춘 다른 시각의 자료다. 동일 GPU capture 프레임이라고 확대하지 않는다. 현 frame94에 이 geometry를 대입하지 않았다.

기존 R3 원본 indexed 소스는 옛 경로에서 확보하지 못해32 색인과 현재31 후속 함수의 원문/hash를 구분해 보관했다. 현재 `regionCorrect31`은 Q 뒤의 perimeter E/2×2 corner C 목적이고 원본 source 곡선 목적이 없다. R5 동시 적용 수정은 이미 있어 과거 in-place 오류를 현재 결함으로 재주장하지 않는다. 44는 색 특징 경계가 아니라 Q 경계다. 저장 path4 접선 .203877926→.171808151/위치 이탈 .799877799→.692588333을 재계산했지만 기존4셀 수정과11영역/6singleton은 그대로이며 전체 미감 성공이 아니다.

현재 실질 보정에 필요한 것은 같은 sourceId의 evaluated 위치(8435정점이면 약101,220bytes)·view/projection/grid와 source sample screen 위치, native 원본 색 경계의 투영 대응이다. 색/gradient의 source 특징 계층 추출 구현도 미완이다. 이는 자동 추출이 불가능하거나 수동 semantic 정답이 반드시 필요하다는 뜻이 아니다. 버퍼 공백과 구현 공백을 구분했으며 이미 양자화한62의 계단을 원곡선으로 fit하지 않았다. 현63은 분류·분리 표현·측정까지이고 실제 공유 곡선 재배치/RGB 개선은 끝나지 않았다. 현재 실행 금지 범위를 넘어 새 캡처하지 않았다.

## 원본 UV 기울기/경계64 — 오프라인 코드·검사, 캡처 준비 미완

[64 source·반례](../../experiments/pixel-pipeline/2026-10-31-uv-features64/INDEX.html), [수식/한계](../../experiments/pixel-pipeline/2026-10-31-uv-features64/README_KO.md), [함수 색인](../../experiments/pixel-pipeline/2026-10-31-uv-features64/FUNCTION_INDEX64.json). 기준 commit `fd1639188dcd99ffc3f332acbab3c73bc986e00a`; 새 commit은64 경로/이 절의 이력으로 추적한다. Unity 조회·Play·렌더·새캡처·제품·31/34 변경0. Python은 실행했고 C# helper는 미컴파일·미실행이다. 현재 RGB/팔레트를 개선했다고 주장하지 않는다.

| 스크립트·함수 | 변경 전제/실제 검사 |
|---|---|
| `uv_features64.py:colour_intervals/intercept_weights/jump_interval/axis_evidence` | Lab 절대 구간 대신 원본 양쪽 affine 기울기를 제거한 jump 구간. native2/4/8 모든 스케일 검출·모델 적합성·구간 일관성 검사 |
| `thin_ridges/barrier_components/edge_components/extract/source_key` | 얇은 후보·닫힌 면·열린 contour/DAG 분리. 면적 삭제·gap 강제 연결 없음. source/UV support/규칙 버전 캐시, g/Q/material/화면위치 키 아님 |
| `palette_invariant/test_uv64.py/run_source64.py` | 합성9사례·3200 encoding 구간 표본·원본PNG4장SHA/373UV 대응. 같은 sourceRGB/Q의 기존18인접쌍 실패를 그대로 기록, 새189family/P 생성 안 함 |
| `capture_contract64.py:validate/require`, `test_capture64.py` | source/view/frame/serial·투영·실제 tap·색공간/g정의·mode·clean backing·global 복원·readback 예산 계약. 합성1/거부8검사 통과 |
| `CpuSourceCapture64.cs:WriteCpuGeometry/WriteCamera/WriteOwnedPlane` | 기존 evaluated mesh/indices/UV/material/texture·bonepose 읽기, raw/effective CPU/GPU 투영 분리, 직접 소유ROI≤1MiB를 순차 streaming/Dispose. entry point·render/global setter 없음 |
| `GlobalJournal64.cs:Snapshot/VerifyExternal/RequireRecoverable/RestoreMarked/VerifyMarked` | 외부 binary+SHA+전체 역읽기 검증+public회수핸들 준비. LegacyInt float 보존, getter bit/identity 검증. buffer setter·reflection 없음 |

합성 일정/선형/이차 gradient는 persistent0, step은 원경계65개/영역2, 분리된 같은색 무늬는 contour2/영역3,1/3texel선과 작은점은 fine에 보존했다. 매끄러운 좁은 봉우리는 fine/ridge 미확정으로 남겼다. 최초 ghost 경계/봉우리 오분류와 “구간 교집합만으로 전 스케일 지지” 오판을 `ABLATION64.json`에 보존했다. 후자는 원본12 X prefix1053→2092→11956이 반례였고, 모든 스케일 검출 조건 후1053→31→6이다. threshold 수치 튜닝이 아니라 논리 조건 수정이며 규칙 `uv-affine-jump64.2`로 캐시를 갱신했다.

원본 image15/18/20/22 bytes를 그대로 보관했고 RGB변경0, 기존373UV 모두 원본점/계층/Q 대응을 재검사했다. native coarse/fine면 수2/458·2/310·1/1·1/1은 palette나 의미 특징 수가 아니다. 열린 선을 별도로 보존하며 실제 흐린 무늬는 contour가 많이 끊어져 **전체 특징 마스크·공유 곡선 조립은 미완**이다. 임의 면적 삭제/연결로 수를 줄이지 않았다. 1x source/evidence PNG를 직접 검수했으며 새 캐릭터 렌더는 없다. 기존31/32·R3 근거/한계는63 인계를 유지한다.

다음 실제 캡처는 sourceId/viewId/frame/renderSerial 하나에 평가 geometry와 raw/effective CPU/GPU P·nativeShift/grid/subsample, sourceRGBA와g정의/owner/depth/coverage, mode/state, 실제 backing을 묶어야 한다. `FullFeature367.Eyes` part10은 ph.backing의 RGBA/meta/UV를 실제로 그리지만 EyeCompose는 meta만 참조한다. layer10 RGBA는 styled pre-eye 값으로 unlit source와 구분하고 옛6목적지는 새feature좌표로 대응시킨다. 주변 피부 추정으로 채우지 않는다.

**새 Play 승인과 별개의 기술적 실행 차단:** 정상 `FullFeature367.Probe:11`이 `ClothRegion524.BeginProbe:134`를 호출해 `_BodyScope551` global buffer를 설정한다. private owner의 `ScopeBuffer551:38`은 null이면 생성하며 public Shader global buffer getter가 없다. 정확한 원래 binding·수명 보존 또는 local-binding 경로 없이는 기존 정상Play를 재사용하지 않는다. C# journal이 이를 해결했다고 주장하지 않으며64에서는 실행0이다. 과거60 원래global 백업도 복구한 것이 아니다. 부모에게 이 정확한 범위를 보고하고 새 승인 전 Unity 접근 금지를 유지했다.

## BodyScope551 소유권65 — 오프라인 패치, Assets 미적용

[65 패치·함수·검증 한계](../../experiments/pixel-pipeline/2026-10-31-body-scope65/README_KO.md), [두 파일 검토 diff](../../experiments/pixel-pipeline/2026-10-31-body-scope65/body-scope65.patch), [실제 검사 결과](../../experiments/pixel-pipeline/2026-10-31-body-scope65/VALIDATION65.json). 기준 commit `b0312165aa7b331415f6f06394808ff5f69c3538`; 이번 commit은65 경로/이 절의 Git 이력으로 추적한다. 현재 수정 작업본 SHA에 맞춘 후보이며 **제품 파일 적용·import·Unity 조회·Play·렌더 0**이다.

| 스크립트·함수 | 확인/변경 |
|---|---|
| `audit65.py` / `SOURCE_AUDIT65.json` | Assets C#/shader/compute/hlsl483파일에서19관련 호출/선언,8파일과 생성/종료 근거2파일. 전역 buffer literal setter는 `ClothRegion524.BeginProbe` 한 곳. compute Prepare/Resolve와 OwnerLines는 이미 kernel-local. 컴파일 DLL·동적 이름까지 증명한 것은 아님 |
| 후보 `ClothRegion524.cs:BodyScopeResources551.Upload/Buffer/Commit/Dispose` | renderer별 직접 소유 buffer, lazy fallback, 성공 업로드 뒤 CPU/GPU 쌍 교체, 실패 candidate만 해제. 기존 skin-weight/primitive 포함 판정 식은 유지 |
| `ScopeOwner551/ReleaseScope551/ReleaseAllScopes551` | `Full319View335`별 소유권. 개별 종료와 기존 전체 adapter 종료를 분리·반복 해제 방지. CPU clothing의 기존 단일 current 준비 구조 전체를 재설계한 것은 아님 |
| `BeginProbe/Bind/BindLines553` | 전역 buffer 쓰기 대신 `MotionView331.Initialise`가 생성·소유한 probe 재질들의 `Material.SetBuffer`. compute는 해당 renderer buffer/count를 커널에 연결. unknown global getter/null/추정 복원 없음 |
| 후보 `Full319View335.cs:OnDisable` | `!ready` return보다 앞에서 scope owner 해제. 초기화 취소/실패 경로를 포함하며 기존 자산 저장/dirty 정리는 추가하지 않음 |
| `validate65.py` / `Harness65.cs` | 실제 후보 owner와 BeginProbe를 그대로 추출해 설치된 .NET csc+CPU fake로 컴파일/실행. 수명13사례, 생성20/해제20, 소스 불변식5개, 대상 Assets SHA변경0. `git apply --check`만 성공, apply 안 함 |

새 짧은 Play 승인은 도착했지만 실제 실행 전 안전성 조건은 남았다. 두 기존 C# 파일을 활성화하려면 import/재컴파일이 필요하며, Play의 `DisableDomainReload`만으로 script import reload를 막을 수 없다. 외부 command runner helper는 기존 정적 호출을 교체하지 않는다. 현재 미저장 내용과 reload 회피를 모두 보장할 방법은 미확인이라 이 단계에서 멈췄다. private reflection/hotpatch/추정 global/null 복원을 사용하지 않았다. 실제 Unity 전체 컴파일 실패·domain reload·GPU in-flight 수명·shader local override·scope off/on 이미지 동등성은 미검증이다. 이 모의 자원 수치를 실제 GPU 메모리 측정/안전한 Play 완료로 확대하지 않는다. 이전60 global 백업 부재와64 입력/곡선 공백도 해결됐다고 쓰지 않는다.


## 승인 실행66 — 복구 확인·검증 파서 수정,65 제품 미적용

[66 최신 상태/함수/검증](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/README_KO.md), [실제 복구 비교](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/RECOVERED66.json), [현 상태](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/STATUS66.json). 기준9cdad2b 이후 이번66 경로와 이 절의 Git 이력으로 추적한다. **65 Assets 패치/import/Play/캡처0**이다.

초기 TimeManager 원인 추정은 오류다. 반환29개 경로를 시작30개와 대조하면 TimeManager는26번째로 반환했고 Mesh가 미완료다. SaveAssetIfDirty(Object)의 실제 GUID lookup 결과/저장 여부는 기록되지 않아 반환을 저장 완료로 취급하지 않는다. Mesh JSON9.36MB를 작은 Json58 parser로 두 번 검증하며 각 숫자에서 입력 suffix 전체를3회 복사한 O(N²) 코드가 확인됐다.536,436숫자/단회parse 예상 누적복사13.81TiB는 RAM 측정이 아니다. loop는 성공 시 인덱스를 전진시키므로 무한loop 근거는 없지만 live stack/완료 ETA는 미확인이다.

| 스크립트·함수 | 실제 수행/한계 |
|---|---|
| `Backup66.cs:Execute/MeshBackup`, `check_backup66.py` | 디스크110파일11.23MB, native5JSON, 공개Mesh9.01MB binary(4060정점/7submesh/91bindposes/57morph delta) 보존·SHA·독립파싱. 큰 원본은 workspace backup에 유지 |
| `Observe66.ps1`, `OBSERVATION_RESULT66.json` | 새 Unity queue 없이 OS 관측.16.17초/CPU16.125초/byteIO0. earliest TID28308 Running, 다른 thread는 그 critical section 대기. WCT cycle 없음으로 전체 deadlock 배제를 주장하지 않음 |
| `Recover66.ps1` | 사용자11:27 승인 후 PID/project/starttime/백업 검증. 정상종료 요청8초 후에도 멈춘 PID28304만 종료. 동일 Unity6000.5.9f1/프로젝트를11:30UTC 새PID31520으로1회 시작. 다른 앱/worker 종료·파일/Library/cache 삭제0 |
| `Json58Linear66.cs:Parse/ParseValue` | 역사58 소스 보존. suffix 복사 제거, 작은JSON65,536chars cap, duplicate 거부 |
| `SerializedContent66.cs:HashFile/HashText/Verify` | UTF8/SHA streaming, 추가 buffers81,920bytes. exact 아니면≤64KiB만 의미 비교. 큰 불일치/고정밀/invalid는 미확정으로 남기며 성공을 만들지 않음 |
| `Save66.cs:Execute`, `build66.py` | 새 비교기와 항목별 전/후 stage 기록. 수정 Save66 재실행0. 디스크 수정이 기존 로드된 Unity코드를 hotpatch한 것이 아님 |
| `TestVerification66.cs`, `VERIFY_RESULT66.json` |14반례 통과, 큰 실제9.36MB 외부CLI1회12.311ms. hashed bytes2N/고정 buffers 확인, 일반 성능 보장 아님. Regex SDK참조 부재는 실행 전 실패 후 작은 scanner로 대체·14검사 재통과 |
| `Recovered66.cs:Execute` |11:33:15UTC 새Editor GameMap1 Edit/scene clean/roots37, options false/None, time1/captureDelta0/양PC_RPAsset 확인. Mesh와 설정4 serialized SHA 모두 백업과 ExactUTF8. dirty24→25는 Mesh load/ToJson 구간이며 Mesh 내용 동일 |

보호110파일과 기존30수정 bytes 변경0. 차이가 없어 원본 위에 backup을 복사하지 않았다. native object identity/compiled shader cache/GPU buffers/RT/static상태 완전복구 주장은 하지 않는다. 이후65 두 C# 적용·컴파일·실제 local-buffer 검증과64 동일source 입력 캡처가 남았다. O(N²) 검증이나 일괄저장/강제dirty해제를 다시 쓰지 않는다.


## BodyScope65 제품 적용·검증67 — 컴파일/작은native 통과, 실제 캡처 미완

[실제 적용·복원·차단 요약](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/PRODUCT_RESULT65.json), [선별 stage 보존 증거](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/PRODUCT_STAGE_PROOF65.json), [Play observer 종료 기록](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/CAPTURE_STATE66.json). 이전66 복구 상태에서 이어간 최신 단계다. 이번 commit은 두 제품 경로/이 절의 Git 이력으로 추적한다.

| 경로·함수 | 실제 변경·검증·미완 |
|---|---|
| `ClothRegion524.cs:BodyScopeResources551/ScopeOwner551/Scope551/BeginProbe/Bind/BindLines553/ReleaseScope551/Release` |65후보 실제 적용. runtime material-local buffer, kernel-local compute, renderer별 소유 및 upload-success 후 교체. source predicate/팔레트/기하 변경 없음 |
| `Full319View335.cs:OnDisable` |ready 전 scope 해제 hook 적용. 기존 두 파일의 사용자13/2·9/5 line delta는 unstaged에 그대로 남도록 index hunk만 분리 |
| `Compile66.cs:Execute` / `COMPILED65.json` |적용 후 자동 script compile/domain reload 완료, 새 public ReleaseScope551 직접 method-group 참조 성공. 명시적 Refresh는 bridge 재생성 중 Unity-not-detected로 미실행. 새 C# compile error0 |
| `ScopeCheck66.cs`, 추출 owner parity |실제 Unity ComputeBuffer3개 총20bytes, 임시 Material2개로 upload/교체/분리 handle/반복해제/invalid mask 검사 통과. global buffer 쓰기0/scene 변경0. private 제품 dictionary 직접 검사는 아님 |
| `Global66.cs` / `GLOBAL_NAMES66.json` |renderer63+scene rain11=74 named globals 외부 binary/SHA/역읽기 검증, 모두 복원 가능. engine-owned builtins 전체 상태까지 보장하지 않음 |
| `Capture66.cs:Execute/Tick/Finish` |승인된 Play 실제1회 진입. 정상 ready70초 timeout, 새 frame/plane/image0. frame1·2 trace만 있어 정상 renderer binding/64입력 계약은 미완. 배경/포커스 원인은 미확정 |
| `CAPTURE_STATE66.json`, `POST_CAPTURE66.json` |정상 Play 종료·observer 제거·options/pipeline/time 복원,74 getter 불일치0. RT41→41. Mesh/settings5 serialized 내용 모두 동일. allocated+451796588/reserved+431951872/mono-172806144bytes는 내부 Profiler counter이며 physical RAM/no-leak 보장 아님 |
| `CaptureRetry66.cs`, `prepare_retry66.py` |첫 실행 종료·복원 확인 후 기존 Editor 캡처처럼 runInBackground 임시true+상태trace를 준비. 자동심사가 추가Play/옵션변경 명시승인 없음으로 프로세스 생성 전에 거부. 실행/옵션변경0, 우회·재시도0. 추가 사용자 승인 필요 |

현재31520 Edit/GameMap1 clean, pausefalse/optionsfalse/None/time1/captureDelta0. 보호110파일 중 이번 두 C# 외 변경0, 다른 기존28파일 SHA와 두 파일의 기존 사용자 delta를 보존했다. NoSubscription은 별도 Unity AI 오류로 기록하고 변경하지 않았다. O(N²) helper나 일괄 저장을 재실행하지 않았다. sourceId `capture67-20261031T115608773Z`는 global journal만 있으며 실제 샘플 packet이 아니다. 새 이미지/미술 개선/시간 안정성 성공을 주장하지 않는다.

## 재개68 — 공식 연결·단일 Play 캡처와 원복 검증

[현재 결과](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/RESUME_RESULT68.json), [현재 기준선](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/RESUME68.json). 2026-11-01 05:22 UTC 기준 새 Editor PID35364/session1, Unity6000.5.9f1, 같은 프로젝트의 GameMap1 Edit/scene clean/options false·None/time1/captureDelta0/runInBackground false를 실제 공식 relay로 읽었다. 어제 PID/dirty를 현재값으로 재사용하지 않았다.

- `Resume68.cs:Execute`: 현재 미저장24개를 먼저 기록하고 resident Mesh/settings5의 직렬화 내용을 외부 파일/SHA로 검증했다. 얼굴 Mesh의 `EditorJsonUtility.ToJson` 읽기에서 dirty false→true가 다시 발생했다. 내용 SHA는 기존 백업과 같으며 저장·ClearDirty·추정 복원을 하지 않았다. 큰 JSON 전체 parse를 사용하지 않았다.
- `CaptureRetry66.cs:Execute/Tick/Capture/Finish`: 05:27 UTC 사용자의 구체 승인 후 단일 Play를 실행했다. trace는 frame1→59→94, Native ready/Gameplay connected true, main serial1을 기록했다. 새 sourceId `capture67-20261101T052807007Z`, frame94/evaluated0에서66 plane(동시 읽기1개, 최대983040bytes), 평가 mesh3/material15/bone pose/view·projection/UV/source/g/Q/owner·depth 및 눈13part를 보존했다. sourceId/pose를 과거 프레임과 섞지 않았다. 실제 main/head의 material-local BodyScope551 binding15개씩을 확인했다.
- 재개 지시만 있을 때의 자동 심사 거절은 미실행이었다. 이후 사용자가 runInBackground 임시true·추가 Play1회·종료/원복을 명시 승인해 같은 정식 relay 경로로1회 실행했고 성공했다. 추가 Play는 하지 않았다. 이번 trace의 focused는 모두true이며 어제의 실패 원인을 비활성 창 하나로 확정하지 않는다.
- 연결 통로: source 편집은 Codex `apply_patch`; Editor 실행은 `exec_command → relay66.py → ~/.unity/relay/relay_win.exe --mcp → Unity MCP bridge → Unity_RunCommand/Unity_GetConsoleLogs`. 현재 read command의 compile/execution 모두 성공했다. manifest/lock/설치본의 `com.unity.ai.assistant=2.18.0-pre.2`; inference2.6.1/navigation2.0.14, 별도 Codex/MCP 패키지는 manifest에서 발견하지 못했다.
- 설치 패키지 `Documentation~/integration/unity-mcp-get-started.md:116–129`는 direct-client 최초 승인과 승인 기억/자동 재연결을 설명한다. `Modules/Unity.AI.MCP.Editor/Settings/UI/ConnectionApprovalDialog.cs`와 `Modules/Unity.AI.Assistant.Tools/Scripting/RunCommandTool.cs:55–73`의 연결 승인/unsafe 실행 승인은 별도다. 사용자가 과거 본 창이 어느 쪽인지는 미확인이다. 승인창 부재만으로 Win11 연동 해제를 단정하지 않는다.
- 오늘 Console에도 `NoSubscription` Info5건(로컬14:21:27–29)이 있으며 `ModelSelectorSuperProxyActions`의 Unity 생성 모델 목록 조회 경로다. 동시에 MCP 조회는 성공했다. Unity 내장 모델 서비스와 현재 외부 Codex 도구 통로를 구분하며 로그인/설정/패키지를 변경하지 않았다.

현재 상세 결과는 [CAPTURE_RESULT68.json](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/CAPTURE_RESULT68.json), [실제 PNG/입력 검토](../../experiments/pixel-pipeline/2026-10-31-apply-capture66/retry-background/capture67-20261101T052807007Z/offline68/INDEX.html)로 연결한다.

| 경로·함수 | 실제 검증·남은 한계 |
|---|---|
| `Post68.cs:Execute`, `Option68.cs:Execute` | 05:28:44 UTC Edit/GameMap1 clean, 옵션 false/None·background false·time1/capture0·pipeline 복원, observer 제거,74global getter 불일치0. Mesh/settings5 native 내용 ExactUTF8 동일. PlayerSettings/Application 두 background getter도false. 전체 PlayerSettings native 사전 백업은 없어 그 객체의 모든 필드 동등성은 미검증 |
| `CAPTURE_RESULT68.json` | Play 직전dirty25→종료후29. 기존25개 제거0, EditorSettings/GraphicsSettings/TimeManager/PlayerSettings가dirty 추가. 저장·ClearDirty하지 않았다. tracked 관련31파일 SHA 변경0 |
| `analyse_capture68.py:plane/camera/geometry/main` |66plane의 sourceId/frame94/serial1·유한값·파일길이, final960×544 전체522240표본 검증. 가시 native1734표본 전부 actual mesh/submesh/triangle/UV·barycentric/material로 유일 연결. world오차 최대1.442e-7m, nativeShift1회 적용 재투영 오차 최대0.002593px. 코드의 material명/역할 상수로 provenance를 대신하지 않았다 |
| `test_reader68.py`, `EYE_OBSERVER68.patch` | 동일 packet 및 잘못된 source/frame/serial 거부와 비항등 texture ST/barycentric fixture 5검사 통과. 눈 count/records는 관찰기의 전역 검색에서 누락됐다. HeadLocal367:18–19의 HideAndDontSave/headEyes 직접 소유 참조, :37의 실제 headEyes dispatch를 확인해 direct host 참조의 관찰기 최소 패치만 준비했다. 미적용·GPU 미검증이며 재캡처하지 않았다 |
| PNG 및 원배율/nearest 확대 | full/current-source/part10 backing PNG를 실제 열어 확인했다. part10은 현재 pose의 실제 5셀이며 과거 6목표셀을 추정 피부색으로 채우지 않았다. 기존 제품 출력만 보여주며 새 팔레트/영역/눈 후보 적용이나 미술 성공이 아니다 |

Profiler allocated는 05:28:07→05:28:17에 +476637854bytes(+454.557MiB), reserved +433508352bytes, mono -532090880bytes다. ready→readback 해제의 allocated 증가는 +852240bytes(0.813MiB), RT는 30→ready437→종료30이다. physical RAM 측정/총메모리 복원/누수 없음의 증명이 아니다. 종료 후 Console 최근 50건에는 Error/Exception/Assert 0이며 새 material binding 오류를 찾지 못했다. 전체 Console 역사에 오류가 없다는 뜻은 아니다.

아직 UV source-feature 경계 graph 투영, 연속 셀 부분 coverage 적분, 과거 6backing 목표와 새 source의 surface 대응, 누락된 눈 feature/count, 실제 회전/blink/시간 안정성은 미검증이라 raw `packetComplete=false`를 유지한다. 이번 제품 파일 변경은 0이며 기존 65커밋 `6a1f2f4a`를 유지한다. 실제 캡처와 오프라인 검증/관찰기 패치를 기존 실험 폴더에만 선택 커밋하며 관련 커밋은 이 절의 Git 이력으로 확인한다.

## 경계69 — 실제 source 대조, 면적 후보 미채택

[동일 입력 비교 PNG·수치](../../experiments/pixel-pipeline/2026-11-01-boundary-input69/INDEX.html), [좌표별 결과](../../experiments/pixel-pipeline/2026-11-01-boundary-input69/RESULT69.json), [회귀10건](../../experiments/pixel-pipeline/2026-11-01-boundary-input69/TEST69.json). 입력은68의 새 sourceId/frame94만 사용했다. 이번 Unity 호출/Play/렌더/옵션 변경/제품 변경은 모두0이다. RGB blur, 새 palette, 명암 임계값 조절은 하지 않았다.

| 스크립트·함수 | 변경 전제·검증·한계 |
|---|---|
| `probe69.py:counts/main`, `schema69.py:shade_labels` | 실제 logical hair373셀의 Q는4연결7영역/단독4셀, native1463표본은17영역/단독7셀이다. 현재 ShadeBoundary 전후 변경0. EyeFeature348.compute:217/222 후단 UV.z는9개 셀에서 primitive 번호로 바뀐다. 이를 Q로 읽는 분석은 잘못이며 producer schema로 거부한다. 제품 RGB 버그나 실제 분할 감소로 확대하지 않는다. 과거63의 색 범위66영역과 현재Q7영역은 서로 다른 집계다 |
| `coverage_boundary69.py:build_reference/both_diagonals` | native g의 선형 보간에서 두 대각선 모두의 면적 하한을 구해 방향 편향을 막았다. source의 실제 공유 정점이 확인되지 않은 구간은 미확인 면적으로 남겼다. 이는 보수적인 충분 조건이며 탈락 구간 전부가 실제 가림이라는 뜻은 아니다. 연속 조명/mesh coverage의 해석적 정답이 아니다 |
| `run69.py:main`, `metrics69.py:fixed_reference/reference_gate` | 후보는(213,51),(213,50) 두 셀의Q를0→1로 바꾼다(논리 y-down). 밝음 면적 하한.609501/.711969로 면적 목표는 개선됐지만, 고정 참조의 위치RMSE .382867→.343831px와 달리 접선 비용.238490→.264986이 악화됐다. 다른 대각선에서도 별도 평가했다. 영역7/단독4/경계46 유지. 접선 회귀로 거부하고 QAccepted는 원본을 유지한다 |
| `run69.py`의 원본 source64 대조 | 현재 평가 mesh UV/index 해시와 기존 원본 PNG 해시를 확인했다. 원본의 밝은 무늬가 보이는 material13에서도64 coarse/fine 영역은 각각1개다. 불확실 edge11,652개는 존재하지만 기존 contour 계층에서 제외됐다. 69는 이를 soft contour로 export한다. 조각3,973개를 의미 특징이나 강제 경계로 승격하지 않았다. hard jump 검출만으로 넓은 gradient 무늬의 특징 영역이 완성됐다고 보는 전제가 틀렸다 |
| `test69.py`, `OBSERVER_REQUIREMENTS69.json` | 회전90/180/270, 얇은 띠/구멍/다른 source 보존, 잘못된 Q schema 거부, 실제 접선 회귀 거부 등10건 통과. direct-host 눈 패치는 source API 참조만 확인했으며 미적용이다. 추가로 count stride48(float4 a,b,uv), records stride256·전체33,423,360bytes가 기존4/16stride·1MiB 읽기 함수와 맞지 않음을 확인했다. 실제ROI 행별 typed readback이 추가로 필요하다 |

대표 좌표(225,59)/(230,55)는 같은 hair domain의4방향 이웃이 없는 실루엣/틈이다. (212,48)은 g=.499622이며 한 셀 안 native source가sm2 primitive4851/4849·2364와sm1 primitive1024로 달라진다. (226,36)도 silhouette에 인접하고 native1007/1009/1068과1193이 섞인다. 모두 잡음으로 덮는 대조군은 영역7→5/단독4→3/경계46→40으로 줄지만 실제 표면을 넘는 보간이므로 채택하지 않았다. 원배율·정수 확대와 실제 원본 texture 도판을 직접 열어 확인했다.

확정된 분석/입력 연결 수정과 미채택 공간 후보를 구분한다. 전체 source-feature 영역·공유 곡선의 완성/현재 캐릭터의 미술 개선/시간 안정성은 입증하지 못했다. 머리의 soft 경계 선택·투영/더 완전한 surface 연결 분석은 현재 자료로 계속할 수 있어 새 Play를 이유로 멈출 부분이 아니다. 실제 눈 공동 배치/가림 검증에는 정확한 eye count/record ROI 및 feature state가 필요하며, 새 sourceId의 추가 캡처는 별도 승인 전 실행하지 않는다. 기존 dirty29는 마지막 live 확인값이며 이번 오프라인 작업에서 다시 조회하거나 해제하지 않았다. 변경 파일과 관련 커밋은 이 절의 Git 이력으로 확인한다.

## 경계70 — 연결 경계 계약 수정·관측 한계·bounded 눈 읽기 준비

[현재 검토 페이지의70절](../../experiments/pixel-pipeline/2026-11-01-boundary-input69/INDEX.html), [실제 곡선 감사](../../experiments/pixel-pipeline/2026-11-01-boundary-input69/CURVE_REPORT70.json), [다음 최소 입력 계약](../../experiments/pixel-pipeline/2026-11-01-boundary-input69/NEXT_INPUT70.json). 이번도 Unity 호출/Play/렌더/import/제품·RGB·Q·팔레트 변경0이다.

| 스크립트·함수 | 실제 변경·검증·미적용 구분 |
|---|---|
| `schema69.py:shade_labels` | producer schema를 강제하고 실제 단계 수의 정수ID를 반환한다. 2/3/4단계의 중간값을 binary round로 소실시키지 않으며 float32 한ULP 밖의 미등록 값을 거부한다.69의 면적 후보는 명시적으로2단계 전용이며 다른 단계 입력을 중단한다 |
| `source_contours70.py:trace_evidence` | persistent/fine/uncertain을 먼저 합쳐 같은 연결 경로를 하나의 순서 있는 곡선 ID로 전달한다. 등급이 바뀌었다는 이유로 분리하지 않고, 간선별 등급과 실제 분기점/끝점 pin을 유지한다. 얇은 띠 양쪽·작은 loop·원래 gap은 보존한다. uncertain은 hard feature가 아니다 |
| `run_contours70.py:clip_segments/main` | 같은 capture67의 평가 geometry와 camera로 실제 관측된 삼각형에 source 경계를 투영했다. 원본 source 곡선 ID, 기하 배치 ID, source 구간 매개변수, primitive, 가까운 native 표본의 일치 여부를 분리한다. 반복된 texture의 다른 배치를 하나의 가시 곡선/가림 owner로 합치지 않는다. runtime wrap/filter가 없으므로 unit texture tile만 다루며 전체 가시성은 미확인이다 |
| `test_contours70.py` | 연결 등급 전환·순회 순서·분기·한texel 띠·loop·gap·2/3/4단계 schema·반복 배치·source 구간 등14검사 통과. 기존69 회귀10건도 통과했다. 합성 반례의 연속장 두 개가 같은 sparse 표본을 내면서 다른 중간 등명암선을 가질 수 있음을 확인했다. 실제 장면 재현이나 픽셀아트 불가능의 증명이 아니다 |
| `EyeReadback70.cs:Readback.Counts/Records`, `UnityEyeBuffer70.cs` | 실제48byte FeaturePacket19와256byte Pixel348을 typed 행별 GetData로 읽는 독립 코어/비소유 adapter 구현. source/frame/view/serial·ROI·stride/count·1MiB payload를 검사한다. 실패·취소·상태 변경은 partial을 남기며 완료 파일을 만들지 않고, 중복은 덮어쓰지 않는다. borrowed ComputeBuffer를 Dispose하지 않는다 |
| `TestEyeReadback70.cs`, `test_eye70.py` | 독립 C# 실행11검사 및 실제6000.5 Unity CoreModule 참조 adapter 컴파일 통과. 테스트 records 행8,448bytes, 전체 너비 행도122,880bytes. 실제 GPU 읽기·Unity 동적SDK 컴파일·호출자 연결은 미실행이다. `EYE_CALLER70.patch`는 direct host 참조, ROI 변환, mode에 따른 count skip, typed reader 호출의 미적용 패치다 |

정정:64에는 이미 persistent/fine contour component가 있었다.69에서 확인한 누락은 uncertain 등급 및 등급 사이의 순서/정체성 전달이다. fill region 수1은 경계 증거가0이라는 뜻이 아니다.70의 source13은15,998간선/4,983순서 경로이며 그중26개만 전 구간 persistent 검출이다. 이것도 의미 특징의 자동 승인 수가 아니다. 대표281texel 경로는 실제 기하 배치 하나에서 약3.085논리px의 가까운 표본 일치 길이가 있었지만 직선 source 구분선이며 밝은 띠 전체의 승인된 곡선이 아니다. 단절·가림을 추정으로 메우거나 자체 평활화를 정답으로 놓지 않았다.

현재 기준은 원본 source64 검출 raster 간선과 같은 프레임의 실제 geometry이다. source 색 경계를 g 명암 경계의 정답으로 교체하지 않는다. 승인된 연속 특징 경계/영역과 독립적인 고밀도 g 기준이 없으므로, 전체 곡선 재배치·픽셀 미술 개선 판정 직전에서 중단한다. 다음 입력은 CPU sampler metadata와 실제 eye count/records ROI이며, 명암 곡선을 검증한다면 같은 조명 producer의 작은6배 ROI가 선택적 독립 관측이다.6배는 기존2배 표본을 k=3j+1로 포함시키기 위한 진단 격자이며 제품 해상도나 palette 단계가 아니다. dense 자료도 작가의 의도를 주지는 않으므로 형태 추론 기준 또는 독립 검토한 source 영역/corridor가 별도로 필요하다. 실행 승인은 요청/실행하지 않았다.

제품 기본 경로와 기존 사용자 파일은 유지했다. 마지막 live dirty29를 현재값으로 재가정하지 않았고 이번에는 조회/해제하지 않았다. 이 절의 변경 파일·함수와 커밋은 Git 이력으로 확인한다.

## 가림71 — 저장된 전체 기하로 연속 선분의 불투명 가림 계산

경로: `experiments/pixel-pipeline/2026-11-01-boundary-input69/`.

- `opaque_visibility71.py:from_meshes/OpaqueScene.line`: capture67의 같은 sourceId/frame94/serial1, 평가 삼각형29,542개 전체를 사용한다. 직교 투영을 확인한 뒤 화면 삼각형 진입·이탈 및 선형 view-depth 교차로 선분 전체를 분할한다. 최근접 표본 하나로 구간 전체를 판정하지 않는다. 모든 삼각형을 양면 불투명으로 둔 조건부 계산이며, 실제 shader alpha/cull 동등성을 주장하지 않는다. perspective/near-far clipping 입력은 지원하지 않으며 조용히 생략하지 않고 거부한다.
- `run_visibility71.py:main`: 기존 실제 GPU 표본1,734개 중 같은 불투명 최전면1,706개, 불일치28개. 머리는1,463개 중1,454개 일치. 불일치 중5개는 실제 기록 primitive가 이상적인 pixel centre를 포함하지 않는 격자 경계 사례,23개는 centre를 포함하지만 다른 불투명 삼각형이 더 앞인 사례다. alpha·culling·렌더 자격 중 원인은 아직 분리되지 않았다. 원본 source barycentric 재투영 위치에서도1,710개만 일치하므로 전체 shader 동등성은 성립하지 않는다. 좌표별 결과는 `OPAQUE_SAMPLES71.json`에 보존했다.
- 전체 source 투영 조각34,071개 중 기하상 완전 무가림28,357개 / 완전 잠재가림5,603개 / 부분 잠재가림111개. 이는 여러 texture 배치에 걸친 원본 경계 조각 수이며 의미 특징 수나 품질 지표가 아니다. `OPAQUE_SEGMENTS71.npz`는 원본70 조각 인덱스를 그대로 사용한다.
- 대표 curve8701/placement36의 투영 길이4.3942445logical px 중 불투명 기하상 무가림1.6610199px. 이전 최근접 native 표본 일치 길이3.0854417px와는 **측정 정의가 다르다**. 허용 오차1e-7/1e-6/1e-5m에서 대표 무가림 길이는 같았다. `REPRESENTATIVE_VISIBILITY71.json`의 sourceParameter/primitive/가림 구간과 `OPAQUE_LINE71.png`를 확인했다. 청록=기하상 무가림, 주황=불투명 가정의 잠재가림이며 실제 머리 RGB 변경 이미지가 아니다.
- `test_visibility71.py`: 삼각형 진입·이탈, 깊이 교차, 뒤쪽/동일평면, 중점에 걸리지 않는 얇은 가림, 전체가림, 겹친 구간 합집합, 방향 반전, 점-선분 일치, 퇴화 삼각형10검사 통과.

판정: 저장 기하로 **조건부 가림 구간 계산은 가능**하며 새 geometry 캡처가 반드시 필요한 상태는 아니다. 그러나 실제 Native333은 material cull과 MToon alpha 판정을 사용하고 원본 hair11~14도 MASK 재질이다. 현재 runtime keywords/cutoff/cull/texture sampling 및 구간 전체에서 target fragment가 살아남는지는 미기록이다. 따라서 기하상 무가림을 실제 최종 표시 확정으로, 잠재가림을 실제 제거 대상으로 승격하지 않는다. 독립적인 미술 기준곡선도 없으므로 이번 결과에서 확정하여 보정에 쓸 구간은0개다. 새 후보·Q/색/팔레트 수정 없이 종료한다.

추가 관측 최소 범위는 geometry 재수집 자체가 아니라 actual runtime material/alpha/cull/sampler 상태와 필요한 source 경계 구간의 fragment 생존·owner/depth 검증이다. 조명 등고선의 기준은 별도 문제여서 dense g 관측 또는 명시된 설계 기준이 필요하다. 눈 최소 입력 계약은 `NEXT_INPUT70.json`을 유지한다. 이번에는 Unity 호출/Play/import/화면 제어0회. 제품 및 기존 사용자 파일은 변경하지 않았으며 관련 커밋은 이 절을 추가한 Git 이력에서 확인한다.

## 눈 관찰기72 — 외부 명령 결합 준비, SDK 승인 상호작용에서 차단

`experiments/pixel-pipeline/2026-11-01-eye-observer72/RESULT72.json` 참조. 최신 사용자 승인 후 기존 공식 relay로 PID35364/Unity6000.5.9f1/GameMap1을 확인했다.06:37:24~06:40:10UTC 전후 읽기에서 Edit/scene clean/dirty29개와 각 identity, domain1, Play옵션 false/None, pause/time/pipeline/build scenes가 동일했다. 관련 디스크31파일 SHA도 동일하다. 관찰기의 전체 PlayerSettings 백업/비교는 **미실행**이므로 전 native 내용 동등성을 주장하지 않는다.

- `build72.py`: 기존 CaptureRetry66와 EyeReadback70/UnityEyeBuffer70를 Assets 밖에서 결합한다. 첫 동적 컴파일은 namespace 오류로 실행되지 않았다. 설치 SDK `SyntaxTreeUtility.MoveToNamespace`가 첫 namespace만 바꾸는 것을 확인하고, 전체 소스를 SDK가 원래 사용하는 단일 outer namespace 안에 넣어 결합했다. SDK나 패키지는 수정하지 않았다.
- `Capture72.cs:Capture`: 실제 `n.host.headEyes/mainEyes`와 해당 full/view를 맞추고 ROI의 typed48/256byte reader를 호출한다. 생산 모드에 따라 counts를 명시적으로 skipped로 기록하고, 동일 frame/serial/source/view 검사를 유지한다. `NativeSnapshot72.Backup/Compare`는 실행 전에 로드된 dirty 자산 및 설정의 직렬화 백업과 전체 PlayerSettings 존재를 확인하고 종료 후 비교하도록 준비했다. 대형 메쉬 비교는 기존 선형 스트리밍 SHA 경로다. 그러나 이 관찰기 호출은 아직 보내지 않았다.
- 컴파일 검증 재시도는 `User interactions are not supported for MCP tool calls. Tools requiring user interaction cannot be called via MCP.`로 차단됐다. 설치 SDK `RunCommandCodeAnalyzer.k_UnsafeMethods`가 reader의 `System.IO.File.Move`(.partial→완료 파일)를 위험 연산으로 분류하고, `RunCommandTool`이 실행 전에 승인을 요구하지만 `NoOpToolInteractions`는 MCP에서 이를 지원하지 않는다. 전체 컴파일 성공 플래그는 반환되지 않았으므로 성공 확정으로 쓰지 않는다.
- Play0회, 캡처 호출0회, 옵션변경0회, Native backup/capture state 파일 없음. 별도 읽기 전용 Post72는 정상 응답했다. GPU 자원/빌린 버퍼를 생성·해제하지 않았고 Assets import/재컴파일/정리/우회도 하지 않았다. 새 GPU 데이터가 없으므로 눈 연결 검증도 미수행이다.

현재 blocker는 사용자 승인 부재가 아니라 **SDK의 승인 상호작용을 현재 MCP가 지원하지 않는 것**이다. File.Move를 다른 파일 API/Reflection으로 바꾸어 우회하지 않았다. 다음 선택은 승인 상호작용을 지원하는 정식 통로 또는 이름 변경 없이 새 파일만 쓰는 별도 완료-marker 프로토콜의 사전 검토다. 후자는 이번에 구현·실행하지 않았으며 reader/consumer 계약과 실패 복구를 먼저 검토해야 한다. 사용자 화면 제어 없이 이 문제를 해결하기 전에는 Capture72를 실행하지 않는다. 이번 커밋은 이 절과 외부 준비 코드/차단 증거만 포함하며 제품 통합·미술 성공이 아니다.

## 눈 관찰기73 — 신규 파일·완료 marker로 실제 1회 캡처/원복

경로 `experiments/pixel-pipeline/2026-11-01-eye-observer73/INDEX.html`, 커밋은 이 절을 추가한 Git 이력 참조. 제품·씬·Assets·31/34 도구는 변경하지 않았다.

- `EyeReadback73.cs:Readback.Complete/CompletedPath`: 데이터는 최초 생성한 `.partial` 이름을 그대로 유지한다. 전체 기록·Flush·SHA256/크기·source/view/frame/serial 검사 후 `ok-{SHA256}-{bytes}.complete` 빈 파일을 CreateNew로 마지막 생성한다. 소비자는 marker 존재만 보지 않고 실제 데이터 해시/길이/헤더/행 인덱스/EOF를 검증한다. 이동·삭제·기존 파일 덮어쓰기가 없으며, 소프트웨어 실패·취소·프레임 변경 때 완료 marker가 없는13개 오프라인 검사를 통과했다. OS crash 내구성 시험을 뜻하지 않는다. 상태 기록도 `STATE73-NNNN-stage.json`으로 새 파일만 생성한다.
- `build73.py`, `Compile73.cs`: 설치 SDK가 기대하는 단일 outer namespace 안에 전체 의존성을 넣었다. 실제 Unity 외부 runner 전체 동적 컴파일 통과 후 실행했다. 패키지/승인 설정/Assets import/프로젝트 재컴파일은 없었다.
- `Capture73.cs:Execute/Tick/Capture/Finish`: 승인된 Play1회, 정상 Gameplay history의 실제 frame94/serial1, sourceId `eye73-20261101T071040550Z-a7d96049` 한 프레임. eye ROI top-left(212,49,16,8)→GPU(212,215,16,8), counts48byte256개/records256byte128개를 행별로 읽었다. 데이터 파일12,673/33,038bytes, payload12,288/32,768bytes. 한 행 최대4,096bytes. counts producer 실제 실행, UseIrisSurface582=false/UseLashRegion583=false를 함께 기록했다. source/view/frame/serial 및 모든 companion plane identity 일치.
- `NativeSnapshot73.Backup/Compare`: 실행 전 현재29dirty 자산과 로드된 설정을 직렬화·스트리밍 해시로 외부 백업했다. 종료 후 기존29dirty 내용 모두 ExactUTF8, PlayerSettings 전체25,590bytes도 동일. 전체45대상 중44동일이고 **비dirty AssetImporter 1개**(ProjectSettings.asset,145bytes)는 종료 후 객체가 조회되지 않아 미확인이다. 처음 경로만 보고 PlayerSettings 차이라고 보고했으나 본체 차이는 없었다. importer를 강제 재생성하거나 dirty를 지우지 않았다. 원본 native snapshot에는 민감 설정이 포함될 수 있어 Git에는 넣지 않고 로컬에만 보존했다.
- `analyse73.py:read/main`: SHA marker·2눈 counts 전체ROI·records ROI의 실제 전역 인덱스/64float순서/finite/EOF를 검증한다. IrisAllocated19의 float32 면적 누적·반올림·정렬을 동결 packet으로 재현했다. stableId2는6개 양의 홍채 후보/면적2.3759196셀→2셀(216,52/53), stableId1은5개/2.1628428셀→2셀(224,52/53). GPU visible iris도 각각 정확히 이2셀이고 allocator 이후 추가 소실0이다. record RGB와 같은 head source-final ROI의 선형RGB 최대차0, 실제 iris pigment role=1. Own의 template 좌표/role provenance는 있지만 TemplateRGBA/TemplateRole 원본 bank 자체는 별도 읽지 않았으므로 원색 bank 완전 검증은 아니다.
- `RESULT73.json`, `VERIFICATION73.json`: 정상 Play종료/observer 제거, background와 PlayerSettings.runInBackground, Play옵션 false/None, pause/time/pipeline, scene clean/dirty29identity 유지, Shader global getter 불일치0, 디스크31파일 SHA 동일. RT30→437→30. Unity GetTotalAllocatedMemoryLong 전후+33.2156MiB, ready→readback 해제 후+.6591MiB. physical RAM 수치가 아니며 누수 유무 확정이 아니다. Console 조회 errorCount0. 추가 Play·강제GC·정리 없음.

원배율/nearest20 눈, 진단 feature 지도, 전체 PNG를 실제로 열어 확인했다. 이번 결과는 **데이터 누락 해결 및 현재 allocator 연결 검증**이다. 새 눈 보정은 제품/GPU에 적용하지 않았다. source 후보가 많아도 면적 반올림/순위가2셀을 결정하는 현 경로가 확인됐으며, 현재 출력의 미술 성공이나 움직임 안정화를 뜻하지 않는다. 과거 frame100/101·실제 회전·blink 반례 재현은 아니며, counts 합계에는 개별 subsample 가림 원인이 남지 않는 한계가 있다. 고밀도 헤어 패스도 실행하지 않았다. `VALIDATED_CAPTURE73.json`은 이 제한을 유지한 한 프레임 데이터 검증 marker다.

### 승인 반복 원인 — 설치본 읽기 근거, 설정 변경 없음

설치 Unity Assistant2.18.0-pre.2의 `ToolPermissions.CodeExecution.cs:CheckCodeExecution/GetCodeExecutionPermission`, `ToolPermissions.State.cs:SaveState/TryLoadState`에는 AllowOnce/AllowAlways와 범주별 임시 승인 상태가 있고 EditorPrefs 저장으로 domain reload를 넘겨 유지한다. 정확한 만료 범위·다른 클라이언트까지의 보장은 이 코드만으로 확정하지 않는다. `McpToolApprovalHandler.RequestApprovalAsync/Complete`는 활성 ACP 세션의 Allow/Always Allow 응답을 클라이언트에 반환하지만, 현재 외부 relay 클라이언트가 이를 어떻게 저장하는지까지 확인하지는 않았다.

이 경로는 `RunCommandTool`의 별도 unsafe-command 승인과 다르다. `UnsafeCommandApprovalInteraction`은 매번 새로운 interaction이며 `ShowScope=false`; `NoOpToolInteractions.WaitForUser`는 외부 MCP의 상호작용을 지원하지 않는다. 따라서 일반 승인 기억 기능이 File.Move 차단을 해소한다고 말할 수 없다.73은 사용자 승인대로 이동 없는 새 출력 계약을 구현하여 이 불필요한 위험 연산 자체를 없앴다. 이미 승인된 동일 범위의 컴파일/읽기/정상 종료·원복을 단계마다 다시 허가받을 필요는 없지만, Play1회 승인을 추가 Play/제품 변경/보안 변경까지 확대하지 않는다. 승인 검사·full-auto·허용목록·보안 설정은 변경하지 않았고 우회도 하지 않았다. 관련 설치 소스 경로/해시는 `APPROVAL_SOURCE73.json`에 있다.

## 눈 allocator74 — 연결성 누락의 제한 수정/대가 확인, 미채택

경로 `experiments/pixel-pipeline/2026-11-01-eye-allocator74/INDEX.html`. Unity 호출·제품 변경·import·추가 Play0회. 실제73의 ROI counts/records와 기존47의6프레임/49동결 fixture,52원본 keyform,53실패 및55부분가림 정정을 재사용했다. 관련 커밋은 이 절의 Git 이력 참조.

- 현 `EyeFeature348.compute:IrisAllocated19/BeforeIris19`는 `K=floor(sum(I/16)+.5)`와 `c=max(sclera,upperLine,lowerLid)-I`의 셀별 top-K다. 원래 면적에 근거한 K=2 자체가 버그는 아니다. 하지만 집합의 연결/원형/소스 cell identity/다른 eye part 공동 배치/프레임 대응 항이 없다. 같은 가시 source 후보가 연결돼도 출력만 대각으로 찢어질 수 있다. `NativeLineAllocated19`가 iris occupancy를 다시 읽으므로 iris만 확대하는49는 상안검 feedback 회귀가 있었다.
- `allocator74.py:legacy/connected`: 원래 float32 면적·K·점수·tie를 유지하고, **명시된 source/style 연결 계약이 있을 때만** 연결된 동일 K개 집합 중 기존 점수합 최소를 찾는 작은 오프라인 후보다. 기준은52의 Template216/205 iris가4연결이라는 기존 형상이며 모든 픽셀아트/모든 pose의 규칙이라고 하지 않는다. 현재73은52와 mesh topology SHA가 같지만 전체 Template bank/style/state 연결은 검증되지 않았으므로 제품 적용 근거가 아니다. 4/2셀·좌우 동일 크기를 하드코딩하지 않는다. 계약 없음/가시 support 단절/조합 예산 초과는 미결정으로 남기고 가림을 잇지 않는다. RGB/팔레트·source 가중치·budget은 바꾸지 않는다.
- `run74.py`: 기존47의12 eye-frame 중6개가 연결 후보 영역에서 대각2셀을 선택했다. 조건부 후보에서는12개 모두 연결되며 K는 전부 동일, NativeLine allocation 변화0. 73의 두 눈은 선택/RGB 모두 기존 그대로(새 candidate RGB를 만든 것이 아님). 원 packet 재생 최대오차5.96046448e-8,49의 저장 fixture로 원47 결과가 완전히 재현되는 것도 확인했다. 이는 원래 셀 손실·형상왜곡 전부 해결이 아니다.
- 대가를 숨기지 않는다. 바뀐6쌍의 기존 점수 비용은+.99697~+3.0이고, 보존되는 iris source 가중치는 한 쌍만+1.0030, 나머지는-.000915~ -1.02806이다. 원 raster-weighted centre 오차는5/6 증가한다. 별도 `source_centre74.py`로 측정 head/camera의 실제 modelEye.centre를 투영한 기준에서도2쌍 개선/4쌍 악화다. 이 기준은 후보 자체의 평활화 결과가 아니며 승인된 미술 중심점도 아니다. 새 점유 셀은4쌍에서 기존 lower-like feature6,2쌍에서 흰자를 대체한다. feature6은 실제 native lid로 확정되지 않았지만, 이를 무조건 지워도 된다는 뜻이 아니다. 상안검 rank가 같아도 전체 눈 보존은 아니다. 따라서 **미채택**이다.
- `test74.py`:16검사 통과. 입력 연결 계약/4·8연결 구분,0·1셀 예산 유지, 가시 support gap 보존, 제한 CPU 조합 수, 동점 불확실성, 독립 예산, translation/비동점 rotation, 현재 한계를 반증하는 미세 점수 변화의 connected-cluster 점프까지 포함한다. 마지막 반례에서 연결성만 지켜도 아주 작은 연속 입력 변화로 위치가 바뀐다. 시간 안정화/소수 좌표 이동 해법이라고 주장하지 않는다.

49의 공통 `floor(delta+.5)`는 정수 이동이고,53의 any(front)는 전체 기각의 과도한 가정이며 pareto 필드는 실제 Pareto 집합이 아니라는 기존 정정을 유지한다.74는 이들을 다시 실행해 근거로 삼지 않았다. 55의 부분 가시량은 실제 opaque cell 채택/합성을 보장하지 않는다. 과거 source47과 현재 source73은 섞지 않았다. 현재73 연속프레임은 없고, 과거47는 실제6프레임이지만 새 후보는 그 동결 입력의 CPU 재생일 뿐 live GPU 시간 검증이 아니다.

다음의 설계/관측을 구분한다. **설계:** 중요 눈의 전체 keyform에서 허용할 크기·연결·안검/흰자/홍채 관계와 source 기하 이동 사이의 대가를 공동으로 정의해야 한다. 이를2px 최소나 연결성 하나로 대체할 수 없다. **관측:**73은 각16 subsample의 역할/가림과 TemplateRole/RGBA bank 전체를 저장하지 않았으며 완전한 현재 state binding도 없다. 과거47의 바뀌는 셀 clean backing을73의 새 source로 채우지 않는다. 따라서 기존 그림 위에 iris만 재색칠한 완성 RGB를 만들지 않았다. 비교 PNG는 실제 RGB/기존 가시 iris ID/조건부 후보 ID의 순서이고 뒤 두 열은 진단색이다. 새 후보를 더 늘리거나 가중치를 튜닝하지 않고 이 충돌을 남긴다. 원본 및 제품/사용자 파일은 보존하며 현재 Editor dirty 상태를 새로 조회하지 않았다.

## 전체 눈75 — 실제 bank 복원·공동 제약 감사, 완성 후보 없음

경로 `experiments/pixel-pipeline/2026-11-01-whole-eye75/INDEX.html`. Unity 호출/추가 Play/import/제품 변경0회. 기존 데이터만 사용했다. 관련 커밋은 이 절의 Git 이력 참조.

### 복원한 실제 자료와 코드 경로

- `audit75.py:texture/main`: 실제 ValidatedPresentation399.prefab의 Template GUID를 따라 SocketTemplate216/Inputs/TemplateRGBA.asset(RGBA32)와 TemplateRole.asset(RGBAFloat)를 직접 읽었다.480×272 단일2D bank의 유효20셀은 눈마다 iris role1=4/white role4=6이며 role6 안검은0이다. 과거49 fixture20셀의 ID/좌표/색과 전부 동일하다. 현재73의 Own 경유10표본도 원본 bank좌표/role와 대응하고 최종 인코딩 sRGB8 차이0이다. 표준 sRGB 역변환과 실제 선형float의 최대차.0019122는 남기며 bit-exact 선형 일치라고 하지 않는다. 현재 GPU bank 전체/미사용 texel binding을 읽은 것은 아니다. bank 원색 확인을 위해 추가 Play나 거대한 Texture readback이 필요한 것은 아니었다.
- `EyeRenderer367.Dispatch`는 단일 templateRGBA/Role를 모든 phase에 바인딩한다. `EyeFeature348.compute:Own`은 role/eye에 맞는 색 texel을 선택하지만 `Classify/CountPacket19/IrisAllocated19`는 그20셀을 전체 눈 shape로 사용하지 않는다. 따라서 **색 bank의 texel 개수4/6을 곧 모든 프레임의 필수 가시 픽셀 예산으로 바꾼 것은 잘못된 전제**다. 기존49의 정수 glyph 이동,52/53의 모든 glyph를 서로 다른 opaque 셀에 남기는 조건을 완전한 원목표로 취급하지 않는다.
- 실제 공동 형상의 기반은 이미 `Full319View335.BindEyes`의 연속 homography와 `EyeCompose333.template262/inside295`의 parent/iris 공유 영역에 있다. 이후348이 별도 normalized Classify와 부위별 top-K로 재선정한다. baseline native line 예외도333 Compose에 있다. 이를 새 독립 팔레트/shape 은행으로 중복 구현할 필요는 없다. 다만 기존 homography의 최종 raster 자체를 시간 안정성/완성 미감으로 승인하지 않는다.
- `EyeFeature348.Initialise/Prepare/BuildLashCurves590`: 저장하는 것은 native topology/rest geometry/closedBoundary와 재사용 sample/record buffer다. source pixel별 전체 눈 keyform/state cache가 아니다. Native upper/lower ring 및 Close morph 기하는52에 있고,590에는 native upper-arc와 기존 두께 규칙이 있다. 그러나 현재73은 UseLashRegion583=false이며 Closed50/100의 등록된 픽셀 keyform은 없다. lower-like feature6은 S0 skin에서도 생성되며 실제 native 하안검으로 승격하지 않는다.52의 native lid2셀은 서로 iris/white와 충돌하는 미채택 source-derived 후보였다.

### 실제 제약 검사와 첫 잘못된 제한

- `joint75.py:hall`: 부위들을 동시에 보는 정확한 capacity/Hall 검사다. 개별 top-K/새 가중치 없이, 선언된 domain과 요구수의 양립 여부만 검사한다. shape/곡률/색 순서까지 통과했다는 뜻은 아니다.
- **조건부 반례:** bank의 iris4/white6을 전부 opaque로 보여야 한다고 요구하면서 현재73 counts>0 셀만 허용하면 양 눈 모두 불가능하다. white 자체가6개 필요하지만 ID2는4셀, ID1은5셀뿐이고 I/W 합집합은 둘 다6셀이다. 이것은 원래 목표의 불가능 증명이 아니라 잘못된 'bank count=가시 budget'와 'counts=원본 domain' 전제의 충돌이다.
- 같은 검사를 과거47의12 eye-frame에 source별 ablation했다. 실제 counts domain0/12 통과, raw source-owner geometry support12/12 통과, Classify를 제거하되 모든 기록 가림을 적용하면0/12, S0만 뺀 감도검사12/12다. 즉 source가 없어서만 못 놓는 것이 아니라 S0 generic skin 처리가 domain을 줄인다. **S0 전체 무시는 채택하지 않는다.** 기존51의 등록 open-aperture underlay 구분을 재사용할 수 있는 부분과 실제 lid/Close 가림을 분리해야 한다. 현재73은4×4 S0~S3 개별 표본이 없어 같은 ablation을 현재 source에서 확정할 수 없다.
- `joint75.layered_identity`: 캐시의 source ID/role/색은 가려져도 남는다. '원본 특징 정체성 보존'과 '모든 reference texel이 매 프레임 전부 가시'는 다르다. 두 source part가 같은 opaque 셀을 요구하는52의(222,52) 반례는 후자의 조건에서 불가능하지만, layered cache의 정체성 자체를 삭제해야 한다는 뜻은 아니다. 부분 가림55를 any(front) 전체 기각으로 되돌리지 않았다.
- `test75.py`:10검사 통과. 공유 셀의 공동 capacity, 순회 독립, source 없음/미등록 state 거절, 가려진 캐시 ID/색 보존, capacity 통과가 상대 형태를 보장하지 않는 반례를 포함한다. 완성 joint RGB 후보를 렌더하거나 원래 state를 임의 생성하지 않았다.

### 중단점과 최소 다음 계약

원본 iris/white bank와 parent/iris 곡선·native 안검 기하는 복원 가능하다. 없는 것은 단일 색 bank를 대신할 **일관된 전체 눈의 현재 상태/공유 경계·가시성 계약**이다. 특히 authored295 opening과 실제 native skin opening이 다를 때 전체 눈을 어느 공통 경계로 변형할지, native 안검의 가림이 intrinsic glyph를 어디까지 자를지 정의돼야 한다. 이것을2/4셀 최소나 임의 점수 가중치로 해결하지 않는다. 설계상 source-cache 정체성은 가려져도 유지하고 최종 가시는 실제 가림으로 결정해야 한다. 기존 bank의 모든 texel 가시를 무조건 강제하는 조건은 폐기 대상이다. 기존 shared parent/iris와 native closedBoundary를 같은 변형/합성 경로로 연결하는 것이 다음 구현 단위이며, 현재 bank를 새로 칠하라는 뜻은 아니다.

추가 관측이 필요하다면 전체재촬영이 아니라 동일 source의 작은 eye ROI에서 **348 Evaluate 대입 전 baseline colour/owner/meta/UV/domain**, S0~S3의4×4 META/POINT/UV 및 S3RGBA/Shade, 외부 가림 S4~S6META, 실제 homography/ray/style/bank asset hash를 대응시켜야 한다. 현재73의 counts는 합계이고 최종 records는 baseline 일부를 덮어써 generic skin/실제 lid의 최초 차이와 full joint colour 합성을 역산할 수 없다. Template 두 asset 자체는 이번에 읽었으므로 다시 대형 readback할 이유가 없다. 현재 입력으로 전체 공동 RGB/회전/blink를 검증했다고 하지 않고 여기서 멈춘다. 새로운 Unity 접근이나 사용자에게 추가 캡처 요청을 보내지 않았다.


## 눈76 — 실제 348 직전 관측, 기존 공동 특징 보존과 안검 예산 계상

실제 적용 파일은 `Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeFeature348.compute`다. `ComposedSource76`은 앞선333/295 공동 parent/iris 합성의 가시 iris/white 및 실제 native eyeline을 현재 S0~S6의 깊이·alpha와 source ID로 확인하여 독립348 top-K가 다른 부위로 덮지 않게 한다. S0 전체를 무시하거나2/4px를 고정하지 않는다. `domain.y`는 eye ID가 아니라 colour-support 값이므로 `_OldEyeOwner.y`를 사용한다. `ComposedPigment76`은333의 직접 texel 우선/동일 role 최근접 색 출처를 기록한다. 이미 합성된 RGB/owner/depth/UV 자체는 Merge에서 재작성하지 않는다. 현재 표본의 UV/primitive/barycentric은 별도 surface/bary 필드에 남긴다.

`CountFeatures19`는48byte packet의 종전 미사용 `uv.z`에 같은 눈의 보존 native line 예약을 표시한다(uv.xy 및 원래 명암/feature counts 불변). `NativeLineAllocated19`는 그 수를 독립 면적 예산에서 차감한다. 이 계상이 없던 중간 후보는 한 눈에 보존 안검+독립 안검을 중복 배정했으므로 채택하지 않았다. 현재 수정은 완성 joint allocator/state bank나 소수 좌표 history cache가 아니다.

실험/재현 경로: `experiments/pixel-pipeline/2026-11-01-whole-eye76/INDEX.html`. `ActualRunner76.cs.txt:Arm76/CameraBegin76/Capture/FrozenOriginal76/Release76`은 실제 deferred Evaluate 직전6×float4를24×16 소유 버퍼에 기록하고 S0~S3 개별4× 표본·외부 가림과 대응시킨다. 기존 알고리즘은 `BaselineProbe76.compute:OriginalEvaluate76`에서 같은 frame/source/view/serial의 동결 입력으로96KiB 소유 record 버퍼에만 재생한다. 원래 전역 buffer/texture는 쓰거나 해제하지 않는다. `ORIGINAL76` 분기에서는 예약 차감도 적용하지 않는다. 이전 Play의 미세한 포즈 차이를 동일 입력 비교로 사용하지 않았다.

검증: actual frame95~100/serial2~7의6연속 프레임에서 보호13셀/프레임(78검사), 같은 입력 대비 변경10셀, 영향 없는 영역의 Evaluate RGB 오차0, bank 경유 sRGB8 오차0. iris8셀은 source에서 나온 결과이며 고정 예산이 아니다. 중복 native line1셀은 매 프레임 제거됐다. `test_archive76.py`는 저장된 실제 compact fixture로 이 조건과16개 표본 인덱스 동치를 재현한다. 원배율·정수 확대 PNG를 직접 검수했다. 전체 PNG는 실제 수정 렌더이고, 같은 프레임 기존/수정 비교의 범위는 eye Evaluate ROI다. 다른 Play의 전체 PNG를 동일 입력 회귀라고 부르지 않는다.

남은 실패: 미보존 쪽 native line이 면적0.5 경계/순위에 반응하여 추가 셀이 남거나 사라진다(현재 native line 총2→1). 현재13셀 보호는 이 전체 눈의 상태/곡선 설계를 해결하지 않는다. 일반 face underlay와 실제 lid/Close 상태의 완전한 공동 경계·변형 계약, 보행/회전/blink 및 실제 subpixel 표면 대응 검증은 미완이다.6프레임의 deltaTime은 매우 짧고 bin0 안의 미세한 실제 입력 변화만 있어 전체 시간 안정성으로 확대하지 않는다. 기존 lower-like S0 shade/머리 영역·팔레트 문제도 미완 그대로다.

원복: PID35364에서 정상 Edit 복귀, GameMap1 clean/기존 dirty29 identity·내용 유지, 옵션 false/None·background false·time/pipeline/global getter 복원, RT30→30. 비교44개는 ExactUTF8이며 PlayerSettings와29 dirty 모두 포함한다. 비dirty ProjectSettings AssetImporter1개는 Play후 객체 부재로 미확인이다. Unity 내부 allocated +32.03MiB는 physical RAM/누수 확정이 아니며 capture-only delta는 약0.00069MiB다. 최종 경고 정리(초기값 명시·유효0..15 인덱스의 동치 bit 연산)는 추가 Play 없이 compute compile/native 비교로 확인했고 신규 정규화 경고·오류는 관측 마지막50개에서0이다. GPU검증 SHA와 경고정리 후 SHA는 `FINAL_COMPILE76.json`에 따로 있다.

로컬 커밋에는 정확한 제품 패치/전후 소스 snapshot, 실제 fixture·검증·진단 asset와 이 인계만 포함한다. 원래 제품 compute에는 이전부터 미커밋 LayerMode19 등의 사용자 변경이 있어 HEAD와 안전하게 분리되지 않는다. 따라서 그 파일 전체를 stage하지 않았다. 실제 작업 트리에는 적용·컴파일되어 있으며 정확한 변경은 `PRODUCT_FINAL76.patch`와 `PATCH_FINAL76.json`으로 보존한다. 관련 커밋은 이 절의 Git 이력이다. CUA/앱 종료/SaveAssets/초기화/push는 하지 않았다.


## Eye77 — 원본 상안검 연결 영역 선택, 실제 제품 부분 적용

코드 색인: `EyeBoundaryRestore348/Shaders/NativeCacheGPU77.hlsl:NativeInit77/NativeSameInput77/NativeRoot77`(12행 부근), `NativeSourceSelection77.hlsl:NativeSample77/NativeVisible77/NativeAllocated77`, `EyeFeature348.compute:CountFeatures19`(141), `LegacyNativeLineAllocated76`(167), `NativeLineAllocated19`(190). 경로 앞에는 `Assets/EUnityValidation01/`을 붙인다. 기준 커밋은84a9c6b이고 이번 절과 실험의 커밋은 `git log -1 -- experiments/pixel-pipeline/2026-11-01-native-eyeline77`로 찾는다.

확정 원인:76 실제 입력에서 S3 전체 가시 면적은0.510→0.449로 내려가 독립 반올림 budget1→0이 된다. 같은 upper source의 primitive46/5도 colour-competition rank에 의해(226,51)→(222,52)로 바뀐다. S0 무시 문제가 아니라 주로 실제 앞머리 가림이다.77은 원본 native 연결 component의 upper/lower를 구별하고, own-skin 이후 intrinsic 면적으로 예산을 정하되 실제 외부 가림 후 가시 표본이 있는 셀만 허용한다. source-rest 중심 오차로 선택하며 iris/white/이미 보존된 native 셀을 덮거나 중복하지 않는다. 최소1/2/4픽셀 고정, 피부 전체 덮기, RGB history/평균, 새 눈 색 생성은 없다. native 원색 자체가 밝은 부분은 그대로다.

W 소유권은 `CACHE_OWNERSHIP77.json`과 전체 Assets 참조12개로 감사했다. instance `restTriangles`의 기존 미사용 W만 명시된 layout으로 사용하고 XYZ는 불변이다. HeadLocal 복제는 NonSerialized 버퍼를 복사하지 않으며 소유자 OnDisable에서 해제한다. Count의 한 스레드만 생산하고 다음 Evaluate dispatch부터 읽는다. count/base/size/centres/axis signature 변경 또는 새 W=0 업로드는 무효화한다. 캐시 지역배열로 생긴 레지스터 한도 경고와 무효 입력 반례는 미채택하고 고쳤다. 최종7개 실제 GPU fixture(별도 instance/반복초기화/무효입력 회복/축변경/재초기화/unknown W/용량 fallback)와 원본 index 기준140삼각형 대응이 통과했다. 현재 adapter 역할 및 정확 rest 위치 welding에 의존한다. 실행 중 sharedMesh만 교체하는 동작은 기존 Initialise부터 미지원이며77이 해결했다고 주장하지 않는다.

실제 입력/검증: `experiments/pixel-pipeline/2026-11-01-native-eyeline77/INDEX.html`. 이전8프레임과 경고 정리 후 최종4프레임은 별도 sourceId다. 각각 동일 프레임의76 GPU replay와77을 비교했다. 상안검은 열린 상태(225,51), 실제 Close 상태(225,53)로 이동하고 최종4프레임 iris는8→0→0→8이다. 반감김은 이전8프레임에서5셀이다. source geometry와 표본 투영 최대오차0.00059px 이하. portable12프레임에서 보존 RGB96건/새 native source 색18건, GPU/오프라인 선택 일치, 안검 외 ROI RGB 변경0이다. 최종 ShaderUtil33메시지를 기존76과 정규화 대조해 새 종류 경고/컴파일 오류0을 확인했다. 외부 getter 보고서의 상대 경로 오류1건은 절대 경로로 수정했고 제품 동작 오류로 숨기지 않았다.

복원: PID35364 Edit/domain1, GameMap1 clean, Assets/ProjectSettings dirty29 identity 및 내용 보존, options false/None/background false/time/pipeline/global 복구. native44/45 ExactUTF8이며 비dirty ProjectSettings AssetImporter1은 unavailable이다. path 없는 Editor Object/SceneVisibilityState 각1개의 raw dirty 증가를 기록했고 소유권 근거 없이 지우지 않았다. RT30→30, 임시 버퍼/셰이더만 해제하고 빌린 참조·morph·afterPose를 복원했다. 최종 Unity 내부 allocated+32.18MiB/capture-only 약0.00125MiB는 물리 RAM/누수 확정이 아니다. C# Assets import/recompile, SaveAssets, CUA, 종료/reset/push는 없었다.

미완: 전체 눈 joint shape/state bank, 곡선 전체와 소수 좌표의 연속 이동, 긴 회전/보행/모든 모델 미관은 해결·검증하지 않았다. 원배율/확대 PNG를 직접 봤지만 거친 눈 모양은 남아 있다. 기존 user LayerMode19 선행 변경 때문에 전체 main compute 함수는 HEAD에 독립 적용 불가하므로 통째로 stage하지 않는다. 새 helper 실제 경로6파일과 분리 가능한 RW 선언 hunk만 선택 보존하며, 정확한 전체 작업 source/전후 snapshot/PRODUCT77.patch/컴팩트 실제 fixture는 위 실험에 남긴다. user 기존29개 다른 tracked 파일 해시는 불변이다.


## Eye78 — 움직임 관찰기 입력 수명 사고, 제품77 유지/유효 캡처0

`experiments/pixel-pipeline/2026-11-01-motion-input78/INDEX.html`에 사고와 복구 근거를 보존한다. Play1회, 준비 중 실제 입력0으로 첫 캡처 전에 중단했다. 원래 임시 InputSettings를 clone으로 교체하면 InputManager.settings setter가 이전 HideAndDontSave 객체를 파괴한다는 계약을 놓쳐 원래 참조로 복원하지 못했다. 현재 InputSettings는 관리 참조가 있으나 native 객체가 파괴돼 Unity bool=false, loaded settings0이다. 공개 getter/JsonUtility의 관리 데이터22필드는 남아 있으며 `INPUT_SETTINGS_RECOVERED78.json` SHA ca3f68bea248d3f95f9daef0889228a710740dd1efc8867ffda63b97b07f4286으로 외부 보존했다. Unity 종료의 JSON overwrite/backup clear 코드와 시험 값이0/0으로 돌아온 관리 필드를 대조했으며 기본값을 추정한 것이 아니다. 원래 native identity 및 비직렬화 feature flags는 복원을 보장하지 않는다. 실제 UI 입력 동작은 검증하지 않았다.

현재 읽기 조사 단계로 새 설정 생성/연결·초기화·재시작·추가Play는 실행하지 않았다. 최소안은 이 실제 JSON으로 새 InputSettings native 객체를 채운 뒤22필드 roundtrip을 확인하고 public setter로 연결하는 것이다. 채택되면 InputManager의 임시 객체 소유권을 따르며 활성 참조를 Destroy하면 안 된다. SerializedObject로 읽은 domain backup은 이미 빈 문자열이었고 Reflection/내부 reset은 사용하지 않았다.

`MotionScope78.FAILED.cs:Start/Dispose`와 실패 runner는 당시 코드이다. `MotionScope78.cs`는 **미컴파일·미실행 제안**이며 설정 포인터를 교체하지 않고 외부 JSON을 먼저 저장한 뒤 transient 두 필드만 바꿔 복원한다. 입력은 queue만 하고 정상 Dynamic update를 기다린다. 기존 Editor callback에서의 `InputSystem.Update()`가 Editor 상태에 이벤트를 소비했을 가능성은 source에 근거한 가설이며 아직 재검증하지 않았다. 복구 확인 전 이 제안을 실행하지 않는다.

자산/씬/기타 옵션은 별도 대조했다: PID35364 Edit/domain1, 사용자 dirty29 identity 동일, native44/45 exact(비dirty Importer1 unavailable), globals 복구, options false/None/background false/time/pipeline 동일, RT30→30, 임시 장치/관찰기 자원 해제와 실제 product rest buffer 미교체 확인. 프로젝트 tracked30 해시는 모두 불변이다. 따라서 입력 native 상태 사고를 다른 상태 보존이나 움직임 품질 성공으로 감추지 않는다.


## Eye79 — 실제 회수22필드로 InputSettings native 객체 복구 완료

현재 상태는78의 복구 대기에서 **복구 연결·검증 완료**로 바뀌었다. `experiments/pixel-pipeline/2026-11-01-input-recovery79/INDEX.html` 및 `VALIDATION79.json`이 근거다. `Restore79.cs:Execute`는 손상된 관리 참조/Json을 static `InputRecoveryAnchor79`와 외부 파일에 먼저 보존하고, 새 비자산 InputSettings에 실제22필드 payload(SHA ca3f68bea248d3f95f9daef0889228a710740dd1efc8867ffda63b97b07f4286)를 overwrite했다. 연결 전 exact roundtrip 통과 뒤 public setter로 연결했으며 별도 `Verify79.cs:Execute` 조회에서도 같은 새native ID/동일22필드를 확인했다. 활성 객체는 임의 Destroy하지 않고 InputManager의 HideAndDontSave 임시 소유권을 따른다. 기본값 추정·InputSystem.Reset·Play·재시작·SaveAssets·C# Assets import·private Reflection은 없었다.

복구 전후 native45/45 ExactUTF8, 사용자 dirty29 identity/내용, GameMap1 clean/Edit/domain1, options false/None/background false/time/pipeline, device IDs/layouts/current Keyboard가 동일하다. 프로젝트 기존30 tracked 파일 해시도 불변이다. 이번79에는 RT 전후 counter를 별도 기록하지 않았고 RenderTexture API는 호출하지 않았다(78의 RT30→30과 구분). 원래 파괴된 객체 ID는 되살리지 못하며 새객체로 직렬화내용을 복구한 것이다. m_FeatureFlags는 NonSerialized/internal이고 전체 공개 getter가 없어 원래flags 복원을 보장하지 않는다. 공개 useIMGUIEditorForAssets 복합값은 전후false였지만 전체flag 증거로 확대하지 않았고 flags를 추정설정하지 않았다. 실제 OS/UI/게임 입력 정상 동작·움직임은 이 turn에서 검증하지 않았다.

`NEXT_INPUT_PLAN79.json`은 미실행 계획이다. 설정 포인터 교체/clone/Destroy 없이 외부 전체JSON과 두임시값을 먼저 보존한 뒤 같은 transient 객체의 필드만 되돌린다. Editor callback에서 InputSystem.Update를 수동 호출하지 않고 정상 Dynamic update로 queue를 소비하게 한다. 우선3프레임의 가상장치 key/enabled/current·실제 action input/active device·PlayerMovement/Animator/render serial 및 복원을 확인한다. 불일치하면 즉시 원복하고 전체24프레임 눈 readback으로 진행하지 않는다. 입력연결과 원복이 입증되기 전에는 회전/보행 안정화 성공을 주장하지 않는다.

## Eye80–82 — 설정 교체 없는 입력 smoke 통과, 실제 눈 움직임 캡처는 차단

`experiments/pixel-pipeline/2026-11-01-input-smoke80-motion82/INDEX.html`과 `VALIDATION80_82.json`이 최신 근거다. 제품 working tree77은 유지하며 이번에 제품/Assets를 변경하지 않았다. `Smoke80.cs:StartInput/Queue/AfterInput/Tick`은 실제 action의 keyboard binding을 찾아 정상 Dynamic update로 전달했다. Up/Right/Release를 두 번 반복한12프레임에서 요청/실제 action, 이동 방향, 회전 반응이 일치했다. 이동량 최대오차5.96e-8m, 방향 내적 최솟값1, release 수평이동0. 이는 입력 전달 검증이며 눈 형상/시간 안정성 검증이 아니다.

`FAILED_TESTED_MotionScope81.cs:Start/Ready/Snapshot` 및 `FAILED_TESTED_Capture81.cs:Arm76/Tick`은 기존 pose에 가장 가까운 Down/S를 queue했으나 준비5프레임 동안 실제입력0이었다. `FAILED_TESTED_Capture82Fixed.cs`는 관찰기 pause를 제거하고 `MotionScope82:AfterInput82`에서 Dynamic을 직접 관측했지만6프레임 모두 장치 enabled/current, S key=false/action0이었다. 따라서 pause가 원인이라는 가설은 충분하지 않다. 첫 유효 이미지 전에 두 시도를 정상 종료했으며 새 유효 PNG/eye packet은0이다. queue event가 수신됐는지와 reset/시간 원인은 미관측이다. `PREPARED_ONLY_InputEventProbe83.cs`는 소유장치의 event timestamp/type·device change·Dynamic 전후를 기록하는 다음 최소 관측안이며 **미컴파일·미실행**이다. 설정/장치 종류를 추정 변경하거나 timeout을 늘리며 반복하지 않았다.

세 Play 모두 `InputSystem.settings` 포인터를 교체·clone·Destroy하지 않았다. 같은 native ID568105589213679894, 전체22필드 SHA ca3f68bea248d3f95f9daef0889228a710740dd1efc8867ffda63b97b07f4286, hideFlags/객체수1/장치/현재Keyboard/바인딩/옵션/time/pipeline/globals를 복원했다. 사용자 dirty29와 자산45개 직렬화내용은 별도 getter 대조에서 모두 exact, scene clean/Edit/domain1, RT30→30이다. 즉시 비교에서 PlayerSettings1개가 일시 unavailable이었으나 별도 getter 뒤45/45를 확인했다. 81/82의 속도·Animator·임시 device도 회수했다. 원래79의 비직렬화flags/원래파괴된native identity 한계는 그대로다.

검증기 오류도 구분한다. Verify80은 JSON wrapper cast로 읽기 비교 전에 실패했고 VerifyContent80에서 명시적 행 변환으로 수정·통과했다. 첫 Capture82는 출력 디렉터리 치환 오류로 첫 CreateNew에서 실패해 Play0회였다. 기존실패소스를 보존한 Capture82Fixed가 실제82의 Play1회를 수행했다. 복구 성공이나 입력 smoke 통과를 이미지 회귀 성공으로 바꾸지 않는다. 관련 commit은 이 절을 추가한 commit(`git log -1 --format=%H -- docs/ai/PIXEL_ALBEDO_20261030.md`)으로 찾을 수 있다.

## Eye83–85 — 입력 관찰기 원인 수정 완료, 실제77 움직임24프레임과 잔여 실패

최신 자료는 `experiments/pixel-pipeline/2026-11-01-input-routing83-motion85/INDEX.html`이다. **제품77/Assets는 이번에 변경하지 않았다.** 외부 `MotionScope:Start`의 `editorInputBehaviorInPlayMode` 대입을 감싼 `#if UNITY_EDITOR`가 원인이었다. 실제 동적 컴파일 심볼은 false(`SOURCE_SYMBOL83.json`)라 그 대입만 제거됐고,83의 같은 W 이벤트는 Dynamic 뒤 Editor에서 수신돼 게임 action0이었다. `FIXED_MotionScope83.cs:Start`는 guard만 제거했다. 같은12프레임 W/D/release의84는 모든 이벤트가 Dynamic에 도착하고 actual action이 일치했다. 전환 때만 queue해도 유지되므로 매프레임 재전송/추정 reset/새 설정이 해법이 아니다. 현재 workspace의 미적용 제안 `eye-motion78/MotionScope78.cs`도 같은 guard를 제거했으며 과거 archive는 보존했다.

`TESTED_Capture85.cs:Tick/Capture/Finish`, `TESTED_MotionScope82.cs:Start/Dispose`로 정상 PlayerMovement/Animator/Gameplay397.Present의 실제6 이동/8 보행/10 회전 프레임을 확보했다. history reset0, 동일 프레임 header/serial/원본 geometry·camera·4x source/owner/depth/눈 records를 대조했다. `validate_motion85.py`의 source77 GPU/CPU 배치가24프레임 일치했고 보호RGB233개를 보존했다. `source_trace85.py` 신규 안검19픽셀은 실제S3색과 기존shade.z의 결과/UV provenance가 일치한다. 새 색 합성이나 제품 팔레트 변경이 아니다. `inspect_motion85.py`는 native primitive 대응을 써 source 재투영 최대오차0.000626px를 확인했다. 테스트 후 설정 같은 native ID/22값, 장치/옵션/time/pipeline/globals, 사용자dirty29·자산45내용, Edit/scene clean, RT30→30을 확인했다. 내부 total allocated는약36.97MiB 감소했으나 물리RAM/누수 판단으로 확대하지 않는다.

**잔여 실패와 범위:** 짧은 보행의 위 안검은 각 눈1셀을 유지했지만 홍채는2~4셀로 변한다.118→119 eye1은4→2이며 Close morph0/iris budget2가 동일한데 보존된 pre348 홍채 footprint가 바뀐다. 같은 프레임 frozen76/77의 홍채 shape는24프레임 모두 같으므로 이번77의 신규 회귀로 오인하지 않는다. 전체 눈 cluster 보정은 여전히 미완이다.6 이동 프레임의 feature/eye label은 동일하나 카메라 추적으로 표시위상 span은0.000168셀 정도뿐이다. 따라서 전0..1픽셀 phase sweep을 검증하지 못했다. RGB도 잔류한다: eye record 최대5, 머리/목 최대34채널 차이가 있고 후자는348 이전에도 동일하게 존재한다(`SOURCE_TRACE85.json`의(216,66) 등). 회전 중 소실은 실제방향·가시량과 함께 변해 셀 수만으로 flicker/정당한 가림을 단정하지 않았다.

원배율/nearest PNG와 stage별 느린GIF를 직접 확인했다.8 warmup 미관측 프레임을 사이에 둔 세 segment이지 전체 uninterrupted24프레임 주행이나 긴 보행주기/모든 blink/state 검증이 아니다.123개 원자료/코드/그림과 추가 portable test를 선별 보존하며 실제24프레임 arrays는 무손실 npz, geometry/camera/완료 marker는zip으로 보관했다. 관찰기 초기 컴파일 생성 오류는 실행 전에 수정했고83 실패·84 통과·85 실제 캡처를 구분한다. 변경 commit은 이 절을 추가한 local commit으로 찾는다. 다음 원인 대상은 관찰기 입력이 아니라 pre348 특징 footprint/색 선택이며, 아직 전체 미감·시간안정화 성공으로 판정하지 않는다.


## Eye86·87 — 원본 윤곽/조명 출처 분리, 캐시 nearest 후보 미채택

최신 비교는 `experiments/pixel-pipeline/2026-11-01-feature-provenance86-cached-role87/INDEX.html`이다. 제품 기본값은77 유지. 이번 Assets 변경은 **기본 경로에서 참조하지 않는** `EyeBoundaryRestore348/Shaders/CachedSourceRole87.compute:template262`와 meta뿐이다. 원래 `GameMapIntegration333/Shaders/EyeCompose333.compute` 및 기존30개 tracked 변경의 실행 전 해시는 불변이다. 이번 커밋은 `git log -1 --format=%H -- experiments/pixel-pipeline/2026-11-01-feature-provenance86-cached-role87`로 찾는다.

`audit86.py:classify/local`은 실제85의118→119 eye1 손실을 분리했다. (222,52)는 source contour의 q=(220.4523,78.5509)→(220.4044,78.5417)로 경계를 넘어 iris→sclera가 된다. (223,52)는 iris 안이지만 실제 native 안검 우선 처리로 반환된다. 두 셀을 모두 잡음으로 고정하면 실제 가림을 지운다. 새86의24프레임은 원본 parent/iris SHA와 실제 canonical sample(.75,.25), material 원색·UV·primitive/물리 입력/LegacyClass를 기록했다. (216,66)은 같은 primitive1694·UV에서 scalar .489164→.510612가 .5를 넘으며 기존 LegacyColour가 .72*source→source를 선택한다. `RestoreStyle335` layered 분기의 입력이며 `Prepare333` 이전 색·팔레트 자체 변조나 HSV 채도 변화로 입증된 것이 아니다. 이 기존 곱셈 경로를 새 유한 팔레트 계약으로 고쳤다고 주장하지 않는다.

`ComposeComparison87:Calibrate/ReplayOriginal/Install/Dispose`는 기존333을 빌린 입력+전용4RT에 재생해 색/owner/intrinsic/audit 차이0인 것을 확인한 뒤 런타임 shader 참조만 후보로 바꿨다. 후보는 이미 연결된 TemplateRole의 floor(q)에서 role/owner를 읽어 같은 텍셀의 색과 대응시킨다. 새 크기 상수·임의 이동·색 보정·가림 무시는 없다. `TESTED_Capture87:Capture`, `TESTED_MotionScope87:BeginSweep86/BeginBlink87/Dispose`로 이동6·보행8·실제 상대 위상10·Close5, 총29프레임을 정상 history 경로로 관측했다. source role GPU/CPU 불일치0, 직접 source RGB8 509셀 일치,76 보호 RGB339셀 일치. 두 가지 다른 합성 bank의 role/owner와 범위 밖 반환도 검증했다.

**미채택 반례:** `trace87.py:local_grid/shape` 및 `TRACE87.json`에서 동일 evaluated mesh의 실제 상대 위상은 .99997944셀, Y 변화 .0000432셀, 원위치 오차0이다. 가림 전 cached iris도 eye2 4↔6셀/2종 형태, eye1 3~5셀/5종 형태로 변한다. 원본 색·역할 캐시를 연결해도 개별 화면 셀 nearest 재표본만으로 작은 중요 특징의 공동 형태는 보존되지 않는다. 기존43/53과 달리 실제 projection/가림 입력에서 이 실패를 확인했다. 최소 픽셀 수를 강제하거나 native 안검을 무시해 통과시키지 않았다. 다음 범위는 source 이미지 셀의 공동 배치/연속 변형과 부분 가림을 함께 평가하는 것이며, 이 nearest 후보를 성공 경로로 활성화하면 안 된다.

조명 관측87에서 실제 `SkyLightingCycleController.CurrentHour`21.5238→21.7771, auto=true, 태양 방향12종을 확인했다. 물리 조명이 변하는 장면이므로 모든 명암 단계 전환을 원인 없는 raster flicker로 취급할 수 없다. 광원·명암 분류·출력색 선택을 별도 기록했고 조명/팔레트/threshold는 바꾸지 않았다. Close getter0/50/100/100/0와 실제 평가 메쉬는1프레임 늦게 대응했다. 실제 닫힌137·138에 열린 iris를 강제 복원하지 않았으나, 재개방 평가 완료 프레임이 없어 완전한 blink 회귀 통과는 아니다. 최종348/native는 실제 후보 출력이고 기존333과 후보333만 동일 프레임 쌍이다. 기존348 전체 paired 비교로 부풀리지 않는다.

`analyse87.py:main`, `test_archive87.py:run`은 완료 marker와1885개 plane의 source/frame/serial/view·원본 role/RGB·76 guard를 검증했다. RAW_MANIFEST planes 리스트가 한 프레임 이전 객체를 참조한 exporter 결함은 발견 그대로 보존했다. binary 헤더는 모두 해당 프레임과 일치한다. `prepare87.py`에 packet commit 직전 `report["planes"]=planes` 수정만 준비했으며 기존 raw나 실행된 소스를 덮어쓰지 않았다. raw86/87.zip과 독립 오프라인 재검사, 원배율/nearest PNG·실제 시퀀스 GIF를 보관했다. 미관/전체 움직임 안정화 성공 주장은 없다.

두 시험 종료 후 Edit/GameMap1 clean/domain1, 원래29 dirty identity/내용, native45/45 ExactUTF8, 같은 InputSettings ID568105589213679894·22필드 SHA ca3f68bea248d3f95f9daef0889228a710740dd1efc8867ffda63b97b07f4286·장치, 카메라/후크/옵션/time/pipeline/global74를 보존했다.87 자체 자원과 shader 참조 원복, RT30→30. GetTotalAllocatedMemoryLong +33.62MiB는 내부 할당 측정이며 물리RAM/누수 확정이 아니다. 제한된 최근 Console 비교에서 신규 warning/error는 없었다. CUA/설정 포인터 교체/SaveAssets/GC/C# import/삭제/초기화/push는 수행하지 않았다.


## Eye88 — 특징 로컬 coverage 캐시와 연속 앵커, 격리 GPU 검증

최신 비교: `experiments/pixel-pipeline/2026-11-01-feature-local88/INDEX.html`. **제품77 유지, 전체 눈/가림/최종 합성 미통합.** 새 Assets 변경은 기본 경로에서 참조하지 않는 `EyeBoundaryRestore348/Shaders/FeatureLayer88.compute:Draw`와 meta뿐이다. 현재 커밋은 이 실험 경로의 `git log -1 --format=%H -- <path>`로 찾는다. 원래30개 사용자/product tracked 해시는 불변이다.

`feature_layer88.py:FeatureCache.update/project/cell_area`는 원본 Template216의 parent/iris/sclera20픽셀 영역을 pose homography로 forward 투영하고 공통 anchor를 뺀 로컬 격자에 coverage로 배치한다. foreground/part coverage로 점유를 선택하고 해당 part 최대 기여 source 텍셀의 P 인덱스를 보존한다. RGB 평균이나 매 프레임 화면 centre-nearest로 역할을 다시 결정하지 않는다. 이 coverage convention은 유일한 미술 정답의 증명이 아니다. 동률·다른 owner 겹침·소스 part 소실은 임의 선택 대신 Unsupported다. source bank20텍셀 수를 가시 셀 수로 강제하지 않는다(실제 sweep pose 로컬25셀, native2x100표본).

`FeatureCache.update/invalidate/dispose`, `raster`는 canonical support/파트/P 인덱스와 연속 anchor를 분리한다. 순수 이동은 anchor만 바꾸고 source/모델/뷰/state 및 실제 비이동 투영변형은 캐시를 무효화한다. float32 좌표 크기에서 유도한 수치 허용오차만 사용한다. caller가 검증된 evaluated-state/원본 key를 공급해야 하며, 이 연결은 제품에 없다. 미등록 Close는 열린 form으로 대체하지 않는다. cache는 renderer/view 소유1개이고 static 공유/화면 RGB history가 없다. 다중뷰/모델교체/이중 dispose는 pure helper 반례를 검사한 것이며 실제 복수 런타임 renderer 수명 검증은 아니다.

`replay88.py:canonical/rays/depth_at/main`, `test88.py:main`은 실제87의 열린 입력24프레임과 합성17×17=289위상을 사용했다. 실제 .99997944셀 sweep10프레임에서 canonical part/색 관계 서명1종·native intrinsic100표본이며 반복 이동으로 재생성하지 않는다. 실제 포즈 변화는 재생성한다. 최종2x native 래스터 이전 anchor는 소수 좌표로 보존한다. 유한2x 출력에서0.1셀마다 새 위치가 보인다는 주장은 하지 않는다.49 정수이동 한계,53 any(front) 전체기각,74 iris 독립선택에 의한 다른part 침범,87 화면 nearest 면적변화에 대한22개 회귀를 기록했다. 과거53/55의 실제 destination4x mask에서 앞선 일부 fragment 때문에 전체를 기각하지 않았으나, 잔여 표본 면적을 최종 셀 채택 보장으로 해석하지 않는다.74의 전체 과거 최종RGB 재합성이 아니라 공동 occupancy의 구조적 회귀다.

`FeatureLayer88.compute:Draw`, `GPU88.cs:Execute`는 explicit Vector4/16B 버퍼와 자체3RT에 저장 실제24입력을 재생했다. `validate_gpu88.py:main`, portable `test_saved88.py:run`에서 source support 재생성24개·GPU 색/ID/coverage72필드 차이0. palette는 literal P[index], g를 RGB에 곱하거나 RGB/시간 평균하지 않는다. canonical palette 변경과 support 불변도 검사했다. alpha는 별도 가시량 계측이며 일반 alpha blend를 실행하지 않았다. 이 레이어를 그대로 blend하여 P 밖 색을 만들면 계약 위반이다. `OUTPUT_CONTRACT88.json`이 source층/coverage/미구현 최종 합성을 구분한다.

**남은 실패:** `VISIBILITY_TRACE88.json`에서 같은 canonical(4,-1),owner1/iris/P7가 유지되지만 head sample(224.75,51.75)의 S3 native안검 alpha0→.996078로 가시량1→.003922가 된다. 가시량 양수 native 표본은 sweep에서37/36/33/40…개로 변한다. 이 수치는 실제 최종 채택 셀 수가 아니다. 가림전 RGB와 coverage 그림을 따로 보아야 하며 거의 가려진 RGB를 밝은 최종 눈으로 표시하지 않는다. source4x sampling·최종 표본 위치·가상 authored 눈 평면과 실제 native 피부/안검의 대응이 아직 분리되지 않았다. 재구성 ray/가상평면은 actual333 depth 최대오차3.53e-6로 일치하지만 실제 mesh 표면 대응의 증명은 아니다. 피부를 통째로 무시하거나 모든 face를 실제 lid로 가정하지 않았다.

다음 제품 연결 전에 authored parent/iris와 실제 native 안검/aperture를 같은 feature-local frame에 묶는 source 대응, 원본 눈 제거/실제 clean backing, 최종 palette-exact owner 선택이 필요하다. 현재 native 안검은 별도 관측 가림층으로 유지하며 새 canonical lid key-form을 만들었다고 하지 않는다. 다른 가림 객체의 실제 변형/material alpha까지 확인된 키 없이 가림을 캐시/동결하면 안 된다. Close/reopen와 실제 scene 연속 적용·미관 성공은 미검증이다. 추가 미술 형태나 pixel-size 상수는 선택하지 않았다.

실행은 Edit에서 Play0/global변경0, C# Assets import0이었다. 처음 using 번들 형식 오류는 미실행, 이어 Interop namespace 금지는 해당 기능과 struct 전송을 제거하고 표준 Vector4 배열 경로로 변경했다. 보안 설정은 변경하지 않았다. 새 compute import messages0/domain1, native45/45, dirty29/동일 InputSettings 객체·22개 값/장치·씬·옵션·시간·pipeline 보존, RT30→30. 소유buffer/RT/clone은 finally 회수하고 빌린 자원은 해제하지 않는다. 입력mask최대163840B/readback11232B, 내부allocated −.0555MiB는 물리RAM/누수 증명이 아니다. 현재 실행 대기/차단은 없고 제품 기본 경로는 바꾸지 않았다.

## Eye89 — native 대응·공동 가림 격리 검증, 미채택

최신 비교는 `experiments/pixel-pipeline/2026-11-01-native-authored89/INDEX.html`이다. **제품77 유지.** 기본 경로에 연결하지 않은 `NativeSurface89.shader`, `NativeSkin89.shader`, `FinalPalette89.compute:Fill` 및 meta만 Assets에 추가했다. 해당 실험 경로의 `git log -1 --format=%H -- <path>`가 이번 커밋이다. 기존30개 tracked 변경과 추가2개 shader의 디스크 해시32개는 불변이다. source52의 material/submesh/feature-ID 계약에 의존하며 임의 모델 자동 대응 완성을 주장하지 않는다.

`code/registration89.py:main`, `NativeRetarget89:F/Forward/Calibrate/Render/Dispose`가 원본 native aperture24정점과 authored parent의 3D→2D 대응을 검사한다. 두 눈 각각48개 cyclic/reverse 대응을 비교했고 현재 rest 경계 최대오차4.1086e-5px, bank20셀 모두 단일 native triangle/barycentric/UV로 대응했다. 이는 새로 검증한 기하 규칙이며 원래 제작 의도·bank 색의 native UV 출처를 복원한 증거는 아니다. 초기 nearest22셀 draft는 미사용이다. 후보의 잘못된 특이4×4 역행렬과 Json58→float의 정수 경유 반올림을 수정했다. 실제58개 행렬 왕복오차8.6e-14 이하, 분수값 회귀를 확인했다. 사용자 제품 코드를 고친 것은 아니다.

`Capture89F:CameraEnd89/Capture/Release76`, `MotionScope89:BeginSweep86/BeginBlink87/Dispose`로 정상 history의 phase6/walk8/상대위상10/Close8, 실제32프레임을 확보했다. A~E는 잘못된 수치 또는 source 대조에서 캡처 전 중단했고 복원했다. F의 native RGBA/meta/rest/UV와 quantized shade/factor 대조는 차이0이나 **continuous shade 최대차.0668289가 남아 채택 차단**이다. 원본 SV_Position/Y부호/같은 head카메라 콜백으로도 제거되지 않았으며 SH 누락 등으로 원인을 확정하지 않았다. 기하 관측을 별도 조건으로 진행했음을 `CONTROL_STAGES89.json`에 보존한다. 기본 shader 참조를 후보로 바꾸지 않았다.

`analyse89.py:geometry/visibility/joint`, `validate89.py:main/synthetic`에서 실제 bank11714표본 RGB8 오차0,76/77 보호368셀의 source predicate·baseline/final RGB 일치,1.000092px 상대위상10프레임 canonical part/owner 및 bank RGB 형태 서명1종을 확인했다. 깊이·원본 source geometry와 canonical raster 대응을 검사했다. Close getter와 evaluated mesh의1프레임 차이를 유지하여 열린/반닫힘/완전닫힘/실제 재개방을 구분했다. raw coupled iris/sclera는 닫힘0/0, 재개방 시 원래 geometry로 돌아온다. 그러나 최종 source-visible 후보는 완전닫힘에 미확정 흰자 조각이 남으므로 blink 최종 합격이 아니다.88의22개 assertion은 원래 보고서를 덮어쓰지 않고 새 report로 재검사했다.49/53/74/87 전체 과거 합성을 다시 통과시켰다는 뜻은 아니다.

**실패 원인과 다음 경계:** 전체 native skin을 함께 warp하면 서로 다른 source 지점이 겹쳐 가짜 가림을 만들 수 있다. 잔여 coverage 양수만으로 셀을 채우면 native line이 과장된다. backing 점유와 경쟁시키며, 인접4×표본의 깊이를 query 깊이로 사용해 곡면이 자신을 가리는 오프라인 오류도 수정했다. 선택된 이웃 삼각형이 query를 포함하지 않으면 미정이다. 현재 hair/body는 selected primitive/UV/alpha 없이 meta만 있고 vacated cell의 실제 backing도 일부 없다. 무시·주변색 추정·피부 전체 제거로 통과시키지 않는다. 정확한 source query ray의 alpha/owner와 clean backing 연결 전 최종 채택 불가다. Native material alpha가 bank branch 전에 평가되는 제한도 남아 있다.

`build_final89.py`, `FinalGPU89:Execute`, `FinalPalette89.compute:Fill`, `finalize89.py`는 실제32입력×2후보를 **오프라인 공동 판정 후 별도 Edit GPU LUT 합성**으로 검사했다.192필드 float 차이0, 선택범위의 팔레트 밖 색0·범위밖/보호/foreground 색 변경0이다. 이는 upstream 정답 검증이 아니다.64재생 누적 미확정1148 native pixels(가시성924/backing224)가 남는다. 분홍색은 독립 debug overlay이며 P 출력색이 아니다. 원배율/nearest PNG와 실제 시퀀스·source/owner/색·실패 수치를 같이 보존했고 개선/전체 시간안정화로 판정하지 않았다. `test_archive89.py`는 원본 프로젝트 없이 raw32 marker/plane identity와64입력/192GPU출력을 압축에서 재검사한다.

종료 후 Edit/scene clean/domain1, 같은 InputSettings ID568105589213679894·22필드·장치, 옵션/pipeline/time/global74를 복원했다. 현재 dirty31과 native47/47 내용 동일. 기존29와 초기 isolated shader import 이후 추가2(CommonSurface329.shader/DeskLivePixelProbe.shader)의 내용도 각각 비교했으나 추가2의 pre-import memory backup은 없어 생성 원인은 미확정이다. Save/ClearDirty로 숨기지 않았다. RT30→30, Play 내부allocated +57.20MiB/GPU 재생 −.0938MiB는 물리RAM·누수 확정이 아니다. 최종 OS 관측은 PID35364 응답 정상·WorkingSet64 3318587392B(공유 포함 working set)·PrivateMemorySize64 7192408064B(private commit), 전후 물리증가 측정은 없다. 실제 움직임·최종 미관 및 product 통합은 미완이다. CUA/InputSettings 교체/C# Assets import/저장/삭제/초기화/강제GC/push는 하지 않았다.

## Eye90 — 완전 Close 흰자 한 셀의 실제 ray/alpha 원인 수정, 제품77 유지

최신 비교는 `experiments/pixel-pipeline/2026-11-01-eye-close90/INDEX.html`이다. 관련 커밋은 `git log -1 --format=%H -- experiments/pixel-pipeline/2026-11-01-eye-close90`로 찾는다. 이전 원본32프레임/89 산출물은 409a6dbca90adf21b34c8ed5c926a83970ffec47 그대로다. 이번 제품/Assets 변경·Play·새 캡처는0이며 격리 Edit GPU 저장입력 재생1회만 수행했다. 현재 제품은77이다.

`surface_query90.py:ProjectedSurface.hits/visibility_bounds/choose_joint_bounds`, `close_candidate90.py:main`은 frame140의 canonical 셀(5,0)/raster(13,5)를 추적한다. 흰자344의 실제 query(226.373051,52.569766)에서 nearest4x의 피부3120은 ray를 포함하지 않고, 실제 앞 피부3116은 depth13.73193354로 흰자13.74600601보다0.01407247 앞이다. `ReadAlpha90:Execute`는 실제 원본 모델 해시·재질/UV·mip1/Bilinear/aniso1과46 UV의230 공개 getter를 확인했고 해당 alpha는1이었다. 89 visibility의 unknown을 scalar joint가 무시해 내부 흰자 선택을 남긴 것이 최초 손실이다. 이전89 final validity는 이미 그 출력을 미확정으로 세었으므로 성공으로 둔 픽셀을 새로 발견했다고 설명하지 않는다. 원본 shape/색을 바꾸지 않고 실제 ray/alpha의 가림과 unknown 구간을 전달한다. source 없는 새 색이나 Close 기반 삭제 규칙은 없다.

`build_focus90.py:main`, `FocusGPU90:Execute`, 기존 `FinalPalette89.compute:Fill`, `validate_gpu90.py:main`은 그 셀만 false-white 선택에서 제외하여 원래 native 피부를 통과시킨다. 최종 head(226,53)의4 native pixels가 #FFFFFF→원래 #B77F71, 대상 밖 변경0, GPU3필드 float 오차0, 선택된 P 밖 색0, alpha 변화0이다. 원래 owner/depth는 baseline pass-through이며 selector0을 새로운 owner0으로 해석하면 안 된다. 89의 다른 미확정56 native pixels는 그대로다. frame140/141 실제 닫힌 메쉬의 흰자 상한0, getter가0인141도 같은 결과이며 실제 재개방142는 open135의 범위로 복귀한다. 열린 눈/안검 전체와 시간 안정성 통과를 뜻하지 않는다. 원배율/nearest 확대 PNG를 직접 검수했다. `test90.py` 15반례와 `test_archive90.py` 작은 독립 기하 witness/GPU packet 검사가 통과했다.

`metadata90.py:decode_independent_meta/clean_skin_underlay`, `backing90.py:main/inspect_cell`은89 분석의 role 오독을 수정했다. Independent333.y=role+1이므로 encoded4는 skin3이다. 과거 backing 부재224 native 표본 중128은 잘못 제외한 실제 피부,96은 Base/Backing에 여전히 없다(32프레임×2후보 누적; 고유 셀 수 아님). frame140 ray-visible의 관련9셀은5셀 기존 피부 있음/4셀 없음이다. 남은 head(217,52),(217,53),(218,52),(218,53)은 현재 S0가16 opaque skin 표본인데 cached original-full은 iris/반투명 eye다. `FullFeature367.Eyes.RecordRenderGraph`의 ph.face/nativeFace/backing과 `Full319View335.PrepareCurrent`의16 phase cache는 현재 Close 변형으로 갱신되지 않는다. 348 전 baseline은333 눈 합성 이후라 clean backing이 아니다. 현재4x 피부색은 있어도 목표 raster의 typed skin/안검 owner·depth 공급으로 연결되지 않았으므로 평균/추정 채움을 하지 않았다. 후속은 이 current-deformed typed backing 연결과 query 가시성의 생산 경로이며, 이번 한 셀 해결을 whole-eye 채택으로 확대하지 않는다.

`evidence90.py:main`/`SHADE_AUDIT90.json`은 continuous g 최대차0.0668288618을 별도 미해결로 남긴다. `FaceSceneLight335:ContinuousSurfaceLight335/AccumulateSurfaceLight335`는 SH ambient와 광원별 lit/available을 합산한다. normal 생성은 VFACE/TBN/normal map이며 viewDir를 직접 쓰지 않는다. 원본/clone RGBA/meta/rest/UV·Q·factor가 같아도 g는 다르다. calibration max의 실제 sample index/paired GPU 입력이 저장되지 않았으므로 뒤의frame140을 같은 표본으로 대체하지 않는다. 최소 다음 관측은 새 sourceId의 동일 S3 sample/serial/primitive/UV, normalWS/TBN/VFACE, SH, main/additional light 항과 screenUV·lit/available이다. SH나 노출 원인으로 단정하거나 RGB 보정을 하지 않았다.

PID35364 Edit/domain1/scene clean, InputSettings native ID568105589213679894/22필드·옵션·dirty 전체 목록 전후 동일, scoped Assets/ProjectSettings dirty31 보존. pure own GPU replay RT30→30,3 RT/3 buffer/clone 해제, globals 쓰기0, Console 신규 차이0이다. 내부 GetTotalAllocatedMemoryLong +96,527B는 physical RAM/누수 확정이 아니다. 보호32파일과 기존 user tracked30 해시를 보존하며 이번 실험·인계만 선별 커밋한다. full native 직렬화/모든 shader globals를 새로 동등검증한 것은 아니며 이번 reader/replay가 그 값에 쓰지 않았다는 범위다. CUA/InputSettings 교체/SaveAssets/ClearDirty/삭제/reset/강제종료/강제GC/push 없음.

## Eye91–93 — 남은 가림/backing/명암 생산자 진단, Graph GPU 재검증 보류

최신 자료는 `experiments/pixel-pipeline/2026-11-01-visibility-backing91-93/INDEX.html`이다. 커밋은 `git log -1 --format=%H -- experiments/pixel-pipeline/2026-11-01-visibility-backing91-93`로 찾는다. **제품77 유지/전체 후보 미채택.** 이전90의03acbb64와89 원본409a6dbc는 보존했다. 이번은 유효19프레임(91A8/91B8/92생산자3), 이후93/93B는 각각0프레임 실패다. 기본 제품/기존 재질/rendererFeatures 자산/C# Assets를 바꾸지 않고 독립 shader6개와meta, 외부 runner/실험만 추가했다.

`prepare91.py`, `resolve91.py:alpha_bounds/main`은 old140의 남은56 native pixels를 backing36/안검20(5셀)로 분리했다. 같은 evaluated face/camera의110 query와 원본178 UV/890 getter를 대조했다. 기존 unknown47하위 표본이 실제 앞 불투명 면에 가려졌다(최종47픽셀 삭제 수가 아님). 현재 보수 질량식의 raster(11,5)는 label0/새 특징 대입 없음, 나머지4셀16native pixels는 old 몸/머리 exact ray 기하 부재로 미확정이다. label0은 배경 RGB/투명 칠이나 미술적 안검 삭제 승인이 아니다. old sourceId에 새 프레임의 몸/머리 기하를 섞지 않았으며 새91B에는 필요한 평가 몸/머리 mesh/material 관계를 동일프레임으로 추가 기록했다. `audit_old_backing91.py:main`은 old138–141의 실제 부재96누적표본 각각에서 앞면 피부/UV/불투명 알파를 확인했으나 RGB 복원/최종 가림 owner 선택 완료로 세지 않는다.

`CurrentRasters91:Bind/Render/Dispose`, `MotionScope91:Start/Apply/Dispose`, `CurrentBacking91.shader`는 현재 evaluated sampleFace의2x typed skin backing과4x source control을 만든다. 실제 Close/reopen8프레임에서 피부414→429→436→414, 기존 특징 footprint 안의 missing-backing 셀 중 완전 피부 제공0→1→4→0을 확인했다. 그러나 동일4x RGBA 최대오차0.15859377이 남아 공급기를 미채택했다. 348전/333후 cache를 clean skin으로 쓰지 않고 색 평균/임의 피부색/원색 보정은 하지 않았다. PNG는 피부 레이어이며 전체 눈 합성 성공이 아니다. source ROI의 일반54셀을 복원 성과로 세지 않고 실제 old feature footprint로 제한했다.

`ProductionTrace92.shader`, `capture92/Capture92:Arm76/Capture/Release76`, `analyse_production92.py:main`은 정상 RenderGraph S3 자체를 기록했다. 첫 프레임 원래 재질 후2프레임 소유 메타데이터 재질, head samplesOnly로 source resolve만 임시 생략하고 정상 종료 전 모두 원복했다(이3프레임은 미관 비교 금지). frame101/serial8/primitive110/sample(6,17)에서 원본 baseline와 geometry/원본g가 정확히 같았고, 같은 프레임 manual probe와 RGBA/meta/normal/SH 차이는0이다. available0.1223201975는 같지만 주광lit0.0290974006 대0.0214363262, g0.2378789485 대0.1752476394다. 차이는 main-light 실행 context로 좁혔고 정확한 shadow-resource/방향/감쇠 항은 미확정이다. 실제 생산자도SH0이므로 CPU ambient 비영만으로 SH가 유일 원인이라 주장하지 않는다. `OwnedAmbient91.hlsl`/`CurrentRasters91.BindAmbient91`의 실제SH A/B는 일부 오차를 줄이면서 원래 맞던 표본을 바꿔 동등성 실패/미채택이다. RGB G/노출/깊이 보정 없음. CPU raw-normal 근사는 normal map/half 정밀도를 재현하지 않으며 .00535 차이를 shader 결함 증거로 쓰지 않는다.

`GraphSources93:Enqueue/RecordRenderGraph/Draw/Dispose`는 endCamera의 수동 draw 대신 shadow 자원을 선언한 pass로 이동하는 독립 수정안이다. 첫93은 추가 카메라 컴포넌트 필수라는 관측기 전제로 실패했고 설치URP의 기본 renderer fallback으로 수정했다. 다음93B는 raster native attachment 총8제한에8색+depth를 넘겨 `FixedAttachmentArray` 오류, 이어 `ZBinningJob` safety 오류를 냈다. 정상 Exit로 끝냈고47개 내용/dirty31/입력/옵션 복원을 확인했다. **현재 최신 UnsafePass 버전은 컴파일만 성공, GPU 미실행**이다. 소유 텍스처와 main/additional shadow read를 모두 선언하고 native attachment 묶음을 피하며 재질4개를 pass별 독립 보유한다. 내부 job 상태를 공개 읽기 API로 확인하지 못했으므로 이후 Play를 반복하지 않았다. renderer의 안전한 정상 정리/재생성 경로 검토와 최소 GPU 재검증이 필요하다. 사용자 renderer Dispose/private job 완료/초기화/강제종료는 하지 않았다. 정책 거절이 아니라 실행 오류 후의 안전성 미확인 차단이다.

5회 모두 Edit/domain1/scene clean으로 종료, 별도 verify public/native47/47 exact, dirty31 및 InputSettings ID568105589213679894/22필드·장치·옵션·시간·pipeline/global·RT30→30을 보존했다. 일반 스냅샷의 native AssetImporter1은 종료 중 Unavailable이었으나 별도 getter verify47개는 exact였다. 이 값/내용 보존은 URP 내부 job 동등성 증명이 아니다. InputSettings 쓰기0/추가 장치0, 관측기/소유 자원 회수, borrowed buffer 미해제다. 내부 allocated delta는 SUMMARY91에 raw값으로 남기고 물리 RAM/누수로 단정하지 않는다. CUA/SaveAssets/ClearDirty/삭제/reset/강제GC/강제종료/보안 변경/push 없음. `test_archive91.py`는 실제 old140 기하110query/178alphas/old96 및 accepted19 raw프레임의 marker/plane identity와 실패·미적용 계약을 오프라인 재검증한다. 새 소스/설정은 미관·보행 시간 안정성의 완성으로 주장하지 않는다.

`JOB_EVIDENCE93.json`은22:44:20 attachment compile 실패와 뒤이은22:44:20–21 ZBinningJob safety 오류8건, 설치URP/Core의 경로·행·SHA를 보존한다. PreSetup의 예약과 SetupLights의Complete 사이에서 graph compile abort가 발생하면 완료 지점을 건너뛸 수 있다는 것은 소스 기반 인과 설명이고 live private job 상태 확인이 아니다. 마지막 공개 상태는 Edit/pausefalse/scene clean/dirty31/native47exact지만 renderer의 비직렬화 job 소유권은 미확인이다. UnsafePass는 Unity 정식 API이며 approval/security 우회가 아니다. 출력24색RT+4depth는 소유·Write, shadow는 borrowed·Read로 선언하고 자원 해제도 소유분만 한다. 추가 Play·renderer 재생성/초기화는 보류 중이다.

## Eye94 — Graph 주광 문맥 동등성 실측, backing 잔차·상태 지연은 미해결
최신 비교: `experiments/pixel-pipeline/2026-11-01-graph-context94/INDEX.html`. 관련 커밋은 `git log -1 --format=%H -- experiments/pixel-pipeline/2026-11-01-graph-context94`로 찾는다. 제품77 유지/Assets 변경0/import0/renderer 재생성·초기화0이다.
`prepare94.py:make`, `GraphSources93:RecordRenderGraph/Draw/Dispose`, `capture/Capture94:Arm76/CameraEnd89/Capture/Release76`은 정식 AddUnsafePass에서 소유24 colour+4depth RT의 Write 및 borrowed shadow Read를 선언한다. 8 colour+depth를 native attachment 배열에 넣지 않는다. 외부 전체 C# 컴파일 후 정상 Play1회, frame99–102 같은 입력136planes/4카메라/4평가메쉬를 완료 marker로 검증했다. begin-camera는 기존 renderer에 pass를 enqueue하고 end-camera는 완료만 확인한다. rendererFeatures 자산·원본 재질을 영구 변경하지 않는다.
`analyse94.py:main`, `test94.py:main`은 actual S3 생산자와 Graph source의 RGBA/meta 및 계측3프레임의 normal/SH/lit/available/mainLit/g 차이0을 확인한다. retarget/original graph8필드도 차이0이다. 이전92 수동 endCamera 문맥의 주광 불일치는 이번 Graph 문맥 비교에서 재현되지 않는다. 다른 모델/뷰/광원 및 최종 눈 합성 전체 동등성 증명은 아니다.
같은4x skin control의 role/owner/alpha/coverage는 정확히 같지만 RGBA max0.0004570484, depth max0.0000057220 잔차가 있다. 명시적 linear→sRGB8 미리보기 변환에서 닫힘 변형 마지막프레임의1표본만1코드 차이가 남는다(RESULT94 좌표/RGBA 보존). backing 공급기와 최종 합성은 미채택이다.
`MotionScope94:Advance/Apply` 요청 Close getter와 평가메쉬를 동일 상태로 해석하면 안 된다. frame101 getter100인데 메쉬는 첫프레임과 동일, frame102 getter0에서 메쉬 delta0.02499783/skin2x414→436이다. 카메라 sourceFrame5.333333/evaluatedFrame5.25 고정과 별도로 native Close 평가가 한프레임 늦게 나타났다. 이번 최소4프레임은 실제 재개방을 포착하지 못했다. PNG는 요청값/메쉬 delta를 함께 표시하며 Close/reopen·보행 안정성 성공으로 세지 않는다.
정상 Edit 종료 후 공개 상태 차이0, dirty31 동일, 별도47/47 직렬화 exact, InputSettings ID568105589213679894/22값·장치·옵션·시간·pipeline/global 복원, own pass/material/RT 회수, RT30→30이다. 신규 Console/프로젝트 로그 예외0이며 과거 ZBinning 오류는 기존 기록으로 보존했다. allocated +33.008MiB는 내부 할당 카운터 차이이며 물리 RAM·누수 확정이 아니다. CUA/SaveAssets/ClearDirty/GC/앱 종료/추가 Play 없음.

## Eye95 — 같은 프레임 가림·현재 바탕·공동 선택의 격리 GPU 검증 (제품77 유지)

- 최신 산출물: `experiments/pixel-pipeline/2026-11-01-whole-eye95/INDEX.html`. 커밋은 해당 경로 `git log -1 --format=%H -- <경로>`로 조회한다. Assets 수정/import0, 제품 기본77 유지.

- `MotionScope95.Apply/Advance`: 정상 ScaleBake378와 같은 `BakeMesh(expected,true)` 및 output-space 변환으로 평가 정점/눈 sampleFace 오차0일 때만 캡처. 첫 false-scale 기준 실패 Play는0packet으로 정상 종료했고, 수정 후 Play1회에서99,100,102,104,105,107,108의110planes씩770planes를 얻었다. 조건 선택 스냅샷이며7연속 움직임 프레임은 아니다.

- `NativeRetarget95.RecordGraph/DrawGraph/Dispose`, `GraphSources95.RecordRenderGraph`: 눈별·파트별 material8개를 분리해 deferred property 덮임을 막고, source/control/현재 바탕을 같은 URP Graph 조명 문맥에서 생성한다. actual S3와 physical control5필드 차이0. own RTHandle wrapper는 transferOwnership=false로 release 후 자기 RT만 해제한다.

- `ownership95.main`, `solve95.main`: UV7 eye-owner 계약으로 현재 feature가 대체하는 원본 iris/white/highlight/eyeline을 외부 가림에서 중복 계산하지 않는다. 실제 피부/안검·반대 눈·머리/몸은 계속 가림이다. 보호 record14.z는 전체 composed-source 표시이므로 전부 안검으로 보호하지 않고 visible role5인 native 안검만 그대로 보존한다. 바탕은 같은 native 표본 위치의 현재 physical 또는 feature-local skin source를 사용하며 source UV/primitive를 기록한다. 주변색 추정/평균/임의 깊이 없음.

- `solve95.source_texel/resolve_identity_tie`: frame102 canonical(12,4) 홍채:흰자 mass7:7에서 이전100과 같은 현재 가시 source texel(eye1,role1,220,79)일 때만 동률을 푼다. 화면 RGB 평균이 아니며 sourceKey가 없거나 alpha/가림이 불확실하면 원래 출력+invalid를 유지한다. cold tie는 미해결. source sequence/mesh/topology/template/bounds가 scope이며 실제 runtime port에는 generation/view lifetime 연결이 추가로 필요하다.

- `FinalGPU95Final.Execute`, `validate_final95.main`: frozen 선택을 colour/실제 Native395 owner/depth 세 개 Float32 LUT로21번 GPU 대입하여 차이0·팔레트 밖0. owner.w를 alpha로 오독한 중간 Close replay는 의미 검증 통과가 아니며 최종본은 실제 source primitive ID로 수정했다. 완전 Close104/105의 보정 scope에 iris/white owner0, 바탕 누락/미확정0. open99/100과 reopen107/108 canonical signature 동일. 검사는150개이나 미관/시간 안정성 증거와 구분한다.

- 94의 preview1코드는 blue 선형 .3993057013/.3994446099가 sRGB8 반올림 경계 .3993615253 양쪽에 있기 때문이다. 원시 source draw 부동소수 차이의 정확한 상류 원인은 미확정.95는 RGB8 roundtrip 없이 실제 Float32 source값을 LUT에 넣으며 변환 오차를 임의 색 오차 허용으로 숨기지 않는다.

- PNG 원래 크기/nearest12/7상태 GIF를 직접 검수했다. 눈 노출 크기·갈색/피부 스타일 차이는 미술 승인되지 않았고 live 공동 selector는 아직 Python oracle이다. 실제 C#/HLSL로 source ownership/current visibility/cache를 이식하지 않았으므로 제품 적용/전체 미관 성공/움직임 안정화 완료가 아니다. 다음 통합 판단은 이 결과와 cold-tie/state/lifetime 한계를 먼저 읽는다.

- 종료 Edit, GameMap1 clean, dirty31/47직렬화 내용/동일 InputSettings22값·장치·옵션·pipeline/time 보존. 외부 global journal getter 불일치0·buffer global writes0. RT30→30. capture 할당량 변화는 SUMMARY95의 Unity allocated counter이며 physical RAM/누수 판정이 아니다. 이번150검사 후 read-only 검증도47/47 exact·공개 상태 차이0·신규 Console 오류0. 원본 사용자30 tracked 변경/보호32파일은 커밋 전후 별도 해시 확인한다.

## Eye96 — 실제 renderer 입력의 격리 GPU 공동 선택 중간 보존점

- 최신: `experiments/pixel-pipeline/2026-11-01-live-joint96/INDEX.html`; 커밋은 해당 경로 git log로 조회. 새 `Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/WholeEye96.compute`와.meta만 추가, 기존 제품77/사용자30변경 유지. C#은 Assets 밖 외부 동적 컴파일이라 domain reload/import0이다.

- `WholeEye96.cs` constructor/Resize/Dispatch/Compose/Dispose, `WholeEye96.compute` Refit/Query/Select/Compose: 고정 topology BVH는 초기1회, 매프레임 현재 정점의 범위를 GPU refit한다. 원본 texture alpha를 직접 읽고 같은 feature가 대체하는 원본 파츠를 중복 가림으로 세지 않는다. 공동 선택·source-key witness·현재 backing 및 실제 Native395 owner.w=primitive를 GPU에서 계산한다. CPU 선택 재생이 아니다. 원본 UV/정점과 현재 변형·가림을 분리한다.

- `LiveSurface96` constructor/Update: 실제 renderer mesh/material 관계를1회 수집하고 기존 CPU 평가메쉬 정점만 매프레임 업로드. `LiveGraph96.Record/Draw`, `NativeRetarget96.RecordGraph`, `GraphSources96.RecordRenderGraph`는 source 쓰기와 compute 의존 RT/GraphicsBuffer를 같은 Graph에 선언한다. `LiveFinal96.Present`는 실제 native가 나온 동일frame/serial의 소유 출력에만 합성한다. 기본 runtime 클래스에 GetData/AsyncGPUReadback0; 캡처 관찰기만 bounded readback한다.

- frozen95의7상태는 좌표→가림→선택→최종 colour/owner/depth 전체 GPU 계산이 CPU와 exact. 새 실제 source `eye96-20261101T152835759Z-98a0bc1e`도 동일7개 평가상태에서 최종3필드/공동 선택 exact, 안검 보호 exact. CPU PNG alpha 출처는 기존 Unity GetPixel4230개와 먼저 대조해flip버전 mismatch0이다. 전체 skin transmittance에는 최대2.9802322e-8의 FP32 연산순서 차이가 있으나 최종 선택/색 차이0; 이를 bit-exact 가림으로 쓰지 않는다.

- 20,459정점/29,542삼각형, 약2,486~2,682쿼리에 삼각형9,540~10,586회, 최고노드197~233개, stack overflow0, 소유 알고리즘버퍼6,418,564bytes. alpha 복제60MB를 제거하고 원본 텍스처를 빌려 읽는다. 실제GPU시간은 미측정이며 debug source 렌더/동기캡처 포함 속도를 제품FPS로 주장하지 않는다.

- 기존 scope거절/이중Dispose/Dispose후사용거절/ownedbytes0를 frozenGPU에서 검증. 동시 다중뷰/재초기화/88위상·회전·보행은 다음 검증이다. 최초 exact tie는 근거 없으면 원래 출력+invalid로 남기는 명시 규칙이며 파츠 우선의 미술 선택은 자동 채택하지 않았다. `LiveFinal96.PresentCurrent`는 후속 매렌더프레임 연결 준비이며 이번7캡처에서는 Present만 호출했다.

- 정상Edit, scene clean/dirty31/실제입력객체·22값·장치·옵션·pipeline/time 보존. 종료직후 Resources46/47 중1개가 Unavailable였으나 분리검증에서는47/47 exact. 해당 객체는 빈145바이트 ProjectSettings AssetImporter가 일시 미조회였으나 공개GetAtPath에서 원래ID와내용exact. getter만 호출했고 reimport/저장/추측복구 없음. RT/할당량은SUMMARY96 참조. 초기 실패 shader의0query COMPLETE marker는 무효이며 후속코드는0query/overflow를 실패로 처리한다. 최신 코드/실제 실행 bundle과 실패는 분리 보존한다. 제품 기본값은 아직77이며 더 큰 눈 노출/피부스타일은 미술 승인되지 않았다.

## Eye97 — 실제 위상·보행·회전 및 실시간 선택의 미해결 계약

- 최신 비교/코드: `experiments/pixel-pipeline/2026-11-01-live-motion97/INDEX.html`. 관련 커밋은 해당 경로의 `git log -1`로 조회. 기준96은 `2672df7a`; 이번97은 Assets 변경0, 제품77 기본 경로와 기존 사용자30변경을 보존한 **격리 실시간 검증**이다. 오프라인 선택값 재생이 아니다.
- `LiveFinal96.PresentCurrent`가 정상 native frame/serial별 별도 RT에 합성한다. 실제 source Graph42회/최종 합성41회, 위상10·보행8·회전10장의 실제 입력을 저장했다. `NativeRetarget96.RecordGraph`, `GraphSources96.RecordRenderGraph`의 기본 diagnostic path를 줄여 현재 source parts/변형 backing만 생산한다. 실행한 정확한 소스는 `motion/RUN_Capture97.cs.txt`에 동결했다. `MotionScope97`는 InputSettings 객체를 교체하지 않는다.
- `WholeEye96.Query/Select/Compose`는 원본 material/UV/alpha와 현재 평가 정점을 GPU에서 사용한다. 실제 측정 상대 위상0→0.999985px에서 canonical role/owner 및 RGBA 서명이 각각1개. 보행8장도 보호/색 출처/불필요한 미확정 회귀0. 그러나 보행의 실제 자세/가림 변화까지 형태 불변이라고 주장하지 않는다. 가림/색 보존은 실제 원배율·nearest 확대/시퀀스를 검수했다. 큰 눈·피부 스타일의 미술적 승인은 별개다.
- **회전 미통과:** frame127/128/134/136의 native 미확정3/6/1/2픽셀을 원본 통과로 유지했다. 독립 CPU 삼각형/원본 alpha 계산과 이4장의 최종 colour/owner/depth 및 canonical 값은 exact. CPU는4장 냉시작이므로 미관측 warm history 전체 동등성 증명은 아니다. `ROTATION_FAILURES97.json`에 좌표·16표본 mass·실제 원본값을 기록했다. exact coverage 동률6canonical 셀(iris/sclera4, eye/background2)과 바탕 부재3native 픽셀을 구분한다. unknown alpha를 투명으로 간주하지 않았다.
- `Compose`의 피부만 허용하는 바탕 계약은 frame128의 두 픽셀에 실제 존재하는 머리카락 base를 거부한다. 임의 피부 채움 문제가 아니라 **현재 비눈 source underlay를 typed owner/depth/정확 sampling과 함께 연결해야 하는 누락**이다. pre348 baseline에는 RGB와 owner가 이미 기존 눈 결과인 반면 meta는 머리카락인 혼합 상태가 있어 baseline RGBA만 복사하면 안 된다. frame134 한 픽셀은 actual skin 교차/base/backing이 모두 없고 정확 native 좌표의 world/non-eye underlay가 미캡처라 주변색 추정 복원은 금지한다. 이 계약을 해결하기 전 제품 대체하지 않는다.
- 냉시작 exact eye-part tie는 기본0=미확정/원본 통과다. 명시적 iris/sclera 우선 비교1/4는 원래 source RGBA와 source key를 유지하지만 서로 다른 미술 선택이라 **미채택**. `COLD_POLICIES97.json`과 비교 PNG. witness는 현재 실제 가시한 동일 원본 texel만 tie-break에 사용할 수 있다. background와 동률은 eye-part priority로 억지 채택하지 않는다.
- `WholeEye96` constructor/Resize/InvalidateWitness/Dispose의 GPU 수명 검증: 동시 두 model/view owner 격리, 팔레트RGB 변경 시 region identity 불변, 명시적 witness 무효화, 다른 owner 해제 후 생존, 첫 frame 전 취소, 생성 실패 cleanup, 잘못된 scope와 dispose후 사용 거부/중복 해제, ownedbytes0. `LiveSurface96`의 camera/view/source-array identity 및 borrowed-alpha 생존 guard는 실제 motion 이후 추가되어 cold/lifetime 외부 컴파일에 포함됐으며 새 actual renderer Play 재검증은 아직 아니다. 같은 텍스처의 in-place 특징 편집은 `SourceFeaturesEditedInPlace()`로 명시 무효화해야 한다.
- 현재20,459정점/29,542삼각형, algorithm buffer 최대6,678,916bytes(ROI에 따라 가변), frame당query1,250~2,858/triangle tests2,946~10,426/max nodes363/overflow0. 정적 BVH 이후 매frame O(T) refit와 계층 query. 추가 runtime GPU→CPU readback0이며 캡처만 진단 읽기. CPU source 정점 업로드는 남아 있다. GPU timestamp/제품 FPS는 **미측정**이고 static build를 포함한 CPU submit시간은 GPU시간이 아니다.
- 정상 Edit 복귀, scene clean/dirty31·입력 객체22값·장치/옵션/pipeline/time 유지, 공개 상태 차이0, 직접 native 직렬화47/47 exact. RT30→30, `Profiler.GetTotalAllocatedMemoryLong` +35.36MiB는 물리 working set/누수 판정이 아니다. 마지막 읽기 시점은 `SUMMARY97.latestReadOnlyEditorUTC`. 소유 자원0·현재 복원 상태를 확인했으며 SaveAssets/GC/ClearDirty/초기화/push0. `test_archive97.py`는 Unity 없이 저장 raw marker/프레임 식별/회전 CPU-GPU exact/실패 분류를 다시 검사한다.

## Eye98 — 피부 전용 backing 제한 수정, 동률은 별도 미채택

- 최신 비교/원본 수치/코드: `experiments/pixel-pipeline/2026-11-01-source-underlay98/INDEX.html`; 관련 커밋은 해당 경로 `git log -1`. 기준97=`ab51a469`. 새 Assets는 `EyeBoundaryRestore348/Shaders/WholeEye98.compute`, `CurrentNonEye98.shader`와 .meta뿐이다. 제품77/default·기존 사용자30파일·보호32해시 유지, C# Assets import/domain reload0, push0. 실제 경로는 외부 runner 격리 통합이다.
- `NonEyeUnderlay98.Record/Draw/Bind` → `GraphSources96.RecordRenderGraph` → `LiveFinal96.Present` → `WholeEye96.PackWorld98/Compose`, HLSL `PackWorld98/Compose`. 현재 evaluated mesh와 기존 material role 관계로 비눈11draw, 원본 RGBA/role/owner/depth/UV/primitive를 한 표본에서 생산한다. 원래 유효한 physical/transported skin을 먼저 보존하고, 없을 때만 typed 비눈 source → 실제 Native395 world sample 순으로 복원한다. 비눈 partial alpha는 새 혼합/팔레트 규칙 없이 확정 복원하지 않는다. material ID/source region/occlusion owner는 합치지 않았다.
- 실제 최종 source=`eye98c-20261101T162728074Z-4dce5c01`, 위상10·보행8·회전10·evaluated Close/reopen7(0/0/50/100/100/0/0), 총35상태. 같은 프레임 기존96/후보98을 GPU에서 함께 실행했다. 기존 유효 native202,959표본은 colour/owner/depth/audit **네 필드 exact**, 실패3표본만 변경, 새 회귀0. `policy98.compose` 독립 CPU도35장 네 필드 exact다. 이것은 실제 GPU 선택/합성이며 offline 선택 재생이 아니다. 진단용 기존96 비교 합성·RT는 추가 오버헤드다.
- 3표본: frame128 native(434,438)=실제 world, (435,438)=원본 hair source slot2/submesh0/primitive761, frame134(437,440)=실제 world. 97 coarse base의 두 표본을 모두 hair라고 보던 가설은 native2x 기하/가림으로 정정했다. `SOURCE_RAYS98.json`은 현재 mesh/원본 PNG alpha의 독립 검증이며 world두 ray에는 비눈 가시 삼각형이 없다. source UV는 CPU double과0.000154 차이, 재투영 약0.00020px를 그대로 기록했다. 같은 원본 삼각형/2x footprint 안이지만 double bit-exact라고 하지 않는다. **실제 GPU RGBA/owner/primitive 복사와 world/native depth는 exact**다.
- `TRIAL_STATUS98`: 최초 trial은 부분 투명 brow가 원래 유효한 skin보다 우선해1회귀 → 미채택. 두 번째는 transported 좌표가 physical p를 덮어 hair를 world로 잘못 복원 → 독립 CPU 네 필드 불일치로 기각. 최종은 별도 `physicalP98`을 보존한다. 실패 소스와 대표 raw 반례도 보관했다. 미확정 숫자 감소만으로 앞 두 결과를 통과시키지 않았다.
- 회전 미확정은127/128/136에3/4/2 native픽셀(정확한 coverage 동률6canonical셀)로 남긴다. 실제 깊이 위계는 이미 표본 가림에 반영되지만8:8 홍채/흰자 또는 눈/바탕 aggregate tie의 디자인 우선순위까지 정하지 않는다. 현재 가시한 동일 source texel witness 규칙은 유지한다. 무근거 role-only 유지/메모리 순서/전체 iris 우선은 채택하지 않았다. `POLICIES98C.json` 및 `policy-review-c/`는 엄격 보존 / 눈파트 우선 / 바탕·흰자 우선의 **오프라인 디자인 비교**이며 changed RGBA/owner/좌표·원배율·nearest 확대·동일 turn/Close 시퀀스를 제공한다. 미확정0은 정책 추가의 결과이지 미관 성공 증거가 아니다. 대안의 GPU 통합은 사용자 디자인 선택 뒤 검증할 항목이다.
- 실제 위상0~1px의 canonical role/owner·RGBA 서명1개 유지. 보호 안검/원본 통과/색 출처 유지. Complete Close는 evaluated BakeMesh 오차0에서 iris/sclera0, reopen 원형 복귀. 현재35상태·단일 실제 URP view의 검증이며 모든 회전/모델/상태를 보장하지 않는다. 새 non-eye pass의 두 실제 view 동시 실행은 미검증; 공통 engine의 다중 owner/취소/해제는97 근거다. 원본 sampler/material의 in-place 편집은 명시적 무효화 계약이 필요하다.
- `GpuTiming98.Read`: 공개 Recorder GPU marker는 valid이나 GPU block0 → GPU시간/FPS **미측정**. CPU marker를 GPU시간으로 쓰지 않는다. profiling/보안 설정 변경0. 새 source+world RT최대224,672bytes, 비교용 legacy4RT는 별도. 기본 추가 GPU→CPU readback0, capture만 bounded 진단. 현재 CPU 평가정점 업로드 및 BVH refit, 추가11draw 비용이 남는다.
- 세 trial 모두 정상 Edit 종료, scene/dirty31·입력 객체22값·장치/옵션/pipeline/time 보존, native 직렬화47/47 exact·RT30→30·신규 Console 오류0. 마지막 읽기는 `SUMMARY98.lastPublicReadUTC`, owned98 material/RT/compute clone0. 최종 `Profiler.GetTotalAllocatedMemoryLong` +35.94MiB는 physical RAM/누수 판정이 아니다. SaveAssets/ClearDirty/GC/초기화/앱 종료0. 남은 사항은 동률 디자인 선택, GPU 예산/실제 다중뷰·다른모델 검증, 제품 기본 callback 연결이며 미관 완성/제품 적용으로 보고하지 않는다.
- Export 주의: non-eye4plane의 raw viewId는 native-final readback group으로 기록됐으나 실제 producer는 `source.camera` physical head2x다. RAW는 수정하지 않았고 `VIEW_CONTRACT98.json`에 명시 대응을 보존했다. source/frame/serial은 일치하고 CPU 재검사는 실제 producer matrix를 사용한다. `prepare98.py`의 다음 export frame label만 고쳤으며 이번 실행 소스는 `capture-c/RUN_Capture98C.cs.txt` 그대로 보존했다. 이 label을 main-view depth로 해석하면 안 된다.

## Eye99 — 실제 두 source view 격리·GPU 표본, 동률 미채택

- 기준 98 = `cf8b1414`. 최신 비교/스크립트: `experiments/pixel-pipeline/2026-11-01-view-isolation99/INDEX.html`; 관련 커밋은 해당 경로 `git log -1`. 제품 77/default·98 확정 복원 수정·사용자 30개 변경·보호 32파일은 유지,99 Assets 변경/import 0.
- `ViewB99.AddB99/PrepareB99/TickViews99/CaptureB99/DisposeB99`: 기존 실제 head/main 카메라별 source·BVH query·typed non-eye·캐시를 분리. source 6프레임 동시 생산, B witness 단독 무효화/재생성, B 해제 후 A 4프레임 지속. scope·버퍼·RT 분리, 실제view행렬/격자 다름. 공유 world 읽기 전용 3,996표본 RGBA/texel/depth exact. raw 1,032plane source/frame/serial/view 대조. A 특징색/identity SHA 1종. B 원본 348 records는 head 모드에서 미생산이므로 **B 최종 눈 합성은 미검증**, 임의 각도 다중뷰/모델 교체 보증 아님.
- `LiveGraph96.Draw`/`NonEyeUnderlay98.Draw`/`LiveFinal96.Present`: GPU-enabled URP ProfilingSampler만 추가, 알고리즘/동률 정책 변경 0. 실제 RX9070XT/D3D11 GPU 표본: query block 중앙 A .41042ms/B .40187ms, non-eye .03528/.03030ms, worldpack .00264/.00246ms. B query/non-eye는 2block/프레임으로 원시 합계를 나눴음. compose 0~.000040ms는 안정적 비용값으로 채택하지 않음.3프레임 지연 집계이며 GPU fence별 동기 측정 아님. Pack/retarget/전체renderer/readback 제외, 전체 프레임/FPS 예산 미확정. CPU 대체 0. 각 engine buffer 6,418,564B(2개 12,837,128B; RT 제외), 뷰당 2,486query. `PROFILING99.json` 원시값/범위.
- Play 1회 10프레임 → 정상 Edit 복귀, dirty31/직렬화 47개·InputSettings 동일 참조·22값/장치/씬/옵션/background/time/pipeline/global 보존, RT30→30, 신규 오류 0. Unity 할당 −18.61MiB는 물리 RAM/누수 증명 아님. `HoldScope99`는이동/animator 속도만 임시 보류하고 복구; 설정 객체 교체/가상 장치 0. `analyse99`와archive회귀검사는실제 marker/같은 frame의 모든 필드 대조.
- 기존 98의 세 동률 정책만 `deliverables/EYE_TIE_CHOICES_99.png`(원배율+nearest16)와`EYE_TIE_TURN_99.webp`(frame127~136,무손실10장·nearest4·느린재생)로재포장. 엄격보존/홍채→흰자→선→바탕/바탕→흰자→홍채→선, 정확한 coverage 동률에만 적용; 현재 미채택. 새 미술 후보 0. Library공식 helper는`prepare_uploads is not available`로업로드 전 실패, fileID/온라인 링크 없음(`DELIVERY_STATUS99.json`). 사용자의 디자인 선택과 B 최종 다중뷰/GPU 전체 예산 기술 미검증을 구분.

## Eye100 — 머리카락 OFF 제품77 실측, Argon2/2.1 대조

- 기준 `c21e260f`. 최신 실제 캡처/코드: `experiments/pixel-pipeline/2026-11-01-hair-isolation100/INDEX.html`; 관련 커밋은 해당 경로 `git log -1`. 제품 알고리즘은 아직77이고98/99 미연결. 동률3지선다 대기는 중단한다. 이번 실제 소스 캡처와 문서 분석을 완성된 정방향 레이어/팔레트 수정으로 보고하지 않는다.
- `HairDrawScope100.Start/Suppress/RestoreHair/Dispose`: 기존 runtime hair mesh의 submesh draw descriptor만0으로 억제, vertex/index buffer 삭제/초기화0. head/main registered/other hair와 shadow/source Renderer 원래 상태를 함께 보존한다. normal Play1회, frame100/103/106의 source hair367→0→367. 원래 descriptor/인덱스 해시/Renderer 상태 exact 복구. Assets C# import·씬/프리팹 저장0. dirty31→31, 직렬화47/47 exact, 입력 같은 객체22값/장치/옵션/씬/pipeline/time/global 보존, RT30→30, 신규 오류0.
- `CaptureFragment100.Capture`는 실제 product77의 source/legacy class/prepared/postLine/348/native와 S0~S6·counts48/records256을 동일 frame/serial의 bounded ROI로 export한다. RAW78plane×3, 유효 marker만 사용. source raw4는 원래 shader 출력이지 unlit albedo로 단정하지 않는다. Template GetPixels crop의 상하 방향 오류는 `EXPORT_CORRECTION100.json`에 남겼고 future producer만 수정(아직 재실행0). RAW는 그대로, 분석은 prefab GUID로 확인한 원본 Template216 RGBA/role 자산을 `template_reference100`으로 오프라인 추출해 보완했다.
- `analyse100/provenance100.trace`: 머리 OFF face role3의 Q0/.5/1이 존재하지만 source shader67색→스타일110색→라인110색→눈 합성107색(RGB8)이다. material role3은 피부/두피 등의 의미 region이 아니다. 홍채8셀/7색·흰자7셀/6색은 현재 Template216 atlas와15/15 RGB8 exact. 348의 `ComposedSource76`이17눈 셀의 기존295 결과를 보존하고, 새 native 안검 선택은1셀이다. visibility 대표 S1/S2 sample을 색 출처로 오해하면 잘못된 오염 판정이 된다. native 안검(eyeROI14,4)은 동일 source UV의 S3 RGBA×shade.z(.72)와 float exact.
- 코드 순서: `HeadLocal367.RenderFrame` L32, `FullFeature367.DispatchPost` L53~64(Prepare→RestoreStyle→JoinBare→OwnerLines→295→DeferredEyes348→Resolve), `HeadLocal367.DeferredEyes` L36~37, `EyeRenderer367.Samples/Dispatch` L6~16. 몸/머리480격자는 분리되고 offset/depthOffset으로 join; 눈 support는 머리 격자의4x subsample, Native395는960표시다. 고정 painter order와 실제 depth/coverage는 구분한다. `SurfaceLayerOutput335`(FaceSceneLight335 L70~74)는 여전히 colour*factor, `EyeFeature348` L39/114/232는 외부 가림을 선택 질량에 결합, L296~297은 lerp, L250~260은 old295 colour 보존이다. 유한 P[region,q]는 현재 제품에 연결되지 않았다.
- `OwnerLines333` L18은 얼굴/눈을 대상에서 제외(이번 변경0셀), L35는 *.55 후 일부 deepSkin/deepCream 슬롯 치환. OFF의 source role7/10은23/60셀이 바뀌며 모두 같은 프레임 pre-line RGB8 집합 밖이다(그 집합은 의도된 finite P가 아님). 실제 main(228,201) linear[.01641632,.06643295,.11124785]→[.00902898,.03653812,.06118632], *.55 exact. 전체 팔레트 밖 색은 P 미설정이라 정의 불가; 임의3~4색으로0 판정을 만들지 않았다.
- 원문 `C:/Users/15352/Desktop/Argon2.md`, 실제 보충 파일 `Argon2.1.md` 둘 다 읽었고 수정/외부연락0. 양자화·레이어가 ‘전혀 없다’는 표현은 과도하지만, 유한색 미연결/가림→shape 결합/이미 눈 있는 BaseFinal의 vacated 복원이라는 핵심 지적은 맞는다. world 복사가 실제 ray와 맞아도 깨끗한2D 얼굴 canvas 계약은 충족하지 않는다. 2.1의 skin-role sclera proxy는 폐합 후보이나 role만 바꿔 UV를 피부로 바꿀 수 없고, .35 법선 혼합이 모든 회전/Close 구멍0을 보증하지 않는다.
- `blueprint_checks100`: K 총3색의 생성0..2와 예제 lookup1/2/3 불일치, 제안 L코너 삭제의4연결1→2 및 회전 편향 반례를 검증. `ResolvePaletteRegionId`, `IsTopContourCell`, cleanup 구체 구현은 문서에 없음. 다음 최소 연결은 **원본 UV 의미 region/P 확정→눈 없는 current face+socket proxy canvas→외부 머리와 독립된 전체 eye canonical/Close→머리 depth/coverage 이산 가림→모든 내부/외곽선 P 직접 조회**다. old==q도 조회하며 슬롯 범위/뷰별 buffer 소유·무효화·동일 source transport를 먼저 계약한다. 초기 native 광량·팔레트 간격·영역 선택은 독립이다.
- 검토 질문: (1) 같은 material의 피부/두피/얇은 무늬를 보존할 UV region resolver와 대표색 근거, (2) original evaluated sclera proxy의 폐합·depth/alpha/Close 및 skin-region mapping, (3) 기존 전체 eye template와 native lid를 source-local 공동 배치하고 visibility를 후단으로 옮기는 정확한 함수 경계. blanket1~2셀 다수결·등방성 없는 thinning·화면 고정 previous-label·고정3~4색을 무조건 채택하지 않는다. 현100은 고정 pose 진단이며 새 hair-off 회전/새 Layer0/Layer1 완성·미관 성공은 미검증이다.

## 101 — 이전 눈을 읽지 않는 격리 Layer0, 부분 구현

- 산출물: `experiments/pixel-pipeline/2026-11-01-layer-zero101/INDEX.html`, `RESULT101.json`, `RAW101.zip`. **제품77 미변경**, 새 `LayerZero101.shader`는 격리 패스에서만 사용한다. 제품의295→348 선합성 호출 자체를 아직 제거한 것은 아니다.
- `LayerZero101.RecordRenderGraph/Draw/Dispose`: 현재 evaluated 피부·sclera·iris 기하를 새 owned RT에 forward draw한다. 기존295/348/98 colour·world backing 입력0. actual URP graph의 SH/주광/그림자 사용, global observer writes0, 빌린 mesh/buffer 해제0. 첫 실행은 head camera AdditionalCameraData 부재로 enqueue 실패했으며 정상 복구 후 기존 URP default renderer 연결로 수정했다. 실패 기록을 보존했다.
- `SkinSource101`→`RendererFamily59.TryReadSourcePoint`→`SourcePalette58.ExtractReference/MakePalette`: 기존 native skin closedBoundary의 실제 source material/UV/texel을 읽어 eye-socket 피부 영역만 등록한다. 두 원본 기준색 RGB8[246,238,222]/[245,237,222]. eye UV나 주변 화면 RGB를 피부색으로 오인하지 않는다. 기존 face shade endpoint에서 팔레트 간격만 유도(임시 설정); 최종 proxy RGB에 광량을 곱하지 않는다. lookup0..N−1, 별도 outline 슬롯0. 전체 material을 이 피부색 하나로 합치지 않는다.
- 실제 Play 두 번(첫 실패1, 성공1), 성공 frame100/103/106 ON/OFF/복원57plane. source 피부/iris/sclera reference 대비 canvas 미피복0/0/0, proxy P[k] 밖 RGB8 0/0/0. `analyse101/test101` 실제 버퍼 재검산 및 Float32 슬롯14,371표본 통과. PNG를 직접 열어 검수했다. 미리보기1x는4x중 선언한1표본으로, 완성된 공동 cell 배치가 아니다. hair/shadow도 OFF하므로 서로 다른 프레임의 g 최대차이.27636/Q281표본 변화는 기록하며 동일 조명 A/B나 시간 안정성으로 주장하지 않는다. coverage mask 변화0, 최대 depth차이1.14e−5.
- 정상 Edit 복귀, dirty31/실제 PlayerSettings 직렬화/InputSettings 동일 객체22값·장치·씬/옵션/time/pipeline/global·protected32파일 및 사용자30변경 보존, RT30→30. 직렬화46개 exact, `ProjectSettings.asset`의 임시 `AssetImporter`1개는 종료 뒤 unavailable(실제 PlayerSettings는 exact). 전체47/47 복구라고 쓰지 않는다. 초기 동적 컴파일 오타와 import wrapper using 오류도 실행 전 실패로 구분했다.
- 미완: native 얼굴은 unlit source 진단이며 **얼굴 전체 UV region resolver/finite P**, 전체 눈 공동 배치, 후단 외부 머리 가림, 회전/Close/reopen 및 미관 검증은 아직 없다. L코너 삭제·다수결·blur를 추가하지 않았다. 다음은 이 clean canvas 위에 전체 눈을 외부 머리 가림과 독립적으로 올리는 단계다.

## 102 — 정방향 눈 계층 수정, 격리 GPU 검증 / 103 source-region 반례

- 기준 커밋101 `109fe57c`. 산출물 `experiments/pixel-pipeline/2026-11-01-forward-eye102/INDEX.html`, `reviewH/EYE_FORWARD_COMPARE102.png`, `EYE_MOTION102.webp`, `RAW102.zip`, `test_archive102.py`. 제품77은 유지하며 아래 경로는 격리 후보다. 이전295/348/98 완성 색·world backing을 입력받지 않는다. 제품의 legacy 호출 자체는 아직 제거하지 않았다.
- `ForwardCanvas102.Record/Draw/Dispose`, `LayerZero101.AfterCanvas`, `NativeRetarget96`, `LiveSurface96/WholeEye96`: source-local 현재 눈 배치→후단 머리 depth/coverage 이산 선택. Query는 현재 source face-skin만 internal occlusion으로 사용하고 hair/brow/body를 canonical eye 질량에서 제외한다. 현재 후단 합성은 hair만 구현했으며 모든 외부 파츠/world 가림 완성은 아니다. 관측 대상 모델의 기존 part binding에 의존하며 자동 의미 분류/모델100%범용성을 주장하지 않는다.
- **확정 원인:** 실제 첫 보행 frozen cell(canonical3,4)은 iris2+white7+canvas7. 기존 Select는 각 part를 canvas와 경쟁시켜 미확정이었으나 eye union9>canvas7이다. `SelectHierarchy102.hlsl`/`ForwardEye102.compute.Select`는 **눈 전체 union→내부 part coverage→동일 coverage의 유일한 실제 source depth** 순서로 수정했다. 정확한 half coverage는 foreground 포함(.5 inclusive)이며 최소 픽셀 예산이 아니다. 동일 source depth까지 동률이면 미확정 유지. frame-order witness로 결정하지 않는다. RGB/명암/특정 눈 크기는 선택 비용에 없다.
- `selection102.cell/choose`, `validate_hierarchy102`: 수정 전 실제 위상10/보행8/회전10에서 미확정 최대4셀, 수정 후 새 source28프레임에서0. 새 GPU 입력4092셀 CPU 재계산 불일치0, synthetic10통과. 같은 새 입력의 이전 strict 선택과 다른 셀도 전부 기록했다. phase world root 이동.99998474px/원점복귀0, canonical part/eye identity1종. RGB8은 native lid1셀 frame104에서[118,94,81]→[118,93,81]변동이 남는다. identity 안정성을 colour/전체 시간 안정화로 과장하지 않는다. 실제28프레임의 서로 다른 eye owner 혼입 표본은0이나 일반 다중-owner 겹침 정책의 완성을 주장하지 않는다.
- 머리OFF/ON 및 evaluated Close/reopen9상태도 새 kernel로 실제 검증했다. open 가림 전 iris9/white7/lid5 → Close50에서3/3/3 → Close100에서0/0/1 → reopen9/7/5. Source.BakeMesh와 현재 source mesh2e−6 이내 일치 조건을 통과한 시점만 캡처했다. source가림 전 배치와 외부 머리 가림을 분리했고 후단 hair RGB는 같은 cell의 actual S4 표본 한 색과 exact, lerp0. **닫힌 안검1셀은 충분한 key-form/눈매 보존 성공이 아니다.** 홍채·흰자는 선언된 원본 Template216 atlas palette 밖0, native lid/전체 얼굴·외곽선 finite P는 아직 미완이다.
- 최신 사용자6+2 평가는 참고 관찰이며 force/template 제약0. 현재 기준각 캡처의 screen-left eye2는 iris4/white4, 다른 eye1 iris5/white3이어서 그 설명과 같은 캡처/눈이라고 확정하지 않았다. 임의 양눈 동일화/고정2·4·6·8셀/화면RGB 평균·잔상·L코너 thinning을 추가하지 않았다.
- 최종18:58:45UTC, PID35364 응답/정상Edit,dirty31,RT30→30,신규Console오류0,입력 동일 객체22값·장치 및 temporary device 제거/옵션/time/pipeline/global 보존. 초기47snapshot의 임시 ProjectSettings AssetImporter1개는 종료 후 unavailable, 후기 baseline46은46exact이며 실제 PlayerSettings는 계속 exact다. 사용자30변경·보호32파일 보존. C# Assets import/reload/SaveAssets/ClearDirty/CUA/삭제/초기화/강제종료/push0. 새 compute는 격리 clone에서만 사용한다.
- **103 미채택 source 전제:** `source-regions103/inspect_source103.native_mesh/native_image/mask_uv`, `uv_features64.extract/axis_evidence/barrier_components`를 실제 VRM SHA·원본 PNG SHA·동일sourceId UV로 검사했다. source native texel/UV triangle 교차로 mask를 만들었으며 dilation/색bin CC가 아니다. 얼굴 role3은866160texel/11638RGB8, coarse5/fine1368. main798508texel의 같은 region에 RGB[42,20,21](L.223)과[254,248,231](L.979)이 함께 들어가 피부와 짙은 두피가 합쳐졌다. native lid는33814texel/8012RGB8, coarse28/fine2176. 원본/source debug PNG를 직접 검수했다.
- 따라서 coarse를 곧바로 P family로 쓰면62의 색 붕괴, fine 전체를 쓰면 과분절을 반복한다. palette family 공유를 region 보정으로 가장하지 않고 이 map을 미적용했다. 원본 AA 경계는 finite-width 연속 전이이므로 strict affine-jump가 모든 meaningful colour boundary를 잡는다는 전제가 틀리다. 범위/팔레트 수 sweep으로 덮지 않았다. Source affinity 단계에 finite-width AA 전이/지속 gradient/얇은 painted feature를 구분하는 source hierarchy가 필요하며 이 부분은 미해결이다.
- 검토 질문(기존 자료로 재현 가능): (1) 같은 source face UV에서 확인된 scalp/skin AA 전이를 source colour-bin 없이 연속 경계로 추출하고 soft gradient와 분리할 최소 기준, (2) native part6 raster1셀 대신 기존77 native upperArc/current closedBoundary와 authored eye의 전체 closed key-form을 어떤 대응 계약으로 묶을지, (3) resolver가 확정된 뒤 동일source/Q의P[region,k]와 별도 outline 슬롯을 초기/최종 모두에 연결할 위치. Argon에 외부 연락하지 않았으며 최신 저장소의 위 source/함수/실패 입력만으로 검토할 수 있다.

### 103 후속 — AA gradient peak 가설도 실제 영역 분할에는 실패

- `source-regions103/aa_transition103.gaussian/peaks`, `test_aa_transition103`, `inspect_aa_graph103`: sourceRGB8 양자 오차보다 큰 gradient peak를 native texel scale1/2/4에서 추적하는 최소 후보. Gaussian은 검출 신호에만 쓰며 원본/출력RGB는 바꾸지 않는다. 새 라이브러리 설치/Unity/GPU/제품 변경0.
- 합성 검증: ramp1영역, AA step2영역 및 서로 다른 두 쪽, 얇은 stripe3영역 및 띠 보존. 하지만 실제 source face는 여전히5영역/skin-scalp 미분리, native lid28영역이다. 얼굴2144edge는324열린 component/closed0, 안검1002edge는186열린 component/closed0. `AA_TRANSITION_TEST103.json`, `AA_GRAPH103.json`, `part*/aa-edges-on-source.png`에 근거를 보존했다. synthetic 통과를 실제 성공으로 올리지 않았고 palette/region map 적용0.
- 다음 쟁점은 더 많은 색 bin/peak 수가 아니라 **관측된 연속 전이→일관된 공유 경계 graph→영역 분할**이다. 원본에 없는 틈 메우기/작은 영역 삭제/curve smoothing을 임의로 덧붙이지 않았다. 현재 edge 검출기만으로 region resolver가 완성된다는 전제는 반례로 기각한다. 102 눈 계층 수정과 별개이며 제품77/사용자 변경 유지.

### 104/105 — UV 영역 분할 비교와 닫힌 안검 손실의 원인 분리

- 최신 재현본: `experiments/pixel-pipeline/2026-11-01-source-regions104-lid105/INDEX.html`. **제품77 유지, 신규 Assets/제품 코드 변경0**. 104는 저장된 원본 UV의 오프라인 분할, 105는 실제 관측6상태와 그 입력에 대한 제한된 오프라인 곡선 후보다. 실제 GPU 후보 통합이나 미관 완성이 아니다. 6+2셀 디자인 강제 없음.
- `source-regions104/graph_regions104.graph/partition`: [FH2004 원문 Algorithm1](https://cs.brown.edu/people/pfelzens/papers/seg-ijcv.pdf)을 독립 구현했다. native texel 4인접·색 차이 그래프, 검출용 σ=.8·k=300, 최소 면적 병합 없음. 끊긴 contour 봉합/색 bin CC가 아니다. 같은 원본에서 두피/피부는 분리하지만 얼굴681영역/단독311, 안검200영역이며 합성 AA step은9띠로 분절된다. **미채택**.
- `watershed104.topography/reconstruct_erosion/minima/flood`: [h-minima 정의](https://scikit-image.org/docs/stable/api/skimage.morphology.html#skimage.morphology.h_minima)와 [marker 기반 분할 원리](https://digitalcommons.usu.edu/microscopy/vol1992/iss6/28/)를 참고했다. 후단은 우리 positive additive geodesic label 계산이며 원논문의 watershed와 동일하다고 주장하지 않는다. 양끝 RGB8 반 코드 변동의 보수적 gradient bound로 h=4.8989868, 16.16 정수 거리의 정확한 동률은 미확정으로 둔다. 초안 minimax/plateau 계산은 L코너 회전 편향으로 기각했고 현재 계산은 회전 검사를 통과한다. 하지만 L코너 원형은2미확정셀/여러 region으로 갈라져 특징 보존에는 실패한다.
- 실제 geodesic 결과는 얼굴36영역/단독0, 안검370영역/단독10이다. 모든 반환 label의4연결은 확인했으나 이것은 미술 합격이 아니다. 볼의 원본 칠 `(382,704) RGB[253,228,208]`, 양옆 `(380,704)[254,235,213]`, `(384,704)[254,237,216]`이 모두 skin parent8로 합쳐진다. parent 하나를 P family 하나로 평탄화하면 이 칠이 소실된다. **native authored RGB8은 실제 입력이다. 잠재 연속색의 ±.5코드 오차를 가정했다고 얇은 무늬를 잡음으로 폐기할 근거가 생기지는 않는다.** 따라서 parent 분할 가능성과 child 색 특징 추출은 분리하고 얼굴/안검 유한P에 아직 연결하지 않았다. source RGBA/g/Q/팔레트는 변경0.
- `closed-support105/analyse105`와 `selection102.cell`: 정상 Play2회에서 각각 열림/평가된 Close100/재개방3상태만 기록했다. 두 실행의 sourceId는 서로 다르며 연속6프레임이라는 뜻이 아니다. 같은 프레임 canonical Layers/Visibility·변형 mesh·직접 기존 eyeInverse를 기록했다. Close source 안검149표본/알파108.4634 → 실제 skin Query 후96.7750,26논리셀 지지 → Select 후1셀이다. `(canonical4,5)`는 raw9.9561→실제 가림 후7.9640으로 낮아져 기각되고, `(13,4)`8.9155만 채택된다. 미확정 가림0. **현 Select는 셀별 면적 선택이며 원래 닫힌 안검 곡선의 연결을 보존하지 않는다.** 팔레트나 디자인 취향으로 넘길 문제가 아니다.
- `source_curve105.upper_arc/fit_homography`와 `curve_candidate105.curve_cells/source_support/hard_hair`: 기존 등록 native skin-ring의 위쪽 chain을 현재 변형·공개 eyeInverse로 투영하고 같은 눈/같은 셀의 확정 가시 안검 색소만 채운 오프라인 반례 후보다. 이 포즈에서 양쪽 각각4연결7셀(목표 수가 아닌 source 곡선 교차 결과), unsupported fill0/색 동률0, 실제 source RGB·UV·primitive·depth14개 증거가 있다. 열림/재개방0변경, Close1→14셀·14RGB변경(13추가+기존1색 표본 변경). 기존 외부 hair depth/coverage는 후단에 별도 적용했다. skin-ring과 lash pigment의 대응은 원저자 저작 정보가 아니며, 열린 eye2의 표본 투영 대조는 .0005289px로 기존 .0005 기준을 초과해 실패로 남겼다. 허용오차를 늘리지 않았다. 부분 Close/회전/실제 시간 연속·안검 유한P·새 GPU 통합은 **미검증/미적용**이다.
- 검증/보존: 독립 CPU/GPU864셀 불일치0, source packet6개/plane120개/완료 marker·색 출처 검사. 마지막19:43:30UTC Edit/dirty31, 실제 PlayerSettings 포함46직렬화 내용 동일. 만료된 임시 `ProjectSettings.asset` AssetImporter1개 unavailable로47/47 동등성은 주장하지 않는다. InputSettings 동일 객체22값·장치·옵션·시간·pipeline·globals 복원, RT30→30, Console 최신 tail 신규오류0. `Profiler.GetTotalAllocatedMemoryLong` 2015285815→2051378685(+34.42MiB)는 물리 WS/누수 판정이 아니다. 보호32파일·사용자30변경 보존, Assets import/SaveAssets/ClearDirty/GC/CUA/삭제/초기화/강제종료/push0.
- 다음 원인 검토: (1) strong parent 내부의 연속 source 색장과 연결된 약한 painted child를 별도로 보존하는 기준, (2) source 곡선의 공동 래스터 제약을 셀 면적 선택 **앞**에 연결하되 실제 가림과 유한 pigment P를 함께 지키는 방법. 현재36영역을 단일색으로 납작하게 만들거나7셀을 전역 예산으로 승격하는 후속은 금지한다. Argon에 직접 연락하지 않았으며 이 최신 인계/스크립트/실패 캡처로 검토 가능하다. 관련 로컬 커밋은 `git log -- experiments/pixel-pipeline/2026-11-01-source-regions104-lid105`로 찾는다.

### 106 — 105 곡선 후보의 실제 GPU 이식과 남은 분절

- 최신 비교: `experiments/pixel-pipeline/2026-11-01-live-lid-curve106/INDEX.html`. **제품77 유지**. 추가한 Unity 자산은 격리 `Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye106.compute`와 `.meta`다. C#은 Assets 밖에서 동적 컴파일했고 프로젝트 C# import/recompile·씬/재질 저장은 하지 않았다. 105의 Close100 제한을 제거해 현재 변형/회전/소수 위상에서 실제 GPU가 선택한다. 원래 source 곡선과 색소를 연결했지만 전체 알고리즘 채택은 아니다. 6+2셀 하드코딩 없음.
- 코드 색인(같은 실험 폴더): `SourceCurves106.Upper/Update/Upload`는 기존 `REGISTRATION89` native skin-ring 상부 chain을 현재 evaluated mesh→등록 source 좌표→현재 공개 `eyeInverse`→공통 연속 anchor로 투영한다. 작가가 그린 lash-pigment contour 복원이라고 주장하지 않는다. `ForwardCanvas106.Record/Draw/Compose`는 clean Layer0→102 전체 눈 선택→`ApplyCurve106`→원본색 직접 대입→외부 머리 depth/coverage 순서다. `CurveSupport106.hlsl::Intersects106/ApplyCurve106`은 같은 셀·같은 눈의 확정 가시 native 안검 표본만 사용하고 source RGB/depth/owner를 직접 복사한다. 원래 홍채·흰자 선택은 유지하며 충돌을 audit2로 남긴다. RGB 평균/최종×g/오프라인 색 재생/정해진 셀 수 없음. `MotionClose106`, `Sequence106/HoldClose106`는 관찰기이며 알고리즘에 테스트 상태를 넘기지 않는다.
- 실제1 Play, 51캡처 상태: evaluated Close 0/25/50/75/100/75/50/25/0의9상태, 열린 위상10/보행8/회전10, 닫힌 위상4/회전10. **51연속 프레임이라는 뜻은 아니다.** 정상 Gameplay397.Present/history 경로다. `analyse106` CPU float32 기준과 실제 GPU 7,500셀 불일치0, 매프레임 곡선 CPU 업로드/GPU readback 동일, 765개 plane의 frame/serial/sourceId 일치. `verify106.hair`의 동일 source-depth/coverage/RGB/owner 규칙으로 두 경로의 외부 머리 가림 채택8,180회를 정확히 재현했다. 원본 source·가림을 무시해 연결한 결과가 아니다.
- frame107 완전 Close는 기존102 안검1→14셀, 실제 source 곡선/색소의 교집합으로 양쪽 각각4연결7셀이다. 목표14셀을 강제하지 않았다. frame99→115 재개방 eye RGBA/owner가 정확히 같다. 모든51상태 홍채·흰자 colour/identity를102와 동일하게 유지했고 source 팔레트 밖0. 그러나 이것은 전체 눈 공동 할당 성공이 아니다. **부분 Close/회전 분절 미통과**: frame101 canonical(3,3)은 같은 eye 확정 색소4표본이 있어도 기존 홍채·흰자 보호와 충돌한다. 해당 프레임 보호 충돌6셀/색소 표본 없음2셀. frame192는 실제 얼굴 가림5셀/색소 표본 없음1셀이다. 4×4에 표본 없음이 연속 원본 색소의 부재를 증명하지는 않는다. `VERIFICATION106.json`에 전체 좌표/원본 alpha/visibility/owner를 남겼고 `review/RESIDUAL_GAPS106.png`로 직접 확인했다. 없는 source를 채우거나 실제 가림을 뚫는 처방은 하지 않았다.
- 위상은 실제 root projection x=218.899→219.899px로 측정했다. 열린10/닫힌4 상태의 source-local shape ID는 각1종이다. 단, 열린 안검 native bilinear RGB8은 최대2코드 변한다. 예: eye2 local(-6,-1), 같은 primitive102/sample(9,12), UV(.153010517,.566202641)→(.153031349,.566092491), RGB8[221,204,184]→[223,205,186]. 선택 후 조명 곱셈이 아니라 원본 UV 표본값 변화이며 유한 안검 팔레트는 여전히 미완이다. 이 결과를 전체 시간 안정성으로 확대하지 않는다.
- UV 정보 감사 `uv_input_audit106/UV_INPUT_CONTRACT106.json`: 실제 face/eyeline의 baseColor와 shadeMultiply가 각각 **같은 PNG**를 공유한다. normal·alpha/outline·native geometry·기존 parent/iris·blink morph는 있으나 별도 볼 칠/음영 layer/feature mask는 없었다. PNG는 IHDR/IDAT/IEND만 있고 정확한 모델 Input 폴더에는 DCC layer 파일이 없다(전체 드라이브 부재 주장 아님). 재질ID≠painted region, source에 그려진 gradient≠현재 조명g.104의 동일 skin parent8 내 약한 볼 칠 반례는 유지하고 새 임계값/색 수 탐색은 하지 않았다. 최소 계약은 unchanged unlit RGBA+UV/texture/sampler provenance, 강한 parent와 약한 연결 child/불확실성의 계층, source-tone과LightQ 분리, 평면P로 축소하기 전 보존/색손실 정책이다. 필요시 authored mask를 추가 단서로 쓴다.
- Argon 검토 질문(직접 연락하지 않음): (1) 약한 연결 무늬를 보존하면서 finite-width AA 전이와 연속 gradient를 분리할 공동 목적함수는 무엇인가? (2) region 하나를 평면 anchor 하나로 붕괴시키기보다 source field/tone을LightQ와 분리해 유지해야 하는가? (3) skin-ring 곡선과 실제 안검 색소를 함께 쓰며 홍채·흰자 보호와 충돌하는 셀을 공동 재배치할 때 어떤 형태/가림 제약을 우선해야 하는가? 현재106은105의 GPU 이식이며 이 질문을 해결한 전체 solver가 아니다.
- 종료/보존:20:08:20UTC Edit/compiling=false/scene clean, dirty31 목록 동일. 가능한46개 직렬화 내용(실제 PlayerSettings 포함) 동일, 임시 ProjectSettings AssetImporter1개는 unavailable이므로47/47 주장 없음. InputSettings 동일 살아 있는 객체/22값/장치, background·Play옵션·pause/time·pipeline·global 복원. 소유 자원만 Dispose, 빌린 버퍼 미해제, callback 제거, 보호32파일 hash/기존 사용자30변경 유지. RT30→30, Console error0→0. `Profiler.GetTotalAllocatedMemoryLong`20:06:06.979 2,023,734,580→20:06:53.059 2,059,362,295bytes(+33.98MiB), 물리WS/누수 확정값 아님. 이번 실행은 단일 view이며 실제 다중뷰/모델 교체 회귀는 미수행. 금지 동작0, 승인 차단0.
- 재검사: `recheck106.py`는 `RAW106.zip`의51개 실제 GPU packet/7,500셀/1,377파일 hash를 독립적으로 읽어 CPU 기준·source 증거를 검사한다. CPU fixture 검사이지 새 런타임 실행/성능 측정이 아니다. `RAW106_INDEX.json`, `RESULT106.json`, `VERIFICATION106.json`, 전체 PNG/Close·회전 WebP가 증거다. 이번 관련 커밋은 `git log -- Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye106.compute experiments/pixel-pipeline/2026-11-01-live-lid-curve106`로 찾는다. 미해결 피부/두피/볼 분할·native 안검 유한P/외곽선·partial/rotation 공동 배치를 가리고 완료라고 보고하지 않는다.

### 107 — 실제 공동 가시성·표본화 원인 검증 / 전체 후보 미채택

- 최신 비교 `experiments/pixel-pipeline/2026-11-01-joint-visibility107/INDEX.html`. **제품77 유지,107 전체 후보 미채택**. 추가 Assets는 격리 `EyeBoundaryRestore348/Shaders/ForwardEye107.compute`와.meta뿐이며 C#은 외부 동적 컴파일이다. UV 영역화 임계값 탐색·6+2셀·최소 셀 수·피부 전체 무시·최종RGB×g·색 평균을 추가하지 않았다. 관련 커밋은 이 실험 경로 및compute 경로의 `git log`로 찾는다.
- 코드 색인: `JointCurve107.hlsl::Contributions107/ResolveCurve107`은 세 파츠를 같은 source 표본 위치에서 깊이/가시 기여로 비교한다. 깊이동률은 구간으로 남기고 array 순서로 결정하지 않는다. `ForwardCanvas107.Record/Draw`는102와106과107을 같은 프레임 입력으로 실행한다. `NativeDense107`은 원본 NativeRetarget96과 같은 bounds/anchor에서8× 표본을 생성하고, `WholeEye107.Query`의 전용 `Evidence107` 버퍼는 실제 앞쪽 face triangle/UV/depth/alpha bound만 기록한다. `LiveSurface107/WholeEye107`은 view별 소유 자원이며 global buffer 덮어쓰기나 런타임 GPU→CPU readback이 없다(관찰기만 bounded readback). 모든 shade/Q/팔레트 경로를 바꾼 완성 renderer가 아니다.
- 원인 분리: 동결106 frame101 보호6셀 중4셀에는 실제 앞쪽 가시 안검 표본이 있고2셀에는4× 안검 표본이 없다. 예 `(3,3)` 안검Z13.71098<기존 홍채Z13.71486. 그러나 이것만으로 전체 셀의 기존 홍채가 틀렸다고 판정할 수는 없다. 같은 셀 내부의 서로 다른 위치/면적을 구별해야 한다. 원본 새 sourceId에서 재현한8×는 frame101 `(14,3)/(7,4)`에 가시 색소2/1개, frame192 `(3,9)`에1개를 보여4× 표본화 손실을 확인했다. 색을 발명해 선을 연결한 것이 아니다.
- 측면frame192의5셀 `(4,4),(5,4),(4,5),(3,6),(4,6)`은 별도다. 같은 프레임의 실제 evaluated triangle/rest/UV와 **실제 Query view/projection**을 저장하고 `rayproof107`로157개 ray를 독립 재계산했다. 모두 source renderer1/submesh3의 앞쪽 얼굴과 alpha bound[1,1]이 확인됐다. GPU와 depth 오차최대2.3352e−6, UV1.7892e−6. `RAY_PROOF107.json`은 이 표본 범위의 기하/alpha bound 근거이며 모든 native derivative AA의 동등성은 주장하지 않는다. 실제 가림을 보호정책 오류로 지우지 않았다.
- 실제 실행 이력: 첫107 Play는 지연 D3D11 컴파일의 bool `|=` 오류로0캡처 후 정상 종료. 공개 IsSupported/group 검사를 추가하고 논리대입으로 수정했다. 중간4× 공동판정은 실제51상태/7,500셀 CPU↔GPU0불일치였으나 hair 관찰기 사전검사에서 종료했다. 최종8×는 **54상태/7,959셀/1,350 plane/오류 없이 종료**, CPU↔GPU0불일치, source iris/white 팔레트 밖0. 부분Close9/열린 위상10·보행8·회전10/닫힌 위상4·회전10/partial25의 실제머리ON·OFF·복원3이다. 54연속 프레임이나 실제GPU 성능 시험이 아니다. 첫 실패와 중간 부분완료를 최종 성공 수에 섞지 않았다.
- 머리 관찰기 `Sequence107.Ready`, `HairDrawScope107.Inspect107/EqualDraw/RestoreHair`: 먼저 요청morph의 evaluated mesh가 실제 도달한 뒤 hair baseline을 잡고 draw 범위와 동적 bounds를 구분해 기록한다. 종료시 전체 descriptor와 index hash/renderer 상태는 정확히 복원한다. 이전100 검사 실패가 어느 세부 필드였는지는 당시 기록이 부족해 확정하지 않는다. 최종 ON/OFF/복원은 range 차이0/14(의도한 OFF)/0, bounds 차이0/0/0, 모든 복원 true다. OFF S4 머리 표본0/최종색=눈색, ON복원 눈RGBA·owner 정확히 동일. 최종RGB8 19픽셀은 원본 S4-rgba가 바뀌었고 meta/owner는 동일하며 각 프레임 출력이 그 입력과 정확히 일치한다. 해당 광원/셰이더 입력 변화의 더 세부 원인은 이번 버퍼만으로 확정하지 않는다.
- 통과와 한계: 최종 외부 머리 source/depth/coverage/owner/RGB 채택12,743회 재현, 재개방 눈RGBA/owner 동일. 실측0~1px 위상의 열린10/닫힌4 상태는 각각shape ID1종/RGB8변화0. 다만 native 안검 유한 팔레트·외곽선·얼굴/두피/볼 분할, 실제 다중뷰/모델교체·제품 성능은 미검증/미해결이다. 검증은 baseline을 함께 돌리고 readback하므로 실제 제품 성능으로 집계하지 않는다. shader integer-divide 성능 경고1개는 남았고 오류는 아니다.
- **미채택의 핵심 반례:** 107은 무조건 보호를 없앴지만 여전히 후단 곡선 표본 선택으로 셀 전체를 안검색으로 정한다. 실제 frame103 canonical `(12,4)`는 홍채 우세30/흰자27/안검2/바탕5 표본이고 visible mass .46875/.421875/.031127이다. 안검은 자기 표본에서 앞이지만 이것이 셀 전체의 올바른 승자를 뜻하지 않는다. `(5,4)`는 홍채 .796875/안검 .155626인데도 안검을 선택한다. 열린 홍채9→6, Close50 한쪽 홍채0이며 일부 분절도 남는다. 단순 count를 미술실패/성공의 유일한 근거로 쓰지 않고 **원본의 큰 가시 영역을 곡선2표본이 덮는 목표 누락**으로 기각한다. `FOCUS107.json`과 `MINIMUM_FAILURE107.png`가 같은 좌표의 원본 증거다.
- 다음 알고리즘 쟁점: 한 셀의 앞/뒤 판정을 전체 눈 공동 배치로 부르는 전제를 제거해야 한다. `WholeEye107.Select` 이전/동일 단계에서 원본 홍채·흰자·안검의 영역과 곡선 경로를 **함께** 재배치하고, source 가시성/외부 가림·특징 연결/형태·원본 재구성 오차를 함께 표현해야 한다. 현재107은 그 전체 solver가 아니며 102 고정도 곡선 우선 덮기도 정답으로 채택하지 않는다. 이 반례는 이미 확보된 dense8/geometry/source family 데이터로 다음 오프라인 설계를 검증할 수 있다. 추가 캡처 부재/서버 승인 탓으로 돌리지 않는다. Argon 질문은 “곡선의 제한된 격자 오차와 큰 홍채·흰자 영역을 공동 보존하도록 어떤 source 기반 목적/제약을 세울 것인가”이며 외부에 직접 연락하지 않았다. UV 기존 입력계약은106을 유지한다.
- 보존: 마지막20:40:11UTC Edit/compiling=false/scene clean/dirty31 목록 동일. 가능한 직렬화46개(실제 PlayerSettings 포함)·동일 InputSettings 객체22값/장치·옵션/time/pipeline/globals 복원, 임시 AssetImporter1개 unavailable. 보호32파일/기존 사용자30변경 유지, RT30→30. `Profiler.GetTotalAllocatedMemoryLong`20:38:20.819 2,049,611,314→20:39:14.166 2,085,436,999bytes(+34.17MiB), 물리WS/누수 확정값 아님. Console의 과거 실패 오류9개는 보존됐으며 최종 실행에서 추가된 오류0. 강제정리/GC/SaveAssets/CUA/초기화/삭제/강제종료/push0, 승인 차단0. 최종 palette/region 미완을 눈 가림·표본화 진단으로 가리지 않았다.


### 108 — 107 저장 입력의 공동 라벨 목적함수 검증, 미채택

- 최신 비교: `experiments/pixel-pipeline/2026-11-01-joint-objective108/INDEX.html`. 새 Play/Unity 호출/GPU/Assets 변경0, 제품77 유지. 107 실제54상태와 별도105 닫힌 눈1상태의 sourceId를 분리했다. 원본544파일 해시/float32 기여880표본 일치, 동결55fixture를 함께 보존한다. 현재 Editor 상태는 새로 조회하지 않았으며 이전107의 Edit/dirty31 관측을 현재 사실로 갱신하지 않는다.
- `joint108.problem/solve/mincost_fixed/data_best/path_sets`와 `MODEL108.json`: 셀당 단일 라벨·출처/관측 지지·part 비소실·기준곡선 경로를 분리하고, 영역 질량 L1과 관측 라벨 불일치 대용 비용을 가중합 없이 비교한다. M안은 질량→데이터 사전식, D안은 데이터 최소다. 입력을 dyadic 정수 비용으로 바꿔 동률을 정확 판정한다. 최소비용 흐름은 공동 할당용이며 연결성은 모든 단순 경로 집합의 별도 열거다. 눈 사이 후보 셀 겹침0을 확인했기에 분해 가능했다. 전체 Pareto 전선이나 지각적 가독성 최적화가 아니다.
- 확정 반례: F103 `(12,4)`의 iris30/white27/lid2/canvas5 및 mass .46875/.421875/.031127/.078248에서 공동 M안은 홍채를 유지하고 전체 I/W/L=1/2/3으로 배치한다. 안검 한 표본으로 셀 전체를 덮는107 전제는 제거했지만 원형·읽힘 성공은 아니다. 같은 눈의 안검 질량2.874339셀과 기준곡선 연결 최소4-neighbour7셀/8-neighbour6셀이 충돌한다. ceil(질량)=3 상한과 연결을 동시에 강제할 수 없으며 이 면적 상한을 미술 규칙으로 채택하지 않았다.
- 기준곡선은 여전히 registered **skin-ring upper arc**이며 실제 색소 윤곽 검증이 없다. 같은 셀의 확정 색소 지지를 강제한 S안+4연결은 가시104눈 상태 중53불가능. 같은 눈의 관측 footprint 안 재배치를 수학적으로 허용하면 그중32개가 가능해진다. 원래 투영 위치 잠금 역시 과제 설정의 가정이지 사용자 요구가 아니다. 완화 R안은 목적지 carrier 깊이/가림·source 표본 운반이 미정이므로 렌더 가능한 후보로 채택하지 않았다. 불가능 판정을 보정 자체의 불가능으로 확대하지 않는다.
- 닫힌105는 M안3+3셀/D안1+1셀로 선이 끊기고, 곡선4연결은7+7셀로 과장된다. F105 부분Close75 eye2의 홍채 `(4,5)`/`(5,5)`는 질량 .897337582/데이터4.878437346의 정확 동등해다. 순회 순서나 미세 가중치로 숨기지 않았다. `EVIDENCE108.json`, `MINIMUM_CONFLICTS108.png`, `JOINT_MODEL108.png`는 같은 좌표와 상충을 보여준다. PNG의 후보 색은 라벨 진단이며 새 최종 RGB가 아니다.
- `check108` 재현: 작은 검사432, 정수비용/동률329, 독립 완전열거36 ROI, 실제440눈/정책 계산, 회전·반사 목적값16검사 통과. 시간 연속성·완성 미감·최종 palette/outline/외부 머리 가림의 신규 검증은 아니다. `CODE_INDEX108.json`에 스크립트/함수/행이 있다. 관련 커밋은 `git log -- experiments/pixel-pipeline/2026-11-01-joint-objective108`로 확인한다.
- 다음 구조 검토 질문: (1) skin-ring을 실제 native 색소의 어떤 feature-local 경로/띠로 바꿀 것인가, (2) 중요 특징 공동 재배치의 source 표본·carrier·목적지 깊이/가림을 어떤 계약으로 연결할 것인가, (3) 동등해를 기존 원형·파트 상대배치·표면 history로 결정할 수 있는가. 현재 두 목적에 정보가 부족하다는 뜻이며 새 사용자 디자인 수치/새 캡처가 반드시 필요하다고 판정하지 않았다. GPU 경로는 추가하지 않았다. Argon에 직접 연락하지 않았으며 이 기존 handoff와 코드/캡처를 검토 근거로 유지한다.


### 109 — 원본 색소·carrier·source 원형/history 전제 검증

- 최신 비교: `experiments/pixel-pipeline/2026-11-01-pigment-carrier109/INDEX.html`. Unity 호출·Play·GPU·Assets 변경 0, 제품 77과 108 미채택 유지. 동일 프레임 105 전체 변형 메쉬, 실제 87의 23입력, 107/108 원본 동등해를 구분해 사용했다. Editor는 새로 조회하지 않았다.
- `native109.create_cache/locate_uv/section_centres/cache_key`: 실제 안검은 material6의 UV/mesh 색소 띠이며 skin-ring과 다르다. carrier texel 33,774개/24성분을 삭제 없이 캐시했고, 양 눈꼬리가 연결된 두 띠에서 UV·삼각형·바리센트릭 기준점 848개를 얻었다. 중간 4,312점도 실제 carrier/양수 alpha 안이다. RGB 평균이나 유일한 작가 skeleton 복원이 아니다. 키는 source rest/UV/topology/material/registration/policy에 묶고 포즈는 별도로 갱신한다. 현재 BLEND·identity UV·factor1 입력을 검사하며 임의 모델 분류 완료를 주장하지 않는다.
- `geometry109.prepare_packet`, `measure109`: 열린 눈·실제 Close100·reopen에서 skin-ring과 색소 중심 경로 차이는 최대 약 0.33~0.64px. 한쪽 색소 texel 26개/닫힘 63개가 기존 parent bounds+고정2 padding ROI 밖으로 잘린다(화면 면적 수치 아님). 범위는 실제 source footprint로 유도해야 한다.
- 실제 같은 연결 carrier로 37개 중심 후보를 대응했다. 105 frame104/eye1 `(12,4)`는 primitive22→20, 이동 0.5926px에 깊이가 6.515mm 달라져 source 깊이를 복사하면 틀린다. 중심이 다른 아래쪽 carrier인 2셀 `(3,5)`/`(14,4)`도 셀 안에는 올바른 기준점 38/74개가 있다. `footprint109.clip`은 실제 표면 조각 8/17개와 UV/bary/world/depth 장을 반환한다. 한 점의 앞선 깊이를 셀 전체 소유권으로 확대하지 않으며 면적 합을 depth-resolved coverage라 하지 않는다.
- 면적 정수 보존은 사용자 요구가 아니다. 닫힌 105의 관측 질량 2.621/3.427셀에서 108 질량 우선 3+3셀은 원본 색소 경로 길이의 51.4%/73.8%를 잃는다. 한 셀 폭 경로 진단 9/10셀은 면적이 6.379/6.573셀 늘고 한쪽 경로 3.9%는 ROI 밖이다. 둘 다 미술 성공이나 고정 셀 수로 채택하지 않았다. 면적·최소 선 표현·곡선 손실을 별도 기준으로 남겼다.
- `history109.canonical_rank/part_scores/pareto_indices/rank`: F105 동등해는 기존 immutable source bank 보존 비용만 추가해도 A의 홍채 1/3이 B의 1보다 낫고 흰자는 둘 다 6/5다. 부위 가중합·새 디자인 수치 없이 성분별 우세로 구분된다. source-key 이력도 A에 동의한다(F103→105 gap2, F105→109 gap4). 현재 가림을 먼저 적용해 완전 Close F107의 iris/white key0을 되살리지 않는다. 원형 source cache는 불변이고 이전 raster를 key-form으로 승격하지 않는다. 초기·충돌 이력·비교 불가능한 part 비용은 다중해 유지. source ID 분포만으로 모든 상대형상 보존을 증명한 것은 아니다.
- `motion109`은 실제 87의 23입력/인접 21쌍에서 848개 UV점을 현재 변형 메쉬에 연결했다(19,504대응, 실제 Close0→50→100→100→0). final label/RGB jitter나 end-to-end 위상 통과는 아니다. `check109`: raw58파일·정적7입력 해시, 축/순회/회전반사/키 무효화 11검사, 중간 4,312점, carrier37·표면조각25, 실제 동등해 회전반사/순회18검사 및 103/105/107/109 raw 재계산 통과. RAW109.zip 4.12MB와 원본을 보존했고 sibling107/108으로 history도 재현한다.
- 미검증: native24성분·파트 상대형태를 합친 전체 joint resolver, 모든 footprint의 depth/alpha/외부 머리 가림, 원래 alpha0인 목적지의 독립 조명·유한 팔레트·최종 RGB. current face geometry clear는 최종 가시성 통과가 아니다. GPU 표본 재투영 최대 0.000529px·source bilinear alpha 최대 0.001727 차이는 남겼으며 허용오차를 올리지 않았다. 직접 eyeInverse는 저장돼 있지만 적용된 head inverse/forward와 D3D 보간을 완전 복제하지는 못했다(`ARITHMETIC109.json`).
- 다음 질문은 “source 경로가 없는가”가 아니라 “실제 ribbon과 원형 비용으로 공동 라벨을 정하면서 목적지 footprint 가림을 어떻게 함께 해결하는가”다. 새 디자인 입력·추가 캡처가 반드시 필요하다고 판정하지 않았다. Argon에 직접 연락하지 않았다. 함수/행은 `CODE_INDEX109.json`, 커밋은 `git log -- experiments/pixel-pipeline/2026-11-01-pigment-carrier109`.


### 110 — 색소/carrier/source 형상 공동 resolver, 오프라인 미채택

- 최신: `experiments/pixel-pipeline/2026-11-01-joint-resolver110/INDEX.html`. 기준 `e26c58b3`; 이번 커밋은 `git log -- experiments/pixel-pipeline/2026-11-01-joint-resolver110`으로 찾는다. Unity/Play/GPU/Assets 변경 0, 제품77 유지. 저장107의19상태×양눈과 독립105 Close×양눈, 총40입력을 같은 규칙으로 계산했다.
- `fields110.build/FaceVisibility.query`, `separate110.problem_from_fields/exposure`: 삼각형 polygon·bary/UV/world/depth와 표본별 가림을 유지한다. 629개 carrier 셀에서 머리 앞/뒤 판정이 표본마다 달랐다. 외부 머리 가림으로 원형 배치를 다시 결정하던 오류를 분리했다. ON/OFF/복구의 배치 후보 집합은 양눈 모두 정확히 같으며, 측면 Close의 잠재 안검3셀은 기록 표본 노출0이다. 이는 최종 RGB 렌더 검증이 아니다.
- `resolver110.solve/feasible`: 세 파트가 하나의 셀 변수를 공유하는 유한 CSP. 면적 반올림·우선순위·고정 셀 수·RGB 비용 없이 source→픽셀 사각형/픽셀 corner→source의 최대 기하 오차를 최소화하는 명시적 가설이다. F103 `(12,4)`의 조건부 해는 홍채이며 안검2표본을 셀 전체 소유권으로 확대하지 않는다. 같은105 실제 색소 경로 누락은108의51.38%/73.84%에서2.49%/8.13%이나, 안검3+3셀→7+8셀로 넓어진 대가가 있다. 미관 성공으로 채택하지 않았다.
- `identity110.rank_with_relative/relative_form`: source-ID 분포만 같아도 원형 모양은 다를 수 있어 source 쌍의 상대 좌표 오차·누락을 별도 Pareto 차원으로 추가했다. History는 동일한 현재 형상 비용 사이에서만 사용하고, 현재 Close/가림을 무효화하지 않는다. Native 연속 UV interval의 완전한 형상/history 및8× 홍채·흰자 source ID는 아직 미검증(현재 실제 ID는4× 입력).
- `reconstruct110.recover/checks`: 105 Open/Close와107의 현재 head·실제 Close(누락 시 교정 정점 깊이 추정)의 재구성 가설이다. 독립54상태 최대0.001584px/1.963µm, 별도2프레임 정점 최대1.421µm. 105=107의 정확한 동일 상태/전체 표면 증명이 아니다. 저장375파일은 기존107 동결본과 byte 동일. 24개 유한 좌표 perturbation에서 검사한 최적 라벨 집합은 같았지만 전체 오차구간 증명은 아니다.
- 미완: `COUNT_RANGE110.json`의 정확한 feasibility 검사에서 F99 눈1은 같은 기하 최적값에 홍채1~5셀이 모두 가능하다. 64해만 열거한 조건부 선택을 유일 해/전체 Pareto로 부르면 안 된다. 원형 상대 배치 기준과 완전한 최적해 선택이 더 필요하며 아직 디자인 셀 수를 사용자에게 요구하지 않는다. 최종 팔레트/외곽선/시간 안정성/GPU 통합은 미완이다. 새 메쉬 캡처로 이 목적함수 동률은 해결되지 않는다.
- `check110.py`, `audit110.py`, `NEXT_INPUT110.json`: 독립 작은 완전탐색24, quota 진단40, 실제 D4/순회18, GPU 가림173증거와 footprint 검사. 다음 직접 캡처는 평가 정점 약49KB·실제 적용 행렬·source 색소 경로의 실제 가림 query·bounded dense source ID가 재구성보다 정확하고 저렴하다. 현재 offline adapter 수초/CSP 수십ms는 실시간 GPU 성능이나 상한이 아니다. 소유/다중뷰/모델 교체/무효화 계획만 작성했으며 새 실행은 하지 않았다. 세부 함수/행은 `CODE_INDEX110.json`.


#### 110 검토 정정과 질문 3개 — 구현 f2c23332 기준

**판정:** 현재 정식화와 탐색 구현이 충분하지 않다. 모든 원본 정보로도 특징을 구별할 수 없다는 원천적 불가능성은 증명하지 않았다. 아래는 코드/저장 결과의 읽기 대조이며 새 실험·캡처·설치·Unity 변경은 없다. 사용자에게 새 셀 수를 선택하라는 질문이 아니다.

1. **원형의 어떤 관계를 공동 최적화의 제약/우선 기준으로 삼아야 하는가?** `resolver110.py:17 distances`, `:120 solve`의 1차 목표는 source점→픽셀 사각형과 픽셀 corner→source의 최대 거리 하나다. 최대값을 유지하면서 내부 표현·폭·면적·source 쌍 배치를 달리할 수 있다. 원형 bank 전체의 경계/인접·파트 상대 관계를 hard invariant로 둘지, 어떤 변형 오차와 함께 비교할지 아직 정식화하지 못했다. `identity110.py:18 conditional_l1`은 현재 available key 안에서 분포를 정규화하며, `:67 observed_key_centres/:78 relative_form`은 불변 bank 경계 대신 매 프레임4× 관측 key 중심의 상대 좌표·누락 쌍을 soft Pareto 차원으로 비교한다. native 안검의 연속 UV interval 형태는 이 pair 기준에 포함되지 않는다. 최소 반례는 `check110.py:36 source_shape_counterexample`의 A+B 한 셀과 A/B 이웃 두 셀(같은 ID 분포, 다른 모양), 그리고 `separated/frame103-eye1-result.json`이다. F103은 기하 최적해32개 전체 열거 후에도 후보7/11/15가 남는다(I/W/L=1/4/7,1/3/7,2/3/7). 후보7→15에서 iris ID 오차는1/3→9/17로 악화되지만 상대배치 오차는29389/25088→538933/4239872로 개선된다. 이는 **전체 비용이 같은 세 해가 아니라 서로 우열이 갈리는 비지배 해**다. 어느 관계를 보존해야 하는지 기술 계약을 먼저 명확히 해야 한다.

2. **그 원형 기준을 첫64개가 아닌 전체 기하 최적해에 어떻게 결합할 것인가?** `resolver110.py:39 feasible`은 열거 상한에 도달하면 `enumerationComplete=false`로 중단한다. `separate110.py:55 main`은 그 표본 집합만 `identity110.py:94 rank_with_relative`에 넘긴다. `COUNT_RANGE110.json`의 F99/눈1, ε*=0.9875076811459061에서 iris1~5셀 가능하다는 것은 **bank/history 적용 전 1차 기하 최적 집합의 정확한 feasibility 결과**다. `count_range110.py:10 main`은 이미 확정한 ε*에서 각 count의 존재만 진단한다. `separated/frame99-eye1-result.json`의 첫64개는 전부 iris1셀이고, 그 안의 bank 비교가 후보61(I/W/L=1/7/6)을 조건부 선택했다. iris2~5셀 증인은 표본 밖에 있으므로 1차 해는 적어도68개지만 전체 개수는 미집계다. **원형/history까지 적용한 전역 최적해가1~5셀로 동률이라는 증거는 없다.** 전체 최적해를 제약식으로 유지하며 원형 기준을 공동 탐색할지, 완전성을 보장하는 후보 표현을 사용할지가 구현 검토점이다. 상한을 키우거나 순회 순서로 선택하는 것을 해법으로 간주하지 않는다. 최소 입력은 같은 폴더의 `separated/frame99-eye1.npz`, 결과 JSON, `COUNT_RANGE110.json`에 모두 있다.

3. **실제 가림·변형과 관측 누락을 나눠 availability/history를 어떻게 정의할 것인가?** `identity110.py:27 transport/:67 observed_key_centres`는 실제4× source ID를 사용하지만 1차 지원 영역은8×다. 기존 `experiments/pixel-pipeline/2026-11-01-pigment-carrier109/HISTORY109.json`의 F99에는 원형 iris key4개가 모두 실제 source에서 관측돼 있다. 반면110의 조건부 iris1셀 배정 histogram에는2개 key만 남는다. 따라서 이 최소 반례를 원형 정보 부재나 source 자체의 불가시성 탓으로 돌릴 수 없다. 별도로8× source ID 미캡처는 다른 상태의 sampling/실제 가림 구별과 대응 정밀도의 검증 한계다. `rank_with_relative`는 같은 현재 형상 비용 벡터 안에서만 이전 **ID 분포**를 비교하며, 연속 anchor·source-local 전체 shape의 변형/운반 규칙을 갖춘 시간 controller는 아니다. F99는 최초 프레임이라 history도 없다. F103은 history가 있어도 남은3개 형상 벡터가 서로 달라 history가 우선순위를 뒤집지 않는다. 동일 포즈 위상 F121/125/129는 실제 최종 시간 안정성 미증명이고, F204/207/210 머리ON/OFF/원복은 원형 배치 동일·노출만 변화, F192 안검3셀은 표본 노출0이라는 경계조건이다. `separate110.py:20 problem_from_fields/:36 exposure`의 원형 배치와 외부 가림 분리는 유지해야 한다. 검토할 것은 source-local canonical shape와 현재 변형/실제 가림을 먼저 대응한 뒤 history를 제한하는 규칙이지, 화면 좌표/RGB 고정이나 blink 복원 규칙이 아니다. 정확 검증용 평가 정점·실제 행렬·dense source key/UV·색소 경로 가림 입력의 누락은 `NEXT_INPUT110.json`에 구분돼 있다. 새 캡처는 이 관측 한계를 줄이지만 질문1·2의 목적/탐색 누락을 자동으로 해결하지 않는다.

최신 저장소만으로 위 검토가 가능하다. 읽기 순서는 이3문항→`experiments/pixel-pipeline/2026-11-01-joint-resolver110/INDEX.html`→명시한 함수/최소 JSON·NPZ다. frozen107/109 입력과 작은105 보충 자료도 같은 저장소에 있다. f2c23332의 frozen-input 재현은 통과했지만, 여기서 새 실행을 추가하지 않았다. 외부 Argon 통신은 하지 않았고 이후 임의 후보를 시작하지 않는다.


#### Argon2.2 경계 역할 검증 — 오프라인, 제품77 미적용

- 원문은 `C:\Users\15352\Desktop\Argon2.2.md`(14752bytes), SHA256 `97ed2bf4efbf24136ec9769256abb6eb5aa0bfa28457bb71ef6fc9572631c3d4`. 수정하지 않았다. 2/2.1의 Layer0·눈·외부 머리 가림 분리를 유지하며, 새 문서는 참고 분석이지 구현 성공 증거가 아니다. 원문·이전 문서 해시는 `experiments/pixel-pipeline/2026-11-01-argon22-boundary/DOCUMENT_PROVENANCE.json`, 정확한 원문 사본도 같은 폴더 references에 있다. 이 절을 추가한 커밋이 해당 실험 보존 커밋이며 기존110 구현은 f2c23332, 검토 정정은 b354cc71이다.
- **변경한 전제:** 실제109 native 색소 곡선을 면적 경쟁 파트가 아니라 위쪽 개구부 경계로 취급한다. `aperture22.py:12 column_rows`는 등록된 canonical 열마다 곡선 호 길이 가중 중심의 floor 행을 구한다. 피부 ring이 아니며, 해부학적 경계 또는 보편적 미술 정답이라고 인증하지 않는다. 전역화면 x 규칙은90도 회전6→2셀/급경사 행3·2칸 점프 반례가 있다. 현재40입력의 눈 로컬 frame에서만 검사했다. 문서의 strict1행 설명과 I+W=0이면 아래도 안검인 식은 같지 않아서 strict 설명만 시험했다.
- **3셀 carrier 정정:** `verify22.py:15 main`에서 source 셀을 이동 후 화면 위치의 geometry로 재검사하던110 추가 제약을 분리했다. F105·109 눈1 x10/y4, F147 눈1 x10/y5에는 현재 source 색소 표본이 있다. 기존102는 source 셀→display 매핑이므로 source 기준에서는 누락0이다. 이것이 단일 source 깊이로 목적지 셀 전체를 소유하게 할 근거는 아니다. footprint별 UV/깊이/alpha 및 외부 머리 가림은 최종 합성의 별도 조건이다. 기존 ROI 밖 곡선이 있는17입력은 source 유래 bounds 확장이 필요하다.
- **문서 방향의 잔여 반례와 최소 구현:** 경계 아래에102의 셀별50% 문턱을 유지하면 Close75 눈1 흰자0.861829셀, 눈2 홍채0.78125·흰자0.34375셀의 실제 가시량까지 전멸한다(4개 눈/상태). `interior22.py:17 allocate`는 EyeUnion 전체 면적 오차→I/W 면적 오차→source 재구성 오차를 비교한다. 안검 면적 quota나 고정 눈 크기는 없다. 면적만 적용하면5입력에서 연결된 원본 홍채가 분절된다. `:74 allocate_topology`는 연결된 immutable 홍채 bank와 현재 확실한 source 지원 그래프를 함께 제약으로 사용한다. 흰자 bank는 실제로 여러 클러스터라 무조건 하나로 잇지 않는다. 모든 최적 배치를 열거한 뒤 source를 비교하며 이 작은 문제의 임의 표본64개를 최종 해로 삼지 않는다. 12개 완전탐색 oracle, 내부 배정 D4검사96개 통과(`check22.py:21 main`).
- **source 형상 비교 정정:** `form22.py:12 rank_source`는 관측된 상대 source 쌍이 없을 때 geometry 오차를0으로 만들지 않고 null로 기록한다. 기존 source 대응 손실은 유지한다. F105·109 눈2의2후보는 이 정정 후 현재 비교에서 하나로 좁혀진다. history/가중치/첫 후보 순서를 사용하지 않았다. 미측정 geometry와 실제 오차를 비교하지 않은 것이며, 모든 문제의 유일한 미술 해를 증명한 것은 아니다.
- **실제 결과:** 저장된38개107 눈/상태+독립105 완전Close2개=40입력. source가 연결된 홍채의 새 분절0, 가시 EyeUnion 전체 소실0, 완전Close I/W 재생성0, 위상 F121/125/129(0/.5/1) canonical 배치 집합 동일. 이 결과는 저장자료의 오프라인 label 검사다. 최종 RGB·외부 가림·팔레트·외곽선 및 새 시간 안정성 검증은 하지 않았다. Close75 눈2는 source 흰자0.34375가 있는데 현재 영역 예산에서는 생략되며, 모든 양의 alpha를 무조건1셀로 늘리는 규칙도 정당화되지 않았다. 작은 흰자/원형 클러스터 상대관계는 미해결이다. GPU·제품 적용은 없으며 현재 Editor 상태도 새로 조회하지 않았다.
- **탐색 정정 유지:**110의64는 열거 상한이다. F99 눈1 iris1~5는 bank/history 전1차 기하 최적 범위이며 적어도68해, 전체 수 미집계다. F103의32는 해당1차 문제에서만 전체 열거했다. 이번 조건부 후보가 이 이전 탐색 불완전성을 일반적으로 해결했다고 주장하지 않는다. 현 실패는 정식화·비교 규칙의 부족이며 현 입력으로 원천 구별 불가가 증명된 것이 아니다.
- **경로/재현:** 같은 폴더 `INDEX.html`, `ARGON22_BOUNDARY_ABLATION.png`, `STATUS22.json`, `CODE_INDEX22.json`. 그림 왼쪽은 기존 GPU77이고 나머지는 false-colour label이며 새 GPU 렌더가 아니다. `verify22.py → report22.py → region22.py → region22.py --topology → check22.py → finish22.py` 순서, Python+기존 NumPy/Pillow 사용. 원본/frozen 입력은107~110 형제 실험을 재사용한다. 실시간 구현은 아직 없고, 정확한 offline subset 열거를 매프레임 GPU 경로라고 부르지 않는다. 입력당 후보는 현재 I≤9/W≤12지만 일반 실행 예산은 미검증이다. 이번에는 Unity/Play/GPU/Assets/사용자설정 변경0, 별도 Argon 통신 없음.

**남은 검토 질문(3개):** (1) UpperLine의 source 색소 중심/아래 경계 중 무엇을 개구부 제약으로 삼고, 단일값 열 표현이 실패할 때 기존 native 곡선/feature frame으로 어떤 연속 경계 계약을 보존할 것인가? (2) 원형 bank의 분리된 흰자 클러스터·파츠 상대관계를 현재 가시 source와 어떻게 공동 보존할 것인가? Close75의 작은 흰자 생략은 단순 셀 수 요청이 아니라 EyeUnion 면적 오차와 작은 중요 파트 표현의 충돌이며, 한쪽만 무조건 우선하면 이전 실패가 반복된다. (3) 현재 source-ID 지원과 footprint별 깊이/alpha를 source→display 재배치 및 실제 source-local history에 연결할 때, 실제 Close/외부 가림이 우선하면서 새로운 분절을 만들지 않는 어떤 조건을 hard invariant로 둘 것인가? 위상 배열 동일을 최종 시간 안정성으로 대신할 수 없고, 미측정 final RGB/coverage를 추정으로 채울 수 없다.


#### 111 실제 source/목적지 carrier 검증 — 제품77 유지, 공동배정 미통합

- **새 실제 입력:** 두 정상 Play에서12+12상태를 새 sourceId로 캡처했다. 107/110의 추정 기하를 섞지 않았다. `experiments/pixel-pipeline/2026-11-02-eye-carrier111/geometry111.py:load`는 같은 프레임의 직접 평가 world/rest/UV/삼각형·재질과 현재 head/camera/등록행렬을 읽는다. `analyse111.py:source_components`는 실제8× rest/역할/RGB를 사용하며 nearest source key를 쓰지 않는다. 원래4× source-ID와8× 질량 차이는 별도로 보존했다. `RAW111.zip`은 완료 marker/sourceId/frame/serial 검증 뒤 선택한24입력이고, 미저장 native 설정 백업·relay/인증 로그는 커밋하지 않았다. 원본 백업은 작업폴더에 유지했다. `replay111.py`, `check111.py`는 저장소 사본에서 frozen 입력으로 통과했다.
- **흰자 소실의 확정 원인:** Close75 새F105/눈2에도 source 흰자0.34375, 홍채0.78125셀의 확실한 가시량이 있다. 원래 흰자2성분 중 한 성분이며, 실제 가림으로 완전히 사라진 것이 아니다. `allocate111.py:solve`에서 면적 우선은 EyeUnion1.125를1셀로 줄이는 오차를 먼저 최소화해 흰자를 생략한다. source 성분 손실을 먼저 비교하는 별도 후보는 고정 최소 셀 수 없이 그것을 남긴다. 하나의 출력 셀이 여러 source 성분을 대표할 수도 있는 반례를 포함해20개 완전탐색 oracle/내부 D4검사160개를 통과했다. 이것을 모든 작은 양의 alpha에1셀씩 주는 보편적 규칙으로 채택하지 않았다.
- **최종 목적지의 두 번째 절단:** `ray111.py:carrier_at/FaceRay.query`, `analyse111.py:expose`는 source 색소, 실제 목적지 삼각형·UV·깊이, 얼굴 가림, 정확한 실제 머리S4 표본을 분리한다. 같은 흰자 셀(x3,y5)을 되돌려도 네이티브 조건에서는1~2/16만 보인다. 거의 가려진 잔여 coverage를 보존 성공으로 세지 않았다. `NativeSurface89`의 원래 I/W bank branch는 source 색을 공급할 때 native pigment alpha를 쓰지 않는데,111의 bank-off carrier는 원래 pigment alpha를 다시 사용했다. 기하 carrier와 옮길 색소를 혼동한 것이다.
- **실제 GPU에서 고친 범위:** 새 `Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/NativeCarrier111.shader:Eye333Fragment`의 `_CarrierGeometryOnly111`은 소유한 임시 재질에서만 기하 meta/rest/UV와 alpha1을 출력한다. 실제 face/hair occluder alpha 및 원본 source-bank RGB는 그대로다. 외부 C# `gpu-carrier/NativeGeometryCarrier111.cs:Bind`, `ForwardGeometry111.cs:Record/Draw/Dispose`로 정상 live Graph에 연결해12상태를 검증했다. shader만 import했고 C# Assets import/domain reload는 없었다. 첫 import 명령은 using 배치 오류로 실행 전에 컴파일 실패했으며 수정된 Import111Gb가 통과했다. 원본12+수정12의 GPU query 표본1728개가 CPU 재계산과 차이0이다. 수정12의 carrier alpha는 실제 GPU에서 모두1, source8× key/RGB 검증도 불일치0이다. 재투영 수치 잔차 약0.000315px는 기록했으며 일반 정밀도 보장이 아니다.
- **기존 bank/가림 계약의 미해결:** `EyeFeature348.Initialise`의 UV7 owner는 얼굴 전체를 가까운 눈 기준으로 나눈 값이다. 실제 안검 표지가 아니므로 owner2라는 이유로 얼굴 피부 전체를 무시하면 안 된다. `canvas111.py:source_domain`, `layer_ablation111.py`는 원본 bank footprint만 바탕으로 묶는 제한적 가설을 구현했다. 이 가설에서 같은 canonical 흰자는 머리OFF2/16→12/16, ON에서는 실제 머리가 가려3/16이다. ON/OFF/복원 전 canonical 배치 집합은 동일하다. 그러나 홍채에는 원형 bank 상대배치가 고른 후보도7/16 등 불충분한 support가 남고, bank 범위가 실제 native 안검 영역이라는 증거는 없다. 이 가설은 GPU/제품에 적용하지 않았다. `form111.py:rank`는4× nearest 운반 대신 실제8× source-ID로 전체 후보를 비교하지만, 그것이 목적지 support 계약을 자동 해결하지 않는다.
- **정확한 적용 구분:** 실제 런타임에 연결된 것은 source/기하/query 입력과 geometry-only carrier 수정이다. 2.2 경계·성분 공동배정기는 아직 오프라인이며, cache의 전체 눈 support를 유지하는 변형 carrier/내부 바탕·실제 lid 소유권 규칙과 GPU 선택·최종 합성은 미구현이다. 검증되지 않은 bank 평면 깊이/피부 전체 무시/픽셀 수 고정/미확정 투명 처리를 쓰지 않았다. 유한 팔레트·외곽선은 별도 미완이고, 새 최종 RGB를 만들지 않았다. 고정된 원본 물리 mask의 재표본화만으로 특징이 보존된다는 전제가 다시 드러난 것이며, 정보론적 불가능성이 증명된 것이 아니다. 다음 검토는 source-local parent/변형 cage에서 전체 stylized support를 어떻게 매핑하고, 실제 lid/Close를 내부 shape에, 외부 face/hair를 footprint 가림에 각각 적용할지라는 소유권 정식화다. 사용자에게 눈 셀 숫자를 고르라는 질문이 아니다.
- **실행/복원:** 마지막 공개 조회2026-11-01 23:52:44UTC에 PID35364/Edit/compiling=false/scene clean/dirty31. 두 실행 모두 입력 설정 동일 살아 있는 객체·JSON·장치, 옵션/시간/pipeline/background/global 복원, 소유 carrier 자원 해제/RT30→30 확인. 직렬화47개 중46개 동일, 조회 불가1개는 PlayerSettings가 아니라 AssetImporter 래퍼이며 PlayerSettings 본문은 동일하다. 보호32 디스크 파일과 기존modified30 보존. Unity `Profiler.GetTotalAllocatedMemoryLong`은 각 실행에서+37,219,134bytes/+27,061,987bytes 증가했고 OS working set 또는 누수 확정을 뜻하지 않는다. 원래 사용자 자원 정리/강제GC/SaveAssets/ClearDirty는 하지 않았다. 이후 Console 최근50개에서 Error/Exception0. 실제 프레임 사이에 gap이 있어 연속 시간 안정성 완성으로 부르지 않는다.
- **찾아보기/비용:** 같은 폴더 `INDEX.html`, `WHITE_CARRIER111.png`, `STATUS111.json`, `GPU_CARRIER111.json`, `CODE_INDEX111.json`, `RUNTIME_CONTRACT111.json`, `ANALYSIS111.zip`. 인물 이미지는 실제 GPU77이며 role/표본 마스크는 진단이다. source 후보≤9I/12W는 관측값이고 offline 완전탐색을 realtime 구현이라고 부르지 않는다. 실제 GPU 시간은 측정하지 않았으며 CPU시간으로 대체하지 않았다. product에는 GPU→CPU 동기 feedback을 추가하지 않고, view/renderer별 소유·model/topology/UV/bank 변경 무효화·실패 해제를 갖춘 GPU/DP 경로가 필요하다. 본 절과111 실험·새 격리 shader2파일만 선택한 커밋이 현재 단계의 보존 커밋이다. 이전2.2는 d774c151. 외부 Argon과 직접 통신하지 않았다.

#### 112 support 연결/안검 소유권 감사 — 제품77 유지, 의존 런타임 단계 보류

- **확인된 연결:** `experiments/pixel-pipeline/2026-11-02-eye-support112/source112.py:Source.map_to_capture`, `support112.py:Support.__init__`는 원본 VRM의 명시적 `blinkLeft → morph15 → ring1`, `blinkRight → morph14 → ring2`를 사용한다. 각 ring은24정점이며 가까운 눈/재질명으로 재분류하지 않았다. source glTF→실제111 삼각형 인덱스는 순서(2,1,0), Unity UV는v반전으로 정확히 일치하고 Head-bind rest 오차 최대7.42e-9m다. **89의20개 I/W bank-cell native barycentric 대입과111의 실제 목적지 footprint는 이미 존재하며 모두 검증했다.** 이 자료가 없다고 판단해서는 안 된다. 원본 bank RGB가 native UV에서 처음 만들어졌다는 뜻도 아니다.
- **배제한 잘못된 소유권:** `EyeFeature348.Initialise`의 UV7는 얼굴 전체의 nearest-eye 태그다. 실제 source의 양안 blink 피부451정점/788삼각형은 두 눈 ring 모두에 연결되고, 단안 영향도 피부43정점에서 겹친다. blink는 눈썹50정점도 움직인다. 따라서 변형 영향권은 feature affiliation이며 안검/눈 내부 canvas의 불투명도 마스크가 아니다. `support112.py:Support.evidence/cache`는 그 구분을 명시하며 미정 피부를 투명 처리하지 않는다. 기존109의 실제 안검 색소848점은 별도 mesh/UV 경로이고2.2는 상단 경계 역할을 정의하지만, 주변 피부의 내부/외부 가림 소유권을 지정하지 않는다.
- **최소 반례/검증:** 같은 실제111 F105 눈2 canonical(x3,y5)는 흰자 source0.34375셀인데 물리 노출2/16이다. 가리는 source skin3의9삼각형은 실제 alpha가 모두1이며 blinkRight 영향권이다. 예: global17440/source primitive2061은 ring 접점0, 가까운 눈 태그2다. 같은 태그2의 global15820/source441은 blink 영향0이다. 어느 쪽도 태그만으로 안검/외부 피부를 결정할 수 없다. `audit112.py:main`의24개 직접 평가 상태에서 source 연결/cache 동일성, 머리ON/OFF/원복 전 intrinsic 배정 동일, Close/reopen을 검사했다. 완전Close I/W source는0인데 skin ring 면적은 눈1약1.113/눈2약1.764 canonical px²로 남아, ring 면적만으로 눈 노출을 복원하면 안 된다. `check112.py:main`은 입력/UV 불일치 거부, morph 변경 무효화, RGB 간격과 기하 독립 등17검사를 통과했다. frozen source subset으로 재현하며 새 Play/Unity 호출0, 보호32파일 해시 동일이다.
- **정확히 남은 계약:** 빠진 것은 I/W 기하나 추가 동일 프레임이 아니라 **공동 보정된 전체 눈/캔버스가 원본 피부를 어떻게 함께 변형·재배정하며, 어떤 피부를 내부 안검/외부 occluder로 남기는지**라는 닫힌 source-local 표면·가림 transfer다. native ring→authored parent 등록과 bank-cell 점 대입만으로 셀 전체 소유권을 확대할 수 없고,2.2의 상단 행 규칙만으로 그3D 대응이 정해지지 않는다. 원본 asset에 그 의미 마스크가 명시돼 있지 않다는 것과 새 규칙을 설계할 수 없다는 것은 다르다. 원천 불가능성을 증명하지 않았으며 새 눈 셀 수를 사용자에게 고르라고 요청하지 않는다. **명시적 새 대응 규칙 없이 모든 blink 피부/모든 bank 내부 피부를 무시하는 runtime 공동배정은 실행하지 않았다.**
- **Argon 검토 질문(2개):** (1)2.2에서 공동으로 양자화한 눈 전체 support의 닫힌 경계/주변 피부를 어떤 source-local 표면 또는 cage에 붙일 것인가? 기존20개 점 대입·24정점 aperture·실제 색소 경로를 재사용하되, 그 점/곡선을 전체 피부 소유권으로 확대하는 규칙과 경계 바깥 불변조건이 필요하다. (2)그 support와 native 안검/피부를 함께 재배치할지, 별도 feature layer로 합성할지 정할 때 현재 native depth/alpha를 새 footprint에 어떻게 운반하여 자기 안검을 두 번 절단하지 않고 측면 얼굴/머리의 실제 가림을 보존할 것인가? 최소 재현은 위F105의9삼각형이며 `AUDIT112.json`에 정점/UV/alpha가 있다. 같은 정보를 더 캡처하는 것으로 이 정의 공백이 해소된다고 가정하지 않는다.
- **적용/인계:** 같은 폴더 `INDEX.html`, `SUPPORT_OWNERSHIP112.png`(기존 GPU77+원본 UV 진단, 새 최종 RGB 아님), `AFFILIATION_CACHE112.json`, `AUDIT112.json`, `CHECK112.json`, `CODE_INDEX112.json`. CPU/offline affiliation/cache 검증만 구현했으며 C#/HLSL 공동배정·새 최종합성·시간 안정성·유한 팔레트/외곽선은 미완이다. model/topology/UV/morph/registration/bank-shape 변경은 무효화, view/renderer/current sourceId/배정 history는 분리한다. unknown→transparent fallback은 없다. 도구/권한 거부가 아니라 위 표현 계약이 런타임 의존 단계의 차단이다. Unity 현재 상태는 새로 조회하지 않았으며111의23:52:44UTC 관측을 현재 사실로 재사용하지 않았다. 본 절과112의 관련 파일만 보존하는 커밋이 이 감사의 보존 커밋이며 기준111은7736f2ce다. Argon 직접 통신은 하지 않았다.

#### 113 Argon2.3 소유권 연결과 실제 GPU 공동 배정·전체 캐릭터 캡처 — 격리 통합, 제품77 미전환

- **현재 결과/코드:** `experiments/pixel-pipeline/2026-11-02-argon23-runtime113/INDEX.html`. 112의 설계 보류를 새 대응 정책으로 해제하고 외부 C# `Forward113.Record/Draw`의 정상 RenderGraph에서 현재 source→원본 색소 경계→GPU 공동 배정→목적지 가림→LUT 직접 대입을 실행했다. `RegionDriver113.QueryBindings/PrepareCarrier/Draw/ComposeBindings`, `Region113.hlsl:PrepareCells113/GatherEye113/BuildSubsets113/Enumerate113/Reduce113/Write113/ComposeRegion113`, 실제 자산 `Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye113.compute`가 연결된다. `Capture113.CaptureFull113/FullStrips113`는 같은 main render serial의 전체480×272 GPU 결과를32행씩 읽는다. 실행 당시 전체 C# 묶음 `RUN_Capture113e.cs.txt`와 `CODE_INDEX113.json`을 보존했다. C# Assets import/domain reload 없이 새 compute만 import했다. 기본 제품77·사용자 modified30은 변경하지 않았다.
- **원문/정식화:** 실제 원본 `C:\Users\15352\Desktop\Argon2.3.md`,12551bytes,SHA256 `6dfff097e26aebc132bb001a19497581c3575dbb2a739d7e62ca11a6bec872de`; 원문 불변이며 사본을 보존했다. 문서의 unilateral blink+ring 접촉 skin 연결성+current depth gap≤12mm 조건을 전용 `_OwnSkin113` 버퍼와 query scope로 연결했다(409삼각형/눈). 얼굴 전체 nearest-eye 태그를 무시하지 않는다. 12mm는 새 제안 정책이며 범용 해부학 사실이 아니다. 112의 combined skin graph는 이미 눈썹5를 제외했다는 문서 전제도 정정했다. 과거110의64해는 열거 상한이었다. 현재113은 주어진 한정 입력에서 최대2^21조합/눈을 실제 GPU 열거하며 overflow는 실패 처리한다. 원본 성분 손실→union 면적 interval 오차→part 면적 interval 오차→source 재구성 오차→원본 bank-key 손실을 사전식으로 비교한다. 연결성은 현재 확정 source component에만 적용한다. 동등해의 pixel consensus는 완전한 feasible layout/형태·history 최적화의 증명이 아니다. form111 전체 Pareto와 시간 대응은 아직 미이식이다.
- **실제 입력/색 출처:** `SourcePigmentStream113.Update/Upload`는 원본 native UV 색소848점/846선분을 현재 평가 정점·barycentric으로 변형한다. 593KB JSON 대신20,459byte bounded binary를 썼으며 원본을 대체하지 않았다. I/W 색은 기존 authored Template20 bank의 immutable source key, 기하는89의 실제 native 등록이다. 이를 native UV에서 그 RGB가 최초 생성됐다는 주장으로 바꾸지 않는다. 안검 색은 원본 UV 성분의 실제 texel medoid를 유한 LUT로 사용한다. skin canvas는 기존 native ring3단계 공급이며 전체 얼굴 피부/두피/볼 색 영역 분할을 해결한 것이 아니다. RGB를 layout 비용으로 쓰거나 연속 명암을 최종 눈 RGB에 곱하지 않는다. `_OwnSkin113`·curve·solver는 renderer/view/topology scope의 소유 버퍼이며 빌린 mesh/RT를 해제하지 않는다. inplace texture 교체/다중뷰/회전 전체 수명 검증은 미완이다.
- **실측 범위:** 실제 Play5회 중 앞선4회는 bounded JSON 초과→스트리밍, 예약어point→entry113, 전체float plane2MiB→32행≤245,760bytes, HLSL ternary의ni++/nw++ 부작용→명시적 counter의 확정 오류를 고쳐 각각 정상 종료했다. 마지막1회는 `eye113-20261102T012349564Z-df6df224`의12개 완료 sourceId/frame/serial, Close0→25→50→75→100→75→50→25→0 및 Close75 hairON/OFF/복구를 캡처했다. 모든 evaluated Close오차0, GPU source flags0, 정확한 완료 marker/동일 프레임 readback 검증. `oracle113.solve`는 실제 GPU proposal table에서 독립 CPU 전수 계산하여24눈(7개 고유 입력)의 점수·전체 동등해 수·합의 마스크가 정확히 일치했다. 최종 눈 소유 픽셀의 **선형 RGB LUT 밖 색0**, 완전Close 최종 I/W0셀, reopen source/label/색 완전 재현, hairON/OFF intrinsic part/owner/RGB 동일. hair 비교는 서로 다른 sourceId이고 depth float까지 같다고 주장하지 않는다. 눈 ROI 밖 전체RGBA byte동일12장. 이는 동일 목적함수 구현 증거이지 미술적 성공/올바른 목적함수 증거가 아니다.
- **남은 실제 실패/다음 원인:** Close50 eye2는 완전 동등해2개여서2canonical셀 미확정이다. source-key 손실만으로 원형 상대배치/history 목적을 대체할 수 없다. 최종 목적지 compose에서 native 기하 coverage<8/16인1~5셀이 다시 잘려 문서의 불투명 셀 소유권이 끝까지 보존되지 않는다. 같은 셀의 실제 fragment/ring 기반 깊이 운반이 아직 미완이며 단일 추정 깊이/피부 무시로 채우지 않았다. 머리/depth interval 최대2셀 미확정, 완전Close upper curve1셀은 dense 확정 색소 표본 부재다. source 없는 색을 발명하지 않았다. 이12상태는 실제 회전/보행/subpixel·다중뷰·전체 팔레트/외곽선 완료 증거가 아니며 기본 제품77 대체를 보류한다. 아직 기술 수정 대상이 있으므로 이를 사용자 미술 숫자 선택으로 전가하지 않는다. GPU 시간은 미측정이고 region 소유 버퍼3,771,712bytes/고정 최대 열거 비용을 남겼다.
- **보존/현재 상태:** 마지막 공식 읽기2026-11-02 01:37:51UTC PID35364,Edit/paused=false/compiling=false/transition=false,GameMap1 clean,filtered dirty31 목록 동일. 현재 InputSettings의 같은 살아 있는 참조·22값 JSON·장치/keyboard/활성상태·hideFlags 불변, 옵션disabled/None/backgroundfalse/time/pipeline 복원,74global getter 검증/복구오류0/global buffer 쓰기0. 현재 직렬화46개 ExactUTF8, 보호32파일 SHA 동일, 소유자원 dispose/observer 제거/RT30→30. 원래47개 중 임시 AssetImporter wrapper1의 과거 unavailable을 PlayerSettings 손실로 부르지 않는다. 이번 마지막 Play의 Unity `GetTotalAllocatedMemoryLong`2,103,611,002→2,139,959,998bytes(+34.67MiB), 후속 읽기2,115,557,799bytes(+11.39MiB); OS physical WS나 누수 증명이 아니다. 강제GC/정리/SaveAssets/ClearDirty/InputSettings교체/CUA/초기화/삭제/강제종료/push0. 최근 Console50은 Info50,Error/Exception0. 구체적 보존은 `PRESERVATION113.json`이다.
- **전달/커밋:** `GPU_RUNTIME113_WHOLE_CHARACTER.png`를 실제로 열어 검수하고 Library에 저장했다. `library_file_id=libfile_331b694ffd788191a7796aa62b0e2783`, `file_id=file_000000001a3c8230ab805a5c53596f22`; Windows xattrs helper는 실패했으며 성공한 Library identity는 별도 로컬 receipt에 보존했다. 새 Library 항목을 중복 생성하지 않는다. 전체 native PNG/nearest·눈ROI·실제 상태 WebP 및 `RAW113.zip`, 입력계약·코드·검증을 이113폴더에 선별 보존한다. 이 절·새 compute/.meta·완료113실험만 포함하는 로컬 커밋은 `git log -- experiments/pixel-pipeline/2026-11-02-argon23-runtime113`로 찾는다(기준112 `fab22d91`). 실제 제품 적용/미관·시간 안정성 완료라고 보고하지 않는다.

#### 114 저장113 실패 분류·최소 좌표 패치 준비 — 추가 Unity/Play 0, 런타임 미적용

- **색인/범위:** `experiments/pixel-pipeline/2026-11-02-eye-failures114/INDEX.html`, `FINDINGS114.json`, `CODE_INDEX114.json`. 기준113 `e4a84a88`. 이번 Unity 호출·Play·Assets 변경·Library 업로드는0이며 제품77/GPU113은 그대로다. 현재 Editor/dirty는 재조회하지 않았고 과거 상태를 현재 사실로 재사용하지 않는다. 입력은 동일113 sourceId의 저장 기하/행렬/query/표본이며,111에서는 해시 검증한 정적 texture만 재사용했다.
- **동등해 원인/오프라인 해결:** `tie114.complete_pool/transport`에서 F103/F111 owner2의 완전한 두 해를 검산했다. W가 canonical(5,5)/(6,5)에 놓이는 차이이며, 같은 white key(2,4,215,79)의 지지는1/64 대11/64다.113은 key 개수만 보존하고 원형/상대배치/history를 이식하지 않았다. 기존 `form111`/`form22.rank_source`를 그대로 쓰면 W분포 L1은25/42→7/57, 상대배치 오차는약2.080→0.700으로 해1이 두 차원 모두 우세하다. history만으로는 동률이다. 새 가중치/셀 수 없이 두 프레임 모두 원형 기준으로 해결했고, D4·후보/셀 순서 회귀를 통과했다. 관측 없는 상대쌍은None이며0오차가 아니다. 실제 GPU에는 아직 미이식이다.
- **표본 연결 오류/패치:** `trace114.geometry/transferred_sample`, `geometry114.Face114.query/carriers`, `pairing114.compose/main`이 carrier 포함4320개·GPU 얼굴 query3190개·최종 합성270셀을 재현했다(가림 interval 오차0, 관측 depth 잔차 최대5.80e-7m, 관측 없음은None). `ComposeRegion113`의4배 S4 표본과 `CarrierQueries113`의8배 floor 표본은 모두(+0.0625,+0.0625)px 다르다. source/display projection 불일치는 현재12입력의 동일 projection gate 안에서 재발하지 않았고, source ID는 dense8을 썼다. 양성 눈 경로는16개 per-fine depth를 사용하므로 옛 단일 owner-depth 축약이 원인은 아니다. `paired-point-patch`의 NativeCarrier113.RecordGraph/RegionDriver113.PrepareCarrier·Draw/Forward113 생성자/Region113.hlsl 및 capture 크기 계약을 수정해 source8x·destination4x를 분리했다. 새 compute114는 실험 폴더에만 있으며 import/컴파일/실행 전이다. 다음 실제 실행에는 새 sourceId/출력 폴더/외부 runner가 필요하다.
- **단독 채택 불가 근거:** 정확한4배 위치 계산은 F125 main(224,219) 안검7/16→8/16 등 기존 미확정6건을 해소한다(안검4건, 머리 가림 확정2건). 그러나270셀의 RGB22개가 달라지며2흰자+6안검→피부,6머리→미확정 바탕도 포함된다. 이 결과를 무회귀/미술 성공으로 부르지 않는다. 선택된 불투명 셀을 native geometry coverage로 다시 자르는 소유권 결함은 좌표 수정만으로 해결되지 않는다. 전후 좌표·source·RGBA/owner는 FINDINGS114와 DATA114.zip에 보존했다.0status가 눈 성공을 뜻하지 않아 머리의 확정 덮어쓰기까지 비교했다.
- **안검1셀:** `pigment114.main`에서 F107 canonical(8,5)의 dense8 중심64개는 meta/alpha0이지만 원본 UV 곡선6점은 alpha0.19869~0.80309이고 현재 기하의 intrinsic CPU 가림도 모두 통과했다. column에 남은 arc0.05183px를 격자 중심이 놓친 얇은 끝부분이다.848점 UV 결합 오차≤4.08e-8. native vertex-raster chart와113 곡선의 투영 차이 최대0.0002805px는 문제 행5를 바꾸지 않아 소실 원인이 아니다. 새 GPU point-query 관측은 아니며, 현재 source-ID/UV/alpha/가시성을 조회하는 좁은 런타임 연결이 필요하다. 원본 부재로 처리하거나 주변색/임의 RGB로 메우지 않는다.
- **12mm·검토 질문2개:** 12mm는 world camera-depth 차이여서 동일 geometry의 균일 scale0.5/2 해석만으로3190 query 중626개의 판정이 달라진다(새 렌더 아님). F99 main(222,222)의 같은 unilateral/ring 피부2726도 gap15.53mm이며 비소유 피부 hit도 있다. 현재113에 측면/다른 scale 캡처는 없고 임계값을 바꾸지 않았다. **(1)** 선택 셀의 native carrier가 없는 하위 표본은 현재 같은 셀의 triangle-plane 연장/ring-plane 중 어떤 source-local 규칙과 깊이 구간으로 운반하는가(F105 main221,221의0/64, F125 main224,219의33/64)? **(2)** world12mm가 소유권 권위인지 모델 local 관계/두께로 정규화할 의도인지? 이는 새 디자인 셀 수가 아니라 자기 표면과 실제 외부 가림의 계약 질문이다. 독립적인 원형/좌표 수정 근거는 이미 검산됐다.
- **검증/보존:** check114.py44검사·4320실제 좌표 대응 통과. 전체 UV/유한 팔레트/외곽선·실제 움직임·패치 GPU 비용/회귀 완료를 뜻하지 않는다. 기존32파일과 GPU113 asset SHA를 보존하고 InputSettings 교체/저장/GC/ClearDirty/CUA/초기화/삭제/종료/push는 하지 않았다. 새114 폴더와 이 절만 선택 커밋한다. 관련 커밋은 `git log -- experiments/pixel-pipeline/2026-11-02-eye-failures114`로 찾으며 중복 업로드는 없다.

#### 115 원형 판정·짝 가림 좌표의 실제 GPU 연결 준비/컴파일 — 첫 프레임 실패, 정상 종료·복원 미확인

- **코드 색인/적용 범위:** `experiments/pixel-pipeline/2026-11-02-gpu-form115/`의 `Form115.hlsl::{PrepareCells115,Enumerate115,CollectForm115,KeyReferences115,EvaluateForm115,Pareto115}`, `RegionDriver115.Draw/PrepareCarrier`, `NativeCarrier115.RecordGraph`, `Forward115.Record/Draw`, `Capture115.Tick/BeginExit/Finish`. 실제 새 자산은 `Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye115.compute`와 기존 GUID를 가진 신규 `.meta`뿐이다. C#은 Assets 밖 외부 runner 동적 컴파일이며 프로젝트 C# import/domain reload는 없었다. 제품77 기본 경로와113 compute는 바꾸지 않았다. 관련 커밋은 이 절과 위 실험 경로의 `git log`로 찾는다(직전114 `07e7e810`).
- **구현:** 기존2.2/111 `rank_source`의 I/W 원본 분포 L1, 빠진 대응쌍 수, 상대배치 오차를 실제 dispatch 경로에 이식했다.113의 source-key-count 대리 벌점을 1차 목적함수에서 제거하고 앞의4개 목적함수만으로 얻은 모든 동률 후보를 평가한다. float 연산은 바깥쪽 구간으로 감싸며 관측쌍이 없으면 valid bit를 끄고 오차0으로 보지 않는다. 후보128은 자원 상한이며 초과하면 무효 처리한다. RGB·독립 조명·팔레트 간격은 배치 비용에 넣지 않았고 history는 아직 구현하지 않았다. 기존113 커널을 보존하여 같은 입력의 별도 control dispatch와 후보를 함께 그리도록 연결했다. **실제 GPU 결과 동등성/성능/수명은 아직 통과하지 않았다.**
- **좌표/컴파일:** intrinsic source8x와 목적지 native carrier4x를 분리하고 `CarrierQueries115/ComposeRegion115`가 실제 S4 중심과 같은 위치를 쓰게 했다. 외부 runner 전체 C# 컴파일 성공, import된 새 compute28개 kernel metadata 검사/Shader 오류0/같은 domain을 확인했다. 이는 완성 프레임의 GPU 수치 검증이 아니다. `primary115.py/REFERENCE115.json`은 저장113 실제 입력12상태×2눈에서 첫4목적함수 동률을 모두 검산했고, 기존 source-form으로24건 모두 하나의 후보가 남았다. 이 CPU 결과를 GPU 선택 입력으로 주입하지 않았다. 구간 구현과 CPU 기준의 실제 GPU 일치는 미검증이다.
- **22RGB 변경 분류:** `classify115.py/DELTA_CLASSIFICATION115.json`은 같은113 원본 geometry/UV/alpha/S4 자료를 쓰는114의 짝4x 반사실 계산을 재검토한다(새115 GPU 출력 아님). 안검 복구4, 확정 머리 가림2, 실제 앞머리 source 재선택2, 명시12mm 정책에 따른 흰자→피부2, carrier8개 부재+실제 얼굴 hit1개에 따른 안검→피부2, 가림 없이 carrier7/16만 있어 탈락한 안검4, 머리 가림 interval 미확정으로 canvas에 내려간6이다. F101/F113 main(222,221)은 실제 own-component 불투명 hit10개가12.286~17.820mm 앞이라 현2.3 정책상 제외되지 않는다. main(222,222)은 carrier8/16 중 실제 비소유 피부 삼각형18096 hit1개(4.536mm)뿐이다. 후자를 피부가 셀 대부분을 가린 것으로 해석하면 틀린다. 미확정6개도 피부가 정답이라는 증거가 아니다. 따라서 바뀐22개를 일괄 회귀나 일괄 성공으로 판정하지 않는다.12mm는 현재 모델 스케일의 명시 정책으로 그대로 유지했다.
- **실제 실행/차단:** PID35364에서 새 sourceId `eye115-20261102T023401691Z-4f7e54be`로 정상 Play1회 진입했다. 마지막 관찰기 상태는02:34:07UTC `probe-armed-on-live-head-next-normal-frame`, 마지막 trace frame94/Native ready/Gameplay connected/main serial1이다. 완료 프레임·완료 marker는0개다.02:34:19UTC Editor.log에 `333 GPU readback` 예외가 `Full319View335.Read:70 → PostView366.AfterRender:15 → HeadLocal367.RenderFrame:32 → Gameplay397.Present:33`에서 기록됐다. 셰이더115가 직접 원인인지, GPU/device/다른 자원 문제인지 live stack 없이 확정하지 않는다. 단순 timeout 연장이나 추가 Play는 하지 않았다.
- **정상 종료/현재 상태는 미확인:** official relay initialize/tools-list는 응답했으나 Unity console/read command가 시간 초과됐다. 보낸 읽기 command는 결과 불명이라 반복하지 않았다. `NormalExit115.cs`는 공개 update callback 목록에 이 시험 assembly의 관찰기가 정확히1개 있을 때만 공개 `EditorApplication.ExitPlaymode`를1회 호출하도록 제한했다(관찰기 private 메서드 호출 없음). 이 정상 종료 command도 시간 초과됐고 `EXIT_COMMAND_RECEIVED115.json`/`EXIT_API_RETURNED115.json`이 없어 실행·정상 종료·관찰기 Dispose/설정 원복은 **불명**이다. 재호출하지 않는다.02:51:47UTC OS PID35364 Responding=true/CPU3293.5s/WS4,004,311,040bytes/private memory10,127,552,512bytes, 로그 갱신은02:34:19UTC에 머물렀다. OS Responding=true는 정상 Editor 동작 증거가 아니다. 이 값은 Unity Profiler allocated counter가 아니며 누수 판정도 아니다.
- **보존 근거/다음 중단점:** 실행 전 Edit/GameMap1 clean/dirty31/InputSettings 동일 객체·22개 값/장치·옵션 disabled/None/background=false와74global 외부 백업이 있다. 실행 후 디스크 보호33파일과 기존 사용자 tracked30개 내용은 유지했지만, 현재 메모리 dirty/InputSettings/옵션/globals/소유 GPU 자원 원복은 조회 불가로 확인하지 못했다. `CHECK115.json`의 `runtimeValidationPassed=false`를 유지한다. 강제 종료/초기화/GC/SaveAssets/설정 교체/CUA는 하지 않았다. 공식 통로의 현재 pending 정상 종료 결과를 먼저 확인해야 하며 불명 상태에서 재실행하면 안 된다. 그 전까지 새 Play/import/렌더는 보류한다. 얇은 안검 UV curve6점의 정확 footprint query 연결은 아직 구현 전이다. 새 전체 PNG/Close·hair ONOFF 회귀 및 Library 업로드는 없으며113 이미지를115 결과로 재사용하지 않는다. 전체 얼굴 UV/외곽선/시간 안정성도 계속 미완이다.

#### 115 후속: Recovery 확인·GPU reset 정적 감사 — 새 Play/GPU 실행0

- **복구 기준:** 사용자 재실행 후 PID6288/6000.5.9f1의 공개 조회05:24:31UTC는 Edit/GameMap1 clean/compiling·updating·전환 false. dirty31을 강제 재현하지 않았다. 재실행 직후24였고 `EditorJsonUtility.ToJson`·해시 조회 구간에서 FaceSourceOwner202.asset dirty false→true가 관측되어 마지막25다. 메쉬9,357,126B는 ExactUTF8이며 ClearDirty/저장은 하지 않았다. native47개 중45개 ExactUTF8, Input22/장치/옵션/시간/pipeline/global74 일치, command update callback0. 객체 ID는 바뀌었으며 Undo/비직렬화 상태 완전 복구는 미증명이다. 두 미로드 shader는 소스/meta/선언 이름/실행 전 보호 hash가 맞고 강제 import/재컴파일하지 않았다. `experiments/pixel-pipeline/2026-11-02-gpu-audit115/recovery/`가 읽기 근거다. 초기 읽기 source에 불필요한 금지 namespace System.Diagnostics가 있었으나 실제 거절 응답은 없어 timeout 원인으로 확정하지 않는다. 이를 완전히 제거한 공개 getter 조회는 성공했다. 외부 비교 번들의 중복 helper/Mesh namespace 컴파일 실패는 실행 전에 확인·수정했으며 프로젝트 컴파일 변경이 아니다.
- **새 실패 근거/구분:** 이전 Editor.log에는 readback 예외 뒤 D3D11 device reset/removed·unrecoverable 종료 메시지가 확인됐다. 정확한 kernel/실제115 GPU header/시간은 없다. OS Responding/CPU 시간이나 저장113 header를 실패115 프레임의 GPU 결과로 대체하지 않는다. 이번 정적 감사의 Unity 호출/dispatch/Play/Assets 변경0, 제품77/115 구현은 그대로다.
- **핵심 함수/계산:** 기존 `ForwardEye115.compute::GatherEye113/RawConnected113`, `BuildSubsets113/Connected113`, `Enumerate113/Enumerate115/CollectForm115`, `PrepareCells113/115`, `EvaluateForm115/Pareto115`, `Query`; driver는 `RegionDriver115.Draw`, `Forward115.Draw`, `WholeEye107.Dispatch/Resize/Dispose`. 새 분석은 `gpu-audit115/audit115.py::{main,raw_connected}`와 `STATIC_AUDIT115.json`. header 경계163건/scope51건/geometry finite12건·기존 vertex/material/partMap 범위 검사 통과. 113은 큰 enumeration1회4,194,304 work item, 115 비교는 baseline+enumeration+collection3회12,582,912개다. 저장 열린 입력은 한쪽20비트1,048,576조합, 1차 동률 뒤 form 후보는 눈별1~2개다. relative 평가가 새 지수 폭발을 만든 것은 아니지만 큰 기존 연산을 반복한다. Pareto는 눈별1thread에서 최대16,256쌍×6차원, metric private 배열1280B/호출이다. Gather/curve의 긴 직렬 루프도 기존부터 있다. Query는 정상 CPU BVH에서 유한하지만 GPU visit 예산·잘못된 node 참조 guard가 없다. 실제 무한루프/잘못된 index 발생은 미확인이다. 전체 source engine은3→4, query82,944→92,160, structured buffer31,966,348→42,814,800B(기타 RT/driver 제외). 구조체 stride/주요 index는 용량 이내, engine별 shader clone·순차 command·조건 밖 barrier를 확인했으나 runtime/driver 문제를 배제하지 못한다.
- **다음 실행 계획/차단:** `AUDIT_AND_PLAN115.md`를 따른다. full115/큰 offscreen은 아직 재실행하지 않는다. own buffer 초기화2thread→실제 F103의2candidate metric/Pareto만 단계별 제출하며 BVH/전수 탐색/전체 렌더를 제외하는 것이 최소안이다. 완료 callback 후에만 다음 제출, WaitForCompletion·자동 재시도 없음. 다음 탐색은64state group부터 offset/chunk·부분 reduction을 검증하고, BVH visit continuation/curve column별 공유 계산/Pareto 병렬화로 연산 예산을 분리해야 한다. 단순 dispatch 나열/timeout 연장으로 TDR 안전을 주장하지 않는다. 아직 원인 kernel/시간이 없어 full 실행의 reset 위험은 해소되지 않았다. 드라이버/TDR/보안 설정을 바꾸지 않는다. 팔레트/외곽선/시간 안정성·얇은 안검 복구는 계속 미완이다. 관련 커밋은 이 절/분석 경로의 git log로 찾으며 직전115 구현은 `75bbcaf9`다.

#### 115 최소 GPU 분리 실행: 초기화 통과·2thread 평가 readback pending — 새 Play0

- **근거/코드:** `experiments/pixel-pipeline/2026-11-02-bounded-form115/RESULT_BOUND115.json`, `FIXTURE115.json`, `Probe115.cs::{Execute,Start,Received,CompleteStage,Finish}`, 실제 실행 source `RUN_BoundRun115.cs.txt`. 이전 감사 `759112d2`의 최소안만 수행했다. fixture는 원본113 F103/owner2의 두 전체1차 동률 후보 `[12,66]`, `[12,130]`와 실제 source weights/key/points/tag에서 만든다. feature ID2는 보존하고 진단 배열 slot0으로만 순열 이동했다. 원형의 GPU 생성(PrepareCells/KeyReferences)은 이번 범위가 아니며 CPU interval 입력을 검증했다. 최종 winner를 입력으로 주입하지 않았다. typed buffer12개98,280B, keys20/active-owner keys10/points9/candidates2, 커널 group은1thread로 확인했다. 모델별 눈 크기·RGB 조정이 아니다.
- **실행:** 외부 full C# compile 성공(첫 누락 using 컴파일 실패는 실행 전 수정), Assets C#/shader import·Play·camera·renderer·BVH·전수 탐색·global setter0. PID6288/D3D11 level11.1/AMD Radeon RX9070XT. `run-20261102T060239032Z-3a7a745a`에서 BeginForm1152thread 완료와 state32B=0/primary96B bytecopy 동일을 확인한 뒤에만 EvaluateForm1152thread를 제출했다. 요청당 readback은 최대160B, 동기 WaitForCompletion은 없다. 초기화 단계는 **실제 GPU 통과**, 원형 metric/Pareto/전체 렌더는 통과가 아니다.
- **현재 차단:** 마지막 기록06:02:49UTC는 두 metric readback pending/제출2회/Pareto0회. metric은 active-key당 point loop≤9, candidate당 source pair≤21인데도 완료 자료가 없다. 원래115의 큰 조합량/BVH/full renderer만으로 설명할 수 없는 완료 정체다. GPU arithmetic/binding/컴파일러·드라이버/비동기 완료 처리 중 어느 원인인지는 미확정이다. RunCommand 응답은 shader warning을 모아 `UNEXPECTED_ERROR: executed partially`로 반환했지만 파일로 실제 초기화 완료/평가 제출이 입증된다. 승인 거부/미실행이 아니다. 특히 EvaluateForm115의 `array reference ... not natively addressable, forcing loop to unroll` 경고와 isfinite/integer divide 경고를 남겼다. 경고만으로 원인 확정하지 않는다.
- **보존/수명:** 실행 전 dirty25/Input 동일 객체·22값/옵션·시간·pipeline/global74를 외부 BEFORE에 기록했다. 06:05:02UTC OS PID6288 Responding=true, 이후 공식 Console 읽기는15초 timeout. PID GPU engine 한 표본은 모두0%였지만 GPU 완료/정상을 뜻하지 않는다. 06:08:16UTC 이후가 아니라 **06:01:30UTC부터06:08:16UTC까지** System/Display 이벤트 조회0건이며 이것만으로 새 device reset을 배제/확정하지 않는다. 기존 로그에는 새 reset 근거가 아직 없다. GPU 완료 불명이라 own buffer98,280B/compute clone을 강제 해제하지 않았다. 관찰기는 두 callback을 기다리며 등록돼 있다. 오류/수치 불일치면 다음 제출을 막는다. 늦게 정상 완료될 경우 승인된 Pareto1thread만 이어질 수 있으므로 결과 파일을 먼저 확인하고 새 명령을 재전송하지 않는다. AFTER/완료 marker/소유 자원 해제/현재 in-memory 보존은 미확인이다. 새 Play·force kill·reset·드라이버/TDR/보안 변경·SaveAssets·ClearDirty·InputSettings 교체0.
- **다음 중단점:** 현재 pending 해결이 먼저이며 큰 단계는 재개하지 않는다. 이후 ABI echo-only kernel로 실제 uniform/header/stride를 확인하고, AsyncGPUReadbackRequest 상태·forcePlayerLoopUpdate 및 public stop-next/완료 후 해제 제어를 명시적으로 보유하도록 관찰기를 보완할 필요가 있다. 원형 계산은 private 동적 array/unroll 대신 candidate/key별 structured 결과·작은 reduction으로 분리하는 가설을 검토하되, 이번 source나 실행 중 관찰기를 자동 갱신했다고 주장하지 않는다. 실제 source metric/shape/색·가림·시간 안정성은 계속 미검증이다. 관련 커밋은 이 절/실험 경로 git log로 찾는다.

- **긴급 후속06:16UTC:** 사용자06:13UTC의 새 D3D11 device reset/removed·unrecoverable Error 화면을 전달받았다. OS06:15:21에6288 부재,06:16:05에 해당 프로젝트 Unity process0 확인. agent가 종료/재시작/정상 Exit를 실행한 것은 아니다. 복구 후 새6288에서 micro 시험이 진행됐고 초기화 완료→평가2thread 제출 이후 새 오류와 process 종료가 관측되어 이전35364 팝업 근거와 구분한다. 정확한 최초 device 오류 시각은 새 file log에서 확보하지 못했고 user screenshot이 첫 fatal 관측이다. metric callback/Pareto/Dispose/AFTER/완료 marker0. 마지막98,280B pending owner는 과거 live 기록이며 process 종료 후 관찰기가 새 작업을 제출할 수는 없다. 정상 자원 회수/메모리 복구를 주장하지 않는다.06:16:48 보호35파일과 기존 native47백업13,008,941B의 해시 모두 동일. 추가 Unity/GPU/compile/Play/재시도/복구 조작0, 신규 시험은 중단한다. `FATAL_UPDATE115.json`, `FATAL_FILE_CHECK115.json` 참조.


#### 115 재부팅 후 CPU/캐시 바이트코드 추적 — GPU 재개 보류
- 오류 증거 36파일은 `87b51ab93f756132f89ab68ba327a44a5a5e1afa`에 보존했다. GPU 초기화 완료 → 두 후보 Evaluate 제출 → callback2 미완 → 새 device reset/6288 종료다. Pareto/정상 Dispose/완료 marker는 없다.
- OS는 **06:20:51.5UTC 재부팅**, 동일 프로젝트 새 Editor **22952**는 **06:22:43UTC** 시작, **06:31:44UTC Responding=true**. agent가 실행하지 않았다. Unity/MCP 명령·GPU·컴파일0이며 새 Editor의 Play/dirty/loaded native 상태는 조회하지 않았다. OS Responding은 GPU 건강 판정이 아니다. 최종 프로세스 기록에는 PID/실행 경로/프로젝트만 남기고 원시 commandline은 포함하지 않는다.
- `experiments/pixel-pipeline/2026-11-02-bounded-form115/cpu_tokens115.py::VM.run`은 기존 캐시를 CPU로만 해석한다. `dxbc_read115.py::decode`가 추출된 SM5 token을 읽는다. 원본 shader `ForwardEye115.compute:442 EvaluateForm115`, `:440 MetricSet115`는 변경하지 않았다. 캐시 SHA `c5c6463f2525c7e228e221d7877fbd7511295b4151daa565f8ef2d9cdc55e302`, DXBC30288B/SHEX30204B/1062명령/10loop/배열5개다. 강제 unroll 경고를 무한 전개 원인으로 단정할 수 없다. 당시 driver machine code와 같다는 attestation은 없다.
- **기대한 uniform/동결 F103 입력에서는 두 후보 모두6006 CPU 명령에 종료**, 검사한 배열·structured 주소가 범위 내이며6차원×2 평가 interval이 독립 유리수 oracle을 포함한다. `cpu_regression115.py::validate/main` **12검사 통과**: stride/범위/캐시 슬롯, width0/key33/point25/cell144/잘못된 mask/짧은 buffer 거부, 후보 순서 교환, 관측0/source0과 CPU step budget. GPU 상수/입력내용 echo가 없으므로 GPU 실행 전체를 배제한 증명은 아니다.
- `CPU_STATIC_AUDIT115.json`에 loop/unsigned/bounds/alias/초기화/컴파일/미완료 readback을 분리했다. C# 각 buffer는 별도 생성됐고 완료 전 해제되지 않았다. 8UAV+1SRV, 상수 offset484·496·560과 정적 입력은 맞는다. 첫 GPU init은 state16/group48만 검증했고 나머지 GPU 입력·driver 변환·request done/hasError는 미관측이다. 미완료 readback만으로 device reset을 설명하지 않는다.
- **원인 확정·GPU 실행 안전성 확보 실패**: 작은 dispatch와 CPU 통과는 재실행 근거가 아니다. 같은115/축소2후보/새 Play/compile를 실행하지 않는다. 실제 제출 입력·binding attestation 및 driver/device-loss 단계 구분이 아직 없으며 별도 안전 판단 전에는 새 GPU 단계도 없다. 향후 늦은 callback이 다음 dispatch를 자동 제출하지 않도록 명시 gate와 request 상태 보존이 필요하다. 강제 해제/driver/TDR 변경은 제안하지 않는다.
- 이번 커밋 시 보호35파일·기존 user modified30·외부 native47백업13,008,941B 해시를 대조한다. 새 Editor 메모리 전체 복원은 미확인. 제품77/미술 알고리즘 변경0, 새 미관·시간 안정성 성공 주장0. CPU 도구/결과만 선택 보존한다.


#### Argon2.4 대조 및113 최소 후보 — CPU 검증, GPU 보류 유지
- 원문 `C:\Users\15352\Desktop\Argon2.4.md`, 20,782B, SHA `289c0f2f17cf32ef3429dfff76b0cecf472ddc9eb9970a6701a79df772002ecc`. 원본 수정0. `ARGON24_REVIEW.json`은 문서 주장/실제 증거/한계를 분리한다. AMD JIT/scratch 원인 확정·제출 즉시 reset·80~85% 완료는 확인된 사실로 채택하지 않는다. SM5 indexable-temp 선언은 특정 드라이버의 실제 scratch 할당 증거가 아니다.
- `direct_support24.py::direct_mass/runtime_float_mass/winners`: 저장113의24개 눈/4개 1차 동률 검산. 직접 지지량만으로 F103/F111 해1 선택, F105/F109는21504 대21504 동률이다. **113의 기존 source-key 손실 기준을 그 뒤에 유지하면24/24가 기존 source-form 결과와 일치**한다(정확 유리수 및 shader순서 float32 모두). 이것을6차원 상대형태 목적 전체와 동등하다고 일반화하지 않는다. 같은 지지량/같은 key 손실이면 여전히 모든 해의 consensus를 보존한다.
- 기존 재구성식은 canvas baseline과 합하면 `K-m_part`라는 정상 categorical 오차다. `K-mI-mW-m_part` 항만 보고 산술 오류라고 하지 않는다. 새 direct support는 명시적 tie-break다. 또 F99 owner1/policy1 W 질량20969.76171875 등 비정수 입력이 실제 존재하므로 문서의 정수 모멘트 무손실 주장은 그대로 쓰지 않는다. 새 epsilon/반올림은 도입하지 않았다.
- `ForwardEye113_Direct24.compute` / `DirectSupport24.patch`: **113 기반 Less113·BuildSubsets113·Enumerate113 세 함수만 수정**. `Subset113.b.z`, `Group113.tail.z`의 기존 미사용을 검사하고 float bitpattern을 명시적으로 기록한다. 새 kernel/buffer/stride0,115 Evaluate/Pareto/interval 함수0. 원래113의 다른 private 배열까지 제거됐다는 주장은 하지 않는다. **소스 후보만 작성했고 컴파일/import/제품 연결0**이다.
- `geometry24.py::transport_assigned_depth/ring_limits/column_curve`: 측정된 하위 깊이를 그대로 보존하고 빠진 위치만 운반해 동일 목적지에서 외부 피부/머리를 다시 조회했다. 문제22셀 CPU 반사실에서 불확정 fallback0, 기존 확정 머리 가림 유지, mean/minimum 최종RGB 차이0. 전부 실제 표면을 새로 측정했다는 뜻은 아니다. 이22셀에는 known0 사례가 없어 그 분기는 합성 검사만 했다.
- 실제 등록24정점 링의 현재 직경은 **37.670~39.791mm**로 문서 예상21~24mm와 다르다. 기존 own-hit1190개의 socket 술어를0.5/1/2 단위 스케일로 검산해 변화0. 3190개 전체 재렌더·다른 시점의 가시성·고정 depth epsilon까지 증명한 검사가 아니다. 더 넓어진 own-component 면제의 일반 타당성은 미검증이다.
- F107 canonical(8,5) 원곡선 호0.05182838px의 중점에 native primitive59/원본 alpha[.164706,.635294]를 찾았다. 곡선평균깊이와 native깊이 차이는-1.8911e-6m다. **source와 destination가1.29056px 다르므로 두 위치를 구분**했고 목적지에서도 가시성[1,1]이다. 원색소 양수라는 증거이지 native 전체 불투명 또는 GPU1셀 복원 완료라는 뜻은 아니다. 다중선분 평균이 실제 색소 표면 위라는 보장 없이 자동 생성하지 않는다.
- `SupportGeometry24.hlsl`은 운반/안와/칼럼 clipping의 **미컴파일 순수 helper**다. 아직 전체 런타임에 결합하지 않았다. `regression24.py::main` 12검사 그룹 통과. CPU 후보/기하 입력/수식 검증과 GPU 안정성은 별개다. GPU/Unity command/compile/Play0, 제품77·팔레트/외곽선 변경0. 다음 런타임안은113 단일 후보로115 위험 경로·중복 baseline·동기 readback을 빼는 것이며, 컴파일/반영/실제 GPU 동등성·성능·원복은 **미수행**이다. 이전 GPU 오류가 해소됐다고 선언하거나 같은115를 재실행하지 않는다.


#### Direct24 전체 host 정적 감사 / GPU 재개 조건 (6885223e 당시)
- **현행 후보 host는 아직 없다.** `Forward113.cs:21`의3개 로드는 원래 `ForwardEye113.compute` 경로다. 현재 후보 소스만으로는 GPU 연결 완료가 아니다. 성공한 `RUN_Capture113e.cs.txt` SHA `c847d770b4245f2df4895c6515a16af7c1d412fec3821332c53862d59fdd4c08`와 실제 요청 hash를 대조했다. 이 번들과 주요8개 종속 소스에는 Forward115/RegionDriver115/EvaluateForm115/BoundRun115/Probe115 참조가 없다. `WholeEye111.cs:26` clone은 Forward113이 넘긴 명시적113 shader의 renderer/view별 소유 복제이며115를 몰래 로드하지 않는다. 원래 observer/AfterCanvas 등록과 해제 위치는 `HOST_ROUTE24.json`에 기록했다.
- 현재 제품 C#231파일2,656,953B 및 관련 직렬화 asset84파일84,302,787B에서115 이름/compute GUID 연결을 찾지 못했다. 대형5asset은 건너뛰었고 package/native/현재 동적 session은 전수 검사하지 않았다. **현재 Editor의 callback/loaded shader 상태까지 증명한 검사가 아니다.** Unity 호출은0이다.
- `HOST_KERNELS24.md` / `HOST_ROUTE24.json`:18커널의 호출 폐쇄·resource 이름/형·dispatch·메모리/반복 상한 비교. 함수 본문은 Less113/BuildSubsets113/Enumerate113만 바뀌지만 **Reduce113도 Less113 호출 폐쇄가 바뀐다.** 모든 resource 이름/형과 stride/할당 범위는 현재 소스상 동일하다. 컴파일된 실제 binding은 아직 미검사다.
- 113 전체 경로에는 Query stack32, Select 배열, Gather의 seen16, Compose의 depth16/known16이 남는다. 기존 캐시에서도 Query private-array1/Select3/Gather6/ComposeRegion2를 관측했다. 따라서 동적 배열 존재만으로 AMD 원인을 확정하지 않는다. 새 첫 검증 대상4커널(BuildSubsets/Enumerate/Reduce/Write)은 기존113 캐시의 이용 가능한 모든 resource-signature 일치 variant에서 indexable-temp0이었다. 새 후보 컴파일 결과 또는 당시 driver machine-code attestation은 아니다.
- **다음 최소안은 `NEXT_GPU_PREFIX24.json`의4단계이며 아직 미구현/미실행이다.** 먼저 이4개 기존 커널+호출 폐쇄만 포함하는 별도 thin module을 준비하고,115 및 나머지 entrypoint를 단순 미호출이 아닌 모듈 밖으로 제외해야 한다. 각 단계당1dispatch/별도 명시 command/자기 소유 새buffer를 사용한다. callback은 결과 저장·종료만 하고 다음 dispatch를 절대 제출하지 않는다. 다음 단계는 이전 GPU 결과 바이트를 hash 그대로 올리며 CPU가 layout을 선택하지 않는다. 과거 Capture113/relay113/Forward115/BoundRun 호스트는 재사용하지 않는다.
- F103의 실제9point/ni5/nw6 입력(원래 sourceID/serial 유지)을 사용한다: **①BuildSubsets(1,2,1),128thread/96 valid subset,≤591,616B; ②Enumerate(32,1,1),2048thread/32group,≤3,671,040B; ③Reduce(1,1,1),64thread/32768group 방문,≤3,145,824B; ④Write(1,1,1),64thread/9point영역,≤68,448B**. 기존Frame/Cell/Tag/Point에서 온 데이터이고115 moment fixture를 전체 재사용하지 않는다. 그룹 공유 메모리3,072B이며 private 배열을 새로 추가하지 않는다. 마지막Write는 여전히8UAV다. 숫자가 작다는 이유로 안전을 보증하지 않는다.
- 각 단계 완료 gate는 request 실제 완료·GPU error0·모든 산출값/미작성 sentinel 비교·파일 hash·마지막 완료 marker·own resource 해제 receipt다. pending/timeout/error면 다음 단계0, 재시도0, 강제 resource 해제0이다. prefix는 Edit compute-only로 Play/카메라/입력/씬/Shader globals 변경과 BVH/Gather/Select/합성·legacy control을 포함하지 않는다. 이로써 정적 구조상 문제115 실행 경로를 제거할 수 있지만 **thin source·단일 dispatch host·새 컴파일/반영/공개 상태 preflight는 아직 없다.** 신규 컴파일 때4entrypoint/기대한 ABI/private-array0 확인이 선행 gate다.
- 16표본 운반·안와 float2·곡선 중점은 여전히CPU/미컴파일 helper에만 있다. 현행 RegionDriver113.QueryBindings의.012 scalar, CarrierQueries113의8x, ComposeRegion113의 missing-carrier 처리는 변경하지 않았다. prefix 통과도 이 기능이나 실제 새 전체 캐릭터 렌더/시간 안정성 통과가 아니다. 기존 장치리셋의 정확한 원인 미확정, Editor/OS 정상GPU 작업의 동시성 및 driver JIT 위험도 남는다. GPU/Unity/compile/Play0, 제품77/기존 사용자 변경 보존.

#### Direct24 4커널·단일 단계 host 구현 — CPU 컴파일만 완료
- **현재:** 위 계획의 별도 모듈과 host를 작성했다. 경로는 `experiments/pixel-pipeline/2026-11-02-bounded-form115/prefix24/`. 제품77 변경, Unity 호출, Assets import, Play, GPU device 생성·dispatch는 모두 **0**이다. 실제 Editor 현재 상태는 이 단계에서 조회하지 않았다. 이 절의 관련 커밋은 `git log --oneline -- <해당 prefix24 경로>`로 찾는다.
- `prepare_module.py::main` → `Prefix24.compute`: 기존 Direct24 후보의 `BuildSubsets113`, `Enumerate113`, `Reduce113`, `Write113`와 6개 helper 본문만 추출했다. 원래 본문 hash 일치, EvaluateForm115/BoundRun115/BVH/observer/나머지 entrypoint는 모듈에 없다. shader SHA `a85bb725503d39e3c7fdd3a354bea2ea31382401f7deaae10fc254fdabe98d0d`.
- `Prefix24Host.cs::Start/Begin/Prepare`: 명령당 한 단계·한 dispatch만 제출하도록 작성했다. `STAGE1~4.command.cs.txt`는 아직 **미제출**인 독립 명령 소스다. Unity 기본 namespace 변환을 고려하여 공식 IRunCommand namespace를 첫 번째로 두었다. 고정 F103 sourceID/frame103/serial10 및 9point·5/6 입력은 `CASE.json`·`CaseLock24.cs`·`fixture/`에 hash로 잠갔다. `prepare_fixture.py::main`은 독립113 oracle과 96개 유효 subset의 기존 필드를 비교하고 2048상태/역순 merge를 검산했다. winner masks `[12,12,130,130]`·해1개는 **CPU 기대값**이며 GPU 선택 입력으로 넣지 않는다.
- `Prefix24Protocol.cs::ClaimStage/Previous/CheckReceipt/ValidateOutput`와 `StepGate24`: 새 파일+마지막 COMPLETE marker, 동일 source/run/shader/case, 이전 단계 실제 GPU 바이트, CPU 기대값 hash, 상태 동일·자원 해제 확인이 모두 필요하다. 불확실 dispatch/readback은 재시도·다음 단계·강제 해제를 막는다. `Prefix24Host.cs::Received/MaybeFinish/Finish`는 후속 dispatch를 호출하지 않는다. 모든 발급 readback의 실제 완료 후 소유 clone/buffer만 해제하며 미완료는 소유 참조를 유지한다. 전역 buffer/입력설정/씬/Play 옵션을 바꾸는 코드가 없다. 공개 상태 전후 차이는 실패로 남기며 추정 복원하지 않는다.
- `compile_hlsl_cpu.py::main`: Microsoft 서명 `d3dcompiler_47.dll`의 D3DCompile/D3DReflect로 **CPU에서** cs_5_0 4개 컴파일·반영 검사. private array 선언0, UAV5/3/2/8, thread64/64/64/8×8, structured stride16/32/48 확인. 기존 Enumerate signed/unsigned 경고 X3203은 남겼다. driver DLL 로드·device 생성·dispatch 없음. 실제 Unity import variant 및 driver machine code의 안전 증거가 아니다.
- `compile_cs_cpu.py::main`: protocol/host/정확한 전체 명령4개와 설치 Mono runtime 참조 조건1개, 총 **7건 CPU 컴파일 통과·C# 경고0**. 설치 DynamicAssemblyBuilder가 일반 System.*를 모두 참조하지 않아 live 명령의 DataContract 직렬화 의존성을 제거하고 Unity JsonUtility에 연결했다. ABI Marshal 검사는 외부 순수 CPU 테스트에서만 수행한다. Unity/host assembly는 실행하지 않았다. action-time 서버 승인 여부는 미검증이다.
- `CpuTests24.cs::Main` / `test_protocol_cpu.py`: **17개 검사 그룹 통과**. ABI·원본 바이트 roundtrip·입력범위·단일 claim·중복 dispatch·불명 제출/미완료 callback·GPU error 상태의 모의 회귀·CPU marker의 GPU 완료 위장 거부·산출물 변조·상태/해제 불일치 거부. 이 GPU 오류들은 CPU 상태기계 모의 입력이며 실제 GPU 재현이 아니다. 새 실행 폴더는 만들지 않았다. `check_prefix_cpu.py::main` / `PREFIX24_CHECK.json`이 소스·컴파일·fixture·호출 금지·CPU 결과를 연결한다.
- **실행 전 남은 조건:** 최신 Editor/project/입력·미저장 내용 preflight, 신규 compute 에셋만의 검토·import 및 실제 variant 확인, 정상 서버 승인 절차가 필요하다. 이후에도 stage1 하나만 제출하고 실제 완료·CPU 바이트 일치·소유 자원 해제·상태 보존을 읽어 확인한 뒤 별도 판단으로 stage2를 고려한다. 자동 진행·timeout 재시도는 없다. 기존 두 차례 D3D11 reset의 정확 원인은 여전히 미확정이며, CPU 컴파일/작은 dispatch/배열0만으로 GPU 재개 안전을 선언하지 않는다.
- **미완 유지:** 16서브샘플 깊이 운반·안와 직경 정규화·곡선 중점 복구는 기존 CPU/helper 수준이며 이 prefix나 실제 renderer에 연결하지 않았다. 최종 가림/합성·전체 캐릭터·유한 팔레트·외곽선·시간 안정성 및 제품77 교체도 미검증/미적용이다. 보호35파일·원래 modified30·외부 native47백업은 디스크 해시로 다시 비교한다. 현재 메모리 native 상태 보존을 새로 증명한 것은 아니다.

#### Direct24 기하·가림 런타임 후보 연결 — Unity/GPU 미실행 (80ed085d 당시)
- **적용 범위:** `experiments/pixel-pipeline/2026-11-02-bounded-form115/runtime24/`. 기존113을 바탕으로 생성한 C# 4파일·compute·원본 UV/primitive/ring 입력·정확한 diff다. `prepare_runtime.py`가 원래 소스와 변경을 대응한다. 제품77/Assets/현재 Editor는 변경하지 않았다. 이번 단계 Unity 호출·import·Play·GPU 장치 생성·dispatch는 모두0이다. 관련 커밋은 이 경로의 `git log`로 찾는다.
- **호출 순서:** `SourcePigment113_Geometry24.cs::Update/ValidateUV24`의 현재 평가 정점·안와 직경/깊이 → `WholeEye107_Geometry24.cs::RefitOnly24/ExternalBindings24` → `RegionDriver113_Geometry24.cs::Draw`의 `CurveColumns24/ColumnVisibility24` → 기존 PrepareCells/Gather 및 **본문 그대로인 BuildSubsets/Enumerate/Reduce/Write 4커널** → `PrepareCarrier`의 목적지16표본 생성/AssignedVisibility24 → `Forward113_Geometry24.cs::ComposeRegion113`에서 외부 앞머리 합성. prefix24는 고정 입력의 독립4커널 시험이고, 이 runtime24는 이후 실제 프레임 기하/가림까지 잇는 별도 미실행 후보다. CPU 기대값을 GPU 결과로 읽어 넣지 않는다.
- `Geometry24.hlsl::CarrierQueries113/Destination24/AssignedVisibility24/ComposeRegion113`: 배정된 부위/owner의 실제 raster 깊이는 개별 보존하고 빈 표본만 셀 내 평균 깊이로 운반한다. 전부 없으면 현재 ring 깊이 범위 내 실제 선택 깊이만 허용한다. 생산·조회·최종 머리 비교가 동일16좌표/인덱스를 사용한다. **8x raster의 깊이 표본 자체를 새16좌표의 직접 측정으로 승격하지 않는다.** 가시성은 운반 후16목적지에서 다시 조회한다. source anchor/carrier origin/main 표시 offset을 별도 계약으로 유지한다.
- **곡선 복구:** `CurveColumns24/ClipCell24`는 기존 arc-weighted mean의 경계 행을 보존하고, 해당 셀 안 실제 곡선 부분의 arc midpoint/깊이/원본 UV를 구한다. 단순 중점으로 경계 행까지 바꾸면 F103/F111 owner2 칼럼0이3→4로 이동하는 반례가 있어 분리했다. 원래 native 피부 primitive는 WholeEye 슬롯0이며 안검 슬롯3이 아니다. `GEOMETRY_BINDINGS24.bin`의 slot/renderer/submesh/primitive와 현재 UV·실제 alpha를 확인하고, 확정 가시성이 있을 때만 기존 안검 LUT를 사용한다. 현재 UV가 바뀌면 `ValidateUV24`가 재생성을 요구한다. texture/material 내용의 임의 in-place 변경에 대한 전체 cache generation 자동 검출은 미검증이다.
- **CPU 실측:** `regression_runtime24.py` / `REGRESSION_RUNTIME24.json`: 같은 source의12프레임, 기존 문제22좌표·목적지352개·개별 raster 깊이220개 보존, 이 범위 바탕 후퇴 상태0, 확정 앞머리 가림 보존. 기존3역할 가중치의 명시적 scalar 변환110,592개 bitwise 일치, 원본 슬롯10,176건/경계 열192개 확인, 현재 ring의0.5/1/2배72검사. 고정3e-5 깊이 epsilon을 포함한 전체 렌더의 스케일 불변성을 입증한 것은 아니다.
- **Close 한계:** F107의 `(8,5)` 원본 곡선 길이0.05182838px에서 source UV alpha `[1,1]`, 목적지 외부 얼굴 가시성 `[1,1]`로 CPU 복구 가능했다. 이는 원래 UV 곡선 경로의 보간점이며 인접 native carrier ray의 UV와 같다고 주장하지 않는다. 저장된 완전Close 입력의 홍채/흰자 배정0은 확인했지만, **새 GPU의 Close100 잔상0/재개방/움직임/최종 owner·RGB는 아직 미검증**이다. F103/F111의 새 흰자 배정과 운반 연결도 CPU oracle로만 검사하며 업로드하지 않는다.
- **컴파일·비용:** `compile_runtime_cpu.py`: 실제 호출될15개 HLSL 커널과 변경 C#을 원래113 의존 소스에 연결하여 CPU 컴파일했다. 새 기하 경로의 forcing-unroll/레지스터 권고 초과 경고는 분리 후0이다. 기존 Enumerate signed 경고, Gather modulus 경고, 의존 C# unused-field3개는 기록했다. BVH stack32 및 기존 Select/Gather의 private 배열은 남는다. `prefix24/compile_hlsl_cpu.py`의 반영 검사만128 bindings까지 읽도록 확장하고 배열 허용은 명시적 runtime 검사에만 사용했다. 4커널 prefix의 기본 배열0 검사는 유지한다.
- **소유·실행 보류:** 추가 GPU 소유량은 현재 source 기준 view당338,368B(columns/16깊이/가시성/proof)이며 각 Region/SourcePigment 소유·해제 경로에 연결했다. BVH/alpha/사용자 자원은 빌려 쓰며 해제하지 않는다. 모델·메쉬·view 변경은 기존 scope 검사를 유지하고 UV는 매 프레임 확인한다. 원래 baseline/legacy 색 출력 dispatch는 제거했으며 그 디버그 RT는 더 이상 유효 비교 출력이 아니다. 기존 Capture113 observer를 그대로 재생하면 안 된다. 전체 renderer에는 원래32768×2 열거와 기존 visibility/Select 경로가 남아 **GPU 재개 예산 검토가 별도로 필요**하다. 기존 TDR 원인 미확정, 실제 GPU 성능·수명·다중뷰·최종 렌더 및 얼굴 팔레트/외곽선/제품 적용은 미검증으로 유지한다.

#### 재실행 전 실행량 감사·최소 입력 가드 — GPU 미실행
- `runtime24/audit_execution24.py` / `EXECUTION_BUDGET24.json`: 성공113의12개 저장 입력 모두 shader SHA `046b56a22fb4476fd1f7f0b642eed2a7b36ff623e042a2b1df0907fc4e0d9356`와 원본 파일이 일치했다. 기존 DXBC cache는 resource-signature로 연결했으며 실제 native-driver 실행 바이너리 attestation은 아니다. 후보와 원본의 코드·loop/배열/UAV 비교 및 각 dispatch 상한을 JSON에 기록했다. 이 단계 Unity/import/Play/GPU device/dispatch0이며 현재 Editor 상태도 조회하지 않았다.
- **원래 결과를 바꾸지 않는 제외:** 현재 합성은 Region.Write113의 Results를 읽으므로 Source/Dense의 Select 출력은 미사용이다. `WholeEye107_Geometry24.cs::Dispatch(...,selectOutput=true)`는 기존 호출의 기본 동작을 보존하고, 후보 Forward.Draw의 두 호출만false로 바꿨다. 필요한 투영/눈 ID 상수는 그대로 설정한다. Select와 사용하지 않는 legacy/control importer entry를 제외하여 후보 active kernel은14개다. Select 함수 텍스트/CPU 비교 컴파일은 남지만 새 모듈의 엔트리와 제출은0이다. 잘못된 호출이 Select를 요청하면 후보 compute 제출 전에 거부한다.
- **입력·종료 가드:** `DispatchBounds24.cs`는 격자/곱 overflow·삼각형/primitive 인덱스·키/곡선/텍스처 범위·비유한 값을 검사한다. WholeEye 생성자의 검사 위치는 자기 shader clone/버퍼 생성 전, Resize 곱 검사는 기존 자원 해제 전이다. `Forward.Draw`는 후보 compute 명령을 기록하기 전에 세 owner의 격자·입력 RT·행렬·투영 결과를 확인한다. 이는 일반 Scene/URP의 기존 raster 작업까지 중단한다는 뜻이 아니다. 현재 source에서 추가 CPU 투영 검사는 owner3개×20,459=61,377정점이며 CPU 비용도 미계측이다.
- `prepare_runtime.py::shader`의 Query/TraceExternal24는 node 인덱스가 범위 밖이거나 방문 횟수가 nodeCount를 초과하면 **메모리 읽기 전에** 중단하고 unknown을 출력한다. `ExternalBindings24`가 빌려 쓰는 실제 BVH owner의 nodeCount를 전달한다. 올바른 tree는 각 node를 최대1회 방문하므로 기존 결과를 바꾸지 않는다. 이 가드는 device fault/모든 GPU 생성 metadata를 검증하는 장치가 아니며, unknown을 투명/복구 성공으로 해석하지 않는다.

현재 저장 입력은 정준18×8, dense/carrier144×64, 원본72×32, 물리ROI16×8, 곡선846개·key20개다. 아래는 **Forward.Draw 한 번/view 하나**의 compute 명목 스레드이며 다른 Scene/URP/표시/캡처 작업은 제외한다.

| 커널 | dispatch 수 | 명목 스레드 합 | 한 dispatch 최대 |
|---|---:|---:|---:|
| PackPart | 12 | 82,944 | 9,216 |
| Refit | 48(3 owner×16 level) | 178,368 | 26,368 |
| Query | 2 | 46,080 | 36,864 |
| Select | 0 | 0 | 0 |
| CurveColumns24 / ColumnVisibility24 | 각각1 | 각각64(유효36) | 각각64 |
| PrepareCells113 / Write113 | 각각1 | 각각192(유효144) | 각각192 |
| GatherEye113 | 1 | 2 | 2 |
| BuildSubsets113 | 1 | 16,384 | 16,384 |
| Enumerate113 | 1 | 4,194,304 | 4,194,304 |
| Reduce113 | 1 | 128 | 128 |
| CarrierQueries113 / AssignedVisibility24 | 각각1 | 각각2,048 | 각각2,048 |
| ComposeRegion113 | 1 | 128 | 128 |

- **반복 상한:** Refit은 node당고정 작업. CurveColumns는 thread당3×846(입력상한3×1024) segment 검사, PrepareCells는64표본×2부위×최대32 key 및64 native안검 검사다. Gather는 eye당16 scope, 각 RawConnected의 코드상512회×최대512셀(실제144셀), valid flood-fill은 셀 수 이내에 정지한다. Build는 valid state당24 point +8×24×24 연결 predicate 상한. Enumerate는 각 lane1상태와6 reduction round이며 초기 barrier까지 **그룹당7개**를 모든 lane이 수행한다. Reduce는 lane당512 group merge+6 round, Write는최대24point. CarrierQueries는표본당16+1 raster depth조회, Compose는16face+16hair다.
- **BVH와 큰 상한:** 실제 triangles29,542/nodes59,083, balanced depth15/DFS stack16이며 물리stack32와기존 push guard를 유지한다. 일반 입력 cap에서 triangles262,144/nodes524,287/balanced stack19다. 실제 source의 query slot48,164개를 모두 합친 유효 tree 최악 box 읽기는 **2,845,673,612회**, cap envelope는90,731,011,072회다. 수정 가드의 malformed tree는 마지막 검출 iteration1회가 추가될 수 있다. 이 값은 GPU 시간 추정이 아니다. CPU 모형 tree59,083개에서 원래/가드 순회가 같았고 cycle·잘못된 child는 unknown으로 정지했다. 실제 GPU node topology/방문량을 새로 관측한 것은 아니다.
- **열거·공유 위험:** 저장 입력 최대 np16/ni8/nw12, valid state-range 합 최대1,114,112이나 host는 여전히4,194,304lane을 제출한다. Close100의 empty header에서도 같은 그룹/barrier 제출량이다. 총73dispatch/4,522,946명목thread(원본113은77/4,594,370;80ed는75/4,523,778)다. EvaluateForm115/BoundRun115 경로는 코드/host에 없지만 기존 BVH stack, Gather private배열6개, Write의8UAV, D3D11 driver/동시 Scene GPU작업은 공유한다. aggregate Stats의 uint counter는 일반 cap에서 wrap할 수 있어 시간/안전 gate로 쓰지 않는다. 전체 callback은 이미 기록된 후 GPU 오류가 나타나면 중간 제출을 취소할 수 없다.
- **CPU 검증:** `BoundsTests24.cs.txt` / `test_bounds_cpu24.py`의18검사 그룹 통과: 실제12격자/29,542삼각형/16,928primitive 인덱스, 최대 격자, overflow/불일치/범위/NaN/Infinity 거부 등. Unity 참조 없는 순수 guard만 실행했다. 변경 C# 연결 컴파일과14 active+Select비교용1개의 CPU HLSL 컴파일 통과. 기존22좌표의 CPU 기하 회귀도 유지되며 실제 GPU 결과는 아니다. 원래4개 배정 함수 본문은 그대로다.
- **다음 최소 실행안(아직 금지/미실행):** 기존 prefix24의 STAGE1만 별도 판단 후 고려한다. 고정 F103 owner2/header `[9,5,6,0]`, BuildSubsets `(1,2,1)`=128thread/96valid subset, structured591,616B, readback4,096B이며 BVH/Select/Play/전체 runtime은 제외한다. 모든 실제 callback done/error0·CPU byte동일·input/source hash·공개 상태 동일·소유 자원 해제·마지막 COMPLETE marker를 확인하기 전 다음 제출0이다. pending/timeout/error/불명 결과는 재시도·강제 회수하지 않는다. 최초 shader/buffer 생성 자체와 모듈에 있는 다른3커널의 backend 처리는 여전히 위험이며 TDR 원인이 해소됐다는 증거가 아니다. 현재 full runtime 재생은 승인된 GPU 예산으로 보지 않는다. 현 Editor/GPU 상태 preflight와 별도 재개 판단이 필요하다.

### 승인된 prefix STAGE1의 현재 사전 확인 — 자산 부재로 제출 전 중단

- **승인/실행 구분:** 사용자가 위험 고지된 F103 BuildSubsets128thread 한 단계를 승인했다. `prefix24/preflight24/ReadPrefix24.cs.txt::CommandScript.Execute`를 공식 relay로 한 번 실행해 현재 상태만 읽었다(11:03:49 UTC). 동적 읽기 명령은 컴파일·실행 성공, relay는 EOF 정상 종료했다. GPU dispatch/import/Play/프로젝트 C# 재컴파일은 모두0이며 불명·pending 요청도 없다.
- **실제 상태:** 현재 Unity PID22952/6000.5.9f1/Direct3D11, Edit·전환false·compilingfalse·updatingfalse·pausefalse, GameMap1 scene dirtyfalse다. 현재 로드된 persistent dirty24개 목록, InputSettings 객체ID와22개 직렬화값, Keyboard/Mouse, background/Play옵션을 `EDITOR_STATE24.json`에 보존했다. 옛PID/dirty31을 현재값으로 사용하지 않았다. 11:04:44 UTC OS Respondingtrue도 별도 기록했다.
- **중단 원인:** 요구 경로 `Assets/EUnityValidation01/Direct24Prefix/Prefix24.compute` 및 `.meta`/폴더가 현재 없다. 공식 `AssetPathToGUID`도 빈값이다. 준비 source SHA와 stage1command SHA 및13fixture hash는 일치하고 run claim은 없으나, 실제 importer variant/kernel ABI는 검증할 수 없다. 예상 차이 시 중단하라는 지시에 따라 자동 자산 생성/import나 다른 셰이더 fallback을 하지 않았다. 서버 거절은 아니다.
- **다음 필요한 최소 조치(미실행):** 준비된 exact source+기존 `.meta`를 격리 경로에 추가하고 부모 폴더 identity를 Editor에서 정식 생성/등록한 뒤 shader만 import하여4kernel/threadgroup ABI를 확인해야 한다. 이 준비에는 Assets C#·domain reload·Play가 필요하지 않으며, import 자체의 backend 위험은 남는다. 현재 테스트는 제출 전 중단 상태이므로 GPU callback/바이트 동등성/소유 GPU자원 해제 결과는 없다. 디스크 보호35/사용자변경30/기존 native47백업 해시는 동일하며 현 native 전체내용 동등성은 추가 직렬화하지 않았다. 재현과 정확한 중단 사유는 같은 폴더 `OUTCOME24.json`, `DISK_PREFLIGHT24.json`, `REQUEST24.json`, `REPLY24.json`, `OS_STATE24.json`에 있다.

### prefix shader-only import 준비 실패 — GPU0, 추가 Unity 요청 중단

- 위 연결 누락을 해결하기 위한 exact shader/meta 추가·shader-only import가 승인됐다. `prefix24/import-stage1/ImportPrefix24.cs.txt::CommandScript.Execute/State`를 공식 relay로 한 번 호출했다. CPU 컴파일은 성공했으나 11:11:07 UTC에 State에서 `NullReferenceException`이 발생했다. 44개 native 직렬화 백업을 기록한 뒤 global 상태 수집 구간에서 실패했으며 `IMPORT_BEFORE24.json`과 `IMPORT_INTENT24.json` 모두 없다. 폴더 생성/파일 추가/import/dispatch/Play는 **0**이다. relay 오류 결과와 정상 EOF가 확인돼 pending/불명 실행이나 서버 거절은 아니다. source의 import 전 단계 실패를 GPU/TDR 재발로 취급하지 않는다.
- **원인 구분:** 디스크 CASE 해시는 기존0bd1a3c7…와 같고 `Globals`74항목에 null Name/Type/record는 없다. State의 역직렬화 DTO 또는 global record에 null이 유입됐을 가능성이 있으나 실제 관리 값은 관측하지 않았다. 확정 결함은 역직렬화 결과의 검증을 생략한 것이다. `IMPORT_FAILED24.json`의 StateEqual=false는 사후 비교 미수행이며 실제 상태 변화를 증명하는 값이 아니다. 기존 자산3703meta의 GUID충돌은 없었으나 Editor registry GUID검사는 State 뒤에 있어 미실행이다.
- **준비한 최소 수정(미실행):** `prepare_import_fix24.py`가 원래 실행 source를 보존한 채 `ImportPrefix24B.cs.txt/.patch`를 생성한다. DTO를 public으로 하고 기존 Protocol처럼 non-generic JsonUtility overload를 사용하며 CASE/expected 결과를 native snapshot 전에 검사한다. B는 CPU C# 컴파일 경고0이나 역직렬화 원인 해소의 실측 증거는 아니다. 신규 GPU 알고리즘/커널은 추가하지 않았다. 오류 이후 추가 Unity/GPU 요청은 중단했고, 11:13:24 OS에서 PID22952 Respondingtrue/CPU238.640625초였다.
- **보존/다음 조건:** raw44백업은 로컬 `import-stage1/before-native-*.json`에 보존하고 repo에는 해시/바이트 manifest만 보관한다. 설정 setter·GPU자원 생성·소유자원 해제는 실행되지 않았다. import/gpu 단계를 계속하려면 먼저 B의 역직렬화·현재 공개/native 상태 비교와 shader-only import를 확인해야 하며 동일 미확인 요청을 재전송하지 않는다. 단일 BuildSubsets는 아직 제출되지 않아 실제 ABI/readback/CPU bytes 동등성 결과가 없다. 증거 `ImportPrefix24_REQUEST/REPLY.json`, `IMPORT_FAILED24.json`, `BACKUP_MANIFEST24.json`, `OUTCOME_IMPORT24.json`, CPU수정 컴파일 `IMPORT_FIX_CPU24.json`을 같은 폴더에 보관한다.

### prefix F103 BuildSubsets 단일 GPU 단계 통과 — 전체 runtime/제품은 미실행

- **관리 예외 원인과 수정:** `import-stage1-b/ARRAY_PROBE24.json`에서 현재 동적 명령의 JsonUtility는 사용자 정의 객체 배열을 읽지 않았고, 수동 구성한1항목도 ToJson이 `{}`를 출력했다. 문자열 배열2항목은 정상이다. public DTO/non-generic overload만으로는 해결되지 않았다. 이 환경/타입의 재현이며 모든 Unity JSON 구현에 대한 일반 주장은 아니다. `PrefixMetadata24.cs::Decode/ReceiptBytes`가 기존 `Json58Linear66`의65,536자 제한 reader를 재사용하여 Case/InputFiles/Globals와 Receipt/Outputs 두 구조만 명시적으로 매핑한다. reflection/새패키지/Assets C#은 없다. `prepare_metadata24.py`가 기존 host의 Encode/Decode delegate만 교체해 exact 단일 단계 명령을 만든다. shader/루프/배정 수식은 변경하지 않았다.
- **CPU 및 읽기 검증:** `metadata24/test_metadata_cpu24.py`의21검사 통과(기존17 +실제 nested case74/13항목·Outputs2개 roundtrip·중복/후행 JSON·입력예산/필수필드), Unity/host DLL/GPU device는 CPU시험에 로드하지 않았다. ReadMetadata24는74항목·현재 상태 수집 성공, 원래 관리 예외 때 보존한 raw44내용도 동일했다. 기존 JsonUtility의 단순 primitive/string[] State/Event 출력은 유지했다. 당시 미수정 `STAGE1~4.command.cs.txt`는 실행하지 않았고 실제 실행본은 `metadata24/STAGE1_METADATA24.command.cs.txt` 하나다. 아래 후속 CPU 통일 작업에서 기존4명령을 갱신했으며 새 버전의 GPU 검증과 후속 단계 실행은 아직 없다.
- **실제 import/ABI:** 11:24:05 UTC에 새 `Assets/EUnityValidation01/Direct24Prefix` 폴더를 Editor로 생성하고 exact Prefix24.compute/meta를 CreateNew로 추가하여 해당 shader만 import했다. 폴더 GUID59ba6080fb8e109439f84b95759ffeac, shader GUIDa86ba181213712cd5cb5d48972d38e82, sourceSHA a85bb725…/metaSHA179cc454…이다. 실제 GetKernelThreadGroupSizes는 Build/Enumerate/Reduce64×1×1, Write8×8×1, shader 메시지 error0이다. 기존 X3203 signed/unsigned 경고4개만 있었고 relay가 경고를 isError 형태로 반환했지만 독립 IMPORT_COMPLETE24/소스/ABI/전후동등성으로 완료를 확인하여 import 재시도0이다. 실제 driver bytecode 전체 identity를 새로 추출한 것은 아니다.
- **실제 GPU 결과:** F103 source `eye113-20261102T012349564Z-df6df224-frame103`, header `[9,5,6,0]`의 BuildSubsets113 `(1,2,1)` **1dispatch/128threads**만 제출했다. 11:24:47.7716652 UTC submitted, 실제 callback I/W는11:24:58.2590307/11:24:58.2683509 UTC에 done=true/hasError=false였다. 이 간격은 Editor scheduling/readback 포함이며 GPU 시간으로 쓰지 않는다. 2×2048바이트가 frozen CPU oracle와 byte-for-byte 동일하다(SHA7413473c…/8896521c…). 완료 marker `prefix24/runs/prefix24-6344598354174e7d93b5ac1590cfd2ae/stage-01/COMPLETE.json`의 Success/StateEqual/ResourcesReleased=true, DispatchCalls1, Errornull, Outputs2를 외부 Python으로 다시 검증했다. 자원은 정상 callback 둘이 정착한 뒤 own5buffer(591,616B)/shaderclone을 해제했다. BVH/115평가기/Enumerate/Reduce/Write/전체runtime/Play 제출은0이며 다음단계는 자동 실행하지 않았다.
- **보존/한계:** `metadata24/IMPORT_BEFORE24.json`, `IMPORT_AFTER24.json`, `post-output/READ_STATE24.json` 세 상태가 완전히 같다(native44 serialized해시/객체ID·dirty24목록·InputSettings 동일ID/22값·장치·globals74·scene/pipeline/time/background/Play옵션). GameMap1 Edit/dirtyfalse다. 원본 사용자변경30·보호35파일·기존47백업 해시 보존도 별도 검증한다. 새 Unity자산3파일과 해당 폴더의 `.gitattributes`(검증된 source/meta의 byte hash를 checkout 줄바꿈 변환으로부터 보존) 외 제품77/기존자산 변경0, 설정 원복이 필요한 setter0, 강제정리/GC/SaveAssets/Refresh 직접호출0이다. Unity 자체의 자동 refresh 로그와 명시적 Refresh 호출을 혼동하지 않는다. 이전 두reset의 원인은 아직 미확정이며 한 번의 작은 단계 통과가 다른 커널·큰 입력·실시간 성능/미관/시간안정성의 성공을 보장하지 않는다. 다음 GPU 단계는 이번 승인에 포함되지 않는다.

### STAGE1~4 JSON 경로 통일·완료/pending 계약 CPU 회귀

- **현재 생성 경로:** `Prefix24Host.cs::Start`의 Encode/Decode를 검증된 `PrefixMetadata24.ReceiptBytes/Decode`로 통일했고 `prepare_commands.py::main`이 scoped `metadata24/Json58Linear24.cs`와 helper를4명령 모두에 포함한다. `STAGE1~4.command.cs.txt`, `COMMANDS.json`, `compile_cs_cpu.py`, `check_prefix_cpu.py`도 같은 의존성/해시로 갱신했다. typed nested 배열을 JsonUtility로 읽는 오래된 대입은 현재4명령에 없다. 현재 명령당 dispatch site1/auto-next0을 유지한다. f919290b의 실제 실행 source와 stage01 완료 기록/출력은 수정하지 않았다.
- **실패/중복 보강:** `Prefix24Protocol.cs::Previous`는 COMPLETE가 있어도 `FAILED.json` 또는 `PENDING-*.json`이 있으면 후속 단계를 거절한다. `ClaimStage`는 기존 폴더에 어떤 intent/submission/pending/output 흔적이라도 있으면 거절하여 INTENT만 사라진 불명 제출도 재사용하지 않는다. 빈 디렉터리에는 기존 CreateNew 원자 claim을 유지한다. 이는 metadata/제출 전 CPU 가드이며 GPU 계산/버퍼/셰이더 변경이 아니다.
- **실제 검증:** 현재 C#7컴파일 경고0, `CpuTests24.cs`/`test_protocol_cpu.py`28검사 통과. 실제 stage01 COMPLETE와2출력은 readonly로 검증했고 nested Outputs 재직렬화 일치, duplicate/pending/failed/orphan SUBMITTED/변조 sourceId·출력바이트 거절을 temp 복사본에서 검사했다. 원본 run 전체 파일 hash가 전후 동일하며 CPU test가 stage02를 만들지 않았다. 이미 있던 같은 shader source의 CPU HLSL4컴파일 근거는 재사용했고 이번 shader compile/Unity/import/GPU/Play는0이다. 새4명령 버전은 CPU 검증이며 GPU 미실행이다.
- **다음 Enumerate 비용:** `audit_enumerate_cpu24.py::main`은 실제 GPU stage01의2×2048바이트를 읽어 F103 `[9,5,6,0]`을 CPU에서 재계산했다. 현 stage2는32×64=**2,048threads**, subset flag 유효쌍1078/비중첩680, 결과32×48=1,536B다. shared3,072B/group, 6 reduction round/7 barrier, 총224 group barrier points/14,336 lane 도달/2,016 merge 호출, merge당 Less최대2×4 score검사다. BVH/private배열/point·curve loop는0이다. Frame index0..3, subset0..31/4096..4159, output group0..31; structured 할당3,671,040B(기존65536 group buffer 포함)다. 이 수치는 GPU 시간 또는 TDR 안전 증명이 아니다.
- **분할 판정:** 기존 shader는 매 dispatch의 SV_GroupID가0으로 시작하므로 단순16group×2회는 후반을 누락하며 실제12group이 달라졌다. group-base를 state와 output index 양쪽에 더하고 기존 group 내부 reduction 순서를 그대로 두는 CPU 모델은1/2/3/4/5/8/16/31/32group 단위9분할 모두1536바이트가 원래 oracle와 같았다. 완전 분할에는 작은 offset uniform 및32group coverage/완료 계약 연결이 필요하지만 구현/import/GPU 검증은 하지 않았다. shader 변경 없는 최소 후속 probe는 group0 **1group/64threads/48B**만 검사하는 방법이며 현재 host는 이 부분출력 모드를 아직 지원하지 않는다. 이 probe는 완전 stage2가 아니므로 stage3용 COMPLETE로 처리하면 안 된다. 세부 상한/반례/hash는 `ENUMERATE_BUDGET24.json`이다. 다음 GPU 실행은 미승인 상태로 유지한다.

### 승인된 F103 Enumerate 단일 GPU 단계 완료

- **현재 상태/입력:** 사용자 승인으로 HEAD7070919a의 exact `STAGE2.command.cs.txt`(SHAca7a34e8…) 하나만 실행했다. `prepare_enumerate24.py`와 `enumerate24/PRE_STATE.command.cs.txt`는 이미 성공한 상태 수집 함수를 재사용한다. 12:43:29 UTC 현재 PID22952/같은 프로젝트/Respondingtrue 확인 후, 12:46:33 UTC Edit·전환/compile/updatefalse·GameMap1 dirtyfalse, native44/dirty24/globals74/Input22값과 동일ID를 새 기준으로 보존했다. 기존 실제 stage1 COMPLETE/2출력과 exact CASE/fixture/shader 해시·GUID, Enumerate64×1×1 ABI를 확인했다. 신규 shader 오류0, 이전 signed/unsigned 경고만 있었다. shader/import/분할 변경은0이다.
- **실제 결과:** `Enumerate113 (32,1,1)` **1dispatch/2,048threads**만 제출했다. submitted12:47:10.4590787 UTC, 실제 callback12:47:38.3747410 UTC done=true/hasError=false. 이 간격은 Editor/readback scheduling을 포함하므로 GPU시간으로 쓰지 않는다. `groups.bin` **1,536바이트**는 CPU 기대값과 byte-for-byte 동일(SHA98adf829086820b9cbfd16c34ea85fec498ee29a68e2e34565f1844cc422b2b9)이다. `runs/prefix24-6344598354174e7d93b5ac1590cfd2ae/stage-02/COMPLETE.json`의 Success/StateEqual/ResourcesReleased=true, DispatchCalls1, Errornull을 독립 Python으로 재검증했다. callback 정착 전 재제출·조기 해제0, 이후 own3buffer(3,671,040B)/shaderclone은 정상 해제했다. 나머지 Reduce/Write/전체runtime/Play/자동다음제출은0이다.
- **보존/증거:** `enumerate24/pre/STATE.json`과 `post/STATE.json`이 완전히 같고 stage02 BEFORE/AFTER도 동일하다. native44 내용·ID/dirty24·global74·InputSettings 동일ID/22값·장치·씬/pipeline/time/옵션을 보존했다. 12:49:53 UTC OS Respondingtrue다. 기존 stage1 원본10파일, shader/meta, 사용자변경30/보호35/기존47백업 해시도 동일하다. raw native백업은 로컬에 유지하고 repo에는 상태/hash와 실제 callback/1536바이트/완료 marker만 보관한다. 결과 `enumerate24/RUN_RESULT_ENUMERATE24.json`; 실행통로 `relay_enumerate24.py`는 Pre/Stage2/Post만 허용한다. `check_prefix_cpu.py`는 이제 완료된 stage1/2를 readonly로 검증하며 stage2의 실행 source SHA를 COMMANDS와 대조한다. COMMANDS의 submitted=false는707 생성 시점 기록이고 실제 실행 상태는 이 절과 stage02 marker가 기준이다.
- **현재 경계:** 이 결과는 저장 F103 입력에 대한 두 번째 compute 단계의 실제 GPU 동등성이다. 새로운 캐릭터 렌더/미관/시간안정성 성공이나 이전reset 원인 해소가 아니다. 다음 Reduce/Write GPU 실행은 승인받지 않았고 stage03/04 폴더도 생성하지 않았다. 제품77/사용자 자산/설정은 바꾸지 않았다.

### 승인된 F103 Reduce→Write 두 단계 통과

- 사용자 승인 범위에서 `STAGE3.command.cs.txt`의 Reduce11364thread를 먼저1회 제출하고 actual48B·done/error0·ResourcesReleased/StateEqual 확인 및 readonly mid 상태 비교 뒤에만 `STAGE4.command.cs.txt`의 Write11364thread를1회 제출했다. `reduce-write24/relay_rw24.py`는 Pre/Reduce/Mid/Write/Post만 명시적으로 허용하며 자동 다음 단계가 없다. 실제 GPU `stage-03/best.bin`48바이트를 `Prior("best")`로 Write에 이어 썼고 CPU winner를 대체 업로드하지 않았다.
- Reduce48바이트(SHA3f193d98…)와 Write4×2304=9216바이트가 모두 frozen CPU oracle와 정확히 같았다. 실제 callback5건 모두 done=true/errorfalse, 두 COMPLETE의 Success/ResourcesReleased/StateEqual=true다. 4출력의 x8..17인80셀은 sentinel -12345.25를 그대로 유지했다. 따라서 Write는 한쪽 눈을 포함한8×8tile 검증이며 전체18×8/전체캐릭터 렌더가 아니다. own buffer/clone은 각 단계 callback 정착 뒤 해제했다.
- `reduce-write24/pre/STATE.json`, `mid/STATE.json`, `post/STATE.json`이 완전히 같아 native44/dirty24/globals74/InputSettings 동일ID·22값/장치·씬·옵션을 보존했다. 제품77·기존 shader/자산·원본 사용자30/보호35/기존47백업도 보존했다. Play/import/전체renderer/EvaluateForm115는 이번 두 단계에서0이다. 기록 `reduce-write24/RESULT_RW24.json`, 실제 marker `runs/prefix24-6344598354174e7d93b5ac1590cfd2ae/stage-03/04/COMPLETE.json`; 원본 raw native 백업은 로컬에 유지한다.
- 이후 별도 사용자 승인으로 두 단계 정상 통과 후113기반2.4 실제 runtime/전체렌더 검증까지 이어가는 범위가 추가됐다. 그 작업은 아직 이 두 단계 결과에 포함되지 않는다. 기존115평가기 재실행, 입력설정교체·CUA·강제종료·초기화·드라이버/TDR/보안변경·push 금지는 유지한다. 이전reset 원인 미확정과 남은73dispatch/full-runtime 비용을 prefix4kernel 통과로 안전 보장하지 않는다.

### Argon2.4 실제 런타임 재연결 · 전체 캐릭터 41프레임 (2026-11-02 14:00~14:08 UTC)

- **적용 범위:** 기준 `80ed085d`의 `Forward113_Geometry24.cs::Draw`, `RegionDriver113_Geometry24.cs::Draw/PrepareCarrier/ComposeBindings`, `SourcePigment113_Geometry24.cs::Update`, `WholeEye107_Geometry24.cs`를 기존 성공113 외부 실행기에 연결했다. 경로는 `experiments/pixel-pipeline/2026-11-02-bounded-form115/runtime24/full-render24/`. 기존 product77 기본 바인딩은 유지한다. 새 Assets는 `Assets/EUnityValidation01/Direct24Geometry/ForwardEye113_Geometry24.compute`와 meta뿐이며 C# Assets import/domain reload는 하지 않았다. 후보 shader SHA `9f749bcfeb272a805b80f02ec69cbae58d69138c7a5fcf4df7aaed4bfa5617e9`, GUID `e262c25c65887454682f2280a1f71fdc`.
- **최소 연결 변경:** CPU 검증된14커널 수학 코드는 유지하고, 원래113의 동일 본문 `ComposeWhole113` pragma만 추가해15커널을 import했다. 전체 합성은60×34그룹/130,560threads, 반복문·private 배열0인 기존 본문이다. `CaptureFull24.cs::Capture/CaptureFull113`는 미생산 legacy/Select 버퍼를 읽지 않고 실제 assigned-depth/visibility16표본과 최종 RGB/owner를 기록한다. 캡처 전용 `ExportSource111`은 기존111의 동일 메서드를 재사용했다. `prepare_full_render24.py`, `prepare_sequence24.py`, `prepare_motion24.py`가 정확한 전체 실행 소스를 만들며 CPU C# 컴파일을 통과했다. `EvaluateForm115/BoundRun115` 참조·제출은 없다. import 경고를 relay가 오류 응답으로 묶었지만 독립 `import/COMPLETE.json`은15개 ABI, 오류0, 전후 상태 해시 동일을 확인한다. 재import하지 않았다.
- **실제 실행:** F103 Reduce/Write 완료 커밋 `fe98a36b` 뒤 별도 명시 승인으로 열린 눈1프레임을 먼저 실행·정상 종료·복원한 다음, Close/reopen 및 hair ON/OFF12상태, 기존97 정상 게임입력 관찰기의 위상10/보행8/회전10프레임을 각각 새 고유 폴더에 기록했다. 총3회 Play/41개 실제 GPU 프레임이다. CPU winner/색 재생을 GPU 결과 대신 업로드하지 않았다. `RAW24.zip`+`CAPTURE_INDEX24.json`에 실제 원시 packet/sourceId/frame/serial 및 완료 marker를 보존한다. `RESULT_FULL24.json`, `sequence24/RESULT_FULL24.json`, `motion24/RESULT_FULL24.json`, `REVIEW_FULL24.json`이 각 범위를 분리한다. 마지막 두 실행은 `sequence24/STATE113-0028-finished.json`, `motion24/STATE113-0060-finished.json`이다.
- **확인한 효과:** Close50 포함 모든 양안 배정은 이 입력에서 최적해1개이며 오류 플래그0. evaluated Close100의 최종 홍채/흰자0셀, 재개방 시 원형 파트 배정 복귀를 확인했다. 실제 hair ON/OFF 전 canonical 역할/owner와 RGB8은 동일하고 최종 가림만 달라진다. 위상 sweep은 실제 투영 x가0→0.999985px 이동하고 돌아온10연속 프레임이며 canonical 역할/owner 배열과 색 RGB8이 전부 동일했다. 실제 정상 입력 보행8프레임에서1.166667world-unit 이동과 회전10프레임의 quaternion 변화를 기록했다. 41프레임의 눈 파트 최종 팔레트 밖 RGB8은0건, 각 프레임 눈 ROI 밖 전체 RGBA는 동일 프레임 제품77과 byte-equal이다. 원배율·nearest 확대 및 시퀀스를 실제 열어 확인했다. 초기에 확대 그림만 보고 열린 눈이 전부 소실됐다고 한 중간 판단은 원시 RGB/owner 대조로 정정했다.
- **미해결/미채택:** Close75 목적지 carrier 부족(-116)1셀, 회전 최대2셀이 남는다. 확정 차단(-117)과 구분하며 depth나 색을 발명하지 않았다. 순수 위상에서 가림 전 원형은 안정적이지만 최종 머리 가림 뒤 흰자/안검 노출량 변화가 남으므로 전체 시간 안정성 성공으로 부르지 않는다. 전체 얼굴 UV 영역화·명암/유한 팔레트·외곽선 문제도 미완이다. 이전115 reset의 정확한 원인과 전체 GPU 시간은 여전히 미측정/미확정이며 이번 정상 실행을 일반 안전 보장으로 확대하지 않는다. 제품77 기본 경로 대체는 하지 않았다.
- **보존/수명:** 세 실행 모두 정상 Edit 복귀, observer 제거, 소유 Forward/Carrier/Canvas dispose, RT 수30→30. 입력 설정 동일 참조/22값/장치·current keyboard·가상 장치 제거, 옵션/background/time/pipeline/global74 복원 확인. native 비교 대상은 최초43개, 후속44개로 모두 내용 동일이며, 새로 로드된 FaceSourceOwner202의 native hash도 기존47백업의 `e2e4fc2a9cda1b0c7a32f4a8273779dffea81c17ec8a0fe4e4683fb25ec32b24`와 동일했다. 첫 실행 후 ProjectSettings4개·Face mesh·내부 Editor 객체에 dirty 표시가 추가됐고 후속 각2개 내부 객체 표시도 추가됐다. 표시를 지우거나 저장하지 않았다. `PRESERVATION_FULL24.json`에 정확한 차이를 기록한다. Undo/nonserialized 전체 복구 보장은 아니다.
- **메모리 한계:** `Profiler.GetTotalAllocatedMemoryLong` 최초 +474.32MiB,12상태 +59.27MiB,28동작 +20.81MiB. physical working set이 아니다. 같은 기록에 Mono/Reserved와 시각을 함께 보존했으며 RT 수 복귀만으로 CPU 메모리가 완전히 원복됐다고 하지 않는다. 강제GC/Unload/정리는 하지 않았고 이 수치만으로 누수를 확정하지 않았다. 원본 사용자 수정30/보호35/기존 native47백업의 디스크 무결성은 별도 확인한다.
- **검토 그림:** `GPU_RUNTIME24_WHOLE_CHARACTER.png`, `GPU_RUNTIME24_CLOSE_HAIR.webp`, `GPU_RUNTIME24_MOTION.webp`. Library 저장 성공 ID는 각각 `libfile_205110286ff08191816f989bb200bbae`, `libfile_89621f979620819183d13757ab23f7bf`, `libfile_d469e6107d2c819189b895d82291eb7d`. 공식 helper의 Windows `os.setxattr` 미지원으로 로컬 xattr 적용만 실패했으며 저장 자체는 성공했다. 정확한 Library identity/version은 `LIBRARY_FILES24.json`에 보존한다. `report_full24.py::main`, `review_full24.py::analyse/animation`, `board_full24.py`가 원시값 검증과 표시 변환을 담당한다. 새 runtime 결과와 이 인계는 같은 선택 로컬 커밋으로 보존하고 사용자 파일은 stage하지 않는다.

### carrier 깊이의 부적절한 ring 범위 제한 수정 · 남은 공유 피부/격자 계약

- 기준 커밋 `cf4c72f0`. 새 근거·실행 소스는 위 `full-render24/carrier-fix24/`에 있다. `trace_carrier24.py::main`은 기존 실제41프레임의 배정 깊이17,696표본을 검산해 좌표/직접 깊이 생산이 일치함을 확인했다. carrier가0인11셀은 전부 실제 native 안검 표본과 양의 확정 가시성을 가졌으나, 안와 개구부 정점의 z 범위에서1.24~6.04mm 벗어나 있었다. `Argon2.4.md`의 ‘선택 깊이는 ring z 구간 안’이라는 전제가 이번 안검에 성립하지 않은 것이며, 새 무표본 상태를 유효 source로 추정한 것이 아니다. `replay_carrier24.py::main`은 같은 source/frame의 기존 GPU query176개와 CPU 기하·alpha 판정 일치 뒤 변경 예상치를 계산했다.
- **최소 수정:** 별도 `Assets/EUnityValidation01/Direct24Carrier/ForwardEye113_Geometry24.compute::CarrierQueries113`의 zero-raster fallback에서, 이미 `Write113`이 현재 native 표본/곡선 근거로 배정한 role6 안검의 유한 양의 `id.z`는 aperture-ring z 범위로 기각하지 않는다. 홍채/흰자 조건·직접 깊이·같은 셀 평균 운반·16개 목적지 좌표·외부 피부/머리 가림·팔레트·배정 목적함수는 유지했다. 새 버퍼/바인딩/임계값/셀 수 제한은 없다. `prepare_fix24.py`의 CPU HLSL audit은64threads/private 배열0/기존16회 합산 루프이며, C# 전체 외부 실행기 컴파일과 실제 shader-only import15개 ABI/상태 보존을 통과했다. 이전 후보와 제품77 기본값은 변경하지 않았다.
- **실제 재검증:** 새 sourceId로 Close/reopen·hair12상태 및 위상/보행/회전28프레임, 총40개 실제 GPU packet을 수집했다. 양쪽 실행 정상 Edit 종료, native44 내용 동일, input 동일 참조/22값/장치와 임시 설정·globals 복원, 소유 buffer/RT/shader 해제 확인. `validate_fix24.py::main`/`VALIDATED_FIX24.json`: 현재 입력에서17,168배정 깊이 검사, 직접 깊이12,824개 bit-exact, 새 zero-raster source fallback은 exact. 평균 운반에는 순차 CPU float32 대비 최대1ULP(9.536743e-7 depth-unit) 차이가 있어 bit-exact라고 하지 않는다. 이 차이의 compiler 원인은 미확정이다. 실제 새 가림 query224개는 같은 현재 기하/alpha CPU 판정과 exact. carrier 미확정(-116)은40프레임 모두0, 최종 눈 파트 팔레트 밖 RGB8도0이다. Close100 홍채/흰자0·재개방·가림 전 hair ON/OFF 역할/색과 위상 원형을 유지했다.
- **효과의 범위:** 같은 현재 입력의 이전 조건 **CPU** counterfactual과 실제 수정 GPU를 대조하면 안검 RGB 복구7건(회전4, hair 통제 상태3)이며 나머지 머리 차단은 유지된다. 동일 입력의 구/신 두 GPU 변형을 동시에 돌린 결과는 아니다. 별도 Play 사이 피부/머리 RGB 입력이 달랐고 hair 통제3상태의 선택 source 깊이도 최대0.370mm 달랐으므로 전체 사진 차이를 수정 효과로 집계하지 않았다. 실제 양쪽 사진과 owner debug는 `GPU_CARRIER_FIX24.png`, 실제 새 회전은 `GPU_CARRIER_FIX_TURN24.webp`. Library ID는 `libfile_2cf539572b54819197d358525c7cbfc8`, `libfile_3c225d65cff4819197270af3ee15cf12`. 로컬 xattr만 Windows 미지원이며 identity JSON은 보존했다.
- **남은 Close75는 input 부재가 아님:** head-view tile(9,3), canonical(10,4), owner1의 native 안검 source는(222.9603,53.0067)에서 가시량1, 등록된 source 표본은(222.2487,53.3583), 최종 목적지 중심은(221.5,52.5)다. 목적지16표본은 skin primitive2691/3177/2692/2718/2717/2693/2716/2694/2715에 차단된다. `CLOSE75_SKIN_AFFILIATION24.json`에서9개 모두 눈1 blink의3정점이 움직이지만 눈2 영향도 전부/일부 존재하며 ring 직접 접촉은0이다. 따라서 현재2.3 단안 성분 규칙에서 mask0인 **양안 공유 피부**다. 깊이 복구 후 -116→-117로 원인을 확정했지만 눈매가 복구됐다고 세지 않았다. 원본이 없는 색을 채우거나 이 피부를 임의로 투명하게 만들지 않았다. `VALIDATED_FIX24.json::close75SkinEvidence`에 source UV/primitive/barycentric와 목적지 각 hit를 보존한다.
- **남은 위상 노출 변동도 원형 배정 실패와 별개:** `phase_exposure24.py::main`/`PHASE_EXPOSURE24.json`: 실제10프레임에서 카메라 기저 변화0, renderer0/1/2 평가 정점 최대 변화4.77e-7/1.19e-7/2.38e-7 world이며 hair가 실제로 크게 움직였다는 근거는 없다. 원형 역할/색은 동일하지만 최종 흰자5위치가 달라진다. owner2 canonical(3,4)은0→0.125px 이동에서 목적지 중심214.5→215.5px로 한 칸 이동하고, 눈 격자 snap delta는-0.4362→+0.4388px, 물리 머리4×4 가림은12/16→0/16으로 변한다. 최종 `ComposeRegion113`의 면적8 이상 판정이 이 변화에 따라 눈/머리 소유권을 전환한다. 현재 목적지 query의 계산 오류는 아니지만, 안정된 눈 정수 배치와 머리 물리 격자의 서로 다른 이동을 아직 공동 처리하지 못한다. 실제 가림이라고 단정해 시간 안정성 목표에서 제외하지 않는다.
- **Argon 검토 질문(두 개, 새 디자인 숫자 선택 아님):** (1) 현재 단안 소유권에서 제외되는 양안 blink 공유 피부를, 원본에서는 가시인 안검의 재배치/확대와 함께 어떤 source-local eye-union/canvas 표면으로 운반해야 하는가? 위9삼각형의 실제 source/목적지 가림을 유지하면서 이 이중 절단을 피할 명시적 shared-skin 소유권/변형 규칙이 필요하다. (2) 동일 포즈의 공통 소수 이동에서 눈과 외부 머리의 정수 배치/가림을 어느 공통 변환 또는 대응 캐시에 함께 묶어야 하는가? 눈만의 안정성을 유지하며 unsnapped 머리를 목적지에서 다시 표본화하는 현재 순서는 최종 흰자 형태를 바꾼다. 단순 history 강제보존이나 목적지 가림 무시는 답으로 채택하지 않는다. 현재 재현에는 위치·메쉬 추가 캡처가 필요한 것이 아니라 이 두 표현의 결합 규칙이 부족하다. 기존 데이터로 해결 불가능하다는 일반적 증명은 아니다.
- **메모리/44번째:** 추가 두 실행의 `GetTotalAllocatedMemoryLong` 증가는35.21/35.90MiB, Mono used는 감소, RT는각30→30. `WriteOwnedPlane`의 최대1MiB owned NativeArray는 완료 뒤 finally Dispose, Forward/Carrier/clone 해제와 callback 제거가 있다. 자체 static 대형 배열 보유는 발견하지 못했으나 retired 객체의 readonly CPU 배열·Editor/RenderGraph 보유 root를 실측하지 않았으므로 누수 해소/정상 캐시로 확정하지 않는다. 첫43 목록에서 빠졌던 FaceSourceOwner202는 이후44 목록에 포함됐고 직렬화 SHA는 원본47백업의e2e4fc2a…와 동일하다(`MEMORY_AND_44TH24.json`). 비직렬화 native 전체 상태 보장은 아니다. 제품77/사용자30/보호35/native47백업을 보존하며, 위 구조적 두 항목을 임의 우선순위/새 GPU 평가기로 덮지 않고 미채택으로 유지한다.

### 얼굴 확정 region → 유한 LUT 연결 준비 — CPU 전용, 제품77 유지

- 경로: `experiments/pixel-pipeline/2026-11-02-face-region-lut`. `ResolvedRegionInput.Build/LookupRGB8`는 원본 model/image/material/UV witness와 외부에서 확정한 `region id/decisionId→family`, 단계별 정수 Q/Qprime를 받는 CPU 입력 경계다. 재질ID·색 family·가림 owner를 합치지 않는다. 미확정 region, 부분/AA/coverage 경계는 LUT 성공에서 제외하며 유효하지 않은 Q·raster 크기·혼합 sourceId·오염된 source 출처를 업로드 전에 거부한다. `confirmed`는 외부 입력의 주장이지 의미 분할을 증명하는 필드가 아니다.
- `candidate/FaceSceneLight335.hlsl::SurfaceLayerOutput335`, `candidate/BodyPalette302.hlsl::MToonFragment`: 실제 stage pixel에 연결된 확정 `(family,k)`가 있으면 기존 `SourceLookup54→SourceRGB8ToLinear54`를 직접 반환한다. `candidate/RestoreStyle335.compute::ApplyShadeBoundary`는 같은 조회를 legacy apply/role/old==q 조기반환보다 먼저 수행하고 factor RGB를1로 둔다. 미확정/제외 입력만 기존 곱셈 경로를 유지하며 이를 유한색 완료로 집계하지 않는다. 초기480/960·최종480의 정렬된 서로 다른 입력 공급은 아직 구현하지 않았다.
- 수학 재구현0: `SourcePalette58.ExtractReference/MakePalette/ShadeIndex/Resolve`, `SourcePalette54.hlsl` 및 `reuse54`의 기존 테스트/JS 수학은 원본과 byte 동일하다. `prepare.py`는 현재 사용자 변경을 포함한 제품77 파일을 읽어 Assets 밖에 최소 diff를 생성한다. 제품 파일/기본값/UI 변경0이며 완료된 R4/R6 슬라이더 작업을 재개하지 않았다.
- `verify_cpu.py`/`CpuTests.cs`: 일반 .NET csc CPU 컴파일 및 새 입력 연결 검사11개, 기존 palette54 검사49개 통과. 저장58의 실제 GPU 결과 중 불투명62표본(동일Q52개)의 초기/최종 RGB8을 새 CPU 입력 경로로 정확히 재현했다. 2재질/63원본표본의 대표색·팔레트도 동일. 이는 이전 GPU 증거의 CPU 재계산이며 새 GPU 결과/현재 얼굴 렌더가 아니다. 간격0/.5/1/1.1 변경은 region/Q를 바꾸지 않으며 출력은 각 해당 팔레트 안이다.
- 실제104의 두피/피부·볼 칠3점·저장된 전이 경계2점은 계속 미확정으로 읽었다. parent8의 (382,704)/(380,704)/(384,704)는 RGB가 다르며 한 anchor로 만들면 원본 칠 대비를 없앤다. 이7probe의 새 얼굴 LUT 바인딩은0이며 segmentation/AA 의미를 확정하지 않았다. 필요한 입력은 약한 source child/gradient/AA를 보존하는 확정 얼굴 계층과 region→원본 표본 연결이다. 58의 재질별 family를 전체 얼굴 정답으로 승격하지 않았다.
- 잔여 계약: 같은 프레임/primitive/UV→각 stage region raster 공급, legacy Qprime class metadata와 공급 k 일치, 부분 alpha/외곽선 및 LUT 후 LineTone/AA/색변환의 별도 처리가 필요하다. `SkinSource101`는 socket skin만 공급하므로 전체 얼굴 resolver를 대신하지 않는다. 이 색 경로는 보류한 눈 공유 피부·머리 격자 질문과 독립이지만 얼굴 색 계층의 자체 미확정까지 해결한 것은 아니다. HLSL/Unity 컴파일·GPU/Play·미관·시간 안정성 검증0.
- 실행 이력/보존: `test_cpu.ps1`은 OS 스크립트 정책으로 실행 전 거절됐으며 재시도/정책 변경0. 설치된 일반 .NET csc로 CPU 검사를 완료했다. 현재 제품3파일 및 기존 tracked 변경30개의 byte hash를 보존했다. Unity 호출·Assets import·InputSettings 접근/교체·저장·삭제/초기화/종료·push0. 재현: 기존 Python 환경으로 이 폴더의 `verify_cpu.py --check-only`; `CONTRACT.json`, `INPUT_ORIGINS.json`, `RESULT.json`, `product-candidate.patch`가 범위/출처/미완을 기록한다. 관련 커밋은 `git log -- experiments/pixel-pipeline/2026-11-02-face-region-lut`로 조회한다.

### 2026-11-11 재개 — 공식 연결 복구, Argon2.5 검산과 위상 최소안 미채택

- 새 경로 `experiments/pixel-pipeline/2026-11-11-resume-argon25`. 사용자가 직접 로그인/실행한 실제 Editor는 PID28080/session2/6000.5.9f1, 프로젝트는 기존 Fantasy Survival Escape Game이다. 부모가 먼저 받은 PID8644/Hub28536은 종료돼 있었으나 원인/exit code는 미확정이며 로그인 만료로 확정하지 않는다. 이 worker의 시작 시도는 기존 인스턴스 guard에서 Start-Process 전에 멈췄다(새 실행0). 03:57UTC 공식 relay의 읽기 명령 성공, 후속 읽기에서 GameMap1/loaded/scene dirty=false/Edit/compiling=false/transitioning=false 확인. 04:09:55UTC OS Responding=true. Unity AI 생성 서비스의 현재 NoSubscription 오류와 정상 공식 MCP 명령 실행은 별개다. 새 Play·GPU dispatch·Assets import·프로젝트 C# 재컴파일0이며 읽기 명령만 동적으로 컴파일했다. 예전 dirty25/31/native47의 메모리 identity를 새 프로세스에 그대로 주장하지 않는다.
- 새 참고 원본 `C:/Users/15352/Desktop/Argon2.5.md`, SHA256 `2ddaee479dc9507c7f1e3be8967b712ddd321c120e4617575143d0fc117a17e5`. 원본 미수정, 검토 복사본은 이 실험의 `reference/Argon2.5.md`. §1 동측 blink 변위 우세/로컬 피부 공수송, §2 눈 스냅 잔차/머리 조회 보정, §3 양안 로컬 템플릿을 구분했다. §3의 폭·높이1/2 고정과 .88/.08/.30 수치를 사용자 확정 디자인으로 승격하지 않았다. 기존 눈 bank/팔레트/제품77은 유지한다. 얼굴 UV의 볼 칠·gradient·AA 분류 계약은 문서2.5로 해소되지 않았다.
- `verify_argon25.py::main`/`ARGON25_CPU.json`: 기존 Source112/Support112 원본 accessor·변위·캐시 key를 재사용했다. Close75의9삼각형 모두 실제 눈1 변위량 합이 눈2 이상이고, 기록된3정점 소속도 동측이다. 이는 단순 bool overlap만으로 배제하던 전제의 반례 근거이나, §1-B의 source-unoccluded 조건을 목적지 면제에 연결하기 전 live mask를 확장하지 않는다. 문서의 epsilon 및 optional 두 링 거리 정의를 임의 확정하지 않았다. 원래 source와 destination에 같은 면제 함수를 무조건 쓰는 코드의 영향도 분리해야 한다.
- `HeadFootprint25.hlsl::HeadShift25/Destination24`, `prepare_coordinate25.py::main`: 현재 안전한113 기반 `ForwardEye113_Geometry24.compute`에서 Assets 밖 `ForwardEye113_Footprint25.compute`만 준비했다. screen query는 bottom-left +Y, hair ROI는 top-left +Y다. 물리 픽셀의 eye snap delta를 공통4× 정수 shift로 옮기며 DirectDepth→Assigned query→Compose 검증과 hair fetch가 동일16좌표를 쓰도록 했다. 정확 연속 좌표와 rounded hair를 섞지 않으며4×근사 오차 상한은1/8px다(저장 자료 최대.07928085px). 새 kernel/buffer/dispatch0, bank/색/소유권 변경0. captured ROI 밖은 clamped edge/투명이 아니라 unknown으로 남긴다. CPU 대수 좌표320쌍 exact. 아직 HLSL/Unity 컴파일·import·런타임 적용하지 않았다.
- **CPU 반례 때문에 후보 미채택:** `replay_phase25.py::FaceWithOneOriginalAlpha/main`, `PHASE25_CPU.json`은 기존 실제 phase0/.125의 서로 다른 sourceId를 각자 current evaluated geometry/native alpha/carrier와 대응했다. 기존 FaceRay 초기화·Face114 query·NativeAlpha·compose를 재사용했고, 해당 프레임의 이전 실제 GPU 가림 query32개와 최종RGBA2개를 먼저 exact 재현했다. 수정 좌표의 깊이/alpha와 hair address32쌍도 exact다. 하지만 old hair coverage12→0이 공통4×좌표 CPU 반사실에서는4→8로 바뀌어 여전히8표본 경계에서 최종 눈/머리 소유권이 전환된다. 실제 GPU 새 결과가 아니며 개선/시간 안정화로 집계하지 않는다. 문서 예제의 hair texel 인덱스 동일은 프레임 간 S4 texel 내용 동일을 보장하지 않는다.
- **다음 실제 원인 단계:** 소비자에 hairShift만 붙이는 것으로 끝낼 수 없다. S4 머리 raster 생산자(`EyeFeature348.samples[4]` 공급)까지 공통 head-local 연속 footprint로 정렬하거나 그 footprint의 실제 geometry/alpha 가시성을 생산해야 한다. `Forward113`은 현재 이 physical4× S4를 그대로 연결한다. 이는 추가 캡처 부재/외부 미술 숫자 선택 문제가 아니라 미완인 생산자·소비자 연결이다. 새 GPU 평가기나115 재실행으로 대체하지 않는다. §1-B 공수송/원본 가시성 gate는 독립적으로 검증·구현할 남은 부분이며 현재 Close75 복구 성공이라고 하지 않는다.
- 보존: HEAD87a5475c 기반 사용자 tracked30파일 byte hash 모두 동일(`RESUME_STATUS.json`), 제품77/입력 설정·현재 씬/옵션·원본 문서를 수정하지 않았다. 위험 EvaluateForm115/driver·TDR/보안 변경·kill/reset/cache삭제/CUA/push0. 현재 기술적 판정은 소비자-only 좌표 후보 실패이며 서버 승인 거절/불명 실행이 blocker인 상태가 아니다. 공식 읽기 요청은 reply/EOF를 남겼다. 스크립트는 원래 작업폴더의 기존 frozen 입력을 읽으며 신규 GPU 캡처를 만들지 않는다. 커밋 색인: `git log -- experiments/pixel-pipeline/2026-11-11-resume-argon25`.
