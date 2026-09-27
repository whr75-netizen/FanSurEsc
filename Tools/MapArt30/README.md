# 첫 2D 상가 아트 실험

입력은 `design.json`과 `prompt.txt`, 설계 계약은 `docs/references/grave_seasons_map_art.md`다. `run.py prepare`는 기하 안내 도면만 만든다. 게임 아트는 내장 imagegen이 제작하고 `normalize`는 기존 수정 PerfectPixel을 호출한다. 도면을 아트로 제출하거나 전체 생성/후처리를 AI 자기 판단 루프로 반복하지 않는다.

현재 결과: `docs/artifacts/map-art30/index.html`. 원본1254×1254 / 정규화384×384 / 표시3배1152×1152. 색상 재분류 없음. 공간 아트·비율의 사용자 판단은 대기 중이다. 개별 자산 분리/Unity 통합은 미실행이다.

현재 WorkLoop 상태: `LocalOnly/WorkLoop/map-art30-v1/validation-state.json`, review ticket `2e915764ec61483f8e44a44d7d2136cc`. 기존 `state.json`은 보존한다. 최초 그래프의 prepare/normalize가 같은 `art:map30` 자원을 쓰면서 선행 관측을 무효화해 `unknown_guard`로 멈췄다. 실제 normalize exit_code=0을 확인하고, 생성/변환을 반복하지 않는 별도 관측 그래프로 인계했다. 수정된 `graph.json`은 plan/generated/normalized 자원을 분리한다. 수정 그래프 전체 재실행은 하지 않았다.

일반 CLI(기존 폴더에는 재실행하지 않음):

```text
python -B run.py prepare NEW_OUTPUT_DIRECTORY
python -B run.py normalize SAME_OUTPUT_DIRECTORY    # stdin: {"source":"실제 생성 경로"}
python -B run.py validate SAME_OUTPUT_DIRECTORY
```

WorkLoop의 전체 `graph.json`은 이번 로컬 경로와 run01로 고정되어 있다. 새 제작은 새 출력/상태 경로와 변경 원인을 명시한 별도 그래프로 시작한다. 기존 결과에 다시 init/run해서 생성량을 소비하지 않는다. 정규화는 `LocalOnly/PerfectPixelPalette_20260906/trigger_cli.py`가 필요한 로컬 의존성이다. 없는 환경에 원본 PerfectPixel이나 3색 목재 경로를 몰래 대체하지 않는다.

최종 확인: 두 층 Rect 포함/겹침/면적, 출력 크기·alpha·원본 해시. 이것으로 실제 이동, 생성물의 기하 정합성 또는 미술 품질을 합격 처리하지 않는다.
