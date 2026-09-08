"""Read-only GPU trace analysis; writes new reports, never changes captures.

Usage: python -B analyze_trace.py CAPTURE_ROOT --out NEW_REPORT_DIRECTORY
GPU buffers are authoritative observations. CPU calculations reconstruct the
current compute equations from captured integer moments and observed candidates;
even the float32 reconstruction is NOT a bit-exact FXC/FMA/pow emulator.
Adjacent controlled samples are not automatically successive gameplay frames.
"""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


GROUPS, BINS, TILES, Q = 160, 32, 16, 65535
LAYOUTS = {
    "groups": ("<u4", (GROUPS, 8)),
    "histogram": ("<u4", (GROUPS, BINS, 6)),
    "tiles": ("<u4", (GROUPS, TILES, 3)),
    "tileHistogram": ("<u4", (GROUPS, TILES, BINS)),
    "supports": ("<u4", (GROUPS, 2)),
    "highlightHistogram": ("<u4", (GROUPS, BINS, 5)),
    "status": ("<u4", (GROUPS + 1,)),
    "palette": ("<f4", (GROUPS, BINS, 4)),
    "solutions": ("<f4", (GROUPS, 3, 4)),
}
DEFAULTS = dict(toneError=.06, chromaError=.06, contrastRetention=.65,
                minimumContrast=.025, highlightMinimumContrast=.025,
                hairLighting=False, hairRelativeError=.10, hairIlluminationFloor=.02,
                skinLighting=False, skinRelativeError=.10, skinIlluminationFloor=.02)
GLOBAL_BITS = {1: "hash_capacity", 2: "dimensions", 4: "RGB_or_depth",
               8: "part_or_chroma_range", 16: "settings", 32: "sparse_native_mismatch",
               64: "native_illumination"}
PART_NAMES = {3: "Hair", 4: "Skin"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_array(path, dtype, shape):
    path, dtype = Path(path), np.dtype(dtype)
    expected = math.prod(shape) * dtype.itemsize
    actual = path.stat().st_size
    if actual != expected:
        raise ValueError(f"{path.name}: expected {expected} bytes, got {actual}")
    return np.fromfile(path, dtype=dtype).reshape(shape)


def find_sample(folder, search_root=None):
    folder = Path(folder).resolve()
    limit = Path(search_root).resolve() if search_root else folder.parent
    for candidate in (folder, *folder.parents):
        path = candidate / "sample.json"
        if path.is_file():
            return read_json(path), str(path)
        if candidate == limit:
            break
    return {}, None


def load_capture(folder, search_root=None):
    folder = Path(folder).resolve()
    meta = read_json(folder / "capture.json")
    if meta.get("error"):
        raise ValueError(f"capture harness reported: {meta['error']}")
    width, height, subject = (meta.get(k) for k in ("width", "height", "subjectId"))
    if any(type(v) is not int for v in (width, height, subject)):
        raise ValueError("width, height and subjectId must be integers")
    if min(width, height) <= 0 or width * height > 4194304 or not 1 <= subject <= 65535:
        raise ValueError("dimensions or subjectId outside the compute contract")
    settings = meta.get("settingsJson", meta.get("settings", {}))
    if isinstance(settings, str):
        settings = json.loads(settings)
    if not isinstance(settings, dict):
        raise ValueError("settingsJson must decode to an object")
    missing = sorted(set(DEFAULTS) - settings.keys())
    settings = {**DEFAULTS, **settings}
    for name in DEFAULTS:
        value = settings[name]
        if name in ("hairLighting", "skinLighting"):
            if not isinstance(value, bool):
                raise ValueError(f"{name} must be boolean")
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"invalid setting {name}")
    arrays = {name: read_array(folder / (name + ".bin"), dtype, shape)
              for name, (dtype, shape) in LAYOUTS.items()}
    for name in ("nativeColor", "cellColor", "output", "nativeLighting", "nativeMeta", "cellMeta"):
        dtype = "u1" if name.endswith("Meta") else "<f2"
        arrays[name] = read_array(folder / (name + ".bin"), dtype, (height, width, 4))
    sample, sample_path = find_sample(folder, search_root)
    return dict(folder=str(folder), metadata=meta, settings=settings,
                settings_defaulted=missing, sample=sample,
                sample_path=str(sample_path) if sample_path else None, arrays=arrays)


def pair_values(values, offset, precision="float64"):
    """Decode low/high words. float32 mirrors PairValue's conversion order."""
    values = np.asarray(values)
    if precision == "float32":
        return (values[..., offset + 1].astype(np.float32) * np.float32(4294967296)
                + values[..., offset].astype(np.float32))
    exact = (values[..., offset].astype(np.uint64)
             | (values[..., offset + 1].astype(np.uint64) << np.uint64(32)))
    return exact.astype(np.float64)


def moments(histogram, precision="float64"):
    f = np.float32 if precision == "float32" else np.float64
    return (histogram[..., 0].astype(f), pair_values(histogram, 1, precision) / f(Q),
            pair_values(histogram, 3, precision) / f(f(Q) * f(Q)))


def sequential_sum(values, f):
    result = f(0)
    for value in values:
        result = f(result + f(value))
    return result


def oklab(rgb):
    rgb = np.asarray(rgb, dtype=np.float32)
    first = np.array([[.4122214708, .5363325363, .0514459929],
                      [.2119034982, .6806995451, .1073969566],
                      [.0883024619, .2817188376, .6299787005]], dtype=np.float32)
    second = np.array([[.2104542553, .7936177850, -.0040720468],
                       [1.9779984951, -2.4285922050, .4505937099],
                       [.0259040371, .7827717662, -.8086757660]], dtype=np.float32)
    lms = np.power(np.maximum(rgb @ first.T, 0), np.float32(1 / 3))
    return lms @ second.T


def subject_ids(meta):
    return meta[..., 0].astype(np.uint32) | (meta[..., 3].astype(np.uint32) << 8)


def color_keys(color, meta, chroma_error):
    """CPU reconstruction only: pixels at grid boundaries may differ from GPU."""
    rgb = np.asarray(color[..., :3], dtype=np.float32)
    valid = np.all(np.isfinite(rgb) & (rgb >= 0) & (rgb <= 16), axis=-1)
    lab = oklab(np.where(valid[..., None], rgb, 0))
    chroma = lab[..., 1:] / np.maximum(lab[..., :1], np.float32(.05))
    cell = np.floor(chroma / np.float32(chroma_error * .7071067811865475) + np.float32(.5)).astype(np.int32)
    part = meta[..., 1].astype(np.uint32)
    valid &= (part <= 4) & np.all((cell >= -128) & (cell <= 127), axis=-1)
    key = ((part + 1) << 16) | ((cell[..., 0] + 128).astype(np.uint32) << 8) | (cell[..., 1] + 128).astype(np.uint32)
    return np.where(valid, key, 0).astype(np.uint32)


def tile_masks(means, counts, f):
    occupied = np.flatnonzero(counts > 0)
    if len(occupied) < 2:
        return 0, 0
    ordered = sorted(f(means[i]) for i in occupied)
    thresholds = []
    for quantile in (.2, .8):
        position = f(f(len(ordered) - 1) * f(quantile))
        lo, hi = math.floor(position), math.ceil(position)
        fraction = f(position - f(lo))
        thresholds.append(f(ordered[lo] + f(f(ordered[hi] - ordered[lo]) * fraction)))
    low, high = thresholds
    if f(high - low) <= f(1e-8):
        return 0, 0
    return (sum(1 << int(i) for i in occupied if means[i] <= low),
            sum(1 << int(i) for i in occupied if means[i] >= high))


def lighting_prefix(settings, part):
    """Independent opt-ins: legacy captures without Skin settings remain L."""
    if part == 3 and settings.get("hairLighting", False):
        return "hair"
    if part == 4 and settings.get("skinLighting", False):
        return "skin"
    return None


def reconstruct_guard(histogram, tiles, minimum, span, settings, hair, precision="float64", *, skin=False):
    f = np.float32 if precision == "float32" else np.float64
    counts, sums, squares = moments(histogram, precision)
    count, total, square = (sequential_sum(v, f) for v in (counts, sums, squares))
    report = dict(precision=precision, guard=False, reason="empty_histogram", count=int(count),
                  low_mask=0, high_mask=0, required_contrast=0., source_contrast=None,
                  fine_coherence=None, coarse_coherence=None, low_overlap=None, high_overlap=None)
    if count <= 0:
        return report
    mean = f(total / count)
    variance = f(max(f(f(square / count) - f(mean * mean)), f(0)))
    metric_mean = f(f(minimum) + f(f(span) * mean))
    if hair and skin:
        raise ValueError("one group cannot simultaneously be Hair and Skin")
    prefix = "hair" if hair else ("skin" if skin else None)
    scale = f(max(metric_mean, f(settings[prefix + "IlluminationFloor"]))) if prefix else f(1)
    contrast_limit = f(f(settings["minimumContrast"]) * scale)
    report.update(normalized_mean=float(mean), normalized_variance=float(variance),
                  metric_mean=float(metric_mean), metric_scale=float(scale),
                  error_limit=float(f(scale * f(settings[prefix + "RelativeError"])) if prefix else f(settings["toneError"])),
                  minimum_contrast=float(contrast_limit),
                  highlight_minimum_contrast=float(f(f(settings["highlightMinimumContrast"]) * scale)))
    if variance <= f(1e-12):
        report["reason"] = "variance_at_or_below_1e-12"
        return report
    if f(span) < contrast_limit:
        report["reason"] = "range_below_minimum_contrast"
        return report
    tc = tiles[:, 0].astype(f)
    ts = pair_values(tiles, 1, precision) / f(Q)
    tm = np.divide(ts, tc, out=np.zeros(TILES, dtype=f), where=tc > 0)
    cc, cs = np.zeros(4, dtype=f), np.zeros(4, dtype=f)
    fine_variance = f(0)
    parents = [(t // 8) * 2 + (t % 4) // 2 for t in range(TILES)]
    for t, parent in enumerate(parents):
        difference = f(tm[t] - mean)
        fine_variance = f(fine_variance + f(f(tc[t] * difference) * difference))
        cc[parent] = f(cc[parent] + tc[t])
        cs[parent] = f(cs[parent] + ts[t])
    cm = np.divide(cs, cc, out=np.zeros(4, dtype=f), where=cc > 0)
    coarse_variance = f(0)
    for c in range(4):
        difference = f(cm[c] - mean)
        coarse_variance = f(coarse_variance + f(f(cc[c] * difference) * difference))
    fine = f(fine_variance / f(count * variance))
    coarse = f(coarse_variance / f(count * variance))
    report.update(fine_coherence=float(fine), coarse_coherence=float(coarse))
    if fine < f(.35) or coarse < f(.35):
        report["reason"] = "fine_coherence_below_.35" if fine < f(.35) else "coarse_coherence_below_.35"
        return report
    fl, fh = tile_masks(tm, tc, f)
    cl, ch = tile_masks(cm, cc, f)
    if not all((fl, fh, cl, ch)):
        report["reason"] = "empty_quantile_support"
        return report
    low_mask = sum(1 << t for t, p in enumerate(parents) if cl & (1 << p))
    high_mask = sum(1 << t for t, p in enumerate(parents) if ch & (1 << p))
    def masked(values, mask):
        return sequential_sum((v for t, v in enumerate(values) if mask & (1 << t)), f)
    lc, hc, flc, fhc = (masked(tc, mask) for mask in (low_mask, high_mask, fl, fh))
    if min(lc, hc, flc, fhc) <= 0:
        report["reason"] = "empty_support_population"
        return report
    lo = f(masked(tc, low_mask & fl) / min(lc, flc))
    ho = f(masked(tc, high_mask & fh) / min(hc, fhc))
    report.update(low_overlap=float(lo), high_overlap=float(ho))
    if lo < f(.65) or ho < f(.65):
        report["reason"] = "low_overlap_below_.65" if lo < f(.65) else "high_overlap_below_.65"
        return report
    contrast = f(f(span) * f(f(masked(ts, high_mask) / hc) - f(masked(ts, low_mask) / lc)))
    report["source_contrast"] = float(contrast)
    if contrast < contrast_limit:
        report["reason"] = "support_contrast_below_minimum"
        return report
    report.update(guard=True, reason="passed", low_mask=low_mask, high_mask=high_mask,
                  required_contrast=float(f(contrast * f(settings["contrastRetention"])) ))
    return report


def reconstruct_k1(histogram, candidate_metrics, minimum, span, precision="float64"):
    f = np.float32 if precision == "float32" else np.float64
    counts, sums, squares = moments(histogram, precision)
    active = np.flatnonzero(counts > 0)
    if not len(active):
        return None
    count, total, square = (sequential_sum(v[active], f) for v in (counts, sums, squares))
    mean = f(total / count)
    normalized = np.clip((np.asarray(candidate_metrics, dtype=f) - f(minimum)) / f(span), 0, 1) if span > 1e-8 else np.zeros(BINS, dtype=f)
    # np.argmin keeps the first ascending bin on an exact distance tie, as HLSL < does.
    chosen = int(active[np.argmin(np.abs(normalized[active] - mean))])
    r = f(normalized[chosen])
    sse = f(max(f(f(square - f(f(f(2) * r) * total)) + f(f(r * r) * count)), f(0)))
    rmse = f(f(span) * f(np.sqrt(f(sse / count))))
    return dict(representative_bin=chosen, representative_metric=float(candidate_metrics[chosen]),
                rmse=float(rmse), normalized_sse=float(sse))


def valid_color(color):
    return (np.all(np.isfinite(color), axis=-1) & (color[..., 3] > 0)
            & np.all((color[..., :3] >= 0) & (color[..., :3] <= 16), axis=-1))


def color_count(color, mask):
    return int(len(np.unique(color[..., :3][mask], axis=0))) if np.any(mask) else 0


def scalar_stats(values):
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    return dict(count=int(values.size), mean=float(values.mean()) if values.size else None,
                minimum=float(values.min()) if values.size else None, maximum=float(values.max()) if values.size else None)


def analyze_capture(capture):
    a, meta, settings = capture["arrays"], capture["metadata"], capture["settings"]
    subject = meta["subjectId"]
    source_mask = subject_ids(a["nativeMeta"]) == subject
    seed_subject = subject_ids(a["cellMeta"]) == subject
    source_valid = source_mask & valid_color(a["nativeColor"])
    seeds = seed_subject & (a["cellColor"][..., 3] > 0)
    outputs = seed_subject & (a["output"][..., 3] > 0)
    changed = np.any(a["cellColor"].view(np.uint16) != a["output"].view(np.uint16), axis=-1)
    lighting = a["nativeLighting"].astype(np.float32)
    e_valid = np.all(np.isfinite(lighting), axis=-1) & (lighting[..., 0] >= 0) & (lighting[..., 3] == 1)
    source_keys = color_keys(a["nativeColor"], a["nativeMeta"], settings["chromaError"])
    seed_keys = color_keys(a["cellColor"], a["cellMeta"], settings["chromaError"])
    global_status = int(a["status"][GROUPS])
    report = {k: capture[k] for k in ("folder", "metadata", "settings", "settings_defaulted", "sample", "sample_path")}
    report.update(global_status=global_status,
                  global_errors=[name for bit, name in GLOBAL_BITS.items() if global_status & bit],
                  unknown_global_bits=global_status & ~127,
                  coverage=dict(source_subject_pixels=int(source_mask.sum()), source_valid_pixels=int(source_valid.sum()),
                                seed_pixels=int(seeds.sum()), output_pixels=int(outputs.sum()),
                                invalid_seed_pixels=int((seeds & ~valid_color(a["cellColor"])).sum()),
                                invalid_output_pixels=int((outputs & ~valid_color(a["output"])).sum()),
                                source_colors=color_count(a["nativeColor"], source_valid), seed_colors=color_count(a["cellColor"], seeds),
                                output_colors=color_count(a["output"], outputs), changed_seed_pixels=int((changed & seeds).sum()),
                                changed_outside_target_seeds=int((changed & ~seeds).sum()),
                                depth_bit_changes=int(np.count_nonzero(a["cellColor"][..., 3].view(np.uint16) != a["output"][..., 3].view(np.uint16))),
                                lighting_valid_source_pixels=int((e_valid & source_valid).sum())), groups=[], warnings=[])
    native_flat = a["nativeColor"].reshape(-1, 4)
    lighting_flat = lighting.reshape(-1, 4)
    for slot in np.flatnonzero(a["groups"][:, 0]):
        group = a["groups"][slot]
        key, part = int(group[0]), int(group[0] >> 16) - 1
        hist = a["histogram"][slot]
        active = hist[:, 0] > 0
        minimum, maximum = (float(v) for v in group[6:8].view("<f4"))
        span = float(np.float32(maximum) - np.float32(minimum))
        if not np.isfinite([minimum, maximum, span]).all() or span < 0:
            raise ValueError(f"group {key}: invalid metric bounds")
        prefix = lighting_prefix(settings, part)
        hair, skin = prefix == "hair", prefix == "skin"
        candidate_metric = np.zeros(BINS, dtype=np.float32)
        candidate_indices = (hist[:, 5] & 4194303).astype(np.int64)
        if np.any(candidate_indices[active] >= len(native_flat)):
            raise ValueError(f"group {key}: observed candidate index outside source")
        candidate_rgb = native_flat[candidate_indices[active], :3].astype(np.float32)
        candidate_metric[active] = lighting_flat[candidate_indices[active], 0] if prefix else oklab(candidate_rgb)[:, 0]
        cpu = {}
        for precision in ("float64", "float32"):
            guard = reconstruct_guard(hist, a["tiles"][slot], minimum, span, settings, hair, precision, skin=skin)
            k1 = reconstruct_k1(hist, candidate_metric, minimum, span, precision)
            if k1 is not None:
                k1["within_error_limit"] = k1["rmse"] <= guard["error_limit"] + 1e-6
                k1["eligible_without_positive_guard"] = k1["within_error_limit"] and not guard["guard"]
            cpu[precision] = dict(guard=guard, k1=k1)
        sol = a["solutions"][slot].astype(np.float64)
        status = int(a["status"][slot])
        gpu_palette = a["palette"][slot][active & (a["palette"][slot, :, 3] >= 0)]
        palette = np.unique(gpu_palette, axis=0)
        if len(palette):
            palette = palette[np.argsort(palette[:, 3], kind="stable")]
        sm = source_valid & (source_keys == key)
        cm = seeds & (seed_keys == key)
        om = outputs & (seed_keys == key)
        observed_count = int(hist[:, 0].astype(np.uint64).sum())
        group_report = dict(subject_id=subject, key=key, identity=f"{subject}:{key}", slot=int(slot),
                            part=part, part_name=PART_NAMES.get(part, str(part)), metric="illumination_Y" if prefix else "Oklab_L",
                            count=int(group[1]), histogram_count=observed_count, occupied_bins=int(active.sum()),
                            minimum=minimum, maximum=maximum, range=span, bbox=group[2:6].astype(int).tolist(),
                            gpu=dict(status=status, ready=bool(status & 1), guard=bool(status & 2),
                                     errors=[name for bit, name in ((4, "RMS_failed"), (8, "contrast_failed")) if status & bit],
                                     K=float(sol[0, 0]), rmse=float(sol[0, 1]), required_contrast=float(sol[0, 2]),
                                     retained_contrast=float(sol[0, 3]), low_mask=int(a["supports"][slot, 0]), high_mask=int(a["supports"][slot, 1]),
                                     highlight=bool(sol[1, 3] > .5), highest_base=float(sol[1, 0]), accent_metric=float(sol[1, 1]),
                                     accent_cutoff=float(sol[1, 2]), accent_rgb=sol[2, :3].tolist(), accent_gain=float(sol[2, 3]),
                                     highlight_support_count=int(a["highlightHistogram"][slot, :, 0].astype(np.uint64).sum()),
                                     palette=palette.astype(float).tolist()), cpu_reconstructed=cpu,
                            cpu_source_group_count=int(sm.sum()), cpu_seed_group_count=int(cm.sum()),
                            source_colors=color_count(a["nativeColor"], sm), seed_colors=color_count(a["cellColor"], cm),
                            output_colors=color_count(a["output"], om), E=scalar_stats(lighting[..., 0][sm & e_valid]),
                            warnings=[])
        if observed_count != int(group[1]):
            group_report["warnings"].append("group_histogram_population_mismatch")
        if int(sm.sum()) != int(group[1]):
            group_report["warnings"].append("CPU_chroma_key_population_differs_from_GPU")
        if int(a["tiles"][slot, :, 0].astype(np.uint64).sum()) != observed_count or int(a["tileHistogram"][slot].astype(np.uint64).sum()) != observed_count:
            group_report["warnings"].append("spatial_histogram_population_mismatch")
        if cpu["float64"]["guard"]["guard"] != bool(status & 2):
            group_report["warnings"].append("CPU64_guard_differs_from_GPU")
        if cpu["float32"]["guard"]["guard"] != bool(status & 2):
            group_report["warnings"].append("CPU32_guard_differs_from_GPU")
        for precision in ("float64", "float32"):
            guard = cpu[precision]["guard"]
            if guard["guard"] and bool(status & 2) and (
                    guard["low_mask"] != int(a["supports"][slot, 0]) or
                    guard["high_mask"] != int(a["supports"][slot, 1])):
                group_report["warnings"].append(f"CPU_{precision}_support_masks_differ_from_GPU")
        report["groups"].append(group_report)
    report["groups"].sort(key=lambda g: g["key"])
    report["group_counts"] = dict(active=len(report["groups"]), ready=sum(g["gpu"]["ready"] for g in report["groups"]),
                                  guarded=sum(g["gpu"]["guard"] for g in report["groups"]),
                                  K1=sum(g["gpu"]["ready"] and g["gpu"]["K"] == 1 for g in report["groups"]),
                                  highlight=sum(g["gpu"]["highlight"] for g in report["groups"]))
    report["parts"] = []
    for part in range(5):
        sm = source_valid & (a["nativeMeta"][..., 1] == part)
        cm = seeds & (a["cellMeta"][..., 1] == part)
        om = outputs & (a["cellMeta"][..., 1] == part)
        groups = [g for g in report["groups"] if g["part"] == part]
        if np.any(sm) or np.any(cm) or groups:
            report["parts"].append(dict(part=part, part_name=PART_NAMES.get(part, str(part)),
                source_pixels=int(sm.sum()), seed_pixels=int(cm.sum()), output_pixels=int(om.sum()),
                source_colors=color_count(a["nativeColor"], sm), seed_colors=color_count(a["cellColor"], cm),
                output_colors=color_count(a["output"], om), E=scalar_stats(lighting[..., 0][sm & e_valid]),
                groups=len(groups), guarded_groups=sum(g["gpu"]["guard"] for g in groups),
                K1_groups=sum(g["gpu"]["ready"] and g["gpu"]["K"] == 1 for g in groups),
                K1_source_population=sum(g["count"] for g in groups if g["gpu"]["ready"] and g["gpu"]["K"] == 1),
                highlight_groups=sum(g["gpu"]["highlight"] for g in groups)))
    if sum(g["count"] for g in report["groups"]) != int(source_valid.sum()):
        report["warnings"].append("GPU_group_population_differs_from_valid_source_coverage")
    return report


def palette_distance(left, right):
    if not left or not right:
        return None, None
    a, b = np.asarray(left), np.asarray(right)
    metric = np.abs(a[:, None, 3] - b[None, :, 3])
    rgb = np.linalg.norm(a[:, None, :3] - b[None, :, :3], axis=-1)
    return (float(max(metric.min(axis=0).max(), metric.min(axis=1).max())),
            float(max(rgb.min(axis=0).max(), rgb.min(axis=1).max())))


def adjacent_jumps(captures):
    """Compare actual keys, never hash slots. Keep changed-condition labels."""
    results = []
    series = {}
    for capture in captures:
        meta, sample = capture["metadata"], capture["sample"]
        context = {k: meta.get(k, sample.get(k)) for k in
                   ("subjectId", "width", "height", "cameraId", "cameraInstanceId", "sessionId", "batchId", "sequenceId")}
        context["mode"] = sample.get("mode")
        # A named experiment phase separates sequences; numeric animation phase
        # is the independent variable and must remain comparable within a series.
        context["named_phase"] = sample.get("phase") if isinstance(sample.get("phase"), str) else None
        series.setdefault(json.dumps(context, sort_keys=True), []).append(capture)
    pairs = [(a, b) for sequence in series.values() for a, b in zip(sequence, sequence[1:])]
    for previous, current in pairs:
        left = {g["identity"]: g for g in previous["groups"]}
        right = {g["identity"]: g for g in current["groups"]}
        changed_conditions = [name for name in ("scale", "mode", "phase")
                              if previous["sample"].get(name) != current["sample"].get(name)]
        if previous["settings"] != current["settings"]:
            changed_conditions.append("settings")
        if any(previous["metadata"].get(k) != current["metadata"].get(k) for k in ("width", "height", "subjectId")):
            changed_conditions.append("dimensions_or_subject")
        for identity in sorted(left.keys() | right.keys()):
            a, b = left.get(identity), right.get(identity)
            row = dict(previous_capture=previous["metadata"].get("captureId"), current_capture=current["metadata"].get("captureId"),
                       previous_frame=previous["metadata"].get("frame"), current_frame=current["metadata"].get("frame"),
                       identity=identity, changed_conditions=changed_conditions, reasons=[])
            if a is None or b is None:
                row["reasons"] = ["group_appeared" if a is None else "group_disappeared"]
            else:
                comparable = a["metric"] == b["metric"]
                for field, label in (("K", "K_changed"), ("guard", "guard_changed"), ("highlight", "highlight_changed"), ("status", "status_changed")):
                    if a["gpu"][field] != b["gpu"][field]:
                        row["reasons"].append(label)
                if comparable and a["gpu"]["K"] > 1 and b["gpu"]["K"] == 1:
                    row["reasons"].append("collapsed_to_K1")
                metric_delta, rgb_delta = palette_distance(a["gpu"]["palette"], b["gpu"]["palette"])
                limit = max(a["cpu_reconstructed"]["float64"]["guard"].get("error_limit", 0),
                            b["cpu_reconstructed"]["float64"]["guard"].get("error_limit", 0))
                range_delta = b["range"] - a["range"] if comparable else None
                if comparable and abs(range_delta) > limit:
                    row["reasons"].append("range_change_exceeds_error_limit")
                if comparable and metric_delta is not None and metric_delta > limit:
                    row["reasons"].append("palette_metric_change_exceeds_error_limit")
                if not comparable:
                    row["reasons"].append("metric_changed_not_comparable")
                    metric_delta, limit = None, None
                row.update(part=b["part"], metric=b["metric"], K_before=a["gpu"]["K"], K_after=b["gpu"]["K"],
                           metric_comparable=comparable, gpu_guard_before=a["gpu"]["guard"], gpu_guard_after=b["gpu"]["guard"],
                           count_delta=b["count"] - a["count"], range_delta=range_delta,
                           palette_metric_hausdorff=metric_delta, palette_RGB_hausdorff=rgb_delta,
                           error_limit_reference=limit, cpu_guard_reason_before=a["cpu_reconstructed"]["float64"]["guard"]["reason"],
                           cpu_guard_reason_after=b["cpu_reconstructed"]["float64"]["guard"]["reason"])
            if row["reasons"]:
                results.append(row)
    return results


def csv_rows(captures):
    rows = []
    for capture in captures:
        for group in capture["groups"]:
            row = dict(capture_id=capture["metadata"].get("captureId"), frame=capture["metadata"].get("frame"),
                       sample_index=capture["sample"].get("index"), phase=capture["sample"].get("phase"),
                       scale=capture["sample"].get("scale"), mode=capture["sample"].get("mode"), global_status=capture["global_status"])
            row.update({k: group[k] for k in ("identity", "slot", "part", "metric", "count", "histogram_count", "occupied_bins", "minimum", "maximum", "range", "source_colors", "seed_colors", "output_colors")})
            row.update({"gpu_" + k: v for k, v in group["gpu"].items() if k != "palette"})
            row["E_mean"] = group["E"]["mean"]
            row["E_count"] = group["E"]["count"]
            row["warnings"] = group["warnings"]
            for precision, value in group["cpu_reconstructed"].items():
                row.update({"cpu_" + precision + "_" + k: v for k, v in value["guard"].items()})
                row.update({"cpu_" + precision + "_K1_" + k: v for k, v in (value["k1"] or {}).items()})
            rows.append(row)
    return rows


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row)) or ["no_rows"]
    with Path(path).open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_root", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mode", help="Analyze only this sample.json mode (e.g. sweep or walk).")
    args = parser.parse_args(argv)
    root, output = args.capture_root.resolve(), args.out.resolve()
    paths = sorted(root.rglob("capture.json")) if not (root / "capture.json").exists() else [root / "capture.json"]
    if not paths:
        parser.error("no capture.json found")
    targets = [output / name for name in ("summary.json", "groups.csv", "adjacent_jumps.csv")]
    if any(p.exists() for p in targets):
        parser.error("report files already exist; use a new output directory")
    reports, errors = [], []
    for path in paths:
        try:
            if args.mode and find_sample(path.parent, root)[0].get("mode") != args.mode:
                continue
            report = analyze_capture(load_capture(path.parent, root))
            json.dumps(report, allow_nan=False)
            reports.append(report)
        except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
            errors.append(dict(folder=str(path.parent), error=str(error)))
    def sample_order(report):
        index = report["sample"].get("index")
        if not isinstance(index, (int, float)) or not math.isfinite(index):
            index = report["metadata"].get("frame", 0)
        if not isinstance(index, (int, float)) or not math.isfinite(index):
            index = 0
        return index, str(report["metadata"].get("captureId", "")), report["folder"]
    reports.sort(key=sample_order)
    jumps = adjacent_jumps(reports)
    summary = dict(schema_version=1, source_root=str(root), mode_filter=args.mode, capture_count=len(reports), capture_errors=errors,
                   interpretation="Numerical observations and candidate transitions only; no art-quality judgment or confirmed temporal cause.",
                   CPU_contract="float64 decodes integer moments; float32 reconstructs scalar operations. Neither emulates FXC FMA/pow exactly. GPU recorded buffers remain authoritative.",
                   membership_caveat="CPU RGB-to-chroma group membership can differ at grid boundaries; GPU group count and subject:key are authoritative, not hash slot.",
                   color_count_contract="Exact distinct stored linear float16 RGB triples, not display/sRGB perceptual color counts. Output counts use seed metadata.",
                   adjacency_contract="Neighboring sample indices (else frame) within subject/dimensions/camera/session/batch/sequence/mode/named-phase, when supplied. Numeric animation phase and illumination scale may change. These may be controlled poses in one Unity frame, not continuous gameplay; changed settings are labeled and different metrics are not numerically compared.",
                   jump_threshold_contract="Discrete K/guard/highlight/status changes or range/palette metric Hausdorff changes greater than the larger reconstructed error limit; candidate flags, not defects.",
                   captures=reports, adjacent_jump_candidates=jumps)
    output.mkdir(parents=True, exist_ok=True)
    # Validate JSON serializability/finite values before creating any report file.
    encoded = json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)
    with targets[0].open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    write_csv(targets[1], csv_rows(reports))
    write_csv(targets[2], jumps)
    print(json.dumps(dict(report=str(targets[0]), captures=len(reports), capture_errors=len(errors), jump_candidates=len(jumps))))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
