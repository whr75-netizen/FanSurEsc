"""Explicit feature scopes; never infer foreground, edges, or an all-image scope.

Scope construction is independent of feature detection. An enabled feature must
have an explicit scope, even when its algorithm could infer candidate pixels.
"""
from numbers import Integral
from pathlib import Path

import numpy as np
from PIL import Image


def _integer(value):
    return isinstance(value, Integral) and not isinstance(value, (bool, np.bool_))


def _shape(shape):
    if (not isinstance(shape, (list, tuple)) or len(shape) != 2 or
            any(not _integer(value) or value <= 0 for value in shape)):
        raise ValueError('shape must contain positive integer (height, width)')
    return int(shape[0]), int(shape[1])


def _keys(specification, required):
    actual = set(specification)
    if actual != set(required):
        raise ValueError('scope keys must be exactly: ' + ', '.join(sorted(required)))


def build_scope(shape, specification, base_dir=None):
    """Return an explicit bool HxW mask without resizing or inference.

    Rectangles use integer exclusive end coordinates and must have positive
    width/height. An empty rectangle list is a valid empty scope. File masks must
    be L or RGB, exactly the requested size, and strictly black/white. RGBA and
    indexed modes are rejected rather than guessing whether alpha is the scope.
    Relative paths are resolved against base_dir, or the current directory when
    it is omitted. File-reading failures propagate; no implicit fallback exists.
    """
    height, width = _shape(shape)
    if not isinstance(specification, dict):
        raise ValueError('scope specification must be a dict; no default scope exists')
    kind = specification.get('kind')
    if kind == 'all':
        _keys(specification, ('kind',))
        return np.ones((height, width), dtype=bool)
    if kind == 'rectangles':
        _keys(specification, ('kind', 'rectangles'))
        rectangles = specification['rectangles']
        if not isinstance(rectangles, (list, tuple)):
            raise ValueError('rectangles must be a sequence of four-integer rectangles')
        result = np.zeros((height, width), dtype=bool)
        for rectangle in rectangles:
            if (not isinstance(rectangle, (list, tuple)) or len(rectangle) != 4 or
                    any(not _integer(value) for value in rectangle)):
                raise ValueError('each rectangle must contain integer x0,y0,x1,y1')
            x0, y0, x1, y1 = map(int, rectangle)
            if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
                raise ValueError('rectangle must have positive area and lie inside the image')
            result[y0:y1, x0:x1] = True
        return result
    if kind == 'mask':
        _keys(specification, ('kind', 'path'))
        raw_path = specification['path']
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError('mask path must be a nonempty string')
        path = Path(raw_path)
        if not path.is_absolute() and base_dir is not None:
            path = Path(base_dir) / path
        with Image.open(path) as mask:
            if mask.mode not in ('L', 'RGB'):
                raise ValueError('mask must be L or RGB; RGBA/indexed masks are ambiguous')
            if mask.size != (width, height):
                raise ValueError('mask dimensions must exactly match the image; no resize is performed')
            pixels = np.asarray(mask)
            if mask.mode == 'L':
                if not np.all((pixels == 0) | (pixels == 255)):
                    raise ValueError('L mask values must be only 0 or 255')
                result = pixels == 255
            else:
                black = np.all(pixels == 0, axis=2)
                white = np.all(pixels == 255, axis=2)
                if not np.all(black | white):
                    raise ValueError('RGB mask pixels must be black (0,0,0) or white (255,255,255)')
                result = white
            return np.array(result, dtype=bool, copy=True)
    raise ValueError('scope kind must be rectangles, mask, or explicitly all')


def validate_feature(feature, allowed_options):
    """Return (enabled, scope_spec, options) without invoking any algorithm.

    Disabled features return (False, None, {}) and ignore scope/options content;
    unknown top-level keys and a non-bool enabled value are always rejected.
    Enabled feature scope structure is subsequently checked by build_scope once
    the image dimensions are known. Option values belong to the owning feature.
    """
    if not isinstance(feature, dict):
        raise ValueError('feature must be a dict')
    unknown = set(feature) - {'enabled', 'scope', 'options'}
    if unknown:
        raise ValueError('unknown feature keys: ' + ', '.join(sorted(map(str, unknown))))
    enabled = feature.get('enabled', False)
    if type(enabled) is not bool:
        raise ValueError('enabled must be a bool, not a number or string')
    if not enabled:
        return False, None, {}
    if 'scope' not in feature or not isinstance(feature['scope'], dict):
        raise ValueError('enabled feature requires an explicit scope dict')
    options = feature.get('options', {})
    if not isinstance(options, dict):
        raise ValueError('feature options must be a dict')
    if (not isinstance(allowed_options, (list, tuple, set, frozenset)) or
            any(not isinstance(key, str) for key in allowed_options)):
        raise ValueError('allowed_options must be a collection of option-name strings')
    unknown_options = set(options) - set(allowed_options)
    if unknown_options:
        raise ValueError('unknown feature options: ' + ', '.join(sorted(map(str, unknown_options))))
    return True, feature['scope'].copy(), options.copy()
