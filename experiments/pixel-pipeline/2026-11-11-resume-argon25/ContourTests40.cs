using System;using System.Linq;using System.Collections.Generic;using UnityEngine;using Unity.AI.Assistant.Agent.Dynamic.Extension.Editor;
public static class ContourTests40 {
 static List<string> passed=new List<string>();static void Check(string n,bool b){if(!b)throw new Exception(n);passed.Add(n);}
 public static void Main(){
  var v=new[]{new Vector3(0,0,1),new Vector3(-1,-1,0),new Vector3(1,-1,0),new Vector3(0,1,0)};var t=new[]{0,2,1,0,3,2,0,1,3,1,2,3};var weld=new[]{0,1,2,3};Func<Vector3,Vector2> project=p=>new Vector2(p.x,p.y);var identity=Matrix4x4.identity;var r=Contour40.Build(v,t,weld,identity,project);Check("closed tetrahedron source apparent contour",r.indices.Length==6&&r.openEdges==0&&r.nonmanifoldEdges==0);
  var ids=r.provenance.Where((x,i)=>i%2==0).Select(x=>x.x).ToArray();
  Check("emitted endpoint source indices retain exact source positions",r.sourceVertexIndices.Length==r.vertices.Length&&r.sourceVertexIndices.Select((x,i)=>v[x].Equals(r.vertices[i])).All(x=>x));
  Check("degree2 source joints have continuous directed endpoints",r.closedChains==1&&r.openChains==0&&r.vertices[1].Equals(r.vertices[2])&&r.vertices[3].Equals(r.vertices[4])&&r.vertices[5].Equals(r.vertices[0]));
  for(int flip=0;flip<2;flip++)for(int k=0;k<4;k++){int kk=k,ff=flip;Func<Vector3,Vector2> f=p=>{float x=ff==0?p.x:-p.x,y=p.y;for(int j=0;j<kk;j++){float z=x;x=-y;y=z;}return new Vector2(x,y);};var a=Contour40.Build(v,t,weld,identity,f);Check("D4 source edge identity "+flip+"/"+k,a.provenance.Where((x,i)=>i%2==0).Select(x=>x.x).SequenceEqual(ids));}
  var shift=identity;shift.m03=.125f;shift.m13=.375f;var moved=Contour40.Build(v,t,weld,shift,project);Check("subpixel translation does not change source contour edges",moved.provenance.Select(x=>x.x).SequenceEqual(r.provenance.Select(x=>x.x)));
  var open=Contour40.Build(v,new[]{0,1,2},weld,identity,project);Check("unpaired source boundaries are reported not closed by invention",open.indices.Length==0&&open.openEdges==3);
  var split=v.Concat(new[]{v[1]}).ToArray();var ws=new[]{0,1,2,3,1};var ts=(int[])t.Clone();ts[2]=4;var seam=Contour40.Build(split,ts,ws,identity,project);Check("registered UV seam has same physical contour",seam.indices.Length==r.indices.Length&&seam.openEdges==0);
  split[4].x+=.00001f;try{Contour40.Build(split,ts,ws,identity,project);throw new Exception("stale weld accepted");}catch(InvalidOperationException){passed.Add("evaluated weld divergence is rejected");}
  var bad=(Vector3[])v.Clone();bad[0].x=float.NaN;try{Contour40.Build(bad,t,weld,identity,project);throw new Exception("nonfinite accepted");}catch(ArgumentException){passed.Add("nonfinite projection input rejected");}
  var nm=Contour40.Build(v,t.Concat(new[]{0,2,1}).ToArray(),weld,identity,project);Check("nonmanifold source edges reported",nm.nonmanifoldEdges>0);
  Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new{checks=passed.Count,passed,engineObjectsCreated=0,GPUCalls=0}));
 }
}
