"""Check the reported failure boundaries, not game or art completion."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/artifacts/building33-native-probe/remediation-checks.json"


def main():
    cases = []
    for name, marker in (("normalize_art.py", "B33_FORCED_GRID_RETIRED"),
                         ("normalize_uniform.py", "B33_SLOT_FIT_RETIRED")):
        run = subprocess.run([sys.executable, "-B", str(ROOT / "Tools/Building33" / name)],
                             cwd=ROOT, text=True, capture_output=True, timeout=30)
        cases.append({"case": name, "exit_code": run.returncode,
                      "passed": run.returncode != 0 and marker in run.stderr})
    receipt = ROOT / "docs/artifacts/building33-native-probe/receipt.json"
    old = ROOT / "docs/artifacts/building33/uniform-art-manifest.json"
    for name, stage, source, expected, expected_reason in (
        ("upstream_actual_source", "normalization", receipt, 0, None),
        ("old_forced_grid_rejected", "normalization", old, 2, "UNREGISTERED_RECEIPT_SCHEMA"),
        ("no_master_art_rejected", "generation", None, 2, "REFERENCE_ART_NOT_REGISTERED"),
        ("no_registered_placement_solver", "placement", receipt, 2, "PLACEMENT_SOLVER_NOT_REGISTERED")):
        argv = [sys.executable, "-B", str(ROOT / "Tools/Building33/production_gate.py"), "--stage", stage]
        if source:
            argv += ["--receipt", str(source)]
        run = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=30)
        try:
            result = json.loads(run.stdout)
        except json.JSONDecodeError:
            result = {"invalid_result": run.stdout, "stderr": run.stderr}
        cases.append({"case": name, "exit_code": run.returncode,
                      "passed": run.returncode == expected and "invalid_result" not in result
                      and result.get("allowed") is (expected == 0)
                      and result.get("code") == expected_reason,
                      "observation": result})
    observed = ROOT / "LocalOnly/ProductionAudit27/unity-retired-check.json"
    unity = json.loads(observed.read_text(encoding="utf-8-sig"))
    cases.append({"case": "actual_unity_authoring_blocked", "observation": unity,
                  "passed": unity["blockedEntryPoints"] == 2 and not unity["isPlaying"]
                  and unity["dirtyBefore"] is False and unity["dirtyAfter"] is False,
                  "evidence_sha256": hashlib.sha256(observed.read_bytes()).hexdigest()})
    result = {"scope": "Operating-contract and source-normalization failure boundaries only",
              "remediation_checks_passed": all(c["passed"] for c in cases), "cases": cases,
              "building_art_complete": False, "model_or_server_fixed": False,
              "remaining": ["Full-scene reference art and asset correspondence",
                            "Shared projection calibration and placement solver",
                            "Actual new Unity art integration and visual result"]}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"checks_passed": result["remediation_checks_passed"], "cases": len(cases),
                      "report": str(OUT)}, ensure_ascii=False))
    return 0 if result["remediation_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
