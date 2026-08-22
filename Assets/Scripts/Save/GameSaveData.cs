using System;
using System.Collections.Generic;

namespace FantasySurvival.SaveSystem
{
    [Serializable]
    public sealed class GameSaveData
    {
        public const string CurrentGameId = "fantasy-survival-escape";
        public const int CurrentFormatVersion = 3;

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
        // Reserved for confirmed base state with stable domain IDs.
        // The current scene-local test chests do not have those IDs yet.
        public int formatVersion;
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
