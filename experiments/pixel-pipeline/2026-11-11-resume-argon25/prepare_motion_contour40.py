from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'face40/motion';sys.path.insert(0,str(H))
from prepare_review30 import compile_source
def main():
 old=(H/'face40/compat/capture/RUN.cs.txt').read_text();done=json.loads((H/'face40/compat/capture/COMPLETE.json').read_text());assert done['restorationChecksPass']and done['ownedResourcesReleased']and done['pendingOwners']==0
 s=old.replace('face40\\compat\\capture','face40\\motion\\capture').replace('id="face40-"','id="face40-motion-"')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('List<Plane> tasks;float runtimeTime37;','List<Plane> tasks;MotionContour40 motion40;float runtimeTime37;')
 rep('void RestoreHold37(){if(held37)', 'void RestoreHold37(){motion40?.Dispose();if(motion40!=null)report["motionRestoration40"]=motion40.RestoreReport;if(held37)')
 a=s.index('runtimeTime37=Time.timeScale;CreateOnly40.Text(Path.Combine(Root,"POSE_HOLD_BEFORE37.json")');b=s.index('cohort=new SourceOutline40[6];',a)
 s=s[:a]+'motion40=new MotionContour40(n,Root);motion40.Start();'+s[b:]
 rep('cohort[i].TargetFrame40=Time.frameCount+2+i;','cohort[i].TargetFrame40=motion40.FirstTarget+i;cohort[i].MotionProof40=motion40.Snapshot;cohort[i].EvidenceRoot40=Root;')
 rep('if(!host.Ready)return;','if(!host.Ready)return;if(!held37){runtimeTime37=Time.timeScale;Time.timeScale=0;held37=true;motion40.Dispose();report["motionRestoration40"]=motion40.RestoreReport;report["motionEvents40"]=motion40.events;if(!motion40.Restored)throw new InvalidOperationException("40 motion state restoration failed");}')
 rep('public Func<Obj40> MotionProof40;','public Func<Obj40> MotionProof40;public string EvidenceRoot40{get;set;}')
 token='  QMetaLattice40.Require(';at=s.index(token);end=s.index('\n',at)
 s=s[:end]+'''\n  if(!String.IsNullOrEmpty(EvidenceRoot40)){var allIndices=Enumerable.Range(0,mesh.subMeshCount).Select(mesh.GetIndices).ToArray();if((long)vertices.Length*24+allIndices.Sum(a=>(long)a.Length*4)>1048576)throw new InvalidOperationException("40 CPU source geometry budget");using(var bw=new BinaryWriter(new FileStream(Path.Combine(EvidenceRoot40,"geometry-frame"+frame+".bin"),FileMode.CreateNew))){bw.Write("face-source-geometry40/v1");bw.Write(FrameKey);bw.Write(model);bw.Write(frame);bw.Write(vertices.Length);bw.Write(mesh.subMeshCount);for(int i=0;i<16;i++)bw.Write(view[i]);for(int i=0;i<16;i++)bw.Write(qvp[i]);for(int i=0;i<vertices.Length;i++){var p=transform.MultiplyPoint3x4(vertices[i]);var q=f.Project(p);bw.Write(p.x);bw.Write(p.y);bw.Write(p.z);bw.Write(q.x);bw.Write(q.y);bw.Write(weld40[i]);}foreach(var ix in allIndices){bw.Write(ix.Length);foreach(int i in ix)bw.Write(i);}}}\n'''+s[end:]
 helper=(H/'MotionContour40.cs').read_text();s=s+'\n'+helper
 G.mkdir(exist_ok=True);(G/'build').mkdir(exist_ok=True);c=G/'capture';c.mkdir(exist_ok=True);assert not(c/'REQUEST.json').exists();(c/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_source([c/'RUN.cs.txt'],G/'build/motion40.dll');(G/'PREPARED_MOTION40.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(s.encode()).hexdigest(),'CPUCompile':'passed','newAssets':0,'frames':6,'walkFrames':3,'turnFrames':3,'settingsReplacement':False,'normalInputEvents':True,'manualInputUpdate':False,'GPUExpectedOutputUpload':False,'CPU_sourceGeometryBudget':1048576,'atlasReadbackBudget':262144},indent=2),encoding='utf-8',newline='\n');print('Prepared normal-input walk3/turn3, bounded actual source geometry and atlas; CPU compile passed.')
if __name__=='__main__':main()
