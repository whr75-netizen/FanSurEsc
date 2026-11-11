"""Archive only this completed support/gate work; preserve all originals."""
from pathlib import Path
import hashlib,json,shutil,sys,zipfile
H=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-11-resume-argon25/producer/support'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 if DEST.exists():
  assert '--resume-verified-partial'in sys.argv,'Existing archive must be inspected, never overwritten'
  for q in DEST.rglob('*'):
   if not q.is_file():continue
   name=q.relative_to(DEST);original=H/name
   assert original.is_file(),'Unexpected partial archive file: '+str(name)
   assert sha(q)==sha(original)or(str(name)=='archive_support.py'and sha(q)=='191239bab74d0387446bffe465948db7a78c37c611fd366feb26cb549d3ff804'),'Partial archive mismatch: '+str(name)
 assert DEST.resolve().is_relative_to((REPO/'experiments/pixel-pipeline').resolve())
 names=[p.relative_to(H)for p in H.iterdir()if p.is_file()and p.suffix in['.py','.cs','.png']]
 names += [Path(n)for n in ['PREPARED26.json','CPU_DOMAIN26.json','GPU_SUPPORT26.json','SOURCE_GATE26.json','SHARED_SOURCE_MASK26.json','GPU_GATE26.json','GPU_MOTION26.json','GATE_CAUSAL26.json','ROTATION_REJECTIONS26.json','MEMORY26.json','PRESERVED26.json','STATUS26.json','LIBRARY_FILES26.json','OS_POST26.json','Forward113_Support26.cs.txt']]
 for rootName in ['preflight','postflight']:
  names += [Path(rootName)/n for n in ['ReadState.cs.txt','READ_REQUEST.json','READ_REPLY.json','READ_RELAY_EOF.json']]
 for rootName,sourceName in [('gate','SharedSkin26.compute'),('gate-alpha','SharedSource26.compute')]:
  names += [Path(rootName)/n for n in [sourceName,'RUN_Import25.cs.txt','RUN_Import25.cs.diagnostics.txt','relay.py','LIVE_PREPARED.json','CPU_HLSL_GATE26.json','IMPORT_REQUEST.json','IMPORT_REPLY.json','IMPORT_RELAY_EOF.json','import/INTENT.json','import/COMPLETE.json','import/BEFORE.json','import/AFTER.json']]
 names += [Path('gate/PREPARED_GATE26.json'),Path('gate-alpha/CAPTURE_OBSERVER_UPDATE26.json'),Path('gate-alpha/MOTION_PREPARED.json'),Path('gate-alpha/relay_motion.py')]
 rows=[]
 assert all((H/name).is_file()for name in names),'Check all selected sources before copy'
 def copy(name):
  p=H/name;q=DEST/name;assert p.is_file(),p;q.parent.mkdir(parents=True,exist_ok=True)
  if q.exists()and sha(q)!=sha(p):assert str(name)=='archive_support.py'and sha(q)=='191239bab74d0387446bffe465948db7a78c37c611fd366feb26cb549d3ff804'
  if not q.exists()or sha(q)!=sha(p):shutil.copyfile(p,q)
  assert sha(p)==sha(q)
  rows.append({'file':str(name),'bytes':p.stat().st_size,'sha256':sha(p)})
 for name in names:copy(name)
 for runName in ['phase-run','gate/phase-run','gate-alpha/phase-run','gate-alpha/motion-run']:
  root=H/runName;end=next(root.glob('STATE113-*-finished.json'));state=read(end)
  assert state['PlayExited']and not state.get('error')and not state.get('restorationError')
  for n in ['RUN_Capture25.cs.txt','RUN_Capture25.cs.diagnostics.txt','GLOBAL_NAMES66.json','PHASE_REQUEST.json','PHASE_REPLY.json','PHASE_RELAY_EOF.json','NATIVE_BEFORE73.json']:
   copy(Path(runName)/n)
  for p in [sorted(root.glob('STATE113-*-ready-before-Play.json'))[0],next(root.glob('STATE113-*-normal-Play-exit-requested.json')),end]:copy(p.relative_to(H))
  for p in (root/'results').glob('*')if(root/'results').exists()else[]:copy(p.relative_to(H))
  archive=DEST/runName/'ACTUAL_GPU_PACKETS26.zip';index=[]
  with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   for packet in state['sequencePackets']:
    p=Path(packet['output'])
    for f in sorted(p.iterdir()):
     assert f.is_file();arc=f.relative_to(root).as_posix();z.write(f,arc);index.append({'file':arc,'bytes':f.stat().st_size,'sha256':sha(f),'sourceId':packet['sourceId']})
  with zipfile.ZipFile(archive)as z:
   assert z.testzip()is None
   for v in index:assert hashlib.sha256(z.read(v['file'])).hexdigest()==v['sha256']
  (archive.parent/'PACKET_INDEX26.json').write_text(json.dumps({'actualGPU':True,'archive':archive.name,'archiveSHA256':sha(archive),'sourceCount':len(state['sequencePackets']),'entries':index,
   'nativeRawBackup':'Original workspace only; original paths and source IDs are retained, never mixed.','replayLimits':'External runners preserve original frozen-workspace paths. Archive is review evidence, not an automatically portable or authorized execution.'},indent=2)+'\n',encoding='utf-8')
 (H/'ARCHIVED26.json').write_text(json.dumps({'destination':str(DEST),'copiedOwnFiles':rows},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'copiedOwnFiles':len(rows),'actualFrames':38,'destination':str(DEST),'archiveMiB':sum(p.stat().st_size for p in DEST.rglob('*')if p.is_file())/1048576}))
if __name__=='__main__':main()
