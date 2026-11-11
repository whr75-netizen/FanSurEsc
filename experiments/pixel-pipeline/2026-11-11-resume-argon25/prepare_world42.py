from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face42/world'
def main():
 (G/'capture').mkdir(parents=True,exist_ok=True);(G/'build').mkdir(exist_ok=True);assert not(G/'capture/REQUEST.json').exists();r=json.loads((H/'face42/capture/COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors']and r['pendingOwners']==0
 s=(H/'face42/capture/RUN.cs.txt').read_text().replace('face42\\capture','face42\\world\\capture').replace('id="face42-native-"','id="face42-world-"')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep(' static CommandScript active;SourceOutline40 producer;',' WorldOccluder42 world42;static CommandScript active;SourceOutline40 producer;')
 rep('motion40=new MotionContour40(n,Root);motion40.Start();','world42=new WorldOccluder42(n);motion40=new MotionContour40(n,Root);motion40.Start();')
 rep('cohort[i].EvidenceRoot40=Root;','cohort[i].EvidenceRoot40=Root;cohort[i].BeforePrepare41=world42.Update;cohort[i].WorldProof41=world42.Snapshot;')
 rep(' void Restore(){if(restored)return;',' void Restore(){if(restored)return;world42?.Dispose();if(world42!=null)report["worldFixture41After"]=world42.Snapshot();')
 fixture=(H/'WorldOccluder42.cs').read_text();fixture=fixture[fixture.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'):];s+='\n'+fixture;p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/world42.dll');(G/'PREPARED_WORLD42.json').write_text(json.dumps({'CPUCompile':True,'captureSHA256':hashlib.sha256(s.encode()).hexdigest(),'newShaderImport':False,'newGPUKernel':False,'fixture':'Owned world quad attached before actual gameCamera world capture; ordinary camera render, no source hook/setting replacement','release':'After native GPU consumers complete and normal Edit return'},indent=2),encoding='utf-8');print('native world42 fixture compiled, not executed')
if __name__=='__main__':main()
