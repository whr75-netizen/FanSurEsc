from pathlib import Path
import hashlib,json,zipfile,sys
H=Path(__file__).resolve().parent;G=H/'face37';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');D=R/'experiments/pixel-pipeline/2026-11-11-resume-argon25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf-8',newline='\n')
def data(p):return json.loads(json.loads(p.read_text())['result']['content'][0]['text'])['data']
def main():
 user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert all(sha(R/p)==v for p,v in user.items())
 prior=json.loads((D/'face36/ARCHIVE36.json').read_text());assert all(sha(D/p['path'])==p['SHA256']for p in prior['files'])
 r=json.loads((G/'capture/COMPLETE.json').read_text());a=json.loads((G/'analysis/SOURCE_ANCHOR37.json').read_text())
 assert r['restorationChecksPass']and r['ownedResourcesReleased']and r['pendingOwners']==0 and not r['errors']and a['samePoseFixedPoint']and a['firstROICPUByteMismatch']==0
 assert data(H/'face33/console/REPLY.json')==data(G/'console/REPLY.json')
 z=G/'ACTUAL_PACKET37.zip'
 if not z.exists():
  with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as out:
   for p in sorted((G/'capture').glob('*.f32')):out.write(p,p.name)
   out.write(G/'capture/COMPLETE.json','COMPLETE.json')
 with zipfile.ZipFile(z)as archive:assert archive.testzip()is None
 save(G/'STATUS37.json',{'baselineCommit':'6b441eb9','actualPlayCount':1,'samePoseSourceAnchorVerified':True,'actualFrames':a['actualFrames'],'firstCPUByteMismatch':0,'watchCPUComparisons':6,'original30Equal':True,'product77Changed':False,'finalRGBModified':False,'actualPhaseRotationBlinkTested':False,'state':'Edit/dirty31/GameMap1clean/input568105589213756420/optionsfalseNone','consoleSameAs33':True,'nativeEqual':46,'nativeUnavailable':1,'rawZipSHA256':sha(z),'memoryBefore':r['beforeMemory'],'memoryAfter':r['afterMemory'],'GPU115Calls':0,'CUA':0,'SaveAssets':0,'KillReset':0,'Push':0})
 roots=['SourceAnchor37.cs','AnchorTests37.cs','test_anchor37.py','prepare_anchor37.py','relay37.py','review_anchor37.py','archive_runtime37.py','commit_runtime37.py']
 selected=roots[:]
 for p in G.rglob('*'):
  if not p.is_file()or 'build'in p.parts or p.name.startswith(('native-before-','TRACE-','library-xattrs-'))or p.suffix in ['.f32','.bin']or p.name in ['ARCHIVE37.json','SCHEMA.json']:continue
  selected.append(str(p.relative_to(H)).replace('\\','/'))
 selected=sorted(set(selected));rows=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in selected];save(G/'ARCHIVE37.json',{'files':rows,'nativeBackupsAndBuildsExcluded':True,'actualDataZip':True})
 if '--publish'in sys.argv:
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';append=(G/'HANDOFF_APPEND37.md').read_bytes();before=doc.read_bytes()
  if not before.endswith(append):assert sha(doc)=='acbfca3e4c085f184e741c258a85a28ea2d6f72207feab4dacd9e78b1e919f4b'
  for row in rows+[{'path':'face37/ARCHIVE37.json','SHA256':sha(G/'ARCHIVE37.json')}]:
   src=H/row['path'];dst=D/row['path']
   if dst.exists():assert sha(dst)==row['SHA256'],'Existing differing file '+row['path']
   else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
  if not before.endswith(append):doc.write_bytes(before+append)
  assert all(sha(D/p['path'])==p['SHA256']for p in rows)and all(sha(R/p)==v for p,v in user.items())
 print(json.dumps({'files':len(rows)+1,'zipBytes':z.stat().st_size,'published':'--publish'in sys.argv,'original30Equal':True}))
if __name__=='__main__':main()
