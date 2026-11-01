using System;
using System.IO;
using System.Text;
public static class CreateOnly73
{
 public static void Text(string path,string text)
 {using(var f=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read))using(var w=new StreamWriter(f,new UTF8Encoding(false))){w.Write(text);w.Flush();f.Flush(true);}}
}
