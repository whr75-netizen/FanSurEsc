"""Uniform real-sequence contact sheet, no rendered/expected RGB replacement."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face92/motion240'
def main():
 c=G/'capture';r=json.loads((c/'COMPLETE.json').read_text());frames=r['stream77']['frames'];indices=np.unique(np.linspace(0,len(frames)-1,24).astype(int));board=Image.new('RGB',(720,4*180+40),(27,29,35));draw=ImageDraw.Draw(board)
 for j,i in enumerate(indices):
  f=frames[i];w,h=f['QROI'][2:];raw=decode((c/f['compressedFile']).read_bytes(),f['bytes']);a=np.frombuffer(raw,'<f4').reshape(h,22,w,4).transpose(1,0,2,3);x=(j%6)*120;y=(j//6)*180;draw.text((x+2,y+2),f"F{f['frame']} actual",fill='white');draw.text((x+2,y+18),'Native / candidate',fill='white');draw.text((x+2,y+34),f"face:{int(np.sum(a[20,:,:,3]==1))}",fill='white')
  for q,layer in enumerate([0,19]):board.paste(srgb(a[layer]).resize((w*2,h*2),Image.Resampling.NEAREST),(x+2+q*56,y+54))
 draw.text((4,725),'Uniform24 samples of240 actual frames,4s. Same current alpha/world visibility. General line width/art remain incomplete.',fill='white');board.save(G/'ACTUAL_SEQUENCE92.png');print(json.dumps({'actualFrames':len(frames),'uniformFramesVisuallyInspectable':len(indices),'CPUExpectedRGBUsed':False}))
if __name__=='__main__':main()
