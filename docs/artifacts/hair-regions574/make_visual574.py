from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).parent
CAP=ROOT/'Full574'
OUT=ROOT/'Deliverable574'
OUT.mkdir(exist_ok=True)
status=json.loads((CAP/'status.json').read_text())
assert status['status']=='CAPTURED' and status['poses']==81, status
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
frames=[]
for f in range(81):
    canvas=Image.new('RGB',(460,504),'#eaf0f2');d=ImageDraw.Draw(canvas)
    for i,(kind,label) in enumerate([('OFF','566 baseline'),('ON','574 small gaps -> hair')]):
        im=Image.open(CAP/f'{f:03}_{kind}.png').convert('RGB')
        assert im.size==(230,470)
        canvas.paste(im,(230*i,24))
        d.text((230*i+6,3),label,fill='#132a39',font=font)
    d.text((6,491),f'Actual Walk {f:02}/80 | same pose/light | 480 x 272 logical grid',fill='#132a39',font=small)
    frames.append(canvas)
durations=[20,10,20]*27
web_durations=[17,16,17]*27
frames[0].save(OUT/'WALK574_ALL81.webp',save_all=True,append_images=frames[1:],duration=web_durations,loop=0,lossless=True,quality=100,method=4)
# One palette for the whole sequence, no rescaling/interpolation or frame deletion.
atlas=Image.new('RGB',(460*9,504*9))
for i,im in enumerate(frames):atlas.paste(im,((i%9)*460,(i//9)*504))
palette=atlas.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
gif=[im.quantize(palette=palette,dither=Image.Dither.NONE)for im in frames]
gif[0].save(OUT/'WALK574_ALL81.gif',save_all=True,append_images=gif[1:],duration=durations,loop=0,optimize=False,disposal=2)
for name in ['WALK574_ALL81.gif','WALK574_ALL81.webp']:
    im=Image.open(OUT/name);assert im.n_frames==81,(name,im.n_frames)
    times=[]
    for i in range(im.n_frames):im.seek(i);im.load();times.append(im.info.get('duration',0))
    print(name,(OUT/name).stat().st_size,'frames',im.n_frames,'duration_ms',sum(times))
for k in ['OFF','ON']:
    sheet=Image.new('RGB',(220*9,198*9),'#eaf0f2');d=ImageDraw.Draw(sheet)
    for f in range(81):
        im=Image.open(CAP/f'{f:03}_{k}.png').convert('RGB').crop((40,25,150,115)).resize((220,180),Image.Resampling.NEAREST)
        x,y=(f%9)*220,(f//9)*198;sheet.paste(im,(x,y+18));d.text((x+4,y+1),f'{f:02} {"566" if k=="OFF" else "574"}',fill='#132a39',font=small)
    sheet.save(OUT/f'HEADS_ALL81_{k}.png')
for f in [16,51,62,71,72,73,76,77]:frames[f].save(OUT/f'FULLBODY_{f:03}_574.png')
frames[72].save(OUT/'FULLBODY574.png')
(OUT/'VISUAL_MANIFEST574.json').write_text(json.dumps({'comparison':'actual runtime 566 versus 574; Clothes547 on, Body0 scope off; not current-product-off','sourceCrop':[350,25,230,470],'logicalGrid':[480,272],'frames':81,'sourceStepSeconds':1/60,'endpointRetained':True,'presentationDurationMs':1350,'gif':'one 256-colour palette, no dither; all frames; no rescale','webp':'lossless RGB, all frames; no rescale','files':{p.name:p.stat().st_size for p in OUT.iterdir()if p.is_file()}},indent=2)+'\n')
