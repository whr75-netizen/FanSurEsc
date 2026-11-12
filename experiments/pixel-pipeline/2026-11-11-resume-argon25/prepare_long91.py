"""Repeat the defined192-frame RGB motion with the proven current-colour fix."""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face91/motion192'
def main():
 for d in ['capture','build','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final'])
 s=(H/'face91/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face91\\capture','resume-20261111\\face91\\motion192\\capture').replace('face91-current-independent-history-','face91-current-RGB192-').replace('motion40.FirstTarget,64,16,motion40.Snapshot','motion40.FirstTarget,192,24,motion40.Snapshot').replace('["plannedSourceFrames"]=64','["plannedSourceFrames"]=192');(G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/rgb192.dll')
 for mode in ['final','post/final']:
  t=(H/'face91'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face91','resume-20261111\\face91\\motion192');(G/mode/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'91.dll'))
 (G/'console/ARGS.json').write_text((H/'face91/console/ARGS.json').read_text());d={'externalCSharp9Compiled':True,'targetFrames':192,'simulationSeconds':3.2,'sameDefinedMotionAs89Failed192':True,'currentColourIndependentFromHistory':True,'historyAndCurrentOcclusionUnchanged':True,'sameSourceValueTableAndOriginalHuePalette':True,'same120SecondDeadline':True,'newShaderImportOrCompute':False,'perFrameReadbackBytes':237952,'GPUExecuted':False};(G/'CPU_PREPARED_LONG91.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
