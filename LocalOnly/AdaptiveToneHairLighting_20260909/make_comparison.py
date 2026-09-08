"""Assemble six untouched 384x768 Unity captures at native size.

No resize, crop, filtering, recoloring, alpha compositing or source overwrite.
RGBA pixels are pasted without a mask, preserving each source pixel exactly.
The capture script writes the JSON manifest before this script is run.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "front_hair_lighting_comparison.png"
WIDTH, HEIGHT = 384, 768
GUTTER, HEADER, ROW_LABEL, FOOTER = 12, 88, 50, 58
MODES = (("source", "연속 명암 원본"), ("old", "기존 방식"), ("new", "새 방식 · 머리카락 광량"))
LIGHTING = (("dim", "어두운 조명 · 밝은 조명의 12%"), ("bright", "밝은 조명 · 기준 세기"))


def main():
    if OUTPUT.exists():
        raise FileExistsError(f"Preserving existing comparison: {OUTPUT}")
    manifest = json.loads((ROOT / "comparison_manifest.json").read_text(encoding="utf-8"))
    for field in ("samePlayer", "sameCamera", "sameFrame", "samePose", "restored"):
        if manifest.get(field) is not True:
            raise ValueError(f"Capture manifest did not confirm {field}")
    # The first completed capture's dynamic DTO array was omitted by JsonUtility.
    # Its common frame/identity/restoration checks and six source PNGs survived.
    # Preserve that manifest; layout can use the already recorded shared settings.
    records = manifest.get("captureRecords")
    if records is not None:
        records = [json.loads(item) if isinstance(item, str) else item for item in records]
        if len(records) != 6:
            raise ValueError("Expected exactly six captures")
        records = {item["file"]: item for item in records}
        if len(records) != 6:
            raise ValueError("Duplicate capture records")
    if manifest["frameStart"] != manifest["frameEnd"] or manifest["pixelCellSize"] != 2:
        raise ValueError("Shared capture conditions changed")
    font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 22)
    small = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 18)
    sheet_width = WIDTH * 3 + GUTTER * 4
    sheet_height = HEADER + 2 * (ROW_LABEL + HEIGHT + GUTTER) + FOOTER
    sheet = Image.new("RGBA", (sheet_width, sheet_height), (29, 32, 39, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((GUTTER, 9), "동일 프레임 · 정면 · 2px 셀 · 원본 크기 384×768", font=font, fill=(239, 241, 247, 255))
    for column, (_, title) in enumerate(MODES):
        draw.text((GUTTER + column * (WIDTH + GUTTER), 49), title, font=font, fill=(239, 241, 247, 255))
    for row, (lighting, title) in enumerate(LIGHTING):
        top = HEADER + row * (ROW_LABEL + HEIGHT + GUTTER)
        scale = .12 if lighting == "dim" else 1.
        first = {name: manifest[name] * scale for name in ("keyIntensity", "fillIntensity", "ambientIntensity")}
        light_values = f"키 {first['keyIntensity']:.3f} / 보조 {first['fillIntensity']:.3f} / 주변 {first['ambientIntensity']:.3f}"
        draw.text((GUTTER, top + 4), f"{title}    {light_values}", font=small, fill=(210, 218, 232, 255))
        for column, (mode, _) in enumerate(MODES):
            filename = f"front_{lighting}_{mode}.png"
            if records is not None:
                record = records[filename]
                if record["frame"] != manifest["frameStart"] or record["cellSize"] != 2 or record["worldYaw"] != 180:
                    raise ValueError(f"Capture conditions changed: {filename}")
                if record["lighting"] != lighting or record["mode"] != mode:
                    raise ValueError(f"Capture record/file mismatch: {filename}")
            with Image.open(ROOT / filename) as source:
                source.load()
                if source.size != (WIDTH, HEIGHT) or source.mode != "RGBA":
                    raise ValueError(f"Unexpected native capture format: {filename}: {source.size} {source.mode}")
                # No mask: copy all RGBA channels verbatim, including transparency.
                sheet.paste(source, (GUTTER + column * (WIDTH + GUTTER), top + ROW_LABEL))
    draw.text((GUTTER, sheet_height - FOOTER + 9), "머리카락 상대 오차 0.10 · 최소 광량 0.02 | 보간·보정 없이 원본 픽셀 배치", font=small, fill=(210, 218, 232, 255))
    with OUTPUT.open("xb") as handle:
        sheet.save(handle, format="PNG")
    print(OUTPUT)


if __name__ == "__main__":
    main()
