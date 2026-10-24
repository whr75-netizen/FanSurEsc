using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
internal class CommandScript:IRunCommand{
 public void Execute(ExecutionResult result){
  const string output="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/EyeInput589/TEXTURE_HASH589.tsv";
  if(File.Exists(output))throw new Exception("Existing query must be consumed, not repeated");
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("Read-only Edit query required");
  var rows=new System.Collections.Generic.List<string>{"texture\twidth\theight\tmips\tformat\tfilter\taniso\twrap\talphaSHA256\tmin\tmax"};
  foreach(var m in AssetDatabase.LoadAllAssetsAtPath("Assets/EUnityValidation01/VRoidSampleA144/Inputs/AvatarSample_A.vrm").OfType<Material>()){
   var t=m.GetTexture("_MainTex")as Texture2D;
   if(!t||!new[]{"_04","_06","_02","_09","_07","_10","_14"}.Contains(t.name))continue;
   var pixels=t.GetPixels32();var alpha=pixels.Select(p=>p.a).ToArray();string hash;
   using(var sha=SHA256.Create())hash=BitConverter.ToString(sha.ComputeHash(alpha)).Replace("-","").ToLowerInvariant();
   rows.Add(t.name+"\t"+t.width+"\t"+t.height+"\t"+t.mipmapCount+"\t"+t.format+"\t"+t.filterMode+"\t"+t.anisoLevel+"\t"+t.wrapMode+"\t"+hash+"\t"+alpha.Min()+"\t"+alpha.Max());
  }
  File.WriteAllLines(output,rows);
  string state="play="+EditorApplication.isPlaying+" dirty="+EditorSceneManager.GetActiveScene().isDirty+" iris="+EyeFeature348.UseIrisSurface582+" lash="+EyeFeature348.UseLashRegion583+" head="+HeadRegion502.Enabled+" clothes="+ClothRegion524.Enabled+" capture="+Time.captureDeltaTime;
  File.WriteAllText(Path.ChangeExtension(output,"state.txt"),state);result.Log("Read-only source alpha hashes; "+state);
 }
}
