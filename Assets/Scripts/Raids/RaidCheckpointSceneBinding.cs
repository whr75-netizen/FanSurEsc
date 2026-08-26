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
        [Serializable]
        private sealed class ChestBinding
        {
            [SerializeField] private string stableId;
            [SerializeField] private Chest chest;

            public string StableId => stableId;
            public Chest Chest => chest;
        }

        [Serializable]
        private sealed class EnemyBinding
        {
            [SerializeField] private string stableId;
            [SerializeField] private EnemyStats stats;
            [SerializeField] private Chest corpseInventory;

            public string StableId => stableId;
            public EnemyStats Stats => stats;
            public Chest CorpseInventory => corpseInventory;
        }

        public sealed class RestorePlan
        {
            internal readonly List<ChestRestore> Chests = new List<ChestRestore>();
            internal readonly List<EnemyRestore> Enemies = new List<EnemyRestore>();
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

        private readonly struct SpawnTransformApplication
        {
            public SpawnTransformApplication(
                Transform target,
                Vector3 position,
                Quaternion rotation)
            {
                Target = target;
                Position = position;
                Rotation = rotation;
            }

            public Transform Target { get; }
            public Vector3 Position { get; }
            public Quaternion Rotation { get; }
        }

        [SerializeField] private string sceneStateId = "core:gamemaptest:v1";
        [SerializeField] private ProceduralUrbanMapGenerator mapGenerator;
        [SerializeField] private ChestBinding[] chests = Array.Empty<ChestBinding>();
        [SerializeField] private EnemyBinding[] enemies = Array.Empty<EnemyBinding>();

        private RaidCheckpointController controller;
        private string seedPreparationError;
        private UrbanRaidSpawnManifest spawnManifest;
        private string spawnPreparationError;
        private bool spawnNavigationValidated;
        private string spawnNavigationValidationError;

        public string SceneStateId => sceneStateId;
        public string SceneName => gameObject.scene.name;
        public ProceduralUrbanMapGenerator MapGenerator => mapGenerator;
        public bool IsConfigured => TryBuildAuthoredIndexes(out _, out _, out _);
        public string SeedPreparationError => seedPreparationError;
        public UrbanRaidSpawnManifest SpawnManifest => spawnManifest;

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

            if (!TryBuildAuthoredIndexes(out _, out _, out string configurationError))
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
        }

        private void HandleLayoutGeometryGenerated(UrbanMapLayout layout)
        {
            spawnManifest = null;
            spawnPreparationError = null;
            spawnNavigationValidated = false;
            spawnNavigationValidationError = null;

            try
            {
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

                if (!TryApplyInitialSpawnManifest(candidate, out string applicationError))
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
            requests = new List<UrbanRaidSpawnRequest>(chests.Length + enemies.Length);
            foreach (ChestBinding binding in chests)
            {
                requests.Add(UrbanRaidSpawnPrototypeRules.CreateChestRequest(binding.StableId));
            }

            foreach (EnemyBinding binding in enemies)
            {
                EnemyDefinition definition = binding.Stats.Definition;
                EnemyAISettings ai = definition != null ? definition.AI : null;
                if (ai == null)
                {
                    error = $"Raid Enemy '{binding.StableId}' has no AI definition for spawn safety.";
                    return false;
                }

                requests.Add(UrbanRaidSpawnPrototypeRules.CreateEnemyRequest(
                    binding.StableId,
                    ai.VisionRange,
                    ai.PatrolRadius));
            }

            error = null;
            return true;
        }

        private bool TryApplyInitialSpawnManifest(
            UrbanRaidSpawnManifest candidate,
            out string error)
        {
            if (candidate == null || candidate.Count != chests.Length + enemies.Length)
            {
                error = "Raid spawn manifest entity count does not match the authored checkpoint bindings.";
                return false;
            }

            var applications = new List<SpawnTransformApplication>(candidate.Count);
            foreach (ChestBinding binding in chests)
            {
                if (!TryCreateSpawnApplication(
                        candidate,
                        binding.StableId,
                        UrbanRaidSpawnKind.Chest,
                        binding.Chest.transform,
                        out SpawnTransformApplication application,
                        out error))
                {
                    return false;
                }

                applications.Add(application);
            }

            foreach (EnemyBinding binding in enemies)
            {
                // Layout generation must happen before the normal EnemyStats/AI Awake pass.
                // A mid-raid reroll would invalidate AI home state and Recovery ownership.
                if (binding.Stats.IsInitialized)
                {
                    error =
                        $"Raid Enemy '{binding.StableId}' was already initialized before its " +
                        "deterministic spawn position was assigned.";
                    return false;
                }

                if (!TryCreateSpawnApplication(
                        candidate,
                        binding.StableId,
                        UrbanRaidSpawnKind.Enemy,
                        binding.Stats.transform,
                        out SpawnTransformApplication application,
                        out error))
                {
                    return false;
                }

                applications.Add(application);
            }

            for (int index = 0; index < applications.Count; index++)
            {
                SpawnTransformApplication application = applications[index];
                application.Target.SetPositionAndRotation(application.Position, application.Rotation);
                Rigidbody body = application.Target.GetComponent<Rigidbody>();
                if (body != null)
                {
                    body.linearVelocity = Vector3.zero;
                    body.angularVelocity = Vector3.zero;
                }
            }

            Physics.SyncTransforms();
            error = null;
            return true;
        }

        private bool TryCreateSpawnApplication(
            UrbanRaidSpawnManifest candidate,
            string stableId,
            UrbanRaidSpawnKind expectedKind,
            Transform target,
            out SpawnTransformApplication application,
            out string error)
        {
            application = default;
            if (target == null ||
                !candidate.TryGetPlacement(stableId, out UrbanRaidSpawnPlacement placement) ||
                placement.Kind != expectedKind)
            {
                error = $"Raid spawn manifest is missing the expected {expectedKind} '{stableId}'.";
                return false;
            }

            Vector3 worldPosition = mapGenerator.GeneratedContent.TransformPoint(
                new Vector3(placement.LocalPosition.x, 0f, placement.LocalPosition.y));
            worldPosition.y = target.position.y;
            Quaternion worldRotation =
                mapGenerator.GeneratedContent.rotation * Quaternion.Euler(0f, placement.LocalYawDegrees, 0f);
            application = new SpawnTransformApplication(target, worldPosition, worldRotation);
            error = null;
            return true;
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
            out string error)
        {
            generatorVersion = 0;
            mapSeed = 0;
            layoutHash = null;
            chestRecords = null;
            enemyRecords = null;

            RaidSceneArrivalReadiness readiness = GetArrivalReadiness(out error);
            if (readiness != RaidSceneArrivalReadiness.Ready)
            {
                if (readiness == RaidSceneArrivalReadiness.Pending)
                {
                    error = "Raid scene navigation is still being prepared.";
                }

                return false;
            }

            if (!TryBuildAuthoredIndexes(
                    out Dictionary<string, ChestBinding> chestIndex,
                    out Dictionary<string, EnemyBinding> enemyIndex,
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
            foreach (ChestBinding binding in chests)
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
            foreach (EnemyBinding binding in enemies)
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

            generatorVersion = mapGenerator.CurrentLayout.GeneratorVersion;
            mapSeed = mapGenerator.CurrentSeed;
            layoutHash = UrbanMapLayoutValidator
                .ComputeStableWorldHash(mapGenerator.CurrentLayout, spawnManifest)
                .ToString("X16");
            chestRecords = capturedChests;
            enemyRecords = capturedEnemies;
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

            if (!TryBuildAuthoredIndexes(
                    out Dictionary<string, ChestBinding> authoredChests,
                    out Dictionary<string, EnemyBinding> authoredEnemies,
                    out error) ||
                mapGenerator.CurrentLayout == null ||
                mapGenerator.CurrentSeed != checkpoint.mapSeed ||
                mapGenerator.CurrentLayout.GeneratorVersion != checkpoint.generatorVersion)
            {
                if (error == null)
                {
                    error = "Recovered raid map identity does not match the checkpoint.";
                }
                return false;
            }

            string currentHash = UrbanMapLayoutValidator
                .ComputeStableWorldHash(mapGenerator.CurrentLayout, spawnManifest)
                .ToString("X16");
            string legacyLayoutHash = UrbanMapLayoutValidator
                .ComputeStableHash(mapGenerator.CurrentLayout)
                .ToString("X16");
            bool matchesCurrentWorld = string.Equals(
                currentHash,
                checkpoint.layoutHash,
                StringComparison.OrdinalIgnoreCase);
            bool matchesLegacyLayout = string.Equals(
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

            var candidate = new RestorePlan();
            foreach (ChestBinding authored in chests)
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

            foreach (EnemyBinding authored in enemies)
            {
                if (!savedEnemies.TryGetValue(authored.StableId, out RaidEnemySaveData saved) ||
                    !authored.Stats.IsInitialized ||
                    !authored.Stats.IsAlive ||
                    !RaidCheckpointValidator.HasValidTransform(saved.transform) ||
                    !Mathf.Approximately(saved.maxHealth, authored.Stats.MaxHealth) ||
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
                    CurrentHealth = saved.currentHealth,
                    MaxHealth = saved.maxHealth
                });
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
            try
            {
                foreach (ChestRestore chest in plan.Chests)
                {
                    if (!chest.Chest.TryBindInventory(chest.Candidate, out error))
                    {
                        RollbackInventoryBindings(appliedChests, appliedEnemies);
                        return false;
                    }
                    appliedChests.Add(chest);
                }

                foreach (EnemyRestore enemy in plan.Enemies)
                {
                    if (!enemy.CorpseInventory.TryBindInventory(enemy.CorpseCandidate, out error))
                    {
                        RollbackInventoryBindings(appliedChests, appliedEnemies);
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
                        return false;
                    }
                }

                error = null;
                return true;
            }
            catch (Exception exception)
            {
                error = $"Raid scene restore threw an exception: {exception.Message}";
                return false;
            }
        }

        private bool TryBuildAuthoredIndexes(
            out Dictionary<string, ChestBinding> chestIndex,
            out Dictionary<string, EnemyBinding> enemyIndex,
            out string error)
        {
            chestIndex = new Dictionary<string, ChestBinding>(StringComparer.Ordinal);
            enemyIndex = new Dictionary<string, EnemyBinding>(StringComparer.Ordinal);
            var allIds = new HashSet<string>(StringComparer.Ordinal);
            var boundInventories = new HashSet<Chest>();
            var boundEnemies = new HashSet<EnemyStats>();
            var spawnTargets = new HashSet<Transform>();

            if (string.IsNullOrWhiteSpace(sceneStateId) || mapGenerator == null ||
                chests == null || enemies == null)
            {
                error = "Scene state ID, map generator, or entity bindings are missing.";
                return false;
            }

            foreach (ChestBinding binding in chests)
            {
                if (binding == null ||
                    string.IsNullOrWhiteSpace(binding.StableId) ||
                    binding.Chest == null ||
                    !boundInventories.Add(binding.Chest) ||
                    !spawnTargets.Add(binding.Chest.transform) ||
                    !allIds.Add(binding.StableId))
                {
                    error =
                        "Chest bindings contain a missing/duplicate component or spawn target, " +
                        "or duplicate stable ID.";
                    return false;
                }
                chestIndex.Add(binding.StableId, binding);
            }

            foreach (EnemyBinding binding in enemies)
            {
                if (binding == null ||
                    string.IsNullOrWhiteSpace(binding.StableId) ||
                    binding.Stats == null ||
                    binding.CorpseInventory == null ||
                    binding.CorpseInventory.GetComponentInParent<EnemyStats>() != binding.Stats ||
                    !boundInventories.Add(binding.CorpseInventory) ||
                    !boundEnemies.Add(binding.Stats) ||
                    !spawnTargets.Add(binding.Stats.transform) ||
                    !allIds.Add(binding.StableId))
                {
                    error =
                        "Enemy bindings contain a missing/duplicate component or spawn target, " +
                        "wrong/duplicate corpse container, or duplicate stable ID.";
                    return false;
                }
                enemyIndex.Add(binding.StableId, binding);
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
