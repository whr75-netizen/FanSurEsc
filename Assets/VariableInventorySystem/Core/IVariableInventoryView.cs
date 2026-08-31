using System;
using UnityEngine.EventSystems;

namespace VariableInventorySystem
{
    public interface IVariableInventoryView
    {
        void SetCellCallback(
            Action<IVariableInventoryCell> onCellClick,
            Action<IVariableInventoryCell> onCellOptionClick,
            Action<IVariableInventoryCell> onCellEnter,
            Action<IVariableInventoryCell> onCellExit);

        void Apply(IVariableInventoryViewData data);
        void ReApply();

        void OnPrePick(IVariableInventoryCell stareCell);
        bool OnPick(IVariableInventoryCell stareCell);
        void OnDrag(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell, PointerEventData cursorPosition);
        bool OnDrop(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell);
        void OnDroped(bool isDroped);

        void OnCellEnter(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell);
        void OnCellExit(IVariableInventoryCell stareCell);

        void OnSwitchRotate(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell);
    }

    /// <summary>
    /// Optional source contract for a carry whose authoritative item remains in
    /// its original owner until a valid drop is committed. The source owns the
    /// complete cross-container transaction so preview and commit can include
    /// rules that ordinary detached-item placement cannot express.
    /// </summary>
    public interface IVariableInventoryDeferredDropSource
    {
        bool IsDeferredDropActive(IVariableInventoryCellData item);

        VariableInventoryDropHandling GetDeferredDropPreviewHandling(
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item);

        bool TryCompleteDeferredDrop(
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item,
            out string error);

        bool TryPrepareDeferredExternalDrop(
            IVariableInventoryCellData item,
            out string error);
    }

    /// <summary>
    /// Resolves the exact logical owner and slot under a visual drop target
    /// without mutating either source or destination. The expected source owner
    /// permits a deferred item to be checked while it is still authoritative in
    /// that owner.
    /// </summary>
    public interface IVariableInventoryDeferredDropTarget : IVariableInventoryView
    {
        bool TryResolveDeferredDropTarget(
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item,
            IVariableInventoryViewData expectedSourceOwner,
            out IVariableInventoryViewData destinationOwner,
            out int destinationIndex,
            out string error);
    }
}
