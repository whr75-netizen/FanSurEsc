using System;using System.IO;using System.Linq;using System.Collections.Generic;using UnityEngine;
public static class ReplayCarrier43 {
 public static void Main(string[] args){
  var rows=new List<object>();int unknown=0,seams=0,total=0;float maxDepthResidual=0;CurveCarrier43 cache=null;
  using(var r=new BinaryReader(File.OpenRead(args[0]))){if(r.ReadString()!="curve-carrier43/v1")throw new Exception("43 ABI");int renderer=r.ReadInt32(),submesh=r.ReadInt32(),nu=r.ReadInt32();if(nu<1||nu>5000)throw new Exception("43 UV budget");var uv=new Vector2[nu];for(int i=0;i<nu;i++)uv[i]=new Vector2(r.ReadSingle(),r.ReadSingle());int frames=r.ReadInt32();if(frames!=12)throw new Exception("43 actual packet count");
   for(int frame=0;frame<frames;frame++){
    string id=r.ReadString(),model=r.ReadString();int number=r.ReadInt32(),n=r.ReadInt32();if(n!=nu)throw new Exception("43 actual vertex registration");var world=new Vector3[n];for(int i=0;i<n;i++)world[i]=new Vector3(r.ReadSingle(),r.ReadSingle(),r.ReadSingle());int count=r.ReadInt32();if(count<3||count>15000)throw new Exception("43 source triangle budget");var tri=new int[count];for(int i=0;i<count;i++)tri[i]=r.ReadInt32();var weld=new int[n];for(int i=0;i<n;i++)weld[i]=r.ReadInt32();var view=new Matrix4x4();for(int i=0;i<16;i++)view[i]=r.ReadSingle();if(cache==null)cache=new CurveCarrier43(model,renderer,submesh,tri,weld,uv);cache.Require(model,tri,weld,uv);int samples=r.ReadInt32();if(samples<0||samples>1024)throw new Exception("43 source sample budget");int known=0,ambiguousUV=0;var keys=new HashSet<string>();
    for(int i=0;i<samples;i++){int edge=r.ReadInt32();float t=r.ReadSingle(),depth=r.ReadSingle();var sample=cache.At(model,edge,t,world);total++;if(!sample.known){unknown++;continue;}known++;keys.Add(sample.key);if(!sample.uniqueUV){seams++;ambiguousUV++;}float d=-view.MultiplyPoint3x4(sample.world).z;maxDepthResidual=Math.Max(maxDepthResidual,Math.Abs(d-depth));}
    rows.Add(new{frame=number,sourceId=id,knownSamples=known,sourceSamples=samples,twoUVCarriersRetained=ambiguousUV,distinctSourceKeys=keys.Count});
   }
   if(r.BaseStream.Position!=r.BaseStream.Length)throw new Exception("43 trailing fixture data");
  }
  Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new{actualSavedFrames=12,sourceSamples=total,unknownSamples=unknown,UVSeamSamples=seams,maxDepthResidual,cacheInputKey=cache.InputKey,sourceEdges=cache.EdgeCount,unambiguousPrimitiveChosen=false,newGPUOrUnityCalls=0,rows}));
 }
}
