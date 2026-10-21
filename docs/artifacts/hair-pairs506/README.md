# Spatial union candidates506 — rejected, comparison artifact only

The experiment changed only Union candidate enumeration and retained505 during
testing. It is rejected because actual runtime gain was not established and
allocation increased. The runtime helper is now restored byte-for-byte to505
(SHA256 c24b4e664bd713b35ba4107707c587adc0575b54c159a459d82b3fe736746dd7).
No506 branch remains in runtime. The tested source survives only as
`REJECTED_CANDIDATE506.diff`, outside Assets and compilation. The505 reference
itself remains defaultOFF and is not realtime.

## Exact contract

Keep every clipped visible polygon, vertex ordinate and original edge. Sort a
temporary list of edge indices by minimum y, with original-index tie breaks.
Stop scanning later indices when their minimum y reaches the current maximum y;
the original interior-y test cannot accept an intersection there. Reject pairs
with disjoint x intervals before solving the line equations. These local edge
bounds only reject impossible pair candidates; the505 region remains authoritative.

Solve each surviving pair in original index order with the exact505 arithmetic
and numerical guards. Sort/integrate the same event ordinates against the same
polygons. No edge deduplication, sampling, triangle/depth/alpha change, geometry
history, frozen-pose cache, time filter, selector-cost change or new render layer
is included.

##81 saved-input paired comparison

Every pose loads its current deformed geometry once, then runs both methods.
Reference/optimized execution order alternates by pose to reduce ordering bias.
All81 deformed geometry fingerprints differ. On both alpha-area bounds:

- Float area bit differences0; maximum numeric area difference0.
- Unchanged selector mask differences0 across all81 pairs.
- Polygon clip/front-occlusion operation counts and raw potential pairs match.
- Existing8 geometry/occlusion/alpha fixtures pass in both modes;4 independent
  disjoint/contact/reversed-edge candidate fixtures also pass in Unity.

| Offline CoreCLR metric |505 reference |506 candidate |
|---|---:|---:|
| Compute median |1120.887ms |1040.553ms|
| Union median |931.121ms |844.293ms|
| Line-pair tests, median |21,368,608 |3,105,395|
| Managed allocation median |741.740MB |742.551MB|

Across paired totals, line tests decrease84.14%, but compute time decreases only
8.09%. Median paired speedup is1.082×. Y-overlap scan iterations have median
7,117,463, distinct from the3,105,395 surviving line-pair tests. The temporary
ordering array/closure increases allocation by an average814,400bytes per pose.
These bytes are allocated within synchronous Compute on the current managed
thread; they are not peak/retained RAM or GPU memory. Input/material loading and
comparison lie outside that measurement. Instrumentation is shared by both modes.

The first isolated cold pose gave a much larger time difference; the81-input
paired result supersedes that as the performance summary.

## Actual minimal Walk comparison

Three actual adjacent poses(.2625/.2750/.2875) use the same pose, camera and light
for505/506. All3 deformed geometry hashes differ. Masks and saved predictions
match; PNG pixel differences, Raw/hair/final/Native boundary violations, packet
mismatches and body-colour differences are0. This verifies output preservation,
not a new animation-quality improvement. No extra full-loop capture was made.

Actual area-compute medians are5054173.997ms /5064217.987ms. Renderer-call medians
are5054939.365ms /5064929.321ms. Three Editor samples do not establish a runtime
speedup, and both remain unusable for realtime. Calls exclude capture readbacks;
target-player FPS and runtime memory have not been benchmarked.

The final pose has53 RawUV float differences(max1.49e-8, up to7ULP), propagated
to53 prepared UV values and387 final RGB values(max3.73e-9, up to2ULP). Earliest
observed difference is RawUV at hair roles12/13/14. Mask, owner, primitive, depth,
Native and independent hair-layer UV match. Source/candidate8-bit PNGs match
exactly. The underlying tiny rendering/rounding cause was not isolated; the
record does not claim every GPU float buffer is bit-identical. No corrective
filter or threshold was added to hide it.

## Remaining cost

A separate instrumented candidate pose spends667.9ms of1018.3ms in221,498 calls
to `Length`(~65.6% of compute, ~81.9% of Union). This unchanged routine rescans
polygon edges, creates span lists and sorts/merges spans for every integration
interval. These calls remain identical in count. Clip/subtraction work and heavy
managed allocation are also unchanged. The one-pose stage measurements include
instrumentation/JIT effects and are not interpreted as a reference-to-candidate
speedup. They identify why pruning line tests alone has limited effect.

No second optimization was implemented. The neighbour-cost event, temporal
design, eyes/front-view and existing remaining505 observations stay unresolved.
The original505 method is preserved as the correctness oracle for later work.

## Handoff

`paired81.csv` stores all81 per-pose counts, times, allocation and equivalence
results. `validation.json` records source/input hashes, local outputs, restoration
and limits. The local full-body GIF is3 paired actual frames,80ms slow inspection,
native spatial pixels and an explicit repeating-excerpt label. Original PNG and
float buffers remain local. Library403 was not retried.

Play/input/Animator Idle speed1/automatic clock/captureDelta0/single PostView366
hook and all experiment gatesOFF were directly read back; diagnostic caches were
released. User settings and44d13c0/42cb52b are preserved. No default activation,
new rendering structure, scene/model/eye edits or project-completion claim.

The statement that21.71million pair tests constituted the main time bottleneck
is withdrawn: it was inferred from count, while84.14% fewer tests yielded only
8.09% offline time reduction and no established runtime gain. A new, separate
measurement unit will time actual stages; no further optimization is included.
