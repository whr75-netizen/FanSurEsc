from pathlib import Path
import json,sys,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parent;sys.path.insert(0,str(ROOT));import compile_cs_cpu as cc
(H/'post-output').mkdir(exist_ok=True)
s=(H/'ReadMetadataState24.command.cs.txt').read_text().replace('Root+@"\\metadata24\\decode-output"','Root+@"\\metadata24\\post-output"')
with(H/'POST_STATE24.command.cs.txt').open('x',encoding='utf-8',newline='\n')as f:f.write(s)
row=next(x for x in json.loads((ROOT/'CS_COMPILE.json').read_text())['compilations']if x['name']=='Stage1MonoReferences');refs=[Path(x[len('/reference:'):])for x in row['arguments']if x.startswith('/reference:')]
result=cc.compile_one('PostMetadataState24',[H/'POST_STATE24.command.cs.txt'],refs)
with(H/'POST_CPU24.json').open('x',encoding='utf-8')as f:json.dump(result,f,indent=2)
