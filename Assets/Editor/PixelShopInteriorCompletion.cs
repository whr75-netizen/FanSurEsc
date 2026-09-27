using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FantasySurvival.WorldGeneration;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

/// <summary>Authored native sprites and box depth share one projection. No image resizing.</summary>
public static class PixelShopInteriorCompletion
{
    public const string Folder = "Assets/Art/PixelShopInterior34Aligned";
    public const string ContentName = "Interior34 - aligned native surfaces";
    public const string Prefab = PlannedPixelBuildingAuthoring.PrefabPath;
    public const string Calibration = "docs/artifacts/building34/calibration-oriented.json";
    private const float FloorY = .015f;
    private const float RoofHeight = 2.65f;
    private static readonly Quaternion View = Quaternion.Euler(30,45,0);
    private static readonly Vector3 Right = View*Vector3.right, Up = View*Vector3.up, Forward = View*Vector3.forward;
    private static float ppu;
    private static readonly Dictionary<string,Texture2D> Sources = new();
    private static readonly Dictionary<Texture2D,Color32[]> SourcePixels = new();
    [Serializable] public sealed class AssetSpec
    {
        public string id, fixture_id, native_path;
        public float width_m,depth_m,height_m;
        public float[] origin_screen_m,center_xz;
        public int[] native_dimensions;
        public int opaque_ray_misses;
        public bool mirrorU;
    }
    [Serializable] public sealed class Spec { public float ppu; public AssetSpec[] assets; }
    [Serializable] private sealed class Rect { public string id;public float[] rect_xz; }
    [Serializable] private sealed class Plan { public Rect[] walls,partitions; }
    [Serializable] public sealed class BakeResult
    {
        public string id;public int opaqueTexels,rayMisses;public float minY,maxY;
    }
    [Serializable] private sealed class BuildReport
    {
        public string producer="UnityEditor.PixelShopInteriorCompletion",prefab=Prefab;
        public float ppu,roofHeight=RoofHeight;
        public BakeResult[] objects;
        public int closedStructureSurfaces;
    }

    [MenuItem("Tools/World Art/Complete Pixel Shop Interior 34")]
    public static void Apply()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit mode required.");
        var spec=JsonUtility.FromJson<Spec>(File.ReadAllText(Calibration));
        if(spec==null||spec.assets==null||spec.assets.Length!=5||spec.ppu<=0||spec.assets.Any(a=>a.opaque_ray_misses!=0))
            throw new InvalidDataException("A source-preserving calibrated five-object set is required.");
        if(AssetDatabase.IsValidFolder(Folder))throw new InvalidOperationException("Existing B34 preserved; use a targeted repair rather than rebuild.");
        ppu=spec.ppu;
        Ensure(Folder);Ensure(Folder+"/Source");Ensure(Folder+"/Meshes");Ensure(Folder+"/Materials");Ensure(Folder+"/Depth");Ensure(Folder+"/Structure");
        foreach(var id in new[]{"counter","rear_shelf","left_shelf","island","stock_shelf","floor","wall_left","wall_right","lamp"})
        {
            string path=Folder+"/Source/"+id+".png";
            File.Copy("docs/artifacts/building34/native/"+id+"/native.png",path,false);
            AssetDatabase.ImportAsset(path);
            var importer=(TextureImporter)AssetImporter.GetAtPath(path);
            importer.textureType=TextureImporterType.Default;importer.filterMode=FilterMode.Point;
            importer.mipmapEnabled=false;importer.textureCompression=TextureImporterCompression.Uncompressed;
            importer.wrapMode=TextureWrapMode.Clamp;importer.npotScale=TextureImporterNPOTScale.None;
            importer.isReadable=true;importer.alphaIsTransparency=false;importer.maxTextureSize=4096;
            importer.SaveAndReimport();Sources[id]=AssetDatabase.LoadAssetAtPath<Texture2D>(path);SourcePixels[Sources[id]]=Sources[id].GetPixels32();
        }
        var root=PrefabUtility.LoadPrefabContents(Prefab);
        try
        {
            foreach(Transform child in root.transform)child.gameObject.SetActive(false);
            var content=Group(root.transform,ContentName);
            var solids=Group(content,"Structure - closed volumes");
            var furniture=Group(content,"Fixtures - role plan");
            var lights=Group(content,"Wall lamps - source anchors");
            var front=new List<Renderer>();var frontCols=new List<Collider>();
            var back=new List<Renderer>();var backCols=new List<Collider>();
            var roof=new List<Renderer>();var roofCols=new List<Collider>();
            var report=new List<BakeResult>();int surfaces=0;
            var floor=BoxSurface(solids,"Floor",new Bounds(new Vector3(0,-.025f,0),new Vector3(10,.08f,8)),"floor");surfaces++;
            var top=BoxSurface(solids,"Roof - closed opaque volume",new Bounds(new Vector3(0,RoofHeight+.075f,0),new Vector3(10.15f,.15f,8.15f)),"roof");
            roof.Add(top);roofCols.Add(top.transform.parent.GetComponent<Collider>());surfaces++;
            var plan=JsonUtility.FromJson<Plan>(File.ReadAllText(PlannedPixelBuildingAuthoring.PlanPath));
            foreach(var wall in plan.walls.Concat(plan.partitions))
            {
                var q=wall.rect_xz;float height=RoofHeight;
                var b=new Bounds(new Vector3((q[0]+q[2])*.5f,height*.5f,(q[1]+q[3])*.5f),new Vector3(q[2]-q[0],height,q[3]-q[1]));
                var r=BoxSurface(solids,wall.id,b,"wall");surfaces++;
                // Camera lies at -Forward: local XMIN and ZMIN are the near walls.
                bool frontFacing=wall.id=="wall_left"||wall.id.StartsWith("wall_front")||wall.id.StartsWith("stock_");
                (frontFacing?front:back).Add(r);(frontFacing?frontCols:backCols).Add(r.transform.parent.GetComponent<Collider>());
            }
            // Lintels complete the openings without blocking their walking volume.
            foreach(var doorway in new[]{new Bounds(new Vector3(0,2.475f,-4),new Vector3(2,.35f,.15f)),
                new Bounds(new Vector3(1.1f,2.475f,2),new Vector3(.15f,.35f,1.5f))})
            {
                var r=BoxSurface(solids,"Door lintel "+surfaces,doorway,"wall");front.Add(r);frontCols.Add(r.transform.parent.GetComponent<Collider>());surfaces++;
            }
            foreach(var a in spec.assets)
            {
                var t=Group(furniture,a.fixture_id);t.localPosition=new Vector3(a.center_xz[0],FloorY,a.center_xz[1]);
                var b=new Bounds(Vector3.up*a.height_m*.5f,new Vector3(a.width_m,a.height_m,a.depth_m));
                var col=t.gameObject.AddComponent<BoxCollider>();col.center=b.center;col.size=b.size;
                var tex=Sources[a.id];var data=BakeDepth(tex,b,a.origin_screen_m[0],a.origin_screen_m[1],a.id,out var stat,a.mirrorU);
                report.Add(stat);CreateSurface(t,a.id,tex,data,a.origin_screen_m[0],a.origin_screen_m[1],a.mirrorU);
            }
            AddLamp(lights,"Back lamp",new Vector3(.55f,1.7f,3.92f),Vector3.back);
            AddLamp(lights,"Left lamp",new Vector3(-4.92f,1.7f,-.15f),Vector3.right);
            BindVolumes(content);
            var building=root.GetComponent<NativePixelBuilding>();
            building.interior=new Bounds(new Vector3(0,RoofHeight*.5f,0),new Vector3(10,RoofHeight,8));
            building.frontWalls=front.ToArray();building.frontColliders=frontCols.ToArray();
            building.backWalls=back.ToArray();building.backColliders=backCols.ToArray();
            building.roof=roof.ToArray();building.roofColliders=roofCols.ToArray();
            building.useNativePixelGrid=true;building.nativePixelsPerUnit=ppu;
            PrefabUtility.SaveAsPrefabAsset(root,Prefab);AssetDatabase.SaveAssets();
            File.WriteAllText("docs/artifacts/building34/unity-build.json",JsonUtility.ToJson(new BuildReport{ppu=ppu,objects=report.ToArray(),closedStructureSurfaces=surfaces},true));
        }
        finally {PrefabUtility.UnloadPrefabContents(root);Sources.Clear();SourcePixels.Clear();}
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        ShowInterior();
    }

    private static Renderer BoxSurface(Transform parent,string id,Bounds b,string kind)
    {
        var t=Group(parent,id);t.localPosition=b.center;
        var box=new Bounds(Vector3.zero,b.size);var col=t.gameObject.AddComponent<BoxCollider>();col.size=b.size;
        var points=new List<Vector2>();
        for(int i=0;i<8;i++){var p=new Vector3((i&1)==0?box.min.x:box.max.x,(i&2)==0?box.min.y:box.max.y,(i&4)==0?box.min.z:box.max.z);points.Add(new Vector2(Vector3.Dot(p,Right),Vector3.Dot(p,Up)));}
        float left=Mathf.Floor(points.Min(p=>p.x)*ppu)/ppu,top=Mathf.Ceil(points.Max(p=>p.y)*ppu)/ppu;
        int w=Mathf.CeilToInt((points.Max(p=>p.x)-left)*ppu)+1,h=Mathf.CeilToInt((top-points.Min(p=>p.y))*ppu)+1;
        var pixels=new Color[w*h];var depths=new Color[w*h];
        for(int y=0;y<h;y++)for(int x=0;x<w;x++)
        {
            var p=Right*(left+(x+.5f)/ppu)+Up*(top+(y+.5f-h)/ppu);
            if(!Hit(p,box,out var hit))continue;
            var worldLocal=hit+b.center;
            pixels[y*w+x]=MaterialColor(kind,worldLocal,hit,box);
            depths[y*w+x]=new Color(hit.x,hit.y,hit.z,1);
        }
        var color=new Texture2D(w,h,TextureFormat.RGBA32,false,false){filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp};
        color.SetPixels(pixels);color.Apply();
        string colorPath=Folder+"/Structure/"+Safe(id)+".png";File.WriteAllBytes(colorPath,color.EncodeToPNG());Object.DestroyImmediate(color);
        AssetDatabase.ImportAsset(colorPath);ConfigureTexture(colorPath,false);color=AssetDatabase.LoadAssetAtPath<Texture2D>(colorPath);
        var depth=SaveDepth(id,w,h,depths);
        return CreateSurface(t,id,color,depth,left,top);
    }

    private static Color MaterialColor(string kind,Vector3 p,Vector3 hit,Bounds box)
    {
        if(kind=="floor")
        {
            var tex=Sources["floor"];float period=(tex.width-32)/(Mathf.Sqrt(2)*ppu);
            float x=Mathf.Repeat(p.x+period*.5f,period)-period*.5f,z=Mathf.Repeat(p.z+period*.5f,period)-period*.5f;
            int u=Mathf.RoundToInt(tex.width*.5f+(x-z)*ppu/Mathf.Sqrt(2));
            int v=Mathf.RoundToInt(tex.height*.5f+(x+z)*ppu*.5f/Mathf.Sqrt(2));
            var c=Sample(tex,u,v);if(c.a<.1f)throw new InvalidDataException("Floor material swatch left its opaque diamond.");c.a=1;return c;
        }
        // Structural material swatches are integer source regions, not resized object sprites.
        var wall=Sources["wall_left"];
        int ix=55+Mathf.FloorToInt(Mathf.Repeat((p.x+p.z)*ppu*.70710678f,38));
        int iy;
        if(kind=="roof")iy=150+Mathf.FloorToInt(Mathf.Repeat((p.x-p.z)*ppu*.35355339f,16));
        else if(p.y<.72f)iy=53+Mathf.FloorToInt(Mathf.Repeat(p.y*ppu*.8660254f,20));
        else iy=135+Mathf.FloorToInt(Mathf.Repeat(p.y*ppu*.8660254f,32));
        var source=Sample(wall,ix,iy);source.a=1;
        if(kind=="roof")source*=new Color(.55f,.62f,.7f,1);
        // Bands are actual baseboard/top cap geometry colors sampled from the source frame.
        if(kind=="wall"&&(p.y<.05f||p.y>RoofHeight-.035f||Mathf.Abs(p.y-.72f)<.015f))source=Sample(wall,61,48);
        source.a=1;return source;
    }

    private static Texture2D BakeDepth(Texture2D source,Bounds b,float left,float top,string id,out BakeResult report,bool mirrorU=false)
    {
        report=new BakeResult{id=id,minY=float.PositiveInfinity,maxY=float.NegativeInfinity};
        var data=new Color[source.width*source.height];var pixels=source.GetPixels();
        for(int y=0;y<source.height;y++)for(int x=0;x<source.width;x++)
        {
            int index=y*source.width+x;if(pixels[index].a<=.1f)continue;report.opaqueTexels++;
            float displayX=mirrorU?source.width-x-.5f:x+.5f;
            var p=Right*(left+displayX/ppu)+Up*(top+(y+.5f-source.height)/ppu);
            if(!Hit(p,b,out var hit)){report.rayMisses++;continue;}
            report.minY=Mathf.Min(report.minY,hit.y);report.maxY=Mathf.Max(report.maxY,hit.y);
            data[index]=new Color(hit.x,hit.y,hit.z,1);
        }
        if(report.rayMisses>0)throw new InvalidDataException(id+": opaque ray misses="+report.rayMisses);
        return SaveDepth(id,source.width,source.height,data);
    }

    private static bool Hit(Vector3 p,Bounds b,out Vector3 hit)
    {
        var ray=new Ray(p-Forward*100,Forward);
        if(b.IntersectRay(ray,out float distance)){hit=ray.GetPoint(distance);return true;}
        hit=default;return false;
    }
    private static Texture2D SaveDepth(string id,int w,int h,Color[] data)
    {
        var tex=new Texture2D(w,h,TextureFormat.RGBAFloat,false,true){name=id+"_surface_positions",filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp};
        tex.SetPixels(data);tex.Apply();string path=Folder+"/Depth/"+Safe(id)+".exr";
        File.WriteAllBytes(path,tex.EncodeToEXR(Texture2D.EXRFlags.OutputAsFloat|Texture2D.EXRFlags.CompressZIP));Object.DestroyImmediate(tex);
        AssetDatabase.ImportAsset(path);ConfigureTexture(path,true);return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }
    private static Color Sample(Texture2D t,int x,int y)=>SourcePixels[t][Mathf.Clamp(y,0,t.height-1)*t.width+Mathf.Clamp(x,0,t.width-1)];
    private static void ConfigureTexture(string path,bool depth)
    {
        var i=(TextureImporter)AssetImporter.GetAtPath(path);i.textureType=TextureImporterType.Default;i.sRGBTexture=!depth;
        i.filterMode=FilterMode.Point;i.wrapMode=TextureWrapMode.Clamp;i.mipmapEnabled=false;i.npotScale=TextureImporterNPOTScale.None;
        i.textureCompression=TextureImporterCompression.Uncompressed;i.isReadable=true;i.maxTextureSize=4096;i.alphaIsTransparency=false;
        if(depth){var ps=i.GetDefaultPlatformTextureSettings();ps.format=TextureImporterFormat.RGBAFloat;i.SetPlatformTextureSettings(ps);}
        i.SaveAndReimport();
    }
    private static Renderer CreateSurface(Transform parent,string id,Texture2D color,Texture2D depth,float left,float top,bool mirrorU=false)
    {
        Vector3 P(float x,float y)=>Right*(left+x/ppu)+Up*(top+y/ppu);
        var mesh=new Mesh{name=id,vertices=new[]{P(0,-color.height),P(color.width,-color.height),P(color.width,0),P(0,0)},triangles=new[]{0,1,2,0,2,3}};
        float u0=mirrorU?1:0,u1=mirrorU?0:1;
        mesh.SetUVs(0,new List<Vector3>{new(u0,0,1),new(u1,0,1),new(u1,1,1),new(u0,1,1)});mesh.RecalculateNormals();mesh.RecalculateBounds();
        var bounds=mesh.bounds;bounds.Expand(2f/ppu);mesh.bounds=bounds;AssetDatabase.CreateAsset(mesh,Folder+"/Meshes/"+Safe(id)+".asset");
        var mat=new Material(Shader.Find("FantasySurvival/World/Isometric Atlas Surface")){name=id};
        mat.SetTexture("_BaseMap",color);mat.SetTexture("_NativeDepthMap",depth);mat.SetFloat("_NativeDepthEnabled",1);
        mat.SetFloat("_VertexAtlasUv",1);mat.SetFloat("_NativeGridEnabled",1);mat.SetFloat("_MetricLighting",0);
        mat.SetVector("_NativeGridOriginOS",mesh.vertices[0]);mat.SetVector("_NativeGridTexelUOS",Right/ppu);mat.SetVector("_NativeGridTexelVOS",Up/ppu);
        AssetDatabase.CreateAsset(mat,Folder+"/Materials/"+Safe(id)+".mat");
        var t=Group(parent,"Native surface");t.gameObject.AddComponent<MeshFilter>().sharedMesh=mesh;
        var renderer=t.gameObject.AddComponent<MeshRenderer>();renderer.sharedMaterial=mat;renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;return renderer;
    }
    private static void AddLamp(Transform parent,string id,Vector3 centre,Vector3 normal)
    {
        var t=Group(parent,id);t.localPosition=centre;
        var source=Sources["lamp"];float left=-source.width*.5f/ppu,top=source.height*.5f/ppu;
        var data=new Color[source.width*source.height];var pixels=source.GetPixels();
        for(int y=0;y<source.height;y++)for(int x=0;x<source.width;x++)
        {
            if(pixels[y*source.width+x].a<=.1f)continue;
            var p=Right*(left+(x+.5f)/ppu)+Up*(top+(y+.5f-source.height)/ppu);
            float parameter=-Vector3.Dot(p,normal)/Vector3.Dot(Forward,normal);
            var hit=p+Forward*parameter;data[y*source.width+x]=new Color(hit.x,hit.y,hit.z,1);
        }
        CreateSurface(t,id,source,SaveDepth(id,source.width,source.height,data),left,top);
        var emitter=Group(t,"Emitter");emitter.localPosition=normal*.12f;
        var light=emitter.gameObject.AddComponent<SteppedLocalLight>();var so=new SerializedObject(light);
        so.FindProperty("color").colorValue=new Color(1,.74f,.42f,1);so.FindProperty("radius").floatValue=3.2f;
        // Small local contribution; three .12 RGB jumps previously made bright disks.
        so.FindProperty("intensity").floatValue=.12f;so.FindProperty("surfaceBands").intValue=6;
        so.FindProperty("haloStrength").floatValue=0;so.FindProperty("normalInfluence").floatValue=0;
        so.FindProperty("worldCellSize").floatValue=1/ppu;so.ApplyModifiedPropertiesWithoutUndo();
    }
    private static void BindVolumes(Transform content)
    {
        var volumes=content.Find("Sales light volumes");
        if(volumes==null)volumes=Group(content,"Sales light volumes");
        var definitions=new[]{new Bounds(new Vector3(-1.9875f,1.325f,0),new Vector3(6.025f,2.65f,8)),
            new Bounds(new Vector3(3.0125f,1.325f,-1.5875f),new Vector3(3.975f,2.65f,4.825f))};
        var boxes=new BoxCollider[2];
        for(int n=0;n<2;n++)
        {
            var t=volumes.Find("Region "+n);if(t==null)t=Group(volumes,"Region "+n);
            var c=t.GetComponent<BoxCollider>();if(c==null)c=t.gameObject.AddComponent<BoxCollider>();
            c.center=definitions[n].center;c.size=definitions[n].size;c.enabled=false;boxes[n]=c;
        }
        foreach(var light in content.GetComponentsInChildren<SteppedLocalLight>())
        {
            var so=new SerializedObject(light);so.FindProperty("illuminationVolume").objectReferenceValue=boxes[0];
            so.FindProperty("illuminationVolume2").objectReferenceValue=boxes[1];so.ApplyModifiedPropertiesWithoutUndo();
        }
    }
    public static void ConnectRoomLighting()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit mode required.");
        var root=PrefabUtility.LoadPrefabContents(Prefab);
        try{BindVolumes(root.transform.Find(ContentName));PrefabUtility.SaveAsPrefabAsset(root,Prefab);AssetDatabase.SaveAssets();}
        finally{PrefabUtility.UnloadPrefabContents(root);}
    }
    public static void ApplyWarmFloor()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit mode required.");
        string source="docs/artifacts/building34/warm-floor/native.png",asset=Folder+"/Source/floor-warm.png";
        if(!File.Exists(source))throw new FileNotFoundException(source);
        File.Copy(source,asset,false);AssetDatabase.ImportAsset(asset);ConfigureTexture(asset,false);
        var warm=AssetDatabase.LoadAssetAtPath<Texture2D>(asset);var warmPixels=warm.GetPixels32();
        var spec=JsonUtility.FromJson<Spec>(File.ReadAllText(Calibration));ppu=spec.ppu;
        var root=PrefabUtility.LoadPrefabContents(Prefab);
        try
        {
            var r=root.transform.Find(ContentName+"/Structure - closed volumes/Floor/Native surface").GetComponent<Renderer>();
            var mat=r.sharedMaterial;var depth=(Texture2D)mat.GetTexture("_NativeDepthMap");var positions=depth.GetPixels();
            var color=(Texture2D)mat.GetTexture("_BaseMap");var pixels=new Color32[positions.Length];
            for(int j=0;j<positions.Length;j++)
            {
                var p=positions[j];if(p.a<.5f)continue;
                int x=Mathf.FloorToInt(Mathf.Repeat(p.r*ppu*.70710678f,warm.width));
                int y=Mathf.FloorToInt(Mathf.Repeat(p.b*ppu*.70710678f,warm.height));
                var c=warmPixels[y*warm.width+x];c.a=255;pixels[j]=c;
            }
            var output=new Texture2D(color.width,color.height,TextureFormat.RGBA32,false);output.SetPixels32(pixels);output.Apply();
            string path=AssetDatabase.GetAssetPath(color);File.WriteAllBytes(path,output.EncodeToPNG());Object.DestroyImmediate(output);AssetDatabase.ImportAsset(path);
            AssetDatabase.SaveAssets();
        }
        finally{PrefabUtility.UnloadPrefabContents(root);}
    }
    public static void ApplyCutawayBases()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit mode required.");
        ppu=JsonUtility.FromJson<Spec>(File.ReadAllText(Calibration)).ppu;
        var wall=AssetDatabase.LoadAssetAtPath<Texture2D>(Folder+"/Source/wall_left.png");
        Sources["wall_left"]=wall;SourcePixels[wall]=wall.GetPixels32();
        var root=PrefabUtility.LoadPrefabContents(Prefab);
        try
        {
            var content=root.transform.Find(ContentName);
            if(content.Find("Cutaway bases")!=null)throw new InvalidOperationException("Cutaway already authored; preserve current result.");
            var bases=Group(content,"Cutaway bases");
            const float cutHeight=.55f;
            var building=root.GetComponent<NativePixelBuilding>();
            foreach(var r in building.frontWalls)
            {
                var id=r.transform.parent.name;
                if(id.StartsWith("Door lintel"))continue;
                var collider=r.transform.parent.GetComponent<BoxCollider>();
                var physical=new Bounds(collider.transform.localPosition+collider.center,collider.size);
                var mat=r.sharedMaterial;var color=(Texture2D)mat.GetTexture("_BaseMap");
                var depth=(Texture2D)mat.GetTexture("_NativeDepthMap");
                var colors=color.GetPixels();var positions=depth.GetPixels();
                for(int i=0;i<positions.Length;i++)
                    if(positions[i].a>.5f&&positions[i].g+r.transform.parent.localPosition.y<cutHeight)
                    {colors[i]=Color.clear;positions[i]=Color.clear;}
                var image=new Texture2D(color.width,color.height,TextureFormat.RGBA32,false);
                image.SetPixels(colors);image.Apply();
                string path=AssetDatabase.GetAssetPath(color);File.WriteAllBytes(path,image.EncodeToPNG());Object.DestroyImmediate(image);AssetDatabase.ImportAsset(path);
                SaveDepth(id,depth.width,depth.height,positions);
                var baseBounds=new Bounds(new Vector3(physical.center.x,cutHeight*.5f,physical.center.z),new Vector3(physical.size.x,cutHeight,physical.size.z));
                var lower=BoxSurface(bases,id+" base",baseBounds,"wall");
                lower.transform.parent.GetComponent<Collider>().enabled=false;
            }
            // The near-wall lamp follows that wall's visibility; its real light stays active.
            var nearLamp=content.Find("Wall lamps - source anchors/Left lamp/Native surface").GetComponent<Renderer>();
            var nearWall=building.frontWalls.First(r=>r.transform.parent.name=="wall_left");
            building.frontWalls=building.frontWalls.Append(nearLamp).ToArray();
            building.frontColliders=building.frontColliders.Append(nearWall.transform.parent.GetComponent<Collider>()).ToArray();
            PrefabUtility.SaveAsPrefabAsset(root,Prefab);AssetDatabase.SaveAssets();
        }
        finally{PrefabUtility.UnloadPrefabContents(root);Sources.Clear();SourcePixels.Clear();}
    }
    [MenuItem("Tools/World Art/Inspect Completed Shop Interior 34")]
    public static void ShowInterior()
    {
        if(EditorApplication.isPlaying){PlannedPixelBuildingAuthoring.Inspect();return;}
        var root=GameObject.Find("PlannedPixelShop33");if(root==null)return;
        Selection.activeGameObject=root;var b=root.GetComponent<NativePixelBuilding>();
        SceneVisibilityManager.instance.Show(root,true);
        foreach(var r in b.roof.Concat(b.frontWalls))if(r)SceneVisibilityManager.instance.Hide(r.gameObject,true);
        var sv=SceneView.lastActiveSceneView;if(sv!=null)sv.LookAt(root.transform.TransformPoint(new Vector3(0,.8f,0)),Quaternion.Euler(30,350,0),8,true,true);
        SceneView.RepaintAll();
    }
    private static Transform Group(Transform p,string n){var go=new GameObject(n);go.transform.SetParent(p,false);return go.transform;}
    private static string Safe(string s)=>s.Replace(' ','_').Replace('-','_');
    private static void Ensure(string path){if(AssetDatabase.IsValidFolder(path))return;Ensure(Path.GetDirectoryName(path).Replace('\\','/'));AssetDatabase.CreateFolder(Path.GetDirectoryName(path).Replace('\\','/'),Path.GetFileName(path));}
}
