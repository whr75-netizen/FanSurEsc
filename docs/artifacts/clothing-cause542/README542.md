# 542 — character-left elbow: retained 1x2 leading tab and delayed ink

Confirmed on the existing540 full Walk. No new full-loop capture or product patch.540 Clothes/Off and4067f62 remain unchanged. This corrects the scope of the earlier mask audits: outside-mask0 and filled0 do not certify the shape of the selected boundary or stable outline ink.

## Exact event and ownership

Frames64→65→66, shared480x272 cells(201,73),(201,74). At65 these two cells form a one-column/two-row leading extension; at64 that column is absent and at66 the column has grown to four rows. This is1x2 logical cells /2x4 pixels in the native960x544 output. The event is present in productOFF and remains with Clothes540 ON; it is not a new Body0-only effect.

Existing source tags map the cells to Body submesh3 (outerwear), role10 / stored owner11, anatomical part2. Humanoid bone names resolve J_Bip_L_UpperArm/J_Bip_L_LowerArm as LEFT; the corresponding skin-weight/triangle map confirms this side. Right arm is existing part3. Screen-left was not used as the side definition. The left elbow moves behind the torso in this phase and appears on the image's left edge. The full-body triptych and integer nearest-neighbour detail are both supplied.

## Original projection → vector region → discrete selection

The continuous source elbow is a broad retained bend, not a new1x2 mesh rectangle. On65 the source/selected-curve left intersections at y73.5/74.5 are identical: x201.395075956 and201.469506670. The unbounded ordered return covering this bend has area24.7201772cell², depth2.9645233 and length15.991246;539's<=1cell² whole-return omission therefore does not remove the physical elbow. No threshold is enlarged to erase it.

The two cell areas are64:[.189482331,.077737711],65:[.592355788,.529834270],66:[.946596503,.940667808]. `ClothRegion524.PrepareSingle540` → `HeadRegion502.SelectRegions` first writes the discrete selected boundary before the source camera render. Its objective is sum(selected?1-A:A)+.14*(.58578644 cardinal boundary cuts+.29289322 diagonal cuts). At65 removing both leading cells increases area error.244380116 and decreases boundary cost.164020203, net+.080359913. Thus the implemented optimizer deliberately keeps the tab. It has no constraint on the progression/width of a new leading stair span on a retained larger bend. This is an objective/representation limitation, not arithmetic error or a later mask leak.

The selected mask already includes the cells, so Probe/Prepare are allowed to supply their original surface colour. Stored65 Prepared and PostLine are identical at each cell, as are productOFF and540ON. The tab is not created by final compositing, outline dilation, neighbour RGB copying or a depth exception.

## Why it looks as though bright fill pierces the outline

`OwnerLines333.compute` uses an independent thinness exemption. At65 each tip cell has outside neighbours and left-boundary `ownCore` support, but has only two vertical part2 cells. `hasThreeInAxis(vertical)` is false; top/bottom outward directions also lack two inward same-part cells. Therefore thin=true, outer=true, reason=0: the bright original colour is retained. At66 all required support exists: thin=false, reason=1; the same cells become existing deepCream ink(.127437696,.068478182,.048171822). `ELBOW_LINE542.json` reconstructs the exact neighbourhood/4-connected exterior and matches the stored Before/PostLine values.

The perceptual pop combines a two-cell leading boundary birth with its thin-feature outline exemption. The closed selected region is enforced, but its shape admits the tip and the ink is not an unconditional representation of that region boundary. Calling outside-mask0 a complete solution missed this case. Fixed-cell alpha ABA was0 in the elbow-domain check: the cells stay occupied while the elbow moves, so one-frame disappearance alone is an insufficient detector.

## Changes / next boundary

No production code, weights, colours, camera, line thickness or selector constants were changed in this investigation. Simply darkening all thin tips or deleting all1px details is not a validated fix; normal hands/ends and the original elbow shape must remain valid. A future change must explicitly reconcile the progressing selected boundary span and its fill/ink ownership in the existing selection/generation contract. The previous global temporal arc DP, history filters, dilation and ad-hoc per-case penalties were not resumed.

## Preserved541 Body0 investigation

Original35/36/41 cases were re-observed with the existing actual-Walk runner35..41 (7poses/21renders), with input/Animator/clock restored. An earlier manual frozen fixture was misaligned and did not run the same NativePlayer395.Follow lifecycle; its exact alignment subcause was not separately isolated. It is preserved separately, not used as cause evidence.

At the valid cases the body centre is empty. Only native quadrant(xx0,yy1) has Body0 primitive9626, sampled at logical(x+.25,y+.25); other quadrants are empty. Selected area.5511476/.6280218/.6388474 admits the cell. Isolated exact Prepare replay outputs Body owner8 before JoinBare, matching the old final owner/depth. For35: body13.698246 versus head bare13.8726997 plus offset-.007336277=13.8653631, so JoinBare's existing comparison rejects the head. The triangle's three vertices have100% Head weights; Body0 includes head skin as well as torso/hands/garments. This confirms the first fill and compare path, but the same-ray physical visibility/scope decision remains pending because the user's left-elbow case took priority. No face-always-front or skin-constant patch was applied. Actual541 input packets are archived for continuation.

Final operational state was directly checked Edit/unpaused, cloth/opacity/area/wholeOFF, capture0, backgroundfalse, scene clean. User QualitySettings/TimeManager bytes and540 runtime sources are preserved. Library403 was not retried. The main page retains the current540 full comparison and explicitly marks this left-elbow defect as unresolved.
