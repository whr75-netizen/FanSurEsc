using System;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

/// <summary>Versioned material writer and one bounded same-camera comparison.</summary>
public static class NativeMaterial29Observation
{
    private const string AssetRoot = "Assets/Art/NativeMaterial29";
    private const string Original = "Assets/Art/NativeBuilding39/empty_counter/surface.mat";
    private const float Ppu = 90.509668f;
    private static GameObject Building => GameObject.Find("PlannedPixelShop33");
    private static Material NewMaterial => AssetDatabase.LoadAssetAtPath<Material>(AssetRoot+"/surface.mat");
    private static MeshRenderer Target => Building.GetComponentsInChildren<MeshRenderer>(true)
        .Single(r => r.gameObject.activeInHierarchy && r.enabled && r.name=="Native surface" &&
            r.transform.parent.name=="checkout" && r.sharedMaterial!=null &&
            r.sharedMaterial.shader.name==NativeBuilding16Importer.ShaderName);
    private static string LightingSignature() => JsonUtility.ToJson(NativeRoom26Observation.ReadMoving())+"\n"+
        string.Join("\n",Building.GetComponentsInChildren<SteppedLocalLight>(true)
            .OrderBy(l=>l.transform.parent.name).Select(l=>l.transform.parent.name+"/"+l.name+"|"+
                l.Color+"|"+l.Intensity.ToString("R")+"|"+l.Radius.ToString("R")+"|"+
                l.WorldCellSize.ToString("R")+"|"+l.SurfaceBands+"|"+l.Role+"|"+
                l.RoomIndirectMultiplier.ToString("R")+"|"+l.RoomDirectMultiplier.ToString("R")));

    [Serializable] private sealed class Receipt
    {
        public bool playMode, samePlayer, sameCamera, sameGeometry, sameLighting;
        public int shaderErrors, bindingCount, changedPixels;
        public float screenPixelsPerCell, cameraPitch, cameraYaw;
        public int[] objectRect;
        public string playerEntity, cameraEntity;
    }

    public static void Prepare(string output)
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit Mode writer required.");
        if(AssetDatabase.IsValidFolder(AssetRoot))throw new InvalidOperationException("Existing asset version is preserved.");
        AssetDatabase.CreateFolder("Assets/Art","NativeMaterial29");
        string png=AssetRoot+"/material.png";
        File.Copy(output+"/material.png",png);
        AssetDatabase.ImportAsset(png,ImportAssetOptions.ForceSynchronousImport);
        var importer=(TextureImporter)AssetImporter.GetAtPath(png);
        importer.sRGBTexture=false;importer.mipmapEnabled=false;importer.filterMode=FilterMode.Point;
        importer.wrapMode=TextureWrapMode.Clamp;importer.textureCompression=TextureImporterCompression.Uncompressed;
        importer.npotScale=TextureImporterNPOTScale.None;importer.maxTextureSize=4096;importer.alphaIsTransparency=false;
        importer.SaveAndReimport();
        var source=AssetDatabase.LoadAssetAtPath<Material>(Original);
        var map=AssetDatabase.LoadAssetAtPath<Texture2D>(png);
        if(source.GetTexture("_MaterialMap").width!=map.width || source.GetTexture("_MaterialMap").height!=map.height)
            throw new InvalidDataException("Native grid dimensions changed.");
        var normal=new Texture2D(map.width,map.height,TextureFormat.RGBAFloat,false,true)
            {name="Native29 handle microrelief",filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp};
        var raw=File.ReadAllBytes(output+"/normal.f32");var bottom=new byte[raw.Length];int stride=map.width*16;
        if(raw.Length!=stride*map.height)throw new InvalidDataException("Float map byte count mismatch.");
        for(int y=0;y<map.height;y++)Buffer.BlockCopy(raw,y*stride,bottom,(map.height-1-y)*stride,stride);
        normal.LoadRawTextureData(bottom);normal.Apply(false,false);
        AssetDatabase.CreateAsset(normal,AssetRoot+"/normal.asset");
        var material=new Material(source){name="Checkout material clusters 29"};
        material.SetTexture("_MaterialMap",map);material.SetTexture("_NormalMap",normal);
        material.SetFloat("_RetainPatternContrast",1);
        AssetDatabase.CreateAsset(material,AssetRoot+"/surface.mat");
        File.WriteAllText(output+"/baseline-geometry.txt",NativeRoom26Observation.GeometrySignature());
        File.WriteAllText(output+"/baseline-lighting.txt",LightingSignature());
        AssetDatabase.SaveAssetIfDirty(normal);AssetDatabase.SaveAssetIfDirty(material);
    }

    // This fixture evaluates the imported normal map through the actual URP
    // directional-light path. All original lights are restored in finally.
    private static void Fixture(string output)
    {
        var directional=Object.FindObjectsByType<Light>(FindObjectsSortMode.None)
            .Where(l=>l.type==LightType.Directional).ToArray();
        var enabled=directional.Select(l=>l.enabled).ToArray();
        var go=new GameObject("Native29 isolated fixture"){hideFlags=HideFlags.HideAndDontSave,layer=31};
        var cameraGo=new GameObject("Native29 fixture camera"){hideFlags=HideFlags.HideAndDontSave};
        var lightGo=new GameObject("Native29 fixture light"){hideFlags=HideFlags.HideAndDontSave};
        var material=new Material(NewMaterial);
        var camera=cameraGo.AddComponent<Camera>();camera.enabled=false;camera.orthographic=true;
        var map=material.GetTexture("_MaterialMap");
        go.transform.position=new Vector3(100,0,100);
        var filter=go.AddComponent<MeshFilter>();filter.sharedMesh=AssetDatabase.LoadAssetAtPath<UnityEngine.Mesh>("Assets/Art/NativeBuilding39/empty_counter/display.asset");
        go.AddComponent<MeshRenderer>().sharedMaterial=material;
        camera.transform.rotation=Quaternion.Euler(30,45,0);
        camera.orthographicSize=map.height/(2*Ppu);camera.aspect=(float)map.width/map.height;
        camera.transform.position=go.transform.TransformPoint(filter.sharedMesh.bounds.center)-camera.transform.forward*10;
        camera.cullingMask=1<<31;camera.nearClipPlane=.01f;camera.farClipPlane=30;
        camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.clear;camera.allowMSAA=false;
        camera.GetUniversalAdditionalCameraData().renderPostProcessing=false;
        var light=lightGo.AddComponent<Light>();light.type=LightType.Directional;light.color=Color.white;
        light.intensity=1;light.shadows=LightShadows.None;light.cullingMask=1<<31;
        material.SetFloat("_AmbientLightStrength",0);material.SetFloat("_AdditionalLightStrength",0);
        material.SetFloat("_SteppedLocalLightStrength",0);material.SetFloat("_MainLightStrength",1);
        material.SetFloat("_NativeGridEnabled",0);material.SetFloat("_DiagnosticMode",3);
        try
        {
            foreach(var l in directional)l.enabled=false;
            light.transform.rotation=Quaternion.LookRotation(-new Vector3(-1,0,-1).normalized);
            NativeBuilding16Observation.Capture(camera,output+"/direct-left-native.png",map.width,map.height);
            light.transform.rotation=Quaternion.LookRotation(-new Vector3(1,0,-1).normalized);
            NativeBuilding16Observation.Capture(camera,output+"/direct-right-native.png",map.width,map.height);
            material.SetFloat("_DiagnosticMode",2);
            NativeBuilding16Observation.Capture(camera,output+"/normal-native.png",map.width,map.height);
        }
        finally
        {
            for(int i=0;i<directional.Length;i++)directional[i].enabled=enabled[i];
            Object.DestroyImmediate(go);Object.DestroyImmediate(cameraGo);Object.DestroyImmediate(lightGo);Object.DestroyImmediate(material);
        }
    }

    public static string Observe(string output)
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Actual Play Mode required.");
        var shell=PersistentGameplayShell.Instance;var camera=shell.PlayerCamera;var player=shell.PlayerTransform;
        var pid=player.GetEntityId();var cid=camera.GetEntityId();
        var clock=shell.GetComponent<SkyLightingCycleController>();var advance=clock.IsAdvancingAutomatically;var hour=clock.CurrentHour;
        var moving=Building.GetComponentsInChildren<SteppedLocalLight>().Single(l=>l.name=="Native17 moving light");
        var motion=moving.GetComponent<NativePixelLightMotion>();bool motionEnabled=motion.enabled;
        Vector3 movingPosition=moving.transform.localPosition;
        var target=Target;var original=target.sharedMaterial;string geometry=NativeRoom26Observation.GeometrySignature(),lighting=LightingSignature();
        var receipt=new Receipt();
        try
        {
            clock.SetAutomaticAdvance(false);clock.SetTimeHours(21);motion.enabled=false;moving.transform.localPosition=motion.localCenter;
            if(!shell.PlayerMovement.TryTeleport(Building.transform.TransformPoint(new Vector3(0,.56f,.3f)),player.rotation,out string error))
                throw new InvalidOperationException(error);
            Physics.SyncTransforms();camera.GetComponent<CameraFollow>().SetViewOrientation(camera.transform.rotation);
            Building.GetComponent<UrbanOcclusionFader>().EvaluateVisibility(camera,player.position,1);
            Matrix4x4 view=camera.worldToCameraMatrix,projection=camera.projectionMatrix;
            var before=NativeBuilding16Observation.Capture(camera,output+"/play-before.png",camera.pixelWidth,camera.pixelHeight);
            target.sharedMaterial=NewMaterial;
            var after=NativeBuilding16Observation.Capture(camera,output+"/play-after.png",camera.pixelWidth,camera.pixelHeight);
            int changed=0;for(int i=0;i<before.Length;i++)if(Math.Abs(before[i].r-after[i].r)>2||Math.Abs(before[i].g-after[i].g)>2||Math.Abs(before[i].b-after[i].b)>2)changed++;
            var mf=target.GetComponent<MeshFilter>();var points=mf.sharedMesh.vertices.Select(p=>camera.WorldToScreenPoint(target.transform.TransformPoint(p))).ToArray();
            int x=Mathf.Clamp(Mathf.FloorToInt(points.Min(p=>p.x))-4,0,camera.pixelWidth-1);
            int y=Mathf.Clamp(camera.pixelHeight-Mathf.CeilToInt(points.Max(p=>p.y))-4,0,camera.pixelHeight-1);
            int right=Mathf.Clamp(Mathf.CeilToInt(points.Max(p=>p.x))+4,x+1,camera.pixelWidth);
            int bottom=Mathf.Clamp(camera.pixelHeight-Mathf.FloorToInt(points.Min(p=>p.y))+4,y+1,camera.pixelHeight);
            receipt.playMode=true;receipt.samePlayer=pid==player.GetEntityId();receipt.sameCamera=cid==camera.GetEntityId()&&view==camera.worldToCameraMatrix&&projection==camera.projectionMatrix;
            receipt.sameGeometry=geometry==NativeRoom26Observation.GeometrySignature();receipt.bindingCount=1;receipt.changedPixels=changed;
            receipt.screenPixelsPerCell=camera.pixelHeight/(2*camera.orthographicSize*Ppu);
            receipt.cameraPitch=camera.transform.eulerAngles.x;receipt.cameraYaw=camera.transform.eulerAngles.y;
            receipt.objectRect=new[]{x,y,right-x,bottom-y};receipt.playerEntity=pid.ToString();receipt.cameraEntity=cid.ToString();
            Fixture(output);
            receipt.shaderErrors=ShaderUtil.GetShaderMessages(NewMaterial.shader).Count(m=>m.severity==UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error);
        }
        finally
        {
            target.sharedMaterial=original;moving.transform.localPosition=movingPosition;motion.enabled=motionEnabled;
            clock.SetTimeHours(hour);clock.SetAutomaticAdvance(advance);
        }
        receipt.sameLighting=lighting==LightingSignature();
        File.WriteAllText(output+"/observation.json",JsonUtility.ToJson(receipt,true));
        return JsonUtility.ToJson(receipt,true);
    }

    public static string BindAndSave(string output)
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit Mode writer required.");
        if(File.ReadAllText(output+"/baseline-geometry.txt")!=NativeRoom26Observation.GeometrySignature()||
            File.ReadAllText(output+"/baseline-lighting.txt")!=LightingSignature())throw new InvalidOperationException("Preserved geometry/lighting changed.");
        var renderer=Target;Undo.RecordObject(renderer,"Native material detail on checkout only");renderer.sharedMaterial=NewMaterial;
        PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);EditorUtility.SetDirty(renderer);EditorSceneManager.MarkSceneDirty(Building.scene);
        bool saved=EditorSceneManager.SaveScene(Building.scene);
        string json="{\"sceneSaved\":"+saved.ToString().ToLowerInvariant()+",\"sceneDirty\":"+Building.scene.isDirty.ToString().ToLowerInvariant()+",\"playing\":false}";
        File.WriteAllText(output+"/final.json",json);return json;
    }
}
