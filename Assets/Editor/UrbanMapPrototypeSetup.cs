using System;
using System.Collections.Generic;
using FantasySurvival.Combat;
using FantasySurvival.Interaction;
using FantasySurvival.Inventory;
using FantasySurvival.Raids;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using Unity.AI.Navigation;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.SceneManagement;

namespace FantasySurvival.EditorTools
{
    public static class UrbanMapPrototypeSetup
    {
        private const string GameMapTestPath = "Assets/Scenes/GameMapTest.unity";
        private const string GeneratorObjectName = "ProceduralUrbanMap";
        private const string ItemDatabasePath = "Assets/GameData/Items/ItemDatabase.asset";
        private const string SourceMeleeDefinitionPath =
            "Assets/GameData/Enemies/Definitions/KenneyZombie.asset";
        private const string TestMeleeDefinitionPath =
            "Assets/GameData/Enemies/Definitions/PrototypeMeleeDamageOne.asset";
        private const string RaidChestLootPath =
            "Assets/GameData/LootTables/PrototypeMedicalPoiLoot.asset";
        private const string MeleeCorpseLootPath =
            "Assets/GameData/LootTables/PrototypeMeleeCorpseLoot.asset";
        private const string RaidSpawnCatalogPath =
            "Assets/GameData/Raids/PrototypeUrbanRaidSpawnCatalog.asset";
        private const string RaidChestPrefabPath =
            "Assets/Prefabs/Raids/PrototypeMedicalPoiChest.prefab";
        private const string MeleeEnemyPrefabPath =
            "Assets/Prefabs/Raids/PrototypeMeleeEnemyDamageOne.prefab";
        private const string RangedEnemyPrefabPath =
            "Assets/Prefabs/Raids/PrototypeRangedEnemyTimed.prefab";
        private const string RaidChestObjectName = "Stage3_TestLootChest";
        private const string MeleeEnemyObjectName = "Test_KenneyZombiePatrol";
        private const string RangedEnemyObjectName = "Test_PrototypeRangedEnemy";
        private const string LayoutProtectionRootName = "UrbanLayoutProtectionAnchors";
        private const string MeleeProtectionAnchorName = "FormerMeleeFixture";
        private const string RangedProtectionAnchorName = "FormerRangedFixture";
        private const string RaidChestStableId = "core:gamemaptest/test_loot_chest";
        private const string MeleeEnemyStableId = "core:gamemaptest/melee_enemy_01";
        private const string RangedEnemyStableId = "core:gamemaptest/ranged_enemy_01";
        private const float PrototypeLootSearchDurationSeconds = 1f;

        [MenuItem("Tools/Fantasy Survival/Urban Map/Configure GameMapTest")]
        public static void ConfigureGameMapTest()
        {
            EnsureOpenScenesAreClean();
            SceneSetup[] previousSetup = EditorSceneManager.GetSceneManagerSetup();

            try
            {
                Scene scene = EditorSceneManager.OpenScene(GameMapTestPath, OpenSceneMode.Single);
                ConfigureLoadedGameMapTest(scene);
            }
            finally
            {
                if (previousSetup.Length > 0)
                {
                    EditorSceneManager.RestoreSceneManagerSetup(previousSetup);
                }
            }
        }

        public static void ConfigureLoadedGameMapTest(Scene scene)
        {
            if (!scene.IsValid() || !scene.isLoaded ||
                !string.Equals(scene.path, GameMapTestPath, StringComparison.Ordinal))
            {
                throw new BuildFailedException(
                    $"Expected a loaded '{GameMapTestPath}' scene for configuration.");
            }

            ItemDatabase itemDatabase = LoadRequiredAsset<ItemDatabase>(ItemDatabasePath);
            LootTableDefinition raidChestLoot = CreateOrUpdateLootTable(
                RaidChestLootPath,
                new LootEntrySetup(7, 100f));
            LootTableDefinition meleeCorpseLoot = CreateOrUpdateLootTable(
                MeleeCorpseLootPath,
                new LootEntrySetup(1, 100f));
            EnemyDefinition testMeleeDefinition = CreateOrUpdateTestMeleeDefinition();
            ValidateLootTables(itemDatabase, raidChestLoot, meleeCorpseLoot);
            ConfigurePreparedRaidPrefabs(
                raidChestLoot,
                meleeCorpseLoot,
                testMeleeDefinition);
            RaidSpawnCatalogDefinition spawnCatalog = CreateOrUpdateRaidSpawnCatalog();

            SceneSpawnPoint raidEntry = FindComponentInScene<SceneSpawnPoint>(
                scene,
                point => point.SpawnId == "RaidEntry");
            ReturnPortalInteractable portal = FindComponentInScene<ReturnPortalInteractable>(
                scene,
                _ => true);
            GameObject legacyGround = FindRootByName(scene, "Plane");
            if (raidEntry == null || portal == null || legacyGround == null)
            {
                throw new BuildFailedException(
                    "GameMapTest is missing RaidEntry, ReturnPortal, or the legacy Plane " +
                    "required by the urban map prototype setup.");
            }

            EnemyAIController legacyMelee = FindEnemyByName(scene, MeleeEnemyObjectName);
            EnemyAIController legacyRanged = FindEnemyByName(scene, RangedEnemyObjectName);
            Chest legacyChest = FindStandaloneChest(scene, RaidChestObjectName);
            IReadOnlyList<Transform> layoutProtectionAnchors =
                EnsureLayoutProtectionAnchors(scene, legacyMelee, legacyRanged);

            GameObject generatorObject = FindRootByName(scene, GeneratorObjectName);
            if (generatorObject == null)
            {
                generatorObject = new GameObject(GeneratorObjectName);
                Undo.RegisterCreatedObjectUndo(generatorObject, "Create Procedural Urban Map");
                SceneManager.MoveGameObjectToScene(generatorObject, scene);
            }

            ProceduralUrbanMapGenerator generator =
                generatorObject.GetComponent<ProceduralUrbanMapGenerator>();
            if (generator == null)
            {
                generator = Undo.AddComponent<ProceduralUrbanMapGenerator>(generatorObject);
            }

            NavMeshSurface surface = generatorObject.GetComponent<NavMeshSurface>();
            if (surface == null)
            {
                surface = Undo.AddComponent<NavMeshSurface>(generatorObject);
            }

            Undo.RecordObject(surface, "Configure Procedural Urban NavMesh");
            surface.collectObjects = CollectObjects.Children;
            surface.useGeometry = NavMeshCollectGeometry.PhysicsColliders;
            surface.layerMask = ~0;
            surface.ignoreNavMeshAgent = true;
            surface.ignoreNavMeshObstacle = true;
            surface.minRegionArea = 1f;
            surface.buildHeightMesh = false;

            Undo.RecordObject(generator, "Configure Procedural Urban Map");
            var serializedGenerator = new SerializedObject(generator);
            serializedGenerator.FindProperty("entryAnchor").objectReferenceValue =
                raidEntry.transform;
            serializedGenerator.FindProperty("returnPortal").objectReferenceValue =
                portal.transform;
            serializedGenerator.FindProperty("legacyGround").objectReferenceValue =
                legacyGround;
            serializedGenerator.FindProperty("navMeshSurface").objectReferenceValue = surface;
            serializedGenerator.FindProperty("randomizeSeedOnAwake").boolValue = true;
            ReplacePrototypeProtectedAnchors(
                serializedGenerator.FindProperty("additionalProtectedAnchors"),
                legacyMelee,
                legacyRanged,
                layoutProtectionAnchors);
            serializedGenerator.ApplyModifiedPropertiesWithoutUndo();

            RaidCheckpointSceneBinding binding =
                FindComponentInScene<RaidCheckpointSceneBinding>(scene, _ => true);
            if (binding == null)
            {
                throw new BuildFailedException(
                    "GameMapTest is missing its RaidCheckpointSceneBinding.");
            }

            ConfigureRaidSceneBinding(binding, generator, spawnCatalog);
            RemoveLegacySpawnFixtures(legacyChest, legacyMelee, legacyRanged);
            EditorUtility.SetDirty(generatorObject);
            EditorSceneManager.MarkSceneDirty(scene);

            ValidateConfiguredScene(
                scene,
                raidChestLoot,
                meleeCorpseLoot,
                testMeleeDefinition,
                spawnCatalog);
            ValidateLayoutSeeds(
                generator.PlanLayout,
                generator.GenerationParameters,
                "GameMapTest serialized settings",
                CreatePrototypeSpawnRequests(LoadRangedEnemySettings()));

            if (!EditorSceneManager.SaveScene(scene))
            {
                throw new BuildFailedException(
                    "Unity could not save the validated GameMapTest urban map setup.");
            }

            Debug.Log(
                "Configured GameMapTest to instantiate its medical Chest and two prototype " +
                "Enemies from the Raid spawn catalog while preserving stable IDs and layout inputs.");
        }

        [MenuItem("Tools/Fantasy Survival/Urban Map/Validate Layout Seeds")]
        public static void ValidateLayoutSeeds()
        {
            UrbanMapGenerationParameters parameters = UrbanMapGenerationParameters.CreateDefault();
            var emptyProtectedPoints = new List<Vector2>();
            ValidateLayoutSeeds(
                seed => UrbanMapLayoutPlanner.Generate(seed, Vector2.zero, emptyProtectedPoints, parameters),
                parameters,
                "default settings",
                CreatePrototypeSpawnRequests(LoadRangedEnemySettings()));
        }

        private static void ValidateLayoutSeeds(
            Func<int, UrbanMapLayout> layoutFactory,
            UrbanMapGenerationParameters parameters,
            string validationLabel,
            IReadOnlyList<UrbanRaidSpawnRequest> spawnRequests)
        {
            const int seedCount = 256;
            float minimumWidth = float.PositiveInfinity;
            float maximumWidth = float.NegativeInfinity;
            float minimumDepth = float.PositiveInfinity;
            float maximumDepth = float.NegativeInfinity;
            int minimumBuildings = int.MaxValue;
            int maximumBuildings = int.MinValue;
            var hashes = new HashSet<ulong>();
            for (int seed = 0; seed < seedCount; seed++)
            {
                UrbanMapLayout layout = layoutFactory(seed);
                if (!UrbanMapLayoutValidator.TryValidate(layout, parameters, out string error))
                {
                    throw new BuildFailedException($"Urban layout seed {seed} failed validation: {error}");
                }

                ulong firstHash = UrbanMapLayoutValidator.ComputeStableHash(layout);
                UrbanMapLayout repeated = layoutFactory(seed);
                ulong repeatedHash = UrbanMapLayoutValidator.ComputeStableHash(repeated);
                if (firstHash != repeatedHash)
                {
                    throw new BuildFailedException($"Urban layout seed {seed} is not deterministic.");
                }

                bool spawnCreated = UrbanMapLayoutPlanner.TryCreateRaidSpawnManifest(
                        layout,
                        spawnRequests,
                        out UrbanRaidSpawnManifest spawnManifest,
                        out string spawnError);
                bool repeatedSpawnCreated = UrbanMapLayoutPlanner.TryCreateRaidSpawnManifest(
                        repeated,
                        spawnRequests,
                        out UrbanRaidSpawnManifest repeatedSpawnManifest,
                        out string repeatedSpawnError);
                if (!spawnCreated || !repeatedSpawnCreated)
                {
                    throw new BuildFailedException(
                        $"Urban layout seed {seed} could not prepare deterministic raid spawns: " +
                        $"{spawnError ?? repeatedSpawnError}");
                }

                ValidateSpawnManifest(layout, spawnRequests, spawnManifest, seed);
                ulong worldHash = UrbanMapLayoutValidator.ComputeStableWorldHash(layout, spawnManifest);
                ulong repeatedWorldHash = UrbanMapLayoutValidator.ComputeStableWorldHash(
                    repeated,
                    repeatedSpawnManifest);
                if (worldHash != repeatedWorldHash)
                {
                    throw new BuildFailedException(
                        $"Urban layout seed {seed} raid spawn manifest is not deterministic.");
                }

                if (layout.Buildings.Count == 0)
                {
                    throw new BuildFailedException($"Urban layout seed {seed} generated no graybox buildings.");
                }

                if (!layout.TryGetPoi(UrbanPoiKind.Medical, out UrbanPoiPlacement medicalPoi) ||
                    medicalPoi.BuildingIndex < 0 ||
                    medicalPoi.BuildingIndex >= layout.Buildings.Count)
                {
                    throw new BuildFailedException(
                        $"Urban layout seed {seed} did not produce one valid Medical POI.");
                }

                hashes.Add(worldHash);
                minimumWidth = Mathf.Min(minimumWidth, layout.LocalBounds.width);
                maximumWidth = Mathf.Max(maximumWidth, layout.LocalBounds.width);
                minimumDepth = Mathf.Min(minimumDepth, layout.LocalBounds.height);
                maximumDepth = Mathf.Max(maximumDepth, layout.LocalBounds.height);
                minimumBuildings = Mathf.Min(minimumBuildings, layout.Buildings.Count);
                maximumBuildings = Mathf.Max(maximumBuildings, layout.Buildings.Count);
            }

            if (hashes.Count < seedCount * 0.95f)
            {
                throw new BuildFailedException(
                    $"Only {hashes.Count} unique urban layouts were generated from {seedCount} tested seeds.");
            }

            if (Mathf.Approximately(minimumWidth, maximumWidth) || Mathf.Approximately(minimumDepth, maximumDepth))
            {
                throw new BuildFailedException("Urban map dimensions did not vary across tested seeds.");
            }

            Debug.Log(
                $"Urban layout validation ({validationLabel}) passed for {seedCount} seeds. Unique={hashes.Count}, " +
                $"Width={minimumWidth:F1}-{maximumWidth:F1}, Depth={minimumDepth:F1}-{maximumDepth:F1}, " +
                $"Buildings={minimumBuildings}-{maximumBuildings}.");
        }

        private static void ValidateSpawnManifest(
            UrbanMapLayout layout,
            IReadOnlyList<UrbanRaidSpawnRequest> requests,
            UrbanRaidSpawnManifest manifest,
            int seed)
        {
            if (manifest == null || manifest.Seed != seed || manifest.Count != requests.Count)
            {
                throw new BuildFailedException(
                    $"Urban layout seed {seed} produced an incomplete raid spawn manifest.");
            }

            var requestIndex = new Dictionary<string, UrbanRaidSpawnRequest>(StringComparer.Ordinal);
            for (int index = 0; index < requests.Count; index++)
            {
                requestIndex.Add(requests[index].StableId, requests[index]);
            }

            var seenIds = new HashSet<string>(StringComparer.Ordinal);
            for (int index = 0; index < manifest.Count; index++)
            {
                UrbanRaidSpawnPlacement placement = manifest.Placements[index];
                if (!seenIds.Add(placement.StableId) ||
                    !requestIndex.TryGetValue(placement.StableId, out UrbanRaidSpawnRequest request) ||
                    placement.Kind != request.Kind)
                {
                    throw new BuildFailedException(
                        $"Urban layout seed {seed} produced an invalid or duplicate spawn stable ID.");
                }

                if (request.RequiredPoiKind != UrbanPoiKind.None)
                {
                    if (!layout.TryGetPoi(request.RequiredPoiKind, out UrbanPoiPlacement poi) ||
                        Vector2.Distance(placement.LocalPosition, poi.ContentLocalPosition) > 0.001f ||
                        Vector2.Distance(placement.ApproachLocalPosition, poi.ApproachLocalPosition) > 0.001f)
                    {
                        throw new BuildFailedException(
                            $"Urban layout seed {seed} did not bind '{placement.StableId}' to " +
                            $"its required {request.RequiredPoiKind} POI.");
                    }
                }

                if (Vector2.Distance(placement.LocalPosition, layout.EntryLocalPosition) + 0.001f <
                    request.EntryClearance)
                {
                    throw new BuildFailedException(
                        $"Urban layout seed {seed} placed '{placement.StableId}' inside RaidEntry protection.");
                }

                if (request.MaximumEntryDistance > 0f &&
                    Vector2.Distance(placement.LocalPosition, layout.EntryLocalPosition) - 0.001f >
                    request.MaximumEntryDistance)
                {
                    throw new BuildFailedException(
                        $"Urban layout seed {seed} placed '{placement.StableId}' outside its nearby test radius.");
                }

                if (Vector2.Distance(placement.LocalPosition, layout.PortalLocalPosition) + 0.001f <
                    request.PortalClearance)
                {
                    throw new BuildFailedException(
                        $"Urban layout seed {seed} placed '{placement.StableId}' inside ReturnPortal protection.");
                }

                for (int otherIndex = index + 1; otherIndex < manifest.Count; otherIndex++)
                {
                    UrbanRaidSpawnPlacement other = manifest.Placements[otherIndex];
                    UrbanRaidSpawnRequest otherRequest = requestIndex[other.StableId];
                    float requiredSeparation = Mathf.Max(
                        request.MinimumSeparation,
                        otherRequest.MinimumSeparation);
                    if (Vector2.Distance(placement.LocalPosition, other.LocalPosition) + 0.001f <
                        requiredSeparation)
                    {
                        throw new BuildFailedException(
                            $"Urban layout seed {seed} overlaps raid spawns '{placement.StableId}' " +
                            $"and '{other.StableId}'.");
                    }
                }
            }
        }

        private readonly struct LootEntrySetup
        {
            public LootEntrySetup(int itemDefinitionId, float dropChancePercent)
            {
                ItemDefinitionId = itemDefinitionId;
                DropChancePercent = dropChancePercent;
            }

            public int ItemDefinitionId { get; }
            public float DropChancePercent { get; }
        }

        private static T LoadRequiredAsset<T>(string path) where T : UnityEngine.Object
        {
            T asset = AssetDatabase.LoadAssetAtPath<T>(path);
            if (asset == null)
            {
                throw new BuildFailedException(
                    $"Required {typeof(T).Name} asset is missing at '{path}'.");
            }

            return asset;
        }

        private static LootTableDefinition CreateOrUpdateLootTable(
            string path,
            params LootEntrySetup[] entrySetups)
        {
            EnsureAssetFolder("Assets/GameData", "LootTables");
            LootTableDefinition lootTable = AssetDatabase.LoadAssetAtPath<LootTableDefinition>(path);
            if (lootTable == null)
            {
                lootTable = ScriptableObject.CreateInstance<LootTableDefinition>();
                lootTable.name = System.IO.Path.GetFileNameWithoutExtension(path);
                AssetDatabase.CreateAsset(lootTable, path);
            }

            ConfigureLootTableEntries(lootTable, entrySetups);
            EditorUtility.SetDirty(lootTable);
            AssetDatabase.SaveAssetIfDirty(lootTable);
            return lootTable;
        }

        private static void ConfigureLootTableEntries(
            LootTableDefinition lootTable,
            IReadOnlyList<LootEntrySetup> entrySetups)
        {
            var serialized = new SerializedObject(lootTable);
            SerializedProperty entries = serialized.FindProperty("entries");
            if (entries == null)
            {
                throw new BuildFailedException(
                    $"Loot table '{lootTable.name}' no longer exposes its serialized entries field.");
            }

            entries.arraySize = entrySetups.Count;
            for (int index = 0; index < entrySetups.Count; index++)
            {
                SerializedProperty entry = entries.GetArrayElementAtIndex(index);
                entry.FindPropertyRelative("itemDefinitionId").intValue =
                    entrySetups[index].ItemDefinitionId;
                entry.FindPropertyRelative("dropChancePercent").floatValue =
                    entrySetups[index].DropChancePercent;
            }

            serialized.ApplyModifiedPropertiesWithoutUndo();
        }

        private static EnemyDefinition CreateOrUpdateTestMeleeDefinition()
        {
            EnemyDefinition source = LoadRequiredAsset<EnemyDefinition>(SourceMeleeDefinitionPath);
            EnemyDefinition target = AssetDatabase.LoadAssetAtPath<EnemyDefinition>(
                TestMeleeDefinitionPath);
            if (target == null)
            {
                target = ScriptableObject.CreateInstance<EnemyDefinition>();
                AssetDatabase.CreateAsset(target, TestMeleeDefinitionPath);
            }

            EditorUtility.CopySerialized(source, target);
            target.name = "PrototypeMeleeDamageOne";
            var serialized = new SerializedObject(target);
            SerializedProperty ai = serialized.FindProperty("ai");
            if (ai == null)
            {
                throw new BuildFailedException(
                    "EnemyDefinition no longer exposes its serialized AI settings.");
            }

            ai.FindPropertyRelative("combatArchetype").enumValueIndex =
                (int)EnemyCombatArchetype.MeleeRush;
            ai.FindPropertyRelative("attackDamage").floatValue =
                CombatValueRules.AttackPowerStep;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(target);
            AssetDatabase.SaveAssetIfDirty(target);
            return LoadRequiredAsset<EnemyDefinition>(TestMeleeDefinitionPath);
        }

        private static void ConfigurePreparedRaidPrefabs(
            LootTableDefinition raidChestLoot,
            LootTableDefinition meleeCorpseLoot,
            EnemyDefinition testMeleeDefinition)
        {
            ConfigurePreparedRaidPrefab(
                RaidChestPrefabPath,
                root =>
                {
                    Chest chest = root.GetComponent<Chest>();
                    if (chest == null)
                    {
                        throw new BuildFailedException(
                            $"Prepared Raid Chest prefab has no root Chest: '{RaidChestPrefabPath}'.");
                    }

                    ConfigureRaidLootChest(chest, raidChestLoot);
                    ConfigureTimedLootInteraction(chest);
                });

            ConfigurePreparedRaidPrefab(
                MeleeEnemyPrefabPath,
                root =>
                {
                    EnemyStats stats = root.GetComponent<EnemyStats>();
                    EnemyAIController ai = root.GetComponent<EnemyAIController>();
                    if (stats == null || ai == null)
                    {
                        throw new BuildFailedException(
                            $"Prepared melee prefab is incomplete: '{MeleeEnemyPrefabPath}'.");
                    }

                    AssignEnemyDefinition(stats, testMeleeDefinition);
                    Chest corpse = FindOnlyCorpseInventory(ai);
                    ConfigureRaidLootChest(corpse, meleeCorpseLoot);
                    ConfigureTimedLootInteraction(corpse);
                });

            ConfigurePreparedRaidPrefab(
                RangedEnemyPrefabPath,
                root =>
                {
                    EnemyAIController ai = root.GetComponent<EnemyAIController>();
                    if (ai == null)
                    {
                        throw new BuildFailedException(
                            $"Prepared ranged prefab is incomplete: '{RangedEnemyPrefabPath}'.");
                    }

                    ConfigureTimedLootInteraction(FindOnlyCorpseInventory(ai));
                });
        }

        private static void ConfigurePreparedRaidPrefab(
            string prefabPath,
            Action<GameObject> configure)
        {
            LoadRequiredAsset<GameObject>(prefabPath);
            GameObject root = PrefabUtility.LoadPrefabContents(prefabPath);
            try
            {
                configure(root);
                GameObject saved = PrefabUtility.SaveAsPrefabAsset(
                    root,
                    prefabPath,
                    out bool success);
                if (!success || saved == null)
                {
                    throw new BuildFailedException(
                        $"Unity could not save prepared Raid prefab '{prefabPath}'.");
                }
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        private static RaidSpawnCatalogDefinition CreateOrUpdateRaidSpawnCatalog()
        {
            EnsureAssetFolder("Assets/GameData", "Raids");
            RaidSpawnCatalogDefinition catalog =
                AssetDatabase.LoadAssetAtPath<RaidSpawnCatalogDefinition>(
                    RaidSpawnCatalogPath);
            if (catalog == null)
            {
                catalog = ScriptableObject.CreateInstance<RaidSpawnCatalogDefinition>();
                AssetDatabase.CreateAsset(catalog, RaidSpawnCatalogPath);
            }

            Undo.RecordObject(catalog, "Configure Prototype Raid Spawn Catalog");
            var serialized = new SerializedObject(catalog);
            SerializedProperty entries = serialized.FindProperty("entries");
            if (entries == null)
            {
                throw new BuildFailedException(
                    "RaidSpawnCatalogDefinition no longer exposes its serialized entries field.");
            }

            entries.arraySize = 3;
            ConfigureSpawnCatalogEntry(
                entries.GetArrayElementAtIndex(0),
                RaidChestStableId,
                RaidChestObjectName,
                RaidSpawnContentKind.Chest,
                LoadRequiredAsset<GameObject>(RaidChestPrefabPath),
                0.5f,
                UrbanPoiKind.Medical);
            ConfigureSpawnCatalogEntry(
                entries.GetArrayElementAtIndex(1),
                MeleeEnemyStableId,
                MeleeEnemyObjectName,
                RaidSpawnContentKind.Enemy,
                LoadRequiredAsset<GameObject>(MeleeEnemyPrefabPath),
                0f,
                UrbanPoiKind.None);
            ConfigureSpawnCatalogEntry(
                entries.GetArrayElementAtIndex(2),
                RangedEnemyStableId,
                RangedEnemyObjectName,
                RaidSpawnContentKind.Enemy,
                LoadRequiredAsset<GameObject>(RangedEnemyPrefabPath),
                0f,
                UrbanPoiKind.None);
            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(catalog);
            AssetDatabase.SaveAssetIfDirty(catalog);

            if (!catalog.TryValidate(out string error))
            {
                throw new BuildFailedException(
                    $"Prototype Raid spawn catalog is invalid: {error}");
            }

            return LoadRequiredAsset<RaidSpawnCatalogDefinition>(RaidSpawnCatalogPath);
        }

        private static void ConfigureSpawnCatalogEntry(
            SerializedProperty entry,
            string stableId,
            string runtimeName,
            RaidSpawnContentKind kind,
            GameObject prefab,
            float groundYOffset,
            UrbanPoiKind requiredPoiKind)
        {
            entry.FindPropertyRelative("stableId").stringValue = stableId;
            entry.FindPropertyRelative("runtimeName").stringValue = runtimeName;
            entry.FindPropertyRelative("kind").enumValueIndex = (int)kind;
            entry.FindPropertyRelative("prefab").objectReferenceValue = prefab;
            entry.FindPropertyRelative("groundYOffset").floatValue = groundYOffset;
            entry.FindPropertyRelative("requiredPoiKind").enumValueIndex =
                (int)requiredPoiKind;
        }

        private static IReadOnlyList<UrbanRaidSpawnRequest> CreatePrototypeSpawnRequests(
            EnemyAISettings rangedSettings)
        {
            if (rangedSettings == null ||
                rangedSettings.CombatArchetype != EnemyCombatArchetype.RangedPursuit)
            {
                throw new BuildFailedException(
                    "The prototype ranged Enemy has no valid ranged AI settings.");
            }

            return new[]
            {
                UrbanRaidSpawnPrototypeRules.CreatePoiChestRequest(
                    RaidChestStableId,
                    UrbanPoiKind.Medical),
                UrbanRaidSpawnPrototypeRules.CreateNearEntryMeleeRequest(MeleeEnemyStableId),
                UrbanRaidSpawnPrototypeRules.CreateEnemyRequest(
                    RangedEnemyStableId,
                    rangedSettings.VisionRange,
                    rangedSettings.PatrolRadius)
            };
        }

        private static EnemyAISettings LoadRangedEnemySettings()
        {
            GameObject prefab = LoadRequiredAsset<GameObject>(RangedEnemyPrefabPath);
            EnemyStats stats = prefab.GetComponentInChildren<EnemyStats>(true);
            if (stats == null || stats.Definition == null)
            {
                throw new BuildFailedException(
                    $"Prototype ranged Enemy prefab has no EnemyStats definition: '{RangedEnemyPrefabPath}'.");
            }

            return stats.Definition.AI;
        }

        private static EnemyAIController FindEnemyByName(Scene scene, string objectName)
        {
            EnemyAIController found = null;
            EnemyAIController[] enemies = FindComponentsInScene<EnemyAIController>(scene);
            for (int index = 0; index < enemies.Length; index++)
            {
                Transform root = enemies[index].transform.root;
                if (enemies[index].name != objectName && root.name != objectName)
                {
                    continue;
                }

                if (found != null)
                {
                    throw new BuildFailedException(
                        $"GameMapTest contains more than one required Enemy named '{objectName}'.");
                }

                found = enemies[index];
            }

            return found;
        }

        private static Chest FindOnlyCorpseInventory(EnemyAIController enemy)
        {
            Chest[] inventories = enemy.GetComponentsInChildren<Chest>(true);
            if (inventories.Length != 1)
            {
                throw new BuildFailedException(
                    $"Enemy '{enemy.name}' must have exactly one corpse Chest, found {inventories.Length}.");
            }

            return inventories[0];
        }

        private static Chest FindStandaloneChest(Scene scene, string objectName)
        {
            Chest found = null;
            Chest[] chests = FindComponentsInScene<Chest>(scene);
            for (int index = 0; index < chests.Length; index++)
            {
                if (chests[index].GetComponentInParent<EnemyAIController>(true) != null)
                {
                    continue;
                }

                if (chests[index].name != objectName)
                {
                    continue;
                }

                if (found != null)
                {
                    throw new BuildFailedException(
                        $"GameMapTest contains more than one standalone Chest named '{objectName}'.");
                }

                found = chests[index];
            }

            return found;
        }

        private static void AssignEnemyDefinition(
            EnemyStats stats,
            EnemyDefinition definition)
        {
            if (stats == null || definition == null)
            {
                throw new BuildFailedException(
                    $"Cannot configure the prototype melee Enemy. " +
                    $"Stats missing={stats == null}, Definition missing={definition == null}.");
            }

            Undo.RecordObject(stats, "Configure Prototype Melee Definition");
            var serialized = new SerializedObject(stats);
            serialized.FindProperty("definition").objectReferenceValue = definition;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(stats);
        }

        private static void ConfigureRaidLootChest(
            Chest chest,
            LootTableDefinition lootTable)
        {
            Undo.RecordObject(chest, "Configure Prototype Raid Loot");
            var serialized = new SerializedObject(chest);
            serialized.FindProperty("lootTable").objectReferenceValue = lootTable;
            serialized.FindProperty("startingItemIds").arraySize = 0;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(chest);
        }

        private static void ConfigureTimedLootInteraction(Chest chest)
        {
            ChestInteractable interactable = chest != null
                ? chest.GetComponent<ChestInteractable>()
                : null;
            if (interactable == null)
            {
                throw new BuildFailedException(
                    $"Raid loot Chest '{chest?.name ?? "<missing>"}' has no ChestInteractable.");
            }

            Undo.RecordObject(interactable, "Configure Timed Raid Loot Interaction");
            var serialized = new SerializedObject(interactable);
            SerializedProperty openMode = serialized.FindProperty("openMode");
            SerializedProperty duration = serialized.FindProperty("openActionDurationSeconds");
            if (openMode == null || duration == null)
            {
                throw new BuildFailedException(
                    "ChestInteractable timed-search serialized fields are missing.");
            }

            openMode.intValue = (int)ChestOpenMode.TimedSearch;
            duration.floatValue = PrototypeLootSearchDurationSeconds;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            if (PrefabUtility.IsPartOfPrefabInstance(interactable))
            {
                PrefabUtility.RecordPrefabInstancePropertyModifications(interactable);
            }

            EditorUtility.SetDirty(interactable);
        }

        private static void ConfigureRaidSceneBinding(
            RaidCheckpointSceneBinding binding,
            ProceduralUrbanMapGenerator generator,
            RaidSpawnCatalogDefinition spawnCatalog)
        {
            Undo.RecordObject(binding, "Configure Prototype Raid Bindings");
            var serialized = new SerializedObject(binding);
            serialized.FindProperty("mapGenerator").objectReferenceValue = generator;
            serialized.FindProperty("spawnCatalog").objectReferenceValue = spawnCatalog;

            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(binding);
        }

        private static IReadOnlyList<Transform> EnsureLayoutProtectionAnchors(
            Scene scene,
            EnemyAIController legacyMelee,
            EnemyAIController legacyRanged)
        {
            GameObject root = FindRootByName(scene, LayoutProtectionRootName);
            if (root == null)
            {
                root = new GameObject(LayoutProtectionRootName);
                Undo.RegisterCreatedObjectUndo(root, "Create Urban Layout Protection Anchors");
                SceneManager.MoveGameObjectToScene(root, scene);
            }

            Transform melee = EnsureProtectionAnchor(
                root.transform,
                MeleeProtectionAnchorName,
                legacyMelee != null
                    ? legacyMelee.transform.position
                    : new Vector3(0f, 0f, 3f));
            Transform ranged = EnsureProtectionAnchor(
                root.transform,
                RangedProtectionAnchorName,
                legacyRanged != null
                    ? legacyRanged.transform.position
                    : new Vector3(6f, 0f, 6f));
            return new[] { melee, ranged };
        }

        private static Transform EnsureProtectionAnchor(
            Transform parent,
            string name,
            Vector3 initialWorldPosition)
        {
            Transform anchor = parent.Find(name);
            if (anchor != null)
            {
                return anchor;
            }

            var anchorObject = new GameObject(name);
            Undo.RegisterCreatedObjectUndo(anchorObject, "Create Urban Layout Protection Anchor");
            anchorObject.transform.SetParent(parent, worldPositionStays: false);
            anchorObject.transform.position = initialWorldPosition;
            return anchorObject.transform;
        }

        private static void ReplacePrototypeProtectedAnchors(
            SerializedProperty protectedAnchors,
            EnemyAIController legacyMelee,
            EnemyAIController legacyRanged,
            IReadOnlyList<Transform> requiredAnchors)
        {
            var preserved = new List<Transform>(
                protectedAnchors.arraySize + requiredAnchors.Count);
            var seen = new HashSet<Transform>();
            Transform legacyMeleeTransform = legacyMelee != null
                ? legacyMelee.transform
                : null;
            Transform legacyRangedTransform = legacyRanged != null
                ? legacyRanged.transform
                : null;
            for (int index = 0; index < protectedAnchors.arraySize; index++)
            {
                Transform existing = protectedAnchors
                    .GetArrayElementAtIndex(index)
                    .objectReferenceValue as Transform;
                if (existing != null && existing != legacyMeleeTransform &&
                    existing != legacyRangedTransform && seen.Add(existing))
                {
                    preserved.Add(existing);
                }
            }

            for (int index = 0; index < requiredAnchors.Count; index++)
            {
                Transform required = requiredAnchors[index];
                if (seen.Add(required))
                {
                    preserved.Add(required);
                }
            }

            protectedAnchors.arraySize = preserved.Count;
            for (int index = 0; index < preserved.Count; index++)
            {
                protectedAnchors.GetArrayElementAtIndex(index).objectReferenceValue =
                    preserved[index];
            }
        }

        private static void RemoveLegacySpawnFixtures(
            Chest legacyChest,
            EnemyAIController legacyMelee,
            EnemyAIController legacyRanged)
        {
            var roots = new HashSet<GameObject>();
            if (legacyChest != null)
            {
                roots.Add(legacyChest.transform.root.gameObject);
            }
            if (legacyMelee != null)
            {
                roots.Add(legacyMelee.transform.root.gameObject);
            }
            if (legacyRanged != null)
            {
                roots.Add(legacyRanged.transform.root.gameObject);
            }

            foreach (GameObject root in roots)
            {
                Undo.DestroyObjectImmediate(root);
            }
        }

        private static void ValidateLootTables(
            ItemDatabase itemDatabase,
            LootTableDefinition raidChestLoot,
            LootTableDefinition meleeCorpseLoot)
        {
            if (!raidChestLoot.TryValidate(itemDatabase, out string chestError))
            {
                throw new BuildFailedException(
                    $"Prototype Chest LootTable validation failed: {chestError}");
            }

            if (!meleeCorpseLoot.TryValidate(itemDatabase, out string corpseError))
            {
                throw new BuildFailedException(
                    $"Prototype corpse LootTable validation failed: {corpseError}");
            }

            for (int seed = 0; seed < 256; seed++)
            {
                if (!LootTableRoller.TryRollDefinitionIds(
                        raidChestLoot,
                        seed,
                        RaidChestStableId,
                        out List<int> first,
                        out string firstError))
                {
                    throw new BuildFailedException(
                        $"Prototype Chest loot seed {seed} failed: {firstError}");
                }

                if (!LootTableRoller.TryRollDefinitionIds(
                        raidChestLoot,
                        seed,
                        RaidChestStableId,
                        out List<int> repeated,
                        out string repeatedError))
                {
                    throw new BuildFailedException(
                        $"Repeated prototype Chest loot seed {seed} failed: {repeatedError}");
                }

                if (first.Count != 1 || repeated.Count != 1 ||
                    first[0] != 7 || repeated[0] != 7)
                {
                    throw new BuildFailedException(
                        $"Medical POI Chest loot seed {seed} did not deterministically select Medicine ID 7.");
                }

                if (!LootTableRoller.TryRollDefinitionIds(
                        meleeCorpseLoot,
                        seed,
                        MeleeEnemyStableId + "/corpse",
                        out List<int> corpse,
                        out string corpseRollError) ||
                    corpse.Count != 1 || corpse[0] != 1)
                {
                    throw new BuildFailedException(
                        $"Prototype melee corpse loot seed {seed} failed: {corpseRollError}");
                }
            }

            var boundaryTable = ScriptableObject.CreateInstance<LootTableDefinition>();
            boundaryTable.name = "ZeroHundredBoundaryValidation";
            try
            {
                ConfigureLootTableEntries(
                    boundaryTable,
                    new[]
                    {
                        new LootEntrySetup(1, 0f),
                        new LootEntrySetup(2, 100f)
                    });
                if (!boundaryTable.TryValidate(itemDatabase, out string boundaryError))
                {
                    throw new BuildFailedException(
                        $"Loot 0/100 boundary table is invalid: {boundaryError}");
                }

                for (int seed = 0; seed < 32; seed++)
                {
                    if (!LootTableRoller.TryRollDefinitionIds(
                            boundaryTable,
                            seed,
                            "validation:zero_hundred",
                            out List<int> boundaryResult,
                            out string boundaryRollError) ||
                        boundaryResult.Count != 1 || boundaryResult[0] != 2)
                    {
                        throw new BuildFailedException(
                            $"Loot 0/100 boundary failed at seed {seed}: {boundaryRollError}");
                    }
                }
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(boundaryTable);
            }

            if (!LootTableRoller.TryCreateInventory(
                    raidChestLoot,
                    itemDatabase,
                    mapSeed: 0,
                    stableContainerId: RaidChestStableId,
                    width: 4,
                    height: 4,
                    out _,
                    out string inventoryError))
            {
                throw new BuildFailedException(
                    $"Prototype Chest loot cannot materialize in a 4x4 inventory: {inventoryError}");
            }
        }

        private static void EnsureAssetFolder(string parentPath, string folderName)
        {
            string folderPath = $"{parentPath}/{folderName}";
            if (!AssetDatabase.IsValidFolder(folderPath))
            {
                AssetDatabase.CreateFolder(parentPath, folderName);
            }
        }

        public static void ConfigureAndValidateBatch()
        {
            ConfigureGameMapTest();
            ValidateLayoutSeeds();
        }

        private static void ValidateConfiguredScene(
            Scene scene,
            LootTableDefinition raidChestLoot,
            LootTableDefinition meleeCorpseLoot,
            EnemyDefinition testMeleeDefinition,
            RaidSpawnCatalogDefinition spawnCatalog)
        {
            ProceduralUrbanMapGenerator[] generators = FindComponentsInScene<ProceduralUrbanMapGenerator>(scene);
            if (generators.Length != 1)
            {
                throw new BuildFailedException(
                    $"GameMapTest must contain exactly one ProceduralUrbanMapGenerator, but found {generators.Length}.");
            }

            if (generators[0].GetComponent<NavMeshSurface>() == null)
            {
                throw new BuildFailedException("GameMapTest ProceduralUrbanMapGenerator has no NavMeshSurface.");
            }

            string catalogError = null;
            if (spawnCatalog == null || !spawnCatalog.TryValidate(out catalogError))
            {
                throw new BuildFailedException(
                    $"GameMapTest Raid spawn catalog is invalid: {catalogError}");
            }

            RaidSpawnCatalogEntry chestEntry = FindCatalogEntry(
                spawnCatalog,
                RaidChestStableId,
                RaidSpawnContentKind.Chest);
            RaidSpawnCatalogEntry meleeEntry = FindCatalogEntry(
                spawnCatalog,
                MeleeEnemyStableId,
                RaidSpawnContentKind.Enemy);
            RaidSpawnCatalogEntry rangedEntry = FindCatalogEntry(
                spawnCatalog,
                RangedEnemyStableId,
                RaidSpawnContentKind.Enemy);

            Chest raidChest = chestEntry.Prefab.GetComponent<Chest>();
            EnemyAIController meleeEnemy = meleeEntry.Prefab.GetComponent<EnemyAIController>();
            EnemyAIController rangedEnemy = rangedEntry.Prefab.GetComponent<EnemyAIController>();
            EnemyStats meleeStats = meleeEntry.Prefab.GetComponent<EnemyStats>();
            EnemyStats rangedStats = rangedEntry.Prefab.GetComponent<EnemyStats>();
            if (meleeStats == null || meleeStats.Definition != testMeleeDefinition ||
                meleeStats.Definition.AI == null ||
                meleeStats.Definition.AI.CombatArchetype != EnemyCombatArchetype.MeleeRush ||
                !Mathf.Approximately(
                    meleeStats.Definition.AI.AttackDamage,
                    CombatValueRules.AttackPowerStep))
            {
                throw new BuildFailedException(
                    "GameMapTest required melee Enemy is not the minimum 10-damage test definition.");
            }

            if (rangedStats == null || rangedStats.Definition == null ||
                rangedStats.Definition.AI == null ||
                rangedStats.Definition.AI.CombatArchetype != EnemyCombatArchetype.RangedPursuit)
            {
                throw new BuildFailedException(
                    "GameMapTest required ranged Enemy did not retain its ranged definition.");
            }

            Chest corpseChest = FindOnlyCorpseInventory(meleeEnemy);
            Chest rangedCorpseChest = FindOnlyCorpseInventory(rangedEnemy);
            if (raidChest.LootTable != raidChestLoot || corpseChest.LootTable != meleeCorpseLoot ||
                HasAuthoredStartingItems(raidChest) || HasAuthoredStartingItems(corpseChest))
            {
                throw new BuildFailedException(
                    "GameMapTest prototype Chest or corpse inventory has conflicting loot sources.");
            }

            if (!HasExpectedTimedLootInteraction(raidChest) ||
                !HasExpectedTimedLootInteraction(corpseChest) ||
                !HasExpectedTimedLootInteraction(rangedCorpseChest))
            {
                throw new BuildFailedException(
                    "GameMapTest raid Chest and corpse inventories must use the explicit " +
                    "prototype timed-search policy.");
            }

            if (FindComponentsInScene<Chest>(scene).Length != 0 ||
                FindComponentsInScene<EnemyStats>(scene).Length != 0)
            {
                throw new BuildFailedException(
                    "GameMapTest still contains authored Raid Chest or Enemy instances; " +
                    "the spawn catalog must be the only runtime creation source.");
            }

            RaidCheckpointSceneBinding[] raidBindings =
                FindComponentsInScene<RaidCheckpointSceneBinding>(scene);
            if (raidBindings.Length != 1 || !raidBindings[0].IsConfigured ||
                raidBindings[0].SpawnCatalog != spawnCatalog)
            {
                throw new BuildFailedException(
                    "GameMapTest must contain one valid RaidCheckpointSceneBinding.");
            }

            int missingScriptCount = 0;
            GameObject[] roots = scene.GetRootGameObjects();
            for (int index = 0; index < roots.Length; index++)
            {
                Transform[] transforms = roots[index].GetComponentsInChildren<Transform>(true);
                for (int transformIndex = 0; transformIndex < transforms.Length; transformIndex++)
                {
                    missingScriptCount += GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(
                        transforms[transformIndex].gameObject);
                }
            }

            if (missingScriptCount != 0)
            {
                throw new BuildFailedException($"GameMapTest contains {missingScriptCount} missing scripts after setup.");
            }
        }

        private static bool HasAuthoredStartingItems(Chest chest)
        {
            var serialized = new SerializedObject(chest);
            SerializedProperty startingItems = serialized.FindProperty("startingItemIds");
            return startingItems == null || startingItems.arraySize != 0;
        }

        private static bool HasExpectedTimedLootInteraction(Chest chest)
        {
            ChestInteractable interactable = chest != null
                ? chest.GetComponent<ChestInteractable>()
                : null;
            return interactable != null && interactable.UsesTimedSearch &&
                   Mathf.Approximately(
                       interactable.OpenActionDurationSeconds,
                       PrototypeLootSearchDurationSeconds) &&
                   interactable.TryValidateOpenConfiguration(out _);
        }

        private static RaidSpawnCatalogEntry FindCatalogEntry(
            RaidSpawnCatalogDefinition catalog,
            string stableId,
            RaidSpawnContentKind expectedKind)
        {
            RaidSpawnCatalogEntry found = null;
            for (int index = 0; index < catalog.Entries.Count; index++)
            {
                RaidSpawnCatalogEntry entry = catalog.Entries[index];
                if (entry.StableId != stableId)
                {
                    continue;
                }

                if (found != null || entry.Kind != expectedKind)
                {
                    throw new BuildFailedException(
                        $"Raid spawn catalog entry '{stableId}' is duplicated or has the wrong kind.");
                }

                found = entry;
            }

            if (found == null)
            {
                throw new BuildFailedException(
                    $"Raid spawn catalog is missing required entry '{stableId}'.");
            }

            return found;
        }

        private static void EnsureOpenScenesAreClean()
        {
            for (int sceneIndex = 0; sceneIndex < SceneManager.sceneCount; sceneIndex++)
            {
                Scene openScene = SceneManager.GetSceneAt(sceneIndex);
                if (openScene.isDirty)
                {
                    throw new BuildFailedException(
                        $"Urban map setup stopped because open scene '{openScene.name}' has unsaved changes. Save or revert it first.");
                }
            }
        }

        private static T FindComponentInScene<T>(Scene scene, Predicate<T> predicate) where T : Component
        {
            T[] components = FindComponentsInScene<T>(scene);
            for (int index = 0; index < components.Length; index++)
            {
                if (predicate(components[index]))
                {
                    return components[index];
                }
            }

            return null;
        }

        private static T[] FindComponentsInScene<T>(Scene scene) where T : Component
        {
            var components = new List<T>();
            GameObject[] roots = scene.GetRootGameObjects();
            for (int index = 0; index < roots.Length; index++)
            {
                components.AddRange(roots[index].GetComponentsInChildren<T>(true));
            }

            return components.ToArray();
        }

        private static GameObject FindRootByName(Scene scene, string objectName)
        {
            GameObject[] roots = scene.GetRootGameObjects();
            for (int index = 0; index < roots.Length; index++)
            {
                if (roots[index].name == objectName)
                {
                    return roots[index];
                }
            }

            return null;
        }
    }
}
