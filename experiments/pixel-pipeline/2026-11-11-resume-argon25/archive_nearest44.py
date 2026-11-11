from pathlib import Path
import hashlib,json,zipfile,subprocess,sys
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';D=R/P
BASE='1f31f2e5895216e3d9697547c5b2edbf1f15561e'
ROOTS=['CurveCarrier43.cs','CurveCarrierTests43.cs','ReplayCarrier43.cs','test_carrier43.py','ContourPayload44.cs','GeoContour44.shader','PairedCurve44.cs','prepare_nearest44.py','prepare_world44.py','relay44.py','review_nearest44.py','audit_nearest44.py','archive_nearest44.py']
ASSETS=['Assets/EUnityValidation01/SourceBoundary44.meta','Assets/EUnityValidation01/SourceBoundary44/GeoContour44.shader','Assets/EUnityValidation01/SourceBoundary44/GeoContour44.shader.meta']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,indent=2),encoding='utf-8',newline='\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def zip_sources(dst,paths):
 if not dst.exists():
  with zipfile.ZipFile(dst,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   for p in sorted(paths):z.write(p,p.relative_to(H).as_posix())
 with zipfile.ZipFile(dst)as z:
  assert z.testzip()is None and set(z.namelist())=={p.relative_to(H).as_posix()for p in paths}
  for p in paths:assert hashlib.sha256(z.read(p.relative_to(H).as_posix())).hexdigest()==sha(p)
def main():
 assert git('rev-parse','HEAD')==BASE
 users=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(users)==30 and all(sha(R/p)==v for p,v in users.items())
 assert not git('diff','--cached','--name-only'),'Do not mix existing staged changes'
 status=json.loads((H/'face44/STATUS44.json').read_text());assert status['fixed44Provenance']['unknown']==0 and all(x['restored']and x['CPUExactFrames']==6 for x in status['cases'].values())
 assert sha(H/'GeoContour44.shader')==sha(H/'face44/shaders/GeoContour44.shader')==sha(R/ASSETS[1])
 raw=[]
 for c in [H/'face44/capture',H/'face44/world/capture']:
  raw.extend(p for p in c.iterdir()if p.suffix=='.f32' or p.name.startswith('geometry-frame')or p.name=='COMPLETE.json')
 zip_sources(H/'face44/ACTUAL_PACKETS44.zip',raw)
 zip_sources(H/'face43/ACTUAL_INPUTS43.zip',[H/'face43/ACTUAL_INPUT43.bin',H/'face43/nearest44/ACTUAL_INPUT43.bin'])
 selected=ROOTS[:]
 for root in [H/'face43',H/'face44']:
  for p in root.rglob('*'):
   if not p.is_file()or'build'in p.parts or p.name.startswith(('native-before-','TRACE-','library-xattrs-'))or p.suffix in ['.f32','.bin','.dll','.pdb','.rsp']or p.name in ['ARCHIVE44.json','COMMIT44.json','COMMIT_BODY44.txt','SCHEMA.json']:continue
   selected.append(p.relative_to(H).as_posix())
 selected=sorted(set(selected));rows=[{'path':p,'SHA256':sha(H/p),'bytes':(H/p).stat().st_size}for p in selected]
 save(H/'face44/ARCHIVE44.json',{'baselineCommit':BASE,'files':rows,'assets':[{'path':p,'SHA256':sha(R/p)}for p in ASSETS],'rawPacketsSHA256':sha(H/'face44/ACTUAL_PACKETS44.zip'),'CPUFixturesSHA256':sha(H/'face43/ACTUAL_INPUTS43.zip'),'nativeBackupsAndBuildsExcluded':True})
 if'--publish'in sys.argv:
  for row in rows+[{'path':'face44/ARCHIVE44.json','SHA256':sha(H/'face44/ARCHIVE44.json')}] :
   src=H/row['path'];dst=D/row['path']
   if dst.exists():assert sha(dst)==row['SHA256'],'Existing snapshot differs: '+row['path']
   else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';old=doc.read_bytes();add=(H/'face44/HANDOFF_APPEND44.md').read_bytes()
  if not old.endswith(add):
   assert '### 원본 곡선 carrier·실제 native 최종 가림 후속43–44'.encode()not in old
   doc.write_bytes(old+add)
  assert all(sha(D/x['path'])==x['SHA256']for x in rows)and all(sha(R/p)==v for p,v in users.items())
 print(json.dumps({'files':len(rows)+1,'bytes':sum(x['bytes']for x in rows),'published':'--publish'in sys.argv,'user30Equal':True,'product77Changed':False}))
 if'--commit'in sys.argv:
  assert'--publish'in sys.argv
  names=[P+'/'+x['path']for x in rows]+[P+'/face44/ARCHIVE44.json','docs/ai/PIXEL_ALBEDO_20261030.md']+ASSETS
  assert len(names)==len(set(names))and not set(names)&set(users) and not git('diff','--cached','--name-only')
  git('add','--',*names);assert set(git('diff','--cached','--name-only').splitlines())==set(names)
  result=subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--','.',':(exclude)*.meta'],cwd=R,capture_output=True,text=True);assert result.returncode==0,result.stdout+result.stderr
  body=H/'face44/COMMIT_BODY44.txt';body.write_text('Keep raster contour source points on their finite native carriers\n\nReplace extrapolated hardware line t with a closest finite source-segment point and reconstruct source depth/width explicitly. Preserve registered topology, both seam UV carriers, and exact native/world sampling in a private diagnostic RT. Verify old/new same-input GPU rasters, twelve walk/turn frames and 176 saved source samples, with restored state and resources.\n\nKeep product77/default and user changes intact. Leave face palette segmentation, variable-width rasterization, final owner/history and temporal art quality incomplete.\n',encoding='utf-8')
  git('commit','--file',str(body));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in users.items())
  save(H/'face44/COMMIT44.json',{'commit':git('rev-parse','HEAD'),'files':len(names),'original30Equal':True,'product77Changed':False,'push':False});print((H/'face44/COMMIT44.json').read_text())
if __name__=='__main__':main()
