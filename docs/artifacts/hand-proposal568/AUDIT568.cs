using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text;
using System.Globalization;
using UnityEditor;
using UnityEngine;
public static class AssetAudit568
{
 [Serializable]public class Binding{public string human,bone,path,method;public bool available;}
 [Serializable]public class Weight{public string region;public double weight;}
 [Serializable]public class Witness{public int primitive;public List<Weight> membership=new();}
 [Serializable]public class Audit{public string prefab,mesh,meshName,meshEntityId;public bool humanoid;public int vertices,bodyTriangles,bodyVertices,bones;public List<Binding>bindings=new();public int singleFingerVertices,mixedFingerVertices,fingerPalmBlendVertices,wristBlendVertices,handLegBlendVertices,mixedFingerTriangles,wristBlendTriangles;public List<Witness>witnesses=new();}
 [Serializable]public class Batch{public List<Audit> sources=new();}
 static readonly HumanBodyBones[] fingers={HumanBodyBones.LeftThumbProximal,HumanBodyBones.LeftIndexProximal,HumanBodyBones.LeftMiddleProximal,HumanBodyBones.LeftRingProximal,HumanBodyBones.LeftLittleProximal,HumanBodyBones.RightThumbProximal,HumanBodyBones.RightIndexProximal,HumanBodyBones.RightMiddleProximal,HumanBodyBones.RightRingProximal,HumanBodyBones.RightLittleProximal};
 static string PathOf(Transform t,Transform root){var p=new List<string>();while(t&&t!=root){p.Add(t.name);t=t.parent;}p.Reverse();return string.Join("/",p);}
 public static void Run()
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("568 read-only cleanEdit required");
  const string output="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HandProposal568/ASSET_PROOFS568.txt";if(File.Exists(output))throw new Exception("Existing audit; inspect before repeating");
  var targets=Resources.FindObjectsOfTypeAll<Source329WalkView>().Where(v=>v.target&&v.target.avatar&&v.target.isHuman).Select(v=>v.target).Distinct().Where(a=>a.GetComponentsInChildren<SkinnedMeshRenderer>(true).Any(s=>s.sharedMesh&&s.sharedMesh.subMeshCount>0&&s.sharedMesh.GetIndexCount(0)/3==10022)).ToArray();
  if(targets.Length==0){Directory.CreateDirectory(System.IO.Path.GetDirectoryName(output));File.WriteAllText(output,"{\"sourceAvailable\":false,\"candidateCount\":0}");return;}
  var batch=new Batch();foreach(var animator in targets){var root=animator.gameObject;
  var renderers=root.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(s=>s.sharedMesh&&s.sharedMesh.subMeshCount>0&&s.sharedMesh.GetIndexCount(0)/3==10022).ToArray();if(renderers.Length!=1)throw new Exception("Stored Body0 witness mesh not unique");var skin=renderers[0];var mesh=skin.sharedMesh;var ix=mesh.GetIndices(0);var weights=mesh.boneWeights;if(weights.Length!=mesh.vertexCount)throw new Exception("Source skin weights unavailable");
  var audit=new Audit{prefab=string.IsNullOrEmpty(AssetDatabase.GetAssetPath(root))?root.scene.path+"#"+root.name:AssetDatabase.GetAssetPath(root),mesh=AssetDatabase.GetAssetPath(mesh),meshName=mesh.name,meshEntityId=mesh.GetEntityId().ToString(),humanoid=animator.isHuman,vertices=mesh.vertexCount,bodyTriangles=ix.Length/3,bones=skin.bones.Length};
  Transform Bind(HumanBodyBones h){Transform t=null;string method="GetBoneTransform";try{t=animator.GetBoneTransform(h);}catch{}if(!t){string canonical=HumanTrait.BoneName[(int)h];var desc=animator.avatar.humanDescription.human.Where(z=>z.humanName==canonical).ToArray();if(desc.Length==1){var matches=root.GetComponentsInChildren<Transform>(true).Where(z=>z.name==desc[0].boneName).ToArray();if(matches.Length==1){t=matches[0];method="unique declared Avatar humanDescription binding";}}}audit.bindings.Add(new Binding{human=h.ToString(),bone=t?t.name:"",path=t?PathOf(t,root.transform):"",method=method,available=t});return t;}
  var roots=fingers.Select(Bind).ToArray();var hands=new[]{Bind(HumanBodyBones.LeftHand),Bind(HumanBodyBones.RightHand)};var arms=new[]{Bind(HumanBodyBones.LeftLowerArm),Bind(HumanBodyBones.RightLowerArm)};var legs=new[]{Bind(HumanBodyBones.LeftUpperLeg),Bind(HumanBodyBones.RightUpperLeg)};
  foreach(HumanBodyBones h in Enum.GetValues(typeof(HumanBodyBones)))if(h.ToString().Contains("Intermediate")||h.ToString().Contains("Distal"))Bind(h);
  if(roots.Any(t=>!t)||hands.Any(t=>!t)||arms.Any(t=>!t)||legs.Any(t=>!t))throw new Exception("Required declared roots unavailable; no guessed bone names");
  var labels=new string[16];for(int i=0;i<10;i++)labels[i]=fingers[i].ToString();labels[10]="LeftPalm";labels[11]="RightPalm";labels[12]="LeftForearm";labels[13]="RightForearm";labels[14]="LeftLeg";labels[15]="RightLeg";
  int Region(int bone){if(bone<0||bone>=skin.bones.Length||!skin.bones[bone])return-1;var t=skin.bones[bone];for(int i=0;i<10;i++)if(t==roots[i]||t.IsChildOf(roots[i]))return i;for(int i=0;i<2;i++)if(t==hands[i]||t.IsChildOf(hands[i]))return 10+i;for(int i=0;i<2;i++)if(t==arms[i]||t.IsChildOf(arms[i]))return 12+i;for(int i=0;i<2;i++)if(t==legs[i]||t.IsChildOf(legs[i]))return 14+i;return-1;}
  var values=new Dictionary<int,double[]>();foreach(int v in ix.Distinct()){var w=weights[v];var a=new double[16];void Add(int b,float z){int k=Region(b);if(z>0&&k>=0)a[k]+=z;}Add(w.boneIndex0,w.weight0);Add(w.boneIndex1,w.weight1);Add(w.boneIndex2,w.weight2);Add(w.boneIndex3,w.weight3);values.Add(v,a);int n=a.Take(10).Count(z=>z>0);bool finger=n>0,palm=a[10]+a[11]>0,arm=a[12]+a[13]>0,leg=a[14]+a[15]>0;if(n==1)audit.singleFingerVertices++;if(n>1)audit.mixedFingerVertices++;if(finger&&(palm||arm))audit.fingerPalmBlendVertices++;if((finger||palm)&&arm)audit.wristBlendVertices++;if((finger||palm)&&leg)audit.handLegBlendVertices++;}audit.bodyVertices=values.Count;
  for(int pr=0;pr<ix.Length/3;pr++){var a=new double[16];for(int j=0;j<3;j++){var v=values[ix[3*pr+j]];for(int k=0;k<16;k++)a[k]+=v[k]/3;}if(a.Take(10).Count(z=>z>0)>1)audit.mixedFingerTriangles++;if(a.Take(12).Sum()>0&&a[12]+a[13]>0)audit.wristBlendTriangles++;if(new[]{7823,7920,8549,7122}.Contains(pr)){var w=new Witness{primitive=pr};for(int k=0;k<16;k++)if(a[k]>0)w.membership.Add(new Weight{region=labels[k],weight=a[k]});audit.witnesses.Add(w);}}
  batch.sources.Add(audit);}
  var text=new StringBuilder();text.AppendLine("sourceCount="+batch.sources.Count);
  foreach(var a in batch.sources){text.AppendLine("SOURCE\t"+a.prefab+"\t"+a.mesh+"\t"+a.meshName+"\t"+a.meshEntityId);text.AppendLine("COUNTS\t"+string.Join("\t",new[]{a.vertices,a.bodyTriangles,a.bodyVertices,a.bones,a.singleFingerVertices,a.mixedFingerVertices,a.fingerPalmBlendVertices,a.wristBlendVertices,a.handLegBlendVertices,a.mixedFingerTriangles,a.wristBlendTriangles}));foreach(var b in a.bindings)text.AppendLine("BIND\t"+b.human+"\t"+b.available+"\t"+b.bone+"\t"+b.path+"\t"+b.method);foreach(var v in a.witnesses){text.Append("TRI\t"+v.primitive);foreach(var m in v.membership)text.Append("\t"+m.region+"="+m.weight.ToString("R",CultureInfo.InvariantCulture));text.AppendLine();}}
  Directory.CreateDirectory(System.IO.Path.GetDirectoryName(output));File.WriteAllText(output,text.ToString());
 }
}
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult result){AssetAudit568.Run();result.Log("568 source prefab/skin/binding read-only audit saved; no Play/mesh edits or renderer changes");}}
