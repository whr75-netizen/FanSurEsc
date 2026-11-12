"""Public resource/input/Console checkpoint after62; no serialization or rendering."""
from pathlib import Path
import json,sys,contextlib,io
import relay33
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face62';p=G/'final';p.mkdir(exist_ok=True);assert not(p/'REQUEST.json').exists()
original=(H/'face49/capture/RUN.cs.txt').read_text();prefix=original[:original.index('// Prepared helper only')];source=(H/'ReadFinal57.cs.txt').read_text().replace('resume-20261111\\face57','resume-20261111\\face62');(p/'RUN.cs.txt').write_text(prefix+source,encoding='utf-8',newline='\n');compile_unity_language(p/'RUN.cs.txt',G/'build/final62.dll')
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G;relay33.TITLE_OVERRIDE='Read final Edit/input/resource/scene metadata only after62; no draw, dispatch, save or serialization';sys.argv=[sys.argv[0],'final']
with contextlib.redirect_stdout(io.StringIO()):relay33.main()
raw=json.loads((p/'REPLY.json').read_text())['result'];r=raw.get('structuredContent')or next(json.loads(x['text'])for x in raw['content']if x.get('type')=='text');assert r['success'];print((p/'STATE.json').read_text())
q=G/'console';q.mkdir(exist_ok=True);assert not(q/'REQUEST.json').exists();(q/'ARGS.json').write_text(json.dumps({'maxEntries':20,'includeStackTrace':True,'logTypes':'Error,Exception'}));sys.argv=[sys.argv[0],'console']
with contextlib.redirect_stdout(io.StringIO()):relay33.main()
raw=json.loads((q/'REPLY.json').read_text())['result'];r=raw.get('structuredContent')or next(json.loads(x['text'])for x in raw['content']if x.get('type')=='text');assert r['success'];print(json.dumps({'console':r['data']}))
