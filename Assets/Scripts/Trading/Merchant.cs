using System;
using FantasySurvival.Inventory;
using UnityEngine;
using VariableInventorySystem;

namespace FantasySurvival.Trading
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(1100)]
    public sealed class Merchant : MonoBehaviour
    {
        [SerializeField] private string merchantId = "base:merchant_test";
        [SerializeField] private ItemDatabase itemDatabase;
        [SerializeField, Min(1)] private int inventoryWidth = InventoryUIManager.DefaultInventoryWidth;
        [SerializeField, Min(1)] private int inventoryHeight = InventoryUIManager.DefaultInventoryHeight;
        [SerializeField] private int[] startingItemIds = { 1, 2, 3, 4, 5 };

        public string MerchantId => merchantId;
        public ItemDatabase ItemDatabase => itemDatabase;
        public int InventoryWidth => inventoryWidth;
        public int InventoryHeight => inventoryHeight;

        private void Start()
        {
            // Materialize authored stock as soon as the base NPC exists so a save made
            // before the first interaction still captures this merchant. Start is used
            // because every scene object's Awake (including GameManager) has completed.
            if (!TryResolveInventory(out _, out string error))
            {
                Debug.LogError($"[{name}] Merchant initialization failed: {error}", this);
                enabled = false;
            }
        }

        public bool TryResolveInventory(
            out StandardStashViewData inventory,
            out string error)
        {
            inventory = null;
            GameManager owner = GameManager.Instance;
            if (owner == null)
            {
                error = "Persistent GameManager is unavailable.";
                return false;
            }

            return TryMaterializeIn(owner.BaseMerchantState, out inventory, out error);
        }

        public bool TryMaterializeIn(
            BaseMerchantStateStore store,
            out StandardStashViewData inventory,
            out string error)
        {
            inventory = null;
            if (store == null)
            {
                error = $"Merchant '{merchantId}' state store is missing.";
                return false;
            }

            return store.TryGetOrCreate(
                merchantId,
                inventoryWidth,
                inventoryHeight,
                itemDatabase,
                startingItemIds ?? Array.Empty<int>(),
                out inventory,
                out error);
        }

        public bool TryValidateAuthoring(out string error)
        {
            if (string.IsNullOrWhiteSpace(merchantId))
            {
                error = "Merchant stable ID is missing.";
                return false;
            }

            if (itemDatabase == null)
            {
                error = $"Merchant '{merchantId}' has no ItemDatabase.";
                return false;
            }

            if (!InventoryGridConstraints.TryValidateDimensions(
                    inventoryWidth,
                    inventoryHeight,
                    out error))
            {
                return false;
            }

            if (startingItemIds == null)
            {
                error = $"Merchant '{merchantId}' starting stock list is missing.";
                return false;
            }

            foreach (int itemId in startingItemIds)
            {
                if (!itemDatabase.TryGet(itemId, out ItemDefinition definition))
                {
                    error = $"Merchant '{merchantId}' references unknown starting item ID {itemId}.";
                    return false;
                }

                if (definition.IsContainer || !definition.IsTradable)
                {
                    error = $"Merchant '{merchantId}' starting item ID {itemId} is not a tradable non-container item.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private void OnValidate()
        {
            merchantId = merchantId?.Trim();
            inventoryWidth = Mathf.Clamp(inventoryWidth, 1, InventoryGridConstraints.MaxDimension);
            inventoryHeight = Mathf.Clamp(inventoryHeight, 1, InventoryGridConstraints.MaxDimension);
        }
    }
}
