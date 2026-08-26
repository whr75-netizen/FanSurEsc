using System;
using FantasySurvival.Inventory;
using UnityEngine;
using VariableInventorySystem; // ★ 에셋 네임스페이스 사용

// 이 스크립트를 상자 프리팹 또는 게임 오브젝트에 추가하세요.
// 상자 오브젝트에는 Collider 컴포넌트가 있어야 하고, IsTrigger가 체크되어 있어야 합니다.
// 또한, 플레이어의 OnTriggerEnter/Exit에서 감지할 수 있도록 적절한 레이어("Chest" 등) 또는 태그("Chest" 등)를 설정해야 합니다.
public class Chest : MonoBehaviour
{
    [System.NonSerialized] public StandardStashViewData chestInventoryData; // 런타임 전용. 세이브 데이터는 별도 DTO로 연결한다.

    [Tooltip("이 상자 인벤토리의 가로 칸 수")]
    public int chestWidth = 6; // 상자마다 다르게 설정 가능
    [Tooltip("이 상자 인벤토리의 세로 칸 수")]
    public int chestHeight = 5; // 상자마다 다르게 설정 가능
    [Header("Optional Starting Items")]
    [SerializeField] private ItemDatabase itemDatabase;
    [SerializeField] private int[] startingItemIds = Array.Empty<int>();
    [Header("Raid Loot")]
    [Tooltip("Optional deterministic loot definition. Raid scene bindings roll it once on Fresh entry.")]
    [SerializeField] private LootTableDefinition lootTable;

    public LootTableDefinition LootTable => lootTable;

    void Awake()
    {
        if (!InventoryGridConstraints.TryValidateDimensions(
                chestWidth,
                chestHeight,
                out string error))
        {
            enabled = false;
            Debug.LogError($"[{name}] Could not allocate chest inventory: {error}", this);
            return;
        }

        // An inactive scene object can be bound to the authoritative base store before
        // Unity invokes this Awake. Preserve that externally supplied grid when the
        // object is activated later instead of replacing it with authored starting loot.
        if (chestInventoryData != null)
        {
            if (!CanBindInventory(chestInventoryData, out error))
            {
                enabled = false;
                Debug.LogError($"[{name}] Existing chest inventory is invalid: {error}", this);
            }

            return;
        }

        if (!TryCreateAuthoredInventory(out chestInventoryData, out error))
        {
            // Keep the component usable for diagnostics without exposing a partially
            // seeded container as valid authored loot.
            chestInventoryData = new StandardStashViewData(chestWidth, chestHeight);
            Debug.LogError($"[{name}] Could not initialize chest inventory: {error}", this);
        }
    }

    public bool TryCreateAuthoredInventory(
        out StandardStashViewData inventory,
        out string error)
    {
        inventory = null;
        if (!InventoryGridConstraints.TryValidateDimensions(
                chestWidth,
                chestHeight,
                out error))
        {
            return false;
        }

        var candidate = new StandardStashViewData(chestWidth, chestHeight);
        if (startingItemIds == null || startingItemIds.Length == 0)
        {
            inventory = candidate;
            error = null;
            return true;
        }

        if (itemDatabase == null)
        {
            error = "Starting item IDs require an ItemDatabase reference.";
            return false;
        }

        foreach (int itemId in startingItemIds)
        {
            if (!itemDatabase.TryGet(itemId, out ItemDefinition definition))
            {
                error = $"ItemDatabase does not contain starting item ID {itemId}.";
                return false;
            }

            if (!InventoryItemDataFactory.TryCreate(definition, out IVariableInventoryCellData item, out error))
            {
                error = $"Starting item ID {itemId} is invalid: {error}";
                return false;
            }

            int? slot = candidate.GetInsertableId(item);
            if (!slot.HasValue)
            {
                error = $"Starting item ID {itemId} does not fit in the {chestWidth}x{chestHeight} chest.";
                return false;
            }

            candidate.InsertInventoryItem(slot.Value, item);
        }

        inventory = candidate;
        error = null;
        return true;
    }

    public bool TryCreateRaidLootInventory(
        ItemDatabase authoritativeItemDatabase,
        int mapSeed,
        string stableContainerId,
        out StandardStashViewData inventory,
        out string error)
    {
        if (lootTable == null)
        {
            inventory = null;
            error = "Raid loot requires an assigned LootTableDefinition.";
            return false;
        }

        return LootTableRoller.TryCreateInventory(
            lootTable,
            authoritativeItemDatabase,
            mapSeed,
            stableContainerId,
            chestWidth,
            chestHeight,
            out inventory,
            out error);
    }

    public bool CanBindInventory(StandardStashViewData inventory, out string error)
    {
        if (!InventoryGridConstraints.TryValidateDimensions(
                chestWidth,
                chestHeight,
                out error))
        {
            return false;
        }

        if (inventory == null)
        {
            error = "Persistent storage grid is missing.";
            return false;
        }

        if (inventory.CapacityWidth != chestWidth || inventory.CapacityHeight != chestHeight ||
            inventory.CellData == null || inventory.CellData.Length != chestWidth * chestHeight)
        {
            error = $"Persistent storage grid must match the authored {chestWidth}x{chestHeight} capacity.";
            return false;
        }

        error = null;
        return true;
    }

    public bool TryBindInventory(StandardStashViewData inventory, out string error)
    {
        if (!CanBindInventory(inventory, out error))
        {
            return false;
        }

        chestInventoryData = inventory;
        error = null;
        return true;
    }
}
