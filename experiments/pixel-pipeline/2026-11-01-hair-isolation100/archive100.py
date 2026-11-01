from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;BASE='c21e260f9bcfb7729f3c6436d61d368092f77771';REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');REL='experiments/pixel-pipeline/2026-11-01-hair-isolation100';DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],text=True,encoding='utf-8')
def copy(p,d):d.parent.mkdir(parents=True,exist_ok=True);assert not d.exists();shutil.copy2(p,d)
def prepare():
 d=HERE/'archive';assert not d.exists();d.mkdir()
 for p in HERE.iterdir():
  if p.is_file()and(p.suffix in ['.py','.cs','.json','.html','.txt','.npz']or p.name=='.gitattributes')and p.name not in ['COMMIT100.json','PRESERVATION100.json']:copy(p,d/p.name)
 for p in (HERE/'review').iterdir():
  if p.is_file():copy(p,d/'review'/p.name)
 copy(ROOT/'apply-capture66/analyse_capture68.py',d/'reader68.py')
 cap=HERE/'capture';state=load(sorted(cap.glob('STATE100-*'))[-1]);last=sorted(cap.glob('STATE100-*'))[-1]
 for n in ['CURRENT100.json','POST100.json','VERIFY100.json','GLOBAL_NAMES66.json','PRIOR47_CURRENT100.json',last.name,'relay100.py']:copy(cap/n,d/'capture'/n)
 for p in cap.iterdir():
  if p.is_file()and(p.suffix=='.cs'or p.name.startswith('RUN_')):copy(p,d/'capture'/p.name)
 with zipfile.ZipFile(d/'RAW100.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for e in state['sequencePackets']:
   p=Path(e['output']);assert(p/'RAW_COMPLETE76.marker').read_text()==sha(p/'RAW_MANIFEST.json')
   for f in p.iterdir():
    if f.is_file():z.write(f,'frame-'+str(e['frame'])+'/'+f.name)
 receipts=[]
 for mode in ['Read100','Compile100','Capture100','Post100','Verify100']:
  r=load(cap/(mode+'_REPLY.json'));q=r['data'];assert q['isCompilationSuccessful']and q['isExecutionSuccessful'];receipts.append({'mode':mode,'request':load(cap/(mode+'_REQUEST.json')),'compiled':True,'executed':True,'logs':q['executionLogs']})
 save(d/'EXECUTION_RECEIPTS100.json',receipts)
 save(d/'ARTIFACTS100.json',{'files':[{'path':str(p.relative_to(d)).replace('\\','/'),'bytes':p.stat().st_size,'SHA256':sha(p)}for p in sorted(d.rglob('*'))if p.is_file()],'excludes':'unrelated native serialized raw backups; no secret values or Library identity/xattrs'})
 print(json.dumps({'files':len(load(d/'ARTIFACTS100.json')['files'])+1,'zipBytes':(d/'RAW100.zip').stat().st_size}))
def install():
 assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip()and len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30
 protected=load(ROOT/'live-underlay98/ASSET_CREATE98.json')['protected32'];assert all(sha(REPO/f)==h for f,h in protected.items());dest=REPO/REL;assert not dest.exists()
 for p in sorted((HERE/'archive').rglob('*')):
  if p.is_file():copy(p,dest/p.relative_to(HERE/'archive'))
 save(HERE/'PRESERVATION100.json',{'protected32':protected,'allExact':True,'base':BASE,'userTrackedChanges':30});print('100 archive copied; no Assets changes; handoff patch pending')
def commit():
 assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();d=REPO/REL;old=git('show','HEAD:'+DOC);append=(HERE/'HANDOFF_APPEND100.txt').read_text(encoding='utf-8');assert(REPO/DOC).read_text(encoding='utf-8')==old+append
 allowed={REL+'/'+f['path']for f in load(d/'ARTIFACTS100.json')['files']}|{REL+'/ARTIFACTS100.json',DOC};git('add','--',REL,DOC);assert set(git('diff','--cached','--name-only').splitlines())==allowed;assert not git('diff','--cached','--check');print(git('diff','--cached','--stat'));git('commit','-m','test(pixel): isolate hair rendering and audit actual colour stages')
 protected=load(HERE/'PRESERVATION100.json')['protected32'];assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30 and not git('diff','--cached','--name-only').strip()and all(sha(REPO/f)==h for f,h in protected.items())
 for f in load(d/'ARTIFACTS100.json')['files']:assert hashlib.sha256(subprocess.check_output(['git','-C',str(REPO),'show','HEAD:'+REL+'/'+f['path']])).hexdigest()==f['SHA256']
 save(HERE/'COMMIT100.json',{'commit':git('rev-parse','HEAD').strip(),'files':len(allowed),'AssetsChanged':False,'product77Unchanged':True,'protected32Exact':True,'userTrackedChangesRemaining':30,'push':False});print(json.dumps(load(HERE/'COMMIT100.json')))
if __name__=='__main__':{'prepare':prepare,'install':install,'commit':commit}[sys.argv[1]]()
