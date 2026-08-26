using System;
using System.Collections.Generic;
using System.Linq;
using FantasySurvival.Inventory;
using FantasySurvival.Trading;
using VariableInventorySystem;

namespace FantasySurvival.SaveSystem
{
    public static class BaseMerchantSaveCodec
    {
        private const int MaxTotalRuntimeGridCells = 262144;
        private const int MaxTotalStoredItems = 50000;

        public static BaseMerchantStateSaveData CreateEmptySaveData(
            bool allowAuthoredMerchantInitialization = false)
        {
            return new BaseMerchantStateSaveData
            {
                formatVersion = BaseMerchantStateSaveData.CurrentFormatVersion,
                layoutId = BaseMerchantStateSaveData.LayoutId,
                merchantRecordCount = 0,
                merchants = new List<BaseMerchantSaveData>(),
                allowAuthoredMerchantInitialization = allowAuthoredMerchantInitialization
            };
        }

        public static bool TryCapture(
            BaseMerchantStateStore source,
            ItemDatabase itemDatabase,
            out BaseMerchantStateSaveData saveData,
            out string error)
        {
            saveData = null;
            if (source == null || itemDatabase == null)
            {
                error = "Base merchant state or ItemDatabase is missing.";
                return false;
            }

            if (!InventorySaveCodec.TryBuildDefinitionIndex(
                    itemDatabase,
                    out Dictionary<int, ItemDefinition> itemDefinitions,
                    out error))
            {
                return false;
            }

            var records = new List<BaseMerchantSaveData>();
            foreach (KeyValuePair<string, StandardStashViewData> entry in
                     source.Entries.OrderBy(value => value.Key, StringComparer.Ordinal))
            {
                if (string.IsNullOrWhiteSpace(entry.Key) || entry.Value == null)
                {
                    error = "Base merchant state contains an empty ID or inventory.";
                    return false;
                }

                if (!InventorySaveCodec.TryCaptureGrid(
                        entry.Value,
                        itemDatabase,
                        out InventoryGridSaveData stock,
                        out error))
                {
                    error = $"Merchant '{entry.Key}' stock capture failed: {error}";
                    return false;
                }

                if (!TryValidateTradableStock(stock, itemDefinitions, out error))
                {
                    error = $"Merchant '{entry.Key}' stock capture failed: {error}";
                    return false;
                }

                records.Add(new BaseMerchantSaveData
                {
                    merchantId = entry.Key,
                    stock = stock
                });
            }

            saveData = new BaseMerchantStateSaveData
            {
                formatVersion = BaseMerchantStateSaveData.CurrentFormatVersion,
                layoutId = BaseMerchantStateSaveData.LayoutId,
                merchantRecordCount = records.Count,
                merchants = records
            };
            error = null;
            return true;
        }

        public static bool TryRestore(
            BaseMerchantStateSaveData saveData,
            ItemDatabase itemDatabase,
            out BaseMerchantStateStore restored,
            out string error)
        {
            restored = null;
            if (saveData == null ||
                saveData.formatVersion != BaseMerchantStateSaveData.CurrentFormatVersion ||
                !string.Equals(saveData.layoutId, BaseMerchantStateSaveData.LayoutId, StringComparison.Ordinal) ||
                saveData.merchantRecordCount < 0 ||
                saveData.merchantRecordCount > BaseMerchantStateStore.MaxMerchantCount ||
                saveData.merchants == null ||
                saveData.merchantRecordCount != saveData.merchants.Count ||
                (saveData.allowAuthoredMerchantInitialization &&
                 saveData.merchantRecordCount != 0) ||
                itemDatabase == null)
            {
                error = "Base merchant payload is missing, malformed, or unsupported.";
                return false;
            }

            if (!InventorySaveCodec.TryBuildDefinitionIndex(
                    itemDatabase,
                    out Dictionary<int, ItemDefinition> itemDefinitions,
                    out error))
            {
                return false;
            }

            var seenIds = new HashSet<string>(StringComparer.Ordinal);
            long totalRuntimeGridCells = 0;
            long totalStoredItems = 0;
            foreach (BaseMerchantSaveData record in saveData.merchants)
            {
                if (record == null || string.IsNullOrWhiteSpace(record.merchantId) ||
                    record.stock == null || !seenIds.Add(record.merchantId))
                {
                    error = "Base merchant payload contains an incomplete or duplicate record.";
                    return false;
                }

                if (!InventorySaveCodec.TryGetValidatedRestoreCost(
                        record.stock,
                        itemDefinitions,
                        out int itemCount,
                        out long runtimeGridCells,
                        out error))
                {
                    error = $"Merchant '{record.merchantId}' stock metadata is invalid: {error}";
                    return false;
                }

                if (!TryValidateTradableStock(record.stock, itemDefinitions, out error))
                {
                    error = $"Merchant '{record.merchantId}' stock is invalid: {error}";
                    return false;
                }

                totalRuntimeGridCells += runtimeGridCells;
                totalStoredItems += itemCount;
                if (totalRuntimeGridCells > MaxTotalRuntimeGridCells ||
                    totalStoredItems > MaxTotalStoredItems)
                {
                    error = "Base merchant payload exceeds the supported aggregate stock size.";
                    return false;
                }
            }

            var candidate = new BaseMerchantStateStore();
            foreach (BaseMerchantSaveData record in saveData.merchants)
            {
                if (!InventorySaveCodec.TryRestoreGrid(
                        record.stock,
                        itemDefinitions,
                        out StandardStashViewData inventory,
                        out error))
                {
                    error = $"Merchant '{record.merchantId}' stock restore failed: {error}";
                    return false;
                }

                if (!candidate.TryRegisterRestored(record.merchantId, inventory, out error))
                {
                    return false;
                }
            }

            restored = candidate;
            error = null;
            return true;
        }

        private static bool TryValidateTradableStock(
            InventoryGridSaveData stock,
            IReadOnlyDictionary<int, ItemDefinition> definitions,
            out string error)
        {
            if (stock?.items == null || definitions == null)
            {
                error = "stock item metadata is missing.";
                return false;
            }

            foreach (InventoryItemSaveData item in stock.items)
            {
                if (item == null ||
                    !definitions.TryGetValue(item.definitionId, out ItemDefinition definition) ||
                    !definition.IsTradable || definition.IsContainer)
                {
                    error = $"item ID {item?.definitionId ?? 0} is not a tradable non-container definition.";
                    return false;
                }
            }

            error = null;
            return true;
        }
    }
}
