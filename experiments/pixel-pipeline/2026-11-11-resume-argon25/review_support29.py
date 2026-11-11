"""Reproduce the native-source region counterexample; no Unity or GPU."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from affine_support29 import H,G,trace_native
def main():
 z=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=z['rgba'][...,:3];mask=z['mask']&(z['rgba'][...,3]==255)
 rows=[trace_native(rgb,mask,(382,704),r)for r in [2,4]]
 (G/'AFFINE_NATIVE_COMPONENT29.json').write_text(json.dumps(rows,indent=2),encoding='utf-8',newline='\n')
 points=np.asarray([p for row in rows for p in row['supportXY']+row['unknownBoundaryXY']]);x0,y0=points.min(0)-5;x1,y1=points.max(0)+6
 source=rgb[y0:y1,x0:x1];scale=7;w,h=source.shape[1]*scale,source.shape[0]*scale;board=Image.new('RGB',(3*w,h+48),'#202020');draw=ImageDraw.Draw(board);views=[(source,'NATIVE SOURCE ONLY')]
 for row in rows:
  view=source.copy()
  for x,y in row['unknownBoundaryXY']:view[y-y0,x-x0]=[240,80,200]
  for x,y in row['supportXY']:view[y-y0,x-x0]=[20,210,210]
  views.append((view,'r'+str(row['radius'])+' HYPOTHESIS / NOT ADOPTED'))
 for i,(v,title)in enumerate(views):board.paste(Image.fromarray(v).resize((w,h),Image.Resampling.NEAREST),(i*w,44));draw.text((i*w+3,5),title,fill='white')
 draw.text((3,23),'Cyan: conditional residual core. Magenta: background model unknown. No final render or fill.',fill='white');board.save(G/'SOURCE_SUPPORT29.png')
 print(json.dumps([{k:v for k,v in r.items()if k not in ['supportXY','unknownBoundaryXY']}for r in rows]))
if __name__=='__main__':main()
