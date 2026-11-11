"""Read actual settings against capture receipt.json; do not rewrite original false evidence."""
from pathlib import Path
import json,sys,contextlib,io
import relay33
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face57/input-check';p=G/'final';p.mkdir(parents=True,exist_ok=True)
assert not(p/'REQUEST.json').exists()
original=(H/'face49/capture/RUN.cs.txt').read_text();code=original[:original.index('// Prepared helper only')]+(H/'CheckInput57.cs.txt').read_text();(p/'RUN.cs.txt').write_text(code,encoding='utf-8',newline='\n');compile_unity_language(p/'RUN.cs.txt',H/'face57/build/inputcheck57.dll')
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G;relay33.TITLE_OVERRIDE='Read InputSettings against the json member of its existing receipt; no assignment, render, save or cleanup';sys.argv=[sys.argv[0],'final']
with contextlib.redirect_stdout(io.StringIO()):relay33.main()
r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r['content']if x.get('type')=='text');assert c['success'];print((G/'STATE.json').read_text())
