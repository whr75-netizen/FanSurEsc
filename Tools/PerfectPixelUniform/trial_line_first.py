"""Prepare and inspect an unchanged legacy line-first engine trial; never resize assets."""
import argparse
import hashlib
import json
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA = "e4eb81a6bb53708a807e7eb182bfaa10bc39e37a5ed337c7913384323172d1ae"
SOURCE = ROOT / "Tools/PerfectPixelUniform/runs/20261003T092818576216Z-59a6e7b8655b4cf4a637cf98f68e32a7/source.png"
RUN = ROOT / "docs/artifacts/building37/Uniform04"
ENGINE = ROOT / "LocalOnly/PerfectPixelPalette_20260906"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def load_rgba(path):
    with Image.open(path) as image:
        if image.mode != "RGBA":
            raise ValueError(f"Explicit RGBA required: {path}")
        return np.array(image)


def prepare():
    data = SOURCE.read_bytes()
    if sha(data) != SOURCE_SHA:
        raise ValueError("The agreed actual source has changed; stop instead of substituting it.")
    with Image.open(BytesIO(data)) as image:
        if image.mode != "RGBA" or image.size != (1489, 1056):
            raise ValueError("Actual-source RGBA/size contract mismatch.")
        original = np.array(image)
    if RUN.exists():
        raise FileExistsError("Previous trials must not be overwritten or repeated.")
    RUN.mkdir(parents=True)
    prepared = original.copy()
    prepared[..., 3] = np.where(original[..., 3] >= 128, 255, 0).astype(np.uint8)
    prepared[prepared[..., 3] == 0] = 0
    Image.fromarray(prepared).save(RUN / "binary-alpha-source.png")
    config = {
        "source": "binary-alpha-source.png", "base_grid": [1489, 1056],
        "scale": "1.0", "preview_zoom": 1,
        "features": {
            "region_colors": {"enabled": True, "scope": {"kind": "all"},
                              "options": {"colors": 64, "iterations": 3}},
            "cell_sampling": {"enabled": True, "scope": {"kind": "all"},
                              "options": {"method": "source_regions", "coverage": .5,
                                          "color_edge_threshold": .08}},
            "line_normalization": {"enabled": True, "scope": {"kind": "all"},
                                   "options": {"mode": "line_first", "fill_source_guard": True}}
        },
        "notes": "Legacy line-first trial at source resolution, not automatic authored-grid recovery. Explicit alpha128 and 64-colour representative palette. Original and engine unchanged."
    }
    write_json(RUN / "config.json", config)
    receipt = {
        "schema": "legacy-line-first-preparation/1", "source_path": str(SOURCE),
        "source_file_sha256": sha(data), "source_array_sha256": sha(original.tobytes()),
        "prepared_array_sha256": sha(prepared.tobytes()), "size": [1489, 1056],
        "alpha_threshold": 128, "alpha_changed_pixels": int(np.count_nonzero(original[..., 3] != prepared[..., 3])),
        "discarded_nonzero_alpha_pixels": int(np.count_nonzero((original[..., 3] > 0) & (original[..., 3] < 128))),
        "opaque_pixels": int(np.count_nonzero(prepared[..., 3] == 255)),
        "source_visible_rgb_count": len(np.unique(original[original[..., 3] > 0, :3], axis=0)),
        "prepared_opaque_rgb_count": len(np.unique(prepared[prepared[..., 3] == 255, :3], axis=0)),
        "engine_path": str(ENGINE), "engine_changed": False, "resize": False,
        "limitation": "Alpha threshold changes edge coverage. This is a separate copy, not lossless restoration."
    }
    write_json(RUN / "preparation.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False))


def preview(original, output):
    # Same fixed crop as V3; never fed back into engine or Unity.
    box = (80, 70, 208, 198)
    panel = Image.new("RGB", (1032, 540), (30, 32, 35))
    draw = ImageDraw.Draw(panel)
    draw.text((8, 8), "ORIGINAL: same 128x128 crop, nearest 4x", fill="white")
    draw.text((524, 8), "LINE FIRST + 64 COLOURS: nearest 4x", fill="white")
    for x, array in ((0, original), (520, output)):
        crop = Image.fromarray(array).crop(box).resize((512, 512), Image.Resampling.NEAREST)
        panel.paste(crop, (x, 28), crop)
    panel.save(RUN / "comparison-crop-x4.png")


def execute():
    """One fixed external-engine process, observed independently of graph timeout."""
    if (RUN / "execution.json").exists() or (RUN / "engine").exists():
        raise FileExistsError("Do not re-execute a previous engine trial.")
    argv = [sys.executable, "-B", str(ENGINE / "trigger_cli.py"),
            "--config", str(RUN / "config.json"), "--output", str(RUN / "engine")]
    started = time.perf_counter()
    with (RUN / "engine-stdout.txt").open("x", encoding="utf-8") as out, (RUN / "engine-stderr.txt").open("x", encoding="utf-8") as err:
        process = subprocess.Popen(argv, cwd=ROOT, stdout=out, stderr=err)
        write_json(RUN / "execution-started.json", {"argv": argv, "pid": process.pid, "cwd": str(ROOT)})
        code = process.wait()
    record = {"schema": "legacy-line-first-process/1", "argv": argv, "cwd": str(ROOT),
              "pid": process.pid, "exit_code": code, "elapsed_seconds": time.perf_counter() - started,
              "stdout_sha256": sha((RUN / "engine-stdout.txt").read_bytes()),
              "stderr_sha256": sha((RUN / "engine-stderr.txt").read_bytes())}
    write_json(RUN / "execution.json", record)
    print(json.dumps(record, ensure_ascii=False))
    raise SystemExit(code)


def validate():
    execution = json.loads((RUN / "execution.json").read_text(encoding="utf-8"))
    assert execution["exit_code"] == 0
    assert execution["argv"][2] == str(ENGINE / "trigger_cli.py")
    assert execution["stdout_sha256"] == sha((RUN / "engine-stdout.txt").read_bytes())
    assert execution["stderr_sha256"] == sha((RUN / "engine-stderr.txt").read_bytes())
    prep = json.loads((RUN / "preparation.json").read_text(encoding="utf-8"))
    record = json.loads((RUN / "engine/settings_and_result.json").read_text(encoding="utf-8"))
    original = load_rgba(SOURCE)
    prepared = load_rgba(RUN / "binary-alpha-source.png")
    output = load_rgba(RUN / "engine/pixel_native.png")
    before_lines = load_rgba(RUN / "engine/before_lines_native.png")
    colours = load_rgba(RUN / "engine/colors_source.png")
    if sha(SOURCE.read_bytes()) != SOURCE_SHA or sha(original.tobytes()) != prep["source_array_sha256"]:
        raise AssertionError("Original input mutated.")
    if sha(prepared.tobytes()) != prep["prepared_array_sha256"]:
        raise AssertionError("Prepared input mutated.")
    assert output.shape == original.shape == prepared.shape == (1056, 1489, 4)
    expected_alpha = np.where(original[..., 3] >= 128, 255, 0).astype(np.uint8)
    np.testing.assert_array_equal(prepared[..., 3], expected_alpha)
    np.testing.assert_array_equal(output[..., 3], expected_alpha)
    for rel, digest in record["code_sha256"].items():
        assert sha((ENGINE / rel).read_bytes()) == digest, f"Legacy engine changed: {rel}"
        assert sha((RUN / "engine/code" / rel).read_bytes()) == digest
    source_colours = set(map(tuple, prepared[expected_alpha == 255, :3]))
    result_colours = set(map(tuple, output[expected_alpha == 255, :3]))
    assert 0 < len(result_colours) <= 64 and result_colours <= source_colours
    with np.load(RUN / "engine/processing_maps.npz", allow_pickle=False) as maps:
        lines = maps["geometry_fixed_line_mask"]
        line_xy = maps["geometry_fixed_line_source_xy"]
        collision = maps["geometry_collision_mask"]
        unresolved = maps["geometry_unresolved_mask"]
        owners = maps["geometry_target_owners"]
        labels = maps["geometry_source_labels"]
        sample_xy = maps["render_source_xy"]
        fallback = collision | unresolved
        ly, lx = np.nonzero(lines)
        xy = line_xy[ly, lx]
        assert len(xy) > 0, "Actual trial detected no fixed lines."
        np.testing.assert_array_equal(xy, np.column_stack((lx, ly)))
        np.testing.assert_array_equal(sample_xy[ly, lx], xy)
        np.testing.assert_array_equal(output[ly, lx], colours[xy[:, 1], xy[:, 0]])
        np.testing.assert_array_equal(output[fallback], before_lines[fallback])
        fill = (expected_alpha == 255) & ~lines & ~fallback & (owners >= 0)
        fy, fx = np.nonzero(fill)
        fxy = sample_xy[fy, fx]
        assert (fxy >= 0).all() and (fxy[:, 0] < 1489).all() and (fxy[:, 1] < 1056).all()
        np.testing.assert_array_equal(labels[fxy[:, 1], fxy[:, 0]], owners[fy, fx])
        np.testing.assert_array_equal(output[fy, fx], colours[fxy[:, 1], fxy[:, 0]])
        composition = record["result"]["features"]["line_normalization"]["composition"]
        assert int(fallback.sum()) == composition["integration_fallback_cells"]
        assert int(lines.sum()) == composition["fixed_line_cells"]
        counts = {"fixed_line_cells": int(lines.sum()), "collision_cells": int(collision.sum()),
                  "unresolved_cells": int(unresolved.sum()), "fallback_cells": int(fallback.sum()),
                  "verified_source_region_fill_cells": len(fy),
                  "fill_samples_moved_from_target_xy": int(np.count_nonzero(np.any(fxy != np.column_stack((fx, fy)), axis=1))),
                  "fixed_line_rgb_changed_from_source": int(np.count_nonzero(np.any(output[ly, lx, :3] != prepared[ly, lx, :3], axis=1)))}
    visible = expected_alpha == 255
    stats = {
        "source_visible_rgb": prep["source_visible_rgb_count"],
        "prepared_opaque_rgb": prep["prepared_opaque_rgb_count"], "output_opaque_rgb": len(result_colours),
        "palette_changed_pixels": int(np.count_nonzero(visible & np.any(prepared[..., :3] != before_lines[..., :3], axis=2))),
        "line_stage_additional_changed_pixels": int(np.count_nonzero(visible & np.any(before_lines[..., :3] != output[..., :3], axis=2))),
        "output_alpha_matches_prepared": True, "no_resize": True
    }
    report = {"schema": "legacy-line-first-validation/1", "passed": True,
              "source_sha256": SOURCE_SHA, "output_sha256": sha((RUN / "engine/pixel_native.png").read_bytes()),
              "checks": ["unchanged original/prepared/engine", "same canvas and explicit alpha128 mask",
                         "at most64 observed sourceRGB", "identity fixed-line projection and actual RGB",
                         "same source-region fill samples", "fallback accounted separately"],
              "counts": counts, "statistics": stats, "line_composition": composition,
              "not_verified": ["original authored pixel grid", "semantic feature retention", "ideal contour restoration", "design approval", "Unity display"]}
    write_json(RUN / "validation.json", report)
    preview(original, output)
    print(json.dumps({"passed": True, "counts": counts, "statistics": stats}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "execute", "validate"))
    args = parser.parse_args()
    {"prepare": prepare, "execute": execute, "validate": validate}[args.stage]()
