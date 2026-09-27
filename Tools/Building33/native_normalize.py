"""Run upstream PerfectPixel automatic detection without a requested output size.

This probe records normalization evidence, not layout or artistic acceptance.
The upstream file is imported from --engine and is never edited. RGB pixels are
passed unchanged; RGBA alpha is sampled at the exact same upstream cell centers.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys


class AutomaticGridFailure(RuntimeError):
    """The source did not produce a usable upstream automatic grid."""


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True,
                        help="Upstream checkout root or its package __init__.py file")
    parser.add_argument("--deps", type=Path, required=True,
                        help="Existing dependencies containing NumPy/Pillow; upstream chooses cv2 when available")
    return parser.parse_args(argv)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_engine(engine_path, deps_path):
    if not deps_path.is_dir():
        raise FileNotFoundError(f"Dependency directory does not exist: {deps_path}")
    sys.path.insert(0, str(deps_path))
    path = engine_path if engine_path.is_file() else engine_path / "src/perfect_pixel/__init__.py"
    if not path.is_file():
        raise FileNotFoundError(f"Upstream public package not found: {path}")
    if path.name != "__init__.py":
        raise ValueError("--engine must select the upstream package, not bypass its backend selector")
    spec = importlib.util.spec_from_file_location("building33_upstream_perfectpixel", path,
                                                submodule_search_locations=[str(path.parent)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    spec.loader.exec_module(package)
    module = sys.modules[package.get_perfect_pixel.__module__]
    return package, module, Path(module.__file__), path


def automatic_sample(engine, source, receipt, entry_point=None):
    """Observe upstream calls without changing their inputs or returned values."""
    import numpy as np

    rgb = source[..., :3].copy()
    observed = {}
    originals = {}

    def observe(name):
        original = getattr(engine, name)
        originals[name] = original

        def wrapped(*args, **kwargs):
            value = original(*args, **kwargs)
            observed.setdefault(name, []).append(value)
            return value

        setattr(engine, name, wrapped)

    for name in ("estimate_grid_fft", "estimate_grid_gradient", "detect_grid_scale", "refine_grids"):
        observe(name)
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            width, height, output_rgb = (entry_point or engine.get_perfect_pixel)(
                rgb, grid_size=None, sample_method="center", refine_intensity=0.25,
                fix_square=False, debug=False)
    finally:
        for name, original in originals.items():
            setattr(engine, name, original)
        receipt["upstream_stdout"] = captured.getvalue()
        receipt["automatic_detection"] = {
            name: [[None if value is None else float(value) for value in pair]
                   if pair is not None else None for pair in observed.get(name, [])]
            for name in ("estimate_grid_fft", "estimate_grid_gradient", "detect_grid_scale")}
    if width is None or height is None or width < 1 or height < 1:
        raise AutomaticGridFailure("AUTOMATIC_GRID_NOT_FOUND: no manual output-size fallback is permitted")
    grids = observed.get("refine_grids", [])
    if len(grids) != 1:
        raise AutomaticGridFailure("Unexpected upstream grid-call count; alpha correspondence is unknown")
    x_lines, y_lines = (np.asarray(values) for values in grids[0])
    receipt["refined_grid"] = {
        "x_source_boundaries": x_lines.tolist(),
        "y_source_boundaries": y_lines.tolist(),
        "x_source_centers": np.clip((x_lines[1:] + x_lines[:-1]) * 0.5, 0,
                                    source.shape[1] - 1).astype(np.int32).tolist(),
        "y_source_centers": np.clip((y_lines[1:] + y_lines[:-1]) * 0.5, 0,
                                    source.shape[0] - 1).astype(np.int32).tolist(),
        "dimensions": [int(width), int(height)],
    }
    sampled_source = engine.sample_center(source, x_lines, y_lines)
    if output_rgb.shape != (height, width, 3) or not np.array_equal(output_rgb, sampled_source[..., :3]):
        raise AutomaticGridFailure("Upstream RGB and recorded source-cell coordinates differ")
    if source.shape[2] == 4:
        output = np.concatenate((output_rgb, sampled_source[..., 3:4]), axis=2)
        receipt["alpha"] = "Unmodified source alpha sampled at the same upstream cell centers as RGB"
    else:
        output = output_rgb
        receipt["alpha"] = "RGB source has no alpha; none added"
    receipt["selected_source_rgb_identity"] = True
    receipt["output_dimensions"] = [int(width), int(height)]
    return output


def main(argv=None):
    args = arguments(argv)
    source_path = args.source.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    # An existing result or even an existing output directory is never replaced.
    output_dir.mkdir(parents=True, exist_ok=False)
    receipt = {
        "schema": "building33-upstream-auto-grid/1",
        "status": "running",
        "source_path": str(source_path),
        "source_sha256": digest(source_path),
        "settings": {"grid_size": None, "sample_method": "center", "refine_intensity": 0.25,
                     "fix_square": False, "debug": False},
        "preprocessing": "none: no crop, resize, palette conversion, alpha threshold, or boundary repair",
        "contract": {
            "output_size_owner": "Upstream automatic detector and its refined grid only",
            "manual_size_fallback": False,
            "evidence_scope": "One source normalization; no Unity integration or layout acceptance",
            "artistic_approval": "not evaluated",
            "limits": ["Auto-detection can choose an incorrect grid when the source has no consistent lattice.",
                       "A single source sample per detected cell cannot preserve every source feature.",
                       "Identical selected RGB is not evidence of feature or artistic preservation.",
                       "Upstream RGB input convention and implementation are used unchanged.",
                       "RGBA hidden RGB participates in upstream detection; no background is silently changed."],
        },
    }
    exit_code = 1
    try:
        package, engine, engine_path, selector_path = load_engine(args.engine.resolve(), args.deps.resolve())
        import numpy as np
        import PIL
        from PIL import Image
        receipt["engine"] = {"path": str(engine_path), "sha256": digest(engine_path),
                             "entry_point": "perfect_pixel.get_perfect_pixel",
                             "module": package.get_perfect_pixel.__module__,
                             "selector_path": str(selector_path), "selector_sha256": digest(selector_path),
                             "backend": "NumPy" if engine_path.name == "perfect_pixel_noCV2.py" else "OpenCV"}
        receipt["dependencies"] = {"path": str(args.deps.resolve()), "numpy": np.__version__,
                                   "pillow": PIL.__version__}
        if hasattr(engine, "cv2"):
            receipt["dependencies"]["opencv"] = engine.cv2.__version__
        with Image.open(source_path) as image:
            if image.mode not in ("RGB", "RGBA"):
                raise ValueError(f"Only unconverted RGB/RGBA inputs are supported, got {image.mode}")
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError("Only one still-image frame is supported")
            receipt["source_mode"] = image.mode
            receipt["source_dimensions"] = list(image.size)
            source = np.array(image)
        if source.dtype != np.uint8:
            raise ValueError("Only unconverted 8-bit RGB/RGBA input is supported")
        output = automatic_sample(engine, source, receipt, package.get_perfect_pixel)
        if digest(engine_path) != receipt["engine"]["sha256"]:
            raise RuntimeError("Upstream engine changed during normalization")
        if digest(selector_path) != receipt["engine"]["selector_sha256"]:
            raise RuntimeError("Upstream backend selector changed during normalization")
        if digest(source_path) != receipt["source_sha256"]:
            raise RuntimeError("Source changed during normalization")
        output_path = output_dir / "native.png"
        with output_path.open("xb") as stream:
            Image.fromarray(output).save(stream, format="PNG")
        receipt["output_path"] = str(output_path)
        receipt["output_sha256"] = digest(output_path)
        receipt["status"] = "normalized"
        exit_code = 0
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        with (output_dir / "receipt.json").open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(output_dir / "receipt.json"),
                      "dimensions": receipt.get("output_dimensions"), "error": receipt.get("error")},
                     ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
