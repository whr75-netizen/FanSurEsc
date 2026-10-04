using System;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

/// <summary>Bounded N31 comparison in the existing gameplay camera, without serialized edits.</summary>
public static class NativeLight31Observation
{
    private static GameObject Building => GameObject.Find("PlannedPixelShop33");
    private static string LightingSignature() => JsonUtility.ToJson(NativeRoom26Observation.ReadMoving())+"\n"+
        string.Join("\n",Building.GetComponentsInChildren<SteppedLocalLight>(true)
        .OrderBy(l=>l.transform.parent.name).Select(l=>l.transform.parent.name+"/"+l.name+"|"+
        l.Color+"|"+l.Intensity.ToString("R")+"|"+l.Radius.ToString("R")+"|"+
        l.WorldCellSize.ToString("R")+"|"+l.SurfaceBands+"|"+l.Role+"|"+
        l.RoomIndirectMultiplier.ToString("R")+"|"+l.RoomDirectMultiplier.ToString("R")));

    [Serializable] private sealed class Natural
    {
        public float hour,ambientIntensity;
        public string ambientMode;
        public Color ambientSky,ambientEquator,ambientGround;
        public int probeCount,roofRenderers,roofCasters;
        public string[] directional;
    }
    [Serializable] private sealed class Receipt
    {
        public bool playMode,samePlayer,sameCamera,sameGeometry,sameLighting,controlsRestored;
        public int shaderErrors,bookChangedPixels,bookMaxByte,bookSumByte,lampsControlPixels,movingControlPixels;
        public int[] bookRect;
        public float screenPixelsPerCell,cameraPitch,cameraYaw;
        public string geometry,lighting;
        public Natural[] natural;
    }
    private static Natural ReadNatural(float hour)
    {
        var roofs=Building.GetComponentsInChildren<MeshRenderer>(true).Where(r=>
            r.transform.parent!=null && (r.transform.parent.name.IndexOf("roof",StringComparison.OrdinalIgnoreCase)>=0 ||
            r.transform.parent.parent!=null&&r.transform.parent.parent.name.IndexOf("roof",StringComparison.OrdinalIgnoreCase)>=0)).ToArray();
        return new Natural {hour=hour,ambientIntensity=RenderSettings.ambientIntensity,
            ambientMode=RenderSettings.ambientMode.ToString(),ambientSky=RenderSettings.ambientSkyColor,
            ambientEquator=RenderSettings.ambientEquatorColor,ambientGround=RenderSettings.ambientGroundColor,
            probeCount=LightmapSettings.lightProbes==null?0:LightmapSettings.lightProbes.count,
            roofRenderers=roofs.Length,roofCasters=roofs.Count(r=>r.enabled&&r.shadowCastingMode!=UnityEngine.Rendering.ShadowCastingMode.Off),
            directional=Object.FindObjectsByType<Light>(FindObjectsSortMode.None).Where(l=>l.type==LightType.Directional)
                .Select(l=>l.name+"|enabled="+l.enabled+"|color="+l.color+"|intensity="+l.intensity.ToString("R")+
                    "|rotation="+l.transform.eulerAngles+"|shadows="+l.shadows).ToArray()};
    }
    private static int Changed(Color32[] a,Color32[] b)
    {
        int n=0;for(int i=0;i<a.Length;i++)if(a[i].r!=b[i].r||a[i].g!=b[i].g||a[i].b!=b[i].b)n++;
        return n;
    }
    public static string Capture(string output,bool controls)
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Actual Play Mode required.");
        if(File.Exists(output+"/observation.json"))throw new InvalidOperationException("Preserve previous observation.");
        Directory.CreateDirectory(output);
        var shell=PersistentGameplayShell.Instance;var camera=shell.PlayerCamera;var player=shell.PlayerTransform;
        var clock=shell.GetComponent<SkyLightingCycleController>();
        var target=Building.GetComponentsInChildren<MeshRenderer>(true).Single(r=>r.gameObject.activeInHierarchy&&
            r.enabled&&r.name=="Native surface"&&r.transform.parent.name=="checkout"&&
            r.sharedMaterial!=null&&r.sharedMaterial.shader.name==NativeBuilding16Importer.ShaderName);
        var caster=Building.GetComponentsInChildren<MeshRenderer>(true).Single(r=>r.gameObject.activeInHierarchy&&
            r.name=="Native16 physical shadow"&&r.transform.parent.parent.name=="checkout_ledger");
        var lamps=Building.GetComponentsInChildren<SteppedLocalLight>().Where(l=>l.Role==SteppedLocalLight.LightingRole.RoomLamp).ToArray();
        var moving=Building.GetComponentsInChildren<SteppedLocalLight>().Single(l=>l.name=="Native17 moving light");
        var motion=moving.GetComponent<NativePixelLightMotion>();var follow=camera.GetComponent<CameraFollow>();
        bool advance=clock.IsAdvancingAutomatically,motionEnabled=motion.enabled,followEnabled=follow.enabled;
        bool casterEnabled=caster.enabled,movingEnabled=moving.enabled;var lampsEnabled=lamps.Select(l=>l.enabled).ToArray();
        float hour=clock.CurrentHour;Vector3 cp=camera.transform.position,pp=player.position,mp=moving.transform.localPosition;
        Quaternion pr=player.rotation;var pid=player.GetEntityId();var cid=camera.GetEntityId();
        var receipt=new Receipt {geometry=NativeRoom26Observation.GeometrySignature(),lighting=LightingSignature()};
        try
        {
            clock.SetAutomaticAdvance(false);clock.SetTimeHours(21);motion.enabled=false;moving.transform.localPosition=motion.localCenter;
            follow.enabled=false;
            if(!shell.PlayerMovement.TryTeleport(Building.transform.TransformPoint(new Vector3(0,.56f,.3f)),player.rotation,out string error))
                throw new InvalidOperationException(error);
            Physics.SyncTransforms();
            var mesh=target.GetComponent<MeshFilter>().sharedMesh;
            camera.transform.position=target.transform.TransformPoint(mesh.bounds.center)-camera.transform.forward*10;
            Building.GetComponent<UrbanOcclusionFader>().EvaluateVisibility(camera,player.position,1);
            var view=camera.worldToCameraMatrix;var projection=camera.projectionMatrix;
            caster.enabled=true;
            var on=NativeBuilding16Observation.Capture(camera,output+"/night-book-on.png",camera.pixelWidth,camera.pixelHeight);
            caster.enabled=false;
            var off=NativeBuilding16Observation.Capture(camera,output+"/night-book-off.png",camera.pixelWidth,camera.pixelHeight);
            caster.enabled=true;
            int max=0,sum=0;for(int i=0;i<on.Length;i++)
            {int d=Math.Max(Math.Abs(on[i].r-off[i].r),Math.Max(Math.Abs(on[i].g-off[i].g),Math.Abs(on[i].b-off[i].b)));max=Math.Max(max,d);sum+=d;}
            receipt.bookChangedPixels=Changed(on,off);receipt.bookMaxByte=max;receipt.bookSumByte=sum;
            var points=mesh.vertices.Select(p=>camera.WorldToScreenPoint(target.transform.TransformPoint(p))).ToArray();
            int x=Mathf.Clamp(Mathf.FloorToInt(points.Min(p=>p.x))-4,0,camera.pixelWidth-1);
            int y=Mathf.Clamp(camera.pixelHeight-Mathf.CeilToInt(points.Max(p=>p.y))-4,0,camera.pixelHeight-1);
            int right=Mathf.Clamp(Mathf.CeilToInt(points.Max(p=>p.x))+4,x+1,camera.pixelWidth);
            int bottom=Mathf.Clamp(camera.pixelHeight-Mathf.FloorToInt(points.Min(p=>p.y))+4,y+1,camera.pixelHeight);
            receipt.bookRect=new[]{x,y,right-x,bottom-y};
            receipt.natural=new Natural[2];receipt.natural[0]=ReadNatural(21);
            clock.SetTimeHours(12);receipt.natural[1]=ReadNatural(12);
            NativeBuilding16Observation.Capture(camera,output+"/day.png",camera.pixelWidth,camera.pixelHeight);
            clock.SetTimeHours(21);
            if(controls)
            {
                foreach(var lamp in lamps)lamp.SetLightingEnabled(false);
                var noLamps=NativeBuilding16Observation.Capture(camera,output+"/lamps-off.png",camera.pixelWidth,camera.pixelHeight);
                receipt.lampsControlPixels=Changed(on,noLamps);
                foreach(var lamp in lamps)lamp.SetLightingEnabled(true);
                moving.SetLightingEnabled(false);
                var noMoving=NativeBuilding16Observation.Capture(camera,output+"/moving-off.png",camera.pixelWidth,camera.pixelHeight);
                receipt.movingControlPixels=Changed(on,noMoving);
            }
            receipt.playMode=true;receipt.samePlayer=pid==player.GetEntityId();
            receipt.sameCamera=cid==camera.GetEntityId()&&view==camera.worldToCameraMatrix&&projection==camera.projectionMatrix;
            receipt.screenPixelsPerCell=camera.pixelHeight/(2*camera.orthographicSize*90.509668f);
            receipt.cameraPitch=camera.transform.eulerAngles.x;receipt.cameraYaw=camera.transform.eulerAngles.y;
            receipt.shaderErrors=ShaderUtil.GetShaderMessages(target.sharedMaterial.shader)
                .Count(m=>m.severity==UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error);
        }
        finally
        {
            caster.enabled=casterEnabled;for(int i=0;i<lamps.Length;i++)lamps[i].SetLightingEnabled(lampsEnabled[i]);
            moving.SetLightingEnabled(movingEnabled);moving.transform.localPosition=mp;motion.enabled=motionEnabled;
            camera.transform.position=cp;follow.enabled=followEnabled;shell.PlayerMovement.TryTeleport(pp,pr,out _);
            clock.SetTimeHours(hour);clock.SetAutomaticAdvance(advance);
        }
        receipt.sameGeometry=receipt.geometry==NativeRoom26Observation.GeometrySignature();
        receipt.sameLighting=receipt.lighting==LightingSignature();
        receipt.controlsRestored=lamps.Select(l=>l.enabled).SequenceEqual(lampsEnabled)&&moving.enabled==movingEnabled&&caster.enabled==casterEnabled;
        string json=JsonUtility.ToJson(receipt,true);File.WriteAllText(output+"/observation.json",json);return json;
    }
}
