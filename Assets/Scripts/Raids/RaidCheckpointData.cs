using System;
using System.Collections.Generic;
using FantasySurvival.SaveSystem;

namespace FantasySurvival.Raids
{
    public enum RaidCheckpointPhase
    {
        Active = 1,
        Resolved = 2
    }

    public enum RaidSettlementJournalKind
    {
        None = 0,
        OutcomeSettlement = 1,
        RecoveryFailureMarker = 2,
        FreshDepartureRollback = 3
    }

    [Serializable]
    public sealed class RaidRecoveryBaselineData
    {
        public const int CurrentFormatVersion = 1;

        public string gameId;
        public int formatVersion;
        public string raidInstanceId;
        public string createdAtUtc;
        public string raidScene;
        public string raidSpawnId;
        public string sceneStateId;
        public GameSaveData startingState;
    }

    [Serializable]
    public sealed class RaidCheckpointData
    {
        public const int CurrentFormatVersion = 1;
        public const int LegacyWorldStateVersion = 1;
        public const int CurrentWorldStateVersion = 2;

        public string gameId;
        public int formatVersion;
        public int worldStateVersion;
        public string raidInstanceId;
        public long sequence;
        public string savedAtUtc;
        public RaidCheckpointPhase phase;
        public RaidOutcome outcome;
        public string raidScene;
        public string raidSpawnId;
        public string sceneStateId;
        public int generatorVersion;
        public int mapSeed;
        // Legacy field name: current captures store the layout + spawn-manifest world hash.
        // Restore also accepts the old layout-only hash once for non-loss migration.
        public string layoutHash;
        public RaidTransformSaveData playerTransform;
        public float playerCurrentHealth;
        public float playerMaxHealth;
        public GameSaveData persistentState;
        public int chestRecordCount;
        public List<RaidChestSaveData> chests = new List<RaidChestSaveData>();
        public int enemyRecordCount;
        public List<RaidEnemySaveData> enemies = new List<RaidEnemySaveData>();
        public int worldItemRecordCount;
        public List<RaidWorldItemSaveData> worldItems = new List<RaidWorldItemSaveData>();
    }

    /// <summary>
    /// Durable fail/settlement intent for an interrupted raid. Version 2 explicitly
    /// distinguishes an exact outcome settlement, a marker-only recovery failure, and
    /// a pre-entry fresh-departure rollback so the shared RecoveryFailed outcome cannot
    /// make their Player-item rules ambiguous. Exact payloads are reused unchanged when
    /// settlement resumes after another process interruption.
    /// </summary>
    [Serializable]
    public sealed class RaidSettlementJournalData
    {
        public const int CurrentFormatVersion = 2;

        public string gameId;
        public int formatVersion;
        public string raidInstanceId;
        public string writtenAtUtc;
        public RaidSettlementJournalKind kind;
        public RaidOutcome outcome;
        public GameSaveData settlementState;
    }

    [Serializable]
    public sealed class RaidChestSaveData
    {
        public string stableId;
        public InventoryGridSaveData inventory;
    }

    [Serializable]
    public sealed class RaidEnemySaveData
    {
        public string stableId;
        public RaidTransformSaveData transform;
        public float currentHealth;
        public float maxHealth;
        public InventoryGridSaveData corpseInventory;
    }

    [Serializable]
    public sealed class RaidWorldItemSaveData
    {
        // Stable world-entity ID for this dropped item. This is intentionally
        // separate from ItemDefinition's numeric kind ID and save-local item records.
        public string stableId;
        public RaidTransformSaveData transform;
        // Exact one-root-item owner grid, including stack count, rotation,
        // magazine state, and any nested container contents.
        public InventoryGridSaveData inventory;
    }

    [Serializable]
    public sealed class RaidTransformSaveData
    {
        public float positionX;
        public float positionY;
        public float positionZ;
        public float rotationX;
        public float rotationY;
        public float rotationZ;
        public float rotationW;
    }
}
