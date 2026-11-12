"""Commit the reviewed staged snapshot without rewriting Unity-generated metadata or executed bytes."""
from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def main():
 assert not(H/'face62/COMMIT62.json').exists();m=json.loads((H/'face62/ARCHIVE62.json').read_text());assert git('rev-parse','HEAD')==m['baseCommit']
 names=[P+'/'+r['path']for r in m['files']]+[P+'/face62/ARCHIVE62.json','docs/ai/PIXEL_ALBEDO_20261030.md']+[a['path']for a in m['ownedNewAssets']];assert set(git('diff','--cached','--name-only').splitlines())==set(names)
 assert all(sha(R/P/x['path'])==x['SHA256']==sha(H/x['path'])for x in m['files']);assert all(sha(R/x['path'])==x['SHA256']for x in m['ownedNewAssets'])
 user=json.loads((H/'face55/BEFORE_GIT55.json').read_text())['user30'];assert all(sha(R/p)==v for p,v in user.items())
 patches=[p for p in names if p.endswith('.patch')]
 for p in patches:git('apply','--numstat',str(R/p))
 meta=[p for p in names if p.endswith('.meta')]
 for p in meta:
  text=(R/p).read_text();assert 'guid:'in text
  for line in text.splitlines():
   if line and line[-1].isspace():assert line.strip()in['userData:','assetBundleName:','assetBundleVariant:']
 computes=['Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.compute',P+'/face62/shaders/SourceNativeHull60.compute']
 for p in computes:
  lines=(R/p).read_text().splitlines();assert lines[-1]==''and all(not line or not line[-1].isspace()for line in lines)
 excluded=patches+meta+computes
 subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--',*[p for p in names if p not in excluded]],cwd=R,check=True)
 m['whitespaceReview']={'patchesParsed':patches,'UnityGeneratedEmptyMetaScalarsPreserved':meta,'executedComputeFinalEmptyLinePreserved':computes,'allOtherFilesChecked':True}
 extra='finish_checkpoint62.py';target=R/P/extra;assert not target.exists();target.write_bytes((H/extra).read_bytes());m['files'].append({'path':extra,'bytes':(H/extra).stat().st_size,'SHA256':sha(H/extra)});(H/'face62/ARCHIVE62.json').write_text(json.dumps(m,indent=2),encoding='utf-8',newline='\n');(R/P/'face62/ARCHIVE62.json').write_bytes((H/'face62/ARCHIVE62.json').read_bytes());names.append(P+'/'+extra);git('add','--',P+'/'+extra,P+'/face62/ARCHIVE62.json');assert set(git('diff','--cached','--name-only').splitlines())==set(names)
 body=H/'face62/COMMIT_BODY62.txt';body.write_text('Use authored face-outline width and compose below confirmed eye children\n\nUse the current original material and actual MToon hull instead of forced one-cell curves. Keep finite source ink and actual primitive/UV ownership in a private path; product77 default unchanged.\n\nActual width0/1/8/32 exposed6 child-eye overwrites. Verify corrected parent composition in4 GPU cases and59 positive final-owner/UV/layer samples against CPU. Preserve skin canvas, hair/world gates and all lifetime/restoration checks.\n\nPreserve failed58/59 provenance guards and raw60/61/62 evidence. Full-face colour regions, runtime history, long-term motion and art approval remain incomplete.\n',encoding='utf-8');print(git('commit','--file',str(body)));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in user.items());data={'commit':git('rev-parse','HEAD'),'files':len(names),'product77DefaultChanged':False,'user30Equal':True,'ownedAssets':[a['path']for a in m['ownedNewAssets']],'actualGPUCases':4,'positiveOwnerSamples':59,'artAdopted':False,'push':False};(H/'face62/COMMIT62.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data))
if __name__=='__main__':main()
