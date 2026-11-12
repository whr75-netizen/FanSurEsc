"""Separate generic exterior silhouette from native per-material hull decoration.

Current Native395's cell.z==1 identifies this view's current actor occupancy,
not a global character ID. Pigment/eyelid feature paths are not inputs here.
"""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
import review_hull60 as api
from face_parent62 import resolve
from native_contour42 import coordinates
H=Path(__file__).resolve().parent;G=H/'face66';C=H/'face65/capture'

def exterior_candidate(before,resolved,gate,native_cell):
 same_actor=native_cell[:,:,2]==1
 reject=(gate[:,:,3]==1)&same_actor
 out=resolved.copy();out[reject]=before[reject]
 return out,reject

def main():
 G.mkdir(exist_ok=True);api.C=C;r=json.loads((C/'COMPLETE.json').read_text());rows=[];board=Image.new('RGB',(960,6*220),(25,27,32));draw=ImageDraw.Draw(board)
 for fi,f in enumerate(r['frames']):
  read=lambda n:api.plane(r,f,n);w=f['QROI'][2];a=read('atlas40');fields=[a[:,i*w:(i+1)*w]for i in range(16)];b=read('ownerReceipts47');domain=b[:,3*w:4*w].copy();domain[:,:,0]=domain[:,:,0]==-4;visible=read('featureProducer49')[:,w:2*w]
  info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);cases=[]
  for ci,scale in enumerate([1,8,32]):
   field=[18,22,24][ci];line=read('nativeLogicalHull60'if field==18 else'widthCaseField'+str(field));proof=read('nativeLogicalHullProof60'if field==18 else'widthCaseField'+str(field+1))
   old,gate,_=resolve(line,proof,fields[9],fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink,4232,visible,domain,b[:,:w]);out,reject=exterior_candidate(fields[9],old,gate,fields[14]);use=(gate[:,:,3]==1)&~reject
   assert np.array_equal(out[fields[14][:,:,2]==1],fields[9][fields[14][:,:,2]==1])
   cases.append({'widthScale':scale,'oldSelected':int((gate[:,:,3]==1).sum()),'sameActorRejected':int(reject.sum()),'exteriorRemaining':int(use.sum()),'rejectedOwnerRoles':np.unique(b[:,:w][reject,0],return_counts=True)[0].tolist()})
   x=np.clip(out[::-1,:,:3],0,1);x=np.where(x<=.0031308,12.92*x,1.055*x**(1/2.4)-.055);im=Image.fromarray(np.uint8(np.rint(x*255)));draw.text((ci*320+6,fi*220+6),f"CPU candidate F{f['frame']} x{scale}: {int(use.sum())} exterior",fill='white');board.paste(im,(ci*320+6,fi*220+30));board.paste(im.resize((w*6,f['QROI'][3]*6),Image.Resampling.NEAREST),(ci*320+80,fi*220+30))
  rows.append({'sourceId':f['sourceId'],'frame':f['frame'],'cases':cases})
 result={'CPUReplayOnly':True,'GPUExecuted66':False,'product77DefaultChanged':False,'meaning':'Generic exterior silhouette cannot overwrite current same-actor occupancy. This does not classify native painted pigment or internal part boundaries.','originalWidthOldSelected':sum(x['cases'][0]['oldSelected']for x in rows),'originalWidthExteriorRemaining':sum(x['cases'][0]['exteriorRemaining']for x in rows),'notSolved':['No complete character outer band or source-origin visibility mapping yet','Large calibration width remains unadopted','No runtime history/colour-region/LUT implementation in this replay'],'rows':rows}
 (G/'CPU_CLASSIFICATION66.json').write_text(json.dumps(result,indent=2));board.save(G/'CPU_EXTERIOR_CLASS66.png');print(json.dumps(result))
if __name__=='__main__':main()
