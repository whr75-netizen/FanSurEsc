# B32 — 제작 전 도면과 표시 결함 실험

현재 결정·미술 명세·근거·재개점은 [통합 연구 B32](../../docs/references/grave_seasons_map_art.md)가 소유합니다. 이 도구는 **새 상점 미술 생성기나 게임 통합기가 아닙니다.** 기존 B31 아트/배치는 사용자 거절 상태입니다.

## 산출물과 실행

- `docs/artifacts/building32/layout-plan.json`: 10×8m, 시설5개/사용점6개인 미적용 도면 후보의 단일 원본.
- `compile_layout.py`: JSON→SVG/관측. 사각 점유·사용공간·벽 부착·문폭, 반경0.5m+제안여유0.1m+0.1m grid 반대각선 팽창, 4방향 BFS. 원본 자동수정 없음, 실패 exit2.
- `native-surface-probe.cs`: Unity_RunCommand용. 기존 floor PNG/재질·임시 preview scene·같은30°/45°·정수4배로 diamond/FullRect coverage 비교. 기지 촬영이나 PNG 편집이 아님.
- `validate_evidence.py`: 단일 바닥 alpha와 도면 기하만 판정. 캐릭터 가림·타일 연결·디자인·광원 반응·실제 이동은 판정하지 않음.
- `graph.json`: 기존 WorkLoop의 `layout command → probe ai.work → evidence command`. complete는 제한된 실험 완료이며 건물 제작 완료가 아님.

```powershell
python -X utf8 -B Tools/Building32/compile_layout.py --plan docs/artifacts/building32/layout-plan.json --svg docs/artifacts/building32/layout-plan.svg --report docs/artifacts/building32/layout-report.json
```

전체 실험은 `Tools/WorkLoop/work_loop.py init <새 state.json> Tools/Building32/graph.json` 이후 run합니다. probe 인계에서 Codex가 C#을 Unity_RunCommand로 실행하고 실제 report 경로를 반환합니다. 같은 입력/검사를 반복하지 않으며 새로운 의문/입력이 있을 때만 재실험합니다.

## 2026-09-27 실제 관측

- 도면: 겹침/사용공간/부착/문폭 위반0, 사용점6/6 연결. Unity 적용/실제 Player 이동 미실행.
- GPU: expected18,368 screen pixels. diamond actual16,384/missing1,984/extra0. FullRect actual18,368/missing0/extra0. 원본64×32의 정수4배. 색/스타일 합격 판정 아님.
- SceneView30°/350°/orthographic 적용. 메뉴만 수정하고 실제 게임 카메라/에셋은 보존.
- preview 생성이 편집 dirty flag를 세웠으나 저장 사본이 기존 씬과 byte-identical함을 확인한 뒤 동일 내용을 저장해 clean 복귀. 씬git diff0. 최종 코드에 이 청소 확인을 합쳤으며 기하 실험은 반복하지 않음.
- MCP 동적 namespace의 Mesh 이름 충돌은 UnityEngine.Mesh 한정으로 해결. 초기 compile 실패는 렌더 결과가 아니며 두 case는 각각1회 관측. 신규 Console 오류0, 기존 relay오류1 보존.
- 증거는 `docs/artifacts/building32/experiment-result.json`, coverage PNG/TXT, layout SVG/JSON, sceneview TXT.

## 미해결

FullRect tile overhang 연결/깊이, 전체 표시 정수배율·공통phase, 새 개별 자산·광원 계획은 미통합입니다. 도면의 수치/역할은 제안이며 사용자 확정이나 미술 승인으로 승격하지 않습니다.
