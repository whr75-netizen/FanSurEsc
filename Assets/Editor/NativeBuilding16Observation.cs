using System;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

/// <summary>Bounded GPU and gameplay observations. No scene saving or new runtime lighting owner.</summary>
public static class NativeBuilding16Observation
{
    [Serializable] private sealed class Receipt
    {
        public string phase, beforeFile, afterFile, lightOnFile, lightOffFile, overviewFile;
        public bool sameMaterialMaps, sameRenderer, isPlayMode, samePlayer, sameCamera;
        public int shaderErrorCount, shadowChangedPixels, boundInstanceCount, sharedObjectTypes;
        public int insideCount, hiddenRoofCount, fadedWallCount;
        public string[] unmatchedSources;
        public float cameraPitch, cameraYaw, sourcePixelsOnScreen;
        public string playerEntity, cameraEntity;
    }

    private static int ShaderErrors() => ShaderUtil.GetShaderMessages(Shader.Find(NativeBuilding16Importer.ShaderName))
        .Count(m => m.severity == UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error);

    private static Color32[] Capture(Camera camera, string path, int width, int height)
    {
        var target = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1 };
        var previous = RenderTexture.active;
        var image = new Texture2D(width, height, TextureFormat.RGBA32, false);
        target.Create();
        try
        {
            RenderPipeline.SubmitRenderRequest(camera, new UniversalRenderPipeline.SingleCameraRequest { destination = target });
            RenderTexture.active = target;
            image.ReadPixels(new Rect(0, 0, width, height), 0, 0); image.Apply();
            File.WriteAllBytes(path, image.EncodeToPNG());
            return image.GetPixels32();
        }
        finally { RenderTexture.active = previous; target.Release(); Object.DestroyImmediate(target); Object.DestroyImmediate(image); }
    }

    private static int Changed(Color32[] a, Color32[] b)
    {
        int count = 0;
        for (int i = 0; i < a.Length; i++)
            if (Math.Abs(a[i].r-b[i].r)>2 || Math.Abs(a[i].g-b[i].g)>2 || Math.Abs(a[i].b-b[i].b)>2) count++;
        return count;
    }

    public static string Probe(string output)
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Isolated probe runs in Edit Mode before binding.");
        output = Path.GetFullPath(output); Directory.CreateDirectory(output);
        var material = AssetDatabase.LoadAssetAtPath<Material>(NativeBuilding16Importer.AssetRoot + "/empty_counter/surface.mat");
        if (material == null) throw new InvalidOperationException("Import native cache assets first.");
        var light = Object.FindObjectsByType<Light>(FindObjectsSortMode.None).First(x => x.type == LightType.Directional && x.enabled);
        var lightRotation = light.transform.rotation;
        float diagnostic = material.GetFloat("_DiagnosticMode");
        var maps = new[] { material.GetTexture("_PositionMap"), material.GetTexture("_NormalMap"), material.GetTexture("_MaterialMap") };
        var root = new GameObject("Native16 isolated GPU probe") { hideFlags = HideFlags.HideAndDontSave, layer = 31 };
        var cameraGo = new GameObject("Native16 probe camera") { hideFlags = HideFlags.HideAndDontSave };
        GameObject ground = null; Material groundMaterial = null;
        root.transform.position = new Vector3(100, 0, 100); root.transform.rotation = Quaternion.Euler(0, 305, 0);
        var display = root.AddComponent<MeshFilter>(); display.sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(NativeBuilding16Importer.AssetRoot + "/empty_counter/display.asset");
        var renderer = root.AddComponent<MeshRenderer>(); renderer.sharedMaterial = material; renderer.shadowCastingMode = ShadowCastingMode.Off;
        var identity = renderer.GetEntityId();
        var casterGo = new GameObject("Actual closed caster") { hideFlags = HideFlags.HideAndDontSave, layer = 31 };
        casterGo.transform.SetParent(root.transform, false);
        casterGo.AddComponent<MeshFilter>().sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(NativeBuilding16Importer.AssetRoot + "/empty_counter/shadow.asset");
        var caster = casterGo.AddComponent<MeshRenderer>(); caster.sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>(NativeBuilding16Importer.AssetRoot + "/physical-shadow.mat"); caster.shadowCastingMode = ShadowCastingMode.ShadowsOnly;
        var camera = cameraGo.AddComponent<Camera>(); camera.enabled = false; camera.orthographic = true;
        camera.orthographicSize = 512f / (2f * 31.75f * 4f); camera.nearClipPlane = .01f; camera.farClipPlane = 30;
        camera.transform.rotation = Quaternion.Euler(30, 350, 0);
        camera.transform.position = root.transform.TransformPoint(new Vector3(0, .5f, 0)) - camera.transform.forward * 10;
        camera.cullingMask = 1 << 31; camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = new Color(0, 0, 0, 0);
        camera.allowMSAA = false; camera.GetUniversalAdditionalCameraData().renderPostProcessing = false;
        try
        {
            material.SetFloat("_DiagnosticMode", 0);
            light.transform.rotation = Quaternion.LookRotation(-root.transform.TransformDirection(new Vector3(-.2f, .84f, -.5f)).normalized);
            Capture(camera, Path.Combine(output, "probe-before.png"), 512, 512);
            light.transform.rotation = Quaternion.LookRotation(-root.transform.TransformDirection(new Vector3(.6f, .3f, .75f)).normalized);
            Capture(camera, Path.Combine(output, "probe-after.png"), 512, 512);
            light.transform.rotation = Quaternion.LookRotation(-root.transform.TransformDirection(new Vector3(-.65f, .55f, -.52f)).normalized);
            ground = GameObject.CreatePrimitive(PrimitiveType.Cube); ground.name = "Probe receiving plane"; ground.hideFlags = HideFlags.HideAndDontSave; ground.layer = 31;
            ground.transform.position = root.transform.position + new Vector3(0, -.06f, 0); ground.transform.localScale = new Vector3(6, .1f, 6);
            groundMaterial = new Material(Shader.Find("Universal Render Pipeline/Lit")); groundMaterial.SetColor("_BaseColor", Color.gray); ground.GetComponent<Renderer>().sharedMaterial = groundMaterial;
            caster.enabled = false; var without = Capture(camera, Path.Combine(output, "probe-shadow-off.png"), 512, 512);
            caster.enabled = true; var with = Capture(camera, Path.Combine(output, "probe-shadow-on.png"), 512, 512);
            var receipt = new Receipt { phase = "probe", beforeFile = "probe-before.png", afterFile = "probe-after.png",
                sameRenderer = renderer.GetEntityId() == identity, sameMaterialMaps = maps.SequenceEqual(new[] { material.GetTexture("_PositionMap"), material.GetTexture("_NormalMap"), material.GetTexture("_MaterialMap") }),
                shadowChangedPixels = Changed(without, with), shaderErrorCount = ShaderErrors() };
            File.WriteAllText(Path.Combine(output, "probe.json"), JsonUtility.ToJson(receipt, true));
            return JsonUtility.ToJson(receipt, true);
        }
        finally
        {
            light.transform.rotation = lightRotation; material.SetFloat("_DiagnosticMode", diagnostic);
            Object.DestroyImmediate(root); Object.DestroyImmediate(cameraGo);
            if (ground != null) Object.DestroyImmediate(ground); if (groundMaterial != null) Object.DestroyImmediate(groundMaterial);
        }
    }

    public static string Gameplay(string output)
    {
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Actual Play Mode required.");
        output=Path.GetFullPath(output); Directory.CreateDirectory(output);
        var building=GameObject.Find("PlannedPixelShop33"); var shell=PersistentGameplayShell.Instance;
        if (building == null || shell == null) throw new InvalidOperationException("Original shop and gameplay shell required.");
        var player=shell.PlayerTransform;var camera=shell.PlayerCamera;var playerId=player.GetEntityId();var cameraId=camera.GetEntityId();
        if (!shell.PlayerMovement.TryTeleport(building.transform.TransformPoint(new Vector3(0,.56f,.3f)),player.rotation,out string error))
            throw new InvalidOperationException(error);
        Physics.SyncTransforms();
        var follow=camera.GetComponent<CameraFollow>();follow.SetViewOrientation(camera.transform.rotation);
        var fader=building.GetComponent<UrbanOcclusionFader>();fader.EvaluateVisibility(camera,player.position,1);
        var renderers=building.GetComponentsInChildren<MeshRenderer>().Where(r=>r.gameObject.activeInHierarchy &&
            r.name=="Native surface" && r.sharedMaterial != null && r.sharedMaterial.shader.name==NativeBuilding16Importer.ShaderName).ToArray();
        var objects=renderers.Where(r=>r.transform.parent.parent.name.Contains("Fixtures35") ||
            r.transform.parent.parent.name.Contains("Details35")).ToArray();
        var lights=building.GetComponentsInChildren<SteppedLocalLight>();var original=lights.Select(l=>l.enabled).ToArray();
        try
        {
            foreach(var local in lights)local.enabled=false;
            Capture(camera,Path.Combine(output,"play-light-off.png"),camera.pixelWidth,camera.pixelHeight);
            for(int i=0;i<lights.Length;i++)lights[i].enabled=original[i];
            Capture(camera,Path.Combine(output,"play-interior.png"),camera.pixelWidth,camera.pixelHeight);
            // Same runtime camera and angle. One temporary integer zoom shows the
            // full building for review; the player's actual zoom is restored.
            float actualSize=camera.orthographicSize;
            try
            {
                camera.orthographicSize=actualSize*2;
                Capture(camera,Path.Combine(output,"play-overview.png"),camera.pixelWidth,camera.pixelHeight);
            }
            finally {camera.orthographicSize=actualSize;}
            var receipt=new Receipt {phase="play",isPlayMode=true,boundInstanceCount=objects.Length,
                sharedObjectTypes=objects.Select(r=>r.sharedMaterial).Distinct().Count(),unmatchedSources=Array.Empty<string>(),
                samePlayer=player.GetEntityId()==playerId,sameCamera=camera.GetEntityId()==cameraId,
                playerEntity=playerId.ToString(),cameraEntity=cameraId.ToString(),cameraPitch=camera.transform.eulerAngles.x,
                cameraYaw=camera.transform.eulerAngles.y,insideCount=fader.InsideBuildingCount,hiddenRoofCount=fader.HiddenUpperStoreyRendererCount,
                fadedWallCount=fader.FadedRendererCount,shaderErrorCount=ShaderErrors(),lightOnFile="play-interior.png",lightOffFile="play-light-off.png",overviewFile="play-overview.png",
                sourcePixelsOnScreen=camera.pixelHeight/(2*camera.orthographicSize*31.75f)};
            File.WriteAllText(Path.Combine(output,"play-observation.json"),JsonUtility.ToJson(receipt,true));
            return JsonUtility.ToJson(receipt,true);
        }
        finally { for(int i=0;i<lights.Length;i++)lights[i].enabled=original[i]; }
    }
}
