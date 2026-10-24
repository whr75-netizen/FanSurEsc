"""Release only this diagnostic's consumed reproducible candidate scratch.
Original pose tables, source captures and covered-sample GPU probes are kept.
"""
from pathlib import Path
import json, hashlib
R=Path(__file__).parent.resolve()
audit=R/'SCRATCH_RELEASE586.json'
history=json.loads(audit.read_text()) if audit.exists() else []
for token in ['AreaGrid32_586','AreaGrid64_586','AreaGrid128_586','AreaGrid128Shift_586']:
    root=(R/token).resolve()
    if not (root/'RESULT.json').exists():continue
    if any(j['token']==token for j in history):continue
    assert root.parent==R and root.is_dir()
    job=json.loads((root/'JOB.json').read_text())
    result=json.loads((root/'RESULT.json').read_text())
    assert result['token']==token and len(result['records'])==9
    files=[Path(q['file']) for q in job['poses']]
    files += [Path(g[k]) for g in job['groups'] for k in ['input','output']]
    records=[]
    for file in files:
        file=file.resolve()
        assert file.parent==root and file.suffix in ['.npz','.bin']
        assert file.name.startswith(('POSE_','INPUT','OUTPUT'))
        records.append(dict(path=str(file),bytes=file.stat().st_size,
            sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    entry=dict(token=token,releasedBytes=sum(q['bytes'] for q in records),
        reason='Own consumed, reproducible GPU-query scratch only; original inputs and result summaries retained.',files=records)
    history.append(entry)
    audit.write_text(json.dumps(history,indent=2)+'\n')
    for file in files:file.unlink()
    print(token,entry['releasedBytes'])
