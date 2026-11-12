"""Same previously successful reciprocal input, current226-address runtime."""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face92/motion240'
def main():
 for d in ['capture','build','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final'])
 base=(H/'face91/bounded192/capture/RUN.cs.txt').read_text();runtime=(H/'face92/gpu/capture/RUN.cs.txt').read_text();marker='// Pure CPU construction. Final runtime RGB';base=base[:base.index(marker)]+runtime[runtime.index(marker):];old='field89=new SourceField89(Path.GetFullPath(Path.Combine(root,"..","face88")),eye,width,height,evidence89);';new='field89=new SourceField89(Path.GetFullPath(Path.Combine(root,"..","face92")),eye,width,height,evidence89,new SourceFiles89{table="TABLE92.json",reference="REFERENCES92.rgb",order="ORDERS92.i32",address="ADDRESS92.r32",control="PALETTE92.rgb",contrast="CONTRAST92.i32"});';assert base.count(old)==1;base=base.replace(old,new).replace('resume-20261111\\face91\\bounded192\\capture','resume-20261111\\face92\\motion240\\capture').replace('face91-reciprocal-RGB192-','face92-reciprocal-RGB240-');assert base.count('motion40.FirstTarget,192,24,motion40.Snapshot')==1;base=base.replace('motion40.FirstTarget,192,24,motion40.Snapshot','motion40.FirstTarget,240,24,motion40.Snapshot').replace('["plannedSourceFrames"]=192','["plannedSourceFrames"]=240');assert 'EvaluateForm115'not in base and 'BoundRun115'not in base
 (G/'capture/RUN.cs.txt').write_text(base,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/motion92.dll')
 for mode in ['final','post/final']:
  t=(H/'face92/gpu'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face92\\gpu','resume-20261111\\face92\\motion240');(G/mode/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'92.dll'))
 (G/'console/ARGS.json').write_text((H/'face92/gpu/console/ARGS.json').read_text());d={'externalCSharp9Compiled':True,'targetFrames':240,'simulationSeconds':4,'sameValidatedReciprocalInput':True,'existing120SecondDeadline':True,'sameSource92CPUBuilderAndShader91':True,'actualGPUExecuted':False};(G/'CPU_PREPARED92.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
