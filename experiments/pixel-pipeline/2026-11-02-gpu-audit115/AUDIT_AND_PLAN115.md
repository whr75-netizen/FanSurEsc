# 115 GPU reset 정적 감사와 다음 검증 계획

이번 감사에서는 Unity 호출·GPU dispatch·Play·Assets 수정·import를 실행하지 않았다. 코드와 저장113 입력으로 상한을 계산했다. 실패115 첫 프레임의 GPU header/완료 단계/시간은 저장되지 않았으므로, 아래113 수치를 실패 프레임의 실측값으로 대체하지 않는다.

## 판정

이전 로그에는 D3D11 device reset/removed와 unrecoverable 종료 메시지가 있다. 정확한 원인 kernel은 아직 확인되지 않았다. 원형 평가가 조합 수의 지수를 추가한 것은 아니지만, 비교용113과115를 같은 pass에 넣으면서 큰 작업을 반복했다. 유한한 루프라는 사실만으로 안전한 GPU 실행 시간을 증명할 수 없다. 동일 full115 또는 큰 offscreen 경로를 재실행하지 않는다.

| 항목 | 113 | 115 비교 경로 | 근거/한계 |
|---|---:|---:|---|
| 큰 dispatch의 명목 work item | 4,194,304 | 12,582,912 | baseline113 enumeration +115 enumeration +115 collection, 각32768×2 groups×64 |
| 같은 source의 BVH query ray | 82,944 | 92,160 | owner3→4, 추가 carrier4x. 실제 살아 있는 ray/visit 수와 GPU 시간은 미측정 |
| structured buffer 합계 | 31,966,348B | 42,814,800B | 저장 geometry/grid 기준. RT·driver·shader 내부 메모리 제외 |
| 원형 평가 후보 | 해당 평가 없음 | 눈별≤128 | 초과는 실패. 저장113의 1차 동률은 눈별1~2개 |

열린 눈 저장 F99/F115는 각각(iris6+white10)16비트, (iris8+white12)20비트다. 두 눈의 eligible state 합은1,114,112이고, 가장 큰 한쪽은1,048,576개다. 첫4목적함수 뒤 원형 평가 입력은 각1개이므로 **이 저장 입력에서 원형 상대배치 계산 자체가 조합 폭발한 것은 아니다.** 실패115에는 이 header가 없어 동일하다고 단정할 수 없다.

## 함수별 상한·범위·동기화

`STATIC_AUDIT115.json`은 모든 저장113 header12개, source scope51건의 CPU 재계산, 유효 ni/nw 경계163개, topology/index/stride를 확인한다. 모든12개 geometry의 world/rest/view/projection은 finite였다. 첫 source의 partMap에 참조된 rest 삼각형 determinant는 모두 양수였다. 이는 실패115의 미관측 GPU 값까지 검증한 것은 아니다.

- `GatherEye113/RawConnected113`(compute360/357행): 눈마다 GPU1thread. 최대512셀×16성분, 각 flood는 최대512회이며 총 두 눈8,404,992 cell scan 상한이다. 불변 source 그래프는 별도 캐시/연결성 단계로 분리할 여지가 있다. palette/RGB 변경으로 이 그래프를 재정의하면 안 된다.
- `BuildSubsets113/Connected113`(374/369행): part별≤12비트, joint≤21비트. 두 눈에서 유효 part subset 합의 최대는9,216개다. 각 subset의8개 scope가 최장 연결성을 검사하는 느슨한 상한은37,158,912 point iteration이다. 빈/빠른 종료는 실제 비용을 줄인다.
- `Enumerate113/Enumerate115/CollectForm115`(375/435/438행): 눈별≤2^21. enumeration은 모든32768group이 barrier/reduction에 참여한다. collection은 group-best가 다르면 조기 종료하지만 큰 dispatch 자체는 그대로다. 115의 source-key 대리 벌점 제거가 bit 상한을 늘리지는 않았다.
- `PrepareCells113/115`(342/450행): keys≤32, cells≤512, curves≤1024. source key 확인≤2,097,152회, native lid distance loop≤33,554,432회라는 느슨한 상한이 있다. Upper curve를 셀마다 반복하고, 안검 셀의64sample 각각 전체 curve를 재검사한다. 현재 grid144셀/846segment/경계16셀에서 distance loop만으로도 최대866,304회/prepare다. source visibility에서 탈락하면 감소한다. baseline과 candidate에서 prepare가 반복된다.
- `EvaluateForm115`(442행): state를 새로 열거하지 않고 최대128개를 평가한다. key≤32/point≤24, 두 part에 속한 key pair 수는 총 choose(32,2) 이하이다. source-form private array5×float2[32]는1280B/호출이다. 실제 register/spill과 실행 시간은 compiler 통계/측정 없이는 알 수 없다. numthreads(1,1,1)라 lane 이용률 저하도 검토 대상이다.
- `Pareto115`(448행): 눈마다 GPU1thread가 최대128×127=16,256 candidate 비교, 최대97,536 dimension test를 직렬 수행한다. pool 상한을 넘긴 count는 비교 전에 실패 처리한다. 무제한 조합 수는 아니지만 병렬화/분할 가능한 직렬 구간이다.
- `Query`(104행): stack32와 overflow 처리는 있으나 visit 수/잘못된 node index에 대한 명시적 작업 예산은 없다. CPU median BVH는 child 집합이 엄격히 줄고 정상 자료에서 acyclic이므로 최대2T−1번 방문한다. 현재 T29,542/node59,083, 일반 계약 최대T262,144/node524,287이다. 정상 자료도 최악 ray 수와 곱하면 매우 큰 상한이다. 손상/잘못된 binding/비finite query가 실제 발생했다는 증거는 없지만, 현 GPU while에 독립적인 안전 예산이 없는 것은 남은 허점이다.
- `Refit`: CPU가 만든 level 순서로 leaf→root, 같은 command buffer에서 처리된다. Source `WholeEye107`별 compute shader는 각각 clone이므로 네 engine이 같은 mutable shader instance를 공유한다는 가설은 코드와 맞지 않는다.
- Region의 주요 buffer index/stride는 선언 용량 안에 있다. key48B/group48B/subset32B/stat32B/metric80B. 현재 geometry의 vertex/material/partMap index 검사 통과. GPU primitive/node 참조에는 추가 guard가 없는 곳이 있어 실패 프레임의 runtime corruption까지 배제하지는 못한다.
- enumeration의 group barrier는 divergent branch 바깥에 있고 uniform stride loop를 돈다. 새 source-form은 group barrier를 추가하지 않았다. `EvaluateForm115`는 RW UAV8개를 사용하므로 진단용 UAV를 무작정 더 붙이지 않는다.
- RenderGraph의 own structured buffer는 import/use 선언돼 있고 동일 command buffer의 순서로 사용한다. 최초 실패 당시 observer Release/Dispose는 아직 시작되지 않았다. 현재 코드에서 그 시점의 조기 해제/중복 해제를 확정하지 못했다. shader/driver 내부 자원 및 실제 제출 경계는 별도 관측이 필요하다.

`Full319View335.Read`의 `AsyncGPUReadback.WaitForCompletion`은 Editor main thread를 막을 수 있다. 따라서 Editor update의240초 timeout/정상 Exit callback은 GPU 작업이 정체된 동안 실행을 보장하지 못한다. timeout을 늘리는 것은 이 문제를 해결하지 않는다.

## 다음 최소 실행안 — 아직 미실행

1. 새 PID6288의 복구 기준을 보존한다. 이전 PID의 ID/buffer binding을 대입하지 않는다. scene/camera/renderer는 생성·재생성하지 않는다.
2. **첫 diagnostic은 own buffer만 사용하는 BeginForm115의2thread 초기화**로 제한한다. 그 다음에만 저장 F103의 실제 source moments/keys/points와 두 동률 layout을 입력으로 `EvaluateForm115`의2개 유효 candidate와 작은 `Pareto115`를 각각 별도 제출한다. BVH/curve raster/전수 열거/baseline 중복/전체 캐릭터 렌더는 포함하지 않는다. 최종 선택을 CPU에서 주입하는 replay가 아니라 GPU metric/부분순서 결과를 CPU exact reference와 비교한다.
3. 각 단계는 작은 기존 state/metric buffer만 `AsyncGPUReadback` callback으로 확인한다. `WaitForCompletion`은 쓰지 않는다. 완료 callback을 받은 뒤에만 다음 제출을 허용한다. 오류·검증 실패·완료 불명일 때 자동 재시도하지 않는다. 소유 자원은 완료 후 해제하고, pending 자원을 강제로 정리하지 않는다. 단계별 완료 표시는 추가 UAV 대신 이미 있는 진단 필드/작은 결과로 남긴다.
4. 전수 탐색 검증은 기존 단일65536group reduction을 부분 입력에 그대로 호출하지 않는다. 우선64state 한 group의 결과만 확인한다. 이후 state offset/chunk와 부분 reduction을 명시적으로 분리하고, 모든 state를 정확히 한 번 덮는 검사를 한다. 동일 command buffer에 큰 dispatch를 여러 개 나열한 것만으로 TDR 안전을 주장하지 않는다. 실제 완료 경계를 둔 별도 제출과 GPU 측정이 필요하다. 진단용 CPU readback/분할을 제품 per-frame 경로로 그대로 넣지 않는다.
5. BVH는 primitive/node/vertex 범위와 finite query를 검사하고, 작은 visit slice와 continuation을 설계한다. 예산 소진/누락은 transparent가 아니라 incomplete/unknown이며 sourceId/view/topology가 바뀌면 이전 작업을 사용하지 않는다. Curve는 column별 공유 계산과 정확한 구간별 합/최솟값 reduction으로 나누어 긴 per-cell loop를 제거한다. Pareto는 candidate별 병렬 판정, metric은 candidate/key별 작은 reduction으로 나눌 수 있다. 수학적 목적함수와 source provenance는 바꾸지 않는다.
6. 각 작은 단계의 동등성/완료·자원 수명을 확인한 뒤에만 전체 렌더를 고려한다. 현재는 원인 kernel/시간을 모르므로 full115 재실행의 위험이 해소됐다고 하지 않는다. 드라이버/TDR/보안 설정은 변경하지 않는다. GPU 시간을 CPU wall time으로 대신하지 않는다.

Windows TDR는 GPU 작업의 완료/선점을 기준으로 동작한다. 큰 dispatch의 소프트웨어 loop가 유한해도 안전 시간 보장은 별도다. [Microsoft TDR](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/timeout-detection-and-recovery). Group barrier의 분기 조건은 [Microsoft GroupMemoryBarrierWithGroupSync](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/groupmemorybarrierwithgroupsync)를 참고했다. 이 자료는 현재 장치의 실제 timeout/정확한 실패 kernel을 알려주지 않는다.

## 복구/미로드 shader

`recovery/RECOVERY_FINDINGS115.json`, `END_STATE_RECOVERY115.json`, `NATIVE_GLOBALS_RECOVERY115.json`이 근거다. 마지막 공개 조회05:24:31UTC/PID6288/6000.5.9f1/Edit/GameMap1 clean/컴파일·전환 없음, dirty25이다. 47개 중45개 ExactUTF8, Input22/장치/옵션/시간/pipeline/global74 일치, 남은 command callback0. 직렬화 조회에서 FaceSourceOwner202.asset이 dirty false→true가 됐지만9,357,126B 내용은 동일했다. ClearDirty/저장/백업 덮어쓰기는 없었다. Undo/비직렬화 메모리 완전 복구는 보장하지 않는다.

미로드 CommonSurface329/DeskLivePixelProbe는 디스크 소스·meta GUID·실행 전 보호 hash·선언 shader 이름이 맞는다. CommonSurface329의 Git raw blob 차이는 CRLF 차이이고 보호 원본 bytes는 같다. 새 native compiled object/AssetDatabase 등록은 강제로 load/import하여 확인하지 않았다. `UNLOADED_SHADER_DISK115.json`을 참조한다.
