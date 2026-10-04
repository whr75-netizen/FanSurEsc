using System;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEngine;

/// <summary>One actual brown-object range ablation; all temporary gameplay state is restored.</summary>
public static class NativeBook32Observation
{
    [Serializable] private sealed class Geometry
    {
        public string name,positionMap,materialMap,positionsFile,normalsFile;
        public int width,height;
        public float[] localToWorld;
        public Vector3 offset;
        public Vector3[] vertices;
        public int[] triangles;
    }
    [Serializable] private sealed class Lamp
    {
        public string name;
        public Vector3 position;
        public Vector3[] roomCorners;
        public float originalRange,policyRange,intensity;
        public Color color;
    }
    [Serializable] private sealed class Context
    {
        public int width,height;
        public float[] view,projection;
        public Vector3 cameraForward;
        public bool orthographic;
        public Geometry counter,target,caster;
        public Lamp[] lamps;
    }
    [Serializable] private sealed class Receipt
    {
        public string phase,geometry,lighting;
        public bool playMode,samePlayer,sameCamera,sameGeometry,sameLighting,controlsRestored;
        public int shaderErrors,lampsControlPixels,movingControlPixels;
        public float screenPixelsPerCell,cameraPitch,cameraYaw;
        public float[] directRanges;
    }
    private static float[] Matrix(Matrix4x4 m) => new[]{m.m00,m.m01,m.m02,m.m03,
        m.m10,m.m11,m.m12,m.m13,m.m20,m.m21,m.m22,m.m23,m.m30,m.m31,m.m32,m.m33};
    private static Vector3[] Corners(BoxCollider box)
    {
        if(box==null)return Array.Empty<Vector3>();
        var points=new Vector3[8];
        for(int i=0;i<8;i++)points[i]=box.transform.TransformPoint(box.center+
            Vector3.Scale(box.size*.5f,new Vector3((i&1)==0?-1:1,(i&2)==0?-1:1,(i&4)==0?-1:1)));
        return points;
    }
    private static Lamp ReadLamp(SteppedLocalLight owner)
    {
        var corners=Corners(owner.IlluminationVolume).Concat(Corners(owner.IlluminationVolume2)).ToArray();
        float d=corners.Length==0?0:corners.Max(p=>Vector3.Distance(owner.transform.position,p));
        return new Lamp {name=owner.transform.parent.name,position=owner.transform.position,
            roomCorners=corners,originalRange=owner.RoomDirectLight.range,policyRange=Mathf.Max(owner.Radius,2*d),
            intensity=owner.RoomDirectLight.intensity,color=owner.RoomDirectLight.color};
    }
    private static void WriteFloatMap(Texture2D texture,string path)
    {
        using(var writer=new BinaryWriter(File.Open(path,FileMode.CreateNew)))
            foreach(var c in texture.GetPixels()) {writer.Write(c.r);writer.Write(c.g);writer.Write(c.b);writer.Write(c.a);}
    }
    private static Geometry ReadGeometry(MeshRenderer renderer,string output,string tag)
    {
        var mesh=renderer.GetComponent<MeshFilter>().sharedMesh;
        var block=new MaterialPropertyBlock();renderer.GetPropertyBlock(block);
        var mat=renderer.sharedMaterial;
        var geometry=new Geometry {name=renderer.transform.parent.name+"/"+renderer.name,
            localToWorld=Matrix(renderer.localToWorldMatrix),offset=block.GetVector(NativeSurfaceGridAlignment.OffsetId),
            vertices=mesh.vertices,triangles=mesh.triangles,
            positionMap=mat.HasProperty("_PositionMap")?AssetDatabase.GetAssetPath(mat.GetTexture("_PositionMap")):"",
            materialMap=mat.HasProperty("_MaterialMap")?AssetDatabase.GetAssetPath(mat.GetTexture("_MaterialMap")):""};
        if(mat.HasProperty("_PositionMap"))
        {
            var positions=(Texture2D)mat.GetTexture("_PositionMap");var normals=(Texture2D)mat.GetTexture("_NormalMap");
            geometry.width=positions.width;geometry.height=positions.height;
            geometry.positionsFile=tag+"-positions.rgba32f";geometry.normalsFile=tag+"-normals.rgba32f";
            WriteFloatMap(positions,output+"/"+geometry.positionsFile);WriteFloatMap(normals,output+"/"+geometry.normalsFile);
        }
        return geometry;
    }
    private static string Signature(SteppedLocalLight[] lamps,SteppedLocalLight moving) =>
        string.Join("\n",lamps.Append(moving).Select(l=>l.name+"|"+l.transform.position+"|"+l.Color+"|"+
            l.Intensity.ToString("R")+"|"+l.Radius.ToString("R")+"|"+l.WorldCellSize.ToString("R")+"|"+
            l.SurfaceBands+"|"+l.Role+"|"+l.RoomIndirectMultiplier.ToString("R")+"|"+l.RoomDirectMultiplier.ToString("R")));
    private static int Changed(Color32[] a,Color32[] b)
    {int n=0;for(int i=0;i<a.Length;i++)if(a[i].r!=b[i].r||a[i].g!=b[i].g||a[i].b!=b[i].b)n++;return n;}

    public static string Capture(string output,bool experiment)
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Actual Play Mode required.");
        if(File.Exists(output+"/observation.json"))throw new InvalidOperationException("Preserve previous observation.");
        Directory.CreateDirectory(output);
        var building=GameObject.Find("PlannedPixelShop33");
        var surfaces=building.GetComponentsInChildren<MeshRenderer>(true).Where(r=>r.enabled&&r.gameObject.activeInHierarchy&&
            r.name=="Native surface"&&r.sharedMaterial!=null&&r.sharedMaterial.shader.name==NativeBuilding16Importer.ShaderName).ToArray();
        var counter=surfaces.Single(r=>r.transform.parent.name=="checkout");
        var target=surfaces.Single(r=>r.transform.parent.name=="checkout_produce");
        var caster=target.transform.Find("Native16 physical shadow").GetComponent<MeshRenderer>();
        var lamps=building.GetComponentsInChildren<SteppedLocalLight>().Where(l=>l.Role==SteppedLocalLight.LightingRole.RoomLamp).ToArray();
        var moving=building.GetComponentsInChildren<SteppedLocalLight>().Single(l=>l.name=="Native17 moving light");
        var motion=moving.GetComponent<NativePixelLightMotion>();
        var shell=PersistentGameplayShell.Instance;var camera=shell.PlayerCamera;var player=shell.PlayerTransform;
        var clock=shell.GetComponent<SkyLightingCycleController>();var follow=camera.GetComponent<CameraFollow>();
        bool advance=clock.IsAdvancingAutomatically,motionEnabled=motion.enabled,followEnabled=follow.enabled;
        bool casterEnabled=caster.enabled,movingEnabled=moving.enabled;var lampsEnabled=lamps.Select(l=>l.enabled).ToArray();
        var ranges=lamps.Select(l=>l.RoomDirectLight.range).ToArray();
        float hour=clock.CurrentHour;Vector3 cp=camera.transform.position,pp=player.position,mp=moving.transform.localPosition;
        Quaternion pr=player.rotation;var pid=player.GetEntityId();var cid=camera.GetEntityId();
        var receipt=new Receipt {phase=experiment?"experiment":"final",geometry=NativeRoom26Observation.GeometrySignature()};
        try
        {
            clock.SetAutomaticAdvance(false);clock.SetTimeHours(21);motion.enabled=false;moving.transform.localPosition=motion.localCenter;
            follow.enabled=false;
            if(!shell.PlayerMovement.TryTeleport(building.transform.TransformPoint(new Vector3(0,.56f,.3f)),pr,out string error))
                throw new InvalidOperationException(error);
            Physics.SyncTransforms();
            camera.transform.position=counter.transform.TransformPoint(counter.GetComponent<MeshFilter>().sharedMesh.bounds.center)-camera.transform.forward*10;
            building.GetComponent<UrbanOcclusionFader>().EvaluateVisibility(camera,player.position,1);
            receipt.lighting=Signature(lamps,moving);
            var view=camera.worldToCameraMatrix;var projection=camera.projectionMatrix;
            var lightData=lamps.Select(ReadLamp).ToArray();
            if(experiment)
            {
                caster.enabled=true;NativeBuilding16Observation.Capture(camera,output+"/baseline-on.png",camera.pixelWidth,camera.pixelHeight);
                caster.enabled=false;NativeBuilding16Observation.Capture(camera,output+"/baseline-off.png",camera.pixelWidth,camera.pixelHeight);
                for(int i=0;i<lamps.Length;i++)lamps[i].RoomDirectLight.range=lightData[i].policyRange;
            }
            caster.enabled=true;
            var on=NativeBuilding16Observation.Capture(camera,output+(experiment?"/policy-on.png":"/shadow-on.png"),camera.pixelWidth,camera.pixelHeight);
            caster.enabled=false;
            NativeBuilding16Observation.Capture(camera,output+(experiment?"/policy-off.png":"/shadow-off.png"),camera.pixelWidth,camera.pixelHeight);
            caster.enabled=true;
            File.WriteAllText(output+"/context.json",JsonUtility.ToJson(new Context {width=camera.pixelWidth,height=camera.pixelHeight,
                view=Matrix(view),projection=Matrix(projection),cameraForward=camera.transform.forward,orthographic=camera.orthographic,
                counter=ReadGeometry(counter,output,"counter"),target=ReadGeometry(target,output,"target"),
                caster=ReadGeometry(caster,output,"caster"),lamps=lightData},true));
            receipt.directRanges=lamps.Select(l=>l.RoomDirectLight.range).ToArray();
            if(!experiment)
            {
                foreach(var lamp in lamps)lamp.SetLightingEnabled(false);
                var dark=NativeBuilding16Observation.Capture(camera,output+"/lamps-off.png",camera.pixelWidth,camera.pixelHeight);
                receipt.lampsControlPixels=Changed(on,dark);
                for(int i=0;i<lamps.Length;i++)lamps[i].SetLightingEnabled(lampsEnabled[i]);
                moving.SetLightingEnabled(false);
                receipt.movingControlPixels=Changed(on,NativeBuilding16Observation.Capture(camera,output+"/moving-off.png",camera.pixelWidth,camera.pixelHeight));
            }
            receipt.playMode=true;receipt.samePlayer=pid==player.GetEntityId();
            receipt.sameCamera=cid==camera.GetEntityId()&&view==camera.worldToCameraMatrix&&projection==camera.projectionMatrix;
            receipt.screenPixelsPerCell=camera.pixelHeight/(2*camera.orthographicSize*90.509668f);
            receipt.cameraPitch=camera.transform.eulerAngles.x;receipt.cameraYaw=camera.transform.eulerAngles.y;
            receipt.shaderErrors=ShaderUtil.GetShaderMessages(counter.sharedMaterial.shader)
                .Count(m=>m.severity==UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error);
        }
        finally
        {
            caster.enabled=casterEnabled;for(int i=0;i<lamps.Length;i++)
            {lamps[i].SetLightingEnabled(lampsEnabled[i]);lamps[i].RoomDirectLight.range=ranges[i];}
            moving.SetLightingEnabled(movingEnabled);moving.transform.localPosition=mp;motion.enabled=motionEnabled;
            camera.transform.position=cp;follow.enabled=followEnabled;shell.PlayerMovement.TryTeleport(pp,pr,out _);
            clock.SetTimeHours(hour);clock.SetAutomaticAdvance(advance);
        }
        receipt.sameGeometry=receipt.geometry==NativeRoom26Observation.GeometrySignature();
        receipt.sameLighting=receipt.lighting==Signature(lamps,moving);
        receipt.controlsRestored=lamps.Select(l=>l.enabled).SequenceEqual(lampsEnabled)&&moving.enabled==movingEnabled&&
            caster.enabled==casterEnabled&&lamps.Select(l=>l.RoomDirectLight.range).SequenceEqual(ranges);
        string json=JsonUtility.ToJson(receipt,true);File.WriteAllText(output+"/observation.json",json);return json;
    }
}
