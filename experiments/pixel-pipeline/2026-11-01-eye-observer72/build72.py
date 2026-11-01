"""Whole command compile preparation only; all source remains outside Assets."""
from pathlib import Path
import sys,re
HERE=Path(__file__).resolve().parent
def sibling(short,archived):
 p=HERE.parent/short
 return p if p.exists() else HERE.parent/archived
OLD=sibling('apply-capture66','2026-10-31-apply-capture66');B=sibling('boundary-input69','2026-11-01-boundary-input69');U=sibling('uv-features64','2026-10-31-uv-features64')
sys.path.insert(0,str(B));from prepare_eye72 import bundle
mode=sys.argv[1];assert mode in ('Compile72','Capture72')
s=(OLD/'CaptureRetry66.cs').read_text(encoding='utf-8-sig')
s=s.replace('apply-capture66\\retry-background','eye-observer72').replace('CAPTURE_STATE66.json','CAPTURE_STATE72.json').replace('capture67-','eye72-')
s=s.replace('GlobalJournal64 journal;Obj58 report;', 'GlobalJournal64 journal;Arr58 nativeBefore;bool oldPlayerBackground;Obj58 report;')
needle=' public void Execute(ExecutionResult result)\n {'
if mode=='Compile72':
 s=s.replace(needle,needle+'\n  CompileOnly72(result);return;\n }\n void CompiledCaptureBody72(ExecutionResult result)\n {',1)
 s=s.replace(' void Tick()', ' void CompileOnly72(ExecutionResult result){result.Log("72 whole observer compiled; no Play, snapshot or settings change executed");}\n void Tick()',1)
s=s.replace('domain=AppDomain.CurrentDomain.Id;oldBackground=', 'oldPlayerBackground=PlayerSettings.runInBackground;nativeBefore=NativeSnapshot72.Backup(Root);domain=AppDomain.CurrentDomain.Id;oldBackground=',1)
s=s.replace('report["afterMemory"]=Memory();report["afterDirty"]=', 'report["nativeComparisons72"]=nativeBefore==null?new Arr58():NativeSnapshot72.Compare(Root,nativeBefore);report["playerSettingsRunInBackgroundRestored"]=PlayerSettings.runInBackground==oldPlayerBackground;report["afterMemory"]=Memory();report["afterDirty"]=',1)
start=s.index('  var e=UnityEngine.Object.FindObjectsByType<EyeFeature348>');end=s.rfind('\n',0,s.index('report["modeFlags"]',start))+1
patch=(B/'EYE_CALLER70.patch').read_text(encoding='utf-8');plus='\n'.join(x[1:] for x in patch.splitlines() if x.startswith('+') and not x.startswith('+++'))+'\n'
plus=plus.replace('  if(e){','  if(!e)throw new InvalidOperationException("Eye host observer unavailable; no valid eye packet");\n  if(e){',1)
s=s[:start]+plus+s[end:]
s=s.replace('report["missingBeforeOfflineBinding"]=new Arr58(', 'report["observerProtocol72"]="direct-host typed48/256 ROI only";report["missingBeforeOfflineBinding"]=new Arr58(',1)
# Keep normal renderer/history; prohibit old buffer reader for48/256.
assert 'FindObjectsByType<EyeFeature348>' not in s
assert 'Readback.Records' in s and 'Readback.Counts' in s
(HERE/(mode+'.cs')).write_text(s,encoding='utf-8')
deps=[OLD/'Json58Linear66.cs',OLD/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',B/'EyeReadback70.cs',B/'UnityEyeBuffer70.cs',HERE/'NativeSnapshot72.cs',HERE/(mode+'.cs')]
target=HERE/('RUN_'+mode+'.cs.txt')
if target.exists() and mode=='Compile72' and (HERE/'Compile72_REPLY.json').exists():
 previous=__import__('json').loads((HERE/'Compile72_REPLY.json').read_text(encoding='utf-8'))
 assert previous['data']['isCompilationSuccessful'] is False and previous['data']['isExecutionSuccessful'] is False
 archive=HERE/'RUN_Compile72_COMPILE_FAILURE1.cs.txt';assert not archive.exists();archive.write_bytes(target.read_bytes())
bundle(deps,target)
# Installed SDK MoveToNamespace rewrites only the first existing namespace.
# Explicitly wrap the whole command in its expected namespace so nested protocol
# namespaces and IRunCommand are retained together; no SDK/package edits.
code=target.read_text(encoding='utf-8');uses=re.findall(r'(?m)^using [^;\n]+;',code);body=re.sub(r'(?m)^using [^;\n]+;\r?\n?','',code)
target.write_text('\n'.join(uses)+'\nnamespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor\n{\n'+body+'\n}\n',encoding='utf-8')
if not (HERE/'GLOBAL_NAMES66.json').exists():(HERE/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
print('Prepared',mode,'outside Assets; compile only' if mode=='Compile72' else 'one-shot Play observer, not executed')
