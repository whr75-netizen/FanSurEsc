"""Publish only unactivated CPU31 source/evidence and the existing handoff append."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'face31';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');D=R/'experiments/pixel-pipeline/2026-11-11-resume-argon25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 original=json.loads((H/'RESUME_STATUS.json').read_text(encoding='utf-8'))['userTrackedFiles'];assert len(original)==30 and all(sha(R/p)==s for p,s in original.items())
 for name in ['SourceOutline29.shader','LineClass29.compute']:
  expected={'SourceOutline29.shader':'0b1653c12dc832418f45c614a4627e31354e63b32128d699cdc7c743f62d16c9','LineClass29.compute':'98bb7dd5638d0ac0c78e11d78b80e600d707d04bee9022f78e192e585d8de6ec'}[name]
  assert sha(R/'Assets/EUnityValidation01/SourceBoundary29'/name)==expected
 assert sha(H/'ProducerContracts30.cs')=='42a3c0ab5868b823279307b21d25f3d3eded64adcf50bc76672ba1d9479060f4'
 tests=json.loads((G/'CPU_LIFETIME31.json').read_text());compile=json.loads((G/'CPU_INTEGRATION31.json').read_text());assert tests['checks']==50 and compile['CPUCompile']=='passed' and all(compile['staticChecks'].values())
 assert all(sha(H/n)==s for n,s in tests['sources'].items())
 for n,s in compile['sourceFiles'].items():
  path=H/n if(H/n).exists()else G/n
  if n=='LegacySignals335.shader':path=R/'Assets/EUnityValidation01/MinimalRestore335/Shaders'/n
  assert sha(path)==s,n
 preservation={'originalTracked30SHA256':original,'original30ByteEqual':True,'historical30AndAssets29Unchanged':True,'AssetsWrites':0,'UnityRelayGPUCalls':0,'currentNativeStateObserved':False}
 (G/'PRESERVATION31.json').write_text(json.dumps(preservation,indent=2),encoding='utf-8',newline='\n')
 roots=['ProducerLifetime31.cs','LifecycleTests31.cs','Projection31.cs','SourceOutline31.cs','SourceCaptureHost31.cs','prepare_lifetime31.py','verify_lifetime31.py','archive_lifetime31.py']
 data=['README.md','READINESS31.json','CPU_LIFETIME31.json','CPU_INTEGRATION31.json','CPU_DIAGNOSTICS31.txt','BOUNDS31.json','Json58Reference31.cs','QMeta31.shader','SourceOutline31.shader','LineClass31.compute','PRESERVATION31.json']
 rows=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in roots+['face31/'+n for n in data]]
 result={'baselineCommit':'abcbfe42','files':rows,'runtimeValidated':False,'UnityGPUCalls':0,'buildBinariesAndRawNativeBackupsExcluded':True}
 (G/'ARCHIVE31.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
 if '--publish'in sys.argv:
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';current=doc.read_bytes();append=(G/'HANDOFF_APPEND31.md').read_bytes()
  if not current.endswith(append):assert sha(doc)=='ee30a76574da0bddd01ecef8c400de70692e52549ff2d04b358731b5919176d4','handoff changed; review before append'
  previous={}
  oldManifest=D/'face31/ARCHIVE31.json'
  if oldManifest.exists():
   previous={row['path']:row['SHA256']for row in json.loads(oldManifest.read_text())['files']};previous['face31/ARCHIVE31.json']=sha(oldManifest)
  for row in rows+[{'path':'face31/ARCHIVE31.json','SHA256':sha(G/'ARCHIVE31.json')}]:
   target=D/row['path'];source=H/row['path']
   if target.exists()and sha(target)!=row['SHA256']:
    assert '--update-owned'in sys.argv and sha(target)==previous.get(row['path']),'destination is not our unchanged prior artifact: '+str(target)
    target.write_bytes(source.read_bytes())
   elif target.exists():pass
   else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
  if not current.endswith(append):doc.write_bytes(current+append)
  assert all(sha(D/v['path'])==v['SHA256']for v in rows)
  assert all(sha(R/p)==s for p,s in original.items())
 print(json.dumps({'files':len(rows)+1,'CPUChecks':tests['checks'],'staticChecks':len(compile['staticChecks']),'user30ByteEqual':True,'published':'--publish'in sys.argv,'UnityGPUCalls':0,'runtimeValidated':False}))
if __name__=='__main__':main()
