# Closed hair region source 502

This is a default-OFF, NOT-ADOPTED prototype in the current Player renderer. It replaces the
old 491 open-ribbon source while enabled. It is not automatically adopted and
does not establish final pixel-art or animation quality.

The canonical domain is the existing head-local 480×272 grid, with one logical
unit per output cell. No model, bone, camera, palette, eye ratio or project setting
is snapped or redesigned. `HeadRegion502.Enabled` is the sole alternative-path
gate; the default source and the active 44d13c0 fix remain available unchanged.

## Representation and responsibility

1. Project all current deformed hair triangles. Union analytic scanline intervals
   on an eight-samples-per-cell extraction lattice and trace oriented closed rings.
   This extraction is an approximation of continuous geometry, not the final mask.
2. Form closed piecewise-linear curves with a 0.1875-cell RDP approximation bound.
   Tiny rings can collapse. No per-strand connectivity, every-gap, or endcap
   preservation constraint is imposed.
3. Integrate signed curve/cell intersection areas and choose the whole binary
   region jointly with an s/t cut. Unary cost is area mismatch; a nonnegative
   eight-neighbour boundary-length term discourages unnecessary perimeter. The
   trial coefficient is 0.14. This is a first region-design objective, not a proven
   pixel-art curvature-rhythm or temporal metric.
4. Trace the selected region's closed cell-edge boundaries. That selected region
   owns hair coverage. Its union with the protected native face/feature domain
   owns the head parent region. There is no ROI rectangle or convex-hull authority.
5. Each selected hair cell carries its original submesh/triangle, barycentric
   point, UV, world point, depth, normal and tangent. A donor can be at most1.1
   logical cells from the target centre. Transfer outside original coverage is
   explicit; it is not described as the same camera ray or a new 3D surface.
6. Raw, Native, World, Independent and Legacy hair draws use these same cell
   quads instead of the original hair geometry. Original source points supply
   lighting, while the quads supply coverage. Native quads retain the common
   logical cell phase, and every native2×2 block uses the same coverage authority.
7. Eye visibility consumes the owned all-hair layer. Original S4 hair coverage is
   disabled on this alternative path. Existing feature design and 348 fallback
   colours remain intact. Prepare, post-eye and final head ownership gates enforce
   the same selected region; body/world owners are outside this head-family gate.

The existing outline remains inside its covered region. Eleven body-colour
differences in the paired loop were examined separately: two outer bands became
hidden, eight became exposed, and one paired internal-line difference required
temporal correction. At .7375 both versions have the internal line; at .7500 only
the source interrupts it; at .7625 both are head-occluded. It was incorrect to
classify the paired .7500 difference as a new one-frame candidate stroke.
The attempted503 body-core variant changed no output in four actual Walk frames
and was withdrawn, including its own asset/meta and code connections. The shared
`OwnerLines333.compute` remains untouched.

The81-pair loop passes common-boundary and packet checks, but adoption fails on
visible boundary selection transients. At .0125/.0250/.0375 the actual source
keeps skin at head-local(218,52), while the candidate selects skin/hair/skin.
This is a change in the selected region, not later alpha leakage.49 located
one-frame boundary observations are not49 independent bugs. They nevertheless
prevent a claim that visible flicker is solved. The same-primitive hair-interior
colour locator found no jumps above its stated0.10 threshold; this is not a
general lighting, colour-cluster or pixel-art quality pass.

## Limits and evidence

- This source changes hair region selection and ownership. It does not yet design
  internal light/shadow clusters, establish temporal curve correspondence, or
  guarantee perceptual stability. Independent-frame region selection still needs
  actual animation review.
- The protected face domain does not repair native107 holes or lid-carrier limits.
- CPU construction is a prototype with allocations and per-frame geometric work.
  Editor measurements are not a target-platform FPS benchmark.
- Geometry extraction precision, curve simplification, donor choice, occlusion and
  material/feature ownership are separate checks from visual preference.
- Local evidence and the reproducible test contract are under
  `C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/CONTRACT502.json`,
  `Pose502B/`, `Walk502/` and `Loop502/`. Original buffers and PNGs are retained.
  `FINAL_REPORT502.json` records restoration, source fingerprints and corrections.
  The81-frame GIF is slowed for inspection; the40-frame GIF uses actual alternate
  captures at approximately original speed (1330ms vs captured1333.3ms), with no
  spatial interpolation. Its temporal sampling is explicitly recorded.
  Library upload was not retried after the earlier403 access restriction.

The binary unary/pairwise cut formulation follows the representable energy class
described by [Kolmogorov and Zabih](https://www.cs.cornell.edu/~rdz/Papers/KZ-PAMI04.pdf).
The project-specific area and boundary costs are a prototype design decision;
that paper does not validate this pixel-art objective. Artist guidance about
clusters and deliberate simplification comes from Pedro Medeiros's
[Cluster Sketching](https://saint11.art/pixel_art_articles/article2/) and
[Basic Shading](https://saint11.art/pixel_art_articles/article4/).
