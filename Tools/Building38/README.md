# N16 실행 진입점

설계·현재 결과·실패 귀속의 단일 원본은 [BUILDING16.md](../PerfectPixelUniform/BUILDING16.md)입니다. 입력은 B37 raw sheet/physical contract와 N15 재료 reference이며, 알려진 부품 기하에서 native pixel을 직접 제작합니다. 가짜 픽셀 원화의 격자를 복원하는 도구와 구분합니다.

현재 결과는 `docs/artifacts/building38/run04`, 공유 Unity 자료는 `Assets/Art/NativeBuilding38`, 적용 대상은 `GameMap1/PlannedPixelShop33`입니다. 기존 결과 사용에는 재생성이 필요하지 않습니다.

새 제작이 승인된 경우 프로젝트 루트에서 NumPy/Pillow가 있는 Python으로 실행합니다.

```powershell
& 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B Tools/Building38/run16.py --output docs/artifacts/building38/새실행폴더
```

실행기는 source/code hash를 고정하고 geometry/materials/export/validate를 연속 실행합니다. 그 뒤 Unity 작업은 활성 Codex에게 넘어갑니다. Codex가 실제 Unity MCP로 `NativeBuilding16Importer.Import`, 최소 GPU 관측, gate submit, `Apply`, 실제 게임 관측을 수행합니다. 사용자 질문이나 사용자 실행기 조작 요청이 아닙니다. native와 preview 파일은 구분하며 PNG 확대/축소를 생산 단계로 쓰지 않습니다.

기존 출력·공유 자산을 다른 source로 덮어쓰지 않습니다. source 변경은 새 자산 버전/기존 GUID·참조 보존 계약이 필요합니다. 원본 prefab 전체 전파는 현재 허용되지 않으며 기지의 한 테스트 인스턴스 override로 저장합니다.

`geometry16.py`: 18종 semantic solids와 구조 boxes, surface hit/normal/edge/closed caster.
`building16.py`: 관측 재료·무늬·표면 annotation, native data export와 invariant.
`run16.py`: 기존 WorkLoop의8단계 연결.
`unity_gate16.py`: 실제 GPU capture/Play 관측을 읽는 마지막 gate.
