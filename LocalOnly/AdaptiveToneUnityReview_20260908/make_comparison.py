"""Presentation only: place untouched Unity PNGs side by side at native size."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 21)
labels = (("legacy", "1  Existing render"),
          ("continuous", "2  Continuous matte source"),
          ("adaptive", "3  Adaptive tone experiment"))
for view in ("front", "angle45"):
    output = root / (view + "_comparison.png")
    if output.exists():
        raise FileExistsError(output)
    sheet = Image.new("RGB", (384 * 3, 808), (29, 32, 39))
    draw = ImageDraw.Draw(sheet)
    for column, (mode, label) in enumerate(labels):
        with Image.open(root / (view + "_" + mode + ".png")) as source:
            if source.size != (384, 768):
                raise ValueError("Unexpected capture size")
            source = source.convert("RGBA")
            sheet.paste(source, (column * 384, 40), source)
        draw.text((column * 384 + 12, 9), label, font=font, fill=(236, 239, 246))
        if column:
            draw.line((column * 384, 0, column * 384, 807), fill=(69, 74, 85))
    sheet.save(output)
    print(output)
