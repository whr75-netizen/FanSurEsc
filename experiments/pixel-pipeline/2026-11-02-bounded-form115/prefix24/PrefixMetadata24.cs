// Explicit mapping for the two nested-array metadata shapes. No reflection or Unity.
// Json58 is the existing bounded linear66 reader, not the historical58 parser.
using System;
using System.Linq;
using System.Text;
using System.IO;
namespace Prefix24 {
 public static class PrefixMetadata24 {
  static Json58 Need(Json58 j,string key){var x=j[key];if(x==null)throw new IOException("Missing metadata field "+key);return x;}
  static Blob24 Blob(Json58 j){return new Blob24{Name=(string)Need(j,"Name"),File=(string)Need(j,"File"),Stage=(int)Need(j,"Stage"),Bytes=(int)Need(j,"Bytes"),Sha256=(string)Need(j,"Sha256")};}
  static Obj58 BlobJson(Blob24 b){return new Obj58{["Name"]=b.Name,["File"]=b.File,["Stage"]=b.Stage,["Bytes"]=b.Bytes,["Sha256"]=b.Sha256};}
  public static object Decode(byte[] bytes,Type type){
   if(bytes.Length>65536)throw new IOException("Small metadata budget");var j=Json58.Parse(Encoding.UTF8.GetString(bytes));
   if(type==typeof(Case24))return new Case24{Schema=(string)Need(j,"Schema"),SourceId=(string)Need(j,"SourceId"),RunId=(string)Need(j,"RunId"),ShaderAssetPath=(string)Need(j,"ShaderAssetPath"),ShaderSha256=(string)Need(j,"ShaderSha256"),ShaderGuid=(string)Need(j,"ShaderGuid"),SourceFrame=(int)Need(j,"SourceFrame"),SourceSerial=(int)Need(j,"SourceSerial"),Width=(int)Need(j,"Width"),Height=(int)Need(j,"Height"),Owner=(int)Need(j,"Owner"),InputFiles=Need(j,"InputFiles").Select(Blob).ToArray(),Globals=Need(j,"Globals").Select(g=>new Global24{Name=(string)Need(g,"Name"),Type=(string)Need(g,"Type")}).ToArray()};
   if(type==typeof(Receipt24))return new Receipt24{Schema=(string)Need(j,"Schema"),ExecutionKind=(string)Need(j,"ExecutionKind"),RunId=(string)Need(j,"RunId"),CaseSha256=(string)Need(j,"CaseSha256"),SourceId=(string)Need(j,"SourceId"),ShaderSha256=(string)Need(j,"ShaderSha256"),Stage=(int)Need(j,"Stage"),DispatchCalls=(int)Need(j,"DispatchCalls"),Success=(bool)Need(j,"Success"),StateEqual=(bool)Need(j,"StateEqual"),ResourcesReleased=(bool)Need(j,"ResourcesReleased"),BeforeStateSha256=(string)Need(j,"BeforeStateSha256"),AfterStateSha256=(string)Need(j,"AfterStateSha256"),Error=(string)j["Error"],Outputs=Need(j,"Outputs").Select(Blob).ToArray()};
   throw new IOException("Unapproved nested metadata type");
  }
  public static byte[] ReceiptBytes(Receipt24 r){return Encoding.UTF8.GetBytes(new Obj58{["Schema"]=r.Schema,["ExecutionKind"]=r.ExecutionKind,["RunId"]=r.RunId,["CaseSha256"]=r.CaseSha256,["SourceId"]=r.SourceId,["ShaderSha256"]=r.ShaderSha256,["Stage"]=r.Stage,["DispatchCalls"]=r.DispatchCalls,["Success"]=r.Success,["StateEqual"]=r.StateEqual,["ResourcesReleased"]=r.ResourcesReleased,["BeforeStateSha256"]=r.BeforeStateSha256,["AfterStateSha256"]=r.AfterStateSha256,["Error"]=r.Error,["Outputs"]=r.Outputs==null?null:new Arr58(r.Outputs.Select(BlobJson))}.ToString());}
 }
}
