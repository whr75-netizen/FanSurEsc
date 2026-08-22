using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace VariableInventorySystem
{
    public class StandardCaseViewData : StandardStashViewData
    {
        public StandardCaseViewData(int capacityWidth, int capacityHeight) : base(capacityWidth, capacityHeight)
        {
        }

        public StandardCaseViewData(IVariableInventoryCellData[] cellData, int capacityWidth, int capacityHeight) : base(cellData, capacityWidth, capacityHeight)
        {
        }

        public override int? GetInsertableId(IVariableInventoryCellData cellData)
        {
            if (WouldCreateContainerCycle(cellData))
            {
                return null;
            }

            return base.GetInsertableId(cellData);
        }

        public override bool CheckInsert(int id, VariableInventorySystem.IVariableInventoryCellData cellData)
        {
            if (WouldCreateContainerCycle(cellData))
            {
                return false;
            }

            return base.CheckInsert(id, cellData);
        }

        private bool WouldCreateContainerCycle(IVariableInventoryCellData cellData)
        {
            if (!(cellData is IStandardCaseCellData caseData) || caseData.CaseData == null)
            {
                return false;
            }

            return ContainsGrid(caseData.CaseData, this, new HashSet<StandardStashViewData>());
        }

        private static bool ContainsGrid(
            StandardStashViewData current,
            StandardStashViewData target,
            HashSet<StandardStashViewData> visited)
        {
            if (ReferenceEquals(current, target))
            {
                return true;
            }

            // A candidate subtree that is already cyclic is invalid as well.
            if (current == null || !visited.Add(current))
            {
                return current != null;
            }

            foreach (IVariableInventoryCellData item in current.CellData)
            {
                if (item is IStandardCaseCellData nested &&
                    ContainsGrid(nested.CaseData, target, visited))
                {
                    return true;
                }
            }

            return false;
        }
    }
}
