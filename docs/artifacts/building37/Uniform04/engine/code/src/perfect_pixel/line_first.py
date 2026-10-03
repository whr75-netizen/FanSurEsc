"""Experimental raw-geometry-first region fill, with immutable projected lines.

This is a bounded custom combination of color-connected components and marker
watershed, not semantic segmentation, Superpixelator, or missing-line recovery.
Preparation reads only raw RGBA; rendering cannot change prepared ownership.
"""
from numbers import Real

import numpy as np

from .palette import rgb_to_oklab


MAX_PIXELS = 4_194_304
MAX_REGIONS = 262_144


def _rgba(value, name):
    a = np.asarray(value)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 4 or min(a.shape[:2]) < 1:
        raise ValueError(name + ' must be nonempty uint8 RGBA.')
    if a.shape[0] * a.shape[1] > MAX_PIXELS:
        raise ValueError('Explicit 4 MP source/target limit; no hidden resize.')
    if not np.all((a[..., 3] == 0) | (a[..., 3] == 255)):
        raise ValueError(name + ' must have binary alpha, 0 or 255.')
    return a


def _mask(a, shape, name):
    if not isinstance(a, np.ndarray) or a.dtype != np.bool_ or a.shape != shape:
        raise ValueError(name + ' must be a boolean mask of shape ' + str(shape))
    return a


def _grid(grid, shape):
    if not isinstance(grid, (tuple, list, np.ndarray)) or len(grid) != 2:
        raise ValueError('grid must contain integer (width,height).')
    if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) or v < 1 for v in grid):
        raise ValueError('Grid dimensions must be positive integers.')
    w, h = map(int, grid)
    if w > shape[1] or h > shape[0] or w * h > MAX_PIXELS:
        raise ValueError('Only downscaling/equal-size grids up to 4 MP are supported.')
    return w, h


def _number(v, name, low, high):
    if isinstance(v, (bool, np.bool_)) or not isinstance(v, Real) or not np.isfinite(v) or not low <= v <= high:
        raise ValueError(name + ' must be finite in ' + str((low, high)))
    return float(v)


def _centers(shape, grid):
    sh, sw = shape
    w, h = grid
    return ((2 * np.arange(h) + 1) * sh // (2 * h),
            (2 * np.arange(w) + 1) * sw // (2 * w))


def _edges(length, target):
    # ceil(t*length/target-.5), without floating-point rounding.
    t = np.arange(target + 1, dtype=np.int64)
    return np.clip((2 * t * length - target + 2 * target - 1) // (2 * target), 0, length)


def _source_regions(lab, eligible, threshold):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    labels = np.full(eligible.shape, -1, np.int32)
    count = int(eligible.sum())
    if not count:
        return labels, 0
    labels[eligible] = np.arange(count, dtype=np.int32)
    rows, cols = [], []
    for before, after in ((np.s_[:-1, :], np.s_[1:, :]),
                          (np.s_[:, :-1], np.s_[:, 1:])):
        linked = eligible[before] & eligible[after]
        linked &= np.sum((lab[before] - lab[after]) ** 2, axis=2) <= threshold ** 2
        rows.append(labels[before][linked])
        cols.append(labels[after][linked])
    row, col = np.concatenate(rows), np.concatenate(cols)
    graph = coo_matrix((np.ones(row.size, bool), (row, col)), shape=(count, count)).tocsr()
    number, components = connected_components(graph, directed=False)
    if number > MAX_REGIONS:
        raise ValueError('Color-connected region limit exceeded (262144); no automatic merging.')
    labels[eligible] = components.astype(np.int32)
    return labels, int(number)


def _supported_expand(markers, energy, mask, lab, opaque, labels, ex, ey, grid, threshold):
    """Priority flood that cannot introduce an unsupported color into a cell.

    A propagated owner must have a nearest raw-region sample compatible with
    an opaque raw sample in the destination cell. Failed proposals do not own
    the cell; other neighboring regions may still compete. No global inpaint.
    """
    import heapq
    from scipy.spatial import cKDTree

    expanded = markers.copy()
    heap, attempted, trees = [], set(), {}
    flat = np.flatnonzero(labels.ravel() >= 0)
    flat = flat[np.argsort(labels.ravel()[flat], kind='stable')]
    ordered = labels.ravel()[flat]
    counter, rejected = 0, 0

    def propose(y, x, owner, cost):
        nonlocal counter
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if not (0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1]):
                continue
            if not mask[ny, nx] or expanded[ny, nx]:
                continue
            key = (ny, nx, owner)
            if key in attempted:
                continue
            heapq.heappush(heap, (max(cost, float(energy[ny, nx])), counter, ny, nx, owner))
            counter += 1

    for y, x in zip(*np.nonzero(markers)):
        propose(int(y), int(x), int(markers[y, x]), float(energy[y, x]))
    while heap:
        cost, _, y, x, owner = heapq.heappop(heap)
        key = (y, x, owner)
        if expanded[y, x] or key in attempted:
            continue
        attempted.add(key)
        if owner not in trees:
            lo = np.searchsorted(ordered, owner - 1, side='left')
            hi = np.searchsorted(ordered, owner - 1, side='right')
            yy, xx = np.divmod(flat[lo:hi], labels.shape[1])
            coords = np.column_stack((yy, xx))
            trees[owner] = (coords, cKDTree(coords))
        coords, tree = trees[owner]
        query = ((y + .5) * labels.shape[0] / grid[1] - .5,
                 (x + .5) * labels.shape[1] / grid[0] - .5)
        _, index = tree.query(query, k=1)
        sy, sx = coords[index]
        ys, xs = slice(ey[y], ey[y + 1]), slice(ex[x], ex[x + 1])
        raw = lab[ys, xs][opaque[ys, xs]]
        if not len(raw) or np.min(np.sum((raw - lab[sy, sx]) ** 2, axis=1)) > threshold ** 2:
            rejected += 1
            continue
        expanded[y, x] = owner
        propose(y, x, owner, cost)
    return expanded, rejected


def prepare_line_geometry(source, grid, scope, line_result, *, coverage=.5,
                          deleted_mask=None, color_edge_threshold=.08, fill_source_guard=False):
    """Prepare raw ownership and line barriers without applying any palette.

    Source labels are zero-based/-1 excluded; marker values are owner+1/0 empty.
    All source candidates are excluded from fill, even if not projected as lines.
    Region labels are connectivity of local color differences, not materials.
    """
    a = _rgba(source, 'source')
    shape = a.shape[:2]
    w, h = _grid(grid, shape)
    scope = _mask(scope, shape, 'scope')
    deleted = np.zeros(shape, bool) if deleted_mask is None else _mask(deleted_mask, shape, 'deleted_mask')
    coverage = _number(coverage, 'coverage', .01, 1)
    threshold = _number(color_edge_threshold, 'color_edge_threshold', .000001, 2)
    if not isinstance(fill_source_guard, (bool, np.bool_)):
        raise ValueError('fill_source_guard must be boolean.')
    if not isinstance(line_result, dict):
        raise ValueError('line_result must be a normalize_lines result dictionary.')
    try:
        candidate = _mask(line_result['source_candidate'], shape, 'source_candidate')
        projected = _mask(line_result['target_mask'], (h, w), 'target_mask')
        collision = _mask(line_result['collision_mask'], (h, w), 'collision_mask')
        xy = np.asarray(line_result['source_xy'])
    except KeyError as exc:
        raise ValueError('Incomplete line_result: ' + str(exc)) from exc
    if xy.shape != (h, w, 2) or not np.issubdtype(xy.dtype, np.integer) or xy.dtype == bool:
        raise ValueError('line source_xy must be integer Ht,Wt,2 in x,y order.')
    py, px = np.nonzero(projected)
    points = xy[py, px]
    if points.size:
        sx, sy = points[:, 0], points[:, 1]
        if ((sx < 0) | (sx >= shape[1]) | (sy < 0) | (sy >= shape[0])).any():
            raise ValueError('Projected line source coordinates are out of bounds.')
        if not (scope[sy, sx] & (a[sy, sx, 3] == 255) & candidate[sy, sx]).all():
            raise ValueError('Projected lines need scoped, opaque source candidate provenance.')
        if not (np.array_equal((2 * sx + 1) * w // (2 * shape[1]), px)
                and np.array_equal((2 * sy + 1) * h // (2 * shape[0]), py)):
            raise ValueError('Line provenance does not project into its target cell.')

    from scipy import ndimage as ndi
    from skimage.segmentation import watershed

    cy, cx = _centers(shape, (w, h))
    target_scope = scope[cy[:, None], cx[None, :]].copy()
    deleted_target = deleted[cy[:, None], cx[None, :]] & target_scope
    opaque = (a[..., 3] == 255) & ~deleted
    source_fill = opaque & scope & ~candidate
    # Hidden RGB is never used in a graph edge, marker, gradient or output fill.
    rgb = a[..., :3].copy()
    rgb[~opaque] = 0
    lab = rgb_to_oklab(rgb.astype(np.float32) / 255)
    source_labels, region_count = _source_regions(lab, source_fill, threshold)
    edge = np.zeros(shape, np.float32)
    for before, after in ((np.s_[:-1, :], np.s_[1:, :]),
                          (np.s_[:, :-1], np.s_[:, 1:])):
        d = np.linalg.norm(lab[before] - lab[after], axis=2)
        d *= opaque[before] & opaque[after] & scope[before] & scope[after]
        edge[before] = np.maximum(edge[before], d)
        edge[after] = np.maximum(edge[after], d)
    ex, ey = _edges(shape[1], w), _edges(shape[0], h)
    foreground = np.zeros((h, w), bool)
    markers = np.zeros((h, w), np.int32)
    energy = np.zeros((h, w), np.float32)
    mixed = 0
    for ty in range(h):
        for tx in range(w):
            ys, xs = slice(ey[ty], ey[ty + 1]), slice(ex[tx], ex[tx + 1])
            foreground[ty, tx] = np.mean(opaque[ys, xs]) >= coverage
            energy[ty, tx] = float(edge[ys, xs].max())
            present = source_labels[ys, xs]
            values, counts = np.unique(present[present >= 0], return_counts=True)
            if values.size:
                markers[ty, tx] = int(values[np.argmax(counts)]) + 1
                mixed += int(values.size > 1)
    fixed_line = projected & foreground & target_scope & ~collision & ~deleted_target
    if points.size:
        fixed_line[py, px] &= ~deleted[points[:, 1], points[:, 0]]
    fill_mask = foreground & target_scope & ~fixed_line & ~collision & ~deleted_target
    markers[~fill_mask] = 0
    rejected = 0
    if fill_source_guard:
        expanded, rejected = _supported_expand(markers, energy, fill_mask, lab,
            opaque & scope, source_labels, ex, ey, (w, h), threshold)
    else:
        expanded = watershed(energy, markers=markers, mask=fill_mask,
                             connectivity=ndi.generate_binary_structure(2, 1))
    # Markers remain authoritative; only their empty neighboring cells expand.
    owners = np.where(fill_mask & (expanded > 0), expanded - 1, -1).astype(np.int32)
    owners[markers > 0] = markers[markers > 0] - 1
    unresolved = fill_mask & (owners < 0)
    unresolved_components = int(ndi.label(unresolved, structure=ndi.generate_binary_structure(2, 1))[1])
    line_xy = np.full((h, w, 2), -1, np.int32)
    line_xy[fixed_line] = xy[fixed_line]
    return dict(source=a.copy(), source_scope=scope.copy(), source_opaque=opaque,
                source_fill_mask=source_fill, source_candidate=candidate.copy(),
                source_labels=source_labels, target_scope=target_scope,
                target_foreground=foreground, deleted_target_mask=deleted_target,
                target_markers=markers, target_owners=owners, target_energy=energy,
                fixed_line_mask=fixed_line, fixed_line_source_xy=line_xy,
                collision_mask=collision.copy(), unresolved_mask=unresolved,
                grid=(w, h), metadata=dict(
                    method=('scoped_source_supported_priority_flood_v2' if fill_source_guard
                            else 'scoped_raw_color_regions_marker_watershed_line_first_v1'),
                    grid=[w, h], source_region_count=region_count,
                    coverage=coverage, color_edge_threshold=threshold,
                    fixed_line_cells=int(fixed_line.sum()), collision_cells=int(collision.sum()),
                    mixed_source_region_cells=mixed, marker_cells=int((markers > 0).sum()),
                    expanded_unseeded_cells=int(((markers == 0) & (owners >= 0)).sum()),
                    unresolved_cells=int(unresolved.sum()), unresolved_components=unresolved_components,
                    deleted_target_cells=int(deleted_target.sum()), palette_in_geometry=False,
                    fill_source_guard=bool(fill_source_guard), unsupported_owner_proposals=rejected,
                    new_line_pixels_created=False, semantic_segmentation=False,
                    limitations=['Color connectivity can chain through gradual color changes.',
                                 'Open lines remain open; topology after downscaling is not guaranteed.',
                                 'Unseeded components and collisions preserve raw center samples.',
                                 'Several source regions competing for one target cell cannot all survive.']))


def _choose_sample(palette, labels, owner, ys, xs):
    yy, xx = np.nonzero(labels[ys, xs] == owner)
    if not yy.size:
        return None
    yy, xx = yy + ys.start, xx + xs.start
    _, inverse, counts = np.unique(palette[yy, xx], axis=0, return_inverse=True, return_counts=True)
    distance = ((yy - (ys.start + ys.stop - 1) / 2) ** 2
                + (xx - (xs.start + xs.stop - 1) / 2) ** 2)
    order = np.lexsort((xx, yy, distance, -counts[inverse]))
    return int(xx[order[0]]), int(yy[order[0]])


def render_line_geometry(geometry, palette_rgba):
    """Render prepared owners from same-source-region actual palette samples.

    Prefer a majority sample in the same cell; otherwise use the nearest pixel
    of that exact source region. Outside scope/unresolved/collision uses raw
    source centers, not guessed fills. Locked line coordinates never move.
    """
    if not isinstance(geometry, dict):
        raise ValueError('geometry must be a prepare_line_geometry dictionary.')
    required = ('source', 'grid', 'source_labels', 'target_scope', 'target_foreground',
                'deleted_target_mask', 'fixed_line_mask', 'fixed_line_source_xy',
                'collision_mask', 'target_owners', 'metadata')
    if any(k not in geometry for k in required):
        raise ValueError('Incomplete line geometry.')
    source = _rgba(geometry['source'], 'geometry source')
    palette = _rgba(palette_rgba, 'palette_rgba')
    if palette.shape != source.shape or not np.array_equal(palette[..., 3], source[..., 3]):
        raise ValueError('palette_rgba must preserve source shape and alpha exactly.')
    w, h = _grid(geometry['grid'], source.shape[:2])
    for key in ('target_scope', 'target_foreground', 'deleted_target_mask', 'fixed_line_mask', 'collision_mask'):
        _mask(geometry[key], (h, w), key)
    labels = np.asarray(geometry['source_labels'])
    owners = np.asarray(geometry['target_owners'])
    if labels.shape != source.shape[:2] or owners.shape != (h, w) or not np.issubdtype(labels.dtype, np.integer) or not np.issubdtype(owners.dtype, np.integer):
        raise ValueError('Invalid source/target region label arrays.')
    cy, cx = _centers(source.shape[:2], (w, h))
    out = source[cy[:, None], cx[None, :]].copy()
    xy = np.empty((h, w, 2), np.int32)
    xy[..., 0] = cx[None, :]
    xy[..., 1] = cy[:, None]
    active = geometry['target_scope']
    erased = active & (geometry['deleted_target_mask'] | (~geometry['target_foreground'] & ~geometry['collision_mask']))
    out[erased] = 0
    xy[erased] = -1
    line = geometry['fixed_line_mask']
    fill = active & geometry['target_foreground'] & ~line & ~geometry['collision_mask'] & ~erased & (owners >= 0)
    ex, ey = _edges(source.shape[1], w), _edges(source.shape[0], h)
    missing = {}
    local_count = 0
    for ty, tx in zip(*np.nonzero(fill)):
        owner = int(owners[ty, tx])
        point = _choose_sample(palette, labels, owner,
                               slice(ey[ty], ey[ty + 1]), slice(ex[tx], ex[tx + 1]))
        if point is None:
            missing.setdefault(owner, []).append((int(ty), int(tx)))
        else:
            sx, sy = point
            out[ty, tx] = palette[sy, sx]
            xy[ty, tx] = point
            local_count += 1
    nearest_count = 0
    if missing:
        from scipy.spatial import cKDTree
        flat = np.flatnonzero(labels.ravel() >= 0)
        sort = np.argsort(labels.ravel()[flat], kind='stable')
        flat = flat[sort]
        sorted_labels = labels.ravel()[flat]
        for owner, targets in missing.items():
            lo = np.searchsorted(sorted_labels, owner, side='left')
            hi = np.searchsorted(sorted_labels, owner, side='right')
            indices = flat[lo:hi]
            if not indices.size:
                raise ValueError('Prepared owner has no source-region samples.')
            yy, xx = np.divmod(indices, source.shape[1])
            coords = np.column_stack((yy, xx))
            tree = cKDTree(coords)
            targets = np.asarray(targets, np.int32)
            query = np.column_stack(((targets[:, 0] + .5) * source.shape[0] / h - .5,
                                     (targets[:, 1] + .5) * source.shape[1] / w - .5))
            _, nearest = tree.query(query, k=1, workers=1)
            points = coords[nearest]
            out[targets[:, 0], targets[:, 1]] = palette[points[:, 0], points[:, 1]]
            xy[targets[:, 0], targets[:, 1]] = points[:, ::-1]
            nearest_count += len(targets)
    line_xy = np.asarray(geometry['fixed_line_source_xy'])
    if line_xy.shape != (h, w, 2) or not np.issubdtype(line_xy.dtype, np.integer):
        raise ValueError('Invalid fixed line provenance.')
    ly, lx = np.nonzero(line)
    points = line_xy[ly, lx]
    if points.size:
        sx, sy = points[:, 0], points[:, 1]
        if ((sx < 0) | (sx >= source.shape[1]) | (sy < 0) | (sy >= source.shape[0])).any():
            raise ValueError('Fixed line provenance is out of bounds.')
        if not (source[sy, sx, 3] == 255).all():
            raise ValueError('Fixed lines require opaque source samples.')
        out[ly, lx] = palette[sy, sx]
        xy[ly, lx] = points
    meta = dict(geometry['metadata'])
    meta.update(same_cell_fill_samples=local_count, same_region_nearest_samples=nearest_count,
                rendered_line_cells=int(line.sum()), fixed_line_geometry_unchanged=True,
                rgb_blending=False, render_palette_changes_geometry=False)
    return dict(image=out, source_xy=xy, metadata=meta)
