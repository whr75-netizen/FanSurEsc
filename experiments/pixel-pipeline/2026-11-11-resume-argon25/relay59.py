"""One native outline-source capture after exact importer colour-space correction."""
from pathlib import Path
import hashlib,json,sys
import relay33
H=Path(__file__).resolve().parent;G=H/'face59';p=G/'capture';assert not(p/'REQUEST.json').exists()and not(p/'STARTED.json').exists()
d=json.loads((H/'face58/capture/FAILED.json').read_text());assert d['Edit']and d['ownedResourcesReleased']and d['restorationChecksPass']and not d['errors']and d['pendingOwners']==0
prepared=json.loads((G/'CPU_PREPARED59.json').read_text());assert prepared['fullExternalCSharp9Compiled']and prepared['newDispatches']==prepared['newShaders']==0
assert hashlib.sha256((p/'RUN.cs.txt').read_bytes()).hexdigest()==prepared['captureSHA256']
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G;relay33.TITLE_OVERRIDE='One native MToon outline ON/OFF capture with exact installed Linear-to-sRGB source-property validation; bounded reads and normal restoration, no new shader or dispatch'
sys.argv=[sys.argv[0],'capture'];relay33.main()
r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'],c.get('error');print(json.dumps({'commandAccepted':True,'asyncMarkersRequired':True}))
