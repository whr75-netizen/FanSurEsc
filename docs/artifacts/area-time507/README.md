#505 area time decomposition507 — observation only

Checkpoint `790e724` rejected506 and restored the runtime helper exactly to505.
The count-based statement that21.71million edge pairs were the main time
bottleneck is withdrawn. No new optimization, rendering patch or capture was
made in this unit. Two explicit-start **Editor-only** observer scripts measure
stored data; they have no automatic startup or production/render connection.

## Scope and observer cost

Unity reports `Mono6.13.0 (Visual Studio built mono)`. The representative input
is `Loop499/022.allmesh`, phase1.275001. After original/instrumented warmups,
each mode executes5 times with rotating order,15 calls total:

| Mode | What runs | Median Compute ms | Range ms |
|---|---|---:|---:|
| A | Original505, no per-call recorder |4403.167 |4033.523–4509.123|
| B | Original505 plus GC recorders |4788.396 |4409.647–4953.348|
| C | Instrumented equivalent copy plus GC recorders |4627.959 |4582.255–4948.015|

All15 area outputs match the warmed original **bit-for-bit**. These measure only
`HeadArea505.Compute`/its equivalent copy. Input/material loading(386.946ms once),
runtime projection/build, renderer calls and image readback are outside. Do not
combine these numbers with earlier5-second renderer timings as if their scopes
were interchangeable. One fixed input was intentionally repeated for measurement;
no animation output or geometry cache was added to runtime.

Medians from different calls must not be subtracted as paired overhead. Paired
per-repeat differences give B−A median385.229ms(range4.783–669.996), C−B
median114.054ms(range−353.162–438.846), and C−A median450.178ms(range112.082–814.970),
about10.89% at the median paired ratio. Heap/scheduling/JIT variation is included.
The non-monotonic aggregate medians are not evidence of negative instrumentation
cost. Empty Begin/End calibration estimates45.949ms for970859 timer pairs; that
is only an estimate. No ad hoc subtraction is applied to raw stage durations.
A common low-frequency GC window recorder is present in all measured modes;
its own cost was not separately calibrated.

## Measured stage durations

These are **mode C raw inclusive durations**, not an exact decomposition of
the uninstrumented total. `STAGE_TABLE507.md` retains the full hierarchy.

| Section | Median ms | Calls | Relation |
|---|---:|---:|---|
| Span construction |2185.539 |221498 |Within integration|
| Span sorting |352.996 |221498 |Within integration|
| Span merge |105.355 |221498 |Within integration|
| Pair intersections |549.182 |1232 |Within Union|
| Event sorting |80.879 |1232 |Within Union|
| Union edge/event setup |37.332 |1232 |Within Union|
| Occlusion processing |1196.215 |28921 |Outside Union; includes next3 rows|
| Overlap/depth clipping |201.723 |136803 |Within occlusion|
| Alpha bounds |50.105 |50214 |Within occlusion|
| Fragment subtraction |876.444 |49773 |Within occlusion|
| Hair/cell clipping |76.704 |34493 |Outside occlusion/Union|
| Spatial binning |2.668 |1 |Outside other sections|

Do not add parent rows and their children. The JSON also derives mutually
exclusive residual sections, which sum to each measured call. Every one of
the5 instrumented calls has span construction much larger than pair testing.
In this measured regime, the main repeated work is polygon/edge rescanning and
span construction; fragment subtraction is another substantial cost. Pair count
alone did not identify the dominant time cost. Observer effects limit the exact
uninstrumented attribution, so the raw stage values are not relabelled as such.

`Length` is called221498 times. Each call loops over **all** visible clipped
polygons and their edges, computes horizontal intersections, creates a span list,
sorts it and merges it. It is repeated for each nontrivial event interval in each
cell's lower/upper union. Occlusion repeats for each clipped hair triangle and
each binned non-hair candidate, then performs overlap/depth clipping, alpha tests
and repeated convex-fragment splitting. The exact calls and source are preserved.

## Allocation and GC

`GC.GetAllocatedBytesForCurrentThread` returned0 in every call in this Mono
environment. This is **measurement unavailable**, not zero allocation. No byte
estimate is imported from the earlier CoreCLR experiment. GC.MaxGeneration=0;
the three generation fields returned the same count and must not be summed.

Per-call profiler markers are collected only on the current thread and summed
for the call's frame, then stopped/disposed. Across10 recorded calls:

- GC.Alloc recorded-marker median165.793ms,6,494,915 events.
- GC.Collect recorded-marker median78.827ms,8 events(median); observed collection
  count was4 per call under the non-generational API.
- GC incremental marker had no events inside Compute.

These are inclusive profiler-marker times. Allocation/collection markers may
overlap algorithm stages or each other; they are not extra time to add to the
table and are not a guaranteed isolated allocator-only duration. The whole
diagnostic window records1562.520ms GC.Collect plus0.0028ms incremental marker
time. It includes A calls and between-call Editor work, so no exact deferred-GC
attribution is inferred. The [Unity recorder API example](https://docs.unity3d.com/6000.2/Documentation/ScriptReference/Unity.Profiling.ProfilerRecorderOptions.SumAllSamplesInFrame.html)
supports current-thread scoped sample aggregation; actual marker names/units
were discovered in this editor and retained in the evidence.

## Equivalent candidate paths — proposals only

1. **Span candidates within one current Union.** A polygon outside the queried
   y interval cannot contribute a crossing. Maintain active polygon indices
   across the existing event intervals, keeping original polygon order and edge
   arithmetic, midpoint/event list, insertion and sort/merge behavior. This avoids
   asking inactive polygons for crossings repeatedly. The active set must be
   rebuilt from each pose's actual clipped polygons; it is not a temporal cache.
   The actual candidate reduction and speed benefit are not yet measured.
2. **Earlier occlusion rejection by an affine depth bound.** With the verified
   orthographic projection, D(p)=z_hair(p)−z_occluder(p) is affine. The true overlap
   lies within the intersection of the cell and both projected bounds. A certified
   upper bound of D on that rectangle is determined by its four corners. If the
   bound is strictly negative, that triangle cannot be nearer anywhere and need
   not undergo overlap/alpha/subtraction. Preserve the original path for uncertain
   or equal cases, including a justified floating-rounding bound. No arbitrary
   depth epsilon, merged role/surface assumption or shape approximation is allowed.

These inclusion arguments describe mathematically equivalent ways to narrow
work. They are not implementations or performance claims. Any later numerical
implementation still needs the505 oracle, saved81-input comparison and actual
animation validation. No next optimization was started here.

## End state and handoff

`COMPLETED` is emitted only after the callback unsubscribes, CSV closes, every
scoped/window recorder disposes, and the window list clears. Profiler.enabled is
false both before/after, and direct runtime readback again confirms false. Play,
unpaused input, Animator Idle speed1, automatic clock, captureDelta0, single
PostView366 hook and all renderer experimentsOFF remain. Diagnostic caches were
released. Runtime505 source SHA is unchanged:
`c24b4e664bd713b35ba4107707c587adc0575b54c159a459d82b3fe736746dd7`.

`measurements.csv` is the15-call evidence. `validation.json` records scope,
overhead, GC limits, input/source hashes, restoration and proposals. Observer
code is under `Assets/EUnityValidation01/HeadRegion502/Editor/Profile507/` and
does not compile into player builds. It starts explicitly and refuses to overwrite
the completed run. No renderer/animation-quality improvement, new capture,
default activation or project completion is claimed.
