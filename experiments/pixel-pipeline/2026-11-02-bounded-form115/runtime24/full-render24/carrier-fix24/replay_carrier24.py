"""CPU oracle using each packet's actual evaluated geometry and static alpha.
No old-frame geometry, rendered output upload, or fabricated source depth.
"""
from pathlib import Path
import json,sys,numpy as np
H=Path(__file__).resolve().parent;R=H.parent;BASE=R.parents[2]
sys.path.insert(0,str(R));sys.path.insert(0,str(BASE/'eye-failures114'))
from report_full24 import read,plane,buffer
from trace_carrier24 import origins,points
from trace114 import geometry
from geometry114 import Face114
from pairing114 import compose

def main():
 trace=read(H/'TRACE_CARRIER24.json');assert not trace['depthMismatch']
 source=read(BASE/'argon23-runtime113/SOURCE113.json');out=[];matched=[]
 for case in trace['zeroAssignedDepthCells']:
  p=Path(case['packet']);m=read(p/'RAW_MANIFEST.json');raw=geometry(p,m);face=Face114(raw,source['ownSkinMask'])
  x,y=case['tile'];roi=m['grid102']['eyeTopLeftROI'];cw=m['forward102']['canonicalSize'][0]//4;cx,cy=case['canonical'];at=cy*cw+cx
  z=np.full(16,case['selectedSourceDepth'],np.float32);xy=np.array(case['destinationXY'],np.float32)
  query=face.query(xy,z,case['eye'],limit=m['runtime24']['socketDiameters'][case['eye']-1]);vis=np.array([v['faceInterval']for v in query])
  canvas=plane(p/'L0-RGBA.plane')[1][y*4+1,x*4+1];meta=plane(p/'L0-META.plane')[1][y*4+1,x*4+1]
  hm=plane(p/'S4-meta.plane')[1][y*4:y*4+4,x*4:x*4+4];hc=plane(p/'S4-rgba.plane')[1][y*4:y*4+4,x*4:x*4+4]
  selected=buffer(p/'curve-colour.f32').reshape(-1,4)[at]
  result=compose({'fine':[{'fineXY':[i%4,i//4]}for i in range(16)]},vis,z,canvas,meta,selected,case['role'],case['eye'],hm,hc)
  #Validate this frame's CPU face oracle against a separate already measured
  #GPU query from the same source before trusting the new transported query.
  q=buffer(p/'ASSIGNED-depth24.f32').reshape(roi[3],roi[2],16,4);v=buffer(p/'ASSIGNED-visibility24.f32').reshape(q.shape)
  ys,xs=np.argwhere((q[:,:,:,2]>0).all(2))[0];known=q[ys,xs];owner=int(round(float(known[0,3])))
  reference=face.query(known[:,:2],known[:,2],owner,limit=m['runtime24']['socketDiameters'][owner-1]);vv=np.array([r['faceInterval']for r in reference])
  error=float(abs(vv-v[ys,xs,:,:2]).max());assert error<=1e-7,('Same-source oracle mismatch',case['sourceId'],error)
  matched.append({'sourceId':case['sourceId'],'tile':[int(xs),int(ys)],'pairedQueries':16,'maxVisibilityError':error})
  out.append({**{k:case[k]for k in ['sourceId','frame','run','tile','canonical','eye','role','selectedSourceDepth','ringDepthRange','sourceWitness','finalStatus']},
              'newDepth16':z.tolist(),'newFaceInterval16':vis.sum(0).tolist(),'newFinal':result,
              'remainingExternalOpaqueHits':sum(any(not h['exempt113']and h['alphaBounds'][0]>0 for h in q['hits'])for q in query)})
 #No new model/pose threshold: missing depth is recoverable only for a valid
 #selected source lid identity. Iris/white and absent/closed IDs keep old policy.
 def fallback(role,sourceDepth,lo,hi):return sourceDepth if np.isfinite(sourceDepth)and sourceDepth>0 and(role==6 or lo<=sourceDepth<=hi)else 0.
 assert fallback(6,1.,2.,3.)==1. and fallback(4,1.,2.,3.)==0.
 assert fallback(1,1.,2.,3.)==0. and fallback(6,0.,2.,3.)==0.
 assert fallback(0,0.,2.,3.)==0. and fallback(6,float('nan'),2.,3.)==0.
 report={'actualZeroDepthCases':len(out),'selectedLidNativeProvenanceVerified':True,'pairedGPUQueries':len(matched)*16,
         'sameSourceOracleChecks':matched,'newCases':out,'newGPUExecuted':False,
         'policy':'Ring z interval bounds only the aperture vertices; valid selected native lid pigment is not restricted to that interval. Destination external occlusion remains mandatory.',
         'syntheticNegativeCases':6,'UnityOrGPUCalls':0}
 (H/'REPLAY_CARRIER24.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'cases':len(out),'pairedGPUQueries':len(matched)*16,'status':[(q['run'],q['frame'],q['tile'],q['newFinal']['status'],q['newFinal']['role'],q['newFinal']['hairInterval'])for q in out]},ensure_ascii=False))
if __name__=='__main__':main()
