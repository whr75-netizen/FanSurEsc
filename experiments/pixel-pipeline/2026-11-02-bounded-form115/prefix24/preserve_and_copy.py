"""Selective experiment snapshot only; no Unity/Assets or existing file writes."""
from pathlib import Path
import datetime,hashlib,json,subprocess

H=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-02-bounded-form115/prefix24'
DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True,encoding='utf-8').strip('\r\n')
def verify():
    baseline=json.loads((H.parent/'DISK_BOUND_BEFORE115.json').read_text(encoding='utf-8'))
    mismatches=[p for p,digest in baseline['files'].items()if sha(REPO/p)!=digest]
    assert not mismatches,mismatches
    status=git('status','--porcelain','--untracked-files=no')
    unchanged='\n'.join(l for l in status.splitlines()if l[3:]!=DOC)
    assert unchanged==baseline['modifiedStatus'].strip('\r\n'), 'Original user modified set changed'
    native=H.parent.parent/'gpu-form115'
    rows=json.loads((native/'NATIVE_BEFORE73.json').read_text(encoding='utf-8'))
    for r in rows:
        p=native/r['snapshot'];assert p.stat().st_size==r['bytes']and sha(p)==r['sha256'],r['snapshot']
    assert len(rows)==47 and sum(r['bytes']for r in rows)==13008941
    assert not(REPO/'Assets/EUnityValidation01/Direct24Prefix/Prefix24.compute').exists()
    case=json.loads((H/'CASE.json').read_text());assert not(H/'runs'/case['RunId']).exists()
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baselineHEAD':'6885223ee5567a1fb779ece12cbf6279964f0d27','protectedFiles':len(baseline['files']),'protectedMismatches':mismatches,'userModifiedCount':len(unchanged.splitlines()),'originalUserModifiedSetEqual':True,'nativeBackupFiles':47,'nativeBackupBytes':13008941,'nativeBackupHashesEqual':True,'AssetsImported':False,'GPUOrUnityCalls':0,'currentEditorNativeStateQueried':False}
def main():
    assert git('rev-parse','HEAD')=='6885223ee5567a1fb779ece12cbf6279964f0d27'
    assert not git('diff','--cached','--name-only'),'Existing staged changes'
    record=verify();(H/'PRESERVE_PREFIX24.json').write_text(json.dumps(record,indent=2)+'\n')
    allowed={'.cs','.py','.json','.compute','.meta','.txt'}
    files=sorted(p for p in H.iterdir()if p.is_file()and(p.suffix in allowed or p.name=='.gitattributes'))
    files+=sorted((H/'fixture').glob('*.bin'))
    # Compiler DLL/DXBC/build outputs stay outside the committed snapshot.
    assert not DEST.exists(),'Snapshot already exists; inspect outcome before retry'
    manifest=[]
    for source in files:
        rel=source.relative_to(H);target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb')as f:f.write(source.read_bytes())
        assert sha(target)==sha(source)
        manifest.append({'path':str(target.relative_to(REPO)).replace('\\','/'),'bytes':source.stat().st_size,'SHA256':sha(source)})
    verify()
    (H/'COPY_PREFIX24.json').write_text(json.dumps({'files':manifest,'filesCount':len(files),'preservation':record,'copyOnly':True,'staged':False},indent=2)+'\n')
    print(json.dumps({'files':len(files),'bytes':sum(x['bytes']for x in manifest),'preservation':record},indent=2))
if __name__=='__main__':main()
