using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using FantasySurvival.WorldGeneration;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

/// <summary>Imports immutable native surface data and binds the existing shop, without resizing source art.</summary>
public static class NativeBuilding16Importer
{
    public const string AssetRoot = "Assets/Art/NativeBuilding38";
    public const string ShaderName = "FantasySurvival/World/Native Palette Surface 16";
    private const string ContractPath = "Tools/Building37/input-contract.json";
    private const string BaselinePath = "docs/artifacts/building38/placement-baseline.json";
    private const string CasterName = "Native16 physical shadow";
    private static readonly Vector3 Right = new Vector3(.707106781f, 0, -.707106781f);
    private static readonly Vector3 Up = new Vector3(.353553391f, .866025404f, .353553391f);
    private static readonly string[] RequiredIds = {
        "empty_counter", "left_shelf", "rear_shelf", "island_body_template", "stock_shelf", "fridge",
        "utility_bench", "cleaning_cabinet", "register", "appletray", "plant", "barrel", "crate",
        "detail_ledger", "detail_clock", "detail_poster", "detail_broom", "detail_bin"
    };

    [Serializable] private sealed class Manifest { public Entry[] assets; }
    [Serializable] private sealed class Entry
    {
        public string id, positionFile, normalFile, materialFile, previewFile, meshFile, bindingPath;
        public int width, height;
        public float ppu;
        public int[] origin;
    }
    [Serializable] private sealed class MeshIndices { public int[] triangles; }
    [Serializable] private sealed class PhysicalContract { public PhysicalAsset[] assets; }
    [Serializable] private sealed class PhysicalAsset { public string id; public float[] size_xyz_m; public Instance[] instances; }
    [Serializable] private sealed class Instance { public string id, support; }
    [Serializable] private sealed class Baseline { public BaselineRow[] rows; }
    [Serializable] private sealed class BaselineRow
    {
        public string path, id, texture, colliderEntity;
        public float[] pos, rot, scale, parentPos, parentRot, colliderCenter, colliderSize;
    }
    [Serializable] private sealed class SourceRecord { public string path, sha256; }
    [Serializable] private sealed class ImportReceipt
    {
        public string sourceFolder, manifestSha256;
        public SourceRecord[] sources;
        public string[] importedIds;
        public int floatMapRgbaMismatches, materialRgbaMismatches;
    }
    [Serializable] private sealed class BindingReport
    {
        public string instance, asset, rendererEntity, mesh, material, shadowMesh;
        public float oldY, newY, visualY;
    }
    [Serializable] private sealed class ApplyReport
    {
        public string scene, building, sourceFolder;
        public int objectBindings, structuralBindings;
        public BindingReport[] bindings;
    }
    private sealed class Prepared
    {
        public Entry entry;
        public byte[] position, normal, material;
        public Vector3[] vertices;
        public int[] triangles;
    }
    private sealed class Binding
    {
        public Entry entry;
        public Transform parent, visual;
        public MeshFilter filter;
        public MeshRenderer renderer;
        public Mesh display, caster;
        public Material material;
        public float newParentY, newVisualY;
        public bool structural;
    }

    /// <summary>Creates or verifies shared Editor assets. This does not bind, instantiate or save a scene.</summary>
    public static string Import(string folderAbsolute)
    {
        RequireEditMode();
        if (!BitConverter.IsLittleEndian) throw new PlatformNotSupportedException("N16 float32 input is little endian.");
        string folder = Path.GetFullPath(folderAbsolute);
        string manifestPath = SourcePath(folder, "manifest.json");
        var manifest = Read<Manifest>(manifestPath);
        ValidateManifest(manifest);
        var sources = new List<SourceRecord>();
        SourceRecord Record(string path)
        {
            var record = new SourceRecord { path = path, sha256 = Sha(path) }; sources.Add(record); return record;
        }
        Record(manifestPath);
        string palettePath = SourcePath(folder, "palette.png"); Record(palettePath);
        using var palette = new TemporaryImage(File.ReadAllBytes(palettePath), false);
        if (palette.texture.width != 4 || palette.texture.height != 10)
            throw new InvalidDataException("Palette must be exactly four tone columns and ten material rows.");
        var prepared = new List<Prepared>();
        foreach (var entry in manifest.assets)
        {
            string positionPath = SourcePath(folder, entry.positionFile), normalPath = SourcePath(folder, entry.normalFile);
            string materialPath = SourcePath(folder, entry.materialFile), meshPath = SourcePath(folder, entry.meshFile);
            foreach (string path in new[] { positionPath, normalPath, materialPath, meshPath }) Record(path);
            if (!string.IsNullOrEmpty(entry.previewFile)) Record(SourcePath(folder, entry.previewFile));
            byte[] positions = ReadFloatRows(positionPath, entry.width, entry.height);
            byte[] normals = ReadFloatRows(normalPath, entry.width, entry.height);
            byte[] materialBytes = File.ReadAllBytes(materialPath);
            using var material = new TemporaryImage(materialBytes, true);
            if (material.texture.width != entry.width || material.texture.height != entry.height)
                throw new InvalidDataException("Material data domain mismatch: " + entry.id);
            ReadMesh(meshPath, out var vertices, out var triangles);
            prepared.Add(new Prepared { entry = entry, position = positions, normal = normals,
                material = materialBytes, vertices = vertices, triangles = triangles });
        }
        string receiptPath = AssetRoot + "/import-receipt.json";
        if (File.Exists(receiptPath))
        {
            var previous = Read<ImportReceipt>(receiptPath);
            if (previous.manifestSha256 != Sha(manifestPath) || previous.sources == null ||
                !previous.sources.Select(s => s.path + ":" + s.sha256).SequenceEqual(sources.Select(s => s.path + ":" + s.sha256)))
                throw new InvalidDataException("Existing N16 assets belong to different source data; preserve them rather than overwrite.");
        }
        Shader shader = Shader.Find(ShaderName);
        if (shader == null) throw new InvalidOperationException("N16 runtime shader is not compiled: " + ShaderName);
        foreach (string property in new[] { "_PositionMap", "_NormalMap", "_MaterialMap", "_PaletteMap", "_NativeGridAnchorOS", "_NativeGridTexelUOS", "_NativeGridTexelVOS" })
        {
            var check = new Material(shader);
            try { if (!check.HasProperty(property)) throw new InvalidDataException("N16 shader contract missing " + property); }
            finally { Object.DestroyImmediate(check); }
        }
        EnsureFolder(AssetRoot);
        Texture2D paletteAsset = ImportPng(palettePath, AssetRoot + "/palette.png", false);
        var shadowMaterial = CreateShadowMaterial();
        foreach (var p in prepared)
        {
            var entry = p.entry;
            string target = AssetRoot + "/" + entry.id;
            EnsureFolder(target);
            Texture2D position = CreateFloatMap(target + "/position.asset", entry, p.position);
            Texture2D normal = CreateFloatMap(target + "/normal.asset", entry, p.normal);
            Texture2D material = ImportPng(SourcePath(folder, entry.materialFile), target + "/material.png", true);
            Mesh display = CreateDisplayMesh(target + "/display.asset", entry);
            CreateCasterMesh(target + "/shadow.asset", entry.id, p.vertices, p.triangles);
            string materialAssetPath = target + "/surface.mat";
            var surface = AssetDatabase.LoadAssetAtPath<Material>(materialAssetPath);
            if (surface == null)
            {
                surface = new Material(shader) { name = "Native16 " + entry.id };
                surface.SetTexture("_PositionMap", position); surface.SetTexture("_NormalMap", normal);
                surface.SetTexture("_MaterialMap", material); surface.SetTexture("_PaletteMap", paletteAsset);
                surface.SetFloat("_NativeGridEnabled", 1);
                // UV zero is the bottom left; source files themselves are top-down.
                surface.SetVector("_NativeGridAnchorOS", display.vertices[0]);
                surface.SetVector("_NativeGridTexelUOS", Right / entry.ppu);
                surface.SetVector("_NativeGridTexelVOS", Up / entry.ppu);
                if (surface.HasProperty("_BaseColor")) surface.SetColor("_BaseColor", Color.white);
                AssetDatabase.CreateAsset(surface, materialAssetPath);
            }
            else if (surface.shader != shader || surface.GetTexture("_PositionMap") != position ||
                surface.GetTexture("_NormalMap") != normal || surface.GetTexture("_MaterialMap") != material ||
                surface.GetTexture("_PaletteMap") != paletteAsset)
                throw new InvalidDataException("Existing N16 surface material differs: " + entry.id);
        }
        CopyUnchanged(manifestPath, AssetRoot + "/manifest.json");
        var receipt = new ImportReceipt { sourceFolder = folder, manifestSha256 = Sha(manifestPath),
            sources = sources.ToArray(), importedIds = manifest.assets.Select(a => a.id).ToArray(),
            floatMapRgbaMismatches = 0, materialRgbaMismatches = 0 };
        if (!File.Exists(receiptPath))
        {
            File.WriteAllText(receiptPath, JsonUtility.ToJson(receipt, true));
            AssetDatabase.ImportAsset(receiptPath, ImportAssetOptions.ForceSynchronousImport);
        }
        AssetDatabase.SaveAssets();
        string report = JsonUtility.ToJson(receipt, true);
        Debug.Log("N16 imported immutable native domains, observed mismatches 0; no scene objects changed. " + prepared.Count + " shared assets.");
        return report;
    }

    /// <summary>Connects existing renderers after root's minimum lighting experiment, preserving their identities and colliders.</summary>
    public static string Apply(GameObject building)
    {
        RequireEditMode();
        if (building == null || building.name != "PlannedPixelShop33" || building.GetComponent<NativePixelBuilding>() == null)
            throw new InvalidOperationException("The preserved PlannedPixelShop33 scene instance is required.");
        if (building.transform.lossyScale != Vector3.one || Mathf.Abs(Mathf.DeltaAngle(building.transform.eulerAngles.y, 305)) > .01f)
            throw new InvalidDataException("Preserved unit building scale and 305 degree root yaw required.");
        var manifest = Read<Manifest>(AssetRoot + "/manifest.json"); ValidateManifest(manifest);
        var imported = Read<ImportReceipt>(AssetRoot + "/import-receipt.json");
        foreach (var source in imported.sources)
            if (Sha(source.path) != source.sha256) throw new InvalidDataException("N16 calculation input changed: " + source.path);
        var entries = manifest.assets.ToDictionary(a => a.id);
        var contract = Read<PhysicalContract>(ContractPath);
        var baseline = Read<Baseline>(BaselinePath).rows.ToDictionary(r => r.path);
        var content = building.transform.Find(PixelShopInteriorCompletion.ContentName);
        if (content == null) throw new InvalidDataException("Existing shop content root is missing.");
        var parentByInstance = new Dictionary<string, Transform>();
        foreach (string groupName in new[] { PixelShopProjection35.GroupName, PixelShopProjection35.DetailsGroupName })
        {
            Transform group = content.Find(groupName);
            if (group == null) throw new InvalidDataException("Existing placement group missing: " + groupName);
            foreach (Transform child in group) parentByInstance.Add(child.name, child);
        }
        if (parentByInstance.Count != 26) throw new InvalidDataException("Exactly 26 existing placement instances are required.");
        var physicalByInstance = contract.assets.SelectMany(a => a.instances.Select(i => (asset: a, instance: i))).ToDictionary(pair => pair.instance.id);
        if (physicalByInstance.Count != 26 || !physicalByInstance.Keys.All(parentByInstance.ContainsKey))
            throw new InvalidDataException("Physical placement contract and existing instance identities differ.");
        var targetY = new Dictionary<string, float>();
        float BaseY(string id, HashSet<string> stack)
        {
            if (targetY.TryGetValue(id, out float cached)) return cached;
            if (!stack.Add(id)) throw new InvalidDataException("Cyclic physical support: " + id);
            var pair = physicalByInstance[id];
            float y = parentByInstance[id].localPosition.y;
            if (parentByInstance.TryGetValue(pair.instance.support ?? "", out var support))
            {
                var supportPhysical = physicalByInstance[pair.instance.support].asset;
                y = BaseY(pair.instance.support, stack) + supportPhysical.size_xyz_m[1];
            }
            stack.Remove(id); targetY.Add(id, y); return y;
        }
        var bindings = new List<Binding>();
        foreach (var pair in physicalByInstance.Values)
        {
            if (!entries.TryGetValue(pair.asset.id, out var entry)) throw new InvalidDataException("Missing native template: " + pair.asset.id);
            var parent = parentByInstance[pair.instance.id];
            var visual = parent.Find("Native surface");
            var binding = PrepareBinding(building, baseline, entry, parent, visual, false);
            binding.newParentY = BaseY(pair.instance.id, new HashSet<string>());
            // Existing wall clock/poster parent anchors are their vertical centres, whereas native geometry starts at its base.
            binding.newVisualY = pair.asset.id == "detail_clock" || pair.asset.id == "detail_poster" ? -pair.asset.size_xyz_m[1] * .5f : 0;
            bindings.Add(binding);
        }
        foreach (var entry in manifest.assets.Where(a => !RequiredIds.Contains(a.id)))
        {
            if (string.IsNullOrEmpty(entry.bindingPath)) throw new InvalidDataException("Structural template requires explicit original renderer bindingPath: " + entry.id);
            if (entry.bindingPath.Contains("/Floor/")) throw new InvalidDataException("The accepted floor is preserved, not replaced by N16.");
            var visual = building.transform.Find(entry.bindingPath);
            if (visual == null) throw new InvalidDataException("Explicit structural renderer does not exist: " + entry.bindingPath);
            bindings.Add(PrepareBinding(building, baseline, entry, visual.parent, visual, true));
        }
        var shadowMaterial = AssetDatabase.LoadAssetAtPath<Material>(AssetRoot + "/physical-shadow.mat");
        if (shadowMaterial == null) throw new InvalidDataException("Imported physical shadow material missing.");
        var reports = new List<BindingReport>();
        foreach (var binding in bindings)
        {
            float oldY = binding.parent.localPosition.y;
            var report = new BindingReport { instance = binding.parent.name, asset = binding.entry.id,
                rendererEntity = binding.renderer.GetEntityId().ToString(), oldY = oldY,
                newY = binding.newParentY, visualY = binding.newVisualY,
                mesh = AssetDatabase.GetAssetPath(binding.display), material = AssetDatabase.GetAssetPath(binding.material),
                shadowMesh = AssetDatabase.GetAssetPath(binding.caster) };
            Undo.RecordObjects(new Object[] { binding.parent, binding.visual, binding.filter, binding.renderer }, "Bind N16 native surface");
            var p = binding.parent.localPosition; p.y = binding.newParentY; binding.parent.localPosition = p;
            binding.visual.localPosition = Vector3.up * binding.newVisualY;
            Material prior = binding.renderer.sharedMaterial;
            PreserveOcclusionProperties(prior, binding.material);
            binding.filter.sharedMesh = binding.display;
            binding.renderer.sharedMaterial = binding.material;
            // Screen cards never cast a card-shaped shadow; actual closed geometry below owns the caster.
            binding.renderer.shadowCastingMode = ShadowCastingMode.Off;
            Transform caster = binding.visual.Find(CasterName);
            bool created = caster == null;
            if (created)
            {
                var go = new GameObject(CasterName); Undo.RegisterCreatedObjectUndo(go, "Add actual N16 shadow geometry");
                caster = go.transform; caster.SetParent(binding.visual, false);
                go.AddComponent<MeshFilter>(); go.AddComponent<MeshRenderer>();
            }
            caster.gameObject.layer = binding.renderer.gameObject.layer;
            var casterFilter = caster.GetComponent<MeshFilter>(); var casterRenderer = caster.GetComponent<MeshRenderer>();
            Undo.RecordObjects(new Object[] { casterFilter, casterRenderer }, "Bind N16 physical caster");
            casterFilter.sharedMesh = binding.caster; casterRenderer.sharedMaterial = shadowMaterial;
            casterRenderer.shadowCastingMode = ShadowCastingMode.ShadowsOnly; casterRenderer.receiveShadows = false;
            casterRenderer.renderingLayerMask = binding.renderer.renderingLayerMask;
            caster.localPosition = Vector3.zero; caster.localRotation = Quaternion.identity; caster.localScale = Vector3.one;
            foreach (var changed in new Object[] { binding.parent, binding.visual, binding.filter, binding.renderer, casterFilter, casterRenderer })
                PrefabUtility.RecordPrefabInstancePropertyModifications(changed);
            reports.Add(report);
        }
        AssetDatabase.SaveAssets();
        EditorSceneManager.MarkSceneDirty(building.scene);
        var result = new ApplyReport { scene = building.scene.path, building = building.name, sourceFolder = imported.sourceFolder,
            objectBindings = bindings.Count(b => !b.structural), structuralBindings = bindings.Count(b => b.structural), bindings = reports.ToArray() };
        Debug.Log("N16 bound " + result.objectBindings + " existing objects and " + result.structuralBindings + " original structural renderers. Scene/prefab saving remains with the calling writer.");
        return JsonUtility.ToJson(result, true);
    }

    private static Binding PrepareBinding(GameObject building, Dictionary<string, BaselineRow> baseline, Entry entry,
        Transform parent, Transform visual, bool structural)
    {
        if (visual == null || parent == null) throw new InvalidDataException("Native renderer missing: " + entry.id);
        var filter = visual.GetComponent<MeshFilter>(); var renderer = visual.GetComponent<MeshRenderer>();
        if (filter == null || renderer == null) throw new InvalidDataException("Original native surface is not a MeshRenderer: " + entry.id);
        if (visual.localRotation != Quaternion.identity || visual.localScale != Vector3.one || parent.localRotation != Quaternion.identity)
            throw new InvalidDataException("Noncanonical existing native transform: " + entry.id);
        string path = AnimationUtility.CalculateTransformPath(visual, building.transform);
        if (!baseline.TryGetValue(path, out var original)) throw new InvalidDataException("Renderer is outside the observed original baseline: " + path);
        if (visual.GetEntityId().ToString() != original.id)
            throw new InvalidDataException("Original native renderer identity changed: " + path);
        var collider = parent.GetComponent<BoxCollider>();
        if (!string.IsNullOrEmpty(original.colliderEntity) && (collider == null || collider.GetEntityId().ToString() != original.colliderEntity ||
            !Near(collider.center, Values(original.colliderCenter)) || !Near(collider.size, Values(original.colliderSize))))
            throw new InvalidDataException("Preserved physical collider changed: " + path);
        if (visual.localPosition != Vector3.zero)
            throw new InvalidDataException("Native binding has a pre-existing visual offset; calculate its cause before replacing: " + path);
        string assetPath = AssetRoot + "/" + entry.id;
        var display = AssetDatabase.LoadAssetAtPath<Mesh>(assetPath + "/display.asset");
        var caster = AssetDatabase.LoadAssetAtPath<Mesh>(assetPath + "/shadow.asset");
        var material = AssetDatabase.LoadAssetAtPath<Material>(assetPath + "/surface.mat");
        if (display == null || caster == null || material == null) throw new InvalidDataException("Imported shared native asset missing: " + entry.id);
        return new Binding { entry = entry, parent = parent, visual = visual, filter = filter, renderer = renderer,
            display = display, caster = caster, material = material, structural = structural,
            newParentY = parent.localPosition.y, newVisualY = 0 };
    }

    private static void PreserveOcclusionProperties(Material prior, Material next)
    {
        if (prior == null) return;
        foreach (string name in new[] { "_ZWrite", "_SrcBlend", "_DstBlend" })
            if (prior.HasProperty(name) && next.HasProperty(name)) next.SetFloat(name, prior.GetFloat(name));
        if (prior.HasProperty("_BaseColor") && next.HasProperty("_BaseColor")) next.SetColor("_BaseColor", prior.GetColor("_BaseColor"));
        next.renderQueue = prior.renderQueue;
        EditorUtility.SetDirty(next);
    }

    private static Mesh CreateDisplayMesh(string path, Entry entry)
    {
        Vector3 Point(float u, float v) => (Right * (entry.origin[0] + u) - Up * (entry.origin[1] + v)) / entry.ppu;
        var vertices = new[] { Point(0, entry.height), Point(entry.width, entry.height), Point(entry.width, 0), Point(0, 0) };
        var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if (mesh != null)
        {
            if (!mesh.vertices.SequenceEqual(vertices)) throw new InvalidDataException("Existing native display domain differs: " + entry.id);
            return mesh;
        }
        mesh = new Mesh { name = "N16 display " + entry.id, vertices = vertices, triangles = new[] { 0, 1, 2, 0, 2, 3 },
            uv = new[] { Vector2.zero, Vector2.right, Vector2.one, Vector2.up } };
        mesh.RecalculateNormals(); mesh.RecalculateBounds(); AssetDatabase.CreateAsset(mesh, path); return mesh;
    }
    private static Mesh CreateCasterMesh(string path, string id, Vector3[] vertices, int[] triangles)
    {
        var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if (mesh != null)
        {
            if (!mesh.vertices.SequenceEqual(vertices) || !mesh.triangles.SequenceEqual(triangles))
                throw new InvalidDataException("Existing physical caster differs: " + id);
            return mesh;
        }
        mesh = new Mesh { name = "N16 actual geometry " + id, indexFormat = vertices.Length > 65535 ? IndexFormat.UInt32 : IndexFormat.UInt16 };
        mesh.vertices = vertices; mesh.triangles = triangles; mesh.RecalculateNormals(); mesh.RecalculateBounds();
        AssetDatabase.CreateAsset(mesh, path); return mesh;
    }
    private static Texture2D CreateFloatMap(string path, Entry entry, byte[] rgba)
    {
        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        if (texture != null)
        {
            if (texture.width != entry.width || texture.height != entry.height || texture.format != TextureFormat.RGBAFloat ||
                texture.filterMode != FilterMode.Point || texture.wrapMode != TextureWrapMode.Clamp || texture.mipmapCount != 1 ||
                !texture.GetRawTextureData<byte>().ToArray().SequenceEqual(rgba))
                throw new InvalidDataException("Existing float32 native data differs: " + path);
            return texture;
        }
        texture = new Texture2D(entry.width, entry.height, TextureFormat.RGBAFloat, false, true) {
            name = Path.GetFileNameWithoutExtension(path) + " " + entry.id, filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, anisoLevel = 0 };
        texture.LoadRawTextureData(rgba); texture.Apply(false, false); AssetDatabase.CreateAsset(texture, path);
        if (!texture.GetRawTextureData<byte>().ToArray().SequenceEqual(rgba)) throw new InvalidDataException("RGBAFloat data changed during asset creation.");
        return texture;
    }
    private static Texture2D ImportPng(string source, string destination, bool linear)
    {
        CopyUnchanged(source, destination);
        var importer = (TextureImporter)AssetImporter.GetAtPath(destination);
        if (importer == null) throw new InvalidDataException("PNG importer unavailable: " + destination);
        bool changed = importer.textureType != TextureImporterType.Default || importer.sRGBTexture == linear ||
            importer.filterMode != FilterMode.Point || importer.mipmapEnabled || importer.isReadable == false ||
            importer.textureCompression != TextureImporterCompression.Uncompressed || importer.npotScale != TextureImporterNPOTScale.None ||
            importer.alphaIsTransparency || importer.wrapMode != TextureWrapMode.Clamp;
        if (changed)
        {
            importer.textureType = TextureImporterType.Default; importer.sRGBTexture = !linear;
            importer.filterMode = FilterMode.Point; importer.wrapMode = TextureWrapMode.Clamp;
            importer.mipmapEnabled = false; importer.isReadable = true; importer.alphaIsTransparency = false;
            importer.textureCompression = TextureImporterCompression.Uncompressed; importer.npotScale = TextureImporterNPOTScale.None;
            importer.alphaSource = TextureImporterAlphaSource.FromInput; importer.maxTextureSize = 8192; importer.anisoLevel = 0;
            var platform = importer.GetDefaultPlatformTextureSettings(); platform.format = TextureImporterFormat.RGBA32;
            platform.textureCompression = TextureImporterCompression.Uncompressed; importer.SetPlatformTextureSettings(platform);
            importer.SaveAndReimport();
        }
        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(destination);
        using var original = new TemporaryImage(File.ReadAllBytes(source), linear);
        if (texture == null || texture.width != original.texture.width || texture.height != original.texture.height ||
            !texture.GetPixels32().SequenceEqual(original.texture.GetPixels32()))
            throw new InvalidDataException("PNG native domain/RGBA changed on import: " + destination);
        return texture;
    }
    private static Material CreateShadowMaterial()
    {
        string path = AssetRoot + "/physical-shadow.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material != null) return material;
        Shader shader = Shader.Find("Universal Render Pipeline/Lit");
        if (shader == null) throw new InvalidOperationException("Existing URP Lit shadow pass unavailable.");
        material = new Material(shader) { name = "N16 closed physical shadow" };
        material.SetFloat("_Cull", (float)CullMode.Off);
        material.SetFloat("_Surface", 0); material.SetFloat("_AlphaClip", 0);
        material.SetColor("_BaseColor", Color.white);
        AssetDatabase.CreateAsset(material, path); return material;
    }
    private static byte[] ReadFloatRows(string path, int width, int height)
    {
        byte[] source = File.ReadAllBytes(path);
        int stride = checked(width * 4 * sizeof(float)), length = checked(stride * height);
        if (source.Length != length) throw new InvalidDataException("Float32 native map byte count mismatch: " + path);
        var flipped = new byte[length];
        for (int row = 0; row < height; row++) Buffer.BlockCopy(source, row * stride, flipped, (height - 1 - row) * stride, stride);
        for (int offset = 0; offset < length; offset += sizeof(float))
        {
            float value = BitConverter.ToSingle(flipped, offset);
            if (float.IsNaN(value) || float.IsInfinity(value)) throw new InvalidDataException("Nonfinite native float map: " + path);
        }
        return flipped;
    }
    private static void ReadMesh(string path, out Vector3[] vertices, out int[] triangles)
    {
        string json = File.ReadAllText(path);
        var field = Regex.Match(json, "\\\"vertices\\\"\\s*:\\s*\\[((?:\\s*,?\\s*\\[[^\\[\\]]*\\])*)\\s*\\]", RegexOptions.Singleline);
        if (!field.Success) throw new InvalidDataException("Mesh requires JSON vertices as XYZ triplets: " + path);
        var values = new List<Vector3>();
        foreach (Match triplet in Regex.Matches(field.Groups[1].Value, "\\[([^\\[\\]]*)\\]"))
        {
            string[] components = triplet.Groups[1].Value.Split(',');
            if (components.Length != 3) throw new InvalidDataException("Mesh vertex is not an XYZ triplet: " + path);
            var xyz = components.Select(s => float.Parse(s, NumberStyles.Float, CultureInfo.InvariantCulture)).ToArray();
            if (xyz.Any(v => float.IsNaN(v) || float.IsInfinity(v))) throw new InvalidDataException("Nonfinite mesh coordinate: " + path);
            values.Add(new Vector3(xyz[0], xyz[1], xyz[2]));
        }
        vertices = values.ToArray(); triangles = JsonUtility.FromJson<MeshIndices>(json)?.triangles;
        if (vertices.Length < 3 || triangles == null || triangles.Length == 0 || triangles.Length % 3 != 0 ||
            triangles.Any(i => i < 0 || i >= values.Count)) throw new InvalidDataException("Invalid physical triangle mesh: " + path);
    }
    private sealed class TemporaryImage : IDisposable
    {
        public readonly Texture2D texture;
        public TemporaryImage(byte[] png, bool linear)
        {
            texture = new Texture2D(2, 2, TextureFormat.RGBA32, false, linear);
            if (!ImageConversion.LoadImage(texture, png)) { Object.DestroyImmediate(texture); throw new InvalidDataException("Invalid PNG input."); }
        }
        public void Dispose() => Object.DestroyImmediate(texture);
    }
    private static void ValidateManifest(Manifest manifest)
    {
        if (manifest?.assets == null || manifest.assets.Length < RequiredIds.Length ||
            manifest.assets.Select(e => e.id).Distinct().Count() != manifest.assets.Length ||
            !RequiredIds.All(id => manifest.assets.Any(e => e.id == id)))
            throw new InvalidDataException("Native manifest must contain all eighteen distinct declared object templates.");
        foreach (var entry in manifest.assets)
            if (string.IsNullOrEmpty(entry.id) || !Regex.IsMatch(entry.id, "^[a-zA-Z0-9_-]+$") || entry.width < 1 || entry.height < 1 ||
                entry.origin == null || entry.origin.Length != 2 || float.IsNaN(entry.ppu) || float.IsInfinity(entry.ppu) ||
                Mathf.Abs(entry.ppu - 31.75f) > .0001f)
                throw new InvalidDataException("Invalid native integer-domain manifest entry: " + entry.id);
    }
    private static string SourcePath(string folder, string relative)
    {
        if (string.IsNullOrWhiteSpace(relative) || Path.IsPathRooted(relative)) throw new InvalidDataException("Relative production source path required.");
        string path = Path.GetFullPath(Path.Combine(folder, relative));
        if (!path.StartsWith(folder.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) || !File.Exists(path))
            throw new InvalidDataException("Missing source file or path outside the fixed production folder: " + relative);
        return path;
    }
    private static void CopyUnchanged(string source, string target)
    {
        if (File.Exists(target))
        {
            if (Sha(source) != Sha(target)) throw new InvalidDataException("Preserve conflicting existing source asset: " + target);
            return;
        }
        File.Copy(source, target, false); AssetDatabase.ImportAsset(target, ImportAssetOptions.ForceSynchronousImport);
    }
    private static T Read<T>(string path) => JsonUtility.FromJson<T>(File.ReadAllText(path));
    private static Vector3 Values(float[] xyz) => xyz != null && xyz.Length == 3 ? new Vector3(xyz[0], xyz[1], xyz[2]) : throw new InvalidDataException("Expected XYZ triple.");
    private static bool Near(Vector3 a, Vector3 b) => (a - b).sqrMagnitude <= 1e-10f;
    private static string Sha(string path)
    {
        using var hash = SHA256.Create(); return string.Concat(hash.ComputeHash(File.ReadAllBytes(path)).Select(b => b.ToString("x2")));
    }
    private static void RequireEditMode()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode) throw new InvalidOperationException("Edit Mode required for native import and persistent binding.");
    }
    private static void EnsureFolder(string path)
    {
        if (AssetDatabase.IsValidFolder(path)) return;
        string parent = Path.GetDirectoryName(path)?.Replace('\\', '/');
        if (string.IsNullOrEmpty(parent)) throw new InvalidDataException("Unity asset folder must remain under Assets.");
        EnsureFolder(parent); AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
    }
}
