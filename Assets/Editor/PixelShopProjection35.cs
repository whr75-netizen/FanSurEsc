using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FantasySurvival.WorldGeneration;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

/// <summary>Imports canonical plane rasters and their matching positions into the existing shop.</summary>
public static class PixelShopProjection35
{
    public const string Folder = "Assets/Art/PixelShopInterior35";
    public const string GroupName = "Fixtures35 - visible fronts and role plan";
    public const string DetailsGroupName = "Details35 - wall and support attachments";
    private const string Artifacts = "docs/artifacts/building35";
    private static readonly Quaternion View = Quaternion.Euler(30,45,0);
    private static readonly Vector3 Right = View*Vector3.right, Up = View*Vector3.up;
    [Serializable] private class Entry { public string id, folder, receipt; }
    [Serializable] private class Manifest { public Entry[] assets; }
    [Serializable] private class Receipt { public int width,height; public float ppu,left,top,support_height; }
    [Serializable] private class Instance { public string id,asset,asset_variant,role,support;public float[] position,collider_size; }
    [Serializable] private class Placement { public float nativePpu;public Instance[] instances; }
    [Serializable] private class BuildReport
    {
        public string producer="UnityEditor.PixelShopProjection35",prefab=PixelShopInteriorCompletion.Prefab;
        public int instances,assetTypes,sourceDepthMismatches;public float commonPpu;
        public string[] instanceNames;
    }
    private sealed class Surface { public Mesh mesh; public Material material;public float supportHeight; }
    [Serializable] private class MetricEntry { public float width_x,depth_z,crate_height_y,display_content_collision_height; }
    [Serializable] private class MetricAssets { public MetricEntry appletray; }
    [Serializable] private class MetricCatalog { public float nativePpu; public MetricAssets assets; }

    public static void Apply()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit mode required.");
        if(AssetDatabase.IsValidFolder(Folder))throw new InvalidOperationException("B35 already exists; do not overwrite a completed import.");
        var manifest=JsonUtility.FromJson<Manifest>(File.ReadAllText(Artifacts+"/production-manifest.json"));
        var plan=JsonUtility.FromJson<Placement>(File.ReadAllText(Artifacts+"/placement.json"));
        if(plan.nativePpu!=127||plan.instances.Length<18)throw new InvalidDataException("Expected the declared role plan and native density.");
        Ensure(Folder);Ensure(Folder+"/Color");Ensure(Folder+"/Depth");Ensure(Folder+"/Meshes");Ensure(Folder+"/Materials");
        int mismatch;
        var surfaces=ImportAssets(manifest,plan.nativePpu,out mismatch);
        if(mismatch!=0)throw new InvalidDataException("Color/depth mask mismatch: "+mismatch);
        var root=PrefabUtility.LoadPrefabContents(PixelShopInteriorCompletion.Prefab);
        try
        {
            var content=root.transform.Find(PixelShopInteriorCompletion.ContentName);
            if(content==null||content.Find(GroupName)!=null)throw new InvalidOperationException("Expected preserved B34 structure and no B35 group.");
            var old=content.Find("Fixtures - role plan");old.gameObject.SetActive(false);
            var group=new GameObject(GroupName).transform;group.SetParent(content,false);
            var placed=new Dictionary<string,Transform>();var supportHeights=new Dictionary<string,float>();
            foreach(var item in plan.instances)
            {
                string assetId=string.IsNullOrEmpty(item.asset_variant)?item.asset:item.asset_variant;
                if(!surfaces.TryGetValue(assetId,out var surface))throw new InvalidDataException("Missing asset "+assetId);
                var t=new GameObject(item.id).transform;t.SetParent(group,false);t.localPosition=V(item.position)+Vector3.up*.015f;
                if(item.support!="floor"&&placed.TryGetValue(item.support,out var support))
                {
                    if(supportHeights[item.support]<=0)throw new InvalidDataException("No declared support plane: "+item.support);
                    var p=t.localPosition;p.y=support.localPosition.y+supportHeights[item.support];t.localPosition=p;
                }
                placed.Add(item.id,t);supportHeights.Add(item.id,surface.supportHeight);
                AttachSurface(t,item,surface);
            }
            PrefabUtility.SaveAsPrefabAsset(root,PixelShopInteriorCompletion.Prefab);AssetDatabase.SaveAssets();
            var report=new BuildReport{instances=plan.instances.Length,assetTypes=surfaces.Count,sourceDepthMismatches=mismatch,
                commonPpu=plan.nativePpu,instanceNames=plan.instances.Select(i=>i.id).ToArray()};
            File.WriteAllText(Artifacts+"/unity-build.json",JsonUtility.ToJson(report,true));
        }
        finally{PrefabUtility.UnloadPrefabContents(root);}
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        PixelShopInteriorCompletion.ShowInterior();
    }

    public static void AppendDetails()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit mode required.");
        const string path=Artifacts+"/details";
        var manifest=JsonUtility.FromJson<Manifest>(File.ReadAllText(path+"/production-manifest.json"));
        var plan=JsonUtility.FromJson<Placement>(File.ReadAllText(path+"/placement.json"));
        if(plan.nativePpu!=127||plan.instances.Length!=6)throw new InvalidDataException("Expected six declared details at common PPU.");
        var root=PrefabUtility.LoadPrefabContents(PixelShopInteriorCompletion.Prefab);
        try
        {
            var content=root.transform.Find(PixelShopInteriorCompletion.ContentName);
            var fixtures=content==null?null:content.Find(GroupName);
            if(fixtures==null||fixtures.childCount!=20||content.Find(DetailsGroupName)!=null)
                throw new InvalidOperationException("Expected approved 20 fixtures and no detail group.");
            if(manifest.assets.Any(e=>File.Exists(Folder+"/Color/"+e.id+".png")))
                throw new InvalidOperationException("Detail assets already exist; inspect prior execution instead of overwriting.");
            var counter=fixtures.Find("checkout");
            var trayMesh=AssetDatabase.LoadAssetAtPath<Mesh>(Folder+"/Meshes/appletray.asset");
            var trayMaterial=AssetDatabase.LoadAssetAtPath<Material>(Folder+"/Materials/appletray.mat");
            if(counter==null||trayMesh==null||trayMaterial==null)
                throw new InvalidDataException("Existing counter and approved tray references are required.");
            int mismatch;
            var surfaces=ImportAssets(manifest,plan.nativePpu,out mismatch);
            if(mismatch!=0)throw new InvalidDataException("Detail color/depth mask mismatch: "+mismatch);
            surfaces.Add("appletray",new Surface{mesh=trayMesh,material=trayMaterial});
            var counterInfo=JsonUtility.FromJson<Receipt>(File.ReadAllText(Artifacts+"/projected-new/empty_counter/receipt.json"));
            var group=new GameObject(DetailsGroupName).transform;group.SetParent(content,false);
            foreach(var item in plan.instances)
            {
                var t=new GameObject(item.id).transform;t.SetParent(group,false);t.localPosition=V(item.position);
                if(item.support=="checkout")
                {
                    var p=t.localPosition;p.y=counter.localPosition.y+counterInfo.support_height;t.localPosition=p;
                }
                AttachSurface(t,item,surfaces[item.asset]);
            }
            PrefabUtility.SaveAsPrefabAsset(root,PixelShopInteriorCompletion.Prefab);AssetDatabase.SaveAssets();
            File.WriteAllText(path+"/unity-build.json",JsonUtility.ToJson(new BuildReport{instances=group.childCount,
                assetTypes=surfaces.Count,sourceDepthMismatches=mismatch,commonPpu=plan.nativePpu,
                instanceNames=plan.instances.Select(i=>i.id).ToArray()},true));
        }
        finally{PrefabUtility.UnloadPrefabContents(root);}
        PixelShopInteriorCompletion.ShowInterior();
    }

    private static void AttachSurface(Transform t,Instance item,Surface surface)
    {
        if(item.collider_size!=null&&item.collider_size.Length==3&&item.collider_size.All(x=>x>0))
        {
            var box=t.gameObject.AddComponent<BoxCollider>();box.size=V(item.collider_size);box.center=Vector3.up*box.size.y*.5f;
        }
        var visual=new GameObject("Native surface");visual.transform.SetParent(t,false);
        visual.AddComponent<MeshFilter>().sharedMesh=surface.mesh;
        var renderer=visual.AddComponent<MeshRenderer>();renderer.sharedMaterial=surface.material;
        renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;
    }

    public static void ApplyMetricTray()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit mode required.");
        const string path=Artifacts+"/tray-composite";
        var manifest=JsonUtility.FromJson<Manifest>(File.ReadAllText(path+"/production-manifest.json"));
        var catalog=JsonUtility.FromJson<MetricCatalog>(File.ReadAllText("Tools/Building35/metric-catalog.json"));
        var metric=catalog.assets.appletray;
        if(catalog.nativePpu!=127||manifest.assets.Length!=1||metric.width_x<=0||metric.depth_z<=0)
            throw new InvalidDataException("Declared crate dimensions and common density required.");
        var root=PrefabUtility.LoadPrefabContents(PixelShopInteriorCompletion.Prefab);
        try
        {
            var content=root.transform.Find(PixelShopInteriorCompletion.ContentName);
            string[] paths={GroupName+"/island_apple_tray_left",GroupName+"/island_apple_tray_right",DetailsGroupName+"/checkout_produce"};
            var targets=paths.Select(p=>content.Find(p)).ToArray();
            if(targets.Any(t=>t==null||t.GetComponent<BoxCollider>()==null||t.Find("Native surface")==null))
                throw new InvalidDataException("Expected existing three trays; do not create replacements.");
            if(manifest.assets.Any(e=>File.Exists(Folder+"/Color/"+e.id+".png")))
                throw new InvalidOperationException("Metric tray already imported; inspect prior execution.");
            int mismatch;var surfaces=ImportAssets(manifest,catalog.nativePpu,out mismatch);
            if(mismatch!=0)throw new InvalidDataException("Metric tray source/depth mismatch");
            var surface=surfaces[manifest.assets[0].id];
            foreach(var target in targets)
            {
                var visual=target.Find("Native surface");
                visual.GetComponent<MeshFilter>().sharedMesh=surface.mesh;
                visual.GetComponent<MeshRenderer>().sharedMaterial=surface.material;
                var box=target.GetComponent<BoxCollider>();box.size=new Vector3(metric.width_x,metric.display_content_collision_height,metric.depth_z);
                box.center=Vector3.up*box.size.y*.5f;
            }
            PrefabUtility.SaveAsPrefabAsset(root,PixelShopInteriorCompletion.Prefab);AssetDatabase.SaveAssets();
            File.WriteAllText(path+"/unity-build.json",JsonUtility.ToJson(new BuildReport{instances=targets.Length,
                assetTypes=1,sourceDepthMismatches=mismatch,commonPpu=catalog.nativePpu,instanceNames=targets.Select(t=>t.name).ToArray()},true));
        }
        finally{PrefabUtility.UnloadPrefabContents(root);}
        PixelShopInteriorCompletion.ShowInterior();
    }

    private static Dictionary<string,Surface> ImportAssets(Manifest manifest,float ppu,out int mismatch)
    {
        var surfaces=new Dictionary<string,Surface>();mismatch=0;
        foreach(var entry in manifest.assets)
        {
            var info=JsonUtility.FromJson<Receipt>(File.ReadAllText(entry.receipt));
            if(info.ppu!=ppu)throw new InvalidDataException(entry.id+": inconsistent PPU");
            string colorPath=Folder+"/Color/"+entry.id+".png",depthPath=Folder+"/Depth/"+entry.id+".exr";
            File.Copy(entry.folder+"/native.png",colorPath,false);
            var raw=File.ReadAllBytes(entry.folder+"/positions.rgba32f");
            if(raw.Length!=info.width*info.height*16)throw new InvalidDataException(entry.id+": raw length");
            var tmp=new Texture2D(info.width,info.height,TextureFormat.RGBAFloat,false,true);
            tmp.LoadRawTextureData(raw);tmp.Apply();
            File.WriteAllBytes(depthPath,tmp.EncodeToEXR(Texture2D.EXRFlags.OutputAsFloat|Texture2D.EXRFlags.CompressZIP));Object.DestroyImmediate(tmp);
            AssetDatabase.ImportAsset(colorPath);AssetDatabase.ImportAsset(depthPath);Configure(colorPath,false);Configure(depthPath,true);
            var color=AssetDatabase.LoadAssetAtPath<Texture2D>(colorPath);var depth=AssetDatabase.LoadAssetAtPath<Texture2D>(depthPath);
            var c=color.GetPixels();var d=depth.GetPixels();
            for(int n=0;n<c.Length;n++)if((c[n].a>.1f)!=(d[n].a>.5f))mismatch++;
            surfaces.Add(entry.id,MakeSurface(entry.id,color,depth,info));
        }
        return surfaces;
    }

    private static Surface MakeSurface(string id,Texture2D color,Texture2D depth,Receipt info)
    {
        Vector3 P(float x,float y)=>Right*(info.left+x/info.ppu)+Up*(info.top+y/info.ppu);
        var mesh=new Mesh{name=id,vertices=new[]{P(0,-info.height),P(info.width,-info.height),P(info.width,0),P(0,0)},triangles=new[]{0,1,2,0,2,3}};
        mesh.SetUVs(0,new List<Vector3>{new(0,0,1),new(1,0,1),new(1,1,1),new(0,1,1)});mesh.RecalculateNormals();mesh.RecalculateBounds();
        var bounds=mesh.bounds;bounds.Expand(2f/info.ppu);mesh.bounds=bounds;
        AssetDatabase.CreateAsset(mesh,Folder+"/Meshes/"+id+".asset");
        var material=new Material(Shader.Find("FantasySurvival/World/Isometric Atlas Surface")){name=id};
        material.SetTexture("_BaseMap",color);material.SetTexture("_NativeDepthMap",depth);material.SetFloat("_NativeDepthEnabled",1);
        material.SetFloat("_VertexAtlasUv",1);material.SetFloat("_NativeGridEnabled",1);material.SetFloat("_MetricLighting",0);
        material.SetVector("_NativeGridOriginOS",mesh.vertices[0]);material.SetVector("_NativeGridTexelUOS",Right/info.ppu);material.SetVector("_NativeGridTexelVOS",Up/info.ppu);
        AssetDatabase.CreateAsset(material,Folder+"/Materials/"+id+".mat");return new Surface{mesh=mesh,material=material,supportHeight=info.support_height};
    }
    private static Vector3 V(float[] a)=>new(a[0],a[1],a[2]);
    private static void Ensure(string path)
    {
        if(AssetDatabase.IsValidFolder(path))return;
        string parent=Path.GetDirectoryName(path).Replace('\\','/');Ensure(parent);AssetDatabase.CreateFolder(parent,Path.GetFileName(path));
    }
    private static void Configure(string path,bool depth)
    {
        var i=(TextureImporter)AssetImporter.GetAtPath(path);i.textureType=TextureImporterType.Default;i.sRGBTexture=!depth;
        i.filterMode=FilterMode.Point;i.wrapMode=TextureWrapMode.Clamp;i.mipmapEnabled=false;i.npotScale=TextureImporterNPOTScale.None;
        i.textureCompression=TextureImporterCompression.Uncompressed;i.isReadable=true;i.maxTextureSize=4096;i.alphaIsTransparency=false;
        if(depth){var ps=i.GetDefaultPlatformTextureSettings();ps.format=TextureImporterFormat.RGBAFloat;i.SetPlatformTextureSettings(ps);}
        i.SaveAndReimport();
    }
}
