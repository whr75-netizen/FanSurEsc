using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

// Small deliberate strong roots for the damaged managed wrapper and its exact
// payload. No reflection, callbacks, state-machine replay, input events or reset.
public static class InputRecoveryAnchor79
{
 public static InputSettings BeforeRecoveryReference,AdoptedReference;
 public static string BeforeRecoveryJSON;
 public static Keyboard BeforeKeyboard;
}
internal class CommandScript:IRunCommand
{
 const string Root=@"ROOT79";
 const string ExpectedSHA="ca3f68bea248d3f95f9daef0889228a710740dd1efc8867ffda63b97b07f4286";
 static string SHA(string text){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(System.Text.Encoding.UTF8.GetBytes(text))).Replace("-","").ToLowerInvariant();}
 static Obj58 State(){var scenes=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);scenes.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["loaded"]=s.isLoaded});}return new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["playing"]=EditorApplication.isPlaying,["compiling"]=EditorApplication.isCompiling,["updating"]=EditorApplication.isUpdating,["domain"]=AppDomain.CurrentDomain.Id,["scenes"]=scenes,["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled,["options"]=(int)EditorSettings.enterPlayModeOptions,["background"]=Application.runInBackground,["playerBackground"]=PlayerSettings.runInBackground,["timeScale"]=Time.timeScale,["captureDelta"]=Time.captureDeltaTime,["graphicsPipeline"]=AssetDatabase.GetAssetPath(GraphicsSettings.defaultRenderPipeline),["qualityPipeline"]=AssetDatabase.GetAssetPath(QualitySettings.renderPipeline),["deviceIds"]=new Arr58(InputSystem.devices.Select(d=>d.deviceId)),["deviceLayouts"]=new Arr58(InputSystem.devices.Select(d=>d.layout)),["keyboardId"]=Keyboard.current!=null?(Json58)Keyboard.current.deviceId:null};}
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required; no automatic retry");
  string payload=File.ReadAllText(Path.Combine(Root,"PAYLOAD79.json"));if(SHA(payload)!=ExpectedSHA)throw new InvalidOperationException("Recovered payload fingerprint changed");
  if(File.Exists(Path.Combine(Root,"RECOVERY_STARTED79.marker")))throw new IOException("Existing outcome must be inspected before any retry");
  var before=InputSystem.settings;if(System.Object.ReferenceEquals(before,null)||before)throw new InvalidOperationException("Expected damaged managed wrapper no longer matches; do not overwrite a live/user setting");
  string beforeJson=JsonUtility.ToJson(before);if(beforeJson!=payload)throw new InvalidOperationException("Managed values changed since recovery evidence; preserve current state, no overwrite");
  InputRecoveryAnchor79.BeforeRecoveryReference=before;InputRecoveryAnchor79.BeforeRecoveryJSON=beforeJson;InputRecoveryAnchor79.BeforeKeyboard=Keyboard.current;
  var state=State();var report=new Obj58{["before"]=state,["beforeNativeAlive"]=before?true:false,["beforeManagedNull"]=false,["beforeJSON"]=beforeJson,["beforeSHA"]=SHA(beforeJson),["managedReferenceRetained"]=System.Object.ReferenceEquals(InputRecoveryAnchor79.BeforeRecoveryReference,before),["privateReflection"]=false,["PlayEntries"]=0,["assetWrites"]=0};
  try{report["beforePublicIMGUIComposite"]=before.useIMGUIEditorForAssets;}catch(Exception e){report["beforePublicIMGUICompositeError"]=e.GetType().Name+": "+e.Message;}
  CreateOnly73.Text(Path.Combine(Root,"RECOVERY_BEFORE79.json"),report.ToString());
  var nativeBefore=NativeSnapshot73.Backup(Root);
  CreateOnly73.Text(Path.Combine(Root,"RECOVERY_STARTED79.marker"),"One native InputSettings reconstruction from actual recovered22-field JSON; no defaults assigned");
  InputSettings candidate=null;bool adopted=false;
  try
  {
   candidate=ScriptableObject.CreateInstance<InputSettings>();
   JsonUtility.FromJsonOverwrite(payload,candidate);
   candidate.hideFlags=HideFlags.HideAndDontSave; // same temporary lifetime as InputManager.CreateAndInitialize
   string roundtrip=JsonUtility.ToJson(candidate);
   CreateOnly73.Text(Path.Combine(Root,"CANDIDATE_ROUNDTRIP79.json"),roundtrip);
   report["candidateSHA"]=SHA(roundtrip);report["candidateExactBeforeAssignment"]=roundtrip==payload;
   if(roundtrip!=payload)throw new InvalidOperationException("New object differs from recovered serialized values; not assigning");
   if(InputSystem.settings||!System.Object.ReferenceEquals(InputSystem.settings,before))throw new InvalidOperationException("Current settings changed before adoption");
   try{InputSystem.settings=candidate;}
   finally{adopted=System.Object.ReferenceEquals(InputSystem.settings,candidate);if(adopted)InputRecoveryAnchor79.AdoptedReference=candidate;}
   var actual=InputSystem.settings;string afterJson=JsonUtility.ToJson(actual);
   report["adopted"]=adopted;report["afterNativeAlive"]=actual?true:false;report["afterJSON"]=afterJson;report["afterSHA"]=SHA(afterJson);report["afterExact"]=afterJson==payload;report["newNativeId"]=actual.GetEntityId().ToString();report["originalNativeIdentityRestored"]=false;report["path"]=AssetDatabase.GetAssetPath(actual);report["persistent"]=EditorUtility.IsPersistent(actual);report["hideFlags"]=actual.hideFlags.ToString();
   report["publicGetters"]=new Obj58{["background"]=actual.backgroundBehavior.ToString(),["editorBehavior"]=actual.editorInputBehaviorInPlayMode.ToString(),["updateMode"]=actual.updateMode.ToString(),["deadzoneMin"]=actual.defaultDeadzoneMin,["deadzoneMax"]=actual.defaultDeadzoneMax,["supportedDevices"]=new Arr58(actual.supportedDevices.ToArray()),["pollingFrequency"]=InputSystem.pollingFrequency,["useIMGUIEditorForAssetsComposite"]=actual.useIMGUIEditorForAssets};
   report["keyboardReferencePreserved"]=System.Object.ReferenceEquals(Keyboard.current,InputRecoveryAnchor79.BeforeKeyboard);var after=State();report["after"]=after;var native=NativeSnapshot73.Compare(Root,nativeBefore);report["nativeComparisons"]=native;
   var unchanged=new Obj58();foreach(string key in new[]{"playing","compiling","updating","domain","scenes","optionsEnabled","options","background","playerBackground","timeScale","captureDelta","graphicsPipeline","qualityPipeline","deviceIds","deviceLayouts","keyboardId"})unchanged[key]=Json58.DeepEquals(state[key],after[key]);report["otherStateUnchanged"]=unchanged;
   report["featureFlagsStatus"]="m_FeatureFlags is NonSerialized/internal; no public enumeration/getter. Public IMGUI property is a composite observation only; no inferred flags set or claimed restored.";
   report["owner"]="InputManager owns the adopted HideAndDontSave temporary; observer does not destroy an active settings object";
   if(!adopted||!actual||afterJson!=payload)throw new InvalidOperationException("Public settings getter/roundtrip failed after adoption; inspect saved result");
   foreach(string key in new[]{"playing","compiling","updating","domain","scenes","optionsEnabled","options","background","playerBackground","timeScale","captureDelta","graphicsPipeline","qualityPipeline","deviceIds","deviceLayouts","keyboardId"})if(!(bool)unchanged[key])throw new InvalidOperationException("Other state changed: "+key);
   foreach(Obj58 row in native)if((string)row["status"]!="ExactUTF8")throw new InvalidOperationException("Native comparison requires review: "+(string)row["path"]+" "+(string)row["status"]);
   CreateOnly73.Text(Path.Combine(Root,"RECOVERY_RESULT79.json"),report.ToString());
   CreateOnly73.Text(Path.Combine(Root,"RECOVERY_CONTENT_COMPLETE79.marker"),SHA(afterJson));
   result.Log("79 InputSettings native object restored from exact recovered22-field JSON; no Play/reset/save");
  }
  catch(Exception e){report["error"]=e.ToString();report["adopted"]=adopted;CreateOnly73.Text(Path.Combine(Root,"RECOVERY_FAILED79.json"),report.ToString());throw;}
  finally{if(candidate&&!adopted&&!System.Object.ReferenceEquals(InputSystem.settings,candidate))UnityEngine.Object.DestroyImmediate(candidate);}
 }
}
