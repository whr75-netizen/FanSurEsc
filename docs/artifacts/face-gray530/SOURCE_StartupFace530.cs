using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.UI;

public static class StartupFace530
{
    const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Face530/Startup530/";
    [Serializable] public class Pixel { public int x,y,role,primitive;public Color rgba;public float depth; }
    [Serializable] public class Buffer { public string stage;public int count;public float minChroma=100,maxChroma;public List<Pixel> pixels=new(); }
    [Serializable] public class Sample { public int frame,capture,presentSerial;public float globalStage;public string faceMaterial;public bool contourReady,headReady;public List<Buffer> buffers=new(); }
    [Serializable] public class Report { public string status,error;public bool controlledPausedEntry=true,oldBackground,restoredBackground,exitPlayRequested;public int captures;public List<string> transitions=new();public List<Sample> samples=new(); }
    static Report report;static bool armed,queued;static int count;static double deadline;static string lastState;static bool oldBg;
    static void Write(string status,string error="") {report.status=status;report.error=error;report.captures=count;File.WriteAllText(Root+"status.json",JsonUtility.ToJson(report,true));}
    static void Observe(Gameplay397 g,string where)
    {
        if(!g)return;
        var p=g.player;var images=g.GetComponentsInChildren<RawImage>(true);bool displayed=images.Any(x=>x&&x.texture);
        string key=(p&&p.ready)+"/"+g.connected+"/"+(p&&p.host&&p.host.head)+"/"+(p&&p.presentSerial>0)+"/"+displayed;
        if(key==lastState)return;lastState=key;
        report.transitions.Add("frame="+Time.frameCount+" where="+where+" ready="+(p&&p.ready)+" connected="+g.connected+" head="+(p&&p.host&&p.host.head)+" presentSerial="+(p?p.presentSerial:-1)+" displayedRT="+displayed+" globalStage="+Shader.GetGlobalFloat("_Auto245Stage"));Write("OBSERVING");
    }
    static void Tick()
    {
        if(!armed)return;
        if(!EditorApplication.isPlaying){Stop("STOPPED","Play ended before observation completed");return;}
        if(EditorApplication.timeSinceStartup>deadline){Stop("TIMEOUT","single startup deadline; no restart");return;}
        Observe(UnityEngine.Object.FindFirstObjectByType<Gameplay397>(),"EditorUpdate");EditorApplication.QueuePlayerLoopUpdate();
    }
    static void Before(ScriptableRenderContext context,Camera camera){if(armed)Observe(UnityEngine.Object.FindFirstObjectByType<Gameplay397>(),"beginCamera:"+camera.name);}
    static void After(ScriptableRenderContext context,Camera camera)
    {
        if(!armed||queued)return;var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();
        if(!g||!g.connected||!g.player||camera!=g.player.localCamera||!g.player.host.main.contourReady)return;
        queued=true;EditorApplication.isPaused=true;EditorApplication.delayCall+=Capture;
    }
    static Color[] Read(RTHandle t)
    {
        if(t==null||!t.rt||!t.rt.IsCreated())throw new Exception("530 producer RT missing");
        var r=AsyncGPUReadback.Request(t.rt,0,TextureFormat.RGBAFloat);r.WaitForCompletion();if(r.hasError)throw new Exception("530 readback");return r.GetData<Color>().ToArray();
    }
    static Buffer Scan(string stage,RTHandle colour,RTHandle meta)
    {
        var rgb=Read(colour);var ids=Read(meta);var b=new Buffer{stage=stage};int x0=480,y0=272,x1=0,y1=0;
        for(int y=0;y<272;y++)for(int x=0;x<480;x++)
        {
            int i=(271-y)*480+x;int role=Mathf.RoundToInt(ids[i].g);if(rgb[i].a<=.5f||role!=4)continue;
            b.pixels.Add(new Pixel{x=x,y=y,role=role,primitive=Mathf.RoundToInt(ids[i].a),depth=ids[i].r,rgba=rgb[i]});
            float chroma=Mathf.Max(rgb[i].r,Mathf.Max(rgb[i].g,rgb[i].b))-Mathf.Min(rgb[i].r,Mathf.Min(rgb[i].g,rgb[i].b));b.minChroma=Mathf.Min(b.minChroma,chroma);b.maxChroma=Mathf.Max(b.maxChroma,chroma);
            x0=Mathf.Min(x0,x);y0=Mathf.Min(y0,y);x1=Mathf.Max(x1,x+1);y1=Mathf.Max(y1,y+1);
        }
        b.count=b.pixels.Count;
        if(b.count>0)
        {
            x0=Mathf.Max(0,x0-3);y0=Mathf.Max(0,y0-3);x1=Mathf.Min(480,x1+3);y1=Mathf.Min(272,y1+3);
            var t=new Texture2D(x1-x0,y1-y0,TextureFormat.RGBA32,false);
            try{var c=new Color[t.width*t.height];for(int y=y0;y<y1;y++)for(int x=x0;x<x1;x++){var q=rgb[(271-y)*480+x];c[(y1-1-y)*t.width+x-x0]=new Color(Mathf.LinearToGammaSpace(q.r),Mathf.LinearToGammaSpace(q.g),Mathf.LinearToGammaSpace(q.b),q.a);}t.SetPixels(c);t.Apply();File.WriteAllBytes(Root+count+"_"+stage+".png",t.EncodeToPNG());}finally{UnityEngine.Object.DestroyImmediate(t);}
        }
        return b;
    }
    static void Capture()
    {
        if(!armed)return;
        try
        {
            var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected||g.runInputTest)throw new Exception("530 expected connected runtime without synthetic input test");
            var h=g.player.host;var f=h.main;var head=h.head;var m=head.motion.materials[7];
            var s=new Sample{frame=Time.frameCount,capture=count,presentSerial=g.player.presentSerial,globalStage=Shader.GetGlobalFloat("_Auto245Stage"),faceMaterial=m.name+":"+m.shader.name+":tex="+(m.GetTexture("_MainTex")?m.GetTexture("_MainTex").name:"null"),contourReady=f.contourReady,headReady=h.headReady};
            s.buffers.Add(Scan("HEAD_SOURCE",head.motion.raw[0],head.motion.raw[5]));
            s.buffers.Add(Scan("HEAD_PROVIDER8",head.layers[8].rgba,head.layers[8].meta));
            s.buffers.Add(Scan("HEAD_PREPARED",head.prepared,head.preparedMeta));
            s.buffers.Add(Scan("MAIN_FINAL",f.colour,f.preparedMeta));report.samples.Add(s);count++;Write("OBSERVED");
            if(count>=2){Stop("CAPTURED");return;}queued=false;EditorApplication.isPaused=false;
        }
        catch(Exception e){Stop("FAILED",e.ToString());}
    }
    static void Stop(string status,string error="")
    {
        if(!armed)return;armed=false;RenderPipelineManager.beginCameraRendering-=Before;RenderPipelineManager.endCameraRendering-=After;EditorApplication.update-=Tick;EditorApplication.delayCall-=Capture;
        Application.runInBackground=oldBg;report.restoredBackground=Application.runInBackground==oldBg;report.exitPlayRequested=EditorApplication.isPlaying;Write(status,error);
        EditorApplication.isPaused=false;if(EditorApplication.isPlaying)EditorApplication.isPlaying=false;
    }
    public static void Start()
    {
        if(Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets"||!EditorApplication.isPlaying||!EditorApplication.isPaused)throw new Exception("530 requires the one controlled paused Play entry");
        if(Directory.Exists(Root))throw new Exception("530 existing observation; no duplicate");
        var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(g&&g.connected)throw new Exception("530 missed startup; do not repeat or call it first frame");
        Directory.CreateDirectory(Root);oldBg=Application.runInBackground;report=new Report{oldBackground=oldBg};armed=true;count=0;queued=false;lastState=null;deadline=EditorApplication.timeSinceStartup+120;
        RenderPipelineManager.beginCameraRendering+=Before;RenderPipelineManager.endCameraRendering+=After;EditorApplication.update+=Tick;Application.runInBackground=true;Observe(g,"AttachPaused");Write("ARMED");EditorApplication.isPaused=false;EditorApplication.QueuePlayerLoopUpdate();
    }
}
