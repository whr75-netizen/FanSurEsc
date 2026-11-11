from pathlib import Path
import json,hashlib,zipfile,sys
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');D=R/'experiments/pixel-pipeline/2026-11-11-resume-argon25';G=H/'face36'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf-8',newline='\n')
def main():
 user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert all(sha(R/p)==v for p,v in user.items())
 prior=json.loads((D/'face33/ARCHIVE33.json').read_text());assert all(sha(D/p['path'])==p['SHA256']for p in prior['files'])
 good=json.loads((G/'fix1/capture/COMPLETE.json').read_text());a=json.loads((G/'analysis/GPU_AREA36.json').read_text());assert good['restorationChecksPass']and good['ownedResourcesReleased']and good['pendingOwners']==0 and not good['errors']and a['firstWholeROIByteMismatch']==0
 baseConsole=lambda p:json.loads(json.loads(p.read_text())['result']['content'][0]['text'])['data'];assert baseConsole(H/'face33/console/REPLY.json')==baseConsole(G/'post/console/REPLY.json')
 scopes=[H/'face34/capture',H/'face35/capture',G/'capture',G/'fix1/capture'];runs=[];z=G/'ACTUAL_PACKETS34_36.zip'
 if not z.exists():
  with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as out:
   for c in scopes:
    marker=c/('COMPLETE.json'if(c/'COMPLETE.json').exists()else'FAILED.json');report=json.loads(marker.read_text())
    for p in c.glob('*.f32'):out.write(p,str(p.relative_to(H)).replace('\\','/'))
    out.write(marker,str(marker.relative_to(H)).replace('\\','/'))
 with zipfile.ZipFile(z)as test:assert test.testzip()is None
 for c in scopes:
  marker=c/('COMPLETE.json'if(c/'COMPLETE.json').exists()else'FAILED.json');r=json.loads(marker.read_text());assert r['ownedResourcesReleased']and r['restorationChecksPass']and r['pendingOwners']==0
  runs.append({'path':str(c.relative_to(H)).replace('\\','/'),'complete':marker.name=='COMPLETE.json','nativeEqual':sum(v.get('equal')is True for v in r['nativeChecks']),'unavailable':[v for v in r['nativeChecks']if v.get('equal')is None],'memoryBefore':r['beforeMemory'],'memoryAfter':r['afterMemory'],'newConsoleErrors':len(r['errors'])})
 status={'baselineCommit':'3ae55c7b','actualPlays':4,'currentDefaultProduct77Changed':False,'original30Equal':True,'prior33Equal':True,'runtimeQRegionImplemented':True,'actualFinalRGBModified':False,'sameSourceTemporalValidated':False,'runs':runs,'GPUComparison':{k:a[k]for k in ['actualConsecutiveFrames','firstWholeROICPUComparisonCells','firstWholeROIByteMismatch','watchCPUComparisons','sourceAreaError','watchUVRange']},'post':'12:17:30UTC Edit/clean GameMap1/dirty31/input unchanged/optionsfalseNone','rawZipSHA256':sha(z),'next':['source UV/barycentric time correspondence','source colour parent/child→family criterion','discrete original thin curve/alpha owner contract']};save(G/'STATUS36.json',status);save(G/'PRESERVATION36.json',{'original30SHA256':user,'allEqual':True,'prior33Equal':True,'newAssets':['SourceBoundary35/FineSourceLight35.shader','SourceBoundary36/SourceArea36.compute'],'GPU115Calls':0,'InputReplacement':0,'SaveAssets':0,'CUA':0,'KillReset':0,'Push':0})
 roots=['prepare_runtime34.py','relay34.py','analyze_normals34.py','surface_paths34.py','test_surface_paths34.py','review_surface_q34.py','prepare_source_light35.py','relay35.py','review_source_regions35.py','SourceArea36.compute','test_source_area36.py','prepare_area36.py','relay36.py','repair_readback36.py','relay36fix.py','review_runtime36.py','relay36post.py','archive_runtime36.py']
 selected=roots[:]
 for folder in ['face34','face35','face36']:
  for p in (H/folder).rglob('*'):
   if not p.is_file()or any(x in p.parts for x in ['build','shaders','preflight-scope']):continue
   if p.name.startswith('native-before-')or p.name.startswith('TRACE-')or p.suffix in ['.f32','.dxbc','.bin']or p.name in ['SCHEMA.json','GLOBALS_BEFORE.bin','ERROR.json']:continue
   if p.name=='ARCHIVE36.json':continue
   selected.append(str(p.relative_to(H)).replace('\\','/'))
 selected=sorted(set(selected));rows=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in selected];save(G/'ARCHIVE36.json',{'files':rows,'nativeBackupsAndBuildsExcluded':True,'actualDataZip':True})
 if '--publish'in sys.argv:
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';append=(G/'HANDOFF_APPEND36.md').read_bytes();before=doc.read_bytes()
  if not before.endswith(append):assert sha(doc)=='8b42908ae30d6e8cc3959afe3f22eb83122c974315f0cd397e6c624dff3d0c28'
  for row in rows+[{'path':'face36/ARCHIVE36.json','SHA256':sha(G/'ARCHIVE36.json')}]:
   src=H/row['path'];dst=D/row['path']
   if dst.exists():assert sha(dst)==row['SHA256'],'Existing differing owned path '+row['path']
   else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
  if not before.endswith(append):doc.write_bytes(before+append)
  assert all(sha(D/p['path'])==p['SHA256']for p in rows)and all(sha(R/p)==v for p,v in user.items())
 print(json.dumps({'files':len(rows)+1,'rawZipBytes':z.stat().st_size,'published':'--publish'in sys.argv,'user30Equal':True,'prior33Equal':True}))
if __name__=='__main__':main()
