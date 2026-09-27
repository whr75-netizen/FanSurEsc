using System;
using System.Collections.Generic;
using System.IO;
using FantasySurvival.WorldGeneration;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

/// <summary>Consumes the B32 layout and B33 native sprites. Does not generate a layout or repaint art.</summary>
public static class PlannedPixelBuildingAuthoring
{
    public const string Folder = "Assets/Art/PlannedPixelBuilding33";
    public const string PrefabPath = "Assets/Prefabs/World/PlannedPixelShop33.prefab";
    public const string PlanPath = "docs/artifacts/building32/layout-plan.json";
    public static readonly float Ppu = 16f * Mathf.Sqrt(2f);
    public static readonly float VerticalPixelsPerMetre = Ppu * Mathf.Cos(30f * Mathf.Deg2Rad);
    public static readonly float WallHeight = 48f / VerticalPixelsPerMetre;
    private const float FloorY = 0.015f;
    private static readonly Vector3 ViewRight = new Vector3(1, 0, -1).normalized;
    private static readonly Vector3 ViewForward = Quaternion.Euler(30,45,0) * Vector3.forward;

    [Serializable] private sealed class RectSpec { public string id; public float[] rect_xz; }
    [Serializable] private sealed class FloorSpec { public float[] rect_xz; }
    [Serializable] private sealed class UseSpec { public string id; public float[] access_xz; }
    [Serializable] private sealed class FixtureSpec
    {
        public string id;
        public float[] rect_xz;
        public float height_m;
        public string facing;
        public UseSpec[] use_areas;
    }
    [Serializable] private sealed class Plan
    {
        public string id;
        public FloorSpec floor;
        public RectSpec[] walls;
        public RectSpec[] partitions;
        public FixtureSpec[] fixtures;
    }

    [MenuItem("Tools/World Art/Build Planned Pixel Shop 33")]
    public static void Build()
    {
        throw new NotSupportedException("B33_FORCED_GRID_RETIRED: this builder consumes rejected forced-size art. Existing scene and Inspect remain available.");
    }

    // Historical implementation retained for diagnosis, not an authoring entry point.
    private static void BuildRetiredForReference()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Build only in Edit Mode.");
        var scene = SceneManager.GetActiveScene();
        if (scene.name != "GameMap1") throw new InvalidOperationException("Open GameMap1 first.");
        if (AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath) != null ||
            GameObject.Find("PlannedPixelShop33") != null)
            throw new InvalidOperationException("Existing B33 is preserved. Edit its source or prefab explicitly.");

        // Validate every external input before making any scene or asset changes.
        var plan = JsonUtility.FromJson<Plan>(File.ReadAllText(PlanPath));
        if (plan == null || plan.floor == null || plan.fixtures == null || plan.walls == null || plan.partitions == null)
            throw new InvalidDataException("Incomplete layout source.");
        CheckRect(plan.floor.rect_xz, "floor");
        float[] bounds = plan.floor.rect_xz;
        int nx = Mathf.RoundToInt((bounds[2]-bounds[0])/2f);
        int nz = Mathf.RoundToInt((bounds[3]-bounds[1])/2f);
        if (Mathf.Abs(nx*2-(bounds[2]-bounds[0])) > .0001f || Mathf.Abs(nz*2-(bounds[3]-bounds[1])) > .0001f)
            throw new InvalidDataException("Floor dimensions must use complete 2m source tiles.");
        var required = new Dictionary<string, Vector2Int>
        {
            {"floor", new Vector2Int(64,32)}, {"wall", new Vector2Int(64,64)},
            {"lamp", new Vector2Int(16,24)}
        };
        foreach (var fixture in plan.fixtures)
        {
            CheckRect(fixture.rect_xz, fixture.id);
            if (fixture.height_m <= 0) throw new InvalidDataException("Invalid height: " + fixture.id);
            required[ArtName(fixture.id)] = new Vector2Int(64,64);
        }
        foreach (var wall in plan.walls) CheckRect(wall.rect_xz, wall.id);
        foreach (var wall in plan.partitions) CheckRect(wall.rect_xz, wall.id);
        foreach (var input in required) ValidatePng(Folder + "/" + input.Key + ".png", input.Value);

        EnsureFolder(Folder + "/Meshes");
        EnsureFolder(Folder + "/Materials");
        EnsureFolder(Folder + "/Derived");
        foreach (var input in required) ImportNative(Folder + "/" + input.Key + ".png");
        var floorTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(Folder + "/floor.png");
        // The two atlas halves are integer crops. Source RGB/alpha and texel dimensions stay intact.
        var leftWallTexture = CropAtlasHalf("wall_left", 0);
        var rightWallTexture = CropAtlasHalf("wall_right", 32);

        var root = new GameObject("PlannedPixelShop33");
        Undo.RegisterCreatedObjectUndo(root, "Assemble planned pixel shop");
        root.transform.SetPositionAndRotation(new Vector3(-16,0,9), Quaternion.Euler(0,305,0));
        var building = root.AddComponent<NativePixelBuilding>();
        building.interior = new Bounds(new Vector3((bounds[0]+bounds[2])*.5f,WallHeight*.5f,(bounds[1]+bounds[3])*.5f),
            new Vector3(bounds[2]-bounds[0],WallHeight,bounds[3]-bounds[1]));
        var floors = Group(root.transform, "Floor - native full rectangles");
        var walls = Group(root.transform, "Walls - layout solids");
        var furniture = Group(root.transform, "Fixtures - layout footprints");
        var roof = Group(root.transform, "Roof - hidden in interior Scene view");
        var frontRenderers = new List<Renderer>(); var frontColliders = new List<Collider>();
        var backRenderers = new List<Renderer>(); var backColliders = new List<Collider>();
        var roofRenderers = new List<Renderer>(); var roofColliders = new List<Collider>();

        var floorMesh = SaveMesh("floor_full_rect", new[]
        {
            new Vector3(-2,0,0), new Vector3(0,0,-2), new Vector3(2,0,0), new Vector3(0,0,2)
        }, UnitUv());
        var floorMaterial = SaveMaterial("floor", floorTexture, floorMesh);
        var roofMaterial = SaveMaterial("roof", floorTexture, floorMesh);
        roofMaterial.SetColor("_BaseColor", new Color(.58f,.64f,.70f,1));
        for (int x=0;x<nx;x++) for (int z=0;z<nz;z++)
        {
            var p = new Vector3(bounds[0]+1+2*x,FloorY,bounds[1]+1+2*z);
            Surface("Floor_"+x+"_"+z,floors,p,floorMesh,floorMaterial);
            var tile = Surface("Roof_"+x+"_"+z,roof,p+Vector3.up*WallHeight,floorMesh,roofMaterial);
            roofRenderers.Add(tile);
            var box = tile.gameObject.AddComponent<BoxCollider>();
            box.center = Vector3.up*.04f; box.size = new Vector3(2,.08f,2);
            roofColliders.Add(box);
        }
        var floorCollider = floors.gameObject.AddComponent<BoxCollider>();
        floorCollider.center = new Vector3((bounds[0]+bounds[2])*.5f,-.005f,(bounds[1]+bounds[3])*.5f);
        floorCollider.size = new Vector3(bounds[2]-bounds[0],.04f,bounds[3]-bounds[1]);

        foreach (var wall in plan.walls)
        {
            bool rear = wall.id == "wall_back" || wall.id == "wall_right";
            AddWall(walls,wall,leftWallTexture,rightWallTexture,
                rear?backRenderers:frontRenderers,rear?backColliders:frontColliders);
        }
        foreach (var wall in plan.partitions)
            AddWall(walls,wall,leftWallTexture,rightWallTexture,frontRenderers,frontColliders);
        foreach (var fixture in plan.fixtures) AddFixture(furniture, fixture);
        var lamps = Group(root.transform,"Wall lamps - existing stepped light owner");
        AddLamp(lamps,"Back lamp",new Vector3(.7f,WallHeight-.12f,3.9f),true);
        AddLamp(lamps,"Left lamp",new Vector3(-4.9f,WallHeight-.12f,-.55f),false);

        building.frontWalls = frontRenderers.ToArray(); building.frontColliders = frontColliders.ToArray();
        building.backWalls = backRenderers.ToArray(); building.backColliders = backColliders.ToArray();
        building.roof = roofRenderers.ToArray(); building.roofColliders = roofColliders.ToArray();
        // Root configures the existing NativePixelBuilding's native-grid/lighting fields.
        // Serialized assignment keeps this builder compatible with the current component schema.
        var serialized = new SerializedObject(building);
        var grid = serialized.FindProperty("useNativePixelGrid");
        if (grid != null) grid.boolValue = true;
        var ppu = serialized.FindProperty("nativePixelsPerUnit");
        if (ppu != null) ppu.floatValue = Ppu;
        serialized.ApplyModifiedPropertiesWithoutUndo();

        PrefabUtility.SaveAsPrefabAssetAndConnect(root,PrefabPath,InteractionMode.AutomatedAction);
        foreach (var oldRoot in scene.GetRootGameObjects())
            if (oldRoot.name == "NativePixelShop31" && oldRoot.activeSelf)
            {
                Undo.RecordObject(oldRoot,"Preserve superseded pixel shop");
                oldRoot.SetActive(false);
            }
        AssetDatabase.SaveAssets();
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        Selection.activeGameObject = root;
        ShowInterior();
        NativePixelBuildingAuthoring.AlignSceneViewToGameplayCamera();
        Debug.Log("B33 assembled from "+plan.id+"; fixtures="+plan.fixtures.Length+"; native PPU="+Ppu);
    }

    [MenuItem("Tools/World Art/Show Planned Shop Interior in Scene View")]
    public static void ShowInterior()
    {
        var root = GameObject.Find("PlannedPixelShop33");
        if (root == null) return;
        var building = root.GetComponent<NativePixelBuilding>();
        foreach (var renderer in building.roof) if(renderer!=null) SceneVisibilityManager.instance.Hide(renderer.gameObject,true);
        foreach (var renderer in building.frontWalls) if(renderer!=null) SceneVisibilityManager.instance.Hide(renderer.gameObject,true);
        SceneView.RepaintAll();
    }

    [MenuItem("Tools/World Art/Inspect Planned Pixel Shop 33")]
    public static void Inspect()
    {
        var root=GameObject.Find("PlannedPixelShop33");
        if(root==null){Debug.LogWarning("Open GameMap1 with B33 first.");return;}
        Selection.activeGameObject=root;
        if(!EditorApplication.isPlaying)
        {
            ShowInterior();NativePixelBuildingAuthoring.AlignSceneViewToGameplayCamera();return;
        }
        var shell=FantasySurvival.SceneFlow.PersistentGameplayShell.Instance;
        if(shell==null)return;
        var movement=shell.PlayerTransform.GetComponent<PlayerMovement>();
        if(!movement.TryTeleport(root.transform.TransformPoint(new Vector3(0,.55f,-.4f)),
            shell.PlayerTransform.rotation,out var error))Debug.LogError(error);
    }

    private static void AddLamp(Transform parent,string id,Vector3 topAnchor,bool backWall)
    {
        var lamp=Group(parent,id);lamp.localPosition=topAnchor;
        var texture=AssetDatabase.LoadAssetAtPath<Texture2D>(Folder+"/lamp.png");
        // Place the image on its supporting wall plane. A free billboard would extend
        // 0.25m behind this wall and clip; inverse projection preserves the same screen
        // pixels and top anchor without moving the wall or inventing a per-part offset.
        Vector3 Point(float u,float v)
        {
            float screenX=u-texture.width*.5f,screenY=-v;
            float along=screenX/16f;
            return backWall?new Vector3(along,(screenY-8*along)/VerticalPixelsPerMetre,0)
                :new Vector3(0,(screenY+8*along)/VerticalPixelsPerMetre,-along);
        }
        string key=backWall?"lamp_back":"lamp_left";
        var mesh=SaveMesh(key,new[]{Point(0,texture.height),Point(texture.width,texture.height),
            Point(texture.width,0),Point(0,0)},UnitUv());
        Surface("Sprite - wall mounted native rectangle",lamp,Vector3.zero,mesh,SaveMaterial(key,texture,mesh));
        var glass=Group(lamp,"Glass centre - dynamic light");
        glass.localPosition=Vector3.up*(-texture.height/VerticalPixelsPerMetre+.3f);
        var light=glass.gameObject.AddComponent<SteppedLocalLight>();
        var settings=new SerializedObject(light);
        settings.FindProperty("color").colorValue=new Color(1f,.72f,.38f,1f);
        settings.FindProperty("radius").floatValue=4.5f;
        settings.FindProperty("intensity").floatValue=.24f;
        settings.FindProperty("surfaceBands").intValue=3;
        settings.FindProperty("haloBands").intValue=3;
        settings.FindProperty("haloStrength").floatValue=.05f;
        settings.FindProperty("normalInfluence").floatValue=0;
        settings.FindProperty("worldCellSize").floatValue=.125f;
        settings.ApplyModifiedPropertiesWithoutUndo();
    }

    public static void AddFoundationToExisting()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit Mode required.");
        var root=PrefabUtility.LoadPrefabContents(PrefabPath);
        try
        {
            if(root.transform.Find("Floor foundation - wall footprint")!=null)
                throw new InvalidOperationException("Foundation already exists; preserve it.");
            var plan=JsonUtility.FromJson<Plan>(File.ReadAllText(PlanPath));
            float xmin=plan.floor.rect_xz[0],zmin=plan.floor.rect_xz[1],xmax=plan.floor.rect_xz[2],zmax=plan.floor.rect_xz[3];
            foreach(var wall in plan.walls)
            {
                xmin=Mathf.Min(xmin,wall.rect_xz[0]);zmin=Mathf.Min(zmin,wall.rect_xz[1]);
                xmax=Mathf.Max(xmax,wall.rect_xz[2]);zmax=Mathf.Max(zmax,wall.rect_xz[3]);
            }
            float width=xmax-xmin,depth=zmax-zmin;
            int w=Mathf.CeilToInt(16*(width+depth)),h=Mathf.CeilToInt(8*(width+depth));
            var source=new Texture2D(2,2,TextureFormat.RGBA32,false);
            source.LoadImage(File.ReadAllBytes(Folder+"/floor.png"));
            var palette=new List<Color32>();
            foreach(var color in source.GetPixels32())if(color.a>127)palette.Add(color);
            palette.Sort((a,b)=>(a.r*299+a.g*587+a.b*114).CompareTo(b.r*299+b.g*587+b.b*114));
            var representative=palette[palette.Count/2];representative.a=255;
            UnityEngine.Object.DestroyImmediate(source);
            var texture=new Texture2D(w,h,TextureFormat.RGBA32,false);
            var pixels=new Color32[w*h];
            for(int y=0;y<h;y++)for(int x=0;x<w;x++)
            {
                float sx=x+.5f-w*.5f,sy=y+.5f-h*.5f;
                float wx=sx/32f+sy/16f,wz=-sx/32f+sy/16f;
                if(Mathf.Abs(wx)<=width*.5f && Mathf.Abs(wz)<=depth*.5f)pixels[y*w+x]=representative;
            }
            texture.SetPixels32(pixels);texture.Apply();
            string path=Folder+"/Derived/foundation.png";
            File.WriteAllBytes(path,texture.EncodeToPNG());UnityEngine.Object.DestroyImmediate(texture);
            AssetDatabase.ImportAsset(path);ImportNative(path);
            texture=AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            Vector3 Point(float u,float v)
            {
                float sx=u*w-w*.5f,sy=v*h-h*.5f;
                return new Vector3(sx/32f+sy/16f,0,-sx/32f+sy/16f);
            }
            var mesh=SaveMesh("foundation",new[]{Point(0,0),Point(1,0),Point(1,1),Point(0,1)},UnitUv());
            var material=SaveMaterial("foundation",texture,mesh);
            // Coplanar base drawn before the authored tiles: no arbitrary height offset.
            material.renderQueue=(int)RenderQueue.Geometry-1;
            // The underlay must not occlude coplanar snapped tile depths.
            material.SetFloat("_ZWrite",0);
            Surface("Floor foundation - wall footprint",root.transform,
                new Vector3((xmin+xmax)*.5f,FloorY,(zmin+zmax)*.5f),mesh,material);
            PrefabUtility.SaveAsPrefabAsset(root,PrefabPath);
        }
        finally{PrefabUtility.UnloadPrefabContents(root);}
        AssetDatabase.SaveAssets();
        EditorSceneManager.SaveScene(SceneManager.GetActiveScene());
    }

    private static void AddWall(Transform parent, RectSpec wall, Texture2D left, Texture2D right,
        List<Renderer> renderers, List<Collider> colliders)
    {
        float[] r = wall.rect_xz;
        float width=r[2]-r[0],depth=r[3]-r[1];
        bool alongX=width>=depth;
        var group=Group(parent,wall.id);
        var box=group.gameObject.AddComponent<BoxCollider>();
        box.center=new Vector3((r[0]+r[2])*.5f,FloorY+WallHeight*.5f,(r[1]+r[3])*.5f);
        box.size=new Vector3(width,WallHeight,depth);
        // All lengths are plan metres. Only the visible crop end is rounded to a source
        // column (1/16m along the wall); the authoritative collision rectangle is unchanged.
        float length=alongX?width:depth;
        int columns=Mathf.Max(1,Mathf.RoundToInt(length*16f));
        for(int start=0;start<columns;start+=32)
        {
            int count=Mathf.Min(32,columns-start);
            float endU=count/32f;
            Vector3 Point(float u,float v) => alongX
                ? new Vector3(2*u,(64*v-16*u)/VerticalPixelsPerMetre,0)
                : new Vector3(0,(64*v-16*(1-u))/VerticalPixelsPerMetre,-2*u);
            var uv=new[]{Vector2.zero,new Vector2(endU,0),new Vector2(endU,1),Vector2.up};
            var mesh=SaveMesh(wall.id+"_"+start,new[]{Point(0,0),Point(endU,0),Point(endU,1),Point(0,1)},uv);
            var material=SaveMaterial(wall.id+"_"+start,alongX?left:right,mesh);
            var p=alongX?new Vector3(r[0]+start/16f,FloorY,(r[1]+r[3])*.5f)
                :new Vector3((r[0]+r[2])*.5f,FloorY,r[3]-start/16f);
            renderers.Add(Surface("SourceColumns_"+start+"_"+count,group,p,mesh,material));
            // Fader binds one renderer/collider pair per surface; a segment's collider
            // is shared by its visual tiles, never duplicated physics.
            colliders.Add(box);
        }
    }

    private static void AddFixture(Transform parent, FixtureSpec spec)
    {
        float[] r=spec.rect_xz;
        float w=r[2]-r[0],d=r[3]-r[1];
        var item=Group(parent,spec.id+" - "+spec.facing);
        item.localPosition=new Vector3((r[0]+r[2])*.5f,FloorY,(r[1]+r[3])*.5f);
        var texture=AssetDatabase.LoadAssetAtPath<Texture2D>(Folder+"/"+ArtName(spec.id)+".png");
        float pivotX=texture.width*.5f,pivotY=texture.height-4*(w+d);
        float raise=(texture.height-pivotY)/VerticalPixelsPerMetre;
        Vector3 rayShift=-ViewForward*(raise/-ViewForward.y);
        Vector3 Point(float u,float v) => ViewRight*((u-pivotX)/Ppu)+
            Vector3.up*((pivotY-v)/VerticalPixelsPerMetre)+rayShift;
        var mesh=SaveMesh(spec.id,new[]{Point(0,texture.height),Point(texture.width,texture.height),
            Point(texture.width,0),Point(0,0)},UnitUv());
        var material=SaveMaterial(spec.id,texture,mesh);
        Surface("Sprite - native full rectangle",item,Vector3.zero,mesh,material);
        var box=item.gameObject.AddComponent<BoxCollider>();
        box.center=Vector3.up*spec.height_m*.5f; box.size=new Vector3(w,spec.height_m,d);
        AddContactShadow(item,spec.id,w,d);
        if(spec.use_areas!=null) foreach(var use in spec.use_areas)
        {
            var point=Group(parent,"Access - "+use.id);
            point.localPosition=new Vector3(use.access_xz[0],FloorY,use.access_xz[1]);
        }
    }

    private static void AddContactShadow(Transform parent,string id,float width,float depth)
    {
        int w=Mathf.CeilToInt(16*(width+depth))+2,h=Mathf.CeilToInt(8*(width+depth))+2;
        var texture=new Texture2D(w,h,TextureFormat.RGBA32,false);
        var pixels=new Color32[w*h];
        for(int y=0;y<h;y++) for(int x=0;x<w;x++)
        {
            float sx=x+.5f-w*.5f,sy=y+.5f-h*.5f;
            float wx=sx/32f+sy/16f,wz=-sx/32f+sy/16f;
            if(Mathf.Abs(wx)<=width*.5f && Mathf.Abs(wz)<=depth*.5f)
                pixels[y*w+x]=new Color32(34,26,43,72);
        }
        texture.SetPixels32(pixels); texture.Apply();
        string path=Folder+"/Derived/"+id+"_contact.png";
        File.WriteAllBytes(path,texture.EncodeToPNG()); UnityEngine.Object.DestroyImmediate(texture);
        AssetDatabase.ImportAsset(path); ImportNative(path);
        texture=AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        Vector3 Point(float u,float v)
        {
            float x=u*w-w*.5f,y=v*h-h*.5f;
            return new Vector3(x/32f+y/16f,.002f,-x/32f+y/16f);
        }
        var mesh=SaveMesh(id+"_contact",new[]{Point(0,0),Point(1,0),Point(1,1),Point(0,1)},UnitUv());
        var material=SaveMaterial(id+"_contact",texture,mesh);
        material.SetFloat("_ZWrite",0);
        material.SetFloat("_SrcBlend",(float)BlendMode.SrcAlpha);
        material.SetFloat("_DstBlend",(float)BlendMode.OneMinusSrcAlpha);
        material.renderQueue=(int)RenderQueue.AlphaTest+1;
        Surface("Contact - footprint mask",parent,Vector3.zero,mesh,material);
    }

    private static Material SaveMaterial(string id,Texture2D texture,Mesh mesh)
    {
        var material=new Material(Shader.Find("FantasySurvival/World/Isometric Atlas Surface")){name=id};
        material.SetTexture("_BaseMap",texture);material.SetFloat("_VertexAtlasUv",1);
        material.SetFloat("_MetricLighting",0);material.SetFloat("_NativeGridEnabled",1);
        var p=mesh.vertices;var uv=mesh.uv;
        float du1=uv[1].x-uv[0].x,dv1=uv[1].y-uv[0].y,du2=uv[2].x-uv[0].x,dv2=uv[2].y-uv[0].y;
        float determinant=du1*dv2-du2*dv1;
        if(Mathf.Abs(determinant)<.000001f)throw new InvalidDataException("Singular sprite UV: "+id);
        var u=((p[1]-p[0])*dv2-(p[2]-p[0])*dv1)/determinant;
        var v=((p[2]-p[0])*du1-(p[1]-p[0])*du2)/determinant;
        material.SetVector("_NativeGridOriginOS",p[0]-u*uv[0].x-v*uv[0].y);
        material.SetVector("_NativeGridTexelUOS",u/texture.width);
        material.SetVector("_NativeGridTexelVOS",v/texture.height);
        AssetDatabase.CreateAsset(material,Folder+"/Materials/"+id+".mat");return material;
    }

    private static Mesh SaveMesh(string id,Vector3[] vertices,Vector2[] uv)
    {
        var mesh=new Mesh{name=id,vertices=vertices,triangles=new[]{0,1,2,0,2,3}};
        var uv3=new List<Vector3>();foreach(var p in uv)uv3.Add(new Vector3(p.x,p.y,1));
        mesh.SetUVs(0,uv3);mesh.RecalculateNormals();mesh.RecalculateBounds();
        // Shader translations are <= one source texel including common camera phase.
        var b=mesh.bounds;b.Expand(2f/Ppu);mesh.bounds=b;
        AssetDatabase.CreateAsset(mesh,Folder+"/Meshes/"+id+".asset");return mesh;
    }
    private static Renderer Surface(string name,Transform parent,Vector3 position,Mesh mesh,Material material)
    {
        var go=Group(parent,name).gameObject;go.transform.localPosition=position;
        go.AddComponent<MeshFilter>().sharedMesh=mesh;
        var renderer=go.AddComponent<MeshRenderer>();renderer.sharedMaterial=material;
        renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;return renderer;
    }
    private static Transform Group(Transform parent,string name)
    {
        var go=new GameObject(name);go.transform.SetParent(parent,false);return go.transform;
    }
    private static Vector2[] UnitUv()=>new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up};
    private static string ArtName(string id)=>id=="checkout"?"counter":id=="display_island"?"island":id;
    private static void CheckRect(float[] r,string id)
    {
        if(r==null||r.Length!=4||!(r[2]>r[0])||!(r[3]>r[1]))throw new InvalidDataException("Invalid rectangle: "+id);
    }
    private static void ValidatePng(string path,Vector2Int expected)
    {
        var texture=new Texture2D(2,2,TextureFormat.RGBA32,false);
        try
        {
            if(!texture.LoadImage(File.ReadAllBytes(path))||texture.width!=expected.x||texture.height!=expected.y)
                throw new InvalidDataException(path+" must be "+expected.x+"x"+expected.y+" native pixels.");
        }
        finally{UnityEngine.Object.DestroyImmediate(texture);}
    }
    private static Texture2D CropAtlasHalf(string id,int startX)
    {
        var input=new Texture2D(2,2,TextureFormat.RGBA32,false);
        input.LoadImage(File.ReadAllBytes(Folder+"/wall.png"));
        var cropped=new Texture2D(32,64,TextureFormat.RGBA32,false);
        cropped.SetPixels(input.GetPixels(startX,0,32,64));cropped.Apply();
        string path=Folder+"/Derived/"+id+".png";
        File.WriteAllBytes(path,cropped.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(input);UnityEngine.Object.DestroyImmediate(cropped);
        AssetDatabase.ImportAsset(path);ImportNative(path);return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }
    private static void ImportNative(string path)
    {
        var importer=(TextureImporter)AssetImporter.GetAtPath(path);
        if(importer==null){AssetDatabase.ImportAsset(path);importer=(TextureImporter)AssetImporter.GetAtPath(path);}
        importer.textureType=TextureImporterType.Sprite;importer.spriteImportMode=SpriteImportMode.Single;
        importer.spritePixelsPerUnit=Ppu;importer.filterMode=FilterMode.Point;importer.mipmapEnabled=false;
        importer.textureCompression=TextureImporterCompression.Uncompressed;importer.npotScale=TextureImporterNPOTScale.None;
        importer.wrapMode=TextureWrapMode.Clamp;importer.alphaIsTransparency=true;importer.SaveAndReimport();
    }
    private static void EnsureFolder(string path)
    {
        if(AssetDatabase.IsValidFolder(path))return;
        string parent=Path.GetDirectoryName(path).Replace('\\','/');
        EnsureFolder(parent);AssetDatabase.CreateFolder(parent,Path.GetFileName(path));
    }
}
