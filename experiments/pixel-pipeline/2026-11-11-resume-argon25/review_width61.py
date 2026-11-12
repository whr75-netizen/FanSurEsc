from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
import review_hull60 as api
from native_contour42 import coordinates
H=Path(__file__).resolve().parent;G=H/'face61';C=G/'capture'
def main():
 api.C=C;r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and r['pendingOwners']==0 and not r['errors']and len(r['frames'])==1
 f=r['frames'][0];read=lambda n:api.plane(r,f,n);x,y,w,h=f['QROI'];a=read('atlas40');fields=[a[:,i*w:(i+1)*w]for i in range(16)];outputs=read('widthCompositeAtlas61');b=read('ownerReceipts47');designed=b[:,3*w:4*w,0]==-4;owner=b[:,:w];info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);triangles=f['frameInfo']['sourceCarrier48']['triangleCount'];rows=[];imgs=[]
 for index,scale in enumerate([0,1,8,32]):
  first=20 if index==0 else 18 if index==1 else 22 if index==2 else 24
  line=read('nativeLogicalHull60'if index==1 else'widthCaseField'+str(first));proof=read('nativeLogicalHullProof60'if index==1 else'widthCaseField'+str(first+1));expected,gate=api.oracle_hull(line,proof,fields[9],fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink,triangles);actual=outputs[:,index*2*w:(index+1)*2*w];assert np.array_equal(actual,np.repeat(np.repeat(expected,2,0),2,1));use=gate[:,:,3]==1;src=gate[:,:,0]==1
  assert np.all(line[src,:3]==ink)and np.all((proof[src,3]>=1)&(proof[src,3]<=triangles))and np.all(proof[src,3]==np.rint(proof[src,3]))
  rows.append({'widthScale':scale,'sourceWidthMetres':f['frameInfo']['nativeOutlineWidthMetres39']*scale,'sourceHullCells':int(src.sum()),'selected':int(use.sum()),'positivePrimitiveUVSamples':int(use.sum()),'positiveFinalOwnerKind6Readback':False,'finalOwnerKind6Note':'Calibration output preserved RGB; final owner atlas was restored to default width1. Source primitive/UV and RGB are observed, per-case final owner write is not separately captured.','styleRejected':int((src&(gate[:,:,1]==0)).sum()),'worldRejected':int((src&(gate[:,:,2]==0)).sum()),'overwrittenDesignedEyeCells':int((use&designed).sum()),'overwrittenNativeFaceRoleCells':int((use&(fields[14][:,:,2]==1)&(owner[:,:,0]==4)).sum()),'newRGBColoursOutsideNativeOrSourceInk':int(((actual!=np.repeat(np.repeat(fields[9],2,0),2,1)).any(2)&(actual[:,:,:3]!=ink).any(2)).sum()),'selectedInkMismatch':int((expected[use,:3]!=ink).any(1).sum()),'unselectedNativeRGBChanged':int((expected[~use]!=fields[9][~use]).any(1).sum()),'CPUGPUByteExact':True})
  z=np.clip(actual[::-1,:,:3],0,1);z=np.where(z<=.0031308,12.92*z,1.055*np.power(z,1/2.4)-.055);imgs.append(Image.fromarray(np.uint8(np.rint(z*255))))
 assert rows[0]['selected']==rows[1]['selected']==0 and rows[2]['selected']>0 and rows[3]['selected']>rows[2]['selected']
 assert all(v['newRGBColoursOutsideNativeOrSourceInk']==v['selectedInkMismatch']==v['unselectedNativeRGBChanged']==0 for v in rows)
 result={'sourceId':f['sourceId'],'frame':f['frame'],'sameEvaluatedFrame':True,'actualGPUWidthCases':4,'CPUByteExactCases':4,'sourceColourProvenance':f['frameInfo']['sourceColour60'],'originalMaterialChanged':False,'artWidthScaleAdopted':False,'defaultScale':1,'designedEyeDomainCells':int(designed.sum()),'positiveUVPrimitiveEvidence':True,'perCaseFinalOwnerReadbackComplete':False,'shapeHistoryOrTimeStabilityValidated':False,'fullFacePaletteComplete':False,'rows':rows}
 (G/'analysis').mkdir(exist_ok=True);(G/'analysis/ACTUAL_WIDTH61.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 board=Image.new('RGB',(1440,360),(28,30,35));d=ImageDraw.Draw(board)
 for index,(im,row)in enumerate(zip(imgs,rows)):
  d.text((index*360+8,10),f"Actual GPU width x{row['widthScale']} | {row['selected']} cells",fill='white');board.paste(im,(index*360+8,38));board.paste(im.resize((224,224),Image.Resampling.NEAREST),(index*360+100,38))
 d.text((8,285),'Same evaluated source frame. Actual current source material/UV/alpha/depth. Default original width x1 remains unchanged.',fill='white')
 d.text((8,309),'x8/x32 are bounded calibration inputs, not adopted art settings. RGB/primitive/UV observed; per-case final owner/history incomplete.',fill='white')
 d.text((8,333),'Eye-domain intersections: '+str([v['overwrittenDesignedEyeCells']for v in rows])+'; domain includes support, not automatically visible iris/lid. No art setting adopted.',fill='white');board.save(G/'FACE_WIDTH_CALIBRATION61.png');print(json.dumps(result))
if __name__=='__main__':main()
