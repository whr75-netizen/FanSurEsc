# 눈 실험50~53 보관 — 2026-10-31

이 보관본은 기존 commit `d0ca21f4ac87e82151357253582f9ce079596a2d`의49 이후 실험50~53을 기록합니다. **제품 미적용·GPU 테스트 미실행·미술 미채택** 상태입니다. Unity 실행, asset import, 화면 조작, 초기화, GC, 앱 종료, 원격 push를 수행하지 않았습니다. 이번 보관 검사는 현재 Unity scene/dirty/메모리 정상 상태를 확인한 검사가 아닙니다.

## 저장 입력 재현

저장소 루트에서 실행합니다. Python3+NumPy가 필요하고 Pillow·Unity·네트워크·원본 VRM은 재생에 필요하지 않습니다.

```powershell
python -B experiments/pixel-pipeline/2026-10-31-eye-experiments50-53/replay.py
python -B experiments/pixel-pipeline/2026-10-31-eye-experiments50-53/verify_snapshot.py
```

일반 Python에 NumPy가 없으면 이미 설치된 Blender bundled Python을 사용할 수 있습니다. Blender 앱을 실행하는 명령이 아닙니다.

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe' -B experiments/pixel-pipeline/2026-10-31-eye-experiments50-53/replay.py
```

49와 이전 pngio의 이미 버전 관리된 파일을 `DEPENDENCIES.json`의 저장소 상대 경로·해시로 연결했습니다. 49의 입력을 중복 복사하지 않습니다. 이 폴더 단독이 아니라 해당 선행 커밋을 포함하는 저장소로 재현합니다. 외부 제품/원본 asset 접근과 파일 쓰기는 audit hook으로 차단합니다. 함수·클래스만 읽어 원래 CLI의 절대 경로와 top-level 작업을 실행하지 않습니다.

재생 범위는50의 source-only 상안검 결정/합성,51의 등록 aperture와 미등록 state 거절,52의 전체 keyform 공통 이동/명시 충돌,53의125개 공동 할당/원래 source 가림/부분 RGBA입니다.53의 기존 rectangle API는 NumPy 배열로 같은2×2 solid fill을 실행해 원본 PNG의 전체 RGBA와 비교합니다. 새 이미지나 완전한 얼굴을 추정해서 만들지 않습니다. 원래 전체 source extraction·GPU shader 컴파일·프로덕션 통합을 재생한 검사가 아닙니다. 원래 보고서의 assertion 수는 당시 기록이며 이번 검사 수와 구분합니다.

## 실험별 판정

| 실험 | 보관한 결과 | 미완·기각 |
|---|---|---|
|50|cached iris에 의해 native line이 재순위되는 feedback을 source-only 결정으로 분리|흰자 손실은 별도 S0/aperture 문제. S0 전체 bypass는 기각. compute 후보 미import·GPU 미검증|
|51|기존 contour, carrier UV/팔레트, 연속 aperture control과 native morph의 출처를 구분|continuous control은 안검 hard mask가 아님. closed50/100 geometry가 있어도 pixel keyform 승인/완성 아님. source 재추출은 제외|
|52|부모·홍채·안검 경계와 source provenance를 묶은 keyform/cache 및 명시적 충돌|고정 opaque 두 glyph의 `(222,52)` 충돌을 단순 순서로 모두 보존할 수 없음. 미채택이며 전체 눈 해결 아님|
|53|동일 frame100/101의 세 파츠를 동시에125조합 검사.0예산 feasible0,1셀 예산 feasible2(B/C)|B/C의 눈 높이가1셀 낮아지는 대가. 두 프레임을 함께 쓴 제한된 오프라인 후보이며 인과적인 runtime/시간 안정성 검증 아님|

53의 source-growth 가림 검사를 생략한 A는 기각했습니다. 이전 overlay의 잔상 버전은 `archive/joint-eye53/source-gate-ghost-draft`에 원본 코드만 보존하며 유효 결과로 취급하지 않습니다. `logical-gate-only`도 source fragment 검사를 빠뜨린 이전 비교안입니다. 현재 코드는 원래 가려진 source를 되살리지 않고 더 앞쪽 hair/brow/body를 보존합니다.

**완전 합성의 입력 공백: clean Base/Backing6표본**

- frame100: `(223,52)`, `(225,52)`
- frame101: `(223,52)`, `(224,52)`, `(225,52)`, `(225,53)`

현재 candidate B/C의 magenta는 그 배경이 UNKNOWN이라는 표시입니다. 이미 눈이 포함된 `final-native/head-colour/eye-output`이나 이웃 피부색으로 대체하지 않습니다. isolated PNG는 파츠만 보여줍니다. 부모/사용자가 새 GPU 입력을 허용하기 전 추가 Unity 테스트를 하지 않습니다. 대각 형상·실제 시간 가림·회전/blink·미술·GPU 회귀 및 제품 연결은 미완입니다.

## 파일·보존 경계

`archive/`는 원본 코드·작은 계약·보고·선택한 이미지를 바이트 그대로 복사했습니다. `SOURCE_MANIFEST.json`에 원본 위치/크기/SHA256, `EXTERNAL_INPUTS.json`에 제외한 큰 표·원본 mesh 재구성 입력·전체 출력의 위치/크기/해시가 있습니다. 원본 VRM·프로젝트 asset·무관한 미추적 파일은 복제하지 않았습니다. source shader/compute와 invalid draft도 runtime 폴더 밖의 참고 코드이며 Unity에서 import/컴파일하지 않습니다.

`PACKAGE_MANIFEST.json`과 `verify_snapshot.py`로 파일 무결성·크기·자격정보 패턴·로컬 모듈/선행 의존성을 검사합니다. 탐지0은 모든 비밀의 부재를 증명하는 보안 감사가 아닙니다. 역사적 원문에는 당시 경로와 "commit0" 같은 작성 시점 상태가 남습니다. 현재 보관/커밋 상태는 이 문서와 Git 이력을 따릅니다. 원본 공백과 EOF 보존을 위해 archive만 공백 검사 예외로 두고 새 코드·문서는 검사합니다. 모든 파일의 Git blob은 manifest와 같은 바이트로 보존합니다.

이 스냅샷은 기존 사용자 수정30개·무관한 미추적2,158개를 섞지 않습니다. 현재 메모리/재부팅 문제의 해결 기록으로 해석하지 않습니다. source sequence는 `counts47-087454994917423fa13c5fe72eceb7f4`이며 프레임 번호만 같은 다른 캡처와 혼용하지 않습니다.
