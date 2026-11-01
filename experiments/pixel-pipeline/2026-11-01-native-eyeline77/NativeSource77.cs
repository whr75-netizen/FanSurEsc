using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

// Original source topology, not screen RGB or per-frame display-cell identity.
public static class NativeSource77
{
 public sealed class Component {public int label,eyeId,triangles;public bool upper;public Vector3 meanRest;public float normalizedV;}
 public static bool Build(EyeFeature348 e,out Vector4[] data,out Component[] descriptors,out string reason)
 {
  data=null;descriptors=null;reason=null;
  if(!e||e.modelEyes==null||e.modelEyes.Length!=2||e.axesY==null){reason="Current source eye binding unavailable";return false;}
  var mesh=e.full.motion.surface.source[1].sharedMesh;var verts=mesh.vertices;var rest=verts.Select(p=>e.sourceToRestHead.MultiplyPoint3x4(p)).ToArray();var all=new List<Vector4>();
  for(int sm=0;sm<7;sm++){if(all.Count!=(int)e.triangleRanges[sm].x){reason="Source triangle layout mismatch";return false;}foreach(int i in mesh.GetIndices(sm))all.Add(rest[i]);}
  if(all.Count!=e.restTriangles.count){reason="Rest buffer count mismatch";return false;}
  var native=mesh.GetIndices(6);int n=native.Length/3;var parent=Enumerable.Range(0,n).ToArray();
  int Find(int x){while(parent[x]!=x){parent[x]=parent[parent[x]];x=parent[x];}return x;}
  var seen=new Dictionary<int,int>();for(int t=0;t<n;t++)for(int j=0;j<3;j++){int index=native[t*3+j];if(seen.TryGetValue(index,out int other))parent[Find(t)]=Find(other);else seen[index]=t;}
  var groups=Enumerable.Range(0,n).GroupBy(Find).Select(g=>g.OrderBy(x=>x).ToArray()).OrderBy(g=>g[0]).ToArray();var parts=new List<Component>();int label=1,offset=(int)e.triangleRanges[6].x;
  foreach(var group in groups)
  {
   Vector3 sum=Vector3.zero;float total=0;foreach(int t in group){var a=rest[native[t*3]];var b=rest[native[t*3+1]];var c=rest[native[t*3+2]];float area=Vector3.Cross(b-a,c-a).magnitude*.5f;sum+=(a+b+c)*(area/3);total+=area;}
   if(total<=0){reason="Degenerate native component";return false;}var mean=sum/total;float d0=(mean-e.modelEyes[0].centre).sqrMagnitude,d1=(mean-e.modelEyes[1].centre).sqrMagnitude;if(d0==d1){reason="Ambiguous source eye ownership";return false;}int eye=d0<d1?0:1;float vertical=-Vector3.Dot(mean-e.modelEyes[eye].centre,e.modelEyes[eye].axisY)/e.axesY[eye].w;if(vertical==0){reason="Native component crosses an unresolved centre";return false;}
   bool upper=vertical<0;foreach(int t in group)for(int j=0;j<3;j++){var v=all[offset+3*t+j];v.w=upper?label:-label;all[offset+3*t+j]=v;}
   parts.Add(new Component{label=label++,eyeId=e.modelEyes[eye].stableId,upper=upper,meanRest=mean,normalizedV=vertical,triangles=group.Length});
  }
  foreach(var eye in e.modelEyes)if(parts.Count(p=>p.eyeId==eye.stableId&&p.upper)!=1){reason="One connected upper source per eye is not established; keep76";return false;}
  data=all.ToArray();descriptors=parts.ToArray();return true;
 }
}
