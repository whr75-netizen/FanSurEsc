"""Existing92 normal capture plus one bounded CPU input observer on failure.

No new shader, Assets import, GPU algorithm, private reflection or retry loop.
Capture the current public body projection and opacity segments for offline
reproduction of the exact union, then existing error handling exits normally.
"""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face94'
def main():
 for d in ['build','capture','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists();s=(H/'face92/motion240/capture/RUN.cs.txt').read_text();s=s.replace('resume-20261111\\face92\\motion240\\capture','resume-20261111\\face94\\capture');assert'face92\\motion240\\capture'not in s
 # Same reciprocal input and selection as the failed run, existing92 raster.
 assert s.count('motion40.FirstTarget,240,24,motion40.Snapshot')==1;s=s.replace('motion40.FirstTarget,240,24,motion40.Snapshot','motion40.FirstTarget,480,24,()=>{if(Time.frameCount==motion40.FirstTarget)CaptureUnion94("baseline");return motion40.Snapshot();}').replace('["plannedSourceFrames"]=240','["plannedSourceFrames"]=480');assert'EditorApplication.timeSinceStartup-started>120'in s;s=s.replace('EditorApplication.timeSinceStartup-started>120','EditorApplication.timeSinceStartup-started>240')
 token=' void LogError(string message,string stack,LogType type){if(type!=LogType.Exception&&type!=LogType.Error)return;';assert s.count(token)==1;s=s.replace(token,(H/'UnionCapture94.cs.txt').read_text()+'\n'+token+'if(message.Contains("524 negative union winding"))CaptureUnion94("failure");');s=s.replace('id="face92-','id="face94-union-');assert'EvaluateForm115'not in s and'BoundRun115'not in s
 p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/union94.dll')
 for mode in ['final','post/final']:
  s=(H/'face93/motion480'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face93\\motion480','resume-20261111\\face94');p=G/mode/'RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build'/(mode.replace('/','-')+'94.dll'))
 (G/'console/ARGS.json').write_bytes((H/'face93/console/ARGS.json').read_bytes());r={'CPUCompiled':True,'existing92RasterOnly':True,'newShaderOrGPUAlgorithm':False,'captureBoundedProjectedInputOnOriginalError':True,'noUnionRetryInEditor':True,'normalErrorExitRestoreUnchanged':True,'plannedFrames':480,'newGPUExecuted':False};(G/'CPU_PREPARED94.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
if __name__=='__main__':main()
