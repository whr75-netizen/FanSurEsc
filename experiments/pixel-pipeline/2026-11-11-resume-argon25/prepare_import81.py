"""Create-only shader import command, using the existing snapshot/helper path."""
from pathlib import Path
import hashlib,json,uuid
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face81'

def main():
 assert not(G/'import/REQUEST.json').exists();path=G/'import/EXPECTED.json'
 if not path.exists():path.write_text(json.dumps({'guid':uuid.uuid4().hex,'shaderSHA256':hashlib.sha256((H/'FeatureCurve81.shader').read_bytes()).hexdigest()},indent=2))
 source=(H/'face75/import/RUN.cs.txt').read_text();source=source[:source.index('internal class CommandScript:IRunCommand')]
 command=r'''internal class CommandScript:IRunCommand {
 const string Root=@"ROOT81";const string Source=@"SOURCE81";const string Target="Assets/EUnityValidation01/FeatureCurve81/FeatureCurve81.shader";
 public void Execute(ExecutionResult result){CreateOnly40.Text(Path.Combine(Root,"STARTED.json"),DateTime.UtcNow.ToString("O"));var report=new Obj40();try{
 if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating||Enumerable.Range(0,SceneManager.sceneCount).Select(SceneManager.GetSceneAt).Any(s=>s.isDirty))throw new InvalidOperationException("81 stable clean Edit required");
 if(File.Exists(Target)||File.Exists(Target+".meta")||AssetDatabase.IsValidFolder("Assets/EUnityValidation01/FeatureCurve81"))throw new InvalidOperationException("81 create-only destination already exists; do not overwrite");
 var expected=Json40.Parse(File.ReadAllText(Path.Combine(Root,"EXPECTED.json")));string guid=(string)expected["guid"];if(!String.IsNullOrEmpty(AssetDatabase.GUIDToAssetPath(guid)))throw new InvalidOperationException("81 GUID collision");
 Func<byte[],string> hash=b=>{using(var d=SHA256.Create())return BitConverter.ToString(d.ComputeHash(b)).Replace("-","").ToLowerInvariant();};byte[] bytes=File.ReadAllBytes(Source);if(hash(bytes)!=(string)expected["shaderSHA256"])throw new InvalidOperationException("81 prepared shader differs");
 var before=NativeSnapshot40.Backup(Root);var input=InputSystem.settings;string json=JsonUtility.ToJson(input);bool options=EditorSettings.enterPlayModeOptionsEnabled;var flags=EditorSettings.enterPlayModeOptions;
 string folder=AssetDatabase.CreateFolder("Assets/EUnityValidation01","FeatureCurve81");if(String.IsNullOrEmpty(folder))throw new IOException("81 folder create failed");CreateOnly40.Text(Target+".meta","fileFormatVersion: 2\nguid: "+guid+"\nShaderImporter:\n  externalObjects: {}\n  defaultTextures: []\n  nonModifiableTextures: []\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n");using(var f=new FileStream(Target,FileMode.CreateNew,FileAccess.Write,FileShare.Read)){f.Write(bytes,0,bytes.Length);f.Flush(true);}AssetDatabase.ImportAsset(Target,ImportAssetOptions.ForceSynchronousImport);
 var shader=AssetDatabase.LoadAssetAtPath<Shader>(Target);if(!shader||ShaderUtil.ShaderHasError(shader)||hash(File.ReadAllBytes(Target))!=hash(bytes)||AssetDatabase.AssetPathToGUID(Target)!=guid)throw new InvalidOperationException("81 shader/import/GUID validation failed");var messages=ShaderUtil.GetShaderMessages(shader);if(messages.Any(m=>m.severity.ToString()=="Error"))throw new InvalidOperationException("81 new shader error");
 var checks=NativeSnapshot40.Compare(Root,before);if(checks.Any(c=>c["equal"]!=null&&!(bool)c["equal"]))throw new InvalidOperationException("81 existing native content changed");if(!System.Object.ReferenceEquals(input,InputSystem.settings)||JsonUtility.ToJson(input)!=json||options!=EditorSettings.enterPlayModeOptionsEnabled||flags!=EditorSettings.enterPlayModeOptions||EditorApplication.isCompiling)throw new InvalidOperationException("81 input/options/compiler changed");
 report["utc"]=DateTime.UtcNow.ToString("O");report["shaderSHA256"]=hash(bytes);report["guid"]=guid;report["nativeChecks"]=checks;report["inputOptionsSame"]=true;report["CSharpImport"]=false;report["renderDispatchPlay"]=0;report["shaderMessages"]=new Arr40(messages.Select(m=>new Obj40{["severity"]=m.severity.ToString(),["message"]=m.message}));CreateOnly40.Text(Path.Combine(Root,"COMPLETE.json"),report.ToString());result.Log("81 create-only tiny raster shader imported; existing native/input/options preserved; no Play/GPU submission");
 }catch(Exception e){report["error"]=e.ToString();CreateOnly40.Text(Path.Combine(Root,"FAILED.json"),report.ToString());result.Log("81 import stopped: "+e.Message);}}
 }
}
'''.replace('ROOT81',str(G/'import')).replace('SOURCE81',str(H/'FeatureCurve81.shader'))
 p=G/'import/RUN.cs.txt';p.write_text(source+command,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/import81.dll');print('CPU compiled shader-only create/import command')
if __name__=='__main__':main()
