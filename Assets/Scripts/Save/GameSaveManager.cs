using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using FantasySurvival.BaseBuilding;
using FantasySurvival.Inventory;
using UnityEngine;

namespace FantasySurvival.SaveSystem
{
    public static class GameSaveManager
    {
        private const int MaxSaveBytes = 2 * 1024 * 1024;
        private const string SaveFolderName = "Saves";
        private const string SlotOneFileName = "save_slot_1.json";

#if UNITY_EDITOR
        private static string editorStorageRootOverride;
#endif

        public static string SlotOnePath => Path.Combine(
            StorageRoot,
            SaveFolderName,
            SlotOneFileName);

        private static string SlotOneBackupPath => SlotOnePath + ".bak";

        private static string StorageRoot
        {
            get
            {
#if UNITY_EDITOR
                if (!string.IsNullOrWhiteSpace(editorStorageRootOverride))
                {
                    return editorStorageRootOverride;
                }
#endif
                return Application.persistentDataPath;
            }
        }

        public static bool TryClonePreservingMigrationContext(
            GameSaveData source,
            out GameSaveData clone,
            out string error)
        {
            clone = null;
            if (source == null)
            {
                error = "Game-save clone source is missing.";
                return false;
            }

            try
            {
                clone = JsonUtility.FromJson<GameSaveData>(JsonUtility.ToJson(source));
            }
            catch (Exception exception)
            {
                error = $"Could not clone game-save state: {exception.Message}";
                return false;
            }

            if (clone == null)
            {
                error = "Could not clone game-save state.";
                return false;
            }

            CopyRuntimeMigrationContext(source, clone);
            error = null;
            return true;
        }

        public static void CopyRuntimeMigrationContext(GameSaveData source, GameSaveData target)
        {
            if (source?.baseState != null && target?.baseState != null)
            {
                target.baseState.allowAuthoredFurnitureInitialization =
                    source.baseState.allowAuthoredFurnitureInitialization;
            }

            if (source?.baseMerchantState != null && target?.baseMerchantState != null)
            {
                target.baseMerchantState.allowAuthoredMerchantInitialization =
                    source.baseMerchantState.allowAuthoredMerchantInitialization;
            }
        }

        public static GameSaveData CreateSave(
            PlayerItemStateSaveData playerItems,
            PlayerCurrencySaveData playerCurrency,
            BaseSaveData baseState,
            BaseMerchantStateSaveData baseMerchantState)
        {
            return new GameSaveData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = GameSaveData.CurrentFormatVersion,
                savedAtUtc = DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture),
                raidInProgress = false,
                activeRaidInstanceId = null,
                playerItems = playerItems,
                playerCurrency = playerCurrency,
                playerInventory = null,
                baseState = baseState,
                baseMerchantState = baseMerchantState
            };
        }

        public static bool TryWriteSlotOne(
            GameSaveData saveData,
            ItemDatabase database,
            BaseFurnitureDatabase furnitureDatabase,
            int expectedInventoryWidth,
            int expectedInventoryHeight,
            out string error)
        {
            if (!TryValidateCompletePayload(
                    saveData,
                    database,
                    furnitureDatabase,
                    expectedInventoryWidth,
                    expectedInventoryHeight,
                    out error))
            {
                return false;
            }

            bool rotatePrimaryToBackup = false;
            if (TryReadFile(SlotOnePath, out GameSaveData existingPrimary, out _) &&
                TryValidateExistingPrimaryForBackup(
                    existingPrimary,
                    saveData,
                    database,
                    furnitureDatabase,
                    expectedInventoryWidth,
                    expectedInventoryHeight))
            {
                rotatePrimaryToBackup = true;
            }

            return TryWriteFile(saveData, SlotOnePath, rotatePrimaryToBackup, out error);
        }

        public static bool TryWriteSlotOneMirrored(
            GameSaveData saveData,
            ItemDatabase database,
            BaseFurnitureDatabase furnitureDatabase,
            int expectedInventoryWidth,
            int expectedInventoryHeight,
            out string error)
        {
            for (int copy = 0; copy < 2; copy++)
            {
                if (!TryWriteSlotOne(
                        saveData,
                        database,
                        furnitureDatabase,
                        expectedInventoryWidth,
                        expectedInventoryHeight,
                        out error))
                {
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryValidateCompletePayload(
            GameSaveData saveData,
            ItemDatabase database,
            BaseFurnitureDatabase furnitureDatabase,
            int expectedInventoryWidth,
            int expectedInventoryHeight,
            out string error)
        {
            if (!TryValidateHeader(saveData, out error))
            {
                return false;
            }

            if (!InventorySaveCodec.TryRestore(
                    saveData.playerItems,
                    database,
                    expectedInventoryWidth,
                    expectedInventoryHeight,
                    out _,
                    out error))
            {
                error = $"Save payload validation failed: {error}";
                return false;
            }

            if (!PlayerCurrencySaveCodec.TryRestore(
                    saveData.playerCurrency,
                    out _,
                    out error))
            {
                error = $"Player currency validation failed: {error}";
                return false;
            }

            if (!BaseFurnitureSaveCodec.TryRestore(
                    saveData.baseState,
                    database,
                    furnitureDatabase,
                    out _,
                    out error))
            {
                error = $"Base payload validation failed: {error}";
                return false;
            }

            if (!BaseMerchantSaveCodec.TryRestore(
                    saveData.baseMerchantState,
                    database,
                    out _,
                    out error))
            {
                error = $"Base merchant payload validation failed: {error}";
                return false;
            }

            error = null;
            return true;
        }

        private static bool TryValidateExistingPrimaryForBackup(
            GameSaveData existingPrimary,
            GameSaveData currentSave,
            ItemDatabase database,
            BaseFurnitureDatabase furnitureDatabase,
            int expectedInventoryWidth,
            int expectedInventoryHeight)
        {
            try
            {
                return TryValidateCompletePayload(
                           existingPrimary,
                           database,
                           furnitureDatabase,
                           expectedInventoryWidth,
                           expectedInventoryHeight,
                           out _) &&
                       HasCompatibleBaseLayoutForBackup(
                           existingPrimary.baseState,
                           currentSave?.baseState) &&
                       HasCompatibleMerchantLayoutForBackup(
                           existingPrimary.baseMerchantState,
                           currentSave?.baseMerchantState);
            }
            catch (Exception)
            {
                // An unexpected problem in untrusted on-disk data must never promote that
                // primary over the only known recovery copy or block a valid new save.
                return false;
            }
        }

        private static bool HasCompatibleBaseLayoutForBackup(
            BaseSaveData existing,
            BaseSaveData current)
        {
            if (existing == null || current == null)
            {
                return false;
            }

            // A successfully normalized v2/v3 file is still loadable because its first
            // current-version load is explicitly allowed to initialize the authored layout.
            if (existing.allowAuthoredFurnitureInitialization)
            {
                return true;
            }

            if (existing.furniture == null || current.furniture == null ||
                existing.furnitureRecordCount != current.furnitureRecordCount ||
                existing.furniture.Count != current.furniture.Count)
            {
                return false;
            }

            var currentDefinitionsByInstance =
                new System.Collections.Generic.Dictionary<string, string>(StringComparer.Ordinal);
            foreach (BaseFurnitureSaveData record in current.furniture)
            {
                if (record == null || string.IsNullOrEmpty(record.instanceId) ||
                    currentDefinitionsByInstance.ContainsKey(record.instanceId))
                {
                    return false;
                }

                currentDefinitionsByInstance.Add(record.instanceId, record.definitionKey);
            }

            foreach (BaseFurnitureSaveData record in existing.furniture)
            {
                if (record == null ||
                    !currentDefinitionsByInstance.TryGetValue(
                        record.instanceId,
                        out string currentDefinition) ||
                    !string.Equals(record.definitionKey, currentDefinition, StringComparison.Ordinal))
                {
                    return false;
                }
            }

            return true;
        }

        private static bool HasCompatibleMerchantLayoutForBackup(
            BaseMerchantStateSaveData existing,
            BaseMerchantStateSaveData current)
        {
            if (existing == null || current == null)
            {
                return false;
            }

            if (existing.allowAuthoredMerchantInitialization)
            {
                return true;
            }

            if (existing.merchants == null || current.merchants == null ||
                existing.merchantRecordCount != current.merchantRecordCount ||
                existing.merchants.Count != current.merchants.Count)
            {
                return false;
            }

            var currentDimensionsById =
                new System.Collections.Generic.Dictionary<string, Vector2Int>(StringComparer.Ordinal);
            foreach (BaseMerchantSaveData record in current.merchants)
            {
                if (record == null || string.IsNullOrWhiteSpace(record.merchantId) ||
                    record.stock == null || currentDimensionsById.ContainsKey(record.merchantId))
                {
                    return false;
                }

                currentDimensionsById.Add(
                    record.merchantId,
                    new Vector2Int(record.stock.width, record.stock.height));
            }

            foreach (BaseMerchantSaveData record in existing.merchants)
            {
                if (record == null || record.stock == null ||
                    !currentDimensionsById.TryGetValue(record.merchantId, out Vector2Int dimensions) ||
                    dimensions.x != record.stock.width || dimensions.y != record.stock.height)
                {
                    return false;
                }
            }

            return true;
        }

        private static bool TryWriteFile(
            GameSaveData saveData,
            string finalPath,
            bool rotatePrimaryToBackup,
            out string error)
        {
            string json;
            try
            {
                json = JsonUtility.ToJson(saveData, true);
            }
            catch (Exception exception)
            {
                error = $"Could not serialize save data: {exception.Message}";
                return false;
            }

            int byteCount = Encoding.UTF8.GetByteCount(json);
            if (byteCount <= 0 || byteCount > MaxSaveBytes)
            {
                error = $"Save data size {byteCount} bytes is invalid.";
                return false;
            }

            string directory = Path.GetDirectoryName(finalPath);
            string temporaryPath = finalPath + ".tmp";
            string backupPath = finalPath + ".bak";
            try
            {
                Directory.CreateDirectory(directory);
                using (var stream = new FileStream(
                           temporaryPath,
                           FileMode.Create,
                           FileAccess.Write,
                           FileShare.None))
                using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
                {
                    writer.Write(json);
                    writer.Flush();
                    // Recovery is removed only after this method returns success. Force the
                    // complete save payload through the OS cache before the atomic replace so
                    // the ordinary slot is a genuinely durable settlement boundary.
                    stream.Flush(true);
                }

                if (File.Exists(finalPath))
                {
                    // Never replace the only known recovery copy with an invalid or
                    // layout-incompatible primary. File.Replace with no backup keeps the
                    // existing .bak untouched while atomically installing the new primary.
                    File.Replace(
                        temporaryPath,
                        finalPath,
                        rotatePrimaryToBackup ? backupPath : null,
                        true);
                }
                else
                {
                    File.Move(temporaryPath, finalPath);
                }

                error = null;
                return true;
            }
            catch (Exception exception)
            {
                error = $"Could not write save slot 1: {exception.Message}";
                return false;
            }
            finally
            {
                try
                {
                    if (File.Exists(temporaryPath))
                    {
                        File.Delete(temporaryPath);
                    }
                }
                catch
                {
                    // A stale temp file is harmless and can be replaced by the next save.
                }
            }
        }

        public static void ReadSlotOneCandidates(
            out GameSaveData primary,
            out string primaryError,
            out GameSaveData backup,
            out string backupError)
        {
            TryReadFile(SlotOnePath, out primary, out primaryError);
            TryReadFile(SlotOneBackupPath, out backup, out backupError);
        }

        public static string GetDisplayTimestamp(GameSaveData saveData)
        {
            if (saveData != null && DateTime.TryParse(
                    saveData.savedAtUtc,
                    CultureInfo.InvariantCulture,
                    DateTimeStyles.RoundtripKind,
                    out DateTime utcTime))
            {
                return utcTime.ToLocalTime().ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.CurrentCulture);
            }

            return "Unknown time";
        }

        private static bool TryReadFile(string path, out GameSaveData saveData, out string error)
        {
            saveData = null;

            if (!File.Exists(path))
            {
                error = "File does not exist.";
                return false;
            }

            try
            {
                var fileInfo = new FileInfo(path);
                if (fileInfo.Length <= 0 || fileInfo.Length > MaxSaveBytes)
                {
                    error = $"File size {fileInfo.Length} bytes is invalid.";
                    return false;
                }

                string json = File.ReadAllText(path, Encoding.UTF8);
                saveData = JsonUtility.FromJson<GameSaveData>(json);
                if (!TryNormalizeToCurrentVersion(saveData, out error))
                {
                    saveData = null;
                    return false;
                }
                if (!TryValidateHeader(saveData, out error))
                {
                    saveData = null;
                    return false;
                }

                return true;
            }
            catch (Exception exception)
            {
                saveData = null;
                error = $"Could not read save file: {exception.Message}";
                return false;
            }
        }

        private static bool TryValidateHeader(GameSaveData saveData, out string error)
        {
            if (saveData == null)
            {
                error = "Save data is empty or malformed.";
                return false;
            }

            if (saveData.gameId != GameSaveData.CurrentGameId)
            {
                error = "Save data belongs to a different game or is missing its game ID.";
                return false;
            }

            if (saveData.formatVersion != GameSaveData.CurrentFormatVersion)
            {
                error = $"Unsupported save version {saveData.formatVersion}.";
                return false;
            }

            if (string.IsNullOrWhiteSpace(saveData.savedAtUtc) ||
                saveData.playerItems == null ||
                saveData.playerCurrency == null ||
                saveData.baseMerchantState == null)
            {
                error = "Save data is missing required fields.";
                return false;
            }

            bool validRaidMarker = saveData.raidInProgress
                ? Guid.TryParse(saveData.activeRaidInstanceId, out _)
                : string.IsNullOrEmpty(saveData.activeRaidInstanceId);
            if (!validRaidMarker)
            {
                error = "Save data has an inconsistent active-raid marker.";
                return false;
            }

            if (!DateTime.TryParse(
                    saveData.savedAtUtc,
                    CultureInfo.InvariantCulture,
                    DateTimeStyles.RoundtripKind,
                    out _))
            {
                error = "Save data has an invalid UTC timestamp.";
                return false;
            }

            if (saveData.baseState == null ||
                saveData.baseState.formatVersion != BaseSaveData.CurrentFormatVersion)
            {
                error = "Save data has an unsupported base-state version.";
                return false;
            }

            error = null;
            return true;
        }

        public static bool TryNormalizeToCurrentVersion(GameSaveData saveData, out string error)
        {
            if (saveData == null)
            {
                error = "Save data is empty or malformed.";
                return false;
            }

            if (saveData.formatVersion == GameSaveData.CurrentFormatVersion)
            {
                error = null;
                return true;
            }

            if (saveData.formatVersion == 4)
            {
                ApplyVersionFiveDefaults(saveData);
            }
            else if (saveData.formatVersion == 2)
            {
                InventoryGridSaveData legacy = saveData.playerInventory;
                if (legacy == null || legacy.layoutId != InventoryGridSaveData.FlatLayoutId ||
                    legacy.width <= 0 || legacy.height <= 0 || legacy.items == null ||
                    legacy.itemRecordCount < 0 || legacy.itemRecordCount != legacy.items.Count)
                {
                    error = "Legacy v2 inventory payload is missing or malformed.";
                    return false;
                }

                foreach (InventoryItemSaveData record in legacy.items)
                {
                    if (record == null)
                    {
                        error = "Legacy v2 inventory contains an empty item record.";
                        return false;
                    }

                    // v2 had no equipment roots. Never infer equipment from a legacy file.
                    record.equipmentSlot = 0;
                }

                saveData.playerItems = new PlayerItemStateSaveData
                {
                    layoutId = PlayerItemStateSaveData.FlatLayoutId,
                    inventoryWidth = legacy.width,
                    inventoryHeight = legacy.height,
                    itemRecordCount = legacy.itemRecordCount,
                    items = legacy.items
                };
                saveData.playerInventory = null;
                saveData.raidInProgress = false;
                saveData.activeRaidInstanceId = null;
                saveData.baseState = BaseFurnitureSaveCodec.CreateEmptySaveData(true);
                ApplyVersionFiveDefaults(saveData);
            }
            else if (saveData.formatVersion == 3)
            {
                if (saveData.baseState != null && saveData.baseState.formatVersion != 1)
                {
                    error = $"Legacy v3 base-state version {saveData.baseState.formatVersion} is unsupported.";
                    return false;
                }

                saveData.baseState = BaseFurnitureSaveCodec.CreateEmptySaveData(true);
                saveData.raidInProgress = false;
                saveData.activeRaidInstanceId = null;
                ApplyVersionFiveDefaults(saveData);
            }

            if (saveData.formatVersion == 5)
            {
                ApplyVersionSixDefaults(saveData);
            }

            if (saveData.formatVersion != GameSaveData.CurrentFormatVersion)
            {
                error = $"Unsupported save version {saveData.formatVersion}.";
                return false;
            }

            error = null;
            return true;
        }

        private static void ApplyVersionFiveDefaults(GameSaveData saveData)
        {
            saveData.playerCurrency = PlayerCurrencySaveCodec.CreateStartingSaveData();
            saveData.baseMerchantState = BaseMerchantSaveCodec.CreateEmptySaveData(true);
            saveData.formatVersion = 5;
        }

        private static void ApplyVersionSixDefaults(GameSaveData saveData)
        {
            ClearLegacyLoadedAmmunition(saveData.playerItems?.items);
            ClearLegacyLoadedAmmunition(saveData.playerInventory?.items);

            if (saveData.baseState?.furniture != null)
            {
                foreach (BaseFurnitureSaveData furniture in saveData.baseState.furniture)
                {
                    ClearLegacyLoadedAmmunition(furniture?.storage?.items);
                }
            }

            if (saveData.baseMerchantState?.merchants != null)
            {
                foreach (BaseMerchantSaveData merchant in saveData.baseMerchantState.merchants)
                {
                    ClearLegacyLoadedAmmunition(merchant?.stock?.items);
                }
            }

            saveData.formatVersion = GameSaveData.CurrentFormatVersion;
        }

        private static void ClearLegacyLoadedAmmunition(
            List<InventoryItemSaveData> records)
        {
            if (records == null)
            {
                return;
            }

            foreach (InventoryItemSaveData record in records)
            {
                if (record == null)
                {
                    continue;
                }

                record.hasLoadedAmmunition = false;
                record.loadedAmmunition = 0;
            }
        }

#if UNITY_EDITOR
        public static bool SetEditorStorageRootForTests(string root, out string error)
        {
            if (string.IsNullOrWhiteSpace(root))
            {
                error = "Editor save-test storage root is empty.";
                return false;
            }

            try
            {
                editorStorageRootOverride = Path.GetFullPath(root);
                error = null;
                return true;
            }
            catch (Exception exception)
            {
                error = $"Editor save-test storage root is invalid: {exception.Message}";
                return false;
            }
        }

        public static void ClearEditorStorageRootForTests()
        {
            editorStorageRootOverride = null;
        }
#endif
    }
}
