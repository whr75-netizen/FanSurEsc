// 파일 경로: Assets/VariableInventorySystem/Core/VariableInventoryCore.cs
// ★★★ 이 파일 전체를 아래 내용으로 교체하세요 ★★★

using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace VariableInventorySystem
{
    public enum VariableInventoryCarryMode
    {
        Pointer = 0,
        Click = 1
    }

    public abstract class VariableInventoryCore : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler
    {
        // --- 필드 ---
        protected List<IVariableInventoryView> InventoryViews { get; set; } = new List<IVariableInventoryView>();
        //    [SerializeField] protected virtual GameObject CellPrefab { get; set; }
        //      [SerializeField] protected virtual RectTransform EffectCellParent { get; set; }
        [field: SerializeField] protected virtual GameObject CellPrefab { get; set; }
        [field: SerializeField] protected virtual RectTransform EffectCellParent { get; set; }
        protected IVariableInventoryCell stareCell;
        protected IVariableInventoryCell effectCell;
        bool? originEffectCellRotate;
        Vector2 cursorPosition;
        private IVariableInventoryView originView = null; // ★ 드래그 시작 View 저장용
        private IVariableInventoryTransferController transferController;
        private VariableInventoryCarryMode carryMode;
        private Func<bool> carryRollback;
        private Func<bool> carryCommit;
        private Func<IVariableInventoryCellData, int, int, bool> carryPartialTransferRecorded;
        private IVariableInventoryStackMergeReceipt pendingStackMergeRecovery;
        private IVariableInventorySinglePlacementReceipt pendingSinglePlacementRecovery;
        private PointerEventData clickCarryPointerEvent;
        private EventSystem clickCarryEventSystem;

        public event Action<IVariableInventoryView, IVariableInventoryCell> HoveredCellChanged;

        // --- 추가/기존 메소드 ---
        public bool IsDragging() => effectCell?.CellData != null;
        public bool IsClickCarryActive => carryMode == VariableInventoryCarryMode.Click && IsDragging();
        protected IVariableInventoryView CarryOriginView => originView;
        private bool HasCarryTransaction => carryRollback != null || carryCommit != null;
        public void SetTransferController(IVariableInventoryTransferController controller)
        {
            transferController = controller;
        }
        protected bool TryHandleQuickTransfer(
            IVariableInventoryView sourceView,
            IVariableInventoryCellData item)
        {
            return transferController != null &&
                   transferController.HandleQuickTransfer(sourceView, item);
        }
        protected bool CanPlaceSingleFromCarriedStack(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item)
        {
            return transferController != null &&
                   transferController.CanPlaceSingleFromCarriedStack(
                       sourceView,
                       destinationView,
                       item);
        }
        public virtual void Initialize() { if (effectCell != null) return; if (CellPrefab == null || EffectCellParent == null) { Debug.LogError($"[{GetType().Name}] CellPrefab or EffectCellParent not set!", gameObject); return; } var e = Instantiate(CellPrefab, EffectCellParent); if (e == null) return; effectCell = e.GetComponent<IVariableInventoryCell>(); if (effectCell == null) { Destroy(e); return; } effectCell.RectTransform.gameObject.SetActive(false); effectCell.SetSelectable(false); }
        public virtual void AddInventoryView(IVariableInventoryView v) { if (v == null || InventoryViews.Contains(v)) return; InventoryViews.Add(v); v.SetCellCallback(OnCellClick, OnCellOptionClick, OnCellEnter, OnCellExit); }
        public virtual void RemoveInventoryView(IVariableInventoryView v)
        {
            if (v == null || !InventoryViews.Contains(v))
            {
                return;
            }

            if (v is IVariableInventoryBoundView boundView &&
                boundView.ContainsCell(stareCell))
            {
                stareCell = null;
                NotifyHoveredCellCleared();
            }

            InventoryViews.Remove(v);
        }
        protected virtual void OnCellClick(IVariableInventoryCell cell) { }
        protected virtual void OnCellOptionClick(IVariableInventoryCell cell) { }
        protected virtual void OnCellEnter(IVariableInventoryCell cell)
        {
            stareCell = cell;
            UpdateDropPreviewHandling();
            foreach (var view in InventoryViews)
            {
                view.OnCellEnter(stareCell, effectCell);
            }

            HoveredCellChanged?.Invoke(FindOwningView(cell), cell);
        }

        protected virtual void OnCellExit(IVariableInventoryCell cell)
        {
            bool exitedCurrentCell = ReferenceEquals(stareCell, cell);
            if (exitedCurrentCell)
            {
                stareCell = null;
            }

            UpdateDropPreviewHandling();
            foreach (var view in InventoryViews)
            {
                view.OnCellExit(cell);
            }

            // Pointer enter/exit events can be delivered out of order while UI changes.
            // An older cell must not clear the tooltip of the newly entered cell.
            if (exitedCurrentCell)
            {
                NotifyHoveredCellCleared();
            }
        }

        protected virtual void Update()
        {
            if (IsClickCarryActive)
            {
                UpdateClickCarryPointer();
            }
        }

        protected bool TryBeginDetachedCarry(
            IVariableInventoryView sourceView,
            IVariableInventoryCell sourceCell,
            IVariableInventoryCellData carriedItem,
            VariableInventoryCarryMode mode,
            Func<bool> rollback,
            Func<bool> commit,
            Func<IVariableInventoryCellData, int, int, bool> partialTransferRecorded,
            out string error)
        {
            if (IsDragging())
            {
                error = "Another inventory drag is already active.";
                return false;
            }

            if (sourceView == null || sourceCell == null || carriedItem == null ||
                rollback == null || commit == null || partialTransferRecorded == null ||
                !InventoryViews.Contains(sourceView) ||
                !(sourceView is IVariableInventoryBoundView boundView) ||
                !boundView.ContainsCell(sourceCell))
            {
                error = "The split stack source is not registered with this inventory core.";
                return false;
            }

            if (carriedItem is IVariableInventoryOwnedCellData owned &&
                owned.InventoryOwner != null)
            {
                error = "The split stack already belongs to an inventory.";
                return false;
            }

            if (effectCell == null)
            {
                Initialize();
            }

            if (effectCell == null)
            {
                error = "The inventory drag display cell is unavailable.";
                return false;
            }

            foreach (IVariableInventoryView inventoryView in InventoryViews)
            {
                inventoryView.OnPrePick(sourceCell);
            }

            originView = sourceView;
            stareCell = sourceCell;
            originEffectCellRotate = carriedItem.IsRotate;
            carryRollback = rollback;
            carryCommit = commit;
            carryPartialTransferRecorded = partialTransferRecorded;
            carryMode = mode;

            effectCell.RectTransform.gameObject.SetActive(true);
            effectCell.Apply(carriedItem);
            NotifyHoveredCellCleared();
            if (mode == VariableInventoryCarryMode.Click)
            {
                UpdateClickCarryPointer();
            }
            error = null;
            return true;
        }

        protected bool TryBeginPickedClickCarry(
            IVariableInventoryCell sourceCell,
            out string error)
        {
            return TryBeginPickedCarry(
                sourceCell,
                VariableInventoryCarryMode.Click,
                out error);
        }

        protected bool TryReleaseClickCarry(IVariableInventoryCell destinationCell)
        {
            if (!IsClickCarryActive || destinationCell == null)
            {
                return false;
            }

            stareCell = destinationCell;
            UpdateClickCarryPointer();
            return FinishCurrentDrag();
        }

        public bool TryPlaceSingleFromClickCarry(IVariableInventoryCell destinationCell)
        {
            if (!IsClickCarryActive || destinationCell == null ||
                destinationCell.CellData != null ||
                !(effectCell.CellData is IVariableInventoryStackCellData stackData) ||
                stackData.MaxStackSize <= 1 || stackData.Quantity <= 0 ||
                !(FindOwningView(destinationCell) is IVariableInventoryPartialDropView destinationView))
            {
                return false;
            }

            if (!TryRecoverPendingSinglePlacement() || !TryRecoverPendingStackMerge())
            {
                return false;
            }

            stareCell = destinationCell;
            UpdateClickCarryPointer();

            // The final unit stays the same runtime item. The ordinary drop path
            // attaches it and closes the carry without ever creating quantity zero.
            bool placingFinalUnit = stackData.Quantity == 1;
            if (placingFinalUnit && !HasCarryTransaction)
            {
                return FinishCurrentDrag();
            }

            IVariableInventorySinglePlacementReceipt placementReceipt = null;
            string placementError = null;
            if (transferController == null ||
                !transferController.TryPlaceSingleFromCarriedStack(
                    originView,
                    destinationView,
                    destinationCell,
                    effectCell.CellData,
                    out placementReceipt,
                    out placementError))
            {
                if (placementReceipt != null)
                {
                    pendingSinglePlacementRecovery = placementReceipt;
                    if (!TryRecoverPendingSinglePlacement())
                    {
                        Debug.LogError(
                            $"[Core] Single-item placement left an unresolved mutation: {placementError}",
                            this);
                    }
                }

                return false;
            }

            if (placingFinalUnit && HasCarryTransaction)
            {
                if (carryCommit == null || !carryCommit())
                {
                    if (!placementReceipt.TryRollback(out string rollbackError))
                    {
                        pendingSinglePlacementRecovery = placementReceipt;
                        Debug.LogError(
                            $"[Core] Final single-item placement commit and rollback both failed: {rollbackError}",
                            this);
                        return false;
                    }

                    destinationView.ReApply();
                    OnCarriedItemChanged();
                    UpdateClickCarryPointer();
                    return false;
                }

                IVariableInventoryCellData transferredItem = effectCell.CellData;
                foreach (IVariableInventoryView inventoryView in InventoryViews)
                {
                    inventoryView?.OnDroped(true);
                }

                IVariableInventoryView completedSingleOriginView = originView;
                ClearDragState();
                transferController.OnDropCompleted(
                    completedSingleOriginView,
                    destinationView,
                    transferredItem,
                    VariableInventoryDropHandling.Standard);
                return true;
            }

            if (HasCarryTransaction &&
                (carryPartialTransferRecorded == null ||
                 !carryPartialTransferRecorded(
                     placementReceipt.PlacedItem,
                     placementReceipt.MovedQuantity,
                     placementReceipt.RemainingQuantity)))
            {
                if (!placementReceipt.TryRollback(out string rollbackError))
                {
                    pendingSinglePlacementRecovery = placementReceipt;
                    Debug.LogError(
                        $"[Core] Single-item placement transaction and rollback both failed: {rollbackError}",
                        this);
                    return false;
                }

                destinationView.ReApply();
                OnCarriedItemChanged();
                UpdateClickCarryPointer();
                return false;
            }

            destinationView.ReApply();
            OnCarriedItemChanged();
            UpdateClickCarryPointer();
            transferController.OnInventoryContentsChanged();
            return true;
        }

        public virtual void OnBeginDrag(PointerEventData eventData)
        {
            if (eventData.button != PointerEventData.InputButton.Left)
            {
                return;
            }

            if (!TryBeginPickedCarry(
                    stareCell,
                    VariableInventoryCarryMode.Pointer,
                    out string error) && !string.IsNullOrEmpty(error))
            {
                Debug.LogWarning($"[Core.OnBeginDrag] {error}", this);
            }
        }

        private bool TryBeginPickedCarry(
            IVariableInventoryCell sourceCell,
            VariableInventoryCarryMode mode,
            out string error)
        {
            if (IsDragging())
            {
                error = "A previous inventory carry is still active.";
                return false;
            }

            IVariableInventoryCellData sourceData = sourceCell?.CellData;
            if (sourceData == null)
            {
                error = null;
                return false;
            }

            if (effectCell == null)
            {
                Initialize();
            }

            if (effectCell == null)
            {
                error = "The inventory carry display cell is unavailable.";
                return false;
            }

            foreach (var inventoryView in InventoryViews)
            {
                inventoryView.OnPrePick(sourceCell);
            }

            originView = null;
            foreach (var inventoryView in InventoryViews)
            {
                if (inventoryView.OnPick(sourceCell))
                {
                    originView = inventoryView;
                    break;
                }
            }

            if (originView == null)
            {
                error = null;
                return false;
            }

            stareCell = sourceCell;
            originEffectCellRotate = sourceData.IsRotate;
            carryMode = mode;
            carryRollback = null;
            carryCommit = null;
            carryPartialTransferRecorded = null;
            NotifyHoveredCellCleared();
            effectCell.RectTransform.gameObject.SetActive(true);
            effectCell.Apply(sourceData);
            transferController?.OnInventoryContentsChanged();
            if (mode == VariableInventoryCarryMode.Click)
            {
                UpdateClickCarryPointer();
            }

            error = null;
            return true;
        }

        // --- OnDrag (원본 유지) ---
        public virtual void OnDrag(PointerEventData eventData) { if (!IsDragging()) return; UpdateDropPreviewHandling(); foreach (var v in InventoryViews) v.OnDrag(stareCell, effectCell, eventData); RectTransformUtility.ScreenPointToLocalPointInRectangle(EffectCellParent, eventData.position, eventData.enterEventCamera, out cursorPosition); var (w, h) = GetRotateSize(effectCell.CellData); effectCell.RectTransform.localPosition = cursorPosition + new Vector2(-(w - 1) * effectCell.DefaultCellSize.x * 0.5f, (h - 1) * effectCell.DefaultCellSize.y * 0.5f); }

        // --- OnEndDrag (originView 초기화 추가) ---
        public virtual void OnEndDrag(PointerEventData eventData)
        {
            FinishCurrentDrag();
        }

        private bool FinishCurrentDrag()
        {
            if (!IsDragging())
            {
                return false;
            }

            if (!TryRecoverPendingSinglePlacement() || !TryRecoverPendingStackMerge())
            {
                return false;
            }

            IVariableInventoryCellData transferredItem = effectCell.CellData;
            IVariableInventoryView destinationView = null;
            VariableInventoryDropHandling handling = VariableInventoryDropHandling.Standard;
            bool isRelease = false;
            bool transactionFinalizedByMerge = false;
            foreach (var view in InventoryViews)
            {
                if (!(view is IVariableInventoryBoundView boundView) ||
                    !boundView.ContainsCell(stareCell))
                {
                    continue;
                }

                handling = transferController != null
                    ? transferController.GetDropHandling(originView, view, transferredItem)
                    : VariableInventoryDropHandling.Standard;
                if (handling == VariableInventoryDropHandling.Reject)
                {
                    break;
                }

                bool canMerge = handling == VariableInventoryDropHandling.Standard &&
                                transferController != null &&
                                transferController.CanMergeStack(
                                    originView,
                                    view,
                                    stareCell,
                                    transferredItem);
                if (canMerge)
                {
                    if (!transferController.TryMergeStack(
                            originView,
                            view,
                            stareCell,
                            transferredItem,
                            out IVariableInventoryStackMergeReceipt mergeReceipt,
                            out string mergeError))
                    {
                        if (mergeReceipt != null)
                        {
                            pendingStackMergeRecovery = mergeReceipt;
                            if (!TryRecoverPendingStackMerge())
                            {
                                Debug.LogError(
                                    $"[Core] Stack merge left an unresolved mutation: {mergeError}. " +
                                    "Carry state was preserved for recovery.",
                                    this);
                                return false;
                            }
                        }

                        Debug.LogError($"[Core] Stack merge failed: {mergeError}", this);
                        break;
                    }

                    if (HasCarryTransaction &&
                        (carryPartialTransferRecorded == null ||
                         !carryPartialTransferRecorded(
                             mergeReceipt.TargetItem,
                             mergeReceipt.MovedQuantity,
                             mergeReceipt.RemainingQuantity)))
                    {
                        if (!mergeReceipt.TryRollback(out string rollbackError))
                        {
                            pendingStackMergeRecovery = mergeReceipt;
                            Debug.LogError(
                                $"[Core] Stack merge transaction and rollback both failed: {rollbackError}",
                                this);
                            return false;
                        }

                        break;
                    }

                    destinationView = view;
                    if (mergeReceipt.RemainingQuantity > 0)
                    {
                        carryMode = VariableInventoryCarryMode.Click;
                        view.ReApply();
                        OnCarriedItemChanged();
                        UpdateClickCarryPointer();
                        transferController.OnInventoryContentsChanged();
                        Debug.Log(
                            $"[Core] Stack merge moved {mergeReceipt.MovedQuantity}; " +
                            $"{mergeReceipt.RemainingQuantity} remains carried.",
                            this);
                        return true;
                    }

                    isRelease = true;
                    transactionFinalizedByMerge = HasCarryTransaction;
                }
                else
                {
                    isRelease = handling == VariableInventoryDropHandling.AcceptWithoutInsert ||
                                view.OnDrop(stareCell, effectCell);
                }

                if (isRelease)
                {
                    destinationView = view;
                }
                break;
            }

            // A click-carry is an explicit held state. Clicking an invalid cell must
            // not silently turn it into a cancelled drag; the next valid click or an
            // explicit cancel still owns the resolution.
            if (!isRelease && carryMode == VariableInventoryCarryMode.Click)
            {
                UpdateDropPreviewHandling();
                return false;
            }

            if (!isRelease)
            {
                RestoreOriginalRotation();
            }

            if (!isRelease && HasCarryTransaction)
            {
                if (!TryRollbackCarryTransaction())
                {
                    Debug.LogError(
                        "[Core] Carry transaction rollback failed. Carry state was kept instead of discarding the detached item reference.");
                    return false;
                }
            }

            if (isRelease && HasCarryTransaction && !transactionFinalizedByMerge &&
                (carryCommit == null || !carryCommit()))
            {
                Debug.LogError(
                    "[Core] Carry transaction commit failed. Carry state was kept for diagnosis instead of silently discarding its transaction boundary.");
                return false;
            }

            foreach (var inventoryView in InventoryViews)
            {
                inventoryView?.OnDroped(isRelease); // ★ 일반 드래그의 원본 복구 소유자
            }

            if (!isRelease && !HasCarryTransaction && IsDetachedOwnedItem())
            {
                Debug.LogError("[Core.OnEndDrag] Rollback failed. Drag state was kept instead of discarding the item reference.");
                return false;
            }

            IVariableInventoryView completedOriginView = originView;
            ClearDragState();
            if (!isRelease)
            {
                transferController?.OnInventoryContentsChanged();
            }
            else if (transferController != null)
            {
                transferController.OnDropCompleted(
                    completedOriginView,
                    destinationView,
                    transferredItem,
                    handling);
            }

            Debug.Log($"[Core.OnEndDrag] Drag ended. Drop Success: {isRelease}");
            return isRelease;
        }

        // --- SwitchRotate, GetRotateSize (원본 유지) ---
        public virtual void SwitchRotate() { if (!IsDragging()) return; if (!originEffectCellRotate.HasValue) originEffectCellRotate = effectCell.CellData.IsRotate; effectCell.CellData.IsRotate = !effectCell.CellData.IsRotate; effectCell.Apply(effectCell.CellData); var (w, h) = GetRotateSize(effectCell.CellData); effectCell.RectTransform.localPosition = cursorPosition + new Vector2(-(w - 1) * effectCell.DefaultCellSize.x * 0.5f, (h - 1) * effectCell.DefaultCellSize.y * 0.5f); UpdateDropPreviewHandling(); foreach (var v in InventoryViews) v.OnSwitchRotate(stareCell, effectCell); }
        (int, int) GetRotateSize(IVariableInventoryCellData cell) { if (cell == null) return (1, 1); return (cell.IsRotate ? cell.Height : cell.Width, cell.IsRotate ? cell.Width : cell.Height); }

        // --- CancelDrag (OnDroped(false) 호출) ---
        public bool CancelDrag()
        {
            if (!IsDragging()) return true;
            Debug.Log("[VariableInventoryCore.CancelDrag] 드래그 취소 시도...");
            if (!TryRecoverPendingSinglePlacement())
            {
                Debug.LogError(
                    "[VariableInventoryCore.CancelDrag] Pending single-item placement recovery failed. Carry state was kept.");
                return false;
            }

            if (!TryRecoverPendingStackMerge())
            {
                Debug.LogError(
                    "[VariableInventoryCore.CancelDrag] Pending stack merge recovery failed. Carry state was kept.");
                return false;
            }

            if (originView != null)
            {
                Debug.Log($"[VariableInventoryCore.CancelDrag] Origin View ({((UnityEngine.Object)originView).GetEntityId()})의 OnDroped(false) 호출 시도.");
            }
            else { Debug.LogWarning("[VariableInventoryCore.CancelDrag] Origin view is unknown!"); }
            RestoreOriginalRotation();
            if (HasCarryTransaction)
            {
                if (!TryRollbackCarryTransaction())
                {
                    Debug.LogError(
                        "[VariableInventoryCore.CancelDrag] Carry transaction rollback failed. Carry state was kept.");
                    return false;
                }
            }

            foreach (var inventoryView in InventoryViews)
            {
                inventoryView?.OnDroped(false);
            }

            if (!HasCarryTransaction && IsDetachedOwnedItem())
            {
                Debug.LogError("[VariableInventoryCore.CancelDrag] Rollback failed. Drag state was kept instead of discarding the item reference.");
                return false;
            }
            ClearDragState();
            NotifyHoveredCellCleared();
            transferController?.OnInventoryContentsChanged();
            Debug.Log("[VariableInventoryCore.CancelDrag] 드래그 취소 완료.");
            return true;
        }

        private bool TryRollbackCarryTransaction()
        {
            if (!HasCarryTransaction || carryRollback == null)
            {
                return false;
            }

            try
            {
                return carryRollback();
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
                return false;
            }
        }

        private void ClearDragState()
        {
            if (effectCell != null)
            {
                if (effectCell.RectTransform != null)
                {
                    effectCell.RectTransform.gameObject.SetActive(false);
                }

                effectCell.Apply(null);
            }

            originEffectCellRotate = null;
            originView = null;
            stareCell = null;
            carryMode = VariableInventoryCarryMode.Pointer;
            carryRollback = null;
            carryCommit = null;
            carryPartialTransferRecorded = null;
            pendingStackMergeRecovery = null;
            pendingSinglePlacementRecovery = null;
            OnCarryStateCleared();
        }

        private bool TryRecoverPendingStackMerge()
        {
            if (pendingStackMergeRecovery == null)
            {
                return true;
            }

            if (!pendingStackMergeRecovery.TryRollback(out string error))
            {
                Debug.LogError(
                    $"[VariableInventoryCore] Pending stack merge rollback failed: {error}",
                    this);
                return false;
            }

            pendingStackMergeRecovery = null;
            foreach (IVariableInventoryView inventoryView in InventoryViews)
            {
                inventoryView?.ReApply();
            }

            OnCarriedItemChanged();
            UpdateDropPreviewHandling();
            return true;
        }

        private bool TryRecoverPendingSinglePlacement()
        {
            if (pendingSinglePlacementRecovery == null)
            {
                return true;
            }

            if (!pendingSinglePlacementRecovery.TryRollback(out string error))
            {
                Debug.LogError(
                    $"[VariableInventoryCore] Pending single-item placement rollback failed: {error}",
                    this);
                return false;
            }

            pendingSinglePlacementRecovery = null;
            foreach (IVariableInventoryView inventoryView in InventoryViews)
            {
                inventoryView?.ReApply();
            }

            OnCarriedItemChanged();
            UpdateDropPreviewHandling();
            return true;
        }

        private void UpdateClickCarryPointer()
        {
            EventSystem currentEventSystem = EventSystem.current;
            if (!IsClickCarryActive || currentEventSystem == null)
            {
                return;
            }

            if (clickCarryPointerEvent == null ||
                clickCarryEventSystem != currentEventSystem)
            {
                clickCarryPointerEvent = new PointerEventData(currentEventSystem);
                clickCarryEventSystem = currentEventSystem;
            }
            else
            {
                clickCarryPointerEvent.Reset();
            }

            clickCarryPointerEvent.position = Input.mousePosition;
            OnDrag(clickCarryPointerEvent);
        }

        private void RestoreOriginalRotation()
        {
            if (!originEffectCellRotate.HasValue || effectCell?.CellData == null)
            {
                return;
            }

            effectCell.CellData.IsRotate = originEffectCellRotate.Value;
            effectCell.Apply(effectCell.CellData);
        }

        protected void UpdateDropPreviewHandling()
        {
            foreach (IVariableInventoryView view in InventoryViews)
            {
                if (!(view is IVariableInventoryBoundView boundView))
                {
                    continue;
                }

                VariableInventoryDropHandling? handling = null;
                if (IsDragging() && stareCell != null && boundView.ContainsCell(stareCell) &&
                    transferController != null)
                {
                    handling = transferController.GetDropPreviewHandling(
                        originView,
                        view,
                        effectCell.CellData);
                    if (handling == VariableInventoryDropHandling.Standard &&
                        TryGetDropPreviewHandlingOverride(
                            view,
                            stareCell,
                            effectCell.CellData,
                            out VariableInventoryDropHandling previewOverride))
                    {
                        handling = previewOverride;
                    }
                    else if (handling == VariableInventoryDropHandling.Standard &&
                             transferController.CanMergeStack(
                                 originView,
                                 view,
                                 stareCell,
                                 effectCell.CellData))
                    {
                        handling = VariableInventoryDropHandling.AcceptWithoutInsert;
                    }
                }

                boundView.SetDropPreviewHandling(handling);
            }
        }

        protected virtual bool TryGetDropPreviewHandlingOverride(
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData carriedItem,
            out VariableInventoryDropHandling handling)
        {
            handling = VariableInventoryDropHandling.Standard;
            return false;
        }

        protected IVariableInventoryView FindOwningView(IVariableInventoryCell cell)
        {
            foreach (IVariableInventoryView view in InventoryViews)
            {
                if (view is IVariableInventoryBoundView boundView &&
                    boundView.ContainsCell(cell))
                {
                    return view;
                }
            }

            return null;
        }

        private void NotifyHoveredCellCleared()
        {
            HoveredCellChanged?.Invoke(null, null);
        }

        private bool IsDetachedOwnedItem()
        {
            return effectCell?.CellData is IVariableInventoryOwnedCellData owned &&
                   owned.InventoryOwner == null;
        }

        protected virtual void OnCarriedItemChanged()
        {
        }

        protected virtual void OnCarryStateCleared()
        {
        }
    }
}
