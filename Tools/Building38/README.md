# N17~N30 실행 진입점

N30은 N29의 큰 도장 얼룩을 폐기하고 원인별 결·접촉·흠집·하단 마모·노출목재·금속 변색을 계산합니다. `run_material30.py`의 features→surface→Unity 관측→GPU gate→저장→최종 gate를 사용하며 이미 계산된 map은 `--reuse-maps`로 검증 후 재사용합니다. 현재 final state는 `LocalOnly/WorkLoop/material30-integration03`, 실제 화면은 `docs/artifacts/building39/material30/run01/comparison.png`입니다. Unity 진입점은 `NativeMaterial30Observation.Prepare/Observe/BindAndSave`이며 기존 버전에는 Prepare를 반복하지 않습니다. 실패 관측은 원래 위치에 남고 현재 관측은 `observation02`입니다. 새16열 palette에서만 normal.w 거칠기와 실제광원 spec를 사용합니다. 원래4열의 실제GPU 두 경로는 byte차0, 생산 이미지는 resize0입니다. 높이/법선은 caster 변형이 아니며 미술·성능 합격은 자동 선언하지 않습니다.

설계·현재 결과·실패 귀속의 단일 원본은 [BUILDING16.md](../PerfectPixelUniform/BUILDING16.md)입니다. 입력은 B37 raw sheet/physical contract와 N15 재료 reference이며, 알려진 부품 기하에서 native pixel을 직접 제작합니다. 가짜 픽셀 원화의 격자를 복원하는 도구와 구분합니다.

N29 재료 계산은 `material29.py generate --output <새경로>`이며 현재 입력은 기존 empty_counter의 canonical chart/normal과 N19 material map입니다. 화면 RGB를 축소하지 않고 G에 색 군집, 별도 float normal map에 손잡이의 곡면 법선을 계산합니다. `run_material29.py`는 계산→Unity writer→관측 gate를 묶고 기존 출력/상태를 덮어쓰지 않습니다. `--reuse-maps --integration-version N`은 명시된 원인 수정 후 같은 map byte를 검증해 통합만 재개합니다. 최초 두 상태는 LocalOnly에 보존됐고 최종은 material29-integration03입니다. Unity 진입점은 `NativeMaterial29Observation.Prepare/Observe/BindAndSave`, 실제GPU 검사는 `material29_finish.py`, 현재 결과는 `material29/run01/comparison.png`입니다. 기존 버전을 재사용할 때 Prepare를 반복하지 않습니다. 이번 Editor writer의 asset version은 NativeMaterial29로 고정되어 있으며 다른 물체/버전 통합은 별도 계약으로 정합니다.

N28은 현재39 원형 caster를 그대로 재사용합니다. `NativeSurfaceGridAlignment`가 카메라별 원래 grid phase를 world δ로 계산하고, native card/cache·원형 shadow vertex·render bounds가 같은 이동을 한 번 소비합니다. 물리/mesh/원화/PPU/색은 변경하지 않습니다. `NativeShadow28Observation.FixtureCapture`는 네 실제 GPU world-position 경우, `AlignmentCapture`는 실제44pair를 관측합니다. 최종 판정은 `shadow28_gate.py`, 고정 그래프는 `shadow28/request-final.json`/`state-final.json`, 최종 실제 화면은 `shadow28/final-frame/both-on.png`입니다. 원본 재료에 자동 저장된 새 기본값의 실패와 Editor 복원 이력도 보존했습니다. centre sampling과 연속 mesh의 외곽 부분 coverage를 픽셀 단위로 완전히 같다고 판정하지 않습니다.

현재N27은청색target보간/채널별반올림/흰RGB덧칠을제거하고 `albedo×(baseResponse+steppedIrradiance)`를사용합니다. 기존야간노출/이동광세단계/URP직광shadow/2px/원본은유지합니다. 일반world fullscreen은기존색증폭근사이며native/character의재료반응과구분합니다. `NativeLight27Observation.FixtureCapture`는96case의실제linear GPU값을저장하고 `light27_gate.py --fixture-only`가통합전판정합니다. 실제Play는기존N26관측기를재사용하고전체gate는 `light27_gate.py`입니다. 현재고정그래프 `light27/request.json`/`state.json`은3노드완료됐으며 최종그림은 `light27/play/both-on.png`, 이전그림은 `light27/before/both-on.png`입니다. N18CPU색실험을새표면의reference로재사용하지않습니다.

N26은 움직이는 Local 테스트 구체와 두 RoomLamp 전등을 분리합니다. 전등 owner는 같은 anchor의 Unity Point Light 직광/Hard shadow와 room box union 안의 diffuse indirect를 함께 켜고 끕니다. 원화·map·mesh·PPU·배치는 재생성하지 않습니다. Unity 메뉴 `Tools/Fantasy Survival/Room lighting`에서 건물 전등과 이동 구체를 각각 on/off할 수 있으며 runtime entry는 `SteppedLocalLight.SetLightingEnabled`입니다. `NativeRoom26Observation.Configure`는 기존 활성 벽등2개만 binding하고, `Capture`는 실제 Play에서 독립 on/off와 shadow를 관측/복원합니다. `SaveFinal`은 원본보존/pairedLight 조건을 확인해 한 씬만 저장합니다. `room26_gate.py`는 실제PNG·먼방표본·2pxROI·512파일hash를 판정합니다. 기존관측재사용 final graph는 `room26/request-final.json`/`state-final.json`이고 현재 화면은 `room26/play/lamps-only.png`입니다. 실제 간접반사를 추적하는 GI나 물리 스위치 모델은 아닙니다.

현재 geometry/cache는 `docs/artifacts/building39/run02`의 사물35종과 `floor-fix01`의 활성 바닥입니다. 공유 Unity 자료는 `NativeBuilding39`/`NativeBuilding39Floor40`, 적용 대상은 `GameMap1/PlannedPixelShop33`입니다. 공통90.5097PPU·정수표시·21시 기본밤·좌우빛은 N17, 읽기용 밤 명암은 N18이며, 네 수납장 금장/목재UV는 N19의 `NativeBuilding41MaterialRepair` 재질 map만 참조합니다. N20은 기본 카메라를 정수2배로 표시합니다. N24의 moving light는 반경5m·intensity.4와 무광 구간이 있는 ramp로 세 백색 유광 단계를 표시하며 N25에서도 유지합니다. 현재 결정/관측은 BUILDING16.md에 기록합니다. 기존 결과 사용에는 재생성이 필요하지 않습니다.

N25의 현재 색은 두 활성 벽등을 white로 맞추고, `NativePaletteSurface16._NativeEdgeSRGBScale=.8`로 강한 선만 최종 재료색보다 sRGB20%짙게 표시합니다. source/PPU/geometry는 그대로이며 캐릭터 선은 별도입니다. 최신 게임 화면은 `style25/after/moving-on.png`, 같은 재료 파라미터의 0/.8/1 비교는 `style25/material-comparison`입니다. `NativeStyle25Observation.CaptureBoundaries`는 실제 Play에서 기존 입장/카메라를 사용하여 세 값을 비교하고 복원합니다. `style25_gate.py`는 불투명선 비율과 기존 반투명선의 linear 합성식을 구분하며, 최종 계약은 `style25/request-final.json`/`state-final.json`입니다. 첫 실패 판정과 PropertyBlock 관측도 원인과 함께 보존합니다.

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
