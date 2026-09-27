"""Compile a proposal JSON to an annotated SVG and explicit geometric observations.

This is an offline floor-plan calculation, never art approval or gameplay validation.
Only Python standard library. The source plan is immutable; no automatic correction.
"""
import argparse
import collections
import hashlib
import html
import json
import math
from pathlib import Path

EPS = 1e-9


def overlaps(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) + EPS and min(a[3], b[3]) > max(a[1], b[1]) + EPS


def contains(a, b):
    return a[0] <= b[0] + EPS and a[1] <= b[1] + EPS and a[2] + EPS >= b[2] and a[3] + EPS >= b[3]


def point_distance_rect(p, b):
    dx = max(b[0] - p[0], 0.0, p[0] - b[2])
    dz = max(b[1] - p[1], 0.0, p[1] - b[3])
    return math.hypot(dx, dz)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--svg", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    plan_path = Path(args.plan)
    raw = plan_path.read_bytes()
    plan = json.loads(raw)
    if plan["status"] != "proposal_unapplied":
        raise ValueError("Compiler accepts unapplied design proposals only")
    fixtures = plan["fixtures"]
    walls = plan["walls"] + plan["partitions"]
    solids = walls + fixtures
    floor = plan["floor"]["rect_xz"]
    violations = []
    checks = []
    for i, item in enumerate(fixtures):
        if not contains(floor, item["rect_xz"]):
            violations.append({"kind": "outside_floor", "id": item["id"]})
        for other in fixtures[i + 1:] + walls:
            if overlaps(item["rect_xz"], other["rect_xz"]):
                violations.append({"kind": "solid_overlap", "ids": [item["id"], other["id"]]})
        for use in item["use_areas"]:
            if not contains(floor, use["rect_xz"]):
                violations.append({"kind": "use_area_outside_floor", "id": use["id"]})
            p = use["access_xz"]
            if not contains(use["rect_xz"], [p[0], p[1], p[0], p[1]]):
                violations.append({"kind": "access_outside_use_area", "id": use["id"]})
            for other in solids:
                if overlaps(use["rect_xz"], other["rect_xz"]):
                    violations.append({"kind": "use_area_blocked", "ids": [use["id"], other["id"]]})
        attachment = item["attachment"]
        if attachment["kind"] == "wall":
            wall = next(w for w in walls if w["id"] == attachment["wall_id"])
            r, w = item["rect_xz"], wall["rect_xz"]
            expected = attachment["gap_m"]
            if item["facing"] == "+X":
                actual = r[0] - w[2]
            elif item["facing"] == "-Z":
                actual = w[1] - r[3]
            else:
                raise ValueError("Unsupported wall facing")
            checks.append({"kind": "wall_attachment_gap", "id": item["id"], "actual_m": round(actual, 6), "expected_m": expected})
            if abs(actual - expected) > 1e-6:
                violations.append({"kind": "wall_attachment_gap_mismatch", "id": item["id"]})
    for route in plan["reserved_routes"]:
        for solid in solids:
            if overlaps(route["rect_xz"], solid["rect_xz"]):
                violations.append({"kind": "reserved_route_blocked", "ids": [route["id"], solid["id"]]})

    config = plan["computation"]
    step = config["grid_cell_m"]
    if config["connectivity"] != 4 or step <= 0:
        raise ValueError("Only positive 4-neighbour grids are supported")
    domain = config["domain_xz"]
    nx = round((domain[2] - domain[0]) / step)
    nz = round((domain[3] - domain[1]) / step)
    design_r = plan["player"]["radius_m"] + plan["player"]["design_margin_m"]
    conservative_r = design_r + step / math.sqrt(2)
    strip = config["outside_entry_strip_xz"]

    def centre(cell):
        return (domain[0] + (cell[0] + 0.5) * step, domain[1] + (cell[1] + 0.5) * step)

    def cell_for(p):
        return (math.floor((p[0] - domain[0]) / step), math.floor((p[1] - domain[1]) / step))

    free = set()
    for iz in range(nz):
        for ix in range(nx):
            cell = ix, iz
            x, z = centre(cell)
            cell_rect = [x - step / 2, z - step / 2, x + step / 2, z + step / 2]
            if not (contains(floor, cell_rect) or contains(strip, cell_rect)):
                continue
            if all(point_distance_rect((x, z), item["rect_xz"]) > conservative_r + EPS for item in solids):
                free.add(cell)
    source = cell_for(config["source_point_xz"])
    parents = {}
    if source in free:
        parents[source] = None
        queue = collections.deque([source])
        while queue:
            here = queue.popleft()
            for delta in ((0, 1), (-1, 0), (1, 0), (0, -1)):
                nxt = here[0] + delta[0], here[1] + delta[1]
                if nxt in free and nxt not in parents:
                    parents[nxt] = here
                    queue.append(nxt)
    else:
        violations.append({"kind": "entry_source_blocked", "cell": source})

    paths = []
    for item in fixtures:
        for use in item["use_areas"]:
            target = cell_for(use["access_xz"])
            reachable = target in parents
            path = []
            if reachable:
                current = target
                while current is not None:
                    path.append(centre(current))
                    current = parents[current]
                path.reverse()
            else:
                violations.append({"kind": "access_unreachable", "id": use["id"], "target_cell": target, "target_free": target in free})
            point = centre(target)
            clearance = min(point_distance_rect(point, s["rect_xz"]) for s in solids)
            paths.append({"id": use["id"], "fixture": item["id"], "requested_xz": use["access_xz"], "grid_centre_xz": [round(v, 4) for v in point], "reachable": reachable, "minimum_access_obstacle_distance_m": round(clearance, 6), "steps": len(path) - 1 if reachable else None, "path_xz": [[round(a, 4), round(b, 4)] for a, b in path]})

    doors = []
    for door in plan["doors"]:
        a, b = door["segment_xz"]
        width = math.dist(a, b)
        sufficient = width >= 2 * conservative_r
        doors.append({"id": door["id"], "width_m": width, "declared_m": door["opening_m"], "minimum_conservative_grid_diameter_m": round(2 * conservative_r, 6), "width_sufficient": sufficient})
        if abs(width - door["opening_m"]) > 1e-6 or not sufficient:
            violations.append({"kind": "door_width_invalid", "id": door["id"]})

    report = {
        "schema": "building-layout-observation/1", "plan_id": plan["id"], "plan_sha256": hashlib.sha256(raw).hexdigest(),
        "status": "GEOMETRY_PASS_PROPOSAL_ONLY" if not violations else "GEOMETRY_FAILED_UNAPPLIED",
        "applied_to_unity": False, "art_approved": False, "gameplay_validated": False,
        "algorithm": "immutable rectangles; exact overlap; grid conservative Euclidean disk dilation; stable 4-neighbour BFS",
        "grid_cell_m": step, "player_radius_m": plan["player"]["radius_m"], "proposal_margin_m": plan["player"]["design_margin_m"],
        "conservative_radius_m": conservative_r, "free_cells": len(free), "entry_reachable_cells": len(parents),
        "fixture_count": len(fixtures), "reachable_access_count": sum(p["reachable"] for p in paths),
        "use_area_count": len(paths), "overlap_policy": "solid interiors never overlap; use areas may overlap each other, never solids; wall joins may overlap",
        "checks": checks, "doors": doors, "paths": paths, "violations": violations,
        "limitations": plan["limitations"] + ["Grid failure may be conservative; never reduce threshold silently", "No compliance or real building regulation claim", "Object images, support landmarks and camera occlusion are not tested"]
    }
    write_svg(plan, report, Path(args.svg))
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "reachable": report["reachable_access_count"], "required": report["use_area_count"], "violation_count": len(violations), "svg": args.svg, "report": args.report}, ensure_ascii=False))
    return 0 if not violations else 2


def write_svg(plan, report, destination):
    # Technical layout visualization only; this is not generated game art.
    ox, oy, scale = 115, 160, 70
    def xy(x, z):
        return ox + (x + 5) * scale, oy + (4 - z) * scale
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="940" viewBox="0 0 1000 940">',
             '<style>text{font-family:"Malgun Gothic","Noto Sans KR",sans-serif;fill:#233445} .small{font-size:13px}.body{font-size:15px}.label{font-size:14px;font-weight:600}</style>',
             '<rect width="1000" height="940" fill="#f7f8f5"/>']
    def text(x, y, message, css="body", anchor="start", fill=None):
        color = f' style="fill:{fill}"' if fill else ''
        parts.append(f'<text x="{x:.2f}" y="{y:.2f}" class="{css}" text-anchor="{anchor}"{color}>{html.escape(str(message))}</text>')
    def rect(r, fill, stroke="none", width=1, opacity=1, dash=None):
        x, y = xy(r[0], r[3])
        extra = f' stroke-dasharray="{dash}"' if dash else ''
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{(r[2]-r[0])*scale:.2f}" height="{(r[3]-r[1])*scale:.2f}" fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{width}"{extra}/>')
    text(55, 47, "B32 · 배치설계 후보 — 10 × 8 m", "label")
    text(55, 77, "미적용 도면 / AI가 물체를 직접 옮기기 전 역할·사용공간·동선을 고정합니다.")
    text(55, 104, "좌표: 건물 local XZ(m) · 앞 -Z / 뒤 +Z · 원래 중앙 2m 출입구 보존", "small")
    status = "기하 조건 충족 · 미술/게임플레이 미검증" if not report["violations"] else "기하 조건 실패 · 적용하지 않음"
    text(55, 130, status, "label", fill="#28695f" if not report["violations"] else "#a02d32")
    rect(plan["floor"]["rect_xz"], "#fafaf5", "#607582")
    for zone in plan["zones"]:
        rect(zone["rect_xz"], zone["color"], opacity=0.68)
    for route in plan["reserved_routes"]:
        rect(route["rect_xz"], route["color"], "#4a9c99", 1, 0.65, "5 4")
    for x in range(-5, 6):
        a, b = xy(x, -4), xy(x, 4)
        parts.append(f'<path d="M{a[0]} {a[1]} L{b[0]} {b[1]}" stroke="#a9b8bc" opacity=".23"/>')
        text(b[0], oy-12, x, "small", "middle")
    for z in range(-4, 5):
        a, b = xy(-5, z), xy(5, z)
        parts.append(f'<path d="M{a[0]} {a[1]} L{b[0]} {b[1]}" stroke="#a9b8bc" opacity=".23"/>')
        text(a[0]-16, a[1]+4, z, "small", "end")
    for item in plan["fixtures"]:
        for use in item["use_areas"]:
            rect(use["rect_xz"], item["color"], item["color"], 1.4, 0.13, "5 4")
    for path in report["paths"]:
        if not path["reachable"]:
            continue
        points = " ".join(f'{xy(x,z)[0]:.2f},{xy(x,z)[1]:.2f}' for x,z in path["path_xz"])
        parts.append(f'<polyline points="{points}" fill="none" stroke="#27767b" stroke-width="2.3" stroke-opacity=".50"/>')
    for wall in plan["walls"] + plan["partitions"]:
        rect(wall["rect_xz"], "#536773")
    for item in plan["fixtures"]:
        r = item["rect_xz"]
        rect(r, item["color"], "#3e4541", 1.4)
        x, y = xy((r[0]+r[2])/2, (r[1]+r[3])/2)
        if r[2]-r[0] < 1:
            parts.append(f'<text x="{x:.2f}" y="{y:.2f}" class="label" text-anchor="middle" transform="rotate(-90 {x:.2f} {y:.2f})">{html.escape(item["label"])}</text>')
        else:
            text(x, y+4, item["label"], "label", "middle")
        for use in item["use_areas"]:
            px, pz = use["access_xz"]
            x, y = xy(px, pz)
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="#216a75" stroke="white" stroke-width="1.5"/>')
            text(x, y+20, use["label"], "small", "middle")
    for door in plan["doors"]:
        a, b = [xy(*p) for p in door["segment_xz"]]
        parts.append(f'<path d="M{a[0]} {a[1]} L{b[0]} {b[1]}" stroke="#20886d" stroke-width="4" stroke-dasharray="7 4"/>')
    text(*xy(3.3, 1.6), "재고실", "label", "middle")
    text(*xy(0, 0.1), "주통로", "small", "middle")
    text(465, 752, "중앙 출입구 2m · 시작점은 건물 밖", "small", "middle")
    text(850, 187, "+Z 뒤", "label")
    text(850, 219, "X →", "label")
    text(850, 273, "진한 면: 물체", "small")
    text(850, 299, "옅은 점선: 사용", "small")
    text(850, 325, "청록 선: BFS", "small")
    text(850, 351, "점: 접근점", "small")
    text(55, 794, f'실제 계산: 비겹침 · 사용공간 · 벽 부착 · 필수 접근 {report["reachable_access_count"]}/{report["use_area_count"]}', "label")
    text(55, 823, "Player 반경 0.5m(prefab 확인) + 설계 여유 0.1m(제안) · 0.1m 보수적 4방향 그리드", "small")
    text(55, 850, "셀 전체를 안전하게 유지하도록 반대각선까지 장애물 팽창에 포함합니다. 임계값 자동 완화 없음.", "small")
    text(55, 879, "카메라 가림·스프라이트 접점·특징/명암·실제 이동은 별도 확인 대상입니다. 이 그림은 게임 아트가 아닙니다.", "small")
    text(55, 906, "근거: Merrell et al. 2011 / Tiled Object Layers · 단일 원본: layout-plan.json", "small")
    parts.append("</svg>")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(parts)+"\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
