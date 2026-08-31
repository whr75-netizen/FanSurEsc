using System;
using System.Collections.Generic;
using FantasySurvival.Quests;

namespace FantasySurvival.SaveSystem
{
    [Serializable]
    public sealed class GameSaveData
    {
        public const string CurrentGameId = "fantasy-survival-escape";
        public const int CurrentFormatVersion = 7;

        public string gameId;
        public int formatVersion;
        public string savedAtUtc;
        // Durable cross-check for an expedition whose Recovery folder is missing.
        // The ordinary slot may hold the raid-start state or the latest explicit
        // raid autosave's persistent state. Live scene/world state stays in Recovery.
        public bool raidInProgress;
        public string activeRaidInstanceId;
        public PlayerItemStateSaveData playerItems;
        public PlayerCurrencySaveData playerCurrency;
        public PlayerProgressSaveData playerProgress;
        // Kept only so JsonUtility can read and migrate the development v2 schema.
        public InventoryGridSaveData playerInventory;
        public BaseSaveData baseState;
        public BaseMerchantStateSaveData baseMerchantState;
    }

    [Serializable]
    public sealed class PlayerProgressSaveData
    {
        public const int CurrentFormatVersion = 1;

        public int formatVersion;
        public int questRecordCount;
        public List<QuestProgressSaveData> quests = new List<QuestProgressSaveData>();

        // A v6-or-older save has no quest roster. This migration provenance allows
        // the current authored definition to materialize as Available on first load.
        public bool allowAuthoredQuestInitialization;

        public int enemyKills;
        public int successfulExtractions;
        public int playerDeaths;
        public int abandonments;
        public int recoveryFailures;
        public int completedQuests;
    }

    [Serializable]
    public sealed class QuestProgressSaveData
    {
        public string questId;
        public QuestProgressStatus status;
        public int enemyKills;
    }

    [Serializable]
    public sealed class PlayerCurrencySaveData
    {
        public const int CurrentFormatVersion = 1;

        public int formatVersion;
        public int gold;
        public int silver;
    }

    [Serializable]
    public sealed class BaseMerchantStateSaveData
    {
        public const int CurrentFormatVersion = 1;
        public const string LayoutId = "base-merchants-v1";

        public int formatVersion;
        public string layoutId;
        public int merchantRecordCount;
        public List<BaseMerchantSaveData> merchants = new List<BaseMerchantSaveData>();

        // Durable migration provenance. Saves older than v5 had no merchant roster,
        // so an exact Recovery settlement may need to carry this permission across a
        // process restart until a live base capture writes the materialized roster.
        public bool allowAuthoredMerchantInitialization;
    }

    [Serializable]
    public sealed class BaseMerchantSaveData
    {
        public string merchantId;
        public InventoryGridSaveData stock;
    }

    [Serializable]
    public sealed class BaseSaveData
    {
        public const int CurrentFormatVersion = 2;
        public const string FurnitureLayoutId = "base-furniture-v1";

        public int formatVersion;
        public string layoutId;
        public int furnitureRecordCount;
        public List<BaseFurnitureSaveData> furniture = new List<BaseFurnitureSaveData>();

        // Durable migration provenance. Legacy v2/v3 files had no furniture records,
        // and exact Recovery payloads can be re-serialized before a live base capture.
        // A native payload without this permission must match the placed-ID set exactly.
        public bool allowAuthoredFurnitureInitialization;
    }

    [Serializable]
    public sealed class BaseFurnitureSaveData
    {
        // Stable placed-object ID. This is separate from the shared definition key.
        public string instanceId;
        // Namespaced shared definition key, for example core:storage_chest.
        public string definitionKey;
        // Optional mutable storage state for furniture with a Chest capability.
        public InventoryGridSaveData storage;
    }

    [Serializable]
    public sealed class InventoryGridSaveData
    {
        public const string FlatLayoutId = "flat-records-v1";

        public string layoutId;
        public int width;
        public int height;
        public int itemRecordCount;
        public List<InventoryItemSaveData> items = new List<InventoryItemSaveData>();
    }

    [Serializable]
    public sealed class PlayerItemStateSaveData
    {
        public const string FlatLayoutId = "flat-player-items-v1";

        public string layoutId;
        public int inventoryWidth;
        public int inventoryHeight;
        public int itemRecordCount;
        public List<InventoryItemSaveData> items = new List<InventoryItemSaveData>();
    }

    [Serializable]
    public sealed class InventoryItemSaveData
    {
        // Save-file-local relationship key only. This is not a persistent item instance ID.
        public int recordId;
        public int parentContainerRecordId = -1;
        public int definitionId;
        public int slotIndex;
        // 0 means a grid/container record. 1..14 are stable EquipmentSlotId values.
        public int equipmentSlot;
        public bool isRotated;
        // Zero is reserved for additive compatibility with records written before
        // stack quantities existed. InventorySaveCodec restores that legacy value as 1.
        public int quantity;
        // Version 6 stores the mutable magazine state on each runtime weapon record.
        // Older records omit the flag and are restored as an empty magazine.
        public bool hasLoadedAmmunition;
        public int loadedAmmunition;
    }
}
