using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;

/// <summary>Imports exact crops of one canonical sheet; never resizes or projects its colour pixels.</summary>
public static class NativeSheetImport36
{
    public const string Folder = "Assets/Art/NativeSheet36";
    private const string ManifestPath = "docs/artifacts/building36/slices/manifest.json";
    private const string ReportPath = "docs/artifacts/building36/unity-import.json";

    [Serializable] private sealed class Cell
    {
        public string id, role, output, sha256;
        public int[] canvas_px, visible_alpha_gt_0p1_bbox_in_crop;
    }
    [Serializable] private sealed class Manifest { public string native_sha256; public Cell[] cells; }
    [Serializable] private sealed class DisplayScale
    {
        public string reference_old_png, reference_new_asset;
        public int q;
        public float existing_camera_ppu;
    }
    [Serializable] private sealed class FitProbe { public DisplayScale uniform_display_scale; }
    [Serializable] private sealed class Item
    {
        public string id, asset, sourceHash, importedHash;
        public int width, height, rgbaMismatches;
        public float pixelsPerUnit;
        public bool fullRect, unchangedPng;
    }
    [Serializable] private sealed class Report
    {
        public string canonicalSheetHash;
        public string scope = "Exact sprite asset import only; existing scene and collision geometry are unchanged.";
        public float cameraGridPpu, spritePpu;
        public int displayMultiplier;
        public string multiplierSource;
        public Item[] items;
        public bool exactNativeImports, sceneIntegrated;
    }

    public static void Import()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Edit mode is required.");
        var manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(ManifestPath));
        var fit = JsonUtility.FromJson<FitProbe>(File.ReadAllText("docs/artifacts/building36/source-fit.json"));
        var cells = manifest.cells.Where(c => c.role == "object").ToArray();
        if (cells.Length != 18 || cells.Select(c => c.id).Distinct().Count() != 18)
            throw new InvalidDataException("Expected eighteen distinct canonical crops.");

        // Complete the read-only input check before creating/importing any asset.
        foreach (var cell in cells)
        {
            if (Hash(cell.output) != cell.sha256) throw new InvalidDataException(cell.id + ": source hash changed.");
            string path = Folder + "/" + cell.id + ".png";
            if (File.Exists(path) && Hash(path) != cell.sha256)
                throw new InvalidDataException(cell.id + ": refusing to replace a different existing asset.");
        }
        var reference = cells.Single(c => c.id == fit.uniform_display_scale.reference_new_asset);
        int sourceWidth = reference.visible_alpha_gt_0p1_bbox_in_crop[2] - reference.visible_alpha_gt_0p1_bbox_in_crop[0];
        var prior = AssetDatabase.LoadAssetAtPath<Texture2D>(fit.uniform_display_scale.reference_old_png);
        if (prior == null || !prior.isReadable || sourceWidth <= 0)
            throw new InvalidDataException("The existing reference texture and canonical crop must be readable.");
        int left = prior.width, right = -1;
        var priorPixels = prior.GetPixels32();
        for (int y = 0; y < prior.height; y++) for (int x = 0; x < prior.width; x++)
            if (priorPixels[y * prior.width + x].a >= 26) { left = Math.Min(left, x); right = Math.Max(right, x); }
        if (right < left) throw new InvalidDataException("Reference has no visible texels.");
        int oldWidth = right - left + 1;
        int multiplier = Math.Max(1, Mathf.FloorToInt((float)oldWidth / sourceWidth + .5f));
        if (multiplier != fit.uniform_display_scale.q || fit.uniform_display_scale.existing_camera_ppu <= 0)
            throw new InvalidDataException("Reference dimensions changed since the shared-scale calculation.");
        EnsureFolder(Folder);
        var report = new Report { canonicalSheetHash = manifest.native_sha256,
            cameraGridPpu = fit.uniform_display_scale.existing_camera_ppu,
            displayMultiplier = multiplier,
            spritePpu = fit.uniform_display_scale.existing_camera_ppu / multiplier,
            multiplierSource = "Visible reference width " + oldWidth + " / canonical width " + sourceWidth +
                "; nearest positive integer " + multiplier + " shared by all crops; no PNG resize." };
        var items = new List<Item>();
        foreach (var cell in cells)
        {
            string path = Folder + "/" + cell.id + ".png";
            if (!File.Exists(path)) File.Copy(cell.output, path);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = report.spritePpu;
            importer.filterMode = FilterMode.Point;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.mipmapEnabled = false;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.maxTextureSize = 4096;
            importer.alphaSource = TextureImporterAlphaSource.FromInput;
            importer.alphaIsTransparency = false;
            importer.sRGBTexture = true;
            importer.isReadable = true;
            var settings = new TextureImporterSettings();
            importer.ReadTextureSettings(settings);
            settings.spriteMeshType = SpriteMeshType.FullRect;
            settings.spriteGenerateFallbackPhysicsShape = false;
            // An explicit neutral pivot; no unverified semantic foot point is inferred from a PNG.
            settings.spriteAlignment = (int)SpriteAlignment.Center;
            importer.SetTextureSettings(settings);
            var platform = importer.GetDefaultPlatformTextureSettings();
            platform.format = TextureImporterFormat.RGBA32;
            platform.textureCompression = TextureImporterCompression.Uncompressed;
            importer.SetPlatformTextureSettings(platform);
            importer.SaveAndReimport();

            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            var source = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            try
            {
                if (!ImageConversion.LoadImage(source, File.ReadAllBytes(cell.output)))
                    throw new InvalidDataException(cell.id + ": invalid PNG.");
                if (texture.width != cell.canvas_px[0] || texture.height != cell.canvas_px[1] ||
                    source.width != texture.width || source.height != texture.height)
                    throw new InvalidDataException(cell.id + ": import changed dimensions.");
                var expected = source.GetPixels32();
                var actual = texture.GetPixels32();
                int mismatches = 0;
                for (int n = 0; n < expected.Length; n++)
                    if (!expected[n].Equals(actual[n])) mismatches++;
                var item = new Item { id = cell.id, asset = path, sourceHash = cell.sha256,
                    importedHash = Hash(path), width = texture.width, height = texture.height,
                    rgbaMismatches = mismatches, pixelsPerUnit = sprite.pixelsPerUnit,
                    fullRect = sprite.vertices.Length == 4 };
                item.unchangedPng = item.sourceHash == item.importedHash;
                items.Add(item);
            }
            finally { UnityEngine.Object.DestroyImmediate(source); }
        }
        report.items = items.ToArray();
        report.exactNativeImports = items.All(i => i.unchangedPng && i.rgbaMismatches == 0 && i.fullRect &&
            Mathf.Abs(i.pixelsPerUnit - report.spritePpu) < 0.00001f);
        File.WriteAllText(ReportPath, JsonUtility.ToJson(report, true));
        AssetDatabase.SaveAssets();
        if (!report.exactNativeImports) throw new InvalidDataException("Native colour import invariant failed. See " + ReportPath);
        Debug.Log("B36: 18 unchanged native sprites imported; scene integration has not run.");
    }

    private static string Hash(string path)
    {
        using var sha = SHA256.Create();
        return string.Concat(sha.ComputeHash(File.ReadAllBytes(path)).Select(b => b.ToString("x2")));
    }

    private static void EnsureFolder(string path)
    {
        if (AssetDatabase.IsValidFolder(path)) return;
        string parent = Path.GetDirectoryName(path).Replace('\\', '/');
        EnsureFolder(parent);
        AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
    }
}
