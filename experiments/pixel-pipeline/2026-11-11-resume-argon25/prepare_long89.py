"""192 consecutive actual RGB frames within the existing120s deadline.

96 pulse/idle frames, then96 normal held movement frames in three directions.
No teleport, source mesh replacement, timeout extension or settings replacement.
"""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face89/motion192'

def main():
 for d in ['build','capture','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final'])
 s=(H/'face89/fix2/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face89\\fix2\\capture','resume-20261111\\face89\\motion192\\capture').replace('face89-source-value-Q-','face89-source-value-RGB192-').replace('motion40.FirstTarget,6,1,motion40.Snapshot','motion40.FirstTarget,192,24,motion40.Snapshot').replace('["plannedSourceFrames"]=6','["plannedSourceFrames"]=192')
 old='void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(Time.frameCount<FirstTarget-1)return;bool walk=(Time.frameCount-FirstTarget+1)%16==0;InputSystem.QueueStateEvent(ownedKeyboard,new KeyboardState(walk?Keys(D[direction]):new Key[0]));}'
 new='void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(Time.frameCount<FirstTarget-1)return;int index=Time.frameCount-FirstTarget+1;bool walk=index>=96||index%16==0;int dir=index<96?direction:(direction+2*(1+(index-96)/32))%8;InputSystem.QueueStateEvent(ownedKeyboard,new KeyboardState(walk?Keys(D[dir]):new Key[0]));}';assert s.count(old)==1;s=s.replace(old,new)
 old='var expected=index%16==0?D[direction]:Vector2.zero;';new='int dir89=index<96?direction:(direction+2*(1+(index-96)/32))%8;var expected=index>=96||index%16==0?D[dir89]:Vector2.zero;';assert s.count(old)==1;s=s.replace(old,new).replace('["stage"]=index%16==0?"walk-pulse":"idle"','["stage"]=index>=96?"turn-walk":index%16==0?"walk-pulse":"idle"')
 old='["originalFormat"]=original.graphicsFormat.ToString(),';new=old+'["originalSRGB"]=UnityEngine.Experimental.Rendering.GraphicsFormatUtility.IsSRGBFormat(original.graphicsFormat),["originalTextureFormat"]=original is Texture2D t89?t89.format.ToString():"not-Texture2D",';assert s.count(old)==1;s=s.replace(old,new)
 assert 'SortedSet'not in s and 'EvaluateForm115'not in s and 'BoundRun115'not in s
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/rgb192.dll')
 for mode in ['final','post/final']:
  t=(H/'face89/fix2'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face89\\fix2','resume-20261111\\face89\\motion192');(G/mode/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'89.dll'))
 (G/'console/ARGS.json').write_text((H/'face89/fix2/console/ARGS.json').read_text());result={'externalCSharp9Compiled':True,'targetFrames':192,'simulationSeconds':3.2,'normalInput':'96 pulse/idle then96 held movement in3 bound directions; actual rotations must be measured, not assumed','existing120SecondDeadlineUnchanged':True,'budgetBasis':'observed120 Q frames57.36s file span;192 estimated92s plus about13s setup/drain, below120s; not a guaranteed completion time','newShaderOrCompute':False,'same89ShaderAndImmutableSourceTable':True,'perFrameAtlasBytes':237952,'maximumPendingSlots':6,'noRGBHistoryOrExpectedGPUUpload':True,'GPUExecuted':False};(G/'CPU_PREPARED_LONG89.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
