"""Validate immutable B35 placement with support geometry and conservative BFS.

Only offline geometry; never Unity/gameplay/art approval. Inputs stay unchanged.
Run from repository root: python Tools/Building35/compute_placement.py
"""
import collections
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "docs/artifacts/building35"
EPS = 1e-8


def footprint(instance):
    x, _, z = instance["position"]
    w, _, d = instance["collider_size"]
    return [x - w / 2, z - d / 2, x + w / 2, z + d / 2]


def contains(a, b):
    return a[0] <= b[0] + EPS and a[1] <= b[1] + EPS and a[2] + EPS >= b[2] and a[3] + EPS >= b[3]


def overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) + EPS and min(a[3], b[3]) > max(a[1], b[1]) + EPS


def distance(p, box):
    return math.hypot(max(box[0] - p[0], 0, p[0] - box[2]), max(box[1] - p[1], 0, p[1] - box[3]))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    placement_path = FOLDER / "placement.json"
    raw = placement_path.read_bytes()
    plan = json.loads(raw)
    shell_raw = (ROOT / plan["source_shell_plan"]).read_bytes()
    if hashlib.sha256(shell_raw).hexdigest() != plan["source_shell_sha256"]:
        raise ValueError("Base shell source changed; explicitly review instead of silently accepting")
    shell = json.loads(shell_raw)
    instances = plan["instances"]
    index = {o["id"]: o for o in instances}
    if len(index) != len(instances):
        raise ValueError("Duplicate instance ID")
    obstacles = [{"id": o["id"], "rect_xz": footprint(o)} for o in instances]
    walls = shell["walls"] + shell["partitions"]
    solids = obstacles + walls
    violations, supports, overlaps = [], [], []
    for i, obj in enumerate(instances):
        box = footprint(obj)
        if not contains(shell["floor"]["rect_xz"], box):
            violations.append({"kind": "outside_floor", "id": obj["id"]})
        if any(v <= 0 for v in obj["collider_size"]):
            violations.append({"kind": "invalid_dimensions", "id": obj["id"]})
        y = obj["position"][1]
        top = y + obj["collider_size"][1]
        for wall in walls:
            if overlap(box, wall["rect_xz"]):
                overlaps.append([obj["id"], wall["id"]])
        for other in instances[i + 1:]:
            oy = other["position"][1]
            ot = oy + other["collider_size"][1]
            if min(top, ot) > max(y, oy) + EPS and overlap(box, footprint(other)):
                overlaps.append([obj["id"], other["id"]])
        parent_id = obj["support"]
        if parent_id == "floor":
            ok = abs(y) < EPS
            supports.append({"id": obj["id"], "support": "floor", "supported": ok, "base_y": y})
        else:
            parent = index.get(parent_id)
            if parent is None:
                ok = False
                supports.append({"id": obj["id"], "support": parent_id, "supported": False, "reason": "missing_support"})
            else:
                support_y = parent["position"][1] + parent["collider_size"][1]
                ok = contains(footprint(parent), box) and abs(y - support_y) < EPS
                supports.append({"id": obj["id"], "support": parent_id, "supported": ok, "base_y": y, "support_top_y": support_y, "footprint_contained": contains(footprint(parent), box)})
        if not ok:
            violations.append({"kind": "support_contract_failed", "id": obj["id"]})
    violations.extend({"kind": "solid_overlap", "ids": pair} for pair in overlaps)
    for reserved in shell["reserved_routes"]:
        for solid in solids:
            if overlap(reserved["rect_xz"], solid["rect_xz"]):
                violations.append({"kind": "reserved_route_blocked", "ids": [reserved["id"], solid["id"]]})

    config = shell["computation"]
    step = config["grid_cell_m"]
    if config["connectivity"] != 4:
        raise ValueError("Only conservative 4-neighbor BFS supported")
    radius = shell["player"]["radius_m"] + shell["player"]["design_margin_m"] + step / math.sqrt(2)
    domain, floor, strip = config["domain_xz"], shell["floor"]["rect_xz"], config["outside_entry_strip_xz"]
    nx, nz = round((domain[2] - domain[0]) / step), round((domain[3] - domain[1]) / step)

    def centre(cell):
        return (round(domain[0] + (cell[0] + .5) * step, 6), round(domain[1] + (cell[1] + .5) * step, 6))

    def cell_for(point):
        return math.floor((point[0] - domain[0]) / step), math.floor((point[1] - domain[1]) / step)

    clearance = {}
    for iz in range(nz):
        for ix in range(nx):
            p = centre((ix, iz))
            rect = [p[0] - step / 2, p[1] - step / 2, p[0] + step / 2, p[1] + step / 2]
            if not (contains(floor, rect) or contains(strip, rect)):
                continue
            d = min(distance(p, o["rect_xz"]) for o in solids)
            if d > radius + EPS:
                clearance[(ix, iz)] = d
    source = cell_for(config["source_point_xz"])
    parents = {}
    if source in clearance:
        parents[source] = None
        queue = collections.deque([source])
        while queue:
            cell = queue.popleft()
            for dx, dz in [(0, 1), (-1, 0), (1, 0), (0, -1)]:
                nxt = cell[0] + dx, cell[1] + dz
                if nxt in clearance and nxt not in parents:
                    parents[nxt] = cell
                    queue.append(nxt)
    else:
        violations.append({"kind": "source_blocked", "source_cell": source})
    paths = []
    for use in plan["use_points"]:
        if use["instance"] not in index:
            raise ValueError("Use point without an actual instance")
        target = cell_for(use["point_xz"])
        cells = []
        if target in parents:
            node = target
            while node is not None:
                cells.append(node)
                node = parents[node]
            cells.reverse()
        else:
            violations.append({"kind": "use_point_unreachable", "id": use["id"], "target_free": target in clearance})
        paths.append({"id": use["id"], "instance": use["instance"], "requested_xz": use["point_xz"], "sampled_xz": centre(target), "reachable": bool(cells), "path_length_m": round(max(0, len(cells) - 1) * step, 6), "minimum_path_obstacle_distance_m": round(min(clearance[c] for c in cells), 6) if cells else None, "endpoint_obstacle_distance_m": round(min(distance(centre(target), o["rect_xz"]) for o in solids), 6), "path_xz": [centre(c) for c in cells]})
    if len(paths) < 10:
        violations.append({"kind": "insufficient_actual_use_points"})
    if not 18 <= len(instances) <= 24:
        violations.append({"kind": "actual_instance_count_out_of_contract", "actual": len(instances)})
    report = {
        "schema": "building35-placement-route-report/1",
        "status": "STATIC_GEOMETRY_PASS" if not violations else "STATIC_GEOMETRY_FAIL",
        "placement_sha256": hashlib.sha256(raw).hexdigest(),
        "applied_to_unity": False, "gameplay_validated": False, "art_validated": False,
        "algorithm": "Explicit immutable physical footprints; exact 3D AABB interiors; support footprint containment and exact base/support height; Euclidean disk-inflated 0.1m grid, stable 4-neighbor BFS from existing entry",
        "player_radius_m": shell["player"]["radius_m"], "design_margin_m": shell["player"]["design_margin_m"], "grid_cell_m": step, "conservative_radius_m": radius,
        "actual_instance_count": len(instances), "painted_shelf_contents_additional_count": 0,
        "floor_supported_count": sum(o["support"] == "floor" for o in instances),
        "object_supported_count": sum(o["support"] != "floor" for o in instances),
        "support_checks": supports, "solid_overlaps": overlaps,
        "free_cell_count": len(clearance), "entry_reachable_cell_count": len(parents),
        "required_use_count": len(paths), "reachable_use_count": sum(p["reachable"] for p in paths),
        "routes": paths, "violations": violations,
        "limitations": plan["limitations"] + ["Radius uses B32 prefab value .5m plus .1m design margin; not a new runtime player measurement.", "Conservative static route does not validate facing, rendered extents, interactions, door-leaf swing or live Unity physics."]
    }
    report_path = FOLDER / "layout-route-report.json"
    write(report_path, report)
    observation = {
        "planPath": "docs/artifacts/building35/placement.json", "planSha256": report["placement_sha256"],
        "reportPath": "docs/artifacts/building35/layout-route-report.json", "reportSha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "fixtures": [{"id": o["id"], "facing": o.get("facing"), "rect_xz": footprint(o)} for o in instances if o["support"] == "floor"],
        "routes": [{"id": p["id"], "points": [{"x": x, "z": z} for x, z in p["path_xz"]]} for p in paths if p["reachable"]],
        "status": report["status"], "evidence_scope": "Offline calculated routes only; consumer must perform actual movement and collision observations"
    }
    write(FOLDER / "observation-input.json", observation)
    print(json.dumps({"status": report["status"], "actual_instances": len(instances), "reachable": report["reachable_use_count"], "required": len(paths), "violations": violations}, ensure_ascii=False))
    return 0 if not violations else 2


if __name__ == "__main__":
    raise SystemExit(main())
