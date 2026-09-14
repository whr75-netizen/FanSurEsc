using System;
using System.Collections.Generic;
using FantasySurvival.Inventory;
using FantasySurvival.SaveSystem;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using UnityEngine;
using UnityEngine.SceneManagement;
using VariableInventorySystem;

namespace FantasySurvival.Raids
{
    public enum RaidSceneArrivalReadiness
    {
        Pending,
        Ready,
        Invalid
    }

    [DefaultExecutionOrder(-10500)]
    [DisallowMultipleComponent]
    public sealed class RaidCheckpointSceneBinding : MonoBehaviour
    {
        private sealed class RuntimeChestBinding
        {
            public RuntimeChestBinding(RaidSpawnCatalogEntry definition, Chest chest)
            {
                Definition = definition;
                Chest = chest;
            }

            public RaidSpawnCatalogEntry Definition { get; }
            public string StableId => Definition.StableId;
            public Chest Chest { get; }
        }

        private sealed class RuntimeEnemyBinding
        {
            public RuntimeEnemyBinding(
                RaidSpawnCatalogEntry definition,
                EnemyStats stats,
                Chest corpseInventory)
            {
                Definition = definition;
                Stats = stats;
                CorpseInventory = corpseInventory;
            }

            public RaidSpawnCatalogEntry Definition { get; }
            public string StableId => Definition.StableId;
            public EnemyStats Stats { get; }
            public Chest CorpseInventory { get; }
        }

        public sealed class RestorePlan
        {
            internal readonly List<ChestRestore> Chests = new List<ChestRestore>();
            internal readonly List<EnemyRestore> Enemies = new List<EnemyRestore>();
            internal readonly List<WorldItemRestore> WorldItems =
                new List<WorldItemRestore>();
        }

        internal sealed class ChestRestore
        {
            public Chest Chest;
            public StandardStashViewData Candidate;
            public StandardStashViewData Original;
        }

        internal sealed class EnemyRestore
        {
            public EnemyStats Stats;
            public Chest CorpseInventory;
            public StandardStashViewData CorpseCandidate;
            public StandardStashViewData OriginalCorpse;
            public Vector3 Position;
            public Quaternion Rotation;
            public Vector3 OriginalPosition;
            public Quaternion OriginalRotation;
            public float CurrentHealth;
            public float MaxHealth;
        }

        internal sealed class WorldItemRestore
        {
            public string StableId;
            public StandardStashViewData Inventory;
            public Vector3 Position;
            public Quaternion Rotation;
        }

        private readonly struct FreshLootApplication
        {
            public FreshLootApplication(
                Chest chest,
                StandardStashViewData original,
                StandardStashViewData candidate)
            {
                Chest = chest;
                Original = original;
                Candidate = candidate;
            }

            public Chest Chest { get; }
            public StandardStashViewData Original { get; }
            public StandardStashViewData Candidate { get; }
        }

        [SerializeField] private string sceneStateId = "core:gamemaptest:v1";
        [SerializeField] private ProceduralUrbanMapGenerator mapGenerator;
        [SerializeField] private RaidSpawnCatalogDefinition spawnCatalog;

        private RaidCheckpointController controller;
        private GameObject runtimeSpawnRoot;
        private readonly List<RuntimeChestBinding> runtimeChests =
            new List<RuntimeChestBinding>();
        private readonly List<RuntimeEnemyBinding> runtimeEnemies =
            new List<RuntimeEnemyBinding>();
        private string seedPreparationError;
        private UrbanRaidSpawnManifest spawnManifest;
        private string spawnPreparationError;
        private bool spawnNavigationValidated;
        private string spawnNavigationValidationError;
        private bool freshLootInitialized;
        private int freshLootSeed;

        public string SceneStateId => sceneStateId;
        public string SceneName => gameObject.scene.name;
        public ProceduralUrbanMapGenerator MapGenerator => mapGenerator;
        public RaidSpawnCatalogDefinition SpawnCatalog => spawnCatalog;
        public int RuntimeChestCount => runtimeChests.Count;
        public int RuntimeEnemyCount => runtimeEnemies.Count;
        public bool RuntimeEntitiesInstantiated => runtimeSpawnRoot != null;
        public bool IsConfigured => TryValidateCatalogConfiguration(out _);
        public string SeedPreparationError => seedPreparationError;
        public UrbanRaidSpawnManifest SpawnManifest => spawnManifest;

        public bool TryGetRuntimeChest(string stableId, out Chest chest)
        {
            for (int index = 0; index < runtimeChests.Count; index++)
            {
                RuntimeChestBinding binding = runtimeChests[index];
                if (string.Equals(binding.StableId, stableId, StringComparison.Ordinal))
                {
                    chest = binding.Chest;
                    return chest != null;
                }
            }

            chest = null;
            return false;
        }

        public bool TryGetRuntimeEnemy(string stableId, out EnemyStats stats)
        {
            for (int index = 0; index < runtimeEnemies.Count; index++)
            {
                RuntimeEnemyBinding binding = runtimeEnemies[index];
                if (string.Equals(binding.StableId, stableId, StringComparison.Ordinal))
                {
                    stats = binding.Stats;
                    return stats != null;
                }
            }

            stats = null;
            return false;
        }

        public RaidSceneArrivalReadiness GetArrivalReadiness(out string error)
        {
            if (!string.IsNullOrEmpty(seedPreparationError))
            {
                error = seedPreparationError;
                return RaidSceneArrivalReadiness.Invalid;
            }

            if (mapGenerator == null)
            {
                error = "Raid scene map generator is missing.";
                return RaidSceneArrivalReadiness.Invalid;
            }

            if (!string.IsNullOrEmpty(spawnPreparationError))
            {
                error = spawnPreparationError;
                return RaidSceneArrivalReadiness.Invalid;
            }

            if (mapGenerator.NavigationBuildPending)
            {
                error = null;
                return RaidSceneArrivalReadiness.Pending;
            }

            if (mapGenerator.CurrentLayout == null)
            {
                error = "Raid scene map layout was not generated.";
                return RaidSceneArrivalReadiness.Invalid;
            }

            if (spawnManifest == null ||
                spawnManifest.Seed != mapGenerator.CurrentSeed ||
                spawnManifest.Seed != mapGenerator.CurrentLayout.Seed)
            {
                error = "Raid scene spawn manifest was not prepared for the current map seed.";
                return RaidSceneArrivalReadiness.Invalid;
            }

            if (!TryBuildRuntimeIndexes(out _, out _, out error))
            {
                return RaidSceneArrivalReadiness.Invalid;
            }

            if (!mapGenerator.NavigationPathComplete)
            {
                error =
                    $"Raid map seed {mapGenerator.CurrentSeed} has no complete " +
                    "RaidEntry-to-ReturnPortal navigation path.";
                return RaidSceneArrivalReadiness.Invalid;
            }

            if (!string.IsNullOrEmpty(spawnNavigationValidationError))
            {
                error = spawnNavigationValidationError;
                return RaidSceneArrivalReadiness.Invalid;
            }

            if (!spawnNavigationValidated)
            {
                if (!TryValidateSpawnNavigation(out spawnNavigationValidationError))
                {
                    error = spawnNavigationValidationError;
                    return RaidSceneArrivalReadiness.Invalid;
                }

                spawnNavigationValidated = true;
            }

            error = null;
            return RaidSceneArrivalReadiness.Ready;
        }

        private void Awake()
        {
            controller = PersistentGameplayShell.Instance != null
                ? PersistentGameplayShell.Instance.RaidCheckpoint
                : null;
            if (controller == null)
            {
                Debug.LogError("Raid checkpoint scene binding requires the persistent checkpoint controller.", this);
                enabled = false;
                return;
            }

            if (!TryValidateCatalogConfiguration(out string configurationError))
            {
                Debug.LogError($"Raid checkpoint scene binding is invalid: {configurationError}", this);
                enabled = false;
                return;
            }

            mapGenerator.LayoutGeometryGenerated += HandleLayoutGeometryGenerated;

            if (!controller.TryRegisterScene(this, out string registrationError))
            {
                Debug.LogError($"Raid checkpoint scene registration failed: {registrationError}", this);
                mapGenerator.LayoutGeometryGenerated -= HandleLayoutGeometryGenerated;
                enabled = false;
                return;
            }

            if (controller.TryGetPendingMapSeed(
                    SceneName,
                    sceneStateId,
                    out int resumeSeed))
            {
                if (!mapGenerator.GenerateWithSeed(resumeSeed))
                {
                    seedPreparationError =
                        $"Could not generate the recovered raid map seed {resumeSeed}.";
                }
            }
            else if (mapGenerator.CurrentLayout != null)
            {
                HandleLayoutGeometryGenerated(mapGenerator.CurrentLayout);
            }
        }

        private void OnDestroy()
        {
            if (mapGenerator != null)
            {
                mapGenerator.LayoutGeometryGenerated -= HandleLayoutGeometryGenerated;
            }
            controller?.UnregisterScene(this);
            runtimeChests.Clear();
            runtimeEnemies.Clear();
            runtimeSpawnRoot = null;
        }

        private void HandleLayoutGeometryGenerated(UrbanMapLayout layout)
        {
            spawnManifest = null;
            spawnPreparationError = null;
            spawnNavigationValidated = false;
            spawnNavigationValidationError = null;

            try
            {
                if (runtimeSpawnRoot != null || runtimeChests.Count != 0 ||
                    runtimeEnemies.Count != 0)
                {
                    spawnPreparationError =
                        "A live Raid entity registry already exists. Mid-raid map rerolls are not supported.";
                    return;
                }

                if (layout == null || mapGenerator == null || mapGenerator.GeneratedContent == null)
                {
                    spawnPreparationError =
                        "Raid spawn placement requires generated map geometry and its owning Transform.";
                    return;
                }

                if (!TryBuildSpawnRequests(out List<UrbanRaidSpawnRequest> requests, out string requestError))
                {
                    spawnPreparationError = requestError;
                    return;
                }

                if (!UrbanMapLayoutPlanner.TryCreateRaidSpawnManifest(
                        layout,
                        requests,
                        out UrbanRaidSpawnManifest candidate,
                        out string manifestError))
                {
                    spawnPreparationError = manifestError;
                    return;
                }

                if (!TryInstantiateRuntimeEntities(candidate, out string applicationError))
                {
                    spawnPreparationError = applicationError;
                    return;
                }

                spawnManifest = candidate;
            }
            catch (Exception exception)
            {
                spawnPreparationError =
                    $"Raid spawn manifest preparation threw an exception: {exception.Message}";
            }
        }

        private bool TryBuildSpawnRequests(
            out List<UrbanRaidSpawnRequest> requests,
            out string error)
        {
            if (!TryValidateCatalogConfiguration(out error))
            {
                requests = null;
                return false;
            }

            requests = new List<UrbanRaidSpawnRequest>(spawnCatalog.Entries.Count);
            for (int index = 0; index < spawnCatalog.Entries.Count; index++)
            {
                RaidSpawnCatalogEntry entry = spawnCatalog.Entries[index];
                if (entry.Kind == RaidSpawnContentKind.Chest)
                {
                    requests.Add(entry.RequiredPoiKind == UrbanPoiKind.None
                        ? UrbanRaidSpawnPrototypeRules.CreateChestRequest(entry.StableId)
                        : UrbanRaidSpawnPrototypeRules.CreatePoiChestRequest(
                            entry.StableId,
                            entry.RequiredPoiKind));
                    continue;
                }

                EnemyStats stats = entry.Prefab.GetComponent<EnemyStats>();
                EnemyAISettings ai = stats != null && stats.Definition != null
                    ? stats.Definition.AI
                    : null;
                if (ai == null)
                {
                    error = $"Raid Enemy '{entry.StableId}' has no AI definition for spawn safety.";
                    requests = null;
                    return false;
                }

                requests.Add(ai.CombatArchetype == EnemyCombatArchetype.MeleeRush
                    ? UrbanRaidSpawnPrototypeRules.CreateNearEntryMeleeRequest(entry.StableId)
                    : UrbanRaidSpawnPrototypeRules.CreateEnemyRequest(
                        entry.StableId,
                        ai.VisionRange,
                        ai.PatrolRadius));
            }

            error = null;
            return true;
        }

        private bool TryInstantiateRuntimeEntities(
            UrbanRaidSpawnManifest candidate,
            out string error)
        {
            error = null;
            if (candidate == null || spawnCatalog == null ||
                candidate.Count != spawnCatalog.Entries.Count)
            {
                error = "Raid spawn manifest entity count does not match the spawn catalog.";
                return false;
            }

            var candidateChests = new List<RuntimeChestBinding>();
            var candidateEnemies = new List<RuntimeEnemyBinding>();
            var root = new GameObject("RuntimeRaidEntities");
            SceneManager.MoveGameObjectToScene(root, gameObject.scene);
            bool succeeded = false;
            try
            {
                for (int index = 0; index < spawnCatalog.Entries.Count; index++)
                {
                    RaidSpawnCatalogEntry entry = spawnCatalog.Entries[index];
                    UrbanRaidSpawnKind expectedKind = entry.Kind == RaidSpawnContentKind.Chest
                        ? UrbanRaidSpawnKind.Chest
                        : UrbanRaidSpawnKind.Enemy;
                    if (!candidate.TryGetPlacement(
                            entry.StableId,
                            out UrbanRaidSpawnPlacement placement) ||
                        placement.Kind != expectedKind)
                    {
                        error =
                            $"Raid spawn manifest is missing the expected {expectedKind} " +
                            $"'{entry.StableId}'.";
                        return false;
                    }

                    Vector3 worldPosition = mapGenerator.GeneratedContent.TransformPoint(
                        new Vector3(placement.LocalPosition.x,
                            mapGenerator.GetLocalSupportHeight(placement.LocalPosition), placement.LocalPosition.y));
                    worldPosition.y += entry.GroundYOffset;
                    Quaternion worldRotation =
                        mapGenerator.GeneratedContent.rotation *
                        Quaternion.Euler(0f, placement.LocalYawDegrees, 0f);
                    GameObject instance = Instantiate(
                        entry.Prefab,
                        worldPosition,
                        worldRotation,
                        root.transform);
                    instance.name = entry.RuntimeName;

                    if (entry.Kind == RaidSpawnContentKind.Chest)
                    {
                        Chest chest = instance.GetComponent<Chest>();
                        if (chest == null || chest.chestInventoryData == null)
                        {
                            error =
                                $"Instantiated Raid Chest '{entry.StableId}' did not initialize its inventory.";
                            return false;
                        }

                        candidateChests.Add(new RuntimeChestBinding(entry, chest));
                        continue;
                    }

                    EnemyStats stats = instance.GetComponent<EnemyStats>();
                    EnemyAIController ai = instance.GetComponent<EnemyAIController>();
                    Chest[] corpseInventories = instance.GetComponentsInChildren<Chest>(true);
                    if (stats == null || ai == null || !stats.IsInitialized ||
                        corpseInventories.Length != 1 ||
                        corpseInventories[0].chestInventoryData == null)
                    {
                        error =
                            $"Instantiated Raid Enemy '{entry.StableId}' did not initialize its " +
                            "Stats, AI, or corpse inventory.";
                        return false;
                    }

                    ai.BindPatrolPointSource(mapGenerator, requireSource: true);
                    Rigidbody body = stats.GetComponent<Rigidbody>();
                    if (body != null)
                    {
                        body.linearVelocity = Vector3.zero;
                        body.angularVelocity = Vector3.zero;
                    }

                    candidateEnemies.Add(
                        new RuntimeEnemyBinding(entry, stats, corpseInventories[0]));
                }

                Physics.SyncTransforms();
                runtimeSpawnRoot = root;
                runtimeChests.AddRange(candidateChests);
                runtimeEnemies.AddRange(candidateEnemies);
                succeeded = true;
                return true;
            }
            catch (Exception exception)
            {
                error = $"Raid entity instantiation threw an exception: {exception.Message}";
                return false;
            }
            finally
            {
                if (!succeeded)
                {
                    root.SetActive(false);
                    Destroy(root);
                }
            }
        }

        public bool TryInitializeFreshLoot(
            ItemDatabase authoritativeItemDatabase,
            out string error)
        {
            if (authoritativeItemDatabase == null)
            {
                error = "Fresh raid loot requires the persistent Player ItemDatabase.";
                return false;
            }

            if (mapGenerator == null || mapGenerator.CurrentLayout == null ||
                spawnManifest == null || spawnManifest.Seed != mapGenerator.CurrentSeed)
            {
                error = "Fresh raid loot requires the current validated map and spawn manifest.";
                return false;
            }

            if (!TryBuildRuntimeIndexes(out _, out _, out error))
            {
                return false;
            }

            if (freshLootInitialized)
            {
                if (freshLootSeed != mapGenerator.CurrentSeed)
                {
                    error = "Fresh raid loot was already initialized for a different map seed.";
                    return false;
                }

                error = null;
                return true;
            }

            var applications = new List<FreshLootApplication>(
                runtimeChests.Count + runtimeEnemies.Count);
            foreach (RuntimeChestBinding binding in runtimeChests)
            {
                // A LootTable is opt-in. Authored/legacy containers keep the inventory
                // created by Chest.Awake and remain valid checkpoint participants.
                if (binding.Chest.LootTable == null)
                {
                    continue;
                }

                if (!TryPrepareFreshLootForChest(
                        binding.Chest,
                        binding.StableId,
                        mapGenerator.CurrentSeed,
                        authoritativeItemDatabase,
                        out FreshLootApplication application,
                        out error))
                {
                    return false;
                }

                applications.Add(application);
            }

            foreach (RuntimeEnemyBinding binding in runtimeEnemies)
            {
                if (binding.CorpseInventory.LootTable == null)
                {
                    continue;
                }

                if (!TryPrepareFreshLootForChest(
                        binding.CorpseInventory,
                        binding.StableId + "/corpse",
                        mapGenerator.CurrentSeed,
                        authoritativeItemDatabase,
                        out FreshLootApplication application,
                        out error))
                {
                    return false;
                }

                applications.Add(application);
            }

            var applied = new List<FreshLootApplication>(applications.Count);
            for (int index = 0; index < applications.Count; index++)
            {
                FreshLootApplication application = applications[index];
                if (!ReferenceEquals(
                        application.Chest.chestInventoryData,
                        application.Original))
                {
                    RollbackFreshLoot(applied);
                    error =
                        $"Fresh raid loot owner '{application.Chest.name}' changed before apply.";
                    return false;
                }

                if (!application.Chest.TryBindInventory(
                        application.Candidate,
                        out string bindingError))
                {
                    RollbackFreshLoot(applied);
                    error =
                        $"Fresh raid loot owner '{application.Chest.name}' rejected its candidate: " +
                        bindingError;
                    return false;
                }

                applied.Add(application);
            }

            freshLootInitialized = true;
            freshLootSeed = mapGenerator.CurrentSeed;
            error = null;
            return true;
        }

        private static bool TryPrepareFreshLootForChest(
            Chest chest,
            string stableContainerId,
            int mapSeed,
            ItemDatabase authoritativeItemDatabase,
            out FreshLootApplication application,
            out string error)
        {
            application = default;
            if (chest == null || chest.chestInventoryData == null)
            {
                error =
                    $"Fresh raid loot owner '{stableContainerId}' was not initialized by Chest.Awake.";
                return false;
            }

            if (!chest.TryCreateRaidLootInventory(
                    authoritativeItemDatabase,
                    mapSeed,
                    stableContainerId,
                    out StandardStashViewData candidate,
                    out error) ||
                !chest.CanBindInventory(candidate, out error))
            {
                error = $"Fresh raid loot '{stableContainerId}' is invalid: {error}";
                return false;
            }

            application = new FreshLootApplication(
                chest,
                chest.chestInventoryData,
                candidate);
            error = null;
            return true;
        }

        private static void RollbackFreshLoot(IReadOnlyList<FreshLootApplication> applied)
        {
            for (int index = applied.Count - 1; index >= 0; index--)
            {
                FreshLootApplication application = applied[index];
                application.Chest.TryBindInventory(application.Original, out _);
            }
        }

        private bool TryValidateSpawnNavigation(out string error)
        {
            if (spawnManifest == null)
            {
                error = "Raid spawn manifest is missing.";
                return false;
            }

            for (int index = 0; index < spawnManifest.Count; index++)
            {
                UrbanRaidSpawnPlacement placement = spawnManifest.Placements[index];
                if (!mapGenerator.TryValidateReachableLocalPoint(
                        placement.ApproachLocalPosition,
                        $"raid {placement.Kind} '{placement.StableId}'",
                        out error))
                {
                    return false;
                }
            }

            error = null;
            return true;
        }

        public bool TryCaptureWorld(
            ItemDatabase itemDatabase,
            out int generatorVersion,
            out int mapSeed,
            out string layoutHash,
            out List<RaidChestSaveData> chestRecords,
            out List<RaidEnemySaveData> enemyRecords,
            out List<RaidWorldItemSaveData> worldItemRecords,
            out string error)
        {
            generatorVersion = 0;
            mapSeed = 0;
            layoutHash = null;
            chestRecords = null;
            enemyRecords = null;
            worldItemRecords = null;

            RaidSceneArrivalReadiness readiness = GetArrivalReadiness(out error);
            if (readiness != RaidSceneArrivalReadiness.Ready)
            {
                if (readiness == RaidSceneArrivalReadiness.Pending)
                {
                    error = "Raid scene navigation is still being prepared.";
                }

                return false;
            }

            if (!TryBuildRuntimeIndexes(
                    out Dictionary<string, RuntimeChestBinding> chestIndex,
                    out Dictionary<string, RuntimeEnemyBinding> enemyIndex,
                    out error) ||
                mapGenerator.CurrentLayout == null)
            {
                if (error == null)
                {
                    error = "Raid map layout is not ready for checkpoint capture.";
                }
                return false;
            }

            var capturedChests = new List<RaidChestSaveData>(chestIndex.Count);
            foreach (RuntimeChestBinding binding in runtimeChests)
            {
                if (binding.Chest.chestInventoryData == null ||
                    !InventorySaveCodec.TryCaptureGrid(
                        binding.Chest.chestInventoryData,
                        itemDatabase,
                        out InventoryGridSaveData inventory,
                        out error))
                {
                    error = $"Could not capture raid Chest '{binding.StableId}': {error}";
                    return false;
                }

                capturedChests.Add(new RaidChestSaveData
                {
                    stableId = binding.StableId,
                    inventory = inventory
                });
            }

            var capturedEnemies = new List<RaidEnemySaveData>(enemyIndex.Count);
            foreach (RuntimeEnemyBinding binding in runtimeEnemies)
            {
                if (!binding.Stats.IsInitialized ||
                    binding.CorpseInventory.chestInventoryData == null ||
                    !InventorySaveCodec.TryCaptureGrid(
                        binding.CorpseInventory.chestInventoryData,
                        itemDatabase,
                        out InventoryGridSaveData corpseInventory,
                        out error))
                {
                    error = $"Could not capture raid Enemy '{binding.StableId}': {error}";
                    return false;
                }

                capturedEnemies.Add(new RaidEnemySaveData
                {
                    stableId = binding.StableId,
                    transform = CaptureTransform(binding.Stats.transform),
                    currentHealth = binding.Stats.CurrentHealth,
                    maxHealth = binding.Stats.MaxHealth,
                    corpseInventory = corpseInventory
                });
            }

            var sceneWorldItems = new List<WorldItemPickup>();
            if (!WorldItemPickup.TryGetActiveItems(
                    gameObject.scene,
                    sceneWorldItems,
                    out error))
            {
                error = $"Could not enumerate raid world items: {error}";
                return false;
            }

            var capturedWorldItems = new List<RaidWorldItemSaveData>(sceneWorldItems.Count);
            foreach (WorldItemPickup pickup in sceneWorldItems)
            {
                if (!InventorySaveCodec.TryCaptureGrid(
                        pickup.Inventory,
                        itemDatabase,
                        out InventoryGridSaveData inventory,
                        out error))
                {
                    error = $"Could not capture raid world item '{pickup.StableId}': {error}";
                    return false;
                }

                capturedWorldItems.Add(new RaidWorldItemSaveData
                {
                    stableId = pickup.StableId,
                    transform = CaptureTransform(pickup.transform),
                    inventory = inventory
                });
            }

            generatorVersion = mapGenerator.CheckpointGeneratorVersion;
            mapSeed = mapGenerator.CurrentSeed;
            layoutHash = mapGenerator
                .ComputeCheckpointWorldHash(spawnManifest)
                .ToString("X16");
            chestRecords = capturedChests;
            enemyRecords = capturedEnemies;
            worldItemRecords = capturedWorldItems;
            error = null;
            return true;
        }

        public bool TryPrepareRestore(
            RaidCheckpointData checkpoint,
            ItemDatabase itemDatabase,
            out RestorePlan plan,
            out string error)
        {
            plan = null;
            if (checkpoint == null ||
                !string.Equals(checkpoint.sceneStateId, sceneStateId, StringComparison.Ordinal) ||
                !string.Equals(checkpoint.raidScene, SceneName, StringComparison.Ordinal))
            {
                error = "Raid checkpoint targets a different scene state binding.";
                return false;
            }

            RaidSceneArrivalReadiness readiness = GetArrivalReadiness(out error);
            if (readiness != RaidSceneArrivalReadiness.Ready)
            {
                if (readiness == RaidSceneArrivalReadiness.Pending)
                {
                    error = "Recovered raid scene navigation is still being prepared.";
                }

                return false;
            }

            if (!TryBuildRuntimeIndexes(
                    out Dictionary<string, RuntimeChestBinding> authoredChests,
                    out Dictionary<string, RuntimeEnemyBinding> authoredEnemies,
                    out error) ||
                mapGenerator.CurrentLayout == null ||
                mapGenerator.CurrentSeed != checkpoint.mapSeed ||
                mapGenerator.CheckpointGeneratorVersion != checkpoint.generatorVersion)
            {
                if (error == null)
                {
                    error = "Recovered raid map identity does not match the checkpoint.";
                }
                return false;
            }

            string currentHash = mapGenerator
                .ComputeCheckpointWorldHash(spawnManifest)
                .ToString("X16");
            string legacyLayoutHash = UrbanMapLayoutValidator
                .ComputeStableHash(mapGenerator.CurrentLayout)
                .ToString("X16");
            bool matchesCurrentWorld = string.Equals(
                currentHash,
                checkpoint.layoutHash,
                StringComparison.OrdinalIgnoreCase);
            bool matchesLegacyLayout = mapGenerator.IsometricStyle == null && string.Equals(
                legacyLayoutHash,
                checkpoint.layoutHash,
                StringComparison.OrdinalIgnoreCase);
            if (!matchesCurrentWorld && !matchesLegacyLayout)
            {
                error = "Recovered raid map layout/content hash does not match the checkpoint.";
                return false;
            }

            if (matchesLegacyLayout && !matchesCurrentWorld)
            {
                Debug.Log(
                    "Migrating a legacy layout-only raid checkpoint to the current " +
                    "layout-and-spawn-manifest world identity.",
                    this);
            }

            if (!TryIndexSavedChests(checkpoint.chests, out var savedChests, out error) ||
                !TryIndexSavedEnemies(checkpoint.enemies, out var savedEnemies, out error) ||
                savedChests.Count != authoredChests.Count ||
                savedEnemies.Count != authoredEnemies.Count)
            {
                if (error == null)
                {
                    error = "Recovered raid entity count does not match the current scene.";
                }
                return false;
            }

            var existingWorldItems = new List<WorldItemPickup>();
            if (!WorldItemPickup.TryGetActiveItems(
                    gameObject.scene,
                    existingWorldItems,
                    out error) ||
                existingWorldItems.Count != 0)
            {
                if (error == null)
                {
                    error = "Recovered raid scene already contains live world items.";
                }
                return false;
            }

            var candidate = new RestorePlan();
            foreach (RuntimeChestBinding authored in runtimeChests)
            {
                if (!savedChests.TryGetValue(authored.StableId, out RaidChestSaveData saved) ||
                    !InventorySaveCodec.TryRestoreGrid(
                        saved.inventory,
                        itemDatabase,
                        out StandardStashViewData restored,
                        out error) ||
                    !authored.Chest.CanBindInventory(restored, out error))
                {
                    error = $"Could not prepare raid Chest '{authored.StableId}': {error}";
                    return false;
                }

                candidate.Chests.Add(new ChestRestore
                {
                    Chest = authored.Chest,
                    Candidate = restored,
                    Original = authored.Chest.chestInventoryData
                });
            }

            foreach (RuntimeEnemyBinding authored in runtimeEnemies)
            {
                if (!savedEnemies.TryGetValue(authored.StableId, out RaidEnemySaveData saved) ||
                    !authored.Stats.IsInitialized ||
                    !authored.Stats.IsAlive ||
                    !RaidCheckpointValidator.HasValidTransform(saved.transform) ||
                    !authored.Stats.CanRestoreCheckpointHealth(
                        saved.currentHealth,
                        saved.maxHealth,
                        out float normalizedCurrentHealth) ||
                    !InventorySaveCodec.TryRestoreGrid(
                        saved.corpseInventory,
                        itemDatabase,
                        out StandardStashViewData restoredCorpse,
                        out error) ||
                    !authored.CorpseInventory.CanBindInventory(restoredCorpse, out error))
                {
                    error = $"Could not prepare raid Enemy '{authored.StableId}': {error}";
                    return false;
                }

                candidate.Enemies.Add(new EnemyRestore
                {
                    Stats = authored.Stats,
                    CorpseInventory = authored.CorpseInventory,
                    CorpseCandidate = restoredCorpse,
                    OriginalCorpse = authored.CorpseInventory.chestInventoryData,
                    Position = RestorePosition(saved.transform),
                    Rotation = RestoreRotation(saved.transform),
                    OriginalPosition = authored.Stats.transform.position,
                    OriginalRotation = authored.Stats.transform.rotation,
                    CurrentHealth = normalizedCurrentHealth,
                    MaxHealth = authored.Stats.MaxHealth
                });
            }


            if (checkpoint.worldItems != null)
            {
                foreach (RaidWorldItemSaveData saved in checkpoint.worldItems)
                {
                    if (saved == null ||
                        !RaidCheckpointValidator.HasValidTransform(saved.transform) ||
                        !InventorySaveCodec.TryRestoreGrid(
                            saved.inventory,
                            itemDatabase,
                            out StandardStashViewData restoredInventory,
                            out error) ||
                        !WorldItemPickup.TryGetSingleOwnedItem(
                            restoredInventory,
                            out _,
                            out error))
                    {
                        error = $"Could not prepare raid world item '{saved?.stableId}': {error}";
                        return false;
                    }

                    candidate.WorldItems.Add(new WorldItemRestore
                    {
                        StableId = saved.stableId,
                        Inventory = restoredInventory,
                        Position = RestorePosition(saved.transform),
                        Rotation = RestoreRotation(saved.transform)
                    });
                }
            }

            plan = candidate;
            error = null;
            return true;
        }

        public bool TryApplyRestore(RestorePlan plan, out string error)
        {
            if (plan == null)
            {
                error = "Raid scene restore plan is missing.";
                return false;
            }

            var appliedChests = new List<ChestRestore>();
            var appliedEnemies = new List<EnemyRestore>();
            var stagedWorldItems = new List<WorldItemPickup>(plan.WorldItems.Count);
            try
            {
                foreach (WorldItemRestore worldItem in plan.WorldItems)
                {
                    if (!WorldItemDropService.TryCreateRestored(
                            gameObject.scene,
                            worldItem.StableId,
                            worldItem.Inventory,
                            worldItem.Position,
                            worldItem.Rotation,
                            out WorldItemPickup pickup,
                            out error))
                    {
                        DestroyWorldItems(stagedWorldItems);
                        return false;
                    }
                    stagedWorldItems.Add(pickup);
                }

                foreach (ChestRestore chest in plan.Chests)
                {
                    if (!chest.Chest.TryBindInventory(chest.Candidate, out error))
                    {
                        RollbackInventoryBindings(appliedChests, appliedEnemies);
                        DestroyWorldItems(stagedWorldItems);
                        return false;
                    }
                    appliedChests.Add(chest);
                }

                foreach (EnemyRestore enemy in plan.Enemies)
                {
                    if (!enemy.CorpseInventory.TryBindInventory(enemy.CorpseCandidate, out error))
                    {
                        RollbackInventoryBindings(appliedChests, appliedEnemies);
                        DestroyWorldItems(stagedWorldItems);
                        return false;
                    }
                    appliedEnemies.Add(enemy);
                }

                foreach (EnemyRestore enemy in plan.Enemies)
                {
                    enemy.Stats.transform.SetPositionAndRotation(enemy.Position, enemy.Rotation);
                    Rigidbody body = enemy.Stats.GetComponent<Rigidbody>();
                    if (body != null)
                    {
                        body.linearVelocity = Vector3.zero;
                        body.angularVelocity = Vector3.zero;
                    }
                }
                Physics.SyncTransforms();

                foreach (EnemyRestore enemy in plan.Enemies)
                {
                    if (!enemy.Stats.TryRestoreCheckpointHealth(
                            enemy.CurrentHealth,
                            enemy.MaxHealth,
                            out error))
                    {
                        // Health/death is applied only after every fallible inventory binding
                        // and transform operation has succeeded. A prevalidated health restore
                        // cannot fail without an external mutation during this black-screen boundary.
                        RollbackInventoryBindings(appliedChests, appliedEnemies);
                        DestroyWorldItems(stagedWorldItems);
                        return false;
                    }
                }

                foreach (WorldItemPickup pickup in stagedWorldItems)
                {
                    if (!pickup.TryActivate(out error))
                    {
                        RollbackInventoryBindings(appliedChests, appliedEnemies);
                        DestroyWorldItems(stagedWorldItems);
                        return false;
                    }
                }
                Physics.SyncTransforms();

                error = null;
                return true;
            }
            catch (Exception exception)
            {
                RollbackInventoryBindings(appliedChests, appliedEnemies);
                DestroyWorldItems(stagedWorldItems);
                error = $"Raid scene restore threw an exception: {exception.Message}";
                return false;
            }
        }

        private bool TryValidateCatalogConfiguration(out string error)
        {
            if (string.IsNullOrWhiteSpace(sceneStateId) || mapGenerator == null ||
                spawnCatalog == null)
            {
                error = "Scene state ID, map generator, or Raid spawn catalog is missing.";
                return false;
            }

            return spawnCatalog.TryValidate(out error);
        }

        private bool TryBuildRuntimeIndexes(
            out Dictionary<string, RuntimeChestBinding> chestIndex,
            out Dictionary<string, RuntimeEnemyBinding> enemyIndex,
            out string error)
        {
            chestIndex = new Dictionary<string, RuntimeChestBinding>(StringComparer.Ordinal);
            enemyIndex = new Dictionary<string, RuntimeEnemyBinding>(StringComparer.Ordinal);
            var allIds = new HashSet<string>(StringComparer.Ordinal);
            var boundInventories = new HashSet<Chest>();
            var boundEnemies = new HashSet<EnemyStats>();
            var spawnTargets = new HashSet<Transform>();

            if (!TryValidateCatalogConfiguration(out error))
            {
                return false;
            }

            if (runtimeSpawnRoot == null || runtimeSpawnRoot.transform.parent != null ||
                runtimeSpawnRoot.scene != gameObject.scene ||
                runtimeChests.Count + runtimeEnemies.Count != spawnCatalog.Entries.Count)
            {
                error = "The Raid runtime entity root or registry is incomplete.";
                return false;
            }

            foreach (RuntimeChestBinding binding in runtimeChests)
            {
                if (binding == null ||
                    string.IsNullOrWhiteSpace(binding.StableId) ||
                    binding.Definition == null ||
                    binding.Definition.Kind != RaidSpawnContentKind.Chest ||
                    binding.Chest == null ||
                    binding.Chest.chestInventoryData == null ||
                    !binding.Chest.transform.IsChildOf(runtimeSpawnRoot.transform) ||
                    !boundInventories.Add(binding.Chest) ||
                    !spawnTargets.Add(binding.Chest.transform) ||
                    !allIds.Add(binding.StableId))
                {
                    error =
                        "Runtime Chest bindings contain a missing/duplicate owner or spawn target, " +
                        "or duplicate stable ID.";
                    return false;
                }
                chestIndex.Add(binding.StableId, binding);
            }

            foreach (RuntimeEnemyBinding binding in runtimeEnemies)
            {
                if (binding == null ||
                    string.IsNullOrWhiteSpace(binding.StableId) ||
                    binding.Definition == null ||
                    binding.Definition.Kind != RaidSpawnContentKind.Enemy ||
                    binding.Stats == null ||
                    binding.Stats.GetComponent<EnemyAIController>() == null ||
                    !binding.Stats.IsInitialized ||
                    binding.CorpseInventory == null ||
                    binding.CorpseInventory.chestInventoryData == null ||
                    binding.CorpseInventory.GetComponentInParent<EnemyStats>() != binding.Stats ||
                    !binding.Stats.transform.IsChildOf(runtimeSpawnRoot.transform) ||
                    !boundInventories.Add(binding.CorpseInventory) ||
                    !boundEnemies.Add(binding.Stats) ||
                    !spawnTargets.Add(binding.Stats.transform) ||
                    !allIds.Add(binding.StableId))
                {
                    error =
                        "Runtime Enemy bindings contain a missing/duplicate component or spawn target, " +
                        "wrong/duplicate corpse container, or duplicate stable ID.";
                    return false;
                }
                enemyIndex.Add(binding.StableId, binding);
            }

            for (int index = 0; index < spawnCatalog.Entries.Count; index++)
            {
                RaidSpawnCatalogEntry entry = spawnCatalog.Entries[index];
                bool exists = entry.Kind == RaidSpawnContentKind.Chest
                    ? chestIndex.ContainsKey(entry.StableId)
                    : enemyIndex.ContainsKey(entry.StableId);
                if (!exists)
                {
                    error =
                        $"Raid runtime registry is missing catalog entry '{entry.StableId}'.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryIndexSavedChests(
            List<RaidChestSaveData> records,
            out Dictionary<string, RaidChestSaveData> index,
            out string error)
        {
            index = new Dictionary<string, RaidChestSaveData>(StringComparer.Ordinal);
            if (records == null)
            {
                error = "Saved Chest records are missing.";
                return false;
            }

            foreach (RaidChestSaveData record in records)
            {
                if (record == null ||
                    string.IsNullOrWhiteSpace(record.stableId) ||
                    record.inventory == null ||
                    !index.TryAdd(record.stableId, record))
                {
                    error = "Saved Chest records contain an invalid or duplicate stable ID.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryIndexSavedEnemies(
            List<RaidEnemySaveData> records,
            out Dictionary<string, RaidEnemySaveData> index,
            out string error)
        {
            index = new Dictionary<string, RaidEnemySaveData>(StringComparer.Ordinal);
            if (records == null)
            {
                error = "Saved Enemy records are missing.";
                return false;
            }

            foreach (RaidEnemySaveData record in records)
            {
                if (record == null ||
                    string.IsNullOrWhiteSpace(record.stableId) ||
                    record.corpseInventory == null ||
                    !index.TryAdd(record.stableId, record))
                {
                    error = "Saved Enemy records contain an invalid or duplicate stable ID.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static void RollbackInventoryBindings(
            List<ChestRestore> chestsToRollback,
            List<EnemyRestore> enemiesToRollback)
        {
            foreach (ChestRestore chest in chestsToRollback)
            {
                if (chest.Original != null)
                {
                    chest.Chest.TryBindInventory(chest.Original, out _);
                }
            }

            foreach (EnemyRestore enemy in enemiesToRollback)
            {
                if (enemy.OriginalCorpse != null)
                {
                    enemy.CorpseInventory.TryBindInventory(enemy.OriginalCorpse, out _);
                }
                enemy.Stats.transform.SetPositionAndRotation(
                    enemy.OriginalPosition,
                    enemy.OriginalRotation);
            }
            Physics.SyncTransforms();
        }

        private static void DestroyWorldItems(List<WorldItemPickup> pickups)
        {
            foreach (WorldItemPickup pickup in pickups)
            {
                WorldItemDropService.DestroyPickup(pickup);
            }
            pickups.Clear();
        }

        public static RaidTransformSaveData CaptureTransform(Transform source)
        {
            Vector3 position = source.position;
            Quaternion rotation = source.rotation;
            return new RaidTransformSaveData
            {
                positionX = position.x,
                positionY = position.y,
                positionZ = position.z,
                rotationX = rotation.x,
                rotationY = rotation.y,
                rotationZ = rotation.z,
                rotationW = rotation.w
            };
        }

        public static Vector3 RestorePosition(RaidTransformSaveData source)
        {
            return new Vector3(source.positionX, source.positionY, source.positionZ);
        }

        public static Quaternion RestoreRotation(RaidTransformSaveData source)
        {
            return new Quaternion(
                source.rotationX,
                source.rotationY,
                source.rotationZ,
                source.rotationW).normalized;
        }
    }
}
