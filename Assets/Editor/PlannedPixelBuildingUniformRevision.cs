using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

/// <summary>Changes B33 source references in place; layout, renderer identities and scene owners survive.</summary>
public static class PlannedPixelBuildingUniformRevision
{
    public const string Folder = "Assets/Art/PlannedPixelBuilding33Uniform";
    private const string ManifestPath = "docs/artifacts/building33/uniform-art-manifest.json";
    public static readonly float Ppu = 32f * Mathf.Sqrt(2f);
    private static readonly float Vertical = Ppu * Mathf.Cos(30f * Mathf.Deg2Rad);
    private static readonly Vector3 Right = new Vector3(1, 0, -1).normalized;
    private static readonly Vector3 Forward = Quaternion.Euler(30, 45, 0) * Vector3.forward;
    [Serializable] private sealed class Target { public float uniform_source_scale; }
    [Serializable] private sealed class Art
    {
        public string id, normalized_path, normalized_sha256;
        public int[] normalized_dimensions, pre_normalization_crop_dimensions;
        public Target target;
    }
    [Serializable] private sealed class Atlas { public string path, sha256; public int[] dimensions; }
    [Serializable] private sealed class Manifest
    {
        public string schema, layout_sha256;
        public float native_pixels_per_unit;
        public Art[] assets;
        public Atlas wall_atlas;
    }
    [Serializable] private sealed class Rect { public float[] rect_xz; }
    [Serializable] private sealed class Fixture { public string id, facing; public float[] rect_xz; public float height_m; }
    [Serializable] private sealed class Plan { public Rect floor; public Rect[] walls; public Fixture[] fixtures; }

    [MenuItem("Tools/World Art/Apply B33 Uniform Source Revision")]
    public static void Apply()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Edit Mode required.");
        var manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(ManifestPath));
        var plan = JsonUtility.FromJson<Plan>(File.ReadAllText(PlannedPixelBuildingAuthoring.PlanPath));
        if (manifest == null || manifest.schema != "building33-uniform-art/1" || manifest.assets == null ||
            Mathf.Abs(manifest.native_pixels_per_unit-Ppu) > .0001f ||
            manifest.layout_sha256 != Hash(PlannedPixelBuildingAuthoring.PlanPath))
            throw new InvalidDataException("Uniform source manifest/PPU/layout mismatch.");
        foreach (var art in manifest.assets)
        {
            ValidatePng(art.normalized_path, art.normalized_dimensions, art.normalized_sha256);
            if (art.id == "floor" || art.id.StartsWith("wall_")) continue;
            var source = art.pre_normalization_crop_dimensions;
            if (art.target == null || art.target.uniform_source_scale <= 0 || source == null || source.Length != 2 ||
                Mathf.Abs(art.normalized_dimensions[0]-source[0]*art.target.uniform_source_scale) > 1.0001f ||
                Mathf.Abs(art.normalized_dimensions[1]-source[1]*art.target.uniform_source_scale) > 1.0001f)
                throw new InvalidDataException("Source must use one isotropic sampling scale: " + art.id);
        }
        ValidatePng(manifest.wall_atlas.path, manifest.wall_atlas.dimensions, manifest.wall_atlas.sha256);
        var root = PrefabUtility.LoadPrefabContents(PlannedPixelBuildingAuthoring.PrefabPath);
        try
        {
            var building = root.GetComponent<NativePixelBuilding>();
            if (building == null || Mathf.Abs(building.nativePixelsPerUnit-Ppu) < .0001f)
                throw new InvalidOperationException("Missing B33 component or uniform revision already applied.");
            var fixtures = root.transform.Find("Fixtures - layout footprints");
            // Validate all referenced geometry before creating derived assets or changing the prefab.
            foreach (var spec in plan.fixtures)
            {
                var item = fixtures.Find(spec.id+" - "+spec.facing);
                if (item == null || item.GetComponent<BoxCollider>() == null ||
                    item.Find("Sprite - native full rectangle") == null || item.Find("Contact - footprint mask") == null)
                    throw new InvalidDataException("Missing existing fixture: " + spec.id);
                var record = Array.Find(manifest.assets, a => a.id == ArtName(spec.id));
                if (record == null || record.normalized_dimensions[0] > 32f*(Width(spec)+Depth(spec))+.0001f)
                    throw new InvalidDataException("Source exceeds allocated footprint: " + spec.id);
            }
            foreach (string dir in new[]{"Derived", "Meshes", "Materials"}) EnsureFolder(Folder+"/"+dir);
            foreach (var art in manifest.assets) ImportNative(art.normalized_path);
            ImportNative(manifest.wall_atlas.path);
            var wall = Decode(manifest.wall_atlas.path);
            if (wall.width != 128 || wall.height != 128) throw new InvalidDataException("Wall atlas contract changed.");
            for (int half=0; half<2; half++)
            {
                var crop = new Texture2D(64,128,TextureFormat.RGBA32,false);
                crop.SetPixels(wall.GetPixels(half*64,0,64,128)); crop.Apply();
                SaveTexture(half==0 ? "wall_left" : "wall_right",crop);
            }
            Object.DestroyImmediate(wall);
            var assigned = new HashSet<Renderer>();
            foreach (var spec in plan.fixtures)
            {
                var item = fixtures.Find(spec.id+" - "+spec.facing);
                var texture = Load(ArtName(spec.id));
                float factor = texture.width/(32f*(Width(spec)+Depth(spec)));
                float width = Width(spec)*factor, depth = Depth(spec)*factor;
                float pivotY = texture.height-8f*(width+depth);
                float raise = (texture.height-pivotY)/Vertical;
                Vector3 shift = -Forward*(raise/-Forward.y);
                Vector3 Point(float x,float y) => Right*((x-texture.width*.5f)/Ppu)+
                    Vector3.up*((pivotY-y)/Vertical)+shift;
                var mesh = Quad(new[]{Point(0,texture.height),Point(texture.width,texture.height),
                    Point(texture.width,0),Point(0,0)});
                Assign(item.Find("Sprite - native full rectangle").GetComponent<Renderer>(),texture,mesh,spec.id,assigned);
                var box = item.GetComponent<BoxCollider>();
                float height = Mathf.Min(spec.height_m,Mathf.Max(.01f,(texture.height-.5f*texture.width)/Vertical));
                box.center = Vector3.up*height*.5f; box.size = new Vector3(width,height,depth);
                int w = Mathf.CeilToInt(32f*(width+depth))+2, h = Mathf.CeilToInt(16f*(width+depth))+2;
                mesh = GroundQuad(w,h,.002f);
                var mask = GroundMask(spec.id+"_contact",mesh,w,h,width,depth,new Color32(34,26,43,72));
                Assign(item.Find("Contact - footprint mask").GetComponent<Renderer>(),mask,mesh,spec.id+"_contact",assigned);
                Debug.Log(spec.id+": footprint factor="+factor+", collider proxy="+box.size+
                    ". Bounds inference only; generated perspective is not certified geometry.");
            }
            // Supporting wall, top anchor and projected width stay fixed; native height follows source aspect.
            foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
            {
                if (assigned.Contains(renderer)) continue;
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter == null || filter.sharedMesh == null || renderer.sharedMaterial == null)
                    throw new InvalidDataException("Unexpected B33 renderer: "+renderer.name);
                string oldPath = AssetDatabase.GetAssetPath(renderer.sharedMaterial.GetTexture("_BaseMap"));
                string id = Path.GetFileNameWithoutExtension(oldPath);
                var mesh = Object.Instantiate(filter.sharedMesh);
                Texture2D texture;
                if (id == "foundation")
                {
                    float xmin=plan.floor.rect_xz[0],zmin=plan.floor.rect_xz[1],xmax=plan.floor.rect_xz[2],zmax=plan.floor.rect_xz[3];
                    foreach(var r in plan.walls) { xmin=Mathf.Min(xmin,r.rect_xz[0]);zmin=Mathf.Min(zmin,r.rect_xz[1]);
                        xmax=Mathf.Max(xmax,r.rect_xz[2]);zmax=Mathf.Max(zmax,r.rect_xz[3]); }
                    var original = (Texture2D)renderer.sharedMaterial.GetTexture("_BaseMap");
                    texture = GroundMask("foundation",mesh,original.width*2,original.height*2,xmax-xmin,zmax-zmin,FloorMedian());
                }
                else if (id == "lamp")
                {
                    texture=Load("lamp"); bool back=renderer.transform.parent.name=="Back lamp";
                    Vector3 Point(float u,float v)
                    {
                        float along=(u-texture.width*.5f)/32f;
                        return back?new Vector3(along,(-v-16*along)/Vertical,0):new Vector3(0,(-v+16*along)/Vertical,-along);
                    }
                    Object.DestroyImmediate(mesh);
                    mesh=Quad(new[]{Point(0,texture.height),Point(texture.width,texture.height),Point(texture.width,0),Point(0,0)});
                    renderer.transform.parent.Find("Glass centre - dynamic light").localPosition=
                        Vector3.up*(-texture.height/Vertical+.3f);
                }
                else texture=Load(id,id.StartsWith("wall_") ? "/Derived/" : "/");
                Assign(renderer,texture,mesh,"surface_"+assigned.Count,assigned);
            }
            building.nativePixelsPerUnit=Ppu; building.useNativePixelGrid=true;
            PrefabUtility.SaveAsPrefabAsset(root,PlannedPixelBuildingAuthoring.PrefabPath);
            AssetDatabase.SaveAssets();
            Debug.Log("B33 uniform source references saved in the existing prefab. Scene/player/camera untouched; PPU="+Ppu);
        }
        finally { PrefabUtility.UnloadPrefabContents(root); }
    }

    private static void Assign(Renderer renderer,Texture2D texture,Mesh mesh,string id,HashSet<Renderer> assigned)
    {
        var material=new Material(renderer.sharedMaterial){name=id+"_uniform"};
        mesh.name=id+"_uniform"; material.SetTexture("_BaseMap",texture);
        var p=mesh.vertices;var uv=mesh.uv;
        float du1=uv[1].x-uv[0].x,dv1=uv[1].y-uv[0].y,du2=uv[2].x-uv[0].x,dv2=uv[2].y-uv[0].y;
        float determinant=du1*dv2-du2*dv1;
        if(Mathf.Abs(determinant)<.000001f)throw new InvalidDataException("Singular native UV: "+id);
        var u=((p[1]-p[0])*dv2-(p[2]-p[0])*dv1)/determinant;
        var v=((p[2]-p[0])*du1-(p[1]-p[0])*du2)/determinant;
        material.SetVector("_NativeGridOriginOS",p[0]-u*uv[0].x-v*uv[0].y);
        material.SetVector("_NativeGridTexelUOS",u/texture.width);
        material.SetVector("_NativeGridTexelVOS",v/texture.height);
        material.SetFloat("_NativeGridEnabled",1);
        AssetDatabase.CreateAsset(mesh,AssetDatabase.GenerateUniqueAssetPath(Folder+"/Meshes/"+id+".asset"));
        AssetDatabase.CreateAsset(material,AssetDatabase.GenerateUniqueAssetPath(Folder+"/Materials/"+id+".mat"));
        renderer.GetComponent<MeshFilter>().sharedMesh=mesh;renderer.sharedMaterial=material;assigned.Add(renderer);
    }
    private static Mesh Quad(Vector3[] vertices)
    {
        var mesh=new Mesh{vertices=vertices,triangles=new[]{0,1,2,0,2,3}};
        mesh.SetUVs(0,new List<Vector3>{new(0,0,1),new(1,0,1),new(1,1,1),new(0,1,1)});
        mesh.RecalculateNormals();mesh.RecalculateBounds();var bounds=mesh.bounds;bounds.Expand(2/Ppu);mesh.bounds=bounds;return mesh;
    }
    private static Mesh GroundQuad(int w,int h,float y)
    {
        Vector3 Point(float u,float v){float sx=(u-.5f)*w,sy=(v-.5f)*h;return new Vector3(sx/64+sy/32,y,-sx/64+sy/32);}
        return Quad(new[]{Point(0,0),Point(1,0),Point(1,1),Point(0,1)});
    }
    private static Texture2D GroundMask(string id,Mesh mesh,int w,int h,float width,float depth,Color32 color)
    {
        var pixels=new Color32[w*h];var p=mesh.vertices;
        for(int y=0;y<h;y++)for(int x=0;x<w;x++)
        {
            Vector3 world=p[0]+(p[1]-p[0])*((x+.5f)/w)+(p[3]-p[0])*((y+.5f)/h);
            if(Mathf.Abs(world.x)<=width*.5f && Mathf.Abs(world.z)<=depth*.5f)pixels[y*w+x]=color;
        }
        var texture=new Texture2D(w,h,TextureFormat.RGBA32,false);texture.SetPixels32(pixels);texture.Apply();return SaveTexture(id,texture);
    }
    private static Color32 FloorMedian()
    {
        var source=Decode(Folder+"/floor.png");var pixels=new List<Color32>();
        foreach(var color in source.GetPixels32())if(color.a>127)pixels.Add(color);
        Object.DestroyImmediate(source);pixels.Sort((a,b)=>(a.r*299+a.g*587+a.b*114).CompareTo(b.r*299+b.g*587+b.b*114));
        if(pixels.Count==0)throw new InvalidDataException("Empty floor source.");var value=pixels[pixels.Count/2];value.a=255;return value;
    }
    private static Texture2D SaveTexture(string id,Texture2D texture)
    {
        string path=Folder+"/Derived/"+id+".png";
        if(File.Exists(path))throw new InvalidOperationException("Preserving existing derived output: "+path);
        File.WriteAllBytes(path,texture.EncodeToPNG());Object.DestroyImmediate(texture);ImportNative(path);return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }
    private static void ImportNative(string path)
    {
        AssetDatabase.ImportAsset(path);var importer=(TextureImporter)AssetImporter.GetAtPath(path);
        importer.textureType=TextureImporterType.Sprite;importer.spriteImportMode=SpriteImportMode.Single;
        importer.spritePixelsPerUnit=Ppu;importer.filterMode=FilterMode.Point;importer.mipmapEnabled=false;
        importer.textureCompression=TextureImporterCompression.Uncompressed;importer.npotScale=TextureImporterNPOTScale.None;
        importer.wrapMode=TextureWrapMode.Clamp;importer.alphaIsTransparency=true;importer.SaveAndReimport();
    }
    private static Texture2D Load(string id,string sub="/") => AssetDatabase.LoadAssetAtPath<Texture2D>(Folder+sub+id+".png") ?? throw new FileNotFoundException(id);
    private static Texture2D Decode(string path)
    {
        var texture=new Texture2D(2,2,TextureFormat.RGBA32,false);
        if(!texture.LoadImage(File.ReadAllBytes(path))){Object.DestroyImmediate(texture);throw new InvalidDataException(path);}return texture;
    }
    private static void ValidatePng(string path,int[] dimensions,string hash)
    {
        if(string.IsNullOrEmpty(path)||!path.StartsWith(Folder+"/",StringComparison.Ordinal)||dimensions==null||dimensions.Length!=2||Hash(path)!=hash)
            throw new InvalidDataException("Uniform asset receipt mismatch: "+path);
        var texture=Decode(path);try{if(texture.width!=dimensions[0]||texture.height!=dimensions[1])throw new InvalidDataException("PNG dimensions: "+path);}
        finally{Object.DestroyImmediate(texture);}
    }
    private static string Hash(string path){using var sha=SHA256.Create();return BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-","").ToLowerInvariant();}
    private static string ArtName(string id)=>id=="checkout"?"counter":id=="display_island"?"island":id;
    private static float Width(Fixture fixture)=>fixture.rect_xz[2]-fixture.rect_xz[0];
    private static float Depth(Fixture fixture)=>fixture.rect_xz[3]-fixture.rect_xz[1];

    [Serializable] private sealed class DisplayReadback
    {
        public long playerEntityId, cameraEntityId;
        public int pixelHeight;
        public Vector3 cameraEuler;
        public float orthographicSize, pixelsPerUnit, theoreticalScreenPixelsPerCell;
        public bool orthographic;
        public List<FixtureReadback> fixtures = new();
    }
    [Serializable] private sealed class FixtureReadback
    {
        public string id;
        public int textureWidth, textureHeight;
        public Vector3 localScale, colliderSize;
        public float projectedWidthPixels, projectedHeightPixels, sourceCellPixelsX, sourceCellPixelsY;
    }
    [MenuItem("Tools/World Art/Capture B33 Uniform Display Readback")]
    public static void CaptureDisplayReadback()
    {
        var shell=PersistentGameplayShell.Instance;
        var root=GameObject.Find("PlannedPixelShop33");
        if(!EditorApplication.isPlaying || shell==null || shell.PlayerCamera==null || root==null)
            throw new InvalidOperationException("Play GameMap1 with the existing gameplay shell and B33 first.");
        Camera camera=shell.PlayerCamera;
        float ppu=root.GetComponent<NativePixelBuilding>().nativePixelsPerUnit;
        var result=new DisplayReadback { playerEntityId=long.Parse(shell.PlayerTransform.gameObject.GetEntityId().ToString()),
            cameraEntityId=long.Parse(camera.GetEntityId().ToString()),pixelHeight=camera.pixelHeight,cameraEuler=camera.transform.eulerAngles,
            orthographicSize=camera.orthographicSize,pixelsPerUnit=ppu,orthographic=camera.orthographic,
            theoreticalScreenPixelsPerCell=camera.pixelHeight/(2f*camera.orthographicSize*ppu) };
        foreach(Transform item in root.transform.Find("Fixtures - layout footprints"))
        {
            var surface=item.Find("Sprite - native full rectangle");if(surface==null)continue;
            var renderer=surface.GetComponent<Renderer>();var material=renderer.sharedMaterial;
            var texture=material.GetTexture("_BaseMap");var mesh=surface.GetComponent<MeshFilter>().sharedMesh;
            Vector3 origin=material.GetVector("_NativeGridOriginOS");
            Vector3 u=material.GetVector("_NativeGridTexelUOS"),v=material.GetVector("_NativeGridTexelVOS");
            Vector2 a=camera.WorldToScreenPoint(surface.TransformPoint(origin));
            Vector2 b=camera.WorldToScreenPoint(surface.TransformPoint(origin+u));
            Vector2 c=camera.WorldToScreenPoint(surface.TransformPoint(origin+v));
            var min=new Vector2(float.PositiveInfinity,float.PositiveInfinity);var max=-min;
            foreach(var vertex in mesh.vertices)
            {
                Vector2 pixel=camera.WorldToScreenPoint(surface.TransformPoint(vertex));min=Vector2.Min(min,pixel);max=Vector2.Max(max,pixel);
            }
            result.fixtures.Add(new FixtureReadback { id=item.name,textureWidth=texture.width,textureHeight=texture.height,
                localScale=surface.localScale,colliderSize=item.GetComponent<BoxCollider>().size,
                projectedWidthPixels=max.x-min.x,projectedHeightPixels=max.y-min.y,
                sourceCellPixelsX=Vector2.Distance(a,b),sourceCellPixelsY=Vector2.Distance(a,c) });
        }
        const string directory="docs/artifacts/building33-uniform";Directory.CreateDirectory(directory);
        File.WriteAllText(directory+"/unity-display.json",JsonUtility.ToJson(result,true)+"\n");
        Debug.Log("B33 actual display dimensions captured; artistic quality and source perspective remain user judgments.");
    }
    private static void EnsureFolder(string path)
    {
        if(AssetDatabase.IsValidFolder(path))return;
        string parent=Path.GetDirectoryName(path).Replace('\\','/');EnsureFolder(parent);AssetDatabase.CreateFolder(parent,Path.GetFileName(path));
    }
}
