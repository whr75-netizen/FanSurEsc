"""Freeze only existing 43/47 inputs. No Unity or repository writes."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parent
W=R.parent
P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game')
S=P/'experiments/pixel-pipeline/2026-10-30-continuous47-counts'
J=W/'author33/feature34/eye-cache42/joint-placement43'
inputs={
 'fixtures/frames.json':S/'fixtures/frames.json',
 'fixtures/replay-inputs.npz':S/'fixtures/replay-inputs.npz',
 'fixtures/template43.json':J/'CELL_AND_COLOUR_PROVENANCE.json',
 'fixtures/expected47.json':S/'archive/analysis/PACKET_REPLAY_AND_ALLOCATOR.json',
 'lib/eye_cache42.py':S/'archive/eye_cache42.py',
 'lib/counts47.py':S/'archive/analyse_counts.py',
 'lib/joint43.py':J/'joint43.py',
}
for f in range(96,102):inputs[f'fixtures/actual-{f}.png']=W/f'continuous47-counts/analysis/frame{f}-actual.png'
records=[]
for name,src in inputs.items():
 dst=R/name;dst.parent.mkdir(parents=True,exist_ok=True)
 data=src.read_bytes()
 if dst.exists() and dst.read_bytes()!=data:raise RuntimeError('Refuse to change frozen input '+name)
 dst.write_bytes(data)
 records.append(dict(file=name,source=str(src),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
product=json.loads((W/'continuous47-counts/FILES_BEFORE.json').read_text(encoding='utf-8-sig'))['files']
current={p:hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in product}
assert current==product,'Current tracked source differs; re-evaluate baseline before continuing'
out=dict(baselineCommits=['1835f10','6c31438'],inputs=records,productBaselineSHA256=current,
 sequenceId='counts47-087454994917423fa13c5fe72eceb7f4',scope='offline only / not product / not GPU')
(R/'INPUT_MANIFEST.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'frozenInputs':len(records),'productTrackedHashesUnchanged':len(product),'bytes':sum(r['bytes']for r in records)}))
