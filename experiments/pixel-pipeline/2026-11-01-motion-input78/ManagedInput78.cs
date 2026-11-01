using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.InputSystem;
internal class CommandScript:IRunCommand{
 public void Execute(ExecutionResult result){var s=InputSystem.settings;var r=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["managedNull"]=System.Object.ReferenceEquals(s,null),["nativeAlive"]=s?true:false};if(!System.Object.ReferenceEquals(s,null)){try{r["jsonUtilityJSON"]=JsonUtility.ToJson(s);}catch(Exception e){r["jsonError"]=e.ToString();}try{r["background"]=s.backgroundBehavior.ToString();r["editorBehavior"]=s.editorInputBehaviorInPlayMode.ToString();r["updateMode"]=s.updateMode.ToString();r["deadzoneMin"]=s.defaultDeadzoneMin;r["deadzoneMax"]=s.defaultDeadzoneMax;r["supportedDevices"]=new Arr58(s.supportedDevices.ToArray());}catch(Exception e){r["getterError"]=e.ToString();}}CreateOnly73.Text(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\eye-motion78\run\MANAGED_INPUT_VALUES78.json",r.ToString());result.Log("78 managed input payload read only; no settings replacement");}
}
