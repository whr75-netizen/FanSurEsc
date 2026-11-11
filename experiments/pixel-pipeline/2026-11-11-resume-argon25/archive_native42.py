from pathlib import Path
import hashlib,json,zipfile,sys,subprocess
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';D=R/P
ROOTS=['ContourFinal41.compute','FinalContour41.cs','final_contour41.py','test_final41.py','prepare_final41.py','relay41.py','review_final41.py','source_limits41.py','WorldOccluder41.cs','WorldOccluder42.cs','prepare_world41.py','ContourNative42.compute','FinalContour42.cs','native_contour42.py','test_native42.py','prepare_native42.py','prepare_world42.py','relay42.py','review_native42.py','archive_native42.py']
ASSETS=[f'Assets/EUnityValidation01/SourceBoundary{n}{suffix}'for n in [41,42]for suffix in ['.meta','/'+('ContourFinal41.compute'if n==41 else'ContourNative42.compute'),'/'+('ContourFinal41.compute.meta'if n==41 else'ContourNative42.compute.meta')]]
REFERENCES=['Assets/EUnityValidation01/NativePlayer395/Runtime/NativeWorldFeature395.cs','Assets/EUnityValidation01/NativePlayer395/Runtime/NativePlayer395.cs','Assets/EUnityValidation01/NativePlayer395/Shaders/Native395.compute','Assets/EUnityValidation01/MatchedPlayer397/Gameplay397.cs','Assets/EUnityValidation01/HeadLocal367/Runtime/HeadLocal367.cs','Assets/EUnityValidation01/HeadLocal367/Runtime/FullFeature367.cs','Assets/EUnityValidation01/HeadLocal367/Shaders/GridJoin367.compute','Assets/EUnityValidation01/GameMapIntegration333/Shaders/Compose333.compute']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf-8',newline='\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def data(p):
 r=json.loads(p.read_text())['result'];c=r.get('structuredContent')
 if not c:c=next(json.loads(b['text'])for b in r['content']if b.get('type')=='text')
 assert c['success'];return c['data']
def main():
 assert git('rev-parse','HEAD')=='2458123fd57c2e903b6a13e0a2ef0baf40a6befe';user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(user)==30 and all(sha(R/p)==v for p,v in user.items())
 assert data(H/'face42/console/REPLY.json')==data(H/'face33/console/REPLY.json');assert'playing=False'in(H/'face42/final/PUBLIC_AFTER.txt').read_text();cases={}
 raw=[]
 for stage in [41,42]:
  for name in ['', 'world/']:
   root=H/f'face{stage}';c=root/name/'capture';r=json.loads((c/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and r['pendingOwners']==0 and not r['errors'];a=json.loads((root/name/'analysis'/('ACTUAL_FINAL41.json'if stage==41 else'ACTUAL_NATIVE42.json')).read_text());assert len(a['rows'])==6
   if stage==42:assert a['CPUExactFrames']==6 and all(p['invalid']==0 and p['paletteMismatch']==0 and p['unselectedNativeRGBChanged']==0 for p in a['rows'])
   if stage==42 and name:assert a['worldOcclusionObserved']and r['worldFixture41After']['disposed']
   cases[str(stage)+'/'+name]={'utc':r['utc'],'nativeDeliveredOutput':stage==42,'worldRejected':[p['worldRejected']for p in a['rows']],'selected':[p['selected']for p in a['rows']],'restored':True,'nativeEqual':sum(x.get('equal')is True for x in r['nativeChecks']),'nativeCheckTotal':len(r['nativeChecks']),'beforeMemory':r['beforeMemory'],'afterMemory':r['afterMemory']}
   raw.extend(p for p in c.iterdir()if p.suffix=='.f32'or p.name.startswith('geometry-frame')or p.name=='COMPLETE.json')
 ref=H/'face42/reference';ref.mkdir(exist_ok=True);sourceRows=[]
 for name in REFERENCES:
  dst=ref/Path(name).name;src=R/name
  if dst.exists():assert sha(dst)==sha(src)
  else:dst.write_bytes(src.read_bytes())
  sourceRows.append({'source':name,'snapshot':dst.relative_to(H).as_posix(),'SHA256':sha(src),'readOnlyInputNotProductModification':True})
 save(H/'face42/PRODUCER_REFERENCES42.json',sourceRows);invariance=json.loads((H/'face42/WORLD_INDEPENDENCE42.json').read_text());assert len(invariance)==6 and all(all(x[k]for k in ['sameQROI','sameHairOnLineMask','sameHairOffLineMask','sameSourceEdgeIDs'])for x in invariance)
 z=H/'face42/ACTUAL_PACKETS42.zip'
 if not z.exists():
  with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as out:
   for p in sorted(raw):out.write(p,p.relative_to(H).as_posix())
 with zipfile.ZipFile(z)as archive:assert archive.testzip()is None
 save(H/'face42/STATUS42.json',{'baselineCommit':'2458123f','cases':cases,'41FinalClaimWithdrawn':'Intermediate Compose333 is not delivered Native395; failed world fixture retained','42ActualNativeOutputGPUVerified':True,'product77Changed':False,'original30Equal':True,'ownerHistoryReplaced':False,'facePaletteComplete':False,'variableThicknessComplete':False,'artTemporalStabilityPassed':False,'consoleSameAs33':True,'GPU115':0,'CUA':0,'SaveAssets':0,'killResetDriverGC':0,'push':False})
 selected=ROOTS[:]
 for root in [H/'face41',H/'face42']:
  for p in root.rglob('*'):
   if not p.is_file()or'build'in p.parts or p.name.startswith(('native-before-','TRACE-','library-xattrs-'))or p.suffix in ['.f32','.bin','.dll','.pdb','.rsp']or p.name in ['ARCHIVE42.json','SCHEMA.json','COMMIT42.json']:continue
   selected.append(p.relative_to(H).as_posix())
 selected=sorted(set(selected));rows=[{'path':p,'SHA256':sha(H/p),'bytes':(H/p).stat().st_size}for p in selected];save(H/'face42/ARCHIVE42.json',{'files':rows,'nativeBackupsAndBuildsExcluded':True,'rawZipSHA256':sha(z),'assets':[{'path':p,'SHA256':sha(R/p)}for p in ASSETS]})
 if'--publish'in sys.argv:
  for row in rows+[{'path':'face42/ARCHIVE42.json','SHA256':sha(H/'face42/ARCHIVE42.json')}]:
   dst=D/row['path'];src=H/row['path']
   if dst.exists():assert sha(dst)==row['SHA256'],'Existing different snapshot '+row['path']
   else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';old=doc.read_bytes();append=(H/'face42/HANDOFF_APPEND42.md').read_bytes()
  if not old.endswith(append):assert '### 실제 native 전달 경로·외부 월드 가림 연결41–42'.encode()not in old;doc.write_bytes(old+append)
  assert all(sha(D/p['path'])==p['SHA256']for p in rows)and all(sha(R/p)==v for p,v in user.items())
 print(json.dumps({'files':len(rows)+1,'bytes':sum(x['bytes']for x in rows),'zipBytes':z.stat().st_size,'published':'--publish'in sys.argv,'user30Equal':True}))
 if'--commit'in sys.argv:
  assert'--publish'in sys.argv;names=[P+'/'+p['path']for p in rows]+[P+'/face42/ARCHIVE42.json','docs/ai/PIXEL_ALBEDO_20261030.md']+ASSETS;assert len(names)==len(set(names))and not(set(names)&set(user));staged=git('diff','--cached','--name-only').splitlines();assert not staged or set(staged)==set(names)
  if not staged:git('add','--',*names)
  assert set(git('diff','--cached','--name-only').splitlines())==set(names)
  r=subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--','.',':(exclude)*.meta'],cwd=R,capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
  body=H/'face42/COMMIT_BODY42.txt';body.write_text('Connect source contour diagnostics to actual native presentation and world depth\n\nObserve Native395 output/depth/cell receipts after its Present pass, preserve continuous delta, and render a bounded private native contour candidate without changing product77 or its owner/history. Verify actual walk/turn pixels and an ordinary-world occluder with CPU byte parity, source-mask independence and restored resources/state.\n\nRetain and correct the intermediate-only41 claim and failed fixture. Leave face colour segmentation, variable width, final curve ownership and temporal art quality incomplete.\n',encoding='utf-8');git('commit','--file',str(body));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in user.items());save(H/'face42/COMMIT42.json',{'commit':git('rev-parse','HEAD'),'files':len(names),'original30Equal':True,'product77Changed':False,'push':False});print((H/'face42/COMMIT42.json').read_text())
if __name__=='__main__':main()
