"""Selective evidence commit; excludes raw native snapshots and local transfers."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys,zipfile
H=Path(__file__).resolve().parent;B=H.parents[2]
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-02-bounded-form115/runtime24/full-render24/carrier-fix24'
DOC='docs/ai/PIXEL_ALBEDO_20261030.md';ASSET='Assets/EUnityValidation01/Direct24Carrier'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True,encoding='utf8').strip('\r\n')
def preserve(owned=()):
 b=read(B/'DISK_BOUND_BEFORE115.json')
 for path,digest in b['files'].items():assert sha(REPO/path)==digest,path
 allowed=set(owned)|{DOC};status=git('status','--porcelain','--untracked-files=no').splitlines()
 assert '\n'.join(x for x in status if x[3:]not in allowed)==b['modifiedStatus'].strip('\r\n'),'Original user status differs'
 n=B.parent/'gpu-form115';native=read(n/'NATIVE_BEFORE73.json');assert len(native)==47
 for r in native:assert(n/r['snapshot']).stat().st_size==r['bytes']and sha(n/r['snapshot'])==r['sha256']
 assert sha(REPO/'Assets/EUnityValidation01/Direct24Geometry/ForwardEye113_Geometry24.compute')==read(H/'PREPARED_FIX24.json')['baselineSHA256']
 assert sha(REPO/ASSET/'ForwardEye113_Geometry24.compute')==read(H/'PREPARED_FIX24.json')['sourceSHA256']
 return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalUser30Equal':True,'protected35Equal':True,'native47BackupEqual':True,'previousCandidateUnchanged':True,'product77DefaultChanged':False}
def copy():
 assert git('rev-parse','HEAD')=='cf4c72f00d140582546f57d35e4697846c74f161'
 assert not git('diff','--cached','--name-only')and not DEST.exists()
 before=preserve();r=read(H/'VALIDATED_FIX24.json');assert r['actualGPUFrames']==40 and r['eyePaletteRGB8Errors']==0
 packets=[];runs=[]
 for key in ['close','motion']:
  s=read(next((H/key).glob('STATE113-*-finished.json')))
  assert s['PlayExited']and not s.get('error')and not s.get('restorationError')and all(x['equal']for x in s['nativeComparisons72'])
  assert not s['globalRestoreErrors']and s['motionRestoration82']['allRestored']
  assert s['forward102Disposed']and s['layer102Disposed']and s['carrierNativeDisposed111']and s['carrierSourceDisposed111']
  for p in s['sequencePackets']:
   path=Path(p['output']);assert sha(path/'RAW_MANIFEST.json')==(path/'RAW_COMPLETE76.marker').read_text().strip()
   packets.append({**p,'run':key,'archiveRoot':key+'/'+path.parent.name+'/'+path.name})
  runs.append({'name':key,'frames':len(s['sequencePackets']),'nativeContents':len(s['nativeComparisons72']),'allContentsEqual':True,'sceneEqual':s['beforeScenes']==s['afterScenes'],'input':s['editInputRestoration82'],'options':{k:s[k]for k in ['PlayExited','backgroundRestored','playerSettingsRunInBackgroundRestored','optionsRestored','timeRestored','pipelineRestored']}})
 archive=H/'RAW_FIX24.zip';assert not archive.exists()
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p in packets:
   for f in sorted(Path(p['output']).iterdir()):assert f.is_file();z.write(f,p['archiveRoot']+'/'+f.name)
 with zipfile.ZipFile(archive)as z:assert z.testzip()is None
 (H/'CAPTURE_INDEX_FIX24.json').write_text(json.dumps({'packets':packets,'archiveSHA256':sha(archive),'archiveBytes':archive.stat().st_size},indent=2)+'\n',encoding='utf8')
 (H/'PRESERVATION_FIX24.json').write_text(json.dumps({'disk':before,'runs':runs},indent=2)+'\n',encoding='utf8')
 #Document is our append only; normalize its line endings without changing text.
 doc=REPO/DOC;old=subprocess.check_output(['git','-C',str(REPO),'show','HEAD:'+DOC]).replace(b'\r\n',b'\n');current=doc.read_bytes().replace(b'\r\n',b'\n');assert current.startswith(old);doc.write_bytes(current)
 selected=[]
 for root in [H,H/'close',H/'motion',H/'import']:
  for p in root.iterdir():
   if not p.is_file()or p.name.startswith(('native-before-','before-native-','after-native-','COPY_','POST_COMMIT'))or p.name.endswith('_REPLY.json'):continue
   if p.name in ['BEFORE.json','AFTER.json','LIBRARY_CREATE24.json']:continue
   if p.suffix not in ['.py','.json','.cs','.txt','.compute','.png','.webp','.zip']:continue
   q=DEST/p.relative_to(H);q.parent.mkdir(parents=True,exist_ok=True)
   with q.open('xb')as f:f.write(p.read_bytes())
   assert sha(q)==sha(p);selected.append(str(q.relative_to(REPO)).replace('\\','/'))
 selected+=[ASSET+'.meta',ASSET+'/ForwardEye113_Geometry24.compute',ASSET+'/ForwardEye113_Geometry24.compute.meta',DOC]
 assert len(selected)==len(set(selected))
 manifest={'files':[{'path':p,'sha256':sha(REPO/p),'bytes':(REPO/p).stat().st_size}for p in selected],'preservation':preserve(selected),'archiveBytes':archive.stat().st_size}
 (H/'COPY_FIX24.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'files':len(selected),'bytes':sum(x['bytes']for x in manifest['files']),'archiveBytes':archive.stat().st_size,'preservation':manifest['preservation']},indent=2))
def stage():
 m=read(H/'COPY_FIX24.json');paths=[x['path']for x in m['files']];assert not git('diff','--cached','--name-only');preserve(paths)
 for x in m['files']:assert sha(REPO/x['path'])==x['sha256']
 subprocess.run(['git','-C',str(REPO),'-c','core.autocrlf=false','add','--pathspec-from-file=-','--pathspec-file-nul'],input=('\0'.join(paths)+'\0').encode(),check=True)
 assert set(git('diff','--cached','--name-only').splitlines())==set(paths)
 for x in m['files']:assert hashlib.sha256(subprocess.check_output(['git','-C',str(REPO),'show',':'+x['path']])).hexdigest()==x['sha256']
 p=subprocess.run(['git','-C',str(REPO),'-c','core.whitespace=cr-at-eol','diff','--cached','--check'],capture_output=True,text=True,encoding='utf8')
 warnings=[s for s in p.stdout.splitlines()if 'trailing whitespace.'in s or 'new blank line at EOF'in s]
 (H/'STAGED_FIX24.json').write_text(json.dumps({'files':len(paths),'allIndexBytesExact':True,'diffCheckExit':p.returncode,'frozenSourceWhitespaceWarnings':warnings,'preservation':preserve(paths)},indent=2)+'\n',encoding='utf8')
 print(json.dumps({'files':len(paths),'allIndexBytesExact':True,'diffCheckExit':p.returncode,'frozenWhitespaceCount':len(warnings),'userChangesPreserved':True}))
if __name__=='__main__':stage()if len(sys.argv)>1 and sys.argv[1]=='stage'else copy()
