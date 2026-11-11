"""Extend this own, verified archive only; preserve prior evidence and originals."""
from pathlib import Path
import hashlib,json,shutil,zipfile
H=Path(__file__).resolve().parent
DEST=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\experiments\pixel-pipeline\2026-11-11-resume-argon25\producer\support')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 old=read(H/'ARCHIVED26.json');assert str(DEST)==old['destination']
 expected={v['file']:v['sha256']for v in old['copiedOwnFiles']}
 assert not(DEST/'ARCHIVE_MANIFEST26.json').exists(),'Inspect completed archive, never rerun blindly'
 for name,digest in expected.items():assert sha(DEST/name)==digest,('Existing archive changed',name)
 names=[p.relative_to(H)for p in H.iterdir()if p.is_file()and p.suffix in['.py','.cs','.png']]
 names += [Path(n)for n in ['MEMORY26.json','PRESERVED26.json','STATUS26.json','LIBRARY_FILES26.json','OS_POST26.json','CURVE_NATIVE_SOURCE_AUDIT26.json','CURVE_NATIVE_SOURCE_AUDIT26_WRONG_PART.json']]
 names += [Path('postflight-native')/n for n in ['ReadState.cs.txt','probe.py','READ_REQUEST.json','READ_REPLY.json','READ_RELAY_EOF.json','INVENTORY.json']]
 names += [p.relative_to(H)for p in(H/'native-proof').iterdir()if p.is_file()and(p.suffix in['.json','.py','.compute','.png']or p.name.endswith('.cs.txt')or p.name.endswith('.diagnostics.txt'))]
 names += [p.relative_to(H)for p in(H/'native-proof/import').glob('*.json')]
 rows=[]
 def copy(name):
  p=H/name;q=DEST/name;assert p.is_file(),str(name);q.parent.mkdir(parents=True,exist_ok=True)
  if q.exists()and sha(q)!=sha(p):assert str(name)in expected and sha(q)==expected[str(name)],('Unowned archive conflict',str(name))
  if not q.exists()or sha(q)!=sha(p):shutil.copyfile(p,q)
  assert sha(p)==sha(q);rows.append({'file':str(name),'bytes':p.stat().st_size,'sha256':sha(p)})
 for name in sorted(set(names)):copy(name)
 for runName in ['phase-run','readback-run','typed-run','motion-run']:
  root=H/'native-proof'/runName;stateFile=next(root.glob('STATE113-*-finished.json'));s=read(stateFile)
  assert s['PlayExited']and not s.get('restorationError')and not s['globalRestoreErrors']
  for name in ['RUN_Capture25.cs.txt','RUN_Capture25.cs.diagnostics.txt','GLOBAL_NAMES66.json','PHASE_REQUEST.json','PHASE_REPLY.json','PHASE_RELAY_EOF.json','NATIVE_BEFORE73.json']:
   copy(root.relative_to(H)/name)
  for p in [next(root.glob('STATE113-*-ready-before-Play.json')),next(root.glob('STATE113-*-normal-Play-exit-requested.json')),stateFile]:copy(p.relative_to(H))
  if s.get('error'):
   assert '107 bounded source readback'in s['error']and not s.get('sequencePackets')
   continue
  for p in(root/'results').iterdir():
   if p.is_file():copy(p.relative_to(H))
  q=DEST/root.relative_to(H)/'ACTUAL_GPU_PACKETS26.zip';entries=[]
  with zipfile.ZipFile(q,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   for packet in s['sequencePackets']:
    p=Path(packet['output']);marker=p/'RAW_COMPLETE76.marker';assert marker.read_text().strip()==sha(p/'RAW_MANIFEST.json')
    for f in sorted(p.iterdir()):
     assert f.is_file();name=f.relative_to(root).as_posix();z.write(f,name);entries.append({'file':name,'bytes':f.stat().st_size,'sha256':sha(f),'sourceId':packet['sourceId']})
  with zipfile.ZipFile(q)as z:
   assert z.testzip()is None
   for v in entries:assert hashlib.sha256(z.read(v['file'])).hexdigest()==v['sha256']
  (q.parent/'PACKET_INDEX26.json').write_text(json.dumps({'actualGPU':True,'archive':q.name,'sha256':sha(q),'frames':len(s['sequencePackets']),'entries':entries,'scope':'Actual native-proof inputs. Exact CPU source curve upload is labelled separately from GPU column readback. External absolute paths retained; review evidence is not an automatic execution.'},indent=2)+'\n',encoding='utf-8')
 allFiles=[{'file':p.relative_to(DEST).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(DEST.rglob('*'))if p.is_file()]
 manifest={'files':allFiles,'latestActualFrames':32,'earlierCapturedFrames':38,'invalidObservationRuns':2,'latestEntry':'STATUS26.json','latestLibraryIdentity':'LIBRARY_FILES26.json','product77DefaultChanged':False}
 (DEST/'ARCHIVE_MANIFEST26.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 (H/'ARCHIVE_MANIFEST26.json').write_bytes((DEST/'ARCHIVE_MANIFEST26.json').read_bytes())
 print(json.dumps({'archiveFiles':len(allFiles),'bytes':sum(v['bytes']for v in allFiles),'latestActualFrames':32,'destination':str(DEST)}))
if __name__=='__main__':main()
