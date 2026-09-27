# Building31 — 개별 native 픽셀 자산으로 조립하는 기지 테스트 건물

사용자 최신 정정은 전체 맵 생성/축소 결과를 거절하고 **오브젝트별로 만든 자산을 배치한 테스트 건물 한 채를 GameMap1 기지씬에 완성**하는 것입니다. 원본은 Hawkbirdtree의 CC0 `furnitureandwalls.png`(320×960)이며, 정수 사각형의 1:1 crop으로 개별 자산을 추출합니다. 이미 native 픽셀인 원본에 재축소/확대를 정규화로 포장하지 않습니다. 출처·파일 해시·crop 좌표·피벗은 acquire에서 반환한 manifest가 담당합니다. PixelLab 만료 요청의 실패는 성공적인 생성이나 유료 사용으로 기록하지 않습니다.

`graph.json`은 기존 WorkLoop의 다섯 단계만 연결합니다.

1. `acquire`: 오브젝트 원본 확보/보존과 1:1 추출 manifest → `{ "source": "실제 원본 경로", "manifest": "실제 manifest 경로" }`
2. `assemble`: 공통 픽셀/좌표/피벗·물리 footprint 규칙으로 Unity Editor prefab 조립 및 GameMap1 배치 → `{ "prefab": "Assets/…prefab" }`
3. `observe`: 실제 Play Mode 출입·충돌·가림, 기존 Player/Camera 동일성, 승인된 실제 카메라 기본 pitch 30도 계약 및 실제 카메라 PNG → `{ "readback": "프로젝트/LocalOnly/Building31/readback.json 절대경로" }`
4. `validate`: 고정된 `validate.py`가 실제 Unity readback과 PNG를 읽어 필요한 최종 기술 조건만 확인합니다. 실패는 차단하며 자동 재시도하지 않습니다.
5. `review`: 실제 플레이 화면을 보여주고 사용자 미술 피드백을 기다립니다. 답변이 없으면 pending을 유지합니다. 사용자 답변 제출 후에도 자동 미술 합격/완료가 아닌 명시된 중단 지점으로 종료하고 해당 피드백으로 다음 범위를 결정합니다.

최신 사용자 승인("해당게임이30도고 쿼터뷰가 대부분다30도면 그렇게바꿔")에 따라 실제 플레이 카메라의 전역 기본 pitch를 30도로 변경하고 기존 yaw 350도는 유지합니다. 건물 root yaw는 305도로 두어 상대 방위 45도를 맞춥니다. 별도 촬영 카메라나 건물 지역 진입 시점 전환을 도입하지 않습니다. 변경 사유 없는 줌·타깃·Player/Camera 인스턴스와 기지 상태는 유지합니다.

## 실행

현재 결과: `Assets/Prefabs/World/NativePixelShop31.prefab`, GameMap1 위치 `(-16,0,9)`, 바닥10×8m. **Play 후 `Tools > World Art > Inspect Native Pixel Shop 31`**을 실행하면 기존 플레이어를 시험 건물 내부로 이동시킨다. Edit Mode에서는 기존 건물을 선택/프레임한다. 제작 메뉴는 기존 프리팹을 덮어쓰지 않는다. 개별 오브젝트는 프리팹의 `ShopFurniture`, `Exterior`, `Floor`, `FlatRoof`에서 편집한다.

원본은 `Tools/Building31/Source/furnitureandwalls.png`, 자산/crop manifest는 `Assets/Art/NativePixelBuilding31/`이다. 새 AI 생성은 하지 않았으며 PixelLab은 잔액 조회에서 구독 만료를 확인했다. 실제 실행 상태는 `LocalOnly/Building31/state.json`이다.

주의: 이 세트는 기본 고정 시점용이다. 기존 자유 오빗 입력을 무단 삭제하지 않았으므로 다른 각도에는 맞지 않는다. 원본 픽셀은 변하지 않지만 화면높이857/ortho5에서는 표시 배율3.78744이므로 화면 열 폭은3/4px로 나뉜다. 정수 화면 배율을 보장하는 줌·렌더 설정은 이번에 바꾸지 않았다. 새 제작 아트의 품질이나 동적 표면 조명까지 검증했다고 하지 않는다.

프로젝트 루트에서 이미 승인된 담당 AI가 실행합니다. 새 프레임워크나 사용자 직접 조작은 필요하지 않습니다.

```powershell
& 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 -B Tools/WorkLoop/work_loop.py init LocalOnly/WorkLoop/building31/state.json Tools/Building31/graph.json
& 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 -B Tools/WorkLoop/work_loop.py run LocalOnly/WorkLoop/building31/state.json
```

각 인계는 실제 현재 ticket으로 `{"ticket":"…","output":{…}}`를 제출합니다. `submit`은 다음 단계까지 일반 계산을 연속 실행하므로 `observe` 제출 직후에는 validator가 한 번 실행됩니다. 그래프와 validator는 init 시 고정되고 `parameters.code_files`의 SHA-256은 실행기가 계산/재확인합니다. 실행 중 계약/검사기를 고치거나 같은 상태를 재실행하여 실패를 지우지 않습니다.

## Unity readback 계약

다음 값은 root의 Unity C# 관측 코드가 **직접** 기록해야 합니다. AI가 결과 JSON에 성공 기본값을 채우는 용도가 아닙니다.

| 필드 | 요구 |
|---|---|
| `scene` | 정확히 `GameMap1` |
| `prefabExists` | 실제 저장 prefab 확인 `true` |
| `nativeSprites` | 정수, 최소 12 |
| `rendererCount` | 정수, 최소 20 |
| `colliderCount` | 정수, 최소 8 |
| `entryReached` | 실제 Player 출입 관측 `true` |
| `wallBlocked` | 실제 벽 충돌 관측 `true` |
| `occlusionObserved` | 실제 가림 처리 관측 `true` |
| `cameraContractMatched` | 실제 기본 pitch 30도·yaw 350도와 보존 대상 카메라 상태의 계약 readback `true` |
| `samePlayer`, `sameCamera` | 전후 실제 인스턴스 동일성 `true` |
| `screenshot` | 실제 Play 카메라 PNG의 절대 또는 프로젝트 상대 경로 |

추가 원시 관측 값·인스턴스 ID·거리·카메라 전후 상태는 readback에 함께 보존할 수 있습니다. validator는 bool과 int를 엄격히 구분하며 필드 누락을 합격으로 바꾸지 않습니다. PNG가 실제로 열리는지와 파일 해시를 기록합니다. readback 파일은 고정된 `LocalOnly/Building31/readback.json`만 허용합니다.

이 검사는 Unity가 기록한 관측의 계약과 PNG 파일을 확인합니다. 게임플레이를 독립 재연하거나 그림체·비율·배치의 만족도를 판정하지 않습니다. Play Mode에서 API로만 조작했다면 보고 역시 `[Play Mode 호출 확인]`으로 남겨야 합니다. 원본 이미지→전체 방 이미지→재축소의 이전 경로는 이 그래프의 입력이 아닙니다.

각 단계는 서로 다른 source/crops, prefab/edit-state, temporary-play/readback 자원을 사용하여 후속 관측이 앞선 자산 관측을 무효화하지 않도록 분리했습니다. 이 자원 선언은 작업 범위 계약이며 OS 권한이나 새로운 외부 쓰기 승인이 아닙니다.
