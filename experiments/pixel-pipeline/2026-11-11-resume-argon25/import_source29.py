"""Prepare the existing small state-preserving shader-only import procedure."""
from pathlib import Path
import hashlib,json,shutil,sys
H=Path(__file__).resolve().parent;G=H/'face29';P=H/'producer/support/surface27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 repair='--repair'in sys.argv
 root=G/('fixed-import'if repair else'import');root.mkdir(exist_ok=True);assert not(root/'IMPORT_REQUEST.json').exists()
 old=P/'RUN_Import25.cs.txt';s=old.read_text(encoding='utf-8');s=s.replace(str(P/'import'),str(root))
 prefix=H.parent/'bounded-form115/prefix24'
 s=s.replace('const string Root=@"'+str(prefix)+'";','const string Root=@"'+str(root)+'";')
 start=s.index('    const string folder=');end=s.index('    var after=Json(State(c,"after"))',start)
 block='''    const string folder="Assets/EUnityValidation01/SourceBoundary29",surface=folder+"/SourceOutline29.shader";
    string project=Directory.GetParent(Application.dataPath).FullName;
    if(project!=@"C:\\Users\\15352\\Documents\\work\\Fantasy Survival Escape Game")throw new IOException("Project changed");
    if(Directory.Exists(Path.Combine(project,folder))||File.Exists(Path.Combine(project,folder)+".meta")||AssetDatabase.IsValidFolder(folder))throw new IOException("29 target exists; never overwrite");
    var bytes=File.ReadAllBytes(@"'''+str(G/'SourceOutline29.shader')+'''");if(Hash(bytes)!="'''+sha(G/'SourceOutline29.shader')+'''")throw new IOException("29 reviewed shader changed");
    New("INTENT.json",Json(receipt));if(String.IsNullOrEmpty(AssetDatabase.CreateFolder("Assets/EUnityValidation01","SourceBoundary29")))throw new IOException("29 folder creation incomplete");
    using(var f=new FileStream(Path.Combine(project,surface),FileMode.CreateNew,FileAccess.Write,FileShare.Read)){f.Write(bytes,0,bytes.Length);f.Flush(true);}AssetDatabase.ImportAsset(surface,ImportAssetOptions.ForceSynchronousImport);
    Stable();var shader=AssetDatabase.LoadAssetAtPath<Shader>(surface);if(!shader||!shader.isSupported)throw new IOException("29 source shader unavailable/unsupported");
    var messages=new List<string>();foreach(var m in ShaderUtil.GetShaderMessages(shader)){messages.Add(m.severity+"|"+m.message);if(m.severity.ToString()=="Error")throw new IOException("29 source compile error: "+m.message);}
    receipt.Messages=messages.ToArray();receipt.Guid=AssetDatabase.AssetPathToGUID(surface);receipt.KernelGroups=new string[0];
'''
 if repair:
  old_sha=json.loads((G/'PREPARED_IMPORT29.json').read_text(encoding='utf-8'))['shaderSHA256']
  check='    if(Directory.Exists(Path.Combine(project,folder))||File.Exists(Path.Combine(project,folder)+".meta")||AssetDatabase.IsValidFolder(folder))throw new IOException("29 target exists; never overwrite");'
  block=block.replace(check,'    if(!AssetDatabase.IsValidFolder(folder)||Hash(File.ReadAllBytes(Path.Combine(project,surface)))!="'+old_sha+'")throw new IOException("29 owned failed shader changed; never overwrite unrelated state");')
  create='New("INTENT.json",Json(receipt));if(String.IsNullOrEmpty(AssetDatabase.CreateFolder("Assets/EUnityValidation01","SourceBoundary29")))throw new IOException("29 folder creation incomplete");'
  block=block.replace(create,'New("INTENT.json",Json(receipt));')
  block=block.replace('FileMode.CreateNew,FileAccess.Write,FileShare.Read','FileMode.Create,FileAccess.Write,FileShare.Read')
 s=s[:start]+block+s[end:]
 out=root/'RUN_Import25.cs.txt';out.write_text(s,encoding='utf-8',newline='\n');shutil.copyfile(prefix/'CASE.json',root/'CASE.json')
 sys.path.insert(0,str(H/'producer'));from prepare_live import compile_cs
 compile_cs(out)
 relay=(P/'relay_pigment.py').read_text(encoding='utf-8');relay=relay.replace("assert mode in ['phase']","assert mode in ['import','phase']")
 relay=relay.replace("root=H/'pigment-run'","root=H/('"+('fixed-import'if repair else'import')+"'if mode=='import'else'run')")
 contract='PREPARED_IMPORT29_FIX.json'if repair else'PREPARED_IMPORT29.json'
 relay=relay.replace("contract=load(H/'PIGMENT_PREPARED.json')","contract=load(H/'"+contract+"')")
 if repair:relay=relay.replace("done=load(H/'import/COMPLETE.json')","done=load(H/'fixed-import/COMPLETE.json')")
 relay=relay.replace('Four evaluated Open Close75 Close100 reopen states then normal exit and restore','One actual native-outline source frame and existing77 stage capture, normal exit/restore')
 (G/('relay29_fix.py'if repair else'relay29.py')).write_text(relay,encoding='utf-8',newline='\n')
 result={'importSourceSHA256':sha(out),'captureSourceSHA256':sha(G/'run/RUN_Capture25.cs.txt'),'shaderSHA256':sha(G/'SourceOutline29.shader'),'hostCPUCompile':'passed','importOrPlayExecuted':False}
 (G/contract).write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
