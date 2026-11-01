using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand{
 public void Execute(ExecutionResult result){var managers=Resources.FindObjectsOfTypeAll<ScriptableObject>().Where(o=>o&&o.GetType().FullName=="UnityEngine.InputSystem.InputSystemStateManager").ToArray();var rows=new Arr58();foreach(var manager in managers){using(var so=new SerializedObject(manager)){var prop=so.FindProperty("settings");if(prop==null||prop.propertyType!=SerializedPropertyType.String)throw new InvalidOperationException("Documented serialized settings field unavailable");string json=prop.stringValue;var row=new Obj58{["managerId"]=manager.GetEntityId().ToString(),["flags"]=manager.hideFlags.ToString(),["json"]=json,["exitEditTime"]=so.FindProperty("exitEditModeTime")?.doubleValue,["enterPlayTime"]=so.FindProperty("enterPlayModeTime")?.doubleValue};rows.Add(row);}}CreateOnly73.Text(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\eye-motion78\run\INPUT_DOMAIN_BACKUP78.json",new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["playing"]=EditorApplication.isPlaying,["rows"]=rows,["source"]="InputSystemEditorInitializer.OnPlayModeChange stores JsonUtility.ToJson on ExitingEditMode; EnteredEditMode clears only after FromJsonOverwrite"}.ToString());result.Log("78 serialized domain input backup read only; managers="+rows.Count);}
}
