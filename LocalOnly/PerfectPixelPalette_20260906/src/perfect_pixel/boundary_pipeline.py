"""Boundary labels, region palettes, then discrete fixed-grid sampling.

Experimental composition of separate algorithms, not a reproduction of any
paper. No semantic parts, object presets, generated colors or image coordinates.
"""
from dataclasses import dataclass, asdict
import hashlib
import numpy as np

from .palette import (_image, scaled_grid, detect_base_grid, rgb_to_oklab,
                      _grid_edges, _feature_map, _box_mean)


@dataclass(frozen=True)
class BoundaryOptions:
    tones: int = 3
    feature_strength: float = 1.5
    refine_intensity: float = .2
    min_retained_tone_delta_l: float = .025
    shading_mode: str = 'legacy_regions'
    color_error: float = .06
    gradient_edge_threshold: float = .06
    gradient_chroma_span: float = .12
    tone_policy: str = 'max_error'
    tone_error: float = .06
    chroma_error: float = .06
    contrast_retention: float = .65
    minimum_contrast: float = .025

    def validate(self):
        if self.shading_mode not in ('legacy_regions', 'continuous'):
            raise ValueError('shading_mode must be legacy_regions or continuous.')
        if self.shading_mode == 'continuous':
            from .gradient_tones import validate_options
            validate_options(self.color_error, self.gradient_edge_threshold, self.gradient_chroma_span)
            if self.tone_policy not in ('max_error', 'weighted_steps', 'spatial_steps'):
                raise ValueError('tone_policy must be max_error, weighted_steps or spatial_steps.')
        if isinstance(self.tones, bool) or not isinstance(self.tones, (int, np.integer)) or not 1 <= self.tones <= 3:
            raise ValueError('tones must be an integer in [1,3].')
        for name, limit in (('feature_strength', 3), ('refine_intensity', .45),
                            ('min_retained_tone_delta_l', 1)):
            value = getattr(self, name)
            if isinstance(value, (bool, str)) or not np.isscalar(value) or not np.isfinite(value) or not 0 <= value <= limit:
                raise ValueError(name + ' is outside its supported finite range.')


@dataclass
class BoundaryResult:
    image: np.ndarray
    flat_image: np.ndarray
    region_labels: np.ndarray
    edge_strength: np.ndarray
    native_regions: np.ndarray
    native_tones: np.ndarray
    palette: np.ndarray
    metadata: dict


def sample_region_grid(image, labels, tones, palette, edges, base_grid, feature_strength=1.5,
                       structure_strength=None):
    """Coverage chooses a region before tone voting; alpha has separate votes.

    Original contrast can protect small details. We never erase a component
    merely because it occupies one or two pixels. No RGB averaging is emitted.
    """
    h, w = image.shape[:2]
    if labels.shape != (h, w) or tones.shape != (h, w):
        raise ValueError('Region and tone maps must use the original image grid.')
    alpha = image[..., 3] if image.shape[2] == 4 else np.full((h, w), 255, np.uint8)
    valid = (alpha >= 128).astype(np.float32)
    if np.any((labels[valid > 0] < 0) | (tones[valid > 0] < 0)):
        raise ValueError('Visible source pixels must have region and tone labels.')
    if np.any(tones[valid > 0] >= len(palette)):
        raise ValueError('Tone label outside the palette.')
    rgb = image[..., :3].copy()
    rgb[valid == 0] = 0
    lab = rgb_to_oklab(rgb.astype(np.float32) / 255)
    cell = min(w / base_grid[0], h / base_grid[1])
    importance = _feature_map(lab, valid, cell)
    radius = max(1, min(10, int(round(cell * .55))))
    # A same-lightness color accent can be important too.
    ab_mean = np.stack([_box_mean(lab[..., c], radius, valid) for c in (1, 2)], axis=-1)
    chroma_feature = np.clip(np.linalg.norm(lab[..., 1:] - ab_mean, axis=-1) / .06, 0, 1) * valid
    importance = np.maximum(importance, chroma_feature)
    support_radius = 0
    if structure_strength is not None:
        if (structure_strength.shape != (h, w) or
                not np.all(np.isfinite(structure_strength)) or
                np.any((structure_strength < 0) | (structure_strength > 1))):
            raise ValueError('Structure confidence must be finite HxW values in [0,1].')
        # Preserve the preceding scale-aware structure decision. Raw photo
        # texture alone must not regain full feature weight during downsampling.
        # A small local maximum lets a feature interior use its nearby boundary;
        # this changes only its bonus, never deletes a region or its coverage.
        support_radius = max(0, min(3, int(np.floor(cell * .25))))
        padded = np.pad(structure_strength, support_radius, mode='edge')
        support = np.zeros((h, w), np.float32)
        for dy in range(support_radius * 2 + 1):
            for dx in range(support_radius * 2 + 1):
                np.maximum(support, padded[dy:dy+h, dx:dx+w], out=support)
        importance *= support
    weight = 1 + feature_strength * importance
    ex, ey = edges
    out = np.zeros((len(ey) - 1, len(ex) - 1, 4), np.uint8)
    chosen_regions = np.full(out.shape[:2], -1, np.int32)
    chosen_tones = np.full(out.shape[:2], -1, np.int32)
    mixed_cells = 0
    for y in range(out.shape[0]):
        y0 = max(0, min(h - 1, int(np.floor(ey[y]))))
        y1 = max(y0 + 1, min(h, int(np.ceil(ey[y + 1]))))
        yy = np.arange(y0, y1)
        overlap_y = np.maximum(0, np.minimum(yy + 1, ey[y + 1]) - np.maximum(yy, ey[y]))
        dy = (yy + .5 - (ey[y] + ey[y + 1]) * .5) / max(ey[y + 1] - ey[y], 1e-6)
        for x in range(out.shape[1]):
            x0 = max(0, min(w - 1, int(np.floor(ex[x]))))
            x1 = max(x0 + 1, min(w, int(np.ceil(ex[x + 1]))))
            xx = np.arange(x0, x1)
            overlap_x = np.maximum(0, np.minimum(xx + 1, ex[x + 1]) - np.maximum(xx, ex[x]))
            dx = (xx + .5 - (ex[x] + ex[x + 1]) * .5) / max(ex[x + 1] - ex[x], 1e-6)
            spatial = overlap_y[:, None] * overlap_x[None, :]
            spatial *= .4 + .6 * np.exp(-2 * (dy[:, None] ** 2 + dx[None, :] ** 2))
            covered = valid[y0:y1, x0:x1]
            fg = float(np.sum(spatial * covered))
            bg = float(np.sum(spatial * (1 - covered)))
            if fg <= 0 or bg > fg:
                continue
            region = labels[y0:y1, x0:x1]
            active = covered > 0
            ballot = spatial * covered * weight[y0:y1, x0:x1]
            ids, inverse = np.unique(region[active], return_inverse=True)
            votes = np.bincount(inverse, weights=ballot[active])
            winner = int(ids[np.argmax(votes)])
            mixed_cells += int(len(ids) > 1)
            eligible = active & (region == winner)
            tone_values = tones[y0:y1, x0:x1][eligible]
            tone_ids, tone_inverse = np.unique(tone_values, return_inverse=True)
            tone_votes = np.bincount(tone_inverse, weights=ballot[eligible])
            tone = int(tone_ids[np.argmax(tone_votes)])
            out[y, x, :3] = palette[tone]
            out[y, x, 3] = 255
            chosen_regions[y, x] = winner
            chosen_tones[y, x] = tone
    source_ids = np.unique(labels[valid > 0])
    used_ids = np.unique(chosen_regions[chosen_regions >= 0])
    info = {
        'method': 'structure-gated-region-then-tone-vote/2',
        'structure_confidence_used': structure_strength is not None,
        'structure_support_radius': support_radius,
        'source_region_count': len(source_ids), 'represented_region_count': len(used_ids),
        'unrepresented_source_regions': np.setdiff1d(source_ids, used_ids).tolist(),
        'mixed_region_cells': mixed_cells,
        'output_rgb_from_palette_only': True, 'rgb_averaging': False,
        'small_component_deletion': False,
        'alpha_policy': 'source alpha>=128 then independent cell-coverage binary vote',
        'note': 'A one-color cell cannot represent every competing source region; missing IDs are recorded.'}
    return out, chosen_regions, chosen_tones, info


def prepare_region_tones(image, reference, base_grid, *, tones=3,
                         min_retained_tone_delta_l=.025, mode='legacy_regions',
                         color_error=.06, gradient_edge_threshold=.06, gradient_chroma_span=.12,
                         tone_policy='max_error', tone_error=.06, chroma_error=.06,
                         contrast_retention=.65, minimum_contrast=.025):
    """Source-resolution shading stage shared by both public pipelines.

    This function never chooses output pixels or adds lines. Its failures must
    propagate: global palette clustering is not a substitute for region tones.
    Source/reference are explicit data, not object-name presets.
    """
    image, reference = _image(image), _image(reference)
    BoundaryOptions(tones=tones, min_retained_tone_delta_l=min_retained_tone_delta_l,
                    shading_mode=mode, color_error=color_error,
                    gradient_edge_threshold=gradient_edge_threshold,
                    gradient_chroma_span=gradient_chroma_span, tone_policy=tone_policy,
                    tone_error=tone_error, chroma_error=chroma_error,
                    contrast_retention=contrast_retention, minimum_contrast=minimum_contrast).validate()
    base = tuple(scaled_grid(base_grid, '1.0'))
    if mode == 'continuous':
        # This mode is source-tone abstraction, not external style transfer.
        # A scoped input can mask out reference pixels, but visible RGB must be
        # the unmodified source. Do not silently ignore an external palette.
        visible = np.ones(image.shape[:2], bool) if image.shape[2] == 3 else image[..., 3] > 0
        if (reference.shape[:2] != image.shape[:2] or
                not np.array_equal(image[..., :3][visible], reference[..., :3][visible])):
            raise ValueError('continuous mode requires the unmodified source as reference; external palette transfer is available in legacy_regions only.')
        from .gradient_tones import prepare_gradient_tones
        result = prepare_gradient_tones(image, color_error=color_error,
            edge_threshold=gradient_edge_threshold, chroma_span=gradient_chroma_span,
            tone_policy=tone_policy, tone_error=tone_error, chroma_error=chroma_error,
            contrast_retention=contrast_retention, minimum_contrast=minimum_contrast)
        result['metadata'].update(mode=mode,
            color_error=color_error if tone_policy == 'max_error' else None,
            source_pixel_sha256=hashlib.sha256(image.tobytes()).hexdigest(),
            reference_pixel_sha256=hashlib.sha256(reference.tobytes()).hexdigest())
        return result
    from .boundary_regions import segment_regions
    from .region_palette import color_regions
    labels, edge_strength, segmentation = segment_regions(image, base_grid=base)
    flat, tone_map, palette, colors = color_regions(
        image, labels, reference, tones=tones,
        min_retained_tone_delta_l=min_retained_tone_delta_l)
    if flat.shape != image.shape:
        raise ValueError('Region color stage changed the source dimensions.')
    if image.shape[2] == 4 and not np.array_equal(flat[..., 3], image[..., 3]):
        raise ValueError('Region color stage changed alpha.')
    return {'flat_image': flat, 'region_labels': labels, 'edge_strength': edge_strength,
            'tone_map': tone_map, 'palette': palette,
            'metadata': {'method': 'source-region-tones/1', 'tones': tones,
                         'min_retained_tone_delta_l': min_retained_tone_delta_l,
                         'segmentation': segmentation, 'region_colors': colors,
                         'source_pixel_sha256': hashlib.sha256(image.tobytes()).hexdigest(),
                         'reference_pixel_sha256': hashlib.sha256(reference.tobytes()).hexdigest(),
                         'output_sampling_performed': False, 'fallback_algorithm': None}}


def get_boundary_pixel(image, reference, base_grid=None, resolution_scale='1.0', options=None):
    image = _image(image)
    reference = _image(reference)
    options = options or BoundaryOptions()
    options.validate()
    if base_grid is None:
        base_grid = detect_base_grid(image)
    grid = scaled_grid(base_grid, resolution_scale)
    base = tuple(int(x) for x in base_grid)
    shading = prepare_region_tones(image, reference, base,
        tones=options.tones,
        min_retained_tone_delta_l=options.min_retained_tone_delta_l,
        mode=options.shading_mode, color_error=options.color_error,
        gradient_edge_threshold=options.gradient_edge_threshold,
        gradient_chroma_span=options.gradient_chroma_span, tone_policy=options.tone_policy,
        tone_error=options.tone_error, chroma_error=options.chroma_error,
        contrast_retention=options.contrast_retention, minimum_contrast=options.minimum_contrast)
    labels, edge_strength = shading['region_labels'], shading['edge_strength']
    flat, tone_map, palette = shading['flat_image'], shading['tone_map'], shading['palette']
    segmentation, colors = shading['metadata']['segmentation'], shading['metadata']['region_colors']
    rgb = image[..., :3].copy()
    if image.shape[2] == 4:
        rgb[image[..., 3] < 128] = 0
    edges = _grid_edges(rgb, grid, options.refine_intensity)
    rgba, native_regions, native_tones, sampling = sample_region_grid(
        image, labels, tone_map, palette, edges, base, options.feature_strength,
        structure_strength=edge_strength)
    output = rgba if image.shape[2] == 4 else rgba[..., :3]
    metadata = {
        'algorithm': 'boundary-region-palette-grid/2', 'options': asdict(options),
        'source_pixel_sha256': hashlib.sha256(image.tobytes()).hexdigest(),
        'reference_pixel_sha256': hashlib.sha256(reference.tobytes()).hexdigest(),
        'source_shape': list(image.shape), 'base_grid': list(base),
        'resolution_scale': str(resolution_scale), 'target_grid': list(grid),
        'palette': palette.tolist(), 'segmentation': segmentation,
        'region_colors': colors, 'sampling': sampling,
        'grid_edges_x': edges[0].tolist(), 'grid_edges_y': edges[1].tolist(),
        'semantic_part_coordinates': False, 'generative_redraw': False,
        'design_approval': 'pending_user_review',
        'comparison_contract': 'Same immutable base size, source and reference; segmentation/tone layout intentionally revised from the original.'}
    return BoundaryResult(output, flat, labels, edge_strength, native_regions, native_tones, palette, metadata)
