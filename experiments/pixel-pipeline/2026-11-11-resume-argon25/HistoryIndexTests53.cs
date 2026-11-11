using System;using System.Collections.Generic;using System.Security.Cryptography;using System.Text;using UnityEngine;
public static class HistoryIndexTests53 {
 public static void Main(){
  string m=new string('a',64);var uv=new[]{Vector2.zero,Vector2.right,Vector2.up,new Vector2(.5f,.5f),Vector2.one};var tri=new[]{0,1,2,3,2,4};var weld=new[]{0,1,2,0,1};var basePoints=new[]{Vector3.zero,Vector3.right,Vector3.up,Vector3.zero,Vector3.right};var carrier=new CurveCarrier43(m,1,3,tri,weld,uv);
  // Serialize the complete observable result, not only counts or a chosen t.
  var output=new StringBuilder();int queries=0,hidden=0,ambiguous=0;long started=GC.GetAllocatedBytesForCurrentThread();
  for(int transform=0;transform<8;transform++){
   var scope=new CurveHistory45.Scope("123","456",m,carrier.InputKey,(uint)(transform+1));var h=new CurveHistory45(scope,carrier,1024);h.Begin(scope,20,30,"old-source");
   for(int i=0;i<512;i++)h.Observe(2,(float)(i%128)/128,basePoints,true);h.Complete(true,false);
   var current=new Vector3[basePoints.Length];for(int j=0;j<current.Length;j++){var p=basePoints[j];if(transform>=4)p.x=-p.x;for(int a=0;a<transform%4;a++)p=new Vector3(-p.y,p.x,p.z);current[j]=p+new Vector3(.125f,-.25f,.5f);}
   h.Begin(scope,21,31,"current-source");
   for(int i=0;i<257;i++){
    var q=h.Observe(2,(float)i/256,current,i%17!=0);queries++;if(!q.visible)hidden++;if(q.ambiguous)ambiguous++;
    output.Append(q.currentKnown).Append('/').Append(q.visible).Append('/').Append(q.historyKnown).Append('/').Append(q.ambiguous).Append('/').Append(q.ownerKey).Append('/').Append(q.reason).Append('/').Append(q.previousSource).Append('/');
    foreach(var t in q.previousT)output.Append(BitConverter.SingleToInt32Bits(t)).Append(',');
    foreach(var p in q.previousReprojected)output.Append(BitConverter.SingleToInt32Bits(p.x)).Append(',').Append(BitConverter.SingleToInt32Bits(p.y)).Append(',').Append(BitConverter.SingleToInt32Bits(p.z)).Append(';');output.Append('\n');
   }
   h.Complete(true,false);if(h.RetainedSamples!=241)throw new Exception("53 retained sample semantic changed");h.Retire();
  }
  long allocated=GC.GetAllocatedBytesForCurrentThread()-started;string digest;using(var hash=SHA256.Create())digest=BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(output.ToString()))).Replace("-","").ToLowerInvariant();
  Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new{queries,hidden,ambiguous,observableSHA256=digest,managedAllocatedBytes=allocated,allocationIsNotGPUTiming=true,GPUOrUnityCalls=0}));
 }
}
