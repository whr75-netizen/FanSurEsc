"""Extend this own, verified archive only; preserve prior evidence and originals."""
from pathlib import Path
import hashlib,json,shutil,sys,zipfile
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
def surface27(final=False):
 oldName='ARCHIVE_MANIFEST27.json'if final else'ARCHIVE_MANIFEST26.json'
 finalName='ARCHIVE_FINAL27.json'if final else'ARCHIVE_MANIFEST27.json'
 old=read(DEST/oldName);expected={v['file']:v['sha256']for v in old['files']}
 assert not(DEST/finalName).exists(),'Inspect outcome before any archive retry'
 for name,digest in expected.items():assert sha(DEST/name)==digest,('Previous committed archive changed',name)
 g=H/'surface27';names=[Path(n)for n in ['surface27.py','test_surface27.py','prepare_surface27.py','audit_face27.py','finalize_surface27.py','compile_gate.py','review_gate.py','prepare_motion.py','verify_native_proof.py','trace_rotation.py','trace_gate_change.py','archive_extend26.py','STATUS26.json','LIBRARY_FILES26.json']]
 if final:names.append(Path('prepare_pigment27.py'))
 names += [p.relative_to(H)for p in g.iterdir()if p.is_file()and not p.name.startswith(('STAGE_REVIEW','COMMIT'))and(p.suffix in['.json','.py','.compute','.bin','.png']or p.name.endswith('.cs.txt')or p.name.endswith('.diagnostics.txt'))]
 names += [p.relative_to(H)for sub in (['import','postflight','pigment-postflight']if final else['import','postflight'])for p in(g/sub).iterdir()if p.is_file()]
 def copy(name):
  p=H/name;q=DEST/name;q.parent.mkdir(parents=True,exist_ok=True);assert p.is_file(),str(name)
  if q.exists()and sha(q)!=sha(p):assert expected.get(name.as_posix())==sha(q),('Unowned archive conflict',name)
  if not q.exists()or sha(q)!=sha(p):shutil.copyfile(p,q)
  assert sha(p)==sha(q)
 for name in names:copy(name)
 for run in (['pigment-run','pigment-motion']if final else['phase-run','motion-run']):
  root=g/run;s=read(next(root.glob('STATE113-*-finished.json')));assert s['PlayExited']and not s.get('error')and not s.get('restorationError')
  for n in ['RUN_Capture25.cs.txt','RUN_Capture25.cs.diagnostics.txt','GLOBAL_NAMES66.json','PHASE_REQUEST.json','PHASE_REPLY.json','PHASE_RELAY_EOF.json','NATIVE_BEFORE73.json']:copy(root.relative_to(H)/n)
  for p in [next(root.glob('STATE113-*-ready-before-Play.json')),next(root.glob('STATE113-*-normal-Play-exit-requested.json')),next(root.glob('STATE113-*-finished.json'))]:copy(p.relative_to(H))
  for p in(root/'results').iterdir():
   if p.is_file():copy(p.relative_to(H))
  archive=DEST/root.relative_to(H)/('ACTUAL_GPU_FINAL27.zip'if final else'ACTUAL_GPU_PACKETS27.zip');entries=[]
  with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   for pkt in s['sequencePackets']:
    folder=Path(pkt['output']);assert(folder/'RAW_COMPLETE76.marker').read_text().strip()==sha(folder/'RAW_MANIFEST.json')
    for p in sorted(folder.iterdir()):
     assert p.is_file();name=p.relative_to(root).as_posix();z.write(p,name);entries.append({'file':name,'bytes':p.stat().st_size,'sha256':sha(p),'sourceId':pkt['sourceId']})
  with zipfile.ZipFile(archive)as z:
   assert z.testzip()is None
   for v in entries:assert hashlib.sha256(z.read(v['file'])).hexdigest()==v['sha256']
  (archive.parent/('PACKET_INDEX_FINAL27.json'if final else'PACKET_INDEX27.json')).write_text(json.dumps({'actualGPU':True,'frames':len(s['sequencePackets']),'archive':archive.name,'sha256':sha(archive),'entries':entries,'scope':'Actual27 source IDs; original geometry uploads labelled separately from GPU readback. Existing absolute paths are review evidence, not automatic execution.'},indent=2)+'\n',encoding='utf-8')
 files=[{'file':p.relative_to(DEST).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(DEST.rglob('*'))if p.is_file()]
 data={'files':files,'latestActualFrames':32,'latestStatus':'surface27/STATUS27.json','previousManifestScope':'Earlier manifests describe their historical snapshots. This final manifest supersedes current root hashes; pre-alpha27 runs are provisional.'if final else'ARCHIVE_MANIFEST26 describes the808fa542 historical tree; this27 manifest supersedes current root file hashes.','product77DefaultChanged':False}
 (DEST/finalName).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');(H/finalName).write_bytes((DEST/finalName).read_bytes())
 print(json.dumps({'archiveFiles':len(files),'latestFrames':32,'totalBytes':sum(v['bytes']for v in files)}))
if __name__=='__main__':surface27('--pigment'in sys.argv)if '--surface'in sys.argv or '--pigment'in sys.argv else main()
