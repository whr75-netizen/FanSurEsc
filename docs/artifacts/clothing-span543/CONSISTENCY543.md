# 543: boundary and ink are different contracts

The earlier explanation is accurate for the observed elbow, with one qualification: the vector curve was an area-cost input, not a hard ordered pixel boundary. SelectRegions made the final binary region. The fill did not write through that region. An unchanged vector curve alone therefore did not guarantee a well-designed pixel silhouette.

| Stage | Actual representation and rule | Authority |
|---|---|---|
| OpacityRegion525.Project / ClosedRegion524.BuildSegments | Skinned projected triangles and UV/cutoff-valid connected closed rings, in top-left 480x272 logical coordinates | Source geometry and opacity |
| ClosedRegionDesign539.Fit | Whole outward-return omission, at most 1 logical-cell squared, with winding and crossing guards | Continuous design curves; not a copy of the center-sampled raster |
| CurveArea511.Compute | Closed-region/cell intersection area A, 0..1 | Geometric evidence for the selector |
| HeadRegion502.SelectRegions | Sum(selected ? 1-A : A) + .14 times cardinal/diagonal cut lengths | Final pixel region; originally no explicit leading-span contract |
| Source/native/surface fill and final gate | Selected per-part masks and same-surface UV/depth packets | May supply color inside the selected region; cannot redefine its outline |
| OwnerLines333 | Covered 4-neighbor exterior, 2-cell inward core, same-anatomical-part 3-cell support; thin pixels keep fill color | Changes RGB only, not alpha or selected geometry |
| Occlusion/composition | Existing depth, ownership and masks | May legitimately hide selected pixels; does not authorize new garment coverage |

The old shape and ink rules were deterministic but did not share a thin-feature design definition. At actual Walk65, areas .592355788 and .529834270 favored keeping two leading cells: removing them cost +.244380116 in area and -.164020203 in boundary, net +.080359913. The 2-cell vertical span then failed OwnerLines' three-cell support and stayed bright. Walk66 supplied enough support and ink became dark. This is a coupled shape/luminance artifact, not evidence that black line color itself is the mask.

543 replaces independent labels for a source-certified broad leading span with one label group in the SAME cut. Retained ordered outward returns define its direction; three consecutive positive-area cells require two fully covered cells inward. A genuinely narrow source tip lacks that certificate. Triplet length reuses the existing ink support scale. It is a design choice in logical pixels, not a universal formula derived from resolution or a paper reproduction. Source holes are not grouped. Both arms use the same code and anatomical ownership rules; no left-arm, coordinate, pose or history exception exists.

Independent actual ablation: seven source poses, four renders each. Shape-only removed the two Walk65 cells; the newly exposed inward edge received the existing ink. Ink-only preserved the tab and darkened it, and changed several other boundary colors. The ink-only branch was rejected and its shader/dispatch changes were restored byte-for-byte. Shape-only retains the original thin policy. The 66 shoe change (one leading cell and its neighboring ink) is recorded, not hidden; full-Walk shape review remains required.

The gate passed all15 stored cases (seven observed outerwear inputs and eight synthetic normal thin ends). Actual seven-pose shape comparison preserved34/43/44/50 and face/eye/hair colors. These are local results, not a claim that all boundary transitions, internal shading or Body0/hand behavior are solved. Body0 face ownership, gray-face user report and previous internal color cases remain separate.

One logical cell becomes 2x2 native output pixels. The elbow tab was 1x2 logical cells, hence 2x4 native pixels. There is no filtering/downsampling between these coordinate definitions.
