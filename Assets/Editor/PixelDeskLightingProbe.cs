using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

/// <summary>Explicit D22 authoring fixture. Does not run or replace gameplay systems.</summary>
public static partial class PixelDeskLightingProbe
{
    public const string RootName = "PixelDeskLightingComparison_D22";
    public const string AssetsPath = "Assets/Tests/PixelDeskLighting22";
    public const string OutputPath = "LocalOnly/PixelUnityProbe22";
    const string InputPath = OutputPath + "/input";
    const int ProbeLayer = 31;
    [Serializable] public class Part
    {
        public int id; public string name, role;
        public float[] center, dimensions, unity_center, unity_dimensions;
    }
    [Serializable] public class ViewSpec
    {
        public float[] r,u,d,screen_origin,bounds_center_unity;
        public int width,height; public float ppu;
    }
    [Serializable] public class Spec { public Part[] parts; public ViewSpec camera; }
    [Serializable] public class BuildEvidence
    {
        public string scene, root, imageShader, modelShader;
        public int actualMeshCount, width, height;
        public float ppu,maxDimensionError;
        public bool point,uncompressed,noMipmaps,geometryOnlySource;
        public Vector3 imageOrigin,modelOrigin;
    }
    static Vector3 V(float[] a) => new Vector3(a[0],a[1],a[2]);
    static Vector3 Map(float[] a) => new Vector3(a[0],a[2],a[1]);
    static Spec ReadSpec() => JsonUtility.FromJson<Spec>(File.ReadAllText(InputPath+"/spec.json"));

    [MenuItem("Tools/Pixel Desk/Place D22 Lighting Comparison")]
    public static void Build()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Build in Edit Mode.");
        var scene=SceneManager.GetActiveScene();
        if(scene.path!="Assets/Scenes/GameMap1.unity") throw new InvalidOperationException("Open the existing base GameMap1 first.");
        if(GameObject.Find(RootName)!=null) throw new InvalidOperationException("Comparison exists; inspect it instead of replacing it.");
        var spec=ReadSpec();
        var liveShader=Shader.Find("FantasySurvival/PixelArt/Desk Live Pixel Probe");
        if(liveShader==null || !liveShader.isSupported) throw new InvalidOperationException("Desk shader not available.");
        if(ShaderUtil.GetShaderMessages(liveShader).Any(x=>x.severity==UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error))
            throw new InvalidOperationException("Desk shader has compilation errors.");
        if(Directory.Exists(AssetsPath)) throw new InvalidOperationException("Asset folder already exists; no overwrite.");
        Directory.CreateDirectory(AssetsPath);
        foreach(string file in new[]{"desk.png","wood-grain.png","edge-mask.png"}) File.Copy(InputPath+"/"+file,AssetsPath+"/"+file);
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        foreach(string file in new[]{"desk.png","wood-grain.png","edge-mask.png"})
        {
            var importer=(TextureImporter)AssetImporter.GetAtPath(AssetsPath+"/"+file);
            importer.textureType=TextureImporterType.Default; importer.sRGBTexture=file!="edge-mask.png";
            importer.filterMode=FilterMode.Point; importer.mipmapEnabled=false; importer.textureCompression=TextureImporterCompression.Uncompressed;
            importer.wrapMode=file=="wood-grain.png"?TextureWrapMode.Repeat:TextureWrapMode.Clamp;
            importer.alphaIsTransparency=false; importer.npotScale=TextureImporterNPOTScale.None;
            importer.maxTextureSize=2048; importer.isReadable=true; importer.SaveAndReimport();
        }
        var root=new GameObject(RootName);Undo.RegisterCreatedObjectUndo(root,"Place pixel desk lighting comparison");
        var a=new GameObject("A_FinalPNG_FixedShading");a.transform.SetParent(root.transform);
        var b=new GameObject("B_Actual12Meshes_LiveShading");b.transform.SetParent(root.transform);
        Vector3 right=Map(spec.camera.r),up=Map(spec.camera.u),view=Map(spec.camera.d);
        var fixture=GameObject.Find("PrototypeSteppedLocalLightFixture_Base");
        if(fixture==null) throw new InvalidOperationException("Existing base light fixture missing.");
        Vector3 horizontalView=new Vector3(view.x,0,view.z).normalized;
        Vector3 middle=fixture.transform.position-horizontalView*1.25f;
        // Exactly 232 source pixels apart, so both use the same pixel-center phase.
        a.transform.position=middle-right*(116f/spec.camera.ppu);
        b.transform.position=middle+right*(116f/spec.camera.ppu);
        Vector3 centre=V(spec.camera.bounds_center_unity);
        float halfW=spec.camera.width/(2*spec.camera.ppu),halfH=spec.camera.height/(2*spec.camera.ppu);
        var image=new GameObject("FinalPNG_174x155");image.layer=ProbeLayer;image.transform.SetParent(a.transform,false);
        var mesh=new Mesh{name="D22 native pixel image plane"};
        mesh.vertices=new[]{centre-right*halfW-up*halfH,centre+right*halfW-up*halfH,centre+right*halfW+up*halfH,centre-right*halfW+up*halfH};
        mesh.uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up};
        mesh.triangles=new[]{0,2,1,0,3,2};mesh.normals=new[]{view,view,view,view};mesh.RecalculateBounds();
        AssetDatabase.CreateAsset(mesh,AssetsPath+"/ImagePlane.asset");image.AddComponent<MeshFilter>().sharedMesh=mesh;
        var imageMaterial=new Material(Shader.Find("Universal Render Pipeline/Unlit")){name="D22 Final PNG (already shaded)"};
        imageMaterial.SetTexture("_BaseMap",AssetDatabase.LoadAssetAtPath<Texture2D>(AssetsPath+"/desk.png"));
        imageMaterial.SetFloat("_AlphaClip",1);imageMaterial.SetFloat("_Cutoff",.5f);imageMaterial.SetFloat("_Cull",0);
        imageMaterial.EnableKeyword("_ALPHATEST_ON");imageMaterial.renderQueue=(int)RenderQueue.AlphaTest;
        AssetDatabase.CreateAsset(imageMaterial,AssetsPath+"/FinalPNG.mat");
        var imageRenderer=image.AddComponent<MeshRenderer>();imageRenderer.sharedMaterial=imageMaterial;
        imageRenderer.shadowCastingMode=ShadowCastingMode.Off;imageRenderer.receiveShadows=false;
        float maxError=0;
        foreach(var part in spec.parts)
        {
            var g=GameObject.CreatePrimitive(PrimitiveType.Cube);g.name=part.name;g.layer=ProbeLayer;
            g.transform.SetParent(b.transform,false);g.transform.localPosition=V(part.unity_center);g.transform.localScale=V(part.unity_dimensions);
            Undo.DestroyObjectImmediate(g.GetComponent<Collider>());
            var mat=new Material(liveShader){name="D22 live wood "+part.name};
            mat.SetTexture("_BaseMap",AssetDatabase.LoadAssetAtPath<Texture2D>(AssetsPath+"/wood-grain.png"));
            mat.SetTexture("_EdgeMask",AssetDatabase.LoadAssetAtPath<Texture2D>(AssetsPath+"/edge-mask.png"));
            mat.SetVector("_PartCenter",V(part.center));mat.SetVector("_PartDimensions",V(part.dimensions));
            mat.SetFloat("_IsLeg",part.role=="leg"?1:0);mat.SetFloat("_TexelMeters",.024f);
            mat.SetFloat("_SteppedLocalLightStrength",.55f);
            mat.SetVector("_ScreenOrigin",new Vector4(spec.camera.screen_origin[0],spec.camera.screen_origin[1],0,0));
            mat.SetVector("_RasterSize",new Vector4(spec.camera.width,spec.camera.height,0,0));mat.SetFloat("_PixelsPerMeter",spec.camera.ppu);
            AssetDatabase.CreateAsset(mat,AssetsPath+"/Part_"+part.id+".mat");g.GetComponent<MeshRenderer>().sharedMaterial=mat;
            maxError=Mathf.Max(maxError,(g.GetComponent<MeshRenderer>().bounds.size-V(part.unity_dimensions)).magnitude);
        }
        if(maxError>0.00001f) throw new InvalidOperationException("Geometry size mismatch: "+maxError);
        PrefabUtility.SaveAsPrefabAssetAndConnect(root,AssetsPath+"/LightingComparison.prefab",InteractionMode.UserAction);
        AssetDatabase.SaveAssets();EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        var t=(TextureImporter)AssetImporter.GetAtPath(AssetsPath+"/desk.png");
        var evidence=new BuildEvidence{scene=scene.path,root=RootName,imageShader=imageMaterial.shader.name,modelShader=liveShader.name,
            actualMeshCount=b.GetComponentsInChildren<MeshRenderer>().Length,width=spec.camera.width,height=spec.camera.height,ppu=spec.camera.ppu,
            maxDimensionError=maxError,point=t.filterMode==FilterMode.Point,uncompressed=t.textureCompression==TextureImporterCompression.Uncompressed,
            noMipmaps=!t.mipmapEnabled,geometryOnlySource=true,imageOrigin=a.transform.position,modelOrigin=b.transform.position};
        Directory.CreateDirectory(OutputPath);File.WriteAllText(OutputPath+"/build.json",JsonUtility.ToJson(evidence,true));
        Selection.activeGameObject=root;
        Debug.Log("D22 pair placed beside existing base light; original image and actual 12 meshes are separate.");
    }
}
