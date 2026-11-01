using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
internal class CommandScript:IRunCommand{
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\visibility-backing91\import91b";
 Obj58 State(){var s=InputSystem.settings;return new Obj58{["domain"]=AppDomain.CurrentDomain.Id,["playing"]=EditorApplication.isPlaying,["compiling"]=EditorApplication.isCompiling,["settingsId"]=s.GetEntityId().ToString(),["settingsJSON"]=JsonUtility.ToJson(s),["deviceIds"]=new Arr58(InputSystem.devices.Select(d=>d.deviceId)),["scenes"]=new Arr58(Enumerable.Range(0,SceneManager.sceneCount).Select(i=>new Obj58{["path"]=SceneManager.GetSceneAt(i).path,["dirty"]=SceneManager.GetSceneAt(i).isDirty})),["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled,["options"]=(int)EditorSettings.enterPlayModeOptions};}
 public void Execute(ExecutionResult result){
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
  if(SystemInfo.supportedRenderTargetCount<8)throw new NotSupportedException("8 MRT needed for bounded source probe");
  if(!InputSystem.settings)throw new InvalidOperationException("Live settings required; never replace");
  if(!File.Exists(Path.Combine(Root,"BEFORE91.json"))){NativeSnapshot73.Backup(Root);CreateOnly73.Text(Path.Combine(Root,"BEFORE91.json"),State().ToString());result.Log("89 shader import preflight only");return;}
  var expected=Json58.Parse(File.ReadAllText(Path.Combine(Root,"BEFORE91.json")));var messages=new Arr58();
  foreach(string name in new[]{"OriginalProducer91.shader","RetargetProducer91.shader","CurrentBacking91.shader"}){string path="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/"+name;AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport);var shader=AssetDatabase.LoadAssetAtPath<UnityEngine.Shader>(path);if(!shader||!shader.isSupported)throw new InvalidOperationException("Candidate source shader unavailable "+path);foreach(var msg in ShaderUtil.GetShaderMessages(shader))messages.Add(new Obj58{["asset"]=path,["severity"]=msg.severity.ToString(),["message"]=msg.message});}
  var current=State();foreach(string key in new[]{"domain","playing","compiling","settingsId","settingsJSON","deviceIds","scenes","optionsEnabled","options"})if(!Json58.DeepEquals(current[key],expected[key]))throw new InvalidOperationException("Source shader import changed state "+key);
  var rows=new Arr58();foreach(var row in Json58.Parse(File.ReadAllText(Path.Combine(Root,"NATIVE_BEFORE73.json"))))rows.Add(new Obj58{["path"]=row["path"],["type"]=row["type"],["snapshot"]=row["snapshot"]});var checks=NativeSnapshot73.Compare(Root,rows);foreach(var row in checks)if((string)row["status"]!="ExactUTF8")throw new InvalidOperationException("Native content changed on source shader import");
  CreateOnly73.Text(Path.Combine(Root,"IMPORTED91.json"),new Obj58{["state"]=current,["nativeComparisons"]=checks,["messages"]=messages}.ToString());if(messages.Any(m=>(string)m["severity"]=="Error"))throw new InvalidOperationException("Native source shader compile error");result.Log("89 shader-only import; original state and source assets unchanged");
 }
}
