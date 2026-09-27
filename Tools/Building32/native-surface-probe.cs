using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using UnityEngine.Rendering.Universal;

// Run with Unity_RunCommand. Isolated coverage experiment, not a game screenshot.
internal class CommandScript : IRunCommand
{
    public void Execute(ExecutionResult result)
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Edit Mode required.");
        string folder = "docs/artifacts/building32";
        Directory.CreateDirectory(folder);
        var main = SceneManager.GetActiveScene();
        bool wasDirty = main.isDirty;
        var preview = EditorSceneManager.NewPreviewScene();
        var previousRT = RenderTexture.active;
        var temporary = new List<UnityEngine.Object>();
        var report = new StringBuilder("Isolated native floor coverage probe\n");
        try
        {
            var cameraGO = new GameObject("B32 temporary coverage camera");
            SceneManager.MoveGameObjectToScene(cameraGO, preview);
            result.RegisterObjectCreation(cameraGO);
            var camera = cameraGO.AddComponent<Camera>();
            camera.enabled = false;
            camera.scene = preview;
            camera.orthographic = true;
            camera.orthographicSize = 192f / (2 * 4 * NativePixelBuildingAuthoring.Ppu);
            camera.aspect = 320f / 192f;
            camera.transform.rotation = Quaternion.Euler(30, 45, 0);
            camera.transform.position = -camera.transform.forward * 10;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = Color.clear;
            camera.allowHDR = false;
            camera.allowMSAA = false;
            var data = camera.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = false;
            data.antialiasing = AntialiasingMode.None;
            var target = new RenderTexture(320,192,24,RenderTextureFormat.ARGB32);
            temporary.Add(target);
            target.antiAliasing = 1;
            target.Create();
            camera.targetTexture = target;

            var surface = new GameObject("B32 temporary floor");
            SceneManager.MoveGameObjectToScene(surface, preview);
            result.RegisterObjectCreation(surface);
            var filter = surface.AddComponent<MeshFilter>();
            surface.AddComponent<MeshRenderer>().sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/Art/NativePixelBuilding31/Materials/floor_wood.mat");
            var full = new UnityEngine.Mesh { name="B32 Full Rect UV inverse on XZ plane" };
            temporary.Add(full);
            full.vertices = new[]{new Vector3(-2,0,0),new Vector3(0,0,-2),new Vector3(2,0,0),new Vector3(0,0,2)};
            full.triangles = new[]{0,1,2,0,2,3};
            full.SetUVs(0,new List<Vector3>{new Vector3(0,0,1),new Vector3(1,0,1),new Vector3(1,1,1),new Vector3(0,1,1)});
            full.RecalculateBounds(); full.RecalculateNormals();
            var source = new Texture2D(2,2,TextureFormat.RGBA32,false);
            temporary.Add(source);
            source.LoadImage(File.ReadAllBytes("Assets/Art/NativePixelBuilding31/floor_wood.png"));
            if(source.width!=64 || source.height!=32) throw new InvalidOperationException("Fixture dimensions changed.");
            var pixels = source.GetPixels32();
            var readback = new Texture2D(320,192,TextureFormat.RGBA32,false);
            temporary.Add(readback);
            string[] names = {"diamond", "full-rect"};
            var meshes = new[]{AssetDatabase.LoadAssetAtPath<UnityEngine.Mesh>("Assets/Art/NativePixelBuilding31/Meshes/Floor.asset"),full};
            for(int i=0;i<2;i++)
            {
                filter.sharedMesh = meshes[i];
                camera.Render();
                RenderTexture.active = target;
                readback.ReadPixels(new Rect(0,0,320,192),0,0); readback.Apply();
                File.WriteAllBytes(folder+"/coverage-"+names[i]+".png",readback.EncodeToPNG());
                var actual = readback.GetPixels32();
                int expectedCount=0, actualCount=0, missing=0, extra=0;
                for(int y=0;y<192;y++) for(int x=0;x<320;x++)
                {
                    bool expected=x>=32&&x<288&&y>=32&&y<160&&pixels[((y-32)/4)*64+(x-32)/4].a>25;
                    bool visible=actual[y*320+x].a>25;
                    if(expected) expectedCount++;
                    if(visible) actualCount++;
                    if(expected&&!visible) missing++;
                    if(!expected&&visible) extra++;
                }
                report.AppendLine(names[i]+": expected="+expectedCount+", actual="+actualCount+", missing="+missing+", extra="+extra);
            }
            camera.targetTexture = null;
        }
        finally
        {
            RenderTexture.active = previousRT;
            EditorSceneManager.ClosePreviewScene(preview);
            foreach(var item in temporary) if(item!=null) result.DestroyObject(item);
        }
        report.AppendLine("sceneDirtyBefore="+wasDirty+", sceneDirtyAfter="+main.isDirty);
        // Clear a transient preview-creation dirty flag only after proving exact scene preservation.
        if (!wasDirty && main.isDirty)
        {
            Directory.CreateDirectory("LocalOnly/Building32");
            string copy="LocalOnly/Building32/GameMap1-preservation-check.unity";
            EditorSceneManager.SaveScene(main,copy,true);
            if(File.ReadAllText(main.path)!=File.ReadAllText(copy))
                throw new InvalidOperationException("Scene serialization changed; preserved dirty scene for inspection.");
            EditorSceneManager.SaveScene(main);
            report.AppendLine("Preservation: saved scene copy byte-identical; transient dirty flag cleared.");
        }
        report.AppendLine("After preview cleanup: sceneDirtyBefore="+wasDirty+", sceneDirtyAfter="+main.isDirty);
        report.AppendLine("Input PNG unchanged. Fixed 30/45 degree camera; 4 screen pixels per source texel; only mesh coverage differs.");
        File.WriteAllText(folder+"/coverage-report.txt",report.ToString());
        File.Copy("LocalOnly/Building32/sceneview.txt",folder+"/sceneview.txt",true);
        result.Log(report.ToString());
    }
}
