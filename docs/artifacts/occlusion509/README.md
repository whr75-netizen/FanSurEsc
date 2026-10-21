# Occluder certificate509 — not adopted, removed from runtime

508 was committed first as `909e324`. It remains default OFF, with its original
505 path preserved. This unit tested only an additional early occluder rejection
against508.509 did not establish a Unity speed improvement and was withdrawn.
Its temporary runtime code, Editor observer and generated metas were removed;
the runtime helper is byte-identical to committed508, SHA256
`2aeca448c6742a66219a700ec053b0680e0221a9602ea1eca778a031b8b9043b`.

## Scope and exactness

For each actual cell-clipped hair polygon, bound the coordinates of the original
three occluder-edge clipping steps, including a binary64 interpolation-error
enclosure. Evaluate an outward upper bound on the **same rounded affine depth
plane difference** used by the original subsequent depth clip. Reject only if
the bound is strictly negative everywhere. Equality, uncertainty and unsafe
numeric ranges retain the original path. The conservative box encloses the
computed overlap; it is not reduced to an ideal triangle/cell intersection.

`BOUND_PROOF509.md` states the assumptions and derivation. The coordinate padding
is64×2^-52×M from three floating interpolation steps, not a tuned depth epsilon.
No same-role/same-surface assumption, alpha change, source sampling change,
occlusion disable, cost-function adjustment or temporal filter was added.
Six geometry/alpha/depth fixtures and six certificate/fallback checks passed.

All81 saved varying-pose inputs match508 lower/upper area bits and ambiguity
counts exactly. The unchanged Unity SelectRegions gives zero selection-mask
differences for both bounds across all81 pairs. This establishes the saved-input
scope; it is not a new visual/animation-quality pass.

## Non-instrumented paired measurements

Both modes warm up and pair order alternates. Scope is complete Compute with
loading/saving/comparison outside. No stage timer/counter, recorder, forced GC
or animation-output cache is used.

| Environment and scope |508 reference|508+509 candidate|Paired result|
|---|---:|---:|---|
| .NET10,81 inputs; mean ms|935.942|928.657|42/81 faster; median paired saving1.807ms,0.175%|
| .NET10,input22 repeated5 pairs; median ms|913.220|894.312|3/5 faster; median paired saving33.859ms|
| Unity Mono6.13,input22 repeated5 pairs; median ms|3247.251|3374.203|2/5 faster; median paired saving−355.896ms|

Unity paired savings range−406.670 to518.311ms. Their directions alternate with
execution order: the first call in each measured pair is faster in this sample.
This exposes scheduling/heap/order effects rather than a consistent509 benefit.
The observed median is not asserted as an intrinsic11.79% algorithm regression.
No further repeated benchmark or parameter-tuning loop was started to seek a
positive result. Since a Unity gain was not established, the conditional actual
Walk capture was **not run**, and no509 GIF is claimed.

The .NET allocation API passed its1MiB sentinel. Average allocations over81 pairs
decrease from755,976,942 to746,577,344bytes, about9,399,598bytes(1.24%) per
Compute. Five repeated pairs show the same direction. This limited memory gain
does not establish a real-time speed gain. Mono's sentinel again returns0, so
its allocation-byte metric stays unavailable. Positive live/reserved heap
snapshots in UnityPairs.csv describe observed heap size only, not total churn,
peak or memory attributable solely to Compute.

## Remaining runtime cost structure

Even508's measured representative Compute remains around3.3seconds, and its
actual renderer call is around4seconds. .NET and Unity scopes, independent
runs and different call populations must not be mixed to imply further gains.
The count-based claim that21.71million edge pairs were the principal time
bottleneck remains withdrawn.509 did not re-profile or identify a new dominant
stage, so no new operation-count claim replaces that correction.

The code still reconstructs cell-clipped triangle fragments, processes their
occluders, and constructs/integrates lower/upper polygon unions per cell on each
pose.508 avoids inactive polygons inside Length but retains this representation
and all original edge events/pairs. The measurement's roughly0.75GB managed
allocation per standalone Compute demonstrates substantial reconstruction work;
this is not a value measured for Mono.

Further small candidate filters cannot be assumed to close a seconds-scale
real-time gap. The next architectural review should examine a canonical curve-
based designed region updated from each changing pose, then boundary-cell
selection instead of reconstructing all mesh detail. It must retain face/hair/
eye ownership and valid occlusion.505 remains a physical/source comparison
oracle; exact505 area or masks at every cell are not a design target. Authored
hair masses may merge or omit insignificant strands/gaps under an explicit
pixel-art contract.
This is a proposed structural review, **not an implemented alternative or a
performance promise**. Reusing an unchanging animation pose, dropping precision
or adding history/color filters would not satisfy that contract. No structural
redesign or next optimization was implemented here.

## End state and deliverables

The10 measured callbacks completed and unsubscribed; no recorder existed.
Before removal, direct readback proved both508/509 flagsOFF and original Idle,
input, automatic clock, single PostView366 hook, captureDelta0 and ProfilerOFF.
After restoring508, compilation and the original Play state were checked again.
Historical Console entries remain; no new related error is accepted as success.
Quality/Time user hashes and44d13c0 are preserved; no source outside the owned
509 experiment was reverted. The rejected code is preserved only as a diff and
standalone comparison source, outside Assets.

The existing508 full-body same-execution GIF remains locally preserved at
`C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Walk508/WALK508_FULLBODY_BEFORE_AFTER.gif`
(70,064bytes). It compares505/508, **not509**. Original PNGs/float buffers remain.
No Library403 retry, new full loop, eye/shape/time-cost redesign, default
activation or claim of complete pixel-pop resolution was made.

`validation.json`, `paired81.csv`, `UnityPairs.csv`, `PairArea509.cs`,
`REJECTED_CANDIDATE509.diff` and `BOUND_PROOF509.md` retain this non-adopted unit.
