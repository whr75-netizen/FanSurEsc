"""Display source and actual native gameplay pixels by copying, never resizing."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/artifacts/building39/gold-density19'
TARGET=OUT/'source-scene-comparison'


def main():
    receipt=json.loads((TARGET/'counter-rectangle.json').read_text(encoding='utf-8'))
    frame=Image.open(TARGET/receipt['framePath']).convert('RGBA')
    if frame.size!=(receipt['frameWidth'],receipt['frameHeight']) or abs(receipt['pixelSpacing']-1)>.001:
        raise ValueError('Actual frame and native pixel measurement must match')
    x,y,w,h=(receipt[k] for k in ['x','y','width','height'])
    pad=8
    rect=(x-pad,y-pad,x+w+pad,y+h+pad)
    crop=frame.crop(rect)
    crop.save(TARGET/'game-counter-crop.png')
    source=Image.open(OUT/'fine/empty_counter/preview.png').convert('RGBA')
    night=Image.open(OUT/'cpu-fixture.png').convert('RGBA')
    if source.size!=(receipt['sourceWidth'],receipt['sourceHeight']) or night.size!=source.size:
        raise ValueError('Source native dimensions changed')
    pictures=[source,night,crop]
    cell=max(p.width for p in pictures)+16
    height=max(p.height for p in pictures)+42
    panel=Image.new('RGBA',(cell*3,height),(28,30,39,255))
    draw=ImageDraw.Draw(panel)
    for i,(label,picture) in enumerate(zip(['SOURCE - reference light','SOURCE - fixed night light','ACTUAL GAME - native crop'],pictures)):
        ox=i*cell+(cell-picture.width)//2
        oy=30+(height-38-picture.height)//2
        panel.alpha_composite(picture,(ox,oy))
        draw.text((i*cell+8,8),label,fill=(235,235,235,255))
    panel.save(TARGET/'source-night-game-native.png')
    manifest={'source':'fine/empty_counter/preview.png','source_size':list(source.size),
        'night_source':'cpu-fixture.png','night_source_condition':'fixed irradiance .03/.045/.085, not exact spatial game lighting',
        'game_frame':receipt['framePath'],'game_crop_rectangle':rect,'native_source_pixels_on_screen':receipt['pixelSpacing'],
        'composition':'crop plus integer paste only','resampling_count':0,'resize_count':0,
        'comparison':'appearance observation; dynamic lights, props and floor make RGB equality inappropriate'}
    (TARGET/'comparison-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'panel':str(TARGET/'source-night-game-native.png'),'frame':frame.size,'source':source.size,'crop':crop.size,'resampling':0}))


if __name__=='__main__':main()
