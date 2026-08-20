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
        private const int MaxContainerDepth = 16;
        private const int MaxItemCount = 10000;

        public static bool TryCapture(
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

            if (source == null)
            {
                error = "Player inventory data is missing.";
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
            return true;
        }

        public static bool TryRestore(
            InventoryGridSaveData saveData,
            ItemDatabase database,
            int expectedWidth,
            int expectedHeight,
            out StandardStashViewData restored,
            out string error)
        {
            restored = null;
            if (!TryBuildDefinitionIndex(database, out Dictionary<int, ItemDefinition> definitions, out error))
            {
                return false;
            }

            if (!HasExpectedRootDimensions(saveData, expectedWidth, expectedHeight, out error))
            {
                return false;
            }

            if (!TryBuildRestoreContext(saveData, definitions, out RestoreContext context, out error))
            {
                return false;
            }

            var candidate = new StandardStashViewData(expectedWidth, expectedHeight);
            if (!TryRestoreChildren(RootParentRecordId, candidate, 0, context, out error))
            {
                return false;
            }

            if (context.RestoredCount != context.RecordsById.Count)
            {
                error = "Save data contains an unreachable or cyclic container relationship.";
                return false;
            }

            restored = candidate;
            error = null;
            return true;
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

            if (source.CellData == null || source.CapacityWidth <= 0 || source.CapacityHeight <= 0 ||
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
                IVariableInventoryCellData cell = source.CellData[slotIndex];
                if (cell == null)
                {
                    continue;
                }

                if (!(cell is InventoryItemData item))
                {
                    error = $"Unsupported inventory item data at slot {slotIndex}.";
                    return false;
                }

                context.ItemCount++;
                if (context.ItemCount > MaxItemCount)
                {
                    error = $"Inventory contains more than {MaxItemCount} items.";
                    return false;
                }

                if (!context.SeenItems.Add(cell))
                {
                    error = $"Inventory item at slot {slotIndex} is referenced more than once.";
                    return false;
                }

                if (!context.Definitions.TryGetValue(item.Id, out ItemDefinition definition) ||
                    !ReferenceEquals(definition, item.Definition))
                {
                    error = $"Inventory item at slot {slotIndex} is not backed by the active ItemDatabase.";
                    return false;
                }

                if (!TryMarkPlacement(occupied, source.CapacityWidth, source.CapacityHeight, slotIndex, item, out error))
                {
                    return false;
                }

                int recordId = context.NextRecordId++;
                context.Output.Add(new InventoryItemSaveData
                {
                    recordId = recordId,
                    parentContainerRecordId = parentContainerRecordId,
                    definitionId = item.Id,
                    slotIndex = slotIndex,
                    isRotated = item.IsRotate
                });

                if (definition.IsContainer)
                {
                    if (!(item is InventoryContainerItemData container) || container.CaseData == null)
                    {
                        error = $"Container item {item.Id} at slot {slotIndex} has no container data.";
                        return false;
                    }

                    if (container.CaseData.CapacityWidth != definition.ContainerWidth ||
                        container.CaseData.CapacityHeight != definition.ContainerHeight)
                    {
                        error = $"Container item {item.Id} has dimensions that do not match its definition.";
                        return false;
                    }

                    if (!TryCaptureGrid(container.CaseData, recordId, depth + 1, context, out error))
                    {
                        return false;
                    }
                }
                else if (item is InventoryContainerItemData)
                {
                    error = $"Standard item {item.Id} unexpectedly contains a nested inventory.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryRestoreChildren(
            int parentRecordId,
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

            if (!context.ChildrenByParent.TryGetValue(parentRecordId, out List<InventoryItemSaveData> children))
            {
                error = null;
                return true;
            }

            for (int i = 0; i < children.Count; i++)
            {
                InventoryItemSaveData record = children[i];
                ItemDefinition definition = context.Definitions[record.definitionId];
                IVariableInventoryCellData item;
                try
                {
                    item = InventoryItemDataFactory.Create(definition);
                    item.IsRotate = record.isRotated;
                }
                catch (Exception exception)
                {
                    error = $"Could not create item definition ID {record.definitionId}: {exception.Message}";
                    return false;
                }

                if (definition.IsContainer)
                {
                    if (!(item is InventoryContainerItemData container))
                    {
                        error = $"Item definition ID {record.definitionId} did not create a container item.";
                        return false;
                    }

                    if (!TryRestoreChildren(record.recordId, container.CaseData, depth + 1, context, out error))
                    {
                        return false;
                    }
                }
                else if (context.ChildrenByParent.TryGetValue(record.recordId, out List<InventoryItemSaveData> nested) &&
                         nested.Count > 0)
                {
                    error = $"Standard item ID {record.definitionId} has nested inventory records.";
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

        private static bool TryBuildRestoreContext(
            InventoryGridSaveData saveData,
            Dictionary<int, ItemDefinition> definitions,
            out RestoreContext context,
            out string error)
        {
            context = new RestoreContext(definitions);
            if (saveData.items == null)
            {
                error = "Save data inventory item list is missing.";
                return false;
            }

            if (saveData.items.Count > MaxItemCount)
            {
                error = $"Save data contains more than {MaxItemCount} items.";
                return false;
            }

            for (int i = 0; i < saveData.items.Count; i++)
            {
                InventoryItemSaveData record = saveData.items[i];
                if (record == null)
                {
                    error = $"Save data contains an empty item entry at index {i}.";
                    return false;
                }

                if (record.recordId < 0 || record.parentContainerRecordId < RootParentRecordId ||
                    record.recordId == record.parentContainerRecordId)
                {
                    error = $"Save data contains invalid relationship IDs at item index {i}.";
                    return false;
                }

                if (!definitions.ContainsKey(record.definitionId))
                {
                    error = $"Save data references unknown item definition ID {record.definitionId}.";
                    return false;
                }

                if (context.RecordsById.ContainsKey(record.recordId))
                {
                    error = $"Save data contains duplicate item record ID {record.recordId}.";
                    return false;
                }

                context.RecordsById.Add(record.recordId, record);
                if (!context.ChildrenByParent.TryGetValue(record.parentContainerRecordId, out List<InventoryItemSaveData> siblings))
                {
                    siblings = new List<InventoryItemSaveData>();
                    context.ChildrenByParent.Add(record.parentContainerRecordId, siblings);
                }
                siblings.Add(record);
            }

            foreach (InventoryItemSaveData record in saveData.items)
            {
                if (record.parentContainerRecordId == RootParentRecordId)
                {
                    continue;
                }

                if (!context.RecordsById.TryGetValue(record.parentContainerRecordId, out InventoryItemSaveData parent))
                {
                    error = $"Save data item record {record.recordId} references missing parent {record.parentContainerRecordId}.";
                    return false;
                }

                if (!definitions[parent.definitionId].IsContainer)
                {
                    error = $"Save data item record {record.recordId} has a non-container parent.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryBuildDefinitionIndex(
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
                if (definition == null)
                {
                    error = $"ItemDatabase contains an empty entry at index {i}.";
                    return false;
                }

                if (definition.Id <= 0)
                {
                    error = $"ItemDatabase contains invalid item ID {definition.Id}.";
                    return false;
                }

                if (definitions.ContainsKey(definition.Id))
                {
                    error = $"ItemDatabase contains duplicate item ID {definition.Id}.";
                    return false;
                }

                definitions.Add(definition.Id, definition);
            }

            error = null;
            return true;
        }

        private static bool HasExpectedRootDimensions(
            InventoryGridSaveData saveData,
            int expectedWidth,
            int expectedHeight,
            out string error)
        {
            if (saveData == null)
            {
                error = "Inventory save data is missing.";
                return false;
            }

            if (saveData.layoutId != InventoryGridSaveData.FlatLayoutId)
            {
                error = "Inventory save data has a missing or unsupported layout ID.";
                return false;
            }

            if (saveData.items == null || saveData.itemRecordCount < 0 ||
                saveData.itemRecordCount != saveData.items.Count)
            {
                error = "Inventory save data item count does not match its payload.";
                return false;
            }

            if (expectedWidth <= 0 || expectedHeight <= 0 ||
                saveData.width != expectedWidth || saveData.height != expectedHeight)
            {
                error = $"Inventory dimensions {saveData.width}x{saveData.height} do not match expected {expectedWidth}x{expectedHeight}.";
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
                }
            }

            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    occupied[slotIndex + x + y * gridWidth] = true;
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
