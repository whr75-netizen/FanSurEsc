using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

// Default-OFF clothing adapter for the common boundary-first generation contract.
// Automatic projected vector regions own fill; this replaces the open arm frontier.
public static class ClothRegion524
{
    public static bool Enabled;
    public static string Status="disabled";
    public static double GeometryMs,AreaMs,SelectionMs,UploadMs;
    public static int SourcePoints,ControlPoints;
    public static readonly List<Vector2[]> Source=new(),Curves=new();
    public static float[] Areas;public static bool[] Selected;public static RectInt Bounds;
    public static Texture2D Mask{get;private set;}
    public static RTHandle Audit{get;private set;}
    static Full319View335 current;
    public static OpacityRegion525 Opacity {get;private set;}
    static Mesh opacityMesh;static Material opacityMaterial;
    static Color[] colours=new Color[480*272];
    public static bool Ready(Full319View335 f)=>Enabled&&current==f&&Status=="ready";
    static double Ms(long t)=>1000.0*(Stopwatch.GetTimestamp()-t)/Stopwatch.Frequency;
    public static void Prepare(Full319View335 f)
    {
        if(!Enabled||HeadLocal367.IsHead(f))return;current=null;Status="building";Source.Clear();Curves.Clear();SourcePoints=ControlPoints=0;
        try{
            long start=Stopwatch.GetTimestamp();var mf=f.motion.surface.outputs[0];var mesh=mf.sharedMesh;
            if(mesh.subMeshCount!=4)throw new InvalidOperationException("524 adapter requires declared body clothing material3; no semantic guessing");
            var world=mesh.vertices.Select(mf.transform.TransformPoint).ToArray();var p=world.Select(f.Project).ToArray();var original=f.motion.surface.source[0].sharedMesh;var material=f.motion.materials[3];
            if(Opacity==null||opacityMesh!=original||opacityMaterial!=material){Opacity=new OpacityRegion525(original,3,material);opacityMesh=original;opacityMaterial=material;}
            Source.AddRange(ClosedRegion524.BuildSegments(Opacity.Project(p)));
            foreach(var ring in Source){SourcePoints+=ring.Length;var fit=ClosedRegion524.Fit(ring,HeadRegion502.CurveError);if(fit.Length>=3){Curves.Add(fit);ControlPoints+=fit.Length;}}
            if(Curves.Count==0)throw new InvalidOperationException("524 no closed clothing curves");
            int x0=Mathf.Clamp(Mathf.FloorToInt(Curves.Min(r=>r.Min(v=>v.x)))-2,0,479),y0=Mathf.Clamp(Mathf.FloorToInt(Curves.Min(r=>r.Min(v=>v.y)))-2,0,271),x1=Mathf.Clamp(Mathf.CeilToInt(Curves.Max(r=>r.Max(v=>v.x)))+2,x0+1,480),y1=Mathf.Clamp(Mathf.CeilToInt(Curves.Max(r=>r.Max(v=>v.y)))+2,y0+1,272);Bounds=new RectInt(x0,y0,x1-x0,y1-y0);GeometryMs=Ms(start);start=Stopwatch.GetTimestamp();
            var graph=Curves.Select(r=>r.Select(v=>new CurveArea511.P(v.x,v.y)).ToArray()).ToList();Areas=CurveArea511.Compute(graph,x0,y0,Bounds.width,Bounds.height);AreaMs=Ms(start);start=Stopwatch.GetTimestamp();Selected=HeadRegion502.SelectRegions(Areas,Bounds.width,Bounds.height);SelectionMs=Ms(start);start=Stopwatch.GetTimestamp();
            if(!Mask)Mask=new Texture2D(480,272,TextureFormat.RGBAFloat,false,true){name="524 authoritative closed clothing region",filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp,hideFlags=HideFlags.DontSave};
            if(Audit==null)Audit=RTHandles.Alloc(480,272,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,enableRandomWrite:true);
            Array.Clear(colours,0,colours.Length);for(int y=0;y<Bounds.height;y++)for(int x=0;x<Bounds.width;x++){int at=y*Bounds.width+x;colours[(271-y-y0)*480+x+x0]=new Color(Selected[at]?1:0,Areas[at],0,1);}
            Mask.SetPixels(colours);Mask.Apply(false,false);Shader.SetGlobalTexture("_Cloth524Mask",Mask);UploadMs=Ms(start);current=f;Status="ready";
        }catch(Exception e){Status="unsupported: "+e.Message;}
    }
    public static void BeginProbe(RasterCommandBuffer cmd,Full319View335 f){cmd.SetGlobalInt("_Cloth524Enabled",Ready(f)?1:0);}
    public static void Bind(CommandBuffer cmd,ComputeShader shader,int kernel,Full319View335 f){cmd.SetComputeIntParam(shader,"_Cloth524Enabled",Ready(f)?1:0);cmd.SetComputeTextureParam(shader,kernel,"_Cloth524Mask",Mask?Mask:Texture2D.blackTexture);cmd.SetComputeTextureParam(shader,kernel,"_Audit",Audit!=null?Audit.rt:f.audit.rt);cmd.SetComputeTextureParam(shader,kernel,"_Before",f.before.rt);cmd.SetComputeTextureParam(shader,kernel,"_Colour",f.colour.rt);}
    public static void CopyAudit(CommandBuffer cmd,Full319View335 f){if(Ready(f))cmd.CopyTexture(f.audit.rt,Audit.rt);}
    public static void Release(){Enabled=false;current=null;Status="disabled";Shader.SetGlobalInt("_Cloth524Enabled",0);Shader.SetGlobalTexture("_Cloth524Mask",Texture2D.blackTexture);if(Mask)UnityEngine.Object.DestroyImmediate(Mask);Mask=null;Audit?.Release();Audit=null;Source.Clear();Curves.Clear();Areas=null;Selected=null;Opacity=null;opacityMesh=null;opacityMaterial=null;ClothSurface525.Release();}
}
