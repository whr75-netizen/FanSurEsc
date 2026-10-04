using System;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

/// <summary>GPU projection of the existing cache and original closed mesh, without remodelling.</summary>
public static class NativeShadow28Observation
{
    [Serializable] private sealed class Case
    {
        public float[] phase;
        public int pixelScale, hitSamples;
        public float legacyProjectionErrorPx, sharedProjectionErrorPx, pairOffsetErrorM, hitProjectionErrorPx;
    }
    [Serializable] private sealed class Fixture { public Case[] cases; public int shaderErrors; }
    [Serializable] private sealed class Alignment
    {
        public int rendererCount, pairCount, shaderErrors;
        public float maximumPairOffsetErrorM, maximumSharedProjectionErrorPx, maximumLegacyProjectionErrorPx;
    }

    private static int Errors() => new[] { NativeSurfaceGridAlignment.SurfaceShader,
        "FantasySurvival/World/Native Aligned Shadow 28", "Hidden/NativeShadow28Fixture" }
        .Sum(n => ShaderUtil.GetShaderMessages(Shader.Find(n))
            .Count(m => m.severity == UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error));

    private static Color[] WorldPixels(Camera camera)
    {
        var rt = new RenderTexture(1024, 768, 24, RenderTextureFormat.ARGBFloat) { antiAliasing = 1 };
        var tex = new Texture2D(1024, 768, TextureFormat.RGBAFloat, false, true);
        var previous = RenderTexture.active;
        try
        {
            rt.Create();
            RenderPipeline.SubmitRenderRequest(camera, new UniversalRenderPipeline.SingleCameraRequest { destination = rt });
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, 1024, 768), 0, 0); tex.Apply();
            return tex.GetPixels();
        }
        finally { RenderTexture.active = previous; rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(tex); }
    }

    private static float CellError(Camera camera, Color pixel, int x, int y, int scale)
    {
        var p = NativeSurfaceGridAlignment.Raster(camera, new Vector3(pixel.r, pixel.g, pixel.b), new Vector2(1024, 768));
        var expected = new Vector2(x / scale * scale + scale * .5f, y / scale * scale + scale * .5f);
        return (p - expected).magnitude;
    }

    public static string FixtureCapture(string output)
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Isolated fixture must precede scene integration.");
        Directory.CreateDirectory(output);
        const string currentRoot = "Assets/Art/NativeBuilding39";
        var source = AssetDatabase.LoadAssetAtPath<Material>(currentRoot + "/empty_counter/surface.mat");
        var material = new Material(source) { hideFlags = HideFlags.HideAndDontSave };
        material.SetFloat("_DiagnosticMode", 9);
        var solidMaterial = new Material(Shader.Find("Hidden/NativeShadow28Fixture")) { hideFlags = HideFlags.HideAndDontSave };
        var root = new GameObject("N28 original mesh fixture") { hideFlags = HideFlags.HideAndDontSave, layer = 31 };
        var cameraGo = new GameObject("N28 GPU fixture camera") { hideFlags = HideFlags.HideAndDontSave };
        root.transform.rotation = Quaternion.Euler(0, 305, 0);
        root.AddComponent<MeshFilter>().sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(currentRoot + "/empty_counter/display.asset");
        var surface = root.AddComponent<MeshRenderer>(); surface.sharedMaterial = material; surface.shadowCastingMode = ShadowCastingMode.Off;
        var solidGo = new GameObject("Native16 physical shadow") { hideFlags = HideFlags.HideAndDontSave, layer = 31 };
        solidGo.transform.SetParent(root.transform, false);
        solidGo.AddComponent<MeshFilter>().sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(currentRoot + "/empty_counter/shadow.asset");
        var solid = solidGo.AddComponent<MeshRenderer>(); solid.sharedMaterial = solidMaterial; solid.shadowCastingMode = ShadowCastingMode.Off;
        var binding = root.AddComponent<NativeSurfaceGridAlignment>(); binding.enabled = false;
        var camera = cameraGo.AddComponent<Camera>(); camera.enabled = false; camera.orthographic = true;
        camera.transform.rotation = Quaternion.Euler(30, 350, 0); camera.nearClipPlane = .01f; camera.farClipPlane = 30;
        camera.cullingMask = 1 << 31; camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = Color.clear;
        camera.allowHDR = true; camera.allowMSAA = false; camera.allowDynamicResolution = false;
        var data = camera.GetUniversalAdditionalCameraData(); data.renderPostProcessing = false;
        data.antialiasing = AntialiasingMode.None; data.requiresColorOption = CameraOverrideOption.Off;
        var phases = new[] { new Vector2(.17f, -.23f), new Vector2(-.31f, .41f) };
        var cases = new System.Collections.Generic.List<Case>();
        try
        {
            foreach (var phase in phases) foreach (int q in new[] { 2, 4 })
            {
                camera.orthographicSize = 768 / (2f * 90.509668f * q); camera.aspect = 1024f / 768;
                camera.transform.position = new Vector3(0, .5f, 0) - camera.transform.forward * 10 +
                    camera.transform.right * phase.x / 90.509668f + camera.transform.up * phase.y / 90.509668f;
                binding.enabled = false; surface.enabled = true; solid.enabled = false;
                var old = WorldPixels(camera);
                binding.enabled = true; var native = WorldPixels(camera);
                var a = new MaterialPropertyBlock(); var b = new MaterialPropertyBlock();
                surface.GetPropertyBlock(a); solid.GetPropertyBlock(b);
                float pairError = (a.GetVector(NativeSurfaceGridAlignment.OffsetId) - b.GetVector(NativeSurfaceGridAlignment.OffsetId)).magnitude;
                surface.enabled = false; solid.enabled = true;
                var mesh = WorldPixels(camera);
                float oldError = 0, nativeError = 0, hitError = 0; int hits = 0;
                for (int y = 0; y < 768; y++) for (int x = 0; x < 1024; x++)
                {
                    int i = y * 1024 + x;
                    if (old[i].a > .5f) oldError = Mathf.Max(oldError, CellError(camera, old[i], x, y, q));
                    if (native[i].a < .5f) continue;
                    nativeError = Mathf.Max(nativeError, CellError(camera, native[i], x, y, q));
                    if (mesh[i].a < .5f) continue;
                    // The continuous solid raster hits screen sample centres; the native cache hits cell centres.
                    var mp = NativeSurfaceGridAlignment.Raster(camera, new Vector3(mesh[i].r, mesh[i].g, mesh[i].b), new Vector2(1024, 768));
                    hitError = Mathf.Max(hitError, (mp - new Vector2(x + .5f, y + .5f)).magnitude);
                    hits++;
                }
                cases.Add(new Case { phase = new[] { phase.x, phase.y }, pixelScale = q,
                    legacyProjectionErrorPx = oldError, sharedProjectionErrorPx = nativeError,
                    pairOffsetErrorM = pairError, hitProjectionErrorPx = hitError, hitSamples = hits });
            }
            var receipt = new Fixture { cases = cases.ToArray(), shaderErrors = Errors() };
            string json = JsonUtility.ToJson(receipt, true); File.WriteAllText(Path.Combine(output, "fixture.json"), json); return json;
        }
        finally { Object.DestroyImmediate(root); Object.DestroyImmediate(cameraGo); Object.DestroyImmediate(material); Object.DestroyImmediate(solidMaterial); }
    }

    public static string AlignmentCapture(string output)
    {
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Actual gameplay camera required.");
        var camera = PersistentGameplayShell.Instance.PlayerCamera;
        var root = GameObject.Find("PlannedPixelShop33"); var alignment = root.GetComponent<NativeSurfaceGridAlignment>();
        alignment.Apply(camera);
        var a = new MaterialPropertyBlock(); var b = new MaterialPropertyBlock();
        var result = new Alignment { shaderErrors = Errors() };
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>().Where(r => r.sharedMaterial != null && r.sharedMaterial.shader.name == NativeSurfaceGridAlignment.SurfaceShader))
        {
            result.rendererCount++;
            var child = r.transform.Find("Native16 physical shadow"); var caster = child != null ? child.GetComponent<Renderer>() : null;
            if (caster == null) continue;
            result.pairCount++;
            r.GetPropertyBlock(a); caster.GetPropertyBlock(b);
            var delta = a.GetVector(NativeSurfaceGridAlignment.OffsetId);
            result.maximumPairOffsetErrorM = Mathf.Max(result.maximumPairOffsetErrorM, (delta - b.GetVector(NativeSurfaceGridAlignment.OffsetId)).magnitude);
            Vector3 anchor = r.localToWorldMatrix.MultiplyPoint3x4(r.sharedMaterial.GetVector("_NativeGridAnchorOS"));
            var size = NativeSurfaceGridAlignment.RasterSize(camera);
            var p = NativeSurfaceGridAlignment.Raster(camera, anchor, size);
            var shifted = NativeSurfaceGridAlignment.Raster(camera, anchor + (Vector3)delta, size);
            result.maximumLegacyProjectionErrorPx = Mathf.Max(result.maximumLegacyProjectionErrorPx, (p - shifted).magnitude);
            result.maximumSharedProjectionErrorPx = Mathf.Max(result.maximumSharedProjectionErrorPx,
                (shifted - NativeSurfaceGridAlignment.Raster(camera, anchor + (Vector3)b.GetVector(NativeSurfaceGridAlignment.OffsetId), size)).magnitude);
        }
        string json = JsonUtility.ToJson(result, true); Directory.CreateDirectory(output);
        File.WriteAllText(Path.Combine(output, "alignment.json"), json); return json;
    }
}
