from pathlib import Path
import hashlib,json,shutil,subprocess,sys,zipfile
HERE=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');BASE='dda9af0b42943146ea97bfd593c074d2156080e2';REL='experiments/pixel-pipeline/2026-11-01-live-joint96';DEST=REPO/REL;DOC='docs/ai/PIXEL_ALBEDO_20261030.md';ASSET='Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/WholeEye96.compute'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a,binary=False):return subprocess.check_output(['git','-C',str(REPO),*a],**({}if binary else{'text':True,'encoding':'utf-8'}))
def preserve():
    p=json.loads((REPO/'experiments/pixel-pipeline/2026-11-01-whole-eye95/PRESERVATION95.json').read_text())['protected32'];assert all(sha(REPO/f)==h for f,h in p.items());return p
def copy(p,d):d.parent.mkdir(exist_ok=True,parents=True);assert not d.exists();shutil.copy2(p,d)
def archive():
    assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();protected=preserve();assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30;assert not DEST.exists();summary=json.loads((HERE/'SUMMARY96.json').read_text());assert summary['liveFinalAllExact']and summary['nativeResourcesDirectExact']==47 and not summary['publicStateDifferences'];DEST.mkdir()
    for p in HERE.iterdir():
        if p.is_file()and p.suffix in ['.py','.cs','.compute','.json','.html']and p.name not in ['MotionScope97.cs','COMMIT96.json']:
            copy(p,DEST/p.name)
    for folder in ['preflight','import','direct','shader-read','direct-fixed','reconstruct','full-frozen','capture','registry']:
        for p in (HERE/folder).iterdir():
            if not p.is_file()or p.name.startswith('native-before-')or '_CONSOLE_'in p.name:continue
            if p.suffix in ['.py','.cs','.txt','.json']or p.name.endswith('.marker'):copy(p,DEST/folder/p.name)
    for folder in ['review','oracle/candidate-source-cache-actual96']:
        for p in (HERE/folder).iterdir():
            if p.is_file():copy(p,DEST/folder/p.name)
    for name in ['RESULT95-source-cache-actual96.json','ORACLE_INPUT96.json']:copy(HERE/'oracle'/name,DEST/'oracle'/name)
    copy(HERE.parent/'apply-capture66/analyse_capture68.py',DEST/'reader68.py')
    state=json.loads(sorted((HERE/'capture').glob('STATE96*'))[-1].read_text())
    with zipfile.ZipFile(DEST/'RAW96.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for e in state['sequencePackets']:
            p=Path(e['output']);assert(p/'RAW_COMPLETE76.marker').read_text()==sha(p/'RAW_MANIFEST.json')
            for f in p.iterdir():assert f.is_file();z.write(f,f'frame-{e["frame"]}/'+f.name)
    for folder,filename in [('fixtures','FROZEN_INPUTS96.zip'),('oracle','ORACLE_DETAILS96.zip')]:
        with zipfile.ZipFile(DEST/filename,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
            for p in (HERE/folder).iterdir():
                if p.is_file():z.write(p,p.name)
    with zipfile.ZipFile(DEST/'FROZEN_GPU96.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for folder in ['direct-fixed','reconstruct','full-frozen']:
            for p in (HERE/folder/'gpu-output').iterdir():
                if p.is_file():z.write(p,folder+'/'+p.name)
    (DEST/'.gitattributes').write_text('* -text\n');copy(REPO/ASSET,DEST/'ASSET_WholeEye96.compute');copy(REPO/(ASSET+'.meta'),DEST/'ASSET_WholeEye96.compute.meta');assert sha(REPO/ASSET)==sha(HERE/'WholeEye96.compute')
    (DEST/'PRESERVATION96.json').write_text(json.dumps({'baselineCommit':BASE,'protected32':protected,'userModified30Preserved':True,'addedAssetsOnly':[ASSET,ASSET+'.meta'],'assetSHA256':sha(REPO/ASSET),'metaSHA256':sha(REPO/(ASSET+'.meta')),'defaultProduct':77,'push':False},indent=2)+'\n')
    files=[{'path':p.relative_to(DEST).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size}for p in sorted(DEST.rglob('*'))if p.is_file()];(DEST/'ARTIFACTS96.json').write_text(json.dumps({'files':files},indent=2)+'\n')
    doc=REPO/DOC;assert b'## Eye96 'not in doc.read_bytes()
    with doc.open('ab')as f:f.write((HERE/'HANDOFF_APPEND96.txt').read_bytes())
    print(json.dumps({'archive':str(DEST),'files':len(files)+1,'rawBytes':(DEST/'RAW96.zip').stat().st_size,'protected32Matched':True,'userModified30Preserved':True},indent=2))
def commit():
    assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();preserve();m=json.loads((DEST/'ARTIFACTS96.json').read_text())['files'];assert all(sha(DEST/x['path'])==x['SHA256']for x in m);assert sha(REPO/ASSET)==sha(DEST/'ASSET_WholeEye96.compute')and sha(REPO/(ASSET+'.meta'))==sha(DEST/'ASSET_WholeEye96.compute.meta')
    git('add','--',REL,DOC,ASSET,ASSET+'.meta');expected={REL+'/'+x['path']for x in m}|{REL+'/ARTIFACTS96.json',DOC,ASSET,ASSET+'.meta'};actual=set(git('diff','--cached','--name-only','-z').strip('\x00').split('\x00'));assert actual==expected
    for x in m:assert hashlib.sha256(git('show',':'+REL+'/'+x['path'],binary=True)).hexdigest()==x['SHA256']
    assert git('diff','--cached','--numstat','--',DOC).strip().split('\t')[1]=='0';git('diff','--cached','--check','--',DOC,ASSET,ASSET+'.meta');print(git('commit','-m','Add isolated GPU whole-eye selection and validate against live source frames'));assert not git('diff','--cached','--name-only').strip();preserve();assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30;r={'commit':git('rev-parse','HEAD').strip(),'files':len(actual),'default':77,'user30Preserved':True,'protected32Preserved':True,'push':False};(HERE/'COMMIT96.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':{'archive':archive,'commit':commit}[sys.argv[1]]()
