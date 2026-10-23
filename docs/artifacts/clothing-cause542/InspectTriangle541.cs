using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets"||EditorApplication.isPlaying)throw new Exception("Current Edit project required");
  var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/EUnityValidation01/OriginalIntegration399/Export/ValidatedPresentation399.prefab");
  foreach(var r in prefab.GetComponentsInChildren<SkinnedMeshRenderer>(true))
  {
   result.Log("renderer "+r.name+" mesh="+r.sharedMesh.name+" vertices="+r.sharedMesh.vertexCount+" submeshes="+r.sharedMesh.subMeshCount);
   if(r.name!="Body")continue;var m=r.sharedMesh;var ids=m.GetIndices(0);var v=m.vertices;var uv=m.uv;var bw=m.boneWeights;int pr=9626;
   for(int i=0;i<3;i++){int at=ids[pr*3+i];var b=bw[at];result.Log("primitive="+pr+" vertex="+at+" local="+v[at].ToString("R")+" uv="+uv[at].ToString("R")+" bone0="+r.bones[b.boneIndex0].name+":"+b.weight0+" bone1="+r.bones[b.boneIndex1].name+":"+b.weight1+" bone2="+r.bones[b.boneIndex2].name+":"+b.weight2+" bone3="+r.bones[b.boneIndex3].name+":"+b.weight3);}
  }
 }
}
