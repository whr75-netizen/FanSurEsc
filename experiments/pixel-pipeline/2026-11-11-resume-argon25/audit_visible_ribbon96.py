from pathlib import Path
import json,sys,numpy as np,time
from PIL import Image
from actor_visibility96 import ActorQuery,packet
from review_packed93 import ribbon
from native_width86 import green_repeat_bilinear
from visible_ribbon96 import area,half,visible,positive_area_evidence
H=Path(__file__).resolve().parent
def main():
 root=Path(sys.argv[1]);report=json.loads((root/'capture/COMPLETE.json').read_text());assert report['packetComplete']and report['restorationChecksPass']and report['ownedResourcesReleased'];texture=np.asarray(Image.open(H/'face40/analysis-directed/SOURCE_WIDTH_MASK40.png').convert('RGBA'));rows=[]
 for f in report['stream77']['frames']:
  if'actorSource96'not in f:continue
  started=time.perf_counter();query=ActorQuery(root,f);a,_,_=packet(root,f);_,_,width,mapped,anchors,vp,view,data=ribbon(root/'capture'/f['ribbon93']['file']);w=f['QROI'][2];origin=np.array([f['QROI'][0],272-f['QROI'][1]-w]);shift=np.array([anchors[2]-anchors[0],-(anchors[3]-anchors[1])]);triangles=[]
  for row in data:
   ends=np.stack([row[3:6],row[6:9]]).astype(float);norm=np.stack([row[9:12],row[12:15]]).astype(float);g=green_repeat_bilinear(texture,row[15:19].reshape(2,2),False)if mapped else np.ones(2);points=np.r_[ends,ends+norm*(width*g)[:,None]];q=np.c_[points,np.ones(4)]@vp.astype(float).T;screen=(q[:,:2]/q[:,3,None]*[1,-1]+1)*w*.5+origin+shift;z=-(np.c_[points,np.ones(4)]@view.astype(float).T)[:,2]
   for ids in[[0,1,3],[0,3,2]]:
    xy=screen[ids]
    if area(xy)>0:triangles.append((int(row[0]),xy,z[ids],xy.min(0),xy.max(0)))
  for yy,xx in np.argwhere(a[10,:,:,3]==1):
   lo=origin+[xx,yy];hi=lo+1;pieces=[]
   for edge,xy,z,tlo,thi in triangles:
    if np.any(tlo>=hi)or np.any(thi<=lo):continue
    p=xy
    for n,c in[(np.array([1.,0]),-hi[0]),(np.array([-1.,0]),lo[0]),(np.array([0.,1]),-hi[1]),(np.array([0.,-1.]),lo[1])]:p=half(p,n,c)
    if not len(p):continue
    result=visible(query,p,xy,z,shift);pieces.append({'edge':edge,'sourceArea':area(p),'visibleLowerArea':result['lowerArea'],'visibleLowerAfterArithmeticUncertainty':positive_area_evidence(result['lower']),'visibleUpperArea':result['upperArea'],'knownOccluders':result['knownOccluders'],'unknownAlphaOccluders':result['unknownAlphaOccluders'],'lowerPolygons':[p.tolist()for p in result['lower']],'upperPolygons':[p.tolist()for p in result['upper']]})
   lower=sum(p['visibleLowerArea']for p in pieces);evidence=sum(p['visibleLowerAfterArithmeticUncertainty']for p in pieces);upper=sum(p['visibleUpperArea']for p in pieces);rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'xy':[int(xx),int(yy)],'pieces':pieces,'summedVisibleLowerNotUnionArea':lower,'summedVisibleLowerAfterArithmeticUncertainty':evidence,'summedVisibleUpperNotUnionArea':upper,'fullyOccludedInCPUModel':bool(pieces)and upper==0,'confirmedSomeVisibleInCPUModel':evidence>0,'partialNotWholeCellRejection':True})
  print(json.dumps({'frame':f['frame'],'CPUSeconds':time.perf_counter()-started,'actualSourceTriangles':sum(len(r['xy'])for r in query.rows)}),flush=True)
 out={'CPUModelFromActualSource':True,'sourceAlphaVerified':True,'allRibbonEdgesIncludedPerCell':True,'opaqueCellSamples':len(rows),'fullyOccludedCellSamples':sum(r['fullyOccludedInCPUModel']for r in rows),'confirmedPartiallyVisibleCellSamples':sum(r['confirmedSomeVisibleInCPUModel']for r in rows),'unknownCellSamples':sum(not r['fullyOccludedInCPUModel']and not r['confirmedSomeVisibleInCPUModel']for r in rows),'sourceFloatGPUIntervalUniversallyProven':False,'GPUIntegrationExecuted':False,'rows':rows};(root/'VISIBLE_RIBBON96.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items()if k!='rows'}))
if __name__=='__main__':main()
