using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

/// <summary>Actual movement and imported surface observations; no artistic approval is inferred.</summary>
public static class PixelShopInteriorObservation
{
    private static string DirectoryPath = "docs/artifacts/building34";
    private static string ReportPath => DirectoryPath + "/play-observation.json";
    [Serializable] public sealed class Access
    {
        public string id; public bool reached; public float errorMetres; public float[] actualLocal;
    }
    [Serializable] public sealed class Capture
    {
        public string path, kind, method; public int width, height;
        public float orthographicSize; public float[] position, rotation;
    }
    [Serializable] public sealed class Observation
    {
        public string producer = "UnityEditor.PixelShopInteriorObservation", scene, phase;
        public long playerBefore, playerAfter, cameraBefore, cameraAfter;
        public bool isPlayMode, entryReached, wallBlocked, roofHiddenInside, roofRestoredOutside;
        public bool closedRoof, depthPassConsistent, noDoublePixelation;
        public int accessReached, frameLeakPixels, roofLeakPixels, sourceDepthMismatches;
        public int newErrors = -1, nativeSurfaceCount, roofOpaqueTexels, roofColliderCount;
        public float pixelScale, ppu, cameraPitch, cameraYaw, roofHeight;
        public bool orthographic, nativeGridFitsZoomLimits;
        public float[] wallStopLocal, roofSurfaceMin, roofSurfaceMax, roofColliderMin, roofColliderMax;
        public Access[] accessRoutes;
        public string[] screenshots = Array.Empty<string>();
        public Capture[] captures = Array.Empty<Capture>();
        public string depthPassEvidence, closedRoofEvidence, rendererConfiguration, consoleEvidence;
        public string limitations = "Movement is StepMove API execution, not keyboard input. Captures use the same live gameplay camera; screen-space overlay HUD is excluded. Overview is explicitly reframed and restored. Pass inspection is structural evidence, not a GPU depth-buffer equality test. Artistic approval is not claimed.";
    }

    public static void Execute(string phase, string outputDirectory = "docs/artifacts/building34", string observationInput = "Tools/Building33/observation-input.json")
    {
        DirectoryPath = outputDirectory;
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Actual Play Mode required.");
        var root = GameObject.Find("PlannedPixelShop33");
        var shell = PersistentGameplayShell.Instance;
        if (root == null || shell == null || shell.PlayerCamera == null)
            throw new InvalidOperationException("Existing building, persistent Player and Camera required.");
        var building = root.GetComponent<NativePixelBuilding>();
        var fader = root.GetComponent<UrbanOcclusionFader>();
        var camera = shell.PlayerCamera;
        var follow = camera.GetComponent<CameraFollow>();
        var zoom = camera.GetComponent<CameraZoomController>();
        var movement = shell.PlayerMovement;
        Directory.CreateDirectory(DirectoryPath);
        var data = phase == "begin" ? new Observation() : JsonUtility.FromJson<Observation>(File.ReadAllText(ReportPath));
        data.phase = phase;

        void Teleport(Vector3 local)
        {
            if (!movement.TryTeleport(root.transform.TransformPoint(local), shell.PlayerTransform.rotation, out string error))
                throw new InvalidOperationException(error);
            Physics.SyncTransforms();
        }
        void MoveToward(Vector3 world, float maximumStep)
        {
            Vector3 delta = world - shell.PlayerTransform.position; delta.y = 0;
            if (delta.sqrMagnitude < .000001f) return;
            Vector3 right = camera.transform.right; right.y = 0; right.Normalize();
            Vector3 forward = camera.transform.forward; forward.y = 0; forward.Normalize();
            var direction = delta.normalized;
            movement.StepMove(new Vector2(Vector3.Dot(direction, right), Vector3.Dot(direction, forward)),
                Mathf.Min(maximumStep, delta.magnitude) / movement.speed, false);
            Physics.SyncTransforms();
        }
        void UpdateView()
        {
            follow.SetViewOrientation(camera.transform.rotation);
            fader.EvaluateVisibility(camera, shell.PlayerTransform.position, 1f);
        }
        void RecordCapture(string filename, bool overview)
        {
            var capture = CaptureCamera(root, camera, building.nativePixelsPerUnit, filename, overview);
            data.captures = data.captures.Where(x => x.path != capture.path).Append(capture).ToArray();
            data.screenshots = data.captures.Select(x => x.path).ToArray();
        }

        if (phase == "begin")
        {
            data.scene = SceneManager.GetActiveScene().name; data.isPlayMode = true;
            data.playerBefore = Identity(shell.PlayerTransform.gameObject);
            data.cameraBefore = Identity(camera.gameObject);
            var input = JsonUtility.FromJson<B33ObservationInput>(File.ReadAllText(observationInput));
            var access = new List<Access>();
            foreach (var route in input.routes)
            {
                if (route.points == null || route.points.Length == 0) throw new InvalidDataException("Empty route " + route.id);
                Teleport(new Vector3(route.points[0].x, .56f, route.points[0].z));
                foreach (var point in route.points.Skip(1))
                {
                    var target = root.transform.TransformPoint(new Vector3(point.x, .56f, point.z));
                    int steps = Mathf.CeilToInt(Vector3.Distance(target, shell.PlayerTransform.position) / .1f) + 2;
                    for (int step = 0; step < steps; step++) MoveToward(target, .1f);
                }
                var local = root.transform.InverseTransformPoint(shell.PlayerTransform.position);
                var last = route.points[route.points.Length - 1];
                float error = Vector2.Distance(new Vector2(local.x, local.z), new Vector2(last.x, last.z));
                access.Add(new Access { id = route.id, reached = error < .15f, errorMetres = error, actualLocal = Values(local) });
            }
            data.accessRoutes = access.ToArray(); data.accessReached = access.Count(x => x.reached);
            data.entryReached = access.Count == input.routes.Length && access.All(x => x.reached);
            Teleport(new Vector3(3, .56f, -3.2f));
            var beyond = root.transform.TransformPoint(new Vector3(3, .56f, -6));
            for (int i = 0; i < 25; i++) MoveToward(beyond, .1f);
            var stop = root.transform.InverseTransformPoint(shell.PlayerTransform.position);
            data.wallStopLocal = Values(stop); data.wallBlocked = stop.z > -3.65f && stop.z < -3.2f;
            Teleport(new Vector3(0, .56f, -5.5f)); UpdateView();
        }
        else if (phase == "inside")
        {
            Teleport(new Vector3(0, .56f, .3f)); UpdateView();
            data.roofHiddenInside = building.roof.Length > 0 && building.roof.All(r => r != null && !r.enabled)
                && fader.InsideBuildingCount > 0;
            RecordCapture("play-interior.png", false);
            RecordCapture("overview-interior.png", true);
        }
        else if (phase == "outside")
        {
            Teleport(new Vector3(0, .56f, -5.5f)); UpdateView();
            data.roofRestoredOutside = building.roof.Length > 0 && building.roof.All(r => r != null && r.enabled);
            RecordCapture("play-exterior.png", false);
            RecordCapture("overview-exterior.png", true);
        }
        else if (phase == "finish")
        {
            data.playerAfter = Identity(shell.PlayerTransform.gameObject); data.cameraAfter = Identity(camera.gameObject);
            data.cameraPitch = camera.transform.eulerAngles.x; data.cameraYaw = camera.transform.eulerAngles.y;
            data.orthographic = camera.orthographic; data.ppu = zoom.NativePixelsPerUnit;
            data.pixelScale = camera.scaledPixelHeight / (2f * camera.orthographicSize * data.ppu);
            data.nativeGridFitsZoomLimits = zoom.NativeGridFitsZoomLimits;
            InspectImportedSurfaces(root, building, data);
            InspectRenderer(camera, data);
        }
        else throw new ArgumentException("Expected begin, inside, outside or finish.", nameof(phase));
        File.WriteAllText(ReportPath, JsonUtility.ToJson(data, true));
        Debug.Log("B34 " + phase + " actual observation saved: " + ReportPath);
    }

    private static Capture CaptureCamera(GameObject root, Camera camera, float ppu, string filename, bool overview)
    {
        // Existing adaptive character tone stores at most 4,194,304 representative indices.
        // 2560x1600 = 4,096,000 pixels fits; 2560x1800 = 4,608,000 does not.
        // Limit this optional overview target, without changing the character algorithm or gameplay viewport.
        int width = overview ? 2560 : camera.pixelWidth, height = overview ? 1600 : camera.pixelHeight;
        if (width < 1 || height < 1) throw new InvalidOperationException("The gameplay camera has no output viewport.");
        var position = camera.transform.position; var rotation = camera.transform.rotation;
        float size = camera.orthographicSize, aspect = camera.aspect, near = camera.nearClipPlane, far = camera.farClipPlane;
        var oldTarget = camera.targetTexture; var oldActive = RenderTexture.active;
        var target = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1, filterMode = FilterMode.Point };
        var image = new Texture2D(width, height, TextureFormat.RGB24, false);
        try
        {
            target.Create();
            if (overview)
            {
                camera.transform.rotation = Quaternion.Euler(30, 350, 0);
                camera.transform.position = root.transform.TransformPoint(new Vector3(0, .8f, 0)) - camera.transform.forward * 20;
                camera.orthographicSize = height / (2f * ppu); camera.nearClipPlane = .01f; camera.farClipPlane = Mathf.Max(far, 100f);
            }
            camera.aspect = width / (float)height;
            camera.targetTexture = target;
            string method;
            if (GraphicsSettings.currentRenderPipeline != null)
            {
                // URP's synchronous equivalent of Camera.Render, on the existing camera.
                RenderPipeline.SubmitRenderRequest(camera, new UniversalRenderPipeline.SingleCameraRequest { destination = target });
                method = "RenderPipeline.SubmitRenderRequest: same existing gameplay Camera, synchronous ReadPixels";
            }
            else { camera.Render(); method = "Camera.Render: same existing gameplay Camera, synchronous ReadPixels"; }
            RenderTexture.active = target; image.ReadPixels(new Rect(0, 0, width, height), 0, 0); image.Apply();
            string path = DirectoryPath + "/" + filename; File.WriteAllBytes(path, image.EncodeToPNG());
            return new Capture { path = path, width = width, height = height, method = method,
                kind = overview ? "Actual scene overview, temporarily reframed existing camera; not walking view; overlay HUD excluded"
                    : "Actual current gameplay camera pose and viewport; overlay HUD excluded",
                orthographicSize = camera.orthographicSize, position = Values(camera.transform.position), rotation = Values(camera.transform.eulerAngles) };
        }
        finally
        {
            camera.targetTexture = oldTarget; RenderTexture.active = oldActive;
            camera.transform.SetPositionAndRotation(position, rotation); camera.orthographicSize = size;
            camera.aspect = aspect; camera.nearClipPlane = near; camera.farClipPlane = far;
            target.Release(); UnityEngine.Object.DestroyImmediate(target); UnityEngine.Object.DestroyImmediate(image);
        }
    }

    private static void InspectImportedSurfaces(GameObject root, NativePixelBuilding building, Observation data)
    {
        data.frameLeakPixels = 0; data.roofLeakPixels = 0; data.sourceDepthMismatches = 0;
        data.nativeSurfaceCount = 0; data.roofOpaqueTexels = 0; data.roofHeight = building.interior.max.y;
        bool passes = true; bool roofPointsFound = false, colliderPointsFound = false;
        var roofBounds = new Bounds(); var colliderBounds = new Bounds();
        var roofSet = new HashSet<Renderer>(building.roof);
        foreach (var renderer in root.GetComponentsInChildren<MeshRenderer>(false))
        {
            var material = renderer.sharedMaterial;
            if (material == null || !material.HasProperty("_NativeDepthEnabled") || material.GetFloat("_NativeDepthEnabled") <= .5f) continue;
            data.nativeSurfaceCount++;
            passes &= material.FindPass("DepthOnly") >= 0 && material.FindPass("DepthNormalsOnly") >= 0
                && material.GetShaderPassEnabled("DepthOnly") && material.GetShaderPassEnabled("DepthNormalsOnly");
            var source = material.GetTexture("_BaseMap") as Texture2D;
            var depth = material.GetTexture("_NativeDepthMap") as Texture2D;
            if (source == null || depth == null || source.width != depth.width || source.height != depth.height)
            { data.sourceDepthMismatches++; continue; }
            var colors = source.GetPixels(); var samples = depth.GetPixels();
            bool isRoof = roofSet.Contains(renderer);
            bool isFixture = renderer.transform.parent.parent != null &&
                (renderer.transform.parent.parent.name == "Fixtures - role plan" || renderer.transform.parent.parent.name == PixelShopProjection35.GroupName || renderer.transform.parent.parent.name == "Wall lamps - source anchors");
            for (int i = 0; i < samples.Length; i++)
            {
                bool opaque = colors[i].a > .1f, valid = samples[i].a > .5f;
                if (!opaque && valid) data.frameLeakPixels++;
                if (opaque && !valid) data.sourceDepthMismatches++;
                if (!opaque || !valid) continue;
                var local = root.transform.InverseTransformPoint(renderer.transform.TransformPoint(new Vector3(samples[i].r, samples[i].g, samples[i].b)));
                if (isFixture && local.y > data.roofHeight + .0001f) data.roofLeakPixels++;
                if (isRoof) { data.roofOpaqueTexels++; Include(ref roofBounds, ref roofPointsFound, local); }
            }
        }
        data.roofColliderCount = building.roofColliders.Count(c => c != null && c.enabled && !c.isTrigger);
        foreach (var collider in building.roofColliders.OfType<BoxCollider>())
        {
            if (!collider.enabled || collider.isTrigger) continue;
            var b = new Bounds(collider.center, collider.size);
            for (int i = 0; i < 8; i++)
            {
                var corner = new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z);
                Include(ref colliderBounds, ref colliderPointsFound, root.transform.InverseTransformPoint(collider.transform.TransformPoint(corner)));
            }
        }
        data.roofSurfaceMin = Values(roofBounds.min); data.roofSurfaceMax = Values(roofBounds.max);
        data.roofColliderMin = Values(colliderBounds.min); data.roofColliderMax = Values(colliderBounds.max);
        float tolerance = 2f / building.nativePixelsPerUnit;
        bool Covers(Bounds b) => b.min.x <= building.interior.min.x + tolerance && b.max.x >= building.interior.max.x - tolerance
            && b.min.z <= building.interior.min.z + tolerance && b.max.z >= building.interior.max.z - tolerance
            && b.min.y >= data.roofHeight - tolerance && b.max.y >= data.roofHeight;
        data.closedRoof = roofPointsFound && colliderPointsFound && Covers(roofBounds) && Covers(colliderBounds)
            && data.roofOpaqueTexels > 0 && data.sourceDepthMismatches == 0;
        string shaderPath = "Assets/Shaders/World/IsometricAtlasSurface.shader";
        string shaderSource = File.ReadAllText(shaderPath);
        bool sharedResolver = shaderSource.Split(new[] { "ResolveSurfaceDepth(input, atlasUv)" }, StringSplitOptions.None).Length - 1 == 3;
        data.depthPassConsistent = data.nativeSurfaceCount > 0 && passes && sharedResolver && data.sourceDepthMismatches == 0;
        data.depthPassEvidence = "Imported native materials: DepthOnly and DepthNormalsOnly found and enabled; Forward/Depth/Normals source share ResolveSurfaceDepth; alpha/depth domain matched. Structural/readback check only; no GPU depth-buffer equality claim.";
        data.closedRoofEvidence = "Actual imported opaque roof surface XYZ envelope plus enabled non-trigger BoxCollider coverage at interior roof height. Source-alpha/depth validity checked; opaque area count and measured bounds included. Not an artistic or full raster-occlusion judgement.";
    }

    private static void InspectRenderer(Camera camera, Observation data)
    {
        var pipeline = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
        if (pipeline == null) { data.noDoublePixelation = false; data.rendererConfiguration = "Active URP asset not found."; return; }
        var pipelineObject = new SerializedObject(pipeline);
        int index = pipelineObject.FindProperty("m_DefaultRendererIndex").intValue;
        var cameraData = camera.GetComponent<UniversalAdditionalCameraData>();
        if (cameraData != null)
        {
            var property = new SerializedObject(cameraData).FindProperty("m_RendererIndex");
            if (property != null && property.intValue >= 0) index = property.intValue;
        }
        var list = pipelineObject.FindProperty("m_RendererDataList");
        var renderer = index >= 0 && index < list.arraySize ? list.GetArrayElementAtIndex(index).objectReferenceValue as ScriptableRendererData : null;
        data.noDoublePixelation = renderer != null && !renderer.rendererFeatures.Any(x => x != null && x.isActive && x.GetType().Name == "PixelArtRendererFeature");
        data.rendererConfiguration = renderer == null ? "Camera renderer unresolved" : AssetDatabase.GetAssetPath(renderer) + "; active PixelArtRendererFeature inspected on actual camera renderer";
    }

    // Console conclusions come from complete provider snapshots and their computed
    // difference (validate_final_delivery.py), never a caller-supplied zero count.
    private static long Identity(GameObject value) => long.Parse(value.GetEntityId().ToString());
    private static float[] Values(Vector3 value) => new[] { value.x, value.y, value.z };
    private static void Include(ref Bounds bounds, ref bool found, Vector3 value)
    {
        if (!found) { bounds = new Bounds(value, Vector3.zero); found = true; } else bounds.Encapsulate(value);
    }
}
