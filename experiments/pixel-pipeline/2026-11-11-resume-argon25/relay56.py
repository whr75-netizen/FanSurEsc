"""One bounded normal-frame diagnostic. No shader import and no automatic retry."""
from pathlib import Path
import json,hashlib,sys
import relay33
H=Path(__file__).resolve().parent;G=H/'face56';p=G/'capture';p.mkdir(exist_ok=True)
assert not(p/'REQUEST.json').exists()and not(p/'STARTED.json').exists(),'Inspect actual outcome; do not repeat'
status=json.loads((H/'face55/reopened/STATE.json').read_text());assert status['Edit']and status['oldDiagnosticRTs']==status['oldDiagnosticMaterials']==status['oldCommandUpdateObservers']==0 and status['inputJSONExact']
prepared=json.loads((G/'CPU_PREPARED56.json').read_text());assert prepared['plannedSourceFrames']==1 and prepared['fullExternalCSharp9Compiled']and prepared['assertionGroups']==8
source=(p/'RUN.cs.txt').read_bytes();assert hashlib.sha256(source).hexdigest()==prepared['captureSHA256']
assert b'EvaluateForm115'not in source and b'BoundRun115'not in source
pid=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.PID=pid;relay33.G=G
relay33.TITLE_OVERRIDE='One normal Gameplay397 source frame using existing SourceDomain49 shader, corrected producer guard and acknowledged lifetime; no product activation or import'
sys.argv=[sys.argv[0],'capture'];relay33.main()
r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'],c.get('error');d=c.get('data',{});print(json.dumps({'success':c['success'],'executed':d.get('isExecutionSuccessful'),'logs':d.get('executionLogs'),'asyncOutcomeMustBeReadFromMarkers':True}))
