# Active y-interval polygons508 — default OFF

This unit changes only the repeated polygon candidates of `Union → Length`.
The original505 Union body remains behind the false default gate
`HeadArea505.UseActivePolygons508`. The exact original source is also preserved
as `Current472/Area508/Reference505.cs`, SHA256
`c24b4e664bd713b35ba4107707c587adc0575b54c159a459d82b3fe736746dd7`.
Occlusion, alpha bounds, selection costs, colors, camera and time handling were
not optimized or redesigned. Rejected506 remains rejected;507 measurements and
the correction of its count-based bottleneck claim remain valid.

## Equivalent operation

Within each current Union, collect each finite polygon's minY/maxY during the
existing edge traversal. Preserve every original vertex event, edge-pair
intersection, event sort and integration midpoint. Sort separate start/end
indices by their y bound, with original polygon index breaking ties. At each
nontrivial midpoint y, remove intervals with maxY<=y and insert intervals with
minY<=y<maxY into an index-sorted active list. `Length508` visits this list in
the original polygon order and uses the original edge crossing formula,
span insertion order, comparison, merge arithmetic and integral accumulation.

For the existing half-open crossing predicate, a polygon outside this interval
cannot contribute any crossing. Removing it therefore removes no span. Equal
midpoint/bound values retain the same half-open behavior, including rounded
midpoints at endpoints. Empty/zero-height polygons contribute no span. The
candidate set is rebuilt from the current clipped polygons of every Union;
there is no cross-frame or stationary-animation cache, geometry approximation,
new sample grid, depth adjustment or new optimization in the occlusion path.

## Saved-input and timing evidence

Eight empty/degenerate/disjoint/touching/equal-bound/thin-interval fixtures
matched original double area bits. All81 distinct saved deformed Walk inputs
matched both float area bounds bit-for-bit, including ambiguity counts.
The unchanged Unity `HeadRegion502.SelectRegions` then produced zero mask
differences for both bounds across all81 pairs.

Measurements time complete Compute calls without stage timers, counters,
profiler recorders or forced GC. Loading, saving and comparison are outside.
Both modes warm up, pair order alternates, and the reference is preserved.

| Environment and scope | Reference | Candidate | Paired result |
|---|---:|---:|---|
| .NET10,81 different saved inputs; mean ms |1207.351|1047.482|78/81 faster; median saving13.49%|
| .NET10,input22 repeated5 pairs; median ms |1084.657|938.664|5/5 faster; median paired saving132.334ms,12.41%|
| Unity Mono6.13,input22 repeated5 pairs; median ms |4519.908|3278.350|5/5 faster; median paired saving1538.343ms,33.97%|

These are paired differences/ratios, not differences of aggregate medians.
Unity paired savings range763.439–1806.212ms,18.51–38.08%. The5-pair result is
limited evidence in this Editor and includes scheduling/heap variation, not a
target-player FPS benchmark or a real-time claim. The candidate still costs
roughly3.3seconds per representative Compute. No second optimization was added.

The standalone .NET allocation API passed a1MiB allocation sentinel:1,048,600
bytes observed. Across81 pairs, measured managed allocation averages
754,039,739bytes reference and755,976,948 candidate: about1,937,208bytes more
per call(0.257%). This is a speed improvement with additional bookkeeping
allocation, not a memory reduction. Five repeated pairs give the same direction.
Unity Mono's same sentinel returns0, so its allocation-byte metric is
**unavailable, never zero allocation**. Unity's positive live/reserved Mono
heap snapshots are retained as observations, not allocation, peak or memory
attributable solely to Compute. Gen0 collection counts total20 reference and19
candidate over5 calls each; the non-generational Mono fields are not summed.

## Actual Walk equivalence

One short real animation excerpt contains three adjacent Walk poses at phases
0.26250255,0.27500260,0.28750265. Every pair has identical bones and lighting;
all three saved deformed hair geometries are distinct. Both sides use the502/505
region path; the right side additionally enables only508. This comparison does
not claim a new full-loop or temporal/art-quality pass.

- Both masks and the saved-input predicted selection match exactly.
- Final full-screen PNG differences:0 pixels across all3 pairs.
- Owner, Meta, Raw coverage/role/depth, hair layer, hair UV, prepared ownership
  and Native buffers match; boundary violations and surface-packet mismatch:0.
- GPU float buffers are **not all bit-identical**: first pose has346 finalRGB
  values different(max2.98023224e-8,2ULP),55 preparedUV and56 rawUV values
  different(max1.49011612e-8,up to19ULP); third pose has4 UV values in each
  corresponding buffer different(up to3ULP). Primitive/owner channels and
  alpha do not differ. Cause of these numerical render differences is not
  isolated here; no normalization, epsilon patch or hidden correction is used.
  Original float buffers and PNGs remain locally available.

The3-pose actual renderer-call median is4912.873ms reference versus4004.191ms
candidate, with Compute medians4108.148ms versus3303.040ms. These calls exclude
capture readback and have a different scope from the stored-input Compute
benchmark. They are supplementary observations, not extra repeated benchmarks.

Full-body native-scale GIF:
`C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Walk508/WALK508_FULLBODY_BEFORE_AFTER.gif`
(70,064bytes). Same-execution left505/right508,3 time-ordered frames,80ms
inspection display per frame from1/60s capture steps. Only empty surrounding
space is cropped; no interpolation or spatial resampling. A common128-color
presentation palette is used; original960×544 PNGs/buffers remain unchanged.

## Restoration and limits

The measurement callback is removed and its CSV closed. It used no recorder.
Final direct readback confirms Play true, unpaused, input enabled, Animator
Idle speed1/Locomotion0, captureDelta0, automatic clock true, one PostView366
hook, all491/502/505/508 flagsOFF, not compiling, global Profiler false.
Diagnostic caches are released. Console has the same16 historical entries
as the import baseline and no new delta. User Quality/Time settings hashes and
44d13c0 are preserved. Refresh timed out during reload; it was not repeated.
The existing approved host relay/project-path recovery resumed the same Editor.

The feature remains default OFF. It is a validated local cost reduction of an
accuracy-reference experiment, not real-time adoption, pixel-pop/art-design
improvement, neighbour-cost resolution, eye/front-view validation or completion
of the character project. No new full loop or Library upload was attempted.

`validation.json`, `paired81.csv`, `UnityPairs.csv` and standalone
`PairArea508.cs` preserve the measurements and reproduction inputs. Editor-only
`Editor/Profile508/AreaBench508.cs` is explicit-start and refuses to overwrite
the completed run. Runtime candidate code is confined to `Runtime/HeadArea505.cs`.
