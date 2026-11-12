"""Count actual source support; empty ROI frames are not face stability evidence."""
from pathlib import Path
import json,hashlib,sys,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from review_motion64 import srgb
H=Path(__file__).resolve().parent;K=sys.argv[1]if len(sys.argv)>1 else'long';assert K in['long','loop120'];G=H/'face77'/K;C=G/'capture'

def main():
 report=json.loads((C/'COMPLETE.json').read_text());frames=report['stream77']['frames'];rows=[];film=[];panels=[]
 role=json.loads((H/'face69/ZERO_POLICY69.json').read_text())['role']
 for f in frames:
  w,h=f['QROI'][2:];raw=decode((C/f['compressedFile']).read_bytes(),f['bytes']);assert hashlib.sha256(raw).hexdigest()==f['rawSHA256']
  data=np.frombuffer(raw,'<f4').reshape(h,w*13,4);parts=[data[:,i*w:(i+1)*w]for i in range(13)];before,after,key,meta,world,cell,owner,uv,source,trace,receipt,domain=parts[:12]
  actor=cell[:,:,2]==1;face=actor&(owner[:,:,0]==role);outline=key[:,:,0]>=100;hist=trace[:,:,3]==1
  row={'ordinal':f['ordinal'],'frame':f['frame'],'actorCells':int(actor.sum()),'faceSourceCells':int(face.sum()),'outlineCells':int(outline.sum()),'historyMatchedCells':int(hist.sum()),'actualInputMatches':f['motion']['matches'],'stage':f['motion']['stage']};rows.append(row)
  if'observedActorCells77'in f:assert f['observedActorCells77']==row['actorCells']and f['observedFaceCells77']==row['faceSourceCells']
  # No native support means no evidence about face/line temporal quality.
  if actor.any():
   a=srgb(before);b=srgb(after);out=Image.new('RGB',(w*12,h*6+24),(27,29,35));out.paste(a.resize((w*6,h*6),Image.Resampling.NEAREST),(0,24));out.paste(b.resize((w*6,h*6),Image.Resampling.NEAREST),(w*6,24));ImageDraw.Draw(out).text((3,3),f"F{f['frame']} native | private candidate; partial LUT rejected",fill='white');film.append(out)
   if face.any():panels.append((f,a,b))
 selected=[panels[i]for i in np.unique(np.linspace(0,len(panels)-1,min(6,len(panels))).astype(int))]if panels else[]
 board=Image.new('RGB',(680,len(selected)*200+32),(27,29,35));draw=ImageDraw.Draw(board)
 for i,(f,a,b)in enumerate(selected):
  for j,(im,title)in enumerate([(a,'Native'),(b,'Private candidate; partial LUT rejected')]):
   draw.text((j*340+4,i*200+4),f"F{f['frame']} {title}",fill='white');board.paste(im,(j*340+4,i*200+24));board.paste(im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST),(j*340+48,i*200+24))
 draw.text((4,len(selected)*200+8),'Only frames with observed face support. No claim of long-term face stability.',fill='white');board.save(G/'VISIBLE_CHARACTER77.png')
 if film:film[0].save(G/'VISIBLE_CHARACTER77.webp',save_all=True,append_images=film[1:],duration=100,loop=0,lossless=True)
 first=(C/frames[0]['compressedFile']).stat().st_mtime;last=(C/frames[-1]['compressedFile']).stat().st_mtime
 result={'actualConsecutiveFrames':len(frames),'actorObservedFrames':sum(r['actorCells']>0 for r in rows),'faceObservedFrames':sum(r['faceSourceCells']>0 for r in rows),'emptyActorFrames':[r['frame']for r in rows if not r['actorCells']],'firstToLastFileSeconds':last-first,'simulationSeconds':sum(f['deltaTime']for f in frames),'allInputMatches':all(r['actualInputMatches']for r in rows),'full120FaceStabilityProven':False,'GPUTimeMeasured':False,'wholeFaceArtAdopted':False,'beforeMemory':report['beforeMemory'],'afterMemory':report['afterMemory'],'rows':rows}
 (G/'VISIBILITY_AUDIT77.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k not in['rows','emptyActorFrames']}))
if __name__=='__main__':main()
