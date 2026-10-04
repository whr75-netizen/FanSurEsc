"""Final checks for the opted-in white local gradient; no asset generation."""
import hashlib
import json
import math
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/artifacts/building39/light21"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


settings = json.loads((OUT / "settings.json").read_text(encoding="utf-8"))
assert settings["sameLight"] and settings["sameMotion"] and settings["sameOtherLights"]
assert settings["white"] and settings["continuous"]
assert abs(settings["radius"] - 7.6) < 0.001
assert abs(settings["intensity"] - 4.2) < 0.001 and settings["halo"] == 0
assert settings["sceneSaved"] and settings["compileErrors"] == 0

play = json.loads((OUT / "play-observation.json").read_text(encoding="utf-8"))
assert play["isPlayMode"] and play["sameMapsAndGeometry"] and play["samePlayerAndCamera"]
assert play["shaderErrors"] == 0 and play["readableMaterials"] == 36
assert abs(play["hour"] - 21) < 0.001
assert abs(play["pixelSpacing"] - 2) < 0.001
assert abs(play["pitch"] - 30) < 0.001 and abs(play["yaw"] - 350) < 0.001

frozen = json.loads((ROOT / "docs/artifacts/building39/gold-density19/frozen-caches.json")
                    .read_text(encoding="utf-8"))
for path, expected in frozen.items():
    assert digest(ROOT / path) == expected, path
extra = json.loads((OUT / "current-material-maps.json").read_text(encoding="utf-8"))
for path, expected in extra.items():
    assert digest(ROOT / path) == expected, path

# The old night functions are unchanged, including their three authored bands.
source = "Assets/Shaders/World/NativeReadable18.hlsl"
old = subprocess.check_output(["git", "show", "HEAD:" + source], cwd=ROOT).decode("utf-8")
new = (ROOT / source).read_text(encoding="utf-8")
assert new[:new.index("// Preserve the existing night response")] == old[:old.rindex("#endif")]

# A white incident field changes only lighting strength, retaining all albedo ranks.
night = (0.10, 0.16, 0.23)
albedo = (0.62, 0.35, 0.13)
weights = []
for i in range(257):
    distance = 7.6 * i / 256
    energy = max(1 - distance / 7.6, 0) ** 2 * 4.2 * 0.55
    weight = 1 - 2 ** (-energy)
    color = tuple(n + (a - n) * weight for n, a in zip(night, albedo))
    assert math.isfinite(weight) and 0 <= weight <= 1
    assert all(min(n, a) <= c <= max(n, a) for n, a, c in zip(night, albedo, color))
    weights.append(weight)
assert weights[-1] == 0 and all(a >= b for a, b in zip(weights, weights[1:]))
assert len(set(weights)) == 257

off = OUT / "readable-off.png"
on = OUT / "readable-on.png"
with Image.open(off) as a, Image.open(on) as b:
    assert a.size == b.size and a.size[0] > 0
    size = a.size
assert digest(off) != digest(on), "The actual rendered light must change the scene."
result = {"success": True, "sourceArtFilesPreserved": len(frozen) + len(extra),
          "shaderErrors": 0, "nativePixelsOnScreen": 2, "radiusMetres": 7.6,
          "continuousDistanceSamples": len(set(weights)), "playImageSize": size,
          "scope": "Actual Play captures plus bounded math/code checks; aesthetic perfection is not asserted."}
(OUT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
