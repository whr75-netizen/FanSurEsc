using System;
using System.Collections.Generic;
using System.Globalization;
using FantasySurvival.BaseBuilding;
using FantasySurvival.Inventory;
using FantasySurvival.SaveSystem;

namespace FantasySurvival.Raids
{
    public static class RaidCheckpointValidator
    {
        private const float QuaternionMagnitudeTolerance = 0.01f;

        public static bool TryValidateBaseline(
            RaidRecoveryBaselineData baseline,
            ItemDatabase itemDatabase,
            BaseFurnitureDatabase furnitureDatabase,
            int expectedInventoryWidth,
            int expectedInventoryHeight,
            out string error)
        {
            if (baseline == null)
            {
                error = "Raid recovery baseline is empty.";
                return false;
            }

            if (baseline.gameId != GameSaveData.CurrentGameId ||
                baseline.formatVersion != RaidRecoveryBaselineData.CurrentFormatVersion)
            {
                error = "Raid recovery baseline has an unsupported header.";
                return false;
            }

            if (!Guid.TryParse(baseline.raidInstanceId, out _) ||
                string.IsNullOrWhiteSpace(baseline.raidScene) ||
                string.IsNullOrWhiteSpace(baseline.raidSpawnId) ||
                string.IsNullOrWhiteSpace(baseline.sceneStateId) ||
                !HasValidUtcTimestamp(baseline.createdAtUtc))
            {
                error = "Raid recovery baseline is missing required identity fields.";
                return false;
            }

            return TryValidatePersistentState(
                baseline.startingState,
                itemDatabase,
                furnitureDatabase,
                expectedInventoryWidth,
                expectedInventoryHeight,
                out error);
        }

        public static bool TryValidateCheckpointForLoad(
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint,
            ItemDatabase itemDatabase,
            BaseFurnitureDatabase furnitureDatabase,
            int expectedInventoryWidth,
            int expectedInventoryHeight,
            out string error)
        {
            if (!TryValidateBaseline(
                    baseline,
                    itemDatabase,
                    furnitureDatabase,
                    expectedInventoryWidth,
                    expectedInventoryHeight,
                    out error) ||
                !TryValidateCheckpointStructure(baseline, checkpoint, out error))
            {
                return false;
            }

            if (!TryValidatePersistentState(
                    checkpoint.persistentState,
                    itemDatabase,
                    furnitureDatabase,
                    expectedInventoryWidth,
                    expectedInventoryHeight,
                    out error))
            {
                error = $"Raid checkpoint persistent state is invalid: {error}";
                return false;
            }

            foreach (RaidChestSaveData chest in checkpoint.chests)
            {
                if (!InventorySaveCodec.TryRestoreGrid(
                        chest.inventory,
                        itemDatabase,
                        out _,
                        out error))
                {
                    error = $"Raid chest '{chest.stableId}' is invalid: {error}";
                    return false;
                }
            }

            foreach (RaidEnemySaveData enemy in checkpoint.enemies)
            {
                if (!InventorySaveCodec.TryRestoreGrid(
                        enemy.corpseInventory,
                        itemDatabase,
                        out _,
                        out error))
                {
                    error = $"Raid enemy '{enemy.stableId}' corpse inventory is invalid: {error}";
                    return false;
                }
            }

            error = null;
            return true;
        }

        public static bool TryValidateCheckpointStructure(
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint,
            out string error)
        {
            if (baseline == null || checkpoint == null)
            {
                error = "Raid checkpoint or its baseline is missing.";
                return false;
            }

            if (checkpoint.gameId != GameSaveData.CurrentGameId ||
                checkpoint.formatVersion != RaidCheckpointData.CurrentFormatVersion ||
                checkpoint.worldStateVersion != RaidCheckpointData.CurrentWorldStateVersion)
            {
                error = "Raid checkpoint has an unsupported header.";
                return false;
            }

            if (!string.Equals(
                    checkpoint.raidInstanceId,
                    baseline.raidInstanceId,
                    StringComparison.Ordinal) ||
                !string.Equals(checkpoint.raidScene, baseline.raidScene, StringComparison.Ordinal) ||
                !string.Equals(checkpoint.raidSpawnId, baseline.raidSpawnId, StringComparison.Ordinal) ||
                !string.Equals(
                    checkpoint.sceneStateId,
                    baseline.sceneStateId,
                    StringComparison.Ordinal))
            {
                error = "Raid checkpoint does not belong to its recovery baseline.";
                return false;
            }

            if (checkpoint.sequence <= 0 || checkpoint.sequence == long.MaxValue ||
                !HasValidUtcTimestamp(checkpoint.savedAtUtc) ||
                checkpoint.generatorVersion <= 0 ||
                string.IsNullOrWhiteSpace(checkpoint.layoutHash) ||
                !ulong.TryParse(
                    checkpoint.layoutHash,
                    NumberStyles.HexNumber,
                    CultureInfo.InvariantCulture,
                    out _))
            {
                error = "Raid checkpoint has invalid sequence, timestamp, or map identity.";
                return false;
            }

            if (checkpoint.phase == RaidCheckpointPhase.Active)
            {
                if (checkpoint.outcome != RaidOutcome.None ||
                    !IsFinite(checkpoint.playerCurrentHealth) ||
                    checkpoint.playerCurrentHealth <= 0f)
                {
                    error = "An active raid checkpoint must contain a living Player and no outcome.";
                    return false;
                }
            }
            else if (checkpoint.phase == RaidCheckpointPhase.Resolved)
            {
                if (!IsTerminalOutcome(checkpoint.outcome))
                {
                    error = "A resolved raid checkpoint has an unknown terminal outcome.";
                    return false;
                }

                bool playerDied = checkpoint.outcome == RaidOutcome.PlayerDied;
                if (playerDied != (checkpoint.playerCurrentHealth <= 0f))
                {
                    error = "Raid outcome and Player health disagree.";
                    return false;
                }
            }
            else
            {
                error = "Raid checkpoint has an unknown phase.";
                return false;
            }

            if (!IsFinite(checkpoint.playerMaxHealth) ||
                checkpoint.playerMaxHealth <= 0f ||
                checkpoint.playerCurrentHealth < 0f ||
                checkpoint.playerCurrentHealth > checkpoint.playerMaxHealth ||
                !HasValidTransform(checkpoint.playerTransform))
            {
                error = "Raid checkpoint Player state is invalid.";
                return false;
            }

            if (checkpoint.persistentState == null ||
                checkpoint.chests == null ||
                checkpoint.enemies == null ||
                checkpoint.chestRecordCount != checkpoint.chests.Count ||
                checkpoint.enemyRecordCount != checkpoint.enemies.Count)
            {
                error = "Raid checkpoint record counts are inconsistent.";
                return false;
            }

            var stableIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (RaidChestSaveData chest in checkpoint.chests)
            {
                if (chest == null ||
                    string.IsNullOrWhiteSpace(chest.stableId) ||
                    !stableIds.Add($"chest:{chest.stableId}") ||
                    chest.inventory == null)
                {
                    error = "Raid checkpoint contains an invalid or duplicate Chest record.";
                    return false;
                }
            }

            foreach (RaidEnemySaveData enemy in checkpoint.enemies)
            {
                if (enemy == null ||
                    string.IsNullOrWhiteSpace(enemy.stableId) ||
                    !stableIds.Add($"enemy:{enemy.stableId}") ||
                    !HasValidTransform(enemy.transform) ||
                    !IsFinite(enemy.currentHealth) ||
                    !IsFinite(enemy.maxHealth) ||
                    enemy.maxHealth <= 0f ||
                    enemy.currentHealth < 0f ||
                    enemy.currentHealth > enemy.maxHealth ||
                    enemy.corpseInventory == null)
                {
                    error = "Raid checkpoint contains an invalid or duplicate Enemy record.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        public static bool TryValidateSettlementJournalStructure(
            RaidRecoveryBaselineData baseline,
            RaidSettlementJournalData journal,
            out string error)
        {
            if (baseline == null || journal == null)
            {
                error = "Raid settlement journal or its baseline is missing.";
                return false;
            }

            if (journal.gameId != GameSaveData.CurrentGameId ||
                journal.formatVersion != RaidSettlementJournalData.CurrentFormatVersion ||
                !string.Equals(
                    journal.raidInstanceId,
                    baseline.raidInstanceId,
                    StringComparison.Ordinal) ||
                !HasValidUtcTimestamp(journal.writtenAtUtc) ||
                !IsTerminalOutcome(journal.outcome) ||
                (journal.settlementState == null &&
                 journal.outcome != RaidOutcome.RecoveryFailed))
            {
                error = "Raid settlement journal has an invalid header or outcome.";
                return false;
            }

            error = null;
            return true;
        }

        public static bool TryValidatePersistentStateForLoad(
            GameSaveData saveData,
            ItemDatabase itemDatabase,
            BaseFurnitureDatabase furnitureDatabase,
            int expectedInventoryWidth,
            int expectedInventoryHeight,
            out string error)
        {
            return TryValidatePersistentState(
                saveData,
                itemDatabase,
                furnitureDatabase,
                expectedInventoryWidth,
                expectedInventoryHeight,
                out error);
        }

        private static bool TryValidatePersistentState(
            GameSaveData saveData,
            ItemDatabase itemDatabase,
            BaseFurnitureDatabase furnitureDatabase,
            int expectedInventoryWidth,
            int expectedInventoryHeight,
            out string error)
        {
            if (saveData == null ||
                saveData.gameId != GameSaveData.CurrentGameId ||
                saveData.formatVersion != GameSaveData.CurrentFormatVersion ||
                !HasValidUtcTimestamp(saveData.savedAtUtc) ||
                saveData.raidInProgress ||
                !string.IsNullOrEmpty(saveData.activeRaidInstanceId) ||
                saveData.playerItems == null ||
                saveData.baseState == null ||
                saveData.baseState.formatVersion != BaseSaveData.CurrentFormatVersion)
            {
                error = "Persistent state has an unsupported or incomplete header.";
                return false;
            }

            if (!InventorySaveCodec.TryRestore(
                    saveData.playerItems,
                    itemDatabase,
                    expectedInventoryWidth,
                    expectedInventoryHeight,
                    out _,
                    out error))
            {
                return false;
            }

            return BaseFurnitureSaveCodec.TryRestore(
                saveData.baseState,
                itemDatabase,
                furnitureDatabase,
                out _,
                out error);
        }

        private static bool HasValidUtcTimestamp(string value)
        {
            return !string.IsNullOrWhiteSpace(value) &&
                   DateTime.TryParse(
                       value,
                       CultureInfo.InvariantCulture,
                       DateTimeStyles.RoundtripKind,
                       out _);
        }

        public static bool HasValidTransform(RaidTransformSaveData value)
        {
            if (value == null ||
                !IsFinite(value.positionX) ||
                !IsFinite(value.positionY) ||
                !IsFinite(value.positionZ) ||
                !IsFinite(value.rotationX) ||
                !IsFinite(value.rotationY) ||
                !IsFinite(value.rotationZ) ||
                !IsFinite(value.rotationW))
            {
                return false;
            }

            float magnitudeSquared =
                value.rotationX * value.rotationX +
                value.rotationY * value.rotationY +
                value.rotationZ * value.rotationZ +
                value.rotationW * value.rotationW;
            return magnitudeSquared >= QuaternionMagnitudeTolerance;
        }

        public static bool IsFinite(float value)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value);
        }

        public static bool IsTerminalOutcome(RaidOutcome outcome)
        {
            return outcome == RaidOutcome.Extracted ||
                   outcome == RaidOutcome.PlayerDied ||
                   outcome == RaidOutcome.Abandoned ||
                   outcome == RaidOutcome.RecoveryFailed;
        }
    }
}
