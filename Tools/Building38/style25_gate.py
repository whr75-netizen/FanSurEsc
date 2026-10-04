"""Actual light-source diagnosis and material-coloured native boundaries."""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/artifacts/building39/style25"
AFTER = OUT / "after"
COMPARISON = OUT / "material-comparison"


def rgb(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255


def linear(c):
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def wall_lamp(value):
    return abs(value["intensity"] - .12) < .001 and abs(value["radius"] - 3.2) < .001


def retained(lights):
    values = []
    for item in lights:
        value = dict(item["MonoBehaviour"])
        if wall_lamp(value):
            value.pop("color")
        values.append(json.dumps(value, sort_keys=True))
    return Counter(values)


before = json.loads((OUT / "baseline-lights.json").read_text())
after = json.loads((OUT / "final-lights.json").read_text())
assert retained(before) == retained(after), "Unrequested light settings changed"
changed = [v["MonoBehaviour"] for v in after if wall_lamp(v["MonoBehaviour"])]
assert len(changed) == 2 and all(v["color"] == dict(r=1, g=1, b=1, a=1) for v in changed)
edit = json.loads((OUT / "edit-final.json").read_text())
assert edit["editMode"] and edit["sceneSaved"] and edit["whiteWallLamps"] == 2
p = json.loads((AFTER / "play-observation.json").read_text())
assert p["isPlayMode"] and p["sameMapsAndGeometry"] and p["samePlayerAndCamera"]
assert p["shaderErrors"] == 0 and abs(p["pixelSpacing"] - 2) < .001
assert abs(p["pitch"] - 30) < .001 and abs(p["yaw"] - 350) < .001
r = json.loads((AFTER / "additive-receipt.json").read_text())
assert abs(r["intensity"] - .4) < .001 and abs(r["radius"] - 5) < .001
assert r["surfaceBands"] == 3 and r["color"] == dict(r=1, g=1, b=1, a=1)
frozen = json.loads((ROOT / "docs/artifacts/building39/gold-density19/frozen-caches.json").read_text())
extra = json.loads((ROOT / "docs/artifacts/building39/light21/current-material-maps.json").read_text())
for path, digest in {**frozen, **extra}.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
# A wall-lamp toggle is the observed cause, distinct from amber bottle material.
warm_delta = linear(rgb(OUT / "before/irradiance-warm-on.png")) - linear(rgb(OUT / "before/irradiance-warm-off.png"))
region = warm_delta[35:340, :180]
warm_hit = np.max(abs(region), -1) > .003
warm_rgb = region[warm_hit].mean(0)
assert warm_hit.sum() >= 100 and warm_rgb[0] > warm_rgb[1] > warm_rgb[2]
# Compare the saved material parameter on the actual camera path. Existing
# occlusion fading composites some boundaries over a visible background.
on = rgb(AFTER / "moving-on.png")
colored = rgb(COMPARISON / "colored-boundaries.png")
black = rgb(COMPARISON / "black-boundaries.png")
surface = rgb(COMPARISON / "surface-boundaries.png")
receipt = json.loads((COMPARISON / "boundary-receipt.json").read_text())
assert receipt["actualPlay"] and receipt["onlySavedBoundaryParameterVaried"]
edge = np.max(abs(colored - black), -1) > 2 / 255
assert edge.sum() >= 100
opaque = edge & (np.max(black, -1) <= 1 / 255)
blend = edge & ~opaque
assert opaque.sum() >= 100
assert np.max(abs(colored[opaque] - surface[opaque] * .8)) <= 2 / 255, "Opaque boundary sRGB ratio differs"
assert np.max(abs(surface[~edge] - colored[~edge])) <= 2 / 255, "Non-boundary surface changed"
assert np.all(colored[edge].mean(-1) < surface[edge].mean(-1)), "Boundary must be darker"
low, high = np.minimum(black, surface) - 2 / 255, np.maximum(black, surface) + 2 / 255
assert not np.any(((colored < low) | (colored > high))[blend]), "Blended boundary is not between its two endpoints"
# B cancels in linear RGB: (render(.8)-render(0))/(render(1)-render(0)).
# The .8 sRGB ramp maps to a linear gain within [.8**2.4,.8]; tolerate
# 8-bit conversion only where the endpoint difference is measurable.
d = linear(surface) - linear(black)
c = linear(colored) - linear(black)
valid = (d >= .03) & blend[:, :, None]
ratios = c[valid] / d[valid]
assert np.all((ratios >= .8**2.4 - .02) & (ratios <= .8 + .02))
gpu = rgb(AFTER / "gpu-additive.png")
neutral = np.ptp(gpu, axis=-1) <= 1 / 255
energy = linear(gpu).mean(-1)
levels = np.array([0, .4 * .55 / 3, .4 * .55 * 2 / 3, .4 * .55])
counts = [int((neutral & (abs(energy - v) <= .005)).sum()) for v in levels]
assert min(counts) >= 100
delta = linear(on) - linear(rgb(AFTER / "moving-off.png"))
white_counts = []
for v in levels[1:]:
    hit = neutral & ~edge & (abs(energy - v) <= .005)
    hit &= np.max(abs(delta - v), -1) <= .015
    white_counts.append(int(hit.sum()))
assert min(white_counts) >= 100, "Three final white contributions missing on non-boundaries"
grid = []
pixels = np.rint(gpu * 255).astype(np.uint8)
for x0, x1, y0, y1 in [(200, 400, 400, 580), (720, 850, 350, 700)]:
    ys, xs = np.arange(y0 + (1-y0) % 2, y1-1, 2), np.arange(x0, x1-1, 2)
    blocks = np.stack([pixels[ys[:, None]+dy, xs[None, :]+dx] for dy in range(2) for dx in range(2)], axis=2)
    mismatch = int(np.any(blocks != blocks[:, :, :1, :], axis=(2, 3)).sum())
    assert mismatch == 0
    grid.append({"boundsXY": [x0, x1, y0, y1], "mismatchedBlocks": mismatch})
result = {"success": True, "warmShelfPixels": int(warm_hit.sum()),
          "warmShelfMeanLinearRGB": warm_rgb.tolist(), "coloredBoundaryPixels": int(edge.sum()),
          "opaqueBoundaryPixels": int(opaque.sum()), "blendedBoundaryPixels": int(blend.sum()),
          "opaqueMaxSRGBError": float(np.max(abs(colored[opaque] - surface[opaque] * .8))),
          "blendedLinearRatioMinMax": [float(ratios.min()), float(ratios.max())],
          "boundarySRGBScale": .8, "gpuLightPixels": counts, "finalNonEdgeWhitePixels": white_counts,
          "floorGridChecks": grid, "artFilesPreserved": len({**frozen, **extra}),
          "scope": "Existing building objects; actual Play colour/owner/grid checks, not character or aesthetic approval."}
(OUT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
