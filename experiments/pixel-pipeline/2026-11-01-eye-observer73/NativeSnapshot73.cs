using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
public static class NativeSnapshot73
{
 public static Arr58 Backup(string root)
 {
  var all=Resources.FindObjectsOfTypeAll<UnityEngine.Object>();var rows=new Arr58();bool player=false;int i=0;
  foreach(var o in all.Where(x=>x&&EditorUtility.IsPersistent(x)).OrderBy(x=>AssetDatabase.GetAssetPath(x)))
  {
   string path=AssetDatabase.GetAssetPath(o);if(!path.StartsWith("Assets/")&&!path.StartsWith("ProjectSettings/"))continue;
   if(!EditorUtility.IsDirty(o)&&!path.StartsWith("ProjectSettings/"))continue;
   bool dirty=EditorUtility.IsDirty(o);string name="native-before-"+(i++)+".json";string file=Path.Combine(root,name);if(File.Exists(file))throw new IOException("Snapshot already exists");
   string text=EditorJsonUtility.ToJson(o);CreateOnly73.Text(file,text);var c=SerializedContent66.Verify(file,text);if(c.Equivalent!=true)throw new IOException("Native backup failed: "+path);
   rows.Add(new Obj58{["path"]=path,["type"]=o.GetType().FullName,["entityId"]=o.GetEntityId().ToString(),["snapshot"]=name,["sha256"]=c.BeforeSHA256,["bytes"]=c.BeforeBytes,["dirtyBefore"]=dirty,["dirtyAfter"]=EditorUtility.IsDirty(o)});
   if(o is PlayerSettings)player=true;
  }
  if(!player)throw new InvalidOperationException("Full loaded PlayerSettings snapshot unavailable; no Play");
  CreateOnly73.Text(Path.Combine(root,"NATIVE_BEFORE73.json"),rows.ToString());return rows;
 }
 public static Arr58 Compare(string root,Arr58 rows)
 {
  var all=Resources.FindObjectsOfTypeAll<UnityEngine.Object>();var checks=new Arr58();
  foreach(Obj58 row in rows)
  {
   string path=(string)row["path"],type=(string)row["type"];var o=all.FirstOrDefault(x=>x&&AssetDatabase.GetAssetPath(x)==path&&x.GetType().FullName==type);
   if(!o){checks.Add(new Obj58{["path"]=path,["type"]=type,["status"]="Unavailable",["equal"]=null});continue;}
   var c=SerializedContent66.Verify(Path.Combine(root,(string)row["snapshot"]),EditorJsonUtility.ToJson(o));checks.Add(new Obj58{["path"]=path,["type"]=type,["status"]=c.Status,["equal"]=c.Equivalent.HasValue?(Json58)c.Equivalent.Value:null,["beforeSHA"]=c.BeforeSHA256,["afterSHA"]=c.AfterSHA256,["dirty"]=EditorUtility.IsDirty(o)});
  }
  return checks;
 }
}
