"""Archive CPU32 source/evidence only; no Assets, Editor or GPU mutation."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'face32';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');D=R/'experiments/pixel-pipeline/2026-11-11-resume-argon25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 original=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(original)==30 and all(sha(R/p)==s for p,s in original.items())
 prior=json.loads((D/'face31/ARCHIVE31.json').read_text());assert all(sha(D/p['path'])==p['SHA256']for p in prior['files'])
 q=json.loads((G/'CPU_Q32.json').read_text());c=json.loads((G/'CPU_CONSUMER32.json').read_text());review=json.loads((G/'CPU_REVIEW32.json').read_text());audit=json.loads((G/'SOURCE_AUDIT32.json').read_text());receipt=json.loads((G/'PATCH_CHECK32.json').read_text())
 assert q['checks']==37 and q['exhaustiveRingPatterns']==256 and q['legacySchemaRangeCases']==108 and q['sourceSHA256']==sha(H/'QPrime32.cjs')
 assert c['checks']==30 and all(sha(H/p)==s for p,s in c['sources'].items())
 assert review['CPUCompile']=='passed'and all(review['staticChecks'].values())and all(sha(H/p)==s for p,s in review['reviewFiles'].items())
 assert all(sha(H/p)==sha(D/p)for p in review['reviewFiles']if(D/p).exists()),'shared candidate31 input changed'
 assert sha(H/'SourceOutline31.cs')==review['baseSource31SHA256']and sha(H/'SourceCaptureHost31.cs')==review['baseHost31SHA256']
 assert all(sha(R/row['path'])==row['SHA256']for row in audit['source'].values())
 assert not receipt['applied']and receipt['shaderPatchDryRun']==0 and receipt['lifetimePatchDryRun']==0 and all(sha(G/p)==s for p,s in receipt['patchSHA256'].items())
 (G/'PRESERVATION32.json').write_text(json.dumps({'originalTracked30SHA256':original,'original30ByteEqual':True,'prior31FilesByteEqual':len(prior['files']),'AssetsWrites':0,'UnityRelayGPUCalls':0,'nativeStateObserved':False,'patchesApplied':False},indent=2),encoding='utf-8',newline='\n')
 roots=['QPrime32.cjs','ConsumerReads32.cs','ConsumerTests32.cs','ReadbackPreflight32.cs','prepare_qreview32.py','verify_qreview32.py','audit_q32.py','archive_qreview32.py']
 data=['README.md','READINESS32.json','CPU_Q32.json','CPU_CONSUMER32.json','CPU_REVIEW32.json','SOURCE_AUDIT32.json','UNAPPLIED_Legacy502_32.patch','UNAPPLIED_ConsumerLifetime32.patch','CPU_DIAGNOSTICS32.txt','PATCH_CHECK32.json','PRESERVATION32.json']
 rows=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in roots+['face32/'+n for n in data]]
 result={'baselineCommit':'cea8f19a','files':rows,'UnityGPUCalls':0,'patchesApplied':False,'buildAndRawBackupsExcluded':True}
 (G/'ARCHIVE32.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
 if '--publish'in sys.argv:
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';current=doc.read_bytes();append=(G/'HANDOFF_APPEND32.md').read_bytes()
  if not current.endswith(append):assert sha(doc)=='a75f57b407d049ad43c952411bacf4117ee48e07d3ae7996e505dcba557b5d60','handoff changed; inspect first'
  previous={};oldManifest=D/'face32/ARCHIVE32.json'
  if oldManifest.exists():previous={p['path']:p['SHA256']for p in json.loads(oldManifest.read_text())['files']};previous['face32/ARCHIVE32.json']=sha(oldManifest)
  for row in rows+[{'path':'face32/ARCHIVE32.json','SHA256':sha(G/'ARCHIVE32.json')}]:
   target=D/row['path'];source=H/row['path']
   if target.exists()and sha(target)!=row['SHA256']:
    assert '--update-owned'in sys.argv and sha(target)==previous.get(row['path']),'destination is not unchanged prior own artifact: '+str(target)
    target.write_bytes(source.read_bytes())
   elif target.exists():pass
   else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
  if not current.endswith(append):doc.write_bytes(current+append)
  assert all(sha(D/p['path'])==p['SHA256']for p in rows)and all(sha(R/p)==s for p,s in original.items())
 print(json.dumps({'files':len(rows)+1,'QScenarios':q['checks'],'consumerChecks':c['checks'],'published':'--publish'in sys.argv,'user30ByteEqual':True,'prior31ByteEqual':True,'UnityGPUCalls':0,'patchesApplied':False}))
if __name__=='__main__':main()
