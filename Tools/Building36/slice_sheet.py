"""Split one automatically normalized 4x5 sheet using integer canvas crops only.

No resize, warp, alpha cleanup, individual normalization or target resolution.
The analysis mask uses the existing Unity clip threshold alpha > 0.1. Stored
RGBA is never changed, including subthreshold residuals in two blank cells.
Exit 2 blocks on unsafe visible boundaries, visible blank cells or mismatch.
Technical success is neither artistic acceptance nor completed Unity integration.
"""
import argparse
from itertools import product
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/artifacts/building36"
ALPHA_CUTOFF = 0.1
IDS = ["empty_counter", "left_shelf", "rear_shelf", "island_body_template",
       "stock_shelf", "fridge", "utility_bench", "cleaning_cabinet",
       "register", "appletray", "plant", "barrel", "crate", "detail_ledger",
       "detail_clock", "detail_poster", "detail_broom", "detail_bin", None, None]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def empty_bands(alpha, axis):
    length = alpha.width if axis == "x" else alpha.height
    runs, start = [], None
    for coordinate in range(length):
        box = (coordinate, 0, coordinate + 1, alpha.height) if axis == "x" else (0, coordinate, alpha.width, coordinate + 1)
        empty = alpha.crop(box).getbbox() is None
        if empty and start is None:
            start = coordinate
        if not empty and start is not None:
            runs.append([start, coordinate])
            start = None
    if start is not None:
        runs.append([start, length])
    return runs


def transparent_edges(alpha, axis, hints, min_fraction, max_fraction):
    length = alpha.width if axis == "x" else alpha.height
    bands = [b for b in empty_bands(alpha, axis) if b[0] > 0 and b[1] < length]
    choices = []
    for hint in hints:
        candidates = [(b, (b[0] + b[1]) // 2) for b in bands
                      if abs((b[0] + b[1]) / (2 * length) - hint) <= .12]
        if not candidates:
            raise ValueError("No fully transparent {} band near layout hint {}".format(axis, hint))
        choices.append(candidates)
    valid = []
    for combination in product(*choices):
        edges = [0] + [item[1] for item in combination] + [length]
        widths = [b - a for a, b in zip(edges, edges[1:])]
        if any(w < min_fraction * length or w > max_fraction * length for w in widths):
            continue
        # Prefer the widest measured gutters. Hints only disambiguate measured
        # empty bands; they can never authorize cutting a nontransparent line.
        score = (-sum(b[1] - b[0] for b, _ in combination),
                 sum(abs(edge / length - hint) for (_, edge), hint in zip(combination, hints)))
        valid.append((score, edges, [b for b, _ in combination]))
    if not valid:
        raise ValueError("No transparent partition satisfies declared count and cell-width limits on " + axis)
    _, edges, selected = min(valid, key=lambda item: item[0])
    return edges, {"available_internal_bands": bands, "selected_bands": selected, "hints": hints,
                   "min_partition_fraction": min_fraction, "max_partition_fraction": max_fraction}


def measured_cells(sheet):
    alpha = sheet.getchannel("A").point(lambda value: 255 if value / 255.0 > ALPHA_CUTOFF else 0)
    # Observed source row positions are search hints only. The actual cuts must
    # lie in fully transparent canonical rows, regardless of these estimates.
    ye, row_evidence = transparent_edges(alpha, "y", [355/1402, 680/1402, 922/1402, 1141/1402], .08, .37)
    rows, evidence = [], []
    for row in range(5):
        row_alpha = alpha.crop((0, ye[row], sheet.width, ye[row + 1]))
        if row < 4:
            xe, proof = transparent_edges(row_alpha, "x", [.25, .5, .75], .10, .42)
        else:
            # First two declared cells contain objects; the trailing two are
            # measured empty space, not invented crops through an object.
            xe, proof = transparent_edges(row_alpha, "x", [.25], .10, .90)
            bbox = row_alpha.getbbox()
            if bbox is None:
                raise ValueError("Last row has no objects")
            blank_start = max(round(sheet.width * .5), bbox[2] + 1)
            blank_middle = max(round(sheet.width * .75), blank_start + 1)
            if blank_start >= blank_middle or blank_middle >= sheet.width or blank_start - xe[1] > .42 * sheet.width:
                raise ValueError("Last-row occupied extent leaves no two declared empty cells")
            xe = [0, xe[1], blank_start, blank_middle, sheet.width]
            if row_alpha.crop((blank_start, 0, sheet.width, row_alpha.height)).getbbox() is not None:
                raise ValueError("Trailing blank cells contain visible alpha above the Unity clip threshold")
            proof["measured_trailing_empty_from_x"] = bbox[2]
        rows.append(xe)
        evidence.append(proof)
    return ye, rows, {"row_partition": row_evidence, "column_partitions_by_row": evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=BASE / "native/native.png")
    parser.add_argument("--receipt", type=Path, default=BASE / "native/receipt.json")
    parser.add_argument("--output", type=Path, default=BASE / "slices")
    parser.add_argument("--deps", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.deps:
        sys.path.insert(0, str(args.deps.resolve(strict=True)))
    from PIL import Image

    report_path = BASE / "technical-validation.json" if args.verify_only else args.output / "manifest.json"
    if report_path.exists():
        raise FileExistsError("Preserve the prior report; inspect its cause before a new run: " + str(report_path))
    if not args.verify_only and args.output.exists() and any(args.output.iterdir()):
        raise FileExistsError("Refusing to overwrite existing sheet slices")
    failures, records, crops = [], [], []
    normalization = load(args.receipt)
    with Image.open(args.native) as image:
        if image.mode != "RGBA":
            raise ValueError("Expected unchanged normalized RGBA canvas")
        sheet = image.copy()
    sheet_visible = sheet.getchannel("A").point(lambda value: 255 if value / 255.0 > ALPHA_CUTOFF else 0)
    if normalization.get("status") != "normalized" or digest(args.native) != normalization.get("output_sha256"):
        failures.append({"code": "NORMALIZED_SOURCE_MISMATCH", "stage": "normalization"})
    if list(sheet.size) != normalization.get("output_dimensions"):
        failures.append({"code": "NORMALIZED_CANVAS_MISMATCH", "stage": "normalization"})
    source = Path(normalization["source_path"])
    if digest(source) != normalization.get("source_sha256"):
        failures.append({"code": "GENERATED_SOURCE_CHANGED", "stage": "source"})
    try:
        ye, row_x_edges, partition_evidence = measured_cells(sheet)
    except ValueError as error:
        ye, row_x_edges, partition_evidence = [], [], {"error": str(error)}
        failures.append({"code": "NO_SAFE_TRANSPARENT_PARTITION", "stage": "source", "detail": str(error),
                         "repair": "Inspect source layout; no inferred boundary, resize or alpha cleanup is permitted"})
    for index, asset_id in enumerate(IDS if row_x_edges else []):
        row, column = divmod(index, 4)
        xe = row_x_edges[row]
        box = [xe[column], ye[row], xe[column + 1], ye[row + 1]]
        crop = sheet.crop(box)
        original_alpha = crop.getchannel("A")
        alpha = original_alpha.point(lambda value: 255 if value / 255.0 > ALPHA_CUTOFF else 0)
        bbox = alpha.getbbox()
        visible_count = sum(1 for value in alpha.getdata() if value > 0)
        nonzero_count = sum(1 for value in original_alpha.getdata() if value > 0)
        contact = []
        if bbox:
            if bbox[0] == 0: contact.append("left")
            if bbox[1] == 0: contact.append("top")
            if bbox[2] == crop.width: contact.append("right")
            if bbox[3] == crop.height: contact.append("bottom")
        # A one-pixel invisible gutter can belong to just one adjacent crop.
        # A touching visible edge is safe when the adjacent canonical line is
        # invisible. At the sheet perimeter there is no such separation proof.
        neighbor_boxes = {"left": (box[0]-1, box[1], box[0], box[3]),
                          "right": (box[2], box[1], box[2]+1, box[3]),
                          "top": (box[0], box[1]-1, box[2], box[1]),
                          "bottom": (box[0], box[3], box[2], box[3]+1)}
        unsafe = []
        for side in contact:
            neighbor = neighbor_boxes[side]
            outside = neighbor[0] < 0 or neighbor[1] < 0 or neighbor[2] > sheet.width or neighbor[3] > sheet.height
            if outside or sheet_visible.crop(neighbor).getbbox() is not None:
                unsafe.append(side)
        record = {"index": index, "row": row, "column": column, "id": asset_id,
                  "integer_crop_xyxy_exclusive": box, "canvas_px": list(crop.size),
                  "visible_alpha_gt_0p1_bbox_in_crop": list(bbox) if bbox else None,
                  "visible_alpha_pixels": visible_count, "original_nonzero_alpha_pixels": nonzero_count,
                  "subthreshold_nonzero_alpha_pixels": nonzero_count - visible_count,
                  "visible_boundary_contacts": contact, "unsafe_visible_boundary_contacts": unsafe,
                  "role": "object" if asset_id else "nonvisible_residual_region"}
        if unsafe:
            failures.append({"code": "VISIBLE_ALPHA_CROSSES_CELL_BOUNDARY", "stage": "source", "cell": index,
                             "sides": unsafe, "repair": "Correct source placement; do not conceal clipping or resize"})
        if asset_id is None and visible_count:
            failures.append({"code": "DECLARED_BLANK_CELL_VISIBLE", "stage": "source", "cell": index, "pixels": visible_count})
        if asset_id is not None and not visible_count:
            failures.append({"code": "DECLARED_OBJECT_CELL_EMPTY", "stage": "source", "cell": index})
        filename = asset_id if asset_id else "residual_blank_{:02d}".format(index - 17)
        output = args.output / (filename + ".png")
        record["output"] = str(output)
        if args.verify_only:
            if not output.is_file():
                failures.append({"code": "MISSING_CROP", "stage": "slice", "cell": index})
            else:
                with Image.open(output) as actual:
                    equal = actual.mode == "RGBA" and actual.size == crop.size and actual.tobytes() == crop.tobytes()
                record["rgba_equals_exact_sheet_crop"] = equal
                record["sha256"] = digest(output)
                if not equal:
                    failures.append({"code": "CROP_RGBA_CHANGED", "stage": "slice", "cell": index})
        crops.append((output, crop, record))
        records.append(record)
    if not failures and not args.verify_only:
        args.output.mkdir(parents=True, exist_ok=True)
        for output, crop, record in crops:
            crop.save(output)
            record["sha256"] = digest(output)
    report = {"schema": "building36-common-sheet-slices/1", "mode": "verify" if args.verify_only else "slice",
              "scope": "Common-sheet normalization and integer-crop material pipeline only",
              "native": str(args.native), "native_sha256": digest(args.native), "native_canvas_px": list(sheet.size),
              "normalization_receipt": str(args.receipt), "normalization_receipt_sha256": digest(args.receipt),
              "source": str(source), "source_sha256": digest(source),
              "grid": {"columns": 4, "rows": 5, "expected_objects_per_row": [4, 4, 4, 4, 2],
                       "native_x_edges_by_row": row_x_edges, "native_y_edges": ye,
                       "mapping": "Measured canonical bands invisible under existing Unity alpha clip >0.1; no equal-row assumption or pixel transformation",
                       "partition_evidence": partition_evidence},
              "alpha_policy": "Analysis only: alpha/255 > 0.1 (A>=26), matching existing Unity shader clip. All original RGBA including subthreshold alpha is saved unchanged",
              "expected_saved_regions": {"objects": 18, "nonvisible_residual_regions": 2},
              "observed_regions": {"objects": sum(r["role"] == "object" for r in records),
                                   "nonvisible_residual_regions": sum(r["role"] == "nonvisible_residual_region" for r in records),
                                   "rgba_identical_to_source_crop": sum(r.get("rgba_equals_exact_sheet_crop", False) for r in records) if args.verify_only else None},
              "partition_area_px": sum(r["canvas_px"][0] * r["canvas_px"][1] for r in records),
              "sheet_area_px": sheet.width * sheet.height,
              "cells": records, "failures": failures, "exit_code": 2 if failures else 0,
              "limitations": ["No artistic acceptance or common visual style guarantee", "No 3D size recovery or Unity integration",
                              "Integer display magnification is permitted; no display-size equality test is imposed",
                              "Boundary contact detects clipping risk, not the semantic identity of objects in cells"]}
    save(report_path, report)
    print(json.dumps({"report": str(report_path), "failures": len(failures), "exit_code": report["exit_code"]}))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
