from pathlib import Path
import json,hashlib,shutil,subprocess
H=Path(__file__).resolve().parent;P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');BASE='90b7fdab7981c0c32345fb76262fa61c56d5a781';REL='experiments/pixel-pipeline/2026-11-01-forward-eye102';D=P/REL
def git(*args):return subprocess.check_output(['git','-C',str(P),*args],encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip()
names=['aa_transition103.py','test_aa_transition103.py','inspect_aa_graph103.py','AA_TRANSITION_TEST103.json','AA_GRAPH103.json','snapshot_aa103.py']+[f'part{part}/{name}'for part in [3,6]for name in ['aa-transition-regions.png','aa-transition.npz','aa-edges-on-source.png']]
for name in names:
 dest=D/'source-regions103'/name;assert not dest.exists();shutil.copy2(H/name,dest)
manifest=D/'ARTIFACTS102.json';old=json.loads(manifest.read_text(encoding='utf-8'))
for f in old['files']:assert sha(D/f['path'])==f['SHA256']
old['files'] += [{'path':'source-regions103/'+name,'SHA256':sha(H/name),'bytes':(H/name).stat().st_size}for name in names]
manifest.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('103 rejected AA hypothesis preserved; no Assets or Unity changes')
