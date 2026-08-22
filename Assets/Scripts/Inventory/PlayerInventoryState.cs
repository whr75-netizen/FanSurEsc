using System;
using System.Collections.Generic;
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
    }
}
