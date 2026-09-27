using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEngine.SceneManagement;
using UnityEngine.Rendering.Universal;
using UnityEngine.Rendering;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using FantasySurvival.WorldLighting;

// Keep DTOs in the ordinary Editor assembly; nested arrays failed in the MCP dynamic assembly.
[Serializable] internal class B33Point { public float x; public float z; }
[Serializable] internal class B33FixtureInput { public string id; public string facing; public float[] rect_xz; }
[Serializable] internal class B33RouteInput { public string id; public B33Point[] points; }
[Serializable] internal class B33ObservationInput
{
    public string planPath; public string planSha256; public string reportPath; public string reportSha256;
    public B33FixtureInput[] fixtures; public B33RouteInput[] routes;
}
[Serializable] internal class B33Identities
{
    public long playerBefore; public long cameraBefore; public long playerAfter; public long cameraAfter;
}
[Serializable] internal class B33FixtureResult { public string id; public float[] rectXZ; }
[Serializable] internal class B33AccessResult
{
    public string id; public float errorMetres; public bool reached; public float[] actualLocal;
}
[Serializable] internal class B33OcclusionResult
{
    public int InsideBuildingCount; public int HiddenUpperStoreyRendererCount; public int FadedRendererCount;
}
[Serializable] internal class B33ViewportResult
{
    public int pixelWidth; public int pixelHeight; public float orthographicSize;
    public int NativeIntegerScale; public bool NativeGridFitsZoomLimits;
}
[Serializable] internal class B33ObservationResult
{
    public string producer; public string scene; public bool isPlayMode; public string artManifest;
    public string layoutPlan; public string prefab; public B33Identities identities;
    public B33FixtureResult[] fixtures; public int fixtureCount; public bool layoutMatches;
    public bool layoutWithinSlots;
    public B33AccessResult[] accessRoutes; public bool entryReached;
    public float[] wallStopLocal; public bool wallBlocked;
    public bool occlusionObserved; public B33OcclusionResult occlusionCounts;
    public float actualCameraPitch; public float actualCameraYaw; public bool orthographic;
    public float sceneViewPitch; public bool sceneViewOrthographic;
    public float nativePixelsPerUnit; public float screenPixelsPerSourcePixel; public B33ViewportResult viewport;
    public int nativeSpriteCount; public bool fullRectCoverage; public bool doublePixelation;
    public string lightingPath; public int lightingRegionCount; public bool lightingObserved;
    public int missingScripts; public int newErrors = -1;
    public int lightingChangedPixels; public int lightingBufferCount;
    public bool samePlayer; public bool sameCamera; public string[] screenshots; public string artisticApproval;
}

// Replace PHASE with begin, inside, lights-off, or finish.
public static class PlannedPixelBuildingObservation
{
    public static void Execute(string phase)
    {
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Actual Play Mode required.");
        var root = GameObject.Find("PlannedPixelShop33");
        var shell = PersistentGameplayShell.Instance;
        if (root == null || shell == null) throw new InvalidOperationException("Building and existing gameplay shell required.");
        var camera = shell.PlayerCamera;
        var movement = shell.PlayerMovement;
        var fader = root.GetComponent<UrbanOcclusionFader>();
        var follow = camera.GetComponent<CameraFollow>();
        var zoom = camera.GetComponent<CameraZoomController>();
        const string dir = "docs/artifacts/building33";
        const string readback = "LocalOnly/Building33/readback.json";
        Directory.CreateDirectory(dir);
        var data = phase == "begin" ? new B33ObservationResult() :
            JsonUtility.FromJson<B33ObservationResult>(File.ReadAllText(readback));
        void Teleport(Vector3 local)
        {
            if (!movement.TryTeleport(root.transform.TransformPoint(local), shell.PlayerTransform.rotation, out string error))
                throw new InvalidOperationException(error);
            Physics.SyncTransforms();
        }
        void MoveToward(Vector3 world, float maxDistance)
        {
            Vector3 delta = world - shell.PlayerTransform.position; delta.y = 0;
            Vector3 right = camera.transform.right; right.y = 0; right.Normalize();
            Vector3 forward = camera.transform.forward; forward.y = 0; forward.Normalize();
            Vector3 direction = delta.normalized;
            movement.StepMove(new Vector2(Vector3.Dot(direction,right),Vector3.Dot(direction,forward)),
                Mathf.Min(maxDistance,delta.magnitude)/movement.speed,false);
        }
        void FrameAndCapture(string name)
        {
            follow.SetViewOrientation(camera.transform.rotation);
            fader.EvaluateVisibility(camera,shell.PlayerTransform.position,1);
            var gameView = EditorWindow.GetWindow(Type.GetType("UnityEditor.GameView,UnityEditor"));
            gameView.Focus(); gameView.Repaint(); EditorApplication.QueuePlayerLoopUpdate();
            // Play Mode can be paused by editor background focus. Root temporarily enables
            // runInBackground and restores it after observation. Capture a subsequent frame.
            double captureAfter=EditorApplication.timeSinceStartup+.6;
            EditorApplication.CallbackFunction capture=null;
            capture=()=>
            {
                if(!EditorApplication.isPlaying)
                {
                    EditorApplication.update-=capture;
                    return;
                }
                if(EditorApplication.timeSinceStartup<captureAfter)return;
                EditorApplication.update-=capture;
                gameView.Repaint();EditorApplication.QueuePlayerLoopUpdate();
                ScreenCapture.CaptureScreenshot(Path.GetFullPath(dir+"/"+name+".png"));
            };
            EditorApplication.update+=capture;
        }
        if (phase == "begin")
        {
            var input=JsonUtility.FromJson<B33ObservationInput>(File.ReadAllText("Tools/Building33/observation-input.json"));
            data.producer="UnityEditor.Building33Observation";
            data.scene=SceneManager.GetActiveScene().name;
            data.isPlayMode=EditorApplication.isPlaying;
            data.artManifest=root.GetComponent<NativePixelBuilding>().nativePixelsPerUnit>30f
                ? "docs/artifacts/building33/uniform-art-manifest.json"
                : "docs/artifacts/building33/art-manifest.json";
            data.layoutPlan=input.planPath;
            data.prefab=SessionState.GetString("B33ObservedScenePrefab", "");
            data.identities=new B33Identities {playerBefore=long.Parse(shell.PlayerTransform.gameObject.GetEntityId().ToString()),
                cameraBefore=long.Parse(camera.gameObject.GetEntityId().ToString())};
            var fixtureParent=root.transform.Find("Fixtures - layout footprints");
            var fixtures=new List<B33FixtureResult>(); bool layoutMatches=true,withinSlots=true;
            foreach(var spec in input.fixtures)
            {
                var t=fixtureParent.Find(spec.id+" - "+spec.facing);
                var box=t.GetComponent<BoxCollider>();
                Vector3 c=root.transform.InverseTransformPoint(t.TransformPoint(box.center));
                var r=new[]{c.x-box.size.x*.5f,c.z-box.size.z*.5f,c.x+box.size.x*.5f,c.z+box.size.z*.5f};
                for(int i=0;i<4;i++)layoutMatches &= Mathf.Abs(r[i]-spec.rect_xz[i])<.01f;
                withinSlots &= r[0]>=spec.rect_xz[0]-.001f && r[1]>=spec.rect_xz[1]-.001f &&
                    r[2]<=spec.rect_xz[2]+.001f && r[3]<=spec.rect_xz[3]+.001f;
                fixtures.Add(new B33FixtureResult{id=spec.id,rectXZ=r});
            }
            data.fixtures=fixtures.ToArray();data.fixtureCount=fixtures.Count;
            data.layoutMatches=fixtures.Count>0&&layoutMatches;
            data.layoutWithinSlots=fixtures.Count>0&&withinSlots;
            var access=new List<B33AccessResult>();
            foreach(var route in input.routes)
            {
                var points=route.points;
                if(points==null||points.Length==0)throw new InvalidOperationException("Empty route: "+route.id);
                Teleport(new Vector3(points[0].x,.56f,points[0].z));
                foreach(var point in points.Skip(1))
                {
                    var target=root.transform.TransformPoint(new Vector3(point.x,.56f,point.z));
                    MoveToward(target,.2f);
                }
                Vector3 local=root.transform.InverseTransformPoint(shell.PlayerTransform.position);
                var last=points[points.Length-1];
                float error=Vector2.Distance(new Vector2(local.x,local.z),new Vector2(last.x,last.z));
                access.Add(new B33AccessResult{id=route.id,errorMetres=error,reached=error<.15f,
                    actualLocal=new[]{local.x,local.y,local.z}});
            }
            data.accessRoutes=access.ToArray();
            data.entryReached=access.Count>0&&access.All(x=>x.reached);
            Teleport(new Vector3(3,.56f,-3.2f));
            var beyond=root.transform.TransformPoint(new Vector3(3,.56f,-6));
            for(int i=0;i<25;i++)MoveToward(beyond,.1f);
            Vector3 stopped=root.transform.InverseTransformPoint(shell.PlayerTransform.position);
            data.wallStopLocal=new[]{stopped.x,stopped.y,stopped.z};
            data.wallBlocked=stopped.z > -3.65f && stopped.z < -3.2f;
            Teleport(new Vector3(0,.56f,-5.5f));
            FrameAndCapture("play-exterior");
        }
        else if(phase=="inside")
        {
            Teleport(new Vector3(0,.56f,.3f));
            FrameAndCapture("play-interior");
            data.occlusionObserved=fader.InsideBuildingCount>0&&fader.HiddenUpperStoreyRendererCount>0&&fader.FadedRendererCount>0;
            data.occlusionCounts=new B33OcclusionResult{InsideBuildingCount=fader.InsideBuildingCount,
                HiddenUpperStoreyRendererCount=fader.HiddenUpperStoreyRendererCount,FadedRendererCount=fader.FadedRendererCount};
        }
        else if(phase=="lights-off")
        {
            foreach(var light in root.GetComponentsInChildren<SteppedLocalLight>())light.enabled=false;
            FrameAndCapture("light-disabled");
        }
        else if(phase=="finish")
        {
            foreach(var light in root.GetComponentsInChildren<SteppedLocalLight>())light.enabled=true;
            FrameAndCapture("play-interior-final");
            data.actualCameraPitch=camera.transform.eulerAngles.x;
            data.actualCameraYaw=camera.transform.eulerAngles.y;
            data.orthographic=camera.orthographic;
            data.sceneViewPitch=SceneView.lastActiveSceneView.rotation.eulerAngles.x;
            data.sceneViewOrthographic=SceneView.lastActiveSceneView.orthographic;
            data.nativePixelsPerUnit=zoom.NativePixelsPerUnit;
            data.screenPixelsPerSourcePixel=camera.scaledPixelHeight/(2f*camera.orthographicSize*zoom.NativePixelsPerUnit);
            data.viewport=new B33ViewportResult{pixelWidth=camera.pixelWidth,pixelHeight=camera.pixelHeight,
                orthographicSize=camera.orthographicSize,NativeIntegerScale=zoom.NativeIntegerScale,
                NativeGridFitsZoomLimits=zoom.NativeGridFitsZoomLimits};
            var renderers=root.GetComponentsInChildren<MeshRenderer>(true);
            data.nativeSpriteCount=renderers.Select(x=>x.sharedMaterial.GetTexture("_BaseMap")).Distinct().Count();
            data.fullRectCoverage=root.GetComponentsInChildren<MeshFilter>(true).All(m=>m.sharedMesh.vertexCount==4&&m.sharedMesh.triangles.Length==6&&
                m.sharedMesh.uv.Length==4&&Mathf.Abs(m.sharedMesh.uv[0].y)<.0001f&&Mathf.Abs(m.sharedMesh.uv[2].y-1)<.0001f);
            var rd=AssetDatabase.LoadAssetAtPath<UniversalRendererData>("Assets/Settings/PC_Renderer.asset");
            data.doublePixelation=rd.rendererFeatures.Any(x=>x!=null&&x.GetType().Name=="PixelArtRendererFeature"&&x.isActive);
            data.lightingPath="Existing SteppedLocalLightRendererFeature + source face colors + footprint contact masks";
            data.lightingRegionCount=root.GetComponentsInChildren<SteppedLocalLight>().Length;
            data.lightingChangedPixels=MeasureLightContribution(root,camera,dir);
            data.lightingBufferCount=Shader.GetGlobalInteger("_SteppedLocalLightCount");
            data.lightingObserved=data.lightingChangedPixels>0 && data.lightingRegionCount==2;
            data.missingScripts=root.GetComponentsInChildren<Transform>(true).Sum(t=>GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(t.gameObject));
            data.identities.playerAfter=long.Parse(shell.PlayerTransform.gameObject.GetEntityId().ToString());
            data.identities.cameraAfter=long.Parse(camera.gameObject.GetEntityId().ToString());
            data.samePlayer=data.identities.playerBefore==data.identities.playerAfter;
            data.sameCamera=data.identities.cameraBefore==data.identities.cameraAfter;
            data.screenshots=new[]{dir+"/play-exterior.png",dir+"/play-interior-final.png"};
            data.artisticApproval="pending";
        }
        else throw new InvalidOperationException("Unknown observation phase.");
        File.WriteAllText(readback,JsonUtility.ToJson(data,true));
        Debug.Log(phase+" recorded; screenshot scheduled after 0.6s: "+readback);
    }

    private static int MeasureLightContribution(GameObject root,Camera camera,string directory)
    {
        // Two synchronous renders of the SAME camera/pose/time. Only B33 light enablement changes.
        var lights=root.GetComponentsInChildren<SteppedLocalLight>();
        var enabled=lights.Select(x=>x.enabled).ToArray();
        var previous=RenderTexture.active;
        var target=new RenderTexture(camera.pixelWidth,camera.pixelHeight,24,RenderTextureFormat.ARGB32);
        target.antiAliasing=1;target.Create();
        var image=new Texture2D(target.width,target.height,TextureFormat.RGB24,false);
        try
        {
            Color32[] Capture(bool state,string filename)
            {
                foreach(var light in lights)light.enabled=state;
                RenderPipeline.SubmitRenderRequest(camera,new UniversalRenderPipeline.SingleCameraRequest{destination=target});
                RenderTexture.active=target;
                image.ReadPixels(new Rect(0,0,target.width,target.height),0,0);image.Apply();
                File.WriteAllBytes(directory+"/"+filename,image.EncodeToPNG());
                return image.GetPixels32();
            }
            var off=Capture(false,"lighting-off-controlled.png");
            var on=Capture(true,"lighting-on-controlled.png");
            int changed=0;
            for(int i=0;i<on.Length;i++)
                if(Math.Abs(on[i].r-off[i].r)>2 || Math.Abs(on[i].g-off[i].g)>2 || Math.Abs(on[i].b-off[i].b)>2)changed++;
            return changed;
        }
        finally
        {
            for(int i=0;i<lights.Length;i++)lights[i].enabled=enabled[i];
            RenderTexture.active=previous;target.Release();
            UnityEngine.Object.DestroyImmediate(target);UnityEngine.Object.DestroyImmediate(image);
        }
    }

    public static void RecordConsoleErrors(int observedNewErrors)
    {
        const string path="LocalOnly/Building33/readback.json";
        var data=JsonUtility.FromJson<B33ObservationResult>(File.ReadAllText(path));
        data.newErrors=observedNewErrors;
        File.WriteAllText(path,JsonUtility.ToJson(data,true));
    }
}
