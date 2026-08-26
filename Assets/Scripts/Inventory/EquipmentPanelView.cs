using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    [DisallowMultipleComponent]
    public sealed class EquipmentPanelView : MonoBehaviour, IVariableInventoryBoundView
    {
        [SerializeField] private EquipmentSlotCell[] slotCells;

        private EquipmentLoadoutData loadout;
        private EquipmentSlotId? originalSlot;
        private IVariableInventoryCellData originalItem;
        private VariableInventoryDropHandling? dropPreviewHandling;

        public IReadOnlyList<EquipmentSlotCell> SlotCells => slotCells;
        public IVariableInventoryViewData ViewData => loadout;

        public void SetCellCallback(
            Action<IVariableInventoryCell> onCellClick,
            Action<IVariableInventoryCell> onCellOptionClick,
            Action<IVariableInventoryCell> onCellEnter,
            Action<IVariableInventoryCell> onCellExit)
        {
            if (slotCells == null)
            {
                return;
            }

            foreach (EquipmentSlotCell cell in slotCells)
            {
                cell?.SetCellCallback(onCellClick, onCellOptionClick, onCellEnter, onCellExit);
            }
        }

        public void Apply(IVariableInventoryViewData data)
        {
            loadout = data as EquipmentLoadoutData;
            if (loadout == null)
            {
                throw new ArgumentException("EquipmentPanelView requires EquipmentLoadoutData.", nameof(data));
            }

            if (!TryValidateCells(out string error))
            {
                throw new InvalidOperationException(error);
            }

            foreach (EquipmentSlotCell cell in slotCells)
            {
                cell.Apply(loadout.GetItem(cell.SlotId));
            }

            loadout.IsDirty = false;
        }

        public void ReApply()
        {
            if (loadout != null && loadout.IsDirty)
            {
                Apply(loadout);
            }
        }

        public void OnPrePick(IVariableInventoryCell stareCell)
        {
        }

        public bool OnPick(IVariableInventoryCell stareCell)
        {
            if (loadout == null || !(stareCell is EquipmentSlotCell cell) ||
                !Contains(cell) || cell.CellData == null)
            {
                return false;
            }

            if (!loadout.TryTake(cell.SlotId, out IVariableInventoryCellData item))
            {
                return false;
            }

            originalSlot = cell.SlotId;
            originalItem = item;
            cell.Apply(null);
            return true;
        }

        public void OnDrag(
            IVariableInventoryCell stareCell,
            IVariableInventoryCell effectCell,
            PointerEventData cursorPosition)
        {
            UpdateDropHighlight(stareCell, effectCell);
        }

        public bool OnDrop(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell)
        {
            if (loadout == null || effectCell?.CellData == null ||
                !(stareCell is EquipmentSlotCell cell) || !Contains(cell))
            {
                return false;
            }

            if (!loadout.TryPlace(cell.SlotId, effectCell.CellData))
            {
                return false;
            }

            cell.Apply(effectCell.CellData);
            ClearOriginal();
            return true;
        }

        public void OnDroped(bool isDroped)
        {
            dropPreviewHandling = null;
            ClearHighlights();
            if (!isDroped && originalSlot.HasValue && originalItem != null)
            {
                if (!loadout.TryPlace(originalSlot.Value, originalItem))
                {
                    Debug.LogError($"Could not restore equipment item to {originalSlot.Value}.", this);
                    return;
                }

                FindCell(originalSlot.Value)?.Apply(originalItem);
            }

            ClearOriginal();
        }

        public void OnCellEnter(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell)
        {
            UpdateDropHighlight(stareCell, effectCell);
        }

        public void OnCellExit(IVariableInventoryCell stareCell)
        {
            if (stareCell is EquipmentSlotCell cell && Contains(cell))
            {
                cell.SetHighlight(false, false);
            }
        }

        public void OnSwitchRotate(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell)
        {
            UpdateDropHighlight(stareCell, effectCell);
        }

        public bool TryValidateCells(out string error)
        {
            if (slotCells == null || slotCells.Length != EquipmentSlotCatalog.Count)
            {
                error = $"Equipment panel must contain exactly {EquipmentSlotCatalog.Count} slot cells.";
                return false;
            }

            var seen = new HashSet<EquipmentSlotId>();
            foreach (EquipmentSlotCell cell in slotCells)
            {
                if (cell == null || !EquipmentSlotCatalog.IsValid(cell.SlotId) || !seen.Add(cell.SlotId))
                {
                    error = "Equipment panel contains a missing, invalid, or duplicate slot.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private void UpdateDropHighlight(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell)
        {
            if (!(stareCell is EquipmentSlotCell cell) || !Contains(cell))
            {
                return;
            }

            bool dragging = effectCell?.CellData != null;
            bool valid = dragging && dropPreviewHandling != VariableInventoryDropHandling.Reject &&
                         loadout != null &&
                         loadout.CheckInsert(EquipmentSlotCatalog.GetIndex(cell.SlotId), effectCell.CellData);
            cell.SetHighlight(dragging, valid);
        }

        private bool Contains(EquipmentSlotCell cell)
        {
            if (slotCells == null)
            {
                return false;
            }

            foreach (EquipmentSlotCell candidate in slotCells)
            {
                if (ReferenceEquals(candidate, cell))
                {
                    return true;
                }
            }

            return false;
        }

        public bool ContainsCell(IVariableInventoryCell cell)
        {
            return cell is EquipmentSlotCell equipmentCell && Contains(equipmentCell);
        }

        public void SetDropPreviewHandling(VariableInventoryDropHandling? handling)
        {
            dropPreviewHandling = handling;
        }

        private EquipmentSlotCell FindCell(EquipmentSlotId slot)
        {
            if (slotCells == null)
            {
                return null;
            }

            foreach (EquipmentSlotCell cell in slotCells)
            {
                if (cell != null && cell.SlotId == slot)
                {
                    return cell;
                }
            }

            return null;
        }

        private void ClearHighlights()
        {
            if (slotCells == null)
            {
                return;
            }

            foreach (EquipmentSlotCell cell in slotCells)
            {
                cell?.SetHighlight(false, false);
            }
        }

        private void ClearOriginal()
        {
            originalSlot = null;
            originalItem = null;
        }
    }
}
