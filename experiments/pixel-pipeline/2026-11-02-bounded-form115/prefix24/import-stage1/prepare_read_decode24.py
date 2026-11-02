"""Reuse B's existing state collector in a strictly read-only command."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;OUT=H.parent/'import-stage1-b';OUT.mkdir(exist_ok=True);(OUT/'decode-output').mkdir(exist_ok=True)
s=(H/'ImportPrefix24B.cs.txt').read_text();s=s[:s.index('  public void Execute(ExecutionResult result){')]
s=s.replace('const string Output=Root+@"\\import-stage1-b";','const string Output=Root+@"\\import-stage1-b\\decode-output";')
s=s.replace(' internal class CommandScript : IRunCommand {',' [Serializable] sealed class OldGlobal24 {public string Name,Type;}\n [Serializable] sealed class OldCase24 {public OldGlobal24[] Globals;}\n [Serializable] public sealed class DecodeResult24 {public int OldCount,OldNullRecords,NewCount,NewNullRecords;public bool SchemaEqual,ExpectedValid,StateCollected,MatchesCurrentBaseline;public string Status,Error;}\n internal class CommandScript : IRunCommand {')
c=json.loads((H.parent/'CASE.json').read_text());schema=';'.join(g['Name']+'|'+g['Type']for g in c['Globals'])
body=r'''  public void Execute(ExecutionResult result){
   var r=new DecodeResult24{Status="begin"};
   try{
    Stable();var json=File.ReadAllText(Path.Combine(Root,"CASE.json"));
    var old=JsonUtility.FromJson<OldCase24>(json);r.OldCount=old==null||old.Globals==null?-1:old.Globals.Length;r.OldNullRecords=old==null||old.Globals==null?-1:old.Globals.Count(g=>g==null);
    var c=(PrefixImportCase24)JsonUtility.FromJson(json,typeof(PrefixImportCase24));r.NewCount=c==null||c.Globals==null?-1:c.Globals.Length;r.NewNullRecords=c==null||c.Globals==null?-1:c.Globals.Count(g=>g==null);
    r.SchemaEqual=r.NewCount==74&&r.NewNullRecords==0&&String.Join(";",c.Globals.Select(g=>g.Name+"|"+g.Type))==SCHEMA_LITERAL;
    var expected=(PrefixExpected24)JsonUtility.FromJson(File.ReadAllText(Path.Combine(Root,@"preflight24\EDITOR_STATE24.json")),typeof(PrefixExpected24));
    r.ExpectedValid=expected!=null&&expected.InputId!=null&&expected.InputJson!=null&&expected.Dirty!=null&&expected.Scenes!=null&&expected.Devices!=null;
    New("DECODE_SCHEMA24.json",Json(r));
    if(!r.SchemaEqual||!r.ExpectedValid)throw new IOException("Decoded schema/baseline invalid; no import");
    var state=State(c,"read");New("READ_STATE24.json",Json(state));r.StateCollected=true;
    r.MatchesCurrentBaseline=state.Playing==expected.Playing&&state.Transition==expected.Transition&&state.Compiling==expected.Compiling&&state.Updating==expected.Updating&&state.Paused==expected.Paused&&state.Background==expected.Background&&state.PlayerBackground==expected.PlayerBackground&&state.OptionsEnabled==expected.OptionsEnabled&&state.Options==expected.Options&&state.InputId==expected.InputId&&state.InputJson==expected.InputJson&&state.Dirty.SequenceEqual(expected.Dirty)&&state.Scenes.SequenceEqual(expected.Scenes)&&state.Devices.SequenceEqual(expected.Devices);
    if(!r.MatchesCurrentBaseline)throw new IOException("Current state changed; stop without import");
    r.Status="complete";New("DECODE_COMPLETE24.json",Json(r));result.Log("Read-only B decode/state succeeded; import/dispatch0");
   }catch(Exception e){r.Status="failed";r.Error=e.ToString();New("DECODE_FAILED24.json",Json(r));result.Log("Read-only decode stopped; inspect receipt; import/dispatch0");}
  }
 }
}
'''.replace('SCHEMA_LITERAL',json.dumps(schema))
s+=body
for bad in ['shader.Dispatch(', 'AssetDatabase.ImportAsset(', 'AssetDatabase.CreateFolder(', 'SaveAssets(', 'EnterPlaymode', 'SetGlobal']:assert bad not in s
with(OUT/'ReadDecode24.cs.txt').open('x',encoding='utf-8',newline='\n')as f:f.write(s)
with(OUT/'ImportPrefix24B.cs.txt').open('xb')as f:f.write((H/'ImportPrefix24B.cs.txt').read_bytes())
print(json.dumps({'readSourceSHA256':hashlib.sha256(s.encode()).hexdigest(),'schemaFields':len(c['Globals']),'UnityCalls':0}))
