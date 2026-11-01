from pathlib import Path
import json,hashlib,numpy as np
from analyse102 import buffer,load,save
from selection102 import cell,tests
H=Path(__file__).resolve().parent
def main():
 s=load(sorted((H/'motionH').glob('STATE102-*'))[-1]);assert s['stage']=='finished'and not s.get('error')and not s.get('restorationError')and s['PlayExited'];rows=[];mismatch=[];phase=[];reason={};total=0
 expected=load(H/'HIERARCHY_APPLIED102.json')['afterSHA256']
 for e in s['sequencePackets']:
  p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');assert m['forwardComputeSHA102']==expected;w,h=m['forward102']['canonicalSize'];d=buffer(p/'canonical-decision.f32');ids=buffer(p/'canonical-identity.f32');cols=buffer(p/'canonical-colour.f32');layers=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);vis=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4);changed=0
  for y in range(h//4):
   for x in range(w//4):
    k=y*(w//4)+x;ref=cell(layers,vis,x,y);r=ref['winner'];code=-1 if r<0 else [1,4,6,0][r]
    if code!=round(float(d[k,0])):mismatch.append({'frame':e['frame'],'xy':[x,y],'CPU':ref,'GPU':d[k].tolist()})
    reason[ref['reason']]=reason.get(ref['reason'],0)+1;old=ref['legacyUnique'];oldcode=-1 if not old else[1,4,6,0][old[0]];changed+=code!=oldcode;total+=1
  signature=hashlib.sha256(np.rint(ids[:,:2]).astype('<i4').tobytes()+np.rint(np.clip(cols[:,:3],0,1)*1e6).astype('<i4').tobytes()).hexdigest()
  r={'frame':e['frame'],'stage':e['testStage82'],'index':e['stageIndex82'],'unresolved':int((d[:,0]<0).sum()),'differentFromLegacyStrict':changed,'relativeCanonicalIdentityHash':hashlib.sha256(np.rint(ids[:,:2]).astype('<i4').tobytes()).hexdigest(),'identityAndLinearRGBSignature':signature,'rootProjected':m['motion82']['worldRootProjectedRaw'],'requestedPhase':m['motion82'].get('requestedPhase')};rows.append(r)
  if e['testStage82']=='measured-phase':phase.append(r)
 assert len(rows)==28 and len(phase)==10
 out={'actualFrames':28,'CPUReferenceCells':total,'CPUGPUSelectorMismatches':mismatch,'unresolvedByFrame':[r['unresolved']for r in rows],'changedFromLegacyStrictByFrame':[r['differentFromLegacyStrict']for r in rows],'reasons':reason,'phaseIdentityVariants':len({r['relativeCanonicalIdentityHash']for r in phase}),'phaseIdentityAndLinearRGBVariants':len({r['identityAndLinearRGBSignature']for r in phase}),'measuredPhaseRootXDelta':phase[8]['rootProjected'][0]-phase[0]['rootProjected'][0],'measuredPhaseReturnXError':phase[9]['rootProjected'][0]-phase[0]['rootProjected'][0],'sourceShaderSHA256':expected,'syntheticTests':tests(),'frames':rows,'noMinimumPixelBudget':True,'wholeFeatureBeforeChildParts':True,'productIntegrated':False}
 save(H/'HIERARCHY_VALIDATION102.json',out);print(json.dumps({k:v for k,v in out.items()if k not in ['frames','CPUGPUSelectorMismatches']}));print('CPU/GPU mismatches',len(mismatch))
if __name__=='__main__':main()
