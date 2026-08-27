using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using FantasySurvival.Inventory;
using VariableInventorySystem;

namespace FantasySurvival.SaveSystem
{
    public static class InventorySaveCodec
    {
        private const int RootParentRecordId = -1;
        private const int EquipmentRootSlotIndex = -1;
        private const int MaxContainerDepth = 16;
        private const int MaxItemCount = 10000;
        private const long MaxRuntimeGridCellsPerPayload = 262144;

        public static bool TryCapture(
            PlayerInventoryState source,
            ItemDatabase database,
            out PlayerItemStateSaveData saveData,
            out string error)
        {
            saveData = null;
            if (!TryBuildDefinitionIndex(database, out Dictionary<int, ItemDefinition> definitions, out error))
            {
                return false;
            }

            if (source?.Inventory == null || source.Equipment == null)
            {
                error = "Player inventory state is missing.";
                return false;
            }

            var result = new PlayerItemStateSaveData
            {
                layoutId = PlayerItemStateSaveData.FlatLayoutId,
                inventoryWidth = source.Inventory.CapacityWidth,
                inventoryHeight = source.Inventory.CapacityHeight
            };
            var context = new CaptureContext(definitions, result.items);
            if (!TryCaptureGrid(source.Inventory, RootParentRecordId, 0, context, out error))
            {
                return false;
            }

            foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
            {
                IVariableInventoryCellData item = source.Equipment.GetItem(slot);
                if (item == null)
                {
                    continue;
                }

                if (!(item is InventoryItemData inventoryItem) || !inventoryItem.Definition.CanEquipIn(slot))
                {
                    error = $"Equipment slot {slot} contains an incompatible item.";
                    return false;
                }

                if (!TryCaptureItem(
                        item,
                        source.Equipment,
                        RootParentRecordId,
                        EquipmentRootSlotIndex,
                        slot,
                        0,
                        context,
                        out error))
                {
                    return false;
                }
            }

            result.itemRecordCount = result.items.Count;
            saveData = result;
            error = null;
            return true;
        }

        public static bool TryCaptureGrid(
            StandardStashViewData source,
            ItemDatabase database,
            out InventoryGridSaveData saveData,
            out string error)
        {
            saveData = null;
            if (!TryBuildDefinitionIndex(database, out Dictionary<int, ItemDefinition> definitions, out error))
            {
                return false;
            }

            if (!HasValidGridDimensions(source, out error))
            {
                return false;
            }

            var result = new InventoryGridSaveData
            {
                layoutId = InventoryGridSaveData.FlatLayoutId,
                width = source.CapacityWidth,
                height = source.CapacityHeight
            };
            var context = new CaptureContext(definitions, result.items);
            if (!TryCaptureGrid(source, RootParentRecordId, 0, context, out error))
            {
                return false;
            }

            result.itemRecordCount = result.items.Count;
            saveData = result;
            error = null;
            return true;
        }

        public static bool TryRestore(
            PlayerItemStateSaveData saveData,
            ItemDatabase database,
            int expectedWidth,
            int expectedHeight,
            out PlayerInventoryState restored,
            out string error)
        {
            restored = null;
            if (!TryBuildDefinitionIndex(database, out Dictionary<int, ItemDefinition> definitions, out error) ||
                !HasExpectedRootDimensions(saveData, expectedWidth, expectedHeight, out error) ||
                !TryBuildRestoreContext(saveData, definitions, out RestoreContext context, out error))
            {
                return false;
            }

            if (!TryCalculateRuntimeGridCellCost(
                    expectedWidth,
                    expectedHeight,
                    context,
                    out _,
                    out error))
            {
                return false;
            }

            var inventory = new StandardStashViewData(expectedWidth, expectedHeight);
            var equipment = new EquipmentLoadoutData();
            if (!TryRestoreRecords(context.RootInventoryRecords, inventory, 0, context, out error))
            {
                return false;
            }

            foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
            {
                if (!context.EquipmentRoots.TryGetValue(slot, out InventoryItemSaveData record))
                {
                    continue;
                }

                if (!TryCreateItem(record, 0, context, out IVariableInventoryCellData item, out error) ||
                    !equipment.TryPlace(slot, item))
                {
                    if (error == null)
                    {
                        error = $"Item ID {record.definitionId} cannot be equipped in slot {slot}.";
                    }
                    return false;
                }

                context.RestoredCount++;
            }

            if (context.RestoredCount != context.RecordsById.Count)
            {
                error = "Save data contains an unreachable or cyclic container relationship.";
                return false;
            }

            restored = new PlayerInventoryState(inventory, equipment);
            error = null;
            return true;
        }

        public static bool TryRestoreGrid(
            InventoryGridSaveData saveData,
            ItemDatabase database,
            out StandardStashViewData restored,
            out string error)
        {
            if (!TryBuildDefinitionIndex(
                    database,
                    out Dictionary<int, ItemDefinition> definitions,
                    out error))
            {
                restored = null;
                return false;
            }

            return TryRestoreGrid(saveData, definitions, out restored, out error);
        }

        internal static bool TryRestoreGrid(
            InventoryGridSaveData saveData,
            Dictionary<int, ItemDefinition> definitions,
            out StandardStashViewData restored,
            out string error)
        {
            restored = null;
            if (!TryPrepareGridRestore(
                    saveData,
                    definitions,
                    out RestoreContext context,
                    out _,
                    out error))
            {
                return false;
            }

            var candidate = new StandardStashViewData(saveData.width, saveData.height);
            if (!TryRestoreRecords(context.RootInventoryRecords, candidate, 0, context, out error))
            {
                return false;
            }

            if (context.RestoredCount != context.RecordsById.Count)
            {
                error = "Storage grid data contains an unreachable or cyclic container relationship.";
                return false;
            }

            restored = candidate;
            error = null;
            return true;
        }

        internal static bool TryGetValidatedRestoreCost(
            InventoryGridSaveData saveData,
            Dictionary<int, ItemDefinition> definitions,
            out int itemCount,
            out long runtimeGridCells,
            out string error)
        {
            itemCount = 0;
            if (!TryPrepareGridRestore(
                    saveData,
                    definitions,
                    out RestoreContext context,
                    out runtimeGridCells,
                    out error))
            {
                return false;
            }

            itemCount = context.RecordsById.Count;
            error = null;
            return true;
        }

        private static bool TryPrepareGridRestore(
            InventoryGridSaveData saveData,
            Dictionary<int, ItemDefinition> definitions,
            out RestoreContext context,
            out long runtimeGridCells,
            out string error)
        {
            context = null;
            runtimeGridCells = 0;
            if (definitions == null)
            {
                error = "Validated item definition index is missing.";
                return false;
            }

            if (!HasValidSavedGridDimensions(saveData, out error))
            {
                return false;
            }

            var playerShapedPayload = new PlayerItemStateSaveData
            {
                layoutId = PlayerItemStateSaveData.FlatLayoutId,
                inventoryWidth = saveData.width,
                inventoryHeight = saveData.height,
                itemRecordCount = saveData.itemRecordCount,
                items = saveData.items
            };
            if (!TryBuildRestoreContext(
                    playerShapedPayload,
                    definitions,
                    out context,
                    out error))
            {
                return false;
            }

            if (context.EquipmentRoots.Count > 0)
            {
                error = "Storage grid data cannot contain equipment-slot roots.";
                return false;
            }

            return TryCalculateRuntimeGridCellCost(
                saveData.width,
                saveData.height,
                context,
                out runtimeGridCells,
                out error);
        }

        private static bool TryCaptureGrid(
            StandardStashViewData source,
            int parentContainerRecordId,
            int depth,
            CaptureContext context,
            out string error)
        {
            if (depth > MaxContainerDepth)
            {
                error = $"Inventory container nesting exceeds {MaxContainerDepth} levels.";
                return false;
            }

            if (source?.CellData == null || source.CapacityWidth <= 0 || source.CapacityHeight <= 0 ||
                source.CellData.Length != source.CapacityWidth * source.CapacityHeight)
            {
                error = "Inventory grid dimensions are invalid.";
                return false;
            }

            if (!context.SeenGrids.Add(source))
            {
                error = "Inventory contains a shared or cyclic container grid.";
                return false;
            }

            var occupied = new bool[source.CellData.Length];
            for (int slotIndex = 0; slotIndex < source.CellData.Length; slotIndex++)
            {
                IVariableInventoryCellData item = source.CellData[slotIndex];
                if (item == null)
                {
                    continue;
                }

                if (!TryMarkPlacement(occupied, source.CapacityWidth, source.CapacityHeight, slotIndex, item, out error) ||
                    !TryCaptureItem(
                        item,
                        source,
                        parentContainerRecordId,
                        slotIndex,
                        EquipmentSlotId.None,
                        depth,
                        context,
                        out error))
                {
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryCaptureItem(
            IVariableInventoryCellData cell,
            IVariableInventoryViewData expectedOwner,
            int parentContainerRecordId,
            int slotIndex,
            EquipmentSlotId equipmentSlot,
            int depth,
            CaptureContext context,
            out string error)
        {
            if (!(cell is InventoryItemData item))
            {
                error = "Unsupported runtime inventory item data.";
                return false;
            }

            context.ItemCount++;
            if (context.ItemCount > MaxItemCount || !context.SeenItems.Add(cell))
            {
                error = context.ItemCount > MaxItemCount
                    ? $"Inventory contains more than {MaxItemCount} items."
                    : "A runtime item is owned by more than one inventory location.";
                return false;
            }

            if (!(cell is IVariableInventoryOwnedCellData owned) ||
                !ReferenceEquals(owned.InventoryOwner, expectedOwner))
            {
                error = $"Item ID {item.Id} has an inconsistent runtime owner.";
                return false;
            }

            if (!context.Definitions.TryGetValue(item.Id, out ItemDefinition definition) ||
                !ReferenceEquals(definition, item.Definition))
            {
                error = $"Item ID {item.Id} is not backed by the active ItemDatabase.";
                return false;
            }

            if (item.Quantity <= 0 || item.Quantity > definition.MaxStackSize)
            {
                error = $"Item ID {item.Id} has invalid runtime quantity {item.Quantity}.";
                return false;
            }

            int recordId = context.NextRecordId++;
            context.Output.Add(new InventoryItemSaveData
            {
                recordId = recordId,
                parentContainerRecordId = parentContainerRecordId,
                definitionId = item.Id,
                slotIndex = slotIndex,
                equipmentSlot = (int)equipmentSlot,
                isRotated = item.IsRotate,
                quantity = item.Quantity
            });

            if (definition.IsContainer)
            {
                if (!(item is InventoryContainerItemData container) || container.CaseData == null ||
                    container.CaseData.CapacityWidth != definition.ContainerWidth ||
                    container.CaseData.CapacityHeight != definition.ContainerHeight)
                {
                    error = $"Container item {item.Id} has invalid container data.";
                    return false;
                }

                return TryCaptureGrid(container.CaseData, recordId, depth + 1, context, out error);
            }

            if (item is InventoryContainerItemData)
            {
                error = $"Standard item {item.Id} unexpectedly contains a nested inventory.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool TryRestoreRecords(
            List<InventoryItemSaveData> records,
            StandardStashViewData target,
            int depth,
            RestoreContext context,
            out string error)
        {
            if (depth > MaxContainerDepth)
            {
                error = $"Inventory container nesting exceeds {MaxContainerDepth} levels.";
                return false;
            }

            if (records == null)
            {
                error = null;
                return true;
            }

            foreach (InventoryItemSaveData record in records)
            {
                if (record.slotIndex < 0 || record.slotIndex >= target.CellData.Length)
                {
                    error = $"Item ID {record.definitionId} has an invalid slot index {record.slotIndex}.";
                    return false;
                }

                if (!TryCreateItem(record, depth, context, out IVariableInventoryCellData item, out error))
                {
                    return false;
                }

                if (!target.CheckInsert(record.slotIndex, item))
                {
                    error = $"Item ID {record.definitionId} cannot be placed at slot {record.slotIndex}.";
                    return false;
                }

                target.InsertInventoryItem(record.slotIndex, item);
                context.RestoredCount++;
            }

            error = null;
            return true;
        }

        private static bool TryCreateItem(
            InventoryItemSaveData record,
            int depth,
            RestoreContext context,
            out IVariableInventoryCellData item,
            out string error)
        {
            item = null;
            ItemDefinition definition = context.Definitions[record.definitionId];
            if (!TryResolveSavedQuantity(record, definition, out int quantity, out error) ||
                !InventoryItemDataFactory.TryCreate(definition, quantity, out item, out error))
            {
                error = $"Could not create item definition ID {record.definitionId}: {error}";
                return false;
            }

            item.IsRotate = record.isRotated;

            context.ChildrenByParent.TryGetValue(record.recordId, out List<InventoryItemSaveData> children);
            if (definition.IsContainer)
            {
                if (!(item is InventoryContainerItemData container))
                {
                    error = $"Item definition ID {record.definitionId} did not create a valid container item.";
                    return false;
                }

                if (!TryRestoreRecords(children, container.CaseData, depth + 1, context, out error))
                {
                    return false;
                }
            }
            else if (children != null && children.Count > 0)
            {
                error = $"Standard item ID {record.definitionId} has nested inventory records.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool TryBuildRestoreContext(
            PlayerItemStateSaveData saveData,
            Dictionary<int, ItemDefinition> definitions,
            out RestoreContext context,
            out string error)
        {
            context = new RestoreContext(definitions);
            if (saveData.items == null || saveData.items.Count > MaxItemCount)
            {
                error = saveData.items == null
                    ? "Save data item list is missing."
                    : $"Save data contains more than {MaxItemCount} items.";
                return false;
            }

            for (int i = 0; i < saveData.items.Count; i++)
            {
                InventoryItemSaveData record = saveData.items[i];
                if (record == null || record.recordId < 0 ||
                    record.parentContainerRecordId < RootParentRecordId ||
                    record.recordId == record.parentContainerRecordId)
                {
                    error = $"Save data contains an invalid item entry at index {i}.";
                    return false;
                }

                if (!definitions.TryGetValue(record.definitionId, out ItemDefinition definition) ||
                    context.RecordsById.ContainsKey(record.recordId))
                {
                    error = !definitions.ContainsKey(record.definitionId)
                        ? $"Save data references unknown item definition ID {record.definitionId}."
                        : $"Save data contains duplicate item record ID {record.recordId}.";
                    return false;
                }

                if (!TryResolveSavedQuantity(record, definition, out _, out error))
                {
                    error = $"Item record {record.recordId} has invalid quantity: {error}";
                    return false;
                }

                var slot = (EquipmentSlotId)record.equipmentSlot;
                if (record.parentContainerRecordId == RootParentRecordId)
                {
                    if (slot == EquipmentSlotId.None)
                    {
                        context.RootInventoryRecords.Add(record);
                    }
                    else if (!EquipmentSlotCatalog.IsValid(slot) ||
                             record.slotIndex != EquipmentRootSlotIndex ||
                             !definition.CanEquipIn(slot) ||
                             context.EquipmentRoots.ContainsKey(slot))
                    {
                        error = $"Save data contains an invalid or duplicate equipment root at item {record.recordId}.";
                        return false;
                    }
                    else
                    {
                        context.EquipmentRoots.Add(slot, record);
                    }
                }
                else
                {
                    if (slot != EquipmentSlotId.None)
                    {
                        error = $"Nested item {record.recordId} cannot declare an equipment slot.";
                        return false;
                    }

                    if (!context.ChildrenByParent.TryGetValue(record.parentContainerRecordId, out List<InventoryItemSaveData> children))
                    {
                        children = new List<InventoryItemSaveData>();
                        context.ChildrenByParent.Add(record.parentContainerRecordId, children);
                    }
                    children.Add(record);
                }

                context.RecordsById.Add(record.recordId, record);
            }

            foreach (InventoryItemSaveData record in saveData.items)
            {
                if (record.parentContainerRecordId == RootParentRecordId)
                {
                    continue;
                }

                if (!context.RecordsById.TryGetValue(record.parentContainerRecordId, out InventoryItemSaveData parent) ||
                    !definitions[parent.definitionId].IsContainer)
                {
                    error = $"Item record {record.recordId} has a missing or non-container parent.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryResolveSavedQuantity(
            InventoryItemSaveData record,
            ItemDefinition definition,
            out int quantity,
            out string error)
        {
            quantity = record.quantity == 0 ? 1 : record.quantity;
            if (quantity <= 0 || quantity > definition.MaxStackSize)
            {
                error = $"expected 1..{definition.MaxStackSize}, found {record.quantity}.";
                return false;
            }

            error = null;
            return true;
        }

        internal static bool TryBuildDefinitionIndex(
            ItemDatabase database,
            out Dictionary<int, ItemDefinition> definitions,
            out string error)
        {
            definitions = new Dictionary<int, ItemDefinition>();
            if (database == null || database.Items == null)
            {
                error = "ItemDatabase is missing.";
                return false;
            }

            for (int i = 0; i < database.Items.Count; i++)
            {
                ItemDefinition definition = database.Items[i];
                if (definition == null || definition.Id <= 0 || definitions.ContainsKey(definition.Id))
                {
                    error = definition == null
                        ? $"ItemDatabase contains an empty entry at index {i}."
                        : $"ItemDatabase contains invalid or duplicate item ID {definition.Id}.";
                    return false;
                }

                if (!definition.TryValidateInventoryShape(out error))
                {
                    return false;
                }

                definitions.Add(definition.Id, definition);
            }

            error = null;
            return true;
        }

        private static bool TryCalculateRuntimeGridCellCost(
            int rootWidth,
            int rootHeight,
            RestoreContext context,
            out long runtimeGridCells,
            out string error)
        {
            runtimeGridCells = 0;
            if (context == null)
            {
                error = "Inventory restore context is missing.";
                return false;
            }

            if (!InventoryGridConstraints.TryValidateDimensions(rootWidth, rootHeight, out error))
            {
                return false;
            }

            runtimeGridCells = (long)rootWidth * rootHeight;
            foreach (InventoryItemSaveData record in context.RecordsById.Values)
            {
                ItemDefinition definition = context.Definitions[record.definitionId];
                if (!definition.IsContainer)
                {
                    continue;
                }

                runtimeGridCells += (long)definition.ContainerWidth * definition.ContainerHeight;
                if (runtimeGridCells > MaxRuntimeGridCellsPerPayload)
                {
                    error = $"Inventory payload requires more than " +
                            $"{MaxRuntimeGridCellsPerPayload} runtime grid cells.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool HasExpectedRootDimensions(
            PlayerItemStateSaveData saveData,
            int expectedWidth,
            int expectedHeight,
            out string error)
        {
            if (saveData == null || saveData.layoutId != PlayerItemStateSaveData.FlatLayoutId)
            {
                error = "Player item save data is missing or has an unsupported layout ID.";
                return false;
            }

            if (saveData.items == null || saveData.itemRecordCount < 0 ||
                saveData.itemRecordCount != saveData.items.Count)
            {
                error = "Player item save data count does not match its payload.";
                return false;
            }

            if (!InventoryGridConstraints.TryValidateDimensions(
                    expectedWidth,
                    expectedHeight,
                    out error) ||
                saveData.inventoryWidth != expectedWidth || saveData.inventoryHeight != expectedHeight)
            {
                if (error == null)
                {
                    error = $"Inventory dimensions {saveData.inventoryWidth}x{saveData.inventoryHeight} " +
                            $"do not match expected {expectedWidth}x{expectedHeight}.";
                }
                return false;
            }

            error = null;
            return true;
        }

        private static bool HasValidGridDimensions(
            StandardStashViewData grid,
            out string error)
        {
            if (grid == null || grid.CellData == null)
            {
                error = "Inventory grid is missing its cell data.";
                return false;
            }

            if (!InventoryGridConstraints.TryValidateDimensions(
                    grid.CapacityWidth,
                    grid.CapacityHeight,
                    out error))
            {
                return false;
            }

            if (grid.CellData.Length != grid.CapacityWidth * grid.CapacityHeight)
            {
                error = "Inventory grid dimensions do not match its cell data length.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool HasValidSavedGridDimensions(
            InventoryGridSaveData saveData,
            out string error)
        {
            if (saveData == null || saveData.layoutId != InventoryGridSaveData.FlatLayoutId)
            {
                error = "Storage grid save data is missing or uses an unsupported layout ID.";
                return false;
            }

            if (!InventoryGridConstraints.TryValidateDimensions(
                    saveData.width,
                    saveData.height,
                    out error))
            {
                return false;
            }

            if (saveData.items == null || saveData.itemRecordCount < 0 ||
                saveData.itemRecordCount != saveData.items.Count ||
                saveData.items.Count > MaxItemCount)
            {
                error = "Storage grid save data is malformed or exceeds the supported item count.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool TryMarkPlacement(
            bool[] occupied,
            int gridWidth,
            int gridHeight,
            int slotIndex,
            IVariableInventoryCellData item,
            out string error)
        {
            if (slotIndex < 0 || slotIndex >= occupied.Length || item.Width <= 0 || item.Height <= 0)
            {
                error = $"Inventory item has an invalid placement at slot {slotIndex}.";
                return false;
            }

            int width = item.IsRotate ? item.Height : item.Width;
            int height = item.IsRotate ? item.Width : item.Height;
            int startX = slotIndex % gridWidth;
            int startY = slotIndex / gridWidth;
            if (startX + width > gridWidth || startY + height > gridHeight)
            {
                error = $"Inventory item at slot {slotIndex} extends outside its grid.";
                return false;
            }

            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    int index = slotIndex + x + y * gridWidth;
                    if (occupied[index])
                    {
                        error = $"Inventory items overlap at slot {index}.";
                        return false;
                    }
                    occupied[index] = true;
                }
            }

            error = null;
            return true;
        }

        private sealed class CaptureContext
        {
            public readonly Dictionary<int, ItemDefinition> Definitions;
            public readonly List<InventoryItemSaveData> Output;
            public readonly HashSet<StandardStashViewData> SeenGrids =
                new HashSet<StandardStashViewData>(ReferenceComparer<StandardStashViewData>.Instance);
            public readonly HashSet<IVariableInventoryCellData> SeenItems =
                new HashSet<IVariableInventoryCellData>(ReferenceComparer<IVariableInventoryCellData>.Instance);
            public int ItemCount;
            public int NextRecordId;

            public CaptureContext(Dictionary<int, ItemDefinition> definitions, List<InventoryItemSaveData> output)
            {
                Definitions = definitions;
                Output = output;
            }
        }

        private sealed class RestoreContext
        {
            public readonly Dictionary<int, ItemDefinition> Definitions;
            public readonly Dictionary<int, InventoryItemSaveData> RecordsById =
                new Dictionary<int, InventoryItemSaveData>();
            public readonly Dictionary<int, List<InventoryItemSaveData>> ChildrenByParent =
                new Dictionary<int, List<InventoryItemSaveData>>();
            public readonly List<InventoryItemSaveData> RootInventoryRecords =
                new List<InventoryItemSaveData>();
            public readonly Dictionary<EquipmentSlotId, InventoryItemSaveData> EquipmentRoots =
                new Dictionary<EquipmentSlotId, InventoryItemSaveData>();
            public int RestoredCount;

            public RestoreContext(Dictionary<int, ItemDefinition> definitions)
            {
                Definitions = definitions;
            }
        }

        private sealed class ReferenceComparer<T> : IEqualityComparer<T> where T : class
        {
            public static readonly ReferenceComparer<T> Instance = new ReferenceComparer<T>();
            public bool Equals(T x, T y) => ReferenceEquals(x, y);
            public int GetHashCode(T value) => RuntimeHelpers.GetHashCode(value);
        }
    }
}
