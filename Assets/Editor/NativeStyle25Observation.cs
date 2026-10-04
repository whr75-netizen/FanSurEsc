using System;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

/// <summary>Compare the saved boundary parameter without switching render batching.</summary>
public static class NativeStyle25Observation
{
    public static string CaptureBoundaries(string output)
    {
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Actual Play Mode required.");
        Directory.CreateDirectory(output);
        var shell = PersistentGameplayShell.Instance;
        var clock = shell.GetComponent<SkyLightingCycleController>();
        bool automatic = clock.IsAdvancingAutomatically;
        float hour = clock.CurrentHour;
        var moving = Object.FindObjectsByType<SteppedLocalLight>(FindObjectsSortMode.None)
            .Single(l => l.name == "Native17 moving light");
        var motion = moving.GetComponent<NativePixelLightMotion>();
        bool motionEnabled = motion.enabled;
        var position = moving.transform.localPosition;
        var materials = GameObject.Find("PlannedPixelShop33").GetComponentsInChildren<MeshRenderer>()
            .Where(r => r.sharedMaterial != null && r.sharedMaterial.shader.name == NativeBuilding16Importer.ShaderName)
            .Select(r => r.sharedMaterial).Distinct().ToArray();
        var scales = materials.Select(m => m.GetFloat("_NativeEdgeSRGBScale")).ToArray();
        try
        {
            clock.SetAutomaticAdvance(false); clock.SetTimeHours(21);
            motion.enabled = false; moving.transform.localPosition = motion.localCenter;
            // Reuse the actual player entry and camera. No camera/mesh replacement.
            NativeBuilding16Observation.Gameplay(output, 90.509668f);
            foreach (float scale in new[] { 0.8f, 0f, 1f })
            {
                foreach (var material in materials) material.SetFloat("_NativeEdgeSRGBScale", scale);
                string name = scale == 0f ? "black-boundaries.png" :
                    (scale == 1f ? "surface-boundaries.png" : "colored-boundaries.png");
                NativeBuilding16Observation.Capture(shell.PlayerCamera, Path.Combine(output, name),
                    shell.PlayerCamera.pixelWidth, shell.PlayerCamera.pixelHeight);
            }
            string receipt = "{\"actualPlay\":true,\"materialCount\":" + materials.Length +
                ",\"propertyBlocksUsed\":false,\"onlySavedBoundaryParameterVaried\":true}";
            File.WriteAllText(Path.Combine(output, "boundary-receipt.json"), receipt);
            return receipt;
        }
        finally
        {
            for (int i = 0; i < materials.Length; i++) materials[i].SetFloat("_NativeEdgeSRGBScale", scales[i]);
            moving.transform.localPosition = position; motion.enabled = motionEnabled;
            clock.SetTimeHours(hour); clock.SetAutomaticAdvance(automatic);
        }
    }
}
