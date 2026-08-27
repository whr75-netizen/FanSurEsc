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

        public event System.Action<IVariableInventoryView, IVariableInventoryCell, bool>
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

            bool controlHeld = Input.GetKey(KeyCode.LeftControl) ||
                               Input.GetKey(KeyCode.RightControl);
            bool shiftHeld = Input.GetKey(KeyCode.LeftShift) ||
                             Input.GetKey(KeyCode.RightShift);
            if (controlHeld && shiftHeld)
            {
                return;
            }

            IVariableInventoryView sourceView = FindOwningView(cell);
            if (controlHeld)
            {
                StackSplitRequested?.Invoke(sourceView, cell, true);
                return;
            }

            if (shiftHeld)
            {
                if (sourceView != null && TryHandleQuickTransfer(sourceView, cell.CellData))
                {
                    return;
                }
            }

            if (cell.CellData is IStandardCaseCellData caseData)
            {
                if (popupList.Contains(caseData))
                {
                    return;
                }

                popupList.Add(caseData);

                var standardCaseViewPopup = Instantiate(casePopupPrefab, caseParent).GetComponent<StandardCaseViewPopup>();
                AddInventoryView(standardCaseViewPopup.StandardCaseView);

                standardCaseViewPopup.Open(
                    caseData,
                    () =>
                    {
                        RemoveInventoryView(standardCaseViewPopup.StandardCaseView);
                        Destroy(standardCaseViewPopup.gameObject);
                        popupList.Remove(caseData);
                    });
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
                StackSplitRequested?.Invoke(FindOwningView(cell), cell, false);
            }
        }

        public bool TryBeginStackSplitCarry(
            IVariableInventoryView sourceView,
            IVariableInventoryCell sourceCell,
            IVariableInventoryCellData splitItem,
            System.Func<bool> rollback,
            System.Func<bool> commit,
            out string error)
        {
            if (!TryBeginClickCarry(
                    sourceView,
                    sourceCell,
                    splitItem,
                    rollback,
                    commit,
                    out error))
            {
                return false;
            }

            RefreshEffectCellQuantityBadge();
            return true;
        }

        public override void OnBeginDrag(PointerEventData eventData)
        {
            base.OnBeginDrag(eventData);
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
