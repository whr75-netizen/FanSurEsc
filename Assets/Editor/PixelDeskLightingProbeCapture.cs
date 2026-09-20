using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

public static partial class PixelDeskLightingProbe
{
    static Camera testCamera;
    static RenderTexture testTarget,oldTarget;
    static Light sun;
    static SteppedLocalLight local;
    static Material[] modelMaterials;
    static readonly List<Behaviour> paused = new List<Behaviour>();
    static Vector3 oldPosition;static Quaternion oldRotation,sunRotation;
    static float oldSize,oldAspect;static bool oldOrtho,oldHdr,oldMsaa,oldPost,localEnabled;
    static int oldMask,phase,nextFrame;static Color oldBackground;
    static string captureOutput;
    static bool oldRunInBackground;
    static CameraClearFlags oldClear;static AntialiasingMode oldAntialias;
    static readonly string[] Cases={"baseline","local_on","opposite","albedo","shadow","incident","incident_local","context"};
    [Serializable] public class CaptureEvidence
    {
        public string status,error,camera,scene;
        public int width,height;public float ppu,maxGridCornerError;
        public Vector3 imageBottomLeft,modelBottomLeft;
        public int imageWidth,imageHeight;
        public string[] cases;
        public bool actualGameCamera,point,aaOff,postOff,restored;
        public float localIntensity,localRadius,sunIntensity;
        public Vector3 localPosition;
        public Color sunColor;
        public Vector3 sunForward;
        public int localShaderCount;
    }
    static CaptureEvidence evidence;

    [MenuItem("Tools/Pixel Desk/Capture D22 Play Mode Comparison")]
    public static void BeginCapture()
        => BeginCaptureTrial("trial-"+DateTime.UtcNow.ToString("yyyyMMdd-HHmmss"));

    public static void BeginCaptureTrial(string trial)
    {
        if(string.IsNullOrEmpty(trial)||trial.Any(c=>!char.IsLetterOrDigit(c)&&c!='-'))throw new ArgumentException("Use a simple trial name.");
        captureOutput=OutputPath+"/"+trial;
        if(Directory.Exists(captureOutput))throw new InvalidOperationException("Trial exists; previous evidence is immutable.");
        if(!EditorApplication.isPlaying || PersistentGameplayShell.Instance==null) throw new InvalidOperationException("Enter base Play Mode first.");
        if(testCamera!=null) throw new InvalidOperationException("A comparison is already running.");
        var root=GameObject.Find(RootName);if(root==null) throw new InvalidOperationException("D22 comparison not present in base.");
        if(UnityEngine.SceneManagement.SceneManager.GetActiveScene().name!="GameMap1") throw new InvalidOperationException("Base scene required.");
        testCamera=PersistentGameplayShell.Instance.PlayerCamera;
        oldRunInBackground=Application.runInBackground;Application.runInBackground=true;
        var extra=testCamera.GetUniversalAdditionalCameraData();
        oldPosition=testCamera.transform.position;oldRotation=testCamera.transform.rotation;oldTarget=testCamera.targetTexture;
        oldSize=testCamera.orthographicSize;oldAspect=testCamera.aspect;oldOrtho=testCamera.orthographic;oldHdr=testCamera.allowHDR;oldMsaa=testCamera.allowMSAA;
        oldMask=testCamera.cullingMask;oldBackground=testCamera.backgroundColor;oldClear=testCamera.clearFlags;
        oldPost=extra.renderPostProcessing;oldAntialias=extra.antialiasing;
        sun=UnityEngine.Object.FindObjectsByType<Light>(FindObjectsSortMode.None).First(x=>x.type==LightType.Directional&&x.gameObject.scene.name=="GameMap1");
        sunRotation=sun.transform.rotation;
        local=GameObject.Find("SteppedLightEmitter").GetComponent<SteppedLocalLight>();localEnabled=local.enabled;
        foreach(var behaviour in UnityEngine.Object.FindObjectsByType<Behaviour>(FindObjectsSortMode.None))
        {
            string name=behaviour.GetType().Name;
            if(behaviour.enabled&&(name=="CameraFollow"||name=="CameraZoomController"||name=="SkyLightingCycleController"))
            { paused.Add(behaviour);behaviour.enabled=false; }
        }
        try
        {
            var spec=ReadSpec();Vector3 right=Map(spec.camera.r),up=Map(spec.camera.u),view=Map(spec.camera.d);
            var a=root.transform.Find("A_FinalPNG_FixedShading");var b=root.transform.Find("B_Actual12Meshes_LiveShading");
            testTarget=new RenderTexture(960,576,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB)
                {name="D22 native96PPU test",antiAliasing=1,filterMode=FilterMode.Point,useMipMap=false};testTarget.Create();
            testCamera.targetTexture=testTarget;testCamera.orthographic=true;testCamera.orthographicSize=576f/(2*spec.camera.ppu);
            testCamera.aspect=960f/576;testCamera.allowHDR=false;testCamera.allowMSAA=false;
            testCamera.clearFlags=CameraClearFlags.SolidColor;testCamera.backgroundColor=Color.black;
            extra.renderPostProcessing=false;extra.antialiasing=AntialiasingMode.None;
            Vector3 center=(a.position+b.position)/2+V(spec.camera.bounds_center_unity)-up*(.5f/spec.camera.ppu);
            testCamera.transform.SetPositionAndRotation(center+view*12,Quaternion.LookRotation(-view,up));
            modelMaterials=b.GetComponentsInChildren<MeshRenderer>().Select(x=>x.sharedMaterial).ToArray();
            Vector3 offset=V(spec.camera.bounds_center_unity)-right*(spec.camera.width/(2*spec.camera.ppu))-up*(spec.camera.height/(2*spec.camera.ppu));
            Vector3 ca=testCamera.WorldToScreenPoint(a.position+offset),cb=testCamera.WorldToScreenPoint(b.position+offset);
            float error=Mathf.Max(Mathf.Abs(ca.x-Mathf.Round(ca.x)),Mathf.Abs(ca.y-Mathf.Round(ca.y)),Mathf.Abs(cb.x-Mathf.Round(cb.x)),Mathf.Abs(cb.y-Mathf.Round(cb.y)));
            evidence=new CaptureEvidence{status="running",camera=testCamera.name,scene="GameMap1",width=960,height=576,ppu=spec.camera.ppu,
                maxGridCornerError=error,imageBottomLeft=ca,modelBottomLeft=cb,imageWidth=spec.camera.width,imageHeight=spec.camera.height,
                actualGameCamera=testCamera==PersistentGameplayShell.Instance.PlayerCamera,point=true,aaOff=true,postOff=true,
                localIntensity=local.Intensity,localRadius=local.Radius,localPosition=local.transform.position,sunIntensity=sun.intensity,
                sunColor=sun.color,sunForward=sun.transform.forward,cases=Cases};
            if(error>.001f) throw new InvalidOperationException("Pixel-center registration failed: "+error);
            Directory.CreateDirectory(captureOutput+"/captures");
            var placed=JsonUtility.FromJson<BuildEvidence>(File.ReadAllText(OutputPath+"/build.json"));placed.imageOrigin=a.position;placed.modelOrigin=b.position;
            File.WriteAllText(captureOutput+"/build.json",JsonUtility.ToJson(placed,true));phase=0;ConfigureCase();
            EditorApplication.update+=CaptureUpdate;
        }
        catch(Exception ex){ if(evidence==null)evidence=new CaptureEvidence();evidence.status="blocked";evidence.error=ex.ToString();FinishCapture();throw; }
    }
    static void ConfigureCase()
    {
        string name=Cases[phase];local.enabled=name=="local_on"||name=="context"||name=="incident_local";
        sun.transform.rotation=name=="opposite"?Quaternion.AngleAxis(180,Vector3.up)*sunRotation:sunRotation;
        foreach(var m in modelMaterials)m.SetFloat("_DiagnosticMode",name=="albedo"?1:name=="shadow"?2:name.StartsWith("incident")?3:0);
        testCamera.cullingMask=name=="context"?oldMask:1<<ProbeLayer;
        nextFrame=Time.frameCount+4;
    }
    static void CaptureUpdate()
    {
        if(!EditorApplication.isPlaying){if(evidence!=null){evidence.status="blocked";evidence.error="Play Mode ended during capture.";}FinishCapture();return;}
        if(Time.frameCount<nextFrame){EditorApplication.QueuePlayerLoopUpdate();return;}
        try
        {
            var previous=RenderTexture.active;var tex=new Texture2D(960,576,TextureFormat.RGBA32,false,false);
            try {RenderTexture.active=testTarget;tex.ReadPixels(new Rect(0,0,960,576),0,0);tex.Apply();File.WriteAllBytes(captureOutput+"/captures/"+Cases[phase]+".png",tex.EncodeToPNG());}
            finally {RenderTexture.active=previous;UnityEngine.Object.DestroyImmediate(tex);}
            if(Cases[phase]=="local_on")evidence.localShaderCount=Shader.GetGlobalInteger("_SteppedLocalLightCount");
            phase++;if(phase<Cases.Length){ConfigureCase();return;}
            evidence.status="captured";FinishCapture();Debug.Log("D22 actual GameCamera captures saved; camera/light controls restored.");
        }
        catch(Exception ex){evidence.status="blocked";evidence.error=ex.ToString();FinishCapture();Debug.LogException(ex);}
    }
    static void FinishCapture()
    {
        EditorApplication.update-=CaptureUpdate;
        if(modelMaterials!=null)foreach(var m in modelMaterials)if(m!=null)m.SetFloat("_DiagnosticMode",0);
        if(local!=null)local.enabled=localEnabled;if(sun!=null)sun.transform.rotation=sunRotation;
        if(testCamera!=null)
        {
            testCamera.targetTexture=oldTarget;testCamera.transform.SetPositionAndRotation(oldPosition,oldRotation);
            testCamera.orthographic=oldOrtho;testCamera.orthographicSize=oldSize;testCamera.aspect=oldAspect;
            testCamera.allowHDR=oldHdr;testCamera.allowMSAA=oldMsaa;testCamera.cullingMask=oldMask;testCamera.backgroundColor=oldBackground;testCamera.clearFlags=oldClear;
            var extra=testCamera.GetUniversalAdditionalCameraData();extra.renderPostProcessing=oldPost;extra.antialiasing=oldAntialias;
        }
        foreach(var b in paused)if(b!=null)b.enabled=true;paused.Clear();
        if(testTarget!=null){testTarget.Release();UnityEngine.Object.DestroyImmediate(testTarget);}
        testCamera=null;testTarget=null;
        Application.runInBackground=oldRunInBackground;
        if(evidence!=null){evidence.restored=true;Directory.CreateDirectory(captureOutput);File.WriteAllText(captureOutput+"/capture.json",JsonUtility.ToJson(evidence,true));}
    }
}
