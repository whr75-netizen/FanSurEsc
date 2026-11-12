"""One-frame source-readability probe before collecting the later motion poses."""
from pathlib import Path
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face96/probe1'
def main():
 for d in ['build','capture','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()
 s=(H/'face96/geometry64/capture/RUN.cs.txt').read_text().replace('face96\\geometry64','face96\\probe1').replace('face96-halo-geometry-','face96-halo-probe1-')
 old='if(ordinal77!=38&&ordinal77!=46&&ordinal77!=47)return;';assert s.count(old)==1;s=s.replace(old,'if(ordinal77!=0&&ordinal77!=38&&ordinal77!=46&&ordinal77!=47)return;')
 assert s.count('motion40.FirstTarget,64,24,motion40.Snapshot')==1;s=s.replace('motion40.FirstTarget,64,24,motion40.Snapshot','motion40.FirstTarget,1,1,motion40.Snapshot').replace('["plannedSourceFrames"]=64','["plannedSourceFrames"]=1')
 p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,G/'build/probe96.dll')
 for d in ['final','post/final']:
  s=(H/'face96/geometry64'/d/'RUN.cs.txt').read_text().replace('face96\\geometry64','face96\\probe1');p=G/d/'RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,G/'build'/(d.replace('/','-')+'96.dll'))
 (G/'console/ARGS.json').write_bytes((H/'face96/geometry64/console/ARGS.json').read_bytes());print('96 one-frame probe compiled; no Unity/GPU execution')
if __name__=='__main__':main()
