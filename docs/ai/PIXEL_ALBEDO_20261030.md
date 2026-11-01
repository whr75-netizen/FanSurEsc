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
