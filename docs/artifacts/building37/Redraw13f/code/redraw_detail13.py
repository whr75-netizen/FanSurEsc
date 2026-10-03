"""R13 face-local shade/detail analysis with an exact observed-color palette.

Geometry, sampling pitch, UV mapping, alpha and structural lines belong to the
caller.  This module never draws grain, changes coordinates or adds RGB detail
to a finished image.  It returns tone IDs at the supplied sample positions.

The fixed experiment uses standard pieces: CIELAB/D65, Huber IRLS fitting of a
quadratic shade basis, a local gradient structure tensor, directional bilateral
detail filtering, one-dimensional Lloyd quantization, and observed-color
medoids.  This combination is an R13 hypothesis, not an implementation of the
complete ETF/FDoG/RTV papers or a proof of semantic grain recovery.

References: Kang et al. (2009), Flow-Based Image Abstraction, sections 2/4;
https://pages.cs.wisc.edu/~dyer/cs534/papers/kang_tvcg09.pdf
RTV's structure/texture distinction motivates retaining both base and residual;
https://www.cse.cuhk.edu.hk/~leojia/projects/texturesep/
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

import numpy as np


DEFAULTS = {
    "shade_basis": "quadratic_uv",
    "shade_huber_iterations": 6,
    "neighbors": 12,
    "tensor_coherence_wood": 0.35,
    "tensor_coherence_paint": 0.55,
    "detail_gain_wood": 1.7,
    "detail_gain_paint": 0.7,
    "detail_minimum_lab_l": 0.4,
    "quantizer_iterations": 24,
}


def _lab(rgb: np.ndarray) -> np.ndarray:
    srgb = np.asarray(rgb, dtype=np.float64) / 255.0
    linear = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    xyz = linear @ np.array([
        [0.4124564, 0.2126729, 0.0193339],
        [0.3575761, 0.7151522, 0.1191920],
        [0.1804375, 0.0721750, 0.9503041],
    ])
    xyz /= np.array([0.95047, 1.0, 1.08883])
    delta = 6.0 / 29.0
    f = np.where(xyz > delta**3, np.cbrt(xyz), xyz / (3 * delta**2) + 4.0 / 29.0)
    return np.column_stack((116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])))


def _mad(values: np.ndarray) -> float:
    center = np.median(values)
    return float(1.4826 * np.median(np.abs(values - center)))


def _shade_fit(lightness: np.ndarray, uv: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    # Basis normalization stabilizes the least-squares solve only; it does not
    # modify the caller's geometry or the positions at which IDs are returned.
    extent = np.ptp(uv, axis=0)
    q = 2 * (uv - np.min(uv, axis=0)) / np.maximum(extent, 1e-12) - 1
    u, v = q.T
    basis = np.column_stack((np.ones(len(q)), u, v, u * u, u * v, v * v))
    weights = np.ones(len(q), dtype=np.float64)
    coefficients = np.zeros(6, dtype=np.float64)
    for _ in range(DEFAULTS["shade_huber_iterations"]):
        root_weights = np.sqrt(weights)
        coefficients = np.linalg.lstsq(basis * root_weights[:, None], lightness * root_weights, rcond=None)[0]
        residual = lightness - basis @ coefficients
        # Huber 1.345 is a conventional robust-regression tuning constant.
        threshold = 1.345 * max(_mad(residual), 0.05)
        weights = np.minimum(1, threshold / np.maximum(np.abs(residual), 1e-12))
    base = (basis @ coefficients).clip(float(lightness.min()), float(lightness.max()))
    return base, {
        "basis": DEFAULTS["shade_basis"],
        "coefficient_order": ["1", "u", "v", "u2", "uv", "v2"],
        "normalized_basis_coefficients": coefficients.tolist(),
        "fit_residual_mad_lab_l": _mad(lightness - base),
        "downweighted_sample_count": int(np.count_nonzero(weights < 0.5)),
    }


def _neighbors(uv: np.ndarray, count: int) -> tuple[np.ndarray, np.ndarray, float]:
    """Bounded local UV neighbor search with uniform spatial hash buckets."""
    n = len(uv)
    q = uv - np.min(uv, axis=0)
    # A single scalar respects the relative length of the two supplied axes.
    scalar = max(float(np.ptp(uv, axis=0).max()), 1e-12)
    q /= scalar
    extent = np.maximum(np.ptp(q, axis=0), 1e-6)
    spacing = max(float(np.sqrt(np.prod(extent) / n)), 1e-6)
    cell_size = 2.5 * spacing
    bins = np.floor(q / cell_size).astype(np.int64)
    buckets: dict[tuple[int, int], list[int]] = {}
    for index, cell in enumerate(bins):
        buckets.setdefault((int(cell[0]), int(cell[1])), []).append(index)
    indices = np.empty((n, count), dtype=np.int32)
    for index, cell in enumerate(bins):
        candidates: list[int] = []
        bx, by = int(cell[0]), int(cell[1])
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                candidates.extend(buckets.get((bx + dx, by + dy), ()))
        candidates = [candidate for candidate in candidates if candidate != index]
        if not candidates:
            indices[index] = index
            continue
        candidate_array = np.asarray(candidates, dtype=np.int32)
        distances = np.sum((q[candidate_array] - q[index]) ** 2, axis=1)
        # Stable sort provides a deterministic order for equal distances.
        selected = candidate_array[np.argsort(distances, kind="stable")[:count]]
        indices[index] = np.pad(selected, (0, count - len(selected)), constant_values=index)
    offsets = q[indices] - q[:, None, :]
    positive_distances = np.linalg.norm(offsets, axis=-1)
    positive_distances = positive_distances[positive_distances > 1e-10]
    if positive_distances.size:
        # Median nearest-neighbor distance is independent of a requested grid.
        nearest = np.linalg.norm(offsets[:, 0], axis=-1)
        nearest = nearest[nearest > 1e-10]
        if nearest.size:
            spacing = max(float(np.median(nearest)), 1e-6)
    return indices, offsets, spacing


def _directional_detail(
    lightness: np.ndarray, residual: np.ndarray, uv: np.ndarray, role: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    n = len(lightness)
    if n < 24 or np.any(np.ptp(uv, axis=0) < 1e-10):
        return np.zeros(n), np.zeros(n), np.zeros(n, dtype=bool), {
            "direction_test_available": False, "reason": "too_few_samples_or_degenerate_face_uv",
            "grain_candidates": 0, "noise_mad_lab_l": None,
        }
    indices, offsets, spacing = _neighbors(uv, min(DEFAULTS["neighbors"], n - 1))
    dx, dy = offsets[..., 0], offsets[..., 1]
    distance_squared = dx * dx + dy * dy
    valid_neighbors = distance_squared > 1e-20
    spatial = np.exp(-distance_squared / (2 * (2.5 * spacing) ** 2)) * valid_neighbors
    local_luma_difference = lightness[indices] - lightness[:, None]
    range_sigma = max(2.0, 2 * _mad(local_luma_difference[valid_neighbors]))
    weights = spatial * np.exp(-(local_luma_difference / range_sigma) ** 2 / 2)
    difference = residual[indices] - residual[:, None]
    a = np.sum(weights * dx * dx, axis=1)
    b = np.sum(weights * dx * dy, axis=1)
    c = np.sum(weights * dy * dy, axis=1)
    bx = np.sum(weights * dx * difference, axis=1)
    by = np.sum(weights * dy * difference, axis=1)
    regularizer = max(spacing**2 * 1e-4, 1e-12)
    a += regularizer
    c += regularizer
    determinant = np.maximum(a * c - b * b, 1e-20)
    gradient_x = (c * bx - b * by) / determinant
    gradient_y = (a * by - b * bx) / determinant
    normalizer = 1 + np.sum(spatial, axis=1)
    jxx = (gradient_x**2 + np.sum(spatial * gradient_x[indices] ** 2, axis=1)) / normalizer
    jxy = (gradient_x * gradient_y + np.sum(spatial * gradient_x[indices] * gradient_y[indices], axis=1)) / normalizer
    jyy = (gradient_y**2 + np.sum(spatial * gradient_y[indices] ** 2, axis=1)) / normalizer
    separation = np.sqrt((jxx - jyy) ** 2 + 4 * jxy**2)
    coherence = separation / np.maximum(jxx + jyy, 1e-12)
    theta = 0.5 * np.arctan2(2 * jxy, jxx - jyy)
    tangent_x, tangent_y = -np.sin(theta), np.cos(theta)
    along = dx * tangent_x[:, None] + dy * tangent_y[:, None]
    across = -dx * tangent_y[:, None] + dy * tangent_x[:, None]
    directional_weights = np.exp(-0.5 * (along / (2.5 * spacing)) ** 2
                                 -0.5 * (across / (0.65 * spacing)) ** 2) * valid_neighbors
    directional_weights *= np.exp(-(local_luma_difference / range_sigma) ** 2 / 2)
    clean_detail = (residual + np.sum(directional_weights * residual[indices], axis=1)) / (
        1 + np.sum(directional_weights, axis=1))
    noise_mad = _mad(residual - clean_detail)
    minimum_coherence = DEFAULTS[f"tensor_coherence_{role}"]
    noise_multiplier = 0.7 if role == "wood" else 1.25
    minimum_amplitude = max(DEFAULTS["detail_minimum_lab_l"], noise_multiplier * noise_mad)
    neighbor_support = np.count_nonzero(directional_weights >= 0.15, axis=1)
    grain = (coherence >= minimum_coherence) & (np.abs(clean_detail) >= minimum_amplitude) & (neighbor_support >= 2)
    accepted = np.where(grain, clean_detail, 0.0)
    return accepted, coherence, grain, {
        "direction_test_available": True,
        "analysis_uv_metric": "caller_uv_with_one_uniform_scalar_normalization",
        "neighbor_spacing_normalized_uv": spacing,
        "noise_mad_lab_l": noise_mad,
        "minimum_detail_amplitude_lab_l": minimum_amplitude,
        "minimum_tensor_coherence": minimum_coherence,
        "grain_candidates": int(np.count_nonzero(grain)),
        "grain_candidate_fraction": float(np.mean(grain)),
        "mean_tensor_coherence": float(np.mean(coherence)),
        "coherent_residual_lab_l_range": [float(accepted.min()), float(accepted.max())],
        "candidate_semantics": "directional_source_detail_hypothesis_not_verified_wood_grain",
    }


def _quantize(values: np.ndarray, count: int) -> tuple[np.ndarray, np.ndarray]:
    centers = np.quantile(values, np.linspace(0.10, 0.90, count))
    for _ in range(DEFAULTS["quantizer_iterations"]):
        ids = np.argmin(np.abs(values[:, None] - centers[None, :]), axis=1)
        updated = centers.copy()
        for index in range(count):
            selected = values[ids == index]
            if selected.size:
                updated[index] = np.mean(selected)
        updated.sort()
        if np.max(np.abs(updated - centers)) < 1e-7:
            centers = updated
            break
        centers = updated
    return np.argmin(np.abs(values[:, None] - centers[None, :]), axis=1).astype(np.uint8), centers


def face_samples(
    rgb_float: np.ndarray, uv: np.ndarray, role: str, tone_count: int = 4,
) -> dict[str, Any]:
    """Analyze a single caller-defined face/material; return its finite palette.

    rgb_float: Nx3 in 0..255, holding nearest sampled source uint8 RGB values.
    uv: Nx2 finite face coordinates.  Relative UV lengths should represent the
        caller's planar metric; coordinates are returned in their input order.
    role: wood or paint.  Metal, internal boundaries and ink are separate roles.

    Palette colors are exact input RGB rows, selected as Lab medoids.  Floating
    mixtures are rejected so interpolated colors cannot silently become a
    purported original-color palette.  Tiny/degenerate faces retain a shade
    quantization but report that directional detail was not tested.
    """
    started = perf_counter()
    rgb = np.asarray(rgb_float, dtype=np.float64)
    positions = np.asarray(uv, dtype=np.float64)
    if role not in ("wood", "paint"):
        raise ValueError("role must be 'wood' or 'paint'; structural ink and metal are caller-owned")
    if not isinstance(tone_count, (int, np.integer)) or isinstance(tone_count, bool) or tone_count not in (3, 4):
        raise ValueError("tone_count must be 3 or 4")
    tone_count = int(tone_count)
    if rgb.ndim != 2 or rgb.shape[1] != 3 or positions.shape != (len(rgb), 2) or not len(rgb):
        raise ValueError("nonempty Nx3 RGB and matching Nx2 UV arrays required")
    if len(rgb) > 80000:
        raise ValueError("face sample limit is 80000; R13 operates on one native face")
    if not np.all(np.isfinite(rgb)) or not np.all(np.isfinite(positions)) or np.any(rgb < 0) or np.any(rgb > 255):
        raise ValueError("RGB must be finite 0..255 and UV must be finite")
    rounded = np.rint(rgb)
    if np.max(np.abs(rgb - rounded)) > 1e-6:
        raise ValueError("palette needs nearest sampled original RGB bytes, not interpolated or averaged RGB")
    rgb_bytes = rounded.astype(np.uint8)
    lab = _lab(rgb)
    lightness = lab[:, 0]
    base, base_analysis = _shade_fit(lightness, positions)
    base_done = perf_counter()
    detail, coherence, grain, detail_analysis = _directional_detail(lightness, lightness - base, positions, role)
    detail_done = perf_counter()
    gain = DEFAULTS[f"detail_gain_{role}"]
    score = (base + gain * detail).clip(float(lightness.min()), float(lightness.max()))
    tone_ids, score_centers = _quantize(score, tone_count)
    palette_indices = np.zeros(tone_count, dtype=np.int64)
    for index in range(tone_count):
        members = np.flatnonzero(tone_ids == index)
        if not members.size:
            palette_indices[index] = int(np.argmin(np.abs(lightness - score_centers[index])))
            continue
        centroid = np.mean(lab[members], axis=0)
        # Squared-Euclidean medoid minimizer is the observed point nearest the
        # centroid.  Selecting an input row preserves the actual source tuple.
        palette_indices[index] = members[np.argmin(np.sum((lab[members] - centroid) ** 2, axis=1))]
    palette = rgb_bytes[palette_indices]
    order = np.argsort(_lab(palette.astype(np.float64))[:, 0], kind="stable")
    inverse = np.empty(tone_count, dtype=np.uint8)
    inverse[order] = np.arange(tone_count, dtype=np.uint8)
    tone_ids = inverse[tone_ids]
    palette, palette_indices = palette[order], palette_indices[order]
    output_lab_l = _lab(palette.astype(np.float64))[tone_ids, 0]
    quantization_done = perf_counter()
    output_colors = int(np.unique(palette[tone_ids], axis=0).shape[0])
    warnings: list[str] = []
    if not detail_analysis["direction_test_available"]:
        warnings.append("directional_detail_not_tested")
    if role == "wood" and not np.any(grain):
        warnings.append("no_directional_grain_candidate_retained")
    if float(np.ptp(lightness)) >= 3 and output_colors < 3:
        warnings.append("less_than_three_output_tones_despite_source_lightness_range")
    if np.any(order != np.arange(tone_count)):
        warnings.append("palette_sorted_by_actual_observed_lightness")
    analysis = {
        "role": role,
        "sample_count": len(rgb),
        "tone_count": tone_count,
        "defaults": dict(DEFAULTS),
        "source_rgb_colors": int(np.unique(rgb_bytes, axis=0).shape[0]),
        "output_rgb_colors": output_colors,
        "occupied_tone_ids": np.unique(tone_ids).astype(int).tolist(),
        "palette_source_sample_indices": palette_indices.astype(int).tolist(),
        "palette_is_exact_observed_rgb": True,
        "source_lightness_range": [float(lightness.min()), float(lightness.max())],
        "shade_lightness_range": [float(base.min()), float(base.max())],
        "source_residual_mad_lab_l": _mad(lightness - base),
        "score_centers_before_palette_order": score_centers.tolist(),
        "detail_gain": gain,
        "output_vs_source_lightness_mae": float(np.mean(np.abs(output_lab_l - lightness))),
        "shade_fit": base_analysis,
        "directional_detail": detail_analysis,
        "timings_seconds": {
            "shade_fit": base_done - started,
            "directional_detail": detail_done - base_done,
            "palette_quantization": quantization_done - detail_done,
            "total": quantization_done - started,
        },
        "warnings": warnings,
        "failure_conditions": [
            "grain_pattern_lost_or_replaced_by_new_lines_in_native_visual_comparison",
            "directional_noise_promoted_as_grain_or_structural_boundary_blurred",
            "palette_or_sampling_contains_colors_not_observed_in_original_source",
            "face_geometry_uv_or_input_semantic_role_is_incorrect",
        ],
        "scope": "R13 shade/detail experiment; no recovered original grid, semantic guarantee, physical albedo, normals, or artistic approval",
    }
    return {
        "palette": palette,
        "tone_ids": tone_ids,
        "base_luma": base,
        "detail_luma": detail,
        "source_residual_luma": lightness - base,
        "grain_confidence": coherence,
        "grain_mask": grain,
        "analysis": analysis,
        "statistics": analysis,
    }
