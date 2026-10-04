"""N28 shared-world-offset alignment gate with the unchanged N26 Play gate.

Consumes actual Unity fixture, integration and Play observations. Full mode
also compares the frozen N27 baselines and hashes their 512 source files.
Writes validation28.json only; passing is technical evidence, not art approval.
"""

import argparse
import hashlib
import itertools
import json
import math
import re
import sys
from pathlib import Path

import room26_gate


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "docs/artifacts/building39/shadow28"
N27_OUTPUT = ROOT / "docs/artifacts/building39/light27"
PHASES = ((.17, -.23), (-.31, .41))
PIXEL_SCALES = (2, 4)
EXPECTED_CASES = set(itertools.product(range(len(PHASES)), PIXEL_SCALES))
PHASE_TOLERANCE = 1e-6
PROJECTION_TOLERANCE = .02
PAIR_TOLERANCE = 1e-6
EXPECTED_PAIRS = 44
REQUIRED_CODE_PATHS = (
    "Assets/Shaders/World/NativePaletteSurface16.shader",
    "Assets/Shaders/World/NativeShadow28.shader",
    "Assets/Scripts/WorldGeneration/NativeSurfaceGridAlignment.cs",
    "Assets/Editor/NativeShadow28Observation.cs",
    "Assets/Editor/NativeShadow28Fixture.shader",
)


def finite_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def bounded_error(value, tolerance):
    return finite_number(value) and 0 <= value <= tolerance


def read_object(path):
    def reject_nonfinite(value):
        raise ValueError(f"{path.name} contains nonfinite JSON number {value}")

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path.name} contains duplicate key {key!r}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8-sig"),
                       parse_constant=reject_nonfinite, object_pairs_hook=unique_keys)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return value


def verify_hashes(hashes):
    """Require unique project-relative paths and hash existing file bytes."""
    failures, verified, normalized = [], [], {}
    if not isinstance(hashes, dict) or not hashes:
        return [{"reason": "missing hash records"}], verified, normalized
    for relative, expected in hashes.items():
        if (not isinstance(relative, str) or not relative
                or not isinstance(expected, str)
                or not re.fullmatch(r"[0-9a-fA-F]{64}", expected)):
            failures.append({"path": str(relative), "reason": "invalid hash record"})
            continue
        key = relative.replace("\\", "/")
        source = Path(relative)
        if source.is_absolute() or source.drive or key in normalized:
            failures.append({"path": relative, "reason": "non-relative or duplicate path"})
            continue
        normalized[key] = expected.lower()
        source = (ROOT / source).resolve()
        try:
            source.relative_to(ROOT.resolve())
        except ValueError:
            failures.append({"path": relative, "reason": "outside project"})
            continue
        if not source.is_file():
            failures.append({"path": relative, "reason": "missing file"})
            continue
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != expected.lower():
            failures.append({"path": relative, "reason": "hash changed",
                             "expected": expected.lower(), "actual": actual})
        else:
            verified.append(key)
    return failures, verified, normalized


class Shadow28Gate:
    def __init__(self, output, fixture_only=False):
        self.output = output
        self.fixture_only = fixture_only
        self.checks = []
        self.metrics = {}

    def check(self, name, passed, detail=None):
        item = {"name": name, "passed": bool(passed)}
        if detail is not None:
            item["detail"] = detail
        self.checks.append(item)
        return item["passed"]

    def read_json(self, relative):
        return read_object(self.output / relative)

    def fixture(self):
        fixture = self.read_json("fixture.json")
        self.check("fixtureShaderErrorsZero", integer(fixture.get("shaderErrors"))
                   and fixture["shaderErrors"] == 0)
        cases = fixture.get("cases")
        self.check("fixtureFourCases", isinstance(cases, list) and len(cases) == 4)
        cases = cases if isinstance(cases, list) else []
        matched, invalid, duplicates, records = set(), [], [], []
        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                invalid.append(index)
                continue
            phase = case.get("phase")
            phase_index = None
            if (isinstance(phase, list) and len(phase) == 2
                    and all(finite_number(value) for value in phase)):
                phase_index = next((i for i, expected in enumerate(PHASES)
                                    if max(abs(a - b) for a, b in zip(phase, expected))
                                    <= PHASE_TOLERANCE), None)
            scale = case.get("pixelScale")
            valid = (phase_index is not None and integer(scale) and scale in PIXEL_SCALES
                     and finite_number(case.get("legacyProjectionErrorPx"))
                     and case["legacyProjectionErrorPx"] >= 0
                     and bounded_error(case.get("sharedProjectionErrorPx"), PROJECTION_TOLERANCE)
                     and bounded_error(case.get("pairOffsetErrorM"), PAIR_TOLERANCE)
                     and integer(case.get("hitSamples")) and case["hitSamples"] >= 100
                     and bounded_error(case.get("hitProjectionErrorPx"), PROJECTION_TOLERANCE))
            if not valid:
                invalid.append(index)
                continue
            key = (phase_index, scale)
            if key in matched:
                duplicates.append(index)
            matched.add(key)
            records.append(case)
        self.check("fixtureFiniteBoundedMeasurements", len(records) == 4 and not invalid,
                   {"invalidIndices": invalid})
        self.check("fixtureExactPhaseScaleMatrix", len(cases) == 4
                   and matched == EXPECTED_CASES and not duplicates,
                   {"missingCases": [list(value) for value in sorted(EXPECTED_CASES - matched)],
                    "duplicateIndices": duplicates, "phases": [list(p) for p in PHASES],
                    "pixelScales": list(PIXEL_SCALES)})
        self.check("fixtureLegacyMisalignmentObserved", bool(records) and any(
            case["legacyProjectionErrorPx"] > 0 for case in records))
        self.metrics["fixture"] = {
            "caseCount": len(cases), "validCaseCount": len(records), "cases": records,
            "maximumSharedProjectionErrorPx": max(
                (c["sharedProjectionErrorPx"] for c in records), default=None),
            "maximumLegacyProjectionErrorPx": max(
                (c["legacyProjectionErrorPx"] for c in records), default=None),
            "maximumPairOffsetErrorM": max((c["pairOffsetErrorM"] for c in records), default=None),
            "minimumHitSamples": min((c["hitSamples"] for c in records), default=None),
            "maximumHitProjectionErrorPx": max(
                (c["hitProjectionErrorPx"] for c in records), default=None),
        }

    def integration(self):
        if self.fixture_only and not (self.output / "integration.json").exists():
            self.metrics["integrationChecked"] = False
            return
        integration = self.read_json("integration.json")
        self.check("integrationPairCount44", integer(integration.get("pairCount"))
                   and integration["pairCount"] == EXPECTED_PAIRS)
        failures, verified, normalized = verify_hashes(integration.get("codeHashes"))
        missing = [path for path in REQUIRED_CODE_PATHS if path not in normalized]
        self.check("integrationRequiredCodeCoverage", not missing, {"missingPaths": missing})
        self.check("integrationCurrentCodeHashesMatch", not failures, failures)
        self.metrics["integrationChecked"] = True
        self.metrics["integrationVerifiedCodePaths"] = verified

    def baseline(self):
        baseline = self.read_json("baseline.json")
        frozen = read_object(N27_OUTPUT / "baseline.json")
        hashes = baseline.get("sourceHashes")
        self.check("frozenSourceCoverage512", isinstance(hashes, dict) and len(hashes) == 512
                   and hashes == frozen.get("sourceHashes"))
        failures, verified, _ = verify_hashes(hashes)
        self.check("frozenSourceActualHashesPreserved", not failures, failures)
        geometry = baseline.get("geometry")
        self.check("frozenGeometry194", isinstance(geometry, list) and len(geometry) == 194
                   and geometry == frozen.get("geometry"))
        self.check("frozenMovingBaseline", isinstance(baseline.get("moving"), dict)
                   and baseline["moving"] == frozen.get("moving"))
        for name in ("baseline-geometry.txt", "baseline-moving.json"):
            self.check("frozenBaselineFile:" + name,
                       (self.output / name).read_bytes() == (N27_OUTPUT / name).read_bytes())
        self.metrics["sourceFilesPreserved"] = len(verified)
        self.metrics["geometryCount"] = len(geometry) if isinstance(geometry, list) else 0

    def alignment(self):
        alignment = self.read_json("play/alignment.json")
        for name in ("rendererCount", "pairCount"):
            self.check("playAlignment:" + name, integer(alignment.get(name))
                       and alignment[name] == EXPECTED_PAIRS)
        self.check("playAlignmentShaderErrorsZero", integer(alignment.get("shaderErrors"))
                   and alignment["shaderErrors"] == 0)
        self.check("playPairOffsetAligned", bounded_error(
            alignment.get("maximumPairOffsetErrorM"), PAIR_TOLERANCE))
        self.check("playSharedProjectionAligned", bounded_error(
            alignment.get("maximumSharedProjectionErrorPx"), PROJECTION_TOLERANCE))
        legacy = alignment.get("maximumLegacyProjectionErrorPx")
        self.check("playLegacyMisalignmentObserved", finite_number(legacy) and legacy > 0)
        self.metrics["playAlignment"] = alignment

    def result(self, preservation=None):
        checks = list(self.checks)
        if preservation is not None:
            checks.extend({**item, "name": "N26." + item["name"]}
                          for item in preservation["checks"])
        success = bool(checks) and all(item["passed"] for item in checks)
        if not self.fixture_only:
            success = success and preservation is not None and preservation.get("success") is True
        return {"success": success, "contract": "Tools/PerfectPixelUniform/BUILDING16.md N28",
                "mode": "fixture-only" if self.fixture_only else "full", "checks": checks,
                **self.metrics, "room26": preservation,
                "tolerances": {"projectionPixels": PROJECTION_TOLERANCE,
                               "pairWorldMetres": PAIR_TOLERANCE, "screenPhase": PHASE_TOLERANCE},
                "scope": "Four actual GPU alignment cases and their sampled projection errors. Full mode additionally checks current production-code hashes, 44 Play renderer/caster pairs, the frozen N27 baselines and the unchanged N26 actual-Play/PNG gate. Centre-hit projection agreement does not establish silhouette-edge or aesthetic approval; no input, build or performance approval."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="N28 observations (default: docs/artifacts/building39/shadow28)")
    parser.add_argument("--fixture-only", action="store_true",
                        help="Measure the fixture; check integration.json when present.")
    args = parser.parse_args(argv)
    gate = Shadow28Gate(args.output.resolve(), args.fixture_only)
    operations = [("fixtureReadable", gate.fixture), ("integrationReadable", gate.integration)]
    if not args.fixture_only:
        operations.extend((("baselineReadable", gate.baseline), ("playAlignmentReadable", gate.alignment)))
    for name, operation in operations:
        try:
            operation()
        except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError) as error:
            gate.check(name, False, f"{type(error).__name__}: {error}")
    preservation = None
    if not args.fixture_only:
        room_gate = room26_gate.Gate(gate.output)
        try:
            room_gate.run()
        except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError) as error:
            room_gate.check("observationReadable", False, f"{type(error).__name__}: {error}")
        preservation = room_gate.result()
    result = gate.result(preservation)
    validation = gate.output / "validation28.json"
    try:
        validation.parent.mkdir(parents=True, exist_ok=True)
        validation.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    except (OSError, ValueError) as error:
        result["success"] = False
        result["validationWriteError"] = f"{type(error).__name__}: {error}"
    summary = {"success": result["success"], "mode": result["mode"],
               "passedChecks": sum(item["passed"] for item in result["checks"]),
               "totalChecks": len(result["checks"]),
               "failedChecks": [item["name"] for item in result["checks"] if not item["passed"]],
               "fixture": gate.metrics.get("fixture", {}), "validation": str(validation)}
    summary["fixture"] = {key: value for key, value in summary["fixture"].items() if key != "cases"}
    if "validationWriteError" in result:
        summary["validationWriteError"] = result["validationWriteError"]
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
