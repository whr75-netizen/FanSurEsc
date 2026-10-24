using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
public static class FaceRays574
{
 struct V{public double x,y,z;public V(Matrix4x4 m,Vector3 p){x=(double)m.m00*p.x+(double)m.m01*p.y+(double)m.m02*p.z+m.m03;y=(double)m.m10*p.x+(double)m.m11*p.y+(double)m.m12*p.z+m.m13;z=-((double)m.m20*p.x+(double)m.m21*p.y+(double)m.m22*p.z+m.m23);}}
 sealed class Hit{public int sm,tri;public string material;public double z,alpha;public Vector2 uv;public Vector3 world,bary;}
 static string R(double v)=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
 static int Mod(int v,int n){int q=v%n;return q<0?q+n:q;}
 static double Alpha(Texture2D t,byte[] data,Vector2 uv){double x=uv.x*(double)t.width-.5,y=uv.y*(double)t.height-.5;int ix=(int)Math.Floor(x),iy=(int)Math.Floor(y);double fx=x-ix,fy=y-iy;double a=data[Mod(iy,t.height)*t.width+Mod(ix,t.width)],b=data[Mod(iy,t.height)*t.width+Mod(ix+1,t.width)],c=data[Mod(iy+1,t.height)*t.width+Mod(ix,t.width)],d=data[Mod(iy+1,t.height)*t.width+Mod(ix+1,t.width)];return((a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy)/255;}
 static void Append(List<string> row,Hit h){if(h==null){for(int i=0;i<14;i++)row.Add("");return;}row.Add('"'+h.material.Replace("\"","\"\"")+'"');row.Add(h.sm.ToString());row.Add(h.tri.ToString());row.Add(R(h.z));row.Add(R(h.alpha));row.Add(R(h.uv.x));row.Add(R(h.uv.y));row.Add(R(h.bary.x));row.Add(R(h.bary.y));row.Add(R(h.bary.z));row.Add(R(h.world.x));row.Add(R(h.world.y));row.Add(R(h.world.z));row.Add("same_source_ray");}
 public static void Write(string path,HeadLocal367 host,Color[] finalMeta)
 {
  var f=host.head;var mf=f.motion.surface.outputs[1];var mesh=mf.sharedMesh;var local=mesh.vertices;var uv=mesh.uv;var world=new Vector3[local.Length];var points=new V[local.Length];var view=f.motion.camera.worldToCameraMatrix;
  for(int i=0;i<local.Length;i++){world[i]=mf.transform.TransformPoint(local[i]);points[i]=new V(view,world[i]);}
  int firstMaterial=f.motion.surface.outputs[0].sharedMesh.subMeshCount;var indices=new int[mesh.subMeshCount][];var textures=new Texture2D[indices.Length];var alpha=new byte[indices.Length][];var cutoff=new double[indices.Length];var cull=new int[indices.Length];var names=new string[indices.Length];var cache=new Dictionary<Texture2D,byte[]>();
  using(var materials=new StreamWriter(path+"_FACE_MATERIALS.tsv"))
  {
   materials.WriteLine("submesh\tmaterial\tcutoff\tcull\ttexture\tST");
   for(int s=0;s<indices.Length;s++){indices[s]=mesh.GetIndices(s);var m=f.motion.materials[firstMaterial+s];textures[s]=m.mainTexture as Texture2D;if(!textures[s])throw new Exception("574 source face texture missing");if(!cache.TryGetValue(textures[s],out var bytes)){bytes=HeadArea505.SourceAlphaBytes525(textures[s]);cache.Add(textures[s],bytes);}alpha[s]=bytes;cutoff[s]=(int)m.GetFloat("_AlphaMode")==1?m.GetFloat("_Cutoff"):6.103515625e-5;cull[s]=(int)m.GetFloat("_M_CullMode");names[s]=m.name;materials.WriteLine(s+"\t"+m.name+"\t"+R(cutoff[s])+"\t"+cull[s]+"\t"+textures[s].name+"\t"+m.GetVector("_MainTex_ST"));}
  }
  using(var writer=new StreamWriter(path+"_FACE_SAME_RAY.csv"))
  {
   string columns="Material,SM,Tri,CamZ,Alpha,U,V,BaryU,BaryV,BaryW,WorldX,WorldY,WorldZ,Ray";
   writer.WriteLine("headX,headY,mainX,mainY,sourceProjX,sourceProjY,sourceToCentre,hairSM,hairTri,hairU,hairV,hairCamX,hairCamY,hairCamZ,hairPacketDepth,"+"any"+columns.Replace(",",",any")+",skin"+columns.Replace(",",",skin")+",anyFront,skinFront,metaR,metaG,metaB,metaA");
   foreach(var packet in HeadRegion502.Packets)
   {
    var ray=new V(view,packet.world);Hit any=null,skin=null;
    for(int s=0;s<indices.Length;s++)for(int n=0;n<indices[s].Length;n+=3)
    {
     int ia=indices[s][n],ib=indices[s][n+1],ic=indices[s][n+2];var a=points[ia];var b=points[ib];var c=points[ic];double bx=b.x-a.x,by=b.y-a.y,cx=c.x-a.x,cy=c.y-a.y,px=ray.x-a.x,py=ray.y-a.y,det=bx*cy-by*cx;if(Math.Abs(det)<1e-20||cull[s]==2&&det>=0)continue;
     double v=(px*cy-py*cx)/det,w=(bx*py-by*px)/det,u=1-v-w;if(u<-.00001||v<-.00001||w<-.00001)continue;double depth=u*a.z+v*b.z+w*c.z;if(depth<=0)continue;var tex=uv[ia]*(float)u+uv[ib]*(float)v+uv[ic]*(float)w;double opacity=Alpha(textures[s],alpha[s],tex);if(opacity<cutoff[s])continue;
     var hit=new Hit{sm=s,tri=n/3,material=names[s],z=depth,alpha=opacity,uv=tex,bary=new Vector3((float)u,(float)v,(float)w),world=world[ia]*(float)u+world[ib]*(float)v+world[ic]*(float)w};if(any==null||depth<any.z)any=hit;if(names[s].IndexOf("SKIN",StringComparison.OrdinalIgnoreCase)>=0&&(skin==null||depth<skin.z))skin=hit;
    }
    int mx=packet.x+host.offset.x,my=packet.y-host.offset.y;var meta=finalMeta[(271-my)*480+mx];double dx=packet.projected.x-packet.x-.5,dy=packet.projected.y-packet.y-.5;
    var row=new List<string>{packet.x.ToString(),packet.y.ToString(),mx.ToString(),my.ToString(),R(packet.projected.x),R(packet.projected.y),R(Math.Sqrt(dx*dx+dy*dy)),packet.submesh.ToString(),packet.primitive.ToString(),R(packet.uv.x),R(packet.uv.y),R(ray.x),R(ray.y),R(ray.z),R(packet.depth)};Append(row,any);Append(row,skin);row.Add(any!=null&&any.z<ray.z-.0001?"1":"0");row.Add(skin!=null&&skin.z<ray.z-.0001?"1":"0");row.Add(R(meta.r));row.Add(R(meta.g));row.Add(R(meta.b));row.Add(R(meta.a));writer.WriteLine(string.Join(",",row));
   }
  }
 }
}
