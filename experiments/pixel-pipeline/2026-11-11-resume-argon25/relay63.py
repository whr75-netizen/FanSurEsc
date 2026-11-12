from pathlib import Path
import json,hashlib,sys
import relay33
H=Path(__file__).resolve().parent;G=H/'face63';p=G/'capture';assert not(p/'REQUEST.json').exists()and not(p/'STARTED.json').exists()
f=json.loads((H/'face62/final/STATE.json').read_text());assert f['Edit']and f['inputJSONExact']and f['diagnosticRTs']==f['diagnosticMaterials']==f['commandUpdateObservers']==0
r=json.loads((H/'face62/analysis/ACTUAL_PARENT62.json').read_text());assert r['CPUExactCases']==4 and r['positiveFinalOwnerSamples']==59 and r['realChildColourPreserved']
d=json.loads((G/'CPU_PREPARED63.json').read_text());assert d['fullExternalCSharp9Compiled']and d['actualFramesPlanned']==6 and d['allSixOwnedTextureByteUpper']==100663296
assert hashlib.sha256((p/'RUN.cs.txt').read_bytes()).hexdigest()==d['captureSHA256'];R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');assert hashlib.sha256((R/'Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.compute').read_bytes()).digest()==hashlib.sha256((H/'face62/shaders/SourceNativeHull60.compute').read_bytes()).digest()
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G;relay33.TITLE_OVERRIDE='Six consecutive normal Gameplay input frames,3walk/3turn, private native-outline/eye-parent regression; bounded96MiB owned RT upper and262144-byte reads; no new shaders, InputSettings replacement, manual render or product adoption'
sys.argv=[sys.argv[0],'capture'];relay33.main();raw=json.loads((p/'REPLY.json').read_text())['result'];reply=raw.get('structuredContent')or next(json.loads(x['text'])for x in raw.get('content',[])if x.get('type')=='text');assert reply['success'],reply.get('error');print(json.dumps({'commandAccepted':True,'actualAsyncCompletionMarkersRequired':True}))
