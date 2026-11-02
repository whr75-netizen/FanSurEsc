"""F103 stage2 work bounds and partition equivalence from actual GPU stage1 bytes.
No shader/Unity/GPU compilation or dispatch. Historical fixture builder is imported,
never executed; only its original float32 compare/merge helpers are reused.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from prepare_fixture import F,U,K,fb,fv,group_invalid,merge,distance

def main():
 case=json.loads((H/'CASE.json').read_text());run=H/'runs'/case['RunId']/'stage-01'
 receipt=json.loads((run/'COMPLETE.json').read_text());assert receipt['Success']and receipt['ExecutionKind']=='gpu-prefix'and receipt['DispatchCalls']==1
 table=np.zeros((16384,8),'<u4')
 for name,start in [('subsets-I',0),('subsets-W',4096)]:
  raw=(run/(name+'.bin')).read_bytes();spec=next(x for x in case['InputFiles']if x['Name']==name)
  assert hashlib.sha256(raw).hexdigest()==spec['Sha256'];table[start:start+64]=np.frombuffer(raw,'<u4').reshape(64,8)
 frame=np.frombuffer((H/'fixture/frame.bin').read_bytes(),'<u4').reshape(2,32,4)
 assert frame[0,0].tolist()==[9,5,6,0]
 mass=frame[0,1].view('<f4');active=frame[0,2];canvas=fv(frame[0,3,0]);states=[];eligible=0;valid_flags=0
 for state in range(2048):
  a=table[state&31];b=table[4096+(state>>5)];g=group_invalid()
  if a[5]and b[5]:valid_flags+=1
  if a[5]and b[5]and not(a[0]&b[0]):
   eligible+=1;cost=F(F(canvas+fv(a[4]))+fv(b[4]));score=[F((int(active[0])&~int(a[1])).bit_count()+(int(active[1])&~int(b[1])).bit_count()),distance(F(a[3]+b[3])*K,F(mass[0]+mass[2]),F(mass[1]+mass[3])),F(distance(F(a[3])*K,mass[0],mass[1])+distance(F(b[3])*K,mass[2],mass[3])),max(cost,F(0))]
   g=U([fb(x)for x in score]+[a[0],a[0],b[0],b[0],(int(active[2])&~int(a[2]|b[2])).bit_count(),1,fb(F(fv(a[6])+fv(b[6]))),0])
  states.append(g)
 def group(index):
  shared=[g.copy()for g in states[index*64:index*64+64]];stride=32
  while stride:
   for i in range(stride):shared[i]=merge(shared[i],shared[i+stride])
   stride//=2
  return shared[0]
 groups=np.array([group(g)for g in range(32)],'<u4');expected=(H/'fixture/groups.bin').read_bytes();assert groups.tobytes()==expected
 partitions=[]
 for chunk in [1,2,3,4,5,8,16,31,32]:
  rebuilt=np.zeros_like(groups);ranges=[list(range(i,min(32,i+chunk)))for i in range(0,32,chunk)]
  for part in reversed(ranges):
   for g in part:rebuilt[g]=group(g)
  assert rebuilt.tobytes()==expected
  partitions.append({'groupsPerHypotheticalDispatch':chunk,'dispatches':len(ranges),'threadsPerFullChunk':chunk*64,'byteEqual':True,'offsetAndIndexedOutputModelRequired':True})
 bad=np.array([group_invalid()for _ in range(32)],'<u4')
 for _ in range(2):
  for g in range(16):bad[g]=group(g)
 changed=int(np.count_nonzero(np.any(bad!=groups,axis=1)));assert changed>0
 out={'scope':'CPU source-level audit; no GPU-time inference','UnityOrGPUCalls':0,'actualStage1SourceId':receipt['SourceId'],'actualStage1OutputsSHA256':{x['Name']:x['Sha256']for x in receipt['Outputs']},'header':[9,5,6,0],
  'currentStage2':{'dispatches':1,'groups':[32,1,1],'threadsPerGroup':64,'threads':2048,'states':2048,'validSubsetFlagPairs':valid_flags,'nonOverlappingEligibleStates':eligible,'groupOutputs':32,'outputBytes':1536,'ownedStructuredBytes':3671040,'uavs':3,'groupsharedBytesPerGroup':3072,'privateArrays':0,'BVHVisits':0,'pointOrCurveLoops':0,'perLaneGroupReductionRounds':6,'barriersPerGroup':7,'groupBarrierPoints':224,'laneBarrierArrivals':14336,'totalGroupMergeCalls':2016,'maxLessCallsPerMerge':2,'maxScorePositionsPerLess':4,'maxScorePositionChecksInMerges':16128,'frameRecordIndices':[0,1,2,3],'subsetReadIndexRanges':[[0,31],[4096,4159]],'groupWriteIndexRange':[0,31],'allocatedSubsetElements':16384,'allocatedGroupElements':65536},
  'cpuWholeGroupsSHA256':hashlib.sha256(groups.tobytes()).hexdigest(),'matchesPriorCpuOracleGroups':True,'partitions':partitions,'naiveTwo16GroupDispatchesWithoutOffset':{'equivalent':False,'changedGroups':changed,'reason':'SV_GroupID restarts at zero and writes groups0..15 twice; groups16..31 are omitted'},
  'minimalUnchangedShaderPrefixProbe':{'groups':[1,1,1],'threads':64,'actualGroupOutputBytes':48,'group0CpuExpectedSHA256':hashlib.sha256(groups[0].tobytes()).hexdigest(),'onlyGroup':0,'completeStage2':False,'currentHostSupportsThisVariant':False,'submitted':False},
  'fullSplitCondition':'Add one explicit group-base uniform for state index and destination index, retaining the original within-group reduction tree and all seven barriers; validate complete non-overlapping32-group coverage in receipt protocol. Not implemented/imported/executed here.',
  'limits':['CPU model of a proposed group-base change is not GPU bytecode validation','Current full stage2 command is2048threads, not the full runtime4194304thread enumeration','A bounded workload or successful prior BuildSubsets does not resolve previous TDR cause','No next GPU stage is approved or submitted']}
 with(H/'ENUMERATE_BUDGET24.json').open('w',encoding='utf-8',newline='\n')as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
