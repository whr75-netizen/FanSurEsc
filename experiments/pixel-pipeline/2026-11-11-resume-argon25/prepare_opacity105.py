"""Use the existing103 runner/passes for one same-edge continuity regression."""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face105'

def main():
 old=H/'face103/rows64C';root=G/'edge64';(G/'build').mkdir(parents=True,exist_ok=True)
 for n in['capture','preflight/final','post/final']:(root/n).mkdir(parents=True,exist_ok=True)
 assert not(root/'capture/REQUEST.json').exists();s=(old/'capture/RUN.cs.txt').read_text();assert hashlib.sha256(s.encode()).hexdigest()==json.loads((old/'capture/REQUEST.json').read_text())['codeSHA256'];s=s.replace(str(old),str(root)).replace('face103-rows-','face105-same-edge-')
 a=(H/'CurveOpacity103.cs').read_text().split('namespace LineGeometry97',1)[1];b=(H/'CurveOpacity105.cs').read_text().split('namespace LineGeometry97',1)[1];assert s.count('namespace LineGeometry97'+a)==1;s=s.replace('namespace LineGeometry97'+a,'namespace LineGeometry97'+b)
 marker='FrameInfo40["sourceColourProducer103"]=';assert s.count(marker)==1;s=s.replace(marker,'FrameInfo40["opacity105"]="Only same authored edge quad halves share a split depth/alpha path. General opacity, source feature semantics and continuous world remain incomplete; product77 default unchanged";'+marker)
 assert s.count('cmd.RequestAsyncReadback(readbackPack93.rt')==1 and'EvaluateForm115'not in s and'BoundRun115'not in s
 p=root/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/edge64.dll')
 for mode in['preflight','post']:
  s=(old/mode/'final/RUN.cs.txt').read_text().replace(str(old/mode),str(root/mode))
  if mode=='post':s=s.replace(str(old/'capture/INPUT_BEFORE.json'),str(root/'capture/INPUT_BEFORE.json'))
  p=root/mode/'final/RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,G/'build'/(mode+'.dll'))
 print('105 entire external runner CPU compiled; no Unity call/import/GPU executed')

if __name__=='__main__':main()
