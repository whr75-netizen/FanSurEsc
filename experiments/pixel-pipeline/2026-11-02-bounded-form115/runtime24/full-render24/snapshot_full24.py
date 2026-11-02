"""Select only this isolated runtime/evidence. No Unity call or broad stage."""
from pathlib import Path
import collections,datetime,hashlib,json,subprocess,sys,zipfile
H=Path(__file__).resolve().parent;B=H.parent.parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-02-bounded-form115/runtime24/full-render24'
DOC='docs/ai/PIXEL_ALBEDO_20261030.md';ASSET='Assets/EUnityValidation01/Direct24Geometry'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True,encoding='utf8').strip('\r\n')
def preserve():
 b=read(B/'DISK_BOUND_BEFORE115.json')
 for p,digest in b['files'].items():assert sha(REPO/p)==digest,p
 lines=git('status','--porcelain','--untracked-files=no').splitlines()
 assert '\n'.join(x for x in lines if x[3:]not in [DOC,ASSET+'.meta']and not x[3:].startswith(ASSET+'/')and not x[3:].startswith(str(DEST.relative_to(REPO)).replace('\\','/')+'/'))==b['modifiedStatus'].strip('\r\n')
 old=B.parent/'gpu-form115';native=read(old/'NATIVE_BEFORE73.json')
 assert len(native)==47
 for r in native:assert (old/r['snapshot']).stat().st_size==r['bytes']and sha(old/r['snapshot'])==r['sha256']
 shader=REPO/ASSET/'ForwardEye113_Geometry24.compute';assert sha(shader)==read(H/'CPU_COMPILE_FULL24.json')['shaderSHA256']
 assert (REPO/ASSET/'ForwardEye113_Geometry24.compute.meta').exists()and(REPO/(ASSET+'.meta')).exists()
 face=next(r['sha256']for r in native if 'FaceSourceOwner202' in r['path'])
 for folder in [H,H/'sequence24',H/'motion24']:
  s=read(next(folder.glob('STATE113-*-finished.json')))
  assert s['PlayExited']and not s.get('error')and not s.get('restorationError')and not s['globalRestoreErrors']
  assert s['forward102Disposed']and s['layer102Disposed']and s['carrierSourceDisposed111']and s['carrierNativeDisposed111']
  assert all(x['equal']for x in s['nativeComparisons72'])
  if folder!=H:assert next(r['sha256']for r in read(folder/'NATIVE_BEFORE73.json')if 'FaceSourceOwner202'in r['path'])==face
 return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected35Equal':True,'originalUserModified30Equal':True,'originalNative47BackupEqual':True,'originalFaceMeshNativeHashEqual':True,'product77DefaultChanged':False,'newOwnedShaderSHA':sha(shader),'GPUOrUnityCallsInThisDiskCheck':0}
def snapshot():
 assert git('rev-parse','HEAD')=='fe98a36bc89c6f1e329559431c8e2601b2fd98d1'
 assert not git('diff','--cached','--name-only')and not DEST.exists()
 before=preserve();files=[];packets=[];states=[];dirty=[]
 for key,folder in [('open',H),('sequence24',H/'sequence24'),('motion24',H/'motion24')]:
  s=read(next(folder.glob('STATE113-*-finished.json')));states.append((key,s))
  a=collections.Counter((r['path'],r['type'])for r in s['beforeDirty']);b=collections.Counter((r['path'],r['type'])for r in s['afterDirty'])
  dirty.append({'run':key,'beforeCount':len(s['beforeDirty']),'afterCount':len(s['afterDirty']),'added':[{'path':k[0],'type':k[1],'count':v}for k,v in(b-a).items()],'removed':[list(x)for x in(a-b).items()],
                'nativeContentsCompared':len(s['nativeComparisons72']),'allComparedContentsEqual':True,'scenesEqual':s['beforeScenes']==s['afterScenes'],
                'memoryAPI':'UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong / GetMonoUsedSizeLong / GetTotalReservedMemoryLong; not physical working set',
                'beforeMemory':s['beforeMemory'],'afterMemory':s['afterMemory'],'allocatedDeltaMiB':(s['afterMemory']['allocated']-s['beforeMemory']['allocated'])/1048576,'leakConclusion':None})
  for p in s['sequencePackets']:
   path=Path(p['output']);packets.append({**p,'run':key,'archiveRoot':key+'/'+path.parent.name+'/'+path.name})
 (H/'PRESERVATION_FULL24.json').write_text(json.dumps({'disk':before,'runs':dirty},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 archive=H/'RAW24.zip';assert not archive.exists()
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for pkt in packets:
   path=Path(pkt['output']);assert (path/'RAW_COMPLETE76.marker').read_text().strip()==sha(path/'RAW_MANIFEST.json')
   for p in sorted(path.iterdir()):
    assert p.is_file(),p
    z.write(p,pkt['archiveRoot']+'/'+p.name)
 with zipfile.ZipFile(archive)as z:assert z.testzip()is None
 (H/'CAPTURE_INDEX24.json').write_text(json.dumps({'packets':packets,'archiveSHA256':sha(archive),'archiveBytes':archive.stat().st_size},indent=2)+'\n',encoding='utf8')
 for folder in [H,H/'sequence24',H/'motion24']:
  for p in folder.iterdir():
   if not p.is_file()or p.name.startswith('native-before-')or p.name.endswith('_REPLY.json')or p.name.startswith('COPY_'):continue
   if p.suffix in ['.py','.json','.cs','.txt','.compute','.png','.webp','.zip']:
    if p.name.startswith('POST_COMMIT'):continue
    files.append(p)
 for p in (H/'import').iterdir():
  if p.is_file()and p.suffix=='.json'and p.name not in ['BEFORE.json','AFTER.json']and not p.name.startswith(('before-native-','after-native-')):files.append(p)
 for p in sorted(files):
  target=DEST/p.relative_to(H);target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb')as f:f.write(p.read_bytes())
  assert sha(target)==sha(p)
 attrs=DEST/'.gitattributes';attrs.write_text('*.compute -text\n*.cs -text\n*.txt -text\n*.json -text\n*.py -text\n',encoding='utf8')
 paths=[str((DEST/p.relative_to(H)).relative_to(REPO)).replace('\\','/')for p in files]+[str(attrs.relative_to(REPO)).replace('\\','/'),ASSET+'.meta',ASSET+'/ForwardEye113_Geometry24.compute',ASSET+'/ForwardEye113_Geometry24.compute.meta',DOC]
 assert len(paths)==len(set(paths));after=preserve()
 result={'files':[{'path':p,'sha256':sha(REPO/p),'bytes':(REPO/p).stat().st_size}for p in paths],'preservationBefore':before,'preservationAfter':after,'rawFrames':len(packets),'archiveBytes':archive.stat().st_size}
 (H/'COPY_FULL24.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'selectedFiles':len(paths),'bytes':sum(x['bytes']for x in result['files']),'rawFrames':len(packets),'archiveBytes':archive.stat().st_size,'preserved':after},indent=2))
def stage():
 m=read(H/'COPY_FULL24.json');assert not git('diff','--cached','--name-only');preserve()
 for x in m['files']:assert sha(REPO/x['path'])==x['sha256']
 #308 long Windows paths exceed CreateProcess's command-line limit. Pass the
 #same exact reviewed set through Git's documented NUL-delimited stdin form.
 spec=('\0'.join(x['path']for x in m['files'])+'\0').encode('utf8')
 subprocess.run(['git','-C',str(REPO),'-c','core.autocrlf=false','add','--pathspec-from-file=-','--pathspec-file-nul'],input=spec,check=True)
 assert set(git('diff','--cached','--name-only').splitlines())=={x['path']for x in m['files']}
 for x in m['files']:assert hashlib.sha256(subprocess.check_output(['git','-C',str(REPO),'show',':'+x['path']])).hexdigest()==x['sha256'],x['path']
 print(git('diff','--cached','--stat'));print('Exact selected/index bytes verified')
if __name__=='__main__':stage()if len(sys.argv)>1 and sys.argv[1]=='stage'else snapshot()
