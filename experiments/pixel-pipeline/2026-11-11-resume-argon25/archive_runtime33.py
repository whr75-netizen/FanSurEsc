"""Select only owned33 source/actual receipts; preserve user30 and prior31."""
from pathlib import Path
import hashlib,json,sys,zipfile,subprocess
H=Path(__file__).resolve().parent;G=H/'face33';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');D=R/'experiments/pixel-pipeline/2026-11-11-resume-argon25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf-8',newline='\n')
def main():
 user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(user)==30 and all(sha(R/p)==v for p,v in user.items())
 prior=json.loads((D/'face31/ARCHIVE31.json').read_text());assert all(sha(D/p['path'])==p['SHA256']for p in prior['files'])
 r=json.loads((G/'capture/COMPLETE.json').read_text());a=json.loads((G/'analysis/ACTUAL33.json').read_text());prepared=json.loads((G/'PREPARED33.json').read_text())
 assert r['Edit']and r['ownedResourcesReleased']and r['pendingOwners']==0 and r['restorationChecksPass']and not r['errors']and r['packetComplete']
 assert a['actualGPU']and a['frame']==95 and a['existingFaceCells']==59 and a['existingQEquationMismatch']==0
 assert all(sha(G/p/'RUN.cs.txt')==v for p,v in prepared['commands'].items())
 def console(phase):return json.loads(json.loads((G/phase/'REPLY.json').read_text())['result']['content'][0]['text'])['data']
 assert console('console')==console('console-after')
 z=G/'ACTUAL_GPU_PACKET33.zip'
 with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as out:
  for row in a['inputFiles']:
   p=G/'capture'/row['file'];assert sha(p)==row['sha256'];out.write(p,'capture/'+row['file'])
  out.write(G/'capture/COMPLETE.json','capture/COMPLETE.json')
 with zipfile.ZipFile(z)as check:assert check.testzip()is None
 status={'baselineCommit':'568479d6','actualGPU':True,'PlayEntries':1,'capturedFrame':95,'stage':'completed actual minimum GPU observation and restored; face region/LUT/outline still incomplete','product77Changed':False,'original30Equal':True,'prior31Equal':True,'newAssets':'Assets/EUnityValidation01/SourceBoundary33','newConsoleErrors':0,'postPublicState':'11:33:20UTC Edit/not compiling/not transitioning/GameMap1 clean/dirty31/optionsfalseNone','inputSameRef22ValuesAndDevices':True,'globals74Restored':True,'nativeEqual':46,'nativeUnavailable':[x for x in r['nativeChecks']if x.get('equal')is None],'memoryDeltaMiB':{k:(r['afterMemory'][k]-r['beforeMemory'][k])/1048576 for k in ['allocated','reserved','monoUsed']},'RTCount':[30,30],'rawZipSHA256':sha(z),'nextUnverified':['Geometric-only normal vs effective-normal gating on same-frame samples.','Unambiguous face UV gradient/AA/paint region to finite LUT input.','Final outline representation/whole character/motion quality; one frame is not completion.'],'forbiddenCalls':0}
 save(G/'STATUS33.json',status);save(G/'PRESERVATION33.json',{'original30SHA256':user,'allEqual':True,'prior31FilesEqual':len(prior['files']),'AssetsCSharpImports':0,'product77Changed':False})
 roots=['prepare_runtime33.py','Import33.cs.txt','Capture33.cs.txt','analyze_runtime33.py','relay33.py','archive_runtime33.py']
 rel=['README.md','STATUS33.json','PRESERVATION33.json','PREPARED33.json','ACTUAL_GPU_PACKET33.zip','HANDOFF_APPEND33.md']
 for phase in ['import','capture','final','console','console-after']:
  rel += [str(p.relative_to(G)).replace('\\','/')for p in (G/phase).iterdir()if p.is_file()and(p.name in ['RUN.cs.txt','REQUEST.json','REPLY.json','RELAY_EOF.json','COMPLETE.json','NATIVE_BEFORE73.json','PUBLIC_AFTER.txt','INPUT_BEFORE.json']or p.name.startswith('STATE-'))]
 rel += [str(p.relative_to(G)).replace('\\','/')for p in (G/'analysis').iterdir()if p.is_file()]
 rows=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in roots+['face33/'+n for n in sorted(set(rel))]]
 save(G/'ARCHIVE33.json',{'files':rows,'backupsAndBuildDLLsExcluded':True,'actualRawCompressed':True,'sourceId':r['frameKey']})
 if '--publish'in sys.argv:
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';current=doc.read_bytes();append=(G/'HANDOFF_APPEND33.md').read_bytes()
  if not current.endswith(append):assert sha(doc)=='4f42bd2d43b221d31f1b99c295807368c2b810c3c7b85659bf4e99a1a3ad8d07','Handoff changed; inspect'
  for row in rows+[{'path':'face33/ARCHIVE33.json','SHA256':sha(G/'ARCHIVE33.json')}]:
   target=D/row['path'];source=H/row['path']
   if target.exists():assert sha(target)==row['SHA256'],'Do not overwrite different content: '+str(target)
   else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
  if not current.endswith(append):doc.write_bytes(current+append)
  assert all(sha(D/p['path'])==p['SHA256']for p in rows)and all(sha(R/p)==s for p,s in user.items())
 print(json.dumps({'files':len(rows)+1,'published':'--publish'in sys.argv,'user30Equal':True,'prior31Equal':True,'actualFrame':95,'rawZipBytes':z.stat().st_size,'sha':sha(z)}))
if __name__=='__main__':main()
