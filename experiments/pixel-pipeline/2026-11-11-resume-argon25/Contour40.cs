// Source geometry contour only. Native MToon inverted-hull strokes and source
// pigment are separate producers. No screen-colour history or RGB averaging.
using System;using System.Collections.Generic;using System.Linq;using UnityEngine;
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
public static class Contour40 {
 public sealed class Result {public Vector3[] vertices;public Vector2[] provenance;public int[] indices,sourceVertexIndices;public int openEdges,nonmanifoldEdges,degenerateTriangles,sourceEdges,closedChains,openChains,branchVertices;}
 sealed class Edge {public int a,b;public List<int> triangles=new List<int>();}
 sealed class Segment {public int id;public Edge edge;}
 public static Result Build(Vector3[] local,int[] tri,int[] weld,Matrix4x4 transform,Func<Vector3,Vector2> project){
  if(local==null||tri==null||weld==null||local.Length!=weld.Length||tri.Length%3!=0||project==null)throw new ArgumentException("40 source topology ABI");
  var world=local.Select(transform.MultiplyPoint3x4).ToArray();var projected=world.Select(project).ToArray();var representatives=new Dictionary<int,Vector3>();
  for(int i=0;i<weld.Length;i++){if(!float.IsFinite(world[i].x)||!float.IsFinite(world[i].y)||!float.IsFinite(world[i].z)||!float.IsFinite(projected[i].x)||!float.IsFinite(projected[i].y))throw new ArgumentException("40 finite evaluated source required");if(representatives.TryGetValue(weld[i],out var old)){if(!old.Equals(world[i]))throw new InvalidOperationException("40 registered equivalent source vertices deformed differently");}else representatives.Add(weld[i],world[i]);}
  var sign=new int[tri.Length/3];var edges=new Dictionary<ulong,Edge>();var r=new Result();
  for(int t=0;t<sign.Length;t++){
   int a=tri[t*3],b=tri[t*3+1],c=tri[t*3+2];if(a<0||b<0||c<0||a>=local.Length||b>=local.Length||c>=local.Length)throw new ArgumentException("40 source index out of range");
   var x=projected[a];var y=projected[b];var z=projected[c];double det=((double)y.x-x.x)*((double)z.y-x.y)-((double)y.y-x.y)*((double)z.x-x.x);sign[t]=Math.Sign(det);if(sign[t]==0)r.degenerateTriangles++;
   foreach(var p in new[]{new[]{a,b},new[]{b,c},new[]{c,a}}){uint lo=(uint)Math.Min(weld[p[0]],weld[p[1]]),hi=(uint)Math.Max(weld[p[0]],weld[p[1]]);if(lo==hi)continue;ulong key=((ulong)lo<<32)|hi;if(!edges.TryGetValue(key,out var e)){e=new Edge{a=p[0],b=p[1]};edges.Add(key,e);}e.triangles.Add(t);}
  }
  var v=new List<Vector3>();var uv=new List<Vector2>();var indices=new List<int>();var sourceVertices=new List<int>();int id=0;var segments=new List<Segment>();
  foreach(var pair in edges.OrderBy(p=>p.Key)){id++;var e=pair.Value;if(e.triangles.Count==1){r.openEdges++;continue;}if(e.triangles.Count!=2){r.nonmanifoldEdges++;continue;}int a=sign[e.triangles[0]],b=sign[e.triangles[1]];if(a!=b)segments.Add(new Segment{id=id,edge=e});}
  var nodes=new Dictionary<int,List<int>>();for(int i=0;i<segments.Count;i++){var e=segments[i].edge;foreach(int node in new[]{weld[e.a],weld[e.b]}){if(!nodes.TryGetValue(node,out var list)){list=new List<int>();nodes.Add(node,list);}list.Add(i);}}
  r.branchVertices=nodes.Count(p=>p.Value.Count>2);var used=new bool[segments.Count];
  // D3D aliased lines use diamond exit. Orient each actual source chain
  // coherently so both incident segments never terminate at a degree2 joint.
  // This changes neither the source edge set nor depth/occlusion testing.
  void Walk(int first,int initial){int current=first,node=initial;while(!used[current]){used[current]=true;var s=segments[current];var e=s.edge;int a=weld[e.a]==node?e.a:e.b,b=a==e.a?e.b:e.a;int start=v.Count;v.Add(world[a]);v.Add(world[b]);sourceVertices.Add(a);sourceVertices.Add(b);uv.Add(new Vector2(s.id,weld[a]<weld[b]?0:1));uv.Add(new Vector2(s.id,weld[b]<weld[a]?0:1));indices.Add(start);indices.Add(start+1);node=weld[b];if(nodes[node].Count!=2)break;int next=nodes[node][0]==current?nodes[node][1]:nodes[node][0];if(used[next])break;current=next;}if(node==initial)r.closedChains++;else r.openChains++;}
  foreach(var p in nodes.Where(p=>p.Value.Count!=2).OrderBy(p=>p.Key))foreach(int i in p.Value)if(!used[i])Walk(i,p.Key);
  for(int i=0;i<segments.Count;i++)if(!used[i])Walk(i,Math.Min(weld[segments[i].edge.a],weld[segments[i].edge.b]));
  r.vertices=v.ToArray();r.provenance=uv.ToArray();r.indices=indices.ToArray();r.sourceVertexIndices=sourceVertices.ToArray();r.sourceEdges=edges.Count;return r;
 }
}
}
