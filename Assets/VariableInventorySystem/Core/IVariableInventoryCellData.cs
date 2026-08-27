namespace VariableInventorySystem
{
    public interface IVariableInventoryCellData
    {
        int Id { get; }
        int Width { get; }
        int Height { get; }
        bool IsRotate { get; set; }
        IVariableInventoryAsset ImageAsset { get; }
    }

    /// <summary>
    /// Optional runtime contract for cell data that represents a quantity stack.
    /// The inventory core reads this boundary only to choose between placing the
    /// final item and asking the transfer authority to separate one unit.
    /// </summary>
    public interface IVariableInventoryStackCellData : IVariableInventoryCellData
    {
        int Quantity { get; }
        int MaxStackSize { get; }
    }
}
