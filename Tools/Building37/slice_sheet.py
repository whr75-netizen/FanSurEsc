"""Reuse whole-sheet upstream normalization and split measured integer gutters.

Guide cells are search hints, never target resize/crop destinations. The mask
uses A>=26 for analysis only; every saved pixel retains its original RGBA.
Technical success covers this material partition, not art or Unity integration.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/artifacts/building37"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalization_input(args, Image):
    receipt = read(args.receipt)
    if receipt.get("status") != "normalized" or digest(args.native) != receipt.get("output_sha256"):
        raise ValueError("NORMALIZED_SOURCE_MISMATCH")
    source = Path(receipt["source_path"])
    if digest(source) != receipt.get("source_sha256"):
        raise ValueError("GENERATED_SOURCE_CHANGED")
    settings = receipt["settings"]
    if settings.get("grid_size") is not None or settings.get("sample_method") != "center" or settings.get("refine_intensity") != .25 or settings.get("fix_square") is not False:
        raise ValueError("UPSTREAM_AUTOMATIC_SETTINGS_CHANGED")
    for file_key, hash_key in (("path", "sha256"), ("selector_path", "selector_sha256")):
        if digest(Path(receipt["engine"][file_key])) != receipt["engine"][hash_key]:
            raise ValueError("UPSTREAM_ENGINE_CHANGED: " + file_key)
    with Image.open(args.native) as image:
        if image.mode != "RGBA" or list(image.size) != receipt["output_dimensions"]:
            raise ValueError("NORMALIZED_RGBA_CANVAS_CHANGED")
        sheet = image.copy()
    return receipt, source, sheet


def bands(empty):
    output, start = [], None
    for i, value in enumerate(list(empty) + [False]):
        if value and start is None:
            start = i
        if not value and start is not None:
            output.append([start, i])
            start = None
    return output


def partition(counts, hints):
    """Ordered DP selects only measured empty bands; all intervals need content."""
    length = len(counts)
    available = [b for b in bands(counts == 0) if b[0] > 0 and b[1] < length]
    candidates = [(b[0] + b[1]) // 2 for b in available]
    prefix = [0]
    for count in counts:
        prefix.append(prefix[-1] + int(count))
    states = {0: (0.0, [], [])}
    for hint in hints:
        following = {}
        for j, edge in enumerate(candidates):
            choices = []
            for previous, (score, selected, selected_bands) in states.items():
                if edge > previous and prefix[edge] > prefix[previous]:
                    choices.append((score + (edge / length - hint) ** 2, selected + [edge], selected_bands + [available[j]]))
            if choices:
                following[edge] = min(choices, key=lambda entry: (entry[0], -sum(b[1] - b[0] for b in entry[2])))
        states = following
        if not states:
            raise ValueError("No ordered transparent partition for the declared asset count")
    final = [entry for edge, entry in states.items() if prefix[length] > prefix[edge]]
    if not final:
        raise ValueError("No content after the last measured gutter")
    score, selected, selected_bands = min(final, key=lambda entry: (entry[0], -sum(b[1] - b[0] for b in entry[2])))
    return [0] + selected + [length], {"available_internal_bands": available, "selected_bands": selected_bands,
        "hints_fraction_only": hints, "selected_integer_lines": selected, "normalized_hint_distance_squared": score,
        "meaning": "Actual transparent bands choose cuts; guide proximity only resolves ordering"}


def measured_regions(sheet, contract, np):
    mask = np.asarray(sheet)[:, :, 3] >= 26
    rows = {}
    for asset in contract["assets"]:
        rows.setdefault(asset["packing"]["cell_xywh"][1], []).append(asset)
    rows = [(y, sorted(items, key=lambda asset: asset["packing"]["cell_xywh"][0])) for y, items in sorted(rows.items())]
    if len(contract["assets"]) != 18 or len({a["id"] for a in contract["assets"]}) != 18:
        raise ValueError("Expected eighteen distinct guide asset IDs")
    guide_w, guide_h = contract["canvas_logical_texels"]
    occupied_y = np.flatnonzero(mask.any(axis=1))
    if not len(occupied_y):
        raise ValueError("The canonical source contains no visible objects")
    start_y, end_y = int(occupied_y[0]), int(occupied_y[-1]) + 1
    # Perimeter contact cannot prove the generated silhouette was preserved.
    if start_y == 0 or end_y == sheet.height or mask[:, 0].any() or mask[:, -1].any():
        raise ValueError("Visible source touches the canvas perimeter; preserve and inspect clipping")
    row_hints = [y / guide_h for y, _ in rows[1:]]
    y_edges, row_evidence = partition(mask.sum(axis=1), row_hints)
    y_edges[0], y_edges[-1] = start_y, end_y
    regions, column_evidence = [], []
    for row_index, (_, assets) in enumerate(rows):
        y0, y1 = y_edges[row_index], y_edges[row_index + 1]
        row_mask = mask[y0:y1]
        column_hints = [asset["packing"]["cell_xywh"][0] / guide_w for asset in assets[1:]]
        edges, proof = partition(row_mask.sum(axis=0), column_hints)
        # Keep one measured invisible column after the last visible texel.
        # Preserve the remaining trailing canvas independently, without edits.
        visible_x = np.flatnonzero(row_mask.any(axis=0))
        content_end = min(sheet.width, int(visible_x[-1]) + 2)
        edges[-1] = content_end
        proof["measured_trailing_residual_start_x"] = content_end
        column_evidence.append(proof)
        for column, asset in enumerate(assets):
            regions.append({"id": asset["id"], "role": "object", "row": row_index, "column": column,
                            "integer_crop_xyxy_exclusive": [edges[column], y0, edges[column + 1], y1]})
        if content_end < sheet.width:
            regions.append({"id": "residual_row_{:02d}".format(row_index), "role": "nonvisible_residual_region",
                            "integer_crop_xyxy_exclusive": [content_end, y0, sheet.width, y1]})
    for name, box in (("residual_top", [0, 0, sheet.width, start_y]),
                      ("residual_bottom", [0, end_y, sheet.width, sheet.height])):
        if box[3] > box[1]:
            regions.append({"id": name, "role": "nonvisible_residual_region", "integer_crop_xyxy_exclusive": box})
    return regions, {"expected_objects_per_row": [len(items) for _, items in rows], "native_y_edges": y_edges,
                    "row_partition": row_evidence, "column_partitions_by_row": column_evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=BASE / "native-final/native.png")
    parser.add_argument("--receipt", type=Path, default=BASE / "native-final/receipt.json")
    parser.add_argument("--contract", type=Path, default=ROOT / "Tools/Building37/input-contract.json")
    parser.add_argument("--output", type=Path, default=BASE / "slices")
    parser.add_argument("--deps", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--check-normalization-only", action="store_true")
    parser.add_argument("--reuse-existing", action="store_true", help="Verify an already produced stage without saving/cropping it again")
    args = parser.parse_args()
    if args.deps:
        sys.path.insert(0, str(args.deps.resolve(strict=True)))
    import numpy as np
    from PIL import Image
    receipt, source, sheet = normalization_input(args, Image)
    if args.check_normalization_only:
        print(json.dumps({"status": "reused_actual_normalization", "receipt": str(args.receipt),
            "receipt_sha256": digest(args.receipt), "native_sha256": digest(args.native), "native_canvas_px": list(sheet.size),
            "producer": "Tools/Building33/native_normalize.py", "settings": receipt["settings"],
            "normalization_reexecuted": False}))
        return 0
    report_path = BASE / "technical-validation.json" if args.verify_only else args.output / "manifest.json"
    if args.reuse_existing and not report_path.is_file():
        raise FileNotFoundError("Actual existing stage report required: " + str(report_path))
    if not args.reuse_existing and (report_path.exists() or (not args.verify_only and args.output.exists() and any(args.output.iterdir()))):
        raise FileExistsError("Preserve existing slices/report; do not repeat or overwrite: " + str(report_path))
    failures, records, pending, evidence = [], [], [], {}
    coverage = np.zeros((sheet.height, sheet.width), dtype=np.uint8)
    try:
        regions, evidence = measured_regions(sheet, read(args.contract), np)
    except ValueError as error:
        regions = []
        failures.append({"code": "NO_SAFE_TRANSPARENT_PARTITION", "stage": "source_layout", "detail": str(error),
            "repair": "Preserve the input and inspect its declared layout; no arbitrary cut, resize or alpha cleanup"})
    for region in regions:
        box = region["integer_crop_xyxy_exclusive"]
        if any(type(value) is not int for value in box) or box[0] >= box[2] or box[1] >= box[3]:
            raise ValueError("Invalid integer crop: " + region["id"])
        coverage[box[1]:box[3], box[0]:box[2]] += 1
        crop = sheet.crop(box)
        pixels = np.asarray(crop)
        mask = pixels[:, :, 3] >= 26
        ys, xs = np.nonzero(mask)
        visible_count = len(xs)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if visible_count else None
        record = dict(region, canvas_px=list(crop.size), visible_alpha_gt_0p1_bbox_in_crop=bbox,
                      visible_alpha_pixels=int(visible_count), original_nonzero_alpha_pixels=int(np.count_nonzero(pixels[:, :, 3])))
        if (region["role"] == "object") != bool(visible_count):
            failures.append({"code": "VISIBLE_CONTENT_ROLE_MISMATCH", "stage": "source_layout", "id": region["id"]})
        path = (args.output / (region["id"] + ".png")).resolve()
        record["output"] = str(path)
        if args.verify_only or args.reuse_existing:
            if not path.is_file():
                failures.append({"code": "MISSING_CROP", "stage": "slice", "id": region["id"]})
            else:
                with Image.open(path) as actual:
                    exact = actual.mode == "RGBA" and actual.size == crop.size and actual.tobytes() == crop.tobytes()
                record.update(rgba_equals_exact_sheet_crop=exact, sha256=digest(path))
                if not exact:
                    failures.append({"code": "CROP_RGBA_CHANGED", "stage": "slice", "id": region["id"]})
        records.append(record)
        pending.append((path, crop, record))
    if regions and not np.all(coverage == 1):
        failures.append({"code": "CANONICAL_PARTITION_COVERAGE_FAILED", "stage": "slice",
                         "uncovered_pixels": int(np.count_nonzero(coverage == 0)), "overlap_pixels": int(np.count_nonzero(coverage > 1))})
    if args.verify_only:
        prior = read(args.output / "manifest.json")
        if prior.get("native_sha256") != digest(args.native) or prior.get("input_contract_sha256") != digest(args.contract) or [cell["integer_crop_xyxy_exclusive"] for cell in prior.get("cells", [])] != [cell["integer_crop_xyxy_exclusive"] for cell in records] or [cell.get("sha256") for cell in prior.get("cells", [])] != [cell.get("sha256") for cell in records]:
            failures.append({"code": "SLICE_PROVENANCE_CHANGED", "stage": "slice"})
    if args.reuse_existing:
        existing = read(report_path)
        if (existing.get("exit_code") != 0 or existing.get("failures") != []
                or existing.get("native_sha256") != digest(args.native)
                or existing.get("normalization_receipt_sha256") != digest(args.receipt)
                or existing.get("input_contract_sha256") != digest(args.contract)
                or [(cell.get("id"), cell.get("sha256"), cell.get("integer_crop_xyxy_exclusive")) for cell in existing.get("cells", [])]
                != [(cell.get("id"), cell.get("sha256"), cell.get("integer_crop_xyxy_exclusive")) for cell in records]):
            failures.append({"code": "EXISTING_STAGE_PROVENANCE_CHANGED", "stage": "cached_materials"})
    if not failures and not args.verify_only and not args.reuse_existing:
        args.output.mkdir(parents=True, exist_ok=True)
        for path, crop, record in pending:
            crop.save(path)
            record["sha256"] = digest(path)
    report = {"schema": "building37-common-sheet-slices/1", "mode": "verify" if args.verify_only else "slice",
        "scope": "Whole-sheet upstream-auto normalization reuse and exact integer-crop materials only",
        "native": str(args.native.resolve()), "native_sha256": digest(args.native), "native_canvas_px": list(sheet.size),
        "normalization_receipt": str(args.receipt.resolve()), "normalization_receipt_sha256": digest(args.receipt),
        "source": str(source), "source_sha256": digest(source), "input_contract_sha256": digest(args.contract),
        "grid": evidence, "alpha_policy": "Analysis A>=26 only. Every source RGBA byte, including faint alpha/background residuals, is preserved.",
        "observed_regions": {"objects": sum(r["role"] == "object" for r in records),
            "nonvisible_residual_regions": sum(r["role"] != "object" for r in records),
            "rgba_identical_to_source_crop": sum(r.get("rgba_equals_exact_sheet_crop", False) for r in records) if args.verify_only else None},
        "partition_area_px": sum(r["canvas_px"][0] * r["canvas_px"][1] for r in records), "sheet_area_px": sheet.width * sheet.height,
        "cells": records, "failures": failures, "exit_code": 2 if failures else 0,
        "limitations": ["Gutters and hints do not prove object semantic identity or design approval", "No feature-preservation claim for upstream normalization", "No physical-size or Unity integration completion"]}
    if not args.reuse_existing:
        write(report_path, report)
    print(json.dumps({"report": str(report_path), "objects": report["observed_regions"]["objects"],
                      "saved_regions": len(records), "failures": len(failures), "exit_code": report["exit_code"],
                      "reused_existing_result": args.reuse_existing, "material_production_reexecuted": not args.reuse_existing,
                      "current_failures": failures}))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
