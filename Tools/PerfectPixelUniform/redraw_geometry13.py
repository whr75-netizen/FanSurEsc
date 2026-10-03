"""R13 source-space masks, robust geometry and feature-constrained authored grid."""
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'LocalOnly/PerfectPixelOpenCV'))
import cv2


def largest(mask):
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if count < 2:
        raise ValueError('GEOMETRY_EMPTY_ROLE')
    return labels == (1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]))


def inside(points, polygon):
    """Half-open ray crossing at continuous texel centers; no vertex snapping."""
    points, polygon = np.asarray(points), np.asarray(polygon)
    x, y = points[..., 0], points[..., 1]
    result = np.zeros(x.shape, bool)
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        if abs(b[1] - a[1]) < 1e-12:
            continue
        cross = ((a[1] > y) != (b[1] > y))
        at = (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
        result ^= cross & (x < at)
    return result


def contour(mask):
    found = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    return max(found, key=cv2.contourArea).reshape(-1, 2).astype(float) + .5


def fit(points):
    # Welsch robust orthogonal fitting; returned direction sign is canonical.
    d = cv2.fitLine(np.asarray(points, np.float32), cv2.DIST_WELSCH, 0, .01, .001).reshape(-1)
    direction = d[:2].astype(float)
    if direction[0] < 0 or (abs(direction[0]) < 1e-6 and direction[1] < 0):
        direction *= -1
    normal = np.array([-direction[1], direction[0]])
    offset = float(normal @ d[2:])
    return direction, normal, offset


def fitted_polygon(points, epsilon, minimum_edge=12):
    """Contour -> robust supporting lines -> adjacent shared intersections."""
    raw = cv2.approxPolyDP(np.asarray(points, np.float32), epsilon, True).reshape(-1, 2)
    lines, residuals = [], []
    for a, b in zip(raw, np.roll(raw, -1, axis=0)):
        delta = b - a
        length = np.linalg.norm(delta)
        direction = delta / length
        normal = np.array([-direction[1], direction[0]])
        t = (points - a) @ direction
        distance = np.abs((points - a) @ normal)
        selected = points[(t >= 1) & (t <= length - 1) & (distance < epsilon + 1)]
        if length >= minimum_edge and len(selected) >= 8:
            _, normal, offset = fit(selected)
            residuals.append(float(np.percentile(np.abs(selected @ normal - offset), 90)))
        else:
            offset = float(normal @ a)
        lines.append((normal, offset))
    vertices = []
    for i in range(len(lines)):
        n0, c0 = lines[i - 1]; n1, c1 = lines[i]
        matrix = np.array([n0, n1])
        if abs(np.linalg.det(matrix)) < .04:
            vertices.append(raw[i].astype(float))
            continue
        q = np.linalg.solve(matrix, np.array([c0, c1]))
        if np.linalg.norm(q - raw[i]) > 2 * epsilon + 2:
            raise ValueError('GEOMETRY_UNSTABLE_INTERSECTION')
        vertices.append(q)
    return np.asarray(vertices), residuals


def masks(rgba):
    r, g, b, a = [rgba[..., i].astype(float) for i in range(4)]
    # Input suitability for this wood/teal/brass cabinet, not semantic universality.
    warm = (r > g * 1.10) & (g > b * 1.20) & (r - b > 32) & (g > 45) & (g > r * .4) & (a > 160)
    # Dim brass becomes nearly neutral in this source. Requiring high saturation
    # removes the upper halves of real continuous frame edges. The observed
    # blue paint has B>R, so the warmer R-B sign separates these shadowed trims.
    metal = (r > g * .98) & (g > b * 1.07) & (r - b > 5) & (g > 30) & (g > r * .4) & (a > 160)
    paint = (b > r * .95) & (g > r * .98) & (a > 160)
    body = cv2.morphologyEx((warm | paint | metal).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    body = largest(body)
    deep = cv2.distanceTransform(warm.astype(np.uint8), cv2.DIST_L2, 5) > 3
    core = largest(deep)
    hull = cv2.convexHull(contour(core).astype(np.float32)).reshape(-1, 2)
    seed = cv2.approxPolyDP(hull, 6, True).reshape(-1, 2)
    if len(seed) != 4:
        raise ValueError('WOOD_FACE_NOT_QUADRILATERAL')
    # Use original warm-mask boundary near the eroded wood-core hull, not erosion
    # offset as geometry. Small interior grain islands cannot enter this contour.
    near = cv2.dilate(core.astype(np.uint8), np.ones((17, 17), np.uint8)) > 0
    wood = largest(warm & near)
    boundary = contour(wood)
    edges, errors = [], []
    for start, end in zip(seed, np.roll(seed, -1, axis=0)):
        d = end - start; length = np.linalg.norm(d); d /= length
        n = np.array([-d[1], d[0]])
        t = (boundary - start) @ d
        distance = np.abs((boundary - start) @ n)
        points = boundary[(t > length * .08) & (t < length * .92) & (distance < 8)]
        if len(points) < 12:
            raise ValueError('WOOD_EDGE_SUPPORT_MISSING')
        _, n, c = fit(points)
        edges.append((n, c))
        errors.append(float(np.percentile(np.abs(points @ n - c), 90)))
    wood_poly = np.array([np.linalg.solve(np.array([edges[i - 1][0], edges[i][0]]),
                                         np.array([edges[i - 1][1], edges[i][1]])) for i in range(4)])
    yy, xx = np.indices(body.shape)
    centers = np.stack((xx + .5, yy + .5), -1)
    wood_coverage = inside(centers, wood_poly)
    return body, wood_coverage, metal & body & ~wood_coverage, wood_poly, errors


def structural_lines(gold, wood_poly):
    lines = cv2.HoughLinesP(gold.astype(np.uint8) * 255, 1, np.pi / 180,
                           threshold=18, minLineLength=25, maxLineGap=3)
    if lines is None:
        raise ValueError('STRUCTURE_NO_LINES')
    segments = lines.reshape(-1, 4).astype(float) + .5
    # Family directions derive from observed wood edges and long near-vertical
    # brass supports. No forced +/- .5 screen slope.
    edge = np.roll(wood_poly, -1, axis=0) - wood_poly
    ed = edge / np.linalg.norm(edge, axis=1)[:, None]
    ed = np.where(ed[:, :1] < 0, -ed, ed)
    minus = np.median(ed[ed[:, 1] < 0], axis=0); minus /= np.linalg.norm(minus)
    plus = np.median(ed[ed[:, 1] > 0], axis=0); plus /= np.linalg.norm(plus)
    vertical_points = []
    for a, b in segments.reshape(-1, 2, 2):
        d = b - a
        if abs(d[0]) < .06 * abs(d[1]):
            vertical_points.append(d * np.sign(d[1]))
    if not vertical_points:
        raise ValueError('STRUCTURE_VERTICAL_FAMILY_MISSING')
    vertical = np.median(np.array(vertical_points) / np.linalg.norm(vertical_points, axis=1)[:, None], axis=0)
    vertical /= np.linalg.norm(vertical)
    families = [minus, plus, vertical]
    result = []
    y, x = np.nonzero(gold); support = np.stack((x + .5, y + .5), -1)
    for fi, direction in enumerate(families):
        normal = np.array([-direction[1], direction[0]])
        candidates = []
        for a, b in segments.reshape(-1, 2, 2):
            d = b - a; length = np.linalg.norm(d)
            if abs((d / length) @ direction) < np.cos(np.deg2rad(5)):
                continue
            candidates.append((float(normal @ ((a + b) / 2)), min(a @ direction, b @ direction),
                               max(a @ direction, b @ direction)))
        candidates.sort()
        clusters = []
        for candidate in candidates:
            if clusters and abs(candidate[0] - np.median([v[0] for v in clusters[-1]])) <= 4:
                clusters[-1].append(candidate)
            else:
                clusters.append([candidate])
        for cluster in clusters:
            c = np.median([v[0] for v in cluster]); t0 = min(v[1] for v in cluster); t1 = max(v[2] for v in cluster)
            ts, ns = support @ direction, support @ normal
            selected = support[(np.abs(ns - c) < 4) & (ts >= t0 - 2) & (ts <= t1 + 2)]
            if len(selected) < 15:
                continue
            # Intercept is robust on the common family, not a new local rotation.
            c = float(np.median(selected @ normal))
            # Source texel centers cover two additional half-texel end extents.
            width = float(np.percentile(selected @ normal, 90) - np.percentile(selected @ normal, 10) + 1)
            # Equal intercept is insufficient: different door frames can have
            # collinear edges separated by a real gap. Split on source support.
            order = np.argsort(selected @ direction)
            ordered = selected[order]; projections = ordered @ direction
            split = np.flatnonzero(np.diff(projections) > 3.5) + 1
            for group in np.split(ordered, split):
                lo, hi = np.percentile(group @ direction, [1, 99])
                if hi - lo < 25:
                    continue
                a, b = direction * lo + normal * c, direction * hi + normal * c
                result.append({'family': fi, 'a': a.tolist(), 'b': b.tolist(), 'width': width,
                               'kind': 'metal_band' if width >= 5.2 else 'trim_line',
                               'support': int(len(group)),
                               'error_p90': float(np.percentile(np.abs(group @ normal - c), 90))})
    return result, np.asarray(families)


def small_features(gold, lines, body):
    # Knobs touching thin trim cannot be detected after removing long lines:
    # that subtracts their own cells. Compact thickness cores are independent
    # foreground seeds, detected BEFORE line ownership.
    thickness=cv2.distanceTransform(gold.astype(np.uint8),cv2.DIST_L2,5)
    count,core_labels,stats,_=cv2.connectedComponentsWithStats((thickness>1.4).astype(np.uint8),8)
    labels=np.zeros(gold.shape,np.int32);features=[]
    boundary_distance = cv2.distanceTransform(body.astype(np.uint8), cv2.DIST_L2, 5)
    for i in range(1, count):
        x, y, w, h, area = stats[i].tolist()
        interior=boundary_distance[y:y+h,x:x+w].max()>8
        coords=np.argwhere(core_labels==i)
        eigen=np.linalg.eigvalsh(np.cov(coords.T)) if len(coords)>2 else np.array([.01,100.])
        aspect=float(np.sqrt(max(eigen[-1],.01)/max(eigen[0],.01)))
        peak=float(thickness[core_labels==i].max())
        if area<10 or max(w,h)>20 or aspect>3.2 or peak<2.4 or not interior:
            continue
        component=cv2.dilate((core_labels==i).astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)&gold
        # Overlapping seeds do not create overlapping authorities.
        component&=labels==0
        if component.sum()<12:continue
        ys,xs=np.nonzero(component);lo=[int(xs.min()),int(ys.min())];hi=[int(xs.max()+1),int(ys.max()+1)]
        index=len(features)+1;labels[component]=index
        features.append({'id':index-1,'bbox':lo+hi,'area':int(component.sum()),
                         'mask_label':index,'minimum_width':int(min(np.array(hi)-lo)),
                         'seed_area':area,'seed_aspect':aspect,'seed_peak_width':peak,
                         'role':'compact_thick_metal_detail'})
    return features, labels


def geometry(rgba):
    body, wood, gold, top, errors = masks(rgba)
    # This closed cabinet's outer profile is convex. Source role thresholds cut
    # notches under the cap; the convex profile restores these missing edge
    # samples, while no door/handle topology is inferred from the hull.
    outer = cv2.convexHull(contour(body | wood).astype(np.float32)).reshape(-1, 2)
    silhouette, errors_body = fitted_polygon(outer, 4, minimum_edge=18)
    features, labels = small_features(gold, [], body)
    # Source knob blobs cannot vote for an extended plane-boundary line.
    lines, families = structural_lines(gold & (labels==0), top)
    if len(features) < 2:
        raise ValueError('DETAIL_SMALL_FEATURES_NOT_DETECTED')
    origin = np.floor(np.minimum(silhouette.min(0), top.min(0)) - 2)
    maximum = np.maximum(silhouette.max(0), top.max(0)) + 2
    # Grid is chosen by measured small-feature support, not a desired image slot.
    candidates = []
    for pitch in [4., 3.5, 3., 2.5, 2.]:
        shape = np.ceil((maximum - origin) / pitch).astype(int)
        yy, xx = np.indices(tuple(shape[::-1])); centers = origin + pitch * np.stack((xx + .5, yy + .5), -1)
        xs = np.clip(np.floor(centers[..., 0]).astype(int), 0, rgba.shape[1] - 1)
        ys = np.clip(np.floor(centers[..., 1]).astype(int), 0, rgba.shape[0] - 1)
        ids = labels[ys, xs]
        observed = []
        for feature in features:
            cells = np.argwhere(ids == feature['mask_label'])
            minimum = 0 if not len(cells) else int(np.min(cells.max(0) - cells.min(0) + 1))
            # Dark/middle/light plus a clean boundary need three-cell transverse
            # support and at least 12 cells per compact source detail cluster.
            observed.append({'feature': feature['id'], 'cells': int(len(cells)), 'minimum_span': minimum})
        broad_bands=[v['width'] for v in lines if v['kind']=='metal_band' and v['width']>=6]
        band_support=[v/pitch for v in broad_bands]
        passed = all(v['minimum_span'] >= 3 and v['cells'] >= 12 for v in observed)
        passed &= bool(band_support) and min(band_support)>=3
        candidates.append({'pitch': pitch, 'size': shape.tolist(), 'features': observed,
                           'main_metal_band_width_cells':band_support,'accepted': bool(passed)})
    valid = [v for v in candidates if v['accepted']]
    if not valid:
        raise ValueError('GRID_UNDERSAMPLED_FEATURES')
    chosen = valid[0]
    return {'silhouette': silhouette.tolist(), 'top': top.tolist(), 'lines': lines,
            'families': families.tolist(), 'features': features, 'origin': origin.tolist(),
            'pitch': chosen['pitch'], 'size': chosen['size'], 'candidates': candidates,
            'fit_residuals_source_px': errors + errors_body,
            'observed_grid_recovered': False}, (body, wood, gold, labels)
