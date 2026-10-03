"""Check actual two-sample B36 display observations; never certify the whole scene."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/artifacts/building36"
SAMPLES = {"stock_shelf": "stock_shelf", "detail_clock": "detail_clock"}
CANONICAL_HASH = "b9dee0e6eb7f3183f70543e81c1c2467ca7b068781641134022417dc514711ea"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(path):
    item = Path(path)
    return item if item.is_absolute() else ROOT / item


def close(value, expected, tolerance=.01):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and abs(value - expected) <= tolerance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=BASE / "R3/report.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve the existing observation: " + str(args.output))
    failures, evidence = [], {}

    def fail(code, stage, detail):
        failures.append({"code": code, "stage": stage, "detail": detail})

    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read().strip()
            if raw:
                submitted = json.loads(raw)
                if resolve(submitted["readback_path"]).resolve() != resolve(args.report).resolve():
                    fail("READBACK_PATH_MISMATCH", "observation", submitted["readback_path"])
        paths = {"report": resolve(args.report), "manifest": BASE / "slices/manifest.json",
                 "import": BASE / "unity-import.json", "canonical": BASE / "native-final/native.png"}
        data = {key: read(path) for key, path in paths.items() if key != "canonical"}
        report, manifest, imported = data["report"], data["manifest"], data["import"]
        evidence["input_sha256"] = {str(path): sha(path) for path in paths.values()}
        if sha(paths["canonical"]) != CANONICAL_HASH or manifest["native_sha256"] != CANONICAL_HASH or imported["canonicalSheetHash"] != CANONICAL_HASH:
            fail("CANONICAL_CHANGED", "input", "Expected the preserved, already-normalized B36 sheet")
        objects = {item["id"]: item for item in manifest["cells"] if item["role"] == "object"}
        items = imported["items"]
        if len(objects) != 18 or len(items) != 18 or {item["id"] for item in items} != set(objects):
            fail("IMPORT_SET_CHANGED", "input", "Expected exactly eighteen canonical imports")
        if imported.get("exactNativeImports") is not True:
            fail("IMPORT_READBACK_FAILED", "input", "Existing Unity import did not preserve native texels")
        by_id = {item["id"]: item for item in items}
        for item in items:
            cell = objects[item["id"]]
            asset = resolve(item["asset"])
            if not (sha(resolve(cell["output"])) == sha(asset) == cell["sha256"] == item["sourceHash"] == item["importedHash"]):
                fail("SOURCE_PNG_CHANGED", "input", item["id"])
            with Image.open(asset) as image:
                dimensions = list(image.size)
                image.verify()
            if dimensions != cell["canvas_px"] or [item["width"], item["height"]] != dimensions or item.get("rgbaMismatches") != 0 or item.get("fullRect") is not True:
                fail("IMPORT_TEXELS_CHANGED", "input", item["id"])

        if report.get("scene") != "Assets/Scenes/GameMap1.unity" or report.get("playMode") is not True:
            fail("PLAY_OBSERVATION_MISSING", "observation", "Expected the actual GameMap1 Play Mode experiment")
        if not close(report.get("cameraPitch"), 30) or not close(report.get("cameraYaw"), 350):
            fail("CAMERA_BASIS_CHANGED", "projection", "Expected pitch30 / world yaw350 degrees")
        if not close(report.get("pixelScale"), 6) or not close(report.get("ppu"), imported["spritePpu"], .00001):
            fail("COMMON_DISPLAY_SCALE_CHANGED", "projection", "Expected shared q6 and imported Sprite PPU")
        samples = report.get("samples", [])
        if len(samples) != 2 or {item.get("id") for item in samples} != set(SAMPLES):
            fail("SAMPLE_SET_MISMATCH", "observation", "Expected source IDs stock_shelf and detail_clock exactly once")
        for sample in samples:
            sample_id = sample.get("id")
            if sample_id not in SAMPLES:
                continue
            expected = by_id[SAMPLES[sample_id]]
            if resolve(sample.get("textureAsset", "")).resolve() != resolve(expected["asset"]).resolve() or [sample.get("width"), sample.get("height")] != [expected["width"], expected["height"]]:
                fail("SAMPLE_SOURCE_CHANGED", "input", sample_id)
            for axis, target in (("screenU", (6, 0)), ("screenV", (0, 6))):
                measured = sample.get(axis)
                if not isinstance(measured, list) or len(measured) != 2 or any(not close(value, want) for value, want in zip(measured, target)):
                    fail("SCREEN_TEXEL_BASIS_INVALID", "projection", {"id": sample_id, "axis": axis, "measured": measured, "expected": target, "tolerance_px": .01})
            height = sample.get("maxLocalY")
            if (not isinstance(sample.get("opaqueTexels"), int) or isinstance(sample.get("opaqueTexels"), bool)
                    or sample["opaqueTexels"] <= 0 or not isinstance(height, (int, float))
                    or isinstance(height, bool) or not math.isfinite(height)):
                fail("GEOMETRY_OBSERVATION_MISSING", "geometry", sample_id)
            if type(sample.get("roofOverflowTexels")) is not int or sample["roofOverflowTexels"] != 0:
                fail("ROOF_OVERFLOW", "geometry", {"id": sample_id, "measured": sample.get("roofOverflowTexels"), "expected": 0})
        captures = {}
        for key in ("gameCapture", "overviewCapture"):
            path = resolve(report[key])
            with Image.open(path) as image:
                dimensions = list(image.size)
                if image.format != "PNG" or min(dimensions) <= 0:
                    raise ValueError(key + ": expected a nonempty PNG capture")
                image.verify()
            captures[key] = {"path": str(path), "sha256": sha(path), "dimensions_px": dimensions}
        if resolve(report["gameCapture"]).resolve() != (BASE / "R3/play-interior.png").resolve():
            fail("GAME_CAPTURE_PATH_MISMATCH", "observation", report["gameCapture"])
        evidence["captures"] = captures
        evidence["observed_samples"] = samples
    except (OSError, ValueError, KeyError, TypeError) as error:
        fail("MISSING_OR_INVALID_OBSERVATION", "observation", str(error))

    output = {"scope": "Representative two-sample technical experiment only",
              "fullSceneCompleted": False, "artApprovalClaimed": False,
              "unverified": ["All 26 scene bindings", "Wall and character occlusion", "Exterior roof visibility", "Design quality"],
              "exit_code": 2 if failures else 0, "failures": failures, "evidence": evidence}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))
    return output["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
