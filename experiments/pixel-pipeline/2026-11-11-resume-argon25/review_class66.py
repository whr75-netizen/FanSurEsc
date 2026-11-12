from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
import review_hull60 as api
from face_parent62 import resolve,child_gate
from native_contour42 import coordinates
from replay_outline_class66 import exterior_candidate
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face66';C=G/'capture'
def main():
 api.C=C;r=json.loads((C/'COMPLETE.json').read_text());assert r['packetComplete']and r['actualConsecutive']and r['restorationChecksPass']and r['ownedResourcesReleased']and r['pendingOwners']==0 and not r['errors'] and len(r['frames'])==6
 board=Image.new('RGB',(1600,1390),(25,27,32));draw=ImageDraw.Draw(board);rows=[];film=[]
 for fi,f in enumerate(r['frames']):
  read=lambda n:api.plane(r,f,n);w=f['QROI'][2];h=f['QROI'][3];a=read('atlas40');fields=[a[:,i*w:(i+1)*w]for i in range(16)];b=read('ownerReceipts47');domain=b[:,3*w:4*w].copy();domain[:,:,0]=domain[:,:,0]==-4;v=read('featureProducer49')[:,w:2*w];info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);outputs=read('widthCompositeAtlas61');owners=read('widthOwnerAndLayerAtlas62');actor=fields[14][:,:,2]==1;cases=[];images=[]
  for ci,scale in enumerate([0,1,8,32,32]):
   field=[20,18,22,24,24][ci]
   line=read('nativeLogicalHull60'if field==18 else'widthCaseField'+str(field))if ci else np.zeros((h,w,4),np.float32);proof=read('nativeLogicalHullProof60'if field==18 else'widthCaseField'+str(field+1))if ci else np.zeros((h,w,4),np.float32)
   old,gate,blocked=resolve(line,proof,fields[9],fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink,4232,v,domain,b[:,:w]);expected,rejected=exterior_candidate(fields[9],old,gate,fields[14])if ci<4 else(old,np.zeros((h,w),bool));use=(gate[:,:,3]==1)&~rejected
   actual=outputs[:,ci*2*w:(ci+1)*2*w];owner=owners[:,ci*2*w:(ci*2+1)*w];layer=owners[:,(ci*2+1)*w:(ci+1)*2*w]
   assert np.array_equal(actual,np.repeat(np.repeat(expected,2,0),2,1))and np.array_equal(owner[:,:,0]==6,use)
   assert np.array_equal(owner[use,1],proof[use,3])and np.array_equal(owner[use,2:],proof[use,1:3])and np.array_equal(layer[:,:,:3],v[:,:,:3])and np.array_equal(layer[:,:,3]==1,blocked)
   assert np.array_equal(expected[~use],fields[9][~use])and np.all(expected[use,:3]==ink)
   if ci<4:assert np.array_equal(expected[actor],fields[9][actor])
   if ci==1:assert np.array_equal(actual,read('nativeAfter42'))
   name='exterior'if ci<4 else'native hull reference';cases.append({'class':name,'widthScale':scale,'oldHullSelected':int((gate[:,:,3]==1).sum()),'sameActorRejected':int(rejected.sum()),'selected':int(use.sum()),'CPUGPURGBAndOwnerAndLayerExact':True,'actualActorRGBChanged':0 if ci<4 else int((expected[actor]!=fields[9][actor]).any(1).sum())})
   im=srgb(actual);images.append(im);draw.text((ci*320+6,fi*222+8),f"Actual F{f['frame']} {name} x{scale}: {int(use.sum())}",fill='white');board.paste(im,(ci*320+6,fi*222+32));board.paste(im.resize((w*6,h*6),Image.Resampling.NEAREST),(ci*320+80,fi*222+32))
  p=Image.new('RGB',(620,240),(25,27,32));d=ImageDraw.Draw(p);d.text((8,8),f"Actual F{f['frame']} | exterior x32 / same-frame hull x32 | 12x slow",fill='white')
  for i,im in enumerate([images[3],images[4]]):p.paste(im,(i*310+6,32));p.paste(im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST),(i*310+82,32))
  film.append(p);rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'cases':cases})
 draw.text((8,1345),'Actual generic exterior class preserves current actor RGB. Native painted pigment/lid producers are unchanged.',fill='white');draw.text((8,1366),'Large width controls are not adopted. Complete exterior band, feature history and full-face LUT remain unfinished.',fill='white');board.save(G/'ACTUAL_EXTERIOR_CLASS66.png');film[0].save(G/'ACTUAL_EXTERIOR_CLASS66.webp',save_all=True,append_images=film[1:],duration=200,loop=0,lossless=True)
 result={'actualGPUFrames':6,'actualWidthClassCases':30,'allRGBAndOwnerAndLayerByteExact':True,'originalWidthExteriorCounts':[x['cases'][1]['selected']for x in rows],'largeWidthCurrentActorOverwriteRemoved':[x['cases'][3]['sameActorRejected']for x in rows],'originalReferenceRetainedSameFrame':True,'genericActorInteriorOverwrite':0,'pigmentLidFeaturePathUnchanged':True,'product77DefaultChanged':False,'wholeCharacterBandAndHistoryCompleted':False,'fullFaceLUTCompleted':False,'rows':rows};(G/'ACTUAL_CLASS66.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
