"""Technical contact sheets: place actual unscaled capture PNGs under labels.

No filtering, recoloring, inferred pixels, crops, or generated character art.
Transparent pixels are displayed on a neutral presentation background only.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
FONT=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22)
SMALL=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)

def sheet(name, rows):
    width=len(rows[0])*384
    canvas=Image.new('RGB',(width,len(rows)*832),(30,31,36))
    draw=ImageDraw.Draw(canvas)
    for row, cells in enumerate(rows):
        for col,(label,detail,path) in enumerate(cells):
            source=Image.open(ROOT/path).convert('RGBA')
            assert source.size==(384,768)
            x,y=col*384,row*832
            draw.text((x+16,y+8),label,font=FONT,fill=(241,242,245))
            draw.text((x+16,y+38),detail,font=SMALL,fill=(192,196,208))
            canvas.paste(source,(x,y+64),source)
    destination=ROOT/name
    if destination.exists():
        raise FileExistsError(destination)
    canvas.save(destination)
    print(destination)

sheet('skin_lowlight_comparison.png',[[
    ('기존: 피부 1색','같은 광량 0.12676배 / 실제 렌더','pair_sweep_17/018/before/final.png'),
    ('수정: 피부 3색','수광량 비례 판정 / 보간 없음','pair_sweep_17/018/after/final.png')]])
sheet('skin_walk_comparison.png',[
    [(f'기존: 자세 {i}',f'피부 {k}색 / 같은 조명',f'pair_walk_17/{i:03}/before/final.png')
     for i,k in [(17,3),(18,4),(19,3)]],
    [(f'수정: 자세 {i}','피부 4색 / 같은 조명',f'pair_walk_17/{i:03}/after/final.png')
     for i in (17,18,19)]])
