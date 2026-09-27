"""Read-only final checks of Building31 Unity observations, not art approval."""
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
READBACK = ROOT / "LocalOnly/Building31/readback.json"
MINIMUMS = {"nativeSprites": 12, "rendererCount": 20, "colliderCount": 8}
FLAGS = (
    "prefabExists", "entryReached", "wallBlocked", "occlusionObserved",
    "cameraContractMatched", "samePlayer", "sameCamera",
)


def project_path(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Nonempty file path required")
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve(strict=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(payload):
    errors = []
    details = {}
    if not isinstance(payload, dict) or set(payload) != {"readback"}:
        raise ValueError("stdin must contain only the observe output: readback")
    readback = project_path(payload["readback"])
    if readback != READBACK.resolve():
        raise ValueError("Observation path differs from the frozen Building31 contract")
    data = json.loads(readback.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Unity readback must be a JSON object")

    if data.get("scene") != "GameMap1":
        errors.append("scene must equal GameMap1")
    for key in FLAGS:
        if data.get(key) is not True:
            errors.append(f"{key} must be JSON true from Unity observation")
    for key, minimum in MINIMUMS.items():
        value = data.get(key)
        if type(value) is not int or value < minimum:
            errors.append(f"{key} must be an integer >= {minimum}")
        details[key] = value

    try:
        screenshot = project_path(data.get("screenshot"))
        if screenshot.suffix.lower() != ".png" or not screenshot.is_file():
            raise ValueError("Screenshot must be an existing PNG file")
        with Image.open(screenshot) as picture:
            if picture.format != "PNG" or min(picture.size) <= 0:
                raise ValueError("Screenshot is not a valid PNG raster")
            details["screenshotSize"] = list(picture.size)
            picture.verify()
        details["screenshot"] = str(screenshot)
        details["screenshotSha256"] = sha256(screenshot)
    except (OSError, ValueError) as exc:
        errors.append(f"screenshot: {exc}")

    return {
        "technicalChecksPassed": not errors,
        "artApproval": "awaiting_user_visual_feedback",
        "readback": str(readback),
        "readbackSha256": sha256(readback),
        "checks": details,
        "errors": errors,
        "evidenceBoundary": "Unity writes the observations. This checks their contract and the captured PNG; it does not independently replay gameplay or judge appearance.",
    }


def main():
    try:
        result = validate(json.load(sys.stdin))
    except (OSError, ValueError, TypeError) as exc:
        result = {"technicalChecksPassed": False, "errors": [str(exc)],
                  "artApproval": "not_requested_technical_failure"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["technicalChecksPassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
