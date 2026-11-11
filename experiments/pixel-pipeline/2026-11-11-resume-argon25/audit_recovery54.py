"""Offline evidence audit only. Does not import the Unity relay or issue commands."""
from pathlib import Path
import collections,hashlib,json,datetime
H=Path(__file__).resolve().parent;G=H/'face54';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def data(p):
 r=json.loads(p.read_text())['result'];return r.get('structuredContent')or next(json.loads(x['text'])for x in r['content']if x.get('type')=='text')
def main():
 b=G/'backup';native=json.loads((b/'NATIVE_BEFORE73.json').read_text());disks=json.loads((b/'DISK_BEFORE.json').read_text());verified=json.loads((b/'VERIFIED54.json').read_text());before=json.loads((b/'COMPLETE.json').read_text());stopped=json.loads((G/'stopped/STATE.json').read_text());saved=json.loads((G/'save/RESULT.json').read_text());denied=json.loads((G/'AUTO_REVIEW_DENIAL54.json').read_text())
 assert len(native)==47 and len(disks)==128 and verified['backupVerified']
 for x in native:assert sha(b/x['snapshot'])==x['sha256'] and(b/x['snapshot']).stat().st_size==x['bytes']
 for x in disks:
  if x['exists']:assert sha(b/'disk'/x['path'])==x['sha256'] and sha(R/x['path'])==x['sha256']
 assert saved['saveCallsReturned']==31 and saved['nativeContentsSame'] and saved['inputSame'] and not saved['allTargetsClean']
 assert stopped['Edit']and not stopped['compiling']and not stopped['updating']and stopped['nativeSame']and stopped['inputSameReferenceIdAndJSON']and stopped['dirtyProject']==31
 assert len(stopped['nativeChecks'])==47 and all(x.get('equal')is True for x in stopped['nativeChecks'])
 assert stopped['diagnosticRTs']==stopped['diagnosticRTsCreated']==45
 assert denied['processStarted']is False and not(G/'project-save-reviewed/final/REQUEST.json').exists() and not(G/'project-save-reviewed/STARTED.json').exists() and not(G/'project-save/STARTED.json').exists()
 assert not list((G/'native-export').glob('*.asset'))
 extra=json.loads((G/'dirty-inspect/RESULT.json').read_text())['dirty'];ids={x['entityId']for x in before['dirty']};extra=[x for x in extra if x['entityId']not in ids]
 assert len(extra)==486 and sum(x['path'].startswith('Packages/')for x in extra)==34
 a=data(H/'face48/console/REPLY.json')['data']['logs'];c=data(G/'console/REPLY.json');assert c['success'];logs=c['data']['logs'];old={x['message']for x in a};new=[{'timestamp':x['timestamp'],'firstLine':x['message'].splitlines()[0]}for x in logs if x['message']not in old]
 assert len(new)==1 and 'already persistent'in new[0]['firstLine']
 user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(user)==30 and all(sha(R/p)==v for p,v in user.items())
 assert (G/'build/project-save-reviewed.language9.txt').read_text()==''
 result={'generatedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'lastEditorUTC':stopped['utc'],'native47BackupsAndContentsExact':True,'disk128BackupsAndCurrentFilesExact':True,'user30Equal':True,'specificGUIDSaveCallsReturned':31,'all31SavedProven':False,'projectDirtyStill31':True,'normalExitRequested':False,'reopenExecuted':False,'GPUExecuted':False,'retainedDiagnosticRTs':45,'newGlobalSaveDeniedBeforeProcess':True,'deniedGlobalSaveRetried':False,'nativeExportRejectedPersistentObject':True,'newProjectOrPackageBytesChanged':0,'currentEditAndInputSettingsIdentityPreserved':True,'otherDirtyAtBoundedRead':{'count':486,'packagesShader':34,'builtin':452,'types':dict(collections.Counter(x['type']for x in extra))},'consoleBoundedLast12':{'newMessagesComparedWith48':new,'oldZBinningMessages':sum('ZBinningJob'in x['message']and x['message']in old for x in logs),'notGlobalHealthProof':True},'plannedSaveExternalCSharp9Compiled':True,'awaitingScopeDecision':'Standard SaveAssets can include builtin/package-derived objects beyond reviewed31; no indirect execution or shutdown to bypass rejection','backupRoot':str(b),'product77Changed':False}
 (G/'AUDIT54.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
