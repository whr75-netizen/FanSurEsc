# Packet-span measurement preparation only

Do not optimize or start measurement while the same-ray ownership event is unresolved.
The212ms median is one grouped stopwatch interval, not evidence of an upload bottleneck.
Later measure the same deforming pose input in paired runs, preserving packet output:
candidate lookup/barycentric and nearest-point search; blocker ray/alpha decisions;
quad vertex/normal/tangent assembly; per-piece Mesh buffer upload. Record call and
candidate counts separately from wall time, and managed allocations only with a
validated sentinel/API. Separate initialization and whole RenderFrame. Quantify
measurement overhead; retain an uninstrumented comparison. No stationary pose/image
cache or source/body/eye/time-cost change is part of this preparation.
