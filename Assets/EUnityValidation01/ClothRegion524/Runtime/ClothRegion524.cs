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
    public static bool UseOpacityCurves527;
    public static bool UseAreaCurves532;
    public static bool UseWholeRegions539;
    public const int Outerwear540=8,Clothing540=14,BodyAndClothing540=15;
    public static int PartBits540=Outerwear540;
    public sealed class Part540
    {
        public readonly int submesh;
        public Vector2[][] source,curves;
        public float[] areas;public bool[] selected;public RectInt bounds;
        public OpacityRegion525 opacity;public Mesh original;public Material material;
        public Texture2D mask;
        public Part540(int submesh){this.submesh=submesh;}
    }
    public static readonly Part540[] Parts540={new(0),new(1),new(2),new(3)};
    public static Texture2D Atlas540{get;private set;}
    static readonly Color[] atlas540=new Color[480*272];
    static int buildingPart540=3;
    public static bool Active540(int sm)=>sm>=0&&sm<4&&(PartBits540&(1<<sm))!=0;
    public static bool Selected540(int sm,int x,int y)
    {if(!Active540(sm))return false;var p=Parts540[sm];return p.selected!=null&&p.bounds.Contains(new Vector2Int(x,y))&&p.selected[(y-p.bounds.y)*p.bounds.width+x-p.bounds.x];}
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
    // The primary-part public fields are retained for existing diagnostic tools.
    // Each part runs this same geometry/area/selection function, not a clone.
    public static void Prepare(Full319View335 f)
    {
        if(!Enabled||HeadLocal367.IsHead(f))return;
        current=null;Array.Clear(atlas540,0,atlas540.Length);double geometry=0,area=0,selection=0,upload=0;int sourceCount=0,controlCount=0;
        if(PartBits540==0||(PartBits540&~15)!=0){Status="unsupported: invalid body semantic part set";return;}
        foreach(var part in Parts540)
        {
            if(!Active540(part.submesh))continue;buildingPart540=part.submesh;
            Mask=part.mask;Opacity=part.opacity;opacityMesh=part.original;opacityMaterial=part.material;
            PrepareSingle540(f);
            part.mask=Mask;part.opacity=Opacity;part.original=opacityMesh;part.material=opacityMaterial;
            part.source=Source.ToArray();part.curves=Curves.ToArray();part.areas=Areas;part.selected=Selected;part.bounds=Bounds;
            if(!Ready(f)){Status="body part "+part.submesh+": "+Status;current=null;return;}
            geometry+=GeometryMs;area+=AreaMs;selection+=SelectionMs;upload+=UploadMs;sourceCount+=SourcePoints;controlCount+=ControlPoints;
            for(int y=0;y<Bounds.height;y++)for(int x=0;x<Bounds.width;x++)
            {int at=y*Bounds.width+x,i=(271-y-Bounds.y)*480+x+Bounds.x;var c=atlas540[i];c[part.submesh]=Selected[at]?1:0;atlas540[i]=c;}
        }
        var primary=Parts540[3];Mask=primary.mask;Opacity=primary.opacity;opacityMesh=primary.original;opacityMaterial=primary.material;
        Source.Clear();Curves.Clear();if(primary.source!=null)Source.AddRange(primary.source);if(primary.curves!=null)Curves.AddRange(primary.curves);Areas=primary.areas;Selected=primary.selected;Bounds=primary.bounds;
        long start=Stopwatch.GetTimestamp();if(!Atlas540)Atlas540=new Texture2D(480,272,TextureFormat.RGBAFloat,false,true){name="540 shared semantic region RGBA",filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp,hideFlags=HideFlags.DontSave};
        Atlas540.SetPixels(atlas540);Atlas540.Apply(false,false);Shader.SetGlobalTexture("_Cloth524Mask",Atlas540);
        GeometryMs=geometry;AreaMs=area;SelectionMs=selection;UploadMs=upload+Ms(start);SourcePoints=sourceCount;ControlPoints=controlCount;
    }
    static void PrepareSingle540(Full319View335 f)
    {
        if(!Enabled||HeadLocal367.IsHead(f))return;current=null;Status="building";Source.Clear();Curves.Clear();SourcePoints=ControlPoints=0;
        try{
            long start=Stopwatch.GetTimestamp();var mf=f.motion.surface.outputs[0];var mesh=mf.sharedMesh;
            if(mesh.subMeshCount!=4)throw new InvalidOperationException("524 adapter requires declared body clothing material3; no semantic guessing");
            var world=mesh.vertices.Select(mf.transform.TransformPoint).ToArray();var p=world.Select(f.Project).ToArray();var original=f.motion.surface.source[0].sharedMesh;var material=f.motion.materials[buildingPart540];
            if(Opacity==null||opacityMesh!=original||opacityMaterial!=material){Opacity=new OpacityRegion525(original,buildingPart540,material);opacityMesh=original;opacityMaterial=material;}
            Source.AddRange(ClosedRegion524.BuildSegments(Opacity.Project(p,UseOpacityCurves527)));
            foreach(var ring in Source){SourcePoints+=ring.Length;var fit=UseWholeRegions539?ClosedRegionDesign539.Fit(ring):UseAreaCurves532?ClosedRegion524.FitArea532(ring):ClosedRegion524.Fit(ring,HeadRegion502.CurveError*(UseOpacityCurves527&&Opacity.UsedCurveFit527 ? .5f : 1f));if(fit.Length>=3){Curves.Add(fit);ControlPoints+=fit.Length;}}
            if(Curves.Count==0)throw new InvalidOperationException("524 no closed clothing curves");
            int x0=Mathf.Clamp(Mathf.FloorToInt(Curves.Min(r=>r.Min(v=>v.x)))-2,0,479),y0=Mathf.Clamp(Mathf.FloorToInt(Curves.Min(r=>r.Min(v=>v.y)))-2,0,271),x1=Mathf.Clamp(Mathf.CeilToInt(Curves.Max(r=>r.Max(v=>v.x)))+2,x0+1,480),y1=Mathf.Clamp(Mathf.CeilToInt(Curves.Max(r=>r.Max(v=>v.y)))+2,y0+1,272);Bounds=new RectInt(x0,y0,x1-x0,y1-y0);GeometryMs=Ms(start);start=Stopwatch.GetTimestamp();
            var graph=Curves.Select(r=>r.Select(v=>new CurveArea511.P(v.x,v.y)).ToArray()).ToList();Areas=CurveArea511.Compute(graph,x0,y0,Bounds.width,Bounds.height);AreaMs=Ms(start);start=Stopwatch.GetTimestamp();Selected=HeadRegion502.SelectRegions(Areas,Bounds.width,Bounds.height);SelectionMs=Ms(start);start=Stopwatch.GetTimestamp();
            if(!Mask)Mask=new Texture2D(480,272,TextureFormat.RGBAFloat,false,true){name="524 authoritative closed clothing region",filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp,hideFlags=HideFlags.DontSave};
            if(Audit==null)Audit=RTHandles.Alloc(480,272,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,enableRandomWrite:true);
            Array.Clear(colours,0,colours.Length);for(int y=0;y<Bounds.height;y++)for(int x=0;x<Bounds.width;x++){int at=y*Bounds.width+x;colours[(271-y-y0)*480+x+x0]=new Color(Selected[at]?1:0,Areas[at],0,1);}
            Mask.SetPixels(colours);Mask.Apply(false,false);Shader.SetGlobalTexture("_Cloth524Mask",Mask);UploadMs=Ms(start);current=f;Status="ready";
        }catch(Exception e){Status="unsupported: "+e.Message;}
    }
    public static void BeginProbe(RasterCommandBuffer cmd,Full319View335 f){cmd.SetGlobalInt("_Cloth524Enabled",Ready(f)?1:0);cmd.SetGlobalInt("_Cloth524Parts",PartBits540);}
    public static void Bind(CommandBuffer cmd,ComputeShader shader,int kernel,Full319View335 f){cmd.SetComputeIntParam(shader,"_Cloth524Enabled",Ready(f)?1:0);cmd.SetComputeIntParam(shader,"_Cloth524Parts",PartBits540);cmd.SetComputeTextureParam(shader,kernel,"_Cloth524Mask",Atlas540?Atlas540:Texture2D.blackTexture);cmd.SetComputeTextureParam(shader,kernel,"_Audit",Audit!=null?Audit.rt:f.audit.rt);cmd.SetComputeTextureParam(shader,kernel,"_Before",f.before.rt);cmd.SetComputeTextureParam(shader,kernel,"_Colour",f.colour.rt);}
    public static void CopyAudit(CommandBuffer cmd,Full319View335 f){if(Ready(f))cmd.CopyTexture(f.audit.rt,Audit.rt);}
    public static void Release(){Enabled=UseOpacityCurves527=UseAreaCurves532=UseWholeRegions539=false;PartBits540=Outerwear540;current=null;Status="disabled";Shader.SetGlobalInt("_Cloth524Enabled",0);Shader.SetGlobalTexture("_Cloth524Mask",Texture2D.blackTexture);foreach(var p in Parts540){if(p.mask)UnityEngine.Object.DestroyImmediate(p.mask);p.mask=null;p.opacity=null;p.original=null;p.material=null;p.source=null;p.curves=null;p.areas=null;p.selected=null;}if(Atlas540)UnityEngine.Object.DestroyImmediate(Atlas540);Atlas540=null;Mask=null;Audit?.Release();Audit=null;Source.Clear();Curves.Clear();Areas=null;Selected=null;Opacity=null;opacityMesh=null;opacityMaterial=null;ClothSurface525.Release();}
}
