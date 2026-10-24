using System;
using System.IO;
using System.Globalization;
using UnityEngine;
using UnityEditor;
public static class ReadArea587 {
 static string F(float v)=>v.ToString("R",CultureInfo.InvariantCulture);
 public static void Write(HeadLocal367 h,string prefix,double renderMs) {
  var e=h.headEyes;var areas=new Vector4[2];if(EyeFeature348.UseLashArea587)e.lashArea587.GetData(areas);
  foreach(var m in ShaderUtil.GetComputeShaderMessages(e.candidateShader))if(m.severity.ToString()=="Error")throw new Exception("587 invalid current compute variant: "+m.message);
  foreach(var s in new[]{e.skinMaterial.shader,e.materials[0].shader})foreach(var m in ShaderUtil.GetShaderMessages(s))if(m.severity.ToString()=="Error")throw new Exception("587 invalid current source variant: "+m.message);
  using(var t=new StreamWriter(prefix+"_AREA587.tsv")){
   t.WriteLine("eyeID\tarea\terrorEstimate\tcoarseMin\tcoarseMax\tboxX\tboxY\tboxW\tboxH\ttextureBytes\trenderFrameCallMsIncludesExistingPipeline");
   for(int i=0;i<2;i++){var a=areas[i];var b=e.area587!=null?e.area587.views[i].box:new RectInt();t.WriteLine(F(e.centres[i].w)+"\t"+F(a.x)+"\t"+F(a.y)+"\t"+F(a.z)+"\t"+F(a.w)+"\t"+b.x+"\t"+b.y+"\t"+b.width+"\t"+b.height+"\t"+(e.area587?.textureBytes??0)+"\t"+renderMs.ToString("R",CultureInfo.InvariantCulture));}
  }
  using(var t=new StreamWriter(prefix+"_CELLS587.tsv")){
   t.WriteLine("x\ty\tbuffer\tr\tg\tb\ta");
   foreach(var item in new[]{("EyeVisible",e.visible.rt),("EyeIntrinsic",e.intrinsic.rt),("Colour",e.full.colour.rt),("Owner",e.full.owner.rt)}) {
    var old=RenderTexture.active;Texture2D tex=null;var rt=item.Item2;
    try{RenderTexture.active=rt;tex=new Texture2D(rt.width,rt.height,TextureFormat.RGBAFloat,false,true);tex.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0);tex.Apply();var a=tex.GetPixels();for(int y=e.roi.y;y<e.roi.yMax;y++)for(int x=e.roi.x;x<e.roi.xMax;x++){var c=a[(271-y)*rt.width+x];t.WriteLine(x+"\t"+y+"\t"+item.Item1+"\t"+F(c.r)+"\t"+F(c.g)+"\t"+F(c.b)+"\t"+F(c.a));}}
    finally{RenderTexture.active=old;if(tex)UnityEngine.Object.DestroyImmediate(tex);}
   }
  }
 }
}
