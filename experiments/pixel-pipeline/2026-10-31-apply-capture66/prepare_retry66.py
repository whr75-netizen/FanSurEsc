"""Independent sourceId/state folder after first observer finished. No Unity call."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
state=json.loads((HERE/'CAPTURE_STATE66.json').read_text())
assert state['stage']=='finished' and state['PlayExited'] and state['observerRemoved']
assert state['optionsRestored'] and state['pipelineRestored'] and state['timeRestored'] and state['globalRestoreErrors']==[]
assert len(state.get('planes',[]))==0 and 'Normal-ready timeout' in state['error']
post=json.loads((HERE/'POST_CAPTURE66.json').read_text())
assert not post['playing'] and not post['paused'] and not post['sceneDirty'] and not post['runInBackground']
assert all(e.get('equal') is True for e in post['nativeComparisons'])
folder=HERE/'retry-background';folder.mkdir(exist_ok=False)
(folder/'GLOBAL_NAMES66.json').write_bytes((HERE/'GLOBAL_NAMES66.json').read_bytes())
s=(HERE/'Capture66.cs').read_text(encoding='utf-8')
s=s.replace('apply-capture66";', 'apply-capture66\\retry-background";')
s=s.replace('double start;int exitTicks', 'double start,lastTelemetry;bool oldBackground;int exitTicks')
s=s.replace('domain=AppDomain.CurrentDomain.Id;oldOptions=', 'domain=AppDomain.CurrentDomain.Id;oldBackground=Application.runInBackground;oldOptions=')
s=s.replace('EditorSettings.enterPlayModeOptionsEnabled=true;', 'Application.runInBackground=true;report["backgroundBefore"]=oldBackground;report["temporaryRunInBackground"]=true;EditorSettings.enterPlayModeOptionsEnabled=true;')
s=s.replace('if(started){EditorSettings.enterPlayModeOptionsEnabled=oldOptions;', 'if(started){Application.runInBackground=oldBackground;EditorSettings.enterPlayModeOptionsEnabled=oldOptions;')
s=s.replace('report["PlayExited"]=!EditorApplication.isPlaying', 'report["backgroundRestored"]=Application.runInBackground==oldBackground;report["PlayExited"]=!EditorApplication.isPlaying')
needle='   if(!n||!n.ready||!gp||!gp.connected||n.host.main.renderedSerial335<=0)return;'
replacement='''   if(EditorApplication.timeSinceStartup-lastTelemetry>.5){lastTelemetry=EditorApplication.timeSinceStartup;File.AppendAllText(Path.Combine(Root,"WAIT_TRACE.jsonl"),new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["frame"]=Time.frameCount,["paused"]=EditorApplication.isPaused,["timeScale"]=Time.timeScale,["background"]=Application.runInBackground,["hasNative"]=n!=null,["nativeReady"]=n&&n.ready,["hasGameplay"]=gp!=null,["connected"]=gp&&gp.connected,["gameplayFailure"]=gp?gp.failure:null,["mainSerial"]=n&&n.host&&n.host.main?n.host.main.renderedSerial335:0}.ToString()+"\\n");}
   if(EditorApplication.isPaused)throw new InvalidOperationException("Runtime paused before observer ready; do not override unidentified pause");
   if(!n||!n.ready||!gp||!gp.connected||n.host.main.renderedSerial335<=0)return;'''
assert s.count(needle)==1
s=s.replace(needle,replacement)
(HERE/'CaptureRetry66.cs').write_text(s,encoding='utf-8')
print('Prepared one separate background-enabled attempt; old outcome preserved')
