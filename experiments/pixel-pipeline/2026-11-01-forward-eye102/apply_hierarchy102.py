from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');a=json.loads((H/'ASSET102.json').read_text());patch=json.loads((H/'HIERARCHY_PATCH102.json').read_text());dest=P/a['newAsset']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(dest)==patch['beforeSHA256']==a['shaderSHA']
assert all(sha(P/r['path'])==r['sha']for r in a['protected32'])
with dest.open('wb')as f:f.write((H/'ForwardEye102.compute').read_bytes())
assert sha(dest)==patch['afterSHA256'];patch['assetApplied']=True;(H/'HIERARCHY_APPLIED102.json').write_text(json.dumps(patch,indent=2),encoding='utf-8');print(json.dumps(patch))
