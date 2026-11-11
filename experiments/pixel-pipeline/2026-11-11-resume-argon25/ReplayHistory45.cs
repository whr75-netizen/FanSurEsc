using System;using System.IO;using System.Linq;using System.Collections.Generic;using UnityEngine;
public static class ReplayHistory45 {
 public static void Main(string[] args){
  var rows=new List<object>();int history=0,ambiguous=0,visible=0,hidden=0;CurveHistory45 sequence=null;
  using(var r=new BinaryReader(File.OpenRead(args[0]))){if(r.ReadString()!="source-history45/v1")throw new Exception("45 ABI");int renderer=r.ReadInt32(),submesh=r.ReadInt32(),nuv=r.ReadInt32();var uv=new Vector2[nuv];for(int i=0;i<nuv;i++)uv[i]=new Vector2(r.ReadSingle(),r.ReadSingle());int count=r.ReadInt32();if(count!=12)throw new Exception("45 actual fixture frames");
   for(int f=0;f<count;f++){
    string id=r.ReadString(),model=r.ReadString(),actor=r.ReadString(),view=r.ReadString();int number=r.ReadInt32();long serial=r.ReadInt64();int n=r.ReadInt32();if(n!=nuv||n>5000)throw new Exception("45 vertex budget");var points=new Vector3[n];for(int i=0;i<n;i++)points[i]=new Vector3(r.ReadSingle(),r.ReadSingle(),r.ReadSingle());int nt=r.ReadInt32();if(nt<3||nt>15000)throw new Exception("45 source indices");var tri=new int[nt];for(int i=0;i<nt;i++)tri[i]=r.ReadInt32();var weld=new int[n];for(int i=0;i<n;i++)weld[i]=r.ReadInt32();var carrier=new CurveCarrier43(model,renderer,submesh,tri,weld,uv);var scope=new CurveHistory45.Scope(actor,view,model,carrier.InputKey,1);if(f%6==0){sequence?.Retire();sequence=new CurveHistory45(scope,carrier,4096);}sequence.Begin(scope,number,serial,id);int samples=r.ReadInt32(),nHistory=0,nVisible=0,nHidden=0;
    for(int i=0;i<samples;i++){int edge=r.ReadInt32();float t=r.ReadSingle();bool shown=r.ReadBoolean();var a=sequence.Observe(edge,t,points,shown);if(!a.currentKnown)throw new Exception("45 actual valid carrier lost");if(!shown){hidden++;nHidden++;if(a.historyKnown)throw new Exception("45 current occlusion ignored");}else{visible++;nVisible++;}if(a.historyKnown){history++;nHistory++;if(a.ambiguous)ambiguous++;foreach(var p in a.previousReprojected)if(!float.IsFinite(p.x)||!float.IsFinite(p.y)||!float.IsFinite(p.z))throw new Exception("45 nonfinite deformation correspondence");}}
    sequence.Complete(true,false);rows.Add(new{frame=number,sourceId=id,visible=nVisible,hidden=nHidden,sourceCorrespondences=nHistory,retainedSamples=sequence.RetainedSamples});
   }sequence.Retire();if(r.BaseStream.Position!=r.BaseStream.Length)throw new Exception("45 trailing fixture");
  }
  Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new{actualSavedFrames=12,visible,hidden,historyCorrespondences=history,equalSourceCorrespondences=ambiguous,screenRGBHistory=false,historyUsedToInventPixels=false,newGPUOrUnityCalls=0,rows}));
 }
}
