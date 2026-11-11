from pathlib import Path
import json,sys,contextlib,io
import relay33
H=Path(__file__).resolve().parent;G=H/'face54';p=G/'console';p.mkdir(parents=True,exist_ok=True)
assert not(p/'REQUEST.json').exists()
(p/'ARGS.json').write_text(json.dumps({'maxEntries':12,'includeStackTrace':True,'logTypes':'Error,Exception'}),encoding='utf-8')
relay33.G=G;sys.argv=[sys.argv[0],'console']
with contextlib.redirect_stdout(io.StringIO()):relay33.main()
r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'];print(json.dumps({'success':True,'count':c['data']['totalCount'],'headings':[x['message'].splitlines()[0]for x in c['data']['logs']]}))
