"""Actual GPU light levels and white additions, with original native art preserved."""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/artifacts/building39/light23"


def image(name):
    return np.asarray(Image.open(OUT / name).convert("RGB"), dtype=np.float64) / 255


def linear(rgb):
    return np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)


r = json.loads((OUT / "additive-receipt.json").read_text(encoding="utf-8"))
edit = json.loads((OUT / "edit-final.json").read_text(encoding="utf-8"))
assert edit["editMode"] and edit["sceneSaved"] and edit["additiveOptIn"]
before = json.loads((OUT / "baseline-lights.json").read_text(encoding="utf-8"))
after = json.loads((OUT / "final-lights.json").read_text(encoding="utf-8"))
def regular_settings(lights):
    values = []
    for item in lights:
        value = dict(item["MonoBehaviour"])
        value.pop("additiveNativePresentation")
        values.append(json.dumps(value, sort_keys=True))
    return Counter(values)
assert regular_settings(before) == regular_settings(after), "Existing light settings changed"
assert sum(x["MonoBehaviour"]["additiveNativePresentation"] for x in after) == 1
assert r["actualPlay"] and r["baseTintWhite"] and r["additiveOptIn"]
assert r["surfaceBands"] == 3 and r["color"] == {"r": 1, "g": 1, "b": 1, "a": 1}
assert abs(r["intensity"] - .8) < .001 and abs(r["radius"] - 14) < .001
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
# NativeAdditiveLight diagnostic encodes the actual opt-in contribution only.
# Coloured non-native character pixels are excluded, not accepted as band data.
neutral = (np.max(gpu, -1) - np.min(gpu, -1)) <= 1 / 255
energy = linear(gpu).mean(-1)
expected = np.array([0, .8 * .55 / 3, .8 * .55 * 2 / 3, .8 * .55])
counts = [int(np.sum(neutral & (np.abs(energy - level) <= .005))) for level in expected]
assert min(counts) >= 100, f"Three positive GPU regions plus zero required: {counts}"
off, on = linear(image("moving-off.png")), linear(image("moving-on.png"))
delta = on - off
white_delta_counts = []
for level in expected[1:]:
    hit = neutral & (np.abs(energy - level) <= .005)
    hit &= np.max(np.abs(delta - level), -1) <= .015
    white_delta_counts.append(int(hit.sum()))
assert min(white_delta_counts) >= 100, f"White RGB additions must survive final shading: {white_delta_counts}"
assert np.any(image("moving-right.png") != image("moving-on.png"))
result = {"success": True, "actualLinearAdditiveLevels": expected.tolist(),
          "gpuRegionPixels": counts, "finalWhiteAdditionPixels": white_delta_counts,
          "sourceArtFilesPreserved": len({**frozen, **extra}), "shaderErrors": 0,
          "nativePixelsOnScreen": 2,
          "scope": "Actual game GPU and final RGB deltas; no aesthetic-perfect or arbitrary-view claim."}
(OUT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
