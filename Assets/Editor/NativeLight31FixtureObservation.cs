using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

/// <summary>Independent linear-float exposure cases; does not touch scenes or existing materials.</summary>
public static class NativeLight31FixtureObservation
{
    [Serializable] private sealed class Sample
    {
        public string id;
        public float[] albedo, shadowedIrradiance, shadowLoss, steppedIrradiance, gpu, legacyGpu;
    }
    [Serializable] private sealed class Fixture
    {
        public string colorSpace;
        public int shaderErrors;
        public Sample[] samples;
    }
    private static float[] V(Vector3 v) => new[] { v.x, v.y, v.z };
    private static Sample Case(string id, Vector3 a, Vector3 e, Vector3 loss, Vector3 stepped)
        => new Sample { id=id, albedo=V(a), shadowedIrradiance=V(e), shadowLoss=V(loss), steppedIrradiance=V(stepped) };
    private static Sample[] Cases()
    {
        var z=Vector3.zero; var a=new Vector3(.4f,.15f,.04f); var w=Vector3.one;
        var cases=new List<Sample>();
        var noShadow=new[] {w*.08f,w*.2f,w*.5f,new Vector3(.03f,.045f,.085f),
            new Vector3(.4f,.1f,.03f),new Vector3(.2f,0,0)};
        for(int i=0;i<noShadow.Length;i++) cases.Add(Case("P0"+i,a,noShadow[i],z,z));
        cases.Add(Case("Z00",a,z,z,z));
        cases.Add(Case("Z01",z,new Vector3(.1f,.2f,.3f),new Vector3(.2f,.1f,0),w*.22f));
        cases.Add(Case("Z02",a,z,new Vector3(.3f,.2f,.1f),z));
        cases.Add(Case("C00",w,new Vector3(.3f,.1f,.3f),z,z));
        cases.Add(Case("C01",w,new Vector3(.1f,.1f,.3f),new Vector3(.2f,0,0),z));
        var visibility=new[] {1f,.75f,.5f,0f};
        for(int i=0;i<visibility.Length;i++) cases.Add(Case("M0"+i,a,w*(.198f+.04f*visibility[i]),w*(.04f*(1-visibility[i])),z));
        cases.Add(Case("S00",a,new Vector3(.03f,.045f,.085f),new Vector3(.05f,0,0),z));
        cases.Add(Case("S01",a,new Vector3(.03f,.045f,.085f),new Vector3(.05f,0,0),w*.22f));
        var openLevels=new[] {.1199f,.1201f,.3999f,.4001f};
        for(int i=0;i<openLevels.Length;i++) cases.Add(Case("T0"+i,a,w*(openLevels[i]*.5f),w*(openLevels[i]*.5f),z));
        cases.Add(Case("E00",a,w*1e-7f,z,z));
        return cases.ToArray();
    }
    private static void Set(Material m,string name,float[] values)
        => m.SetVector(name,new Vector4(values[0],values[1],values[2],0));
    private static float[] Read(Material m,RenderTexture rt,Texture2D pixels,bool legacy)
    {
        m.SetFloat("_Legacy",legacy?1:0);
        Graphics.Blit(Texture2D.whiteTexture,rt,m);
        RenderTexture.active=rt;
        pixels.ReadPixels(new Rect(0,0,1,1),0,0); pixels.Apply();
        var c=pixels.GetPixel(0,0); return new[] {c.r,c.g,c.b};
    }
    public static string Capture(string output)
    {
        Directory.CreateDirectory(output);
        string path=Path.Combine(output,"fixture.json");
        if(File.Exists(path)) throw new InvalidOperationException("Previous fixture evidence is preserved; use a fresh output.");
        var shader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/Editor/NativeLight31Fixture.shader");
        if(shader==null||ShaderUtil.ShaderHasError(shader)) throw new InvalidOperationException("N31 fixture shader unavailable or invalid.");
        var material=new Material(shader);
        var rt=new RenderTexture(1,1,0,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear);
        var pixels=new Texture2D(1,1,TextureFormat.RGBAFloat,false,true);
        var old=RenderTexture.active; var samples=Cases();
        try
        {
            if(!rt.Create()) throw new InvalidOperationException("Linear ARGBFloat render texture creation failed.");
            foreach(var s in samples)
            {
                Set(material,"_Albedo",s.albedo);Set(material,"_ShadowedIrradiance",s.shadowedIrradiance);
                Set(material,"_ShadowLoss",s.shadowLoss);Set(material,"_SteppedIrradiance",s.steppedIrradiance);
                s.gpu=Read(material,rt,pixels,false);s.legacyGpu=Read(material,rt,pixels,true);
            }
            var receipt=new Fixture {colorSpace=QualitySettings.activeColorSpace.ToString(),samples=samples,
                shaderErrors=ShaderUtil.GetShaderMessages(shader).Count(m=>m.severity==UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error)};
            File.WriteAllText(path,JsonUtility.ToJson(receipt,true));
            return "Actual N31 linear float GPU fixture cases="+samples.Length;
        }
        finally
        {
            RenderTexture.active=old;
            UnityEngine.Object.DestroyImmediate(pixels);UnityEngine.Object.DestroyImmediate(material);
            rt.Release();UnityEngine.Object.DestroyImmediate(rt);
        }
    }
}
