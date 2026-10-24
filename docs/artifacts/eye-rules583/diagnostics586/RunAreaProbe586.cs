using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
public struct AreaFilterInput586 { public Vector4 uvdx,dyparams; }
internal class CommandScript : IRunCommand {
 public void Execute(ExecutionResult result) {
  const string baseRoot="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/EyeFilter586/";
  var token=File.ReadAllText(baseRoot+"CURRENT_AREA_JOB586.txt").Trim();
  if(!token.All(c=>char.IsLetterOrDigit(c)||c=='_'))throw new Exception("Job token");
  var root=baseRoot+token+"/";
  if(EditorApplication.isPlaying||EditorApplication.isCompiling||File.Exists(root+"STARTED.txt"))throw new Exception("Unique job and clean Edit required");
  var lines=File.ReadAllLines(root+"GROUPS.tsv").Skip(1).Where(l=>l.Length>0).Select(l=>l.Split('\t')).ToArray();
  foreach(var q in lines)if(q.Length!=4||File.Exists(q[3]))throw new Exception("Inspect existing output before any repeat");
  var shader=AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Diagnostics586/AlphaSampler586.compute");
  if(!shader)throw new Exception("Existing sampler diagnostic required");
  var textures=AssetDatabase.LoadAllAssetsAtPath("Assets/EUnityValidation01/VRoidSampleA144/Inputs/AvatarSample_A.vrm").OfType<Texture2D>().GroupBy(t=>t.name).ToDictionary(g=>g.Key,g=>g.First());
  File.WriteAllText(root+"STARTED.txt","ENTERED");int kernel=shader.FindKernel("Probe586"),done=0;double began=EditorApplication.timeSinceStartup;
  foreach(var q in lines) {
   int count=int.Parse(q[1]);var data=new AreaFilterInput586[count];
   using(var b=new BinaryReader(File.OpenRead(q[2]))) {
    if(b.ReadInt32()!=count)throw new Exception("Input count");
    for(int i=0;i<count;i++)data[i]=new AreaFilterInput586{uvdx=new Vector4(b.ReadSingle(),b.ReadSingle(),b.ReadSingle(),b.ReadSingle()),dyparams=new Vector4(b.ReadSingle(),b.ReadSingle(),b.ReadSingle(),b.ReadSingle())};
   }
   ComputeBuffer input=null,output=null;
   try {
    input=new ComputeBuffer(count,32);output=new ComputeBuffer(count,16);input.SetData(data);
    shader.SetInt("_Count586",count);shader.SetTexture(kernel,"_MainTex",textures[q[0]]);shader.SetBuffer(kernel,"_Input586",input);shader.SetBuffer(kernel,"_Output586",output);
    shader.Dispatch(kernel,(count+63)/64,1,1);var values=new Vector4[count];output.GetData(values);
    using(var b=new BinaryWriter(new FileStream(q[3],FileMode.CreateNew))) {b.Write(count);foreach(var v in values){b.Write(v.x);b.Write(v.y);b.Write(v.z);b.Write(v.w);}}
    done++;File.WriteAllText(root+"PROGRESS.json","{\"groups\":"+done+"}");
   } finally {input?.Release();output?.Release();}
  }
  File.WriteAllText(root+"COMPLETE.json","{\"groups\":"+done+",\"secondsIncludingReadback\":"+(EditorApplication.timeSinceStartup-began).ToString("R",System.Globalization.CultureInfo.InvariantCulture)+",\"settingsChanged\":false,\"originalRenderBuffersTouched\":false}");
  result.Log("586 area-filter batch complete: "+token+"; diagnostic sampling only");
 }
}
