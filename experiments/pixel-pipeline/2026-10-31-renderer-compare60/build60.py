from pathlib import Path
import re,sys
R=Path(__file__).resolve().parent;mode=sys.argv[1]
base=R.parent/'source-palette58'
if not base.exists():base=R.parent/'2026-10-31-source-palette58'
previous=R.parent/'renderer-family59'
if not previous.exists():previous=R.parent/'2026-10-31-renderer-family59'
files=[base/'Json58.cs',base/'State58.cs']
if mode.startswith('compare'):
 files += [base/'SourcePalette58.cs',base/'SourceJson58.cs',previous/'RendererFamily59.cs']
files += [R/(sys.argv[2]if len(sys.argv)>2 else mode+'.cs')]
using=[];body=[]
for p in files:
 s=p.read_text(encoding='utf-8-sig')
 for m in re.findall(r'(?m)^using [^;\n]+;',s):
  if m not in using:using.append(m)
 body.append(re.sub(r'(?m)^using [^;\n]+;\r?\n?','',s))
(R/('RUN_'+mode+'.cs.txt')).write_text('\n'.join(using)+'\n'+'\n'.join(body),encoding='utf8')
print('built',mode)
