using System;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

/// <summary>Bounded actual-game capture of the additive light. Restores diagnostics and clock.</summary>
public static class NativeLight23Observation
{
    public static string Capture(string output)
    {
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Actual Play Mode required.");
        Directory.CreateDirectory(output);
        var shell = PersistentGameplayShell.Instance;
        var camera = shell.PlayerCamera;
        var clock = shell.GetComponent<SkyLightingCycleController>();
        bool automatic = clock.IsAdvancingAutomatically;
        float hour = clock.CurrentHour;
        var renderers = Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None)
            .Where(r => r.gameObject.activeInHierarchy && r.sharedMaterial != null &&
                r.sharedMaterial.shader.name == NativeBuilding16Importer.ShaderName).ToArray();
        var materials = renderers.Select(r => r.sharedMaterial).Distinct().ToArray();
        var diagnostics = materials.Select(m => m.GetFloat("_DiagnosticMode")).ToArray();
        var lights = Object.FindObjectsByType<SteppedLocalLight>(FindObjectsSortMode.None);
        var moving = lights.Single(l => l.name == "Native17 moving light");
        var enabled = lights.Select(l => l.enabled).ToArray();
        var motion = moving.GetComponent<NativePixelLightMotion>();
        bool motionEnabled = motion.enabled;
        var position = moving.transform.localPosition;
        try
        {
            clock.SetAutomaticAdvance(false); clock.SetTimeHours(21);
            motion.enabled = false; moving.transform.localPosition = motion.localCenter;
            // Existing observer uses the actual shell/player/camera and original
            // entry point, then returns maps/mesh/instance preservation evidence.
            string play = NativeNight18Observation.Gameplay(output);
            moving.enabled = false;
            NativeBuilding16Observation.Capture(camera, Path.Combine(output, "moving-off.png"), camera.pixelWidth, camera.pixelHeight);
            moving.enabled = true;
            NativeBuilding16Observation.Capture(camera, Path.Combine(output, "moving-on.png"), camera.pixelWidth, camera.pixelHeight);
            foreach (var material in materials) material.SetFloat("_DiagnosticMode", 7);
            NativeBuilding16Observation.Capture(camera, Path.Combine(output, "gpu-additive.png"), camera.pixelWidth, camera.pixelHeight);
            for (int i = 0; i < materials.Length; i++) materials[i].SetFloat("_DiagnosticMode", diagnostics[i]);
            // Capture a second location only to observe the requested moving
            // effect with the same grid, scene and actual gameplay camera.
            moving.transform.localPosition = motion.localCenter + Vector3.right * motion.amplitude;
            NativeBuilding16Observation.Capture(camera, Path.Combine(output, "moving-right.png"), camera.pixelWidth, camera.pixelHeight);
            string json = JsonUtility.ToJson(new Receipt {
                actualPlay = EditorApplication.isPlaying, baseTintWhite = materials.All(m => m.GetColor("_BaseColor") == Color.white),
                additiveOptIn = moving.AdditiveNativePresentation, surfaceBands = moving.SurfaceBands,
                color = moving.Color, intensity = moving.Intensity, radius = moving.Radius,
                strengthValues = materials.Select(m => m.GetFloat("_SteppedLocalLightStrength")).Distinct().ToArray(),
                materialCount = materials.Length, originalPlayReceipt = play }, true);
            File.WriteAllText(Path.Combine(output, "additive-receipt.json"), json);
            return json;
        }
        finally
        {
            for (int i = 0; i < materials.Length; i++) materials[i].SetFloat("_DiagnosticMode", diagnostics[i]);
            for (int i = 0; i < lights.Length; i++) lights[i].enabled = enabled[i];
            moving.transform.localPosition = position; motion.enabled = motionEnabled;
            clock.SetTimeHours(hour); clock.SetAutomaticAdvance(automatic);
        }
    }

    [Serializable] private sealed class Receipt
    {
        public bool actualPlay, baseTintWhite, additiveOptIn;
        public int surfaceBands, materialCount;
        public Color color;
        public float intensity, radius;
        public float[] strengthValues;
        public string originalPlayReceipt;
    }
}
