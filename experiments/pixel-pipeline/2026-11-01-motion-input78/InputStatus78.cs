using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.InputSystem;
internal class CommandScript:IRunCommand{
 public void Execute(ExecutionResult result){var current=InputSystem.settings;var all=Resources.FindObjectsOfTypeAll<InputSettings>();var rows=new Arr58(all.Take(16).Select(s=>new Obj58{["id"]=s.GetEntityId().ToString(),["path"]=AssetDatabase.GetAssetPath(s),["flags"]=s.hideFlags.ToString(),["current"]=s==current}));InputSettings configured;bool configuredFound=EditorBuildSettings.TryGetConfigObject("com.unity.input.settings",out configured);var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["playing"]=EditorApplication.isPlaying,["compiling"]=EditorApplication.isCompiling,["settingsManagedNull"]=System.Object.ReferenceEquals(current,null),["settingsUnityAlive"]=current?true:false,["settingsId"]=current?current.GetEntityId().ToString():null,["settingsJSON"]=current?EditorJsonUtility.ToJson(current):null,["settingsPath"]=current?AssetDatabase.GetAssetPath(current):null,["settingsFlags"]=current?current.hideFlags.ToString():null,["loadedSettingsCount"]=all.Length,["settingsObjects"]=rows,["configuredAssetFound"]=configuredFound,["configuredPath"]=configured?AssetDatabase.GetAssetPath(configured):null,["temporaryDeviceRemaining"]=InputSystem.devices.Any(d=>d.name.StartsWith("Eye78",StringComparison.Ordinal))};CreateOnly73.Text(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\eye-motion78\run\CURRENT_INPUT78.json",report.ToString());result.Log("78 current InputSystem state read only; alive="+(current?true:false));}
}
