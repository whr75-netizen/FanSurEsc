"""Narrow B33 production preflight; not an art judge or a security sandbox.

WorkLoop must pin this file, native_normalize.py, and upstream code_files before
running the producer. Receipts are checked against actual registered files and
sampled pixels, never against an AI-authored approval flag.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
RECEIPT_KEYS = set("schema status source_path source_sha256 settings preprocessing contract engine dependencies source_mode source_dimensions upstream_stdout automatic_detection refined_grid alpha selected_source_rgb_identity output_dimensions output_path output_sha256".split())
SETTINGS = dict(grid_size=None, sample_method="center", refine_intensity=0.25, fix_square=False, debug=False)


class Rejected(ValueError):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


def require(value, code, detail):
    if not value:
        raise Rejected(code, detail)


def resolve(value):
    require(isinstance(value, str) and bool(value), "INVALID_PATH", "A real file path is required.")
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve(strict=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"),
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def registered(record, label):
    require(isinstance(record, dict) and set(record) == {"path", "sha256"},
            "REGISTRATION_REQUIRED", label + " must have an exact path and SHA-256.")
    path = resolve(record["path"])
    require(path.is_file() and sha(path) == record["sha256"], "REGISTERED_HASH_MISMATCH", label)
    return path


def png(path, dimensions):
    with path.open("rb") as stream:
        header = stream.read(24)
    require(len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR",
            "INVALID_PNG", str(path))
    actual = list(struct.unpack(">II", header[16:24]))
    require(actual == dimensions and all(type(n) is int and n > 0 for n in dimensions),
            "PNG_DIMENSION_MISMATCH", str(path))


def normalize(contract, receipt_path):
    require(receipt_path is not None, "NORMALIZATION_RECEIPT_REQUIRED", "Pass the actual native_normalize receipt.")
    receipt = read(resolve(str(receipt_path)))
    require(isinstance(receipt, dict) and set(receipt) == RECEIPT_KEYS,
            "UNREGISTERED_RECEIPT_SCHEMA", "Only native automatic-grid receipts are accepted; target sizes/PPU/scales are forbidden.")
    require(receipt["schema"] == "building33-upstream-auto-grid/1" and receipt["status"] == "normalized",
            "NATIVE_NORMALIZATION_REQUIRED", "The producer must finish automatic normalization.")
    require(receipt["settings"] == SETTINGS and receipt["settings"]["grid_size"] is None and
            receipt["settings"]["fix_square"] is False and receipt["settings"]["debug"] is False,
            "MANUAL_GRID_FORBIDDEN", "Use the upstream automatic grid, center sampling and no square correction.")
    require(receipt["preprocessing"] == "none: no crop, resize, palette conversion, alpha threshold, or boundary repair",
            "PREPROCESSING_FORBIDDEN", "No undeclared source manipulation is permitted.")
    dependencies = receipt["dependencies"]
    require(isinstance(dependencies, dict) and {"path", "numpy", "pillow"} <= set(dependencies)
            and set(dependencies) <= {"path", "numpy", "pillow", "opencv"}
            and all(isinstance(value, str) for value in dependencies.values()),
            "DEPENDENCY_SCHEMA_MISMATCH", "Only recorded dependency versions and path are accepted.")
    scope = receipt["contract"]
    require(isinstance(scope, dict) and set(scope) == {"output_size_owner", "manual_size_fallback", "evidence_scope", "artistic_approval", "limits"}
            and scope["manual_size_fallback"] is False and scope["artistic_approval"] == "not evaluated"
            and scope["output_size_owner"] == "Upstream automatic detector and its refined grid only",
            "NATIVE_CONTRACT_MISMATCH", "No manual-size fallback or self-awarded art acceptance.")
    manifest = read(registered(contract["registered_source_manifest"], "source registry"))
    source = resolve(receipt["source_path"])
    source_hash = sha(source)
    matches = [item for item in manifest["assets"] if resolve(item["preserved_source_path"]) == source
               and item["original_sha256"] == source_hash == receipt["source_sha256"]]
    require(len(matches) == 1, "UNREGISTERED_SOURCE", "Source path and original bytes must match the frozen registry.")
    engine = receipt["engine"]
    require(isinstance(engine, dict) and set(engine) == {"path", "sha256", "entry_point", "module", "selector_path", "selector_sha256", "backend"},
            "ENGINE_SCHEMA_MISMATCH", "Backend and public selector evidence is required.")
    backend = registered({"path": engine["path"], "sha256": engine["sha256"]}, "selected backend")
    selector = registered({"path": engine["selector_path"], "sha256": engine["selector_sha256"]}, "public selector")
    require(backend == registered(contract["upstream_backend"], "frozen upstream backend") and
            selector == registered(contract["upstream_selector"], "frozen upstream selector"),
            "UPSTREAM_IDENTITY_CHANGED", "Self-reported engine hashes cannot replace the registered original.")
    expected = {"perfect_pixel_noCV2.py": "NumPy", "perfect_pixel.py": "OpenCV"}
    require(backend.name in expected and engine["backend"] == expected[backend.name] and
            selector.name == "__init__.py" and selector.parent == backend.parent and
            engine["entry_point"] == "perfect_pixel.get_perfect_pixel",
            "UNREGISTERED_ENGINE_ENTRY", "Use the upstream public backend selector.")
    detection = receipt["automatic_detection"]
    require(isinstance(detection, dict) and set(detection) == {"estimate_grid_fft", "estimate_grid_gradient", "detect_grid_scale"}
            and len(detection["detect_grid_scale"]) == 1, "DETECTION_EVIDENCE_MISSING", "One actual automatic detection is required.")
    output = resolve(receipt["output_path"])
    require(output != source and sha(output) == receipt["output_sha256"], "OUTPUT_HASH_MISMATCH", str(output))
    png(source, receipt["source_dimensions"])
    png(output, receipt["output_dimensions"])
    grid = receipt["refined_grid"]
    require(isinstance(grid, dict) and set(grid) == {"x_source_boundaries", "y_source_boundaries", "x_source_centers", "y_source_centers", "dimensions"}
            and grid["dimensions"] == receipt["output_dimensions"], "GRID_SCHEMA_MISMATCH", "Recorded refined-grid dimensions differ.")
    for axis, dimension in enumerate(("x", "y")):
        lines, centers = grid[dimension + "_source_boundaries"], grid[dimension + "_source_centers"]
        require(len(lines) == receipt["output_dimensions"][axis] + 1 and
                all(type(n) in (int, float) and math.isfinite(n) for n in lines) and
                all(a < b for a, b in zip(lines, lines[1:])), "INVALID_GRID", dimension)
        expected_centers = [int(max(0, min((a + b) * .5, receipt["source_dimensions"][axis] - 1)))
                            for a, b in zip(lines, lines[1:])]
        require(centers == expected_centers and all(type(n) is int for n in centers),
                "GRID_CENTER_MISMATCH", dimension)
    from PIL import Image  # Use the installed runtime, never receipt-supplied import paths.
    with Image.open(source) as original, Image.open(output) as normalized:
        require(original.mode in ("RGB", "RGBA") and original.mode == normalized.mode == receipt["source_mode"],
                "IMAGE_MODE_CHANGED", "Color/alpha channels must be preserved.")
        pixels, actual = original.load(), normalized.load()
        for y, sy in enumerate(grid["y_source_centers"]):
            for x, sx in enumerate(grid["x_source_centers"]):
                require(actual[x, y] == pixels[sx, sy], "SOURCE_SAMPLE_MISMATCH", f"Output cell ({x},{y}) changed.")
    return {"asset_id": matches[0]["id"], "source_sha256": source_hash,
            "output_sha256": receipt["output_sha256"], "dimensions": receipt["output_dimensions"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--stage", required=True, choices=("generation", "normalization", "placement"))
    parser.add_argument("--contract", type=Path, default=ROOT / "Tools/Building33/production-contract.json")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        contract_path = resolve(str(args.contract))
        contract = read(contract_path)
        layout = registered(contract["layout_template"], "layout template")
        require(contract["source_generation_method"] == "master_reference_per_asset",
                "GENERATION_METHOD_MISMATCH", "Individual assets must derive from the common reference plan.")
        evidence = {}
        if args.stage == "generation":
            require(contract["reference_art"] is not None, "REFERENCE_ART_NOT_REGISTERED",
                    "Create and register the common reference artwork before object generation.")
            reference = registered(contract["reference_art"], "reference artwork")
            from PIL import Image
            with Image.open(reference) as artwork:
                artwork.verify()
        else:
            evidence = normalize(contract, args.receipt)
            if args.stage == "placement":
                raise Rejected("PLACEMENT_SOLVER_NOT_REGISTERED",
                               "Projection calibration and per-asset template correspondence have no registered placement solver; normalization cannot authorize placement.")
        result = {"stage": args.stage, "allowed": True, "contract_sha256": sha(contract_path),
                  "layout_sha256": sha(layout), "evidence": evidence, "artistic_approval": "not evaluated",
                  "scope": "Registered inputs and automatic-sampling integrity only; no artistic quality, feature preservation or Unity placement approval."}
        code = 0
    except (Rejected, OSError, ValueError, KeyError, TypeError, ImportError) as error:
        result = {"stage": args.stage, "allowed": False, "code": getattr(error, "code", "INVALID_EVIDENCE"),
                  "detail": str(error), "artistic_approval": "not evaluated"}
        code = 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
