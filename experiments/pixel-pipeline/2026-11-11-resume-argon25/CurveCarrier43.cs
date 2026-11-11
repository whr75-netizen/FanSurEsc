// SourceCurve is a distinct owner kind. Its edge ID is never a native primitive ID.
// key is immutable model-feature identity only, NOT an actor/view history key.
// A history consumer must additionally scope it to the live feature owner and view.
using System;using System.Collections.Generic;using System.Linq;using System.Security.Cryptography;using System.IO;using UnityEngine;
public sealed class CurveCarrier43 {
 public sealed class Sample {public string key;public bool known,uniqueUV;public string reason;public int[] triangles;public Vector2[] uv;public Vector3 world;public float t;}
 sealed class Incident {public int triangle,a,b;}
 sealed class Edge {public int lo,hi;public List<Incident> incidents=new List<Incident>();}
 readonly string model;readonly int renderer,submesh;readonly Vector2[] uv;readonly Edge[] edges;readonly int[] weld;readonly string inputKey;
 public string InputKey=>inputKey;public int EdgeCount=>edges.Length;
 static string Hash(int[] tri,int[] weld,Vector2[] uv){using(var bytes=new MemoryStream()){using(var w=new BinaryWriter(bytes,System.Text.Encoding.UTF8,true)){w.Write(tri.Length);foreach(int x in tri)w.Write(x);w.Write(weld.Length);foreach(int x in weld)w.Write(x);w.Write(uv.Length);foreach(var p in uv){if(!float.IsFinite(p.x)||!float.IsFinite(p.y))throw new ArgumentException("43 nonfinite UV");w.Write(p.x);w.Write(p.y);}}using(var hash=SHA256.Create())return BitConverter.ToString(hash.ComputeHash(bytes.ToArray())).Replace("-","").ToLowerInvariant();}}
 public CurveCarrier43(string modelSHA,int renderer,int submesh,int[] tri,int[] sourceWeld,Vector2[] sourceUV){
  if(String.IsNullOrEmpty(modelSHA)||modelSHA.Length!=64||renderer<0||submesh<0||tri==null||tri.Length%3!=0||sourceWeld==null||sourceUV==null||sourceWeld.Length!=sourceUV.Length||sourceWeld.Any(x=>x<0)||tri.Any(x=>x<0||x>=sourceUV.Length))throw new ArgumentException("43 registered source ABI");
  model=modelSHA;this.renderer=renderer;this.submesh=submesh;uv=(Vector2[])sourceUV.Clone();weld=(int[])sourceWeld.Clone();inputKey=Hash(tri,weld,uv);var map=new Dictionary<ulong,Edge>();
  for(int t=0;t<tri.Length/3;t++)for(int k=0;k<3;k++){int a=tri[3*t+k],b=tri[3*t+(k+1)%3],lo=Math.Min(weld[a],weld[b]),hi=Math.Max(weld[a],weld[b]);if(lo==hi)continue;ulong key=((ulong)(uint)lo<<32)|(uint)hi;if(!map.TryGetValue(key,out var e)){e=new Edge{lo=lo,hi=hi};map.Add(key,e);}e.incidents.Add(new Incident{triangle=t,a=weld[a]==lo?a:b,b=weld[b]==hi?b:a});}
  edges=map.OrderBy(p=>p.Key).Select(p=>p.Value).ToArray();
 }
 public void Require(string modelSHA,int[] tri,int[] sourceWeld,Vector2[] sourceUV){if(modelSHA!=model||Hash(tri,sourceWeld,sourceUV)!=inputKey)throw new InvalidOperationException("43 model/topology/weld/UV cache invalidated");}
 public Sample At(string currentModelSHA,int edgeId,float t,Vector3[] evaluatedWorld){
  if(currentModelSHA!=model)return new Sample{known=false,reason="current model changed; register a new source cache"};
  if(edgeId<1||edgeId>edges.Length||!float.IsFinite(t)||t<0||t>1||evaluatedWorld==null||evaluatedWorld.Length!=uv.Length)return new Sample{known=false,reason="invalid edge/t/current vertices"};
  var e=edges[edgeId-1];var key=model+"/renderer"+renderer+"/submesh"+submesh+"/edge"+e.lo+":"+e.hi;
  if(e.incidents.Count!=2)return new Sample{known=false,key=key,reason="open/nonmanifold carrier is not an inferred two-sided surface"};
  var a=e.incidents[0];var b=e.incidents[1];
  if(!evaluatedWorld[a.a].Equals(evaluatedWorld[b.a])||!evaluatedWorld[a.b].Equals(evaluatedWorld[b.b]))return new Sample{known=false,key=key,reason="registered weld deformed inconsistently"};
  var p=Vector3.LerpUnclamped(evaluatedWorld[a.a],evaluatedWorld[a.b],t);if(!float.IsFinite(p.x)||!float.IsFinite(p.y)||!float.IsFinite(p.z))return new Sample{known=false,key=key,reason="nonfinite current point"};
  var u=new[]{Vector2.LerpUnclamped(uv[a.a],uv[a.b],t),Vector2.LerpUnclamped(uv[b.a],uv[b.b],t)};
  return new Sample{known=true,key=key,triangles=new[]{a.triangle,b.triangle},uv=u,uniqueUV=u[0].Equals(u[1]),world=p,t=t};
 }
 public Sample Nearest(string currentModelSHA,int edgeId,Vector3[] evaluatedWorld,Vector2 pixel,Func<Vector3,Vector2> project){
  if(currentModelSHA!=model||edgeId<1||edgeId>edges.Length||evaluatedWorld==null||evaluatedWorld.Length!=uv.Length||project==null)return new Sample{known=false,reason="unregistered nearest-source input"};
  var e=edges[edgeId-1];if(e.incidents.Count!=2)return new Sample{known=false,reason="unpaired source edge"};var pair=e.incidents[0];var a=project(evaluatedWorld[pair.a]);var b=project(evaluatedWorld[pair.b]);double dx=(double)b.x-a.x,dy=(double)b.y-a.y,denom=dx*dx+dy*dy;if(!Double.IsFinite(denom)||denom==0||!float.IsFinite(pixel.x)||!float.IsFinite(pixel.y))return new Sample{known=false,reason="degenerate/nonfinite projected source edge"};
  double t=(((double)pixel.x-a.x)*dx+((double)pixel.y-a.y)*dy)/denom;return At(currentModelSHA,edgeId,(float)Math.Max(0,Math.Min(1,t)),evaluatedWorld);
 }
}
