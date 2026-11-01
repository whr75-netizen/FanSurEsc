// Pure bounded protocol core. No Unity dependency, borrowed-buffer disposal,
// static data cache, full-grid allocation, or implicit top-left/bottom-left flip.
using System;
using System.IO;
using System.Security.Cryptography;
using System.Globalization;
namespace PixelReadback70
{
 public struct F4 { public float x,y,z,w; public F4(float a,float b,float c,float d){x=a;y=b;z=c;w=d;} }
 public struct Feature19 { public F4 a,b,uv; }
 public struct Pixel348 { public F4 colour,owner,intrinsic,visible,histA,histB,surface,pigment,audit,domain,bary,globalOwner,preparedMeta,preparedUV,control,supportMeta; }
 public struct Identity { public string source,view;public int frame,serial;public bool Same(Identity o){return source==o.source&&view==o.view&&frame==o.frame&&serial==o.serial;} }
 public struct GpuRoi { public int x,y,width,height;public GpuRoi(int a,int b,int c,int d){x=a;y=b;width=c;height=d;} }
 public interface IBuffer { int Count{get;} int Stride{get;} void GetData(Array destination,int destinationStart,int sourceStart,int count); }
 public static class Readback
 {
  public const int GridWidth=480,GridHeight=272,MaxRowBytes=1024*1024,MaxPayloadBytes=1024*1024;
  public static GpuRoi FromTopLeft(int x,int y,int width,int height){return new GpuRoi(x,GridHeight-y-height,width,height);}
  static void Validate(IBuffer b,Identity id,GpuRoi r,int stride,int count)
  {
   if(b==null||b.Stride!=stride||b.Count!=count)throw new ArgumentException("Buffer layout/count mismatch");
   if(String.IsNullOrEmpty(id.source)||String.IsNullOrEmpty(id.view)||id.frame<0||id.serial<=0)throw new ArgumentException("Actual source/frame/view/serial required");
   if(r.x<0||r.y<0||r.width<=0||r.height<=0||(long)r.x+r.width>GridWidth||(long)r.y+r.height>GridHeight)throw new ArgumentException("GPU bottom-left ROI out of bounds");
   if((long)r.width*stride>MaxRowBytes)throw new ArgumentException("Owned row budget exceeded");
  }
  static void Check(Identity id,Func<Identity> current,Func<bool> cancel)
  {if(cancel!=null&&cancel())throw new OperationCanceledException();if(current==null||!id.Same(current()))throw new InvalidOperationException("Source/frame/view/serial advanced");}
  static string Target(string root,string name)
  {if(String.IsNullOrEmpty(name)||name=="."||name==".."||name.IndexOfAny(Path.GetInvalidFileNameChars())>=0||Path.GetFileName(name)!=name)throw new ArgumentException("Local file name required");string path=Path.Combine(Path.GetFullPath(root),name);if(File.Exists(path)||File.Exists(path+".partial"))throw new IOException("Existing result: inspect before repeat");return path;}
  static void Header(BinaryWriter w,string kind,Identity id,GpuRoi r,int stride)
  {w.Write("pixel-eye-readback70/v1");w.Write(kind);w.Write(id.source);w.Write(id.view);w.Write(id.frame);w.Write(id.serial);w.Write("GPU storage bottom-left; caller converts e.roi.y via272-y-height exactly once");w.Write(r.x);w.Write(r.y);w.Write(r.width);w.Write(r.height);w.Write(stride);}
  static void V(BinaryWriter w,F4 v){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}
  static void Pixel(BinaryWriter w,Pixel348 p){V(w,p.colour);V(w,p.owner);V(w,p.intrinsic);V(w,p.visible);V(w,p.histA);V(w,p.histB);V(w,p.surface);V(w,p.pigment);V(w,p.audit);V(w,p.domain);V(w,p.bary);V(w,p.globalOwner);V(w,p.preparedMeta);V(w,p.preparedUV);V(w,p.control);V(w,p.supportMeta);}
  static string CompletionMarker(string path)
  {long n;string hash;using(var h=SHA256.Create())using(var f=File.OpenRead(path)){n=f.Length;hash=BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}return Path.Combine(Path.GetDirectoryName(path),"ok-"+hash+"-"+n.ToString(CultureInfo.InvariantCulture)+".complete");}
  static void Complete(string target,Identity id,Func<Identity> current,Func<bool> cancel)
  {string marker=CompletionMarker(target+".partial");Check(id,current,cancel);using(var f=new FileStream(marker,FileMode.CreateNew,FileAccess.Write,FileShare.Read)){} }
  public static string CompletedPath(string root,string name)
  {string path=Path.Combine(Path.GetFullPath(root),name+".partial");string marker=CompletionMarker(path);if(!File.Exists(marker)||new FileInfo(marker).Length!=0)throw new IOException("No validated zero-byte completion marker");return path;}
  public static void Counts(string root,string name,IBuffer source,Identity id,GpuRoi r,Func<Identity> current,Func<bool> cancel)
  {
   int count=checked(r.width*r.height*2);Validate(source,id,r,48,count);if((long)count*48>MaxPayloadBytes)throw new ArgumentException("Count ROI payload budget exceeded");Check(id,current,cancel);string target=Target(root,name);var row=new Feature19[r.width];
   using(var stream=new FileStream(target+".partial",FileMode.CreateNew,FileAccess.Write,FileShare.Read))using(var w=new BinaryWriter(stream))
   {
    Header(w,"FeaturePacket19:a,b,uv",id,r,48);
    for(int eye=0;eye<2;eye++)for(int y=0;y<r.height;y++)
    {Check(id,current,cancel);int start=(eye*r.height+y)*r.width;source.GetData(row,0,start,r.width);Check(id,current,cancel);w.Write(eye);w.Write(y);w.Write(start);for(int x=0;x<r.width;x++){V(w,row[x].a);V(w,row[x].b);V(w,row[x].uv);}}
    w.Flush();stream.Flush(true);
   }
   Check(id,current,cancel);Complete(target,id,current,cancel);
  }
  public static void Records(string root,string name,IBuffer source,Identity id,GpuRoi r,Func<Identity> current,Func<bool> cancel)
  {
   Validate(source,id,r,256,GridWidth*GridHeight);if((long)r.width*r.height*256>MaxPayloadBytes)throw new ArgumentException("Record ROI payload budget exceeded");Check(id,current,cancel);string target=Target(root,name);var row=new Pixel348[r.width];
   using(var stream=new FileStream(target+".partial",FileMode.CreateNew,FileAccess.Write,FileShare.Read))using(var w=new BinaryWriter(stream))
   {
    Header(w,"Pixel348:sixteenFloat4InShaderOrder",id,r,256);
    for(int y=0;y<r.height;y++)
    {Check(id,current,cancel);int start=(r.y+y)*GridWidth+r.x;source.GetData(row,0,start,r.width);Check(id,current,cancel);w.Write(r.y+y);w.Write(start);for(int x=0;x<r.width;x++)Pixel(w,row[x]);}
    w.Flush();stream.Flush(true);
   }
   Check(id,current,cancel);Complete(target,id,current,cancel);
  }
 }
}
