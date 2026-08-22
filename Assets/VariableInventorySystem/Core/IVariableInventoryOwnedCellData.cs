namespace VariableInventorySystem
{
    /// <summary>
    /// Optional ownership contract for runtime items that must belong to at most one
    /// inventory container at a time. A drag may temporarily detach an item, but it
    /// must either attach it to the destination or restore it to the source.
    /// </summary>
    public interface IVariableInventoryOwnedCellData : IVariableInventoryCellData
    {
        IVariableInventoryViewData InventoryOwner { get; }

        bool TryChangeInventoryOwner(
            IVariableInventoryViewData expectedOwner,
            IVariableInventoryViewData newOwner);
    }
}
