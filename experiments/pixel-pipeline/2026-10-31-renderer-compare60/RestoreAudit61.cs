using System;
using System.IO;
using System.Linq;
using Unity.Collections;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

internal class CommandScript:IRunCommand {
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\renderer-compare60";
 static Arr58 V(Vector4 v){return new Arr58(new[]{v.x,v.y,v.z,v.w});}
 public void Execute(ExecutionResult result){
  if(EditorApplication.isPlaying||EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit only; no restoration writes");
  var r=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["domain"]=AppDomain.CurrentDomain.Id,["playing"]=EditorApplication.isPlaying,["paused"]=EditorApplication.isPaused,["settersExecuted"]=0,["globalOriginalValuesAvailable"]=false,["globalBufferBindingsChanged"]=false,["memoryBefore"]=State58.Memory()};
  var globals=new Arr58();
  foreach(var g in Json58.Parse(File.ReadAllText(Path.Combine(Root,"GLOBAL_NAMES60.json")))){
   string name=(string)g["name"],type=(string)g["type"];var row=new Obj58{["name"]=name,["type"]=type};
   switch(type){case "Float":row["current"]=Shader.GetGlobalFloat(name);break;case "Int":row["current"]=Shader.GetGlobalInt(name);break;case "Vector":row["current"]=V(Shader.GetGlobalVector(name));break;case "Matrix":var m=Shader.GetGlobalMatrix(name);row["current"]=new Arr58(Enumerable.Range(0,16).Select(i=>m[i/4,i%4]));break;case "Texture":var t=Shader.GetGlobalTexture(name);row["current"]=t?new Obj58{["entityId"]=t.GetEntityId().ToString(),["name"]=t.name,["asset"]=AssetDatabase.GetAssetPath(t),["width"]=t.width,["height"]=t.height}:null;break;}
   globals.Add(row);
  }
  r["currentGlobals"]=globals;
  var all=Resources.FindObjectsOfTypeAll<UnityEngine.Object>();var dirty=new Arr58();var settings=new Obj58();
  var wanted=new[]{"ProjectSettings/EditorSettings.asset","ProjectSettings/GraphicsSettings.asset","ProjectSettings/TimeManager.asset"};
  foreach(var o in all.Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).OrderBy(o=>AssetDatabase.GetAssetPath(o)).ThenBy(o=>o.GetEntityId().ToString())){
   string p=AssetDatabase.GetAssetPath(o);if(!p.StartsWith("Assets/")&&!p.StartsWith("ProjectSettings/"))continue;
   dirty.Add(new Obj58{["path"]=p,["entityId"]=o.GetEntityId().ToString(),["type"]=o.GetType().FullName});
   if(wanted.Contains(p)){string text=EditorJsonUtility.ToJson(o);settings[p]=new Obj58{["bytes"]=System.Text.Encoding.UTF8.GetByteCount(text),["sha256"]=State58.Hash(System.Text.Encoding.UTF8.GetBytes(text)),["native"]=text.Length<65536?Json58.Parse(text):null};}
  }
  r["dirty"]=dirty;r["smallSettings"]=settings;r["fullShaderNativeJsonGenerated"]=false;
  r["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled;r["options"]=(int)EditorSettings.enterPlayModeOptions;r["timeScale"]=Time.timeScale;r["captureDeltaTime"]=Time.captureDeltaTime;r["graphicsPipelinePath"]=AssetDatabase.GetAssetPath(GraphicsSettings.defaultRenderPipeline);r["qualityPipelinePath"]=AssetDatabase.GetAssetPath(QualitySettings.renderPipeline);
  var scenes=new Arr58();foreach(var s in Enumerable.Range(0,SceneManager.sceneCount).Select(SceneManager.GetSceneAt))scenes.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["roots"]=new Arr58(s.GetRootGameObjects().Select(o=>o.GetEntityId().ToString()).OrderBy(v=>v)),["active"]=s==SceneManager.GetActiveScene()});r["scenes"]=scenes;
  r["liveNativeCount"]=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsInactive.Include,FindObjectsSortMode.None).Length;
  var mat=Resources.FindObjectsOfTypeAll<Material>().Where(m=>m&&m.shader&&m.shader.name.StartsWith("Hidden/Renderer60/")).ToArray();r["liveCandidateMaterials"]=new Arr58(mat.Select(m=>new Obj58{["entityId"]=m.GetEntityId().ToString(),["name"]=m.name,["shader"]=m.shader.name,["asset"]=AssetDatabase.GetAssetPath(m),["flags"]=m.hideFlags.ToString()}));
  r["liveCandidateComputeClones"]=new Arr58(Resources.FindObjectsOfTypeAll<ComputeShader>().Where(c=>c&&c.name.StartsWith("RestoreStyle60")&&!EditorUtility.IsPersistent(c)).Select(c=>new Obj58{["entityId"]=c.GetEntityId().ToString(),["name"]=c.name,["flags"]=c.hideFlags.ToString()}));
  r["renderTextures"]=new Arr58(Resources.FindObjectsOfTypeAll<RenderTexture>().Select(t=>new Obj58{["id"]=t.GetEntityId().ToString(),["name"]=t.name,["width"]=t.width,["height"]=t.height,["asset"]=AssetDatabase.GetAssetPath(t)}));
  r["publicProductCaches"]=new Obj58{["ContourSelect333.TagBytesLength"]=ContourSelect333.TagBytes==null?0:ContourSelect333.TagBytes.Length,["ClothRegion524.SourceCount"]=ClothRegion524.Source.Count,["ClothRegion524.CurvesCount"]=ClothRegion524.Curves.Count,["ClothRegion524.AreasLength"]=ClothRegion524.Areas==null?0:ClothRegion524.Areas.Length,["ClothRegion524.SelectedLength"]=ClothRegion524.Selected==null?0:ClothRegion524.Selected.Length,["ClothRegion524.AtlasLive"]=ClothRegion524.Atlas540!=null,["ClothRegion524.AuditLive"]=ClothRegion524.Audit!=null,["ClothSurface525.PacketsCount"]=ClothSurface525.Packets.Count,["HeadRegion502.SourceLoopsCount"]=HeadRegion502.SourceLoops.Count,["HeadRegion502.CurvesCount"]=HeadRegion502.Curves.Count,["HeadRegion502.PacketsCount"]=HeadRegion502.Packets.Count,["HeadRegion502.MaskLive"]=HeadRegion502.Mask!=null,["HeadRegion502.HairLength"]=HeadRegion502.Hair.Length,["HeadRegion502.ParentLength"]=HeadRegion502.Parent.Length};
  var mesh=AssetDatabase.LoadAssetAtPath<UnityEngine.Mesh>("Assets/EUnityValidation01/EyeContoursLayers202/Meshes/FaceSourceOwner202.asset");
  if(mesh){var view=new Obj58{["entityId"]=mesh.GetEntityId().ToString(),["vertexCount"]=mesh.vertexCount,["subMeshCount"]=mesh.subMeshCount,["blendShapeCount"]=mesh.blendShapeCount,["isReadable"]=mesh.isReadable};
   using(var data=UnityEngine.Mesh.AcquireReadOnlyMeshData(mesh)){var m=data[0];using(var bytes=new MemoryStream()){for(int i=0;i<m.vertexBufferCount;i++){byte[] b=m.GetVertexData<byte>(i).ToArray();bytes.Write(b,0,b.Length);}view["vertexBytes"]=bytes.Length;view["vertexSHA256"]=State58.Hash(bytes.ToArray());}var ix=m.GetIndexData<byte>().ToArray();view["indexBytes"]=ix.Length;view["indexSHA256"]=State58.Hash(ix);}
   using(var stream=new MemoryStream()){using(var writer=new BinaryWriter(stream)){foreach(var m in mesh.bindposes)for(int i=0;i<16;i++)writer.Write(m[i/4,i%4]);}view["bindposesSHA256"]=State58.Hash(stream.ToArray());}
   view["blendShapes"]=new Arr58(Enumerable.Range(0,mesh.blendShapeCount).Select(i=>new Obj58{["name"]=mesh.GetBlendShapeName(i),["frameCount"]=mesh.GetBlendShapeFrameCount(i),["weights"]=new Arr58(Enumerable.Range(0,mesh.GetBlendShapeFrameCount(i)).Select(j=>mesh.GetBlendShapeFrameWeight(i,j)))}));r["faceMesh"]=view;
  }
  r["memoryAfter"]=State58.Memory();File.WriteAllText(Path.Combine(Root,"RESTORE_READ61.json"),r.ToString());result.Log("61 read-only; Edit; dirty="+dirty.Count+" globalsRead="+globals.Count+" ownedCandidateMaterials="+mat.Length+" no setters/Play/GC");
 }
}
