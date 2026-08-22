using System;
using System.Globalization;
using System.IO;
using System.Text;
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
        public static GameSaveData CreateSave(PlayerItemStateSaveData playerItems)
        {
            return new GameSaveData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = GameSaveData.CurrentFormatVersion,
                savedAtUtc = DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture),
                playerItems = playerItems,
                playerInventory = null,
                baseState = new BaseSaveData { formatVersion = 1 }
            };
        }

        public static bool TryWriteSlotOne(
            GameSaveData saveData,
            ItemDatabase database,
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

            return TryWriteFile(saveData, SlotOnePath, out error);
        }

        private static bool TryWriteFile(GameSaveData saveData, string finalPath, out string error)
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
                    File.Replace(temporaryPath, finalPath, backupPath, true);
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

            if (saveData.baseState == null || saveData.baseState.formatVersion != 1)
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

            if (saveData.formatVersion != 2)
            {
                error = $"Unsupported save version {saveData.formatVersion}.";
                return false;
            }

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
            saveData.formatVersion = GameSaveData.CurrentFormatVersion;
            error = null;
            return true;
        }
    }
}
