using System;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

/// <summary>N30: one versioned cabinet and bounded legacy/specular observations.</summary>
public static class NativeMaterial30Observation
{
    private const string AssetRoot="Assets/Art/NativeMaterial30";
    private const string OldRoot="Assets/Art/NativeMaterial29";
    private const float Ppu=90.509668f;
    private static GameObject Building=>GameObject.Find("PlannedPixelShop33");
    private static Material NewMaterial=>AssetDatabase.LoadAssetAtPath<Material>(AssetRoot+"/surface.mat");
    private static MeshRenderer Target=>Building.GetComponentsInChildren<MeshRenderer>(true).Single(r=>
        r.gameObject.activeInHierarchy&&r.enabled&&r.name=="Native surface"&&r.transform.parent.name=="checkout"&&
        r.sharedMaterial!=null&&r.sharedMaterial.shader.name==NativeBuilding16Importer.ShaderName);
    private static string LightingSignature()=>JsonUtility.ToJson(NativeRoom26Observation.ReadMoving())+"\n"+
        string.Join("\n",Building.GetComponentsInChildren<SteppedLocalLight>(true).OrderBy(l=>l.transform.parent.name)
        .Select(l=>l.transform.parent.name+"/"+l.name+"|"+l.Color+"|"+l.Intensity.ToString("R")+"|"+
        l.Radius.ToString("R")+"|"+l.WorldCellSize.ToString("R")+"|"+l.SurfaceBands+"|"+l.Role+"|"+
        l.RoomIndirectMultiplier.ToString("R")+"|"+l.RoomDirectMultiplier.ToString("R")));

    [Serializable] private sealed class Receipt
    {
        public bool playMode,samePlayer,sameCamera,sameGeometry,sameLighting;
        public int shaderErrors,bindingCount,changedPixels;
        public float screenPixelsPerCell,cameraPitch,cameraYaw;
        public int[] objectRect;
        public string playerEntity,cameraEntity;
    }

    private static Texture2D ImportMap(string output,string name,bool srgb)
    {
        string path=AssetRoot+"/"+name+".png";File.Copy(output+"/"+name+".png",path);
        AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport);
        var i=(TextureImporter)AssetImporter.GetAtPath(path);
        i.sRGBTexture=srgb;i.mipmapEnabled=false;i.filterMode=FilterMode.Point;i.wrapMode=TextureWrapMode.Clamp;
        i.textureCompression=TextureImporterCompression.Uncompressed;i.npotScale=TextureImporterNPOTScale.None;
        i.maxTextureSize=4096;i.alphaIsTransparency=false;i.SaveAndReimport();
        return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }

    public static void Prepare(string output)
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit Mode writer required.");
        if(AssetDatabase.IsValidFolder(AssetRoot))throw new InvalidOperationException("Previous asset version preserved.");
        AssetDatabase.CreateFolder("Assets/Art","NativeMaterial30");
        var map=ImportMap(output,"material",false);var palette=ImportMap(output,"palette",true);
        var old=AssetDatabase.LoadAssetAtPath<Material>(OldRoot+"/surface.mat");
        if(map.width!=old.GetTexture("_MaterialMap").width||map.height!=old.GetTexture("_MaterialMap").height||
            palette.width!=16||palette.height!=10)throw new InvalidDataException("Canonical map/palette size changed.");
        var normal=new Texture2D(map.width,map.height,TextureFormat.RGBAFloat,false,true)
            {name="Native30 cause-specific microrelief and roughness",filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp};
        byte[] raw=File.ReadAllBytes(output+"/normal.f32"),bottom=new byte[raw.Length];int stride=map.width*16;
        if(raw.Length!=stride*map.height)throw new InvalidDataException("Float map byte count mismatch.");
        for(int y=0;y<map.height;y++)Buffer.BlockCopy(raw,y*stride,bottom,(map.height-1-y)*stride,stride);
        normal.LoadRawTextureData(bottom);normal.Apply(false,false);AssetDatabase.CreateAsset(normal,AssetRoot+"/normal.asset");
        var material=new Material(old){name="Checkout cause-specific material 30"};
        material.SetTexture("_MaterialMap",map);material.SetTexture("_PaletteMap",palette);material.SetTexture("_NormalMap",normal);
        material.SetFloat("_RetainPatternContrast",1);AssetDatabase.CreateAsset(material,AssetRoot+"/surface.mat");
        AssetDatabase.SaveAssetIfDirty(material);AssetDatabase.SaveAssetIfDirty(normal);
        File.WriteAllText(output+"/baseline-geometry.txt",NativeRoom26Observation.GeometrySignature());
        File.WriteAllText(output+"/baseline-lighting.txt",LightingSignature());
    }

    // Detached layer-31 cache uses exactly one native screen pixel per cell.
    // Diagnostics exercise URP rather than the CPU generator's equations.
    private static void Fixture(string output,bool baseline)
    {
        Directory.CreateDirectory(output);
        var allLights=Object.FindObjectsByType<Light>(FindObjectsSortMode.None);
        var enabled=allLights.Select(l=>l.enabled).ToArray();
        var go=new GameObject("Native30 isolated fixture"){hideFlags=HideFlags.HideAndDontSave,layer=31};
        var cameraGo=new GameObject("Native30 fixture camera"){hideFlags=HideFlags.HideAndDontSave};
        var lightGo=new GameObject("Native30 actual point fixture"){hideFlags=HideFlags.HideAndDontSave};
        var old=new Material(AssetDatabase.LoadAssetAtPath<Material>(OldRoot+"/surface.mat"));
        Material material=baseline?old:new Material(NewMaterial);
        var map=old.GetTexture("_MaterialMap");var camera=cameraGo.AddComponent<Camera>();
        camera.enabled=false;camera.orthographic=true;camera.transform.rotation=Quaternion.Euler(30,45,0);
        camera.orthographicSize=map.height/(2*Ppu);camera.aspect=(float)map.width/map.height;
        go.transform.position=new Vector3(100,0,100);
        var filter=go.AddComponent<MeshFilter>();filter.sharedMesh=AssetDatabase.LoadAssetAtPath<UnityEngine.Mesh>("Assets/Art/NativeBuilding39/empty_counter/display.asset");
        var renderer=go.AddComponent<MeshRenderer>();renderer.sharedMaterial=old;
        camera.transform.position=go.transform.TransformPoint(filter.sharedMesh.bounds.center)-camera.transform.forward*10;
        camera.cullingMask=1<<31;camera.nearClipPlane=.01f;camera.farClipPlane=30;
        camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.clear;camera.allowMSAA=false;
        camera.GetUniversalAdditionalCameraData().renderPostProcessing=false;
        var light=lightGo.AddComponent<Light>();light.type=LightType.Point;light.color=Color.white;
        light.intensity=4;light.range=6;light.shadows=LightShadows.None;light.cullingMask=1<<31;
        try
        {
            foreach(var l in allLights)l.enabled=false;light.enabled=false;
            foreach(var m in new[]{old,material})
            {
                m.SetFloat("_AmbientLightStrength",0);m.SetFloat("_MainLightStrength",0);
                m.SetFloat("_AdditionalLightStrength",1);m.SetFloat("_SteppedLocalLightStrength",0);
                m.SetFloat("_NativeGridEnabled",0);m.SetFloat("_DiagnosticMode",6);
            }
            NativeBuilding16Observation.Capture(camera,output+"/legacy-readable-native.png",map.width,map.height);
            old.SetFloat("_DiagnosticMode",1);
            NativeBuilding16Observation.Capture(camera,output+"/legacy-albedo-native.png",map.width,map.height);
            if(!baseline)
            {
                renderer.sharedMaterial=material;material.SetFloat("_DiagnosticMode",1);
                NativeBuilding16Observation.Capture(camera,output+"/gpu-albedo-native.png",map.width,map.height);
                material.SetFloat("_DiagnosticMode",10);light.enabled=false;
                NativeBuilding16Observation.Capture(camera,output+"/spec-zero-native.png",map.width,map.height);
                light.enabled=true;lightGo.transform.position=go.transform.position+new Vector3(-1.8f,1.6f,-2.5f);
                NativeBuilding16Observation.Capture(camera,output+"/spec-left-native.png",map.width,map.height);
                material.SetFloat("_DiagnosticMode",0);
                NativeBuilding16Observation.Capture(camera,output+"/lit-left-native.png",map.width,map.height);
                lightGo.transform.position=go.transform.position+new Vector3(2,1.5f,-2.5f);material.SetFloat("_DiagnosticMode",10);
                NativeBuilding16Observation.Capture(camera,output+"/spec-right-native.png",map.width,map.height);
                material.SetFloat("_DiagnosticMode",0);
                NativeBuilding16Observation.Capture(camera,output+"/lit-right-native.png",map.width,map.height);
            }
        }
        finally
        {
            for(int i=0;i<allLights.Length;i++)allLights[i].enabled=enabled[i];
            Object.DestroyImmediate(go);Object.DestroyImmediate(cameraGo);Object.DestroyImmediate(lightGo);
            if(material!=old)Object.DestroyImmediate(material);Object.DestroyImmediate(old);
        }
    }
    public static void Baseline(string output)=>Fixture(output,true);

    public static string Observe(string output)
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Actual Play Mode required.");
        if(File.Exists(output+"/observation.json"))throw new InvalidOperationException("Previous observation preserved; use a fresh evidence directory.");
        Directory.CreateDirectory(output);
        var shell=PersistentGameplayShell.Instance;var camera=shell.PlayerCamera;var player=shell.PlayerTransform;
        var pid=player.GetEntityId();var cid=camera.GetEntityId();var target=Target;var original=target.sharedMaterial;
        string geometry=NativeRoom26Observation.GeometrySignature(),lighting=LightingSignature();
        var clock=shell.GetComponent<SkyLightingCycleController>();bool advance=clock.IsAdvancingAutomatically;float hour=clock.CurrentHour;
        var moving=Building.GetComponentsInChildren<SteppedLocalLight>().Single(l=>l.name=="Native17 moving light");
        var motion=moving.GetComponent<NativePixelLightMotion>();bool motionEnabled=motion.enabled;
        Vector3 movingPosition=moving.transform.localPosition,cameraPosition=camera.transform.position;
        Vector3 playerPosition=player.position;Quaternion playerRotation=player.rotation;
        var follow=camera.GetComponent<CameraFollow>();bool followEnabled=follow.enabled;
        var receipt=new Receipt();
        try
        {
            clock.SetAutomaticAdvance(false);clock.SetTimeHours(21);motion.enabled=false;moving.transform.localPosition=motion.localCenter;
            follow.enabled=false;
            // Building occlusion is player-membership driven. A camera-only move
            // from the outside leaves the roof opaque and observes no furniture.
            if(!shell.PlayerMovement.TryTeleport(Building.transform.TransformPoint(new Vector3(0,.56f,.3f)),player.rotation,out string error))
                throw new InvalidOperationException(error);
            Physics.SyncTransforms();
            // Observation framing only; angle, native scale, camera entity and saved gameplay pose stay intact.
            var mf=target.GetComponent<MeshFilter>();camera.transform.position=target.transform.TransformPoint(mf.sharedMesh.bounds.center)-camera.transform.forward*10;
            Building.GetComponent<UrbanOcclusionFader>().EvaluateVisibility(camera,player.position,1);
            Matrix4x4 view=camera.worldToCameraMatrix,projection=camera.projectionMatrix;
            var before=NativeBuilding16Observation.Capture(camera,output+"/play-before.png",camera.pixelWidth,camera.pixelHeight);
            target.sharedMaterial=NewMaterial;
            var after=NativeBuilding16Observation.Capture(camera,output+"/play-after.png",camera.pixelWidth,camera.pixelHeight);
            int changed=0;for(int i=0;i<before.Length;i++)if(Math.Abs(before[i].r-after[i].r)>2||Math.Abs(before[i].g-after[i].g)>2||Math.Abs(before[i].b-after[i].b)>2)changed++;
            var points=mf.sharedMesh.vertices.Select(p=>camera.WorldToScreenPoint(target.transform.TransformPoint(p))).ToArray();
            int x=Mathf.Clamp(Mathf.FloorToInt(points.Min(p=>p.x))-4,0,camera.pixelWidth-1);
            int y=Mathf.Clamp(camera.pixelHeight-Mathf.CeilToInt(points.Max(p=>p.y))-4,0,camera.pixelHeight-1);
            int right=Mathf.Clamp(Mathf.CeilToInt(points.Max(p=>p.x))+4,x+1,camera.pixelWidth);
            int bottom=Mathf.Clamp(camera.pixelHeight-Mathf.FloorToInt(points.Min(p=>p.y))+4,y+1,camera.pixelHeight);
            receipt.playMode=true;receipt.samePlayer=pid==player.GetEntityId();receipt.sameCamera=cid==camera.GetEntityId()&&view==camera.worldToCameraMatrix&&projection==camera.projectionMatrix;
            receipt.sameGeometry=geometry==NativeRoom26Observation.GeometrySignature();
            receipt.bindingCount=Building.GetComponentsInChildren<MeshRenderer>(true).Count(r=>r.gameObject.activeInHierarchy&&r.sharedMaterial==NewMaterial);
            receipt.changedPixels=changed;
            receipt.screenPixelsPerCell=camera.pixelHeight/(2*camera.orthographicSize*Ppu);
            receipt.cameraPitch=camera.transform.eulerAngles.x;receipt.cameraYaw=camera.transform.eulerAngles.y;
            receipt.objectRect=new[]{x,y,right-x,bottom-y};receipt.playerEntity=pid.ToString();receipt.cameraEntity=cid.ToString();
            Fixture(output,false);
            receipt.shaderErrors=ShaderUtil.GetShaderMessages(NewMaterial.shader).Count(m=>m.severity==UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error);
        }
        finally
        {
            target.sharedMaterial=original;camera.transform.position=cameraPosition;follow.enabled=followEnabled;
            shell.PlayerMovement.TryTeleport(playerPosition,playerRotation,out _);
            moving.transform.localPosition=movingPosition;motion.enabled=motionEnabled;clock.SetTimeHours(hour);clock.SetAutomaticAdvance(advance);
        }
        receipt.sameLighting=lighting==LightingSignature();File.WriteAllText(output+"/observation.json",JsonUtility.ToJson(receipt,true));
        return JsonUtility.ToJson(receipt,true);
    }

    public static string BindAndSave(string output)
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Edit Mode writer required.");
        if(File.ReadAllText(output+"/baseline-geometry.txt")!=NativeRoom26Observation.GeometrySignature()||
            File.ReadAllText(output+"/baseline-lighting.txt")!=LightingSignature())throw new InvalidOperationException("Preserved geometry/lighting changed.");
        var renderer=Target;Undo.RecordObject(renderer,"Native cause-specific material on checkout only");renderer.sharedMaterial=NewMaterial;
        PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);EditorUtility.SetDirty(renderer);EditorSceneManager.MarkSceneDirty(Building.scene);
        bool saved=EditorSceneManager.SaveScene(Building.scene);
        string json="{\"sceneSaved\":"+saved.ToString().ToLowerInvariant()+",\"sceneDirty\":"+Building.scene.isDirty.ToString().ToLowerInvariant()+",\"playing\":false}";
        File.WriteAllText(output+"/final.json",json);return json;
    }
}
