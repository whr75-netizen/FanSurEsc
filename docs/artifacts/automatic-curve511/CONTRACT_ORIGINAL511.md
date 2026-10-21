#511 — automatic curve input, first vertical experiment

Latest requirement replaces510's manual-authoring premise. Compile a model's
declared Hair part automatically from topology/current evaluated geometry into
persistent closed control rings and original triangle/barycentric anchors.
No model coordinates, chosen strand, primitive range or animation phase enters
the algorithm. Semantic Hair/Face/Eye bindings are required input metadata;
topology cannot prove those meanings or an artist's intended tip importance.
Current adapter supplies these existing parts. Missing meanings remain explicit.

First prototype uses **closed piecewise-linear curves**, not a claimed Bézier
implementation. It supports the currently verified opaque, double-sided Hair
materials and current game-view Walk. Other material/view/clip cases remain
unverified or unsupported, not silently classified as success.

Preparation: model/reference view snapshot → projected triangle cycles, each
oriented CCW → cancel opposite coincident edges with integer winding weights →
exact rational segment arrangement → boundary separating positive winding from
zero → closed rings → one-time curve simplification and small-region design →
persistent source anchors. This regularized vector union is preparation only;
there is no low-resolution source mask. CGAL's Boolean set operation guide is
the reference for regularized polygon-region/arrangement terminology; no CGAL
code/package is installed. The implementation is a bounded local experiment.

The generic preparation profile reuses502's0.1875-logical-cell curve error and
0.14 area/perimeter coefficient. These are declared design parameters, not pure
numerical tolerances. RDP selection occurs once, with topology checks/refinement,
not independently on every animation frame. A component/hole may be omitted or
filled if its area cost is smaller than saved0.14×perimeter; no constraint keeps
all tiny gaps/strands. Geometric tips are candidates, not proven semantic intent.
Record every omitted ring and geometric error for actual design review.

Runtime: current evaluated mesh → barycentric control points → existing head
projection → continuous closed curve/cell areas → unchanged joint SelectRegions
→ closed cell boundary and common mask → current source-triangle packet →
existing Raw/Native/layer/eye/final Draw/Gate. Bypass both unconditional source
Union and505 Build on this path. Static triangle indices/UV and source signatures
are cached; current positions/projections and cell search bins update per pose.
This is not a stationary pose/image cache. Current physical occlusion and
original UV/color/depth ownership remain; same role is not same surface.

Canonical2D:480×272, origin top-left, x right/y down,1unit per final logical
cell, native attachments2×; no new resampling or root/camera/bone snapping.
Control anchor world=Σbary_i*TransformPoint(current vertex_i); then use the same
Full319View335.Project/effective projection as the other head passes. UV is from
the same original primitive. Pose and projection are read from one frame state.

Preparation predicates: exact closed arrangement on overlap/touch/hole/duplicate
fixtures; no open ring; anchored barycentrics finite/sum1; projected anchor error
<=0.0005 logical cell (small float projection allowance, separate from design
curve error); source topology/UV/bind signature matches; no unsupported alpha.
Reject an invalid input rather than changing coordinates or relaxing tolerances.

Runtime predicates: current curve validity, bounded donor support, common mask
authority in every pass (outside violations0), correct primitive/UV/depth/owner,
same pose/light paired captures, color/eye/proportion/occlusion review, actual
short Walk continuity and isolated-pop/staircase/internal-shading review.
505 mask equality is not the design criterion. Keep the.8750 neighbour-cost
event separate; changing representation does not prove its resolution.

First runtime scope: existing representative adjacent Walk interval plus the
neighbour event when the initial path is ready. No whole-loop restart first.
Report preparation and runtime/renderer cost separately. DefaultOFF, restore
input/Animator/clock/hooks and preserve348/508/user changes. Preserve a local
full-body GIF; no Library403 retry. No auto-adoption or complete-project claim.
