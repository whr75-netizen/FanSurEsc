using System;
using System.Collections.Generic;

namespace FantasySurvival.SaveSystem
{
    [Serializable]
    public sealed class GameSaveData
    {
        public const string CurrentGameId = "fantasy-survival-escape";
        public const int CurrentFormatVersion = 4;

        public string gameId;
        public int formatVersion;
        public string savedAtUtc;
        public PlayerItemStateSaveData playerItems;
        // Kept only so JsonUtility can read and migrate the development v2 schema.
        public InventoryGridSaveData playerInventory;
        public BaseSaveData baseState;
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

        // Runtime-only migration context. Legacy v2/v3 files had no furniture records,
        // so their first v4 load may initialize the authored base layout. A native v4
        // payload must instead match the current placed-ID set exactly.
        [NonSerialized] public bool allowAuthoredFurnitureInitialization;
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
    }
}
