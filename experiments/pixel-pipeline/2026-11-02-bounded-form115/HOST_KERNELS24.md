# 113 → Direct24 정적 커널 비교

소스/호출 폐쇄만 비교했다. 후보 host 없음, Assets/import/컴파일/GPU0. 현행 C#을 실행하면 원래113 shader가 로드된다.

| 커널 | 코드·호출 폐쇄 변화 | 기존/예정 dispatch | 메모리·반복 한계 |
|---|---|---|---|
| ResolveCurve107 | 동일; 바인딩 이름·형 동일 | Not called in successful113 Draw (literal ApplyCurve106 selected) | Unchanged declarations; Dead on audited path, but retained shader entrypoint |
| ApplyCurve106 | 동일; 바인딩 이름·형 동일 | 1 control dispatch:ceil(18/8),ceil(8/8) | Original legacy106 debug output/curves; Curve loop and source sampling unchanged; control-only work not needed in first probe |
| ComposeForward102 | 동일; 바인딩 이름·형 동일 | Twice for original102 and legacy106 controls;ceil(ROI/8) | Same canvas/hair and four ROI RTs; 16 fine samples and legacy select; control-only work not required in new first probe |
| PackWorld98 | 동일; 바인딩 이름·형 동일 | Not called by Forward113 path; method exists in WholeEye107 | Unchanged world-underlay resources; Dead on audited path; no claim physically absent from asset |
| PackPart | 동일; 바인딩 이름·형 동일 | 12 dispatches:4 parts ×3 engines; ceil(w/8),ceil(h/8) | Native dimensions72×32, dense/carrier144×64;20 float4 planes/engine; Constant5 fields; per-thread O(1) |
| Refit | 동일; 바인딩 이름·형 동일 | 3 engines × each recorded BVH level; ceil(levelCount/64) | Nodes59083, depth15 in actual113; boxes2×nodes; indices checked by original constructor; One node/thread per level; full topology unchanged |
| Query | 동일; 바인딩 이름·형 동일 | 3 dispatches; total82944 logical query rays | Same triangles29542/vertices20459/materials15/BVH59083 in saved inputs; while(sp>0), stack32; no explicit visit-budget check. Acyclic-tree proof only; worst59083 node visits/ray |
| Select | 동일; 바인딩 이름·형 동일 | 3 dispatches; each ceil((w/4)/8),ceil((h/4)/8) | Same input layers/visibility, canonical outputs n/16; 16 sub-samples,3 parts; private weight48/L4/U4 arrays retained |
| Compose | 동일; 바인딩 이름·형 동일 | Not called by Forward113 path; method exists in WholeEye107 | Unchanged legacy composition resources; Dead on audited path; no claim physically absent from asset |
| PrepareCells113 | 동일; 바인딩 이름·형 동일 | 3×1 groups ×64 threads;144 in-bounds cells | Cells512×7×16, tags512×16, source144×64, keys20, curves846; 64 samples/cell; SourceKey scan≤32; curve loops≤1024. Source limits unchanged |
| GatherEye113 | 동일; 바인딩 이름·형 동일 | 2×1×1, numthreads1 | Frame64×16, points48×16, grid≤512; same caches; RawConnected seen16; up to32 active scope calls ×512 passes ×512 cells, plus24-point adjacency |
| BuildSubsets113 | 본문 및 폐쇄 변경; 바인딩 이름·형 동일 | 64×4×1, numthreads64 =16384 nominal threads | Subsets16384×32; head np≤24/ni,nw≤12/ni+nw≤21; b.z now direct float bits; Per valid subset≤24 point scans +8×24×24 connectivity checks. New≤24 scalar mass additions/subset |
| Enumerate113 | 본문 및 폐쇄 변경; 바인딩 이름·형 동일 | 32768×2×1, numthreads64 =4194304 nominal threads | Groups65536×48; subset indices<16384; same guard/buffer sizes; 64-thread shared reduction,6 barrier rounds; one direct-sum add/valid pair; comparator adds scalar tie check |
| Reduce113 | 본문 동일, Less113 폐쇄 변경; 바인딩 이름·형 동일 | 2×1×1, numthreads64 | Read32768 groups/eye; best2×48; tail.z now direct float bits; 512 serial group merges/thread +6 shared reduction rounds. Body unchanged but Less113 closure changes |
| Write113 | 동일; 바인딩 이름·형 동일 | 3×1 groups ×64 threads;144 in-bounds cells | Read cells/frame/points/best; four144×16 outputs for current grid; ≤24 point lookups/cell; closure unchanged; valid first-write diagnostic entry |
| ComposeWhole113 | 동일; 바인딩 이름·형 동일 | 1 extra capture dispatch:60×34 groups ×64 threads | 480×272 float4 RT; candidate tile/current product77 colour; O(1)/pixel; capture helper then synchronous plane readbacks |
| ComposeRegion113 | 동일; 바인딩 이름·형 동일 | 1 dispatch:ceil(ROI/8) | Same four region output RTs; exposure1024×16; 16 carrier/hair samples; private depth16/known16 retained. New transport and ring policy NOT integrated |
| CarrierQueries113 | 동일; 바인딩 이름·형 동일 | 1 dispatch:ceil(144×64×4/64)=576 groups | Read20 layer planes; write4×9216 query records; O(1)/query; original8x carrier coordinate contract remains |

115 Evaluate/Pareto/interval 기능은 후보에 없다. 113의 나머지 배열/큰 반복은 남아 있으므로 전체 shader가 zero-scratch이거나 현재 GPU가 안전하다는 뜻은 아니다.

관측된113 전체 GPU dispatch/자원은 제품77·URP/world 자체 작업을 포함한 전체 시스템 상한이 아니다. Stage별 작은 검증은 아래 NEXT_GPU_PREFIX24.json 계획이며 아직 host도 작성·실행하지 않았다.
