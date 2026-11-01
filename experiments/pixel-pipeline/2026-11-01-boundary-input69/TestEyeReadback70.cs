using System;
using System.IO;
using System.Runtime.InteropServices;
using PixelReadback70;
class TestEyeReadback70
{
 sealed class Fake : IBuffer
 {
  public int Count{get;set;}public int Stride{get;set;}public int Calls,MaxRow;public int FailAt=-1;public Action After;
  static F4 V(int index,int field){return new F4(index*100+field*4,index*100+field*4+1,index*100+field*4+2,index*100+field*4+3);}
  public void GetData(Array destination,int destinationStart,int sourceStart,int count)
  {
   Calls++;MaxRow=Math.Max(MaxRow,count*Stride);if(Calls==FailAt)throw new IOException("injected GPU-read failure");
   if(destinationStart!=0||sourceStart<0||sourceStart+count>Count||destination.Length!=count)throw new Exception("row/index contract");
   var f=destination as Feature19[];var p=destination as Pixel348[];
   for(int i=0;i<count;i++)
   {
    int n=sourceStart+i;
    if(f!=null)f[i]=new Feature19{a=V(n,0),b=V(n,1),uv=V(n,2)};
    else if(p!=null)p[i]=new Pixel348{colour=V(n,0),owner=V(n,1),intrinsic=V(n,2),visible=V(n,3),histA=V(n,4),histB=V(n,5),surface=V(n,6),pigment=V(n,7),audit=V(n,8),domain=V(n,9),bary=V(n,10),globalOwner=V(n,11),preparedMeta=V(n,12),preparedUV=V(n,13),control=V(n,14),supportMeta=V(n,15)};
    else throw new Exception("typed layout required");
   }
   if(After!=null)After();
  }
 }
 static string root;static Identity id=new Identity{source="offline-counterexample70",view="head",frame=94,serial=1};static int passed;
 static void Check(bool yes,string message){if(!yes)throw new Exception(message);}
 static void Test(string name,Action action){action();passed++;Console.WriteLine("PASS "+name);}
 static void Throws(Action f){try{f();}catch(ArgumentException){return;}catch(InvalidOperationException){return;}catch(IOException){return;}catch(OperationCanceledException){return;}throw new Exception("failure expected");}
 static Identity Current(){return id;}
 static void Header(BinaryReader r,string kind,int stride,GpuRoi roi)
 {Check(r.ReadString()=="pixel-eye-readback70/v1","magic");Check(r.ReadString()==kind,"kind");Check(r.ReadString()==id.source&&r.ReadString()==id.view&&r.ReadInt32()==id.frame&&r.ReadInt32()==id.serial,"identity");r.ReadString();Check(r.ReadInt32()==roi.x&&r.ReadInt32()==roi.y&&r.ReadInt32()==roi.width&&r.ReadInt32()==roi.height&&r.ReadInt32()==stride,"ROI/stride");}
 static void Main(string[] args)
 {
  root=Path.GetFullPath(args[0]);Directory.CreateDirectory(root);
  Test("actual shader struct sizes",delegate{Check(Marshal.SizeOf(typeof(F4))==16&&Marshal.SizeOf(typeof(Feature19))==48&&Marshal.SizeOf(typeof(Pixel348))==256,"layout");});
  Test("ROI top-left converts to GPU origin exactly once",delegate{var r=Readback.FromTopLeft(204,43,33,21);Check(r.x==204&&r.y==208&&r.width==33&&r.height==21,"ROI conversion");});
  Test("counts both eyes exact floats and indices",delegate{
   var roi=new GpuRoi(211,203,7,3);var b=new Fake{Count=42,Stride=48};Readback.Counts(root,"counts.bin",b,id,roi,Current,null);
   using(var r=new BinaryReader(File.OpenRead(Path.Combine(root,"counts.bin")))){Header(r,"FeaturePacket19:a,b,uv",48,roi);for(int eye=0;eye<2;eye++)for(int y=0;y<3;y++){int start=(eye*3+y)*7;Check(r.ReadInt32()==eye&&r.ReadInt32()==y&&r.ReadInt32()==start,"counts row");for(int x=0;x<7;x++)for(int f=0;f<12;f++)Check(r.ReadSingle()==(start+x)*100+f,"float field");}Check(r.BaseStream.Position==r.BaseStream.Length,"end");}Check(b.Calls==6&&b.MaxRow==336,"bounded counts");});
  Test("records eye ROI exact global indices and256byte fields",delegate{
   var roi=new GpuRoi(204,208,33,21);var b=new Fake{Count=480*272,Stride=256};Readback.Records(root,"records.bin",b,id,roi,Current,null);
   using(var r=new BinaryReader(File.OpenRead(Path.Combine(root,"records.bin")))){Header(r,"Pixel348:sixteenFloat4InShaderOrder",256,roi);for(int y=0;y<21;y++){int start=(208+y)*480+204;Check(r.ReadInt32()==208+y&&r.ReadInt32()==start,"record row");for(int x=0;x<33;x++)for(int f=0;f<64;f++)Check(r.ReadSingle()==(start+x)*100+f,"record float field");}Check(r.BaseStream.Position==r.BaseStream.Length,"record end");}Check(b.Calls==21&&b.MaxRow==8448,"bounded records");});
  Test("duplicate result never overwritten or read again",delegate{var b=new Fake{Count=42,Stride=48};Throws(delegate{Readback.Counts(root,"counts.bin",b,id,new GpuRoi(211,203,7,3),Current,null);});Check(b.Calls==0,"duplicate read");});
  Test("wrong stride count ROI full-grid budget rejected before read",delegate{
   var b=new Fake{Count=42,Stride=16};Throws(delegate{Readback.Counts(root,"wrong.bin",b,id,new GpuRoi(0,0,7,3),Current,null);});b.Stride=48;b.Count=41;Throws(delegate{Readback.Counts(root,"wrong.bin",b,id,new GpuRoi(0,0,7,3),Current,null);});b.Stride=256;b.Count=480*272;Throws(delegate{Readback.Records(root,"wrong.bin",b,id,new GpuRoi(0,0,480,272),Current,null);});Throws(delegate{Readback.Records(root,"wrong.bin",b,id,new GpuRoi(-1,0,1,1),Current,null);});Check(b.Calls==0&&!File.Exists(Path.Combine(root,"wrong.bin.partial")),"preflight must reject");});
  Test("read failure retains partial and no completed packet",delegate{var b=new Fake{Count=42,Stride=48,FailAt=2};Throws(delegate{Readback.Counts(root,"failure.bin",b,id,new GpuRoi(0,0,7,3),Current,null);});Check(b.Calls==2&&File.Exists(Path.Combine(root,"failure.bin.partial"))&&!File.Exists(Path.Combine(root,"failure.bin")),"partial contract");});
  Test("frame advance aborts before another row",delegate{int frame=id.frame;var b=new Fake{Count=42,Stride=48};b.After=delegate{frame++;};Throws(delegate{Readback.Counts(root,"advance.bin",b,id,new GpuRoi(0,0,7,3),delegate{return new Identity{source=id.source,view=id.view,frame=frame,serial=id.serial};},null);});Check(b.Calls==1&&!File.Exists(Path.Combine(root,"advance.bin")),"frame guard");});
  Test("source view or serial mismatch rejected before read",delegate{foreach(int k in new int[]{0,1,2}){var b=new Fake{Count=42,Stride=48};int n=k;Throws(delegate{Readback.Counts(root,"identity"+k+".bin",b,id,new GpuRoi(0,0,7,3),delegate{return new Identity{source=n==0?"other":id.source,view=n==1?"main":id.view,frame=id.frame,serial=n==2?2:1};},null);});Check(b.Calls==0,"identity guard");}});
  Test("cancellation stops own operation without cleanup of borrowed resources",delegate{var b=new Fake{Count=42,Stride=48};Throws(delegate{Readback.Counts(root,"cancel.bin",b,id,new GpuRoi(0,0,7,3),Current,delegate{return b.Calls>0;});});Check(b.Calls==1&&!File.Exists(Path.Combine(root,"cancel.bin")),"cancel guard");});
  Test("unrelated output path rejected",delegate{var b=new Fake{Count=42,Stride=48};Throws(delegate{Readback.Counts(root,"..\\outside.bin",b,id,new GpuRoi(0,0,7,3),Current,null);});Check(b.Calls==0,"path guard");});
  Console.WriteLine("RESULT passed="+passed+" UnityCalls=0 GPUCalls=0");
 }
}
