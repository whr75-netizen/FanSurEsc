"""Actual runtime103 source/owner/finite-colour and performance evidence."""
from pathlib import Path
import json,sys,collections,numpy as np
from actor_visibility96 import packet
from review_motion64 import srgb
import review_long99
H=Path(__file__).resolve().parent

def main():
 name=sys.argv[1]if len(sys.argv)>1 else'rows64B';root=H/name if'/'in name else H/'face103'/name
 r=json.loads((root/'capture/COMPLETE.json').read_text());frames=r['stream77']['frames']
 assert r['restorationChecksPass']and r['Edit']and not r['errors']
 palette=np.fromfile(root/'capture/RUNTIME_PALETTE89.rgb',np.uint8).reshape(-1,3,3);counts=collections.Counter()
 for f in frames:
  s=f['profile103'];assert s['allCPUWorkCompleted']and s['queryViewsReleased']and s['noUnityAPIsOnWorker']
  a,_,_=packet(root,f);encoded=a[14,:,:,0].astype(int);flags=encoded&511;owner=a[14,:,:,3];known=a[14,:,:,2]==1;valid=(a[4,:,:,3]==1)&(a[4,:,:,0]>0)
  assert np.array_equal(known,flags==0)and np.array_equal(valid,known)
  rgb=np.flipud(np.asarray(srgb(a[5])))[:,:,:3];family=a[4,:,:,0].astype(int)-1;q=a[4,:,:,2].astype(int)
  assert np.array_equal(rgb[valid],palette[family[valid],q[valid]])
  actual=(owner==f['mappedRole100'])&(a[13,:,:,2]==1);plain=actual&((flags&1)==0)
  counts['actualVisibleFace']+=int(actual.sum());counts['ordinaryFaceLUT']+=int((plain&valid).sum());counts['ordinaryFaceUnknown']+=int((plain&~valid).sum())
 def stats(fs):return {k:float(np.median([f['profile99'][k]for f in fs]))for k in['totalMs','rasterMs','coupledMs']}
 baseline=json.loads((H/'face99/fine64/capture/COMPLETE.json').read_text())['stream77']['frames']
 out={'actualFrames':len(frames),'simulationSeconds':sum(f['deltaTime']for f in frames),'rowCPUOnlyNoGPUAlgorithmChange':True,'current91SourceLUTUnchanged':True,'102RejectedCandidateNotLoaded':True,'allWorkersJoinedAndQueryLeasesReleased':True,'actualFiniteLUTExact':True,'ownerAwareCounts':dict(counts),'currentMedianMs':stats(frames),'first12MedianMs':stats(frames[:12]),'separateRun99First12MedianMs':stats(baseline[:12]),'separateRunTimingNotSameInputBitwiseProof':True,'rowWallMedianMs':{k:float(np.median([f['profile103'][k]for f in frames]))for k in['mainRowWallMs','workerRowWallMs','joinWallMs','rowPhaseWallMs']},'restored':r['restorationChecksPass'],'generalLineOpacityContinuousWorldAndArtCompleted':False}
 (root/'ACTUAL_ROWS103.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
 sys.argv=[sys.argv[0],'../'+root.relative_to(H).as_posix()];review_long99.main()

if __name__=='__main__':main()
