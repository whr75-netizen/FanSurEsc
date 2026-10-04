"""N31 comparison: crop real captures, without resizing or filtering."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs/artifacts/building39/light31/run01'
if __name__=='__main__':
    receipt=json.loads((OUTPUT/'after/observation.json').read_text(encoding='utf-8'))
    x,y,w,h=receipt['bookRect']
    crops=[Image.open(OUTPUT/p).convert('RGB').crop((x,y,x+w,y+h)) for p in
        ('before/night-book-on.png','after/night-book-on.png')]
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    image=Image.new('RGB',(w*2+16,h+42),(24,27,33));draw=ImageDraw.Draw(image)
    for i,(crop,label) in enumerate(zip(crops,('수정 전 · 실제 게임 2px','수정 후 · 실제 게임 2px'))):
        image.paste(crop,(i*(w+16),42));draw.text((i*(w+16)+8,8),label,font=font,fill=(240,240,240))
    image.save(OUTPUT/'comparison.png')
    # A separate unchanged-pixel detail makes the contact shadow inspectable.
    before=Image.open(OUTPUT/'before/night-book-on.png').convert('RGB')
    after=Image.open(OUTPUT/'after/night-book-on.png').convert('RGB')
    off=Image.open(OUTPUT/'after/night-book-off.png').convert('RGB')
    import numpy as np
    changed=np.any(np.asarray(after)!=np.asarray(off),axis=2)
    yy,xx=np.where(changed)
    box=(max(0,int(xx.min())-20),max(0,int(yy.min())-30),min(after.width,int(xx.max())+21),min(after.height,int(yy.max())+25))
    c=[im.crop(box) for im in (before,after,off)];dw,dh=c[0].size
    detail=Image.new('RGB',(dw*3+32,dh+42),(24,27,33));draw=ImageDraw.Draw(detail)
    for i,(crop,label) in enumerate(zip(c,('수정 전','수정 후','책 차광 OFF'))):
        detail.paste(crop,(i*(dw+16),42));draw.text((i*(dw+16)+6,8),label,font=font,fill=(240,240,240))
    detail.save(OUTPUT/'book-contact-comparison.png')
    print(json.dumps({'comparison':str(OUTPUT/'comparison.png'),'detail':str(OUTPUT/'book-contact-comparison.png'),
        'cropOnly':True,'resize':False,'bookBeforeMax':3,'bookAfterMax':receipt['bookMaxByte']}))
