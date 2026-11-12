"""Preserve exact Unity metadata / executed EOF while checking all other whitespace."""
from pathlib import Path
import json,subprocess
from archive_checkpoint65 import H,R,P,sha,git,load,save
def main():
 assert git('rev-parse','HEAD')=='558bcc81dc13ad0f826c6644432be35ac88777dd'
 m=load(H/'face66/ARCHIVE66.json');names=[P+'/'+x['path']for x in m['files']]+[P+'/face66/ARCHIVE66.json','docs/ai/PIXEL_ALBEDO_20261030.md','Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.compute']
 assert set(git('diff','--cached','--name-only').splitlines())==set(names)
 for x in m['files']:assert sha(R/P/x['path'])==x['SHA256']==sha(H/x['path'])
 user=load(H/'face55/BEFORE_GIT55.json')['user30'];assert all(sha(R/p)==v for p,v in user.items())
 source='Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.compute';assert (R/source).read_bytes()==(H/'face66/shaders/SourceNativeHull60.compute').read_bytes()
 exceptions=[P+'/face66/import/OWNED_BEFORE.compute',P+'/face66/import/OWNED_BEFORE.meta',P+'/face66/shaders/SourceNativeHull60.compute']
 assert (R/exceptions[0]).read_bytes()==(H/'face62/shaders/SourceNativeHull60.compute').read_bytes()
 assert (R/exceptions[1]).read_bytes()==(R/(source+'.meta')).read_bytes()
 for p in exceptions:
  lines=(R/p).read_text().splitlines()
  for line in lines:
   if line.rstrip()!=line:assert p.endswith('.meta')and line in ['  userData: ','  assetBundleName: ','  assetBundleVariant: ']
 # Keep the exact backup/shader bytes. Strictly check all other changes using
 # a short exclusion pathspec instead of another long Windows argv.
 check=subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in exceptions]],cwd=R,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
 me=Path(__file__).resolve();target=R/P/me.name;assert not target.exists();target.write_bytes(me.read_bytes());git('add','--',P+'/'+me.name);names.append(P+'/'+me.name);assert set(git('diff','--cached','--name-only').splitlines())==set(names)
 body=H/'face66/COMMIT_BODY66.txt';body.write_text('Separate actor-exterior contours from native material hull decoration\n\nGeneric exterior class cannot overwrite current actor occupancy. Retain original hull as explicit same-frame control and keep product77 default. Six actual normal frames /30 width-class cases match CPU RGB/owner/layer; eliminate4 original-width clothing/hair dots and17-38 self-overwrites in large controls.\n\nPreserve actual source, input/settings/resources and user edits. Closed native-colour flank basins retain weak paint witness but whole-region extents disagree; do not infer full-face families or claim runtime history/LUT completion.\n',encoding='utf-8');git('commit','--file',str(body));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in user.items());r={'commit':git('rev-parse','HEAD'),'files':len(names),'user30Protected128Equal':True,'product77DefaultChanged':False,'actualGPUFrames':6,'actualCases':30,'runtimeHistoryOrFaceLUTComplete':False,'push':False};save(H/'face66/COMMIT66.json',r);print(json.dumps(r))
if __name__=='__main__':main()
