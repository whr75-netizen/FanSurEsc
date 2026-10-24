"""Present the saved full canvases; never crop or replace the original evidence."""
from pathlib import Path
import json,sys,math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).parent
CAP=ROOT/'CanvasFull260'
OUT=ROOT/'Deliverable576'
status=json.loads((CAP/'status.json').read_text())
partial='--partial' in sys.argv
assert(status['status']=='CAPTURED'and status['poses']==81)or(partial and status['status']=='FAILED'and status['poses']>0),status
count=status['poses'];suffix=f'PARTIAL{count}'if partial else'ALL81'
OUT.mkdir(exist_ok=True)
captures=[json.loads((CAP/f'{f:03}_{k}_CAPTURE.json').read_text())for f in range(count)for k in ['OFF','ON']]
assert all(not c['sourceCropApplied']and(c['originalWidth'],c['originalHeight'])==(960,544)for c in captures)
# One common integer crop around the union of every character cell in both runs.
# Two logical cells of margin retain the one-cell outline band and its context.
b=[c['charBounds']for c in captures]
box=(max(0,2*(min(z[0]for z in b)-2)),max(0,2*(min(z[1]for z in b)-2)),min(960,2*(max(z[2]for z in b)+2)),min(544,2*(max(z[3]for z in b)+2)))
assert all(box[0]<=2*z[0]and box[1]<=2*z[1]and box[2]>=2*z[2]and box[3]>=2*z[3]for z in b)
w,h=box[2]-box[0],box[3]-box[1]
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',11)
frames=[]
for f in range(count):
    canvas=Image.new('RGB',(2*w,h+46),'#eaf0f2');d=ImageDraw.Draw(canvas)
    for i,(k,label)in enumerate([('OFF','566 signed baseline'),('ON','576 shared KEEP')]):
        im=Image.open(CAP/f'{f:03}_{k}.png').convert('RGB')
        assert im.size==(960,544)
        canvas.paste(im.crop(box),(i*w,24));d.text((i*w+4,3),label,fill='#132a39',font=font)
    d.text((4,h+27),f'{"PARTIAL "if partial else""}Walk {f:02}/80 | yaw260 | same pose / light',fill='#132a39',font=small)
    frames.append(canvas)
durations=([20,10,20]*math.ceil(count/3))[:count]
web_durations=([17,16,17]*math.ceil(count/3))[:count]
frames[0].save(OUT/f'WALK576_{suffix}.webp',save_all=True,append_images=frames[1:],duration=web_durations,loop=0,lossless=True,quality=100,method=4)
atlas=Image.new('RGB',(2*w*9,(h+46)*math.ceil(count/9)))
for i,im in enumerate(frames):atlas.paste(im,((i%9)*2*w,(i//9)*(h+46)))
palette=atlas.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
gif=[im.quantize(palette=palette,dither=Image.Dither.NONE)for im in frames]
gif[0].save(OUT/f'WALK576_{suffix}.gif',save_all=True,append_images=gif[1:],duration=durations,loop=0,optimize=False,disposal=2)
manifest={'comparison':'actual yaw260 runtime signed selection566 vs shared KEEP576; both same prepared curve input, Clothes547 on, Body0 region off; not product default OFF/ON','originalCanvas':[960,544],'originalFrameCount':2*count,'additionalFailedFrameOFF':partial,'originalsRetained':True,'derivedCommonCropLTRB':box,'allCharacterCellsIncluded':True,'rescale':False,'logicalGrid':[480,272],'frames':count,'sourceStepSeconds':1/60,'endpointRetained':not partial,'durationMs':sum(durations),'partialNotFullLoop':partial,'failure':status.get('error',''),'files':{}}
for name in [f'WALK576_{suffix}.gif',f'WALK576_{suffix}.webp']:
    im=Image.open(OUT/name);assert im.n_frames==count,(name,im.n_frames)
    total=0;maxerr=0
    for i in range(count):
        im.seek(i);im.load();total+=im.info.get('duration',0)
        if name.endswith('webp'):
            assert im.convert('RGB').tobytes()==frames[i].tobytes(),('lossless decode differs',i)
    assert total==sum(durations),(name,total)
    manifest['files'][name]={'bytes':(OUT/name).stat().st_size,'frames':im.n_frames,'durationMs':total,'losslessRGB':name.endswith('webp')}
for k in ['OFF','ON']:
    sheet=Image.new('RGB',(220*9,198*math.ceil(count/9)),'#eaf0f2');d=ImageDraw.Draw(sheet)
    for f in range(count):
        im=Image.open(CAP/f'{f:03}_{k}.png').convert('RGB').crop((390,50,500,140)).resize((220,180),Image.Resampling.NEAREST)
        x,y=(f%9)*220,(f//9)*198;sheet.paste(im,(x,y+18));d.text((x+4,y+1),f'{f:02} {k}',fill='#132a39',font=small)
    sheet.save(OUT/f'HEADS_{suffix}_{k}.png')
for f in sorted(set(z for z in [0,16,35,40,41,51,62,69,70,71,72,73,77,80]if z<count)):frames[f].save(OUT/f'FULLBODY_{f:03}_576.png')
(OUT/'VISUAL_MANIFEST576.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest))
