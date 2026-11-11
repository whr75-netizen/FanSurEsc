from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face41/world'
def main():
 (G/'capture').mkdir(parents=True,exist_ok=True);(G/'build').mkdir(exist_ok=True);assert not(G/'capture/REQUEST.json').exists()
 r=json.loads((H/'face41/capture/COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors']and r['pendingOwners']==0
 s=(H/'face41/capture/RUN.cs.txt').read_text().replace('face41\\capture','face41\\world\\capture').replace('id="face41-final-"','id="face41-world-"')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep(' static CommandScript active;SourceOutline40 producer;',' WorldOccluder41 world41;static CommandScript active;SourceOutline40 producer;')
 rep('motion40=new MotionContour40(n,Root);motion40.Start();','world41=new WorldOccluder41(n);motion40=new MotionContour40(n,Root);motion40.Start();')
 rep('cohort[i].EvidenceRoot40=Root;','cohort[i].EvidenceRoot40=Root;cohort[i].BeforePrepare41=world41.Update;cohort[i].WorldProof41=world41.Snapshot;')
 rep(' void Prepare(){\n',' void Prepare(){\n  PrepareWorld41();\n')
 rep(' void Restore(){if(restored)return;',' void Restore(){if(restored)return;world41?.Dispose();if(world41!=null)report["worldFixture41After"]=world41.Snapshot();')
 # Replace only the appended partial helper, preserving the executed baseline.
 a=s.rindex('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\npublic sealed partial class SourceOutline40 {');helper=(H/'FinalContour41.cs').read_text();helper=helper[helper.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'):];s=s[:a]+helper
 fixture=(H/'WorldOccluder41.cs').read_text();fixture=fixture[fixture.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'):];s+='\n'+fixture
 p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/world41.dll');(G/'PREPARED_WORLD41.json').write_text(json.dumps({'CPUCompile':True,'captureSHA256':hashlib.sha256(s.encode()).hexdigest(),'newShaderImport':False,'newGPUKernel':False,'fixture':'Owned ordinary-world quad; no collider/light/persistent asset, source pose hook or InputSettings replacement','release':'After producer/consumer GPU completion and normal Edit return'},indent=2),encoding='utf-8');print('world fixture runner compiled; not executed')
if __name__=='__main__':main()
