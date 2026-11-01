"""Create-only selective experiment archive and append existing handoff."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,zipfile
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
REL='experiments/pixel-pipeline/2026-11-01-graph-context94'; DEST=REPO/REL
DOC='docs/ai/PIXEL_ALBEDO_20261030.md'; BASE='cd0b2dcbc816eabd4bb4c6884c311e7caab5670f'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,binary=False):return subprocess.check_output(['git','-C',str(REPO),*args],**({}if binary else{'text':True,'encoding':'utf-8'}))
def preservation():
    p=json.loads((REPO/'experiments/pixel-pipeline/2026-11-01-visibility-backing91-93/PRESERVATION91.json').read_text())
    assert all(sha(REPO/f)==h for f,h in p['protected32'].items()),'User/protected source changed; inspect, do not overwrite'
    assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30
    return p['protected32']

def archive():
    assert git('rev-parse','HEAD').strip()==BASE
    assert not git('diff','--cached','--name-only').strip()
    protected=preservation(); assert not DEST.exists(),'Inspect previous outcome; do not merge automatically'
    summary=json.loads((HERE/'SUMMARY94.json').read_text()); assert summary['nativeExact']==47 and not summary['publicStateDifferences']and not summary['newConsoleErrors']
    DEST.mkdir()
    for p in HERE.iterdir():
        if p.is_file()and p.suffix in ['.py','.json','.png','.html']and p.name not in ['COMMIT94.json','STAGED94.json']:
            shutil.copy2(p,DEST/p.name)
    shutil.copy2(HERE.parent/'apply-capture66/analyse_capture68.py',DEST/'reader68.py')
    shutil.copy2(HERE.parent/'visibility-backing91/GraphSources93.cs',DEST/'GraphSources93.cs')
    shutil.copy2(HERE/'MotionScope94.cs',DEST/'MotionScope94.cs')
    for p in (HERE/'capture').iterdir():
        if not p.is_file()or p.name.startswith('native-before-')or '_CONSOLE_'in p.name:continue
        if p.suffix in ['.py','.cs','.json']or p.name.startswith('RUN_'):
            target=DEST/'capture'/p.name; target.parent.mkdir(exist_ok=True); shutil.copy2(p,target)
    with zipfile.ZipFile(DEST/'RAW94.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for entry in summary['packets']:
            q=Path(entry['output']); assert (q/'RAW_COMPLETE76.marker').read_text()==sha(q/'RAW_MANIFEST.json')
            for p in q.iterdir():
                assert p.is_file()
                z.write(p,'frame-'+str(entry['frame'])+'/'+p.name)
    (DEST/'.gitattributes').write_text('* -text\n')
    (DEST/'PRESERVATION94.json').write_text(json.dumps({'baselineCommit':BASE,'protected32':protected,'userTrackedModified30Preserved':True,'AssetsChanges':0,'noProductIntegration':True},indent=2)+'\n')
    files=[{'path':p.relative_to(DEST).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size}for p in sorted(DEST.rglob('*'))if p.is_file()]
    (DEST/'ARTIFACTS94.json').write_text(json.dumps({'files':files},indent=2)+'\n')
    doc=REPO/DOC; before=doc.read_bytes(); assert b'## Eye94 'not in before
    (HERE/'HANDOFF_BEFORE94.sha256').write_text(hashlib.sha256(before).hexdigest()+'\n')
    with doc.open('ab')as f:f.write((HERE/'HANDOFF_APPEND94.txt').read_bytes())
    print(json.dumps({'archive':str(DEST),'files':len(files)+1,'rawZipBytes':(DEST/'RAW94.zip').stat().st_size,'protected32Matched':True,'AssetsChanges':0},indent=2))

def commit():
    assert git('rev-parse','HEAD').strip()==BASE
    assert not git('diff','--cached','--name-only').strip()
    p=json.loads((DEST/'PRESERVATION94.json').read_text())
    assert all(sha(REPO/f)==h for f,h in p['protected32'].items())
    manifest=json.loads((DEST/'ARTIFACTS94.json').read_text())['files']
    for r in manifest:assert sha(DEST/r['path'])==r['SHA256']
    git('add','--',REL,DOC)
    expected={REL+'/'+r['path']for r in manifest}|{REL+'/ARTIFACTS94.json',DOC}
    staged=set(git('diff','--cached','--name-only','-z').strip('\x00').split('\x00')); assert staged==expected
    for r in manifest:assert hashlib.sha256(git('show',':'+REL+'/'+r['path'],binary=True)).hexdigest()==r['SHA256']
    assert git('diff','--cached','--numstat','--',DOC).strip().split('\t')[1]=='0'
    git('diff','--cached','--check','--',DOC)
    staged_report={'stagedFiles':len(staged),'archiveFiles':len(expected)-1,'AssetsStaged':0,'userModified30NotStaged':True,'protected32Matched':True,'archiveHashesMatched':True}
    (HERE/'STAGED94.json').write_text(json.dumps(staged_report,indent=2)+'\n')
    print(git('commit','-m','Verify RenderGraph source lighting and backing with frozen ROI packets'))
    assert not git('diff','--cached','--name-only').strip()
    assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30
    assert all(sha(REPO/f)==h for f,h in p['protected32'].items())
    out={'commit':git('rev-parse','HEAD').strip(),'archive':REL,'files':len(staged),'product':77,'userModified30Preserved':True,'protected32Matched':True,'push':False}
    (HERE/'COMMIT94.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))

if __name__=='__main__':
    {'archive':archive,'commit':commit}[sys.argv[1]]()
