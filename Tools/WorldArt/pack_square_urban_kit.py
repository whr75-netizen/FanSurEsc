"""Pack original native PixelLab material tiles without resizing or pixel normalization.

This is lossless atlas packing, not another image generation or a new art result.
The generated PNGs and the MCP request/receipt remain the provenance authority.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'Assets/Art/UrbanCoherent09/Surfaces'
NAMES = ['asphalt', 'slabs', 'brick', 'plaster', 'ceramic', 'roof', 'window',
         'metal_light', 'wood', 'metal_dark', 'olive', 'concrete',
         'asphalt_variant', 'slabs_variant', 'brick_variant', 'olive_variant']

def main():
    atlas_path = DEST / 'MaterialAtlas.png'
    if atlas_path.exists():
        raise RuntimeError('Preserve existing atlas; use a new explicit revision for changed sources.')
    atlas = Image.new('RGBA', (512, 512))
    entries = []
    for i, name in enumerate(NAMES):
        source = DEST / 'Source' / f'tile_{i}.png'
        image = Image.open(source).convert('RGBA')
        if image.size != (64, 64) or image.getextrema()[3] != (255, 255):
            raise RuntimeError(f'{source}: expected opaque native 64x64 surface')
        left, top = (i % 4)*68 + 2, (i // 4)*68 + 2
        atlas.paste(image, (left, top))
        # Two-texel edge extrusion only; source pixels and pixel density are unchanged.
        atlas.paste(image.crop((0, 0, 1, 64)).resize((2, 64)), (left-2, top))
        atlas.paste(image.crop((63, 0, 64, 64)).resize((2, 64)), (left+64, top))
        atlas.paste(image.crop((0, 0, 64, 1)).resize((64, 2)), (left, top-2))
        atlas.paste(image.crop((0, 63, 64, 64)).resize((64, 2)), (left, top+64))
        entries.append({'name': name, 'source': str(source.relative_to(ROOT)),
                        'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'pixel_rect': [left, top, 64, 64], 'metres': [2, 2],
                        'colour_only': i in (6, 7, 9, 10, 11, 15)})
    atlas.save(atlas_path)
    (DEST / 'MaterialAtlas.json').write_text(json.dumps({
        'generator': 'PixelLab MCP create_tiles_pro',
        'job_id': 'f9eb76e3-4443-4a61-a070-7db94bcee95e',
        'texels_per_metre': 32, 'native_tile_size': [64, 64],
        'transform': 'lossless packing; PNG top-left to Unity UV flip only at consumption',
        'normalization_calls': 0, 'entries': entries}, indent=2), encoding='utf-8')
    print(json.dumps({'atlas': str(atlas_path), 'tiles': len(entries), 'new_generation_calls': 0}))

if __name__ == '__main__':
    main()
