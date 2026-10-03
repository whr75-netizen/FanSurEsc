"""Validate actual two-sample ray-plane display; do not certify all 26 bindings."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/artifacts/building36"
R4 = BASE / "R4"
CANONICAL_HASH = "b9dee0e6eb7f3183f70543e81c1c2467ca7b068781641134022417dc514711ea"
SAMPLE_IDS = {"stock_shelf", "detail_clock"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(path):
    item = Path(path)
    return item if item.is_absolute() else ROOT / item


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def close(value, expected, tolerance=.01):
    return finite(value) and finite(expected) and abs(value - expected) <= tolerance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve the existing gate: " + str(args.output))
    failures, evidence = [], {}

    def fail(code, stage, detail):
        failures.append({"code": code, "stage": stage, "detail": detail})

    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read().strip()
            if raw and resolve(json.loads(raw)["readback_path"]).resolve() != (R4 / "experiment.json").resolve():
                fail("READBACK_PATH_MISMATCH", "observation", "Expected actual R4 experiment.json")
        paths = {"plan": R4 / "support-plan.json", "experiment": R4 / "experiment.json",
                 "manifest": BASE / "slices/manifest.json", "import": BASE / "unity-import.json",
                 "canonical": BASE / "native-final/native.png",
                 "producer": ROOT / "Assets/Editor/NativeSheetDisplay36.cs"}
        data = {key: read(path) for key, path in paths.items() if key not in ("canonical", "producer")}
        evidence["input_sha256"] = {str(path): sha(path) for path in paths.values()}
        plan, report, manifest, imported = (data[key] for key in ("plan", "experiment", "manifest", "import"))
        if sha(paths["canonical"]) != CANONICAL_HASH or manifest["native_sha256"] != CANONICAL_HASH or imported["canonicalSheetHash"] != CANONICAL_HASH or plan.get("canonicalHash") != CANONICAL_HASH:
            fail("CANONICAL_CHANGED", "input", "Use the preserved normalized sheet, without another normalization")
        objects = {cell["id"]: cell for cell in manifest["cells"] if cell["role"] == "object"}
        items = imported["items"]
        if len(objects) != 18 or len(items) != 18 or {item["id"] for item in items} != set(objects) or imported.get("exactNativeImports") is not True:
            fail("IMPORT_SET_CHANGED", "input", "Expected eighteen previously verified canonical imports")
        by_id = {item["id"]: item for item in items}
        for item in items:
            cell = objects[item["id"]]
            asset = resolve(item["asset"])
            if not (sha(resolve(cell["output"])) == sha(asset) == cell["sha256"] == item["sourceHash"] == item["importedHash"]):
                fail("SOURCE_PNG_CHANGED", "input", item["id"])
            with Image.open(asset) as image:
                dimensions = list(image.size)
                image.verify()
            if dimensions != cell["canvas_px"] or [item["width"], item["height"]] != dimensions or item.get("rgbaMismatches") != 0:
                fail("IMPORT_TEXELS_CHANGED", "input", item["id"])

        q = plan.get("displayMultiplier")
        if type(q) is not int or not 1 <= q <= 6:
            fail("INVALID_SHARED_DENSITY", "plan", q)
            q = 1  # Continue collecting errors; this default never creates a pass.
        camera_ppu = imported["cameraGridPpu"]
        if not close(plan.get("ppu"), camera_ppu / q, .00001) or plan.get("importedRgbaMismatches") != 0:
            fail("PLAN_SOURCE_OR_DENSITY_MISMATCH", "plan", "Expected unchanged RGBA and ppu=cameraGridPpu/q")
        expected_bindings = {}
        for path in (ROOT / "docs/artifacts/building35/placement.json", ROOT / "docs/artifacts/building35/details/placement.json"):
            evidence["input_sha256"][str(path)] = sha(path)
            expected_bindings.update({item["id"]: item.get("asset_variant") or item["asset"] for item in read(path)["instances"]})
        bindings = plan.get("bindings", [])
        if len(bindings) != 26 or {item.get("instance"): item.get("asset") for item in bindings} != expected_bindings:
            fail("PLAN_BINDING_SET_CHANGED", "plan", "Expected the preserved 26 placement identities and source IDs")
        for binding in bindings:
            if (not finite(binding.get("minY")) or not finite(binding.get("maxY"))
                    or binding["minY"] < -.0001 or binding["maxY"] > plan["roofHeight"] + .0001):
                fail("PLAN_HEIGHT_OUTSIDE_HOST", "plan", binding.get("instance"))
        if report.get("scene") != "Assets/Scenes/GameMap1.unity" or plan.get("scene") != report.get("scene") or report.get("playMode") is not True:
            fail("PLAY_OBSERVATION_MISSING", "observation", "Expected actual GameMap1 Play Mode")
        if not close(report.get("cameraPitch"), 30) or not close(report.get("cameraYaw"), 350):
            fail("CAMERA_BASIS_CHANGED", "projection", "Expected pitch30 / world yaw350")
        if not close(report.get("ppu"), plan.get("ppu"), .00001):
            fail("EXPERIMENT_DENSITY_CHANGED", "projection", "Actual experiment PPU differs from the fixed support plan")
        scale = report.get("pixelScale")
        if not finite(scale) or scale < 1 or not close(scale, round(scale)) or not close(scale / q, round(scale / q)) or round(scale / q) < 1:
            fail("NONINTEGER_SCREEN_SCALE", "projection", {"measured": scale, "shared_q": q})
        samples = report.get("samples", [])
        if len(samples) != 2 or {sample.get("id") for sample in samples} != SAMPLE_IDS:
            fail("SAMPLE_SET_CHANGED", "observation", "Expected stock_shelf and detail_clock exactly once")
        for sample in samples:
            sample_id = sample.get("id")
            if sample_id not in SAMPLE_IDS:
                continue
            expected = by_id[sample_id]
            if resolve(sample.get("textureAsset", "")).resolve() != resolve(expected["asset"]).resolve() or [sample.get("width"), sample.get("height")] != [expected["width"], expected["height"]]:
                fail("SAMPLE_SOURCE_CHANGED", "input", sample_id)
            for axis, target in (("screenU", (scale, 0)), ("screenV", (0, scale))):
                actual = sample.get(axis)
                if not isinstance(actual, list) or len(actual) != 2 or any(not close(value, want) for value, want in zip(actual, target)):
                    fail("SCREEN_TEXEL_BASIS_INVALID", "projection", {"id": sample_id, "axis": axis, "measured": actual, "expected": target, "tolerance_px": .01})
            if type(sample.get("opaqueTexels")) is not int or sample["opaqueTexels"] <= 0 or not finite(sample.get("maxLocalY")):
                fail("GEOMETRY_OBSERVATION_MISSING", "geometry", sample_id)
            if type(sample.get("roofOverflowTexels")) is not int or sample["roofOverflowTexels"] != 0:
                fail("ROOF_OVERFLOW", "geometry", {"id": sample_id, "measured": sample.get("roofOverflowTexels"), "expected": 0})
        captures = {}
        for key, filename in (("gameCapture", "play-interior.png"), ("overviewCapture", "overview-interior.png")):
            path = resolve(report[key])
            if path.resolve() != (R4 / filename).resolve():
                fail("CAPTURE_PATH_MISMATCH", "observation", {"key": key, "path": str(path)})
            with Image.open(path) as image:
                dimensions = list(image.size)
                if image.format != "PNG" or min(dimensions) <= 0:
                    raise ValueError(key + ": expected a nonempty PNG capture")
                image.verify()
            captures[key] = {"path": str(path), "sha256": sha(path), "dimensions_px": dimensions}
        evidence.update({"selected_q": q, "actual_screen_scale": scale, "observed_samples": samples, "captures": captures})
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError) as error:
        fail("MISSING_OR_INVALID_OBSERVATION", "observation", str(error))

    output = {"scope": "R4 representative two-sample ray-plane technical experiment only",
              "fullSceneCompleted": False, "artApprovalClaimed": False,
              "unverified": ["All 26 actual bindings", "Wall and character occlusion", "Exterior roof visibility", "Object physical proportions and support semantics", "Design quality"],
              "exit_code": 2 if failures else 0, "failures": failures, "evidence": evidence}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))
    return output["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
