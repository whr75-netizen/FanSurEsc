# 눈 후보49 인계 — 실험 적용과 제품 통합 구분

기준 로컬 커밋1835f10 및6c31438 이후의 독립 후속입니다. [비교 페이지](INDEX.html), [셀별 결과](RESULTS.json), [원인·검증·실패 보고](REPORT_KO.md), [GPU 통합 계획](INTEGRATION_PLAN_KO.md)을 함께 읽습니다.

`python -B verify49.py`로 동결된47 source packet과Template216 셀을 재생합니다. 기존 Python+NumPy+Pillow가 필요하며 새 설치·Unity·네트워크·원본VRM·제품 소스 접근은 필요하지 않습니다. `fixtures`와`lib`만 입력으로 사용합니다. 검증 결과와 PNG를 이 실험 폴더에 다시 씁니다. 제품 코드/씬/기본 설정을 바꾸지 않습니다.

- **실험 완료:** 가림 gate47 재현, reference-cell 공동 배치49, 같은 source의 조합 회귀 검사, 분리RGBA/원래크기/nearest 확대 출력.
- **명확한 실패:** full20-cell 참고 템플릿은 현재 native sclera/안검과 맞지 않으며 frame101의NativeLine 선택을 간접 변경합니다. full49는 미채택입니다.
- **제한 후보:** gate47은 frame100의 가려진 iris 선택만 바꿉니다. frame101 대각 눈을 고친 결과가 아닙니다. GPU 컴파일/실제 후보 합성 전에는 제품 반영하지 않습니다.
- **제품 통합0:** 추가 Unity 호출·Play·캡처·GC·프로젝트 저장·Desktop 복사0. 원본30개 미커밋 변경과dirty25는 덮어쓰지 않았습니다. dirty25는 이전 확정 상태이며 이번에 Unity에서 새로 조회하지 않았습니다.

원본Template의각눈4개iris셀은실제기존자산에서추출한값입니다. 모든눈을4픽셀로고정한알고리즘이아닙니다. 현재6개미세보행pose의단일open형태차용시험이며모든pose/회전/blink승인또는시간안정화완료가아닙니다. 실제앞쪽hair가가린셀은보충하지않습니다.

`prepare_fixture.py`/`finish49.py`는 원본 작업폴더에서 수행한 준비 도구입니다. 재생하려고 다시 실행할 필요가 없습니다. `INPUT_MANIFEST.json`은 출처·SHA256을, `PACKAGE_MANIFEST.json`은 보관본 무결성을 기록합니다. `lib`와`patches`의 역사적 경로/공백은 원본 바이트를 보존합니다. 그 source의 CLI main/import를 직접 실행하지 않고 함수 AST만 읽습니다.
