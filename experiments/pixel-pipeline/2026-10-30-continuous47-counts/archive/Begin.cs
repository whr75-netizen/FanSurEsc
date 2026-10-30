using System;using System.IO;using System.Linq;using UnityEngine;using UnityEditor;using UnityEngine.SceneManagement;
internal class CommandScript:IRunCommand{
 const string R="C:/Users/15352/Documents/Codex/2026-10-27/task-2/render-fix21/continuous47-counts/";
 [Serializable]class Header{public string utc,scenePath,sceneName;public bool sceneDirty;public string[]rootIDs,dirtyAssets;public float timeScale,captureDelta;public bool background;}
 [Serializable]class Row{public string gid,type,name,hierarchy,json;public bool dirty;}
 static string ID(UnityEngine.Object o)=>o?GlobalObjectId.GetGlobalObjectIdSlow(o).ToString():"null";
 static string PathOf(Transform t){string p=t.name;while(t.parent){t=t.parent;p=t.name+"/"+p;}return p;}
 public void Execute(ExecutionResult r){var s=SceneManager.GetActiveScene();if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||s.path!="Assets/Scenes/GameMap1.unity"||SceneManager.sceneCount!=1)throw new Exception("Existing stable GameMap1 Edit required; state preserved");if(File.Exists(R+"SCENE_BEFORE.ndjson"))throw new Exception("Baseline exists; inspect outcome before repeating");
 var h=new Header{utc=DateTime.UtcNow.ToString("O"),scenePath=s.path,sceneName=s.name,sceneDirty=s.isDirty,rootIDs=s.GetRootGameObjects().Select(ID).ToArray(),timeScale=Time.timeScale,captureDelta=Time.captureDeltaTime,background=Application.runInBackground,dirtyAssets=Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Select(AssetDatabase.GetAssetPath).Where(p=>!string.IsNullOrEmpty(p)&&(p.StartsWith("Assets/")||p.StartsWith("ProjectSettings/"))).Distinct().OrderBy(p=>p).ToArray()};
 using(var f=new StreamWriter(R+"SCENE_BEFORE.ndjson")){f.WriteLine(JsonUtility.ToJson(h));foreach(var t in s.GetRootGameObjects().SelectMany(g=>g.GetComponentsInChildren<Transform>(true)))foreach(var o in new UnityEngine.Object[]{t.gameObject}.Concat(t.GetComponents<Component>().Cast<UnityEngine.Object>()))if(o)f.WriteLine(JsonUtility.ToJson(new Row{gid=ID(o),type=o.GetType().FullName,name=o.name,hierarchy=PathOf(t),json=EditorJsonUtility.ToJson(o),dirty=EditorUtility.IsDirty(o)}));}
 r.Log("Baseline scene="+s.path+" dirty="+h.sceneDirty+" persistentDirty="+h.dirtyAssets.Length+" roots="+h.rootIDs.Length+"; owned limited Play requested, no save/reload.");EditorApplication.isPlaying=true;EditorApplication.isPaused=true;
 }
}

