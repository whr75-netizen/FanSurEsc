"""Prepare outside-Assets observer; does not call Unity."""
from pathlib import Path
import re,json,hashlib
HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'eye-observer72'
OLD=HERE.parent/'apply-capture66'
def bundle(paths,target):
 uses=[];b=[]
 for p in paths:
  s=p.read_text(encoding='utf-8-sig')
  for u in re.findall(r'(?m)^using [^;\n]+;',s):
   if u not in uses:uses.append(u)
  b.append(re.sub(r'(?m)^using [^;\n]+;\r?\n?','',s))
 target.write_text('\n'.join(uses)+'\n'+'\n'.join(b),encoding='utf-8')
def main():
 OUT.mkdir(exist_ok=False)
 relay=(OLD/'relay66.py').read_text(encoding='utf-8');start=relay.index('assert mode in (');end=relay.index('\n',start)
 relay=relay[:start]+"assert mode in ('Read72','Compile72','Capture72','Post72')"+relay[end:]
 (OUT/'relay72.py').write_text(relay,encoding='utf-8')
 s=(OLD/'Read66.cs').read_text(encoding='utf-8-sig').replace('apply-capture66\\CURRENT66.json','eye-observer72\\CURRENT72.json')
 (OUT/'Read72.cs').write_text(s,encoding='utf-8');bundle([OLD/'Json58Linear66.cs',OUT/'Read72.cs'],OUT/'RUN_Read72.cs.txt')
 # Retain an exact pre-execution disk baseline and no full unrelated Git scan.
 repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');old=json.loads((OLD/'RESUME68_DISK.json').read_text(encoding='utf-8'))
 baseline={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in old['files']}
 (OUT/'DISK_BEFORE72.json').write_text(json.dumps({'files':baseline},indent=2)+'\n')
 print('Prepared read-only current-state command at',OUT)
if __name__=='__main__':main()
