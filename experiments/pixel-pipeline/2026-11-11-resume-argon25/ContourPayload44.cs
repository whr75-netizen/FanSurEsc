using System;using UnityEngine;
public static class ContourPayload44 {
 public sealed class Channels {public Vector3[] a,b;public Vector4[] uv;}
 public static Channels Build(Unity.AI.Assistant.Agent.Dynamic.Extension.Editor.Contour40.Result source,Vector2[] meshUV){
  int n=source.vertices.Length;if(n%2!=0||source.provenance.Length!=n||source.sourceVertexIndices.Length!=n)throw new ArgumentException("44 paired source line ABI");var r=new Channels{a=new Vector3[n],b=new Vector3[n],uv=new Vector4[n]};
  for(int i=0;i<n;i+=2){int a=source.provenance[i].y==0?i:i+1,b=a==i?i+1:i;if(source.provenance[a].y!=0||source.provenance[b].y!=1||source.provenance[a].x!=source.provenance[b].x)throw new ArgumentException("44 canonical source endpoints required");var ua=meshUV[source.sourceVertexIndices[a]];var ub=meshUV[source.sourceVertexIndices[b]];for(int j=i;j<i+2;j++){r.a[j]=source.vertices[a];r.b[j]=source.vertices[b];r.uv[j]=new Vector4(ua.x,ua.y,ub.x,ub.y);}}
  return r;
 }
}
