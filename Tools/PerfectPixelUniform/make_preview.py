"""Create a separately labelled integer nearest preview, never replace the PNG."""
import json
from pathlib import Path
import sys
from PIL import Image

result = Path(sys.argv[1])
destination = result / "output-preview-x4.png"
if destination.exists():
    raise FileExistsError(destination)
with Image.open(result / "output.png") as source:
    source.resize((source.width * 4, source.height * 4), Image.Resampling.NEAREST).save(destination)
with (result / "preview-receipt.json").open("x", encoding="utf-8") as stream:
    json.dump({"source": "output.png", "source_dimensions": [source.width, source.height],
               "preview": destination.name, "preview_dimensions": [source.width * 4, source.height * 4],
               "operation": "integer nearest x4; presentation only", "canonical_unchanged": True}, stream, indent=2)
    stream.write("\n")
