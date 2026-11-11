"""One explicit official relay action. No automatic save/exit/reopen/Play sequence."""
from pathlib import Path
import json,sys
from prepare_final41 import compile_unity_language
import relay33
H=Path(__file__).resolve().parent;G=H/'face54'
TITLES={'backup':'Back up current unsaved contents and project/settings by public getters; no save or GPU',
        'save':'Save the exact reviewed dirty asset set after verified external backups; no Play or GPU',
        'project-save':'Standard project SaveAssets once, only if the complete dirty set is the reviewed31; no discard or GPU',
        'project-save-reviewed':'Save reviewed31 project assets; require every extra to be builtin or generated foreign Shader, back up package source and verify no source changes',
        'dirty-inspect':'Read all persistent dirty paths and types after save preflight stopped; no save, exit or GPU',
        'native-export':'Export reviewed native Mesh and five ProjectSettings objects to new workspace copies only; no project/package/global save, no exit or GPU',
        'stopped':'Read and verify preserved native/input/scene/settings and retained RT state after save/export stopped; no save or exit',
        'quit':'Request normal Unity Editor exit after verified saving; no forced termination',
        'reopened':'Read reopened project state, serialized contents and diagnostic resource counts only'}
def main():
 action=sys.argv[1];assert action in TITLES;variant='managed-fix1'if'--managed-fix1'in sys.argv else''
 if action=='project-save-reviewed' and (G/'AUTO_REVIEW_DENIAL54.json').exists() and '--prepare-only'not in sys.argv:
  raise RuntimeError('54 global save was denied before execution. Do not submit without materially new authorization and a reviewed plan; no automatic retry.')
 if variant:
  old=json.loads((G/action/'final/REPLY.json').read_text())['result'];c=old.get('structuredContent')or next(json.loads(x['text'])for x in old['content']if x.get('type')=='text')
  assert c['error'].startswith('COMPILATION_FAILED') and c['data']['isExecutionSuccessful']is False and not(G/action/'STARTED.json').exists()
 p=G/action/variant/'final';p.mkdir(parents=True,exist_ok=True);assert not(p/'REQUEST.json').exists(),'Inspect previous outcome before another request'
 body=H/({'backup':'BackupRestart54.cs.txt','save':'SaveRestart54.cs.txt','project-save':'SaveProject54.cs.txt','project-save-reviewed':'SaveProjectReviewed54.cs.txt','dirty-inspect':'InspectDirty54.cs.txt','native-export':'ExportNative54.cs.txt','stopped':'ReadStopped54.cs.txt','quit':'QuitRestart54.cs.txt','reopened':'ReadReopened54.cs.txt'}[action]);source=body.read_text(encoding='utf-8')
 if action in ['backup','save','project-save','project-save-reviewed','dirty-inspect','native-export','stopped']:
  if action=='backup':
   user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(user)==30;(G/action/'USER_PATHS54.json').write_text(json.dumps(list(user)),encoding='utf-8')
  old=(H/'face49/capture/RUN.cs.txt').read_text();prefix=old[:old.index('// Prepared helper only. No entry point, Asset import, renderer call or global setter.')];source=prefix+source
 (p/'RUN.cs.txt').write_text(source,encoding='utf-8',newline='\n');b=G/'build';b.mkdir(exist_ok=True);compile_unity_language(p/'RUN.cs.txt',b/(action+'.dll'))
 if '--prepare-only'in sys.argv:print('54 CPU compiled '+action+'; not executed');return
 relay33.G=G/action/variant;relay33.TITLE_OVERRIDE=TITLES[action];sys.argv=[sys.argv[0],'final'];relay33.main()
 r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text');assert c['success'],c.get('error');d=c.get('data',{});print(json.dumps({'action':action,'success':c['success'],'compiled':d.get('isCompilationSuccessful'),'executed':d.get('isExecutionSuccessful'),'logs':d.get('executionLogs')}))
if __name__=='__main__':main()
