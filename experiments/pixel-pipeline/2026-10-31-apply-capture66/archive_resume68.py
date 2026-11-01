"""Archive only completed resume diagnostics; no Unity commands or source-asset writes."""
from pathlib import Path
import hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-10-31-apply-capture66'
NAMES=['Resume68.cs','RESUME68.json','RESUME68_DISK.json','RESUME_RESULT68.json','CaptureRetry66.cs','relay66.py','build66.py','archive_resume68.py']
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='6a1f2f4a11636a40f008f4231cdcb513f22b6a21'
 assert not git('diff','--cached','--name-only'),'Preserve somebody else\'s staged work'
 baseline=json.loads((HERE/'RESUME68_DISK.json').read_text(encoding='utf-8'))
 for path,h in baseline['files'].items():assert hashlib.sha256((REPO/path).read_bytes()).hexdigest()==h,path
 assert not (HERE/'CaptureRetry66_REQUEST.json').exists()
 assert not (HERE/'retry-background/CAPTURE_STATE66.json').exists()
 paths=[]
 for name in NAMES:
  src=HERE/name;dst=DEST/name;shutil.copyfile(src,dst);assert src.read_bytes()==dst.read_bytes();paths.append(dst.relative_to(REPO).as_posix())
 paths.append('docs/ai/PIXEL_ALBEDO_20261030.md')
 git('add','--',*paths)
 assert set(git('diff','--cached','--name-only').splitlines())==set(paths)
 git('diff','--cached','--check')
 print(git('diff','--cached','--stat'),flush=True)
 message=HERE/'.commit-resume68.txt';message.write_text('Record current Unity relay baseline and blocked capture retry\n\nCurrent PID35364 official MCP read succeeded; snapshot ToJson dirtied Face Mesh without content hash change. Preserve user asset contents and track exact side effect. No extra Play or runInBackground change executed; automatic reviewer rejected resume as insufficient explicit approval. Document installed Assistant version, remembered direct-client approvals and separate current NoSubscription model-list errors. No product integration or art-success claim.\n',encoding='utf-8')
 print(git('commit','--file',str(message)),flush=True)
 assert not git('diff','--cached','--name-only')
 for path,h in baseline['files'].items():assert hashlib.sha256((REPO/path).read_bytes()).hexdigest()==h,path
 result={'commit':git('rev-parse','HEAD'),'paths':paths,'productFilesChanged':0,'baseline31HashesUnchanged':True,'retryExecuted':False,'stageEmpty':True}
 (HERE/'RESUME_COMMIT68.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
