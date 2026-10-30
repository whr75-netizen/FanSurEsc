# 픽셀 진단 코드 보관본 — 2026-10-30

이 폴더는 완료한 오프라인 실험의 고정 스냅샷입니다. **Unity 제품에 통합하지 않았습니다.** `Assets`와 `Packages` 밖에 있으며 실행·컴파일·에셋 가져오기에 등록하지 않습니다. 원본 실험은 이동하거나 삭제하지 않았습니다. 진행 중 `continuous46`은 포함하지 않습니다.

## 바로 재현할 범위

Node.js 22 이상, Python 3와 NumPy가 필요합니다. 이 두 진입점은 폴더 위치와 무관하게 보관된 코드·fixture만 읽습니다. Unity, 네트워크, 원본 VRM, 전체 GPU 버퍼, Pillow와 브라우저가 필요하지 않습니다. 저장소 파일에 결과를 덮어쓰지 않고 JSON을 표준 출력으로 반환합니다.

```powershell
node experiments/pixel-pipeline/2026-10-30-source-diagnostics/replay.cjs
python -B experiments/pixel-pipeline/2026-10-30-source-diagnostics/replay.py
python -B experiments/pixel-pipeline/2026-10-30-source-diagnostics/verify_snapshot.py
```

일반 Python에 NumPy가 없다면 이미 설치된 Blender의 Python을 사용할 수 있습니다. 이 검증에서는 Blender 앱을 실행하지 않습니다.

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe' -B experiments/pixel-pipeline/2026-10-30-source-diagnostics/replay.py
```

`replay.cjs`는 원래 팔레트 제약 solver와 단색 `run.cjs`를 읽기 전용 가상 파일 시스템에서 실행해 출력 계약과 8분기의 전체 RGBA를 비교합니다. Node71검사입니다. `replay.py`는 원본 코드의 함수·클래스 AST만 불러와 경로 상수, CLI main, 원래 파일 쓰기를 실행하지 않습니다. NumPy 재생은 눈의 5×4,225위상, 셀935 선택, 102개 경계의 9개 공유 경로 fit/raster를 포함합니다. 재배치 후 검사 결과는 `VALIDATION.json`에 고정합니다. 검사 통과가 미술 완성이나 연속 동작 성공은 아닙니다.

## 무엇을 보관했는가

- `archive/exp30`: palette-v3, palette-v4-feature, flat-albedo-control의 알고리즘·빌더·원 검사, 작은 계약·보고서와 필요한 보조 모듈입니다. `archive/exp27`: eye-cache42/joint-placement43, flat-shade-boundary44/selection935와 공통 curve/geometry 코드를 보관합니다.
- `SOURCE_MANIFEST.json`은 원래 위치의 약칭·상대 경로, 복사 전 SHA256·바이트 수와 복사/추출 방식을 기록합니다. `archive`와 `evidence`는 원본과 바이트가 같습니다. `fixtures`는 명시된 원본에서 필요한 숫자만 추출했으며 별도 원본인 척하지 않습니다.
- 단색 입력309KB, 눈의 다섯 포즈 source packet 약50KB, 경계102쌍과9개 fit의 guide/control point, 셀935에 걸친 삼각형28개/후보7개가 핵심 fixture입니다. 전체 메시·텍스처·VRM을 포함하지 않습니다. 대표 PNG12개는 결과 확인용 작은 파생 이미지이며 원본 에셋 배포본이 아닙니다.
- `PACKAGE_MANIFEST.json`은 보관 파일 전체의 SHA256·크기를 기록합니다. `verify_snapshot.py`는 무결성, 원본 복사 해시, 의존 모듈 포함, 파일 크기와 자격정보 패턴을 확인합니다. 자격정보 패턴 검사는 모든 비밀의 부재를 증명하는 전문 보안 감사가 아닙니다.

원래 `archive` CLI에는 역사적 절대 경로와 출력/공개 동작이 남아 있습니다. 그대로 실행하는 진입점은 아닙니다. 바이트 보존을 위해 과거 경로를 고쳐 쓰지 않았으며, 새 재생 진입점은 외부 입력 접근을 차단합니다. 원래 browser 검사 코드는 보관만 했습니다. Desktop 공개/복사 스크립트는 보관 대상에서 제외했습니다.

## 성공 범위와 기각·미해결

| 실험 | 확인한 범위 | 한계/판정 |
|---|---|---|
| palette-v3 | 두 bank 매핑이 증폭한 색 점프를 줄임 | source 대비9쌍 일부 손실. 추가 경계113개는 v2 대비 추가 수이며 전체 경계 수 아님. 채택 아님 |
| palette-v4-feature | 원본 대비 제약을 16/32/64색 후보에 적용. 64색에서 검사한8쌍 대비 보존 | 출력 known358셀51색, 단독184개. 원색 통과 unknown10 문제를 남긴 비교안. 예산/미술안 승인 아님 |
| flat-albedo-control | 같은 geometry/g/Q/P에서 albedo만 단색화. 전체 mask override와 중복 Q색을 별도 분리 | 같은 legacy P: 원본51색/단색2색. distinct 진단 P: 원본51색/단색3색. 무조명 단색1색. 단색에서도 Q 4연결11성분/단독6셀. 텍스처만 원인이라고 결론낼 수 없음 |
| eye-cache42 | source feature identity/cache binding 및 area allocator 반례 | 같은 ID만으로 형태 보존 안 됨. source UV adapter 완성·제품 눈 수정 아님 |
| joint-placement43 | 같은 reference의20셀을 공동 이동하면 21,125개 위상에서 상대 배치·literal RGBA 유지 | 과거5포즈 입력을 쓴 이동 실험. 포즈별 디자인/blink/가림/실제 연속 GPU 동작 미검증 |
| flat-shade-boundary44 | 원래 g/Q 보존과 별도 Qprime 경로, 4셀 수정 기록·fit/raster 재생 | 최종 후보도 단독6개 유지. thin-connection 손실 후보는 기각 기록 보존. 새로운 전체 곡선 해법이나 제품 채택 아님 |
| selection935 | 고정 셀의 표면 선택을 8/16/32/64 적분 및9 offset에서 재생 | 같은 셀의 서로 다른 표면 대표 선택 비교. 실제 시간상의 Q3→Q2 변화 재현이 아님 |

sourceId는 `95d042f14adf8e99685f26838beeb00ab57773e445e5997d16a9c61d0f1e2c3f`, geometry packet SHA256은 `76fc49b722854b71f9112462b4a4753b1c59549eb700ab84b887f5257d2bf9cc`입니다. 구 sourceId와 혼용하지 않습니다. 단색 `(94,64,63)`은 실제 native texel medoid 시험값이며 제품 하드코딩이 아닙니다. 팔레트 간격 배율과 Q 라벨은 서로 독립입니다.

## 완전 독립 재현과 외부 의존성의 구분

위 **bounded 재생 검사는 이 보관본만으로 재현**합니다. 외부 파일 차단은 Node 가상 FS와 Python audit hook으로 확인합니다. 다만 모든 원본 프레임을 재추출하거나 팔레트 native texel fit을 처음부터 다시 계산하는 전체 파이프라인은 독립 재현이 아닙니다. `EXTERNAL_INPUTS.json`에 원본 위치 약칭·SHA256·크기·필요 단계를 적었습니다. 원본 VRM, 전체 GPU/raw buffer와 평가 메시, native 이미지, 현재 Unity dirty 소스와 미저장 Editor 상태를 재배포하거나 복제하지 않았습니다.

보존한 셀935 geometry fixture는 완전한 모델을 대신하지 않고, 해당 셀의 적분에 필요한 projected triangle/depth/chart만 포함합니다. boundary 재생은 저장된 visibility witness에서 guide/fit/raster를 다시 계산하고, 원본 전체 메시의 visibility를 다시 계산하지 않습니다. 눈 source packet도 저장 버퍼에서 이미 추출한 S1/S2/S3이며 실제 GPU를 다시 읽지 않습니다. `tools/prepare_snapshot.py`는 원본 외부 입력이 있을 때 fixture를 어떤 규칙으로 추출했는지 기록한 준비 도구입니다.

원래 제품 실행 기준은 `a976f69` 이후 미커밋 수정30개가 있는 상태입니다. 문서 커밋6094e02 및 이 보관 커밋을 제품 코드 적용 버전으로 부르지 않습니다. Unity Save/Play/Exit/Reimport, 사용자 변경 stage, cache 삭제·브라우저 종료·원격 push는 수행하지 않았습니다. 제품 통합과 시간적 연속성, 남은 Q 분단의 원인 수정은 별도 미완 작업입니다.
