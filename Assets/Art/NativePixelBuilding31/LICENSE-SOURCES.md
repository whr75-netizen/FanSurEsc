# Building31 source provenance

Selected source: **Isometric Furniture and Walls**, author **hawkbirdtree**.

- Asset page: https://opengameart.org/content/isometric-furniture-and-walls
- Original PNG: https://opengameart.org/sites/default/files/furnitureandwalls.png
- Page license: **CC0** (verified 2026-09-27).
- License link: https://creativecommons.org/publicdomain/zero/1.0/
- Original resolution: 320 by 960 RGBA pixels, transparent background.
- Processing: integer rectangular crop only. No resize, rotation, recoloring, alpha removal, filtering, or generated pixels.
- Original file is preserved at `Tools/Building31/Source/furnitureandwalls.png` in the project.

Two comparison archives were downloaded before selecting the single hawkbirdtree set. They are preserved, but none of their pixels enter the selected crops:

- RatMoleRat, Isometric Building Interiors: https://opengameart.org/content/isometric-building-interiors ; https://opengameart.org/sites/default/files/interiorTiles_0.zip ; page license CC0.
- RatMoleRat, Isometric Furniture: https://opengameart.org/content/isometric-furniture ; https://opengameart.org/sites/default/files/isometricFurniture.zip ; page license CC0.

The selected set contains individual pixel-drawn furniture, floors and wall pieces in a consistent 2:1 isometric projection. A doorway sprite is not supplied in this selected extraction. The building entrance must be formed by an unoccupied wall segment, rather than mislabelling furniture as a doorway.

Grid basis is an interpretation for assembly: one 64x32 floor diamond spans image basis vectors (32,16) and (-32,16), with image X right and Y down. Wall half-strips are 32 pixels wide. Furniture pivots in the extraction manifest are measured bottom-support anchors, not assertions of hidden 3D geometry. Floor and wall corner anchors use their cell lattice. Render these native pixels without resampling.
