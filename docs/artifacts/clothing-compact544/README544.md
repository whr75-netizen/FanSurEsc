# 544: same-output cut optimisation

543 elbow fix remains intact. The old540 Clothes mode remains available. `EValidation/Boundary540/Clothes543 (validated spans)` enables the same shape with this faster selector. All trials and product defaults are OFF after tests; no scene/prefab/settings are saved.

The new path analytically removes strictly fixed cells from the existing graph. With the existing .14 boundary weight, the maximum eight-neighbour boundary change is .4920614, less than a unit unary change. Non-grouped A=0 cells are therefore false; non-grouped full A=1 interior cells true. Group members remain variables. Fixed/free edges become terminal costs and fixed/fixed terms become an irrelevant constant. The remaining graph uses the existing solver. Source curves, areas, groups, weights, colors, UV, depth and time are unchanged. This is not a frozen-pose cache, sample approximation or extra rendering layer.

Stored81poses x3parts (243 masks) and8 thin ends are exact. Actual81poses with alternating measured pair order also have exact final RGBA, UV, metadata/ownership, masks and world output between the prepared reference and compact selector. Every pose retains a reference self-control; its native8-bit display also matches exactly. No animation frame is removed. See PERFORMANCE544.json and ACTUAL_EQUIVALENCE544.csv.

| Milliseconds | Reference median / p95 | Compact median / p95 |
|---|---:|---:|
| Selection, including same span generation |22.30 /42.01|2.15 /2.89|
| All clothing boundary stages |43.24 /94.37|23.06 /35.93|
| Core RenderFrame |347.00 /747.17|323.36 /725.87|

Actual geometry remains17.74/17.76ms median. Cold model preprocessing is excluded by existing gameplay startup plus3 warmup pairs. Both modes use real changing Walk poses at480x272 logical/native960x544. Extra diagnostic readbacks,8-bit conversion, PNG and file writes are outside timers. Existing runtime readbacks remain inside RenderFrame, so these are not PlayerFPS or GPU-only timings. The earlier54042.48ms is context only; the improvement uses paired current-run timings. Stage timing noise/GC is reflected in p95, not hidden.

Allocation **bytes per frame are unavailable**: Mono GC.GetAllocatedBytesForCurrentThread returned0 even after a real1MB positive probe. Do not interpret this as zero allocation. As a separate structural metric, actual65 outerwear reduces graph nodes1980→169 and allocated edge objects38524→3412; those are code-derived object counts, not measured bytes or retained heap. TIMER_OVERHEAD544.json records the clock-call control.

First strict-float gate Runtime544 stopped at pose2 (272 RGBA/70 UV/12 world differences; masks/meta equal). Those first failing buffers were not stored, so their exact original pixels are not retrospectively asserted. A bounded independent same-pose control retained all inputs/buffers: unchanged reference→reference itself differed262/70/24 by at most7.45e-9/1.49e-8/1.86e-9, nativePNG8 difference0; referenceB→compact→referenceC were then float-identical. Mesh/camera hashes and pose/clock inputs matched. The arithmetic origin of that original reference-repeat drift is not claimed solved.

The corrected full gate retains reference self-repeat on **every** pose. It requires exact masks/meta/native8-bit output; any candidate float not actually observed in its same-pose references is rejected without epsilon. Final compact/reference raw float differences were0 across81poses. Reference self-drift remains in the CSV (21495 RGBA/5237 UV/1720 world observations, all native8-bit differences0). This is a verification correction, not a new product filter or a deletion of animation frames.

The primary full-body GIF remains the verified543 feature comparison (3095462bytes,81frames1350ms). It is reused honestly as the same functional output, not relabeled as a new544 video. ACTUAL_COMPARE544.png is the new same-pose optimisation pair. These executions have different scene hours; cross-run backgrounds are not claimed identical. Library403 was not retried or bypassed.

Still open: overall real-time performance, remaining geometry/runtime readback costs, frame allocation measurement, Body0 face ownership and hand scope, gray-face user report (not reproduced/resolved), earlier internal shading and hair issues. 348 remains active; hair511/source-ray513 trial scope was not expanded. This unit does not complete the whole project.
