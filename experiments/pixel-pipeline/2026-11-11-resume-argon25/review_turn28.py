"""Show the two actual27 occlusion cells, never fabricate an uncovered eye."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parent;G=H/'face28';P=H/'producer/support/surface27'
sys.path.insert(0,str(R/'bounded-form115/runtime24/full-render24'))
from report_full24 import read,plane,full,rgba
def main():
 state=read(next((P/'pigment-motion').glob('STATE113-*-finished.json')));index={v['frame']:Path(v['output'])for v in state['sequencePackets']}
 reasons=read(P/'ROTATION_REJECTIONS26.json');negative=read(P/'GPU_MOTION26.json')['negativeRows'];rows=[]
 sizes=[read(index[n['frame']+delta]/'RAW_MANIFEST.json')['grid102']['eyeTopLeftROI'][2:]for n in negative for delta in [-1,0,1]]
 cw=max(320,max(w*16+16 for w,h in sizes));rh=max(h*16+82 for w,h in sizes)
 board=Image.new('RGB',(3*cw,2*rh),'#202020');draw=ImageDraw.Draw(board)
 for row,neg in enumerate(negative):
  frame=neg['frame']
  for col,f in enumerate([frame-1,frame,frame+1]):
   p=index[f];m=read(p/'RAW_MANIFEST.json');assert hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()==(p/'RAW_COMPLETE76.marker').read_text().strip()
   a,sid=full(p,'candidate113');assert sid==m['sourceId'];rx,ry,w,h=m['grid102']['eyeTopLeftROI'];ox,oy=m['grid102']['headToMainOffset'];xx=rx+round(ox);yy=272-ry-h+round(oy)
   im=Image.fromarray(rgba(a[::-1]));crop=im.crop((xx,272-yy-h,xx+w,272-yy)).convert('RGB');large=crop.resize((w*16,h*16),Image.Resampling.NEAREST)
   board.paste(crop,(col*cw+8,row*rh+28));board.paste(large,(col*cw+8,row*rh+58));draw.text((col*cw+8,row*rh+6),f'ACTUAL27 turn frame {f}',fill='white')
   if f==frame:
    x,y=neg['physicalROI'];top=h-1-y;draw.rectangle((col*cw+8+x*16,row*rh+58+top*16,col*cw+8+(x+1)*16-1,row*rh+58+(top+1)*16-1),outline='#ff6060',width=2)
    _,owner=plane(p/'F-FinalOwner.plane');proof=next(v for v in reasons['rows']if v['frame']==frame)
    rows.append({'sourceId':sid,'frame':frame,'physicalROI_bottomLeft':[x,y],'canonical':[4,5],'finalOwner':owner[y,x].tolist(),'sameFrameFaceVisibleSampleCount16':proof['faceVisible16'],'meaning':'Definite rejection under the current source-blink dominance AND skin ownership policy; not a support crop/alpha unknown or a proof of artistic correctness. No alternate image manufactured.'})
 board.save(G/'ROTATION_OCCLUSION28.png')
 result={'newPlayOrGPU':False,'source':'Actual final27 same-frame packets; distinct frame/source IDs retained','rows':rows,'policyChoice':'Relaxing blink/affiliation conjunction would change the approved Argon2.5 occlusion policy. No policy altered here; no original RGB/support fabricated.'}
 (G/'ROTATION_VIEW28.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'actualFramesShown':6,'cells':len(rows)}))
if __name__=='__main__':main()
