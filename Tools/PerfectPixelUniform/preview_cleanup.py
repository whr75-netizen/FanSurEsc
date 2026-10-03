"""Render a labelled native crop at integer nearest zoom; not a production asset."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--result", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("미리보기를 덮어쓰지 않습니다.")
box = (80, 70, 208, 198)
with Image.open(args.source) as source, Image.open(args.result) as result:
    if source.size != result.size:
        raise RuntimeError("색 정리 전후 해상도가 다릅니다.")
    panel = Image.new("RGB", (1032, 540), (30, 32, 35))
    draw = ImageDraw.Draw(panel)
    draw.text((8, 8), "SOURCE: 128x128 crop, nearest 4x", fill=(240, 240, 240))
    draw.text((524, 8), "CLEANUP: same crop, nearest 4x", fill=(240, 240, 240))
    for x, image in ((0, source), (520, result)):
        crop = image.crop(box).convert("RGBA").resize((512, 512), Image.Resampling.NEAREST)
        panel.paste(crop, (x, 28), crop)
    panel.save(args.output)
print(str(args.output.resolve()))
