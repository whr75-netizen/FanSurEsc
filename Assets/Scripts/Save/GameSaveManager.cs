using System;
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

        public static string SlotOnePath => Path.Combine(
            Application.persistentDataPath,
            SaveFolderName,
            SlotOneFileName);

        private static string SlotOneBackupPath => SlotOnePath + ".bak";
        public static GameSaveData CreateSave(
            PlayerItemStateSaveData playerItems,
            BaseSaveData baseState)
        {
            return new GameSaveData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = GameSaveData.CurrentFormatVersion,
                savedAtUtc = DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture),
                playerItems = playerItems,
                playerInventory = null,
                baseState = baseState
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
                           currentSave?.baseState);
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
                File.WriteAllText(temporaryPath, json, new UTF8Encoding(false));

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

            if (string.IsNullOrWhiteSpace(saveData.savedAtUtc) || saveData.playerItems == null)
            {
                error = "Save data is missing required fields.";
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

        private static bool TryNormalizeToCurrentVersion(GameSaveData saveData, out string error)
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

            if (saveData.formatVersion == 2)
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
                saveData.baseState = BaseFurnitureSaveCodec.CreateEmptySaveData(true);
                saveData.formatVersion = GameSaveData.CurrentFormatVersion;
                error = null;
                return true;
            }

            if (saveData.formatVersion == 3)
            {
                if (saveData.baseState != null && saveData.baseState.formatVersion != 1)
                {
                    error = $"Legacy v3 base-state version {saveData.baseState.formatVersion} is unsupported.";
                    return false;
                }

                saveData.baseState = BaseFurnitureSaveCodec.CreateEmptySaveData(true);
                saveData.formatVersion = GameSaveData.CurrentFormatVersion;
                error = null;
                return true;
            }

            if (saveData.formatVersion != GameSaveData.CurrentFormatVersion)
            {
                error = $"Unsupported save version {saveData.formatVersion}.";
                return false;
            }

            error = null;
            return true;
        }
    }
}
