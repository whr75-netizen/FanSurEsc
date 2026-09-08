"""Native-size montage of unmodified Unity captures; no resampling."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 22)
output = root / "front_cell_comparison.png"
if output.exists():
    raise FileExistsError(output)
sheet = Image.new("RGB", (1152, 812), (29, 32, 39))
draw = ImageDraw.Draw(sheet)
for column, cell in enumerate((2, 3, 4)):
    with Image.open(root / f"front_{cell}x{cell}.png") as source:
        if source.size != (384, 768):
            raise ValueError("Unexpected capture dimensions")
        source = source.convert("RGBA")
        sheet.paste(source, (column * 384, 44), source)
    label = f"{cell}×{cell}" + ("  현재 기본값" if cell == 2 else "")
    draw.text((column * 384 + 18, 8), label, font=font, fill=(239, 241, 247))
    if column:
        draw.line((column * 384, 0, column * 384, 811), fill=(65, 70, 82))
sheet.save(output)
print(output)
