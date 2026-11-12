"""192 normal reciprocal movement frames; bound travel using actual speed10.

Four input frames out, four in the opposite direction,24 idle. Change the
direction each32 frames. No position/camera/speed/setting object manipulation.
"""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face91/bounded192'
def main():
 for d in ['capture','build','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final'])
 s=(H/'face91/motion192/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face91\\motion192\\capture','resume-20261111\\face91\\bounded192\\capture').replace('face91-current-RGB192-','face91-reciprocal-RGB192-')
 old='void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(Time.frameCount<FirstTarget-1)return;int index=Time.frameCount-FirstTarget+1;bool walk=index>=96||index%16==0;int dir=index<96?direction:(direction+2*(1+(index-96)/32))%8;InputSystem.QueueStateEvent(ownedKeyboard,new KeyboardState(walk?Keys(D[dir]):new Key[0]));}'
 new='void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(Time.frameCount<FirstTarget-1)return;int index=Time.frameCount-FirstTarget+1,part=index%32;bool walk=part<8;int dir=(direction+2*(index/32%4)+(part>=4?4:0))%8;InputSystem.QueueStateEvent(ownedKeyboard,new KeyboardState(walk?Keys(D[dir]):new Key[0]));}';assert s.count(old)==1;s=s.replace(old,new)
 old='int dir89=index<96?direction:(direction+2*(1+(index-96)/32))%8;var expected=index>=96||index%16==0?D[dir89]:Vector2.zero;';new='int part89=index%32;int dir89=(direction+2*(index/32%4)+(part89>=4?4:0))%8;var expected=part89<8?D[dir89]:Vector2.zero;';assert s.count(old)==1;s=s.replace(old,new).replace('["stage"]=index>=96?"turn-walk":index%16==0?"walk-pulse":"idle"','["stage"]=part89<4?"walk-out":part89<8?"walk-back":"idle"')
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/bounded192.dll')
 for mode in ['final','post/final']:
  t=(H/'face91/motion192'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face91\\motion192','resume-20261111\\face91\\bounded192');(G/mode/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'91.dll'))
 (G/'console/ARGS.json').write_text((H/'face91/motion192/console/ARGS.json').read_text());d={'externalCSharp9Compiled':True,'targetFrames':192,'simulationSeconds':3.2,'observedPriorSpeed':10,'priorHeld32TravelMetres':32*10/60,'newFourFrameOutTravelMetres':4*10/60,'normalOppositeInputReturnsWithoutPositionWrite':True,'sourceShaderTableHistoryAndVisibilityUnchanged':True,'same120sDeadline':True,'newGPUExecution':False};(G/'CPU_PREPARED_BOUNDED91.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
