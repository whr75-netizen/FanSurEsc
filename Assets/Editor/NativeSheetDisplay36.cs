using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using UnityEditor.SceneManagement;
using System.Security.Cryptography;

/// <summary>Direct native colour display experiment. No colour resampling or per-asset scaling.</summary>
public static class NativeSheetDisplay36
{
    private const string ManifestPath = "docs/artifacts/building36/slices/manifest.json";
    private static readonly Quaternion View = Quaternion.Euler(30, 45, 0);
    private static readonly Vector3 Right = View * Vector3.right, Up = View * Vector3.up;
    [Serializable] private sealed class Cell { public string id, role; public int[] canvas_px, visible_alpha_gt_0p1_bbox_in_crop; }
    [Serializable] private sealed class Manifest { public Cell[] cells; }
    private sealed class Binding { public MeshFilter filter; public MeshRenderer renderer; public Mesh priorMesh, mesh; public Material priorMaterial, material; }
    private static readonly List<Binding> Current = new List<Binding>();
    [Serializable] private sealed class Sample
    {
        public string id, textureAsset;
        public int width, height, opaqueTexels, roofOverflowTexels;
        public float[] screenU, screenV;
        public float maxLocalY;
    }
    [Serializable] private sealed class Report
    {
        public string scene, gameCapture = "docs/artifacts/building36/R3/play-interior.png", overviewCapture = "docs/artifacts/building36/R3/overview-interior.png";
        public bool playMode;
        public float cameraPitch, cameraYaw, pixelScale, ppu;
        public Sample[] samples;
    }

    public static void BeginExperiment()
    {
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Transient experiment requires actual Play Mode.");
        if (Current.Count != 0) throw new InvalidOperationException("An experiment is already active; do not stack changes.");
        var root = GameObject.Find("PlannedPixelShop33");
        if (root == null) throw new InvalidOperationException("Existing building required.");
        var manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(ManifestPath));
        var content = root.transform.Find(PixelShopInteriorCompletion.ContentName);
        if (content == null) throw new InvalidOperationException("Preserved content required.");
        var fixtures = content.Find(PixelShopProjection35.GroupName);
        var details = content.Find(PixelShopProjection35.DetailsGroupName);
        var targets = new[] { (fixtures.Find("stock_shelf"), "stock_shelf"), (details.Find("wall_clock"), "detail_clock") };
        var camera = PersistentGameplayShell.Instance.PlayerCamera;
        var building = root.GetComponent<NativePixelBuilding>();
        var samples = new List<Sample>();
        try
        {
            foreach (var target in targets)
            {
                var cell = manifest.cells.Single(x => x.id == target.Item2 && x.role == "object");
                var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(NativeSheetImport36.Folder + "/" + cell.id + ".png");
                if (sprite == null || sprite.texture.width != cell.canvas_px[0] || sprite.texture.height != cell.canvas_px[1])
                    throw new InvalidDataException("Native import missing or changed: " + cell.id);
                var visual = target.Item1.Find("Native surface");
                var filter = visual.GetComponent<MeshFilter>(); var renderer = visual.GetComponent<MeshRenderer>();
                if (visual.localScale != Vector3.one || target.Item1.localScale != Vector3.one)
                    throw new InvalidDataException("Nonunit existing transform: " + cell.id);
                float ppu = sprite.pixelsPerUnit;
                var box = cell.visible_alpha_gt_0p1_bbox_in_crop;
                float anchorX = (box[0] + box[2]) * .5f, anchorY = box[3];
                Vector3 P(float u, float v) => Right * ((u - anchorX) / ppu) + Up * ((anchorY - v) / ppu);
                int w = cell.canvas_px[0], h = cell.canvas_px[1];
                var mesh = new Mesh { name = "R3 native " + cell.id,
                    vertices = new[] { P(0, h), P(w, h), P(w, 0), P(0, 0) }, triangles = new[] { 0, 1, 2, 0, 2, 3 } };
                mesh.SetUVs(0, new List<Vector3> { new Vector3(0,0,1),new Vector3(1,0,1),new Vector3(1,1,1),new Vector3(0,1,1) });
                mesh.RecalculateNormals(); mesh.RecalculateBounds();
                var material = new Material(Shader.Find("FantasySurvival/World/Isometric Atlas Surface")) { name = "R3 unchanged " + cell.id };
                material.SetTexture("_BaseMap", sprite.texture); material.SetFloat("_VertexAtlasUv", 1);
                material.SetFloat("_NativeGridEnabled", 1); material.SetFloat("_NativeDepthEnabled", 0); material.SetFloat("_MetricLighting", 0);
                material.SetVector("_NativeGridOriginOS", mesh.vertices[0]);
                material.SetVector("_NativeGridTexelUOS", Right / ppu); material.SetVector("_NativeGridTexelVOS", Up / ppu);
                Current.Add(new Binding { filter = filter, renderer = renderer, priorMesh = filter.sharedMesh,
                    priorMaterial = renderer.sharedMaterial, mesh = mesh, material = material });
                filter.sharedMesh = mesh; renderer.sharedMaterial = material;
                var zero = camera.WorldToScreenPoint(visual.TransformPoint(Vector3.zero));
                var uStep = camera.WorldToScreenPoint(visual.TransformPoint(Right / ppu)) - zero;
                var vStep = camera.WorldToScreenPoint(visual.TransformPoint(Up / ppu)) - zero;
                var sample = new Sample { id = cell.id, textureAsset = AssetDatabase.GetAssetPath(sprite.texture), width = w, height = h,
                    screenU = new[] { uStep.x, uStep.y }, screenV = new[] { vStep.x, vStep.y }, maxLocalY = float.MinValue };
                var pixels = sprite.texture.GetPixels32();
                for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
                {
                    if (pixels[y * w + x].a < 26) continue;
                    var point = root.transform.InverseTransformPoint(visual.TransformPoint(P(x + .5f, h - y - .5f)));
                    sample.opaqueTexels++; sample.maxLocalY = Mathf.Max(sample.maxLocalY, point.y);
                    if (point.y > building.interior.max.y + .00001f) sample.roofOverflowTexels++;
                }
                samples.Add(sample);
            }
        }
        catch { EndExperiment(); throw; }
        Directory.CreateDirectory("docs/artifacts/building36/R3");
        if (File.Exists("docs/artifacts/building36/R3/report.json"))
        { EndExperiment(); throw new InvalidOperationException("Preserve prior experiment; do not overwrite report."); }
        var report = new Report { scene = root.scene.path, playMode = EditorApplication.isPlaying,
            cameraPitch = camera.transform.eulerAngles.x, cameraYaw = camera.transform.eulerAngles.y,
            ppu = AssetDatabase.LoadAssetAtPath<Sprite>(NativeSheetImport36.Folder + "/stock_shelf.png").pixelsPerUnit,
            samples = samples.ToArray() };
        report.pixelScale = camera.scaledPixelHeight / (2f * camera.orthographicSize * report.ppu);
        File.WriteAllText("docs/artifacts/building36/R3/report.json", JsonUtility.ToJson(report, true));
        Debug.Log("R3 transient: two direct native surfaces. No scene/prefab saved.");
    }

    public static void EndExperiment()
    {
        foreach (var item in Current)
        {
            if (item.filter != null) item.filter.sharedMesh = item.priorMesh;
            if (item.renderer != null) item.renderer.sharedMaterial = item.priorMaterial;
            UnityEngine.Object.DestroyImmediate(item.mesh); UnityEngine.Object.DestroyImmediate(item.material);
        }
        Current.Clear();
    }

    [Serializable] private sealed class InstancePlan { public string id, asset, asset_variant, support, facing; }
    [Serializable] private sealed class Placement { public InstancePlan[] instances; }
    [Serializable] private sealed class NativeCell { public string id, role, output, sha256; public int[] canvas_px; }
    [Serializable] private sealed class NativeManifest { public string native_sha256; public NativeCell[] cells; }
    private sealed class AssetPlane
    {
        public string id; public Texture2D texture; public Color32[] pixels; public Vector3 normal, planePoint;
        public bool wall; public float preservedWallTop; public int width, height; public Mesh mesh; public Material material;
    }
    private sealed class Target { public InstancePlan plan; public Transform t, visual; public MeshFilter filter; public MeshRenderer renderer; public AssetPlane plane; }
    [Serializable] private sealed class State
    {
        public string entityId, mesh, material, texture, collider;
        public float[] position, rotation, scale;
    }
    [Serializable] private sealed class AppliedBinding { public string instance, asset; public State before, after; public float minY, maxY; }
    [Serializable] private sealed class AppliedReport
    {
        public string scene, canonicalHash, representation = "Direct RGBA, orthographic ray-plane intersection; planar 2D art, not reconstructed volume.";
        public int displayMultiplier, importedRgbaMismatches;
        public float ppu, roofHeight;
        public AppliedBinding[] bindings;
        public CandidateFit[] candidates;
    }
    [Serializable] private sealed class CandidateFit { public int q; public string[] outside; }
    [Serializable] private sealed class Gate { public int exit_code = -1; public string planHash, experimentHash, authoringCodeHash; }

    /// <summary>Author native surfaces on declared front/support planes; texture pixels are never transformed.</summary>
    public static void ApplyPlanarSources(Action<UnityEngine.Object> recordModification, string mode = "apply",
        string folder = NativeSheetImport36.Folder, string manifestPath = ManifestPath, string output = "docs/artifacts/building36/R4")
    {
        bool transient = mode == "experiment", preview = mode == "plan";
        if (mode != "apply" && !transient && !preview) throw new ArgumentException("Unknown phase.");
        if (EditorApplication.isPlaying != transient) throw new InvalidOperationException("Experiment requires Play; planning/integration require Edit Mode.");
        if (transient && Current.Count != 0) throw new InvalidOperationException("Do not stack experiments.");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        if (scene.path != "Assets/Scenes/GameMap1.unity" || scene.isDirty) throw new InvalidOperationException("Expected saved GameMap1 before binding.");
        string reportPath = output + (preview ? "/support-plan.json" : transient ? "/experiment.json" : "/binding.json");
        if (File.Exists(reportPath)) throw new InvalidOperationException("Existing phase: read its result rather than repeat.");
        if (!preview && !transient && !File.Exists(output + "/gate.json")) throw new InvalidOperationException("Representative rendering gate required before integration.");
        if (!preview && !transient && JsonUtility.FromJson<Gate>(File.ReadAllText(output + "/gate.json")).exit_code != 0)
            throw new InvalidDataException("Representative gate failed; no integration allowed.");
        if (!preview && !transient && folder != NativeSheetImport36.Folder)
        {
            var gate = JsonUtility.FromJson<Gate>(File.ReadAllText(output + "/gate.json"));
            if (Sha(output + "/support-plan.json") != gate.planHash || Sha(output + "/experiment.json") != gate.experimentHash ||
                Sha("Assets/Editor/NativeSheetDisplay36.cs") != gate.authoringCodeHash)
                throw new InvalidDataException("Representative evidence inputs changed; no integration allowed.");
        }
        var root = GameObject.Find("PlannedPixelShop33");
        var building = root.GetComponent<NativePixelBuilding>();
        if (!building.useNativePixelGrid || root.transform.lossyScale != Vector3.one) throw new InvalidDataException("Existing common grid and unit building scale required.");
        float cameraPpu = building.nativePixelsPerUnit;
        var native = JsonUtility.FromJson<NativeManifest>(File.ReadAllText(manifestPath));
        var cells = native.cells.Where(x => x.role == "object").ToDictionary(x => x.id);
        if (cells.Count != 18) throw new InvalidDataException("Expected 18 canonical crops.");
        var content = root.transform.Find(PixelShopInteriorCompletion.ContentName);
        var targets = new List<Target>();
        var planes = new Dictionary<string, AssetPlane>();
        foreach (var pair in new[] { ("docs/artifacts/building35/placement.json", PixelShopProjection35.GroupName),
            ("docs/artifacts/building35/details/placement.json", PixelShopProjection35.DetailsGroupName) })
        {
            var plan = JsonUtility.FromJson<Placement>(File.ReadAllText(pair.Item1));
            var group = content.Find(pair.Item2);
            foreach (var item in plan.instances)
            {
                string id = string.IsNullOrEmpty(item.asset_variant) ? item.asset : item.asset_variant;
                var t = group.Find(item.id); var visual = t.Find("Native surface");
                if (t.localScale != Vector3.one || visual.localScale != Vector3.one || visual.localRotation != Quaternion.identity)
                    throw new InvalidDataException("Noncanonical existing transform: " + item.id);
                var target = new Target { plan = item, t = t, visual = visual, filter = visual.GetComponent<MeshFilter>(), renderer = visual.GetComponent<MeshRenderer>() };
                if (!planes.TryGetValue(id, out var p))
                {
                    var cell = cells[id]; string assetPath = folder + "/" + id + ".png";
                    if (Sha(assetPath) != cell.sha256 || Sha(cell.output) != cell.sha256) throw new InvalidDataException("Source PNG changed: " + id);
                    var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
                    var decoded = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                    try
                    {
                        ImageConversion.LoadImage(decoded, File.ReadAllBytes(cell.output));
                        if (!decoded.GetPixels32().SequenceEqual(texture.GetPixels32())) throw new InvalidDataException("Imported RGBA changed: " + id);
                    }
                    finally { UnityEngine.Object.DestroyImmediate(decoded); }
                    p = new AssetPlane { id = id, texture = texture, pixels = texture.GetPixels32(), width = texture.width, height = texture.height,
                        wall = item.support.StartsWith("wall_") };
                    if (p.wall)
                    {
                        // Existing wall template owns attachment plane and upper mounting line.
                        var depth = (Texture2D)target.renderer.sharedMaterial.GetTexture("_NativeDepthMap");
                        var valid = depth.GetPixels().Where(c => c.a > .5f).ToArray();
                        if (valid.Length == 0) throw new InvalidDataException("Wall attachment geometry missing: " + id);
                        p.preservedWallTop = valid.Max(c => c.g);
                        p.normal = item.support == "wall_right" ? Vector3.right : Vector3.forward;
                        float coord = item.support == "wall_right" ? valid.Min(c => c.r) : valid.Min(c => c.b);
                        p.planePoint = p.normal * coord;
                    }
                    else
                    {
                        var collider = t.GetComponent<BoxCollider>();
                        if (collider == null) throw new InvalidDataException("Authored footprint missing: " + id);
                        if (item.facing == "-X" || item.facing == "+X")
                        { p.normal = Vector3.right; p.planePoint = Vector3.right * collider.size.x * .5f * (item.facing == "-X" ? -1 : 1); }
                        else if (item.facing == "-Z" || item.facing == "+Z")
                        { p.normal = Vector3.forward; p.planePoint = Vector3.forward * collider.size.z * .5f * (item.facing == "-Z" ? -1 : 1); }
                        else
                        {
                            var forward = View * Vector3.forward; forward.y = 0; forward.Normalize(); p.normal = forward;
                            // No front face is authored for these sprites. The declared
                            // support/foot anchor owns their vertical display plane.
                            p.planePoint = Vector3.zero;
                        }
                    }
                    planes.Add(id, p);
                }
                target.plane = p; targets.Add(target);
            }
        }
        if (targets.Count != 26 || planes.Count != 18) throw new InvalidDataException("Preserved binding set mismatch.");
        int q;
        var candidates = new List<CandidateFit>();
        // A single density for every source, chosen by the host's actual enclosure.
        // This changes neither PNG dimensions nor its texels and never scales one asset separately.
        for (q = 6; q >= 1; q--)
        {
            foreach (var p in planes.Values) p.mesh = CreatePlanarMesh(p, cameraPpu / q);
            var outside = targets.Where(t => !OpaqueCorners(t.plane, t.plane.mesh).All(point =>
            {
                var local = root.transform.InverseTransformPoint(t.visual.TransformPoint(point));
                return local.y >= building.interior.min.y - .0001f && local.y <= building.interior.max.y + .0001f &&
                    local.x >= building.interior.min.x && local.x <= building.interior.max.x &&
                    local.z >= building.interior.min.z && local.z <= building.interior.max.z;
            })).Select(t => t.plan.id).ToArray();
            candidates.Add(new CandidateFit { q = q, outside = outside });
            if (outside.Length == 0) break;
            foreach (var p in planes.Values) { UnityEngine.Object.DestroyImmediate(p.mesh); p.mesh = null; }
        }
        if (q < 1) throw new InvalidDataException("Native art cannot fit enclosure at any positive shared integer density. No bindings changed.");
        float ppu = cameraPpu / q;
        if (!preview && !transient)
        {
            var plan = JsonUtility.FromJson<AppliedReport>(File.ReadAllText(output + "/support-plan.json"));
            if (plan.displayMultiplier != q || plan.canonicalHash != native.native_sha256)
                throw new InvalidDataException("Current calculation differs from tested plan; no integration allowed.");
        }
        var report = new AppliedReport { scene = scene.path, canonicalHash = native.native_sha256, ppu = ppu, displayMultiplier = q, roofHeight = building.interior.max.y, candidates = candidates.ToArray() };
        var bindings = targets.Select(t => new AppliedBinding { instance = t.plan.id, asset = t.plane.id, before = ReadState(t) }).ToArray();
        if (preview)
        {
            for (int i = 0; i < targets.Count; i++)
            {
                var t = targets[i]; var points = OpaqueCorners(t.plane, t.plane.mesh).Select(point => root.transform.InverseTransformPoint(t.visual.TransformPoint(point))).ToArray();
                bindings[i].minY = points.Min(v => v.y); bindings[i].maxY = points.Max(v => v.y);
            }
            report.bindings = bindings; Directory.CreateDirectory(output); File.WriteAllText(reportPath, JsonUtility.ToJson(report, true));
            foreach (var p in planes.Values) UnityEngine.Object.DestroyImmediate(p.mesh);
            Debug.Log("R4 preflight: unchanged native PNGs, all 26 placements fit, shared q=" + q + ". No Unity assets or bindings changed.");
            return;
        }
        if (transient)
        {
            var camera = PersistentGameplayShell.Instance.PlayerCamera; var samples = new List<Sample>();
            foreach (var t in targets.Where(t => t.plan.id == "stock_shelf" || t.plan.id == "wall_clock"))
            {
                var p = t.plane; p.material = CreateMaterial(p, ppu);
                Current.Add(new Binding { filter = t.filter, renderer = t.renderer, priorMesh = t.filter.sharedMesh, priorMaterial = t.renderer.sharedMaterial, mesh = p.mesh, material = p.material });
                t.filter.sharedMesh = p.mesh; t.renderer.sharedMaterial = p.material;
                var zero = camera.WorldToScreenPoint(t.visual.TransformPoint(Vector3.zero));
                var uStep = camera.WorldToScreenPoint(t.visual.TransformPoint((p.mesh.vertices[1] - p.mesh.vertices[0]) / p.width)) - zero;
                var vStep = camera.WorldToScreenPoint(t.visual.TransformPoint((p.mesh.vertices[3] - p.mesh.vertices[0]) / p.height)) - zero;
                var corners = OpaqueCorners(p, p.mesh).Select(point => root.transform.InverseTransformPoint(t.visual.TransformPoint(point))).ToArray();
                samples.Add(new Sample { id = p.id, textureAsset = AssetDatabase.GetAssetPath(p.texture), width = p.width, height = p.height,
                    screenU = new[] { uStep.x, uStep.y }, screenV = new[] { vStep.x, vStep.y },
                    maxLocalY = corners.Max(v => v.y), roofOverflowTexels = corners.Count(v => v.y > building.interior.max.y + .0001f), opaqueTexels = p.pixels.Count(c => c.a >= 26) });
            }
            foreach (var p in planes.Values.Where(p => !Current.Any(c => c.mesh == p.mesh))) UnityEngine.Object.DestroyImmediate(p.mesh);
            Directory.CreateDirectory(output);
            var experiment = new Report { scene = scene.path, playMode = true, ppu = ppu, pixelScale = camera.scaledPixelHeight / (2f * camera.orthographicSize * ppu),
                cameraPitch = camera.transform.eulerAngles.x, cameraYaw = camera.transform.eulerAngles.y, samples = samples.ToArray(),
                gameCapture = output + "/play-interior.png", overviewCapture = output + "/overview-interior.png" };
            File.WriteAllText(reportPath, JsonUtility.ToJson(experiment, true));
            Debug.Log("R4 transient: two inverse-projected support planes, shared q=" + q + ". No scene/prefab saved."); return;
        }
        EnsureFolder(folder + "/Meshes"); EnsureFolder(folder + "/Materials");
        foreach (var p in planes.Values)
        {
            string meshPath = folder + "/Meshes/" + p.id + ".asset";
            string materialPath = folder + "/Materials/" + p.id + ".mat";
            if (File.Exists(meshPath) || File.Exists(materialPath)) throw new InvalidDataException("Existing asset collision: " + p.id);
        }
        foreach (var p in planes.Values)
        {
            AssetDatabase.CreateAsset(p.mesh, folder + "/Meshes/" + p.id + ".asset");
            p.material = CreateMaterial(p, ppu);
            AssetDatabase.CreateAsset(p.material, folder + "/Materials/" + p.id + ".mat");
            var importer = (TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(p.texture));
            importer.spritePixelsPerUnit = ppu; importer.SaveAndReimport();
        }
        for (int i = 0; i < targets.Count; i++)
        {
            var t = targets[i]; recordModification(t.filter); recordModification(t.renderer);
            t.filter.sharedMesh = t.plane.mesh; t.renderer.sharedMaterial = t.plane.material;
            PrefabUtility.RecordPrefabInstancePropertyModifications(t.filter); PrefabUtility.RecordPrefabInstancePropertyModifications(t.renderer);
            bindings[i].after = ReadState(t);
            var points = OpaqueCorners(t.plane, t.plane.mesh).Select(point => root.transform.InverseTransformPoint(t.visual.TransformPoint(point))).ToArray();
            bindings[i].minY = points.Min(v => v.y); bindings[i].maxY = points.Max(v => v.y);
        }
        report.bindings = bindings;
        // Only the mesh/material fields are applied to their original prefab; layout and colliders are untouched.
        foreach (var t in targets)
        {
            PrefabUtility.ApplyPropertyOverride(new SerializedObject(t.filter).FindProperty("m_Mesh"), PixelShopInteriorCompletion.Prefab, InteractionMode.AutomatedAction);
            PrefabUtility.ApplyPropertyOverride(new SerializedObject(t.renderer).FindProperty("m_Materials.Array.data[0]"), PixelShopInteriorCompletion.Prefab, InteractionMode.AutomatedAction);
        }
        AssetDatabase.SaveAssets(); EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
        Directory.CreateDirectory(output); File.WriteAllText(reportPath, JsonUtility.ToJson(report, true));
        Debug.Log("R4: 26 existing objects bound to 18 unchanged PNGs, shared q=" + q + ", planar depth. Actual Play/capture validation pending.");
    }

    private static Material CreateMaterial(AssetPlane p, float ppu)
    {
        var material = new Material(Shader.Find("FantasySurvival/World/Isometric Atlas Surface")) { name = "native " + p.id };
        material.SetTexture("_BaseMap", p.texture); material.SetFloat("_VertexAtlasUv", 1);
        material.SetFloat("_NativeDepthEnabled", 0); material.SetFloat("_NativeGridEnabled", 1); material.SetFloat("_MetricLighting", 0);
        material.SetVector("_NativeGridOriginOS", p.mesh.vertices[0]);
        material.SetVector("_NativeGridTexelUOS", (p.mesh.vertices[1] - p.mesh.vertices[0]) / p.width);
        material.SetVector("_NativeGridTexelVOS", (p.mesh.vertices[3] - p.mesh.vertices[0]) / p.height);
        return material;
    }

    public static void ImportExactCrops(string manifestPath, string folder, Action<UnityEngine.Object> recordCreation)
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Edit Mode import required.");
        var manifest = JsonUtility.FromJson<NativeManifest>(File.ReadAllText(manifestPath));
        EnsureFolder(folder);
        foreach (var cell in manifest.cells.Where(c => c.role == "object"))
        {
            string path = folder + "/" + cell.id + ".png";
            if (File.Exists(path)) throw new InvalidDataException("Do not overwrite an existing crop: " + path);
            if (Sha(cell.output) != cell.sha256) throw new InvalidDataException("Crop hash changed: " + cell.id);
            File.Copy(cell.output, path);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.textureType = TextureImporterType.Sprite; importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = 127; importer.filterMode = FilterMode.Point; importer.wrapMode = TextureWrapMode.Clamp;
            importer.mipmapEnabled = false; importer.npotScale = TextureImporterNPOTScale.None;
            importer.textureCompression = TextureImporterCompression.Uncompressed; importer.maxTextureSize = 4096;
            importer.alphaSource = TextureImporterAlphaSource.FromInput; importer.alphaIsTransparency = false;
            importer.sRGBTexture = true; importer.isReadable = true;
            var settings = new TextureImporterSettings(); importer.ReadTextureSettings(settings);
            settings.spriteMeshType = SpriteMeshType.FullRect; settings.spriteGenerateFallbackPhysicsShape = false;
            settings.spriteAlignment = (int)SpriteAlignment.Center; importer.SetTextureSettings(settings);
            var platform = importer.GetDefaultPlatformTextureSettings(); platform.format = TextureImporterFormat.RGBA32;
            platform.textureCompression = TextureImporterCompression.Uncompressed; importer.SetPlatformTextureSettings(platform);
            importer.SaveAndReimport();
            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path); var decoded = new Texture2D(2,2,TextureFormat.RGBA32,false);
            try
            {
                ImageConversion.LoadImage(decoded, File.ReadAllBytes(cell.output));
                if (texture.width != cell.canvas_px[0] || texture.height != cell.canvas_px[1] ||
                    !texture.GetPixels32().SequenceEqual(decoded.GetPixels32()) || Sha(path) != cell.sha256)
                    throw new InvalidDataException("Exact import failed: " + cell.id);
            }
            finally { UnityEngine.Object.DestroyImmediate(decoded); }
            recordCreation(texture);
        }
        Debug.Log("Exact canonical crops imported; no PNG resize or colour/depth reprojection.");
    }

    private static Mesh CreatePlanarMesh(AssetPlane p, float ppu)
    {
        Vector3 forward = View * Vector3.forward;
        float denom = Vector3.Dot(p.normal, forward);
        if (Mathf.Abs(denom) < .0001f) throw new InvalidDataException("Attachment plane parallel to view: " + p.id);
        Vector3 Position(float u, float v)
        {
            var screenPlane = Right * (u / ppu) + Up * (-v / ppu);
            // The source ray starts at the authored attachment anchor, not the
            // camera-plane origin. Otherwise a front-plane Z displacement also
            // creates an unintended X displacement (and conversely).
            return p.planePoint + screenPlane - forward * (Vector3.Dot(p.normal, screenPlane) / denom);
        }
        var opaque = Enumerable.Range(0, p.pixels.Length).Where(i => p.pixels[i].a >= 26).ToArray();
        if (opaque.Length == 0) throw new InvalidDataException("Empty canonical source: " + p.id);
        int minX = opaque.Min(i => i % p.width), maxX = opaque.Max(i => i % p.width) + 1;
        float anchorX = (minX + maxX) * .5f;
        Vector3 horizontalShift = Position(anchorX, 0) - Position(0, 0);
        float minY = float.MaxValue, maxY = float.MinValue;
        foreach (int i in opaque)
        {
            int x = i % p.width, y = p.height - 1 - i / p.width;
            for (int dx = 0; dx <= 1; dx++) for (int dy = 0; dy <= 1; dy++)
            { float h = (Position(x + dx, y + dy) - horizontalShift).y; minY = Mathf.Min(minY, h); maxY = Mathf.Max(maxY, h); }
        }
        Vector3 shift = -horizontalShift + Vector3.up * (p.wall ? p.preservedWallTop - maxY : -minY);
        var mesh = new Mesh { name = p.id,
            vertices = new[] { Position(0, p.height) + shift, Position(p.width, p.height) + shift, Position(p.width, 0) + shift, Position(0, 0) + shift },
            triangles = new[] { 0, 1, 2, 0, 2, 3 } };
        mesh.SetUVs(0, new List<Vector3> { new Vector3(0,0,1),new Vector3(1,0,1),new Vector3(1,1,1),new Vector3(0,1,1) });
        mesh.RecalculateNormals(); mesh.RecalculateBounds(); return mesh;
    }
    private static IEnumerable<Vector3> OpaqueCorners(AssetPlane p, Mesh mesh)
    {
        var origin = mesh.vertices[3]; var right = (mesh.vertices[2] - origin) / p.width; var down = (mesh.vertices[0] - origin) / p.height;
        for (int i = 0; i < p.pixels.Length; i++) if (p.pixels[i].a >= 26)
        {
            int x = i % p.width, y = p.height - 1 - i / p.width;
            for (int dx = 0; dx <= 1; dx++) for (int dy = 0; dy <= 1; dy++) yield return origin + right * (x + dx) + down * (y + dy);
        }
    }

    [Serializable] private sealed class LiveSample
    {
        public string instance, asset, mesh, material, texture;
        public float[] screenU, screenV;
        public int rgbaMismatches, width, height, boundsOverflowCorners;
        public float minY, maxY;
        public State state;
    }
    [Serializable] private sealed class LiveReport
    {
        public string scene, playerEntityId, cameraEntityId;
        public bool playMode, orthographic;
        public float cameraPitch, cameraYaw, displayMultiplier;
        public LiveSample[] samples;
    }
    public static void ObserveLive(string folder, string manifestPath, string output)
    {
        if (!EditorApplication.isPlaying) throw new InvalidOperationException("Actual Play Mode required.");
        if (File.Exists(output)) throw new InvalidOperationException("Preserve live observation rather than repeat.");
        var root = GameObject.Find("PlannedPixelShop33"); var shell = PersistentGameplayShell.Instance; var camera = shell.PlayerCamera;
        var interior = root.GetComponent<NativePixelBuilding>().interior;
        var cells = JsonUtility.FromJson<NativeManifest>(File.ReadAllText(manifestPath)).cells.Where(c => c.role == "object").ToDictionary(c => c.id);
        var samples = new List<LiveSample>(); var content = root.transform.Find(PixelShopInteriorCompletion.ContentName);
        foreach (var pair in new[] { ("docs/artifacts/building35/placement.json", PixelShopProjection35.GroupName),
            ("docs/artifacts/building35/details/placement.json", PixelShopProjection35.DetailsGroupName) })
        foreach (var item in JsonUtility.FromJson<Placement>(File.ReadAllText(pair.Item1)).instances)
        {
            string id = string.IsNullOrEmpty(item.asset_variant) ? item.asset : item.asset_variant;
            var t = content.Find(pair.Item2).Find(item.id); var visual = t.Find("Native surface");
            var target = new Target { t = t, visual = visual, filter = visual.GetComponent<MeshFilter>(), renderer = visual.GetComponent<MeshRenderer>() };
            var texture = (Texture2D)target.renderer.sharedMaterial.mainTexture;
            if (AssetDatabase.GetAssetPath(texture) != folder + "/" + id + ".png") throw new InvalidDataException("Unexpected live source: " + item.id);
            var mesh = target.filter.sharedMesh; var vertices = mesh.vertices;
            var zero = camera.WorldToScreenPoint(visual.TransformPoint(Vector3.zero));
            var u = camera.WorldToScreenPoint(visual.TransformPoint((vertices[1]-vertices[0])/texture.width)) - zero;
            var v = camera.WorldToScreenPoint(visual.TransformPoint((vertices[3]-vertices[0])/texture.height)) - zero;
            var decoded = new Texture2D(2,2,TextureFormat.RGBA32,false);
            int mismatches;
            try { ImageConversion.LoadImage(decoded,File.ReadAllBytes(cells[id].output)); var expected = decoded.GetPixels32(); var actual = texture.GetPixels32(); mismatches = actual.Where((c,i)=>!c.Equals(expected[i])).Count(); }
            finally { UnityEngine.Object.DestroyImmediate(decoded); }
            var p = new AssetPlane { width=texture.width, height=texture.height, pixels=texture.GetPixels32() };
            var corners = OpaqueCorners(p,mesh).Select(point=>root.transform.InverseTransformPoint(visual.TransformPoint(point))).ToArray();
            int overflow = corners.Count(point=>point.x<interior.min.x-.0001f||point.x>interior.max.x+.0001f||point.y<interior.min.y-.0001f||point.y>interior.max.y+.0001f||point.z<interior.min.z-.0001f||point.z>interior.max.z+.0001f);
            samples.Add(new LiveSample { instance=item.id,asset=id,mesh=AssetDatabase.GetAssetPath(mesh),material=AssetDatabase.GetAssetPath(target.renderer.sharedMaterial),
                texture=AssetDatabase.GetAssetPath(texture),width=texture.width,height=texture.height,rgbaMismatches=mismatches,
                screenU=new[]{u.x,u.y},screenV=new[]{v.x,v.y},boundsOverflowCorners=overflow,minY=corners.Min(c=>c.y),maxY=corners.Max(c=>c.y),state=ReadState(target) });
        }
        var report = new LiveReport { scene=root.scene.path,playMode=true,orthographic=camera.orthographic,cameraPitch=camera.transform.eulerAngles.x,cameraYaw=camera.transform.eulerAngles.y,
            playerEntityId=shell.PlayerTransform.gameObject.GetEntityId().ToString(),cameraEntityId=camera.gameObject.GetEntityId().ToString(),displayMultiplier=samples[0].screenU[0],samples=samples.ToArray() };
        File.WriteAllText(output,JsonUtility.ToJson(report,true)); Debug.Log("Actual26 native binding/source/projection observations saved: "+output);
    }
    private static State ReadState(Target t)
    {
        var collider = t.t.GetComponent<BoxCollider>();
        return new State { entityId = t.t.gameObject.GetEntityId().ToString(), mesh = AssetDatabase.GetAssetPath(t.filter.sharedMesh),
            material = AssetDatabase.GetAssetPath(t.renderer.sharedMaterial), texture = AssetDatabase.GetAssetPath(t.renderer.sharedMaterial.mainTexture),
            position = Values(t.t.localPosition), rotation = Values(t.t.localEulerAngles), scale = Values(t.t.localScale),
            collider = collider == null ? "none" : JsonUtility.ToJson(new ColliderState { size = Values(collider.size), center = Values(collider.center), enabled = collider.enabled, trigger = collider.isTrigger }) };
    }
    [Serializable] private sealed class ColliderState { public float[] size, center; public bool enabled, trigger; }
    private static float[] Values(Vector3 v) => new[] { v.x, v.y, v.z };
    private static string Sha(string path) { using var sha = SHA256.Create(); return string.Concat(sha.ComputeHash(File.ReadAllBytes(path)).Select(b => b.ToString("x2"))); }
    private static void EnsureFolder(string path) { if (AssetDatabase.IsValidFolder(path)) return; var parent = Path.GetDirectoryName(path).Replace('\\','/'); EnsureFolder(parent); AssetDatabase.CreateFolder(parent, Path.GetFileName(path)); }
}
