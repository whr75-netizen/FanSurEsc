using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using FantasySurvival.BaseBuilding;
using FantasySurvival.Inventory;
using VariableInventorySystem;

namespace FantasySurvival.SaveSystem
{
    public static class BaseFurnitureSaveCodec
    {
        private const int MaxFurnitureCount = 4096;
        private const int MaxTotalRuntimeGridCells = 262144;
        private const int MaxTotalStoredItems = 50000;

        public static BaseSaveData CreateEmptySaveData(
            bool allowAuthoredFurnitureInitialization = false)
        {
            return new BaseSaveData
            {
                formatVersion = BaseSaveData.CurrentFormatVersion,
                layoutId = BaseSaveData.FurnitureLayoutId,
                furnitureRecordCount = 0,
                furniture = new List<BaseFurnitureSaveData>(),
                allowAuthoredFurnitureInitialization = allowAuthoredFurnitureInitialization
            };
        }

        public static bool TryCapture(
            BaseFurnitureStateStore source,
            ItemDatabase itemDatabase,
            BaseFurnitureDatabase furnitureDatabase,
            out BaseSaveData saveData,
            out string error)
        {
            saveData = null;
            if (source == null)
            {
                error = "Base furniture runtime state is missing.";
                return false;
            }

            if (furnitureDatabase == null)
            {
                error = "Base furniture database is missing.";
                return false;
            }

            if (!furnitureDatabase.TryValidate(out error))
            {
                return false;
            }

            var states = new List<BaseFurnitureRuntimeState>(source.States);
            if (states.Count > MaxFurnitureCount)
            {
                error = $"Base contains more than {MaxFurnitureCount} persistent furniture records.";
                return false;
            }

            states.Sort((left, right) => string.CompareOrdinal(left.InstanceId, right.InstanceId));
            var result = CreateEmptySaveData();
            var seenIds = new HashSet<string>(StringComparer.Ordinal);
            var seenStorage = new HashSet<StandardStashViewData>(
                ReferenceComparer<StandardStashViewData>.Instance);

            foreach (BaseFurnitureRuntimeState state in states)
            {
                if (state == null || !BaseContentKey.IsValid(state.InstanceId) ||
                    !BaseContentKey.IsValid(state.DefinitionKey) || !seenIds.Add(state.InstanceId))
                {
                    error = "Base runtime state contains an invalid or duplicate furniture record.";
                    return false;
                }

                if (!furnitureDatabase.TryGet(
                        state.DefinitionKey,
                        out BaseFurnitureDefinition definition))
                {
                    error = $"Furniture '{state.InstanceId}' references unknown definition '{state.DefinitionKey}'.";
                    return false;
                }

                if (!HasExpectedStorageShape(definition, state.Storage, out error))
                {
                    error = $"Furniture '{state.InstanceId}' is incompatible with definition " +
                            $"'{state.DefinitionKey}': {error}";
                    return false;
                }

                InventoryGridSaveData storageSave = null;
                if (state.Storage != null)
                {
                    if (!seenStorage.Add(state.Storage))
                    {
                        error = $"Furniture '{state.InstanceId}' shares its storage grid with another furniture instance.";
                        return false;
                    }

                    if (!InventorySaveCodec.TryCaptureGrid(
                            state.Storage,
                            itemDatabase,
                            out storageSave,
                            out error))
                    {
                        error = $"Furniture '{state.InstanceId}' storage capture failed: {error}";
                        return false;
                    }
                }

                result.furniture.Add(new BaseFurnitureSaveData
                {
                    instanceId = state.InstanceId,
                    definitionKey = state.DefinitionKey,
                    storage = storageSave
                });
            }

            result.furnitureRecordCount = result.furniture.Count;
            saveData = result;
            error = null;
            return true;
        }

        public static bool TryRestore(
            BaseSaveData saveData,
            ItemDatabase itemDatabase,
            BaseFurnitureDatabase furnitureDatabase,
            out BaseFurnitureStateStore restored,
            out string error)
        {
            restored = null;
            if (saveData == null ||
                saveData.formatVersion != BaseSaveData.CurrentFormatVersion ||
                saveData.layoutId != BaseSaveData.FurnitureLayoutId ||
                saveData.furniture == null ||
                saveData.furnitureRecordCount < 0 ||
                saveData.furnitureRecordCount != saveData.furniture.Count ||
                saveData.furniture.Count > MaxFurnitureCount)
            {
                error = "Base save data is missing, malformed, or has an unsupported format.";
                return false;
            }

            if (furnitureDatabase == null)
            {
                error = "Base furniture database is missing.";
                return false;
            }

            if (!furnitureDatabase.TryValidate(out error))
            {
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
            for (int index = 0; index < saveData.furniture.Count; index++)
            {
                BaseFurnitureSaveData record = saveData.furniture[index];
                if (record == null || !BaseContentKey.IsValid(record.instanceId) ||
                    !BaseContentKey.IsValid(record.definitionKey) ||
                    !seenIds.Add(record.instanceId))
                {
                    error = $"Base save contains an invalid or duplicate furniture record at index {index}.";
                    return false;
                }

                if (!furnitureDatabase.TryGet(
                        record.definitionKey,
                        out BaseFurnitureDefinition definition))
                {
                    error = $"Furniture '{record.instanceId}' references unknown definition " +
                            $"'{record.definitionKey}'. Install the required content or migration.";
                    return false;
                }

                if (!HasExpectedSavedStorageShape(definition, record.storage, out error))
                {
                    error = $"Furniture '{record.instanceId}' is incompatible with definition " +
                            $"'{record.definitionKey}': {error}";
                    return false;
                }

                if (record.storage == null)
                {
                    continue;
                }

                if (!InventorySaveCodec.TryGetValidatedRestoreCost(
                        record.storage,
                        itemDefinitions,
                        out int itemCount,
                        out long runtimeGridCells,
                        out error))
                {
                    error = $"Furniture '{record.instanceId}' storage metadata is invalid: {error}";
                    return false;
                }

                totalRuntimeGridCells += runtimeGridCells;
                totalStoredItems += itemCount;
                if (totalRuntimeGridCells > MaxTotalRuntimeGridCells ||
                    totalStoredItems > MaxTotalStoredItems)
                {
                    error = "Base save exceeds the supported aggregate storage size.";
                    return false;
                }
            }

            // Allocate runtime grids only after the complete payload has passed structural and
            // aggregate-size validation. This prevents a small malformed save from forcing many
            // maximum-size grid allocations before a later record fails.
            var candidate = new BaseFurnitureStateStore();
            for (int index = 0; index < saveData.furniture.Count; index++)
            {
                BaseFurnitureSaveData record = saveData.furniture[index];
                StandardStashViewData storage = null;
                if (record.storage != null && !InventorySaveCodec.TryRestoreGrid(
                        record.storage,
                        itemDefinitions,
                        out storage,
                        out error))
                {
                    error = $"Furniture '{record.instanceId}' storage restore failed: {error}";
                    return false;
                }

                var state = new BaseFurnitureRuntimeState(
                    record.instanceId,
                    record.definitionKey,
                    storage);
                if (!candidate.TryAddRestoredState(state, out error))
                {
                    return false;
                }
            }

            restored = candidate;
            error = null;
            return true;
        }

        private static bool HasExpectedSavedStorageShape(
            BaseFurnitureDefinition definition,
            InventoryGridSaveData storage,
            out string error)
        {
            if (definition == null)
            {
                error = "Furniture definition is missing.";
                return false;
            }

            if (!definition.HasStorage)
            {
                if (storage != null)
                {
                    error = "non-storage furniture contains a storage payload.";
                    return false;
                }

                error = null;
                return true;
            }

            if (storage == null ||
                storage.width != definition.StorageWidth ||
                storage.height != definition.StorageHeight)
            {
                error = $"storage must be {definition.StorageWidth}x{definition.StorageHeight}.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool HasExpectedStorageShape(
            BaseFurnitureDefinition definition,
            StandardStashViewData storage,
            out string error)
        {
            if (definition == null)
            {
                error = "Furniture definition is missing.";
                return false;
            }

            if (!definition.HasStorage)
            {
                if (storage != null)
                {
                    error = "non-storage furniture contains a storage payload.";
                    return false;
                }

                error = null;
                return true;
            }

            if (storage == null ||
                storage.CapacityWidth != definition.StorageWidth ||
                storage.CapacityHeight != definition.StorageHeight)
            {
                error = $"storage must be {definition.StorageWidth}x{definition.StorageHeight}.";
                return false;
            }

            error = null;
            return true;
        }

        private sealed class ReferenceComparer<T> : IEqualityComparer<T> where T : class
        {
            public static readonly ReferenceComparer<T> Instance = new ReferenceComparer<T>();
            public bool Equals(T left, T right) => ReferenceEquals(left, right);
            public int GetHashCode(T value) => RuntimeHelpers.GetHashCode(value);
        }
    }
}
