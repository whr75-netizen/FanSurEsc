from pathlib import Path
import json,hashlib,shutil,subprocess,sys,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
BASE='cf8b14147e94ff87f2487efc523e62ea9456877f';REL='experiments/pixel-pipeline/2026-11-01-view-isolation99';DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists();shutil.copy2(p,q)
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],text=True,encoding='utf-8')
def prepare():
    d=HERE/'archive';assert not d.exists();d.mkdir()
    for n in ['.gitattributes','WholeEye96.cs','NativeRetarget96.cs','LiveSurface96.cs','LiveGraph96.cs','LiveFinal96.cs','GraphSources96.cs','NonEyeUnderlay98.cs','GpuTiming98.cs','HoldScope99.cs','ViewB99.cs','prepare99.py','analyse99.py','finalize99.py','archive99.py','test_archive99.py','repackage99.py','INDEX.html','SUMMARY99.json','PROFILING99.json','DELIVERY_STATUS99.json','HANDOFF_APPEND99.txt']:copy(HERE/n,d/n)
    for p in (HERE/'deliverables').iterdir():assert p.is_file();copy(p,d/'deliverables'/p.name)
    copy(ROOT/'apply-capture66/analyse_capture68.py',d/'reader68.py')
    cap=HERE/'capture';last=sorted(cap.glob('STATE99-*'))[-1];state=load(last)
    for n in ['CURRENT99.json','PRIOR47_CURRENT99.json','POST99.json','VERIFY99.json','GLOBAL_NAMES66.json','NATIVE_BEFORE73.json',last.name,'relay99.py']:
        copy(cap/n,d/'capture'/n)
    for p in cap.iterdir():
        if p.is_file()and(p.suffix=='.cs'or p.name.startswith('RUN_')):copy(p,d/'capture'/p.name)
    receipts=[]
    for mode in ['Read99','Compile99','Capture99','Post99','Verify99']:
        r=load(cap/(mode+'_REPLY.json'));x=r['data'];assert x['isCompilationSuccessful']and x['isExecutionSuccessful']
        receipts.append({'mode':mode,'request':load(cap/(mode+'_REQUEST.json')),'compiled':True,'executed':True,'compilationLogs':x['compilationLogs'],'executionLogs':x['executionLogs']})
    save(d/'EXECUTION_RECEIPTS99.json',receipts)
    with zipfile.ZipFile(d/'RAW99.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for e in state['sequencePackets']:
            p=Path(e['output']);assert(p/'RAW_COMPLETE76.marker').read_text()==sha(p/'RAW_MANIFEST.json')
            for f in p.iterdir():assert f.is_file();z.write(f,'frame-'+str(e['frame'])+'/'+f.name)
    # No native-before-*.json: those include unrelated UnityConnect settings.
    files=[{'path':str(p.relative_to(d)).replace('\\','/'),'bytes':p.stat().st_size,'SHA256':sha(p)}for p in sorted(d.rglob('*'))if p.is_file()]
    save(d/'ARTIFACTS99.json',{'files':files,'excludes':'raw native serialized backups, helper/network state and credentials; no online write receipt exists'})
    print(json.dumps({'prepared':str(d),'files':len(files)+1,'RAWZipBytes':(d/'RAW99.zip').stat().st_size}))
def install():
    assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip()
    p=load(ROOT/'live-underlay98/ASSET_CREATE98.json')['protected32'];assert all(sha(REPO/n)==h for n,h in p.items())
    tracked=git('status','--porcelain=v1','--untracked-files=no').splitlines();assert len(tracked)in [30,31]
    d=REPO/REL;assert not d.exists();src=HERE/'archive';manifest=load(src/'ARTIFACTS99.json');assert all(sha(src/f['path'])==f['SHA256']for f in manifest['files'])
    for f in sorted(src.rglob('*')):
        if f.is_file():copy(f,d/f.relative_to(src))
    save(HERE/'PRESERVATION99.json',{'base':BASE,'protected32':p,'allExact':True,'preInstallTrackedStatus':tracked,'AssetsWritten':False})
    print('Copied exact99-only archive; handoff update and selective staging still separate')
def commit():
    d=REPO/REL;assert git('rev-parse','HEAD').strip()==BASE
    p=load(HERE/'PRESERVATION99.json')['protected32'];assert all(sha(REPO/n)==h for n,h in p.items());append=(HERE/'HANDOFF_APPEND99.txt').read_text(encoding='utf-8');old=git('show','HEAD:'+DOC);assert(REPO/DOC).read_text(encoding='utf-8')==old+append
    allowed={REL+'/'+f['path']for f in load(d/'ARTIFACTS99.json')['files']}|{REL+'/ARTIFACTS99.json',DOC}
    assert set(git('diff','--cached','--name-only').splitlines())<=allowed
    git('add','--',REL,DOC);staged=set(git('diff','--cached','--name-only').splitlines());assert staged==allowed,(staged-allowed,allowed-staged)
    assert not git('diff','--cached','--check');stat=git('diff','--cached','--stat');(HERE/'STAGED_STAT99.txt').write_text(stat,encoding='utf-8');print(stat)
    git('commit','-m','test(pixel): validate actual view isolation and present tie choices')
    h=git('rev-parse','HEAD').strip();assert not git('diff','--cached','--name-only').strip()and len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30 and all(sha(REPO/n)==v for n,v in p.items())
    save(HERE/'COMMIT99.json',{'commit':h,'base':BASE,'files':len(staged),'AssetsModifiedBy99':False,'protected32Exact':True,'userTrackedModificationsRemaining':30,'remotePush':False});print(json.dumps(load(HERE/'COMMIT99.json')))
if __name__=='__main__':{'prepare':prepare,'install':install,'commit':commit}[sys.argv[1]]()
