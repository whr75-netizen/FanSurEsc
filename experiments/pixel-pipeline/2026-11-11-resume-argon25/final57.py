"""Small post-capture state + Console read; no redraw, serialization, or cleanup."""
from pathlib import Path
import json,sys,contextlib,io
import relay33
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face57';p=G/'final';p.mkdir(exist_ok=True)
assert not(p/'REQUEST.json').exists()
source=(G/'capture/RUN.cs.txt').read_text().split('// Prepared helper only. No normal Exit or Play occurs in this prefix.')[0]
# Reuse the proven shared helper prefix, excluding the capture command.
original=(H/'face49/capture/RUN.cs.txt').read_text();mark='// Prepared helper only'
assert mark in original;source=original[:original.index(mark)]
code=source+(H/'ReadFinal57.cs.txt').read_text();(p/'RUN.cs.txt').write_text(code,encoding='utf-8',newline='\n')
compile_unity_language(p/'RUN.cs.txt',G/'build/final57.dll')
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G;relay33.TITLE_OVERRIDE='Read final Edit/input/resource/scene metadata only; no render, serialization, cleanup or save'
sys.argv=[sys.argv[0],'final']
with contextlib.redirect_stdout(io.StringIO()):relay33.main()
r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r['content']if x.get('type')=='text');assert c['success'];assert(p/'STATE.json').exists()
print((p/'STATE.json').read_text())
q=G/'console';q.mkdir(exist_ok=True);assert not(q/'REQUEST.json').exists();(q/'ARGS.json').write_text(json.dumps({'maxEntries':20,'includeStackTrace':True,'logTypes':'Error,Exception'}),encoding='utf-8');sys.argv=[sys.argv[0],'console']
with contextlib.redirect_stdout(io.StringIO()):relay33.main()
r=json.loads((q/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r['content']if x.get('type')=='text');assert c['success'];print(json.dumps({'console':c.get('data')}))
