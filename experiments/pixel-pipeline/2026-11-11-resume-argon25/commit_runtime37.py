from pathlib import Path
import json,hashlib,subprocess
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';D=R/P
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='6b441eb9e4c4bf1f9dfa3c7bed273a54a5542968'
 user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert all(sha(R/p)==v for p,v in user.items())
 m=json.loads((D/'face37/ARCHIVE37.json').read_text());assert all(sha(D/p['path'])==p['SHA256']for p in m['files'])
 names=[P+'/'+p['path']for p in m['files']]+[P+'/face37/ARCHIVE37.json','docs/ai/PIXEL_ALBEDO_20261030.md'];assert len(names)==len(set(names))and not(set(names)&set(user))
 staged=git('diff','--cached','--name-only').splitlines()
 if staged:assert set(staged)==set(names),'Unrelated staged files; stop'
 else:git('add','--',*names)
 assert set(git('diff','--cached','--name-only').splitlines())==set(names)
 c=subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=R,capture_output=True,text=True);assert c.returncode==0,c.stdout+c.stderr
 body=H/'face37/COMMIT_BODY.txt';body.write_text('Track native source anchors for consecutive Q-region validation\n\nConnect UV/triangle/barycentric provenance to evaluated mesh and read the corresponding footprint rather than fixed screen coordinates. Verify six controlled same-pose GPU frames, whole-ROI CPU parity and restored owned resources/state.\n\nKeep actual final RGB, face colour regions and final outline activation explicitly incomplete; preserve original user changes and product77.\n',encoding='utf-8');git('commit','--file',str(body));commit=git('rev-parse','HEAD');assert all(sha(R/p)==v for p,v in user.items())and not git('diff','--cached','--name-only')
 result={'commit':commit,'files':len(names),'original30Equal':True,'product77Changed':False,'push':False};(H/'face37/COMMIT37.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
