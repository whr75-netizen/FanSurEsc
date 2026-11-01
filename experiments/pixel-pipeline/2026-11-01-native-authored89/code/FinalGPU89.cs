using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Profiling;
using Unity.Collections;
internal class CommandScript:IRunCommand{
 const string Root=@"ROOT_FINAL89",Inputs=@"INPUT_FINAL89",Asset="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/FinalPalette89.compute";
 static Vector4[] Vectors(BinaryReader r,int count){var a=new Vector4[count];for(int i=0;i<count;i++)a[i]=new Vector4(r.ReadSingle(),r.ReadSingle(),r.ReadSingle(),r.ReadSingle());return a;}
 static Obj58 Memory()=>new Obj58{["allocated"]=Profiler.GetTotalAllocatedMemoryLong(),["reserved"]=Profiler.GetTotalReservedMemoryLong(),["mono"]=Profiler.GetMonoUsedSizeLong(),["RTcount"]=Resources.FindObjectsOfTypeAll<RenderTexture>().Length};
 public void Execute(ExecutionResult result){
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit only");
  var report=new Obj58{["before"]=Memory(),["PlayEntries"]=0,["productActivation"]=false,["globalWrites"]=0,["jointAllocation"]="offline; this GPU kernel verifies literal final palette fill only",["dispatchComplete"]=false};ComputeShader cs=null;var rows=new Arr58();
  string output=Path.Combine(Root,"gpu-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ")+"-"+Guid.NewGuid().ToString("N").Substring(0,8));Directory.CreateDirectory(output);report["output"]=output;
  try{
   cs=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<ComputeShader>(Asset));if(!cs)throw new InvalidOperationException("Isolated final LUT asset missing");cs.hideFlags=HideFlags.DontSave;int kernel=cs.FindKernel("Fill");
   foreach(string file in Directory.GetFiles(Inputs,"*.bin").OrderBy(p=>p))using(var r=new BinaryReader(File.OpenRead(file))){
    if(r.ReadString()!="final-palette89/v1")throw new InvalidOperationException("Input contract");string source=r.ReadString(),variant=r.ReadString();int frame=r.ReadInt32(),serial=r.ReadInt32(),w=r.ReadInt32(),h=r.ReadInt32(),count=r.ReadInt32();if(w*h>32768||count>4096||count<1)throw new InvalidOperationException("Bounded replay budget");var b=Vectors(r,w*h);var map=Vectors(r,w*h);var palette=Vectors(r,count);if(r.BaseStream.Position!=r.BaseStream.Length)throw new InvalidOperationException("Trailing data");ComputeBuffer bb=null,mb=null,pb=null;var rt=new RenderTexture[3];
    try{
     bb=new ComputeBuffer(b.Length,16);mb=new ComputeBuffer(map.Length,16);pb=new ComputeBuffer(palette.Length,16);bb.SetData(b);mb.SetData(map);pb.SetData(palette);
     for(int i=0;i<3;i++){rt[i]=new RenderTexture(w,h,0,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear){enableRandomWrite=true,filterMode=FilterMode.Point,hideFlags=HideFlags.DontSave,name="89 owned final palette "+i};if(!rt[i].Create())throw new InvalidOperationException("Own RT creation");}
     cs.SetInts("_Size89",w,h);cs.SetInt("_PaletteCount89",count);cs.SetBuffer(kernel,"_Base89",bb);cs.SetBuffer(kernel,"_Select89",mb);cs.SetBuffer(kernel,"_Palette89",pb);for(int i=0;i<3;i++)cs.SetTexture(kernel,new[]{"_Final89","_Owner89","_Valid89"}[i],rt[i]);cs.Dispatch(kernel,(w+7)/8,(h+7)/8,1);
     for(int ch=0;ch<3;ch++){var data=new NativeArray<Color>(w*h,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);try{var req=AsyncGPUReadback.RequestIntoNativeArray(ref data,rt[ch],0,TextureFormat.RGBAFloat);req.WaitForCompletion();if(req.hasError)throw new InvalidOperationException("Own readback failure");using(var bw=new BinaryWriter(new FileStream(Path.Combine(output,Path.GetFileNameWithoutExtension(file)+"-"+ch+".bin"),FileMode.CreateNew,FileAccess.Write,FileShare.Read))){bw.Write("final-palette89-GPU/v1");bw.Write(source);bw.Write(variant);bw.Write(frame);bw.Write(serial);bw.Write(w);bw.Write(h);foreach(var c in data){bw.Write(c.r);bw.Write(c.g);bw.Write(c.b);bw.Write(c.a);}}}finally{if(data.IsCreated)data.Dispose();}}
     rows.Add(new Obj58{["sourceId"]=source,["variant"]=variant,["frame"]=frame,["serial"]=serial,["size"]=new Arr58(w,h),["paletteCount"]=count,["largestReadbackBytes"]=w*h*16});
    }finally{bb?.Dispose();mb?.Dispose();pb?.Dispose();foreach(var t in rt)if(t){t.Release();UnityEngine.Object.DestroyImmediate(t);}}
   }
   report["dispatchComplete"]=rows.Count==64;
  }catch(Exception error){report["error"]=error.ToString();}
  finally{if(cs)UnityEngine.Object.DestroyImmediate(cs);report["after"]=Memory();report["rows"]=rows;report["ownedResourcesReleased"]=true;CreateOnly73.Text(Path.Combine(Root,"FINAL_GPU89.json"),report.ToString());if((bool)report["dispatchComplete"])CreateOnly73.Text(Path.Combine(output,"DISPATCH_COMPLETE89.marker"),"GPU replay complete; offline validation still required");}
  result.Log("89 isolated saved-frame finite-palette final fill; no product/Play activation");
 }
}
