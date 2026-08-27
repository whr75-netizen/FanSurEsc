using System;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    public static class InventoryGridConstraints
    {
        public const int MaxDimension = 256;
        public const int MaxCellCount = 65536;

        public static bool TryValidateDimensions(int width, int height, out string error)
        {
            long cellCount = (long)width * height;
            if (width <= 0 || width > MaxDimension ||
                height <= 0 || height > MaxDimension ||
                cellCount <= 0 || cellCount > MaxCellCount)
            {
                error = $"Inventory grid {width}x{height} exceeds the supported " +
                        $"{MaxDimension}x{MaxDimension} / {MaxCellCount}-cell limit.";
                return false;
            }

            error = null;
            return true;
        }
    }

    public class InventoryItemData : IVariableInventoryOwnedCellData
    {
        private readonly IVariableInventoryAsset imageAsset;
        private readonly int quantity;

        public ItemDefinition Definition { get; }
        public int Id => Definition.Id;
        public int Width => Definition.Width;
        public int Height => Definition.Height;
        public bool IsRotate { get; set; }
        public IVariableInventoryAsset ImageAsset => imageAsset;
        public IVariableInventoryViewData InventoryOwner { get; private set; }
        public int Quantity => quantity;
        public int MaxStackSize => Definition.MaxStackSize;

        public InventoryItemData(ItemDefinition definition, int quantity = 1)
        {
            Definition = definition != null
                ? definition
                : throw new ArgumentNullException(nameof(definition));

            if (!definition.TryValidateInventoryShape(out string error))
            {
                throw new ArgumentException(error, nameof(definition));
            }

            if (quantity <= 0 || quantity > definition.MaxStackSize)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(quantity),
                    quantity,
                    $"Item definition {definition.Id} requires a quantity from 1 to " +
                    $"{definition.MaxStackSize}.");
            }

            this.quantity = quantity;
            imageAsset = new StandardAsset(definition.Icon);
        }

        public bool TryChangeInventoryOwner(
            IVariableInventoryViewData expectedOwner,
            IVariableInventoryViewData newOwner)
        {
            if (!ReferenceEquals(InventoryOwner, expectedOwner))
            {
                return false;
            }

            InventoryOwner = newOwner;
            return true;
        }
    }

    public sealed class InventoryContainerItemData : InventoryItemData, IStandardCaseCellData
    {
        public StandardCaseViewData CaseData { get; }

        public InventoryContainerItemData(ItemDefinition definition, int quantity = 1)
            : base(definition, quantity)
        {
            if (!definition.IsContainer)
            {
                throw new ArgumentException(
                    $"Item definition {definition.Id} is not configured as a container.",
                    nameof(definition));
            }

            if (!InventoryGridConstraints.TryValidateDimensions(
                    definition.ContainerWidth,
                    definition.ContainerHeight,
                    out string error))
            {
                throw new ArgumentException(
                    $"Item definition {definition.Id} has invalid container dimensions: {error}",
                    nameof(definition));
            }

            CaseData = new StandardCaseViewData(
                definition.ContainerWidth,
                definition.ContainerHeight);
        }
    }

    public static class InventoryItemDataFactory
    {
        public static IVariableInventoryCellData Create(ItemDefinition definition, int quantity = 1)
        {
            if (!TryCreate(definition, quantity, out IVariableInventoryCellData item, out string error))
            {
                throw new ArgumentException(error, nameof(definition));
            }

            return item;
        }

        public static bool TryCreate(
            ItemDefinition definition,
            out IVariableInventoryCellData item,
            out string error)
        {
            return TryCreate(definition, 1, out item, out error);
        }

        public static bool TryCreate(
            ItemDefinition definition,
            int quantity,
            out IVariableInventoryCellData item,
            out string error)
        {
            item = null;
            if (definition == null)
            {
                error = "Item definition is missing.";
                return false;
            }

            if (!definition.TryValidateInventoryShape(out error))
            {
                return false;
            }

            try
            {
                item = definition.IsContainer
                    ? new InventoryContainerItemData(definition, quantity)
                    : new InventoryItemData(definition, quantity);
            }
            catch (ArgumentException exception)
            {
                error = exception.Message;
                return false;
            }

            error = null;
            return true;
        }
    }
}
