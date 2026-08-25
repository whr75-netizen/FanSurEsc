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
        public const int CurrentWorldStateVersion = 1;

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
        public string layoutHash;
        public RaidTransformSaveData playerTransform;
        public float playerCurrentHealth;
        public float playerMaxHealth;
        public GameSaveData persistentState;
        public int chestRecordCount;
        public List<RaidChestSaveData> chests = new List<RaidChestSaveData>();
        public int enemyRecordCount;
        public List<RaidEnemySaveData> enemies = new List<RaidEnemySaveData>();
    }

    /// <summary>
    /// Durable fail/settlement intent for an interrupted raid. A record without
    /// settlementState is a fail-closed marker. Once the Player reaches the base,
    /// settlementState is filled with the exact ordinary-save payload so repeating
    /// settlement after another process interruption is idempotent.
    /// </summary>
    [Serializable]
    public sealed class RaidSettlementJournalData
    {
        public const int CurrentFormatVersion = 1;

        public string gameId;
        public int formatVersion;
        public string raidInstanceId;
        public string writtenAtUtc;
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
