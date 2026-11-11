"""Fresh backup and one newly authorized retry; no automatic next operation."""
from pathlib import Path
import json,sys
from prepare_final41 import compile_unity_language
import relay33
H=Path(__file__).resolve().parent;G=H/'face55'
TITLES={'backup':'Refresh current unsaved native/disk/input/settings backup only; no save, exit or GPU',
        'save':'One standard project SaveAssets including builtin and package Shader objects; verified backups and no manual source edits',
        'quit-check':'Read saved project scene/input/options readiness for normal close; no exit or GPU',
        'quit':'Normal Unity shutdown after save verification; no forced process termination',
        'reopened':'Read reopened project state, saved settings, compilation and diagnostic resource counts only'}
def main():
 action=sys.argv[1];assert action in TITLES;p=G/action/'final';p.mkdir(parents=True,exist_ok=True);assert not(p/'REQUEST.json').exists(),'Inspect original outcome; never duplicate uncertain work'
 if action=='save':
  prior=json.loads((H/'face54/AUTO_REVIEW_DENIAL54.json').read_text());assert prior['processStarted']is False and not(H/'face54/project-save-reviewed/final/REQUEST.json').exists()
  assert not(G/'project-save-reviewed/STARTED.json').exists()
 body=H/({'backup':'BackupRestart54.cs.txt','save':'SaveProjectReviewed54.cs.txt','quit-check':'QuitCheck55.cs.txt','quit':'QuitRestart55.cs.txt','reopened':'ReadReopened55.cs.txt'}[action]);source=body.read_text(encoding='utf-8').replace('resume-20261111\\face54','resume-20261111\\face55')
 if action in ['backup','save','quit-check','reopened']:
  if action=='backup':
   user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];(G/action/'USER_PATHS54.json').write_text(json.dumps(list(user)),encoding='utf-8')
  if action=='save':
   needle='AssetDatabase.SaveAssets();CreateOnly40.Text(Path.Combine(output,"API_RETURNED.json"),DateTime.UtcNow.ToString("O"));'
   assert source.count(needle)==1
   source=source.replace(needle,needle+'\n  var immediate=new Arr40(Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Where(o=>{var p=AssetDatabase.GetAssetPath(o);return p.StartsWith("Assets/")||p.StartsWith("ProjectSettings/");}).Select(o=>new Obj40{["path"]=AssetDatabase.GetAssetPath(o),["type"]=o.GetType().FullName}));CreateOnly40.Text(Path.Combine(output,"IMMEDIATE_AFTER_SAVE.json"),new Obj40{["utc"]=DateTime.UtcNow.ToString("O"),["beforeNativeReserialization"]=true,["dirtyProject"]=immediate}.ToString());')
  old=(H/'face49/capture/RUN.cs.txt').read_text();prefix=old[:old.index('// Prepared helper only. No entry point, Asset import, renderer call or global setter.')];source=prefix+source
 (p/'RUN.cs.txt').write_text(source,encoding='utf-8',newline='\n');b=G/'build';b.mkdir(exist_ok=True);compile_unity_language(p/'RUN.cs.txt',b/(action+'.dll'))
 if '--prepare-only'in sys.argv:print('55 CPU compiled '+action+'; not executed');return
 if action=='reopened':relay33.PID=json.loads((G/'reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid']
 relay33.G=G/action;relay33.TITLE_OVERRIDE=TITLES[action];sys.argv=[sys.argv[0],'final'];relay33.main()
 r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'],c.get('error');d=c.get('data',{});print(json.dumps({'action':action,'success':c['success'],'compiled':d.get('isCompilationSuccessful'),'executed':d.get('isExecutionSuccessful'),'logs':d.get('executionLogs')}))
if __name__=='__main__':main()
