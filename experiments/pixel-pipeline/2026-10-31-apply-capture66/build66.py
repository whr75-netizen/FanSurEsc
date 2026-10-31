from pathlib import Path
import re,sys
HERE=Path(__file__).resolve().parent
mode=sys.argv[1]
base=HERE.parent/'source-palette58'
if not base.exists():base=HERE.parent/'2026-10-31-source-palette58'
files=[base/'Json58.cs',HERE/(mode+'.cs')]
usings=[];body=[]
for p in files:
 s=p.read_text(encoding='utf-8-sig')
 for u in re.findall(r'(?m)^using [^;\n]+;',s):
  if u not in usings:usings.append(u)
 body.append(re.sub(r'(?m)^using [^;\n]+;\r?\n?','',s))
(HERE/('RUN_'+mode+'.cs.txt')).write_text('\n'.join(usings)+'\n'+'\n'.join(body),encoding='utf-8')
print('Prepared outside Assets:',mode)
