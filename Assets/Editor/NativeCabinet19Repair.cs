using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

/// <summary>Material-only repair; temporary fixed-camera comparison of direct native grids.</summary>
public static class NativeCabinet19Repair
{
    private const string AssetRoot = "Assets/Art/NativeBuilding41MaterialRepair";
    private static readonly string[] Ids = { "empty_counter", "island_body_template", "utility_bench", "cleaning_cabinet" };
    private static readonly Vector3 R = new Vector3(.70710678f, 0, -.70710678f);
    private static readonly Vector3 U = new Vector3(.35355339f, .8660254f, .35355339f);
    [Serializable] private sealed class Entry { public string id; public int width, height; public int[] origin; public float ppu; }
    [Serializable] private sealed class Manifest { public Entry[] assets; }
    [Serializable] private sealed class Receipt
    {
        public int mapBindings, shaderErrors;
        public bool existingGeometryPreserved, sameComparisonCamera;
        public float fineScreenPixel, coarseScreenPixel;
    }

    public static void ApplyAndCompare(string output)
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Edit Mode writer required.");
        if (!AssetDatabase.IsValidFolder(AssetRoot)) AssetDatabase.CreateFolder("Assets/Art", "NativeBuilding41MaterialRepair");
        var geometries = Ids.Select(id => AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/NativeBuilding39/"+id+"/surface.mat"))
            .SelectMany(m => new[] { m.GetTexture("_PositionMap"), m.GetTexture("_NormalMap"), m.GetTexture("_PaletteMap") }).ToArray();
        foreach (string id in Ids)
        {
            string target = AssetRoot+"/"+id+".png";
            var source = File.ReadAllBytes(output+"/fine/"+id+"/material.png");
            if (File.Exists(target) && !source.SequenceEqual(File.ReadAllBytes(target)))
                throw new InvalidDataException("Versioned corrected image belongs to another source: "+target);
            if (!File.Exists(target)) File.WriteAllBytes(target, source);
            AssetDatabase.ImportAsset(target, ImportAssetOptions.ForceSynchronousImport);
            var importer = (TextureImporter)AssetImporter.GetAtPath(target);
            importer.sRGBTexture=false; importer.mipmapEnabled=false; importer.filterMode=FilterMode.Point;
            importer.wrapMode=TextureWrapMode.Clamp; importer.textureCompression=TextureImporterCompression.Uncompressed;
            importer.npotScale=TextureImporterNPOTScale.None; importer.maxTextureSize=4096;
            importer.alphaIsTransparency=false; importer.SaveAndReimport();
            var material = AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/NativeBuilding39/"+id+"/surface.mat");
            var old = material.GetTexture("_MaterialMap"); var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(target);
            if (old.width!=texture.width || old.height!=texture.height) throw new InvalidDataException("Native dimensions changed.");
            Undo.RecordObject(material,"Restore existing cabinet gold inlay");
            material.SetTexture("_MaterialMap",texture); EditorUtility.SetDirty(material); AssetDatabase.SaveAssetIfDirty(material);
        }
        bool preserved=geometries.SequenceEqual(Ids.Select(id => AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/NativeBuilding39/"+id+"/surface.mat"))
            .SelectMany(m => new[] { m.GetTexture("_PositionMap"), m.GetTexture("_NormalMap"), m.GetTexture("_PaletteMap") }));
        Compare(output, output, preserved);
    }

    public static void RecaptureComparison(string source, string output)
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Edit Mode comparison required.");
        if (Directory.Exists(output)) throw new InvalidOperationException("Preserve prior comparison output.");
        Directory.CreateDirectory(output);
        Compare(source, output, true);
    }

    private static Texture2D FloatMap(string path, Entry e)
    {
        var map=new Texture2D(e.width,e.height,TextureFormat.RGBAFloat,false,true);
        map.filterMode=FilterMode.Point; map.wrapMode=TextureWrapMode.Clamp;
        var source=File.ReadAllBytes(path);
        int stride=checked(e.width*4*sizeof(float));
        if(source.Length!=checked(stride*e.height)) throw new InvalidDataException("Native float byte count mismatch.");
        var bottomUp=new byte[source.Length];
        // Match NativeBuilding16Importer.ReadFloatRows: PNG is top-down;
        // Unity raw Texture2D rows start at the bottom. All maps share one index.
        for(int row=0;row<e.height;row++) Buffer.BlockCopy(source,row*stride,bottomUp,(e.height-1-row)*stride,stride);
        map.LoadRawTextureData(bottomUp); map.Apply(false,true); return map;
    }

    private static void Compare(string sourceOutput, string output, bool preserved)
    {
        var entry=JsonUtility.FromJson<Manifest>(File.ReadAllText(sourceOutput+"/coarse/manifest.json")).assets.Single();
        var source=AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/NativeBuilding39/empty_counter/surface.mat");
        var fine=new Material(source); fine.SetFloat("_DiagnosticMode",6);
        fine.SetVector("_ReadableFixtureIrradiance",new Vector4(.03f,.045f,.085f,0));
        var coarse=new Material(fine);
        var position=FloatMap(sourceOutput+"/coarse/empty_counter/position.f32",entry);
        var normal=FloatMap(sourceOutput+"/coarse/empty_counter/normal.f32",entry);
        var data=new Texture2D(2,2,TextureFormat.RGBA32,false,true) { filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp };
        data.LoadImage(File.ReadAllBytes(sourceOutput+"/coarse/empty_counter/material.png"));
        coarse.SetTexture("_PositionMap",position); coarse.SetTexture("_NormalMap",normal); coarse.SetTexture("_MaterialMap",data);
        Vector3 Point(float x,float y)=>(R*(entry.origin[0]+x)-U*(entry.origin[1]+y))/entry.ppu;
        var mesh=new Mesh { vertices=new[] { Point(0,entry.height),Point(entry.width,entry.height),Point(entry.width,0),Point(0,0) },
            triangles=new[] {0,1,2,0,2,3},uv=new[] {Vector2.zero,Vector2.right,Vector2.one,Vector2.up} };
        mesh.RecalculateBounds();
        coarse.SetVector("_NativeGridAnchorOS",mesh.vertices[0]);coarse.SetVector("_NativeGridTexelUOS",R/entry.ppu);
        coarse.SetVector("_NativeGridTexelVOS",U/entry.ppu);
        var go=new GameObject("N19 density fixture") { hideFlags=HideFlags.HideAndDontSave,layer=31 };
        go.transform.SetPositionAndRotation(new Vector3(100,0,100),Quaternion.Euler(0,305,0));
        var filter=go.AddComponent<MeshFilter>();var renderer=go.AddComponent<MeshRenderer>();renderer.shadowCastingMode=ShadowCastingMode.Off;
        var cameraGo=new GameObject("N19 fixed comparison camera") {hideFlags=HideFlags.HideAndDontSave};
        var camera=cameraGo.AddComponent<Camera>();camera.enabled=false;camera.orthographic=true;
        camera.transform.rotation=Quaternion.Euler(30,350,0);
        camera.transform.position=go.transform.TransformPoint(new Vector3(0,.5f,0))-camera.transform.forward*10;
        camera.orthographicSize=480/(2*90.509668f);camera.aspect=640f/480;camera.nearClipPlane=.01f;camera.farClipPlane=30;
        camera.cullingMask=1<<31;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.clear;
        camera.allowMSAA=false;camera.GetUniversalAdditionalCameraData().renderPostProcessing=false;
        var cameraId=camera.GetEntityId();var matrix=camera.worldToCameraMatrix;float size=camera.orthographicSize;
        var fineMesh=AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Art/NativeBuilding39/empty_counter/display.asset");
        try
        {
            filter.sharedMesh=fineMesh;renderer.sharedMaterial=fine;
            NativeBuilding16Observation.Capture(camera,output+"/density-current.png",640,480);
            filter.sharedMesh=mesh;renderer.sharedMaterial=coarse;
            NativeBuilding16Observation.Capture(camera,output+"/density-double-dot.png",640,480);
            bool same=camera.GetEntityId()==cameraId && camera.worldToCameraMatrix==matrix && camera.orthographicSize==size;
            filter.sharedMesh=fineMesh;renderer.sharedMaterial=fine;
            var map=source.GetTexture("_MaterialMap");fine.SetFloat("_NativeGridEnabled",0);
            camera.orthographicSize=map.height/(2*90.509668f);camera.aspect=(float)map.width/map.height;
            camera.transform.position=go.transform.TransformPoint(fineMesh.bounds.center)-camera.transform.forward*10;
            NativeBuilding16Observation.Capture(camera,output+"/gpu-fixture.png",map.width,map.height);
            filter.sharedMesh=mesh;renderer.sharedMaterial=coarse;coarse.SetFloat("_NativeGridEnabled",0);
            camera.orthographicSize=entry.height/(2*entry.ppu);camera.aspect=(float)entry.width/entry.height;
            camera.transform.position=go.transform.TransformPoint(mesh.bounds.center)-camera.transform.forward*10;
            NativeBuilding16Observation.Capture(camera,output+"/gpu-coarse-fixture.png",entry.width,entry.height);
            var receipt=new Receipt {mapBindings=Ids.Length,existingGeometryPreserved=preserved,sameComparisonCamera=same,
                fineScreenPixel=480/(2*size*90.509668f),coarseScreenPixel=480/(2*size*entry.ppu),
                shaderErrors=ShaderUtil.GetShaderMessages(source.shader).Count(m=>m.severity==UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error)};
            File.WriteAllText(output+"/unity-observation.json",JsonUtility.ToJson(receipt,true));
        }
        finally
        {
            Object.DestroyImmediate(go);Object.DestroyImmediate(cameraGo);Object.DestroyImmediate(fine);Object.DestroyImmediate(coarse);
            Object.DestroyImmediate(position);Object.DestroyImmediate(normal);Object.DestroyImmediate(data);Object.DestroyImmediate(mesh);
        }
    }
}
