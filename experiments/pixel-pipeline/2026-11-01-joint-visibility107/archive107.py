"""Selective107 snapshot/commit only. Product77 and original30 edits preserved."""
from pathlib import Path
import json,hashlib,subprocess,shutil,sys
H=Path(__file__).resolve().parent;P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game')
BASE='bf6f9275bf588dfcc94f6928fc43c128470d181a';REL='experiments/pixel-pipeline/2026-11-01-joint-visibility107';DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(P),*args],encoding='utf-8').strip()
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists(),q;shutil.copy2(p,q)
def guard():
 a=load(H/'ASSET107_FINAL.json');assert git('rev-parse','HEAD')==BASE
 assert all(sha(P/r['path'])==r['sha']for r in a['protected32'])and sha(P/a['newAsset'])==a['sha256']
 return a
def prepare():
 d=H/'archive-selected';d.mkdir(exist_ok=False)
 # Root algorithms/contracts, not Library transfer metadata or unrelated files.
 for p in sorted(H.iterdir()):
  if p.name in ['RESULT107.json','JOINT_SOURCE_PROOFS107.json','DENSITY_OCCLUSION107.json','MISMATCHES107.json']or p.name.startswith(('DOC_','COMMIT')):continue
  if p.is_file()and(p.suffix in ['.py','.cs','.hlsl','.compute','.json','.html','.txt','.zip','.md']):copy(p,d/p.name)
 copy(H.parent/'live-curve106/curve_reference106.py',d/'curve_reference106.py')
 for p in sorted((H/'analysis-final').rglob('*')):
  if p.is_file():copy(p,d/'analysis-final'/p.relative_to(H/'analysis-final'))
 c=H/'capture';execution=[]
 # Preserve immutable actual source bundles (including failures) and receipts.
 for p in sorted(c.iterdir()):
  if p.is_file()and(p.name.endswith('_REQUEST.json')or p.name.endswith('_REPLY.json')or p.name.startswith('RUN_')or p.name.startswith('IMPORT')or p.name in ['SHADER_POST107.json','CaptureFinal107_CONSOLE_BEFORE.json','PostFinal107_CONSOLE_AFTER.json']):copy(p,d/'execution'/p.name)
 for request in sorted(c.glob('*_REQUEST.json')):
  mode=request.stem[:-8];src=c/('RUN_'+mode+'.cs.txt');r=load(request);actual=sha(src)if src.exists()else None
  execution.append({'mode':mode,'requestSourceSHA256':r['sourceSHA256'],'preservedSourceSHA256':actual,'matches':actual==r['sourceSHA256']})
 # Recover the compile-only failed source by exact reverse diff and SHA proof.
 expected=load(c/'Compile107_REQUEST.json')['sourceSHA256'];b=(c/'RUN_Compile107b.cs.txt').read_bytes()
 replacements=[(b'var triangles=new System.Collections.Generic.Dictionary<int,bool>();',b'var triangles=new System.Collections.Generic.HashSet<int>();'),(b'triangles[hit]=true',b'triangles.Add(hit)'),(b'triangles[source.Engine.PartTriangle107(3,primitive)]=true',b'triangles.Add(source.Engine.PartTriangle107(3,primitive))'),(b'triangles.Keys.OrderBy',b'triangles.OrderBy')]
 for old,new in replacements:assert b.count(old)==1;b=b.replace(old,new)
 recovered=hashlib.sha256(b).hexdigest()==expected
 if recovered:(d/'execution/INITIAL_FAILED_COMPILE107_EXACT.cs.txt').write_bytes(b)
 (d/'EXECUTION_SOURCE107.json').write_text(json.dumps({'requests':execution,'initialFailedCompileExactRecovered':recovered,'captureSourceSHAsAllMatch':all(r['matches']for r in execution if r['mode'].startswith('Capture'))},indent=2)+'\n',encoding='utf-8')
 for label in ['capture','capture-b','capture-final']:
  cap=H/label;copy(sorted(cap.glob('STATE107-*'))[-1],d/'state'/label/'COMPLETE_STATE107.json')
  for name in ['CURRENT102.json','POST102.json']:
   if(cap/name).is_file():copy(cap/name,d/'state'/label/name)
  for p in cap.glob('eye107-*/partial-hair107/*.json'):copy(p,d/'state'/label/'hair'/p.name)
  if label=='capture-final':
   for p in cap.glob('*.cs'):copy(p,d/'execution/final-source'/p.name)
 ids=load(H/'library-private107/IDENTITY107.json');public=[{'name':Path(r['localPath']).name,'library_file_id':r['library_file_id'],'file_id':r['file_id']}for r in ids];(d/'LIBRARY_IDS107.json').write_text(json.dumps(public,indent=2)+'\n',encoding='utf-8')
 (d/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n',encoding='utf-8')
 items=[{'path':p.relative_to(d).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(d.rglob('*'))if p.is_file()]
 (d/'ARTIFACTS107.json').write_text(json.dumps({'files':items},indent=2)+'\n',encoding='utf-8');(H/'DOC_BEFORE107.json').write_text(json.dumps({'sha256':sha(P/DOC)}),encoding='utf-8')
 print(json.dumps({'files':len(items)+1,'bytes':sum(r['bytes']for r in items),'initialFailedCompileExactRecovered':recovered}))
def install():
 a=guard();assert not git('diff','--cached','--name-only')and git('diff','--name-only').splitlines()==a['modifiedBefore']
 assert sha(P/DOC)==load(H/'DOC_BEFORE107.json')['sha256'];dest=P/REL;assert not dest.exists()
 for p in sorted((H/'archive-selected').rglob('*')):
  if p.is_file():copy(p,dest/p.relative_to(H/'archive-selected'))
 with(P/DOC).open('ab')as f:f.write((H/'HANDOFF107.txt').read_bytes())
 (H/'DOC_EXPECTED107.json').write_text(json.dumps({'sha256':sha(P/DOC)}),encoding='utf-8');print('107 rejected candidate and actual evidence installed; product77 unchanged')
def commit():
 a=guard();assert sha(P/DOC)==load(H/'DOC_EXPECTED107.json')['sha256'];manifest=load(P/REL/'ARTIFACTS107.json')['files']
 assert all(sha(P/REL/r['path'])==r['sha256']for r in manifest)
 allowed={REL+'/'+r['path']for r in manifest}|{REL+'/ARTIFACTS107.json',DOC,a['newAsset'],a['newAsset']+'.meta'}
 staged=set(git('diff','--cached','--name-only').splitlines());assert not staged or staged==allowed
 assert set(git('diff','--name-only').splitlines())==set(a['modifiedBefore'])|({DOC}if DOC not in staged else set())
 if not staged:git('add','--',REL,DOC,a['newAsset'],a['newAsset']+'.meta')
 assert set(git('diff','--cached','--name-only').splitlines())==allowed
 check=subprocess.run(['git','-C',str(P),'diff','--cached','--check'],encoding='utf-8',capture_output=True);findings=check.stdout.splitlines()
 for line in findings:
  if line.startswith(REL+'/')and line.endswith(': new blank line at EOF.'):continue
  if line in ['+  userData: ','+  assetBundleName: ','+  assetBundleVariant: ']:continue
  if any(line==a['newAsset']+'.meta:'+str(n)+': trailing whitespace.'for n in [5,6,7]):continue
  raise AssertionError('Unexpected whitespace finding: '+line)
 assert check.returncode in [0,2]
 git('commit','-m','test(pixel): trace joint eye visibility and reject pointwise curve ownership')
 assert not git('diff','--cached','--name-only')and git('diff','--name-only').splitlines()==a['modifiedBefore']
 assert all(sha(P/r['path'])==r['sha']for r in a['protected32'])
 result={'commit':git('rev-parse','HEAD'),'selectedFiles':len(allowed),'candidateAccepted':False,'productDefault':77,'protected32Exact':True,'originalModified30Preserved':True,'recordedStyleOnlyFindings':findings,'push':False}
 (H/'COMMIT107.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':{'prepare':prepare,'install':install,'commit':commit}[sys.argv[1]]()
