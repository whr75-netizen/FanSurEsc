"""Fixed source supports for preserving one coherent lightness contrast.

This is a spatial guard for an existing color quantizer, not a segmentation or
material detector. Only pixels of one fixed chromaticity group enter the API.
The returned histograms permit checking a candidate palette without blurring it.

The default scales (2%, 4%, 8% of each bounding-box axis) look for broad
structure independently of the output grid. A half-source-pixel sigma is only a
sampling floor. Repeated floor-limited scales do not count as separate evidence.
The 35% variance gate rejects substantially averaged-away noise; 65% support
overlap requires the same bright/dark structure at two neighboring scales.
These are explicit heuristics, not guarantees of material or artistic accuracy.
"""
from numbers import Integral, Real

import numpy as np


SCALE_FRACTIONS = (.02, .04, .08)
MINIMUM_SIGMA = .5
MINIMUM_COHERENCE = .35
MINIMUM_SUPPORT_OVERLAP = .65
SUPPORT_QUANTILES = (.2, .8)
MAX_SOURCE_PIXELS = 4_194_304
MAX_BOUNDING_BOX_PIXELS = 4_194_304
MAX_COLOR_COUNT = 65_536
MAX_FILTER_PIXEL_TAPS = 8_000_000_000
GAUSSIAN_TRUNCATE = 4.


def _fraction(value, name):
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
            or not np.isfinite(value) or not 0 < value <= 1):
        raise ValueError(name + ' must be finite in (0,1].')
    return float(value)


def validate_spatial_options(options=None):
    """Return a fresh, complete JSON-safe set of source-support options.

    Input dictionaries and sequences are never mutated. Sampling floors and
    resource bounds are deliberately not configurable through these options.
    """
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise ValueError('spatial_options must be a dictionary or None')
    allowed = {'scale_fractions', 'minimum_coherence', 'minimum_support_overlap',
               'support_quantiles'}
    unknown = set(options) - allowed
    if unknown:
        raise ValueError('Unknown spatial_options: ' + ', '.join(sorted(map(str, unknown))))

    def sequence(name, default, minimum_size, maximum_size):
        values = options.get(name, default)
        if (not isinstance(values, (list, tuple, np.ndarray))
                or (isinstance(values, np.ndarray) and values.ndim != 1)
                or not minimum_size <= len(values) <= maximum_size):
            raise ValueError(name + ' must be a one-dimensional sequence of '
                             + str(minimum_size) + ' to ' + str(maximum_size) + ' numbers')
        return [_fraction(value, name) for value in values]

    scales = sequence('scale_fractions', SCALE_FRACTIONS, 2, 6)
    if scales[-1] > .5 or any(left >= right for left, right in zip(scales, scales[1:])):
        raise ValueError('scale_fractions must be strictly increasing values in (0,.5]')
    quantiles = sequence('support_quantiles', SUPPORT_QUANTILES, 2, 2)
    if not 0 < quantiles[0] < .5 < quantiles[1] < 1:
        raise ValueError('support_quantiles must satisfy 0 < low < .5 < high < 1')
    return {
        'scale_fractions': scales,
        'minimum_coherence': _fraction(options.get('minimum_coherence', MINIMUM_COHERENCE),
                                       'minimum_coherence'),
        'minimum_support_overlap': _fraction(
            options.get('minimum_support_overlap', MINIMUM_SUPPORT_OVERLAP),
            'minimum_support_overlap'),
        'support_quantiles': quantiles,
    }


def _inputs(lightness, color_indices, positions, color_count):
    lightness, color_indices, positions = map(np.asarray, (lightness, color_indices, positions))
    if (lightness.ndim != 1 or not 1 <= len(lightness) <= MAX_SOURCE_PIXELS
            or lightness.dtype.kind not in 'iuf' or not np.all(np.isfinite(lightness))):
        raise ValueError('lightness must be a nonempty finite numeric vector within the source-pixel bound')
    if (isinstance(color_count, (bool, np.bool_)) or not isinstance(color_count, Integral)
            or not 1 <= color_count <= MAX_COLOR_COUNT):
        raise ValueError('color_count must be a positive integer within the color resource bound')
    if (color_indices.shape != lightness.shape or color_indices.dtype.kind not in 'iu'
            or np.any(color_indices < 0) or np.any(color_indices >= color_count)):
        raise ValueError('color_indices must be an integer vector in [0,color_count), one per pixel')
    if positions.shape != (len(lightness), 2) or positions.dtype.kind not in 'iu':
        raise ValueError('positions must be an integer Nx2 array of (y,x) coordinates')
    # Python integers make subtraction safe even for large translated coordinates.
    origin = [int(positions[:, axis].min()) for axis in (0, 1)]
    shape = tuple(int(positions[:, axis].max()) - origin[axis] + 1 for axis in (0, 1))
    if shape[0] * shape[1] > MAX_BOUNDING_BOX_PIXELS:
        raise ValueError('spatial bounding-box resource bound exceeded; no resize or coordinate clipping is performed')
    coordinates = np.column_stack([
        (positions[:, axis] - origin[axis]).astype(np.int64) for axis in (0, 1)])
    flat = coordinates[:, 0] * shape[1] + coordinates[:, 1]
    if len(np.unique(flat)) != len(flat):
        raise ValueError('positions must be unique; duplicate pixels cannot contribute twice')
    lightness = lightness.astype(np.float64)
    if np.any(lightness < 0) or np.any(lightness > 1):
        raise ValueError('lightness must be in [0,1]')
    return lightness, color_indices.astype(np.int64), flat, shape


def build_spatial_constraints(lightness, color_indices, positions, color_count, *,
                              contrast_retention=.65, minimum_contrast=.025,
                              return_supports=False, spatial_options=None):
    """Return at most one contrast constraint and compact JSON-safe diagnostics.

    For each constraint, dot(coefficients, candidate_L_per_input_color) must be
    at least minimum_contrast. The supports remain fixed to the source pixels.
    Coordinates outside the input mask never contribute lightness or support.
    A single broad persistent contrast is protected, not every local gradient.
    When requested, a third return value contains the selected input-pixel masks
    (or None). These arrays are kept separate from the JSON-safe metadata.
    spatial_options only changes the explicitly supplied source-support gates
    and scales; omitting it preserves the original defaults.
    """
    if not isinstance(return_supports, (bool, np.bool_)):
        raise ValueError('return_supports must be boolean')
    contrast_retention = _fraction(contrast_retention, 'contrast_retention')
    minimum_contrast = _fraction(minimum_contrast, 'minimum_contrast')
    options = validate_spatial_options(spatial_options)
    lightness, color_indices, flat, shape = _inputs(
        lightness, color_indices, positions, color_count)
    raw_variance = float(np.var(lightness))
    metadata = {
        'method': 'masked-source-multiscale-support-contrast/1',
        'source_pixel_count': len(lightness), 'bounding_box_size': list(shape),
        'scale_units': 'fraction of each source group bounding-box axis; output grid unused',
        'scale_fractions': options['scale_fractions'], 'sampling_sigma_floor': MINIMUM_SIGMA,
        'support_quantiles': options['support_quantiles'],
        'minimum_coherence_ratio': options['minimum_coherence'],
        'minimum_support_overlap': options['minimum_support_overlap'],
        'required_persistent_scales': 2, 'minimum_source_contrast': minimum_contrast,
        'contrast_retention': contrast_retention, 'source_variance_l': raw_variance,
        'source_mean_l': float(np.mean(lightness)), 'scales': [],
        'constraint_count': 0, 'bypass_reason': None,
        'resource_limits': {
            'source_pixels': MAX_SOURCE_PIXELS, 'bounding_box_pixels': MAX_BOUNDING_BOX_PIXELS,
            'color_count': MAX_COLOR_COUNT, 'filter_pixel_taps': MAX_FILTER_PIXEL_TAPS},
        'limitations': [
            'Heuristic structure confidence; not material recognition or artistic approval.',
            'Thin structures and sparse masks can lack reliable multiscale support.',
            'Source enlargement invariance is not guaranteed at the sampling floor.'],
    }
    def result(constraints, supports=None):
        return ((constraints, metadata, supports) if return_supports
                else (constraints, metadata))

    if raw_variance <= 1e-14 or float(np.ptp(lightness)) < minimum_contrast:
        metadata['bypass_reason'] = 'insufficient_source_lightness_contrast'
        return result([])

    scale_specs, filter_pixel_taps = [], 0
    previous_sigma = None
    for fraction in options['scale_fractions']:
        sigma = tuple(max(MINIMUM_SIGMA, size * fraction) for size in shape)
        if sigma == previous_sigma:
            metadata['scales'].append({'fraction': fraction, 'sigma': list(sigma),
                                       'bypass_reason': 'duplicate_sampling_floor_scale'})
            continue
        previous_sigma = sigma
        # scipy's separable implementation filters mask and masked lightness.
        taps = sum(2 * int(GAUSSIAN_TRUNCATE * value + .5) + 1 for value in sigma)
        filter_pixel_taps += 2 * shape[0] * shape[1] * taps
        scale_specs.append((fraction, sigma))
    if filter_pixel_taps > MAX_FILTER_PIXEL_TAPS:
        raise ValueError('spatial filter resource bound exceeded; no resize or forced support is performed')
    metadata['estimated_filter_pixel_taps'] = filter_pixel_taps
    if len(scale_specs) < 2:
        metadata['bypass_reason'] = 'fewer_than_two_distinct_source_scales'
        return result([])

    from scipy.ndimage import gaussian_filter

    mask = np.zeros(shape, np.float64)
    masked_lightness = np.zeros(shape, np.float64)
    mask.ravel()[flat] = 1.
    masked_lightness.ravel()[flat] = lightness
    previous_support, selected = None, None
    for fraction, sigma in scale_specs:
        normalization = gaussian_filter(mask, sigma, mode='constant', cval=0.,
                                        truncate=GAUSSIAN_TRUNCATE)
        numerator = gaussian_filter(masked_lightness, sigma, mode='constant', cval=0.,
                                    truncate=GAUSSIAN_TRUNCATE)
        # Every queried location contributes its own positive Gaussian center.
        smooth = numerator.ravel()[flat] / normalization.ravel()[flat]
        coherence = float(np.var(smooth) / raw_variance)
        low_level, high_level = np.quantile(smooth, options['support_quantiles'])
        low, high = smooth <= low_level, smooth >= high_level
        source_contrast = float(np.mean(lightness[high]) - np.mean(lightness[low]))
        report = {
            'fraction': fraction, 'sigma': list(sigma), 'coherence_ratio': coherence,
            'source_contrast_l': source_contrast,
            'support_count': {'low': int(low.sum()), 'high': int(high.sum())},
            'bypass_reason': None,
        }
        metadata['scales'].append(report)
        if coherence < options['minimum_coherence']:
            report['bypass_reason'] = 'lightness_variance_does_not_survive_smoothing'
            previous_support = None
            continue
        if source_contrast < minimum_contrast or np.any(low & high):
            report['bypass_reason'] = 'insufficient_disjoint_support_contrast'
            previous_support = None
            continue
        current = (low, high, source_contrast, report)
        if previous_support is not None:
            prev_low, prev_high, _, prev_report = previous_support
            low_overlap = float(np.count_nonzero(low & prev_low) / min(low.sum(), prev_low.sum()))
            high_overlap = float(np.count_nonzero(high & prev_high) / min(high.sum(), prev_high.sum()))
            report['previous_scale_support_overlap'] = {'low': low_overlap, 'high': high_overlap}
            if min(low_overlap, high_overlap) >= options['minimum_support_overlap']:
                # Keep one coarsest persistent support pair, avoiding a separate
                # constraint for every scale or each small source gradient.
                selected = current
                report['persistent_with_scale_fraction'] = prev_report['fraction']
        previous_support = current

    if selected is None:
        metadata['bypass_reason'] = 'no_coherent_contrast_persistent_across_two_scales'
        return result([])
    low, high, source_contrast, report = selected
    coefficients = np.bincount(color_indices[high], minlength=color_count).astype(np.float64) / high.sum()
    coefficients -= np.bincount(color_indices[low], minlength=color_count) / low.sum()
    required = source_contrast * contrast_retention
    metadata.update(constraint_count=1, selected_scale_fraction=report['fraction'],
                    selected_source_contrast_l=source_contrast,
                    required_output_contrast_l=required,
                    selected_support_count=report['support_count'])
    return result([{'coefficients': coefficients, 'minimum_contrast': required}],
                  {'low': low.copy(), 'high': high.copy()} if return_supports else None)
