"""Reuse successful read-only collector and exact HEAD707 stage2 command."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;D=H/'enumerate24';D.mkdir(exist_ok=True)
base=(H/'metadata24/ReadMetadataState24.command.cs.txt').read_text();a=base.index('  public void Execute(ExecutionResult result){');b=base.index('\nnamespace Prefix24 {',a)
helper=base[b:];front=base[:a]
extra=' [Serializable] public sealed class EnumeratePreflight24 {public string Utc,Phase,StateSha256,ShaderSha256,ShaderGuid,KernelGroup;public string[] ShaderMessages;public bool StableEdit;public int Dispatches;}\n'
front=front.replace(' internal class CommandScript : IRunCommand {',extra+' internal class CommandScript : IRunCommand {')
for phase in ['pre','post']:
 (D/phase).mkdir(exist_ok=True)
 src=front.replace('Root+@"\\metadata24\\decode-output"','Root+@"\\enumerate24\\'+phase+'"')
 body=r'''  public void Execute(ExecutionResult result){
   Stable();if(Directory.GetParent(Application.dataPath).FullName!=@"C:\Users\15352\Documents\work\Fantasy Survival Escape Game"||SystemInfo.graphicsDeviceType!=GraphicsDeviceType.Direct3D11)throw new IOException("Current project/device differs");
   global::Prefix24.Protocol24.Decode=global::Prefix24.PrefixMetadata24.Decode;
   var typed=global::Prefix24.Protocol24.LoadCase(Root,"0bd1a3c7fbc3e30791cbcaa000854a6fafd79598f34a730b8a7e2e2c0559027b");
   global::Prefix24.Protocol24.Previous(typed,"0bd1a3c7fbc3e30791cbcaa000854a6fafd79598f34a730b8a7e2e2c0559027b",global::Prefix24.CaseLock24.RunRoot,2);
   var c=new PrefixImportCase24{Globals=typed.Globals.Select(g=>new PrefixImportGlobal24{Name=g.Name,Type=g.Type}).ToArray()};
   string path=Path.Combine(Directory.GetParent(Application.dataPath).FullName,typed.ShaderAssetPath);
   string sourceHash=Hash(File.ReadAllBytes(path));if(sourceHash!=typed.ShaderSha256||AssetDatabase.AssetPathToGUID(typed.ShaderAssetPath)!=typed.ShaderGuid)throw new IOException("Shader source/GUID differs");
   var shader=AssetDatabase.LoadAssetAtPath<ComputeShader>(typed.ShaderAssetPath);if(!shader||!shader.HasKernel("Enumerate113"))throw new IOException("Existing shader/Enumerate missing; no import");
   uint x,y,z;shader.GetKernelThreadGroupSizes(shader.FindKernel("Enumerate113"),out x,out y,out z);if(x!=64||y!=1||z!=1)throw new IOException("Enumerate group ABI differs");
   var messages=ShaderUtil.GetComputeShaderMessages(shader);if(messages.Any(m=>m.severity.ToString()=="Error"))throw new IOException("Existing shader compiler error; no dispatch");
   byte[] state=Json(State(c,"native"));New("STATE.json",state);
   New("COMPLETE.json",Json(new EnumeratePreflight24{Utc=DateTime.UtcNow.ToString("O"),Phase=PHASE_LITERAL,StateSha256=Hash(state),ShaderSha256=sourceHash,ShaderGuid=typed.ShaderGuid,KernelGroup=x+","+y+","+z,StableEdit=true,Dispatches=0,ShaderMessages=messages.Select(m=>m.severity+"|"+m.message).ToArray()}));
   result.Log("Read-only Enumerate PHASE_NAME state complete; no dispatch/import/Play");
  }
 }
}
'''.replace('PHASE_LITERAL',json.dumps(phase)).replace('PHASE_NAME',phase)
 # The proven collector bundle already includes scoped Json58/Protocol/Metadata.
 # Add only CaseLock, needed to read the existing real GPU predecessor.
 src+=body+helper+'\n'+(H/'CaseLock24.cs').read_text()
 assert 'shader.Dispatch('not in src and 'AssetDatabase.ImportAsset('not in src
 with(D/(phase.upper()+'_STATE.command.cs.txt')).open('x',encoding='utf-8',newline='\n')as f:f.write(src)
record={'scope':'one stage2 only','stage2CommandSHA256':hashlib.sha256((H/'STAGE2.command.cs.txt').read_bytes()).hexdigest(),'shaderChanged':False,'UnityOrGpuCalls':0}
with(D/'PREPARED_ENUMERATE24.json').open('x',encoding='utf-8')as f:json.dump(record,f,indent=2)
