"""Prepare one-shot append-only observer; no Unity call or Assets import."""
from pathlib import Path
import sys,re
HERE=Path(__file__).resolve().parent
def sibling(short,archived):
 p=HERE.parent/short
 return p if p.exists() else HERE.parent/archived
OLD=sibling('apply-capture66','2026-10-31-apply-capture66');P72=sibling('eye-observer72','2026-11-01-eye-observer72');B=sibling('boundary-input69','2026-11-01-boundary-input69');U=sibling('uv-features64','2026-10-31-uv-features64')
sys.path.insert(0,str(B));from prepare73 import bundle
mode=sys.argv[1];assert mode in ('Compile73','Capture73','Post73')
if mode=='Post73':
 s=(HERE/'Read73.cs').read_text(encoding='utf-8').replace('CURRENT73.json','POST73.json').replace('File.WriteAllText(','CreateOnly73.Text(')
 needle='  result.Log("66 read only:'
 at=s.index(needle);s=s[:at]+'  var ps=Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Single(x=>x&&x.GetType()==typeof(PlayerSettings));CreateOnly73.Text(@"'+str(HERE/'PLAYER_AFTER73.json')+'",EditorJsonUtility.ToJson(ps));\n'+s[at:]
 (HERE/'Post73.cs').write_text(s,encoding='utf-8');bundle([OLD/'Json58Linear66.cs',HERE/'CreateOnly73.cs',HERE/'Post73.cs'],HERE/'RUN_Post73.cs.txt');print('Prepared read-only postflight plus full PlayerSettings serialization');raise SystemExit
native=(P72/'NativeSnapshot72.cs').read_text(encoding='utf-8').replace('NativeSnapshot72','NativeSnapshot73').replace('File.WriteAllText(file,text,new System.Text.UTF8Encoding(false))','CreateOnly73.Text(file,text)').replace('File.WriteAllText(Path.Combine(root,"NATIVE_BEFORE72.json"),rows.ToString())','CreateOnly73.Text(Path.Combine(root,"NATIVE_BEFORE73.json"),rows.ToString())')
(HERE/'NativeSnapshot73.cs').write_text(native,encoding='utf-8')
s=(P72/'Capture72.cs').read_text(encoding='utf-8').replace('eye-observer72','eye-observer73').replace('NativeSnapshot72','NativeSnapshot73').replace('eye72-','eye73-').replace('capture67-','eye73-')
s=s.replace('string output,sourceId;','string output,sourceId;int stateSequence;')
start=s.index(' void Save(string stage)');end=s.index('\n public void Execute',start)
s=s[:start]+''' void Save(string stage){report["stage"]=stage;report["utc"]=DateTime.UtcNow.ToString("O");report["planes"]=planes;CreateOnly73.Text(Path.Combine(Root,"STATE73-"+(stateSequence++).ToString("D4")+"-"+stage+".json"),report.ToString());}
'''+s[end:]
s=s.replace('if(File.Exists(Path.Combine(Root,"CAPTURE_STATE72.json")))throw new InvalidOperationException("Existing capture outcome must be inspected; no repeat");','if(File.Exists(Path.Combine(Root,"CAPTURE_STARTED73.json")))throw new InvalidOperationException("Existing capture outcome must be inspected; no repeat");CreateOnly73.Text(Path.Combine(Root,"CAPTURE_STARTED73.json"),"one approved observer invocation");')
s=s.replace('DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ");output=', 'DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ")+"-"+Guid.NewGuid().ToString("N").Substring(0,8);output=')
s=s.replace('Directory.CreateDirectory(output);','if(Directory.Exists(output))throw new IOException("Unique output required");Directory.CreateDirectory(output);',1)
s=s.replace('File.AppendAllText(Path.Combine(Root,"WAIT_TRACE.jsonl"),','CreateOnly73.Text(Path.Combine(Root,"TRACE73-"+Guid.NewGuid().ToString("N")+".json"),')
s=s.replace('File.Create(path)','new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read)').replace('File.Create(Path.Combine(output,name+".buffer"))','new FileStream(Path.Combine(output,name+".buffer"),FileMode.CreateNew,FileAccess.Write,FileShare.Read)').replace('File.WriteAllText(Path.Combine(output,"RAW_MANIFEST.json"),report.ToString())','CreateOnly73.Text(Path.Combine(output,"RAW_MANIFEST.json"),report.ToString())')
s=s.replace('eye-counts70.bin','eye-counts73.bin').replace('eye-records70.bin','eye-records73.bin')
if mode=='Compile73':
 needle=' public void Execute(ExecutionResult result)\n {';assert needle in s
 s=s.replace(needle,needle+'\n  result.Log("73 entire append-only observer compiled; capture/backup/options not executed");return;\n }\n void CompiledCaptureBody73(ExecutionResult result)\n {',1)
(HERE/(mode+'.cs')).write_text(s,encoding='utf-8')
deps=[OLD/'Json58Linear66.cs',OLD/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',HERE/'EyeReadback73.cs',HERE/'UnityEyeBuffer70.cs',HERE/'CreateOnly73.cs',HERE/'NativeSnapshot73.cs',HERE/(mode+'.cs')]
target=HERE/('RUN_'+mode+'.cs.txt');bundle(deps,target)
full=target.read_text(encoding='utf-8')
for bad in ['File.Move(','Directory.Move(','File.Delete(','Directory.Delete(','File.WriteAllText(','File.AppendAllText(','FileMode.Create,','File.Create(']:assert bad not in full,bad
assert 'Readback.Counts' in full and 'Readback.Records' in full and 'DisableDomainReload' in full
print('Prepared',mode,'outside Assets, CreateNew-only output; not invoked')
