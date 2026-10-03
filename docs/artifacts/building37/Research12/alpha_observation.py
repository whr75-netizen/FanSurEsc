"""Read-only reproduction of the R12 alpha/color observation; no PNG is written."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def observe(path):
    path = Path(path)
    with Image.open(path) as im:
        if im.mode != 'RGBA':
            raise ValueError('Expected explicit RGBA; no conversion or resizing.')
        a = np.array(im)
    v = a[..., 3] > 0
    c = a[v, :3].astype(np.float64) / 255
    lin = np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
    alpha = a[v, 3:4].astype(np.float64) / 255
    result = {
        'input': str(path), 'input_png_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'size': [a.shape[1], a.shape[0]],
        'partial_alpha_pixels': int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum()),
        'visible_alpha_levels': len(np.unique(a[v, 3])),
        'visible_RGB_count': len(np.unique(a[v, :3], axis=0)),
        'visible_RGBA_count': len(np.unique(a[v], axis=0)),
        'compositing': 'Assume sRGB; decode to linear, composite on opaque background, encode and np.rint to 8-bit RGB',
        'unity_capture': False, 'png_modified': False,
    }
    for label, background in [('black', 0.), ('white', 1.)]:
        mix = lin * alpha + background * (1 - alpha)
        srgb = np.where(mix <= .0031308, 12.92 * mix, 1.055 * mix ** (1 / 2.4) - .055)
        out = np.clip(np.rint(srgb * 255), 0, 255).astype(np.uint8)
        result['composited_' + label + '_RGB_count'] = len(np.unique(out, axis=0))
    return result


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=str(root / 'docs/artifacts/building37/Legacy11/native-4.png'))
    args = parser.parse_args()
    print(json.dumps(observe(args.source), ensure_ascii=False, indent=2))
