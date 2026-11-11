"""Copy this completed candidate/evidence only. No Unity or Git mutation."""
from pathlib import Path
import hashlib,json,shutil,zipfile
H=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-11-resume-argon25/producer'
FILES=[
 'HeadHair25.cs','Forward113_HeadHair25.cs','HeadHair25.shader','ForwardEye113_HeadHair25.compute',
 'prepare.py','prepare_live.py','test_cpu.py','compile_cpu.py','verify_gpu.py','relay.py','archive25.py',
 'HOST_CPU_ONLY.cs.txt','RUN_Import25.cs.txt','CONTRACT.json','PREPARED.json','LIVE_PREPARED.json',
 'CPU_COMPILE.json','CPU_DIAGNOSTICS.txt','CPU_PRODUCER.json','CPU_GPU_HAIR25.json','GPU_RESULT25.json',
 'PRESERVED25.json','DEPENDENCIES25.json','EYE_COMPARE25.png',
 'import/INTENT.json','import/COMPLETE.json','import/BEFORE.json','import/AFTER.json',
 'IMPORT_REQUEST.json','IMPORT_REPLY.json','IMPORT_RELAY_EOF.json',
 'phase-run/RUN_Capture25.cs.txt','phase-run/RUN_Capture25.cs.diagnostics.txt',
 'phase-run/STATE113-0000-ready-before-Play.json','phase-run/STATE113-0007-normal-Play-exit-requested.json',
 'phase-run/STATE113-0008-finished.json','phase-run/NATIVE_BEFORE73.json','phase-run/RESULT_FULL24.json',
 'phase-run/PHASE_REQUEST.json','phase-run/PHASE_REPLY.json','phase-run/PHASE_RELAY_EOF.json',
 'phase-run/results/00-control.png','phase-run/results/00-candidate.png',
 'phase-run/results/01-control.png','phase-run/results/01-candidate.png',
 'phase-run/results/00-control-eye.png','phase-run/results/00-candidate-eye.png',
 'phase-run/results/01-control-eye.png','phase-run/results/01-candidate-eye.png',
 'phase-run/results/SEQUENCE_FULL24.webp']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert DEST.resolve().is_relative_to((REPO/'experiments/pixel-pipeline').resolve())
 assert not DEST.exists(),'Archive already exists; inspect before any update'
 state=json.loads((H/'phase-run/STATE113-0008-finished.json').read_text())
 assert state['PlayExited']and state['forward102Disposed']and not state.get('error')and not state.get('restorationError')
 rows=[]
 for name in FILES:
  p=H/name;q=DEST/name;assert p.is_file(),p
  q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);assert sha(p)==sha(q)
  rows.append({'file':name,'bytes':p.stat().st_size,'sha256':sha(p)})
 index=[];zpath=DEST/'phase-run/ACTUAL_GPU_PACKETS25.zip'
 with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for packet in state['sequencePackets']:
   p=Path(packet['output'])
   for f in sorted(p.iterdir()):
    assert f.is_file()
    arc=f.relative_to(H/'phase-run').as_posix();z.write(f,arc)
    index.append({'file':arc,'bytes':f.stat().st_size,'sha256':sha(f),'sourceId':packet['sourceId']})
 with zipfile.ZipFile(zpath)as z:
  assert z.testzip()is None
  for v in index:assert hashlib.sha256(z.read(v['file'])).hexdigest()==v['sha256']
 evidence={'actualGPU':True,'sourceIdCount':2,'noCPUReplacement':True,'archive':zpath.name,
  'archiveSHA256':sha(zpath),'archiveBytes':zpath.stat().st_size,'entries':index,
  'extraction':'Extract without overwriting into a fresh phase-run directory. Raw manifests preserve original sourceId/output declarations.',
  'nativeBackups':'Full before-native JSON remains in original workspace; repository keeps content hashes and comparisons only.',
  'replayLimits':'These external runners retain absolute paths to the original frozen workspace. Copying this archive does not authorize re-execution or make the full Unity host portable.'}
 (DEST/'phase-run/PACKET_INDEX25.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
 (H/'ARCHIVED25.json').write_text(json.dumps({'destination':str(DEST),'files':rows,'packetArchiveSHA256':sha(zpath)},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'copiedOwnFiles':len(rows),'rawPacketFiles':len(index),'rawZipMiB':zpath.stat().st_size/1048576,'destination':str(DEST)}))
if __name__=='__main__':main()
