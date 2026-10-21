#511 Hair/body source-ray input correction512, local verification513

DefaultOFF, not adopted. Active348 and automatic-curve511 preparation stay intact.
`JoinBare` used a head packet depth from source world point W but a body depth
from a different main-grid sample after rounded XY transport. The two observed
.8750 cells compared rays separated by roughly0.34..0.39 logical cells. Actual
front-facing opaque body triangles at W's ray are1.74/4.46mm behind the hair;
the unrelated destination sample's depth was in front. Role equality never
established surface identity: body primitive IDs actually differ between rays.

The selected definition is source-ray model-body visibility. W, triangle/UV/depth
and its physical body occlusion travel with the designed cell's integer display
placement. Every frame the current evaluated body mesh is intersected at W's
orthographic camera ray, with actual primitive/barycentric UV, cull and conservative
source-alpha bounds. Opaque foreground still wins. An alpha-uncertain foreground
without a known opaque blocker fails explicitly. A nearer potential-alpha surface
already behind W can be a conservative depth bound; no-body is explicit.

Existing mask R/G are untouched. Unused B/A carry source-body depth/reference kind.
JoinBare consumes it only for511 hair versus body; both depths use head-camera
coordinates before the same existing depthOffset. Same100um epsilon, no RGB/history/
morphology/bias/coordinate/phase rules. This replaces a mismatched input; it is not
a second serial filter. The old source-destination comparison remains when OFF.

Composition scope is typed, not a global statement that all renderer rays are
now unified. Face/eye roles never read this body reference. Head-to-main and
main-to-head depth-offset transforms remain inverse, and the same head-cell key
is used for the added data. Face/eye providers, their local sample planes and
authored masks stay unchanged. An off-centre hair donor is not automatically an
eye sample ray; that pre-existing relationship has not been globally certified.
External world composition still compares its own destination world-depth input;
body/body and face/body retain their old paths.512 does not silently convert those
contracts. The three-pose eye/face counts/colour and scene PNG checks below show
no introduced local regression, not frontal/all-part ray correctness.

Actual unit validation: Rig|Walk_Loop .8625/.8750/.8875, same pose/light per pair,
before511 versus512;3 separate deformed meshes. GPU JoinBare fixtures pass near
and far destination-body cases plus defaultOFF: opaque-front, opaque-behind,
no-body, face exclusion, missing-reference, unchanged epsilon. The source-opaque
front case still blocks even when the destination body depth is behind. A live
hand-crossing animation is not covered by these three Walk poses.

- Both reported cells become hair/hair/hair; at centre they were hair/body/hair.
- Five changed cell observations across two poses are body8→hair14. Every changed
  source depth is independently checked against its actual current body triangle.
-1568 packet body references:778 opaque and790 no-body. Reference mask, source
  world, primitive, UV/barycentric/depth checks have0 mismatch; max ray-depth
  difference4.76757e-7m and UV1.05884e-7. No uncertain-front fallback occurred.
- Mask R/G float bits0 difference; Raw/Native/Hair/final boundary violations0,
  packet mismatch0. Main body source buffers and action map bit-identical.
  Head RawUV differs in3 floats at last pose, max1.49012e-8; other captured source
  buffers match. This small observation is preserved without normalization.
- Same-role body/face and same-source-primitive hair RGB differences0; face/eye
  role counts and final character alpha unchanged. Actual scene PNG changes are
  exactly12/8 character pixels in corrected2x2 blocks at the last two poses,
  with0 pixels outside the character changed; first pose is identical.
- Direct state: Play/unpaused, movement/Animator enabled, Idle speed1/Loc0,
  automatic clock, captureDelta0, PostView366 only,491/502/505/508/511/512 OFF,
  ProfilerOFF, compilation finished. Console16 historical entries unchanged.
  One earlier alpha-read tool request failed; the CSV read succeeded without
  changing runtime state. It is not a production runtime failure.

Full-body GIF Current472/Compare513/WALK513_BEFORE511_AFTER512.gif103103 bytes,
same execution, time order, native crop/no interpolation. SHA256:
79f7fc02cacff3474e9e525d59cddd489f62662f388a7aebac9952d418a93302.
Original PNG/float/mesh/projection records remain local. Library403 not retried.

Packet performance was not optimized. MEASUREMENT_PLAN512.md only prepares later
breakdown; the previous212ms grouped span was not attributed to upload. Current
inputs/culling checks add correctness work, with no real-time/FPS claim.

This purpose checkpoint precedes broader regression. Because the input applies
to every hair packet, one actual complete Walk of the corrected representation
is required, covering the old16 intervals without repeating them first. That run
must separate physical/drawn ownership changes, remaining silhouette/region pops,
internal shading, eye/face colour, world occlusion and loop seam. Keep OFF until
that evidence and adoption decision; no full-project or pixel-art completion claim.
