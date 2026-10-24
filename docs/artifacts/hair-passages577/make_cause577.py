from pathlib import Path
import csv,struct,json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).parent;O=R/'Deliverable577';O.mkdir(exist_ok=True)
grid=list(csv.DictReader((R/'Trace577B/GRID577.tsv').open(),delimiter='\t'))
old={(int(z['x']),int(z['y'])):z['protectedPositive']=='True'for z in grid}
raw=(R/'Probe577/260_042_MASK.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',raw)
new={(x+i%w,y+i//w):bool(raw[16+w*h+i])for i in range(w*h)}
spans=list(csv.DictReader((R/'Trace577B/FEATURE_7_SPANS577.tsv').open(),delimiter='\t'))
S=60;W,H=400,520;canvas=Image.new('RGB',(3*W,H),'#edf3f5');d=ImageDraw.Draw(canvas)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
blue='#253850';empty='#fff5d9';x0,y0=217,46
for panel,label in enumerate(['Continuous source negative region','566: 8-neighbour selected groups','577: same-source 4-way passage']):
    tile=Image.new('RGB',(S*6,S*6),blue);q=ImageDraw.Draw(tile)
    if panel==0:
        for s in spans:
            lo,hi,l0,l1,r0,r1=[float(s[k])for k in ['lo','hi','l0','l1','r0','r1']]
            q.polygon([((l0-x0)*S,(lo-y0)*S),((r0-x0)*S,(lo-y0)*S),((r1-x0)*S,(hi-y0)*S),((l1-x0)*S,(hi-y0)*S)],fill=empty)
    else:
        mask=old if panel==1 else new
        for yy in range(6):
            for xx in range(6):q.rectangle((xx*S,yy*S,(xx+1)*S-1,(yy+1)*S-1),fill=blue if mask[(x0+xx,y0+yy)]else empty)
    for i in range(7):q.line((i*S,0,i*S,6*S),fill='#6c7d86');q.line((0,i*S,6*S,i*S),fill='#6c7d86')
    for point,col in [((220,49),'#f5a623'),((219,50),'#26be87')]:
        xx,yy=(point[0]-x0)*S,(point[1]-y0)*S;q.rectangle((xx+2,yy+2,xx+S-3,yy+S-3),outline=col,width=4)
    canvas.paste(tile,(panel*W+20,48));d.text((panel*W+16,12),label,fill='#102e40',font=font)
    d.text((panel*W+18,420),['Orange cell: disconnected L/T and B/R','Four empty cells are already sealed','Green cell opens the actual source route'][panel],fill='#102e40',font=small)
d.text((20,451),'Frame42 stored-input diagram, NOT a rendered frame. Logical cells x217..222 / y46..51.',fill='#102e40',font=font)
d.text((20,478),'Guard: 0.66677758 - 0.37770432 = 0.28907326 px^2. Delta E: orange +0.30820 invalid / green +0.75658 admissible.',fill='#102e40',font=small)
canvas.save(O/'CAUSE577.png')
print(json.dumps({'file':str(O/'CAUSE577.png'),'bytes':(O/'CAUSE577.png').stat().st_size,'type':'stored continuous geometry and grid diagram; not runtime output'}))
