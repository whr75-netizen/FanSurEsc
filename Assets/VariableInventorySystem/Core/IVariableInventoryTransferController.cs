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

    public interface IVariableInventorySinglePlacementReceipt
    {
        IVariableInventoryCellData PlacedItem { get; }
        int MovedQuantity { get; }
        int RemainingQuantity { get; }
        bool TryRollback(out string error);
    }

    /// <summary>
    /// A provisional receiver for a carried item outside registered inventory
    /// views. The inventory core keeps the source rollback state until this
    /// receipt commits; a failed commit restores the receiver before the ordinary
    /// source rollback path continues.
    /// </summary>
    public interface IVariableInventoryExternalDropReceipt
    {
        bool TryCommit(out string error);
        bool TryRollback(out string error);
    }

    public interface IVariableInventoryExternalDropController
    {
        bool TryStageExternalDrop(
            IVariableInventoryView sourceView,
            IVariableInventoryCellData item,
            out IVariableInventoryExternalDropReceipt receipt,
            out string error);
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

        bool TryPlaceSingleFromCarriedStack(
            IVariableInventoryView sourceView,
            IVariableInventoryPartialDropView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item,
            out IVariableInventorySinglePlacementReceipt receipt,
            out string error);

        bool CanPlaceSingleFromCarriedStack(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item);

        // Lightweight read-only observer boundary for authoritative owner/quantity
        // changes. Implementations must not start another transfer synchronously.
        void OnInventoryContentsChanged();

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

    public interface IVariableInventoryPartialDropView : IVariableInventoryBoundView
    {
        bool TryResolvePartialDrop(
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData detachedItem,
            out IVariableInventoryViewData destinationOwner,
            out int destinationIndex,
            out string error);
    }
}
