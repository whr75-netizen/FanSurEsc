using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Profiling;
using Unity.Collections;
internal class CommandScript:IRunCommand{
 const string Root=@"ROOT88",Inputs=@"INPUTS88",Asset="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/FeatureLayer88.compute";
 static Vector4 V(BinaryReader r)=>new Vector4(r.ReadSingle(),r.ReadSingle(),r.ReadSingle(),r.ReadSingle());
 static Vector4[] Vectors(BinaryReader r,int n){var a=new Vector4[n];for(int i=0;i<n;i++)a[i]=V(r);return a;}
 static Obj58 Memory()=>new Obj58{["allocated"]=Profiler.GetTotalAllocatedMemoryLong(),["reserved"]=Profiler.GetTotalReservedMemoryLong(),["mono"]=Profiler.GetMonoUsedSizeLong(),["RTcount"]=Resources.FindObjectsOfTypeAll<RenderTexture>().Length};
 public void Execute(ExecutionResult result){
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required; no Play or settings changes");
  string output=Path.Combine(Root,"gpu-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ")+"-"+Guid.NewGuid().ToString("N").Substring(0,8));Directory.CreateDirectory(output);
  var report=new Obj58{["output"]=output,["before"]=Memory(),["PlayEntries"]=0,["globalWrites"]=0,["productActivation"]=false,["dispatchComplete"]=false};ComputeShader cs=null;var frames=new Arr58();
  try{cs=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<ComputeShader>(Asset));if(!cs)throw new InvalidOperationException("Candidate compute missing");cs.hideFlags=HideFlags.DontSave;int kernel=cs.FindKernel("Draw");
   foreach(string file in Directory.GetFiles(Inputs,"INPUT88.bin",SearchOption.AllDirectories).OrderBy(p=>int.Parse(new DirectoryInfo(Path.GetDirectoryName(p)).Name.Substring(5)))){
    using(var r=new BinaryReader(File.OpenRead(file))){if(r.ReadString()!="feature-layer88/v1")throw new InvalidOperationException("Packet contract");string sourceId=r.ReadString();int frame=r.ReadInt32(),serial=r.ReadInt32(),w=r.ReadInt32(),h=r.ReadInt32();float scale=r.ReadSingle();var origin=new Vector2(r.ReadSingle(),r.ReadSingle());var anchor=new Vector2(r.ReadSingle(),r.ReadSingle());int count=r.ReadInt32();if(count<=0||count>1024||w*h>16384)throw new InvalidOperationException("Bounded packet exceeded");var cells=Vectors(r,count*2);int paletteCount=r.ReadInt32();if(paletteCount<=0||paletteCount>4096)throw new InvalidOperationException("Palette size");var palette=Vectors(r,paletteCount);int rx=r.ReadInt32(),ry=r.ReadInt32(),rw=r.ReadInt32(),rh=r.ReadInt32();int maskCount=5*rw*4*rh*4;if(maskCount*16L>1024*1024)throw new InvalidOperationException("Source mask exceeds one MiB");var mask=Vectors(r,maskCount);var ray=new Vector4[4];for(int i=0;i<4;i++)ray[i]=new Vector4(r.ReadSingle(),r.ReadSingle(),r.ReadSingle(),0);var planes=Vectors(r,2);int owner0=r.ReadInt32(),owner1=r.ReadInt32();if(r.BaseStream.Position!=r.BaseStream.Length)throw new InvalidOperationException("Trailing packet bytes");
     ComputeBuffer cb=null,pb=null,mb=null;var textures=new RenderTexture[3];
     try{cb=new ComputeBuffer(count*2,16);cb.SetData(cells);pb=new ComputeBuffer(paletteCount,16);pb.SetData(palette);mb=new ComputeBuffer(maskCount,16);mb.SetData(mask);for(int i=0;i<3;i++){textures[i]=new RenderTexture(w,h,0,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear){enableRandomWrite=true,filterMode=FilterMode.Point,hideFlags=HideFlags.DontSave,name="88 owned isolated layer "+i};if(!textures[i].Create())throw new InvalidOperationException("Own RT create failed");}
      cs.SetBuffer(kernel,"_Cells88",cb);cs.SetBuffer(kernel,"_Palette88",pb);cs.SetBuffer(kernel,"_Meta88",mb);cs.SetInt("_Count88",count);cs.SetInt("_PaletteCount88",paletteCount);cs.SetInts("_Size88",w,h);cs.SetInts("_MetaSize88",rw*4,rh*4);cs.SetInts("_SourceROI88",rx,ry,rw,rh);cs.SetInts("_Owners88",owner0,owner1);cs.SetFloat("_Scale88",scale);cs.SetVector("_Origin88",origin);cs.SetVector("_Anchor88",anchor);foreach(var v in new[]{new{n="_RayBase88",v=ray[0]},new{n="_RayX88",v=ray[1]},new{n="_RayY88",v=ray[2]},new{n="_RayDepth88",v=ray[3]},new{n="_Plane088",v=planes[0]},new{n="_Plane188",v=planes[1]}})cs.SetVector(v.n,v.v);for(int i=0;i<3;i++)cs.SetTexture(kernel,new[]{"_Colour88","_Identity88","_Coverage88"}[i],textures[i]);cs.Dispatch(kernel,(w+7)/8,(h+7)/8,1);
      for(int ch=0;ch<3;ch++){var data=new NativeArray<Color>(w*h,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);try{var req=AsyncGPUReadback.RequestIntoNativeArray(ref data,textures[ch],0,TextureFormat.RGBAFloat);req.WaitForCompletion();if(req.hasError)throw new InvalidOperationException("Own bounded readback failed");using(var bw=new BinaryWriter(new FileStream(Path.Combine(output,"frame"+frame+"-"+ch+".bin"),FileMode.CreateNew,FileAccess.Write,FileShare.Read))){bw.Write("feature-layer88-GPU/v1");bw.Write(sourceId);bw.Write(frame);bw.Write(serial);bw.Write(w);bw.Write(h);foreach(var c in data){bw.Write(c.r);bw.Write(c.g);bw.Write(c.b);bw.Write(c.a);}}}finally{if(data.IsCreated)data.Dispose();}}
      frames.Add(new Obj58{["sourceId"]=sourceId,["frame"]=frame,["serial"]=serial,["width"]=w,["height"]=h,["cells"]=count,["maskBytes"]=maskCount*16,["largestReadbackBytes"]=w*h*16});
     }finally{cb?.Dispose();pb?.Dispose();mb?.Dispose();foreach(var t in textures)if(t){t.Release();UnityEngine.Object.DestroyImmediate(t);}}
    }
   }
   if(frames.Count!=24)throw new InvalidOperationException("Incomplete saved sequence");report["dispatchComplete"]=true;
  }catch(Exception e){report["error"]=e.ToString();}
  finally{if(cs)UnityEngine.Object.DestroyImmediate(cs);report["after"]=Memory();report["ownedResourcesReleaseAttempted"]=true;report["frames"]=frames;var rows=new Arr58();foreach(var row in Json58.Parse(File.ReadAllText(Path.Combine(Root,"NATIVE_BEFORE73.json"))))rows.Add(new Obj58{["path"]=row["path"],["type"]=row["type"],["snapshot"]=row["snapshot"]});report["nativeComparisons"]=NativeSnapshot73.Compare(Root,rows);CreateOnly73.Text(Path.Combine(Root,"GPU_RESULT88.json"),report.ToString());if((bool)report["dispatchComplete"])CreateOnly73.Text(Path.Combine(output,"DISPATCH_COMPLETE88.marker"),"GPU dispatch complete; offline equality and state validation still required");}
  result.Log("88 isolated saved-input GPU dispatch; no runtime/product/Play activation; inspect GPU_RESULT88");
 }
}
