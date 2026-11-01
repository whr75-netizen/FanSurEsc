using System;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;
// Diagnostic input loader and readback, excluded from the runtime path.
public sealed class FrozenComposition96:IDisposable{
 public readonly WholeEye96.Composition Bindings=new WholeEye96.Composition();readonly Texture2D[] input=new Texture2D[8];ComputeBuffer records;bool disposed;
 public struct Record{public Vector4 a0,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15;}
 static Vector4 V(BinaryReader r)=>new Vector4(r.ReadSingle(),r.ReadSingle(),r.ReadSingle(),r.ReadSingle());
 public FrozenComposition96(string file){
  try{using(var r=new BinaryReader(File.OpenRead(file))){if(r.ReadString()!="whole-eye96-composition/v1")throw new InvalidOperationException("Composition source contract");r.ReadInt32();Bindings.nativeROI=V(r);Bindings.oldROI=V(r);Bindings.backingROI=V(r);Bindings.recordROI=V(r);Bindings.originScale=V(r);Bindings.joinDelta=V(r);Bindings.anchorBounds=V(r);Bindings.depthOffset=r.ReadSingle();Bindings.cropped=true;
   int count=r.ReadInt32();var rr=new Record[count];for(int i=0;i<count;i++)rr[i]=new Record{a0=V(r),a1=V(r),a2=V(r),a3=V(r),a4=V(r),a5=V(r),a6=V(r),a7=V(r),a8=V(r),a9=V(r),a10=V(r),a11=V(r),a12=V(r),a13=V(r),a14=V(r),a15=V(r)};records=new ComputeBuffer(count,256);records.SetData(rr);Bindings.records=records;
   for(int i=0;i<8;i++){int w=r.ReadInt32(),h=r.ReadInt32();if(w*h>32768)throw new InvalidOperationException("Bounded fixture texture");var bytes=r.ReadBytes(w*h*16);input[i]=new Texture2D(w,h,TextureFormat.RGBAFloat,false,true){hideFlags=HideFlags.DontSave,filterMode=FilterMode.Point};input[i].LoadRawTextureData(bytes);input[i].Apply(false,false);}if(r.BaseStream.Position!=r.BaseStream.Length)throw new InvalidOperationException("Trailing composition bytes");}
   Bindings.baseColour=input[0];Bindings.baseOwner=input[1];Bindings.baseDepth=input[2];Bindings.oldOwner=input[3];Bindings.oldIntrinsic=input[4];Bindings.backingColour=input[5];Bindings.backingMeta=input[6];Bindings.backingUV=input[7];Bindings.output=new RenderTexture[4];for(int i=0;i<4;i++){var t=new RenderTexture((int)Bindings.nativeROI.z,(int)Bindings.nativeROI.w,0,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear){enableRandomWrite=true,hideFlags=HideFlags.DontSave,filterMode=FilterMode.Point};Bindings.output[i]=t;if(!t.Create())throw new InvalidOperationException("Owned output RT creation");}
  }catch{Dispose();throw;}
 }
 public void Write(string root,int frame){for(int i=0;i<4;i++){var req=AsyncGPUReadback.Request(Bindings.output[i],0,TextureFormat.RGBAFloat);req.WaitForCompletion();if(req.hasError)throw new InvalidOperationException("Diagnostic readback");var data=req.GetData<Color>();using(var w=new BinaryWriter(new FileStream(Path.Combine(root,frame+"-final"+i+".bin"),FileMode.CreateNew))){w.Write(data.Length);foreach(var c in data){w.Write(c.r);w.Write(c.g);w.Write(c.b);w.Write(c.a);}}}}
 public void Dispose(){if(disposed)return;disposed=true;records?.Dispose();foreach(var t in input)if(t)UnityEngine.Object.DestroyImmediate(t);if(Bindings.output!=null)foreach(var t in Bindings.output)if(t){t.Release();UnityEngine.Object.DestroyImmediate(t);}}
}
