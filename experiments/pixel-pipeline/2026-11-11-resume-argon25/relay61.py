"""One source frame, explicit bounded width calibration, no retry or product switch."""
from pathlib import Path
import hashlib,json,sys
import relay33
H=Path(__file__).resolve().parent;G=H/'face61';p=G/'capture';assert not(p/'REQUEST.json').exists()and not(p/'STARTED.json').exists()
d=json.loads((H/'face60/capture/COMPLETE.json').read_text());assert d['Edit']and d['ownedResourcesReleased']and d['restorationChecksPass']and not d['errors']and d['pendingOwners']==0
prep=json.loads((G/'CPU_PREPARED61.json').read_text());assert prep['fullExternalCSharp9Compiled']and prep['additionalShaders']==prep['additionalBuffers']==0 and prep['scales']==[0,1,8,32]
assert hashlib.sha256((p/'RUN.cs.txt').read_bytes()).hexdigest()==prep['captureSHA256']
R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');assert all(hashlib.sha256((R/'Assets/EUnityValidation01/SourceBoundary60'/name).read_bytes()).digest()==hashlib.sha256((H/'face60/shaders'/name).read_bytes()).digest()for name in['SourceNativeHull60.shader','SourceNativeHull60.compute'])
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G;relay33.TITLE_OVERRIDE='One evaluated frame, four bounded original-material width calibrations 0/1/8/32, same actual native/world inputs; no shader import, material edit or product adoption; normal acknowledged restoration'
sys.argv=[sys.argv[0],'capture'];relay33.main();r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'],c.get('error');print(json.dumps({'commandAccepted':True,'markersRequired':True}))
