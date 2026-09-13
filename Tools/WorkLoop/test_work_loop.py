"""End-of-change contract cases. No Unity, provider, network or paid model calls."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("work_loop.py")


def literal(value):
    return {"literal": value}


def ref(path):
    return {"ref": path}


def check(op, *args):
    return {"op": op, "args": list(args)}


def edge(target, condition=None, **extra):
    return {"to": target, "when": condition or check("eq", literal(1), literal(1)), **extra}


def node(key, algorithm, inputs, edges, phase="work", parameters=None, **extra):
    return dict(id=key, algorithm=algorithm, phase=phase, inputs=inputs, edges=edges,
                parameters=parameters or {}, **extra)


def graph(worker=False):
    calc = node("sum", "math.reduce", {"values": literal([12, 18, 20])},
                [edge("worker" if worker else "check")], parameters={"op": "sum"})
    verify = node("check", "value.compare",
                  {"left": ref("worker.candidate" if worker else "sum.value"), "right": literal(50)},
                  [edge("@complete", check("eq", ref("check.value"), literal(True))),
                   edge("worker" if worker else "@blocked", check("eq", ref("check.value"), literal(False)), feedback=True)],
                  phase="validation", parameters={"op": "eq"})
    items = [calc, verify]
    if worker:
        items.insert(1, node("worker", "ai.map",
                             {"values": literal([12, 18, 20]), "previous": {"feedback_ref": "check.value", "default": None}},
                             [edge("check")], question="Return only the numeric candidate.",
                             output_schema={"candidate": {"type": "number", "min": 0, "max": 100}}))
    return dict(goal="Synthetic algorithm contract", entry="sum", nodes=items,
                requirements=[dict(id="R", text="Total must be 50", source="Fixed arithmetic fixture",
                                   predicate=check("eq", ref("check.value"), literal(True)))])


class GraphContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / "state.json"
        self.addCleanup(self.temp.cleanup)

    def call(self, command, data=None, ok=True):
        argv = [sys.executable, "-B", str(SCRIPT), command, str(self.state)]
        if data is not None:
            source = self.root / "input.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            argv.append(str(source))
        before = self.state.read_bytes() if self.state.exists() else None
        result = subprocess.run(argv, capture_output=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        if not ok:
            self.assertEqual(self.state.read_bytes() if self.state.exists() else None, before)
        return json.loads(result.stdout)

    def answer(self, prompt, value):
        return self.call("submit", dict(ticket=prompt["ticket"], output={"candidate": value}))

    def test_algorithms_run_continuously_without_ai(self):
        self.call("init", graph())
        result = self.call("run")
        self.assertEqual((result["action"], result["steps"]), ("graph_complete", 2))
        self.assertEqual(json.loads(self.state.read_text())["results"]["sum"]["output"]["value"], 50)

    def test_ai_cannot_submit_control_or_wrong_output(self):
        self.call("init", graph(True))
        prompt = self.call("run")
        self.assertEqual(prompt["action"], "compute_unit")
        for event in (dict(ticket=prompt["ticket"], output={"candidate": 50}, verdict="pass"),
                      dict(ticket=prompt["ticket"], output={"candidate": 50, "next": "@complete"}),
                      dict(ticket="stale", output={"candidate": 50}),
                      dict(ticket=prompt["ticket"], output={"candidate": True})):
            self.call("submit", event, ok=False)
        self.assertEqual(self.answer(prompt, 50)["action"], "graph_complete")

    def test_feedback_is_graph_controlled_and_repeated_input_stops(self):
        self.call("init", graph(True))
        first = self.call("run")
        repair = self.answer(first, 40)
        self.assertEqual((repair["action"], repair["inputs"]["previous"]), ("compute_unit", False))
        result = self.answer(repair, 40)
        self.assertEqual(result["reason"], "unchanged_feedback_loop")

    def test_corrected_candidate_reaches_final_verifier(self):
        self.call("init", graph(True))
        repair = self.answer(self.call("run"), 40)
        self.assertEqual(self.answer(repair, 50)["action"], "graph_complete")

    def test_ambiguous_unknown_and_no_matching_guards(self):
        for expected, edges in (
            ("ambiguous_guard", [edge("check"), edge("@blocked")]),
            ("unknown_guard", [edge("check"), edge("@blocked", check("eq", ref("check.value"), literal(True)))]),
            ("no_matching_edge", [edge("check", check("eq", literal(1), literal(2)))])):
            with self.subTest(expected=expected):
                self.state = self.root / (expected + ".json")
                spec = graph()
                spec["nodes"][0]["edges"] = edges
                self.call("init", spec)
                self.assertEqual(self.call("run")["reason"], expected)

    def test_terminal_cannot_override_requirements(self):
        spec = graph()
        spec["requirements"][0]["predicate"] = check("eq", ref("check.value"), literal(False))
        self.call("init", spec)
        self.assertIn("unmet_requirements", self.call("run")["reason"])

    def test_algorithm_id_and_validation_authority_are_checked_before_execution(self):
        for changes in ({"algorithm": "freeform.do_everything"}, {"phase": "validation"}):
            spec = graph(True)
            spec["nodes"][1].update(changes)
            self.call("init", spec, ok=False)
        spec = graph()
        spec["nodes"][0]["edges"] = [edge("@complete")]
        self.call("init", spec, ok=False)

    def test_file_change_invalidates_old_observation(self):
        source = self.root / "input.bin"
        source.write_bytes(b"A")
        spec = graph(True)
        spec["nodes"][0] = node("sum", "file.inspect", {"path": literal(str(source))}, [edge("worker")])
        spec["nodes"][-1]["inputs"] = {"left": ref("sum.size"), "right": literal(1)}
        self.call("init", spec)
        prompt = self.call("run")
        source.write_bytes(b"changed")
        self.assertIn("missing_input", self.answer(prompt, 50)["reason"])

    def command_graph(self, code, timeout=5, writes=None):
        helper = self.root / "helper.py"
        helper.write_text(code, encoding="utf-8")
        spec = graph()
        spec["nodes"][0] = node("sum", "command.run", {}, [edge("check")],
                               parameters={"argv": [sys.executable, str(helper)], "timeout": timeout,
                                           "code_files": [str(helper)]}, reads=[], writes=writes or [])
        spec["nodes"][1]["inputs"] = {"left": ref("sum.exit_code"), "right": literal(0)}
        return spec

    def test_real_process_result_and_code_pin(self):
        self.call("init", self.command_graph("print('actual execution')"))
        self.assertEqual(self.call("run")["action"], "graph_complete")
        result = json.loads(self.state.read_text())["results"]["sum"]["output"]
        self.assertEqual(result["stdout"].strip(), "actual execution")
        self.state = self.root / "changed-code.json"
        self.call("init", self.command_graph("print('before')"))
        (self.root / "helper.py").write_text("print('after')", encoding="utf-8")
        self.assertEqual(self.call("run")["action"], "uncertain_execution")

    def test_command_can_rerun_when_declared_file_input_really_changes(self):
        source = self.root / "source.txt"
        source.write_text("bad", encoding="utf-8")
        spec = self.command_graph(f"from pathlib import Path\nprint(Path({str(source)!r}).read_text())")
        spec["nodes"][0]["reads"] = ["file:" + str(source)]
        spec["nodes"][1]["inputs"] = {"left": ref("sum.stdout"), "right": literal("good\n")}
        spec["nodes"][1]["edges"][1]["to"] = "worker"
        spec["nodes"].append(node("worker", "ai.map", {}, [edge("sum")], question="Return the fixture acknowledgement.",
                                  output_schema={"candidate": {"type": "number"}}))
        self.call("init", spec)
        prompt = self.call("run")
        self.assertEqual(prompt["action"], "compute_unit")
        source.write_text("good", encoding="utf-8")
        self.assertEqual(self.answer(prompt, 0)["action"], "graph_complete")

    def test_process_timeout_and_output_failure_never_auto_replay(self):
        for name, code, timeout in (("timeout", "import time; time.sleep(0.2)", 0.02),
                                    ("output", "print('x' * 300000)", 5)):
            with self.subTest(name=name):
                self.state = self.root / (name + ".json")
                self.call("init", self.command_graph(code, timeout))
                self.assertEqual(self.call("run")["action"], "uncertain_execution")
                before = self.state.read_bytes()
                self.assertEqual(self.call("run")["action"], "uncertain_execution")
                self.assertEqual(self.state.read_bytes(), before)

    def test_pause_contract_tamper_budget_and_v1_preservation(self):
        spec = graph()
        spec["max_steps"] = 1
        self.call("init", spec)
        self.call("stop")
        self.assertEqual(self.call("run")["action"], "paused")
        self.call("resume")
        self.assertEqual(self.call("run")["reason"], "execution_budget")
        state = json.loads(self.state.read_text())
        state["graph"]["goal"] = "unapproved replacement"
        self.state.write_text(json.dumps(state), encoding="utf-8")
        self.call("run", ok=False)
        self.state = self.root / "legacy.json"
        self.state.write_text('{"version":1,"goal":"preserved"}', encoding="utf-8")
        self.call("run", ok=False)

    def test_declared_write_invalidates_even_restored_file_timestamp(self):
        source = self.root / "artifact.bin"
        source.write_bytes(b"A")
        timestamp = source.stat().st_mtime_ns
        code = ("from pathlib import Path\nimport os\n"
                f"p=Path({str(source)!r})\np.write_bytes(b'B')\nos.utime(p,ns=({timestamp},{timestamp}))\n")
        spec = self.command_graph(code, writes=["file:" + str(source)])
        spec["entry"] = "capture"
        spec["nodes"].insert(0, node("capture", "file.inspect", {"path": literal(str(source))},
                                    [edge("sum", feedback=True)], phase="validation"))
        spec["requirements"].append(dict(id="old", text="Old observation must not survive mutation", source="Fixture",
                                         predicate=check("eq", ref("capture.size"), literal(1))))
        self.call("init", spec)
        self.assertIn("unmet_requirements", self.call("run")["reason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
