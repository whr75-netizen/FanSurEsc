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
