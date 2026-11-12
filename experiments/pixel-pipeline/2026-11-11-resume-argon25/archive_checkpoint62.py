"""Selective intermediate commit of owned58-62 diagnostics and two new assets."""
from pathlib import Path
import json,hashlib,subprocess,sys
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';BASE='5802b5cb1096f3e81892baabff0174452cb2956f'
ROOTS=['prepare_width58.py','relay58.py','prepare_width59.py','relay59.py','prepare_hull60.py','relay60.py','review_hull60.py','test_hull60.py','prepare_width61.py','relay61.py','review_width61.py','face_parent62.py','test_parent62.py','replay_parent62.py','UpdateOwned62.cs.txt','prepare_parent62.py','relay62.py','review_parent62.py','final62.py','archive_checkpoint62.py']
ASSETS=['Assets/EUnityValidation01/SourceBoundary60.meta','Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.shader','Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.shader.meta','Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.compute','Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.compute.meta']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf-8',newline='\n')
def main():
 assert git('rev-parse','HEAD')==BASE and not git('diff','--cached','--name-only')
 user=load(H/'face55/BEFORE_GIT55.json')['user30'];assert all(sha(R/p)==v for p,v in user.items())
 disk=load(H/'face55/backup/DISK_BEFORE.json');assert all((R/x['path']).exists()==x['exists']and(not x['exists']or sha(R/x['path'])==x['sha256'])for x in disk)
 f=load(H/'face62/final/STATE.json');assert f['Edit']and f['inputJSONExact']and f['diagnosticRTs']==f['diagnosticMaterials']==f['commandUpdateObservers']==0 and f['allRTCount']==30
 for n in[58,59,60,61,62]:
  d=load(H/f'face{n}/capture'/('FAILED.json'if n<60 else'COMPLETE.json'));assert d['restorationChecksPass']and d['ownedResourcesReleased']and not d['errors']and d['pendingOwners']==0 and all(c['equal'] is not False for c in d['nativeChecks'])
 a=load(H/'face62/analysis/ACTUAL_PARENT62.json');assert a['positiveFinalOwnerSamples']==59 and a['realChildColourPreserved']and a['CPUExactCases']==4
 console=load(H/'face62/console/REPLY.json')['result'];c=console.get('structuredContent')or next(json.loads(x['text'])for x in console['content']if x.get('type')=='text');assert c['success']and not c['data']['logs']
 assert sha(R/ASSETS[1])==sha(H/'face60/shaders/SourceNativeHull60.shader')and sha(R/ASSETS[3])==sha(H/'face62/shaders/SourceNativeHull60.compute')
 files=ROOTS[:]
 for n in[58,59,60,61,62]:
  for p in(H/f'face{n}').rglob('*'):
   if not p.is_file()or'build'in p.parts or p.name.startswith(('native-before-','native-after-'))or p.name in['GLOBALS_BEFORE.bin','INPUT_BEFORE.json','INPUT_AFTER.json','REPLY.json','SCHEMA.json','COMMIT62.json','ARCHIVE62.json','COMMIT_BODY62.txt']:continue
   files.append(p.relative_to(H).as_posix())
 files=sorted(set(files));rows=[{'path':p,'bytes':(H/p).stat().st_size,'SHA256':sha(H/p)}for p in files];assets=[{'path':p,'bytes':(R/p).stat().st_size,'SHA256':sha(R/p)}for p in ASSETS]
 save(H/'face62/ARCHIVE62.json',{'baseCommit':BASE,'files':rows,'ownedNewAssets':assets,'user30AndProtected128Exact':True,'product77DefaultChanged':False,'calibrationArtAdopted':False})
 if'--publish'in sys.argv:
  for row in rows+[{'path':'face62/ARCHIVE62.json','SHA256':sha(H/'face62/ARCHIVE62.json')}]:
   target=R/P/row['path'];assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((H/row['path']).read_bytes());assert sha(target)==row['SHA256']
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';assert not git('diff','--name-only','--',str(doc));old=doc.read_bytes();add=(H/'face62/HANDOFF_APPEND62.md').read_bytes();assert add not in old;doc.write_bytes(old+add)
 print(json.dumps({'files':len(rows)+1,'bytes':sum(x['bytes']for x in rows),'ownAssets':len(assets),'published':'--publish'in sys.argv,'user30And128Equal':True}))
 if'--commit'in sys.argv:
  assert'--publish'in sys.argv;names=[P+'/'+r['path']for r in rows]+[P+'/face62/ARCHIVE62.json','docs/ai/PIXEL_ALBEDO_20261030.md']+ASSETS;assert not set(names).intersection(user);git('add','--',*names);assert set(git('diff','--cached','--name-only').splitlines())==set(names)
  patches=[p for p in names if p.endswith('.patch')]
  for p in patches:git('apply','--numstat',str(R/p))
  subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--',*[p for p in names if p not in patches]],cwd=R,check=True)
  body=H/'face62/COMMIT_BODY62.txt';body.write_text('Use authored face-outline width and compose below confirmed eye children\n\nPreserve failed58/59 source comparisons; use current source material colour and width instead of frozen values or tolerance. Add private native MToon hull and explicit primitive/UV ownership. Keep product77 default untouched.\n\nActual same-frame width0/1/8/32 calibration proves variable geometry and exposes6 iris/sclera overwrites. Apply same-frame child-role/native-owner parent composition; verify4 GPU RGB cases plus59 final owner/UV/layer samples against CPU. Preserve canvas, hair/world tests, callback lifetime, user30/protected128 and Editor state.\n\nFull-face regions/palette, runtime history, long-term motion and art approval remain incomplete.\n',encoding='utf-8');print(git('commit','--file',str(body)));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in user.items());save(H/'face62/COMMIT62.json',{'commit':git('rev-parse','HEAD'),'files':len(names),'product77DefaultChanged':False,'user30Equal':True,'ownedAssets':ASSETS,'actualGPUCases':4,'positiveOwnerSamples':59,'artAdopted':False,'push':False});print((H/'face62/COMMIT62.json').read_text())
if __name__=='__main__':main()
