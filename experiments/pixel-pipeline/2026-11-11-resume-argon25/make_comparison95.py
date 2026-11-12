"""Render exact actual pixels and a data-derived partial-coverage diagram."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont
from review_footprint95 import frame
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face95/colour64';B=H/'face95/motion64'
def main():
 fonts=Path(r'C:\Windows\Fonts');font=ImageFont.truetype(str(fonts/'arial.ttf'),16);small=ImageFont.truetype(str(fonts/'arial.ttf'),13);frames=json.loads((G/'capture/COMPLETE.json').read_text())['stream77']['frames'];old=json.loads((B/'capture/COMPLETE.json').read_text())['stream77']['frames'];image=Image.new('RGB',(820,760),'#191d24');d=ImageDraw.Draw(image);d.text((16,12),'ACTUAL GPU: source mapping comparison - candidate NOT adopted',font=font,fill='white');cache={};video=[]
 for f,of in zip(frames,old):
  a,_=frame(G,f);b,_=frame(B,of);im=Image.new('RGB',(520,254),'#191d24');v=ImageDraw.Draw(im);v.text((12,8),'92 baseline / 95 rejected candidate   frame '+str(f['frame']),font=font,fill='white')
  for col,p in enumerate([b,a]):
   actual=srgb(p[18,:,:,:3]);im.paste(actual,(col*260+12,44));im.paste(actual.resize((208,208),Image.Resampling.NEAREST),(col*260+45,44))
  video.append(im)
  if f['frame']in[148,149]:cache[f['frame']]=b,a
 for row,index in enumerate([148,149]):
  y=48+row*238;d.text((16,y),'Frame '+str(index),font=font,fill='white')
  for col,p in enumerate(cache[index]):
   actual=srgb(p[18,:,:,:3]);x=col*400+20;image.paste(actual,(x,y+33));image.paste(actual.resize((208,208),Image.Resampling.NEAREST),(x+50,y+25));d.text((x+270,y+35),'92 baseline'if col==0 else'95 candidate',font=font,fill='white');d.text((x+270,y+64),'1x + nearest8x',font=small,fill='#b6c4d8');px,py=6,25-7;d.rectangle((x+50+8*px,y+25+8*py,x+50+8*(px+1)-1,y+25+8*(py+1)-1),outline='#ffca53',width=1)
 y=535;d.text((16,y),'Same Q. GPU step: (0,-4,-5) -> (0,-1,-3). 93 CPU step was (0,-1,-1).',font=font,fill='#ffca53');d.text((16,y+25),'Lower source MSE alone failed the original temporal counterexample.',font=small,fill='white');support=json.loads((B/'LINE_SUPPORT95.json').read_text());line=next(x for x in support['rows']if x['frame']==140 and x['localXY']==[23,18]);cell=Image.new('RGB',(128,128),'#dce4ee');cd=ImageDraw.Draw(cell);xy=np.array(line['localXY']);poly=np.array(line['sourceRibbonPolygon'])[[0,1,3,2]]-xy;pts=[(float(x*128),float((1-y)*128))for x,y in poly];cd.polygon(pts,fill='#397fcc');cd.rectangle((0,0,127,127),outline='#ffffff',width=1)
 for sample in line['headSamplesInFront']:
  q=np.array(sample['localPoint'])-xy;x,y=q*[128,-128]+[0,128];cd.ellipse((x-4,y-4,x+4,y+4),fill='#da2929')
 image.paste(cell,(20,598));d.text((168,604),'Actual frame140 / cell(23,18)',font=font,fill='white');d.text((168,633),'Blue: selected edge ribbon; red: front head sample.',font=small,fill='white');d.text((168,655),'Opaque cell1.0 vs ALL-edge area upper bound '+format(line['unoccludedSourceRibbonAreaUpperBoundCells'],'.5f'),font=small,fill='white');d.text((168,678),'Partial front support is NOT a whole-cell rejection rule.',font=small,fill='#ffca53');image.save(G/'EVIDENCE95.png');video[0].save(G/'ACTUAL_COMPARISON95.webp',save_all=True,append_images=video[1:],duration=[17 if i%3==0 else 16 for i in range(len(video))],loop=0,lossless=True,method=6);print(json.dumps({'PNG':str(G/'EVIDENCE95.png'),'actualVideoFrames':len(video),'nearestOnly':True,'candidateAdopted':False}))
if __name__=='__main__':main()
