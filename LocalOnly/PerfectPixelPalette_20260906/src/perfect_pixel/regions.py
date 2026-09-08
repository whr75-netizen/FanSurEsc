"""Source-preserving, explicit color-range masks BEFORE palette abstraction.

HSV range tests + seed-connected regions. Not semantic segmentation. User/agent
annotations are stored outside the engine; ambiguous labels are never recolored.
"""
from dataclasses import dataclass, asdict
from collections import deque
import hashlib
import numpy as np


@dataclass(frozen=True)
class RegionSpec:
    name: str
    # Each range is (hue_low_deg, hue_high_deg, sat_low, sat_high, val_low, val_high).
    # Hue low > high denotes a wrap across red. 0..360 includes all hues.
    hsv_ranges: tuple
    seeds: tuple = ()  # original pixel coordinates (x,y); no resizing
    boxes: tuple = ()  # optional union of [left,top,right,bottom), original pixels
    priority: int = 0  # explicit precedence only; equal priorities stay ambiguous


def rgb_to_hsv(rgb):
    rgb = np.asarray(rgb, dtype=np.float32) / 255.0
    high = rgb.max(axis=-1)
    low = rgb.min(axis=-1)
    delta = high - low
    safe = np.where(delta > 0, delta, 1)
    r,g,b = np.moveaxis(rgb, -1, 0)
    hue = np.zeros_like(high)
    chromatic = delta > 0
    red = chromatic & (high == r)
    green = chromatic & ~red & (high == g)
    blue = chromatic & ~red & ~green
    hue[red] = ((g-b)/safe)[red] % 6
    hue[green] = ((b-r)/safe + 2)[green]
    hue[blue] = ((r-g)/safe + 4)[blue]
    saturation = delta / np.where(high > 0, high, 1)
    return np.stack([hue*60, saturation, high], axis=-1)


def _validate(spec, width, height):
    if not isinstance(spec.name, str) or not spec.name.strip():
        raise ValueError('Region name must be nonempty.')
    if not spec.hsv_ranges:
        raise ValueError('A region requires at least one explicit HSV range.')
    for bounds in spec.hsv_ranges:
        if len(bounds) != 6 or not np.isfinite(bounds).all():
            raise ValueError('HSV range needs six finite numbers.')
        hl,hh,sl,sh,vl,vh = bounds
        if not (0 <= hl <= 360 and 0 <= hh <= 360 and 0 <= sl <= sh <= 1 and 0 <= vl <= vh <= 1):
            raise ValueError('HSV ranges use hue 0..360, saturation/value 0..1.')
    if isinstance(spec.priority, bool) or not isinstance(spec.priority, int):
        raise ValueError('Priority must be an integer.')
    for x,y in spec.seeds:
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (x,y)) or not (0 <= x < width and 0 <= y < height):
            raise ValueError('Seed is not a valid original-image pixel: %s' % ((x,y),))
    for box in spec.boxes:
        if len(box) != 4 or not all(isinstance(v, int) and not isinstance(v, bool) for v in box):
            raise ValueError('Boxes need four integer coordinates.')
        x0,y0,x1,y1 = box
        if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            raise ValueError('Box must stay within original image.')


def _connected(candidate, seeds):
    """Union of 4-connected components reached by the explicit seeds."""
    if not seeds:
        return candidate.copy(), []
    h,w = candidate.shape
    selected = np.zeros_like(candidate)
    pending = deque()
    missed = []
    for x,y in seeds:
        if not candidate[y,x]:
            missed.append([x,y])
        elif not selected[y,x]:
            selected[y,x] = True
            pending.append((x,y))
    while pending:
        x,y = pending.popleft()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < w and 0 <= ny < h and candidate[ny,nx] and not selected[ny,nx]:
                selected[ny,nx] = True
                pending.append((nx,ny))
    return selected, missed


def classify_regions(image, specs):
    """Return integer labels + provenance; original RGB/alpha are never changed.

    -1 = unassigned, -2 = equal-priority conflict, -3 = transparent.
    Lower-priority regions cannot absorb an accent with explicit higher priority.
    No automatic nearest-family fallback, blur, desaturation or palette selection.
    """
    a = np.asarray(image)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] not in (3,4) or min(a.shape[:2]) < 1:
        raise ValueError('Expected a nonempty uint8 RGB/RGBA image.')
    h,w = a.shape[:2]
    if h*w > 16_000_000:
        raise ValueError('Explicit 16MP input limit; no hidden image resize.')
    if not specs or len({s.name for s in specs}) != len(specs):
        raise ValueError('Region names must be unique and at least one region is required.')
    for spec in specs:
        _validate(spec,w,h)
    hsv = rgb_to_hsv(a[...,:3])
    visible = a[...,3] > 0 if a.shape[2] == 4 else np.ones((h,w), dtype=bool)
    labels = np.full((h,w), -1, dtype=np.int16)
    labels[~visible] = -3
    highest = np.full((h,w), -np.inf, dtype=np.float64)
    candidate_count = np.zeros((h,w), dtype=np.uint16)
    info = []
    for i,spec in enumerate(specs):
        candidate = np.zeros((h,w), dtype=bool)
        for hl,hh,sl,sh,vl,vh in spec.hsv_ranges:
            hue = ((hsv[...,0] >= hl) & (hsv[...,0] <= hh)) if hl <= hh else ((hsv[...,0] >= hl) | (hsv[...,0] <= hh))
            candidate |= hue & (hsv[...,1] >= sl) & (hsv[...,1] <= sh) & (hsv[...,2] >= vl) & (hsv[...,2] <= vh)
        if spec.boxes:
            domain = np.zeros((h,w), dtype=bool)
            for x0,y0,x1,y1 in spec.boxes:
                domain[y0:y1,x0:x1] = True
            candidate &= domain
        candidate &= visible
        mask,missed = _connected(candidate,spec.seeds)
        candidate_count += mask
        stronger = mask & (spec.priority > highest)
        equal = mask & (spec.priority == highest)
        labels[stronger] = i
        labels[equal] = -2
        highest[stronger] = spec.priority
        info.append({'spec':asdict(spec), 'candidate_pixels':int(mask.sum()), 'missed_seeds':missed,
                     'source_seed_rgb':[a[y,x,:3].tolist() for x,y in spec.seeds]})
    for i,item in enumerate(info):
        item['selected_pixels'] = int(np.sum(labels == i))
    metadata = {'algorithm':'explicit-region-ranges/0.1', 'source_shape':list(a.shape),
                'source_sha256_pixels':hashlib.sha256(a.tobytes()).hexdigest(), 'regions':info,
                'unassigned_pixels':int(np.sum(labels == -1)), 'conflict_pixels':int(np.sum(labels == -2)),
                'overlapping_candidates_pixels':int(np.sum(candidate_count > 1)),
                'label_values':{'unassigned':-1,'conflict':-2,'transparent':-3},
                'annotation_policy':'explicit source-specific color ranges, optional spatial boxes and seeds',
                'source_colors_modified':False, 'palette_applied':False, 'semantic_model_used':False,
                'review_status':'pending_user_review'}
    return labels, metadata


def extract_region(image, labels, index):
    """RGBA cutout with exact source RGB and original alpha on selected pixels."""
    out = np.zeros((*image.shape[:2],4), dtype=np.uint8)
    selected = labels == index
    out[selected,:3] = image[selected,:3]
    out[selected,3] = image[selected,3] if image.shape[2] == 4 else 255
    return out
