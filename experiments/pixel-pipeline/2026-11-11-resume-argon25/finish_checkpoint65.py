"""Finish already copied owned files after Windows rejected argv before git add."""
from pathlib import Path
import subprocess,json,hashlib
from archive_checkpoint65 import H,R,P,BASE,sha,git,load,save
def main():
 assert git('rev-parse','HEAD')==BASE and not git('diff','--cached','--name-only')
 user=load(H/'face55/BEFORE_GIT55.json')['user30'];assert all(sha(R/p)==v for p,v in user.items())
 disk=load(H/'face55/backup/DISK_BEFORE.json');assert all((R/x['path']).exists()==x['exists'] and(not x['exists']or sha(R/x['path'])==x['sha256'])for x in disk)
 manifest=H/'face65/ARCHIVE65.json';m=load(manifest);old=sha(manifest);targetManifest=R/P/'face65/ARCHIVE65.json';assert sha(targetManifest)==old
 for row in m['files']:
  target=R/P/row['path'];assert sha(target)==row['SHA256']
  if row['path']=='archive_checkpoint65.py':
   # Only the owned publication helper changed; actual GPU RUN inputs and
   # receipts remain exactly as executed. Use stdin pathspecs, not long argv.
   target.write_bytes((H/row['path']).read_bytes());row.update(bytes=target.stat().st_size,SHA256=sha(target))
  else:assert sha(H/row['path'])==row['SHA256']
 me=Path(__file__).resolve();target=R/P/me.name;assert not target.exists();target.write_bytes(me.read_bytes());m['files'].append({'path':me.name,'bytes':me.stat().st_size,'SHA256':sha(me)})
 m['publicationFix']='WinError206 occurred before git process creation; exact owned paths staged with NUL stdin pathspecs.';save(manifest,m);targetManifest.write_bytes(manifest.read_bytes())
 names=[P+'/'+x['path']for x in m['files']]+[P+'/face65/ARCHIVE65.json','docs/ai/PIXEL_ALBEDO_20261030.md'];assert not set(names).intersection(user)
 subprocess.run(['git','add','--pathspec-from-file=-','--pathspec-file-nul'],cwd=R,input=('\0'.join(names)+'\0').encode('utf-8'),check=True)
 assert set(git('diff','--cached','--name-only').splitlines())==set(names)
 check=subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=R,capture_output=True,text=True,encoding='utf-8');assert check.returncode==0,check.stdout+check.stderr
 body=H/'face65/COMMIT_BODY65.txt';body.write_text('Validate authored outline motion and recover selected surface shade receipts\n\nFix bounded six-owner readback scheduling without timeout extension or new shader work. Preserve failed63/64 evidence. Six real normal-input frames and24 width cases match CPU RGB/owner/layer; retain original77 and user edits.\n\nAdapt observed selected-surface Q from UV receipt to existing52 supplier;264 CPU checks and31 actual consumer-guard checks. Full-face region/family mapping and stable pixel-art stroke policy remain incomplete; do not promote calibration or thin raster flicker to success.\n',encoding='utf-8')
 print(git('commit','--file',str(body)));assert not git('diff','--cached','--name-only') and all(sha(R/p)==v for p,v in user.items())
 receipt={'commit':git('rev-parse','HEAD'),'files':len(names),'product77DefaultChanged':False,'user30Exact':True,'protected128Exact':True,'actualGPUFrames':6,'CPUExactCases':24,'CPUSelectedShadeTests':264,'consumerChecks':31,'fullFaceLUTApplied':False,'longTermStabilityValidated':False,'push':False};save(H/'face65/COMMIT65.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':main()
