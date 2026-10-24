using System;
using System.IO;
using System.Globalization;
using UnityEngine;
public static class CropGradient586{
 static string F(float v)=>v.ToString("R",CultureInfo.InvariantCulture);
 public static void Write(HeadLocal367 h,string prefix){var e=h.headEyes;var v=h.head;var vp=e.cropProjection*v.motion.camera.worldToCameraMatrix;int w=e.samples[0].meta.rt.width,ht=e.samples[0].meta.rt.height;
  var meshes=new[]{v.motion.surface.outputs[0].sharedMesh,e.sampleFace};var uvAll=new Vector2[2][];var xyAll=new Vector2[2][];for(int r=0;r<2;r++){uvAll[r]=meshes[r].uv;var vertices=meshes[r].vertices;xyAll[r]=new Vector2[vertices.Length];var model=v.motion.surface.outputs[r].transform.localToWorldMatrix;for(int k=0;k<vertices.Length;k++){Vector3 world=model.MultiplyPoint3x4(vertices[k]);Vector4 clip=vp*new Vector4(world.x,world.y,world.z,1);xyAll[r][k]=new Vector2((clip.x/clip.w*.5f+.5f)*w,(clip.y/clip.w*.5f+.5f)*ht);}}
  using(var t=new StreamWriter(prefix+"_CROPGRAD586.tsv")){t.WriteLine("support\tsubmesh\tprimitive\tduDx\tdvDx\tduDy\tdvDy");
   foreach(var line in File.ReadAllLines("C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/EyeArea585/Runtime585/Geometry5/000_ON_TRIS585.tsv")){
    if(line.StartsWith("support"))continue;var q=line.Split('\t');int support=int.Parse(q[0]),renderer=int.Parse(q[1]),sm=int.Parse(q[2]),primitive=int.Parse(q[3]);var uv=uvAll[renderer];var ids=new[]{int.Parse(q[4]),int.Parse(q[5]),int.Parse(q[6])};var p=new[]{xyAll[renderer][ids[0]],xyAll[renderer][ids[1]],xyAll[renderer][ids[2]]};
    var b=p[1]-p[0];var c=p[2]-p[0];float det=b.x*c.y-b.y*c.x;if(Mathf.Abs(det)<1e-12f)continue;var u=uv[ids[1]]-uv[ids[0]];var z=uv[ids[2]]-uv[ids[0]];var dx=(u*c.y-z*b.y)/det;var dy=(-u*c.x+z*b.x)/det;t.WriteLine(support+"\t"+sm+"\t"+primitive+"\t"+F(dx.x)+"\t"+F(dx.y)+"\t"+F(dy.x)+"\t"+F(dy.y));
   }
  }
  using(var t=new StreamWriter(prefix+"_PARITY586.tsv")){t.WriteLine("x\ty\tbuffer\tr\tg\tb\ta");foreach(var item in new[]{("EyeVisible",e.visible.rt),("EyeIntrinsic",e.intrinsic.rt)}){var old=RenderTexture.active;var rt=item.Item2;Texture2D tex=null;try{RenderTexture.active=rt;tex=new Texture2D(rt.width,rt.height,TextureFormat.RGBAFloat,false,true);tex.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0);tex.Apply();var a=tex.GetPixels();for(int y=e.roi.y;y<e.roi.yMax;y++)for(int x=e.roi.x;x<e.roi.xMax;x++){var c=a[(271-y)*rt.width+x];t.WriteLine(x+"\t"+y+"\t"+item.Item1+"\t"+F(c.r)+"\t"+F(c.g)+"\t"+F(c.b)+"\t"+F(c.a));}}finally{RenderTexture.active=old;if(tex)UnityEngine.Object.DestroyImmediate(tex);}}}
 }
}
