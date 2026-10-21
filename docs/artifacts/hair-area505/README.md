# Visible hair area505 — accuracy reference, OFF, not realtime

This is a diagnostic reference input for the existing closed-region selector.
It is not an adopted realtime renderer. Both `HeadRegion502.Enabled` and
`UseVisibleArea505` default to false; setting only the former retains504 for
same-pose comparisons. The active44d13c0 fix and current user settings remain.

## Region and area contract

On the existing head-local480×272 top-left grid, clip each deformed projected
hair triangle to a logical cell. Remove portions covered by a nearer non-hair
source triangle under the current source pass's culling, alpha and depth rules.
Equal-depth hair wins because it is drawn last. Union the remaining polygons;
overlapping or hidden hair triangles contribute area once. Integrate that union
by exact piecewise-linear scanline events in double arithmetic. No8x raster,
sample-count increase, RDP fit, ROI hull, morphology or time filter chooses A.

Formally, `A(C)=area(C ∩ V_hair)`, where `V_hair` is the projected coverage for
which a hair triangle survives all nearer coverage-positive non-hair triangles.
Self-overlap is a union. Source material alpha uncertainty is retained as lower
and upper visible domains. Current textures have one mip, bilinear/repeat
sampling, identity UV transforms, zero UV animation and alpha factor1. Runtime
guards reject unverified conditions; alpha texel extrema bound each polygon.
The selector runs on both area bounds when they differ and refuses an uncertain
selection. It does not silently call an original-source fallback a success.

The unchanged binary energy is area mismatch plus.14 times8-neighbour boundary
length, orthogonal/diagonal weights.58578644/.29289322. The selected cell-edge
loops remain the final coverage authority. RDP/source8 loops are diagnostics.
UV/depth donors, material colours, eyes, outlines and time logic are unchanged.
This is a geometric input precision fix, not a complete pixel-art design rule.

## Evidence and correction

The first subtraction implementation failed an independent half-occlusion
fixture(.875 instead of.5). Clipping had emitted duplicate vertices; a
zero-length remove edge then appended an uncut polygon. The corrected clip
canonicalizes exact duplicate endpoints and subtraction skips zero-length edges.
All8 fixtures now pass: duplicate/overlap union, half/front/behind/tied depth,
depth crossing, transparent front and unresolved alpha bounds. Earlier
`Bilinear81` visibility results are superseded, not the final reference.

Direct compressed-texture GPU readback also emitted unsupported-format errors.
The reference uses the already verified temporary linear RT copy/readback and
restores/releases its temporary resources. Alpha/material data alone is cached;
deformed geometry is recomputed every pose. The separate disjoint-union cost
helper82242 produced no result and was interrupted through its own session.
It is not in the product. Unity and other processes were not terminated.

After correction,81 saved full-geometry poses have identical lower/upper selected
masks. The saved full geometry is from499; its measured drift against33 current
poses is at most.00013733cell, so it is not called bit-identical input.
Two whole-mask reversal observations remain; they are not proven error counts.

Actual22 paired Walk poses in7 adjacent intervals compare504 against505 within
the same execution. Both masks match their saved predictions in all22 pairs.
Raw/hair/final/Native boundary violations, packet primitive mismatches, body
colour differences and same-surface visible skin colour differences are0.
Native packet depth difference is at most1.90735e-6. All22 deformed hair geometry
fingerprints differ; this is animated input, not a frozen-pose cache.

Seven targeted temporal episodes lose their unnecessary return. Cases at.8750
and.9375 become one-way movement, not a requirement for zero pixel changes.
The separate neighbour-cost event at(224,58) changes indirectly under the new
area inputs; its general design/cause is still unresolved. The current game
angle exposes skin but no eye feature roles, so frontal eyes remain untested.
The original texture/eye geometry is unchanged. Same-run lighting matches;
brightness against earlier runs is not asserted identical or retuned.

## Runtime cost and minimum next path

This is **not realtime**. Across the22 actual pairs, median505 geometry area
calculation is4247ms. Median renderer call wall time is504:469ms /505:5048ms;
capture readbacks are outside those call timings. These are Editor diagnostics,
not player FPS. The pose is actually recomputed at every captured animation step.

A one-pose offline operation profile of the same corrected core, with the
runtime's conservative depth/bbox candidate rejects, measures:

| Cost item | Measured count/time |
|---|---:|
| Cell-bin triangle assignments |51,374|
| Front-occlusion candidate pairs after broad rejects |136,803|
| Polygon half-plane clip calls |2,355,912|
| Union event edge-pair comparisons |21,710,000|
| Union stage / total offline compute |1453.5ms /1688.9ms (~86%)|

The instrumented scalar areas match the uninstrumented reference exactly in that
pose. These stage times are offline CoreCLR measurements, not a runtime Mono
stage profile. The source still creates per-frame projected triangle objects,
cell-bin lists, clipped polygon lists, subtraction fragments, union edges/levels
and scanline interval lists. This causes allocation pressure; allocated bytes
have not been measured and are not invented here. Alpha bytes are cached once.

The smallest proposed next step is confined to `Union`: deduplicate exactly
identical event segments and reject disjoint XY edge bounding intervals before
intersection solving. Keep original polygon intervals and the integral. Duplicate
segments add no new event; disjoint boxes cannot intersect, so this reduces
candidates without changing the area objective or region ownership. No speedup
has yet been measured. Use these fixtures and81 reference inputs as the oracle.
Reusing the already computed **same-frame** projected hair data and immutable
topology/material inputs can separately reduce allocations. Vertices, depth and
spatial candidates must still update with animation. Such reuse alone cannot
remove the dominant union cost. No new optimization has been implemented.

## Deliverables and limits

`Current472/Walk505/WALK505_FULLBODY_BEFORE_AFTER.gif`:22 paired full-body frames,
7 labelled adjacent intervals, explicit time jumps between groups,80ms slow
inspection. Native spatial pixels are retained; original PNG/float buffers stay
local. `validation.json` contains paths, bytes, SHA256, detailed results and
restoration. The review PNG is an integer enlargement for diagnosis.

Play/input/Animator Idle speed1/automatic clock/captureDelta0/single PostView366
hook and all experiment gatesOFF were directly read back. User Quality/Time
hashes are unchanged. Library403 was not retried. Full runtime loop, general
temporal quality, cluster/stair/light-shadow design, other clips/cameras,
grounding, builds and target-player performance are not validated. The numerical
degeneracy guards are not a formal global error proof. No whole-project completion
or visual adoption is claimed.
