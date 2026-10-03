"""Single editable control block for the existing spatial-tone pipeline.

This adapter only routes values; it never changes scopes, enables features,
chooses a palette, or processes an image. Legacy feature-only configs stay valid.
"""
from copy import deepcopy
from math import isfinite
from numbers import Real

from .spatial_tones import validate_spatial_options


DEFAULT_TONE_CONTROLS = {
    'tone_error': .06,
    'chroma_error': .06,
    'contrast_retention': .65,
    'minimum_contrast': .025,
    'highlight_minimum_contrast': .025,
    'gradient_edge_threshold': .06,
    'gradient_chroma_span': .12,
}


def validate_tone_controls(controls):
    if not isinstance(controls, dict):
        raise ValueError('tone_controls must be an object')
    unknown = set(controls) - set(DEFAULT_TONE_CONTROLS) - {'spatial_options'}
    if unknown:
        raise ValueError('Unknown tone_controls: ' + ', '.join(sorted(map(str, unknown))))
    values = dict(DEFAULT_TONE_CONTROLS)
    for key in values:
        value = controls.get(key, values[key])
        if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or not 0 < value <= 1:
            raise ValueError('tone_controls.' + key + ' must be finite in (0,1]')
        values[key] = float(value)
    if 'spatial_options' in controls and not isinstance(controls['spatial_options'], dict):
        raise ValueError('tone_controls.spatial_options must be an object')
    values['spatial_options'] = validate_spatial_options(controls.get('spatial_options'))
    return values


def resolve_tone_controls(features, controls):
    """Return new effective features; refuse two conflicting setting owners."""
    values = validate_tone_controls(controls)
    if not isinstance(features, dict):
        raise ValueError('features must be an object')
    resolved = deepcopy(features)
    region = resolved.get('region_tones')
    if not isinstance(region, dict) or not isinstance(region.get('options'), dict):
        raise ValueError('tone_controls requires region_tones with explicit mode and tone_policy')
    options = region['options']
    if options.get('mode') != 'continuous' or options.get('tone_policy') != 'spatial_steps':
        raise ValueError('tone_controls requires continuous spatial_steps')
    keys = (set(DEFAULT_TONE_CONTROLS) - {'highlight_minimum_contrast'}) | {'spatial_options'}
    duplicates = set(options) & keys
    if duplicates:
        raise ValueError('Move these region_tones options into tone_controls: ' + ', '.join(sorted(duplicates)))
    options.update({key: deepcopy(values[key]) for key in keys})
    highlight = resolved.get('highlight_accents')
    if highlight is not None:
        if not isinstance(highlight, dict):
            raise ValueError('highlight_accents must be an object')
        highlight_options = highlight.setdefault('options', {})
        if not isinstance(highlight_options, dict):
            raise ValueError('highlight_accents.options must be an object')
        if set(highlight_options) & {'minimum_contrast', 'chroma_error', 'spatial_options'}:
            raise ValueError('With tone_controls, highlight thresholds belong only in tone_controls')
        highlight_options['minimum_contrast'] = values['highlight_minimum_contrast']
        # Chroma and spatial support are inherited by the dispatcher from region_tones.
    return resolved
