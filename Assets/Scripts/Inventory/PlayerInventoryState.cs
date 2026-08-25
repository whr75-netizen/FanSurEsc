using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
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

            EquipmentSlotId primarySlot = EquipmentSlotCatalog.GetPrimarySlot(
                item.Definition.EquipmentSlot);
            int index = EquipmentSlotCatalog.GetIndex(primarySlot);
            return index >= 0 && CheckInsert(index, cellData) ? index : (int?)null;
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
            Changed?.Invoke();
        }

        public bool TryTake(EquipmentSlotId slot, out IVariableInventoryCellData item)
        {
            item = null;
            int index = EquipmentSlotCatalog.GetIndex(slot);
            if (index < 0 || items[index] == null)
            {
                return false;
            }

            item = items[index];
            InsertInventoryItem(index, null);
            return true;
        }

        public bool TryPlace(EquipmentSlotId slot, IVariableInventoryCellData item)
        {
            int index = EquipmentSlotCatalog.GetIndex(slot);
            if (!CheckInsert(index, item))
            {
                return false;
            }

            InsertInventoryItem(index, item);
            return true;
        }

        internal bool TryClearAll(out string error)
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
            Changed?.Invoke();
            error = null;
            return true;
        }
    }

    public sealed class PlayerInventoryState
    {
        public StandardStashViewData Inventory { get; }
        public EquipmentLoadoutData Equipment { get; }

        public PlayerInventoryState(
            StandardStashViewData inventory,
            EquipmentLoadoutData equipment)
        {
            Inventory = inventory ?? throw new ArgumentNullException(nameof(inventory));
            Equipment = equipment ?? throw new ArgumentNullException(nameof(equipment));
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

            if (!Equipment.TryClearAll(out string equipmentError))
            {
                string rollbackError = RestoreInventoryRoots(
                    inventoryRoots,
                    removedInventoryRoots);
                error = "Could not clear Player equipment: " + equipmentError + rollbackError;
                return false;
            }

            error = null;
            return true;
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
