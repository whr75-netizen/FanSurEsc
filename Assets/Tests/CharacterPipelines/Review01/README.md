# Character pipeline comparison — reference, not project instructions

Status: technical prototype; C visual result REJECTED by the user. No gameplay integration.

Open `CharacterPipelineComparison.unity`, then Play. Left A / middle B / right C.
Or use `Tools > Fantasy Survival > Character Presentation > Open Pipeline Comparison`.
The on-screen controls pause/advance the walk and change A's key light. The active
camera is front-facing; this sample does not supply other viewing directions.

| Sample | Actual implementation | Intentionally missing / limitations |
| --- | --- | --- |
| A | Existing Chibi visual, Humanoid controller, approved per-object 2px cell renderer and relative-lightness tones | Existing temporal/partial-shadow questions remain; no rendering rewrite here |
| B | 16 automatically captured RGBA sprites from A's walk, point sampling, 12 fps | Lighting is baked. A new animation requires another automatic bake; directions/equipment combinations increase asset count |
| C | 14 fixed part sprites, original modular rig/skin/motion definitions and pose solver, projected bone movement | Front only. No depth reconstruction, per-pixel depth, hidden-face generation or Smack Studio implementation. Back hair is in the Head image and covers the torso; cut boundaries show at joints. This is NOT final art |

All samples use the same Chibi source and `Rig|Walk_Loop` through
`PlayerLocomotion.controller`, without Player gameplay scripts. Walk period 4/3 s,
16 samples; source capture 256×512, pixel cells 2×2, 96 captured pixels per world
unit. Part pivot and bone coordinates share an integer-pixel attachment grid.
The PNGs store actual Unity pixels; no AI-generated replacement frames were used.

## Ownership and reproduction

`CharacterPipelineComparisonBuilder` stages a dedicated scene, prepares skin-weight
partitions in Edit Mode, captures in Play Mode, then imports sprites and saves the
three existing definition types. `ModularSpriteActor` consumes these definitions;
it does not introduce another character/gameplay manager. It owns only generated
SpriteRenderer children. Missing facing slots stay hidden rather than mirrored.

Automatic partitioning assigns each source triangle to exactly one nearest-ancestor
bone group using all vertex influences. Whole-source triangle counts are checked.
It is a mechanical cutting method, not an artist's front/back layer decomposition.
The next C art decision must address hair layer separation and joint overlap/cleanup;
changing a sort number cannot generally solve interleaved front/back geometry.

Order for a NEW review folder (builder refuses to overwrite an existing review):
`Prepare` → `PreparePartitions` (Edit Mode) → Play → `BeginBake` → wait for bake.json
status complete → stop Play → `FinishAssets` (Edit Mode). Bake meshes are disposable
editor inputs and are removed once no scene reference needs them. Original model
Read/Write settings stay unchanged. Source assets are not reimported.

## Evidence — 2026-09-10

- 16 full-body + 14 part captures completed; exact partition index-count conservation.
- 17 actual review frames completed: 16 walk poses, one lower-key-light pose.
- Play Mode calls: B and C sample frame 4 together; 14 visible parts; disable/enable
  does not remove an unrelated child; unsupported facing hides all parts.
- Latest Console query: 0 errors. No player gameplay loop, build, performance claim,
  8-direction asset test, new animation import or mod-loader test.
- First review capture timed out at 1 frame because background execution was off;
  the corrected bounded capture enables it temporarily and restores it afterwards.
- Outputs: `LocalOnly/CharacterPipelineComparison_20260910/` (`bake.json`, source
  PNGs, `review_take02/`, `comparison.png` APNG). The timed-out take is retained.
- User-facing preview shown. A/B look the same (expected: B captures A). User rejected
  C's torso occlusion and detached feet. C is a failed conversion prototype, not a
  demonstration that a proper 2D bone pipeline cannot work.
- Recorded LeftFoot local angles: 0°, 68.6°, 86.2°, 91.2°, 97.6° in frames 0–4.
  The generic projected bone-up direction is not a suitable foot-art orientation.
  Actor applies rigid translation/rotation only; no weighted joint deformation,
  foreshortening or depth-layer splitting exists. These are unresolved conversion
  defects. No cosmetic patch was applied after the user's report.

## Comparison sources

- [Never's End 3D sprite-world production](https://blog.hypersect.com/how-we-draw-a-3d-sprite-world-gdc2026/)
- [Smack Studio's 2D-to-depth/skeleton technique](https://smackstudio.com/here-is-our-technique-for-animating-3d-without-using-3d-models/)
- [Spine parts/accessory example](https://eu.esotericsoftware.com/spine-examples-mix-and-match)
- [Unity readable-mesh/editor access](https://docs.unity.cn/6000.1/Documentation/ScriptReference/Mesh-isReadable.html)

These are references, not imported packages. This comparison does not reproduce
Smack's proprietary depth technique or adopt Never's End's complete renderer.
