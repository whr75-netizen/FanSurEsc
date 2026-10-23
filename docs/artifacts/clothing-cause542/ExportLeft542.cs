using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets")throw new Exception("Intended Edit project required");
  var asset=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/EUnityValidation01/OriginalIntegration399/Export/ValidatedPresentation399.prefab");var f=asset.GetComponentInChildren<Full319View335>(true);var r=f.motion.surface.source[0];var mesh=r.sharedMesh;var human=f.motion.animation.target.avatar.humanDescription.human;
  string path="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/BodyRay541/BODY_BONES542.bin";
  using(var w=new BinaryWriter(File.Create(path)))
  {
   w.Write(r.bones.Length);foreach(var bone in r.bones){w.Write(bone.name);w.Write(string.Join("|",human.Where(h=>h.boneName==bone.name).Select(h=>h.humanName)));}
   var v=mesh.vertices;var uv=mesh.uv;var b=mesh.boneWeights;w.Write(v.Length);for(int i=0;i<v.Length;i++){foreach(float n in new[]{v[i].x,v[i].y,v[i].z,uv[i].x,uv[i].y})w.Write(n);var a=b[i];w.Write(a.boneIndex0);w.Write(a.weight0);w.Write(a.boneIndex1);w.Write(a.weight1);w.Write(a.boneIndex2);w.Write(a.weight2);w.Write(a.boneIndex3);w.Write(a.weight3);}
   w.Write(mesh.subMeshCount);for(int sm=0;sm<mesh.subMeshCount;sm++){var ids=mesh.GetIndices(sm);w.Write(ids.Length);foreach(int i in ids)w.Write(i);}
  }
  File.WriteAllBytes("C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/BodyRay541/BODY_PARTS542.bin",f.bodyParts.bytes);
  result.Log("542 read-only body UV/bone/triangle export and existing semantic tags saved; left arm mapping uses Humanoid names, not screen side");
 }
}
