"""Bind deterministic pixel stages to the existing, frozen WorkLoop graph.

Stages own computation and dependency receipts. This module only constructs the
finite procedure and delegates execution, persistence and branch evaluation to
WorkLoop. Technical acceptance always awaits the user's visual review.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = ROOT / "Tools" / "WorkLoop" / "work_loop.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


work_loop = _load_module(ENGINE_PATH, "pixel_pipeline_work_loop")


def _literal(value):
    return {"literal": value}


def _ref(value):
    return {"ref": value}


def _equal(reference, value):
    return {"op": "eq", "args": [_ref(reference), _literal(value)]}


def _edge(target, predicate):
    return {"to": target, "when": predicate}


def _file_resource(path):
    path = str(path)
    if path.startswith("file:"):
        path = path[5:]
    return "file:" + str(Path(path).resolve())


def build_graph(run_dir, contract_path, stages_path, resource_resolver,
                code_files=(), max_repairs=2, python_executable=None):
    """Create the fixed graph using the stages module's exact artifact scopes.

    resource_resolver(stage, pass_index, run_dir, contract_path) returns
    {"reads": [absolute file paths], "writes": [absolute file paths]}.
    repair at pass N reads diagnosis/settings from N-1 and writes settings for N.
    Initial geometry/material and all earlier pass outputs remain immutable.
    """
    if type(max_repairs) is not int or not 0 <= max_repairs <= 2:
        raise ValueError("max_repairs must be between 0 and 2")
    run_dir = Path(run_dir).resolve()
    contract_path = Path(contract_path).resolve(strict=True)
    stages_path = Path(stages_path).resolve(strict=True)
    executable = str(Path(python_executable or sys.executable).resolve())
    # The actual stage scripts, helper modules, and driver are frozen by the
    # engine. Contract content is also checked on every driver continuation.
    frozen = list(dict.fromkeys(str(Path(path).resolve(strict=True))
                               for path in [stages_path, Path(__file__), *code_files]))
    graph_nodes = []

    def add_stage(stage, pass_index, next_id=None, diagnose=False, validate=False):
        key = f"{stage}_{pass_index}"
        parsed = key + "_json"
        scope = resource_resolver(stage, pass_index, run_dir, contract_path)
        if not isinstance(scope, dict) or set(scope) != {"reads", "writes"}:
            raise ValueError(f"Invalid resource scope: {key}")
        if not all(isinstance(scope[access], (list, tuple)) for access in scope):
            raise ValueError(f"Resource scopes must be lists: {key}")
        reads = list(dict.fromkeys([_file_resource(contract_path)] +
                                   [_file_resource(path) for path in scope["reads"]]))
        writes = list(dict.fromkeys(_file_resource(path) for path in scope["writes"]))
        for resource in writes:
            if not Path(resource[5:]).is_relative_to(run_dir):
                raise ValueError(f"Stage output must stay within run directory: {resource}")
        graph_nodes.append({
            "id": key, "algorithm": "command.run", "phase": "work",
            "inputs": {}, "reads": reads, "writes": writes, "max_visits": 1,
            "parameters": {
                "argv": [executable, "-B", str(stages_path), "--stage", stage,
                         "--pass", str(pass_index), "--run-dir", str(run_dir),
                         "--contract", str(contract_path)],
                "cwd": str(ROOT), "timeout": 60, "code_files": frozen,
            },
            "edges": [
                _edge(parsed, _equal(key + ".exit_code", 0)),
                _edge("@blocked", {"op": "ne", "args": [_ref(key + ".exit_code"), _literal(0)]}),
            ],
        })
        if validate:
            edges = [_edge("@complete", _equal(parsed + ".value.accepted", True)),
                     _edge("@blocked", _equal(parsed + ".value.accepted", False))]
        else:
            if diagnose:
                next_id = f"package_{pass_index}"
                repair_id = f"repair_{pass_index + 1}" if pass_index < max_repairs else "@blocked"
            else:
                repair_id = "@blocked"
            edges = [_edge(next_id, _equal(parsed + ".value.state", "ready")),
                     _edge(repair_id, _equal(parsed + ".value.state", "repairable")),
                     _edge("@blocked", _equal(parsed + ".value.state", "blocked"))]
        graph_nodes.append({
            "id": parsed, "algorithm": "json.select",
            "phase": "validation" if validate else "work",
            "inputs": {"document": _ref(key + ".stdout")},
            "parameters": {"path": []}, "max_visits": 1, "edges": edges,
        })

    add_stage("inputs", 0, "geometry_0")
    add_stage("geometry", 0, "material_0")
    add_stage("material", 0, "raster_0")
    for pass_index in range(max_repairs + 1):
        if pass_index:
            add_stage("repair", pass_index, f"raster_{pass_index}")
        for stage, following in (("raster", "shade"), ("shade", "pixel"), ("pixel", "diagnose")):
            add_stage(stage, pass_index, f"{following}_{pass_index}")
        add_stage("diagnose", pass_index, diagnose=True)
        add_stage("package", pass_index, f"validate_{pass_index}")
        add_stage("validate", pass_index, validate=True)
    acceptance = {"op": "any", "args": [
        _equal(f"validate_{pass_index}_json.value.accepted", True)
        for pass_index in range(max_repairs + 1)
    ]}
    return {
        "goal": "Execute source-driven pixel construction and bounded repair; await visual review after technical validation.",
        "entry": "inputs_0", "max_steps": len(graph_nodes), "nodes": graph_nodes,
        "requirements": [{
            "id": "technical_artifact_checks",
            "text": "The selected pass package passes the final executable content checks. Visual acceptance remains pending.",
            "source": str(contract_path), "predicate": acceptance,
        }],
    }


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def initialize(run_dir, contract_path, stages_path=None, code_files=(), max_repairs=2):
    """Initialize once. Never replace an earlier execution state or graph."""
    run_dir = Path(run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    state_path = run_dir / "workflow-state.json"
    graph_path = run_dir / "workflow-graph.json"
    contract_path = Path(contract_path).resolve(strict=True)
    stages_path = Path(stages_path or Path(__file__).with_name("stages.py")).resolve(strict=True)
    with work_loop.locked(state_path):
        if state_path.exists() or graph_path.exists():
            raise ValueError("Existing graph/state is preserved. Continue it with run or resume.")
        stages_module = _load_module(stages_path, "pixel_pipeline_stages_for_graph")
        resolver = getattr(stages_module, "stage_resources", None)
        if not callable(resolver):
            raise ValueError("The stages module must define stage_resources(stage, pass_index, run_dir, contract_path).")
        spec = build_graph(run_dir, contract_path, stages_path, resolver, code_files, max_repairs)
        graph = work_loop.compile_graph(spec)
        state = {
            "version": 2, "graph": graph, "graph_hash": work_loop.digest(graph),
            "engine_hash": _sha256(ENGINE_PATH), "cursor": graph["entry"],
            "results": {}, "events": [], "transitions": [], "steps": 0,
            "visits": {}, "resources": {}, "pending": None, "active": None,
            "paused": False, "complete": False, "halt": None,
            "pixel_pipeline": {
                "contract_path": str(contract_path), "contract_sha256": _sha256(contract_path),
                "stages_path": str(stages_path), "run_dir": str(run_dir),
                "max_repairs": max_repairs,
            },
        }
        work_loop.save(graph_path, spec)
        work_loop.save(state_path, state)
    return summarize(state, state_path)


def recover(run_dir, from_stage, pass_index):
    """Freeze an explicit new contract at a confirmed failed command.

    This does not execute stages. Successful artifacts are verified through the
    stages module's common.verify_receipt function and reused unchanged. The old
    graph, state and failed command outputs remain in recovery-history.
    """
    return _restart(run_dir, from_stage, pass_index)


def reopen(run_dir, from_stage, pass_index, evidence_path):
    """Reopen completed technical validation after a recorded boundary defect."""
    return _restart(run_dir, from_stage, pass_index, evidence_path=Path(evidence_path))


def _restart(run_dir, from_stage, pass_index, evidence_path=None):
    opening = evidence_path is not None
    run_dir = Path(run_dir).resolve(strict=True)
    state_path = run_dir / "workflow-state.json"
    graph_path = run_dir / "workflow-graph.json"
    key = f"{from_stage}_{pass_index}"
    with work_loop.locked(state_path):
        old = work_loop.load_state(state_path)
        if opening and (not old["complete"] or old["halt"] or old["active"] or old["pending"]):
            raise ValueError("Reopening requires a completed technical validation state.")
        if not opening and (old["active"] or old["pending"] or old["complete"] or not old["halt"]):
            raise ValueError("Recovery requires a confirmed failed command, not uncertain or completed execution.")
        table = work_loop.nodes(old["graph"])
        failed = old["results"].get(key)
        if opening:
            accepted = old["results"].get(f"validate_{pass_index}_json", {}).get("output", {}).get("value", {})
            parsed = old["results"].get(key + "_json", {}).get("output", {}).get("value", {})
            if (from_stage != "diagnose" or failed is None or failed["output"].get("exit_code") != 0
                    or parsed.get("state") != "ready" or accepted.get("accepted") is not True):
                raise ValueError("Reopen from-stage/pass must identify the completed pass's diagnose stage.")
        elif (old["cursor"] != key or key not in table or table[key]["algorithm"] != "command.run"
                or failed is None or failed["output"].get("exit_code", 0) == 0):
            raise ValueError("from-stage/pass must match the current command with a nonzero exit code.")
        evidence = None
        if opening:
            evidence_path = evidence_path.resolve(strict=True)
            evidence = work_loop.read_json(evidence_path)
            if not isinstance(evidence, dict):
                raise ValueError("Reopening evidence must be a JSON object.")
            files = evidence.get("files")
            if (evidence.get("reason") != "BOUNDARY_DOUBLE_STROKE"
                    or not isinstance(files, dict) or not files):
                raise ValueError("Reopening needs BOUNDARY_DOUBLE_STROKE evidence with target file hashes.")
            current_pass = run_dir / f"pass-{pass_index}"
            relevant = False
            for name, expected in files.items():
                target = Path(name)
                if not target.is_absolute() or not target.resolve().is_relative_to(run_dir):
                    raise ValueError("Evidence target files must be absolute paths inside the run directory.")
                if not target.is_file() or _sha256(target) != expected:
                    raise ValueError(f"STALE_EVIDENCE: {target}")
                relevant |= target.resolve().is_relative_to(current_pass)
            if not relevant:
                raise ValueError("Evidence must include an artifact from the completed target pass.")
        metadata = old["pixel_pipeline"]
        contract_path = Path(metadata["contract_path"])
        if _sha256(contract_path) != metadata["contract_sha256"]:
            raise ValueError("The original contract changed; recovery cannot reuse its existing artifacts.")
        stages_path = Path(metadata["stages_path"])
        stages = _load_module(stages_path, "pixel_pipeline_stages_for_recovery")
        verify = getattr(stages, "verify_receipt", None)
        if not callable(verify):
            raise ValueError("The stages module must expose common.verify_receipt for recovery.")

        verified = []
        protected = set()
        inherited = metadata.get("recovery_record")
        if inherited:
            previous = work_loop.read_json(inherited)
            for item in previous["verified_receipts"]:
                receipt_path = Path(item["path"]).resolve()
                if not receipt_path.is_relative_to(run_dir) or _sha256(receipt_path) != item["sha256"]:
                    raise ValueError("A previously reused stage receipt changed.")
                receipt = verify(receipt_path)
                protected.add(receipt_path)
                protected.update(Path(path).resolve() for bucket in ("inputs", "outputs") for path in receipt[bucket])
                verified.append(item)
        prior_commands = sorted(((node_key, result) for node_key, result in old["results"].items()
                                 if table[node_key]["algorithm"] == "command.run"
                                 and result["revision"] < failed["revision"]),
                                key=lambda pair: pair[1]["revision"])
        for node_key, result in prior_commands:
            parsed = old["results"].get(node_key + "_json", {}).get("output", {}).get("value", {})
            if result["output"].get("exit_code") != 0 or parsed.get("state") not in {"ready", "repairable"}:
                raise ValueError(f"Prior command is not a successful reusable stage: {node_key}")
            stage, number = node_key.rsplit("_", 1)
            scope = stages.stage_resources(stage, int(number), run_dir, contract_path)
            candidates = set()
            for output in scope["writes"]:
                output = Path(output).resolve()
                directory = output if output.is_dir() else output.parent
                candidate = directory / "stage_receipt.json"
                if candidate.is_file():
                    candidates.add(candidate)
            if len(candidates) != 1:
                raise ValueError(f"Expected one existing stage receipt for {node_key}")
            receipt_path = candidates.pop()
            if not receipt_path.is_relative_to(run_dir):
                raise ValueError("A reusable stage receipt is outside the run directory.")
            receipt = verify(receipt_path)
            if receipt.get("stage") != stage or not receipt.get("inputs") or not receipt.get("outputs"):
                raise ValueError(f"Incomplete stage receipt: {receipt_path}")
            protected.add(receipt_path)
            protected.update(Path(path).resolve() for bucket in ("inputs", "outputs") for path in receipt[bucket])
            verified.append({"node": node_key, "path": str(receipt_path), "sha256": _sha256(receipt_path)})

        # Follow the frozen file-resource dependencies to ensure that recovery
        # cannot bypass an earlier producer which never completed.
        required, pending = set(), [key]
        while pending:
            consumer = pending.pop()
            for producer, node in table.items():
                if (producer != key and producer not in required and node["algorithm"] == "command.run"
                        and set(node["writes"]).intersection(table[consumer]["reads"])):
                    required.add(producer)
                    pending.append(producer)
        missing = required - {item["node"] for item in verified}
        if missing:
            raise ValueError("Missing successful prerequisite receipts: " + ", ".join(sorted(missing)))
        restarted_stages = ("diagnose", "package", "validate") if opening else (from_stage,)
        new_writes = set()
        for stage in restarted_stages:
            stage_key = f"{stage}_{pass_index}"
            scope = stages.stage_resources(stage, pass_index, run_dir, contract_path)
            old_writes = {Path(resource[5:]).resolve() for resource in table[stage_key]["writes"]}
            actual_writes = {Path(path).resolve() for path in scope["writes"]}
            if actual_writes != old_writes:
                raise ValueError("The restarted stage's output scope changed; automatic recovery is not applicable.")
            new_writes.update(actual_writes)
        preserve = []
        for output in sorted(new_writes, key=lambda path: len(path.parts)):
            if output == run_dir or not output.is_relative_to(run_dir):
                raise ValueError(f"Failed output is outside the permitted run directory: {output}")
            if any(path == output or path.is_relative_to(output) for path in protected):
                raise ValueError(f"Failed output overlaps a verified artifact: {output}")
            if output.exists() and not any(output.is_relative_to(parent) for parent in preserve):
                preserve.append(output)

        code_files = table[key]["parameters"]["code_files"]
        spec = build_graph(run_dir, contract_path, stages_path, stages.stage_resources,
                           code_files, metadata["max_repairs"])
        spec["entry"] = key
        graph = work_loop.compile_graph(spec)
        previous_hashes = table[key]["parameters"]["code_hashes"]
        recovery_hashes = work_loop.nodes(graph)[key]["parameters"]["code_hashes"]
        changed_code = [path for path, value in recovery_hashes.items()
                        if previous_hashes.get(path) != value and Path(path).resolve() != Path(__file__).resolve()]
        if not changed_code:
            raise ValueError("No stage/helper code changed; recovery cannot repeat the same failed algorithm.")
        history_root = (run_dir / ("reopening-history" if opening else "recovery-history")).resolve()
        if not history_root.is_relative_to(run_dir):
            raise ValueError("Recovery history resolves outside the run directory.")
        sequence = 1
        while (history_root / f"{sequence:04d}").exists():
            sequence += 1
        history = history_root / f"{sequence:04d}"
        moves = [(output, history / ("completed-output" if opening else "failed-output") / output.relative_to(run_dir))
                 for output in preserve]
        if any(not destination.resolve().is_relative_to(history.resolve()) for _, destination in moves):
            raise ValueError("A failed output archive resolves outside its recovery directory.")
        record = {
            "entry_node": key, "kind": "reopen" if opening else "recover", "previous_graph_hash": old["graph_hash"],
            "previous_state_sha256": _sha256(state_path), "previous_graph_sha256": _sha256(graph_path),
            "verified_receipts": verified,
            "previous_code_hashes": previous_hashes, "recovery_code_hashes": recovery_hashes,
            "changed_algorithm_files": changed_code,
            "preserved_completed_outputs" if opening else "preserved_failed_outputs":
                [{"from": str(source), "to": str(destination)} for source, destination in moves],
        }
        record["reopened_node" if opening else "failed_node"] = key
        if opening:
            record["evidence"] = {"source": str(evidence_path), "sha256": _sha256(evidence_path),
                                  "reason": evidence["reason"], "files": evidence["files"]}
        record_path = history / ("reopening.json" if opening else "recovery.json")
        state = {
            "version": 2, "graph": graph, "graph_hash": work_loop.digest(graph),
            "engine_hash": _sha256(ENGINE_PATH), "cursor": key, "results": {},
            "events": [], "transitions": [], "steps": 0, "visits": {}, "resources": {},
            "pending": None, "active": None, "paused": False, "complete": False, "halt": None,
            "pixel_pipeline": {**metadata, "recovery_record": str(record_path)},
        }
        # All validation and compilation precede the first filesystem mutation.
        history.mkdir(parents=True)
        shutil.copy2(state_path, history / state_path.name)
        shutil.copy2(graph_path, history / graph_path.name)
        work_loop.save(record_path, record)
        if opening:
            shutil.copy2(evidence_path, history / "evidence.json")
        for source, destination in moves:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
        work_loop.save(graph_path, spec)
        work_loop.save(state_path, state)
    report = summarize(state, state_path)
    report["reopening_record" if opening else "recovery_record"] = str(record_path)
    report["verified_prior_stages"] = [item["node"] for item in verified]
    return report


def summarize(state, state_path):
    report = work_loop.describe(state)
    report["state_path"] = str(state_path)
    report["status"] = "awaiting_visual_review" if state["complete"] else report["action"]
    report["visual_acceptance"] = "pending"
    last = sorted(state["results"].items(), key=lambda pair: pair[1]["revision"], reverse=True)
    for key, result in last:
        if key.endswith("_json") and work_loop.fresh(state, key):
            report["last_stage"] = key[:-5]
            report["stage_result"] = result["output"]["value"]
            break
    return report


def continue_run(run_dir, *, resume=False, contract_path=None):
    state_path = Path(run_dir).resolve() / "workflow-state.json"
    with work_loop.locked(state_path):
        state = work_loop.load_state(state_path)
        metadata = state["pixel_pipeline"]
        frozen_contract = Path(metadata["contract_path"])
        if contract_path is not None and Path(contract_path).resolve() != frozen_contract:
            raise ValueError("The supplied contract path differs from the frozen contract.")
        if _sha256(frozen_contract) != metadata["contract_sha256"]:
            raise ValueError("Contract content changed. Existing execution is preserved for review.")
        if resume:
            state["paused"] = False
        work_loop.execute(state, state_path)
        return summarize(state, state_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "run", "resume", "status", "recover", "reopen"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--stages", type=Path)
    parser.add_argument("--code-file", type=Path, action="append", default=[])
    parser.add_argument("--max-repairs", type=int, choices=range(3), default=2)
    parser.add_argument("--from-stage")
    parser.add_argument("--pass", dest="pass_index", type=int, default=0)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args(argv)
    state_path = args.run_dir.resolve() / "workflow-state.json"
    if args.command == "reopen":
        if args.from_stage is None or args.pass_index < 0 or args.evidence is None:
            parser.error("reopen requires --from-stage, a nonnegative --pass and --evidence")
        return reopen(args.run_dir, args.from_stage, args.pass_index, args.evidence)
    if args.command == "recover":
        if args.from_stage is None or args.pass_index < 0:
            parser.error("recover requires --from-stage and a nonnegative --pass")
        return recover(args.run_dir, args.from_stage, args.pass_index)
    if args.command == "status":
        return summarize(work_loop.load_state(state_path), state_path)
    if args.command == "init" or (args.command == "run" and not state_path.exists()):
        if args.contract is None:
            parser.error("--contract is required to initialize a run")
        result = initialize(args.run_dir, args.contract, args.stages, args.code_file, args.max_repairs)
        if args.command == "init":
            return result
    return continue_run(args.run_dir, resume=args.command == "resume", contract_path=args.contract)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"status": "error", "message": str(error)}, ensure_ascii=False))
        sys.exit(2)
