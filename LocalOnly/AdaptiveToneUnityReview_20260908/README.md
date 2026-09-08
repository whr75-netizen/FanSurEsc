# Adaptive tone numerical validation

These are independent CPU references and synthetic numeric inputs. CPU tests alone
do not establish shader compilation, GPU correctness, visual quality or runtime
performance. Actual GPU findings are recorded separately below. The numerical
tests do not change existing character art or Unity scenes.

Run the dependency-free checks from the repository root:

```powershell
python -B -m unittest discover -s LocalOnly/AdaptiveToneUnityReview_20260908 -p 'test_*.py' -v
```

`run_cpu_validation.py --output NEW_PATH.json` writes a separate CPU-only
summary. The original 16-check summary is preserved; the later
`cpu_oracle_summary_with_gpu_checker.json` includes 20 checks after adding mock
artifact tests for the GPU validator itself. Mocks are never GPU evidence.

`gpu_contract_validation.cs.txt` is the `IRunCommand` script executed by the
main task through Unity MCP after shader compilation.
It uses Unity `JsonUtility` DTOs with flat `float[]` fields, requiring no Newtonsoft
assembly in the dynamic compiler. It reads the seven `fixtures_unity/` JSON fixtures, dispatches synthetic textures, records raw
buffer/readback JSON, and disposes its temporary resources. It never accesses
gameplay objects, cameras, scenes, or rendered character artwork. An optional
`gpu_validation_request.json` can choose a case subset, a fresh output
subdirectory, RGBAHalf input colors, and RGBA32 metadata.
The dynamic compiler does not register the nested settings DTO during JSON
loading, so the runner explicitly deserializes the fixture's flat number-only
settings object. Diagnostic wall time uses `EditorApplication.timeSinceStartup`;
`System.Diagnostics.Stopwatch` is not referenced by this RunCommand environment.
The original nested-array `fixtures/` remain preserved. The Python validator
accepts both schemas; `arrayLayout: "flat_float4_v1"` identifies the DTO schema.
Generate a fresh set of DTO fixtures with `gpu_cases.py --unity-flat --output-dir
PATH` inside this review folder. Existing artifacts are never overwritten.

To reproduce numeric inputs in a fresh checkout (large raw readbacks and generated
fixture arrays are local artifacts, not required committed source):

```powershell
python -B LocalOnly/AdaptiveToneUnityReview_20260908/gpu_cases.py --output-dir LocalOnly/AdaptiveToneUnityReview_20260908/fixtures
python -B LocalOnly/AdaptiveToneUnityReview_20260908/gpu_cases.py --unity-flat --output-dir LocalOnly/AdaptiveToneUnityReview_20260908/fixtures_unity
```

Use a fresh output directory in `gpu_validation_request.json` for another GPU run.
The local request left by this experiment selects the additional half-precision
case; it is not a committed default for the seven-case suite.

After actual GPU artifacts exist, run the independent validator:

```powershell
python -B LocalOnly/AdaptiveToneUnityReview_20260908/validate_gpu_result.py --fixture-dir LocalOnly/AdaptiveToneUnityReview_20260908/fixtures --result-dir LocalOnly/AdaptiveToneUnityReview_20260908/gpu_validation --output LocalOnly/AdaptiveToneUnityReview_20260908/gpu_validation_summary.json
```

Its separate `stage_dp` findings test the histogram moments, observed palette
candidates, variable K and fixed support contrast. Resolve findings test the
actual output RGB, unchanged eye depth and sparse metadata, excluded subjects,
and source-supported highlight placement. The default absolute L comparison
tolerance is `3e-5` for independently recomputed versus HLSL float SSE results.

`cpu_oracle.py` directly enumerates interval representatives and sums errors.
The GPU can use prefix moments; comparison against this independent formulation
can detect indexing/cost reconstruction errors. Both search the first
unconstrained SSE-optimal partition in increasing K that passes the required
RMSE and spatial contrast. This does not claim the global minimum K among all
possible spatially constrained partitions.

The GPU histogram contract is 32 adaptive L bins per source owner key, with
count, uint16-normalized first and second source moments, and one actual source
RGB representative selected by its distance to the bin center then source index.
Bin-center RGB is never synthesized. The moments retain within-bin variance.
The CPU uses double arithmetic and fixtures avoid exact rounding half-ties;
HLSL float tolerances must be checked separately.

`gpu_cases.py --list` prints compact case contracts. `--case NAME` prints four
flattened row-major texture arrays suitable for a separately authorized GPU
dispatcher. `--output-dir PATH` writes fixture JSON artifacts inside this review
folder and refuses to overwrite any existing fixture. `source_color_depth` and `seed_color_depth` encode linear RGB in RGB
and eye depth in A. Metadata encodes subject low byte in R, part in G, cell size
in B, and subject high byte in A. Metadata A is not opacity. Seed positions are
sparse and fixed; non-seed data deliberately contains nonzero hidden RGB.

The source owner is a subject-specific dispatch plus part and fixed chroma cell.
The synthetic ownership fixture includes subject IDs 257 and 258 to exercise
both encoded bytes and to catch unintended cross-subject pooling. Other cases
cover constant color, narrow gradient K=1, four observed levels K=4, broad
spatial contrast, invalid part, and 165 valid keys exceeding the 160-key table.

GPU status assertions agreed with the compute author:

| Location | Bit | Meaning |
|---|---:|---|
| Global status index 160 | 1 | Group hash capacity exceeded |
| Global status index 160 | 2 | Source dimensions exceed 4 MP |
| Global status index 160 | 4 | Invalid/nonfinite RGB or eye depth |
| Global status index 160 | 8 | Unsupported part/chroma grid range |
| Global status index 160 | 16 | Invalid settings |
| Global status index 160 | 32 | Resolve key missing; informational failure |
| Each group status | 1 | READY |
| Each group status | 2 | Spatial guard present |
| Each group status | 4 | RMSE candidate failure |
| Each group status | 8 | Contrast candidate failure |

For a group without READY, the original sparse seed color/depth must remain.
The live dispatcher must additionally assert that all seed metadata, eye-depth
values, and seed locations remain unchanged; CPU fixture integrity tests alone
do not prove this GPU behavior. The >4 MP case should inspect/reject dispatch
dimensions rather than construct an unnecessary large synthetic texture.

The fixed chroma grid may over-separate colors close to a cell boundary. The
agreed key uses `floor(chroma / width + .5)`, placing zero at a cell center so
near-zero Oklab chroma roundoff does not split a gray ramp at the origin.

## Actual GPU evidence, 2026-09-08

The main task executed the prepared synthetic dispatches on D3D11. This review
then validated the seven `gpu_validation/` JSON readbacks. Six cases passed all
checks. `four_observed_levels` passed K=4, observed-RGB ownership and resolve /
depth / metadata preservation, but failed the strict reported-RMSE comparison:
the GPU reported `9.155274e-5` while exact source moments with its selected
palette give approximately `6.0e-8`. The original failure is preserved in
`gpu_validation_summary.json`; no tolerance was silently increased.

`gpu_roundoff_audit.json` separately explains this residual through binary32
prefix moment cancellation. In occupied bin 21, exact sum U `85.3333333333`
becomes `85.3333282471`, and exact sum U squared `56.8888888889` becomes
`56.8888931274`. The expanded SSE subtracts terms of comparable size. A
conservative bound derived from unit roundoff `2^-24` and six scalar arithmetic
operations encloses the reported residual. This fixture's requested error
`0.001`, the current `0.06` setting and its K=4 decision are unaffected; the
reported residual is also below `0.0001`. Accurate reporting and decisions at
arbitrarily smaller error settings are not established.

The additional actual `gpu_validation_half/broad_gradient.json` case, using
RGBAHalf input and RGBA32 metadata, passed every check; see
`gpu_validation_half_summary.json`. Both float and half broad-gradient cases
selected K=4 and an observed positive highlight. The float case raised retained
top L from `0.70161289` to `0.73387098`, and the half case from `0.70166880` to
`0.73388660`. Their original support, seed coordinate, metadata and eye-depth
contracts passed. Hash capacity produced explicit status 1 and unsupported part
produced status 8, both preserving the original seed colors.

The recorded runner timings are diagnostic wall-clock times, not GPU profiling
measurements. Runtime frame cost and artistic approval remain outside this
numerical validation report.
