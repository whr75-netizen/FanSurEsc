"""Archive this completed single-source packet, scripts and evidence only. No Unity calls."""
from pathlib import Path
import hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-10-31-apply-capture66'
NAMES=['build66.py','relay66.py','Post68.cs','Option68.cs','analyse_capture68.py','test_reader68.py','archive_capture68.py','BEFORE_PLAY68.json','POST_PLAY68.json','TARGET_OPTION68.json','CAPTURE_RESULT68.json','EYE_OBSERVER68.patch','RUN_CaptureRetry66.cs.txt','CaptureRetry66_REQUEST.json','CaptureRetry66_REPLY.json']
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='ca28421f96a479104f3cd5432054d6d12e850487'
 assert not git('diff','--cached','--name-only'),'Preserve other staged work'
 baseline=json.loads((HERE/'RESUME68_DISK.json').read_text(encoding='utf-8'))
 for p,h in baseline['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 result=json.loads((HERE/'CAPTURE_RESULT68.json').read_text(encoding='utf-8'));assert result['PlayEntries']==1 and result['PlayExited'] and result['observerRemoved'] and not result['error']
 packet=Path(json.loads((HERE/'retry-background/CAPTURE_STATE66.json').read_text())['output']);assert packet.parent==HERE/'retry-background'
 sources=[HERE/n for n in NAMES]+[HERE/'retry-background/CAPTURE_STATE66.json',HERE/'retry-background/WAIT_TRACE.jsonl']+sorted(p for p in packet.rglob('*') if p.is_file())
 assert len(sources)<130 and sum(p.stat().st_size for p in sources)<32*1024*1024
 paths=[];total=0
 for src in sources:
  rel=src.relative_to(HERE);dst=DEST/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert hashlib.sha256(src.read_bytes()).digest()==hashlib.sha256(dst.read_bytes()).digest();paths.append(dst.relative_to(REPO).as_posix());total+=src.stat().st_size
 paths.append('docs/ai/PIXEL_ALBEDO_20261030.md');git('add','--',*paths)
 staged=git('diff','--cached','--name-only').splitlines();assert set(staged)==set(paths);git('diff','--cached','--check')
 print(json.dumps({'staged':len(staged),'copiedBytes':total,'sourceId':result['sourceId']},ensure_ascii=False),flush=True)
 msg=HERE/'.commit-capture68.txt';msg.write_text('Capture one restored Play packet and validate surface provenance\n\nExplicitly approved background-enabled Play ran once, reached frame94/serial1 and captured66 bounded planes with evaluated geometry and camera provenance. Verify actual material-local BodyScope bindings, native content5 and74named globals; restore Play/options/pipeline/time/background. Retain dirty flag additions and disclose PlayerSettings full-native baseline gap and internal allocated+454.557MiB. Map all1734native samples uniquely to source triangles/UV/material with max reprojection0.002593px. Preserve raw packet, previews and missing eye observer buffers; prepare unapplied direct-host lookup patch only. No product/art/temporal-success claim or push.\n',encoding='utf-8')
 print(git('commit','--file',str(msg)),flush=True)
 assert not git('diff','--cached','--name-only')
 for p,h in baseline['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 receipt={'commit':git('rev-parse','HEAD'),'paths':len(staged),'copiedBytes':total,'sourceId':result['sourceId'],'productFilesChanged':0,'baseline31HashesUnchanged':True,'stageEmpty':True}
 (HERE/'CAPTURE_COMMIT68.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
