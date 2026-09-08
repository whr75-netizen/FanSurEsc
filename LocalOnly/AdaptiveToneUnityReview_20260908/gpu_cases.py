"""Tiny numeric texture fixtures for the parent's Unity GPU dispatch checks.

Run ``python -B gpu_cases.py --list`` for the compact case contracts, or pass
``--case NAME`` for flattened source/seed Color arrays in row-major (y,x) order.
This module only prints JSON; it does not create textures, files, or artwork.
"""
import argparse
import json
from pathlib import Path


def oklab_to_linear_rgb(lightness, a, b):
    l = (lightness + .3963377774 * a + .2158037573 * b) ** 3
    m = (lightness - .1055613458 * a - .0638541728 * b) ** 3
    s = (lightness - .0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + .2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
            -.0041960863 * l - .7034186147 * m + 1.7076147010 * s)


def encode_meta(subject, part, size=4):
    return ((subject & 255) / 255., part / 255., size / 255., (subject >> 8) / 255.)


def build_case(name):
    width, height = 32, 16
    if name == 'hash_capacity':
        width, height = 33, 5
    subject = 257
    source, source_meta, seed, seed_meta = [], [], [], []
    settings = {'subject_id': subject, 'tone_error': .06, 'chroma_error': .06,
                'minimum_contrast': .025, 'contrast_retention': .65}
    expected = {'metadata_unchanged': True, 'seed_coordinates_unchanged': True,
                'eye_depth_unchanged': True, 'observed_rgb_from_same_part_chroma_group': True,
                'global_status': 0}
    if name == 'flat_constant':
        expected.update(exact_seed_color_depth=True, active_group_count=1, group_tone_counts=[1])
    elif name == 'narrow_gradient_one_tone':
        expected.update(active_group_count=1, group_tone_counts=[1])
    elif name == 'four_observed_levels':
        settings['tone_error'] = .001
        expected.update(active_group_count=1, group_tone_counts=[4])
    elif name == 'broad_gradient':
        settings['tone_error'] = .04
        expected.update(active_group_count=1, require_guard_present=True,
                        minimum_group_tone_count=2, broad_source_contrast_preserved=True)
    elif name == 'equal_l_chroma_part_subject':
        expected.update(active_group_count=3, group_tone_counts=[1, 1, 1],
                        excluded_subject_id=258, excluded_subject_unchanged=True,
                        exact_seed_color_depth=True)
    elif name == 'unsupported_part':
        expected.update(global_status_bits_required=8, exact_seed_color_depth=True)
        expected.pop('global_status')
    elif name == 'hash_capacity':
        settings['chroma_error'] = .005
        expected.update(global_status_bits_required=1, exact_seed_color_depth=True)
        expected.pop('global_status')
    else:
        raise ValueError('Unknown case: ' + name)
    for y in range(height):
        for x in range(width):
            part, sample_subject = 1, subject
            lightness = .5
            rgb = (lightness ** 3,) * 3
            if name == 'narrow_gradient_one_tone':
                lightness = .495 + .01 * x / (width - 1)
                rgb = (lightness ** 3,) * 3
            elif name == 'four_observed_levels':
                lightness = (.125, .375, .625, .875)[x // 8]
                rgb = (lightness ** 3,) * 3
            elif name == 'broad_gradient':
                lightness = .25 + .5 * x / (width - 1)
                rgb = (lightness ** 3,) * 3
            elif name == 'equal_l_chroma_part_subject':
                band = x // 8
                rgb = oklab_to_linear_rgb(.65, .1 if band in (0, 2) else -.1, .02)
                if band == 2:
                    part = 2
                elif band == 3:
                    sample_subject = 258
            elif name == 'unsupported_part':
                part = 255
            elif name == 'hash_capacity':
                part = y
                rgb = (.03 + .9 * x / 32., .03 + .9 * ((x * 13) % 33) / 32., .2)
            depth = 2. + x / 128. + y / 1024.
            color_depth = tuple(rgb) + (depth,)
            meta = encode_meta(sample_subject, part)
            source.append(color_depth)
            source_meta.append(meta)
            is_seed = x % 4 == 2 and y % 4 == 2
            # Non-seed color bytes deliberately contain nonzero values. They
            # must not acquire coverage or become relocated visible cells.
            seed.append(color_depth if is_seed else (.03125, .0625, .09375, 0.))
            seed_meta.append(meta if is_seed else (0., 0., 0., 0.))
    return {'name': name, 'width': width, 'height': height, 'settings': settings,
            'source_color_depth': source, 'source_meta': source_meta,
            'seed_color_depth': seed, 'seed_meta': seed_meta, 'expected': expected,
            'precision_note': 'Compare copied RGB/depth in the chosen texture format; numerical DP tolerances are separate.'}


CASE_NAMES = ('flat_constant', 'narrow_gradient_one_tone', 'four_observed_levels',
              'broad_gradient', 'equal_l_chroma_part_subject', 'unsupported_part',
              'hash_capacity')


def unity_flat_fixture(case):
    """JsonUtility supports primitive arrays, but not nested float arrays."""
    result = dict(case)
    result['arrayLayout'] = 'flat_float4_v1'
    result['settings'] = dict(case['settings'])
    result['settings'].setdefault('highlight_minimum_contrast', .025)
    for name in ('source_color_depth', 'source_meta', 'seed_color_depth', 'seed_meta'):
        result[name] = [channel for pixel in case[name] for channel in pixel]
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--case', choices=CASE_NAMES)
    parser.add_argument('--output-dir', type=Path,
                        help='Write fixture JSON files under this review folder; existing files are rejected.')
    parser.add_argument('--unity-flat', action='store_true',
                        help='Use flat float4 arrays supported by Unity JsonUtility DTOs.')
    args = parser.parse_args()
    if args.output_dir:
        if args.list:
            parser.error('--list cannot be combined with --output-dir')
        destination = args.output_dir.resolve()
        if not destination.is_relative_to(Path(__file__).resolve().parent):
            parser.error('--output-dir must stay inside the AdaptiveToneUnityReview_20260908 folder')
        names = (args.case,) if args.case else CASE_NAMES
        targets = [destination / (name + '.json') for name in names]
        existing = [str(target) for target in targets if target.exists()]
        if existing:
            parser.error('Refusing to overwrite existing fixtures: ' + ', '.join(existing))
        destination.mkdir(parents=True, exist_ok=True)
        for name, target in zip(names, targets):
            with target.open('x', encoding='utf-8') as stream:
                case = build_case(name)
                json.dump(unity_flat_fixture(case) if args.unity_flat else case, stream, allow_nan=False)
        result = {'written': [str(target) for target in targets], 'case_count': len(targets)}
    elif args.case:
        result = build_case(args.case)
        if args.unity_flat:
            result = unity_flat_fixture(result)
    else:
        result = [{'name': name, 'expected': build_case(name)['expected']} for name in CASE_NAMES]
    print(json.dumps(result, allow_nan=False))
