"""Read-only pixel checks of a saved layered run and actual Aseprite CLI exports.

First export character_layers.aseprite with Aseprite --batch --save-as to
aseprite_composite_check.png, then with --ignore-layer Highlight before the
input file to aseprite_base_check.png. This script does not render or restyle.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
ENGINE = ROOT.parent / 'PerfectPixelPalette_20260906'
sys.path[:0] = [str(ENGINE / '.deps'), str(ENGINE / 'src')]
import numpy as np
from PIL import Image
from perfect_pixel.color_layers import rebuild_color_layers
from perfect_pixel.palette import rgb_to_oklab


def read(path):
    with Image.open(path) as im:
        return np.array(im.convert('RGBA'))


def verify(result, approved):
    final = read(result / 'pixel_native.png')
    base = read(result / 'base_native.png')
    previous = read(approved / 'pixel_native.png')
    overlay = read(result / 'highlight_native.png')
    active = overlay[..., 3] == 255
    np.testing.assert_array_equal(base, previous)
    np.testing.assert_array_equal(final[..., 3], base[..., 3])
    np.testing.assert_array_equal(final[~active], base[~active])
    composed = base.copy(); composed[active] = overlay[active]
    np.testing.assert_array_equal(composed, final)
    with np.load(result / 'processing_maps.npz') as current_maps, \
         np.load(approved / 'processing_maps.npz') as previous_maps:
        np.testing.assert_array_equal(current_maps['sampling_source_xy'],
                                      previous_maps['sampling_source_xy'])
    source = read(result / 'source_input.png')
    observed = set(map(tuple, source[..., :3][source[..., 3] == 255]))
    assert set(map(tuple, final[..., :3][final[..., 3] == 255])) <= observed
    previous_l = rgb_to_oklab(base[..., :3].astype(np.float32) / 255)[..., 0]
    final_l = rgb_to_oklab(final[..., :3].astype(np.float32) / 255)[..., 0]
    assert np.all(final_l[active] > previous_l[active])
    for include, expected in ((True, final), (False, base)):
        np.testing.assert_array_equal(rebuild_color_layers(result / 'color_layers',
                                        include_highlights=include), expected)
    np.testing.assert_array_equal(read(result / 'aseprite_composite_check.png'), final)
    np.testing.assert_array_equal(read(result / 'aseprite_base_check.png'), previous)
    manifest = json.loads((result / 'color_layers' / 'manifest.json').read_text(encoding='utf8'))
    record = json.loads((result / 'settings_and_result.json').read_text(encoding='utf8'))
    accent = record['result']['features']['highlight_accents']
    # Details live in the feature metadata, not an aesthetic score.
    return {'native_size': list(final.shape[1::-1]),
            'approved_base_byte_exact': True, 'sampling_coordinates_unchanged': True,
            'alpha_unchanged': True, 'outside_highlight_byte_exact': True,
            'all_changed_pixels_brighter': True, 'all_final_rgb_observed_in_source': True,
            'json_mask_recomposition_both_modes_exact': True,
            'actual_aseprite_composite_exact': True, 'actual_aseprite_without_highlight_exact': True,
            'changed_native_pixels': int(active.sum()),
            'groups': {g['name']: len(g['layer_ids']) for g in manifest['groups']},
            'highlight_metadata': accent, 'design_approval': 'user review pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, default=ROOT / 'result_highlight_layers_96')
    parser.add_argument('--approved', type=Path, default=ROOT / 'result_spatial_steps_96')
    args = parser.parse_args()
    report = verify(args.result.resolve(), args.approved.resolve())
    # Existing processing records and inputs are never rewritten.
    with (args.result / 'layer_verification.json').open('x', encoding='utf8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    brief = {key: value for key, value in report.items() if key != 'highlight_metadata'}
    print(json.dumps(brief, ensure_ascii=False))


if __name__ == '__main__': main()
