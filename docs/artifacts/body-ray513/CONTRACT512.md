# Source-ray visibility transport for511 Hair only, default OFF

A selected511 hair cell carries source triangle/barycentric world point W, UV,
normal and depth. The physical model-body occlusion sample is the current
orthographic ray through W, not a new ray through the integer-shifted display
cell. Its body intersection and W are measured in the same head-camera depth;
the existing scalar depthOffset converts both to the main camera. Integer XY
placement transports this sampled ownership with the pixel-art cell. Rounding
the display position must not select another body triangle as a new source
visibility decision. This deliberately chooses source-ray visibility, not a new
virtual3D surface made by stretching the cell over destination geometry.

The existing512 correction replaces JoinBare's body-depth input for511 hair
packets. It uses the current evaluated body triangles/UV/material/culling/alpha
and the existing spatial bins, not role identity or neighbour depth. Same-camera
ray barycentrics supply depth. Opaque foreground still blocks. A potentially
visible but alpha-uncertain foreground fails explicitly; it is not treated as
clear or patched by depth bias. A potentially visible surface already behind W
can supply a conservative lower depth bound: even that nearer bound cannot hide
W, so farther actual opaque surfaces cannot hide W either. No-body is explicit.

The shared existing mask keeps R/G coverage bit-identical; unused B/A carry
reference depth/kind for the selected source packet. The renderer consumes that
reference at the same canonical head cell. Same100um comparison epsilon remains.
There is no new colour layer, morphology, history, RGB replacement, pixel/phase
condition, head-always-first rule or packet-cost optimization.

Impact boundary: only JoinBare's511 hair versus model-body comparison changes.
Face/eye source layers, provider geometry and their local depth comparisons are
unchanged. They share the head camera but an off-centre hair donor and an eye
sample are not automatically the same physical ray; no global eye-depth claim
is made. Body versus body and external world composition keep their existing
inputs. External world occlusion and frontal eye cases remain separate validation
scope; this correction does not certify every existing pipeline comparison.
No new source/destination claim is silently applied to those paths. Actual
face/eye colour/ownership regressions must still be checked in paired Walk.

Validation order: current3 adjacent actual Walk poses compare511 input versus
source-ray body input, mask/packets unchanged, body references versus exported
deformed-geometry oracle. A GPU JoinBare fixture checks opaque front/behind,
no-body, face exclusion, missing reference and default-OFF behavior. Then select
necessary animation regression scope from those results. Do not begin a full
loop to replace the point/ray evidence. Preserve defaultOFF, current user
settings and44d13c0; restore input/Animator/clock/hooks. Packet performance only
has a prepared measurement plan and remains unoptimized.
