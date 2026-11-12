"""Same480-frame workload; align transport lifetime and measured wall budget.

291 completed frames took~196s in the interrupted run (~.674s/frame).
480 extrapolates to~324s;420s includes startup/observation margin. This bounds
normal CPU/IO observation, never a GPU completion timeout or TDR setting.
No per-frame workload, renderer, shader, input, completion or release change.
"""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face94/held480'
def main():
 for d in ['build','capture','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists();s=(H/'face94/verify480/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face94\\verify480\\capture','resume-20261111\\face94\\held480\\capture').replace('face94-fixed-union-ribbon480-','face94-fixed-union-held480-');assert s.count('EditorApplication.timeSinceStartup-started>240')==1;s=s.replace('EditorApplication.timeSinceStartup-started>240','EditorApplication.timeSinceStartup-started>420').replace('93 declared480-frame240s observation limit','94 measured480-frame420s CPU-IO observation limit');p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/held94.dll')
 for mode in ['final','post/final']:
  p=G/mode/'RUN.cs.txt';p.write_text((H/'face94/verify480'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face94\\verify480','resume-20261111\\face94\\held480'),encoding='utf-8',newline='\n');compile_unity_language(p,G/'build'/(mode.replace('/','-')+'94.dll'))
 (G/'console/ARGS.json').write_bytes((H/'face93/console/ARGS.json').read_bytes());r={'CPUCompiled':True,'plannedFrames':480,'simulationSeconds':8,'observationWallSeconds':420,'measured291FrameSeconds':196,'normalWorkEstimateSeconds':324,'perFrameWorkloadOrGPUCompletionGuardsChanged':False,'officialSessionHeldUntilOwnedTerminal':True,'newPlayExecuted':False};(G/'CPU_PREPARED94.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
if __name__=='__main__':main()
