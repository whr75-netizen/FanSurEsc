from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;out=R/'logical-gate-only'
assert not out.exists(),'Archive already exists; do not overwrite'
out.mkdir();rows=[]
for p in sorted(R.iterdir()):
    if not p.is_file():continue
    q=out/p.name;q.write_bytes(p.read_bytes());rows.append(dict(path=q.name,sha256=hashlib.sha256(q.read_bytes()).hexdigest()))
(out/'ARCHIVE_MANIFEST.json').write_text(json.dumps(dict(status='initial logical winner gate only; NOT source-fragment occlusion validation',files=rows),indent=2),encoding='utf8')
print('Preserved',len(rows),'initial files')
