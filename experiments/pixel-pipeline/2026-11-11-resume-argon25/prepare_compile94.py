"""Back up native/input/global state, hold only our import/reload scope.

Three source files are patched via apply_patch outside this command. The
paired release has one receipt and never saves assets or substitutes settings.
"""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face94/recompile'
def main():
 for d in ['pre','release','post','build']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['pre','release','post']);s=(H/'face94/final/RUN.cs.txt').read_text();prefix=s[:s.index('internal class CommandScript:IRunCommand')];root=str(G)
 common='''
internal class CommandScript:IRunCommand {
 const string Root=@"ROOT94";
 GlobalJournal40 Globals(string mode){var specs=Json40.Parse(File.ReadAllText(@"SPEC94")).Select(o=>new GlobalJournal40.Spec{name=(string)o["name"],kind=(string)o["type"]=="Int"?GlobalJournal40.Kind.LegacyInt:(GlobalJournal40.Kind)Enum.Parse(typeof(GlobalJournal40.Kind),(string)o["type"])}).ToArray();return GlobalJournal40.Snapshot("compile94",Path.Combine(Root,mode,"GLOBALS.bin"),specs);}
 Obj40 Input(){var devices=new Arr40();foreach(var d in InputSystem.devices)devices.Add(new Obj40{["id"]=d.deviceId,["layout"]=d.layout,["name"]=d.name});return new Obj40{["id"]=InputSystem.settings.GetEntityId().ToString(),["json"]=JsonUtility.ToJson(InputSystem.settings),["devices"]=devices};}
 public void Execute(ExecutionResult result){BODY94}
}
}
'''.replace('ROOT94',root).replace('SPEC94',str(H/'face29/run/GLOBAL_NAMES66.json'))
 body={
 'pre':'''if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("94 stable Edit before import");if((EditorApplication.update?.GetInvocationList()??Array.Empty<Delegate>()).Any(x=>x.Target is IRunCommand))throw new InvalidOperationException("94 pending external observer");string dir=Path.Combine(Root,"pre");var native=NativeSnapshot40.Backup(dir);CreateOnly40.Text(Path.Combine(dir,"INPUT.json"),Input().ToString());var journal=Globals("pre");var scenes=new Arr40();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);scenes.Add(new Obj40{["path"]=s.path,["dirty"]=s.isDirty});}CreateOnly40.Text(Path.Combine(dir,"BACKUP_COMPLETE.json"),new Obj40{["nativeCount"]=native.Count,["globalSHA"]=journal.backupSHA256,["scenes"]=scenes,["saveAssets"]=false,["utc"]=DateTime.UtcNow.ToString("O")}.ToString());bool editing=false,locked=false;try{AssetDatabase.StartAssetEditing();editing=true;EditorApplication.LockReloadAssemblies();locked=true;CreateOnly40.Text(Path.Combine(dir,"OWN_LOCK_HELD.json"),new Obj40{["editing"]=true,["reload"]=true,["utc"]=DateTime.UtcNow.ToString("O")}.ToString());}catch{if(locked)EditorApplication.UnlockReloadAssemblies();if(editing)AssetDatabase.StopAssetEditing();throw;}result.Log("94 native/input/global backup verified; one owned import/reload hold, no save");''',
 'release':'''if(!File.Exists(Path.Combine(Root,"pre","OWN_LOCK_HELD.json"))||File.Exists(Path.Combine(Root,"release","RELEASED.json")))throw new InvalidOperationException("94 hold receipt or duplicate release");try{foreach(var name in new[]{"ClosedRegion524.cs","OpacityRegion525.cs","ClothRegion524.cs"})AssetDatabase.ImportAsset("Assets/EUnityValidation01/ClothRegion524/Runtime/"+name,ImportAssetOptions.ForceUpdate);}finally{AssetDatabase.StopAssetEditing();EditorApplication.UnlockReloadAssemblies();}CreateOnly40.Text(Path.Combine(Root,"release","RELEASED.json"),new Obj40{["ownHoldReleased"]=true,["saveAssets"]=false,["utc"]=DateTime.UtcNow.ToString("O")}.ToString());result.Log("94 three targeted source imports requested; own import/reload hold released");''',
 'post':'''if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("94 compilation not finished; no rendering");string dir=Path.Combine(Root,"pre");var rows=(Arr40)Json40.Parse(File.ReadAllText(Path.Combine(dir,"NATIVE_BEFORE73.json")));var checks=NativeSnapshot40.Compare(dir,rows);var old=Json40.Parse(File.ReadAllText(Path.Combine(dir,"INPUT.json")));var now=Input();var journal=Globals("post");var pre=Json40.Parse(File.ReadAllText(Path.Combine(dir,"BACKUP_COMPLETE.json")));var report=new Obj40{["utc"]=DateTime.UtcNow.ToString("O"),["Edit"]=true,["nativeChecks"]=checks,["inputSameIdAndJSONAndDevices"]=Json40.DeepEquals(old,now),["globalBytesEqual"]=journal.backupSHA256==(string)pre["globalSHA"],["saveAssets"]=false};CreateOnly40.Text(Path.Combine(Root,"post","RESULT.json"),report.ToString());if(checks.Any(c=>c["equal"]!=null&&!(bool)c["equal"])||!Json40.DeepEquals(old,now)||journal.backupSHA256!=(string)pre["globalSHA"])throw new InvalidOperationException("94 post-recompile state comparison failed; no Play");result.Log("94 post-recompile Edit/native/input/globals preserved");'''}
 for name,b in body.items():
  p=G/name/'RUN.cs.txt';p.write_text(prefix+common.replace('BODY94',b),encoding='utf-8',newline='\n');compile_unity_language(p,G/'build'/(name+'94.dll'))
 print(json.dumps({'externalCommandsCompiled':True,'EditorOrImportExecuted':False,'nativeBackedBeforeOwnedImportHold':True,'noSettingsSubstitutionOrSave':True}))
if __name__=='__main__':main()
