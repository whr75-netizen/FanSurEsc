"""Inspect a fixed region of the saved actual gameplay capture; never edit pixels."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "docs/artifacts/building37/R6/final/play-interior.png"
OUTPUT = ROOT / "docs/artifacts/building37/R6/capture-blocks.json"
image = np.asarray(Image.open(CAPTURE).convert("RGB"), dtype=np.int16)
phases = []
for dy in range(4):
    for dx in range(4):
        ranges = np.array([
            np.ptp(image[y:y + 4, x:x + 4], axis=(0, 1)).max()
            for y in range(240 + dy, 386, 4)
            for x in range(40 + dx, 216, 4)
        ])
        phases.append({"phase": [dx, dy], "blocks": int(ranges.size),
                       "identical_rgb_blocks": int((ranges == 0).sum()),
                       "mean_max_channel_range": float(ranges.mean())})
region = image[240:390, 40:220]
report = {
    "capture": str(CAPTURE.relative_to(ROOT)).replace("\\", "/"),
    "capture_dimensions": [int(image.shape[1]), int(image.shape[0])],
    "scope": "Saved gameplay camera GPU readback; fixed left-shelf region only",
    "region_xywh": [40, 240, 180, 150], "block_size": 4,
    "equal_horizontal_neighbours": float((region[:, 1:] == region[:, :-1]).all(2).mean()),
    "equal_vertical_neighbours": float((region[1:] == region[:-1]).all(2).mean()),
    "phases": phases,
    "best_phase": min(phases, key=lambda row: row["mean_max_channel_range"]),
    "interpretation": "A dominant four-pixel plateau is present after renderer passes. Remaining nonconstant blocks may include occlusion, background or lighting; this is not an all-pixel equality or artistic acceptance test.",
    "source_cause_limit": "High-frequency source colour and original detector sample loss can still look soft. No palette reduction, PNG resize, new full-screen pixelation or light disabling is authorized by this observation.",
}
OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["best_phase"]))
