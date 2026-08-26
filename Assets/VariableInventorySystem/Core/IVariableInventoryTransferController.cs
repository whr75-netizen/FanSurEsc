namespace VariableInventorySystem
{
    public enum VariableInventoryDropHandling
    {
        Standard = 0,
        AcceptWithoutInsert = 1,
        Reject = 2
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
