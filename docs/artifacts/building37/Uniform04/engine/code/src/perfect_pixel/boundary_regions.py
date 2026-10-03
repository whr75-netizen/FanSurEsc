"""Source-resolution SLIC regions with conservative boundary-aware merging.

Only labels and guidance are produced; no RGB is recolored or resized. This is
color/edge segmentation, not semantic material or object recognition.
"""
import heapq
import math

import numpy as np


MAX_PIXELS = 4_194_304
MAX_SLIC_REGIONS = 4_096
MAX_INITIAL_REGIONS = 65_536
# Splitting can separate a SLIC seed into several connected source regions.
# The already accepted partition keeps its capacity after conservative merging.
MAX_REGIONS = MAX_INITIAL_REGIONS
_SPLIT_DELTA_E = 6.0
_MERGE_DELTA_E = 3.0
_MERGE_EDGE = .22


def _validate(image, base_grid):
    if (not isinstance(image, np.ndarray) or image.dtype != np.uint8 or image.ndim != 3
            or image.shape[2] not in (3, 4) or min(image.shape[:2]) < 1):
        raise ValueError('image must be a nonempty uint8 RGB/RGBA array')
    if image.shape[0] * image.shape[1] > MAX_PIXELS:
        raise ValueError('image exceeds the 4194304-pixel bound; no hidden resize is performed')
    if not isinstance(base_grid, (tuple, list)) or len(base_grid) != 2:
        raise ValueError('base_grid must be (width, height)')
    if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer))
           or not 1 <= v <= 4096 for v in base_grid):
        raise ValueError('base_grid dimensions must be integers in 1..4096')
    if int(base_grid[0]) * int(base_grid[1]) > 262144:
        raise ValueError('base_grid exceeds the 262144-cell guidance bound')


def _gradient(lab, visible):
    """Forward-difference CIELAB gradient; both incident pixels receive it."""
    out = np.zeros(visible.shape, np.float32)
    for axis in (0, 1):
        first = (slice(None, -1), slice(None)) if axis == 0 else (slice(None), slice(None, -1))
        second = (slice(1, None), slice(None)) if axis == 0 else (slice(None), slice(1, None))
        difference = np.linalg.norm(lab[first] - lab[second], axis=2)
        difference *= visible[first] & visible[second]
        np.maximum(out[first], difference, out=out[first])
        np.maximum(out[second], difference, out=out[second])
    return out


def _split_connected(slic_labels, guidance_lab, visible, micro_labels, csr_matrix, connected_components):
    """Use persistent structure, not every raw texture jump, as a hard fence."""
    ids = np.arange(visible.size, dtype=np.int32).reshape(visible.shape)
    starts, ends = [], []
    for axis in (0, 1):
        first = (slice(None, -1), slice(None)) if axis == 0 else (slice(None), slice(None, -1))
        second = (slice(1, None), slice(None)) if axis == 0 else (slice(None), slice(1, None))
        allowed = visible[first] & visible[second] & (slic_labels[first] == slic_labels[second])
        allowed &= np.linalg.norm(guidance_lab[first] - guidance_lab[second], axis=2) <= _SPLIT_DELTA_E
        allowed &= micro_labels[first] == micro_labels[second]
        starts.append(ids[first][allowed])
        ends.append(ids[second][allowed])
    rows, cols = np.concatenate(starts), np.concatenate(ends)
    graph = csr_matrix((np.ones(len(rows), np.uint8), (rows, cols)),
                       shape=(visible.size, visible.size))
    _, components = connected_components(graph, directed=False, return_labels=True)
    labels = np.full(visible.shape, -1, np.int32)
    unique, inverse = np.unique(components[visible.ravel()], return_inverse=True)
    if len(unique) > MAX_INITIAL_REGIONS:
        raise ValueError('source has more than 65536 separated regions; no small-region pruning is performed')
    labels[visible] = inverse.astype(np.int32)
    return labels, len(unique)


def _merge(labels, lab, edge, count):
    visible = labels >= 0
    flat_labels = labels[visible]
    areas = np.bincount(flat_labels, minlength=count).astype(np.float64)
    sums = np.stack([np.bincount(flat_labels, weights=lab[..., channel][visible], minlength=count)
                     for channel in range(3)], axis=1)
    parent = np.arange(count, dtype=np.int32)
    codes, strengths = [], []
    for axis in (0, 1):
        first = (slice(None, -1), slice(None)) if axis == 0 else (slice(None), slice(None, -1))
        second = (slice(1, None), slice(None)) if axis == 0 else (slice(None), slice(1, None))
        a, b = labels[first], labels[second]
        boundary = (a >= 0) & (b >= 0) & (a != b)
        low, high = np.minimum(a[boundary], b[boundary]), np.maximum(a[boundary], b[boundary])
        codes.append(low.astype(np.int64) * count + high)
        strengths.append(np.maximum(edge[first][boundary], edge[second][boundary]))
    codes, inverse = np.unique(np.concatenate(codes), return_inverse=True)
    maximum = np.zeros(len(codes), np.float32)
    np.maximum.at(maximum, inverse, np.concatenate(strengths))
    adjacency = [dict() for _ in range(count)]
    pending = []
    for code, strength in zip(codes, maximum):
        a, b = divmod(int(code), count)
        weight = float(strength)
        adjacency[a][b] = adjacency[b][a] = weight
        if weight < _MERGE_EDGE:
            heapq.heappush(pending, (weight, a, b))

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = int(parent[node])
        return node

    merges = 0
    while pending:
        _, a, b = heapq.heappop(pending)
        a, b = find(a), find(b)
        if a == b or b not in adjacency[a] or adjacency[a][b] >= _MERGE_EDGE:
            continue
        if np.linalg.norm(sums[a] / areas[a] - sums[b] / areas[b]) > _MERGE_DELTA_E:
            continue
        a, b = min(a, b), max(a, b)
        combined = dict(adjacency[a])
        for neighbor, strength in adjacency[b].items():
            combined[neighbor] = max(combined.get(neighbor, 0.0), strength)
        combined.pop(a, None)
        combined.pop(b, None)
        # Keep the strongest shared boundary after merging. A weak route must
        # not bypass an already known strong boundary between the same groups.
        for neighbor, strength in combined.items():
            adjacency[neighbor].pop(a, None)
            adjacency[neighbor].pop(b, None)
            adjacency[neighbor][a] = strength
            if strength < _MERGE_EDGE:
                heapq.heappush(pending, (strength, min(a, neighbor), max(a, neighbor)))
        adjacency[a], adjacency[b] = combined, {}
        parent[b] = a
        sums[a] += sums[b]
        areas[a] += areas[b]
        merges += 1
    roots = np.array([find(i) for i in range(count)], np.int32)
    _, contiguous = np.unique(roots, return_inverse=True)
    output = labels.copy()
    output[visible] = contiguous[labels[visible]].astype(np.int32)
    return output, count - merges, merges


def segment_regions(image, base_grid=(70, 73)):
    """Return ``(int32 labels, float32 edge_strength, JSON metadata)``.

    Labels/edges keep the exact input H,W. Alpha==0 is label -1 and edge 0;
    nonzero-alpha pixels are segmented without changing any input byte.
    SLIC uses one seed per four output cells, capped at 4096. Structure and
    microfeature splitting permit 65536 connected regions. Conservative merging
    does not impose the SLIC seed count as a second, smaller capacity limit.
    Limits fail explicitly, not resized.
    Working storage is O(input pixels + adjacency edges), including a sparse
    four-neighbor graph; the largest accepted images can require hundreds of MB.
    """
    _validate(image, base_grid)
    try:
        import skimage
        from skimage.color import rgb2lab
        from skimage.segmentation import slic
        from scipy.ndimage import gaussian_filter, median_filter, uniform_filter, label as connected_label
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import connected_components
    except ImportError as exc:
        raise ImportError('boundary_regions requires scikit-image and scipy; no alternate segmentation is used') from exc
    height, width = image.shape[:2]
    visible = np.ones((height, width), bool) if image.shape[2] == 3 else image[..., 3] > 0
    cell_x, cell_y = width / int(base_grid[0]), height / int(base_grid[1])
    cell_scale = math.sqrt(cell_x * cell_y)
    sigma = float(np.clip(.5 * cell_scale, .5, 4.0))
    requested = min(MAX_SLIC_REGIONS, int(visible.sum()),
                    max(1, math.ceil(int(base_grid[0]) * int(base_grid[1]) / 4)))
    metadata = {
        'method': 'source-slic-boundary-regions/3', 'skimage_version': skimage.__version__,
        'base_grid': [int(v) for v in base_grid], 'source_size': [width, height],
        'cell_size_source_pixels': [cell_x, cell_y], 'guidance_sigma': sigma,
        'slic_requested_segments': requested, 'slic_compactness_lab_units': 3.0,
        'slic_output_cells_per_seed': 4,
        'split_delta_e76': _SPLIT_DELTA_E, 'merge_delta_e76': _MERGE_DELTA_E,
        'merge_maximum_boundary_strength': _MERGE_EDGE,
        'maximum_pixels': MAX_PIXELS, 'maximum_slic_regions': MAX_SLIC_REGIONS,
        'maximum_regions': MAX_REGIONS, 'maximum_initial_regions': MAX_INITIAL_REGIONS,
        'connectivity': 4,
        'hidden_resize': False, 'minimum_area_pruning': False, 'input_rgb_modified': False,
        'alpha_policy': 'alpha zero excluded; nonzero alpha included; original alpha untouched',
        'notes': ['SLIC color/position regions are not semantic materials or named parts.',
                  'SLIC and splitting use cell-scale smoothed CIELAB guidance, never recolored output RGB.',
                  'Only adjacent weak-boundary, small guidance-color-distance regions may merge.',
                  'Raw contrast is confidence, not an unconditional texture-preserving hard boundary.',
                  'Isolated high-contrast median residuals receive microfeature protection; dense texture does not.',
                  'No guarantee of separating smoothly blended material/shading boundaries.'],
    }
    if not np.any(visible):
        metadata.update(initial_region_count=0, region_count=0, merge_count=0)
        return np.full((height, width), -1, np.int32), np.zeros((height, width), np.float32), metadata
    rgb = image[..., :3].astype(np.float32) / 255
    rgb[~visible] = 0
    lab = rgb2lab(rgb).astype(np.float32)
    lab[~visible] = 0
    smooth_weight = gaussian_filter(visible.astype(np.float32), sigma, mode='nearest')
    smooth = gaussian_filter(lab, (sigma, sigma, 0), mode='nearest')
    smooth /= np.maximum(smooth_weight[..., None], 1e-8)
    raw = _gradient(lab, visible)
    guided = _gradient(smooth, visible)
    raw_confidence = np.clip(raw / 10.0, 0, 1)
    structure_confidence = np.clip(guided / 6.0, 0, 1)
    edge = np.sqrt(raw_confidence * structure_confidence).astype(np.float32)
    median_lab = median_filter(lab, size=(3, 3, 1), mode='nearest')
    residual = np.linalg.norm(lab - median_lab, axis=2)
    candidates = visible & (residual >= 20.0)
    neighborhood = min(31, max(3, int(math.ceil(2 * cell_scale)) | 1))
    density = uniform_filter(candidates.astype(np.float32), neighborhood, mode='nearest')
    # Missing alpha neighbors must not manufacture median-residual features.
    coverage = uniform_filter(visible.astype(np.float32), 3, mode='nearest')
    micro_mask = candidates & (density <= .08) & (coverage >= .999)
    micro_labels, micro_count = connected_label(micro_mask)
    edge[micro_mask] = 1.0
    metadata.update(microfeature_region_count=int(micro_count),
                    microfeature_pixel_count=int(micro_mask.sum()),
                    microfeature_residual_delta_e76=20.0,
                    microfeature_maximum_local_density=.08,
                    microfeature_density_window=neighborhood,
                    raw_edge_policy='confidence only; never standalone hard split or merge barrier',
                    boundary_policy='sqrt(raw contrast confidence * cell-scale structure confidence)')
    for axis in (0, 1):
        first = (slice(None, -1), slice(None)) if axis == 0 else (slice(None), slice(None, -1))
        second = (slice(1, None), slice(None)) if axis == 0 else (slice(None), slice(1, None))
        boundary = visible[first] != visible[second]
        edge[first][boundary] = 1
        edge[second][boundary] = 1
    edge[~visible] = 0
    # slic rescales its input to [0,1]. Compensate compactness to preserve the
    # stated CIELAB-distance balance when passing Lab guidance directly.
    lab_span = max(float(np.ptp(smooth[visible])), 1.0)
    compactness = 3.0 / lab_span
    metadata['slic_normalized_compactness'] = compactness
    slic_labels = slic(smooth, n_segments=requested, compactness=compactness, max_num_iter=10,
                       sigma=0, convert2lab=False, enforce_connectivity=False,
                       start_label=0, mask=None if np.all(visible) else visible,
                       channel_axis=-1, slic_zero=False)
    labels, initial_count = _split_connected(slic_labels, smooth, visible, micro_labels,
                                            csr_matrix, connected_components)
    labels, final_count, merges = _merge(labels, smooth, edge, initial_count)
    metadata.update(initial_region_count=initial_count, region_count=final_count, merge_count=merges)
    return labels, edge, metadata
