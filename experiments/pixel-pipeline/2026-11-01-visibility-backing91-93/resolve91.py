"""Never convert unavailable other-mesh visibility into clear transmission."""
from pathlib import Path
import json,sys,numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'eye-close90'))
from surface_query90 import visibility_bounds,choose_joint_bounds

def alpha_bounds(source):
 out={}
 for q in source['queries']:
  mat=source['sources'][str(q['sourceSubMesh'])];lo,hi=q['min'],q['max']
  if mat['alphaTest']:
   if lo>=mat['cutoff']:value=[1.,1.]
   elif hi<mat['cutoff']:value=[0.,0.]
   else:value=[0.,1.] # derivatives not captured; do not guess the cutoff side
  elif mat['alphaBlend']:value=[max(0.,lo),min(1.,hi)]
  else:value=[1.,1.]
  out[q['id']]=value
 return out

def main():
 source=json.loads((HERE/'ALPHA_SOURCE91.json').read_text());assert source['success']and all(source['unchanged'].values());alpha=alpha_bounds(source);queries=json.loads((HERE/'QUERIES91.json').read_text())['queries'];data=np.load(HERE/'FROZEN_INPUT91.npz');details=[];cells=[]
 for q in queries:
  hits=[]
  for hit in q['hits']:
   if hit['depth']>=q['sourceDepth']-3e-5:continue
   mat=source['sources'][str(hit['sourcePart'])];cull=mat['cullMode'];winding=hit['projectedWinding']
   # The same stored source camera/mesh has observed front-face winding+1.
   if(cull==2 and winding!=1)or(cull==1 and winding==1):continue
   hits.append(hit)
  proof=visibility_bounds(hits,q['sourceDepth'],alpha)
  blocked=proof['upper']==0
  details.append({**q,'faceVisibilityBounds':[proof['lower'],proof['upper']],'allGeometryVisibilityBounds':[0.,proof['upper']],'definitelyOccluded':blocked,'unknownOtherMesh':not blocked,'firstOpaqueOccluder':next((h for h in proof['hits']if h['alphaBounds']==[1.,1.]),None),'usedHitBounds':proof['hits'],'reason':'actual front native triangle and original alpha'if blocked else'foreign hair/body exact ray geometry is absent; no clear-visibility claim'})
 classification=json.loads((HERE/'CLASSIFICATION91.json').read_text())
 for c in classification['cells']:
  cx,cy=c['rasterCell'];partLabels=[1,4,6];lower=np.zeros((3,16));upper=lower.copy();depth=np.full((3,16),np.inf)
  for q in details:
   if q['rasterCell']!=[cx,cy]:continue
   part=partLabels.index(q['part']);sx,sy=q['sample'];i=(sy-cy*4)*4+sx-cx*4;upper[part,i]=q['candidateAlpha']*q['allGeometryVisibilityBounds'][1];depth[part,i]=q['sourceDepth']
  decision=choose_joint_bounds(lower,upper,depth,partLabels);line=[q for q in details if q['rasterCell']==[cx,cy]and q['part']==6]
  cells.append({**c,'oldSelectedRole':6,'candidateSamples':len(line),'definitelyOccludedLineSamples':sum(q['definitelyOccluded']for q in line),'lineSamplesWithoutProofOfClearVisibility':sum(not q['definitelyOccluded']for q in line),'decision':decision,'nativePixels':len(c['nativePixelsBottomLeft'])})
 report={'status':'SAME_FRAME_EXACT_FACE_RAY_ALPHA_WITH_EXPLICIT_OTHER_MESH_UNKNOWN','sourceId':classification['sourceId'],'frame':140,'serial':classification['serial'],'remainingNativePixels':56,'backingNativePixels':36,'eyelineNativePixels':20,'cells':cells,'queryCount':len(details),'oldUnknownQueries':sum(q['oldUnknown']for q in details),'newDefinitelyOccludedQueries':sum(q['definitelyOccluded']for q in details),'opaqueBlockedOldUnknown':sum(q['definitelyOccluded']and q['oldUnknown']for q in details),'opaqueBlockedOldScalarPositive':sum(q['definitelyOccluded']and q['oldScalarVisibility']>0 for q in details),'robustBackgroundNativePixels':sum(c['nativePixels']for c in cells if c['decision']['winner']==0),'remainingUncertainNativePixels':sum(c['nativePixels']for c in cells if c['decision']['winner']is None),'productIntegrated':False,'details':details,'currentLimit':'Opaque-face rejection is proven where upper0. A visible role is not accepted without actual other-mesh visibility. No unknown is multiplied as transparent.'}
 (HERE/'VISIBILITY_RESULT91.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['details','cells']},indent=2));print(json.dumps([{'cell':c['rasterCell'],'decision':c['decision']['winner'],'lineUpper':c['decision']['massBounds']['6'][1],'occluded':c['definitelyOccludedLineSamples'],'samples':c['candidateSamples']}for c in cells],indent=2))
if __name__=='__main__':main()
