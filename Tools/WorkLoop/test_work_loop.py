"""Final contract checks; synthetic evidence never invokes a media/Unity provider."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("work_loop.py")


def task(key, phase="work", deps=(), req="R"):
    return dict(id=key, requirement=req, question="What observable result is needed?",
                contribution="Satisfy the named requirement", phase=phase, depends_on=list(deps))


class WorkLoopContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / "state.json"
        self.addCleanup(self.temp.cleanup)

    def call(self, command, data=None, ok=True):
        args = [sys.executable, "-B", str(SCRIPT), command, str(self.state)]
        if isinstance(data, dict):
            source = self.root / "input.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            args.append(str(source))
        elif data is not None:
            args.append(data)
        before = self.state.read_bytes() if self.state.exists() else None
        result = subprocess.run(args, capture_output=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        if not ok:
            self.assertEqual(self.state.read_bytes() if self.state.exists() else None, before)
        return json.loads(result.stdout)

    def init(self, kind="generated", tasks=None, **extra):
        spec = dict(goal="Synthetic controller contract, not real generation",
                    requirements=[dict(id="R", text="Required observable result", evidence_kind=kind)],
                    tasks=tasks or [task("work"), task("check", "validation", ["work"])])
        return self.call("init", {**spec, **extra})

    def finish(self, key, evidence=None, **extra):
        report = dict(task=key, status="done", observation="Synthetic tool outcome",
                      feedback="Continue only remaining necessary work")
        if evidence:
            report["evidence"] = evidence
        return self.call("submit", {**report, **extra})

    @staticmethod
    def generated(key="G"):
        return dict(id=key, kind="generated", ref="fixture-output", receipt="fixture-only-receipt")

    def test_normal_progress_pause_resume_and_final_only(self):
        self.init()
        self.call("start", "check", ok=False)
        self.call("stop")
        self.call("start", "work", ok=False)
        self.call("resume")
        self.call("start", "work")
        self.assertEqual(self.call("next")["action"], "resume")
        self.assertEqual(self.finish("work", [self.generated()])["action"], "final_validation")
        self.call("start", "check")
        self.assertEqual(self.finish("check", uses=["G"], verdict="pass")["action"], "protocol_complete")

    def test_gif_roundtrip_cannot_meet_fresh_generation(self):
        self.init()
        self.call("start", "work")
        self.finish("work", [dict(id="old", kind="imported", ref="old.gif"),
                             dict(id="frames", kind="transformed", ref="frames", parents=["old"]),
                             dict(id="gif", kind="transformed", ref="again.gif", parents=["frames"])])
        self.call("start", "check")
        self.call("submit", dict(task="check", status="done", observation="Same decoded pixels",
                                 feedback="No fresh generation evidence", uses=["gif"], verdict="pass"), ok=False)
        self.assertEqual(self.finish("check", uses=["gif"], verdict="fail")["action"], "needs_plan")

    def test_pruning_does_not_delete_acceptance_and_cycle_is_atomic(self):
        self.init()
        self.call("submit", dict(feedback="Invalid cyclic branch",
                                 add=[task("a", deps=["b"]), task("b", deps=["a"])]), ok=False)
        result = self.call("submit", dict(feedback="Both tasks were unnecessary",
                                          drop=[dict(id="work", reason="Prune"), dict(id="check", reason="Prune")]))
        self.assertEqual(result["action"], "needs_plan")
        self.assertEqual(result["unmet"][0]["id"], "R")

    def test_feedback_reopens_related_check(self):
        self.init()
        self.call("start", "work")
        self.finish("work", [self.generated()])
        self.call("start", "check")
        self.finish("check", uses=["G"], verdict="pass")
        result = self.call("submit", dict(feedback="New evidence requires a repair", add=[task("repair")]))
        self.assertEqual(result["action"], "choose_work")
        self.call("start", "check", ok=False)
        self.call("start", "repair")
        self.finish("repair", [dict(id="repair-log", kind="execution", ref="fixture-log")])
        self.assertEqual(self.call("next")["action"], "final_validation")

    def test_work_cannot_be_added_while_validation_is_running(self):
        self.init(requirements=[dict(id="R", text="Main", evidence_kind="generated"),
                                dict(id="R2", text="Other", evidence_kind="execution")])
        self.call("start", "work")
        self.finish("work", [self.generated()])
        self.call("start", "check")
        self.call("submit", dict(feedback="New branch", add=[task("extra", req="R2")]), ok=False)

    def test_stale_ancestor_is_rejected_even_without_task_dependency(self):
        tasks = [task("source"), task("transform", req="R2"), task("check", "validation", req="R2")]
        self.init(tasks=tasks, requirements=[dict(id="R", text="Source", evidence_kind="generated"),
                                           dict(id="R2", text="Output", evidence_kind="transformed")])
        self.call("start", "source")
        self.finish("source", [self.generated()])
        self.call("start", "transform")
        self.finish("transform", [dict(id="T", kind="transformed", ref="fixture", parents=["G"])])
        self.call("start", "check")
        self.finish("check", uses=["T"], verdict="pass")
        self.call("submit", dict(feedback="Source changed", reopen=[dict(id="source", reason="New source")]))
        self.call("start", "source")
        self.finish("source", [self.generated("G2")])
        result = self.call("next")
        self.assertEqual(result["action"], "needs_plan")
        self.assertIn("check", result["unresolved_tasks"])

    def test_missing_receipt_and_evidence_do_not_finish_work(self):
        self.init()
        self.call("start", "work")
        for evidence in ([], [dict(id="G", kind="generated", ref="fixture")]):
            self.call("submit", dict(task="work", status="done", observation="Claim only", feedback="Continue",
                                     evidence=evidence), ok=False)

    def test_failed_validation_repair_and_budget_stop(self):
        self.init(kind="execution", max_starts=3)
        self.call("start", "work")
        self.finish("work", [dict(id="log", kind="execution", ref="fixture")])
        self.call("start", "check")
        self.finish("check", uses=["log"], verdict="fail", add=[task("repair")])
        self.call("start", "repair")
        result = self.finish("repair", [dict(id="fixed", kind="execution", ref="fixture")])
        self.assertEqual(result["action"], "budget_stop")
        self.call("start", "check", ok=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
