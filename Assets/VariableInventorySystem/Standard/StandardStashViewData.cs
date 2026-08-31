using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace VariableInventorySystem
{
    public class StandardStashViewData : IVariableInventoryViewData
    {
        private const int MaxRepackSearchNodes = 500000;
        private const int MaxInventoryDimension = 256;
        private const int MaxInventoryCellCount = 65536;

        private sealed class ResizeItem
        {
            public IVariableInventoryCellData Item;
            public int SourceIndex;
            public bool OriginalRotation;
            public int Area;
            public int LongestSide;
        }

        private struct ResizePlacement
        {
            public int CellIndex;
            public bool IsRotated;

            public ResizePlacement(int cellIndex, bool isRotated)
            {
                CellIndex = cellIndex;
                IsRotated = isRotated;
            }
        }

        private sealed class ReferenceCellComparer : IEqualityComparer<IVariableInventoryCellData>
        {
            public static readonly ReferenceCellComparer Instance = new ReferenceCellComparer();

            public bool Equals(
                IVariableInventoryCellData first,
                IVariableInventoryCellData second)
            {
                return ReferenceEquals(first, second);
            }

            public int GetHashCode(IVariableInventoryCellData item)
            {
                return item == null ? 0 : RuntimeHelpers.GetHashCode(item);
            }
        }

        public sealed class HeightResizeReceipt
        {
            internal StandardStashViewData Owner;
            internal int BeforeHeight;
            internal int AfterHeight;
            internal IVariableInventoryCellData[] BeforeCells;
            internal IVariableInventoryCellData[] AfterCells;
            internal Dictionary<IVariableInventoryCellData, bool> BeforeRotations;
            internal Dictionary<IVariableInventoryCellData, bool> AfterRotations;
            internal bool IsConsumed;
        }

        public bool IsDirty { get; set; }
        public IVariableInventoryCellData[] CellData { get; private set; }

        public int CapacityWidth { get; }
        public int CapacityHeight { get; private set; }

        bool[] mask;

        public StandardStashViewData(int capacityWidth, int capacityHeight)
            : this(new IVariableInventoryCellData[capacityWidth * capacityHeight], capacityWidth, capacityHeight)
        {
        }

        public StandardStashViewData(IVariableInventoryCellData[] cellData, int capacityWidth, int capacityHeight)
        {
            Debug.Assert(cellData.Length == capacityWidth * capacityHeight);

            IsDirty = true;
            CellData = cellData;
            CapacityWidth = capacityWidth;
            CapacityHeight = capacityHeight;

            AttachInitialOwners();
            UpdateMask();
        }

        public virtual int? GetId(IVariableInventoryCellData cellData)
        {
            for (var i = 0; i < CellData.Length; i++)
            {
                if (CellData[i] == cellData)
                {
                    return i;
                }
            }

            return null;
        }

        public virtual int? GetInsertableId(IVariableInventoryCellData cellData)
        {
            for (var i = 0; i < mask.Length; i++)
            {
                if (!mask[i] && CheckInsert(i, cellData))
                {
                    return i;
                }
            }

            return null;
        }

        public virtual void InsertInventoryItem(int id, VariableInventorySystem.IVariableInventoryCellData cellData)
        {
            if (id < 0 || id >= CellData.Length)
            {
                throw new ArgumentOutOfRangeException(nameof(id));
            }

            var previous = CellData[id];
            if (ReferenceEquals(previous, cellData))
            {
                return;
            }

            if (cellData != null)
            {
                if (GetId(cellData).HasValue)
                {
                    throw new InvalidOperationException("The item is already present in this inventory grid.");
                }

                if (cellData is IVariableInventoryOwnedCellData incoming && incoming.InventoryOwner != null)
                {
                    throw new InvalidOperationException("The item already belongs to another inventory container.");
                }
            }

            if (previous is IVariableInventoryOwnedCellData outgoing &&
                !outgoing.TryChangeInventoryOwner(this, null))
            {
                throw new InvalidOperationException("The item ownership does not match this inventory grid.");
            }

            if (cellData is IVariableInventoryOwnedCellData owned &&
                !owned.TryChangeInventoryOwner(null, this))
            {
                if (previous is IVariableInventoryOwnedCellData rollback)
                {
                    rollback.TryChangeInventoryOwner(null, this);
                }

                throw new InvalidOperationException("Could not attach the item to this inventory grid.");
            }

            CellData[id] = cellData;
            IsDirty = true;

            UpdateMask();
        }

        public virtual bool CheckInsert(int id, VariableInventorySystem.IVariableInventoryCellData cellData)
        {
            if (id < 0 || id >= CellData.Length || cellData == null)
            {
                return false;
            }

            if (cellData is IVariableInventoryOwnedCellData owned && owned.InventoryOwner != null)
            {
                return false;
            }

            var (width, height) = GetRotateSize(cellData);

            // check width
            if ((id % CapacityWidth) + (width - 1) >= CapacityWidth)
            {
                return false;
            }

            // check height
            if (id + ((height - 1) * CapacityWidth) >= CellData.Length)
            {
                return false;
            }

            for (var i = 0; i < width; i++)
            {
                for (var t = 0; t < height; t++)
                {
                    if (mask[id + i + (t * CapacityWidth)])
                    {
                        return false;
                    }
                }
            }

            return true;
        }

        /// <summary>
        /// Atomically changes only the row count when the caller still observes the
        /// expected current height. A shrinking grid first keeps every placement that
        /// still fits, then deterministically repacks when necessary. Existing item
        /// instances and ownership stay intact.
        /// </summary>
        public bool TryResizeHeight(
            int expectedCurrentHeight,
            int newHeight,
            out string error)
        {
            return TryResizeHeight(
                expectedCurrentHeight,
                newHeight,
                out _,
                out error);
        }

        public bool TryResizeHeight(
            int expectedCurrentHeight,
            int newHeight,
            out HeightResizeReceipt receipt,
            out string error)
        {
            return TryResizeHeightInternal(
                expectedCurrentHeight,
                newHeight,
                null,
                out _,
                out _,
                out receipt,
                out error);
        }

        /// <summary>
        /// Previews the target layout with one external item included as reserved space.
        /// Current placements are preserved when they and the reserved item already fit;
        /// otherwise every item is deterministically repacked. The reserved item is not
        /// inserted or mutated, so the caller can complete a cross-container transaction
        /// only after the full layout has been proven possible.
        /// </summary>
        public bool TryResizeHeightReservingItem(
            int expectedCurrentHeight,
            int newHeight,
            IVariableInventoryCellData reservedItem,
            out int reservedCellIndex,
            out bool reservedRotation,
            out HeightResizeReceipt receipt,
            out string error)
        {
            if (reservedItem == null)
            {
                reservedCellIndex = -1;
                reservedRotation = false;
                receipt = null;
                error = "The item whose space must be reserved is missing.";
                return false;
            }

            return TryResizeHeightInternal(
                expectedCurrentHeight,
                newHeight,
                reservedItem,
                out reservedCellIndex,
                out reservedRotation,
                out receipt,
                out error);
        }

        private bool TryResizeHeightInternal(
            int expectedCurrentHeight,
            int newHeight,
            IVariableInventoryCellData reservedItem,
            out int reservedCellIndex,
            out bool reservedRotation,
            out HeightResizeReceipt receipt,
            out string error)
        {
            reservedCellIndex = -1;
            reservedRotation = false;
            receipt = null;
            if (CapacityHeight != expectedCurrentHeight)
            {
                error = $"Inventory height changed from the expected {expectedCurrentHeight} " +
                        $"to {CapacityHeight}.";
                return false;
            }

            if (newHeight <= 0 || newHeight > MaxInventoryDimension ||
                CapacityWidth <= 0 || CapacityWidth > MaxInventoryDimension)
            {
                error = $"Inventory grid {CapacityWidth}x{newHeight} exceeds the supported " +
                        $"{MaxInventoryDimension}x{MaxInventoryDimension} dimensions.";
                return false;
            }

            long newCellCount = (long)CapacityWidth * newHeight;
            if (newCellCount <= 0 || newCellCount > MaxInventoryCellCount)
            {
                error = $"Inventory grid {CapacityWidth}x{newHeight} exceeds the supported " +
                        $"{MaxInventoryCellCount}-cell limit.";
                return false;
            }

            if (newHeight == CapacityHeight && reservedItem == null)
            {
                error = null;
                return true;
            }

            if (!TryCollectResizeItems(out List<ResizeItem> items, out error))
            {
                return false;
            }

            ResizeItem reservedResizeItem = null;
            if (reservedItem != null)
            {
                if (GetId(reservedItem).HasValue)
                {
                    error = "The reserved item is already present in this inventory grid.";
                    return false;
                }

                int reservedWidth = reservedItem.Width;
                int reservedHeight = reservedItem.Height;
                if (reservedWidth <= 0 || reservedHeight <= 0)
                {
                    error = $"The reserved item has an invalid " +
                            $"{reservedWidth}x{reservedHeight} footprint.";
                    return false;
                }

                long reservedArea = (long)reservedWidth * reservedHeight;
                if (reservedArea > int.MaxValue)
                {
                    error = "The reserved item is too large to repack.";
                    return false;
                }

                reservedResizeItem = new ResizeItem
                {
                    Item = reservedItem,
                    SourceIndex = CellData.Length,
                    OriginalRotation = reservedItem.IsRotate,
                    Area = (int)reservedArea,
                    LongestSide = Math.Max(reservedWidth, reservedHeight)
                };
            }

            var placements = new Dictionary<IVariableInventoryCellData, ResizePlacement>(
                ReferenceCellComparer.Instance);
            var candidateMask = new bool[(int)newCellCount];
            bool keptCurrentPlacements =
                TryKeepCurrentPlacements(items, newHeight, candidateMask, placements);
            if (keptCurrentPlacements && reservedResizeItem != null)
            {
                if (TryPlaceFirstAvailable(
                        reservedResizeItem,
                        newHeight,
                        candidateMask,
                        out ResizePlacement reservation))
                {
                    placements.Add(reservedItem, reservation);
                }
                else
                {
                    keptCurrentPlacements = false;
                }
            }

            if (!keptCurrentPlacements)
            {
                Array.Clear(candidateMask, 0, candidateMask.Length);
                placements.Clear();
                List<ResizeItem> plannedItems = items;
                if (reservedResizeItem != null)
                {
                    plannedItems = new List<ResizeItem>(items.Count + 1);
                    plannedItems.AddRange(items);
                    plannedItems.Add(reservedResizeItem);
                }

                if (!TryBuildRepackedLayout(
                        plannedItems,
                        newHeight,
                        candidateMask,
                        placements,
                        out error))
                {
                    return false;
                }
            }

            var candidateCells = new IVariableInventoryCellData[(int)newCellCount];
            foreach (ResizeItem resizeItem in items)
            {
                ResizePlacement placement = placements[resizeItem.Item];
                candidateCells[placement.CellIndex] = resizeItem.Item;
            }

            if (!TryApplyPlannedRotations(items, placements, out error))
            {
                return false;
            }

            if (reservedResizeItem != null)
            {
                ResizePlacement reservation = placements[reservedItem];
                reservedCellIndex = reservation.CellIndex;
                reservedRotation = reservation.IsRotated;
            }

            var beforeRotations = new Dictionary<IVariableInventoryCellData, bool>(
                ReferenceCellComparer.Instance);
            var afterRotations = new Dictionary<IVariableInventoryCellData, bool>(
                ReferenceCellComparer.Instance);
            foreach (ResizeItem resizeItem in items)
            {
                beforeRotations.Add(resizeItem.Item, resizeItem.OriginalRotation);
                afterRotations.Add(
                    resizeItem.Item,
                    placements[resizeItem.Item].IsRotated);
            }

            receipt = new HeightResizeReceipt
            {
                Owner = this,
                BeforeHeight = CapacityHeight,
                AfterHeight = newHeight,
                BeforeCells = (IVariableInventoryCellData[])CellData.Clone(),
                AfterCells = (IVariableInventoryCellData[])candidateCells.Clone(),
                BeforeRotations = beforeRotations,
                AfterRotations = afterRotations
            };
            CellData = candidateCells;
            CapacityHeight = newHeight;
            UpdateMask();
            IsDirty = true;
            error = null;
            return true;
        }

        public bool TryRestoreHeightResize(HeightResizeReceipt receipt, out string error)
        {
            if (receipt == null || !ReferenceEquals(receipt.Owner, this) || receipt.IsConsumed)
            {
                error = "The inventory resize receipt is missing, foreign, or already consumed.";
                return false;
            }

            if (CapacityHeight != receipt.AfterHeight ||
                CellData.Length != receipt.AfterCells.Length)
            {
                error = "Inventory capacity changed after the backpack was removed.";
                return false;
            }

            for (int index = 0; index < CellData.Length; index++)
            {
                if (!ReferenceEquals(CellData[index], receipt.AfterCells[index]))
                {
                    error = "Inventory contents moved after the backpack was removed.";
                    return false;
                }
            }

            foreach (KeyValuePair<IVariableInventoryCellData, bool> rotation in receipt.AfterRotations)
            {
                if (rotation.Key.IsRotate != rotation.Value ||
                    (rotation.Key is IVariableInventoryOwnedCellData owned &&
                     !ReferenceEquals(owned.InventoryOwner, this)))
                {
                    error = "Inventory item rotation or ownership changed after the backpack was removed.";
                    return false;
                }
            }

            var changed = new List<KeyValuePair<IVariableInventoryCellData, bool>>();
            try
            {
                foreach (KeyValuePair<IVariableInventoryCellData, bool> rotation in receipt.BeforeRotations)
                {
                    if (rotation.Key.IsRotate == rotation.Value)
                    {
                        continue;
                    }

                    changed.Add(new KeyValuePair<IVariableInventoryCellData, bool>(
                        rotation.Key,
                        rotation.Key.IsRotate));
                    rotation.Key.IsRotate = rotation.Value;
                }
            }
            catch (Exception exception)
            {
                for (int index = changed.Count - 1; index >= 0; index--)
                {
                    changed[index].Key.IsRotate = changed[index].Value;
                }

                error = $"Could not restore the original item rotations: {exception.Message}";
                return false;
            }

            CellData = (IVariableInventoryCellData[])receipt.BeforeCells.Clone();
            CapacityHeight = receipt.BeforeHeight;
            UpdateMask();
            IsDirty = true;
            receipt.IsConsumed = true;
            error = null;
            return true;
        }

        private bool TryCollectResizeItems(out List<ResizeItem> items, out string error)
        {
            items = new List<ResizeItem>();
            var seen = new HashSet<IVariableInventoryCellData>(ReferenceCellComparer.Instance);
            var occupied = new bool[CellData.Length];
            long totalArea = 0;

            for (int sourceIndex = 0; sourceIndex < CellData.Length; sourceIndex++)
            {
                IVariableInventoryCellData item = CellData[sourceIndex];
                if (item == null)
                {
                    continue;
                }

                if (!seen.Add(item))
                {
                    error = $"The same item is referenced by multiple inventory slots " +
                            $"while resizing at slot {sourceIndex}.";
                    return false;
                }

                if (item is IVariableInventoryOwnedCellData owned &&
                    !ReferenceEquals(owned.InventoryOwner, this))
                {
                    error = $"The item at slot {sourceIndex} is not owned by this inventory.";
                    return false;
                }

                int unrotatedWidth = item.Width;
                int unrotatedHeight = item.Height;
                if (unrotatedWidth <= 0 || unrotatedHeight <= 0)
                {
                    error = $"The item at slot {sourceIndex} has an invalid " +
                            $"{unrotatedWidth}x{unrotatedHeight} footprint.";
                    return false;
                }

                long itemArea = (long)unrotatedWidth * unrotatedHeight;
                if (itemArea > int.MaxValue)
                {
                    error = $"The item at slot {sourceIndex} is too large to repack.";
                    return false;
                }

                GetFootprint(item, item.IsRotate, out int width, out int height);
                if (!TryMarkPlacement(
                        occupied,
                        CapacityHeight,
                        sourceIndex,
                        width,
                        height))
                {
                    error = $"The item at slot {sourceIndex} is outside or overlaps another " +
                            $"item in the current {CapacityWidth}x{CapacityHeight} inventory.";
                    return false;
                }

                totalArea += itemArea;
                if (totalArea > CellData.Length)
                {
                    error = "The current inventory contains more item cells than its capacity.";
                    return false;
                }

                items.Add(new ResizeItem
                {
                    Item = item,
                    SourceIndex = sourceIndex,
                    OriginalRotation = item.IsRotate,
                    Area = (int)itemArea,
                    LongestSide = Math.Max(unrotatedWidth, unrotatedHeight)
                });
            }

            error = null;
            return true;
        }

        private bool TryKeepCurrentPlacements(
            IReadOnlyList<ResizeItem> items,
            int targetHeight,
            bool[] occupied,
            IDictionary<IVariableInventoryCellData, ResizePlacement> placements)
        {
            foreach (ResizeItem resizeItem in items)
            {
                GetFootprint(
                    resizeItem.Item,
                    resizeItem.OriginalRotation,
                    out int width,
                    out int height);
                if (!TryMarkPlacement(
                        occupied,
                        targetHeight,
                        resizeItem.SourceIndex,
                        width,
                        height))
                {
                    return false;
                }

                placements.Add(
                    resizeItem.Item,
                    new ResizePlacement(resizeItem.SourceIndex, resizeItem.OriginalRotation));
            }

            return true;
        }

        private bool TryBuildRepackedLayout(
            List<ResizeItem> items,
            int targetHeight,
            bool[] occupied,
            IDictionary<IVariableInventoryCellData, ResizePlacement> placements,
            out string error)
        {
            long totalArea = items.Sum(item => (long)item.Area);
            if (totalArea > occupied.Length)
            {
                error = $"The items require {totalArea} cells, but the resized inventory only " +
                        $"contains {occupied.Length}.";
                return false;
            }

            var ordered = items
                .OrderByDescending(item => item.Area)
                .ThenByDescending(item => item.LongestSide)
                .ThenBy(item => item.SourceIndex)
                .ToList();

            if (TryGreedyRepack(ordered, targetHeight, occupied, placements))
            {
                error = null;
                return true;
            }

            Array.Clear(occupied, 0, occupied.Length);
            placements.Clear();
            int visitedNodes = 0;
            bool searchLimitReached = false;
            if (TryExactRepack(
                    ordered,
                    0,
                    targetHeight,
                    occupied,
                    placements,
                    ref visitedNodes,
                    ref searchLimitReached))
            {
                error = null;
                return true;
            }

            error = searchLimitReached
                ? $"The items could not be safely repacked before the deterministic " +
                  $"{MaxRepackSearchNodes}-state search limit. Keep the backpack equipped or " +
                  "free more base-inventory space."
                : $"The items cannot fit in the resized {CapacityWidth}x{targetHeight} inventory, " +
                  "even when item rotation is allowed.";
            return false;
        }

        private bool TryGreedyRepack(
            IReadOnlyList<ResizeItem> ordered,
            int targetHeight,
            bool[] occupied,
            IDictionary<IVariableInventoryCellData, ResizePlacement> placements)
        {
            foreach (ResizeItem resizeItem in ordered)
            {
                if (!TryPlaceFirstAvailable(
                        resizeItem,
                        targetHeight,
                        occupied,
                        out ResizePlacement placement))
                {
                    Array.Clear(occupied, 0, occupied.Length);
                    placements.Clear();
                    return false;
                }

                placements.Add(resizeItem.Item, placement);
            }

            return true;
        }

        private bool TryExactRepack(
            IReadOnlyList<ResizeItem> ordered,
            int itemIndex,
            int targetHeight,
            bool[] occupied,
            IDictionary<IVariableInventoryCellData, ResizePlacement> placements,
            ref int visitedNodes,
            ref bool searchLimitReached)
        {
            if (itemIndex >= ordered.Count)
            {
                return true;
            }

            if (visitedNodes >= MaxRepackSearchNodes)
            {
                searchLimitReached = true;
                return false;
            }

            ResizeItem resizeItem = ordered[itemIndex];
            int rotationCount = resizeItem.Item.Width == resizeItem.Item.Height ? 1 : 2;
            for (int rotationIndex = 0; rotationIndex < rotationCount; rotationIndex++)
            {
                bool isRotated = rotationIndex == 0
                    ? resizeItem.OriginalRotation
                    : !resizeItem.OriginalRotation;
                GetFootprint(resizeItem.Item, isRotated, out int width, out int height);
                if (width > CapacityWidth || height > targetHeight)
                {
                    continue;
                }

                int maxX = CapacityWidth - width;
                int maxY = targetHeight - height;
                for (int y = 0; y <= maxY; y++)
                {
                    for (int x = 0; x <= maxX; x++)
                    {
                        int cellIndex = x + y * CapacityWidth;
                        if (!CanPlace(occupied, cellIndex, width, height))
                        {
                            continue;
                        }

                        visitedNodes++;
                        MarkPlacement(occupied, cellIndex, width, height, true);
                        placements[resizeItem.Item] = new ResizePlacement(cellIndex, isRotated);
                        if (TryExactRepack(
                                ordered,
                                itemIndex + 1,
                                targetHeight,
                                occupied,
                                placements,
                                ref visitedNodes,
                                ref searchLimitReached))
                        {
                            return true;
                        }

                        placements.Remove(resizeItem.Item);
                        MarkPlacement(occupied, cellIndex, width, height, false);
                        if (searchLimitReached)
                        {
                            return false;
                        }
                    }
                }
            }

            return false;
        }

        private bool TryPlaceFirstAvailable(
            ResizeItem resizeItem,
            int targetHeight,
            bool[] occupied,
            out ResizePlacement placement)
        {
            int rotationCount = resizeItem.Item.Width == resizeItem.Item.Height ? 1 : 2;
            for (int rotationIndex = 0; rotationIndex < rotationCount; rotationIndex++)
            {
                bool isRotated = rotationIndex == 0
                    ? resizeItem.OriginalRotation
                    : !resizeItem.OriginalRotation;
                GetFootprint(resizeItem.Item, isRotated, out int width, out int height);
                if (width > CapacityWidth || height > targetHeight)
                {
                    continue;
                }

                int maxX = CapacityWidth - width;
                int maxY = targetHeight - height;
                for (int y = 0; y <= maxY; y++)
                {
                    for (int x = 0; x <= maxX; x++)
                    {
                        int cellIndex = x + y * CapacityWidth;
                        if (!CanPlace(occupied, cellIndex, width, height))
                        {
                            continue;
                        }

                        MarkPlacement(occupied, cellIndex, width, height, true);
                        placement = new ResizePlacement(cellIndex, isRotated);
                        return true;
                    }
                }
            }

            placement = default;
            return false;
        }

        private bool TryApplyPlannedRotations(
            IReadOnlyList<ResizeItem> items,
            IReadOnlyDictionary<IVariableInventoryCellData, ResizePlacement> placements,
            out string error)
        {
            var changed = new List<ResizeItem>();
            try
            {
                foreach (ResizeItem resizeItem in items)
                {
                    bool targetRotation = placements[resizeItem.Item].IsRotated;
                    if (resizeItem.Item.IsRotate == targetRotation)
                    {
                        continue;
                    }

                    resizeItem.Item.IsRotate = targetRotation;
                    changed.Add(resizeItem);
                }
            }
            catch (Exception exception)
            {
                for (int index = changed.Count - 1; index >= 0; index--)
                {
                    changed[index].Item.IsRotate = changed[index].OriginalRotation;
                }

                error = $"Could not apply the planned item rotations: {exception.Message}";
                return false;
            }

            error = null;
            return true;
        }

        private bool TryMarkPlacement(
            bool[] occupied,
            int targetHeight,
            int cellIndex,
            int width,
            int height)
        {
            if (cellIndex < 0 || cellIndex >= occupied.Length ||
                width <= 0 || height <= 0)
            {
                return false;
            }

            int x = cellIndex % CapacityWidth;
            int y = cellIndex / CapacityWidth;
            if (x + width > CapacityWidth || y + height > targetHeight ||
                !CanPlace(occupied, cellIndex, width, height))
            {
                return false;
            }

            MarkPlacement(occupied, cellIndex, width, height, true);
            return true;
        }

        private bool CanPlace(bool[] occupied, int cellIndex, int width, int height)
        {
            for (int offsetY = 0; offsetY < height; offsetY++)
            {
                for (int offsetX = 0; offsetX < width; offsetX++)
                {
                    if (occupied[cellIndex + offsetX + offsetY * CapacityWidth])
                    {
                        return false;
                    }
                }
            }

            return true;
        }

        private void MarkPlacement(
            bool[] occupied,
            int cellIndex,
            int width,
            int height,
            bool value)
        {
            for (int offsetY = 0; offsetY < height; offsetY++)
            {
                for (int offsetX = 0; offsetX < width; offsetX++)
                {
                    occupied[cellIndex + offsetX + offsetY * CapacityWidth] = value;
                }
            }
        }

        private static void GetFootprint(
            IVariableInventoryCellData item,
            bool isRotated,
            out int width,
            out int height)
        {
            width = isRotated ? item.Height : item.Width;
            height = isRotated ? item.Width : item.Height;
        }

        private void AttachInitialOwners()
        {
            var seen = new HashSet<IVariableInventoryCellData>();
            for (var i = 0; i < CellData.Length; i++)
            {
                var item = CellData[i];
                if (item == null)
                {
                    continue;
                }

                if (!seen.Add(item))
                {
                    throw new InvalidOperationException("The same item is referenced by multiple inventory slots.");
                }

                if (item is IVariableInventoryOwnedCellData owned &&
                    !owned.TryChangeInventoryOwner(null, this))
                {
                    throw new InvalidOperationException("An initial item already belongs to another inventory container.");
                }
            }
        }

        protected void UpdateMask()
        {
            mask = new bool[CapacityWidth * CapacityHeight];

            for (var i = 0; i < CellData.Length; i++)
            {
                if (CellData[i] == null || mask[i])
                {
                    continue;
                }

                var width = CellData[i].IsRotate ? CellData[i].Height : CellData[i].Width;
                var height = CellData[i].IsRotate ? CellData[i].Width : CellData[i].Height;

                for (var w = 0; w < width; w++)
                {
                    for (var h = 0; h < height; h++)
                    {
                        var checkIndex = i + w + (h * CapacityWidth);
                        if (checkIndex < mask.Length)
                        {
                            mask[checkIndex] = true;
                        }
                    }
                }
            }
        }

        protected (int, int) GetRotateSize(IVariableInventoryCellData cell)
        {
            if (cell == null)
            {
                return (1, 1);
            }

            return (cell.IsRotate ? cell.Height : cell.Width, cell.IsRotate ? cell.Width : cell.Height);
        }
    }
}
