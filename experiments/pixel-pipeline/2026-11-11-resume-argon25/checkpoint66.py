from pathlib import Path
import subprocess,json,hashlib
from archive_checkpoint65 import H,R,P,sha,git,load,save
BASE='558bcc81dc13ad0f826c6644432be35ac88777dd'
ROOTS=['replay_outline_class66.py','prepare_class66.py','relay66.py','review_class66.py','source_basin66.py','test_basin66.py','checkpoint66.py']
ASSET='Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.compute'
def main():
 assert git('rev-parse','HEAD')==BASE and not git('diff','--cached','--name-only')
 user=load(H/'face55/BEFORE_GIT55.json')['user30'];assert all(sha(R/p)==v for p,v in user.items());disk=load(H/'face55/backup/DISK_BEFORE.json');assert all((R/x['path']).exists()==x['exists'] and(not x['exists']or sha(R/x['path'])==x['sha256'])for x in disk)
 r=load(H/'face66/capture/COMPLETE.json');assert r['restorationChecksPass']and r['ownedResourcesReleased']and r['pendingOwners']==0 and not r['errors']and all(x.get('equal')is not False for x in r['nativeChecks'])
 a=load(H/'face66/ACTUAL_CLASS66.json');assert a['actualWidthClassCases']==30 and a['originalWidthExteriorCounts']==[0]*6 and a['genericActorInteriorOverwrite']==0
 state=load(H/'face66/post/STATE.json');assert state['Edit'] and state['inputJSONExact']and state['diagnosticRTs']==state['diagnosticMaterials']==state['commandUpdateObservers']==0 and state['allRTCount']==30
 c=load(H/'face66/console/REPLY.json')['result'];c=c.get('structuredContent')or next(json.loads(x['text'])for x in c['content']if x.get('type')=='text');assert c['success']and not c['data']['logs'];assert sha(R/ASSET)==sha(H/'face66/shaders/SourceNativeHull60.compute')
 files=list(ROOTS)
 for f in(H/'face66').rglob('*'):
  if not f.is_file()or'build'in f.parts or f.name.startswith(('native-before-','native-after-'))or f.name in ['GLOBALS_BEFORE.bin','INPUT_BEFORE.json','INPUT_AFTER.json','REPLY.json','SCHEMA.json','ARCHIVE66.json','COMMIT66.json','COMMIT_BODY66.txt']:continue
  files.append(f.relative_to(H).as_posix())
 rows=[{'path':f,'bytes':(H/f).stat().st_size,'SHA256':sha(H/f)}for f in sorted(set(files))];save(H/'face66/ARCHIVE66.json',{'baseCommit':BASE,'files':rows,'ownedAsset':ASSET,'user30Protected128Equal':True,'product77DefaultChanged':False})
 for row in rows+[{'path':'face66/ARCHIVE66.json','SHA256':sha(H/'face66/ARCHIVE66.json')}]:
  target=R/P/row['path'];assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((H/row['path']).read_bytes());assert sha(target)==row['SHA256']
 doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';assert not git('diff','--name-only','--',str(doc));add=(H/'face66/HANDOFF_APPEND66.md').read_bytes();assert add not in doc.read_bytes();doc.write_bytes(doc.read_bytes()+add)
 names=[P+'/'+x['path']for x in rows]+[P+'/face66/ARCHIVE66.json','docs/ai/PIXEL_ALBEDO_20261030.md',ASSET];assert not set(names).intersection(user)
 subprocess.run(['git','add','--pathspec-from-file=-','--pathspec-file-nul'],cwd=R,input=('\0'.join(names)+'\0').encode(),check=True);assert set(git('diff','--cached','--name-only').splitlines())==set(names)
 subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=R,check=True)
 body=H/'face66/COMMIT_BODY66.txt';body.write_text('Separate actor-exterior contours from native material hull decoration\n\nGeneric exterior class cannot overwrite current actor occupancy. Retain original hull as explicit same-frame control and keep product77 default. Six actual normal frames /30 width-class cases match CPU RGB/owner/layer; eliminate4 original-width clothing/hair dots and17-38 self-overwrites in large controls.\n\nPreserve actual source, input/settings/resources and user edits. Closed native-colour flank basins retain weak paint witness but whole-region extents disagree; do not infer full-face families or claim runtime history/LUT completion.\n',encoding='utf-8');git('commit','--file',str(body));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in user.items());result={'commit':git('rev-parse','HEAD'),'files':len(names),'user30Protected128Equal':True,'product77DefaultChanged':False,'actualGPUFrames':6,'actualCases':30,'runtimeHistoryOrFaceLUTComplete':False,'push':False};save(H/'face66/COMMIT66.json',result);print(json.dumps(result))
if __name__=='__main__':main()
