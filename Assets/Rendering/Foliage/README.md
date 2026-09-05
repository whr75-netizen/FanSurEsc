# Object-local pixel foliage prototype

## Scope and source of truth

`Assets/Prefabs/Foliage/PrototypePixelFoliage.prefab` is the reusable source. Its single `GameMap1` instance is at `(-5.5, 0, -5)`, left/front of the player start. Existing foliage is unchanged. No camera pixelation, renderer feature, runtime manager, package or city-generation integration was added.

`PixelFoliagePatch` stores authoring inputs only. `PixelFoliageMeshBuilder` bakes one combined grass mesh and one combined leaf mesh. Four coincident vertices carry each card's world anchor, source normal, dimensions, atlas row and stable seed. The material expands the billboard and samples the mask; it does not create one GameObject or Update per leaf. Use unit Transform scale and the authored size range for card dimensions.

Grass uses terrain-up normals; leaves use ellipsoid crown normals. A separate low-poly, shadow-only crown casts the tree's shadow; the trunk alone has a static collider. The sprite atlas supplies **alpha silhouettes only**, never painted lighting. Source position/normal drive URP lighting, including the main-light Cookie once. The existing stepped-local-light fullscreen pass remains its own owner and uses rendered depth; it is not duplicated in this shader.

## Authoring and current comparison

- Material: Base Color, Sprite Frames Per Second, Per-Tuft Brightness Variation, Diffuse Shade Steps and lighting strengths.
- Current comparison: `0.4 fps` = each tuft holds one frame for `2.5 seconds`; four frames form a 10-second loop. Random starting phase staggers changes across tufts, so the whole tree does **not** change in unison every 2.5 seconds.
- Brightness variation `0` removes the baked per-tuft ±7% variation; `1` restores it. Diffuse steps `2` reduces direct-light bands, including the ground-reference material. SH, shadow/cookie attenuation, light colour and fog remain continuous: this is not an exact two-colour final framebuffer.
- Previous prototype appearance can be restored with `fps=8`, `variation=1`, `steps=3`. Geometry, colours and original atlas were retained.
- Patch Inspector: seed, count, dimensions and crown ellipsoids, then **Rebuild Foliage Mesh**. Rebuild changes the shared mesh asset for all instances using it; no silent runtime regeneration.
- Create menu: `Tools/Fantasy Survival/Environment/Create Pixel Foliage Prototype`.

The user wants sparse colour masses and infrequent shape changes suggesting leaves/grass. The 2.5-second comparison is **not a verified setting from the reference author**. Trunk/branch bending, global weather-driven wind, large-forest GPU profiling and Player builds are outside this prototype. The trunk itself is ordinary 3D, not camera-pixelated geometry.

Latest user correction (2026-09-05): the leaf shader is satisfactory; preserve it and focus on grass. Grass currently has one base colour per tuft and terrain-up lighting. Wind swaps alpha silhouettes only; it does not animate a second colour or normal. Setting diffuse steps to two does not produce two visible colours under uniform light. Whether the reference uses an animated second tone remains unconfirmed; do not silently impose a new grass palette or change leaves together with grass.

## Environmental comparison and integration

The existing `PrototypeSunShaftContrastTestArea` prefab now contains a 100×64 metre comparison yard: open ground, full roof, a 5×6 metre skylight, slatted alley, mature grove and distance controls. The base-scene instance is `PrototypeSunShaftContrastTestArea_BaseTest`. Nine grove trees reach roughly 13 metres. Grass and its receiving ground share their palette and source-normal lighting; shadows and cloud attenuation, rather than random extra grass colours, separate their tones. Approved leaf materials are retained. `FoliageLightingTestSetup.Populate` is an explicit Editor-only operation, not a runtime generation loop. Mesh assets are shared and existing authored meshes are not silently rebuilt.

| Responsibility | Implementation and limits |
|---|---|
| Grass | Baked source position/up normal light each card uniformly, with two direct diffuse bands. Smooth shadow/cookie attenuation is intentional. No claim that the final image contains exactly two colours. |
| Sun shafts | Existing half-resolution world-plane integration reads the real main-light shadow map and cloud Cookie at each sample. The compositor compares scene depth before reconstructing light at full resolution, avoiding blind foreground/background blur. 24 samples are the prototype default. This is an independent implementation, not the author's unpublished shader. |
| Storm | `SkyLightingCycleController` is the only weather owner. The existing cloud field grows into overcast for `StormGatherSeconds` (8 s), then precipitation fades in over `WeatherTransitionSeconds` (0.75 s). No new cloud objects/noise layer; the density texture's second channel retains the continuous shape field. Clear/Rain endpoints share one directional-light attenuation budget, avoiding double dimming. |
| Rain mist | `StylizedLightShaftPresentation` derives density and sun-volume suppression from the sky owner's overcast coverage, alongside the 8-second cloud gathering; only precipitation waits for the subsequent 0.75-second fade. The existing renderer adds analytic gray extinction through a 0–8 m world-height layer, clipped by opaque depth. Ambient light controls mist brightness. This is height fog, not camera pixelation or simulated smoke, and has no indoor exclusion volumes yet. |

The ESC environment test's weather buttons now request the transition, not an immediate switch. Repeating Rain does not restart gathering; Clear can interrupt it. Restore/initialization APIs retain their explicit immediate option. Streetlamp cone rendering and object-local pixel controls remain separate and unchanged. Transparent-surface occlusion/compositing, room-specific fog exclusion and target-hardware GPU profiling remain unvalidated follow-ups, not finished features.

Technical comparison: the author's [Godrays description](https://www.youtube.com/watch?v=fSNdZ82I-eQ) confirms light-space shadow-map sampling and angle/time/rain modulation, but does not publish exact integration parameters. [David Holland's reconstruction](https://www.davidhol.land/articles/3d-pixel-art-rendering/) discusses source-position grass lighting, stacked light planes, grass-edge depth artifacts and the cost of repeated depth blurs. [Frostbite's participating-media presentation](https://www.advances.realtimerendering.com/s2015/index.html) is the professional reference for unified media/extinction, not a reason to import a full volumetric-cloud system into this prototype. Unity's [volumetric-cloud documentation](https://docs.unity.cn/Packages/com.unity.render-pipelines.high-definition%4012.0/manual/Override-Volumetric-Clouds.html) separates shape/erosion/coverage and rain controls; those principles were compared, not its HDRP renderer imported. The requested video timestamps were not directly visually inspected in this tool environment; exact author parity is unverified.

## References (principles, not copied source code)

- t3ssel8r [Grass V2](https://www.youtube.com/watch?v=thUXblUXKeU): grass lighting from source terrain position/normal.
- t3ssel8r [Trees](https://www.youtube.com/watch?v=pslJg8vpeHo): leaf sprites using proxy surface normals and shadow geometry.
- [Wind description repost](https://www.gamesinprogress.com/indie-game-developers/t3ssel8r/wind-animations): sprite-sheet UV selection by position/time; exact frame cadence and colour count unconfirmed.
- David Holland [3D pixel-art rendering](https://www.davidhol.land/articles/3d-pixel-art-rendering/), [Unity implementation](https://github.com/bababuyyy/unity-isometric-pixel-pipeline): reviewed source-position lighting separately from the project's fullscreen pixel pipeline. That pipeline was not imported.

## Generated asset provenance

`Assets/GameData/Foliage/FoliageWindAtlas.png` was generated once with built-in image generation, not downloaded or copied from the reference. The original file is retained; Unity imports it at 128×64, Point/Clamp, no mipmaps, uncompressed (32×32 per frame). It is a 4×2 atlas: leaves on the top row, grass on the bottom row. The comparison above does not regenerate or edit the image.

Prompt used:

> Use case: stylized-concept. Asset type: a single production sprite animation atlas for a Unity isometric pixel-art foliage shader. Make an original functional 4-column by 2-row atlas on a genuinely transparent background, exactly 1024 by 512 output if possible. Every cell is an equal 256x256 square, representing a hand-pixeled 32x32 logical sprite enlarged nearest-neighbor by 8. TOP ROW: four looping gentle-wind frames of the SAME small rounded cluster of 5 to 7 broad overlapping deciduous leaves, an irregular scalloped silhouette, arranged as a compact leaf tuft rather than an entire tree, with a few clean transparent gaps. BOTTOM ROW: four looping gentle-wind frames of the SAME small clump of 5 to 7 upright pointed meadow grass blades, bottom-root centered identically at x center, y=bottom of each cell leaving 2 logical pixel padding, varying tip sway only. All eight silhouettes are solid white RGBA masks; no gray shading or green, the game shader supplies their color and 3D lighting. Very readable fine stair-step pixel edges, no big mosaic blocks, no outlines, no gradients, no antialiasing, no shadow, no text, no cell borders, no background pattern. Keep each sprite centered and separate within its own cell, generous consistent 2 to 3 logical pixel transparent margin. Top leaf cluster square-ish, grass tuft taller than wide. Wind phases 0 / leaning slightly right / neutral / leaning slightly left, so looping frame4 back to1 is gentle. This is a sprite texture asset, not a scene, not a showcase, not a tree illustration.
