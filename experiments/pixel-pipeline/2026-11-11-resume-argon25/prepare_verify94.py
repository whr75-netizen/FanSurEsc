"""Actual same480-frame motion after the CPU-confirmed carrier precision fix.

Reuse successfully observed93 ribbon/92 LUT and bounded24-plane readback.
Only the three production clothing source projection files changed; no new
GPU algorithm, import, input settings replacement or manual rendering here.
"""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face94/verify480'
def main():
 r=json.loads((H/'face94/recompile/post/RESULT.json').read_text());assert r['Edit']and r['globalBytesEqual']and r['inputSameIdAndJSONAndDevices']and all(x['equal']is True for x in r['nativeChecks'])
 for d in ['build','capture','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists();s=(H/'face93/motion480/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face93\\motion480\\capture','resume-20261111\\face94\\verify480\\capture').replace('face93-reciprocal-RGB-ribbon480-','face94-fixed-union-ribbon480-');p=(H/'UnionCapture94.cs.txt').read_text();p=p.replace('op.Anchors.Count*24L','op.Anchors.Count*40L').replace('segments.Count*16L','segments.Count*32L').replace('var segments=op.Project(points,fit)','var segments=op.ProjectExact94(points,fit)').replace('union-input94/v1','union-input94/v2').replace('b.Write(a.weights.z);','b.Write(a.weights.z);b.Write(a.weightB94);b.Write(a.weightC94);').replace('b.Write(s.Item1.x);b.Write(s.Item1.y);b.Write(s.Item2.x);b.Write(s.Item2.y);','b.Write(s.Item1.X);b.Write(s.Item1.Y);b.Write(s.Item2.X);b.Write(s.Item2.Y);');assert'ProjectExact94'in p and'weightB94'in p;(G/'UNION_CAPTURE_V2.cs.txt').write_text(p,encoding='utf-8',newline='\n');token=' void LogError(string message,string stack,LogType type){if(type!=LogType.Exception&&type!=LogType.Error)return;';assert s.count(token)==1;s=s.replace(token,p+'\n'+token+'if(message.Contains("524 negative union winding"))CaptureUnion94("failure");');assert s.count('motion40.FirstTarget,480,24,motion40.Snapshot')==1;s=s.replace('motion40.FirstTarget,480,24,motion40.Snapshot','motion40.FirstTarget,480,24,()=>{int at94=Time.frameCount-motion40.FirstTarget;if(at94==0)CaptureUnion94("baseline");if(at94==479)CaptureUnion94("final");return motion40.Snapshot();}');assert'EvaluateForm115'not in s and'BoundRun115'not in s;p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/verify94.dll')
 for mode in ['final','post/final']:
  p=G/mode/'RUN.cs.txt';p.write_text((H/'face94'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face94','resume-20261111\\face94\\verify480'),encoding='utf-8',newline='\n');compile_unity_language(p,G/'build'/(mode.replace('/','-')+'94.dll'))
 (G/'console/ARGS.json').write_bytes((H/'face93/console/ARGS.json').read_bytes());out={'CPUCompiledAgainstUpdatedAssembly':True,'plannedFrames':480,'simulationSeconds':8,'existing93RibbonAnd92Colour':True,'readbackBytes':259584,'newShaderOrGPUAlgorithm':False,'runtimeDoubleCarrierInputConnected':True,'runtimeDoubleCarrierInputObserved':False,'newPlayExecuted':False};(G/'CPU_PREPARED94.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=='__main__':main()
