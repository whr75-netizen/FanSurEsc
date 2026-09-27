# B34 — 기지 상가 내부 완성 및 깊이 교정

요청: 기존 기지 건물 한 채를 개별 픽셀 오브젝트로 완성하고 지붕/이미지 프레임 누출을 고친다. B33의 강제 축소·그림 전체 높이를 물리 높이로 쓰는 전제는 재사용하지 않는다. 기존 Player/Camera, B32 평면·사용점, 기존 원본/거절 결과를 보존한다.

## 제작 결정 / 실패 조건

`기준 아트+B32 역할 도면 → 원본 자동 격자 → 공통 투영/물체 체적 연결 → 개별 자산·실제 깊이 → 기존 prefab 내부 교체 → 실제 플레이`

- 기준: `Source/master-reference.png`. 이는 기존 개별 원본을 사용해 만든 스타일·배치 참고이며 최종 배경 이미지가 아니다. 원작 복제/정확한 투영/미술 승인을 뜻하지 않는다.
- 재료: B33의 고해상도 가구/벽/바닥/램프 원본 9종. 이미 만든 원본을 보존하고 원본 PerfectPixel 자동 검출로 복원한 `docs/artifacts/building34/native/`를 사용한다. 수동 target/resize/재확대 없음. 계산대는 지난 실제 결과 재사용.
- 최종 바닥 재료: 기준 아트의 따뜻한 목재와 기존 청회색 바닥의 차이를 보완한 `Source/floor-warm-source.png`다. 내장 이미지 생성1회와 원본 자동 정규화1회를 거친 `docs/artifacts/building34/warm-floor/native.png`(125×132)를 그대로 재료로 읽는다. 생성 원본1254×1254와 prompt/provenance/receipt를 보존하며 정사각형이나 목표 크기로 재축소하지 않는다.
- 평면: B32 10×8m, 앞 출입구2m, 뒤 우측 재고실, 주통로1.5m, 시설5개/접근점6개. 계산대 체적에는 상판 위 계산기까지 포함하므로 proxy 높이만1.55m로 명시한다. 표면은 생성 원본, 충돌/가림 체적은 설계 데이터이며 정확한 3D 복원이 아니다.
- 대안: 수직 sprite plane은 바닥 깊이 성분을 높이로 오인해 선반이 지붕 위로 올라간다. 뒤로 옮기는 보정은 밑부분을 바닥에 묻는다. 정렬순서 강제/지붕 상승/그림 축소를 채택하지 않는다.
- 선택: fixed-view depth impostor. CPU의 ray/box slab 교점 XYZ를 source texel과 1:1로 저장하고 Forward/DepthOnly/DepthNormals에 같은 SV_Depth를 쓴다. 색은 원본 Point sampling 그대로다. 물체별 sortingOrder 예외 없음.
- 구조 면: 바닥·벽·지붕은 실제 닫힌 box 면을 공통 격자에 저작한다. 가구 이미지를 면마다 바르지 않는다. 지붕은 독립 불투명 coverage이며 바닥의 alpha diamond를 지붕 구멍으로 재사용하지 않는다. 벽/바닥 재질은 기존 정규화 이미지의 명시한 내부 재료 영역에서 샘플한다.

## 좌표·변환 계약

- 원본: 좌상단 원점, x오른쪽/y아래, px. Unity UV는 좌하단; `y_native=H-1-y_unity`.
- 건물: Unity 좌수계 X오른쪽/Y위/Z뒤, m, root yaw305°. 카메라 world yaw350°/pitch30°, ortho. local yaw45°.
- `r=(1,0,-1)/sqrt(2)`, `u=(sin30/sqrt2,cos30,sin30/sqrt2)`, `d=(cos30/sqrt2,-sin30,cos30/sqrt2)`. 실제 Unity Quaternion 기저와 직교성으로 부호를 확인한다.
- 이미지 셀 중심 q에서 투영좌표 `s=q/p+t`, image plane `P=r*s.x+u*s.y`, ray `P+λd`. 모든 물체에 같은 p(px/m). t는 cuboid 투영 hull와 원본 alpha 셀 사각형의 halfplane 제약으로 계산한다. 임의 per-part scale/rotation은 없다. 이미지 자체의 생성 각도 오차를 이 계산이 복구했다고 주장하지 않는다.
- CPU가 모든 불투명 셀의 교차를 검사한다. miss는 실패이며 clip/fallback으로 통과시키지 않는다. 유효 교점은 선언 체적 내부, 가구 높이는 지붕 아래. depthmap XYZ는 오브젝트 local, renderer transform이 world로 운반한다.
- Unity 그림은 native texture 한 칸을 화면 정수칸으로 표시한다. 전체화면 픽셀 패스는 끈 기존 상태 유지. shader snap은 전체 visual translation만 허용하며 텍스처 재축소는 없다.
- 지원: 이번 고정 시점과 동일 SceneView. 자유 회전/방향별 새 아트는 이번 결과에 포함되지 않는다.

## 방향 교정과 최종 공통 축척

`calibration.json`의 최초181px/m 결과는 실패 기록으로 보존한다. 원본 계산대·선반 장축이 B32 시설 축과 반대인 상태에서 실루엣 전체를 cuboid 투영 안에 넣으려 했기 때문에, 포함 제약이 잘못된 방향을 해결하지 못하고 공통 PPU를 높였다. 그 결과 캐릭터 대비 가구가 작게 보였다. ray miss0은 이 방향·비율 요구의 충족을 증명하지 않았다.

현재 권위 입력은 `docs/artifacts/building34/calibration-oriented.json`이다. 실제 Unity 카메라의 직교 기저에서 local X 장축은 화면 오른쪽 위를 향하고 local Z 장축은 왼쪽 위를 향한다. 계산대·좌선반·뒤선반·재고선반의 `mirrorU=true`, 진열섬은 `false`로 각 원본의 장축을 명시한 시설 축에 맞춘다. 원본 PNG 바이트는 바꾸지 않으며 렌더 UV와 깊이 계산의 픽셀 주소에 같은 반전을 적용한다.

반전 시 셀 중심은 `q=(W-x-0.5, -y-0.5)`, 유지 시 `q=(x+0.5, -y-0.5)`다. 동일 halfplane 포함 제약을 다시 풀어 최소 공통126.568887px/m를 구했고 올림한 **127px/m**를 사용한다. 불투명 셀 중심과 네 모서리의 slab ray miss는5시설 모두0이다. 정확한 최하단 접지가 불가능한 경우에는 feasible translation polygon의 최저Y를 선택하고 간격을 artifact에 기록했다. 이 기하 계산을 실제 플레이 완료나 미술 합격으로 승격하지 않는다.

가림 면도 같은 기저를 따른다. 카메라는 local `-forward` 쪽에 있으므로 near wall은 `wall_left`(X최소)와 앞벽(Z최소)이다. 내부에서는 이 벽과 칸막이를 기존 가림 소유자가 처리하고, 뒤/우측 벽은 남긴다. 반대로 우측 벽을 near wall로 등록하던 분류를 수정한다.

잔여 한계: U반전은 방향만 바꾸며 원본의 내부 기울기나 서로 다른 생성물의 논리 픽셀 밀도를 복원하지 않는다. 공통127px/m와 보존된 원본 조건 아래 재고선반의 표시 높이 등 차이가 남는다. 원본 생성 단계의 공통 시점·치수 landmark·asset sheet 없이 모든 의도 치수와 원본 특징을 동시에 정확히 맞췄다고 주장할 수 없다. 이 결과는 local pitch30°/yaw45° 고정 시점용이며 임의 카메라 회전에서의 동등한 깊이/외형을 보장하지 않는다.

## 로컬 재현 경로

1. 보존된 `native/`9종, `warm-floor/`, B32 도면을 입력으로 사용한다. 새 원본 변경이 없다면 정규화를 다시 실행하지 않는다.
2. 새 교정 파일이 필요할 때만 `calibrate.py --orientation-policy fixture-facing --output <새 파일>`을 실행한다. 기존 출력은 덮어쓰지 않는다. 현재 Unity 저작기는 `calibration-oriented.json`을 읽는다.
3. Unity Edit Mode에서 `PixelShopInteriorCompletion.Apply()`를 실행하고 이어서 `PixelShopInteriorCompletion.ApplyWarmFloor()`를 실행한다. 첫 호출은 같은 기존 건물 prefab 내부에 개별 sprite/depth/닫힌 구조 면을 연결하고, 두 번째 호출은 생성 목재 재료를 해당 바닥 표면에 연결한다. Player/Camera를 새로 만들지 않는다.
4. 새 저작 출력은 `Assets/Art/PixelShopInterior34Aligned/`에 저장한다. 종전 `PixelShopInterior34/`와181 교정 결과는 보존한다. `Apply()`와 `ApplyWarmFloor()`는 기존 출력 덮어쓰기를 거부하므로 완료 경로를 무조건 반복하거나 재실행을 위해 폴더를 삭제하지 않는다.
5. `PixelShopInteriorCompletion.ShowInterior()`로 개발용 내부 시점을 확인하고 실제 Play Mode의 출입/사용점/가림/픽셀 표시를 별도로 관찰한다. 이 README 갱신 시점에는 방향 교정 뒤 최종 Play 검증을 완료했다고 기록하지 않는다.

## 실제 확인할 조건

최종 편집 실행 순서는 `Apply()` → `ApplyWarmFloor()` → `ApplyCutawayBases()`다. 마지막 단계는 앞벽·칸막이의 실제 하단 .55m를 남기고 상부만 fade하여 보이지 않는 충돌 경계를 없앤다. 충돌 체적은 변경하지 않는다. 중복 제작은 거절한다. `ShowInterior()`는 SceneView를 정렬하며 Play에서는 기존 Player를 상가로 이동시킨다.

### 실제 납품 / 실패를 보존한 최종 판정

`graph.json`의181px/m 통합은 방향 누락이 발견되어 중지했고, `graph-oriented.json`은 제작·관측 후 수동 Console값이 미확정(-1)이므로 완료되지 않았다. 그 기준을 조용히 바꾸지 않았다. 수동 오류0 기록은 자동 승인 검토에서 거부됐다. 마지막 실제 렌더를 사이에 둔 완전한 MCP 응답 `console-window-before.json`/`after.json`을 별도로 저장했다. 오류 이력11건이 그대로 남았고 구간 내 추가 오류는0이다. `graph-final-validation.json`과 `validate_final_delivery.py`는 응답 개수·시간 순서·이력 보존·차이를 직접 계산하며 수동 `newErrors` 필드를 사용하지 않는다. 기존 오류가 모두 없다는 뜻이 아니다.

`delivery-final-result.json`의 기술 조건은 통과했다. StepMove6/6, 같은 Player/Camera, 벽정지, 지붕 전환, source/depth mask 불일치0, frame/roof 누출0. Console 경고 중 기존 volumetric Spot Light 가시성/개수 경고는 남겼다. 미술 합격과 자유 회전, 물리 키 입력, 빌드/저장로드, GPU 성능은 이 판정에 포함되지 않는다.

Game뷰1114×857은127px/m에서1배이며 기존 줌 범위를 만족하지 않는다. 텍스처를 강제 축소하지 않도록1배를 우선하는 기존 카메라 계약의 한계다. 전체 실내 PNG2560×1600은 같은 카메라의 일시적 조망이고 실제 걷기 화면과 구분한다. 독립 생성 원본의 내부 투영/정보 밀도 차이는 남아 있다.

입력 hash/원본 격자, opaque-ray miss0, 교점의 cuboid 포함(1e-4m), 구조 표면의 closed roof coverage, alpha 밖 depth쓰기 없음, 동일 실제 Player/Camera, 출입/6사용점/벽충돌, 내부 지붕숨김·외부복원, 실제 GameView/SceneView, 신규 shader/Console 오류. 기술 판정과 미술 완성도는 구분하며 형식적 만족도 질문으로 작업을 중단하지 않는다.

근거: [Unity shader depth pass](https://docs.unity.com/en-us/engine/6000.6/manual/materials-and-shaders/shaders/writing-custom-shaders-urp/writing-shaders-urp/depth-only)는 모든 pass의 동일 fragment/위치·alpha를 요구한다. [ZTest](https://docs.unity3d.com/Manual/SL-ZTest.html)는 실제 depth 비교를 담당한다. 해당 API는 연결 단계의 근거이며 생성 이미지의 의미적 깊이를 증명하지 않는다.
