using System;
using System.Collections.Generic;
using FantasySurvival.Inventory;
using VariableInventorySystem;

namespace FantasySurvival.Trading
{
    /// <summary>
    /// Base-session authority for merchant stock. Scene NPCs only resolve their stable ID
    /// through this store and never own a second copy of the inventory.
    /// </summary>
    public sealed class BaseMerchantStateStore
    {
        public const int MaxMerchantCount = 256;

        private readonly Dictionary<string, StandardStashViewData> inventories =
            new Dictionary<string, StandardStashViewData>(StringComparer.Ordinal);

        public int Count => inventories.Count;

        public IEnumerable<KeyValuePair<string, StandardStashViewData>> Entries => inventories;

        public bool TryValidateBindings(
            IReadOnlyList<Merchant> merchants,
            bool allowCreateMissingStates,
            out string error)
        {
            if (merchants == null)
            {
                error = "Base merchant binding list is missing.";
                return false;
            }

            var seenIds = new HashSet<string>(StringComparer.Ordinal);
            for (int index = 0; index < merchants.Count; index++)
            {
                Merchant merchant = merchants[index];
                if (merchant == null)
                {
                    error = $"Base merchant binding at index {index} is missing.";
                    return false;
                }

                if (!merchant.TryValidateAuthoring(out error))
                {
                    error = $"[{merchant.name}] {error}";
                    return false;
                }

                if (!seenIds.Add(merchant.MerchantId))
                {
                    error = $"Base merchant ID '{merchant.MerchantId}' is assigned more than once in the scene.";
                    return false;
                }

                if (inventories.TryGetValue(merchant.MerchantId, out StandardStashViewData inventory))
                {
                    if (inventory == null ||
                        inventory.CapacityWidth != merchant.InventoryWidth ||
                        inventory.CapacityHeight != merchant.InventoryHeight)
                    {
                        error = $"Base merchant ID '{merchant.MerchantId}' stock dimensions do not match its authored layout.";
                        return false;
                    }
                }
                else if (!allowCreateMissingStates)
                {
                    error = $"Base state is missing required merchant ID '{merchant.MerchantId}'.";
                    return false;
                }
            }

            if (!allowCreateMissingStates && inventories.Count != seenIds.Count)
            {
                foreach (string stateId in inventories.Keys)
                {
                    if (!seenIds.Contains(stateId))
                    {
                        error = $"Base state contains merchant ID '{stateId}' that is not placed in this base layout.";
                        return false;
                    }
                }

                error = "Base state merchant count does not match the placed base layout.";
                return false;
            }

            error = null;
            return true;
        }

        public bool TryGet(string merchantId, out StandardStashViewData inventory)
        {
            inventory = null;
            return !string.IsNullOrWhiteSpace(merchantId) &&
                   inventories.TryGetValue(merchantId, out inventory);
        }

        public bool TryGetOrCreate(
            string merchantId,
            int width,
            int height,
            ItemDatabase itemDatabase,
            IReadOnlyList<int> startingItemIds,
            out StandardStashViewData inventory,
            out string error)
        {
            inventory = null;
            if (string.IsNullOrWhiteSpace(merchantId))
            {
                error = "Merchant stable ID is missing.";
                return false;
            }

            if (!InventoryGridConstraints.TryValidateDimensions(width, height, out error))
            {
                return false;
            }

            if (inventories.TryGetValue(merchantId, out inventory))
            {
                if (inventory == null || inventory.CapacityWidth != width ||
                    inventory.CapacityHeight != height)
                {
                    error = $"Merchant '{merchantId}' stock dimensions do not match its authored {width}x{height} grid.";
                    inventory = null;
                    return false;
                }

                error = null;
                return true;
            }

            if (inventories.Count >= MaxMerchantCount)
            {
                error = $"Merchant count exceeds the supported limit of {MaxMerchantCount}.";
                return false;
            }

            if (itemDatabase == null)
            {
                error = $"Merchant '{merchantId}' has no ItemDatabase.";
                return false;
            }

            var candidate = new StandardStashViewData(width, height);
            if (startingItemIds != null)
            {
                foreach (int itemId in startingItemIds)
                {
                    if (!itemDatabase.TryGet(itemId, out ItemDefinition definition))
                    {
                        error = $"Merchant '{merchantId}' references unknown starting item ID {itemId}.";
                        return false;
                    }

                    if (definition.IsContainer || !definition.IsTradable)
                    {
                        error = $"Merchant '{merchantId}' starting stock cannot include non-tradable item ID {itemId}.";
                        return false;
                    }

                    if (!InventoryItemDataFactory.TryCreate(definition, out var item, out error))
                    {
                        error = $"Merchant '{merchantId}' starting item ID {itemId} is invalid: {error}";
                        return false;
                    }

                    int? slot = candidate.GetInsertableId(item);
                    if (!slot.HasValue)
                    {
                        error = $"Merchant '{merchantId}' has no room for starting item ID {itemId}.";
                        return false;
                    }

                    candidate.InsertInventoryItem(slot.Value, item);
                }
            }

            inventories.Add(merchantId, candidate);
            inventory = candidate;
            error = null;
            return true;
        }

        public bool TryRegisterRestored(
            string merchantId,
            StandardStashViewData inventory,
            out string error)
        {
            if (string.IsNullOrWhiteSpace(merchantId) || inventory == null)
            {
                error = "Restored merchant ID or inventory is missing.";
                return false;
            }

            if (inventories.Count >= MaxMerchantCount)
            {
                error = $"Merchant count exceeds the supported limit of {MaxMerchantCount}.";
                return false;
            }

            if (inventories.ContainsKey(merchantId))
            {
                error = $"Merchant state contains duplicate stable ID '{merchantId}'.";
                return false;
            }

            inventories.Add(merchantId, inventory);
            error = null;
            return true;
        }
    }
}
