using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEngine.SceneManagement;

internal class CommandScript : IRunCommand
{
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66";
 static string Hash(string p){using(var h=SHA256.Create())using(var f=File.OpenRead(p))return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}
 static void Bytes(BinaryWriter w,Unity.Collections.NativeArray<byte> src){var tmp=new byte[65536];w.Write(src.Length);for(int i=0;i<src.Length;i+=tmp.Length){int n=Math.Min(tmp.Length,src.Length-i);Unity.Collections.NativeArray<byte>.Copy(src,i,tmp,0,n);w.Write(tmp,0,n);}}
 static void V(BinaryWriter w,Vector3 v){w.Write(v.x);w.Write(v.y);w.Write(v.z);}
 static void MeshBackup(UnityEngine.Mesh mesh,string path)
 {
  using(var fs=File.Create(path))using(var w=new BinaryWriter(fs))
  {
   w.Write("mesh-readable66/v1");w.Write(mesh.vertexCount);w.Write((int)mesh.indexFormat);
   V(w,mesh.bounds.center);V(w,mesh.bounds.size);
   var attributes=mesh.GetVertexAttributes();w.Write(attributes.Length);
   foreach(var a in attributes){w.Write((int)a.attribute);w.Write((int)a.format);w.Write(a.dimension);w.Write(a.stream);}
   using(var all=UnityEngine.Mesh.AcquireReadOnlyMeshData(mesh))
   {
    var d=all[0];w.Write(d.vertexBufferCount);
    for(int i=0;i<d.vertexBufferCount;i++){w.Write(d.GetVertexBufferStride(i));Bytes(w,d.GetVertexData<byte>(i));}
    Bytes(w,d.GetIndexData<byte>());
   }
   w.Write(mesh.subMeshCount);
   for(int i=0;i<mesh.subMeshCount;i++){var d=mesh.GetSubMesh(i);w.Write(d.indexStart);w.Write(d.indexCount);w.Write((int)d.topology);w.Write(d.baseVertex);w.Write(d.firstVertex);w.Write(d.vertexCount);V(w,d.bounds.center);V(w,d.bounds.size);}
   var bind=mesh.bindposes;w.Write(bind.Length);foreach(var m in bind)for(int row=0;row<4;row++)for(int col=0;col<4;col++)w.Write(m[row,col]);
   // Full native serialized JSON is a second backup, including skinning fields.
   // This binary explicitly preserves the public readable mesh + morph deltas.
   var dv=new Vector3[mesh.vertexCount];var dn=new Vector3[mesh.vertexCount];var dt=new Vector3[mesh.vertexCount];
   w.Write(mesh.blendShapeCount);
   for(int i=0;i<mesh.blendShapeCount;i++)
   {
    w.Write(mesh.GetBlendShapeName(i));int count=mesh.GetBlendShapeFrameCount(i);w.Write(count);
    for(int j=0;j<count;j++){w.Write(mesh.GetBlendShapeFrameWeight(i,j));mesh.GetBlendShapeFrameVertices(i,j,dv,dn,dt);foreach(var a in new[]{dv,dn,dt})foreach(var v in a)V(w,v);}
   }
  }
 }
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isPlaying||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
  var plan=(Obj58)Json58.Parse(File.ReadAllText(Path.Combine(Root,"BACKUP_PLAN66.json")));
  var expected=(Arr58)plan["dirty"];
  var objects=Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o))
   .Where(o=>{string p=AssetDatabase.GetAssetPath(o);return p.StartsWith("Assets/")||p.StartsWith("ProjectSettings/");}).ToArray();
  if(objects.Length!=expected.Count)throw new InvalidOperationException("Dirty set changed");
  foreach(Obj58 e in expected)if(!objects.Any(o=>AssetDatabase.GetAssetPath(o)==(string)e["path"]&&o.GetEntityId().ToString()==(string)e["entityId"]))throw new InvalidOperationException("Dirty identity changed");
  string backup=Path.Combine(Root,"backup");if(Directory.Exists(backup))throw new InvalidOperationException("Backup already exists; inspect instead of repeating");Directory.CreateDirectory(backup);
  string project=Directory.GetParent(Application.dataPath).FullName+Path.DirectorySeparatorChar;
  var disk=new Arr58();
  foreach(Obj58 e in (Arr58)plan["files"])
  {
   string rel=(string)e["path"],source=Path.GetFullPath(Path.Combine(project,rel));
   if(!source.StartsWith(project,StringComparison.OrdinalIgnoreCase))throw new InvalidOperationException("Out of project backup path");
   if(Hash(source)!=(string)e["sha256"])throw new InvalidOperationException("Disk changed: "+rel);
   string target=Path.Combine(backup,"disk",rel);Directory.CreateDirectory(Path.GetDirectoryName(target));File.Copy(source,target,false);
   if(Hash(target)!=(string)e["sha256"])throw new InvalidOperationException("Backup hash mismatch");disk.Add(new Obj58{["path"]=rel,["sha256"]=Hash(target),["bytes"]=new FileInfo(target).Length});
  }
  var native=new Arr58();
  foreach(var o in objects)
  {
   string rel=AssetDatabase.GetAssetPath(o);var e=new Obj58{["path"]=rel,["type"]=o.GetType().FullName,["entityId"]=o.GetEntityId().ToString()};
   if(o is Shader){e["nativeSnapshot"]=false;e["limit"]="Shader imported native/compiled cache not serialized; exact source/meta copied. No GPU binding/cache restoration claim.";}
   else
   {
    string target=Path.Combine(backup,"serialized",rel+".json");Directory.CreateDirectory(Path.GetDirectoryName(target));
    string json=EditorJsonUtility.ToJson(o);File.WriteAllText(target,json);
    using(var h=SHA256.Create()){string expectedHash=BitConverter.ToString(h.ComputeHash(System.Text.Encoding.UTF8.GetBytes(json))).Replace("-","").ToLowerInvariant();if(Hash(target)!=expectedHash)throw new InvalidOperationException("Native backup mismatch");}
    e["nativeSnapshot"]=true;e["jsonSHA256"]=Hash(target);e["jsonBytes"]=new FileInfo(target).Length;
    if(o is UnityEngine.Mesh mesh){string binary=Path.Combine(backup,"mesh-readable66.bin");MeshBackup(mesh,binary);e["publicMeshSHA256"]=Hash(binary);e["publicMeshBytes"]=new FileInfo(binary).Length;e["vertices"]=mesh.vertexCount;e["morphs"]=mesh.blendShapeCount;}
   }
   native.Add(e);
  }
  var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["disk"]=disk,["native"]=native,["saved"]=false,["sceneSaved"]=false,["limits"]="GPU buffers/RT contents, compiled shader caches, nonserialized static state and unknown global buffer bindings are not recoverable by these asset snapshots."};
  File.WriteAllText(Path.Combine(Root,"BACKUP66.json"),report.ToString());
  result.Log("66 backup verified: disk="+disk.Count+" dirty="+native.Count+" no save/import/Play");
 }
}
