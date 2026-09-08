"""Independent, small CPU oracle for bounded observed-lightness quantization.

This file is validation scaffolding, not the Unity implementation. It uses
direct sums and interval representative enumeration instead of the shader's
prefix arithmetic, so it can detect discrepancies in that optimized math.
It never produces artwork, changes a source image, or calls Unity Editor APIs.
"""
from dataclasses import dataclass
from math import floor, isfinite, sqrt


@dataclass(frozen=True)
class Bin:
    """One occupied ordered histogram bin with an observed representative.

    The source moments can retain sub-bin lightness variation. `sample_index`
    identifies the actual source RGB represented by `representative_l`.
    """
    count: int
    sum_l: float
    sum_l2: float
    representative_l: float
    sample_index: int
    low_count: int = 0
    high_count: int = 0


@dataclass(frozen=True)
class Solution:
    status: str
    tone_count: int
    representatives: tuple
    assignments: tuple
    rmse: float | None
    support_contrast: float | None


@dataclass(frozen=True)
class HighlightSolution:
    status: str
    source_index: int | None
    changed_indices: tuple
    sse_reduction: float


def adaptive_histogram(lightness, *, bin_count=32, candidate_quantized=False):
    """Build the agreed GPU's adaptive histogram using integer source moments.

    GPU representative key: round(abs(u*32-(bin+.5))*1023) in the high bits,
    followed by the 22-bit source index. Fixtures avoid exact rounding half-ties;
    double CPU arithmetic is not a bit-for-bit substitute for HLSL float math.
    Returned Bin moments and representatives are in normalized [0,1] units.
    """
    values = tuple(float(value) for value in lightness)
    if not values:
        return 0., 0., (), ()
    if len(values) > 4_194_304:
        raise ValueError('source_index_22bit_limit_exceeded')
    if any(not isfinite(value) or not 0 <= value <= 1 for value in values):
        raise ValueError('source lightness must be finite in [0,1]')
    if not isinstance(bin_count, int) or isinstance(bin_count, bool) or not 1 <= bin_count <= 32:
        raise ValueError('bin_count must be an integer in [1,32]')
    minimum, maximum = min(values), max(values)
    span = maximum - minimum
    normalized = tuple((value - minimum) / span if span else 0. for value in values)
    per_bin = {}
    original_bins = []
    for index, value in enumerate(normalized):
        identifier = min(bin_count - 1, int(floor(value * bin_count)))
        quantized = int(floor(value * 65535 + .5))
        distance = int(floor(abs(value * bin_count - (identifier + .5)) * 1023 + .5))
        key = (distance << 22) | index
        per_bin.setdefault(identifier, []).append((quantized, key, index, value))
        original_bins.append(identifier)
    bins, compact = [], {}
    for identifier, samples in sorted(per_bin.items()):
        compact[identifier] = len(bins)
        selected = min(samples, key=lambda sample: sample[1])
        candidate = selected[0] / 65535 if candidate_quantized else selected[3]
        bins.append(Bin(len(samples), sum(sample[0] for sample in samples) / 65535,
                        sum(sample[0] ** 2 for sample in samples) / 65535 ** 2,
                        candidate, selected[2]))
    return minimum, span, tuple(bins), tuple(compact[index] for index in original_bins)


def chroma_cell_key(part, chroma, chroma_error=.06):
    """Collision-free logical key before the GPU's bounded hash table lookup.

    Subject identity is intentionally not invented here: a caller must use a
    separate dispatch/table per subject, or include subject in its owner key.
    """
    if isinstance(part, bool) or not isinstance(part, int) or not 0 <= part <= 4:
        raise ValueError('part must be an integer in [0,4]')
    if len(chroma) != 2 or any(not isfinite(value) for value in chroma):
        raise ValueError('chroma must contain two finite values')
    if not isfinite(chroma_error) or chroma_error <= 0:
        raise ValueError('chroma_error must be finite and positive')
    width = chroma_error / sqrt(2.)
    return part, floor(chroma[0] / width + .5), floor(chroma[1] / width + .5)


def supported_highlight(source_l, frozen_l, high_support, *, minimum_contrast=.025):
    """Exhaustive small-case oracle for an observed positive frozen-top accent.

    Returned positions are original source positions. Their coordinates, depth,
    alpha and group keys must be copied unchanged by a caller/renderer; this
    mathematical helper intentionally has no mechanism for relocating them.
    """
    source_l, frozen_l, high_support = tuple(source_l), tuple(frozen_l), tuple(high_support)
    if not (len(source_l) == len(frozen_l) == len(high_support)):
        raise ValueError('source, frozen palette and support must have the same sample count')
    if not isfinite(minimum_contrast) or minimum_contrast <= 0:
        raise ValueError('minimum_contrast must be finite and positive')
    if not source_l:
        return HighlightSolution('no_supported_positive_accent', None, (), 0.)
    if any(not isfinite(value) or not 0 <= value <= 1 for value in source_l + frozen_l):
        raise ValueError('lightness must be finite in [0,1]')
    top = max(frozen_l)
    eligible = tuple(index for index in range(len(source_l))
                     if high_support[index] and frozen_l[index] == top)
    best = HighlightSolution('no_supported_positive_accent', None, (), 0.)
    for cutoff in sorted(set(source_l[index] for index in eligible)):
        changed = tuple(index for index in eligible if source_l[index] >= cutoff)
        for candidate, level in enumerate(source_l):
            if level < top + minimum_contrast or any(source_l[index] < (top + level) * .5 for index in changed):
                continue
            gain = sum((source_l[index] - top) ** 2 - (source_l[index] - level) ** 2 for index in changed)
            if gain > best.sse_reduction + 1e-12:
                best = HighlightSolution('ok', candidate, changed, gain)
    return best


def observed_bins(lightness, sample_indices=None):
    """Create exact observed-L bins for small oracle and synthetic cases."""
    values = tuple(float(value) for value in lightness)
    if sample_indices is None:
        sample_indices = tuple(range(len(values)))
    if len(sample_indices) != len(values):
        raise ValueError('one source index is required per lightness')
    grouped = {}
    for value, index in zip(values, sample_indices):
        if not isfinite(value) or not 0 <= value <= 1:
            raise ValueError('source lightness must be finite in [0,1]')
        grouped.setdefault(value, []).append(index)
    return tuple(Bin(len(indices), value * len(indices), value * value * len(indices),
                     value, min(indices)) for value, indices in sorted(grouped.items()))


def solve_observed_bins(bins, *, tone_error=.06, max_tones=32,
                        max_bins=32, minimum_support_contrast=None):
    """First SSE-optimal contiguous K candidate passing RMSE and support guards.

    This is NOT the global minimum K under an arbitrary spatial constraint:
    only the unconstrained SSE-optimal partition for each K is considered.
    A resource cap returns a visible failure status, never a successful forced
    palette. The caller decides how to present failure without changing data.
    """
    bins = tuple(bins)
    if not isfinite(tone_error) or tone_error <= 0:
        raise ValueError('tone_error must be finite and positive')
    if isinstance(max_tones, bool) or not isinstance(max_tones, int) or max_tones < 1:
        raise ValueError('max_tones must be a positive integer')
    if isinstance(max_bins, bool) or not isinstance(max_bins, int) or max_bins < 1:
        raise ValueError('max_bins must be a positive integer')
    if minimum_support_contrast is not None and (
            not isfinite(minimum_support_contrast) or minimum_support_contrast < 0):
        raise ValueError('minimum_support_contrast must be finite and nonnegative')
    if not bins:
        return Solution('empty', 0, (), (), 0., None)
    if len(bins) > max_bins:
        return Solution('bin_limit_exceeded', 0, (), (), None, None)
    for index, item in enumerate(bins):
        if (item.count < 1 or not all(isfinite(value) for value in (
                item.sum_l, item.sum_l2, item.representative_l))
                or not 0 <= item.representative_l <= 1
                or not 0 <= item.low_count <= item.count
                or not 0 <= item.high_count <= item.count):
            raise ValueError('invalid occupied-bin source moments or support counts')
        if index and bins[index - 1].representative_l > item.representative_l:
            raise ValueError('bins must be ordered by representative lightness')
    count = len(bins)
    population = sum(item.count for item in bins)
    low_count, high_count = sum(item.low_count for item in bins), sum(item.high_count for item in bins)
    if minimum_support_contrast is not None and (not low_count or not high_count):
        raise ValueError('contrast guard needs nonempty low and high support counts')
    interval_cost, interval_rep = {}, {}
    for start in range(count):
        for end in range(start + 1, count + 1):
            scores = []
            for representative in range(start, end):
                level = bins[representative].representative_l
                error = sum(item.sum_l2 - 2 * level * item.sum_l + level * level * item.count
                            for item in bins[start:end])
                scores.append((max(error, 0.), representative))
            interval_cost[start, end], interval_rep[start, end] = min(scores)
    previous = {0: (0., ())}
    for tones in range(1, min(max_tones, count) + 1):
        current = {}
        for end in range(tones, count + 1):
            candidates = []
            for start in range(tones - 1, end):
                if start in previous:
                    error, intervals = previous[start]
                    candidates.append((error + interval_cost[start, end], start,
                                       intervals + ((start, end),)))
            error, _, intervals = min(candidates, key=lambda entry: (entry[0], entry[1]))
            current[end] = error, intervals
        error, intervals = current[count]
        assignments = [0] * count
        representatives = []
        for tone, (start, end) in enumerate(intervals):
            representative = interval_rep[start, end]
            representatives.append(representative)
            assignments[start:end] = [tone] * (end - start)
        target_l = [bins[representatives[tone]].representative_l for tone in assignments]
        rmse = sqrt(max(error, 0.) / population)
        contrast = None
        if low_count and high_count:
            contrast = (sum(item.high_count * level for item, level in zip(bins, target_l)) / high_count
                        - sum(item.low_count * level for item, level in zip(bins, target_l)) / low_count)
        if rmse <= tone_error + 1e-12 and (minimum_support_contrast is None
                or contrast + 1e-12 >= minimum_support_contrast):
            return Solution('ok', tones, tuple(representatives), tuple(assignments), rmse, contrast)
        previous = current
    return Solution('no_feasible_candidate_within_tone_limit', 0, (), (), None, None)
