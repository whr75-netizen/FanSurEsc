"""Proposed parent-order rule on actual61 packets; explicitly CPU only."""
from pathlib import Path
import json,numpy as np
import review_hull60 as api
from native_contour42 import coordinates
from face_parent62 import resolve
H=Path(__file__).resolve().parent;G=H/'face62';C=H/'face61/capture'
def main():
 api.C=C;r=json.loads((C/'COMPLETE.json').read_text());f=r['frames'][0];read=lambda n:api.plane(r,f,n);w=f['QROI'][2];a=read('atlas40');fields=[a[:,i*w:(i+1)*w]for i in range(16)];b=read('ownerReceipts47');domain=b[:,3*w:4*w].copy();domain[:,:,0]=(domain[:,:,0]==-4);eyes=read('featureProducer49');visible=eyes[:,w:2*w];info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);rows=[]
 for idx,scale in enumerate([0,1,8,32]):
  first=[20,18,22,24][idx];line=read('nativeLogicalHull60'if idx==1 else'widthCaseField'+str(first));proof=read('nativeLogicalHullProof60'if idx==1 else'widthCaseField'+str(first+1));out,gate,blocked=resolve(line,proof,fields[9],fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink,4232,visible,domain,b[:,:w]);use=gate[:,:,3]==1;assert np.array_equal(out[blocked],fields[9][blocked]);assert not(use&blocked).any()
  coords=[{'localPixel':[int(x),int(y)],'visibleFeature':float(visible[y,x,0]),'eyeId':float(visible[y,x,1]),'weight':float(visible[y,x,2]),'nativeOwnerRole':float(b[y,x,0]),'primitive':int(proof[y,x,3])}for y,x in np.argwhere(blocked)]
  rows.append({'scale':scale,'selectedAfterProposedLayerRule':int(use.sum()),'confirmedVisibleChildrenRestored':int(blocked.sum()),'restored':coords})
 assert [v['confirmedVisibleChildrenRestored']for v in rows]==[0,0,0,6]and [v['selectedAfterProposedLayerRule']for v in rows]==[0,0,7,52]
 data={'input':'actual61 same-frame raw data','CPUOnly':True,'GPUExecutedByThisScript':False,'proposedRule':'face outline decoration below visible same-actor eye children only when native final owner role confirms child; canvas not protected; actual hair/world tests remain prior gates','allCurrentEyesRestoredInLargeWidthCounterexample':True,'rows':rows};(G/'CPU_REPLAY62.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data))
if __name__=='__main__':main()
