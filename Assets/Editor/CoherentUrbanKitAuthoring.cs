using System;
using System.Collections.Generic;
using System.Linq;
using FantasySurvival.WorldGeneration;
using Unity.AI.Navigation;
using UnityEditor;
using UnityEngine;

/// <summary>Explicit authoring of the D09 material/model catalog. Never called during map generation.</summary>
public static class CoherentUrbanKitAuthoring
{
    public const string Root = "Assets/Art/UrbanCoherent09";
    public const string StylePath = Root + "/CoherentUrbanStyle.asset";
    public const string PrefabFolder = "Assets/Prefabs/World/CoherentUrban09";
    public const string BuildingPath = PrefabFolder + "/CoherentUrbanBuilding.prefab";
    private static readonly string[] Models = {"office_desk", "storage_shelf", "retail_shelf", "workbench",
        "wardrobe", "sofa", "bed", "public_round_bin", "wheeled_dumpster", "bench", "planter"};

    public static void Create()
    {
        if(AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(StylePath)!=null ||
           AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(BuildingPath)!=null)
            throw new InvalidOperationException("D09 assets already exist. Preserve them; apply explicit scoped edits instead of regenerating.");
        Folder(PrefabFolder); Folder(Root+"/Materials");
        for(int i=0;i<16;i++) ConfigureTexture(Root+"/Surfaces/Source/tile_"+i+".png", true);
        ConfigureTexture(Root+"/Surfaces/MaterialAtlas.png", false);
        Texture2D atlas=AssetDatabase.LoadAssetAtPath<Texture2D>(Root+"/Surfaces/MaterialAtlas.png");
        var style=ScriptableObject.CreateInstance<IsometricUrbanStyle>();
        style.surfaceShader=Shader.Find(IsometricUrbanStyle.ShaderName);
        style.useMetricRoadPaint=true; style.texelsPerMetre=32;
        style.ground=Patch(atlas,1);style.sidewalk=Patch(atlas,1);style.road=Patch(atlas,0);
        style.wall=Patch(atlas,2);style.plasterWall=Patch(atlas,3);style.interior=Patch(atlas,4);
        style.roof=Patch(atlas,5);style.concrete=ColourPatch(atlas,3,32,32);
        style.glass=ColourPatch(atlas,6,20,20);
        AssignPersistentRoadPaint(style);
        style.groundVariants=Variants(atlas,13,6f,1f);
        style.sidewalkVariants=Variants(atlas,13,6f,1f);
        style.roadVariants=Variants(atlas,12,6f,1f);
        style.plainModule=null;style.windowModule=null;style.entranceModule=null;
        style.propAtlas=null;style.wallHeight=3.4f;style.wallThickness=.2f;
        style.doorWidth=2.4f;style.wallModuleWidth=2f;
        style.brickRepeatMetres=Vector2.one*2f;style.concreteRepeatMetres=Vector2.one*2f;
        if(!style.TryValidate(out string styleError))throw new InvalidOperationException(styleError);
        AssetDatabase.CreateAsset(style,StylePath);

        var materials=CreateMaterials();
        CreateTree(materials);
        var props=new UrbanBuildingProp[Models.Length];
        for(int i=0;i<Models.Length;i++)props[i]=CreateProp(Models[i],materials);
        var root=new GameObject("CoherentUrbanBuilding");
        try
        {
            var prefab=root.AddComponent<UrbanBuildingPrefab>();
            prefab.reservedMargin=1.5f;prefab.aisleWidth=1.4f;prefab.catalogRevision=3;
            prefab.propPrefabs=props;
            var rules=new List<UrbanBuildingPrefab.Rule>();
            Add(UrbanPoiKind.Medical,"administration",UrbanDecorationZone.InteriorWorkArea,1f,1,0);
            Add(UrbanPoiKind.Medical,"storage",UrbanDecorationZone.InteriorStorage,1f,2,1);
            Add(UrbanPoiKind.Medical,"waste",UrbanDecorationZone.ExteriorService,.8f,1,8);
            Add(UrbanPoiKind.Residential,"living",UrbanDecorationZone.InteriorWorkArea,1f,1,5);
            Add(UrbanPoiKind.Residential,"sleeping",UrbanDecorationZone.InteriorWorkArea,1f,1,6);
            Add(UrbanPoiKind.Residential,"wardrobe",UrbanDecorationZone.InteriorStorage,.9f,1,4);
            Add(UrbanPoiKind.Residential,"garden",UrbanDecorationZone.ExteriorService,.65f,1,10);
            Add(UrbanPoiKind.Retail,"display",UrbanDecorationZone.InteriorWorkArea,1f,3,2);
            Add(UrbanPoiKind.Retail,"stock",UrbanDecorationZone.InteriorStorage,1f,2,1);
            Add(UrbanPoiKind.Retail,"service",UrbanDecorationZone.ExteriorService,.85f,1,8);
            Add(UrbanPoiKind.Workshop,"work",UrbanDecorationZone.InteriorWorkArea,1f,2,3);
            Add(UrbanPoiKind.Workshop,"stock",UrbanDecorationZone.InteriorStorage,1f,2,1);
            Add(UrbanPoiKind.Workshop,"service",UrbanDecorationZone.ExteriorService,.9f,1,8);
            Add(UrbanPoiKind.Office,"desks",UrbanDecorationZone.InteriorWorkArea,1f,3,0);
            Add(UrbanPoiKind.Office,"filing",UrbanDecorationZone.InteriorStorage,1f,2,1);
            Add(UrbanPoiKind.Office,"outside_seat",UrbanDecorationZone.ExteriorService,.5f,1,9);
            foreach(UrbanPoiKind kind in new[]{UrbanPoiKind.Medical,UrbanPoiKind.Residential,UrbanPoiKind.Retail,UrbanPoiKind.Workshop,UrbanPoiKind.Office})
                Add(kind,"entrance_bin",UrbanDecorationZone.InteriorEntrance,.4f,1,7);
            prefab.rules=rules.ToArray();
            prefab.Snapshot(style);
            PrefabUtility.SaveAsPrefabAsset(root,BuildingPath);
            void Add(UrbanPoiKind kind,string id,UrbanDecorationZone zone,float chance,int cap,int prop)
            {
                rules.Add(new UrbanBuildingPrefab.Rule {stableId=kind.ToString().ToLowerInvariant()+"/"+id,
                    requiredPoiKind=kind,zone=zone,chance=chance,maxCount=cap,
                    choices=new[]{new UrbanBuildingPrefab.Choice{propIndex=prop,weight=1f}}});
            }
        }
        finally {UnityEngine.Object.DestroyImmediate(root);}
        AssetDatabase.SaveAssets();
    }

    private static Dictionary<string,Material> CreateMaterials()
    {
        var map=new Dictionary<string,Material>();
        Add("Urban_Wood",8,32,32,true);Add("Urban_MetalDark",9,32,32);
        Add("Urban_MetalLight",7,32,32);Add("Urban_Glass",6,20,20);
        Add("Urban_Olive",10,32,32);Add("Urban_Fabric",6,20,20);
        Add("Urban_Ceramic",3,32,32);Add("Urban_Brick",2,32,32,true);
        return map;
        void Add(string name,int tile,int x,int y,bool textured=false)
        {
            Texture2D texture=AssetDatabase.LoadAssetAtPath<Texture2D>(Root+"/Surfaces/Source/tile_"+tile+".png");
            var material=new Material(Shader.Find("Universal Render Pipeline/Lit")){name=name,enableInstancing=true};
            material.SetColor("_BaseColor",textured?Color.white:texture.GetPixel(x,63-y));
            material.SetTexture("_BaseMap",textured?texture:Texture2D.whiteTexture);
            material.SetFloat("_Smoothness",.12f);material.SetFloat("_Metallic",0f);
            AssetDatabase.CreateAsset(material,Root+"/Materials/"+name+".mat");map.Add(name,material);
        }
    }

    private static UrbanBuildingProp CreateProp(string id,Dictionary<string,Material> materials)
    {
        string path=Root+"/Models/"+id+".fbx";
        var importer=AssetImporter.GetAtPath(path) as ModelImporter;
        if(importer==null)throw new InvalidOperationException("Missing canonical model: "+path);
        importer.isReadable=true;importer.importAnimation=false;importer.globalScale=1;
        importer.useFileScale=true;importer.bakeAxisConversion=true;
        importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;
        importer.SaveAndReimport();
        var root=new GameObject(id);
        try
        {
            GameObject model=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(path),root.transform,false);
            model.name="Model";
            foreach(Renderer renderer in model.GetComponentsInChildren<Renderer>())
            {
                renderer.sharedMaterials=renderer.sharedMaterials.Select(m=>
                {
                    string key=m.name.Split('.')[0];
                    if(!materials.TryGetValue(key,out Material result))throw new InvalidOperationException("Unmapped model material: "+key);
                    return result;
                }).ToArray();
            }
            Bounds bounds=GeometryBounds(root.transform);
            // One measured canonicalization of the source asset; never a visual fitting offset.
            model.transform.localPosition-=new Vector3(bounds.center.x,bounds.min.y,bounds.center.z);
            bounds=GeometryBounds(root.transform);
            if(bounds.size.y<.3f || bounds.size.y>2.2f || bounds.size.x>2.5f || bounds.size.z>2.5f)
                throw new InvalidOperationException("Model metre conversion violates furniture scale: "+id+" "+bounds.size);
            var prop=root.AddComponent<UrbanBuildingProp>();prop.metricMesh=true;prop.catalogId=id;
            prop.physicalSize=new Vector3(bounds.extents.x*2,bounds.max.y,bounds.extents.z*2);
            prop.maxPerBuilding=id=="public_round_bin"||id=="wheeled_dumpster"?1:3;
            prop.allowedZones=id=="wheeled_dumpster"||id=="bench"||id=="planter"?UrbanDecorationZone.ExteriorService:
                id=="public_round_bin"?UrbanDecorationZone.InteriorEntrance:
                id=="storage_shelf"||id=="wardrobe"?UrbanDecorationZone.InteriorStorage:UrbanDecorationZone.InteriorWorkArea;
            prop.placementNotes="D09: canonical metre model; +Z front; actual geometry and POI zone rule own placement.";
            var box=root.GetComponent<BoxCollider>();box.center=Vector3.up*prop.physicalSize.y*.5f;box.size=prop.physicalSize;
            var nav=root.GetComponent<NavMeshModifier>();nav.overrideArea=true;nav.area=1;root.tag="Obstacle";
            if(!prop.TryValidate(out string error))throw new InvalidOperationException(id+": "+error);
            var saved=PrefabUtility.SaveAsPrefabAsset(root,PrefabFolder+"/"+id+".prefab");
            return saved.GetComponent<UrbanBuildingProp>();
        }
        finally {UnityEngine.Object.DestroyImmediate(root);}
    }

    private static void CreateTree(Dictionary<string,Material> materials)
    {
        string path=Root+"/Models/street_tree.fbx";
        var importer=AssetImporter.GetAtPath(path) as ModelImporter;
        if(importer==null)throw new InvalidOperationException("Missing canonical street tree.");
        importer.isReadable=true;importer.importAnimation=false;importer.globalScale=1;
        importer.useFileScale=true;importer.bakeAxisConversion=true;
        importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;importer.SaveAndReimport();
        GameObject root=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(path));
        try
        {
            root.name="StreetTreeVisual";
            foreach(Renderer renderer in root.GetComponentsInChildren<Renderer>())
                renderer.sharedMaterials=renderer.sharedMaterials.Select(m=>materials[m.name.Split('.')[0]]).ToArray();
            if(Mathf.Abs(GeometryBounds(root.transform).size.y-4f)>.02f)
                throw new InvalidOperationException("Street tree import metre conversion failed.");
            PrefabUtility.SaveAsPrefabAsset(root,PrefabFolder+"/StreetTreeVisual.prefab");
        }
        finally {UnityEngine.Object.DestroyImmediate(root);}
    }

    public static Bounds GeometryBounds(Transform root)
    {
        Bounds bounds=default;bool first=true;
        foreach(MeshFilter filter in root.GetComponentsInChildren<MeshFilter>(true))
        {
            Matrix4x4 matrix=root.worldToLocalMatrix*filter.transform.localToWorldMatrix;
            foreach(Vector3 vertex in filter.sharedMesh.vertices)
            {
                Vector3 p=matrix.MultiplyPoint3x4(vertex);
                if(first){bounds=new Bounds(p,Vector3.zero);first=false;}else bounds.Encapsulate(p);
            }
        }
        if(first)throw new InvalidOperationException("Model has no mesh vertices.");
        return bounds;
    }

    private static void ConfigureTexture(string path,bool repeat)
    {
        var importer=AssetImporter.GetAtPath(path) as TextureImporter;
        if(importer==null)throw new InvalidOperationException("Missing original texture: "+path);
        importer.textureType=TextureImporterType.Default;importer.filterMode=FilterMode.Point;
        importer.wrapMode=repeat?TextureWrapMode.Repeat:TextureWrapMode.Clamp;
        importer.mipmapEnabled=false;importer.isReadable=true;importer.npotScale=TextureImporterNPOTScale.None;
        importer.textureCompression=TextureImporterCompression.Uncompressed;importer.SaveAndReimport();
    }
    private static IsometricUrbanStyle.AtlasPatch Patch(Texture2D atlas,int index)
    {
        float x=index%4*68+2-.5f,y=index/4*68+2-.5f;
        return RectPatch(atlas,x,y,64,64);
    }
    private static IsometricUrbanStyle.AtlasPatch ColourPatch(Texture2D atlas,int index,int px,int py)
    {
        // A uniform 2x2 colour sample is a palette material, not a stretched depicted object.
        return RectPatch(atlas,index%4*68+2+px,index/4*68+2+py,1,1);
    }
    public static void AssignPersistentRoadPaint(IsometricUrbanStyle style)
    {
        const string path=Root+"/Surfaces/PaintWhite.asset";
        var texture=AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        if(texture==null)
        {
            texture=new Texture2D(2,2,TextureFormat.RGBA32,false){name="Road paint white",filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp};
            texture.SetPixels(new[]{Color.white,Color.white,Color.white,Color.white});texture.Apply();
            AssetDatabase.CreateAsset(texture,path);
        }
        // Built-in whiteTexture is transient and cannot survive style asset serialization.
        style.yellowLine=RectPatch(texture,0,0,1,1);
        style.whiteLine=RectPatch(texture,0,0,1,1);
        style.crosswalk=RectPatch(texture,0,0,1,1);
        EditorUtility.SetDirty(style);
    }
    private static IsometricUrbanStyle.AtlasPatch RectPatch(Texture2D texture,float x,float y,float w,float h)=>
        new IsometricUrbanStyle.AtlasPatch(new Vector2(x,y+h),new Vector2(x,y),new Vector2(x+w,y),new Vector2(x+w,y+h)){texture=texture};
    private static IsometricUrbanStyle.SurfaceVariantCatalog Variants(Texture2D atlas,int index,float baseWeight,float weight)=>
        new IsometricUrbanStyle.SurfaceVariantCatalog {baseWeight=baseWeight,variants=new[]{
            new IsometricUrbanStyle.WeightedSurfaceVariant{name="Compatible material variant",patch=Patch(atlas,index),weight=weight}}};
    private static void Folder(string path)
    {
        if(AssetDatabase.IsValidFolder(path))return;
        int slash=path.LastIndexOf('/');Folder(path.Substring(0,slash));AssetDatabase.CreateFolder(path.Substring(0,slash),path.Substring(slash+1));
    }
}
