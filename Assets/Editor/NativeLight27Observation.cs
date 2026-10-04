using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;

public static class NativeLight27Observation
{
    [Serializable] private sealed class Sample
    {
        public float[] albedo, baseIrradiance, steppedIrradiance, gpu;
    }
    [Serializable] private sealed class Fixture
    {
        public string colorSpace;
        public Sample[] samples;
        public int shaderErrors;
    }

    public static string FixtureCapture(string output)
    {
        Directory.CreateDirectory(output);
        var shader = AssetDatabase.LoadAssetAtPath<Shader>("Assets/Editor/MaterialLight27Fixture.shader");
        if (shader == null || ShaderUtil.ShaderHasError(shader))
            throw new InvalidOperationException("N27 fixture shader unavailable or invalid.");
        var material = new Material(shader);
        var rt = new RenderTexture(1, 1, 0, RenderTextureFormat.ARGBFloat, RenderTextureReadWrite.Linear);
        var pixels = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
        var old = RenderTexture.active;
        var bases = new[] { Vector3.zero, Vector3.one * .08f, Vector3.one * .2f,
            Vector3.one * .5f, new Vector3(.03f, .045f, .085f), new Vector3(.4f,.1f,.03f) };
        var albedos = new[] { Vector3.zero, new Vector3(.4f,.15f,.04f),
            new Vector3(.02f,.08f,.15f), new Vector3(.8f,.8f,.8f) };
        var locals = new[] { Vector3.zero, Vector3.one * (.22f/3f),
            Vector3.one * (.44f/3f), Vector3.one * .22f };
        var samples = new System.Collections.Generic.List<Sample>();
        try
        {
            rt.Create();
            foreach (var a in albedos) foreach (var b in bases) foreach (var l in locals)
            {
                material.SetVector("_Albedo", a); material.SetVector("_BaseIrradiance", b);
                material.SetVector("_SteppedIrradiance", l);
                Graphics.Blit(Texture2D.whiteTexture, rt, material);
                RenderTexture.active = rt;
                pixels.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); pixels.Apply();
                var c = pixels.GetPixel(0, 0);
                samples.Add(new Sample { albedo = V(a), baseIrradiance = V(b),
                    steppedIrradiance = V(l), gpu = new[] { c.r, c.g, c.b } });
            }
            var receipt = new Fixture { colorSpace = QualitySettings.activeColorSpace.ToString(),
                samples = samples.ToArray(), shaderErrors = ShaderUtil.GetShaderMessages(shader)
                    .Count(m => m.severity == UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error) };
            string json = JsonUtility.ToJson(receipt, true);
            File.WriteAllText(Path.Combine(output, "fixture.json"), json);
            return "Actual GPU float fixture samples=" + samples.Count;
        }
        finally
        {
            RenderTexture.active = old;
            UnityEngine.Object.DestroyImmediate(pixels); UnityEngine.Object.DestroyImmediate(material);
            rt.Release(); UnityEngine.Object.DestroyImmediate(rt);
        }
    }
    private static float[] V(Vector3 v) => new[] { v.x, v.y, v.z };
}
