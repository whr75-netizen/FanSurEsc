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
