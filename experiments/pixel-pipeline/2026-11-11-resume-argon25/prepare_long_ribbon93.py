"""480 actual frames,8s simulation; bounded observed240-frame work doubled.

No timeout workaround for a failed kernel. Same successful440-instruction
ribbon,24-plane readback and normal reciprocal input. A240s observation budget
is explicit for twice the240-frame workload, not a GPU completion guarantee.
"""
from pathlib import Path
import json,re,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face93/motion480'
def main():
 for d in ['capture','build','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final']);r=json.loads((H/'face93/witness-fix/capture/COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors']
 s=(H/'face93/witness-fix/capture/RUN.cs.txt').read_text();marker='namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\npublic sealed partial class SourceOutline40 {\n readonly RTHandle[] ribbonFields93';p=s.rfind(marker);assert p>0;s=s[:p]+(H/'Ribbon93.cs.txt').read_text();s=s.replace('resume-20261111\\face93\\witness-fix\\capture','resume-20261111\\face93\\motion480\\capture').replace('face93-guarded-witness-ribbon-','face93-reciprocal-RGB-ribbon480-');assert s.count('motion40.FirstTarget,1,1,motion40.Snapshot')==1;s=s.replace('motion40.FirstTarget,1,1,motion40.Snapshot','motion40.FirstTarget,480,24,motion40.Snapshot').replace('["plannedSourceFrames"]=1','["plannedSourceFrames"]=480')
 reference=(H/'face92/motion240/capture/RUN.cs.txt').read_text()
 for prefix in ['void AfterFrame(ScriptableRenderContext context,Camera[] cameras)','public Obj40 Snapshot()']:
  pattern=re.escape(prefix)+r'[^\n]+';old=re.findall(pattern,s);new=re.findall(pattern,reference);assert len(old)==len(new)==1,(prefix,len(old),len(new));s=s.replace(old[0],new[0])
 assert s.count('EditorApplication.timeSinceStartup-started>120')==1;s=s.replace('EditorApplication.timeSinceStartup-started>120','EditorApplication.timeSinceStartup-started>240').replace('77 bounded observation limit; no extension or retry','93 declared480-frame240s observation limit; no retry or time-based resource release');assert 'bytes.Length>262144'in s and 'EvaluateForm115'not in s and 'BoundRun115'not in s;(G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/long93.dll')
 for mode in ['final','post/final']:
  t=(H/'face93/witness-fix'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face93\\witness-fix','resume-20261111\\face93\\motion480');(G/mode/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'93.dll'))
 (G/'console/ARGS.json').write_text((H/'face93/console/ARGS.json').read_text());d={'externalCSharp9Compiled':True,'targetFrames':480,'simulationSeconds':8,'observationBudgetSeconds':240,'priorMeasured240FrameWallSeconds':93.4,'normalInputSameAsPassed240':True,'shaderSHA256':hashlib.sha256((H/'ProjectedRibbon93.shader').read_bytes()).hexdigest(),'readbackBytesPerFrame':259584,'capUnchanged':262144,'noNewShaderOrGPUKernel':True,'newGPUExecuted':False};(G/'CPU_PREPARED93.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
