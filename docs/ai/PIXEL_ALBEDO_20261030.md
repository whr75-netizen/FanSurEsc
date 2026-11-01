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
