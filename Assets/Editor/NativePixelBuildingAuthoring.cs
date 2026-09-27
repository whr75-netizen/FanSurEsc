using System;
using System.Collections.Generic;
using System.IO;
using FantasySurvival.WorldGeneration;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

public static class NativePixelBuildingAuthoring
{
    public const string Folder = "Assets/Art/NativePixelBuilding31";
    public const string PrefabPath = "Assets/Prefabs/World/NativePixelShop31.prefab";
    public const float Cell = 2f;
    public static readonly float Ppu = 16f * Mathf.Sqrt(2f);
    public static readonly float Height = 48f / (Ppu * Mathf.Cos(30f * Mathf.Deg2Rad));
    private static readonly Vector3 Right = new Vector3(1, 0, -1).normalized;
    [Serializable] private class Entry { public string name; public string file; public float[] pivot_top_left_pixels; }
    [Serializable] private class Manifest { public Entry[] entries; }
    private static readonly Dictionary<string, Material> Materials = new Dictionary<string, Material>();
    private static readonly Dictionary<string, Mesh> PropMeshes = new Dictionary<string, Mesh>();
    private static readonly Dictionary<string, Entry> Entries = new Dictionary<string, Entry>();

    [MenuItem("Tools/World Art/Inspect Native Pixel Shop 31")]
    public static void Inspect()
    {
        var building = UnityEngine.Object.FindFirstObjectByType<NativePixelBuilding>();
        if (building == null) { Debug.LogWarning("Open GameMap1 first."); return; }
        Selection.activeGameObject = building.gameObject;
        if (!EditorApplication.isPlaying)
        {
            SceneView.lastActiveSceneView?.FrameSelected();
            return;
        }
        var shell = FantasySurvival.SceneFlow.PersistentGameplayShell.Instance;
        if (shell == null) return;
        var movement = shell.PlayerTransform.GetComponent<PlayerMovement>();
        if (!movement.TryTeleport(building.transform.TransformPoint(new Vector3(0,.55f,-.4f)),
            shell.PlayerTransform.rotation, out var error)) Debug.LogError(error);
    }

    [MenuItem("Tools/World Art/Build Native Pixel Shop 31")]
    public static void Build()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Build in Edit Mode only.");
        var scene = SceneManager.GetActiveScene();
        if (scene.name != "GameMap1") throw new InvalidOperationException("Open GameMap1 first.");
        if (GameObject.Find("NativePixelShop31") != null || AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath) != null)
            throw new InvalidOperationException("Existing building preserved. Edit the prefab instead of regenerating it.");
        Directory.CreateDirectory(Folder + "/Materials"); Directory.CreateDirectory(Folder + "/Meshes");
        Directory.CreateDirectory("Assets/Prefabs/World");
        AssetDatabase.Refresh();
        Materials.Clear(); PropMeshes.Clear(); Entries.Clear();
        var manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(Folder + "/manifest.json"));
        foreach (var entry in manifest.entries)
        {
            Entries.Add(entry.name, entry);
            string path = Folder + "/" + entry.file;
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = Ppu;
            importer.filterMode = FilterMode.Point;
            importer.mipmapEnabled = false;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.alphaIsTransparency = true;
            importer.SaveAndReimport();
            var material = new Material(Shader.Find("FantasySurvival/World/Isometric Atlas Surface"));
            material.name = entry.name;
            material.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(path));
            material.SetFloat("_MetricLighting", 0);
            material.SetFloat("_VertexAtlasUv", 1);
            AssetDatabase.CreateAsset(material, Folder + "/Materials/" + entry.name + ".mat");
            Materials.Add(entry.name, material);
        }

        var root = new GameObject("NativePixelShop31"); Undo.RegisterCreatedObjectUndo(root, "Native pixel shop");
        var surfaces = root.AddComponent<NativePixelBuilding>();
        var floor = new GameObject("Floor - native 64x32 tiles").transform; floor.SetParent(root.transform, false);
        var exterior = new GameObject("Exterior").transform; exterior.SetParent(root.transform, false);
        var props = new GameObject("ShopFurniture").transform; props.SetParent(root.transform, false);
        var roofParent = new GameObject("FlatRoof - cut away indoors").transform; roofParent.SetParent(root.transform, false);
        var floorMesh = FloorMesh();
        var roofRenderers = new List<Renderer>(); var roofColliders = new List<Collider>();
        for (int x = 0; x < 5; x++) for (int z = 0; z < 4; z++)
        {
            var position = new Vector3(-4 + 2*x, .015f, -3 + 2*z);
            Surface("Floor_"+x+"_"+z, floor, position, floorMesh, "floor_wood");
            var roofPiece = Surface("Roof_"+x+"_"+z, roofParent, position + Vector3.up*Height, floorMesh, "floor_wood");
            var collider = roofPiece.gameObject.AddComponent<BoxCollider>();
            collider.size = new Vector3(2, .08f, 2); collider.center = Vector3.up * .04f;
            roofRenderers.Add(roofPiece); roofColliders.Add(collider);
        }
        var floorCollider = floor.gameObject.AddComponent<BoxCollider>();
        floorCollider.center = new Vector3(0, -.005f, 0); floorCollider.size = new Vector3(10, .04f, 8);
        var frontR = new List<Renderer>(); var frontC = new List<Collider>();
        var backR = new List<Renderer>(); var backC = new List<Collider>();
        for (int x=0; x<5; x++)
        {
            Wall(exterior, new Vector3(-4+2*x, .015f, 4), true, backR, backC);
            if (x != 2) Wall(exterior, new Vector3(-4+2*x, .015f, -4), true, frontR, frontC);
        }
        for (int z=0; z<4; z++)
        {
            Wall(exterior, new Vector3(5, .015f, -3+2*z), false, backR, backC);
            Wall(exterior, new Vector3(-5, .015f, -3+2*z), false, frontR, frontC);
        }
        // Rear stock bay: a partition with a 2m passage, not an inaccessible enclosed decoration.
        var stock = new GameObject("StockBay - 4m x 4m").transform; stock.SetParent(root.transform, false);
        Wall(stock, new Vector3(2, .015f, 0), true, frontR, frontC);
        Wall(stock, new Vector3(4, .015f, 0), true, frontR, frontC);
        Wall(stock, new Vector3(1, .015f, 3), false, backR, backC);

        Prop(props, "counter", "Checkout", -2.9f, -1.6f, 2.2f, 1.0f, 1.0f);
        Prop(props, "chair_left", "ClerkChair", -2.8f, .0f, .6f, .65f, .95f);
        Prop(props, "bookshelf_front", "Bookshelf_1", -4.1f, 2.8f, .65f, 1.5f, 2.1f);
        Prop(props, "bookshelf_front", "Bookshelf_2", -2.25f, 2.8f, .65f, 1.5f, 2.1f);
        Prop(props, "wood_table", "DisplayTable", 2.5f, -2.15f, 1.6f, 1.6f, .85f);
        Prop(props, "pot", "PotteryDisplay", 2.5f, -2.15f, .5f, .5f, .65f, .85f, false);
        ProjectSupportedSprite(props.Find("PotteryDisplay/Sprite"), props.Find("DisplayTable/Sprite"));
        Prop(props, "chair_right", "CustomerChair", 4.1f, -2.1f, .6f, .65f, .95f);
        Prop(props, "flower_vase", "EntryFlowers", -1.35f, -3.35f, .45f, .45f, 1.3f);
        Prop(props, "storage_chest", "StockChest_1", 2.1f, 2.9f, .8f, .6f, .65f);
        Prop(props, "storage_chest_red", "StockChest_2", 3.5f, 2.9f, .8f, .6f, .65f);
        Prop(props, "barrel", "StockBarrel_1", 4.15f, 1.3f, .7f, .7f, 1.0f);
        Prop(props, "barrel", "StockBarrel_2", 2.85f, 1.3f, .7f, .7f, 1.0f);
        Prop(props, "fireplace", "UnlitStove", -4.0f, .6f, .9f, .9f, 1.8f);
        Prop(props, "pot", "EntryPot", 1.45f, -4.9f, .55f, .55f, .6f);
        Prop(props, "flower_vase", "ExteriorFlowers", -1.5f, -4.9f, .45f, .45f, 1.3f);
        for (int z=0; z<3; z++) Surface("EntryPath_"+z, exterior, new Vector3(0,.02f,-5-2*z),floorMesh,"floor_wood");
        surfaces.frontWalls = frontR.ToArray(); surfaces.frontColliders = frontC.ToArray();
        surfaces.backWalls = backR.ToArray(); surfaces.backColliders = backC.ToArray();
        surfaces.roof = roofRenderers.ToArray(); surfaces.roofColliders = roofColliders.ToArray();
        root.transform.SetPositionAndRotation(new Vector3(-16, 0, 9), Quaternion.Euler(0,305,0));
        var prefab = PrefabUtility.SaveAsPrefabAssetAndConnect(root, PrefabPath, InteractionMode.AutomatedAction);
        AssetDatabase.SaveAssets(); EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
        Selection.activeGameObject = prefab;
        Debug.Log("B31 native sprite building saved: " + PrefabPath + "; PPU=" + Ppu + "; wall height=" + Height);
    }

    private static Mesh SaveMesh(string name, Vector3[] vertices, Vector2[] uv)
    {
        var mesh = new Mesh { name = name, vertices = vertices, triangles = new[]{0,1,2,0,2,3} };
        var uv3 = new List<Vector3>(); foreach(var p in uv) uv3.Add(new Vector3(p.x,p.y,1));
        mesh.SetUVs(0,uv3); mesh.RecalculateNormals(); mesh.RecalculateBounds();
        AssetDatabase.CreateAsset(mesh, Folder+"/Meshes/"+name+".asset"); return mesh;
    }
    private static Mesh FloorMesh() => SaveMesh("Floor", new[]{new Vector3(-1,0,-1),new Vector3(1,0,-1),new Vector3(1,0,1),new Vector3(-1,0,1)},
        new[]{new Vector2(.5f,0),new Vector2(1,.5f),new Vector2(.5f,1),new Vector2(0,.5f)});
    private static Renderer Surface(string name, Transform parent, Vector3 position, Mesh mesh, string material)
    {
        var go=new GameObject(name); go.transform.SetParent(parent,false); go.transform.localPosition=position;
        go.AddComponent<MeshFilter>().sharedMesh=mesh;
        var renderer=go.AddComponent<MeshRenderer>(); renderer.sharedMaterial=Materials[material];
        renderer.shadowCastingMode=ShadowCastingMode.Off; renderer.receiveShadows=false; return renderer;
    }
    private static void Wall(Transform parent, Vector3 position, bool alongX, List<Renderer> renderers, List<Collider> colliders)
    {
        string name=alongX?"wall_brick_left":"wall_brick_right";
        if(!PropMeshes.TryGetValue(name,out var mesh))
        {
            var a=alongX?Vector3.left:Vector3.forward; var b=-a;
            mesh=SaveMesh(name,new[]{a,b,b+Vector3.up*Height,a+Vector3.up*Height},
                alongX?new[]{new Vector2(0,0),new Vector2(1,.25f),new Vector2(1,1),new Vector2(0,.75f)}:
                new[]{new Vector2(0,.25f),new Vector2(1,0),new Vector2(1,.75f),new Vector2(0,1)});
            PropMeshes.Add(name,mesh);
        }
        var renderer=Surface(name+"_"+position.x+"_"+position.z,parent,position,mesh,name);
        var box=renderer.gameObject.AddComponent<BoxCollider>(); box.center=Vector3.up*Height*.5f;
        box.size=alongX?new Vector3(2,Height,.15f):new Vector3(.15f,Height,2);
        renderers.Add(renderer);colliders.Add(box);
    }
    private static void Prop(Transform parent, string asset, string name, float x, float z, float width, float depth, float height, float supportY=0, bool collide=true)
    {
        if(!PropMeshes.TryGetValue(asset,out var mesh))
        {
            var tex=(Texture2D)Materials[asset].GetTexture("_BaseMap"); var pivot=Entries[asset].pivot_top_left_pixels;
            Vector3 Point(float u,float v) => Right*((u-pivot[0])/Ppu)+Vector3.up*((pivot[1]-v)/(Ppu*Mathf.Cos(30*Mathf.Deg2Rad)));
            mesh=SaveMesh(asset,new[]{Point(0,tex.height),Point(tex.width,tex.height),Point(tex.width,0),Point(0,0)},new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up});
            PropMeshes.Add(asset,mesh);
        }
        var item=new GameObject(name);item.transform.SetParent(parent,false);item.transform.localPosition=new Vector3(x,.015f+supportY,z);
        // The authored lowest support is the footprint's near corner, not its centre.
        Surface("Sprite",item.transform,new Vector3(-width*.5f,0,-depth*.5f),mesh,asset);
        if(collide){var box=item.AddComponent<BoxCollider>();box.center=Vector3.up*height*.5f;box.size=new Vector3(width,height,depth);}
    }

    public static void ProjectSupportedSprite(Transform child, Transform support)
    {
        // A stacked 2D prop shares its support's depth plane. Shift along the viewing ray,
        // preserving every screen coordinate; 1mm resolves only the coplanar depth tie.
        var away = support.root.TransformDirection(new Vector3(1,0,1).normalized);
        var ray = support.root.rotation * Quaternion.Euler(30,45,0) * Vector3.forward;
        float distance = Vector3.Dot(child.position-support.position, away) / Vector3.Dot(ray,away);
        child.position -= ray * (distance + .001f);
    }
}
