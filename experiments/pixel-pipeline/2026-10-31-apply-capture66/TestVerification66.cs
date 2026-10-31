using System;
using System.IO;
using System.Text;
using System.Diagnostics;

class TestVerification66
{
 static string root;static int cases;
 static void Check(bool test,string name){if(!test)throw new Exception(name);}
 static SerializedContent66.Comparison Compare(string before,string after)
 {var p=Path.Combine(root,"small-input.json");File.WriteAllText(p,before,new UTF8Encoding(false));return SerializedContent66.Verify(p,after);}
 static void Test(string name,string a,string b,bool? equal,string status)
 {var r=Compare(a,b);Check(r.Equivalent==equal&&r.Status==status,name+" "+r.Status);Console.WriteLine("PASS "+name);cases++;}
 static int Main(string[] args)
 {
  try
  {
   root=args[0];Directory.CreateDirectory(root);
   Test("unchanged","{\"x\":1}","{\"x\":1}",true,"ExactUTF8");
   Test("changed","{\"x\":1}","{\"x\":2}",false,"SmallSemanticDifferent");
   Test("field_order","{\"a\":1,\"b\":[2,3]}","{\"b\":[2,3],\"a\":1}",true,"SmallSemanticEquivalent");
   Test("whitespace_number_spelling","{\"x\":1.0}"," { \"x\" : 1 } ",true,"SmallSemanticEquivalent");
   Test("unicode_escaped","{\"x\":\"한😀\"}","{\"x\":\"\\ud55c\\ud83d\\ude00\"}",true,"SmallSemanticEquivalent");
   Test("duplicate_member","{\"x\":0,\"x\":1}","{\"x\":1}",null,"UnverifiedInvalidOrUnsupportedJSON");
   Test("precise_integer_change","{\"x\":9007199254740992}","{\"x\":9007199254740993}",null,"UnverifiedNumericPrecision");
   Test("invalid","{\"x\":}","{}",null,"UnverifiedInvalidOrUnsupportedJSON");
   Test("array_order","[1,2,3]","[3,2,1]",false,"SmallSemanticDifferent");
   // Encoder chunk boundary bisects a UTF16 surrogate pair.
   string unicode="\""+new string('a',8190)+"😀\"";Test("utf8_chunk_boundary",unicode,unicode,true,"ExactUTF8");
   foreach(int n in new[]{1024,2048,4096,8192})
   {
    string s="["+new string(' ',n)+"1]";var w=Stopwatch.StartNew();var r=Compare(s,s);w.Stop();
    Check(r.Equivalent==true&&r.HashInputBytes==Encoding.UTF8.GetByteCount(s)*2L,"linear bytes");
    Console.WriteLine("SCALE chars="+s.Length+" hashedBytes="+r.HashInputBytes+" ms="+w.Elapsed.TotalMilliseconds.ToString("F3",System.Globalization.CultureInfo.InvariantCulture));
   }
   string large="["+string.Join(",",new string('1',40000).ToCharArray())+"]";
   Test("large_numeric_exact",large,large,true,"ExactUTF8");
   Test("large_numeric_changed_no_tree",large,large.Replace("1]","2]"),null,"UnverifiedRepresentationChange");
   string bigA="{\"a\":"+large+",\"b\":0}",bigB="{\"b\":0,\"a\":"+large+"}";
   Test("large_field_order_explicit_unverified",bigA,bigB,null,"UnverifiedRepresentationChange");
   try{Json58.Parse(large);throw new Exception("missing parse budget");}catch(ArgumentException){}
   Console.WriteLine("PASS direct_large_parser_budget");cases++;
   if(args.Length>1)
   {
    // Single real input. No JSON tree; required current string is the only large input.
    string input=File.ReadAllText(args[1],new UTF8Encoding(false,true));
    var watch=Stopwatch.StartNew();var r=SerializedContent66.Verify(args[1],input);watch.Stop();
    Check(r.Status=="ExactUTF8"&&r.Equivalent==true,"actual mesh exact hash");
    Console.WriteLine("ACTUAL bytes="+r.BeforeBytes+" hashedBytes="+r.HashInputBytes+" ms="+watch.Elapsed.TotalMilliseconds.ToString("F3",System.Globalization.CultureInfo.InvariantCulture)+" extraHashBufferBytes="+(SerializedContent66.ByteChunk*2+SerializedContent66.CharChunk*2));
   }
   Console.WriteLine("CASES "+cases);return 0;
  }
  catch(Exception e){Console.Error.WriteLine(e);return 1;}
 }
}
