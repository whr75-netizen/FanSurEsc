# Hair region area input 504 — default OFF, not adopted

Only the fidelity area input changed after checkpoint `60191b59`. The old RDP
closed-curve approximation inflated a representative cell's area and caused a
visible skin/hair/skin flash at Walk .0250. The new input integrates the original
closed **1/8-cell extraction region** (64 equal-area squares per logical cell).
This is exact for that extracted polygon, not exact for the continuous mesh.

The selected output remains a jointly chosen binary region on the common
head-local 480×272 grid. The unchanged objective is
`sum(q*(1-A)+(1-q)*A) + .14*sum(w*abs(q_i-q_j))`, with orthogonal/diagonal weights
`.58578644/.29289322`. Source area is evidence for this selection; it is not a
centre-sampled output, an area threshold, or a copy of the input raster.
`SelectedLoops` is the final closed cell-edge boundary. The .1875-cell RDP fit is
now diagnostic only. Shared coverage/packet/eye/final gates from502 are unchanged.
There is no temporal/RGB filter, added morphology, coordinate exception, or
requirement to preserve each strand and every tiny gap.

## Measured results

- All81 saved inputs replayed with the exact original selector: reference
  mismatch0. Whole-mask one-frame reversal observations128→11; this is **not**
  the earlier49 final visible observations and is **not** an error count.
- Of those49 old observations, the new selection gives32 stable omissions,
  8 stable fills,8 shifted transitions and1 retained010 observation. These are
  classifications, not automatic quality passes.
- Actual5 adjacent Walk pairs remove the .0250 flash. Another33 paired poses in
  eight adjacent intervals match all saved predicted masks. Together38 pairs
  have pose/light agreement, Raw/hair/final boundary violations0, packet
  mismatches0 and unsupported donors0. This is **not a new full runtime loop**.
- Six of the8 stable-fill cases have actual adjacent shape comparisons; indices
  47 and64 remain saved-input only. The selected design changes face exposure at
  hair edges; it does not resize the model or eyes. Frontal eyes remain untested.
- Five body-colour paired differences were independently checked. Same owner,
  primitive/meta and UV remain; external coverage and the existing thickness
  predicate expose an outer band, with exact0.55 colour ratio. They are not five
  newly born internal strokes. This does not establish all shading quality.
- Current source hair coverage differs from old502 coverage at one cell in
  target79; paired current pose/light and candidate prediction still match.
  The old run is not used as exact current colour/lighting ground truth.

## Remaining cause and limit

The9 targeted reversal observations group into8 temporal episodes. The deformed
triangle-union area and actual triangle-edge identities were recovered from the
saved33 poses. Seven episodes (8 observations) show an extraction-area error
contribution: for example at head(220,57), .2625/.2750/.2875, continuous union
area increases .306404/.310049/.313548 while extracted area turns back
.296875/.343750/.265625. The final roles are body8/hair14/body8. This is already
chosen in the mask and is not a later occlusion discard. The .6625 episode also
changes neighbours; its extracted area plateaus rather than turns back.

At(224,58), .8625/.8750/.8875, both area estimates decrease, but the recorded
neighbour contribution changes +.0820101 to−.1640202. This explains the local
preference reversal. Whether a global joint-boundary selection can avoid it at
equal shape quality remains unresolved. It is not classified as normal occlusion.
Local exact-area counterfactuals keep neighbour labels fixed; no full exact-area
global replacement has been implemented or validated. No next patch was made.

The alternative remains **OFF and not adopted**. Boundary enforcement passes
and partial flash improvement do not establish pixel-art cluster design,
stair rhythm, internal light/shadow design, or animation stability. The active
44d13c0 fix, user settings and current scene are preserved. Play/input/Animator
Idle speed1/automatic clock/captureDelta0/single PostView366 hook were read back.

## Local deliverables

`Current472/First504/WALK504_FULLBODY_BEFORE_AFTER.gif` is5 actual adjacent pairs.
`Current472/Groups504/WALK504_FULLBODY_BEFORE_AFTER.gif` is33 full-body paired
frames, eight labelled intervals with explicit time jumps,80ms slow inspection.
Native spatial pixels are preserved; original PNG and float buffers remain.
Library403 was not retried. `validation.json` lists exact paths, sizes and hashes;
the review PNGs are nearest-integer diagnostic enlargements, not game resampling.
