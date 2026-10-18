using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Rendering.RenderGraphModule;
using FantasySurvival.CharacterPresentation;

// Observes the literal gameplay Player. No source pass, shader, cell size or world is changed.
public sealed class ActualPlayerAudit391 : MonoBehaviour
{
    public const string RunName = "Run04"; public static string Output => "C:/Users/JG/Documents/Codex/2026-10-07/task/E_UnityValidation_01/ActualPlayer391/" + RunName + "/";
    public static ActualPlayerAudit391 Active;
    public RenderPipelineAsset frozenPipeline; public string beforeG,beforeQ;
    public bool captured;
    public List<string> samples = new List<string>();
    static BindingFlags fields = BindingFlags.Instance | BindingFlags.NonPublic;
    public static string PathOf(Transform t) => t.parent ? PathOf(t.parent) + "/" + t.name : t.name;
    void OnEnable() { Active = this; if(Application.isPlaying && frozenPipeline) {beforeG=GraphicsSettings.defaultRenderPipeline?GraphicsSettings.defaultRenderPipeline.name:"null";beforeQ=QualitySettings.renderPipeline?QualitySettings.renderPipeline.name:"null";GraphicsSettings.defaultRenderPipeline=frozenPipeline;QualitySettings.renderPipeline=frozenPipeline;} RenderPipelineManager.beginCameraRendering+=Begin; }
    void Begin(ScriptableRenderContext context,Camera camera) {if(!captured && camera==Camera.main && samples.Count<150)samples.Add("BEGIN;G="+(GraphicsSettings.defaultRenderPipeline?GraphicsSettings.defaultRenderPipeline.name:"null")+";Q="+(QualitySettings.renderPipeline?QualitySettings.renderPipeline.name:"null")+";current="+(GraphicsSettings.currentRenderPipeline?GraphicsSettings.currentRenderPipeline.name:"null")+";type="+(RenderPipelineManager.currentPipeline?.GetType().FullName??"null"));}
    void OnDisable() {RenderPipelineManager.beginCameraRendering-=Begin; if (Active == this) Active = null; }
    public void Observe(Camera camera, int stage, int width, int height, string format, Vector4 scale)
    {
        if (captured || samples.Count >= 150 || camera != Camera.main) return;
        foreach (var s in FindObjectsByType<CharacterSilhouetteSubject>(FindObjectsSortMode.None))
        {
            if (!s.name.Contains("PlayerVisual")) continue;
            bool applied = (bool)typeof(CharacterSilhouetteSubject).GetField("renderSnapApplied", fields).GetValue(s);
            var original = (Vector3)typeof(CharacterSilhouetteSubject).GetField("unsnappedPosition", fields).GetValue(s);
            var vp = camera.WorldToViewportPoint(s.transform.position);
            var op = camera.WorldToViewportPoint(applied ? original : s.transform.position);
            samples.Add(JsonUtility.ToJson(new PassSample {
                frame = Time.frameCount, stage = stage, sourceWidth = width, sourceHeight = height,
                cameraWidth = camera.pixelWidth, cameraHeight = camera.pixelHeight,
                scaledWidth = camera.scaledPixelWidth, scaledHeight = camera.scaledPixelHeight,
                renderScale = UniversalRenderPipeline.asset.renderScale, ortho = camera.orthographicSize,
                target = camera.targetTexture ? camera.targetTexture.name : "null", format = format,
                handleScale = scale, player = PathOf(s.transform), cellSize = s.PixelCellSize,
                snapped = applied, originalPosition = original, renderPosition = s.transform.position,
                originalViewport = op, renderViewport = vp, residualInSourcePixels = new Vector2((op.x-vp.x)*width,(op.y-vp.y)*height),
                full335 = Full319View335.Active ? PathOf(Full319View335.Active.transform) : "null",
                head367 = HeadLocal367.Active ? PathOf(HeadLocal367.Active.transform) : "null"
            }));
        }
    }
    [Serializable] public class PassSample {
        public int frame,stage,sourceWidth,sourceHeight,cameraWidth,cameraHeight,scaledWidth,scaledHeight,cellSize;
        public float renderScale,ortho; public string target,format,player,full335,head367;
        public bool snapped; public Vector4 handleScale; public Vector3 originalPosition,renderPosition,originalViewport,renderViewport;
        public Vector2 residualInSourcePixels;
    }
    public IEnumerator Capture()
    {
        yield return new WaitForEndOfFrame();
        var image = ScreenCapture.CaptureScreenshotAsTexture();
        File.WriteAllBytes(Output + "LITERAL_GAMEMAP1_ACTUAL_GAMEVIEW391.png", image.EncodeToPNG());
        var data = new SceneRecord {
            width = image.width, height = image.height, format = image.graphicsFormat.ToString(),pipelineAtEnableG=beforeG,pipelineAtEnableQ=beforeQ,currentPipeline=GraphicsSettings.currentRenderPipeline?GraphicsSettings.currentRenderPipeline.name:"null",rendererType=Camera.main.GetUniversalAdditionalCameraData().scriptableRenderer.GetType().FullName,
            cameras = FindObjectsByType<Camera>(FindObjectsSortMode.None).Select(c => PathOf(c.transform)+";enabled="+c.enabled+";target="+(c.targetTexture?c.targetTexture.name:"null")+";size="+c.pixelWidth+"x"+c.pixelHeight+";ortho="+c.orthographicSize).ToArray(),
            subjects = FindObjectsByType<CharacterSilhouetteSubject>(FindObjectsSortMode.None).Select(s => PathOf(s.transform)+";cell="+s.PixelCellSurface+";size="+s.PixelCellSize+";adaptive="+s.AdaptiveToneExperiment+";scale="+s.transform.lossyScale+";renderers="+string.Join("|",s.GetComponentsInChildren<Renderer>().Select(r=>r.name+":"+r.bounds.size+":"+string.Join(",",r.sharedMaterials.Select(m=>m?m.name:"null"))))).ToArray(),
            samples = samples.ToArray()
        };
        File.WriteAllText(Output + "RUNTIME_AND_PASS_SAMPLES391.json", JsonUtility.ToJson(data, true));
        Destroy(image); captured = true;
    }
    [Serializable] class SceneRecord { public int width,height; public string format,pipelineAtEnableG,pipelineAtEnableQ,currentPipeline,rendererType; public string[] cameras,subjects,samples; }
}

