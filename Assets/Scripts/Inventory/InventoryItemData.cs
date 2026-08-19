using System;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    public class InventoryItemData : IVariableInventoryCellData
    {
        private readonly IVariableInventoryAsset imageAsset;

        public ItemDefinition Definition { get; }
        public int Id => Definition.Id;
        public int Width => Definition.Width;
        public int Height => Definition.Height;
        public bool IsRotate { get; set; }
        public IVariableInventoryAsset ImageAsset => imageAsset;

        public InventoryItemData(ItemDefinition definition)
        {
            Definition = definition != null
                ? definition
                : throw new ArgumentNullException(nameof(definition));
            imageAsset = new StandardAsset(definition.Icon);
        }
    }

    public sealed class InventoryContainerItemData : InventoryItemData, IStandardCaseCellData
    {
        public StandardCaseViewData CaseData { get; }

        public InventoryContainerItemData(ItemDefinition definition) : base(definition)
        {
            if (!definition.IsContainer)
            {
                throw new ArgumentException(
                    $"Item definition {definition.Id} is not configured as a container.",
                    nameof(definition));
            }

            CaseData = new StandardCaseViewData(
                definition.ContainerWidth,
                definition.ContainerHeight);
        }
    }

    public static class InventoryItemDataFactory
    {
        public static IVariableInventoryCellData Create(ItemDefinition definition)
        {
            if (definition == null)
            {
                throw new ArgumentNullException(nameof(definition));
            }

            return definition.IsContainer
                ? new InventoryContainerItemData(definition)
                : new InventoryItemData(definition);
        }
    }
}
