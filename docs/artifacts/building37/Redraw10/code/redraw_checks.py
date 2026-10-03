"""Independent invariants and known-feature checks for the R10 experiment.

This module does not import or call the redraw implementation.  Passing these
checks certifies the tested numeric properties, not artistic similarity, a
recovered physical material, or an unknown source's logical pixel pitch.
"""

from __future__ import annotations

from hashlib import sha256
from numbers import Real
from typing import Any

import numpy as np


FIXTURE_WIDTH = 192
FIXTURE_HEIGHT = 128
FIXTURE_HANDLE = (35, 52, 73, 78)  # x0, y0, x1, y1; upper bounds excluded.
FIXTURE_METAL_CENTER = (146.0, 60.0)
FIXTURE_METAL_RADII = (22.0, 29.0)
FIXTURE_DARK_METAL_BAND = (145, 47, 147, 73)
FIXTURE_DARK_METAL_ANCHOR = (151, 48, 158, 72)


def _luminance(rgb: np.ndarray) -> np.ndarray:
    """Rec.709 weighted display RGB, used only for high-contrast fixture tests."""
    return np.asarray(rgb, dtype=np.float64) @ np.array([0.2126, 0.7152, 0.0722])


def make_fixture(*, rgba: bool = True) -> np.ndarray:
    """Return a deterministic 192x128 object with independently known features.

    The one-pixel outer outline and two-pixel rectangular handle are structural
    dark ink.  The elliptical metal interior has four broad, increasing bands
    with continuous variation within each band and varying chroma.  No dark
    ridge is added within the metal.  Alpha is binary, including the edge.
    """
    yy, xx = np.indices((FIXTURE_HEIGHT, FIXTURE_WIDTH))
    rgb = np.full((FIXTURE_HEIGHT, FIXTURE_WIDTH, 3), [232, 226, 212], dtype=np.uint8)
    alpha = np.zeros((FIXTURE_HEIGHT, FIXTURE_WIDTH), dtype=np.uint8)
    body = (xx >= 8) & (xx < 184) & (yy >= 14) & (yy < 114)
    alpha[body] = 255

    # Continuous, colored wood stripes; these are not labels from the core.
    stripe = 0.5 + 0.5 * np.sin(xx * 0.39 + yy * 0.024)
    grain = 0.5 + 0.5 * np.sin(xx * 1.63 + yy * 0.075)
    vertical = (yy - 14) / 99.0
    wood = np.stack((
        127 + 44 * stripe + 13 * vertical + 3 * grain,
        66 + 28 * stripe + 11 * vertical + 4 * grain,
        31 + 13 * stripe + 5 * vertical + 2 * grain,
    ), axis=-1)
    rgb[body] = np.rint(wood[body]).clip(0, 255).astype(np.uint8)

    outline = body & ((xx == 8) | (xx == 183) | (yy == 14) | (yy == 113))
    rgb[outline] = [16, 14, 13]
    # One-pixel partition with no interpolation or antialiasing.
    rgb[22:106, 108] = [18, 16, 15]

    cx, cy = FIXTURE_METAL_CENTER
    rx, ry = FIXTURE_METAL_RADII
    distance = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    metal = distance <= 1.0
    inner = ((xx - cx) / (rx - 1.0)) ** 2 + ((yy - cy) / (ry - 1.0)) ** 2 <= 1.0
    rgb[metal & ~inner] = [21, 22, 23]
    # Curved band boundaries, each strictly increasing along every row.
    t = ((xx - (cx - rx)) / (2 * rx) + 0.075 * ((yy - cy) / ry) ** 2).clip(0, 1)
    band = np.minimum((t * 4).astype(np.int16), 3)
    plateau = np.array([76.0, 120.0, 170.0, 224.0])[band]
    continuous = 12 * (t * 4 - band) + 1.8 * np.sin((yy - cy) * 0.18)
    chroma = 1.6 * np.sin((yy - cy) * 0.21)
    metallic = np.stack((
        plateau + continuous - 2 + chroma,
        plateau + continuous + 1,
        plateau + continuous + 5 - chroma,
    ), axis=-1)
    rgb[inner] = np.rint(metallic[inner]).clip(0, 255).astype(np.uint8)

    x0, y0, x1, y1 = FIXTURE_HANDLE
    handle_box = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    handle_hole = (xx >= x0 + 2) & (xx < x1 - 2) & (yy >= y0 + 2) & (yy < y1 - 2)
    rgb[handle_box & ~handle_hole] = [19, 18, 17]
    if rgba:
        return np.dstack((rgb, alpha))
    return rgb


def make_dark_metal_fixture(*, rgba: bool = True) -> np.ndarray:
    """Add a known dark reflection band to neutral metal, not structural ink.

    The two-pixel band has display luminance 86; the independently chosen right
    anchor is above 170 in the source.  Both belong to the same synthetic metal
    surface.  These labels are fixture facts, not a claim that RGB can identify
    an arbitrary real reflection or groove.
    """
    result = make_fixture(rgba=rgba)
    yy, xx = np.indices(result.shape[:2])
    cx, cy = FIXTURE_METAL_CENTER
    rx, ry = FIXTURE_METAL_RADII
    inner = ((xx - cx) / (rx - 1)) ** 2 + ((yy - cy) / (ry - 1)) ** 2 <= 1
    neutral = np.rint(_luminance(result[..., :3])).clip(0, 255).astype(np.uint8)
    result[..., :3][inner] = np.repeat(neutral[inner, None], 3, axis=1)
    x0, y0, x1, y1 = FIXTURE_DARK_METAL_BAND
    result[y0:y1, x0:x1, :3] = 86
    return result


def palette_lookup(
    material: np.ndarray,
    tone: np.ndarray,
    palette: np.ndarray,
    delta: int | np.ndarray = 0,
) -> np.ndarray:
    """Move tone IDs and select exact LUT colors; never mix RGB values.

    This is a style-band experiment, not removal of baked illumination or
    recovery of normals.  Preserve an existing line mask by supplying zero
    delta at those positions if fixed line color is part of the style contract.
    """
    material = np.asarray(material)
    tone = np.asarray(tone)
    palette = np.asarray(palette)
    if material.shape != tone.shape or material.ndim != 2:
        raise ValueError("material and tone must be equally sized 2D maps")
    if not np.issubdtype(material.dtype, np.integer) or not np.issubdtype(tone.dtype, np.integer):
        raise ValueError("material and tone must contain integer IDs")
    if palette.dtype != np.uint8 or palette.ndim != 3 or palette.shape[2] != 3:
        raise ValueError("palette must be uint8 [material, tone, RGB]")
    if not palette.shape[0] or not palette.shape[1]:
        raise ValueError("palette must contain at least one material and one tone")
    if np.any(material < -1) or np.any(material >= palette.shape[0]):
        raise ValueError("material ID outside palette")
    visible_material = material >= 0
    if np.any(tone[visible_material] < 0) or np.any(tone[visible_material] >= palette.shape[1]):
        raise ValueError("tone ID outside palette")
    shift = np.asarray(delta)
    if not np.issubdtype(shift.dtype, np.integer):
        raise ValueError("delta must contain integer band shifts")
    try:
        shift = np.broadcast_to(shift, tone.shape)
    except ValueError as exc:
        raise ValueError("delta must be broadcastable to the tone map") from exc
    shifted = np.clip(tone.astype(np.int64) + shift.astype(np.int64), 0, palette.shape[1] - 1)
    result = np.zeros((*material.shape, 3), dtype=np.uint8)
    result[visible_material] = palette[material[visible_material], shifted[visible_material]]
    return result


def _component_count(mask: np.ndarray, *, connectivity: int = 4) -> int:
    """Count components using row-run unions without a scipy dependency."""
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2 or connectivity not in (4, 8):
        raise ValueError("2D mask and 4 or 8 connectivity required")
    parent: list[int] = []

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    previous: list[tuple[int, int, int]] = []
    for row in mask:
        boundaries = np.flatnonzero(np.diff(np.pad(row.astype(np.int8), (1, 1))))
        current: list[tuple[int, int, int]] = []
        for start, end in boundaries.reshape(-1, 2):
            index = len(parent)
            parent.append(index)
            current.append((int(start), int(end), index))
        a = b = 0
        while a < len(previous) and b < len(current):
            p0, p1, pi = previous[a]
            c0, c1, ci = current[b]
            overlap = max(p0, c0) < min(p1, c1)
            if connectivity == 8:
                overlap = max(p0, c0) <= min(p1, c1)
            if overlap:
                root_previous, root_current = find(pi), find(ci)
                if root_previous != root_current:
                    parent[root_current] = root_previous
            if p1 <= c1:
                a += 1
            else:
                b += 1
        previous = current
    return len({find(index) for index in range(len(parent))})


def _hole_count(mask: np.ndarray) -> int:
    # Padding makes exactly one connected exterior background component.
    background = ~np.pad(np.asarray(mask, dtype=bool), 1, constant_values=False)
    return max(0, _component_count(background, connectivity=4) - 1)


def _color_count(rgb: np.ndarray, visible: np.ndarray | None = None) -> int:
    colors = np.asarray(rgb)[..., :3]
    colors = colors.reshape(-1, 3) if visible is None else colors[np.asarray(visible, dtype=bool)]
    return int(np.unique(colors, axis=0).shape[0]) if colors.size else 0


def _distinct_luminance_count(values: np.ndarray, minimum_gap: float = 10.0) -> int:
    ordered = np.unique(np.asarray(values, dtype=np.float64))
    if not ordered.size:
        return 0
    count, last = 1, float(ordered[0])
    for value in ordered[1:]:
        if value - last >= minimum_gap:
            count += 1
            last = float(value)
    return count


def verify(
    source: np.ndarray,
    out: np.ndarray,
    report: dict[str, Any],
    maps: dict[str, Any],
    *,
    color_budget: int = 48,
) -> dict[str, Any]:
    """Return independent checks, observations, and explicit uncertified scope.

    Core schema: maps material_id/tone_id/line_mask/alpha/palette; report
    transform uniform_pitch/source_origin/nonlinear_warp and grid_status.
    Exact repeated inputs may use pitch>1.  Other outputs must retain source
    width and height and remain marked uncertified_source_lattice.
    """
    source, out = np.asarray(source), np.asarray(out)
    checks: dict[str, dict[str, Any]] = {}
    observations: dict[str, Any] = {}

    def check(name: str, passed: bool, **details: Any) -> None:
        checks[name] = {"passed": bool(passed), **details}

    source_valid = source.dtype == np.uint8 and source.ndim == 3 and source.shape[-1] in (3, 4)
    output_valid = out.dtype == np.uint8 and out.ndim == 3 and out.shape[-1] in (3, 4)
    check("input_uint8_rgb_or_rgba", source_valid)
    check("output_uint8_rgb_or_rgba", output_valid)
    if not source_valid or not output_valid:
        return _finish(checks, observations, str(report.get("grid_status", "missing")))
    source_alpha = source[..., 3] if source.shape[-1] == 4 else np.full(source.shape[:2], 255, np.uint8)
    out_alpha = out[..., 3] if out.shape[-1] == 4 else np.full(out.shape[:2], 255, np.uint8)
    observations.update({
        "source_shape": list(source.shape),
        "output_shape": list(out.shape),
        "source_array_sha256": sha256(source.tobytes()).hexdigest(),
        "output_array_sha256": sha256(out.tobytes()).hexdigest(),
        "source_rgb_colors_all": _color_count(source),
        "source_rgb_colors_visible": _color_count(source, source_alpha > 0),
        "source_rgb_colors_hidden": _color_count(source, source_alpha == 0),
        "output_rgb_colors_all": _color_count(out),
        "output_rgb_colors_visible": _color_count(out, out_alpha > 0),
        "output_rgb_colors_hidden": _color_count(out, out_alpha == 0),
    })
    check("finite_palette_budget", observations["output_rgb_colors_visible"] <= color_budget,
          actual_visible=observations["output_rgb_colors_visible"], maximum=color_budget,
          hidden_rgb_colors=observations["output_rgb_colors_hidden"])
    check("binary_output_alpha", bool(np.all((out_alpha == 0) | (out_alpha == 255))))
    check("channel_contract", source.shape[-1] == out.shape[-1])

    missing = [key for key in ("material_id", "tone_id", "line_mask", "alpha", "palette") if key not in maps]
    check("canonical_maps_present", not missing, missing=missing)
    if missing:
        return _finish(checks, observations, str(report.get("grid_status", "missing")))
    material, tone = np.asarray(maps["material_id"]), np.asarray(maps["tone_id"])
    line, alpha, palette = np.asarray(maps["line_mask"]), np.asarray(maps["alpha"]), np.asarray(maps["palette"])
    aligned = all(item.shape == out.shape[:2] for item in (material, tone, line, alpha))
    check("canonical_map_alignment", aligned)
    source_maps = {key: np.asarray(value) for key, value in maps.items()
                   if key in ("source_material_id", "source_tone_id", "source_line_mask", "source_alpha")}
    if source_maps:
        check("source_map_alignment", all(value.shape == source.shape[:2] for value in source_maps.values()),
              checked=list(source_maps))
    integer_ids = np.issubdtype(material.dtype, np.integer) and np.issubdtype(tone.dtype, np.integer)
    check("integer_material_and_tone_ids", integer_ids)
    check("binary_line_mask", bool(np.all((line == 0) | (line == 1) | (line == 255))))
    check("palette_uint8_material_tone_rgb", palette.dtype == np.uint8 and palette.ndim == 3 and palette.shape[-1] == 3)
    palette_valid = palette.dtype == np.uint8 and palette.ndim == 3 and palette.shape[-1] == 3
    if palette_valid:
        observations["palette_shape"] = list(palette.shape)
        check("material_tone_capacity", palette.shape[0] <= 12 and palette.shape[1] in (3, 4),
              materials=int(palette.shape[0]), tones=int(palette.shape[1]))
    if aligned:
        check("alpha_map_matches_output", bool(np.array_equal(alpha, out_alpha)))
        check("background_material_only_transparent", not bool(np.any((material == -1) & (out_alpha > 0))))
    if aligned and integer_ids and palette_valid:
        try:
            canonical_rgb = palette_lookup(material, tone, palette)
            # Alpha-zero RGB is nondisplayed data; record its count separately.
            exact = bool(np.array_equal(canonical_rgb[out_alpha > 0], out[..., :3][out_alpha > 0]))
            check("final_visible_rgb_is_exact_palette_lookup", exact)
            lighting_checks = []
            for delta in (-1, 0, 1):
                shifted = palette_lookup(material, tone, palette, np.where(line != 0, 0, delta))
                lighting_checks.append(_color_count(shifted, out_alpha > 0) <= color_budget)
            check("lighting_band_lookup_keeps_palette_budget", all(lighting_checks))
        except (ValueError, IndexError) as exc:
            check("final_visible_rgb_is_exact_palette_lookup", False, reason=str(exc))

    transform = report.get("transform", maps.get("transform", {}))
    pitch = transform.get("uniform_pitch") if isinstance(transform, dict) else None
    origin = transform.get("source_origin") if isinstance(transform, dict) else None
    pitch_valid = isinstance(pitch, (int, np.integer)) and not isinstance(pitch, bool) and pitch >= 1
    origin_valid = pitch_valid and isinstance(origin, (list, tuple)) and len(origin) == 2 and all(
        isinstance(value, Real) and not isinstance(value, bool) and float(value).is_integer() and -pitch < value <= 0
        for value in origin
    )
    uniform = pitch_valid and origin_valid and transform.get("nonlinear_warp") is False
    check("declared_uniform_integer_transform", uniform, transform=transform)
    grid_status = str(report.get("grid_status", "missing"))
    check("grid_status_explicit", grid_status in ("certified_repeated_rgba", "uncertified_source_lattice"), value=grid_status)
    if uniform:
        pitch = int(pitch)
        origin_x, origin_y = int(origin[0]), int(origin[1])
        expected_shape = ((source.shape[0] - origin_y + pitch - 1) // pitch,
                          (source.shape[1] - origin_x + pitch - 1) // pitch)
        geometry_matches = out.shape[:2] == expected_shape
        check("source_and_native_lattice_dimensions", geometry_matches,
              expected_native_shape=list(expected_shape))
        check("pitch_requires_certificate", pitch == 1 or grid_status == "certified_repeated_rgba")
        if geometry_matches:
            source_y = (np.arange(source.shape[0], dtype=np.int64) - origin_y) // pitch
            source_x = (np.arange(source.shape[1], dtype=np.int64) - origin_x) // pitch
            expanded = out[source_y[:, None], source_x[None, :]]
            expanded_alpha = expanded[..., 3] if expanded.shape[-1] == 4 else np.full(source.shape[:2], 255, np.uint8)
            expected_alpha = np.where(source_alpha >= 128, 255, 0).astype(np.uint8)
            observations.update({
                "rgb_changed_pixels": int(np.count_nonzero(np.any(source[..., :3] != expanded[..., :3], axis=-1))),
                "alpha_changed_pixels": int(np.count_nonzero(source_alpha != expanded_alpha)),
                "alpha_threshold_mismatch_pixels": int(np.count_nonzero(expected_alpha != expanded_alpha)),
                "alpha_partial_source_pixels": int(np.count_nonzero((source_alpha > 0) & (source_alpha < 255))),
                "alpha_removed_source_pixels": int(np.count_nonzero((source_alpha > 0) & (expanded_alpha == 0))),
                "hidden_rgb_changed_source_pixels": int(np.count_nonzero(
                    (source_alpha == 0) & np.any(source[..., :3] != expanded[..., :3], axis=-1))),
                "silhouette_components_source_threshold128": _component_count(expected_alpha > 0, connectivity=8),
                "silhouette_components_output": _component_count(expanded_alpha > 0, connectivity=8),
            })
            check("alpha128_coverage_contract", observations["alpha_threshold_mismatch_pixels"] == 0)
            if pitch > 1:
                start_y = origin_y + np.arange(out.shape[0], dtype=np.int64) * pitch
                start_x = origin_x + np.arange(out.shape[1], dtype=np.int64) * pitch
                representative_y = np.clip(start_y, 0, source.shape[0] - 1)
                representative_x = np.clip(start_x, 0, source.shape[1] - 1)
                representative = source[representative_y[:, None], representative_x[None, :]]
                reconstructed = representative[source_y[:, None], source_x[None, :]]
                equal_pixels = np.all(source == reconstructed, axis=-1)
                complete_y = (start_y[source_y] >= 0) & (start_y[source_y] + pitch <= source.shape[0])
                complete_x = (start_x[source_x] >= 0) & (start_x[source_x] + pitch <= source.shape[1])
                complete = complete_y[:, None] & complete_x[None, :]
                complete_pixels = int(np.count_nonzero(complete))
                complete_mismatches = int(np.count_nonzero(complete & ~equal_pixels))
                check("original_rgba_repetition_certificate", complete_pixels > 0 and complete_mismatches == 0,
                      complete_block_pixels=complete_pixels, mismatched_complete_block_pixels=complete_mismatches,
                      mismatched_partial_edge_pixels=int(np.count_nonzero(~complete & ~equal_pixels)))
            fixture = make_fixture(rgba=source.shape[-1] == 4)
            is_fixture = source.shape == fixture.shape and np.array_equal(source, fixture)
            is_dark_fixture = False
            if not is_fixture and source.shape == fixture.shape:
                is_dark_fixture = np.array_equal(source, make_dark_metal_fixture(rgba=source.shape[-1] == 4))
            if is_fixture or is_dark_fixture:
                observations["fixture_kind"] = "dark_metal_reflection" if is_dark_fixture else "bright_metal_and_handle"
                if aligned:
                    expanded_line = line[source_y[:, None], source_x[None, :]] != 0
                    expanded_tone = tone[source_y[:, None], source_x[None, :]]
                    _verify_fixture(expanded, expanded_line, expanded_tone, checks, observations)
                    if is_dark_fixture:
                        _verify_dark_metal_fixture(expanded, expanded_line, expanded_tone, checks)
                else:
                    check("fixture_maps_aligned", False)

    timing_key = next((key for key in ("timings_ms", "timings_seconds", "timings", "stage_timings") if key in report), None)
    timings = report[timing_key] if timing_key else {}
    observations["reported_stage_timings"] = timings
    observations["reported_stage_timing_key"] = timing_key
    timing_valid = isinstance(timings, dict) and bool(timings) and all(
        isinstance(value, Real) and np.isfinite(value) and value >= 0 for value in timings.values()
    )
    check("stage_timings_recorded", timing_valid)
    return _finish(checks, observations, grid_status)


def _verify_fixture(
    expanded: np.ndarray,
    line: np.ndarray,
    tone: np.ndarray,
    checks: dict[str, dict[str, Any]],
    observations: dict[str, Any],
) -> None:
    """Use fixture coordinates and photometric facts, not implementation output."""
    yy, xx = np.indices(expanded.shape[:2])
    cx, cy = FIXTURE_METAL_CENTER
    rx, ry = FIXTURE_METAL_RADII
    metal_interior = ((xx - cx) / (rx - 4)) ** 2 + ((yy - cy) / (ry - 4)) ** 2 <= 1
    bright_band = metal_interior & (xx >= 153) & (yy >= 43) & (yy < 78)
    luminance = _luminance(expanded[..., :3])
    tone_count = int(np.unique(tone[metal_interior]).size)
    luminance_count = _distinct_luminance_count(luminance[metal_interior])
    bright_line_pixels = int(np.count_nonzero(line & bright_band))
    bright_dark_pixels = int(np.count_nonzero((luminance < 60) & bright_band))
    checks["fixture_metal_has_at_least_three_tones"] = {
        "passed": tone_count >= 3 and luminance_count >= 3,
        "tone_ids": tone_count, "distinct_luminance_groups_gap10": luminance_count,
    }
    checks["fixture_bright_band_is_not_dark_line"] = {
        "passed": bright_line_pixels == 0 and bright_dark_pixels == 0,
        "line_pixels": bright_line_pixels, "dark_pixels": bright_dark_pixels,
    }
    observations["fixture_metal_rgb_colors"] = _color_count(expanded, metal_interior)

    x0, y0, x1, y1 = FIXTURE_HANDLE
    handle = luminance[y0:y1, x0:x1] < 60
    components, holes = _component_count(handle, connectivity=8), _hole_count(handle)
    reference_border = np.ones(handle.shape, dtype=bool)
    reference_border[2:-2, 2:-2] = False
    structural_coverage = int(np.count_nonzero(handle & reference_border))
    reference_pixels = int(np.count_nonzero(reference_border))
    center_is_clear = bool(np.all(~handle[5:-5, 5:-5]))
    checks["fixture_thin_handle_connected_with_hole"] = {
        "passed": components == 1 and holes == 1 and center_is_clear and structural_coverage >= reference_pixels // 2,
        "components_8_connected": components, "holes_4_connected_background": holes,
        "dark_border_pixels": structural_coverage, "reference_border_pixels": reference_pixels,
        "central_hole_clear": center_is_clear,
    }
    # Four sides and the interior divider have explicit one-pixel coordinates.
    outline = ((xx >= 8) & (xx < 184) & ((yy == 14) | (yy == 113))) | (
        (yy >= 14) & (yy < 114) & ((xx == 8) | (xx == 183)))
    divider = (xx == 108) & (yy >= 22) & (yy < 106)
    outline_missing = int(np.count_nonzero((luminance >= 60) & (outline | divider)))
    checks["fixture_one_pixel_structural_outline_survives"] = {
        "passed": outline_missing == 0, "missing_dark_pixels": outline_missing,
    }


def _verify_dark_metal_fixture(
    expanded: np.ndarray,
    line: np.ndarray,
    tone: np.ndarray,
    checks: dict[str, dict[str, Any]],
) -> None:
    """Check the independently labeled two-pixel reflection and its contrast."""
    x0, y0, x1, y1 = FIXTURE_DARK_METAL_BAND
    ax0, ay0, ax1, ay1 = FIXTURE_DARK_METAL_ANCHOR
    luminance = _luminance(expanded[..., :3])
    band_luma = float(np.median(luminance[y0:y1, x0:x1]))
    anchor_luma = float(np.median(luminance[ay0:ay1, ax0:ax1]))
    band_tone = float(np.median(tone[y0:y1, x0:x1]))
    anchor_tone = float(np.median(tone[ay0:ay1, ax0:ax1]))
    accepted_line_pixels = int(np.count_nonzero(line[y0:y1, x0:x1]))
    checks["fixture_dark_metal_band_not_accepted_outline"] = {
        "passed": accepted_line_pixels == 0 and band_luma >= 60,
        "accepted_line_pixels": accepted_line_pixels,
        "output_band_median_luminance": band_luma,
        "known_source_band_luminance": 86,
    }
    checks["fixture_dark_metal_band_keeps_tone_contrast"] = {
        "passed": anchor_luma - band_luma >= 30 and anchor_tone > band_tone,
        "output_luminance_contrast": anchor_luma - band_luma,
        "minimum_luminance_contrast": 30,
        "output_band_median_tone_id": band_tone,
        "output_anchor_median_tone_id": anchor_tone,
        "known_source_anchor_minimum_luminance": 170,
    }


def _finish(
    checks: dict[str, dict[str, Any]], observations: dict[str, Any], grid_status: str
) -> dict[str, Any]:
    failures = [name for name, item in checks.items() if not item["passed"]]
    fixture_checks = [item["passed"] for name, item in checks.items() if name.startswith("fixture_")]
    return {
        "ok": not failures,
        "passed": not failures,
        "failures": failures,
        "checks": checks,
        "observations": observations,
        "fixture_tested": bool(fixture_checks),
        "fixture_features_passed": all(fixture_checks) if fixture_checks else None,
        "global_logical_grid_certified": grid_status == "certified_repeated_rgba" and
        checks.get("original_rgba_repetition_certificate", {"passed": False})["passed"],
        "grid_status_reported_by_core": grid_status,
        "whole_normalization_completed": False,
        "art_approval": False,
        "physical_material_or_lighting_recovered": False,
        "scope": "Numeric invariants and only the independently known fixture features; not whole-image artistic or semantic reconstruction.",
    }
