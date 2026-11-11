"""Read errors after completed/fully restored capture56; no renderer commands."""
from pathlib import Path
import json,sys,contextlib,io
import relay33
H=Path(__file__).resolve().parent;G=H/'face56';p=G/'console';p.mkdir(exist_ok=True)
assert not(p/'REQUEST.json').exists()
(p/'ARGS.json').write_text(json.dumps({'maxEntries':20,'includeStackTrace':True,'logTypes':'Error,Exception'}),encoding='utf-8')
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G;sys.argv=[sys.argv[0],'console']
with contextlib.redirect_stdout(io.StringIO()):relay33.main()
r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r['content']if x.get('type')=='text');assert c['success'];print(json.dumps(c.get('data')))
