using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    [DisallowMultipleComponent]
    public sealed class EquipmentPanelView : MonoBehaviour, IVariableInventoryBoundView,
        IVariableInventoryDeferredDropSource
    {
        [SerializeField] private EquipmentSlotCell[] slotCells;

        private EquipmentLoadoutData loadout;
        private PlayerInventoryState playerState;
        private Action<string> failureCallback;
        private EquipmentSlotId? originalSlot;
        private IVariableInventoryCellData originalItem;
        private PlayerInventoryState.EquipmentTakeReceipt originalTakeReceipt;
        private bool originalPickDeferred;
        private VariableInventoryDropHandling? dropPreviewHandling;
        private bool hasDeferredPreviewCache;
        private IVariableInventoryView cachedDeferredDestinationView;
        private IVariableInventoryViewData cachedDeferredDestinationOwner;
        private int cachedDeferredDestinationIndex;
        private bool cachedDeferredItemRotation;
        private long cachedPlayerInventoryLayoutVersion;
        private long cachedDestinationLayoutVersion;
        private VariableInventoryDropHandling cachedDeferredHandling;

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

            if (playerState != null && cell.SlotId == EquipmentSlotId.Backpack &&
                ReferenceEquals(loadout.GetItem(cell.SlotId), cell.CellData))
            {
                originalSlot = cell.SlotId;
                originalItem = cell.CellData;
                originalTakeReceipt = null;
                originalPickDeferred = true;
                cell.Apply(null);
                return true;
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
            if (originalPickDeferred)
            {
                if (isDroped && originalTakeReceipt != null && playerState != null)
                {
                    if (!playerState.TryPublishStagedEquipmentTake(
                            originalTakeReceipt,
                            out string deferredPublishError))
                    {
                        string message =
                            $"Could not publish the completed deferred equipment drop: " +
                            deferredPublishError;
                        ReportFailure(message);
                        Debug.LogError(message, this);
                        ClearOriginal();
                        return;
                    }

                    originalTakeReceipt = null;
                }
                else if (!isDroped && originalTakeReceipt != null && playerState != null &&
                         !playerState.TryRestoreTakenEquipment(
                             originalTakeReceipt,
                             out string deferredRestoreError))
                {
                    string message =
                        $"Could not restore deferred equipment item to {originalSlot}: " +
                        deferredRestoreError;
                    ReportFailure(message);
                    Debug.LogError(message, this);
                    return;
                }

                if (originalSlot.HasValue)
                {
                    FindCell(originalSlot.Value)?.Apply(
                        loadout.GetItem(originalSlot.Value));
                }

                ClearOriginal();
                return;
            }

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
            bool valid = dragging &&
                         (dropPreviewHandling == VariableInventoryDropHandling.AcceptWithoutInsert ||
                          dropPreviewHandling != VariableInventoryDropHandling.Reject &&
                          loadout != null &&
                          (loadout.CheckInsert(
                               EquipmentSlotCatalog.GetIndex(cell.SlotId),
                               effectCell.CellData) ||
                           playerState != null &&
                           cell.SlotId == EquipmentSlotId.Backpack &&
                           playerState.CanUpgradeBackpackWithDetachedReplacement(
                               effectCell.CellData,
                               out _)));
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

        public bool IsDeferredDropActive(IVariableInventoryCellData item)
        {
            return originalPickDeferred && originalSlot == EquipmentSlotId.Backpack &&
                   ReferenceEquals(originalItem, item) && playerState != null &&
                   loadout != null &&
                   ReferenceEquals(loadout.GetItem(EquipmentSlotId.Backpack), item);
        }

        public VariableInventoryDropHandling GetDeferredDropPreviewHandling(
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item)
        {
            if (!IsDeferredDropActive(item))
            {
                return VariableInventoryDropHandling.Reject;
            }

            if (ReferenceEquals(destinationView, this))
            {
                return destinationCell is EquipmentSlotCell equipmentCell &&
                       equipmentCell.SlotId == originalSlot
                    ? VariableInventoryDropHandling.AcceptWithoutInsert
                    : VariableInventoryDropHandling.Reject;
            }

            if (!(destinationView is IVariableInventoryDeferredDropTarget target) ||
                !target.TryResolveDeferredDropTarget(
                    destinationCell,
                    item,
                    loadout,
                    out IVariableInventoryViewData destinationOwner,
                    out int destinationIndex,
                    out _))
            {
                return VariableInventoryDropHandling.Reject;
            }

            StandardStashViewData destinationGrid =
                destinationOwner as StandardStashViewData;
            long playerInventoryLayoutVersion = playerState.Inventory.LayoutVersion;
            long destinationLayoutVersion = destinationGrid?.LayoutVersion ?? -1L;

            if (hasDeferredPreviewCache &&
                ReferenceEquals(cachedDeferredDestinationView, destinationView) &&
                ReferenceEquals(cachedDeferredDestinationOwner, destinationOwner) &&
                cachedDeferredDestinationIndex == destinationIndex &&
                cachedDeferredItemRotation == item.IsRotate &&
                cachedPlayerInventoryLayoutVersion == playerInventoryLayoutVersion &&
                cachedDestinationLayoutVersion == destinationLayoutVersion)
            {
                return cachedDeferredHandling;
            }

            bool valid = ReferenceEquals(destinationOwner, playerState.Inventory)
                ? playerState.CanUnequipToPlayerInventoryAt(
                    originalSlot.Value,
                    destinationIndex,
                    item.IsRotate,
                    out _)
                : playerState.CanTakeEquipment(originalSlot.Value, out _);
            cachedDeferredHandling = valid
                ? VariableInventoryDropHandling.AcceptWithoutInsert
                : VariableInventoryDropHandling.Reject;
            hasDeferredPreviewCache = destinationGrid != null;
            cachedDeferredDestinationView = destinationView;
            cachedDeferredDestinationOwner = destinationOwner;
            cachedDeferredDestinationIndex = destinationIndex;
            cachedDeferredItemRotation = item.IsRotate;
            cachedPlayerInventoryLayoutVersion = playerInventoryLayoutVersion;
            cachedDestinationLayoutVersion = destinationLayoutVersion;
            return cachedDeferredHandling;
        }

        public bool TryCompleteDeferredDrop(
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item,
            out string error)
        {
            error = null;
            if (!IsDeferredDropActive(item))
            {
                error = "The deferred equipment drag is no longer active.";
                return false;
            }

            if (ReferenceEquals(destinationView, this))
            {
                bool sameSlot = destinationCell is EquipmentSlotCell equipmentCell &&
                                equipmentCell.SlotId == originalSlot &&
                                ReferenceEquals(
                                    loadout.GetItem(originalSlot.Value),
                                    item);
                error = sameSlot ? null : "The equipment item cannot be dropped in that slot.";
                return sameSlot;
            }

            if (!(destinationView is IVariableInventoryDeferredDropTarget target) ||
                !target.TryResolveDeferredDropTarget(
                    destinationCell,
                    item,
                    loadout,
                    out IVariableInventoryViewData destinationOwner,
                    out int destinationIndex,
                    out error))
            {
                return false;
            }

            if (ReferenceEquals(destinationOwner, playerState.Inventory))
            {
                return playerState.TryUnequipToPlayerInventoryAt(
                    originalSlot.Value,
                    destinationIndex,
                    item.IsRotate,
                    out error);
            }

            if (!playerState.TryStageTakeEquipment(
                    originalSlot.Value,
                    out IVariableInventoryCellData detachedItem,
                    out PlayerInventoryState.EquipmentTakeReceipt takeReceipt,
                    out error))
            {
                return false;
            }

            if (!ReferenceEquals(detachedItem, item))
            {
                originalTakeReceipt = takeReceipt;
                string mismatch = "A different equipment item was detached during the drop.";
                if (!playerState.TryRestoreTakenEquipment(
                        takeReceipt,
                        out string mismatchRollbackError))
                {
                    error = $"{mismatch} Equipment rollback also failed: " +
                            mismatchRollbackError;
                    return false;
                }

                originalTakeReceipt = null;
                error = mismatch;
                return false;
            }

            try
            {
                if (!destinationOwner.CheckInsert(destinationIndex, item))
                {
                    error = "The selected destination changed before the equipment drop completed.";
                }
                else
                {
                    destinationOwner.InsertInventoryItem(destinationIndex, item);
                    originalTakeReceipt = takeReceipt;
                    if (playerState.TryPublishStagedEquipmentTake(
                            takeReceipt,
                            out string publishError))
                    {
                        originalTakeReceipt = null;
                        error = null;
                        return true;
                    }

                    error = $"The deferred equipment drop could not be published: " +
                            publishError;
                }
            }
            catch (Exception exception)
            {
                error = $"Could not place the equipment item: {exception.Message}";
            }

            originalTakeReceipt = takeReceipt;
            if (item is IVariableInventoryOwnedCellData owned &&
                ReferenceEquals(owned.InventoryOwner, destinationOwner))
            {
                int? insertedIndex = destinationOwner.GetId(item);
                if (!insertedIndex.HasValue)
                {
                    error += " The destination owns the item without a matching slot.";
                    return false;
                }

                try
                {
                    destinationOwner.InsertInventoryItem(insertedIndex.Value, null);
                }
                catch (Exception rollbackException)
                {
                    error += $" Destination rollback also failed: {rollbackException.Message}";
                    return false;
                }
            }

            if (!playerState.TryRestoreTakenEquipment(
                    takeReceipt,
                    out string rollbackError))
            {
                error += $" Equipment rollback also failed: {rollbackError}";
                return false;
            }

            originalTakeReceipt = null;
            return false;
        }

        public bool TryPrepareDeferredExternalDrop(
            IVariableInventoryCellData item,
            out string error)
        {
            if (!IsDeferredDropActive(item))
            {
                error = "The deferred equipment drag is no longer active.";
                return false;
            }

            if (originalTakeReceipt != null)
            {
                error = null;
                return item is IVariableInventoryOwnedCellData owned &&
                       owned.InventoryOwner == null;
            }

            if (!playerState.TryStageTakeEquipment(
                    originalSlot.Value,
                    out IVariableInventoryCellData detachedItem,
                    out originalTakeReceipt,
                    out error))
            {
                originalTakeReceipt = null;
                ReportFailure(error);
                return false;
            }

            if (!ReferenceEquals(detachedItem, item))
            {
                string mismatch = "A different equipment item was detached for the external drop.";
                if (!playerState.TryRestoreTakenEquipment(
                        originalTakeReceipt,
                        out string rollbackError))
                {
                    error = $"{mismatch} Equipment rollback also failed: {rollbackError}";
                    ReportFailure(error);
                    return false;
                }

                originalTakeReceipt = null;
                error = mismatch;
                ReportFailure(error);
                return false;
            }

            if (!playerState.TryPrepareStagedEquipmentTakePublication(
                    originalTakeReceipt,
                    out string prepareError))
            {
                string preparationFailure =
                    $"The external equipment drop could not be prepared: {prepareError}";
                if (!playerState.TryRestoreTakenEquipment(
                        originalTakeReceipt,
                        out string preparationRollbackError))
                {
                    error = $"{preparationFailure} Equipment rollback also failed: " +
                            preparationRollbackError;
                    ReportFailure(error);
                    return false;
                }

                originalTakeReceipt = null;
                error = preparationFailure;
                ReportFailure(error);
                return false;
            }

            return true;
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
            originalPickDeferred = false;
            hasDeferredPreviewCache = false;
            cachedDeferredDestinationView = null;
            cachedDeferredDestinationOwner = null;
            cachedDeferredDestinationIndex = -1;
            cachedDeferredItemRotation = false;
            cachedPlayerInventoryLayoutVersion = -1L;
            cachedDestinationLayoutVersion = -1L;
            cachedDeferredHandling = VariableInventoryDropHandling.Reject;
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

            if (!playerState.CanUpgradeBackpackWithDetachedReplacement(item, out error))
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
