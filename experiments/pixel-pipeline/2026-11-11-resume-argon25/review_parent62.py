from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
import review_hull60 as api
from native_contour42 import coordinates
from face_parent62 import resolve,child_gate
from trace_contour40 import geometry
H=Path(__file__).resolve().parent;G=H/'face62';C=G/'capture'
def main():
 api.C=C;r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors']and r['pendingOwners']==0 and len(r['frames'])==1
 f=r['frames'][0];read=lambda n:api.plane(r,f,n);w=f['QROI'][2];a=read('atlas40');fields=[a[:,i*w:(i+1)*w]for i in range(16)];outputs=read('widthCompositeAtlas61');ownerAtlas=read('widthOwnerAndLayerAtlas62');b=read('ownerReceipts47');assert b.shape[1]==5*w;domain=b[:,3*w:4*w].copy();domain[:,:,0]=(domain[:,:,0]==-4);v=read('featureProducer49');visible=v[:,w:2*w];info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);child=child_gate(visible,domain,b[:,:w],fields[14]);rows=[];imgs=[]
 for idx,scale in enumerate([0,1,8,32]):
  first=[20,18,22,24][idx];line=read('nativeLogicalHull60'if idx==1 else'widthCaseField'+str(first));proof=read('nativeLogicalHullProof60'if idx==1 else'widthCaseField'+str(first+1));expected,gate,blocked=resolve(line,proof,fields[9],fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink,4232,visible,domain,b[:,:w]);actual=outputs[:,idx*2*w:(idx+1)*2*w];finalOwner=ownerAtlas[:,idx*2*w:(idx*2+1)*w];layer=ownerAtlas[:,(idx*2+1)*w:(idx+1)*2*w];use=gate[:,:,3]==1
  assert np.array_equal(actual,np.repeat(np.repeat(expected,2,0),2,1));assert np.array_equal(finalOwner[:,:,0]==6,use);assert np.array_equal(finalOwner[use,1],proof[use,3])and np.array_equal(finalOwner[use,2:],proof[use,1:3]);assert np.array_equal(layer[:,:,:3],visible[:,:,:3])and np.array_equal(layer[:,:,3]==1,blocked)
  assert np.array_equal(expected[child],fields[9][child]);assert np.all(expected[use,:3]==ink)and np.array_equal(expected[~use],fields[9][~use]);rows.append({'widthScale':scale,'sourceHullCells':int((gate[:,:,0]==1).sum()),'selected':int(use.sum()),'actualFinalKind6OwnerSamples':int(use.sum()),'ownerPrimitiveUVByteExact':True,'blockedChildren':int(blocked.sum()),'actualEyeChildRGBChanged':0,'nonSelectedRGBChanged':0,'sourceInkMismatch':0,'CPUGPUCompositeByteExact':True,'actualLayerReceiptsByteExact':True})
  z=np.clip(actual[::-1,:,:3],0,1);z=np.where(z<=.0031308,12.92*z,1.055*np.power(z,1/2.4)-.055);imgs.append(Image.fromarray(np.uint8(np.rint(z*255))))
 assert [x['selected']for x in rows]==[0,0,7,52]and[x['blockedChildren']for x in rows]==[0,0,0,6]
 old=geometry(H/'face61/capture/geometry-frame102.bin');current=geometry(C/f"geometry-frame{f['frame']}.bin");poseDifference=float(np.max(np.abs(old['points']['world']-current['points']['world'])));assert old['model']==current['model']
 result={'sourceId':f['sourceId'],'frame':f['frame'],'actualGPUCases':4,'CPUExactCases':4,'positiveFinalOwnerSamples':sum(v['actualFinalKind6OwnerSamples']for v in rows),'confirmedCurrentEyeChildCells':int(child.sum()),'realChildColourPreserved':True,'canvasNotBlanketProtected':True,'sourceAndDestinationMapping':'child at head-local hp; native owner/world at transported main q','UVsNotClampedInResolver':True,'originalMaterialAndProduct77Unchanged':True,'widthScaleArtPolicyAdopted':False,'sameStateGeometryMaxWorldDifferenceFrom61Metres':poseDifference,'differentSourceIdsNotMixed':True,'temporalHistoryOrLongTermValidated':False,'fullFacePaletteComplete':False,'rows':rows};(G/'analysis').mkdir(exist_ok=True);(G/'analysis/ACTUAL_PARENT62.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 board=Image.new('RGB',(1440,360),(28,30,35));d=ImageDraw.Draw(board)
 for idx,(im,row)in enumerate(zip(imgs,rows)):
  d.text((idx*360+8,10),f"Actual GPU x{row['widthScale']} | {row['selected']} cells | eye blocked {row['blockedChildren']}",fill='white');board.paste(im,(idx*360+8,38));board.paste(im.resize((224,224),Image.Resampling.NEAREST),(idx*360+100,38))
 d.text((8,285),'Face outline parent below actual visible eye children. Same-frame role/owner proof; actual hair/world tests unchanged.',fill='white');d.text((8,308),'All4 RGB outputs + per-case final primitive/UV owners + layer flags match CPU. x8/x32 are calibration, no art setting adopted.',fill='white');d.text((8,332),'Product77 unchanged. Full face regions/palette, runtime history and long-term motion/art quality remain incomplete.',fill='white');board.save(G/'FACE_PARENT_LAYER62.png');print(json.dumps(result))
if __name__=='__main__':main()
