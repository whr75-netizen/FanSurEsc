"""Explicit shader import or one source capture; never follows up automatically."""
from pathlib import Path
import json,hashlib,sys
import relay33
H=Path(__file__).resolve().parent;G=H/'face60';mode=sys.argv[1];assert mode in['import','capture'];p=G/mode;assert not(p/'REQUEST.json').exists()and not(p/'STARTED.json').exists()
d=json.loads((H/'face59/capture/FAILED.json').read_text());assert d['restorationChecksPass']and d['ownedResourcesReleased']and d['pendingOwners']==0 and not d['errors']
prep=json.loads((G/'CPU_PREPARED60.json').read_text());assert prep['fullExternalCSharp9Compiled']and prep['computeLoops']==prep['newBuffers']==0
if mode=='capture':assert(G/'import/COMPLETE.json').exists()and hashlib.sha256((p/'RUN.cs.txt').read_bytes()).hexdigest()==prep['captureSHA256']
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G;relay33.TITLE_OVERRIDE={'import':'Import two new owned native-outline shaders only; no C# import, Play, Refresh or save','capture':'One actual authored-width native hull versus forced one-cell curve, same frame and current source material; bounded completion and normal restoration; product77 unchanged'}[mode]
sys.argv=[sys.argv[0],mode];relay33.main();r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'],c.get('error');print(json.dumps({'mode':mode,'commandAccepted':True,'markersRequired':True}))
