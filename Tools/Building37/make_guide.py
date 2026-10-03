"""Rasterize the vector generation diagram; this is never a game texture."""
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

base = Path(__file__).resolve().parent
svg = ET.parse(base / "guide.svg").getroot()
scale = 4
image = Image.new("RGB", (int(svg.attrib["width"])*scale, int(svg.attrib["height"])*scale), "#0e1820")
draw = ImageDraw.Draw(image)
for item in svg.iter():
    kind = item.tag.rsplit("}",1)[-1]
    a = item.attrib
    if kind == "polygon":
        points = [tuple(float(v)*scale for v in pair.split(",")) for pair in a["points"].split()]
        draw.polygon(points, fill=a["fill"], outline=a["stroke"], width=2)
    elif kind == "rect" and "x" in a:
        x,y,w,h = [float(a.get(k,0))*scale for k in ("x","y","width","height")]
        draw.rectangle((x,y,x+w,y+h), outline=a["stroke"], width=1)
    elif kind == "text":
        draw.text((float(a["x"])*scale,float(a["y"])*scale-12), item.text or "", fill=a["fill"])
output = base / "guide.png"
if output.exists():
    raise FileExistsError("Do not overwrite the generation diagram")
image.save(output)
print(output)
