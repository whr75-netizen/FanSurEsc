// Offline66 candidate: no Unity/API/thread/process/GC actions.
using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

public static class SerializedContent66
{
 public const int SmallSemanticBudgetBytes=65536;
 public const int CharChunk=8192,ByteChunk=32768;
 public sealed class Comparison
 {
  public string Status,BeforeSHA256,AfterSHA256,Reason;
  public long BeforeBytes,AfterBytes,HashInputBytes;
  public bool? Equivalent;
 }
 static string Finish(SHA256 h)
 {
  h.TransformFinalBlock(new byte[0],0,0);
  return BitConverter.ToString(h.Hash).Replace("-","").ToLowerInvariant();
 }
 static string HashFile(string path,out long length)
 {
  length=0;
  using(var h=SHA256.Create())using(var f=File.OpenRead(path))
  {
   var buffer=new byte[ByteChunk];int n;
   while((n=f.Read(buffer,0,buffer.Length))>0){h.TransformBlock(buffer,0,n,buffer,0);length+=n;}
   return Finish(h);
  }
 }
 static string HashText(string text,out long length)
 {
  length=0;var chars=new char[CharChunk];var bytes=new byte[ByteChunk];
  var encoder=new UTF8Encoding(false,true).GetEncoder();
  using(var h=SHA256.Create())
  {
   int position=0;bool completed=false;
   do
   {
    int count=Math.Min(chars.Length,text.Length-position);
    text.CopyTo(position,chars,0,count);
    int charsUsed,bytesUsed;
    encoder.Convert(chars,0,count,bytes,0,bytes.Length,position+count==text.Length,out charsUsed,out bytesUsed,out completed);
    if(charsUsed==0&&bytesUsed==0&&!completed)throw new InvalidOperationException("UTF8 encoder made no progress");
    position+=charsUsed;
    if(bytesUsed>0){h.TransformBlock(bytes,0,bytesUsed,bytes,0);length+=bytesUsed;}
   }while(position<text.Length||!completed);
   return Finish(h);
  }
 }
 static bool RequiresExactNumericReview(string text)
 {
  int i=0;
  while(i<text.Length)
  {
   if(text[i]=='"')
   {i++;while(i<text.Length){char c=text[i++];if(c=='\\'){if(i<text.Length)i++;}else if(c=='"')break;}continue;}
   char first=text[i];
   if(first=='-'||(first>='0'&&first<='9'))
   {
    int j=i;if(text[j]=='-')j++;int significant=0;bool started=false;
    while(j<text.Length)
    {
     char c=text[j];if(c=='.'){j++;continue;}
     if(c<'0'||c>'9')break;if(c!='0')started=true;if(started)significant++;j++;
    }
    if(significant>15)return true;
    if(j<text.Length&&(text[j]=='e'||text[j]=='E')){j++;if(j<text.Length&&(text[j]=='+'||text[j]=='-'))j++;while(j<text.Length&&text[j]>='0'&&text[j]<='9')j++;}
    i=Math.Max(i+1,j);continue;
   }
   i++;
  }
  return false;
 }
 public static Comparison Verify(string beforePath,string currentSerialized)
 {
  if(currentSerialized==null)throw new ArgumentNullException("currentSerialized");
  var r=new Comparison();long before,after;
  r.BeforeSHA256=HashFile(beforePath,out before);r.AfterSHA256=HashText(currentSerialized,out after);
  r.BeforeBytes=before;r.AfterBytes=after;r.HashInputBytes=before+after;
  if(before==after&&r.BeforeSHA256==r.AfterSHA256)
  {r.Status="ExactUTF8";r.Equivalent=true;r.Reason="Same serialized UTF8 fingerprint; no JSON parse/re-serialization.";return r;}
  if(before>SmallSemanticBudgetBytes||after>SmallSemanticBudgetBytes)
  {r.Status="UnverifiedRepresentationChange";r.Equivalent=null;r.Reason="Large nonidentical input exceeds bounded semantic fallback; not declared changed or equivalent.";return r;}
  string previous=File.ReadAllText(beforePath,new UTF8Encoding(false,true));
  if(RequiresExactNumericReview(previous)||RequiresExactNumericReview(currentSerialized))
  {r.Status="UnverifiedNumericPrecision";r.Equivalent=null;r.Reason="No double-rounding equivalence for >15 significant digits.";return r;}
  try
  {
   r.Equivalent=Json58.DeepEquals(Json58.Parse(previous),Json58.Parse(currentSerialized));
   r.Status=r.Equivalent.Value?"SmallSemanticEquivalent":"SmallSemanticDifferent";
   r.Reason="Fallback <=64KiB; no suffix copying. High-precision numbers/duplicate keys are not accepted as equivalent.";
  }
  catch(Exception e)
  {
   if(!(e is ArgumentException)&&!(e is FormatException)&&!(e is OverflowException)&&!(e is IndexOutOfRangeException))throw;
   r.Status="UnverifiedInvalidOrUnsupportedJSON";r.Equivalent=null;r.Reason=e.GetType().Name+": "+e.Message;
  }
  return r;
 }
}
