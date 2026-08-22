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

    void Awake()
    {
        if (!TryCreateInitialInventory(out chestInventoryData, out string error))
        {
            // Keep the component usable for diagnostics without exposing a partially
            // seeded container as valid authored loot.
            chestInventoryData = new StandardStashViewData(chestWidth, chestHeight);
            Debug.LogError($"[{name}] Could not initialize chest inventory: {error}", this);
        }
    }

    private bool TryCreateInitialInventory(
        out StandardStashViewData inventory,
        out string error)
    {
        inventory = new StandardStashViewData(chestWidth, chestHeight);
        if (startingItemIds == null || startingItemIds.Length == 0)
        {
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

            IVariableInventoryCellData item = InventoryItemDataFactory.Create(definition);
            int? slot = inventory.GetInsertableId(item);
            if (!slot.HasValue)
            {
                error = $"Starting item ID {itemId} does not fit in the {chestWidth}x{chestHeight} chest.";
                return false;
            }

            inventory.InsertInventoryItem(slot.Value, item);
        }

        error = null;
        return true;
    }
}
