"""Run a fixed Unity pixel-object recipe through the existing WorkLoop engine."""
import argparse
import json
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

import work_loop as engine

ROOT = Path(__file__).resolve().parents[2]
RECIPE = Path(__file__).parent / "recipes" / "pixel_object.json"


def literal(value):
    return {"literal": value}


def ref(value):
    return {"ref": value}


def compare(operation, left, right):
    return {"op": operation, "args": [left, right]}


def edge(target, condition):
    return {"to": target, "when": condition}


def invoke(*arguments):
    previous = sys.argv
    try:
        sys.argv = ["work_loop.py", *map(str, arguments)]
        return engine.main()
    finally:
        sys.argv = previous


def describe(result):
    if result.get("node") == "review" and result.get("action") == "work_unit":
        result = dict(result, action="awaiting_user_visual_feedback",
                      artisticApproval="pending", automationComplete=False)
    return result


def make_graph(task, pixel_size, output):
    recipe = engine.read_json(RECIPE)
    mechanism = recipe["mechanism"]
    engine.need(mechanism["minimumPixelSize"] <= pixel_size <= mechanism["maximumPixelSize"],
                "기존 렌더러의 pixelCellSize 범위는 1~8입니다.")
    contract = {"task": task, "requestedScreenPixelSize": pixel_size,
                "mechanism": mechanism, "recipeVersion": recipe["version"]}
    nodes = []
    for key, next_key, field in (("apply", "present", "readback"),
                                 ("present", "observe", "preview")):
        inputs = {"contract": literal(contract)}
        if key == "present":
            inputs["readback"] = ref("apply.readback")
        nodes.append({"id": key, "algorithm": "ai.work", "phase": "work",
                      "inputs": inputs, "parameters": {"scope": recipe[key]["scope"]},
                      "question": recipe[key]["assignment"],
                      "reads": ["file:" + str(RECIPE)],
                      "writes": ["unity:pixel-object-target", "file:" + str(output)],
                      "output_schema": {field: {"type": "string"}},
                      "edges": [edge(next_key, {"op": "known", "args": [ref(key + "." + field)]})]})
    nodes.append({"id": "observe", "algorithm": "command.run", "phase": "validation",
                  "inputs": {"stdin": ref("present.preview")},
                  "reads": ["file:" + str(RECIPE)],
                  "writes": ["file:" + str(output / "observations.json")],
                  "parameters": {"argv": [sys.executable, "-B", str(Path(__file__).resolve()),
                                           "_observe", str(output / "state.json")],
                                 "cwd": str(ROOT), "timeout": 30,
                                 "code_files": [str(Path(__file__).resolve()), str(RECIPE)]},
                  "edges": [dict(edge("review", compare("eq", ref("observe.exit_code"), literal(0))), feedback=True),
                            edge("@blocked", compare("ne", ref("observe.exit_code"), literal(0)))]})
    nodes.append({"id": "review", "algorithm": "ai.work", "phase": "work",
                  "inputs": {"preview": ref("present.preview"), "observations": ref("observe.stdout")},
                  "parameters": {"scope": recipe["review"]["scope"]},
                  "question": recipe["review"]["assignment"],
                  "reads": ["file:" + str(output / "observations.json")], "writes": [],
                  "output_schema": {"userFeedbackSource": {"type": "string"}},
                  "edges": [edge("@blocked", {"op": "known", "args": [ref("review.userFeedbackSource")]})]})
    return {"goal": task, "entry": "apply", "max_steps": 8, "nodes": nodes,
            "requirements": [{"id": "technical_observation", "text": "요청한 픽셀 크기와 실제 미리보기 출처를 보존합니다. 외형 승인을 뜻하지 않습니다.",
                              "source": "사용자 요청과 고정 pixel_object 레시피",
                              "predicate": compare("eq", ref("observe.exit_code"), literal(0))}]}


def observe(state_path):
    """Read actual files once; do not infer artistic quality from them."""
    state = engine.read_json(state_path)
    contract = state["results"]["apply"]["output"]
    readback_path = Path(contract["readback"]).resolve(strict=True)
    readback = engine.read_json(readback_path)
    requested = engine.nodes(state["graph"])["apply"]["inputs"]["contract"]["literal"]
    required = {"scene", "target", "pixelCellSize", "rendererFeature", "lightingPath", "shaderNames"}
    engine.need(required <= readback.keys(), "Unity readback 필드가 누락됐습니다: " + str(sorted(required - readback.keys())))
    engine.need(type(readback["pixelCellSize"]) is int and readback["pixelCellSize"] == requested["requestedScreenPixelSize"],
                "실제 Unity pixelCellSize가 요청과 다릅니다.")
    engine.need(readback["rendererFeature"] == requested["mechanism"]["rendererFeature"], "기존 캐릭터 픽셀 렌더 경로가 아닙니다.")
    for field in ("scene", "target", "lightingPath"):
        engine.need(isinstance(readback[field], str) and readback[field].strip(), "빈 Unity 관측: " + field)
    engine.need(isinstance(readback["shaderNames"], list) and readback["shaderNames"] and
                all(isinstance(name, str) and name.strip() for name in readback["shaderNames"]), "실제 shaderNames가 필요합니다.")
    preview_path = Path(json.load(sys.stdin)).resolve(strict=True)
    with preview_path.open("rb") as stream:
        header = stream.read(24)
    engine.need(len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR", "실제 PNG 미리보기가 필요합니다.")
    width, height = struct.unpack(">II", header[16:24])
    engine.need(width > 0 and height > 0, "빈 PNG입니다.")
    result = {"readback": engine.algorithm({"algorithm": "file.inspect", "parameters": {}}, {"path": str(readback_path)}),
              "preview": engine.algorithm({"algorithm": "file.inspect", "parameters": {}}, {"path": str(preview_path)}),
              "previewDimensions": [width, height], "unity": readback,
              "artisticApproval": "pending",
              "limits": "파일 존재·PNG 헤더·반환된 Unity 수치만 확인합니다. readback은 실제 Unity 도구에서 저장해야 하며 이 실행기가 Unity 호출의 진위를 증명하지는 않습니다."}
    engine.save(state_path.parent / "observations.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--task", required=True)
    start.add_argument("--pixel-size", required=True, type=int)
    start.add_argument("--run-dir", type=Path)
    for name in ("status", "stop", "resume", "submit", "_observe"):
        child = commands.add_parser(name)
        child.add_argument("state", type=Path)
        if name == "submit":
            child.add_argument("answer", type=Path, help="현재 단계의 output JSON; ticket은 실행기가 연결합니다.")
    args = parser.parse_args()
    if args.command == "start":
        engine.need(args.task.strip(), "작업 요청이 비어 있습니다.")
        output = (args.run_dir or ROOT / "LocalOnly" / "WorkLoop" /
                  datetime.now(timezone.utc).strftime("pixel-object-%Y%m%dT%H%M%S%fZ")).resolve()
        engine.need(not output.exists(), "새 run-dir을 지정하세요. 기존 계약과 결과는 보존합니다.")
        graph = make_graph(args.task, args.pixel_size, output)
        engine.compile_graph(graph)
        output.mkdir(parents=True)
        graph_path, state_path = output / "graph.json", output / "state.json"
        engine.save(graph_path, graph)
        invoke("init", state_path, graph_path)
        return dict(describe(invoke("run", state_path)), state=str(state_path))
    state_path = args.state.resolve()
    if args.command == "_observe":
        return observe(state_path)
    if args.command == "submit":
        state = engine.load_state(state_path)
        engine.need(state["cursor"] != "review", "사용자 시각 피드백 대기입니다. AI submit으로 통과하지 않습니다. 다음 사용자 정정은 새 계약으로 연결하세요.")
        engine.need(state["pending"] is not None, "현재 작업 인계가 없습니다.")
        answer = {"ticket": state["pending"]["ticket"], "output": engine.read_json(args.answer)}
        destination = state_path.parent / (state["cursor"] + "-answer.json")
        engine.need(not destination.exists(), "이 단계의 제출 기록이 이미 있습니다.")
        engine.save(destination, answer)
        return describe(invoke("submit", state_path, destination))
    action = "next" if args.command == "status" else args.command
    result = invoke(action, state_path)
    if args.command == "resume":
        result = invoke("run", state_path)
    return describe(result)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"action": "error", "message": str(error)}, ensure_ascii=False))
        sys.exit(2)
