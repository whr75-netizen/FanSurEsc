using System;using System.IO;using Unity.AI.Assistant.Agent.Dynamic.Extension.Editor;
public static class PaletteConstraintsTests92 {
 static int[] Ints(string path){var b=File.ReadAllBytes(path);if(b.Length%4!=0)throw new ArgumentException("92 integer byte ABI");var x=new int[b.Length/4];Buffer.BlockCopy(b,0,x,0,b.Length);return x;}
 public static void Main(string[] args){var refs=File.ReadAllBytes(args[0]);var orders=Ints(args[1]);var vectors=Ints(args[2]);double floor=Double.Parse(args[3],System.Globalization.CultureInfo.InvariantCulture);var p=PaletteRuntime89.BuildConstrained92(refs,orders,3,floor,vectors);File.WriteAllBytes(args[4],p.rgb8);Console.WriteLine("nativeConstraints="+p.sourceContrastPairs92+";corrections="+p.contrastCorrections92+";maxCodeError="+p.maxCodeError);}
}
