from pathlib import Path
import sys,json,hashlib
import relay33
G=Path(__file__).resolve().parent/'face46';relay33.G=G
assert sys.argv[1]in ['import','capture','final','console']
if sys.argv[1]=='capture':
 assert(G/'import/COMPLETE.json').exists();asset=relay33.PROJECT/'Assets/EUnityValidation01/SourceBoundary46/VariableStroke46.shader';assert hashlib.sha256(asset.read_bytes()).hexdigest()==hashlib.sha256((G/'shaders/VariableStroke46.shader').read_bytes()).hexdigest()
relay33.main();r=json.loads((G/sys.argv[1]/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r['content']if x.get('type')=='text');assert c['success'],c.get('error')
