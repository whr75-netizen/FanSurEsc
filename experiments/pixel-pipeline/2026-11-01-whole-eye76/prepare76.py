"""Build bounded observation inputs outside Assets. Does not invoke Unity."""
from pathlib import Path
import sys, json, hashlib
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'eye-observer73'
sys.path.insert(0,str(HERE.parent/'boundary-input69'))
from prepare73 import bundle

def prepare_read():
    relay=(OLD/'relay73.py').read_text(encoding='utf-8')
    relay=relay.replace("('Read73','Compile73','Capture73','Post73')", "('Read76','Import76','Compile76','Capture76','Post76')")
    (HERE/'relay76.py').write_text(relay,encoding='utf-8')
    s=(OLD/'Read73.cs').read_text(encoding='utf-8').replace('eye-observer73\\CURRENT73.json','whole-eye76\\CURRENT76.json')
    s=s.replace('File.WriteAllText(', 'CreateOnly73.Text(')
    (HERE/'Read76.cs').write_text(s,encoding='utf-8')
    bundle([HERE.parent/'apply-capture66'/'Json58Linear66.cs',OLD/'CreateOnly73.cs',HERE/'Read76.cs'],HERE/'RUN_Read76.cs.txt')
    repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
    paths=json.loads((OLD/'DISK_BEFORE73.json').read_text())['files']
    (HERE/'DISK_BEFORE76.json').write_text(json.dumps({'files':{p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}},indent=2)+'\n')
    print('Prepared current-state read only; Unity not invoked')

if __name__=='__main__':prepare_read()
