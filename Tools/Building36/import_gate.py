"""Read actual B36 artifacts; material import alone cannot complete scene replacement."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/artifacts/building36"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("input", "integration"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve prior gate report: " + str(args.output))
    failures, evidence = [], {}

    def fail(code, stage, detail):
        failures.append({"code": code, "stage": stage, "detail": detail})

    try:
        paths = {"import": BASE / "unity-import.json", "technical": BASE / "technical-validation.json",
                 "fit": BASE / "source-fit.json", "manifest": BASE / "slices/manifest.json"}
        data = {key: read(path) for key, path in paths.items()}
        evidence["input_sha256"] = {str(path.relative_to(ROOT)): sha(path) for path in paths.values()}
        manifest, imported, technical, fit = (data[k] for k in ("manifest", "import", "technical", "fit"))
        objects = {item["id"]: item for item in manifest["cells"] if item["role"] == "object"}
        items = imported.get("items", [])
        evidence["imported_count"] = len(items)
        if len(objects) != 18 or len(items) != 18 or {item.get("id") for item in items} != set(objects):
            fail("IMPORT_SET_MISMATCH", "import", "Expected all 18 canonical object IDs exactly once")
        if imported.get("exactNativeImports") is not True:
            fail("IMPORT_READBACK_FAILED", "import", "Unity did not confirm native imports")
        if imported.get("canonicalSheetHash") != manifest["native_sha256"]:
            fail("CANONICAL_HASH_MISMATCH", "import", "Import does not reference this normalized sheet")
        for item in items:
            cell = objects.get(item.get("id"))
            if cell is None:
                continue
            original, asset = Path(cell["output"]), ROOT / item["asset"]
            expected = cell["sha256"]
            if not (sha(original) == sha(asset) == expected == item.get("sourceHash") == item.get("importedHash")):
                fail("IMPORTED_PNG_CHANGED", "import", item["id"])
            if (item.get("rgbaMismatches") != 0 or item.get("unchangedPng") is not True
                    or item.get("fullRect") is not True
                    or [item.get("width"), item.get("height")] != cell["canvas_px"]):
                fail("IMPORTED_TEXELS_CHANGED", "import", item["id"])
        observed = technical.get("observed_regions", {})
        if (technical.get("exit_code") != 0 or technical.get("failures") != []
                or technical.get("native_sha256") != manifest["native_sha256"]
                or observed.get("rgba_identical_to_source_crop") != 20
                or technical.get("partition_area_px") != technical.get("sheet_area_px")):
            fail("CANONICAL_CROP_VALIDATION_FAILED", "slice", "Expected complete exact RGBA partition")
        for path, expected in fit.get("input_sha256", {}).items():
            if sha(ROOT / path) != expected:
                fail("SOURCE_FIT_INPUT_CHANGED", "source_fit", path)
        if fit.get("inputs_unchanged_after_probe") is not True:
            fail("SOURCE_FIT_INPUT_UNVERIFIED", "source_fit", "Probe input stability was not confirmed")
        fit_assets = fit.get("assets", [])
        if len(fit_assets) != 18 or {item.get("id") for item in fit_assets} != set(objects):
            fail("SOURCE_FIT_SET_MISMATCH", "source_fit", "Expected necessary conditions for all 18 objects")
        geometry_failures = [item["id"] for item in fit_assets
                             if item.get("translation_independent_bbox_necessary_condition", {}).get("status") != "pass"]
        evidence["collider_as_visual_proxy_candidate"] = {
            "status": "rejected" if geometry_failures else "necessary_condition_only",
            "bbox_fail_ids": geometry_failures,
            "scope": "The proposed collider-box proxy only; this is not the existing B35 visual-depth surface",
            "does_not_prove_all_unity_integration_impossible": True}
        # This project has not authored a mapping from the NEW canonical colour
        # texels to the preserved visual depth/roof/character-occlusion contract.
        # Existing collider boxes are not that visual geometry. Neither the old
        # warped colour/depth raster nor an approval boolean can supply it.
        # Reopen this implementation boundary with its actual producer and
        # readback validator; do not turn a file-existence check into a pass.
        evidence["native_depth_mapping"] = {
            "status": "not_authored",
            "current_implementation": "No B36 canonical-colour-to-preserved-visual-depth producer or validator",
            "preserved_contract": "Existing roof and character occlusion, independently of collider proxy shape"}
        fail("NATIVE_DEPTH_MAPPING_NOT_AUTHORED", "depth_mapping",
             "New canonical texels need an authored mapping preserving existing visual-depth occlusion; no such producer/validator is implemented")
        evidence["material_import_is_scene_integration"] = False
        if args.mode == "integration":
            path = BASE / "unity-integration.json"
            scene = read(path)
            evidence["input_sha256"][str(path.relative_to(ROOT))] = sha(path)
            bindings = scene.get("bindings", [])
            expected_instances = {(item["id"], instance) for item in fit_assets for instance in item["instances"]}
            actual_instances = {(item.get("id"), item.get("instance")) for item in bindings}
            if len(bindings) != len(expected_instances) or actual_instances != expected_instances:
                fail("SCENE_BINDING_SET_MISMATCH", "integration", "All existing planned instances need actual readback")
            asset_by_id = {item["id"]: item["asset"] for item in items}
            references = {}
            for binding in bindings:
                key = (binding.get("id"), binding.get("instance"))
                before, after = binding.get("before", {}), binding.get("after", {})
                if not before.get("instanceId") or before.get("instanceId") != after.get("instanceId"):
                    fail("SCENE_INSTANCE_REPLACED", "integration", key)
                for field in ("meshDepthHash", "colliderHash"):
                    if not before.get(field) or before.get(field) != after.get(field):
                        fail("PRESERVED_CONTRACT_CHANGED", "integration", [key, field])
                if after.get("localScale") != [1, 1, 1] or after.get("spriteAsset") != asset_by_id.get(binding.get("id")):
                    fail("SCENE_SPRITE_BINDING_INVALID", "integration", key)
                ref = after.get("spriteGuid")
                if not ref or references.setdefault(binding.get("id"), ref) != ref:
                    fail("DUPLICATED_SPRITE_REFERENCE", "integration", key)
            if scene.get("scenePath") != "Assets/Scenes/GameMap1.unity" or scene.get("sceneIntegrated") is not True:
                fail("SCENE_NOT_INTEGRATED", "integration", "Unity scene integration readback missing")
            preview = ROOT / scene.get("gameViewCapture", "")
            if not preview.is_file() or sha(preview) != scene.get("gameViewCaptureSha256"):
                fail("GAME_VIEW_CAPTURE_MISSING", "integration", "Actual final camera capture is required")
    except (OSError, ValueError, KeyError, TypeError) as error:
        fail("EVIDENCE_UNAVAILABLE", args.mode, str(error))
    report = {"schema": "building36-import-gate/1", "mode": args.mode, "evidence": evidence,
              "failures": failures, "exit_code": 2 if failures else 0,
              "production_complete": args.mode == "integration" and not failures,
              "limits": ["Collider-box proxy failure is not failure of every Unity integration or actual B35 visual geometry",
                         "The native-depth producer and validator are unimplemented; the integration branch cannot pass yet",
                         "Unity readback is produced by Editor observation, not AI approval flags",
                         "Input gate success permits only the scoped integration attempt; it is not completion"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"report": str(args.output), "failures": len(failures), "exit_code": report["exit_code"],
                      "production_complete": report["production_complete"]}))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
