using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using System;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();
  if(EditorApplication.isPlaying||EditorApplication.isPaused||EditorApplication.isCompiling||EditorSceneManager.GetActiveScene().isDirty||ClothRegion524.Enabled||ClothRegion524.UseSpans543||ClothRegion524.UseCompact544||ClothRegion524.UseSimplifiedSpanReference546||HeadRegion502.Enabled||Time.captureDeltaTime!=0||Application.runInBackground)throw new Exception("547 final restored-state assertion failed");
  result.Log("547 direct restore confirmed: Edit/unpaused/compiled/scene clean; cloth/spans/compact/legacy-reference/head OFF; captureDelta0; backgroundfalse; active gameplay="+(g?g.connected.ToString():"none")+". No new operation requested.");
 }
}
