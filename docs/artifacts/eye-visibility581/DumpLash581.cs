using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;
public static class DumpLash581
{
 static string F(float v)=>v.ToString("R",CultureInfo.InvariantCulture);
 static Color[] Read(RenderTexture rt){var prior=RenderTexture.active;Texture2D t=null;try{RenderTexture.active=rt;t=new Texture2D(rt.width,rt.height,TextureFormat.RGBAFloat,false,true);t.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0,false);t.Apply(false,false);return t.GetPixels();}finally{RenderTexture.active=prior;if(t)UnityEngine.Object.DestroyImmediate(t);}}
 static string Values(Color c)=>F(c.r)+"\t"+F(c.g)+"\t"+F(c.b)+"\t"+F(c.a);
 static void V(StreamWriter t,string name,Vector4 v)=>t.WriteLine(name+"\t"+F(v.x)+"\t"+F(v.y)+"\t"+F(v.z)+"\t"+F(v.w));
 static void M(StreamWriter t,string name,Matrix4x4 m){for(int r=0;r<4;r++)V(t,name+".row"+r,new Vector4(m[r,0],m[r,1],m[r,2],m[r,3]));}
 public static void Write(HeadLocal367 h,string prefix)
 {
  var e=h.headEyes;var v=h.head;int bottom=272-e.roi.y-e.roi.height;
  using(var t=new StreamWriter(prefix+"_CONFIG581.tsv")){
   V(t,"ROI348",new Vector4(e.roi.x,bottom,e.roi.width,e.roi.height));V(t,"UpperLower348",new Vector4(e.style.upper.x,e.style.upper.y,e.style.lower.x,e.style.lower.y));V(t,"Iris348",new Vector4(e.style.irisRadii.x,e.style.irisRadii.y,e.style.irisOffset,e.style.irisPower));V(t,"Catch348",new Vector4(e.style.catchU.x,e.style.catchU.y,e.style.catchV.x,e.style.catchV.y));
   for(int i=0;i<2;i++){V(t,"Centres348."+i,e.centres[i]);V(t,"AxesX348."+i,e.axesX[i]);V(t,"AxesY348."+i,e.axesY[i]);V(t,"Plane348."+i,v.eyePlanes[i]);M(t,"Inverse348."+i,v.eyeInverse[i]);}
   V(t,"RayBase348",v.rayBase);V(t,"RayX348",v.rayX);V(t,"RayY348",v.rayY);V(t,"RayDepth348",v.rayDepth);V(t,"Profile",v.motion.animation.shadeProfile);M(t,"WorldToHead348",e.headMatrix.inverse);M(t,"HeadView",v.motion.camera.worldToCameraMatrix);M(t,"HeadEffectiveProjection",v.effectiveProjection);M(t,"EyeCropProjection",e.cropProjection);M(t,"FaceLocalToWorld",v.motion.surface.outputs[1].transform.localToWorldMatrix);
  }
  using(var t=new StreamWriter(prefix+"_SUBPIXELS581.tsv")){
   t.WriteLine("cellX\tcellY\tk\tsupport\tinROI\tqX\tqY\tdepth\trole\teye\talpha\trestX\trestY\trestZ\tpointValid\tuvX\tuvY\tprimitive\tuvW\tr\tg\tb\ta");
   for(int s=0;s<7;s++){var layer=e.samples[s];var meta=Read(layer.meta.rt);var point=Read(layer.point.rt);var uv=Read(layer.uv.rt);var rgba=Read(layer.rgba.rt);int width=layer.meta.rt.width,height=layer.meta.rt.height;
    for(int y=51;y<=53;y++)for(int x=216;x<=221;x++)for(int k=0;k<16;k++){int qx=(x-e.roi.x)*4+k%4,qy=(271-y-bottom)*4+k/4;bool inside=qx>=0&&qx<width&&qy>=0&&qy<height;int at=inside?qy*width+qx:0;var z=inside?meta[at]:Color.clear;var p=inside?point[at]:Color.clear;var u=inside?uv[at]:Color.clear;var c=inside?rgba[at]:Color.clear;t.WriteLine(x+"\t"+y+"\t"+k+"\t"+s+"\t"+(inside?1:0)+"\t"+qx+"\t"+qy+"\t"+Values(z)+"\t"+Values(p)+"\t"+Values(u)+"\t"+Values(c));}
   }
  }
  using(var t=new StreamWriter(prefix+"_CELLS581.tsv")){
   t.WriteLine("cellX\tcellY\tbuffer\tr\tg\tb\ta");
   void Add(string name,RenderTexture rt){var a=Read(rt);for(int y=51;y<=53;y++)for(int x=216;x<=221;x++){var c=a[(271-y)*rt.width+x];t.WriteLine(x+"\t"+y+"\t"+name+"\t"+Values(c));}}
   Add("HairMETA",v.layers[6].meta.rt);Add("HairRGBA",v.layers[6].rgba.rt);Add("BrowMETA",v.layers[7].meta.rt);Add("BaseMETA",v.layers[8].meta.rt);Add("BackingMETA",v.layers[10].meta.rt);Add("EyeVisible",e.visible.rt);Add("EyeIntrinsic",e.intrinsic.rt);Add("EyeHistVisible",e.histA.rt);Add("EyeHistIntrinsic",e.histB.rt);Add("EyeAudit",e.audit.rt);Add("EyeSurface",e.surface.rt);Add("EyeSupportMeta",e.supportMeta.rt);Add("EyeOwner",e.owner.rt);Add("EyeOutput",e.output.rt);
  }
  // Original deformed source triangles intersecting the observed lash support box.
  // This is diagnostic data selection, never a rendering condition.
  using(var t=new StreamWriter(prefix+"_TRIANGLES581.tsv")){
   t.WriteLine("renderer\tsubmesh\tprimitive\tvertex\tpx\tpy\tdepth\tuvX\tuvY\tworldX\tworldY\tworldZ");
   foreach(int renderer in new[]{1,2}){var mf=v.motion.surface.outputs[renderer];var mesh=renderer==1?e.sampleFace:mf.sharedMesh;var verts=mesh.vertices;var uv=mesh.uv;var world=verts.Select(p=>mf.transform.TransformPoint(p)).ToArray();var xy=world.Select(v.Project).ToArray();var depth=world.Select(p=>-v.motion.camera.worldToCameraMatrix.MultiplyPoint3x4(p).z).ToArray();
    for(int sm=0;sm<mesh.subMeshCount;sm++){var ids=mesh.GetIndices(sm);for(int k=0;k<ids.Length;k+=3){int a=ids[k],b=ids[k+1],c=ids[k+2];float minX=Mathf.Min(xy[a].x,Mathf.Min(xy[b].x,xy[c].x)),maxX=Mathf.Max(xy[a].x,Mathf.Max(xy[b].x,xy[c].x)),minY=Mathf.Min(xy[a].y,Mathf.Min(xy[b].y,xy[c].y)),maxY=Mathf.Max(xy[a].y,Mathf.Max(xy[b].y,xy[c].y));if(maxX<216||minX>222||maxY<51||minY>54)continue;foreach(int id in new[]{a,b,c})t.WriteLine(renderer+"\t"+sm+"\t"+(k/3+1)+"\t"+id+"\t"+F(xy[id].x)+"\t"+F(xy[id].y)+"\t"+F(depth[id])+"\t"+F(uv[id].x)+"\t"+F(uv[id].y)+"\t"+F(world[id].x)+"\t"+F(world[id].y)+"\t"+F(world[id].z));}}
   }
  }
 }
}
