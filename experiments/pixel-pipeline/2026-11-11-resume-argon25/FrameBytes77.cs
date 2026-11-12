// Small exact-byte record format; no extra assembly, Unity state or GPU use.
// Header: R77F / uint32 mode(0 raw,1 RLE16) / uint32 raw length, little endian.
// RLE token: high bit = repeated16-byte pixel; other31 bits = positive count.
// Literal token's payload is count*16 bytes. Raw fallback never exceeds raw+12.
public static class FrameBytes77 {
 public static byte[] Encode(byte[] bytes){
  if(bytes==null||bytes.Length==0||bytes.Length>262144||bytes.Length%16!=0)throw new System.ArgumentException("77 bounded RGBAFloat32 bytes");
  int n=bytes.Length/16;bool Same(int a,int b)=>System.BitConverter.ToInt64(bytes,16*a)==System.BitConverter.ToInt64(bytes,16*b)&&System.BitConverter.ToInt64(bytes,16*a+8)==System.BitConverter.ToInt64(bytes,16*b+8);
  byte[] payload;using(var memory=new System.IO.MemoryStream())using(var w=new System.IO.BinaryWriter(memory)){
   int i=0;while(i<n){int run=1;while(i+run<n&&Same(i,i+run))run++;if(run>=2){w.Write(0x80000000u|(uint)run);w.Write(bytes,i*16,16);i+=run;}else{int start=i++;while(i<n&&!(i+1<n&&Same(i,i+1)))i++;w.Write((uint)(i-start));w.Write(bytes,start*16,(i-start)*16);}}payload=memory.ToArray();
  }
  using(var output=new System.IO.MemoryStream())using(var w=new System.IO.BinaryWriter(output)){w.Write(new byte[]{82,55,55,70});w.Write(payload.Length<bytes.Length?1u:0u);w.Write((uint)bytes.Length);w.Write(payload.Length<bytes.Length?payload:bytes);return output.ToArray();}
 }
}
