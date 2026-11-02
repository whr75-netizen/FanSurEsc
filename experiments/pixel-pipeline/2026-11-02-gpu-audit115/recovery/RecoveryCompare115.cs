using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
// Public reads only. Never applies old snapshots/global bindings to the new session.
internal class CommandScript:IRunCommand {
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\gpu-form115";
 const string Out=Root+@"\recovery-read";
 static string[] Bits(IEnumerable<float> values){return values.Select(v=>BitConverter.ToUInt32(BitConverter.GetBytes(v),0).ToString("x8")).ToArray();}
 static float[] Vector(BinaryReader r){return Enumerable.Range(0,4).Select(_=>r.ReadSingle()).ToArray();}
 static float[] Matrix(BinaryReader r){return Enumerable.Range(0,16).Select(_=>r.ReadSingle()).ToArray();}
 static IEnumerable<float> V(Vector4 v){for(int i=0;i<4;i++)yield return v[i];}
 static IEnumerable<float> M(Matrix4x4 m){for(int c=0;c<4;c++)for(int r=0;r<4;r++)yield return m[r,c];}
 static int Count(BinaryReader r){int n=r.ReadInt32();if(n<0||n>4096)throw new IOException("Global array outside frozen backup bound");return n;}
 static Arr58 ReadGlobals(){
  var rows=new Arr58();
  using(var r=new BinaryReader(File.OpenRead(Root+@"\eye115-20261102T023401691Z-4f7e54be\GLOBALS_BEFORE.bin"))){
   if(r.ReadInt32()!=0x34364a47||r.ReadInt32()!=1)throw new IOException("Global backup header");
   if(r.ReadString()!="eye115-20261102T023401691Z-4f7e54be")throw new IOException("Global backup source identity");
   int total=Count(r);if(total!=74)throw new IOException("Expected frozen74 globals");
   for(int index=0;index<total;index++){
    string name=r.ReadString();int kind=r.ReadInt32();bool restorable=r.ReadBoolean();string reason=r.ReadString();float scalar=r.ReadSingle();int integer=r.ReadInt32();var vector=Vector(r);var matrix=Matrix(r);string textureKind=r.ReadString(),guid=r.ReadString();long local=r.ReadInt64();
    var floats=Enumerable.Range(0,Count(r)).Select(_=>r.ReadSingle()).ToArray();var vectors=Enumerable.Range(0,Count(r)).SelectMany(_=>Vector(r)).ToArray();var matrices=Enumerable.Range(0,Count(r)).SelectMany(_=>Matrix(r)).ToArray();
    string[] before=null,after=null;string oldIdentity=null,newIdentity=null;bool? equal=null;
    switch(kind){
     case 0:before=Bits(new[]{scalar});after=Bits(new[]{Shader.GetGlobalFloat(name)});break;
     case 1:before=Bits(new[]{scalar}).Concat(new[]{integer.ToString()}).ToArray();after=Bits(new[]{Shader.GetGlobalFloat(name)}).Concat(new[]{Shader.GetGlobalInt(name).ToString()}).ToArray();break;
     case 2:oldIdentity=integer.ToString();newIdentity=Shader.GetGlobalInteger(name).ToString();break;
     case 3:before=Bits(vector);after=Bits(V(Shader.GetGlobalVector(name)));break;
     case 4:before=Bits(matrix);after=Bits(M(Shader.GetGlobalMatrix(name)));break;
     case 5:
      oldIdentity=textureKind+"|"+guid+"|"+local;
      var texture=Shader.GetGlobalTexture(name);string currentKind,currentGUID="";long currentLocal=0;
      if(!texture)currentKind="null";else if(texture==Texture2D.blackTexture)currentKind="builtin-black";else if(texture==Texture2D.whiteTexture)currentKind="builtin-white";else if(texture==Texture2D.grayTexture)currentKind="builtin-gray";else currentKind=EditorUtility.IsPersistent(texture)&&AssetDatabase.TryGetGUIDAndLocalFileIdentifier(texture,out currentGUID,out currentLocal)?"persistent-asset":"runtime-unrecoverable";
      newIdentity=currentKind+"|"+currentGUID+"|"+currentLocal;break;
     case 6:before=Bits(floats);after=Bits(Shader.GetGlobalFloatArray(name)??new float[0]);break;
     case 7:before=Bits(vectors);after=Bits((Shader.GetGlobalVectorArray(name)??new Vector4[0]).SelectMany(V));break;
     case 8:before=Bits(matrices);after=Bits((Shader.GetGlobalMatrixArray(name)??new Matrix4x4[0]).SelectMany(M));break;
     case 9:case 10:reason="No public binding getter; no read/restore attempted";break;
     default:throw new IOException("Unknown frozen global kind");
    }
    if(before!=null)equal=before.SequenceEqual(after);else if(oldIdentity!=null)equal=oldIdentity==newIdentity;
    rows.Add(new Obj58{["name"]=name,["kind"]=kind,["beforeRestorable"]=restorable,["equalPublicValues"]=equal.HasValue?(Json58)equal.Value:null,["beforeBits"]=before==null?null:new Arr58(before),["currentBits"]=after==null?null:new Arr58(after),["beforeIdentity"]=oldIdentity,["currentIdentity"]=newIdentity,["reason"]=reason});
   }
   if(r.BaseStream.Position!=r.BaseStream.Length)throw new IOException("Global backup trailing bytes");
  }
  return rows;
 }
 public void Execute(ExecutionResult result){
  var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["readComplete"]=false,["writesToUnityObjects"]=0,["restorationAttempted"]=false};
  try{
   if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required for read-only comparison");
   var all=Resources.FindObjectsOfTypeAll<UnityEngine.Object>();
   var indexed=new Dictionary<string,List<UnityEngine.Object>>();
   foreach(var o in all){if(!o||!EditorUtility.IsPersistent(o))continue;string path=AssetDatabase.GetAssetPath(o);if(!path.StartsWith("Assets/")&&!path.StartsWith("ProjectSettings/"))continue;string key=path+"|"+o.GetType().FullName;if(!indexed.TryGetValue(key,out var list)){list=new List<UnityEngine.Object>();indexed.Add(key,list);}list.Add(o);}
   var checks=new Arr58();var old=Json58.Parse(File.ReadAllText(Root+@"\NATIVE_BEFORE73.json"));int index=0;
   foreach(Obj58 row in old){
    string path=(string)row["path"],type=(string)row["type"];var item=new Obj58{["path"]=path,["type"]=type,["beforeDirty"]=row["dirtyBefore"],["beforeEntityId"]=row["entityId"],["beforeSnapshot"]=row["snapshot"]};checks.Add(item);
    if(!indexed.TryGetValue(path+"|"+type,out var matches)||matches.Count!=1){item["status"]=matches==null?"Unavailable":"AmbiguousLoadedObjects";item["loadedMatches"]=matches==null?0:matches.Count;item["equal"]=null;index++;continue;}
    var o=matches[0];bool dirty=EditorUtility.IsDirty(o);string text=EditorJsonUtility.ToJson(o);var c=SerializedContent66.Verify(Path.Combine(Root,(string)row["snapshot"]),text);
    item["status"]=c.Status;item["equal"]=c.Equivalent.HasValue?(Json58)c.Equivalent.Value:null;item["beforeSHA256"]=c.BeforeSHA256;item["currentSHA256"]=c.AfterSHA256;item["beforeBytes"]=c.BeforeBytes;item["currentBytes"]=c.AfterBytes;item["currentEntityId"]=o.GetEntityId().ToString();item["dirtyBeforeRead"]=dirty;item["dirtyAfterRead"]=EditorUtility.IsDirty(o);
    if(c.BeforeSHA256!=c.AfterSHA256){string file="native-current-"+index+".json";CreateOnly73.Text(Path.Combine(Out,file),text);item["currentSnapshot"]=file;}
    if(o is UnityEngine.Mesh mesh){item["vertexCount"]=mesh.vertexCount;item["subMeshCount"]=mesh.subMeshCount;item["blendShapeCount"]=mesh.blendShapeCount;}
    index++;
   }
   report["nativeComparisons"]=checks;report["globals"]=ReadGlobals();report["readComplete"]=true;
   report["endPlaying"]=EditorApplication.isPlaying;report["endCompiling"]=EditorApplication.isCompiling;report["endUpdating"]=EditorApplication.isUpdating;
  }catch(Exception e){report["error"]=e.ToString();}
  CreateOnly73.Text(Path.Combine(Out,"NATIVE_GLOBALS_RECOVERY115.json"),report.ToString());
  result.Log("115 recovery public native/global comparison complete="+(bool)report["readComplete"]+"; no restoration or Unity object writes");
 }
}
