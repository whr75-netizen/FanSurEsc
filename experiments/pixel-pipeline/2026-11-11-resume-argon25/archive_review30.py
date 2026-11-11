"""Archive only CPU30 review artifacts; never touches Assets or a Unity endpoint."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'face30'
R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
D=R/'experiments/pixel-pipeline/2026-11-11-resume-argon25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 baseline=json.loads((H/'RESUME_STATUS.json').read_text(encoding='utf-8'))['userTrackedFiles']
 checks={p:sha(R/p)==v for p,v in baseline.items()};assert len(checks)==30 and all(checks.values()),checks
 originals={
 'Assets/EUnityValidation01/SourceBoundary29/SourceOutline29.shader':'0b1653c12dc832418f45c614a4627e31354e63b32128d699cdc7c743f62d16c9',
 'Assets/EUnityValidation01/SourceBoundary29/LineClass29.compute':'98bb7dd5638d0ac0c78e11d78b80e600d707d04bee9022f78e192e585d8de6ec',
 }
 assert all(sha(R/p)==s for p,s in originals.items())
 originalRunner=H/'face29/run/RUN_Capture25.cs.txt'
 assert sha(originalRunner)=='9a21259f9296550b5f373245cf98999889c6e5fcc7e85f8a59754bb139ceea34'
 tests=json.loads((G/'CPU_CONTRACT30.json').read_text());integration=json.loads((G/'CPU_INTEGRATION30.json').read_text())
 assert tests['checks']==38 and integration['CPUCompile']=='passed' and all(integration['shaderABIStaticChecks'].values())
 assert integration['sourceSHA256']==sha(G/'SourceOutline30.cs') and integration['contractsSHA256']==sha(H/'ProducerContracts30.cs')
 assert all(sha(H/p)==s for p,s in tests['sourceFiles'].items())
 assert tests['fixtureSHA256']==sha(G/'FIXTURE30.json')
 preservation={'originalTracked30':checks,'originalShaderAndCompute':originals,'failed29RunnerUnchanged':True,'AssetsWrites':0,'UnityRelayCalls':0,'GPUCalls':0,'currentNativeEditorStateObserved':False}
 (G/'PRESERVATION30.json').write_text(json.dumps(preservation,indent=2),encoding='utf-8',newline='\n')
 names=['ProducerContracts30.cs','ContractTests30.cs','verify_contracts30.py','prepare_review30.py','audit_sources30.py','archive_review30.py']
 names+=['face30/'+n for n in ['README.md','READINESS30.json','FIXTURE30.json','SourceOutline30.cs','CPU_CONTRACT30.json','CPU_INTEGRATION30.json','SOURCE_AUDIT30.json','CPU_DIAGNOSTICS30.txt','PRESERVATION30.json']]
 rows=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in names]
 manifest={'baselineCommit':'f7a4ea8480312510f2c6d25ee9d7c887e5e6698b','files':rows,'runtimeReady':False,'buildBinariesAndRawNativeBackupsExcluded':True}
 (G/'ARCHIVE30.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
 if '--publish'in sys.argv:
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';current=doc.read_bytes();append=(G/'HANDOFF_APPEND30.md').read_bytes()
  expected='5a801cd316d9d709c5274b9c1fb7a19dc6c3076d12c9eb92b2b39201654e49d7'
  if not current.endswith(append):assert sha(doc)==expected,'handoff changed; review before writing'
  for row in rows+[{'path':'face30/ARCHIVE30.json','SHA256':sha(G/'ARCHIVE30.json')}]:
   target=D/row['path'];source=H/row['path']
   if target.exists():assert sha(target)==row['SHA256'],'different existing destination: '+str(target)
   else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
  if not current.endswith(append):doc.write_bytes(current+append)
  assert all(sha(D/row['path'])==row['SHA256']for row in rows)
  assert all(sha(R/p)==v for p,v in baseline.items())
 print(json.dumps({'files':len(rows)+1,'CPUChecks':tests['checks'],'ABIStaticChecks':len(integration['shaderABIStaticChecks']),'published':'--publish'in sys.argv,'user30ByteEqual':True,'UnityGPUCalls':0,'runtimeReady':False}))
if __name__=='__main__':main()
