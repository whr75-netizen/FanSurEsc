"""Original PerfectPixel period detection followed by one global affine sampler.

This is a separate correction, NOT the unchanged upstream get_perfect_pixel.
The upstream files and input arrays are never edited. No requested output size,
per-boundary refinement, cumulative rounding, palette processing or resize.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENGINE = Path.home() / "Desktop/GPT/3/perfectPixel-main/perfectPixel-main"
DEFAULT_DEPS = ROOT / "LocalOnly/PerfectPixelOpenCV"


class GridDetectionError(RuntimeError):
    """Automatic detection is unusable; never invent a fallback grid."""


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def original_period(rgb, engine_root=None, deps=None):
    """Observe original estimates before detect_grid_scale's final rounding."""
    helper = ROOT / "Tools/Building33/native_normalize.py"
    spec = importlib.util.spec_from_file_location("uniform_original_loader", helper)
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    _, engine, module_path, selector_path = loader.load_engine(
        Path(engine_root or DEFAULT_ENGINE), Path(deps or DEFAULT_DEPS))
    hashes = {str(p): sha256(p) for p in (module_path, selector_path)}
    observations = []
    originals = {}
    stdout = io.StringIO()

    def observe(name):
        original = getattr(engine, name)
        originals[name] = original

        def wrapped(*args, **kwargs):
            value = original(*args, **kwargs)
            observations.append({"method": name, "grid_counts": [
                None if x is None else float(x) for x in value]})
            return value
        setattr(engine, name, wrapped)

    try:
        observe("estimate_grid_fft")
        observe("estimate_grid_gradient")
        with contextlib.redirect_stdout(stdout), np.errstate(divide="ignore", invalid="ignore"):
            rounded = engine.detect_grid_scale(rgb.copy(), peak_width=6, max_ratio=1.5, min_size=4)
        if len(rounded) != 2 or any(x is None for x in rounded) or not observations:
            raise GridDetectionError("원본 자동 격자 검출이 실패했습니다. 임의 크기로 대체하지 않습니다.")
        counts = observations[-1]["grid_counts"]
        if any(x is None or not math.isfinite(x) or x <= 0 for x in counts):
            raise GridDetectionError("원본 검출기의 격자 개수가 올바르지 않습니다.")
        height, width = rgb.shape[:2]
        sx, sy = width / counts[0], height / counts[1]
        ratio = max(sx, sy) / min(sx, sy)
        period = min(sx, sy) if ratio > 1.5 else (sx + sy) / 2
        if not math.isfinite(period) or period < 1:
            raise GridDetectionError("검출 간격이 1 원본 픽셀 미만이거나 비유한 값입니다.")
    except GridDetectionError:
        raise
    except Exception as error:
        raise GridDetectionError("원본 자동 검출 오류: " + str(error)) from error
    finally:
        for name, original in originals.items():
            setattr(engine, name, original)
        if any(sha256(p) != digest for p, digest in hashes.items()):
            raise RuntimeError("실행 중 원본 엔진 파일이 변경됐습니다.")
    return float(period), {
        "estimates": observations,
        "selected_counts_before_final_rounding": counts,
        "rounded_detect_grid_scale_counts": [int(x) for x in rounded],
        "axis_periods_source_px": [float(sx), float(sy)],
        "common_period_rule": "upstream min if ratio > 1.5 else arithmetic mean",
        "stdout": stdout.getvalue(),
        "upstream_input_convention": "unchanged RGB passed to original detector (OpenCV uses BGR gray weights)",
        "engine": {"path": str(module_path), "sha256": hashes[str(module_path)],
                   "selector_path": str(selector_path), "selector_sha256": hashes[str(selector_path)],
                   "backend": "OpenCV" if hasattr(engine, "cv2") else "NumPy"},
    }


def edge_profile(pixels, axis):
    """One global edge profile; opacity weights affect analysis only."""
    colors = pixels[..., :3].astype(np.float32) / 255
    alpha = pixels[..., 3].astype(np.float32) / 255 if pixels.shape[2] == 4 else np.ones(pixels.shape[:2], np.float32)
    if axis == 1:
        rgb = np.abs(colors[:, 1:] - colors[:, :-1]).mean(axis=2)
        edge = rgb * np.minimum(alpha[:, 1:], alpha[:, :-1]) + np.abs(alpha[:, 1:] - alpha[:, :-1])
        profile = edge.mean(axis=0, dtype=np.float64)
    else:
        rgb = np.abs(colors[1:] - colors[:-1]).mean(axis=2)
        edge = rgb * np.minimum(alpha[1:], alpha[:-1]) + np.abs(alpha[1:] - alpha[:-1])
        profile = edge.mean(axis=1, dtype=np.float64)
    # A difference between texels k-1 and k lies at source boundary k.
    return np.arange(1, len(profile) + 1, dtype=np.float64), profile


def global_phase(pixels, period, axis):
    positions, energy = edge_profile(pixels, axis)
    total = float(energy.sum())
    if total <= 0:
        return 0.0, 0.0, False
    coefficient = np.dot(energy, np.exp(-2j * np.pi * positions / period))
    coherence = float(abs(coefficient) / total)
    if abs(coefficient) <= np.finfo(float).eps * total:
        return 0.0, coherence, False
    phase = float((-period * np.angle(coefficient) / (2 * np.pi)) % period)
    return phase, coherence, True


def axis_centres(length, period, boundary_phase):
    origin = float((boundary_phase + period / 2) % period)
    count = int(math.ceil((length - origin) / period))
    if count <= 0:
        raise GridDetectionError("이미지 범위 안에 표본 중심이 없습니다.")
    centres = origin + np.arange(count, dtype=np.float64) * period
    centres = centres[centres < length]
    indices = np.floor(centres).astype(np.int64)
    return origin, centres, indices


def uniform_sample(pixels, period, phases):
    """Pure sampler used by automatic production and independent known-grid tests."""
    if not math.isfinite(period) or period < 1:
        raise GridDetectionError("올바른 공통 간격이 필요합니다.")
    if len(phases) != 2 or any(not math.isfinite(x) for x in phases):
        raise GridDetectionError("올바른 전역 위상이 필요합니다.")
    height, width = pixels.shape[:2]
    x0, cx, ix = axis_centres(width, period, phases[0])
    y0, cy, iy = axis_centres(height, period, phases[1])
    output = pixels[iy[:, None], ix[None, :]].copy()
    spacing_error = max(float(np.max(np.abs(np.diff(c) - period))) if len(c) > 1 else 0.0 for c in (cx, cy))
    nearest_error = max(float(np.max(np.abs(c - (i + 0.5)))) for c, i in ((cx, ix), (cy, iy)))
    if spacing_error > 1e-10 or nearest_error > 0.5 + 1e-10:
        raise RuntimeError("좌표 불변조건을 만족하지 못했습니다.")
    return output, {
        "geometry": {"nonlinear_warp": False, "inverse_jacobian": [[period, 0.0], [0.0, period]],
                     "spacing_error": spacing_error, "nearest_source_center_error_max": nearest_error,
                     "edge_policy": "sample centres inside source only; no border clamp, forced endpoint or last-cell stretch"},
        "grid": {"centre_origin_source_px": [x0, y0], "phase_boundary_source_px": [float(p) for p in phases],
                 "sample_x_indices": ix.tolist(), "sample_y_indices": iy.tolist(),
                 "first_last_centre_source_px": [[float(cx[0]), float(cx[-1])], [float(cy[0]), float(cy[-1])]]},
    }


def process_array(pixels, engine_root=None, deps=None):
    if not isinstance(pixels, np.ndarray) or pixels.dtype != np.uint8 or pixels.ndim != 3 or pixels.shape[2] not in (3, 4):
        raise ValueError("입력은 RGB/RGBA uint8 배열이어야 합니다. 자동 모드 변환은 하지 않습니다.")
    if min(pixels.shape[:2]) < 2:
        raise ValueError("입력 각 축은 2픽셀 이상이어야 합니다.")
    if not np.any(pixels[..., :3] != pixels[0, 0, :3]):
        raise GridDetectionError("RGB 경계 신호가 없는 단색 입력에서 자동 격자를 확정할 수 없습니다.")
    start = time.perf_counter()
    source_digest = hashlib.sha256(pixels.tobytes()).hexdigest()
    period, detection = original_period(pixels[..., :3], engine_root, deps)
    px, rx, known_x = global_phase(pixels, period, 1)
    py, ry, known_y = global_phase(pixels, period, 0)
    output, transform = uniform_sample(pixels, period, [px, py])
    warnings = ["간격/위상은 자동 추정값입니다. 등간격 계산은 원본 특징·디자인 보존의 증명이 아닙니다."]
    warnings.append("원본 안의 격자 중심만 표본으로 취합니다. 중심 사이의 미세 특징과 캔버스 가장자리 세부는 출력에서 사라질 수 있습니다.")
    if len(detection["estimates"]) > 1:
        warnings.append("원본 FFT 후보가 채택되지 않아 gradient 후보를 사용했습니다. 격자 해석이 불명확할 수 있습니다.")
    if not known_x or not known_y:
        warnings.append("한 축 이상의 위상 신호가 없어 명시된 0 경계 위상을 사용했습니다. 격자는 미확정입니다.")
    if min(rx, ry) < 0.1:
        warnings.append("전역 위상 신호가 약합니다(coherence < 0.1). 잘못된 간격/위상과 세부 손실 가능성을 확인하십시오.")
    status = "estimated" if known_x and known_y and min(rx, ry) >= 0.1 else "unconfirmed"
    if hashlib.sha256(pixels.tobytes()).hexdigest() != source_digest:
        raise RuntimeError("입력 배열이 변경됐습니다.")
    report = {
        "schema": "perfect-pixel-uniform/1", "algorithm": "original detector + global phase + affine nearest sample",
        "source_dimensions": [int(pixels.shape[1]), int(pixels.shape[0])],
        "output_dimensions": [int(output.shape[1]), int(output.shape[0])],
        "source_mode": "RGBA" if pixels.shape[2] == 4 else "RGB",
        "period_source_px": period, "grid_status": status, "phase_coherence": [rx, ry], "warnings": warnings,
        "preprocessing": "none", "manual_size_fallback": False, "local_refinement": False,
        "source_array_sha256": source_digest, "output_array_sha256": hashlib.sha256(output.tobytes()).hexdigest(),
        "automatic_detection": detection, "elapsed_seconds": time.perf_counter() - start,
        "phase_energy": "mean absolute RGB difference weighted by min opacity + absolute opacity difference; analysis only",
        **transform,
    }
    return output, report


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    parser.add_argument("--deps", type=Path, default=DEFAULT_DEPS)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("결과 폴더가 이미 있습니다. 기존 결과를 덮어쓰지 않습니다.")
    source_hash = sha256(args.source)
    with Image.open(args.source) as image:
        if image.mode not in ("RGB", "RGBA") or getattr(image, "n_frames", 1) != 1:
            parser.error("RGB/RGBA 단일 이미지만 지원합니다.")
        pixels = np.array(image)
    output, report = process_array(pixels, args.engine, args.deps)
    if sha256(args.source) != source_hash:
        raise RuntimeError("원본 파일이 변경됐습니다.")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    output_path = args.output_dir / "output.png"
    Image.fromarray(output).save(output_path)
    report.update({"source_path": str(args.source.resolve()), "source_sha256": source_hash,
                   "output_sha256": sha256(output_path)})
    with (args.output_dir / "receipt.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(output_path.resolve()), "dimensions": report["output_dimensions"],
                      "period_source_px": report["period_source_px"], "grid_status": report["grid_status"],
                      "elapsed_seconds": report["elapsed_seconds"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
