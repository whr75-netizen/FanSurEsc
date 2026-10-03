"""Native-grid material lookup from an immutable design reference.

The caller owns geometry, UVs, coverage, structural lines and compositing.
This module maps each UV to its specified source surface and assigns an actual
observed RGB palette entry. It does not resize an image, estimate depth, fit a
shade polynomial, remove a halo, draw details or perform pairwise optimization.

Configuration: {material: {"quad": [[x,y], ...], "palette_samples":
[[x0,y0,x1,y1], ...], "tones": 4, "median3x3": False}}. Quad order is UV
00,10,11,01. Source XY uses pixel-center coordinates: integer (x,y) denotes
that source texel's center. Rectangles use integer, half-open array bounds.
An optional {"materials": ...} wrapper is also accepted.
"""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _lab(rgb: np.ndarray) -> np.ndarray:
    """CIELAB with the D65/sRGB conversion used by the reference pipeline."""
    s = np.asarray(rgb, dtype=np.float64) / 255.0
    linear = np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
    xyz = linear @ np.array([[.4124564, .2126729, .0193339],
                             [.3575761, .7151522, .1191920],
                             [.1804375, .0721750, .9503041]])
    xyz /= np.array([.95047, 1., 1.08883])
    delta = 6. / 29.
    f = np.where(xyz > delta ** 3, np.cbrt(xyz),
                 xyz / (3. * delta ** 2) + 4. / 29.)
    return np.stack((116. * f[..., 1] - 16.,
                     500. * (f[..., 0] - f[..., 1]),
                     200. * (f[..., 1] - f[..., 2])), axis=-1)


def _histogram_candidates(rgb: np.ndarray, maximum: int = 4096):
    """Bounded weighted candidates; every candidate is an observed source RGB.

    Adaptive Lab histogram cells retain their aggregate population and the
    observed RGB nearest their weighted Lab centroid. No centroid RGB becomes
    a palette entry. Reduction concerns palette fitting only, never positions.
    """
    observed, weights = np.unique(rgb, axis=0, return_counts=True)
    lab = _lab(observed)
    if len(observed) <= maximum:
        return observed, lab, weights.astype(float), 0., len(observed)
    step = 1.
    while True:
        bins = np.floor((lab + [0., 128., 128.]) / step).astype(np.int32)
        _, group = np.unique(bins, axis=0, return_inverse=True)
        count = int(group.max()) + 1
        if count <= maximum:
            break
        step *= 2.
    population = np.bincount(group, weights=weights, minlength=count)
    centers = np.stack([np.bincount(group, weights=weights * lab[:, axis],
                                    minlength=count) / population
                        for axis in range(3)], axis=1)
    error = np.sum((lab - centers[group]) ** 2, axis=1)
    # np.unique's lexicographic RGB order supplies the final deterministic tie.
    order = np.lexsort((np.arange(len(observed)), error, group))
    first = order[np.r_[True, group[order][1:] != group[order][:-1]]]
    return observed[first], lab[first], population[group[first]], step, len(observed)


def _palette(rgb: np.ndarray, count: int):
    colors, lab, weights, histogram_step, unique_count = _histogram_candidates(rgb)
    if len(colors) < count:
        raise ValueError(f"palette needs {count} observed tones; only {len(colors)} candidates")
    by_lightness = np.argsort(lab[:, 0], kind="stable")
    cumulative = np.cumsum(weights[by_lightness]) / weights.sum()
    indices = []
    for quantile in np.linspace(.02, .98, count):
        index = int(by_lightness[min(int(np.searchsorted(cumulative, quantile)),
                                    len(by_lightness) - 1)])
        if index in indices:
            available = np.array([i for i in range(len(colors)) if i not in indices])
            index = int(available[np.argmin(np.abs(lab[available, 0] - lab[index, 0]))])
        indices.append(index)
    indices = np.array(indices, dtype=np.int32)
    iterations = 0
    # For squared Euclidean Lab, the cluster's observed point nearest its
    # weighted centroid minimizes the weighted sum of squared distances.
    # This is deterministic Lloyd-style observed-medoid updating, not PAM or
    # a claim of globally optimal palette/label selection.
    for iterations in range(1, 33):
        squared = np.sum((lab[:, None, :] - lab[indices][None, :, :]) ** 2, axis=2)
        labels = np.argmin(squared, axis=1)
        updated = indices.copy()
        for label in range(count):
            members = np.flatnonzero(labels == label)
            if not len(members):
                available = np.array([i for i in range(len(colors)) if i not in updated])
                nearest = squared[available].min(axis=1)
                updated[label] = available[np.argmax(nearest * weights[available])]
                continue
            centroid = np.average(lab[members], axis=0, weights=weights[members])
            updated[label] = members[np.argmin(np.sum((lab[members] - centroid) ** 2, axis=1))]
        if np.array_equal(updated, indices):
            break
        indices = updated
    indices = indices[np.argsort(lab[indices, 0], kind="stable")]
    palette = colors[indices].copy()
    palette_lab = lab[indices].copy()
    source_lab = _lab(rgb)
    error = np.sqrt(np.sum((source_lab[:, None, :] - palette_lab[None, :, :]) ** 2,
                          axis=2).min(axis=1))
    return palette, palette_lab, {
        "method": "weighted_Lloyd_observed_Lab_medoid",
        "global_optimum_claimed": False,
        "source_sample_count": int(len(rgb)),
        "source_unique_rgb": int(unique_count),
        "bounded_candidate_count": int(len(colors)),
        "candidate_histogram_lab_step": histogram_step,
        "iterations": iterations,
        "palette_rgb": palette.tolist(),
        "palette_lab_l": palette_lab[:, 0].tolist(),
        "source_lab_l_q05_q50_q95": np.percentile(source_lab[:, 0], [5, 50, 95]).tolist(),
        "nearest_palette_deltaE76_q50_q95": np.percentile(error, [50, 95]).tolist(),
    }


class Appearance:
    """Surface-local texture sampling and source-observed palette assignment."""

    def __init__(self, reference_path: str | Path, config: dict[str, Any]):
        self.reference_path = Path(reference_path).resolve()
        content = self.reference_path.read_bytes()
        self._reference_sha = sha256(content).hexdigest()
        self._rgba = np.asarray(Image.open(BytesIO(content)).convert("RGBA")).copy()
        self._rgba.setflags(write=False)
        self._height, self._width = self._rgba.shape[:2]
        definitions = config.get("materials", config)
        if not isinstance(definitions, dict) or not definitions:
            raise ValueError("nonempty material configuration required")
        self._materials: dict[str, dict[str, Any]] = {}
        self.palettes: dict[str, np.ndarray] = {}
        self._reports: dict[str, dict[str, Any]] = {}
        for name, settings in definitions.items():
            quad = np.asarray(settings["quad"], dtype=float)
            if quad.shape != (4, 2) or not np.isfinite(quad).all():
                raise ValueError(f"{name}: quad needs four finite source XY vertices")
            if (quad[:, 0].min() < 0 or quad[:, 1].min() < 0 or
                quad[:, 0].max() > self._width - 1 or quad[:, 1].max() > self._height - 1):
                raise ValueError(f"{name}: quad exceeds reference pixel-center bounds")
            edges = np.roll(quad, -1, axis=0) - quad
            next_edges = np.roll(edges, -1, axis=0)
            crosses = edges[:, 0] * next_edges[:, 1] - edges[:, 1] * next_edges[:, 0]
            if not (np.all(crosses > 1e-9) or np.all(crosses < -1e-9)):
                raise ValueError(f"{name}: source quad must be convex and nondegenerate")
            tones = settings["tones"]
            if isinstance(tones, bool) or not isinstance(tones, int) or not 2 <= tones <= 16:
                raise ValueError(f"{name}: tones must be an integer in 2..16")
            rectangles = settings["palette_samples"]
            if not rectangles:
                raise ValueError(f"{name}: palette_samples cannot be empty")
            # The mask deduplicates overlapping rectangles without changing any
            # source coordinate or deleting a halo around structural features.
            selected = np.zeros((self._height, self._width), dtype=bool)
            rectangle_report = []
            for rectangle in rectangles:
                values = np.asarray(rectangle)
                if values.shape != (4,) or not np.isfinite(values).all() or not np.equal(values, np.floor(values)).all():
                    raise ValueError(f"{name}: rectangles need four integer bounds")
                x0, y0, x1, y1 = map(int, values)
                if not (0 <= x0 < x1 <= self._width and 0 <= y0 < y1 <= self._height):
                    raise ValueError(f"{name}: invalid source rectangle {rectangle}")
                selected[y0:y1, x0:x1] = True
                rectangle_report.append([x0, y0, x1, y1])
            rgb = self._rgba[..., :3]
            black = np.all(rgb == 0, axis=-1)
            selected &= (self._rgba[..., 3] > 0) & ~black
            if not selected.any():
                raise ValueError(f"{name}: palette rectangles have no visible nonblack samples")
            palette, palette_lab, statistics = _palette(rgb[selected], tones)
            palette.setflags(write=False)
            self.palettes[name] = palette
            self._materials[name] = {"quad": quad.copy(), "palette_lab": palette_lab,
                                     "median3x3": bool(settings.get("median3x3", False))}
            self._reports[name] = {"source_quad_uv00_10_11_01": quad.tolist(),
                                   "palette_rectangles_half_open": rectangle_report,
                                   "median3x3": self._materials[name]["median3x3"],
                                   **statistics}

    def _local_medoid(self, xy: np.ndarray, base_rgb: np.ndarray, quad: np.ndarray):
        offsets = np.array([(x, y) for y in (-1, 0, 1) for x in (-1, 0, 1)])
        positions = xy[:, None, :] + offsets[None, :, :]
        valid = ((positions[..., 0] >= 0) & (positions[..., 0] < self._width) &
                 (positions[..., 1] >= 0) & (positions[..., 1] < self._height))
        for start, end in zip(quad, np.roll(quad, -1, axis=0)):
            edge = end - start
            side = edge[0] * (positions[..., 1] - start[1]) - edge[1] * (positions[..., 0] - start[0])
            # Convex membership is independent of the quad's winding.
            midpoint = quad.mean(axis=0) - start
            orientation = edge[0] * midpoint[1] - edge[1] * midpoint[0]
            valid &= side * orientation >= -1e-9
        safe = positions.copy()
        safe[..., 0] = safe[..., 0].clip(0, self._width - 1)
        safe[..., 1] = safe[..., 1].clip(0, self._height - 1)
        patch = self._rgba[safe[..., 1], safe[..., 0]]
        valid &= (patch[..., 3] > 0) & np.any(patch[..., :3] != 0, axis=-1)
        candidate_lab = _lab(patch[..., :3])
        has_neighbors = valid.any(axis=1)
        result = base_rgb.copy()
        if has_neighbors.any():
            local = np.where(valid[has_neighbors, :, None], candidate_lab[has_neighbors], np.nan)
            target = np.nanmedian(local, axis=1)
            distances = np.sum((candidate_lab[has_neighbors] - target[:, None, :]) ** 2, axis=2)
            distances[~valid[has_neighbors]] = np.inf
            result[has_neighbors] = patch[has_neighbors, np.argmin(distances, axis=1), :3]
        return result

    def sample(self, material: str, u_array, v_array) -> np.ndarray:
        """Return flattened N x 3 uint8 RGB; UV is clamped to this source quad.

        Bilinear interpolation maps coordinates only. No interpolated RGB is
        introduced. Black source texels map to the darkest permitted material
        color by nearest Lab, while final black lines belong to the caller.
        Transparent source texels raise an input error instead of borrowing a
        distant color. Optional 3x3 filtering selects an observed local medoid.
        """
        settings = self._materials[material]
        u, v = np.broadcast_arrays(np.asarray(u_array, float), np.asarray(v_array, float))
        if not np.isfinite(u).all() or not np.isfinite(v).all():
            raise ValueError("UV values must be finite")
        u, v = u.ravel().clip(0., 1.), v.ravel().clip(0., 1.)
        if not len(u):
            return np.empty((0, 3), dtype=np.uint8)
        quad = settings["quad"]
        xy = ((1-u)[:, None] * (1-v)[:, None] * quad[0] +
              u[:, None] * (1-v)[:, None] * quad[1] +
              u[:, None] * v[:, None] * quad[2] +
              (1-u)[:, None] * v[:, None] * quad[3])
        texels = np.floor(xy + .5).astype(np.int32)
        source = self._rgba[texels[:, 1], texels[:, 0]]
        if np.any(source[:, 3] == 0):
            bad = texels[source[:, 3] == 0][:5].tolist()
            raise ValueError(f"{material}: UV mapped to transparent source texels: {bad}")
        rgb = source[:, :3]
        if settings["median3x3"]:
            rgb = self._local_medoid(texels, rgb, quad)
        lab = _lab(rgb)
        squared = np.sum((lab[:, None, :] - settings["palette_lab"][None, :, :]) ** 2,
                         axis=2)
        ids = np.argmin(squared, axis=1)
        return self.palettes[material][ids].copy()

    def report(self) -> dict[str, Any]:
        """JSON-compatible input/palette provenance; no art approval claim."""
        return {"reference_path": str(self.reference_path),
                "reference_sha256": self._reference_sha,
                "reference_size": [self._width, self._height],
                "source_coordinates": "integer XY denotes source pixel center",
                "rgb_interpolation": False,
                "spatial_shade_fit": False,
                "halo_exclusion": False,
                "pairwise_label_optimization_implemented": False,
                "black_palette_entries_permitted": False,
                "materials": self._reports}
