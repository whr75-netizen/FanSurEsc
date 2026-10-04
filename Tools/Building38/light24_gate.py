"""One actual-game gate for bounded, three-step white light and native pixels."""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/artifacts/building39/light24"


def image(name):
    return np.asarray(Image.open(OUT / name).convert("RGB"), dtype=np.float64) / 255


def linear(rgb):
    return np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)


def preserved_settings(lights):
    values = []
    for item in lights:
        value = dict(item["MonoBehaviour"])
        if value["additiveNativePresentation"]:
            # Only this existing light's requested range and intensity may change.
            value.pop("radius")
            value.pop("intensity")
        values.append(json.dumps(value, sort_keys=True))
    return Counter(values)


r = json.loads((OUT / "additive-receipt.json").read_text(encoding="utf-8"))
edit = json.loads((OUT / "edit-final.json").read_text(encoding="utf-8"))
before = json.loads((OUT / "baseline-lights.json").read_text(encoding="utf-8"))
after = json.loads((OUT / "final-lights.json").read_text(encoding="utf-8"))
assert edit["editMode"] and edit["sceneSaved"] and edit["additiveOptIn"]
assert preserved_settings(before) == preserved_settings(after), "Unrequested light settings changed"
assert sum(x["MonoBehaviour"]["additiveNativePresentation"] for x in after) == 1
assert r["actualPlay"] and r["baseTintWhite"] and r["additiveOptIn"]
assert r["surfaceBands"] == 3 and r["color"] == {"r": 1, "g": 1, "b": 1, "a": 1}
assert abs(r["intensity"] - .4) < .001 and abs(r["radius"] - 5) < .001
assert all(abs(v - .55) < .001 for v in r["strengthValues"])
p = json.loads((OUT / "play-observation.json").read_text(encoding="utf-8"))
assert p["isPlayMode"] and p["sameMapsAndGeometry"] and p["samePlayerAndCamera"]
assert p["shaderErrors"] == 0 and abs(p["pixelSpacing"] - 2) < .001
assert abs(p["pitch"] - 30) < .001 and abs(p["yaw"] - 350) < .001
frozen = json.loads((ROOT / "docs/artifacts/building39/gold-density19/frozen-caches.json").read_text(encoding="utf-8"))
extra = json.loads((ROOT / "docs/artifacts/building39/light21/current-material-maps.json").read_text(encoding="utf-8"))
for path, digest in {**frozen, **extra}.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
gpu = image("gpu-additive.png")
neutral = (np.max(gpu, -1) - np.min(gpu, -1)) <= 1 / 255
energy = linear(gpu).mean(-1)
expected = np.array([0, .4 * .55 / 3, .4 * .55 * 2 / 3, .4 * .55])
counts = [int(np.sum(neutral & (np.abs(energy - level) <= .005))) for level in expected]
assert min(counts) >= 100, f"Three positive GPU regions plus zero required: {counts}"
prior = json.loads((ROOT / "docs/artifacts/building39/light23/validation.json").read_text(encoding="utf-8"))
assert sum(counts[1:]) < sum(prior["gpuRegionPixels"][1:]), "Illuminated area did not shrink"
off, on = linear(image("moving-off.png")), linear(image("moving-on.png"))
delta = on - off
white_counts = []
for level in expected[1:]:
    hit = neutral & (np.abs(energy - level) <= .005)
    hit &= np.max(np.abs(delta - level), -1) <= .015
    white_counts.append(int(hit.sum()))
assert min(white_counts) >= 100, f"White RGB additions must survive final shading: {white_counts}"
# These two floor patches were audited before editing. They exclude objects
# and characters: the check concerns native light pixels, not the whole frame.
rois = [(200, 400, 400, 580), (720, 850, 350, 700)]
pixels = np.rint(gpu * 255).astype(np.uint8)
grid_checks = []
for x0, x1, y0, y1 in rois:
    ys = np.arange(y0 + (1 - y0) % 2, y1 - 1, 2)
    xs = np.arange(x0 + (0 - x0) % 2, x1 - 1, 2)
    blocks = np.stack([pixels[ys[:, None] + dy, xs[None, :] + dx]
                       for dy in range(2) for dx in range(2)], axis=2)
    mismatch = int(np.any(blocks != blocks[:, :, :1, :], axis=(2, 3)).sum())
    assert mismatch == 0, f"Floor native 2x2 block split: {mismatch}"
    grid_checks.append({"boundsXY": [x0, x1, y0, y1], "phaseXY": [0, 1],
                        "blockCount": int(len(xs) * len(ys)), "mismatchedBlocks": mismatch,
                        "distinctRGB": int(len(np.unique(blocks[:, :, 0, :].reshape(-1, 3), axis=0)))})
assert max(v["distinctRGB"] for v in grid_checks) >= 2, "Floor checks missed the light boundary"
assert np.any(image("moving-right.png") != image("moving-on.png"))
result = {"success": True, "actualLinearAdditiveLevels": expected.tolist(),
          "gpuRegionPixels": counts, "finalWhiteAdditionPixels": white_counts,
          "priorIlluminatedPixels": sum(prior["gpuRegionPixels"][1:]),
          "illuminatedPixels": sum(counts[1:]), "floorGridChecks": grid_checks,
          "sourceArtFilesPreserved": len({**frozen, **extra}), "shaderErrors": 0,
          "nativePixelsOnScreen": 2,
          "scope": "Actual Play GPU, final RGB and two floor ROIs; no aesthetic or whole-frame pixel guarantee."}
(OUT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
