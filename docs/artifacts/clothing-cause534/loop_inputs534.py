from pathlib import Path
import struct,json
from collections import Counter
import numpy as np
O=Path(__file__).resolve().parent;RUN=O.parent/'Outline533/FullLoop';OLD=O.parent/'Cloth527/FullLoopB'
def buf(root,frame,tag,name):
 b=(root/f'{frame:03d}_{tag}_{name}.bin').read_bytes();w,h,x,y=struct.unpack_from('<4i',b);a=np.zeros((272,480,4),np.float32);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',offset=16).reshape(h,w,4);return a
def audit(root,tag):
 c0,c1=buf(root,0,tag,'FINAL'),buf(root,80,tag,'FINAL');m0,m1=buf(root,0,tag,'META'),buf(root,80,tag,'META');u0,u1=buf(root,0,tag,'UV'),buf(root,80,tag,'UV')
 valid=(c0[:,:,3]>.5)&(c1[:,:,3]>.5);same=valid&(m0[:,:,1]==m1[:,:,1])&(m0[:,:,3]==m1[:,:,3])&(np.max(abs(u0[:,:,:2]-u1[:,:,:2]),2)<2e-5)
 diff=np.max(abs(c1[:,:,:3]-c0[:,:,:3]),2);changed=same&(diff>1e-5);exact=valid&np.all(m0==m1,2)&np.all(u0==u1,2)
 rows=[{'xy':[int(x),int(y)],'role':int(m0[y,x,1]),'primitive':int(m0[y,x,3]),'RGB0':c0[y,x,:3].tolist(),'RGB80':c1[y,x,:3].tolist(),'UVMaxError':float(np.max(abs(u1[y,x,:2]-u0[y,x,:2]))),'depthError':float(abs(m1[y,x,0]-m0[y,x,0])),'exactMetaUV':bool(exact[y,x])}for y,x in np.argwhere(changed)]
 return {'alphaChanged':int(np.count_nonzero((c0[:,:,3]>.5)!=(c1[:,:,3]>.5))),'approxSurfaceRGBSamples':len(rows),'exactMetaUVChangedCount':int((exact&(diff>1e-5)).sum()),'rows':rows},(c0,c1,m0,m1,u0,u1)
on,bd=audit(RUN,'BASE');area,ad=audit(RUN,'ALT');off,od=audit(OLD,'BASE')
deltaB=bd[1][:,:,:3]-bd[0][:,:,:3];deltaA=ad[1][:,:,:3]-ad[0][:,:,:3];targets=[tuple(q['xy'])for q in area['rows']]
compare=[]
for x,y in targets:
 compare.append({'xy':[x,y],'bothVariantsRGBAtBothEndpointsEqual':bool(np.array_equal(bd[0][y,x],ad[0][y,x])and np.array_equal(bd[1][y,x],ad[1][y,x])),'deltaDifference':float(np.max(abs(deltaA[y,x]-deltaB[y,x]))),'historicalOFFReportedSameCoordinate':any(q['xy']==[x,y]for q in off['rows'])})
p0,p1=[json.loads((RUN/f'{i:03d}_probe.json').read_text())for i in[0,80]]
sourceB=(RUN/'000_ALT_GEOMETRY.bin').read_bytes();sourceE=(RUN/'080_ALT_GEOMETRY.bin').read_bytes()
def groups(b):
 at=0;out=[]
 for _ in range(2):
  nr=struct.unpack_from('<i',b,at)[0];at+=4;rs=[]
  for k in range(nr):
   n=struct.unpack_from('<i',b,at)[0];at+=4;rs.append(np.frombuffer(b,'<f4',2*n,at).reshape(-1,2));at+=n*8
  out.append(rs)
 return out
g0,g1=groups(sourceB),groups(sourceE);geometry=[]
for k in[0,1]:
 row={'group':'preFitClosedSource'if k==0 else'areaFittedCurve','lengths0':[len(r)for r in g0[k]],'lengths80':[len(r)for r in g1[k]]}
 if row['lengths0']==row['lengths80']:
  row['sameOrderedProjectedVerticesMaxCoordinateError']=max(float(np.max(abs(a-b)))for a,b in zip(g0[k],g1[k]))
 geometry.append(row)
availability={'pose':{'clipSame':p0['clip']==p1['clip'],'phase0':p0['phase'],'phase80':p1['phase'],'phaseDifference':p1['phase']-p0['phase'],'exactPhaseSame':p0['phase']==p1['phase'],'boneMatricesOrSkinPositionsSaved':False,'exactPoseEstablished':False},'camera':{'rotationSame':p0['rotation']==p1['rotation'],'offsetSame':p0['offset']==p1['offset'],'orthoSame':True,'effectiveProjectionAndWorldToCameraMatricesSaved':False},'lighting':{'skyHour0':p0['skyHour'],'skyHour80':p1['skyHour'],'hourSame':p0['skyHour']==p1['skyHour'],'allLightShadowWorldInputsSaved':False},'clock':{'captureDeltaSame':p0['capture']==p1['capture'],'elapsedAnimationIntervals':80,'shaderTimeOrFrameCounterSaved':False},'history':{'historyTexturesSaved':False,'measurement':'Full319View335.colour before final world Composite; downstream motion.historyColour cannot retroactively change this saved RT','headEyeHistoryNotFullyAudited':True},'originalOFF':{'available':True,'source':'old527 FullLoopB BASE','sameCurrentRunOrLighting':False,'formalMatchedInputControl':False}}
result={'status':'NO_IDENTICAL_ENDPOINT_INPUTS_NO_LOOP_REGRESSION_VERDICT','inputAvailability':availability,'projectedGeometry':geometry,'sameRun527_ON':on,'sameRun532_AREA':area,'historicalOriginalOFF':off,'areaVsDistanceControlAt28':compare,'all28IncrementalAreaEffectZero':all(q['bothVariantsRGBAtBothEndpointsEqual']for q in compare),'sameCoordinatesInHistoricalOFF':sum(q['historicalOFFReportedSameCoordinate']for q in compare),'limits':['Approximate source matching (UV<2e-5) is not identical input matching.','Historical OFF colour observations are not a matched-light/current-run causal test.','No new rendering or forced endpoint pose was performed.']}
(O/'LOOP_INPUT_AUDIT534.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'status':result['status'],'counts':{'527_ON':on['approxSurfaceRGBSamples'],'532_AREA':area['approxSurfaceRGBSamples'],'originalOFFHistorical':off['approxSurfaceRGBSamples']},'exactMetaUVChanged':{'527_ON':on['exactMetaUVChangedCount'],'532_AREA':area['exactMetaUVChangedCount'],'historicalOFF':off['exactMetaUVChangedCount']},'all28AreaEffectZero':result['all28IncrementalAreaEffectZero'],'historicalSameCoordinates':result['sameCoordinatesInHistoricalOFF'],'inputs':availability,'geometry':geometry}))
