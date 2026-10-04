using System;
using System.IO;
using System.Linq;
using FantasySurvival.WorldGeneration;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

/// <summary>One building's authoring and exact neutral-light comparison; no new runtime owner.</summary>
[InitializeOnLoad]
public static class NativeBuilding17Setup
{
    public const string AssetRoot = "Assets/Art/NativeBuilding39";
    public const float Ppu = 90.509668f;
    private static readonly Vector3 Right = new Vector3(.707106781f, 0, -.707106781f);
    private static readonly Vector3 Up = new Vector3(.353553391f, .866025404f, .353553391f);

    static NativeBuilding17Setup() => SceneView.duringSceneGui += AlignSceneView;

    private static void AlignSceneView(SceneView view)
    {
        if (view.camera == null || !view.orthographic || EditorApplication.isPlaying) return;
        var building = GameObject.Find("PlannedPixelShop33");
        if (building == null || building.scene.name != "GameMap1") return;
        var native = building.GetComponent<NativePixelBuilding>();
        if (native == null || Mathf.Abs(native.nativePixelsPerUnit - Ppu) > .001f) return;
        var preview = Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).FirstOrDefault(c => c.name == "Preview Camera");
        if (preview != null && preview.orthographic)
        {
            float unit = preview.pixelHeight / (2f * Ppu);
            int previewScale = Mathf.Max(1, Mathf.RoundToInt(unit / Mathf.Max(.01f, preview.orthographicSize)));
            float previewSize = unit / previewScale;
            if (Mathf.Abs(preview.orthographicSize-previewSize) > .00001f)
            {
                preview.orthographicSize = previewSize;
                PrefabUtility.RecordPrefabInstancePropertyModifications(preview);
            }
        }
        var angle = view.rotation.eulerAngles;
        if (Mathf.Abs(Mathf.DeltaAngle(angle.x, 30)) > .01f || Mathf.Abs(Mathf.DeltaAngle(angle.y, 350)) > .01f) return;
        float one = view.camera.pixelHeight / (2f * Ppu);
        int scale = Mathf.Max(1, Mathf.RoundToInt(one / Mathf.Max(.01f, view.camera.orthographicSize)));
        float target = one / scale;
        float sceneSize = target * Mathf.Min(1f, view.camera.aspect);
        if (Mathf.Abs(view.size - sceneSize) > .00001f) view.size = sceneSize;
    }

    public static void Configure(GameObject building)
    {
        if (EditorApplication.isPlaying || building == null) throw new InvalidOperationException("Edit-mode shop required.");
        var native = building.GetComponent<NativePixelBuilding>();
        Undo.RecordObject(native, "Common native pixel density");
        native.useNativePixelGrid = true; native.nativePixelsPerUnit = Ppu;
        PrefabUtility.RecordPrefabInstancePropertyModifications(native);

        var existing = building.transform.Find("Native17 moving light");
        if (existing == null)
        {
            var go = new GameObject("Native17 moving light"); Undo.RegisterCreatedObjectUndo(go, "Add moving stepped light");
            existing = go.transform; existing.SetParent(building.transform, false);
            go.AddComponent<SteppedLocalLight>(); go.AddComponent<NativePixelLightMotion>();
        }
        var light = existing.GetComponent<SteppedLocalLight>();
        var settings = new SerializedObject(light);
        settings.FindProperty("color").colorValue = new Color(.78f, 1f, .44f, 1f);
        settings.FindProperty("radius").floatValue = 3.8f;
        settings.FindProperty("intensity").floatValue = 4.2f;
        settings.FindProperty("surfaceBands").intValue = 4;
        settings.FindProperty("haloStrength").floatValue = 0f;
        settings.FindProperty("normalInfluence").floatValue = 1f;
        settings.FindProperty("worldCellSize").floatValue = 1f / Ppu;
        settings.ApplyModifiedProperties();
        existing.localPosition = new Vector3(0, 1.35f, 0);
        CreateMarker(existing);

        string shellPath = "Assets/Prefabs/PersistentGameplayShell.prefab";
        var shell = PrefabUtility.LoadPrefabContents(shellPath);
        try
        {
            var clock = shell.GetComponent<SkyLightingCycleController>();
            var clockData = new SerializedObject(clock);
            clockData.FindProperty("initialHour").floatValue = 21f;
            clockData.ApplyModifiedPropertiesWithoutUndo();
            // The existing runtime owner applies horizon/weather/minimum-light rules.
            // Authoring uses CaptureNightPreview/ApplyNightPreview from that actual output.
            PrefabUtility.SaveAsPrefabAsset(shell, shellPath);
        }
        finally { PrefabUtility.UnloadPrefabContents(shell); }
        var camera = Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).FirstOrDefault(c => c.name == "Preview Camera");
        if (camera != null)
        {
            Undo.RecordObject(camera, "Integer native authoring camera");
            camera.orthographicSize = camera.pixelHeight / (2f * Ppu);
            PrefabUtility.RecordPrefabInstancePropertyModifications(camera);
        }
        if (SceneView.lastActiveSceneView != null)
        {
            var view = SceneView.lastActiveSceneView;
            view.rotation = Quaternion.Euler(30, 350, 0); view.orthographic = true;
            view.pivot = building.transform.TransformPoint(new Vector3(0, .5f, 0));
            view.in2DMode = false;
            view.size = view.camera.pixelHeight / (2f * Ppu) * Mathf.Min(1f, view.camera.aspect); view.Repaint();
        }
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(building.scene);
    }

    [Serializable] private sealed class NightPreview
    {
        public float hour, intensity, shadowStrength, ambientIntensity, reflectionIntensity;
        public Color sky, equator, ground, color;
        public Quaternion rotation;
        public LightShadows shadows;
        public bool enabled;
    }

    public static void CaptureNightPreview(SkyLightingCycleController clock, string path)
    {
        if (!EditorApplication.isPlaying || clock == null || Mathf.Abs(clock.CurrentHour-21f) > .001f || clock.SceneDirectionalLight == null)
            throw new InvalidOperationException("Capture the existing owner's actual 21:00 Play Mode lighting.");
        var light=clock.SceneDirectionalLight;
        File.WriteAllText(path, JsonUtility.ToJson(new NightPreview { hour=clock.CurrentHour,
            intensity=light.intensity, color=light.color, rotation=light.transform.rotation,
            shadowStrength=light.shadowStrength, shadows=light.shadows, enabled=light.enabled,
            sky=RenderSettings.ambientSkyColor, equator=RenderSettings.ambientEquatorColor, ground=RenderSettings.ambientGroundColor,
            ambientIntensity=RenderSettings.ambientIntensity, reflectionIntensity=RenderSettings.reflectionIntensity }, true));
    }

    public static void ApplyNightPreview(string path)
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Authoring lighting requires Edit Mode.");
        var sample=JsonUtility.FromJson<NightPreview>(File.ReadAllText(path));
        if (Mathf.Abs(sample.hour-21f)>.001f) throw new InvalidDataException("Expected the owner's recorded 21:00 output.");
        var light=Object.FindObjectsByType<Light>(FindObjectsSortMode.None).First(x=>x.type==LightType.Directional);
        Undo.RecordObjects(new Object[] { light, light.transform }, "Existing owner's night authoring output");
        light.color=sample.color;light.intensity=sample.intensity;light.transform.rotation=sample.rotation;
        light.shadowStrength=sample.shadowStrength;light.shadows=sample.shadows;light.enabled=sample.enabled;
        RenderSettings.ambientMode=AmbientMode.Trilight;RenderSettings.ambientSkyColor=sample.sky;
        RenderSettings.ambientEquatorColor=sample.equator;RenderSettings.ambientGroundColor=sample.ground;
        RenderSettings.ambientIntensity=sample.ambientIntensity;RenderSettings.reflectionIntensity=sample.reflectionIntensity;
        RenderSettings.sun=light;
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(light.gameObject.scene);
    }

    private static void CreateMarker(Transform parent)
    {
        if (parent.Find("Native glow") != null) return;
        string folder = AssetRoot + "/light-marker";
        if (!AssetDatabase.IsValidFolder(folder)) AssetDatabase.CreateFolder(AssetRoot, "light-marker");
        var texture = new Texture2D(5, 5, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
        var pixels = new Color32[25];
        for (int y = 0; y < 5; y++) for (int x = 0; x < 5; x++)
            if (Mathf.Abs(x-2) + Mathf.Abs(y-2) <= 2) pixels[y*5+x] = new Color32(235, 255, 142, 255);
        texture.SetPixels32(pixels); texture.Apply(); AssetDatabase.CreateAsset(texture, folder + "/glow.asset");
        var mesh = new Mesh { name = "Five native pixel glow" };
        float half = 2.5f / Ppu;
        mesh.vertices = new[] { (-Right-Up)*half, (Right-Up)*half, (Right+Up)*half, (-Right+Up)*half };
        mesh.uv = new[] { Vector2.zero, Vector2.right, Vector2.one, Vector2.up };
        mesh.triangles = new[] { 0,1,2,0,2,3 }; mesh.RecalculateBounds(); mesh.RecalculateNormals();
        AssetDatabase.CreateAsset(mesh, folder + "/display.asset");
        var material = new Material(Shader.Find("FantasySurvival/World/Isometric Atlas Surface")) { name = "Native firefly marker" };
        material.SetTexture("_BaseMap", texture); material.SetFloat("_MetricLighting", 0);
        material.SetFloat("_NativeDepthEnabled", 0); material.SetFloat("_NativeGridEnabled", 1);
        material.SetVector("_NativeGridOriginOS", mesh.vertices[0]);
        material.SetVector("_NativeGridTexelUOS", Right/Ppu); material.SetVector("_NativeGridTexelVOS", Up/Ppu);
        AssetDatabase.CreateAsset(material, folder + "/surface.mat");
        var marker = new GameObject("Native glow"); Undo.RegisterCreatedObjectUndo(marker, "Add native light marker");
        marker.transform.SetParent(parent, false); marker.AddComponent<MeshFilter>().sharedMesh = mesh;
        var renderer = marker.AddComponent<MeshRenderer>(); renderer.sharedMaterial = material;
        renderer.shadowCastingMode = ShadowCastingMode.Off;
        AssetDatabase.SaveAssets();
    }

    [Serializable] private sealed class Manifest { public Entry[] assets; }
    [Serializable] private sealed class Entry { public string id; public int width, height; }
    public static string CompareFixture(string output, string assetRoot = AssetRoot, string[] ids = null)
    {
        var entries = JsonUtility.FromJson<Manifest>(File.ReadAllText(output + "/manifest.json")).assets;
        var root = new GameObject("N17 parity fixture") { hideFlags = HideFlags.HideAndDontSave, layer = 31 };
        root.transform.position = new Vector3(100,0,100); root.transform.rotation = Quaternion.Euler(0,305,0);
        var filter = root.AddComponent<MeshFilter>(); var renderer = root.AddComponent<MeshRenderer>(); renderer.shadowCastingMode = ShadowCastingMode.Off;
        var cameraObject = new GameObject("N17 parity camera") { hideFlags = HideFlags.HideAndDontSave };
        var camera = cameraObject.AddComponent<Camera>(); camera.enabled = false; camera.orthographic = true;
        camera.transform.rotation = Quaternion.Euler(30,350,0); camera.nearClipPlane = .01f; camera.farClipPlane = 30;
        camera.cullingMask = 1 << 31; camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = Color.clear;
        camera.allowMSAA = false; camera.GetUniversalAdditionalCameraData().renderPostProcessing = false;
        try
        {
            foreach (string id in ids ?? new[] { "empty_counter", "stock_shelf", "floor_surface" })
            {
                var e = entries.First(x => x.id == id);
                filter.sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(assetRoot + "/" + id + "/display.asset");
                var material = AssetDatabase.LoadAssetAtPath<Material>(assetRoot + "/" + id + "/surface.mat");
                float diagnostic = material.GetFloat("_DiagnosticMode"), grid = material.GetFloat("_NativeGridEnabled");
                try
                {
                    material.SetFloat("_DiagnosticMode", 5); material.SetFloat("_NativeGridEnabled", 0);
                    renderer.sharedMaterial = material; camera.orthographicSize = e.height / (2f*Ppu);
                    camera.aspect = (float)e.width / e.height;
                    camera.transform.position = root.transform.TransformPoint(filter.sharedMesh.bounds.center) - camera.transform.forward*10;
                    NativeBuilding16Observation.Capture(camera, output+"/"+id+"/gpu-fixture.png", e.width, e.height);
                }
                finally { material.SetFloat("_DiagnosticMode", diagnostic); material.SetFloat("_NativeGridEnabled", grid); }
            }
            return "Actual GPU fixture renders captured: " + (ids?.Length ?? 3);
        }
        finally { Object.DestroyImmediate(root); Object.DestroyImmediate(cameraObject); }
    }
}
