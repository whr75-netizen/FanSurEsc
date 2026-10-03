"""Source-resolution, bounded colour cleanup; never estimates or resizes a grid."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from PIL import Image


def rgb_lab(rgb):
    """8-bit sRGB -> CIELAB with D65 reference white, for Delta E 76 only."""
    c = np.asarray(rgb, dtype=np.float32) / 255.0
    linear = np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
    matrix = np.array([[.4124564, .3575761, .1804375],
                       [.2126729, .7151522, .0721750],
                       [.0193339, .1191920, .9503041]], dtype=np.float32)
    xyz = linear @ matrix.T / np.array([.95047, 1.0, 1.08883], dtype=np.float32)
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack((116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])), axis=-1)


def delta(a, b):
    return np.sqrt(np.sum((a - b) ** 2, axis=-1))


def colour_count(rgb, visible):
    c = rgb[visible].astype(np.uint32)
    return int(len(np.unique((c[:, 0] << 16) | (c[:, 1] << 8) | c[:, 2])))


def protected_edges(lab, visible, threshold):
    protected = np.zeros(visible.shape, dtype=bool)
    for axis in (0, 1):
        a = (slice(None, -1), slice(None)) if axis == 0 else (slice(None), slice(None, -1))
        b = (slice(1, None), slice(None)) if axis == 0 else (slice(None), slice(1, None))
        edge = (delta(lab[a], lab[b]) >= threshold) & visible[a] & visible[b]
        protected[a] |= edge
        protected[b] |= edge
    return protected


def bilateral(rgb, lab, alpha, strength):
    """5x5, sigmaSpace=1 px, Lab range weights; average stored sRGB bytes."""
    height, width = alpha.shape
    numer = np.zeros(rgb.shape, dtype=np.float32)
    denom = np.zeros(alpha.shape, dtype=np.float32)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            y0, y1 = max(0, -dy), min(height, height - dy)
            x0, x1 = max(0, -dx), min(width, width - dx)
            dst = (slice(y0, y1), slice(x0, x1))
            src = (slice(y0 + dy, y1 + dy), slice(x0 + dx, x1 + dx))
            distance2 = np.sum((lab[dst] - lab[src]) ** 2, axis=-1)
            weights = np.exp(-.5 * (dx * dx + dy * dy) - distance2 / (2 * strength * strength))
            weights *= alpha[src] / 255.0
            numer[dst] += weights[..., None] * rgb[src]
            denom[dst] += weights
    # Empty support is restored below, without allowing NaN to propagate.
    return np.clip(np.rint(numer / np.maximum(denom[..., None], 1e-20)), 0, 255).astype(np.uint8)


def process_cleanup(pixels, strength=4, palette_colors=256):
    if not isinstance(pixels, np.ndarray) or pixels.dtype != np.uint8 or pixels.ndim != 3 or pixels.shape[2] not in (3, 4):
        raise ValueError("입력은 RGB/RGBA uint8 배열이어야 합니다.")
    if min(pixels.shape[:2]) < 1 or pixels.shape[0] * pixels.shape[1] > 4_000_000:
        raise ValueError("입력 제한은 4 MP입니다.")
    if type(strength) not in (int, float) or strength not in (2, 4, 8):
        raise ValueError("색 정리 강도는 2, 4, 8 ΔE76 중 하나입니다.")
    if type(palette_colors) is not int or palette_colors not in (64, 128, 256):
        raise ValueError("후보 팔레트는 64, 128, 256색 중 하나입니다.")
    start = time.perf_counter()
    before_hash = hashlib.sha256(pixels.tobytes()).hexdigest()
    rgb = pixels[..., :3]
    alpha = pixels[..., 3] if pixels.shape[2] == 4 else np.full(pixels.shape[:2], 255, dtype=np.uint8)
    visible = alpha > 0
    before_colors = colour_count(rgb, visible)
    lab = rgb_lab(rgb)
    threshold = max(12, 3 * strength)
    protected = protected_edges(lab, visible, threshold)
    output = pixels.copy()
    timings = {}
    mapped_count = fallback_count = 0
    noop = before_colors <= palette_colors
    if not noop:
        stage = time.perf_counter()
        smoothed = bilateral(rgb, lab, alpha, strength)
        allowed = visible & ~protected & (delta(lab, rgb_lab(smoothed)) <= strength)
        smoothed[~allowed] = rgb[~allowed]
        timings["bilateral_seconds"] = time.perf_counter() - stage
        stage = time.perf_counter()
        # Train only on visible pixels; hidden background must not spend palette slots.
        training_mask = alpha >= 16
        if not np.any(training_mask):
            training_mask = visible
        training = Image.fromarray(smoothed[training_mask][None, ...])
        palette = training.quantize(colors=palette_colors, method=Image.Quantize.MEDIANCUT,
                                    dither=Image.Dither.NONE)
        mapped = np.asarray(Image.fromarray(smoothed).quantize(palette=palette, dither=Image.Dither.NONE).convert("RGB"))
        allowed_palette = visible & ~protected & (delta(lab, rgb_lab(mapped)) <= strength)
        result = smoothed.copy()
        result[allowed_palette] = mapped[allowed_palette]
        result[protected | ~visible] = rgb[protected | ~visible]
        output[..., :3] = result
        mapped_count = int(np.count_nonzero(allowed_palette))
        fallback_count = int(np.count_nonzero(visible & ~protected & ~allowed_palette))
        timings["palette_seconds"] = time.perf_counter() - stage
    out_lab = rgb_lab(output[..., :3])
    errors = delta(lab, out_lab)
    max_error = float(np.max(errors, initial=0))
    alpha_exact = np.array_equal(output[..., 3:], pixels[..., 3:])
    hidden_exact = np.array_equal(output[~visible], pixels[~visible])
    edge_exact = np.array_equal(output[..., :3][protected], rgb[protected])
    source_exact = hashlib.sha256(pixels.tobytes()).hexdigest() == before_hash
    if not (output.shape == pixels.shape and source_exact and alpha_exact and hidden_exact and edge_exact
            and np.isfinite(errors).all() and max_error <= strength + .001):
        raise RuntimeError("색 정리 보존 계약 실패: 출력 저장을 중단합니다.")
    changed = visible & np.any(output[..., :3] != rgb, axis=-1)
    # Measure the same source-defined low-contrast pairs, excluding protected endpoints.
    noise_before = noise_after = 0.0
    noise_pairs = 0
    for axis in (0, 1):
        a = (slice(None, -1), slice(None)) if axis == 0 else (slice(None), slice(None, -1))
        b = (slice(1, None), slice(None)) if axis == 0 else (slice(None), slice(1, None))
        d0, d1 = delta(lab[a], lab[b]), delta(out_lab[a], out_lab[b])
        mask = visible[a] & visible[b] & ~protected[a] & ~protected[b] & (d0 > 0) & (d0 <= strength)
        noise_before += float(np.sum(d0[mask] ** 2, dtype=np.float64))
        noise_after += float(np.sum(d1[mask] ** 2, dtype=np.float64))
        noise_pairs += int(np.count_nonzero(mask))
    report = {
        "schema": "perfect-pixel-colour-cleanup/3", "algorithm": "bounded bilateral + median-cut palette, dithering NONE",
        "grid_status": "source_resolution_cleanup", "grid_recovered": False, "period_source_px": 1,
        "source_dimensions": [pixels.shape[1], pixels.shape[0]], "output_dimensions": [pixels.shape[1], pixels.shape[0]],
        "source_array_sha256": before_hash, "output_array_sha256": hashlib.sha256(output.tobytes()).hexdigest(),
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "settings": {"maximum_delta_e76": strength, "candidate_palette_colors": palette_colors,
                     "radius_source_px": 2, "sigma_space_px": 1, "sigma_colour_delta_e76": strength,
                     "strong_edge_threshold_delta_e76": threshold, "dithering": "NONE",
                     "palette_training": "alpha >= 16; all visible only if no such pixel exists",
                     "filter_average_space": "stored sRGB byte values; CIELAB D65 weights"},
        "geometry": {"nonlinear_warp": False, "inverse_jacobian": [[1, 0], [0, 1]], "resized": False, "cropped": False},
        "invariants": {"input_unchanged": source_exact, "alpha_byte_exact": alpha_exact,
                       "hidden_rgb_exact": hidden_exact, "protected_edge_rgb_exact": edge_exact,
                       "protected_edge_pixel_count": int(np.count_nonzero(protected)), "maximum_measured_delta_e76": max_error},
        "colour_statistics": {"visible_rgb_colors_before": before_colors, "visible_rgb_colors_after": colour_count(output[..., :3], visible),
                              "changed_visible_pixels": int(np.count_nonzero(changed)), "palette_mapped_pixels": mapped_count,
                              "preservation_fallback_pixels": fallback_count, "already_limited_palette_noop": noop},
        "low_contrast_statistics": {"source_selected_pair_count": noise_pairs,
                                    "squared_delta_e76_before": noise_before, "squared_delta_e76_after": noise_after,
                                    "energy_ratio": noise_after / noise_before if noise_before else None,
                                    "meaning": "local colour variation only; not a semantic feature or art quality score"},
        "elapsed_seconds": time.perf_counter() - start, "stage_seconds": timings,
        "warnings": ["원본 크기의 색 정리 후보입니다. 원래 픽셀 격자 복원이나 모든 의미 있는 특징 보존을 증명하지 않습니다.",
                     "보호 색과 오차 제한 때문에 최종 색 수는 후보 팔레트 수보다 많을 수 있습니다.",
                     "고대비 외곽 잔색과 alpha 번짐은 보존될 수 있습니다. 이 경로는 alpha/matte를 변경하지 않습니다."],
    }
    return output, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--strength", type=int, choices=(2, 4, 8), default=4)
    parser.add_argument("--palette-colors", type=int, choices=(64, 128, 256), default=256)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("기존 결과 폴더를 덮어쓰지 않습니다.")
    source_bytes = args.source.read_bytes()
    with Image.open(args.source) as source:
        if source.mode not in ("RGB", "RGBA") or getattr(source, "n_frames", 1) != 1:
            parser.error("RGB/RGBA 단일 정지 이미지만 지원합니다.")
        output, report = process_cleanup(np.array(source), args.strength, args.palette_colors)
    if args.source.read_bytes() != source_bytes:
        raise RuntimeError("원본 파일이 변경됐습니다.")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    Image.fromarray(output).save(args.output_dir / "output.png")
    report["source_path"] = str(args.source.resolve())
    report["source_file_sha256"] = hashlib.sha256(source_bytes).hexdigest()
    with (args.output_dir / "receipt.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str((args.output_dir / "output.png").resolve()), "report": report}, ensure_ascii=False))


if __name__ == "__main__":
    main()
