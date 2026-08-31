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
        private PlayerInventoryState playerState;
        private Action<string> failureCallback;
        private EquipmentSlotId? originalSlot;
        private IVariableInventoryCellData originalItem;
        private PlayerInventoryState.EquipmentTakeReceipt originalTakeReceipt;
        private VariableInventoryDropHandling? dropPreviewHandling;

        public IReadOnlyList<EquipmentSlotCell> SlotCells => slotCells;
        public IVariableInventoryViewData ViewData => loadout;

        public void BindPlayerState(
            PlayerInventoryState state,
            Action<string> onFailure = null)
        {
            playerState = state ?? throw new ArgumentNullException(nameof(state));
            failureCallback = onFailure;
            Apply(state.Equipment);
        }

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
            EquipmentLoadoutData nextLoadout = data as EquipmentLoadoutData;
            if (nextLoadout == null)
            {
                throw new ArgumentException("EquipmentPanelView requires EquipmentLoadoutData.", nameof(data));
            }

            if (playerState != null && !ReferenceEquals(playerState.Equipment, nextLoadout))
            {
                playerState = null;
                failureCallback = null;
            }

            loadout = nextLoadout;

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

            IVariableInventoryCellData item;
            PlayerInventoryState.EquipmentTakeReceipt takeReceipt = null;
            string error;
            bool taken = playerState != null
                ? playerState.TryTakeEquipment(
                    cell.SlotId,
                    out item,
                    out takeReceipt,
                    out error)
                : TryTakeLegacy(cell.SlotId, out item, out error);
            if (!taken)
            {
                ReportFailure(error);
                return false;
            }

            originalSlot = cell.SlotId;
            originalItem = item;
            originalTakeReceipt = takeReceipt;
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

            if (playerState != null &&
                originalTakeReceipt != null &&
                originalSlot == cell.SlotId &&
                ReferenceEquals(originalItem, effectCell.CellData))
            {
                if (!playerState.TryRestoreTakenEquipment(originalTakeReceipt, out string restoreError))
                {
                    ReportFailure(restoreError);
                    return false;
                }

                cell.Apply(effectCell.CellData);
                ClearOriginal();
                return true;
            }

            string error;
            bool placed = playerState != null
                ? TryPlaceOrUpgradeEquipment(
                    cell.SlotId,
                    effectCell.CellData,
                    out error)
                : TryPlaceLegacy(cell.SlotId, effectCell.CellData, out error);
            if (!placed)
            {
                ReportFailure(error);
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
                string error;
                bool restored;
                if (playerState != null)
                {
                    if (originalTakeReceipt == null)
                    {
                        restored = false;
                        error = "The equipment-take receipt is missing.";
                    }
                    else
                    {
                        restored = playerState.TryRestoreTakenEquipment(
                            originalTakeReceipt,
                            out error);
                    }
                }
                else
                {
                    restored = TryPlaceLegacy(
                        originalSlot.Value,
                        originalItem,
                        out error);
                }
                if (!restored)
                {
                    string message =
                        $"Could not restore equipment item to {originalSlot.Value}: {error}";
                    ReportFailure(message);
                    Debug.LogError(message, this);
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
                         (loadout.CheckInsert(
                              EquipmentSlotCatalog.GetIndex(cell.SlotId),
                              effectCell.CellData) ||
                          playerState != null &&
                          cell.SlotId == EquipmentSlotId.Backpack &&
                          playerState.CanUpgradeBackpack(effectCell.CellData, out _));
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
            originalTakeReceipt = null;
        }

        private bool TryPlaceOrUpgradeEquipment(
            EquipmentSlotId slot,
            IVariableInventoryCellData item,
            out string error)
        {
            if (loadout.GetItem(slot) == null)
            {
                return playerState.TryPlaceEquipment(slot, item, out error);
            }

            if (slot != EquipmentSlotId.Backpack)
            {
                error = $"Equipment slot {slot} is already occupied.";
                return false;
            }

            if (!playerState.CanUpgradeBackpack(item, out error))
            {
                return false;
            }

            if (!playerState.TryUpgradeBackpack(
                    item,
                    out IVariableInventoryCellData removedBackpack,
                    out PlayerInventoryState.BackpackUpgradeReceipt upgradeReceipt,
                    out error))
            {
                return false;
            }

            int? storageIndex = playerState.Inventory.GetInsertableId(removedBackpack);
            if (storageIndex.HasValue)
            {
                try
                {
                    playerState.Inventory.InsertInventoryItem(
                        storageIndex.Value,
                        removedBackpack);
                    error = null;
                    return true;
                }
                catch (Exception exception)
                {
                    error = $"The previous backpack could not be stored: {exception.Message}";
                }
            }
            else
            {
                error = "The previous backpack cannot fit in the Player inventory.";
            }

            string storageError = error;
            if (!playerState.TryRestoreBackpackUpgrade(
                    upgradeReceipt,
                    out IVariableInventoryCellData restoredReplacement,
                    out string rollbackError) ||
                !ReferenceEquals(restoredReplacement, item))
            {
                error = $"{storageError} Backpack upgrade rollback also failed: {rollbackError}";
                return false;
            }

            error = storageError;
            return false;
        }

        private bool TryTakeLegacy(
            EquipmentSlotId slot,
            out IVariableInventoryCellData item,
            out string error)
        {
            if (loadout.TryTake(slot, out item))
            {
                error = null;
                return true;
            }

            error = $"Could not remove the item from {slot}.";
            return false;
        }

        private bool TryPlaceLegacy(
            EquipmentSlotId slot,
            IVariableInventoryCellData item,
            out string error)
        {
            if (loadout.TryPlace(slot, item))
            {
                error = null;
                return true;
            }

            error = $"Could not place the item in {slot}.";
            return false;
        }

        private void ReportFailure(string error)
        {
            if (!string.IsNullOrEmpty(error))
            {
                failureCallback?.Invoke(error);
            }
        }
    }
}
