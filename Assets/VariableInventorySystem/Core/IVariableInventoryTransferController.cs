namespace VariableInventorySystem
{
    public enum VariableInventoryDropHandling
    {
        Standard = 0,
        AcceptWithoutInsert = 1,
        Reject = 2
    }

    public interface IVariableInventoryStackMergeReceipt
    {
        IVariableInventoryCellData TargetItem { get; }
        int MovedQuantity { get; }
        int RemainingQuantity { get; }
        bool TryRollback(out string error);
    }

    /// <summary>
    /// Optional game-rule boundary around the inventory asset's drag mechanics.
    /// The core still owns pick/drop/rollback; this controller only authorizes and
    /// observes transfers such as merchant purchase and sale.
    /// </summary>
    public interface IVariableInventoryTransferController
    {
        bool HandleQuickTransfer(
            IVariableInventoryView sourceView,
            IVariableInventoryCellData item);

        VariableInventoryDropHandling GetDropHandling(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item);

        VariableInventoryDropHandling GetDropPreviewHandling(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item);

        bool CanMergeStack(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item);

        bool TryMergeStack(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item,
            // A non-null receipt on false means a mutation could not be rolled back.
            // The caller must keep the carried item detached and retry the receipt.
            out IVariableInventoryStackMergeReceipt receipt,
            out string error);

        void OnDropCompleted(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item,
            VariableInventoryDropHandling handling);
    }

    public interface IVariableInventoryBoundView : IVariableInventoryView
    {
        IVariableInventoryViewData ViewData { get; }
        bool ContainsCell(IVariableInventoryCell cell);
        void SetDropPreviewHandling(VariableInventoryDropHandling? handling);
    }
}
