from pathlib import Path
import hashlib,json,sys
import relay33
H=Path(__file__).resolve().parent;G=H/'face62';mode=sys.argv[1];assert mode in['import','capture'];p=G/mode;assert not(p/'REQUEST.json').exists()and not(p/'STARTED.json').exists()
d=json.loads((H/'face61/capture/COMPLETE.json').read_text());assert d['restorationChecksPass']and d['ownedResourcesReleased']and not d['errors']and d['pendingOwners']==0
prep=json.loads((G/'CPU_PREPARED62.json').read_text());assert prep['fullExternalCSharp9Compiled']and prep['computeLoops']==prep['newStructuredBuffers']==0
if mode=='capture':
 assert(G/'import/COMPLETE.json').exists()and hashlib.sha256((p/'RUN.cs.txt').read_bytes()).hexdigest()==prep['captureSHA256']
 target=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\SourceBoundary60\SourceNativeHull60.compute');assert hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256((G/'shaders/SourceNativeHull60.compute').read_bytes()).digest()
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G;relay33.TITLE_OVERRIDE={'import':'Update only the owned SourceBoundary60 compute after exact source/GUID backup; same8x8 ABI, no C# import, Play, save or dispatch','capture':'One evaluated frame validating face-outline parent layer below confirmed visible eye children; unchanged world/hair gates and same four bounded width controls; per-case final owner readback and normal restoration'}[mode]
sys.argv=[sys.argv[0],mode];relay33.main();r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'],c.get('error');print(json.dumps({'mode':mode,'commandAccepted':True,'markersRequired':True}))
