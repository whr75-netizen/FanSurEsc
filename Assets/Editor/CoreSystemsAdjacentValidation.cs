using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using FantasySurvival.Actions;
using FantasySurvival.BaseBuilding;
using FantasySurvival.Combat;
using FantasySurvival.Controls;
using FantasySurvival.Inventory;
using FantasySurvival.Raids;
using FantasySurvival.SaveSystem;
using UnityEditor;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;
using VariableInventorySystem;

namespace FantasySurvival.EditorTools
{
    /// <summary>
    /// Fast, Edit Mode contract checks for the systems most often changed together.
    /// This deliberately avoids scene travel and is not a replacement for a release
    /// game-loop pass.
    /// </summary>
    public static class CoreSystemsAdjacentValidation
    {
        private const string MenuPath =
            "Tools/Fantasy Survival/Validation/Run Core Adjacent Contracts";
        private const string ItemDatabasePath = "Assets/GameData/Items/ItemDatabase.asset";
        private const string ShellPrefabPath = "Assets/Prefabs/PersistentGameplayShell.prefab";
        private const string KeyPanelPrefabPath =
            "Assets/Prefabs/UI/KeyBindingSettingsPanel.prefab";

        [MenuItem(MenuPath)]
        public static void Run()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning(
                    "Core adjacent contract validation is Edit Mode only and was not run.");
                return;
            }

            ValidateEquipmentAmmunitionAndTooltip();
            ValidateActionAndDamageNotifications();
            ValidateInputBindingTransactions();
            ValidateSaveArtifactDetection();
            ValidateRaidWorldItemRecoveryPayload();
            ValidatePrefabWiring();
            Debug.Log(
                "Core adjacent contract validation passed: equipment W1-W3, ammunition, " +
                "runtime tooltip, action/damage notifications, key-row transactions, " +
                "3-slot save isolation, raid world-item Recovery, and prefab wiring.");
        }

        [MenuItem(MenuPath, true)]
        private static bool CanRun()
        {
            return !EditorApplication.isPlayingOrWillChangePlaymode;
        }

        private static void ValidateEquipmentAmmunitionAndTooltip()
        {
            ItemDatabase database =
                AssetDatabase.LoadAssetAtPath<ItemDatabase>(ItemDatabasePath);
            Require(database != null, "ItemDatabase asset is missing.");

            ItemDefinition[] weaponDefinitions = { GetItem(database, 1), GetItem(database, 2),
                GetItem(database, 3), GetItem(database, 4) };
            ItemDefinition ammunitionDefinition = GetItem(database, 8);

            var inventory = new StandardStashViewData(8, 9);
            var equipment = new EquipmentLoadoutData();
            var state = new PlayerInventoryState(inventory, equipment);
            var weapons = weaponDefinitions
                .Select(definition => (InventoryItemData)InventoryItemDataFactory.Create(definition))
                .ToArray();

            for (int index = 0; index < EquipmentSlotCatalog.WeaponSlotCount; index++)
            {
                int? insertableIndex = equipment.GetInsertableId(weapons[index]);
                Require(insertableIndex.HasValue, $"Weapon {index + 1} has no insertable slot.");
                EquipmentSlotId expectedSlot = EquipmentSlotCatalog.GetWeaponSlot(index + 1);
                Require(
                    EquipmentSlotCatalog.GetSlotAtIndex(insertableIndex.Value) == expectedSlot,
                    $"Weapon {index + 1} did not choose {expectedSlot}.");
                equipment.InsertInventoryItem(insertableIndex.Value, weapons[index]);
            }

            Require(
                equipment.GetInsertableId(weapons[3]) == null &&
                equipment.GetFirstAvailableSlot(weapons[3].Definition) == EquipmentSlotId.None,
                "A fourth weapon was accepted after W1-W3 were occupied.");

            var ammunition = (InventoryItemData)InventoryItemDataFactory.Create(
                ammunitionDefinition,
                5);
            inventory.InsertInventoryItem(0, ammunition);
            int loadedRounds = Math.Min(2, weapons[0].MagazineCapacity);
            Require(loadedRounds > 0, "Validation weapon has no magazine capacity.");
            Require(
                weapons[0].TryChangeLoadedAmmunition(
                    equipment,
                    0,
                    loadedRounds,
                    out string ammunitionError),
                ammunitionError);
            Require(
                state.TryGetReserveAmmunitionCount(
                    weapons[0],
                    out int reserveCount,
                    out ammunitionError),
                ammunitionError);
            Require(reserveCount == 5, $"Expected 5 reserve rounds but found {reserveCount}.");

            InventoryItemTooltipContent tooltip =
                InventoryItemTooltipFormatter.Create(weapons[0]);
            Require(
                tooltip.Stats.Contains(
                    $"현재 탄창: {loadedRounds} / {weapons[0].MagazineCapacity}"),
                "Runtime weapon tooltip does not expose the loaded magazine state.");
        }

        private static void ValidateActionAndDamageNotifications()
        {
            var player = new GameObject("CoreValidation_Player");
            var source = new GameObject("CoreValidation_ActionSource");
            try
            {
                PlayerStats stats = player.AddComponent<PlayerStats>();
                PlayerActionController actions = player.AddComponent<PlayerActionController>();
                InvokePrivateAwake(actions);

                int resolvedCount = 0;
                PlayerActionResult lastActionResult = default;
                actions.ActionResolved += result =>
                {
                    resolvedCount++;
                    lastActionResult = result;
                };

                bool immediateCallback = false;
                Require(
                    actions.TryBegin(
                        "validation.immediate",
                        source,
                        PlayerActionScope.Self,
                        0f,
                        () => immediateCallback = true),
                    "Immediate validation action was rejected.");
                Require(
                    immediateCallback && resolvedCount == 1 &&
                    lastActionResult.WasCompleted &&
                    lastActionResult.ActionId == "validation.immediate",
                    "Immediate action did not publish one completed result.");

                Require(
                    actions.TryBegin(
                        "validation.cancel",
                        source,
                        PlayerActionScope.External,
                        1f,
                        () => { }),
                    "Cancellable validation action was rejected.");
                Require(
                    actions.CancelActive(PlayerActionCancelReason.Requested),
                    "Cancellable validation action could not be cancelled.");
                Require(
                    resolvedCount == 2 && lastActionResult.WasCancelled &&
                    lastActionResult.CancelReason == PlayerActionCancelReason.Requested,
                    "Cancelled action did not publish one reasoned result.");

                int damageNotificationCount = 0;
                DamageResult observedDamage = default;
                stats.DamageApplied += (_, __, result) =>
                {
                    damageNotificationCount++;
                    observedDamage = result;
                };
                float healthBeforeDamage = stats.CurrentHealth;
                var damageContext = new DamageContext(
                    1f,
                    source,
                    player.transform.position);
                DamageResult returnedDamage = stats.ApplyDamage(damageContext);
                Require(
                    damageNotificationCount == 1 && returnedDamage.WasApplied &&
                    observedDamage.WasApplied &&
                    Mathf.Approximately(
                        observedDamage.CurrentHealth,
                        Mathf.Max(0f, healthBeforeDamage - damageContext.Amount)),
                    "Player damage did not publish the confirmed DamageResult once.");

                stats.DamageApplied += (_, __, result) =>
                {
                    if (result.CausedDeath)
                    {
                        stats.ResetHealth();
                    }
                };
                stats.HealthChanged += (_, __) => stats.ResetHealth();
                int deathNotificationCount = 0;
                stats.Died += (_, __) => deathNotificationCount++;
                DamageResult lethalDamage = stats.ApplyDamage(
                    new DamageContext(200f, source, player.transform.position));
                Require(
                    lethalDamage.CausedDeath && deathNotificationCount == 1 && !stats.IsAlive &&
                    Mathf.Approximately(stats.CurrentHealth, 0f),
                    "A health observer changed or blocked the lethal Player transition.");
                stats.ResetHealth();
                Require(
                    stats.IsAlive && Mathf.Approximately(stats.CurrentHealth, stats.MaxHealth),
                    "Player health could not be reset after damage notification completed.");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(source);
                UnityEngine.Object.DestroyImmediate(player);
            }
        }

        private static void ValidateInputBindingTransactions()
        {
            InputActionMap map = GameInputBindings.GameplayMap;
            Require(map != null, "Gameplay Input Action Map is missing.");

            string originalOverrides = map.SaveBindingOverridesAsJson();
            bool mapWasEnabled = map.enabled;
            string temporaryRoot = Path.Combine(
                Path.GetTempPath(),
                "FantasySurvival_InputValidation_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temporaryRoot);

            try
            {
                if (map.enabled)
                {
                    map.Disable();
                }
                map.RemoveAllBindingOverrides();

                Require(
                    GameUserSettings.SetEditorStorageRootForTests(
                        temporaryRoot,
                        false,
                        out string error),
                    error);
                Require(
                    GameUserSettings.TryClearSecondaryInputBinding(
                        GameInputActionId.MoveUp,
                        out error),
                    error);
                Require(
                    string.IsNullOrEmpty(GameInputBindings.GetEffectivePath(
                        GameInputActionId.MoveUp,
                        GameInputBindingSlot.Secondary)) &&
                    GameInputBindings.HasBindingOverride(
                        GameInputActionId.MoveUp,
                        GameInputBindingSlot.Secondary),
                    "Secondary binding clear did not persist an explicit empty override.");

                Require(
                    GameUserSettings.TryResetInputBindings(
                        GameInputActionId.MoveUp,
                        out error),
                    error);
                Require(
                    !GameInputBindings.HasBindingOverride(
                        GameInputActionId.MoveUp,
                        GameInputBindingSlot.Primary) &&
                    !GameInputBindings.HasBindingOverride(
                        GameInputActionId.MoveUp,
                        GameInputBindingSlot.Secondary),
                    "Per-row reset left an override on MoveUp.");
            }
            finally
            {
                GameUserSettings.ClearEditorStorageRootForTests();
                if (map.enabled)
                {
                    map.Disable();
                }
                map.RemoveAllBindingOverrides();
                if (!string.IsNullOrWhiteSpace(originalOverrides))
                {
                    map.LoadBindingOverridesFromJson(originalOverrides, false);
                }
                if (mapWasEnabled)
                {
                    map.Enable();
                }
                DeleteTemporaryDirectory(temporaryRoot);
            }
        }

        private static void ValidateSaveArtifactDetection()
        {
            string temporaryRoot = Path.Combine(
                Path.GetTempPath(),
                "FantasySurvival_SaveValidation_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temporaryRoot);
            try
            {
                Require(
                    GameSaveManager.SetEditorStorageRootForTests(
                        temporaryRoot,
                        out string error),
                    error);
                Require(
                    RaidCheckpointStore.SetEditorStorageRootForTests(
                        temporaryRoot,
                        out error),
                    error);
                Require(!GameSaveManager.HasSlotOneArtifacts, "Empty test root reports a save.");

                string slotOnePath = GameSaveManager.GetSlotPath(1);
                string slotTwoPath = GameSaveManager.GetSlotPath(2);
                string slotThreePath = GameSaveManager.GetSlotPath(3);
                Require(
                    slotOnePath == GameSaveManager.SlotOnePath &&
                    slotOnePath != slotTwoPath && slotTwoPath != slotThreePath,
                    "Save-slot paths are not isolated or slot 1 lost its legacy path.");

                string primaryPath = slotOnePath;
                Directory.CreateDirectory(Path.GetDirectoryName(primaryPath));
                File.WriteAllText(primaryPath, "validation");
                Require(GameSaveManager.HasSlotOneArtifacts, "Primary save was not detected.");
                Require(
                    !GameSaveManager.HasSlotArtifacts(2) &&
                    !GameSaveManager.HasSlotArtifacts(3),
                    "A slot 1 artifact leaked into another ordinary slot.");

                File.Delete(primaryPath);
                File.WriteAllText(primaryPath + ".bak", "validation");
                Require(GameSaveManager.HasSlotOneArtifacts, "Backup save was not detected.");

                Directory.CreateDirectory(Path.GetDirectoryName(slotTwoPath));
                File.WriteAllText(slotTwoPath, "validation");
                Require(
                    GameSaveManager.HasSlotArtifacts(2) &&
                    !GameSaveManager.HasSlotArtifacts(3),
                    "Slot 2 ordinary artifact detection is not isolated.");

                string slotTwoRecovery = RaidCheckpointStore.GetBaselinePath(2);
                Directory.CreateDirectory(Path.GetDirectoryName(slotTwoRecovery));
                File.WriteAllText(slotTwoRecovery, "validation");
                Require(
                    RaidCheckpointStore.HasRecoveryArtifactsForSlot(2) &&
                    !RaidCheckpointStore.HasRecoveryArtifactsForSlot(1) &&
                    !RaidCheckpointStore.HasRecoveryArtifactsForSlot(3),
                    "Raid Recovery artifacts leaked across save slots.");

                File.Delete(slotOnePath + ".bak");
                File.Delete(slotTwoPath);
                ItemDatabase itemDatabase =
                    AssetDatabase.LoadAssetAtPath<ItemDatabase>(ItemDatabasePath);
                BaseFurnitureDatabase furnitureDatabase =
                    AssetDatabase.LoadAssetAtPath<BaseFurnitureDatabase>(
                        "Assets/GameData/BaseFurniture/BaseFurnitureDatabase.asset");
                Require(itemDatabase != null && furnitureDatabase != null,
                    "Save-slot validation databases are missing.");

                for (int slotIndex = 1; slotIndex <= GameSaveManager.SlotCount; slotIndex++)
                {
                    GameSaveData save = GameSaveManager.CreateSave(
                        new PlayerItemStateSaveData
                        {
                            layoutId = PlayerItemStateSaveData.FlatLayoutId,
                            inventoryWidth = 8,
                            inventoryHeight = 9,
                            itemRecordCount = 0
                        },
                        new PlayerCurrencySaveData
                        {
                            formatVersion = PlayerCurrencySaveData.CurrentFormatVersion,
                            gold = slotIndex,
                            silver = slotIndex * 10
                        },
                        PlayerProgressSaveCodec.CreateEmptySaveData(true),
                        BaseFurnitureSaveCodec.CreateEmptySaveData(true),
                        BaseMerchantSaveCodec.CreateEmptySaveData(true));
                    Require(
                        GameSaveManager.TryWriteSlotMirrored(
                            slotIndex,
                            save,
                            itemDatabase,
                            furnitureDatabase,
                            8,
                            9,
                            out error),
                        error);
                }

                for (int slotIndex = 1; slotIndex <= GameSaveManager.SlotCount; slotIndex++)
                {
                    GameSaveManager.ReadSlotCandidates(
                        slotIndex,
                        out GameSaveData primary,
                        out string primaryError,
                        out GameSaveData backup,
                        out string backupError);
                    Require(primary != null && backup != null,
                        $"Slot {slotIndex} did not produce primary+backup: " +
                        $"{primaryError} {backupError}");
                    Require(
                        primary.playerCurrency.gold == slotIndex &&
                        backup.playerCurrency.gold == slotIndex,
                        $"Slot {slotIndex} read data from another slot.");
                }
            }
            finally
            {
                RaidCheckpointStore.ClearEditorStorageRootForTests();
                GameSaveManager.ClearEditorStorageRootForTests();
                DeleteTemporaryDirectory(temporaryRoot);
            }
        }

        private static void ValidateRaidWorldItemRecoveryPayload()
        {
            ItemDatabase itemDatabase =
                AssetDatabase.LoadAssetAtPath<ItemDatabase>(ItemDatabasePath);
            BaseFurnitureDatabase furnitureDatabase =
                AssetDatabase.LoadAssetAtPath<BaseFurnitureDatabase>(
                    "Assets/GameData/BaseFurniture/BaseFurnitureDatabase.asset");
            Require(itemDatabase != null && furnitureDatabase != null,
                "Raid world-item validation databases are missing.");

            ItemDefinition definition = GetItem(itemDatabase, 8);
            var item = (InventoryItemData)InventoryItemDataFactory.Create(definition, 5);
            int width = item.IsRotate ? item.Height : item.Width;
            int height = item.IsRotate ? item.Width : item.Height;
            var worldOwner = new StandardStashViewData(width, height);
            int? slot = worldOwner.GetInsertableId(item);
            Require(slot.HasValue, "Validation world item has no insertable root slot.");
            worldOwner.InsertInventoryItem(slot.Value, item);
            Require(
                InventorySaveCodec.TryCaptureGrid(
                    worldOwner,
                    itemDatabase,
                    out InventoryGridSaveData itemGrid,
                    out string error),
                error);

            GameSaveData persistentState = GameSaveManager.CreateSave(
                new PlayerItemStateSaveData
                {
                    layoutId = PlayerItemStateSaveData.FlatLayoutId,
                    inventoryWidth = 8,
                    inventoryHeight = 9,
                    itemRecordCount = 0
                },
                new PlayerCurrencySaveData
                {
                    formatVersion = PlayerCurrencySaveData.CurrentFormatVersion
                },
                PlayerProgressSaveCodec.CreateEmptySaveData(true),
                BaseFurnitureSaveCodec.CreateEmptySaveData(true),
                BaseMerchantSaveCodec.CreateEmptySaveData(true));
            string raidId = Guid.NewGuid().ToString("D");
            var baseline = new RaidRecoveryBaselineData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = RaidRecoveryBaselineData.CurrentFormatVersion,
                raidInstanceId = raidId,
                createdAtUtc = DateTime.UtcNow.ToString("O"),
                raidScene = "GameMapTest",
                raidSpawnId = "RaidEntry",
                sceneStateId = "core:gamemaptest:v1",
                startingState = persistentState
            };
            var checkpoint = new RaidCheckpointData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = RaidCheckpointData.CurrentFormatVersion,
                worldStateVersion = RaidCheckpointData.CurrentWorldStateVersion,
                raidInstanceId = raidId,
                sequence = 1,
                savedAtUtc = DateTime.UtcNow.ToString("O"),
                phase = RaidCheckpointPhase.Active,
                outcome = RaidOutcome.None,
                raidScene = baseline.raidScene,
                raidSpawnId = baseline.raidSpawnId,
                sceneStateId = baseline.sceneStateId,
                generatorVersion = 1,
                mapSeed = 123,
                layoutHash = "0000000000000001",
                playerTransform = new RaidTransformSaveData { rotationW = 1f },
                playerCurrentHealth = 100f,
                playerMaxHealth = 100f,
                persistentState = persistentState,
                chestRecordCount = 0,
                chests = new List<RaidChestSaveData>(),
                enemyRecordCount = 0,
                enemies = new List<RaidEnemySaveData>(),
                worldItemRecordCount = 1,
                worldItems = new List<RaidWorldItemSaveData>
                {
                    new RaidWorldItemSaveData
                    {
                        stableId = Guid.NewGuid().ToString("D"),
                        transform = new RaidTransformSaveData
                        {
                            positionX = 2f,
                            positionY = 0.16f,
                            positionZ = -3f,
                            rotationW = 1f
                        },
                        inventory = itemGrid
                    }
                }
            };

            Require(
                RaidCheckpointValidator.TryValidateCheckpointForLoad(
                    baseline,
                    checkpoint,
                    itemDatabase,
                    furnitureDatabase,
                    8,
                    9,
                    out error),
                error);

            checkpoint.worldItemRecordCount = 0;
            Require(
                !RaidCheckpointValidator.TryValidateCheckpointStructure(
                    baseline,
                    checkpoint,
                    out _),
                "A mismatched raid world-item count was accepted.");

            checkpoint.worldStateVersion = RaidCheckpointData.LegacyWorldStateVersion;
            checkpoint.worldItems = null;
            Require(
                RaidCheckpointValidator.TryValidateCheckpointForLoad(
                    baseline,
                    checkpoint,
                    itemDatabase,
                    furnitureDatabase,
                    8,
                    9,
                    out error),
                $"Legacy world-state v1 compatibility failed: {error}");
        }

        private static void ValidatePrefabWiring()
        {
            GameObject shell = AssetDatabase.LoadAssetAtPath<GameObject>(ShellPrefabPath);
            Require(shell != null, "PersistentGameplayShell prefab is missing.");
            EquipmentPanelView equipmentPanel =
                shell.GetComponentInChildren<EquipmentPanelView>(true);
            Require(equipmentPanel != null, "Equipment panel is missing.");
            Require(
                equipmentPanel.TryValidateCells(out string error),
                error);

            EquipmentSlotCell[] cells =
                equipmentPanel.GetComponentsInChildren<EquipmentSlotCell>(true);
            Require(
                cells.Single(cell => cell.SlotId == EquipmentSlotId.Weapon2)
                    .gameObject.activeSelf &&
                cells.Single(cell => cell.SlotId == EquipmentSlotId.Weapon3)
                    .gameObject.activeSelf,
                "W2 or W3 is inactive in the persistent shell prefab.");

            GameObject keyPanel = AssetDatabase.LoadAssetAtPath<GameObject>(KeyPanelPrefabPath);
            KeyBindingRowView row =
                keyPanel != null ? keyPanel.GetComponentInChildren<KeyBindingRowView>(true) : null;
            Require(row != null && row.IsConfigured, "Key binding row template is incomplete.");
            SerializedObject serializedRow = new SerializedObject(row);
            Require(
                serializedRow.FindProperty("clearSecondaryButton").objectReferenceValue is Button &&
                serializedRow.FindProperty("resetRowButton").objectReferenceValue is Button,
                "Key binding row utility buttons are not wired.");
        }

        private static ItemDefinition GetItem(ItemDatabase database, int id)
        {
            Require(database.TryGet(id, out ItemDefinition definition),
                $"Item definition ID {id} is missing.");
            return definition;
        }

        private static void InvokePrivateAwake(PlayerActionController controller)
        {
            MethodInfo awake = typeof(PlayerActionController).GetMethod(
                "Awake",
                BindingFlags.Instance | BindingFlags.NonPublic);
            Require(awake != null, "PlayerActionController.Awake was not found.");
            awake.Invoke(controller, null);
        }

        private static void DeleteTemporaryDirectory(string path)
        {
            if (Directory.Exists(path))
            {
                Directory.Delete(path, true);
            }
        }

        private static void Require(bool condition, string message)
        {
            if (!condition)
            {
                throw new InvalidOperationException(message);
            }
        }
    }
}
