from pathlib import Path
import hashlib,json,shutil,subprocess,sys,zipfile
HERE=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');BASE='ab51a469c6e476fda88a756172599512d5cdb524';REL='experiments/pixel-pipeline/2026-11-01-source-underlay98';DEST=REPO/REL;DOC='docs/ai/PIXEL_ALBEDO_20261030.md';ASSETS=['Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/'+n for n in ['WholeEye98.compute','CurrentNonEye98.shader']];ASSETS+=[n+'.meta'for n in ASSETS]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a,binary=False):return subprocess.check_output(['git','-C',str(REPO),*a],**({}if binary else{'text':True,'encoding':'utf-8'}))
def preserve():
    p=json.loads((HERE/'ASSET_CREATE98.json').read_text())['protected32'];assert all(sha(REPO/f)==h for f,h in p.items());return p
def copy(p,d):d.parent.mkdir(exist_ok=True,parents=True);assert not d.exists();shutil.copy2(p,d)
def archive():
    assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();protected=preserve();assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30 and not DEST.exists();s=json.loads((HERE/'SUMMARY98.json').read_text());assert s['fixedThree']==3 and s['newInvalidRegression']==0 and s['owned98NativeMaterialsRTComputeClonesRemaining']==0 and not s['lastEditorPlaying'];DEST.mkdir()
    for p in HERE.iterdir():
        if p.is_file()and p.suffix in ['.py','.cs','.compute','.shader','.json','.html']and p.name not in ['WholeEye96.compute','COMMIT98.json']:copy(p,DEST/p.name)
    for folder in ['capture','capture-b','capture-c','frozen','end-status']:
        for p in (HERE/folder).iterdir():
            if not p.is_file()or p.name.startswith('native-before-')or '_CONSOLE_'in p.name:continue
            if p.suffix in ['.py','.cs','.txt','.json']or p.name.endswith('.marker'):copy(p,DEST/folder/p.name)
    for folder in ['analysis-b','analysis-c','policy-review-c']:
        for p in (HERE/folder).rglob('*'):
            if p.is_file():copy(p,DEST/folder/p.relative_to(HERE/folder))
    # Keep the specific rejected-brow example; all original failed trial data
    # remains untouched in the workspace, not falsely promoted to final output.
    for name in ['frame136-comparison8.png','frame136-legacy96-native1x.png','frame136-underlay98-native1x.png']:copy(HERE/'review'/name,DEST/'rejected-brow-review'/name)
    copy(HERE.parent/'apply-capture66/analyse_capture68.py',DEST/'reader68.py')
    with zipfile.ZipFile(DEST/'RAW98C.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        state=json.loads(sorted((HERE/'capture-c').glob('STATE98C*'))[-1].read_text())
        for e in state['sequencePackets']:
            p=Path(e['output']);assert(p/'RAW_COMPLETE76.marker').read_text()==sha(p/'RAW_MANIFEST.json')
            for f in p.iterdir():assert f.is_file();z.write(f,f'frame-{e["frame"]}/'+f.name)
    with zipfile.ZipFile(DEST/'REJECTED_RAW98.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for folder,frame in [('capture',136),('capture-b',128)]:
            state=json.loads(sorted((HERE/folder).glob('STATE98*'))[-1].read_text());e=next(e for e in state['sequencePackets']if e['frame']==frame);p=Path(e['output']);assert(p/'RAW_COMPLETE76.marker').read_text()==sha(p/'RAW_MANIFEST.json')
            for f in p.iterdir():assert f.is_file();z.write(f,folder+'/'+f.name)
    with zipfile.ZipFile(DEST/'FROZEN98_GPU.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for p in (HERE/'frozen/gpu-output').iterdir():
            if p.is_file():z.write(p,p.name)
    for name in ASSETS:
        p=REPO/name
        if p.suffix=='.meta':p.write_bytes(b'\n'.join(l.rstrip()for l in p.read_bytes().splitlines())+b'\n')
        copy(p,DEST/('ASSET_'+p.name))
    assert sha(REPO/ASSETS[0])==sha(HERE/'WholeEye98.compute')and sha(REPO/ASSETS[1])==sha(HERE/'CurrentNonEye98.shader')
    (DEST/'.gitattributes').write_text('* -text\n');(DEST/'PRESERVATION98.json').write_text(json.dumps({'baselineCommit':BASE,'protected32':protected,'userModified30Preserved':True,'AssetsAddedOnly':{n:sha(REPO/n)for n in ASSETS},'productDefault':77,'push':False},indent=2)+'\n')
    files=[{'path':p.relative_to(DEST).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size}for p in sorted(DEST.rglob('*'))if p.is_file()];(DEST/'ARTIFACTS98.json').write_text(json.dumps({'files':files},indent=2)+'\n');doc=REPO/DOC;assert b'## Eye98 'not in doc.read_bytes()
    with doc.open('ab')as f:f.write((HERE/'HANDOFF_APPEND98.txt').read_bytes())
    print(json.dumps({'archive':str(DEST),'files':len(files)+1,'rawZipBytes':(DEST/'RAW98C.zip').stat().st_size,'protected32Matched':True,'userModified30Preserved':True},indent=2))
def commit():
    assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();preserve();m=json.loads((DEST/'ARTIFACTS98.json').read_text())['files'];assert all(sha(DEST/x['path'])==x['SHA256']for x in m)
    git('add','--',REL,DOC,*ASSETS);expected={REL+'/'+x['path']for x in m}|{REL+'/ARTIFACTS98.json',DOC,*ASSETS};actual=set(git('diff','--cached','--name-only','-z').strip('\x00').split('\x00'));assert actual==expected
    for x in m:assert hashlib.sha256(git('show',':'+REL+'/'+x['path'],binary=True)).hexdigest()==x['SHA256']
    assert git('diff','--cached','--numstat','--',DOC).strip().split('\t')[1]=='0';git('diff','--cached','--check','--',DOC,*ASSETS);summary=git('diff','--cached','--stat');(HERE/'STAGED_STAT98.txt').write_text(summary);result=git('commit','-m','Restore typed non-eye and actual world underlays in isolated eye renderer');print(result.splitlines()[0]);assert not git('diff','--cached','--name-only').strip();preserve();assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30;r={'commit':git('rev-parse','HEAD').strip(),'files':len(actual),'AssetsAddedOnly':ASSETS,'productDefault':77,'user30Preserved':True,'protected32Preserved':True,'push':False};(HERE/'COMMIT98.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':{'archive':archive,'commit':commit}[sys.argv[1]]()
