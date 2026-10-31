// Small hash-only state snapshots. One native serialization per dirty object.
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEngine.SceneManagement;
using UnityEngine.Profiling;

public static class State58
{
    public static string Hash(byte[] b) {using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(b)).Replace("-","").ToLowerInvariant();}
    public static Obj58 Memory() {return new Obj58 { ["utc"]=DateTime.UtcNow.ToString("O"),["GetTotalAllocatedMemoryLong"]=Profiler.GetTotalAllocatedMemoryLong(),["GetTotalReservedMemoryLong"]=Profiler.GetTotalReservedMemoryLong(),["GetMonoUsedSizeLong"]=Profiler.GetMonoUsedSizeLong()};}
    public static Obj58 Read() {
        var dirty=new Arr58();long serializedBytes=0;
        var objects=Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o))
            .Where(o=>AssetDatabase.GetAssetPath(o).StartsWith("Assets/")||AssetDatabase.GetAssetPath(o).StartsWith("ProjectSettings/"))
            .OrderBy(o=>AssetDatabase.GetAssetPath(o)).ThenBy(o=>o.GetEntityId().ToString());
        foreach(var o in objects) {
            string native=EditorJsonUtility.ToJson(o);byte[] bytes=System.Text.Encoding.UTF8.GetBytes(native);serializedBytes+=bytes.Length;
            dirty.Add(new Obj58 {["path"]=AssetDatabase.GetAssetPath(o),["guid"]=AssetDatabase.AssetPathToGUID(AssetDatabase.GetAssetPath(o)),
                ["entityId"]=o.GetEntityId().ToString(),["type"]=o.GetType().FullName,["sha256"]=Hash(bytes),["bytes"]=bytes.Length});
            // Neither full JSON nor byte copies enter the snapshot/return value.
        }
        var active=SceneManager.GetActiveScene();var scenes=new Arr58();
        foreach(var s in Enumerable.Range(0,SceneManager.sceneCount).Select(i=>SceneManager.GetSceneAt(i)))scenes.Add(new Obj58 {
            ["path"]=s.path,["dirty"]=s.isDirty,["loaded"]=s.isLoaded,["active"]=s==active,
            ["roots"]=new Arr58(s.isLoaded?s.GetRootGameObjects().Select(o=>o.GetEntityId().ToString()).OrderBy(v=>v):Enumerable.Empty<string>())});
        var files=new Arr58();
        foreach(var path in dirty.Select(r=>(string)r["path"]).Concat(scenes.Select(s=>(string)s["path"]))
            .SelectMany(p=>new[]{p,p+".meta"}).Distinct().OrderBy(p=>p).Where(File.Exists))files.Add(new Obj58 {["path"]=path,["sha256"]=Hash(File.ReadAllBytes(path))});
        var textures=new Arr58(Resources.FindObjectsOfTypeAll<Texture2D>().Select(t=>t.GetEntityId().ToString()).OrderBy(v=>v));
        var rts=new Arr58(Resources.FindObjectsOfTypeAll<RenderTexture>().Select(t=>t.GetEntityId().ToString()).OrderBy(v=>v));
        return new Obj58 {["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["version"]=Application.unityVersion,
            ["domain"]=AppDomain.CurrentDomain.Id,["playing"]=EditorApplication.isPlaying,["paused"]=EditorApplication.isPaused,
            ["transitioning"]=EditorApplication.isPlayingOrWillChangePlaymode,["compiling"]=EditorApplication.isCompiling,["updating"]=EditorApplication.isUpdating,
            ["dirty"]=dirty,["serializedBytes"]=serializedBytes,["files"]=files,["scenes"]=scenes,["texture2DIds"]=textures,["rtIds"]=rts,
            ["buildScenes"]=new Arr58(EditorBuildSettings.scenes.Select(s=>(s.enabled?"1":"0")+"\t"+s.path+"\t"+s.guid))};
    }
    public static string[] Changes(Obj58 a,Obj58 b) {return new[]{"project","version","domain","playing","paused","transitioning","compiling","updating","dirty","files","scenes","buildScenes"}.Where(k=>!Json58.DeepEquals(a[k],b[k])).ToArray();}
    public static void RequireEdit(Obj58 state) {
        if((bool)state["playing"]||(bool)state["transitioning"]||(bool)state["compiling"]||(bool)state["updating"])throw new InvalidOperationException("Stable Edit state required");
    }
}
