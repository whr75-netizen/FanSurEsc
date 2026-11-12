"""Actual GPU images and separately labelled CPU visibility evidence."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet
from review_motion64 import srgb
H=Path(__file__).resolve().parent

def main():
 root=H/'face96/geometry64';report=json.loads((root/'capture/COMPLETE.json').read_text());assert report['packetComplete']and report['ownedResourcesReleased']and report['restorationChecksPass'];audit=json.loads((root/'VISIBLE_RIBBON96.json').read_text());by={(r['frame'],tuple(r['xy'])):r for r in audit['rows']};chosen=[f for f in report['stream77']['frames']if'actorSource96'in f];sheet=Image.new('RGB',(1120,100+len(chosen)*260+170),'#20252c');draw=ImageDraw.Draw(sheet);draw.text((16,12),'96: ACTUAL GPU baseline / LUT92 / existing opaque ribbon93. NO new colour or line fix adopted.',fill='white');draw.text((16,33),'CPU source visibility is a separate diagnostic; magenta = uncertain, green = some visible source area.',fill='white')
 for row,f in enumerate(chosen):
  a,world,depth=packet(root,f);y=80+row*260;draw.text((16,y),f"frame {f['frame']} / ordinal {f['ordinal']}",fill='white')
  for col,(plane,label)in enumerate([(11,'Actual baseline'),(5,'Actual LUT92'),(9,'Actual ribbon93 final')]):
   im=srgb(a[plane,:,:,:3]);x=16+col*225;sheet.paste(im,(x,y+24));sheet.paste(im.resize((182,182),Image.Resampling.NEAREST),(x,y+56));draw.text((x+34,y+29),label,fill='white')
  diagnostic=srgb(a[9,:,:,:3]).resize((182,182),Image.Resampling.NEAREST);d=ImageDraw.Draw(diagnostic)
  for (frame,xy),r in by.items():
   if frame!=f['frame']:continue
   x0,y0=xy;colour='#62ff78'if r['confirmedSomeVisibleInCPUModel']else'#ff55d8';d.rectangle((x0*7,(25-y0)*7,x0*7+6,(25-y0)*7+6),outline=colour,width=1)
  sheet.paste(diagnostic,(706,y+56));draw.text((706,y+29),'CPU support state overlay',fill='white');draw.text((914,y+58),'Opaque cells are not',fill='white');draw.text((914,y+77),'source visible area.',fill='white')
  if f['frame']in[148,149]:
   draw.text((914,y+105),'Colour step at (6,7)',fill='#ffd989');draw.text((914,y+124),'Point family changes;',fill='white');draw.text((914,y+143),'area leader stays 215.',fill='white')
 y=100+len(chosen)*260;draw.text((16,y),'Frame102 (22,13): chosen ribbon witness lies behind actual opaque hair by 39.95mm.',fill='#ffd989');draw.text((16,y+22),'All source pieces were checked: 18 / 21 cells have positive visible area; 3 remain uncertain.',fill='white');draw.text((16,y+44),'Some positive fragments are far smaller than one pixel. Full opacity from any intersection is still unresolved.',fill='white');draw.text((16,y+66),'At colour cell (6,7), existing detected foreground occupies ~0.024 cell; no new semantic paint label is inferred.',fill='white');draw.text((16,y+88),'64 real consecutive frames = 1.0667 simulation seconds; not long-term stability or art acceptance.',fill='white');sheet.save(root/'ACTUAL_SOURCE_VISIBILITY96.png')
 sequence=[]
 for f in report['stream77']['frames']:
  a,_,_=packet(root,f);p=Image.new('RGB',(610,240),'#20252c');d=ImageDraw.Draw(p);d.text((8,7),f"ACTUAL GPU96 frame {f['frame']} / ordinal {f['ordinal']} - existing92/93 path",fill='white')
  for i,(plane,label)in enumerate([(11,'Baseline'),(5,'LUT92'),(9,'Ribbon93')]):
   im=srgb(a[plane,:,:,:3]);p.paste(im,(8+i*200,31));p.paste(im.resize((182,182),Image.Resampling.NEAREST),(8+i*200,55));d.text((42+i*200,35),label,fill='white')
  sequence.append(p)
 sequence[0].save(root/'ACTUAL_SEQUENCE96.webp',save_all=True,append_images=sequence[1:],duration=80,loop=0,lossless=True)
 print(json.dumps({'actualGPUFrames':len(sequence),'newFixAdopted':False,'diagram':str(root/'ACTUAL_SOURCE_VISIBILITY96.png'),'sequence':str(root/'ACTUAL_SEQUENCE96.webp')}))
if __name__=='__main__':main()
