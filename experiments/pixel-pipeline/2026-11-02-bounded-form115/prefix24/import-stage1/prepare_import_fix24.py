"""Prepare a deserialization guard revision only. Never submit it to Unity."""
from pathlib import Path
import difflib,hashlib,json
H=Path(__file__).resolve().parent
old=(H/'ImportPrefix24.cs.txt').read_text(encoding='utf-8')
s=old.replace('[Serializable] sealed class PrefixImportGlobal24','[Serializable] public sealed class PrefixImportGlobal24').replace('[Serializable] sealed class PrefixImportCase24','[Serializable] public sealed class PrefixImportCase24').replace('[Serializable] sealed class PrefixExpected24','[Serializable] public sealed class PrefixExpected24')
s=s.replace('JsonUtility.FromJson<PrefixExpected24>(File.ReadAllText(Path.Combine(Root,@"preflight24\\EDITOR_STATE24.json")))','(PrefixExpected24)JsonUtility.FromJson(File.ReadAllText(Path.Combine(Root,@"preflight24\\EDITOR_STATE24.json")),typeof(PrefixExpected24))')
s=s.replace('JsonUtility.FromJson<PrefixImportCase24>(File.ReadAllText(Path.Combine(Root,"CASE.json")))','(PrefixImportCase24)JsonUtility.FromJson(File.ReadAllText(Path.Combine(Root,"CASE.json")),typeof(PrefixImportCase24))')
needle='    var state=State(c,"before");'
assert s.count(needle)==1
s=s.replace(needle,'    if(c==null||c.Globals==null||c.Globals.Length!=74||c.Globals.Any(g=>g==null||String.IsNullOrEmpty(g.Name)||String.IsNullOrEmpty(g.Type)))throw new IOException("Case deserialization failed before native snapshot; no import");\n    if(expected==null||expected.InputId==null||expected.InputJson==null||expected.Dirty==null||expected.Scenes==null||expected.Devices==null)throw new IOException("Current baseline deserialization failed; no import");\n'+needle)
s=s.replace('const string Output=Root+@"\\import-stage1";','const string Output=Root+@"\\import-stage1-b";')
assert s!=old and 'FromJson<'not in s
for name,data in [('ImportPrefix24B.cs.txt',s),('ImportPrefix24B.patch',''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='ImportPrefix24.cs.txt',tofile='ImportPrefix24B.cs.txt')))]:
 with(H/name).open('x',encoding='utf-8',newline='\n')as f:f.write(data)
print(json.dumps({'variant':'B','sourceSHA256':hashlib.sha256(s.encode()).hexdigest(),'UnityCalls':0,'GPUDispatches':0,'status':'prepared-only; public DTO/non-generic API are a hypothesis; explicit null guards are confirmed missing validation'}))
