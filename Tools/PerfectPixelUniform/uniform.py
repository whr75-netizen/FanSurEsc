"""V2: recover only a common repeated RGBA lattice proven lossless.

No manual output size, coarse-period guess, local warp or colour conversion.
The former upstream detector and fractional sampler remain diagnostic helpers;
production does not call them. Unsupported sources are rejected without a PNG.
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

    def __init__(self, message, report=None):
        super().__init__(message)
        self.report = report or {"grid_status": "rejected", "reason": message}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def original_period(rgb, engine_root=None, deps=None):
    """V1 diagnostic only; NOT the production period selector in V2."""
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


def axis_evidence(pixels, axis):
    """Exact byte boundaries, including weak colours and alpha-only features."""
    if axis == 1:
        changed = np.any(pixels[:, 1:] != pixels[:, :-1], axis=(0, 2))
    else:
        changed = np.any(pixels[1:] != pixels[:-1], axis=(1, 2))
    positions = np.flatnonzero(changed).astype(np.int64) + 1
    intervals = np.diff(positions)
    step_gcd = int(np.gcd.reduce(intervals)) if len(intervals) else 0
    return positions, {
        "change_boundary_count": int(len(positions)),
        "boundary_interval_gcd": step_gcd,
        "first_boundary": int(positions[0]) if len(positions) else None,
        "flat_axis": not bool(len(positions)),
        "boundary_examples": positions[:16].tolist(),
        "evidence": "all RGB/RGBA byte changes, no threshold or peak suppression",
    }


def lossless_axis(length, step, positions):
    phase = int(positions[0] % step) if len(positions) else 0
    source_coords = np.arange(length, dtype=np.int64)
    global_cells = np.floor_divide(source_coords - phase, step)
    first_cell = int(global_cells[0])
    cells = global_cells - first_cell
    count = int(cells[-1]) + 1
    starts = np.r_[0, np.flatnonzero(np.diff(cells)) + 1]
    ends = np.r_[starts[1:], length]
    # Representative centre of the source intersection, including partial ends.
    sample_indices = np.floor((starts + ends) / 2).astype(np.int64)
    nominal_centres = phase + (first_cell + np.arange(count) + 0.5) * step
    return cells, sample_indices, {
        "boundary_phase_source_px": phase,
        "source_offset": phase + first_cell * step,
        "nominal_centre_origin": float(nominal_centres[0]),
        "partial_first_cell": int(ends[0] - starts[0]) != step,
        "partial_last_cell": int(ends[-1] - starts[-1]) != step,
        "source_interval_centres": ((starts + ends) / 2).tolist(),
    }


def process_array(pixels, engine_root=None, deps=None):
    if not isinstance(pixels, np.ndarray) or pixels.dtype != np.uint8 or pixels.ndim != 3 or pixels.shape[2] not in (3, 4):
        raise ValueError("입력은 RGB/RGBA uint8 배열이어야 합니다. 자동 모드 변환은 하지 않습니다.")
    if min(pixels.shape[:2]) < 2:
        raise ValueError("입력 각 축은 2픽셀 이상이어야 합니다.")
    start = time.perf_counter()
    source_digest = hashlib.sha256(pixels.tobytes()).hexdigest()
    xpos, xproof = axis_evidence(pixels, 1)
    ypos, yproof = axis_evidence(pixels, 0)
    gx, gy = xproof["boundary_interval_gcd"], yproof["boundary_interval_gcd"]
    step = math.gcd(gx, gy)
    report = {
        "schema": "perfect-pixel-uniform/2", "algorithm": "common integer boundary lattice + exact source reconstruction",
        "source_dimensions": [int(pixels.shape[1]), int(pixels.shape[0])],
        "source_mode": "RGBA" if pixels.shape[2] == 4 else "RGB", "source_array_sha256": source_digest,
        "axis_evidence": {"x": xproof, "y": yproof}, "period_source_px": step,
        "grid_status": "rejected", "preprocessing": "none", "manual_size_fallback": False, "local_refinement": False,
        "upstream_detector_used": False, "producer_sha256": sha256(Path(__file__)),
    }
    if step <= 1:
        report.update({"reason_code": "NO_LOSSLESS_COARSER_LATTICE", "output_dimensions": None,
                       "elapsed_seconds": time.perf_counter() - start})
        raise GridDetectionError("동일 RGBA 블록의 공통 간격을 2px 이상으로 확인하지 못했습니다. 이미 1px 원본이거나 격자가 불규칙한 입력입니다. 특징을 버리는 축소는 실행하지 않습니다.", report)
    candidates = [n for n in range(2, step + 1) if step % n == 0]
    # A larger period must also reconstruct exactly; frequency strength never wins.
    report["consistent_divisor_steps"] = candidates
    ix, sx, xmap = lossless_axis(pixels.shape[1], step, xpos)
    iy, sy, ymap = lossless_axis(pixels.shape[0], step, ypos)
    output = pixels[sy[:, None], sx[None, :]].copy()
    reconstructed = output[iy[:, None], ix[None, :]]
    changed_texels = int(np.count_nonzero(np.any(reconstructed != pixels, axis=2)))
    report["reconstruction"] = {"changed_source_texels": changed_texels, "required_changed_texels": 0,
                                "scope": "entire source canvas, every RGB/RGBA byte including hidden RGB and alpha",
                                "source_reconstructed_sha256": hashlib.sha256(reconstructed.tobytes()).hexdigest()}
    if changed_texels:
        report.update({"reason_code": "SOURCE_DETAIL_LOSS", "output_dimensions": None,
                       "elapsed_seconds": time.perf_counter() - start})
        raise GridDetectionError("픽셀 경계 후보가 원본 세부를 변경합니다. 결과를 저장하지 않습니다.", report)
    if hashlib.sha256(pixels.tobytes()).hexdigest() != source_digest:
        raise RuntimeError("입력 배열이 변경됐습니다.")
    warnings = ["관찰된 반복 표현을 무손실로 축약했습니다. 더 작은 작가 격자와 미술적 완성은 이 증거만으로 확정하지 않습니다."]
    if any(a[key] for a in (xmap, ymap) for key in ("partial_first_cell", "partial_last_cell")):
        warnings.append("원본 가장자리에 잘린 셀이 있습니다. source canvas/offset 기록을 함께 사용해야 같은 범위로 재표시할 수 있습니다.")
    report.update({
        "grid_status": "verified_lossless", "warnings": warnings,
        "output_dimensions": [int(output.shape[1]), int(output.shape[0])],
        "output_array_sha256": hashlib.sha256(output.tobytes()).hexdigest(),
        "elapsed_seconds": time.perf_counter() - start,
        "geometry": {"nonlinear_warp": False, "inverse_jacobian": [[step, 0], [0, step]], "spacing_error": 0,
                     "source_offset": [xmap["source_offset"], ymap["source_offset"]],
                     "edge_policy": "source canvas intersection of global cells; no discarded edge features",
                     "axis_source_coverage": {"x": xmap, "y": ymap}},
        "grid": {"cell_x_indices": ix.tolist(), "cell_y_indices": iy.tolist(),
                 "sample_x_indices": sx.tolist(), "sample_y_indices": sy.tolist(),
                 "centre_origin_source_px": [xmap["nominal_centre_origin"], ymap["nominal_centre_origin"]],
                 "phase_boundary_source_px": [xmap["boundary_phase_source_px"], ymap["boundary_phase_source_px"]]},
    })
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
    try:
        output, report = process_array(pixels, args.engine, args.deps)
    except GridDetectionError as error:
        if sha256(args.source) != source_hash:
            raise RuntimeError("원본 파일이 변경됐습니다.")
        args.output_dir.mkdir(parents=True, exist_ok=False)
        diagnostic = dict(error.report, error=str(error), source_path=str(args.source.resolve()), source_sha256=source_hash)
        with (args.output_dir / "failure.json").open("x", encoding="utf-8") as stream:
            json.dump(diagnostic, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps(diagnostic, ensure_ascii=False))
        raise SystemExit(2)
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
