"""Deterministic source-colour material candidates and three/four lightness steps.

Material IDs describe CIELAB chromaticity clusters, not semantic materials.
Centroids guide assignments only: every emitted visible RGB is an actual input
RGB from its assigned material candidate. Geometry and background are untouched.
"""
from __future__ import annotations

import time

import numpy as np


MAX_PIXELS = 4_000_000
MAX_SAMPLES = 32_768
MAX_MATERIALS = 32
CLUSTER_ITERATIONS = 6
MAP_CHUNK = 32_768
LIGHTNESS_BINS = 4_096
CHROMA_SEED_EPSILON = .001


def _lab(rgb):
    """Stored sRGB bytes to CIELAB, D65 reference white."""
    c = np.asarray(rgb, dtype=np.float32) / 255.0
    linear = np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
    matrix = np.array([[.4124564, .3575761, .1804375],
                       [.2126729, .7151522, .0721750],
                       [.0193339, .1191920, .9503041]], dtype=np.float32)
    xyz = linear @ matrix.T / np.array([.95047, 1.0, 1.08883], dtype=np.float32)
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz),
                 xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack((116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])), axis=-1)


def _distances(points, centers):
    # Direct differences avoid cancellation for identical float32 colours.
    da = points[:, None, 0] - centers[None, :, 0]
    db = points[:, None, 1] - centers[None, :, 1]
    return da * da + db * db


def _material_centers(chroma, materials):
    count = len(chroma)
    samples = min(MAX_SAMPLES, count)
    # Equally spaced ranks in the visible-pixel scan order; no RNG state.
    ranks = (np.arange(samples, dtype=np.int64) * count + count // 2) // samples
    points = chroma[ranks]
    mean = np.mean(points, axis=0, dtype=np.float64)
    seed = int(np.argmin(np.sum((points - mean) ** 2, axis=1)))
    centers = [points[seed].copy()]
    distance = np.sum((points - centers[0]) ** 2, axis=1)
    for _ in range(1, materials):
        farthest = int(np.argmax(distance))
        # Suppress only sub-millilab numerical differences, including neutral
        # greys whose computed a/b are not bit-exact zero in float32.
        if float(distance[farthest]) <= CHROMA_SEED_EPSILON ** 2:
            break
        centers.append(points[farthest].copy())
        np.minimum(distance, np.sum((points - centers[-1]) ** 2, axis=1), out=distance)
    centers = np.asarray(centers, dtype=np.float32)
    for _ in range(CLUSTER_ITERATIONS):
        assignment = np.argmin(_distances(points, centers), axis=1)
        weights = np.bincount(assignment, minlength=len(centers))
        for axis in (0, 1):
            sums = np.bincount(assignment, weights=points[:, axis], minlength=len(centers))
            used = weights > 0
            centers[used, axis] = sums[used] / weights[used]
        # Empty candidates keep their previous centers; they are removed only
        # after full-source assignment, with a recorded contiguous ID mapping.
    return centers, samples


def _tone_centers(lightness, levels):
    """Frequency-weighted one-dimensional Lloyd quantizer on a bounded histogram.

    Histogram means and Lloyd means are analysis values, never output colours.
    Six iterations and a 4096-bin representation bound computation independently
    of the number of source colours. This is not an exact optimal SSE partition.
    """
    bins = np.clip((lightness * ((LIGHTNESS_BINS - 1) / 100)).astype(np.int32),
                   0, LIGHTNESS_BINS - 1)
    counts = np.bincount(bins, minlength=LIGHTNESS_BINS)
    used = counts > 0
    weights = counts[used].astype(np.float64)
    values = np.bincount(bins, weights=lightness, minlength=LIGHTNESS_BINS)[used] / weights
    centers = np.linspace(float(lightness.min()), float(lightness.max()), levels)
    for _ in range(CLUSTER_ITERATIONS):
        labels = np.argmin((values[:, None] - centers[None, :]) ** 2, axis=1)
        for tone in range(levels):
            selected = labels == tone
            if selected.any():
                centers[tone] = np.dot(values[selected], weights[selected]) / weights[selected].sum()
        centers.sort()
    return centers


def build_tones(rgb, visible, levels=4, materials=12):
    """Return material/tone maps, observed-colour ramps and an unchanged-size RGB.

    ``rgb`` is uint8 HxWx3; ``visible`` is a matching boolean mask. ``levels``
    must be 3 or 4 and ``materials`` 1..32. Outside the mask material_id=-1,
    tone_id=0 and RGB remains byte identical. Alpha is not accepted or altered.
    Palette shape is Mxlevelsx3. Limited-colour or constant candidates may repeat
    representative colours: requesting four slots does not invent four tones.
    """
    if (not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8
            or rgb.ndim != 3 or rgb.shape[2] != 3 or min(rgb.shape[:2]) < 1):
        raise ValueError('rgb must be a nonempty uint8 HxWx3 array.')
    if rgb.shape[0] * rgb.shape[1] > MAX_PIXELS:
        raise ValueError('Tone reconstruction supports at most 4,000,000 source pixels; no hidden resize.')
    if not isinstance(visible, np.ndarray) or visible.dtype != np.bool_ or visible.shape != rgb.shape[:2]:
        raise ValueError('visible must be a boolean HxW array matching rgb.')
    if type(levels) is not int or levels not in (3, 4):
        raise ValueError('levels must be the integer 3 or 4.')
    if type(materials) is not int or not 1 <= materials <= MAX_MATERIALS:
        raise ValueError('materials must be an integer from 1 through 32.')
    started = time.perf_counter()
    shape = rgb.shape[:2]
    material_map = np.full(shape, -1, dtype=np.int16)
    tone_map = np.zeros(shape, dtype=np.uint8)
    # Writable C-order storage also supports strided or Fortran-order inputs;
    # a reshape of those arrays can otherwise silently write into a copy.
    result = np.array(rgb, copy=True, order='C')
    positions = np.flatnonzero(visible)
    report = {'schema': 'source-material-stepped-tones/1',
              'algorithm': 'CIELAB a/b sampled k-means + weighted histogram Lloyd lightness + observed RGB representatives',
              'requested_materials': materials, 'levels_per_candidate': levels,
              'source_dimensions': [int(rgb.shape[1]), int(rgb.shape[0])],
              'visible_pixels': int(len(positions)), 'semantic_material_recognition': False,
              'material_assignment_channels': 'CIELAB a/b only', 'rgb_averaging_emitted': False,
              'dithering': False, 'background_rgb_preserved': True,
              'sampling_limit': MAX_SAMPLES, 'cluster_iterations': CLUSTER_ITERATIONS,
              'chroma_seed_epsilon': CHROMA_SEED_EPSILON,
              'lightness_histogram_bins': LIGHTNESS_BINS,
              'tone_label_filter': 'none', 'materials': [], 'stage_seconds': {}}
    if not len(positions):
        report.update({'material_count': 0, 'sample_count': 0, 'visible_palette_size': 0,
                       'colour_bound': 0, 'elapsed_seconds': time.perf_counter() - started})
        return {'material_id': material_map, 'tone_id': tone_map,
                'palette': np.empty((0, levels, 3), np.uint8), 'rgb': result, 'report': report}

    stage = time.perf_counter()
    source = rgb.reshape(-1, 3)[positions]
    lab = _lab(source)
    centers, sample_count = _material_centers(lab[:, 1:], materials)
    report['stage_seconds']['analysis_and_clustering'] = time.perf_counter() - stage
    stage = time.perf_counter()
    assignment = np.empty(len(positions), dtype=np.int16)
    ambiguity_count = 0
    for begin in range(0, len(positions), MAP_CHUNK):
        end = min(len(positions), begin + MAP_CHUNK)
        distances = _distances(lab[begin:end, 1:], centers)
        assignment[begin:end] = np.argmin(distances, axis=1)
        if len(centers) > 1:
            two = np.partition(distances, 1, axis=1)[:, :2]
            ambiguity_count += int(np.count_nonzero(np.sqrt(two[:, 1]) - np.sqrt(two[:, 0]) < 2))
    used_centers = np.unique(assignment)
    remap = np.full(len(centers), -1, np.int16)
    remap[used_centers] = np.arange(len(used_centers), dtype=np.int16)
    assignment = remap[assignment]
    centers = centers[used_centers]
    material_map.ravel()[positions] = assignment
    report['stage_seconds']['full_material_assignment'] = time.perf_counter() - stage

    stage = time.perf_counter()
    palette = np.empty((len(centers), levels, 3), np.uint8)
    source_tones = np.empty(len(positions), dtype=np.uint8)
    output_errors = np.empty(len(positions), dtype=np.float32)
    for material, center in enumerate(centers):
        indices = np.flatnonzero(assignment == material)
        local_lab = lab[indices]
        tone_centers = _tone_centers(local_lab[:, 0], levels)
        provisional = np.argmin((local_lab[:, 0, None] - tone_centers[None, :]) ** 2, axis=1)
        chroma_error = np.sum((local_lab[:, 1:] - center) ** 2, axis=1)
        representatives = []
        for tone, light in enumerate(tone_centers):
            members = np.flatnonzero(provisional == tone)
            # Empty slots duplicate the nearest observed representative. They
            # never introduce a colour or borrow a different candidate's RGB.
            candidates = members if len(members) else np.arange(len(indices))
            score = (local_lab[candidates, 0] - light) ** 2 + chroma_error[candidates]
            representatives.append(int(candidates[int(np.argmin(score))]))
        representatives = np.asarray(representatives, dtype=np.int64)
        representatives = representatives[np.argsort(local_lab[representatives, 0], kind='stable')]
        palette[material] = source[indices[representatives]]
        palette_lab = local_lab[representatives]
        labels = np.argmin((local_lab[:, 0, None] - palette_lab[None, :, 0]) ** 2, axis=1).astype(np.uint8)
        source_tones[indices] = labels
        error = np.sqrt(np.sum((local_lab - palette_lab[labels]) ** 2, axis=1))
        output_errors[indices] = error
        report['materials'].append({'id': material, 'pixel_count': int(len(indices)),
                                    'sample_chroma_center_ab': [float(v) for v in center],
                                    'source_lightness_min': float(local_lab[:, 0].min()),
                                    'source_lightness_max': float(local_lab[:, 0].max()),
                                    'used_tone_count': int(len(np.unique(labels))),
                                    'unique_ramp_colours': int(len(np.unique(palette[material], axis=0))),
                                    'source_representative_xy': [[int(positions[indices[v]] % shape[1]),
                                                                  int(positions[indices[v]] // shape[1])]
                                                                 for v in representatives],
                                    'mean_delta_e76': float(error.mean()), 'maximum_delta_e76': float(error.max())})
    tone_map.ravel()[positions] = source_tones
    result.reshape(-1, 3)[positions] = palette[assignment, source_tones]
    used_palette_slots = np.unique(assignment.astype(np.int32) * levels + source_tones)
    final_colours = int(len(np.unique(palette.reshape(-1, 3)[used_palette_slots], axis=0)))
    if final_colours > len(centers) * levels or not np.array_equal(result[~visible], rgb[~visible]):
        raise RuntimeError('Tone palette bound or background preservation invariant failed.')
    report['stage_seconds']['tone_quantization_and_render'] = time.perf_counter() - stage
    report.update({'material_count': int(len(centers)), 'sample_count': sample_count,
                   'visible_palette_size': final_colours, 'colour_bound': int(len(centers) * levels),
                   'ambiguity_margin_delta_ab': 2, 'ambiguous_visible_pixels': ambiguity_count,
                   'mean_delta_e76': float(output_errors.mean()),
                   'maximum_delta_e76': float(output_errors.max()),
                   'elapsed_seconds': time.perf_counter() - started,
                   'limitations': ['Chroma clusters are not semantic materials; reflections can cross candidate boundaries.',
                                   'Narrow gradients and texture details can lose contrast under a finite tone budget.',
                                   'Weighted histogram Lloyd is deterministic but not globally optimal quantization.',
                                   'Tone IDs include baked shading; they are neither albedo nor normals.',
                                   'An ambiguous pixel still receives one candidate; ambiguity counts are diagnostics.']})
    return {'material_id': material_map, 'tone_id': tone_map,
            'palette': palette, 'rgb': result, 'report': report}
