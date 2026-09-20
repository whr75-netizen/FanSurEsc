"""Exercise real WorkLoop commands and branches with temporary stage artifacts."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


DRIVER_PATH = Path(__file__).with_name("graph_driver.py")
SPEC = importlib.util.spec_from_file_location("pixel_graph_driver_under_test", DRIVER_PATH)
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)


FAKE_STAGES = r'''
import argparse
import hashlib
import json
from pathlib import Path


def artifact(root, stage, p):
    return root / f"pass-{p}" / stage / "receipt.json"


def stage_resources(stage, pass_index, run_dir, contract_path):
    root, p = Path(run_dir), pass_index
    settings = root / f"pass-{p}" / "settings.json"
    writes = [artifact(root, stage, p), artifact(root, stage, p).parent / "stage_receipt.json"]
    reads = [Path(contract_path)]
    if stage == "inputs":
        writes.append(settings)
    elif stage == "geometry":
        reads.append(artifact(root, "inputs", 0))
    elif stage == "material":
        reads.append(artifact(root, "geometry", 0))
    elif stage == "repair":
        reads += [artifact(root, "diagnose", p-1), root / f"pass-{p-1}" / "settings.json"]
        writes.append(settings)
    elif stage == "raster":
        reads += [artifact(root, "geometry", 0), artifact(root, "material", 0), settings]
    else:
        predecessor = {"shade": "raster", "pixel": "shade", "diagnose": "pixel",
                       "package": "diagnose", "validate": "package"}[stage]
        reads.append(artifact(root, predecessor, p))
    return {"reads": reads, "writes": writes}


def verify_receipt(path):
    result = json.loads(Path(path).read_text(encoding="utf-8"))
    for bucket in ("inputs", "outputs"):
        for name, expected in result[bucket].items():
            if not Path(name).is_file() or hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
                raise ValueError("STALE_ARTIFACT: " + name)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--pass", dest="pass_index", type=int, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args()
    stage, p, root = args.stage, args.pass_index, args.run_dir
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    paths = stage_resources(stage, p, root, args.contract)
    for path in paths["reads"]:
        if not path.is_file():
            raise RuntimeError(f"Missing actual dependency: {path}")
    receipt = artifact(root, stage, p)
    count = json.loads(receipt.read_text())["calls"] if receipt.exists() else 0
    result = {"state": "ready", "stage": stage, "pass": p, "calls": count + 1}
    if stage == "diagnose":
        diagnoses = contract.get("diagnoses", ["ready"])
        result["state"] = diagnoses[min(p, len(diagnoses)-1)]
        result["diagnosis"] = {"projected_gap": 0.2 + p}
        if contract.get("missing_state"):
            del result["state"]
    if stage == "validate":
        result["accepted"] = contract.get("accepted", True)
    for path in paths["writes"]:
        if path.name == "stage_receipt.json":
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result), encoding="utf-8")
    if contract.get("fail_stage") == stage:
        raise SystemExit(7)
    hashes = lambda files: {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in files if path.name != "stage_receipt.json"}
    (receipt.parent / "stage_receipt.json").write_text(json.dumps({
        "stage": stage, "inputs": hashes(paths["reads"]), "outputs": hashes(paths["writes"]),
        "details": result}), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
'''


class PixelGraphContracts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.stages = self.root / "stages.py"
        self.stages.write_text(FAKE_STAGES, encoding="utf-8")
        self.contract = self.root / "contract.json"
        self.run_dir = self.root / "run"

    def initialize(self, config=None, max_repairs=2):
        self.contract.write_text(json.dumps(config or {}), encoding="utf-8")
        return driver.initialize(self.run_dir, self.contract, self.stages,
                                 max_repairs=max_repairs)

    def execute(self, config=None, max_repairs=2):
        self.initialize(config, max_repairs)
        return driver.continue_run(self.run_dir)

    def state(self):
        return json.loads((self.run_dir / "workflow-state.json").read_text(encoding="utf-8"))

    def artifacts(self):
        return {path.relative_to(self.run_dir).as_posix(): json.loads(path.read_text())
                for path in self.run_dir.glob("pass-*/*/receipt.json")}

    def test_ready_routes_to_executable_validation_and_visual_review(self):
        report = self.execute()
        self.assertEqual(report["status"], "awaiting_visual_review")
        self.assertEqual(report["visual_acceptance"], "pending")
        self.assertEqual(report["last_stage"], "validate_0")
        self.assertEqual(report["steps"], 18)
        self.assertTrue(report["stage_result"]["accepted"])
        self.assertEqual(len(self.artifacts()), 9)
        self.assertTrue(all(item["calls"] == 1 for item in self.artifacts().values()))
        self.assertFalse(any(node["algorithm"].startswith("ai.") for node in self.state()["graph"]["nodes"]))

    def test_repair_rerenders_only_later_stages_and_resume_reuses_completion(self):
        report = self.execute({"diagnoses": ["repairable", "ready"]})
        self.assertEqual(report["status"], "awaiting_visual_review")
        self.assertEqual(report["last_stage"], "validate_1")
        artifacts = self.artifacts()
        self.assertIn("pass-1/repair/receipt.json", artifacts)
        self.assertIn("pass-1/raster/receipt.json", artifacts)
        self.assertNotIn("pass-1/geometry/receipt.json", artifacts)
        self.assertNotIn("pass-1/material/receipt.json", artifacts)
        self.assertNotIn("pass-0/package/receipt.json", artifacts)
        before = {path: path.read_bytes() for path in self.run_dir.rglob("*.json")}
        resumed = driver.continue_run(self.run_dir, resume=True)
        self.assertEqual(resumed["status"], "awaiting_visual_review")
        self.assertEqual(before, {path: path.read_bytes() for path in self.run_dir.rglob("*.json")})
        self.assertTrue(all(item["calls"] == 1 for item in artifacts.values()))

    def test_two_repairs_are_bounded_and_keep_prior_passes_immutable(self):
        report = self.execute({"diagnoses": ["repairable", "repairable", "ready"]})
        self.assertEqual(report["status"], "awaiting_visual_review")
        self.assertEqual(report["last_stage"], "validate_2")
        self.assertEqual(report["steps"], 38)
        self.assertEqual(len(self.artifacts()), 19)
        self.assertTrue(all(item["calls"] == 1 for item in self.artifacts().values()))
        self.assertFalse((self.run_dir / "pass-3").exists())

    def test_exhausted_repair_budget_blocks_without_packaging(self):
        report = self.execute({"diagnoses": ["repairable"]})
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["last_stage"], "diagnose_2")
        self.assertEqual(report["stage_result"]["state"], "repairable")
        self.assertFalse(any("package" in path for path in self.artifacts()))
        self.assertFalse((self.run_dir / "pass-3").exists())
        self.assertFalse(self.state()["complete"])

    def test_diagnosed_block_does_not_trigger_repair(self):
        report = self.execute({"diagnoses": ["blocked"]})
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["last_stage"], "diagnose_0")
        self.assertFalse((self.run_dir / "pass-1").exists())

    def test_missing_diagnosis_state_cannot_default_to_success(self):
        report = self.execute({"missing_state": True})
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["reason"], "unknown_guard")
        self.assertFalse(any("package" in path for path in self.artifacts()))

    def test_final_content_check_rejection_blocks(self):
        report = self.execute({"accepted": False})
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["last_stage"], "validate_0")
        self.assertFalse(self.state()["complete"])

    def test_unexpected_command_exit_blocks_and_is_not_retried(self):
        report = self.execute({"fail_stage": "raster"})
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(self.state()["results"]["raster_0"]["output"]["exit_code"], 7)
        self.assertNotIn("pass-0/shade/receipt.json", self.artifacts())
        before = self.artifacts()
        driver.continue_run(self.run_dir, resume=True)
        self.assertEqual(before, self.artifacts())

    def test_uncertain_command_state_is_preserved_without_replay(self):
        self.initialize()
        state = self.state()
        state["active"] = {"node": "inputs_0", "signature": "interrupted-command"}
        driver.work_loop.save(self.run_dir / "workflow-state.json", state)
        report = driver.continue_run(self.run_dir, resume=True)
        self.assertEqual(report["status"], "uncertain_execution")
        self.assertEqual(self.artifacts(), {})

    def test_modified_contract_preserves_state_and_requires_review(self):
        self.initialize()
        before = (self.run_dir / "workflow-state.json").read_bytes()
        self.contract.write_text('{"diagnoses": ["ready"]}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Contract content changed"):
            driver.continue_run(self.run_dir)
        self.assertEqual(before, (self.run_dir / "workflow-state.json").read_bytes())
        self.assertEqual(self.artifacts(), {})

    def test_existing_state_is_not_overwritten_by_init(self):
        self.initialize()
        before = (self.run_dir / "workflow-state.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "Existing graph/state"):
            driver.initialize(self.run_dir, self.contract, self.stages)
        self.assertEqual(before, (self.run_dir / "workflow-state.json").read_bytes())

    def test_explicit_recovery_preserves_failed_run_and_reuses_six_stages(self):
        self.execute({"fail_stage": "diagnose"})
        original = {name: (self.run_dir / name).read_bytes()
                    for name in ("workflow-state.json", "workflow-graph.json")}
        retained = {path: path.read_bytes() for path in self.run_dir.rglob("*.json")
                    if path.name not in original and "diagnose" not in path.parts}
        self.stages.write_text(FAKE_STAGES.replace('if contract.get("fail_stage") == stage:', 'if False:'),
                               encoding="utf-8")
        recovery = driver.recover(self.run_dir, "diagnose", 0)
        self.assertEqual(recovery["status"], "ready")
        self.assertEqual(recovery["verified_prior_stages"],
                         ["inputs_0", "geometry_0", "material_0", "raster_0", "shade_0", "pixel_0"])
        history = self.run_dir / "recovery-history" / "0001"
        for name, content in original.items():
            self.assertEqual(content, (history / name).read_bytes())
        self.assertTrue((history / "failed-output/pass-0/diagnose/receipt.json").is_file())
        self.assertFalse((self.run_dir / "pass-0/diagnose/receipt.json").exists())
        self.assertEqual(self.state()["graph"]["entry"], "diagnose_0")
        self.assertEqual(retained, {path: path.read_bytes() for path in retained})
        report = driver.continue_run(self.run_dir)
        self.assertEqual(report["status"], "awaiting_visual_review")
        self.assertEqual(report["steps"], 6)
        self.assertEqual(retained, {path: path.read_bytes() for path in retained})
        self.assertNotIn("raster_0", self.state()["visits"])

    def test_recovery_rejects_a_changed_successful_output_before_mutation(self):
        self.execute({"fail_stage": "diagnose"})
        (self.run_dir / "pass-0/pixel/receipt.json").write_text('{"calls":999}', encoding="utf-8")
        before = (self.run_dir / "workflow-state.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "STALE_ARTIFACT"):
            driver.recover(self.run_dir, "diagnose", 0)
        self.assertEqual(before, (self.run_dir / "workflow-state.json").read_bytes())
        self.assertFalse((self.run_dir / "recovery-history").exists())

    def test_recovery_rejects_a_different_stage_and_unchanged_run_stays_blocked(self):
        self.execute({"fail_stage": "diagnose"})
        before = (self.run_dir / "workflow-state.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "must match"):
            driver.recover(self.run_dir, "shade", 0)
        self.assertEqual(before, (self.run_dir / "workflow-state.json").read_bytes())
        self.assertEqual(driver.continue_run(self.run_dir, resume=True)["status"], "blocked")
        self.assertFalse((self.run_dir / "recovery-history").exists())

    def test_recovery_cannot_relabel_an_identical_failed_algorithm_as_progress(self):
        self.execute({"fail_stage": "diagnose"})
        before = (self.run_dir / "workflow-state.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "No stage/helper code changed"):
            driver.recover(self.run_dir, "diagnose", 0)
        self.assertEqual(before, (self.run_dir / "workflow-state.json").read_bytes())
        self.assertFalse((self.run_dir / "recovery-history").exists())

    def evidence(self, pass_index=0):
        target = self.run_dir / f"pass-{pass_index}/pixel/receipt.json"
        path = self.root / "boundary-evidence.json"
        path.write_text(json.dumps({"reason": "BOUNDARY_DOUBLE_STROKE",
                                    "files": {str(target): driver._sha256(target)}}), encoding="utf-8")
        return path

    def test_completed_pass_reopens_at_diagnosis_and_routes_to_remaining_repair(self):
        self.execute({"diagnoses": ["repairable", "ready", "ready"]})
        evidence = self.evidence(1)
        original = {path: path.read_bytes() for path in self.run_dir.rglob("*.json")}
        self.stages.write_text(FAKE_STAGES.replace(
            'result["state"] = diagnoses[min(p, len(diagnoses)-1)]',
            'result["state"] = "repairable" if p == 1 else diagnoses[min(p, len(diagnoses)-1)]'), encoding="utf-8")
        report = driver.reopen(self.run_dir, "diagnose", 1, evidence)
        self.assertEqual(report["status"], "ready")
        self.assertEqual(self.state()["graph"]["entry"], "diagnose_1")
        history = self.run_dir / "reopening-history/0001"
        for stage in ("diagnose", "package", "validate"):
            source = self.run_dir / f"pass-1/{stage}/receipt.json"
            self.assertFalse(source.exists())
            self.assertEqual(original[source], (history / f"completed-output/pass-1/{stage}/receipt.json").read_bytes())
        self.assertEqual(evidence.read_bytes(), (history / "evidence.json").read_bytes())
        for name in ("workflow-state.json", "workflow-graph.json"):
            self.assertEqual(original[self.run_dir / name], (history / name).read_bytes())
        retained = {path: content for path, content in original.items()
                    if path.is_file() and path.name not in ("workflow-state.json", "workflow-graph.json")}
        completed = driver.continue_run(self.run_dir)
        self.assertEqual(completed["status"], "awaiting_visual_review")
        self.assertEqual(completed["last_stage"], "validate_2")
        self.assertIn("repair_2", self.state()["visits"])
        self.assertNotIn("raster_1", self.state()["visits"])
        self.assertNotIn("geometry_0", self.state()["visits"])
        self.assertEqual(retained, {path: path.read_bytes() for path in retained})

    def test_reopen_rejects_incomplete_state_and_stale_evidence(self):
        self.execute({"fail_stage": "diagnose"})
        evidence = self.evidence()
        before = (self.run_dir / "workflow-state.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "completed technical validation"):
            driver.reopen(self.run_dir, "diagnose", 0, evidence)
        self.assertEqual(before, (self.run_dir / "workflow-state.json").read_bytes())
        self.assertFalse((self.run_dir / "reopening-history").exists())

    def test_reopen_rejects_tampered_evidence_targets_without_moving_results(self):
        self.execute()
        evidence = self.evidence()
        target = self.run_dir / "pass-0/pixel/receipt.json"
        target.write_text('{"tampered":true}', encoding="utf-8")
        before = (self.run_dir / "workflow-state.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "STALE_EVIDENCE"):
            driver.reopen(self.run_dir, "diagnose", 0, evidence)
        self.assertEqual(before, (self.run_dir / "workflow-state.json").read_bytes())
        self.assertTrue((self.run_dir / "pass-0/package/receipt.json").is_file())
        self.assertFalse((self.run_dir / "reopening-history").exists())

    def test_reopen_requires_changed_algorithm_and_the_completed_pass(self):
        self.execute()
        evidence = self.evidence()
        before = (self.run_dir / "workflow-state.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "completed pass's diagnose"):
            driver.reopen(self.run_dir, "diagnose", 1, evidence)
        with self.assertRaisesRegex(ValueError, "No stage/helper code changed"):
            driver.reopen(self.run_dir, "diagnose", 0, evidence)
        self.assertEqual(before, (self.run_dir / "workflow-state.json").read_bytes())
        self.assertFalse((self.run_dir / "reopening-history").exists())


if __name__ == "__main__":
    unittest.main()
