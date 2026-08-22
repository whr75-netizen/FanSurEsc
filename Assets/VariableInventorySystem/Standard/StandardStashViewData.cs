using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace VariableInventorySystem
{
    public class StandardStashViewData : IVariableInventoryViewData
    {
        public bool IsDirty { get; set; }
        public IVariableInventoryCellData[] CellData { get; }

        public int CapacityWidth { get; }
        public int CapacityHeight { get; }

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
            if (id < 0 || cellData == null)
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
