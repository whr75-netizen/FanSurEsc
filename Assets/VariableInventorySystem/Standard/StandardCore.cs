using System.Collections.Generic;
using FantasySurvival.Controls;
using UnityEngine;
using UnityEngine.EventSystems;

namespace VariableInventorySystem
{
    public class StandardCore : VariableInventoryCore
    {
        [SerializeField] GameObject cellPrefab;
        [SerializeField] GameObject casePopupPrefab;
        [SerializeField] RectTransform effectCellParent;
        [SerializeField] RectTransform caseParent;

        protected override GameObject CellPrefab => cellPrefab;
        protected override RectTransform EffectCellParent => effectCellParent;

        protected List<IStandardCaseCellData> popupList = new List<IStandardCaseCellData>();
        private System.Func<IVariableInventoryCellData, string> quantityBadgeTextProvider;
        private readonly HashSet<IVariableInventoryCell> singlePlacementVisitedCells =
            new HashSet<IVariableInventoryCell>();
        private bool singlePlacementDragActive;
        private bool consumeSinglePlacementEndDrag;
        private bool consumeReleasedBeginDragEnd;

        public event System.Action<IVariableInventoryView, IVariableInventoryCell>
            ItemContextRequested;
        public event System.Action<
                IVariableInventoryView,
                IVariableInventoryCell,
                VariableInventoryCarryMode>
            AlternateItemActionRequested;
        public event System.Action<IVariableInventoryView, IVariableInventoryCell>
            SingleItemPickupRequested;

        public void SetQuantityBadgeTextProvider(
            System.Func<IVariableInventoryCellData, string> provider)
        {
            quantityBadgeTextProvider = provider;
            foreach (IVariableInventoryView view in InventoryViews)
            {
                if (view is StandardStashView stashView)
                {
                    stashView.SetQuantityBadgeTextProvider(provider);
                }
            }

            RefreshEffectCellQuantityBadge();
        }

        public override void AddInventoryView(IVariableInventoryView view)
        {
            if (view is StandardStashView stashView)
            {
                stashView.SetQuantityBadgeTextProvider(
                    quantityBadgeTextProvider,
                    false);
            }

            base.AddInventoryView(view);
        }

        public void CloseAllCasePopups()
        {
            if (caseParent == null)
            {
                popupList.Clear();
                return;
            }

            var openPopups = caseParent.GetComponentsInChildren<StandardCaseViewPopup>(true);
            foreach (var popup in openPopups)
            {
                if (popup == null)
                {
                    continue;
                }

                RemoveInventoryView(popup.StandardCaseView);
                Destroy(popup.gameObject);
            }

            popupList.Clear();
        }

        protected override void OnCellClick(IVariableInventoryCell cell)
        {
            bool altHeld = GameInputBindings.IsPressed(
                GameInputActionId.AlternateItemModifier);
            bool controlHeld = GameInputBindings.IsPressed(
                GameInputActionId.SingleItemModifier);
            bool shiftHeld = GameInputBindings.IsPressed(
                GameInputActionId.QuickTransferModifier);

            if (IsClickCarryActive)
            {
                if (IsSinglePlacementModifierHeld())
                {
                    TryPlaceSingleFromClickCarry(cell);
                }
                else
                {
                    TryReleaseClickCarry(cell);
                }

                return;
            }

            if (cell?.CellData == null)
            {
                return;
            }

            if ((altHeld || controlHeld) && shiftHeld)
            {
                return;
            }

            IVariableInventoryView sourceView = FindOwningView(cell);
            if (altHeld)
            {
                AlternateItemActionRequested?.Invoke(
                    sourceView,
                    cell,
                    VariableInventoryCarryMode.Click);
                return;
            }

            if (controlHeld)
            {
                if (cell.CellData is IVariableInventoryStackCellData stackData &&
                    stackData.MaxStackSize > 1 && stackData.Quantity > 1)
                {
                    SingleItemPickupRequested?.Invoke(
                        FindOwningView(cell),
                        cell);
                    return;
                }

                if (!TryBeginPickedClickCarry(cell, out string pickupError) &&
                    !string.IsNullOrEmpty(pickupError))
                {
                    Debug.LogWarning(
                        $"[StandardCore] Ctrl-click pickup failed: {pickupError}",
                        this);
                }

                return;
            }

            if (shiftHeld)
            {
                if (sourceView != null)
                {
                    TryHandleQuickTransfer(sourceView, cell.CellData);
                }

                return;
            }

            if (!TryBeginPickedClickCarry(cell, out string error) &&
                !string.IsNullOrEmpty(error))
            {
                Debug.LogWarning($"[StandardCore] Click pickup failed: {error}", this);
            }
        }

        protected override void OnCellOptionClick(IVariableInventoryCell cell)
        {
            if (IsClickCarryActive)
            {
                CancelDrag();
                return;
            }

            if (cell?.CellData != null)
            {
                ItemContextRequested?.Invoke(FindOwningView(cell), cell);
            }
        }

        public bool TryOpenCase(
            IVariableInventoryView sourceView,
            IVariableInventoryCell sourceCell)
        {
            if (!CanOpenCase(sourceView, sourceCell) ||
                !(sourceCell.CellData is IStandardCaseCellData caseData))
            {
                return false;
            }

            StandardCaseViewPopup popup = Instantiate(casePopupPrefab, caseParent)
                .GetComponent<StandardCaseViewPopup>();
            if (popup == null || popup.StandardCaseView == null)
            {
                if (popup != null)
                {
                    Destroy(popup.gameObject);
                }

                return false;
            }

            popupList.Add(caseData);
            AddInventoryView(popup.StandardCaseView);
            popup.Open(
                caseData,
                () =>
                {
                    RemoveInventoryView(popup.StandardCaseView);
                    Destroy(popup.gameObject);
                    popupList.Remove(caseData);
                });
            return true;
        }

        public bool CanOpenCase(
            IVariableInventoryView sourceView,
            IVariableInventoryCell sourceCell)
        {
            return sourceView != null && sourceCell != null &&
                   ReferenceEquals(FindOwningView(sourceCell), sourceView) &&
                   sourceCell.CellData is IStandardCaseCellData caseData &&
                   !popupList.Contains(caseData) &&
                   casePopupPrefab != null && caseParent != null;
        }

        public bool TryBeginStackSplitCarry(
            IVariableInventoryView sourceView,
            IVariableInventoryCell sourceCell,
            IVariableInventoryCellData splitItem,
            VariableInventoryCarryMode carryMode,
            System.Func<bool> rollback,
            System.Func<bool> commit,
            System.Func<IVariableInventoryCellData, int, int, bool> partialTransferRecorded,
            out string error)
        {
            if (!TryBeginDetachedCarry(
                    sourceView,
                    sourceCell,
                    splitItem,
                    carryMode,
                    rollback,
                    commit,
                    partialTransferRecorded,
                    out error))
            {
                return false;
            }

            RefreshEffectCellQuantityBadge();
            return true;
        }

        public override void OnBeginDrag(PointerEventData eventData)
        {
            consumeReleasedBeginDragEnd = false;
            bool altHeld = GameInputBindings.IsPressed(
                GameInputActionId.AlternateItemModifier);
            bool controlHeld = GameInputBindings.IsPressed(
                GameInputActionId.SingleItemModifier);
            bool shiftHeld = GameInputBindings.IsPressed(
                GameInputActionId.QuickTransferModifier);
            IVariableInventoryCell currentCell = ResolveCurrentCell(eventData);
            IVariableInventoryCell pressedCell = ResolvePressedCell(eventData);
            if (pressedCell != null)
            {
                // Drag thresholds can be crossed after the pointer entered a
                // neighboring cell. The pressed cell remains the authoritative source.
                stareCell = pressedCell;
            }

            if (IsClickCarryActive &&
                eventData.button == PointerEventData.InputButton.Left &&
                IsSinglePlacementModifierHeld())
            {
                // InputSystemUIInputModule can report BeginDrag after button release
                // when the threshold crossing and release occur in the same frame.
                // Keep the existing click-carry untouched in that case.
                if (eventData.pointerPress == null && eventData.rawPointerPress == null)
                {
                    consumeReleasedBeginDragEnd = true;
                    return;
                }

                singlePlacementDragActive = true;
                consumeSinglePlacementEndDrag = true;
                singlePlacementVisitedCells.Clear();
                TryPaintSingleItem(pressedCell ?? stareCell);
                if (currentCell != null && !ReferenceEquals(currentCell, pressedCell))
                {
                    // Pointer-enter is processed before BeginDrag. Paint the current
                    // hover explicitly so the first threshold-crossed cell is not lost.
                    stareCell = currentCell;
                    TryPaintSingleItem(currentCell);
                }

                UpdateDropPreviewHandling();
                return;
            }

            if (eventData.button == PointerEventData.InputButton.Left && shiftHeld &&
                (altHeld || controlHeld))
            {
                return;
            }

            if (eventData.button == PointerEventData.InputButton.Left && altHeld)
            {
                if (stareCell?.CellData != null)
                {
                    AlternateItemActionRequested?.Invoke(
                        FindOwningView(stareCell),
                        stareCell,
                        VariableInventoryCarryMode.Pointer);
                }

                return;
            }

            base.OnBeginDrag(eventData);
            RefreshEffectCellQuantityBadge();
        }

        public override void OnEndDrag(PointerEventData eventData)
        {
            if (consumeReleasedBeginDragEnd)
            {
                consumeReleasedBeginDragEnd = false;
                return;
            }

            if (consumeSinglePlacementEndDrag)
            {
                ResetSinglePlacementGesture();
                return;
            }

            base.OnEndDrag(eventData);
        }

        protected override void OnCellEnter(IVariableInventoryCell cell)
        {
            base.OnCellEnter(cell);
            if (singlePlacementDragActive)
            {
                TryPaintSingleItem(cell);
            }
        }

        protected override bool TryGetDropPreviewHandlingOverride(
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData carriedItem,
            out VariableInventoryDropHandling handling)
        {
            bool singlePlacementPreview = IsClickCarryActive &&
                                          (singlePlacementDragActive ||
                                           IsSinglePlacementModifierHeld());
            if (!singlePlacementPreview ||
                !(carriedItem is IVariableInventoryStackCellData stackData) ||
                stackData.MaxStackSize <= 1 || stackData.Quantity <= 0 ||
                !(destinationView is IVariableInventoryPartialDropView partialDropView))
            {
                handling = VariableInventoryDropHandling.Standard;
                return false;
            }

            handling = CanPlaceSingleFromCarriedStack(
                           CarryOriginView,
                           destinationView,
                           carriedItem) &&
                       partialDropView.TryResolvePartialDrop(
                           destinationCell,
                           carriedItem,
                           out _,
                           out _,
                           out _)
                ? VariableInventoryDropHandling.Standard
                : VariableInventoryDropHandling.Reject;
            return true;
        }

        protected virtual bool IsSinglePlacementModifierHeld()
        {
            bool controlHeld = GameInputBindings.IsPressed(
                GameInputActionId.SingleItemModifier);
            bool altHeld = GameInputBindings.IsPressed(
                GameInputActionId.AlternateItemModifier);
            bool shiftHeld = GameInputBindings.IsPressed(
                GameInputActionId.QuickTransferModifier);
            return controlHeld && !altHeld && !shiftHeld;
        }

        private IVariableInventoryCell ResolvePressedCell(PointerEventData eventData)
        {
            GameObject pressed = eventData?.pointerPress ?? eventData?.rawPointerPress;
            VariableInventoryCell cell = pressed != null
                ? pressed.GetComponentInParent<VariableInventoryCell>()
                : null;
            return cell != null && FindOwningView(cell) != null ? cell : stareCell;
        }

        private IVariableInventoryCell ResolveCurrentCell(PointerEventData eventData)
        {
            GameObject current = eventData?.pointerCurrentRaycast.gameObject;
            VariableInventoryCell cell = current != null
                ? current.GetComponentInParent<VariableInventoryCell>()
                : null;
            return cell != null && FindOwningView(cell) != null ? cell : null;
        }

        protected override void OnCarriedItemChanged()
        {
            RefreshEffectCellQuantityBadge();
        }

        protected override void OnCarryStateCleared()
        {
            ResetSinglePlacementGesture();
        }

        private void TryPaintSingleItem(IVariableInventoryCell cell)
        {
            if (!singlePlacementDragActive || cell == null ||
                !singlePlacementVisitedCells.Add(cell))
            {
                return;
            }

            TryPlaceSingleFromClickCarry(cell);
            UpdateDropPreviewHandling();
        }

        private void ResetSinglePlacementGesture()
        {
            singlePlacementDragActive = false;
            consumeSinglePlacementEndDrag = false;
            consumeReleasedBeginDragEnd = false;
            singlePlacementVisitedCells.Clear();
        }

        private void RefreshEffectCellQuantityBadge()
        {
            if (effectCell is StandardCell standardCell)
            {
                string quantity = effectCell.CellData != null &&
                                  quantityBadgeTextProvider != null
                    ? quantityBadgeTextProvider(effectCell.CellData)
                    : null;
                standardCell.SetQuantityBadgeText(quantity);
            }
        }
    }
}
