using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;

namespace Prefix24 {
// C# value structs have sequential layout by default. Only32-bit scalar/nested
// value fields are used. Actual sizes/offsets are checked OUTSIDE Unity by the
// CPU test executable; the live command performs no native interop or Marshal.
public struct F4 { public float x,y,z,w; public F4(float a,float b,float c,float d){x=a;y=b;z=c;w=d;} }
public struct U4 { public uint x,y,z,w; public U4(uint a,uint b,uint c,uint d){x=a;y=b;z=c;w=d;} }
public struct Group24 { public F4 score; public U4 masks,tail; }
public struct Subset24 { public U4 a,b; }
[Serializable] public sealed class Blob24 {
 public string Name;
 public string File;
 public int Stage;
 public int Bytes;
 public string Sha256;
}
[Serializable] public sealed class Global24 { public string Name; public string Type; }
[Serializable] public sealed class Case24 {
 public string Schema,SourceId,RunId,ShaderAssetPath,ShaderSha256,ShaderGuid;
 public int SourceFrame,SourceSerial,Width,Height,Owner;
 public Blob24[] InputFiles;
 public Global24[] Globals;
}
[Serializable] public sealed class Receipt24 {
 public string Schema="prefix24/receipt/v1",ExecutionKind,RunId,CaseSha256,SourceId,ShaderSha256;
 public int Stage,DispatchCalls;
 public bool Success,StateEqual,ResourcesReleased;
 public string BeforeStateSha256,AfterStateSha256,Error;
 public Blob24[] Outputs;
}

// One fixed diagnostic run; callbacks cannot advance this state to a new stage.
public sealed class StepGate24 {
 public int DispatchCalls {get;private set;}
 public int Pending {get;private set;}
 public bool Unknown {get;private set;}
 public bool Failed {get;private set;}
 public bool Issuing {get;private set;}
 public bool Finalized {get;private set;}
 bool returned; int completed; readonly HashSet<string> reads=new HashSet<string>();
 public void BeforeDispatch(){if(DispatchCalls!=0||Finalized)throw new InvalidOperationException("One dispatch only");DispatchCalls=1;Unknown=true;}
 public void DispatchReturned(){if(DispatchCalls!=1||returned)throw new InvalidOperationException("Submission state");returned=true;Unknown=false;}
 public void BeginReads(){if(!returned||Issuing)throw new InvalidOperationException("No overlapping scheduling");Issuing=true;}
 public void BeforeRead(string name){if(!Issuing||!reads.Add(name))throw new InvalidOperationException("Duplicate read");Pending++;}
 public void ReadRequestUncertain(){Unknown=true;Failed=true;}
 public void EndReads(){Issuing=false;}
 public void CompleteRead(string name,bool done,bool hasError){
  if(Finalized)throw new InvalidOperationException("Late callback after terminal state");
  if(!done){Unknown=true;Failed=true;return;}
  if(!reads.Remove(name))throw new InvalidOperationException("Unregistered or duplicate callback");
  Pending--;completed++;if(hasError)Failed=true;
 }
 public void Fail(){Failed=true;}
 public bool CanRelease=>!Finalized&&!Unknown&&!Issuing&&Pending==0&&(DispatchCalls==0||(returned&&completed>0));
 public void MarkFinalized(){if(!CanRelease)throw new InvalidOperationException("GPU completion not established");Finalized=true;}
 public bool CanComplete=>Finalized&&!Failed&&DispatchCalls==1;
}

public static class Protocol24 {
 public const int MaxBlobBytes=4*1024*1024;
 // Host installs Unity JsonUtility. The external CPU test installs its own
 // field serializer; neither path requires a live command assembly reference
 // to System.Runtime.Serialization or native interop.
 public static Func<object,byte[]> Encode;
 public static Func<byte[],Type,object> Decode;
 public static string Hash(byte[] bytes){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();}
 public static byte[] ReadBounded(string path,int limit){var f=new FileInfo(path);if(f.Length<1||f.Length>limit)throw new IOException("File budget");return File.ReadAllBytes(path);}
 public static byte[] Json<T>(T value){if(Encode==null)throw new InvalidOperationException("Metadata encoder not installed");var bytes=Encode(value);if(bytes==null||bytes.Length>256*1024)throw new IOException("Metadata budget");return bytes;}
 public static T Parse<T>(byte[] bytes){if(Decode==null)throw new InvalidOperationException("Metadata decoder not installed");if(bytes.Length>256*1024)throw new IOException("Metadata budget");return(T)Decode(bytes,typeof(T));}
 public static void Create(string path,byte[] bytes){if(bytes.Length>MaxBlobBytes)throw new IOException("Output budget");using(var f=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read)){f.Write(bytes,0,bytes.Length);f.Flush(true);}}
 public static void CreateJson<T>(string path,T value){Create(path,Json(value));}
 public static string Child(string parent,string name){if(String.IsNullOrEmpty(name)||Path.GetFileName(name)!=name||name=="."||name=="..")throw new IOException("Relative filename required");return Path.Combine(parent,name);}
 public static Case24 LoadCase(string root,string approvedHash){
  if(!BitConverter.IsLittleEndian)throw new PlatformNotSupportedException("Little-endian fixture");
  var bytes=ReadBounded(Path.Combine(root,"CASE.json"),65536);if(Hash(bytes)!=approvedHash)throw new IOException("Unapproved case");var c=Parse<Case24>(bytes);
  if(c.Schema!="prefix24/case/v1"||c.SourceFrame!=103||c.SourceSerial!=10||c.Width!=18||c.Height!=8||c.Owner!=2||c.InputFiles==null||c.InputFiles.Select(x=>x.Name).Distinct().Count()!=c.InputFiles.Length)throw new IOException("Frozen case changed");
  foreach(var row in c.InputFiles){var data=ReadBounded(Child(Path.Combine(root,"fixture"),row.File),MaxBlobBytes);if(data.Length!=row.Bytes||Hash(data)!=row.Sha256)throw new IOException("Fixture hash "+row.Name);}
  ValidateCaseData(c,root);
  return c;
 }
 public static void ValidateCaseData(Case24 c,string root){
  var sizes=new Dictionary<string,int>{{"cells",57344},{"tags",8192},{"frame",1024},{"points",768},{"old-best",96}};
  foreach(var row in sizes)if(Input(c,root,row.Key).Length!=row.Value)throw new IOException("Input stride/count");
  var frame=UInts(Input(c,root,"frame"));if(frame[0].x!=9||frame[0].y!=5||frame[0].z!=6||frame[0].w!=0)throw new IOException("Frozen header");
  var points=UInts(Input(c,root,"points"));for(int i=0;i<9;i++)if(points[i].x>=144||(points[i].y!=UInt32.MaxValue&&points[i].y>=5)||(points[i].z!=UInt32.MaxValue&&points[i].z>=6)||(points[i].w&~511u)!=0)throw new IOException("Point/mask bounds");
  var cells=Fours(Input(c,root,"cells"));for(int i=0;i<144;i++){var m=cells[i*7];if(Single.IsNaN(m.x)||Single.IsNaN(m.y)||Single.IsNaN(m.z)||Single.IsNaN(m.w)||Single.IsInfinity(m.x)||Single.IsInfinity(m.y)||Single.IsInfinity(m.z)||Single.IsInfinity(m.w)||m.x<0||m.z<0||m.y<m.x||m.w<m.z)throw new IOException("Invalid source mass");}
  var expected=new Dictionary<string,int>{{"subsets-I",2048},{"subsets-W",2048},{"groups",1536},{"best",48},{"colour",2304},{"identity",2304},{"decision",2304},{"audit",2304}};
  if(c.InputFiles.Length!=sizes.Count+expected.Count)throw new IOException("Case blob set");foreach(var row in expected)if(c.InputFiles.Single(x=>x.Name==row.Key&&x.Stage>0).Bytes!=row.Value)throw new IOException("Output count/stride");
 }
 public static byte[] Input(Case24 c,string root,string name){var row=c.InputFiles.Single(x=>x.Name==name&&x.Stage==0);return ReadBounded(Child(Path.Combine(root,"fixture"),row.File),row.Bytes);}
 public static Blob24 ValidateOutput(Case24 c,int stage,string name,byte[] bytes){var row=c.InputFiles.Single(x=>x.Name==name&&x.Stage==stage);if(bytes.Length!=row.Bytes||Hash(bytes)!=row.Sha256)throw new IOException("GPU/CPU byte mismatch "+name);return new Blob24{Name=name,File=name+".bin",Stage=stage,Bytes=bytes.Length,Sha256=Hash(bytes)};}
 public static string StagePath(string runRoot,int stage){if(stage<1||stage>4)throw new ArgumentOutOfRangeException(nameof(stage));return Path.Combine(runRoot,"stage-"+stage.ToString("D2"));}
 public static Receipt24 Previous(Case24 c,string caseHash,string runRoot,int stage){
  if(stage<=1||stage>4)throw new ArgumentOutOfRangeException(nameof(stage));var dir=StagePath(runRoot,stage-1);var bytes=ReadBounded(Path.Combine(dir,"COMPLETE.json"),65536);
  if(File.Exists(Path.Combine(dir,"FAILED.json"))||Directory.EnumerateFiles(dir,"PENDING-*.json").Any())throw new IOException("Failed/pending predecessor is never complete");
  var r=Parse<Receipt24>(bytes);CheckReceipt(c,caseHash,stage-1,r,"gpu-prefix");
  foreach(var row in r.Outputs){var data=ReadBounded(Child(dir,row.File),MaxBlobBytes);if(data.Length!=row.Bytes||Hash(data)!=row.Sha256)throw new IOException("Previous output corrupt");ValidateOutput(c,stage-1,row.Name,data);}
  return r;
 }
 public static void CheckReceipt(Case24 c,string hash,int stage,Receipt24 r,string kind){
  if(r.Schema!="prefix24/receipt/v1"||r.ExecutionKind!=kind||r.RunId!=c.RunId||r.Stage!=stage||r.CaseSha256!=hash||r.SourceId!=c.SourceId||r.ShaderSha256!=c.ShaderSha256||r.DispatchCalls!=1||!r.Success||!r.StateEqual||!r.ResourcesReleased||r.BeforeStateSha256!=r.AfterStateSha256||!String.IsNullOrEmpty(r.Error)||r.Outputs==null)throw new IOException("No validated predecessor");
  var names=c.InputFiles.Where(x=>x.Stage==stage).Select(x=>x.Name).OrderBy(x=>x,StringComparer.Ordinal);
  if(!names.SequenceEqual(r.Outputs.Select(x=>x.Name).OrderBy(x=>x,StringComparer.Ordinal)))throw new IOException("Incomplete outputs");
 }
 public static byte[] PreviousBytes(Case24 c,string hash,string runRoot,int stage,string name){var r=Previous(c,hash,runRoot,stage);var row=r.Outputs.Single(x=>x.Name==name);return ReadBounded(Child(StagePath(runRoot,stage-1),row.File),row.Bytes);}
 public static string ClaimStage(Case24 c,string caseHash,string runRoot,int stage){
  if(Path.GetFileName(runRoot)!=c.RunId)throw new IOException("Run identity mismatch");
  if(stage>1)Previous(c,caseHash,runRoot,stage);
  string dir=StagePath(runRoot,stage);Directory.CreateDirectory(dir);
  if(Directory.EnumerateFileSystemEntries(dir).Any())throw new IOException("Stage already has intent, submission, pending or output evidence; no replay");
  // CreateNew is the single-use claim; even an uncertain prior attempt blocks replay.
  Create(Path.Combine(dir,"INTENT.json"),Json(new Receipt24{ExecutionKind="intent",RunId=c.RunId,Stage=stage,CaseSha256=caseHash,SourceId=c.SourceId,ShaderSha256=c.ShaderSha256}));
  return dir;
 }
 public static F4[] Fours(byte[] bytes){if(bytes.Length%16!=0)throw new IOException("F4 stride");var a=new F4[bytes.Length/16];using(var r=new BinaryReader(new MemoryStream(bytes)))for(int i=0;i<a.Length;i++)a[i]=new F4(r.ReadSingle(),r.ReadSingle(),r.ReadSingle(),r.ReadSingle());return a;}
 public static U4[] UInts(byte[] bytes){if(bytes.Length%16!=0)throw new IOException("U4 stride");var a=new U4[bytes.Length/16];using(var r=new BinaryReader(new MemoryStream(bytes)))for(int i=0;i<a.Length;i++)a[i]=new U4(r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32());return a;}
 public static Group24[] Groups(byte[] bytes){if(bytes.Length%48!=0)throw new IOException("Group stride");var a=new Group24[bytes.Length/48];using(var r=new BinaryReader(new MemoryStream(bytes)))for(int i=0;i<a.Length;i++)a[i]=new Group24{score=new F4(r.ReadSingle(),r.ReadSingle(),r.ReadSingle(),r.ReadSingle()),masks=new U4(r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32()),tail=new U4(r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32())};return a;}
 public static Subset24[] Subsets(byte[] bytes){if(bytes.Length%32!=0)throw new IOException("Subset stride");var a=new Subset24[bytes.Length/32];using(var r=new BinaryReader(new MemoryStream(bytes)))for(int i=0;i<a.Length;i++)a[i]=new Subset24{a=new U4(r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32()),b=new U4(r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32())};return a;}
 public static Group24[] InvalidGroups(int n){var a=new Group24[n];for(int i=0;i<n;i++)a[i]=new Group24{score=new F4(3.402823e38f,3.402823e38f,3.402823e38f,3.402823e38f),tail=new U4(UInt32.MaxValue,0,0,0)};return a;}
 public static int ExpectedStride<T>()where T:struct{if(typeof(T)==typeof(F4)||typeof(T)==typeof(U4))return 16;if(typeof(T)==typeof(Subset24))return 32;if(typeof(T)==typeof(Group24))return 48;throw new IOException("Unapproved upload type");}
}
}
