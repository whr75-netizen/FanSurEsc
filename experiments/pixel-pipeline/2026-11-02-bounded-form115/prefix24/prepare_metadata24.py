"""Reuse bounded Json58Linear66 for live case/receipt metadata; no GPU changes."""
from pathlib import Path
import json,re,hashlib
H=Path(__file__).resolve().parent;R=H/'metadata24';R.mkdir(exist_ok=True);(R/'decode-output').mkdir(exist_ok=True)
source=H.parent.parent/'apply-capture66/Json58Linear66.cs'
s=source.read_text();uses=re.findall(r'(?m)^using [^;\n]+;',s);body=re.sub(r'(?m)^using [^;\n]+;\r?\n?','',s)
scoped='\n'.join(uses)+'\nnamespace Prefix24 {\n'+body+'\n}\n'
with(R/'Json58Linear24.cs').open('x',encoding='utf-8',newline='\n')as f:f.write(scoped)
def bundle(entry,parts):
 us=[];bs=[]
 for s in parts:
  for line in re.findall(r'(?m)^using [^;\n]+;',s):
   if line not in us:us.append(line)
  bs.append(re.sub(r'(?m)^using [^;\n]+;\r?\n?','',s))
 return '\n'.join(us)+'\n'+entry+'\n'+'\n'.join(bs)
base=(H/'import-stage1-b/ReadDecode24.cs.txt').read_text()
base=base.replace('Root+@"\\import-stage1-b\\decode-output"','Root+@"\\metadata24\\decode-output"')
a=base.index('    var old=JsonUtility.FromJson<OldCase24>');b=base.index('    var expected=',a)
base=base[:a]+'''    var typed=(global::Prefix24.Case24)global::Prefix24.PrefixMetadata24.Decode(Encoding.UTF8.GetBytes(json),typeof(global::Prefix24.Case24));
    var c=new PrefixImportCase24{Globals=typed.Globals.Select(g=>new PrefixImportGlobal24{Name=g.Name,Type=g.Type}).ToArray()};
    r.OldCount=-1;r.OldNullRecords=-1;r.NewCount=c.Globals.Length;r.NewNullRecords=c.Globals.Count(g=>g==null);r.SchemaEqual=r.NewCount==74&&r.NewNullRecords==0;
''' +base[b:]
parts=[base,(R/'Json58Linear24.cs').read_text(),(H/'Prefix24Protocol.cs').read_text(),(H/'PrefixMetadata24.cs').read_text()]
read=bundle('',parts)
with(R/'ReadMetadataState24.command.cs.txt').open('x',encoding='utf-8',newline='\n')as f:f.write(read)
imp=(H/'import-stage1/ImportPrefix24B.cs.txt').read_text().replace('Root+@"\\import-stage1-b"','Root+@"\\metadata24"')
needle='    c=(PrefixImportCase24)JsonUtility.FromJson(File.ReadAllText(Path.Combine(Root,"CASE.json")),typeof(PrefixImportCase24));'
assert needle in imp
imp=imp.replace(needle,'    var typed=(global::Prefix24.Case24)global::Prefix24.PrefixMetadata24.Decode(File.ReadAllBytes(Path.Combine(Root,"CASE.json")),typeof(global::Prefix24.Case24));\n    c=new PrefixImportCase24{Globals=typed.Globals.Select(g=>new PrefixImportGlobal24{Name=g.Name,Type=g.Type}).ToArray()};')
imp=bundle('',[imp,*parts[1:]])
with(R/'ImportMetadata24.command.cs.txt').open('x',encoding='utf-8',newline='\n')as f:f.write(imp)
host=(H/'Prefix24Host.cs').read_text().replace('Protocol24.Encode=value=>Encoding.UTF8.GetBytes(JsonUtility.ToJson(value));','Protocol24.Encode=value=>value is Receipt24?PrefixMetadata24.ReceiptBytes((Receipt24)value):Encoding.UTF8.GetBytes(JsonUtility.ToJson(value));').replace('Protocol24.Decode=(bytes,type)=>JsonUtility.FromJson(Encoding.UTF8.GetString(bytes),type);','Protocol24.Decode=PrefixMetadata24.Decode;')
entry='namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {internal class CommandScript : IRunCommand {public void Execute(ExecutionResult result){global::Prefix24.Prefix24Host.Start(1,message=>result.Log(message));}}}'
stage=bundle(entry,[(H/'Prefix24Protocol.cs').read_text(),(H/'CaseLock24.cs').read_text(),host,*parts[1:2],parts[3]])
assert stage.count('shader.Dispatch(')==1 and all(x not in stage for x in ['EvaluateForm115','BoundRun115','AssetDatabase.ImportAsset','EnterPlaymode'])
with(R/'STAGE1_METADATA24.command.cs.txt').open('x',encoding='utf-8',newline='\n')as f:f.write(stage)
record={'linearReaderOriginalSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'commands':{name:hashlib.sha256((R/name).read_bytes()).hexdigest()for name in ['ReadMetadataState24.command.cs.txt','ImportMetadata24.command.cs.txt','STAGE1_METADATA24.command.cs.txt']},'shaderSHA256':hashlib.sha256((H/'Prefix24.compute').read_bytes()).hexdigest(),'shaderChanged':False,'GPUCalls':0,'UnityCalls':0}
with(R/'PREPARED_METADATA24.json').open('x',encoding='utf-8')as f:json.dump(record,f,indent=2)
print(json.dumps(record,indent=2))
