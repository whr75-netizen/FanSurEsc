"""Check restoration of the existing three-step light and its actual observation."""
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/artifacts/building39/light22/final"
r = json.loads((OUT / "settings.json").read_text(encoding="utf-8"))
assert r["sameLight"] and r["sameMotion"] and r["sameOtherLights"] and r["white"]
assert r["surfaceBands"] == 3 and r["halo"] == 0 and r["sceneSaved"]
assert abs(r["radius"] - 14) < .001 and abs(r["intensity"] - .8) < .001
assert r["floorPeakInput"] >= .75, "The highest floor-light band must be attainable."
assert r["compileErrors"] == 0
p = json.loads((OUT / "play-observation.json").read_text(encoding="utf-8"))
assert p["isPlayMode"] and p["sameMapsAndGeometry"] and p["samePlayerAndCamera"]
assert p["shaderErrors"] == 0 and p["readableMaterials"] == 36
assert abs(p["hour"]-21) < .001 and abs(p["pixelSpacing"]-2) < .001
assert abs(p["pitch"]-30) < .001 and abs(p["yaw"]-350) < .001
for path in ["Assets/Scripts/WorldLighting/SteppedLocalLight.cs",
             "Assets/Rendering/LocalLighting/SteppedLocalLightCommon.hlsl",
             "Assets/Shaders/World/NativeReadable18.hlsl",
             "Assets/Shaders/World/NativePaletteSurface16.shader"]:
    previous = subprocess.check_output(["git", "show", "8711b7c:"+path], cwd=ROOT).decode("utf-8")
    assert (ROOT/path).read_text(encoding="utf-8") == previous.replace("\r\n", "\n"), path
frozen = json.loads((ROOT / "docs/artifacts/building39/gold-density19/frozen-caches.json")
                    .read_text(encoding="utf-8"))
extra = json.loads((ROOT / "docs/artifacts/building39/light21/current-material-maps.json")
                   .read_text(encoding="utf-8"))
for path, digest in {**frozen, **extra}.items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
# The input and final quantizers must retain three distinct levels in the
# existing night fixture. A high intensity makes the middle and high bands equal.
night_y = .03*.2126729 + .045*.7151522 + .085*.0721750
def band(value):
    return int(value >= .12) + int(value >= .4)
new_bands = [band(night_y + q*.8*.55) for q in [0, .5, 1]]
old_bands = [band(night_y + q*4.2*.55) for q in [0, .5, 1]]
assert new_bands == [0, 1, 2] and old_bands == [0, 2, 2]
with Image.open(OUT/"readable-on.png") as im:
    size = im.size
assert (OUT/"readable-on.png").read_bytes() != (OUT/"readable-off.png").read_bytes()
result = {"success": True, "sourceArtFilesPreserved":len(frozen)+len(extra),
          "surfaceBands":3, "nativeBrightnessLevels":[.55,.78,1], "fixtureBands":new_bands,
          "priorHighIntensityBands":old_bands, "restoredCalculationFiles":4,
          "shaderErrors":0, "nativePixelsOnScreen":2, "playImageSize":size,
          "scope":"Actual Play plus existing-path/math checks; not an aesthetic approval."}
(OUT/"validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result))
