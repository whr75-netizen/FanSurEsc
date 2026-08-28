using System;
using System.Collections.Generic;
using System.IO;
using FantasySurvival.Inventory;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine;

namespace FantasySurvival.EditorTools
{
    public static class PrototypeResourceItemSetup
    {
        private const string DefinitionsFolder = "Assets/GameData/Items/Definitions";
        private const string IconsFolder = "Assets/GameData/Items/Icons";
        private const string ItemDatabasePath = "Assets/GameData/Items/ItemDatabase.asset";
        private const string ShellPrefabPath = "Assets/Prefabs/PersistentGameplayShell.prefab";
        private const int PrototypeMaxStackSize = 10;

        private static readonly ResourceItemSpec[] Specs =
        {
            new ResourceItemSpec(
                7,
                "Medicine",
                "치료제",
                "회복 행동 연결 전의 시험용 치료제입니다.",
                ItemDefinitionKind.Medicine,
                new Color(0.18f, 0.82f, 0.32f, 1f)),
            new ResourceItemSpec(
                8,
                "Ammunition",
                "총알",
                "무기 재장전에 소비되는 시험용 탄약입니다.",
                ItemDefinitionKind.Ammunition,
                new Color(1f, 0.76f, 0.08f, 1f)),
            new ResourceItemSpec(
                9,
                "Food",
                "음식",
                "섭취 행동 연결 전의 시험용 음식입니다.",
                ItemDefinitionKind.Food,
                new Color(0.16f, 0.52f, 1f, 1f))
        };

        [MenuItem("Tools/Fantasy Survival/Inventory/Apply Prototype Resource Items")]
        public static void ApplyAll()
        {
            EnsureEditorReady();
            EnsureFolder(IconsFolder);

            var definitions = new List<ItemDefinition>(Specs.Length);
            foreach (ResourceItemSpec spec in Specs)
            {
                Texture2D icon = WriteAndImportCircleIcon(spec);
                definitions.Add(ConfigureDefinition(spec, icon));
            }

            ConfigureDatabase(definitions);
            InventoryItemPresentationSetup.ApplyPrefabAssets();
            ConfigurePlayerStartingItems();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log(
                "Prototype resource items configured: Medicine ID 7, Ammunition ID 8, " +
                "Food ID 9; 1x1, initial quantity 1, prototype max stack 10.");
        }

        private static Texture2D WriteAndImportCircleIcon(ResourceItemSpec spec)
        {
            const int size = 64;
            const float radius = 25f;
            const float borderThickness = 3f;
            var texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
            var pixels = new Color32[size * size];
            Vector2 center = new Vector2((size - 1) * 0.5f, (size - 1) * 0.5f);
            Color borderColor = Color.Lerp(spec.Color, Color.black, 0.42f);

            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float distance = Vector2.Distance(new Vector2(x, y), center);
                    Color color = Color.clear;
                    if (distance <= radius)
                    {
                        color = distance >= radius - borderThickness
                            ? borderColor
                            : spec.Color;
                    }

                    pixels[y * size + x] = color;
                }
            }

            texture.SetPixels32(pixels);
            texture.Apply(false, false);

            string iconPath = $"{IconsFolder}/{spec.AssetName}.png";
            try
            {
                File.WriteAllBytes(Path.GetFullPath(iconPath), texture.EncodeToPNG());
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(texture);
            }

            AssetDatabase.ImportAsset(
                iconPath,
                ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            if (!(AssetImporter.GetAtPath(iconPath) is TextureImporter importer))
            {
                throw new BuildFailedException($"Could not import prototype icon: {iconPath}");
            }

            importer.textureType = TextureImporterType.Default;
            importer.alphaIsTransparency = true;
            importer.mipmapEnabled = false;
            importer.filterMode = FilterMode.Point;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.SaveAndReimport();

            Texture2D imported = AssetDatabase.LoadAssetAtPath<Texture2D>(iconPath);
            if (imported == null)
            {
                throw new BuildFailedException($"Prototype icon is missing after import: {iconPath}");
            }

            return imported;
        }

        private static ItemDefinition ConfigureDefinition(ResourceItemSpec spec, Texture2D icon)
        {
            string definitionPath = $"{DefinitionsFolder}/{spec.AssetName}.asset";
            ItemDefinition definition = AssetDatabase.LoadAssetAtPath<ItemDefinition>(definitionPath);
            if (definition == null)
            {
                definition = ScriptableObject.CreateInstance<ItemDefinition>();
                definition.name = spec.AssetName;
                AssetDatabase.CreateAsset(definition, definitionPath);
            }

            var serialized = new SerializedObject(definition);
            serialized.FindProperty("id").intValue = spec.Id;
            serialized.FindProperty("displayName").stringValue = spec.DisplayName;
            serialized.FindProperty("description").stringValue = spec.Description;
            serialized.FindProperty("width").intValue = 1;
            serialized.FindProperty("height").intValue = 1;
            serialized.FindProperty("icon").objectReferenceValue = icon;
            serialized.FindProperty("maxStackSize").intValue = PrototypeMaxStackSize;
            serialized.FindProperty("equipmentSlot").enumValueIndex = 0;
            serialized.FindProperty("isTradable").boolValue = false;
            serialized.FindProperty("tradePrice").intValue = 0;
            serialized.FindProperty("kind").enumValueIndex = (int)spec.Kind;
            serialized.FindProperty("containerWidth").intValue = 1;
            serialized.FindProperty("containerHeight").intValue = 1;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(definition);

            if (!definition.TryValidateInventoryShape(out string error) ||
                definition.Id != spec.Id || definition.Width != 1 || definition.Height != 1 ||
                definition.Icon != icon || definition.Kind != spec.Kind ||
                definition.MaxStackSize != PrototypeMaxStackSize)
            {
                throw new BuildFailedException(
                    $"Prototype item definition '{spec.AssetName}' is invalid: {error}");
            }

            return definition;
        }

        private static void ConfigureDatabase(IReadOnlyList<ItemDefinition> definitions)
        {
            ItemDatabase database = AssetDatabase.LoadAssetAtPath<ItemDatabase>(ItemDatabasePath);
            if (database == null)
            {
                throw new BuildFailedException($"ItemDatabase is missing: {ItemDatabasePath}");
            }

            var serialized = new SerializedObject(database);
            SerializedProperty items = serialized.FindProperty("items");
            if (items == null || !items.isArray)
            {
                throw new BuildFailedException("ItemDatabase item list is missing.");
            }

            foreach (ItemDefinition definition in definitions)
            {
                bool found = false;
                for (int index = 0; index < items.arraySize; index++)
                {
                    ItemDefinition existing =
                        items.GetArrayElementAtIndex(index).objectReferenceValue as ItemDefinition;
                    if (existing == definition)
                    {
                        found = true;
                        break;
                    }

                    if (existing != null && existing.Id == definition.Id)
                    {
                        throw new BuildFailedException(
                            $"ItemDatabase already uses definition ID {definition.Id} at '{existing.name}'.");
                    }
                }

                if (!found)
                {
                    int index = items.arraySize;
                    items.arraySize++;
                    items.GetArrayElementAtIndex(index).objectReferenceValue = definition;
                }
            }

            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(database);
        }

        private static void ConfigurePlayerStartingItems()
        {
            GameObject root = PrefabUtility.LoadPrefabContents(ShellPrefabPath);
            if (root == null)
            {
                throw new BuildFailedException($"Could not load prefab: {ShellPrefabPath}");
            }

            try
            {
                InventoryUIManager manager = root.GetComponentInChildren<InventoryUIManager>(true);
                if (manager == null)
                {
                    throw new BuildFailedException(
                        "PersistentGameplayShell has no InventoryUIManager.");
                }

                var serialized = new SerializedObject(manager);
                SerializedProperty startingIds = serialized.FindProperty("startingItemIds");
                if (startingIds == null || !startingIds.isArray)
                {
                    throw new BuildFailedException("Player starting item ID array is missing.");
                }

                foreach (ResourceItemSpec spec in Specs)
                {
                    bool found = false;
                    for (int index = 0; index < startingIds.arraySize; index++)
                    {
                        if (startingIds.GetArrayElementAtIndex(index).intValue == spec.Id)
                        {
                            found = true;
                            break;
                        }
                    }

                    if (!found)
                    {
                        int index = startingIds.arraySize;
                        startingIds.arraySize++;
                        startingIds.GetArrayElementAtIndex(index).intValue = spec.Id;
                    }
                }

                serialized.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(manager);
                PrefabUtility.SaveAsPrefabAsset(root, ShellPrefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        private static void EnsureFolder(string assetFolder)
        {
            if (AssetDatabase.IsValidFolder(assetFolder))
            {
                return;
            }

            string parent = Path.GetDirectoryName(assetFolder)?.Replace('\\', '/');
            string folderName = Path.GetFileName(assetFolder);
            if (string.IsNullOrWhiteSpace(parent) || string.IsNullOrWhiteSpace(folderName) ||
                !AssetDatabase.IsValidFolder(parent))
            {
                throw new BuildFailedException($"Could not create asset folder: {assetFolder}");
            }

            AssetDatabase.CreateFolder(parent, folderName);
        }

        private static void EnsureEditorReady()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode ||
                EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                throw new BuildFailedException(
                    "Prototype resource setup requires an idle Unity Editor in Edit Mode.");
            }
        }

        private readonly struct ResourceItemSpec
        {
            public int Id { get; }
            public string AssetName { get; }
            public string DisplayName { get; }
            public string Description { get; }
            public ItemDefinitionKind Kind { get; }
            public Color Color { get; }

            public ResourceItemSpec(
                int id,
                string assetName,
                string displayName,
                string description,
                ItemDefinitionKind kind,
                Color color)
            {
                Id = id;
                AssetName = assetName;
                DisplayName = displayName;
                Description = description;
                Kind = kind;
                Color = color;
            }
        }
    }
}
