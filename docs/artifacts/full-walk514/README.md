# 514 — actual Walk full-loop review, default OFF / not adopted

The 81 matched captures include 80 intervals of the actual Rig|Walk_Loop and its repeated endpoint. The recorded duration is 1.333333177 seconds. The comparison is this run's active348 original versus automatic closed curves511 plus source-ray body visibility512. It does not isolate512 from511; the three-pose513 comparison does that. No new capture or runtime/shader patch was added during the stored-data review.

## Boundary enforcement and temporal selection are separate results

All81 pairs match pose and the recorded light inputs, with81 different deformed geometry fingerprints. Raw/Native/HairLayer/localFinal hair/face boundary violations0, packet mismatch0, unsupported0, body-reference validation errors0. Maximum body ray depth discrepancy4.76830e-7m. These are boundary/packet checks, not a pixel-art or animation-quality pass.

The .6375 event has two different causes. Both first change at region selection, then propagate to Raw and the final output. Neither is a recurrence of the .8750 JoinBare depth defect. Persistent segment IDs remain the same and move continuously; there is no per-pose RDP/anchor replacement or transient body foreground at the selected packet.

| Head cell | .6250 / .6375 / .6500 curve cell area | Original projected mesh union area | Conditional fill-minus-empty cost |
|---|---|---|---|
|234,43|.489966 / .504317 / .487092|.442587 / .449809 / .435558|+.184088 / -.008634 / +.025815|
|218,55|.367875 / .345867 / .321112|.303332 / .282171 / .258389|+.264249 / -.019774 / +.029736|

The first cell has a small real motion peak, while the polygonal approximation increases its area enough to make the middle fill preferable under the current joint energy. In the second cell both areas decrease monotonically. Three neighboring cells fill between the first and middle pose; their perimeter terms temporarily make filling this cell preferable, before its further area decrease turns it off. The latter is not an actual strand appearing and vanishing or body occlusion. Original mesh area is supporting geometry evidence, not a requirement to preserve every mesh detail.

The existing selector minimizes each pose independently: fill unary1-A, empty unaryA, perimeter lambda.14 with axis.58578644 and diagonal.29289322. It has no persistent-boundary temporal/staircase design objective. A lower per-pose energy does not establish acceptable animation. Omitting the two middle cells with the other labels fixed costs.008634 and.019774 respectively; an equal-quality alternative global sequence has not been optimized or proven. No majority, RGB history, threshold or extra quantization layer was applied. The candidate remains unadopted because these one-frame pulses remain.

## Internal colour and candidate-induced body changes

The23 candidate hair flash observations are screening selections, not23 independently certified bugs. Twelve are consistent with the existing OwnerLines333 exterior/thickness reason changing between0 and1. Eleven keep that reconstructed reason unchanged; source colour, UV-dependent shading/texture, normals and world-shadow input changes cannot be separated at their first GPU stage from the saved buffers. Twenty-one also meet the screen in the original348 run. That fact does not make them acceptable. The two newly screened observations are phase.7375 cell224,58 (line-rule consistent) and.8125 cell229,48 (unresolved). GPU Before/Flood/Audit were not captured; reconstructed line reasons must not be reported as direct GPU first-stage proof. Same primitive across animation is not the same UV sample.

There are also8 paired same-body-sample colour changes. Paired META/UV/OWNER match exactly in each, and the pose/light are matched. Seven are .55 RGB ramps within1e-7 and agree with reconstructed exterior eligibility changing0→1 because the selected hair region changes connected exterior. The remaining phase.7500 main cell210,57 changes from(.703125,.6328125,.582188) to(.127438,.068478,.048172) with the same body sample. It is not explained by the exterior reconstruction. Internal/Palette GPU audit is missing; its first stage is unresolved. Do not classify all8 as one cause, normal shading, or successful512 correction. See sameRoleBodyColourClassification in FINAL_REVIEW514.json.

## Light, loop and native-world evidence limits

All81 recorded directional rotations/colours/intensities, ambient intensity and hour4.740795 match. Automatic clock was frozen only for this comparison and restored. Game time advances1.333333177sec, so other scene animation can change. No brightness or scene setting was tuned.

Local preworld region mask, character role and alpha repeat at the loop endpoint. Whole-character preworld RGB maximum is.00295410 linear, identically for the original and candidate; the head preworld maxima are.00026855 and.00061401. Native scene PNG differences reach73byte at positions covered by the local character, with the same maximum in both versions; examples have exactly equal local preworld RGB. This points beyond the local colour change for those examples, but does not prove a normal native-world/shadow transition.

**Scope correction:** saved WORLDINFO is f.motion.worldInfo from legacy480 Compose333. Actual g.player.output is960 Native395.Present, which uses independent world colour/depth and deliveredDelta/origin. Native395 world/worldDepth/owner/cellID/depthAudit and per-pose registration were not captured. WORLDINFO visibility0/1 and zero visibility-change counts therefore cannot certify native world visibility. Screen-vs-local seam statistics in the JSON are explicitly provisional registration comparisons. The large head-ROI screen difference occurs in visually background-coloured samples while local alpha is0; it is not evidence of a head colour seam. Native scene loop colour closure and the exact moving world/shadow cause remain unverified, rather than being declared normal because both versions show it.

## Presentation and preserved state

- WALK514_NORMAL_SPEED_FULLBODY.gif:2,327,242bytes; native full-body crop,67 samples at50fps/1.34sec, no spatial interpolation. Nearest-time sampling omits source51, so this GIF alone hides the representative one-frame event.
- WALK514_NORMAL60_ALL_FRAMES.webp:1,325,022bytes; all80 loop samples, lossless pixels,16/17ms durations totaling1333ms, no spatial interpolation. This retains51 at normal nominal speed.
- WALK514_ALL_FRAMES_INSPECTION.gif:2,778,726bytes; all80 samples at40ms for inspection. Original81 paired PNG/float/geometry records remain locally in Current472/Loop514; endpoint80 is used for seam checking, not duplicated in loop playback.
- CASES514_NATIVE_REVIEW.png shows the representative region and colour triplets at integer magnification. Yellow boxes are diagnostic annotations, not added game outlines.

Normal-speed full-body presentation preserves the walking pose, camera, pixel scale and existing palette; the remaining two short region pulses and line/shading transitions prevent a quality pass. No colour/eye/proportion redesign was made. Eye/frontal/other-angle/other-clip, external-world same-ray correctness, contact and build are not certified by this run. Grouped packet/quad upload212ms remains a separate unoptimized performance blocker.

RESTORED_LOOP514 confirms Playtrue/unpaused, input and Animator enabled, Idle speed1/Locomotion0, capture0, automaticClocktrue, PostView366 only,491/502/505/508/511/512 OFF, profilerOFF and compilation complete. Console remains the historical16 entries after the diagnostic CompressionLevel ambiguity was fixed. Runtime/shader hashes and user Quality/Time settings are guarded;348 commit44d13c0 is retained. Library403 was not retried. This record closes514 analysis, not the whole project.
