# 539 — whole-return clothing boundary, local validation

Status: implemented and locally validated on outerwear Body submesh 3 only. Default OFF. This is not an integrated clothing/full-loop pass.

## Algorithm

Input is the projected, opacity-aware, closed vector region in the shared 480x272 logical grid. ClosedRegionDesign539 replaces arbitrary RDP subchords with omission of a whole outward return: identify both returns to a common extremal level, require monotone progress along the other axis, and allow the shortcut only when its entire outward area is at most 1 logical cell squared. Select disjoint parameter intervals deterministically; preserve winding and reject proper crossings. This replaces the approximation stage, not a post-mask filter. The existing exact curve-cell area computation and spatial region selector follow it. Source geometry/UV/depth supplies the interior; downstream masks retain boundary authority.

The one-cell area budget is a design constant in logical-pixel units, not a unique optimum derived from resolution or a reproduction of Feature-Aware 2016. No temporal history, case coordinates, frame exceptions or all-thin-feature removal are used. This outward-return implementation does not claim general hole filling. The nested `rule` strings in the Python WHOLE_CURVES539 diagnostic inherited the old529 "depth<1" wording; that label is stale, while the actual outer rule and C#/Python code use whole-return area <=1. Numerical candidate records and the C# equality checks are unaffected.

## Evidence

Python and actual C# results agree on all 11 stored inputs: projected curves, areas and selected masks (max area difference 0). The eight rotated/subdivided 0.75-by-3-cell normal ends retain their masks. Actual Walk frames 42..51 were captured once as 10 matched full-body pairs: control 527 outerwear ON versus candidate 539 outerwear ON. Same pose/camera/light, skyHour 6.0668816566467285. Frame 43 two-cell spur removed; 44 normal step retained; frame 50 avoids the former RDP notch by quantizing the complete return together. Face/eye RGBA difference 0 in these 10 pairs. Missing/unfilled/outside audits 0 within this scope. Full quality/adoption is not inferred from these counters.

PRIMARY_WALK539.gif: 10 frames, 400x332, 220620 bytes. WebP uses 16/17 ms durations (167 ms total); GIF uses accumulated 10 ms quantization. Full body retained. The short excerpt repeats and does not certify loop closure. Main page displays it at integer scale and labels the historical 533 full loop separately. Browser verification is saved.

Timing: median candidate RenderFrame 343.65 ms, control 351.83 ms; geometry 8.53 ms, area 0.59 ms, selection 10.83 ms, upload 0.37 ms. RenderFrame excludes subsequent PNG/probe writes but includes synchronous readbacks inside the existing core renderer. It is not measured Player FPS or a real-time adoption pass.

Direct final check: Edit, unpaused, not compiling/updating; clothing/opacity/area/whole flags OFF, capture rate 0, runInBackground false, scene clean. User QualitySettings and TimeManager bytes unchanged. No Library retry (prior 403); media remains local.

## Actual parts / next scope

Body has 4 submeshes: 3 outerwear, 1 bottom, 2 shoes, 0 shared skin/hands/inner top/stockings. Face has 7; Hair has 4. Slot 3 is an index, not a count of clothing types. Body0 has no separate material classification for the requested garments and must be labelled a whole-body/hands test until independent evidence exists. Lower/shoes common integration, optional Body0 comparison, product-OFF baseline and full Walk validation remain pending. Face/hair algorithms remain unchanged. Internal colour, gray-face non-reproduction and old head packet cost remain separate issues.
