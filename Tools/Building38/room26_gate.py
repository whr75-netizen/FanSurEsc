"""N26 actual-Play gate for separate room lamps and the preserved local mover.

The observer writes baseline.json, play/receipt.json, final.json and the seven
PNG captures under --output. This gate measures their pixels and re-hashes the
frozen art; it does not create observations or declare aesthetic approval.
"""

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "docs/artifacts/building39/room26"
WORLD_TOLERANCE = 1e-5
LINEAR_TOLERANCE = 1 / 255
SCREEN_TOLERANCE = .001
EXPECTED_FILL = .198
FLOOR_ROIS = ((200, 400, 400, 580), (720, 850, 350, 700))
IMAGE_NAMES = (
    "all-off.png", "lamps-only.png", "moving-only.png", "both-on.png",
    "lamps-no-shadows.png", "gpu-room-fill.png", "gpu-room-fill-off.png",
)


def linear(rgb):
    """Decode the existing 8-bit sRGB capture path to linear RGB."""
    value = np.asarray(rgb, dtype=np.float64) / 255
    return np.where(value <= .04045, value / 12.92,
                    ((value + .055) / 1.055) ** 2.4)


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def near(value, expected, tolerance):
    return finite_number(value) and abs(value - expected) <= tolerance


def preserved(before, after):
    """Compare recorded values, allowing only the N26 float32 world tolerance."""
    if isinstance(before, dict):
        return isinstance(after, dict) and all(
            key in after and preserved(value, after[key]) for key, value in before.items())
    if isinstance(before, list):
        return isinstance(after, list) and len(before) == len(after) and all(
            preserved(a, b) for a, b in zip(before, after))
    if finite_number(before):
        return near(after, before, WORLD_TOLERANCE)
    return type(before) is type(after) and before == after


def changed_pixels(first, second):
    return int(np.any(first != second, axis=-1).sum())


def floor_grid_check(pixels, bounds):
    """Use the audited light24 floor patches and their fixed (0, 1) phase."""
    x0, x1, y0, y1 = bounds
    height, width = pixels.shape[:2]
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError(f"Audited floor ROI {bounds} is outside {width}x{height}")
    xs = np.arange(x0 + (0 - x0) % 2, x1 - 1, 2)
    ys = np.arange(y0 + (1 - y0) % 2, y1 - 1, 2)
    blocks = np.stack([pixels[ys[:, None] + dy, xs[None, :] + dx]
                       for dy in range(2) for dx in range(2)], axis=2)
    mismatch = int(np.any(blocks != blocks[:, :, :1, :], axis=(2, 3)).sum())
    return {"boundsXY": list(bounds), "phaseXY": [0, 1],
            "blockCount": int(len(xs) * len(ys)), "mismatchedBlocks": mismatch,
            "distinctRGB": int(len(np.unique(blocks[:, :, 0, :].reshape(-1, 3), axis=0)))}


class Gate:
    def __init__(self, output):
        self.output = output
        self.checks = []
        self.metrics = {}

    def check(self, name, passed, detail=None):
        record = {"name": name, "passed": bool(passed)}
        if detail is not None:
            record["detail"] = detail
        self.checks.append(record)
        return record["passed"]

    def read_json(self, relative):
        def reject_nonfinite(value):
            raise ValueError(f"{relative} contains nonfinite JSON number {value}")

        value = json.loads((self.output / relative).read_text(encoding="utf-8-sig"),
                           parse_constant=reject_nonfinite)
        if not isinstance(value, dict):
            raise ValueError(f"{relative} must be a JSON object")
        return value

    def run(self):
        baseline = self.read_json("baseline.json")
        receipt = self.read_json("play/receipt.json")
        final = self.read_json("final.json")
        self.check("actualPlay", receipt.get("actualPlay") is True)
        self.check("samePlayer", receipt.get("samePlayer") is True)
        self.check("sameCamera", receipt.get("sameCamera") is True)
        self.check("nativePixelsOnScreen", near(receipt.get("nativePixelsOnScreen"), 2,
                                                SCREEN_TOLERANCE))
        self.check("shaderErrors", receipt.get("shaderErrors") == 0
                   and not isinstance(receipt.get("shaderErrors"), bool))
        self.check("roomLampCountPlay", receipt.get("roomLampCount") == 2)
        self.check("roomLampCountEdit", final.get("roomLampCount") == 2)
        self.check("pairedDirectLightCount", final.get("directLightCount") == 2)
        self.check("directPairsValidPlay", receipt.get("directPairsValid") is True)
        self.check("directPairsValidEdit", final.get("directPairsValid") is True)
        self.check("editMode", final.get("editPlaying") is False)
        self.check("sceneClean", final.get("sceneDirty") is False)
        self.check("sceneSaved", final.get("sceneSaved") is True)
        self.check("geometryPreservedPlay", receipt.get("geometryPreserved") is True)
        self.check("geometryPreservedEdit", final.get("geometryPreserved") is True)
        self.check("movingPreservedPlay", receipt.get("movingPreserved") is True)
        self.check("movingPreservedEdit", final.get("movingPreserved") is True)
        self.check("roomFillLinear", near(receipt.get("roomFillLinear"), EXPECTED_FILL,
                                          LINEAR_TOLERANCE))
        self.check("insideFarFillLinear", near(receipt.get("insideFarFillLinear"), EXPECTED_FILL,
                                               LINEAR_TOLERANCE))
        self.check("outsideFillLinear", near(receipt.get("outsideFillLinear"), 0,
                                             WORLD_TOLERANCE))
        self.check("pixelOrigin", receipt.get("pixelOrigin") == "top-left")

        mover = baseline.get("moving", {})
        self.check("movingBaselinePresent", isinstance(mover, dict) and bool(mover))
        if not isinstance(mover, dict):
            mover = {}
        self.check("movingWhite", isinstance(mover.get("color"), dict) and all(
            near(mover["color"].get(channel), 1, WORLD_TOLERANCE) for channel in "rgba"))
        self.check("movingIntensity", near(mover.get("intensity"), .4, WORLD_TOLERANCE))
        self.check("movingRadius", near(mover.get("radius"), 5, WORLD_TOLERANCE))
        self.check("movingSurfaceBands", mover.get("surfaceBands") == 3)
        self.check("movingLocalRole", mover.get("role") == 0 and not isinstance(mover.get("role"), bool))
        self.check("movingNativeCellSize", finite_number(mover.get("worldCellSize"))
                   and mover["worldCellSize"] > 0)
        for label, record in (("Play", receipt), ("Edit", final)):
            self.check("movingValuesPreserved" + label,
                       bool(mover) and isinstance(record.get("moving"), dict)
                       and preserved(mover, record["moving"]))
        self.metrics["movingBaseline"] = mover

        geometry = baseline.get("geometry")
        valid_geometry = isinstance(geometry, list) and bool(geometry) and all(
            isinstance(item, dict) and isinstance(item.get("path"), str)
            and all(key in item for key in ("mesh", "position", "rotation", "scale"))
            for item in geometry)
        if valid_geometry:
            valid_geometry = len({item["path"] for item in geometry}) == len(geometry)
        self.check("geometryBaselinePresent", valid_geometry)
        self.metrics["geometryBaselineCount"] = len(geometry) if isinstance(geometry, list) else 0
        # The Unity observer owns geometry equality; compare raw records too if
        # supplied, without requiring a new parallel observation mechanism.
        for label, record in (("Play", receipt), ("Edit", final)):
            if "geometry" in record:
                self.check("geometryRecordsPreserved" + label,
                           valid_geometry and preserved(geometry, record["geometry"]))

        hashes = baseline.get("sourceHashes")
        self.check("sourceHashCoverage193", isinstance(hashes, dict) and len(hashes) >= 193)
        changed_art = []
        if isinstance(hashes, dict):
            for relative, expected in hashes.items():
                if not isinstance(relative, str) or not isinstance(expected, str) or not re.fullmatch(
                        r"[0-9a-fA-F]{64}", expected):
                    changed_art.append({"path": str(relative), "reason": "invalid hash record"})
                    continue
                path = (ROOT / relative).resolve()
                try:
                    path.relative_to(ROOT.resolve())
                except ValueError:
                    changed_art.append({"path": relative, "reason": "outside project"})
                    continue
                if not path.is_file():
                    changed_art.append({"path": relative, "reason": "missing source"})
                elif hashlib.sha256(path.read_bytes()).hexdigest() != expected.lower():
                    changed_art.append({"path": relative, "reason": "hash changed"})
        self.check("sourceArtHashesPreserved", isinstance(hashes, dict) and bool(hashes)
                   and not changed_art, changed_art)
        self.metrics["sourceArtFilesPreserved"] = len(hashes) - len(changed_art) if isinstance(hashes, dict) else 0

        images = {}
        dimensions = {}
        for name in IMAGE_NAMES:
            with Image.open(self.output / "play" / name) as capture:
                if capture.format != "PNG":
                    raise ValueError(f"{name} is not a PNG capture")
                images[name] = np.asarray(capture.convert("RGB"), dtype=np.uint8)
                dimensions[name] = list(capture.size)
        self.metrics["imageDimensions"] = dimensions
        if not self.check("identicalImageDimensions", len({tuple(value) for value in dimensions.values()}) == 1):
            return

        off = images["all-off.png"]
        lamps = images["lamps-only.png"]
        moving = images["moving-only.png"]
        both = images["both-on.png"]
        shadow = images["lamps-no-shadows.png"]
        changes = {"lampsOnlyVsAllOff": changed_pixels(lamps, off),
                   "movingOnlyVsAllOff": changed_pixels(moving, off),
                   "bothVsLampsOnly": changed_pixels(both, lamps),
                   "bothVsMovingOnly": changed_pixels(both, moving),
                   "shadowsOnVsOff": changed_pixels(lamps, shadow)}
        self.metrics["changedPixels"] = changes
        self.check("lampsActualPixelChange", changes["lampsOnlyVsAllOff"] > 1000)
        self.check("movingActualPixelChange", changes["movingOnlyVsAllOff"] > 1000)
        self.check("bothSourcesVisible", changes["bothVsLampsOnly"] > 0
                   and changes["bothVsMovingOnly"] > 0)
        self.check("shadowActualPixelChange", changes["shadowsOnVsOff"] > 0)
        self.check("shadowReceiptPixelChange", finite_number(receipt.get("shadowChangedPixels"))
                   and receipt["shadowChangedPixels"] > 0)

        fill = images["gpu-room-fill.png"]
        fill_off = images["gpu-room-fill-off.png"]
        fill_linear = linear(fill)
        neutral = np.ptp(fill.astype(np.int16), axis=-1) <= 1
        target = np.max(np.abs(fill_linear - EXPECTED_FILL), axis=-1) <= LINEAR_TOLERANCE
        target_count = int((neutral & target).sum())
        self.metrics["gpuWhiteTargetPixels"] = target_count
        self.check("gpuWhiteRoomFill", target_count >= 100)

        probes = receipt.get("probes")
        self.check("worldPixelProbesPresent", isinstance(probes, list) and bool(probes))
        probe_results = []
        known_inside = []
        far_inside = []
        if isinstance(probes, list):
            height, width = fill.shape[:2]
            for index, probe in enumerate(probes):
                if not isinstance(probe, dict):
                    self.check(f"probeRecord{index}", False)
                    continue
                point = probe.get("pixel")
                world = probe.get("world")
                valid = (isinstance(point, list) and len(point) == 2
                         and all(finite_number(value) for value in point)
                         and all(value == int(value) for value in point)
                         and isinstance(world, list) and len(world) == 3
                         and all(finite_number(value) for value in world)
                         and isinstance(probe.get("inside"), bool)
                         and isinstance(probe.get("far"), bool))
                if valid:
                    x, y = map(int, point)
                    valid = 0 <= x < width and 0 <= y < height
                self.check(f"probeRecord{index}", valid)
                if not valid:
                    continue
                eligible = probe.get("occluded") is not True and probe.get("visibleNative") is not False
                on_rgb = fill[y, x]
                off_rgb = fill_off[y, x]
                white_target = bool(neutral[y, x] and target[y, x])
                black_off = bool(np.max(off_rgb) <= 1)
                detail = {"index": index, "world": world, "pixel": [x, y],
                          "inside": probe.get("inside") is True,
                          "far": probe.get("far") is True, "eligibleNative": eligible,
                          "onRGB": on_rgb.tolist(), "offRGB": off_rgb.tolist(),
                          "onLinearRGB": fill_linear[y, x].tolist(),
                          "whiteTarget": white_target, "offBlack": black_off}
                probe_results.append(detail)
                if eligible and probe.get("inside") is True and white_target:
                    known_inside.append(detail)
                    if probe.get("far") is True:
                        far_inside.append(detail)
                # A world-plane projection can be covered by another surface.
                # Require the target on observed native points, rather than
                # treating every projected point as an unobstructed floor hit.
                if eligible and probe.get("inside") is False:
                    self.check(f"outsideGpuProbe{index}", np.max(on_rgb) <= 1)
        self.metrics["gpuProbes"] = probe_results
        self.metrics["insideWhiteTargetProbes"] = len(known_inside)
        self.metrics["farWhiteTargetProbes"] = len(far_inside)
        self.check("knownInteriorNativeFill", bool(known_inside))
        self.check("knownFarInteriorNativeFill", bool(far_inside))
        self.check("knownInteriorFillOffBlack", bool(known_inside)
                   and all(item["offBlack"] for item in known_inside))

        grid_checks = []
        for index, bounds in enumerate(FLOOR_ROIS):
            result = floor_grid_check(fill, bounds)
            grid_checks.append(result)
            self.check(f"roomFillFloorNativeGrid{index}", result["mismatchedBlocks"] == 0, result)
        self.metrics["floorGridChecks"] = grid_checks
        # Room fill is deliberately uniform. A distinct-colour boundary is not
        # required in these patches, and final busy frames are not grid-tested.

    def result(self):
        return {"success": bool(self.checks) and all(item["passed"] for item in self.checks),
                "contract": "Tools/PerfectPixelUniform/BUILDING16.md N26",
                "checks": self.checks, **self.metrics,
                "tolerances": {"world": WORLD_TOLERANCE, "linearRGB": LINEAR_TOLERANCE,
                               "screenPixels": SCREEN_TOLERANCE},
                "scope": "Actual Play receipt, PNG differences, GPU room-only fill probes and two audited floor ROIs; source hashes are measured directly. Outside-fill CPU receipt is separate from visible native GPU probes. No whole-frame black, final-frame grid, aesthetic, input or build approval."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="N26 observation directory (default: docs/artifacts/building39/room26)")
    args = parser.parse_args(argv)
    gate = Gate(args.output.resolve())
    try:
        gate.run()
    except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
        gate.check("observationReadable", False, f"{type(error).__name__}: {error}")
    result = gate.result()
    validation = gate.output / "validation.json"
    try:
        validation.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    except (OSError, ValueError) as error:
        result["success"] = False
        result["validationWriteError"] = f"{type(error).__name__}: {error}"
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
