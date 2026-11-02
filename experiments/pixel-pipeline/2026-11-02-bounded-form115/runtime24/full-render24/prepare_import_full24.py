from pathlib import Path
import json,hashlib,re,sys
H=Path(__file__).resolve().parent;P=H.parent.parent/'prefix24';D=H/'import';D.mkdir(exist_ok=True)
s=(P/'enumerate24/PRE_STATE.command.cs.txt').read_text();a=s.index('  public void Execute(ExecutionResult result){');b=s.index('\nnamespace Prefix24 {',a);front=s[:a].replace('Root+@"\\enumerate24\\pre"', '@"'+str(D)+'"')
front=front.replace(' internal class CommandScript : IRunCommand {',' [Serializable] public class ImportFullReceipt24 {public string Status,Utc,SourceSha,Guid,BeforeSha,AfterSha,Error;public bool StateEqual;public string[] KernelGroups,Messages;}\n internal class CommandScript : IRunCommand {')
groups={k['entry']:k['audit']['threads']for k in json.loads((H.parent/'HLSL_RUNTIME24.json').read_text())['kernels']if k['activeEntrypoint']};groups['ComposeWhole113']=[8,8,1]
source=H/'ForwardEye113_Geometry24.compute';manifest=json.loads((H/'PREPARED_FULL24.json').read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['fullShaderSHA256']
schema='new string[]{'+','.join(json.dumps(k+':'+','.join(map(str,groups[k])))for k in manifest['activeKernels'])+'}'
body=r'''  public void Execute(ExecutionResult result){
   var receipt=new ImportFullReceipt24{Status="begin",Utc=DateTime.UtcNow.ToString("O")};
   try{
    Stable();if(SystemInfo.graphicsDeviceType!=GraphicsDeviceType.Direct3D11)throw new IOException("Confirmed D3D11 required");
    var typed=(global::Prefix24.Case24)global::Prefix24.PrefixMetadata24.Decode(File.ReadAllBytes(Path.Combine(Root,"CASE.json")),typeof(global::Prefix24.Case24));
    var c=new PrefixImportCase24{Globals=typed.Globals.Select(g=>new PrefixImportGlobal24{Name=g.Name,Type=g.Type}).ToArray()};
    byte[] before=Json(State(c,"before"));New("BEFORE.json",before);receipt.BeforeSha=Hash(before);
    const string folder="Assets/EUnityValidation01/Direct24Geometry",asset=folder+"/ForwardEye113_Geometry24.compute";
    string project=Directory.GetParent(Application.dataPath).FullName;if(project!=@"C:\Users\15352\Documents\work\Fantasy Survival Escape Game")throw new IOException("Project changed");
    if(Directory.Exists(Path.Combine(project,folder))||File.Exists(Path.Combine(project,folder)+".meta")||AssetDatabase.IsValidFolder(folder)||!String.IsNullOrEmpty(AssetDatabase.AssetPathToGUID(asset)))throw new IOException("Existing candidate folder/asset; inspect, never overwrite");
    byte[] source=File.ReadAllBytes(SOURCE_PATH);receipt.SourceSha=Hash(source);if(receipt.SourceSha!=SOURCE_HASH)throw new IOException("Reviewed shader source mismatch");
    New("INTENT.json",Json(receipt));string guid=AssetDatabase.CreateFolder("Assets/EUnityValidation01","Direct24Geometry");if(String.IsNullOrEmpty(guid))throw new IOException("Candidate folder creation incomplete");
    using(var file=new FileStream(Path.Combine(project,asset),FileMode.CreateNew,FileAccess.Write,FileShare.Read)){file.Write(source,0,source.Length);file.Flush(true);}
    AssetDatabase.ImportAsset(asset,ImportAssetOptions.ForceSynchronousImport);Stable();
    var shader=AssetDatabase.LoadAssetAtPath<ComputeShader>(asset);if(!shader)throw new IOException("Imported shader unavailable");receipt.Guid=AssetDatabase.AssetPathToGUID(asset);
    var kernels=new List<string>();foreach(string spec in GROUP_SCHEMA){var p=spec.Split(':');if(!shader.HasKernel(p[0]))throw new IOException("Missing kernel "+p[0]);uint x,y,z;shader.GetKernelThreadGroupSizes(shader.FindKernel(p[0]),out x,out y,out z);string row=p[0]+":"+x+","+y+","+z;if(row!=spec)throw new IOException("Kernel group differs "+row);kernels.Add(row);}receipt.KernelGroups=kernels.ToArray();
    var messages=ShaderUtil.GetComputeShaderMessages(shader);receipt.Messages=messages.Select(m=>m.severity+"|"+m.message).ToArray();if(messages.Any(m=>m.severity.ToString()=="Error"))throw new IOException("Imported shader compile error");
    var after=Json(State(c,"after"));New("AFTER.json",after);receipt.AfterSha=Hash(after);receipt.StateEqual=before.SequenceEqual(after);if(!receipt.StateEqual)throw new IOException("Native/public state changed during import");
    receipt.Status="complete";New("COMPLETE.json",Json(receipt));result.Log("Runtime24 isolated shader import complete;15 groups/ABI and before-after state match; dispatch0");
   }catch(Exception e){receipt.Status="failed";receipt.Error=e.ToString();New("FAILED.json",Json(receipt));result.Log("Runtime24 import stopped; inspect failed record; no dispatch");}
  }
 }
}
'''.replace('SOURCE_PATH','@"'+str(source)+'"').replace('SOURCE_HASH',json.dumps(manifest['fullShaderSHA256'])).replace('GROUP_SCHEMA',schema)
unit=front+body+s[b:]
with(H/'RUN_ImportFull24.cs.txt').open('x',encoding='utf-8',newline='\n')as f:f.write(unit)
sys.path.insert(0,str(P));import compile_cs_cpu as cc
row=next(x for x in json.loads((P/'CS_COMPILE.json').read_text())['compilations']if x['name']=='Stage1MonoReferences');refs=[Path(x[len('/reference:'):])for x in row['arguments']if x.startswith('/reference:')]
record=cc.compile_one('ImportFull24',[H/'RUN_ImportFull24.cs.txt'],refs)
with(H/'CPU_IMPORT24.json').open('x',encoding='utf-8')as f:json.dump(record,f,indent=2)
