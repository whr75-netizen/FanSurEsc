"""Execute small registered algorithms under a frozen procedural graph."""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

MISSING = object()
OPS = {"eq", "ne", "lt", "le", "gt", "ge"}
ALGORITHMS = {"value.identity", "math.reduce", "value.compare", "json.select",
              "file.inspect", "command.run", "ai.map"}
PURE = {"value.identity", "math.reduce", "value.compare", "json.select"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(packed(value).encode("utf-8")).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite JSON: " + value)))


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def compare(op, left, right):
    numeric = number(left) and number(right)
    need(numeric or type(left) is type(right), "비교 타입이 다릅니다.")
    if op in {"eq", "ne"}:
        equal = left == right if numeric else packed(left) == packed(right)
        return equal if op == "eq" else not equal
    need(numeric, "순서 비교에는 유한 수가 필요합니다.")
    return {"lt": lambda: left < right, "le": lambda: left <= right,
            "gt": lambda: left > right, "ge": lambda: left >= right}[op]()


def nodes(graph):
    return {node["id"]: node for node in graph["nodes"]}


def resource(key):
    need(isinstance(key, str) and key, "빈 자원 ID입니다.")
    return "file:" + os.path.normcase(str(Path(key[5:]).resolve())) if key.startswith("file:") else key


def unit_signature(state, node, inputs):
    observed = {}
    for key in node["reads"]:
        if key.startswith("file:"):
            try:
                hasher = hashlib.sha256()
                with Path(key[5:]).open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        hasher.update(chunk)
                observed[key] = hasher.hexdigest()
            except OSError:
                observed[key] = "unavailable"
        else:
            observed[key] = state["resources"].get(key, 0)
    return digest({"node": node["id"], "inputs": inputs, "parameters": node["parameters"], "reads": observed})


def references(value):
    if isinstance(value, dict):
        if "literal" in value:
            return set()
        if "ref" in value or "feedback_ref" in value:
            return {value.get("ref", value.get("feedback_ref")).split(".")[0]}
        return set().union(*(references(item) for item in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(references(item) for item in value)) if value else set()
    return set()


def operand_spec(value, feedback=False):
    need(isinstance(value, dict), "입력은 literal/ref 바인딩이어야 합니다.")
    if set(value) == {"literal"}:
        packed(value["literal"])
    elif set(value) == {"ref"}:
        need(isinstance(value["ref"], str) and value["ref"], "빈 ref입니다.")
    elif feedback and set(value) == {"feedback_ref", "default"}:
        need(isinstance(value["feedback_ref"], str) and value["feedback_ref"], "빈 feedback_ref입니다.")
    else:
        raise ValueError("허용되지 않는 입력 바인딩입니다.")


def guard_spec(expr):
    need(isinstance(expr, dict) and set(expr) == {"op", "args"}, "Guard에는 op/args만 허용합니다.")
    op, args = expr["op"], expr["args"]
    need(isinstance(args, list), "Guard args는 목록입니다.")
    if op in OPS or op == "known":
        need(len(args) == (1 if op == "known" else 2), "Guard 인수 개수가 다릅니다.")
        for arg in args:
            operand_spec(arg)
    else:
        need(op in {"all", "any", "not"} and len(args) > 0, "없는 Guard 연산입니다.")
        need(op != "not" or len(args) == 1, "not은 인수 하나입니다.")
        for arg in args:
            guard_spec(arg)


def schema_check(output, schema):
    need(isinstance(output, dict) and set(output) == set(schema), "AI 출력 필드가 계약과 다릅니다.")
    for key, rule in schema.items():
        value, kind = output[key], rule["type"]
        valid = {"number": number(value), "integer": type(value) is int,
                 "string": isinstance(value, str), "boolean": type(value) is bool,
                 "object": isinstance(value, dict), "array": isinstance(value, list)}[kind]
        need(valid, "AI 출력 타입 불일치: " + key)
        if "enum" in rule:
            need(any(type(value) is type(item) and value == item for item in rule["enum"]), "enum 불일치: " + key)
        if number(value):
            need(rule.get("min", -math.inf) <= value <= rule.get("max", math.inf), "수치 범위 불일치: " + key)
    need(len(packed(output).encode("utf-8")) <= 32768, "AI 출력은 32 KiB 이하입니다.")


def compile_graph(spec):
    need(set(spec) <= {"goal", "entry", "nodes", "requirements", "max_steps"}, "없는 그래프 필드입니다.")
    need(isinstance(spec["goal"], str) and spec["goal"].strip(), "goal이 필요합니다.")
    graph = json.loads(packed(spec))
    table = nodes(graph)
    need(table and len(table) == len(graph["nodes"]), "노드 ID가 중복되거나 비어 있습니다.")
    need(graph["entry"] in table, "없는 시작 노드입니다.")
    graph.setdefault("max_steps", 64)
    need(type(graph["max_steps"]) is int and 0 < graph["max_steps"] <= 1000, "max_steps는 1~1000입니다.")
    for key, node in table.items():
        need(isinstance(key, str) and key and "." not in key and not key.startswith("@"), "잘못된 노드 ID입니다.")
        need(set(node) <= {"id", "algorithm", "phase", "inputs", "parameters", "edges",
                          "on_error", "max_visits", "question", "output_schema", "reads", "writes"}, "없는 노드 필드: " + key)
        need(node["algorithm"] in ALGORITHMS, "등록되지 않은 알고리즘: " + node["algorithm"])
        need(node["phase"] in {"work", "validation"}, "phase가 잘못됐습니다.")
        node.setdefault("inputs", {})
        node.setdefault("parameters", {})
        node.setdefault("on_error", "@blocked")
        node.setdefault("max_visits", 3)
        if node["algorithm"] == "command.run":
            need("reads" in node and "writes" in node, "외부 명령은 reads/writes 자원 목록을 명시해야 합니다.")
        for access in ("reads", "writes"):
            need(isinstance(node.get(access, []), list), "자원은 목록입니다.")
            node[access] = [resource(item) for item in node.get(access, [])]
        need(node["algorithm"] == "command.run" or not node["writes"], "자원 변경은 등록된 외부 실행 단위만 가능합니다.")
        need(type(node["max_visits"]) is int and 0 < node["max_visits"] <= 100, "max_visits는 1~100입니다.")
        need(isinstance(node["parameters"], dict), "parameters는 객체입니다.")
        need(isinstance(node["inputs"], dict), "inputs는 객체입니다.")
        for binding in node["inputs"].values():
            operand_spec(binding, feedback=node["phase"] == "work")
        if node["algorithm"] == "ai.map":
            need(node["phase"] == "work", "AI는 validation 판정 알고리즘이 될 수 없습니다.")
            need(isinstance(node.get("question"), str) and node["question"].strip(), "AI 단위의 질문이 필요합니다.")
            schema = node.get("output_schema")
            need(isinstance(schema, dict) and schema, "AI 출력 schema가 필요합니다.")
            for rule in schema.values():
                need(isinstance(rule, dict) and rule.get("type") in
                     {"number", "integer", "string", "boolean", "object", "array"}, "지원하지 않는 schema입니다.")
        need(isinstance(node["edges"], list) and node["edges"], "명시적 전이 간선이 필요합니다.")
        for edge in node["edges"]:
            need(set(edge) <= {"when", "to", "feedback"}, "없는 간선 필드입니다.")
            guard_spec(edge["when"])
            target = edge["to"]
            need(target in table or target in {"@complete", "@blocked"}, "없는 전이 대상입니다.")
            if target == "@complete":
                need(node["phase"] == "validation", "완료는 마지막 validation에서만 가능합니다.")
            if target in table and node["phase"] == "validation" and table[target]["phase"] == "work":
                need(edge.get("feedback") is True, "검증→작업은 명시된 feedback 간선이어야 합니다.")
        need(node["on_error"] in table or node["on_error"] == "@blocked", "잘못된 on_error 대상입니다.")
        if node["algorithm"] == "command.run":
            params = node["parameters"]
            need(isinstance(params.get("argv"), list) and params["argv"] and
                 all(isinstance(arg, str) and arg for arg in params["argv"]), "고정 argv가 필요합니다.")
            need(number(params.get("timeout", 30)) and 0 < params.get("timeout", 30) <= 60, "timeout은 최대 60초입니다.")
            params.setdefault("code_files", [])
            need(isinstance(params["code_files"], list), "code_files는 고정할 알고리즘 파일 목록입니다.")
            node["parameters"]["code_hashes"] = {str(Path(p).resolve()): hashlib.sha256(Path(p).read_bytes()).hexdigest()
                                                   for p in params["code_files"]}
        used = references(node["inputs"]) | references(node["edges"])
        need(used <= table.keys(), "없는 데이터 참조: " + str(used - table.keys()))
    requirements = graph["requirements"]
    need(isinstance(requirements, list) and requirements, "요구 predicate가 필요합니다.")
    need(len({r["id"] for r in requirements}) == len(requirements), "요구 ID 중복입니다.")
    for req in requirements:
        need(set(req) == {"id", "text", "source", "predicate"}, "요구에는 id/text/source/predicate가 필요합니다.")
        need(all(isinstance(req[k], str) and req[k].strip() for k in ("id", "text", "source")), "빈 요구 정보입니다.")
        guard_spec(req["predicate"])
        used = references(req["predicate"])
        need(used <= table.keys() and any(table[key]["phase"] == "validation" for key in used),
             "요구 판정은 실제 validation 알고리즘 결과를 참조해야 합니다.")
    return graph


def fresh(state, key, seen=None):
    result = state["results"].get(key)
    if result is None:
        return False
    if any(state["resources"].get(key, 0) != revision for key, revision in result.get("resources", {}).items()):
        return False
    if "file_observation" in result:
        path, size, modified = result["file_observation"]
        try:
            current = Path(path).stat()
            if current.st_size != size or current.st_mtime_ns != modified:
                return False
        except OSError:
            return False
    seen = set() if seen is None else seen
    if key in seen:
        return False
    return all(dep not in seen and state["results"].get(dep, {}).get("revision") == revision
               and fresh(state, dep, seen | {key}) for dep, revision in result["dependencies"].items())


def field(value, path):
    for key in path:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return MISSING
    return value


def resolve(state, binding):
    if "literal" in binding:
        return binding["literal"]
    ref = binding.get("ref", binding.get("feedback_ref"))
    key, *path = ref.split(".")
    if "feedback_ref" in binding:
        result = state["results"].get(key)
        value = field(result["output"], path) if result else MISSING
        return binding["default"] if value is MISSING else value
    if not fresh(state, key):
        return MISSING
    return field(state["results"][key]["output"], path)


def guard(state, expr):
    op, args = expr["op"], expr["args"]
    if op in OPS or op == "known":
        values = [resolve(state, item) for item in args]
        if op == "known":
            return values[0] is not MISSING
        if any(value is MISSING for value in values):
            return None
        try:
            return compare(op, *values)
        except (ValueError, TypeError):
            return None
    values = [guard(state, item) for item in args]
    if op == "not":
        return None if values[0] is None else not values[0]
    if op == "all":
        return False if False in values else (None if None in values else True)
    return True if True in values else (None if None in values else False)


def algorithm(node, inputs):
    name, params = node["algorithm"], node["parameters"]
    if name == "value.identity":
        need(set(inputs) == {"value"}, "identity 입력은 value입니다.")
        return {"value": inputs["value"]}
    if name == "math.reduce":
        need(set(inputs) == {"values"}, "reduce 입력은 values입니다.")
        values = inputs["values"]
        need(isinstance(values, list) and values and all(number(v) for v in values), "유한 수 목록이 필요합니다.")
        op = params.get("op")
        need(op in {"sum", "mean", "min", "max"}, "등록되지 않은 통계 연산입니다.")
        value = {"sum": lambda: sum(values), "mean": lambda: sum(values) / len(values),
                 "min": lambda: min(values), "max": lambda: max(values)}[op]()
        need(number(value), "계산 결과가 유한 수가 아닙니다.")
        return {"value": value}
    if name == "value.compare":
        need(set(inputs) == {"left", "right"} and params.get("op") in OPS, "비교 계약이 잘못됐습니다.")
        return {"value": compare(params["op"], inputs["left"], inputs["right"])}
    if name == "json.select":
        need(set(inputs) == {"document"}, "select 입력은 document입니다.")
        document = inputs["document"]
        if isinstance(document, str):
            document = json.loads(document)
        need(isinstance(params.get("path"), list), "JSON 키 경로가 필요합니다.")
        result = field(document, params["path"])
        need(result is not MISSING, "JSON 경로를 찾지 못했습니다.")
        return {"value": result}
    if name == "file.inspect":
        need(set(inputs) == {"path"} and isinstance(inputs["path"], str), "파일 경로가 필요합니다.")
        path = Path(inputs["path"]).resolve(strict=True)
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        stat = path.stat()
        return {"path": str(path), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": hasher.hexdigest()}
    need(name == "command.run" and set(inputs) <= {"stdin"}, "알고리즘 입력 계약이 다릅니다.")
    for path, expected in params["code_hashes"].items():
        need(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "외부 알고리즘 코드 변경: " + path)
    result = subprocess.run(params["argv"], input=packed(inputs.get("stdin")), capture_output=True,
                            encoding="utf-8", errors="replace", shell=False,
                            cwd=params.get("cwd"), timeout=params.get("timeout", 30), check=False)
    need(len(result.stdout.encode("utf-8")) + len(result.stderr.encode("utf-8")) <= 262144, "명령 출력은 256 KiB 이하입니다.")
    return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def save(path, state):
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(packed(state))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def halt(state, reason):
    state["halt"] = reason


def finish_node(state, node, inputs, output, signature):
    packed(output)
    dependencies = {binding["ref"].split(".")[0]: state["results"][binding["ref"].split(".")[0]]["revision"]
                    for binding in node["inputs"].values() if "ref" in binding}
    state["steps"] += 1
    state["visits"][node["id"]] = state["visits"].get(node["id"], 0) + 1
    state["results"][node["id"]] = {"output": output, "dependencies": dependencies,
                                   "revision": state["steps"], "signature": signature,
                                   "resources": {key: state["resources"].get(key, 0) for key in node["reads"] + node["writes"]}}
    if node["algorithm"] == "file.inspect":
        state["results"][node["id"]]["file_observation"] = [output["path"], output["size"], output["mtime_ns"]]
        key = resource("file:" + output["path"])
        state["results"][node["id"]]["resources"][key] = state["resources"].get(key, 0)
    state["events"].append({"node": node["id"], "signature": signature, "output_hash": digest(output)})
    values = [guard(state, edge["when"]) for edge in node["edges"]]
    if None in values:
        halt(state, "unknown_guard")
        return
    if values.count(True) != 1:
        halt(state, "ambiguous_guard" if values.count(True) > 1 else "no_matching_edge")
        return
    target = node["edges"][values.index(True)]["to"]
    transition = digest({"signature": signature, "output": output, "to": target})
    if transition in state["transitions"]:
        halt(state, "unchanged_feedback_loop")
        return
    state["transitions"].append(transition)
    if target == "@complete":
        unmet = [r["id"] for r in state["graph"]["requirements"] if guard(state, r["predicate"]) is not True]
        if unmet:
            halt(state, "unmet_requirements: " + ", ".join(unmet))
        else:
            state["complete"] = True
    elif target == "@blocked":
        halt(state, "declared_block")
    else:
        state["cursor"] = target


def describe(state):
    base = {"goal": state["graph"]["goal"], "steps": state["steps"]}
    if state["paused"]:
        return {**base, "action": "paused"}
    if state["halt"]:
        return {**base, "action": "blocked", "reason": state["halt"]}
    if state["complete"]:
        return {**base, "action": "graph_complete", "message": "고정된 요구 판정식이 충족되었습니다. 실제 관측 범위로 결과를 보고하세요."}
    if state["active"]:
        return {**base, "action": "uncertain_execution", "node": state["active"]["node"],
                "message": "이미 시작한 외부 실행의 결과를 먼저 확인하세요. 자동 재실행하지 않습니다."}
    if state["pending"]:
        node = nodes(state["graph"])[state["cursor"]]
        return {**base, "action": "compute_unit", "node": node["id"], "algorithm": "ai.map",
                "ticket": state["pending"]["ticket"], "question": node["question"],
                "inputs": state["pending"]["inputs"], "output_schema": node["output_schema"],
                "instruction": "주어진 입력의 지정된 출력 후보만 JSON으로 계산하세요. 도구 실행·작업 선택·상태·합격·분기 변경 권한은 이 요청에 없습니다."}
    return {**base, "action": "ready", "node": state["cursor"], "message": "run으로 일반 알고리즘 구간을 연속 실행하세요."}


def execute(state, path):
    while not state["paused"] and not state["halt"] and not state["complete"] and not state["pending"] and not state["active"]:
        node = nodes(state["graph"])[state["cursor"]]
        if state["steps"] >= state["graph"]["max_steps"] or state["visits"].get(node["id"], 0) >= node["max_visits"]:
            halt(state, "execution_budget")
            break
        inputs = {key: resolve(state, binding) for key, binding in node["inputs"].items()}
        if any(value is MISSING for value in inputs.values()):
            halt(state, "missing_input: " + node["id"])
            break
        signature = unit_signature(state, node, inputs)
        repeated = any(event["node"] == node["id"] and event["signature"] == signature for event in state["events"])
        if repeated and node["algorithm"] in {"ai.map", "command.run"}:
            halt(state, "unchanged_input: " + node["id"])
            break
        if node["algorithm"] == "ai.map":
            state["pending"] = {"ticket": uuid.uuid4().hex, "inputs": inputs, "signature": signature}
            break
        state["active"] = {"node": node["id"], "signature": signature}
        for key in node["writes"]:
            state["resources"][key] = state["resources"].get(key, 0) + 1
        save(path, state)  # Persist before side effects; interruption never implies safe replay.
        try:
            prior = state["results"].get(node["id"])
            output = prior["output"] if node["algorithm"] in PURE and prior and prior["signature"] == signature else algorithm(node, inputs)
            finish_node(state, node, inputs, output, signature)
            state["active"] = None
        except subprocess.TimeoutExpired as error:
            # A remote effect may already have been submitted; a timeout is not a safe retry.
            state["events"].append({"node": node["id"], "signature": signature, "uncertain": str(error)})
        except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
            if node["algorithm"] == "command.run":
                state["events"].append({"node": node["id"], "signature": signature, "uncertain": str(error)})
                save(path, state)
                continue
            state["active"] = None
            state["steps"] += 1
            state["visits"][node["id"]] = state["visits"].get(node["id"], 0) + 1
            state["results"].pop(node["id"], None)
            state["events"].append({"node": node["id"], "signature": signature, "error": str(error)})
            if node["on_error"] == "@blocked":
                halt(state, "algorithm_error: " + str(error))
            else:
                state["cursor"] = node["on_error"]
        save(path, state)
    save(path, state)
    return describe(state)


def load_state(path):
    state = read_json(path)
    need(state.get("version") == 2, "v1/미지원 상태는 보존합니다. 명시적인 v2 계약과 새 상태가 필요합니다.")
    need(digest(state["graph"]) == state["graph_hash"], "고정 그래프 변경을 감지했습니다.")
    need(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == state["engine_hash"], "알고리즘 코드가 바뀌었습니다. 계약을 재검토하여 새 상태를 사용하세요.")
    return state


@contextmanager
def locked(path):
    lock = path.with_name(path.name + ".lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "next", "run", "submit", "stop", "resume"])
    parser.add_argument("state", type=Path)
    parser.add_argument("input", nargs="?")
    args = parser.parse_args()
    path = args.state.resolve()
    if args.command == "next":
        return describe(load_state(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with locked(path):
        if args.command == "init":
            need(not path.exists(), "기존 상태를 덮어쓰지 않습니다.")
            graph = compile_graph(read_json(args.input))
            state = {"version": 2, "graph": graph, "graph_hash": digest(graph),
                     "engine_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     "cursor": graph["entry"], "results": {}, "events": [], "transitions": [],
                     "steps": 0, "visits": {}, "resources": {}, "pending": None, "active": None,
                     "paused": False, "complete": False, "halt": None}
        else:
            state = load_state(path)
            if args.command == "run":
                return execute(state, path)
            if args.command == "submit":
                need(not state["paused"] and state["pending"] and not state["halt"], "현재 AI 출력 요청이 없습니다.")
                update = read_json(args.input)
                need(set(update) == {"ticket", "output"}, "AI는 ticket/output만 제출할 수 있습니다.")
                need(update["ticket"] == state["pending"]["ticket"], "현재 요청의 ticket이 아닙니다.")
                node = nodes(state["graph"])[state["cursor"]]
                schema_check(update["output"], node["output_schema"])
                inputs = state["pending"]["inputs"]
                signature = state["pending"]["signature"]
                current_inputs = {key: resolve(state, binding) for key, binding in node["inputs"].items()}
                need(not any(value is MISSING for value in current_inputs.values()) and
                     unit_signature(state, node, current_inputs) == signature,
                     "AI 계산 중 입력이 바뀌었습니다. 낡은 출력 후보를 승인하지 않습니다.")
                state["pending"] = None
                finish_node(state, node, inputs, update["output"], signature)
                save(path, state)
                return execute(state, path)
            state["paused"] = args.command == "stop"
        save(path, state)
        return describe(state)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        print(json.dumps({"action": "error", "message": str(error)}, ensure_ascii=False))
        sys.exit(2)
