using System.Collections.Generic;
using UnityEngine;

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
            if ((Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift)) &&
                cell?.CellData != null)
            {
                foreach (IVariableInventoryView view in InventoryViews)
                {
                    if (view is IVariableInventoryBoundView boundView &&
                        boundView.ContainsCell(cell) &&
                        TryHandleQuickTransfer(view, cell.CellData))
                    {
                        return;
                    }
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
    }
}
