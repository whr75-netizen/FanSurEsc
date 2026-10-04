"""N27 GPU material-filter gate, with the unchanged N26 preservation gate.

The Unity observer supplies fixture.json with 96 linear ARGBFloat samples.
Full mode also consumes integration.json and the N26 baseline, Play receipt,
final receipt and seven PNGs. This script writes only validation27.json; it
does not manufacture observations or declare aesthetic approval.
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
DEFAULT_OUTPUT = ROOT / "docs/artifacts/building39/light27"
FLOAT_TOLERANCE = 1e-5
INPUT_TOLERANCE = 1e-6
LUMINANCE = (.2126729, .7151522, .0721750)
ALBEDOS = ((0., 0., 0.), (.4, .15, .04), (.02, .08, .15), (.8, .8, .8))
BASES = ((0., 0., 0.), (.08, .08, .08), (.2, .2, .2), (.5, .5, .5),
         (.03, .045, .085), (.4, .1, .03))
LOCALS = ((0., 0., 0.), (.22 / 3,) * 3, (.44 / 3,) * 3, (.22,) * 3)
EXPECTED_CASES = set(itertools.product(range(len(ALBEDOS)), range(len(BASES)),
                                     range(len(LOCALS))))
REQUIRED_CODE_PATHS = (
    "Assets/Rendering/LocalLighting/MaterialLightResponse27.hlsl",
    "Assets/Editor/MaterialLight27Fixture.shader",
    "Assets/Shaders/World/NativeReadable18.hlsl",
    "Assets/Shaders/World/NativePaletteSurface16.shader",
    "Assets/Rendering/LocalLighting/SteppedLocalLightFullscreen.shader",
)


def finite_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def vector(value):
    return (isinstance(value, list) and len(value) == 3
            and all(finite_number(channel) for channel in value))


def case_index(value, candidates):
    for index, candidate in enumerate(candidates):
        if max(abs(a - b) for a, b in zip(value, candidate)) <= INPUT_TOLERANCE:
            return index
    return None


def reference(albedo, base_irradiance, stepped_irradiance):
    """Mirror the shared float HLSL formula using an independent CPU reference."""
    irradiance = [max(channel, 0.) for channel in base_irradiance]
    peak = max(irradiance)
    tint = [channel / peak for channel in irradiance] if peak > 1e-6 else [0.] * 3
    y = sum(channel * weight for channel, weight in zip(irradiance, LUMINANCE))
    brightness = .55 if y < .12 else (.78 if y < .4 else 1.)
    return [a * (brightness * t + max(local, 0.))
            for a, t, local in zip(albedo, tint, stepped_irradiance)]


class Light27Gate:
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

    def read_json(self, name):
        def reject_nonfinite(value):
            raise ValueError(f"{name} contains nonfinite JSON number {value}")

        value = json.loads((self.output / name).read_text(encoding="utf-8-sig"),
                           parse_constant=reject_nonfinite)
        if not isinstance(value, dict):
            raise ValueError(f"{name} must be a JSON object")
        return value

    def fixture(self):
        fixture = self.read_json("fixture.json")
        self.check("fixtureLinearColorSpace", fixture.get("colorSpace") == "Linear")
        self.check("fixtureShaderErrorsZero", fixture.get("shaderErrors") == 0
                   and not isinstance(fixture.get("shaderErrors"), bool))
        samples = fixture.get("samples")
        is_list = isinstance(samples, list)
        self.check("fixtureSamplesPresent", is_list)
        count = len(samples) if is_list else 0
        self.metrics["sampleCount"] = count
        self.metrics["expectedSampleCount"] = len(EXPECTED_CASES)
        self.check("fixtureAtLeast96Samples", count >= 96)
        self.check("fixtureExpectedCaseCount96", len(EXPECTED_CASES) == 96)
        if not is_list:
            return

        records = []
        invalid = []
        unmatched = []
        duplicates = []
        by_case = {}
        cpu_failures = []
        black_failures = []
        ratio_failures = []
        maximum_error = 0.
        maximum_black = 0.
        maximum_ratio_error = 0.
        for index, sample in enumerate(samples):
            keys = ("albedo", "baseIrradiance", "steppedIrradiance", "gpu")
            if not isinstance(sample, dict) or not all(vector(sample.get(key)) for key in keys):
                invalid.append(index)
                continue
            a, b, local, gpu = (sample[key] for key in keys)
            expected = reference(a, b, local)
            error = max(abs(actual - wanted) for actual, wanted in zip(gpu, expected))
            maximum_error = max(maximum_error, error)
            key = (case_index(a, ALBEDOS), case_index(b, BASES), case_index(local, LOCALS))
            record = {"index": index, "albedo": a, "baseIrradiance": b,
                      "steppedIrradiance": local, "gpu": gpu, "expected": expected,
                      "maximumAbsoluteError": error}
            records.append(record)
            if None in key:
                unmatched.append(index)
            elif key in by_case:
                duplicates.append({"index": index, "firstIndex": by_case[key]["index"],
                                   "case": list(key)})
            else:
                by_case[key] = record
            if error > FLOAT_TOLERANCE:
                cpu_failures.append({"index": index, "maximumAbsoluteError": error})
            if key[0] == 0:
                black_error = max(abs(channel) for channel in gpu)
                maximum_black = max(maximum_black, black_error)
                if black_error > FLOAT_TOLERANCE:
                    black_failures.append({"index": index, "gpu": gpu})
            # A channel cross-product checks hue ratios without unstable division
            # by dark channels. Its normalized error has the same RGB units and
            # tolerance as the CPU comparison; it also permits physical light tint.
            for first, second in itertools.combinations(range(3), 2):
                denominator = abs(expected[first]) + abs(expected[second])
                if denominator <= 0.:
                    continue
                ratio_error = abs(gpu[first] * expected[second]
                                  - gpu[second] * expected[first]) / denominator
                maximum_ratio_error = max(maximum_ratio_error, ratio_error)
                if ratio_error > FLOAT_TOLERANCE:
                    ratio_failures.append({"index": index, "channels": [first, second],
                                           "normalizedError": ratio_error})

        missing = sorted(EXPECTED_CASES - set(by_case))
        self.check("fixtureSamplesFinite", not invalid, {"invalidIndices": invalid})
        self.check("fixtureInputCasesExact96", count == 96 and len(by_case) == 96
                   and not missing and not unmatched and not duplicates,
                   {"matchedCaseCount": len(by_case), "missingCases": [list(k) for k in missing],
                    "unmatchedIndices": unmatched, "duplicateCases": duplicates})
        self.check("gpuMatchesCPUReference", len(records) == count and bool(records)
                   and not cpu_failures, cpu_failures)
        self.check("blackAlbedoGPUZero", sum(key[0] == 0 for key in by_case) == 24
                   and not black_failures, black_failures)
        self.check("noCrossHueRatioViolations", bool(records) and not ratio_failures,
                   ratio_failures)
        self.metrics.update({"validSampleCount": len(records), "matchedCaseCount": len(by_case),
                             "maximumCPUError": maximum_error if records else None,
                             "maximumBlackRGB": maximum_black,
                             "maximumNormalizedHueRatioError": maximum_ratio_error,
                             "crossHueRatioViolationCount": len(ratio_failures),
                             "samples": records})
        self.local_levels(by_case)

    def local_levels(self, by_case):
        levels = []
        level_failures = []
        proportional_failures = []
        maximum_proportional_error = 0.
        for albedo_index in range(1, len(ALBEDOS)):
            for base_index in range(len(BASES)):
                group = [by_case.get((albedo_index, base_index, local_index))
                         for local_index in range(len(LOCALS))]
                if any(sample is None for sample in group):
                    level_failures.append({"albedoIndex": albedo_index, "baseIndex": base_index,
                                           "reason": "missing local level"})
                    continue
                baseline = group[0]["gpu"]
                gains = [[value - off for value, off in zip(sample["gpu"], baseline)]
                         for sample in group[1:]]
                positive_count = sum(all(channel > 0. for channel in gain) for gain in gains)
                distinct = []
                for sample in group[1:]:
                    if not any(max(abs(a - b) for a, b in zip(sample["gpu"], previous))
                               <= FLOAT_TOLERANCE for previous in distinct):
                        distinct.append(sample["gpu"])
                minimum_increment = min(current - previous
                                        for earlier, later in zip(group, group[1:])
                                        for previous, current in zip(earlier["gpu"], later["gpu"]))
                detail = {"albedoIndex": albedo_index, "baseIndex": base_index,
                          "positiveLevelCount": positive_count,
                          "distinctPositiveLevelCount": len(distinct),
                          "minimumChannelIncrement": minimum_increment}
                levels.append(detail)
                if positive_count != 3 or len(distinct) != 3 or minimum_increment <= 0.:
                    level_failures.append(detail)
                # Neutral bases (including no base) must retain the material's
                # channel proportions under each added white-light band.
                if base_index < 4:
                    albedo = group[0]["albedo"]
                    for sample, gain in zip(group[1:], gains):
                        local = sample["steppedIrradiance"]
                        error = max(abs(delta / channel - illumination)
                                    for delta, channel, illumination in zip(gain, albedo, local))
                        maximum_proportional_error = max(maximum_proportional_error, error)
                        if error > FLOAT_TOLERANCE:
                            proportional_failures.append({"index": sample["index"],
                                                          "maximumRatioError": error})
        self.check("threePositiveWhiteLocalLevels", len(levels) == 18 and not level_failures,
                   level_failures)
        self.check("whiteBaseLocalDeltaAlbedoProportional", len(levels) == 18
                   and not proportional_failures, proportional_failures)
        self.metrics["whiteLocalLevelCounts"] = levels
        self.metrics["maximumWhiteLocalDeltaPerAlbedoError"] = maximum_proportional_error

    def integration(self):
        path = self.output / "integration.json"
        if self.fixture_only and not path.exists():
            self.metrics["integrationChecked"] = False
            self.metrics["integrationScope"] = "Optional in fixture-only mode; no production binding verified."
            return
        integration = self.read_json("integration.json")
        hashes = integration.get("codeHashes")
        valid_hashes = isinstance(hashes, dict) and bool(hashes)
        self.check("integrationCodeHashesPresent", valid_hashes)
        if not isinstance(hashes, dict):
            hashes = {}
        normalized = {key.replace("\\", "/"): value for key, value in hashes.items()
                      if isinstance(key, str)}
        missing = [path for path in REQUIRED_CODE_PATHS if path not in normalized]
        self.check("integrationRequiredProductionCodeCoverage", not missing,
                   {"missingPaths": missing, "requiredPaths": list(REQUIRED_CODE_PATHS)})
        required = integration.get("requiredCodePaths", list(REQUIRED_CODE_PATHS))
        valid_required = (isinstance(required, list) and bool(required)
                          and all(isinstance(item, str) and item for item in required))
        self.check("integrationDeclaredCoverage", valid_required and all(
            item.replace("\\", "/") in normalized for item in required),
            {"requiredCodePaths": required})
        changed = []
        verified = []
        for relative, expected in hashes.items():
            if not isinstance(relative, str) or not isinstance(expected, str) or not re.fullmatch(
                    r"[0-9a-fA-F]{64}", expected):
                changed.append({"path": str(relative), "reason": "invalid hash record"})
                continue
            source = (ROOT / relative).resolve()
            try:
                source.relative_to(ROOT.resolve())
            except ValueError:
                changed.append({"path": relative, "reason": "outside project"})
                continue
            if not source.is_file():
                changed.append({"path": relative, "reason": "missing code"})
                continue
            actual = hashlib.sha256(source.read_bytes()).hexdigest()
            if actual != expected.lower():
                changed.append({"path": relative, "reason": "hash changed",
                                "expected": expected.lower(), "actual": actual})
            else:
                verified.append(relative)
        self.check("integrationCurrentCodeHashesMatch", valid_hashes and not changed, changed)
        self.metrics["integrationChecked"] = True
        self.metrics["integrationVerifiedCodePaths"] = verified
        self.metrics["integrationCodeHashes"] = hashes

    def result(self, preservation=None):
        checks = list(self.checks)
        if preservation is not None:
            checks.extend({**item, "name": "N26." + item["name"]}
                          for item in preservation["checks"])
        success = bool(checks) and all(item["passed"] for item in checks)
        if not self.fixture_only:
            success = success and preservation is not None and preservation.get("success") is True
        return {"success": success,
                "contract": "Tools/PerfectPixelUniform/BUILDING16.md N27",
                "mode": "fixture-only" if self.fixture_only else "full",
                "checks": checks, "fixture": self.metrics, "room26": preservation,
                "tolerances": {"fixtureFloatRGB": FLOAT_TOLERANCE,
                               "whiteLocalDeltaPerAlbedo": FLOAT_TOLERANCE,
                               "fixtureInputRGB": INPUT_TOLERANCE},
                "scope": "Actual linear GPU fixture versus CPU material-filter reference; black reflectance, three white-local levels and hue ratios. Full mode additionally binds current production-code hashes and reuses the unchanged N26 preservation/pixel gate. No aesthetic, input, build or performance approval."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="N27 observation directory (default: docs/artifacts/building39/light27)")
    parser.add_argument("--fixture-only", action="store_true",
                        help="Measure only the GPU fixture; verify integration.json when present.")
    args = parser.parse_args(argv)
    gate = Light27Gate(args.output.resolve(), args.fixture_only)
    for name, operation in (("fixtureObservationReadable", gate.fixture),
                            ("integrationObservationReadable", gate.integration)):
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
    validation = gate.output / "validation27.json"
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
               "sampleCount": gate.metrics.get("sampleCount", 0),
               "maximumCPUError": gate.metrics.get("maximumCPUError"),
               "validation": str(validation)}
    if "validationWriteError" in result:
        summary["validationWriteError"] = result["validationWriteError"]
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
