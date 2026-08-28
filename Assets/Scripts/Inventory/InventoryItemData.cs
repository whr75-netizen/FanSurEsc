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

    public class InventoryItemData : IVariableInventoryOwnedCellData, IVariableInventoryStackCellData
    {
        private readonly IVariableInventoryAsset imageAsset;
        private int quantity;
        private int loadedAmmunition;

        public ItemDefinition Definition { get; }
        public int Id => Definition.Id;
        public int Width => Definition.Width;
        public int Height => Definition.Height;
        public bool IsRotate { get; set; }
        public IVariableInventoryAsset ImageAsset => imageAsset;
        public IVariableInventoryViewData InventoryOwner { get; private set; }
        public int Quantity => quantity;
        public int MaxStackSize => Definition.MaxStackSize;
        public int LoadedAmmunition => loadedAmmunition;
        public int MagazineCapacity => Definition.IsWeapon ? Definition.MagazineCapacity : 0;

        public InventoryItemData(ItemDefinition definition, int quantity = 1)
            : this(definition, quantity, 0)
        {
        }

        internal InventoryItemData(
            ItemDefinition definition,
            int quantity,
            int initialLoadedAmmunition)
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

            int maximumLoadedAmmunition = definition.IsWeapon
                ? definition.MagazineCapacity
                : 0;
            if (initialLoadedAmmunition < 0 ||
                initialLoadedAmmunition > maximumLoadedAmmunition)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(initialLoadedAmmunition),
                    initialLoadedAmmunition,
                    $"Item definition {definition.Id} requires loaded ammunition from 0 to " +
                    $"{maximumLoadedAmmunition}.");
            }

            this.quantity = quantity;
            loadedAmmunition = initialLoadedAmmunition;
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

        public bool TryChangeQuantity(
            IVariableInventoryViewData expectedOwner,
            int expectedQuantity,
            int newQuantity,
            out string error)
        {
            if (!ReferenceEquals(InventoryOwner, expectedOwner))
            {
                error = "The item owner changed before its quantity could be updated.";
                return false;
            }

            if (quantity != expectedQuantity)
            {
                error = "The item quantity changed before the requested update.";
                return false;
            }

            if (newQuantity <= 0 || newQuantity > MaxStackSize)
            {
                error = $"Item definition {Definition.Id} requires a quantity from 1 to " +
                        $"{MaxStackSize}.";
                return false;
            }

            quantity = newQuantity;
            if (InventoryOwner != null)
            {
                InventoryOwner.IsDirty = true;
            }

            error = null;
            return true;
        }

        public bool TryChangeLoadedAmmunition(
            IVariableInventoryViewData expectedOwner,
            int expectedLoadedAmmunition,
            int newLoadedAmmunition,
            out string error)
        {
            if (!Definition.IsWeapon)
            {
                error = $"Item definition {Definition.Id} is not a weapon.";
                return false;
            }

            if (!ReferenceEquals(InventoryOwner, expectedOwner))
            {
                error = "The weapon owner changed before its loaded ammunition could be updated.";
                return false;
            }

            if (loadedAmmunition != expectedLoadedAmmunition)
            {
                error = "The weapon's loaded ammunition changed before the requested update.";
                return false;
            }

            if (newLoadedAmmunition < 0 || newLoadedAmmunition > MagazineCapacity)
            {
                error = $"Weapon definition {Definition.Id} requires loaded ammunition from 0 " +
                        $"to {MagazineCapacity}.";
                return false;
            }

            loadedAmmunition = newLoadedAmmunition;
            if (InventoryOwner != null)
            {
                InventoryOwner.IsDirty = true;
            }

            error = null;
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
            return TryCreate(
                definition,
                quantity,
                0,
                out item,
                out error);
        }

        public static bool TryCreate(
            ItemDefinition definition,
            int quantity,
            int loadedAmmunition,
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

            if (definition.IsContainer && loadedAmmunition != 0)
            {
                error = $"Container item definition {definition.Id} cannot carry loaded ammunition.";
                return false;
            }

            try
            {
                item = definition.IsContainer
                    ? new InventoryContainerItemData(definition, quantity)
                    : new InventoryItemData(definition, quantity, loadedAmmunition);
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
