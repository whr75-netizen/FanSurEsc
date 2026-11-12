# 66: material hull and character-exterior silhouette are different line classes

Input: original face MToon width/ink and evaluated mesh -> existing head logical
QROI -> same-frame transported main q -> Native395 cell/world/owner receipts ->
private outline colour/primitive/UV output. Existing coordinate origins, matrix
conventions,2x native mapping, raw source UV, depth/hair/world gates are unchanged.

Confirmed counterexample: all4 original-width selected samples in65 occur on
current actor occupancy (native role8 clothing or14 hair). The original material
hull is an internally overlapping decoration, not a generic exterior silhouette.
GDD14.1.4.2 says same-character overlaps do not create total outer lines. Argon2
and2.1's internal part boundary suggestions are not evidence that every native
material hull should be promoted to this exterior class. Pigment/eyelid lines
are separate and keep their original feature paths.

Candidate: explicit class0 preserves the original62 material-hull reference;
class1 rejects this view's own actor occupancy(cell.z==1). This is not a global
CharacterID implementation and does not identify invisible source origins. It
does not suppress actual world occlusion or infer a new pigment family.

CPU replay: original-width extraneous points4 ->0. At32x calibration, internal
overwrites are rejected while outside portions remain. Do not choose another
width, lighten the ink, or cache these incorrect internal points as a fix.

Discriminating GPU test: one normal Play with6consecutive frames, four exterior
width controls0/1/8/32 plus a same-frame original-hull32 reference. Original
draws unchanged; compositor5x1024threads per28x28 frame,8x8 ABI,0loops/arrays/
StructuredBuffers/BVH. No EvaluateForm115. One bounded read per owner, at most
6owners/1.5MiB in flight,120s unchanged. Normal exit and preservation checks
must pass before another execution. Compare every RGB and owner byte against
the current source receipts; actual actor RGB must be unchanged by class1.

Success is the classification fix, not whole-line stability or art completion.
Full character exterior-band geometry/source-origin visibility, generic variable
integer width, valid feature-history selection, face colour-region mapping and
runtime LUT remain separate uncompleted dependencies. Product77 stays default.
