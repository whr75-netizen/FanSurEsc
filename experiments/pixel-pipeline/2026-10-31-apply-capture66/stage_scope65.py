"""Select only the65 product hunks, leaving pre-existing worktree changes unstaged."""
from pathlib import Path
import difflib,hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
BASE=HERE.parent/'body-scope65'
CLOTH='Assets/EUnityValidation01/ClothRegion524/Runtime/ClothRegion524.cs'
FULL='Assets/EUnityValidation01/MinimalRestore335/Runtime/Full319View335.cs'
def git(*args):return subprocess.run(['git','-C',str(REPO),*args],capture_output=True,text=True,encoding='utf-8',check=True).stdout
def changes(a,b):
 return [l for l in difflib.unified_diff(a.splitlines(),b.splitlines(),n=0) if (l.startswith('+') or l.startswith('-')) and not l.startswith(('+++','---'))]
def main():
 assert git('diff','--cached','--name-only')==''
 originals={p:git('show','HEAD:'+p) for p in [CLOTH,FULL]}
 # The cloth hunk is independent of the pre-existing profile547 edits.
 git('apply','--cached','--check','--include='+CLOTH,str(BASE/'body-scope65.patch'))
 head=originals[FULL];start=head.index('void OnDisable()');pos=head.index('  if(Active==this)Active=null;if(!ready)return;',start)
 new=head[:pos]+'  ClothRegion524.ReleaseScope551(this); // also runs after incomplete Initialise / cancelled capture\n'+head[pos:]
 patch=''.join(difflib.unified_diff(head.splitlines(True),new.splitlines(True),fromfile='a/'+FULL,tofile='b/'+FULL))
 index_patch=HERE/'FULL65_INDEX_ONLY.patch';index_patch.write_text(patch,encoding='utf-8',newline='\n')
 git('apply','--cached','--check',str(index_patch))
 # Confirm the actual worktree still equals the reviewed candidate (EOL normalization only).
 for p in [CLOTH,FULL]:assert (REPO/p).read_text(encoding='utf-8-sig')==(BASE/'candidate'/p).read_text(encoding='utf-8-sig')
 git('apply','--cached','--include='+CLOTH,str(BASE/'body-scope65.patch'))
 git('apply','--cached',str(index_patch))
 proof=[]
 for p in [CLOTH,FULL]:
  staged=git('show',':'+p);work=(REPO/p).read_text(encoding='utf-8-sig');before=(BASE/'before'/p).read_text(encoding='utf-8-sig')
  expected=changes(originals[p],before);actual=changes(staged,work)
  assert expected==actual,'Pre-existing delta differs after selective stage: '+p
  proof.append({'path':p,'preexistingChangedLinePayloadSame':True,'preexistingChangedPayloadLines':len(expected),'workingCopySHA256':hashlib.sha256((REPO/p).read_bytes()).hexdigest(),'stagedTextSHA256':hashlib.sha256(staged.encode()).hexdigest()})
 assert sorted(git('diff','--cached','--name-only').splitlines())==sorted([CLOTH,FULL])
 git('diff','--cached','--check')
 (HERE/'PRODUCT_STAGE_PROOF65.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(git('diff','--cached','--stat'))
 print(json.dumps(proof,ensure_ascii=False))
if __name__=='__main__':main()
