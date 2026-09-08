"""Explicitly scoped pixel operations. No automatic 'the image has outlines' mode.

The dispatcher owns only ordering. Each feature is opt-in and requires its own
scope. Spatial scopes are asset configuration, never character/body-part tests.
No RGB averaging, invented ink color, or generative reconstruction is used.
"""
from __future__ import annotations
import numpy as np
from .palette import _image, rgb_to_oklab, scaled_grid
from .feature_scopes import build_scope, validate_feature

FEATURES = {
    'mask_cleanup': ('mode', 'seeds', 'max_distance', 'max_chroma_distance'),
    'region_colors': ('colors', 'iterations'),
    'region_tones': ('tones', 'min_retained_tone_delta_l', 'mode', 'color_error',
                     'gradient_edge_threshold', 'gradient_chroma_span'),
    'cell_sampling': ('coverage', 'method', 'color_edge_threshold'),
    'line_normalization': ('max_width_source_px', 'min_contrast',
                           'min_response', 'min_component_pixels', 'mode', 'color_edge_threshold', 'silhouette_coverage', 'fill_source_guard'),
}


def _integer(value, name, low, high):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in [{low},{high}].')
    return int(value)


def _real(value, name, low, high):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float)) or not np.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{name} must be finite in [{low},{high}].')
    return float(value)


def center_indices(shape, grid):
    h, w = shape
    W, H = grid
    x = np.minimum(((np.arange(W) + .5) * w / W).astype(int), w - 1)
    y = np.minimum(((np.arange(H) + .5) * h / H).astype(int), h - 1)
    return y, x


def center_sample(image, grid):
    y, x = center_indices(image.shape[:2], grid)
    return image[y[:, None], x[None, :]].copy()


def cleanup_mask(image, scope, mode='erase', seeds=None, max_distance=.15, max_chroma_distance=.025):
    """Explicit erase or seeded, color-constrained connected selection.

    Seed positions belong to this asset's selection config, not the algorithm.
    Color similarity alone never deletes unrelated islands or the whole image.
    """
    if mode not in ('erase', 'color_connected'):
        raise ValueError('mask cleanup mode must be erase or color_connected.')
    if mode == 'erase':
        if seeds is not None:
            raise ValueError('Seeds belong only to color_connected mode.')
        return scope.copy()
    max_distance = _real(max_distance, 'max_distance', .001, .5)
    max_chroma_distance = _real(max_chroma_distance, 'max_chroma_distance', .001, .5)
    if not isinstance(seeds, (list, tuple)) or not 1 <= len(seeds) <= 64:
        raise ValueError('color_connected requires 1..64 explicit source-coordinate seeds.')
    from scipy.ndimage import label
    lab = rgb_to_oklab(image[..., :3] / 255.)
    valid = scope & (image[..., 3] == 255)
    erase = np.zeros(scope.shape, bool)
    for seed in seeds:
        if not isinstance(seed, (list, tuple)) or len(seed) != 2:
            raise ValueError('Each seed must be integer [x,y].')
        x = _integer(seed[0], 'seed x', 0, image.shape[1]-1)
        y = _integer(seed[1], 'seed y', 0, image.shape[0]-1)
        if not valid[y,x]:
            raise ValueError('Seed must be opaque and inside its explicit scope.')
        d = lab - lab[y,x]
        candidate = valid & ((d*d).sum(2) <= max_distance**2) & ((d[...,1:]*d[...,1:]).sum(2) <= max_chroma_distance**2)
        labels, _ = label(candidate, structure=np.ones((3,3), bool))
        erase |= labels == labels[y,x]
    return erase


def source_palette(image, scope, colors=64, iterations=3):
    """Weighted farthest seeding + observed-color representatives in Oklab.

    Means are used only to choose representatives. Every output RGB is an
    actually observed opaque RGB. Rare colors have sqrt-frequency influence,
    not linear frequency, so a small accent is not automatically swallowed.
    This is color clustering, not semantic/material segmentation.
    """
    colors = _integer(colors, 'colors', 2, 256)
    iterations = _integer(iterations, 'iterations', 0, 8)
    selected = scope & (image[..., 3] == 255)
    out = image.copy()
    if not selected.any():
        return out, {'palette': [], 'changed_pixels': 0}
    values, inverse, counts = np.unique(image[..., :3][selected], axis=0,
                                         return_inverse=True, return_counts=True)
    lab = rgb_to_oklab(values / 255.)
    k = min(colors, len(values))
    if k == len(values):
        return out, {'palette': values.tolist(), 'changed_pixels': 0}
    seeds = [int(np.argmax(counts))]
    distance = np.full(len(values), np.inf)
    # sqrt(count) in the squared-distance objective keeps minority hues visible.
    weight = np.sqrt(counts.astype(float))
    for _ in range(1, k):
        distance = np.minimum(distance, ((lab - lab[seeds[-1]]) ** 2).sum(1))
        score = distance * weight
        score[seeds] = -1
        seeds.append(int(np.argmax(score)))
    seeds = np.asarray(seeds)
    def assign():
        # Bounded chunks avoid a source-pixels x colors x channels allocation.
        labels = np.empty(len(values), np.int32)
        for start in range(0, len(values), 4096):
            d = ((lab[start:start+4096, None] - lab[seeds][None]) ** 2).sum(2)
            labels[start:start+4096] = np.argmin(d, axis=1)
        return labels
    for _ in range(iterations):
        labels = assign()
        for index in range(k):
            members = np.flatnonzero(labels == index)
            if len(members):
                mean = np.average(lab[members], axis=0, weights=weight[members])
                seeds[index] = members[np.argmin(((lab[members] - mean) ** 2).sum(1))]
    labels = assign()
    out[..., :3][selected] = values[seeds[labels[inverse]]]
    return out, {'palette': values[seeds].tolist(),
                 'changed_pixels': int(np.any(out != image, axis=2).sum()),
                 'method': 'observed-RGB Oklab representatives; no RGB averaging'}


def _cell_edges(length, target):
    # Disjoint ownership of source pixel centers, same convention as projection.
    return np.clip(np.ceil(np.arange(target + 1) * length / target - .5).astype(int), 0, length)


def _pick_sample(block, allowed):
    """Area vote, then the actual source pixel nearest the cell center. No blend."""
    ys, xs = np.nonzero(allowed)
    if not len(ys):
        return None
    rgb = block[ys, xs, :3]
    _, inverse, counts = np.unique(rgb, axis=0, return_inverse=True, return_counts=True)
    score = counts[inverse]
    distance = (ys - (block.shape[0] - 1) / 2.) ** 2 + (xs - (block.shape[1] - 1) / 2.) ** 2
    rank = np.lexsort((xs, ys, distance, -score))
    chosen = rank[0]
    return block[ys[chosen], xs[chosen]].copy(), int(ys[chosen]), int(xs[chosen])


def _pick_color(block, allowed):
    picked = _pick_sample(block, allowed)
    return None if picked is None else picked[0]


def sample_scoped(image, grid, scope, *, coverage=.5, return_source_xy=False,
                  method='rgb_vote', source_guide=None, color_edge_threshold=.08):
    coverage = _real(coverage, 'coverage', .01, 1.)
    if method not in ('rgb_vote', 'source_regions'):
        raise ValueError('Sampling method must be rgb_vote or source_regions.')
    lab = None
    if method == 'source_regions':
        from .source_sampling import pick_region_sample
        if source_guide is None:
            raise ValueError('source_regions needs an explicit raw source_guide.')
        guide = np.asarray(source_guide)
        if guide.dtype != np.uint8 or guide.shape != image.shape or not np.array_equal(guide[..., 3], image[..., 3]):
            raise ValueError('source_guide must match image shape, uint8 and alpha.')
        color_edge_threshold = _real(color_edge_threshold, 'color_edge_threshold', .000001, 2.)
        lab = rgb_to_oklab(guide[..., :3] / 255.)
    out = center_sample(image, grid)
    cy, cx = center_indices(image.shape[:2], grid)
    xx, yy = np.meshgrid(cx, cy)
    source_xy = np.stack([xx, yy], axis=2)
    target_scope = center_sample(scope, grid)
    ex = _cell_edges(image.shape[1], grid[0])
    ey = _cell_edges(image.shape[0], grid[1])
    for ty, tx in zip(*np.nonzero(target_scope)):
        ys, xs = slice(ey[ty], ey[ty+1]), slice(ex[tx], ex[tx+1])
        block = image[ys, xs]
        # Source samples also require scope, not just the target's center.
        eligible = scope[ys, xs]
        opaque = (block[..., 3] == 255) & eligible
        if not eligible.any():
            continue
        if opaque.sum() / eligible.sum() < coverage:
            out[ty, tx] = 0
            source_xy[ty, tx] = -1
        else:
            if method == 'source_regions':
                center = ((ty + .5) * image.shape[0] / grid[1] - .5 - ey[ty],
                          (tx + .5) * image.shape[1] / grid[0] - .5 - ex[tx])
                py, px = pick_region_sample(lab[ys, xs], opaque, center, color_edge_threshold)
                picked = block[py, px]
            else:
                picked, py, px = _pick_sample(block, opaque)
            out[ty, tx] = picked
            source_xy[ty, tx] = [ex[tx]+px, ey[ty]+py]
    return (out, source_xy) if return_source_xy else out


def compose_lines(base, source, line_result, scope, grid, base_source_xy=None):
    """One replace pass, not an extra outline piled over the old one.

    Non-centerline pixels are replaced only if that SAME source cell contains
    an opaque non-line sample. Fully covered cells are retained, not inpainted
    with guessed body/cloth color. Thus strict 1px width is not guaranteed.
    """
    out = base.copy()
    active = center_sample(scope, grid)
    line = line_result['target_mask'] & active & (base[..., 3] == 255)
    collision = line_result['collision_mask']
    line &= ~collision
    support = line_result['source_candidate']
    if base_source_xy is None:
        cy, cx = center_indices(source.shape[:2], grid)
        xx, yy = np.meshgrid(cx, cy)
        base_source_xy = np.stack([xx, yy], axis=2)
    valid_xy = np.all(base_source_xy >= 0, axis=2)
    hit = np.zeros(active.shape, bool)
    xy = base_source_xy[valid_xy]
    hit[valid_xy] = support[xy[:,1], xy[:,0]]
    hit &= active & (base[..., 3] == 255) & ~line
    ex, ey = _cell_edges(source.shape[1], grid[0]), _cell_edges(source.shape[0], grid[1])
    replaced, unresolved = 0, 0
    for ty, tx in zip(*np.nonzero(hit & ~collision)):
        ys, xs = slice(ey[ty], ey[ty+1]), slice(ex[tx], ex[tx+1])
        block = source[ys, xs]
        allowed = (block[..., 3] == 255) & scope[ys, xs] & ~support[ys, xs]
        chosen = _pick_color(block, allowed)
        if chosen is None:
            unresolved += 1
        else:
            out[ty, tx] = chosen
            replaced += 1
    ty, tx = np.nonzero(line)
    xy = line_result['source_xy'][ty, tx]
    if len(ty):
        if (xy < 0).any() or not scope[xy[:, 1], xy[:, 0]].all():
            raise RuntimeError('Line provenance escaped the selected source scope.')
        out[ty, tx] = source[xy[:, 1], xy[:, 0]]
    return out, {'painted_cells': len(ty), 'replaced_mixed_support_cells': replaced,
                 'unresolved_full_support_cells': unresolved,
                 'skipped_collision_cells': int(collision.sum())}


def normalize_triggered(image, base_grid, scale='1.0', features=None, *, base_dir=None,
                        reference=None):
    """Return native RGBA plus explicit masks/stage snapshots for reproducibility."""
    image = _image(image)
    if image.shape[2] != 4:
        raise ValueError('This pipeline requires RGBA; no implicit alpha generation.')
    if not np.isin(image[..., 3], [0, 255]).all():
        raise ValueError('Input alpha must be binary. Choose an explicit alpha preprocessing method first.')
    if image.shape[0] * image.shape[1] > 4_194_304:
        raise ValueError('Trigger pipeline limit is 4 megapixels; no hidden resize.')
    grid = scaled_grid(base_grid, scale)
    if grid[0] > image.shape[1] or grid[1] > image.shape[0]:
        raise ValueError('Native upscaling is not supported; use nearest preview zoom.')
    features = {} if features is None else features
    if not isinstance(features, dict) or set(features) - set(FEATURES):
        raise ValueError('Unknown feature. Supported: ' + ', '.join(FEATURES))
    config, masks, metadata = {}, {}, {}
    for name, allowed in FEATURES.items():
        enabled, specification, options = validate_feature(features.get(name, {}), allowed)
        if enabled:
            masks[name] = build_scope(image.shape[:2], specification, base_dir=base_dir)
            config[name] = options
        metadata[name] = {'enabled': enabled, 'scope_pixels': int(masks[name].sum()) if enabled else 0}
    if 'region_tones' in config:
        if 'region_colors' in config:
            raise ValueError('region_tones and region_colors are alternative color contracts; enable only one.')
        if reference is None:
            raise ValueError('region_tones requires an explicit reference image; pass the source itself for a source palette.')
        if config.get('cell_sampling', {}).get('method') != 'source_regions':
            raise ValueError('region_tones requires cell_sampling.method=source_regions to preserve raw-source ownership.')
        if 'line_normalization' in config:
            raise ValueError('region_tones with line_normalization is not validated; no implicit line/fill substitution is allowed.')
    baseline = center_sample(image, grid)
    work = image.copy()
    if 'mask_cleanup' in config:
        erase = cleanup_mask(work, masks['mask_cleanup'], **config['mask_cleanup'])
        metadata['mask_cleanup']['erased_opaque_pixels'] = int(((work[..., 3] == 255) & erase).sum())
        work[erase] = 0
    cleaned = work.copy()
    line_result, line_geometry, line_render = None, None, None
    if 'line_normalization' in config:
        from .line_triggers import normalize_lines
        line_mode = config['line_normalization'].get('mode','post')
        if line_mode not in ('post','line_first'):
            raise ValueError('line mode must be post or line_first.')
        if line_mode == 'post' and ({'color_edge_threshold','silhouette_coverage','fill_source_guard'} & set(config['line_normalization'])):
            raise ValueError('color_edge_threshold/silhouette_coverage/fill_source_guard belong only to line_first mode.')
        line_options = {k:v for k,v in config['line_normalization'].items()
                        if k not in ('mode','color_edge_threshold','silhouette_coverage','fill_source_guard')}
        # Geometry is taken from untouched (apart from explicit erase) RGB,
        # before either palette selection or the ordinary color sampler.
        line_result = normalize_lines(cleaned, grid, masks['line_normalization'], enabled=True,
                                      options=line_options)
        if line_mode == 'line_first':
            from .line_first import prepare_line_geometry
            line_geometry = prepare_line_geometry(cleaned, grid, masks['line_normalization'], line_result,
                coverage=config['line_normalization'].get('silhouette_coverage',.5),
                deleted_mask=erase if 'mask_cleanup' in config else None,
                color_edge_threshold=config['line_normalization'].get('color_edge_threshold',.08),
                fill_source_guard=config['line_normalization'].get('fill_source_guard',False))
    if 'region_colors' in config:
        work, meta = source_palette(work, masks['region_colors'], **config['region_colors'])
        metadata['region_colors'].update(meta)
    tonal_result = None
    if 'region_tones' in config:
        from .boundary_pipeline import prepare_region_tones
        selected = cleaned.copy()
        selected[~masks['region_tones']] = 0
        # Only colors change. Ownership always continues to read cleaned raw RGB.
        tonal_result = prepare_region_tones(selected, reference, base_grid,
                                             **config['region_tones'])
        work[masks['region_tones']] = tonal_result['flat_image'][masks['region_tones']]
        metadata['region_tones'].update(tonal_result['metadata'])
    colors_source = work.copy()
    if 'cell_sampling' in config:
        out, sampling_xy = sample_scoped(work, grid, masks['cell_sampling'],
                                         return_source_xy=True, source_guide=cleaned, **config['cell_sampling'])
        metadata['cell_sampling']['method'] = config['cell_sampling'].get('method', 'rgb_vote')
        metadata['cell_sampling']['palette_independent_coordinates'] = config['cell_sampling'].get('method') == 'source_regions'
    else:
        out = center_sample(work, grid)
        cy, cx = center_indices(work.shape[:2], grid)
        xx, yy = np.meshgrid(cx, cy)
        sampling_xy = np.stack([xx, yy], axis=2)
    before_lines = out.copy()
    if 'line_normalization' in config:
        if line_geometry is None:
            out, composition = compose_lines(out, work, line_result, masks['line_normalization'], grid, sampling_xy)
        else:
            from .line_first import render_line_geometry
            line_render = render_line_geometry(line_geometry, work)
            target_scope = center_sample(masks['line_normalization'],grid)
            out[target_scope] = line_render['image'][target_scope]
            # Unresolved/collision cells keep the already processed base colors,
            # rather than restoring hundreds of raw photographic RGB values.
            fallback = target_scope & (line_geometry['unresolved_mask'] | line_geometry['collision_mask'])
            out[fallback] = before_lines[fallback]
            composition = dict(line_render['metadata'])
            composition['integration_fallback_stage'] = 'pre-line palette/cell output'
            composition['integration_fallback_cells'] = int(fallback.sum())
        metadata['line_normalization'].update(line_result['metadata'])
        metadata['line_normalization']['mode'] = line_mode
        metadata['line_normalization']['composition'] = composition
    if 'mask_cleanup' in config:
        # Explicit deletion wins over later coverage votes / line projection.
        # Source-to-target mask projection uses the same cell-center convention.
        blocked = center_sample(erase, grid)
        out[blocked] = 0
        metadata['mask_cleanup']['blocked_target_cells'] = int(blocked.sum())
    # OFF means byte identity at the same grid, including hidden RGB.
    # With processing enabled, transparent RGB is intentionally cleared inside
    # the union of selected scopes only, never on unrelated image regions.
    touched = np.zeros(image.shape[:2], bool)
    for mask in masks.values():
        touched |= mask
    target_touched = center_sample(touched, grid)
    out[(out[..., 3] == 0) & target_touched] = 0
    if not np.array_equal(out[~target_touched], baseline[~target_touched]):
        raise RuntimeError('Feature changes escaped their selected target scopes.')
    return {'image': out, 'baseline': baseline, 'cleaned_source': cleaned,
            'colors_source': colors_source, 'before_lines': before_lines,
            'region_tones_result': tonal_result,
            'scopes': masks, 'line_result': line_result,
            'line_geometry': line_geometry, 'line_render': line_render,
            'sampling_source_xy': sampling_xy,
            'erase_mask': erase if 'mask_cleanup' in config else np.zeros(image.shape[:2],bool),
            'metadata': {'grid': list(grid), 'base_grid': list(base_grid), 'scale': str(scale),
                         'features': metadata, 'changed_target_cells': int(np.any(out != baseline, axis=2).sum()),
                         'limitations': ['Color regions are not semantic parts.',
                            'Full-support line cells are not guessed or inpainted.',
                            'Downscaling cannot guarantee topology or lost detail recovery.']}}
