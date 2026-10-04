"""N17 floor surface: immutable material UVs on the original horizontal slab.

The native camera grid owns sample locations, not the material's world period.
No PNG resize, additional screen pixelation, invented plank seam or RGB lighting
is applied here. Geometry and material rank are separate downstream inputs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from geometry16 import build_box


ROOT = Path(__file__).resolve().parents[2]
BINDING_PATH = (
    'Interior34 - aligned native surfaces/'
    'Structure - closed volumes/Floor/Native surface'
)
SOURCE = ROOT / 'Assets/Art/PixelShopInterior34Aligned/Source/floor-warm.png'
CALIBRATION = ROOT / 'docs/artifacts/building34/calibration-oriented.json'
LOCAL_BOUNDS = np.array([[-5., -.04, -4.], [5., .04, 4.]])
FLOOR_PARENT_Y = -.025


def _source():
    """Read the actual bound floor's retained 125 x 132 material, unchanged."""
    content = SOURCE.read_bytes()
    with Image.open(SOURCE) as image:
        if image.size != (125, 132):
            raise ValueError('N17 floor material dimensions changed; new UV contract required')
        rgba = np.asarray(image.convert('RGBA'))
    if not np.all(rgba[..., 3] == 255):
        raise ValueError('Original floor material must be fully opaque')
    original_ppu = float(json.loads(CALIBRATION.read_text(encoding='utf-8'))['ppu'])
    if not np.isfinite(original_ppu) or original_ppu <= 0:
        raise ValueError('Original floor material UV density is invalid')
    return rgba[..., :3], hashlib.sha256(content).hexdigest(), original_ppu


def build_floor(ppu):
    """Return geometry16 buffers in the existing Floor renderer's local space.

    The parent centre is building-local Y=-.025m, so local top Y=.04m is
    building-local Y=.015m. The original 10 x .08 x 8m slab remains the closed
    caster. Display coverage belongs only to its horizontal top plane, with an
    upward normal; thin side faces do not gain a fictitious upward normal.
    """
    _, source_sha, original_ppu = _source()
    data = build_box('floor_surface', LOCAL_BOUNDS, ppu=ppu, material=1)
    top = data['mask'] & (data['normal'][..., 1] > .999999)
    data['mask'] = top
    data['position'][~top] = 0
    data['normal'][~top] = 0
    data['material'][~top] = 0
    data['part'][~top] = -1
    data['chart'][~top] = -1
    data['depth'][~top] = np.inf
    # The previous floor had no authored perimeter stroke. Plank seams remain
    # source-material samples, not newly synthesized line or silhouette roles.
    data['edge'][:] = 0
    data['metadata'].update({
        'bindingPath': BINDING_PATH,
        'binding_selection': 'active aligned Floor observed in actual GameMap1 Play Mode',
        'coverage': 'native pixel-centre ray hit on original horizontal floor top',
        'normal': [0., 1., 0.],
        'renderer_parent_building_y_m': FLOOR_PARENT_Y,
        'renderer_local_top_y_m': float(LOCAL_BOUNDS[1, 1]),
        'building_local_top_y_m': float(FLOOR_PARENT_Y + LOCAL_BOUNDS[1, 1]),
        'original_floor_local_bounds_m': LOCAL_BOUNDS.tolist(),
        'shadow_mesh': 'original closed 10 x .08 x 8m floor slab, twelve triangles',
        'source': str(SOURCE.relative_to(ROOT)).replace('\\', '/'),
        'source_sha256': source_sha,
        'source_dimensions': [125, 132],
        'source_resize_count': 0,
        'material_original_ppu': original_ppu,
        'material_uv_texels_per_metre': original_ppu * .70710678,
        'material_uv_formula': 'floor(repeat(local x/z * originalPPU * .70710678, width/height))',
        'material_uv_origin': 'original renderer-local X/Z zero; no translation added',
        'source_row_convention': 'Unity GetPixels32 is bottom-up; PIL row is height-1-y',
        'material_world_uv_changed': False,
        'new_perimeter_or_plank_lines': False,
    })
    return data


def assign_floor(data, palette):
    """Return wood ids, nearest observed wood-tone rank and no new edge roles.

    ``palette`` is the shared 10 x 4 x 3 observed sRGB uint8 palette. The source
    RGB only chooses a material rank. Runtime light chooses the final palette
    entry; no source brightness is copied as an extra illumination multiplier.
    The source's low/high material tone can still include painted illumination,
    and this function makes no claim of recovering pure albedo from one image.
    """
    colors = np.asarray(palette)
    if colors.shape != (10, 4, 3) or colors.dtype != np.uint8:
        raise ValueError('N17 shared observed sRGB palette must be uint8 10 x 4 x 3')
    source, source_sha, original_ppu = _source()
    metadata = data.get('metadata', {})
    if metadata.get('source_sha256', source_sha) != source_sha:
        raise ValueError('Floor source changed between geometry and material stages')
    mask = data['mask']
    position = data['position'][mask].astype(np.float64)
    normal = data['normal'][mask]
    if not np.isfinite(position).all() or not np.allclose(normal, [0., 1., 0.], atol=1e-6):
        raise ValueError('Floor material input must be finite upward top-plane hits')
    scale = original_ppu * .70710678
    # Exactly the former Unity material mapping; its repeat period does not
    # change when the active aligned camera/native cache changes from 127 to
    # 90.5097 PPU. The inactive original 181-PPU floor is not this binding.
    x = np.floor(np.mod(position[:, 0] * scale, source.shape[1])).astype(np.int32)
    y = np.floor(np.mod(position[:, 2] * scale, source.shape[0])).astype(np.int32)
    sampled = source[source.shape[0] - 1 - y, x].astype(np.float64)
    difference = sampled[:, None, :] - colors[0][None, :, :].astype(np.float64)
    nearest = np.argmin(np.sum(difference * difference, axis=-1), axis=1).astype(np.uint8)
    ids = np.zeros(mask.shape, np.uint8)
    pattern = np.zeros(mask.shape, np.uint8)
    edge = np.zeros(mask.shape, np.uint8)
    ids[mask] = 1
    pattern[mask] = nearest
    return ids, pattern, edge
