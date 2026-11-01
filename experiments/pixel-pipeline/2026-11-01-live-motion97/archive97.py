"""Selective completed experimental checkpoint; no user product files staged."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,zipfile
HERE=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');BASE='2672df7a54027dbb6f2699baf44151a7ab61c9d6';REL='experiments/pixel-pipeline/2026-11-01-live-motion97';DEST=REPO/REL;DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a,binary=False):return subprocess.check_output(['git','-C',str(REPO),*a],**({}if binary else{'text':True,'encoding':'utf-8'}))
def preserve():
    p=json.loads((REPO/'experiments/pixel-pipeline/2026-11-01-live-joint96/PRESERVATION96.json').read_text())['protected32'];assert all(sha(REPO/f)==h for f,h in p.items());return p
def copy(p,d):d.parent.mkdir(exist_ok=True,parents=True);assert not d.exists();shutil.copy2(p,d)
def archive():
    assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();protected=preserve();assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30 and not DEST.exists();s=json.loads((HERE/'SUMMARY97.json').read_text());assert s['EditorPlayExited']and s['nativeContentsDirectExact']==47 and s['latestPublicStateStillRestored']and not s['productIntegrated'];DEST.mkdir()
    for name in ['WholeEye96.compute','WholeEye96.cs','LiveSurface96.cs','LiveGraph96.cs','LiveFinal96.cs','NativeRetarget96.cs','GraphSources96.cs','FrozenComposition96.cs','MotionScope97.cs','prepare_motion97.py','prepare_cold97.py','prepare_lifetime97.py','RunFrozen96.cs','oracle_live96.py','validate96.py','review_motion97.py','checkpoint97.py','archive97.py','test_archive97.py','SUMMARY97.json','MOTION_REVIEW97.json','MOTION_GPU97.json','TURN_CPU_GPU97.json','ROTATION_FAILURES97.json','BACKING_FAILURE97.json','COLD_POLICIES97.json']:
        copy(HERE/name,DEST/name)
    copy(HERE/'INDEX97.html',DEST/'INDEX.html')
    for folder in ['motion','cold0','cold1','cold4','lifetime','status97']:
        for p in (HERE/folder).iterdir():
            if not p.is_file()or p.name.startswith('native-before-')or '_CONSOLE_'in p.name:continue
            if p.suffix in ['.py','.cs','.txt','.json']or p.name.endswith('.marker'):copy(p,DEST/folder/p.name)
    for p in (HERE/'review97').iterdir():
        if p.is_file():copy(p,DEST/'review97'/p.name)
    for p in (HERE/'oracle-turn97').iterdir():
        if p.is_file()and p.name in ['RESULT95-source-cache-turn97v2.json','ORACLE_INPUT96.json']:copy(p,DEST/'oracle-turn97'/p.name)
    copy(HERE.parent/'apply-capture66/analyse_capture68.py',DEST/'reader68.py')
    state=json.loads(sorted((HERE/'motion').glob('STATE97*'))[-1].read_text())
    with zipfile.ZipFile(DEST/'RAW97.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for e in state['sequencePackets']:
            p=Path(e['output']);assert(p/'RAW_COMPLETE76.marker').read_text()==sha(p/'RAW_MANIFEST.json')
            for f in p.iterdir():assert f.is_file();z.write(f,f'frame-{e["frame"]}/'+f.name)
    with zipfile.ZipFile(DEST/'OFFLINE_ORACLE97.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for p in (HERE/'oracle-turn97').rglob('*'):
            if p.is_file():z.write(p,p.relative_to(HERE/'oracle-turn97').as_posix())
    with zipfile.ZipFile(DEST/'GPU_COLD_LIFETIME97.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for folder in ['cold0','cold1','cold4','lifetime']:
            for p in (HERE/folder/'gpu-output').iterdir():
                if p.is_file():z.write(p,folder+'/'+p.name)
    (DEST/'.gitattributes').write_text('* -text\n');(DEST/'PRESERVATION97.json').write_text(json.dumps({'baselineCommit':BASE,'protected32':protected,'userModified30Preserved':True,'AssetsChanged':0,'productDefault':77,'push':False},indent=2)+'\n')
    files=[{'path':p.relative_to(DEST).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size}for p in sorted(DEST.rglob('*'))if p.is_file()];(DEST/'ARTIFACTS97.json').write_text(json.dumps({'files':files},indent=2)+'\n')
    doc=REPO/DOC;assert b'## Eye97 'not in doc.read_bytes()
    with doc.open('ab')as f:f.write((HERE/'HANDOFF_APPEND97.txt').read_bytes())
    print(json.dumps({'archive':str(DEST),'files':len(files)+1,'rawZipBytes':(DEST/'RAW97.zip').stat().st_size,'protected32Matched':True,'userModified30Preserved':True},indent=2))
def commit():
    assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();preserve();m=json.loads((DEST/'ARTIFACTS97.json').read_text())['files'];assert all(sha(DEST/x['path'])==x['SHA256']for x in m)
    git('add','--',REL,DOC);expected={REL+'/'+x['path']for x in m}|{REL+'/ARTIFACTS97.json',DOC};actual=set(git('diff','--cached','--name-only','-z').strip('\x00').split('\x00'));assert actual==expected
    for x in m:assert hashlib.sha256(git('show',':'+REL+'/'+x['path'],binary=True)).hexdigest()==x['SHA256']
    assert git('diff','--cached','--numstat','--',DOC).strip().split('\t')[1]=='0';git('diff','--cached','--check','--',DOC);print(git('commit','-m','Checkpoint live eye phase motion and expose rotation tie and backing failures'));assert not git('diff','--cached','--name-only').strip();preserve();assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30;r={'commit':git('rev-parse','HEAD').strip(),'files':len(actual),'AssetsChanged':0,'productDefault':77,'user30Preserved':True,'protected32Preserved':True,'push':False};(HERE/'COMMIT97.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':{'archive':archive,'commit':commit}[sys.argv[1]]()
