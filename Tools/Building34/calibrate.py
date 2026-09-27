"""Bind preserved native texels to one metre scale and explicit cuboid proxies.

No image resizing, cropping, palette conversion or re-normalization occurs here.
The fit is a conservative geometry contract, not recovered original 3D or art approval.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
EPS = 1e-10
ASSETS = {
    "checkout": "counter", "left_shelf": "left_shelf",
    "rear_shelf": "rear_shelf", "display_island": "island",
    "stock_shelf": "stock_shelf",
}
MIRROR_FOR_FIXTURE_FACING = {"counter", "left_shelf", "rear_shelf", "stock_shelf"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def convex_hull(points):
    points = sorted(set(tuple(map(float, p)) for p in points))
    cross = lambda o, a, b: (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= EPS:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= EPS:
            upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def clip_polygon(poly, normal, limit):
    if not poly:
        return []
    result = []
    previous = poly[-1]
    old_distance = sum(a*b for a, b in zip(normal, previous))-limit
    for current in poly:
        distance = sum(a*b for a, b in zip(normal, current))-limit
        old_inside, inside = old_distance <= EPS, distance <= EPS
        if old_inside != inside:
            t = old_distance/(old_distance-distance)
            result.append([previous[k]+t*(current[k]-previous[k]) for k in (0, 1)])
        if inside:
            result.append(list(current))
        previous, old_distance = current, distance
    return result


def feasible_polygon(asset, ppu):
    # A finite initial square containing every possible translation. Its extent
    # includes source origin distance, source size and the complete proxy hull.
    extent = 4*(asset["q_abs_max"]/ppu+asset["proxy_extent"]+1)
    poly = [[-extent, -extent], [extent, -extent], [extent, extent], [-extent, extent]]
    for n, h, support in asset["constraints"]:
        poly = clip_polygon(poly, n, h-support/ppu)
        if not poly:
            break
    return poly


def minimum_ppu(assets):
    low, high = 0.0, 1.0
    while not all(feasible_polygon(a, high) for a in assets):
        high *= 2
        if high > 1e8:
            raise RuntimeError("No finite common PPU found within the declared search bound")
    for _ in range(80):
        middle = (low+high)*0.5
        if all(feasible_polygon(a, middle) for a in assets):
            high = middle
        else:
            low = middle
    return high


def choose_translation(asset, ppu):
    poly = feasible_polygon(asset, ppu)
    if not poly:
        raise RuntimeError("Fixed PPU does not have a feasible translation")
    ground_y = min(p[1] for p in asset["hull"])
    desired_y = ground_y-asset["minimum_q_y"]/ppu
    lower, upper = -math.inf, math.inf
    ground_possible = True
    for normal, h, support in asset["constraints"]:
        remaining = h-support/ppu-normal[1]*desired_y
        if abs(normal[0]) <= EPS:
            ground_possible &= remaining >= -EPS
        elif normal[0] > 0:
            upper = min(upper, remaining/normal[0])
        else:
            lower = max(lower, remaining/normal[0])
    ground_possible &= lower <= upper+EPS
    if ground_possible:
        translation = [(lower+upper)*0.5, desired_y]
        selected = "exact opaque-bottom to projected front-ground anchor"
    else:
        min_y = min(p[1] for p in poly)
        # At a flat minimum edge select its middle; do not prefer an arbitrary side.
        candidates = [p[0] for p in poly if abs(p[1]-min_y) <= EPS]
        translation = [(min(candidates)+max(candidates))*0.5, min_y]
        selected = "minimum translation Y in feasible polygon"
    gap = asset["minimum_q_y"]/ppu+translation[1]-ground_y
    return translation, {
        "selection": selected, "exact_ground_anchor_feasible": bool(ground_possible),
        "desired_translation_y_m": desired_y,
        "projected_front_ground_min_y_m": ground_y,
        "opaque_bottom_gap_screen_m": gap,
        "opaque_bottom_gap_native_pixels": gap*ppu,
        "note": "Finite texel lower edges can require a positive gap above the single lowest hull vertex.",
    }


def slab_readback(asset, ppu, translation, right, up, direction, np):
    centers = asset["centers"]
    offsets = np.array([[0., 0.], [-.5, -.5], [-.5, .5], [.5, -.5], [.5, .5]])
    q = (centers[:, None, :]+offsets[None, :, :]).reshape(-1, 2)
    screen = q/ppu+np.asarray(translation)
    origins = screen[:, :1]*right+screen[:, 1:]*up
    t0 = (asset["minimum"]-origins)/direction
    t1 = (asset["maximum"]-origins)/direction
    near = np.max(np.minimum(t0, t1), axis=1)
    far = np.min(np.maximum(t0, t1), axis=1)
    hit = near <= far+1e-8
    misses = int(np.count_nonzero(~hit))
    points = origins[hit]+near[hit, None]*direction
    if misses:
        raise RuntimeError(f"Opaque pixel centre/corner rays miss {asset['id']} proxy: {misses}")
    residual = max(sum(n[k]*translation[k] for k in (0, 1))-(h-support/ppu)
                   for n, h, support in asset["constraints"])
    return {
        "opaque_pixel_count": int(len(centers)),
        "sample_count": int(len(q)),
        "sample_rule": "Each alpha > 0.1 pixel centre and all four full-cell corners",
        "hit_count": int(np.count_nonzero(hit)), "hit_miss_count": misses,
        "entry_height_min_m": float(points[:, 1].min()),
        "entry_height_max_m": float(points[:, 1].max()),
        "slab_near_min_m": float(near.min()), "slab_near_max_m": float(near.max()),
        "maximum_halfplane_violation_m": float(residual),
        "ray": "line = right * screenX + up * screenY + lambda * cameraForward; entry uses minimum lambda",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"docs/artifacts/building34/calibration.json")
    parser.add_argument("--orientation-policy", choices=("preserved", "fixture-facing"), default="preserved",
                        help="Fixture-facing mirrors source U for explicit long-axis orientation; PNG bytes stay unchanged")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Calibration output already exists; refusing to replace it")
    prior = json.loads((ROOT/"docs/artifacts/building33-native-probe/receipt.json").read_text(encoding="utf-8-sig"))
    sys.path.insert(0, prior["dependencies"]["path"])
    import numpy as np
    from PIL import Image
    plan_path = ROOT/"docs/artifacts/building32/layout-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    summary_path = ROOT/"docs/artifacts/building34/native-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    sources = {a["id"]: a for a in summary["assets"]}
    sin30, cos30, sqrt2 = .5, math.sqrt(3)/2, math.sqrt(2)
    right = np.array([1/sqrt2, 0., -1/sqrt2])
    # Unity Quaternion.Euler(30, 45, 0): screen-up and camera-forward must be
    # orthogonal. Negative X/Z up components belong to a different view direction.
    up = np.array([sin30/sqrt2, cos30, sin30/sqrt2])
    direction = np.array([cos30/sqrt2, -sin30, cos30/sqrt2])
    basis_matrix = np.stack((right, up, direction))
    if not np.allclose(basis_matrix@basis_matrix.T, np.eye(3), atol=1e-12):
        raise ValueError("Projection and ray basis are not orthonormal")
    assets = []
    for fixture in plan["fixtures"]:
        source = sources[ASSETS[fixture["id"]]]
        path = ROOT/source["native_path"]
        if sha(path) != source["native_sha256"]:
            raise RuntimeError("Preserved native source hash differs: "+str(path))
        with Image.open(path) as image:
            if image.mode != "RGBA":
                raise ValueError("Calibration requires preserved RGBA native input")
            rgba = np.asarray(image)
        ys, xs = np.nonzero(rgba[..., 3] > 25.5)
        if not len(xs):
            raise ValueError("No opaque input texels: "+str(path))
        mirror_u = args.orientation_policy == "fixture-facing" and source["id"] in MIRROR_FOR_FIXTURE_FACING
        screen_x = rgba.shape[1]-xs-.5 if mirror_u else xs+.5
        centers = np.column_stack((screen_x, -ys-.5))
        x0, z0, x1, z1 = fixture["rect_xz"]
        w, d = x1-x0, z1-z0
        height = 1.55 if fixture["id"] == "checkout" else fixture["height_m"]
        minimum = np.array([-w/2, 0., -d/2])
        maximum = np.array([w/2, height, d/2])
        corners = np.array(list(itertools.product([-w/2, w/2], [0., height], [-d/2, d/2])))
        projected = np.column_stack((corners@right, corners@up))
        hull = convex_hull(projected)
        constraints = []
        for a, b in zip(hull, hull[1:]+hull[:1]):
            edge = np.asarray(b)-a
            normal = np.array([edge[1], -edge[0]])
            normal /= np.linalg.norm(normal)
            limit = float(normal@a)
            support = float(np.max(centers@normal)+.5*np.sum(np.abs(normal)))
            constraints.append((normal.tolist(), limit, support))
        assets.append({"id": fixture["id"], "asset_id": source["id"], "path": path,
                       "mirror_u": mirror_u,
                       "source": source, "centers": centers, "minimum": minimum,
                       "maximum": maximum, "width": w, "depth": d, "height": height,
                       "planned_center": [(x0+x1)/2, (z0+z1)/2],
                       "hull": hull, "constraints": constraints,
                       "q_abs_max": float(np.max(np.abs(centers))+.5),
                       "proxy_extent": float(np.max(np.abs(projected))),
                       "minimum_q_y": -float(ys.max()+1)})
    ppu_min = minimum_ppu(assets)
    ppu = int(math.ceil(ppu_min))
    rows = []
    for asset in assets:
        translation, grounding = choose_translation(asset, ppu)
        observation = slab_readback(asset, ppu, translation, right, up, direction, np)
        rows.append({
            "id": asset["asset_id"], "fixture_id": asset["id"],
            "native_path": asset["source"]["native_path"], "native_sha256": sha(asset["path"]),
            "native_dimensions": asset["source"]["native_dimensions"],
            "origin_screen_m": translation, "ppu": ppu,
            "mirrorU": asset["mirror_u"],
            "width_m": asset["width"], "depth_m": asset["depth"], "height_m": asset["height"],
            "center_xz": asset["planned_center"], "opaque_ray_misses": observation["hit_miss_count"],
            "bbox_width_depth_height_m": [asset["width"], asset["depth"], asset["height"]],
            "bbox_min_xyz_m": asset["minimum"].tolist(), "bbox_max_xyz_m": asset["maximum"].tolist(),
            "planned_center_xz_m": asset["planned_center"],
            "projected_proxy_hull_m": asset["hull"],
            "opaque_bbox_xyxy_exclusive": asset["source"]["alpha_gt_0_1_bbox_xyxy_exclusive"],
            "minimum_individual_ppu": minimum_ppu([asset]),
            "grounding": grounding, "ray_observation": observation,
        })
    result = {
        "schema": "building34-common-pixel-proxy-calibration/1", "status": "geometry_calibrated",
        "scope": "Common native texel metre size and conservative depth proxy only; not original 3D recovery or art approval",
        "normalization_is_separate": "Native PNG data is preserved byte-for-byte; this is a world mapping, not image pixel-grid detection",
        "plan_path": str(plan_path.relative_to(ROOT)).replace("\\", "/"), "plan_sha256": sha(plan_path),
        "input_summary_path": str(summary_path.relative_to(ROOT)).replace("\\", "/"),
        "input_summary_sha256": sha(summary_path), "solver_path": "Tools/Building34/calibrate.py",
        "solver_sha256": sha(__file__), "alpha_coverage_rule": "alpha > 0.1; all four texel corners inside projected proxy hull",
        "camera_local_pitch_degrees": 30, "camera_local_yaw_degrees": 45,
        "basis": {"right": right.tolist(), "up": up.tolist(), "forward": direction.tolist()},
        "basis_consistency": "Unity Quaternion.Euler(30,45,0); orthonormal basis checked before projection",
        "mapping": "screen_m = (mirrorU ? nativeWidth-native_x-0.5 : native_x+0.5, -native_y-0.5) / ppu + origin_screen_m",
        "orientation_policy": args.orientation_policy,
        "orientation_reason": "Local X edges project up-right and local Z edges project up-left at the fixed Unity camera. Mirroring explicitly aligns source long axes with fixture footprint axes; no image resampling or source-byte modification.",
        "fit_algorithm": "Convex hull halfplanes; support of all opaque texel squares; polygon-clipped feasible translations; monotone binary search; ceil common PPU",
        "minimum_common_ppu": ppu_min, "ppu": ppu, "metres_per_native_texel": 1/ppu,
        "height_override": {"checkout": {"height_m": 1.55, "reason": "Includes the cash register silhouette above the 1m counter"}},
        "assets": rows, "total_hit_miss_count": sum(a["ray_observation"]["hit_miss_count"] for a in rows),
        "limits": ["A cuboid is only an explicit physical/depth proxy, not recovered detailed furniture geometry.",
                   "Projected containment does not prove source camera angle, internal perspective or stylistic correctness.",
                   "Exact opaque-bottom contact may be infeasible because the projected ground minimum is a single vertex.",
                   "This calibration supports the fixed local 30 degree pitch and 45 degree yaw only.",
                   "World integration, actual gameplay and visual quality have not been tested by this script."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "ppu": ppu, "minimum_common_ppu": ppu_min,
                      "total_hit_miss_count": result["total_hit_miss_count"], "output": str(args.output),
                      "assets": [{"id": a["id"], "origin_screen_m": a["origin_screen_m"],
                                  "ground_gap_pixels": a["grounding"]["opaque_bottom_gap_native_pixels"],
                                  "minimum_individual_ppu": a["minimum_individual_ppu"]} for a in rows]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
