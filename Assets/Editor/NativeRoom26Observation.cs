using System;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

/// <summary>Authoring and bounded actual-game observation of the existing shop's room lamps.</summary>
public static class NativeRoom26Observation
{
    private static GameObject Building => GameObject.Find("PlannedPixelShop33");
    private static SteppedLocalLight[] Lamps => Building.GetComponentsInChildren<SteppedLocalLight>(true)
        .Where(l => l.Role == SteppedLocalLight.LightingRole.RoomLamp).ToArray();

    public static int Configure()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Configure in Edit Mode.");
        var emitters = Building.GetComponentsInChildren<SteppedLocalLight>()
            .Where(l => l.name == "Emitter" && l.transform.parent.parent.parent.name == "Interior34 - aligned native surfaces").ToArray();
        if (emitters.Length != 2) throw new InvalidOperationException("Exactly two existing active aligned wall lamps required.");
        foreach (var emitter in emitters)
        {
            Undo.RecordObject(emitter, "Separate room lamp from moving test light");
            var direct = emitter.GetComponent<Light>();
            // Unity's missing-component sentinel uses overloaded ==, not CLR ?? semantics.
            if (direct == null) direct = Undo.AddComponent<Light>(emitter.gameObject);
            if (direct == null) throw new InvalidOperationException("Could not add the room lamp's Unity Light.");
            Undo.RecordObject(direct, "Derived room point light");
            var data = new SerializedObject(emitter);
            data.FindProperty("role").enumValueIndex = (int)SteppedLocalLight.LightingRole.RoomLamp;
            data.FindProperty("roomDirectLight").objectReferenceValue = direct;
            data.FindProperty("roomIndirectMultiplier").floatValue = 1.5f;
            data.FindProperty("roomDirectMultiplier").floatValue = 30f;
            data.ApplyModifiedProperties();
            direct.lightmapBakeType = LightmapBakeType.Realtime;
            emitter.SynchronizeRoomDirectLight();
            PrefabUtility.RecordPrefabInstancePropertyModifications(emitter);
            PrefabUtility.RecordPrefabInstancePropertyModifications(direct);
            EditorUtility.SetDirty(emitter); EditorUtility.SetDirty(direct);
        }
        EditorSceneManager.MarkSceneDirty(Building.scene);
        return emitters.Length;
    }

    [MenuItem("Tools/Fantasy Survival/Room lighting/Building lamps on")]
    public static void LampsOn() => SwitchLamps(true);
    [MenuItem("Tools/Fantasy Survival/Room lighting/Building lamps off")]
    public static void LampsOff() => SwitchLamps(false);
    [MenuItem("Tools/Fantasy Survival/Room lighting/Moving test light on")]
    public static void MovingOn() => SwitchMoving(true);
    [MenuItem("Tools/Fantasy Survival/Room lighting/Moving test light off")]
    public static void MovingOff() => SwitchMoving(false);

    private static void SwitchLamps(bool on)
    {
        foreach (var lamp in Lamps)
        {
            if (!EditorApplication.isPlaying) Undo.RecordObject(lamp, "Switch building room lamps");
            lamp.SetLightingEnabled(on);
            if (!EditorApplication.isPlaying)
            {
                PrefabUtility.RecordPrefabInstancePropertyModifications(lamp);
                PrefabUtility.RecordPrefabInstancePropertyModifications(lamp.RoomDirectLight);
            }
        }
        if (!EditorApplication.isPlaying) EditorSceneManager.MarkSceneDirty(Building.scene);
    }

    private static void SwitchMoving(bool on)
    {
        var moving = Moving();
        if (!EditorApplication.isPlaying) Undo.RecordObject(moving, "Switch moving test light");
        moving.SetLightingEnabled(on);
        if (!EditorApplication.isPlaying)
        {
            PrefabUtility.RecordPrefabInstancePropertyModifications(moving);
            EditorSceneManager.MarkSceneDirty(Building.scene);
        }
    }

    private static SteppedLocalLight Moving() => Building.GetComponentsInChildren<SteppedLocalLight>(true)
        .Single(l => l.name == "Native17 moving light");
    private static string PathOf(Transform t)
    {
        string path = t.name;
        while (t.parent != null) { t = t.parent; path = t.name + "/" + path; }
        return path;
    }

    public static string GeometrySignature() => string.Join("\n", Building.GetComponentsInChildren<MeshFilter>(true)
        .OrderBy(m => PathOf(m.transform)).Select(m => PathOf(m.transform) + "|" +
            AssetDatabase.GetAssetPath(m.sharedMesh) + "|" + m.transform.localPosition.ToString("R") + "|" +
            m.transform.localRotation.ToString("R") + "|" + m.transform.localScale.ToString("R")));

    [Serializable] public sealed class MovingState
    {
        public Color color;
        public float intensity, radius, worldCellSize;
        public int surfaceBands, role;
    }
    public static MovingState ReadMoving()
    {
        var m = Moving();
        return new MovingState { color = m.Color, intensity = m.Intensity, radius = m.Radius,
            worldCellSize = m.WorldCellSize, surfaceBands = m.SurfaceBands, role = (int)m.Role };
    }

    public static string SaveFinal(string output)
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Save in Edit Mode.");
        bool geometry = GeometrySignature() == File.ReadAllText(Path.Combine(output, "baseline-geometry.txt"));
        var before = JsonUtility.FromJson<MovingState>(File.ReadAllText(Path.Combine(output, "baseline-moving.json")));
        bool mover = JsonUtility.ToJson(before) == JsonUtility.ToJson(ReadMoving());
        var lamps = Lamps;
        bool pairs = lamps.Length == 2 && lamps.All(l => l.RoomDirectLight != null &&
            l.RoomDirectLight.transform == l.transform && l.enabled == l.RoomDirectLight.enabled &&
            l.RoomDirectLight.type == LightType.Point && l.RoomDirectLight.shadows == LightShadows.Hard &&
            Mathf.Abs(l.RoomDirectLight.intensity-l.Intensity*l.RoomDirectMultiplier) < .00001f &&
            Mathf.Abs(l.RoomDirectLight.range-l.Radius) < .00001f && l.Color == Color.white);
        if (!geometry || !mover || !pairs) throw new InvalidOperationException("N26 preserved inputs or direct-light binding failed.");
        var receipt = new FinalReceipt { editPlaying = false, geometryPreserved = geometry,
            movingPreserved = mover, moving = ReadMoving(), roomLampCount = lamps.Length,
            directLightCount = lamps.Count(l => l.RoomDirectLight != null), directPairsValid = pairs,
            sceneSaved = EditorSceneManager.SaveScene(Building.scene), sceneDirty = Building.scene.isDirty };
        string json = JsonUtility.ToJson(receipt, true);
        File.WriteAllText(Path.Combine(output, "final.json"), json);
        return json;
    }

    public static string Capture(string output)
    {
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Actual Play Mode required.");
        Directory.CreateDirectory(output);
        var shell = PersistentGameplayShell.Instance;
        var camera = shell.PlayerCamera;
        var clock = shell.GetComponent<SkyLightingCycleController>();
        bool advance = clock.IsAdvancingAutomatically; float hour = clock.CurrentHour;
        var moving = Moving(); var motion = moving.GetComponent<NativePixelLightMotion>();
        bool movingEnabled = moving.enabled, motionEnabled = motion.enabled;
        var localPosition = moving.transform.localPosition;
        var lamps = Lamps; var enabled = lamps.Select(l => l.enabled).ToArray();
        var materials = Building.GetComponentsInChildren<MeshRenderer>().Select(r => r.sharedMaterial)
            .Where(m => m != null && m.shader.name == NativeBuilding16Importer.ShaderName).Distinct().ToArray();
        var diagnostic = materials.Select(m => m.GetFloat("_DiagnosticMode")).ToArray();
        string geometry = GeometrySignature(), movingState = JsonUtility.ToJson(ReadMoving());
        var playerId = shell.PlayerTransform.GetEntityId(); var cameraId = camera.GetEntityId();
        try
        {
            clock.SetAutomaticAdvance(false); clock.SetTimeHours(21);
            motion.enabled = false; moving.transform.localPosition = motion.localCenter;
            NativeBuilding16Observation.Gameplay(output, 90.509668f);
            foreach (var m in materials) m.SetFloat("_DiagnosticMode", 0);
            SwitchLamps(false); moving.SetLightingEnabled(false);
            CaptureFrame(camera, output, "all-off.png");
            SwitchLamps(true);
            var lampPixels = CaptureFrame(camera, output, "lamps-only.png");
            bool enabledPairsValid = lamps.All(l => l.enabled && l.RoomDirectLight != null && l.RoomDirectLight.enabled);
            foreach (var lamp in lamps) lamp.RoomDirectLight.shadows = LightShadows.None;
            var noShadowPixels = CaptureFrame(camera, output, "lamps-no-shadows.png");
            foreach (var lamp in lamps) lamp.SynchronizeRoomDirectLight();
            SwitchLamps(false); moving.SetLightingEnabled(true);
            CaptureFrame(camera, output, "moving-only.png");
            SwitchLamps(true);
            CaptureFrame(camera, output, "both-on.png");
            moving.SetLightingEnabled(false);
            foreach (var m in materials) m.SetFloat("_DiagnosticMode", 8);
            CaptureFrame(camera, output, "gpu-room-fill.png");
            SwitchLamps(false);
            CaptureFrame(camera, output, "gpu-room-fill-off.png");
            int shadowChanged = lampPixels.Zip(noShadowPixels, (a, b) =>
                Math.Abs(a.r-b.r)>2 || Math.Abs(a.g-b.g)>2 || Math.Abs(a.b-b.b)>2).Count(x => x);
            float nativeStrength = materials[0].GetFloat("_SteppedLocalLightStrength");
            var probes = FarProbes(camera, lamps);
            float expectedFill = lamps.Sum(l => l.Color.linear.r * l.Intensity * l.Color.a * l.RoomIndirectMultiplier) * nativeStrength;
            Vector3 outside = Building.transform.TransformPoint(new Vector3(100, .15f, 100));
            float outsideFill = lamps.Where(l => Inside(l.IlluminationVolume, outside) || Inside(l.IlluminationVolume2, outside))
                .Sum(l => l.Color.linear.r * l.Intensity * l.Color.a * l.RoomIndirectMultiplier) * nativeStrength;
            var receipt = new Receipt {
                actualPlay = true, samePlayer = playerId == shell.PlayerTransform.GetEntityId(),
                sameCamera = cameraId == camera.GetEntityId(), geometryPreserved = geometry == GeometrySignature(),
                movingPreserved = movingState == JsonUtility.ToJson(ReadMoving()), moving = ReadMoving(),
                nativePixelsOnScreen = camera.pixelHeight / (2f * camera.orthographicSize * 90.509668f),
                roomLampCount = lamps.Length,
                shaderErrors = ShaderUtil.GetShaderMessages(Shader.Find(NativeBuilding16Importer.ShaderName))
                    .Count(m => m.severity == UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error),
                shadowChangedPixels = shadowChanged, roomFillLinear = expectedFill,
                insideFarFillLinear = probes.Length > 0 ? expectedFill : 0, outsideFillLinear = outsideFill,
                pixelOrigin = "top-left", probes = probes,
                directPairsValid = enabledPairsValid && lamps.All(l => l.RoomDirectLight != null &&
                    l.RoomDirectLight.transform == l.transform && l.RoomDirectLight.type == LightType.Point &&
                    Mathf.Abs(l.RoomDirectLight.intensity - 3.6f) < .00001f &&
                    Mathf.Abs(l.RoomDirectLight.range - l.Radius) < .00001f &&
                    l.RoomDirectLight.shadows == LightShadows.Hard && !l.RoomDirectLight.enabled)
            };
            string json = JsonUtility.ToJson(receipt, true);
            File.WriteAllText(Path.Combine(output, "receipt.json"), json);
            return json;
        }
        finally
        {
            for (int i = 0; i < materials.Length; i++) materials[i].SetFloat("_DiagnosticMode", diagnostic[i]);
            for (int i = 0; i < lamps.Length; i++) lamps[i].SetLightingEnabled(enabled[i]);
            moving.SetLightingEnabled(movingEnabled); moving.transform.localPosition = localPosition;
            motion.enabled = motionEnabled; clock.SetTimeHours(hour); clock.SetAutomaticAdvance(advance);
        }
    }

    private static Color32[] CaptureFrame(Camera c, string output, string name) =>
        NativeBuilding16Observation.Capture(c, Path.Combine(output, name), c.pixelWidth, c.pixelHeight);

    private static Probe[] FarProbes(Camera camera, SteppedLocalLight[] lamps)
    {
        var points = new System.Collections.Generic.List<Probe>();
        for (float x = -5; x <= 5; x += .5f)
        for (float z = -5; z <= 5; z += .5f)
        {
            var world = Building.transform.TransformPoint(new Vector3(x, .15f, z));
            bool inside = lamps.Any(l => Inside(l.IlluminationVolume, world) || Inside(l.IlluminationVolume2, world));
            bool far = lamps.All(l => Vector3.Distance(world, l.transform.position) > l.Radius);
            var screen = camera.WorldToScreenPoint(world);
            if (!inside || !far || screen.z < 0 || screen.x < 10 || screen.y < 10 ||
                screen.x >= camera.pixelWidth-10 || screen.y >= camera.pixelHeight-10) continue;
            points.Add(new Probe { world = new[] { world.x, world.y, world.z },
                pixel = new[] { (int)screen.x, camera.pixelHeight - 1 - (int)screen.y }, inside = true, far = true });
        }
        return points.ToArray();
    }
    private static bool Inside(BoxCollider box, Vector3 p)
    {
        if (box == null) return false;
        var local = box.transform.InverseTransformPoint(p) - box.center;
        var size = box.size * .5f;
        return Mathf.Abs(local.x) <= size.x && Mathf.Abs(local.y) <= size.y && Mathf.Abs(local.z) <= size.z;
    }
    [Serializable] private sealed class Probe { public float[] world; public int[] pixel; public bool inside, far; }
    [Serializable] private sealed class Receipt
    {
        public bool actualPlay, samePlayer, sameCamera, geometryPreserved, movingPreserved, directPairsValid;
        public float nativePixelsOnScreen, roomFillLinear, insideFarFillLinear, outsideFillLinear;
        public int shaderErrors, roomLampCount, shadowChangedPixels;
        public string pixelOrigin;
        public Probe[] probes;
        public MovingState moving;
    }
    [Serializable] private sealed class FinalReceipt
    {
        public bool editPlaying, sceneDirty, sceneSaved, geometryPreserved, movingPreserved, directPairsValid;
        public int roomLampCount, directLightCount;
        public MovingState moving;
    }
}
