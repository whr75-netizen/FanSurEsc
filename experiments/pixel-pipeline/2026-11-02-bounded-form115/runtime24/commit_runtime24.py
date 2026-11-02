"""Selective source/evidence snapshot. No Unity, GPU, deletion or broad stage."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
H=Path(__file__).resolve().parent;B=H.parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-02-bounded-form115/runtime24'
DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
UTILITY='experiments/pixel-pipeline/2026-11-02-bounded-form115/prefix24/compile_hlsl_cpu.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True,encoding='utf-8').strip('\r\n')
def preserve():
    base=json.loads((B/'DISK_BOUND_BEFORE115.json').read_text())
    for name,digest in base['files'].items():assert sha(REPO/name)==digest,name
    status=git('status','--porcelain','--untracked-files=no')
    user='\n'.join(l for l in status.splitlines()if l[3:]not in [DOC,UTILITY] and not l[3:].startswith(str(DEST.relative_to(REPO)).replace('\\','/')+'/'))
    assert user==base['modifiedStatus'].strip('\r\n'),'Original user changes differ'
    native=B.parent/'gpu-form115';rows=json.loads((native/'NATIVE_BEFORE73.json').read_text())
    for row in rows:assert(native/row['snapshot']).stat().st_size==row['bytes']and sha(native/row['snapshot'])==row['sha256']
    assert len(rows)==47 and sum(r['bytes']for r in rows)==13008941
    assert not(REPO/'Assets/EUnityValidation01/Direct24Geometry/ForwardEye113_Geometry24.compute').exists()
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected35Equal':True,'userModified30Equal':True,'native47BackupEqual':True,'nativeBackupBytes':13008941,'currentEditorNativeStateQueried':False,'GPUOrUnityCalls':0}
def snapshot():
    assert git('rev-parse','HEAD')=='98fdf994fd02c6da479c5860e71966b4ab7ef346'
    assert not git('diff','--cached','--name-only'),'Other staged changes'
    assert not DEST.exists(),'Uncertain prior copy: inspect before retry'
    sys.path.insert(0,str(H));from regression_runtime24 import check_prepared
    checks=check_prepared();record=preserve();(H/'PRESERVE_RUNTIME24.json').write_text(json.dumps(record,indent=2)+'\n')
    suffixes={'.cs','.compute','.hlsl','.py','.json','.txt','.bin','.patch'}
    files=sorted(p for p in H.iterdir()if p.is_file()and(p.suffix in suffixes or p.name=='.gitattributes'))
    manifest=[]
    for source in files:
        target=DEST/source.name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb')as f:f.write(source.read_bytes())
        assert sha(target)==sha(source)
        manifest.append({'path':str(target.relative_to(REPO)).replace('\\','/'),'SHA256':sha(source),'bytes':source.stat().st_size})
    assert (REPO/UTILITY).read_bytes()==(B/'prefix24/compile_hlsl_cpu.py').read_bytes()
    record['afterCopy']=preserve()
    m={'files':manifest,'existingOwnedPaths':[DOC,UTILITY],'preservation':record,'checks':checks,'staged':False}
    (H/'COPY_RUNTIME24.json').write_text(json.dumps(m,indent=2)+'\n')
    print(json.dumps({'files':len(manifest),'bytes':sum(x['bytes']for x in manifest),'checks':checks,'preservation':record},indent=2))
def stage():
    m=json.loads((H/'COPY_RUNTIME24.json').read_text());paths=[x['path']for x in m['files']]+m['existingOwnedPaths']
    assert not git('diff','--cached','--name-only')
    for x in m['files']:assert sha(REPO/x['path'])==x['SHA256']
    subprocess.run(['git','-C',str(REPO),'add','--',*paths],check=True)
    assert set(git('diff','--cached','--name-only').splitlines())==set(paths)
    for x in m['files']:assert hashlib.sha256(subprocess.check_output(['git','-C',str(REPO),'show',':'+x['path']])).hexdigest()==x['SHA256']
    print(git('diff','--cached','--stat'));print('selected files',len(paths),'exact index hashes passed')
if __name__=='__main__':
    if len(sys.argv)==1:snapshot()
    elif sys.argv[1]=='stage':stage()
