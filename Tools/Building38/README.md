# N17~N24 실행 진입점

설계·현재 결과·실패 귀속의 단일 원본은 [BUILDING16.md](../PerfectPixelUniform/BUILDING16.md)입니다. 입력은 B37 raw sheet/physical contract와 N15 재료 reference이며, 알려진 부품 기하에서 native pixel을 직접 제작합니다. 가짜 픽셀 원화의 격자를 복원하는 도구와 구분합니다.

현재 geometry/cache는 `docs/artifacts/building39/run02`의 사물35종과 `floor-fix01`의 활성 바닥입니다. 공유 Unity 자료는 `NativeBuilding39`/`NativeBuilding39Floor40`, 적용 대상은 `GameMap1/PlannedPixelShop33`입니다. 공통90.5097PPU·정수표시·21시 기본밤·좌우빛은 N17, 읽기용 밤 명암은 N18이며, 네 수납장 금장/목재UV는 N19의 `NativeBuilding41MaterialRepair` 재질 map만 참조합니다. N20은 기본 카메라를 정수2배로 표시합니다. N24는 같은 moving light의 반경5m·intensity.4와 무광 구간이 있는 ramp로 세 백색 유광 단계를 표시합니다. 범위·밝기·단계는 별개이며 다른 광원·아트·camera/PPU·motion은 유지합니다. 현재 결정/관측은 BUILDING16.md에 기록합니다. 최신 실제 화면은 `docs/artifacts/building39/light24/moving-on.png`입니다. 기존 결과 사용에는 재생성이 필요하지 않습니다.

새 제작이 승인된 경우 프로젝트 루트에서 NumPy/Pillow가 있는 Python으로 실행합니다.

```powershell
& 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B Tools/Building38/run16.py --output docs/artifacts/building39/새실행폴더
```

실행기는 source/code hash를 고정하고 geometry/materials/export/validate를 연속 실행합니다. 그 뒤 Unity 작업은 활성 Codex에게 넘어갑니다. Codex가 실제 Unity MCP로 `NativeBuilding16Importer.Import`, 최소 GPU 관측, gate submit, `Apply`, 실제 게임 관측을 수행합니다. 사용자 질문이나 사용자 실행기 조작 요청이 아닙니다. native와 preview 파일은 구분하며 PNG 확대/축소를 생산 단계로 쓰지 않습니다.

기존 출력·공유 자산을 다른 source로 덮어쓰지 않습니다. source 변경은 새 자산 버전/기존 GUID·참조 보존 계약이 필요합니다. 원본 prefab 전체 전파는 현재 허용되지 않으며 기지의 한 테스트 인스턴스 override로 저장합니다.

`geometry16.py`: 18종 semantic solids와 구조 boxes, surface hit/normal/edge/closed caster.
`building16.py`: 관측 재료·무늬·표면 annotation, native data export와 invariant.
`run16.py`: 기존 WorkLoop의8단계 연결.
`shade17.py`/`shading17.json`/`NativeShade17.hlsl`: 관측색과 동일 중립 CPU/GPU 규약.
`floor17.py`: 실제 활성 Aligned 바닥의 worldUV를 유지한 공통 격자 제작.
`unity_gate17.py`: 실제 GPU capture/Play 관측을 읽는 마지막 gate.
`floor_repair17.py`: 잘못된 활성 대상의 바닥만 새 버전으로 수선한 실행 이력.
`final_check17.py`: float32 검증 하한 결함의 명시 재개방; 생산 재실행0.

`repair19.py`/`NativeCabinet19Repair`: 실제 serialized metadata의 금장/woodUV 분기를 복구하며 기존 기하를 재사용합니다. 낮은 PPU 표본은 동일 물리 형태의 직접 제작 비교용이며 전체 건물에는 적용하지 않았습니다. 임시 float row 수선의 명시 재개는 `reopen_comparison`이며 기존 계산과 Play 관측을 재사용합니다. `compare19.py`는 현재 제작 원본·고정 밤광·실제 게임의 native crop을 무변형으로 나란히 저장합니다.

`night18.py`/`NativeReadable18.hlsl`/`NativeNight18Observation`: 기존cache/PPU/기하를그대로사용하는색계산3단계. `night18.py start --output <새폴더>`로CPU색→활성Codex의실제GPU/Play관측→최종gate를연결합니다. 이실험에서캐릭터조명·원화디자인·전체픽셀grid를변경하지않습니다.

`light24_gate.py`/`NativeLight23Observation`: 실제 Play GPU의 0+세 백색 유광 단계, 최종 RGB 기여, 이전 대비 작은 범위, 두 바닥 영역의 2×2 격자, 원본193파일·다른 광원·같은 Player/Camera/기하·Edit 저장을 확인합니다. 계약은 `light24/request.json`/`state.json`입니다. 영역 검사만으로 전체 화면이나 미술 합격을 주장하지 않습니다. N23의 `light23_gate.py`/`request-final.json`/`state-final.json`은 세 단계 계산의 과거 증거이며, 과도한 범위·밝기 피드백으로 N24에서 재개했습니다. N22/N21도 과거 관측으로 보존하며 원본/팔레트를 다시 생성하지 않습니다.
