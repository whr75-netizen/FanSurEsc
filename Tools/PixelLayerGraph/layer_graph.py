"""Deterministic Hierarchical Pixel Layer Graph Executor & GPU Pass Compiler.

Designed specifically to eliminate GPT-6.2 Sol / GPT-6.2 Astra / Codex Dot failure modes:
1. Moves pipeline authority out of AI chat memory into a frozen, SHA-256 disk state machine.
2. Supports arbitrarily deep nested layer trees (20~50+ layers: 1, 2-1, 3-2-3-1, ...) while
   compiling them into minimal physical GPU passes (zero RT explosion).
3. Emits ultra-compact (< 2 KB) 1-node atomic tickets so Codex Dot crashes or context
   compaction never lose progress or trigger 2,000-line history re-reads.
4. Enforces mechanical invariants (0 mixels, 0 parent-clip leaks / frog-eyes, frontal
   local-eye symmetry -> upstream 3D attribution, 0 out-of-palette RGB, 0 forbidden
   double-ops or inverse ray-tracing scripts) and hard-caps retries at max_attempts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import invariants as inv  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_obj(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def build_children_map(tree: dict) -> Dict[Optional[str], List[dict]]:
    children: Dict[Optional[str], List[dict]] = {}
    for node in tree["nodes"]:
        children.setdefault(node.get("parent_id"), []).append(node)
    return children


def ancestor_chain(tree: dict, node_id: str) -> List[str]:
    by_id = {n["id"]: n for n in tree["nodes"]}
    chain: List[str] = []
    cur = by_id[node_id].get("parent_id")
    while cur is not None:
        chain.append(cur)
        cur = by_id[cur].get("parent_id")
    chain.reverse()
    return chain


def inherited_clip_chain(tree: dict, node_id: str) -> List[str]:
    """Compute effective clip ancestor chain automatically inherited down nested subtrees."""
    by_id = {n["id"]: n for n in tree["nodes"]}
    clips: List[str] = []
    chain = ancestor_chain(tree, node_id) + [node_id]
    for nid in chain:
        node = by_id[nid]
        if node.get("clip_mode") == "CLIP_TO_PARENT" and node.get("parent_id"):
            clips.append(node["parent_id"])
    return clips


def descendants_of(tree: dict, node_id: str) -> List[str]:
    children = build_children_map(tree)
    out: List[str] = []
    stack = list(reversed(children.get(node_id, [])))
    while stack:
        cur = stack.pop()
        out.append(cur["id"])
        stack.extend(reversed(children.get(cur["id"], [])))
    return out


def compile_gpu_plan(tree: dict) -> dict:
    """Flatten an arbitrarily deep 20~50+ layer logical tree into minimal GPU passes.

    Logical hierarchy = infinite extensible tree (1, 2-1, 3-2-3-1, ...).
    Physical GPU execution = 5 batched passes (zero RenderTexture explosion!).
    """
    check = inv.check_layer_tree_integrity(tree)
    if not check["passed"]:
        raise ValueError("Invalid layer tree: " + "; ".join(check["errors"]))

    passes = [
        {
            "pass_id": "GPU_PASS_1_ROOT_GBUFFER",
            "purpose": "단일 루트 위상(-delta_root) 동기화 3D G-Buffer: 모든 전신·의상·스타킹·얼굴바탕·헤어 메쉬를 1회 래스터화해 (NodeID, Region r, Shade q, Depth z) 기록 (믹셀 0)",
            "grid": "ROOT_GRID (480x272 logical, 1:1)",
            "nodes": [],
        },
        {
            "pass_id": "GPU_PASS_2_LOCAL_SUBTREES",
            "purpose": "독립 로컬 격자 서브트리(눈 3-2 계층 등): 각 눈 3D 중심 원점 로컬 격자에서 정면 거울 대칭 검증 + M_eye_visible 부모 클리핑 상속으로 흰자->홍채->동공->눈꺼풀 경계 합성 (개구리눈 0)",
            "grid": "LOCAL_EYE_GRID (동일 논리 피치, 32x16 소형 ROI)",
            "nodes": [],
        },
        {
            "pass_id": "GPU_PASS_3_2D_TREE_COMPOSE",
            "purpose": "2D 출력 레이어 순서 합성: 3D 메쉬 앞당기기 없이 클리핑된 눈 계층을 얼굴 피부 위로 승격하고, 앞머리(4)는 실제 3D 깊이 z_hair < z_face/eye 비교로 가림 처리",
            "grid": "ROOT_GRID (480x272 logical, 1:1)",
            "nodes": [],
        },
        {
            "pass_id": "GPU_PASS_4_2D_CURVE_REG",
            "purpose": "단일 2D 이산 곡선·클러스터 보정: 인덱스 (r, q) 공간에서 1px 돌기와 고립 명암 점 정돈 (눈 경계 보호, 2차 카메라 렌더 0)",
            "grid": "FINAL_2D_GRID (480x272 logical)",
            "nodes": [],
        },
        {
            "pass_id": "GPU_PASS_5_SILHOUETTE_AND_LUT",
            "purpose": "물리적 앞쪽 좌표(z_front + tau_z < z_back) 기준 단일 1px 실루엣(턱-목 포함) + 최종 팔레트 P[r, q] 단 1회 조회 + 정수배(k x k) 무손실 출력",
            "grid": "FINAL_2D_GRID -> Display (integer scale k x k)",
            "nodes": [],
        },
    ]

    for node in tree["nodes"]:
        nid = node["id"]
        entry = {
            "id": nid,
            "name": node["name"],
            "design_status": node["design_status"],
            "inherited_clips": inherited_clip_chain(tree, nid),
            "occlude_mode": node["occlude_mode"],
        }
        dom = node["domain"]
        grid = node["grid_space"]
        if dom == "3D_SOURCE" and grid == "ROOT_GRID":
            passes[0]["nodes"].append(entry)
        elif dom == "LOCAL_GRID":
            passes[1]["nodes"].append(entry)
        elif dom == "2D_COMPOSE":
            passes[2]["nodes"].append(entry)
        elif dom == "2D_FINISH":
            if nid == "5-1":
                passes[3]["nodes"].append(entry)
            else:
                passes[4]["nodes"].append(entry)
        else:
            passes[2]["nodes"].append(entry)

    return {
        "tree_id": tree["tree_id"],
        "logical_layer_count": len(tree["nodes"]),
        "physical_gpu_pass_count": len(passes),
        "confirmed_layers": check["confirmedCount"],
        "tbd_design_layers": check["tbdDesignCount"],
        "debug_layer_sheet_contract": "검증 모드에서는 모든 활성 노드의 단독(node_<id>.png) + 누적(accum_<id>.png) 시트를 출력해 역산 스크립트 없이 1초 만에 오류 겹을 확정한다.",
        "passes": passes,
    }


def init_state(state_path: Path, tree_path: Path) -> dict:
    tree = load_json(tree_path)
    check = inv.check_layer_tree_integrity(tree)
    if not check["passed"]:
        raise ValueError("Cannot init invalid layer tree: " + "; ".join(check["errors"]))
    node_states = {}
    for node in tree["nodes"]:
        status = "TBD_BLOCKED" if node["design_status"] == "TBD_DESIGN" else "PENDING"
        node_states[node["id"]] = {
            "name": node["name"],
            "design_status": node["design_status"],
            "status": status,
            "attempts": 0,
            "exit_class": "",
            "artifact_hashes": {},
            "invariant_receipt": {},
            "updated_utc": "",
        }
    state = {
        "schema_version": "4.0",
        "tree_path": str(tree_path.resolve()),
        "tree_sha256": sha256_file(tree_path),
        "tree_id": tree["tree_id"],
        "max_attempts_per_node": tree.get("max_attempts_per_node", 2),
        "created_utc": utc_now(),
        "updated_utc": utc_now(),
        "nodes": node_states,
        "history": [],
    }
    save_json(state_path, state)
    return state


def verify_tree_not_drifted(state: dict) -> dict:
    tree_path = Path(state["tree_path"])
    if not tree_path.exists():
        raise FileNotFoundError(f"Frozen layer tree missing: {tree_path}")
    current_sha = sha256_file(tree_path)
    if current_sha != state["tree_sha256"]:
        raise ValueError("Frozen tree SHA-256 changed after init! Start a new versioned state instead of mutating mid-run.")
    return load_json(tree_path)


def next_ticket(state_path: Path) -> dict:
    """Return a compact (< 2 KB) self-contained atomic worker ticket for the 1 next PENDING node."""
    state = load_json(state_path)
    tree = verify_tree_not_drifted(state)
    by_id = {n["id"]: n for n in tree["nodes"]}

    for node in tree["nodes"]:
        nid = node["id"]
        ns = state["nodes"][nid]
        if ns["status"] == "BLOCKED_MAX_ATTEMPTS":
            return {
                "ticket_status": "BLOCKED",
                "node_id": nid,
                "reason": f"Node {nid} reached max_attempts ({state['max_attempts_per_node']}). User review or upstream fix required.",
                "last_exit_class": ns["exit_class"],
            }
        if ns["status"] == "UPSTREAM_3D_ASYMMETRY":
            return {
                "ticket_status": "BLOCKED_UPSTREAM",
                "node_id": nid,
                "reason": f"Node {nid} failed frontal local-eye mirror symmetry! Fix upstream 3D source/rig/UV/light before retrying.",
                "invariant_receipt": ns["invariant_receipt"],
            }
        if ns["status"] == "PENDING":
            pid = node.get("parent_id")
            if pid is not None and state["nodes"][pid]["status"] not in ("DONE", "TBD_BLOCKED"):
                return {
                    "ticket_status": "BLOCKED_PARENT",
                    "node_id": nid,
                    "reason": f"Parent node {pid} is not DONE (status={state['nodes'][pid]['status']}).",
                }
            # Build compact atomic ticket (forces 1-node focus, zero history sprawl)
            return {
                "ticket_status": "READY",
                "node_id": nid,
                "name": node["name"],
                "attempt": ns["attempts"] + 1,
                "max_attempts": state["max_attempts_per_node"],
                "domain": node["domain"],
                "grid_space": node["grid_space"],
                "clip_mode": node["clip_mode"],
                "inherited_clip_masks": inherited_clip_chain(tree, nid),
                "occlude_mode": node["occlude_mode"],
                "palette_mode": node["palette_mode"],
                "single_op_contract": node["single_op_contract"],
                "allowed_target_files": node["target_files"],
                "required_invariants": node["invariants"],
                "forbidden_patterns": tree["forbidden_patterns"],
                "parent_artifacts": state["nodes"][pid]["artifact_hashes"] if pid else {},
                "worker_rules": [
                    "Read ONLY this ticket + allowed_target_files. NEVER read PIXEL_ALBEDO_20261030.md or legacy EUnityValidation01.",
                    "Modify ONLY allowed_target_files. Zero inverse ray-tracing scripts, zero side folders.",
                    "Output node_<id>.png + accum_<id>.png and submit via layer_graph.py submit."
                ],
            }

    tbd_nodes = [n["id"] for n in tree["nodes"] if state["nodes"][n["id"]]["status"] == "TBD_BLOCKED"]
    return {
        "ticket_status": "ALL_CONFIRMED_DONE",
        "tbd_design_nodes_awaiting_user": tbd_nodes,
    }


def submit_node(state_path: Path, submission_path: Path, workspace_root: Optional[Path] = None) -> dict:
    """Mechanically verify invariants on an AI worker's submission and update state atomically."""
    state = load_json(state_path)
    tree = verify_tree_not_drifted(state)
    sub = load_json(submission_path)
    by_id = {n["id"]: n for n in tree["nodes"]}

    nid = sub.get("node_id")
    if nid not in by_id:
        raise ValueError(f"Unknown node_id in submission: {nid}")
    node = by_id[nid]
    ns = state["nodes"][nid]

    if node["design_status"] == "TBD_DESIGN":
        raise ValueError(f"Node {nid} ({node['name']}) is TBD_DESIGN! AI cannot submit/confirm a [미정] design node.")
    if ns["status"] == "DONE":
        raise ValueError(f"Node {nid} is already DONE. Use 'invalidate' explicitly if code/inputs changed.")
    if ns["attempts"] >= state["max_attempts_per_node"]:
        ns["status"] = "BLOCKED_MAX_ATTEMPTS"
        save_json(state_path, state)
        raise ValueError(f"Node {nid} exceeded max_attempts ({state['max_attempts_per_node']}).")

    ns["attempts"] += 1
    root = workspace_root or Path.cwd()

    # 1. Scope check: reject undeclared file edits (blocks r2..r22 side folder explosion!)
    changed_files: List[str] = sub.get("changed_files", [])
    allowed_set = {Path(p).as_posix() for p in node["target_files"]}
    undeclared = [f for f in changed_files if Path(f).as_posix() not in allowed_set]

    receipts: Dict[str, dict] = {}
    all_passed = True
    exit_class = "NODE_DONE"

    def fail(code: str) -> None:
        nonlocal all_passed, exit_class
        all_passed = False
        if exit_class == "NODE_DONE":
            exit_class = code

    if undeclared:
        fail("SCOPE_VIOLATION")
        receipts["scope_check"] = {"passed": False, "undeclaredFiles": undeclared, "allowedFiles": sorted(allowed_set)}
    else:
        receipts["scope_check"] = {"passed": True, "changedFiles": changed_files}

    # 2. Run every required mechanical invariant
    artifacts = sub.get("artifacts", {})
    for req in node["invariants"]:
        if req == "tree_integrity":
            r = inv.check_layer_tree_integrity(tree)
            receipts[req] = r
            if not r["passed"]:
                fail("INVARIANT_FAIL")
        elif req == "no_forbidden_ops":
            resolved = [root / f if not Path(f).is_absolute() else Path(f) for f in changed_files]
            r = inv.check_source_no_forbidden_ops(resolved, tree["forbidden_patterns"])
            receipts[req] = r
            if not r["passed"]:
                fail("FORBIDDEN_DOUBLE_OP")
        elif req == "uniform_grid_no_mixels":
            png_path = artifacts.get("node_png")
            pitch = int(artifacts.get("pitch", tree["logical_grid"]["display_integer_scale"]))
            if not png_path or not Path(png_path).exists():
                receipts[req] = {"passed": False, "reason": "Missing artifacts.node_png for mixel check"}
                fail("MISSING_ARTIFACT")
            else:
                w, h, px = inv.read_png_rgba(png_path)
                r = inv.check_uniform_grid_no_mixels(px, w, h, pitch)
                receipts[req] = r
                if not r["passed"]:
                    fail("MIXEL_GRID_VIOLATION")
        elif req == "parent_clip_containment":
            child_png = artifacts.get("node_png")
            parent_png = artifacts.get("parent_mask_png")
            if not child_png or not parent_png or not Path(child_png).exists() or not Path(parent_png).exists():
                receipts[req] = {"passed": False, "reason": "Missing node_png or parent_mask_png for clip containment"}
                fail("MISSING_ARTIFACT")
            else:
                cw, ch, cpx = inv.read_png_rgba(child_png)
                pw, ph, ppx = inv.read_png_rgba(parent_png)
                if (cw, ch) != (pw, ph):
                    receipts[req] = {"passed": False, "reason": f"Dimension mismatch child {cw}x{ch} vs parent {pw}x{ph}"}
                    fail("CLIP_LEAK_VIOLATION")
                else:
                    r = inv.check_parent_clip_containment(cpx, ppx, cw, ch)
                    receipts[req] = r
                    if not r["passed"]:
                        fail("CLIP_LEAK_VIOLATION")
        elif req == "local_eye_frontal_symmetry":
            l_png = artifacts.get("left_eye_local_png")
            r_png = artifacts.get("right_eye_local_png")
            if not l_png or not r_png or not Path(l_png).exists() or not Path(r_png).exists():
                receipts[req] = {"passed": False, "reason": "Missing left_eye_local_png or right_eye_local_png"}
                fail("MISSING_ARTIFACT")
            else:
                lw, lh, lpx = inv.read_png_rgba(l_png)
                rw, rh, rpx = inv.read_png_rgba(r_png)
                if (lw, lh) != (rw, rh):
                    receipts[req] = {"passed": False, "reason": f"Eye grid dimension mismatch {lw}x{lh} vs {rw}x{rh}"}
                    fail("UPSTREAM_3D_ASYMMETRY")
                else:
                    r = inv.check_local_eye_frontal_symmetry(lpx, rpx, lw, lh)
                    receipts[req] = r
                    if not r["passed"]:
                        fail("UPSTREAM_3D_ASYMMETRY")
        elif req == "finite_palette_exact":
            png_path = artifacts.get("node_png")
            palette = artifacts.get("allowed_palette_rgb")
            if not png_path or not Path(png_path).exists() or not palette:
                receipts[req] = {"passed": False, "reason": "Missing node_png or allowed_palette_rgb"}
                fail("MISSING_ARTIFACT")
            else:
                w, h, px = inv.read_png_rgba(png_path)
                r = inv.check_finite_palette_exact(px, [tuple(c) for c in palette])
                receipts[req] = r
                if not r["passed"]:
                    fail("OUT_OF_PALETTE_VIOLATION")

    # 3. Record immutable hashes and update state atomically
    art_hashes: Dict[str, str] = {}
    for k, v in artifacts.items():
        if isinstance(v, str) and Path(v).is_file():
            art_hashes[k] = sha256_file(Path(v))
    for f in changed_files:
        fp = root / f if not Path(f).is_absolute() else Path(f)
        if fp.is_file():
            art_hashes["file:" + Path(f).as_posix()] = sha256_file(fp)

    ns["invariant_receipt"] = receipts
    ns["exit_class"] = exit_class
    ns["updated_utc"] = utc_now()
    if all_passed:
        ns["status"] = "DONE"
        ns["artifact_hashes"] = art_hashes
    elif exit_class == "UPSTREAM_3D_ASYMMETRY":
        ns["status"] = "UPSTREAM_3D_ASYMMETRY"
    elif ns["attempts"] >= state["max_attempts_per_node"]:
        ns["status"] = "BLOCKED_MAX_ATTEMPTS"
    else:
        ns["status"] = "PENDING"

    state["updated_utc"] = utc_now()
    state["history"].append({
        "utc": ns["updated_utc"],
        "node_id": nid,
        "attempt": ns["attempts"],
        "passed": all_passed,
        "exit_class": exit_class,
    })
    save_json(state_path, state)
    return {
        "node_id": nid,
        "passed": all_passed,
        "exit_class": exit_class,
        "status": ns["status"],
        "attempts": ns["attempts"],
        "receipts": receipts,
    }


def invalidate_node(state_path: Path, node_id: str) -> dict:
    """Invalidate ONLY node_id and its descendants; preserve all upstream/sibling caches!"""
    state = load_json(state_path)
    tree = verify_tree_not_drifted(state)
    if node_id not in state["nodes"]:
        raise ValueError(f"Unknown node_id: {node_id}")
    affected = [node_id] + descendants_of(tree, node_id)
    reset_ids: List[str] = []
    for nid in affected:
        ns = state["nodes"][nid]
        if ns["design_status"] == "CONFIRMED":
            ns["status"] = "PENDING"
            ns["attempts"] = 0
            ns["exit_class"] = ""
            ns["artifact_hashes"] = {}
            ns["invariant_receipt"] = {}
            reset_ids.append(nid)
    state["updated_utc"] = utc_now()
    save_json(state_path, state)
    return {"invalidated": reset_ids, "preservedCount": len(state["nodes"]) - len(reset_ids)}


def format_tree_text(tree: dict) -> str:
    children = build_children_map(tree)
    lines: List[str] = [
        f"=== {tree['tree_id']} ({len(tree['nodes'])} logical layers, infinite tree extensible) ==="
    ]

    def walk(parent: Optional[str], depth: int) -> None:
        for node in children.get(parent, []):
            indent = "  " * depth
            nid = node["id"]
            clips = inherited_clip_chain(tree, nid)
            clip_tag = f" [CLIP<={','.join(clips)}]" if clips else ""
            tbd_tag = " [TBD_DESIGN]" if node["design_status"] == "TBD_DESIGN" else ""
            lines.append(
                f"{indent}- [{nid}] {node['name']} ({node['domain']} | {node['grid_space']} | {node['occlude_mode']}){clip_tag}{tbd_tag}"
            )
            walk(nid, depth + 1)

    walk(None, 0)
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Hierarchical Pixel Layer Graph Executor & GPU Pass Compiler")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_tree = sub.add_parser("inspect-tree", help="Print the hierarchical layer tree with clipping inheritance")
    p_tree.add_argument("tree_json", nargs="?", default=str(SCRIPT_DIR / "character_layer_tree.json"))

    p_gpu = sub.add_parser("compile-gpu-plan", help="Compile the logical N-layer tree into minimal GPU passes")
    p_gpu.add_argument("tree_json", nargs="?", default=str(SCRIPT_DIR / "character_layer_tree.json"))

    p_init = sub.add_parser("init", help="Freeze a layer tree and initialize disk state.json")
    p_init.add_argument("state_json")
    p_init.add_argument("tree_json", nargs="?", default=str(SCRIPT_DIR / "character_layer_tree.json"))

    p_next = sub.add_parser("next", help="Emit the compact atomic ticket for the next pending node")
    p_next.add_argument("state_json")

    p_sub = sub.add_parser("submit", help="Mechanically verify invariants and submit a node result")
    p_sub.add_argument("state_json")
    p_sub.add_argument("submission_json")
    p_sub.add_argument("--workspace-root", default=None)

    p_inv = sub.add_parser("invalidate", help="Invalidate only one node and its descendants")
    p_inv.add_argument("state_json")
    p_inv.add_argument("node_id")

    args = parser.parse_args(argv)
    if args.cmd == "inspect-tree":
        tree = load_json(Path(args.tree_json))
        check = inv.check_layer_tree_integrity(tree)
        print(format_tree_text(tree))
        print(json.dumps(check, ensure_ascii=False, indent=2))
        return 0 if check["passed"] else 1
    if args.cmd == "compile-gpu-plan":
        tree = load_json(Path(args.tree_json))
        plan = compile_gpu_plan(tree)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "init":
        st = init_state(Path(args.state_json), Path(args.tree_json))
        print(json.dumps({"initialized": args.state_json, "tree_sha256": st["tree_sha256"], "nodeCount": len(st["nodes"])}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "next":
        ticket = next_ticket(Path(args.state_json))
        print(json.dumps(ticket, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "submit":
        ws = Path(args.workspace_root) if args.workspace_root else None
        res = submit_node(Path(args.state_json), Path(args.submission_json), ws)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["passed"] else 2
    if args.cmd == "invalidate":
        res = invalidate_node(Path(args.state_json), args.node_id)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
