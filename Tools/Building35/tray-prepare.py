"""Single three-plane tray experiment. Run only from the owning work graph."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/artifacts/building35/tray-size-correction"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deps", type=Path, default=ROOT / "LocalOnly/PerfectPixelPalette_20260906/.deps")
    args = parser.parse_args()
    sys.path.insert(0, str(args.deps.resolve(strict=True)))
    from project_faces import project

    catalog_path = ROOT / "Tools/Building35/metric-catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
    metric = catalog["assets"]["appletray"]
    annotations_path = OUT / "source-corners-proposal.json"
    annotations = json.loads(annotations_path.read_text(encoding="utf-8-sig"))
    source = ROOT / annotations["source"]
    if annotations["source"] != metric["source"] or hashlib.sha256(source.read_bytes()).hexdigest() != annotations["source_sha256"]:
        raise ValueError("Tray source changed after source-face observation")
    w, d, h = metric["width_x"], metric["depth_z"], metric["crate_height_y"]
    if min(w, d, h) <= 0 or catalog["nativePpu"] != 127 or catalog["camera"] != {"pitch": 30, "local_yaw": 45}:
        raise ValueError("This experiment requires positive metric dimensions and the fixed B35 projection")
    vertices = {"top_back": [w/2,h,d/2], "top_left": [-w/2,h,d/2],
                "top_right": [w/2,h,-d/2], "top_near": [-w/2,h,-d/2],
                "bottom_left": [-w/2,0,d/2], "bottom_right": [w/2,0,-d/2], "bottom_near": [-w/2,0,-d/2]}
    spec = {"id": "appletray_metric", "source": annotations["source"], "ppu": catalog["nativePpu"],
            "preserve_outline": True, "ground_from_source_outline": True,
            "faces": [{"id": face_id, "source_xy": [annotations["vertices"][key]["xy"] for key in keys],
                       "xyz": [vertices[key] for key in keys]} for face_id, keys in annotations["faces"].items()],
            "limitations": annotations["limits"] + ["Existing project_faces alpha>=128/binary-alpha policy is reused unchanged.",
                "Three-plane experimental output requires actual first-view and fruit-size review before integration."],
            "metric_catalog": catalog_path.relative_to(ROOT).as_posix(),
            "metric_catalog_sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
            "source_annotation": annotations_path.relative_to(ROOT).as_posix()}
    folder = OUT / "appletray_metric"
    manifest_path = OUT / "production-manifest.json"
    if folder.exists() or manifest_path.exists():
        raise FileExistsError("Preserve existing tray experiment outputs; do not silently regenerate")
    OUT.mkdir(parents=True, exist_ok=True)
    project(spec, folder)
    manifest = {"schema": "building35-tray-experiment-manifest/1", "status": "experiment_not_art_approved",
                "assets": [{"id": "appletray_metric", "folder": folder.relative_to(ROOT).as_posix(),
                            "receipt": (folder / "receipt.json").relative_to(ROOT).as_posix()}]}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "experiment_prepared", "manifest": str(manifest_path)}))


if __name__ == "__main__":
    main()
