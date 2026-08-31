using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using FantasySurvival.Trading;
using UnityEngine;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    public enum EquipmentSlotType
    {
        None = 0,
        Headgear = 1,
        BodyArmor = 2,
        FunctionalShoes = 3,
        Backpack = 4,
        Necklace = 5,
        Ring = 6,
        Pendant = 7,
        CosmeticHead = 8,
        CosmeticTop = 9,
        CosmeticBottom = 10,
        CosmeticShoes = 11,
        Weapon = 12
    }

    public enum EquipmentSlotId
    {
        None = 0,
        Headgear = 1,
        BodyArmor = 2,
        FunctionalShoes = 3,
        Backpack = 4,
        Necklace = 5,
        Ring = 6,
        Pendant = 7,
        CosmeticHead = 8,
        CosmeticTop = 9,
        CosmeticBottom = 10,
        CosmeticShoes = 11,
        Weapon1 = 12,
        Weapon2 = 13,
        Weapon3 = 14
    }

    public static class EquipmentSlotCatalog
    {
        public const int WeaponSlotCount = 3;

        private static readonly EquipmentSlotId[] orderedSlots =
        {
            EquipmentSlotId.Headgear,
            EquipmentSlotId.BodyArmor,
            EquipmentSlotId.FunctionalShoes,
            EquipmentSlotId.Backpack,
            EquipmentSlotId.Necklace,
            EquipmentSlotId.Ring,
            EquipmentSlotId.Pendant,
            EquipmentSlotId.CosmeticHead,
            EquipmentSlotId.CosmeticTop,
            EquipmentSlotId.CosmeticBottom,
            EquipmentSlotId.CosmeticShoes,
            EquipmentSlotId.Weapon1,
            EquipmentSlotId.Weapon2,
            EquipmentSlotId.Weapon3
        };

        public static IReadOnlyList<EquipmentSlotId> OrderedSlots => orderedSlots;
        public static int Count => orderedSlots.Length;

        public static bool IsValid(EquipmentSlotId slot)
        {
            return slot >= EquipmentSlotId.Headgear && slot <= EquipmentSlotId.Weapon3;
        }

        public static int GetIndex(EquipmentSlotId slot)
        {
            return IsValid(slot) ? (int)slot - 1 : -1;
        }

        public static EquipmentSlotId GetSlotAtIndex(int index)
        {
            return index >= 0 && index < orderedSlots.Length
                ? orderedSlots[index]
                : EquipmentSlotId.None;
        }

        public static EquipmentSlotType GetSlotType(EquipmentSlotId slot)
        {
            if (!IsValid(slot))
            {
                return EquipmentSlotType.None;
            }

            return slot >= EquipmentSlotId.Weapon1
                ? EquipmentSlotType.Weapon
                : (EquipmentSlotType)slot;
        }

        public static EquipmentSlotId GetPrimarySlot(EquipmentSlotType type)
        {
            if (type == EquipmentSlotType.None)
            {
                return EquipmentSlotId.None;
            }

            return type == EquipmentSlotType.Weapon
                ? EquipmentSlotId.Weapon1
                : (EquipmentSlotId)type;
        }

        public static EquipmentSlotId GetWeaponSlot(int oneBasedNumber)
        {
            switch (oneBasedNumber)
            {
                case 1: return EquipmentSlotId.Weapon1;
                case 2: return EquipmentSlotId.Weapon2;
                case 3: return EquipmentSlotId.Weapon3;
                default: return EquipmentSlotId.None;
            }
        }

        public static int GetWeaponNumber(EquipmentSlotId slot)
        {
            return slot >= EquipmentSlotId.Weapon1 && slot <= EquipmentSlotId.Weapon3
                ? (int)slot - (int)EquipmentSlotId.Weapon1 + 1
                : 0;
        }

        public static string GetDisplayName(EquipmentSlotId slot)
        {
            switch (slot)
            {
                case EquipmentSlotId.Headgear: return "모자";
                case EquipmentSlotId.BodyArmor: return "갑빠";
                case EquipmentSlotId.FunctionalShoes: return "신발";
                case EquipmentSlotId.Backpack: return "가방";
                case EquipmentSlotId.Necklace: return "목걸이";
                case EquipmentSlotId.Ring: return "반지";
                case EquipmentSlotId.Pendant: return "팬던트";
                case EquipmentSlotId.CosmeticHead: return "꾸밈 머리";
                case EquipmentSlotId.CosmeticTop: return "꾸밈 상의";
                case EquipmentSlotId.CosmeticBottom: return "꾸밈 하의";
                case EquipmentSlotId.CosmeticShoes: return "꾸밈 신발";
                case EquipmentSlotId.Weapon1: return "무기 1";
                case EquipmentSlotId.Weapon2: return "무기 2";
                case EquipmentSlotId.Weapon3: return "무기 3";
                default: return "장비 없음";
            }
        }

        public static string GetShortLabel(EquipmentSlotId slot)
        {
            switch (slot)
            {
                case EquipmentSlotId.Headgear: return "HAT";
                case EquipmentSlotId.BodyArmor: return "ARM";
                case EquipmentSlotId.FunctionalShoes: return "SHO";
                case EquipmentSlotId.Backpack: return "BAG";
                case EquipmentSlotId.Necklace: return "NEC";
                case EquipmentSlotId.Ring: return "RNG";
                case EquipmentSlotId.Pendant: return "PEN";
                case EquipmentSlotId.CosmeticHead: return "C-H";
                case EquipmentSlotId.CosmeticTop: return "C-T";
                case EquipmentSlotId.CosmeticBottom: return "C-B";
                case EquipmentSlotId.CosmeticShoes: return "C-S";
                case EquipmentSlotId.Weapon1: return "W1";
                case EquipmentSlotId.Weapon2: return "W2";
                case EquipmentSlotId.Weapon3: return "W3";
                default: return "---";
            }
        }
    }

    public sealed class EquipmentLoadoutData : IVariableInventoryViewData
    {
        private readonly IVariableInventoryCellData[] items =
            new IVariableInventoryCellData[EquipmentSlotCatalog.Count];

        public event Action Changed;

        public bool IsDirty { get; set; } = true;

        public IVariableInventoryCellData GetItem(EquipmentSlotId slot)
        {
            int index = EquipmentSlotCatalog.GetIndex(slot);
            return index >= 0 ? items[index] : null;
        }

        public int? GetId(IVariableInventoryCellData cellData)
        {
            if (cellData == null)
            {
                return null;
            }

            for (int i = 0; i < items.Length; i++)
            {
                if (ReferenceEquals(items[i], cellData))
                {
                    return i;
                }
            }

            return null;
        }

        public int? GetInsertableId(IVariableInventoryCellData cellData)
        {
            if (!(cellData is InventoryItemData item))
            {
                return null;
            }

            EquipmentSlotId slot = GetFirstAvailableSlot(item.Definition);
            int index = EquipmentSlotCatalog.GetIndex(slot);
            return index >= 0 && CheckInsert(index, cellData) ? index : (int?)null;
        }

        public EquipmentSlotId GetFirstAvailableSlot(ItemDefinition definition)
        {
            if (definition == null || !definition.IsEquippable)
            {
                return EquipmentSlotId.None;
            }

            foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
            {
                int index = EquipmentSlotCatalog.GetIndex(slot);
                if (items[index] == null && definition.CanEquipIn(slot))
                {
                    return slot;
                }
            }

            return EquipmentSlotId.None;
        }

        public bool CheckInsert(int id, IVariableInventoryCellData cellData)
        {
            if (id < 0 || id >= items.Length || items[id] != null ||
                !(cellData is InventoryItemData item))
            {
                return false;
            }

            EquipmentSlotId slot = EquipmentSlotCatalog.GetSlotAtIndex(id);
            if (!item.Definition.CanEquipIn(slot))
            {
                return false;
            }

            return !(cellData is IVariableInventoryOwnedCellData owned) || owned.InventoryOwner == null;
        }

        public void InsertInventoryItem(int id, IVariableInventoryCellData cellData)
        {
            if (id < 0 || id >= items.Length)
            {
                throw new ArgumentOutOfRangeException(nameof(id));
            }

            var previous = items[id];
            if (ReferenceEquals(previous, cellData))
            {
                return;
            }

            if (cellData != null && !CheckInsert(id, cellData))
            {
                throw new InvalidOperationException("The item cannot be equipped in this slot.");
            }

            if (previous is IVariableInventoryOwnedCellData outgoing &&
                !outgoing.TryChangeInventoryOwner(this, null))
            {
                throw new InvalidOperationException("The equipped item ownership is inconsistent.");
            }

            if (cellData is IVariableInventoryOwnedCellData incoming &&
                !incoming.TryChangeInventoryOwner(null, this))
            {
                if (previous is IVariableInventoryOwnedCellData rollback)
                {
                    rollback.TryChangeInventoryOwner(null, this);
                }

                throw new InvalidOperationException("Could not attach the item to the equipment loadout.");
            }

            items[id] = cellData;
            IsDirty = true;
            NotifyChangedSafely();
        }

        public bool TryTake(EquipmentSlotId slot, out IVariableInventoryCellData item)
        {
            if (!TryTakeWithoutNotification(slot, out item, out _))
            {
                return false;
            }

            NotifyChangedSafely();
            return true;
        }

        public bool TryPlace(EquipmentSlotId slot, IVariableInventoryCellData item)
        {
            if (!TryPlaceWithoutNotification(slot, item, out _))
            {
                return false;
            }

            NotifyChangedSafely();
            return true;
        }

        internal bool TryTakeWithoutNotification(
            EquipmentSlotId slot,
            out IVariableInventoryCellData item,
            out string error)
        {
            item = null;
            int index = EquipmentSlotCatalog.GetIndex(slot);
            if (index < 0 || items[index] == null)
            {
                error = $"Equipment slot {slot} is empty.";
                return false;
            }

            IVariableInventoryCellData current = items[index];
            if (current is IVariableInventoryOwnedCellData owned &&
                !owned.TryChangeInventoryOwner(this, null))
            {
                error = $"The item ownership in equipment slot {slot} is inconsistent.";
                return false;
            }

            items[index] = null;
            IsDirty = true;
            item = current;
            error = null;
            return true;
        }

        internal bool TryPlaceWithoutNotification(
            EquipmentSlotId slot,
            IVariableInventoryCellData item,
            out string error)
        {
            int index = EquipmentSlotCatalog.GetIndex(slot);
            if (!CheckInsert(index, item))
            {
                error = $"The item cannot be equipped in {slot}.";
                return false;
            }

            if (item is IVariableInventoryOwnedCellData owned &&
                !owned.TryChangeInventoryOwner(null, this))
            {
                error = $"Could not attach the item to equipment slot {slot}.";
                return false;
            }

            items[index] = item;
            IsDirty = true;
            error = null;
            return true;
        }

        internal bool TryReplaceWithoutNotification(
            EquipmentSlotId slot,
            IVariableInventoryCellData expectedCurrent,
            IVariableInventoryCellData replacement,
            out IVariableInventoryCellData removed,
            out string error)
        {
            removed = null;
            int index = EquipmentSlotCatalog.GetIndex(slot);
            if (index < 0 || expectedCurrent == null || replacement == null ||
                !ReferenceEquals(items[index], expectedCurrent))
            {
                error = $"Equipment slot {slot} changed before it could be replaced.";
                return false;
            }

            if (!(replacement is InventoryItemData inventoryItem) ||
                inventoryItem.Definition == null ||
                !inventoryItem.Definition.CanEquipIn(slot))
            {
                error = $"The replacement item cannot be equipped in {slot}.";
                return false;
            }

            if (replacement is IVariableInventoryOwnedCellData replacementOwned &&
                replacementOwned.InventoryOwner != null)
            {
                error = "The replacement item already belongs to another inventory container.";
                return false;
            }

            if (expectedCurrent is IVariableInventoryOwnedCellData currentOwned &&
                !currentOwned.TryChangeInventoryOwner(this, null))
            {
                error = $"The current item ownership in equipment slot {slot} is inconsistent.";
                return false;
            }

            if (replacement is IVariableInventoryOwnedCellData incoming &&
                !incoming.TryChangeInventoryOwner(null, this))
            {
                bool rollbackSucceeded = !(expectedCurrent is IVariableInventoryOwnedCellData rollback) ||
                                         rollback.TryChangeInventoryOwner(null, this);
                error = $"Could not attach the replacement item to equipment slot {slot}." +
                        (rollbackSucceeded
                            ? string.Empty
                            : " The previous item ownership rollback also failed.");
                return false;
            }

            items[index] = replacement;
            IsDirty = true;
            removed = expectedCurrent;
            error = null;
            return true;
        }

        internal void NotifyOwnedItemStateChanged(InventoryItemData item)
        {
            if (item == null || !ReferenceEquals(item.InventoryOwner, this) ||
                !GetId(item).HasValue)
            {
                return;
            }

            IsDirty = true;
            NotifyChangedSafely();
        }

        internal bool TryClearAll(out string error)
        {
            return TryClearAll(true, out error);
        }

        internal bool TryClearAllWithoutNotification(out string error)
        {
            return TryClearAll(false, out error);
        }

        private bool TryClearAll(bool notifyChanged, out string error)
        {
            var occupied = new List<KeyValuePair<int, InventoryItemData>>();
            var seen = new HashSet<InventoryItemData>(
                InventoryReferenceComparer<InventoryItemData>.Instance);
            for (int index = 0; index < items.Length; index++)
            {
                IVariableInventoryCellData item = items[index];
                if (item == null)
                {
                    continue;
                }

                if (!(item is InventoryItemData inventoryItem))
                {
                    error = $"Equipment slot {index} contains an unsupported runtime item type.";
                    return false;
                }

                if (!seen.Add(inventoryItem))
                {
                    error = "The same item is equipped in more than one slot.";
                    return false;
                }

                if (!ReferenceEquals(inventoryItem.InventoryOwner, this))
                {
                    error = $"Equipment slot {index} has inconsistent item ownership.";
                    return false;
                }

                occupied.Add(new KeyValuePair<int, InventoryItemData>(index, inventoryItem));
            }

            if (occupied.Count == 0)
            {
                error = null;
                return true;
            }

            int detachedCount = 0;
            for (; detachedCount < occupied.Count; detachedCount++)
            {
                InventoryItemData item = occupied[detachedCount].Value;
                if (!item.TryChangeInventoryOwner(this, null))
                {
                    var rollbackFailures = new List<int>();
                    for (int rollback = detachedCount - 1; rollback >= 0; rollback--)
                    {
                        if (!occupied[rollback].Value.TryChangeInventoryOwner(null, this))
                        {
                            rollbackFailures.Add(occupied[rollback].Key);
                        }
                    }

                    error = $"Could not detach the item in equipment slot {occupied[detachedCount].Key}." +
                            (rollbackFailures.Count == 0
                                ? string.Empty
                                : $" Equipment ownership rollback also failed for slots {string.Join(", ", rollbackFailures)}.");
                    return false;
                }
            }

            foreach (KeyValuePair<int, InventoryItemData> placement in occupied)
            {
                items[placement.Key] = null;
            }

            IsDirty = true;
            if (notifyChanged)
            {
                NotifyChangedSafely();
            }
            error = null;
            return true;
        }

        internal void NotifyChangedSafely()
        {
            Delegate[] subscribers = Changed?.GetInvocationList();
            if (subscribers == null)
            {
                return;
            }

            foreach (Delegate subscriber in subscribers)
            {
                try
                {
                    ((Action)subscriber).Invoke();
                }
                catch (Exception exception)
                {
                    Debug.LogException(exception);
                }
            }
        }
    }

    public sealed class PlayerInventoryState
    {
        internal enum EquipmentTakeReceiptState
        {
            Invalid = 0,
            Staged = 1,
            Published = 2,
            Restored = 3
        }

        public sealed class EquipmentTakeReceipt
        {
            internal PlayerInventoryState Owner;
            internal EquipmentSlotId Slot;
            internal IVariableInventoryCellData Item;
            internal StandardStashViewData.HeightResizeReceipt InventoryResize;
            internal EquipmentTakeReceiptState State;
            internal bool PublicationPrepared;
        }

        public sealed class BackpackUpgradeReceipt
        {
            internal PlayerInventoryState Owner;
            internal IVariableInventoryCellData PreviousBackpack;
            internal IVariableInventoryCellData ReplacementBackpack;
            internal StandardStashViewData.HeightResizeReceipt InventoryResize;
            internal int ReservedInventoryIndex;
            internal bool PreviousBackpackOriginalRotation;
            internal bool PreviousBackpackReservedRotation;
            internal bool IsConsumed;
        }

        private sealed class AmmunitionMutation
        {
            public StandardStashViewData Owner;
            public int SlotIndex;
            public InventoryItemData Item;
            public int OriginalQuantity;
            public int ConsumedQuantity;

            public int RemainingQuantity => OriginalQuantity - ConsumedQuantity;
        }

        private readonly HashSet<StandardStashViewData> ammunitionCountVisitedGrids =
            new HashSet<StandardStashViewData>(
                InventoryReferenceComparer<StandardStashViewData>.Instance);

        public event Action CapacityChanged;

        public StandardStashViewData Inventory { get; }
        public EquipmentLoadoutData Equipment { get; }
        public PlayerWallet Wallet { get; }
        public int BaseInventoryWidth { get; }
        public int BaseInventoryHeight { get; }
        public int ExpectedInventoryHeight
        {
            get
            {
                if (!TryCalculateExpectedInventoryHeight(
                        Equipment.GetItem(EquipmentSlotId.Backpack),
                        out int expectedHeight,
                        out string error))
                {
                    throw new InvalidOperationException(error);
                }

                return expectedHeight;
            }
        }

        public PlayerInventoryState(
            StandardStashViewData inventory,
            EquipmentLoadoutData equipment)
            : this(
                inventory,
                equipment,
                new PlayerWallet(),
                GetInitialBaseWidth(inventory),
                GetInitialBaseHeight(inventory, equipment))
        {
        }

        public PlayerInventoryState(
            StandardStashViewData inventory,
            EquipmentLoadoutData equipment,
            PlayerWallet wallet)
            : this(
                inventory,
                equipment,
                wallet,
                GetInitialBaseWidth(inventory),
                GetInitialBaseHeight(inventory, equipment))
        {
        }

        public PlayerInventoryState(
            StandardStashViewData inventory,
            EquipmentLoadoutData equipment,
            PlayerWallet wallet,
            int baseInventoryWidth,
            int baseInventoryHeight)
        {
            Inventory = inventory ?? throw new ArgumentNullException(nameof(inventory));
            Equipment = equipment ?? throw new ArgumentNullException(nameof(equipment));
            Wallet = wallet ?? throw new ArgumentNullException(nameof(wallet));
            BaseInventoryWidth = baseInventoryWidth;
            BaseInventoryHeight = baseInventoryHeight;

            if (!TryValidateInventoryCapacity(out string error))
            {
                throw new ArgumentException(error, nameof(inventory));
            }
        }

        public bool TryValidateInventoryCapacity(out string error)
        {
            if (!InventoryGridConstraints.TryValidateDimensions(
                    BaseInventoryWidth,
                    BaseInventoryHeight,
                    out error))
            {
                error = $"Player base inventory is invalid: {error}";
                return false;
            }

            if (!TryCalculateExpectedInventoryHeight(
                    Equipment.GetItem(EquipmentSlotId.Backpack),
                    out int expectedHeight,
                    out error))
            {
                return false;
            }

            if (Inventory.CapacityWidth != BaseInventoryWidth ||
                Inventory.CapacityHeight != expectedHeight ||
                Inventory.CellData == null ||
                Inventory.CellData.Length != BaseInventoryWidth * expectedHeight)
            {
                error = $"Player inventory is {Inventory.CapacityWidth}x{Inventory.CapacityHeight}, " +
                        $"but its equipment requires {BaseInventoryWidth}x{expectedHeight}.";
                return false;
            }

            error = null;
            return true;
        }

        public bool TryPlaceEquipment(
            EquipmentSlotId slot,
            IVariableInventoryCellData item,
            out string error)
        {
            int slotIndex = EquipmentSlotCatalog.GetIndex(slot);
            if (!TryValidateInventoryCapacity(out error) ||
                slotIndex < 0 || !Equipment.CheckInsert(slotIndex, item))
            {
                if (error == null)
                {
                    error = $"The item cannot be equipped in {slot}.";
                }
                return false;
            }

            IVariableInventoryCellData targetBackpack = slot == EquipmentSlotId.Backpack
                ? item
                : Equipment.GetItem(EquipmentSlotId.Backpack);
            if (!TryCalculateExpectedInventoryHeight(
                    targetBackpack,
                    out int targetHeight,
                    out error))
            {
                return false;
            }

            int previousHeight = Inventory.CapacityHeight;
            bool capacityChanged = targetHeight != previousHeight;
            if (capacityChanged &&
                !Inventory.TryResizeHeight(previousHeight, targetHeight, out error))
            {
                return false;
            }

            try
            {
                if (!Equipment.TryPlaceWithoutNotification(slot, item, out string placementError))
                {
                    if (capacityChanged &&
                        !Inventory.TryResizeHeight(targetHeight, previousHeight, out string rollbackError))
                    {
                        error = $"The item could not be equipped, and inventory capacity rollback " +
                                $"also failed: {rollbackError}";
                        return false;
                    }

                    error = placementError;
                    return false;
                }
            }
            catch (Exception exception)
            {
                string rollbackSuffix = string.Empty;
                if (capacityChanged &&
                    !Inventory.TryResizeHeight(targetHeight, previousHeight, out string rollbackError))
                {
                    rollbackSuffix = $" Inventory capacity rollback also failed: {rollbackError}";
                }

                error = $"Could not equip the item: {exception.Message}.{rollbackSuffix}";
                return false;
            }

            if (!TryValidateInventoryCapacity(out string validationError))
            {
                bool equipmentRolledBack = Equipment.TryTakeWithoutNotification(
                                               slot,
                                               out IVariableInventoryCellData rollbackItem,
                                               out _) &&
                                           ReferenceEquals(rollbackItem, item);
                string capacityRollbackError = null;
                bool capacityRolledBack = !capacityChanged ||
                                          Inventory.TryResizeHeight(
                                              targetHeight,
                                              previousHeight,
                                              out capacityRollbackError);
                error = $"Equipping produced an invalid Player inventory: {validationError}" +
                        (equipmentRolledBack && capacityRolledBack
                            ? string.Empty
                            : $" Rollback was incomplete" +
                              (capacityRolledBack ? "." : $": {capacityRollbackError}"));
                return false;
            }

            Equipment.NotifyChangedSafely();
            if (capacityChanged)
            {
                NotifyCapacityChangedSafely();
            }

            error = null;
            return true;
        }

        public bool TryTakeEquipment(
            EquipmentSlotId slot,
            out IVariableInventoryCellData item,
            out string error)
        {
            return TryTakeEquipment(slot, out item, out _, out error);
        }

        public bool CanTakeEquipment(EquipmentSlotId slot, out string error)
        {
            if (!TryValidateInventoryCapacity(out error))
            {
                return false;
            }

            IVariableInventoryCellData equippedItem = Equipment.GetItem(slot);
            if (equippedItem == null)
            {
                error = $"Equipment slot {slot} is empty.";
                return false;
            }

            IVariableInventoryCellData targetBackpack = slot == EquipmentSlotId.Backpack
                ? null
                : Equipment.GetItem(EquipmentSlotId.Backpack);
            if (!TryCalculateExpectedInventoryHeight(
                    targetBackpack,
                    out int targetHeight,
                    out error))
            {
                return false;
            }

            return Inventory.TryPreviewResizeHeight(
                Inventory.CapacityHeight,
                targetHeight,
                out error);
        }

        public bool CanUnequipToPlayerInventoryAt(
            EquipmentSlotId slot,
            int destinationIndex,
            bool destinationRotation,
            out string error)
        {
            if (!TryValidateInventoryCapacity(out error))
            {
                return false;
            }

            IVariableInventoryCellData equippedItem = Equipment.GetItem(slot);
            if (equippedItem == null)
            {
                error = $"Equipment slot {slot} is empty.";
                return false;
            }

            IVariableInventoryCellData targetBackpack = slot == EquipmentSlotId.Backpack
                ? null
                : Equipment.GetItem(EquipmentSlotId.Backpack);
            if (!TryCalculateExpectedInventoryHeight(
                    targetBackpack,
                    out int targetHeight,
                    out error))
            {
                return false;
            }

            return Inventory.TryPreviewResizeHeightReservingItemAt(
                Inventory.CapacityHeight,
                targetHeight,
                equippedItem,
                destinationIndex,
                destinationRotation,
                out error);
        }

        public bool TryUnequipToPlayerInventoryAt(
            EquipmentSlotId slot,
            int destinationIndex,
            bool destinationRotation,
            out string error)
        {
            if (!CanUnequipToPlayerInventoryAt(
                    slot,
                    destinationIndex,
                    destinationRotation,
                    out error))
            {
                return false;
            }

            IVariableInventoryCellData equippedItem = Equipment.GetItem(slot);
            bool originalRotation = equippedItem.IsRotate;
            IVariableInventoryCellData targetBackpack = slot == EquipmentSlotId.Backpack
                ? null
                : Equipment.GetItem(EquipmentSlotId.Backpack);
            if (!TryCalculateExpectedInventoryHeight(
                    targetBackpack,
                    out int targetHeight,
                    out error))
            {
                return false;
            }

            int previousHeight = Inventory.CapacityHeight;
            if (!Inventory.TryResizeHeightReservingItemAt(
                    previousHeight,
                    targetHeight,
                    equippedItem,
                    destinationIndex,
                    destinationRotation,
                    out StandardStashViewData.HeightResizeReceipt inventoryResize,
                    out error))
            {
                return false;
            }

            bool equipmentTaken = Equipment.TryTakeWithoutNotification(
                slot,
                out IVariableInventoryCellData removedItem,
                out string takeError);
            if (!equipmentTaken || !ReferenceEquals(removedItem, equippedItem))
            {
                string equipmentRollbackError = null;
                bool equipmentRolledBack = !equipmentTaken || removedItem == null ||
                    Equipment.TryPlaceWithoutNotification(
                        slot,
                        removedItem,
                        out equipmentRollbackError);
                bool capacityRolledBack = Inventory.TryRestoreHeightResize(
                    inventoryResize,
                    out string capacityRollbackError);
                error = $"The equipment item changed before the deferred drop completed: " +
                        takeError +
                        (equipmentRolledBack && capacityRolledBack
                            ? string.Empty
                            : $" Rollback was incomplete: {equipmentRollbackError} " +
                              capacityRollbackError);
                return false;
            }

            equippedItem.IsRotate = destinationRotation;
            string placementError = null;
            try
            {
                if (!Inventory.CheckInsert(destinationIndex, equippedItem))
                {
                    placementError =
                        "The previewed Player inventory position changed before drop completion.";
                }
                else
                {
                    Inventory.InsertInventoryItem(destinationIndex, equippedItem);
                }
            }
            catch (Exception exception)
            {
                placementError = $"Could not place the unequipped item: {exception.Message}";
            }

            if (placementError == null &&
                !TryValidateInventoryCapacity(out string validationError))
            {
                placementError =
                    $"Deferred equipment drop produced an invalid Player inventory: " +
                    validationError;
            }

            if (placementError != null)
            {
                bool detachedFromInventory = true;
                if (equippedItem is IVariableInventoryOwnedCellData owned &&
                    ReferenceEquals(owned.InventoryOwner, Inventory))
                {
                    int? insertedIndex = Inventory.GetId(equippedItem);
                    if (!insertedIndex.HasValue)
                    {
                        detachedFromInventory = false;
                    }
                    else
                    {
                        try
                        {
                            Inventory.InsertInventoryItem(insertedIndex.Value, null);
                        }
                        catch (Exception exception)
                        {
                            detachedFromInventory = false;
                            placementError +=
                                $" Destination rollback also failed: {exception.Message}";
                        }
                    }
                }
                else if (equippedItem is IVariableInventoryOwnedCellData unexpectedOwned &&
                         unexpectedOwned.InventoryOwner != null)
                {
                    detachedFromInventory = false;
                    placementError += " The item moved to an unexpected owner.";
                }

                equippedItem.IsRotate = originalRotation;
                string capacityRollbackError = null;
                bool capacityRolledBack = detachedFromInventory &&
                    Inventory.TryRestoreHeightResize(
                        inventoryResize,
                        out capacityRollbackError);
                string equipmentRollbackError = null;
                bool equipmentRolledBack = capacityRolledBack &&
                    Equipment.TryPlaceWithoutNotification(
                        slot,
                        equippedItem,
                        out equipmentRollbackError);
                error = placementError +
                        (equipmentRolledBack
                            ? string.Empty
                            : " Rollback was incomplete: " +
                              (capacityRolledBack
                                  ? equipmentRollbackError
                                  : capacityRollbackError));
                return false;
            }

            Equipment.NotifyChangedSafely();
            if (targetHeight != previousHeight)
            {
                NotifyCapacityChangedSafely();
            }

            error = null;
            return true;
        }

        public bool TryTakeEquipment(
            EquipmentSlotId slot,
            out IVariableInventoryCellData item,
            out EquipmentTakeReceipt receipt,
            out string error)
        {
            if (!TryStageTakeEquipment(slot, out item, out receipt, out error))
            {
                return false;
            }

            if (TryPublishStagedEquipmentTake(receipt, out error))
            {
                return true;
            }

            string publishError = error;
            bool restored = TryRestoreTakenEquipment(receipt, out string rollbackError);
            item = null;
            receipt = null;
            error = $"The equipment take could not be published: {publishError}" +
                    (restored
                        ? string.Empty
                        : $" Staged equipment rollback also failed: {rollbackError}");
            return false;
        }

        public bool TryStageTakeEquipment(
            EquipmentSlotId slot,
            out IVariableInventoryCellData item,
            out EquipmentTakeReceipt receipt,
            out string error)
        {
            item = null;
            receipt = null;
            if (!TryValidateInventoryCapacity(out error))
            {
                return false;
            }

            IVariableInventoryCellData equippedItem = Equipment.GetItem(slot);
            if (equippedItem == null)
            {
                error = $"Equipment slot {slot} is empty.";
                return false;
            }

            IVariableInventoryCellData targetBackpack = slot == EquipmentSlotId.Backpack
                ? null
                : Equipment.GetItem(EquipmentSlotId.Backpack);
            if (!TryCalculateExpectedInventoryHeight(
                    targetBackpack,
                    out int targetHeight,
                    out error))
            {
                return false;
            }

            int previousHeight = Inventory.CapacityHeight;
            bool capacityChanged = targetHeight != previousHeight;
            if (!Equipment.TryTakeWithoutNotification(slot, out item, out error) ||
                !ReferenceEquals(item, equippedItem))
            {
                item = null;
                return false;
            }

            StandardStashViewData.HeightResizeReceipt inventoryResize = null;
            if (capacityChanged &&
                !Inventory.TryResizeHeight(
                    previousHeight,
                    targetHeight,
                    out inventoryResize,
                    out string resizeError))
            {
                bool equipmentRolledBack = Equipment.TryPlaceWithoutNotification(
                    slot,
                    item,
                    out string equipmentRollbackError);
                error = $"The backpack cannot be removed because its items do not fit in the " +
                        $"base inventory: {resizeError}" +
                        (equipmentRolledBack
                            ? string.Empty
                            : $" Equipment rollback also failed: {equipmentRollbackError}");
                item = null;
                return false;
            }

            if (!TryValidateInventoryCapacity(out string validationError))
            {
                string capacityRollbackError = null;
                bool capacityRolledBack = !capacityChanged ||
                                          Inventory.TryRestoreHeightResize(
                                              inventoryResize,
                                              out capacityRollbackError);
                bool equipmentRolledBack = capacityRolledBack &&
                                           Equipment.TryPlaceWithoutNotification(
                                               slot,
                                               item,
                                               out _);
                error = $"Removing equipment produced an invalid Player inventory: {validationError}" +
                        (equipmentRolledBack
                            ? string.Empty
                            : $" Rollback was incomplete" +
                              (capacityRolledBack ? "." : $": {capacityRollbackError}"));
                item = null;
                return false;
            }

            receipt = new EquipmentTakeReceipt
            {
                Owner = this,
                Slot = slot,
                Item = item,
                InventoryResize = inventoryResize,
                State = EquipmentTakeReceiptState.Staged
            };

            error = null;
            return true;
        }

        public bool TryPublishStagedEquipmentTake(
            EquipmentTakeReceipt receipt,
            out string error)
        {
            if (receipt == null || !ReferenceEquals(receipt.Owner, this))
            {
                error = "The equipment-take receipt is missing or belongs to another Player inventory.";
                return false;
            }

            if (receipt.State != EquipmentTakeReceiptState.Staged)
            {
                error = receipt.State == EquipmentTakeReceiptState.Published
                    ? "The staged equipment take was already published."
                    : "The staged equipment take is invalid or was already restored.";
                return false;
            }

            if (!receipt.PublicationPrepared &&
                !TryValidateStagedEquipmentTakePublication(receipt, out error))
            {
                return false;
            }

            receipt.State = EquipmentTakeReceiptState.Published;
            Equipment.NotifyChangedSafely();
            if (receipt.InventoryResize != null)
            {
                NotifyCapacityChangedSafely();
            }

            error = null;
            return true;
        }

        public bool TryPrepareStagedEquipmentTakePublication(
            EquipmentTakeReceipt receipt,
            out string error)
        {
            if (receipt == null || !ReferenceEquals(receipt.Owner, this))
            {
                error = "The equipment-take receipt is missing or belongs to another Player inventory.";
                return false;
            }

            if (receipt.State != EquipmentTakeReceiptState.Staged)
            {
                error = receipt.State == EquipmentTakeReceiptState.Published
                    ? "The staged equipment take was already published."
                    : "The staged equipment take is invalid or was already restored.";
                return false;
            }

            if (receipt.PublicationPrepared)
            {
                error = null;
                return true;
            }

            if (!TryValidateStagedEquipmentTakePublication(receipt, out error))
            {
                return false;
            }

            receipt.PublicationPrepared = true;
            error = null;
            return true;
        }

        private bool TryValidateStagedEquipmentTakePublication(
            EquipmentTakeReceipt receipt,
            out string error)
        {
            if (!EquipmentSlotCatalog.IsValid(receipt.Slot) || receipt.Item == null ||
                Equipment.GetItem(receipt.Slot) != null ||
                Equipment.GetId(receipt.Item).HasValue)
            {
                error = "The staged equipment take no longer matches the equipment loadout.";
                return false;
            }

            return TryValidateInventoryCapacity(out error);
        }

        public bool TryRestoreTakenEquipment(EquipmentTakeReceipt receipt, out string error)
        {
            if (receipt == null || !ReferenceEquals(receipt.Owner, this))
            {
                error = "The equipment-take receipt is missing or belongs to another Player inventory.";
                return false;
            }

            if (receipt.State != EquipmentTakeReceiptState.Staged &&
                receipt.State != EquipmentTakeReceiptState.Published)
            {
                error = "The equipment-take receipt is invalid or was already restored.";
                return false;
            }

            if (!EquipmentSlotCatalog.IsValid(receipt.Slot) || receipt.Item == null)
            {
                error = "The equipment-take receipt does not describe a valid equipment item.";
                return false;
            }

            bool publishRestore = receipt.State == EquipmentTakeReceiptState.Published;

            if (!TryValidateInventoryCapacity(out error))
            {
                return false;
            }

            if (Equipment.GetItem(receipt.Slot) != null ||
                (receipt.Item is IVariableInventoryOwnedCellData owned &&
                 owned.InventoryOwner != null))
            {
                error = "The equipment slot or removed item changed before it could be restored.";
                return false;
            }

            if (receipt.Slot == EquipmentSlotId.Backpack)
            {
                if (!TryCalculateExpectedInventoryHeight(
                        receipt.Item,
                        out int restoredHeight,
                        out error))
                {
                    return false;
                }

                int receiptHeight = receipt.InventoryResize?.BeforeHeight ??
                                    Inventory.CapacityHeight;
                if (restoredHeight != receiptHeight)
                {
                    error = "The removed backpack capacity changed before it could be restored.";
                    return false;
                }
            }

            if (!Equipment.TryPlaceWithoutNotification(
                    receipt.Slot,
                    receipt.Item,
                    out error))
            {
                return false;
            }

            bool capacityChanged = receipt.InventoryResize != null;
            if (capacityChanged &&
                !Inventory.TryRestoreHeightResize(receipt.InventoryResize, out string restoreError))
            {
                bool equipmentRolledBack = Equipment.TryTakeWithoutNotification(
                    receipt.Slot,
                    out IVariableInventoryCellData rollbackItem,
                    out string rollbackError);
                error = $"The original backpack inventory layout could not be restored: {restoreError}" +
                        (equipmentRolledBack && ReferenceEquals(rollbackItem, receipt.Item)
                            ? string.Empty
                            : $" Equipment rollback also failed: {rollbackError}");
                return false;
            }

            if (!TryValidateInventoryCapacity(out string validationError))
            {
                error = $"Restoring the removed equipment produced an invalid Player inventory: " +
                        validationError;
                return false;
            }

            receipt.State = EquipmentTakeReceiptState.Restored;
            if (publishRestore)
            {
                Equipment.NotifyChangedSafely();
                if (capacityChanged)
                {
                    NotifyCapacityChangedSafely();
                }
            }

            error = null;
            return true;
        }

        public bool TryUpgradeBackpack(
            IVariableInventoryCellData replacement,
            out IVariableInventoryCellData removedBackpack,
            out string error)
        {
            return TryUpgradeBackpack(
                replacement,
                out removedBackpack,
                out _,
                out error);
        }

        public bool CanUpgradeBackpack(
            IVariableInventoryCellData replacement,
            out string error)
        {
            if (!TryValidateInventoryCapacity(out error))
            {
                return false;
            }

            IVariableInventoryCellData currentBackpack =
                Equipment.GetItem(EquipmentSlotId.Backpack);
            if (currentBackpack == null)
            {
                error = "No backpack is currently equipped.";
                return false;
            }

            if (!TryGetBackpackBonusRows(currentBackpack, out _, out error) ||
                !TryGetBackpackBonusRows(replacement, out _, out error))
            {
                return false;
            }

            error = null;
            return true;
        }

        public bool CanUpgradeBackpackWithDetachedReplacement(
            IVariableInventoryCellData replacement,
            out string error)
        {
            if (!CanUpgradeBackpack(replacement, out error))
            {
                return false;
            }

            if (replacement is IVariableInventoryOwnedCellData owned &&
                owned.InventoryOwner != null)
            {
                error = "The replacement backpack must be detached before previewing its drop.";
                return false;
            }

            IVariableInventoryCellData currentBackpack =
                Equipment.GetItem(EquipmentSlotId.Backpack);
            if (!TryCalculateExpectedInventoryHeight(
                    replacement,
                    out int targetHeight,
                    out error))
            {
                return false;
            }

            return Inventory.TryPreviewResizeHeightReservingItem(
                Inventory.CapacityHeight,
                targetHeight,
                currentBackpack,
                out _,
                out _,
                out error);
        }

        public bool TryUpgradeBackpack(
            IVariableInventoryCellData replacement,
            out IVariableInventoryCellData removedBackpack,
            out BackpackUpgradeReceipt receipt,
            out string error)
        {
            removedBackpack = null;
            receipt = null;
            if (!TryValidateInventoryCapacity(out error))
            {
                return false;
            }

            if (!CanUpgradeBackpack(replacement, out error))
            {
                return false;
            }

            IVariableInventoryCellData currentBackpack =
                Equipment.GetItem(EquipmentSlotId.Backpack);

            if (replacement is IVariableInventoryOwnedCellData owned &&
                owned.InventoryOwner != null)
            {
                error = "The replacement backpack must be detached before an upgrade.";
                return false;
            }

            if (!TryCalculateExpectedInventoryHeight(
                    replacement,
                    out int targetHeight,
                    out error))
            {
                return false;
            }

            int previousHeight = Inventory.CapacityHeight;
            bool previousBackpackOriginalRotation = currentBackpack.IsRotate;
            if (!Inventory.TryResizeHeightReservingItem(
                    previousHeight,
                    targetHeight,
                    currentBackpack,
                    out int reservedInventoryIndex,
                    out bool reservedBackpackRotation,
                    out StandardStashViewData.HeightResizeReceipt inventoryResize,
                    out error))
            {
                return false;
            }

            if (!Equipment.TryReplaceWithoutNotification(
                    EquipmentSlotId.Backpack,
                    currentBackpack,
                    replacement,
                    out removedBackpack,
                    out string replacementError))
            {
                bool capacityRolledBack = Inventory.TryRestoreHeightResize(
                    inventoryResize,
                    out string rollbackError);
                error = replacementError +
                        (capacityRolledBack
                            ? string.Empty
                            : $" Inventory capacity rollback also failed: {rollbackError}");
                removedBackpack = null;
                return false;
            }

            if (ReferenceEquals(removedBackpack, currentBackpack))
            {
                removedBackpack.IsRotate = reservedBackpackRotation;
            }

            if (!ReferenceEquals(removedBackpack, currentBackpack) ||
                !Inventory.CheckInsert(reservedInventoryIndex, removedBackpack))
            {
                if (removedBackpack != null)
                {
                    removedBackpack.IsRotate = previousBackpackOriginalRotation;
                }
                bool equipmentRolledBack = Equipment.TryReplaceWithoutNotification(
                    EquipmentSlotId.Backpack,
                    replacement,
                    currentBackpack,
                    out IVariableInventoryCellData rolledBackReplacement,
                    out string equipmentRollbackError);
                string capacityRollbackError = null;
                bool capacityRolledBack = equipmentRolledBack &&
                                          ReferenceEquals(rolledBackReplacement, replacement) &&
                                          Inventory.TryRestoreHeightResize(
                                              inventoryResize,
                                              out capacityRollbackError);
                error = "The previewed slot for the previous backpack became invalid." +
                        (equipmentRolledBack && capacityRolledBack
                            ? string.Empty
                            : $" Rollback was incomplete: {equipmentRollbackError}" +
                              (capacityRolledBack ? string.Empty : $" {capacityRollbackError}"));
                removedBackpack = null;
                return false;
            }

            if (!TryValidateInventoryCapacity(out string validationError))
            {
                removedBackpack.IsRotate = previousBackpackOriginalRotation;
                bool equipmentRolledBack = Equipment.TryReplaceWithoutNotification(
                    EquipmentSlotId.Backpack,
                    replacement,
                    currentBackpack,
                    out IVariableInventoryCellData rolledBackReplacement,
                    out string equipmentRollbackError);
                string capacityRollbackError = null;
                bool capacityRolledBack = equipmentRolledBack &&
                                          ReferenceEquals(rolledBackReplacement, replacement) &&
                                          Inventory.TryRestoreHeightResize(
                                              inventoryResize,
                                              out capacityRollbackError);
                error = $"Backpack upgrade produced an invalid Player inventory: {validationError}" +
                        (equipmentRolledBack && capacityRolledBack
                            ? string.Empty
                            : $" Rollback was incomplete: {equipmentRollbackError}" +
                              (capacityRolledBack ? string.Empty : $" {capacityRollbackError}"));
                removedBackpack = null;
                return false;
            }

            Equipment.NotifyChangedSafely();
            NotifyCapacityChangedSafely();
            receipt = new BackpackUpgradeReceipt
            {
                Owner = this,
                PreviousBackpack = removedBackpack,
                ReplacementBackpack = replacement,
                InventoryResize = inventoryResize,
                ReservedInventoryIndex = reservedInventoryIndex,
                PreviousBackpackOriginalRotation = previousBackpackOriginalRotation,
                PreviousBackpackReservedRotation = reservedBackpackRotation
            };
            error = null;
            return true;
        }

        public bool TryRestoreBackpackUpgrade(
            BackpackUpgradeReceipt receipt,
            out IVariableInventoryCellData removedReplacement,
            out string error)
        {
            removedReplacement = null;
            if (receipt == null || !ReferenceEquals(receipt.Owner, this) || receipt.IsConsumed ||
                receipt.InventoryResize == null)
            {
                error = "The backpack-upgrade receipt is missing, foreign, or already consumed.";
                return false;
            }

            if (!TryValidateInventoryCapacity(out error))
            {
                return false;
            }

            if (!ReferenceEquals(
                    Equipment.GetItem(EquipmentSlotId.Backpack),
                    receipt.ReplacementBackpack) ||
                (receipt.PreviousBackpack is IVariableInventoryOwnedCellData previousOwned &&
                 previousOwned.InventoryOwner != null) ||
                receipt.PreviousBackpack.IsRotate !=
                receipt.PreviousBackpackReservedRotation ||
                !Inventory.CheckInsert(
                    receipt.ReservedInventoryIndex,
                    receipt.PreviousBackpack))
            {
                error = "The backpack slot, previewed storage space, or previous backpack " +
                        "changed before rollback.";
                return false;
            }

            if (!TryCalculateExpectedInventoryHeight(
                    receipt.PreviousBackpack,
                    out int restoredHeight,
                    out error) ||
                restoredHeight != receipt.InventoryResize.BeforeHeight)
            {
                if (error == null)
                {
                    error = "The previous backpack capacity changed before rollback.";
                }
                return false;
            }

            if (!Equipment.TryReplaceWithoutNotification(
                    EquipmentSlotId.Backpack,
                    receipt.ReplacementBackpack,
                    receipt.PreviousBackpack,
                    out removedReplacement,
                    out error))
            {
                return false;
            }

            receipt.PreviousBackpack.IsRotate =
                receipt.PreviousBackpackOriginalRotation;

            if (!Inventory.TryRestoreHeightResize(receipt.InventoryResize, out string resizeError))
            {
                bool equipmentRolledBack = Equipment.TryReplaceWithoutNotification(
                    EquipmentSlotId.Backpack,
                    receipt.PreviousBackpack,
                    receipt.ReplacementBackpack,
                    out IVariableInventoryCellData rolledBackPrevious,
                    out string equipmentRollbackError);
                if (equipmentRolledBack &&
                    ReferenceEquals(rolledBackPrevious, receipt.PreviousBackpack))
                {
                    receipt.PreviousBackpack.IsRotate =
                        receipt.PreviousBackpackReservedRotation;
                }
                error = $"The original backpack capacity/layout could not be restored: {resizeError}" +
                        (equipmentRolledBack &&
                         ReferenceEquals(rolledBackPrevious, receipt.PreviousBackpack)
                            ? string.Empty
                            : $" Equipment rollback also failed: {equipmentRollbackError}");
                removedReplacement = null;
                return false;
            }

            if (!TryValidateInventoryCapacity(out string validationError))
            {
                error = $"Backpack upgrade rollback produced an invalid Player inventory: " +
                        validationError;
                removedReplacement = null;
                return false;
            }

            receipt.IsConsumed = true;
            Equipment.NotifyChangedSafely();
            NotifyCapacityChangedSafely();
            error = null;
            return true;
        }

        private bool TryCalculateExpectedInventoryHeight(
            IVariableInventoryCellData backpackItem,
            out int expectedHeight,
            out string error)
        {
            expectedHeight = BaseInventoryHeight;
            int bonusRows = 0;
            if (backpackItem != null &&
                !TryGetBackpackBonusRows(backpackItem, out bonusRows, out error))
            {
                return false;
            }

            long candidateHeight = (long)BaseInventoryHeight + bonusRows;
            if (candidateHeight > int.MaxValue)
            {
                error = "The backpack inventory height exceeds the supported integer range.";
                return false;
            }

            if (!InventoryGridConstraints.TryValidateDimensions(
                    BaseInventoryWidth,
                    (int)candidateHeight,
                    out error))
            {
                error = $"The backpack inventory capacity is invalid: {error}";
                return false;
            }

            expectedHeight = (int)candidateHeight;
            error = null;
            return true;
        }

        private static bool TryGetBackpackBonusRows(
            IVariableInventoryCellData backpackItem,
            out int bonusRows,
            out string error)
        {
            bonusRows = 0;
            if (!(backpackItem is InventoryItemData inventoryItem) ||
                inventoryItem.Definition == null ||
                !inventoryItem.Definition.CanEquipIn(EquipmentSlotId.Backpack))
            {
                error = "The backpack definition is invalid.";
                return false;
            }

            if (!inventoryItem.Definition.TryValidateInventoryShape(out error))
            {
                return false;
            }

            bonusRows = inventoryItem.Definition.BackpackBonusRows;
            error = null;
            return true;
        }

        private void NotifyCapacityChangedSafely()
        {
            Delegate[] subscribers = CapacityChanged?.GetInvocationList();
            if (subscribers == null)
            {
                return;
            }

            foreach (Delegate subscriber in subscribers)
            {
                try
                {
                    ((Action)subscriber).Invoke();
                }
                catch (Exception exception)
                {
                    Debug.LogException(exception);
                }
            }
        }

        private static int GetInitialBaseWidth(StandardStashViewData inventory)
        {
            return inventory?.CapacityWidth ?? 0;
        }

        private static int GetInitialBaseHeight(
            StandardStashViewData inventory,
            EquipmentLoadoutData equipment)
        {
            if (inventory == null)
            {
                return 0;
            }

            int bonusRows = 0;
            if (equipment?.GetItem(EquipmentSlotId.Backpack) is InventoryItemData backpack &&
                backpack.Definition != null)
            {
                bonusRows = backpack.Definition.BackpackBonusRows;
            }

            return inventory.CapacityHeight - bonusRows;
        }

        public bool TryGetOwnedStackItemPlacement(
            InventoryItemData item,
            out StandardStashViewData owner,
            out int slotIndex,
            out string error)
        {
            owner = null;
            slotIndex = -1;
            if (item?.Definition == null || item.Quantity <= 0)
            {
                error = "The requested stack item is invalid.";
                return false;
            }

            if (!(item.InventoryOwner is StandardStashViewData itemOwner) ||
                !OwnsInventory(itemOwner))
            {
                error = "The requested stack item is not owned by the Player inventory.";
                return false;
            }

            int? itemSlot = itemOwner.GetId(item);
            if (!itemSlot.HasValue)
            {
                error = "The stack item owner does not contain the requested item.";
                return false;
            }

            owner = itemOwner;
            slotIndex = itemSlot.Value;
            error = null;
            return true;
        }

        public bool OwnsInventory(IVariableInventoryViewData candidate)
        {
            if (candidate == null)
            {
                return false;
            }

            if (ReferenceEquals(candidate, Inventory) ||
                ReferenceEquals(candidate, Equipment))
            {
                return true;
            }

            return IsNestedInventory(Inventory, candidate) ||
                   IsNestedInventory(Equipment, candidate);
        }

        internal static bool IsNestedInventory(
            IVariableInventoryViewData root,
            IVariableInventoryViewData candidate)
        {
            if (root == null || candidate == null)
            {
                return false;
            }

            if (ReferenceEquals(root, candidate))
            {
                return true;
            }

            var visited = new HashSet<IVariableInventoryViewData>(
                InventoryReferenceComparer<IVariableInventoryViewData>.Instance);
            return ContainsNestedInventory(root, candidate, visited);
        }

        public bool TryConsumeOneOwnedStackItem(
            InventoryItemData item,
            StandardStashViewData expectedOwner,
            int expectedSlotIndex,
            int expectedQuantity,
            out string error)
        {
            if (expectedOwner == null || expectedQuantity <= 0)
            {
                error = "The expected stack item placement is invalid.";
                return false;
            }

            if (!TryGetOwnedStackItemPlacement(
                    item,
                    out StandardStashViewData actualOwner,
                    out int actualSlotIndex,
                    out error))
            {
                return false;
            }

            if (!ReferenceEquals(actualOwner, expectedOwner) ||
                actualSlotIndex != expectedSlotIndex ||
                item.Quantity != expectedQuantity)
            {
                error = "The stack item changed before it could be consumed.";
                return false;
            }

            if (expectedQuantity > 1)
            {
                return item.TryChangeQuantity(
                    expectedOwner,
                    expectedQuantity,
                    expectedQuantity - 1,
                    out error);
            }

            try
            {
                expectedOwner.InsertInventoryItem(expectedSlotIndex, null);
            }
            catch (Exception exception)
            {
                error = $"Could not remove the consumed stack item: {exception.Message}";
                return false;
            }

            error = null;
            return true;
        }

        public bool TryGetReloadableRoundCount(
            InventoryItemData weapon,
            out int reloadableRoundCount,
            out string error)
        {
            reloadableRoundCount = 0;
            if (!TryValidateEquippedWeapon(weapon, out error))
            {
                return false;
            }

            int missingRounds = weapon.MagazineCapacity - weapon.LoadedAmmunition;
            if (missingRounds <= 0)
            {
                error = null;
                return true;
            }

            if (!TryBuildAmmunitionPlan(
                    weapon.Definition.AmmunitionDefinitionId,
                    missingRounds,
                    out List<AmmunitionMutation> plan,
                    out error))
            {
                return false;
            }

            foreach (AmmunitionMutation mutation in plan)
            {
                reloadableRoundCount += mutation.ConsumedQuantity;
            }

            error = null;
            return true;
        }

        public bool TryGetReserveAmmunitionCount(
            InventoryItemData weapon,
            out int reserveRoundCount,
            out string error)
        {
            reserveRoundCount = 0;
            if (!TryValidateEquippedWeapon(weapon, out error))
            {
                return false;
            }

            ammunitionCountVisitedGrids.Clear();
            long total = 0;
            try
            {
                if (!TryCountAmmunitionFromGrid(
                        Inventory,
                        weapon.Definition.AmmunitionDefinitionId,
                        ammunitionCountVisitedGrids,
                        ref total,
                        out error))
                {
                    return false;
                }

                foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
                {
                    if (!(Equipment.GetItem(slot) is InventoryContainerItemData container))
                    {
                        continue;
                    }

                    if (!TryCountAmmunitionFromGrid(
                            container.CaseData,
                            weapon.Definition.AmmunitionDefinitionId,
                            ammunitionCountVisitedGrids,
                            ref total,
                            out error))
                    {
                        return false;
                    }
                }

                reserveRoundCount = total >= int.MaxValue ? int.MaxValue : (int)total;
                error = null;
                return true;
            }
            finally
            {
                ammunitionCountVisitedGrids.Clear();
            }
        }

        public bool TryConsumeLoadedRound(InventoryItemData weapon, out string error)
        {
            if (!TryValidateEquippedWeapon(weapon, out error))
            {
                return false;
            }

            int loadedBefore = weapon.LoadedAmmunition;
            if (loadedBefore <= 0)
            {
                error = "The active weapon has no loaded ammunition.";
                return false;
            }

            if (!weapon.TryChangeLoadedAmmunition(
                    Equipment,
                    loadedBefore,
                    loadedBefore - 1,
                    out error))
            {
                return false;
            }

            Equipment.NotifyOwnedItemStateChanged(weapon);
            error = null;
            return true;
        }

        public bool TryReloadWeapon(
            InventoryItemData weapon,
            out int loadedRoundCount,
            out string error)
        {
            loadedRoundCount = 0;
            if (!TryValidateEquippedWeapon(weapon, out error))
            {
                return false;
            }

            int loadedBefore = weapon.LoadedAmmunition;
            int missingRounds = weapon.MagazineCapacity - loadedBefore;
            if (missingRounds <= 0)
            {
                error = "The active weapon magazine is already full.";
                return false;
            }

            if (!TryBuildAmmunitionPlan(
                    weapon.Definition.AmmunitionDefinitionId,
                    missingRounds,
                    out List<AmmunitionMutation> plan,
                    out error))
            {
                return false;
            }

            foreach (AmmunitionMutation mutation in plan)
            {
                loadedRoundCount += mutation.ConsumedQuantity;
            }

            if (loadedRoundCount <= 0)
            {
                error = "The Player inventory contains no compatible ammunition.";
                return false;
            }

            int appliedCount = 0;
            try
            {
                for (; appliedCount < plan.Count; appliedCount++)
                {
                    AmmunitionMutation mutation = plan[appliedCount];
                    if (mutation.RemainingQuantity > 0)
                    {
                        if (!mutation.Item.TryChangeQuantity(
                                mutation.Owner,
                                mutation.OriginalQuantity,
                                mutation.RemainingQuantity,
                                out string quantityError))
                        {
                            throw new InvalidOperationException(quantityError);
                        }
                    }
                    else
                    {
                        mutation.Owner.InsertInventoryItem(mutation.SlotIndex, null);
                    }
                }

                if (!weapon.TryChangeLoadedAmmunition(
                        Equipment,
                        loadedBefore,
                        loadedBefore + loadedRoundCount,
                        out string weaponError))
                {
                    throw new InvalidOperationException(weaponError);
                }
            }
            catch (Exception exception)
            {
                string rollbackError = RollBackAmmunitionPlan(plan, appliedCount);
                loadedRoundCount = 0;
                error = "Could not complete the ammunition reload transaction: " +
                        exception.Message + rollbackError;
                return false;
            }

            Equipment.NotifyOwnedItemStateChanged(weapon);
            error = null;
            return true;
        }

        /// <summary>
        /// Atomically removes every root item carried in the Player grid and equipment.
        /// Nested container contents leave with their root container. The Player state and
        /// both container instances stay alive so scene-persistent observers keep the same
        /// authoritative object graph.
        /// </summary>
        public bool TryDiscardAllCarriedItems(out string error)
        {
            if (Inventory.CellData == null)
            {
                error = "Player inventory cell data is missing.";
                return false;
            }

            var inventoryRoots = new List<KeyValuePair<int, InventoryItemData>>();
            var equipmentRoots = new List<KeyValuePair<EquipmentSlotId, InventoryItemData>>();
            var seen = new HashSet<InventoryItemData>(
                InventoryReferenceComparer<InventoryItemData>.Instance);
            for (int index = 0; index < Inventory.CellData.Length; index++)
            {
                IVariableInventoryCellData item = Inventory.CellData[index];
                if (item == null)
                {
                    continue;
                }

                if (!(item is InventoryItemData inventoryItem))
                {
                    error = $"Player inventory slot {index} contains an unsupported runtime item type.";
                    return false;
                }

                if (!seen.Add(inventoryItem))
                {
                    error = "The same item is referenced by multiple Player inventory slots.";
                    return false;
                }

                if (!ReferenceEquals(inventoryItem.InventoryOwner, Inventory))
                {
                    error = $"Player inventory slot {index} has inconsistent item ownership.";
                    return false;
                }

                inventoryRoots.Add(
                    new KeyValuePair<int, InventoryItemData>(index, inventoryItem));
            }

            foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
            {
                IVariableInventoryCellData item = Equipment.GetItem(slot);
                if (item == null)
                {
                    continue;
                }

                if (!(item is InventoryItemData inventoryItem))
                {
                    error = $"Equipment slot {slot} contains an unsupported runtime item type.";
                    return false;
                }

                if (!seen.Add(inventoryItem))
                {
                    error = "The same item is owned by both the Player grid and equipment.";
                    return false;
                }

                if (!ReferenceEquals(inventoryItem.InventoryOwner, Equipment))
                {
                    error = $"Equipment slot {slot} has inconsistent item ownership.";
                    return false;
                }

                equipmentRoots.Add(
                    new KeyValuePair<EquipmentSlotId, InventoryItemData>(slot, inventoryItem));
            }

            int removedInventoryRoots = 0;
            try
            {
                for (; removedInventoryRoots < inventoryRoots.Count; removedInventoryRoots++)
                {
                    Inventory.InsertInventoryItem(inventoryRoots[removedInventoryRoots].Key, null);
                }
            }
            catch (Exception exception)
            {
                string rollbackError = RestoreInventoryRoots(
                    inventoryRoots,
                    removedInventoryRoots);
                error = "Could not clear the Player inventory: " + exception.Message + rollbackError;
                return false;
            }

            if (!Equipment.TryClearAllWithoutNotification(out string equipmentError))
            {
                string rollbackError = RestoreInventoryRoots(
                    inventoryRoots,
                    removedInventoryRoots);
                error = "Could not clear Player equipment: " + equipmentError + rollbackError;
                return false;
            }

            int previousHeight = Inventory.CapacityHeight;
            bool capacityChanged = previousHeight != BaseInventoryHeight;
            if (capacityChanged &&
                !Inventory.TryResizeHeight(
                    previousHeight,
                    BaseInventoryHeight,
                    out string resizeError))
            {
                string equipmentRollbackError = RestoreEquipmentRoots(equipmentRoots);
                string inventoryRollbackError = RestoreInventoryRoots(
                    inventoryRoots,
                    removedInventoryRoots);
                error = "Could not restore the base inventory capacity after discarding the " +
                        $"equipped backpack: {resizeError}" +
                        equipmentRollbackError +
                        inventoryRollbackError;
                return false;
            }

            if (equipmentRoots.Count > 0)
            {
                Equipment.NotifyChangedSafely();
            }
            if (capacityChanged)
            {
                NotifyCapacityChangedSafely();
            }
            error = null;
            return true;
        }

        private string RestoreEquipmentRoots(
            IReadOnlyList<KeyValuePair<EquipmentSlotId, InventoryItemData>> roots)
        {
            var failures = new List<string>();
            foreach (KeyValuePair<EquipmentSlotId, InventoryItemData> placement in roots)
            {
                if (!Equipment.TryPlaceWithoutNotification(
                        placement.Key,
                        placement.Value,
                        out string restoreError))
                {
                    failures.Add($"{placement.Key}: {restoreError}");
                }
            }

            return failures.Count == 0
                ? string.Empty
                : " Equipment rollback failed for " + string.Join("; ", failures) + ".";
        }

        private string RestoreInventoryRoots(
            IReadOnlyList<KeyValuePair<int, InventoryItemData>> roots,
            int removedCount)
        {
            var failures = new List<string>();
            for (int index = 0; index < removedCount; index++)
            {
                KeyValuePair<int, InventoryItemData> placement = roots[index];
                try
                {
                    Inventory.InsertInventoryItem(placement.Key, placement.Value);
                }
                catch (Exception exception)
                {
                    failures.Add($"slot {placement.Key}: {exception.Message}");
                }
            }

            return failures.Count == 0
                ? string.Empty
                : $" Inventory rollback also failed ({string.Join("; ", failures)}).";
        }

        private static bool ContainsNestedInventory(
            IVariableInventoryViewData current,
            IVariableInventoryViewData target,
            HashSet<IVariableInventoryViewData> visited)
        {
            if (current == null || !visited.Add(current))
            {
                return false;
            }

            if (current is StandardStashViewData stash && stash.CellData != null)
            {
                foreach (IVariableInventoryCellData cell in stash.CellData)
                {
                    if (cell is IStandardCaseCellData container &&
                        container.CaseData != null &&
                        (ReferenceEquals(container.CaseData, target) ||
                         ContainsNestedInventory(container.CaseData, target, visited)))
                    {
                        return true;
                    }
                }
            }
            else if (current is EquipmentLoadoutData equipment)
            {
                foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
                {
                    if (equipment.GetItem(slot) is IStandardCaseCellData container &&
                        container.CaseData != null &&
                        (ReferenceEquals(container.CaseData, target) ||
                         ContainsNestedInventory(container.CaseData, target, visited)))
                    {
                        return true;
                    }
                }
            }

            return false;
        }

        private bool TryValidateEquippedWeapon(
            InventoryItemData weapon,
            out string error)
        {
            if (weapon?.Definition == null || !weapon.Definition.IsWeapon)
            {
                error = "The requested item is not a weapon.";
                return false;
            }

            if (!ReferenceEquals(weapon.InventoryOwner, Equipment))
            {
                error = "The requested weapon is not owned by the Player equipment loadout.";
                return false;
            }

            for (int weaponNumber = 1;
                 weaponNumber <= EquipmentSlotCatalog.WeaponSlotCount;
                 weaponNumber++)
            {
                if (ReferenceEquals(
                        Equipment.GetItem(EquipmentSlotCatalog.GetWeaponSlot(weaponNumber)),
                        weapon))
                {
                    error = null;
                    return true;
                }
            }

            error = "The requested weapon is not present in a Player weapon slot.";
            return false;
        }

        private bool TryBuildAmmunitionPlan(
            int ammunitionDefinitionId,
            int requestedQuantity,
            out List<AmmunitionMutation> plan,
            out string error)
        {
            plan = new List<AmmunitionMutation>();
            int remaining = requestedQuantity;
            var visitedGrids = new HashSet<StandardStashViewData>(
                InventoryReferenceComparer<StandardStashViewData>.Instance);
            if (!TryAppendAmmunitionFromGrid(
                    Inventory,
                    ammunitionDefinitionId,
                    plan,
                    visitedGrids,
                    ref remaining,
                    out error))
            {
                return false;
            }

            if (remaining > 0)
            {
                foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
                {
                    if (!(Equipment.GetItem(slot) is InventoryContainerItemData container))
                    {
                        continue;
                    }

                    if (!TryAppendAmmunitionFromGrid(
                            container.CaseData,
                            ammunitionDefinitionId,
                            plan,
                            visitedGrids,
                            ref remaining,
                            out error))
                    {
                        return false;
                    }

                    if (remaining <= 0)
                    {
                        break;
                    }
                }
            }

            error = null;
            return true;
        }

        private static bool TryCountAmmunitionFromGrid(
            StandardStashViewData grid,
            int ammunitionDefinitionId,
            HashSet<StandardStashViewData> visitedGrids,
            ref long total,
            out string error)
        {
            if (grid?.CellData == null || !visitedGrids.Add(grid))
            {
                error = grid == null || grid.CellData == null
                    ? "A Player-owned inventory grid is missing."
                    : "The Player inventory contains a shared or cyclic container grid.";
                return false;
            }

            for (int slotIndex = 0; slotIndex < grid.CellData.Length; slotIndex++)
            {
                if (!(grid.CellData[slotIndex] is InventoryItemData item))
                {
                    if (grid.CellData[slotIndex] != null)
                    {
                        error = $"Player inventory slot {slotIndex} contains an unsupported runtime item type.";
                        return false;
                    }

                    continue;
                }

                if (!ReferenceEquals(item.InventoryOwner, grid))
                {
                    error = $"Player inventory item ID {item.Id} has inconsistent ownership.";
                    return false;
                }

                if (item.Id == ammunitionDefinitionId && item.Definition.IsAmmunition)
                {
                    total = Math.Min(int.MaxValue, total + item.Quantity);
                }

                if (item is InventoryContainerItemData container &&
                    !TryCountAmmunitionFromGrid(
                        container.CaseData,
                        ammunitionDefinitionId,
                        visitedGrids,
                        ref total,
                        out error))
                {
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryAppendAmmunitionFromGrid(
            StandardStashViewData grid,
            int ammunitionDefinitionId,
            List<AmmunitionMutation> plan,
            HashSet<StandardStashViewData> visitedGrids,
            ref int remaining,
            out string error)
        {
            if (grid?.CellData == null || !visitedGrids.Add(grid))
            {
                error = grid == null || grid.CellData == null
                    ? "A Player-owned inventory grid is missing."
                    : "The Player inventory contains a shared or cyclic container grid.";
                return false;
            }

            for (int slotIndex = 0;
                 slotIndex < grid.CellData.Length && remaining > 0;
                 slotIndex++)
            {
                if (!(grid.CellData[slotIndex] is InventoryItemData item))
                {
                    if (grid.CellData[slotIndex] != null)
                    {
                        error = $"Player inventory slot {slotIndex} contains an unsupported runtime item type.";
                        return false;
                    }

                    continue;
                }

                if (!ReferenceEquals(item.InventoryOwner, grid))
                {
                    error = $"Player inventory item ID {item.Id} has inconsistent ownership.";
                    return false;
                }

                if (item.Id == ammunitionDefinitionId && item.Definition.IsAmmunition)
                {
                    int consumed = Math.Min(item.Quantity, remaining);
                    plan.Add(new AmmunitionMutation
                    {
                        Owner = grid,
                        SlotIndex = slotIndex,
                        Item = item,
                        OriginalQuantity = item.Quantity,
                        ConsumedQuantity = consumed
                    });
                    remaining -= consumed;
                }

                if (remaining > 0 && item is InventoryContainerItemData container &&
                    !TryAppendAmmunitionFromGrid(
                        container.CaseData,
                        ammunitionDefinitionId,
                        plan,
                        visitedGrids,
                        ref remaining,
                        out error))
                {
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static string RollBackAmmunitionPlan(
            IReadOnlyList<AmmunitionMutation> plan,
            int appliedCount)
        {
            var failures = new List<string>();
            int lastAppliedIndex = Math.Min(appliedCount, plan.Count) - 1;
            for (int index = lastAppliedIndex; index >= 0; index--)
            {
                AmmunitionMutation mutation = plan[index];
                try
                {
                    if (mutation.RemainingQuantity > 0)
                    {
                        if (!mutation.Item.TryChangeQuantity(
                                mutation.Owner,
                                mutation.RemainingQuantity,
                                mutation.OriginalQuantity,
                                out string quantityError))
                        {
                            failures.Add($"slot {mutation.SlotIndex}: {quantityError}");
                        }
                    }
                    else
                    {
                        mutation.Owner.InsertInventoryItem(
                            mutation.SlotIndex,
                            mutation.Item);
                    }
                }
                catch (Exception exception)
                {
                    failures.Add($"slot {mutation.SlotIndex}: {exception.Message}");
                }
            }

            return failures.Count == 0
                ? string.Empty
                : $" Ammunition rollback also failed ({string.Join("; ", failures)}).";
        }
    }

    internal sealed class InventoryReferenceComparer<T> : IEqualityComparer<T>
        where T : class
    {
        public static readonly InventoryReferenceComparer<T> Instance =
            new InventoryReferenceComparer<T>();

        public bool Equals(T x, T y) => ReferenceEquals(x, y);
        public int GetHashCode(T value) => RuntimeHelpers.GetHashCode(value);
    }
}
