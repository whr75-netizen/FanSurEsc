"""Single source frame after proven first-pass observer correction; no retry."""
from pathlib import Path
import hashlib,json,sys
import relay33
H=Path(__file__).resolve().parent;G=H/'face57';p=G/'capture'
assert not(p/'REQUEST.json').exists()and not(p/'STARTED.json').exists(),'Inspect original outcome; no duplicate'
d=json.loads((H/'face56/capture/FAILED.json').read_text());assert d['Edit']and d['ownedResourcesReleased']and d['restorationChecksPass']and not d['errors']and d['pendingOwners']==0
prepared=json.loads((G/'CPU_PREPARED57.json').read_text());assert prepared['fullExternalCSharp9Compiled']and prepared['plannedSourceFrames']==1
assert hashlib.sha256((p/'RUN.cs.txt').read_bytes()).hexdigest()==prepared['captureSHA256']
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G
relay33.TITLE_OVERRIDE='One normal source frame at completed second main camera render; existing shaders, strict same-frame guards and acknowledged cleanup; no product activation or import'
sys.argv=[sys.argv[0],'capture'];relay33.main()
r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'],c.get('error');print(json.dumps({'commandAccepted':True,'asyncMarkersRequired':True}))
