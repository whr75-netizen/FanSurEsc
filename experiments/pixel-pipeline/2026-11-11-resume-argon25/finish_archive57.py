"""Finish only the already-staged owned snapshot after checking valid patch context."""
from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def main():
 assert not(H/'face57/COMMIT57.json').exists()
 manifest=json.loads((H/'face57/ARCHIVE57.json').read_text());assert git('rev-parse','HEAD')==manifest['baseCommit']
 names=[P+'/'+x['path']for x in manifest['files']]+[P+'/face57/ARCHIVE57.json','docs/ai/PIXEL_ALBEDO_20261030.md'];assert set(git('diff','--cached','--name-only').splitlines())==set(names)
 assert all(sha(R/P/x['path'])==x['SHA256']==sha(H/x['path'])for x in manifest['files'])
 user=json.loads((H/'face55/BEFORE_GIT55.json').read_text())['user30'];assert all(sha(R/p)==v for p,v in user.items())
 patches=[x for x in names if x.endswith('.patch')]
 # difflib did not emit the mandatory no-final-newline marker for added56 code.
 # Repair the convenience diff only; the exact executed C# source stays untouched.
 patch56=P+'/face56/from50.patch';raw=(R/patch56).read_bytes()
 if not raw.endswith(b'\n'):
  assert raw.endswith(b'+}')
  raw+=b'\n\\ No newline at end of file\n';local=H/'face56/from50.patch';local.write_bytes(raw);(R/patch56).write_bytes(raw)
  row=next(x for x in manifest['files']if x['path']=='face56/from50.patch');row['bytes']=len(raw);row['SHA256']=sha(local)
 # A unified diff's unchanged empty context line is exactly one space. Preserve
 # that required syntax, parse the patch, and check whitespace on every other file.
 for p in patches:
  lines=(R/p).read_text().splitlines();assert all(line==' 'for line in lines if line and line[-1].isspace());git('apply','--numstat',str(R/p))
 checked=[x for x in names if x not in patches]
 subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--',*checked],cwd=R,check=True)
 extras=['face57/LIBRARY_RESULT57.json','finish_archive57.py']
 for p in extras:
  dest=R/P/p;assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((H/p).read_bytes());assert sha(dest)==sha(H/p)
  manifest['files'].append({'path':p,'bytes':(H/p).stat().st_size,'SHA256':sha(H/p)})
 manifest['patchWhitespaceReview']={'unchangedEmptyContextIsOneSpace':True,'gitApplyNumstatParsed':patches,'allOtherStagedFilesWhitespaceChecked':True}
 (H/'face57/ARCHIVE57.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n');(R/P/'face57/ARCHIVE57.json').write_bytes((H/'face57/ARCHIVE57.json').read_bytes())
 names += [P+'/'+p for p in extras];git('add','--',*[P+'/'+p for p in extras],patch56,P+'/face57/ARCHIVE57.json');assert set(git('diff','--cached','--name-only').splitlines())==set(names)
 subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--',*[x for x in names if x not in patches]],cwd=R,check=True)
 body=H/'face57/COMMIT_BODY57.txt';body.write_text('Resume native source-domain capture after verified normal Editor restart\n\nVerify one approved standard save, exact serialized/disk preservation, normal same-project restart and zero retained diagnostic resources. Observe the completed second main-camera render while retaining fail-closed completion and cleanup.\n\nPreserve failed56 and actual57 raw evidence:45 ordinary carriers pass geometry;27 eye-domain cells stay separate; native composite matches CPU bytes. Reject over-dark chin contour; full-face palette/width/history remain incomplete. Correct the input receipt schema check without changing original evidence.\n\nOwned snapshots and handoff only; user30/product77 preserved. No push.\n',encoding='utf-8')
 print(git('commit','--file',str(body)));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in user.items())
 result={'commit':git('rev-parse','HEAD'),'files':len(names),'user30Equal':True,'product77Changed':False,'standardSaveExecuted':True,'normalRestartExecuted':True,'actualGPUCapture57Complete':True,'candidateAdopted':False,'push':False};(H/'face57/COMMIT57.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
