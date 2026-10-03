"""Choose source coordinates from raw local color regions, never palette counts.

This is area sampling, not stroke recovery: details smaller than a cell can
still disappear. The threshold is explicit Oklab distance, not a body-part rule.
"""
import numpy as np


def pick_region_sample(lab, allowed, center, threshold):
    """Local 4-connected regions; area first, geometric center breaks ties.

    center is the continuous target-cell center in source-pixel coordinates.
    At an exact half-pixel tie, prefer bottom/right, like center sampling.
    Return local (y,x). No output color is computed here.
    """
    ys, xs = np.nonzero(allowed)
    if not len(ys):
        return None
    labels = np.full(allowed.shape, -1, np.int32)
    counts = []
    for y, x in zip(ys, xs):
        if labels[y, x] >= 0:
            continue
        owner = len(counts)
        labels[y, x] = owner
        stack, size = [(int(y), int(x))], 0
        while stack:
            yy, xx = stack.pop()
            size += 1
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = yy + dy, xx + dx
                if not (0 <= ny < allowed.shape[0] and 0 <= nx < allowed.shape[1]):
                    continue
                if not allowed[ny, nx] or labels[ny, nx] >= 0:
                    continue
                d = lab[yy, xx] - lab[ny, nx]
                if np.dot(d, d) <= threshold * threshold:
                    labels[ny, nx] = owner
                    stack.append((ny, nx))
        counts.append(size)
    weight = np.asarray(counts)[labels[ys, xs]]
    distance = (ys - center[0]) ** 2 + (xs - center[1]) ** 2
    index = np.lexsort((-xs, -ys, distance, -weight))[0]
    return int(ys[index]), int(xs[index])
