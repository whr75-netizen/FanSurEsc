# B33 — 거절된 제작 경로와 원본 자동 격자 교정

**현재:** B33의 고정/가변 강제 축소 둘 다 사용자 거절입니다. 아래의 uniform 완료/실행 설명은 과거 기록이며 새 제작에 사용하지 않습니다. `normalize_art.py`, `normalize_uniform.py`, Unity `Build()`/`Apply()`는 부작용 전에 오류로 거절합니다. 기존 씬・원본・Inspect 기능은 보존합니다.

현재 실행 가능한 정규화는 `native_normalize.py`입니다. `--source`, 새 `--output-dir`, 원본 checkout `--engine`, 기존 `--deps`만 받고 수동 grid/target/PPU/scale은 받지 않습니다. 실제 원본 public API의 자동 검출 → 경계 정렬 → center sampling을 수행하며 RGBA를 같은 좌표에서 취합니다. 크기 맞춤・crop・경계/색/명암 수정은 하지 않습니다. 실패는 receipt에 보존하고 임의 해상도로 대신하지 않습니다. [실행 기록](../../docs/artifacts/building33-native-probe/receipt.json)은 계산대1374×1145 →274×228이며, 최종 배치나 디자인 승인 증거가 아닙니다.

생성・정규화・배치의 입력 경계는 `production_gate.py`와 `production-contract.json`에서 확인합니다. 기준 전체 아트/배치 calibration이 아직 없으므로 새 생성/배치가 준비됐다고 판정하지 않습니다. 이 게이트는 제작 경로의 계약 검사이며 Codex 도구 전체를 막는 샌드박스가 아닙니다. 현재 연구와 남은 제작은 [통합 연구](../../docs/references/grave_seasons_map_art.md), 운영 교정은 [Astra 리뷰](../../docs/references/codex_interruption_research.md)를 봅니다.

고정된 `remediation-graph.json`은 7개 실패 경계의 [실제 확인 결과](../../docs/artifacts/building33-native-probe/remediation-checks.json)를 만들었습니다. 최종 상태는 `LocalOnly/ProductionAudit27/exact-cause-state.json`에 보존합니다. 거절 결과는 임의 오류가 아니라 각 사례의 원인 코드까지 비교합니다. 이 그래프 완료는 운영 교정의 검사 범위이며 새 건물 제작 완료가 아닙니다. 이후 자산을 만들 때는 생성 전에 `production_gate.py --stage generation`, 원본 변환 후 `--stage normalization --receipt <실제 receipt>`, 배치 전에 `--stage placement --receipt <실제 receipt>`를 사용합니다. placement solver는 아직 미등록이며 성공을 가정하지 않습니다. 기준 맵 컨셉 생성 자체와 그 기준에서 개별 자산을 생산하는 generation gate는 별개입니다.

## 아래는 종전 B33 기록 — 재실행 지침 아님

부모 목표는 **개별 픽셀 오브젝트로 구성한 기지 테스트 건물 한 채의 디자인·배치·표시·명암을 실제 GameMap1에 통합하여 보여 주는 것**입니다. B32 도면/coverage 실험은 선행 입력으로 재사용합니다. 연구·자산 생성·컴파일 완료에서 부모 요청을 종료하지 않습니다. 기존 B31/32 실행 기록·원본은 보존합니다.

현재 결정·원본/정규화의 비례 한계·실제 관측 상태는 [통합 연구 B33](../../docs/references/grave_seasons_map_art.md)가 담당합니다. 최신 사용자 계약은 **물체마다 실제 크기는 다르게, 픽셀 크기만 공통**입니다. 새 변환은 [uniform manifest](../../docs/artifacts/building33/uniform-art-manifest.json), 거절된 이전 변환은 [이전 art manifest](../../docs/artifacts/building33/art-manifest.json)에 분리 보존합니다.

**이전 B33 외형은 거절 상태로 보존하고 새 수정본의 통합·기술 관측은 완료했습니다. 미술 승인은 별도입니다.** `normalize_uniform.py`는 원본 crop에 `q=min(Wmax/Ws,Hmax/Hs)` 한 개를 적용해 물체별 가변 native canvas를 만듭니다. 계산대102×85, 뒤선반109×126, 좌선반71×118, 진열섬89×64, 재고선반94×119입니다. B32 slot은 예약공간이고 실제 물리 proxy는 그 안에서 축소됩니다. 원본 내부 각도와 bbox 추정 높이를 CAD처럼 정확히 보장하지 않으며, 각 축 정수화 오차는1px 미만입니다.

새 PPU=`32√2=45.254834`로 밀도만 이전의2배입니다. 실제857px/ortho4.734301 시야에서 source 한 칸당 화면2칸을 확인했습니다. 5개 물체 x/y cell 측정 오차는0.00008 screen pixel 미만, transform scale은 모두1입니다. 사용자 미술 승인은 남아 있습니다.

## 최종 기술 증거와 한계

[technical-result.json](../../docs/artifacts/building33-uniform/technical-result.json)은 `technicalReady:true`/오류0이며 uniform graph는3단계에서 완료했습니다. [readback](../../docs/artifacts/building33-uniform/readback.json)과 [display](../../docs/artifacts/building33-uniform/unity-display.json)는 예약 slot 내부의 서로 다른 시설 크기, 접근6/6·벽 차단·가림·동일 실제 Player/Camera ID·Missing Script0·신규 Console 오류0을 기록합니다. 기존 relay 오류1개는 보존했고, 마지막 GameMap1은 Edit Mode 저장·clean/SceneView30° 상태입니다.

조명차이0은 기존 CharacterSilhouetteRendererFeature의 두 depth copy가 공유 material source 바인딩을 덮는 문제였습니다. 각 draw의 source를 MaterialPropertyBlock으로 분리한 뒤 feature를 켠 정상 경로에서 광원 ON/OFF195,848픽셀 차이를 확인했습니다. feature OFF의200,487픽셀 case는 의존성 진단이며 최종 설정이 아닙니다. 실제 [실내](../../docs/artifacts/building33-uniform/play-interior.png)·[실외](../../docs/artifacts/building33-uniform/play-exterior.png)를 최종 관찰 단위로 제시합니다.

기술 통과는 생성 원본의 내부 각도·정확한 CAD 높이·팔레트/클러스터·Grave Seasons 수준의 미술 합격이 아닙니다. 기존 방사형 local light에는 실제 벽/가구 occluder 계산이 없어 빛이 경계를 넘을 수 있습니다. 최종 건물 피드백은 한 번 받고, 중간 재료마다 다시 질문하여 작업을 끊지 않습니다.

## 현재 수정 실행

사용자 정정으로 이전 `graph.json` 실행은 보존·정지하고 새 `uniform-graph.json`을 사용합니다. 기존 고정 판정 기준을 바꾸는 재실행이 아닙니다. 이미 생성된 state는 덮어쓰거나 다시 init하지 않습니다.

```powershell
& 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 -B Tools/WorkLoop/work_loop.py next LocalOnly/Building33/uniform-state.json
```

새 실행을 처음 설정할 때만 `init LocalOnly/Building33/uniform-state.json Tools/Building33/uniform-graph.json`과 `run`을 사용합니다. 현재 흐름은 `apply → observe → validate`이고 반환은 각각 `{"prefab":"실제 기존 prefab 경로"}`, `{"readback":"실제 Unity 관측 경로"}`입니다. 실제 Unity 표시 관측은 `docs/artifacts/building33-uniform/unity-display.json`, 판정은 같은 폴더의 `technical-result.json`입니다.

`PlannedPixelBuildingUniformRevision.Apply()` / `Tools > World Art > Apply B33 Uniform Source Revision`은 기존 prefab 참조·표시·해당 proxy만 수정합니다. 새 건물/Player/Camera를 재생성하지 않습니다. `Capture B33 Uniform Display Readback`은 각 자산의 서로 다른 native 크기, 공통 source cell 표시폭, transform scale을 실제 Unity에서 읽습니다. 결과는 source cell x/y폭2px·scale1·예약공간 내 점유·실제 기지 동작·광원 기여를 포함해야 하며 미술 합격은 사용자 판단입니다.

## Unity 진입점과 관측 실행

- **기존 Build:** Edit Mode의 `Tools > World Art > Build Planned Pixel Shop 33` → `PlannedPixelBuildingAuthoring.Build()`는 최초 B33 조립 진입점입니다. 현재 uniform 수정에는 위 Apply를 사용하며 기존 건물을 재생성하지 않습니다.
- **Inspect:** `Tools > World Art > Inspect Planned Pixel Shop 33` → `Inspect()`. Edit Mode에서는 선택·SceneView30° 정렬·실내 표시; Play Mode에서는 기존 Player를 실내로 이동합니다. 촬영용 Camera나 Player 복제본을 만들지 않습니다.
- **실내 개발 보기:** `Tools > World Art > Show Planned Shop Interior in Scene View` → `ShowInterior()`. SceneVisibility로 지붕/앞벽만 editor에서 숨깁니다. 실제 게임의 UrbanOcclusionFader와 분리됩니다.
- **관측 helper:** `Assets/Editor/PlannedPixelBuildingObservation.cs`의 public `Execute(string phase)`를 `Tools/Building33/observe.cs`의 짧은 Unity_RunCommand 어댑터로 호출합니다. Editor assembly가 JsonUtility DTO를 소유하며 동적 MCP assembly에서 배열 DTO를 중복 정의하지 않습니다.

현재 관측 순서는 정상 Play가 시작된 상태에서 `begin → inside → finish`입니다. `begin`은 현재 인스턴스 ID와 collider 좌표, 실제 이동/벽 충돌을 기록하고 외부 GameView를 예약합니다. `inside`는 실내/가림을 기록합니다. `finish`가 최종 화면과 같은 카메라 controlled ON/OFF 렌더로 조명 기여를 분리합니다. `lights-off`는 과거 별도 화면을 보존할 때 쓰는 선택 단계이며 현재 필수 절차가 아닙니다. 각 screenshot 예약은 후속 프레임에 처리되므로 파일 생성이 끝나기 전에 다음 상태나 Play 종료로 넘어가지 않습니다. Play 중 코드 편집/재컴파일은 현재 관측 세션의 상태를 깨뜨릴 수 있으므로 필요한 편집을 마치고 정상 새 Play에서 관측을 시작합니다.

관측 전에 저장된 scene prefab 경로를 `SessionState`의 `B33ObservedScenePrefab`에 실제 prefab 연결에서 기록합니다. Console은 MCP로 실제 새 오류를 확인한 뒤 `RecordConsoleErrors(int observedNewErrors)`로 그 수를 반영합니다. 임의로0을 넣는 호출은 검증이 아닙니다. 실행한 단계와 미실행 단계를 구분하며, 부분 readback은 최종 결과로 제출하지 않습니다.

## 이전 거절본 그래프 계약 — 보존용

아래는 이전 `graph.json`의 기록이며 현재 수정의 실행 명령이 아닙니다. 현재는 위 uniform graph를 사용합니다.

```powershell
& 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 -B Tools/WorkLoop/work_loop.py init LocalOnly/Building33/state.json Tools/Building33/graph.json
& 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 -B Tools/WorkLoop/work_loop.py run LocalOnly/Building33/state.json
```

각 인계에서 실제 작업 후 `{"ticket":"반환 ticket","output":{...}}` 파일을 `submit`합니다. `ai.work.question`은 Codex의 작업 지시이며 사용자에게 다시 물으라는 뜻이 아닙니다.

| 노드 | 실제 작업 | 반환 schema |
|---|---|---|
| art | 참고작/역할 명세에 맞는 개별 자산 및 필요한 정규화 | `{"manifest":"실제 manifest 경로"}` |
| integrate | B32 도면, FullRect·공통 격자·정수 표시, 명암을 기지에 통합 | `{"prefab":"실제 저장 prefab 경로"}` |
| observe | 기존 실제 Player/Camera로 Unity 관측·GameView PNG 준비 | `{"readback":"LocalOnly/Building33/readback.json 절대경로"}` |
| validate | 고정 Python이 Unity 관측값·도면 수치·PNG를 읽어 판정 | exit 0이면 기술 납품 완료, 사용자 미술 판단은 pending |

validate가 실패하면 실제 측정 실패가 `integrate.repairEvidence`로 전달됩니다. 첫 제작을 포함해 통합/관측/판정은 최대 2회이며, 수정 원인이 생긴 항목만 수선합니다. 동일 입력 무의미 반복을 허용하지 않습니다. 실행 중 그래프/요구를 바꿔 통과시키지 않습니다. 실제 외부 차단이나 두 번째 기술 실패는 원인과 남은 결과를 그대로 보고해야 하며 미술 질문으로 덮지 않습니다.

## 이전 거절본 Unity readback 계약 — 보존용

아래 값은 **Unity Editor API가 실제 관측으로 기록**합니다. AI가 JSON에 `true`를 써 넣어 성공을 만드는 것은 불합격입니다. 코드와 실제 도구 호출 출처를 보존합니다. 이 값이 기계적으로 참조 가능하다는 사실은 사용자 미술 승인이나 실행의 암호학적 증명을 뜻하지 않습니다.

| 필드 | 자료형·판정 | 관측 원천 |
|---|---|---|
| producer | `UnityEditor.Building33Observation` | Unity 관측 코드의 고정 식별자 |
| scene / isPlayMode | `GameMap1` / true | 현재 Scene/EditorApplication |
| prefab / artManifest / layoutPlan | 실제 파일 경로 | 배치된 prefab 연결·제작 입력 |
| fixtureCount / nativeSpriteCount | 정수 ≥5 / ≥8 | 실제 건물 하위 시설·자산 참조 |
| fixtures | `{id,rectXZ:[x0,z0,x1,z1]}` 배열 | 실제 collider를 building-local XZ로 변환 |
| layoutMatches | true | B32 fixture별 footprint 비교 |
| actualCameraPitch / actualCameraYaw | 30 / 350, 오차0.05° 미만 | 실제 gameplay camera transform |
| orthographic | true | 실제 gameplay camera |
| sceneViewPitch / sceneViewOrthographic | 30 / true | 실제 SceneView |
| nativePixelsPerUnit | 양의 유한 수 | 현재 native pixel/world 변환 |
| screenPixelsPerSourcePixel | ≥1의 정수, 오차0.001 미만 | 실제 viewport/직교크기/PPU 또는 실제 동일 격자 표시 변환 |
| fullRectCoverage / doublePixelation | true / false | 실제 quad UV/coverage와 renderer pass 연결 |
| entryReached / wallBlocked / occlusionObserved | true | 실제 Player 이동 및 fader 관측 |
| identities | playerBefore/After, cameraBefore/After | 실제 런타임 entity ID, 각각 동일해야 함 |
| lightingPath / lightingRegionCount | 실제 경로 문자열 / ≥1 | 실제 material/shader·조명영역 연결 |
| lightingObserved | true | 실제 GameView의 적용과 관측 근거 |
| missingScripts / newErrors | 정수0 / 0 | 실제 계층 및 이번 범위 Console |
| screenshots | 내부/외부 실제 PNG 경로2개 이상 | 변경하지 않은 실제 gameplay view |
| artisticApproval | `pending` | 기술 판정과 별도의 사용자 판단 상태 |

fixture 사각형은 `docs/artifacts/building32/layout-plan.json`의 5개 시설과 각 좌표 0.01m 이내여야 합니다. 이 검사는 접근로 설계의 기하 원본을 보존할 뿐 모든 동작·미술을 증명하지 않습니다. 동일성이란 ID의 실제 전후 관측이며, 복제본의 값 일치가 아닙니다. 호출로 이동했다면 사용자 보고/상세 증거에 `[Play Mode 호출 확인]`으로 표시합니다.

최종 명령은 `docs/artifacts/building33/technical-result.json`에 판정 범위·readback 해시·미리보기 해시·실패 목록을 기록합니다. `technicalReady:true`여도 `artisticApproval:pending`입니다. Codex는 실제 최종 화면과 변경 결과를 사용자에게 납품한 다음 외형 피드백을 받습니다. 중간 자산/문서만 보여 주고 이 최종 납품을 생략하면 그래프의 부모 목표를 달성하지 못한 것입니다.

## 검증 한계

이 그래프는 올바른 관측 코드가 제공한 제한된 기술 계약을 판정합니다. 픽셀 통계로 레퍼런스의 미술 수준을 자동 판정하지 않습니다. 검증 실패를 통과시키려고 입력 schema·기준을 완화하지 않습니다. 사용자 수정은 실제 변화 원인으로 다음 계약에 연결하고, 승인/거절 여부를 AI가 발명하지 않습니다.
