"""Read-only geometric suitability probe for the unchanged common-sheet crops.

No source image, mesh, collider, placement, or Unity asset is modified. The only
output is an evidence JSON. A hypothetical bottom-centre alignment is a probe,
not an inferred semantic foot/support pivot or permission to integrate the art.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
R = np.array([1.0, 0.0, -1.0]) / np.sqrt(2.0)
U = np.array([0.5 / np.sqrt(2.0), np.sqrt(0.75), 0.5 / np.sqrt(2.0)])
F = np.cross(R, U)
CUTOFF = 0.1


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def rgba(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        if image.mode != "RGBA":
            raise ValueError(f"Expected RGBA without conversion: {path}")
        return np.asarray(image).copy()


def visible_bbox(pixels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ys, xs = np.nonzero(pixels[..., 3].astype(float) / 255.0 > CUTOFF)
    if not len(xs):
        raise ValueError("Empty visible source")
    return np.array([xs.min(), ys.min(), xs.max() + 1, ys.max() + 1]), xs, ys


def ray_hits(points: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    # Orthographic source rays, identical basis to Unity's authored local view.
    # All direction components are nonzero for pitch30/yaw45.
    origins = points - F * 100.0
    t0 = (low - origins) / F
    t1 = (high - origins) / F
    entry = np.minimum(t0, t1).max(axis=-1)
    leave = np.maximum(t0, t1).min(axis=-1)
    return (entry <= leave + 1e-8) & (leave >= 0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/artifacts/building36/source-fit.json")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Preserve existing evidence: {output}")

    inputs: dict[str, str] = {}

    def record(path: Path) -> Path:
        path = path.resolve()
        inputs[relative(path)] = sha(path)
        return path

    def read_json(path: Path):
        return json.loads(record(path).read_text(encoding="utf-8-sig"))

    manifest = read_json(ROOT / "docs/artifacts/building36/slices/manifest.json")
    placement_path = ROOT / "docs/artifacts/building35/placement.json"
    details_path = ROOT / "docs/artifacts/building35/details/placement.json"
    metric_path = ROOT / "Tools/Building35/metric-catalog.json"
    plan = read_json(placement_path)
    details = read_json(details_path)
    metrics = read_json(metric_path)
    ppu = float(plan["nativePpu"])
    if ppu != float(metrics["nativePpu"]):
        raise ValueError("Existing metric and placement PPU differ")

    cells = {cell["id"]: cell for cell in manifest["cells"] if cell["id"]}
    pictures = {}
    for asset_id, cell in cells.items():
        path = record(Path(cell["output"]))
        if sha(path) != cell["sha256"]:
            raise ValueError(f"Source crop changed: {asset_id}")
        pictures[asset_id] = rgba(path)

    old_counter = record(ROOT / "Assets/Art/PixelShopInterior35/Color/empty_counter.png")
    old_bbox, _, _ = visible_bbox(rgba(old_counter))
    new_bbox, _, _ = visible_bbox(pictures["empty_counter"])
    reference_ratio = float((old_bbox[2] - old_bbox[0]) / (new_bbox[2] - new_bbox[0]))
    q = max(1, int(np.floor(reference_ratio + 0.5)))
    source_ppu = ppu / q

    by_asset: dict[str, list[dict]] = {}
    for source_plan, path in ((plan, placement_path), (details, details_path)):
        for item in source_plan["instances"]:
            key = item.get("asset_variant") or item["asset"]
            if key in cells:
                by_asset.setdefault(key, []).append({**item, "plan_path": relative(path)})

    reports = []
    for asset_id, picture in pictures.items():
        bbox, xs, ys = visible_bbox(picture)
        instances = by_asset.get(asset_id, [])
        if not instances:
            raise ValueError(f"No existing placement owner for {asset_id}")

        positive_boxes = [item for item in instances if item.get("collider_size")
                          and all(float(x) > 0 for x in item["collider_size"])]
        geometry_kind = "existing_collision_box"
        if asset_id == "appletray":
            metric = metrics["assets"]["appletray"]
            size = np.array([metric["width_x"], metric["display_content_collision_height"],
                             metric["depth_z"]], dtype=float)
            low = np.array([-size[0] / 2.0, 0.0, -size[2] / 2.0])
            high = low + size
            geometry_source = relative(metric_path)
            geometry_kind = "current_metric_tray_collision_box"
        elif positive_boxes:
            dimensions = {tuple(float(x) for x in item["collider_size"]) for item in positive_boxes}
            if len(dimensions) != 1:
                raise ValueError(f"Same asset has differing existing dimensions: {asset_id}")
            size = np.array(next(iter(dimensions)))
            low = np.array([-size[0] / 2.0, 0.0, -size[2] / 2.0])
            high = low + size
            geometry_source = positive_boxes[0]["plan_path"]
        else:
            spec_path = ROOT / f"docs/artifacts/building35/details/{asset_id}/spec.json"
            spec = read_json(spec_path)
            points = np.array([p for face in spec["faces"] for p in face["xyz"]], dtype=float)
            low, high = points.min(axis=0), points.max(axis=0)
            size = high - low
            if np.count_nonzero(np.abs(size) < 1e-10) != 1:
                raise ValueError(f"Expected existing axis-aligned flat detail: {asset_id}")
            geometry_source = relative(spec_path)
            geometry_kind = "existing_authored_flat_detail_plane"

        corners = np.array(list(itertools.product(*zip(low, high))), dtype=float)
        projected = np.column_stack((corners @ R, corners @ U))
        projected_low, projected_high = projected.min(axis=0), projected.max(axis=0)
        projected_extent_m = projected_high - projected_low
        source_extent_m = (bbox[2:] - bbox[:2]).astype(float) / source_ppu
        necessary_axes = source_extent_m <= projected_extent_m + 1e-8

        # A fixed diagnostic hypothesis: align the source visible bbox's bottom
        # centre to the existing geometry's projected bbox bottom centre. This
        # is not a detected footpoint, support plane, or production placement.
        source_center_x = (bbox[0] + bbox[2]) * 0.5
        box_center_x = (projected_low[0] + projected_high[0]) * 0.5
        s = (xs + 0.5 - source_center_x) / source_ppu + box_center_x
        t = (bbox[3] - ys - 0.5) / source_ppu + projected_low[1]
        points = s[:, None] * R + t[:, None] * U
        centers_hit = ray_hits(points, low, high)
        all_corners_hit = np.ones(len(xs), dtype=bool)
        corner_miss_samples = 0
        for dx, dy in itertools.product((-0.5, 0.5), repeat=2):
            hits = ray_hits(points + (R * dx + U * dy) / source_ppu, low, high)
            all_corners_hit &= hits
            corner_miss_samples += int((~hits).sum())

        reports.append({
            "id": asset_id,
            "source_png": relative(Path(cells[asset_id]["output"])),
            "source_sha256": cells[asset_id]["sha256"],
            "source_canvas_px": [int(picture.shape[1]), int(picture.shape[0])],
            "source_visible_bbox_xyxy": bbox.tolist(),
            "source_visible_extent_native_px": (bbox[2:] - bbox[:2]).tolist(),
            "source_visible_extent_at_camera_k1_px": ((bbox[2:] - bbox[:2]) * q).tolist(),
            "source_visible_extent_m": source_extent_m.tolist(),
            "instances": [item["id"] for item in instances],
            "geometry_kind": geometry_kind,
            "geometry_source": geometry_source,
            "geometry_min_xyz_m": low.tolist(),
            "geometry_max_xyz_m": high.tolist(),
            "geometry_size_xyz_m": size.tolist(),
            "geometry_projected_extent_at_camera_k1_px": (projected_extent_m * ppu).tolist(),
            "source_to_geometry_projected_extent_ratio_xy": (source_extent_m / projected_extent_m).tolist(),
            "translation_independent_bbox_necessary_condition": {
                "width_fits": bool(necessary_axes[0]),
                "height_fits": bool(necessary_axes[1]),
                "status": "necessary_condition_pass_only" if bool(necessary_axes.all()) else "fail",
                "meaning": "An axis failure cannot be fixed by a different pivot/translation. An axis pass does not establish fit inside the projected convex hull.",
            },
            "hypothetical_bottom_center_ray_probe": {
                "semantic_pivot_confirmed": False,
                "visible_texels": int(len(xs)),
                "center_ray_hits": int(centers_hit.sum()),
                "center_ray_misses": int((~centers_hit).sum()),
                "texels_with_any_corner_ray_miss": int((~all_corners_hit).sum()),
                "corner_ray_miss_samples_of_four_per_texel": corner_miss_samples,
                "center_coverage_fraction": float(centers_hit.mean()),
                "all_four_corners_coverage_fraction": float(all_corners_hit.mean()),
                "hypothesis_status": "geometric_fit_under_unconfirmed_anchor" if bool(all_corners_hit.all()) else "fail_under_unconfirmed_anchor",
            },
            "production_integration_authorized_by_probe": False,
        })

    unchanged = all(sha(ROOT / name) == digest for name, digest in inputs.items())
    if not unchanged:
        raise RuntimeError("An input changed while this read-only probe ran")
    result = {
        "schema": "building36-source-fit-probe/1",
        "scope": "Read-only input suitability; necessary conditions and one unconfirmed anchor hypothesis only",
        "source_image_operations": "Read existing RGBA only. No resize, warp, pixel mutation, depth generation, collider change, or Unity write.",
        "camera_basis_local": {"pitch_degrees": 30, "yaw_degrees": 45,
                               "right": R.tolist(), "up": U.tolist(), "forward": F.tolist()},
        "uniform_display_scale": {
            "reference_old_png": relative(old_counter),
            "reference_old_visible_bbox_xyxy": old_bbox.tolist(),
            "reference_new_asset": "empty_counter",
            "reference_new_visible_bbox_xyxy": new_bbox.tolist(),
            "ratio_old_width_divided_by_new_width": reference_ratio,
            "selection": "q=max(1,floor(reference_ratio+0.5)); one common q for every crop",
            "q": q, "existing_camera_ppu": ppu, "unchanged_crop_mesh_ppu": source_ppu,
            "screen_scale_relation": "camera k integer => new crop texel screen side=q*k integer; source PNG stays unchanged",
        },
        "anchor_hypothesis": "Visible source bbox bottom centre aligned to existing geometry projected bbox bottom centre; not footprint centre. No semantic contact point can be inferred from bbox alone.",
        "limitations": [
            "Passing bbox/ray containment is not a correct semantic pivot, recovered object geometry, design approval, or scene-integration evidence.",
            "Existing collider boxes and authored flat planes are tested as provided, not expanded to fit the new art.",
            "An existing collider is not necessarily identical to the old B35 per-texel visual-depth surface; the result specifically tests the requested preserved box/plane contract.",
            "No alternative pivot search or per-object scale is attempted. A hypothetical-anchor miss alone does not prove every other translation fails.",
            "Apple-tray metric catalog overrides the older placement dimensions, matching ApplyMetricTray's current collision-size owner.",
        ],
        "assets": reports,
        "summary": {
            "asset_count": len(reports),
            "bbox_necessary_pass_ids": [r["id"] for r in reports if r["translation_independent_bbox_necessary_condition"]["status"] == "necessary_condition_pass_only"],
            "bbox_necessary_fail_ids": [r["id"] for r in reports if r["translation_independent_bbox_necessary_condition"]["status"] == "fail"],
            "hypothetical_all_corner_fit_ids": [r["id"] for r in reports if r["hypothetical_bottom_center_ray_probe"]["hypothesis_status"] == "geometric_fit_under_unconfirmed_anchor"],
            "production_pass_claimed": False,
        },
        "inputs_unchanged_after_probe": unchanged,
        "input_sha256": inputs,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": relative(output), "q": q, **result["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
