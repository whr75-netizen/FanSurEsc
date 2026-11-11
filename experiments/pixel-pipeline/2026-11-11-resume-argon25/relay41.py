from pathlib import Path
import sys,json,hashlib
import relay33
G=Path(__file__).resolve().parent/'face41';relay33.G=G/'world'if'--world'in sys.argv else G/'fix1'if sys.argv[1]=='import'and'--fix1'in sys.argv else G
assert sys.argv[1]in ['details','import','capture','final','console']
if sys.argv[1]=='capture':
 assert(G/'fix1/import/COMPLETE.json').exists()
 asset=relay33.PROJECT/'Assets/EUnityValidation01/SourceBoundary41/ContourFinal41.compute';assert hashlib.sha256(asset.read_bytes()).hexdigest()==hashlib.sha256((G/'shaders/ContourFinal41.compute').read_bytes()).hexdigest()
relay33.main()
r=json.loads((relay33.G/sys.argv[1]/'REPLY.json').read_text())['result'];c=r.get('structuredContent')
if not c:c=next(json.loads(x['text'])for x in r['content']if x.get('type')=='text')
assert c['success'],c.get('error')
