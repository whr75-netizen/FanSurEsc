using System.Collections.Generic;
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

        public event System.Action<IVariableInventoryView, IVariableInventoryCell>
            ItemContextRequested;
        public event System.Action<
                IVariableInventoryView,
                IVariableInventoryCell,
                VariableInventoryCarryMode>
            StackSplitRequested;

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
            if (IsClickCarryActive)
            {
                TryReleaseClickCarry(cell);
                return;
            }

            if (cell?.CellData == null)
            {
                return;
            }

            bool altHeld = Input.GetKey(KeyCode.LeftAlt) ||
                           Input.GetKey(KeyCode.RightAlt);
            bool controlHeld = Input.GetKey(KeyCode.LeftControl) ||
                               Input.GetKey(KeyCode.RightControl);
            bool shiftHeld = Input.GetKey(KeyCode.LeftShift) ||
                             Input.GetKey(KeyCode.RightShift);
            if ((altHeld || controlHeld) && shiftHeld)
            {
                return;
            }

            IVariableInventoryView sourceView = FindOwningView(cell);
            if (altHeld)
            {
                StackSplitRequested?.Invoke(
                    sourceView,
                    cell,
                    VariableInventoryCarryMode.Click);
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
            System.Func<IVariableInventoryCellData, int, int, bool> stackMergeRecorded,
            out string error)
        {
            if (!TryBeginDetachedCarry(
                    sourceView,
                    sourceCell,
                    splitItem,
                    carryMode,
                    rollback,
                    commit,
                    stackMergeRecorded,
                    out error))
            {
                return false;
            }

            RefreshEffectCellQuantityBadge();
            return true;
        }

        public override void OnBeginDrag(PointerEventData eventData)
        {
            bool altHeld = Input.GetKey(KeyCode.LeftAlt) ||
                           Input.GetKey(KeyCode.RightAlt);
            bool controlHeld = Input.GetKey(KeyCode.LeftControl) ||
                               Input.GetKey(KeyCode.RightControl);
            bool shiftHeld = Input.GetKey(KeyCode.LeftShift) ||
                             Input.GetKey(KeyCode.RightShift);
            IVariableInventoryCell pressedCell = ResolvePressedCell(eventData);
            if (pressedCell != null)
            {
                // Drag thresholds can be crossed after the pointer entered a
                // neighboring cell. The pressed cell remains the authoritative source.
                stareCell = pressedCell;
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
                    StackSplitRequested?.Invoke(
                        FindOwningView(stareCell),
                        stareCell,
                        VariableInventoryCarryMode.Pointer);
                }

                return;
            }

            base.OnBeginDrag(eventData);
            RefreshEffectCellQuantityBadge();
        }

        private IVariableInventoryCell ResolvePressedCell(PointerEventData eventData)
        {
            GameObject pressed = eventData?.pointerPress ?? eventData?.rawPointerPress;
            VariableInventoryCell cell = pressed != null
                ? pressed.GetComponentInParent<VariableInventoryCell>()
                : null;
            return cell != null && FindOwningView(cell) != null ? cell : stareCell;
        }

        protected override void OnCarriedItemChanged()
        {
            RefreshEffectCellQuantityBadge();
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
