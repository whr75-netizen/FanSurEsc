# Disabled original-curve hair source experiment494

The prior RDP chord choice changed the original ribbon shape. A near-edge-on triangle also falsely occluded its own source packet.
This revision takes positions from the actual60-section curve, uses RDP only for directional spans, samples real grid intersections,
and preserves only the two physical UV caps as endpoints. Exact source triangle identity prevents numerical self-occlusion; other surfaces remain depth tested.

The selected source cell and original triangle/barycentric/world/UV/depth packet are authored together in the existing source alternative.
There is no extra closing/dilation/history/colour layer, coordinate condition, phase rule or depth epsilon increase.

Four actual same-pose Walk pairs0.30..0.3375 passed this bounded failure case. The strand stays connected, its5-cell hole is preserved,
and the former split/2-cell indentation transition is absent. Default OFF; appearance is not adopted. Full-loop/other hair/clip/view/performance remain unverified.
Current active product fix44d13c0 remains separate. The user's project is not complete.

`validation.json` records provenance, exact failure, packet/occlusion checks, controls restoration and deliverable paths.
Shared-workspace diagnostics: `Current472/CapturePairs494B.cs`, `Pairs494B/`, `Probe494/`, `Geometry494/`.
The new native full-body GIF is same-execution original centre source versus494; old492 images are separate executions and are not used as an exact RGB baseline.
