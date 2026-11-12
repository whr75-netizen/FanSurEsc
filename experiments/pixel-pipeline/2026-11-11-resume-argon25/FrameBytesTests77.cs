using System;
using System.IO;
public static class FrameBytesTests77 {
 public static int Main(string[] args){for(int i=0;i<args.Length;i+=2){var bytes=FrameBytes77.Encode(File.ReadAllBytes(args[i]));using(var f=new FileStream(args[i+1],FileMode.CreateNew,FileAccess.Write))f.Write(bytes,0,bytes.Length);}return 0;}
}
