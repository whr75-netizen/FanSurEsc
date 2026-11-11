from pathlib import Path
import json,sys
import relay33
H=Path(__file__).resolve().parent;G=H/'face49/recovery';p=G/'owned-completion';p.mkdir(exist_ok=True)
assert not(p/'REQUEST.json').exists();(p/'RUN.cs.txt').write_bytes((H/'CompleteOwned49.cs.txt').read_bytes());relay33.G=G;sys.argv=[sys.argv[0],'owned-completion'];relay33.main();r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r['content']if x.get('type')=='text');assert c['success'],c.get('error')
