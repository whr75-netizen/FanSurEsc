"""Explicitly scoped, opt-in ridge thinning; not semantic line reconstruction.

Sato + measured two-sided contrast is a bounded custom heuristic, not a complete
implementation of Superpixelator or a guarantee of topology after downsampling.
Only actual, fully opaque source samples can supply the returned overlay.
"""
from numbers import Real

import numpy as np


_DEFAULTS = dict(max_width_source_px=6, min_contrast=.045,
                 min_response=.006, min_component_pixels=3)
_MAX_PIXELS = 4_194_304


def _validate(image, target_grid, scope, enabled, options):
    a = np.asarray(image)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 4 or min(a.shape[:2]) < 1:
        raise ValueError('image must be nonempty uint8 RGBA.')
    if a.shape[0] * a.shape[1] > _MAX_PIXELS:
        raise ValueError('Source exceeds the explicit 4 MP limit; no hidden resize.')
    if not isinstance(enabled, (bool, np.bool_)):
        raise ValueError('enabled must be boolean.')
    if not isinstance(target_grid, (tuple, list, np.ndarray)) or len(target_grid) != 2:
        raise ValueError('target_grid must contain integer width and height.')
    for v in target_grid:
        if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) or v < 1:
            raise ValueError('target_grid dimensions must be positive integers.')
    w, h = map(int, target_grid)
    if w > a.shape[1] or h > a.shape[0]:
        raise ValueError('Only downscaling or equal-size grids are supported.')
    if scope is None:
        if enabled:
            raise ValueError('An explicit boolean scope is required when enabled.')
    elif not isinstance(scope, np.ndarray) or scope.dtype != np.bool_ or scope.shape != a.shape[:2]:
        raise ValueError('scope must be a boolean array matching source H,W.')
    if options is not None and not isinstance(options, dict):
        raise ValueError('options must be a plain dictionary or None.')
    opt = dict(_DEFAULTS)
    if options:
        unknown = set(options) - set(opt)
        if unknown:
            raise ValueError('Unknown line options: ' + ', '.join(map(str, sorted(unknown, key=str))))
        opt.update(options)
    for key, low, high in [('max_width_source_px', 1, 32),
                           ('min_contrast', 0, 1), ('min_response', 0, 1)]:
        v = opt[key]
        if isinstance(v, (bool, np.bool_)) or not isinstance(v, Real) or not np.isfinite(v):
            raise ValueError(key + ' must be finite and numeric.')
        if not low <= v <= high or (low == 0 and v == 0):
            raise ValueError(key + ' is outside its supported positive range.')
        opt[key] = float(v)
    v = opt['min_component_pixels']
    if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) or not 1 <= v <= _MAX_PIXELS:
        raise ValueError('min_component_pixels must be a positive integer <= 4 MP.')
    opt['min_component_pixels'] = int(v)
    return a, w, h, opt


def _shift(a, dy, dx, fill):
    """Value at (y+dy,x+dx), without wraparound or invented boundary evidence."""
    out = np.full(a.shape, fill, dtype=a.dtype)
    h, w = a.shape
    y0, y1 = max(0, -dy), min(h, h - dy)
    x0, x1 = max(0, -dx), min(w, w - dx)
    if y0 < y1 and x0 < x1:
        out[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
    return out


def _cross_section(light, opaque, max_width, min_contrast, dark):
    """Nearest opposite-side contrast crossings estimate source-pixel width."""
    best = np.zeros(light.shape, np.float32)
    sign = 1 if dark else -1
    for dy, dx in ((1, 0), (0, 1), (1, 1), (1, -1)):
        step = float(np.hypot(dy, dx))
        distances = [np.zeros(light.shape, np.int16) for _ in range(2)]
        contrasts = [np.zeros(light.shape, np.float32) for _ in range(2)]
        # At most 32 source steps, independent of image/content coordinates.
        for r in range(1, int(np.ceil(max_width / step)) + 1):
            for side, direction in enumerate((-1, 1)):
                yy, xx = direction * dy * r, direction * dx * r
                contrast = sign * (_shift(light, yy, xx, 0) - light)
                hit = ((distances[side] == 0) & _shift(opaque, yy, xx, False)
                       & (contrast >= min_contrast))
                distances[side][hit] = r
                contrasts[side][hit] = contrast[hit]
        width = (distances[0] + distances[1] - 1) * step
        valid = (distances[0] > 0) & (distances[1] > 0) & (width <= max_width)
        best = np.maximum(best, np.where(valid, np.minimum(*contrasts), 0))
    return best


def normalize_lines(image, target_grid, scope, *, enabled=False, options=None):
    """Return diagnostics and a separate source-exact RGBA line overlay.

    Grid ordering is (width,height); source_xy[...,0/1] is (x,y).
    Non-line RGBA is zero and its source_xy is (-1,-1). No caller image is
    modified. Disabled mode performs validation/allocation but imports neither
    scipy nor skimage. Scope is never inferred from an apparent outline.
    """
    a, w, h, opt = _validate(image, target_grid, scope, enabled, options)
    sh, sw = a.shape[:2]
    meta = dict(method='scoped_sato_two_sided_ridge_thinning_v1', enabled=bool(enabled),
                options=opt, source_shape=list(a.shape), target_grid=[w, h],
                source_candidate_pixels=0, source_skeleton_pixels=0,
                source_components=0, target_line_pixels=0, collision_cells=0,
                target_scope_rejected_samples=0, source_exact_rgba=True,
                alpha_requirement=255, endpoint_gap_bridging=False,
                semantic_detection=False, topology_preservation_guaranteed=False,
                notes=['Custom bounded heuristic; not Superpixelator.',
                       'Equal-lightness color lines may be missed.',
                       'Thinning/projection may collapse branches or separate lines at small grids.',
                       'min_component_pixels filters candidate components, not the original image.'])
    result = dict(source_candidate=np.zeros((sh, sw), bool),
                  source_skeleton=np.zeros((sh, sw), bool),
                  target_mask=np.zeros((h, w), bool),
                  target_rgba=np.zeros((h, w, 4), np.uint8),
                  source_xy=np.full((h, w, 2), -1, np.int32),
                  collision_mask=np.zeros((h, w), bool), metadata=meta)
    if not enabled or not np.any(scope) or not np.any(a[..., 3] == 255):
        return result

    # These are deliberately lazy; missing dependencies never silently fallback.
    from scipy import ndimage as ndi
    from skimage.filters import sato
    from skimage.morphology import skeletonize
    from .palette import rgb_to_oklab

    opaque = a[..., 3] == 255
    light = rgb_to_oklab(a[..., :3].astype(np.float32) / 255)[..., 0]
    # Guidance only: ignore hidden/semitransparent RGB, without painting the
    # scope boundary black. Two-sided evidence still requires original opacity.
    if not opaque.all():
        nearest = ndi.distance_transform_edt(~opaque, return_distances=False, return_indices=True)
        light = light[tuple(nearest)]
    maximum = max(.6, min(3., opt['max_width_source_px'] / 2))
    sigmas = np.unique(np.array([.6, max(.6, maximum / 2), maximum]))
    meta['sigmas_source_px'] = sigmas.tolist()
    component_map = np.zeros((sh, sw), np.int32)
    confidence = np.zeros((sh, sw), np.float32)
    component_count = 0
    for dark in (True, False):
        response = sato(light, sigmas=sigmas, black_ridges=dark, mode='reflect')
        contrast = _cross_section(light, opaque, opt['max_width_source_px'], opt['min_contrast'], dark)
        candidate = scope & opaque & (contrast >= opt['min_contrast']) & (response >= opt['min_response'])
        labels, count = ndi.label(candidate, structure=np.ones((3, 3), bool))
        sizes = np.bincount(labels.ravel())
        keep = sizes >= opt['min_component_pixels']
        keep[0] = False
        candidate = keep[labels]
        result['source_candidate'] |= candidate
        # Process each polarity independently, preventing the two masks from
        # being interpreted as a single thick binary band before thinning.
        skeleton = skeletonize(candidate, method='zhang')
        labels, count = ndi.label(skeleton, structure=np.ones((3, 3), bool))
        if component_count + count > 65536:
            raise ValueError('Line component safety limit exceeded (65536).')
        take = skeleton & (response > confidence)
        component_map[take] = labels[take] + component_count
        confidence[take] = response[take]
        component_count += count
    skeleton = component_map > 0
    result['source_skeleton'][:] = skeleton
    meta['source_candidate_pixels'] = int(result['source_candidate'].sum())
    meta['source_skeleton_pixels'] = int(skeleton.sum())
    meta['source_components'] = int(np.unique(component_map[skeleton]).size)
    if not skeleton.any():
        return result

    sy, sx = np.nonzero(skeleton)
    # Integer form of floor((source_coordinate+.5)*target_size/source_size).
    tx = ((2 * sx + 1) * w // (2 * sw)).astype(np.int32)
    ty = ((2 * sy + 1) * h // (2 * sh)).astype(np.int32)
    center_x = np.minimum(sw - 1, ((2 * tx + 1) * sw // (2 * w)))
    center_y = np.minimum(sh - 1, ((2 * ty + 1) * sh // (2 * h)))
    allowed = scope[center_y, center_x] & scope[sy, sx]
    meta['target_scope_rejected_samples'] = int((~allowed).sum())
    sy, sx, tx, ty = (v[allowed] for v in (sy, sx, tx, ty))
    components = component_map[sy, sx]
    ids = ty.astype(np.int64) * w + tx
    if not ids.size:
        return result
    # Report collisions before any thinning chooses a winner.
    pairs = np.unique(np.column_stack((ids, components)), axis=0)
    cells, counts = np.unique(pairs[:, 0], return_counts=True)
    result['collision_mask'].ravel()[cells[counts > 1]] = True
    retained = np.zeros(ids.size, bool)
    order = np.argsort(components, kind='stable')
    cuts = np.r_[0, np.flatnonzero(np.diff(components[order])) + 1, len(order)]
    for start, stop in zip(cuts[:-1], cuts[1:]):
        selected = order[start:stop]
        xx, yy = tx[selected], ty[selected]
        x0, y0 = int(xx.min()), int(yy.min())
        patch = np.zeros((int(yy.max()) - y0 + 1, int(xx.max()) - x0 + 1), bool)
        patch[yy - y0, xx - x0] = True
        thin = skeletonize(patch, method='zhang')
        retained[selected] = thin[yy - y0, xx - x0]
    sy, sx, ids = (v[retained] for v in (sy, sx, ids))
    # Strongest measured source ridge wins; source scan order is a stable tie.
    ranking = np.lexsort((sy.astype(np.int64) * sw + sx, -confidence[sy, sx], ids))
    ranked_ids = ids[ranking]
    winners = ranking[np.r_[True, np.diff(ranked_ids) != 0]] if ranking.size else ranking
    chosen = ids[winners]
    result['target_mask'].ravel()[chosen] = True
    result['source_xy'].reshape(-1, 2)[chosen] = np.column_stack((sx[winners], sy[winners]))
    result['target_rgba'].reshape(-1, 4)[chosen] = a[sy[winners], sx[winners]]
    meta['target_line_pixels'] = int(result['target_mask'].sum())
    meta['collision_cells'] = int(result['collision_mask'].sum())
    return result
