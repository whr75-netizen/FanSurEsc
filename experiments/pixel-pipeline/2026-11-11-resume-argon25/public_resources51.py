from pathlib import Path
import json,sys
from prepare_final41 import compile_unity_language
import relay33
H=Path(__file__).resolve().parent;G=H/'face51/public';p=G/'final';p.mkdir(parents=True,exist_ok=True);assert not(p/'REQUEST.json').exists();source=(H/'PublicResources51.cs.txt').read_text();(p/'RUN.cs.txt').write_text(source,encoding='utf-8');b=H/'face51/build';b.mkdir(exist_ok=True);compile_unity_language(p/'RUN.cs.txt',b/'public51.dll');relay33.G=G;sys.argv=[sys.argv[0],'final'];relay33.main();r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'],c.get('error');print((G/'PUBLIC_RESOURCES51.txt').read_text())
