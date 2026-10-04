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

/// <summary>Colour-only opt-in and bounded native/GPU observations; no geometry generation.</summary>
public static class NativeNight18Observation
{
    private const float Ppu = 90.509668f;
    private static MeshRenderer[] Surfaces() => GameObject.Find("PlannedPixelShop33")
        .GetComponentsInChildren<MeshRenderer>().Where(r => r.sharedMaterial != null &&
            r.sharedMaterial.shader.name == NativeBuilding16Importer.ShaderName).ToArray();

    public static int Configure()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Persist material opt-in in Edit Mode.");
        var materials = Surfaces().Select(r => r.sharedMaterial).Distinct().ToArray();
        foreach (var material in materials)
        {
            Undo.RecordObject(material, "Readable native night");
            material.SetFloat("_ReadableNight", 1);
            EditorUtility.SetDirty(material);
            AssetDatabase.SaveAssetIfDirty(material);
        }
        return materials.Length;
    }

    public static void Fixture(string output)
    {
        Directory.CreateDirectory(output);
        string rootPath = "Assets/Art/NativeBuilding39/stock_shelf/";
        var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(rootPath + "display.asset");
        var material = AssetDatabase.LoadAssetAtPath<Material>(rootPath + "surface.mat");
        var map = material.GetTexture("_MaterialMap");
        var root = new GameObject("N18 bounded palette fixture") { hideFlags = HideFlags.HideAndDontSave, layer = 31 };
        var cameraObject = new GameObject("N18 bounded palette camera") { hideFlags = HideFlags.HideAndDontSave };
        var renderer = root.AddComponent<MeshRenderer>(); renderer.sharedMaterial = material;
        renderer.shadowCastingMode = ShadowCastingMode.Off;
        root.AddComponent<MeshFilter>().sharedMesh = mesh;
        root.transform.SetPositionAndRotation(new Vector3(100, 0, 100), Quaternion.Euler(0, 305, 0));
        var camera = cameraObject.AddComponent<Camera>(); camera.enabled = false; camera.orthographic = true;
        camera.transform.rotation = Quaternion.Euler(30, 350, 0);
        camera.transform.position = root.transform.TransformPoint(mesh.bounds.center) - camera.transform.forward * 10;
        camera.orthographicSize = map.height / (2f * Ppu); camera.aspect = (float)map.width / map.height;
        camera.nearClipPlane = .01f; camera.farClipPlane = 30;
        camera.cullingMask = 1 << 31; camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = Color.clear;
        camera.allowMSAA = false; camera.GetUniversalAdditionalCameraData().renderPostProcessing = false;
        float diagnostic = material.GetFloat("_DiagnosticMode"), grid = material.GetFloat("_NativeGridEnabled");
        Vector4 incident = material.GetVector("_ReadableFixtureIrradiance");
        try
        {
            material.SetFloat("_DiagnosticMode", 6); material.SetFloat("_NativeGridEnabled", 0);
            material.SetVector("_ReadableFixtureIrradiance", new Vector4(.03f, .045f, .085f, 0));
            NativeBuilding16Observation.Capture(camera, Path.Combine(output, "gpu-fixture.png"), map.width, map.height);
        }
        finally
        {
            material.SetFloat("_DiagnosticMode", diagnostic); material.SetFloat("_NativeGridEnabled", grid);
            material.SetVector("_ReadableFixtureIrradiance", incident);
            Object.DestroyImmediate(root); Object.DestroyImmediate(cameraObject);
        }
    }

    [Serializable] private sealed class Receipt
    {
        public bool isPlayMode, sameMapsAndGeometry, samePlayerAndCamera;
        public float hour, pixelSpacing, pitch, yaw;
        public int readableMaterials, shaderErrors;
    }

    public static string Gameplay(string output)
    {
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Actual Play Mode required.");
        Directory.CreateDirectory(output);
        var shell = PersistentGameplayShell.Instance;
        var clock = shell.GetComponent<SkyLightingCycleController>();
        bool automatic = clock.IsAdvancingAutomatically; float hour = clock.CurrentHour;
        var camera = shell.PlayerCamera; var player = shell.PlayerTransform;
        var cameraId = camera.GetEntityId(); var playerId = player.GetEntityId();
        var renderers = Surfaces(); var materials = renderers.Select(r => r.sharedMaterial).Distinct().ToArray();
        var maps = materials.SelectMany(m => new[] { m.GetTexture("_PositionMap"), m.GetTexture("_NormalMap"), m.GetTexture("_MaterialMap"), m.GetTexture("_PaletteMap") }).ToArray();
        var meshes = renderers.Select(r => r.GetComponent<MeshFilter>().sharedMesh).ToArray();
        var matrices = renderers.Select(r => r.transform.localToWorldMatrix).ToArray();
        var modes = materials.Select(m => m.GetFloat("_ReadableNight")).ToArray();
        var lights = GameObject.Find("PlannedPixelShop33").GetComponentsInChildren<SteppedLocalLight>();
        var enabled = lights.Select(l => l.enabled).ToArray();
        try
        {
            clock.SetAutomaticAdvance(false); clock.SetTimeHours(21);
            NativeBuilding16Observation.Gameplay(output, Ppu);
            foreach (var light in lights) light.enabled = false;
            foreach (var material in materials) material.SetFloat("_ReadableNight", 0);
            NativeBuilding16Observation.Capture(camera, Path.Combine(output, "legacy-off.png"), camera.pixelWidth, camera.pixelHeight);
            foreach (var material in materials) material.SetFloat("_ReadableNight", 1);
            NativeBuilding16Observation.Capture(camera, Path.Combine(output, "readable-off.png"), camera.pixelWidth, camera.pixelHeight);
            for (int i = 0; i < lights.Length; i++) lights[i].enabled = enabled[i];
            NativeBuilding16Observation.Capture(camera, Path.Combine(output, "readable-on.png"), camera.pixelWidth, camera.pixelHeight);
            var result = new Receipt { isPlayMode = true, hour = clock.CurrentHour,
                samePlayerAndCamera = camera.GetEntityId() == cameraId && player.GetEntityId() == playerId,
                sameMapsAndGeometry = maps.SequenceEqual(materials.SelectMany(m => new[] { m.GetTexture("_PositionMap"), m.GetTexture("_NormalMap"), m.GetTexture("_MaterialMap"), m.GetTexture("_PaletteMap") })) &&
                    meshes.SequenceEqual(renderers.Select(r => r.GetComponent<MeshFilter>().sharedMesh)) &&
                    matrices.SequenceEqual(renderers.Select(r => r.transform.localToWorldMatrix)),
                readableMaterials = materials.Count(m => m.GetFloat("_ReadableNight") == 1),
                shaderErrors = ShaderUtil.GetShaderMessages(Shader.Find(NativeBuilding16Importer.ShaderName)).Count(m => m.severity == UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error),
                pixelSpacing = camera.pixelHeight / (2 * camera.orthographicSize * Ppu),
                pitch = camera.transform.eulerAngles.x, yaw = camera.transform.eulerAngles.y };
            string json = JsonUtility.ToJson(result, true);
            File.WriteAllText(Path.Combine(output, "play-observation.json"), json);
            return json;
        }
        finally
        {
            for (int i = 0; i < materials.Length; i++) materials[i].SetFloat("_ReadableNight", modes[i]);
            for (int i = 0; i < lights.Length; i++) lights[i].enabled = enabled[i];
            clock.SetTimeHours(hour); clock.SetAutomaticAdvance(automatic);
        }
    }
}
