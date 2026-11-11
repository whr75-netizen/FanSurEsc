from pathlib import Path
import hashlib,json,zipfile,sys,subprocess
H=Path(__file__).resolve().parent;G=H/'face40';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';D=R/P
ROOTS=['Contour40.cs','ContourTests40.cs','test_contour40.py','GeoContour40.shader','GeoContour40Authored.shader','GeoResolve40.compute','prepare_contour40.py','prepare_motion_contour40.py','prepare_authored_contour40.py','MotionContour40.cs','relay40.py','review_contour40.py','trace_contour40.py','audit_width40.py','deliver_contour40.py','archive_runtime40.py']
ASSETS=['Assets/EUnityValidation01/SourceBoundary40.meta','Assets/EUnityValidation01/SourceBoundary40/GeoContour40.shader','Assets/EUnityValidation01/SourceBoundary40/GeoContour40.shader.meta','Assets/EUnityValidation01/SourceBoundary40/GeoResolve40.compute','Assets/EUnityValidation01/SourceBoundary40/GeoResolve40.compute.meta','Assets/EUnityValidation01/SourceBoundary40Authored.meta','Assets/EUnityValidation01/SourceBoundary40Authored/GeoContour40Authored.shader','Assets/EUnityValidation01/SourceBoundary40Authored/GeoContour40Authored.shader.meta']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf-8',newline='\n')
def data(p):
 r=json.loads(p.read_text())['result'];c=r.get('structuredContent')
 if not c:c=next(json.loads(x['text'])for x in r['content']if x.get('type')=='text')
 assert c['success'];return c['data']
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def main():
 user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(user)==30 and all(sha(R/p)==v for p,v in user.items())
 assert git('rev-parse','HEAD')=='194d5315adcc7490c3299f55b17e81de85ea6f46'
 assert data(H/'face33/console/REPLY.json')==data(G/'console/REPLY.json');assert'playing=False'in(G/'final/PUBLIC_AFTER.txt').read_text()
 cases={};raw=[]
 for name in ['compat','motion','directed','authored']:
  c=G/name/'capture';r=json.loads((c/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and r['pendingOwners']==0 and not r['errors'];a=json.loads((G/('analysis'if name=='compat'else'analysis-'+name)/'ACTUAL_CONTOUR40.json').read_text());assert a['CPUByteMatches']==6 and all(p['paletteMismatch']==0 and p['unselectedChanged']==0 and p['invalidCells']==0 for p in a['records'])
  cases[name]={'completeUTC':r['utc'],'frames':a['actualFrames'],'selected':[p['selectedCells']for p in a['records']],'occluded':[p['occludedCells']for p in a['records']],'CPUByteMatches':a['CPUByteMatches'],'restored':True,'pendingOwners':0,'beforeMemory':r['beforeMemory'],'afterMemory':r['afterMemory'],'nativeChecks':{'equal':sum(x.get('equal')is True for x in r['nativeChecks']),'total':len(r['nativeChecks'])}}
  raw.extend(p for p in c.iterdir()if p.suffix=='.f32'or p.name.startswith('geometry-frame')or p.name=='COMPLETE.json')
 z=G/'ACTUAL_PACKETS40.zip'
 if not z.exists():
  with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as out:
   for p in sorted(raw):out.write(p,p.relative_to(G).as_posix())
 with zipfile.ZipFile(z)as archive:assert archive.testzip()is None
 save(G/'STATUS40.json',{'baselineCommit':'194d5315','cases':cases,'CPUContourTests':17,'product77Changed':False,'artOrTimeStabilityPassed':False,'fullFaceColourRegionAndPaletteComplete':False,'worldDepthOwnerIntegrated':False,'variableThicknessQuantized':False,'consoleSameAs33':True,'originalUser30Equal':True,'GPU115Calls':0,'CUA':0,'SaveAssets':0,'forcedGC':0,'killResetDriverChanges':0,'push':False})
 pkg=Path((G/'package/final/PACKAGE_PATH.txt').read_text().strip());refs=[]
 for n in ['MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl','MToon10/Shaders/vrmc_materials_mtoon_geometry_vertex.hlsl']:
  p=pkg/n;refs.append({'path':str(p),'SHA256':sha(p)})
 save(G/'SOURCE_IMPLEMENTATION40.json',{'installedSourcesReadOnly':refs,'rule':'MToon parameter map green, raw mesh vertex UV, LOD0; no MainTexST or animated fragment UV is substituted','GPUCandidateSupportGateOnly':True})
 selected=ROOTS[:]
 for p in G.rglob('*'):
  if not p.is_file()or'build'in p.parts or p.name.startswith(('native-before-','TRACE-','library-xattrs-'))or p.suffix in ['.f32','.bin','.dll','.pdb','.rsp']or p.name in ['ARCHIVE40.json','SCHEMA.json','COMMIT40.json']:continue
  selected.append(p.relative_to(H).as_posix())
 selected=sorted(set(selected));rows=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in selected];save(G/'ARCHIVE40.json',{'files':rows,'originalNativeBackupsAndBuildsExcluded':True,'rawZipSHA256':sha(z),'assets':[{'path':p,'SHA256':sha(R/p)}for p in ASSETS]})
 if '--publish'in sys.argv:
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';before=doc.read_bytes();append=(G/'HANDOFF_APPEND40.md').read_bytes();assert b'### \xec\x9b\x90\xeb\xb3\xb8 \xea\xb8\xb0\xed\x95\x98 \xea\xb3\xa1\xec\x84\xa0'not in before or before.endswith(append)
  for row in rows+[{'path':'face40/ARCHIVE40.json','SHA256':sha(G/'ARCHIVE40.json')}]:
   dst=D/row['path'];src=H/row['path']
   if dst.exists():assert sha(dst)==row['SHA256'],'Existing differing file '+str(dst)
   else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
  if not before.endswith(append):doc.write_bytes(before+append)
  assert all(sha(D/x['path'])==x['SHA256']for x in rows)and all(sha(R/p)==v for p,v in user.items())
 print(json.dumps({'files':len(rows)+1,'bytes':sum(x['bytes']for x in rows),'rawZipBytes':z.stat().st_size,'published':'--publish'in sys.argv,'original30Equal':True}))
 if '--commit'in sys.argv:
  assert'--publish'in sys.argv;names=[P+'/'+x['path']for x in rows]+[P+'/face40/ARCHIVE40.json','docs/ai/PIXEL_ALBEDO_20261030.md']+ASSETS;assert not(set(names)&set(user))and len(names)==len(set(names));staged=git('diff','--cached','--name-only').splitlines();assert not staged or set(staged)==set(names)
  if not staged:git('add','--',*names)
  assert set(git('diff','--cached','--name-only').splitlines())==set(names)
  check=subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--','.',':(exclude)*.meta'],cwd=R,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
  body=G/'COMMIT_BODY40.txt';body.write_text('Preserve source contour direction and authored width support in GPU diagnostics\n\nConnect evaluated source edges, canonical provenance and original MToon width-mask support in an isolated head contour. Verify controlled and actual walk/turn frames, CPU composition parity and owned resource/state restoration.\n\nKeep product77 and original user changes intact. Record remaining variable thickness, final world/style ownership, face colour segmentation and temporal art limitations.\n',encoding='utf-8');git('commit','--file',str(body));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in user.items());save(G/'COMMIT40.json',{'commit':git('rev-parse','HEAD'),'files':len(names),'original30Equal':True,'product77Changed':False,'push':False});print((G/'COMMIT40.json').read_text())
if __name__=='__main__':main()
